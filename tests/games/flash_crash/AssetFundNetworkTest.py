import unittest
from unittest.mock import MagicMock, call

import networkx as nx
import numpy as np

import AssetFundNetwork
from AssetFundNetwork import AssetFundsNetwork, Asset, Fund
from MarketImpactCalculator import MarketImpactCalculator, ExponentialMarketImpactCalculator
from Orders import Sell, NoLimitOrder, Buy
from SysConfig import SysConfig


class MockMarketImpactTestCalculator(MarketImpactCalculator):
    def get_market_impact(self, order: NoLimitOrder, asset):
        sign = -1 if isinstance(order, Sell) else 1
        if sign > 0:
            return asset.daily_volume/order.num_shares
        else:
            return order.num_shares / asset.daily_volume

    def get_updated_price(self, num_shares, asset, sign):
        return asset.price * (1 + sign * 0.1 * num_shares)


class TestAssetFundsNetwork  (unittest.TestCase):

    def test_encode_decode_network(self):
        network = AssetFundsNetwork.generate_random_network(0.5, 3, 2, [1]*3, [2]*3, [1]*2, [2]*3, [1]*3,[1.5]*3,
                                                            ExponentialMarketImpactCalculator(1))
        network.save_to_file('../../../resources/encoding_decoding_test.json')
        decoded_network = AssetFundsNetwork.load_from_file('../../../resources/encoding_decoding_test.json',
                                                           ExponentialMarketImpactCalculator(1))
        self.assertEqual(network, decoded_network)

    def test_generate_random_network(self):
        num_funds = 3
        num_assets = 2

        assets_num_shares = [3, 4]
        initial_prices = [1, 2]
        volatility = [1.5, 1]

        initial_capitals = [100, 200, 300]
        initial_leverages = [1, 2, 3]
        tolerances = [4, 5, 6]


        g = AssetFundsNetwork.generate_random_network(0.5, num_funds, num_assets,initial_capitals,
                                                      initial_leverages, initial_prices,
                                                      tolerances, assets_num_shares, volatility,
                                                      ExponentialMarketImpactCalculator(1))
        assets = g.assets
        funds = g.funds
        self.assertEqual(len(assets), num_assets)
        self.assertEqual(len(funds), num_funds)
        for i in range(len(assets)):
            asset = assets['a' + str(i)]
            self.assertEqual(initial_prices[i], asset.price)
            self.assertEqual(assets_num_shares[i], asset.daily_volume)
            self.assertEqual(volatility[i], asset.volatility)
        for i in range(len(funds)):
            fund = funds['f' + str(i)]
            self.assertEqual(initial_capitals[i], fund.initial_capital)
            self.assertEqual(initial_leverages[i], fund.initial_leverage)
            self.assertEqual(tolerances[i], fund.tolerance)

    def test_generate_network_from_graph(self):
        num_funds = 2
        num_assets = 2
        daily_volumes = [3, 4]
        volatility = [1.5, 1, 1.1]
        initial_prices = [1, 2]
        initial_capitals = [100, 200]
        initial_leverages = [1, 2]
        tolerances = [4, 5]
        investment_proportions = {'f0': [0.6, 0.4], 'f1': [1.0]}
        g = nx.DiGraph()
        g.add_nodes_from([0, 1, 2, 3])
        g.add_edges_from([(0, 2), (0, 3), (1, 3)])
        network = AssetFundsNetwork.gen_network_from_graph(g=g, investment_proportions=investment_proportions,
                                                           initial_capitals=initial_capitals,
                                                           initial_leverages=initial_leverages,assets_initial_prices=initial_prices,
                                                           tolerances=tolerances, daily_volumes=daily_volumes,
                                                           volatility=volatility,
                                                           mi_calc=ExponentialMarketImpactCalculator(1))
        assets = network.assets
        funds = network.funds
        self.assertEqual(len(assets), num_assets)
        self.assertEqual(len(funds), num_funds)
        for i in range(len(assets)):
            asset = assets['a' + str(i)]
            self.assertEqual(initial_prices[i], asset.price)
            self.assertEqual(daily_volumes[i], asset.daily_volume)
            self.assertEqual(volatility[i], asset.volatility)
        for i in range(len(funds)):
            fund = funds['f' + str(i)]
            self.assertEqual(initial_capitals[i], fund.initial_capital)
            self.assertEqual(initial_leverages[i], fund.initial_leverage)
            self.assertEqual(tolerances[i], fund.tolerance)
        prot0 = funds['f0'].portfolio
        self.assertEqual(len(prot0.items()), 2)
        self.assertEqual(prot0['a0'], 120)
        self.assertEqual(prot0['a1'], 40)

        prot1 = funds['f1'].portfolio
        self.assertEqual(len(prot1.items()), 1)
        self.assertEqual(prot1['a1'], 300)
        self.assertTrue('a0' not in prot1)


    def test_gen_network_from_graph_with_assets(self):
        num_funds = 2
        assets= {'A1':Asset(price=1, daily_volume=3, symbol='A1', volatility=1.5),
                 'A2': Asset(price=2, daily_volume=4, symbol='A2', volatility=1)}
        initial_capitals = [100, 200]
        initial_leverages = [1, 2]
        tolerances = [4, 5]
        investment_proportions = {'f0': [0.6, 0.4], 'f1': [1.0]}
        g = nx.DiGraph()
        g.add_nodes_from([0, 1, 2, 3])
        g.add_edges_from([(0, 2), (0, 3), (1, 3)])
        network = AssetFundsNetwork.gen_network_from_graph_with_assets(g=g, investment_proportions=investment_proportions,
                                                           initial_capitals=initial_capitals,
                                                           initial_leverages=initial_leverages,
                                                           tolerances=tolerances,
                                                           assets = assets,
                                                           mi_calc=ExponentialMarketImpactCalculator(1))
        assets = network.assets
        funds = network.funds
        self.assertEqual(len(assets), 2)
        self.assertEqual(len(funds), num_funds)
        self.assertTrue((network.assets, assets))
        for i in range(len(funds)):
            fund = funds['f' + str(i)]
            self.assertEqual(initial_capitals[i], fund.initial_capital)
            self.assertEqual(initial_leverages[i], fund.initial_leverage)
            self.assertEqual(tolerances[i], fund.tolerance)
        prot0 = funds['f0'].portfolio
        self.assertEqual(len(prot0.items()), 2)
        self.assertEqual(prot0['A1'], 120)
        self.assertEqual(prot0['A2'], 40)

        prot1 = funds['f1'].portfolio
        self.assertEqual(len(prot1.items()), 1)
        self.assertEqual(prot1['A2'], 300)
        self.assertTrue('A1' not in prot1)

    def test_update_funds(self):
        assets = {'XXX': Asset(1, 20, 1.5, 'XXX'), 'YYY': Asset(1, 20, 1.5, 'yyy')}
        f1 = Fund('F1', {'XXX': 10, 'YYY': 10}, 5, 2, 0.25)
        f2 = Fund('F1', {'XXX': 5, 'YYY': 4}, 5, 2, 0.25)
        f3 = Fund('F1', {'XXX': 20, 'YYY': 4}, 5, 2, 4)

        network = AssetFundsNetwork({'f1': f1, 'f2': f2, 'f3': f3}, assets,
                                    MockMarketImpactTestCalculator())
        network.update_funds()

        self.assertTrue(f1.is_in_margin_call())
        self.assertFalse(f1.default())

        self.assertTrue(f2.is_in_margin_call())
        self.assertTrue(f2.default())

        self.assertFalse(f3.is_in_margin_call())
        self.assertFalse(f3.default())

        """a0 = Asset(price=1, daily_volume=40, volatility=1.5, symbol='a0')
        a1 = Asset(price=2, daily_volume=40, volatility=1.5, symbol='a1')
        f0 = Fund('f0', {'a0': 10}, initial_capital=2, initial_leverage=8, tolerance=1.01)
        f1 = Fund('f1', {'a0': 10, 'a1': 1}, initial_capital=1, initial_leverage=1, tolerance=1.01)
        network = AssetFundsNetwork({'f0': f0, 'f1': f1}, {'a0': a0, 'a1': a1},
                                    MockMarketImpactTestCalculator())
        a = [Sell('a0', num_shares=10, share_price=2), Buy('a1', num_shares=10, share_price=2)]
        network.update_funds()

        expected_a0 = Asset(price=0.0625, daily_volume=40, volatility=1.5, symbol='a0')
        expected_a1 = Asset(price=8.0, daily_volume=40, volatility=1.5, symbol='a1')
        expected_f0 = Fund('f0', {}, initial_capital=2, initial_leverage=8, tolerance=1.01)
        expected_network = AssetFundsNetwork({'f0': expected_f0, 'f1': f1}, {'a0': expected_a0, 'a1': expected_a1},
                                             MockMarketImpactTestCalculator())

        self.assertEqual(network, expected_network)"""

    def test_get_canonical_form(self):
        a0 = Asset(price=1, daily_volume=40, volatility=1.5, symbol='a0')
        a1 = Asset(price=2, daily_volume=40, volatility=1.5, symbol='a1')
        f0 = Fund('f0', {'a0': 10}, initial_capital=2, initial_leverage=8, tolerance=2)
        f1 = Fund('f1', {'a0': 10, 'a1': 10}, initial_capital=1, initial_leverage=1, tolerance=3)
        network = AssetFundsNetwork({'f0': f0, 'f1': f1}, {'a0': a0, 'a1': a1},
                                    MockMarketImpactTestCalculator())
        expected_canonical_form = np.array([[10., 0.], [10., 20.]])
        actual_canonical_form = network.get_canonical_form()
        self.assertTrue(np.array_equal(expected_canonical_form, actual_canonical_form))

    def test_run_intraday_simulation_price_rises(self):
        a0 = Asset(price=1, daily_volume=40, volatility=1.5, symbol='a0')
        a1 = Asset(price=2, daily_volume=40, volatility=1.5, symbol='a1')
        f0 = Fund('f0', {'a0': 10}, initial_capital=2, initial_leverage=8, tolerance=2)
        f1 = Fund('f1', {'a0': 10, 'a1': 1}, initial_capital=1, initial_leverage=1, tolerance=3)
        network = AssetFundsNetwork({'f0': f0, 'f1': f1}, {'a0': a0, 'a1': a1},
                                    MockMarketImpactTestCalculator())
        network.run_intraday_simulation(1.5, 1)
        self.assertTrue(a0.price >= 1)
        self.assertTrue(a1.price >= 2)

    def test_run_intraday_simulation_goal_leverage_reached(self):
        a0 = Asset(price=1, daily_volume=40, volatility=1.5, symbol='a0')
        a1 = Asset(price=2, daily_volume=40, volatility=1.5, symbol='a1')
        f0 = Fund('f0', {'a0': 10}, initial_capital=2, initial_leverage=8, tolerance=2)
        f1 = Fund('f1', {'a0': 10, 'a1': 1}, initial_capital=1, initial_leverage=1, tolerance=3)
        assets = {'a0': a0, 'a1': a1}
        network = AssetFundsNetwork({'f0': f0, 'f1': f1}, assets,
                                    MockMarketImpactTestCalculator())
        network.run_intraday_simulation(2, 0.8)
        self.assertTrue(f0.compute_curr_leverage(assets) <= 0.8)
        self.assertTrue(f1.compute_curr_leverage(assets) <= 0.8)


    def test_run_intraday_simulation_raises_exception_for_price_reduction(self):
        a0 = Asset(price=1, daily_volume=40, volatility=1.5, symbol='a0')
        a1 = Asset(price=2, daily_volume=40, volatility=1.5, symbol='a1')
        f0 = Fund('f0', {'a0': 10}, initial_capital=2, initial_leverage=8, tolerance=2)
        f1 = Fund('f1', {'a0': 10, 'a1': 1}, initial_capital=1, initial_leverage=1, tolerance=3)
        network = AssetFundsNetwork({'f0': f0, 'f1': f1}, {'a0': a0, 'a1': a1},
                                    MockMarketImpactTestCalculator())

        with self.assertRaises(ValueError):
            network.run_intraday_simulation(0.8, 0.7)

    def test_simulate_trade_only_sell(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=1, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=1, symbol='a2')
        f1 = Fund('f1', {'a1' : 10}, 100, 1, 1)
        f2 = Fund('f2', {'a2' : 10}, 100, 1, 1)
        mi_calc = MarketImpactCalculator()
        mi_calc.get_updated_price = MagicMock(return_value=0.5)
        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2}, assets={'a1': a1, 'a2': a2},
                                                     mi_calc=mi_calc, limit_trade_step= False)
        network.submit_sell_orders([Sell('a1',2)])
        log = network.simulate_trade()
        mi_calc.get_updated_price.assert_called_once_with(2, a1, -1)
        self.assertDictEqual({'a1':'1->0.5'},log)
        self.assertFalse(network.buy_orders)
        self.assertFalse(network.sell_orders)
        self.assertTrue(a1.price == 0.5)
        self.assertTrue(a2.price == 2)

    def test_simulate_trade_only_buy(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=1, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=1, symbol='a2')
        f1 = Fund('f1', {'a1' : 10}, 100, 1, 1)
        f2 = Fund('f2', {'a2' : 10}, 100, 1, 1)
        mi_calc = MarketImpactCalculator()
        mi_calc.get_updated_price = MagicMock(return_value=1.5)
        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2}, assets={'a1': a1, 'a2': a2},
                                                     mi_calc=mi_calc, limit_trade_step= False)
        network.submit_buy_orders([Buy('a1',2)])
        log = network.simulate_trade()
        mi_calc.get_updated_price.assert_called_once_with(2, a1, 1)
        self.assertDictEqual({'a1': '1->1.5'}, log)
        self.assertFalse(network.buy_orders)
        self.assertFalse(network.sell_orders)
        self.assertTrue(a1.price == 1.5)
        self.assertTrue(a2.price == 2)

    def test_simulate_trade_mix_trades(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=1, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=1, symbol='a2')
        f1 = Fund('f1', {'a1' : 10}, 100, 1, 1)
        f2 = Fund('f2', {'a2' : 10}, 100, 1, 1)
        mi_calc = MarketImpactCalculator()
        mi_calc.get_updated_price = MagicMock(return_value=1.5)

        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2}, assets={'a1': a1, 'a2': a2},
                                                     mi_calc=mi_calc, limit_trade_step= False)

        network.submit_sell_orders([Sell('a2',2)])
        network.submit_buy_orders([Buy('a1', 2)])

        log = network.simulate_trade()
        calls = [call(2, a2, -1), call(2, a1, 1)]
        mi_calc.get_updated_price.assert_has_calls(calls, any_order =True)
        self.assertDictEqual({'a1': '1->1.5', 'a2': '2->1.5'}, log)
        self.assertFalse(network.buy_orders)
        self.assertFalse(network.sell_orders)

    def test_simulate_trade_buy_equals_sell(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=1, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=1, symbol='a2')
        f1 = Fund('f1', {'a1' : 10}, 100, 1, 1)
        f2 = Fund('f2', {'a2' : 10}, 100, 1, 1)
        mi_calc = MarketImpactCalculator()
        mi_calc.get_updated_price = MagicMock()

        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2}, assets={'a1': a1, 'a2': a2},
                                                     mi_calc=mi_calc, limit_trade_step= False)
        network.submit_buy_orders([Buy('a1',3)])
        network.submit_sell_orders([Sell('a1',3)])
        log = network.simulate_trade()
        mi_calc.get_updated_price.assert_not_called()
        self.assertFalse(log)
        self.assertFalse(network.buy_orders)
        self.assertFalse(network.sell_orders)
        self.assertTrue(a1.price == 1)
        self.assertTrue(a2.price == 2)

    def test_simulate_trade_buy_more_than_sell(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=1, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=1, symbol='a2')
        f1 = Fund('f1', {'a1' : 10}, 100, 1, 1)
        f2 = Fund('f2', {'a2' : 10}, 100, 1, 1)
        mi_calc = MarketImpactCalculator()
        mi_calc.get_updated_price = MagicMock(return_value=1.5)
        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2}, assets={'a1': a1, 'a2': a2},
                                                     mi_calc=mi_calc, limit_trade_step= False)
        network.submit_buy_orders([Buy('a1',3)])
        network.submit_sell_orders([Sell('a1',2)])
        log = network.simulate_trade()
        self.assertDictEqual({'a1': '1->1.5'}, log)
        mi_calc.get_updated_price.assert_called_once_with(1, a1, 1)
        self.assertFalse(network.buy_orders)
        self.assertFalse(network.sell_orders)
        self.assertTrue(a1.price  == 1.5 )
        self.assertTrue(a2.price == 2)

    def test_simulate_trade_sell_more_than_buy(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=1, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=1, symbol='a2')
        f1 = Fund('f1', {'a1' : 10}, 100, 1, 1)
        f2 = Fund('f2', {'a2' : 10}, 100, 1, 1)
        mi_calc = MarketImpactCalculator()
        mi_calc.get_updated_price = MagicMock(return_value=0.5)

        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2}, assets={'a1': a1, 'a2': a2},
                                                     mi_calc=mi_calc, limit_trade_step= False)
        network.submit_buy_orders([Buy('a1',2)])
        network.submit_sell_orders([Sell('a1',3)])
        log = network.simulate_trade()
        self.assertDictEqual({'a1': '1->0.5'}, log)
        mi_calc.get_updated_price.assert_called_once_with(1, a1, -1)
        self.assertFalse(network.buy_orders)
        self.assertFalse(network.sell_orders)
        self.assertTrue(a1.price == 0.5 )
        self.assertTrue(a2.price == 2)

    def test_simulate_trade_buy_orders_in_sell_command(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=1, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=1, symbol='a2')
        f1 = Fund('f1', {'a1' : 10}, 100, 1, 1)
        f2 = Fund('f2', {'a2' : 10}, 100, 1, 1)
        mi_calc = MarketImpactCalculator()
        mi_calc.get_updated_price = MagicMock()
        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2}, assets={'a1': a1, 'a2': a2},
                                                     mi_calc=mi_calc, limit_trade_step= False)
        exception = False
        try:
            network.submit_sell_orders([Sell('a1',2), Buy('a1',2)])
        except TypeError:
            exception = True

        mi_calc.get_updated_price.assert_not_called()
        self.assertTrue(exception)

    def test_simulate_trade_sell_orders_in_buy_command(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=1, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=1, symbol='a2')
        f1 = Fund('f1', {'a1' : 10}, 100, 1, 1)
        f2 = Fund('f2', {'a2' : 10}, 100, 1, 1)
        mi_calc = MarketImpactCalculator()
        mi_calc.get_updated_price = MagicMock()
        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2}, assets={'a1': a1, 'a2': a2},
                                                     mi_calc=mi_calc, limit_trade_step= False)
        exception = False
        try:
            network.submit_buy_orders([Buy('a1',2), Sell('a1',2)])
        except TypeError:
            exception = True

        mi_calc.get_updated_price.assert_not_called()
        self.assertTrue(exception)

    def test_simulate_trade_limit_trade_step(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=1000, symbol='a1')
        f1 = Fund('f1', {'a1' : 10}, 100, 1, 1)
        mi_calc = MarketImpactCalculator()
        mi_calc.get_updated_price = MagicMock(return_value = 1.5)
        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1}, assets={'a1': a1},
                                                     mi_calc=mi_calc)
        SysConfig.set('TIME_STEP_MINUTES',1)
        SysConfig.set('DAILY_PORTION_PER_MIN', 0.001)
        network.submit_buy_orders([Buy('a1',2)])
        log = network.simulate_trade()
        self.assertDictEqual({'a1': '1->1.5'}, log)
        mi_calc.get_updated_price.assert_called_once_with(1, a1, 1)
        self.assertEqual(network.buy_orders['a1'],1)

    def test_read_two_assets_from_file(self):
        assets = AssetFundNetwork.read_assets_file('../../resources/assets.csv', 2)
        expected_assets = {'A1':Asset( price=145.6, daily_volume=605.3, symbol='A1'),
                           'A2': Asset(price=100, daily_volume=10, symbol='A2')}
        self.assertEqual(len(assets), 2)
        self.assertEqual(assets,expected_assets)

    def test_read_all_assets_from_file(self):
        assets = AssetFundNetwork.read_assets_file('../../resources/assets.csv', 4)
        expected_assets = {'A1':Asset( price=145.6, daily_volume=605.3, symbol='A1'),
                           'A2': Asset(price=100, daily_volume=10, symbol='A2'),
                           'A3': Asset(price=100, daily_volume=10, symbol='A3')}
        self.assertEqual(len(assets), 3)
        self.assertEqual(assets,expected_assets)

    def test_reset_books(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=1, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=1, symbol='a2')
        f1 = Fund('f1', {'a1': 10}, 100, 1, 1)
        f2 = Fund('f2', {'a2': 10}, 100, 1, 1)
        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2}, assets={'a1': a1, 'a2': a2},
                                                     mi_calc=MockMarketImpactTestCalculator(), limit_trade_step=True)
        network.submit_buy_orders([Buy('a1', 2)])
        network.submit_sell_orders([Sell('a1', 2)])
        self.assertTrue(network.sell_orders)
        self.assertTrue(network.buy_orders)
        network.reset_order_books()
        self.assertFalse(network.sell_orders)
        self.assertFalse(network.buy_orders)



if __name__ == '__main__':
    unittest.main()
