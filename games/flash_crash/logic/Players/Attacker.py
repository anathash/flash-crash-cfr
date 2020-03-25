import random
from typing import List, Dict

from GameLogic.Players.Players import Player
from GameLogic.SysConfig import SysConfig
from GameLogic.Orders import Sell
from GameLogic.AssetFundNetwork import Asset, Fund


class Attacker(Player):
    def __init__(self, initial_portfolio: Dict[str, int], goals: List[str], asset_slicing, max_assets_in_action):
        super().__init__(0, initial_portfolio, asset_slicing, max_assets_in_action)
        self.goals = goals
        self.resources_exhusted_flag = False

    def resources_exhusted(self):
        if not self.portfolio:
            self.resources_exhusted_flag = True
        return self.resources_exhusted_flag

    def is_goal_achieved(self, funds: Dict[str, Fund]):
        for fund_symbol in self.goals:
            if not funds[fund_symbol].is_in_margin_call():
                return False
        return True

    def apply_order(self, order: Sell):
        if not isinstance(order, Sell):
            raise ValueError("attacker only sells")

        self.initial_capital += order.share_price * order.num_shares
        num_shares = self.portfolio[order.asset_symbol]
        num_shares -= order.num_shares
        if num_shares == 0:
            del self.portfolio[order.asset_symbol]
        else:
            self.portfolio[order.asset_symbol] = num_shares

    def game_reward(self, funds: List[Fund], history=None):
        for fund in self.goals:
            if not funds[fund].is_in_margin_call():
                return -1
        return 1

    def get_valid_actions(self, assets: Dict[str, Asset]):
        assets_list = [assets[x] for x in self.portfolio.keys()]
        if self.max_assets_in_action > 1:
            orders = self.gen_orders_rec(assets_list)
        else:
            orders = self.gen_single_asset_orders(assets_list)
        if not orders:
            self.resources_exhusted_flag = True
        return orders

    def gen_single_asset_orders(self, assets: List[Asset]):
        if not assets:
            return []
        orders_list = []
        for asset in assets:
            for i in range(1, self.asset_slicing + 1):
                shares_to_sell = int(i * self.portfolio[asset.symbol] / self.asset_slicing)
                if asset.price * shares_to_sell < SysConfig.get(SysConfig.MIN_ORDER_VALUE): #ignore small orders
                    continue
                order = Sell(asset.symbol, shares_to_sell, asset.price)
                orders_list.append([order])
        return orders_list


    def gen_orders_rec(self, assets: List[Asset]):
        if not assets:
            return []
        orders_list = []
        asset = assets[0]
        orders_to_add = self.gen_orders_rec(assets[1:])
        orders_list.extend(orders_to_add)
        for i in range(1, self.asset_slicing + 1):
            shares_to_sell = int(i * self.portfolio[asset.symbol] / self.asset_slicing)
            if asset.price * shares_to_sell < SysConfig.get(SysConfig.MIN_ORDER_VALUE): #ignore small orders
                continue
            order = Sell(asset.symbol, shares_to_sell, asset.price)
            orders_list.append([order])
            for orders in orders_to_add:
                if len(orders) < self.max_assets_in_action:
                    order_including_asset = list(orders)
                    order_including_asset.append(order)
                    orders_list.append(order_including_asset)
        return orders_list

    def gen_orders_rec_old(self, assets: List[Asset]):
        if not assets:
            return []
        orders_list = []
        asset = assets[0]
        sell_percent = self.sell_share_portion_jump
        orders_to_add = self.gen_orders_rec(assets[1:])
        orders_list.extend(orders_to_add)
        while sell_percent <= 1:
            shares_to_sell = int(sell_percent * self.portfolio[asset.symbol])
            order = Sell(asset.symbol, shares_to_sell, asset.price)
            orders_list.append([order])
            for orders in orders_to_add:
                if len(orders) < self.max_assets_in_action:
                    order_including_asset = list(orders)
                    order_including_asset.append(order)
                    orders_list.append(order_including_asset)
            sell_percent += self.sell_share_portion_jump
        return orders_list

    def gen_random_action(self, assets: Dict[str, Asset] = None):
        orders = []
        portfolio_assets = list(self.portfolio.keys())
        num_assets = min(len(portfolio_assets), random.randint(1, self.max_assets_in_action))
        chosen_assets = random.sample(portfolio_assets, num_assets)

        for sym in chosen_assets:
            asset = assets[sym]
            portion = random.randint(1, self.asset_slicing)
            shares_to_sell = int(portion * self.portfolio[asset.symbol] / self.asset_slicing)
            order = Sell(asset.symbol, shares_to_sell, asset.price)
            orders.append(order)

        return orders

    def __str__(self):
        return 'Attacker'
