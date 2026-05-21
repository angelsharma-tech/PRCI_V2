#!/usr/bin/env python3
"""Test Phase 3A.3 natural conversation flow."""

import sys
import os
sys.path.insert(0, r'd:\PRCI_v2\PRCI_v2')

from upgrade_pipeline.conversation import ConversationEngine


class FakeEngine:
    def run_full_inference(self, text):
        return {
            'emotion': {'depression_score': 0.4, 'anxiety_score': 0.6},
            'risk': {'level': 'MODERATE', 'score': 0.5},
            'root_causes': {'top_root_cause': 'perfectionism'},
            'planner': {},
        }


def test_natural_responses():
    """Test varied, natural response patterns."""
    chat = ConversationEngine(FakeEngine())
    
    test_cases = [
        "I feel guilty for falling behind.",
        "My studies are overwhelming me.",
        "I can't sleep and my mind races.",
        "I feel so alone lately.",
        "I'm completely burned out.",
    ]
    
    print("=== NATURAL CONVERSATION TEST ===")
    for i, msg in enumerate(test_cases, 1):
        result = chat.generate_response(msg)
        print(f"\n--- Turn {i} ---")
        print(f"User: {msg}")
        print(f"Assistant: {result['response']}")
        if result['follow_up']:
            print(f"Follow-up: {result['follow_up']}")
        else:
            print("(No follow-up - natural pause)")


if __name__ == "__main__":
    test_natural_responses()
