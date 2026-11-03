"""Plot completed anti pair; source data and decomposition accompany the PNG."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from plot_trajectories import COLORS, components, hull

R = Path(__file__).resolve().parent
inp = R / 'inputs/anti.json'
data = json.loads(inp.read_text())
files = [R / 'logs/hybrid_280' / f'anti_1402_{v}.solution.json' for v in ['v4', 'hybrid']]
sols = [json.loads(p.read_text()) for p in files]
xy = [(s['x'], s['y']) for s in data['sites']]
ox = [(o['x'], o['y']) for o in data['offices']]
points = xy + ox
xmin, ymin = min(x for x, y in points), min(y for x, y in points)
extent = max(max(x for x, y in points)-xmin, max(y for x, y in points)-ymin, 1e-12)
assign = [{s: r['officeId'] for r in sol for s in r['sites']} for sol in sols]
changes = {'added': [], 'removed': [], 'reassigned': []}
for s in range(len(xy)):
    a, b = assign[0].get(s), assign[1].get(s)
    if a == b:
        continue
    changes['added' if a is None else 'removed' if b is None else 'reassigned'].append(s)
cs = [components(data, sol) for sol in sols]
pic = Image.new('RGB', (1920,790), 'white')
d = ImageDraw.Draw(pic)
font, small = ImageFont.load_default(size=20), ImageFont.load_default(size=15)
d.text((28,16), 'Anti geometry: frozen v4 versus frozen hybrid / 280 s each / NT=2 / seed 1402', font=font, fill='#17212B')
titles = ['Exact server v4', 'Batch + geometry + joint DP', 'Changed assignments (same input coordinates)']
for panel in range(3):
    left = 55 + panel*635
    def pixel(p):
        return (round(left+(p[0]-xmin)/extent*540), round(625-(p[1]-ymin)/extent*540))
    d.text((left,54), titles[panel], font=small, fill='#17212B')
    d.rectangle((left,85,left+540,625), outline='#CCD2D8')
    for j in range(5):
        pos = left+j*135
        d.text((pos-12,630), f'{xmin+extent*j/4:.2f}', font=small, fill='#555555')
    for p in xy:
        x,y=pixel(p);d.ellipse((x-1,y-1,x+1,y+1),fill='#CDD2D6')
    if panel<2:
        for r in sols[panel]:
            o=r['officeId'];color=COLORS[o%len(COLORS)]
            h=[pixel(p) for p in hull([ox[o]]+[xy[s] for s in r['sites']])]
            if len(h)>1:d.line(h+[h[0]], fill=color, width=2)
            for s in r['sites']:
                x,y=pixel(xy[s]);d.ellipse((x-2,y-2,x+2,y+2),fill=color)
        c=cs[panel]
        d.text((left,663),f'Objective: {c["objective"]:.6f}',font=small,fill='#17212B')
        d.text((left,689),f'Counts: {c["counts"]}; tasks: {c["loads"]}',font=small,fill='#17212B')
        d.text((left,715),f'Site profit: {c["site_profit"]:.3f}; penalty: {c["penalty"]:.3f}',font=small,fill='#17212B')
    else:
        colors={'added':'#009E73','removed':'#D55E00','reassigned':'#882255'}
        for j,(kind,ss) in enumerate(changes.items()):
            color=colors[kind]
            for s in ss:
                x,y=pixel(xy[s]);d.ellipse((x-3,y-3,x+3,y+3),fill=color)
            d.text((left,663+j*26),f'{kind}: {len(ss)}',font=small,fill=color)
    for o,p in enumerate(ox):
        x,y=pixel(p);color=COLORS[o%len(COLORS)]
        d.line((x-5,y-5,x+5,y+5),fill=color,width=2)
        d.line((x-5,y+5,x+5,y-5),fill=color,width=2)
        d.text((x+6,y-18),str(o),font=small,fill=color)
d.text((28,760),'All input sites and office anchors are shown. Equal x/y scale in every panel. Polygon overlap alone is not the feasibility rule.',font=small,fill='#444444')
out=R/'figures/anti_hybrid_280.png';pic.save(out)
metrics={'components':cs,'delta':{k:cs[1][k]-cs[0][k] for k in ['objective','site_profit','office_cost','penalty']},
         'changes':changes,'input_sha256':hashlib.sha256(inp.read_bytes()).hexdigest(),
         'solution_sha256':[hashlib.sha256(p.read_bytes()).hexdigest() for p in files],
         'figure':str(out.relative_to(R))}
(R/'figures/ANTI_HYBRID_280.json').write_text(json.dumps(metrics,indent=2))
print({k:len(v) for k,v in changes.items()},metrics['delta'])
