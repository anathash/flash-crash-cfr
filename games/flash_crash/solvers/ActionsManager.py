import copy

import numpy
from sortedcontainers import SortedDict, SortedList, SortedKeyList
import AssetFundNetwork
from constants import MAX_ORDERS_PER_ASSETS, SELL, BUY
import itertools
from Orders import Sell, Buy
from SysConfig import SysConfig
from flash_crash_players_cfr import AttackerMoveGameState, DefenderMoveGameState
from solvers.common import copy_network


class Attack:
    def __init__(self, order_set, cost):
        self.cost = cost
        self.order_set = order_set
        self.assets_dict = {x.asset_symbol:x.num_shares for x in order_set}

    def __eq__(self, other):
        return isinstance(other, Attack) and self.cost == other.cost and self.order_set == other.order_set and \
               self.assets_dict == other.assets_dict


class ActionsManager:
    def __init__(self, assets, step_order_size, max_order_num=1, attacker_budgets= None, portfolios_probs= None):
        self.__step_order_size = step_order_size
        self.__max_order_num = max_order_num
        self.__id_to_sym = {}
        i = 1
        for sym in assets.keys():
            self.__id_to_sym[i] = sym
            i += 1
        self.__portfolios_dict = self.__get_portfolio_dict(assets)
        self.__sorted_keys = SortedKeyList(self.__portfolios_dict.keys())
        self.__sell_all_assets = [Sell(a.symbol, self.__step_order_size * a.daily_volume)
                                  for a in assets.values()]
        self.__updated_asset = None
        self.__portfolios_probs = portfolios_probs
        self.__id_to_portfolio = {}
        self.__pid_to_cost = {}
        if not portfolios_probs:
            if attacker_budgets:
                self.__set_uniform_portfolios_probabilities(attacker_budgets)

    def get_portfolios(self):
        return self.__id_to_portfolio

    def get_probable_portfolios(self):
        return {x:y for x,y in self.__id_to_portfolio.items() if x in self.__portfolios_probs}

    def get_portfolios_prob(self):
        return self.__portfolios_probs

    def get_portfolios_in_budget(self, budget):
        return [pid for pid in self.__id_to_portfolio.keys() if self.__pid_to_cost[pid] <= budget]

    def get_portfolios_in_budget_dict(self, budgets):
        return {b: self.get_portfolios_in_budget(b) for b in budgets}

    def __set_uniform_portfolios_probabilities(self, attacker_budgets):
        attackers_portfolio_num = {x:0 for x in attacker_budgets}

        for cost, portfolios_list in self.__portfolios_dict.items():
            for a in attacker_budgets:
                if a >= cost:
                    attackers_portfolio_num[a] += len(portfolios_list)
        attacker_prob = 1./len(attacker_budgets)
        i = 0
        portfolios_probs = {}
        for cost, portfolios_list in self.__portfolios_dict.items():
            for p in portfolios_list:
                i+=1
                id = 'p' + str(i)
                self.__id_to_portfolio[id] = p
                self.__pid_to_cost[id] = cost
                portfolios_probs[id] = 0
                for a in attacker_budgets:
                    if a >= cost:
                        portfolios_probs[id] += attacker_prob/attackers_portfolio_num[a]
        assert (numpy.isclose(sum(portfolios_probs.values()), 1.0, rtol=1e-05, atol=1e-08, equal_nan=False))
