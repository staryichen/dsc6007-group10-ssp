"""Shared output helpers for C's deterministic experiments."""
import csv
import json
from pathlib import Path
import numpy as np


def output_dirs(tag, experiment):
    if not tag or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in tag):
        raise ValueError('tag must contain only letters, digits, underscore or hyphen')
    for name in ['results','figures']:
        Path(name).mkdir(exist_ok=True)
    if list(Path('results').glob(f'{experiment}_*_{tag}.*')):
        raise FileExistsError('this experiment tag exists; choose a new tag')


def write_csv(path, rows):
    with Path(path).open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def nominal_route(env, choose, limit=10000):
    """Illustration only: follow most probable joint outcome, updating actual cost."""
    s,z=env.start,0; route=[s]; seen=set()
    for _ in range(limit):
        if s==env.goal: return route
        if (s,z) in seen: raise RuntimeError('nominal route loops')
        seen.add((s,z))
        a=choose(s,z)
        o=max(env.outcomes[s][a],key=lambda o:o.prob)
        s=o.next_state;z+=o.cost;route.append(s)
    raise RuntimeError('nominal route exceeded limit')


def save_policy(env, mean, budget, cutoff, alpha, path):
    payload=dict(grid=env.params,alpha=alpha,initial_budget=budget.initial_budget,
                 mean_policy=mean.policy.tolist(),budget_policy=budget.policy.tolist(),
                 cutoff=cutoff,mean_value=mean.value.tolist(),cvar=budget.value,
                 certified=budget.certified)
    # make_grid does not accept its redundant metadata name; params are its kwargs.
    Path(path).write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
