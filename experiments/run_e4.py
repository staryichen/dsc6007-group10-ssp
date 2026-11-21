"""Optional scaling benchmark; median of three runs, including mean solve."""
import argparse
import platform
import time
import numpy as np
import scipy
from ssp.envs.grid import make_grid
from ssp.solvers.budget_dp import budget_dp
from experiments.c_common import output_dirs,write_csv
import ssp.figstyle as fs
import matplotlib.pyplot as plt


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--tag',default='v1')
    args=parser.parse_args();output_dirs(args.tag,'e4');rows=[]
    for size in [10,20,40]:
        env=make_grid(size=size,start=(size//2-1,0),goal=(size//2-1,size-1),
                      zone_rows=(size//5,3*size//5),zone_cols=(3*size//10,3*size//5))
        for B in [128,256,512]:
            times=[]
            for repeat in range(3):
                start=time.perf_counter();result=budget_dp(env,.9,B=B)
                times.append(time.perf_counter()-start)
            rows.append(dict(size=size,states=env.n_states,B_requested=B,
                B_actual=result.W.shape[1]-1,seconds_median=float(np.median(times)),
                seconds_min=min(times),seconds_max=max(times),repeats=3,
                table_bytes=result.W.nbytes+result.policy.nbytes,cvar=result.value,
                p=.1,q=.1,alpha=.9,seed='not_used',python=platform.python_version(),
                numpy=np.__version__,scipy=scipy.__version__,platform=platform.platform()))
            print(rows[-1],flush=True)
    write_csv(f'results/e4_scaling_{args.tag}.csv',rows)
    fs.setup('report');fig,ax=plt.subplots(figsize=(5,3.5))
    for size in [10,20,40]:
        subset=[r for r in rows if r['size']==size]
        ax.plot([r['B_actual'] for r in subset],[r['seconds_median'] for r in subset],'-o',label=f'{size} x {size}')
    ax.set_xlabel('Budget cap B');ax.set_ylabel('Wall time (seconds, median of 3)')
    ax.legend();fig.tight_layout();fs.save(fig,f'figures/f7_scaling_{args.tag}');plt.close(fig)


if __name__=='__main__': main()
