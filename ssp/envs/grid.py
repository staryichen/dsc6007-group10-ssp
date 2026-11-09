"""Slippery 10x10 grid with a risky shortcut (experiments E2, E3, E5, E6, E9).

Default layout: start S at (4,0), goal G at (4,9), shortcut zone '~' in rows 2-6
and columns 3-6.

    . . . . . . . . . .
    . . . . . . . . . .
    . . . ~ ~ ~ ~ . . .
    . . . ~ ~ ~ ~ . . .
    S . . ~ ~ ~ ~ . . G
    . . . ~ ~ ~ ~ . . .
    . . . ~ ~ ~ ~ . . .
    . . . . . . . . . .
    . . . . . . . . . .
    . . . . . . . . . .

Going straight along row 4 takes 9 steps through 4 shortcut cells; going around
the zone takes 15 steps through none.

Model (whole minutes, gamma = 1):
- actions up, down, left, right (indices 0-3);
- slip: with probability 1 - p the agent moves as chosen, with probability p in
  one of the 4 directions picked uniformly at random, so the chosen direction
  gets 1 - p + p/4 in total;
- a move into the border leaves the agent where it is;
- a step costs the cost of the cell the agent ends up in: 1 minute, or 2 minutes
  with probability p_slow; in a shortcut cell this is multiplied by `delay` with
  probability q (a jam).

    python3 -m ssp.envs.grid    # print the map and run the self-check
"""

from __future__ import annotations

import numbers

import numpy as np

from ..mdp import SSP, make_outcomes
from ._checks import add_independent, discrete_cvar

ACTIONS = ["up", "down", "left", "right"]
UP, DOWN, LEFT, RIGHT = range(4)
MOVES = [(-1, 0), (1, 0), (0, -1), (0, 1)]
ARROWS = "^v<>"


def make_grid(p: float = 0.1, q: float = 0.1, delay: int = 10, p_slow: float = 0.2,
              size: int = 10, start: tuple[int, int] = (4, 0), goal: tuple[int, int] = (4, 9),
              zone_rows: tuple[int, int] = (2, 6), zone_cols: tuple[int, int] = (3, 6)) -> SSP:
    """Build the grid.  zone_rows and zone_cols are inclusive (first, last) ranges.

    State index = row * size + column; state names are "(row,col)".
    """
    params = dict(p=p, q=q, delay=delay, p_slow=p_slow, size=size, start=start, goal=goal,
                  zone_rows=zone_rows, zone_cols=zone_cols)
    _check_params(params)
    base = [(1, 1 - p_slow), (2, p_slow)]

    def idx(r: int, c: int) -> int:
        return r * size + c

    def cell_costs(r: int, c: int) -> list[tuple[int, float]]:
        if not in_zone(params, r, c):
            return base
        return [(b, pb * (1 - q)) for b, pb in base] + [(b * delay, pb * q) for b, pb in base]

    def landing(r: int, c: int, d: int) -> tuple[int, int]:
        r2, c2 = r + MOVES[d][0], c + MOVES[d][1]
        return (r2, c2) if 0 <= r2 < size and 0 <= c2 < size else (r, c)

    actions, outcomes = [], []
    for r in range(size):
        for c in range(size):
            if (r, c) == goal:
                actions.append([])
                outcomes.append([])
                continue
            per_action = []
            for a in range(4):
                triples = []
                for d in range(4):
                    p_dir = (1 - p) * (d == a) + p / 4
                    r2, c2 = landing(r, c, d)
                    triples += [(idx(r2, c2), cost, p_dir * pc) for cost, pc in cell_costs(r2, c2)]
                per_action.append(make_outcomes(triples))
            actions.append(list(ACTIONS))
            outcomes.append(per_action)

    return SSP(
        name=f"grid{size}_p{p:g}_q{q:g}",
        state_names=[f"({r},{c})" for r in range(size) for c in range(size)],
        start=idx(*start),
        goal=idx(*goal),
        actions=actions,
        outcomes=outcomes,
        params=params,
        coords=[(r, c) for r in range(size) for c in range(size)],
    )


def in_zone(params: dict, r: int, c: int) -> bool:
    """Whether cell (r, c) is a shortcut cell of the grid built with `params`."""
    (r0, r1), (c0, c1) = params["zone_rows"], params["zone_cols"]
    return r0 <= r <= r1 and c0 <= c <= c1


def cell_index(env: SSP, r: int, c: int) -> int:
    """State index of cell (r, c)."""
    return r * env.params["size"] + c


def render(env: SSP, policy=None) -> str:
    """The map as text (S start, G goal, ~ shortcut), or a stationary policy as arrows."""
    size, rows = env.params["size"], []
    for r in range(size):
        cells = []
        for c in range(size):
            s = r * size + c
            if s == env.goal:
                cells.append("G")
            elif policy is not None:
                cells.append(ARROWS[policy[s]])
            elif s == env.start:
                cells.append("S")
            else:
                cells.append("~" if in_zone(env.params, r, c) else ".")
        rows.append(" ".join(cells))
    return "\n".join(rows)


