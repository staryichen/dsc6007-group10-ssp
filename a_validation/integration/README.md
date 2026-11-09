# A 对 C PR #3 的独立验收

验收固定提交：`94aac225b2d731a2c724de5fa0259efc2358816e`。结论见 [验收报告](验收报告.md)。本目录不复制 C 的生产代码，也不改变基础 `run_all.py` 的参考验证含义。

## 范围

- 两个无环例子、五个 α、请求 B=0／64，共 20 项正式策略精确核对。
- 由 A 执行 C 返回的策略，以 A 的精确分数路径枚举建立标准答案；不用 C 的穷举／指标／模拟自查函数建立标准答案。
- 核对 D 的完整 PMF、预算适配器和 C 尾部补全的均值／CVaR。
- 实际轨迹 2,000,000 条，20/20 个种子案例落在本次估计 3SE 内，偏差原样记录。
- C 原有 7 组回归测试另外复跑通过，日志单独保留，不与 A 独立检查混算。

尚未独立验收全部 E2/E9/E4、最终网格图表、集成后的最新代码或例子 2 的正式环境归属。源码一旦变更，当前结果不会自动适用于新提交。

## 复现

在包含本 PR 的仓库根目录，准备 C 固定提交的独立源码目录。下面只导出源码，不合并分支：

```bash
git fetch origin refs/pull/3/head:refs/remotes/origin/review-c-pr3
mkdir -p /tmp/ssp-c-review-94aac22
git archive 94aac225b2d731a2c724de5fa0259efc2358816e | tar -x -C /tmp/ssp-c-review-94aac22
python -m pip install -r a_validation/integration/requirements.txt
python a_validation/integration/verify_c.py --c-source /tmp/ssp-c-review-94aac22
```

导出目录应为空或仅包含该固定提交。脚本会核对 C `ssp/` 源码 SHA-256，版本不同则报错，不会静默使用当前 dev。也可以用 `--output /tmp/ssp-c-review-results` 指定新的结果目录以保留旧结果。

模拟用 seed=0…9，每个 100,000 条；经验 CVaR 标准误来自已知精确 PMF 下 20,000 次多项分布重复模拟。3SE 是诊断，不是严格覆盖保证。环境版本记录于 `c_source_hashes.json`。

## 文件

- `verify_c.py`：独立验收入口；共享 A 的 `../exact.py`。
- `c_source_hashes.json`：固定 C 源码摘要和运行环境。
- `results/c_exact.csv`：20 项精确比较。
- `results/c_mc.csv`：20 个模拟案例。
- `results/c_actual_policies.json`：C 的实际策略、fallback 和 A 精确分布。
- `results/summary.json`：范围明确的验收状态。
- `a_independent_review.log`：A 独立检查日志。
- `c_original_tests.log`：C 原有回归测试日志。
