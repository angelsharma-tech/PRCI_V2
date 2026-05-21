import re
import importlib.util
import os
import sys
from dataclasses import dataclass
from typing import Optional

import pandas as pd


_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_WS_RE = re.compile(r"\s+")


def preprocess_text(text: str) -> str:
    if text is None:
        return ""
    s = str(text)
    s = s.lower()
    s = _URL_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    return s


def preprocess_dataframe(df: pd.DataFrame, text_col: str) -> pd.DataFrame:
    if text_col not in df.columns:
        raise ValueError(f"Missing text column: {text_col}")

    out = df.copy()
    out = out.dropna(subset=[text_col])
    out[text_col] = out[text_col].map(preprocess_text)
    out = out[out[text_col].str.len() > 0]
    out = out.drop_duplicates(subset=[text_col])
    return out.reset_index(drop=True)


@dataclass
class MentalStateScores:
    depression_score: float
    anxiety_score: float


class TwoHeadBertInference:
    """Reusable inference wrapper around the legacy two-head BERT pipeline.

    This wrapper does not retrain. It loads a checkpoint produced by
    legacy_model_pipeline/train_two_heads.py (best.pt/last.pt).

    Expected output:
        {"depression_score": float, "anxiety_score": float}
    """

    def __init__(self, ckpt_path: str):
        self.ckpt_path = ckpt_path
        self._infer = None

    def _maybe_download_ckpt(self) -> None:
        if not self.ckpt_path:
            return

        if os.path.exists(self.ckpt_path):
            return

        drive_id = os.getenv("PRCI_TWOHEAD_DRIVE_ID", "").strip()
        if not drive_id:
            raise FileNotFoundError(
                f"Checkpoint not found at '{self.ckpt_path}'. Set PRCI_TWOHEAD_DRIVE_ID to auto-download, or provide a valid path."
            )

        try:
            import gdown
        except Exception as e:
            raise ImportError(
                "gdown is required for auto-download. Install it (pip install gdown) or provide a valid local checkpoint path."
            ) from e

        os.makedirs(os.path.dirname(os.path.abspath(self.ckpt_path)) or ".", exist_ok=True)
        url = f"https://drive.google.com/uc?id={drive_id}"
        gdown.download(url, self.ckpt_path, quiet=False)

        if not os.path.exists(self.ckpt_path):
            raise FileNotFoundError(
                f"Auto-download finished but checkpoint still missing at '{self.ckpt_path}'. Verify PRCI_TWOHEAD_DRIVE_ID and Drive sharing permissions."
            )

    def _load_legacy_modules(self):
        legacy_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "legacy_model_pipeline")
        train_path = os.path.join(legacy_dir, "train_two_heads.py")
        infer_path = os.path.join(legacy_dir, "model_infer.py")

        if not os.path.exists(train_path):
            raise FileNotFoundError(f"Missing legacy training module: {train_path}")
        if not os.path.exists(infer_path):
            raise FileNotFoundError(f"Missing legacy inference module: {infer_path}")

        if "train_two_heads" not in sys.modules:
            spec_train = importlib.util.spec_from_file_location("train_two_heads", train_path)
            mod_train = importlib.util.module_from_spec(spec_train)
            sys.modules["train_two_heads"] = mod_train
            if spec_train is None or spec_train.loader is None:
                raise ImportError("Failed to load train_two_heads module spec")
            spec_train.loader.exec_module(mod_train)

        if "model_infer" not in sys.modules:
            spec_infer = importlib.util.spec_from_file_location("model_infer", infer_path)
            mod_infer = importlib.util.module_from_spec(spec_infer)
            sys.modules["model_infer"] = mod_infer
            if spec_infer is None or spec_infer.loader is None:
                raise ImportError("Failed to load model_infer module spec")
            spec_infer.loader.exec_module(mod_infer)

    def load(self) -> "TwoHeadBertInference":
        if os.path.exists(self.ckpt_path):
            print("Loading model from local path...")
        else:
            print("Downloading model from Google Drive...")
            self._maybe_download_ckpt()
        
        self._load_legacy_modules()
        TwoHeadInfer = sys.modules["model_infer"].TwoHeadInfer
        self._infer = TwoHeadInfer(self.ckpt_path)
        return self

    def predict(self, text: str) -> MentalStateScores:
        if self._infer is None:
            self.load()

        out = self._infer.predict(text)
        dep = float(out.get("dep_prob", 0.0))
        anx = float(out.get("anx_prob", 0.0))
        return MentalStateScores(depression_score=dep, anxiety_score=anx)
