# E2 最终网格与绘图数据链核对

固定 C 提交 `94aac225b2d731a2c724de5fa0259efc2358816e`。结论与待修接口见 [网格验收报告](网格验收报告.md)。这不是 JSON→D 导出端到端验收通过：该流程仍有坐标类型问题，旧 D 导出器也未接入尾部补全。

## 复现

按上层 integration 的说明导出 C 固定代码到独立目录（包含 results 和 figures）；这里假定为 `/tmp/ssp-c-review-94aac22`。在仓库根目录运行：

```bash
python -m pip install -r a_validation/integration/grid/requirements.txt
python a_validation/integration/grid/check_grid_artifacts.py --c-source /tmp/ssp-c-review-94aac22
MPLCONFIGDIR=/tmp/ssp-mpl python a_validation/integration/grid/reproduce_grid_figures.py --c-source /tmp/ssp-c-review-94aac22
python a_validation/integration/grid/check_figure_data.py --c-source /tmp/ssp-c-review-94aac22
```

三个命令的 `--output`、`--tag` 必须相同。重现脚本不覆盖已有 tag；再次运行请使用新输出目录或新 tag。脚本核对生产模块、绘图脚本、提交 CSV/JSON 和原 PNG 的 SHA-256，不会静默改验其他版本。

## 验证范围

- 全部 25 组 E2：A 的独立预算递推、策略评价、首次越界尾部评价与提交 CSV 比较。
- Poster 策略 JSON：参数、动作表、初始阈值、fallback 等价性和 PMF CSV。
- F2 的众数路线、风险区域、PMF，F3 的 25 个红点／25 个蓝点及 α 标签。
- Poster 两策略在 cutoff=30/40/80/160/320 下补全后的均值与 CVaR。

只复跑 C 原 E2 不作为独立计算依据；`check_grid_artifacts.py` 自行组装线性方程、预算递推和尾部积分。`check_figure_data.py` 另外核对重现时实际传入 Matplotlib 的数据。已查看提交 PNG；原 PDF 的矢量对象未逐一解析。原 PNG 为 Matplotlib 3.9.2，重现环境为 3.11.2，不要求像素相同。

## 结果与交接

提交 `results/` 下的四份小型数值证据；图表和原始 artist 记录由上述命令生成，避免在 PR 重复保存整套原图。E9/E4 不在本轮独立验收范围。C/D 接口修复后需新增“JSON 重建环境→执行策略→导出补全指标”的回归检查。
