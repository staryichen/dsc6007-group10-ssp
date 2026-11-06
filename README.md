# DSC6007 Group 10 · dsc6007-group10-ssp

**随机代价与随机转移下的最短路：均值之外的风险敏感路由**

本项目为 DSC6007（Dynamic Programming and Reinforcement Learning，Semester A 2026）课程组项目，第 10 组，5 人。研究对象为随机代价与随机转移条件下的 Stochastic Shortest Path（下称 SSP）：当路段代价由分布而非单一数值给出时，最短路径的定义方式、求解方法与学习方法。

本仓库为课程项目工程，非任何论文的官方实现。求解主线复现并改造 Bäuerle 与 Ott（2011）的预算 DP（budget dynamic programming）；项目侧新增内容为整数代价下的精确代价分布计算，以及刻画"期望最优与 CVaR 最优何时分叉"的参数相图。完整方案见 `docs/SSP项目方案_v2.md`。

## 研究问题

本项目检查以下三个问题。

1. 随机代价与随机转移的 SSP 中，风险中性最优策略与 CVaR 最优策略在何种参数区间分叉，分叉幅度为何。
2. CVaR 最优策略依赖剩余预算的原因，以及依赖预算的策略相对仅依赖状态的策略的改进幅度。
3. $\gamma=1$ 的 SSP 上，表格型 Q-learning 达到期望最优路线所需样本量，以及探索阶段进入 improper 策略（无法到达终点）的频率与处理方式。

CVaR 最优策略依赖已花代价为静态风险度量的已知性质（Hau et al., 2023），非本项目结论。本项目的工作在于给出该性质在 SSP 上的可计算形式，并量化由此产生的路线差异。

## 方法

### 记号与假设

SSP 记为 $(\mathcal S,\mathcal A,P,c,s_0,\mathcal G)$，其中 $\mathcal G$ 为吸收态、出边代价为 0。全程不折扣，$\gamma=1$。代价取整数分钟，每步不少于 1 分钟。所需假设如下。

- A1：存在 proper policy，即以概率 1、有限期望步数到达 $\mathcal G$ 的策略。
- A2：任一 improper policy 的期望代价为无穷。每步代价不少于 1 分钟时，A2 成立。

### 期望塌缩

由全期望公式，$\mathbb{E}[Z]$ 仅依赖每步的条件均值 $\bar c(s,a)$，与代价和转移的随机性无关。因此风险中性最优策略，等于将每步代价替换为均值、保留随机转移的 SSP 的最优策略。随机性仅在尾部目标下改变决策。

### CVaR 与预算 DP

$\mathrm{CVaR}_\alpha(Z)=\min_{y}\big\{y+\tfrac{1}{1-\alpha}\mathbb{E}[(Z-y)^+]\big\}$，其中 $\alpha=0.9$ 对应最坏 10% 情形的均值。

将剩余预算 $b$ 纳入状态，$W(s,b)$ 为自 $s$ 出发、剩余预算为 $b$ 时的最小期望超支。

```text
W(G, b) = max(-b, 0)
W(s, b) = J*(s) - b                                  if b <= 0
W(s, b) = min_a sum_{s',c} P(s',c | s,a) W(s', b-c)   if b >= 1

CVaR*_alpha = min_y { y + W(s0, y) / (1 - alpha) }
```

每步代价不少于 1 分钟，故 $W(\cdot,b)$ 仅依赖更小预算，按 $b=1,2,\dots,B$ 顺序计算一次即可，无需迭代收敛，亦无网格误差。

### 代价分布

给定策略（含上述依赖预算的策略），自起点按已花代价 $z=0,1,2,\dots$ 递推概率：位于 $(s,z)$ 的概率按 $P(s',c\mid s,a)$ 转移至 $(s',z+c)$，落入 $\mathcal G$ 的部分即 $\Pr(Z=z+c)$。代价为整数，平移始终落在格点上，无投影误差；唯一误差为 $z_{\max}$ 处截断，截断概率单独记录并报告。

## 项目结构

