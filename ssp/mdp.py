"""Shared SSP format used by every environment, solver and learner.

An environment is one outcome table:

    outcomes[s][k] = (Outcome(next_state, cost, prob), ...)

meaning: in state s, action k moves to `next_state` and costs `cost` minutes
with probability `prob`.  Everything else (mean costs, arrays for VI/PI/LP,
sampling for simulation and learning) is derived here, so nobody keeps a
second copy of the model.

Rules, checked when an SSP is created:
1. costs are integers >= 1 (minutes);
2. for each (s, k) the probabilities are > 0 and sum to 1;
3. the goal is absorbing and cost-free: it has no actions;
4. every state can reach the goal, so at least one proper policy exists;
5. the model holds no randomness: callers pass a numpy Generator to `sample`.
There is no discounting (gamma = 1).
"""

from __future__ import annotations

import numbers
from collections import deque
from dataclasses import dataclass, field
from typing import NamedTuple, Sequence

import numpy as np

PROB_TOL = 1e-9


class Outcome(NamedTuple):
    next_state: int
    cost: int
    prob: float


class SSPArrays(NamedTuple):
    """Dense arrays over the non-goal states, for VI / PI / LP.

    states[i]   : original index of row i (the goal is left out)
    P[k, i, j]  : probability that action k in states[i] moves to states[j];
                  rows are substochastic, the missing mass goes to the goal
    cbar[k, i]  : mean cost of action k in states[i]; inf if that action does not exist
    valid[k, i] : whether action k exists in states[i]
    """

    states: np.ndarray
    P: np.ndarray
    cbar: np.ndarray
    valid: np.ndarray


def make_outcomes(triples) -> tuple[Outcome, ...]:
    """Build the outcome list of one (s, k) from (next_state, cost, prob) triples.

    Repeated (next_state, cost) pairs are merged, zero probabilities dropped and
    the result sorted, so environment builders can list outcomes in any order.
    """
    merged: dict[tuple[int, int], float] = {}
    for next_state, cost, prob in triples:
        if not isinstance(cost, numbers.Integral):
            raise TypeError(f"cost must be an integer number of minutes, got {cost!r}")
        key = (int(next_state), int(cost))
        merged[key] = merged.get(key, 0.0) + float(prob)
    return tuple(Outcome(s2, c, p) for (s2, c), p in sorted(merged.items()) if p > 0)


