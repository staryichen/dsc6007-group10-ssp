"""在独立目录重跑 C 的 E2，并记录 F2/F3 实际交给绘图库的数据。"""
from pathlib import Path
import json
import os
import runpy
import sys

ROOT=Path(__file__).resolve().parent
from paths import SOURCE, OUT, TAG
sys.path.insert(0,str(SOURCE))
import ssp.figstyle as fs

out=OUT/'reproduced'
out.mkdir(parents=True,exist_ok=True)
os.chdir(out)
original_save=fs.save
captured={}


def save_with_evidence(fig,stem):
    """保留曲线、散点、标题和标注，供 A 与提交 CSV 独立核对。"""
    axes=[]
    for ax in fig.axes:
        axes.append(dict(title=ax.get_title(),xlabel=ax.get_xlabel(),ylabel=ax.get_ylabel(),
            xlim=list(ax.get_xlim()),ylim=list(ax.get_ylim()),
            lines=[dict(label=line.get_label(),x=line.get_xdata().tolist(),y=line.get_ydata().tolist()) for line in ax.lines],
            collections=[dict(label=c.get_label(),offsets=c.get_offsets().tolist()) for c in ax.collections],
            images=[im.get_array().tolist() for im in ax.images],
            texts=[dict(text=t.get_text(),position=list(t.get_position())) for t in ax.texts]))
    captured[Path(stem).name]=dict(title=fig._suptitle.get_text() if fig._suptitle else '',axes=axes)
    original_save(fig,stem)
    (out/'figure_artists.json').write_text(json.dumps(captured,ensure_ascii=False,indent=2)+'\n')


fs.save=save_with_evidence
sys.argv=['run_e2','--tag',TAG]
runpy.run_module('experiments.run_e2',run_name='__main__')
