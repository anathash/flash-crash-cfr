import AssetFundNetwork
from MarketImpactCalculator import MarketImpactCalculator
from Orders import NoLimitOrder


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
        return assets[self.my_asset.symbol].price <= self.margin_ratio*self.asset_initial_price
