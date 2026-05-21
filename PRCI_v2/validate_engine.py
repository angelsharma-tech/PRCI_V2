"""Validation script: compare legacy orchestration vs InferenceEngine output.

Run with the project venv:
    py -3.12 validate_engine.py
"""

import os
import sys

_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)

from upgrade_pipeline.preprocess import preprocess_text, TwoHeadBertInference
from upgrade_pipeline.root_cause_model import RootCauseClassifier
from upgrade_pipeline.risk_engine import calculate_risk_score
from upgrade_pipeline.planner import generate_planner
from upgrade_pipeline.web_agent import get_suggestions
from upgrade_pipeline.tracker import SlidingWindowTracker, TrackerEntry
from upgrade_pipeline.core.inference_engine import InferenceEngine

import pandas as pd


BERT_CKPT = os.path.join(
    _project_root, "legacy_model_pipeline", "outputs", "twohead", "best.pt"
)
ROOT_CAUSE_DATASET = os.path.join(
    _project_root, "phase_3_data", "raw", "root_cause", "procrastination_dataset.csv"
)

TEST_INPUTS = [
    "I feel nervous about tomorrow and deadlines make me anxious. My mind keeps racing.",
    "Nothing excites me anymore. I feel empty and tired all the time, and life feels meaningless lately.",
    "I keep delaying my assignment even after planning. I end up scrolling on my phone instead of starting.",
]


def legacy_orchestrate(text: str, ckpt_path: str, dataset_path: str):
    """Reproduce the exact legacy backend block from app_upgrade.py."""
    bert = TwoHeadBertInference(ckpt_path).load()
    mental = bert.predict(text)

    df = pd.read_csv(dataset_path)
    root_model = RootCauseClassifier(model_type="ovr_logreg")
    root_model.fit(df, text_col="statement")
    root_pred = root_model.predict_proba(text)
    root_probs = root_pred.probabilities

    top_root = max(root_probs.items(), key=lambda kv: kv[1])[0] if root_probs else "none"

    risk = calculate_risk_score(
        depression_score=mental.depression_score,
        anxiety_score=mental.anxiety_score,
        root_cause_probs=root_probs,
    )

    tracker = SlidingWindowTracker(window_size=7)
    tracker.add(
        TrackerEntry(
            text=text,
            depression_score=mental.depression_score,
            anxiety_score=mental.anxiety_score,
            risk_score=risk.score,
            top_root_cause=top_root,
        )
    )

    planner_type, plan = generate_planner(
        mental.depression_score,
        mental.anxiety_score,
        root_probs,
    )

    suggestions = get_suggestions(top_root)

    return {
        "emotion": {
            "depression_score": mental.depression_score,
            "anxiety_score": mental.anxiety_score,
        },
        "root_causes": {
            "probabilities": root_probs,
            "top_root_cause": top_root,
        },
        "risk": {
            "score": risk.score,
            "level": risk.level,
        },
        "planner": {
            "type": planner_type,
            "plan": plan,
        },
        "suggestions": suggestions,
        "tracker": {
            "text": text,
            "depression_score": mental.depression_score,
            "anxiety_score": mental.anxiety_score,
            "risk_score": risk.score,
            "top_root_cause": top_root,
        },
    }


def compare_dicts(a: dict, b: dict, path="") -> list:
    diffs = []
    keys = set(a.keys()) | set(b.keys())
    for k in sorted(keys):
        ap = f"{path}.{k}" if path else k
        if k not in a:
            diffs.append(f"[MISSING in legacy] {ap}")
            continue
        if k not in b:
            diffs.append(f"[MISSING in engine] {ap}")
            continue
        av, bv = a[k], b[k]
        if isinstance(av, dict) and isinstance(bv, dict):
            diffs.extend(compare_dicts(av, bv, ap))
        elif isinstance(av, float) and isinstance(bv, float):
            if abs(av - bv) > 1e-6:
                diffs.append(f"[FLOAT MISMATCH] {ap}: legacy={av}, engine={bv}")
        elif av != bv:
            diffs.append(f"[MISMATCH] {ap}: legacy={av!r}, engine={bv!r}")
    return diffs


def main():
    print("=" * 60)
    print("VALIDATION: Legacy orchestration vs InferenceEngine")
    print("=" * 60)

    print("\n[1/3] Loading InferenceEngine (this may take a moment)...")
    engine = InferenceEngine(
        bert_ckpt_path=BERT_CKPT,
        root_cause_dataset_path=ROOT_CAUSE_DATASET,
        root_cause_model_type="ovr_logreg",
        root_cause_model_dir=os.path.join(
            os.path.dirname(ROOT_CAUSE_DATASET), "serialized_root_model"
        ),
    )
    print("   InferenceEngine loaded.")

    all_pass = True
    for i, text in enumerate(TEST_INPUTS, start=1):
        print(f"\n[2/3] Test case {i}/{len(TEST_INPUTS)}")
        print(f"      Input: {text[:60]}...")

        legacy = legacy_orchestrate(text, BERT_CKPT, ROOT_CAUSE_DATASET)
        engine_out = engine.run_full_inference(text)

        diffs = compare_dicts(legacy, engine_out)
        if diffs:
            all_pass = False
            print(f"   ❌ DIFFERENCES FOUND ({len(diffs)}):")
            for d in diffs:
                print(f"      - {d}")
        else:
            print("   ✅ Outputs match exactly.")

    print("\n" + "=" * 60)
    if all_pass:
        print("🎉 ALL TESTS PASSED — orchestration migration is correct.")
    else:
        print("⚠️  SOME DIFFERENCES FOUND — review above.")
    print("=" * 60)

    # Check tracker state
    print(f"\n[3/3] Tracker state: {len(engine._tracker.entries())} entries")
    print("      (Expected: 3, one per test input)")


if __name__ == "__main__":
    main()
