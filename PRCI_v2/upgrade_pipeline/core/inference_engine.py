"""Centralized inference orchestrator for the mental-health upgrade pipeline.

This module encapsulates all model interactions and returns a single structured
dictionary for downstream consumers such as:

* Streamlit UI
* Chatbot backends
* FastAPI endpoints
* Batch inference jobs
* Unit / integration tests

Usage:
    engine = InferenceEngine(
        bert_ckpt_path="path/to/best.pt",
        root_cause_dataset_path="path/to/root_cause_dataset.csv",
    )
    result = engine.run_full_inference("I feel overwhelmed by deadlines...")
"""

import os
from dataclasses import asdict
from typing import Any, Dict, List, Optional

import pandas as pd

from ..preprocess import preprocess_text, TwoHeadBertInference
from ..root_cause_model import RootCauseClassifier
from ..risk_engine import calculate_risk_score
from ..planner import generate_planner
from ..web_agent import get_suggestions
from ..tracker import SlidingWindowTracker, TrackerEntry


class InferenceEngine:
    """Orchestrates the full inference pipeline end-to-end.

    The engine owns stateful components (BERT model, fitted root-cause
    classifier, sliding-window tracker) and exposes a single method
    ``run_full_inference`` that returns a normalized result dictionary.
    """

    _SERIALIZED_FILES = [
        "upgrade_root_tfidf.pkl",
        "upgrade_root_model.pkl",
        "upgrade_root_labels.pkl",
    ]

    def __init__(
        self,
        bert_ckpt_path: str,
        root_cause_dataset_path: str,
        root_cause_model_type: str = "ovr_logreg",
        tracker_window_size: int = 7,
        root_cause_model_dir: Optional[str] = None,
    ) -> None:
        """Initialize all pipeline modules.

        Args:
            bert_ckpt_path: Absolute or relative path to the two-head BERT
                checkpoint (``.pt`` file).
            root_cause_dataset_path: Path to the CSV used to fit the
                :class:`RootCauseClassifier` when no serialized model is found.
            root_cause_model_type: Model flavour for root-cause classification.
                One of ``"ovr_logreg"`` or ``"xgboost"``. Defaults to
                ``"ovr_logreg"``.
            tracker_window_size: Maximum number of entries retained by the
                sliding-window tracker. Defaults to ``7``.
            root_cause_model_dir: Directory containing serialized
                :class:`RootCauseClassifier` artefacts. If provided and all
                required files exist, the fitted model is loaded instead of
                retraining. If provided but files are missing, the model is
                fitted and automatically saved to this directory.

        Raises:
            FileNotFoundError: If the BERT checkpoint or root-cause dataset
                does not exist.
            ValueError: If ``tracker_window_size`` is not a positive integer.
        """
        if not bert_ckpt_path:
            raise ValueError("bert_ckpt_path must be provided.")
        if not os.path.exists(bert_ckpt_path):
            raise FileNotFoundError(f"BERT checkpoint not found: {bert_ckpt_path}")

        if not root_cause_dataset_path:
            raise ValueError("root_cause_dataset_path must be provided.")
        if not os.path.exists(root_cause_dataset_path):
            raise FileNotFoundError(
                f"Root-cause dataset not found: {root_cause_dataset_path}"
            )

        if tracker_window_size < 1:
            raise ValueError("tracker_window_size must be a positive integer.")

        # 1. Emotion inference model (two-head BERT) — loaded ONCE
        self._bert = TwoHeadBertInference(bert_ckpt_path).load()

        # 2. Root-cause classifier — prefer loading a serialized model to avoid
        #    retraining on every startup.
        can_load = (
            root_cause_model_dir is not None
            and all(
                os.path.exists(os.path.join(root_cause_model_dir, f))
                for f in self._SERIALIZED_FILES
            )
        )

        if can_load:
            self._root_classifier = RootCauseClassifier.load(root_cause_model_dir)
        else:
            df = pd.read_csv(root_cause_dataset_path)
            self._root_classifier = RootCauseClassifier(model_type=root_cause_model_type)
            self._root_classifier.fit(df, text_col="statement")
            if root_cause_model_dir is not None:
                os.makedirs(root_cause_model_dir, exist_ok=True)
                self._root_classifier.save(root_cause_model_dir)

        # 3. Sliding-window tracker (stateful across calls)
        self._tracker = SlidingWindowTracker(window_size=tracker_window_size)

    def run_full_inference(self, text: str) -> Dict[str, Any]:
        """Run the complete inference pipeline on a single user text.

        The method executes the following stages in order:
        1. Text preprocessing
        2. Emotional prediction (depression + anxiety)
        3. Root-cause prediction
        4. Risk scoring
        5. Planner generation
        6. Suggestion generation
        7. Tracker entry creation

        Args:
            text: Raw user input text.

        Returns:
            A structured dictionary with the following keys:

            * ``emotion`` – ``{"depression_score": float, "anxiety_score": float}``
            * ``root_causes`` – ``{"probabilities": dict, "top_root_cause": str}``
            * ``risk`` – ``{"score": float, "level": str}``
            * ``planner`` – ``{"type": str, "plan": dict}``
            * ``suggestions`` – ``List[str]``
            * ``tracker`` – ``{"text": str, "depression_score": float,
              "anxiety_score": float, "risk_score": float,
              "top_root_cause": str}``

        Raises:
            ValueError: If ``text`` is ``None`` or empty after preprocessing.
        """
        if text is None:
            raise ValueError("Input text cannot be None.")

        preprocessed = preprocess_text(text)
        if not preprocessed:
            raise ValueError("Input text is empty after preprocessing.")

        # --- 1. Emotional inference ---
        mental = self._bert.predict(preprocessed)

        # --- 2. Root-cause inference ---
        root_pred = self._root_classifier.predict_proba(preprocessed)
        root_probs = root_pred.probabilities
        top_root = (
            max(root_probs.items(), key=lambda kv: kv[1])[0]
            if root_probs
            else "none"
        )

        # --- 3. Risk scoring ---
        risk = calculate_risk_score(
            depression_score=mental.depression_score,
            anxiety_score=mental.anxiety_score,
            root_cause_probs=root_probs,
        )

        # --- 4. Planner generation ---
        planner_type, plan = generate_planner(
            mental.depression_score,
            mental.anxiety_score,
            root_probs,
        )

        # --- 5. Suggestions ---
        suggestions: List[str] = get_suggestions(top_root)

        # --- 6. Tracker entry ---
        entry = TrackerEntry(
            text=text,
            depression_score=mental.depression_score,
            anxiety_score=mental.anxiety_score,
            risk_score=risk.score,
            top_root_cause=top_root,
        )
        self._tracker.add(entry)

        return {
            "emotion": asdict(mental),
            "root_causes": {
                "probabilities": root_probs,
                "top_root_cause": top_root,
            },
            "risk": asdict(risk),
            "planner": {
                "type": planner_type,
                "plan": plan,
            },
            "suggestions": suggestions,
            "tracker": asdict(entry),
        }
