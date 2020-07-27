import copy
import csv
import json
import os
from datetime import datetime
from math import ceil, inf, factorial

import numpy

from SysConfig import SysConfig
from constants import ATTACKER
from exp.network_generators import get_network_from_dir, gen_new_network
from flash_crash_players_cfr import FlashCrashRootChanceGameState
from flash_crash_players_portfolio_cfr import PortfolioFlashCrashRootChanceGameState
from flash_crash_players_portfolio_per_attacker_cfr import PPAFlashCrashRootChanceGameState
from flash_crash_portfolios_selector_cfr import PortfolioSelectorFlashCrashRootChanceGameState
from solvers.ActionsManager import ActionsManager
from solvers.minimax import minimax, minimax2, alphabeta, single_agent
from solvers.cfr import VanillaCFR
from solvers.split_game_cfr import SplitGameCFR

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

def compute_cfr_ppa_equilibrium(action_mgr, network, defender_budget, attacker_budgets, iterations):
    network.limit_trade_step = True
    root = PPAFlashCrashRootChanceGameState(action_mgr=action_mgr, af_network=network, defender_budget=defender_budget,
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
    cumulative_pos_regret = vanilla_cfr.total_positive_regret()
    return {'defender':defender_eq, 'attackers':attackers_eq, 'regrets':regrets,
            'pos_regret': cumulative_pos_regret / iterations}

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
    cumulative_pos_regret = vanilla_cfr.total_positive_regret()
    return {'defender':defender_eq, 'attackers':attackers_eq, 'regrets':regrets,
            'pos_regret': cumulative_pos_regret / iterations}


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
    initial_netowork = copy.deepcopy(network)
    cfr_actions_mgr = ActionsManager(network.assets, SysConfig.get("STEP_ORDER_SIZE"), 1)
    minimax_actions_mgr = ActionsManager(network.assets, SysConfig.get("STEP_ORDER_SIZE"), 2)
    while defender_budget <= upper_bound:
        attacker_budgets = [int(defender_budget * r) for r in ratios]
        minimax_results = run_minimax_experiments_for_defender_budget(minimax_actions_mgr, network, defender_budget,
                                                                      "minimax", attacker_budgets)
        cfr_results = compute_cfr_equilibrium(cfr_actions_mgr, network, defender_budget, attacker_budgets, iterations)
        update_result_file(defender_budget, attacker_budgets, minimax_results, cfr_results, filename)
        defender_budget += jump


def count_game_states_old(game_network, lower_bound, ratios, network):
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
        actions_mgr = ActionsManager(assets=game_network.assets,
                                     step_order_size=SysConfig.get("STEP_ORDER_SIZE"),
                                     max_order_num=1,
                                     attacker_budgets=attacker_budgets)
        root = PortfolioFlashCrashRootChanceGameState(action_mgr=actions_mgr, af_network=initial_network,
                                                      defender_budget=defender_budget)
    else:
        actions_mgr = ActionsManager(game_network.assets, SysConfig.get("STEP_ORDER_SIZE"), 1)
        root = FlashCrashRootChanceGameState(action_mgr=actions_mgr, af_network=initial_network, defender_budget=defender_budget,
                                             attacker_budgets=attacker_budgets)
    print (count(root, 0))
    print('num_states =%d, num_assets=%d, num_funds = %d, num_attackers = %d' % (root.tree_size, len(game_network.assets),
          len(game_network.funds), len(ratios)))


def count_game_states_portfolios(game_network, lower_bound, ratios,network):
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


def count_portfolios_nodes( defender_budget, attacker_budgets, network, step_order_size, max_order_num):
    split_actions_mgr = ActionsManager(assets=network.assets,
                                       step_order_size=step_order_size,
                                       max_order_num=max_order_num,
                                       attacker_budgets=attacker_budgets)

    root = PortfolioFlashCrashRootChanceGameState(action_mgr=split_actions_mgr, af_network=network,
                                                  defender_budget=defender_budget)
    dummy_utilities = {pid: 0 for pid in split_actions_mgr.get_probable_portfolios().keys()}
    p_selector_root = PortfolioSelectorFlashCrashRootChanceGameState(attacker_budgets, dummy_utilities,
                                                                     split_actions_mgr.get_portfolios_in_budget_dict())
    return root.tree_size + p_selector_root.tree_size


def count_vanilla_nods(defender_budget, attacker_budgets, network, step_order_size, max_order_num):
    vanilla_actions_mgr = ActionsManager(assets=network.assets, step_order_size=step_order_size,
                                         max_order_num=max_order_num)
    vanilla_root = FlashCrashRootChanceGameState(action_mgr=vanilla_actions_mgr, af_network=network,
                                                 defender_budget=defender_budget,
                                                 attacker_budgets=attacker_budgets)
    return vanilla_root.tree_size


def count_game_nodes_csv(res_dir, defender_budget, attacker_budgets, max_num_assets, num_exp=10):
    results = []
    for i in range (1, max_num_assets + 1):
        print('num assets = ' + str(i))
        dirname, network = gen_new_network(i)
        network.limit_trade_step = True
        step_order_size = SysConfig.get("STEP_ORDER_SIZE")
        max_order_num = 1
        print(str(datetime.now()) + ': split')
        split = count_portfolios_nodes(defender_budget=defender_budget,
                                            attacker_budgets=attacker_budgets,
                                            network=network,
                                            step_order_size= step_order_size,
                                            max_order_num = max_order_num)
        print(str(datetime.now()) + ': vanilla')
        vanilla = count_vanilla_nods(defender_budget=defender_budget,
                                          attacker_budgets=attacker_budgets,
                                          network=network,
                                          step_order_size=step_order_size,
                                          max_order_num=max_order_num)

        results.append({'num_assets': str(i), 'vanilla_cfr': vanilla, 'split_cfr': split})

    with open(res_dir + 'count_game_nodes.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['num_assets','vanilla_cfr','split_cfr'])
        writer.writeheader()
        for row in results:
            writer.writerow(row)


def compute_node_size_csv(res_dir, max_num_attackers = 4, max_num_portfolios = 4, portfolio_size = 4):
    results = []
    for num_attackers in range (1, max_num_attackers + 1):
        for num_portfolios in range(1, max_num_portfolios + 1):
            #chance + attackers level + portfolios_tree_num*portfolio_sub_trre_size , use uniform size for simplicity
            vanilla = 1 + num_attackers + num_attackers * portfolio_size*num_portfolios
            # tree1: chance nodes + portfolios_tree_num*portfolio_sub_tree_size
            # tree2: chance node + attackers level + portfolio_level
            split = 1 + num_portfolios*portfolio_size + 1 + num_attackers + num_portfolios
            sv_ratio = split/vanilla
            vs_ratio = vanilla/split
            results.append({'num_attackers': str(num_attackers),
                            'num_portfolios': str(num_portfolios),
                            'vanilla_cfr': vanilla,
                            'split_cfr': split,
                            'split/vanilla':sv_ratio,
                            'vanilla/split':vs_ratio})
        with open(res_dir + 'compute_game_nodes.csv', 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['num_attackers','num_portfolios', 'vanilla_cfr', 'split_cfr',
                                                         'vanilla/split', 'split/vanilla'])
            writer.writeheader()
            for row in results:
                writer.writerow(row)


def get_split_cfr_regret(defender_budget, attacker_budgets, network, step_order_size,
                         max_order_num, iterations, main_game_iteration_portion):
    network.limit_trade_step = True
    # assets, step_order_size, max_order_num=1, attacker_budgets
    cfr_actions_mgr = ActionsManager(assets=network.assets, step_order_size=step_order_size,
                                     max_order_num=max_order_num, attacker_budgets=attacker_budgets)

    split_game_cfr = SplitGameCFR()
    run_results = split_game_cfr.run(action_mgr=cfr_actions_mgr, network=network, defender_budget=defender_budget,
                      attacker_budgets=attacker_budgets,
                      game1_iterations=ceil(iterations*main_game_iteration_portion),
                      game2_iterations=ceil(iterations*(1-main_game_iteration_portion)),
                      round=1)
    return run_results['pos_regret']


def get_vanilla_cfr_regret(defender_budget, attacker_budgets, network, step_order_size, max_order_num, iterations):
    vanilla_actions_mgr = ActionsManager(assets=network.assets, step_order_size=step_order_size,
                                         max_order_num=max_order_num)
    results = compute_cfr_equilibrium(vanilla_actions_mgr, network, defender_budget, attacker_budgets, iterations)
    return results['pos_regret']


def iteration_portion_exp_csv(res_dir, defender_budget, attacker_budgets,
                        min_portion, max_portion, jump, num_assets,iterations_num, step_order_size, max_order_num,num_exp=10):
    portion = min_portion
    regrets = []
    iteration_regrets = {}
    for i in range(0, num_exp):
        while portion < max_portion:
            if portion not in regrets:
                iteration_regrets[portion] = 0
            dirname, network = gen_new_network(num_assets)
            split_cfr_regret = get_split_cfr_regret(defender_budget, attacker_budgets, network, step_order_size,
                                                    max_order_num, iterations_num, portion)
            iterations_num += jump
            iteration_regrets[portion] += split_cfr_regret

    for it_portion in iteration_regrets.keys():
        regrets.append({'iteration_portion': it_portion, 'regret': iteration_regrets[it_portion] / num_exp})

    with open(res_dir + 'iteration_portion.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['num_iterations', 'vanilla_cfr', 'split_cfr'])
        writer.writeheader()
        for row in regrets:
            writer.writerow(row)


def iteration_stats_csv(res_dir, defender_budget, attacker_budgets, main_game_iteration_portion,
                        min_iterations, max_iterations, jump, num_assets, step_order_size, max_order_num, num_exp=10):
    iterations_num = min_iterations
    regrets = []
    iteration_regrets = {}
    for i in range (0, num_exp):
        while iterations_num < max_iterations:
            if iterations_num not in regrets:
                iteration_regrets[iterations_num] = {'split': 0, 'vanilla': 0}
            dirname, network = gen_new_network(num_assets)
            split_cfr_regret = get_split_cfr_regret(defender_budget, attacker_budgets, network, step_order_size,
                             max_order_num, iterations_num, main_game_iteration_portion)
            vanilla_cfr_regret = get_vanilla_cfr_regret(defender_budget, attacker_budgets, network, step_order_size, max_order_num, iterations_num)
            iterations_num += jump
            iteration_regrets[iterations_num]['split'] += split_cfr_regret
            iteration_regrets[iterations_num]['vanilla'] += vanilla_cfr_regret

    for it_num in iteration_regrets.keys():
        regrets.append({'num_iterations':it_num,'split':iteration_regrets[it_num]['split_cfr']/ num_exp,
                        'vanilla_cfr': iteration_regrets[it_num]['vanilla']/num_exp})

    with open(res_dir + 'num_iterations.csv','w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['num_iterations','vanilla_cfr','split_cfr'])
        writer.writeheader()
        for row in regrets:
            writer.writerow(row)
    ## number of attackers?


def run_csv_exps():
    dt = datetime.today()
    dt = str(dt).split(' ')[0]
    res_dir = '../../results/stats/' + dt.replace(":", "_").replace(" ", "_") + '/'
    if not os.path.exists(res_dir):
        os.mkdir(res_dir)
    exp_params = {'defender_budget': 2000000000,
                  'attacker_budgets': [4000000000, 6000000000],
                  'main_game_iteration_portion': 0.9,
                  'min_iterations': 10,
                  'max_iterations': 100,
                  'jump': 10,
                  'num_assets': 3,
                  'step_order_size': SysConfig.get("STEP_ORDER_SIZE")*2,
                  'max_order_num': 1}

    with open(res_dir+'params.json', 'w') as fp:
        json.dump(exp_params, fp)

    compute_node_size_csv(res_dir=res_dir,  max_num_attackers = 4, max_num_portfolios = 4, portfolio_size = 10)
  #  count_game_nodes_csv(res_dir=res_dir, defender_budget=exp_params['defender_budget'],
  #                      attacker_budgets=exp_params['attacker_budgets'],
  #                      max_num_assets = 3)


if __name__ == "__main__":
    run_csv_exps()
    # dirname ='../../results/Tue_May_26_11_14_51_2020/'
    #dirname ='../../results/Wed_Jul__8_14_25_11_2020/'
    #network = get_network_from_dir(dirname)
    ratios = [1, 1.25, 1.5]
 #   dirname, network = '../../../results/Wed_Jul__8_14_25_11_2020/'
    #count_game_states(network, lower_bound=2000000000, ratios=ratios, portfolios=True)
 #   GameStateBase.init_num_nodes()
   # count_game_states(network, lower_bound=2000000000, ratios=ratios, portfolios=False)

    #count_game_states_portfolios(network, lower_bound=700000000, ratios=ratios)
   # exit(0)

  #  network.limit_trade_step = True
  #  run_experiments(network, lower_bound=400000000, jump = 400000000,upper_bound= 4000000000, dirname=dirname, iterations = 10)

    #run_experiments(network, lower_bound=200000000, jump = 400000000,upper_bound= 600000000, dirname=dirname, iterations = 1000)
    #validate_results(dirname+'all_algs_results.json')


#    dirname, network = gen_new_network()
#    dirname ='../results/Mon_Apr_13_17_06_46_2020/'
#    run_experiments(network, lower_bound=200000000, jump = 100000000,upper_bound= 200000000, dirname=dirname)



