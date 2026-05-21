from dataclasses import dataclass
from typing import Dict, List


@dataclass
class TrackerEntry:
    text: str
    depression_score: float
    anxiety_score: float
    risk_score: float
    top_root_cause: str


class SlidingWindowTracker:
    def __init__(self, window_size: int = 7):
        self.window_size = int(window_size)
        self._entries: List[TrackerEntry] = []

    def add(self, entry: TrackerEntry) -> None:
        self._entries.append(entry)
        if len(self._entries) > self.window_size:
            self._entries = self._entries[-self.window_size :]

    def entries(self) -> List[TrackerEntry]:
        return list(self._entries)

    def trend_risk(self) -> float:
        if not self._entries:
            return 0.0
        return sum(e.risk_score for e in self._entries) / len(self._entries)

    def trend_root_cause(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for e in self._entries:
            k = e.top_root_cause or "none"
            counts[k] = counts.get(k, 0) + 1
        return counts
