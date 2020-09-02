import unittest


import AssetFundNetwork
from AssetFundNetworkTest import MockMarketImpactTestCalculator
from MarketImpactCalculator import MarketImpactCalculator
from Orders import NoLimitOrder, Sell
from common import Solution
from solvers.single_agent_solver import SingleAgentESSolver


class MockMarketImpactTestCalculator(MarketImpactCalculator):
    def __init__(self, prices= {}):
        self.prices = prices

    def get_market_impact(self, order: NoLimitOrder, asset_daily_volume):
        pass

    def get_updated_price(self, num_shares, asset, sign):
        return self.prices[asset.symbol][num_shares]


class MockFund(AssetFundNetwork.Fund):
    def __init__(self, symbol, my_asset, margin_call_func):
        self.my_asset = my_asset
        self.asset_initial_price = my_asset.price
        self.margin_call_func = margin_call_func
        super().__init__(symbol, {my_asset.symbol: 100}, 100, 1, 1)

    def marginal_call(self, assets):
        return self.margin_call_func(assets)


class TestSingleAgentSolver  (unittest.TestCase):

    # def test_get_all_attack_portfolios(self):
    #     a1 = AssetFundNetwork.Asset(price=10, daily_volume=10, symbol='a1')
    #     a2 = AssetFundNetwork.Asset(price=20, daily_volume=10, symbol='a2')
    #     f1 = MockFund('f1', a1, 1)
    #     f2 = MockFund('f2', a2, 1)
    #     network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2}, assets={'a1': a1, 'a2': a2},
    #                                                  mi_calc=MockMarketImpactTestCalculator())
    #
    #     expected_portfolio = [([],0),
    #                            ([Sell("a1",5)],50),([Sell("a1",10)],100),
    #                            ([Sell("a2", 5)], 100), ([Sell("a2", 10)], 200),
    #                            ([Sell("a1", 5),Sell("a2", 5) ], 150),
    #                            ([Sell("a1", 5),Sell("a2", 10) ], 250),
    #                            ([Sell("a1", 10),Sell("a2", 5) ], 200),
    #                            ([Sell("a1", 10),Sell("a2", 10) ], 300)
    #                            ]
    #     solver = SingleAgentESSolver(network, 0.5,2)
    #     actual_portfolio = solver.get_all_attack_portfolios(network.assets, 2)
    #     expected_portfolio_str = sorted([(str(x),str(y)) for (x,y) in expected_portfolio])
    #     actual_portfolio_str = sorted([(str(x),str(y)) for (x,y) in actual_portfolio])
    #
    #     self.assertEqual(expected_portfolio_str, actual_portfolio_str)

    def test_get_attacks_in_budget(self):
        a1 = AssetFundNetwork.Asset(price=10, daily_volume=10, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=20, daily_volume=10, symbol='a2')
        f1 = MockFund('f1', a1, 1)
        f2 = MockFund('f2', a2, 1)
        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2}, assets={'a1': a1, 'a2': a2},
                                                     mi_calc=MockMarketImpactTestCalculator())

        expected_portfolio = [([], 0),
                              ([Sell("a1", 5)], 50), ([Sell("a1", 10)], 100),
                              ([Sell("a2", 5)], 100), ([Sell("a2", 10)], 200),
                              ([Sell("a1", 5), Sell("a2", 5)], 150),
                              ([Sell("a1", 10), Sell("a2", 5)], 200),

                              ]
        solver = SingleAgentESSolver(network, 0.5, 2)
        actual_portfolio = solver.get_attacks_in_budget(200, True)
        expected_portfolio_str = sorted([(str(x), str(y)) for (x, y) in expected_portfolio])
        actual_portfolio_str = sorted([(str(x), str(y)) for (x, y) in actual_portfolio])
        self.assertEqual(expected_portfolio_str, actual_portfolio_str)

    def test_gen_optimal_attacks(self):
        a1 = AssetFundNetwork.Asset(price=10, daily_volume=10, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=20, daily_volume=10, symbol='a2')
        f1_margin_call = lambda assets:assets['a1'].price <= 8
        f2_margin_call = lambda assets:assets['a2'].price <= 19
        f3_margin_call = lambda assets:assets['a2'].price <= 19
        mi_calc = MockMarketImpactTestCalculator({'a1':{5:9,10:8},'a2':{5:19,10:18}})
        f1 = MockFund('f1', a1, f1_margin_call)
        f2 = MockFund('f2', a2, f2_margin_call)
        f3 = MockFund('f3', a2, f3_margin_call)
        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2, 'f3':f3},
                                                     assets={'a1': a1, 'a2': a2},
                                                     mi_calc=mi_calc,
                                                     limit_trade_step=False)
        solver = SingleAgentESSolver(network, 0.5, 2)
        actual_solutions = solver.gen_optimal_attacks()
        solution_2 = Solution(network, [Sell('a2',5)],2,['f2','f3'],100)
        solution_3 = Solution(network, [Sell('a1',10),Sell('a2',5)],3,['f1','f2','f3'],200)
        expected_solutions = {1:solution_2,2:solution_2,3:solution_3}
        self.assertEqual(expected_solutions, actual_solutions)



if __name__ == '__main__':
    unittest.main()
