"""A 独立核对 C 最终网格 CSV、JSON、绘图数据及截断尾部补全。"""
from pathlib import Path
import csv
import json
import sys

ROOT=Path(__file__).resolve().parent
from paths import SOURCE, OUT, TAG
sys.path.insert(0,str(SOURCE))
import numpy as np
from ssp.envs.grid import make_grid
from ssp.solvers.expected import value_iteration
from ssp.solvers.budget_dp import budget_dp
from ssp.solvers.tail_evaluation import evaluate_distribution

OUT.mkdir(parents=True,exist_ok=True)


def read_csv(path):
    with path.open() as f:return list(csv.DictReader(f))


def require(ok,message):
    if not ok:raise AssertionError(message)


def fallback_value(env,pi):
    """独立组装非终点线性方程；不调用 C 的策略评价函数。"""
    states=[s for s in range(env.n_states) if s!=env.goal]
    pos={s:i for i,s in enumerate(states)}
    P=np.zeros((len(states),len(states)));c=np.zeros(len(states))
    for s in states:
        for o in env.outcomes[s][pi[s]]:
            c[pos[s]]+=o.prob*o.cost
            if o.next_state!=env.goal:P[pos[s],pos[o.next_state]]+=o.prob
    J=np.zeros(env.n_states);J[states]=np.linalg.solve(np.eye(len(states))-P,c)
    return J


def own_budget_values(env,J,B):
    """从定义按预算逐层计算 W，逐状态／动作求和，不调用 C 的预算递推。"""
    W=np.zeros((env.n_states,B+1));W[:,0]=J
    for b in range(1,B+1):
        for s in range(env.n_states):
            if s==env.goal:continue
            W[s,b]=min(sum(o.prob*(J[o.next_state]-(b-o.cost) if b-o.cost<=0
                       else W[o.next_state,b-o.cost]) for o in outs)
                       for outs in env.outcomes[s])
    return W


def own_distribution(env,choose,fallback,L,alpha):
    """按已花代价传播，并保留首次越界到达的状态与代价。"""
    J=fallback_value(env,fallback)
    pending=np.zeros((L+1,env.n_states));pending[0,env.start]=1
    pmf=np.zeros(L+1);crossings={}
    for spent in range(L+1):
        for s in np.flatnonzero(pending[spent]):
            for o in env.outcomes[s][choose(int(s),spent)]:
                z=spent+o.cost;mass=pending[spent,s]*o.prob
                if z>L:crossings[o.next_state,z]=crossings.get((o.next_state,z),0)+mass
                elif o.next_state==env.goal:pmf[z]+=mass
                else:pending[z,o.next_state]+=mass
    overflow=sum(crossings.values())
    tail=sum(m*(z+J[s]) for (s,z),m in crossings.items())
    require(abs(pmf.sum()+overflow-1)<1e-10,'概率不守恒')
    cumulative=0;var=None
    for z,p in enumerate(pmf):
        cumulative+=p
        if cumulative>=alpha-1e-12:var=z;break
    require(var is not None,'截断上限未覆盖 VaR')
    # 直接从最坏概率积分：越界质量全在当前 VaR 之外。
    remaining=1-alpha-overflow;tail_sum=tail
    for z in range(L,-1,-1):
        take=min(pmf[z],max(remaining,0));tail_sum+=z*take;remaining-=take
        if remaining<=1e-15:break
    mean=sum(z*p for z,p in enumerate(pmf))+tail
    return dict(mean=float(mean),var=var,cvar=float(tail_sum/(1-alpha)),
                overflow=float(overflow),tail_first_moment=float(tail),pmf=pmf)


def nominal(env,choose):
    """独立展开众数联合结果路线，不使用 C 的绘图路线函数。"""
    route=[env.start];s,z=env.start,0
    for _ in range(1000):
        if s==env.goal:return route
        o=max(env.outcomes[s][choose(s,z)],key=lambda x:x.prob)
        s=o.next_state;z+=o.cost;route.append(s)
    raise AssertionError('代表路线未终止')


