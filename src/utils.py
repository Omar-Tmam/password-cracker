"""
Shared helpers: result type, timer, wordlist loader, data generation.
"""
import hashlib
import os
import random
import string
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


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




def generate_test_data(size: int) -> Tuple[str, str, str, List[str]]:
    """
    Generate a test wordlist and target hash.
    Returns (wordlist_path, target_hash, target_plaintext, log_lines)
    """
    log = [f"[Generate] creating {size:,} words..."]
    chars = string.ascii_lowercase + string.digits

    words = [
        "".join(random.choices(chars, k=random.randint(4, 12)))
        for _ in range(size)
    ]
    random.shuffle(words)

    target_idx = random.randint(size // 2, size - 1)
    target_password = words[target_idx]

    here = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(here), "data")
    os.makedirs(data_dir, exist_ok=True)
    wordlist_path = os.path.join(data_dir, "wordlist.txt")
    target_path = os.path.join(data_dir, "sample_target_hash.txt")

    with open(wordlist_path, "w", encoding="utf-8") as f:
        f.write("\n".join(words))

    digest = hashlib.sha256(target_password.encode("utf-8")).hexdigest()
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(f"sha256:{digest}:{target_password}\n")

    log.append(f"[Generate] wrote {wordlist_path}")
    log.append(f"[Generate] target plaintext: {target_password!r} (line ~{target_idx + 1:,})")
    log.append(f"[Generate] sha256: {digest}")

    return wordlist_path, digest, target_password, log

