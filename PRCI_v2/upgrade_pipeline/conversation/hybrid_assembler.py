"""Hybrid Response Assembler for Natural Conversational Flow.

This module dynamically assembles responses from human-curated pools while
maintaining repetition suppression, behavioral continuity, and conversational
realism. It replaces fixed template responses with modular assembly.

Architecture:
    Emotional State → Pool Selection → Variant Selection → Response Assembly
                                    ↳ Repetition Suppression
                                    ↳ Contextual Topic Integration
                                    ↳ Pacing Variability
                                    ↳ Recurrent Escalation
"""

import random
from typing import Dict, List, Optional, Set, Tuple

from .conversational_pools import (
    get_response_pools,
    select_variant,
    get_state_vocabulary,
)


# ============================================
# RESPONSE ASSEMBLY CONFIGURATION
# ============================================

RESPONSE_PATTERNS = {
    "short": ["intro"],
    "medium": ["intro", "observation"],
    "deep": ["intro", "observation", "reasoning", "intervention"],
    "full": ["intro", "observation", "reasoning", "intervention"],
}

# Probability weights for response patterns
PATTERN_WEIGHTS = {
    "short": 0.15,      # 15% brief responses
    "medium": 0.35,     # 35% moderate responses  
    "deep": 0.40,       # 40% detailed responses
    "full": 0.10,       # 10% comprehensive responses
}

# Maximum history for repetition suppression
MAX_RECENT_PHRASES = 8
MAX_RECENT_INTERVENTIONS = 6
MAX_RECENT_FOLLOWUPS = 5


# ============================================
# REPETITION SUPPRESSION TRACKER
# ============================================

class RepetitionTracker:
    """Tracks recently used conversational fragments to avoid repetition."""
    
    def __init__(self):
        self._used_phrases: List[str] = []
        self._used_interventions: List[str] = []
        self._used_followups: List[str] = []
        self._used_vocabulary: List[str] = []
    
    def add_phrase(self, phrase: str) -> None:
        """Track a used conversational phrase."""
        self._used_phrases.append(phrase)
        if len(self._used_phrases) > MAX_RECENT_PHRASES:
            self._used_phrases.pop(0)
    
    def add_intervention(self, intervention: str) -> None:
        """Track a used intervention suggestion."""
        self._used_interventions.append(intervention)
        if len(self._used_interventions) > MAX_RECENT_INTERVENTIONS:
            self._used_interventions.pop(0)
    
    def add_followup(self, followup: str) -> None:
        """Track a used follow-up question."""
        self._used_followups.append(followup)
        if len(self._used_followups) > MAX_RECENT_FOLLOWUPS:
            self._used_followups.pop(0)
    
    def add_vocabulary(self, vocab: str) -> None:
        """Track used emotional vocabulary."""
        self._used_vocabulary.append(vocab)
        if len(self._used_vocabulary) > MAX_RECENT_PHRASES:
            self._used_vocabulary.pop(0)
    
    def is_phrase_recent(self, phrase: str) -> bool:
        """Check if a phrase was used recently."""
        return phrase in self._used_phrases
    
    def is_intervention_recent(self, intervention: str) -> bool:
        """Check if an intervention was used recently."""
        return intervention in self._used_interventions
    
    def is_followup_recent(self, followup: str) -> bool:
        """Check if a follow-up was used recently."""
        return followup in self._used_followups
    
    def is_vocabulary_recent(self, vocab: str) -> bool:
        """Check if vocabulary was used recently."""
        return vocab in self._used_vocabulary
    
    def clear(self) -> None:
        """Clear all tracking history."""
        self._used_phrases.clear()
        self._used_interventions.clear()
        self._used_followups.clear()
        self._used_vocabulary.clear()


# ============================================
# CONTEXTUAL TOPIC INTEGRATION
# ============================================

