"""统一绘图风格。

所有实验脚本通过本模块设置 rcParams，不单独配置。颜色常量见 ``C``：
``mean`` 对应风险中性，``cvar`` 对应 CVaR 最优，``bar`` 用于中性填充，
``hi`` 用于强调。
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

C = {"mean": "#1f77b4", "cvar": "#d62728", "bar": "#7f7f7f", "hi": "#2ca02c"}


def setup(where="poster"):
    """按输出场景设置 rcParams，返回建议画布尺寸。

    where 取 ``poster``（A0 横版，默认）、``slides`` 或 ``report``。
    返回值单位为英寸，供 ``plt.subplots(figsize=...)`` 使用。
    """
    if where == "poster":
        figsize, base = (7.2, 4.2), 20
    elif where == "slides":
        figsize, base = (6.0, 3.5), 15
    else:
        figsize, base = (3.4, 2.5), 9
    plt.rcParams.update({
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "font.size": base,
        "axes.titlesize": base + 2,
        "axes.labelsize": base,
        "xtick.labelsize": base - 2,
        "ytick.labelsize": base - 2,
        "legend.fontsize": base - 2,
        "lines.linewidth": 2.0,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 150,
    })
    return figsize


def save(fig, stem):
    """保存为 png（300 dpi，用于预览）与 pdf（矢量，用于 poster 与报告）。

    ``stem`` 不含后缀，例如 ``figures/f2_routes``。
    """
    fig.savefig(stem + ".png", dpi=300, bbox_inches="tight")
    fig.savefig(stem + ".pdf", bbox_inches="tight")
