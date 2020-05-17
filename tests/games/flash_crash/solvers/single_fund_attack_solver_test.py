import unittest

import AssetFundNetwork
from AssetFundNetworkTest import MockMarketImpactTestCalculator
from MarketImpactCalculator import MarketImpactCalculator
from Orders import NoLimitOrder, Sell
from solvers.single_fund_attack_solver import single_fund_attack_optimal_attack_generator


class MockMarketImpactTestCalculator(MarketImpactCalculator):
    def __init__(self, impacts = [0.75,0.5,0.25]):
        self.impacts = impacts
        self.i = 0

    def get_market_impact(self, order: NoLimitOrder, asset_daily_volume):
        return order.num_shares /asset_daily_volume

    def get_updated_price(self, num_shares, asset, sign):
        updates = asset.zero_time_price * self.impacts[self.i]
        self.i += 1
        return updates




## initial_leverage = 1, tolerance =1 . Therefore form a margin call we need curr_portfolio_value < 2*initial_capital

class TestSingleFundAttackSolver  (unittest.TestCase):

    def test_solution1(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=1000, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=1000, symbol='a2')
        f1 = AssetFundNetwork.Fund('f1', {'a1': 10, 'a2': 10}, 13, 1, 1)
        f2 = AssetFundNetwork.Fund('f2', {'a1': 5, 'a2': 4}, 5, 2, 0.25)
        network = AssetFundNetwork.AssetFundsNetwork(funds = {'f1':f1, 'f2':f2},
                                                     assets={'a1':a1, 'a2':a2},
                                                     mi_calc=MockMarketImpactTestCalculator(),
                                                     intraday_asset_gain_max_range=None,
                                                     limit_trade_step=False
                                                     )

        actions,cost = single_fund_attack_optimal_attack_generator(network, 'f1',
                                                                   MockMarketImpactTestCalculator(),0.25,3)
        self.assertEqual(cost, 500)
        self.assertEqual(actions, [Sell('a1', 250),Sell('a1', 250)])

    def test_solution2(self):
        a1 = AssetFundNetwork.Asset(price=2, daily_volume=500, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=1000, symbol='a2')
        f1 = AssetFundNetwork.Fund('f1', {'a1': 10, 'a2': 10}, 16, 1, 1)
        f2 = AssetFundNetwork.Fund('f2', {'a1': 5, 'a2': 4}, 5, 2, 0.25)
        network = AssetFundNetwork.AssetFundsNetwork(funds = {'f1':f1, 'f2':f2},
                                                     assets={'a1':a1, 'a2':a2},
                                                     mi_calc=MockMarketImpactTestCalculator(),
                                                     intraday_asset_gain_max_range=None,
                                                     limit_trade_step=False
                                                     )

        actions,cost = single_fund_attack_optimal_attack_generator(network, 'f1',
                                                                   MockMarketImpactTestCalculator(),0.25,3)
        self.assertEqual(cost, 500)
        self.assertEqual(actions, [Sell('a1', 125),Sell('a1', 125)])

    def test_solution3(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=1000, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=1, daily_volume=1000, symbol='a2')
        f1 = AssetFundNetwork.Fund('f1', {'a1': 5, 'a2': 10}, 6, 1, 1)
        f2 = AssetFundNetwork.Fund('f2', {'a1': 5, 'a2': 4}, 5, 2, 0.25)
        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2},
                                                     assets={'a1': a1, 'a2': a2},
                                                     mi_calc=MockMarketImpactTestCalculator(),
                                                     intraday_asset_gain_max_range=None,
                                                     limit_trade_step=False
                                                     )

        actions, cost = single_fund_attack_optimal_attack_generator(network, 'f1',
                                                                    MockMarketImpactTestCalculator(),
                                                                    0.25,
                                                                    3)
        self.assertEqual(cost, 500)
        self.assertEqual(actions, [Sell('a2', 250), Sell('a2', 250)])

    def test_solution4(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=1000, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=1000, symbol='a2')
        f1 = AssetFundNetwork.Fund('f1', {'a1': 10, 'a2': 10}, 13, 1, 1)
        f2 = AssetFundNetwork.Fund('f2', {'a1': 5, 'a2': 4}, 5, 2, 0.25)
        network = AssetFundNetwork.AssetFundsNetwork(funds = {'f1':f1, 'f2':f2},
                                                     assets={'a1':a1, 'a2':a2},
                                                     mi_calc=MockMarketImpactTestCalculator(),
                                                     intraday_asset_gain_max_range=None,
                                                     limit_trade_step=False
                                                     )

        actions,cost = single_fund_attack_optimal_attack_generator(network, 'f1',
                                                                   MockMarketImpactTestCalculator(),0.25,
                                                                   1)
        self.assertEqual(cost, 750)
        self.assertEqual(actions, [Sell('a1', 250),Sell('a2', 250)])

if __name__ == '__main__':
    unittest.main()
