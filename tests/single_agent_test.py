import unittest


import AssetFundNetwork
from MarketImpactCalculator import MarketImpactCalculator
from Orders import NoLimitOrder, Sell
from single_agent import SingleAgentDynamicProgrammingSolver


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
        network = AssetFundNetwork.AssetFundsNetwork(funds = {'f1':f1,'f2':f2}, assets={'a1':a1,'a2':a2}, mi_calc=MockMarketImpactTestCalculator())

        solver = SingleAgentDynamicProgrammingSolver(network, 4, 0.5)
        self.assertEqual(solver.weights[1], 5)
        self.assertEqual(solver.weights[2], 4)


    def test_1(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=1, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=1, symbol='a2')
        f1 = MockFund('f1', a1,1)
        f2 = MockFund('f2', a2,1)
        network = AssetFundNetwork.AssetFundsNetwork(funds = {'f1':f1,'f2':f2}, assets={'a1':a1,'a2':a2}, mi_calc=MockMarketImpactTestCalculator())

        solver = SingleAgentDynamicProgrammingSolver(network, 4, 1)
        self.assertEqual(solver.results.value, 2)
        self.assertEqual(solver.results.actions[0], Sell('a1', 1))
        self.assertEqual(solver.results.actions[1], Sell('a2', 1))

    def test_2(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=1, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=1, symbol='a2')
        f1 = MockFund('f1', a1,1)
        f2 = MockFund('f2', a2,1)
        network = AssetFundNetwork.AssetFundsNetwork(funds = {'f1':f1,'f2':f2}, assets={'a1':a1,'a2':a2}, mi_calc=MockMarketImpactTestCalculator())

        solver = SingleAgentDynamicProgrammingSolver(network, 3, 1)
        self.assertEqual(solver.results.value, 2)
        self.assertEqual(solver.results.actions[0], Sell('a1', 1))
        self.assertEqual(solver.results.actions[1], Sell('a2', 1))


    def test_3(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=1, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=1, symbol='a2')
        f1 = MockFund(symbol='f1', my_asset=a1, margin_ratio=0.1)
        f2 = MockFund(symbol='f2', my_asset=a2, margin_ratio=0.9)
        network = AssetFundNetwork.AssetFundsNetwork(funds = {'f1':f1,'f2':f2}, assets={'a1':a1,'a2':a2}, mi_calc=MockMarketImpactTestCalculator())

        solver = SingleAgentDynamicProgrammingSolver(network, 4, 1)
        self.assertEqual(solver.results.value, 1)
        self.assertEqual(solver.results.actions[0], Sell('a2', 2))

    def test_4(self):
        a1 = AssetFundNetwork.Asset(price=1, daily_volume=1, symbol='a1')
        a2 = AssetFundNetwork.Asset(price=2, daily_volume=1, symbol='a2')
        f1 = MockFund(symbol='f1', my_asset=a1, margin_ratio=1)
        f2 = MockFund(symbol='f1', my_asset=a1, margin_ratio=1)
        network = AssetFundNetwork.AssetFundsNetwork(funds = {'f1':f1,'f2':f2}, assets={'a1':a1,'a2':a2}, mi_calc=MockMarketImpactTestCalculator())

        solver = SingleAgentDynamicProgrammingSolver(network, 4, 1)
        self.assertEqual(solver.results.value, 2)
        self.assertEqual(solver.results.actions[0], Sell('a1', 1))



    def not_test_solver_finds_best_attack_integration(self):
        a1 = AssetFundNetwork.Asset(50, 2, 'a1')
        a2 = AssetFundNetwork.Asset(20, 2, 'a2')
        a3 = AssetFundNetwork.Asset(30, 2, 'a3')
        f1 = AssetFundNetwork.Fund('f1', {'a1':10}, {'a2':10},1000,1,1)
        f2 = AssetFundNetwork.Fund('f2', {'a2':10}, {'a3':10},1000,1,1)


        network = AssetFundNetwork.AssetFundsNetwork(funds = [f1,f2], assets=[a1,a2,a3])

        solver = SingleAgentDynamicProgrammingSolver(network, 10, 0.5)
        print(solver.results.value)
        print(solver.results.actions)

if __name__ == '__main__':
    unittest.main()
