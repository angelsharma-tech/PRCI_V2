"""
Intervention Service for PRCI v2
Phase 4.1 - Backend Stabilization & Architecture Refactor
"""

import random
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from config import INTERVENTION_TEMPLATES, MODEL_CONFIG
from utils.logging_utils import get_logger, PerformanceTimer, log_user_action

logger = get_logger(__name__)


class InterventionService:
    """
    Centralized intervention service for personalized recommendations
    """
    
    def __init__(self):
        self.user_intervention_history = []
        self.intervention_effectiveness = {}
    
    def get_personalized_interventions(
        self,
        root_cause: str,
        depression_score: float,
        anxiety_score: float,
        risk_level: str,
        user_preferences: Optional[Dict[str, Any]] = None,
        count: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get personalized interventions based on user's current state
        """
        try:
            with PerformanceTimer("intervention_generation", {
                "root_cause": root_cause,
                "risk_level": risk_level
            }):
                
                # Get base interventions for root cause
                base_interventions = self._get_base_interventions(root_cause)
                
                # Score and rank interventions based on user context
                scored_interventions = self._score_interventions(
                    base_interventions,
                    depression_score,
                    anxiety_score,
                    risk_level,
                    user_preferences or {}
                )
                
                # Get top interventions
                top_interventions = scored_interventions[:count]
                
                # Add metadata
                for i, intervention in enumerate(top_interventions):
                    intervention.update({
                        "id": f"intervention_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                        "root_cause": root_cause,
                        "risk_level": risk_level,
                        "generated_at": datetime.now().isoformat(),
                        "priority": self._calculate_priority(intervention, risk_level)
                    })
                
                # Log intervention generation
                log_user_action("interventions_generated", {
                    "root_cause": root_cause,
                    "risk_level": risk_level,
                    "count": len(top_interventions)
                })
                
                return top_interventions
                
        except Exception as e:
            logger.error(f"Error generating interventions: {e}")
            return self._get_fallback_interventions(count)
    
    def get_daily_intervention(
        self,
        user_id: Optional[str] = None,
        current_mood: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a daily intervention based on user's current state
        """
        try:
            with PerformanceTimer("daily_intervention"):
                # Select intervention type based on mood
                if current_mood:
                    intervention_type = self._map_mood_to_intervention_type(current_mood)
                else:
                    intervention_type = random.choice(["mindfulness", "activity", "social", "productivity"])
                
                # Get appropriate intervention
                intervention = self._get_daily_intervention_by_type(intervention_type)
                
                # Add metadata
                intervention.update({
                    "type": "daily",
                    "intervention_type": intervention_type,
                    "user_id": user_id,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "generated_at": datetime.now().isoformat()
                })
                
                return intervention
                
        except Exception as e:
            logger.error(f"Error generating daily intervention: {e}")
            return self._get_fallback_daily_intervention()
    
    def track_intervention_completion(
        self,
        intervention_id: str,
        user_feedback: Optional[str] = None,
        effectiveness_score: Optional[int] = None
    ) -> bool:
        """
        Track when user completes an intervention
        """
        try:
            completion_entry = {
                "intervention_id": intervention_id,
                "completed_at": datetime.now().isoformat(),
                "user_feedback": user_feedback,
                "effectiveness_score": effectiveness_score,
                "auto_tracked": False
            }
            
            self.user_intervention_history.append(completion_entry)
            
            # Update effectiveness tracking
            if effectiveness_score is not None:
                self._update_intervention_effectiveness(intervention_id, effectiveness_score)
            
            # Log completion
            log_user_action("intervention_completed", {
                "intervention_id": intervention_id,
                "effectiveness_score": effectiveness_score
            })
            
            logger.info(f"Intervention {intervention_id} marked as completed")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking intervention completion: {e}")
            return False
    
    def get_intervention_insights(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get insights about intervention effectiveness
        """
        try:
            with PerformanceTimer("intervention_insights", {"days": days}):
                cutoff_date = datetime.now() - timedelta(days=days)
                recent_completions = [
                    entry for entry in self.user_intervention_history
                    if datetime.fromisoformat(entry["completed_at"]) > cutoff_date
                ]
                
                if not recent_completions:
                    return {"message": "No intervention data available"}
                
                # Calculate completion statistics
                total_completions = len(recent_completions)
                avg_effectiveness = 0
                
                entries_with_scores = [
                    entry for entry in recent_completions
                    if entry.get("effectiveness_score") is not None
                ]
                
                if entries_with_scores:
                    avg_effectiveness = sum(entry["effectiveness_score"] for entry in entries_with_scores) / len(entries_with_scores)
                
                # Most effective intervention types
                type_effectiveness = {}
                for entry in entries_with_scores:
                    intervention_id = entry["intervention_id"]
                    intervention_type = self._extract_intervention_type(intervention_id)
                    
                    if intervention_type not in type_effectiveness:
                        type_effectiveness[intervention_type] = []
                    type_effectiveness[intervention_type].append(entry["effectiveness_score"])
                
                avg_by_type = {
                    int_type: sum(scores) / len(scores)
                    for int_type, scores in type_effectiveness.items()
                }
                
                insights = {
                    "period_days": days,
                    "total_completions": total_completions,
                    "average_effectiveness": avg_effectiveness,
                    "completion_rate": total_completions / days,  # Completions per day
                    "effectiveness_by_type": avg_by_type,
                    "most_effective_type": max(avg_by_type.items(), key=lambda x: x[1])[0] if avg_by_type else None,
                    "data_points": len(entries_with_scores),
                    "timestamp": datetime.now().isoformat()
                }
                
                return insights
                
        except Exception as e:
            logger.error(f"Error getting intervention insights: {e}")
            return {"error": str(e)}
    
    def get_adaptive_interventions(
        self,
        user_profile: Dict[str, Any],
        recent_scores: List[Dict[str, float]]
    ) -> List[Dict[str, Any]]:
        """
        Get interventions that adapt to user's progress and preferences
        """
        try:
            with PerformanceTimer("adaptive_interventions"):
                # Analyze recent trends
                trend_analysis = self._analyze_recent_trends(recent_scores)
                
                # Get user's preferred intervention types
                preferred_types = user_profile.get("preferred_intervention_types", [])
                
                # Get interventions based on current state and preferences
                adaptive_interventions = []
                
                # If user is improving, suggest maintenance interventions
                if trend_analysis.get("trend") == "improving":
                    adaptive_interventions.extend(self._get_maintenance_interventions(preferred_types))
                
                # If user is declining, suggest intensive interventions
                elif trend_analysis.get("trend") == "declining":
                    adaptive_interventions.extend(self._get_intensive_interventions(preferred_types))
                
                # If stable, suggest variety
                else:
                    adaptive_interventions.extend(self._get_variety_interventions(preferred_types))
                
                # Add adaptive metadata
                for intervention in adaptive_interventions:
                    intervention.update({
                        "adaptive": True,
                        "trend_analysis": trend_analysis,
                        "user_preferences_considered": True,
                        "generated_at": datetime.now().isoformat()
                    })
                
                return adaptive_interventions[:5]  # Return top 5
                
        except Exception as e:
            logger.error(f"Error generating adaptive interventions: {e}")
            return self._get_fallback_interventions(3)
    
    def _get_base_interventions(self, root_cause: str) -> List[str]:
        """
        Get base interventions for a root cause
        """
        return INTERVENTION_TEMPLATES.get(root_cause, [
            "Practice mindfulness and self-awareness.",
            "Take regular breaks throughout the day.",
            "Focus on one task at a time.",
            "Seek support from friends or family.",
            "Consider professional help if needed."
        ])
    
    def _score_interventions(
        self,
        interventions: List[str],
        depression_score: float,
        anxiety_score: float,
        risk_level: str,
        user_preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Score interventions based on user context
        """
        scored_interventions = []
        
        for intervention in interventions:
            score = 0.5  # Base score
            
            # Adjust based on risk level
            if risk_level == "HIGH":
                score += 0.3 if "professional" in intervention.lower() else 0.1
            elif risk_level == "MODERATE":
                score += 0.2 if "practice" in intervention.lower() else 0.1
            
            # Adjust based on depression score
            if depression_score > 0.6:
                score += 0.2 if any(word in intervention.lower() for word in ["connect", "activity", "enjoy"]) else 0
            
            # Adjust based on anxiety score
            if anxiety_score > 0.6:
                score += 0.2 if any(word in intervention.lower() for word in ["breathing", "relaxation", "mindfulness"]) else 0
            
            # Adjust based on user preferences
            preferred_types = user_preferences.get("preferred_intervention_types", [])
            for pref_type in preferred_types:
                if pref_type.lower() in intervention.lower():
                    score += 0.15
            
            # Add some randomness to prevent same interventions every time
            score += random.uniform(-0.05, 0.05)
            
            scored_interventions.append({
                "text": intervention,
                "score": min(score, 1.0),
                "scoring_factors": {
                    "risk_level_adjustment": 0.3 if risk_level == "HIGH" else 0.2 if risk_level == "MODERATE" else 0.1,
                    "depression_adjustment": 0.2 if depression_score > 0.6 else 0,
                    "anxiety_adjustment": 0.2 if anxiety_score > 0.6 else 0,
                    "preference_adjustment": 0.15 if any(pref.lower() in intervention.lower() for pref in preferred_types) else 0
                }
            })
        
        # Sort by score (descending)
        scored_interventions.sort(key=lambda x: x["score"], reverse=True)
        return scored_interventions
    
    def _calculate_priority(self, intervention: Dict[str, Any], risk_level: str) -> str:
        """
        Calculate priority level for intervention
        """
        score = intervention["score"]
        
        if risk_level == "HIGH" and score > 0.7:
            return "high"
        elif risk_level in ["HIGH", "MODERATE"] and score > 0.5:
            return "medium"
        else:
            return "low"
    
    def _map_mood_to_intervention_type(self, mood: str) -> str:
        """
        Map user mood to intervention type
        """
        mood_mapping = {
            "anxious": "mindfulness",
            "depressed": "activity",
            "stressed": "relaxation",
            "motivated": "productivity",
            "lonely": "social",
            "tired": "rest",
            "angry": "calming",
            "happy": "maintenance"
        }
        
        return mood_mapping.get(mood.lower(), "mindfulness")
    
    def _get_daily_intervention_by_type(self, intervention_type: str) -> Dict[str, Any]:
        """
        Get daily intervention by type
        """
        daily_interventions = {
            "mindfulness": {
                "title": "Mindful Moment",
                "text": "Take 3 deep breaths and focus on the present moment. Notice 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, and 1 you can taste.",
                "duration_minutes": 5,
                "category": "mental_health"
            },
            "activity": {
                "title": "Movement Break",
                "text": "Stand up and stretch for 2 minutes. Reach for the sky, touch your toes, and roll your shoulders. Movement helps reset your mind and body.",
                "duration_minutes": 2,
                "category": "physical"
            },
            "social": {
                "title": "Connection Check",
                "text": "Send a thoughtful message to someone you care about. A simple 'thinking of you' can strengthen relationships and boost your mood.",
                "duration_minutes": 3,
                "category": "social"
            },
            "productivity": {
                "title": "Focus Sprint",
                "text": "Set a timer for 15 minutes and work on one important task without distractions. Small focused blocks build momentum.",
                "duration_minutes": 15,
                "category": "productivity"
            },
            "relaxation": {
                "title": "Progressive Relaxation",
                "text": "Starting from your toes, tense each muscle group for 5 seconds then release. Work your way up to your head. Release physical tension.",
                "duration_minutes": 10,
                "category": "relaxation"
            },
            "calming": {
                "title": "Cool Down Corner",
                "text": "Find a quiet space and practice box breathing: inhale for 4 counts, hold for 4, exhale for 4, hold for 4. Repeat 5 times.",
                "duration_minutes": 5,
                "category": "emotional_regulation"
            }
        }
        
        return daily_interventions.get(intervention_type, daily_interventions["mindfulness"])
    
    def _analyze_recent_trends(self, recent_scores: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Analyze trends in recent scores
        """
        if len(recent_scores) < 2:
            return {"trend": "insufficient_data"}
        
        # Simple trend analysis (could be made more sophisticated)
        latest = recent_scores[-1]
        previous = recent_scores[-2]
        
        composite_change = latest.get("composite", 0) - previous.get("composite", 0)
        
        if composite_change > 0.05:
            trend = "declining"
        elif composite_change < -0.05:
            trend = "improving"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "change_amount": composite_change,
            "data_points": len(recent_scores)
        }
    
    def _get_maintenance_interventions(self, preferred_types: List[str]) -> List[Dict[str, Any]]:
        """
        Get interventions for maintaining progress
        """
        return [
            {
                "text": "Continue your current positive habits and routines.",
                "category": "maintenance",
                "score": 0.8
            },
            {
                "text": "Set new achievable goals to maintain motivation.",
                "category": "goal_setting",
                "score": 0.7
            },
            {
                "text": "Share your progress with someone supportive.",
                "category": "social",
                "score": 0.6
            }
        ]
    
    def _get_intensive_interventions(self, preferred_types: List[str]) -> List[Dict[str, Any]]:
        """
        Get intensive interventions for declining trends
        """
        return [
            {
                "text": "Consider reaching out to a mental health professional.",
                "category": "professional",
                "score": 0.9
            },
            {
                "text": "Implement a structured daily routine with self-care priorities.",
                "category": "structure",
                "score": 0.8
            },
            {
                "text": "Practice grounding techniques when feeling overwhelmed.",
                "category": "coping",
                "score": 0.7
            }
        ]
    
    def _get_variety_interventions(self, preferred_types: List[str]) -> List[Dict[str, Any]]:
        """
        Get variety interventions for stable trends
        """
        return [
            {
                "text": "Try a new stress management technique this week.",
                "category": "learning",
                "score": 0.7
            },
            {
                "text": "Explore different types of physical activity.",
                "category": "physical",
                "score": 0.6
            },
            {
                "text": "Connect with nature by spending time outdoors.",
                "category": "environmental",
                "score": 0.6
            }
        ]
    
    def _get_fallback_interventions(self, count: int) -> List[Dict[str, Any]]:
        """
        Get fallback interventions when main logic fails
        """
        fallbacks = [
            {
                "text": "Take a few deep breaths and focus on the present moment.",
                "category": "mindfulness",
                "score": 0.5
            },
            {
                "text": "Take a short walk to clear your mind.",
                "category": "physical",
                "score": 0.5
            },
            {
                "text": "Reach out to a friend or family member.",
                "category": "social",
                "score": 0.5
            }
        ]
        
        return fallbacks[:count]
    
    def _get_fallback_daily_intervention(self) -> Dict[str, Any]:
        """
        Get fallback daily intervention
        """
        return {
            "title": "Self-Care Moment",
            "text": "Take a moment to check in with yourself. How are you feeling physically, mentally, and emotionally?",
            "duration_minutes": 2,
            "category": "self_awareness",
            "fallback": True
        }
    
    def _update_intervention_effectiveness(self, intervention_id: str, score: int) -> None:
        """
        Update intervention effectiveness tracking
        """
        if intervention_id not in self.intervention_effectiveness:
            self.intervention_effectiveness[intervention_id] = []
        
        self.intervention_effectiveness[intervention_id].append(score)
        
        # Keep only last 10 scores per intervention
        if len(self.intervention_effectiveness[intervention_id]) > 10:
            self.intervention_effectiveness[intervention_id] = self.intervention_effectiveness[intervention_id][-10:]
    
    def _extract_intervention_type(self, intervention_id: str) -> str:
        """
        Extract intervention type from ID
        """
        # This is a simplified implementation
        # In practice, you'd store more metadata with interventions
        return "general"
    
    def clear_history(self) -> None:
        """
        Clear intervention history
        """
        self.user_intervention_history.clear()
        self.intervention_effectiveness.clear()
        logger.info("Intervention history cleared")


# Global instance
_intervention_service = None


def get_intervention_service() -> InterventionService:
    """
    Get the global intervention service instance
    """
    global _intervention_service
    if _intervention_service is None:
        _intervention_service = InterventionService()
    return _intervention_service
