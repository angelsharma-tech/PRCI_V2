"""Adaptive Therapeutic Response Orchestrator

This layer sits above the InferenceEngine outputs and dynamically routes
the conversation based on the user's detected emotional state.

Architecture:
    InferenceEngine → ConversationState → detect_conversation_state
                                          → adaptive response + follow_up

Design goals:
* No external LLM APIs — pure deterministic therapeutic logic.
* Context-aware instead of generic supportive replies.
* State-specific interventions and follow-ups.
* Preserves existing ML pipeline unchanged.
"""

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from .hybrid_assembler import HybridResponseAssembler

# Global hybrid assembler instance
_hybrid_assembler = HybridResponseAssembler()


# ============================================
# CONVERSATION STATE
# ============================================

@dataclass
class ConversationState:
    anxiety_score: float
    depression_score: float
    risk_level: str
    root_causes: Dict[str, float]
    user_message: str

    def dominant_root(self) -> Optional[str]:
        """Return the root cause with highest probability."""
        if not self.root_causes:
            return None
        return max(self.root_causes, key=self.root_causes.get)

    def root_cause_probability(self, name: str) -> float:
        """Return probability for a specific root cause, defaulting to 0.0."""
        return float(self.root_causes.get(name, 0.0))


# ============================================
# STATE DETECTION
# ============================================

_StateLabel = str


RECURRENCE_THRESHOLD = 3
"""How many times a state must appear in recent history to trigger escalation."""


def detect_conversation_state(
    state: ConversationState,
    state_frequency: Optional[Dict[str, int]] = None,
) -> _StateLabel:
    """Map emotional snapshot to a therapeutic state label.

    If a state has appeared >= RECURRENCE_THRESHOLD times in recent history,
    the label is escalated to its *recurrent* variant so the response layer
    can intensify interventions.
    """
    dom = state.dominant_root()
    freq = state_frequency or {}

    # HIGH ANXIETY (highest priority for safety)
    if state.anxiety_score >= 0.70:
        base = "high_anxiety"
    # DEPRESSIVE FATIGUE
    elif state.depression_score >= 0.70:
        base = "depressive_fatigue"
    # BURNOUT
    elif dom and (
        "environment_distraction" in dom.lower()
        or "lack_of_interest" in dom.lower()
    ):
        base = "burnout"
    # DOPAMINE OVERLOAD
    elif dom and "dopamine" in dom.lower():
        base = "dopamine_overload"
    # FEAR / PERFECTIONISM
    elif dom and (
        "fear" in dom.lower()
        or "perfectionism" in dom.lower()
    ):
        base = "performance_pressure"
    else:
        base = "general_support"

    # Escalate to recurrent variant if threshold crossed
    if freq.get(base, 0) >= RECURRENCE_THRESHOLD:
        return f"recurrent_{base}"
    return base


# ============================================
# RESPONSE STRATEGIES
# ============================================

def _anxiety_response(state: ConversationState) -> str:
    return (
        "I can help with that.\n\n"
        "Your responses suggest signs of anxiety-driven mental overload and "
        "excessive cognitive pressure. It sounds like your mind is struggling "
        "to slow down, especially under stress.\n\n"
        "Right now, the goal should not be 'maximum productivity.' "
        "The goal should be reducing mental overload first.\n\n"
        "Here are 3 immediate interventions:\n"
        "• reduce multitasking\n"
        "• avoid doom-scrolling during breaks\n"
        "• focus on one small task instead of everything together"
    )


def _depression_response(state: ConversationState) -> str:
    return (
        "I'm here with you.\n\n"
        "Your responses suggest emotional exhaustion, low motivation, and "
        "possible depressive fatigue patterns. This usually makes even simple "
        "tasks feel mentally heavy.\n\n"
        "Instead of forcing yourself into high productivity immediately, try "
        "rebuilding momentum gradually.\n\n"
        "Start with:\n"
        "• restoring sleep consistency\n"
        "• reducing isolation\n"
        "• completing very small achievable tasks\n"
        "• avoiding harsh self-judgment"
    )


