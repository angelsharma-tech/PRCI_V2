"""
Procrastination Risk Engine for PRCI v2.0

Aggregates recent detection outputs to
estimate short-term procrastination risk.

NOTE:
This is a behavioral risk indicator,
not a clinical assessment.
"""

from statistics import mean
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from phase_4_models.detection_interface import DetectionResult


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
    def __init__(self, score: float, level: str, trend: str, 
                 confidence: float, contributing_factors: List[str], 
                 timestamp: datetime, recommendations: List[str]):
        self.score = score
        self.level = level
        self.trend = trend
        self.confidence = confidence
        self.contributing_factors = contributing_factors
        self.timestamp = timestamp
        self.recommendations = recommendations


class ProcrastinationRiskEngine:
    """
    Procrastination risk assessment engine.
    
    This engine aggregates detection results over time to compute
    comprehensive risk scores using rule-based approaches
    while maintaining interpretability and academic focus.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the risk assessment engine.
        
        Args:
            config: Configuration parameters for risk assessment
        """
        self.config = config or {}
        
        # Risk thresholds (configurable)
        self.low_threshold = self.config.get('low_threshold', 0.3)
        self.high_threshold = self.config.get('high_threshold', 0.7)
        
        # Temporal window settings
        self.default_window_size = self.config.get('default_window_size', 5)
        self.max_history_age = self.config.get('max_history_age', 30)  # days
        
        # Feature weights
        self.emotional_weight = self.config.get('emotional_weight', 0.6)
        self.behavioral_weight = self.config.get('behavioral_weight', 0.4)
        
        # Risk history for trend analysis
        self.risk_history = []
    
    def compute_risk_score(self, history: List[DetectionResult]) -> float:
        """
        Compute an aggregate risk score from
        recent detection results.
        
        Args:
            history: List of recent detection results
            
        Returns:
            float: Aggregate risk score (0.0-1.0)
            
        TODO (Phase-5):
        - Implement weighted emotional indicators
        - Add temporal pattern analysis
        - Include root cause persistence scoring
        - Add trend-based adjustment factors
        """
        if not history:
            return 0.0
        
        # Filter to recent results within time window
        recent_history = self._filter_recent_history(history)
        
        if not recent_history:
            return 0.0
        
        # Calculate emotional risk component
        emotional_risk = self._calculate_emotional_risk(recent_history)
        
        # Calculate behavioral risk component
        behavioral_risk = self._calculate_behavioral_risk(recent_history)
        
        # Combine components with weights
        aggregate_risk = (
            emotional_risk * self.emotional_weight +
            behavioral_risk * self.behavioral_weight
        )
        
        # Apply trend adjustment
        trend_adjustment = self._calculate_trend_adjustment(history)
        final_risk = aggregate_risk * trend_adjustment
        
        # Ensure within bounds
        return max(0.0, min(1.0, final_risk))
    
    def _filter_recent_history(self, history: List[DetectionResult]) -> List[DetectionResult]:
        """
        Filter detection history to recent relevant results.
        
        Args:
            history: Complete detection history
            
        Returns:
            List[DetectionResult]: Recent detection results
            
        TODO (Phase-5):
        - Implement configurable time windows
        - Add academic calendar awareness
        - Include quality-based filtering
        - Add adaptive window sizing
        """
        if not history:
            return []
        
        # Sort by timestamp
        sorted_history = sorted(history, key=lambda x: x.timestamp)
        
        # Filter by age
        cutoff_time = datetime.now() - timedelta(days=self.max_history_age)
        recent_by_age = [d for d in sorted_history if d.timestamp >= cutoff_time]
        
        # Take most recent N results
        recent_by_count = recent_by_age[-self.default_window_size:]
        
        return recent_by_count
    
    def _calculate_emotional_risk(self, history: List[DetectionResult]) -> float:
        """
        Calculate emotional risk component from detection history.
        
        Args:
            history: Recent detection results
            
        Returns:
            float: Emotional risk score (0.0-1.0)
            
        TODO (Phase-5):
        - Implement emotional intensity weighting
        - Add emotional volatility analysis
        - Include emotional trend calculation
        - Add emotional persistence scoring
        """
        if not history:
            return 0.0
        
        # Extract emotional indicators
        anxiety_scores = [d.anxiety_prob for d in history]
        depression_scores = [d.depression_prob for d in history]
        
        # Calculate average emotional indicators
        avg_anxiety = mean(anxiety_scores) if anxiety_scores else 0.0
        avg_depression = mean(depression_scores) if depression_scores else 0.0
        
        # Calculate emotional intensity (weighted combination)
        emotional_intensity = avg_anxiety * 0.7 + avg_depression * 0.3
        
        # Calculate emotional volatility (standard deviation)
        if len(anxiety_scores) > 1:
            anxiety_volatility = (max(anxiety_scores) - min(anxiety_scores)) / len(anxiety_scores)
        else:
            anxiety_volatility = 0.0
        
        # Combine intensity and volatility
        emotional_risk = emotional_intensity * 0.8 + anxiety_volatility * 0.2
        
        return min(1.0, emotional_risk)
    
    def _calculate_behavioral_risk(self, history: List[DetectionResult]) -> float:
        """
        Calculate behavioral risk component from detection history.
        
        Args:
            history: Recent detection results
            
        Returns:
            float: Behavioral risk score (0.0-1.0)
            
        TODO (Phase-5):
        - Implement root cause frequency analysis
        - Add cause persistence scoring
        - Include behavioral consistency evaluation
        - Add coping strategy assessment
        """
        if not history:
            return 0.0
        
        # Analyze root cause patterns
        all_root_causes = []
        for detection in history:
            if detection.root_causes:
                all_root_causes.extend(detection.root_causes)
        
        # Calculate cause frequency risk
        if all_root_causes:
            # High-risk causes that indicate persistent procrastination
            high_risk_causes = {'perfectionism', 'overwhelm', 'fear_of_failure', 'task_aversion'}
            high_risk_count = sum(1 for cause in all_root_causes if cause.lower() in high_risk_causes)
            cause_frequency_risk = min(1.0, high_risk_count / len(all_root_causes) * 2)
        else:
            cause_frequency_risk = 0.0
        
        # Calculate cause diversity risk (many different causes may indicate complexity)
        unique_causes = set(all_root_causes)
        cause_diversity = len(unique_causes) / max(len(all_root_causes), 1)
        diversity_risk = min(1.0, cause_diversity / 3.0)  # Normalize to max 3 causes
        
        # Combine behavioral risk factors
        behavioral_risk = cause_frequency_risk * 0.7 + diversity_risk * 0.3
        
        return min(1.0, behavioral_risk)
    
    def _calculate_trend_adjustment(self, history: List[DetectionResult]) -> float:
        """
        Calculate trend-based adjustment factor.
        
        Args:
            history: Complete detection history
            
        Returns:
            float: Trend adjustment factor (0.5-1.5)
            
        TODO (Phase-5):
        - Implement short-term trend analysis
        - Add academic calendar awareness
        - Include pattern recognition
        - Add predictive trend factors
        """
        if len(history) < 3:
            return 1.0  # No trend adjustment with insufficient data
        
        # Calculate recent trend (last 3 vs previous 3)
        recent_history = sorted(history, key=lambda x: x.timestamp)[-3:]
        previous_history = sorted(history, key=lambda x: x.timestamp)[-6:-3]
        
        if not previous_history:
            return 1.0
        
        # Calculate average risk scores for each period
        recent_avg_risk = mean([d.anxiety_prob + d.depression_prob for d in recent_history]) / 2
        previous_avg_risk = mean([d.anxiety_prob + d.depression_prob for d in previous_history]) / 2
        
        # Calculate trend adjustment
        if recent_avg_risk > previous_avg_risk * 1.2:
            return 1.3  # Increasing trend
        elif recent_avg_risk < previous_avg_risk * 0.8:
            return 0.8  # Decreasing trend
        else:
            return 1.0  # Stable trend
    
    def categorize_risk(self, score: float) -> str:
        """
        Convert numerical risk score into
        human-readable category.
        
        Args:
            score: Risk score (0.0-1.0)
            
        Returns:
            str: Risk level category
            
        TODO (Phase-5):
        - Add context-aware categorization
        - Implement adaptive thresholds
        - Include uncertainty handling
        - Add academic calendar adjustment
        """
        if score < self.low_threshold:
            return "LOW"
        elif score < self.high_threshold:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def assess(self, history: List[DetectionResult]) -> RiskResult:
        """
        Full risk assessment pipeline.
        
        Args:
            history: List of detection results
            
        Returns:
            RiskResult: Comprehensive risk assessment
            
        TODO (Phase-5):
        - Add contributing factor identification
        - Implement trend analysis
        - Include confidence scoring
        - Add recommendation generation
        """
        # Calculate risk score
        risk_score = self.compute_risk_score(history)
        
        # Categorize risk level
        risk_level = self.categorize_risk(risk_score)
        
        # Identify contributing factors
        contributing_factors = self._identify_contributing_factors(history)
        
        # Calculate trend
        trend = self._calculate_trend(history)
        
        # Calculate confidence
        confidence = self._calculate_confidence(history)
        
        # Create risk result
        result = RiskResult(
            score=risk_score,
            level=risk_level,
            trend=trend,
            confidence=confidence,
            contributing_factors=contributing_factors,
            timestamp=datetime.now(),
            recommendations=self._generate_recommendations(risk_level, contributing_factors)
        )
        
        # Store in risk history
        self.risk_history.append(result)
        
        return result
    
    def _identify_contributing_factors(self, history: List[DetectionResult]) -> List[str]:
        """
        Identify main contributing factors to risk assessment.
        
        Args:
            history: Recent detection results
            
        Returns:
            List[str]: List of contributing factors
            
        TODO (Phase-5):
        - Implement factor ranking
        - Add temporal factor analysis
        - Include context-aware factor identification
        - Add factor interaction analysis
        """
        if not history:
            return []
        
        # Analyze root cause frequency
        all_causes = []
        for detection in history:
            if detection.root_causes:
                all_causes.extend(detection.root_causes)

        if not all_causes:
            return ["no_root_causes_detected"]
        
        # Count frequency of each cause
        cause_counts = {}
        for cause in all_causes:
            cause_counts[cause] = cause_counts.get(cause, 0) + 1
        
        # Sort by frequency and return top factors
        sorted_causes = sorted(cause_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Return top contributing factors
        return [cause for cause, count in sorted_causes[:3]]
    
    def _calculate_trend(self, history: List[DetectionResult]) -> str:
        """
        Calculate risk trend over time.
        
        Args:
            history: Detection history
            
        Returns:
            str: Trend indicator
            
        TODO (Phase-5):
        - Implement sophisticated trend analysis
        - Add academic calendar awareness
        - Include pattern recognition
        - Add predictive trend calculation
        """
        if len(history) < 3:
            return "insufficient_data"
        
        # Calculate trend based on recent risk scores
        recent_history = sorted(history, key=lambda x: x.timestamp)[-5:]
        
        if len(recent_history) < 3:
            return "insufficient_data"
        
        # Calculate simple trend
        recent_scores = [d.anxiety_prob + d.depression_prob for d in recent_history]
        
        # Compare first half to second half
        mid_point = len(recent_scores) // 2
        first_half_avg = mean(recent_scores[:mid_point])
        second_half_avg = mean(recent_scores[mid_point:])
        
        if second_half_avg > first_half_avg * 1.1:
            return "deteriorating"
        elif second_half_avg < first_half_avg * 0.9:
            return "improving"
        else:
            return "stable"
    
    def _calculate_confidence(self, history: List[DetectionResult]) -> float:
        """
        Calculate confidence in risk assessment.
        
        Args:
            history: Detection history
            
        Returns:
            float: Confidence score (0.0-1.0)
            
        TODO (Phase-5):
        - Implement data quality assessment
        - Add temporal confidence weighting
        - Include pattern consistency evaluation
        - Add uncertainty quantification
        """
        if not history:
            return 0.0
        
        # Base confidence on data quantity and quality
        data_quantity = min(1.0, len(history) / 5.0)  # Normalize to 5 samples
        
        # Calculate average confidence from detection results
        avg_detection_confidence = mean([d.confidence for d in history])
        
        # Combine factors
        overall_confidence = (data_quantity * 0.4 + avg_detection_confidence * 0.6)
        
        return min(1.0, overall_confidence)
    
    def _generate_recommendations(self, risk_level: str, contributing_factors: List[str]) -> List[str]:
        """
        Generate risk-appropriate recommendations.
        
        Args:
            risk_level: Categorized risk level
            contributing_factors: Identified contributing factors
            
        Returns:
            List[str]: List of recommendations
            
        TODO (Phase-5):
        - Implement personalized recommendations
        - Add context-aware suggestion generation
        - Include academic calendar awareness
        - Add resource recommendation logic
        """
        recommendations = []
        
        if risk_level == "HIGH":
            recommendations.extend([
                "Consider speaking with an academic advisor",
                "Break down large tasks into smaller steps",
                "Seek support from university resources"
            ])
        elif risk_level == "MEDIUM":
            recommendations.extend([
                "Review your study schedule and priorities",
                "Try time management techniques",
                "Consider study group formation"
            ])
        elif risk_level == "LOW":
            recommendations.extend([
                "Maintain current productive habits",
                "Continue effective coping strategies",
                "Monitor for early warning signs"
            ])
        
        # Add factor-specific recommendations
        if "perfectionism" in contributing_factors:
            recommendations.append("Practice 'good enough' standards")
        if "overwhelm" in contributing_factors:
            recommendations.append("Use task prioritization methods")
        if "task_aversion" in contributing_factors:
            recommendations.append("Try the 5-minute rule for difficult tasks")
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Update risk engine configuration.
        
        Args:
            new_config: New configuration parameters
            
        TODO (Phase-5):
        - Add configuration validation
        - Implement config change logging
        - Add configuration versioning
        - Include config impact assessment
        """
        self.config.update(new_config)
        
        # Update specific parameters
        self.low_threshold = self.config.get('low_threshold', self.low_threshold)
        self.high_threshold = self.config.get('high_threshold', self.high_threshold)
        self.default_window_size = self.config.get('default_window_size', self.default_window_size)
        self.max_history_age = self.config.get('max_history_age', self.max_history_age)
        self.emotional_weight = self.config.get('emotional_weight', self.emotional_weight)
        self.behavioral_weight = self.config.get('behavioral_weight', self.behavioral_weight)
    
    def get_risk_history(self, limit: int = 10) -> List[RiskResult]:
        """
        Get recent risk assessment history.
        
        Args:
            limit: Maximum number of historical results to return
            
        Returns:
            List[RiskResult]: Recent risk assessments
            
        TODO (Phase-5):
        - Add history filtering options
        - Implement trend analysis from history
        - Include performance metrics
        - Add history export functionality
        """
        return self.risk_history[-limit:] if limit > 0 else self.risk_history
    
    def clear_history(self) -> None:
        """
        Clear risk assessment history.
        
        TODO (Phase-5):
        - Add history backup before clearing
        - Implement selective history clearing
        - Add history archiving
        - Include clearing confirmation
        """
        self.risk_history = []
    
    def get_engine_info(self) -> Dict[str, Any]:
        """
        Get information about the risk engine.
        
        Returns:
            Dict: Engine configuration and status
            
        TODO (Phase-5):
        - Add performance metrics
        - Include usage statistics
        - Add configuration validation
        - Include engine health status
        """
        return {
            "engine_type": "ProcrastinationRiskEngine",
            "version": "1.0.0",
            "config": self.config,
            "risk_history_count": len(self.risk_history),
            "last_assessment": self.risk_history[-1].timestamp if self.risk_history else None
        }
