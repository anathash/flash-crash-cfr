import unittest

from AssetFundNetwork import Asset, Fund
from Orders import Sell
from SysConfig import SysConfig


class TestFund  (unittest.TestCase):

    def test_update_state_margin_only(self):
        assets = {'XXX': Asset(1, 20, 1.5, 'XXX'), 'YYY': Asset(1, 20, 1.5, 'yyy')}
        fund = Fund('F1', {'XXX': 10, 'YYY': 10}, 5, 2, 0.25)
        fund.update_state(assets)
        self.assertTrue(fund.is_in_margin_call())
        self.assertFalse(fund.default())

    def test_update_state_default(self):
        assets = {'XXX': Asset(1, 20, 1.5, 'XXX'), 'YYY': Asset(1, 20, 1.5, 'yyy')}
        fund = Fund('F1', {'XXX': 5, 'YYY': 4}, 5, 2, 0.25)
        fund.update_state(assets)
        self.assertTrue(fund.is_in_margin_call())
        self.assertTrue(fund.default())
        self.assertTrue(fund.default())

    def test_get_orders(self):
        assets = {'XXX': Asset(1, 20, 1.5, 'XXX'), 'YYY': Asset(1, 20, 1.5, 'yyy')}
        fund = Fund('F1', {'XXX': 5, 'YYY': 4}, 5, 2, 0.25)
        self.assertEqual(fund.get_orders(assets), [])

    def test_gen_liquidation_orders(self):
        SysConfig.set("MINUTE_VOLUME_LIMIT", 0.1)
        assets = {'XXX': Asset(2, 3900, 1.5, 'XXX'), 'YYY': Asset(1, 7900, 1.5, 'yyy'),
                  'ZZZ': Asset(1, 7900, 1.5, 'yyy')}
        fund = Fund('F1', {'XXX': 10, 'YYY': 11, 'ZZZ': 2}, 5, 2, 0.25)
        expected_orders = [Sell('XXX', 1), Sell('YYY', 2), Sell('ZZZ', 2)]
        expected_portfolio = {'XXX': 9, 'YYY': 9}
        orders = fund.gen_liquidation_orders(assets)
        self.assertEqual(orders, expected_orders)
        self.assertEqual(fund.portfolio, expected_portfolio)


    def test_liquidate(self):
        fund = Fund('F1', {'XXX': 10, 'YYY': 10}, 5, 2, 3)
        self.assertFalse(fund.is_in_margin_call())
        fund.liquidate()
        self.assertTrue(fund.is_in_margin_call())

    def test_is_liquidated(self):
        fund = Fund('F1', {'XXX': 10, 'YYY': 10}, 5, 2, 3)
        self.assertFalse(fund.is_in_margin_call())
        fund.is_liquidating = True
        self.assertTrue(fund.is_in_margin_call())
        fund.is_liquidating = False
        self.assertFalse(fund.is_in_margin_call())

    def test_default(self):
        fund = Fund('F1', {'XXX': 10, 'YYY': 10}, 5, 2, 3)
        self.assertFalse(fund.default())
        fund.is_in_default = True
        self.assertTrue(fund.default())
        fund.is_in_default = False
        self.assertFalse(fund.default())

    def test_compute_portfolio_value(self):
        assets = {'XXX': Asset(1, 20, 1.5, 'XXX'), 'YYY': Asset(4, 20, 1.5, 'yyy')}
        fund = Fund('F1', {'XXX': 10, 'YYY': 10}, 5, 2, 3)
        self.assertEqual(50, fund.compute_portfolio_value(assets))

    def test_compute_compute_curr_leverage(self):
        assets = {'XXX': Asset(1, 20, 1.5, 'XXX'), 'YYY': Asset(4, 20, 1.5, 'yyy')}
        fund = Fund('F1', {'XXX': 10, 'YYY': 10}, 5, 2, 3)
        self.assertEqual(0.25, fund.compute_curr_leverage(assets))

    def test_marginal_call_false(self):
        assets = {'XXX': Asset(1, 20, 1.5, 'XXX'), 'YYY': Asset(4, 20, 1.5, 'yyy')}
        fund = Fund('F1', {'XXX': 10, 'YYY': 10}, 5, 2, 3)
        self.assertFalse(False, fund.marginal_call(assets))

    def test_marginal_call_true(self):
        assets = {'XXX': Asset(1, 20, 1.5, 'XXX'), 'YYY': Asset(1, 20, 1.5, 'yyy')}
        fund = Fund('F1', {'XXX': 10, 'YYY': 10}, 5, 2, 3)
        self.assertTrue(True, fund.marginal_call(assets))

