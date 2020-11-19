import unittest

import numpy

from SysConfig import SysConfig
from cfr import VanillaCFR
from exp.archive.cfr_experiment_runner import compute_cfr_equilibrium, compute_complete_game_equilibrium
from exp.network_generators import get_network_from_dir, gen_new_network
from ActionsManager import ActionsManager
from exp.root_generators import FlashCrashRootGenerator
from flash_crash_players_portfolio_cfr import PortfolioFlashCrashRootChanceGameState
from flash_crash_players_portfolio_per_attacker_cfr import PPAFlashCrashRootChanceGameState
from solvers.test_utils import compare_equilibrium
from split_game_cfr import SplitGameCFR


class TestSplitCFR(unittest.TestCase):

    def test_flash_crash_split_eq_cfr(self):
        exp_params = {'defender_budget': 2000000000,
                      'attacker_budgets': [4000000000, 6000000000],
                      'main_game_iteration_portion': 0.9,
                      'min_iterations': 10,
                      'max_iterations': 100,
                      'jump': 10,
                      'num_assets': 3,
                      'step_order_size': SysConfig.get("STEP_ORDER_SIZE") * 2,
                      'max_order_num': 1}
        network  = get_network_from_dir('../resources/three_assets_net')
        network.limit_trade_step = True
        (main_game_results, selector_game_result) = self.get_flash_crash_split_cfr_eq(exp_params['defender_budget'],
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

    def dont_test_flash_crash_split_eq_ppa_cfr(self):
        exp_params = {'defender_budget': 2000000000,
                      'attacker_budgets': [4000000000, 8000000000, 12000000000],
                      'iterations': 300,
                      'num_assets': 3,
                      'step_order_size': SysConfig.get("STEP_ORDER_SIZE") * 2,
                      'max_order_num': 1}
        iterations = exp_params['iterations']
        root_generator = FlashCrashRootGenerator(exp_params)
        root_generator.gen_roots(exp_params['num_assets'])
        split_game_cfr = SplitGameCFR()
        main_game_cfr, selector_cfr = split_game_cfr.run_split_cfr(root_generator, exp_params)

        selector_game_result = split_game_cfr.get_selector_stats(main_game_cfr, selector_cfr, iterations, \
                                                             exp_params['attacker_budgets'],
                                                             root_generator.get_attack_costs())
        main_results = split_game_cfr.get_main_results_stats(main_game_cfr, iterations)

        vanilla_results = compute_complete_game_equilibrium(root_generator.get_complete_game_root(),
                                                            exp_params['attacker_budgets'], exp_params['iterations'])
        complete_sigma = vanilla_results['cfr'].sigma
        split_sigma = main_results['cfr'].sigma
        selector_sigma = selector_game_result['cfr'].sigma
        self.cmp_inf_sets_vals(exp_params['attacker_budgets'], selector_sigma, split_sigma, complete_sigma)
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
            self.cmp_dict('', vanilla_results['sigma'][at], selector_game_result['sigma'][at])
#            self.assertDictEqual(vanilla_results['sigma'][at], selector_game_result['sigma'][at])

    def cmp_dict(self, inf_set, sigma1, sigma2):
        self.assertCountEqual(list(sigma1.keys()), list(sigma2.keys()))
        for k, v in sigma1.items():
            self.assertAlmostEqual(v, sigma2[k], 5)
            #if v != sigma2[k]:
            #    print(inf_set)

    def cmp_inf_sets_vals(self, attacker_budgets, selector_tree, split_main_treee, complete_tree):
        ignore_inf_set = ['.']
        for attacker_budget in attacker_budgets:
            ignore_inf_set.append('.' + str(attacker_budget))
        for inf_set, selector_sigma in selector_tree.items():
            if selector_sigma:
                self.cmp_dict(inf_set, selector_sigma, complete_tree[inf_set])
        for inf_set, sigma in complete_tree.items():
            if inf_set not in ignore_inf_set:
                #   print(inf_set)
                if 'A_HISTORY' in inf_set:
                    budget = '.' + inf_set.split('.')[1]
                    split_inf_set = inf_set.split(budget)[1]
                else:
                    split_inf_set = inf_set
                self.cmp_dict(inf_set, sigma, split_main_treee[split_inf_set])

    def cmp_fc_game_split_eq_complete_cfr_sigma(self, iterations, game_size):
        exp_params = {'defender_budget': 2000000000,
                      'attacker_budgets': [4000000000, 8000000000, 12000000000],
                      'step_order_size': SysConfig.get("STEP_ORDER_SIZE") * 2,
                      'max_order_num': 1,
                      'iterations':iterations}

        root_generator = FlashCrashRootGenerator(exp_params)
        root_generator.gen_roots(game_size)
        split_game_cfr = SplitGameCFR()
        main_game_cfr, selector_cfr = split_game_cfr.run_split_cfr(root_generator, exp_params)
        complete_root = root_generator.get_complete_game_root()
        vanilla_cfr = VanillaCFR(complete_root)
        vanilla_cfr.run(iterations=iterations)
        complete_sigma = vanilla_cfr.sigma
        split_sigma = main_game_cfr.sigma
        selector_sigma = selector_cfr.sigma
        self.cmp_inf_sets_vals(exp_params['attacker_budgets'], selector_sigma, split_sigma, complete_sigma)

    def cmp_equilibrium(self, game_size, iterations):
        exp_params = {'defender_budget': 2000000000,
                      'attacker_budgets': [4000000000, 8000000000, 12000000000],
                      'step_order_size': SysConfig.get("STEP_ORDER_SIZE") * 2,
                      'max_order_num': 1,
                      'iterations': iterations}

        root_generator = FlashCrashRootGenerator(exp_params)
      #  root_generator.gen_roots(game_size, test = True)
        compare_equilibrium(self, game_size, iterations, root_generator, exp_params['attacker_budgets'])

    def test_equilibrium_equal(self):
        print(' 3 assets')
        print('test_equilibrium_equal(3, 1)')
        self.cmp_equilibrium(3, 1)
        print('run_test_search_equilibrium(3, 2)')
        self.cmp_equilibrium(3, 2)
        print('run_test_search_equilibrium(3, 10)')
        self.cmp_equilibrium(3, 10)
        print('run_test_search_equilibrium(3, 1000)')
        self.cmp_equilibrium(3, 1000)

        print(' 4 assets')
        print('test_equilibrium_equal(4, 1)')
        self.cmp_equilibrium(4, 1)
        print('run_test_search_equilibrium(4, 2)')
        self.cmp_equilibrium(4, 2)
        print('run_test_search_equilibrium(4, 10)')
        self.cmp_equilibrium(4, 10)
        print('run_test_search_equilibrium(4, 1000)')
        self.cmp_equilibrium(4, 1000)

    def dont_test_fc_game_split_eq_complete_cfr_sigma(self):
        self.cmp_fc_game_split_eq_complete_cfr_sigma(1, 3)
        self.cmp_fc_game_split_eq_complete_cfr_sigma(2, 3)
        self.cmp_fc_game_split_eq_complete_cfr_sigma(10, 3)
        self.cmp_fc_game_split_eq_complete_cfr_sigma(100, 3)

        self.cmp_fc_game_split_eq_complete_cfr_sigma(1, 4)
        self.cmp_fc_game_split_eq_complete_cfr_sigma(2, 4)
        self.cmp_fc_game_split_eq_complete_cfr_sigma(10, 4)
        self.cmp_fc_game_split_eq_complete_cfr_sigma(100, 4)

if __name__ == '__main__':
    unittest.main()
