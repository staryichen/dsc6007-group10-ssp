# 报告合并稿修改意见（11-22）

核对依据：

- §5.0 对照 `ssp/envs/grid.py` 和环境实际生成的转移表；
- §5.3 对照 `results/e3_phase_v1.csv`、`results/e2_alpha_sweep_v3.csv` 和 F4、F5 两张图；
- 复现：在干净副本里按 README 顺序跑完全部命令，均通过；报告引用的 csv 都能重跑出相同数值（E4 的运行时间随机器变化）。

每条都给了原句和改成的句子，可以直接复制。

## 清单

- [ ] 1. §5.0 打滑那句（写错了，必须改）
- [ ] 2. §5.0 适用范围（E4 不是 10×10）
- [ ] 3. §5.0 随机来源的个数
- [ ] 4. §5.0 坐标从 0 开始数（可选）
- [ ] 5. §5.3 q = 0 那句
- [ ] 6. §5.3 "0–3 minutes"
- [ ] 7. §5.3 补一句解释（可选）
- [ ] 8. §5.1 "pending" 那句
- [ ] 9. §6 扩展缺"理论"一类
- [ ] 10. 排版清理
- [ ] 11. §0 交付物里的 demo mp4
- [ ] 12. 代码提交的分支和文件命名
- [ ] 13. §7 加一行分工

---

## §5.0 Environment

### 1. 打滑（写错了，必须改）

代码是在 4 个方向里均匀随机选一个，可能选回原方向，所以原方向的总概率是 1 − p + p/4（p = 0.1 时是 0.925）。原文写成了"换成原方向以外的一格"。

原句：

```text
With probability p the move goes to a uniformly chosen neighbouring cell instead of the intended one; a move into the boundary keeps the agent in place.
```

改成：

```text
With probability p the chosen direction is replaced by one of the four directions drawn uniformly at random, possibly the chosen one, so the intended move happens with probability 1 − p + p/4 and each other direction with probability p/4. A move into the boundary keeps the agent in place and still costs a step.
```

### 2. 适用范围

E4 用了 20×20 和 40×40 的网格，起点、终点和拥堵区都按网格尺寸放大，所以"所有实验都是 10×10"不准确。

原句：

```text
All grid experiments use one environment, `ssp/envs/grid.py`. The map is a 10×10 grid of cells.
```

改成：

```text
All grid experiments use the environment in `ssp/envs/grid.py`. The map is a 10×10 grid of cells; the scaling runs in §5.4 enlarge the same layout, scaling the start, goal and jam zone with the grid size.
```

### 3. 随机来源的个数

除了打滑和拥堵，每步 1 分钟还是 2 分钟的基础代价也是随机的。

原句：

```text
Two independent random mechanisms act on every step:
```

改成：

```text
Besides the random base cost below, two independent random mechanisms act on every step:
```

### 4. 坐标从 0 开始数（可选）

不说明的话，读者可能把"第 4 行"理解成从 1 开始数。

原句：

```text
The agent starts at row 4, column 0 and must reach row 4, column 9.
```

改成：

```text
Rows and columns are numbered from 0; the agent starts at row 4, column 0 and must reach row 4, column 9.
```

---

## §5.3 E3

表里 25 格的数字、α 那段的 0.55 / 5.13 / 8.17 / 10.46 / 16.47、F4 的 13 个红框都和数据一致，只改措辞。

### 5. q = 0 那句

两处不准确：q = 0 时基础代价仍然是随机的，不只剩打滑；p = 0.3 那格的增益是 0.001 分钟，两个策略走的路线相同，但不是完全相同的策略。

原句：

```text
At q = 0 the jam multiplier never fires, the only randomness left is slip, and both objectives select the same policy, with zero gain throughout the column.
```

改成：

```text
At q = 0 the jam multiplier never fires, the only randomness left is slip and the 1-or-2-minute base cost, and both objectives follow the same route, with essentially zero gain (at most 0.001 minutes) throughout the column.
```

### 6. "0–3 minutes"

这一档的最大增益是 3.146 分钟。

原句：

```text
At q = 0.2 and 0.3 the gain collapses to 0–3 minutes,
```

改成：

```text
At q = 0.2 and 0.3 the gain collapses to at most about 3 minutes,
```

### 7. 补一句解释（可选）

文中没解释为什么 q = 0.2、0.3 时增益随 p 变大。按两种策略的典型路线看：均值最优的绕行路线离拥堵区只隔一行，p ≥ 0.1 时 CVaR 策略多走两步、隔两行。可以补在 "The ridge dies at high q" 那段后面：

```text
At q = 0.2 and 0.3 the remaining gain grows with p: the mean-optimal detour runs one row from the jam zone, where a slip can still push it into a jam, while for p ≥ 0.1 the CVaR-optimal policy keeps two rows away at the cost of two extra steps (modal trajectories).
```

---

## §5.1 E0

### 8. "pending" 那句

例子 2 已经收进共享环境，`report/C_sections.md` 已在这次的 PR 里同步改了，合并稿也要改。

原句：

```text
The second environment is A's candidate and remains pending shared-environment adoption.
```

改成：

```text
Both examples are defined in the shared environment module (`ssp/envs/acyclic.py`); the second was designed by A.
```

---

## 其他

### 9. §6 扩展缺"理论"一类

评分要求结论里的扩展分理论、算法、应用三类。现在的三条是更细的相图、Q-learning、路网，缺理论方向，可以加一句嵌套 CVaR 或 adaptive SSP。

### 10. 排版清理

- §2–§3 的公式分隔符丢了，`(\mathcal S)` 这类会原样显示，要改回 `$…$`；
- 全文有 `\---`、`\_`、`\[` 这类转义残留；
- §0 的中文元信息表、§5.4 的中文注释和 HTML 注释，定稿前删掉或换成英文；
- 图号要重排，现在只有 F2–F5 和 F7；
- 排成 PDF 后再看是否超过 15 页。

### 11. §0 交付物里的 demo mp4

原计划的 demo 是 Q-learning 训练前、中、后的录像。Q-learning 没做的话，这一项要删掉或者另定。项目说明里 demo 是可选的。

### 12. 代码提交

- 报告写的是 `dev` 分支，提交前合进 `main`，或者写明 commit 号；
- zip 里的代码文件按 `Group_10_c_文件名.txt` 命名。

### 13. §7 加一行分工

E7 路网按报告写成了 future work。建议在 §7 加一行分工：A 理论和验证例子，B 环境、E3 相图和复现检查，C 求解器和 E0 / E2 / E4 / E9，D 分布计算，E 整合和写作。
