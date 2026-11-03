"""Build separate experimental ZIP without deleting or overwriting historical dist/.
Uses the same one-level include flattening and Makefile as make_zips.sh.
"""
from pathlib import Path
import re,json,hashlib,zipfile
R=Path(__file__).resolve().parent;ROOT=R.parents[1];source=R/'src/candidate_v4';dest=R/'artifacts/package_cycle_safe';dest.mkdir(exist_ok=True)
s=(source/'solve.cpp').read_text();s=re.sub(r'^#include "([^"]+)"\s*$',lambda m:(source/m[1]).read_text(),s,flags=re.M)
old='vector<State> population{current};'
assert s.count(old)==1
s=s.replace(old,'vector<State> population(mode==4?4:1,current);')
assert not re.search(r'^#include "',s,re.M)
a='int depth=getenv("FINAL_EXCHANGE")?max(0,min(2,atoi(getenv("FINAL_EXCHANGE")))):0;';b='if(getenv("BALANCED_CYCLE") && atoi(getenv("BALANCED_CYCLE")))'
assert s.count(a)==1 and s.count(b)==1
s=s.replace(a,a[:-2]+'2;').replace(b,'if(!getenv("BALANCED_CYCLE") || atoi(getenv("BALANCED_CYCLE")))')
(dest/'main.cpp').write_text(s);(dest/'Makefile').write_bytes((ROOT/'submission/cpp/Makefile').read_bytes())
archive=R/'artifacts/case03_cpp_v4_balanced_cycle_safe_experimental_O3.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for n in ['main.cpp','Makefile']:z.write(dest/n,n)
(R/'PACKAGE_SAFE.json').write_text(json.dumps({'source':'candidate_v4 plus GWW population initialization fix (inactive under default SEARCH_MODE=0)','default_overrides':{'FINAL_EXCHANGE':2,'BALANCED_CYCLE':1},'TL_default':280,'files':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [archive,dest/'main.cpp',dest/'Makefile']},'experimental':True,'submitted':False},indent=2))
print(archive)
