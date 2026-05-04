"""
Timing + chunking helpers shared by all cracker variants.
"""
import time
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class CrackResult:
    """Unified result type for every cracker mode."""
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
    """Context-manager timer (Parallel-1 lec 4 style: time.time() before/after)."""
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *_):
        self.end = time.time()
        self.elapsed = self.end - self.start


def load_wordlist(path: str) -> List[str]:
    """Read whole wordlist into memory (one word per line)."""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return [line.rstrip("\n\r") for line in f if line.strip()]


def chunkify(items: List[str], n_chunks: int) -> List[List[str]]:
    """
    Split `items` into `n_chunks` contiguous chunks.
    EN: Static partitioning — same idea as Pool.map's static chunking
        (Adv-Patterns lec 13: "Pool.map() = Static chunking").
    AR: تقسيم ثابت للقائمة على عدد العمال.
    """
    if n_chunks <= 0:
        n_chunks = 1
    size = max(1, len(items) // n_chunks)
    chunks = [items[i:i + size] for i in range(0, len(items), size)]
    # Merge any tail overflow into the last chunk so we end up with exactly n_chunks (or fewer if items < n_chunks).
    while len(chunks) > n_chunks:
        chunks[-2].extend(chunks[-1])
        chunks.pop()
    return chunks
