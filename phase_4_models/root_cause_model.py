"""
Root Cause Classification Model

Classifies primary behavioral causes
(e.g., lack of motivation, overload,
fear of failure).
"""

import json
import os
import pickle
from typing import Any, Dict, List, Optional

import numpy as np


class RootCauseModel:
    """
    Root cause classification model for identifying procrastination triggers.
    
    This model uses classical machine learning to classify the primary
    behavioral causes of procrastination in academic contexts,
    supporting targeted intervention strategies.
    """
    
    def __init__(self, threshold: float = 0.5, models_dir: Optional[str] = None):
        """Initialize inference-only root cause model.

        Args:
            threshold: Probability threshold for returning a label as a hit
            models_dir: Directory containing inference artifacts
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.models_dir = models_dir or base_dir
        self.threshold = float(threshold)

        self.tfidf = None
        self.ovr_logreg = None
        self.labels: List[str] = []
        self.is_loaded = False
    
    def load(self, models_dir: Optional[str] = None) -> "RootCauseModel":
        """Load inference artifacts from disk."""
        if models_dir:
            self.models_dir = models_dir

        tfidf_path = os.path.join(self.models_dir, "root_tfidf.pkl")
        model_path = os.path.join(self.models_dir, "root_ovr_logreg.pkl")
        labels_path = os.path.join(self.models_dir, "root_labels.json")

        if not os.path.exists(tfidf_path):
            raise FileNotFoundError(f"Missing TF-IDF artifact: {tfidf_path}")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Missing OVR LogisticRegression artifact: {model_path}")
        if not os.path.exists(labels_path):
            raise FileNotFoundError(f"Missing labels artifact: {labels_path}")

        with open(tfidf_path, "rb") as f:
            self.tfidf = pickle.load(f)

        with open(model_path, "rb") as f:
            self.ovr_logreg = pickle.load(f)

        with open(labels_path, "r", encoding="utf-8") as f:
            self.labels = json.load(f)

        self.is_loaded = True
        return self
    
    def _predict_proba_ovr(self, X_vec) -> np.ndarray:
        if hasattr(self.ovr_logreg, "predict_proba"):
            P = self.ovr_logreg.predict_proba(X_vec)
            if isinstance(P, list):
                P = np.column_stack(P)
            return P

        raise RuntimeError("Loaded classifier does not support probability prediction.")
    
    def predict(self, text: str) -> Dict[str, Any]:
        """Predict root causes for a single text input.

        Returns:
            Dict: {
                "root_causes": [..],
                "probabilities": {label: prob}
            }
        """
        if not self.is_loaded:
            self.load()

        X_vec = self.tfidf.transform([str(text)])
        P_all = self._predict_proba_ovr(X_vec)

        n = min(len(self.labels), P_all.shape[1])
        active_labels = self.labels[:n]

        probs = {lbl: float(P_all[0, i]) for i, lbl in enumerate(active_labels)}
        hits = [lbl for lbl, p in probs.items() if p >= self.threshold]

        return {
            "root_causes": hits,
            "probabilities": probs,
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "type": "RootCauseModel",
            "is_loaded": self.is_loaded,
            "models_dir": self.models_dir,
            "labels": self.labels,
            "threshold": self.threshold,
        }
