"""python -m experiments.run_e2 --tag v1"""
import argparse
import numpy as np
from ssp.envs.grid import make_grid, in_zone
from ssp.solvers.expected import value_iteration,policy_iteration,linear_programming,dijkstra
from ssp.solvers.budget_dp import budget_dp
from ssp.solvers.dist import budget_policy, cost_distribution
from ssp.solvers.tail_evaluation import evaluate_distribution
from experiments.c_common import output_dirs,write_csv,nominal_route,save_policy
import ssp.figstyle as fs
import matplotlib.pyplot as plt


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--tag',default='v1')
    args=parser.parse_args();output_dirs(args.tag,'e2')
    rows=[]; checks=[]; example=None
    for p in [0,.05,.1,.2,.3]:
        env=make_grid(p=p)
        mean=value_iteration(env);pi=policy_iteration(env);lp=linear_programming(env)
        vi_pi=float(np.max(np.abs(mean.value-pi.value)))
        vi_lp=float(np.max(np.abs(mean.value-lp.value)))
        assert max(vi_pi,vi_lp)<1e-8
        dj=float(np.max(np.abs(mean.value-dijkstra(env)))) if p==0 else ''
        if p==0: assert dj<1e-8
        checks.append(dict(p=p,vi_pi_max_abs=vi_pi,vi_lp_max_abs=vi_lp,
                           dijkstra_max_abs=dj,vi_iterations=mean.iterations,
                           vi_residual=mean.residual,seed='not_used'))
        for alpha in [.5,.8,.9,.95,.99]:
            budget=budget_dp(env,alpha,B=128)
            choose=budget_policy(budget.policy,budget.initial_budget,budget.fallback)
            cutoff=max(160,budget.initial_budget)
            neutral=evaluate_distribution(env,mean.policy,alpha,cutoff)
            risk=evaluate_distribution(env,choose,alpha,cutoff,budget.fallback,budget.initial_budget)
            assert abs(neutral.mean-mean.value[env.start])<1e-8
            assert abs(risk.cvar-budget.value)<1e-8
            # Independently check retained PMF and overflow with D's implementation.
            d=cost_distribution(env,choose,cutoff)
            np.testing.assert_allclose(d.pmf,risk.pmf,atol=1e-13,rtol=0)
            assert abs(d.overflow-risk.overflow)<1e-13
            mean_route=nominal_route(env,lambda s,z:mean.policy[s])
            risk_route=nominal_route(env,choose)
            rows.append(dict(p=p,q=.1,delay=10,p_slow=.2,alpha=alpha,
                mean_optimal=neutral.mean,mean_policy_cvar=neutral.cvar,
                cvar_policy_mean=risk.mean,cvar_optimal=risk.cvar,
                mean_premium=risk.mean-neutral.mean,cvar_reduction=neutral.cvar-risk.cvar,
                initial_budget=budget.initial_budget,B=budget.W.shape[1]-1,
                budget_certified=budget.certified,cutoff=cutoff,
                mean_overflow=neutral.overflow,cvar_overflow=risk.overflow,
                mean_tail_first_moment=neutral.tail_first_moment,
                cvar_tail_first_moment=risk.tail_first_moment,
                nominal_routes_differ=mean_route!=risk_route,
                mean_route_steps=len(mean_route)-1,cvar_route_steps=len(risk_route)-1,
                cvar_dp_abs_error=abs(risk.cvar-budget.value),seed='not_used'))
            if p==.1 and alpha==.9:
                example=(env,neutral,risk,mean_route,risk_route)
                save_policy(env,mean,budget,cutoff,alpha,f'results/e2_policies_{args.tag}.json')
            print(f'E2 p={p:g} alpha={alpha:g}: mean={neutral.mean:.6f}, CVaR={risk.cvar:.6f}',flush=True)
    write_csv(f'results/e2_alpha_sweep_{args.tag}.csv',rows)
    write_csv(f'results/e2_solver_checks_{args.tag}.csv',checks)
    fs.setup('report')
    env,neutral,risk,mroute,rroute=example
    fig,axes=plt.subplots(1,2,figsize=(9,3.8))
    zone=np.array([[in_zone(env.params,r,c) for c in range(10)] for r in range(10)])
    axes[0].imshow(zone,cmap='Greys',vmin=0,vmax=3,origin='upper')
    for route,label,color in [(mroute,'Mean-optimal',fs.C['mean']),(rroute,'CVaR-optimal',fs.C['cvar'])]:
        xy=np.array([env.coords[s] for s in route])
        axes[0].plot(xy[:,1],xy[:,0],'-o',markersize=3,label=label,color=color)
    for s,label in [(env.start,'S'),(env.goal,'G')]:
        r,c=env.coords[s];axes[0].text(c,r-.35,label,ha='center',weight='bold')
    axes[0].set_title('Representative routes (modal outcomes)')
    axes[0].set_xlabel('Column');axes[0].set_ylabel('Row');axes[0].legend(fontsize=8)
    for metric,label,color in [(neutral,'Mean-optimal',fs.C['mean']),(risk,'CVaR-optimal',fs.C['cvar'])]:
        axes[1].step(np.arange(len(metric.pmf)),metric.pmf,where='mid',color=color,label=label)
    axes[1].set_xlim(0,90);axes[1].set_xlabel('Total cost (minutes)');axes[1].set_ylabel('Probability')
    axes[1].set_title('Policy cost distributions');axes[1].legend()
    fig.suptitle('10 x 10 grid: p=0.1, q=0.1, alpha=0.9')
    fig.tight_layout();fs.save(fig,f'figures/f2_routes_{args.tag}');plt.close(fig)
    write_csv(f'results/e2_poster_pmf_{args.tag}.csv',[
        dict(cost=z,mean_policy=neutral.pmf[z],cvar_policy=risk.pmf[z]) for z in range(len(risk.pmf))])
    fig,axes=plt.subplots(1,5,figsize=(15,3.4),sharey=True)
    for ax,p in zip(axes,[0,.05,.1,.2,.3]):
        subset=[r for r in rows if r['p']==p]
        ax.plot([r['cvar_policy_mean'] for r in subset],[r['cvar_optimal'] for r in subset],'-o',color=fs.C['cvar'],label='CVaR-optimal')
        for i,r in enumerate(subset):
            ax.annotate(f"{r['alpha']:g}",(r['cvar_policy_mean'],r['cvar_optimal']),fontsize=7,xytext=(5,2),textcoords='offset points')
        ax.scatter([r['mean_optimal'] for r in subset],[r['mean_policy_cvar'] for r in subset],marker='x',color=fs.C['mean'],label='Mean-optimal')
        ax.set_xlabel('Expected cost');ax.set_title(f'p={p:g}');ax.margins(x=.35)
    axes[0].set_ylabel('CVaR at annotated alpha (minutes)')
    axes[-1].legend(fontsize=7,loc='upper left')
    fig.suptitle('Risk-return comparison (labels are alpha; costs in minutes)')
    fig.tight_layout();fs.save(fig,f'figures/f3_risk_return_{args.tag}');plt.close(fig)


if __name__=='__main__': main()
