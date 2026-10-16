#!/bin/sh
# Собирает посылки для NSUTS: submission/case03_cpp.zip и submission/case03_python.zip.
# solve.cpp / solve.py берутся из solver/, чтобы посылка не расходилась с кодом.
set -e
cd "$(dirname "$0")"
cp ../solver/solve.cpp cpp/solve.cpp
cp ../solver/solve.py python/solve.py
rm -f case03_cpp.zip case03_python.zip
(cd cpp && zip -q -X ../case03_cpp.zip Makefile solve.cpp)
(cd python && zip -q -X ../case03_python.zip Makefile requirements.txt solve.py)
echo "ok: case03_cpp.zip case03_python.zip"
