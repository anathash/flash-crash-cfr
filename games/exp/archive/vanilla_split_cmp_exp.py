import csv
import json
import os
from datetime import datetime
from math import ceil

from SysConfig import SysConfig
from exp.network_generators import gen_new_network
from flash_crash_players_cfr import FlashCrashRootChanceGameState
from flash_crash_players_portfolio_cfr import PortfolioFlashCrashRootChanceGameState
from flash_crash_players_portfolio_per_attacker_cfr import PPAFlashCrashRootChanceGameState
from ActionsManager import ActionsManager
from split_game_cfr import SplitGameCFR
from split_selector_game import SelectorRootChanceGameState
from vanilla_cfr_runner import compute_cfr_equilibrium

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


def count_portfolios_nodes( defender_budget, attacker_budgets, network, step_order_size, max_order_num):
    split_actions_mgr = ActionsManager(assets=network.assets,
                                       step_order_size=step_order_size,
                                       max_order_num=max_order_num,
                                       attacker_budgets=attacker_budgets)

    root = PortfolioFlashCrashRootChanceGameState(action_mgr=split_actions_mgr, af_network=network,
                                                  defender_budget=defender_budget)
    dummy_utilities = {pid: 0 for pid in split_actions_mgr.get_probable_portfolios().keys()}
    p_selector_root = SelectorRootChanceGameState(attacker_budgets, dummy_utilities,
                                                                     split_actions_mgr.get_portfolios_in_budget_dict())
    return root.tree_size + p_selector_root.tree_size


def count_ppa_nods(defender_budget, attacker_budgets, network, step_order_size, max_order_num):
    actions_mgr = ActionsManager(assets=network.assets,
                                       step_order_size=step_order_size,
                                       max_order_num=max_order_num,
                                       attacker_budgets=attacker_budgets)
    root = PPAFlashCrashRootChanceGameState(action_mgr=actions_mgr, af_network=network,
                                                 defender_budget=defender_budget,
                                                 attacker_budgets=attacker_budgets)
    return root.tree_size


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
        vanilla = count_ppa_nods(defender_budget=defender_budget,
                                          attacker_budgets=attacker_budgets,
                                          network=network,
                                          step_order_size=step_order_size,
                                          max_order_num=max_order_num)

        results.append({'num_assets': str(i), 'vanilla_cfr': vanilla, 'split_cfr': split})

    with open(res_dir + 'count_game_nodes_ppa.csv', 'w', newline='') as csvfile:
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


def get_split_cfr_exploitabilty(defender_budget, attacker_budgets, network, step_order_size,
                         max_order_num, iterations, main_game_iteration_portion):
    network.limit_trade_step = True
    # assets, step_order_size, max_order_num=1, attacker_budgets
    cfr_actions_mgr = ActionsManager(assets=network.assets, step_order_size=step_order_size,
                                     max_order_num=max_order_num, attacker_budgets=attacker_budgets)

    split_game_cfr = SplitGameCFR()

    root = PortfolioFlashCrashRootChanceGameState(action_mgr=cfr_actions_mgr,
                                                  af_network=network,
                                                  defender_budget=defender_budget)

    (main_game_results, selector_game_result) = split_game_cfr.run(main_game_root=root, attacker_types=attacker_budgets,
                                     game1_iterations=ceil(iterations*main_game_iteration_portion),
                                     game2_iterations=ceil(iterations*(1-main_game_iteration_portion)),
                                     attacks_in_budget_dict=cfr_actions_mgr.get_portfolios_in_budget_dict(),
                                     subgame_keys=cfr_actions_mgr.get_portfolios().keys())

    return main_game_results['exploitability']+selector_game_result['exploitability']



def get_vanilla_cfr_exp(defender_budget, attacker_budgets, network, step_order_size, max_order_num, iterations):
    vanilla_actions_mgr = ActionsManager(assets=network.assets, step_order_size=step_order_size,
                                         max_order_num=max_order_num)
    results = compute_cfr_equilibrium(vanilla_actions_mgr, network, defender_budget, attacker_budgets, iterations)
    return results['exploitability']


def iteration_portion_exp_csv(res_dir, defender_budget, attacker_budgets,
                        min_portion, max_portion, jump, num_assets,iterations_num, step_order_size, max_order_num,num_exp=10):
    portion = min_portion
    regrets = []
    iteration_regrets = {}
    for i in range(0, num_exp):
        dirname, network = gen_new_network(num_assets)
        while portion < max_portion:
            if portion not in regrets:
                iteration_regrets[portion] = 0
            split_cfr_exploitability = get_split_cfr_exploitabilty(defender_budget, attacker_budgets, network, step_order_size,
                                                    max_order_num, iterations_num, portion)
            iterations_num += jump
            iteration_regrets[portion] += split_cfr_exploitability

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
            split_cfr_exp = get_split_cfr_exploitabilty(defender_budget, attacker_budgets, network, step_order_size,
                             max_order_num, iterations_num, main_game_iteration_portion)
            vanilla_cfr_exp = get_vanilla_cfr_exp(defender_budget, attacker_budgets, network, step_order_size, max_order_num, iterations_num)
            iteration_regrets[iterations_num]['split'] += split_cfr_exp
            iteration_regrets[iterations_num]['vanilla'] += vanilla_cfr_exp
            iterations_num += jump

    for it_num in iteration_regrets.keys():
        regrets.append({'num_iterations':it_num,'split_cfr_exp':iteration_regrets[it_num]['split']/ num_exp,
                        'vanilla_cfr_exp': iteration_regrets[it_num]['vanilla']/num_exp})

    with open(res_dir + 'exploitability.csv','w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['num_iterations','vanilla_cfr_exp','split_cfr_exp'])
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
                  'main_game_iteration_portion': 0.8,
                  'min_iterations': 10,
                  'max_iterations': 100,
                  'jump': 10,
                  'num_assets': 3,
                  'step_order_size': SysConfig.get("STEP_ORDER_SIZE")*2,
                  'max_order_num': 1}

    with open(res_dir+'params.json', 'w') as fp:
        json.dump(exp_params, fp)
    iteration_stats_csv(res_dir=res_dir,
                        defender_budget=exp_params['defender_budget'],
                        attacker_budgets=exp_params['attacker_budgets'],
                        main_game_iteration_portion=exp_params['main_game_iteration_portion'],
                        min_iterations=exp_params['min_iterations'],
                        max_iterations=exp_params['max_iterations'],
                        jump=exp_params['jump'],
                        num_assets=exp_params['num_assets'],
                        step_order_size=exp_params['step_order_size'],
                        max_order_num=exp_params['max_order_num'])

    #compute_node_size_csv(res_dir=res_dir,  max_num_attackers = 4, max_num_portfolios = 4, portfolio_size = 10)
  #  count_game_nodes_csv(res_dir=res_dir, defender_budget=exp_params['defender_budget'],
  #                      attacker_budgets=exp_params['attacker_budgets'],
  #                      max_num_assets = 5)



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



