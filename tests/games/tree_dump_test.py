import unittest
from unittest.mock import MagicMock

import AssetFundNetwork
from ActionsManager import ActionsManager
from MarketImpactCalculator import MarketImpactCalculator
from SerializableState import save_tree_to_file, load_from_file
from SysConfig import SysConfig
from flash_crash_players_portfolio_cfr import PortfolioFlashCrashRootChanceGameState
from flash_crash_players_portfolio_per_attacker_cfr import PPAFlashCrashRootChanceGameState
from search.BinaryGrid import BinaryGrid
from search.ProbsGrid import ProbsGrid
from search.search_players_complete_game import SearchCompleteGameRootChanceGameState
from search.search_players_split_main_game import SearchMainGameRootChanceGameState
from split_selector_game import SelectorRootChanceGameState

def f1_margin_call_side_effect(assets):
    return assets['a1'].price == 0.5


def update_price_side_effects(num_shares, asset, sign):
    if sign > 0:
        return 1.5
    else:
        return 0.5

class DumpTreeTest  (unittest.TestCase):

    def cmp_tree(self, ser_tree, act_tree, p_ser, p_act):
        self.assertEqual(ser_tree.parent, p_ser)
        self.assertEqual(act_tree.parent, p_act)

        self.assertEqual(ser_tree.to_move, act_tree.to_move)
        self.assertCountEqual(ser_tree.actions, act_tree.actions)
        self.assertEqual(ser_tree.inf_set(), act_tree.inf_set())
        self.assertEqual(ser_tree.is_terminal(), act_tree.is_terminal())
        if ser_tree.is_terminal():
            self.assertEqual(ser_tree.evaluation(), act_tree.evaluation())
        if '_chance_prob' in act_tree.__dict__:
            self.assertEqual(ser_tree.chance_prob(), act_tree.chance_prob())
        else:
            self.assertIsNone(ser_tree.chance_prob())
        self.assertCountEqual(ser_tree.children.keys(), act_tree.children.keys())
        for k in ser_tree.children.keys():
            self.cmp_tree(ser_tree.children[k], act_tree.children[k], ser_tree ,act_tree)

    def cmp_ser_tree(self, actual_tree, filename):
        full_filename = '../resources/'+filename
        save_tree_to_file(actual_tree,full_filename )
        ser_tree = load_from_file(full_filename)
        self.cmp_tree(ser_tree, actual_tree, None, None)

    def test_selector_tree(self):
        attacker_budgets = [10, 20]
        attack_utilities = {'p1':0, 'p2':-1}
        actual_tree = SelectorRootChanceGameState(attacker_budgets, attack_utilities,
                                                                     {10:['p1', 'p2'], 20:['p1', 'p2']})

        self.cmp_ser_tree(actual_tree, 'test_selector_tree.json')

    def test_search_main_tree_probs(self):
        grid = ProbsGrid(2)
        attacker_budgets = [5, 11]
        goal_probs = grid.get_attacks_probabilities(attacker_budgets)

        actual_tree = SearchMainGameRootChanceGameState(rounds_left=2, grid=grid, goal_probs=goal_probs)
        self.cmp_ser_tree(actual_tree, 'test_search_main_tree_probs')

    def test_search_main_tree_binary(self):
        grid = BinaryGrid(2)
        attacker_budgets = [5, 11]
        goal_probs = grid.get_attacks_probabilities(attacker_budgets)

        actual_tree = SearchMainGameRootChanceGameState(rounds_left=2, grid=grid, goal_probs=goal_probs)
        self.cmp_ser_tree(actual_tree, 'test_search_main_tree_binary')

    def test_search_complete_tree_binary(self):
        grid = BinaryGrid(2)
        attacker_budgets = [4, 5, 11]

        actual_tree = SearchCompleteGameRootChanceGameState(grid=grid, attacker_budgets=attacker_budgets,
                                                     rounds_left=2)
        self.cmp_ser_tree(actual_tree, 'test_search_complete_tree_binary')

    def test_search_complete_tree_probs(self):
        grid = ProbsGrid(2)
        attacker_budgets = [4, 5, 11]

        actual_tree = SearchCompleteGameRootChanceGameState(grid=grid, attacker_budgets=attacker_budgets,
                                                     rounds_left=2)
        self.cmp_ser_tree(actual_tree, 'test_search_complete_tree_probs')

    def test_fc_complete_tree(self):
        attackers_budgets = [10, 50]
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=100, symbol='a1')
        f1 = AssetFundNetwork.Fund('f1', {'a1': 10}, 100, 1, 1)
        f2 = AssetFundNetwork.Fund('f2', {'a1': 20}, 100, 1, 1)
        mi_calc = MarketImpactCalculator()
        mi_calc.get_updated_price = MagicMock()
        mi_calc.get_updated_price.side_effect = update_price_side_effects
        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2}, assets={'a1': a1},
                                                     mi_calc=mi_calc, limit_trade_step=False)

        action_manager = ActionsManager(network.assets, 0.5, 1, attackers_budgets)
        SysConfig.set("STEP_ORDER_SIZE", 0.5)

        f1.marginal_call = MagicMock(return_value=False)
        f2.marginal_call = MagicMock()
        f2.marginal_call.side_effect = f1_margin_call_side_effect
        actual_tree = PPAFlashCrashRootChanceGameState(action_manager, af_network=network, defender_budget=50,
                                                       attacker_budgets=attackers_budgets)
        self.cmp_ser_tree(actual_tree, 'test_fc_complete_tree')

    def test_fc_main_tree(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=100, symbol='a1')
        f1 = AssetFundNetwork.Fund('f1', {'a1': 10}, 100, 1, 1)
        f2 = AssetFundNetwork.Fund('f2', {'a1': 20}, 100, 1, 1)
        mi_calc = MarketImpactCalculator()
        mi_calc.get_updated_price = MagicMock()
        mi_calc.get_updated_price.side_effect = update_price_side_effects
        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2}, assets={'a1': a1},
                                                     mi_calc=mi_calc, limit_trade_step=False)

        action_manager = ActionsManager(network.assets, 0.5, 1, [50, 30])
        SysConfig.set("STEP_ORDER_SIZE", 0.5)

        f1.marginal_call = MagicMock(return_value=False)
        f2.marginal_call = MagicMock()
        f2.marginal_call.side_effect = f1_margin_call_side_effect
        actual_tree = PortfolioFlashCrashRootChanceGameState(action_manager, af_network=network, defender_budget=50)
        self.cmp_ser_tree(actual_tree, 'test_fc_main_tree')
