#!/bin/sh
# Собирает посылку для NSUTS: dist/case03_cpp.zip (Docker, Makefile + solve.cpp).
# solver/solve.cpp включает части solver/*.h — здесь они склеиваются в один solve.cpp,
# поэтому формат посылки прежний. zip не хранится в git: его собирает CI (артефакт) или этот скрипт.
set -e
cd "$(dirname "$0")/.."
mkdir -p dist
rm -f dist/case03_cpp.zip
awk '/^#include "/ { f = $2; gsub(/"/, "", f); while ((getline l < ("solver/" f)) > 0) print l; close("solver/" f); next } { print }' \
    solver/solve.cpp > dist/solve.cpp
if grep -q '^#include "' dist/solve.cpp; then echo "в dist/solve.cpp остались локальные #include" >&2; exit 1; fi
zip -q -X -j dist/case03_cpp.zip submission/cpp/Makefile dist/solve.cpp
echo "ok: dist/case03_cpp.zip ($(git rev-parse --short HEAD 2>/dev/null))"
