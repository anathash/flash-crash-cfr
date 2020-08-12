import itertools
from math import floor

from Orders import  Sell, Buy
from SysConfig import SysConfig


def gen_sell_order(asset, size):
    return Sell(asset.symbol, int(floor(size * asset.daily_volume)))


def gen_buy_order(asset, size):
    return Buy(asset.symbol, int(floor(size * asset.daily_volume)))


def get_single_orders(assets, gen_order_func):
    orders = []
    for asset in assets.values():
        order = gen_order_func(asset, SysConfig.get('STEP_ORDER_SIZE'))
        orders.append(order)
    return orders


def get_actions_in_budget(assets, single_asset_orders, asset_price_lambda, budget):
    actions = []
    costs = {o.asset_symbol:asset_price_lambda(assets[o.asset_symbol])*o.num_shares for o in single_asset_orders}
    orders_in_budget = [o for o in single_asset_orders if
                        asset_price_lambda(assets[o.asset_symbol])*o.num_shares <= budget]
    for i in range(0, len(orders_in_budget)):
        action_subset = itertools.combinations(single_asset_orders, i+1)
        # attackers buys before game start
        for orders in action_subset:
            orders_list = list(orders)
            attack_cost = sum(
                [asset_price_lambda(assets[order.asset_symbol])*order.num_shares for order in orders_list])

            if attack_cost <= budget:
                actions.append((orders_list, attack_cost))
    return actions


def get_possible_attacks(af_network, budget, root_attacker =False):
    single_asset_attacks = get_single_orders(af_network.assets, gen_sell_order)
    actions = get_actions_in_budget(af_network.assets, single_asset_attacks, lambda a:a.zero_time_price, budget)
    if not root_attacker:
        actions.append(([], 0))
    return actions


def get_possible_defenses(af_network, budget):
    #funds_under_threat = af_network.get_funds_under_threat()
    funds_under_threat = af_network.funds
    asset_syms = set()
    for f in funds_under_threat.values():
        asset_syms.update(f.portfolio.keys())
    assets = {sym: af_network.assets[sym] for sym in asset_syms}
    single_asset_defenses = get_single_orders(assets, gen_buy_order)
    actions = get_actions_in_budget(assets, single_asset_defenses, lambda a: a.price, budget)
    actions.append(([], 0))
    return actions

