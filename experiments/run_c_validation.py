"""Execute C's actual policies: exact history enumeration and 100k MC x 10 seeds."""
import argparse
import itertools
import numpy as np
from tests.test_solvers import example2, enumerate_policies
from ssp.envs.acyclic import example1, _cost_distribution
from ssp.envs._checks import discrete_cvar
from ssp.solvers.budget_dp import budget_dp
from ssp.solvers.dist import budget_policy, cost_distribution
from experiments.c_common import output_dirs, write_csv


def empirical(counts, support, n, alpha):
    return np.min([y+(counts@np.maximum(support-y,0))/n/(1-alpha) for y in support],axis=0)


def simulate(env, choose, n, rng):
    # Vectorized real trajectories, grouped by (state, actual accumulated cost).
    states=np.full(n,env.start);spent=np.zeros(n,dtype=int)
    for _ in range(env.n_states):
        active=np.flatnonzero(states!=env.goal)
        if len(active)==0: return spent
        pairs=np.stack((states[active],spent[active]),axis=1)
        for s,z in np.unique(pairs,axis=0):
            indices=active[(pairs[:,0]==s)&(pairs[:,1]==z)]
            outs=env.outcomes[s][choose(int(s),int(z))]
            draw=np.searchsorted(np.cumsum([o.prob for o in outs]),rng.random(len(indices)),side='right')
            for k,o in enumerate(outs):
                selected=indices[draw==k];states[selected]=o.next_state;spent[selected]+=o.cost
    if np.any(states!=env.goal): raise AssertionError('acyclic trajectories did not terminate')
    return spent


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--tag',default='v1')
    args=parser.parse_args();output_dirs(args.tag,'c_validation');exact=[];mc=[]
    for env in [example1(),example2()]:
        distributions=list(enumerate_policies(env))
        for alpha in [.5,.8,.9,.95,.99]:
            result=budget_dp(env,alpha,B=64)
            choose=budget_policy(result.policy,result.initial_budget,result.fallback)
            oracle=min(discrete_cvar(d,alpha) for d in distributions)
            dist=_cost_distribution(env,choose)
            executed=discrete_cvar(dist,alpha)
            d=cost_distribution(env,choose,60)
            np.testing.assert_allclose(d.pmf,[dist.get(z,0) for z in range(61)],atol=1e-12)
            assert abs(result.value-oracle)<1e-9 and abs(executed-oracle)<1e-9
            exact.append(dict(example=env.name,alpha=alpha,dp_cvar=result.value,
                exhaustive_cvar=oracle,executed_cvar=executed,initial_budget=result.initial_budget,
                B=result.W.shape[1]-1,certified=result.certified,policies_enumerated=len(distributions),seed='not_used'))
            if alpha!=.9: continue
            support=np.array(sorted(dist));probs=np.array([dist[z] for z in support]);n=100000
            rep_seed=20261108
            counts=np.random.default_rng(rep_seed).multinomial(n,probs,size=20000)
            reps=empirical(counts,support,n,alpha);se=float(reps.std(ddof=1))
            for seed in range(10):
                totals=simulate(env,choose,n,np.random.default_rng(seed))
                observed=np.array([(totals==z).sum() for z in support])
                assert observed.sum()==n
                estimate=float(empirical(observed,support,n,alpha))
                mc.append(dict(example=env.name,seed=seed,trajectories=n,cvar_exact=oracle,
                    empirical_cvar=estimate,standard_error=se,bias_estimate=float(reps.mean()-oracle),
                    within_3se=abs(estimate-oracle)<=3*se,replication_seed=rep_seed,replications=20000))
        print(env.name,'exact checks complete; actual C policies simulated',flush=True)
    write_csv(f'results/c_validation_exact_{args.tag}.csv',exact)
    write_csv(f'results/c_validation_mc_{args.tag}.csv',mc)
    print('Exact cases:',len(exact),'MC within 3 SE:',sum(r['within_3se'] for r in mc),'/',len(mc))
    if not all(r['within_3se'] for r in mc):
        raise SystemExit('MC gate failed; inspect the recorded estimates (do not change seeds)')


if __name__=='__main__': main()
