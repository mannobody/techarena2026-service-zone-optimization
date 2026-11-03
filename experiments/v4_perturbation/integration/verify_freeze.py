"""Bind each independent run to the candidate frozen before data generation."""
import hashlib,json
from pathlib import Path
I=Path(__file__).resolve().parent
ROOT=I.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(specpath=None, manifest=None):
    f=json.loads((I/'FINAL_FREEZE.json').read_text())
    for key in ['source','binary']:
        assert sha(ROOT/f[key])==f[key+'_sha256'], f'frozen {key} changed'
    assert sha((ROOT/f['source']).parent/'Makefile')==f['makefile_sha256']
    records=json.loads((I/'HOLDOUT_INPUTS.json').read_text())
    assert records['freeze_sha256']==sha(I/'FINAL_FREEZE.json')
    assert f['frozen_unix'] < records['generated_unix']
    if specpath is not None:
        sp=Path(specpath);s=json.loads(sp.read_text())
        seconds=s['seconds'];assert seconds in [60,280]
        extra=sp.stem.endswith('_VARIANCE')
        assert sp.stem==f'HOLDOUT{seconds}'+('_VARIANCE' if extra else '')
        expected_cases=set(records['inputs']) if seconds==60 else {'anti','tightA','alphabig','multiskill','cluster','huge'}
        expected_seeds=[2101,2102,2103] if seconds==60 else [2201,2202]
        if extra:
            decision=json.loads((I/f'HOLDOUT{seconds}_DECISION.json').read_text())
            expected_cases=set(decision['variance_extension_reasons'])
            expected_seeds=[2104,2105] if seconds==60 else [2203,2204]
        assert set(s['cases'])==expected_cases
        assert s['seeds']==expected_seeds
        assert len(records['inputs'])==12
        assert set(s['variants'])=={'v4','off','candidate'}
        for name,env in [('candidate',f['candidate_env']),('off',f['off_env'])]:
            assert s['variants'][name]=={'binary':f['binary'],'source':f['source'],'env':env}
        v=s['variants']['v4']
        assert sha(ROOT/v['source'])=='5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25'
        assert sha(ROOT/v['binary'])=='5cc54b6ad0f02a3d6d471d0e2f9129c229b4925aaa2b2c01ce26bd5305a4963c'
        for case,path in s['cases'].items():
            assert path==records['inputs'][case]['path']
            assert sha(ROOT/path)==records['inputs'][case]['sha256']
        if manifest is not None:
            assert manifest['spec']==s
            assert manifest['spec_sha256']==sha(Path(specpath))
            for label in ['off','candidate']:
                assert manifest['sources'][label]==f['source_sha256']
                assert manifest['binaries'][label]==f['binary_sha256']
            assert manifest['runner_sha256']==sha(I.parent/'shared/run_blocks.py')
            assert manifest['validator_sha256']==sha(ROOT/'task/validate_solution.py')
            d=ROOT/s['destination']
            for row in json.loads((d/'results.json').read_text()):
                stem=f"{row['case']}_{row['seed']}_{row['variant']}"
                assert json.loads((d/(stem+'.json')).read_text())==row
                if row.get('solution_sha256'):
                    assert sha(d/(stem+'.solution.json'))==row['solution_sha256']
    return True
