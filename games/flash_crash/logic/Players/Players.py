from typing import List, Dict
from GameLogic.Orders import  Move, Order
from GameLogic.AssetFundNetwork import Asset, Fund


class Player:
    def __init__(self, initial_capital, initial_portfolio: Dict[str, int], asset_slicing: int,
                 max_assets_in_action: int):
        self.initial_capital = initial_capital
        self.portfolio = initial_portfolio
        self.max_assets_in_action = max_assets_in_action
        self.asset_slicing = asset_slicing

    def apply_action(self, orders: Move):
        for order in orders:
            self.apply_order(order)

    def get_valid_actions(self, assets: Dict[str, Asset]):
        raise NotImplementedError


    def gen_random_action(self, assets: Dict[str, Asset]):
        raise NotImplementedError

    def is_legal(self, orders: List[Order]):
        return True

    def resources_exhusted(self):
        raise NotImplementedError()

    def apply_order(self, order: Move):
        raise NotImplementedError

    def game_reward(self, funds: Dict[str, Fund],  history=None):
        raise NotImplementedError
"""    def get_valid_actions(self, assets: Dict[str, Asset] = None):
        actions = []
        orders_lists = self.gen_orders(assets)
        selected_assets_comb = itertools.combinations(orders_lists, self.max_assets_in_action)
        for comb in selected_assets_comb:
            orders = list(itertools.product(tuple(comb)))
            if self.is_legal(orders):
                actions.append(Action(orders))
"""




"""

    def gen_orders(self, assets: Dict[str, Asset] = None):
        orders_lists = []
        for sym, asset in assets.items():
            buy_percent = self.buy_share_portion_jump
            capital_needed = buy_percent * asset.price * asset.daily_volume
            orders = []
            while buy_percent <= 1 and capital_needed <= self.capital:
                orders.append(Buy(sym, int(buy_percent * asset.daily_volume), asset.price))
                buy_percent += self.buy_share_portion_jump
                capital_needed = buy_percent * asset.price * asset.daily_volume
            if orders:
                orders_lists.append(orders)
        return orders_lists

   def gen_orders(self, assets: Dict[str, Asset]):
        orders_lists = []
        'TODO: make sure we dont get to ver small numbers'
        for asset_symbol, num_shares in self.portfolio.items():
            orders = []
            sell_percent = self.sell_share_portion_jump
            while sell_percent <= 1:
                orders.append(Sell(asset_symbol, int(sell_percent * num_shares), assets[asset_symbol].price))
                sell_percent += self.sell_share_portion_jump
            if orders:
                orders_lists.append(orders)
        return orders_lists
        
    def gen_orders_rec(self, money_left, assets: List[Asset]):
        if not assets:
            return []
        orders_list = []
        asset = assets[0]
        buy_percent = self.buy_share_portion_jump
        capital_jump = self.buy_share_portion_jump * asset.price * asset.daily_volume
        capital_needed = capital_jump
        'orders without current asset'
        if len(assets) > 1:
            orders_list.extend(self.gen_orders_rec(money_left, assets[1:]))
        while buy_percent <= 1 and capital_needed <= money_left:
            shares_to_buy = int(buy_percent * asset.daily_volume)
            order = Buy(asset.symbol, shares_to_buy, asset.price)
            orders_list.append([order])
            'orders that include current asset'
            orders_to_add = self.gen_orders_rec(money_left - capital_needed, assets[1:])
            for orders in orders_to_add:
                if len(orders) < self.max_assets_in_action:
                    orders.append(order)
            if orders_to_add:
                orders_list.extend(orders_to_add)
            buy_percent += self.buy_share_portion_jump
            capital_needed += capital_jump
        return orders_list
        
        
    def gen_orders_rec(self, money_left, assets: List[Asset]):
        if not assets:
            return []
        orders_list = []
        asset = assets[0]
        buy_percent = self.buy_share_portion_jump
        capital_jump = self.buy_share_portion_jump * asset.price * asset.daily_volume
        capital_needed = capital_jump
        'orders without current asset'
        if len(assets) > 1:
            orders_list.extend(self.gen_orders_rec(money_left, assets[1:]))
        while buy_percent <= 1 and capital_needed <= money_left:
            shares_to_buy = int(buy_percent * asset.daily_volume)
            order = Buy(asset.symbol, shares_to_buy, asset.price)
            orders_list.append(([order], capital_needed))
            orders_to_add = self.gen_orders_rec(money_left - capital_needed, assets[1:])
            for tup in orders_to_add:
                orders = tup[0]
                orders_capital = tup[1]
                total_capital = capital_needed + orders_capital
                if len(orders) < self.max_assets_in_action and total_capital <= self.capital:
                    orders.append(order)
                    orders_list.append((new_orders, total_capital))
            buy_percent += self.buy_share_portion_jump
            capital_needed += capital_jump
        return orders_list

"""

