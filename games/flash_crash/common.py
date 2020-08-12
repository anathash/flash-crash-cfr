import copy
import csv
from math import floor

from AssetFundNetwork import AssetFundsNetwork


class Solution:
    def __init__(self, network, actions, value, funds, cost):
        self.network = network
        self.actions = actions
        self.value = value
        self.funds = funds
        self.cost = cost

    def __eq__(self, other):
        return isinstance(other, Solution) and self.actions == other.actions and \
               self.value == other.value and self.funds == other.funds and self.cost == other.cost and self.network == other.network



def copy_network(from_net):
    new_assets = copy.deepcopy(from_net.assets)
    new_net = AssetFundsNetwork(funds=from_net.funds,
                                assets=new_assets,
                                mi_calc=from_net.mi_calc,
                                limit_trade_step=from_net.limit_trade_step)
    new_net.sell_orders = copy.deepcopy(from_net.sell_orders)
    new_net.buy_orders = copy.deepcopy(from_net.buy_orders)
    return new_net

def store_solutions( filename, solutions):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['value', 'cost','funds', 'actions']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for val in sorted(solutions.keys()):
            solution = solutions[val]
            row = {'value': str(val), 'cost': str(int(floor(solution.cost))),'funds': str(solution.funds),'actions': str(solution.actions)}
            writer.writerow(row)


def store_solutions_by_key( filename, solutions, key_name = None):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = [] if not key_name else [key_name]
        fieldnames.extend(['value', 'cost','funds', 'actions'])
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for val in sorted(solutions.keys()):
            solution = solutions[val]
            row = {} if not key_name else {key_name:val}
            row.update({'value': str(solution.value), 'cost': str(int(floor(solution.cost))),'funds': str(solution.funds),'actions': str(solution.actions)})
            writer.writerow(row)


def store_minimax_results( filename, solutions, key_name = None):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = [] if not key_name else [key_name]
        fieldnames.extend(['attacker_budget','defender_budget','attacker_cost','defender_cost','value', 'funds', 'actions'])
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for val in sorted(solutions.keys()):
            solution = solutions[val]
            row = {} if not key_name else {key_name:val}
            row.update({'value': str(solution.value), 'cost': str(int(floor(solution.cost))),'funds': str(solution.funds),'actions': str(solution.actions)})
            writer.writerow(row)

