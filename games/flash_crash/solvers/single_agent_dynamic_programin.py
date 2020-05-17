import copy
import csv
import math
from math import floor

import AssetFundNetwork
from MarketImpactCalculator import ExponentialMarketImpactCalculator
from Orders import Sell

import networkx as nx

from solvers.common import Solution


class SingleAgentDynamicProgrammingSolver:
    def __init__(self, network: AssetFundNetwork, capacity, min_order_percentage, max_order_num):
        self.max_order_num = max_order_num #(int)(floor(max_order_percentage/min_order_percentage))
        self.min_order_percentage = min_order_percentage
        num_assets = len(network.assets)
        self.id_to_sym = {}
        i = 1
        for sym in network.assets.keys():
            self.id_to_sym[i] = sym
            i += 1
        #self.solutions = [[None for x in range(capacity + 1)] for x in range(num_assets + 1)]
        #self.solutions = [[None] *(capacity+1)]*(num_assets + 1)
        self.solutions = [{}]*(num_assets + 1)
        self.weights = self.gen_weights_array(min_order_percentage, network)
        self.results = self.build_attack(num_assets, capacity, network)

    # the cost of each assets min order size
    def gen_weights_array(self, min_order_percentage, network):
        weights = {}
        for i, sym in self.id_to_sym.items():
            asset = network.assets[sym]
            weights[i] = int(math.ceil(min_order_percentage * asset.daily_volume * asset.price))
        return weights


    def build_attack(self, n, c, network):
        if n == 0 or c == 0:
            s = Solution(network,  [], 0, [], 0)
            self.solutions[n][c] = s
            return s
        asset_sym = self.id_to_sym[n]
        if c in self.solutions[n]:
            return self.solutions[n][c]
        elif self.weights[n] > c:
            s = self.build_attack(n-1, c, copy.deepcopy(network))
            self.solutions[n][c] = s
            return s
        else:
            max_assets_orders = min(self.max_order_num, (int)(floor(c / self.weights[n])))
            max_result = self.build_attack(n - 1, c,  copy.deepcopy(network))
            for i in range(1, max_assets_orders+1):
                prev_solution = self.build_attack(n - 1, c - i * self.weights[n], copy.deepcopy(network))
                num_shares = floor(i * self.min_order_percentage * network.assets[asset_sym].daily_volume)
                if not num_shares:
                    continue
                order = Sell(asset_sym, num_shares)
                net2 = prev_solution.network
                net2.submit_sell_orders([order])
                net2.clear_order_book()
                funds = net2.get_funds_in_margin_calls()
                value = len(funds)
                cost = prev_solution.cost + order.num_shares * network.assets[order.asset_symbol].zero_time_price
                if value > max_result.value or (value == max_result.value  and cost < max_result.cost):
                    actions = copy.copy(prev_solution.actions)
                    actions.append(order)
                    max_result = Solution(net2,  actions, value, funds, cost)

            self.solutions[n][c] = max_result
            return max_result

    def build_attack_rec_wrong(self, n, c, network):
        if n == 0 or c == 0:
            s = Solution(network, [], 0)
            self.solutions[n][c] = s
            return s
        asset_sym = self.id_to_sym[n]
        if self.solutions[n][c]:
            return self.solutions[n][c]
        elif self.weights[n] > c:
            s = self.build_attack(n-1, c, copy.deepcopy(network))
            self.solutions[n][c] = s
            return s
        else:
            prev_solutions = {}
            max_result = self.build_attack(n - 1, c,  copy.deepcopy(network))
            prev_solutions[1] = self.build_attack(n - 1, c - self.weights[n], copy.deepcopy(network))
            prev_solutions[2] = self.build_attack(n, c - self.weights[n], copy.deepcopy(network))
            order = Sell(asset_sym, self.min_order_percentage * network.assets[asset_sym].daily_volume)
            for i in range(1, 2):
                net2 = prev_solutions[i].network
                net2.submit_sell_orders([order])
                net2.clear_order_book()
                value = net2.count_margin_calls()
                if value > max_result.value:
                    actions = copy.copy(prev_solutions[i].actions)
                    actions.append(order)
                    max_result = Solution(net2, actions, value)

            self.solutions[n][c] = max_result
            return max_result

    def store_solution(self, filename):
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['budget', 'value', 'actions']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            max_solutions = self.solutions[len(self.solutions)-1]
            for budget, solution in max_solutions.items():
                writer.writerow({'budget': budget, 'value': str(solution.value),'actions': str(solution.actions)})


def main():
    assets_num_shares = [5, 5]
    volatility = [1.5, 1, 1.1]
    initial_prices = [1, 2]
    initial_capitals = [100, 200]
    initial_leverages = [1, 2]
    tolerances = [4, 5]
    investment_proportions = {'f0': [0.6, 0.4], 'f1': [1.0]}
    g = nx.DiGraph()
    g.add_nodes_from([0, 1, 2, 3])
    g.add_edges_from([(0, 2), (0, 3), (1, 3)])
    network = AssetFundNetwork.AssetFundsNetwork.gen_network_from_graph(g, investment_proportions, initial_capitals,
                                                                        initial_leverages, initial_prices,
                                                                        tolerances, assets_num_shares, volatility,
                                                                        ExponentialMarketImpactCalculator(1))

    solver = SingleAgentDynamicProgrammingSolver(network, 10000000, 0.5)
    print(solver.results.value)
    print(solver.results.actions)




