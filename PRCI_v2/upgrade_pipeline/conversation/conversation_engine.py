"""Lightweight conversational orchestration layer.

This module sits **above** the :class:`~upgrade_pipeline.core.inference_engine.InferenceEngine`
and manages short-term conversational memory, emotional continuity, and
rule-based supportive responses.

Architecture:

    UI → ConversationEngine → InferenceEngine → Models

Key design choices:
* No external LLM APIs – pure template / rule-based logic.
* In-memory history only (no persistent DB in v1).
* ``InferenceEngine`` is injected via constructor so the conversation
  layer never owns or rebuilds heavy model artefacts.

Usage:
    from upgrade_pipeline.core.inference_engine import InferenceEngine
    from upgrade_pipeline.conversation import ConversationEngine

    inf = InferenceEngine(...)
    chat = ConversationEngine(inference_engine=inf, max_history=10)

    reply = chat.generate_response("I feel overwhelmed today...")
    print(reply["response"])
    print(reply["follow_up"])
"""

import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from ..core.inference_engine import InferenceEngine
from .adaptive_response import (
    ConversationState,
    generate_adaptive_response,
    generate_adaptive_follow_up,
    build_conversation_state,
)
from .hybrid_assembler import HybridResponseAssembler


# Topic configuration for contextual follow-ups
TOPIC_CONFIG = {
    "sleep": {
        "keywords": [
            "sleep", "insomnia", "tired", "exhausted", "rest", "fatigue",
            "can't sleep", "sleepless", "sleeping", "awake", "drowsy"
        ],
        "acknowledgements": [
            "That sounds exhausting, especially when sleep is being affected.",
            "Sleep issues can make everything feel harder.",
            "It sounds like your sleep has been really challenging lately.",
            "Feeling tired all the time is really draining."
        ],
        "follow_ups": [
            "Have you noticed any patterns in when you struggle to sleep?",
            "Do you find your mind racing when you try to rest?",
            "How has your sleep routine been lately?",
            "Are there specific things keeping you up at night?"
        ]
    },
    "studies": {
        "keywords": [
            "study", "studies", "exam", "work", "deadline", "focus", 
            "assignment", "project", "academic", "school", "university",
            "college", "homework", "research", "paper", "grade"
        ],
        "acknowledgements": [
            "Academic pressure can feel overwhelming sometimes.",
            "That sounds really stressful, especially with studies involved.",
            "Managing studies and everything else is a lot to handle.",
            "It sounds like academic pressure has been building up."
        ],
        "follow_ups": [
            "Do you feel like the pressure has been building gradually?",
            "What part of your studies feels most challenging right now?",
            "How are you balancing your study workload?",
            "Have there been specific deadlines that feel particularly stressful?"
        ]
    },
    "anxiety": {
        "keywords": [
            "anxious", "anxiety", "worry", "overthink", "nervous", "panic",
            "stress", "stressed", "overthinking", "worried", "tense"
        ],
        "acknowledgements": [
            "That sounds really anxiety-provoking.",
            "Feeling anxious or overthinking is exhausting.",
            "It sounds like anxiety has been really difficult lately.",
            "That sounds really stressful and overwhelming."
        ],
        "follow_ups": [
            "When do you notice the anxiety feeling strongest?",
            "What tends to trigger the overthinking for you?",
            "Have you noticed any patterns in when you feel most anxious?",
            "How long have you been feeling this level of anxiety?"
        ]
    },
    "social": {
        "keywords": [
            "alone", "isolated", "friends", "people", "social", "lonely",
            "connection", "relationships", "family", "talk to someone",
            "withdrawn", "socializing", "socialize"
        ],
        "acknowledgements": [
            "Feeling isolated or disconnected is really hard.",
            "It sounds like you've been feeling quite alone lately.",
            "Social connections can feel really challenging sometimes.",
            "That sounds really lonely and difficult."
        ],
        "follow_ups": [
            "Have you been able to connect with anyone recently?",
            "What makes social situations feel most difficult right now?",
            "Is there someone you've wanted to reach out to?",
            "How long have you been feeling this sense of isolation?"
        ]
    },
    "burnout": {
        "keywords": [
            "motivation", "burnout", "drained", "exhausted", "overwhelmed",
            "can't", "no energy", "tired of", "giving up", "burned out",
            "unmotivated", "procrastinate", "procrastination"
        ],
        "acknowledgements": [
            "Feeling burned out and unmotivated is really exhausting.",
            "That sounds completely overwhelming and draining.",
            "It sounds like you're running on empty right now.",
            "Burnout can make everything feel impossible."
        ],
        "follow_ups": [
            "When did you start feeling this level of burnout?",
            "What feels most draining about your current situation?",
            "Have you noticed any specific triggers for the burnout?",
            "Is there anything that used to give you energy that doesn't anymore?"
        ]
    }
}


