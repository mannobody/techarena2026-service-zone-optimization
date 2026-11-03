import pathlib,json,hashlib,subprocess,time,os
root=pathlib.Path(__file__).resolve().parents[3]; lab=pathlib.Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[root/'experiments/v4_local_search/baseline/frozen_v4.cpp',root/'experiments/v4_perturbation/shared/checkpoint.h',root/'experiments/v4_perturbation/shared/post_v4.cpp']+list((lab/'src').glob('*'))+list((lab/'bin').glob('*'))
freeze={'time':time.time(),'files':{str(p.relative_to(root)):sha(p) for p in files},'compiler':subprocess.check_output(['g++','--version'],text=True),'flags':['-O3','-std=c++17','-pthread'],'cpu':[14,15],'NT':2}
(lab/'FREEZE_SCREEN.json').write_text(json.dumps(freeze,indent=2))
classes=['anti','tightA','alphabig','multiskill','large','huge'];dev=json.loads((root/'experiments/v4_perturbation/shared/DEV_INPUTS.json').read_text())
variants={'v4':{'binary':str((lab/'bin/post_v4').relative_to(root)),'source':'experiments/v4_perturbation/shared/post_v4.cpp','mode':0,'env':{'DBG':'1'}}}
for label,mode in [('off',0),('retain',4),('kick',1),('late',2),('tabu',3)]:variants[label]={'binary':str((lab/'bin/post_escape').relative_to(root)),'source':str((lab/'src/post_escape.cpp').relative_to(root)),'mode':mode,'env':{'DBG':'1'}}
spec={'destination':str((lab/'logs/screen60').relative_to(root)),'seconds':4,'cpu_pairs':[[14,15]],'seeds':[2101,2102],'cases':{c:dev[c]['path'] for c in classes},'checkpoints':{c:f'experiments/v4_perturbation/shared/logs/checkpoint60/{c}_1901_v4.solution.json' for c in classes},'variants':variants,'order_seed':871001}
(lab/'SCREEN60.json').write_text(json.dumps(spec,indent=2))
print(json.dumps({'freeze':str(lab/'FREEZE_SCREEN.json'),'spec':str(lab/'SCREEN60.json')}))
