"""
Detection Engine Implementation

Implements DetectionEngine interface
defined in Phase-2 with integrated Root Cause inference logic
from mhealth-intake system.
"""

import os
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime

from .detection_interface import DetectionEngine, DetectionResult
from .emotion_model import EmotionModel
from .root_cause_model import RootCauseModel
from .feature_extractor import FeatureExtractor


class DetectionEngineImpl(DetectionEngine):
    """
    Implementation of the DetectionEngine interface with integrated
    Root Cause inference from mhealth-intake system.
    
    This class combines emotion detection and root cause classification
    models to provide comprehensive behavioral analysis for
    procrastination prediction and intervention systems.
    """
    
    def __init__(self, emotion_model: Optional[EmotionModel] = None, 
                 root_model: Optional[RootCauseModel] = None, 
                 extractor: Optional[FeatureExtractor] = None,
                 models_dir: Optional[str] = None):
        """
        Initialize the detection engine implementation.
        
        Args:
            emotion_model: Trained emotion detection model
            root_model: Trained root cause classification model  
            extractor: Fitted feature extractor
            models_dir: Directory containing mhealth-intake model artifacts
        """
        self.emotion_model = emotion_model
        self.root_model = root_model
        self.extractor = extractor

        # Initialize governed Root Cause inference (inference-only artifacts)
        self.root_cause_inference = (root_model or RootCauseModel(models_dir=models_dir)).load(models_dir=models_dir)
        
        self.is_initialized = True
        
        # Validate that components are ready (if provided)
        if emotion_model or root_model or extractor:
            self._validate_components()
    
    def predict(self, text: str, context: Optional[Dict[str, Any]] = None) -> DetectionResult:
        """
        Analyze user text and return emotional
        and behavioral indicators.
        
        Args:
            text: User text to analyze
            context: Additional context information
            
        Returns:
            DetectionResult: Structured detection output
        """
        # Validate input
        if not text or not isinstance(text, str):
            return self._create_default_result(context)
        
        try:
            # Initialize default values
            anxiety_prob = 0.0
            depression_prob = 0.0
            root_causes = []
            confidence = 0.0
            
            # Get emotion predictions if emotion model is available
            if self.emotion_model and self.extractor:
                try:
                    X = self.extractor.transform([text])
                    emotion_probs = self.emotion_model.predict_proba(X)[0]
                    
                    # Map emotion probabilities to specific indicators
                    # Assuming binary classification: [non_anxiety, anxiety]
                    anxiety_prob = float(emotion_probs[1])
                    depression_prob = float(emotion_probs[0])  # Using non-anxiety as depression indicator
                    
                except Exception as e:
                    print(f"Emotion prediction failed: {e}")
            
            # Get root cause predictions (governed artifacts)
            root_cause_result = self.root_cause_inference.predict(text)
            root_causes = root_cause_result.get("root_causes", [])
            
            # Calculate confidence based on available predictions
            if self.emotion_model and self.extractor:
                try:
                    X = self.extractor.transform([text])
                    emotion_probs = self.emotion_model.predict_proba(X)[0]
                    emotion_confidence = np.max(emotion_probs)
                    
                    # Use root cause probability confidence if available
                    root_cause_probs = root_cause_result.get("probabilities", {})
                    root_cause_confidence = max(root_cause_probs.values()) if root_cause_probs else 0.0
                    
                    # Average confidence
                    confidence = (emotion_confidence + root_cause_confidence) / 2.0
                    
                except Exception as e:
                    print(f"Confidence calculation failed: {e}")
                    confidence = 0.0
            else:
                # Use only root cause confidence
                root_cause_probs = root_cause_result.get("probabilities", {})
                confidence = max(root_cause_probs.values()) if root_cause_probs else 0.0
            
            # Create detection result
            result = DetectionResult(
                anxiety_prob=anxiety_prob,
                depression_prob=depression_prob,
                root_causes=root_causes,
                confidence=confidence,
                timestamp=datetime.now(),
                context=context or {}
            )
            
            return result
            
        except Exception as e:
            print(f"Error in detection prediction: {e}")
            return self._create_error_result(context, str(e))
    
    def _validate_components(self) -> None:
        """
        Validate that components are properly initialized.
        Modified to handle optional components.
        """
        if self.emotion_model and not self.emotion_model.is_trained:
            print("Warning: Emotion model is not trained")
        
        if self.root_model and not self.root_model.is_trained:
            print("Warning: Root cause model is not trained")
        
        if self.extractor and not self.extractor.is_fitted:
            print("Warning: Feature extractor is not fitted")
        
        # Root Cause inference validation
        if not self.root_cause_inference.is_loaded:
            print("Warning: Root Cause inference models not loaded")
    
    def _create_default_result(self, context: Optional[Dict[str, Any]]) -> DetectionResult:
        """
        Create a default detection result for edge cases.
        
        Args:
            context: Context information
            
        Returns:
            DetectionResult: Default result
        """
        return DetectionResult(
            anxiety_prob=0.0,
            depression_prob=0.0,
            root_causes=[],
            confidence=0.0,
            timestamp=datetime.now(),
            context=context or {}
        )
    
    def _create_error_result(self, context: Optional[Dict[str, Any]], 
                          error_message: str) -> DetectionResult:
        """
        Create an error detection result.
        
        Args:
            context: Context information
            error_message: Error description
            
        Returns:
            DetectionResult: Error result
        """
        return DetectionResult(
            anxiety_prob=0.0,
            depression_prob=0.0,
            root_causes=["error"],
            confidence=0.0,
            timestamp=datetime.now(),
            context={
                **(context or {}),
                "error": error_message
            }
        )
    
    def batch_predict(self, texts: List[str], 
                    contexts: Optional[List[Dict[str, Any]]] = None) -> List[DetectionResult]:
        """
        Predict detection results for multiple texts.
        
        Args:
            texts: List of texts to analyze
            contexts: List of context dictionaries
            
        Returns:
            List[DetectionResult]: Detection results for each text
        """
        if contexts is None:
            contexts = [{}] * len(texts)
        
        results = []
        for text, context in zip(texts, contexts):
            result = self.predict(text, context)
            results.append(result)
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the detection engine models.
        
        Returns:
            Dict: Model information
        """
        info = {
            "detection_engine_type": "DetectionEngineImpl",
            "is_initialized": self.is_initialized,
            "root_cause_inference": {
                "is_loaded": self.root_cause_inference.is_loaded,
                "models_dir": self.root_cause_inference.models_dir,
                "labels_count": len(self.root_cause_inference.labels),
                "labels": self.root_cause_inference.labels
            }
        }
        
        if self.emotion_model:
            info["emotion_model"] = self.emotion_model.get_model_info()
        
        if self.root_model:
            info["root_cause_model"] = self.root_model.get_model_info()
        
        if self.extractor:
            info["feature_extractor"] = {
                "is_fitted": self.extractor.is_fitted,
                "vocabulary_stats": self.extractor.get_vocabulary_stats()
            }
        
        return info
    
    def update_models(self, emotion_model: Optional[EmotionModel] = None,
                    root_model: Optional[RootCauseModel] = None,
                    extractor: Optional[FeatureExtractor] = None) -> None:
        """
        Update the detection engine models.
        
        Args:
            emotion_model: New emotion model (optional)
            root_model: New root cause model (optional)
            extractor: New feature extractor (optional)
        """
        if emotion_model:
            self.emotion_model = emotion_model
        
        if root_model:
            self.root_model = root_model
        
        if extractor:
            self.extractor = extractor
        
        # Re-validate components
        self._validate_components()
    
    def get_feature_importance(self) -> Dict[str, Any]:
        """
        Get feature importance from available models.
        
        Returns:
            Dict: Feature importance information
        """
        importance = {}
        
        if self.emotion_model:
            try:
                importance["emotion_importance"] = self.emotion_model.get_feature_importance()
            except Exception as e:
                print(f"Error getting emotion feature importance: {e}")
        
        if self.root_model:
            try:
                importance["root_cause_importance"] = self.root_model.get_feature_importance()
            except Exception as e:
                print(f"Error getting root cause feature importance: {e}")
        
        return importance
    
    def predict_with_explanation(self, text: str, 
                             context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Predict with detailed explanation.
        
        Args:
            text: User text to analyze
            context: Additional context information
            
        Returns:
            Dict: Prediction with explanation
        """
        # Get basic prediction
        result = self.predict(text, context)
        
        # Get root cause details
        root_cause_result = self.root_cause_inference.predict_root_causes(text)
        
        explanation = {
            "detection_result": result,
            "explanation": {
                "root_cause_probs": root_cause_result.get("root_cause_probs", {}),
                "root_cause_hits": root_cause_result.get("root_cause_hits", []),
                "root_cause_available": self.root_cause_inference.is_loaded,
                "emotion_available": bool(self.emotion_model and self.extractor)
            }
        }
        
        # Add emotion explanation if available
        if self.emotion_model and self.extractor:
            try:
                X = self.extractor.transform([text])
                emotion_probs = self.emotion_model.predict_proba(X)[0]
                
                explanation["explanation"]["emotion_confidence"] = float(np.max(emotion_probs))
                explanation["explanation"]["emotion_probs"] = {
                    "anxiety": float(emotion_probs[1]),
                    "non_anxiety": float(emotion_probs[0])
                }
                
            except Exception as e:
                explanation["explanation"]["emotion_error"] = str(e)
        
        return explanation
    
    def initialize(self) -> bool:
        """
        Initialize the detection engine.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            self._validate_components()
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"Detection engine initialization failed: {e}")
            self.is_initialized = False
            return False
    
    def reload_root_cause_models(self, models_dir: Optional[str] = None) -> bool:
        """
        Reload Root Cause inference models.
        
        Args:
            models_dir: New models directory (optional)
            
        Returns:
            bool: True if reload successful
        """
        try:
            if models_dir:
                self.root_cause_inference = RootCauseInference(models_dir)
            else:
                self.root_cause_inference._load_models()
            
            return self.root_cause_inference.is_loaded
        except Exception as e:
            print(f"Error reloading Root Cause models: {e}")
            return False
