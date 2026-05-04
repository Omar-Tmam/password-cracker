# Performance Report — Sequential vs Parallel

## 1. System

| Item | Value |
|---|---|
| OS | Windows 10 Pro |
| CPU | Intel64 (16 logical cores) |
| Python | 3.13 |

## 2. Test setup

| Item | Value |
|---|---|
| Wordlist | 1,000,000 words (random + 20 common passwords) |
| Hash | SHA-256 (only algorithm supported) |
| Target position | line 949,283 (~95% of the list) |
| Sub-chunk size (parallel) | 2,000 words |

## 3. Results

| Workers | Sequential time | Parallel time | Speedup |
|---:|---:|---:|---:|
| 1 (sequential) | 0.97 s | — | 1.00x |
| 2 | — | 0.71 s | 1.37x |
| 4 | — | 0.48 s | 2.02x |
| 8 | — | 0.36 s | **2.69x** |

## 4. Design

### Sequential
Single process, single core. Reads the wordlist into memory, then iterates
word-by-word, hashing with SHA-256 and comparing to the target. Stops on
first match.

### Parallel
`multiprocessing.Pool` with `imap_unordered`:

- **Persistent pool** — `n` worker processes are spawned once and reused
  for every sub-chunk. Avoids the per-task spawn cost of one-shot
  `Process(target=...)`.
- **Static sub-chunking** — the wordlist is split into 2,000-word
  sub-chunks streamed lazily into the pool. Small enough to keep progress
  smooth and to enable fast early-exit; large enough that IPC overhead
  per item stays negligible.
- **Streaming results** — `imap_unordered` yields each completed
  sub-chunk's `(count, hit_or_None, last_word)` tuple as soon as it's
  ready. The main process accumulates the running total and forwards it
  to the GUI's progress callback.
- **Early termination** — when a worker reports `hit is not None`, the
  main process calls `pool.terminate()` to kill the remaining workers
  mid-flight. No shared `Value` flag, no manual poison-pill check needed.

## 5. Discussion

### Why parallel wins
SHA-256 hashing is **CPU-bound**. Python threads share the GIL, so true
parallelism on CPU work requires multiple processes. With `n` workers,
roughly `n` cores compute hashes simultaneously.

### Why the speedup is sub-linear (Amdahl's Law)

$$S(N) = \frac{1}{(1-P) + P/N}$$

Measured 2.69x at N=8 vs. ideal 8x. Non-parallel costs:

- Reading the wordlist from disk (paid once, not parallelized)
- Pool spawn cost on Windows (`spawn`, not `fork` — ~150 ms per worker
  on first task)
- `imap_unordered` IPC: pickling each sub-chunk and unpickling the
  result over the pool's pipe

Fitting the data, the parallelizable fraction is roughly **P ≈ 0.74**.

### Why not more processes?
On a 16-logical / 8-physical machine, going past 8 plateaus quickly:
hyperthreading helps little on tight integer loops like SHA-256, and
pickling overhead grows with worker count.

### Match position bias
The target is planted in the second half of the list so neither mode
"wins by luck." Sequential walks in order and would short-circuit early
if it were near the front. Parallel splits the list into many sub-chunks,
so the match latency depends on which sub-chunk lands on which worker
and when.

## 6. Conclusion

- Parallel beats Sequential by **~2.7x** on 8 workers for a 1 M wordlist.
- Switching from `Process(target=worker)` per chunk to a persistent
  `Pool` cut overhead enough that parallel wins even on smaller
  (~100 k word) lists where the per-process spawn cost previously
  dominated.
- The remaining gap from ideal speedup is explained by Amdahl's Law:
  disk I/O, pool startup, and IPC are not parallelizable.
