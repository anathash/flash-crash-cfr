import copy

from sortedcontainers import SortedDict, SortedList, SortedKeyList
import AssetFundNetwork
from constants import MAX_ORDERS_PER_ASSETS, SELL, BUY
import itertools
from Orders import Sell, Buy
from SysConfig import SysConfig


class Attack:
    def __init__(self, order_set, cost):
        self.cost = cost
        self.order_set = order_set
        self.asset_list = [x.asset_symbol for x in order_set]

    def __eq__(self, other):
        return isinstance(other, Attack) and self.cost == other.cost and self.order_set == other.order_set and \
               self.asset_list == other.asset_list


class ActionsManager:
    def __init__(self, network: AssetFundNetwork):
        self.__min_order_percentage = SysConfig.get('STEP_ORDER_SIZE')
        self.__id_to_sym = {}
        i = 1
        for sym in network.assets.keys():
            self.__id_to_sym[i] = sym
            i += 1
        self.__portfolios_dict = self.__get_portfolio_dict(network.assets)
        self.__sorted_keys = SortedKeyList(self.__portfolios_dict.keys())
        self.__sell_all_assets = [Sell(a.symbol, self.__min_order_percentage * a.daily_volume)
                                  for a in network.assets.values()]

    @staticmethod
    def __filter_from_history(action, history, key):
        assets_in_limit = [k  for k, v in history[key].items() if v == MAX_ORDERS_PER_ASSETS]
        for asset in action.asset_list:
            if asset in assets_in_limit:
                return True
        return False

    @staticmethod
    def __get_single_orders(assets, gen_order_func):
        orders = []
        for asset in assets.values():
            order = gen_order_func(asset, SysConfig.get('STEP_ORDER_SIZE'))
            orders.append(order)
        return orders

    @staticmethod
    def __gen_sell_order(asset, size):
        return Sell(asset.symbol, size * asset.daily_volume)

    @staticmethod
    def __gen_buy_order(asset, size):
        return Buy(asset.symbol, size * asset.daily_volume)

    @staticmethod
    def __get_defenses_in_budget(assets, single_asset_orders, asset_price_lambda, budget):
        actions = []
        orders_in_budget = [o for o in single_asset_orders if
                            asset_price_lambda(assets[o.asset_symbol]) * o.num_shares <= budget]
        for i in range(0, len(orders_in_budget)):
            action_subset = itertools.combinations(single_asset_orders, i + 1)
            # attackers buys before game start
            for orders in action_subset:
                orders_list = list(orders)
                attack_cost = sum(
                    [asset_price_lambda(assets[order.asset_symbol]) * order.num_shares for order in orders_list])

                if attack_cost <= budget:
                    actions.append((orders_list, attack_cost))
        return actions

    def __funds_under_risk(self, network: AssetFundNetwork):
        network.reset_order_books()
        network.submit_sell_orders(self.__sell_all_assets)
        network.simulate_trade()
        return network.get_funds_in_margin_calls()

    def __get_all_attacks(self, assets, n):
        if n == 0:
            return [Attack(order_set=[], cost=0)]
        asset_sym = self.__id_to_sym[n]
        asset = assets[asset_sym]
        orders = []
        prev_orders = self.__get_all_attacks(assets, n - 1)
        orders.extend(prev_orders)
        num_shares = int(self.__min_order_percentage * assets[asset_sym].daily_volume)
        order = Sell(asset_sym, num_shares)
        cost = asset.zero_time_price * num_shares
        for action in prev_orders:
            new_order = copy.copy(action.order_set)
            new_order.append(order)
            new_cost = cost + action.cost
            orders.append(Attack(order_set=new_order, cost=new_cost))
        return orders

    def __get_portfolio_dict(self, assets):
        portfolios = self.__get_all_attacks(assets, len(assets))
        portfolios_dict = SortedDict({a.cost: a for a in portfolios})
        return portfolios_dict

    def get_possible_attacks(self, budget, history):
        attacks_costs_in_budget = self.__sorted_keys.irange_key(min_key=0, max_key=budget)
        attacks_in_budget = [self.__portfolios_dict[cost] for cost in attacks_costs_in_budget]
        attacks = [(attack.order_set, attack.cost) for attack in attacks_in_budget if
                   not self.__filter_from_history(attack, history, SELL)]
        return attacks

    def get_possible_defenses(self, af_network, budget, history_assets_dict):
        funds_under_risk = self.__funds_under_risk(af_network)
        asset_syms = set()
        for f in funds_under_risk:
            asset_syms.update(af_network.funds[f].portfolio.keys())
        assets = {sym: af_network.assets[sym] for sym in asset_syms}
        single_asset_defenses = self.__get_single_orders(assets, self.__gen_buy_order)
        filtered_defenses = [d for d in single_asset_defenses if d.asset_symbol not in history_assets_dict[BUY]
                             or history_assets_dict[BUY][d.asset_symbol] < MAX_ORDERS_PER_ASSETS]
        actions = self.__get_defenses_in_budget(assets, filtered_defenses, lambda a: a.price, budget)
        actions.append(([], 0))
        return actions
