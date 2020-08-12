import random

from constants import ATTACKER, CHANCE
from games.bases import GameStateBase


class SelectorGameStateBase(GameStateBase):

    def __init__(self, parent, to_move, actions):
        super().__init__(parent = parent, to_move = to_move,actions=actions)
        self.children = {}

    def inf_set(self):
        return self._information_set


class SelectorRootChanceGameState(GameStateBase):
    def __init__(self, attacker_budgets, attacks_utilities, attacks_costs):
        super().__init__(parent=None, to_move=CHANCE, actions =[str(x) for x in attacker_budgets])
        self.children = {}
        for budget in attacker_budgets:
            attacks_in_budget = attacks_costs[budget]
            self.children[str(budget)]= SelectorAttackerMoveGameState(
                parent=self, to_move=ATTACKER,
                attacks={x:y for x,y in attacks_utilities.items() if x in attacks_in_budget},
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


class SelectorAttackerMoveGameState(SelectorGameStateBase):
    def __init__(self, parent, to_move, attacks, attacker_budget):

        super().__init__(parent=parent,  to_move=to_move,
                          actions=list(attacks.keys()))

        self.children = {
            str(goal): SelectorAttackGameState(
                parent=self,  to_move='ATTACK',goal = goal, utility = utility,attacker_budget=attacker_budget
            ) for goal, utility in attacks.items()
        }

        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])
        self._information_set = ".{0}".format(attacker_budget)

    def is_terminal(self):
        return False


class SelectorAttackGameState(SelectorGameStateBase):
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
