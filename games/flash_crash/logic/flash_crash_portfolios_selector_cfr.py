import copy

from AssetFundNetwork import AssetFundsNetwork
import random

from constants import ATTACKER, CHANCE, DEFENDER, MARKET, BUY, SELL, SIM_TRADE
from games.bases import GameStateBase
from solvers.common import copy_network


class PortfolioSelectorFlashCrashGameStateBase(GameStateBase):

    def __init__(self, parent, to_move, actions):
        super().__init__(parent = parent, to_move = to_move,actions=actions)
        self.children = {}


    def inf_set(self):
        return self._information_set

    def evaluation(self):
        if not self.is_terminal():
            raise RuntimeError("trying to evaluate non-terminal node")

        return -1*self.af_network.count_margin_calls()


class PortfolioSelectorFlashCrashRootChanceGameState(GameStateBase):
    def __init__(self, attacker_budgets, portfolios_utilities, action_manager):
        super().__init__(parent=None, to_move=CHANCE, actions =[str(x) for x in attacker_budgets])
        self.children = {}
        for budget in attacker_budgets:
            pids_in_budget= action_manager.get_portfolios_in_budget(budget)
            self.children[str(budget)]= PortfolioSelectorAttackerMoveGameState(
                parent=self, to_move=ATTACKER,
                portfolios={x:y for x,y in portfolios_utilities.items() if x in pids_in_budget},
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


class PortfolioSelectorAttackerMoveGameState(PortfolioSelectorFlashCrashGameStateBase):
    def __init__(self, parent, to_move, portfolios, attacker_budget):

        super().__init__(parent=parent,  to_move=to_move,
                          actions=list(portfolios.keys()))

        self.children = {
            pid: PortfolioMoveGameState(
                parent=self,  to_move='PORTFOLIO',pid = pid, utility = utility,attacker_budget=attacker_budget
            ) for pid, utility in portfolios.items()
        }

        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])
        self._information_set = ".{0}".format(attacker_budget)

    def is_terminal(self):
        return False


class PortfolioMoveGameState(PortfolioSelectorFlashCrashGameStateBase):
    def __init__(self, parent,to_move, pid, utility, attacker_budget):
        super().__init__(parent=parent,  to_move=to_move, actions = [])
        self.tree_size = 1
        self.pid = pid
        self.__utility = utility
        self._information_set = ".{0}.{1}".format(attacker_budget, pid)

    def is_terminal(self):
        return True

    def evaluation(self):
        if not self.is_terminal():
            raise RuntimeError("trying to evaluate non-terminal node")

        return self.__utility
