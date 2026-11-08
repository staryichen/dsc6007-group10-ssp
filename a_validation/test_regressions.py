"""防错与随机小环境交叉检查，不使用外部测试依赖。"""
from fractions import Fraction as F
import random
import unittest

from check_budget_dp import oracle, reference_dp, exhaustive_optimum, distribution_of_policy
from ssp.mdp import SSP, make_outcomes
from ssp.envs.acyclic import example1


class VerificationChecks(unittest.TestCase):
    """检查非法输入、求解范围和独立穷举的一致性。"""

    def test_invalid_distributions(self):
        """无效概率和空分布应明确报错。"""
        for dist in [{}, {1:F(1,2)}, {1:F(-1),2:F(2)}, {-1:F(1)}]:
            with self.subTest(dist=dist), self.assertRaises(ValueError):
                oracle.risk_metrics(dist,F(9,10))
        for alpha in [0,1,-1]:
            with self.subTest(alpha=alpha), self.assertRaises(ValueError):
                oracle.risk_metrics({1:F(1)},alpha)

    def test_partial_atom(self):
        """只取分位点原子的部分概率，而不是整个条件尾部。"""
        _,var,cvar,_=oracle.risk_metrics({2:F(81,100),26:F(1,10),31:F(9,100)},F(9,10))
        self.assertEqual(var,26)
        self.assertEqual(cvar,F(61,2))

    def test_invalid_actions_and_bounds(self):
        """负动作、无效预算及不足以证明全局搜索的范围均应被拒绝。"""
        env=example1()
        for action in [-1,10,0.5]:
            policy={pair:action for pair in oracle.reachable_pairs(env)}
            with self.subTest(action=action), self.assertRaises(ValueError):
                oracle.exact_distribution(env,policy)
        for bound in [-1,0,2.5]:
            with self.subTest(bound=bound), self.assertRaises(ValueError):
                reference_dp(env,bound,F(9,10))

    def test_unreachable_state(self):
        """起点不可达但可到终点的状态仍须有合法参考值。"""
        env=SSP(name='unreachable',state_names=['S','U','G'],start=0,goal=2,
                actions=[['go'],['go'],[]],outcomes=[
                    [make_outcomes([(2,1,1.)])],[make_outcomes([(2,2,1.)])],[]])
        mean,value,_,_=reference_dp(env,2,F(9,10))
        self.assertEqual(mean[1],2)
        self.assertEqual(value,1)

    def test_cycle_is_rejected(self):
        """有环 SSP 可以是 proper，但不在这个 DAG 参考求解器的范围内。"""
        env=SSP(name='cycle',state_names=['S','G'],start=0,goal=1,
                actions=[['go'],[]],outcomes=[[make_outcomes([(0,1,.5),(1,1,.5)])],[]])
        with self.assertRaises(ValueError):
            reference_dp(env,10,F(9,10))
        with self.assertRaises(ValueError):
            oracle.exact_distribution(env,{(0,0):0})

    def test_random_small_dags(self):
        """固定二十个种子，各比较三个 α，共六十个独立小环境案例。"""
        for seed in range(20):
            rng=random.Random(seed)
            actions=[['a','b'],['x','y'],[]]
            outcomes=[]
            for state in range(2):
                row=[]
                for action in range(2):
                    targets=[rng.choice([1,2]) for _ in range(2)] if state==0 else [2,2]
                    row.append(make_outcomes([(targets[i],rng.randint(1,5),.5) for i in range(2)]))
                outcomes.append(row)
            outcomes.append([])
            env=SSP(name=f'dag_{seed}',state_names=['S','M','G'],start=0,goal=2,
                    actions=actions,outcomes=outcomes)
            for alpha in [F(1,2),F(9,10),F(19,20)]:
                with self.subTest(seed=seed,alpha=alpha):
                    _,value,_,choose=reference_dp(env,10,alpha)
                    self.assertEqual(value,exhaustive_optimum(env,alpha))
                    self.assertEqual(value,oracle.risk_metrics(distribution_of_policy(env,choose),alpha)[2])


if __name__=='__main__':
    unittest.main(verbosity=2)
