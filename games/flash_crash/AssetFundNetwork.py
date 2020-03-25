#!/usr/bin/python
import json
import random
from math import floor

import networkx as nx
import numpy


from typing import Dict, List
import jsonpickle

import MarketImpactCalculator
from Orders import NoLimitOrder, Sell, Buy
from SysConfig import SysConfig
from constants import MS_IN_MINUTE

'TODO: do we need the total market cap of assets or do funds hold the entire market'


class Asset:
    def __init__(self, price, daily_volume, symbol, volatility = 0):
        self.price = price
        self.daily_volume = daily_volume
        self.avg_minute_volume = daily_volume/(60*6.5)
        self.symbol = symbol
        self.volatility = volatility

    def set_price(self, new_price):
        self.price = new_price

    def __eq__(self, other):
        return isinstance(other, Asset) and self.price == other.price and self.daily_volume == other.daily_volume \
               and self.volatility == other.volatility and self.symbol == other.symbol


class Fund:
    def __init__(self, symbol, portfolio: Dict[str, int], initial_capital, initial_leverage, tolerance):
        self.symbol = symbol
        self.portfolio = portfolio
        self.initial_leverage = initial_leverage
        self.initial_capital = initial_capital
        self.loan = initial_capital*initial_leverage
        self.tolerance = tolerance
        self.is_liquidating = False
        self.is_in_default = False

    def __eq__(self, other):
        return isinstance(other, Fund) and \
               self.symbol == other.symbol and \
               self.portfolio == other.portfolio and \
               self.initial_leverage == other.initial_leverage and \
               self.initial_capital == other.initial_capital and \
               self.tolerance == other.tolerance and \
               self.loan == other.loan

    def update_state(self, assets):
        curr_leverage = self.compute_curr_leverage(assets)
        if curr_leverage == numpy.inf:
            self.is_in_default = True
            self.is_liquidating = True
        else:
            if curr_leverage / self.initial_leverage > self.tolerance:
                self.is_liquidating = True

    def gen_liquidation_orders(self, assets: Dict[str, Asset]):
        orders = []
        assets_to_remove = []
        for asset_symbol, num_shares in self.portfolio.items():
            asset = assets[asset_symbol]
            shares_limit = floor(asset.avg_minute_volume * SysConfig.get("MINUTE_VOLUME_LIMIT"))
            shares_to_sell = min(shares_limit, num_shares)
            orders.append(Sell(asset_symbol, shares_to_sell))
            self.portfolio[asset_symbol] -= shares_to_sell
            if self.portfolio[asset_symbol] == 0:
                assets_to_remove.append(asset_symbol)
        for asset_symbol in assets_to_remove:
            self.portfolio.pop(asset_symbol)
        return orders

  #  def get_orders(self, assets: Dict[str, Asset]):
    def get_orders(self, assets):
        if self.is_liquidating:
            return self.gen_liquidation_orders(assets)
        return []

    def liquidate(self):
        self.is_liquidating = True

    def is_in_margin_call(self):
        return self.is_liquidating

    def default(self):
        return self.is_in_default

    def compute_curr_capital(self, assets):
        return self.compute_portfolio_value(assets) - self.loan

    def compute_portfolio_value(self, assets):
        v = 0
        for asset_symbol, num_shares in self.portfolio.items():
            v += num_shares * assets[asset_symbol].price
        return v

    """ leverage = curr_portfolio_value / curr_capital -1
       = curr_portfolio_value/(curr_portfolio_value - loan) -1
    """

    def compute_curr_leverage(self, assets):
        curr_portfolio_value = self.compute_portfolio_value(assets)
        curr_capital = curr_portfolio_value - self.loan
        if curr_capital <= 0:
            return numpy.inf
        return curr_portfolio_value / curr_capital - 1 #return self.compute_portfolio_value(assets) / self.capital - 1

    def marginal_call(self, assets):
        return self.compute_curr_leverage(assets) / self.initial_leverage > self.tolerance


