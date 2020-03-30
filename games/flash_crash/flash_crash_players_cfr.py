import itertools

from Orders import EmptyOrder
from AssetFundNetwork import AssetFundsNetwork
import random

from actions import get_possible_defenses, get_possible_attacks
from constants import ATTACKER, CHANCE, DEFENDER, MARKET
from games.bases import GameStateBase
import Orders


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
                DEFENDER,
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
        self.actions = get_possible_attacks(self.af_network, budget)
        for action, cost in self.actions:
            self.budget.attacker_budget -= cost
            self.actions_history += [action]
            self.children[action] = DefenderMoveGameState(
                self,
                MARKET,
                budget,
                af_network.apply_action(action)
            )

        self._information_set = ".{0}.{1}".format(self.af_network.public_state(), ".".join(self.actions_history))

    def is_terminal(self):
        return self.af_network.margin_calls() or self.actions == []


class DefenderMoveGameState(FlashCrashGameStateBase):

    def __init__(self, parent, to_move, actions_history, budget, af_network):
        super().__init__(parent = parent, to_move = to_move, actions_history=actions_history,
                         af_network = af_network,  budget=budget)
        self.actions = get_possible_defenses(self.af_network, budget)

        if not self.actions:
            self.budget.defender_budget = 0 #in case there is only a small amount of money
            self.actions.append(([Orders.EmptyOrder()], 0))

        elif not self.af_network.min_defense_conditions():
            self.actions.append(([Orders.EmptyOrder()], 0))

        else:
            for action, cost in self.actions:
                self.budget.defender_budget -= cost
                self.actions_history += [action]
                self.children[action] = MarketMoveGameState(
                    self,
                    ATTACKER,
                    budget,
                    af_network.apply_action(action)
                )

        self._information_set = ".{0}.{1}".format(self.af_network.public_state(), ".".join(self.actions_history))

    def is_terminal(self):
        return False


