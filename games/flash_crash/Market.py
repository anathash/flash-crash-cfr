from typing import Dict, List

from GameLogic.Asset import Asset
from GameLogic.MarketImpactCalculator import MarketImpactCalculator
from GameLogic.Orders import Buy, Sell, Order
from GameLogic.SysConfig import SysConfig


class Market:

    def __init__(self, mic:MarketImpactCalculator, timestep_seconds, timestep_order_limit, assets: Dict[str, Asset]):
        self.buy_orders_log = {}
        self.sell_orders_log = {}
        self.mic = mic
        self.timestep_order_limit = timestep_order_limit
        self.timestep_seconds = timestep_seconds
        self.minute_counter = 0
        self.minute_volume_counter = {}
        self.assets = assets
        for sym, asset in assets.items():
            self.minute_volume_counter[sym] = 0
            self.buy_orders_log[sym] = 0
            self.sell_orders_log[sym] = 0


    def submit_sell_orders(self, orders:List[Sell]):
        self.submit_orders(orders, self.sell_orders_log, Sell)

    def submit_buy_orders(self, orders: List[Buy]):
        self.submit_orders(orders, self.buy_orders_log, Buy)

    def submit_orders(self, orders: List[Order], orders_log, cls):
        for order in orders:
            if not isinstance(order, cls):
                raise TypeError()
            orders_log[order.asset_symbol] += order.num_shares

    def update_symmetric_trades(self):
        for order in self.orders:
            if order.asset_symbol in self.buy_orders_log:
                buy_order_size = self.buy_orders_log[order.asset_symbol]
                traded_shares = min(buy_order_size, order.num_shares)
                delta = buy_order_size - order.num_shares
                if delta > 0:
                    self.buy_orders_log[order.asset_symbol] -= delta
                else:
                    self.sell_orders_log[order.asset_symbol] -= delta
                self.avg_minute_volume += traded_shares

    def update_logs(self, delta, sym, buy, sell, asym_trade):
        if delta < 0:  # supply > demand
            self.buy_orders_log[sym] = 0
            self.sell_orders_log[sym] = self.sell_orders_log[sym] - buy - asym_trade
        else:
            self.buy_orders_log[sym] = self.buy_orders_log[sym] - sell - asym_trade
            self.sell_orders_log[sym] = 0

    def update_avg_minute_volume(self):
        for sym, asset in self.assets.items():
            # curr minute average is the previous minutes average + this minutes distressed trades
            asset.avg_minute_volume = (asset.avg_minute_volume * 2 + self.minute_volume_counter[sym]) / 2
            self.minute_volume_counter[sym] = 0

    def apply_actions(self):
        self.minute_counter += self.timestep_seconds
        orders = self.buy_orders_log.keys() & self.sell_orders_log.keys()

        for sym in orders:
            asset = self.assets[sym]
            buy = self.buy_orders_log[sym]
            sell = self.sell_orders_log[sym]
            sym_trade = min(buy, sell)
            self.minute_volume_counter[sym] += sym_trade
            delta = buy - sell
            abs_delta = abs(delta)
            limit = self.timestep_order_limit * asset.avg_minute_volume
            asym_trade = min(abs_delta, limit)
            self.minute_volume_counter[sym] += asym_trade
            num_shares = asym_trade if delta > 0 else -1*asym_trade
            new_price = self.mic.get_updated_price(num_shares, asset)
            asset.set_price(new_price)
            self.update_logs(delta, sym, buy, sell, asym_trade)
        if self.minute_counter == 1:
            self.update_avg_minute_volume()
            self.minute_counter = 0



    def submit_sell_orders_new(self, orders: List[Sell]):
        for order in orders:
            if order.asset_symbol in self.buy_orders_log:
                buy_order_size = self.buy_orders_log[order.asset_symbol]
                traded_shares = min(buy_order_size, order.num_shares)
                delta = buy_order_size - order.num_shares
                if delta > 0:
                    self.buy_orders_log[order.asset_symbol] -= delta
                else:
                    self.sell_orders_log[order.asset_symbol] -= delta
                self.avg_minute_volume += traded_shares
