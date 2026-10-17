#!/usr/bin/env python3
"""Бенчмарк решателя: сборка (флаги из submission/cpp/Makefile), параллельный прогон,
официальный валидатор, компактная таблица.

    python3 bench.py [сек=60] [--only 0,3] [--runs N] [--base REF] [--synth] [--record]

--runs N   N зёрен (SEED=1..N) на инстанс: печатается медиана и максимум.
--base REF  A/B: тот же прогон для solver/solve.cpp из git-ревизии REF (напр. origin/main),
            колонка delta — медиана ветки против медианы базы на тех же зёрнах.
--synth    вместо открытых инстансов — синтетика tools/gen.py (12 случайных + edge_*),
            главное там — VALID и время, а не значение.
--record   обновить results/best.csv и results/best<k>.json (только открытые инстансы,
            делать в отдельном PR). Без флага лучшие решения кладутся в results/local/.
Итог: score = Σ min(f/best, 1) по открытым инстансам (так нормирует жюри), TIME — wall
превысил лимит + 3 с. Код выхода 1, если есть INVALID или TIME.
"""
import argparse
import csv
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TASK = ROOT / "task"
BEST = ROOT / "results" / "best.csv"
LOCAL = ROOT / "results" / "local"
SYNTH = LOCAL / "synth"


def py_with(mods):
    for py in (str(ROOT / ".venv/bin/python"), sys.executable):
        if Path(py).exists() and subprocess.run([py, "-c", "import " + ",".join(mods)],
                                                capture_output=True).returncode == 0:
            return py
    sys.exit(f"нет модулей {mods}: python3 -m venv .venv && .venv/bin/pip install pydantic shapely")


def build(src, exe):
    """Собирает тем же флагами, что и посылка (строка g++ из Makefile)."""
    mk = (ROOT / "submission/cpp/Makefile").read_text()
    flags = re.search(r"g\+\+ (.*?) -o solve solve\.cpp", mk).group(1).split()
    cxx = os.environ.get("CXX") or shutil.which("g++") or shutil.which("clang++")
    if not cxx:
        sys.exit("нет C++ компилятора: sudo apt install g++")
    subprocess.run([cxx, *flags, "-o", str(exe), str(src)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("seconds", nargs="?", type=float, default=60)
    ap.add_argument("--only", default="")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--base", default="")
    ap.add_argument("--synth", action="store_true")
    ap.add_argument("--record", action="store_true")
    a = ap.parse_args()

    if a.synth:
        if not (SYNTH / "edge_big10k.json").exists():
            SYNTH.mkdir(parents=True, exist_ok=True)
            subprocess.run([sys.executable, str(ROOT / "tools/gen.py"), str(SYNTH), "12", "--edge"],
                           check=True, capture_output=True)
        insts = {p.stem: p for p in sorted(SYNTH.glob("*.json"))}
    else:
        insts = {p.name[8:]: p / "instance.json" for p in sorted(TASK.glob("instance*")) if p.is_dir()}
    if a.only:
        insts = {k: insts[k] for k in a.only.split(",")}

    tmp = Path(tempfile.mkdtemp(prefix="bench_"))
    exes = {"head": tmp / "solve"}
    build(ROOT / "solver/solve.cpp", exes["head"])
    if a.base:
        src = tmp / "base.cpp"
        src.write_text(subprocess.run(["git", "show", f"{a.base}:solver/solve.cpp"], cwd=ROOT,
                                      check=True, capture_output=True, text=True).stdout)
        exes["base"] = tmp / "solve_base"
        build(src, exes["base"])
    vpy = py_with(["pydantic", "shapely"])

    jobs = [(v, k, s) for v in exes for k in insts for s in range(1, a.runs + 1)]
    par = min(len(jobs), os.cpu_count() or 1)
    nt = str(max(1, (os.cpu_count() or 1) // par))

    def run(job):
        v, k, seed = job
        out = tmp / f"{v}_{k}_{seed}.json"
        env = dict(os.environ, NT=nt, SEED=str(seed))
        t0 = time.time()
        r = subprocess.run([str(exes[v]), str(insts[k]), str(out), str(a.seconds)],
                           capture_output=True, text=True, env=env)
        wall = time.time() - t0
        lines = subprocess.run([vpy, "-I", str(TASK / "validate_solution.py"), str(insts[k]), str(out)],
                               capture_output=True, text=True).stdout.strip().splitlines()
        if not lines or lines[0] == "FAIL":
            msg = lines[-1] if lines else (r.stderr.strip()[-60:] or f"rc={r.returncode}")
            return job, None, msg, wall, out
        return job, float(lines[-1]), "", wall, out

    with ThreadPoolExecutor(par) as ex:
        res = list(ex.map(run, jobs))

    best = {}
    if BEST.exists() and not a.synth:
        best = {r["instance"]: float(r["objective"]) for r in csv.DictReader(BEST.open())}
    by = {}
    for (v, k, _), f, msg, wall, out in res:
        by.setdefault((v, k), []).append((f, msg, wall, out))

    print(f"threads/run={nt} runs={a.runs}" + (f" base={a.base}" if a.base else ""))
    print(f"{'inst':>12} {'median':>15} {'max':>15} {'wall':>6} {'ref':>15} {'delta':>8}")
    bad, score, nscore, rec = False, 0.0, 0, False
    for k in insts:
        rs = by[("head", k)]
        wall = max(r[2] for r in rs)
        fails = [r[1] for r in rs if r[0] is None]
        flag = ""
        if wall > a.seconds + 3:
            flag, bad = " TIME", True
        if fails:
            bad = True
            print(f"{k:>12} INVALID {len(fails)}/{len(rs)}: {fails[0]}{flag}")
            continue
        vals = [r[0] for r in rs]
        med, mx = statistics.median(vals), max(vals)
        if a.base:
            bv = [r[0] for r in by[("base", k)] if r[0] is not None]
            ref = statistics.median(bv) if bv else None
        else:
            ref = best.get(k)
        d = "" if ref is None else f"{(med - ref) / max(abs(ref), 1e-9) * 100:+.2f}%"
        print(f"{k:>12} {med:>15.3f} {mx:>15.3f} {wall:>6.1f} "
              f"{'-' if ref is None else f'{ref:.3f}':>15} {d:>8}{flag}")
        b = best.get(k)
        if b is not None and b > 0:
            score += min(med / b, 1.0)
            nscore += 1
        # лучшее решение: в results/local/ всегда, в results/best* — только по --record
        top = max(rs, key=lambda r: r[0])
        LOCAL.mkdir(parents=True, exist_ok=True)
        shutil.copy(top[3], LOCAL / f"{'synth_' if a.synth else ''}best{k}.json")
        if a.record and not a.synth and (b is None or mx > b + 1e-9):
            best[k] = mx
            shutil.copy(top[3], ROOT / "results" / f"best{k}.json")
            rec = True
    if nscore:
        print(f"score (медиана / рекорд, max {nscore}): {score:.4f}")
    if rec:
        with BEST.open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["instance", "objective"])
            for k in sorted(best, key=int):
                w.writerow([k, f"{best[k]:.6f}"])
        print("results/best.csv обновлён")
    shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
