from typing import List

from GameLogic import Market
from GameLogic.Orders import Move, Order
from GameLogic.AssetFundNetwork import AssetFundsNetwork
from GameLogic.Players import Defender, Attacker


class GameState:
    def __init__(self, network: AssetFundsNetwork, players, market: Market):
        self.players = players
        self.network = network
        self.market = market
        self.liquidators = []
        self.turn = 0

    def current_player(self):
        return self.players[self.turn]

    def move_turn(self):
        self.turn = (self.turn + 1) % len(self.players)

    def game_reward(self):
        raise NotImplementedError

    def game_ended(self):
        raise NotImplementedError

    def get_valid_actions(self):
        raise NotImplementedError

    def apply_action(self, action: Move):
        raise NotImplementedError

    def gen_random_action(self):
        raise NotImplementedError

    def print_winner(self):
        if self.attacker.is_goal_achieved(self.network.funds):
            print('Attacker Won!')
            return
        if self.attacker.resources_exhusted():
            print('Defender Won!')
            return
        print('No One Won!')

    def get_winner(self):
        if self.attacker.is_goal_achieved(self.network.funds):
            return self.attacker
        if self.attacker.resources_exhusted():
            return self.defender
        return None

    def GetResult(self, playerjm):
        return playerjm.game_reward(self.network.funds)

    def __repr__(self):
        ret = 'Players: /n'
        for player in self.players:
            ret += str(player) + '/n'
        ret = 'Network: /n'
        ret += str(self.network) + '/n'
        return ret


class TwoPlayersSimultaneousGameState(GameState):
    def __init__(self, network, attacker, defender):
        self.defender = defender
        self.attacker = attacker
        super().__init__(network, [self.attacker, self.defender])

    def game_reward(self):
        return self.defender.game_reward(self.network.funds)

    def game_ended(self):
        return self.attacker.is_goal_achieved(self.network.funds) or self.attacker.resources_exhusted()

    def get_valid_actions(self):
        return self.players[self.turn].get_valid_actions(self.network.assets)

    def gen_random_action(self):
        return self.players[self.turn].gen_random_action(self.network.assets)

    def apply_action(self, action: List[Order]):
        self.players[self.turn].apply_action(action)
        for liquidator in self.liquidators:
            self.market.submit_sell_orders(liquidator.get_orders(self.network.assets))
        self.market.apply_actions()
        self.liquidators.append(self.network.get_liquidaton_orders(action))
        self.move_turn()


class TwoPlayersGameState(GameState):

    def __init__(self, network, attacker, defender):
        self.defender = defender
        self.attacker = attacker
        super().__init__(network, [self.attacker, self.defender])

    def game_reward(self):
        return self.defender.game_reward(self.network.funds)

    def game_ended(self):
        return self.attacker.is_goal_achieved(self.network.funds) or self.attacker.resources_exhusted()

    def get_valid_actions(self):
        return self.players[self.turn].get_valid_actions(self.network.assets)

    def gen_random_action(self):
        return self.players[self.turn].gen_random_action(self.network.assets)

    def apply_action(self, action: Move):
        self.players[self.turn].apply_action(action)
        for liquidator in self.liquidators:
            self.market.submit_sell_orders(liquidator.get_orders(self.network.assets))
        self.market.apply_actions()
        self.liquidators.append(self.network.get_liquidaton_orders(action))
        self.move_turn()


class SinglePlayerGameState(GameState):
    def __init__(self, network, attacker_initial_portfolio, attacker_goals, attacker_asset_slicing,
                 max_assets_in_action):
        self.attacker = Attacker(attacker_initial_portfolio, attacker_goals, attacker_asset_slicing,
                                 max_assets_in_action)
        super().__init__(network, [self.attacker])

    def game_reward(self):
        return self.attacker.game_reward(self.network)

    def game_ended(self):
        return self.attacker.is_goal_achieved(self.network.funds)

    def get_valid_actions(self):
        return self.attacker.get_valid_actions(self.network.assets)

    def gen_random_action(self):
        return self.attacker.gen_random_action(self.network.assets)

    def apply_action(self, action: Move):
        self.attacker.apply_action(action)
        self.network.apply_action(action)
