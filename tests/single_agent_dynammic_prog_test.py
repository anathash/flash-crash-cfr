import csv
import unittest


import AssetFundNetwork
from AssetFundNetworkTest import MockMarketImpactTestCalculator
from MarketImpactCalculator import MarketImpactCalculator
from Orders import NoLimitOrder, Sell
from SysConfig import SysConfig
from solvers.single_agent_dynamic_programin import SingleAgentDynamicProgrammingSolver
from solvers.single_agent_solver import SingleAgentESSolver


class MockMarketImpactTestCalculator(MarketImpactCalculator):
    def get_market_impact(self, order: NoLimitOrder, asset_daily_volume):
        pass

    def get_updated_price(self, num_shares, asset, sign):
        return asset.price*(1+sign *0.1*num_shares)


class MockFund(AssetFundNetwork.Fund):
    def __init__(self, symbol, my_asset, margin_ratio):
        self.my_asset = my_asset
        self.asset_initial_price = my_asset.price
        self.margin_ratio = margin_ratio
        super().__init__(symbol, {my_asset.symbol: 100}, 100, 1, 1)

    def marginal_call(self, assets):
        return assets[self.my_asset.symbol].price < self.margin_ratio*self.asset_initial_price


class TestSingleAgentSolver  (unittest.TestCase):

    def test_gen_weights(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=10, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=4, symbol='a2')
        f1 = MockFund('f1', a1,1)
        f2 = MockFund('f2', a2,1)
        network = AssetFundNetwork.AssetFundsNetwork(funds = {'f1':f1, 'f2':f2}, assets={'a1':a1, 'a2':a2}, mi_calc=MockMarketImpactTestCalculator())

        solver = SingleAgentDynamicProgrammingSolver(network, 4, 0.5, 1)
        self.assertEqual(solver.weights[1], 5)
        self.assertEqual(solver.weights[2], 4)

    def test_get_all_attack_portfolios(self):
        a1 = AssetFundNetwork.Asset(price=10, daily_volume=10, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=20, daily_volume=10, symbol='a2')
        f1 = MockFund('f1', a1, 1)
        f2 = MockFund('f2', a2, 1)
        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2}, assets={'a1': a1, 'a2': a2},
                                                     mi_calc=MockMarketImpactTestCalculator())

        expected_portfolio = [([],0),
                               ([Sell("a1",5)],50),([Sell("a1",10)],100),
                               ([Sell("a2", 5)], 100), ([Sell("a2", 10)], 200),
                               ([Sell("a1", 5),Sell("a2", 5) ], 150),
                               ([Sell("a1", 5),Sell("a2", 10) ], 250),
                               ([Sell("a1", 10),Sell("a2", 5) ], 200),
                               ([Sell("a1", 10),Sell("a2", 10) ], 300)
                               ]
        solver = SingleAgentESSolver(network, 0.5,2)
        actual_portfolio = solver.get_all_attack_portfolios(network.assets, 2)
        expected_portfolio_str = sorted([(str(x),str(y)) for (x,y) in expected_portfolio])
        actual_portfolio_str = sorted([(str(x),str(y)) for (x,y) in actual_portfolio])

        self.assertEqual(expected_portfolio_str, actual_portfolio_str)

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
        f1 = MockFund('f1', a1, 1)
        f2 = MockFund('f2', a2, 1)
        f2 = MockFund('f3', a2, 1)
        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2}, assets={'a1': a1, 'a2': a2},
                                                     mi_calc=MockMarketImpactTestCalculator())

        expected_portfolio = [([], 0),
                              ([Sell("a1", 5)], 50), ([Sell("a1", 10)], 100),
                              ([Sell("a2", 5)], 100), ([Sell("a2", 10)], 200),
                              ([Sell("a1", 5), Sell("a2", 5)], 150),
                              ([Sell("a1", 10), Sell("a2", 5)], 200),
                              ]

    def test_1(self):
        a1 = AssetFundNetwork.Asset(price=10, daily_volume=1, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=20, daily_volume=1, symbol='a2')
        f1 = MockFund('f1', a1,1)
        f2 = MockFund('f2', a2,1)
        network = AssetFundNetwork.AssetFundsNetwork(funds = {'f1':f1, 'f2':f2}, assets={'a1':a1, 'a2':a2}, mi_calc=MockMarketImpactTestCalculator())

        solver = SingleAgentDynamicProgrammingSolver(network, 40, 1, 1)
        for solutions in solver.solutions:
            self.assertEqual([40,30,20,10], list(solutions.keys()))

        self.assertEqual(solver.results.value, 2)
        self.assertEqual(solver.results.actions[0], Sell('a1', 1))
        self.assertEqual(solver.results.actions[1], Sell('a2', 1))

    def test_2(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=1, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=1, symbol='a2')
        f1 = MockFund('f1', a1,1)
        f2 = MockFund('f2', a2,1)
        network = AssetFundNetwork.AssetFundsNetwork(funds = {'f1':f1, 'f2':f2}, assets={'a1':a1, 'a2':a2}, mi_calc=MockMarketImpactTestCalculator())

        solver = SingleAgentDynamicProgrammingSolver(network, 3, 1, 1)
        self.assertEqual(solver.results.value, 2)
        self.assertEqual(solver.results.actions[0], Sell('a1', 1))
        self.assertEqual(solver.results.actions[1], Sell('a2', 1))


    def test_3(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=10, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=20, symbol='a2')
        f1 = MockFund(symbol='f1', my_asset=a1, margin_ratio=0.1)
        f2 = MockFund(symbol='f2', my_asset=a2, margin_ratio=0.9)
        network = AssetFundNetwork.AssetFundsNetwork(funds = {'f1':f1, 'f2':f2}, assets={'a1':a1, 'a2':a2}, mi_calc=MockMarketImpactTestCalculator())

        solver = SingleAgentDynamicProgrammingSolver(network, 40, 0.5, 2)
        self.assertEqual(solver.results.value, 1)
        self.assertEqual(solver.results.actions[0], Sell('a2', 10))


    def test_4(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=1, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=1, symbol='a2')
        f1 = MockFund(symbol='f1', my_asset=a1, margin_ratio=1)
        f2 = MockFund(symbol='f1', my_asset=a1, margin_ratio=1)
        network = AssetFundNetwork.AssetFundsNetwork(funds = {'f1':f1, 'f2':f2}, assets={'a1':a1, 'a2':a2}, mi_calc=MockMarketImpactTestCalculator())

        solver = SingleAgentDynamicProgrammingSolver(network, 4, 1, 1)
        self.assertEqual(solver.results.value, 2)
        self.assertEqual(solver.results.actions[0], Sell('a1', 1))


    def test_order_limited_by_parameter(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=1, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=2, symbol='a2')
        f1 = MockFund(symbol='f1', my_asset=a1, margin_ratio=0.9)
        f2 = MockFund(symbol='f2', my_asset=a2, margin_ratio=0.9)
        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2}, assets={'a1': a1, 'a2': a2},
                                                     mi_calc=MockMarketImpactTestCalculator())

        solver = SingleAgentDynamicProgrammingSolver(network, 4, 0.5, 2)
        self.assertEqual(solver.results.value, 1)
        self.assertEqual(solver.results.actions[0], Sell('a2', 2))


    def not_test_solver_finds_best_attack_integration(self):
        a1 = AssetFundNetwork.Asset(50, 2, 'a1')
        a2 = AssetFundNetwork.Asset(20, 2, 'a2')
        a3 = AssetFundNetwork.Asset(30, 2, 'a3')
        f1 = AssetFundNetwork.Fund('f1', {'a1':10}, {'a2':10}, 1000, 1, 1)
        f2 = AssetFundNetwork.Fund('f2', {'a2':10}, {'a3':10}, 1000, 1, 1)

        network = AssetFundNetwork.AssetFundsNetwork(funds = [f1, f2], assets=[a1, a2, a3])

        solver = SingleAgentDynamicProgrammingSolver(network, 10, 0.5)
        print(solver.results.value)
        print(solver.results.actions)

    def test_store_file(self):
        a1 = AssetFundNetwork.Asset(price=10, daily_volume=1, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=20, daily_volume=1, symbol='a2')
        f1 = MockFund('f1', a1, 1)
        f2 = MockFund('f2', a2, 1)
        network = AssetFundNetwork.AssetFundsNetwork(funds={'f1': f1, 'f2': f2}, assets={'a1': a1, 'a2': a2},
                                                     mi_calc=MockMarketImpactTestCalculator())

        solver = SingleAgentDynamicProgrammingSolver(network, 40, 1, 1)
        solver.store_solution('../resources/test_store_file.csv')
        expected_rows = []
        for budget in [40,30,20,10]:
            expected_rows.append({'budget':str(budget), 'value':str(solver.solutions[2][budget].value),
                                  'actions':str(solver.solutions[2][budget].actions)})
        i =0
        with open('../resources/test_store_file.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.assertEqual(dict(row), expected_rows[i])
                i+=1



if __name__ == '__main__':
    unittest.main()
