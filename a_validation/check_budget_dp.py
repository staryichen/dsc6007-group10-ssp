"""A 使用的无环图精确参考动态规划；不是 C 的正式求解器。"""
from pathlib import Path
from fractions import Fraction as F
import csv
import itertools
import json
import numbers
import sys

ROOT = Path(__file__).resolve().parent
from example2 import candidate, oracle, np
from ssp.envs.acyclic import example1


def reference_dp(env, bound, alpha):
    """使用精确分数运算处理有限无环图，按预算递推，无需穷举策略。"""
    if not isinstance(bound, numbers.Integral) or bound < 0:
        raise ValueError("预算上限必须是非负整数")
    if not 0 < alpha < 1:
        raise ValueError("置信水平 α 必须位于 (0,1)")
    mean, fallback, visiting = {env.goal:F(0)}, {}, set()
    maximum_cost = {env.goal:0}
    def solve_mean(s):
        if s in mean:
            return mean[s]
        if s in visiting:
            raise ValueError("A 的参考求解器只支持无环环境，检测到循环")
        visiting.add(s)
        values = [sum(F(str(o.prob))*(o.cost+solve_mean(o.next_state)) for o in outs)
                  for outs in env.outcomes[s]]
        fallback[s] = min(range(len(values)),key=values.__getitem__)
        mean[s] = min(values)
        maximum_cost[s] = max(o.cost + maximum_cost[o.next_state]
                              for outs in env.outcomes[s] for o in outs)
        visiting.remove(s)
        return mean[s]
    for s in range(env.n_states):
        solve_mean(s)
    if bound < maximum_cost[env.start]:
        raise ValueError("本地参考验证要求预算上限覆盖起点的完整代价支撑，不能把受限搜索当全局最优")
    W, actions = {}, {}
    def value(s,b):
        if s==env.goal:
            return F(max(-b,0))
        return mean[s]-b if b<=0 else W[s,b]
    for b in range(1,bound+1):
        for s in range(env.n_states):
            if s==env.goal:
                continue
            values = [sum(F(str(o.prob))*value(o.next_state,b-o.cost) for o in outs)
                      for outs in env.outcomes[s]]
            actions[s,b] = min(range(len(values)),key=values.__getitem__)
            W[s,b] = min(values)
    objectives = {y:F(y)+value(env.start,y)/(1-alpha) for y in range(bound+1)}
    optimum = min(objectives.values())
    thresholds = [y for y,v in objectives.items() if v==optimum]
    y = thresholds[0]
    def policy(s,spent):
        b=y-spent
        return fallback[s] if b<=0 else actions[s,b]
    return mean, optimum, thresholds, policy


def distribution_of_policy(env, choose):
    mapping={(s,z):choose(s,z) for s,z in oracle.reachable_pairs(env)}
    return oracle.exact_distribution(env,mapping)


def exhaustive_optimum(env,alpha):
    pairs=oracle.reachable_pairs(env)
    values=[]
    for choices in itertools.product(*(range(len(env.actions[s])) for s,_ in pairs)):
        dist=oracle.exact_distribution(env,dict(zip(pairs,choices)))
        values.append(oracle.risk_metrics(dist,alpha)[2])
    return min(values)


def empirical_cvar_from_counts(counts, support, n):
    probabilities=counts/n
    # 在有限支撑的各个阈值处计算变分目标，取其中的最小值。
    values=[y+(probabilities*np.maximum(support-y,0)).sum(axis=-1)/.1 for y in support]
    return np.min(values,axis=0)


def main():
    out=ROOT/"results";out.mkdir(exist_ok=True)
    exact_rows,mc_rows=[],[]
    for name,env,bound in [("example1",example1(),50),("example2",candidate(),51)]:
        for alpha in [F(1,2),F(4,5),F(9,10),F(19,20),F(99,100)]:
            mean,optimum,thresholds,choose=reference_dp(env,bound,alpha)
            brute=exhaustive_optimum(env,alpha)
            dist=distribution_of_policy(env,choose)
            evaluated=oracle.risk_metrics(dist,alpha)[2]
            if optimum!=brute or evaluated!=brute:
                raise AssertionError((name,alpha,optimum,brute,evaluated))
            exact_rows.append(dict(example=name,alpha=str(alpha),mean_optimum=float(mean[env.start]),
                                   dp_cvar=float(optimum),exhaustive_cvar=float(brute),
                                   executed_policy_cvar=float(evaluated),thresholds=str(thresholds)))
        mean,optimum,thresholds,choose=reference_dp(env,bound,F(9,10))
        dist=distribution_of_policy(env,choose)
        support=np.array(list(dist),dtype=int)
        probs=np.array([float(dist[z]) for z in support])
        n=100_000
        # 根据已知的精确概率质量函数进行有限支撑参数重复模拟。
        # 这里估计实际经验 CVaR 估计量的标准差，
        # 包含分位点跳变的影响，不借用固定阈值估计量的标准误。
        replication_seed=20261107+(name=="example2")
        counts=np.random.default_rng(replication_seed).multinomial(n,probs,size=20_000)
        reps=empirical_cvar_from_counts(counts,support,n)
        se=float(reps.std(ddof=1));bias=float(reps.mean()-float(optimum))
        for seed in range(10):
            rng=np.random.default_rng(seed)
            totals=np.empty(n,dtype=int)
            for i in range(n):
                s,z,steps=env.start,0,0
                while s!=env.goal:
                    s,c=env.sample(s,choose(s,z),rng);z+=c
                    steps+=1
                    if steps>env.n_states-1:
                        raise AssertionError("无环图轨迹超过了最大路径长度")
                totals[i]=z
            sample_counts=np.array([(totals==z).sum() for z in support])
            if sample_counts.sum()!=n:
                raise AssertionError("采样产生了精确策略分布支撑之外的总代价")
            estimate=float(empirical_cvar_from_counts(sample_counts,support,n))
            error=estimate-float(optimum)
            mc_rows.append(dict(example=name,seed=seed,trajectories=n,cvar_exact=float(optimum),
                                cvar_empirical=estimate,cvar_se_parametric=se,
                                replication_bias=bias,replication_seed=replication_seed,
                                replications=20_000,within_3se=abs(error)<=3*se))
        print({"example1":"例子 1", "example2":"例子 2"}[name],"五个风险水平均满足：精确动态规划值＝穷举最优值＝执行策略评价值；",
              "经验 CVaR 标准误",se,"重复模拟估计偏差",bias,flush=True)
    for name,rows in [("budget_dp_exact.csv",exact_rows),("budget_policy_mc.csv",mc_rows)]:
        with (out/name).open("w",newline="",encoding="utf-8") as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    result=dict(reference_scope="A 的无环图参考验证器，不是 C 的正式求解器",exact_cases=len(exact_rows),
                monte_carlo_cases=len(mc_rows),within_3se=sum(r["within_3se"] for r in mc_rows),
                exact=exact_rows,mc=mc_rows,mc_se_method="根据已知精确概率质量函数进行 20,000 次多项分布重复模拟")
    (out/"validation_summary.json").write_text(json.dumps(result,indent=2)+"\n")
    print(f"通过的精确比较案例数：{len(exact_rows)}；蒙特卡洛结果在三个标准误内的数量：{result['within_3se']}/{len(mc_rows)}")


if __name__=="__main__":
    main()
