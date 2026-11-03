import pathlib,json,time,hashlib
lab=pathlib.Path(__file__).resolve().parent;root=lab.parents[2]
spec=json.loads((lab/'SCREEN60.json').read_text());spec.update(destination=str((lab/'logs/diagnostic').relative_to(root)),seeds=[2401,2402],order_seed=871044)
spec['variants']={k:{'binary':str((lab/'bin/post_diagnostic').relative_to(root)),'source':str((lab/'src/post_diagnostic.cpp').relative_to(root)),'mode':m,'env':{'DBG':'1'}}for k,m in [('kick',1),('late',2),('tabu',3)]}
(lab/'DIAGNOSTIC.json').write_text(json.dumps(spec,indent=2))
paths=[lab/'src/escape_diagnostic.h',lab/'src/escape_diagnostic_v4.cpp',lab/'src/post_diagnostic.cpp',lab/'bin/post_diagnostic']
(lab/'FREEZE_DIAGNOSTIC.json').write_text(json.dumps({'time':time.time(),'quality_source_unchanged':True,'files':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}},indent=2))
