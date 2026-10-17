#!/bin/sh
# Собирает посылку для NSUTS: dist/case03_cpp.zip (Docker, Makefile + solve.cpp из solver/).
# zip не хранится в git: его собирает CI (артефакт) или этот скрипт локально.
set -e
cd "$(dirname "$0")/.."
mkdir -p dist
rm -f dist/case03_cpp.zip
zip -q -X -j dist/case03_cpp.zip submission/cpp/Makefile solver/solve.cpp
echo "ok: dist/case03_cpp.zip ($(git rev-parse --short HEAD 2>/dev/null))"
