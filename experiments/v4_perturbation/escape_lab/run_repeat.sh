#!/bin/sh
set -eu
cd .
lab=experiments/v4_perturbation/escape_lab
while [ ! -f "$lab/logs/diagnostic/COMPLETE.json" ]; do sleep 1; done
taskset -c 14,15 g++ -O3 -std=c++17 -pthread "$lab/src/post_repeat_escape.cpp" -o "$lab/bin/post_repeat_escape" 2> "$lab/logs/build_repeat_escape.log"
taskset -c 14,15 g++ -O3 -std=c++17 -pthread "$lab/src/post_repeat_v4.cpp" -o "$lab/bin/post_repeat_v4" 2> "$lab/logs/build_repeat_v4.log"
taskset -c 14,15 python3 "$lab/prepare_repeat.py"
NT=2 taskset -c 14,15 .venv/bin/python experiments/v4_perturbation/shared/run_blocks.py "$lab/REPEAT280.json" > "$lab/logs/repeat280.log" 2>&1
taskset -c 14,15 python3 "$lab/summarize.py" "$lab/logs/repeat280" > "$lab/logs/summary_repeat.log"
