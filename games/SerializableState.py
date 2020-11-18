import json

import jsonpickle

from bases import GameStateBase

class SerializableState(GameStateBase):

    def __init__(self, parent, to_move, actions, inf_set, children, terminal_value=None, chance_prob = None):
        self.tree_size = 1
        self.parent = parent
        self.to_move = to_move
        self.actions = actions
        self.terminal_value = terminal_value
        self.__inf_set = inf_set
        self.children = children
        self.__chance_prob = chance_prob

    def inf_set(self):
        return self.__inf_set

    def is_terminal(self):
        return not self.children

    def evaluation(self):
        if self.is_terminal() == False:
            raise RuntimeError("trying to evaluate non-terminal node")
        return self.terminal_value

    def chance_prob(self):
        return self.__chance_prob

 #   def set_value(self, value):
 #       self.value = value

#    def get_value(self):
#        return self.value



def rec_create_ser_tree(state: GameStateBase):
    if state.is_terminal():
        ser_state = SerializableState(parent=state.parent, to_move=state.to_move, actions=state.actions,
                                      children=state.children, inf_set=state.inf_set(), terminal_value=state.evaluation())
        return ser_state
    else:
        ser_children = []
        for c in state.children:
            ser_children.append(rec_serialize_tree(c))
        ser_state = SerializableState(parent=state.parent, to_move=state.to_move, actions=state.actions,
                                      children=ser_children, inf_set=state.inf_set())
        return ser_state


def create_ser_tree(state: GameStateBase):
    ser_children = []
    for c in state.children:
        ser_children.append(rec_serialize_tree(c))
    ser_state = SerializableState(parent=state.parent, to_move=state.to_move, actions=state.actions,
                                  children=ser_children, inf_set=state.inf_set(), chance_prob=state.chance_prob())
    return ser_state


def fill_ser_state(tree_size, children, to_move, actions, inf_set, terminal_value = None, chance_prob=None):
    ser_children = {}
    for k, v in children.items():
        ser_children[k] = rec_serialize_tree(v)
    state_str = {'tree_size':tree_size,
                 'to_move': to_move,
                 'actions': list(actions),
                 'children': ser_children,
                 'inf_set': inf_set,
                 'terminal_value': terminal_value,
                 'chance_prob': chance_prob}
    return state_str


def rec_serialize_tree(state):
    if state.is_terminal():
        return fill_ser_state(tree_size=state.tree_size, to_move=state.to_move, actions=state.actions,
                              children=state.children, inf_set=state.inf_set(), terminal_value=state.evaluation())
    else:
        return fill_ser_state(tree_size=state.tree_size, to_move=state.to_move, actions=state.actions,
                              children=state.children, inf_set=state.inf_set())


def save_tree_to_file(root: GameStateBase, filename):
    ser_tree = fill_ser_state(tree_size=root.tree_size, to_move=root.to_move, actions=root.actions,
                              children=root.children, inf_set=root.inf_set(),chance_prob=root.chance_prob())
    with open(filename, 'w') as fp:
        json.dump(ser_tree, fp)

def load_state_rec(class_dict, parent):
    children = {}
    state = SerializableState(parent = parent,
                             to_move = class_dict['to_move'],
                             actions = class_dict['actions'],
                             inf_set = class_dict['inf_set'],
                             children = children,
                             terminal_value=class_dict['terminal_value'],
                             chance_prob = class_dict['chance_prob'])

    if class_dict['children']:
        for k, v in class_dict['children'].items():
            state.children[k] = load_state_rec(v, state)

    return  state

def load_from_file(filename):
    with open(filename, 'r') as f:
        class_dict = json.load(f)
        return load_state_rec(class_dict, None)

