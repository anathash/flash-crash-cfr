#from __future__ import division
import copy
import csv
import os
import random
import time
from math import ceil, inf

from AssetFundNetwork import AssetFundsNetwork
from GameConfig import GameConfig
from MarketImpactCalculator import ExponentialMarketImpactCalculator
from SysConfig import SysConfig
from constants import ATTACKER
from flash_crash_players_cfr import FlashCrashRootChanceGameState
from solvers.minimax import minimax, minimax2, alphabeta
from solvers.cfr import VanillaCFR
from solvers.common import store_solutions_by_key, store_solutions
from solvers.single_agent_dynamic_programin import SingleAgentDynamicProgrammingSolver
from solvers.single_agent_solver import SingleAgentESSolver
from solvers.single_fund_attack_solver import single_fund_attack_optimal_attack_generator

BUDGET_LOWER_BOUND = 10000000
BUDGET_UPPER_BOUND = 100000000
MINIMAX = "minimax"
SINGLE_AGENT = "single_agent"
CFR = "cfr"
NUM_ACTIONS = "num_actions"
VALUE = "value"
TIME ="time"
alg_fields = [VALUE,NUM_ACTIONS, TIME]
DEFENDER_BUDGET = "defender_budget"
ATTACKER_BUDGET = "attacker_budget"


def get_cost_boundaries(orig_network, order_size, max_num_orders):
    network = copy.deepcopy(orig_network)
    min = inf
    total = 0
    for sym,fund in network.funds.items():
        actions, cost = single_fund_attack_optimal_attack_generator(network,sym,network.mi_calc,order_size, max_num_orders)
        if cost < min:
            print(actions)
            min = cost
        total += cost
    return min, total

def round_to_decimal(num,f):
    int_num = int(num)
    num_digits = len(str(int_num))
    decimal = pow(10, num_digits -1)
    return (f(int_num/decimal))*decimal


def gen_es_solution_file_old(network, dirname):
    order_size = SysConfig.get("STEP_ORDER_SIZE")
    max_num_orders= SysConfig.get("MAX_NUM_ORDERS")
    es_solver = SingleAgentESSolver(network, order_size,max_num_orders)
    es_solver.gen_attacks(network)
    store_solutions(dirname+'solutions.csv', es_solver.solutions)


def gen_es_solution_file(network, dirname):
    order_size = SysConfig.get("STEP_ORDER_SIZE")
    max_num_orders= SysConfig.get("MAX_NUM_ORDERS")
    es_solver = SingleAgentESSolver(network, order_size,max_num_orders)
    solutions = es_solver.gen_optimal_attacks()
    store_solutions(dirname+'solutions_es.csv', solutions)

def gen_single_agents_solution_file__(network, dirname):
    order_size = SysConfig.get("STEP_ORDER_SIZE")
    max_num_orders= SysConfig.get("MAX_NUM_ORDERS")
    min, max = get_cost_boundaries(network,  order_size, max_num_orders)
   # jump = pow (10, len(str(int(min))))
    min_bound = round_to_decimal(min, ceil)
    #max_bound = min_bound*10
    budget = 1500000000
    single_agent_solver = SingleAgentDynamicProgrammingSolver(network, min+1,
                                                              order_size,max_num_orders )


    single_agent_solver.store_solution(dirname+'solutions.csv')


def gen_single_agents_solution_file(network, dirname, upper_bound, jump,lower_bound):
    order_size = SysConfig.get("STEP_ORDER_SIZE")
    max_num_orders= SysConfig.get("MAX_NUM_ORDERS")
    budget = lower_bound
    solutions = {}
    while (budget <= upper_bound):
        single_agent_solver = SingleAgentDynamicProgrammingSolver(copy.deepcopy(network), budget,
                                                                  order_size,max_num_orders)
        solutions[budget] = single_agent_solver.results
        budget += jump

    store_solutions_by_key(dirname+'/dynamic_programming_solutions.csv', solutions, 'budget')


