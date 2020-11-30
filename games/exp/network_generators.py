import os
import time
from AssetFundNetwork import AssetFundsNetwork
from GameConfig import GameConfig
from MarketImpactCalculator import ExponentialMarketImpactCalculator, SqrtMarketImpactCalculator


def generate_paper_network(game_config, num_assets):
    dir_name = '../../results/networks/'
    initial_capitals = [game_config.initial_fund_capital] * game_config.num_funds
    initial_leverages = [game_config.initial_leverage] * game_config.num_funds
    tolerances = [game_config.tolerance] * game_config.num_funds
    assets_file = '..\\..\\resources\\assets.csv'
    network = AssetFundsNetwork.gen_network_by_paper(beta=game_config.beta,
                                                     num_assets=num_assets,
                                                     rho=game_config.rho,
                                                     sigma=game_config.sigma,
                                                     assets_file=assets_file,
                                                     initial_capitals=initial_capitals,
                                                     initial_leverages=initial_leverages,
                                                     tolerances=tolerances,
                                                     mi_calc= ExponentialMarketImpactCalculator(game_config.impact_calc_constant))
    network.save_to_file(dir_name + 'network.json')

    return network


def gen_network_uniform_funds(game_config, num_assets, assets_file, dir_name):
    config = GameConfig()
#    config.num_assets = 10
 #   config.num_funds = 4
    config.initial_fund_capital = 1000000
    initial_capitals = [game_config.initial_fund_capital] * game_config.num_funds
    initial_leverages = [game_config.initial_leverage] * game_config.num_funds
    tolerances = [game_config.tolerance] * game_config.num_funds

    network = AssetFundsNetwork.generate_random_funds_network(density = game_config.rho,
                                                              num_funds=num_assets,
                                                              initial_capitals= initial_capitals,
                                                              initial_leverages=initial_leverages,
                                                              tolerances=tolerances,
                                                              num_assets=num_assets,
                                                              assets_file=assets_file,
                                                              mi_calc=ExponentialMarketImpactCalculator(config.impact_calc_constant))
    network.save_to_file(dir_name+'network.json')

    return  network

def gen_network_nonuniform_funds(game_config, num_assets, assets_file, dir_name, num_low_risk, num_medium_risk, num_high_risk):
    game_config.num_assets = num_assets
    game_config.num_funds =  num_low_risk +  num_medium_risk + num_high_risk
    initial_capitals, initial_leverages, tolerances = gen_funds_parameters( num_low_risk, num_medium_risk, num_high_risk, game_config)
    #config.initial_fund_capital = 1000000
    # = [game_config.initial_fund_capital] * game_config.num_funds
    #initial_leverages = [game_config.initial_leverage] * game_config.num_funds
    #tolerances = [game_config.tolerance] * game_config.num_funds

    network = AssetFundsNetwork.generate_random_funds_network(density = game_config.rho,
                                                              num_funds=game_config.num_funds,
                                                              initial_capitals= initial_capitals,
                                                              initial_leverages=initial_leverages,
                                                              tolerances=tolerances,
                                                              num_assets=num_assets,
                                                              assets_file=assets_file,
                                                              mi_calc=ExponentialMarketImpactCalculator(game_config.impact_calc_constant))
    network.save_to_file(dir_name+'network.json')

    return  network

def gen_funds_parameters(num_low_risk, num_medium_risk, num_high_risk, game_config):
    initial_capitals = [game_config.initial_fund_capital_lr] * num_low_risk
    initial_capitals.extend([game_config.initial_fund_capital_mr] * num_medium_risk)
    initial_capitals.extend([game_config.initial_fund_capital_hr] * num_high_risk)

    initial_leverages = [game_config.initial_leverage_lr] * num_low_risk
    initial_leverages.extend([game_config.initial_leverage_mr] * num_medium_risk)
    initial_leverages.extend([game_config.initial_leverage_hr] * num_high_risk)

    tolerances = [game_config.tolerance_lr] * num_low_risk
    tolerances.extend([game_config.tolerance_mr] * num_medium_risk)
    tolerances.extend([game_config.tolerance_hr] * num_high_risk)

    return initial_capitals,initial_leverages, tolerances


def get_network_from_dir(dirname, test = False):
    config = GameConfig()
    if test:
        mic = SqrtMarketImpactCalculator()
    else:
        mic = ExponentialMarketImpactCalculator(config.impact_calc_constant)
    return AssetFundsNetwork.load_from_file(dirname+'/network.json', mic)


def gen_new_network(num_assets, net_type ='nonuniform' , results_dir = '../../results/networks/'):
    print('gen network')
    now = time.ctime()
    dirname = results_dir + now.replace(":", "_").replace(" ", "_") + '/'
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    config = GameConfig()
    config.initial_leverage = 3
    config.tolerance = 1.01
    config.initial_fund_capital = 1000000
    config.density = 0.5
    if net_type == 'paper':
        return dirname, generate_paper_network(config, num_assets)
    elif net_type == 'uniform':
        return dirname, gen_network_uniform_funds(config,  num_assets, '..\\..\\resources\\real_assets.csv', dirname)
    elif net_type == 'nonuniform':
        return dirname, gen_network_nonuniform_funds(config,  num_assets, '..\\..\\resources\\real_assets.csv',dirname, 5, 5,5)


#    if uniform:
#        return dirname, gen_network_uniform_funds(config,  num_assets, 'C:\\research\\Flash Crash\\real market data\\assets.csv', dirname)
#    else:
#        return dirname, gen_network_nonuniform_funds(config,  num_assets, 'C:\\research\\Flash Crash\\real market data\\assets.csv', dirname, num_assets, 5, 5,5)#
