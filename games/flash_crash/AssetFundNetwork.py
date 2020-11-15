#!/usr/bin/python
import csv
import json
import random
from math import floor, ceil

import networkx as nx
import numpy


from typing import Dict
import jsonpickle

import MarketImpactCalculator
from Orders import Sell, Buy
from SysConfig import SysConfig
from constants import MINUTES_IN_TRADING_DAY

'TODO: do we need the total market cap of assets or do funds hold the entire market'


class Asset:
    def __init__(self, price, daily_volume, symbol, volatility = 0):
        self.zero_time_price = price
        self.price = price
        self.daily_volume = daily_volume
        self.avg_minute_volume = daily_volume/MINUTES_IN_TRADING_DAY
        self.symbol = symbol
        self.volatility = volatility
        self.max_shares_to_trade_in_ts = ceil(SysConfig.get('TIME_STEP_MINUTES')\
                                      *SysConfig.get('DAILY_PORTION_PER_MIN')*daily_volume)

    def set_price(self, new_price):
        self.price = new_price

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Asset) and self.price == other.price and self.daily_volume == other.daily_volume \
               and self.volatility == other.volatility and self.symbol == other.symbol and self.zero_time_price == other.zero_time_price


class Fund:
    def __init__(self, symbol, portfolio: Dict[str, int], initial_capital, initial_leverage, tolerance):
        self.symbol = symbol
        self.leverage = initial_leverage
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
               self.leverage == other.leverage and \
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
        self.leverage = curr_portfolio_value / curr_capital - 1 #return self.compute_portfolio_value(assets) / self.capital - 1
        return self.leverage

    def marginal_call(self, assets):
        return self.compute_curr_leverage(assets) / self.initial_leverage > self.tolerance


