import copy

from AssetFundNetwork import AssetFundsNetwork
from SysConfig import SysConfig
from actions import get_possible_attacks, get_possible_defenses
from constants import ATTACKER, DEFENDER, MARKET
from solvers.ActionsManager import ActionsManager


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


def single_agent(network: AssetFundsNetwork,attacker_budget, step_order_size):
    action_manager = ActionsManager(network.assets, step_order_size, SysConfig.get("MAX_NUM_ORDERS"))
    network.limit_trade_step = False
    return minimax2(action_manager, ATTACKER, network, attacker_budget, 0, True)

def minimax2(actions_mgr, turn, network: AssetFundsNetwork, attacker_budget, defender_budget, include_opt_out = True):
 #   print(turn + ' Defender:' + str(defender_budget) + ' Attacker' + str(attacker_budget))
    best_result = None
    node = MiniMaxTree(turn)
    if turn == ATTACKER:
#        order_size = SysConfig.get("STEP_ORDER_SIZE")
#        max_num_orders = SysConfig.get("MAX_NUM_ORDERS")
#        actions_mgr = ActionsManager(order_size, max_num_orders)
#        es_solver = SingleAgentESSolver(network, order_size, max_num_orders)
 #       portfolios = es_solver.get_attacks_in_budget(attacker_budget, include_opt_out)
        attacks = actions_mgr.get_possible_attacks(attacker_budget)
        i = -1
        for (order_set, cost) in attacks:
            i+=1
            net2 = copy.deepcopy(network)
            net2.submit_sell_orders(order_set)
            child_result= minimax2(actions_mgr, MARKET,net2,attacker_budget - cost, defender_budget)
            node.add_child(str(order_set), child_result.tree)
            total_cost = child_result.attacker_cost + cost
            if not best_result or child_result.value < best_result.value or (child_result.value == best_result.value and
                                                                             total_cost < best_result.attacker_cost):
                best_result = Result(funds=child_result.funds,node=node, order_set=order_set,
                                     future_actions=child_result.actions, network=child_result.network,
                                     attacker_cost = total_cost,
                                     defender_cost = child_result.defender_cost)
        return best_result
    elif turn == DEFENDER:
        actions = actions_mgr.get_possible_defenses(network, defender_budget)
        for (order_set, cost) in actions:
            net2 = copy.deepcopy(network)
            net2.submit_buy_orders(order_set)
            child_result = minimax2(actions_mgr, MARKET,net2,attacker_budget, defender_budget - cost)
            node.add_child(str(order_set), child_result.tree)
            total_cost = child_result.defender_cost + cost
            if not best_result or child_result.value > best_result.value  or (child_result.value == best_result.value and
                                                                              total_cost < best_result.defender_cost):
                best_result = Result(funds=child_result.funds, node=node, order_set=order_set,
                                     future_actions=child_result.actions, network=child_result.network,
                                     attacker_cost=child_result.attacker_cost,
                                     defender_cost=total_cost)

        return best_result
    else: #MARKET
        net2 = copy.deepcopy(network)
        net2.simulate_trade()
        funds = net2.get_funds_in_margin_calls()
        if net2.no_more_sell_orders():
            return Result(funds=funds, node=node, order_set=['MARKET'],
                                     future_actions=[], network=net2,
                                     attacker_cost=0,
                                     defender_cost=0)

        child_result  = minimax2(actions_mgr, DEFENDER,net2,attacker_budget, defender_budget)
        node.add_child('MARKET', child_result.tree)
        return Result(funds=child_result.funds,node=node, order_set=['MARKET'],
                                     future_actions=child_result.actions, network=child_result.network,
                      attacker_cost=child_result.attacker_cost, defender_cost=child_result.defender_cost)


def alphabeta(actions_mgr, turn, network: AssetFundsNetwork, attacker_budget, defender_budget, alpha, beta, include_opt_out=True):
    #   print(turn + ' Defender:' + str(defender_budget) + ' Attacker' + str(attacker_budget))
    best_result = None
    node = MiniMaxTree(turn)
    if turn == ATTACKER:
