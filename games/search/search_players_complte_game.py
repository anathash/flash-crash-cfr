import copy
from math import inf

from AssetFundNetwork import AssetFundsNetwork
import random

from constants import ATTACKER, CHANCE, DEFENDER, MARKET, BUY, SELL, SIM_TRADE
from games.bases import GameStateBase
from solvers.common import copy_network


class SearchCompleteGameStateBase(GameStateBase):

    def __init__(self, parent, to_move, actions, grid, actions_history):
        super().__init__(parent=parent, to_move = to_move,actions=actions)
        self.actions_history=actions_history
        self.grid = grid
        self.children = {}

    def inf_set(self):
        return self._information_set

    def evaluation(self):
        if not self.is_terminal():
            raise RuntimeError("trying to evaluate non-terminal node")
        if self.self.rounds_left == 0:
            return inf
        else:
            return self.grid.get_game_value()

    def is_terminal(self):
        return self.rounds_left == 0 or self.grid.attacker_caught()

class SearchCompleteGameRootChanceGameState(GameStateBase):
    def __init__(self, goal_costs, grid, attacker_budgets):
        super().__init__(parent=None, to_move=CHANCE, grid=grid, actions = [str(x) for x in attacker_budgets])
        self.children = {
            str(attacker_budget): SearchCompleteGameSelectorGameState(
                parent=self,  to_move=ATTACKER,
                grid=grid, attacker_budget=attacker_budget, goal_costs=goal_costs
            ) for attacker_budget in attacker_budgets
        }

        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])
        self._chance_prob = 1./len(attacker_budgets)


    def is_terminal(self):
        return False

    def inf_set(self):
        return "."

    def chance_prob(self):
        return self._chance_prob

    def sample_one(self):
        return random.choice(list(self.children.values()))


class SearchCompleteGameSelectorGameState(SearchCompleteGameStateBase):
    def __init__(self, parent, to_move, grid,  attacker_budget, goal_costs):
        goals_in_budget = [x for x in goal_costs.keys() if goal_costs[x] <= attacker_budget]
        actions = [str(g) for g in goals_in_budget]
        super().__init__(parent=parent, to_move=to_move, actions= actions)

        self.children = {
            str(goal): SearchCompleteGameAttackerMoveGameState(
                parent=self,  to_move=ATTACKER,
                af_network=grid.set_attacker_goal(goal),
                actions_history={ATTACKER: ['g:' + str(goal)], DEFENDER: []},
            ) for goal in goals_in_budget
        }

        self._information_set = ".{0}".format(str(attacker_budget))
        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])

    def is_terminal(self):
        return False

    def inf_set(self):
        return self._information_set


class SearchCompleteGameAttackerMoveGameState(SearchCompleteGameStateBase):
    def __init__(self, parent,  to_move, grid,  actions_history, rounds_left):
        if self.is_terminal():
            actions = []
        else:
            actions = grid.get_attacker_actions()

        super().__init__(parent=parent,  to_move=to_move, actions = [str(x) for x in actions ],
                           actions_history=actions_history, rounds_left = rounds_left)

        for action in actions:
            actions_history2 = copy.deepcopy(actions_history)
            actions_history2.append(action)
            self.children[str(action)] = SearchCompleteGameDefenderMoveGameState(
                parent=self,
                to_move=DEFENDER,
                grid=grid.apply_attacker_action(action),
                actions_history=actions_history2,
                rounds_left=rounds_left
            )

        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])
        self._information_set = ".{0}".format(".".join(self.actions_history[ATTACKER]))

    def is_terminal(self):
        return self.terminal


class SearchCompleteGameDefenderMoveGameState(SearchCompleteGameStateBase):

    def __init__(self, parent, to_move, actions_history, grid:Grid, rounds_left):
        actions = grid.get_defender_actions()
        super().__init__(parent=parent, to_move=to_move, actions=[(str(x(0)), str(x(1))) for x in actions],
                         actions_history=actions_history, rounds_left = rounds_left)
        for action in actions:
            actions_history2 = copy.deepcopy(actions_history)
            actions_history2.append(action)
            self.children[str(action)] = SearchCompleteGameDefenderMoveGameState(
                parent=self,
                to_move=ATTACKER,
                grid=grid.apply_defender_action(action),
                actions_history=actions_history2,
                rounds_left=rounds_left-1
            )
        self._information_set = ".{0}".format(".".join(self.actions_history[DEFENDER]))
        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])


    def is_terminal(self):
        return False




