"""Small acyclic examples for checking the CVaR solver (experiment E0).

Acyclic means no state is ever visited twice, so every policy, including one
that looks at how much has been spent so far, can be listed, and the exact
distribution of the total cost Z can be written down path by path.

    python3 -m ssp.envs.acyclic   # print example 1 and check its reference values
"""

from __future__ import annotations

from ..mdp import SSP, make_outcomes
from ._checks import discrete_cvar as _cvar

S, M, G = 0, 1, 2
X, Y = 0, 1  # action indices at M


def example1() -> SSP:
    """Example 1 of the plan (section 4.3); its answers are known in advance.

    S -> M : no choice; 1 minute (90%) or 20 minutes (10%, a jam)
    M -> G : route X, 1 minute (90%) or 30 minutes (10%); or route Y, always 6 minutes
    With alpha = 0.9 the best choice at M depends on how long the first leg
    took, so the CVaR-optimal policy looks at history (see EXAMPLE1_REFERENCE).
    """
    return SSP(
        name="example1",
        state_names=["S", "M", "G"],
        start=S,
        goal=G,
        actions=[["go"], ["X", "Y"], []],
        outcomes=[
            [make_outcomes([(M, 1, 0.9), (M, 20, 0.1)])],
            [make_outcomes([(G, 1, 0.9), (G, 30, 0.1)]), make_outcomes([(G, 6, 1.0)])],
            [],
        ],
    )


# Exact answers for example 1, all at alpha = 0.9.
# The optimal budget is not unique: any integer y from 7 to 21 gives 23.9
# (the smallest, 7, is VaR_0.9 of the optimal policy's cost).  When checking a
# solver, compare the CVaR value, not y.  Starting from y = 7, the optimal
# policy reaches M with budget 6 after a 1-minute first leg (-> Y) or with
# budget -13 after a jam (over budget -> risk-neutral choice X).
EXAMPLE1_REFERENCE = {
    "alpha": 0.9,
    "cvar_always_X": 32.9,
    "cvar_always_Y": 26.0,       # best policy that looks only at the state
    "cvar_optimal": 23.9,        # 1-minute first leg -> Y, 20-minute first leg -> X
    "y_star_range": (7, 21),
}


def _cost_distribution(env: SSP, choose) -> dict[int, float]:
    """Exact {total cost: prob} of choose(state, spent) -> action index (acyclic env only)."""
    dist: dict[int, float] = {}

    def walk(s: int, spent: int, prob: float) -> None:
        if s == env.goal:
            dist[spent] = dist.get(spent, 0.0) + prob
            return
        for o in env.outcomes[s][choose(s, spent)]:
            walk(o.next_state, spent + o.cost, prob * o.prob)

    walk(env.start, 0, 1.0)
    return dist


def _self_check() -> bool:
    env, ref = example1(), EXAMPLE1_REFERENCE
    alpha = ref["alpha"]
    print(env.describe())
    print(f"\nExact CVaR_{alpha} of the total cost for every deterministic policy")
    print("(the choice at M may depend on the first leg: 1 or 20 minutes)")
    results = {}
    for after_1 in (X, Y):
        for after_20 in (X, Y):
            def choose(s, spent, a1=after_1, a20=after_20):
                return 0 if s == S else (a1 if spent == 1 else a20)

            dist = _cost_distribution(env, choose)
            results[(after_1, after_20)] = dist
            label = f"1 min -> {env.actions[M][after_1]}, 20 min -> {env.actions[M][after_20]}"
            mean = sum(z * p for z, p in dist.items())
            print(f"  {label:<24} mean {mean:6.2f}   CVaR {_cvar(dist, alpha):6.2f}")

    cvars = {key: _cvar(dist, alpha) for key, dist in results.items()}
    best = min(cvars, key=cvars.get)
    best_dist = results[best]
    rockafellar = {y: y + sum(p * max(z - y, 0) for z, p in best_dist.items()) / (1 - alpha)
                   for y in range(61)}
    flat = [y for y, v in rockafellar.items() if abs(v - cvars[best]) < 1e-9]
    print(f"\n  budgets y giving {cvars[best]:.2f} for the optimal policy: {flat[0]} to {flat[-1]}")

    checks = {
        "always X": abs(cvars[(X, X)] - ref["cvar_always_X"]) < 1e-9,
        "always Y": abs(cvars[(Y, Y)] - ref["cvar_always_Y"]) < 1e-9,
        "optimum": best == (Y, X) and abs(cvars[best] - ref["cvar_optimal"]) < 1e-9,
        "y range": flat == list(range(ref["y_star_range"][0], ref["y_star_range"][1] + 1)),
    }
    for name, ok in checks.items():
        print(f"  reference {name:<9} {'OK' if ok else 'MISMATCH'}")
    return all(checks.values())


if __name__ == "__main__":
    raise SystemExit(0 if _self_check() else 1)
