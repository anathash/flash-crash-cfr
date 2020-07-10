import copy
import csv
import json
import os
from math import ceil, inf

import numpy

from SysConfig import SysConfig
from bases import GameStateBase
from constants import ATTACKER
from exp.network_generators import get_network_from_dir, gen_new_network
from flash_crash_players_cfr import FlashCrashRootChanceGameState
from flash_crash_players_portfolio_cfr import PortfolioFlashCrashRootChanceGameState
from solvers.ActionsManager import ActionsManager
from solvers.minimax import minimax, minimax2, alphabeta, single_agent
from solvers.cfr import VanillaCFR

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



def update_all_algs_stats(defender_budget, attacker_budgets, minimax_results, cfr_results):
    dict = {}
    dict['defender_budget'] = '%f' % defender_budget
    dict['cfr_defender_eq'] = '%f' % cfr_results['defender']

    for i in range(0,len(attacker_budgets)):
        attacker_budget = attacker_budgets[i]
        dict['attacker'+str(i+1)+'_budget'] = '%f' % attacker_budget
        dict['attacker'+str(i+1)+'_cfr_value'] = '%f' % cfr_results['attackers'][attacker_budget]
#        dict['attacker' + str(i + 1) + '_regret'] = '%.2f' % cfr_results['regrets'][attacker_budget]
        dict['attacker'+str(i+1)+'_minimax_value'] = '%f' % minimax_results[defender_budget][attacker_budget].value
        dict['attacker'+str(i+1)+'_single_agent_value'] = '%f' % minimax_results[0][attacker_budget].value

    return dict

# function to add to JSON
def write_json(data, filename):
    with open(filename,'w') as f:
        json.dump(data, f, indent=4)

def update_result_file(defender_budget, attacker_budgets, minimax_results, cfr_results, filename):
    dict = update_all_algs_stats(defender_budget, attacker_budgets, minimax_results, cfr_results)
    if os.path.exists(filename):
        with open(filename, 'r') as outfile:
            data = json.load(outfile)
            # convert data to list if not
            if type(data) is dict:
                data = [data]

            # append new item to data lit
            data.append(dict)
    else:
        data = [dict]

    # write list to file
    with open(filename, 'w+') as outfile:
        json.dump(data, outfile, indent=4)



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


def compute_cfr_equilibrium(action_mgr, network, defender_budget, attacker_budgets, iterations):
    network.limit_trade_step = True
    root = FlashCrashRootChanceGameState(action_mgr=action_mgr, af_network=network, defender_budget=defender_budget,
                                         attacker_budgets=attacker_budgets)
    vanilla_cfr = VanillaCFR(root)
    vanilla_cfr.run(iterations=iterations)
    vanilla_cfr.compute_nash_equilibrium()
    defender_eq =  vanilla_cfr.value_of_the_game()
    attackers_eq = {}
    regrets = {}
    root =vanilla_cfr.root
    for attacker in attacker_budgets:
        attackers_eq[attacker] = root.children[str(attacker)].get_value()
        regrets[attacker]  = vanilla_cfr.cumulative_regrets[root.children[str(attacker)].inf_set()]
    return {'defender':defender_eq, 'attackers':attackers_eq, 'regrets':regrets}

def run_minimax_experiments_for_defender_budget(actions_mgr, network, defender_budget,  alg, attacker_budgets):
    results = {0: {}, defender_budget:{}}
    for attacker_budget in attacker_budgets:
        print(' Defender:' + str(defender_budget) + ' Attacker: ' + str(attacker_budget))
        results[0][attacker_budget] = single_agent(actions_mgr, network, attacker_budget)
        network.limit_trade_step = True
        if alg == 'minimax':
            results[defender_budget][attacker_budget] = minimax2(actions_mgr, ATTACKER, network, attacker_budget, defender_budget)
        else:
            results[defender_budget][attacker_budget] = alphabeta(actions_mgr, ATTACKER, network, attacker_budget, defender_budget, (-inf,inf),(inf, inf))
    return results




def run_experiments(network, lower_bound, jump, upper_bound, dirname, iterations = 1000):
    filename = dirname+'//all_algs_results.json'
    if os.path. exists(filename):
        os.remove(filename)

    defender_budget = lower_bound
    ratios = [0.75, 1, 1.25, 1.5]
    initia_netowork = copy.deepcopy(network)
    cfr_actions_mgr = ActionsManager(network.assets, SysConfig.get("STEP_ORDER_SIZE"), 1)
    minimax_actions_mgr = ActionsManager(network.assets, SysConfig.get("STEP_ORDER_SIZE"), 2)
    while defender_budget <= upper_bound:
        attacker_budgets = [int(defender_budget * r) for r in ratios]
        minimax_results = run_minimax_experiments_for_defender_budget(minimax_actions_mgr, network, defender_budget,
                                                                      "minimax", attacker_budgets)
        cfr_results = compute_cfr_equilibrium(cfr_actions_mgr, network, defender_budget, attacker_budgets, iterations)
        update_result_file(defender_budget, attacker_budgets, minimax_results, cfr_results, filename)
        defender_budget += jump


