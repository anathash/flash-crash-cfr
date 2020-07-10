from constants import MARKET
from games.kunh.constants import CHANCE




class GameStateBase:
    num_nodes = 0
    @staticmethod
    def init_num_nodes():
        GameStateBase.num_nodes = 0

    def __init__(self, parent, to_move, actions):
        GameStateBase.num_nodes +=1
        print(GameStateBase.num_nodes)
        self.parent = parent
        self.to_move = to_move
        self.actions = actions
        self.value = None

    def play(self, action):
        return self.children[action]

    def is_chance(self):
        return self.to_move == CHANCE

    def is_market(self):
        return self.to_move == MARKET

    def inf_set(self):
        raise NotImplementedError("Please implement information_set method")

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value
