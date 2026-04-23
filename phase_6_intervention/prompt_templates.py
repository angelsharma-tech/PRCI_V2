"""
Prompt Templates for PRCI v2.0 Interventions

Defines safe, reusable prompt templates
for AI-assisted behavioral support.
"""

from typing import Dict, List, Any
from enum import Enum


class TemplateType(Enum):
    """
    Types of intervention templates.
    """
    MOTIVATION = "motivation"
    TASK_BREAKDOWN = "task_breakdown"
    TIME_MANAGEMENT = "time_management"
    REFLECTION = "reflection"
    ENCOURAGEMENT = "encouragement"
    SAFETY = "safety"
    RESOURCE = "resource"


class PromptTemplate:
    """
    Structure for intervention prompt templates.
    
    Attributes:
        template_id: Unique identifier for the template
        type: Category of intervention template
        risk_level: Appropriate risk level for this template
        template: Template string with placeholders
        variables: List of variables that can be substituted
        safety_checks: Safety validation requirements
        ethical_boundaries: Ethical constraints for this template
    """
    def __init__(self, template_id: str, template_type: TemplateType, 
                 risk_level: str, template: str, variables: List[str],
                 safety_checks: List[str], ethical_boundaries: List[str]):
        self.template_id = template_id
        self.type = template_type
        self.risk_level = risk_level
        self.template = template
        self.variables = variables
        self.safety_checks = safety_checks
        self.ethical_boundaries = ethical_boundaries
    
    def format(self, **kwargs) -> str:
        """
        Format template with provided variables.
        
        Args:
            **kwargs: Variable substitutions
            
        Returns:
            str: Formatted template string
            
        TODO (Phase-6):
            - Add variable validation
            - Implement safety check enforcement
            - Add ethical boundary validation
            - Include error handling for missing variables
        """
        # Validate required variables
        for var in self.variables:
            if var not in kwargs:
                kwargs[var] = f"[{var.upper()}]"
        
        return self.template.format(**kwargs)


# Core prompt templates for different intervention types
PROMPT_TEMPLATES = {
    "motivation": PromptTemplate(
        template_id="motivation_001",
        template_type=TemplateType.MOTIVATION,
        risk_level="ALL",
        template="Encourage user to take one small, achievable step today. Focus on progress, not perfection.",
        variables=["task_type", "time_available"],
        safety_checks=["no_pressure", "user_autonomy"],
        ethical_boundaries=["non_clinical", "supportive_only"]
    ),
    
    "focus": PromptTemplate(
        template_id="focus_001",
        template_type=TemplateType.TIME_MANAGEMENT,
        risk_level="ALL",
        template="Suggest a short, distraction-free work session. Emphasize creating a conducive study environment.",
        variables=["session_length", "distraction_type"],
        safety_checks=["realistic_expectations", "break_inclusion"],
        ethical_boundaries=["productivity_focus", "no_medical_advice"]
    ),
    
    "reflection": PromptTemplate(
        template_id="reflection_001",
        template_type=TemplateType.REFLECTION,
        risk_level="ALL",
        template="Ask user to reflect on what is blocking progress without judgment. Focus on situational factors.",
        variables=["blockage_type", "context"],
        safety_checks=["no_blame", "solution_oriented"],
        ethical_boundaries=["self_awareness", "no_diagnosis"]
    ),
    
    "task_breakdown": PromptTemplate(
        template_id="breakdown_001",
        template_type=TemplateType.TASK_BREAKDOWN,
        risk_level="MEDIUM_HIGH",
        template="Guide user through breaking overwhelming tasks into smaller, manageable steps.",
        variables=["task_complexity", "available_time", "deadline_pressure"],
        safety_checks=["achievable_steps", "time_realistic"],
        ethical_boundaries=["skill_building", "no_therapy"]
    ),
    
    "encouragement": PromptTemplate(
        template_id="encouragement_001",
        template_type=TemplateType.ENCOURAGEMENT,
        risk_level="ALL",
        template="Provide supportive acknowledgment of effort and progress. Reinforce capability and resilience.",
        variables=["achievement_type", "effort_level"],
        safety_checks=["authentic_praise", "avoid_comparison"],
        ethical_boundaries=["positive_psychology", "no_clinical_judgment"]
    ),
    
    "safety": PromptTemplate(
        template_id="safety_001",
        template_type=TemplateType.SAFETY,
        risk_level="HIGH",
        template="Include appropriate safety disclaimer and resource referral information.",
        variables=["risk_level", "available_resources"],
        safety_checks=["professional_referral", "boundary_clarification"],
        ethical_boundaries=["responsibility_limitation", "help_connection"]
    )
}