def read_assets_file(assets_file, num_assets):
    assets = {}
    with open(assets_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            symbol = row['symbol']
            assets[symbol] = Asset(price=float(row['price']), daily_volume=float(row['volume']), symbol=symbol)
            if len(assets) == num_assets:
                return assets
    return assets


class AssetFundsNetwork:

    def __init__(self, funds: Dict[str, Fund], assets: Dict[str, Asset], mi_calc: MarketImpactCalculator,
                 intraday_asset_gain_max_range =None, limit_trade_step = True):
        self.mi_calc = mi_calc
        self.funds = funds
        self.assets = assets
        self.buy_orders = {}
        self.sell_orders = {}
#        if intraday_asset_gain_max_range:
#            self.run_intraday_simulation(intraday_asset_gain_max_range, 0.7)
        self.limit_trade_step = limit_trade_step
        for f in self.funds.values():
            assert(not f.is_in_margin_call())

    def __eq__(self, other):
        return isinstance(other, AssetFundsNetwork) and isinstance(other.mi_calc, type(self.mi_calc)) and \
               self.funds == other.funds and self.assets == other.assets

    def __repr__(self):
        return str(self.funds)

    def reset_order_books(self):
        self.buy_orders = {}
        self.sell_orders = {}

    def public_state(self):
        return str({a.symbol:a.price for a in self.assets.values()})


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
        while not self.order_books_empty():
            self.simulate_trade()

    def order_books_empty(self):
        return not (self.buy_orders or self.sell_orders)

    def no_more_sell_orders(self):
        return not (self.sell_orders)

    def simulate_trade(self):
        log = {}
        order_keys = set(self.sell_orders.keys())
        order_keys.update(self.buy_orders.keys())
        for order_key in order_keys:
            if not order_key: #empty order
                continue
            buy = self.buy_orders[order_key] if order_key in self.buy_orders else 0
            sell = self.sell_orders[order_key] if order_key in self.sell_orders else 0
            balance = buy - sell
            if balance == 0:
                del self.buy_orders[order_key]
                del self.sell_orders[order_key]
                continue
            if self.limit_trade_step:
                max_shares_to_trade_in_ts = ceil(SysConfig.get('TIME_STEP_MINUTES')\
                                      *SysConfig.get('DAILY_PORTION_PER_MIN')* self.assets[order_key].daily_volume)
                #max_shares_to_trade = self.assets[order_key].max_shares_to_trade_in_ts
                shares_to_trade = min(abs(balance), max_shares_to_trade_in_ts)
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
            log[order_key] = '{0}->{1}'.format(self.assets[order_key].price, updated_price)
            self.assets[order_key].price = updated_price
        return log


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
    def gen_network_from_graph_with_assets(cls, g, investment_proportions,
                                           initial_capitals, initial_leverages, assets,
                                           tolerances, mi_calc: MarketImpactCalculator):
        funds = {}
        fund_nodes, asset_nodes = nx.bipartite.sets(g)
        num_funds = len(fund_nodes)
        assets_list = list(assets.values())
        for i in range(num_funds):
            portfolio = {}
            fund_symbol = 'f' + str(i)
            investments = list(g.out_edges(i))
            if investments:
                fund_capital = initial_capitals[i] * (1 + initial_leverages[i])
                portfolio_value = 0
                for j in range(len(investments)):
                    asset_index = investments[j][1] - num_funds
                    asset = assets_list[asset_index]
                    portfolio[asset.symbol] = floor(investment_proportions[fund_symbol][j] * fund_capital / asset.price)
                    portfolio_asset_value = portfolio[asset.symbol] * asset.price
                    portfolio_value+=portfolio_asset_value
            funds[fund_symbol] = Fund(fund_symbol, portfolio, initial_capitals[i], initial_leverages[i], tolerances[i])
            #print(funds[fund_symbol].compute_portfolio_value(assets))
            #print('')

        return cls(funds, assets, mi_calc)

    @classmethod
    def generate_random_funds_network(cls, density, num_funds, initial_capitals, initial_leverages,
                                      tolerances, num_assets, assets_file, mi_calc: MarketImpactCalculator):
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
        assets = read_assets_file(assets_file, num_assets)
        return cls.gen_network_from_graph_with_assets(g, investment_proportions, initial_capitals,
                                          initial_leverages,assets, tolerances, mi_calc)
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

    def gen_network_by_paper(cls,  beta, rho, sigma,
                               initial_capitals, initial_leverages, assets_initial_prices,
                               tolerances, daily_volumes, volatility, mi_calc: MarketImpactCalculator, replace = False,):
        funds = {}
        assets = {}
        assets_investment_portion = {sym:0 for sym in assets.keys()}
        num_assets = len(assets_initial_prices)
        for i in range(len(num_assets)):
            symbol = 'a' + str(i)
            assets[symbol] = Asset(price=assets_initial_prices[i], daily_volume=daily_volumes[i], symbol=symbol,
                                   volatility = volatility[i])
        for i in range(initial_leverages):
            investment_size = {}
            assets_sorted = sorted(assets_investment_portion.items(), key=lambda kv: kv[1])
            pj = {}
            for j in range(1, num_assets+1):
                if beta < 0:
                    r_j =  num_assets - j +1
                else:
                    r_j = j
                sym = assets_sorted[j][0]
                pj[sym] = pow(r_j,beta)
            pj_sum = sum(pj.values())
            pj[symbol] = pj[symbol]/pj_sum
            k_fund = max(1,numpy.random.normal(rho, sigma))
            for k in range (0, k_fund):
                choice = numpy.random.choice(pj.keys(), p = pj.values(),replace=replace)
                investment_size[choice] = numpy.random.normal(0, 1)
                investemnt_sum = sum(investment_size.values())
            investemnt_sum_normed = {x:(total_capital*y)/investemnt_sum for x,y in  investment_size.items()}
            portfolio = {floor(investemnt_sum_normed[x]/assets[x].price for x in investemnt_sum_normed.keys())}
            fund_symbol = 'f' + str(i)
            total_capital = initial_capitals[i](+ initial_leverages[i])
            funds[fund_symbol] = Fund(fund_symbol, portfolio, initial_capitals[i], initial_leverages[i], tolerances[i])
        return cls(funds, assets, mi_calc)


    @classmethod
    def load_from_file(cls, file_name, mi_calc: MarketImpactCalculator):
        with open(file_name, 'r') as f:
            class_dict = json.load(f)
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

    def get_funds_in_margin_calls(self):
        fund_in_margin = []
        for fund in self.funds.values():
            if fund.marginal_call(self.assets):
                fund_in_margin.append(fund.symbol)
        return fund_in_margin

    def margin_calls(self):
        for fund in self.funds.values():
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

    def get_single_orders_multiple_options(self, gen_order_func):
        orders = []
        for asset in self.assets.values():
            for size in SysConfig.get('ORDER_SIZES'):
                order = gen_order_func(asset, size)
                orders.append(order)
        return orders




