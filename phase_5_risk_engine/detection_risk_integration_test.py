"""
Integration Test: DetectionEngine → RiskEngine Pipeline

Tests complete compatibility between detection and risk assessment layers.
"""

import sys
import os
from datetime import datetime, timedelta

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase_4_models'))
sys.path.append(os.path.join(os.path.dirname(__file__)))

from detection_engine_impl import DetectionEngineImpl
from risk_engine import RiskEngine
from procrastination_risk_engine import ProcrastinationRiskEngine


def test_detection_risk_integration():
    """Test complete DetectionEngine → RiskEngine pipeline"""
    
    print("=== DetectionEngine -> RiskEngine Integration Test ===")
    
    # Step 1: Initialize DetectionEngine
    print("\n1. Initializing DetectionEngine...")
    try:
        detection_engine = DetectionEngineImpl(
            emotion_model=None,
            root_model=None,
            extractor=None
        )
        print(f"DetectionEngine initialized: {detection_engine.is_initialized}")
        print(f"Root Cause models loaded: {detection_engine.root_cause_inference.is_loaded}")
        
    except Exception as e:
        print(f"DetectionEngine initialization failed: {e}")
        return False
    
    # Step 2: Initialize RiskEngines
    print("\n2. Initializing RiskEngines...")
    try:
        # Test both risk engines
        risk_engine_v1 = RiskEngine()
        risk_engine_v2 = ProcrastinationRiskEngine()
        
        print("RiskEngine v1 (risk_engine.py) initialized")
        print("ProcrastinationRiskEngine v2 (procrastination_risk_engine.py) initialized")
        
    except Exception as e:
        print(f"RiskEngine initialization failed: {e}")
        return False
    
    # Step 3: Generate sample detection results
    print("\n3. Generating sample detection results...")
    try:
        sample_texts = [
            "I keep delaying my assignments because I feel they won't be perfect.",
            "I'm not interested in my courses anymore and can't focus.",
            "I'm afraid I'll fail if I don't do everything perfectly.",
            "My phone keeps distracting me from studying.",
            "I keep scrolling social media instead of working."
        ]
        
        detection_history = []
        
        for i, text in enumerate(sample_texts):
            # Create timestamp for each detection (spread over time)
            timestamp = datetime.now() - timedelta(hours=len(sample_texts)-i)
            
            result = detection_engine.predict(text, context={"session_id": i})
            detection_history.append(result)
            
            print(f"Detection {i+1}: {text[:40]}...")
            print(f"  Anxiety: {result.anxiety_prob:.3f}")
            print(f"  Depression: {result.depression_prob:.3f}")
            print(f"  Root causes: {result.root_causes}")
            print(f"  Confidence: {result.confidence:.3f}")
            print()
        
        print(f"Generated {len(detection_history)} detection results")
        
    except Exception as e:
        print(f"Detection generation failed: {e}")
        return False
    
    # Step 4: Test RiskEngine v1 (risk_engine.py)
    print("\n4. Testing RiskEngine v1...")
    try:
        risk_result_v1 = risk_engine_v1.compute_risk(detection_history)
        
        print("RiskEngine v1 Results:")
        print(f"  Risk Score: {risk_result_v1.score:.3f}")
        print(f"  Risk Level: {risk_result_v1.level}")
        print(f"  Trend: {risk_result_v1.trend}")
        print(f"  Confidence: {risk_result_v1.confidence:.3f}")
        print(f"  Contributing Factors: {risk_result_v1.contributing_factors}")
        print(f"  Recommendations: {risk_result_v1.recommendations}")
        
    except Exception as e:
        print(f"RiskEngine v1 failed: {e}")
        return False
    
    # Step 5: Test RiskEngine v2 (procrastination_risk_engine.py)
    print("\n5. Testing RiskEngine v2...")
    try:
        risk_result_v2 = risk_engine_v2.assess(detection_history)
        
        print("ProcrastinationRiskEngine v2 Results:")
        print(f"  Risk Score: {risk_result_v2.score:.3f}")
        print(f"  Risk Level: {risk_result_v2.level}")
        print(f"  Trend: {risk_result_v2.trend}")
        print(f"  Confidence: {risk_result_v2.confidence:.3f}")
        print(f"  Contributing Factors: {risk_result_v2.contributing_factors}")
        print(f"  Recommendations: {risk_result_v2.recommendations}")
        
    except Exception as e:
        print(f"RiskEngine v2 failed: {e}")
        return False
    
    # Step 6: Test edge cases
    print("\n6. Testing edge cases...")
    try:
        # Empty history
        empty_result_v1 = risk_engine_v1.compute_risk([])
        empty_result_v2 = risk_engine_v2.assess([])
        
        print(f"Empty history - v1: {empty_result_v1.level} (score: {empty_result_v1.score})")
        print(f"Empty history - v2: {empty_result_v2.level} (score: {empty_result_v2.score})")
        
        # Single detection
        single_result_v1 = risk_engine_v1.compute_risk([detection_history[0]])
        single_result_v2 = risk_engine_v2.assess([detection_history[0]])
        
        print(f"Single detection - v1: {single_result_v1.level} (score: {single_result_v1.score:.3f})")
        print(f"Single detection - v2: {single_result_v2.level} (score: {single_result_v2.score:.3f})")
        
    except Exception as e:
        print(f"Edge case testing failed: {e}")
        return False
    
    # Step 7: Verify data flow integrity
    print("\n7. Verifying data flow integrity...")
    try:
        # Check that all detection fields are accessible by risk engines
        for detection in detection_history:
            # Verify all required fields are present and accessible
            assert hasattr(detection, 'anxiety_prob'), "Missing anxiety_prob"
            assert hasattr(detection, 'depression_prob'), "Missing depression_prob"
            assert hasattr(detection, 'root_causes'), "Missing root_causes"
            assert hasattr(detection, 'confidence'), "Missing confidence"
            assert hasattr(detection, 'timestamp'), "Missing timestamp"
            assert hasattr(detection, 'context'), "Missing context"
            
            # Verify data types
            assert isinstance(detection.anxiety_prob, float), "anxiety_prob should be float"
            assert isinstance(detection.depression_prob, float), "depression_prob should be float"
            assert isinstance(detection.root_causes, list), "root_causes should be list"
            assert isinstance(detection.confidence, float), "confidence should be float"
            assert isinstance(detection.timestamp, datetime), "timestamp should be datetime"
            assert isinstance(detection.context, dict), "context should be dict"
        
        print("All detection fields verified and accessible")
        
    except Exception as e:
        print(f"Data flow integrity check failed: {e}")
        return False
    
    print("\n=== INTEGRATION TEST COMPLETE ===")
    print("DetectionEngine -> RiskEngine pipeline working perfectly")
    print("Both risk engines compatible with detection output")
    print("No refactoring required")
    print("Ready for UI integration")
    return True


if __name__ == "__main__":
    test_detection_risk_integration()
