import unittest

import numpy
from numpy import isclose

from SysConfig import SysConfig
from exp.cfr_experiment_runner import compute_cfr_equilibrium, compute_cfr_ppa_equilibrium
from exp.network_generators import get_network_from_dir
from solvers.ActionsManager import ActionsManager
from solvers.split_game_cfr import SplitGameCFR

class TestSplitCFR(unittest.TestCase):

    def get_split_cfr_eq(self, defender_budget, attacker_budgets, network, step_order_size,
                             max_order_num, iterations1, iterations2):
        network.limit_trade_step = True
        # assets, step_order_size, max_order_num=1, attacker_budgets
        cfr_actions_mgr = ActionsManager(assets=network.assets, step_order_size=step_order_size,
                                         max_order_num=max_order_num, attacker_budgets=attacker_budgets)

        split_game_cfr = SplitGameCFR()
        run_results = split_game_cfr.run(action_mgr=cfr_actions_mgr, network=network, defender_budget=defender_budget,
                          attacker_budgets=attacker_budgets,
                          game1_iterations=iterations1,
                          game2_iterations=iterations2,
                          round=1)
        return run_results

    def test_split_eq_cfr(self):
        exp_params = {'defender_budget': 2000000000,
                      'attacker_budgets': [4000000000, 6000000000],
                      'main_game_iteration_portion': 0.9,
                      'min_iterations': 10,
                      'max_iterations': 100,
                      'jump': 10,
                      'num_assets': 3,
                      'step_order_size': SysConfig.get("STEP_ORDER_SIZE") * 2,
                      'max_order_num': 1}
        network  = get_network_from_dir('../../../../results/three_assets_net')
        network.limit_trade_step = True
        (main_game_results, selector_game_result) = self.get_split_cfr_eq(exp_params['defender_budget'],
                                         exp_params['attacker_budgets'],
                                         network,
                                         exp_params['step_order_size'],
                                         exp_params['max_order_num'],
                                         800,
                                         200)

        vanilla_actions_mgr = ActionsManager(assets=network.assets, step_order_size=exp_params['step_order_size'],
                                             max_order_num=exp_params['max_order_num'])
        vanilla_results = compute_cfr_equilibrium(vanilla_actions_mgr, network, exp_params['defender_budget'],
                                          exp_params['attacker_budgets'], 1000)
        print('Vanilla')
        print('defender = ' + str(vanilla_results['defender']))
        print('attackers = ' + str(vanilla_results['attackers']))
        print('Split')
        print('defender = ' + str(selector_game_result['defender']))
        print('attackers = ' +str(selector_game_result['attackers']))
        self.assertTrue (numpy.isclose(float(vanilla_results['defender']),
                         float(selector_game_result['defender']), rtol=0.01, atol=0.01, equal_nan=False))
        for at in exp_params['attacker_budgets']:
            self.assertTrue(numpy.isclose(float(vanilla_results['attackers'][at]),
                                          float(selector_game_result['attackers'][at]), rtol=0.01, atol=0.01, equal_nan=False))

    def test_split_eq_ppa_cfr(self):
        exp_params = {'defender_budget': 2000000000,
                      'attacker_budgets': [4000000000, 6000000000],
                      'main_game_iteration_portion': 0.9,
                      'min_iterations': 10,
                      'max_iterations': 100,
                      'jump': 10,
                      'num_assets': 3,
                      'step_order_size': SysConfig.get("STEP_ORDER_SIZE") * 2,
                      'max_order_num': 1}
        network  = get_network_from_dir('../../../../resources/three_assets_net')
        network.limit_trade_step = True
        main_game_results, selector_game_result = self.get_split_cfr_eq(exp_params['defender_budget'],
                                         exp_params['attacker_budgets'],
                                         network,
                                         exp_params['step_order_size'],
                                         exp_params['max_order_num'],
                                         8,
                                         20)

        vanilla_actions_mgr = ActionsManager(assets=network.assets, step_order_size=exp_params['step_order_size'],
                                             max_order_num=exp_params['max_order_num'],attacker_budgets=  exp_params['attacker_budgets'])


        vanilla_results = compute_cfr_ppa_equilibrium(vanilla_actions_mgr, network, exp_params['defender_budget'],
                                          exp_params['attacker_budgets'], 30)
       # print(vanilla_results)
       # print(eq_split)
        print('PPA')
        print('defender = ' + str(vanilla_results['defender']))
        print('attackers = ' + str(vanilla_results['attackers']))
        print('sigma = ' + str(vanilla_results['sigma']))
        print('Split')
        print('defender = ' + str(selector_game_result['defender']))
        print('attackers = ' +str(selector_game_result['attackers']))
        print('sigma = ' +str(selector_game_result['sigma']))
        self.assertTrue (numpy.isclose(float(vanilla_results['defender']),
                         float(selector_game_result['defender']), rtol=0.01, atol=0.01, equal_nan=False))
        for at in exp_params['attacker_budgets']:
            self.assertTrue(numpy.isclose(float(vanilla_results['attackers'][at]),
                                          float(selector_game_result['attackers'][at]), rtol=0.01, atol=0.01, equal_nan=False))
            self.assertDictEqual(vanilla_results['sigma'][at], selector_game_result['sigma'][at])

if __name__ == '__main__':
    unittest.main()
