import copy

import random
from math import inf

from constants import ATTACKER, CHANCE, DEFENDER
from games.bases import GameStateBase
from search.Grid import Grid


class SearchMainGameStateBase(GameStateBase):

    def __init__(self, parent, to_move, actions, grid:Grid, actions_history, rounds_left, terminal = False):
        super().__init__(parent=parent, to_move = to_move,actions=actions)
        self.actions_history=actions_history
        self.grid = grid
        self.children = {}
        self.rounds_left = rounds_left
        self.terminal = terminal

    def inf_set(self):
        return self._information_set

    def evaluation(self):
        if not self.is_terminal():
            raise RuntimeError("trying to evaluate non-terminal node")

        return self.grid.get_game_value()

    def is_terminal(self):
        return self.terminal


class SearchMainGameRootChanceGameState(GameStateBase):
    def __init__(self, goal_probs, grid, rounds_left):
        self._chance_prob = goal_probs
        actions = goal_probs.keys()
        super().__init__(parent=None, to_move=CHANCE, actions = [str(x) for x in actions ])
        self.children = {
            str(attacker_goal): SearchMainGameAttackerMoveGameState(
                parent=self, to_move=ATTACKER,
                grid = grid.set_attacker_goal(attacker_goal),
                actions_history={ATTACKER:['g:' + str(attacker_goal)],DEFENDER:[]},
                rounds_left = rounds_left
            ) for attacker_goal in actions
        }

        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])


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



class SearchMainGameAttackerMoveGameState(SearchMainGameStateBase):
    def __init__(self, parent,  to_move, grid,  actions_history, rounds_left):
        terminal = (rounds_left == 0 or grid.attacker_caught() or grid.attacker_reached_goal_nodes())
        if terminal:
            actions = []
        else:
            actions = grid.get_attacker_actions()

        super().__init__(parent=parent,  to_move=to_move, actions = [x.name for x in actions ],
                         grid=grid, actions_history=actions_history, rounds_left = rounds_left, terminal=terminal)
        for action in actions:
            actions_history2 = copy.deepcopy(actions_history)
            actions_history2[ATTACKER].append(action.name)
            self.children[action.name] = SearchMainGameDefenderMoveGameState(
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


class SearchMainGameDefenderMoveGameState(SearchMainGameStateBase):

    @staticmethod
    def action_str(action):
        return '(' + action[0].name + ', ' + action[1].name + ')'

    def __init__(self, parent, to_move, actions_history, grid:Grid, rounds_left):

        actions = grid.get_defender_actions()
        super().__init__(parent=parent, to_move=to_move, actions=[self.action_str(x) for x in actions],
                         grid=grid, actions_history=actions_history, rounds_left = rounds_left)
        for action in actions:
            actions_history2 = copy.deepcopy(actions_history)
            actions_history2[DEFENDER].append(self.action_str(action))
            self.children[self.action_str(action)] = SearchMainGameAttackerMoveGameState(
                parent=self,
                to_move=ATTACKER,
                grid=grid.apply_defender_action(action[0],action[1]),
                actions_history=actions_history2,
                rounds_left=rounds_left-1
            )
        self._information_set = "..{0}".format(".".join(self.actions_history[DEFENDER]))
        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])

    def is_terminal(self):
        return False
