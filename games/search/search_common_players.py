import copy

from bases import GameStateBase
from constants import ATTACKER, DEFENDER
from search import Grid


class SearchGameStateBase(GameStateBase):

    def __init__(self, parent, to_move, actions, grid, actions_history, rounds_left, terminal=False):
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


class SearchAttackerMoveGameState(SearchGameStateBase):
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
            self.children[action.name] = SearchDefenderMoveGameState(
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


class SearchDefenderMoveGameState(SearchGameStateBase):

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
            self.children[self.action_str(action)] = SearchAttackerMoveGameState(
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
