#!/bin/sh
set -eu
cd .
lab=experiments/v4_perturbation/escape_lab
# Caller must first wait for the screen to finish; this job owns CPU14/15.
taskset -c 14,15 g++ -O0 -std=c++17 -pthread "$lab/src/property_extended.cpp" -o "$lab/bin/property_extended" 2> "$lab/logs/build_property_extended.log"
NT=2 taskset -c 14,15 "$lab/bin/property_extended" experiments/v4_perturbation/shared/inputs/dev/tightA.json experiments/v4_perturbation/shared/logs/checkpoint60/tightA_1901_v4.solution.json 2> "$lab/logs/property_extended_tightA.log"
NT=2 taskset -c 14,15 "$lab/bin/property_extended" experiments/v4_perturbation/shared/inputs/dev/multiskill.json experiments/v4_perturbation/shared/logs/checkpoint60/multiskill_1901_v4.solution.json 2> "$lab/logs/property_extended_multiskill.log"
taskset -c 14,15 g++ -O3 -std=c++17 -pthread "$lab/src/post_diagnostic.cpp" -o "$lab/bin/post_diagnostic" 2> "$lab/logs/build_diagnostic.log"
taskset -c 14,15 python3 "$lab/prepare_diagnostic.py"
NT=2 taskset -c 14,15 .venv/bin/python experiments/v4_perturbation/shared/run_blocks.py "$lab/DIAGNOSTIC.json" > "$lab/logs/diagnostic.log" 2>&1
