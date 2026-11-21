# D: poster distribution handoff

Run from repository root (NumPy and Matplotlib required):

```powershell
python -m experiments.run_dist_demo --tag v1
```

Use a fresh tag for each revision. Outputs: `figures/d_toy_<tag>.png/.pdf`,
`figures/d_grid_fixed_<tag>.png/.pdf`, and corresponding PMF and metric CSVs
under `results/`. Computation is deterministic: no sampling or seed is used.

## What can be used now

The toy figure is a verified comparison: bridge mean 10.9, CVaR(0.9) 100;
detour mean and CVaR both 12. Suggested caption:

“A small expected-cost advantage (10.9 vs 12 minutes) hides a much larger
worst-decile cost (100 vs 12 minutes).”

The grid figure compares **fixed routes at p=0**, not optimized policies.
Straight: mean 15.12, CVaR approximately 31.71. Detour: mean 18,
CVaR approximately 20.84. Both distributions have zero overflow at cutoff 400.
Do not label this figure as the final stochastic-transition solver comparison.

## C handoff

`cost_distribution(env, policy, z_max)` accepts a full-state action array or
`policy(state, spent_cost)` callable. `budget_policy(table, y, fallback)` adapts
a full-state budget table with axes `[original_state, remaining_budget]` and
columns 0 through y; nonpositive budget uses the mean-optimal fallback.
The goal entry is ignored. Arrays excluding the goal must first be mapped via
`env.to_arrays().states`. Never use a negative remaining budget as an array index.

Optional JSON integration:

```text
{
  "grid": {"p": 0.1, "q": 0.1, "delay": 10, "p_slow": 0.2},
  "alpha": 0.9,
  "initial_budget": <integer>,
  "mean_policy": <full-state action array>,
  "budget_policy": <full-state two-dimensional action array>,
  "cutoff": 2000
}
```

Run `python -m experiments.run_dist_demo --tag v2 --policy-json policies.json`.
This exports solver distributions, but does not independently certify policy
optimality. Compare against C's VI and budget-DP objective values before release.

## Truncation and release gate

Forward propagation conserves terminal mass plus first-crossing overflow.
Integer costs avoid projection; runtime is O(cutoff * number of outcome entries),
memory O(cutoff * states). Policies must depend only on state and spent cost.

`risk_metrics` intentionally rejects distributions with any overflow. For a
cyclic environment, increasing cutoff need not yield literally zero overflow.
Metric CSV cells are then blank, rather than silently normalizing or claiming
exact CVaR. Before the final p>0 poster comparison, add a justified residual
cost bound or exact residual expectation using C's proper fallback policy,
and compare metrics with solver objectives. Small overflow alone is not an
error bound on a mean or CVaR. This is the remaining integration work with C.

Verification embedded in the command covers all four history strategies in
example 1, the budget adapter (23.9), invalid actions, known grid results,
and a cyclic geometric distribution with analytically known overflow.
