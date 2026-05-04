"""
Sequential Cracker — single-process baseline.
"""
from __future__ import annotations

from .hasher import hash_word, normalize_hash
from .utils import CrackResult, Timer, load_wordlist


def crack_sequential(wordlist_path: str,
                     target_hash: str,
                     progress_callback=None) -> CrackResult:
    target = normalize_hash(target_hash)
    words = load_wordlist(wordlist_path)
    total = len(words)
    log = [f"[Sequential] loaded {total:,} words from {wordlist_path}"]

    found_password = None
    checked = 0
    REPORT_EVERY = max(50, total // 500)

    with Timer() as t:
        for word in words:
            checked += 1
            if hash_word(word) == target:
                found_password = word
                log.append(f"[Sequential] MATCH at word #{checked}: {word!r}")
                if progress_callback:
                    progress_callback(checked, total, word)
                break
            if progress_callback and checked % REPORT_EVERY == 0:
                progress_callback(checked, total, word)

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
        print("usage: python -m src.sequential_cracker <wordlist> <target_hash>")
        sys.exit(1)
    r = crack_sequential(sys.argv[1], sys.argv[2])
    print(f"Found: {r.found}  Password: {r.password}")
    print(f"Time: {r.time_taken:.3f}s   Words: {r.words_checked:,}   Rate: {r.words_per_second:,.0f}/s")
