"""Static total-cost CVaR through integer remaining-budget dynamic programming."""
from dataclasses import dataclass
import numbers
import numpy as np
from .expected import policy_iteration, compile_model, _greedy


@dataclass
class BudgetSolution:
    value: float
    initial_budget: int
    policy: np.ndarray
    fallback: np.ndarray
    mean_value: np.ndarray
    W: np.ndarray
    objective: np.ndarray
    certified: bool


def budget_dp(env, alpha=.9, B=128, max_budget=100000):
    """Automatically extend B until unseen thresholds cannot improve the answer.

    Since W>=0, every unsearched integer y>=B+1 has objective >=B+1.
    Unlike merely testing whether the minimizer touches B, this is a global
    certificate even when the lower envelope across policies is nonconvex.
    Floating-point arithmetic and the mean-policy linear solve remain numerical.
    """
    if not 0 < alpha < 1:
        raise ValueError('alpha must lie in (0,1)')
    if not isinstance(B, numbers.Integral) or B < 0:
        raise ValueError('B must be a nonnegative integer')
    if not isinstance(max_budget, numbers.Integral) or max_budget < B:
        raise ValueError('max_budget must be an integer >= B')
    mean = policy_iteration(env)
    states, actions, _, _ = compile_model(env)
    row, dest, cost, prob = [], [], [], []
    for i, (s, a) in enumerate(zip(states, actions)):
        for o in env.outcomes[s][a]:
            row.append(i); dest.append(o.next_state); cost.append(o.cost); prob.append(o.prob)
    row, dest, cost, prob = map(np.asarray, (row, dest, cost, prob))
    W = np.zeros((env.n_states, B+1)); W[:, 0] = mean.value
    policy = np.tile(mean.policy[:, None], (1, B+1))
    previous = 0
    while True:
        for b in range(previous+1, B+1):
            remaining = b-cost
            continuation = W[dest, np.maximum(remaining, 0)]-np.minimum(remaining, 0)
            q = np.bincount(row, weights=prob*continuation, minlength=len(states))
            W[:, b], policy[:, b] = _greedy(env, states, actions, q)
        objective = np.arange(B+1)+W[env.start]/(1-alpha)
        best = float(objective.min())
        y = int(np.flatnonzero(objective <= best+1e-11)[0])
        if B+1 >= best+1e-10:
            return BudgetSolution(float(objective[y]), y, policy, mean.policy,
                                  mean.value, W, objective, True)
        target = min(max_budget, max(B+1, 2*B, int(np.ceil(best))))
        if target <= B:
            raise RuntimeError('max_budget reached without a global threshold certificate')
        previous, B = B, target
        W = np.pad(W, ((0, 0), (0, B-previous)))
        policy = np.pad(policy, ((0, 0), (0, B-previous)), constant_values=-1)
