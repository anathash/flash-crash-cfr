import unittest
from unittest.mock import MagicMock

import AssetFundNetwork
from AssetFundNetwork import Asset, Fund
from Orders import Sell,  Buy
from constants import BUY, SELL
from mocks import  MockMarketImpactTestCalculator

from ActionsManager import Attack, ActionsManager


class TestActionsManager  (unittest.TestCase):

    def test_filter_from_history(self):
        sell_action1 = Attack([Sell('a1', 1), Sell('a2', 1)], 10)
        sell_action2 = Attack([Sell('a1', 1),Sell('a3', 1)], 10)
        buy_action1 = Attack([Buy('a1', 1), Buy('a2', 1)], 10)
        buy_action2 = Attack([Buy('a2', 1)], 10)
        history = {BUY:{'a1':2},SELL:{'a1':1,'a2':2}}
        self.assertTrue(ActionsManager._ActionsManager__filter_from_history(sell_action1, history, SELL))
        self.assertFalse(ActionsManager._ActionsManager__filter_from_history(sell_action2, history, SELL))
        self.assertTrue(ActionsManager._ActionsManager__filter_from_history(buy_action1, history, BUY))
        self.assertFalse(ActionsManager._ActionsManager__filter_from_history(buy_action2, history, BUY))

    def test_get_single_orders(self):
        assets = {'a1':Asset(10,100,'a1'), 'a2':Asset(20, 200,'a2')}
        expected_sell_orders = [Sell('a1',10), Sell('a2',20)]
        expected_buy_orders = [Buy('a1',10), Buy('a2',20)]
        actions_mgr = ActionsManager(assets, 0.1)
        actual_buy_orders = actions_mgr._ActionsManager__get_single_orders(assets, ActionsManager._ActionsManager__gen_buy_order)
        actual_sell_orders = actions_mgr._ActionsManager__get_single_orders(assets, ActionsManager._ActionsManager__gen_sell_order)
        self.assertListEqual(expected_sell_orders, actual_sell_orders)
        self.assertListEqual(expected_buy_orders, actual_buy_orders)

    def test_funds_under_risk(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=100, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=200, symbol='a2')
        f1 = Fund('f1', {'a1': 10, 'a2': 10, 'a3': 10}, 100, 1, 1)
        f2 = Fund('f2', {'a1': 10}, 100, 1, 1)
        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2}, assets={'a1': a1, 'a2': a2},
                                                     mi_calc=MockMarketImpactTestCalculator())
        network.reset_order_books = MagicMock()
        network.simulate_trade = MagicMock()
        network.submit_sell_orders = MagicMock()
        network.get_funds_in_margin_calls = MagicMock(return_value = ['f1'])
        actions_mgr = ActionsManager(network.assets, 0.1)
        actual_funds = actions_mgr._ActionsManager__funds_under_risk(network)
        self.assertListEqual(actual_funds,['f1'])
        network.reset_order_books.assert_called_once()
        network.submit_sell_orders.assert_called_once_with([Sell('a1',10),Sell('a2',20)])
        network.simulate_trade.assert_called_once()
        network.get_funds_in_margin_calls.assert_called_once()

    def test_get_defenses_in_budget(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=100, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=200, symbol='a2')
        a3 = AssetFundNetwork.Asset(price=2, daily_volume=300, symbol='a3')
        assets = {'a1': a1, 'a2': a2, 'a3':a3}
        single_asset_orders = [Buy('a1', 10), Buy('a2', 20),Buy('a3', 30)]
        expected_defenses = [([Buy('a1', 10)],10),
                             ([Buy('a2', 20)],40),
                             ([Buy('a3', 30)],60),
                             ([Buy('a1', 10),Buy('a2', 20)],50)]
        actual_defenses = ActionsManager._ActionsManager__get_defenses_in_budget(assets, single_asset_orders,
                                                                lambda a: a.price,60)
        self.assertListEqual(expected_defenses, actual_defenses)

    def test_get_possible_defenses_integ(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=100, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=100, symbol='a2')
        a3 = AssetFundNetwork.Asset(price=3, daily_volume=100, symbol='a3')
        a4 = AssetFundNetwork.Asset(price=1, daily_volume=100, symbol='a4')
        f1 = Fund('f1', {'a1': 10, 'a2': 10, 'a3':10}, 100, 1, 1)
        f2 = Fund('f2', {'a4': 10}, 100, 1, 1)
        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2},
                                                     assets={'a1': a1, 'a2': a2, 'a3': a3, 'a4': a4},
                                                     mi_calc=MockMarketImpactTestCalculator())
        actions_mgr = ActionsManager(network.assets, 0.1)
        history = {BUY:{'a1':2}, SELL:{'a1':1, 'a2':2}}
        budget = 20
        actions_mgr._ActionsManager__funds_under_risk = MagicMock(return_value=['f1'])
        actual_defenses = actions_mgr.get_possible_defenses(network, budget , history)
        self.assertListEqual(actual_defenses, [([Buy('a2', 10)],20), ([], 0)])
        actions_mgr._ActionsManager__funds_under_risk.assert_called_once_with(network)

    def dont_test_get_possible_defenses_unit(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=100, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=100, symbol='a2')
        a3 = AssetFundNetwork.Asset(price=3, daily_volume=100, symbol='a3')
        a4 = AssetFundNetwork.Asset(price=1, daily_volume=100, symbol='a4')
        f1 = Fund('f1', {'a1': 10, 'a2': 10, 'a3':10}, 100, 1, 1)
        f2 = Fund('f2', {'a4': 10}, 100, 1, 1)
        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2},
                                                     assets={'a1': a1, 'a2': a2, 'a3': a3, 'a4': a4},
                                                     mi_calc=MockMarketImpactTestCalculator())
        actions_mgr = ActionsManager(network.assets, 0.1)
        actions_mgr.funds_under_risk = MagicMock(return_value=['f1'])
        actions_mgr.get_single_orders = MagicMock(return_value=[Buy('a1', 10),
                                                                Buy('a2', 10),
                                                                Buy('a3', 10)])
        expected_order_set = [[Buy('a1', 10)]]
        actions_mgr.get_defenses_in_budget = MagicMock(return_value= [(expected_order_set, 10)])
        history = {BUY:{'a1':2}, SELL:{'a1':1, 'a2':2}}
        budget = 60
        actual_defenses = actions_mgr.get_possible_defenses(network, budget , history)
        self.assertListEqual(actual_defenses, [(expected_order_set,10), ([], 0)])
        actions_mgr.funds_under_risk.assert_called_once_with(network)
        defense_assets = {'a2': a2,'a1': a1, 'a3': a3, }
        actions_mgr.get_single_orders.assert_called_once_with(defense_assets)
        filtered_defenses = [Buy('a2', 10), Buy('a3', 10)]
        actions_mgr.get_defenses_in_budget.assert_called_once_with(defense_assets, filtered_defenses)

    def test_get_portfolio_dict(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=100, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=100, symbol='a2')
        a3 = AssetFundNetwork.Asset(price=1, daily_volume=100, symbol='a3')
        a4 = AssetFundNetwork.Asset(price=1, daily_volume=100, symbol='a4')
        assets = {'a1': a1, 'a2': a2, 'a3': a3, 'a4': a4}
        actions_mgr = ActionsManager(assets, 0.1)
        attack1 = Attack([Sell('a1', 10)], 10)
        attack2 = Attack([Sell('a1', 10),Sell('a2',10)],40)
        attack3 = Attack([Sell('a3', 10)], 10)
        actions_mgr._ActionsManager__get_all_attacks = MagicMock(return_value=[attack1, attack2, attack3])
        expected_dict = {10: [attack1, attack3], 40: [attack2]}
        actual_dict = dict(actions_mgr._ActionsManager__get_portfolio_dict(assets))
        self.assertDictEqual(expected_dict,actual_dict)
        actions_mgr._ActionsManager__get_all_attacks.assert_called_once_with(assets, 4)

    def test_get_all_attacks(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=100, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=200, symbol='a2')
        a3 = AssetFundNetwork.Asset(price=3, daily_volume=300, symbol='a3')
        assets = {'a1': a1, 'a2': a2, 'a3': a3}
        expected_attacks = [Attack([Sell('a1', 10)],10),
                            Attack([Sell('a2', 20)],40),
                            Attack([Sell('a3', 30)], 90),
                            Attack([Sell('a1', 10), Buy('a2', 20)], 50),
                            Attack([Sell('a1', 10), Buy('a3', 30)], 100),
                            Attack([Sell('a2', 20), Buy('a3', 30)], 130),
                            Attack([Sell('a1', 10), Sell('a2', 20), Buy('a3', 30)], 140),
                            Attack([],0)
                            ]
        mgr = ActionsManager(assets, 0.1)
        actual_attacks = mgr._ActionsManager__get_all_attacks(assets, 3)
        actual_attacks.sort(key=lambda a: a.cost)
        expected_attacks.sort(key=lambda a: a.cost)
        self.assertListEqual(actual_attacks,expected_attacks)

    def test_constructor(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=100, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=200, symbol='a2')
        a3 = AssetFundNetwork.Asset(price=3, daily_volume=300, symbol='a3')
        assets = {'a1': a1, 'a2': a2, 'a3': a3}
        mgr = ActionsManager(assets, 0.1)
        sell_all_assets = [Sell('a1', 10),Sell('a2',20),Sell('a3',30)]
        portfolio_dict = {  10:[Attack([Sell('a1', 10)],10)],
                            40: [Attack([Sell('a2', 20)],40)],
                            90: [Attack([Sell('a3', 30)], 90)],
                            50: [Attack([Sell('a1', 10), Buy('a2', 20)], 50)],
                            100: [Attack([Sell('a1', 10), Buy('a3', 30)], 100)],
                            130: [Attack([Sell('a2', 20), Buy('a3', 30)], 130)],
                            140: [Attack([Sell('a1', 10), Sell('a2', 20), Buy('a3', 30)], 140)],
                            0: [Attack([],0)]}
        self.assertEqual(mgr._ActionsManager__step_order_size, 0.1)
        self.assertDictEqual({1:'a1',2:'a2',3:'a3'}, mgr._ActionsManager__id_to_sym)
        self.assertDictEqual(portfolio_dict, mgr._ActionsManager__portfolios_dict)
        self.assertListEqual([0, 10, 40, 50, 90, 100, 130, 140], list(mgr._ActionsManager__sorted_keys))
        self.assertListEqual(sell_all_assets, mgr._ActionsManager__sell_all_assets)

    def test_get_possible_attacks(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=100, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=200, symbol='a2')
        a3 = AssetFundNetwork.Asset(price=3, daily_volume=300, symbol='a3')
        assets = {'a1': a1, 'a2': a2, 'a3': a3}
        mgr = ActionsManager(assets, 0.1)
        history = {BUY:{'a1':2},SELL:{'a1':1,'a2':2}}
        expected_attacks = [([Sell('a1', 10)], 10),
                            ([Sell('a3', 30)], 90),
                            ([Sell('a1', 10), Sell('a3', 30)], 100),
                            ([], 0)]
        actual_attacks = mgr.get_possible_attacks(100, history)
        actual_attacks.sort(key=lambda a: a[1])
        expected_attacks.sort(key=lambda a: a[1])
        self.assertListEqual(expected_attacks, actual_attacks)

    def test_get_all_attacks(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=100, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=200, symbol='a2')
        assets = {'a1': a1, 'a2': a2}
        mgr = ActionsManager(assets, 0.1)
        expected_attacks = [([Sell('a1', 10)], 10),
                            ([Sell('a2', 20)], 40),
                            ([Sell('a1', 10), Sell('a2', 20)], 50),
                            ([], 0)]
        actual_attacks = mgr.get_possible_attacks()
        actual_attacks.sort(key=lambda a: a[1])
        expected_attacks.sort(key=lambda a: a[1])
        self.assertListEqual(expected_attacks, actual_attacks)

    def test_get_possible_attacks_no_history(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=100, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=200, symbol='a2')
        assets = {'a1': a1, 'a2': a2}
        mgr = ActionsManager(assets, 0.1)
        expected_attacks = [([Sell('a1', 10)], 10),
                            ([Sell('a2', 20)], 40),
                            ([], 0)]
        actual_attacks = mgr.get_possible_attacks(budget=40)
        actual_attacks.sort(key=lambda a: a[1])
        expected_attacks.sort(key=lambda a: a[1])
        self.assertListEqual(expected_attacks, actual_attacks)

    def test_get_possible_attacks_no_budget(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=100, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=200, symbol='a2')
        assets = {'a1': a1, 'a2': a2}
        history = {BUY:{'a1':2}, SELL:{'a1':1,'a2':2}}
        mgr = ActionsManager(assets, 0.1)
        expected_attacks = [([Sell('a1', 10)], 10),
                            ([], 0)]
        actual_attacks = mgr.get_possible_attacks(history=history)
        actual_attacks.sort(key=lambda a: a[1])
        expected_attacks.sort(key=lambda a: a[1])
        self.assertListEqual(expected_attacks, actual_attacks)

    def test_get_possible_attacks_zero_budget(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=100, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=200, symbol='a2')
        assets = {'a1': a1, 'a2': a2}
        mgr = ActionsManager(assets, 0.1)
        expected_attacks = [([], 0)]
        actual_attacks = mgr.get_possible_attacks(budget=0)
        actual_attacks.sort(key=lambda a: a[1])
        expected_attacks.sort(key=lambda a: a[1])
        self.assertListEqual(expected_attacks, actual_attacks)

    def test_get_portfolios_in_budget(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=100, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=200, symbol='a2')
        assets = {'a1': a1, 'a2': a2}
        mgr = ActionsManager(assets, 0.1, attacker_budgets = [20, 30])
        id2portfolios = mgr.get_portfolios()

        actual = mgr.get_portfolios_in_budget(10)
        expected_attacks = [Attack([], 0), Attack([Sell('a1',10)], 10)]
        actual_attacks= [id2portfolios[x] for x in actual]
        self.assertListEqual(expected_attacks, actual_attacks)

        actual = mgr.get_portfolios_in_budget(15)
        actual_attacks= [id2portfolios[x] for x in actual]
        self.assertListEqual(expected_attacks, actual_attacks)

    def test_get_portfolios_in_budget_dict(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=100, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=200, symbol='a2')
        assets = {'a1': a1, 'a2': a2}
        mgr = ActionsManager(assets, 0.1, attacker_budgets=[5, 10])
        id2portfolios = mgr.get_portfolios()
        actual = mgr.get_portfolios_in_budget_dict()
        expected_attacks_b5 = [Attack([], 0)]
        expected_attacks_b10 = [Attack([], 0), Attack([Sell('a1',10)], 10)]
        actual_attacks_b5= [id2portfolios[x] for x in actual[5]]
        actual_attacks_b10= [id2portfolios[x] for x in actual[10]]

        self.assertListEqual(expected_attacks_b5, actual_attacks_b5)
        self.assertListEqual(expected_attacks_b10, actual_attacks_b10)


