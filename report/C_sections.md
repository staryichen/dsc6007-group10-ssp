# C: Algorithms and experimental results

## 4.1 Expected-cost optimization

We use the joint outcome table P(s',c|s,a) shared by all environments. For the expected-cost objective, each action has mean immediate cost cbar(s,a)=sum P(s',c|s,a)c. Its transition probabilities remain stochastic. The Bellman update is T_gamma V(s)=min_a sum P(s',c|s,a)[c+gamma V(s')], with V(G)=0. The primary SSP objective uses gamma=1; discounted values are computed only for E9.

Value iteration starts from zero and stops when the maximum consecutive-iterate difference is below 1e-10. At gamma=1 this is a numerical stopping criterion, not a contraction-based error bound. We therefore independently compare values with policy iteration and linear programming. Policy iteration starts from a proper policy: assign graph distance to the goal and select an action maximizing the probability of a strictly closer successor. Every non-goal closed communicating class would have a minimum-distance state with a positive-probability exit, contradicting closure. Evaluation solves (I-gamma P_mu)J=cbar_mu using sparse linear algebra. Policy improvement preserves the current action on numerical ties. The LP maximizes sum_s V(s), subject to V(s)<=cbar(s,a)+gamma sum P(s'|s,a)V(s') and V(G)=0.

Before undiscounted evaluation, we identify states that cannot reach the goal under the policy, then mark all their predecessors as having infinite expected cost. Remaining states are evaluated separately. This avoids confusing global improperness with infinite cost from a particular start. All action matrices are sparse; a Bellman sweep costs O(M), where M is the number of joint outcome entries. Sparse linear-solve and LP costs depend on sparsity and conditioning; no linear complexity claim is made for them.

```text
VI: V <- 0
repeat: U <- T_gamma V; delta <- max|U-V|; V <- U
until delta < tolerance; return V and greedy policy

PI: mu <- proper initial policy
repeat: J <- solve policy equations; mu_new <- greedy(J), preserving ties
until mu_new = mu; return J, mu

LP: maximize sum V subject to all Bellman upper inequalities and V(G)=0
```

## 4.2 Static CVaR optimization

For integer remaining budget b, W(s,b) is the minimum expected excess of the remaining total cost above b. We use W(G,b)=max(-b,0), W(s,b)=J*(s)-b for b<=0, and W(s,b)=min_a sum P(s',c|s,a)W(s',b-c) otherwise. Strictly positive integer costs ensure that every dependency is on a smaller budget. The recurrence is computed once in increasing budget order.

The optimal objective is min_y {y+W(s0,y)/(1-alpha)}. Since total costs are integer, searching integer thresholds suffices. The pointwise minimum across policies need not be convex in y. Thus an interior minimizer on a finite search interval alone does not certify global optimality. Our implementation expands the interval until B+1 exceeds the best objective: every unsearched integer y>=B+1 has objective at least y because W>=0. This gives a global search certificate, subject to floating-point evaluation. A resource limit causes an explicit failure rather than an uncertified optimum.

```text
J*, mu_mean <- expected-cost solver
W[:,0] <- J*; mu[:,0] <- mu_mean
for b = 1,...,B:
  for nonterminal state s:
    W[s,b], mu[s,b] <- minimum expected continuation over actions
choose y minimizing y + W[s0,y]/(1-alpha)
if B+1 does not exceed this value: expand B and continue
execute mu[s,b]; update b <- b - observed_cost
if b<=0: execute mu_mean[s]
```

The budget recurrence costs O(BM) time and O(B|S|+M) storage, excluding the initial mean solve. The output is a policy on (state, remaining budget), not a single fixed path. Action ties may produce different mean costs while preserving the same optimal CVaR; we do not impose a secondary mean-minimization objective.

### Distribution integration

We retain D's forward-propagation PMF and explicitly account for its omitted tail. At the first crossing of cutoff L into state s with spent cost z>L and probability mass m, the policy has already switched to its proper stationary fallback. The contribution to E[Z;Z>L] is therefore m(z+J_fallback(s)). Summing these contributions provides the exact residual first moment, up to floating-point arithmetic. If VaR=v<=L, the CVaR excess numerator is sum_{z<=L}p(z)(z-v)^+ + E[Z;Z>L] - v Pr(Z>L). No renormalization or placement of overflow mass at L is used. The plotted PMF is still truncated, even though its reported mean and CVaR include the tail.

## Verification

Production policies, rather than A's reference policies, were executed and checked. For two acyclic examples and alpha in {0.5,0.8,0.9,0.95,0.99}, all 10 budget-DP values equal exhaustive history-dependent policy optima and independently evaluated policy values within 1e-9. At alpha=0.9 the values are 23.9 and 24.4; mean optima are 6.8 and 7.75. The second environment is A's candidate and remains pending shared-environment adoption.

