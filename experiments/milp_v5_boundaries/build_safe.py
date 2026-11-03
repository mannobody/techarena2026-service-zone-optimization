"""Reproduce the frozen safe candidate; use --output for a new build, never overwrite."""
from pathlib import Path
import argparse,subprocess,hashlib,json
H=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--output',type=Path);a=p.parse_args()
base=H.parent/'milp_v5/artifacts/native_v5.cpp';header=H/'src/region_mip_safe.h';s=base.read_text().replace('int main(int argc, char** argv)',header.read_text()+'\nint main(int argc, char** argv)',1)
pos=s.index('static void worker(');s=s[:pos]+'static void v52_finish(const Inst&,double);\n'+s[pos:];pos=s.index('static void worker(');before=s[:pos];after=s[pos:];after=after.replace('    int round = 0;','    int round = 0;\n    bool regional_done=false;',1)
after=after.replace('        double now0 = elapsed();','''        if(tid==0&&!regional_done&&elapsed()>=.70*tend&&(!getenv("REGION")||atoi(getenv("REGION")))&&(!getenv("MIP")||atoi(getenv("MIP")))){
            regional_done=true;v52_finish(I,min(tend-max(.8,.02*tend),elapsed()+min(2.,.035*tend)));
        }
        double now0 = elapsed();''',1);s=before+after
if a.output:
 assert a.output.suffix=='.cpp' and not a.output.exists() and not a.output.with_suffix('').exists()
 a.output.write_text(s);subprocess.run(['g++','-O3','-std=c++17',str(a.output),'-o',str(a.output.with_suffix('')),'-ldl'],check=True)
else:
 assert s==(H/'artifacts/native_safe.cpp').read_text()
 r=dict(reproduced_exactly=True,command='g++ -O3 -std=c++17 main.cpp -o solution -ldl',source_sha256=hashlib.sha256(s.encode()).hexdigest(),header_sha256=hashlib.sha256(header.read_bytes()).hexdigest(),base_sha256=hashlib.sha256(base.read_bytes()).hexdigest());(H/'BUILD_SAFE.json').write_text(json.dumps(r,indent=2));print(r)
