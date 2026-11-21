"""Run from repo root: python -m experiments.run_dist_demo --tag v1.

Optional C handoff: --policy-json path.json (schema in docs/D_distribution.md).
"""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from ssp.solvers.dist import cost_distribution, budget_policy
from ssp.risk import risk_metrics
from ssp.envs.toy import two_route
from ssp.envs.acyclic import example1
from ssp.envs.grid import make_grid, UP, DOWN, RIGHT
import ssp.figstyle as fs
import matplotlib.pyplot as plt


def export(env, policies, stem, title, alpha, cutoff):
    results = [(name, cost_distribution(env, pi, cutoff)) for name, pi in policies]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    rows = []
    for (name, result), color in zip(results, [fs.C['mean'], fs.C['cvar']]):
        p = result.pmf
        # Never turn an unbounded unknown residual into a claimed exact CVaR.
        metrics = risk_metrics(p, alpha, result.overflow) if result.overflow == 0 else dict(mean='', var='', cvar='')
        rows.append(dict(policy=name, alpha=alpha, cutoff=cutoff, overflow=result.overflow,
                         **metrics, parameters=json.dumps(env.params, sort_keys=True)))
        z = np.arange(len(p))
        axes[0].step(z, p, where='mid', label=name, color=color)
        survival = np.maximum(0, 1-np.cumsum(p))
        axes[1].step(z, survival, where='post', label=name, color=color)
    last = max(int(np.flatnonzero(r.pmf)[-1]) for _, r in results if np.any(r.pmf))
    for ax in axes:
        ax.set_xlim(0, last+2)
        ax.set_xlabel('Total cost (minutes)')
        ax.legend(fontsize=10)
    axes[0].set_ylabel('Probability')
    axes[1].set_ylabel('Probability of exceeding cost')
    fig.suptitle(title)
    fig.tight_layout()
    fs.save(fig, str(Path('figures')/stem))
    plt.close(fig)
    with (Path('results')/(stem+'_metrics.csv')).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    with (Path('results')/(stem+'_pmf.csv')).open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['cost']+[name for name, _ in results])
        w.writerows([z]+[r.pmf[z] for _, r in results] for z in range(cutoff+1))
    print(stem, rows)


def verify():
    toy = two_route()
    bridge = cost_distribution(toy, [0, -1], 100)
    assert np.isclose(bridge.pmf[1], .9) and np.isclose(bridge.pmf[100], .1)
    assert np.isclose(risk_metrics(bridge.pmf)['cvar'], 100)
    cut = cost_distribution(toy, [0, -1], 10)
    assert np.isclose(cut.overflow, .1)
    try:
        risk_metrics(cut.pmf, overflow=cut.overflow)
    except ValueError:
        pass
    else:
        raise AssertionError('truncated metrics must be rejected')
    for a1, a20, expected in [(0,0,32.9),(0,1,30.5),(1,0,23.9),(1,1,26.)]:
        d = cost_distribution(example1(), lambda s,z: 0 if s == 0 else (a1 if z == 1 else a20), 60)
        assert np.isclose(risk_metrics(d.pmf)['cvar'], expected)
    table = np.zeros((3,8), dtype=int); table[1,6] = 1
    adapted = cost_distribution(example1(), budget_policy(table,7,[0,0,-1]),60)
    assert np.isclose(risk_metrics(adapted.pmf)['cvar'],23.9)
    try:
        cost_distribution(toy, [-1,-1])
    except ValueError:
        pass
    else:
        raise AssertionError('negative actions must be rejected')
    # Cyclic proper policy: geometric cost, P(Z=k)=2^-k.
    from ssp.mdp import SSP, Outcome
    loop = SSP('loop',['S','G'],0,1,[['go'],[]],[[ (Outcome(0,1,.5),Outcome(1,1,.5)) ],[]])
    d = cost_distribution(loop,[0,-1],10)
    assert np.allclose(d.pmf[1:], .5**np.arange(1,11))
    assert np.isclose(d.overflow,.5**10)
    print('PASS: toy, all four history policies, budget adapter, truncation, invalid action, cyclic propagation')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tag', default='v1')
    parser.add_argument('--policy-json')
    args = parser.parse_args()
    for folder in ['figures','results']:
        Path(folder).mkdir(exist_ok=True)
    if any(Path('figures').glob('*_'+args.tag+'.png')):
        raise SystemExit('Tag already exists; choose a new --tag to preserve figures')
    verify()
    fs.setup('report')
    export(two_route(), [('Bridge',[0,-1]),('Detour',[1,-1])], 'd_toy_'+args.tag,
           'Toy: mean-optimal bridge vs risk-optimal detour', .9, 100)
    grid = make_grid(p=0)
    def straight(s,z):
        r,c = grid.coords[s]
        return DOWN if r<4 else UP if r>4 else RIGHT
    def around(s,z):
        r,c = grid.coords[s]
        return UP if c<7 and r>1 else RIGHT if c<7 else DOWN if r<4 else UP if r>4 else RIGHT
    for pi, mean, cvar in [(straight,15.12,31.71),(around,18.,20.84)]:
        d = cost_distribution(grid,pi,400)
        m = risk_metrics(d.pmf)
        assert np.isclose(m['mean'],mean) and abs(m['cvar']-cvar)<.005
    export(grid,[('Fixed straight route',straight),('Fixed detour',around)],
           'd_grid_fixed_'+args.tag, 'Fixed routes only (p=0, q=0.1; not solver optima)',.9,400)
    if args.policy_json:
        data = json.loads(Path(args.policy_json).read_text(encoding='utf-8'))
        params = dict(data['grid'])
        for key in ('start', 'goal', 'zone_rows', 'zone_cols'):
            if key in params:
                params[key] = tuple(params[key])
        env = make_grid(**params)
        fallback = data.get('fallback', np.asarray(data['budget_policy'])[:, 0])
        pi = budget_policy(data['budget_policy'],data['initial_budget'],fallback)
        export(env,[('Mean-optimal',data['mean_policy']),('CVaR-optimal',pi)],
               'd_grid_solver_'+args.tag,'Solver policies (values require cross-check)',
               data['alpha'],data.get('cutoff',2000))


if __name__ == '__main__':
    main()