def _burnout_response(state: ConversationState) -> str:
    return (
        "What you're describing sounds closer to sustained burnout than "
        "temporary tiredness.\n\n"
        "Your system may be overloaded mentally and emotionally, especially if "
        "you've been continuously pushing yourself without proper recovery.\n\n"
        "Right now your brain likely needs:\n"
        "• cognitive rest\n"
        "• reduced pressure\n"
        "• structured recovery\n"
        "• fewer stimulation cycles"
    )


def _dopamine_response(state: ConversationState) -> str:
    return (
        "I notice patterns that may be linked with overstimulation and "
        "dopamine exhaustion.\n\n"
        "When the brain constantly switches between scrolling, stimulation, and "
        "pressure, focus and motivation often collapse.\n\n"
        "Instead of trying to 'force discipline,' try reducing stimulation "
        "intensity first.\n\n"
        "You could start with:\n"
        "• app limits\n"
        "• scheduled breaks\n"
        "• reduced short-form content\n"
        "• deep-focus sessions with no notifications"
    )


def _performance_response(state: ConversationState) -> str:
    return (
        "Your responses suggest strong performance pressure and overthinking "
        "patterns.\n\n"
        "This often happens when fear of failure or perfectionism becomes "
        "mentally exhausting.\n\n"
        "The brain starts treating every task like a high-stakes evaluation, "
        "which creates procrastination and anxiety loops.\n\n"
        "Right now it may help to:\n"
        "• lower perfection expectations\n"
        "• focus on progress instead of outcomes\n"
        "• break tasks into smaller targets\n"
        "• reduce self-comparison"
    )


def _general_response(state: ConversationState) -> str:
    pool = [
        (
            "Thank you for sharing this honestly.\n\n"
            "It sounds like you're carrying a lot mentally right now, and that "
            "can slowly drain motivation and emotional energy.\n\n"
            "Let's take this step-by-step instead of trying to solve everything "
            "at once.\n\n"
            "What part feels hardest right now:\n"
            "focus, emotions, sleep, motivation, or stress?"
        ),
        (
            "I'm here to help.\n\n"
            "Your responses suggest mental fatigue and emotional pressure, but "
            "small structured changes can still make a meaningful difference.\n\n"
            "Instead of overwhelming yourself, let's identify the biggest source "
            "of strain first.\n\n"
            "What feels most exhausting lately?"
        ),
    ]
    return random.choice(pool)


# ============================================
# RECURRENT (ESCALATED) RESPONSES
# ============================================

def _recurrent_anxiety_response(state: ConversationState) -> str:
    return (
        "I've noticed this pattern of anxiety showing up repeatedly in our "
        "conversation.\n\n"
        "When anxiety becomes a recurring cycle, the nervous system can stay "
        "chronically activated, making it harder to rest even when you try.\n\n"
        "At this stage, short-term coping may not be enough. It's worth "
        "considering:\n"
        "• a structured daily grounding routine (same time, same place)\n"
        "• reducing caffeine and screen stimulation in the evening\n"
        "• brief breathing exercises before high-stress tasks\n"
        "• speaking with a mental-health professional if this persists\n\n"
        "What has helped you calm down even slightly in the past?"
    )


def _recurrent_depression_response(state: ConversationState) -> str:
    return (
        "This isn't the first time we've talked about feeling emotionally "
        "heavy, and I want you to know that pattern matters.\n\n"
        "Recurring low motivation and fatigue can signal that your system "
        "needs deeper support, not just willpower.\n\n"
        "Consider:\n"
        "• a consistent sleep-wake schedule, even on weekends\n"
        "• small social interactions, even brief ones\n"
        "• physical movement, however gentle\n"
        "• reducing alcohol or substance use that numbs emotions\n\n"
        "Have you been able to share how you're feeling with anyone close to you?"
    )


