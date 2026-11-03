"""Create a standalone standard-library candidate, outside shared submission/."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

from build import HERE,ROOT,replace_once


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--variant',choices=['workers','genetic','scout'],default='workers')
    ap.add_argument('--tag',default='candidate_v4');args=ap.parse_args()
    folder=HERE/'artifacts'/args.tag;folder.mkdir(parents=True,exist_ok=True)
    source=(HERE/'artifacts/warm.cpp').read_text()
    if args.variant!='genetic':
        source=replace_once(source,'int evo_mode = getenv("EVO") ? atoi(getenv("EVO")) : 2;',
                            'int evo_mode = getenv("EVO") ? atoi(getenv("EVO")) : 0;')
        source=replace_once(source,'int mode=getenv("EVO")?atoi(getenv("EVO")):2;',
                            'int mode=getenv("EVO")?atoi(getenv("EVO")):0;')
    source=replace_once(source,'if(!getenv("WORKER_DFS")||atoi(getenv("WORKER_DFS"))==0)return false;',
                        'if(getenv("WORKER_DFS")&&atoi(getenv("WORKER_DFS"))==0)return false;')
    if args.variant=='scout':
        source=replace_once(source,'int early = getenv("SCOUT") && atoi(getenv("SCOUT")) ? nth/2 : 0;',
                            'int early = !getenv("SCOUT") || atoi(getenv("SCOUT")) ? nth/2 : 0;')
    assert '#include "' not in source
    (folder/'main.cpp').write_text(source)
    (folder/'Makefile').write_bytes((ROOT/'submission/cpp/Makefile').read_bytes())
    subprocess.run(['make','-s','build'],cwd=folder,check=True)
    archive=HERE/'artifacts'/f'{args.tag}.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name in ('main.cpp','Makefile'):z.write(folder/name,name)
    metadata=dict(variant=args.variant,source_build=json.loads((HERE/'artifacts/build.json').read_text()),
                  sha256={name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in ('main.cpp','Makefile','solution')},
                  archive=str(archive),archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
    (folder/'manifest.json').write_text(json.dumps(metadata,indent=2))
    print(archive)


if __name__=='__main__':main()
