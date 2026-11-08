# Sections 2–3: Background and theory

Working draft for the DSC6007 course report. These sections explain established methods and their specialization to the project's integer-cost SSP. They do not claim a new risk measure or a new general CVaR algorithm. The small-example results are reproducible in `../`; optimized grid results are outside this draft.

## 2. Background

### 2.1 Stochastic shortest paths

We consider a finite stochastic shortest path (SSP) model with state space \(\mathcal S\), finite available action sets \(\mathcal A(s)\), initial state \(s_0\), and absorbing goal \(G\). An action generates a next state and a cost according to the joint kernel \(P(s',c\mid s,a)\). Each state-action pair has finitely many joint outcomes, as in the environment's outcome tables; stage costs are therefore bounded. All nonterminal costs are positive integers measured in minutes. Entering the goal may incur a positive cost; after arrival no further cost is incurred. This convention matches the environment interface, where the goal has no available actions.

Let \(T\) be the first arrival time at the goal. We optimize the undiscounted total cost

\[
Z=\sum_{t=0}^{T-1}C_t,\qquad \gamma=1.
\]

A policy may depend on the observed history, including previous realized costs. We assume that the conditional law of \((S_{t+1},C_t)\), given that history and the current action, is the specified kernel at \((S_t,A_t)\). Thus previous delays do not reveal an unobserved persistent congestion variable. Such information would require an enlarged physical state or a belief-state model.

For stationary policies, properness means reaching the goal from every nonterminal state with probability one and finite expected arrival time. The classical finite SSP framework assumes (A1) existence of a proper policy and (A2) infinite expected cost from at least one state for every improper stationary policy. Positive costs ensure that an infinite expected arrival time entails infinite expected cost. Under the standard SSP conditions, the risk-neutral Bellman equation has a unique finite solution with goal value zero, and value iteration converges from any finite initialization with that boundary condition. An optimal proper stationary policy exists. These statements concern expected cost, not static CVaR. [Bertsekas and Tsitsiklis, 1991](https://www.mit.edu/~jnt/Papers/J034-91-berts-SSP.pdf)

### 2.2 Expected-cost optimization and course connections

Writing \(\bar c(s,a)=\sum_{s',c}P(s',c\mid s,a)c\), the risk-neutral optimal value satisfies

\[
J^*(G)=0,\qquad J^*(s)=\min_a\sum_{s',c}P(s',c\mid s,a)[c+J^*(s')].
\]

For a fixed proper stationary policy \(\mu\), let \(P_\mu\) contain transitions only between nonterminal states. Policy evaluation is the undiscounted Markov reward process calculation

\[
J_\mu=\bar c_\mu+P_\mu J_\mu,
\qquad J_\mu=(I-P_\mu)^{-1}\bar c_\mu.
\]

In the finite stationary setting, properness makes the nonterminal chain transient. The inverse exists globally precisely when no nonterminal recurrent class remains. This qualification matters: an improper policy can still have finite cost from some individual states, so global improperness does not imply infinite cost from every state.

Value iteration, policy iteration initialized with a proper policy, and the linear program below provide complementary ways to compute \(J^*\):

\[
\max_V\sum_{s\ne G}V(s),\quad
V(s)\le\bar c(s,a)+\sum_{s'\ne G}P(s'\mid s,a)V(s').
\]

The usual discounted contraction error bound cannot be substituted at \(\gamma=1\). A small successive-iterate difference is therefore a numerical stopping heuristic, not by itself a certificate of value error. The project cross-checks expected-cost solvers rather than assigning such a certificate to the residual.

When transitions are deterministic, positive mean edge costs reduce this objective to a deterministic shortest path, enabling a Dijkstra comparison. A discounted MDP can conversely be represented by adding independent termination after each paid transition. However, adding discounting to the present model changes the objective: it reduces the weight of later delays. The undiscounted setting preserves the intended interpretation as actual travel time.

## 3. Theory

### 3.1 What the expected-cost objective retains

For any policy obeying the joint Markov model, nonnegativity permits exchanging expectation and the stopped sum. Conditioning on the complete observed history before each transition gives

\[
\begin{aligned}
E_\pi[Z]
&=\sum_{t\ge0}E_\pi[\mathbf1_{\{t<T\}}C_t]\\
&=\sum_{t\ge0}E_\pi[\mathbf1_{\{t<T\}}\bar c(S_t,A_t)].
\end{aligned}
\]

The equality holds even when cost and next state are dependent. For risk-neutral optimization, an optimal stationary policy can be selected, so replacing each immediate cost by its conditional mean and retaining the transition probabilities preserves the optimal expected value. This does not remove transition uncertainty. Nor does it assert equality of history-dependent policy behavior after deleting the cost observations on which that behavior depended. The result motivates examining the total-cost distribution when tail outcomes matter.

### 3.2 VaR and CVaR for discrete travel times

For \(0<\alpha<1\), we use the upper-loss convention

\[
\operatorname{VaR}_\alpha(Z)=\inf\{z:P(Z\le z)\ge\alpha\},
\]
\[
\operatorname{CVaR}_\alpha(Z)=\min_{y\in\mathbb R}
\left[y+\frac{E[(Z-y)^+]}{1-\alpha}\right].
\]

The variational approach originates with [Rockafellar and Uryasev (2000)](https://doi.org/10.21314/jor.2000.038); their [general-distribution treatment (2002)](https://doi.org/10.1016/S0378-4266(02)00271-6) is particularly relevant to integer-valued costs. CVaR averages exactly the worst \(1-\alpha\) probability mass, including only the needed fraction of an atom at the quantile. It is generally not \(E[Z\mid Z\ge\operatorname{VaR}_\alpha(Z)]\). It has monotonicity, translation equivariance, positive homogeneity, and subadditivity for integrable losses.

The project's bridge example has mean 10.9 and CVaR at level 0.9 equal to 100, compared with 12 for both metrics on the deterministic detour. A second example holds the mean at 11 while changing CVaR from 20 to 11. These calculations illustrate different objectives rather than establish universal superiority of one route. Variance also differs from an upper-tail measure: a route taking 11 minutes with probability 0.9 and 1 minute otherwise has variance 9, yet the same CVaR at level 0.9 as a constant 11-minute route. For a mean-plus-variance objective, preference depends on the penalty coefficient.

### 3.3 Deriving the remaining-budget recursion

For a fixed threshold \(y\), minimizing the CVaR variational expression over policies reduces to minimizing expected excess cost. Define the optimal expected excess from state \(s\) with remaining budget \(b\) as

\[
W(s,b)=\inf_\pi E_s^\pi[(Z_s-b)^+].
\]

The augmentation follows the expected-excess approach of [Bäuerle and Ott (2011)](https://publikationen.bibliothek.kit.edu/1000032887/3310751). Their discounted infinite-horizon contraction theorem is not used as an undiscounted SSP theorem here. The following recursion follows directly from positive integer costs and the finite SSP assumptions. Total-cost risk-sensitive MDPs are also studied by [Carpin, Chow and Pavone (2016)](https://arxiv.org/abs/1602.05130), under structural assumptions that should not be conflated with existence of just one proper policy.

At the goal, no future cost remains:

\[
W(G,b)=(-b)^+.
\]

For a nonterminal state and \(b\le0\), nonnegative future cost implies \((Z_s-b)^+=Z_s-b\). Consequently,

\[
W(s,b)=J^*(s)-b\quad (s\ne G,\ b\le0).
\]

For an integer \(b\ge1\), condition on the first action and its joint outcome:

\[
W(s,b)=\min_{a\in\mathcal A(s)}
\sum_{s',c}P(s',c\mid s,a)W(s',b-c).
\]

Every successor budget is strictly smaller because \(c\ge1\). Thus positive budgets can be processed in ascending order even when the physical graph contains cycles. Once the budget is exhausted, execution switches to a proper expected-cost-optimal policy. A finite starting budget permits only finitely many positive-budget transitions, and the proper fallback ensures eventual finite-mean termination thereafter.

The two infima over policies and thresholds commute, giving

\[
\inf_\pi\operatorname{CVaR}_\alpha(Z_\pi)
=\inf_y\left[y+\frac{W(s_0,y)}{1-\alpha}\right].
\]

An integer-valued loss admits an integer minimizing threshold, so no threshold interpolation is needed. For a chosen budget bound \(B\), a pass over all budget layers costs \(O(B\sum_{s,a}K_{sa})\), where \(K_{sa}\) counts joint outcomes. This excludes the separate computation of \(J^*\). Optimal actions form a table indexed by physical state and remaining budget; with fixed initial \(y\), remaining budget is \(b=y-z\), where \(z\) is realized cumulative cost.

### 3.4 Certifying the threshold range

An interior numerical minimum alone does not certify the budget bound. Let \(U\) be any certified upper bound on the optimal CVaR, obtained from a feasible proper policy. Since \(y+W(s_0,y)/(1-\alpha)\ge y\), no threshold \(y>U\) can improve on that feasible value. For nonnegative costs, thresholds below zero cannot improve on zero. Hence searching integers from zero through \(\lceil U\rceil\) is sufficient. A conservative feasible bound is \(U=E[Z_\mu]/(1-\alpha)\) for a proper policy \(\mu\). In our finite acyclic examples, all policy costs are at most 50 and 51, respectively, so those support limits also certify complete threshold searches.

### 3.5 History dependence and distribution evaluation

Example 1 has best state-only CVaR 26, whereas choosing Y after a 1-minute first leg and X after a 20-minute first leg gives 23.9. The five-state second example yields 26.5 for the best state-only policy and 24.4 when actions use accrued cost. These are exact finite-example results. They demonstrate that physical state alone need not suffice; they do not imply that every environment requires history dependence. The underlying augmented-state principle is established prior work.

For a stationary policy, its remaining-cost distribution satisfies

\[
\eta_\mu(G)=\delta_0,\qquad
\eta_\mu(s)=\sum_{s',c}P(s',c\mid s,\mu(s))\,\mathcal T_c\eta_\mu(s'),
\]

where \(\mathcal T_c\) translates a distribution by \(c\). For a policy \(\mu(s,z)\), evaluation instead tracks probability at each pair \((s,z)\) from the initial condition. A joint outcome sends that mass to \((s',z+c)\); arrival at the goal adds to the terminal mass at cost \(z+c\). Since costs are positive integers, processing accrued costs in increasing order gives exact finite-support probabilities up to floating-point roundoff. A dense implementation up to cost \(L\) uses \(O(L|\mathcal S|)\) working memory and at most \(O(L\sum_{s,a}K_{sa})\) time.

With cutoff \(L\), overflow probability must be reported separately and must not be normalized away. Small overflow alone does not bound an omitted tail expectation or CVaR. A cyclic model requires additional residual-cost bounds or exact continuation evaluation. Our two acyclic examples have complete finite support, so their evaluations require no tail approximation.

### 3.6 Interpretation and limits

Static CVaR evaluates the total cost once, from the start. Repeated conditional CVaR evaluates a different, nested objective. Adding an augmented state preserves the initial static objective; it does not make unconstrained reoptimization of static CVaR time consistent. [Hau et al. (2023)](https://arxiv.org/abs/2304.12477) identify failures of particular risk-level DP decompositions; this does not invalidate every augmented-state approach.

CVaR is not generally additive across stages. Mean–variance control likewise cannot be treated as an ordinary scalar immediate-cost Bellman problem; the admissible policy class can affect attainable performance, as shown by [Mannor and Tsitsiklis (2011)](https://www.mit.edu/~jnt/Papers/C-11-mv-MDP-ICML.pdf). Finally, discounting changes the optimization target rather than merely accelerating computation. For unit stage costs, discounted cost is \((1-\gamma^T)/(1-\gamma)\); at fixed mean duration, a mean-preserving spread of duration can reduce its expectation because \(\gamma^T\) is convex. This is a qualified illustration, not a claim that discounting always increases risk for arbitrary costs.