#        order_size = SysConfig.get("STEP_ORDER_SIZE")
#        max_num_orders = SysConfig.get("MAX_NUM_ORDERS")
#        es_solver = SingleAgentESSolver(network, order_size, max_num_orders)
#        portfolios = es_solver.get_attacks_in_budget(attacker_budget, include_opt_out)
#        actions_mgr = ActionsManager(order_size, max_num_orders)
        attacks = actions_mgr.get_possible_attacks(attacker_budget)

        # value = inf
        i = -1
        for (order_set,cost) in attacks:
            i += 1
            net2 = copy.deepcopy(network)
            net2.submit_sell_orders(order_set)
            child_result = alphabeta(actions_mgr, MARKET, net2, attacker_budget - cost, defender_budget, alpha, beta)
            node.add_child(str(order_set), child_result.tree)
            total_cost = child_result.attacker_cost + cost
            if child_result.value < beta[0] or (child_result.value == beta[0] and total_cost < beta[1]):
                beta = (child_result.value, total_cost)
            if not best_result or child_result.value < best_result.value or (child_result.value == best_result.value and
                                                                             total_cost < best_result.attacker_cost):
                best_result = Result(funds=child_result.funds, node=node, order_set=order_set,
                                     future_actions=child_result.actions, network=child_result.network,
                                     attacker_cost=total_cost,
                                     defender_cost=child_result.defender_cost)
        return best_result
    elif turn == DEFENDER:
        # net2 = copy.deepcopy(network)
        # net2.simulate_trade()
        # if net2.count_margin_calls() == 0:
        #     actions = [([], 0)]
        # else:
        actions = actions_mgr.get_possible_defenses(network, defender_budget)
        for (order_set, cost) in actions:
            net2 = copy.deepcopy(network)
            net2.submit_buy_orders(order_set)
            child_result = alphabeta(actions_mgr, MARKET, net2, attacker_budget, defender_budget - cost, alpha, beta)
            node.add_child(str(order_set), child_result.tree)
            total_cost = child_result.defender_cost + cost
            if child_result.value >= alpha[0]:
                alpha = (child_result.value, child_result.attacker_cost)

            if not best_result or child_result.value > best_result.value or (child_result.value == best_result.value and
                                                                             total_cost < best_result.defender_cost):
                best_result = Result(funds=child_result.funds, node=node, order_set=order_set,
                                     future_actions=child_result.actions, network=child_result.network,
                                     attacker_cost=child_result.attacker_cost,
                                     defender_cost=total_cost)

            if alpha[0] > beta[0] or (alpha[0] == beta[0] and alpha[1] < beta[1]):
                break

        return best_result
    else:  # MARKET
        net2 = copy.deepcopy(network)
        net2.simulate_trade()
        funds = net2.get_funds_in_margin_calls()
        if net2.no_more_sell_orders():
            return Result(funds=funds, node=node, order_set=['MARKET'],
                          future_actions=[], network=net2,
                          attacker_cost=0,
                          defender_cost=0)

        child_result = alphabeta(actions_mgr, DEFENDER, net2, attacker_budget, defender_budget, alpha, beta)
        node.add_child('MARKET', child_result.tree)
        return Result(funds=child_result.funds, node=node, order_set=['MARKET'],
                      future_actions=child_result.actions, network=child_result.network,
                      attacker_cost=child_result.attacker_cost, defender_cost=child_result.defender_cost)

def minimax(actions_mgr, turn, network: AssetFundsNetwork, attacker_budget, defender_budget, root_attacker = False):
   # print(turn + ' Defender:' + str(defender_budget) + ' Attacker ' + str(attacker_budget))
    best_result = None
    node = MiniMaxTree(turn)
    if turn == ATTACKER:
        attacks = actions_mgr.get_possible_attacks(attacker_budget)
#        actions = get_possible_attacks(network, attacker_budget,root_attacker)
        #value = inf
        for (order_set, cost) in attacks:
            net2 = copy.deepcopy(network)
            net2.submit_sell_orders(order_set)
            child_result= minimax(actions_mgr, MARKET,net2,attacker_budget - cost, defender_budget)
            node.add_child(str(order_set), child_result.tree)
            total_cost = child_result.attacker_cost+cost
            if not best_result or child_result.value < best_result.value or (child_result.value == best_result.value and
                                                                             total_cost < best_result.attacker_cost):
                best_result = Result(funds=child_result.funds,node=node, order_set=order_set,
                                     future_actions=child_result.actions, network=child_result.network,
                                     attacker_cost = total_cost,
                                     defender_cost = child_result.defender_cost)
        return best_result
    elif turn == DEFENDER:
        net2 = copy.deepcopy(network)
        net2.simulate_trade()
        if not net2.count_margin_calls() ==0:
            #actions = get_possible_defenses(network, defender_budget)
            actions = actions_mgr.get_possible_defenses(network, defender_budget)
        for (order_set, cost) in actions:
            net2 = copy.deepcopy(network)
            net2.submit_buy_orders(order_set)
            child_result = minimax(actions_mgr, ATTACKER,net2,attacker_budget, defender_budget - cost)
            node.add_child(str(order_set), child_result.tree)
            total_cost = child_result.defender_cost + cost
            if not best_result or child_result.value > best_result.value or (child_result.value == best_result.value and
                                                                               total_cost < best_result.defender_cost):
                best_result = Result(funds=child_result.funds, node=node, order_set=order_set,
                                     future_actions=child_result.actions, network=child_result.network,
                                     attacker_cost=child_result.attacker_cost,
                                     defender_cost=total_cost)

        return best_result
    else: #MARKET
        net2 = copy.deepcopy(network)
        net2.simulate_trade()
        funds = net2.get_funds_in_margin_calls()
        if len(funds) or net2.no_more_sell_orders():
            return Result(funds=funds, node=node, order_set=['MARKET'],
                                     future_actions=[], network=net2,
                                     attacker_cost=0,
                                     defender_cost=0)
        child_result  = minimax(actions_mgr, DEFENDER,net2,attacker_budget, defender_budget)
        node.add_child('MARKET', child_result.tree)
        return Result(funds=child_result.funds,node=node, order_set=['MARKET'],
                                     future_actions=child_result.actions, network=child_result.network,
                      attacker_cost=child_result.attacker_cost, defender_cost=child_result.defender_cost)


