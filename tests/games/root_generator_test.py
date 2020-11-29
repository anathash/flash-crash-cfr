import unittest
from unittest.mock import MagicMock

import AssetFundNetwork
from ActionsManager import ActionsManager
from MarketImpactCalculator import MarketImpactCalculator
from SerializableState import save_tree_to_file, load_from_file
from SysConfig import SysConfig
from exp.root_generators import FlashCrashRootGenerator, SearchRootGenerator, RootGenerator
from flash_crash_players_portfolio_cfr import PortfolioFlashCrashRootChanceGameState
from flash_crash_players_portfolio_per_attacker_cfr import PPAFlashCrashRootChanceGameState
from search.BinaryGrid import BinaryGrid
from search.ProbsGrid import ProbsGrid
from search.search_players_complete_game import SearchCompleteGameRootChanceGameState
from search.search_players_split_main_game import SearchMainGameRootChanceGameState
from split_selector_game import SelectorRootChanceGameState

class RootGeneratorTest  (unittest.TestCase):

    def cmp_tree(self, ser_tree, act_tree, p_ser, p_act):
        self.assertEqual(ser_tree.parent, p_ser)
        self.assertEqual(act_tree.parent, p_act)

        self.assertEqual(ser_tree.to_move, act_tree.to_move)
        self.assertEqual(ser_tree.tree_size, act_tree.tree_size)
        self.assertCountEqual(ser_tree.actions, act_tree.actions)
        self.assertEqual(ser_tree.inf_set(), act_tree.inf_set())
        self.assertEqual(ser_tree.is_terminal(), act_tree.is_terminal())
        if ser_tree.is_terminal():
            self.assertEqual(ser_tree.evaluation(), act_tree.evaluation())
        if '_chance_prob' in act_tree.__dict__ or act_tree.to_move == 0:
            self.assertEqual(ser_tree.chance_prob(), act_tree.chance_prob())
        else:
            self.assertIsNone(ser_tree.chance_prob())
        self.assertCountEqual(ser_tree.children.keys(), act_tree.children.keys())
        for k in ser_tree.children.keys():
            self.cmp_tree(ser_tree.children[k], act_tree.children[k], ser_tree, act_tree)


    def test_fc_root_generator_save_and_load(self):
        exp_params = {
            'game_size': 3,
            'defender_budget': 400000,
            'attacker_budgets': [450000,  900000],
            'step_order_size': SysConfig.get("STEP_ORDER_SIZE") * 2,
            'max_order_num': 1,
            'net_type': 'uniform'}

        root_generator = FlashCrashRootGenerator(exp_params)
        root_generator.gen_roots(game_size=3, test = True)
        filename = '../resources/root_generator_fc.json'
        root_generator.save_roots_to_file(filename)
        exp_params['trees_file'] = filename
        loaded_root_generator = FlashCrashRootGenerator(exp_params)
        loaded_root_generator.gen_roots(game_size = 4, test = False)
        self.assertDictEqual(root_generator.get_attack_costs(),
                         loaded_root_generator.get_attack_costs())

        self.assertCountEqual(list(root_generator.get_attack_keys()),
                         loaded_root_generator.get_attack_keys())

        self.cmp_tree(ser_tree = loaded_root_generator.get_split_main_game_root(),
                      act_tree = root_generator.get_split_main_game_root(),
                      p_ser = None, p_act = None)

        self.cmp_tree(ser_tree=loaded_root_generator.get_complete_game_root(),
                      act_tree = root_generator.get_complete_game_root(),
                      p_ser=None, p_act=None)

    def test_search_root_generator_save_and_load(self):
        filename = '../resources/root_generator_search.json'
        exp_params = {'game_size': 4,
                      'attacker_budgets': [4, 5, 11],
                      'binary': True}

        # 2500000
        root_generator = SearchRootGenerator(exp_params)
        root_generator.gen_roots(game_size=4, test=True)
        root_generator.save_roots_to_file(filename)
        exp_params['trees_file'] = filename
        loaded_root_generator = SearchRootGenerator(exp_params)
        loaded_root_generator.gen_roots(game_size=6, test=False)
        self.assertDictEqual(root_generator.get_attack_costs(),
                         loaded_root_generator.get_attack_costs())

        self.assertCountEqual(list(root_generator.get_attack_keys()),
                         loaded_root_generator.get_attack_keys())

        self.cmp_tree(ser_tree = loaded_root_generator.get_split_main_game_root(),
                      act_tree = root_generator.get_split_main_game_root(),
                      p_ser = None, p_act = None)

        self.cmp_tree(ser_tree=loaded_root_generator.get_complete_game_root(),
                      act_tree = root_generator.get_complete_game_root(),
                      p_ser=None, p_act=None)