class TopicIntegrator:
    """Handles conditional topic mentions based on context support."""
    
    def __init__(self):
        self.topic_keywords = {
            "sleep": ["sleep", "insomnia", "tired", "exhausted", "rest", "fatigue", 
                     "can't sleep", "sleepless", "sleeping", "awake", "drowsy", "night"],
            "social": ["alone", "isolated", "friends", "people", "social", "lonely",
                      "connection", "relationships", "family", "talk to someone", "withdrawn"],
            "productivity": ["work", "study", "deadline", "focus", "assignment", "project",
                           "academic", "school", "university", "homework", "research", "grade"],
            "burnout": ["motivation", "drained", "exhausted", "overwhelmed", "can't",
                       "no energy", "tired of", "giving up", "burned out", "unmotivated"],
            "scrolling": ["phone", "social media", "scrolling", "apps", "notifications",
                         "screen", "digital", "online", "internet", "videos", "content"],
            "self_worth": ["worth", "value", "good enough", "failure", "success", "perfect",
                         "mistake", "error", "achievement", "performance", "criticism"]
        }
    
    def detect_topics(self, user_message: str, root_causes: Dict[str, float]) -> Set[str]:
        """Detect relevant topics from user message and root causes."""
        detected = set()
        message_lower = user_message.lower()
        
        # Check message keywords
        for topic, keywords in self.topic_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    detected.add(topic)
                    break
        
        # Check root causes for topic relevance
        for cause in root_causes:
            cause_lower = cause.lower()
            for topic, keywords in self.topic_keywords.items():
                for keyword in keywords:
                    if keyword in cause_lower:
                        detected.add(topic)
                        break
        
        return detected
    
    def should_mention_topic(self, topic: str, detected_topics: Set[str]) -> bool:
        """Determine if a topic should be mentioned based on context support."""
        return topic in detected_topics


# ============================================
# RESPONSE ASSEMBLY ENGINE
# ============================================

