"""A 的独立精确验证：读取 B 的环境，不使用 B 的自查计算函数。

请在安装 NumPy 的 Python 环境中运行：python exact.py
"""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
import numbers
import sys
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parent

ALPHA = F(9, 10)
COMMIT = "22675a2933b9011127bddf5c04f9cdbfc0f5f98c"


def probability(value):
    # 环境给出十进制概率，将其恢复为精确分数。
    return F(str(value))


def reachable_pairs(env):
    """列出任意动作下可达的（状态，已花代价）组合；仅适用于无环图。"""
    # 先排除循环；一般有环 SSP 不能使用这种有限路径穷举方法。
    visiting, visited = set(), set()

    def visit(s):
        if s in visiting:
            raise ValueError("精确穷举要求环境为无环图")
        if s in visited:
            return
        visiting.add(s)
        for action in env.outcomes[s]:
            for outcome in action:
                visit(outcome.next_state)
        visiting.remove(s)
        visited.add(s)

    visit(env.start)
    pending, pairs = [(env.start, 0)], set()
    while pending:
        s, spent = pending.pop()
        if (s, spent) in pairs or s == env.goal:
            continue
        pairs.add((s, spent))
        for action in env.outcomes[s]:
            for outcome in action:
                pending.append((outcome.next_state, spent + outcome.cost))
    return sorted(pairs, key=lambda pair: (pair[1], pair[0]))


def exact_distribution(env, policy):
    """用精确分数运算展开所有路径，并在终点按总代价汇总概率。"""
    reachable_pairs(env)
    pending = [(env.start, 0, F(1))]
    dist = defaultdict(F)
    while pending:
        s, spent, mass = pending.pop()
        if s == env.goal:
            dist[spent] += mass
            continue
        action = policy[(s, spent)]
        if not isinstance(action, numbers.Integral) or not 0 <= action < len(env.actions[s]):
            raise ValueError("策略动作编号不合法，不能使用负数或越界编号")
        for o in env.outcomes[s][action]:
            pending.append((o.next_state, spent + o.cost, mass * probability(o.prob)))
    if sum(dist.values()) != 1:
        raise AssertionError("终点概率之和必须为 1")
    return dict(sorted(dist.items()))


def risk_metrics(dist, alpha):
    if not 0 < alpha < 1:
        raise ValueError("置信水平 α 必须位于 (0,1)")
    if not dist or any(not isinstance(z, numbers.Integral) or z < 0 for z in dist):
        raise ValueError("总代价分布必须非空，且支撑为非负整数")
    if any(p < 0 for p in dist.values()) or sum(dist.values()) != 1:
        raise ValueError("概率必须非负且精确相加为 1；请传入精确分数")
    mean = sum(z * p for z, p in dist.items())
    cumulative = F(0)
    for z, p in sorted(dist.items()):
        cumulative += p
        if cumulative >= alpha:
            var = z
            break
    # 独立主计算：最小化 CVaR 的变分表达式。
    # 有限支撑下，分段线性目标至少在一个支撑点处达到最小值。
    objectives = {
        y: F(y) + sum(p * max(z - y, 0) for z, p in dist.items()) / (1 - alpha)
        for y in dist
    }
    cvar = min(objectives.values())
    # 按最坏尾部直接分配概率进行交叉核对，支持只取离散原子的部分概率。
    remaining, tail_sum, allocation = 1 - alpha, F(0), []
    for z, p in sorted(dist.items(), reverse=True):
        take = min(p, remaining)
        if take:
            allocation.append((z, take))
            tail_sum += z * take
            remaining -= take
    if remaining != 0 or tail_sum / (1 - alpha) != cvar:
        raise AssertionError("CVaR 变分计算与直接尾部计算不一致")
    return mean, var, cvar, allocation


