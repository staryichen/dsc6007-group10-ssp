# DSC6007 小组项目方案：Random Costs & Transitions 的 SSP（新版）

> 状态：11-05 新版，在 11-04 初稿上改出来；改了什么、为什么改，见 `SSP方案修改说明.md`。题目已锁（10-25 Canvas），只能靠副标题和内容收窄。
> A–E 只是编号，认领完在群里对一下名字。
> 原则：先保证一条做得完的主线，其余做成可选。实验分三档：**必做**（poster 前完成）、**11-17 前**、**可选**（有余力再做）。

---

## 0. 一句话

题目不动，加一个副标题，把范围收到一个能检验的问题上：

**Stochastic Shortest Path Problems with Random Costs and Transitions**
*— Beyond the Mean: Risk-Sensitive Routing via CVaR and Distributional Dynamic Programming*

中文口头版：**「随机代价下，'最短'到底该按什么定义？」**

三个候选标题，推荐第一个：

1. `Beyond the Mean: Risk-Sensitive Stochastic Shortest Path under Random Costs and Transitions` ← 推荐，跟别组的 `Safe Pathfinding under Uncertainty: ...` 是一个句式
2. `When the Shortest Path Is Not the Safest: CVaR-Optimal Routing with Stochastic Costs and Transitions`
3. `From Expectations to Distributions: A Distributional View of Stochastic Shortest Path Problems`

副标题的作用有三个：把笼统的题目变成一个问句；让 poster 上有一句能被记住的话；跟另一组「Safe Pathfinding under Uncertainty: TD Learning for SSP」明确分开（他们做安全约束 + TD，我们做风险度量 + 分布 + model-based 精确解）。为了分得更开，网格里**不放悬崖**，风险来自随机代价里的大延误。

---

## 1. 为什么收窄成「均值之外」

**Observation 1（期望塌缩）**：只最小化期望代价时，随机代价会被完全抹平。

设总代价 $Z=\sum_{t=0}^{T-1} c(s_t,a_t,s_{t+1})$（不打折，$\gamma=1$），$c$ 是随机的、非负的。由全期望公式（代价非负，用单调收敛定理交换求和与期望）

$$\mathbb{E}[Z]=\mathbb{E}\Big[\sum_{t=0}^{T-1} \mathbb{E}[c(s_t,a_t,s_{t+1})\mid s_t,a_t]\Big]=\mathbb{E}\Big[\sum_{t=0}^{T-1} \bar c(s_t,a_t)\Big],\quad \bar c(s,a)=\mathbb{E}[c\mid s,a].$$

所以策略 $\pi$ 在随机代价 SSP 里对期望最优 **当且仅当** 它在"把每步代价换成平均代价 $\bar c$、转移仍然随机"的 SSP 里最优。注意这个结论不需要代价和转移独立，也不需要转移确定——随机性整个被均值吃掉了（前提见 Observation 3）。

这句话就是整个项目的 motivation：**如果你只看均值，那 "random costs" 这个题目里最重要的那个词是白写的。**

**Observation 2（那该看什么）**：随机性在下面这类目标下会改变决策（不止这三种，这三种最常用）。

| 目标 | 形式 | 适用场景 | 本项目 |
|---|---|---|---|
| 尾部风险 | $\min \mathrm{CVaR}_\alpha(Z)$ | 救援、SLA、电池余量 | 主线 |
| 整条分布 | 求出 $Z$ 的分布，任意风险度量都能读 | 想让决策者自己挑风险偏好 | 主线（用来评估策略） |
| 机会约束 | $\min \mathbb{E}[Z]$ s.t. $\Pr(Z\le d)\ge 0.95$ | 「必须 30 分钟内到」 | 放 extension |

第三条不放主线的理由要能讲出来：机会约束对策略是非凸的，得靠 Lagrangian 和对偶，三周做不完；而 CVaR 是它的保守代理：$\mathrm{CVaR}_\alpha(Z)\le d \;\Rightarrow\; \Pr(Z>d)\le 1-\alpha$。

**Observation 3（我们的边界，也是 reviewer 会问的）**：上面 Observation 1 有个隐藏前提——**代价的实现值不携带关于未来的信息**。如果同一条路的拥堵是持续性的（早高峰堵过一次，下一段还堵），那么风险中性的最优策略也会利用观测到的代价去更新信念，这就是 adaptive / Bayesian SSP。我们不做，写进 limitation + extension。这句话写进报告，能把「你们是不是漏了什么」挡回去。

---

## 2. 一个能在 poster 上用的例子（先把这个算对）

两条路从 S 到 G：

- **近路（桥）**：90% 概率 1 分钟，10% 概率 100 分钟（封桥绕行）→ 均值 10.9
- **远路（绕行）**：稳定 12 分钟 → 均值 12

