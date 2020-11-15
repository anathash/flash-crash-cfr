import copy
import sys
from enum import Enum
from itertools import product

####################################################
# Beging of the game:
#    0   1    2  3   4
#  0     X    X   X     5
#  1 S   X    X   X     10
#  2     X    X   X     3

##################################################
from math import inf

MAX_X = 4
MAX_Y = 2
MAX_VALUE = 0


# define Python user-defined exceptions
class AgentLocationError(Exception):
    """Base class for other exceptions"""
    pass


class OCCUPANTS(Enum):
    P1 = 1
    P2 = 2
    ATTACKER = 3


class Actions(Enum):
    STAY = 0
    NORTH = 1
    SOUTH = 2
    EAST = 3
    NORTH_EAST = 4
    SOUTH_EAST = 5


ATTACKER_TRANSITIONS = {(0, 1):[Actions.NORTH_EAST, Actions.EAST, Actions.SOUTH_EAST],
                        (1, 0): [Actions.STAY, Actions.EAST],
                        (1, 1): [Actions.STAY, Actions.EAST],
                        (1, 2): [Actions.STAY, Actions.EAST],
                        (2, 0):[Actions.STAY, Actions.EAST, Actions.NORTH],
                        (2, 1):[Actions.STAY, Actions.EAST],
                        (2, 2):[Actions.STAY, Actions.EAST, Actions.SOUTH],
                        (3, 0):[Actions.STAY, Actions.EAST],
                        (3, 1):[Actions.STAY, Actions.EAST],
                        (3, 2):[Actions.STAY, Actions.EAST]}

SUCCESFULL_ATTACK_PAYOFF = {(4, 0): 3,
                            (4, 1): 10,
                            (4, 2): 5}


class Node:
    def __init__(self, occupants, tracks = False, payoff = None):
        self.occupants = occupants
        self.tracks = tracks
        self.payoff = payoff

    def __str__(self):
        return "{0}_{1}".format(str([x.name for x in self.occupants]), str(self.tracks))

INITAL_COSTS= {(4, 0):3, (4, 1):10,(4, 2):5}

INITIAL_GRID = {
    (0,1): Node([OCCUPANTS.ATTACKER]),
    (1,0): Node([]),
    (1,1): Node([OCCUPANTS.P1]),
    (1,2): Node([]),
    (2,0): Node([]),
    (2,1): Node([]),
    (2,2): Node([]),
    (3,0): Node([]),
    (3,1): Node([OCCUPANTS.P2]),
    (3,2): Node([]),
    (4,0): Node([], False, 3),
    (4,1): Node([], False, 11),
    (4,2): Node([], False, 5)
}

