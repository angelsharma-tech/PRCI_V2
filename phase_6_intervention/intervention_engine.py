"""
AI-Based Intervention Engine

Maps detected root causes and risk levels
to safe, non-clinical interventions.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Import from risk engine
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase_5_risk_engine'))
from risk_engine import RiskLevel


class InterventionType(Enum):
    """
    Types of interventions supported by the system.
    """
    TIME_MANAGEMENT = "time_management"
    MOTIVATIONAL = "motivational"
    ENVIRONMENTAL = "environmental"
    COGNITIVE = "cognitive"
    BEHAVIORAL = "behavioral"
    RESOURCE = "resource"


class InterventionPriority(Enum):
    """
    Priority levels for interventions.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Intervention:
    """
    Structure representing an intervention recommendation.
    
    Attributes:
        title: Brief title of the intervention
        description: Detailed description of the intervention
        type: Category of intervention
        priority: Priority level for this intervention
        steps: Step-by-step implementation guide
        expected_outcomes: Anticipated benefits
        time_required: Estimated time to implement
        difficulty: Difficulty level (1-5 scale)
        resources: Additional resources needed
        ethical_safety_check: Ethical validation status
    """
    title: str
    description: str
    type: InterventionType
    priority: InterventionPriority
    steps: List[str]
    expected_outcomes: List[str]
    time_required: str
    difficulty: int
    resources: List[str]
    ethical_safety_check: bool