# Risk-level specific template variations
RISK_SPECIFIC_TEMPLATES = {
    "LOW": {
        "motivation": [
            "You seem to be managing well. Consider setting a small goal to maintain momentum.",
            "A short focused session can help you stay on track today.",
            "Your current approach is working well. Keep building on your success."
        ],
        "task_breakdown": [
            "You're doing great! Maybe organize your next task into clear steps.",
            "Consider outlining your approach before starting your next assignment."
        ],
        "time_management": [
            "Your current schedule seems effective. Consider adding short review sessions.",
            "Try maintaining your current routine with brief planning breaks."
        ],
        "reflection": [
            "Reflect on what's working well in your current study approach.",
            "Consider how you can maintain your current positive momentum."
        ],
        "encouragement": [
            "You're doing an excellent job managing your academic responsibilities.",
            "Your consistent effort is paying off. Keep up the great work!"
        ]
    },
    
    "MEDIUM": {
        "motivation": [
            "Breaking your task into smaller steps may make it feel more manageable.",
            "Try working for 25 minutes followed by a short break to maintain focus.",
            "Focus on making progress, not perfection. Every step counts."
        ],
        "task_breakdown": [
            "Break your current task into specific, actionable steps with clear deadlines.",
            "Try the 2-minute rule: if a task takes less than 2 minutes, do it immediately."
        ],
        "time_management": [
            "Try the Pomodoro technique: 25 minutes focused work, 5-minute break.",
            "Schedule your most challenging tasks during your peak energy hours."
        ],
        "reflection": [
            "What specific aspect of your current task feels most challenging right now?",
            "Consider what strategies have helped you overcome similar challenges before."
        ],
        "encouragement": [
            "Academic challenges are normal. You have the skills to overcome this.",
            "Every expert was once a beginner. Your persistence will lead to success."
        ]
    },
    
    "HIGH": {
        "motivation": [
            "It might help to pause and identify one small action you can take right now.",
            "Consider writing down your tasks and prioritizing just one to start with.",
            "Focus on making progress, not achieving perfection. Small steps matter."
        ],
        "task_breakdown": [
            "Start with the absolute smallest possible step you can take right now.",
            "Break your overwhelming task into 5-minute chunks to reduce anxiety."
        ],
        "time_management": [
            "Try working for just 10 minutes, then reassess how you feel.",
            "Consider changing your study environment to refresh your perspective."
        ],
        "reflection": [
            "What's the smallest change you could make to your current approach?",
            "Consider what support or resources might help you move forward right now."
        ],
        "encouragement": [
            "It's okay to feel overwhelmed. You're not alone in this experience.",
            "This difficult period will pass. Be patient and kind to yourself."
        ]
    }
}


# Root cause specific templates
ROOT_CAUSE_TEMPLATES = {
    "perfectionism": [
        "Try setting a 'good enough' standard instead of perfect.",
        "Consider the 80/20 rule: focus on the 20% that gives 80% of the results.",
        "Remember that done is better than perfect when facing deadlines."
    ],
    
    "overwhelm": [
        "Focus only on what you can control in this moment.",
        "Try the 'one thing' approach: pick just one task to complete today.",
        "Consider which tasks you could delegate or postpone if possible."
    ],
    
    "task_aversion": [
        "Try the 5-minute rule: commit to working for just 5 minutes.",
        "Pair your task with something enjoyable (music, tea, comfortable space).",
        "Consider what makes this task unappealing and how you could change that."
    ],
    
    "fear_of_failure": [
        "Remember that mistakes are learning opportunities, not failures.",
        "Focus on effort and progress rather than just outcomes.",
        "Consider what's the worst that could realistically happen and how you'd handle it."
    ],
    
    "lack_of_motivation": [
        "Connect your current task to your long-term goals and values.",
        "Try working with a study partner or in a public space like a library.",
        "Consider what used to motivate you and try recreating those conditions."
    ],
    
    "time_management": [
        "Try time-blocking your day with specific activities scheduled.",
        "Use the Eisenhower matrix to prioritize urgent vs. important tasks.",
        "Consider using a digital calendar with reminders for important deadlines."
    ]
}


# Safety and boundary templates
SAFETY_TEMPLATES = {
    "disclaimer": "This is supportive guidance for academic productivity. Consider seeking professional help if you're experiencing significant distress.",
    
    "boundary_note": "These suggestions are for academic support and do not replace professional medical or mental health services.",
    
    "resource_referral": "If you're experiencing significant distress, consider reaching out to your university's counseling services or academic support center.",
    
    "emergency_note": "If you're in crisis, please contact emergency services or crisis helplines immediately."
}


# Template selection rules
TEMPLATE_SELECTION_RULES = {
    "risk_level_mapping": {
        "LOW": ["motivation", "encouragement", "reflection"],
        "MEDIUM": ["task_breakdown", "time_management", "motivation"],
        "HIGH": ["task_breakdown", "reflection", "encouragement", "safety"]
    },
    
    "cause_priority": {
        "perfectionism": ["task_breakdown", "reflection"],
        "overwhelm": ["task_breakdown", "time_management"],
        "task_aversion": ["motivation", "task_breakdown"],
        "fear_of_failure": ["encouragement", "reflection"],
        "lack_of_motivation": ["motivation", "encouragement"],
        "time_management": ["time_management", "task_breakdown"]
    },
    
    "avoid_repetition": {
        "max_recent_use": 3,
        "time_window_hours": 24
    }
}


