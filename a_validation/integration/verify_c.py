"""A 独立验收 C PR #3 的正式输出，不调用 C 的穷举或自查计算函数。"""
from pathlib import Path
from fractions import Fraction as F
import csv
import argparse
import hashlib
import importlib.util
import itertools
import json
import sys

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description='独立验收 C 的固定提交')
parser.add_argument('--c-source',required=True,type=Path,help='C 固定提交的源码目录')
parser.add_argument('--output',type=Path,default=ROOT/'results',help='结果输出目录')
args=parser.parse_args()
c_source=args.c_source.resolve()
expected=json.loads((ROOT/'c_source_hashes.json').read_text())
for name,digest in expected['files'].items():
    p=c_source/name
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
        raise RuntimeError('C 源码与已验收版本不一致：'+name)
sys.path.insert(0,str(c_source))
import numpy as np
from ssp.mdp import SSP, make_outcomes as O
from ssp.envs.acyclic import example1
from ssp.solvers.expected import value_iteration, policy_iteration, linear_programming
from ssp.solvers.budget_dp import budget_dp
from ssp.solvers.dist import budget_policy, cost_distribution
from ssp.solvers.tail_evaluation import evaluate_distribution

spec=importlib.util.spec_from_file_location('a_exact',ROOT.parent/'exact.py')
oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
C_SHA='94aac225b2d731a2c724de5fa0259efc2358816e'


def require(ok,message):
    if not ok: raise AssertionError(message)


def example2():
    """使用 A 已定义的环境，C 仅提供共享 SSP 数据容器。"""
    return SSP('example2_candidate',['S','A','B','M','G'],0,4,
        [['go'],['continue'],['continue'],['X','Y'],[]],
        [[O([(1,1,.9),(2,10,.1)])],[O([(3,1,1.)])],
         [O([(3,10,.5),(3,11,.5)])],
         [O([(4,1,.9),(4,30,.1)]),O([(4,6,1.)])],[]])


def enumerate_distributions(env):
    pairs=oracle.reachable_pairs(env)
    return [oracle.exact_distribution(env,dict(zip(pairs,choices)))
            for choices in itertools.product(*(range(len(env.actions[s])) for s,z in pairs))]


def empirical(counts,support,n):
    """在已知有限支撑上计算经验 CVaR₀.₉，包含分位点概率的部分截取。"""
    return np.min([y+(counts*np.maximum(support-y,0)).sum(axis=-1)/n/.1 for y in support],axis=0)


