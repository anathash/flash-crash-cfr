import unittest
import numpy.testing as npt

from AssetFundNetwork import Asset
from MarketImpactCalculator import ExponentialMarketImpactCalculator, SqrtMarketImpactCalculator
from Orders import Buy, Sell


class TestMarketImpactCalculator  (unittest.TestCase):

    def test_market_impact_buy_order_exp(self):
        calc = ExponentialMarketImpactCalculator(2)
        order = Buy('a1', 10)
        a = Asset(price=2, daily_volume=100, volatility=1.5, symbol='a1')
        mi = calc.get_market_impact(order, a)
        npt.assert_almost_equal(1.2214, mi, decimal=4)

    def test_market_impact_sell_order_exp(self):
        calc = ExponentialMarketImpactCalculator(2)
        a = Asset(price=2, daily_volume=100, volatility=1.5, symbol='a1')
        order = Sell('a1', 10)
        mi = calc.get_market_impact(order, a)
        npt.assert_almost_equal(0.8187, mi, decimal=4)

    def test_updated_price_buy_exp(self):
        calc = ExponentialMarketImpactCalculator(2)
        a = Asset(price=2, daily_volume=100, volatility=1.5, symbol='a1')
        updated_price = calc.get_updated_price(10, a, 1)
        npt.assert_almost_equal(2.4428, updated_price, decimal=4)

    def test_updated_price_sell_exp(self):
        calc = ExponentialMarketImpactCalculator(2)
        a = Asset(price=2, daily_volume=100, volatility=1.5, symbol='a1')
        mi = calc.get_updated_price(10, a, -1)
        npt.assert_almost_equal(1.6374, mi, decimal=4)

    def test_market_impact_buy_sqrt(self):
        calc = SqrtMarketImpactCalculator(0.5)
        order = Buy('a1', 10)
        a = Asset(price=2, daily_volume=1000, volatility=1.5, symbol='a1')
        mi = calc.get_market_impact(order, a, )
        npt.assert_almost_equal(0.075, mi, decimal=4)

    def test_market_impact_sell_sqrt(self):
        calc = SqrtMarketImpactCalculator(0.5)
        a = Asset(price=2, daily_volume=1000, volatility=1.5, symbol='a1')
        order = Sell('a1', 10)
        mi = calc.get_market_impact(order, a)
        npt.assert_almost_equal(-0.075, mi, decimal=4)


    def test_updated_price_buy_sqrt(self):
        calc = SqrtMarketImpactCalculator(0.5)
        order = Buy('a1', 10)
        a = Asset(price=2, daily_volume=1000, volatility=1.5, symbol='a1')
        mi = calc.get_updated_price(order.num_shares, a, 1)
        npt.assert_almost_equal(2.075, mi, decimal=4)

    def test_updated_price_sell_sqrt(self):
        calc = SqrtMarketImpactCalculator(0.5)
        a = Asset(price=2, daily_volume=1000, volatility=1.5, symbol='a1')
        order = Sell('a1', 10)
        mi = calc.get_updated_price(order.num_shares, a, -1)
        npt.assert_almost_equal(1.925, mi, decimal=4)


if __name__ == '__main__':
    unittest.main()
