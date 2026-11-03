#!/bin/sh
set -eu
cd .
lab=experiments/v4_perturbation/escape_lab
while [ ! -x "$lab/bin/escape_v4" ]; do sleep 1; done
# This script starts only after the final compilation command is complete.
taskset -c 14,15 g++ -O0 -std=c++17 -pthread "$lab/src/property.cpp" -o "$lab/bin/property" 2> "$lab/logs/build_property.log"
NT=2 taskset -c 14,15 "$lab/bin/property" experiments/v4_perturbation/shared/inputs/dev/tightA.json experiments/v4_perturbation/shared/logs/checkpoint60/tightA_1901_v4.solution.json 2> "$lab/logs/property_tightA.log"
NT=2 taskset -c 14,15 "$lab/bin/property" experiments/v4_perturbation/shared/inputs/dev/multiskill.json experiments/v4_perturbation/shared/logs/checkpoint60/multiskill_1901_v4.solution.json 2> "$lab/logs/property_multiskill.log"
taskset -c 14,15 python3 "$lab/prepare_screen.py" > "$lab/logs/prepare_screen.log"
NT=2 taskset -c 14,15 .venv/bin/python experiments/v4_perturbation/shared/run_blocks.py "$lab/SCREEN60.json" > "$lab/logs/screen60.log" 2>&1
taskset -c 14,15 python3 "$lab/summarize.py" "$lab/logs/screen60" > "$lab/logs/summary60.log"