风险中性选桥（10.9 < 12）。但 $\mathrm{CVaR}_{0.9}$（最坏 10% 的均值）：桥 = 100，绕行 = 12。风险厌恶选绕行。

**一句话版本**：用 1.1 分钟的均值优势，换 100 分钟的尾部。

再补一个「均值相同、尾部不同」的例子，堵住「CVaR 不就是嫌方差大吗」这个质疑：

- A：90% 概率 10，10% 概率 20 → 均值 11，$\mathrm{CVaR}_{0.9}=20$
- B：恒定 11 → 均值 11，$\mathrm{CVaR}_{0.9}=11$

均值一样，风险中性无差别，CVaR 选 B。方差也选 B，所以再补一个反例：方差惩罚两头，CVaR 只看坏的那头——构造一个「偶尔特别快、其余普通」的选项，方差大但 CVaR 不差。这个细节写进报告 3.2 节。

这几个例子的代价都是整数，可以手算，直接当 E1。

---

## 3. 研究问题与贡献

**RQ1**（主线）：在随机代价 + 随机转移的 SSP 里，风险中性最优与 CVaR 最优的路线在什么参数区间分叉？分叉幅度多大？

**RQ2**（主线）：CVaR 最优策略为什么要看"还剩多少预算"？看预算的策略比只看位置的策略好多少？（在小例子上精确算）

**RQ3**（11-17 前）：$\gamma=1$ 的 SSP 上，tabular Q-learning 要多少样本才能学到期望最优路线？探索时走进 improper 策略（一直到不了终点）的问题有多严重、怎么处理？

**贡献（报告里按这个写）**

- C1 统一形式化（$\gamma=1$、proper policy、两条假设，以及和 MRP、确定性最短路、折扣 MDP 的关系）+「期望塌缩」命题（附 5 行证明）+ 为什么不能打折的数据（E9）
- C2 CVaR-SSP 的预算 DP：表格实现，并在小例子上和穷举（含看历史的策略）对上
- C3 整数代价下的精确分布计算：没有投影误差，只有上界截断，截掉多少可以报告
- C4 一张相图：在（打滑率，大延误概率）平面上，风险中性路线与 CVaR 路线是否分叉
- C5 可复现代码 + 训练前/中/后的 demo（rubric 里 demos 是 optional，但「before/during/after」这个说法就是在等这个）

C1 不新，写法上要老实说「这是个 observation / 已知结论，不是我们的定理」——反而显得懂。

---

## 4. 技术路线

### 4.1 形式化（写进报告 §2）

SSP：$(\mathcal S,\mathcal A,P,c,s_0,\mathcal G)$。$\mathcal G$ 吸收、出边代价 0。**不打折，$\gamma=1$**：目标就是到达 $\mathcal G$ 之前的总代价 $Z$。

