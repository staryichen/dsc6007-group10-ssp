# C 部分交付与审核入口

分支：`feat/c-solvers-experiments`。用户已审核，提交 PR 供团队 review；不自动合并。

## 依赖与范围

仓库 main/dev 当时只有框架。实现基于 D 分支 `22675a2933b9011127bddf5c04f9cdbfc0f5f98c`，已包含 B 环境提交 `0a66eb1`。未改动 B 的环境和 D 的 `dist.py/risk.py`。A 分支 `9f62078` 的例子 2 复制为测试夹具，保留“候选环境”身份，不擅自加入共享环境。未来 PR 应在 B/D 合入 dev 后以 dev 为目标；否则明确说明堆叠依赖，避免把他们的成果当作 C 的新增实现。

三份用户提供的大纲全部已读；main/dev 与 B/D 分支的源码、接口说明已读，A 的对齐清单、参考 DP、例子 2 已核对。A 的参考结果不能代替本次 C 实际策略的验收。课程原始 PDF 不在提供文件或当前代码树中，未声称核验原始评分条款。

## 已完成

- 稀疏 VI、PI、LP；proper 初始策略；逐状态 improper 评估；确定性转移下 Dijkstra。
- 整数预算 DP、预算自动扩展及全局阈值搜索证书。
- 与 D 接口兼容的尾部补全评价：保留截断概率，准确补入尾部一阶矩。
- E2：全部 25 组 p/alpha 扫描、F2/F3、策略 JSON 与 PMF。
- E9：5 个 p × 3 个 gamma，共 15 行真实总代价对照。
- E4：10/20/40 网格 × 128/256/512 预算，3 次计时中位数、F7。
- 正式 C 策略的两个例子 × 5 个 alpha 穷举对照；每例 10 个 seed × 100,000 条真实轨迹，20/20 在 3 SE 内。

## 复现

在仓库根目录运行。仅使用已安装的 NumPy、SciPy、Matplotlib 和 Python 标准库。

```bash
python -m unittest discover -s tests -v
python -m experiments.run_c_validation --tag review1
python -m experiments.run_e2 --tag review1
python -m experiments.run_e9 --tag review1
python -m experiments.run_e4 --tag review1
```

各实验使用新 tag；已有结果不覆盖。确定性计算的 seed 字段为 `not_used`，MC 为 0–9；标准误使用固定种子 20261108、20,000 次多项分布重复模拟，包含经验分位点跳动。计时随机器和负载变化。

推荐审核版本：E2 **v3**，E9/E4/验证 **v1**。E2 v1/v2 仅留在本地作为修订历史，不纳入本次提交。

## API

```python
from ssp.envs.grid import make_grid
from ssp.solvers.vi import value_iteration
from ssp.solvers.pi import policy_iteration, evaluate_policy
from ssp.solvers.lp import linear_programming
from ssp.solvers.budget_dp import budget_dp
from ssp.solvers.dist import budget_policy
from ssp.solvers.tail_evaluation import evaluate_distribution

env = make_grid()
mean = value_iteration(env)
risk = budget_dp(env, alpha=.9, B=128)
choose = budget_policy(risk.policy, risk.initial_budget, risk.fallback)
metrics = evaluate_distribution(env, choose, .9, 160,
                                risk.fallback, risk.initial_budget)
```

`Solution.value/policy` 均使用原始完整状态编号，终点 value=0、policy=-1。预算表轴为 `[state, remaining_budget]`，列 0 使用期望最优策略；负预算必须使用 fallback，禁止负索引。每步减去实际观察到的整数代价。`BudgetSolution` 返回 CVaR `value`、`initial_budget`、完整 `W`、`objective`、fallback 和 `certified`。

预算 `B` 是初始请求，返回表可能更宽。未搜索整数 y≥B+1 的目标至少为 B+1；仅当 B+1 大于已找到的最优值，才声明完成搜索。超过 `max_budget` 报错。仅检查最优 y 是否落在边界是不充分的，已有专门反例回归测试。

PI 平局保留当前动作（1e-12 浮点容差）；VI/LP 与预算 DP 在动作精确平局时取第一个。最小阈值使用 1e-11 数值容差。CVaR 最优策略不唯一，不能要求其均值也最小。尤其 p=0 的部分预算内动作都产生零超支，任意平局动作可能多走几步但不改变最优 CVaR；报告已说明。

`evaluate_policy` 对能够到达不终止闭类的状态返回 inf，其他状态仍正确求有限值。不要因为策略在一个不可达状态 improper，就把起点值也错误写成 inf。

`evaluate_distribution` 对 callable 要求其在 `spent >= fallback_after` 后确实使用声明的 proper fallback；该契约用于尾部一阶矩补全。需 cutoff≥fallback_after 且覆盖 VaR，否则报错。PMF 本身仍截断，不能称为无限支撑完整分布；均值/CVaR 已补全尾部，只有浮点计算误差。

## 审核结果与交接

F2：`figures/f2_routes_v3.png/.pdf`，F3：`figures/f3_risk_return_v3.png/.pdf`，F7：`figures/f7_scaling_v1.png/.pdf`。

- 给 A：`results/c_validation_exact_v1.csv`、`c_validation_mc_v1.csv`；可直接调用正式 C solver 重验。
- 给 D：`results/e2_policies_v3.json`，直接符合其 JSON handoff 格式；尾部补全模块可单独集成。
- 给 E：`report/C_sections.md` 为可合并的 §4.1–4.2 与实验分析；F2/F3/F7 均有矢量 PDF。
- 例子 2 仍需 B/A 组内确认；本次仅作为已有候选的验证，不声称替他们完成正式环境合并。

用户审核已完成。本次 PR 以 dev 为目标，保留 B/D 原始依赖提交；请先审查和合入依赖，再合入 C。
