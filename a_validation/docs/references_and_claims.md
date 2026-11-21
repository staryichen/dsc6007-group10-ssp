# 参考文献与论断对应

核对日期：2026-11-07。只列本次可核对的学术来源；本项目的小例子数值来自本地计算，不来自文献。不是完整文献综述。

| 文献 | 核对内容／使用范围 | 阅读状态与边界 |
|---|---|---|
| Bertsekas, D. P. & Tsitsiklis, J. N. (1991). An Analysis of Stochastic Shortest Path Problems. Mathematics of Operations Research, 16(3), 580–595. DOI: 10.1287/moor.16.3.580. [作者 PDF](https://www.mit.edu/~jnt/Papers/J034-91-berts-SSP.pdf)；[期刊页](https://pubsonline.informs.org/doi/10.1287/moor.16.3.580) | 有限 SSP 的 proper 条件、唯一 Bellman 固定点、VI 和最优平稳 proper 策略 | 已核对期刊元数据和 Proposition 2；用于期望代价，不作为静态 CVaR 平稳性结论 |
| Rockafellar, R. T. & Uryasev, S. (2000). Optimization of Conditional Value-at-Risk. Journal of Risk, 2(3), 21–41. DOI: 10.21314/jor.2000.038. [作者目录](https://uryasev.github.io/publications/) | CVaR 变分优化表达式的原始归属 | 作者目录与 DOI/书目信息已核对；作者链接的全文本次获取失败，不声称逐页读过。公式同时在已读取的后续原始论文中得到交叉核对 |
| Rockafellar, R. T. & Uryasev, S. (2002). Conditional Value-at-Risk for General Loss Distributions. Journal of Banking & Finance, 26(7), 1443–1471. DOI: 10.1016/S0378-4266(02)00271-6. [出版页](https://www.sciencedirect.com/science/article/pii/S0378426602002716)；[作者目录](https://uryasev.github.io/publications/) | 一般／离散分布下的 CVaR 和相干性 | 已核对原始摘要与作者目录；未取得全文，不给出虚构页内定位。离散尾部公式另由定义直接计算 |
| Bäuerle, N. & Ott, J. (2011). Markov Decision Processes with Average-Value-at-Risk Criteria. Mathematical Methods of Operations Research, 74(3), 361–379. DOI: 10.1007/s00186-011-0367-0. [机构元数据](https://publikationen.bibliothek.kit.edu/1000032887)；[机构全文](https://publikationen.bibliothek.kit.edu/1000032887/3310751) | 将期望超支转为增广状态控制的来源 | 已读取全文相关模型、有限／无限期定义和 Section 4 条件。不能把其折扣无限期压缩定理直接用作 γ=1 的 SSP 证明；本报告专门给出正整数预算递推 |
| Carpin, S., Chow, Y.-L. & Pavone, M. (2016). Risk Aversion in Finite Markov Decision Processes Using Total Cost Criteria and Average Value at Risk. [arXiv:1602.05130](https://arxiv.org/abs/1602.05130)；[全文](https://arxiv.org/html/1602.05130v1) | 不折扣总成本的相关背景与假设区别 | 已核对作者、标题、2016 预印本及正文 Assumptions 1–2。其全局可达条件强于“只存在一个 proper 策略”；当前引用预印本，不填写尚未独立核对的会议页码 |
| Hau, J. L., Delage, E., Ghavamzadeh, M. & Petrik, M. (2023). On Dynamic Programming Decompositions of Static Risk Measures in Markov Decision Processes. NeurIPS. [arXiv:2304.12477](https://arxiv.org/abs/2304.12477)；[作者全文 v4](https://arxiv.org/html/2304.12477v4) | 某些风险水平分解的最优化错误 | 会议年份在 arXiv 元数据中核对；本次阅读的是 2024 更新的 v4。不能解释成“所有 CVaR 增广状态 DP 都错误” |
| Mannor, S. & Tsitsiklis, J. N. (2011). Mean-Variance Optimization in Markov Decision Processes. ICML. [作者 PDF](https://www.mit.edu/~jnt/Papers/C-11-mv-MDP-ICML.pdf) | 均值–方差问题中历史和随机化政策类的影响 | 已核对原始摘要和策略类讨论；不声称仅扩大成两个矩状态即可普遍解决 |

## 关键论断与证据

| 论断 | 证据 | 可以写多强 |
|---|---|---|
| 期望目标只需条件均值 | 本报告的全期望推导与 SSP 平稳最优性 | 在已陈述 Markov 条件下成立；转移随机性保留 |
| 预算 DP 的三条递推 | 本报告分情况推导、增广状态来源、A 小例子精确检查 | 针对本模型正整数条件的推导；不声明原创通用算法 |
| 阈值搜索充分范围 | 目标≥y、可行上界 U、两个例子的有限支撑 | 可给严格充分界；不能只以未触顶作为证书 |
| 例子 1：26→23.9 | `results/` 和新增 DP 验证 | 小例子精确最优值 |
| 例子 2：26.5→24.4 | `results/` 和新增 DP 验证 | A 本地候选小例子的精确最优值 |
| 10 项 α 比较完全相等 | `results/budget_dp_exact.csv` | 参考 DP 与独立穷举、执行策略评价一致 |
| 20/20 模拟结果在 3SE 内 | `results/budget_policy_mc.csv` | 本次固定种子与参数模拟 SE 下的诊断；不保证一般覆盖率 |
| 最终网格收益与运行时间 | 当前无 A 独立证据 | 不写已验证结果，不声称秒级实测性能 |

未纳入模糊的 SSP 学习复杂度参考条目，也未把此前方案中未核实的精确文献编号当成已确认引用。正文不依赖这些条目。
