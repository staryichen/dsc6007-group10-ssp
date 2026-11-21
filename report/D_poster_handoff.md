# D poster handoff — verified 2026-11-08

## Files for E

- Final distribution + survival figure: `figures/d_poster_v1.pdf` (preferred for layout), `.png` (preview).
- Routes are already supplied by C in `figures/f2_routes_v3.pdf`; coordinate with E to avoid repeating the distribution panel.
- Values: `results/d_poster_v1_metrics.csv`.
- Full retained PMF: `results/d_poster_v1_pmf.csv`.
- Checks/provenance: `results/d_poster_v1_checks.csv` and `results/d_poster_v1_verification.json`.

## Poster table (minutes)

| Policy | Mean | VaR 0.9 | CVaR 0.9 |
|---|---:|---:|---:|
| Mean-optimal | 17.28 | 29 | 35.00 |
| CVaR-optimal | 20.32 | 24 | 26.83 |

Suggested English caption:

**Risk-sensitive routing reduces worst-decile cost.** On a 10×10 grid with
slip probability p=0.1 and delay probability q=0.1, optimizing CVaR at alpha=0.9
reduces CVaR from 35.00 to 26.83 minutes (23.3%), while expected cost rises
from 17.28 to 20.32 minutes (17.6%). The CVaR policy adapts to remaining budget,
starting at 24 minutes. The right panel shows P(Z>x) on a logarithmic scale.

中文讲解：风险敏感策略将最坏 10% 情况下的平均总代价降低约 23.3%，
代价是总体平均时间增加约 17.6%。策略会根据已花费的时间调整动作。

Model: gamma=1, p_slow=0.2, delay multiplier=10, start=(4,0), goal=(4,9),
risky cells rows 2–6 / columns 3–6. Costs and transitions use B's environment.
Policies and residual-mean completion use C's implementation at commit 94aac22;
D supplies independent forward-distribution checks, integration and these figures.

## Numerical qualification

PMF is retained through 160 minutes, not an infinite-support complete PMF.
Overflow probabilities: mean policy 2.82531e-13, CVaR policy 6.47397e-15.
Mean and CVaR include residual first moments using the proper stationary
fallback; no renormalization is used. At a first crossing (s,z), the tail
contribution is crossing probability times (z+J_fallback(s)). Since the
cutoff covers the initial budget and VaR, the same first moment completes CVaR.

Figure display ends at 73 minutes to show the distributions clearly; data CSV
retains 0–160. The logarithmic panel displays probabilities down to 1e-5.
These display limits do not truncate the metric calculations.

Recomputed mean objective differs from VI by 3.57e-12; CVaR agrees with
budget DP at displayed machine precision. Doubling cutoff to 320 changes
neither mean nor CVaR at the recorded precision. D's retained PMF and overflow
agree with C's propagation. Seven solver regression tests also passed locally.
No new Monte Carlo claim is made; these checks are deterministic.

## Reproduction

From repository root with requirements installed:

```powershell
python -m unittest discover -s tests -v
python -m experiments.run_d_poster --tag v2
```

Use a fresh tag. No GitHub push, PR creation, or remote merge is performed by
the experiment. Local D branch now includes C's commit as a dependency;
review D's new integration changes separately from C's original work.
