#!/bin/sh
# Собирает посылку для NSUTS: dist/case03_cpp.zip (Docker: Makefile + main.cpp, как в образце задания).
# solver/solve.cpp включает части solver/*.h — здесь они склеиваются в один main.cpp.
# zip не хранится в git: его собирает CI или этот скрипт.
# dist/pkg/ — те же два файла без упаковки: CI выкладывает их артефактом, и скачанный из GitHub zip
# сразу годен к отправке (Makefile в корне). Не отправлять zip, внутри которого лежит zip, — это вердикт C.
set -e
cd "$(dirname "$0")/.."
mkdir -p dist
rm -f dist/case03_cpp.zip
awk '/^#include "/ { f = $2; gsub(/"/, "", f); while ((getline l < ("solver/" f)) > 0) print l; close("solver/" f); next } { print }' \
    solver/solve.cpp > dist/main.cpp
if grep -q '^#include "' dist/main.cpp; then echo "в dist/main.cpp остались локальные #include" >&2; exit 1; fi
zip -q -X -j dist/case03_cpp.zip submission/cpp/Makefile dist/main.cpp
rm -rf dist/pkg && mkdir dist/pkg && cp submission/cpp/Makefile dist/main.cpp dist/pkg/
# как на тестере: распаковать в пустой каталог и выполнить make build
t=$(mktemp -d) && trap 'rm -rf "$t"' EXIT
unzip -q dist/case03_cpp.zip -d "$t"
make -C "$t" -s build >/dev/null || { echo "make build в распакованной посылке не прошёл" >&2; exit 1; }
[ -x "$t/solution" ] || { echo "после make build нет ./solution" >&2; exit 1; }
echo "ok: dist/case03_cpp.zip ($(git rev-parse --short HEAD 2>/dev/null))"
