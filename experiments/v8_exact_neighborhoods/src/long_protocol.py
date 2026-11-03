"""Append-only diagnostic extension following user's concern about TL10.
Does not relax acceptance or replace a failed primary result. No candidate edit.
"""
import hashlib,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
f=json.loads((R/'FREEZE.json').read_text());base=json.loads((R/'CONDITIONAL60.json').read_text())
assert not (R/'LONG_PROTOCOL_ADDENDUM.json').exists()
for p,h in f['files'].items():assert sha(ROOT/p)==h,(p,'frozen file changed')
names=['anti','tightA_alpha','multi_deficit','huge']
base.update(destination=str((R/'logs/long60_diagnostic').relative_to(ROOT)),seeds=[3401,3402],
    cases={k:base['cases'][k] for k in names},order_seed=20261023)
(R/'LONG60_DIAGNOSTIC.json').write_text(json.dumps(base,indent=2))
(R/'LONG_PROTOCOL_ADDENDUM.json').write_text(json.dumps(dict(registered_unix=time.time(),freeze_sha256=sha(R/'FREEZE.json'),
    motivation='User explicitly noted that some search situations cannot be caught at ten seconds; original request permits TL60 for the best candidates.',
    candidate_unchanged=True,one_candidate_only=True,primary_criteria_unchanged=True,
    primary_failure_remains_failure=True,acceptance_requires_primary_AND_long=True,
    change='Run a diagnostic TL60 even if the primary gate fails; redistribute the already capped 32 long processes into 4 named classes x 2 seeds x 4 variants.',
    names=names,processes=32,TL=60,TL280=0,
    scope='Same four inputs already in the eight frozen primary inputs; not four additional independent tasks. No combined percentages across budgets.',
    no_selection_after_viewing_long_results=True,accept=f['accept']),indent=2))
print('TL60 diagnostic preregistered: 32 processes, 4 inputs x 2 seeds x 4 variants; original TL10 verdict preserved.')
