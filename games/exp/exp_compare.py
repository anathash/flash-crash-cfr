import csv
import datetime
import os
from math import ceil, floor

from jsonpickle import json
from numpy import random, mean

from SysConfig import SysConfig
from cfr import VanillaCFR
from exp.exp_common import setup_dir
from exp.network_generators import gen_new_network
from exp.root_generators import FlashCrashRootGenerator, SearchRootGenerator
from split_game_cfr import SplitGameCFR


def run_exp_cmp_iterations(root_generator, res_dir, params,
                               min_iterations, max_iterations, jump, game_size, game_name):

    fieldnames = ['nodes allocated', 'complete game iterations',
                  'split game iterations', 'split_exploitability', 'complete_exploitability']

    file_name = res_dir + game_name + '_exp_cmp' + '_' + str(game_size)+ '_' + str(params['attacker_budgets'])+'.csv'
    with open(file_name,'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    complete_iterations = min_iterations
    while complete_iterations <= max_iterations:

        print('Generating Roots')
        root_generator.gen_roots(game_size)
        print('Done Generating Roots')

        nodes_allocated = root_generator.get_complete_game_root().tree_size * complete_iterations
        split_overall_nodes_num = root_generator.get_split_main_game_root().tree_size + 1 + \
                                  len(params['attacker_budgets']) + \
                                  sum([len(v) for k, v, in root_generator.get_attack_costs().items()])
        print('split_overall_nodes_num:' + str(split_overall_nodes_num))
        print('complete_overall_nodes_num:' + str(root_generator.get_complete_game_root().tree_size))

        split_iterations = int(ceil(nodes_allocated / split_overall_nodes_num))

        print('complete_iterations:' + str(complete_iterations))
        print("nodes allocated:" + str(nodes_allocated))
        print('split_iterations:' + str(split_iterations))


        complete_cfr = VanillaCFR(root_generator.get_complete_game_root())
        complete_cfr.run( round = 0, iterations = complete_iterations)
        complete_cfr.compute_nash_equilibrium()

        print('Generating Roots')
        root_generator.gen_roots(game_size)
        print('Done Generating Roots')

        split_cfr = VanillaCFR(root_generator.get_complete_game_root())
        split_cfr.run( round = 0, iterations = split_iterations)
        split_cfr.compute_nash_equilibrium()
        complete_exploitability = complete_cfr.get_exploitability()
        split_exploitability = split_cfr.get_exploitability()
        row = {'nodes allocated': nodes_allocated,
               'complete game iterations': complete_iterations,
               'split game iterations': split_iterations,
               'complete_exploitability':complete_exploitability,
               'split_exploitability':split_exploitability}

        with open(file_name, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow(row)

        complete_iterations += jump

    return res_dir


def run_search_exp_cmp_nodes(game_size, attacker_budgets, binary):
    res_dir = setup_dir('search')
    exp_params = {'game_size': game_size,
                  'attacker_budgets': attacker_budgets,
                  'binary':binary}

    #2500000
    root_generator = SearchRootGenerator(exp_params)

    run_exp_cmp_iterations(root_generator=root_generator,
                          res_dir=res_dir,
                          params =exp_params,
                          min_iterations=10,
                          max_iterations=102,
                          jump=10,
                          game_size=exp_params['game_size'],
                          game_name='search')

    return




def search_utility_exp():
    run_search_exp_cmp_nodes(5, [3, 5], True)
    run_search_exp_cmp_nodes(5, [3, 11], True)
    run_search_exp_cmp_nodes(5, [5, 11], True)
    run_search_exp_cmp_nodes(5, [3, 5, 11], True)
    run_search_exp_cmp_nodes(6, [3, 5], True)
    run_search_exp_cmp_nodes(6, [3, 11], True)
    run_search_exp_cmp_nodes(6, [5, 11], True)
    run_search_exp_cmp_nodes(6, [3, 5, 11], True)



def run_fc_utility_cmp_nodes(game_size, attacker_budgets, net_type, trees_dir):
    res_dir = setup_dir('flash_crash')
    filename = trees_dir + '/fc_tree_' + str(game_size) + '_' + \
               str(attacker_budgets) + '_' + net_type + '.json'
    exp_params = {'trees_file': filename, 'attacker_budgets':attacker_budgets,'game_size':game_size}
    root_generator = FlashCrashRootGenerator(exp_params)


    run_exp_cmp_iterations(root_generator=root_generator,
                                     res_dir=res_dir,
                                     params=exp_params,
                                     min_iterations=10,
                                     max_iterations=102,
                                     jump=10,
                                     game_size=game_size,
                                     game_name='flash_crash')



def run_fc_experiments_real_assets(trees_dir):
    net_type = 'paper'
    asset1_single_attack = 1400000000
    asset2_single_attack = 2200000000
    asset3_single_attack = 2400000000

    budget1 = asset1_single_attack
    budget2 = asset2_single_attack
    budget3 = asset3_single_attack
    budget4 = asset1_single_attack + asset2_single_attack
    budget5 = asset1_single_attack + asset3_single_attack
    budget6 = asset2_single_attack + asset3_single_attack
    budget7 = asset1_single_attack + asset2_single_attack + asset3_single_attack

#    run_fc_utility_cmp_nodes(game_size=3, attacker_budgets=[budget4, budget5], net_type=net_type, trees_dir=trees_dir)
    run_fc_utility_cmp_nodes(game_size=3, attacker_budgets=[budget4, budget6], net_type=net_type, trees_dir=trees_dir)
    run_fc_utility_cmp_nodes(game_size=3, attacker_budgets=[budget4, budget7], net_type=net_type, trees_dir=trees_dir)

#    run_fc_utility_cmp_nodes(game_size=3, attacker_budgets=[budget5, budget6], net_type=net_type, trees_dir= trees_dir)
#    run_fc_utility_cmp_nodes(game_size=3, attacker_budgets=[budget5, budget7], net_type=net_type,
    #                         trees_dir=trees_dir)

 #   run_fc_utility_cmp_nodes(game_size=3, attacker_budgets=[budget6, budget7], net_type=net_type,
        #                     trees_dir=trees_dir)

  #  run_fc_utility_cmp_nodes(game_size=3, attacker_budgets=[budget5, budget6, budget7], net_type=net_type,
       #                      trees_dir=trees_dir)

   # run_fc_utility_cmp_nodes(game_size=3, attacker_budgets=[budget4, budget6, budget7], net_type=net_type,
      #                       trees_dir=trees_dir)
    #run_fc_utility_cmp_nodes(game_size=3, attacker_budgets=[budget4, budget5, budget7], net_type=net_type,
     #                        trees_dir=trees_dir)
    #run_fc_utility_cmp_nodes(game_size=3, attacker_budgets=[budget4, budget5, budget6], net_type=net_type, trees_dir= trees_dir)



if __name__ == "__main__":
   # search_utility_exp()
    trees_dir = '../../results/stats/flash_crash/lab_pc/2020-12-09/trees_2156000000.0/'
    run_fc_experiments_real_assets(trees_dir)



#    run_search_utility_cmp_nodes(6, [3, 11])
#    run_search_utility_cmp_nodes(6, [3, 5, 11])
#    run_search_utility_cmp_nodes(6, [3, 4, 5, 11])
#    run_search_utility_cmp_nodes(6, [3, 4, 5, 8, 11])
#    run_search_utility_cmp_nodes(6, [3, 4, 5, 6, 8, 11])
#    run_search_utility_cmp_nodes(6, [3, 4, 5, 6, 7, 8, 11])
#    run_search_utility_cmp_nodes(6, [3, 4, 5, 6, 7, 8, 9, 11])
#    run_search_utility_cmp_nodes(6, [3, 4, 5, 6, 7, 8, 9, 11])

    #run_fc_utility_cmp_nodes(4)
