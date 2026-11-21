"""E3：参数相图 —— 均值最优与 CVaR 最优在什么条件下分叉。

扫描打滑率 p 与拥堵率 q（5×5），对每一格分别求均值最优与 CVaR 最优策略，
用前推分布读出各自的均值与 CVaR，比较两策略的典型轨迹是否相同。

同时输出 α 敏感度图：直接读 results/e2_alpha_sweep_v3.csv，不重复计算。

用法：python -m experiments.run_e3_phase
输出：results/e3_phase_v1.csv，figures/f4_phase.{png,pdf}，figures/f_alpha_gain.{png,pdf}
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import matplotlib.pyplot as plt

import ssp.figstyle as fs
from ssp.envs.grid import make_grid
from ssp.risk import risk_metrics
from ssp.solvers import budget_dp, dist, expected

PS = [0.0, 0.05, 0.1, 0.2, 0.3]
QS = [0.0, 0.05, 0.1, 0.2, 0.3]
ALPHA = 0.9
Z_MAX = 4000
B_CAP = 256
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"


def modal_route(env, choose, limit=20000):
    """按最可能的联合结果走出的轨迹；仅用于比较两条策略是否走同一条路。"""
    s, z, route = env.start, 0, [env.start]
    seen = set()
    for _ in range(limit):
        if s == env.goal:
            return route
        if (s, z) in seen:
            return None
        seen.add((s, z))
        a = choose(s, z)
        o = max(env.outcomes[s][a], key=lambda o: o.prob)
        s, z = o.next_state, z + o.cost
        route.append(s)
    return None


def sweep():
    rows = []
    for p in PS:
        for q in QS:
            env = make_grid(p=p, q=q, delay=10, p_slow=0.2)
            mean = expected.value_iteration(env)
            bud = budget_dp.budget_dp(env, alpha=ALPHA, B=B_CAP)
            budget = bud.initial_budget

            pol_mean = lambda s, z: int(mean.policy[s])
            pol_cvar = dist.budget_policy(bud.policy, budget, mean.policy)

            d_mean = dist.cost_distribution(env, pol_mean, z_max=Z_MAX)
            d_cvar = dist.cost_distribution(env, pol_cvar, z_max=Z_MAX)
            # 浮点累加会留下 1e-314 量级的残渣，按零处理
            ov_mean = 0.0 if d_mean.overflow < 1e-12 else d_mean.overflow
            ov_cvar = 0.0 if d_cvar.overflow < 1e-12 else d_cvar.overflow
            m_mean = risk_metrics(d_mean.pmf, ALPHA, ov_mean)
            m_cvar = risk_metrics(d_cvar.pmf, ALPHA, ov_cvar)

            r_mean = modal_route(env, pol_mean)
            r_cvar = modal_route(env, pol_cvar)
            rows.append(dict(
                p=p, q=q,
                mean_opt_mean=round(m_mean["mean"], 3),
                mean_opt_cvar=round(m_mean["cvar"], 3),
                cvar_opt_mean=round(m_cvar["mean"], 3),
                cvar_opt_cvar=round(m_cvar["cvar"], 3),
                d_mean=round(m_cvar["mean"] - m_mean["mean"], 3),
                d_cvar=round(m_mean["cvar"] - m_cvar["cvar"], 3),
                same_route=(r_mean is not None and r_mean == r_cvar),
            ))
    return rows


def plot_phase(rows):
    grid = np.array([[next(r["d_cvar"] for r in rows if r["p"] == p and r["q"] == q) for q in QS] for p in PS])

    fs.setup("slides")
    fig, ax = plt.subplots(figsize=(6.2, 4.8))
    im = ax.imshow(grid, origin="lower", cmap="Blues", aspect="auto")
    for i in range(len(PS)):
        for j in range(len(QS)):
            ax.text(j, i, f"{grid[i, j]:.1f}", ha="center", va="center",
                    fontsize=11, color="black" if grid[i, j] < grid.max() * 0.6 else "white")
            if grid[i, j] >= 1.0:
                ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, ec="#D62728", lw=2))
    ax.set_xticks(range(len(QS)), [f"{q:g}" for q in QS])
    ax.set_yticks(range(len(PS)), [f"{p:g}" for p in PS])
    ax.set_xlabel("jam probability q")
    ax.set_ylabel("slip probability p")
    ax.set_title("CVaR gain over the mean-optimal policy (min)\nred box: at least one minute", fontsize=12)
    fig.colorbar(im, ax=ax, shrink=0.85, label="CVaR improvement (min)")
    fig.tight_layout()
    fs.save(fig, str(FIGURES / "f4_phase"))


def plot_alpha():
    path = RESULTS / "e2_alpha_sweep_v3.csv"
    if not path.exists():
        print("skip alpha figure: missing", path.name)
        return
    series = defaultdict(list)
    for r in csv.DictReader(path.open(encoding="utf-8")):
        series[float(r["p"])].append((float(r["alpha"]), float(r["cvar_reduction"])))

    fs.setup("slides")
    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    for p in sorted(series):
        pts = sorted(series[p])
        ax.plot([a for a, _ in pts], [g for _, g in pts], marker="o", label=f"slip p = {p:g}")
    ax.set_xlabel(r"confidence level $\alpha$")
    ax.set_ylabel("CVaR reduction (min)")
    ax.set_title("The more we care about the tail, the more the two objectives differ", fontsize=12)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=11, frameon=False)
    fig.tight_layout()
    fs.save(fig, str(FIGURES / "f_alpha_gain"))


def main():
    RESULTS.mkdir(exist_ok=True)
    FIGURES.mkdir(exist_ok=True)
    rows = sweep()
    out = RESULTS / "e3_phase_v1.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    plot_phase(rows)
    plot_alpha()
    print("wrote", out)
    for r in rows:
        print(f"p={r['p']:.2f} q={r['q']:.2f} dmean={r['d_mean']:+.2f} dcvar={r['d_cvar']:+.2f} same={r['same_route']}")


if __name__ == "__main__":
    main()