#        assert (1 == sum(portfolios_probs.values()))
#        self.__portfolios_probs = portfolios_probs
        self.__portfolios_probs = {x: y for x, y in portfolios_probs.items() if portfolios_probs[x] > 0}

    @staticmethod
    def __filter_from_history(action, history, key):
        assets_in_limit = [k  for k, v in history[key].items() if v == MAX_ORDERS_PER_ASSETS]
        for asset in action.assets_dict:
            if asset in assets_in_limit:
                return True
        return False

    @staticmethod
    def __gen_sell_order(asset, size):
        return Sell(asset.symbol, size * asset.daily_volume)

    @staticmethod
    def __gen_buy_order(asset, size):
        return Buy(asset.symbol, size * asset.daily_volume)

    @staticmethod
    def __get_defenses_in_budget(assets, single_asset_orders, asset_price_lambda, budget, asset_filter_sym=None):
        actions = []
        orders_in_budget = [o for o in single_asset_orders if
                            asset_price_lambda(assets[o.asset_symbol]) * o.num_shares <= budget]
        for i in range(0, len(orders_in_budget)):
            action_subset = itertools.combinations(single_asset_orders, i + 1)
            # attackers buys before game start
            for orders in action_subset:
                orders_list = list(orders)
                if asset_filter_sym and (asset_filter_sym not in [x.asset_symbol for x in orders]):
                    continue
                attack_cost = sum(
                    [asset_price_lambda(assets[order.asset_symbol]) * order.num_shares for order in orders_list])

                if attack_cost <= budget:
                    actions.append((orders_list, attack_cost))
        return actions

    def __get_single_orders(self,assets, gen_order_func):
        orders = []
        for asset in assets.values():
            order = gen_order_func(asset, self.__step_order_size)
            orders.append(order)
        return orders

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
        for i in range(0, self.__max_order_num):
            num_shares = int(self.__step_order_size * assets[asset_sym].daily_volume * (i + 1))
            if not num_shares:
                return orders
            order = Sell(asset_sym, num_shares)
            cost = asset.zero_time_price * num_shares
            for action in prev_orders:
                new_order = copy.copy(action.order_set)
                new_order.append(order)
                new_cost = cost + action.cost
                orders.append(Attack(order_set=new_order, cost=new_cost))
        return orders

    def __get_portfolio_dict(self, assets):
        attacks = self.__get_all_attacks(assets, len(assets))
        portfolios_dict = {}
        for attack in attacks:
            if attack.cost not in portfolios_dict:
                portfolios_dict[attack.cost] = []
            portfolios_dict[attack.cost].append(attack)
        return portfolios_dict

    def __rebuild_portfolio_dict(self, asset_sym,  old_price, new_price):
        new_portfolios_dict = {}
        price_delta = new_price - old_price
        for cost, attacks in self.__portfolios_dict.items():
            for attack in attacks:
                if asset_sym in attack.assets_dict:
                    new_cost = attack.cost + price_delta * attack.assets_dict[asset_sym]
                else:
                    new_cost = attack.cost
                if new_cost not in new_portfolios_dict:
                    new_portfolios_dict[new_cost] = []
                new_portfolios_dict[new_cost].append(attack)
        return new_portfolios_dict

    def update_asset(self, asset_sym, old_price, new_price):
        self.__updated_asset = asset_sym
        self.__portfolios_dict = self.__rebuild_portfolio_dict(asset_sym,  old_price, new_price)
        self.__sorted_keys = SortedKeyList(self.__portfolios_dict.keys())

    def __build_actions(self, single_orders, no_more_sell_orders):
        actions = []
        for i in range(1, len(single_orders)+1):
            action_subset = itertools.combinations(single_orders, i)
            for orders in action_subset:
                orders_list = list(orders)
                remaining_orders = [x for x in single_orders if x not in orders_list]
                actions.append({'action_subset': list(action_subset), 'remaining_orders': remaining_orders})
        if not no_more_sell_orders:
            actions.append({'action_subset': [] ,'remaining_orders': single_orders})

    def __attack_subset(self, order_set1, order_set2):
        if len(order_set1)> len(order_set2):
            return
        for order in order_set1:
            if order not in order_set2:
                return False
        return True

    def get_possible_attacks_from_portfolio(self, attack, no_more_sell_orders):
        actions = []
        id2po = self.__id_to_portfolio.values()
        optional_attacks = [x.order_set for x in id2po if self.__attack_subset(x.order_set, attack)]
        for a in optional_attacks:
            if not a and no_more_sell_orders: #nope actions not allowed if sell book is empty
                continue
            remaining_orders = [x for x in attack if x not in a]
            actions.append({'action_subset': a, 'remaining_orders': remaining_orders})
#        if not no_more_sell_orders:
#            actions.append({'action_subset': [], 'remaining_orders': attack.assets_dict})
        return actions

    def get_possible_attacks(self, budget = None, history=[], asset_filter_sym=None):
        if budget is None:
            attacks_in_budget = self.__portfolios_dict.values()
        else:
            attacks_costs_in_budget = self.__sorted_keys.irange_key(min_key=0, max_key=budget)
            attacks_in_budget = [self.__portfolios_dict[cost] for cost in attacks_costs_in_budget]

        attacks_in_budget_flat = [attack for attack_list in attacks_in_budget for attack in attack_list]
        if asset_filter_sym:
            attacks_in_budget_flat= [x for x in attacks_in_budget_flat if asset_filter_sym in x.assets_dict]
        if history:
            return [(attack.order_set, attack.cost) for attack in attacks_in_budget_flat
                    if not self.__filter_from_history(attack, history, SELL)]
        else:
            return [(attack.order_set, attack.cost) for attack in attacks_in_budget_flat]

    def get_possible_defenses(self, af_network, budget, history_assets_dict={}, asset_filter_sym=None):
        funds_under_risk = self.__funds_under_risk(copy_network(af_network))
        if not  funds_under_risk:
            return [([], 0)]
        asset_syms = set()
        for f in funds_under_risk:
            asset_syms.update(af_network.funds[f].portfolio.keys())
        assets = {sym: af_network.assets[sym] for sym in asset_syms}
        single_asset_defenses = self.__get_single_orders(assets, self.__gen_buy_order)
        if history_assets_dict:
            filtered_defenses = [d for d in single_asset_defenses if d.asset_symbol not in history_assets_dict[BUY]
                                 or history_assets_dict[BUY][d.asset_symbol] < MAX_ORDERS_PER_ASSETS]
        else:
            filtered_defenses = single_asset_defenses
        actions = self.__get_defenses_in_budget(assets, filtered_defenses, lambda a: a.price, budget, asset_filter_sym)
        actions.append(([], 0))
        return actions

    def get_additional_actions(self, state):
        if isinstance(state, AttackerMoveGameState):
            return self.get_possible_attacks(state.budget.attacker, self.additional_asset)
        if isinstance(state, DefenderMoveGameState):
            return self.get_additional_defenses(state.budget.attacker, self.additional_asset)
        return []

