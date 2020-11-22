import unittest

import numpy

from cfr import VanillaCFR
from constants import ATTACKER
from exp.archive.cfr_experiment_runner import compute_complete_game_equilibrium
from exp.root_generators import SearchRootGenerator, RootGenerator
from search.ProbsGrid import ProbsGrid
from search.search_players_complete_game import SearchCompleteGameRootChanceGameState
from search.search_players_split_main_game import SearchMainGameRootChanceGameState
from solvers.test_utils import compare_equilibrium
from split_game_cfr import SplitGameCFR


class TestSplitCFR(unittest.TestCase):

    def get_split_cfr_eq_old(self, attacker_budgets, iterations, rounds_left, stats = False):
        split_game_cfr = SplitGameCFR()
        grid = ProbsGrid(rounds_left)
        attacks_in_budget = grid.get_attacks_in_budget_dict(attacker_budgets)
        goal_probs = grid.get_attacks_probabilities(attacker_budgets)

        root = SearchMainGameRootChanceGameState(rounds_left=rounds_left,
                                                 grid=grid,
                                                 goal_probs=goal_probs)

        main_cfr, selector_cfr = split_game_cfr.run(main_game_root=root, attacker_types=attacker_budgets,
                                         iterations=iterations,
                           attacks_in_budget_dict=attacks_in_budget,
                           subgame_keys = [str(x) for x in goal_probs.keys()])
        if not stats:
            return  main_cfr, selector_cfr
        selector_results = split_game_cfr.get_selector_stats(main_cfr, selector_cfr, iterations, \
                                                             attacker_budgets, attacks_in_budget)
        main_results = split_game_cfr.get_main_results_stats(main_cfr, iterations)
        return main_results, selector_results


    def get_split_cfr_eq(self, attacker_budgets, iterations, rounds_left, stats = False):
        split_game_cfr = SplitGameCFR()
        grid = ProbsGrid(rounds_left)
        attacks_in_budget = grid.get_attacks_in_budget_dict(attacker_budgets)
        goal_probs = grid.get_attacks_probabilities(attacker_budgets)

        root = SearchMainGameRootChanceGameState(rounds_left=rounds_left,
                                                 grid=grid,
                                                 goal_probs=goal_probs)

        main_cfr, selector_cfr = split_game_cfr.run(main_game_root=root, attacker_types=attacker_budgets,
                                         iterations=iterations,
                           attacks_in_budget_dict=attacks_in_budget,
                           subgame_keys = [str(x) for x in goal_probs.keys()])
        if not stats:
            return  main_cfr, selector_cfr
        selector_results = split_game_cfr.get_selector_stats(main_cfr, selector_cfr, iterations, \
                                                             attacker_budgets, attacks_in_budget)
        main_results = split_game_cfr.get_main_results_stats(main_cfr, iterations)
        return main_results, selector_results



    def cmp_dict(self, dict1, dict2, inf_set):
        self.assertCountEqual(list(dict1.keys()), list(dict2.keys()))
        for k ,v in dict1.items():
            if not numpy.isclose(v, dict2[k], rtol=1e-05, atol=1e-08, equal_nan=False):
                print(inf_set)
            self.assertAlmostEqual(v, dict2[k], 5)

    def cmp_inf_sets_vals(self, attacker_budgets, selector_tree, split_main_treee, complete_tree):
        ignore_inf_set = ['.']
        for attacker_budget in attacker_budgets:
            ignore_inf_set.append('.' + str(attacker_budget))
        for inf_set, selector_sigma in selector_tree.items():
            if selector_sigma:
                self.cmp_dict(selector_sigma, complete_tree[inf_set], inf_set)
        for inf_set, sigma in complete_tree.items():
            if inf_set not in ignore_inf_set:
           #     print(inf_set)
                if inf_set[1].isdigit():
                    if inf_set[2].isdigit():
                        split_inf_set = inf_set[3:]
                    else:
                        split_inf_set = inf_set[2:]
                else:
                    split_inf_set = inf_set
                self.cmp_dict(sigma, split_main_treee[split_inf_set], inf_set)

    def cmp_split_to_complete(self, rounds, iterations):
        rounds_left = rounds
        iterations = iterations
        attacker_budgets = [4,5,11]
        main_results, selector_game_result = self.get_split_cfr_eq(attacker_budgets, iterations, rounds_left, True)

        grid = ProbsGrid(rounds_left=rounds_left)
        root = SearchCompleteGameRootChanceGameState(grid, attacker_budgets, rounds_left)
        vanilla_results = compute_complete_game_equilibrium(root=root,  attacker_budgets=attacker_budgets,
                                                            iterations=iterations)

        #compare sigma
        complete_sigma = vanilla_results['cfr'].sigma
        split_sigma = main_results['cfr'].sigma
        selector_sigma = selector_game_result['cfr'].sigma
        self.cmp_inf_sets_vals(attacker_budgets, selector_sigma, split_sigma, complete_sigma)
        print('PPA')
        print('defender = ' + str(vanilla_results['defender']))
        print('attackers = ' + str(vanilla_results['attackers']))
        print('sigma = ' + str(vanilla_results['sigma']))
        print('Split')
        print('defender = ' + str(selector_game_result['defender']))
        print('attackers = ' + str(selector_game_result['attackers']))
        print('sigma = ' + str(selector_game_result['sigma']))
        self.assertTrue(numpy.isclose(float(vanilla_results['defender']),
                                      float(selector_game_result['defender']), rtol=0.01, atol=0.01, equal_nan=False))
        for at in attacker_budgets:
            self.assertTrue(numpy.isclose(float(vanilla_results['attackers'][at]),
                                          float(selector_game_result['attackers'][at]), rtol=0.01, atol=0.01,
                                          equal_nan=False))
            self.assertDictEqual(vanilla_results['sigma'][at], selector_game_result['sigma'][at])

    def cmp_subtree(self,split_node, complete_node, split_cfr, complete_cfr, attacker_type):