def update_stats(result, alg, attacker_budget, defender_budget):
    dict = {}
    dict[alg+'_attacker_budget'] = str(attacker_budget)
    dict[alg+'_defender_budget'] = str(defender_budget)
    dict[alg+'_attacker_cost'] = '%.2f' % result.attacker_cost
    dict[alg+'_defender_cost'] =  '%.2f' % result.defender_cost
    dict[alg+'_'+ VALUE] = str(result.value)
    dict[alg+'_funds'] = str(result.funds)
    dict[alg+'_actions'] = str(result.actions)
    return dict

def run_single_exp(network, attacker_budget, defender_budget):
    stats = {ATTACKER_BUDGET:attacker_budget,DEFENDER_BUDGET:defender_budget}
    start = time.time()
    minimax_result = minimax(ROOT_ATTACKER, network,attacker_budget, defender_budget)
    minimax_time = time.time() - start
    update_stats(minimax_result, minimax_time, stats)
    start = time.time()
    signel_agent_solver = SingleAgentDynamicProgrammingSolver(network, attacker_budget,
                                                              SysConfig.get("STEP_ORDER_SIZE"))
    single_agent_time = time.time() - start
    update_stats(signel_agent_solver.results, single_agent_time, stats )

    return  stats
    #cfr


def run_experiments(network):
    stats_list = []
    for i in range(0, 10):
        defender_budget = random.randint(BUDGET_LOWER_BOUND, BUDGET_UPPER_BOUND)
        attacker_budget = random.randint(defender_budget, BUDGET_UPPER_BOUND)
        stats = run_single_exp(network=network, attacker_budget=attacker_budget, defender_budget=defender_budget)
        stats_list.append(stats)

    for i in range(0, 10):
        attacker_budget = random.randint(BUDGET_LOWER_BOUND, BUDGET_UPPER_BOUND)
        defender_budget = random.randint(defender_budget, BUDGET_UPPER_BOUND)
        stats = run_single_exp(network=network, attacker_budget=attacker_budget, defender_budget=defender_budget)
        stats_list.append(stats)
    return  stats_list



