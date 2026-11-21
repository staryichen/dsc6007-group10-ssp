"""Toy examples from section 2 of the plan, in the shared SSP format.

Each toy has one decision: at S pick an action, then arrive at G.  The total
cost Z is the cost of that single step, so means and CVaRs can be checked by
hand (experiment E1).

    python3 -m ssp.envs.toy      # print the tables and run the self-check
"""

from __future__ import annotations

import numpy as np

from ..mdp import SSP, make_outcomes

S, G = 0, 1


def _one_step(name: str, options: dict[str, list[tuple[int, float]]], params: dict) -> SSP:
    """S --(chosen option)--> G; each option is a list of (cost, prob)."""
    return SSP(
        name=name,
        state_names=["S", "G"],
        start=S,
        goal=G,
        actions=[list(options), []],
        outcomes=[[make_outcomes((G, c, p) for c, p in dist) for dist in options.values()], []],
        params=params,
    )


def two_route(fast: int = 1, closed: int = 100, p_closed: float = 0.1, detour: int = 12) -> SSP:
    """Bridge vs detour, the poster example.

    bridge: `fast` minutes, or `closed` minutes with probability `p_closed`
            (default 1 or 100 minutes, mean 10.9);
    detour: always `detour` minutes (default 12).
    Risk-neutral picks the bridge; CVaR_0.9 picks the detour (100 vs 12).
    """
    return _one_step(
        "toy_two_route",
        {"bridge": [(fast, 1 - p_closed), (closed, p_closed)], "detour": [(detour, 1.0)]},
        dict(fast=fast, closed=closed, p_closed=p_closed, detour=detour),
    )


def same_mean() -> SSP:
    """Same mean, different tails: A = 10 (90%) or 20 (10%); B = always 11.

    Both means are 11; CVaR_0.9 is 20 for A and 11 for B.
    """
    return _one_step("toy_same_mean", {"A": [(10, 0.9), (20, 0.1)], "B": [(11, 1.0)]}, {})


def occasional_fast() -> SSP:
    """Variance vs CVaR: C = 11 (90%) or 1 (10%); B = always 11.

    C is sometimes much faster: mean 10 vs 11 and variance 9 vs 0, but its
    worst 10% is still 11 minutes, so CVaR_0.9 is 11 for both.  A variance
    penalty prefers B; CVaR does not.  The plan describes this example
    without numbers; these are a suggestion and can be changed.
    """
    return _one_step("toy_occasional_fast", {"C": [(11, 0.9), (1, 0.1)], "B": [(11, 1.0)]}, {})


def all_toys() -> list[SSP]:
    return [two_route(), same_mean(), occasional_fast()]


def _self_check(n_samples: int = 100_000, seed: int = 0) -> None:
    """Print each table, then compare exact and sampled mean cost of every action."""
    rng = np.random.default_rng(seed)
    for env in all_toys():
        print(env.describe())
        for k, action in enumerate(env.actions[S]):
            draws = np.array([env.sample(S, k, rng)[1] for _ in range(n_samples)])
            proper = env.is_proper([k, -1])
            print(f"  {action:<8} mean {env.mean_cost(S, k):6.2f}   "
                  f"sampled mean {draws.mean():6.2f}   proper {proper}")
        arrays = env.to_arrays()
        print(f"  to_arrays: P shape {arrays.P.shape}, cbar {arrays.cbar.ravel()}")
        print()


if __name__ == "__main__":
    _self_check()
