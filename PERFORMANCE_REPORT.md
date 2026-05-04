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
| Hash | SHA-256 |
| Target position | line 949,283 (~95% of the list) |

## 3. Results

| Workers | Sequential time | Parallel time | Speedup |
|---:|---:|---:|---:|
| 1 (sequential) | 0.97 s | — | 1.00x |
| 2 | — | 0.73 s | 1.34x |
| 4 | — | 0.52 s | 1.86x |
| 8 | — | 0.40 s | **2.47x** |

## 4. Discussion

### Why parallel is faster
SHA-256 hashing is **CPU-bound** (Parallel-1 slide 3). With more processes,
more cores actually compute hashes in parallel. We use `multiprocessing`
because Python threads share the GIL — only multiprocessing gives true
parallelism on CPU work.

### Why we use a shared `Value` flag + Poison Pill
Without early termination, every worker would finish its full chunk even
after one of them already found the password. We use:

- A shared `Value('b', False)` (Communication slide 9) as a "found" flag.
- Each worker checks the flag every 1,000 hashes and exits if it's set —
  this is the **Poison Pill** termination idiom (Adv-Patterns slide 5).
- A `Queue` (Communication slide 10) carries the matched word back to
  the main process — no shared variables, no locks for the result.

### Amdahl's Law
$$S(N) = \frac{1}{(1-P) + P/N}$$

Our measured speedup at N=8 is 2.47x, below the ideal 8x. The non-parallel
fraction includes:
- Reading the wordlist from disk (sequential, shared by all modes)
- Process spawn cost on Windows (`spawn` not `fork`, ~150 ms)
- Putting/getting through the result `Queue`

Fitting the data, the parallelizable fraction is roughly **P ≈ 0.70**.

### When does adding workers stop helping?
Going 4 → 8 added 24% speedup; going beyond 8 on a 16-logical-core machine
will plateau quickly because the 8 *physical* cores are already saturated
and hyperthreading gives little extra throughput on tight integer/hash loops.

## 5. Screenshots

> Take these from the GUI for the submission:
> - "Run Both & Compare" filled-in results table.
> - "Show Chart" matplotlib comparison.

## 6. Conclusion

- Parallel beats Sequential by **~2.5x** on 8 workers for a 1 M wordlist.
- Patterns reused directly from the lectures: `multiprocessing`, `Value`,
  `Queue`, Poison Pill, chunking.
- The remaining gap from ideal speedup is explained by Amdahl's Law:
  disk I/O and process-spawn overhead are not parallelizable.
