import pathlib,hashlib,json,difflib
root=pathlib.Path(__file__).resolve().parents[3]
lab=pathlib.Path(__file__).resolve().parent
base=root/'experiments/v4_local_search/baseline/frozen_v4.cpp'
s=base.read_text(); assert hashlib.sha256(base.read_bytes()).hexdigest()=='5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25'
original=s
start=s.index('static void lns(');end=s.index('// Сколько потоков',start)
p=s[start:end]
p=p.replace('    double dur = max(1e-3, tloop - t_start);','    double dur = max(1e-3, tloop - t_start);\n    EscapeControl escape(s,tloop,scale);')
p=p.replace('            if (now >= tloop) break;','            if (now >= tloop) break;\n            if (escape.tick(E,Gd,rng,cur,now)) wsig=~0ULL;')
old='d > -1e-12 || U(rng) < exp(d / max(1e-12, T))';assert p.count(old)==5
p=p.replace(old,'escape.accept(d,T,rng,U,E)')
p=p.replace('        dpn++;','        escape.resync();\n        dpn++;')
p=p.replace('    if (elapsed() < dp_deadline) try_dp();','    escape.finish(E,Gd,cur);\n    if (elapsed() < dp_deadline) try_dp();')
s=s[:start]+'#include "escape.h"\n\n'+p+s[end:]
(lab/'src/escape_v4.cpp').write_text(s)
(lab/'src/integration.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='frozen_v4.cpp',tofile='escape_v4.cpp')))
(lab/'SOURCE.json').write_text(json.dumps({'baseline_sha256':hashlib.sha256(base.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(s.encode()).hexdigest(),'header_sha256':hashlib.sha256((lab/'src/escape.h').read_bytes()).hexdigest(),'cpu':[14,15],'default_mode':0},indent=2)+'\n')
