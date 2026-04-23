import json
import os
import pickle
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    f1_score,
    hamming_loss,
    precision_score,
    recall_score,
)
from sklearn.model_selection import KFold
from sklearn.multiclass import OneVsRestClassifier


SEED = 42
TRAIN_PATH = "phase_3_data/splits/root_cause/train.csv"
VAL_PATH = "phase_3_data/splits/root_cause/val.csv"

VECTORIZER_KWARGS = {
    "max_features": 3000,
    "ngram_range": (1, 2),
}

BASE_ESTIMATOR_KWARGS = {
    "class_weight": "balanced",
    "solver": "liblinear",
    "random_state": SEED,
}

LABEL_COLS = [
    "perfectionism",
    "fear_of_failure",
    "lack_of_interest",
    "environment_distraction",
    "dopamine_addiction",
]


@dataclass
class CvMetrics:
    micro_f1: float
    macro_f1: float
    hamming_loss: float
    precision_micro: float
    recall_micro: float


def _load_splits() -> pd.DataFrame:
    if not os.path.exists(TRAIN_PATH):
        raise FileNotFoundError(TRAIN_PATH)
    if not os.path.exists(VAL_PATH):
        raise FileNotFoundError(VAL_PATH)

    train_df = pd.read_csv(TRAIN_PATH)
    val_df = pd.read_csv(VAL_PATH)
    df = pd.concat([train_df, val_df], axis=0, ignore_index=True)

    required = ["text", *LABEL_COLS]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df.dropna(subset=["text"]).copy()
    df["text"] = df["text"].astype(str)

    dup_count = int(df.duplicated(subset=["text"]).sum())
    if dup_count:
        df = df.drop_duplicates(subset=["text"]).copy()

    for c in LABEL_COLS:
        vals = set(df[c].unique())
        if not vals.issubset({0, 1}):
            raise ValueError(f"Non-binary values in '{c}': {sorted(list(vals))}")

    return df.reset_index(drop=True)


def _build_model() -> Tuple[TfidfVectorizer, OneVsRestClassifier]:
    vectorizer = TfidfVectorizer(**VECTORIZER_KWARGS)
    base = LogisticRegression(**BASE_ESTIMATOR_KWARGS)
    clf = OneVsRestClassifier(base)
    return vectorizer, clf


def _cross_validate(df: pd.DataFrame) -> CvMetrics:
    texts = df["text"].values
    Y = df[LABEL_COLS].values

    kf = KFold(n_splits=5, shuffle=True, random_state=SEED)

    micro_f1s: List[float] = []
    macro_f1s: List[float] = []
    hls: List[float] = []
    precs: List[float] = []
    recs: List[float] = []

    for train_idx, test_idx in kf.split(texts):
        vectorizer, clf = _build_model()

        X_train = vectorizer.fit_transform(texts[train_idx])
        X_test = vectorizer.transform(texts[test_idx])

        y_train = Y[train_idx]
        y_test = Y[test_idx]

        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)

        micro_f1s.append(float(f1_score(y_test, y_pred, average="micro", zero_division=0)))
        macro_f1s.append(float(f1_score(y_test, y_pred, average="macro", zero_division=0)))
        hls.append(float(hamming_loss(y_test, y_pred)))
        precs.append(float(precision_score(y_test, y_pred, average="micro", zero_division=0)))
        recs.append(float(recall_score(y_test, y_pred, average="micro", zero_division=0)))

    return CvMetrics(
        micro_f1=float(np.mean(micro_f1s)),
        macro_f1=float(np.mean(macro_f1s)),
        hamming_loss=float(np.mean(hls)),
        precision_micro=float(np.mean(precs)),
        recall_micro=float(np.mean(recs)),
    )


def _train_final(df: pd.DataFrame) -> Tuple[TfidfVectorizer, OneVsRestClassifier]:
    vectorizer, clf = _build_model()
    X = vectorizer.fit_transform(df["text"].values)
    Y = df[LABEL_COLS].values
    clf.fit(X, Y)
    return vectorizer, clf


def _save_artifacts(vectorizer: TfidfVectorizer, clf: OneVsRestClassifier) -> Dict[str, str]:
    out_dir = os.path.join("phase_4_models")
    os.makedirs(out_dir, exist_ok=True)

    tfidf_path = os.path.join(out_dir, "root_tfidf.pkl")
    model_path = os.path.join(out_dir, "root_ovr_logreg.pkl")
    labels_path = os.path.join(out_dir, "root_labels.json")

    with open(tfidf_path, "wb") as f:
        pickle.dump(vectorizer, f)

    with open(model_path, "wb") as f:
        pickle.dump(clf, f)

    with open(labels_path, "w", encoding="utf-8") as f:
        json.dump(LABEL_COLS, f, indent=2)

    return {
        "root_tfidf.pkl": tfidf_path,
        "root_ovr_logreg.pkl": model_path,
        "root_labels.json": labels_path,
    }


def main() -> None:
    df = _load_splits()

    print("Root cause training pipeline")
    print(f"Seed: {SEED}")
    print(f"Samples used (train+val, de-duplicated): {len(df)}")
    print("Labels:")
    for c in LABEL_COLS:
        print(f"- {c}")

    cv = _cross_validate(df)

    print("\n5-Fold Cross-Validation (averaged)")
    print(f"Micro F1:      {cv.micro_f1:.4f}")
    print(f"Macro F1:      {cv.macro_f1:.4f}")
    print(f"Hamming Loss:  {cv.hamming_loss:.4f}")
    print(f"Precision:     {cv.precision_micro:.4f}")
    print(f"Recall:        {cv.recall_micro:.4f}")

    vectorizer, clf = _train_final(df)
    paths = _save_artifacts(vectorizer, clf)

    print("\nSaved artifacts:")
    for k, v in paths.items():
        print(f"- {k}: {v}")

    print(f"\nCompleted at: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
