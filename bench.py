#!/usr/bin/env python3
"""Бенчмарк решателя: сборка, прогон всех инстансов параллельно, проверка валидатором,
компактная таблица и обновление results/best.csv.

    python3 bench.py [секунды=60] [--py] [--only 0,3] [--no-update]

--py      гонять solver/solve.py вместо C++
--only    список инстансов
Валидатору нужны pydantic и shapely: если их нет в системе, берётся .venv/bin/python
(создать: python3 -m venv .venv && .venv/bin/pip install pydantic shapely numpy).
"""
import argparse
import csv
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TASK = ROOT / "task"
BEST = ROOT / "results" / "best.csv"


def py_with(mods):
    for py in (str(ROOT / ".venv/bin/python"), sys.executable):
        if Path(py).exists() and subprocess.run([py, "-c", "import " + ",".join(mods)],
                                                capture_output=True).returncode == 0:
            return py
    sys.exit(f"нет модулей {mods}: python3 -m venv .venv && .venv/bin/pip install pydantic shapely numpy")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("seconds", nargs="?", type=float, default=60)
    ap.add_argument("--py", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--no-update", action="store_true")
    a = ap.parse_args()

    insts = sorted(int(p.name[8:]) for p in TASK.glob("instance*") if p.is_dir())
    if a.only:
        insts = [int(x) for x in a.only.split(",")]
    tmp = Path(tempfile.mkdtemp(prefix="bench_"))
    if a.py:
        cmd = [py_with(["numpy"]), str(ROOT / "solver/solve.py")]
    else:
        cxx = os.environ.get("CXX") or shutil.which("g++") or shutil.which("clang++")
        if not cxx:
            sys.exit("нет C++ компилятора: sudo apt install g++  (или --py)")
        exe = tmp / "solve"
        subprocess.run([cxx, "-O2", "-std=c++17", "-o", str(exe), str(ROOT / "solver/solve.cpp")], check=True)
        cmd = [str(exe)]
    vpy = py_with(["pydantic", "shapely"])

    def run(k):
        inst = TASK / f"instance{k}/instance.json"
        out = tmp / f"sol{k}.json"
        r = subprocess.run(cmd + [str(inst), str(out), str(a.seconds)], capture_output=True, text=True)
        v = subprocess.run([vpy, "-I", str(TASK / "validate_solution.py"), str(inst), str(out)],
                           capture_output=True, text=True).stdout.split()
        ok = bool(v) and v[0] != "FAIL"
        return k, (float(v[-1]) if ok else None), (v[-1] if v else r.stderr.strip()[-80:]), out

    with ThreadPoolExecutor(len(insts)) as ex:
        res = list(ex.map(run, insts))

    best = {}
    if BEST.exists():
        best = {int(r["instance"]): float(r["objective"]) for r in csv.DictReader(BEST.open())}
    print(f"{'inst':>4} {'objective':>16} {'best':>16} {'delta':>9}")
    improved = False
    for k, f, msg, out in res:
        b = best.get(k)
        if f is None:
            print(f"{k:>4} {'INVALID: ' + msg:>16}")
            continue
        d = "" if b is None else f"{(f - b) / max(abs(b), 1e-9) * 100:+.2f}%"
        print(f"{k:>4} {f:>16.3f} {b if b is not None else '-':>16} {d:>9}")
        if b is None or f > b + 1e-9:
            best[k] = f
            improved = True
            if not a.no_update:
                (ROOT / "results").mkdir(exist_ok=True)
                shutil.copy(out, ROOT / "results" / f"best{k}.json")
    if improved and not a.no_update:
        with BEST.open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["instance", "objective"])
            for k in sorted(best):
                w.writerow([k, f"{best[k]:.6f}"])
        print("results/best.csv обновлён")
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
