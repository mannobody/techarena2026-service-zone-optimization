#!/bin/sh
set -eu
cd .
lab=experiments/v4_perturbation/escape_lab
taskset -c 18,19 g++ -O3 -std=c++17 -pthread "$lab/src/post_geometry_kick_polish.cpp" -o "$lab/bin/post_geometry_kick_polish" 2> "$lab/logs/build_geometry_kick_polish.log"
taskset -c 18,19 python3 "$lab/prepare_geometry_kick_polish.py"
NT=2 taskset -c 18,19 .venv/bin/python experiments/v4_perturbation/shared/run_blocks.py "$lab/GEOMETRY_KICK_POLISH60.json" > "$lab/logs/geometry_kick_polish60.log" 2>&1
taskset -c 18,19 python3 "$lab/summarize.py" "$lab/logs/geometry_kick_polish60" > "$lab/logs/summary_geometry_kick_polish.log"
