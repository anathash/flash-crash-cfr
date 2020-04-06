import unittest


import AssetFundNetwork
from SysConfig import SysConfig

from constants import ATTACKER, MARKET, DEFENDER, ROOT_ATTACKER
from minimax import minimax, MiniMaxTree
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
        root = MiniMaxTree(ROOT_ATTACKER)
        root.value = 0
        node1 = MiniMaxTree(MARKET, 0)
        node2 = MiniMaxTree(DEFENDER, 0)
        node3 = MiniMaxTree(ATTACKER, 0)
        node4 = MiniMaxTree(ATTACKER, -1)
        node5 = MiniMaxTree(MARKET, -1)
        node6 = MiniMaxTree(MARKET, 0)
        node7 = MiniMaxTree(DEFENDER, 0)
        node8 = MiniMaxTree(ATTACKER, 0)
        node9 = MiniMaxTree(MARKET, 0)

        sell = '[Sell a1 2.0]'
        buy = '[Buy a1 2.0]'
        nope = '[]'
        market = 'MARKET'
        root.add_child(sell, node1)
        node1.add_child(market, node2)
        node2.add_child(buy, node3)
        node2.add_child(nope, node4)
        node4.add_child(nope, node5)
        node3.add_child(nope, node6)
        node6.add_child(market, node7)
        node7.add_child(nope, node8)
        node8.add_child(nope, node9)

        return root

    def test_minimax(self):
        a1 = AssetFundNetwork.Asset(price=100, daily_volume=390, symbol='a1')
        f1 = MockFund('f1', a1,0.82)
        SysConfig.set("STEP_ORDER_SIZE", 2/390)
        SysConfig.set("TIME_STEP_MS", 60000)
        network = AssetFundNetwork.AssetFundsNetwork(funds = {'f1':f1},
                                                     assets={'a1':a1},
                                                     mi_calc=MockMarketImpactTestCalculator(),
                                                     limit_trade_step = True)

     #   value, actions, actual_tree = minimax(ROOT_ATTACKER, network, 205,190)
        result = minimax(ROOT_ATTACKER, network, 205,190)
        expected_tree = self.gen_tree()

        print(result.value)
        print(result.actions)
        self.compare_trees(result.tree, expected_tree)
        self.assertEqual(int(result.network.assets['a1'].price),99)

if __name__ == '__main__':
    unittest.main()
