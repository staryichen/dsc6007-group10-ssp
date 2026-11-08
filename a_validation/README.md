# A：独立验证与理论材料

本目录用于 A 的课程项目工作：精确验证小型无环例子，核对固定版本的分布接口，并提供报告理论初稿。**现已补充 C 提交 `94aac22` 在两个无环例子上的正式策略独立验收；E2 数值与绘图数据已核对，JSON→D 导出和全范围集成仍待完成。** 新证据与复现入口见 [integration/README.md](integration/README.md)。

## 运行

本次验证环境为 Python 3.11.9、NumPy 2.4.6。在仓库根目录：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r a_validation/requirements.txt
python a_validation/run_all.py
```

无需 GPU，不需要联网获取数据；安装依赖后所有计算在本地进行。完整运行会执行两个例子各 10 个种子、每个 100,000 条的模拟。只看精确结果可单独运行 `python a_validation/exact.py`、`python a_validation/verify_e1.py` 或 `python a_validation/example2.py`。

## 文件

| 文件 | 用途 |
|---|---|
| exact.py | 精确分数概率、完整路径枚举、VaR/CVaR，以及例子 1 的四策略验证 |
| example2.py | 五状态候选环境与八策略精确结果 |
| verify_e1.py | E1 六动作手算值及固定 D 分布接口核对 |
| check_budget_dp.py | A 的无环图参考预算 DP、五个风险水平与穷举比较、模拟 |
| test_regressions.py | 六组防错测试，含 60 个随机小型 DAG 对照 |
| run_all.py | 统一运行入口 |
| results/ | 可重新生成的结果和日志 |
| docs/对齐清单.md | 提交范围与 B/C/D/E 待确认事项 |
| docs/ | 报告 §2–§3、中文推导、来源说明、poster 图文源稿 |
| reference/ | 独立复现用的固定参考代码；不覆盖仓库顶层 ssp |

## 当前结果

- 例子 1：最优期望 6.8；最优 CVaR₀.₉ 23.9；只看位置时最优 CVaR 26。
- 例子 2：最优期望 7.75；最优 CVaR₀.₉ 24.4；只看位置时最优 CVaR 26.5。
- 两例×五个 α 的 10 项参考 DP、独立穷举和执行策略评价精确一致。
- 20 个轨迹模拟案例的经验 CVaR 均在本次估计的 3 个标准误内。标准误来自已知精确 PMF 下 20,000 次多项分布重复模拟；约 −0.05 的有限样本偏差仍保留。这是诊断，不是通用置信覆盖保证。

## 参考代码与独立性

`reference/ssp` 来自 D 的提交 `22675a2933b9011127bddf5c04f9cdbfc0f5f98c`，包含 B 的环境。例子 1 的原始环境来源为 B 的提交 `0a66eb1d8d3874d853d374d105ea90f28fb39b1f`。参考副本保留原样，未进行中文化或算法修改。来源校验见 `reference/source_manifest.json`。

独立标准答案不调用 B/D 的参考常量或自查计算函数。使用共享环境定义，在 A 的代码中以分数展开路径并比较变分式与直接尾部计算；D 的输出作为待核对对象。A 的预算 DP 与穷举是不同求解流程，但共用精确指标评价代码。

没有修改仓库根目录的 ssp、requirements 或他人模块。固定快照允许这个 PR 在 B/D 尚未合并时独立复现，之后若迁移到共享环境，需重跑验证，不能直接删除 reference 后声称已对齐。

## 适用范围及待办

参考 DP 只支持有限无环模型，并要求预算覆盖完整总代价支撑；不能直接用于有环网格。例子 2 仍为 A 候选。C 的两个无环例子已按其实际返回策略独立检查，E2 数值、尾部补全和绘图数据已核对，JSON→D 导出接口及最终组内集成待修复复验。展示材料为源稿，尚未排成最终 poster／slides。报告引用和页数以全组模板为准。

## E2 网格核对更新

C 固定提交 94aac22 的 25 组数值、F2/F3 绘图数据及尾部补全已独立核对，见 [网格报告](integration/grid/网格验收报告.md)。发现 JSON 坐标类型导致载入失败；D 旧导出入口也尚未接入尾部补全，因此端到端交接不标为通过。E9/E4 未独立重跑。
