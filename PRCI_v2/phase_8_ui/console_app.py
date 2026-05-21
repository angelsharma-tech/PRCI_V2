"""
Console-Based UI for PRCI v2.0
Demonstration-only interaction layer
"""

import sys
import os
from typing import Dict, Any, Optional

# Add project paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase_4_models'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase_5_risk_engine'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase_6_intervention'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase_7_personalization'))

# Import system components (for demonstration)
try:
    from detection_engine_impl import DetectionEngine
    from risk_engine import RiskEngine, RiskLevel
    from intervention_engine import InterventionEngine
    from personalization_engine import PersonalizationEngine
except ImportError:
    # Fallback for demonstration without full system integration
    print("Note: Running in demonstration mode without full system integration")
    DetectionEngine = None
    RiskEngine = None
    InterventionEngine = None
    PersonalizationEngine = None


class PRCIConsoleApp:
    """
    Console-based demonstration interface for PRCI v2.0
    """
    
    def __init__(self):
        """Initialize the console application"""
        self.user_id = "demo_user"
        self.session_count = 0
        
        # Initialize system components (if available)
        self.detection_engine = DetectionEngine() if DetectionEngine else None
        self.risk_engine = RiskEngine() if RiskEngine else None
        self.intervention_engine = InterventionEngine() if InterventionEngine else None
        self.personalization_engine = PersonalizationEngine() if PersonalizationEngine else None
        
        # Session data (not persisted)
        self.session_data = {
            "inputs": [],
            "detection_results": [],
            "risk_levels": [],
            "interventions": [],
            "feedback": []
        }
    
    def display_welcome(self):
        """Display welcome message and disclaimer"""
        print("=" * 60)
        print("PRCI v2.0 – Academic Support System")
        print("=" * 60)
        print()
        print("IMPORTANT DISCLAIMER:")
        print("This system provides academic support suggestions and does not")
        print("offer psychological or medical advice.")
        print()
        print("This system is intended for academic support and productivity")
        print("guidance only. For professional help, please contact")
        print("university counseling services or qualified professionals.")
        print()
        print("This is a non-clinical, academic demonstration tool.")
        print("=" * 60)
        print()
    
    def get_user_input(self) -> str:
        """Get academic situation description from user"""
        print("\n" + "-" * 40)
        print("Please describe your current academic situation:")
        print("(e.g., struggling with assignment deadlines,")
        print(" difficulty focusing on studies, etc.)")
        print("-" * 40)
        
        while True:
            user_input = input(">> ").strip()
            
            if len(user_input) < 10:
                print("Please provide more detail (at least 10 characters):")
                continue
            
            if len(user_input) > 500:
                print("Please keep your description under 500 characters:")
                continue
            
            # Basic content validation
            if self._validate_input(user_input):
                return user_input
            else:
                print("Please focus on academic situations only:")
    
    def _validate_input(self, user_input: str) -> bool:
        """Validate user input for appropriateness"""
        # Basic academic context check
        academic_keywords = [
            'study', 'assignment', 'deadline', 'exam', 'class', 'course',
            'homework', 'project', 'paper', 'research', 'grade', 'academic'
        ]
        
        # Check if input contains academic context
        has_academic_context = any(keyword in user_input.lower() for keyword in academic_keywords)
        
        # Basic inappropriate content check (simplified)
        inappropriate_keywords = ['suicide', 'harm', 'kill', 'die']
        has_inappropriate = any(keyword in user_input.lower() for keyword in inappropriate_keywords)
        
        return has_academic_context and not has_inappropriate
    
    def process_detection(self, user_input: str) -> Dict[str, Any]:
        """Process user input through detection layer"""
        print("\n" + "-" * 40)
        print("Analyzing your academic situation...")
        print("-" * 40)
        
        if self.detection_engine:
            try:
                # Use actual detection engine
                result = self.detection_engine.analyze_text(user_input)
                return {
                    "emotional_signal": result.get('emotion', 'moderate'),
                    "root_cause": result.get('root_cause', 'task_overload'),
                    "confidence": result.get('confidence', 0.7)
                }
            except Exception as e:
                print(f"Detection processing error: {e}")
        
        # Fallback demonstration data
        return {
            "emotional_signal": "moderate stress indicators",
            "root_cause": "task_overload",
            "confidence": 0.75
        }
    
    def assess_risk(self, detection_result: Dict[str, Any]) -> str:
        """Assess procrastination risk level"""
        print("\n" + "-" * 40)
        print("Assessing procrastination risk level...")
        print("-" * 40)
        
        if self.risk_engine:
            try:
                # Use actual risk engine
                risk_result = self.risk_engine.assess_risk([detection_result])
                return risk_result.risk_level.value
            except Exception as e:
                print(f"Risk assessment error: {e}")
        
        # Fallback demonstration logic
        emotional_signal = detection_result.get("emotional_signal", "")
        if "high" in emotional_signal.lower():
            return "HIGH"
        elif "low" in emotional_signal.lower():
            return "LOW"
        else:
            return "MEDIUM"
    
    def generate_intervention(self, risk_level: str, root_cause: str) -> str:
        """Generate appropriate intervention"""
        print("\n" + "-" * 40)
        print("Generating academic support suggestion...")
        print("-" * 40)
        
        if self.intervention_engine:
            try:
                # Use actual intervention engine
                interventions = self.intervention_engine.suggest(risk_level, [root_cause])
                if interventions:
                    return interventions[0].description
            except Exception as e:
                print(f"Intervention generation error: {e}")
        
        # Fallback demonstration interventions
        interventions_by_risk = {
            "LOW": [
                "You seem to be managing well. Consider setting a small goal to maintain momentum.",
                "Your current approach is working well. Keep building on your success."
            ],
            "MEDIUM": [
                "Consider breaking your task into smaller steps and allocating focused time blocks.",
                "Try working for 25 minutes followed by a short break to maintain focus."
            ],
            "HIGH": [
                "It might help to pause and identify one small action you can take right now.",
                "Focus on making progress, not achieving perfection. Small steps matter."
            ]
        }
        
        interventions = interventions_by_risk.get(risk_level, interventions_by_risk["MEDIUM"])
        return interventions[0] if interventions else "Consider taking a thoughtful approach to your current academic tasks."
    
    def apply_personalization(self, intervention: str) -> str:
        """Apply personalization if available"""
        if self.personalization_engine:
            try:
                # Get user preferences
                analytics = self.personalization_engine.get_user_analytics(self.user_id)
                if analytics and analytics.get('total_feedback_count', 0) > 0:
                    print("\n[Personalization applied based on your preferences]")
            except Exception as e:
                print(f"Personalization error: {e}")
        
        return intervention
    
    def display_results(self, detection_result: Dict[str, Any], risk_level: str, intervention: str):
        """Display all results to user"""
        print("\n" + "=" * 60)
        print("ANALYSIS RESULTS")
        print("=" * 60)
        
        print("\n--- Detection Summary ---")
        print(f"Emotional Signal: {detection_result.get('emotional_signal', 'N/A')}")
        print(f"Primary Root Cause: {detection_result.get('root_cause', 'N/A')}")
        print(f"Analysis Confidence: {detection_result.get('confidence', 'N/A')}")
        
        print("\n--- Procrastination Risk Level ---")
        risk_colors = {
            "LOW": "🟢",
            "MEDIUM": "🟡", 
            "HIGH": "🔴"
        }
        print(f"{risk_colors.get(risk_level, '⚪')} {risk_level}")
        
        print("\n--- Suggested Academic Support ---")
        print(intervention)
        
        print("\n" + "=" * 60)
    
    def collect_feedback(self) -> str:
        """Collect user feedback on intervention"""
        print("\n" + "-" * 40)
        print("Was this suggestion helpful for your academic situation?")
        print("Options: helpful, not_helpful, skip")
        print("-" * 40)
        
        while True:
            feedback = input(">> ").strip().lower()
            
            valid_feedback = ["helpful", "not_helpful", "skip"]
            if feedback in valid_feedback:
                return feedback
            else:
                print("Please enter: helpful, not_helpful, or skip")
    
    def process_feedback(self, feedback: str, intervention: str):
        """Process user feedback for personalization"""
        if feedback == "skip":
            return
        
        print("\n" + "-" * 40)
        print("Processing your feedback...")
        print("-" * 40)
        
        if self.personalization_engine:
            try:
                # Update personalization engine with feedback
                feedback_data = {
                    "intervention_id": "demo_intervention",
                    "feedback_type": "rating",
                    "feedback_data": {
                        "rating": 5 if feedback == "helpful" else 1,
                        "intervention_type": "motivational"
                    },
                    "source": "direct"
                }
                
                success = self.personalization_engine.update(self.user_id, feedback_data)
                if success:
                    print("✓ Your feedback has been recorded for future improvements.")
                else:
                    print("⚠ Feedback processing encountered an issue.")
            except Exception as e:
                print(f"Feedback processing error: {e}")
        else:
            print("✓ Thank you for your feedback!")
    
    def display_session_summary(self):
        """Display session summary"""
        print("\n" + "=" * 60)
        print("SESSION SUMMARY")
        print("=" * 60)
        
        print(f"Sessions completed: {self.session_count}")
        print("Your feedback helps improve future suggestions.")
        
        if self.personalization_engine:
            try:
                analytics = self.personalization_engine.get_user_analytics(self.user_id)
                if analytics:
                    print(f"Total feedback provided: {analytics.get('total_feedback_count', 0)}")
            except Exception:
                pass
        
        print("\nThank you for using PRCI v2.0!")
        print("Remember: This system provides academic support suggestions and")
        print("does not offer psychological or medical advice.")
        print("=" * 60)
    
    def run_session(self):
        """Run a single interaction session"""
        self.session_count += 1
        
        # Get user input
        user_input = self.get_user_input()
        self.session_data["inputs"].append(user_input)
        
        # Process through detection
        detection_result = self.process_detection(user_input)
        self.session_data["detection_results"].append(detection_result)
        
        # Assess risk
        risk_level = self.assess_risk(detection_result)
        self.session_data["risk_levels"].append(risk_level)
        
        # Generate intervention
        root_cause = detection_result.get("root_cause", "task_overload")
        intervention = self.generate_intervention(risk_level, root_cause)
        
        # Apply personalization
        personalized_intervention = self.apply_personalization(intervention)
        self.session_data["interventions"].append(personalized_intervention)
        
        # Display results
        self.display_results(detection_result, risk_level, personalized_intervention)
        
        # Collect feedback
        feedback = self.collect_feedback()
        self.session_data["feedback"].append(feedback)
        
        # Process feedback
        self.process_feedback(feedback, personalized_intervention)
    
    def run(self):
        """Run the main application loop"""
        self.display_welcome()
        
        while True:
            try:
                self.run_session()
                
                # Ask if user wants to continue
                print("\n" + "-" * 40)
                continue_session = input("Would you like another session? (yes/no): ").strip().lower()
                
                if continue_session in ['no', 'n', 'exit', 'quit']:
                    break
                elif continue_session in ['yes', 'y']:
                    continue
                else:
                    print("Please enter 'yes' or 'no'")
                    continue
                    
            except KeyboardInterrupt:
                print("\n\nSession interrupted by user.")
                break
            except Exception as e:
                print(f"\nAn error occurred: {e}")
                print("The session will continue.")
                continue
        
        self.display_session_summary()


def main():
    """Main entry point for the console application"""
    try:
        app = PRCIConsoleApp()
        app.run()
    except Exception as e:
        print(f"Application error: {e}")
        print("Please restart the application.")


if __name__ == "__main__":
    main()
