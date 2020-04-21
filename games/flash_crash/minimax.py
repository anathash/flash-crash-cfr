import copy
from math import inf

from AssetFundNetwork import AssetFundsNetwork
from SysConfig import SysConfig
from actions import get_possible_attacks, get_possible_defenses
from constants import ATTACKER, DEFENDER, MARKET, ROOT_ATTACKER
from solvers.single_agent_solver import SingleAgentESSolver


class Result:
    def __init__(self, funds, node, order_set, future_actions, network, attacker_cost, defender_cost):
        self.value = -1*len(funds)
        self.funds = funds
        best_actions = []
        best_actions.append(order_set)
        best_actions.extend(future_actions)
        self.actions = best_actions
        node.value = self.value
        self.tree = node
        self.network = network
        self.attacker_cost = attacker_cost
        self.defender_cost = defender_cost


class MiniMaxTree:
    def __init__(self, player, value = None):
        self.player = player
        self.children = {}
        self.value = value


    def add_child(self, action, sub_tree):
        self.children[action] = sub_tree


def end_game(network):
    network.clear_order_book()
    return -1*network.count_margin_calls()


def append_actions(order_set,future_actions ):
    best_actions = []
    best_actions.append(order_set)
    best_actions.extend(future_actions)
    return best_actions

def minimax2(turn, network: AssetFundsNetwork, attacker_budget, defender_budget):
    print(turn + ' Defender:' + str(defender_budget) + ' Attacker' + str(attacker_budget))
    best_result = None
    node = MiniMaxTree(turn)
    if turn == ROOT_ATTACKER:
        order_size = SysConfig.get("STEP_ORDER_SIZE")
        max_num_orders = SysConfig.get("MAX_NUM_ORDERS")
        es_solver = SingleAgentESSolver(network, order_size, max_num_orders)
        portfolios = es_solver.get_attacks_in_budget(attacker_budget)
        #value = inf
        for (order_set, cost) in portfolios:
            net2 = copy.deepcopy(network)
            net2.submit_sell_orders(order_set)
            child_result= minimax2(MARKET,net2,attacker_budget - cost, defender_budget)
            node.add_child(str(order_set), child_result.tree)
            if not best_result or child_result.value < best_result.value or (child_result.value == best_result.value and
                                                                             child_result.attacker_cost < best_result.attacker_cost):
                best_result = Result(funds=child_result.funds,node=node, order_set=order_set,
                                     future_actions=child_result.actions, network=child_result.network,
                                     attacker_cost = child_result.attacker_cost+cost,
                                     defender_cost = child_result.defender_cost)
        return best_result
    elif turn == DEFENDER:
        net2 = copy.deepcopy(network)
        net2.simulate_trade()
        if net2.count_margin_calls() ==0:
            actions =[([], 0)]
        else:
            actions = get_possible_defenses(network, defender_budget)
        for (order_set, cost) in actions:
            net2 = copy.deepcopy(network)
            net2.submit_buy_orders(order_set)
            child_result = minimax2(MARKET,net2,attacker_budget, defender_budget - cost)
            node.add_child(str(order_set), child_result.tree)
            if not best_result or child_result.value > best_result.value  or (child_result.value == best_result.value and
                                                                             child_result.defender_cost < best_result.defender_cost):
                best_result = Result(funds=child_result.funds, node=node, order_set=order_set,
                                     future_actions=child_result.actions, network=child_result.network,
                                     attacker_cost=child_result.attacker_cost,
                                     defender_cost=child_result.defender_cost + cost)

        return best_result
    else: #MARKET
        network.simulate_trade()
        funds = network.get_funds_in_margin_calls()
        if len(funds) or network.no_more_sell_orders():
            return Result(funds=funds, node=node, order_set=['MARKET'],
                                     future_actions=[], network=network,
                                     attacker_cost=0,
                                     defender_cost=0)

        child_result  = minimax2(DEFENDER,network,attacker_budget, defender_budget)
        node.add_child('MARKET', child_result.tree)
        return Result(funds=child_result.funds,node=node, order_set=['MARKET'],
                                     future_actions=child_result.actions, network=child_result.network,
                      attacker_cost=child_result.attacker_cost, defender_cost=child_result.defender_cost)

def minimax(turn, network: AssetFundsNetwork, attacker_budget, defender_budget):
    print(turn + ' Defender:' + str(defender_budget) + ' Attacker ' + str(attacker_budget))
    best_result = None
    node = MiniMaxTree(turn)
    if turn == ATTACKER or turn == ROOT_ATTACKER:
        actions = get_possible_attacks(network, attacker_budget,turn == ROOT_ATTACKER)
        #value = inf
        for (order_set, cost) in actions:
            net2 = copy.deepcopy(network)
            net2.submit_sell_orders(order_set)
            child_result= minimax(MARKET,net2,attacker_budget - cost, defender_budget)
            node.add_child(str(order_set), child_result.tree)
            if not best_result or child_result.value < best_result.value:
                best_result = Result(funds=child_result.funds,node=node, order_set=order_set,
                                     future_actions=child_result.actions, network=child_result.network,
                                     attacker_cost = child_result.attacker_cost+cost,
                                     defender_cost = child_result.defender_cost)
        return best_result
    elif turn == DEFENDER:
#        net2 = copy.deepcopy(network)
#        net2.simulate_trade()
#        if net2.count_margin_calls() ==0:
#            actions =[([], 0)]
#        else:
#           actions = get_possible_defenses(network, defender_budget)
        actions = get_possible_defenses(network, defender_budget)
        for (order_set, cost) in actions:
            net2 = copy.deepcopy(network)
            net2.submit_buy_orders(order_set)
            child_result = minimax(ATTACKER,net2,attacker_budget, defender_budget - cost)
            node.add_child(str(order_set), child_result.tree)
            if not best_result or child_result.value > best_result.value:
                best_result = Result(funds=child_result.funds, node=node, order_set=order_set,
                                     future_actions=child_result.actions, network=child_result.network,
                                     attacker_cost=child_result.attacker_cost,
                                     defender_cost=child_result.defender_cost + cost)

        return best_result
    else: #MARKET
        if network.order_books_empty():
            funds = network.get_funds_in_margin_calls()
            utility = -1*len(funds)
            return Result(funds=funds, node=node, order_set=['MARKET'],
                                     future_actions=[], network=network,
                                     attacker_cost=0,
                                     defender_cost=0)

        network.simulate_trade()
        funds = network.get_funds_in_margin_calls()
        utility  = -1*len(funds)
        if utility != 0:
            return Result(funds=funds, node=node, order_set=['MARKET'],
                                     future_actions=[], network=network, attacker_cost=0, defender_cost=0)

        child_result  = minimax(DEFENDER,network,attacker_budget, defender_budget)
        node.add_child('MARKET', child_result.tree)
        return Result(funds=child_result.funds,node=node, order_set=['MARKET'],
                                     future_actions=child_result.actions, network=child_result.network,
                      attacker_cost=child_result.attacker_cost, defender_cost=child_result.defender_cost)


