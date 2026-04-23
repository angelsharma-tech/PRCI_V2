"""
Procrastination Risk Engine

Aggregates recent detection results to
estimate short-term procrastination risk.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from phase_4_models.detection_interface import DetectionResult


class RiskLevel(Enum):
    """
    Enumeration of risk levels for procrastination.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskResult:
    """
    Result structure for risk assessment outputs.
    
    Attributes:
        score: Overall risk score (0.0-1.0)
        level: Categorized risk level
        trend: Risk trend over time
        confidence: Confidence in risk assessment
        contributing_factors: Factors contributing to risk
        timestamp: When risk was assessed
        recommendations: Risk-appropriate recommendations
    """
    score: float
    level: RiskLevel
    trend: str
    confidence: float
    contributing_factors: List[str]
    timestamp: datetime
    recommendations: List[str]


class RiskEngine:
    """
    Core risk assessment engine for procrastination prediction.
    
    This engine processes detection results over time to
    compute comprehensive risk assessments and identify
    emerging patterns that indicate increased procrastination risk.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the risk engine.
        
        Args:
            config: Configuration parameters for risk calculation
        """
        self.config = config or {}
        self.risk_thresholds = self.config.get('risk_thresholds', {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8
        })
        self.time_window_days = self.config.get('time_window_days', 7)
        self.min_detections = self.config.get('min_detections', 3)
    
    def compute_risk(self, detection_history: List[DetectionResult]) -> RiskResult:
        """
        Compute risk score based on recent
        emotional and behavioral signals.
        
        Args:
            detection_history: List of recent detection results
            
        Returns:
            RiskResult: Comprehensive risk assessment
            
        TODO (Phase-5):
        - Implement temporal aggregation logic
        - Apply weighted scoring based on recency
        - Calculate trend indicators
        - Identify contributing factors
        - Generate risk-appropriate recommendations
        """
        if not detection_history:
            return self._create_default_risk_result()
        
        # Filter detection results within time window
        recent_detections = self._filter_recent_detections(detection_history)
        
        if len(recent_detections) < self.min_detections:
            return self._create_insufficient_data_risk_result(recent_detections)
        
        # Calculate risk components
        anxiety_risk = self._calculate_anxiety_risk(recent_detections)
        depression_risk = self._calculate_depression_risk(recent_detections)
        behavioral_risk = self._calculate_behavioral_risk(recent_detections)
        
        # Combine risk components
        overall_score = self._combine_risk_scores(anxiety_risk, depression_risk, behavioral_risk)
        
        # Determine risk level and trend
        risk_level = self._determine_risk_level(overall_score)
        trend = self._calculate_trend(detection_history)
        confidence = self._calculate_confidence(recent_detections)
        contributing_factors = self._identify_contributing_factors(recent_detections)
        recommendations = self._generate_recommendations(risk_level, contributing_factors)
        
        return RiskResult(
            score=overall_score,
            level=risk_level,
            trend=trend,
            confidence=confidence,
            contributing_factors=contributing_factors,
            timestamp=datetime.now(),
            recommendations=recommendations
        )
    
    def _filter_recent_detections(self, detection_history: List[DetectionResult]) -> List[DetectionResult]:
        """
        Filter detection results to include only recent ones within time window.
        
        Args:
            detection_history: All available detection results
            
        Returns:
            List[DetectionResult]: Recent detection results
            
        TODO (Phase-5):
        - Implement time-based filtering logic
        - Add configurable time windows
        - Handle timezone considerations
        - Optimize for large datasets
        """
        cutoff_time = datetime.now() - timedelta(days=self.time_window_days)
        return [d for d in detection_history if d.timestamp >= cutoff_time]
    
    def _calculate_anxiety_risk(self, detections: List[DetectionResult]) -> float:
        """
        Calculate risk component based on anxiety indicators.
        
        Args:
            detections: Recent detection results
            
        Returns:
            float: Anxiety-based risk score (0.0-1.0)
            
        TODO (Phase-5):
        - Implement weighted anxiety scoring
        - Consider anxiety trend patterns
        - Apply confidence weighting
        - Handle edge cases and outliers
        """
        if not detections:
            return 0.0
        
        # Placeholder implementation - simple average
        anxiety_scores = [d.anxiety_prob for d in detections]
        return sum(anxiety_scores) / len(anxiety_scores)
    
    def _calculate_depression_risk(self, detections: List[DetectionResult]) -> float:
        """
        Calculate risk component based on depression indicators.
        
        Args:
            detections: Recent detection results
            
        Returns:
            float: Depression-based risk score (0.0-1.0)
            
        TODO (Phase-5):
        - Implement weighted depression scoring
        - Consider depression pattern recognition
        - Apply clinical threshold considerations
        - Integrate with non-clinical boundaries
        """
        if not detections:
            return 0.0
        
        # Placeholder implementation - simple average
        depression_scores = [d.depression_prob for d in detections]
        return sum(depression_scores) / len(depression_scores)
    
    def _calculate_behavioral_risk(self, detections: List[DetectionResult]) -> float:
        """
        Calculate risk component based on behavioral patterns.
        
        Args:
            detections: Recent detection results
            
        Returns:
            float: Behavioral-based risk score (0.0-1.0)
            
        TODO (Phase-5):
        - Analyze root cause patterns
        - Identify behavioral risk markers
        - Consider temporal patterns
        - Weight by behavioral severity
        """
        if not detections:
            return 0.0
        
        # Placeholder implementation - based on root causes
        high_risk_causes = {'perfectionism', 'task_aversion', 'overwhelm'}
        risk_score = 0.0
        
        for detection in detections:
            for cause in detection.root_causes:
                if cause.lower() in high_risk_causes:
                    risk_score += 0.2
        
        return min(risk_score, 1.0)
    
    def _combine_risk_scores(self, anxiety: float, depression: float, behavioral: float) -> float:
        """
        Combine individual risk components into overall score.
        
        Args:
            anxiety: Anxiety-based risk score
            depression: Depression-based risk score
            behavioral: Behavioral-based risk score
            
        Returns:
            float: Combined overall risk score
            
        TODO (Phase-5):
        - Implement weighted combination logic
        - Add non-linear combination methods
        - Consider interaction effects
        - Apply normalization techniques
        """
        # Placeholder implementation - weighted average
        weights = self.config.get('risk_weights', {
            'anxiety': 0.3,
            'depression': 0.3,
            'behavioral': 0.4
        })
        
        combined = (
            anxiety * weights['anxiety'] +
            depression * weights['depression'] +
            behavioral * weights['behavioral']
        )
        
        return min(combined, 1.0)
    
    def _determine_risk_level(self, score: float) -> RiskLevel:
        """
        Determine risk level category based on score.
        
        Args:
            score: Overall risk score
            
        Returns:
            RiskLevel: Categorized risk level
            
        TODO (Phase-5):
        - Implement configurable threshold logic
        - Add hysteresis to prevent level flipping
            - Consider user-specific thresholds
            - Add uncertainty considerations
        """
        if score >= self.risk_thresholds['high']:
            return RiskLevel.HIGH
        elif score >= self.risk_thresholds['medium']:
            return RiskLevel.MEDIUM
        elif score >= self.risk_thresholds['low']:
            return RiskLevel.LOW
        else:
            return RiskLevel.LOW
    
    def _calculate_trend(self, detection_history: List[DetectionResult]) -> str:
        """
        Calculate risk trend over time.
        
        Args:
            detection_history: Historical detection results
            
        Returns:
            str: Trend indicator ('improving', 'stable', 'deteriorating')
            
        TODO (Phase-5):
        - Implement trend analysis algorithms
        - Consider multiple time windows
        - Add statistical significance testing
        - Handle insufficient data scenarios
        """
        if len(detection_history) < 2:
            return "stable"
        
        # Placeholder implementation - simple comparison
        recent_avg = sum(d.anxiety_prob + d.depression_prob for d in detection_history[-3:]) / max(len(detection_history[-3:]), 1)
        older_avg = sum(d.anxiety_prob + d.depression_prob for d in detection_history[:-3]) / max(len(detection_history[:-3]), 1)
        
        if recent_avg < older_avg * 0.9:
            return "improving"
        elif recent_avg > older_avg * 1.1:
            return "deteriorating"
        else:
            return "stable"
    
    def _calculate_confidence(self, detections: List[DetectionResult]) -> float:
        """
        Calculate confidence in risk assessment.
        
        Args:
            detections: Detection results used for assessment
            
        Returns:
            float: Confidence score (0.0-1.0)
            
        TODO (Phase-5):
        - Implement confidence calculation logic
        - Consider data quality and quantity
        - Account for model uncertainty
        - Add temporal confidence weighting
        """
        if not detections:
            return 0.0
        
        # Placeholder implementation - based on data quantity and quality
        data_quantity_factor = min(len(detections) / 10.0, 1.0)
        avg_confidence = sum(d.confidence for d in detections) / len(detections)
        
        return (data_quantity_factor + avg_confidence) / 2.0
    
    def _identify_contributing_factors(self, detections: List[DetectionResult]) -> List[str]:
        """
        Identify main factors contributing to risk.
        
        Args:
            detections: Detection results to analyze
            
        Returns:
            List[str]: List of contributing factors
            
        TODO (Phase-5):
        - Implement factor analysis logic
        - Rank factors by contribution
        - Add temporal factor weighting
        - Consider factor interactions
        """
        factors = []
        factor_counts = {}
        
        for detection in detections:
            for cause in detection.root_causes:
                factor_counts[cause] = factor_counts.get(cause, 0) + 1
        
        # Sort by frequency and return top factors
        sorted_factors = sorted(factor_counts.items(), key=lambda x: x[1], reverse=True)
        return [factor for factor, count in sorted_factors[:3]]
    
    def _generate_recommendations(self, risk_level: RiskLevel, factors: List[str]) -> List[str]:
        """
        Generate risk-appropriate recommendations.
        
        Args:
            risk_level: Current risk level
            factors: Contributing factors
            
        Returns:
            List[str]: List of recommendations
            
        TODO (Phase-5):
        - Implement recommendation logic
        - Personalize based on factors
        - Add severity-appropriate suggestions
        - Include resource recommendations
        """
        recommendations = []
        
        if risk_level == RiskLevel.HIGH:
            recommendations.append("Consider speaking with an academic advisor")
            recommendations.append("Break down large tasks into smaller steps")
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.append("Review your study schedule")
            recommendations.append("Try time management techniques")
        elif risk_level == RiskLevel.LOW:
            recommendations.append("Maintain current productive habits")
        
        return recommendations
    
    def _create_default_risk_result(self) -> RiskResult:
        """Create default risk result for no data scenarios."""
        return RiskResult(
            score=0.0,
            level=RiskLevel.LOW,
            trend="stable",
            confidence=0.0,
            contributing_factors=[],
            timestamp=datetime.now(),
            recommendations=["No data available for risk assessment"]
        )
    
    def _create_insufficient_data_risk_result(self, detections: List[DetectionResult]) -> RiskResult:
        """Create risk result for insufficient data scenarios."""
        return RiskResult(
            score=0.1,
            level=RiskLevel.LOW,
            trend="insufficient_data",
            confidence=0.1,
            contributing_factors=[],
            timestamp=datetime.now(),
            recommendations=["More data needed for accurate risk assessment"]
        )
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Update risk engine configuration.
        
        Args:
            new_config: New configuration parameters
            
        TODO (Phase-5):
        - Validate configuration parameters
        - Add configuration change logging
        - Implement rollback capability
        - Add configuration versioning
        """
        self.config.update(new_config)
        self.risk_thresholds = self.config.get('risk_thresholds', self.risk_thresholds)
        self.time_window_days = self.config.get('time_window_days', self.time_window_days)
        self.min_detections = self.config.get('min_detections', self.min_detections)
