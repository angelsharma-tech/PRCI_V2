from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class RiskResult:
    score: float
    level: str


def calculate_risk_score(
    depression_score: float,
    anxiety_score: float,
    root_cause_probs: Dict[str, float],
    w_dep: float = 0.4,
    w_anx: float = 0.3,
    w_root: float = 0.3,
) -> RiskResult:
    dep = float(depression_score)
    anx = float(anxiety_score)
    root_max = max([float(v) for v in root_cause_probs.values()], default=0.0)

    score = w_dep * dep + w_anx * anx + w_root * root_max
    score = max(0.0, min(1.0, score))

    if score < 0.33:
        level = "LOW"
    elif score < 0.66:
        level = "MODERATE"
    else:
        level = "HIGH"

    return RiskResult(score=score, level=level)
