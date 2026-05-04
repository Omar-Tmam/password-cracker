# Password Hash Cracker — Sequential vs Parallel

Dictionary-attack cracker comparing sequential and parallel SHA-256 password cracking. Built with `multiprocessing.Pool` and features a CustomTkinter GUI for live progress tracking.

## Features

- **Sequential mode** — single-process baseline for comparison
- **Parallel mode** — `multiprocessing.Pool` with `imap_unordered` for per-chunk streaming results
- **Live progress UI** — watch both modes run side-by-side; see current word, progress %, and throughput in real-time
- **In-app test data generation** — no CLI setup needed; generate wordlist and target hash from the GUI
- **Embedded charts** — time and words/second comparison; zoom out UI to see everything without scrolling
- **Early termination** — parallel mode stops all workers immediately upon finding a match

## Setup

```bash
pip install -r requirements.txt
```

Requires: `customtkinter` (GUI), `matplotlib` (charts).

## Run

Launch the GUI:
```bash
python src/gui.py
```

1. Click **Generate Wordlist + Target** and set a size (default 100,000).
2. Click **Run Both & Compare** to run sequential and parallel side-by-side.
3. Watch the live progress bars, current words, and final comparison chart.

Or use CLI:
```bash
python -m src.sequential_cracker data/wordlist.txt <target_hash>
python -m src.parallel_cracker   data/wordlist.txt <target_hash> [num_workers]
python tests/generate_test_data.py [size]
```

## Design

### Sequential
Single process, single core. Iterates the wordlist, hashing each word and comparing to the target. Stops on first match.

### Parallel
Uses `multiprocessing.Pool`:
- **Persistent pool** — workers spawned once and reused (avoids per-task spawn cost on Windows)
- **Sub-chunking** — wordlist split into 2,000-word chunks streamed to the pool
- **Streaming results** — `imap_unordered` yields results as soon as ready, enabling live progress callbacks
- **Early termination** — `pool.terminate()` immediately stops all workers when a match is found

### GUI
- **CustomTkinter** dark theme with card-based layout
- **Live Processing panel** — determinate progress bar, word count, current word for both modes
- **Results table** — status, password found, time, words checked, words/second, speedup
- **Comparison charts** — time taken and throughput (words/sec), side-by-side
- **Log** — real-time output from both crackers
- **Generate button** — in-app wordlist + target creation (replaces CLI step)

## Project Layout

```
password_cracker/
├── src/
│   ├── hasher.py             SHA-256 hashing
│   ├── utils.py              Timer, CrackResult, generate_test_data
│   ├── sequential_cracker.py single-process baseline
│   ├── parallel_cracker.py   Pool + imap_unordered
│   └── gui.py                CustomTkinter UI
├── tests/
│   └── generate_test_data.py CLI wrapper for utils.generate_test_data
├── data/
│   ├── small_wordlist.txt   fallback wordlist
│   ├── wordlist.txt         generated (gitignored)
│   └── sample_target_hash.txt generated (gitignored)
├── requirements.txt
├── README.md
├── PERFORMANCE_REPORT.md
└── .gitignore
```

## Performance

On a 16-logical / 8-physical core machine with 1M word list:

| Mode | Time | Speedup |
|---|---|---|
| Sequential | 0.97s | 1.00x |
| Parallel (2 workers) | 0.71s | 1.37x |
| Parallel (4 workers) | 0.48s | 2.02x |
| Parallel (8 workers) | 0.36s | **2.69x** |

See `PERFORMANCE_REPORT.md` for analysis and Amdahl's Law discussion.

## Algorithm

SHA-256 only (no algorithm parameter). Both crackers hash words with the same function for fair comparison.

## Notes

- **Windows spawn cost** — multiprocessing on Windows uses "spawn" (not "fork"), which has ~150ms overhead per worker. Pool reuse amortizes this cost.
- **Match position** — test data plants the password in the second half of the list so neither mode has an advantage.
- **Scaling** — speedup plateaus around 8 workers; beyond that, hyperthreading and IPC overhead dominate.
