"""
Shared helpers: result type, timer, wordlist loader.
"""
import time
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CrackResult:
    mode: str
    found: bool
    password: Optional[str]
    words_checked: int
    time_taken: float
    workers: int = 1
    log: List[str] = field(default_factory=list)

    @property
    def words_per_second(self) -> float:
        return self.words_checked / self.time_taken if self.time_taken > 0 else 0.0


class Timer:
    """Context-manager wall-clock timer."""
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *_):
        self.end = time.time()
        self.elapsed = self.end - self.start


def load_wordlist(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return [line.rstrip("\n\r") for line in f if line.strip()]
