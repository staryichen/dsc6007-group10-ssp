"""Discounted optimization evaluated under the true undiscounted objective."""
import argparse
import numpy as np
from ssp.envs.grid import make_grid
from ssp.solvers.expected import value_iteration,evaluate_policy
from experiments.c_common import output_dirs,write_csv


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--tag',default='v1')
    args=parser.parse_args();output_dirs(args.tag,'e9');rows=[]
    for p in [0,.05,.1,.2,.3]:
        env=make_grid(p=p);base=value_iteration(env)
        optimum=evaluate_policy(env,base.policy)[env.start]
        for gamma in [1.,.99,.9]:
            result=value_iteration(env,gamma)
            actual=evaluate_policy(env,result.policy)[env.start]
            rows.append(dict(p=p,q=.1,delay=10,p_slow=.2,gamma=gamma,
                             discounted_value=result.value[env.start],true_total_cost=actual,
                             undiscounted_optimum=optimum,absolute_gap=actual-optimum,
                             relative_gap_percent=100*(actual/optimum-1),
                             proper_all_states=env.is_proper(result.policy),
                             finite_from_start=bool(np.isfinite(actual)),
                             changed_states=int(np.count_nonzero(result.policy!=base.policy)),
                             bellman_residual=result.residual,seed='not_used'))
    write_csv(f'results/e9_discount_comparison_{args.tag}.csv',rows)
    for r in rows: print(r)


if __name__=='__main__': main()
