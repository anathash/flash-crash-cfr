import copy

from AssetFundNetwork import AssetFundsNetwork
import random

from constants import ATTACKER, CHANCE, DEFENDER, MARKET, BUY, SELL, SIM_TRADE
from games.bases import GameStateBase
from solvers.common import copy_network


class SearchSelectorGameStateBase(GameStateBase):

    def __init__(self, parent, to_move, actions):
        super().__init__(parent = parent, to_move = to_move,actions=actions)
        self.children = {}

    def inf_set(self):
        return self._information_set

    def evaluation(self):
        if not self.is_terminal():
            raise RuntimeError("trying to evaluate non-terminal node")

        return -1*self.af_network.count_margin_calls()


class SearchSelectorChanceGameState(GameStateBase):
    def __init__(self, attacker_budgets, attacks_utilities, goal_costs):
        super().__init__(parent=None, to_move=CHANCE, actions =[str(x) for x in attacker_budgets])
        self.children = {}
        for budget in attacker_budgets:
            goals_in_budget= [x for x in goal_costs.keys() if goal_costs[x] <= budget]
            self.children[str(budget)]= SearchSelectorAttackerMoveGameState(
                parent=self, to_move=ATTACKER,
                attacks={x:y for x,y in attacks_utilities.items() if x in goals_in_budget},
                attacker_budget=budget)
        self._chance_prob = 1. / len(self.children)
        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])

    def is_terminal(self):
        return False

    def inf_set(self):
        return "."

    def chance_prob(self):
        return self._chance_prob

    def sample_one(self):
        return random.choice(list(self.children.values()))


class SearchSelectorAttackerMoveGameState(SearchSelectorGameStateBase):
    def __init__(self, parent, to_move, attacks, attacker_budget):

        super().__init__(parent=parent,  to_move=to_move,
                          actions=list(attacks.keys()))

        self.children = {
            str(goal): SearchSelectorAttackGameState(
                parent=self,  to_move='ATTACK',goal = goal, utility = utility,attacker_budget=attacker_budget
            ) for goal, utility in attacks.items()
        }

        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])
        self._information_set = ".{0}".format(attacker_budget)

    def is_terminal(self):
        return False


class SearchSelectorAttackGameState(SearchSelectorChanceGameState):
    def __init__(self, parent,to_move, goal, utility, attacker_budget):
        super().__init__(parent=parent,  to_move=to_move, actions = [])
        self.tree_size = 1
        self.goal = goal
        self.__utility = utility
        self._information_set = ".{0}.{1}".format(attacker_budget, goal)

    def is_terminal(self):
        return True

    def evaluation(self):
        if not self.is_terminal():
            raise RuntimeError("trying to evaluate non-terminal node")

        return self.__utility
