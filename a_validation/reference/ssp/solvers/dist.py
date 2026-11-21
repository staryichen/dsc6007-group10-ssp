"""Forward cost propagation for stationary and spent-cost-dependent policies."""
from dataclasses import dataclass
import numbers
import numpy as np


@dataclass
class Distribution:
    pmf: np.ndarray
    overflow: float


def budget_policy(policy, initial_budget, fallback):
    """Adapt C's full-state policy[s,b]; b <= 0 uses the mean-optimal policy."""
    table = np.asarray(policy)
    if not isinstance(initial_budget, numbers.Integral) or initial_budget < 0:
        raise ValueError('initial_budget must be a nonnegative integer')
    if table.ndim != 2 or table.shape[1] <= initial_budget:
        raise ValueError('budget policy must have columns 0 through initial_budget')
    return lambda s, spent: table[s, initial_budget-spent] if spent < initial_budget else fallback[s]


def cost_distribution(env, policy, z_max=1000):
    """policy is a full-state action array or callable (state, spent)->action.

    overflow is first-crossing probability, not a terminal-cost distribution.
    No normalization or approximation of the unobserved tail is performed.
    """
    if not isinstance(z_max, numbers.Integral) or z_max < 0:
        raise ValueError('z_max must be a nonnegative integer')
    if not callable(policy):
        policy = np.asarray(policy)
        if policy.shape != (env.n_states,):
            raise ValueError('policy must have one entry per original state')
        actions = policy
        policy = lambda s, z: actions[s]
    pending = np.zeros((z_max+1, env.n_states))
    pending[0, env.start] = 1.
    pmf = np.zeros(z_max+1)
    overflow = 0.
    for z in range(z_max+1):
        for s in np.flatnonzero(pending[z]):
            mass = pending[z, s]
            a = policy(int(s), z)
            if not isinstance(a, numbers.Integral) or not 0 <= a < len(env.actions[s]):
                raise ValueError(f'invalid action {a} at state {s}, spent {z}')
            for o in env.outcomes[s][a]:
                dest, weight = z+o.cost, mass*o.prob
                if dest > z_max:
                    overflow += weight
                elif o.next_state == env.goal:
                    pmf[dest] += weight
                else:
                    pending[dest, o.next_state] += weight
    if not np.isclose(pmf.sum()+overflow, 1., atol=1e-8, rtol=0):
        raise ArithmeticError('probability conservation failed')
    return Distribution(pmf, float(overflow))
