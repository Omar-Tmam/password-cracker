"""
Modern CustomTkinter GUI: Sequential vs Parallel comparison.
"""
from __future__ import annotations

import os
import sys
import threading
import hashlib
import random
import string
from typing import Dict
from tkinter import filedialog, messagebox

import customtkinter as ctk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sequential_cracker import crack_sequential
from src.parallel_cracker import crack_parallel
from src.utils import CrackResult


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ACCENT = "#3b82f6"
ACCENT_HOVER = "#2563eb"
SEQ_COLOR = "#94a3b8"
PAR_COLOR = "#10b981"
BG_CARD = "#1e293b"
BG_DARK = "#0f172a"
TEXT_DIM = "#cbd5e1"


class CrackerGUI:
    def __init__(self, root: ctk.CTk):
        self.root = root
        root.title("Password Hash Cracker — Sequential vs Parallel")
        root.geometry("1100x720")
        root.minsize(980, 660)
        self.results: Dict[str, CrackResult] = {}
        self._build_ui()

    def _build_ui(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(4, weight=1)

        # Header
        header = ctk.CTkFrame(self.root, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(14, 6))
        ctk.CTkLabel(
            header, text="Password Hash Cracker",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            header, text="Sequential vs Parallel benchmark",
            font=ctk.CTkFont(size=13), text_color=TEXT_DIM,
        ).pack(side="left", padx=(12, 0), pady=(6, 0))

        # Input card
        inp = ctk.CTkFrame(self.root, corner_radius=12)
        inp.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=6)
        for c in range(6):
            inp.grid_columnconfigure(c, weight=(1 if c in (1, 4) else 0))

        ctk.CTkLabel(inp, text="Target hash").grid(row=0, column=0, sticky="w", padx=12, pady=(12, 4))
        self.hash_var = ctk.StringVar()
        ctk.CTkEntry(inp, textvariable=self.hash_var, placeholder_text="hex digest...").grid(
            row=0, column=1, columnspan=5, sticky="ew", padx=12, pady=(12, 4))

        ctk.CTkLabel(inp, text="Wordlist").grid(row=1, column=0, sticky="w", padx=12, pady=4)
        self.wordlist_var = ctk.StringVar()
        ctk.CTkEntry(inp, textvariable=self.wordlist_var, placeholder_text="path/to/wordlist.txt").grid(
            row=1, column=1, columnspan=3, sticky="ew", padx=12, pady=4)
        ctk.CTkButton(inp, text="Browse", width=90, command=self.browse,
                      fg_color=ACCENT, hover_color=ACCENT_HOVER).grid(row=1, column=4, padx=4, pady=4)
        ctk.CTkButton(inp, text="Load Sample", width=110, command=self.load_sample,
                      fg_color=ACCENT, hover_color=ACCENT_HOVER).grid(row=1, column=5, padx=(4, 12), pady=4)

        ctk.CTkLabel(inp, text="Algorithm").grid(row=2, column=0, sticky="w", padx=12, pady=(4, 12))
        ctk.CTkLabel(inp, text="SHA-256", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=ACCENT).grid(row=2, column=1, sticky="w", padx=12, pady=(4, 12))

        ctk.CTkLabel(inp, text="Workers").grid(row=2, column=2, sticky="e", padx=12, pady=(4, 12))
        self.workers_var = ctk.IntVar(value=4)
        self.workers_label = ctk.CTkLabel(inp, text="4", width=30)
        worker_slider = ctk.CTkSlider(inp, from_=1, to=16, number_of_steps=15,
                                      variable=self.workers_var,
                                      command=lambda v: self.workers_label.configure(text=f"{int(float(v))}"))
        worker_slider.grid(row=2, column=3, sticky="ew", padx=12, pady=(4, 12))
        self.workers_label.grid(row=2, column=4, sticky="w", padx=4, pady=(4, 12))

        # Generate panel
        gen = ctk.CTkFrame(self.root, corner_radius=12)
        gen.grid(row=2, column=0, columnspan=2, sticky="ew", padx=16, pady=6)
        ctk.CTkLabel(gen, text="Generate test data",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(14, 8), pady=10)
        ctk.CTkLabel(gen, text="Words:").pack(side="left", padx=(8, 4), pady=10)
        self.gen_size_var = ctk.StringVar(value="100000")
        ctk.CTkEntry(gen, textvariable=self.gen_size_var, width=100).pack(side="left", padx=4, pady=10)
        ctk.CTkButton(gen, text="Generate Wordlist + Target", width=210,
                      command=self.generate_data,
                      fg_color="#9333ea", hover_color="#7e22ce").pack(side="left", padx=10, pady=10)
        ctk.CTkButton(gen, text="Pop-out Chart", width=130,
                      command=self.show_chart,
                      fg_color="transparent", border_width=1, border_color=ACCENT,
                      text_color=ACCENT, hover_color="#1e293b").pack(side="right", padx=10, pady=10)

        # Control bar
        ctl = ctk.CTkFrame(self.root, corner_radius=12)
        ctl.grid(row=3, column=0, columnspan=2, sticky="ew", padx=16, pady=6)
        ctk.CTkButton(ctl, text="Run Sequential", width=150,
                      command=lambda: self._run("Sequential"),
                      fg_color="#475569", hover_color="#334155").pack(side="left", padx=10, pady=10)
        ctk.CTkButton(ctl, text="Run Parallel", width=150,
                      command=lambda: self._run("Parallel"),
                      fg_color="#0d9488", hover_color="#0f766e").pack(side="left", padx=4, pady=10)
        ctk.CTkButton(ctl, text="Run Both & Compare", width=180,
                      command=self._run_both,
                      fg_color=ACCENT, hover_color=ACCENT_HOVER).pack(side="left", padx=10, pady=10)

        # --- Left column: results + progress + log ---
        left = ctk.CTkFrame(self.root, fg_color="transparent")
        left.grid(row=4, column=0, sticky="nsew", padx=(16, 8), pady=6)
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(2, weight=1)

        # Results card
        res = ctk.CTkFrame(left, corner_radius=12)
        res.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ctk.CTkLabel(res, text="Results", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=14, pady=(10, 4))

        headers = ["Metric", "Sequential", "Parallel"]
        for c, h in enumerate(headers):
            ctk.CTkLabel(res, text=h, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=TEXT_DIM).grid(row=1, column=c, padx=12, pady=(2, 6),
                                                    sticky="w" if c == 0 else "")
        res.grid_columnconfigure(0, weight=1)
        res.grid_columnconfigure(1, weight=1)
        res.grid_columnconfigure(2, weight=1)

        self._cells: Dict[str, Dict[str, ctk.CTkLabel]] = {"seq": {}, "par": {}}
        rows = ("Status", "Password Found", "Time Taken", "Words Checked",
                "Words/Second", "Speedup")
        for i, label in enumerate(rows, start=2):
            ctk.CTkLabel(res, text=label, text_color=TEXT_DIM).grid(
                row=i, column=0, sticky="w", padx=14, pady=2)
            for c, key in enumerate(("seq", "par"), start=1):
                lbl = ctk.CTkLabel(res, text="—", font=ctk.CTkFont(size=12, weight="bold"))
                lbl.grid(row=i, column=c, padx=12, pady=2)
                self._cells[key][label] = lbl
        ctk.CTkLabel(res, text="").grid(row=len(rows) + 2, column=0, pady=4)

        # Progress card
        prog = ctk.CTkFrame(left, corner_radius=12)
        prog.grid(row=1, column=0, sticky="ew", pady=8)
        prog.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(prog, text="Progress", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(10, 4))
        self.bars = {}
        for i, mode in enumerate(("Sequential", "Parallel"), start=1):
            ctk.CTkLabel(prog, text=mode, width=90).grid(row=i, column=0, sticky="w", padx=14, pady=6)
            pb = ctk.CTkProgressBar(prog, mode="indeterminate",
                                    progress_color=SEQ_COLOR if mode == "Sequential" else PAR_COLOR)
            pb.set(0)
            pb.grid(row=i, column=1, sticky="ew", padx=14, pady=6)
            self.bars[mode] = pb
        ctk.CTkLabel(prog, text="").grid(row=3, column=0, pady=4)

        # Log card
        logf = ctk.CTkFrame(left, corner_radius=12)
        logf.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        logf.grid_columnconfigure(0, weight=1)
        logf.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(logf, text="Log", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=14, pady=(10, 4))
        self.log = ctk.CTkTextbox(logf, wrap="word", font=ctk.CTkFont(size=11), height=140)
        self.log.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        # --- Right column: charts ---
        right = ctk.CTkFrame(self.root, corner_radius=12)
        right.grid(row=4, column=1, sticky="nsew", padx=(8, 16), pady=6)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)
        right.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(right, text="Live Comparison", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=14, pady=(10, 4))

        self._embed_charts(right)

    # ---------------------------------------------------------- charts
    def _embed_charts(self, parent):
        # Compact embedded charts (small width).
        self.fig_time = Figure(figsize=(4.2, 2.2), dpi=100, facecolor=BG_CARD)
        self.ax_time = self.fig_time.add_subplot(111)
        self._style_axes(self.ax_time, "Time Taken (s)")
        self.canvas_time = FigureCanvasTkAgg(self.fig_time, master=parent)
        self.canvas_time.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=10, pady=4)

        self.fig_wps = Figure(figsize=(4.2, 2.2), dpi=100, facecolor=BG_CARD)
        self.ax_wps = self.fig_wps.add_subplot(111)
        self._style_axes(self.ax_wps, "Words / Second")
        self.canvas_wps = FigureCanvasTkAgg(self.fig_wps, master=parent)
        self.canvas_wps.get_tk_widget().grid(row=2, column=0, sticky="nsew", padx=10, pady=(4, 10))

        self._refresh_charts()

    def _style_axes(self, ax, title):
        ax.set_facecolor(BG_DARK)
        ax.set_title(title, color="white", fontsize=10, pad=8)
        ax.tick_params(colors=TEXT_DIM, labelsize=9)
        for spine in ax.spines.values():
            spine.set_color("#334155")
        ax.grid(True, axis="y", alpha=0.15, color=TEXT_DIM)

    def _refresh_charts(self):
        modes = ["Sequential", "Parallel"]
        colors = [SEQ_COLOR, PAR_COLOR]

        times = [self.results[m].time_taken if m in self.results else 0 for m in modes]
        self.ax_time.clear(); self._style_axes(self.ax_time, "Time Taken (s) — lower is better")
        bars = self.ax_time.bar(modes, times, color=colors, width=0.5,
                                edgecolor="white", linewidth=0.5)
        for b, t in zip(bars, times):
            if t > 0:
                self.ax_time.text(b.get_x() + b.get_width() / 2, b.get_height(),
                                  f"{t:.2f}s", ha="center", va="bottom",
                                  color="white", fontsize=9, fontweight="bold")
        self.fig_time.tight_layout()
        self.canvas_time.draw_idle()

        wps = [self.results[m].words_per_second if m in self.results else 0 for m in modes]
        self.ax_wps.clear(); self._style_axes(self.ax_wps, "Throughput (words/s) — higher is better")
        bars = self.ax_wps.bar(modes, wps, color=colors, width=0.5,
                               edgecolor="white", linewidth=0.5)
        for b, w in zip(bars, wps):
            if w > 0:
                self.ax_wps.text(b.get_x() + b.get_width() / 2, b.get_height(),
                                 f"{w:,.0f}", ha="center", va="bottom",
                                 color="white", fontsize=9, fontweight="bold")
        self.fig_wps.tight_layout()
        self.canvas_wps.draw_idle()

    # ------------------------------------------------------------- helpers
    def browse(self):
        p = filedialog.askopenfilename(filetypes=[("Text", "*.txt"), ("All", "*.*")])
        if p:
            self.wordlist_var.set(p)

    def generate_data(self):
        try:
            size = int(self.gen_size_var.get())
            if size < 20:
                raise ValueError("size must be >= 20")
        except ValueError as e:
            messagebox.showerror("Invalid size", f"Enter a positive integer (>=20). {e}")
            return
        threading.Thread(target=self._generate_thread, args=(size,), daemon=True).start()

    def _generate_thread(self, size: int):
        common = ["password", "123456", "qwerty", "letmein", "admin", "welcome",
                  "monkey", "dragon", "iloveyou", "trustno1", "master", "shadow",
                  "football", "baseball", "superman", "batman", "starwars",
                  "abc123", "password1", "passw0rd"]
        chars = string.ascii_lowercase + string.digits

        self._log(f"[Generate] creating {size:,} words...")
        words = list(common) + [
            "".join(random.choices(chars, k=random.randint(4, 12)))
            for _ in range(max(0, size - len(common)))
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

        self.root.after(0, lambda: (
            self.wordlist_var.set(wordlist_path),
            self.hash_var.set(digest),
        ))
        self._log(f"[Generate] wrote {wordlist_path}")
        self._log(f"[Generate] target plaintext: {target_password!r} (line ~{target_idx + 1:,})")
        self._log(f"[Generate] sha256: {digest}")

    def load_sample(self):
        here = os.path.dirname(os.path.abspath(__file__))
        target = os.path.join(os.path.dirname(here), "data", "sample_target_hash.txt")
        if not os.path.exists(target):
            messagebox.showwarning("Missing", "Run tests/generate_test_data.py first.")
            return
        with open(target) as f:
            _, digest, plaintext = f.readline().strip().split(":", 2)
        self.hash_var.set(digest)
        wl = os.path.join(os.path.dirname(here), "data", "wordlist.txt")
        if not os.path.exists(wl):
            wl = os.path.join(os.path.dirname(here), "data", "small_wordlist.txt")
        self.wordlist_var.set(wl)
        self._log(f"Loaded sample. Plaintext (verification): {plaintext}")

    def show_chart(self):
        if "Sequential" not in self.results or "Parallel" not in self.results:
            messagebox.showinfo("No data", "Run both modes first."); return
        win = ctk.CTkToplevel(self.root)
        win.title("Comparison Chart")
        win.geometry("640x420")
        fig = Figure(figsize=(5.5, 3.4), dpi=100, facecolor=BG_CARD)
        ax = fig.add_subplot(111)
        self._style_axes(ax, "Sequential vs Parallel — Time (s)")
        modes = ["Sequential", "Parallel"]
        times = [self.results[m].time_taken for m in modes]
        bars = ax.bar(modes, times, color=[SEQ_COLOR, PAR_COLOR], width=0.5,
                      edgecolor="white", linewidth=0.5)
        for b, t in zip(bars, times):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{t:.2f}s",
                    ha="center", va="bottom", color="white", fontweight="bold")
        fig.tight_layout()
        FigureCanvasTkAgg(fig, master=win).get_tk_widget().pack(fill="both", expand=True,
                                                                 padx=12, pady=12)

    # ----------------------------------------------------------------- run
    def _validate(self) -> bool:
        if not self.hash_var.get().strip():
            messagebox.showerror("Missing", "Enter target hash"); return False
        if not os.path.exists(self.wordlist_var.get()):
            messagebox.showerror("Missing", "Pick a valid wordlist file"); return False
        return True

    def _run(self, mode: str):
        if not self._validate():
            return
        threading.Thread(target=self._worker_thread, args=(mode,), daemon=True).start()

    def _run_both(self):
        if not self._validate():
            return
        threading.Thread(target=self._both_thread, daemon=True).start()

    def _both_thread(self):
        self._worker_thread("Sequential")
        self._worker_thread("Parallel")

    def _worker_thread(self, mode: str):
        self._set_cell(mode, "Status", "running...")
        self._bar(mode, start=True)
        self._log(f"[{mode}] starting...")
        wl = self.wordlist_var.get()
        target = self.hash_var.get().strip()
        algo = "sha256"
        try:
            if mode == "Sequential":
                res = crack_sequential(wl, target, algo)
            else:
                res = crack_parallel(wl, target, algo, self.workers_var.get())
        except Exception as e:
            self._log(f"[{mode}] ERROR: {e}")
            self._set_cell(mode, "Status", "error")
            self._bar(mode, start=False)
            return
        self._bar(mode, start=False)
        self.results[mode] = res
        for line in res.log:
            self._log(line)
        self._update(mode, res)
        self.root.after(0, self._refresh_charts)

    # --------------------------------------------------------------- UI ops
    def _col(self, mode):
        return "seq" if mode == "Sequential" else "par"

    def _set_cell(self, mode: str, row: str, value: str):
        col = self._col(mode)
        self.root.after(0, lambda: self._cells[col][row].configure(text=value))

    def _update(self, mode: str, res: CrackResult):
        col = self._col(mode)
        cells = {
            "Status": "FOUND" if res.found else "not found",
            "Password Found": res.password or "—",
            "Time Taken": f"{res.time_taken:.3f}s",
            "Words Checked": f"{res.words_checked:,}",
            "Words/Second": f"{res.words_per_second:,.0f}",
        }
        if "Sequential" in self.results and mode == "Parallel" and res.time_taken > 0:
            speedup = self.results["Sequential"].time_taken / res.time_taken
            cells["Speedup"] = f"{speedup:.2f}x"
        elif mode == "Sequential":
            cells["Speedup"] = "1.00x (baseline)"
        for row, val in cells.items():
            color = "white"
            if row == "Status":
                color = PAR_COLOR if val == "FOUND" else "#f87171" if val == "error" else TEXT_DIM
            self.root.after(0, lambda r=row, v=val, c=color:
                            self._cells[col][r].configure(text=v, text_color=c))

    def _bar(self, mode: str, start: bool):
        if start:
            self.root.after(0, lambda: (self.bars[mode].configure(mode="indeterminate"),
                                        self.bars[mode].start()))
        else:
            def stop():
                self.bars[mode].stop()
                self.bars[mode].configure(mode="determinate")
                self.bars[mode].set(1.0)
            self.root.after(0, stop)

    def _log(self, msg: str):
        def append():
            self.log.insert("end", msg + "\n")
            self.log.see("end")
        self.root.after(0, append)


def main():
    root = ctk.CTk()
    CrackerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
