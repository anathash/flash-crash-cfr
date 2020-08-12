import unittest
from unittest.mock import MagicMock

import AssetFundNetwork
from AssetFundNetwork import Fund
from MarketImpactCalculator import MarketImpactCalculator
from Orders import Sell, Buy
from SysConfig import SysConfig
from constants import CHANCE, ATTACKER, BUY, SELL, SIM_TRADE, DEFENDER, MARKET
from flash_crash_players_portfolio_cfr import PortfolioFlashCrashRootChanceGameState, PlayersHiddenInfo
from ActionsManager import ActionsManager


def f1_margin_call_side_effect(assets):
    return assets['a1'].price == 0.5


def update_price_side_effects(num_shares, asset, sign):
    if sign > 0:
        return 1.5
    else:
        return 0.5

class TestFlashCrashPortfolioPlayers_CFR  (unittest.TestCase):

    @staticmethod
    def fill_dict(tree_size, to_move, actions, history_assets_dict, players_info, actions_history, inf_set, terminal, eval):
        return{'tree_size':tree_size,'to_move':to_move,'actions':actions,'actions_history':actions_history,
               'players_info':players_info,'history_assets_dict':history_assets_dict,'inf_set':inf_set,
               'terminal':terminal, 'eval':eval}

    def cmp_node(self, expected_node, actual_node):
        self.assertEqual(expected_node['tree_size'], actual_node.tree_size)
        self.assertEqual(expected_node['to_move'], actual_node.to_move)
        self.assertCountEqual(expected_node['actions'], actual_node.actions)
        self.assertEqual(expected_node['inf_set'], actual_node.inf_set())
        self.assertEqual(expected_node['terminal'], actual_node.is_terminal())
        if actual_node.is_terminal():
            self.assertEqual(expected_node['eval'], actual_node.evaluation())
        if 'actions_history' in expected_node:
            self.assertDictEqual(expected_node['actions_history'], actual_node.actions_history)
        if actual_node.to_move != 'CHANCE':
            self.assertEqual(expected_node['players_info'], actual_node.players_info)


    def cmp_tree(self, expected_tree, actual_tree):
        self.cmp_node(expected_tree, actual_tree)
        kids_sort1 = sorted(actual_tree.children.keys())
        kids_sort2 = sorted(expected_tree['children'].keys())
        self.assertEqual(kids_sort1, kids_sort2)
        for k in kids_sort1:
            self.cmp_tree(expected_tree['children'][k], actual_tree.children[k])

    def test_tree(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=100, symbol='a1')
        f1 = Fund('f1', {'a1': 10}, 100, 1, 1)
        f2 = Fund('f2', {'a1': 20}, 100, 1, 1)
        mi_calc = MarketImpactCalculator()
        mi_calc.get_updated_price = MagicMock()
        mi_calc.get_updated_price.side_effect = update_price_side_effects
        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2}, assets={'a1': a1},
                                                     mi_calc=mi_calc, limit_trade_step =False)

        action_manager = ActionsManager(network.assets, 0.5 , 1, [50,30])
        SysConfig.set("STEP_ORDER_SIZE", 0.5)

        f1.marginal_call = MagicMock(return_value=False)
        f2.marginal_call = MagicMock()
        f2.marginal_call.side_effect = f1_margin_call_side_effect
        actual_tree = PortfolioFlashCrashRootChanceGameState(action_manager, af_network=network, defender_budget=50)
        expected_tree = self.gen_tree()
        self.assertEqual(actual_tree.chance_prob(), {'p1':0.75,'p2':0.25})
        self.assertEqual(actual_tree.tree_size, 8)
        self.cmp_tree(expected_tree, actual_tree)

    def gen_tree(self,):
        sell_order = Sell('a1', 50)
        sell = str([sell_order])
        buy = str([Buy('a1', 50)])
        nope = str([])
        buy_actions = [nope,buy ]
        root = {'tree_size':8, 'to_move':CHANCE,'actions':['p1','p2'],  'inf_set':'.', 'terminal':False }
        price_drop_log= "{'a1': '1->0.5'}"
        empty_log = '{}'

        node_1_0 = self.fill_dict(tree_size=6, to_move=ATTACKER, actions = [sell], history_assets_dict={BUY:{},SELL:{}},
                                  players_info=PlayersHiddenInfo(attacker_attack=[sell_order],attacker_pid='p2',
                                                                 defender_budget=50),
                                  actions_history={BUY:[],SELL:[], SIM_TRADE:[]},inf_set= '.p2.A_HISTORY:[]',
                                  terminal=False, eval=None)

        node_1_0_0 = self.fill_dict(tree_size=5 , to_move=DEFENDER, actions=buy_actions, history_assets_dict={BUY: {}, SELL: {'a1':1}},
                                    players_info=PlayersHiddenInfo(attacker_attack=[],attacker_pid='p2', defender_budget=50),
                                    actions_history={BUY: [], SELL: [sell], SIM_TRADE: []}, inf_set='.50.D_HISTORY:[]',
                                    terminal=False, eval=None)


        node_1_0_0_0 = self.fill_dict(tree_size=2,to_move=MARKET, actions=[empty_log], history_assets_dict={BUY: {'a1':1}, SELL: {'a1':1}},
                                      players_info=PlayersHiddenInfo(attacker_attack=[], attacker_pid='p2',
                                                                     defender_budget=0),
                                    actions_history={BUY: [buy], SELL: [sell], SIM_TRADE: []},
                                      inf_set=".MARKET_HISTORY:[].BUY:{'a1': 50}.SELL:{'a1': 50}",
                                      terminal=False, eval=None)

        node_1_0_0_1 = self.fill_dict(tree_size=2,to_move=MARKET, actions=[price_drop_log],
                                      history_assets_dict={BUY: {}, SELL: {'a1': 1}},
                                      players_info=PlayersHiddenInfo(attacker_attack=[], attacker_pid='p2',
                                                                     defender_budget=50),
                                      actions_history={BUY: [nope], SELL: [sell], SIM_TRADE: []},
                                      inf_set=".MARKET_HISTORY:[].BUY:{}.SELL:{'a1': 50}",
                                      terminal=False, eval=None)

        node_1_0_0_0_0 = self.fill_dict(tree_size = 1,terminal=True, eval=0, to_move=ATTACKER, actions=[], history_assets_dict={BUY: {'a1':1}, SELL: {'a1':1}},
                                        players_info=PlayersHiddenInfo(attacker_attack=[], attacker_pid='p2',
                                                                       defender_budget=0),
                                    actions_history={BUY: [buy, empty_log], SELL: [sell, empty_log], SIM_TRADE: [empty_log]}, inf_set=".p2.A_HISTORY:['[Sell a1 50]', '{}']")

        node_1_0_0_1_0 = self.fill_dict(tree_size = 1,terminal=True, eval=-1, to_move=ATTACKER, actions=[], history_assets_dict={BUY: {'a1':1}, SELL: {'a1':1}},
                                        players_info=PlayersHiddenInfo(attacker_attack=[], attacker_pid='p2',
                                                                       defender_budget=50),
                                    actions_history={BUY: [nope, price_drop_log], SELL: [sell, price_drop_log], SIM_TRADE: [price_drop_log]}, inf_set=".p2.A_HISTORY:['[Sell a1 50]', \"{'a1': '1->0.5'}\"]")

        ###########
        node_1_1 = self.fill_dict(tree_size = 1, terminal=True, eval=0, to_move=ATTACKER, actions = [] , history_assets_dict={BUY:{},SELL:{}},
                                  players_info=PlayersHiddenInfo(attacker_attack=[], attacker_pid='p1',
                                                                 defender_budget=50), actions_history={BUY:[],SELL:[], SIM_TRADE:[]},inf_set= '.p1.A_HISTORY:[]')

        ##########

        root['children'] = {'p2': node_1_0, 'p1': node_1_1}
        node_1_0['children'] = {sell: node_1_0_0}
        node_1_0_0['children'] = {buy:  node_1_0_0_0, nope: node_1_0_0_1}
        node_1_0_0_0['children'] = {empty_log: node_1_0_0_0_0}
        node_1_0_0_1['children'] = {price_drop_log: node_1_0_0_1_0}
        node_1_0_0_0_0['children'] = {}
        node_1_0_0_1_0['children'] = {}
        node_1_1['children'] = {}
        return root
