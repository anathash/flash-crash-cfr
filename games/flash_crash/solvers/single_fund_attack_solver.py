from math import floor

import MarketImpactCalculator
from AssetFundNetwork import AssetFundsNetwork
from Orders import Sell


def single_fund_attack_optimal_attack_generator(network:AssetFundsNetwork, fund_sym, mic:MarketImpactCalculator,
                                                order_size, max_num_orders):

    fund = network.funds[fund_sym]
    assets = network.assets
    fund_impacts = {}
    for a in assets.values():
        shares_for_1M = floor(10000000/a.zero_time_price)
        asset_price_impact =  mic.get_market_impact(Sell(a.symbol, shares_for_1M), a.daily_volume)
        fund_impacts[a.symbol] = 0 if a.symbol not in fund.portfolio else fund.portfolio[a.symbol] * asset_price_impact
    sorted_impact = sorted(fund_impacts.items(), key=lambda x: x[1], reverse=True)
    cost = 0
    actions = []
    for sym, impact in sorted_impact:
        num_orders = 1
        num_shares = floor(assets[sym].daily_volume * order_size)
        while num_orders <= max_num_orders:
            order = Sell(sym, num_shares)
            actions.append(order)
            cost += assets[sym].zero_time_price * num_shares
            network.submit_sell_orders([order])
            network.clear_order_book()
            if fund.marginal_call(assets):
                return actions, cost
            num_orders += 1
    return actions, cost
