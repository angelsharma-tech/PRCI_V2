from typing import Dict, List, Optional, Tuple

import numpy as np


def explain_root_causes_top_words(
    vectorizer,
    model,
    labels: List[str],
    text: str,
    top_k: int = 8,
) -> Dict[str, List[Tuple[str, float]]]:
    """SHAP-based explanations for root-cause predictions.

    If SHAP is unavailable, falls back to coefficient-based explanations for
    linear models (LogisticRegression) and returns an empty dict otherwise.
    """

    try:
        import shap

        X = vectorizer.transform([text])
        feature_names = vectorizer.get_feature_names_out()

        explanations: Dict[str, List[Tuple[str, float]]] = {}

        if hasattr(model, "estimators_") and len(getattr(model, "estimators_", [])) == len(labels):
            for i, lbl in enumerate(labels):
                est = model.estimators_[i]
                explainer = shap.LinearExplainer(est, X, feature_perturbation="interventional")
                sv = explainer.shap_values(X)
                sv = sv[0] if isinstance(sv, (list, tuple)) else sv
                sv = np.asarray(sv).reshape(-1)
                idx = np.argsort(np.abs(sv))[::-1][:top_k]
                explanations[lbl] = [(str(feature_names[j]), float(sv[j])) for j in idx]
            return explanations

    except Exception:
        pass

    explanations: Dict[str, List[Tuple[str, float]]] = {}
    if hasattr(model, "estimators_") and hasattr(vectorizer, "get_feature_names_out"):
        feature_names = vectorizer.get_feature_names_out()
        X = vectorizer.transform([text])
        x_row = X.toarray().reshape(-1)

        for i, lbl in enumerate(labels):
            est = model.estimators_[i]
            if hasattr(est, "coef_"):
                coef = est.coef_.reshape(-1)
                contrib = coef * x_row
                idx = np.argsort(np.abs(contrib))[::-1][:top_k]
                explanations[lbl] = [(str(feature_names[j]), float(contrib[j])) for j in idx]

    return explanations