class AssetFundsNetwork:
    assets: Dict[str, Asset]

    def __init__(self, funds: Dict[str, Fund], assets: Dict[str, Asset], mi_calc: MarketImpactCalculator, intraday_asset_gain_max_range =None):
        self.mi_calc = mi_calc
        self.funds = funds
        self.assets = assets
        self.buy_orders = {}
        self.sell_orders = {}
        if intraday_asset_gain_max_range:
            self.run_intraday_simulation(intraday_asset_gain_max_range, 0.7)

    def __eq__(self, other):
        return isinstance(other, AssetFundsNetwork) and isinstance(other.mi_calc, type(self.mi_calc)) and \
               self.funds == other.funds and self.assets == other.assets

    def __repr__(self):
        return str(self.funds)

    @staticmethod
    def submit_orders(orders, book):
        for order in orders:
            old_num_shares = book[order.asset_symbol] if order.asset_symbol in book else 0
            book[order.asset_symbol] = old_num_shares + order.num_shares

    def submit_buy_orders(self, orders):
        for order in orders:
            if not isinstance(order, Buy):
                raise TypeError('orders must be buy orders')

        self.submit_orders(orders, self.buy_orders)

    def submit_sell_orders(self, orders):
        for order in orders:
            if not isinstance(order, Sell):
                raise TypeError('orders must be sell orders')

        self.submit_orders(orders, self.sell_orders)

    def clear_order_book(self):
        self.simulate_trade(False)

    def simulate_trade(self, limit_trade_step = True):
        order_keys = set(self.sell_orders.keys())
        order_keys.update(self.buy_orders.keys())
        for order_key in order_keys:
            buy = self.buy_orders[order_key] if order_key in self.buy_orders else 0
            sell = self.sell_orders[order_key] if order_key in self.sell_orders else 0
            balance = buy - sell
            if balance == 0:
                del self.buy_orders[order_key]
                del self.sell_orders[order_key]
                continue
            if limit_trade_step:
                time_step = SysConfig.get('TIME_STEP_MS')
                max_shares_to_trade = (self.assets[order_key].avg_minute_volume / MS_IN_MINUTE) * time_step
                shares_to_trade = min(abs(balance), max_shares_to_trade)
            else:
                shares_to_trade = abs(balance)

            if balance < 0: #sell > buy
                self.sell_orders[order_key] -= (shares_to_trade + buy)
                if self.sell_orders[order_key] == 0:
                    del self.sell_orders[order_key]
                if buy > 0:
                    del self.buy_orders[order_key]
                sign = -1
            else:
                self.buy_orders[order_key] -= (shares_to_trade + sell)
                if self.buy_orders[order_key] == 0:
                    del self.buy_orders[order_key]
                if sell > 0:
                    del self.sell_orders[order_key]
                sign = 1
            updated_price  = self.mi_calc.get_updated_price(shares_to_trade, self.assets[order_key], sign)
            self.assets[order_key].price = updated_price


    def are_funds_leveraged_less_than(self, leverage_goal):
        for fund in self.funds.values():
            if leverage_goal < fund.compute_curr_leverage(self.assets):
                return False
        return True

    def run_intraday_simulation_2(self, intraday_asset_gain_max_range):
        if (intraday_asset_gain_max_range < 1):
            raise ValueError
        for asset in self.assets.values():
            price_gain = random.uniform(1, intraday_asset_gain_max_range)
            asset.set_price(asset.price * price_gain)

    def run_intraday_simulation(self, intraday_asset_gain_max_range, leverage_goal):
        if intraday_asset_gain_max_range < 1:
            raise ValueError
        while not self.are_funds_leveraged_less_than(leverage_goal):
            for asset in self.assets.values():
                price_gain = random.uniform(1, intraday_asset_gain_max_range)
                asset.set_price(asset.price * price_gain)

    @classmethod
    def generate_random_network(cls, density, num_funds, num_assets, initial_capitals, initial_leverages,
                                assets_initial_prices, tolerances, assets_num_shares, volatility, mi_calc: MarketImpactCalculator):
        connected = False
        while not connected:
            g = nx.algorithms.bipartite.random_graph(num_funds, num_assets, density, directed=True)
            connected = True
            try:
                fund_nodes, asset_nodes = nx.bipartite.sets(g)
            except nx.AmbiguousSolution:
                connected = False

        investment_proportions = {}
        for fund_node in list(fund_nodes):
            fund_symbol = 'f' + str(fund_node)
            investments = list(g.out_edges(fund_node))
            rand = list(numpy.random.randint(1, 10, size=len(investments)))
            rand_sum = sum(rand)
            investment_proportions[fund_symbol] = [float(i) / rand_sum for i in rand]

        return cls.gen_network_from_graph(g, investment_proportions, initial_capitals,
                                          initial_leverages, assets_initial_prices,
                                          tolerances, assets_num_shares, volatility, mi_calc)

    @classmethod
    def gen_network_from_graph(cls, g, investment_proportions,
                               initial_capitals, initial_leverages, assets_initial_prices,
                               tolerances, daily_volumes, volatility, mi_calc: MarketImpactCalculator):
        funds = {}
        assets = {}
        fund_nodes, asset_nodes = nx.bipartite.sets(g)
        num_funds = len(fund_nodes)
        for i in range(len(asset_nodes)):
            symbol = 'a' + str(i)
            assets[symbol] = Asset(price=assets_initial_prices[i], daily_volume=daily_volumes[i], symbol=symbol,
                                   volatility = volatility[i])
        for i in range(num_funds):
            portfolio = {}
            fund_symbol = 'f' + str(i)
            investments = list(g.out_edges(i))
            if investments:
                fund_capital = initial_capitals[i] * (1 + initial_leverages[i])
                for j in range(len(investments)):
                    asset_index = investments[j][1] - num_funds
                    asset_symbol = 'a' + str(asset_index)
                    asset = assets[asset_symbol]
                    portfolio[asset_symbol] = floor(investment_proportions[fund_symbol][j] * fund_capital/asset.price)
            funds[fund_symbol] = Fund(fund_symbol, portfolio, initial_capitals[i], initial_leverages[i], tolerances[i])
        return cls(funds, assets, mi_calc)


    @classmethod
    def load_from_file(cls, file_name, mi_calc: MarketImpactCalculator):
        class_dict = json.load(open(file_name))
        class_funds = class_dict['funds']
        class_assets = class_dict['assets']
        funds = jsonpickle.decode(class_funds)
        assets = jsonpickle.decode(class_assets)
        return cls(funds, assets, mi_calc)

    def save_to_file(self, filename):
        funds_dict = jsonpickle.encode(self.funds)
        asset_dict = jsonpickle.encode(self.assets)
        class_dict = {'funds': funds_dict, 'assets': asset_dict}
        with open(filename, 'w') as fp:
            json.dump(class_dict, fp)

    def get_canonical_form(self):
        num_funds = len(self.funds)
        num_assets = len(self.assets)
        board = numpy.zeros([num_funds, num_assets])
        for i in range(num_funds):
            fund = self.funds['f' + str(i)]
            for j in range(num_assets):
                sym = 'a' + str(j)
                if sym in fund.portfolio:
                    board[i, j] = fund.portfolio[sym] * self.assets[sym].price
        return board

    def get_public_state(self):
        state =  ["{0}:{1}".format(a.symbol, a.price) for a in self.assets]
        return ','.join(state)

    def count_margin_calls(self):
        fund_in_margin = 0
        for fund in self.funds.values():
            if fund.marginal_call(self.assets):
                fund_in_margin += 1
        return fund_in_margin

    def margin_calls(self):
        for fund in self.funds:
            if fund.marginal_call(self.assets):
                return True
        return False

    def get_liquidation_orders(self):
        orders = []
        for fund in self.funds.values():
            orders.append(fund.get_orders(self.assets))
        return orders

    def update_funds(self):
        for fund in self.funds.values():
            fund.update_state(self.assets)

    @staticmethod
    def gen_sell_order(asset):
        return Sell(asset.symbol, SysConfig.get('ORDER_SIZES')*asset.daily_volume)

    @staticmethod
    def gen_buy_order(asset):
        return Buy(asset.symbol, SysConfig.get('ORDER_SIZES') * asset.daily_volume)

    def get_single_orders(self, gen_order_func):
        orders = []
        for asset in self.assets:
            orders.append(gen_order_func(asset))
        return orders