class HybridResponseAssembler:
    """Dynamically assembles natural-feeling responses from curated pools."""
    
    def __init__(self):
        self.repetition_tracker = RepetitionTracker()
        self.topic_integrator = TopicIntegrator()
    
    def assemble_response(
        self,
        state: str,
        user_message: str,
        root_causes: Dict[str, float],
        state_frequency: Optional[Dict[str, int]] = None,
        is_recurrent: bool = False,
    ) -> Dict[str, str]:
        """Assemble a dynamic response from human-curated pools.
        
        Args:
            state: Detected emotional state
            user_message: User's input message
            root_causes: Root cause probabilities
            state_frequency: Historical frequency for escalation
            is_recurrent: Whether this is a recurrent state
            
        Returns:
            {"response": str, "followup": str, "detected_state": str}
        """
        # Defensive input validation
        if not state:
            state = "general_support"
        if not user_message:
            user_message = ""
        if not root_causes:
            root_causes = {}
        
        # Debug prints
        print(f"[DEBUG] Assembling response for state: {state}")
        print(f"[DEBUG] Is recurrent: {is_recurrent}")
        
        # Get appropriate pools with fallback
        try:
            pools = get_response_pools(state)
            print(f"[DEBUG] Pool keys: {list(pools.keys())}")
        except Exception as e:
            print(f"[DEBUG] Error getting pools: {e}")
            pools = get_response_pools("general_support")
        
        # Validate pools have content
        for pool_name, pool_content in pools.items():
            if not pool_content:
                print(f"[DEBUG] Empty pool detected: {pool_name}")
                # Fallback to general support pools
                pools = get_response_pools("general_support")
                break
        
        # Detect contextual topics
        try:
            detected_topics = self.topic_integrator.detect_topics(user_message, root_causes)
            print(f"[DEBUG] Detected topics: {detected_topics}")
        except Exception as e:
            print(f"[DEBUG] Error detecting topics: {e}")
            detected_topics = set()
        
        # Select response pattern based on pacing
        try:
            pattern = self._select_response_pattern(is_recurrent)
            print(f"[DEBUG] Selected pattern: {pattern}")
        except Exception as e:
            print(f"[DEBUG] Error selecting pattern: {e}")
            pattern = ["intro", "observation"]  # Safe fallback
        
        # Assemble response components
        response_parts = []
        
        for component in pattern:
            try:
                if component == "intro":
                    if "intros" not in pools or not pools["intros"]:
                        intro = "I'm here to help."
                    else:
                        intro = self._select_intro(pools["intros"])
                    response_parts.append(intro)
                    self.repetition_tracker.add_phrase(intro)
                
                elif component == "observation":
                    if "observations" not in pools or not pools["observations"]:
                        observation = "Your responses suggest you're going through something challenging."
                    else:
                        observation = self._select_observation(
                            pools["observations"], 
                            detected_topics,
                            get_state_vocabulary(state)
                        )
                    response_parts.append(observation)
                    self.repetition_tracker.add_phrase(observation)
                
                elif component == "reasoning":
                    if "reasoning" not in pools or not pools["reasoning"]:
                        reasoning = "This situation can be difficult to navigate alone."
                    else:
                        reasoning = self._select_reasoning(
                            pools["reasoning"],
                            is_recurrent,
                            state_frequency or {}
                        )
                    response_parts.append(reasoning)
                    self.repetition_tracker.add_phrase(reasoning)
                
                elif component == "intervention":
                    if "interventions" not in pools or not pools["interventions"]:
                        intervention = "Consider taking small steps toward self-care."
                    else:
                        intervention = self._select_intervention(
                            pools["interventions"],
                            detected_topics,
                            is_recurrent
                        )
                    response_parts.append(intervention)
                    self.repetition_tracker.add_intervention(intervention)
                    
            except Exception as e:
                print(f"[DEBUG] Error assembling component {component}: {e}")
                # Add safe fallback
                response_parts.append("I'm here to support you through this.")
        
        # Generate follow-up with fallback
        try:
            if "followups" not in pools or not pools["followups"]:
                followup = "Would you like to tell me more about what you're experiencing?"
            else:
                followup = self._generate_followup(
                    pools["followups"],
                    detected_topics,
                    is_recurrent,
                    state_frequency or {}
                )
        except Exception as e:
            print(f"[DEBUG] Error generating followup: {e}")
            followup = "How can I best support you right now?"
        
        # Assemble final response
        full_response = "\n\n".join(response_parts)
        
        print(f"[DEBUG] Final response length: {len(full_response)}")
        print(f"[DEBUG] Followup: {followup}")
        
        return {
            "response": full_response,
            "followup": followup,
            "detected_state": state,
        }
    
    def _select_response_pattern(self, is_recurrent: bool) -> List[str]:
        """Select response pattern based on pacing and recurrence."""
        # Escalate to deeper patterns for recurrent states
        if is_recurrent:
            weights = {
                "short": 0.05,
                "medium": 0.20,
                "deep": 0.50,
                "full": 0.25,
            }
        else:
            weights = PATTERN_WEIGHTS
        
        patterns = list(weights.keys())
        probabilities = list(weights.values())
        selected = random.choices(patterns, weights=probabilities)[0]
        return RESPONSE_PATTERNS[selected]
    
    def _select_intro(self, intro_pool: List[str]) -> str:
        """Select an intro variant avoiding repetition."""
        return select_variant(intro_pool, set(self.repetition_tracker._used_phrases))
    
    def _select_observation(
        self, 
        observation_pool: List[str], 
        detected_topics: Set[str],
        vocabulary: List[str]
    ) -> str:
        """Select an observation with contextual vocabulary integration."""
        # Select base observation
        base_obs = select_variant(observation_pool, set(self.repetition_tracker._used_phrases))
        
        # Optionally integrate contextual vocabulary
        if vocabulary and random.random() < 0.3:  # 30% chance to add specific vocab
            available_vocab = [v for v in vocabulary if not self.repetition_tracker.is_vocabulary_recent(v)]
            if available_vocab:
                vocab_word = random.choice(available_vocab)
                self.repetition_tracker.add_vocabulary(vocab_word)
                # Natural integration would go here - for now just return base
                return base_obs
        
        return base_obs
    
    def _select_reasoning(
        self, 
        reasoning_pool: List[str], 
        is_recurrent: bool,
        state_frequency: Dict[str, int]
    ) -> str:
        """Select reasoning with escalation for recurrent states."""
        base_state = "recurrent_" if is_recurrent else ""
        
        # For recurrent states, prefer deeper reasoning
        if is_recurrent:
            # Filter for reasoning that acknowledges persistence
            persistent_reasoning = [r for r in reasoning_pool if any(
                word in r.lower() for word in ["persistent", "repeated", "ongoing", "continues", "chronic"]
            )]
            if persistent_reasoning:
                return select_variant(persistent_reasoning, set(self.repetition_tracker._used_phrases))
        
        return select_variant(reasoning_pool, set(self.repetition_tracker._used_phrases))
    
    def _select_intervention(
        self, 
        intervention_pool: List[str], 
        detected_topics: Set[str],
        is_recurrent: bool
    ) -> str:
        """Select intervention with topic integration and escalation."""
        # Filter interventions based on detected topics
        if detected_topics:
            topic_interventions = []
            for intervention in intervention_pool:
                for topic in detected_topics:
                    if any(keyword in intervention.lower() for keyword in self.topic_integrator.topic_keywords.get(topic, [])):
                        topic_interventions.append(intervention)
                        break
            
            if topic_interventions:
                pool = topic_interventions
            else:
                pool = intervention_pool
        else:
            pool = intervention_pool
        
        # For recurrent states, prefer more structured interventions
        if is_recurrent:
            structured_interventions = [i for i in pool if any(
                word in i.lower() for word in ["structure", "routine", "professional", "support", "boundaries"]
            )]
            if structured_interventions:
                pool = structured_interventions
        
        return select_variant(pool, set(self.repetition_tracker._used_interventions))
    
    def _generate_followup(
        self, 
        followup_pool: List[str], 
        detected_topics: Set[str],
        is_recurrent: bool,
        state_frequency: Dict[str, int]
    ) -> str:
        """Generate contextual follow-up with escalation."""
        # Filter followups based on detected topics
        if detected_topics:
            topic_followups = []
            for followup in followup_pool:
                for topic in detected_topics:
                    if any(keyword in followup.lower() for keyword in self.topic_integrator.topic_keywords.get(topic, [])):
                        topic_followups.append(followup)
                        break
            
            if topic_followups:
                pool = topic_followups
            else:
                pool = followup_pool
        else:
            pool = followup_pool
        
        # For recurrent states, prefer deeper followups
        if is_recurrent:
            deeper_followups = [f for f in pool if any(
                word in f.lower() for word in ["several", "multiple", "pattern", "persistent", "ongoing"]
            )]
            if deeper_followups:
                pool = deeper_followups
        
        return select_variant(pool, set(self.repetition_tracker._used_followups))
    
    def clear_tracking(self) -> None:
        """Clear all repetition tracking history."""
        self.repetition_tracker.clear()


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

def create_hybrid_assembler() -> HybridResponseAssembler:
    """Create a new hybrid response assembler instance."""
    return HybridResponseAssembler()


def assemble_hybrid_response(
    state: str,
    user_message: str,
    root_causes: Dict[str, float],
    state_frequency: Optional[Dict[str, int]] = None,
    assembler: Optional[HybridResponseAssembler] = None,
) -> Dict[str, str]:
    """Convenience function to assemble a hybrid response."""
    if assembler is None:
        assembler = create_hybrid_assembler()
    
    is_recurrent = state.startswith("recurrent_")
    
    try:
        return assembler.assemble_response(
            state=state,
            user_message=user_message,
            root_causes=root_causes,
            state_frequency=state_frequency,
            is_recurrent=is_recurrent,
        )
    except Exception as e:
        print(f"[DEBUG] Error in assemble_hybrid_response: {e}")
        # Return safe fallback
        return {
            "response": "I'm here to support you through this. Your responses suggest you're going through something challenging. This situation can be difficult to navigate alone. Consider taking small steps toward self-care.",
            "followup": "How can I best support you right now?",
            "detected_state": state,
        }
