"""Apply the development-only selection rule and build one frozen candidate."""
import json,statistics,subprocess,sys,time
from pathlib import Path
I=Path(__file__).resolve().parent;R=I.parent;ROOT=R.parents[1]
sys.path.insert(0,str(R/'shared'))
from analyze import analyze,describe,sha
rule=json.loads((I/'FINAL_SELECTION_RULE.json').read_text())
assert not rule['additional_series_complete_at_registration']
assert sha(ROOT/rule['full_source'])==rule['source_sha256']
summaries=[]
for name in ['BOUNDARY_DEVELOPMENT60','BOUNDARY_DEVELOPMENT60_VARIANCE']:
    spec=json.loads((I/f'{name}.json').read_text())
    summary=analyze(ROOT/spec['destination']);summaries.append(summary)
    target=I/f'{name}_SUMMARY.json'
    if target.exists():assert json.loads(target.read_text())==json.loads(json.dumps(summary))
    else:target.write_text(json.dumps(summary,indent=2))
pooled={}
for key in summaries[0]['comparisons']:
    pairs=sum([s['comparisons'][key]['pairs'] for s in summaries],[])
    bycase={c:describe([x['pct'] for x in pairs if x['case']==c and x.get('pct') is not None]) for c in summaries[0]['comparisons'][key]['by_case']}
    pooled[key]={'input_weighted_mean':statistics.mean(x['mean'] for x in bycase.values()),'by_case':bycase,
                 'pair_distribution_descriptive_only':describe([x['pct'] for x in pairs if x.get('pct') is not None]),
                 'wtl':{k:sum(x.get('result')==k for x in pairs) for k in ['win','tie','loss']}}
g=pooled['geometry_boundary_vs_v4']['input_weighted_mean'];b=pooled['boundary_only_vs_v4']['input_weighted_mean']
variant='geometry_boundary' if g>b+1e-9 else 'boundary_only';mode=rule['eligible_variants'][variant]
selection={'selected_unix':time.time(),'rule_sha256':sha(I/'FINAL_SELECTION_RULE.json'),'variant':variant,'mode':mode,
    'pooled_development':pooled,'all_development_successful':all(s['runs']==s['success'] for s in summaries),
    'note':'Research selection only. Large regressions and development reuse prevent a superiority claim; independent protocol must still pass.'}
(I/'FINAL_SELECTION.json').write_text(json.dumps(selection,indent=2))
print('Selected',variant,mode,'input-weighted means geometry/boundary',g,b,flush=True)
subprocess.run([sys.executable,str(I/'prepare_final.py'),str(mode)],check=True,cwd=ROOT)
f=json.loads((I/'FINAL_FREEZE.json').read_text())
contract={'destination':str((I/'logs/final_contract10').relative_to(ROOT)),
    'source':f['source'],'binary':f['binary'],'env':{},'seconds':10,'cpu':[18,19]}
(I/'FINAL_CONTRACT10.json').write_text(json.dumps(contract,indent=2))