def main():
    source=SOURCE;rows=read_csv(source/'results/e2_alpha_sweep_v3.csv')
    grid_json=json.loads((source/'results/e2_policies_v3.json').read_text())
    findings=[]
    try:make_grid(**grid_json['grid'])
    except Exception as e:
        findings.append(dict(priority='P1',item='导出 JSON 不能按文档直接载入环境',error=str(e),
          cause='start/goal 经 JSON 变成 list，环境用 tuple 比较终点，导致终点被赋动作',
          fix='读取时将 start/goal/zone_rows/zone_cols 转 tuple，或在 make_grid 入口统一规范化'))
    checked=[];all_models={};selected=None
    for p in [0,.05,.1,.2,.3]:
        env=make_grid(p=p);mean=value_iteration(env)
        J=fallback_value(env,mean.policy)
        require(np.max(abs(J-mean.value))<1e-8,'均值策略与 VI 不一致')
        W=own_budget_values(env,J,128)
        for row in [r for r in rows if float(r['p'])==p]:
            alpha=float(row['alpha']);solution=budget_dp(env,alpha,B=128)
            choose=lambda s,z: int(solution.fallback[s] if z>=solution.initial_budget
                                      else solution.policy[s,solution.initial_budget-z])
            mu=lambda s,z:int(mean.policy[s])
            n=own_distribution(env,mu,mean.policy,160,alpha)
            r=own_distribution(env,choose,solution.fallback,160,alpha)
            own_opt=float(np.min(np.arange(129)+W[env.start]/(1-alpha)))
            require(own_opt<129,'独立预算搜索范围不足')
            values={'mean_optimal':n['mean'],'mean_policy_cvar':n['cvar'],
                'cvar_policy_mean':r['mean'],'cvar_optimal':r['cvar'],
                'mean_premium':r['mean']-n['mean'],'cvar_reduction':n['cvar']-r['cvar'],
                'mean_overflow':n['overflow'],'cvar_overflow':r['overflow'],
                'mean_tail_first_moment':n['tail_first_moment'],
                'cvar_tail_first_moment':r['tail_first_moment']}
            maxerr=max(abs(values[k]-float(row[k])) for k in values)
            require(maxerr<1e-8,f'CSV 不一致：p={p},alpha={alpha},error={maxerr}')
            require(abs(own_opt-r['cvar'])<1e-8,'独立预算值与执行策略不一致')
            require(int(row['initial_budget'])==solution.initial_budget,'起始阈值不一致')
            mr,rr=nominal(env,mu),nominal(env,choose)
            require(len(mr)-1==int(row['mean_route_steps']) and len(rr)-1==int(row['cvar_route_steps']),'路线长度不一致')
            require((mr!=rr)==(row['nominal_routes_differ']=='True'),'路线差异标识不一致')
            checked.append(dict(p=p,alpha=alpha,max_csv_error=maxerr,independent_cvar=own_opt,
                                policy_cvar=r['cvar'],dp_error=abs(own_opt-r['cvar'])))
            if p==.1 and alpha==.9:selected=(env,mean,solution,n,r,mr,rr)
        print('完成 p=',p,'的五个风险水平',flush=True)
    env,mean,sol,n,r,mr,rr=selected
    require(np.array_equal(grid_json['mean_policy'],mean.policy),'JSON 均值策略不同')
    require(np.array_equal(grid_json['budget_policy'],sol.policy),'JSON 预算策略表不同')
    require(np.array_equal(grid_json['mean_policy'],sol.fallback),'JSON 未单独导出的 fallback 在当前版本不相同')
    require(abs(grid_json['cvar']-r['cvar'])<1e-8,'JSON 目标不同')
    pmf=read_csv(source/'results/e2_poster_pmf_v3.csv')
    require(len(pmf)==161,'PMF CSV 长度错误')
    for z,row in enumerate(pmf):
        require(int(row['cost'])==z and abs(float(row['mean_policy'])-n['pmf'][z])<1e-13
                and abs(float(row['cvar_policy'])-r['pmf'][z])<1e-13,'F2 PMF CSV 不一致')
    tail_checks=[]
    for L in [30,40,80,160,320]:
        choose=lambda s,z:int(sol.fallback[s] if z>=sol.initial_budget else sol.policy[s,sol.initial_budget-z])
        for label,pi,fallback in [('mean',lambda s,z:int(mean.policy[s]),mean.policy),('cvar',choose,sol.fallback)]:
            a=own_distribution(env,pi,fallback,L,.9)
            c=evaluate_distribution(env,pi,.9,L,fallback,sol.initial_budget if label=='cvar' else 0)
            err=max(abs(a['mean']-c.mean),abs(a['cvar']-c.cvar),abs(a['tail_first_moment']-c.tail_first_moment))
            require(err<1e-8,'尾部补全实现不一致')
            baseline=n if label=='mean' else r
            require(abs(a['mean']-baseline['mean'])<1e-8 and abs(a['cvar']-baseline['cvar'])<1e-8,'指标依赖截断上限')
            tail_checks.append(dict(policy=label,cutoff=L,overflow=a['overflow'],mean=a['mean'],cvar=a['cvar'],max_error=err))
    result=dict(c_commit='94aac225b2d731a2c724de5fa0259efc2358816e',grid_cases=checked,
       selected=dict(mean=n['mean'],mean_cvar=n['cvar'],cvar_policy_mean=r['mean'],cvar=r['cvar'],
           mean_route=mr,cvar_route=rr,mean_pmf=n['pmf'].tolist(),cvar_pmf=r['pmf'].tolist(),
           mean_display_omitted_mass=float(1-n['pmf'][:91].sum()),cvar_display_omitted_mass=float(1-r['pmf'][:91].sum())),
       tail_checks=tail_checks,findings=findings)
    (OUT/'numeric_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    with (OUT/'numeric_audit.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(checked[0]),lineterminator='\n');w.writeheader();w.writerows(checked)
    print('数值核对通过；JSON 直接载入问题数：',len(findings))


if __name__=='__main__':main()
