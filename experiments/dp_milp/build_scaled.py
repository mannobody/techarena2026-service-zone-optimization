from pathlib import Path
import subprocess,hashlib,json
H=Path(__file__).resolve().parent
for name in ['window_v1','post_window']:
 s=(H/'artifacts'/f'{name}.cpp').read_text();a=s.index('static bool resize_dp_window(');b=s.index('static bool resize_dp(Sol&',a)
 scaled=s[a:b].replace('resize_dp_window(', 'resize_dp_scaled(',1).replace('I.ntask[x]','(I.ntask[x]/scale)').replace('(int)s.load[ops[b]]','(int)(s.load[ops[b]]/scale)').replace('costs,I.alpha,allow_close','costs,I.alpha*scale,allow_close')
 scaled=scaled.replace('    int K = ops.size();','    int scale=0;for(int o:ops)for(int x:s.members[o])scale=std::gcd(scale,I.ntask[x]);scale=max(1,scale);\n    int K = ops.size();',1)
 s=s[:b]+scaled+s[b:];s=s.replace('atoi(getenv("DP_MODE")):1','atoi(getenv("DP_MODE")):2').replace('return mode?resize_dp_window(s,deadline,allow_close):resize_dp_reference(s,deadline,allow_close);','return mode==2?resize_dp_scaled(s,deadline,allow_close):mode?resize_dp_window(s,deadline,allow_close):resize_dp_reference(s,deadline,allow_close);')
 dest='scaled_v1' if name=='window_v1' else 'post_scaled';p=H/'artifacts'/f'{dest}.cpp';p.write_text(s);subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(p.with_suffix(''))],check=True)
(H/'BUILD_SCALED.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (H/'artifacts').glob('*scaled*')},indent=2))
