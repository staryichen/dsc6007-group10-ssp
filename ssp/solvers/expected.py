"""Sparse mean-cost SSP solvers. All returned arrays include the goal."""
from dataclasses import dataclass
from collections import deque
import heapq
import numpy as np
from scipy.sparse import csr_matrix, eye
from scipy.sparse.linalg import spsolve
from scipy.optimize import linprog


@dataclass
class Solution:
    value: np.ndarray
    policy: np.ndarray
    iterations: int
    residual: float


def _gamma(gamma):
    if not 0 < gamma <= 1:
        raise ValueError('gamma must lie in (0,1]')


def compile_model(env):
    """One sparse row per valid state/action, including transitions to goal."""
    states, actions, costs, rr, cc, pp = [], [], [], [], [], []
    for s in range(env.n_states):
        for a, outcomes in enumerate(env.outcomes[s]):
            row = len(states)
            states.append(s); actions.append(a); costs.append(env.mean_cost(s, a))
            for o in outcomes:
                rr.append(row); cc.append(o.next_state); pp.append(o.prob)
    return (np.array(states), np.array(actions), np.array(costs),
            csr_matrix((pp, (rr, cc)), shape=(len(states), env.n_states)))


def _greedy(env, states, actions, q):
    value = np.full(env.n_states, np.inf)
    np.minimum.at(value, states, q)
    value[env.goal] = 0.
    # Deterministic first-action tie breaking; no approximate tie can hide improvement.
    rows = np.full(env.n_states, len(states), dtype=int)
    candidates = np.flatnonzero(q == value[states])
    np.minimum.at(rows, states[candidates], candidates)
    policy = np.full(env.n_states, -1, dtype=int)
    mask = np.arange(env.n_states) != env.goal
    policy[mask] = actions[rows[mask]]
    return value, policy


def validate_policy(env, policy):
    pi = np.asarray(policy)
    if pi.shape != (env.n_states,) or not np.issubdtype(pi.dtype, np.integer):
        raise ValueError('policy must be a full-state integer array')
    for s in range(env.n_states):
        if s != env.goal and not 0 <= pi[s] < len(env.actions[s]):
            raise ValueError(f'invalid action at state {s}')
    return pi


def evaluate_policy(env, policy, gamma=1.):
    """Exact linear evaluation; infinity only at states that can reach a closed class.

    A policy improper elsewhere can still have finite cost from the start.
    Graph reachability detects improper classes without a numerical singularity test.
    """
    _gamma(gamma)
    pi = validate_policy(env, policy)
    succ = [[] if s == env.goal else [o.next_state for o in env.outcomes[s][pi[s]]]
            for s in range(env.n_states)]
    bad = set(env._cannot_reach_goal(succ)) if gamma == 1 else set()
    pred = [[] for _ in succ]
    for s, dests in enumerate(succ):
        for dest in dests:
            pred[dest].append(s)
    queue = deque(bad)
    while queue:
        for s in pred[queue.popleft()]:
            if s not in bad:
                bad.add(s); queue.append(s)
    good = [s for s in range(env.n_states) if s != env.goal and s not in bad]
    index = {s: i for i, s in enumerate(good)}
    rr, cc, pp = [], [], []
    for s in good:
        for o in env.outcomes[s][pi[s]]:
            if o.next_state in index:
                rr.append(index[s]); cc.append(index[o.next_state]); pp.append(o.prob)
    value = np.full(env.n_states, np.inf); value[env.goal] = 0.
    if good:
        P = csr_matrix((pp, (rr, cc)), shape=(len(good), len(good)))
        value[good] = spsolve(eye(len(good), format='csr')-gamma*P,
                            [env.mean_cost(s, pi[s]) for s in good])
        if not np.all(np.isfinite(value[good])) or np.any(value[good] < 0):
            raise ArithmeticError('policy evaluation is numerically unstable')
    return value


