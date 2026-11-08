"""Exact helpers used only by the environments' self-checks (not part of the solvers)."""

from __future__ import annotations


def discrete_cvar(dist: dict[int, float], alpha: float) -> float:
    """CVaR_alpha: mean of the worst (1 - alpha) share of a discrete cost distribution."""
    tail, acc, total = 1 - alpha, 0.0, 0.0
    for z, p in sorted(dist.items(), reverse=True):
        take = min(p, tail - acc)
        if take <= 0:
            break
        total += take * z
        acc += take
    return total / tail


def add_independent(d1: dict[int, float], d2: dict[int, float]) -> dict[int, float]:
    """Distribution of X1 + X2 for independent discrete X1 ~ d1 and X2 ~ d2."""
    out: dict[int, float] = {}
    for z1, p1 in d1.items():
        for z2, p2 in d2.items():
            out[z1 + z2] = out.get(z1 + z2, 0.0) + p1 * p2
    return out
