"""Build and fingerprint the integrated solver; retain the old baseline separately."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]


def build(compile=True):
    source=(ROOT/'solver/solve.cpp').read_text()
    inputs=[ROOT/'solver/solve.cpp',*(ROOT/'solver').glob('*.h')]
    for p in inputs[1:]:source=source.replace(f'#include "{p.name}"',p.read_text())
    assert '#include "' not in source
    path=HERE/'artifacts/integrated.cpp';path.write_text(source)
    exe=HERE/'artifacts/integrated'
    if compile:subprocess.run(['g++','-O2','-std=c++17',str(path),'-o',str(exe)],check=True)
    assert exe.exists()
    (HERE/'artifacts/integrated_build.json').write_text(json.dumps(dict(
        source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        flattened_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        binary_sha256=hashlib.sha256(exe.read_bytes()).hexdigest()),indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--no-compile',action='store_true');args=ap.parse_args()
    build(not args.no_compile)