def write_results_file(stats_list, dirname):
    all_stats_fields = [ATTACKER_BUDGET, DEFENDER_BUDGET]
    algs = [MINIMAX, SINGLE_AGENT, CFR]
    for alg in algs:
        for field in alg_fields:
            all_stats_fields.append(alg + '_' + field)

    with open(dirname + dirname + '_results.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=all_stats_fields)
        writer.writeheader()
        for row in stats_list:
            writer.writerow(row)



def gen_network_uniform_funds(game_config, num_assets, assets_file, dir_name):
    config = GameConfig()
    config.num_assets = 10
    config.num_funds = 10
    config.initial_fund_capital = 1000000
    initial_capitals = [game_config.initial_fund_capital] * game_config.num_funds
    initial_leverages = [game_config.initial_leverage] * game_config.num_funds
    tolerances = [game_config.tolerance] * game_config.num_funds

    network = AssetFundsNetwork.generate_random_funds_network(density = game_config.density,
                                                              num_funds=game_config.num_funds,
                                                              initial_capitals= initial_capitals,
                                                              initial_leverages=initial_leverages,
                                                              tolerances=tolerances,
                                                              num_assets=num_assets,
                                                              assets_file=assets_file,
                                                              mi_calc=ExponentialMarketImpactCalculator(config.impact_calc_constant))
    network.save_to_file(dir_name+'network.json')

    return  network

def gen_network_nonuniform_funds(game_config, num_assets, assets_file, dir_name, num_low_risk, num_medium_risk, num_high_risk):
    game_config.num_assets = 10
    game_config.num_funds =  num_low_risk +  num_medium_risk + num_high_risk
    initial_capitals, initial_leverages, tolerances = gen_funds_parameters( num_low_risk, num_medium_risk, num_high_risk, game_config)
    #config.initial_fund_capital = 1000000
    # = [game_config.initial_fund_capital] * game_config.num_funds
    #initial_leverages = [game_config.initial_leverage] * game_config.num_funds
    #tolerances = [game_config.tolerance] * game_config.num_funds

    network = AssetFundsNetwork.generate_random_funds_network(density = game_config.density,
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


def get_network_from_dir(dirname):
    config = GameConfig()
    return AssetFundsNetwork.load_from_file(dirname+'/network.json', ExponentialMarketImpactCalculator(config.impact_calc_constant))

def  gen_new_network():
    now = time.ctime()
    dirname = '../results/' + now.replace(":", "_").replace(" ", "_") + '/'
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    config = GameConfig()
    config.initial_leverage = 3
    config.tolerance = 1.01
    config.initial_fund_capital = 1000000
    config.density = 0.5
    return dirname, gen_network_nonuniform_funds(config,  10, 'C:\\research\\Flash Crash\\real market data\\assets.csv', dirname, 5, 5,5)

def run_cfr_experiments(network, lower_bound, jump, upper_bound, dirname):
    defender_budgets = lower_bound

    while (defender_budgets <= upper_bound):
        run_cfr_experiments_for_defender_budget(network, defender_budgets, dirname)
        defender_budgets += jump

def compute_equilibrium(network, defender_budget):
    ratios = [0.5, 2]
    attacker_budgets = [int(defender_budget * r) for r in ratios]
    root = FlashCrashRootChanceGameState(af_network=network, defender_budget=defender_budget,
                                         attacker_budgets=attacker_budgets)
    vanilla_cfr = VanillaCFR(root)
    vanilla_cfr.run(iterations=1000)
    vanilla_cfr.compute_nash_equilibrium()
    return vanilla_cfr.value_of_the_game()


def run_cfr_experiments_for_defender_budget(network, defender_budget, dir_name):
    eq_value =compute_equilibrium(network, defender_budget)
    print(eq_value)
    #result =[]
    #results.append(update_stats(result, 'cfr', attacker_budget, defender_budget))
    #print_results(dir_name,attacker_budget,results, 'cfr')


def run_minimax_experiments(network, lower_bound, jump, upper_bound, dirname, alg ='minimax'):
    attacker_budget = lower_bound
    while (attacker_budget <= upper_bound):
        run_minimax_experiments_for_attacker_budget(network, attacker_budget, dirname, alg)
        attacker_budget += jump



def print_results(dir_name,attacker_budget,results, alg='minimax'):
    with open(dir_name+'/'+alg+'/attacker_budget_'+str(attacker_budget)+'.csv', 'w', newline='') as csvfile:
        fieldnames = [alg+'_attacker_budget', alg+'_defender_budget', alg+'_attacker_cost',
                      alg+'_defender_cost', alg+'_value', alg+'_funds', alg+'_actions']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)

def run_minimax_experiments_for_attacker_budget(network, attacker_budget, dir_name, alg):
    results = []
    ratios = [0.1* i for i in range(10,1, -1)]
    defender_budgets = [0]
    defender_budgets.extend([int(attacker_budget * r) for r in ratios])
    #defender_budgets = [int(attacker_budget * r) for r in ratios]
    for defender_budget in defender_budgets:
        print(' Defender:' + str(defender_budget) + ' Attacker: ' + str(attacker_budget))
        if alg == 'minimax':
            minimax_result = minimax2(ATTACKER, network, attacker_budget, defender_budget)
        else:
            minimax_result = alphabeta(ATTACKER, network, attacker_budget, defender_budget, (-inf,inf),(inf, inf))


        results.append(update_stats(minimax_result, 'minimax', attacker_budget, defender_budget))
    print_results(dir_name,attacker_budget,results, alg)


if __name__ == "__main__":
#    dirname, network = gen_new_network()
#    dirname ='../results/Mon_Apr_13_17_06_46_2020/'
    dirname ='../results/Tue_May__5_15_11_13_2020/'
    network = get_network_from_dir(dirname)
    network.limit_trade_step = True
#    os.mkdir(dirname+'/cfr')
    run_cfr_experiments(network, lower_bound=200000000, jump = 100000000,upper_bound= 200000000, dirname=dirname)
#    gen_es_solution_file(network, dirname)
#    gen_single_agents_solution_file(network=network, dirname=dirname,lower_bound=4800000000, jump = 100000000,upper_bound=12000000000 )
 #   run_minimax_experiments(network, lower_bound=1000000000, jump = 1000000000,upper_bound= 1500000000, dirname=dirname)
  #  run_minimax_experiments(network, lower_bound=2000000000, jump = 2000000000,upper_bound= 6000000000, dirname=dirname, alg='alphabeta')
#    stats_list = run_experiments(network)
#    write_results_file(stats_list, dirname)


