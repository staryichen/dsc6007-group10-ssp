"""核对重现时的实际绘图数据与提交 CSV、A 独立评价结果。"""
from pathlib import Path
import csv
import json
import numpy as np
from PIL import Image, ImageChops

ROOT=Path(__file__).resolve().parent
from paths import SOURCE, OUT, TAG
source=SOURCE;review=OUT;repro=review/'reproduced'
read=lambda p:list(csv.DictReader(p.open()))
numeric=json.loads((review/'numeric_audit.json').read_text())
artists=json.loads((repro/'figure_artists.json').read_text())
rows=read(source/'results/e2_alpha_sweep_v3.csv')
fresh=read(repro/f'results/e2_alpha_sweep_{TAG}.csv')
assert len(rows)==len(fresh)==25
max_csv_error=0.
for a,b in zip(rows,fresh):
    for key,value in a.items():
        try:err=abs(float(value)-float(b[key]));max_csv_error=max(max_csv_error,err);assert err<1e-8
        except ValueError:assert value==b[key]
old_json=json.loads((source/'results/e2_policies_v3.json').read_text())
new_json=json.loads((repro/f'results/e2_policies_{TAG}.json').read_text())
json_errors={}
for key in old_json:
    if key in ['mean_value','cvar']:
        error=float(np.max(np.abs(np.asarray(old_json[key])-np.asarray(new_json[key]))))
        assert error<1e-10
        json_errors[key]=error
    else:assert old_json[key]==new_json[key]
f2=artists[f'f2_routes_{TAG}'];sel=numeric['selected']
for line,route in zip(f2['axes'][0]['lines'],[sel['mean_route'],sel['cvar_route']]):
    assert line['x']==[s%10 for s in route] and line['y']==[s//10 for s in route]
for line,key in zip(f2['axes'][1]['lines'],['mean_pmf','cvar_pmf']):
    assert np.array_equal(line['x'],np.arange(161))
    assert np.allclose(line['y'],sel[key],atol=1e-13,rtol=0)
assert f2['axes'][1]['xlim']==[0.,90.]
zone=np.zeros((10,10));zone[2:7,3:7]=1
assert np.array_equal(f2['axes'][0]['images'][0],zone)
f3=artists[f'f3_risk_return_{TAG}']
for ax,p in zip(f3['axes'],[0,.05,.1,.2,.3]):
    subset=[r for r in rows if float(r['p'])==p]
    red=ax['lines'][0]
    assert np.allclose(red['x'],[float(r['cvar_policy_mean']) for r in subset],atol=1e-10,rtol=0)
    assert np.allclose(red['y'],[float(r['cvar_optimal']) for r in subset],atol=1e-10,rtol=0)
    assert np.allclose(ax['collections'][0]['offsets'],[[float(r['mean_optimal']),float(r['mean_policy_cvar'])] for r in subset],atol=1e-10,rtol=0)
    assert [t['text'] for t in ax['texts']]==['0.5','0.8','0.9','0.95','0.99']
figures=[]
for old,new in [('f2_routes_v3',f'f2_routes_{TAG}'),('f3_risk_return_v3',f'f3_risk_return_{TAG}')]:
    a=Image.open(source/'figures'/f'{old}.png').convert('RGB')
    b=Image.open(repro/'figures'/f'{new}.png').convert('RGB')
    figures.append(dict(name=old,submitted_size=list(a.size),reproduced_size=list(b.size),
                        pixel_identical=a.size==b.size and ImageChops.difference(a,b).getbbox() is None))
summary=dict(reproduced_grid_cases=25,max_reproduced_csv_error=max_csv_error,
             exported_json_policy_metadata_identical=True,json_numeric_errors=json_errors,f2_route_pmf_zone_match=True,
             f3_all_25_red_points_and_25_blue_points_match=True,
             figures=figures,limitation='绘图数据已精确核对；字体与库版本导致栅格尺寸差异，不声明二进制或逐像素相同')
(review/'figure_audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False))
