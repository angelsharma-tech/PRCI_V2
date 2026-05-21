#!/usr/bin/env python3
"""Test script for Phase 3A.2 topic extraction and contextual follow-ups."""

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


def test_topic_extraction():
    """Test topic detection accuracy."""
    chat = ConversationEngine(FakeEngine())
    
    test_messages = [
        'My studies and sleep are getting worse.',
        'I feel anxious about my exams and can\'t focus.',
        'I feel so alone and isolated from my friends.',
        'I\'m completely burned out and have no motivation.',
        'I\'ve been procrastinating a lot lately.',
        'I just feel tired all the time.',
        'Work deadlines are making me nervous.',
        'I can\'t sleep and my mind keeps racing.',
    ]
    
    print('=== TOPIC EXTRACTION TEST ===')
    for msg in test_messages:
        topics = chat._extract_topics(msg)
        print(f'Message: "{msg}"')
        print(f'Detected topics: {topics}')
        print()


def test_contextual_responses():
    """Test contextual response generation."""
    chat = ConversationEngine(FakeEngine())
    
    print('=== CONTEXTUAL RESPONSE TEST ===')
    
    # Test sleep + studies combination
    result = chat.generate_response('My studies and sleep are getting worse.')
    print('User: My studies and sleep are getting worse.')
    print(f'Assistant: {result["response"]}')
    print(f'Follow-up: {result["follow_up"]}')
    print()
    
    # Test anxiety + studies
    result2 = chat.generate_response('I feel anxious about my exams and can\'t focus.')
    print('User: I feel anxious about my exams and can\'t focus.')
    print(f'Assistant: {result2["response"]}')
    print(f'Follow-up: {result2["follow_up"]}')
    print()
    
    # Test social isolation
    result3 = chat.generate_response('I feel so alone and isolated from my friends.')
    print('User: I feel so alone and isolated from my friends.')
    print(f'Assistant: {result3["response"]}')
    print(f'Follow-up: {result3["follow_up"]}')
    print()
    
    # Test burnout
    result4 = chat.generate_response('I\'m completely burned out and have no motivation.')
    print('User: I\'m completely burned out and have no motivation.')
    print(f'Assistant: {result4["response"]}')
    print(f'Follow-up: {result4["follow_up"]}')


if __name__ == "__main__":
    test_topic_extraction()
    test_contextual_responses()
