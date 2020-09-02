import unittest
from math import inf
from unittest.mock import MagicMock

import AssetFundNetwork
from MarketImpactCalculator import MarketImpactCalculator
from Orders import Sell
from SysConfig import SysConfig

from constants import ATTACKER, MARKET, DEFENDER
from ActionsManager import ActionsManager
from solvers.minimax import minimax, MiniMaxTree, minimax2, alphabeta, single_agent
from mocks import MockFund, MockMarketImpactTestCalculator


class TestMinimax(unittest.TestCase):

    def compare_trees(self, actual_tree:MiniMaxTree, expected_tree:MiniMaxTree):
        self.assertEqual(actual_tree.player, expected_tree.player)
        self.assertEqual(actual_tree.value, expected_tree.value)
        kids_sort1 = sorted(actual_tree.children.keys())
        kids_sort2 = sorted(expected_tree.children.keys())
        self.assertEqual(kids_sort1,kids_sort2)
        for k in kids_sort1:
            self.compare_trees(actual_tree.children[k],expected_tree.children[k])

    def print_tree(self, tree: MiniMaxTree, prefix):
        print(tree.player)
        for action, subtree in tree.children.items():
            print(prefix + action)
            self.print_tree(subtree, prefix + '\t')

    def gen_tree(self):
        root = MiniMaxTree(ATTACKER)
        root.value = 0
        node1 = MiniMaxTree(MARKET, 0)
        node11 = MiniMaxTree(MARKET, 0)
        node2 = MiniMaxTree(DEFENDER, 0)
        node3 = MiniMaxTree(ATTACKER, 0)
        node4 = MiniMaxTree(ATTACKER, -1)
        node5 = MiniMaxTree(MARKET, -1)
        node6 = MiniMaxTree(MARKET, 0)
        node7 = MiniMaxTree(DEFENDER, 0)
        node8 = MiniMaxTree(ATTACKER, 0)
        node9 = MiniMaxTree(MARKET, 0)

        sell = '[Sell a1 2]'
        buy = '[Buy a1 2]'
        nope = '[]'
        market = 'MARKET'
        root.add_child(sell, node1)
        root.add_child(nope, node11)
        node1.add_child(market, node2)
        node2.add_child(buy, node3)
        node2.add_child(nope, node4)
        node3.add_child(nope, node6)
        node4.add_child(nope, node5)
      #  node6.add_child(market, node7)
      #  node7.add_child(nope, node8)
     #   node8.add_child(nope, node9)

        return root

    def gen_tree2(self):
        root = MiniMaxTree(ATTACKER, -1)
        node1 = MiniMaxTree(MARKET, 0)
        node2 = MiniMaxTree(MARKET, 0)
        node3 = MiniMaxTree(MARKET, 0)
        node4 = MiniMaxTree(MARKET, -1)

        node5 = MiniMaxTree(DEFENDER, 0)
        node6 = MiniMaxTree(DEFENDER, 0)
        node7 = MiniMaxTree(DEFENDER, -1)

        node8 = MiniMaxTree(MARKET, -1)
        node9 = MiniMaxTree(MARKET, 0)
        node10 = MiniMaxTree(MARKET, -2)
        node11 = MiniMaxTree(MARKET, 0)
        node12 = MiniMaxTree(MARKET, -3)
        node13 = MiniMaxTree(MARKET, -2)
        node14 = MiniMaxTree(MARKET, -1)

   #     node15 = MiniMaxTree(DEFENDER, 0)
   #     node16 = MiniMaxTree(DEFENDER, 0)
   #     node19 = MiniMaxTree(MARKET, 0)
   #     node20 = MiniMaxTree(MARKET, 0)

        nope = '[]'
        market = 'MARKET'

        root.add_child(nope, node1)
        root.add_child('[Sell a1 2]', node2)
        root.add_child('[Sell a2 2]', node3)
        root.add_child('[Sell a1 2, Sell a2 2]', node4)

        node2.add_child(market, node5)
        node3.add_child(market, node6)
        node4.add_child(market, node7)

        node5.add_child(nope, node8)
        node5.add_child('[Buy a1 2]', node9)

        node6.add_child(nope, node10)
        node6.add_child('[Buy a2 2]', node11)

        node7.add_child(nope, node12)
        node7.add_child('[Buy a1 2]', node13)
        node7.add_child('[Buy a2 2]', node14)

    #    node9.add_child(market, node15)
    #    node11.add_child(market, node16)