def main():
    out=args.output;out.mkdir(parents=True,exist_ok=True)
    exact_rows,mc_rows,policies=[],[],[]
    for name,env,limit in [('example1',example1(),50),('example2',example2(),51)]:
        all_dist=enumerate_distributions(env)
        mean_best=min(sum(z*p for z,p in d.items()) for d in all_dist)
        for solver in [value_iteration,policy_iteration,linear_programming]:
            result=solver(env)
            require(abs(result.value[env.start]-float(mean_best))<1e-9,'期望求解器与 A 穷举不同')
            d=oracle.exact_distribution(env,{(s,z):int(result.policy[s]) for s,z in oracle.reachable_pairs(env)})
            require(abs(float(sum(z*p for z,p in d.items()))-float(mean_best))<1e-9,'期望最优策略执行错误')
        for alpha in [F(1,2),F(4,5),F(9,10),F(19,20),F(99,100)]:
            brute=min(oracle.risk_metrics(d,alpha)[2] for d in all_dist)
            for requested_B in [0,64]:
                c=budget_dp(env,float(alpha),B=requested_B)
                require(c.certified,'C 未给出搜索证书')
                require(c.W.shape==(env.n_states,c.policy.shape[1]),'预算表尺寸错误')
                def choose(s,z):
                    b=int(c.initial_budget)-z
                    return int(c.fallback[s] if b<=0 else c.policy[s,b])
                pairs=oracle.reachable_pairs(env)
                adapter=budget_policy(c.policy,c.initial_budget,c.fallback)
                require(all(choose(s,z)==adapter(s,z) for s,z in pairs),'A 执行与 D 预算适配器不一致')
                dist=oracle.exact_distribution(env,{(s,z):choose(s,z) for s,z in pairs})
                mean,var,cvar,_=oracle.risk_metrics(dist,alpha)
                require(abs(float(brute)-c.value)<1e-9 and cvar==brute,'C 最优值／执行策略与穷举不同')
                d=cost_distribution(env,choose,limit)
                require(d.overflow==0,'完整支撑仍存在 overflow')
                require(np.allclose(d.pmf,[float(dist.get(z,0)) for z in range(limit+1)],atol=1e-12,rtol=0),'D PMF 与 A 精确分布不一致')
                # 截断评价必须使用同一个 C 返回的 fallback，不能偷偷换策略。
                cutoff=max(int(c.initial_budget),var)
                tail=evaluate_distribution(env,choose,float(alpha),cutoff,c.fallback,int(c.initial_budget))
                require(abs(tail.mean-float(mean))<1e-9 and abs(tail.cvar-float(cvar))<1e-9,'尾部补全指标错误')
                exact_rows.append(dict(example=name,alpha=str(alpha),requested_B=requested_B,
                    returned_B=c.policy.shape[1]-1,initial_budget=int(c.initial_budget),
                    certified=bool(c.certified),mean_optimal=float(mean_best),policy_mean=float(mean),
                    c_value=c.value,oracle_cvar=float(brute),executed_cvar=float(cvar),
                    d_pmf_match=True,tail_cutoff=cutoff,overflow=tail.overflow,tail_metrics_match=True))
                policies.append(dict(example=name,alpha=str(alpha),requested_B=requested_B,
                    initial_budget=int(c.initial_budget),policy=c.policy.tolist(),fallback=c.fallback.tolist(),
                    exact_distribution={str(z):str(p) for z,p in dist.items()}))
                if alpha!=F(9,10) or requested_B!=64:continue
                support=np.array(list(dist));probs=np.array([float(dist[z]) for z in support]);n=100_000
                replication_seed=20261108+(name=='example2')
                counts=np.random.default_rng(replication_seed).multinomial(n,probs,size=20_000)
                reps=empirical(counts,support,n);se=float(reps.std(ddof=1));bias=float(reps.mean()-float(cvar))
                for seed in range(10):
                    rng=np.random.default_rng(seed);totals=np.empty(n,dtype=int)
                    for i in range(n):
                        s,z,steps=env.start,0,0
                        while s!=env.goal:
                            s,cost=env.sample(s,choose(s,z),rng);z+=cost;steps+=1
                            require(steps<env.n_states,'无环例子出现超长轨迹')
                        totals[i]=z
                    observed=np.array([(totals==z).sum() for z in support])
                    require(observed.sum()==n,'模拟样本不在精确支撑内')
                    estimate=float(empirical(observed,support,n));passed=abs(estimate-float(cvar))<=3*se
                    mc_rows.append(dict(example=name,seed=seed,trajectories=n,cvar_exact=float(cvar),
                        cvar_empirical=estimate,se_parametric=se,bias_estimate=bias,within_3se=passed,
                        replication_seed=replication_seed,replications=20_000))
            print(name,'风险水平',str(alpha),'正式策略核对通过',flush=True)
    for file,rows in [('c_exact.csv',exact_rows),('c_mc.csv',mc_rows)]:
        with (out/file).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (out/'c_actual_policies.json').write_text(json.dumps(policies,ensure_ascii=False,indent=2)+'\n')
    summary=dict(c_commit=C_SHA,scope='两个无环例子的 C 正式策略独立验收，不包含全部网格实验',
        exact_cases=len(exact_rows),mc_cases=len(mc_rows),mc_within_3se=sum(r['within_3se'] for r in mc_rows),
        exact_pass=True,mc_pass=all(r['within_3se'] for r in mc_rows))
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False),flush=True)
    require(summary['mc_pass'],'模拟诊断未全部通过，保留原种子并检查结果')


if __name__=='__main__':main()
