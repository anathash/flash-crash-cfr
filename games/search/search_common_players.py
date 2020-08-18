import copy

from bases import GameStateBase
from constants import ATTACKER, DEFENDER, GRID
from search import Grid
from search.Grid import OCCUPANTS


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
        return self.grid.is_terminal()


class SearchAttackerMoveGameState(SearchGameStateBase):
    def __init__(self, parent,  to_move, grid,  actions_history, rounds_left):
        if grid.is_terminal():
            actions = []
        else:
            actions = grid.get_attacker_actions()

        super().__init__(parent=parent,  to_move=to_move, actions = [x.name for x in actions ],
                         grid=grid, actions_history=actions_history, rounds_left = rounds_left, terminal=False)
        for action in actions:
            new_grid = copy.deepcopy(grid)
            new_grid.set_attacker_action(action)
            actions_history2 = copy.deepcopy(actions_history)
            actions_history2[ATTACKER].append(action.name)
            self.children[action.name] = SearchDefenderMoveGameState(
                parent=self,
                to_move=DEFENDER,
                grid=new_grid,
                actions_history=actions_history2,
                rounds_left=rounds_left
            )

        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])
        self._information_set = ".{0}.{1}".format(".".join(self.actions_history[ATTACKER]),
                                                  str(grid.matrix[grid.locations[OCCUPANTS.ATTACKER]]))



class SearchDefenderMoveGameState(SearchGameStateBase):

    @staticmethod
    def action_str(action):
        return '(' + action[0].name + ', ' + action[1].name + ')'

    def __init__(self, parent, to_move, actions_history, grid:Grid, rounds_left):
        actions = grid.get_defender_actions()
        super().__init__(parent=parent, to_move=to_move, actions=[self.action_str(x) for x in actions],
                         grid=grid, actions_history=actions_history, rounds_left = rounds_left)
        for action in actions:
            new_grid = copy.deepcopy(grid)
            new_grid.set_defender_action(action[0],action[1])
            actions_history2 = copy.deepcopy(actions_history)
            actions_history2[DEFENDER].append(self.action_str(action))
            self.children[self.action_str(action)] = SearchGridMoveGameState(
                parent=self,
                to_move=GRID,
                grid=new_grid,
                actions_history=actions_history2,
                rounds_left=rounds_left-1
            )
        self._information_set = ".{0}.{1}.{2}".format(".".join(self.actions_history[DEFENDER]),
                                                       str(grid.matrix[grid.locations[OCCUPANTS.P1]]),
                                                       str(grid.matrix[grid.locations[OCCUPANTS.P2]]))
        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])


class SearchGridMoveGameState(SearchGameStateBase):

    def __init__(self, parent, to_move, actions_history, grid:Grid, rounds_left):
        super().__init__(parent=parent, to_move=to_move, actions=['GRID'],
                         grid=grid, actions_history=actions_history, rounds_left = rounds_left)

        actions_history2 = copy.deepcopy(actions_history)
        self.children['GRID'] = SearchAttackerMoveGameState(
            parent=self,
            to_move=ATTACKER,
            grid=grid.apply_actions(),
            actions_history=actions_history2,
            rounds_left=rounds_left-1
        )
        self._information_set = "GRID"
        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])

    def chance_prob(self):
        return 1