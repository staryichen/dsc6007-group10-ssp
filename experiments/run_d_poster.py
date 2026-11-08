"""Recompute and verify poster distributions from C's exported policies."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from ssp.envs.grid import make_grid
from ssp.solvers.dist import budget_policy, cost_distribution
from ssp.solvers.expected import value_iteration
from ssp.solvers.budget_dp import budget_dp
from ssp.solvers.tail_evaluation import evaluate_distribution
from experiments.c_common import output_dirs, write_csv
import ssp.figstyle as fs
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--policies', default='results/e2_policies_v3.json')
    parser.add_argument('--tag', default='v1')
    args = parser.parse_args()
    output_dirs(args.tag, 'd_poster')
    source = Path(args.policies)
    data = json.loads(source.read_text(encoding='utf-8'))
    params = dict(data['grid'])
    for key in ('start', 'goal', 'zone_rows', 'zone_cols'):
        if key in params:
            params[key] = tuple(params[key])
    env = make_grid(**params)
    alpha, y = data['alpha'], data['initial_budget']
    mean_policy = np.asarray(data['mean_policy'])
    table = np.asarray(data['budget_policy'])
    # JSON's legacy schema omits fallback; column zero contains C's actual fallback.
    fallback = np.asarray(data.get('fallback', table[:, 0]))
    choose = budget_policy(table, y, fallback)
    cutoff = max(data.get('cutoff', 160), y)
    vi = value_iteration(env)
    dp = budget_dp(env, alpha, B=table.shape[1]-1)
    if not dp.certified:
        raise AssertionError('budget search not certified')
    pairs = [('Mean-optimal', mean_policy, None, 0), ('CVaR-optimal', choose, fallback, y)]
    evaluations, rows, checks = [], [], []
    for label, policy, tail_policy, after in pairs:
        evaluated = evaluate_distribution(env, policy, alpha, cutoff, tail_policy, after)
        larger = evaluate_distribution(env, policy, alpha, 2*cutoff, tail_policy, after)
        independent = cost_distribution(env, policy, cutoff)
        np.testing.assert_allclose(independent.pmf, evaluated.pmf, rtol=0, atol=1e-13)
        assert abs(independent.overflow-evaluated.overflow) < 1e-13
        np.testing.assert_allclose([evaluated.mean, evaluated.cvar], [larger.mean, larger.cvar], rtol=0, atol=1e-8)
        assert evaluated.var == larger.var
        objective = vi.value[env.start] if label == 'Mean-optimal' else dp.value
        observed = evaluated.mean if label == 'Mean-optimal' else evaluated.cvar
        assert abs(observed-objective) < 1e-8
        saved = data['mean_value'][env.start] if label == 'Mean-optimal' else data['cvar']
        assert abs(observed-saved) < 1e-8
        evaluations.append(evaluated)
        rows.append(dict(policy=label, alpha=alpha, mean=evaluated.mean, var=evaluated.var,
            cvar=evaluated.cvar, cutoff=cutoff, overflow=evaluated.overflow,
            tail_first_moment=evaluated.tail_first_moment, initial_budget=y if after else '',
            grid=json.dumps(params), seed='not_used'))
        checks.append(dict(policy=label, solver_abs_error=abs(observed-objective),
            saved_objective_abs_error=abs(observed-saved),
            doubled_cutoff_mean_error=abs(evaluated.mean-larger.mean),
            doubled_cutoff_cvar_error=abs(evaluated.cvar-larger.cvar),
            probability_sum=float(evaluated.pmf.sum()+evaluated.overflow),
            pmf_max_error=float(np.max(np.abs(independent.pmf-evaluated.pmf)))))
    stem = 'd_poster_'+args.tag
    write_csv(f'results/{stem}_metrics.csv', rows)
    write_csv(f'results/{stem}_checks.csv', checks)
    write_csv(f'results/{stem}_pmf.csv', [dict(cost=z, mean_policy=evaluations[0].pmf[z],
        cvar_policy=evaluations[1].pmf[z]) for z in range(cutoff+1)])
    fs.setup('poster')
    fig, axes = plt.subplots(1,2,figsize=(14,5.8))
    # Zoom is explicitly a display choice; CSV retains the entire computed PMF.
    xmax = min(cutoff, max(int(np.searchsorted(np.cumsum(e.pmf), .9999)) for e in evaluations)+5)
    for label, e, color in zip(['Mean-optimal','CVaR-optimal'],evaluations,[fs.C['mean'],fs.C['cvar']]):
        z = np.arange(cutoff+1)
        axes[0].step(z,e.pmf,where='mid',color=color,label=label)
        survival = np.cumsum(e.pmf[::-1])[::-1]-e.pmf+e.overflow
        axes[1].step(z,survival,where='post',color=color,label=label)
    axes[0].set_ylabel('Probability'); axes[0].set_title('Total-cost distribution')
    axes[1].set_ylabel('P(total cost > x)'); axes[1].set_title('Tail probability')
    axes[1].set_yscale('log'); axes[1].set_ylim(1e-5,1.05)
    for ax in axes:
        ax.set_xlim(0,xmax); ax.set_xlabel('Total cost (minutes)'); ax.legend(fontsize=13)
    fig.suptitle(f"10 × 10 grid  |  slip p={params['p']}  |  delay q={params['q']}  |  alpha={alpha}",fontsize=20)
    mean, risk = evaluations
    footer = (f'Mean-optimal: mean {mean.mean:.2f}, CVaR {mean.cvar:.2f}    |    '
              f'CVaR-optimal: mean {risk.mean:.2f}, CVaR {risk.cvar:.2f}')
    fig.text(.5,.025,footer,ha='center',fontsize=14)
    fig.tight_layout(rect=(0,.07,1,.95))
    fs.save(fig,f'figures/{stem}'); plt.close(fig)
    manifest = dict(source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        cutoff=cutoff, display_xmax=xmax, checks=checks, budget_certified=bool(dp.certified),
        mean_premium_percent=100*(risk.mean/mean.mean-1),cvar_reduction_percent=100*(1-risk.cvar/mean.cvar))
    Path(f'results/{stem}_verification.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(metrics=rows,verification=manifest),indent=2))


if __name__ == '__main__':
    main()
