import copy
from math import floor

import AssetFundNetwork
from Orders import Sell
from ActionsManager import ActionsManager
from common import Solution


class SingleAgentESSolver:
    def __init__(self, network: AssetFundNetwork, min_order_percentage, max_order_num):
        self.max_order_num = max_order_num #(int)(floor(max_order_percentage/min_order_percentage))
        self.min_order_percentage = min_order_percentage
        self.id_to_sym = {}
        i = 1
        for sym in network.assets.keys():
            self.id_to_sym[i] = sym
            i += 1
        self.solutions = {}
        self.network = network
        self.action_mgr = ActionsManager(self.network.assets, self.min_order_percentage, self.max_order_num)

    def gen_attacks(self,network):
        self.attack(len(network.assets), network, [])
        return self.solutions

    def attack(self, n, network, orders_list):
        if n == 0:
            net2 = copy.deepcopy(network)
            net2.submit_sell_orders(orders_list)
            net2.clear_order_book()
            funds = net2.get_funds_in_margin_calls()
            cost = sum([o.num_shares*network.assets[o.asset_symbol].zero_time_price for o in orders_list])
            value = len(funds)
            for i in range (1, value+1):
                if i not in self.solutions or cost < self.solutions[i].cost:
                    self.solutions[i] = Solution(network, orders_list, value, funds, cost)
            return
        asset_sym = self.id_to_sym[n]
        orders_list2 = copy.copy(orders_list)
        self.attack(n - 1, network,  orders_list2)
        for i in range(1, self.max_order_num + 1):
            num_shares = int(floor(i * self.min_order_percentage * network.assets[asset_sym].daily_volume))
            order = Sell(asset_sym, num_shares)
            orders_list2 = copy.copy(orders_list)
            orders_list2.append(order)
            self.attack(n-1,  network, orders_list2)
        return

    def gen_optimal_attacks(self):
        solutions = {}
#        portfolios = self.get_all_attack_portfolios(self.network.assets, len(self.network.assets))
        attacks = self.action_mgr.get_possible_attacks()
        for (order_set,cost) in attacks:
            net2 = copy.deepcopy(self.network)
            net2.submit_sell_orders(order_set)
            net2.clear_order_book()
            funds = net2.get_funds_in_margin_calls()
            value = len(funds)
            for i in range(1, value + 1):
                if i not in solutions or cost <= solutions[i].cost:
                    solutions[i] = Solution(self.network, order_set, value, funds, cost)
        return solutions

    def get_attacks_in_budget(self, budget, include_opt_out):
        attacks = self.action_mgr.get_possible_attacks(budget)
        return [x for x in attacks if x[1] <= budget and (include_opt_out or x[1] > 0)]


    def get_all_attack_portfolios2(self, n, assets, budget, order_set):
        if n == 0:
            return
        order_set.append(self.get_all_attack_portfolios(n-1, assets, budget, order_set))
        asset_sym = self.id_to_sym[n]
        for i in range(1, self.max_order_num + 1):
            asset = assets[asset_sym]
            num_shares = int(floor(i * self.min_order_percentage * asset.daily_volume))
            cost = num_shares * asset.zero_time_price
            if cost < budget:
                return
            order = Sell(asset_sym, num_shares)
            prev = self.get_all_attack_portfolios(n-1, assets, budget - cost, order_set)


    # def get_all_attack_portfolios(self, assets, n):
    #     if n == 0:
    #         return [([], 0)]
    #     asset_sym = self.id_to_sym[n]
    #     asset = assets[asset_sym]
    #     orders = []
    #     prev_orders = self.get_all_attack_portfolios(assets, n - 1)
    #     orders.extend(prev_orders)
    #     for i in range(1, self.max_order_num + 1):
    #         num_shares = int(floor(i * self.min_order_percentage * assets[asset_sym].daily_volume))
    #         order = Sell(asset_sym, num_shares)
    #         cost = asset.zero_time_price * num_shares
    #         for o, o_cost in prev_orders:
    #             new_order = copy.copy(o)
    #             new_order.append(order)
    #             new_cost = cost + o_cost
    #             orders.append((new_order, new_cost))
    #     return orders
