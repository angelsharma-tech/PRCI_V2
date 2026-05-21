"""
Inference Service for PRCI v2
Phase 4.1 - Backend Stabilization & Architecture Refactor
"""

import os
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any
import time

from config import ROOT_CAUSE_DATASET, MODEL_CONFIG
from upgrade_pipeline.core.inference_engine import InferenceEngine
from upgrade_pipeline.conversation import ConversationEngine
from utils.logging_utils import get_logger, log_model_inference, PerformanceTimer

logger = get_logger(__name__)


class InferenceService:
    """
    Centralized inference service for mental health analysis
    """
    
    def __init__(self):
        self.inference_engine: Optional[InferenceEngine] = None
        self.conversation_engine: Optional[ConversationEngine] = None
        self.model_path: Optional[str] = None
        self.model_type: Optional[str] = None
        self._initialized = False
    
    def initialize(
        self,
        model_path: Optional[str] = None,
        model_type: str = None,
        force_rebuild: bool = False
    ) -> bool:
        """
        Initialize the inference engines
        """
        try:
            model_path = model_path or self._get_default_model_path()
            model_type = model_type or MODEL_CONFIG["default_type"]
            
            # Check if model file exists
            if not os.path.exists(model_path):
                logger.warning(f"Model file not found: {model_path}")
                return False
            
            # Check if dataset exists
            if not os.path.exists(ROOT_CAUSE_DATASET):
                logger.error(f"Dataset not found: {ROOT_CAUSE_DATASET}")
                return False
            
            # Initialize engines
            with PerformanceTimer("inference_initialization"):
                self.inference_engine = InferenceEngine(
                    bert_ckpt_path=model_path,
                    root_cause_dataset_path=ROOT_CAUSE_DATASET,
                    root_cause_model_type=model_type,
                    root_cause_model_dir=os.path.dirname(os.path.abspath(ROOT_CAUSE_DATASET))
                )
                
                self.conversation_engine = ConversationEngine(
                    self.inference_engine,
                    max_history=MODEL_CONFIG["conversation_max_history"]
                )
            
            self.model_path = model_path
            self.model_type = model_type
            self._initialized = True
            
            logger.info(f"Inference service initialized with model: {model_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize inference service: {e}")
            log_error(e, "inference_service_initialization")
            return False
    
    def is_initialized(self) -> bool:
        """Check if service is initialized"""
        return self._initialized and all([
            self.inference_engine is not None,
            self.conversation_engine is not None
        ])
    
    def _get_default_model_path(self) -> str:
        """Get default model path"""
        from config import DEFAULT_MODEL_PATH
        return DEFAULT_MODEL_PATH
    
    def analyze_text(
        self,
        text: str,
        include_confidence: bool = True,
        include_root_cause: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze text for mental health indicators
        """
        if not self.is_initialized():
            raise RuntimeError("Inference service not initialized")
        
        try:
            with PerformanceTimer("text_analysis"):
                # Get basic predictions
                depression_score = self.inference_engine.predict_depression(text)
                anxiety_score = self.inference_engine.predict_anxiety(text)
                
                result = {
                    "text": text,
                    "depression_score": depression_score,
                    "anxiety_score": anxiety_score,
                    "timestamp": time.time()
                }
                
                # Add confidence scores if requested
                if include_confidence:
                    # Note: This would need to be implemented in the actual inference engine
                    result["confidence"] = {
                        "depression": self._estimate_confidence(depression_score),
                        "anxiety": self._estimate_confidence(anxiety_score)
                    }
                
                # Add root cause analysis if requested
                if include_root_cause:
                    root_causes = self.inference_engine.predict_root_causes(text)
                    result["root_causes"] = root_causes
                
                # Log the inference
                log_model_inference(
                    model_type=self.model_type,
                    input_data={"text": text[:100] + "..." if len(text) > 100 else text},
                    output_data={
                        "depression": depression_score,
                        "anxiety": anxiety_score,
                        "root_causes": result.get("root_causes", {})
                    },
                    confidence=result.get("confidence", {}).get("depression"),
                    processing_time=None  # Would be captured by PerformanceTimer
                )
                
                return result
                
        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            log_error(e, f"text_analysis - text: {text[:50]}...")
            raise
    
    def get_risk_level(
        self,
        depression_score: float,
        anxiety_score: float,
        root_causes: Optional[Dict[str, float]] = None
    ) -> str:
        """
        Calculate overall risk level
        """
        try:
            # Weight the scores (can be adjusted based on clinical requirements)
            depression_weight = 0.5
            anxiety_weight = 0.5
            
            # Calculate weighted average
            overall_score = (depression_score * depression_weight) + (anxiety_score * anxiety_weight)
            
            # Consider root cause severity if available
            if root_causes:
                max_root_cause = max(root_causes.values())
                # Boost risk if any root cause is high
                if max_root_cause > 0.7:
                    overall_score = min(overall_score * 1.2, 1.0)
            
            # Determine risk level
            if overall_score < 0.33:
                return "LOW"
            elif overall_score < 0.66:
                return "MODERATE"
            else:
                return "HIGH"
                
        except Exception as e:
            logger.error(f"Error calculating risk level: {e}")
            return "MODERATE"  # Default to moderate
    
    def get_top_root_cause(self, root_causes: Dict[str, float]) -> str:
        """
        Get the primary root cause
        """
        try:
            if not root_causes:
                return "none"
            
            return max(root_causes.items(), key=lambda x: x[1])[0]
            
        except Exception as e:
            logger.error(f"Error getting top root cause: {e}")
            return "none"
    
    def batch_analyze(
        self,
        texts: List[str],
        include_confidence: bool = True,
        include_root_cause: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple texts in batch
        """
        if not self.is_initialized():
            raise RuntimeError("Inference service not initialized")
        
        results = []
        
        with PerformanceTimer("batch_analysis", {"text_count": len(texts)}):
            for i, text in enumerate(texts):
                try:
                    result = self.analyze_text(text, include_confidence, include_root_cause)
                    result["batch_index"] = i
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error analyzing text {i}: {e}")
                    # Add error result to maintain batch consistency
                    results.append({
                        "text": text,
                        "error": str(e),
                        "batch_index": i,
                        "timestamp": time.time()
                    })
        
        return results
    
    def get_conversation_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Get response from conversation engine
        """
        if not self.is_initialized():
            raise RuntimeError("Inference service not initialized")
        
        try:
            with PerformanceTimer("conversation_response"):
                # Add message to conversation
                response = self.conversation_engine.respond(user_message)
                
                result = {
                    "user_message": user_message,
                    "bot_response": response,
                    "timestamp": time.time(),
                    "conversation_history_length": len(self.conversation_engine.history)
                }
                
                # Log the interaction
                log_model_inference(
                    model_type="conversation",
                    input_data={"user_message": user_message},
                    output_data={"bot_response": response[:200] + "..." if len(response) > 200 else response},
                    processing_time=None
                )
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting conversation response: {e}")
            log_error(e, f"conversation_response - message: {user_message[:50]}...")
            raise
    
    def clear_conversation_history(self) -> bool:
        """
        Clear conversation history
        """
        try:
            if self.conversation_engine:
                self.conversation_engine.clear_history()
                logger.info("Conversation history cleared")
                return True
            return False
        except Exception as e:
            logger.error(f"Error clearing conversation history: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model
        """
        if not self.is_initialized():
            return {"status": "not_initialized"}
        
        return {
            "status": "initialized",
            "model_path": self.model_path,
            "model_type": self.model_type,
            "dataset_path": ROOT_CAUSE_DATASET,
            "conversation_history_length": len(self.conversation_engine.history) if self.conversation_engine else 0
        }
    
    def _estimate_confidence(self, score: float) -> float:
        """
        Estimate confidence based on score (placeholder implementation)
        In a real implementation, this would come from the model's confidence output
        """
        # Simple heuristic: scores near 0 or 1 have higher confidence
        distance_from_center = abs(score - 0.5)
        return 0.5 + distance_from_center
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the inference service
        """
        health_status = {
            "status": "healthy",
            "checks": {},
            "timestamp": time.time()
        }
        
        try:
            # Check initialization
            health_status["checks"]["initialization"] = self.is_initialized()
            
            # Check model file
            health_status["checks"]["model_file_exists"] = os.path.exists(self.model_path) if self.model_path else False
            
            # Check dataset
            health_status["checks"]["dataset_exists"] = os.path.exists(ROOT_CAUSE_DATASET)
            
            # Test inference with dummy data
            if self.is_initialized():
                try:
                    test_result = self.analyze_text("I feel fine today.", include_confidence=False, include_root_cause=False)
                    health_status["checks"]["test_inference"] = "success"
                except Exception as e:
                    health_status["checks"]["test_inference"] = f"failed: {str(e)}"
            else:
                health_status["checks"]["test_inference"] = "skipped"
            
            # Determine overall status
            if not all(health_status["checks"].values()):
                health_status["status"] = "unhealthy"
            
        except Exception as e:
            health_status["status"] = "error"
            health_status["error"] = str(e)
            logger.error(f"Health check failed: {e}")
        
        return health_status


# Global instance
_inference_service = None


def get_inference_service() -> InferenceService:
    """
    Get the global inference service instance
    """
    global _inference_service
    if _inference_service is None:
        _inference_service = InferenceService()
    return _inference_service


def log_error(error: Exception, context: str = None) -> None:
    """
    Log errors with context
    """
    logger = get_logger("inference_service_errors")
    logger.error(f"Error in {context}: {error}", exc_info=True)
