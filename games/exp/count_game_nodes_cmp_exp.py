import csv
import json
import os
from datetime import datetime
from math import ceil

from SysConfig import SysConfig
from exp.network_generators import gen_new_network
from exp.root_generators import FlashCrashRootGenerator, SearchRootGenerator
from flash_crash_players_cfr import FlashCrashRootChanceGameState
from flash_crash_players_portfolio_cfr import PortfolioFlashCrashRootChanceGameState
from flash_crash_players_portfolio_per_attacker_cfr import PPAFlashCrashRootChanceGameState
from ActionsManager import ActionsManager
from split_game_cfr import SplitGameCFR
from split_selector_game import SelectorRootChanceGameState
from vanilla_cfr_runner import compute_cfr_equilibrium


def count_split_game_nodes(params, root_generator):
    dummy_utilities = {pid: 0 for pid in root_generator.get_attack_keys()}
    p_selector_root = SelectorRootChanceGameState(params['attacker_budgets'], dummy_utilities,
                                                  root_generator.get_attack_costs())
    return root_generator.split_root.tree_size + p_selector_root.tree_size



def count_game_nodes_csv(root_generator, res_dir,  game_size_range, params, game_name, game_size_fields_name):
    results = []
    for i in game_size_range:
        print('game size = ' + str(i))
        root_generator.gen_roots(i)
        print(str(datetime.now()) + ': split')
        split = count_split_game_nodes(params, root_generator)
        print(str(datetime.now()) + ': complete')
        vanilla = root_generator.complete_root.tree_size

        results.append({game_size_fields_name: str(i), 'vanilla_cfr': vanilla, 'split_cfr': split})

    with open(res_dir + game_name + '_count_game_nodes.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[game_size_fields_name,'vanilla_cfr','split_cfr'])
        writer.writeheader()
        for row in results:
            writer.writerow(row)

def setup_dir(game_name):
    dt = datetime.today()
    dt = str(dt).split(' ')[0]
    res_dir = '../../results/stats/' + game_name + '/' + dt.replace(":", "_").replace(" ", "_") + '/'
    if not os.path.exists(res_dir):
        os.mkdir(res_dir)

    return res_dir


def count_flash_crash_game_nodes():
#    dt = datetime.today()
#    dt = str(dt).split(' ')[0]
#    res_dir = '../../results/stats/' + dt.replace(":", "_").replace(" ", "_") + '/'
 #   if not os.path.exists(res_dir):
 #       os.mkdir(res_dir)
    res_dir = setup_dir('flash_crash')
    exp_params = {'defender_budget': 2000000000,
                  'attacker_budgets': [4000000000, 6000000000],
                  'step_order_size': SysConfig.get("STEP_ORDER_SIZE"),
                  'max_order_num': 1}

    root_generator = FlashCrashRootGenerator(exp_params)
    count_game_nodes_csv(root_generator=root_generator, res_dir=res_dir,game_size_range = range(3,6), params=exp_params,
                         game_name='flash_crash',
                         game_size_fields_name ='num_assets')



def count_search_game_nodes():
    res_dir=setup_dir('search')
    exp_params = {'attacker_budgets':  [4,5,11]}
    root_generator = SearchRootGenerator(exp_params)
    count_game_nodes_csv(root_generator=root_generator, res_dir=res_dir, game_size_range=range(3, 6), params=exp_params,
                         game_name='search',
                         game_size_fields_name='rounds')


if __name__ == "__main__":
    count_flash_crash_game_nodes()
    #count_search_game_nodes()