def _recurrent_burnout_response(state: ConversationState) -> str:
    return (
        "We've talked about burnout-like exhaustion before, and seeing it "
        "recur tells me your recovery systems aren't catching up.\n\n"
        "This isn't about trying harder. It's about protecting what energy "
        "you still have and rebuilding slowly.\n\n"
        "Priority actions now:\n"
        "• clear boundaries on work/study hours\n"
        "• one genuine rest activity per day (not just scrolling)\n"
        "• saying no to non-essential commitments\n"
        "• speaking to someone who can help reduce your load\n\n"
        "Is there anything you can delegate, postpone, or remove this week?"
    )


def _recurrent_dopamine_response(state: ConversationState) -> str:
    return (
        "The pattern of overstimulation keeps showing up. Your brain may be "
        "stuck in a loop where quick dopamine hits are replacing real rest "
        "and focus.\n\n"
        "Breaking this loop takes structure, not motivation.\n\n"
        "Try these stricter resets:\n"
        "• phone in another room during deep-work blocks\n"
        "• no short-form content before 10am or after 8pm\n"
        "• one full day per week with zero social media\n"
        "• replace one scrolling habit with a 10-minute walk\n\n"
        "Which of these feels hardest but also most necessary right now?"
    )


def _recurrent_performance_response(state: ConversationState) -> str:
    return (
        "Perfectionism and fear of failure have come up repeatedly. That "
        "pattern can create a self-reinforcing trap where every task feels "
        "like a judgment on your worth.\n\n"
        "This needs active reframing, not just encouragement.\n\n"
        "Practices to interrupt the loop:\n"
        "• deliberately submit work at 'good enough' on purpose\n"
        "• set time limits, not quality targets\n"
        "• track effort, not outcomes\n"
        "• notice when comparison is driving your stress\n\n"
        "What would 'good enough' look like on your current task?"
    )


def _recurrent_general_response(state: ConversationState) -> str:
    return (
        "I've been tracking our conversation, and some of the strain you've "
        "described seems to keep resurfacing.\n\n"
        "That repetition is valuable information — it usually means the root "
        "cause hasn't been addressed yet.\n\n"
        "Let's try to identify the single biggest source of pressure and "
        "focus only on that for now.\n\n"
        "Which one area — work, relationships, health, or habits — keeps "
        "coming up most?"
    )


# ============================================
# ADAPTIVE FOLLOW-UPS
# ============================================

def _anxiety_follow_up(state: ConversationState) -> str:
    return "Do your thoughts feel more overwhelming at night or during work/study situations?"


def _depression_follow_up(state: ConversationState) -> str:
    return "Have you also noticed losing interest in things you normally enjoy?"


def _burnout_follow_up(state: ConversationState) -> str:
    return "Have you been feeling emotionally drained for multiple weeks continuously?"


def _dopamine_follow_up(state: ConversationState) -> str:
    return "Do you feel your focus drops quickly after checking social media or short videos?"


def _performance_follow_up(state: ConversationState) -> str:
    return "Do you often delay tasks because you feel they must be done perfectly?"


def _general_follow_up(state: ConversationState) -> str:
    pool = [
        "Would you like to tell me a little more about what's been going on?",
        "How long have you been feeling this way?",
        "Is there anything else on your mind you'd like to share?",
    ]
    return random.choice(pool)


# ============================================
# MAIN ROUTERS
# ============================================

_RESPONSE_HANDLERS: Dict[str, Any] = {
    # Base states
    "high_anxiety": _anxiety_response,
    "depressive_fatigue": _depression_response,
    "burnout": _burnout_response,
    "dopamine_overload": _dopamine_response,
    "performance_pressure": _performance_response,
    "general_support": _general_response,
    # Recurrent (escalated) states
    "recurrent_high_anxiety": _recurrent_anxiety_response,
    "recurrent_depressive_fatigue": _recurrent_depression_response,
    "recurrent_burnout": _recurrent_burnout_response,
    "recurrent_dopamine_overload": _recurrent_dopamine_response,
    "recurrent_performance_pressure": _recurrent_performance_response,
    "recurrent_general_support": _recurrent_general_response,
}

