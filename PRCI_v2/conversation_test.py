"""CLI behavioral tester for ConversationEngine.

Run in two modes:

1. Automated scenario tests (default):
    $ python conversation_test.py

2. Interactive chat loop:
    $ python conversation_test.py --interactive

The script loads the InferenceEngine once, then exercises the
ConversationEngine through predefined stress-test scenarios.
"""

import argparse
import os
import sys
from typing import Any, Dict, List

_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)

from upgrade_pipeline.core.inference_engine import InferenceEngine
from upgrade_pipeline.conversation import ConversationEngine


BERT_CKPT = os.path.join(
    _project_root, "legacy_model_pipeline", "outputs", "twohead", "best.pt"
)
ROOT_CAUSE_DATASET = os.path.join(
    _project_root, "phase_3_data", "raw", "root_cause", "procrastination_dataset.csv"
)


def _separator(label: str = "") -> None:
    print("=" * 70)
    if label:
        print(f"  {label}")
        print("=" * 70)


def _show_turn(user: str, reply: Dict[str, Any]) -> None:
    print(f"\n👤 USER: {user}")
    print(f"🤖 RESPONSE: {reply['response']}")
    print(f"❓ FOLLOW-UP: {reply['follow_up']}")
    print(f"📊 EMOTION: dep={reply['emotion_context']['depression_score']:.3f}  "
          f"anx={reply['emotion_context']['anxiety_score']:.3f}  "
          f"risk={reply['emotion_context']['risk_level']}  "
          f"root={reply['emotion_context']['top_root_cause']}")
    print(f"📏 HISTORY: {reply['history_length']} messages")


def case_1_mild_stress(engine: InferenceEngine) -> None:
    _separator("CASE 1 — Mild Stress")
    chat = ConversationEngine(engine, max_history=10)
    text = "I feel tired because of work lately."
    reply = chat.generate_response(text)
    _show_turn(text, reply)
    print("\n✅ CHECK: Tone should be supportive, not alarmist. "
          "Follow-up should invite more sharing.")


def case_2_escalation(engine: InferenceEngine) -> None:
    _separator("CASE 2 — Escalating Emotional State")
    chat = ConversationEngine(engine, max_history=10)
    messages = [
        "I'm a bit stressed about my exams.",
        "It's getting worse, I can't sleep well.",
        "I feel completely overwhelmed and hopeless.",
    ]
    for msg in messages:
        reply = chat.generate_response(msg)
        _show_turn(msg, reply)
    print("\n✅ CHECK: Watch for 'worsening' continuity markers in responses. "
          "Risk level should progress LOW → MODERATE → HIGH.")


def case_3_repetition(engine: InferenceEngine) -> None:
    _separator("CASE 3 — Repetition Stress Test (6 similar messages)")
    chat = ConversationEngine(engine, max_history=10)
    text = "I keep procrastinating on my assignments."
    responses: List[str] = []
    follow_ups: List[str] = []
    for i in range(6):
        reply = chat.generate_response(text)
        responses.append(reply["response"])
        follow_ups.append(reply["follow_up"])

    for i, (r, f) in enumerate(zip(responses, follow_ups), start=1):
        print(f"\n--- Turn {i} ---")
        print(f"Response: {r[:120]}...")
        print(f"Follow-up: {f}")

    unique_responses = len(set(responses))
    unique_follow_ups = len(set(follow_ups))
    print(f"\n✅ CHECK: Unique responses = {unique_responses}/6, "
          f"unique follow-ups = {unique_follow_ups}/6")
    print("   If both are < 3, repetition avoidance is broken.")


def case_4_high_risk(engine: InferenceEngine) -> None:
    _separator("CASE 4 — High-Risk Wording")
    chat = ConversationEngine(engine, max_history=10)
    text = "I feel hopeless and like nothing matters anymore."
    reply = chat.generate_response(text)
    _show_turn(text, reply)
    print("\n✅ CHECK: Opening should NOT be generic-cheerful. "
          "Should contain 'glad you reached out' or similar. "
          "No toxic positivity.")


def case_5_history_cap(engine: InferenceEngine) -> None:
    _separator("CASE 5 — History FIFO Cap (max_history=4)")
    chat = ConversationEngine(engine, max_history=4)
    for i in range(1, 8):
        reply = chat.generate_response(f"Test message number {i}")
        print(f"Turn {i}: history_length = {reply['history_length']}")

    print(f"\n✅ CHECK: history_length should never exceed 4. "
          f"Final history length = {reply['history_length']}")

    # Also verify that history is actually FIFO-trimmed
    history = chat.get_conversation_history()
    contents = [h["content"] for h in history]
    assert "Test message number 1" not in contents, "FIFO trim failed — oldest user msg still present"
    assert "Test message number 2" not in contents, "FIFO trim failed — second-oldest user msg still present"
    print("   ✅ FIFO trimming confirmed: oldest messages rotated out.")


def interactive_mode(engine: InferenceEngine) -> None:
    _separator("INTERACTIVE MODE — type 'quit' to exit, 'clear' to reset memory")
    chat = ConversationEngine(engine, max_history=10)
    while True:
        try:
            text = input("\n👤 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nExiting...")
            break

        if text.lower() in ("quit", "exit", "q"):
            break
        if text.lower() == "clear":
            chat.clear_history()
            print("🧹 History cleared.")
            continue
        if not text:
            continue

        reply = chat.generate_response(text)
        _show_turn(text, reply)


def main() -> None:
    parser = argparse.ArgumentParser(description="ConversationEngine behavioral tester")
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run interactive chat loop instead of automated scenarios",
    )
    args = parser.parse_args()

    print("Loading InferenceEngine (one-time, may take ~30s)...")
    engine = InferenceEngine(
        bert_ckpt_path=BERT_CKPT,
        root_cause_dataset_path=ROOT_CAUSE_DATASET,
        root_cause_model_type="ovr_logreg",
        root_cause_model_dir=os.path.join(
            os.path.dirname(ROOT_CAUSE_DATASET), "serialized_root_model"
        ),
    )
    print("Engine ready.\n")

    if args.interactive:
        interactive_mode(engine)
    else:
        case_1_mild_stress(engine)
        case_2_escalation(engine)
        case_3_repetition(engine)
        case_4_high_risk(engine)
        case_5_history_cap(engine)
        _separator("ALL SCENARIOS COMPLETE")


if __name__ == "__main__":
    main()
