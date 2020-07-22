import unittest
from unittest.mock import MagicMock

import AssetFundNetwork
from AssetFundNetwork import Fund
from MarketImpactCalculator import MarketImpactCalculator
from Orders import Sell, Buy
from SysConfig import SysConfig
from constants import CHANCE, ATTACKER, BUY, SELL, SIM_TRADE, DEFENDER, MARKET
from flash_crash_players_cfr import FlashCrashRootChanceGameState, Budget
from solvers.ActionsManager import ActionsManager


def f1_margin_call_side_effect(assets):
    return assets['a1'].price == 0.5


def update_price_side_effects(num_shares, asset, sign):
    if sign > 0:
        return 1.5
    else:
        return 0.5

class TestFlashCrashPlayers_CFR  (unittest.TestCase):

    @staticmethod
    def fill_dict(tree_size, name, to_move, actions, history_assets_dict, budget, actions_history, inf_set, terminal=False, eval=None):
        return{'tree_size':tree_size, 'name':name,'to_move':to_move,'actions':actions,'actions_history':actions_history,
               'budget':budget,'history_assets_dict':history_assets_dict,'inf_set':inf_set,
               'terminal':terminal, 'eval':eval}

    def cmp_node(self, expected_node, actual_node):
        print(expected_node['name'])
        self.assertEqual(expected_node['tree_size'], actual_node.tree_size)
        self.assertEqual(expected_node['to_move'], actual_node.to_move)
        self.assertCountEqual(expected_node['actions'], actual_node.actions)
        self.assertEqual(expected_node['inf_set'], actual_node.inf_set())
        self.assertEqual(expected_node['terminal'], actual_node.is_terminal())
        if actual_node.is_terminal():
            self.assertEqual(expected_node['eval'], actual_node.evaluation())
        if 'actions_history' in expected_node:
            self.assertDictEqual(expected_node['actions_history'], actual_node.actions_history)
        if 'budget' in expected_node:
            self.assertEqual(expected_node['budget'], actual_node.budget)
        if 'history_assets_dict' in expected_node:
            self.assertDictEqual(expected_node['history_assets_dict'], actual_node.history_assets_dict)
        print(expected_node['name'] + ' ok')


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

        action_manager = ActionsManager(network.assets, 0.5 , 1)
        SysConfig.set("STEP_ORDER_SIZE", 0.5)

        f1.marginal_call = MagicMock(return_value=False)
        f2.marginal_call = MagicMock()
        f2.marginal_call.side_effect = f1_margin_call_side_effect
        actual_tree = FlashCrashRootChanceGameState(action_manager, af_network=network, defender_budget=50,
                                                    attacker_budgets=[40, 30])
        expected_tree = self.gen_tree()
        self.assertEqual(actual_tree.chance_prob(), 1./2)
        self.assertEqual(actual_tree.tree_size, 15)
        self.cmp_tree(expected_tree, actual_tree)


    def cmp_node_2(self, expected_node, actual_node):
        self.assertEqual(expected_node.to_move, actual_node.to_move)
        self.assertListEqual(expected_node.actions, actual_node.actions)
        self.assertListEqual(expected_node.actions_history, actual_node.actions_history)
        self.assertEqual(expected_node.budget, actual_node.budget)
        self.assertDictEqual(expected_node.history_assets_dict, actual_node.history_assets_dict)
        self.assertDictEqual(expected_node._information_set, actual_node._information_set)

    def gen_tree(self,):
        buy = str([Buy('a1', 50)])
        nope = str([])
        buy_actions = [nope,buy ]
        root = {'tree_size':15, 'name':'root', 'to_move':CHANCE,'actions':['40','30'],  'inf_set':'.', 'terminal':False }
        price_bump_log = "{'a1': '1->1.5'}"

        node_1_0 = self.fill_dict(tree_size= 7,name ='node_1_0',to_move=ATTACKER, actions = [nope] , history_assets_dict={BUY:{},SELL:{}},
                                  budget=Budget(attacker=40,defender=50), actions_history={BUY:[],SELL:[], SIM_TRADE:[]},
                                  inf_set= '.40.A_HISTORY:[]')

        node_1_0_0 = self.fill_dict(tree_size=6 ,name ='node_1_0_0',to_move=DEFENDER, actions=buy_actions,
                                    history_assets_dict={BUY: {}, SELL: {}},
                                    budget=Budget(attacker=40, defender=50),
                                    actions_history={BUY: [], SELL: [nope], SIM_TRADE: []}, inf_set='.50.D_HISTORY:[]')

        node_1_0_0_0 = self.fill_dict(tree_size= 4,name ='node_1_0_0_0',to_move=MARKET, actions=[price_bump_log], history_assets_dict={BUY: {'a1':1}, SELL: {}},
                                    budget=Budget(attacker=40, defender=0),
                                    actions_history={BUY: [buy], SELL: [nope], SIM_TRADE: []},
                                    inf_set=".MARKET_HISTORY:[].BUY:{'a1': 50}.SELL:{}")

        node_1_0_0_0_0 = self.fill_dict(tree_size= 3,name='node_1_0_0_0_0', to_move=ATTACKER, actions=[nope],
                                  history_assets_dict={BUY: {'a1':1}, SELL: {}},
                                  budget=Budget(attacker=40, defender=0),
                                  actions_history={BUY: [buy, price_bump_log], SELL: [nope, price_bump_log],
                                                   SIM_TRADE: [price_bump_log]},
                                  inf_set=".40.A_HISTORY:['[]', \"{'a1': '1->1.5'}\"]")

        node_1_0_0_0_0_0 = self.fill_dict(tree_size= 2,name='node_1_0_0_0_0_0', to_move=DEFENDER, actions=[nope],
                                    history_assets_dict={BUY: {'a1': 1}, SELL: {}},
                                    budget=Budget(attacker=40, defender=0),
                                    actions_history={BUY: [buy, price_bump_log], SELL: [nope, price_bump_log, nope],
                                                           SIM_TRADE: [price_bump_log]}
                                          , inf_set=".0.D_HISTORY:['[Buy a1 50]', \"{'a1': '1->1.5'}\"]")

        node_1_0_0_0_0_0_0 = self.fill_dict(tree_size= 1,name='node_1_0_0_0_0_0_0', to_move=MARKET, actions=[],
                                      history_assets_dict={BUY: {'a1': 1}, SELL: {}},
                                      budget=Budget(attacker=40, defender=0),
                                      actions_history={BUY: [buy, price_bump_log, nope],
                                                             SELL: [nope, price_bump_log, nope],
                                                             SIM_TRADE: [price_bump_log]},terminal=True,eval=0,
                                      inf_set=".MARKET_HISTORY:[\"{'a1': '1->1.5'}\"].BUY:{}.SELL:{}")


        node_1_0_0_1 = self.fill_dict(tree_size= 1,name ='node_1_0_0_1',to_move=MARKET, actions=[], history_assets_dict={BUY: {}, SELL: {}},
                                    budget=Budget(attacker=40, defender=50),
                                    actions_history={BUY: [nope], SELL: [nope], SIM_TRADE: []}, inf_set=".MARKET_HISTORY:[].BUY:{}.SELL:{}",terminal=True, eval=0)

        ###########
        node_1_1 = self.fill_dict(tree_size= 7,name ='node_1_1',to_move=ATTACKER, actions = [nope] , history_assets_dict={BUY:{},SELL:{}},
                                  budget=Budget(attacker=30,defender=50),
                                  actions_history={BUY:[],SELL:[], SIM_TRADE:[]},
                                  inf_set= '.30.A_HISTORY:[]')

        node_1_1_0 = self.fill_dict(tree_size= 6,name ='node_1_1_0',to_move=DEFENDER, actions=buy_actions,
                                    history_assets_dict={BUY: {}, SELL: {}},
                                    budget=Budget(attacker=30, defender=50),
                                    actions_history={BUY: [], SELL: [nope], SIM_TRADE: []}, inf_set='.50.D_HISTORY:[]')

        node_1_1_0_0 = self.fill_dict(tree_size= 4,name ='node_1_1_0_0',to_move=MARKET, actions=[price_bump_log], history_assets_dict={BUY: {'a1':1}, SELL: {}},
                                    budget=Budget(attacker=30, defender=0),
                                    actions_history={BUY: [buy], SELL: [nope], SIM_TRADE: []}, inf_set=".MARKET_HISTORY:[].BUY:{'a1': 50}.SELL:{}")

        node_1_1_0_0_0 = self.fill_dict(tree_size= 3,name='node_1_1_0_0_0', to_move=ATTACKER, actions=[nope],
                                  history_assets_dict={BUY: {'a1':1}, SELL: {}},
                                  budget=Budget(attacker=30, defender=0),
                                  actions_history={BUY: [buy, price_bump_log], SELL: [nope, price_bump_log], SIM_TRADE: [price_bump_log]}, inf_set=".30.A_HISTORY:['[]', \"{'a1': '1->1.5'}\"]")

        node_1_1_0_0_0_0 = self.fill_dict(tree_size= 2,name='node_1_1_0_0_0_0', to_move=DEFENDER, actions=[nope],
                                    history_assets_dict={BUY: {'a1': 1}, SELL: {}},
                                    budget=Budget(attacker=30, defender=0),
                                    actions_history={BUY: [buy, price_bump_log], SELL: [nope, price_bump_log, nope],
                                                           SIM_TRADE: [price_bump_log]}
                                          , inf_set=".0.D_HISTORY:['[Buy a1 50]', \"{'a1': '1->1.5'}\"]")

        node_1_1_0_0_0_0_0 = self.fill_dict(tree_size= 1,name='node_1_1_0_0_0_0_0', to_move=MARKET, actions=[],
                                      history_assets_dict={BUY: {'a1': 1}, SELL: {}},
                                      budget=Budget(attacker=30, defender=0),
                                      actions_history={BUY: [buy, price_bump_log, nope],
                                                             SELL: [nope, price_bump_log, nope],
                                                             SIM_TRADE: [price_bump_log]},terminal=True,eval=0,
                                      inf_set=".MARKET_HISTORY:[\"{'a1': '1->1.5'}\"].BUY:{}.SELL:{}")


        node_1_1_0_1 = self.fill_dict(tree_size= 1,name ='node_1_1_0_1',to_move=MARKET, actions=[], history_assets_dict={BUY: {}, SELL: {}},
                                    budget=Budget(attacker=30, defender=50),
                                    actions_history={BUY: [nope], SELL: [nope], SIM_TRADE: []}, inf_set=".MARKET_HISTORY:[].BUY:{}.SELL:{}",terminal=True, eval=0)

        ##########

        root['children'] = {'40': node_1_0, '30': node_1_1}

        node_1_0['children'] = {nope: node_1_0_0}
        node_1_0_0['children'] = {buy: node_1_0_0_0, nope: node_1_0_0_1}
        node_1_0_0_0['children'] = {price_bump_log:node_1_0_0_0_0}
        node_1_0_0_0_0['children'] = {nope:node_1_0_0_0_0_0}
        node_1_0_0_0_0_0['children'] = {nope:node_1_0_0_0_0_0_0}
        node_1_0_0_0_0_0_0['children'] = {}
        node_1_0_0_1['children'] = {}

        node_1_1['children'] = {nope: node_1_1_0}
        node_1_1_0['children'] = {buy: node_1_1_0_0, nope: node_1_1_0_1}
        node_1_1_0_0['children'] = {price_bump_log:node_1_1_0_0_0}
        node_1_1_0_0_0['children'] = {nope:node_1_1_0_0_0_0}
        node_1_1_0_0_0_0['children'] = {nope:node_1_1_0_0_0_0_0}
        node_1_1_0_0_0_0_0['children'] = {}
        node_1_1_0_1['children'] = {}
        return root
