# Password Hash Cracker — Sequential vs Parallel

Dictionary-attack password cracker that compares **Sequential** and
**Parallel** execution. Built using only the patterns taught in the four
parallel-programming lectures.

## Lecture patterns used

| Pattern | From which lecture | Where in the code |
|---|---|---|
| Sequential for-loop baseline | Parallel-1 slide 4 | `sequential_cracker.py` |
| `multiprocessing` + `cpu_count()` | Parallel-1 slide 5 | `parallel_cracker.py` |
| Chunking the work | Parallel-1 slide 5 | `utils.chunkify` |
| Shared `Value('b', False)` flag | Communication slide 9 | `parallel_cracker.py` |
| `Queue` for sending result back | Communication slide 10 | `parallel_cracker.py` |
| **Poison Pill** (early termination) | Adv-Patterns slide 5 | `parallel_cracker.py` |
| `time.time()` start/end timing | Parallel-1 slide 4 | `utils.Timer` |

## Setup

```bash
pip install -r requirements.txt
```

Only `matplotlib` is needed; everything else is the standard library.

## Run

1. Generate the test data:
   ```bash
   python tests/generate_test_data.py 1000000 sha256
   ```
2. Launch the GUI:
   ```bash
   python -m src.gui
   ```
   Click **Load sample** → **Run Both & Compare**.

Or from CLI:
```bash
python -m src.sequential_cracker data/wordlist.txt <hash> sha256
python -m src.parallel_cracker   data/wordlist.txt <hash> sha256 8
```

## Layout

```
password_cracker/
├── src/
│   ├── hasher.py             shared hashing
│   ├── utils.py              Timer, chunkify, CrackResult
│   ├── sequential_cracker.py
│   ├── parallel_cracker.py   Pool/Process + Value + Queue + Poison Pill
│   └── gui.py
├── tests/generate_test_data.py
├── data/                     small_wordlist.txt + generated wordlist + target
├── requirements.txt
├── README.md
└── PERFORMANCE_REPORT.md
```
