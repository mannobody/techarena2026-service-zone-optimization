"""Package the actual integrated solver, without touching shared dist outputs."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

from build_current import HERE,ROOT,build


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--tag',default='integrated_v1')
    ap.add_argument('--optimization',choices=['O2','O3'],default='O2');args=ap.parse_args()
    build(compile=False)
    folder=HERE/'artifacts'/args.tag;folder.mkdir(parents=True,exist_ok=True)
    shutil.copy2(HERE/'artifacts/integrated.cpp',folder/'main.cpp')
    shutil.copy2(ROOT/'submission/cpp/Makefile',folder/'Makefile')
    makefile=folder/'Makefile';text=makefile.read_text()
    assert text.count('-O2')==1
    makefile.write_text(text.replace('-O2','-'+args.optimization,1))
    subprocess.run(['make','-s','build'],cwd=folder,check=True)
    archive=HERE/'artifacts'/(args.tag+'.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for name in ('main.cpp','Makefile'):z.write(folder/name,name)
    meta=dict(optimization='-'+args.optimization,
              source_build=json.loads((HERE/'artifacts/integrated_build.json').read_text()),
              sha256={n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in ('main.cpp','Makefile','solution')},
              archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
    (folder/'manifest.json').write_text(json.dumps(meta,indent=2));print(archive)
