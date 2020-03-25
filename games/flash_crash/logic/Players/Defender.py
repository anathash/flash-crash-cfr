import random
from math import floor
from typing import List, Dict

from GameLogic.Players.Players import Player
from GameLogic.SysConfig import SysConfig
from GameLogic.Orders import  Order, Buy
from GameLogic.AssetFundNetwork import Asset, Fund

class Defender(Player):
    def __init__(self, initial_capital, asset_slicing, max_assets_in_action):
        super().__init__(initial_capital, {}, asset_slicing, max_assets_in_action)
        self.resources_exhusted_flag = False

    ' think: should we allow selling of assets when capital is zero?'
    def resources_exhusted(self):
        'allow overdraft?'
        if self.initial_capital <= 0:
            self.resources_exhusted_flag = True

        return self.resources_exhusted_flag

        'TODO: make sure we dont get to very small numbers'

    def apply_order(self, order: Buy):
        if not isinstance(order, Buy):
            raise ValueError("attacker only buys")
        self.initial_capital -= order.share_price * order.num_shares
        num_shares = self.portfolio[order.asset_symbol] if order.asset_symbol in self.portfolio else 0
        num_shares += order.num_shares
        self.portfolio[order.asset_symbol] = num_shares

    def game_reward(self, funds: Dict[str, Fund], history=None):
        raise NotImplementedError

    def is_legal(self, orders: List[Order]):
        capital_needed = 0
        for order in orders:
            capital_needed += order.share_price * order.num_shares
            if capital_needed > self.initial_capital:
                return True
        return False

    def get_valid_actions(self, assets: Dict[str, Asset] = None):
        if self.max_assets_in_action > 1:
            orders_list_tup = self.gen_orders_rec(list(assets.values()))
            orders_list = [x[0] for x in orders_list_tup]
        else:
            orders_list = self.gen_single_asset_orders(list(assets.values()))
        if not orders_list:
            self.resources_exhusted_flag = True
            return []
        return orders_list

    def gen_random_action(self, assets: Dict[str, Asset] = None):
        orders = []
        num_assets = random.randint(1, self.max_assets_in_action)
        chosen_assets = random.sample(list(assets.values()), num_assets)
        action_required_capital = 0
        while not orders: #in case no valid orders for the entire iteration
            i = 0
            while i < num_assets and action_required_capital < self.initial_capital:
                asset = chosen_assets[i]
                portion = random.randint(1, self.asset_slicing)
                order_required_capital = portion * asset.price * asset.daily_volume/ self.asset_slicing
                if order_required_capital + action_required_capital > self.initial_capital:
                    portion = int(floor((self.initial_capital * self.asset_slicing) / (asset.price * asset.daily_volume)))
                order = Buy(asset.symbol, portion*chosen_assets[i].daily_volume/self.asset_slicing, asset.price)
                action_required_capital += order_required_capital
                orders.append(order)
                i += 1
        return orders

    def gen_single_asset_orders(self, assets: List[Asset]):
        orders_list = []
        for asset in assets:
            buy_slice = 1
            capital_jump = asset.price * asset.daily_volume / self.asset_slicing
            capital_needed = capital_jump
            while buy_slice <= self.asset_slicing and capital_needed <= self.initial_capital:
                shares_to_buy = int(asset.daily_volume * buy_slice / self.asset_slicing)
                if asset.price * shares_to_buy < SysConfig.get(SysConfig.MIN_ORDER_VALUE):  # ignore small orders
                    buy_slice += 1
                    continue
                order = Buy(asset.symbol, shares_to_buy, asset.price)
                orders_list.append([order])
                buy_slice += 1
                capital_needed += capital_jump
        return orders_list

    def gen_orders_rec(self, assets: List[Asset]):
        if not assets:
            return []
        orders_list = []
        asset = assets[0]
        buy_slice = 1
        orders_to_add = self.gen_orders_rec(assets[1:])
        orders_list.extend(orders_to_add)
        capital_jump = asset.price * asset.daily_volume / self.asset_slicing
        capital_needed = capital_jump
        while buy_slice <= self.asset_slicing and capital_needed <= self.initial_capital:
            shares_to_buy = int(asset.daily_volume * buy_slice / self.asset_slicing)
            if asset.price * shares_to_buy < SysConfig.get(SysConfig.MIN_ORDER_VALUE):  # ignore small orders
                buy_slice += 1
                continue
            order = Buy(asset.symbol, shares_to_buy, asset.price)
            orders_list.append(([order], capital_needed))
            for tup in orders_to_add:
                orders = tup[0]
                orders_capital = tup[1]
                total_capital = capital_needed + orders_capital
                if len(orders) < self.max_assets_in_action and total_capital <= self.initial_capital:
                    order_including_asset = list(orders)
                    order_including_asset.append(order)
                    orders_list.append((order_including_asset, total_capital))
            buy_slice += 1
            capital_needed += capital_jump
        return orders_list

    def gen_orders_rec_old(self, assets: List[Asset]):
        if not assets:
            return []
        orders_list = []
        asset = assets[0]
        buy_percent = self.buy_share_portion_jump
        orders_to_add = self.gen_orders_rec(assets[1:])
        orders_list.extend(orders_to_add)
        capital_jump = self.buy_share_portion_jump * asset.price * asset.daily_volume
        capital_needed = capital_jump
        while buy_percent <= 1 and capital_needed <= self.initial_capital:
            shares_to_buy = int(buy_percent * asset.daily_volume)
            order = Buy(asset.symbol, shares_to_buy, asset.price)
            orders_list.append(([order], capital_needed))
            for tup in orders_to_add:
                orders = tup[0]
                orders_capital = tup[1]
                total_capital = capital_needed + orders_capital
                if len(orders) < self.max_assets_in_action and total_capital <= self.initial_capital:
                    order_including_asset = list(orders)
                    order_including_asset.append(order)
                    orders_list.append((order_including_asset, total_capital))
            buy_percent += self.buy_share_portion_jump
            capital_needed += capital_jump
        return orders_list


class RobustDefender(Defender):
    def game_reward(self, funds: Dict[str, Fund],  history=None):
        reward = 0
        for fund in funds.values():
            if fund.is_in_margin_call():
                reward -= 1
        return reward

    def __repr__(self):
        return 'Robust Defender'


class OracleDefender(Defender):
    def __init__(self, initial_capital, asset_slicing, max_assets_in_action, goals):
        super().__init__(initial_capital, asset_slicing, max_assets_in_action)
        self.goals = goals

    def game_reward(self, funds: Dict[str, Fund],  history=None):
        for fund in self.goals:
            if not funds[fund].is_in_margin_call():
                return 1
        return -1

    def __repr__(self):
        return 'Oracle Defender'

class NNDefender(Defender):
    def __init__(self, initial_capital, asset_slicing, max_assets_in_action, neural_network):
        super().__init__(initial_capital, asset_slicing, max_assets_in_action)
        self.neural_network = neural_network

    def game_reward(self, funds: Dict[str, Fund], history):
        reward = 0
        for fund in funds:
            if funds[fund].is_liquidated():
                reward -= self.neural_network.predict(fund.symbol, history)
        return reward
