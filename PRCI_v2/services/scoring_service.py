"""
Scoring Service for PRCI v2
Phase 4.1 - Backend Stabilization & Architecture Refactor
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

from config import SCORE_THRESHOLDS, RISK_COLORS, MODEL_CONFIG
from utils.logging_utils import get_logger, PerformanceTimer

logger = get_logger(__name__)


class ScoringService:
    """
    Centralized scoring service for mental health metrics
    """
    
    def __init__(self):
        self.score_history = []
        self.risk_trends = {}
    
    def calculate_composite_score(
        self,
        depression_score: float,
        anxiety_score: float,
        root_causes: Optional[Dict[str, float]] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate composite mental health score
        """
        try:
            with PerformanceTimer("composite_score_calculation"):
                # Default weights
                default_weights = {
                    "depression": 0.35,
                    "anxiety": 0.35,
                    "root_cause_severity": 0.20,
                    "volatility": 0.10
                }
                
                weights = weights or default_weights
                
                # Normalize scores to 0-1 range
                dep_norm = np.clip(depression_score, 0, 1)
                anx_norm = np.clip(anxiety_score, 0, 1)
                
                # Calculate root cause severity
                rc_severity = 0
                if root_causes:
                    rc_severity = np.mean(list(root_causes.values()))
                
                # Calculate volatility (based on recent history)
                volatility = self._calculate_volatility()
                
                # Calculate weighted composite score
                composite = (
                    dep_norm * weights["depression"] +
                    anx_norm * weights["anxiety"] +
                    rc_severity * weights["root_cause_severity"] +
                    volatility * weights["volatility"]
                )
                
                result = {
                    "composite_score": np.clip(composite, 0, 1),
                    "depression_score": dep_norm,
                    "anxiety_score": anx_norm,
                    "root_cause_severity": rc_severity,
                    "volatility": volatility,
                    "weights_used": weights,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Store in history
                self._store_score_entry(result)
                
                return result
                
        except Exception as e:
            logger.error(f"Error calculating composite score: {e}")
            raise
    
    def get_risk_level(
        self,
        score: float,
        score_type: str = "composite"
    ) -> Dict[str, Any]:
        """
        Determine risk level for a given score
        """
        try:
            thresholds = SCORE_THRESHOLDS.get(score_type, SCORE_THRESHOLDS["depression"])
            
            if score < thresholds["low"]:
                level = "LOW"
                color = RISK_COLORS["LOW"]
                description = "Low risk - Continue current positive habits"
            elif score < thresholds["moderate"]:
                level = "MODERATE"
                color = RISK_COLORS["MODERATE"]
                description = "Moderate risk - Consider implementing coping strategies"
            else:
                level = "HIGH"
                color = RISK_COLORS["HIGH"]
                description = "High risk - Seek professional support"
            
            return {
                "level": level,
                "color": color,
                "score": score,
                "threshold_used": thresholds,
                "description": description,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error determining risk level: {e}")
            return {
                "level": "MODERATE",
                "color": RISK_COLORS["MODERATE"],
                "score": score,
                "error": str(e)
            }
    
    def calculate_trend_analysis(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Calculate trend analysis for recent scores
        """
        try:
            with PerformanceTimer("trend_analysis", {"days": days}):
                # Get recent scores
                cutoff_date = datetime.now() - timedelta(days=days)
                recent_scores = [
                    entry for entry in self.score_history
                    if datetime.fromisoformat(entry["timestamp"]) > cutoff_date
                ]
                
                if len(recent_scores) < 2:
                    return {
                        "trend": "insufficient_data",
                        "message": f"Need at least 2 data points, got {len(recent_scores)}",
                        "data_points": len(recent_scores)
                    }
                
                # Extract composite scores
                scores = [entry["composite_score"] for entry in recent_scores]
                
                # Calculate trend
                trend_slope = self._calculate_trend_slope(scores)
                
                # Determine trend direction
                if abs(trend_slope) < 0.01:
                    trend_direction = "stable"
                elif trend_slope > 0:
                    trend_direction = "improving"
                else:
                    trend_direction = "declining"
                
                # Calculate statistics
                avg_score = np.mean(scores)
                std_score = np.std(scores)
                min_score = np.min(scores)
                max_score = np.max(scores)
                
                result = {
                    "trend_direction": trend_direction,
                    "trend_slope": trend_slope,
                    "statistics": {
                        "average": avg_score,
                        "std_deviation": std_score,
                        "minimum": min_score,
                        "maximum": max_score,
                        "range": max_score - min_score
                    },
                    "data_points": len(recent_scores),
                    "period_days": days,
                    "timestamp": datetime.now().isoformat()
                }
                
                return result
                
        except Exception as e:
            logger.error(f"Error calculating trend analysis: {e}")
            return {
                "trend": "error",
                "error": str(e)
            }
    
    def get_score_distribution(
        self,
        score_type: str = "composite"
    ) -> Dict[str, Any]:
        """
        Get distribution of scores
        """
        try:
            if not self.score_history:
                return {"message": "No score history available"}
            
            # Extract scores based on type
            if score_type == "composite":
                scores = [entry["composite_score"] for entry in self.score_history]
            elif score_type == "depression":
                scores = [entry["depression_score"] for entry in self.score_history]
            elif score_type == "anxiety":
                scores = [entry["anxiety_score"] for entry in self.score_history]
            else:
                raise ValueError(f"Unknown score type: {score_type}")
            
            # Calculate distribution
            distribution = {
                "count": len(scores),
                "mean": np.mean(scores),
                "median": np.median(scores),
                "std": np.std(scores),
                "min": np.min(scores),
                "max": np.max(scores),
                "q25": np.percentile(scores, 25),
                "q75": np.percentile(scores, 75)
            }
            
            # Risk level distribution
            risk_levels = []
            for score in scores:
                risk_info = self.get_risk_level(score, score_type)
                risk_levels.append(risk_info["level"])
            
            risk_counts = {level: risk_levels.count(level) for level in ["LOW", "MODERATE", "HIGH"]}
            
            result = {
                "score_type": score_type,
                "distribution": distribution,
                "risk_level_counts": risk_counts,
                "risk_level_percentages": {
                    level: (count / len(scores)) * 100
                    for level, count in risk_counts.items()
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting score distribution: {e}")
            return {"error": str(e)}
    
    def calculate_improvement_suggestions(
        self,
        current_scores: Dict[str, float],
        target_scores: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate improvement suggestions based on score gaps
        """
        try:
            suggestions = []
            
            # Default targets if not provided
            if target_scores is None:
                target_scores = {
                    "depression": 0.2,  # Low risk target
                    "anxiety": 0.2,
                    "composite": 0.25
                }
            
            for metric, current_score in current_scores.items():
                if metric in target_scores:
                    target = target_scores[metric]
                    gap = current_score - target
                    
                    if gap > 0.1:  # Only suggest if gap is significant
                        priority = "high" if gap > 0.4 else "medium" if gap > 0.2 else "low"
                        
                        suggestion = {
                            "metric": metric,
                            "current_score": current_score,
                            "target_score": target,
                            "gap": gap,
                            "priority": priority,
                            "improvement_needed_pct": (gap / current_score) * 100 if current_score > 0 else 0,
                            "suggestions": self._get_metric_suggestions(metric, gap)
                        }
                        
                        suggestions.append(suggestion)
            
            # Sort by priority and gap
            suggestions.sort(key=lambda x: (x["priority"] != "high", x["priority"] != "medium", -x["gap"]))
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error calculating improvement suggestions: {e}")
            return []
    
    def get_weekly_summary(self) -> Dict[str, Any]:
        """
        Get weekly summary of scores
        """
        try:
            with PerformanceTimer("weekly_summary"):
                # Get last 7 days of data
                cutoff_date = datetime.now() - timedelta(days=7)
                weekly_scores = [
                    entry for entry in self.score_history
                    if datetime.fromisoformat(entry["timestamp"]) > cutoff_date
                ]
                
                if not weekly_scores:
                    return {"message": "No data available for the past week"}
                
                # Calculate averages
                avg_composite = np.mean([entry["composite_score"] for entry in weekly_scores])
                avg_depression = np.mean([entry["depression_score"] for entry in weekly_scores])
                avg_anxiety = np.mean([entry["anxiety_score"] for entry in weekly_scores])
                
                # Get risk levels
                composite_risk = self.get_risk_level(avg_composite, "composite")
                depression_risk = self.get_risk_level(avg_depression, "depression")
                anxiety_risk = self.get_risk_level(avg_anxiety, "anxiety")
                
                # Calculate trend
                trend = self.calculate_trend_analysis(7)
                
                summary = {
                    "period": "last_7_days",
                    "data_points": len(weekly_scores),
                    "averages": {
                        "composite": avg_composite,
                        "depression": avg_depression,
                        "anxiety": avg_anxiety
                    },
                    "risk_levels": {
                        "composite": composite_risk["level"],
                        "depression": depression_risk["level"],
                        "anxiety": anxiety_risk["level"]
                    },
                    "trend_direction": trend.get("trend_direction", "unknown"),
                    "improvement_suggestions": self.calculate_improvement_suggestions({
                        "composite": avg_composite,
                        "depression": avg_depression,
                        "anxiety": avg_anxiety
                    }),
                    "timestamp": datetime.now().isoformat()
                }
                
                return summary
                
        except Exception as e:
            logger.error(f"Error getting weekly summary: {e}")
            return {"error": str(e)}
    
    def _calculate_volatility(self) -> float:
        """
        Calculate volatility based on recent score changes
        """
        try:
            if len(self.score_history) < 2:
                return 0.0
            
            # Get last 5 scores for volatility calculation
            recent_scores = self.score_history[-5:]
            composite_scores = [entry["composite_score"] for entry in recent_scores]
            
            if len(composite_scores) < 2:
                return 0.0
            
            # Calculate standard deviation as volatility measure
            return np.std(composite_scores)
            
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return 0.0
    
    def _calculate_trend_slope(self, scores: List[float]) -> float:
        """
        Calculate linear trend slope
        """
        try:
            if len(scores) < 2:
                return 0.0
            
            x = np.arange(len(scores))
            y = np.array(scores)
            
            # Simple linear regression
            slope = np.polyfit(x, y, 1)[0]
            return slope
            
        except Exception as e:
            logger.error(f"Error calculating trend slope: {e}")
            return 0.0
    
    def _store_score_entry(self, entry: Dict[str, Any]) -> None:
        """
        Store score entry in history
        """
        try:
            self.score_history.append(entry)
            
            # Keep only last 100 entries to prevent memory issues
            if len(self.score_history) > 100:
                self.score_history = self.score_history[-100:]
                
        except Exception as e:
            logger.error(f"Error storing score entry: {e}")
    
    def _get_metric_suggestions(self, metric: str, gap: float) -> List[str]:
        """
        Get specific suggestions for a metric
        """
        suggestions_map = {
            "depression": [
                "Consider regular physical activity",
                "Practice mindfulness or meditation",
                "Maintain a consistent sleep schedule",
                "Connect with friends or family",
                "Engage in hobbies you enjoy"
            ],
            "anxiety": [
                "Practice deep breathing exercises",
                "Try progressive muscle relaxation",
                "Limit caffeine and alcohol",
                "Write down your thoughts",
                "Consider talking to a therapist"
            ],
            "composite": [
                "Focus on overall wellness habits",
                "Maintain work-life balance",
                "Practice stress management techniques",
                "Ensure adequate sleep and nutrition",
                "Consider professional support if needed"
            ]
        }
        
        return suggestions_map.get(metric, ["Focus on general wellness practices"])
    
    def clear_history(self) -> None:
        """
        Clear score history
        """
        self.score_history.clear()
        logger.info("Score history cleared")
    
    def get_history_summary(self) -> Dict[str, Any]:
        """
        Get summary of score history
        """
        return {
            "total_entries": len(self.score_history),
            "date_range": {
                "earliest": self.score_history[0]["timestamp"] if self.score_history else None,
                "latest": self.score_history[-1]["timestamp"] if self.score_history else None
            },
            "average_composite": np.mean([entry["composite_score"] for entry in self.score_history]) if self.score_history else 0
        }


# Global instance
_scoring_service = None


def get_scoring_service() -> ScoringService:
    """
    Get the global scoring service instance
    """
    global _scoring_service
    if _scoring_service is None:
        _scoring_service = ScoringService()
    return _scoring_service
