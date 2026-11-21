"""Tail-completed distribution metrics, complementing D's unchanged dist.py."""
from dataclasses import dataclass
import numbers
import numpy as np
from .expected import evaluate_policy, validate_policy


@dataclass
class TailEvaluation:
    pmf: np.ndarray
    overflow: float
    tail_first_moment: float
    mean: float
    var: int
    cvar: float


def evaluate_distribution(env, policy, alpha=.9, cutoff=400, fallback=None, fallback_after=0):
    """Retain first-crossing mass AND its exact residual expected cost.

    Callable policies must equal fallback for spent >= fallback_after. Require
    cutoff >= fallback_after. At a first crossing (s,z), z>cutoff, the remaining
    expected total is z+J_fallback(s). Once VaR <= cutoff, this suffices to
    compute both the mean and CVaR, without pretending the tail PMF is known.
    """
    if not 0 < alpha < 1 or not isinstance(cutoff, numbers.Integral) or cutoff < 0:
        raise ValueError('invalid alpha or cutoff')
    if not isinstance(fallback_after, numbers.Integral) or not 0 <= fallback_after <= cutoff:
        raise ValueError('cutoff must cover fallback_after')
    if callable(policy):
        if fallback is None:
            raise ValueError('callable policy requires a stationary tail fallback')
        choose = policy
    else:
        fallback = validate_policy(env, policy)
        choose = lambda s, z: fallback[s]
    fallback = validate_policy(env, fallback)
    J = evaluate_policy(env, fallback)
    if not np.all(np.isfinite(J)):
        raise ValueError('tail fallback must be proper from every state')
    pending = np.zeros((cutoff+1, env.n_states)); pending[0, env.start] = 1.
    pmf = np.zeros(cutoff+1); overflow = 0.; tail = 0.
    for z in range(cutoff+1):
        for s in np.flatnonzero(pending[z]):
            a = choose(int(s), z)
            if not isinstance(a, numbers.Integral) or not 0 <= a < len(env.actions[s]):
                raise ValueError('invalid policy action')
            if z >= fallback_after and a != fallback[s]:
                raise ValueError('policy does not match its declared tail fallback')
            for o in env.outcomes[s][a]:
                mass = pending[z, s]*o.prob; total = z+o.cost
                if total > cutoff:
                    overflow += mass
                    tail += mass*(total+J[o.next_state])
                elif o.next_state == env.goal:
                    pmf[total] += mass
                else:
                    pending[total, o.next_state] += mass
    if not np.isclose(pmf.sum()+overflow, 1., atol=1e-10, rtol=0):
        raise ArithmeticError('probability conservation failed')
    cdf = np.cumsum(pmf)
    if cdf[-1] < alpha:
        raise ValueError('cutoff does not cover VaR; increase cutoff')
    var = int(np.searchsorted(cdf, alpha-1e-12))
    z = np.arange(cutoff+1)
    mean = float(z@pmf+tail)
    cvar = var+float(np.maximum(z-var, 0)@pmf+tail-var*overflow)/(1-alpha)
    return TailEvaluation(pmf, float(overflow), float(tail), mean, var, cvar)
