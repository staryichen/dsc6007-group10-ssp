"""供 B 与 A 讨论的本地候选环境，未修改远程共享环境。"""
from pathlib import Path
from fractions import Fraction as F
import itertools
import json
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "reference"))
from ssp.mdp import SSP, make_outcomes
from ssp.solvers.dist import cost_distribution
import numpy as np

import exact as oracle


def candidate():
    # 状态编号：S=0、A=1、B=2、M=3、G=4。在 S 处，下一状态和代价均为随机变量。
    return SSP(name="example2_candidate", state_names=["S", "A", "B", "M", "G"],
               start=0, goal=4,
               actions=[["go"], ["continue"], ["continue"], ["X", "Y"], []],
               outcomes=[
                   [make_outcomes([(1, 1, .9), (2, 10, .1)])],
                   [make_outcomes([(3, 1, 1.)])],
                   [make_outcomes([(3, 10, .5), (3, 11, .5)])],
                   [make_outcomes([(4, 1, .9), (4, 30, .1)]), make_outcomes([(4, 6, 1.)])],
                   []])


def main():
    env = candidate()
    pairs = oracle.reachable_pairs(env)
    rows = []
    for choices in itertools.product(*(range(len(env.actions[s])) for s, _ in pairs)):
        policy = dict(zip(pairs, choices))
        dist = oracle.exact_distribution(env, policy)
        mean, var, cvar, tail = oracle.risk_metrics(dist, F(9, 10))
        label = "".join(env.actions[3][policy[3, z]] for z in (2, 20, 21))
        # 在完整支撑上核对 D 的分布，而不只是比较风险指标。
        d = cost_distribution(env, lambda s,z: policy[s,z], z_max=51)
        expected = np.array([float(dist.get(z, 0)) for z in range(52)])
        if d.overflow != 0 or not np.allclose(d.pmf, expected, atol=1e-12, rtol=0):
            raise AssertionError(label)
        rows.append(dict(policy=label, distribution=dist, mean=mean, var=var, cvar=cvar, tail=tail))
    best = min(rows, key=lambda r:r["cvar"])
    stationary = min((r for r in rows if len(set(r["policy"])) == 1), key=lambda r:r["cvar"])
    budgets = [y for y in range(52) if F(y)+sum(p*max(z-y,0) for z,p in best["distribution"].items())/F(1,10)==best["cvar"]]
    payload = dict(status="本地候选环境，尚未与 B 对齐", pairs=pairs,
                   number_of_policies=len(rows), policies=rows, best=best["policy"],
                   best_stationary=stationary["policy"], optimal_integer_thresholds=budgets,
                   d_reference_commit="22675a2933b9011127bddf5c04f9cdbfc0f5f98c",
                   scope="精确穷举与 D 的有限支撑分布核对；不包含 C 求解器验收或模拟")
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "example2_candidates.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2,default=str)+"\n")
    print(env.describe().replace("start=", "起点=").replace("goal=", "终点=")
          .replace("cost", "代价").replace("go ", "前进 ").replace("continue", "继续"))
    print("M 处的决策依次对应已花代价（2、20、21）")
    for r in rows:
        print(r["policy"], "均值",float(r["mean"]),"条件风险价值 CVaR",float(r["cvar"]))
    print("最优策略：",best["policy"],"总代价分布",best["distribution"],"最优整数阈值",budgets)
    print("通过：八种策略及 D 的概率质量函数一致；最多三次转移，总耗时不超过 51")


if __name__ == "__main__":
    main()