@dataclass
class _Message:
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class _EmotionSnapshot:
    depression_score: float
    anxiety_score: float
    risk_level: str
    top_root_cause: str
    risk_score: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "depression_score": self.depression_score,
            "anxiety_score": self.anxiety_score,
            "risk_level": self.risk_level,
            "top_root_cause": self.top_root_cause,
            "risk_score": self.risk_score,
            "timestamp": self.timestamp,
        }


class ConversationEngine:
    """Manages conversational state, emotional continuity, and supportive replies.

    The engine is intentionally lightweight:

    * **No ML inference** – delegates 100 % to the injected
      :class:`InferenceEngine`.
    * **No external APIs** – all replies are generated from deterministic
      templates.
    * **No persistent storage** – everything lives in RAM (v1).
    """

    def __init__(
        self,
        inference_engine: InferenceEngine,
        max_history: int = 10,
    ) -> None:
        """Initialize conversational memory.

        Args:
            inference_engine: Any object providing a callable
                ``run_full_inference(text: str) -> dict`` method.
                Duck-typed for compatibility with Streamlit hot-reloads.
            max_history: Maximum number of user+assistant turns kept in
                memory. Older turns are dropped FIFO. Defaults to ``10``.

        Raises:
            TypeError: If ``inference_engine`` is ``None`` or does not provide
                a callable ``run_full_inference`` method.
            ValueError: If ``max_history`` is not a positive integer.
        """
        if inference_engine is None:
            raise TypeError("inference_engine cannot be None.")
        if not hasattr(inference_engine, "run_full_inference"):
            raise TypeError(
                f"inference_engine must provide a 'run_full_inference' method. "
                f"Got {type(inference_engine).__name__}"
            )
        if not callable(getattr(inference_engine, "run_full_inference")):
            raise TypeError(
                f"inference_engine.run_full_inference must be callable. "
                f"Got {type(getattr(inference_engine, 'run_full_inference'))}"
            )
        if max_history < 1:
            raise ValueError("max_history must be a positive integer.")

        self._inference_engine = inference_engine
        self._max_history = max_history

        # -- Short-term memory --
        self._history: List[_Message] = []
        self._emotion_log: List[_EmotionSnapshot] = []

        # -- Repetition guard --
        self._recent_root_causes: List[str] = []
        self._recent_suggestions: Set[str] = set()
        self._response_counter: int = 0

        # -- Topic tracking for contextual follow-ups --
        self._recent_topics: List[str] = []
        self._used_follow_ups: Set[str] = set()

        # -- Conversational pacing and naturalness --
        self._recent_empathy_openers: List[str] = []
        self._recent_encouragements: List[str] = []
        self._consecutive_questions: int = 0
        self._last_response_style: str = "none"

        # -- Longitudinal state weighting --
        self._state_frequency: Dict[str, int] = {}

        # -- Hybrid response assembler for natural conversational flow --
        self._hybrid_assembler = HybridResponseAssembler()

        # -- Template bank (loaded lazily so tests can swap easily) --
        self._templates = self._load_templates()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_user_message(self, text: str) -> None:
        """Record a raw user utterance without running inference.

        Useful when the caller wants to buffer messages before calling
        :meth:`generate_response`.

        Args:
            text: User input text.

        Raises:
            ValueError: If ``text`` is ``None`` or empty after stripping.
        """
        self._validate_text(text)
        self._history.append(_Message(role="user", content=text.strip()))
        self._trim_history()

    def generate_response(self, text: str) -> Dict[str, Any]:
        """Process a user message end-to-end and return a structured reply.

        The method performs the following steps:

        1. Validates input.
        2. Stores the user message.
        3. Runs inference via the injected :class:`InferenceEngine`.
        4. Stores the emotional snapshot.
        5. Builds a supportive reply (risk-aware + cause-aware).
        6. Generates a context-aware follow-up question.
        7. Stores the assistant turn.

        Args:
            text: Raw user input text.

        Returns:
            A structured dictionary:

            * ``response`` (``str``) – primary supportive message.
            * ``follow_up`` (``str``) – short follow-up question.
            * ``emotion_context`` (``dict``) – current emotional snapshot.
            * ``risk`` (``dict``) – risk score and level from inference.
            * ``planner`` (``dict``) – planner type and plan.
            * ``history_length`` (``int``) – current number of turns.

        Raises:
            ValueError: If ``text`` is ``None`` or empty after stripping.
        """
        self._validate_text(text)

        # 1. Store user message
        user_msg = _Message(role="user", content=text.strip())
        self._history.append(user_msg)

        # 2. Run inference
        inference_result = self._inference_engine.run_full_inference(text)

        # 3. Extract emotion snapshot
        current_emotion = self._build_emotion_snapshot(inference_result)
        self._emotion_log.append(current_emotion)
        if len(self._emotion_log) > self._max_history:
            self._emotion_log = self._emotion_log[-self._max_history :]

        # 4. Detect emotional shift (continuity)
        prev_emotion = self._emotion_log[-2] if len(self._emotion_log) >= 2 else None
        shift = self._detect_emotional_shift(prev_emotion, current_emotion)

        # 5. Build supportive reply
        response_text = self._compose_response(
            inference_result, current_emotion, shift, text
        )

        # 6. Follow-up question
        follow_up_text = self._compose_follow_up(
            inference_result, current_emotion, shift, text
        )

        # 7. Store assistant turn
        assistant_msg = _Message(
            role="assistant",
            content=response_text,
            metadata={
                "follow_up": follow_up_text,
                "emotion_context": current_emotion.to_dict(),
            },
        )
        self._history.append(assistant_msg)
        self._trim_history()

        return {
            "response": response_text,
            "follow_up": follow_up_text,
            "emotion_context": current_emotion.to_dict(),
            "risk": inference_result.get("risk", {}),
            "root_causes": inference_result.get("root_causes", {}),
            "planner": inference_result.get("planner", {}),
            "history_length": len(self._history),
        }

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Return a JSON-safe snapshot of the conversation history.

        Each entry is a dict with keys ``role``, ``content``, ``timestamp``,
        and optionally ``metadata``.
        """
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp,
                **msg.metadata,
            }
            for msg in self._history
        ]

    def clear_history(self) -> None:
        """Remove all messages and emotion snapshots from memory."""
        self._history.clear()
        self._emotion_log.clear()
        self._recent_topics.clear()
        self._used_follow_ups.clear()
        self._recent_root_causes.clear()
        self._recent_suggestions.clear()
        self._recent_empathy_openers.clear()
        self._recent_encouragements.clear()
        self._consecutive_questions = 0
        self._last_response_style = "none"
        self._state_frequency.clear()
        self._hybrid_assembler.clear_tracking()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_text(text: Optional[str]) -> None:
        if text is None:
            raise ValueError("Input text cannot be None.")
        if not text.strip():
            raise ValueError("Input text cannot be empty or whitespace only.")

    def _trim_history(self) -> None:
        if len(self._history) > self._max_history:
            dropped = self._history[: len(self._history) - self._max_history]
            self._history = self._history[-self._max_history :]
            # Drop associated emotion log entries when user messages rotate out
            self._emotion_log = self._emotion_log[-self._max_history :]
            # Update repetition guard from remaining history
            self._recent_root_causes = [
                e.top_root_cause for e in self._emotion_log
            ]

    @staticmethod
    def _build_emotion_snapshot(result: Dict[str, Any]) -> _EmotionSnapshot:
        emotion = result.get("emotion", {})
        risk = result.get("risk", {})
        root_causes = result.get("root_causes", {})
        return _EmotionSnapshot(
            depression_score=float(emotion.get("depression_score", 0.0)),
            anxiety_score=float(emotion.get("anxiety_score", 0.0)),
            risk_level=str(risk.get("level", "LOW")),
            top_root_cause=str(root_causes.get("top_root_cause", "none")),
            risk_score=float(risk.get("score", 0.0)),
        )

    def _detect_emotional_shift(
        self,
        prev: Optional[_EmotionSnapshot],
        curr: _EmotionSnapshot,
    ) -> str:
        """Return a short label describing the emotional trend."""
        if prev is None:
            return "first_message"

        dep_delta = curr.depression_score - prev.depression_score
        anx_delta = curr.anxiety_score - prev.anxiety_score
        risk_changed = curr.risk_level != prev.risk_level

        if risk_changed:
            if curr.risk_score > prev.risk_score:
                return "worsening"
            return "improving"

        if dep_delta > 0.1 or anx_delta > 0.1:
            return "worsening"
        if dep_delta < -0.1 or anx_delta < -0.1:
            return "improving"

        return "stable"

    def _extract_topics(self, text: str) -> List[str]:
        """Extract relevant topics from user text using keyword matching.
        
        Args:
            text: User input text.
            
        Returns:
            List of detected topic names in order of relevance.
        """
        text_lower = text.lower()
        detected_topics = []
        
        for topic_name, config in TOPIC_CONFIG.items():
            for keyword in config["keywords"]:
                if keyword.lower() in text_lower:
                    detected_topics.append(topic_name)
                    break  # Only count each topic once per message
        
        return detected_topics

    def _get_topic_acknowledgement(self, topics: List[str]) -> Optional[str]:
        """Get topic-specific acknowledgement for detected topics.
        
        Args:
            topics: List of detected topic names.
            
        Returns:
            Topic acknowledgement string or None if no topics detected.
        """
        if not topics:
            return None
            
        # Use the first detected topic for acknowledgement
        topic = topics[0]
        if topic in TOPIC_CONFIG:
            acknowledgements = TOPIC_CONFIG[topic]["acknowledgements"]
            return self._pick_variant(acknowledgements)
        
        return None

    def _get_topic_follow_up(self, topics: List[str]) -> Optional[str]:
        """Get contextual follow-up question for detected topics.
        
        Args:
            topics: List of detected topic names.
            
        Returns:
            Topic-specific follow-up question or None if no suitable follow-up.
        """
        if not topics:
            return None
            
        # Try each detected topic in order
        for topic in topics:
            if topic in TOPIC_CONFIG:
                follow_ups = TOPIC_CONFIG[topic]["follow_ups"]
                
                # Find a follow-up that hasn't been used recently
                available = [fu for fu in follow_ups if fu not in self._used_follow_ups]
                
                if available:
                    selected = self._pick_variant(available)
                    self._used_follow_ups.add(selected)
                    
                    # Keep only recent 5 follow-ups to allow rotation
                    if len(self._used_follow_ups) > 5:
                        self._used_follow_ups = set(list(self._used_follow_ups)[-5:])
                    
                    return selected
        
        return None

    def _update_topic_history(self, topics: List[str]) -> None:
        """Update recent topics tracking.
        
        Args:
            topics: List of detected topic names.
        """
        for topic in topics:
            if topic not in self._recent_topics:
                self._recent_topics.append(topic)
        
        # Keep only last 10 topics
        if len(self._recent_topics) > 10:
            self._recent_topics = self._recent_topics[-10:]

    def _should_use_empathy_opener(self) -> bool:
        """Probabilistically decide whether to use empathy opener."""
        # Reduce usage if used recently
        recent_count = len(self._recent_empathy_openers)
        if recent_count >= 3:
            return False
        
        # 60% chance normally, 30% if used recently, 20% if used very recently
        if recent_count == 0:
            return self._response_counter % 10 < 6
        elif recent_count == 1:
            return self._response_counter % 10 < 3
        else:
            return self._response_counter % 10 < 2

    def _should_use_encouragement(self, emotion: _EmotionSnapshot) -> bool:
        """Decide whether to add encouragement based on context."""
        # Only for moderate/high risk, and use sparingly
        if emotion.risk_level not in ("MODERATE", "HIGH"):
            return False
        
        # Check recent usage
        recent_count = len(self._recent_encouragements)
        if recent_count >= 2:
            return False
        
        # 40% chance for high risk, 25% for moderate
        if emotion.risk_level == "HIGH":
            return self._response_counter % 10 < 4
        else:
            return self._response_counter % 10 < 3

    def _should_ask_question(self) -> bool:
        """Decide whether to end with a follow-up question."""
        # Don't ask questions too frequently
        if self._consecutive_questions >= 2:
            return False
        
        # 70% chance normally, but reduce if asked recently
        if self._consecutive_questions == 0:
            return self._response_counter % 10 < 7
        elif self._consecutive_questions == 1:
            return self._response_counter % 10 < 4
        else:
            return False

    def _select_response_style(self, emotion: _EmotionSnapshot, topics: List[str]) -> str:
        """Select response style based on emotional state and context."""
        # If escalating, prefer grounding/minimal
        if emotion.risk_level == "HIGH":
            if self._last_response_style in ["grounding", "minimal"]:
                return "validating"
            else:
                return "grounding"
        
        # If casual/low risk, vary more
        if emotion.risk_level == "LOW":
            styles = ["reflective", "exploratory", "validating"]
            if self._last_response_style in styles:
                styles.remove(self._last_response_style)
            return styles[self._response_counter % len(styles)]
        
        # Moderate risk - balance between styles
        styles = ["reflective", "validating", "grounding"]
        if self._last_response_style in styles:
            styles.remove(self._last_response_style)
        return styles[self._response_counter % len(styles)]

    def _update_conversation_memory(self, used_opener: str = None, 
                                 used_encouragement: str = None,
                                 asked_question: bool = False) -> None:
        """Update conversational memory tracking."""
        if used_opener:
            self._recent_empathy_openers.append(used_opener)
            if len(self._recent_empathy_openers) > 3:
                self._recent_empathy_openers.pop(0)
        
        if used_encouragement:
            self._recent_encouragements.append(used_encouragement)
            if len(self._recent_encouragements) > 2:
                self._recent_encouragements.pop(0)
        
        if asked_question:
            self._consecutive_questions += 1
        else:
            self._consecutive_questions = 0

    # ------------------------------------------------------------------
    # Templates
    # ------------------------------------------------------------------

    @staticmethod
    def _load_templates() -> Dict[str, Any]:
        """Return the rule-based response template bank.

        Each template slot holds a *list* of equivalent variants so the
        engine can rotate responses and avoid robotic repetition.
        """
        return {
            "risk_greeting": {
                "LOW": [
                    "Thank you for sharing that with me.",
                    "I'm glad you felt comfortable telling me that.",
                ],
                "MODERATE": [
                    "I appreciate you opening up to me — that takes courage.",
                    "It means a lot that you're sharing this with me.",
                ],
                "HIGH": [
                    "I'm really glad you reached out. You are not alone in this.",
                    "Thank you for trusting me with how you're feeling right now.",
                ],
            },
            "emotion_aware": {
                "depression_high": [
                    "It sounds like things feel really heavy right now.",
                    "I can hear the weight you're carrying at the moment.",
                ],
                "depression_moderate": [
                    "It seems like you've been carrying a lot lately.",
                    "I can sense that things have been feeling difficult for you.",
                ],
                "depression_low": [
                    "I'm glad things feel manageable at the moment.",
                    "It's good to hear you're not feeling too weighed down right now.",
                ],
                "anxiety_high": [
                    "I can hear how overwhelmed your mind feels right now.",
                    "It sounds like your thoughts are racing and it feels hard to slow down.",
                ],
                "anxiety_moderate": [
                    "It sounds like there's a lot swirling around in your head.",
                    "I can sense some restlessness in what you're describing.",
                ],
                "anxiety_low": [
                    "It's good to hear you feeling relatively calm.",
                    "I'm glad your mind feels a bit more settled right now.",
                ],
            },
            "root_cause_ack": {
                "perfectionism": [
                    "Trying to make everything perfect can be exhausting.",
                    "Holding yourself to such high standards is really draining.",
                ],
                "fear_of_failure": [
                    "Fear of not doing well can be a powerful paralyser.",
                    "Worrying about how things might turn out can freeze us completely.",
                ],
                "lack_of_interest": [
                    "Losing interest in things you used to care about is hard.",
                    "When motivation disappears, even small tasks can feel impossible.",
                ],
                "environment_distraction": [
                    "Distractions around us can make focus so difficult.",
                    "It's tough when your surroundings keep pulling your attention away.",
                ],
                "dopamine_addiction": [
                    "It's easy to get pulled into quick dopamine loops these days.",
                    "Those little instant-reward habits can quietly steal a lot of our time.",
                ],
                "none": [
                    "It's okay to feel unclear about what's driving things right now.",
                    "Sometimes we don't know exactly why we feel off — and that's completely valid.",
                ],
            },
            "follow_up": {
                "first_message": [
                    "Would you like to tell me a little more about what's been going on?",
                    "How long have you been feeling this way?",
                ],
                "worsening": [
                    "Is there something specific that triggered this change?",
                    "Would it help to talk through what feels hardest right now?",
                ],
                "improving": [
                    "What's helping you feel a bit better today?",
                    "It's great to hear things feel lighter — what's shifted for you?",
                ],
                "stable": [
                    "Is there anything else on your mind you'd like to share?",
                    "How are you feeling about the rest of your day?",
                ],
            },
            # Response style modes for natural conversation
            "response_styles": {
                "reflective": [
                    "That sounds really exhausting.",
                    "That kind of pressure can quietly build up over time.",
                    "It sounds like you've been carrying this for a while.",
                    "That can wear a person down after a bit.",
                ],
                "validating": [
                    "Anyone under that pressure would struggle.",
                    "It makes complete sense that you'd feel that way.",
                    "That's a completely understandable reaction.",
                    "Most people would find that really difficult.",
                ],
                "exploratory": [
                    "What part has been hardest lately?",
                    "When did you start noticing this pattern?",
                    "How does this usually show up for you?",
                    "What makes this feel different from before?",
                ],
                "grounding": [
                    "It sounds like your mind hasn't had much rest.",
                    "Your body and mind are probably asking for a break.",
                    "That sounds like it's taking a lot of energy right now.",
                    "Everything feels harder when we're running on empty.",
                ],
                "minimal": [
                    "That sounds really difficult.",
                    "I can hear how heavy that feels.",
                    "That sounds exhausting.",
                    "That sounds really challenging.",
                ],
            },
            # Selective encouragement phrases (used sparingly)
            "encouragement": {
                "gentle": [
                    "Small steps still count.",
                    "Be gentle with yourself today.",
                    "Progress isn't always linear.",
                    "Even resting is progress.",
                ],
                "context_specific": [
                    "That kind of pressure can be really draining.",
                    "You're carrying more than you realize.",
                    "It takes strength to acknowledge this.",
                ],
            },
        }

    def _pick_variant(self, pool: List[str]) -> str:
        """Rotate through a list of template variants using a simple counter."""
        if not pool:
            return ""
        idx = self._response_counter % len(pool)
        return pool[idx]

    def _compose_response(
        self,
        result: Dict[str, Any],
        emotion: _EmotionSnapshot,
        shift: str,
        user_text: str,
    ) -> str:
        """Build a context-aware therapeutic reply using the adaptive decision layer."""
        # Extract topics from user message (still used for memory tracking)
        topics = self._extract_topics(user_text)
        self._update_topic_history(topics)

        # Build adaptive state from inference outputs
        state = build_conversation_state(result, user_text)
        adaptive = generate_adaptive_response(state, self._state_frequency)
        parts: List[str] = [adaptive["response"]]

        # Topic-aware acknowledgement appended when relevant
        topic_ack = self._get_topic_acknowledgement(topics)
        if topic_ack and topic_ack not in adaptive["response"]:
            parts.append(topic_ack)

        # Continuity comment (only for significant shifts)
        if shift == "worsening" and emotion.risk_level in ("MODERATE", "HIGH"):
            parts.append(self._pick_variant([
                "Things feel like they've gotten harder lately.",
                "I notice the pressure has increased since we last spoke.",
            ]))
        elif shift == "improving":
            parts.append(self._pick_variant([
                "It sounds like there's some relief showing through.",
                "I'm glad to hear things feel a bit lighter.",
            ]))

        # Update conversation memory (track that we generated a response)
        self._update_conversation_memory(None, None, False)
        self._response_counter += 1

        # Update root cause tracking
        root_cause = emotion.top_root_cause
        self._recent_root_causes.append(root_cause)
        if len(self._recent_root_causes) > 3:
            self._recent_root_causes.pop(0)

        # Update longitudinal state frequency for escalation
        detected = adaptive["detected_state"]
        base_state = detected.replace("recurrent_", "")
        self._state_frequency[base_state] = self._state_frequency.get(base_state, 0) + 1

        return "\n\n".join(p for p in parts if p)

    def _compose_follow_up(
        self,
        result: Dict[str, Any],
        emotion: _EmotionSnapshot,
        shift: str,
        user_text: str,
    ) -> str:
        """Pick a state-aware follow-up question that hasn't been asked recently."""
        # Decide whether to ask a question at all
        if not self._should_ask_question():
            return ""  # Return empty string for no follow-up

        # Primary: adaptive therapeutic follow-up based on detected state
        state = build_conversation_state(result, user_text)
        adaptive_fu = generate_adaptive_follow_up(state, self._state_frequency)

        # Guard against repetition for adaptive follow-ups
        if adaptive_fu not in self._used_follow_ups:
            self._used_follow_ups.add(adaptive_fu)
            if len(self._used_follow_ups) > 5:
                self._used_follow_ups = set(list(self._used_follow_ups)[-5:])
            self._update_conversation_memory(asked_question=True)
            return adaptive_fu

        # Secondary: topic-aware follow-up
        topics = self._extract_topics(user_text)
        topic_follow_up = self._get_topic_follow_up(topics)
        if topic_follow_up and topic_follow_up not in self._used_follow_ups:
            self._used_follow_ups.add(topic_follow_up)
            if len(self._used_follow_ups) > 5:
                self._used_follow_ups = set(list(self._used_follow_ups)[-5:])
            self._update_conversation_memory(asked_question=True)
            return topic_follow_up

        # Fallback: emotion-based follow-up from static templates
        pool = self._templates["follow_up"].get(shift, self._templates["follow_up"]["stable"])
        for candidate in pool:
            if candidate not in self._recent_suggestions:
                self._recent_suggestions.add(candidate)
                if len(self._recent_suggestions) > 6:
                    self._recent_suggestions.clear()
                self._update_conversation_memory(asked_question=True)
                return candidate

        # All exhausted — return the first one and reset guard
        self._recent_suggestions.clear()
        self._update_conversation_memory(asked_question=True)
        return pool[0]
