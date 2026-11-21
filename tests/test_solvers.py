"""Independent regression oracles for C's production solvers."""
import itertools
import unittest
import numpy as np
from ssp.mdp import SSP, make_outcomes as O
from ssp.envs.acyclic import example1, _cost_distribution
from ssp.envs.toy import two_route
from ssp.envs.grid import make_grid
from ssp.envs._checks import discrete_cvar
from ssp.solvers.expected import (value_iteration, policy_iteration, linear_programming,
                                  evaluate_policy, dijkstra)
from ssp.solvers.budget_dp import budget_dp
from ssp.solvers.dist import budget_policy, cost_distribution
from ssp.solvers.tail_evaluation import evaluate_distribution


def example2():
    """A's candidate at 9f62078, kept as a fixture pending B's adoption."""
    return SSP('example2_candidate', ['S','A','B','M','G'], 0, 4,
               [['go'],['continue'],['continue'],['X','Y'],[]],
               [[O([(1,1,.9),(2,10,.1)])], [O([(3,1,1.)])],
                [O([(3,10,.5),(3,11,.5)])],
                [O([(4,1,.9),(4,30,.1)]), O([(4,6,1.)])], []])


def enumerate_policies(env):
    pairs = set()
    def visit(s, z):
        if s == env.goal or (s,z) in pairs:
            return
        pairs.add((s,z))
        for outs in env.outcomes[s]:
            for o in outs:
                visit(o.next_state, z+o.cost)
    visit(env.start, 0)
    pairs = sorted(pairs)
    for choices in itertools.product(*(range(len(env.actions[s])) for s,z in pairs)):
        mapping = dict(zip(pairs, choices))
        yield _cost_distribution(env, lambda s,z: mapping[s,z])


class SolverTests(unittest.TestCase):
    def test_expected_crosschecks(self):
        for env in [two_route(), example1(), example2(), make_grid(p=0), make_grid(p=.3)]:
            vi, pi, lp = [f(env) for f in (value_iteration, policy_iteration, linear_programming)]
            np.testing.assert_allclose(vi.value, pi.value, atol=1e-8, rtol=0)
            np.testing.assert_allclose(lp.value, pi.value, atol=1e-8, rtol=0)
            for result in (vi, pi, lp):
                self.assertTrue(env.is_proper(result.policy))
                np.testing.assert_allclose(evaluate_policy(env,result.policy),pi.value,atol=1e-8)
        np.testing.assert_allclose(value_iteration(make_grid(p=0)).value,dijkstra(make_grid(p=0)))
        with self.assertRaises(ValueError): dijkstra(make_grid(p=.1))

    def test_exhaustive_history_and_distribution(self):
        for env, known in [(example1(),23.9),(example2(),24.4)]:
            distributions = list(enumerate_policies(env))
            for alpha in [.5,.8,.9,.95,.99]:
                result = budget_dp(env, alpha, B=0)
                best = min(discrete_cvar(d,alpha) for d in distributions)
                self.assertAlmostEqual(result.value,best,places=9)
                choose = budget_policy(result.policy,result.initial_budget,result.fallback)
                exact = _cost_distribution(env,choose)
                evaluated = evaluate_distribution(env,choose,alpha,60,result.fallback,result.initial_budget)
                np.testing.assert_allclose(evaluated.pmf,[exact.get(z,0) for z in range(61)],atol=1e-12)
                self.assertAlmostEqual(evaluated.cvar,best,places=9)
                if alpha == .9: self.assertAlmostEqual(result.value,known,places=9)

    def test_geometric_tail(self):
        env = SSP('loop',['S','G'],0,1,[['go'],[]],[[O([(0,1,.5),(1,1,.5)])],[]])
        result = evaluate_distribution(env,[0,-1],.9,4)
        self.assertAlmostEqual(result.overflow,1/16)
        self.assertAlmostEqual(result.tail_first_moment,6/16)
        self.assertAlmostEqual(result.mean,2.)
        self.assertEqual(result.var,4)
        self.assertAlmostEqual(result.cvar,5.25)
        np.testing.assert_allclose(result.pmf,cost_distribution(env,[0,-1],4).pmf)

    def test_improper_and_unreachable_bad_class(self):
        env = SSP('trap',['S','T','G'],0,2,[['finish','trap'],['stay','exit'],[]],
                  [[O([(2,20,1.)]),O([(1,1,1.)])], [O([(1,1,1.)]),O([(2,20,1.)])],[]])
        j = evaluate_policy(env,[0,0,-1])
        self.assertEqual(j[0],20); self.assertTrue(np.isinf(j[1]))
        self.assertTrue(np.isinf(evaluate_policy(env,[1,0,-1])[0]))
        discounted = value_iteration(env,gamma=.9)
        self.assertTrue(np.isinf(evaluate_policy(env,discounted.policy)[0]))
        self.assertTrue(np.all(np.isfinite(evaluate_policy(env,discounted.policy,.9))))
        with self.assertRaises(ValueError): policy_iteration(env,initial_policy=[1,0,-1])

    def test_budget_search_interior_false_optimum(self):
        # Restricted best y=0 is interior for B=2, but global best is y=20.
        env = SSP('nonconvex',['S','G'],0,1,[['risky','safe'],[]],
                  [[O([(1,1,.99),(1,1000,.01)]),O([(1,20,1.)])],[]])
        result = budget_dp(env,.9,B=2)
        self.assertAlmostEqual(result.value,20.)
        self.assertEqual(result.initial_budget,20)
        with self.assertRaises(RuntimeError): budget_dp(env,.9,B=2,max_budget=2)

    def test_random_acyclic(self):
        rng = np.random.default_rng(20261108)
        for _ in range(20):
            outs = [[O([(1,int(rng.integers(1,5)),.5),(2,int(rng.integers(1,5)),.5)])],
                    [O([(2,int(rng.integers(1,5)),.5),(2,int(rng.integers(5,10)),.5)]),
                     O([(2,int(rng.integers(2,8)),1.)])],[]]
            env = SSP('random',['S','M','G'],0,2,[['go'],['X','Y'],[]],outs)
            for alpha in [.5,.9]:
                best = min(discrete_cvar(d,alpha) for d in enumerate_policies(env))
                self.assertAlmostEqual(budget_dp(env,alpha,B=16).value,best,places=9)

    def test_invalid_inputs_and_limits(self):
        env=example1()
        for alpha in [0,1,np.nan]:
            with self.assertRaises(ValueError): budget_dp(env,alpha)
        with self.assertRaises(ValueError): budget_dp(env,B=-1)
        with self.assertRaises(ValueError): evaluate_policy(env,[-1,0,-1])
        with self.assertRaises(RuntimeError): value_iteration(env,max_iter=1)
        with self.assertRaises(ValueError): evaluate_distribution(env,[0,0,-1],cutoff=0)


if __name__ == '__main__':
    unittest.main()