def main():
    sys.path.insert(0, str(ROOT / "reference"))
    from ssp.envs.acyclic import example1
    env = example1()
    pairs = reachable_pairs(env)
    results = []
    for choices in itertools.product(*(range(len(env.actions[s])) for s, _ in pairs)):
        policy = dict(zip(pairs, choices))
        dist = exact_distribution(env, policy)
        mean, var, cvar, tail = risk_metrics(dist, ALPHA)
        decisions = [
            {"state": env.state_names[s], "spent": spent, "action": env.actions[s][k]}
            for (s, spent), k in policy.items()
        ]
        label = "".join(d["action"] for d in decisions if d["state"] == "M")
        results.append(dict(policy=label, decisions=decisions, dist=dist,
                            mean=mean, var=var, cvar=cvar, tail=tail))
    results.sort(key=lambda r: r["policy"])
    if len(results) != 4:
        raise AssertionError("例子 1 应当恰好有四种确定性策略")
    best = min(results, key=lambda r: r["cvar"])
    stationary = [r for r in results if len(set(r["policy"])) == 1]
    best_stationary = min(stationary, key=lambda r: r["cvar"])
    # 独立检查最优策略的非唯一阈值，不使用 B 的参考常量。
    # 本例支撑有限，搜索到最大支撑值即可覆盖最优阈值。
    dist = best["dist"]
    budgets = [y for y in range(max(dist) + 1)
               if F(y) + sum(p * max(z-y, 0) for z, p in dist.items()) / (1-ALPHA)
               == best["cvar"]]
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    with (out / "example1_summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["policy_after_1_after_20", "mean", "var_0.9", "cvar_0.9",
                         "cvar_exact", "probability_sum"])
        for r in results:
            writer.writerow([r["policy"], float(r["mean"]), r["var"],
                             float(r["cvar"]), str(r["cvar"]), str(sum(r["dist"].values()))])
    with (out / "example1_distributions.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["policy", "total_cost", "probability_exact", "probability"])
        for r in results:
            for z, p in r["dist"].items():
                writer.writerow([r["policy"], z, str(p), float(p)])
    hashes = {str(p.relative_to(ROOT / "reference")): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted((ROOT / "reference").rglob("*.py"))}
    payload = {"source_commit": COMMIT, "source_sha256": hashes,
               "alpha": str(ALPHA), "arithmetic": "将环境中的十进制概率转换为 fractions.Fraction 精确分数",
               "best_policy": best["policy"], "best_cvar": str(best["cvar"]),
               "best_stationary_policy": best_stationary["policy"],
               "improvement": str(best_stationary["cvar"] - best["cvar"]),
               "optimal_integer_thresholds": budgets, "policies": results,
               "scope": "例子 1 的确定性（状态，已花代价）策略精确穷举；本脚本不验收预算求解器或蒙特卡洛模拟"}
    (out / "example1_details.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    lines = ["# 例子 1：A 的独立精确验证", "",
             f"环境快照版本：`{COMMIT}`。α = 0.9；概率以分数精确计算，无随机抽样。", "",
             "策略名第一位表示第一段花 1 分钟后的动作，第二位表示花 20 分钟后的动作。", "",
             "| 策略 | 总耗时分布：分钟（概率） | 均值 | VaR₀.₉ | CVaR₀.₉ |",
             "|---|---|---:|---:|---:|"]
    for r in results:
        distribution = "、".join(f"{z}（{float(p):.0%}）" for z, p in r["dist"].items())
        lines.append(f"| {r['policy']} | {distribution} | {float(r['mean']):.2f} | {r['var']} | {float(r['cvar']):.1f} |")
    lines += ["", "## 最坏 10% 的组成", ""]
    for r in results:
        terms = " + ".join(f"{z}×{float(p):.0%}" for z, p in r["tail"])
        lines.append(f"- {r['policy']}：({terms}) / 10% = {float(r['cvar']):.1f}。")
    lines += ["", f"最优策略为 {best['policy']}；相对只看位置的最优策略 {best_stationary['policy']}，CVaR 降低 {float(best_stationary['cvar']-best['cvar']):.1f} 分钟。",
              f"最优整数起始阈值为 {budgets[0]}–{budgets[-1]}，因此不能要求求解器必须返回 7。", "",
              "## 本次检查范围", "",
              "读取 B 的环境定义；没有调用 B 的 `_cost_distribution`、`_cvar` 或 `EXAMPLE1_REFERENCE`。",
              "程序枚举可达的（状态，已花代价）决策组合，列举路径，检查概率总和，并用 CVaR 变分式与直接尾部积分相互核对。",
              "这里只穷举确定性策略；例子 1 中它们涵盖所有可观察历史的确定性选择。随机混合不会降低其最小 CVaR：混合分布的 CVaR 不小于混合成分 CVaR 的加权平均（由变分式对阈值取下确界可得）。", "",
              "尚未接入 C 的预算 DP、D 的分布程序，也未执行 10 万条轨迹模拟；本结果不表示完整 E0 已通过。", ""]
    (out / "例子1验证结果.md").write_text("\n".join(lines), encoding="utf-8")
    print("策略    均值    风险价值 VaR₀.₉    条件风险价值 CVaR₀.₉")
    for r in results:
        print(f"{r['policy']:6} {float(r['mean']):5.2f} {r['var']:8} {float(r['cvar']):9.1f}")
    print(f"通过：{len(results)} 种策略；概率总和为 1；两种精确 CVaR 算法一致")
    print(f"最优策略： {best['policy']}；最优整数阈值范围：{budgets[0]}..{budgets[-1]}")
    print(f"结果目录：{out}")


if __name__ == "__main__":
    main()
