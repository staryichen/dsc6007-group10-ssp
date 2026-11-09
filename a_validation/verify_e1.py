"""A 对 D 的例子 1 分布及 E1 三个玩具例子进行独立核对。"""
from __future__ import annotations

import csv
import json
import sys
from fractions import Fraction as F
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "reference"))
from ssp.envs.acyclic import example1
from ssp.envs.toy import all_toys
from ssp.solvers.dist import cost_distribution, budget_policy
from ssp.risk import risk_metrics as d_metrics

# 复用 A 已核对的精确分数计算器，不调用 D 或 B 的自查辅助函数。
import exact as oracle

D_COMMIT = "22675a2933b9011127bddf5c04f9cdbfc0f5f98c"
ALPHA = F(9, 10)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def compare(env, choose, label, cutoffs):
    policy = {(s, spent): choose(s, spent) for s, spent in oracle.reachable_pairs(env)}
    exact = oracle.exact_distribution(env, policy)
    mean, var, cvar, _ = oracle.risk_metrics(exact, ALPHA)
    checks = []
    for cutoff in cutoffs:
        observed = cost_distribution(env, choose, cutoff)
        expected = np.array([float(exact.get(z, 0)) for z in range(cutoff + 1)])
        max_error = float(np.max(np.abs(expected - observed.pmf)))
        expected_overflow = float(sum(p for z, p in exact.items() if z > cutoff))
        require(max_error < 1e-12, f"{label}：概率质量函数不一致，截断上限为 {cutoff}")
        require(abs(observed.overflow - expected_overflow) < 1e-12,
                f"{label}：溢出概率不一致")
        if expected_overflow == 0:
            metrics = d_metrics(observed.pmf, float(ALPHA), observed.overflow)
            for key, expected_value in [("mean", mean), ("var", var), ("cvar", cvar)]:
                require(abs(metrics[key] - float(expected_value)) < 1e-10,
                        f"{label}：指标 {key} 不一致")
        else:
            try:
                d_metrics(observed.pmf, float(ALPHA), observed.overflow)
            except ValueError:
                pass
            else:
                raise AssertionError("截断分布不应直接给出精确 CVaR")
        checks.append(dict(label=label, cutoff=cutoff, max_pmf_error=max_error,
                           overflow=observed.overflow, status="PASS"))
    return exact, (mean, var, cvar), checks