#        self.assertCountEqual(list(complete_node.children.keys()), list(split_node.children.keys()))
        for k in complete_node.children:
            self.cmp_subtree(split_node.children[k], complete_node.children[k], split_cfr, complete_cfr, attacker_type)
        if complete_node.inf_set() == '.' or complete_node.inf_set() == '.'+str(attacker_type):
            return
        for action, eq in complete_cfr.nash_equilibrium[complete_node.inf_set()].items():
            if complete_node.to_move != ATTACKER:
                self.assertAlmostEqual(eq, split_cfr.nash_equilibrium[split_node.inf_set()][action], 5)
            else:
                if not numpy.isclose(eq, split_cfr.nash_equilibrium[split_node.inf_set()][attacker_type][action], rtol=1e-04, atol=1e-04, equal_nan=False):
    #        if not numpy.isclose(complete_node.value, split_node.value, rtol=1e-08, atol=1e-08, equal_nan=False):
    #        if split_node.inf_set() == '.(((1, 1), False), ((3, 1), False)).(((1, 0), False), ((3, 2), False)).(((1, 1), False), ((3, 1), False))':
            #if split_node.inf_set() == '.g:(4, 0).(0, 1).(1, 1)_False':
    #                print('value')
    #                print(complete_node.value)
    #                print(split_node.value)
                    print('inf sets')
                    print(complete_node.inf_set())
                    print(split_node.inf_set())

                    print('sigma')
                    print(complete_cfr.sigma[complete_node.inf_set()])
                    print(split_cfr.sigma[split_node.inf_set()])
                    print('cumulative sigma')
                    print(complete_cfr.cumulative_sigma[complete_node.inf_set()])
                    print(split_cfr.cumulative_sigma[split_node.inf_set()])
                    print('eq')
                    print(complete_cfr.nash_equilibrium[complete_node.inf_set()])
                    print(split_cfr.nash_equilibrium[split_node.inf_set()])
                #    print(split_node.value)
                    print('------------------------------------')
        #            self.assertAlmostEqual(split_node.value, complete_node.value, 5)
                    self.assertTrue(False)


    def dont_test_search_game_split_eq_complete_cfr(self):
        rounds_left = 4
        iterations = 2
        attacker_budgets = [4,5,11]

        exp_params = {'attacker_budgets':attacker_budgets, 'iterations':iterations, 'binary':False}
        root_generator = SearchRootGenerator(exp_params)
        root_generator.gen_roots(rounds_left)

        vanilla_results = compute_complete_game_equilibrium(root_generator.get_complete_game_root(),
                                                            exp_params['attacker_budgets'], iterations)


        split_game_cfr = SplitGameCFR()
        main_game_cfr, selector_cfr = split_game_cfr.run_split_cfr(root_generator, exp_params)
        selector_game_result = split_game_cfr.get_selector_stats(main_game_cfr, selector_cfr, iterations, \
                                                                 exp_params['attacker_budgets'],
                                                                 root_generator.get_attack_costs())


        complete_sigma = vanilla_results['cfr'].sigma
        split_sigma = main_game_cfr.sigma
        selector_sigma = selector_game_result['cfr'].sigma
        self.cmp_subtree(root_generator.get_split_main_game_root(),
                         root_generator.get_complete_game_root().children['11'],
                         main_game_cfr.nash_equilibrium,
                         vanilla_results['cfr'].nash_equilibrium)

        self.cmp_inf_sets_vals(attacker_budgets, selector_sigma, split_sigma, complete_sigma)
        # print(vanilla_results)
        # print(eq_split)
        print('PPA')
        print('defender = ' + str(vanilla_results['defender']))
        print('attackers = ' + str(vanilla_results['attackers']))
        print('sigma = ' + str(vanilla_results['sigma']))
        print('Split')
        print('defender = ' + str(selector_game_result['defender']))
        print('attackers = ' + str(selector_game_result['attackers']))
        print('sigma = ' + str(selector_game_result['sigma']))
        self.assertTrue(numpy.isclose(float(vanilla_results['defender']),
                                      float(selector_game_result['defender']), rtol=0.01, atol=0.01, equal_nan=False))
        for at in attacker_budgets:
            self.assertTrue(numpy.isclose(float(vanilla_results['attackers'][at]),
                                          float(selector_game_result['attackers'][at]), rtol=0.01, atol=0.01,
                                          equal_nan=False))
            self.assertDictEqual(vanilla_results['sigma'][at], selector_game_result['sigma'][at])


    def cmp_search_game_split_eq_complete_cfr_elements(self, iterations):
        rounds_left = 6
        attacker_budgets = [4,5,11]
        main_game_cfr, selector_cfr = self.get_split_cfr_eq(
            attacker_budgets, iterations, rounds_left)
        grid = ProbsGrid(rounds_left=rounds_left)
        complete_root = SearchCompleteGameRootChanceGameState(grid, attacker_budgets, rounds_left)
        vanilla_cfr = VanillaCFR(complete_root)
        vanilla_cfr.run(iterations=iterations)

        complete_sigma = vanilla_cfr.sigma
        split_sigma = main_game_cfr.sigma
        selector_sigma = selector_cfr.sigma
        self.cmp_inf_sets_vals(attacker_budgets, selector_sigma, split_sigma, complete_sigma)

    def dont_test_search_game_split_eq_complete_cfr_sigma(self):
        self.cmp_search_game_split_eq_complete_cfr_elements(1)
        self.cmp_search_game_split_eq_complete_cfr_elements(2)
        self.cmp_search_game_split_eq_complete_cfr_elements(10)
        self.cmp_search_game_split_eq_complete_cfr_elements(100)


    def run_test_search_equilibrium_old(self, rounds, iterations):
        rounds_left = rounds
        iterations = iterations
        attacker_budgets = [4,5,11]

        exp_params = {'attacker_budgets':attacker_budgets, 'iterations':iterations}
        root_generator = SearchRootGenerator(exp_params)
        root_generator.gen_roots(rounds_left)



        split_game_cfr = SplitGameCFR()
        main_game_cfr, selector_cfr = split_game_cfr.run_split_cfr(root_generator, exp_params)
        selector_game_result = split_game_cfr.get_selector_stats(main_game_cfr, selector_cfr, iterations, \
                                                                 exp_params['attacker_budgets'],
                                                                 root_generator.get_attack_costs())

        vanilla_results = compute_complete_game_equilibrium(root_generator.get_complete_game_root(),
                                                            exp_params['attacker_budgets'], iterations)

        complete_game_root = root_generator.get_complete_game_root()
        complete_cfr = vanilla_results['cfr']
        for b in attacker_budgets:
            inf_set = '.'+str(b)
            node = complete_game_root.children[str(b)]
            for action in node.actions:
                sigma = complete_cfr.nash_equilibrium[inf_set][action]
                #sigma = complete_cfr.sigma[inf_set][action]
               # if not numpy.isclose(sigma, 0, rtol=1e-05, atol=1e-08, equal_nan=False):
                self.cmp_subtree(split_node = root_generator.get_split_main_game_root().children[action],
                                 complete_node =  node.children[action],
                                 split_cfr = main_game_cfr,
                                 complete_cfr = vanilla_results['cfr'],
                                 attacker_type=b)

    def run_test_search_equilibrium(self, rounds, iterations):
        rounds_left = rounds
        iterations = iterations
        attacker_budgets = [4,5,11]

        exp_params = {'attacker_budgets':attacker_budgets, 'iterations':iterations, 'binary': False}
        root_generator = SearchRootGenerator(exp_params)
        root_generator.gen_roots(rounds_left, test=True)
        compare_equilibrium(self,  iterations, root_generator, attacker_budgets)


    def test_search_equilibrium(self):
        print(' 4 rounds')
        print('run_test_search_equilibrium(4, 1)')
        self.run_test_search_equilibrium(4, 1)
        print('run_test_search_equilibrium(4, 2)')
        self.run_test_search_equilibrium(4, 2)
        print('run_test_search_equilibrium(4, 10)')
        self.run_test_search_equilibrium(4, 10)
        print('run_test_search_equilibrium(4, 1000)')
        self.run_test_search_equilibrium(4, 1000)

        print(' 6 rounds')
        print('run_test_search_equilibrium(6, 1)')
        self.run_test_search_equilibrium(6, 1)
        print('run_test_search_equilibrium(6, 2)')
        self.run_test_search_equilibrium(6, 2)
        print('run_test_search_equilibrium(6, 10)')
        self.run_test_search_equilibrium(6, 10)
        print('run_test_search_equilibrium(6, 100)')
        self.run_test_search_equilibrium(6, 100)

    def test_loaded_tree_equilibrium_equal(self):
        attacker_budgets = [4,5,11]
        exp_params = {'attacker_budgets':attacker_budgets, 'iterations':100, 'binary': False}
        root_generator = SearchRootGenerator(exp_params)
        root_generator.gen_roots(4, True)
        filename = '../resources/cfr_test_search_rg.json'
        root_generator.save_roots_to_file(filename)
        loaded_root_generator = RootGenerator.load_root_generator(filename)
        compare_equilibrium(self, 2, loaded_root_generator, attacker_budgets)



if __name__ == '__main__':
    unittest.main()
