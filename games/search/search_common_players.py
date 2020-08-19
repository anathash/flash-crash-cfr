import copy

from bases import GameStateBase
from constants import ATTACKER, DEFENDER, GRID
from search import Grid
from search.Grid import OCCUPANTS, AgentLocationError





class SearchGameStateBase(GameStateBase):

    def __init__(self, parent, to_move, actions, grid, location_history, rounds_left, terminal=False):
        super().__init__(parent=parent, to_move = to_move,actions=actions)
        self.location_history=location_history
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
    def __init__(self, parent,  to_move, grid,  location_history, rounds_left):
        if grid.is_terminal():
            actions = {}
            terminal = True
        else:
            actions = grid.get_attacker_actions()
            terminal = False

        super().__init__(parent=parent,  to_move=to_move, actions = [x.name for x in actions ],
                         grid=grid, location_history=location_history, rounds_left = rounds_left, terminal = terminal)

    #    curr_location = str(grid.locations[OCCUPANTS.ATTACKER])
        for action in actions:
          #  location_history2 = copy.deepcopy(location_history)
          #  location_history2[ATTACKER].append(curr_location)
            new_grid = copy.deepcopy(grid)
            new_grid.set_attacker_action(action)
            self.children[action.name] = SearchDefenderMoveGameState(
                parent=self,
                to_move=DEFENDER,
                grid=new_grid,
                location_history= copy.deepcopy(location_history),
                rounds_left=rounds_left
            )

        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])
        self._information_set = ".{0}.{1}".format(".".join(self.location_history[ATTACKER]), grid.attacker_caught())


class SearchDefenderMoveGameState(SearchGameStateBase):

    @staticmethod
    def action_str(action):
        return '(' + action[0].name + ', ' + action[1].name + ')'

    def __init__(self, parent, to_move, location_history, grid:Grid, rounds_left):
        if grid.is_terminal():
            raise AgentLocationError

        actions = grid.get_defender_actions()
        super().__init__(parent=parent, to_move=to_move, actions=[self.action_str(x) for x in actions],
                         grid=grid, location_history=location_history, rounds_left=rounds_left)

        for action in actions:
            new_grid = copy.deepcopy(grid)
            new_grid.set_defender_action(action[0],action[1])
            self.children[self.action_str(action)] = SearchGridMoveGameState(
                parent=self,
                to_move=GRID,
                grid=new_grid,
                location_history=copy.deepcopy(location_history),
                rounds_left=rounds_left
            )
        self._information_set = ".{0}".format(".".join(self.location_history[DEFENDER]))
        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])


class SearchGridMoveGameState(SearchGameStateBase):

    def __init__(self, parent, to_move, location_history, grid:Grid, rounds_left):
        super().__init__(parent=parent, to_move=to_move, actions=['GRID'],
                         grid=grid, location_history=location_history, rounds_left = rounds_left)

        new_grid = grid.apply_actions()
        defender_curr_locations, attacker_curr_location = new_grid.get_curr_locations_strs()
        location_history2 = copy.deepcopy(location_history)
        location_history2[DEFENDER].append(str(defender_curr_locations))
        location_history2[ATTACKER].append(str(attacker_curr_location))

        self.children['GRID'] = SearchAttackerMoveGameState(
            parent=self,
            to_move=ATTACKER,
            grid=new_grid,
            location_history=location_history2,
            rounds_left=rounds_left-1
        )
        self._information_set = "GRID"
        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])

    def chance_prob(self):
        return 1
