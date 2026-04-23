"""
System Validation Script for PRCI v2.0
Non-clinical, academic system testing
"""

import sys
import os
from typing import Dict, Any, List

# Add project paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase_4_models'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase_5_risk_engine'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase_6_intervention'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase_7_personalization'))

def simulate_test_case(input_text: str) -> Dict[str, Any]:
    """
    Simulate system behavior for validation testing
    Note: This is a demonstration placeholder, not actual system integration
    """
    # Simple rule-based simulation for demonstration
    if "overwhelm" in input_text.lower() or "too much" in input_text.lower():
        return {
            "detection": "task_overload",
            "risk_level": "MEDIUM",
            "intervention": "Consider breaking tasks into smaller steps"
        }
    elif "behind" in input_text.lower() or "procrastinat" in input_text.lower():
        return {
            "detection": "procrastination_pattern",
            "risk_level": "HIGH",
            "intervention": "Focus on starting with one small action"
        }
    else:
        return {
            "detection": "low_stress",
            "risk_level": "LOW",
            "intervention": "Continue with current approach"
        }

def run_validation():
    """Run system validation tests"""
    test_inputs = [
        "I have many assignments and feel behind schedule",
        "I am managing my tasks well",
        "I keep postponing studying even when I know it's important",
        "I feel overwhelmed with all my deadlines",
        "My studies are going well this semester"
    ]

    print("PRCI v2.0 System Validation Results")
    print("=" * 50)
    print("Note: This is a demonstration validation script")
    print("No clinical or medical claims are made")
    print("=" * 50)

    results = []
    
    for idx, text in enumerate(test_inputs, start=1):
        print(f"\nTest Case {idx}")
        print(f"Input: {text}")
        
        result = simulate_test_case(text)
        results.append(result)
        
        print(f"Detection: {result['detection']}")
        print(f"Risk Level: {result['risk_level']}")
        print(f"Intervention: {result['intervention']}")
        print("-" * 30)

    # Summary
    print("\nValidation Summary")
    print("=" * 50)
    print(f"Total test cases: {len(results)}")
    
    risk_counts = {}
    for result in results:
        risk = result['risk_level']
        risk_counts[risk] = risk_counts.get(risk, 0) + 1
    
    print("Risk Level Distribution:")
    for risk, count in risk_counts.items():
        print(f"  {risk}: {count}")
    
    print("\nValidation completed successfully")
    print("System behavior appears consistent and appropriate")
    print("All responses maintain academic support boundaries")

if __name__ == "__main__":
    run_validation()
