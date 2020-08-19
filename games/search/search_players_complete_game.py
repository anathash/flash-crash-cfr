import copy
from math import inf

import random

from constants import ATTACKER, CHANCE, DEFENDER
from games.bases import GameStateBase
from search import Grid
from search.search_common_players import SearchAttackerMoveGameState, SearchGameStateBase


class SearchCompleteGameRootChanceGameState(GameStateBase):
    def __init__(self, grid, attacker_budgets, rounds_left):
        goals_in_budget_dict = grid.get_attacks_in_budget_dict(attacker_budgets, False)
        super().__init__(parent=None, to_move=CHANCE, actions= [str(x) for x in attacker_budgets])

        self.children = {
            str(attacker_budget): SearchCompleteGameSelectorGameState(
                parent=self,  to_move=ATTACKER,
                grid=grid, attacker_budget=attacker_budget,
                rounds_left=rounds_left,
                goals_in_budget=goals_in_budget_dict[attacker_budget],
                location_history={ATTACKER: [str(attacker_budget)],
                                  DEFENDER: []},
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

    def evaluation(self):
        raise RuntimeError("trying to evaluate non-terminal node")


class SearchCompleteGameSelectorGameState(SearchGameStateBase):
    def __init__(self, parent, to_move, grid,  attacker_budget, rounds_left, goals_in_budget, location_history):

        actions = [str(g) for g in goals_in_budget]
        super().__init__(parent=parent, to_move=to_move, actions=actions,
                         grid=grid, location_history=location_history, rounds_left=rounds_left, terminal=False)
        defender_curr_locations, attacker_curr_location = grid.get_curr_locations_strs()
        for goal in goals_in_budget:
            location_history2 = copy.deepcopy(location_history)
            location_history2[ATTACKER].append('g:' + str(goal))
            location_history2[ATTACKER].append(attacker_curr_location)
            location_history2[DEFENDER].append(defender_curr_locations)
            self.children[str(goal)] = SearchAttackerMoveGameState(
                parent=self,  to_move=ATTACKER,
                grid=grid.set_attacker_goal(goal),
                location_history=location_history2,
                rounds_left=rounds_left
            )

        self._information_set = '.' + str(attacker_budget)
        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])

    def is_terminal(self):
        return False

    def inf_set(self):
        return self._information_set