def main():
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    checks = []
    env = example1()
    for a1, a20 in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        def choose(s, spent, a1=a1, a20=a20):
            return 0 if s == env.start else (a1 if spent == 1 else a20)
        label = "XY"[a1] + "XY"[a20]
        _, _, rows = compare(env, choose, label, [0, 6, 7, 20, 21, 49, 50])
        checks.extend(rows)
    # 手工构造已知策略；这里只检查适配器，不是动态规划求解器验收。
    table = np.zeros((env.n_states, 8), dtype=int)
    table[1, 6] = 1
    adapted = budget_policy(table, 7, np.array([0, 0, -1]))
    _, metrics, rows = compare(env, adapted, "manual_YX_budget_adapter", [50])
    require(metrics[2] == F(239, 10), "手工 YX 策略的 CVaR 应为 23.9")
    checks.extend(rows)

    # 使用独立手算的预期值，不依赖 B 的参考常量或 D 的指标函数。
    expected = {
        ("toy_two_route", "bridge"): (F(109, 10), F(88209, 100), 1, F(100)),
        ("toy_two_route", "detour"): (F(12), F(0), 12, F(12)),
        ("toy_same_mean", "A"): (F(11), F(9), 10, F(20)),
        ("toy_same_mean", "B"): (F(11), F(0), 11, F(11)),
        ("toy_occasional_fast", "C"): (F(10), F(9), 11, F(11)),
        ("toy_occasional_fast", "B"): (F(11), F(0), 11, F(11)),
    }
    toys = []
    for toy in all_toys():
        for k, name in enumerate(toy.actions[toy.start]):
            choose = lambda s, spent, k=k: k
            dist, (mean, var, cvar), rows = compare(
                toy, choose, f"{toy.name}/{name}", [max(o.cost for o in toy.outcomes[toy.start][k])])
            checks.extend(rows)
            variance = sum(p * (z - mean)**2 for z, p in dist.items())
            require((mean, variance, var, cvar) == expected[(toy.name, name)],
                    f"以下动作与手算结果不一致：{toy.name}/{name}")
            toys.append(dict(environment=toy.name, action=name, distribution=dist,
                             mean=mean, variance=variance, var=var, cvar=cvar))
    with (out / "e1_toy_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["environment", "action", "mean", "variance", "var_0.9", "cvar_0.9"])
        for r in toys:
            w.writerow([r["environment"], r["action"], float(r["mean"]),
                        float(r["variance"]), r["var"], float(r["cvar"])])
    with (out / "e1_toy_distributions.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["environment", "action", "cost", "probability_exact"])
        for r in toys:
            for z, p in r["distribution"].items():
                w.writerow([r["environment"], r["action"], z, str(p)])
    (out / "verification.json").write_text(json.dumps(
        dict(d_commit=D_COMMIT, alpha=str(ALPHA), distribution_checks=checks,
             toy_results=toys, sampling=False, c_budget_dp_checked=False),
        ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    lines = ["# E1 玩具例子与 D 分布程序的独立核对", "",
             f"检查 D 的固定版本 `{D_COMMIT}`；α = 0.9。", "",
             "## E1 数字表", "",
             "| 例子 | 动作 | 总耗时（概率） | 均值 | 方差 | VaR₀.₉ | CVaR₀.₉ |",
             "|---|---|---|---:|---:|---:|---:|"]
    for r in toys:
        dist_text = "、".join(f"{z}（{float(p):.0%}）" for z, p in r["distribution"].items())
        lines.append(f"| {r['environment']} | {r['action']} | {dist_text} | {float(r['mean']):g} | {float(r['variance']):g} | {r['var']} | {float(r['cvar']):g} |")
    lines += ["", "## 可支持的解释", "",
              "1. 桥与绕行：平均最优选桥（10.9 < 12），CVaR₀.₉ 最优选绕行（12 < 100）。多花 1.1 分钟平均耗时，换取最坏十分位均值降低 88 分钟。",
              "2. 相同均值：A、B 均值都是 11，但 CVaR 分别为 20、11；均值无法区分两者的尾部。",
              "3. 偶尔特别快：C 比恒定 11 分钟的 B 有更大的方差，但 CVaR 都是 11。这说明增加方差未必增加该水平的 CVaR。",
              "注意：若目标是均值 + λ×方差，C 的目标为 10+9λ，B 为 11；只有 λ>1/9 才严格偏好 B，λ=1/9 时并列。不能笼统说任何方差惩罚都会选 B。", "",
              "## D 程序联调结果", "",
              f"共 {len(checks)} 项分布/截断检查通过：例子 1 的四种策略，各检查 7 个截断位置；手工 YX 预算策略适配器 1 项；E1 六个动作各 1 项。",
              "逐项与 A 的精确分数路径枚举比较，覆盖完整 PMF、截断概率、均值、VaR 和 CVaR。截断分布调用风险函数时正确拒绝给出精确指标。",
              "所有 E1 数字还与独立手算预期值核对；没有使用 B/D 的参考常量。", "",
              "## 进度与边界", "",
              "本文件只记录固定 D 提交的小例子接口检查，不代表仓库当前分支或 PR 进度。",
              "本次只核对 D 的例子 1 和 E1，有环网格的截断误差及最终最优策略尚未验收。",
              "本脚本的适配器使用手工已知策略，不验收 C 的预算 DP；整个 A 工作包的后续模拟及例子 2 见本目录 results 和 README。",
              "B 的 toy.py 中关于方差惩罚的注释需要采用上述 λ 条件来解释；本地参考副本保持原样。", ""]
    (out / "核对结果.md").write_text("\n".join(lines), encoding="utf-8")
    for r in toys:
        print(f"{r['environment']}/{r['action']}：均值={float(r['mean']):g}，方差={float(r['variance']):g}，风险价值 VaR={r['var']}，条件风险价值 CVaR={float(r['cvar']):g}")
    print(f"通过：{len(checks)} 项分布与截断案例；六个玩具动作的精确手算值均一致")
    print("本脚本尚未核对 C 的预算动态规划、蒙特卡洛模拟或例子 2。")


if __name__ == "__main__":
    main()