def _check_params(pr: dict) -> None:
    for key in ("p", "q", "p_slow"):
        if not 0 <= pr[key] <= 1:
            raise ValueError(f"{key} must be a probability, got {pr[key]}")
    if not isinstance(pr["delay"], numbers.Integral) or pr["delay"] < 1:
        raise ValueError(f"delay must be an integer >= 1, got {pr['delay']!r}")
    size = pr["size"]
    if not isinstance(size, numbers.Integral) or size < 2:
        raise ValueError(f"size must be an integer >= 2, got {size!r}")

    def inside(cell: tuple[int, int]) -> bool:
        return 0 <= cell[0] < size and 0 <= cell[1] < size

    if not (inside(pr["start"]) and inside(pr["goal"])) or pr["start"] == pr["goal"]:
        raise ValueError("start and goal must be two different cells inside the grid")
    (r0, r1), (c0, c1) = pr["zone_rows"], pr["zone_cols"]
    if not (0 <= r0 <= r1 < size and 0 <= c0 <= c1 < size):
        raise ValueError("the shortcut zone must lie inside the grid")
    if in_zone(pr, *pr["start"]) or in_zone(pr, *pr["goal"]):
        raise ValueError("start and goal must lie outside the shortcut zone")


def _route_distribution(env: SSP, moves: list[int]) -> tuple[int, dict[int, float]]:
    """End state and exact total-cost distribution of a fixed list of moves (needs p = 0)."""
    dist, s = {0: 1.0}, env.start
    for k in moves:
        outs = env.outcomes[s][k]
        if len({o.next_state for o in outs}) != 1:
            raise ValueError("fixed routes can only be checked without slipping (p = 0)")
        step: dict[int, float] = {}
        for o in outs:
            step[o.cost] = step.get(o.cost, 0.0) + o.prob
        dist = add_independent(dist, step)
        s = outs[0].next_state
    return s, dist


def _self_check(n_runs: int = 20_000, seed: int = 0, alpha: float = 0.9) -> bool:
    checks = {}
    env = make_grid()
    arrays = env.to_arrays()
    print(f"{env.name}: {env.n_states} states, start {env.state_names[env.start]}, "
          f"goal {env.state_names[env.goal]}, to_arrays P shape {arrays.P.shape}")
    print(render(env))

    slip = make_grid(p=0.2)

    def where_to(r: int, c: int, k: int) -> dict[str, float]:
        out: dict[str, float] = {}
        for o in slip.outcomes[cell_index(slip, r, c)][k]:
            name = slip.state_names[o.next_state]
            out[name] = out.get(name, 0.0) + o.prob
        return out

    inner, corner = where_to(1, 1, RIGHT), where_to(0, 0, UP)
    print(f"\np = 0.2, at (1,1) choose right: {', '.join(f'{k} {v:.2f}' for k, v in inner.items())}")
    print(f"p = 0.2, at (0,0) choose up:    {', '.join(f'{k} {v:.2f}' for k, v in corner.items())}")
    checks["slip"] = (abs(inner["(1,2)"] - 0.85) < 1e-12
                      and all(abs(inner[c] - 0.05) < 1e-12 for c in ("(0,1)", "(2,1)", "(1,0)")))
    checks["border"] = abs(corner["(0,0)"] - 0.9) < 1e-12

    flat = make_grid(p=0.0)
    straight = [RIGHT] * 9
    around = [UP] * 3 + [RIGHT] * 7 + [DOWN] * 3 + [RIGHT] * 2
    rng = np.random.default_rng(seed)
    print(f"\np = 0, q = {flat.params['q']}: two fixed routes from S, exact and sampled ({n_runs} runs)")
    stats = {}
    for name, moves in (("straight", straight), ("around", around)):
        end, dist = _route_distribution(flat, moves)
        mean = sum(z * pr for z, pr in dist.items())
        totals = []
        for _ in range(n_runs):
            s, total = flat.start, 0
            for k in moves:
                s, cost = flat.sample(s, k, rng)
                total += cost
            totals.append(total)
        sampled = float(np.mean(totals))
        cvar = discrete_cvar(dist, alpha)
        stats[name] = (mean, cvar)
        print(f"  {name:<9} {len(moves):>2} steps   mean {mean:6.2f} (sampled {sampled:6.2f})   "
              f"CVaR_{alpha} {cvar:6.2f}")
        checks[f"{name} ends at G"] = end == flat.goal
        checks[f"{name} sampling"] = abs(sampled - mean) < 0.3
    checks["routes split"] = (stats["straight"][0] < stats["around"][0]
                              and stats["straight"][1] > stats["around"][1])
    print()
    for name, ok in checks.items():
        print(f"  check {name:<20} {'OK' if ok else 'MISMATCH'}")
    return all(checks.values())


if __name__ == "__main__":
    raise SystemExit(0 if _self_check() else 1)
