import copy
from math import inf

from AssetFundNetwork import AssetFundsNetwork
from actions import get_possible_attacks, get_possible_defenses
from constants import ATTACKER, DEFENDER, MARKET, ROOT_ATTACKER


class Result:
    def __init__(self, value, node, order_set, future_actions, network):
        self.value = value
        best_actions = []
        best_actions.append(order_set)
        best_actions.extend(future_actions)
        self.actions = best_actions
        node.value = value
        self.node = node
        self.network = network


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


def minimax(turn, network: AssetFundsNetwork, attacker_budget, defender_budget):
    best_result = None
    node = MiniMaxTree(turn)
    if turn == ATTACKER or turn == ROOT_ATTACKER:
        actions = get_possible_attacks(network, attacker_budget,turn == ROOT_ATTACKER)
        #value = inf
        for (order_set, cost) in actions:
            net2 = copy.deepcopy(network)
            net2.submit_sell_orders(order_set)
            child_result= minimax(MARKET,net2,attacker_budget - cost, defender_budget)
            node.add_child(str(order_set), child_result.node)
            if not best_result or child_result.value < best_result.value:
                best_result = Result(value=child_result.value,node=node, order_set=order_set,
                                     future_actions=child_result.actions, network=child_result.network)
        return best_result
    elif turn == DEFENDER:
        actions = get_possible_defenses(network, defender_budget)
        for (order_set, cost) in actions:
            net2 = copy.deepcopy(network)
            net2.submit_buy_orders(order_set)
            child_result = minimax(ATTACKER,net2,attacker_budget, defender_budget - cost)
            node.add_child(str(order_set), child_result.node)
            if not best_result or child_result.value > best_result.value:
                best_result = Result(value=child_result.value, node=node, order_set=order_set,
                                     future_actions=child_result.actions, network=child_result.network)

        return best_result
    else: #MARKET
        if network.order_books_empty():
            utility = -1*network.count_margin_calls()
            return Result(value=utility, node=node, order_set=['MARKET'],
                                     future_actions=[], network=network)
        network.simulate_trade()
        utility  = -1*network.count_margin_calls()
        if utility != 0:
            return Result(value=utility, node=node, order_set=['MARKET'],
                                     future_actions=[], network=network)

        child_result  = minimax(DEFENDER,network,attacker_budget, defender_budget)
        node.add_child('MARKET', child_result.node)
        return Result(value=child_result.value,node=node, order_set=['MARKET'],
                                     future_actions=child_result.actions, network=child_result.network)