_FOLLOW_UP_HANDLERS: Dict[str, Any] = {
    # Base states
    "high_anxiety": _anxiety_follow_up,
    "depressive_fatigue": _depression_follow_up,
    "burnout": _burnout_follow_up,
    "dopamine_overload": _dopamine_follow_up,
    "performance_pressure": _performance_follow_up,
    "general_support": _general_follow_up,
    # Recurrent states reuse same follow-ups (they're already diagnostic)
    "recurrent_high_anxiety": _anxiety_follow_up,
    "recurrent_depressive_fatigue": _depression_follow_up,
    "recurrent_burnout": _burnout_follow_up,
    "recurrent_dopamine_overload": _dopamine_follow_up,
    "recurrent_performance_pressure": _performance_follow_up,
    "recurrent_general_support": _general_follow_up,
}


def generate_adaptive_response(
    state: ConversationState,
    state_frequency: Optional[Dict[str, int]] = None,
) -> Dict[str, str]:
    """Route to the correct therapeutic response using hybrid assembly.

    Args:
        state: Current emotional snapshot.
        state_frequency: Optional count of how many times each state label
            has appeared in recent conversation history. Used to escalate
            to recurrent variants when a threshold is crossed.

    Returns:
        {"detected_state": str, "response": str}
    """
    detected = detect_conversation_state(state, state_frequency)
    
    # Use hybrid assembler for natural conversational flow
    result = _hybrid_assembler.assemble_response(
        state=detected,
        user_message=state.user_message,
        root_causes=state.root_causes,
        state_frequency=state_frequency,
        is_recurrent=detected.startswith("recurrent_"),
    )
    
    return {
        "detected_state": detected,
        "response": result["response"],
    }


def generate_adaptive_follow_up(
    state: ConversationState,
    state_frequency: Optional[Dict[str, int]] = None,
) -> str:
    """Return a state-aware follow-up question using hybrid assembly.

    Args:
        state: Current emotional snapshot.
        state_frequency: Optional historical frequency map for escalation.

    Returns:
        A single follow-up question string tailored to the detected state.
    """
    detected = detect_conversation_state(state, state_frequency)
    
    # Use hybrid assembler for contextual follow-up generation
    result = _hybrid_assembler.assemble_response(
        state=detected,
        user_message=state.user_message,
        root_causes=state.root_causes,
        state_frequency=state_frequency,
        is_recurrent=detected.startswith("recurrent_"),
    )
    
    return result["followup"]


# ============================================
# HELPER: Build ConversationState from inference dict
# ============================================

def build_conversation_state(
    inference_result: Dict[str, Any],
    user_message: str,
) -> ConversationState:
    """Construct a ConversationState from an InferenceEngine output dict.

    Defensively casts scores to float and coerces NaN/inf to 0.0 so FP16
    values never propagate into the adaptive decision layer.
    """
    emotion = inference_result.get("emotion", {})
    risk = inference_result.get("risk", {})
    root_causes = inference_result.get("root_causes", {})

    def _safe_float(v):
        try:
            f = float(v.item() if hasattr(v, "item") else v)
            if math.isnan(f) or math.isinf(f):
                return 0.0
            return f
        except Exception:
            return 0.0

    return ConversationState(
        anxiety_score=_safe_float(emotion.get("anxiety_score", 0.0)),
        depression_score=_safe_float(emotion.get("depression_score", 0.0)),
        risk_level=str(risk.get("level", "LOW")),
        root_causes={
            k: _safe_float(v) for k, v in root_causes.get("probabilities", {}).items()
        },
        user_message=user_message,
    )
