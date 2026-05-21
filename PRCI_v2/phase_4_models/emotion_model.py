"""
Emotion Detection Model

Detects anxiety-like and stress-related
signals from user text.

NOTE:
This is a behavioral indicator model,
not a clinical diagnostic tool.
"""

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import cross_val_score
import numpy as np
from typing import List, Optional, Dict, Any, Tuple
import pickle
import os


class EmotionModel:
    """
    Emotion detection model for identifying anxiety-like and stress-related signals.
    
    This model uses classical machine learning to detect behavioral indicators
    of stress and anxiety in academic contexts, providing probabilistic
    outputs for risk assessment while maintaining non-clinical boundaries.
    """
    
    def __init__(self, random_state: int = 42):
        """
        Initialize the emotion detection model.
        
        Args:
            random_state: Random state for reproducibility
        """
        self.model = LogisticRegression(
            max_iter=1000,
            random_state=random_state,
            class_weight='balanced',  # Handle class imbalance
            solver='liblinear',
            penalty='l2',
            C=1.0
        )
        self.is_trained = False
        self.classes_ = None
        self.feature_names = None
        self.training_history = []
    
    def train(self, X: np.ndarray, y: np.ndarray, 
              feature_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Train the emotion detection model.
        
        Args:
            X: Feature matrix
            y: Target labels (0=non-anxiety, 1=anxiety-like)
            feature_names: Names of features for interpretability
            
        Returns:
            Dict: Training results and metrics
            
        TODO (Phase-4):
        - Add cross-validation for robust evaluation
        - Implement class imbalance handling strategies
        - Add feature importance analysis
        """
        # Validate inputs
        if X.shape[0] != len(y):
            raise ValueError("Number of samples in X and y must match")
        
        if len(np.unique(y)) != 2:
            raise ValueError("Emotion model requires binary classification (2 classes)")
        
        # Store feature names for interpretability
        self.feature_names = feature_names
        
        # Train the model
        self.model.fit(X, y)
        self.classes_ = self.model.classes_
        self.is_trained = True
        
        # Calculate training metrics
        y_pred = self.model.predict(X)
        y_proba = self.model.predict_proba(X)
        
        training_results = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, average='binary'),
            'recall': recall_score(y, y_pred, average='binary'),
            'f1_score': f1_score(y, y_pred, average='binary'),
            'training_samples': len(y),
            'feature_count': X.shape[1],
            'class_distribution': dict(zip(*np.unique(y, return_counts=True)))
        }
        
        # Store training history
        self.training_history.append(training_results)
        
        return training_results
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict probability of anxiety-like indicators.
        
        Args:
            X: Feature matrix
            
        Returns:
            np.ndarray: Probability predictions [non_anxiety, anxiety]
            
        TODO (Phase-4):
        - Add prediction confidence scoring
        - Implement uncertainty estimation
        - Add prediction validation
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        return self.model.predict_proba(X)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict binary emotion classification.
        
        Args:
            X: Feature matrix
            
        Returns:
            np.ndarray: Binary predictions (0 or 1)
            
        TODO (Phase-4):
        - Add prediction threshold tuning
        - Implement cost-sensitive prediction
        - Add prediction explanation
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        return self.model.predict(X)
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        Evaluate model performance.
        
        Args:
            X: Test feature matrix
            y: True labels
            
        Returns:
            Dict: Evaluation metrics
            
        TODO (Phase-4):
        - Add more comprehensive evaluation metrics
        - Implement ROC curve analysis
        - Add confusion matrix analysis
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        y_pred = self.model.predict(X)
        y_proba = self.model.predict_proba(X)
        
        return {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, average='binary'),
            'recall': recall_score(y, y_pred, average='binary'),
            'f1_score': f1_score(y, y_pred, average='binary'),
            'auc_score': self._calculate_auc(y, y_proba[:, 1])
        }
    
    def _calculate_auc(self, y_true: np.ndarray, y_scores: np.ndarray) -> float:
        """
        Calculate AUC score for binary classification.
        
        Args:
            y_true: True labels
            y_scores: Predicted scores
            
        Returns:
            float: AUC score
            
        TODO (Phase-4):
        - Implement proper ROC curve calculation
        - Add confidence intervals for AUC
        - Add multi-class AUC support
        """
        try:
            from sklearn.metrics import roc_auc_score
            return roc_auc_score(y_true, y_scores)
        except ImportError:
            # Simple approximation if sklearn metrics not available
            return 0.5  # Random baseline
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance coefficients.
        
        Returns:
            Dict: Feature importance scores
            
        TODO (Phase-4):
        - Add statistical significance testing
        - Implement feature importance visualization
        - Add feature grouping analysis
        """
        if not self.is_trained:
            raise ValueError("Model must be trained first")
        
        if self.feature_names is None:
            return {}
        
        # Get coefficients for the positive class (anxiety-like)
        coefficients = self.model.coef_[0]
        
        feature_importance = {}
        for i, feature_name in enumerate(self.feature_names):
            if i < len(coefficients):
                feature_importance[feature_name] = float(coefficients[i])
        
        return feature_importance
    
    def get_top_features(self, n: int = 10, positive: bool = True) -> List[Tuple[str, float]]:
        """
        Get top features by importance.
        
        Args:
            n: Number of top features to return
            positive: Whether to return positive (anxiety) or negative features
            
        Returns:
            List of tuples: (feature_name, importance_score)
            
        TODO (Phase-4):
        - Add feature category analysis
        - Implement statistical significance filtering
        - Add feature interaction analysis
        """
        if not self.is_trained:
            raise ValueError("Model must be trained first")
        
        feature_importance = self.get_feature_importance()
        
        # Sort features by importance
        sorted_features = sorted(feature_importance.items(), key=lambda x: abs(x[1]), reverse=True)
        
        # Filter by sign if specified
        if positive:
            sorted_features = [(f, s) for f, s in sorted_features if s > 0]
        else:
            sorted_features = [(f, s) for f, s in sorted_features if s < 0]
        
        return sorted_features[:n]
    
    def cross_validate(self, X: np.ndarray, y: np.ndarray, cv: int = 5) -> Dict[str, float]:
        """
        Perform cross-validation evaluation.
        
        Args:
            X: Feature matrix
            y: Target labels
            cv: Number of cross-validation folds
            
        Returns:
            Dict: Cross-validation results
            
        TODO (Phase-4):
        - Add stratified cross-validation
        - Implement temporal cross-validation
        - Add cross-validation visualization
        """
        if len(np.unique(y)) != 2:
            raise ValueError("Cross-validation requires binary classification")
        
        # Perform cross-validation
        cv_scores = cross_val_score(self.model, X, y, cv=cv, scoring='f1')
        
        return {
            'cv_f1_mean': np.mean(cv_scores),
            'cv_f1_std': np.std(cv_scores),
            'cv_scores': cv_scores.tolist(),
            'cv_folds': cv
        }
    
    def save_model(self, filepath: str) -> bool:
        """
        Save the trained model to disk.
        
        Args:
            filepath: Path to save the model
            
        Returns:
            bool: True if successful
            
        TODO (Phase-4):
        - Add model versioning
        - Implement model compression
        - Add model validation after loading
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before saving")
        
        try:
            model_data = {
                'model': self.model,
                'classes_': self.classes_,
                'feature_names': self.feature_names,
                'is_trained': self.is_trained,
                'training_history': self.training_history
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def load_model(self, filepath: str) -> bool:
        """
        Load a trained model from disk.
        
        Args:
            filepath: Path to the saved model
            
        Returns:
            bool: True if successful
            
        TODO (Phase-4):
        - Add model compatibility checking
        - Implement model validation
        - Add version migration support
        """
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.classes_ = model_data['classes_']
            self.feature_names = model_data.get('feature_names')
            self.is_trained = model_data['is_trained']
            self.training_history = model_data.get('training_history', [])
            
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the trained model.
        
        Returns:
            Dict: Model information
            
        TODO (Phase-4):
        - Add model performance summary
        - Implement training data statistics
        - Add model configuration details
        """
        info = {
            'model_type': 'LogisticRegression',
            'is_trained': self.is_trained,
            'classes': self.classes_.tolist() if self.classes_ is not None else None,
            'feature_count': len(self.feature_names) if self.feature_names else None,
            'training_history_count': len(self.training_history)
        }
        
        if self.is_trained:
            info.update({
                'model_params': self.model.get_params(),
                'last_training_metrics': self.training_history[-1] if self.training_history else None
            })
        
        return info
    
    def reset_model(self) -> None:
        """
        Reset the model to untrained state.
        
        TODO (Phase-4):
        - Add model state validation
        - Implement partial reset options
        - Add reset confirmation
        """
        self.model = LogisticRegression(
            max_iter=1000,
            random_state=42,
            class_weight='balanced',
            solver='liblinear',
            penalty='l2',
            C=1.0
        )
        self.is_trained = False
        self.classes_ = None
        self.feature_names = None
        self.training_history = []
