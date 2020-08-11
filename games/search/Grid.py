import copy
from enum import Enum


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


ATTACKER_TRANSITIONS = {(0,1):[Actions.NORTH_EAST, Actions.EAST, Actions.SOUTH_EAST],
                        (1,0):[Actions.STAY, Actions.EAST, Actions.NORTH],
                        (1,1):[Actions.STAY, Actions.EAST],
                        (1,2):[Actions.STAY, Actions.EAST, Actions.SOUTH],
                        (2,0):[Actions.STAY, Actions.EAST],
                        (2,1):[Actions.STAY, Actions.EAST],
                        (2,2):[Actions.STAY, Actions.EAST],
}

SUCCESFULL_ATTACK_PAYOFF = {(3,0):3,
                            (3,1):10,
                            (3,2):5}


class Node:
    def __init__(self, occupants = [], tracks = False, payoff = 0):
        self.occupants = occupants
        self.tracks = tracks
        self.payoff = payoff

INITIAL_GRID = {
    (0,1): Node([OCCUPANTS.ATTACKER], None, 0),
    (1,0): Node(),
    (1,1): Node([OCCUPANTS.P1]),
    (1,2): Node(),
    (2,0): Node(),
    (2,1): Node([OCCUPANTS.P2]),
    (2,2): Node(),
    (3,0): Node([], None, 3),
    (3,1): Node([], None, 5),
    (3,2): Node([], None, 10)
}


class Grid:
    def __init__(self, attacker_goal = None, matrix = INITIAL_GRID,
                 attacker_location = (0,1),
                 p1_location = (1,1),
                 p2_location = (2,1)):

        self.attacker_location = attacker_location
        self.attacker_goal = attacker_goal
        self.locations[OCCUPANTS.ATTACKER] = attacker_location
        self.locations[OCCUPANTS.P1] = p1_location
        self.locations[OCCUPANTS.P2] = p2_location
        self.matrix = matrix

    def set_attacker_goal(self, goal):
        new_grid = copy.deepcopy(self)
        new_grid.attacker_goal = goal
        return new_grid

    def apply_attacker_action(self, action):
        new_grid = copy.deepcopy(self)
        new_grid.__execute_attacker_action(action)
        return new_grid

    def apply_defender_action(self, p1_action, p2_action):
        new_grid = copy.deepcopy(self)
        new_grid.__execute_defender_action(p1_action, p2_action)
        return new_grid

    def get_attacker_actions(self):
        (x,y) = (self.attacker_location.x_loc, self.attacker_location.y_loc)
        if not (x,y) in ATTACKER_TRANSITIONS:
            return []
        return ATTACKER_TRANSITIONS[(self.attacker_location.x_loc, self.attacker_location.y_loc)]

    def get_patroller_actions(self, location):
        actions = []

        if location.y_loc < MAX_Y:  # up
            #            actions.append((self.x_loc, self.y_loc + 1))
            actions.append(Actions.NORTH)

        if location.y_loc > 0:  # down
            #           actions.append((self.x_loc, self.y_loc - 1))
            actions.append(Actions.SOUTH)

        return actions

    def get_defender_actions(self):
        p1_actions = self.p1_location.get_defender_actions()
        p_2_actions = self.p1_location.get_defender_actions()
        return list(zip(p1_actions, p_2_actions))

    @staticmethod
    def get_new_location(current_x, current_y, action):
        new_x = current_x
        new_y = current_y
        if action == Actions.EAST:
            new_x += 1
        elif action == Actions.NORTH:
            new_y = +1

        elif action == Actions.SOUTH:
            new_y = -1

        elif action == Actions.NORTH_EAST:
           new_x += 1
           new_y += 1

        elif action == Actions.SOUTH_EAST:
            new_x += 1
            new_y -= 1

        return new_x, new_y

    def execute_patroller_action(self, current_x, current_y, action, patroller_id):
        new_x, new_y = self.get_new_location(current_x,current_y, action)
        self.matrix[(current_x, current_y)].matrix.remove(patroller_id)
        self.matrix[(new_x, new_y)].occupants.append(patroller_id)

    def update_matrix(self, occupant, action, tracks = False):
        current_x = self.locations[occupant].x_loc
        current_y = self.locations[occupant].y_loc
        new_x, new_y = self.get_new_location(current_x, current_y, action)
        self.matrix[(current_x, current_y)].matrix.remove(occupant)
        self.matrix[(new_x, new_y)].occupants.append(occupant)
        self.matrix[(new_x, new_y)].tracks = tracks
        self.locations[occupant].x_loc = new_x
        self.locations[occupant].y_loc = new_y

    def attacker_caught(self):
        return self.locations[OCCUPANTS.ATTACKER] == self.locations[OCCUPANTS.P1] or \
               self.locations[OCCUPANTS.ATTACKER] == self.locations[OCCUPANTS.P2]

    def get_game_value(self):
        #defender caught attacker
        if self.locations[OCCUPANTS.ATTACKER] == self.locations[OCCUPANTS.P1]\
                or self.locations[OCCUPANTS.ATTACKER] == self.locations[OCCUPANTS.P2]:
            return 0
        # attacker reached a goal node
        if self.attacker_location == self.attacker_location[OCCUPANTS.ATTACKER]:
            x = self.attacker_location[OCCUPANTS.ATTACKER].x_loc
            y = self.attacker_location[OCCUPANTS.ATTACKER].y_loc
            return self.matrix[(x,y)].payoff

        if self.attacker_location[OCCUPANTS.ATTACKER].x_loc == MAX_X:
            return inf
        return None

    def __execute_attacker_action(self, action):
        current_x = self.attacker_location.x_loc
        current_y = self.attacker_location.y_loc
        if action == Actions.STAY:
            self.matrix[(current_x, current_y)].tracks = False
        else:
            self.update_matrix(OCCUPANTS.ATTACKER, action, True)

    def __execute_defender_action(self, p1_action, p2_action):
        self.update_matrix(OCCUPANTS.P1, p1_action)
        self.update_matrix(OCCUPANTS.P2, p2_action)