```text
ssp/envs/        环境：toy 例子、无环验证例子、10×10 网格、15 节点路网
ssp/solvers/     求解器：VI、PI、LP、预算 DP、代价分布
ssp/rl/          表格型 Q-learning；可选 quantile TD
ssp/figstyle.py  统一绘图风格
experiments/     实验脚本，每个实验一条命令
results/         全部 csv
figures/         png 用于预览，pdf 用于 poster 与报告
report/          报告、slides、poster 源文件
```

## 环境与运行

运行环境为 Python 3.9 及以上，依赖 NumPy、SciPy、Matplotlib。不要求 GPU，不依赖网络。

```bash
python -m pip install -r requirements.txt
python experiments/run_e1.py
```

运行结果写入 `results/` 与 `figures/`。绘图统一调用 `ssp.figstyle`，实验脚本不另行设置 `rcParams`。

```python
import ssp.figstyle as fs

figsize = fs.setup("poster")            # 取值：poster、slides、report
fig, ax = plt.subplots(figsize=figsize)
ax.plot(x, y, color=fs.C["cvar"], label="CVaR 最优")
fs.save(fig, "figures/f2_routes_v1")    # 同时输出 png 与 pdf
```

颜色常量集中于 `fs.C`：`mean` 对应风险中性，`cvar` 对应 CVaR，`bar` 用于中性填充，`hi` 用于强调。全仓库、报告与 poster 使用同一配色。

## 实验与结果约定

- 一个实验对应一个脚本，单条命令完成运行，输出 `results/<实验名>.csv` 与 `figures/<图名>.png`、`figures/<图名>.pdf`。
- 随机种子固定并写入 csv；报告中每个数值可由 csv 复现。
- 图文件不覆盖，修订时另存为 `f2_routes_v2.png`。
- 未运行的结果不得写入报告、slides 或 poster。
- 实验分三档：poster 前必做、11-17 前完成、可选。11-17 尚未开始的可选项取消。

## Git 协作规范

`dev` 为日常集成分支，`main` 仅保存经验证的稳定版本。一个任务对应一个分支，不按成员维护长期分支。

| 分支 | 用途 |
| --- | --- |
| `main` | 稳定版本，交付节点由 `dev` 合并 |
| `dev` | 日常开发汇总，任务分支由此创建并合并回此 |
| `feat/<用户名>-<任务>` | 新功能，如 `feat/jin-budget-dp` |
| `fix/<用户名>-<问题>` | 缺陷修复，如 `fix/lin-dist-truncation` |
| `docs/<用户名>-<内容>` | 文档更新，如 `docs/wang-poster-text` |
| `chore/<用户名>-<任务>` | 依赖与配置维护 |

- 日常修改不直接推送至 `dev` 或 `main`，统一通过 Pull Request 合并，每个 PR 至少由一名组员检查。
- 提交信息格式为 `类型: 简短说明`，类型取 `feat`、`fix`、`docs`、`chore`，如 `feat: add budget DP for CVaR`。
- `__pycache__/`、虚拟环境与临时文件不纳入版本控制，规则见 `.gitignore`。
- 出现冲突时与对应修改人确认后解决，不得覆盖他人改动。

## 交付节点

| 日期 | 交付内容 |
| --- | --- |
| 11-10 18:00 | poster PDF（横版） |
| 11-24 18:00 | slides、report、15 分钟录像、demo 视频、代码、zip |
| 11-25 | 现场报告，随机抽取 |

文件命名统一为 `Group_10_*`，如 `Group_10_poster.pdf`、`Group_10_report.pdf`、`Group_10.zip`。

## 参考资料

- Bertsekas, D. P. & Tsitsiklis, J. N. (1991). *An Analysis of Stochastic Shortest Path Problems*. Mathematics of Operations Research, 16(3).
- Rockafellar, R. T. & Uryasev, S. (2000). *Optimization of Conditional Value-at-Risk*. Journal of Risk, 2(3).
- Bäuerle, N. & Ott, J. (2011). *Markov Decision Processes with Average-Value-at-Risk Criteria*. Mathematical Methods of Operations Research, 74(3), 361–379.
- Carpin, S., Chow, Y. & Pavone, M. (2016). *Risk Aversion in Finite Markov Decision Processes Using Total Cost Criteria and Average Value at Risk*. ICRA, 335–342.
- Hau, J. L. et al. (2023). *On Dynamic Programming Decompositions of Static Risk Measures in Markov Decision Processes*. NeurIPS.
