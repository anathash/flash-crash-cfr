from typing import Dict

import numpy as np
from scipy.optimize import minimize

from flash_crash import GameConfig, Fund
from flash_crash.AssetFundNetwork import AssetFundsNetwork
from flash_crash.MarketImpactCalculator import ExponentialMarketImpactCalculator
from flash_crash.NetworkGenerator import generate_rand_network

assets = []
fund = None
mi_calc = None
budget = 100000

initial_attacks = []


def fund_portfolio_value(num_shares):
    v = 0
    for i in range(0, len(num_shares)):
        asset = assets[i]
        if num_shares[i] == 0:
            continue
        v += fund.portfolio[asset.symbol]*asset.price * mi_calc.get_market_impact(
            -1 * num_shares[i]/asset.daily_volume)
    return v

def budget_constraint(num_shares):
    attack_price = 0
    for i in range(0, len(num_shares)):
        if num_shares[i] == 0:
            continue
        attack_price +=10* num_shares[i]
    return budget - attack_price

def margin_call_constraint(sell_fractions):
    con = fund.initial_capital*(fund.initial_leverage + 1/fund.tolerance)
    return con - fund_portfolio_value(sell_fractions)


def generate_attacks(network: AssetFundsNetwork, goals: str):
    funds = [network.funds[goal] for goal in goals]
    assets = set()
    for fund in funds:
        assets.update(fund.portfolio.keys())

    n = len(assets)
    bnds = [0]*n
    x0 = [0] * n
    equal_budget = budget/n
    for i in range(0, n):
        asset = assets[i]
        bnds[i] = asset.daily_volume * volume_limit
        x0[i] = np.floor(equal_budget /assets[i].price)
    con1 = {'type': 'ineq', 'fun': budget_constraint}
    con2 = {'type': 'ineq', 'fun': margin_call_constraint}
    cons = [con1]
    sol = minimize(fund_portfolio_value, x0, 'SLSQP',  constraints=cons)
    #sol = minimize(self.fund_portfolio_value, x0, 'SLSQP', bounds=bnds, constraints=cons)
    return sol


def get_threatened_funds_combinations(funds):

    combinations = []
    for L in range(1, len(funds) + 1):
        for subset in np.itertools.combinations(funds, L):
            combinations.append(subset)


def get_possible_attacks(network: AssetFundsNetwork, budget, initial_attack):
    if initial_attack:
        funds = network.get_funds_under_threats()
    else:
        funds = network.funds

    goals = get_threatened_funds_combinations(funds)



if __name__ == "__main__":
    config = GameConfig()
    config.num_assets = 10
    config.num_funds = 10
    g = generate_rand_network(config)
    g.run_intraday_simulation(config.intraday_asset_gain_max_range, 0.7 * config.initial_leverage)
    goal = 'f2'
    sol = generate_attacks(g, goal, budget, 0.1, ExponentialMarketImpactCalculator(config.impact_calc_constant))
    exit(0)





