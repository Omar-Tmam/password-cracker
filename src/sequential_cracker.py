"""
Sequential Cracker — baseline.

EN: Reads wordlist, hashes each word one-by-one, compares with target.
    Lecture reference: Parallel Programming (1), slide 4 (Sequential Version).
    Pattern: simple for-loop, single CPU core.
AR: نسخة سيريال (متسلسلة) — أبسط نسخة، عامل واحد فقط.
"""
from __future__ import annotations

from .hasher import hash_word, normalize_hash
from .utils import CrackResult, Timer, load_wordlist


def crack_sequential(wordlist_path: str,
                     target_hash: str,
                     algorithm: str = "sha256") -> CrackResult:
    target = normalize_hash(target_hash)
    words = load_wordlist(wordlist_path)
    log = [f"[Sequential] loaded {len(words):,} words from {wordlist_path}"]

    found_password = None
    checked = 0

    with Timer() as t:
        for word in words:
            checked += 1
            if hash_word(word, algorithm) == target:
                found_password = word
                log.append(f"[Sequential] MATCH at word #{checked}: {word!r}")
                break

    if found_password is None:
        log.append("[Sequential] password not in wordlist")

    return CrackResult(
        mode="Sequential",
        found=found_password is not None,
        password=found_password,
        words_checked=checked,
        time_taken=t.elapsed,
        workers=1,
        log=log,
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("usage: python -m src.sequential_cracker <wordlist> <target_hash> [algo]")
        sys.exit(1)
    algo = sys.argv[3] if len(sys.argv) > 3 else "sha256"
    r = crack_sequential(sys.argv[1], sys.argv[2], algo)
    print(f"Found: {r.found}  Password: {r.password}")
    print(f"Time: {r.time_taken:.3f}s   Words: {r.words_checked:,}   Rate: {r.words_per_second:,.0f}/s")
