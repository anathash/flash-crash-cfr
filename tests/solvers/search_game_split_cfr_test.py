import unittest

import numpy

from exp.archive.cfr_experiment_runner import compute_complete_game_equilibrium
from search.Grid import Grid
from search.search_players_complete_game import SearchCompleteGameRootChanceGameState
from search.search_players_split_main_game import SearchMainGameRootChanceGameState
from split_game_cfr import SplitGameCFR


class TestSplitCFR(unittest.TestCase):

    def get_split_cfr_eq(self, attacker_budgets, iterations1, iterations2, rounds_left):
        split_game_cfr = SplitGameCFR()
        grid = Grid(rounds_left)
        attacks_in_budget = grid.get_attacks_in_budget_dict(attacker_budgets)
        goal_probs = grid.get_attacks_probabilities(attacker_budgets)

        root = SearchMainGameRootChanceGameState(rounds_left=rounds_left,
                                                 grid=grid,
                                                 goal_probs=goal_probs)

        run_results = split_game_cfr.run(main_game_root=root, attacker_types=attacker_budgets,
                           game1_iterations=iterations1,
                           game2_iterations=iterations2,
                           attacks_in_budget_dict=attacks_in_budget,
                           subgame_keys = [str(x) for x in goal_probs.keys()],
                           game_2_pure=False)

        return run_results

    def test_search_game_split_eq_complete_cfr(self):
        rounds_left = 3
        attacker_budgets = [4,5,11]
        main_game_results, selector_game_result = self.get_split_cfr_eq(attacker_budgets, 90, 10, rounds_left)
        grid = Grid(rounds_left=rounds_left)
        root = SearchCompleteGameRootChanceGameState(grid, attacker_budgets, rounds_left)
        vanilla_results = compute_complete_game_equilibrium(root=root,  attacker_budgets=attacker_budgets, iterations=90)
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


if __name__ == '__main__':
    unittest.main()
