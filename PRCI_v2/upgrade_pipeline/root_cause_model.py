import os
import pickle
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier

from .preprocess import preprocess_dataframe


LABEL_COLS = [
    "perfectionism",
    "fear_of_failure",
    "lack_of_interest",
    "environment_distraction",
    "dopamine_addiction",
]


@dataclass
class RootCausePrediction:
    probabilities: Dict[str, float]


class RootCauseClassifier:
    """Trainable root-cause classifier for the upgrade pipeline.

    Default model: TF-IDF + OneVsRest(LogisticRegression)
    Optional: TF-IDF + OneVsRest(XGBoost) when enabled and installed.
    """

    def __init__(
        self,
        max_features: int = 3000,
        ngram_range: Tuple[int, int] = (1, 2),
        model_type: str = "ovr_logreg",
        random_state: int = 42,
    ):
        self.max_features = max_features
        self.ngram_range = ngram_range
        self.model_type = model_type
        self.random_state = random_state

        self.vectorizer: Optional[TfidfVectorizer] = None
        self.model = None
        self.labels: List[str] = list(LABEL_COLS)
        self.is_fitted = False

    def _build(self):
        self.vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            ngram_range=self.ngram_range,
        )

        if self.model_type == "xgboost":
            try:
                from xgboost import XGBClassifier
            except Exception as e:
                raise ImportError(
                    "XGBoost requested but not installed. Install xgboost or use model_type='ovr_logreg'."
                ) from e

            base = XGBClassifier(
                n_estimators=300,
                max_depth=4,
                learning_rate=0.08,
                subsample=0.9,
                colsample_bytree=0.9,
                reg_lambda=1.0,
                random_state=self.random_state,
                n_jobs=1,
                eval_metric="logloss",
            )
            self.model = OneVsRestClassifier(base)
            return

        base = LogisticRegression(
            class_weight="balanced",
            solver="liblinear",
            random_state=self.random_state,
            max_iter=2000,
        )
        self.model = OneVsRestClassifier(base)

    def fit(self, df: pd.DataFrame, text_col: str = "statement") -> "RootCauseClassifier":
        if self.vectorizer is None or self.model is None:
            self._build()

        df = preprocess_dataframe(df, text_col=text_col)

        missing = [c for c in [text_col, *self.labels] if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        X_text = df[text_col].astype(str).values
        Y = df[self.labels].astype(int).values

        X = self.vectorizer.fit_transform(X_text)
        self.model.fit(X, Y)
        self.is_fitted = True
        return self

    def predict_proba(self, text: str) -> RootCausePrediction:
        if not self.is_fitted:
            raise ValueError("RootCauseClassifier must be fitted before prediction")

        X = self.vectorizer.transform([str(text)])
        P = self.model.predict_proba(X)

        if isinstance(P, list):
            P = np.column_stack(P)

        n = min(len(self.labels), P.shape[1])
        probs = {self.labels[i]: float(P[0, i]) for i in range(n)}
        return RootCausePrediction(probabilities=probs)

    def save(self, out_dir: str) -> Dict[str, str]:
        if not self.is_fitted:
            raise ValueError("RootCauseClassifier must be fitted before saving")

        os.makedirs(out_dir, exist_ok=True)
        vec_path = os.path.join(out_dir, "upgrade_root_tfidf.pkl")
        model_path = os.path.join(out_dir, "upgrade_root_model.pkl")
        labels_path = os.path.join(out_dir, "upgrade_root_labels.pkl")

        with open(vec_path, "wb") as f:
            pickle.dump(self.vectorizer, f)
        with open(model_path, "wb") as f:
            pickle.dump(self.model, f)
        with open(labels_path, "wb") as f:
            pickle.dump(self.labels, f)

        return {
            "vectorizer": vec_path,
            "model": model_path,
            "labels": labels_path,
        }

    @classmethod
    def load(cls, out_dir: str) -> "RootCauseClassifier":
        vec_path = os.path.join(out_dir, "upgrade_root_tfidf.pkl")
        model_path = os.path.join(out_dir, "upgrade_root_model.pkl")
        labels_path = os.path.join(out_dir, "upgrade_root_labels.pkl")

        with open(vec_path, "rb") as f:
            vectorizer = pickle.load(f)
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        with open(labels_path, "rb") as f:
            labels = pickle.load(f)

        inst = cls()
        inst.vectorizer = vectorizer
        inst.model = model
        inst.labels = list(labels)
        inst.is_fitted = True
        return inst
