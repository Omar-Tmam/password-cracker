"""
Parallel Cracker — multiprocessing.Pool with imap_unordered.

EN: Splits the wordlist into many small sub-chunks and feeds them to a
    persistent Pool. Workers are reused across sub-chunks (no respawn cost),
    results stream back as they complete, and we abort by terminating the
    pool the moment any worker reports a match.

Patterns:
  - Pool + imap_unordered = streaming static chunking with worker reuse
  - Early-exit via pool.terminate() (no shared flag needed)
"""
from __future__ import annotations

from multiprocessing import Pool, cpu_count
from typing import List, Optional, Tuple

from .hasher import hash_word, normalize_hash
from .utils import CrackResult, Timer, load_wordlist


# Words per sub-chunk. Smaller = faster early-exit + smoother progress;
# larger = lower IPC overhead per item.
SUBCHUNK_SIZE = 2000


def _hash_subchunk(args: Tuple[List[str], str, str]) -> Tuple[int, Optional[str], Optional[str]]:
    """Hash one sub-chunk. Returns (count_processed, found_word_or_None, last_word)."""
    words, target, algorithm = args
    last = None
    for i, w in enumerate(words):
        if hash_word(w, algorithm) == target:
            return (i + 1, w, w)
        last = w
    return (len(words), None, last)


def _iter_subchunks(words: List[str], target: str, algorithm: str):
    for start in range(0, len(words), SUBCHUNK_SIZE):
        yield (words[start:start + SUBCHUNK_SIZE], target, algorithm)


def crack_parallel(wordlist_path: str,
                   target_hash: str,
                   algorithm: str = "sha256",
                   num_workers: Optional[int] = None,
                   progress_callback=None) -> CrackResult:
    target = normalize_hash(target_hash)
    words = load_wordlist(wordlist_path)
    total = len(words)
    n = num_workers or cpu_count()
    log = [f"[Parallel] {total:,} words -> Pool({n}), subchunk={SUBCHUNK_SIZE}"]

    found_password: Optional[str] = None
    checked = 0

    with Timer() as t:
        pool = Pool(processes=n)
        try:
            tasks = _iter_subchunks(words, target, algorithm)
            for processed, hit, last in pool.imap_unordered(_hash_subchunk, tasks):
                checked += processed
                if progress_callback:
                    progress_callback(checked, total, hit or last)
                if hit is not None:
                    found_password = hit
                    pool.terminate()
                    break
            else:
                pool.close()
            pool.join()
        finally:
            try:
                pool.close()
            except Exception:
                pass

    if found_password:
        log.append(f"[Parallel] MATCH: {found_password!r}")
    else:
        log.append("[Parallel] password not in wordlist")

    return CrackResult(
        mode="Parallel",
        found=found_password is not None,
        password=found_password,
        words_checked=checked,
        time_taken=t.elapsed,
        workers=n,
        log=log,
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("usage: python -m src.parallel_cracker <wordlist> <target_hash> [algo] [n_workers]")
        sys.exit(1)
    algo = sys.argv[3] if len(sys.argv) > 3 else "sha256"
    n = int(sys.argv[4]) if len(sys.argv) > 4 else None
    r = crack_parallel(sys.argv[1], sys.argv[2], algo, n)
    print(f"Found: {r.found}  Password: {r.password}")
    print(f"Time: {r.time_taken:.3f}s   Words: {r.words_checked:,}   Workers: {r.workers}   Rate: {r.words_per_second:,.0f}/s")