- 随机代价：每步代价 $c(s,a,s')$ 取**整数分钟**，平时小，偶尔有大延误（比如普通格子 1 或 2 分钟，"拥堵格子"以概率 $q$ 变成 10 倍）。**每步至少 1 分钟**。对数正态之类的连续分布，先离散成整数分钟再用。
- 随机转移：网格上用打滑率 $p$ 参数化（以 $p$ 概率走到随机相邻格）。
- 模型统一写成 $P(s',c\mid s,a)$：给定状态和动作，下一个状态和这一步代价的联合分布。toy、网格、路网都用这个格式，求解器只写一套。
- **proper policy**：以概率 1 且有限期望步数到达 $\mathcal G$ 的策略。两条假设（报告里显式写）：
  - A1：至少存在一个 proper policy；
  - A2：每个 improper policy 从某个状态出发的期望代价是无穷大。每步代价至少 1 时 A2 自动成立：到不了终点就要付无穷多步代价。
- 在 A1、A2 下的标准结论（Bertsekas & Tsitsiklis 1991，照着陈述、注明出处）：Bellman 方程有唯一解 $J^\star$；VI 从任意初值收敛到 $J^\star$；PI 从 proper policy 出发收敛；LP 可用；最优策略是平稳的、proper 的。
- 为什么要写这段：课上的收敛证明靠"$\gamma<1$ 时是压缩"（Lecture 4 第 10 页，上界依赖 $\gamma$），Lecture 3 第 30 页也说 $\gamma=1$ 只能用在回合长度一定有限的时候。这段就是在回答"$\gamma=1$ 为什么还能用"，半页就够。
- 和课上内容的关系（也写进报告 §2）：
  - 给定策略 $\mu$，SSP 就是一个 $\gamma=1$ 的 MRP：$J_\mu=\bar c_\mu+P_\mu J_\mu$（$P_\mu$ 只含非终点状态）。课上的闭式解 $v=(I-\gamma P)^{-1}r$ 在 $\gamma<1$ 时总存在；$\gamma=1$ 时，$I-P_\mu$ 可逆当且仅当 $\mu$ 是 proper policy。
  - 课上的两类问题都是 SSP 的特例：转移确定时就是确定性最短路；折扣 MDP 等价于"每步以 $1-\gamma$ 的概率直接终止"的 SSP。
- 目标：$\min_\pi \mathbb{E}[Z]$ / $\min_\pi \mathrm{CVaR}_\alpha(Z)$ / 给定策略求 $Z$ 的分布

风险度量（写清楚约定，别把 $\alpha$ 和 $1-\alpha$ 弄反）：

$$\mathrm{VaR}_\alpha(Z)=\inf\{z:\Pr(Z\le z)\ge\alpha\},\qquad
\mathrm{CVaR}_\alpha(Z)=\min_{y}\Big\{y+\tfrac{1}{1-\alpha}\mathbb{E}[(Z-y)^+]\Big\}$$
$\alpha\in(0,1)$，CVaR 是**最坏 $1-\alpha$ 比例**的均值：$\alpha=0.9$ 就是最坏 10%。

### 4.2 三个 solver

1. **期望最优**：VI + policy iteration，再加一个 LP 形式（$\max\sum_s V(s)$ s.t. $V(s)\le \bar c(s,a)+\sum_{s'}P(s'\mid s,a)\,V(s')$）互相校验。LP 那个还能在报告里讲最短路对偶，是加分项。LP 用 scipy 的 `linprog`（课上用 CVXPY，本机装不了）。
   - $\gamma=1$ 时课上的停止规则 $\frac{\gamma}{1-\gamma}\,\mathrm{span}(Tv-v)\le\epsilon$ 用不了（分母为 0）。改成"相邻两次迭代的最大差 < 1e-10"；这个规则没有误差保证，所以再用 PI 或 LP 核对。
   - 给定策略 $\mu$ 的期望代价（PI 的策略评估、E9 的真实总代价）用 MRP 的闭式解 $J_\mu=(I-P_\mu)^{-1}\bar c_\mu$ 算。$I-P_\mu$ 不可逆，说明 $\mu$ 是 improper，真实代价是无穷。
   - $p=0$ 时转移确定，风险中性问题就是以 $\bar c$ 为边长的确定性最短路：用 Dijkstra（课上最短路那讲）求一遍，最短代价要和 VI 一致（路线并列时可能不同）。
2. **代价分布**（给定策略，包括 3 里那种看预算的策略）：从起点出发，按已花代价 $z=0,1,2,\dots$ 依次把概率往前推。处在 $(s,z)$ 的概率按 $P(s',c\mid s,a)$ 推到 $(s',z+c)$；推到 $\mathcal G$ 的那部分就是 $\Pr(Z=z+c)$。
   - 每步代价至少 1，已花代价只增不减，按 $z$ 从小到大推一遍就完。
   - 代价是整数，每次都正好落在整数格点上，**没有投影误差**。唯一的误差是 $z_{\max}$ 处的截断：超过 $z_{\max}$ 的概率单独记下来并报告，要远小于 $1-\alpha$，不够就加大 $z_{\max}$。
   - 输出整条分布，均值 / VaR / CVaR / 分位数都能直接读。
   - 报告理论部分讲分布型 Bellman 方程 $\eta(s)=\sum_{s',c}P(s',c\mid s,\pi(s))\,(c\,\#\,\eta(s'))$（$\#$ 是平移）；对只看位置的策略，它和"往前推"给出同样的结果。实现上用"往前推"，是因为它对看预算的策略也能用。
3. **CVaR 最优：预算 DP**。把"还剩多少预算" $b$ 放进状态。定义 $W(s,b)$：从 $s$ 出发、剩余预算为 $b$ 时，最小的期望超支 $\mathbb{E}[(\text{剩余总代价}-b)^+]$。
   - 到达终点：$W(\mathcal G,b)=\max(-b,0)$
   - 已经超支（$b\le 0$）：$W(s,b)=J^\star(s)-b$。超支以后每多一分钟都算数，只管期望最小，$J^\star$ 就是 1 里的风险中性最优值
   - 还有预算（$b\ge 1$）：$W(s,b)=\min_a \sum_{s',c}P(s',c\mid s,a)\,W(s',b-c)$
   - 最后：$\mathrm{CVaR}^\star_\alpha=\min_{y\in\{0,1,\dots,B\}}\big\{y+W(s_0,y)/(1-\alpha)\big\}$，取到最小的 $y^\star$ 就是起始预算
   - 每步代价至少 1，所以 $W(\cdot,b)$ 只依赖更小的预算：按 $b=1,2,\dots,B$ 扫一遍就算完，不用迭代到收敛。计算量约 $B\times|\mathcal S|\times|\mathcal A|\times K$（$K$ 是每个 $(s,a)$ 的 $(s',c)$ 结果数），10×10 网格是秒级
   - 执行：从 $b=y^\star$ 出发，每步选 $a=\mu(s,b)$，走完再 $b\leftarrow b-c$。直觉：还在预算内就求稳，已经超支就只管平均最小
   - $B$ 要取够大：如果 $y^\star$ 碰到上限 $B$，就加大 $B$ 重算

### 4.3 一个必须有的 ground truth（这条最重要）

CVaR 最优策略一般**要看历史**（具体说，要看已经花了多少）。所以穷举时不能只列"只看位置"的平稳策略：那样正确的 DP 反而会比"穷举最优"更好，检查就过不了。

做法：用**无环**的小例子（每步代价至少 1，状态图没有回路）。这样"按已花代价选动作"的策略也能全部列出来，每个策略的 CVaR 都能把所有路径和概率列出来**精确**算，不用 MC。

- **例子 1（答案已知，先用它对代码）**：S → M 这一段 90% 1 分钟、10% 20 分钟；到 M 后选路线 X（90% 1 分钟、10% 30 分钟）或路线 Y（恒定 6 分钟）；$\alpha=0.9$。
  - 只看位置的策略：总走 X 的 CVaR = 32.9，总走 Y 的 CVaR = 26.0
  - 看历史的最优：第一段顺利就走 Y、第一段堵了就走 X，CVaR = 23.9
  - 预算 DP：$y^\star=7$，$\mathrm{CVaR}^\star=23.9$
- **例子 2**：自己设计一个 5–6 个状态、带打滑和随机代价的无环例子。可达的（状态，已花代价）组合控制在 10 个左右，这样策略最多约 1000 个，全部穷举。

判定标准写死：

1. 预算 DP 的 $\mathrm{CVaR}^\star$ 等于穷举（含看历史的策略）的最优值，浮点误差内相等。
2. 预算 DP 的策略用 10 万条轨迹模拟（模拟时要跟踪剩余预算），估出的 CVaR 与 $\mathrm{CVaR}^\star$ 差在 3 个标准误以内。不用 1 个标准误：实现完全正确时，也有约 1/3 的概率差超过 1 个标准误。
3. 4.2 的分布计算：在例子上和"列出所有路径"得到的分布完全一致；在网格上，风险中性策略的分布均值等于 VI 的 $J^\star(s_0)$，CVaR 策略的分布算出的 CVaR 等于预算 DP 的 $\mathrm{CVaR}^\star$。
4. 记下"看历史"比"只看位置的最好策略"好多少（例子 1 是 26.0 → 23.9），这个回答 RQ2。

**例子 1 对不上，网格上的 CVaR 图就不许画；全部检查不过，报告里的图不许定稿。** 没有它，整个项目的可信度是零。

### 4.4 learner

1. **tabular Q-learning**（期望代价，**$\gamma=1$**，别顺手写成 0.9）：学期望最优路线，录训练前/中/后的 demo。
   SSP 上做 model-free 有个绕不开的坑：**$\epsilon$-greedy 可能长时间到不了终点**。处理办法：每回合限最大步数（到了就截断，记为超时）；Q 初值取 0（代价为正，0 是乐观初值，会鼓励去试没走过的动作）；必要时用"朝终点方向"的定向探索。超时率当结果报，别藏起来，这就是实验 E6（11-17 前）。这是 SSP 特有的 RL 问题：折扣 MDP 里回合不必结束、值总是有限，没有这个问题。
2. **可选：分布型学习只做策略评估**。固定一个策略，用 quantile TD 学它的代价分布，和 4.2 的精确分布比（分布距离、CVaR 误差随样本数怎么降）。**不做**"按学到的 CVaR 贪心选动作"：这种做法一般不收敛到 CVaR 最优，讲不清楚。

### 4.5 四个容易踩的理论坑（写进报告的 discussion，能显水平）

1. CVaR 对时间的和**不可加**：$\mathrm{CVaR}(Z_1+Z_2)\ne \mathrm{CVaR}(Z_1)+\mathrm{CVaR}(Z_2)$。所以不能"每步 CVaR 相加"。
2. **静态 vs 嵌套 CVaR**：一次性对整个 $Z$ 取 CVaR（**我们做的是这个**），跟每一步按条件取 CVaR，结果不一样。后者天然满足 Bellman 递归；前者要把剩余预算放进状态才行，所以最优策略要看历史。
3. **mean-variance 时间不一致**：$\min \mathbb{E}[Z]+\lambda\mathrm{Var}(Z)$ 在 MDP 里一般不满足最优性原理，需要把 $(\mathbb E,\mathbb E^2)$ 一起放进状态，而且重优化出来的策略会自相矛盾。所以我们用 CVaR 不用方差——这是有理由的取舍，不是没想到。
4. **$\gamma$ 不能随手改成小于 1**：打折会改变目标。每步代价都是 1 时，打折后的总代价是 $(1-\gamma^T)/(1-\gamma)$，最小化它等于最大化 $\mathbb E[\gamma^T]$；$\gamma^T$ 对 $T$ 是凸的，所以平均步数相同时，步数波动越大反而越"好"——打折偏好冒险，跟我们研究风险厌恶的主线冲突。E9 用数据说明这一点。

### 4.6 和课程内容的对应（报告 Introduction 末尾放一段，slides 放一页）

| 课程内容 | 项目里对应的部分 |
|---|---|
| 动态规划、VI、PI | 期望最优用 VI / PI / LP；预算 DP 是在"状态 + 剩余预算"上做 DP |
| MDP、SSP | 整个问题：$\gamma=1$、有终点；proper policy 和两条假设 |
| 最短路 | $p=0$ 时风险中性问题就是确定性最短路，用 Dijkstra 核对 VI |
| MRP | 给定策略的期望代价 $J_\mu=(I-P_\mu)^{-1}\bar c_\mu$；代价分布计算 |
| MC、TD | MC 模拟核对 CVaR；Q-learning 是 TD 方法；可选的 E8 是分布型 TD |
| Model-free control | Q-learning（$\gamma=1$）和探索失败分析（E5、E6） |
| Function approx、PG、Bandits | 不用；写进 extension（大路网用函数逼近、用策略梯度优化 CVaR） |

不用全覆盖课程内容；这张表的作用是让老师一眼看出项目是从课上延伸出来的。

---

## 5. 实验矩阵

| 编号 | 档位 | 问题 | 设置 | 产出 | 谁 | 验收 |
|---|---|---|---|---|---|---|
| E0 | 必做 | 求解器对不对 | 两个无环小例子，穷举含看历史的策略 + 10 万条 MC | 对照表 | A | 4.3 的判定标准全过 |
| E1 | 必做 | 直觉 | 双路线玩具（第 2 节） | 图 F1 + 表 | A | 手算数字对得上 |
| E2 | 必做 | 分叉 | 10×10 网格，$p\in\{0,.05,.1,.2,.3\}$，$\alpha\in\{.5,.8,.9,.95,.99\}$ | 图 F2 两条路线 + 两条代价分布；F3 风险-收益平面 | C | $\alpha$ 越大路线一般越保守，不单调的地方要能解释；$p=0$ 时风险中性的最短代价和 Dijkstra 一致 |
| E3 | 11-17 前 | 相图 | 横轴大延误概率 $q$（10 倍代价），纵轴打滑率 $p$ | 图 F4 热图 | B | 分叉区域连通、可解释 |
| E5 | 11-17 前 | model-free | tabular Q-learning，$\gamma=1$ | 图 F5 学习曲线 + demo | D | 学到的贪心路线和 VI 的一致 |
| E6 | 11-17 前 | 探索失败 | 不同探索策略（$\epsilon$-greedy、定向探索、乐观初值）下的超时率和失败率 | 表 | D | 至少两种策略，能解释原因 |
| E7 | 11-17 前 | 应用 | 15 节点路网（手工搭，不用 OSM，没网），整数随机代价，SLA = 30 分钟 | 图 F6 推荐路线 + 达标率 | B | 期望最优与 CVaR 最优路线不同 |
| E9 | 11-17 前 | 为什么不打折 | 10×10 网格，用 $\gamma\in\{0.9,0.99\}$ 求最优策略，按真实总代价（$\gamma=1$）评估，和 $\gamma=1$ 的最优比 | 表 | C | 差多少写清楚；策略 improper 时真实代价是无穷，照实报 |
| E4 | 可选 | 规模 | 网格 10/20/40 × 预算上限 $B$ | 图 F7 运行时间 | C | 能跑完，时间随规模的变化能解释 || E8 | 可选 | 分布型学习 | 固定策略，quantile TD 学分布 vs 精确分布 | 误差曲线（可放附录） | D | 误差随样本数下降 |

网格怎么设计（建议）：起点和终点之间有一段"近路"，近路上的格子以概率 $q$ 出现 10 倍延误；绕开它要多走几步；打滑率 $p$ 控制转移的随机性。这样调 $q$ 和 $p$，两条路线就容易分叉，E3 的相图也是在这两个参数上扫。

跑量：全是表格法，单次秒级到分钟级；MC 和学习用 10 个 seed，总共不到 1 小时。**不需要 GPU，不需要联网，只用 numpy / scipy / matplotlib**（本机 pip 装不了包，这条是硬约束）。

---

## 6. 报告（≤15 页）与 poster

| 节 | 内容 | 页 |
|---|---|---|
| 1 | Introduction：随机代价为什么不等于随机数表；toy 例子；贡献列表；末尾一段和课程内容的对应（4.6） | 1.5 |
| 2 | Background：SSP 定义、$\gamma=1$、proper policy 与两条假设、Bellman 方程、VI/PI/LP 及其收敛（"$\gamma=1$ 为什么还能用"，约半页）；和 MRP、确定性最短路、折扣 MDP 的关系 | 2 |
| 3 | Theory：塌缩命题；VaR/CVaR 与相干性；预算 DP 的推导，以及最优策略为什么要看剩余预算；整数代价下的精确分布（只有截断误差）；四个理论坑 | 3.5 |
| 4 | Algorithms：伪代码 + 复杂度（4.1 期望最优，4.2 预算 DP，4.3 代价分布，4.4 学习） | 1.5 |
| 5 | Experiments：E0–E3、E5–E7、E9（可选项做了再加） | 4 |
| 6 | Conclusion（评分要求点名了这三块，缺一不可）：优点 strength（精确，能和穷举对上；可解释，策略看剩余预算；计算量小，表格法一遍扫完）；局限 limitation（表格法、模型已知、整数代价、静态 CVaR、规模受状态数 × 预算上限限制）；扩展 extension 分三类写——理论（adaptive SSP、机会约束、嵌套 CVaR）、算法（大路网用函数逼近、用策略梯度直接优化 CVaR、深度分布型 RL）、应用（真实路网数据、救援 / 物流的 SLA） | 1 |
| 7 | 参考文献 + 分工声明 | 1 |

图 7 张封顶：F1 toy、F2 网格两条路线 + 分布、F3 风险-收益、F4 相图、F5 学习曲线、F6 路网、F7 规模（可选）；E6、E9 出的是表，不占图的名额。**别超过 7 张**，15 页里图占太多正文就写不下，宁可图少但每张都分析透。

### poster（单独的交付物，不是实验的附产品）

11-10 18:00 截止，11-11 现场站台加 2 分钟讲。六块内容：

1. 标题加副标题
2. 动机：toy 例子和那两个数字
3. 形式化：三行，SSP 记号加 CVaR 定义
4. 方法：三条线各一段（期望最优、代价分布、预算 DP）
5. 初步结果：一张图，10×10 网格上的两条路线加两条代价分布
6. 计划与分工

倒推着做：11-06 必须有第一张真图（toy 表 + 网格上的风险中性路线），11-07 出网格上的 CVaR 路线和两条分布、拼 v1，11-08 v2 并练三遍，11-09 定稿交掉。poster 的进度比报告早两周，这是全组第一个硬节点。

分工：E 排版定稿；A 出方法框图、第 3 块文字和 toy 的数字表；B 出 toy 图和网格图；C 出网格上的两条路线；D 出两条代价分布。Q-learning 曲线有就放，没有就留到 slides。

一条纪律：poster 上只放已经跑出来的东西，没做的写进"计划"那一块，别画成结果。

---

## 7. 五人分工

一人一块，粗着分。只约定三件事：负责什么、对应报告哪节、什么时候交；具体怎么做各自决定，不用开会分。

| 人 | 负责 | 报告 |
|---|---|---|
| **A** | 理论与验证：形式化（$\gamma=1$、两条假设）、塌缩命题、CVaR 与预算 DP 的推导、四个理论坑；E0 穷举验证、E1 toy | §2 §3 |
| **B** | 环境与数据：toy、无环验证例子、网格、路网、参数网格、种子，所有图的数据；E3 相图、E7 路网 | §5.1 |
| **C** | 求解器：VI/PI/LP、预算 DP；E2、E9，可选 E4 | §4.1–4.2 |
| **D** | 分布与学习：代价分布计算、Q-learning 和 demo；E5、E6，可选 E8 | §4.3–4.4 |
| **E** | 整合与交付：repo、图风格、poster 排版定稿（内容各人提供）、报告合并排版、录制、提交；讲 poster 那 2 分钟 | §1 §6 |

E 的活是整合类：不写实验代码、不推公式，但要盯齐所有人的东西、排 poster、最后录屏和提交。看着轻，其实全压在最后两周，所以别再给 E 加实验任务。

poster 是 E 的第一个真活，也是全组第一个硬节点：11-07 就要有能看的 v1，那版的内容得靠 A、C、D 在 11-07 之前跑出东西来。

15 分钟录像是 A 讲理论、C 讲实验，各讲自己写的那块，不用另外写稿。理论部分要给"$\gamma=1$ 为什么还能用"和"最优策略为什么要看剩余预算"留够时间，这两块最能体现深度，别让 toy 和路线图占满。

只在三个时间点对齐，其余不用互相等：11-06/11-07 出 poster 用的图、11-17 冻结实验清单、11-21 报告合并。

工作量：先做必做和"11-17 前"两档，做完再领可选项；11-17 还没开始的可选项直接砍。

---

## 8. 时间线（今天 11-05 周四）

| 日期 | 事 | 谁 |
|---|---|---|
| **11-05 今晚** | 认领 A–E（如果还没认）、建 repo；环境 v1（toy、10×10 网格，统一成 $P(s',c\mid s,a)$ 格式）；VI 基线；形式化草稿 | 全员 |
| 11-06 | toy 的均值 / CVaR 表；预算 DP 在例子 1 上对上 23.9；网格上的风险中性路线 | A C B |
| 11-07 | 网格上的 CVaR 路线 + 两条代价分布；poster v1（各交一块，E 拼） | C D E |
| 11-08 | poster v2；2 分钟稿练 3 遍（只写 7 句话的 cue card，不许念稿） | E |
| **11-09 晚** | poster 定稿、导 PDF、**提前交掉**（deadline 是 10 号 18:00） | E |
| 11-11 | poster session，2 分钟；记下被问的问题 | E |
| 11-12 → 11-16 | E0 全部检查（含例子 2）、E2 参数扫描、E3 相图、E5 Q-learning、E6 探索失败、E7 路网、E9 折扣对比 | A C B D |
| **11-17** | **mid freeze**：实验清单定死，不再加新想法；决定可选项（E4/E8）做不做 | 全员 |
| 11-18 → 11-20 | 可选项（如果做）；图全部定稿；demo 录好 | C D B |
| 11-21 | 报告全文草稿（各交各节，E 合并）+ slides v1 | 全员 |
| 11-22 | 报告 v2 + slides v2；15 分钟排练 2 遍，计时 | 全员 |
| **11-23** | Zoom 一次录完（不剪辑）；代码转 .txt；打包 zip；**当晚提交** | E |
| 11-24 | 18:00 前确认提交成功；准备 live 的 Q&A | E |
| 11-25 | live presentation + Q&A（如果被抽到；内容和录像完全一样，不许念稿） | A C |

两个硬节点：**11-09 交 poster**、**11-23 交全套**。11-24 只做确认，不留任何活。

---

## 9. 提交清单（这个最容易白丢分）

文件名照项目说明 PDF 第 3 页（渲染出来是带下划线的），x 换成组号：

| 文件 | 命名 | 截止 |
|---|---|---|
| poster | `Group_x_poster.pdf` | 11-10 18:00 |
| slides | `Group_x_slides.pdf` | 11-24 18:00 |
| report | `Group_x_report.pdf` | 11-24 18:00 |
| 15 分钟录像 | PDF 没给命名，按 Canvas 上的要求 | 11-24 18:00 |
| demo 视频 | `Group_x_demo_1_before.mp4`、`Group_x_demo_1_during.mp4`、`Group_x_demo_1_after.mp4`；第二个 demo 用 `demo_2` | 11-24 18:00 |
| 代码 | `Group_x_c_main.txt`、`Group_x_c_solver.txt` 等（py/txt） | 11-24 18:00 |
| 打包 | `Group_x.zip` | 11-24 18:00 |

两个坑：

1. 用工具从 PDF 里抽文字时，下划线会丢，所以以渲染出来的页面为准；有疑问再去 Canvas 原帖确认。
2. 代码要 .txt/.py，zip 里所有文件名都按上表改过再打包。

participation 占 6 分（占整个项目 20%），是白送的：每人至少给别组提 1 个问题 + 交 1 份匿名 feedback，记在一个小表里（日期 / 组号 / 问题）。别全组一个人问。

---

## 10. 风险与 fallback

| 风险 | 触发信号 | 应对 | 决策点 |
|---|---|---|---|
| 预算 DP 对不上 | 例子 1 算不出 23.9 | 在例子 1 上逐项手算 $W(s,b)$ 对照；还不行就在小网格上用穷举/MC 策略搜索（CEM）直接优化 CVaR，理论部分保留推导 | 11-07 |
| 网格上两条路线一样 | E2 没有分叉 | 调大延误倍数或概率 $q$、调近路长度 | 11-07 |
| poster 前网格 CVaR 图没出来 | 11-08 还没有 | poster 用 toy + 网格风险中性路线，网格 CVaR 写进"计划"块 | 11-08 |
| 截断太多 | 超过 $z_{\max}$ 的概率不可忽略 | 加大 $z_{\max}$ 和 $B$ | 随时 |
| 学习不收敛 / 长时间到不了终点 | 10 万步还学不到最优路线 | 限步长 + 乐观初值 + 定向探索；把超时率当结果报，不藏 | 11-16 |
| 跟「TD learning for SSP」那组撞题 | poster session 撞车 | 副标题已经隔开，网格不放悬崖；slides 第 2 页加一句"我们跟他们做的三处不同" | 11-11 当场 |
| 有人掉线 | 连续 2 天没动静 | E 机动补位；必做部分尽量两人共管 | 随时 |
| 时间不够 | 11-20 还有图没出 | 可选项全砍；还不够就在 E3、E7 里砍一个，保 E0/E1/E2 和工作量小的 E5/E6/E9；报告里明说砍了什么 | 11-20 |

---

## 11. 文献（必读 4 篇，其余选读）

必读：

1. Bertsekas & Tsitsiklis (1991), *An Analysis of Stochastic Shortest Path Problems*, Mathematics of Operations Research 16(3)（SSP 的标准参考：proper policy、两条假设、VI/PI 收敛）
2. Rockafellar & Uryasev (2000), *Optimization of Conditional Value-at-Risk*（只读前 8 页，把变分式搞懂）
3. Bäuerle & Ott (2011), *Markov Decision Processes with Average-Value-at-Risk Criteria*, Mathematical Methods of Operations Research 74(3):361–379（预算 DP 的来源，A/C 的核心）
4. Carpin, Chow & Pavone (2016), *Risk Aversion in Finite Markov Decision Processes Using Total Cost Criteria and Average Value at Risk*, ICRA 2016, pp. 335–342（不打折的总代价下做 CVaR，跟 SSP 最贴近）

选读：

5. Bertsekas & Yu, *Stochastic Shortest Path Problems Under Weak Conditions*（MIT 报告，mit.edu/~dimitrib/SSP_Weak_Conditions.pdf；假设能放宽到什么程度）
6. Chow, Tamar, Mannor & Pavone, NIPS 2015, *Risk-Sensitive and Robust Decision-Making: A CVaR Optimization Approach*（另一种增广状态做法，related work 里提一句；它假设 $\gamma<1$）
7. Hau 等, NeurIPS 2023, *On Dynamic Programming Decompositions of Static Risk Measures in Markov Decision Processes*（arXiv 2304.12477；说明 6 那类分解一般不是最优，这是我们不用它的理由）
8. Bellemare, Dabney & Munos, ICML 2017, *A Distributional Perspective on Reinforcement Learning*（分布型 Bellman 方程）
9. Lim & Malik, NeurIPS 2022, *Distributional Reinforcement Learning for Risk-Sensitive Policies*（按学到的 CVaR 贪心选动作为什么不对）
10. Dabney et al., AAAI 2018, *Distributional Reinforcement Learning with Quantile Regression*（quantile TD，可选的 E8 用）
11. Mannor & Tsitsiklis, ICML 2011, *Mean-Variance Optimization in Markov Decision Processes*（为什么不用方差）
12. Sibul, Schütz & Fagerholt, *Arctic route planning under ice uncertainty: a risk-averse stochastic shortest path problem*, Transportation Research Part E 第 205 卷（真实场景的风险厌恶 SSP，当 motivation；年份引用前再核一次）
13. Tarbouriech 等人的 SSP 样本复杂度工作（ALT/NeurIPS 2020–21 一带，具体出处让 A 查准再引）——支撑"improper policy 是本质困难"这句话

引用规矩：不确认的文献不引。宁可少两篇，不要被 TA 抓到编文献。1、3、4、5、6、7、9、12 的出处核过；标题和页码引用前仍按原文对一次。

---

## 12. 组内协作

```
ssp/
  README.md              # 环境、复现命令、结果表
  requirements.txt       # numpy scipy matplotlib
  ssp/
    mdp.py               # SSP 定义（P(s',c|s,a)，整数代价）、proper 检查、采样
    risk.py              # VaR/CVaR（经验分布 + 精确分布两套）
    envs/toy.py  envs/acyclic.py  envs/grid.py  envs/network.py
    solvers/vi.py  solvers/lp.py  solvers/dist.py  solvers/budget_dp.py
    rl/qlearning.py      # 可选：rl/quantile_td.py
    figstyle.py          # 统一配色/字号，所有图走这里
  experiments/run_e0.py ... run_e9.py  + runner.py（固定 seed，输出 csv+png）
  results/  figures/  report/
```

- 每个实验脚本：一条命令跑完，输出 `results/e2_alpha_sweep.csv` + `figures/f3_risk_return.png`，图里不写死数据
- 所有随机种子写死并记录在 csv；报告里的数字必须能从 csv 复现
- 分支：`main` 只放能跑的；每人一个分支；合并前 E review
- 节奏：每天群里 3 行进度（昨天/今天/卡点），周日晚上 30 分钟同步

---

## 13. 如果最后人数不是 5

- **5 人**：必做 + 11-17 前两档全做，可选项有余力再做
- **4 人**：不做可选项
- **3 人**：再在 E3、E7 里砍一个，E6 也砍；Q-learning 只做 demo，不做细的学习曲线
- **2 人**：只做「塌缩 + $\gamma=1$ 的 SSP 基础 + 双路线 toy + 10×10 网格两条路线 + E0 例子 1」，报告 8 页，重点写清楚为什么期望不够

人数以 Canvas 上已提交的 group.txt 为准。
