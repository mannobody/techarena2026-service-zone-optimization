"""Coordinate-faithful PNG plots of the recorded solver snapshots (Pillow)."""
import hashlib,json,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

R=Path(__file__).resolve().parent
COLORS=['#0072B2','#D55E00','#009E73','#CC79A7','#E69F00','#56B4E9',
        '#882255','#44AA99','#332288','#999933','#AA4499','#661100']
def hull(points):
    pts=sorted(set(points))
    if len(pts)<3:return pts
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo=[];hi=[]
    for p in pts:
        while len(lo)>=2 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi)>=2 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
        hi.append(p)
    return lo[:-1]+hi[:-1]

def components(data,sol):
    gain=sum(data['sites'][s]['reward']-data['distances'][row['officeId']][s] for row in sol for s in row['sites'])
    cost=sum(data['offices'][row['officeId']]['cost'] for row in sol)
    loads=[sum(len(data['sites'][s]['tasks']) for s in row['sites']) for row in sol]
    counts=[len(row['sites']) for row in sol]
    penalty=data['balanceCoefficient']*(max(loads,default=0)-min(loads,default=0))
    return {'objective':gain-cost-penalty,'site_profit':gain,'office_cost':cost,'penalty':penalty,
            'counts':counts,'loads':loads,'offices':[row['officeId'] for row in sol]}

def main():
    dest=R/'figures';dest.mkdir(exist_ok=True)
    font=ImageFont.load_default(size=18)
    small=ImageFont.load_default(size=14)
    rows=json.loads((R/'logs/mature_v4_280/results.json').read_text())
    metrics=[]
    for row in rows:
        if row['seed']!=1301:continue
        case=row['case'];data=json.loads((R/'inputs'/f'{case}.json').read_text())
        base=R/'logs/mature_v4_280'/f'{case}_1301_v4'
        files=[Path(str(base)+f'.t{t}.solution.json') for t in [60,240]]+[Path(str(base)+'.solution.json')]
        if not all(p.exists() for p in files):continue
        sols=[json.loads(p.read_text()) for p in files]
        xy=[(s['x'],s['y']) for s in data['sites']]
        ox=[(o['x'],o['y']) for o in data['offices']]
        allxy=xy+ox;mnx=min(p[0] for p in allxy);mny=min(p[1] for p in allxy)
        ext=max(max(p[0] for p in allxy)-mnx,max(p[1] for p in allxy)-mny,1e-12)
        pic=Image.new('RGB',(1860,720),'white');d=ImageDraw.Draw(pic)
        d.text((25,15),f'{case}: exact frozen v4 / seed 1301 / NT=2 / total budget 280 s',font=font,fill='#17212B')
        cs=[components(data,s) for s in sols]
        for panel,(sol,c,t) in enumerate(zip(sols,cs,[60,240,280])):
            left=panel*620+30
            def pixel(p):return (round(left+(p[0]-mnx)/ext*550),round(625-(p[1]-mny)/ext*550))
            d.text((left,51),f't={t}s; objective={c["objective"]:.4f}',font=font,fill='#17212B')
            d.rectangle((left,75,left+550,625),outline='#CCD2D8')
            for p in xy:
                x,y=pixel(p);d.ellipse((x-1,y-1,x+1,y+1),fill='#D0D4D8')
            for r in sol:
                o=r['officeId'];color=COLORS[o%len(COLORS)]
                h=[pixel(p) for p in hull([ox[o]]+[xy[s] for s in r['sites']])]
                if len(h)>1:d.line(h+[h[0]],fill=color,width=2)
                for s in r['sites']:
                    x,y=pixel(xy[s]);d.ellipse((x-2,y-2,x+2,y+2),fill=color)
            active={r['officeId'] for r in sol}
            for o,p in enumerate(ox):
                x,y=pixel(p);color=COLORS[o%len(COLORS)] if o in active else '#444444'
                d.line((x-4,y-4,x+4,y+4),fill=color,width=2)
                d.line((x-4,y+4,x+4,y-4),fill=color,width=2)
                if o in active:d.text((x+5,y-15),str(o),font=small,fill=color)
            d.text((left,639),f'sites={sum(c["counts"])}; count range={min(c["counts"],default=0)}..{max(c["counts"],default=0)}',font=small,fill='#17212B')
            d.text((left,661),f'load range={min(c["loads"],default=0)}..{max(c["loads"],default=0)}; penalty={c["penalty"]:.3f}',font=small,fill='#17212B')
        d.text((25,695),'All sites shown. Grey: unassigned; colour: assigned; crosses: offices. Same coordinate scale across panels.',font=small,fill='#444444')
        file=dest/f'{case}_trajectory.png';pic.save(file)
        assignments=[{s:r['officeId'] for r in sol for s in r['sites']} for sol in sols]
        metrics.append({'case':case,'components':cs,'assignment_changes_60_to_280':sum(assignments[0].get(s)!=assignments[2].get(s) for s in range(len(xy))),
                        'snapshot_sha256':[hashlib.sha256(p.read_bytes()).hexdigest() for p in files],
                        'figure':str(file.relative_to(R))})
    (dest/'METRICS.json').write_text(json.dumps(metrics,indent=2))
    print('figures',len(metrics))
if __name__=='__main__':main()