class InterventionEngine:
    """
    Core intervention generation engine.
    
    This engine maps risk levels and root causes to
    appropriate, ethical, and personalized intervention
    strategies while maintaining strict non-clinical boundaries.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the intervention engine.
        
        Args:
            config: Configuration parameters for intervention generation
        """
        self.config = config or {}
        self.intervention_library = self._load_intervention_library()
        self.ethical_filters = self._load_ethical_filters()
        self.personalization_weights = self.config.get('personalization_weights', {})
    
    def suggest(self, risk_level: str, root_causes: List[str], 
                user_context: Dict[str, Any] = None) -> List[Intervention]:
        """
        Generate personalized, ethical
        intervention suggestions.
        
        Args:
            risk_level: Current risk level (from RiskLevel enum)
            root_causes: List of identified procrastination root causes
            user_context: Additional context for personalization
            
        Returns:
            List[Intervention]: List of recommended interventions
            
        TODO (Phase-6):
        - Implement rule-based mapping logic
        - Add prompt-driven response generation
        - Apply ethical filtering
        - Personalize based on user context
        - Rank interventions by effectiveness
        """
        user_context = user_context or {}
        
        # Validate inputs
        if not self._validate_inputs(risk_level, root_causes):
            return self._create_default_interventions()
        
        # Generate candidate interventions
        candidates = self._generate_candidates(risk_level, root_causes)
        
        # Apply ethical filtering
        ethical_candidates = self._apply_ethical_filters(candidates)
        
        # Personalize interventions
        personalized = self._personalize_interventions(ethical_candidates, user_context)
        
        # Rank and select best interventions
        ranked = self._rank_interventions(personalized, risk_level)
        
        return ranked[:3]  # Return top 3 interventions
    
    def _validate_inputs(self, risk_level: str, root_causes: List[str]) -> bool:
        """
        Validate input parameters for intervention generation.
        
        Args:
            risk_level: Risk level string
            root_causes: List of root causes
            
        Returns:
            bool: True if inputs are valid
            
        TODO (Phase-6):
        - Implement comprehensive input validation
        - Add risk level verification
        - Validate root cause categories
        - Check for inappropriate content
        """
        if not risk_level or not isinstance(risk_level, str):
            return False
        
        if not root_causes or not isinstance(root_causes, list):
            return False
        
        # Validate risk level
        valid_levels = [level.value for level in RiskLevel]
        if risk_level not in valid_levels:
            return False
        
        return True
    
    def _generate_candidates(self, risk_level: str, root_causes: List[str]) -> List[Intervention]:
        """
        Generate candidate interventions based on risk and causes.
        
        Args:
            risk_level: Current risk level
            root_causes: Identified root causes
            
        Returns:
            List[Intervention]: Candidate interventions
            
        TODO (Phase-6):
        - Implement rule-based mapping algorithms
        - Add risk-appropriate intervention selection
        - Map root causes to intervention types
        - Consider intervention combinations
        """
        candidates = []
        
        # Map risk level to intervention priority
        priority_map = {
            'low': InterventionPriority.LOW,
            'medium': InterventionPriority.MEDIUM,
            'high': InterventionPriority.HIGH,
            'critical': InterventionPriority.URGENT
        }
        
        base_priority = priority_map.get(risk_level, InterventionPriority.MEDIUM)
        
        # Generate interventions for each root cause
        for cause in root_causes:
            cause_interventions = self._get_interventions_for_cause(cause, base_priority)
            candidates.extend(cause_interventions)
        
        # Add general risk-level interventions
        general_interventions = self._get_general_interventions(risk_level, base_priority)
        candidates.extend(general_interventions)
        
        return candidates
    
    def _get_interventions_for_cause(self, cause: str, priority: InterventionPriority) -> List[Intervention]:
        """
        Get interventions specific to a root cause.
        
        Args:
            cause: Root cause identifier
            priority: Intervention priority level
            
        Returns:
            List[Intervention]: Cause-specific interventions
            
        TODO (Phase-6):
        - Implement comprehensive cause-to-intervention mapping
        - Add evidence-based intervention selection
        - Consider cause severity and duration
        - Add intervention effectiveness data
        """
        interventions = []
        
        # Placeholder mappings for common causes
        cause_mappings = {
            'perfectionism': [
                Intervention(
                    title="Good Enough Principle",
                    description="Focus on completing tasks to a good enough standard rather than perfect",
                    type=InterventionType.COGNITIVE,
                    priority=priority,
                    steps=[
                        "Define 'good enough' criteria before starting",
                        "Set time limits for each task component",
                        "Review work only once before submission"
                    ],
                    expected_outcomes=["Reduced task completion time", "Lower anxiety levels"],
                    time_required="15 minutes",
                    difficulty=2,
                    resources=["Timer", "Task checklist"],
                    ethical_safety_check=True
                )
            ],
            'task_aversion': [
                Intervention(
                    title="5-Minute Rule",
                    description="Commit to working on a task for just 5 minutes to overcome initial resistance",
                    type=InterventionType.BEHAVIORAL,
                    priority=priority,
                    steps=[
                        "Set a timer for 5 minutes",
                        "Start the task without judgment",
                        "Continue after 5 minutes if you feel motivated"
                    ],
                    expected_outcomes=["Increased task initiation", "Reduced procrastination"],
                    time_required="5 minutes",
                    difficulty=1,
                    resources=["Timer", "Task materials"],
                    ethical_safety_check=True
                )
            ],
            'overwhelm': [
                Intervention(
                    title="Task Breakdown Method",
                    description="Break large tasks into smaller, manageable steps",
                    type=InterventionType.TIME_MANAGEMENT,
                    priority=priority,
                    steps=[
                        "List all components of the large task",
                        "Estimate time for each component",
                        "Schedule components over multiple days"
                    ],
                    expected_outcomes=["Reduced overwhelm", "Clear action plan"],
                    time_required="30 minutes",
                    difficulty=2,
                    resources=["Paper/pen", "Calendar"],
                    ethical_safety_check=True
                )
            ]
        }
        
        return cause_mappings.get(cause.lower(), [])
    
    def _get_general_interventions(self, risk_level: str, priority: InterventionPriority) -> List[Intervention]:
        """
        Get general interventions for risk level.
        
        Args:
            risk_level: Current risk level
            priority: Intervention priority
            
        Returns:
            List[Intervention]: General interventions
            
        TODO (Phase-6):
        - Implement risk-level appropriate general interventions
        - Add preventive strategies for low risk
        - Include intensive support for high risk
        - Consider resource availability
        """
        interventions = []
        
        if risk_level in ['high', 'critical']:
            interventions.append(Intervention(
                title="Academic Support Connection",
                description="Connect with university academic support services",
                type=InterventionType.RESOURCE,
                priority=InterventionPriority.HIGH,
                steps=[
                    "Contact university academic support center",
                    "Schedule appointment with advisor",
                    "Discuss current challenges and strategies"
                ],
                expected_outcomes=["Professional guidance", "Accountability support"],
                time_required="1 hour",
                difficulty=1,
                resources=["University support contact information"],
                ethical_safety_check=True
            ))
        
        return interventions
    
    def _apply_ethical_filters(self, candidates: List[Intervention]) -> List[Intervention]:
        """
        Apply ethical and safety filters to interventions.
        
        Args:
            candidates: List of candidate interventions
            
        Returns:
            List[Intervention]: Ethically filtered interventions
            
        TODO (Phase-6):
        - Implement comprehensive ethical filtering
        - Add clinical boundary checks
        - Include cultural sensitivity validation
        - Add accessibility considerations
        """
        filtered = []
        
        for intervention in candidates:
            # Check if intervention passes ethical filters
            if self._passes_ethical_check(intervention):
                filtered.append(intervention)
        
        return filtered
    
    def _passes_ethical_check(self, intervention: Intervention) -> bool:
        """
        Check if intervention passes ethical validation.
        
        Args:
            intervention: Intervention to validate
            
        Returns:
            bool: True if intervention is ethically appropriate
            
        TODO (Phase-6):
        - Implement comprehensive ethical validation
        - Add non-clinical boundary enforcement
        - Include harm potential assessment
        - Add user autonomy preservation checks
        """
        # Basic ethical checks
        if not intervention.ethical_safety_check:
            return False
        
        # Ensure intervention maintains user autonomy
        if "must" in intervention.description.lower() or "required" in intervention.title.lower():
            return False
        
        # Check for clinical content
        clinical_keywords = ["therapy", "diagnosis", "treatment", "medication"]
        for keyword in clinical_keywords:
            if keyword in intervention.description.lower():
                return False
        
        return True
    
    def _personalize_interventions(self, candidates: List[Intervention], 
                                 user_context: Dict[str, Any]) -> List[Intervention]:
        """
        Personalize interventions based on user context.
        
        Args:
            candidates: List of candidate interventions
            user_context: User-specific context information
            
        Returns:
            List[Intervention]: Personalized interventions
            
        TODO (Phase-6):
        - Implement comprehensive personalization logic
        - Add learning style adaptation
        - Consider time constraints and preferences
        - Add cultural and personal value alignment
        """
        personalized = []
        
        for intervention in candidates:
            # Create personalized copy
            personalized_intervention = self._create_personalized_copy(intervention, user_context)
            personalized.append(personalized_intervention)
        
        return personalized
    
    def _create_personalized_copy(self, intervention: Intervention, 
                                user_context: Dict[str, Any]) -> Intervention:
        """
        Create personalized copy of intervention.
        
        Args:
            intervention: Original intervention
            user_context: User context information
            
        Returns:
            Intervention: Personalized intervention copy
            
        TODO (Phase-6):
        - Implement personalization logic
        - Add context-aware modifications
        - Include user preference integration
        - Add adaptive difficulty adjustment
        """
        # Placeholder implementation - return original
        return intervention
    
    def _rank_interventions(self, interventions: List[Intervention], risk_level: str) -> List[Intervention]:
        """
        Rank interventions by effectiveness and appropriateness.
        
        Args:
            interventions: List of interventions to rank
            risk_level: Current risk level
            
        Returns:
            List[Intervention]: Ranked interventions
            
        TODO (Phase-6):
        - Implement comprehensive ranking algorithm
        - Add effectiveness weighting
        - Consider user preference alignment
        - Add implementation feasibility factors
        """
        # Placeholder implementation - sort by priority and difficulty
        priority_order = {
            InterventionPriority.URGENT: 0,
            InterventionPriority.HIGH: 1,
            InterventionPriority.MEDIUM: 2,
            InterventionPriority.LOW: 3
        }
        
        return sorted(interventions, key=lambda x: (priority_order[x.priority], x.difficulty))
    
    def _create_default_interventions(self) -> List[Intervention]:
        """
        Create default interventions for edge cases.
        
        Returns:
            List[Intervention]: Default safe interventions
            
        TODO (Phase-6):
        - Implement safe default interventions
        - Add general productivity suggestions
        - Include resource recommendations
        - Add professional help suggestions
        """
        return [Intervention(
            title="Basic Time Management",
            description="Review and organize your study schedule",
            type=InterventionType.TIME_MANAGEMENT,
            priority=InterventionPriority.LOW,
            steps=[
                "List all upcoming assignments",
                "Prioritize by deadline and importance",
                "Create a study schedule"
            ],
            expected_outcomes=["Better organization", "Reduced stress"],
            time_required="30 minutes",
            difficulty=1,
            resources=["Calendar", "Task list"],
            ethical_safety_check=True
        )]
    
    def _load_intervention_library(self) -> Dict[str, Any]:
        """
        Load the intervention library from storage.
        
        Returns:
            Dict[str, Any]: Intervention library data
            
        TODO (Phase-6):
        - Implement library loading from database/files
        - Add intervention metadata and effectiveness data
        - Include version control and updates
        - Add quality validation
        """
        return {}
    
    def _load_ethical_filters(self) -> Dict[str, Any]:
        """
        Load ethical filtering rules and constraints.
        
        Returns:
            Dict[str, Any]: Ethical filter configuration
            
        TODO (Phase-6):
        - Implement ethical rule loading
        - Add boundary condition definitions
        - Include cultural sensitivity rules
        - Add safety check protocols
        """
        return {}
    
    def update_intervention_library(self, new_interventions: List[Intervention]) -> None:
        """
        Update the intervention library with new interventions.
        
        Args:
            new_interventions: List of new interventions to add
            
        TODO (Phase-6):
        - Implement library update logic
        - Add intervention validation
        - Include effectiveness tracking
        - Add version management
        """
        pass
    
    def get_intervention_effectiveness(self, intervention_id: str) -> Dict[str, Any]:
        """
        Get effectiveness data for a specific intervention.
        
        Args:
            intervention_id: Identifier for the intervention
            
        Returns:
            Dict[str, Any]: Effectiveness metrics and data
            
        TODO (Phase-6):
        - Implement effectiveness tracking
        - Add success rate metrics
        - Include user satisfaction data
        - Add demographic effectiveness breakdown
        """
        return {}
