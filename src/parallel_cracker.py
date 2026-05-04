"""
Parallel Cracker.

EN: Splits the wordlist into chunks (one per worker) and runs them in parallel
    using multiprocessing. Stops as soon as ANY worker finds the password.

Lecture patterns used (only what's needed for sequential-vs-parallel):
  - Parallel-1 slide 5 : multiprocessing.Pool with cpu_count()
  - Communication slide 9 : shared Value('b', False) + Lock as the "found" flag
  - Communication slide 10: Queue for sending the result back to main
  - Adv-Patterns slide 5 : Poison Pill (None) to terminate workers cleanly
AR: تقسيم القائمة على عمال متوازيين مع إيقاف الكل لما واحد يلاقي الباسورد.
"""
from __future__ import annotations

from multiprocessing import Process, Queue, Value, cpu_count
from typing import List, Optional

from .hasher import hash_word, normalize_hash
from .utils import CrackResult, Timer, load_wordlist, chunkify


# How often each worker checks the shared "found" flag.
# Smaller = faster early-exit; larger = less synchronization overhead.
CHECK_EVERY = 1000


def _worker(chunk: List[str],
            target: str,
            algorithm: str,
            found_flag,        # multiprocessing.Value('b', False)
            words_counter,     # multiprocessing.Value('i', 0)
            result_q: Queue):
    """One process. Hashes its chunk; aborts when found_flag is set."""
    local_count = 0
    try:
        for i, word in enumerate(chunk):
            # Periodic check on the shared flag = poison-pill trigger.
            if i % CHECK_EVERY == 0 and found_flag.value:
                return
            local_count += 1
            if hash_word(word, algorithm) == target:
                with found_flag.get_lock():
                    found_flag.value = True
                result_q.put(word)        # send result back via Queue (Communication lec 10)
                return
    finally:
        # Add this worker's local count to the shared total.
        # Communication slide 9 pattern: Value + its built-in lock.
        with words_counter.get_lock():
            words_counter.value += local_count


def crack_parallel(wordlist_path: str,
                   target_hash: str,
                   algorithm: str = "sha256",
                   num_workers: Optional[int] = None) -> CrackResult:
    target = normalize_hash(target_hash)
    words = load_wordlist(wordlist_path)
    n = num_workers or cpu_count()
    chunks = chunkify(words, n)
    n = len(chunks)
    log = [f"[Parallel] {len(words):,} words -> {n} workers"]

    # Shared state (Communication lec 9): Value flag + Queue for result.
    found_flag = Value("b", False)
    words_counter = Value("i", 0)        # shared int: total words actually hashed
    result_q: Queue = Queue()

    processes = []
    with Timer() as t:
        for chunk in chunks:
            p = Process(target=_worker,
                        args=(chunk, target, algorithm,
                              found_flag, words_counter, result_q))
            p.start()
            processes.append(p)
        for p in processes:
            p.join()

    found_password: Optional[str] = None
    while not result_q.empty():
        found_password = result_q.get()

    # Real number of words workers actually hashed (less than total if Poison
    # Pill triggered early termination).
    checked = words_counter.value
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