@dataclass
class SSP:
    """A stochastic shortest path problem with integer random costs (gamma = 1).

    state_names[s]  : name of state s (grids use "(row,col)")
    start, goal     : indices of the start and the goal state
    actions[s]      : names of the actions available in s; action k is actions[s][k]
    outcomes[s][k]  : tuple of Outcome(next_state, cost, prob)
    params          : parameters the environment was built with
    coords          : (row, col) of each state for plotting, or None
    """

    name: str
    state_names: list[str]
    start: int
    goal: int
    actions: list[list[str]]
    outcomes: list[list[tuple[Outcome, ...]]]
    params: dict = field(default_factory=dict)
    coords: list[tuple[int, int]] | None = None
    _cum: list = field(init=False, repr=False, compare=False, default_factory=list)

    def __post_init__(self) -> None:
        self.validate()
        self._cum = [[np.cumsum([o.prob for o in outs]) for outs in per_state]
                     for per_state in self.outcomes]

    @property
    def n_states(self) -> int:
        return len(self.state_names)

    def validate(self) -> None:
        """Raise ValueError if the model breaks one of the rules in the module docstring."""
        n = self.n_states
        if len(self.actions) != n or len(self.outcomes) != n:
            raise ValueError("state_names, actions and outcomes need one entry per state")
        if not (0 <= self.start < n and 0 <= self.goal < n) or self.start == self.goal:
            raise ValueError("start and goal must be two different valid states")
        if self.actions[self.goal] or self.outcomes[self.goal]:
            raise ValueError("the goal must have no actions")
        if self.coords is not None and len(self.coords) != n:
            raise ValueError("coords needs one entry per state")
        for s in range(n):
            if s == self.goal:
                continue
            where = f"state {s} ({self.state_names[s]})"
            if not self.actions[s]:
                raise ValueError(f"{where} has no actions")
            if len(self.outcomes[s]) != len(self.actions[s]):
                raise ValueError(f"{where}: actions and outcomes have different lengths")
            for k, outs in enumerate(self.outcomes[s]):
                at = f"{where}, action {k} ({self.actions[s][k]})"
                if not outs:
                    raise ValueError(f"{at} has no outcomes")
                for o in outs:
                    if not 0 <= o.next_state < n:
                        raise ValueError(f"{at}: next_state {o.next_state} is out of range")
                    if not isinstance(o.cost, numbers.Integral) or o.cost < 1:
                        raise ValueError(f"{at}: cost must be an integer >= 1, got {o.cost!r}")
                    if not o.prob > 0:
                        raise ValueError(f"{at}: probabilities must be > 0, got {o.prob!r}")
                total = sum(o.prob for o in outs)
                if abs(total - 1.0) > PROB_TOL:
                    raise ValueError(f"{at}: probabilities sum to {total}, not 1")
        succ = [[o.next_state for outs in self.outcomes[s] for o in outs] for s in range(n)]
        stuck = self._cannot_reach_goal(succ)
        if stuck:
            names = ", ".join(self.state_names[s] for s in stuck[:5])
            raise ValueError(f"{len(stuck)} state(s) cannot reach the goal, e.g. {names}")

    def _cannot_reach_goal(self, succ: list[list[int]]) -> list[int]:
        """States from which the goal cannot be reached in the successor graph `succ`."""
        pred: list[list[int]] = [[] for _ in range(self.n_states)]
        for s, nexts in enumerate(succ):
            for s2 in nexts:
                pred[s2].append(s)
        seen = {self.goal}
        queue = deque([self.goal])
        while queue:
            for s in pred[queue.popleft()]:
                if s not in seen:
                    seen.add(s)
                    queue.append(s)
        return [s for s in range(self.n_states) if s not in seen]

    def mean_cost(self, s: int, k: int) -> float:
        """Mean cost cbar(s, a) of action k in state s."""
        return sum(o.prob * o.cost for o in self.outcomes[s][k])

    def to_arrays(self) -> SSPArrays:
        """Arrays over the non-goal states for VI / PI / LP (see SSPArrays)."""
        states = [s for s in range(self.n_states) if s != self.goal]
        pos = {s: i for i, s in enumerate(states)}
        m = len(states)
        n_act = max(len(self.actions[s]) for s in states)
        P = np.zeros((n_act, m, m))
        cbar = np.full((n_act, m), np.inf)
        valid = np.zeros((n_act, m), dtype=bool)
        for s in states:
            i = pos[s]
            for k, outs in enumerate(self.outcomes[s]):
                valid[k, i] = True
                cbar[k, i] = self.mean_cost(s, k)
                for o in outs:
                    if o.next_state != self.goal:
                        P[k, i, pos[o.next_state]] += o.prob
        return SSPArrays(np.array(states), P, cbar, valid)

    def sample(self, s: int, k: int, rng: np.random.Generator) -> tuple[int, int]:
        """Draw one outcome of action k in state s; returns (next_state, cost)."""
        outs = self.outcomes[s][k]
        i = int(np.searchsorted(self._cum[s][k], rng.random(), side="right"))
        o = outs[min(i, len(outs) - 1)]
        return o.next_state, o.cost

    def is_proper(self, policy: Sequence[int]) -> bool:
        """Whether a stationary policy (policy[s] = action index) reaches the goal w.p. 1.

        In a finite SSP this holds iff the goal can be reached from every state
        in the graph of the policy's transitions.  policy[goal] is ignored.
        """
        succ = [[] if s == self.goal else [o.next_state for o in self.outcomes[s][policy[s]]]
                for s in range(self.n_states)]
        return not self._cannot_reach_goal(succ)

    def describe(self) -> str:
        """The outcome table as text."""
        lines = [f"{self.name}: start={self.state_names[self.start]}, "
                 f"goal={self.state_names[self.goal]}"]
        for s in range(self.n_states):
            for k, outs in enumerate(self.outcomes[s]):
                head = f"  {self.state_names[s]:>6} {self.actions[s][k]:<8}"
                for j, o in enumerate(outs):
                    lead = head if j == 0 else " " * len(head)
                    lines.append(f"{lead} -> {self.state_names[o.next_state]:<6} "
                                 f"cost {o.cost:>3}  p={o.prob:g}")
        return "\n".join(lines)