#        node15.add_child(nope, node19)
#        node16.add_child(nope, node20)

        return root

    def test_minimax(self):
        a1 = AssetFundNetwork.Asset(price=100, daily_volume=390, symbol='a1')
        f1 = MockFund('f1', a1, 0.82)
        SysConfig.set("STEP_ORDER_SIZE", 2/390)
        SysConfig.set("TIME_STEP_MINUTES", 1)
        SysConfig.set('DAILY_PORTION_PER_MIN',1/390)
        network = AssetFundNetwork.AssetFundsNetwork(funds = {'f1':f1},
                                                     assets={'a1':a1},
                                                     mi_calc=MockMarketImpactTestCalculator(),
                                                     limit_trade_step = True)

     #   value, actions, actual_tree = minimax(ROOT_ATTACKER, network, 205,190)
        actions_mgr = ActionsManager(network.assets, 2 / 390, 1)
        result = minimax(actions_mgr, ATTACKER, network, 205,190, True)
        expected_tree = self.gen_tree()

        print(result.value)
        print(result.actions)
        self.compare_trees(result.tree, expected_tree)
        self.assertEqual(int(result.network.assets['a1'].price),100)

    def run_one_time_attack_tree_test(self, pruning = False):
        a1 = AssetFundNetwork.Asset(price=100, daily_volume=390, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=100, daily_volume=390, symbol='a2')
        f1 = MockFund('f1', a1, 0.82)
        f2 = MockFund('f2', a2, 0.82)
        f3 = MockFund('f3', a2, 0.82)
        SysConfig.set("STEP_ORDER_SIZE", 2/390)
        SysConfig.set("TIME_STEP_MINUTES", 1)
        SysConfig.set('DAILY_PORTION_PER_MIN',1/390)
        SysConfig.set("MAX_NUM_ORDERS", 1)
        network = AssetFundNetwork.AssetFundsNetwork(funds = {'f1':f1, 'f2':f2, 'f3':f3},
                                                     assets={'a1':a1, 'a2':a2},
                                                     mi_calc=MockMarketImpactTestCalculator(),
                                                     limit_trade_step = True)

     #   value, actions, actual_tree = minimax(ROOT_ATTACKER, network, 205,190)
        actions_mgr = ActionsManager(network.assets,2/390, 1)
        if pruning:
            result = alphabeta(actions_mgr, ATTACKER, network, 405, 190, (-inf, inf), (inf, inf), True)
        else:
            result = minimax2(actions_mgr, ATTACKER, network, 405,190, True)
        expected_tree = self.gen_tree2()

        print(result.value)
        print(result.actions)
        self.compare_trees(result.tree, expected_tree)
        self.assertEqual(int(result.network.assets['a1'].price),81)
        self.assertEqual(int(result.network.assets['a2'].price),99)
        self.assertEqual(int(network.assets['a1'].price),100)
        self.assertEqual(int(network.assets['a2'].price),100)

    def test_minimax2(self):
        self.run_one_time_attack_tree_test(pruning=False)

    def test_alpha_beta(self):
        self.run_one_time_attack_tree_test(pruning=True)

    def test_single_agent(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=100, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=1, daily_volume=100, symbol='a1')

        f1 = AssetFundNetwork.Fund('f1', {'a2': 10}, 100, 1, 1)
        f2 = AssetFundNetwork.Fund('f2', {'a1': 20}, 100, 1, 1)
        mi_calc = MarketImpactCalculator()
        mi_calc.get_updated_price = MagicMock()
        mi_calc.get_updated_price.side_effect = update_price_side_effects
        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2}, assets={'a1': a1, 'a2':a2},
                                                     mi_calc=mi_calc, limit_trade_step=True)


        f1.marginal_call = MagicMock(return_value=False)
        f2.marginal_call = MagicMock()
        f2.marginal_call.side_effect = f1_margin_call_side_effect
        actions_mgr = ActionsManager(network.assets, 0.1, 2)
        result =single_agent(actions_mgr, network, 200)
        print(result.value)
        print(result.actions)
        self.assertEqual(result.value, -1)
        self.assertListEqual(result.actions, [[Sell('a1',20)], ['MARKET']])


def f1_margin_call_side_effect(assets):
    return assets['a1'].price == 0.25


def update_price_side_effects(num_shares, asset, sign):
    if sign > 0:
        if num_shares == 10:
            return 1.5
        if num_shares == 20:
            return 2
    else:
        if num_shares == 10:
            return 0.5
        if num_shares == 20:
            return 0.25


if __name__ == '__main__':
    unittest.main()
