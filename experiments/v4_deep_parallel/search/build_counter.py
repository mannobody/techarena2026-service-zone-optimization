from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent;s=(R/'src/lab2.cpp').read_text()
s=s.replace('const bool persist=lab_flag("LAB_ARCHIVE"), wide=lab_flag("LAB_WIDE");','const bool persist=lab_flag("LAB_ARCHIVE"), wide=lab_flag("LAB_WIDE"), counter=wide||lab_flag("LAB_COUNTER");')
s=s.replace('int r = (wide?starts:round)', 'int r = (counter?starts:round)')
s=s.replace('            starts++;','''            if(lab_flag("LAB_TRACE"))fprintf(stderr,"schedule tid=%d round=%d fromBest=0 starts=%d selected=%d old_rank=%zu counter_rank=%zu wide_rank=%zu combo=%d time=%.6f\\n",tid,round,starts,r,round%max<size_t>(1,min<size_t>(rank.size(),6)),starts%max<size_t>(1,min<size_t>(rank.size(),6)),starts%max<size_t>(1,rank.size()),rank[r].second,elapsed());
            starts++;''')
s=s.replace('        round++;\n        if (!fromBest', '        if(fromBest && lab_flag("LAB_TRACE"))fprintf(stderr,"schedule tid=%d round=%d fromBest=1 starts=%d time=%.6f\\n",tid,round,starts,elapsed());\n        round++;\n        if (!fromBest')
s=s.replace('    if (DBG && tid == 0) {','    if (DBG && (tid == 0 || lab_flag("LAB_TRACE"))) {\n        fprintf(stderr,"rank_owner tid=%d\\n",tid);')
(R/'src/counter.cpp').write_text(s);(R/'COUNTER_SOURCE.json').write_text(json.dumps({'sha256':hashlib.sha256(s.encode()).hexdigest(),'base':'src/lab2.cpp','new_flags':['LAB_COUNTER','LAB_TRACE'],'LAB_COUNTER':'real-start counter, top6 only','LAB_WIDE':'real-start counter, whole rank'},indent=2))
spec=json.loads((R/'PHASE2_BLOCK60.json').read_text());spec.update(name='counter_pilot30',seconds=30,jobs=2,cpus=[8,9,10,11],seeds=[1301,1302]);spec['cases']={k:spec['cases'][k] for k in ['multiskill']};b='experiments/v4_deep_parallel/search/bin/counter';spec['variants']={'trace_off':{'binary':b,'env':{'DBG':'1','LAB_TRACE':'1'}},'counter':{'binary':b,'env':{'DBG':'1','LAB_TRACE':'1','LAB_COUNTER':'1'}},'wide':{'binary':b,'env':{'DBG':'1','LAB_TRACE':'1','LAB_WIDE':'1'}}};(R/'COUNTER_PILOT30.json').write_text(json.dumps(spec,indent=2))