def proper_initial_policy(env):
    """Choose an action with an outcome one graph-distance closer to the goal.

    Every non-goal closed class would contain a minimum-distance state with
    a positive-probability exit, a contradiction. Thus this policy is proper.
    """
    pred = [[] for _ in range(env.n_states)]
    for s in range(env.n_states):
        for a, outs in enumerate(env.outcomes[s]):
            for o in outs:
                pred[o.next_state].append((s, a))
    pi = np.full(env.n_states, -1, dtype=int)
    # Compute BFS distances, then maximize probability of moving closer.
    # Picking the first action with *any* closer outcome can point away from
    # the goal on slippery grids, producing an extremely ill-conditioned MRP.
    distance = np.full(env.n_states, np.inf); distance[env.goal] = 0; queue = deque([env.goal])
    while queue:
        dest = queue.popleft()
        for s, _ in pred[dest]:
            if not np.isfinite(distance[s]):
                distance[s] = distance[dest]+1; queue.append(s)
    if not np.all(np.isfinite(distance)):
        raise ValueError('no proper policy exists')
    for s in range(env.n_states):
        if s != env.goal:
            scores = [sum(o.prob for o in outs if distance[o.next_state] < distance[s])
                      for outs in env.outcomes[s]]
            pi[s] = int(np.argmax(scores))
    return pi


def value_iteration(env, gamma=1., tol=1e-10, max_iter=100000):
    _gamma(gamma)
    if not np.isfinite(tol) or tol <= 0 or max_iter < 1:
        raise ValueError('positive tolerance and iteration limit required')
    states, actions, costs, P = compile_model(env)
    value = np.zeros(env.n_states)
    for iteration in range(1, max_iter+1):
        updated, policy = _greedy(env, states, actions, costs+gamma*(P@value))
        delta = np.max(np.abs(updated-value)); value = updated
        if delta < tol:
            bellman, policy = _greedy(env, states, actions, costs+gamma*(P@value))
            if gamma == 1 and not env.is_proper(policy):
                continue
            return Solution(value, policy, iteration, float(np.max(np.abs(bellman-value))))
    raise RuntimeError('VI did not converge within max_iter')


def policy_iteration(env, gamma=1., initial_policy=None, max_iter=10000):
    _gamma(gamma)
    policy = proper_initial_policy(env) if initial_policy is None else validate_policy(env, initial_policy).copy()
    if gamma == 1 and not env.is_proper(policy):
        raise ValueError('PI requires a proper initial policy at gamma=1')
    states, actions, costs, P = compile_model(env)
    for iteration in range(1, max_iter+1):
        value = evaluate_policy(env, policy, gamma)
        q = costs+gamma*(P@value)
        bellman, improved = _greedy(env, states, actions, q)
        # Preserve current actions on floating-point ties, preventing PI cycles.
        current = np.zeros(env.n_states)
        chosen = actions == policy[states]
        current[states[chosen]] = q[chosen]
        keep = current-bellman <= 1e-12
        improved[keep] = policy[keep]
        if np.array_equal(policy, improved):
            return Solution(value, policy, iteration, float(np.max(np.abs(bellman-value))))
        policy = improved
    raise RuntimeError('PI did not converge within max_iter')


def linear_programming(env, gamma=1.):
    _gamma(gamma)
    states, actions, costs, P = compile_model(env)
    selector = csr_matrix((np.ones(len(states)), (np.arange(len(states)), states)), shape=P.shape)
    bounds = [(0, 0) if s == env.goal else (None, None) for s in range(env.n_states)]
    result = linprog(-np.ones(env.n_states), A_ub=selector-gamma*P,
                     b_ub=costs, bounds=bounds, method='highs')
    if not result.success:
        raise RuntimeError(f'LP failed: {result.message}')
    bellman, policy = _greedy(env, states, actions, costs+gamma*(P@result.x))
    return Solution(result.x, policy, int(result.nit), float(np.max(np.abs(bellman-result.x))))


def dijkstra(env):
    """Deterministic transitions only; random costs are replaced by their means."""
    pred = [[] for _ in range(env.n_states)]
    for s in range(env.n_states):
        for a, outs in enumerate(env.outcomes[s]):
            dests = {o.next_state for o in outs}
            if len(dests) != 1:
                raise ValueError('Dijkstra requires deterministic transitions')
            pred[next(iter(dests))].append((s, env.mean_cost(s, a)))
    value = np.full(env.n_states, np.inf); value[env.goal] = 0.
    queue = [(0., env.goal)]
    while queue:
        cost, s = heapq.heappop(queue)
        if cost > value[s]:
            continue
        for prev, edge in pred[s]:
            if cost+edge < value[prev]:
                value[prev] = cost+edge; heapq.heappush(queue, (value[prev], prev))
    return value