Each example was also simulated for 100,000 trajectories under each of seeds 0–9. All 20 empirical CVaR estimates lie within three estimated standard errors. The standard error is computed using 20,000 multinomial replications of the exact policy distribution, including empirical quantile changes. This is a stochastic diagnostic, not a proof. Exact enumeration is the primary correctness check. Seven regression test groups additionally cover 20 random acyclic models, improper policies, a geometric infinite tail, solver crosschecks, invalid inputs, and an insufficient-budget interior-minimum counterexample.

## E2: risk-return tradeoff

The shared 10x10 grid uses q=0.1, delay multiplier 10 and p_slow=0.2. We sweep p in {0,0.05,0.1,0.2,0.3} and alpha in {0.5,0.8,0.9,0.95,0.99}, without changing the environment to obtain a desired result. All 25 cases pass distribution/solver agreement checks. VI/PI/LP differ by less than 1e-8; at p=0 the expected-cost values also agree with Dijkstra using mean edge costs. The largest CVaR evaluation/DP difference is approximately 7.1e-15.

| p | Mean-optimal E[Z] | Its CVaR_0.9 | CVaR-policy E[Z] | Optimal CVaR_0.9 |
|---|---:|---:|---:|---:|
| 0 | 15.1200 | 31.7099 | 18.1056 | 20.8426 |
| 0.05 | 16.1621 | 33.2729 | 19.1024 | 23.9888 |
| 0.1 | 17.2797 | 34.9988 | 20.3226 | 26.8317 |
| 0.2 | 19.8363 | 39.1224 | 23.8187 | 32.6632 |
| 0.3 | 23.0160 | 44.7495 | 27.5435 | 39.7146 |

At p=0.1, optimizing CVaR_0.9 reduces the worst-decile mean by about 8.17 minutes while increasing expected cost by about 3.04 minutes. The modal trajectory changes from the shortcut to a detour. These are representative trajectories obtained by following the most probable joint outcome at each step; actual actions adapt to realized cost and slips. They are not claims that the controller follows a fixed route.

In the observed sweep the mean cost of the selected CVaR policy is nondecreasing with alpha, with plateaus and discrete route changes. This is an empirical observation, not a monotonic-policy theorem. At p=0.3 and alpha=0.5 the modal path remains the 9-step shortcut; at alpha=0.8 it takes a 15-step detour. At p=0, some equal-CVaR policy choices spend additional budget on outcomes that remain below the tail threshold. Hence the selected policy's mean need not equal the fixed detour's mean 18. This reflects nonuniqueness and tie breaking, not an improvement in CVaR beyond the optimum.

F2 caption: Mean-optimal and CVaR_0.9-optimal policies on the shared grid (p=0.1). Left: modal representative trajectories; grey cells have random delays. Right: their cost PMFs (display cropped to 90 minutes; propagation cutoff 160). Overflow and residual first moments are retained in the CSV; reported risk metrics include residual costs.

F3 caption: Expected cost versus CVaR at each annotated alpha, with separate panels for slip probabilities. Red circles are optimized policies; blue crosses evaluate the mean-optimal policy at the corresponding alpha. Points across different alpha use different tail fractions and are not a single fixed-risk Pareto frontier.

Sources: `results/e2_alpha_sweep_v3.csv`, `e2_solver_checks_v3.csv`, `e2_poster_pmf_v3.csv`.

## E9: discounting changes the objective

| p | True optimum (gamma=1) | True cost of gamma=0.99 policy | True cost of gamma=0.9 policy | gamma=0.9 excess |
|---|---:|---:|---:|---:|
| 0 | 15.1200 | 15.1200 | 18.0000 | 19.05% |
| 0.05 | 16.1621 | 16.1621 | 19.0749 | 18.02% |
| 0.1 | 17.2797 | 17.2797 | 20.2557 | 17.22% |
| 0.2 | 19.8363 | 19.8363 | 23.0277 | 16.09% |
| 0.3 | 23.0160 | 23.0275 | 26.5221 | 15.23% |

All policies in this grid sweep are proper. The gamma=0.99 gap is zero at the first three p values, about 7.83e-7 minutes at p=0.2, and 0.01148 minutes at p=0.3. Gamma=0.9 raises true expected cost by 15.23–19.05%. Thus a lower discounted objective is not evidence of a lower undiscounted cost. In this environment discounting can choose a longer detour; the experiment does not establish that discounting always chooses a spatially riskier route. An independent regression fixture demonstrates a discounted optimum that loops forever and is correctly assigned infinite undiscounted cost, but that fixture is not presented as a grid finding.

Source: `results/e9_discount_comparison_v1.csv`.

## E4: optional scaling

All nine combinations of 10x10, 20x20, 40x40 grids and B=128,256,512 completed. At B=512, median times over three runs, including the mean solve, are approximately 0.045, 0.146 and 0.698 seconds. The 40x40 W/action tables occupy 13,132,800 bytes (about 12.5 MiB); this excludes other arrays and process overhead. At fixed state count, time rises with B but includes setup and linear-solve costs, so doubling B need not double total runtime. These local timings do not establish performance on larger or ill-conditioned models. The implementation avoids dense |S| squared action matrices.

Source: `results/e4_scaling_v1.csv`, including Python/library/platform versions and minimum/maximum timings. F7 plots these measured medians.