def get_template(template_type: str, risk_level: str = "MEDIUM", 
                root_cause: str = None) -> PromptTemplate:
    """
    Get appropriate template based on type and context.
    
    Args:
        template_type: Type of intervention template
        risk_level: Current risk level
        root_cause: Specific root cause (optional)
        
    Returns:
        PromptTemplate: Selected template
        
    TODO (Phase-6):
        - Add intelligent template selection
        - Implement context-aware matching
        - Add variety and repetition avoidance
        - Include personalization factors
    """
    # Get base template
    base_template = PROMPT_TEMPLATES.get(template_type)
    
    if not base_template:
        # Return default template
        return PROMPT_TEMPLATES["motivation"]
    
    return base_template


def format_template(template_type: str, variables: Dict[str, Any], 
                 risk_level: str = "MEDIUM") -> str:
    """
    Format template with provided variables.
    
    Args:
        template_type: Type of template to format
        variables: Variable substitutions
        risk_level: Risk level for template selection
        
    Returns:
        str: Formatted template string
        
    TODO (Phase-6):
        - Add variable validation
        - Implement safety check enforcement
        - Add ethical boundary validation
        - Include error handling
    """
    template = get_template(template_type, risk_level)
    return template.format(**variables)


def get_risk_specific_message(intervention_type: str, risk_level: str) -> str:
    """
    Get risk-level specific intervention message.
    
    Args:
        intervention_type: Type of intervention
        risk_level: Current risk level
        
    Returns:
        str: Risk-specific message
        
    TODO (Phase-6):
        - Add intelligent message selection
        - Implement variety and repetition avoidance
        - Add context appropriateness
        - Include personalization
    """
    messages = RISK_SPECIFIC_TEMPLATES.get(risk_level, {})
    type_messages = messages.get(intervention_type, [])
    
    if not type_messages:
        return "Consider taking a thoughtful approach to your current academic tasks."
    
    return type_messages[0]  # Simple selection - can be enhanced


def get_cause_specific_message(root_cause: str) -> str:
    """
    Get root cause specific intervention message.
    
    Args:
        root_cause: Identified root cause
        
    Returns:
        str: Cause-specific message
        
    TODO (Phase-6):
        - Add cause prioritization
        - Implement multiple cause handling
        - Add cause severity consideration
        - Include personalization
    """
    messages = ROOT_CAUSE_TEMPLATES.get(root_cause, [])
    
    if not messages:
        return ""
    
    return messages[0]  # Simple selection - can be enhanced


def get_safety_message(risk_level: str = "MEDIUM") -> str:
    """
    Get appropriate safety message based on risk level.
    
    Args:
        risk_level: Current risk level
        
    Returns:
        str: Safety message
        
    TODO (Phase-6):
        - Add risk-level appropriate safety messages
        - Include resource-specific information
        - Add emergency contact details
        - Include context appropriateness
    """
    if risk_level == "HIGH":
        return SAFETY_TEMPLATES["disclaimer"] + " " + SAFETY_TEMPLATES["resource_referral"]
    else:
        return SAFETY_TEMPLATES["boundary_note"]


def validate_template_safety(template: PromptTemplate, variables: Dict[str, Any]) -> bool:
    """
    Validate that template formatting maintains safety boundaries.
    
    Args:
        template: Template to validate
        variables: Variables for formatting
        
    Returns:
        bool: True if template is safe
        
    TODO (Phase-6):
        - Implement comprehensive safety validation
        - Add clinical boundary checking
        - Include harm potential assessment
        - Add user autonomy preservation checks
    """
    # Format template
    formatted = template.format(**variables)
    
    # Check for clinical terms
    clinical_keywords = ["therapy", "diagnosis", "treatment", "medication", "clinical"]
    for keyword in clinical_keywords:
        if keyword.lower() in formatted.lower():
            return False
    
    # Check for authoritative language
    authoritative_terms = ["must", "should", "required", "mandatory"]
    for term in authoritative_terms:
        if term.lower() in formatted.lower():
            return False
    
    return True


def get_template_info() -> Dict[str, Any]:
    """
    Get information about available templates.
    
    Returns:
        Dict: Template information and statistics
        
    TODO (Phase-6):
        - Add template usage statistics
        - Include effectiveness data
        - Add template version information
        - Include quality metrics
    """
    return {
        "total_templates": len(PROMPT_TEMPLATES),
        "template_types": [t.value for t in TemplateType],
        "risk_levels": ["LOW", "MEDIUM", "HIGH"],
        "root_causes_supported": list(ROOT_CAUSE_TEMPLATES.keys()),
        "safety_templates": list(SAFETY_TEMPLATES.keys())
    }
