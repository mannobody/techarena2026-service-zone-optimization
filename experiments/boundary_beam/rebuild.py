"""Rebuild frozen sources in a fresh directory; never overwrite prior artifacts."""
import argparse,subprocess,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--tag',required=True);ap.add_argument('--names',default='baseline,candidate_tail');a=ap.parse_args();dst=H/'artifacts'/('rebuild_'+a.tag);dst.mkdir()
for name in a.names.split(','):
 if name=='baseline':
  b=H/'baseline/solver';s=(b/'solve.cpp').read_text()
  for p in b.glob('*.h'):s=s.replace(f'#include "{p.name}"',p.read_text())
 else:s=(H/'artifacts'/f'{name}.cpp').read_text()
 p=dst/f'{name}.cpp';p.write_text(s);subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(dst/name)],check=True)
(dst/'manifest.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in dst.iterdir() if p.is_file()},indent=2))
print(dst)
