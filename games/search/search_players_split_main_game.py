import copy

import random
from math import inf

from constants import ATTACKER, CHANCE, DEFENDER
from games.bases import GameStateBase
from search.search_common_players import SearchGameStateBase, SearchAttackerMoveGameState


class SearchMainGameRootChanceGameState(GameStateBase):
    def __init__(self, goal_probs, grid, rounds_left):
        self._chance_prob = {str(x):y for x,y in goal_probs.items()}
        actions = [x for x in goal_probs.keys() if goal_probs[x] > 0]
        super().__init__(parent=None, to_move=CHANCE, actions = [str(x) for x in actions ])
        defender_curr_locations, attacker_curr_location = grid.get_curr_locations_strs()
        self.children = {
            str(attacker_goal): SearchAttackerMoveGameState(
                parent=self, to_move=ATTACKER,
                grid = grid.set_attacker_goal(attacker_goal),
                location_history={ATTACKER: ['g:' + str(attacker_goal), attacker_curr_location],
                                  DEFENDER: [defender_curr_locations]},
                rounds_left = rounds_left
            ) for attacker_goal in actions
        }

        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])

    def update_chance_probs(self, new_probs):
        self._chance_prob = {str(x):y for x,y in new_probs.items()}

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
