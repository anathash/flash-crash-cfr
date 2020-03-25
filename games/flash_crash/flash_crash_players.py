import itertools

from Orders import EmptyOrder
from flash_crash.AssetFundNetwork import AssetFundsNetwork
import random

from flash_crash.constants import ATTACKER, CHANCE, DEFENDER, MARKET
from games.bases import GameStateBase
from flash_crash import Orders


class FlashCrashRootChanceGameState(GameStateBase):

    def __init__(self, af_network:AssetFundsNetwork, actions):
        self.af_network = af_network
        super().__init__(parent=None, to_move=CHANCE, actions = actions)
        self.children = {
            budget: AttackerMoveGameState(
                self,  ATTACKER, [],  budget, af_network
            ) for budget in self.actions
        }
        self._chance_prob = 1. / len(self.children)

    def is_terminal(self):
        raise NotImplementedError

    def inf_set(self):
        return "."

    def chance_prob(self):
        return self._chance_prob

    def sample_one(self):
        return random.choice(list(self.children.values()))


class FlashCrashGameStateBase(GameStateBase):

    def __init__(self, parent, to_move, actions_history, af_network, budget):
        super().__init__(parent = parent, to_move = to_move,actions_history=actions_history)
        self.af_network = af_network
        self.actions_history = actions_history
        self.budget = budget
        self.children = {}

    def inf_set(self):
        return self._information_set

    def evaluation(self):
        if not self.is_terminal():
            raise RuntimeError("trying to evaluate non-terminal node")

        self.af_network.clear_order_book()
        return -1*self.af_network.count_margin_calls()


class MarketMoveGameState(GameStateBase):

    def __init__(self, parent, to_move, actions_history, budget, af_network):
        super().__init__(parent = parent, to_move = to_move, actions_history=actions_history,
                         af_network = af_network, budget=budget)

        self.children['SIM'] = AttackerMoveGameState(
                self,
                ATTACKER,
                budget,
                af_network.simulate_trade()
            )

        self._information_set = ".{0}.{1}".format(self.af_network.public_state(), ".".join(self.actions_history))

    def is_terminal(self):
        return self.af_network.margin_calls() or self.actions == []


class AttackerMoveGameState(FlashCrashGameStateBase):

    def __init__(self, parent, to_move, actions_history, budget, af_network):
        super().__init__(parent=parent, to_move=to_move, actions_history=actions_history,
                         af_network=af_network, budget=budget)
        self.actions = self.__get_possible_attacks()
        for action, cost in self.actions:
            self.budget.attacker_budget -= cost
            self.actions_history += [action]
            self.children[action] = DefenderMoveGameState(
                self,
                DEFENDER,
                budget,
                af_network.apply_action(action)
            )

        self._information_set = ".{0}.{1}".format(self.af_network.public_state(), ".".join(self.actions_history))

    def is_terminal(self):
        return self.af_network.margin_calls() or self.actions == []

    def __get_possible_attacks(self):
        actions = []
        single_asset_attacks =self.af_network.get_single_orders(AssetFundsNetwork.gen_sell_order) # TODO: maybe allow various attack sizes?
        for i in range(1, len(single_asset_attacks)):
            action_subset = itertools.combinations(single_asset_attacks, i)
            attack_cost = sum(a.cost for a in action_subset)
            if attack_cost <= self.budget:
                actions.append((action_subset,attack_cost))
        actions.append(EmptyOrder())
        return actions


class DefenderMoveGameState(FlashCrashGameStateBase):

    def __init__(self, parent, to_move, actions_history, budget, af_network):
        super().__init__(parent = parent, to_move = to_move, actions_history=actions_history,
                         af_network = af_network,  budget=budget)
        self.actions = self.__get_possible_defenses()

        if not self.actions:
            self.budget.defender_budget = 0 #in case there is only a small amount of money
            self.actions.append(([Orders.EmptyOrder()],0))

        elif not self.af_network.min_defense_conditions():
            self.actions.append(([Orders.EmptyOrder()], 0))

        else:
            for action, cost in self.actions:
                self.budget.defender_budget -= cost
                self.actions_history += [action]
                self.children[action] = MarketMoveGameState(
                    self,
                    MARKET,
                    budget,
                    af_network.apply_action(action)
                )

        self._information_set = ".{0}.{1}".format(self.af_network.public_state(), ".".join(self.actions_history))

    def is_terminal(self):
        return False

    def __get_possible_defenses(self):
        actions = []
        funds_under_threat = self.af_network.get_funds_under_threat()
        assets = set()
        for funds in funds_under_threat:
            for f in funds:
                assets.update(f.portfolio.keys())
        single_asset_defenses = self.af_network.get_single_orders(AssetFundsNetwork.gen_buy_order) # TODO: maybe allow various attack sizes?
        for i in range(1, len(single_asset_defenses)):
            action_subset = itertools.combinations(single_asset_defenses, i)
            defense_cost = sum(a.cost for a in action_subset)
            if defense_cost <= self.budget:
                actions.append((action_subset, defense_cost))
        actions.append(EmptyOrder())
        return actions

