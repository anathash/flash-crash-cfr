from copy import deepcopy

from GameLogic import AssetFundNetwork
from GameLogic.GameState import GameState
from GameLogic.Players import Attacker, Defender


class SimultaneousGame:
    def __init__(self, init_state: GameState, network: AssetFundNetwork, attacker: Attacker, defender: Defender):
        self.state = init_state
        self.network = network
        self.attacker = attacker
        self.defender = defender

    def game_reward(self):
        return self.defender.game_reward(self.network.funds)

    def game_ended(self):
        return self.attacker.is_goal_achieved(self.network.funds) or self.attacker.resources_exhusted()

    def get_valid_actions(self):
        return self.state.get_valid_actions()

    def apply_actions(self, attacker_orders, defender_orders, fund_orders):
        self.market.submit_sell_orders(attacker_orders)
        self.market.submit_buy_orders(defender_orders)
        self.market.submit_sell_orders(fund_orders)
        self.market.apply_actions()
        self.network.apply_actions()

    def play_single_game(self):
        state = GameState.TwoPlayersSimultaneousGameState(self.network, self.attacker, self.defender)
        if self.config.verbose:
            self.print_portfolios(state.network, self.attacker)
        moves_counter = 0
        #first move by attacker only
        attacker_orders = self.attacker.get_action(state)
        self.apply_actions(attacker_orders, [], [])
        while not state.game_ended():
            attacker_orders = self.attacker.get_action()
            defender_orders = self.defender.get_action()
            liquidation_orders = self.network.get_liquidation_orders()
            self.apply_actions(attacker_orders, defender_orders, liquidation_orders)

        if state.game_ended():
            self.stats.update_stats(state.get_winner(), moves_counter)