def count_game_states_old(game_network, lower_bound, ratios):
    network.limit_trade_step = True
    defender_budget = lower_bound
    actions_mgr = ActionsManager(network.assets, SysConfig.get("STEP_ORDER_SIZE"), 1)
    initial_network = copy.deepcopy(game_network)
    attacker_budgets = [int(defender_budget * r) for r in ratios]
    root = FlashCrashRootChanceGameState(action_mgr=actions_mgr, af_network=initial_network, defender_budget=defender_budget,
                                         attacker_budgets=attacker_budgets)
    print('num_states =%d, num_assets=%d, num_funds = %d, num_attackers = %d' % (root.tree_size, len(game_network.assets),
          len(game_network.funds), len(ratios)))

def count(state, counter):
    for kid in state.children.values():
        counter += count(kid, 0)
    return counter +1


def count_game_states(game_network, lower_bound, ratios, portfolios = False):
    network.limit_trade_step = True
    defender_budget = lower_bound
    initial_network = copy.deepcopy(game_network)
    attacker_budgets = [int(defender_budget * r) for r in ratios]
    if portfolios:
        actions_mgr = ActionsManager(assets=network.assets,
                                     step_order_size=SysConfig.get("STEP_ORDER_SIZE"),
                                     max_order_num=1,
                                     attacker_budgets=attacker_budgets)
        root = PortfolioFlashCrashRootChanceGameState(action_mgr=actions_mgr, af_network=initial_network,
                                                      defender_budget=defender_budget)
    else:
        actions_mgr = ActionsManager(network.assets, SysConfig.get("STEP_ORDER_SIZE"), 1)
        root = FlashCrashRootChanceGameState(action_mgr=actions_mgr, af_network=initial_network, defender_budget=defender_budget,
                                             attacker_budgets=attacker_budgets)
    print (count(root, 0))
    print('num_states =%d, num_assets=%d, num_funds = %d, num_attackers = %d' % (root.tree_size, len(game_network.assets),
          len(game_network.funds), len(ratios)))

def count_game_states_portfolios(game_network, lower_bound, ratios):
    network.limit_trade_step = True
    defender_budget = lower_bound
    attacker_budgets = [int(defender_budget * r) for r in ratios]
    actions_mgr = ActionsManager(assets=network.assets,
                                 step_order_size=SysConfig.get("STEP_ORDER_SIZE"),
                                 max_order_num=1,
                                 attacker_budgets=attacker_budgets)
    initial_network = copy.deepcopy(game_network)

    root = PortfolioFlashCrashRootChanceGameState(action_mgr=actions_mgr, af_network=initial_network,
                                                  defender_budget=defender_budget)
    print('num_states =%d, num_assets=%d, num_funds = %d, num_attackers = %d' % (root.tree_size, len(game_network.assets),
          len(game_network.funds), len(ratios)))


def validate_results(filename):
    with open(filename,'r') as res_file:
        data = json.load(res_file)
        for entry in data:
            defender_budget = entry['defender_budget']
            cfr_defender_eq = float(entry['cfr_defender_eq'])
            cfr_attacker1_eq = float(entry['attacker1_cfr_value'])
            cfr_attacker2_eq = float(entry['attacker2_cfr_value'])
            expected_cfr_val = 0.5*(cfr_attacker1_eq+cfr_attacker2_eq)
            if not numpy.isclose(cfr_defender_eq, expected_cfr_val, rtol=1e-03, atol=1e-08, equal_nan=False):
                print('cfr_defender_eq +!= 0.5*cfr_attacker1_eq+0.5*cfr_attacker2_eq for defender budget ' + defender_budget)
                print(str(cfr_defender_eq) +'!=' + str(expected_cfr_val))

            for i in range(1,3):
                attacker_budget = entry['attacker' + str(i) + '_budget']
                minimax_value = entry['attacker' +str(i)+'_minimax_value']
                single_agent_value = entry['attacker' +str(i)+'_single_agent_value']
                cfr_agent_value  = entry['attacker' +str(i)+'_cfr_value']
                valid = float(single_agent_value) <= float(cfr_agent_value) <=  float(minimax_value)
                if not valid:
                    print('Invalid entry. Defender Budget: ' + defender_budget +", attacker budget: " + attacker_budget + '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                else:
                    print('Valid entry. Defender Budget: ' + defender_budget +", attacker budget: " + attacker_budget)



if __name__ == "__main__":

   # dirname ='../../results/Tue_May_26_11_14_51_2020/'
    #dirname ='../../results/Wed_Jul__8_14_25_11_2020/'
    #network = get_network_from_dir(dirname)
    ratios = [1, 1.25, 1.5]
    dirname, network = gen_new_network(2)
    count_game_states(network, lower_bound=2000000000, ratios=ratios, portfolios=True)
 #   GameStateBase.init_num_nodes()
   # count_game_states(network, lower_bound=2000000000, ratios=ratios, portfolios=False)

    #count_game_states_portfolios(network, lower_bound=700000000, ratios=ratios)
    exit(0)

    network.limit_trade_step = True
    run_experiments(network, lower_bound=400000000, jump = 400000000,upper_bound= 4000000000, dirname=dirname, iterations = 10)

    run_experiments(network, lower_bound=200000000, jump = 400000000,upper_bound= 600000000, dirname=dirname, iterations = 1000)
    validate_results(dirname+'all_algs_results.json')


#    dirname, network = gen_new_network()
#    dirname ='../results/Mon_Apr_13_17_06_46_2020/'
#    run_experiments(network, lower_bound=200000000, jump = 100000000,upper_bound= 200000000, dirname=dirname)



