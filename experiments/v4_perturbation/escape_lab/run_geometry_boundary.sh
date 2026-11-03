#!/bin/sh
set -eu
cd .
lab=experiments/v4_perturbation/escape_lab
while [ ! -f "$lab/logs/geometry_kick60/COMPLETE.json" ]; do sleep 1; done
taskset -c 14,15 g++ -O3 -std=c++17 -pthread "$lab/src/post_geometry_boundary.cpp" -o "$lab/bin/post_geometry_boundary" 2> "$lab/logs/build_geometry_boundary.log"
while [ ! -f "$lab/POLISH_SUPERSEDED.json" ]; do sleep 1; done
taskset -c 14,15 python3 "$lab/prepare_geometry_boundary.py"
NT=2 taskset -c 14,15,18,19 .venv/bin/python experiments/v4_perturbation/shared/run_blocks.py "$lab/GEOMETRY_BOUNDARY60.json" > "$lab/logs/geometry_boundary60.log" 2>&1
taskset -c 14,15 python3 "$lab/summarize_anycpu.py" "$lab/logs/geometry_boundary60" > "$lab/logs/summary_geometry_boundary.log"
