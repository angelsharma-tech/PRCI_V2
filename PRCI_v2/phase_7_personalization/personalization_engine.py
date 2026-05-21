"""
Personalization & Feedback Engine

Tracks user feedback to adapt future
interventions over time.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

# Import from intervention engine
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase_6_intervention'))
from intervention_engine import Intervention, InterventionType


class FeedbackType(Enum):
    """
    Types of user feedback supported by the system.
    """
    RATING = "rating"           # 1-5 star rating
    IMPLEMENTATION = "implementation"  # Whether user implemented intervention
    EFFECTIVENESS = "effectiveness"    # Perceived effectiveness
    PREFERENCE = "preference"         # User preference for intervention type
    OUTCOME = "outcome"         # Actual outcome measurement


class FeedbackSource(Enum):
    """
    Sources of user feedback.
    """
    DIRECT = "direct"          # Explicit user feedback
    BEHAVIORAL = "behavioral"   # Inferred from behavior
    ACADEMIC = "academic"       # Academic performance changes
    SYSTEM = "system"          # System usage patterns


@dataclass
class UserFeedback:
    """
    Structure representing user feedback on interventions.
    
    Attributes:
        user_id: Unique identifier for the user
        intervention_id: Identifier for the intervention
        feedback_type: Type of feedback provided
        feedback_data: Actual feedback content
        source: Source of the feedback
        timestamp: When feedback was provided
        context: Additional context information
    """
    user_id: str
    intervention_id: str
    feedback_type: FeedbackType
    feedback_data: Dict[str, Any]
    source: FeedbackSource
    timestamp: datetime
    context: Dict[str, Any]


@dataclass
class UserProfile:
    """
    Structure representing user personalization profile.
    
    Attributes:
        user_id: Unique identifier for the user
        intervention_preferences: Preferred intervention types
        effectiveness_weights: Weights for different intervention types
        risk_sensitivity: User's sensitivity to risk levels
        time_preferences: Preferred time requirements
        difficulty_preference: Preferred difficulty levels
        learning_style: User's learning style preferences
        cultural_factors: Cultural and personal value factors
        last_updated: When profile was last updated
        feedback_history: History of user feedback
    """
    user_id: str
    intervention_preferences: Dict[InterventionType, float]
    effectiveness_weights: Dict[InterventionType, float]
    risk_sensitivity: float
    time_preferences: Dict[str, float]
    difficulty_preference: int
    learning_style: str
    cultural_factors: List[str]
    last_updated: datetime
    feedback_history: List[UserFeedback]


class PersonalizationEngine:
    """
    Core personalization and feedback processing engine.
    
    This engine tracks user feedback, adapts intervention recommendations,
    and maintains personalized user profiles to improve system effectiveness
    over time through continuous learning.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the personalization engine.
        
        Args:
            config: Configuration parameters for personalization
        """
        self.config = config or {}
        self.user_profiles = {}  # In-memory storage for demo
        self.learning_rate = self.config.get('learning_rate', 0.1)
        self.feedback_weight_decay = self.config.get('feedback_weight_decay', 0.95)
        self.min_feedback_threshold = self.config.get('min_feedback_threshold', 5)
    
    def update(self, user_id: str, feedback: Dict[str, Any]) -> bool:
        """
        Update user profile based on
        interaction outcomes.
        
        Args:
            user_id: Unique identifier for the user
            feedback: Feedback data from user interaction
            
        Returns:
            bool: True if update successful, False otherwise
            
        TODO (Phase-7):
        - Implement feedback scoring algorithms
        - Add adaptive weighting mechanisms
        - Update user preferences and weights
        - Apply learning rate adjustments
        - Validate feedback quality and consistency
        """
        try:
            # Parse and validate feedback
            parsed_feedback = self._parse_feedback(user_id, feedback)
            if not parsed_feedback:
                return False
            
            # Get or create user profile
            user_profile = self._get_or_create_profile(user_id)
            
            # Process different types of feedback
            self._process_feedback(user_profile, parsed_feedback)
            
            # Update profile weights and preferences
            self._update_profile_weights(user_profile)
            
            # Save updated profile
            self._save_profile(user_profile)
            
            return True
            
        except Exception as e:
            # Log error and return failure
            print(f"Error updating user profile: {e}")
            return False
    
    def get_personalized_recommendations(self, user_id: str, 
                                      candidate_interventions: List[Intervention]) -> List[Intervention]:
        """
        Get personalized recommendations based on user profile.
        
        Args:
            user_id: Unique identifier for the user
            candidate_interventions: List of candidate interventions
            
        Returns:
            List[Intervention]: Personalized and ranked interventions
            
        TODO (Phase-7):
        - Implement personalization algorithm
        - Apply user preference weighting
        - Consider historical effectiveness
        - Add contextual personalization
        - Rank by predicted effectiveness
        """
        user_profile = self._get_profile(user_id)
        if not user_profile:
            return candidate_interventions
        
        # Score interventions based on user profile
        scored_interventions = []
        for intervention in candidate_interventions:
            score = self._calculate_intervention_score(intervention, user_profile)
            scored_interventions.append((intervention, score))
        
        # Sort by score and return top recommendations
        scored_interventions.sort(key=lambda x: x[1], reverse=True)
        return [intervention for intervention, score in scored_interventions]
    
    def _parse_feedback(self, user_id: str, feedback: Dict[str, Any]) -> Optional[UserFeedback]:
        """
        Parse and validate raw feedback data.
        
        Args:
            user_id: Unique identifier for the user
            feedback: Raw feedback data
            
        Returns:
            UserFeedback: Parsed feedback object or None if invalid
            
        TODO (Phase-7):
        - Implement comprehensive feedback parsing
        - Add data validation and sanitization
        - Include feedback type detection
        - Add quality scoring for feedback
        """
        try:
            # Validate required fields
            if not all(key in feedback for key in ['intervention_id', 'feedback_type', 'feedback_data']):
                return None
            
            # Create feedback object
            return UserFeedback(
                user_id=user_id,
                intervention_id=feedback['intervention_id'],
                feedback_type=FeedbackType(feedback['feedback_type']),
                feedback_data=feedback['feedback_data'],
                source=FeedbackSource(feedback.get('source', 'direct')),
                timestamp=datetime.now(),
                context=feedback.get('context', {})
            )
            
        except (ValueError, KeyError) as e:
            print(f"Invalid feedback format: {e}")
            return None
    
    def _get_or_create_profile(self, user_id: str) -> UserProfile:
        """
        Get existing user profile or create new one.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            UserProfile: User profile object
            
        TODO (Phase-7):
        - Implement profile retrieval from storage
        - Add profile validation and migration
        - Include default profile creation
        - Add profile version management
        """
        if user_id not in self.user_profiles:
            # Create new profile with defaults
            self.user_profiles[user_id] = UserProfile(
                user_id=user_id,
                intervention_preferences={int_type: 1.0 for int_type in InterventionType},
                effectiveness_weights={int_type: 1.0 for int_type in InterventionType},
                risk_sensitivity=0.5,
                time_preferences={'short': 0.3, 'medium': 0.5, 'long': 0.2},
                difficulty_preference=2,
                learning_style="visual",
                cultural_factors=[],
                last_updated=datetime.now(),
                feedback_history=[]
            )
        
        return self.user_profiles[user_id]
    
    def _get_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Get user profile if it exists.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            UserProfile: User profile or None if not found
            
        TODO (Phase-7):
        - Implement profile retrieval with caching
        - Add profile validation and repair
        - Include profile loading optimization
        - Add profile backup and recovery
        """
        return self.user_profiles.get(user_id)
    
    def _process_feedback(self, profile: UserProfile, feedback: UserFeedback) -> None:
        """
        Process different types of feedback and update profile.
        
        Args:
            profile: User profile to update
            feedback: Feedback to process
            
        TODO (Phase-7):
        - Implement comprehensive feedback processing
        - Add feedback type-specific handling
        - Include feedback quality weighting
        - Add temporal feedback weighting
        """
        # Add feedback to history
        profile.feedback_history.append(feedback)
        
        # Process based on feedback type
        if feedback.feedback_type == FeedbackType.RATING:
            self._process_rating_feedback(profile, feedback)
        elif feedback.feedback_type == FeedbackType.EFFECTIVENESS:
            self._process_effectiveness_feedback(profile, feedback)
        elif feedback.feedback_type == FeedbackType.PREFERENCE:
            self._process_preference_feedback(profile, feedback)
        elif feedback.feedback_type == FeedbackType.IMPLEMENTATION:
            self._process_implementation_feedback(profile, feedback)
    
    def _process_rating_feedback(self, profile: UserProfile, feedback: UserFeedback) -> None:
        """
        Process rating feedback and update intervention preferences.
        
        Args:
            profile: User profile to update
            feedback: Rating feedback
            
        TODO (Phase-7):
        - Implement rating-based preference updates
        - Add intervention type learning
        - Include rating normalization
        - Add temporal weighting for ratings
        """
        rating = feedback.feedback_data.get('rating', 0)
        intervention_type = feedback.feedback_data.get('intervention_type')
        
        if intervention_type and 1 <= rating <= 5:
            # Update intervention preference based on rating
            current_weight = profile.effectiveness_weights.get(intervention_type, 1.0)
            
            # Apply learning rate adjustment
            rating_normalized = (rating - 3) / 2.0  # Convert to [-1, 1] range
            weight_update = self.learning_rate * rating_normalized
            
            new_weight = current_weight + weight_update
            profile.effectiveness_weights[intervention_type] = max(0.1, new_weight)
    
    def _process_effectiveness_feedback(self, profile: UserProfile, feedback: UserFeedback) -> None:
        """
        Process effectiveness feedback and update weights.
        
        Args:
            profile: User profile to update
            feedback: Effectiveness feedback
            
        TODO (Phase-7):
        - Implement effectiveness-based learning
        - Add outcome-based weight updates
        - Include effectiveness normalization
        - Add long-term effectiveness tracking
        """
        effectiveness = feedback.feedback_data.get('effectiveness_score', 0.5)
        intervention_type = feedback.feedback_data.get('intervention_type')
        
        if intervention_type and 0 <= effectiveness <= 1:
            current_weight = profile.effectiveness_weights.get(intervention_type, 1.0)
            
            # Update weight based on effectiveness
            weight_update = self.learning_rate * (effectiveness - 0.5)
            new_weight = current_weight + weight_update
            
            profile.effectiveness_weights[intervention_type] = max(0.1, new_weight)
    
    def _process_preference_feedback(self, profile: UserProfile, feedback: UserFeedback) -> None:
        """
        Process preference feedback and update user preferences.
        
        Args:
            profile: User profile to update
            feedback: Preference feedback
            
        TODO (Phase-7):
        - Implement preference-based updates
        - Add learning style adaptation
        - Include time preference updates
        - Add difficulty preference learning
        """
        preferences = feedback.feedback_data
        
        # Update intervention type preferences
        if 'intervention_preferences' in preferences:
            for int_type, preference in preferences['intervention_preferences'].items():
                if int_type in InterventionType:
                    current = profile.intervention_preferences.get(int_type, 1.0)
                    update = self.learning_rate * (preference - current)
                    profile.intervention_preferences[int_type] = max(0.1, current + update)
        
        # Update other preferences
        if 'time_preference' in preferences:
            profile.time_preferences.update(preferences['time_preference'])
        
        if 'difficulty_preference' in preferences:
            profile.difficulty_preference = preferences['difficulty_preference']
    
    def _process_implementation_feedback(self, profile: UserProfile, feedback: UserFeedback) -> None:
        """
        Process implementation feedback and update weights.
        
        Args:
            profile: User profile to update
            feedback: Implementation feedback
            
        TODO (Phase-7):
        - Implement implementation-based learning
        - Add completion rate tracking
        - Include implementation difficulty assessment
        - Add implementation pattern recognition
        """
        implemented = feedback.feedback_data.get('implemented', False)
        intervention_type = feedback.feedback_data.get('intervention_type')
        
        if intervention_type:
            current_weight = profile.effectiveness_weights.get(intervention_type, 1.0)
            
            # Small adjustment for implementation feedback
            if implemented:
                weight_update = self.learning_rate * 0.1  # Positive reinforcement
            else:
                weight_update = -self.learning_rate * 0.05  # Slight negative
            
            new_weight = current_weight + weight_update
            profile.effectiveness_weights[intervention_type] = max(0.1, new_weight)
    
    def _update_profile_weights(self, profile: UserProfile) -> None:
        """
        Update profile weights based on accumulated feedback.
        
        Args:
            profile: User profile to update
            
        TODO (Phase-7):
        - Implement comprehensive weight updates
        - Add weight normalization
        - Include feedback decay application
        - Add weight smoothing algorithms
        """
        # Apply feedback weight decay to older feedback
        current_time = datetime.now()
        
        # Update last updated timestamp
        profile.last_updated = current_time
        
        # Normalize effectiveness weights to prevent unbounded growth
        total_weight = sum(profile.effectiveness_weights.values())
        if total_weight > 0:
            normalization_factor = len(profile.effectiveness_weights) / total_weight
            for int_type in profile.effectiveness_weights:
                profile.effectiveness_weights[int_type] *= normalization_factor
    
    def _calculate_intervention_score(self, intervention: Intervention, 
                                   profile: UserProfile) -> float:
        """
        Calculate personalization score for an intervention.
        
        Args:
            intervention: Intervention to score
            profile: User profile
            
        Returns:
            float: Personalization score
            
        TODO (Phase-7):
        - Implement comprehensive scoring algorithm
        - Add multi-factor scoring components
        - Include context-aware scoring
        - Add temporal scoring adjustments
        """
        score = 0.0
        
        # Base score from intervention type preference
        type_preference = profile.intervention_preferences.get(intervention.type, 1.0)
        score += type_preference * 0.4
        
        # Effectiveness weight for intervention type
        effectiveness = profile.effectiveness_weights.get(intervention.type, 1.0)
        score += effectiveness * 0.3
        
        # Difficulty preference alignment
        difficulty_match = 1.0 - abs(intervention.difficulty - profile.difficulty_preference) / 4.0
        score += difficulty_match * 0.2
        
        # Time preference alignment
        time_score = self._calculate_time_preference_score(intervention, profile)
        score += time_score * 0.1
        
        return score
    
    def _calculate_time_preference_score(self, intervention: Intervention, 
                                       profile: UserProfile) -> float:
        """
        Calculate time preference alignment score.
        
        Args:
            intervention: Intervention to score
            profile: User profile
            
        Returns:
            float: Time preference score
            
        TODO (Phase-7):
        - Implement time preference parsing
        - Add time requirement matching
        - Include flexibility scoring
        - Add temporal context consideration
        """
        # Placeholder implementation
        return 0.5
    
    def _save_profile(self, profile: UserProfile) -> None:
        """
        Save updated user profile.
        
        Args:
            profile: User profile to save
            
        TODO (Phase-7):
        - Implement persistent profile storage
        - Add profile backup and recovery
        - Include profile versioning
        - Add profile synchronization
        """
        # Placeholder implementation - in-memory storage
        self.user_profiles[profile.user_id] = profile
    
    def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """
        Get analytics and insights for a user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Dict[str, Any]: User analytics data
            
        TODO (Phase-7):
        - Implement comprehensive user analytics
        - Add progress tracking metrics
        - Include effectiveness measurements
        - Add trend analysis and insights
        """
        profile = self._get_profile(user_id)
        if not profile:
            return {}
        
        return {
            'preferred_intervention_types': sorted(
                profile.intervention_preferences.items(), 
                key=lambda x: x[1], 
                reverse=True
            ),
            'most_effective_types': sorted(
                profile.effectiveness_weights.items(),
                key=lambda x: x[1],
                reverse=True
            ),
            'total_feedback_count': len(profile.feedback_history),
            'last_updated': profile.last_updated,
            'risk_sensitivity': profile.risk_sensitivity
        }
    
    def reset_profile(self, user_id: str) -> bool:
        """
        Reset user profile to default values.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            bool: True if reset successful
            
        TODO (Phase-7):
        - Implement profile reset functionality
        - Add profile backup before reset
        - Include reset confirmation
        - Add reset logging and audit
        """
        if user_id in self.user_profiles:
            del self.user_profiles[user_id]
            return True
        return False
