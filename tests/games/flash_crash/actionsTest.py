import operator
import unittest

import AssetFundNetwork
from AssetFundNetwork import Fund
from Orders import Sell,  Buy
from SysConfig import SysConfig
from actions import get_possible_attacks, get_possible_defenses
from mocks import  MockMarketImpactTestCalculator


class TestActions  (unittest.TestCase):

    def test_get_root_possible_attacks(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=10, symbol='a1')
        a1.set_price(3)
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=4, symbol='a2')
        a2.set_price(4)
        a3 = AssetFundNetwork.Asset(price=7, daily_volume=2, symbol='a3')
        f1 = Fund('f1', {'a1': 10,'a2':10,'a3':10}, 100, 1, 1)
        f2 = Fund('f2', {'a1': 10}, 100, 1, 1)
        SysConfig.set("STEP_ORDER_SIZE", 0.5)
        network = AssetFundNetwork.AssetFundsNetwork(funds = {'f1':f1, 'f2':f2}, assets={'a1':a1, 'a2':a2, 'a3':a3}, mi_calc=MockMarketImpactTestCalculator())
        actual_orders = get_possible_attacks(network,10, True)
        expected_orders = []
        expected_orders.append(([Sell('a1',5)], 5))
        expected_orders.append(([Sell('a2', 2)], 4))
        expected_orders.append(([Sell('a3', 1)], 7))
        expected_orders.append(([Sell('a1', 5),Sell('a2', 2)], 9))
        self.assertEqual(actual_orders, expected_orders)

    def test_get_possible_attacks(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=10, symbol='a1')
        a1.set_price(3)
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=4, symbol='a2')
        a2.set_price(4)
        a3 = AssetFundNetwork.Asset(price=7, daily_volume=2, symbol='a3')
        f1 = Fund('f1', {'a1': 10,'a2':10,'a3':10}, 100, 1, 1)
        f2 = Fund('f2', {'a1': 10}, 100, 1, 1)
        SysConfig.set("STEP_ORDER_SIZE", 0.5)
        network = AssetFundNetwork.AssetFundsNetwork(funds = {'f1':f1, 'f2':f2}, assets={'a1':a1, 'a2':a2, 'a3':a3}, mi_calc=MockMarketImpactTestCalculator())
        actual_orders = get_possible_attacks(network,10)
        expected_orders = []
        expected_orders.append(([Sell('a1',5)], 5))
        expected_orders.append(([Sell('a2', 2)], 4))
        expected_orders.append(([Sell('a3', 1)], 7))
        expected_orders.append(([Sell('a1', 5),Sell('a2', 2)], 9))
        expected_orders.append(([],0))
        self.assertEqual(actual_orders, expected_orders)

    def test_get_possible_defenses(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=10, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=4, symbol='a2')
        a3 = AssetFundNetwork.Asset(price=7, daily_volume=2, symbol='a3')
        f1 = Fund('f1', {'a1': 10,'a2':10,'a3':10}, 100, 1, 1)
        f2 = Fund('f2', {'a1': 10}, 100, 1, 1)
        SysConfig.set("STEP_ORDER_SIZE", 0.5)
        network = AssetFundNetwork.AssetFundsNetwork(funds = {'f1':f1, 'f2':f2}, assets={'a1':a1, 'a2':a2, 'a3':a3}, mi_calc=MockMarketImpactTestCalculator())
        actual_orders = get_possible_defenses(network,10)
        expected_orders = []
        expected_orders.append(([Buy('a1',5)], 5))
        expected_orders.append(([Buy('a2', 2)], 4))
        expected_orders.append(([Buy('a3', 1)], 7))
        expected_orders.append(([ Buy('a1', 5),Buy('a2', 2)], 9))
        expected_orders.append(([],0))
        actual_orders.sort(key=operator.itemgetter(1))
        expected_orders.sort(key=operator.itemgetter(1))
        self.assertEqual(len(actual_orders), len(expected_orders))
        for i in range(0, len(actual_orders)):
            actual_orders[i][0].sort(key=lambda x:x.asset_symbol)
            expected_orders[i][0].sort(key=lambda x:x.asset_symbol)
            self.assertListEqual(actual_orders[i][0],expected_orders[i][0])
            self.assertEqual(actual_orders[i][1],expected_orders[i][1])

    def dont_test_get_possible_attacks(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=10, symbol='a1')
        a1.set_price(3)
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=4, symbol='a2')
        a2.set_price(4)
        a3 = AssetFundNetwork.Asset(price=7, daily_volume=2, symbol='a3')
        f1 = Fund('f1', {'a1': 10,'a2':10,'a3':10}, 100, 1, 1)
        f2 = Fund('f2', {'a1': 10}, 100, 1, 1)
        SysConfig.set("ORDER_SIZES", [0.5,1])
        network = AssetFundNetwork.AssetFundsNetwork(funds = {'f1':f1, 'f2':f2}, assets={'a1':a1, 'a2':a2, 'a3':a3}, mi_calc=MockMarketImpactTestCalculator())
        actual_orders = get_possible_attacks(network,10)
        expected_orders = []
        expected_orders.append(([Sell('a1',5)], 5))
        expected_orders.append(([Sell('a1',10)], 10))
        expected_orders.append(([Sell('a2', 2)], 4))
        expected_orders.append(([Sell('a2', 4)], 8))
        expected_orders.append(([Sell('a3', 1)], 7))
        expected_orders.append(([Sell('a2', 2), Sell('a1', 5)], 9))
        expected_orders.append(([],0))
        self.assertEqual(actual_orders, expected_orders)

    def dont_test_get_possible_defenses(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=10, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=4, symbol='a2')
        a3 = AssetFundNetwork.Asset(price=7, daily_volume=2, symbol='a3')
        f1 = Fund('f1', {'a1': 10,'a2':10,'a3':10}, 100, 1, 1)
        f2 = Fund('f2', {'a1': 10}, 100, 1, 1)
        SysConfig.set("ORDER_SIZES", [0.5,1])
        network = AssetFundNetwork.AssetFundsNetwork(funds = {'f1':f1, 'f2':f2}, assets={'a1':a1, 'a2':a2, 'a3':a3}, mi_calc=MockMarketImpactTestCalculator())
        actual_orders = get_possible_defenses(network,10)
        expected_orders = []
        expected_orders.append(([Buy('a1',5)], 5))
        expected_orders.append(([Buy('a1',10)], 10))
        expected_orders.append(([Buy('a2', 2)], 4))
        expected_orders.append(([Buy('a2', 4)], 8))
        expected_orders.append(([Buy('a3', 1)], 7))
        expected_orders.append(([Buy('a1', 5),Buy('a2', 2)], 9))
        expected_orders.append(([],0))
        self.assertEqual(actual_orders, expected_orders)

    def dont_test_get_possible_attacks_single_asset_per_attack(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=2, symbol='a1')
        f1 = Fund('f1', {'a1': 10}, 100, 1, 1)
        SysConfig.set("ORDER_SIZES", [0.5,1])
        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1}, assets={'a1': a1},
                                                     mi_calc=MockMarketImpactTestCalculator())
        actual_sell_orders = get_possible_attacks(network, 10)
        expected_sell_orders = []
        expected_sell_orders.append(([Sell('a1', 2)], 2))
        expected_sell_orders.append(([Sell('a1', 1)], 1))
        expected_sell_orders.append(([], 0))
        self.assertEqual(actual_sell_orders, expected_sell_orders)

    def dont_test_rounding(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=5, symbol='a1')
        f1 = Fund('f1', {'a1': 10}, 100, 1, 1)
        SysConfig.set("ORDER_SIZES", [0.5])
        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1}, assets={'a1': a1},
                                                     mi_calc=MockMarketImpactTestCalculator())
        actual_sell_orders = get_possible_attacks(network, 10)
        expected_sell_orders = []
        expected_sell_orders.append(([Sell('a1', 2)], 2))
        expected_sell_orders.append(([], 0))
        self.assertEqual(actual_sell_orders, expected_sell_orders)
        expected_buy_orders = get_possible_defenses(network, 10)
        actual_buy_orders = []
        expected_buy_orders.append(([Sell('a1', 2)], 2))
        expected_buy_orders.append(([], 0))
        self.assertEqual(actual_buy_orders, expected_buy_orders)
