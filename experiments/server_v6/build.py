"""Package the tested deep-research hybrid as the v6 submission candidate."""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RESEARCH = ROOT / 'experiments/v4_deep_parallel/integration'
SOURCE_SHA = 'c7ae1602c35d8d41d7791bbc8a296b3396675d6e858767c7cb69b0a9dd039366'
ZIP_SHA = 'dba049d786ef5cb72829fa4355ae63bb119a1c5d6b48ea85587fbefa9a945a9a'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    original = RESEARCH / 'artifacts/case03_cpp_v4_deep_hybrid_experimental_O3.zip'
    assert sha(original) == ZIP_SHA
    assert sha(RESEARCH / 'src/hybrid_frozen.cpp') == SOURCE_SHA
    artifacts = HERE / 'artifacts'
    package = artifacts / 'package'
    package.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(original) as z:
        assert sorted(z.namelist()) == ['Makefile', 'main.cpp']
        for name in z.namelist():
            target = package / name
            data = z.read(name)
            if target.exists():
                assert target.read_bytes() == data, f'Refusing to overwrite changed {target}'
            else:
                target.write_bytes(data)
    assert sha(package / 'main.cpp') == SOURCE_SHA
    targets = [artifacts / 'case03_cpp_server_v6_O3.zip', ROOT / 'dist/case03_cpp_server_v6_O3.zip']
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert sha(target) == ZIP_SHA, f'Refusing to overwrite changed {target}'
        else:
            shutil.copyfile(original, target)
    manifest = {
        'version': 'v6', 'status': 'experimental server candidate, not submitted',
        'source_sha256': SOURCE_SHA, 'zip_sha256': ZIP_SHA,
        'source': str((package / 'main.cpp').relative_to(ROOT)),
        'archives': [str(p.relative_to(ROOT)) for p in targets],
        'defaults': {'TL': 280, 'GEOM_TAIL': 15, 'JOINT_TERRITORY': 1, 'HYBRID_ORDER': 0},
        'threads': 'automatic CPU-affinity detection, NT override supported; benchmarks NT=2',
        'runtime': 'C++17/Linux; no SCIP/HiGHS dependency',
        'provenance': str((RESEARCH / 'FINAL_FREEZE.json').relative_to(ROOT)),
        'quality': 'Same tested frozen hybrid: holdout60 mean +0.1332%; holdout280 mean -0.1765%, worst -2.0007%. No new quality claim.',
        'identity': 'ZIP and source are byte-identical to the tested research candidate; only the archive filename is versioned.'
    }
    (HERE / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(targets[-1])


if __name__ == '__main__':
    main()