class Grid:
    def __init__(self, rounds_left, attacker_goal = None, matrix = INITIAL_GRID,
                 costs = INITAL_COSTS,
                 attacker_location = (0,1),
                 p1_location = (1,1),
                 p2_location = (3,1)):

        self.attacker_goal = attacker_goal
        self.locations = dict()
        self.locations[OCCUPANTS.ATTACKER] = attacker_location
        self.locations[OCCUPANTS.P1] = p1_location
        self.locations[OCCUPANTS.P2] = p2_location
        self.matrix = matrix
        self.costs = costs
        self.rounds_left = rounds_left
        self.round_actions= dict()
        self.terminal = False

    def get_goal_costs(self):
        return self.costs

    def set_attacker_goal(self, goal):
        new_grid = copy.deepcopy(self)
        if goal[0] != MAX_X:
            raise AgentLocationError
        new_grid.attacker_goal = goal
        return new_grid

    def get_attacker_actions(self):
        if self.terminal:
            raise AgentLocationError
        (x,y) = (self.locations[OCCUPANTS.ATTACKER][0], self.locations[OCCUPANTS.ATTACKER][1])
        if not (x,y) in ATTACKER_TRANSITIONS:
            raise AgentLocationError
        return ATTACKER_TRANSITIONS[(x,y)]

    def get_patroller_actions(self, location):
        actions = []
        if self.terminal or location[0] not in [1,3]:
            raise AgentLocationError

        if location[1] < MAX_Y:  # up
            #            actions.append((self.x_loc, self.y_loc + 1))
            actions.append(Actions.NORTH)

        if location[1] > 0:  # down
            #           actions.append((self.x_loc, self.y_loc - 1))
            actions.append(Actions.SOUTH)

        return actions

    def get_defender_actions(self):
        if self.terminal:
            raise AgentLocationError

        p1_actions = self.get_patroller_actions(self.locations[OCCUPANTS.P1])
        p_2_actions = self.get_patroller_actions(self.locations[OCCUPANTS.P2])
        prod = product(p1_actions, p_2_actions)
        return list(prod)

    @staticmethod
    def get_new_location(current_x, current_y, action):
        new_x = current_x
        new_y = current_y
        if action == Actions.STAY:
            return current_x, current_y

        elif action == Actions.EAST:
            new_x += 1
        elif action == Actions.NORTH:
            new_y += 1

        elif action == Actions.SOUTH:
            new_y -= 1

        elif action == Actions.NORTH_EAST:
           new_x += 1
           new_y += 1

        elif action == Actions.SOUTH_EAST:
            new_x += 1
            new_y -= 1

        return new_x, new_y

    def attacker_caught(self):
        return self.locations[OCCUPANTS.ATTACKER] == self.locations[OCCUPANTS.P1] or \
               self.locations[OCCUPANTS.ATTACKER] == self.locations[OCCUPANTS.P2]

    def attacker_reached_goal_nodes(self):
        return self.locations[OCCUPANTS.ATTACKER][0] == MAX_X

    def attacker_reached_her_goal(self):
        return self.attacker_goal == self.locations[OCCUPANTS.ATTACKER]

    def get_game_value(self):
        #defender caught attacker
        if self.attacker_caught():
            return 0
        # attacker reached its goal node
        if self.attacker_reached_her_goal():
            x = self.locations[OCCUPANTS.ATTACKER][0]
            y = self.locations[OCCUPANTS.ATTACKER][1]
            return -1*self.matrix[(x,y)].payoff

        #reached a goal node not its own
        if self.attacker_reached_goal_nodes():
            return MAX_VALUE

        return MAX_VALUE

    def update_matrix(self, occupant, action, tracks = None):
        current_x = self.locations[occupant][0]
        current_y = self.locations[occupant][1]
        if tracks:
            self.matrix[(current_x, current_y)].tracks = tracks

        new_x, new_y = self.get_new_location(current_x, current_y, action)
        self.matrix[(current_x, current_y)].occupants.remove(occupant)
        self.matrix[(new_x, new_y)].occupants.append(occupant)
        self.locations[occupant] = (new_x, new_y)

    def __execute_attacker_action(self, action):
        tracks = not (action == Actions.STAY)
        self.update_matrix(OCCUPANTS.ATTACKER, action, tracks)

    def __execute_defender_action(self, p1_action, p2_action):
        self.update_matrix(OCCUPANTS.P1, p1_action)
        self.update_matrix(OCCUPANTS.P2, p2_action)

    def get_attacks_in_budget_dict(self, attacker_budgets, to_str=True):
        attacks_in_budget_dict = {x: [] for x in attacker_budgets}
        for goal, cost in self.costs.items():
            for budget in attacker_budgets:
                if budget >= cost:
                    if to_str:
                        attacks_in_budget_dict[budget].append(str(goal))
                    else:
                        attacks_in_budget_dict[budget].append(goal)

        return attacks_in_budget_dict

    def get_attacks_probabilities(self, attacker_budgets):
        attacks_in_budget = self.get_attacks_in_budget_dict(attacker_budgets, False)
        probs = {x:0 for x in self.costs.keys()}
        for budget, attack_list in attacks_in_budget.items():
            for attack in attack_list:
                probs[attack] += 1/(len(attacker_budgets)*len(attack_list))
        return probs

    def set_attacker_action(self, action):
        self.round_actions[OCCUPANTS.ATTACKER] = action

    def set_defender_action(self, p1_action, p2_action):
        self.round_actions[OCCUPANTS.P1] = p1_action
        self.round_actions[OCCUPANTS.P2] = p2_action

    def is_terminal(self):
        return self.rounds_left == 0 or self.attacker_caught() or self.attacker_reached_goal_nodes()

    def apply_actions(self):
        new_grid = copy.deepcopy(self)
        new_grid.__execute_defender_action(self.round_actions[OCCUPANTS.P1], self.round_actions[OCCUPANTS.P2])
        new_grid.__execute_attacker_action(self.round_actions[OCCUPANTS.ATTACKER])
        new_grid.rounds_left -= 1
        new_grid.rounds_actions = {}
        new_grid.terminal = new_grid.is_terminal()
        return new_grid

    def get_curr_locations_strs(self):
        p1_loc = self.locations[OCCUPANTS.P1]
        p2_loc = self.locations[OCCUPANTS.P2]
        defender_curr_locations = str(((p1_loc, self.matrix[p1_loc].tracks),
                                       (p2_loc, self.matrix[p2_loc].tracks)))
        attacker_curr_location = str(self   .locations[OCCUPANTS.ATTACKER])

        return defender_curr_locations, attacker_curr_location
