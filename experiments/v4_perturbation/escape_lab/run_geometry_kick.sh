#!/bin/sh
set -eu
cd .
lab=experiments/v4_perturbation/escape_lab
while [ ! -f "$lab/logs/repeat280/COMPLETE.json" ]; do sleep 1; done
taskset -c 14,15 g++ -O3 -std=c++17 -pthread "$lab/src/post_geometry_kick.cpp" -o "$lab/bin/post_geometry_kick" 2> "$lab/logs/build_geometry_kick.log"
taskset -c 14,15 python3 "$lab/prepare_geometry_kick.py"
NT=2 taskset -c 14,15 .venv/bin/python experiments/v4_perturbation/shared/run_blocks.py "$lab/GEOMETRY_KICK60.json" > "$lab/logs/geometry_kick60.log" 2>&1
taskset -c 14,15 python3 "$lab/summarize.py" "$lab/logs/geometry_kick60" > "$lab/logs/summary_geometry_kick.log"
