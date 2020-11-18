import csv
import datetime
from math import ceil, floor

from jsonpickle import json
from numpy import random, mean

from SysConfig import SysConfig
from cfr import VanillaCFR
from exp.exp_common import setup_dir
from exp.root_generators import FlashCrashRootGenerator, SearchRootGenerator
from split_game_cfr import SplitGameCFR


class Player:

    def get_next_action(self, inf_set):
        raise NotImplementedError

    def get_subgame_root(self):
        raise NotImplementedError

    def select_action_from_strategy(self, cfr, inf_set):
        raise NotImplementedError


class SplitPlayer(Player):
    def __init__(self, selection_cfr, main_cfr, selection_root, main_root):
        self.selection_cfr = selection_cfr
        self.main_cfr = main_cfr
        self.selection_root = selection_root
        self.main_game_root = main_root
        self.attacker_type = None
#        main_cfr.fix_attackers_eq(selection_root.children.keys())


    def select_action_from_strategy(self, cfr, inf_set):
        if self.attacker_type:
            strategy = cfr.nash_equilibrium[inf_set][self.attacker_type]
        else:
            strategy = cfr.nash_equilibrium[inf_set]
        return random.choice(list(strategy.keys()), p=list(strategy.values()))

    def get_next_action(self, inf_set):
        return self.select_action_from_strategy(self.main_cfr, inf_set)

    def get_subgame_root(self):
        nature_choice = self.select_action_from_strategy(self.selection_cfr, '.')
        attacker_root = self.selection_root.children[nature_choice]
        subgame_action = self.select_action_from_strategy(self.selection_cfr, attacker_root.inf_set())
        self.attacker_type = int(nature_choice)
        return nature_choice, self.main_game_root.children[subgame_action]


class CompletePlayer(Player):
    def __init__(self, cfr, root):
        self.cfr = cfr
        self.root = root

    def select_action_from_strategy(self, cfr, inf_set):
        strategy = cfr.nash_equilibrium[inf_set]
        return random.choice(list(strategy.keys()), p=list(strategy.values()))

    def get_next_action(self, inf_set):
        return self.select_action_from_strategy(self.cfr, inf_set)

    def get_subgame_root(self):
        nature_action = self.select_action_from_strategy(self.cfr,'.')
        attacker_root = self.root.children[nature_action]
        subgame_action = self.select_action_from_strategy(self.cfr, attacker_root.inf_set())
        return nature_action, attacker_root.children[subgame_action]

def run_game(node, attacker, defender):
    while not node.is_terminal():
            attacker_action = attacker.get_next_action(node.inf_set())
            defender_node = node.children[attacker_action]
            defender_action = defender.get_next_action(defender_node.inf_set())
            chance_node = defender_node.children[defender_action]
            #market or grid
            if chance_node.is_terminal():
                node = chance_node
            else:
                market_action = defender.get_next_action(chance_node.inf_set())
                node = chance_node.children[market_action]



    return node.evaluation()


def run_game_iteration_old(complete_root, complete_cfr,
                       split_selection_root, split_selection_cfr,
                       split_main_root, split_main_cfr,
                       attacker_alg):
    if attacker_alg == 'SPLIT':
        attacker = SplitPlayer(split_selection_cfr, split_main_cfr, split_selection_root, split_main_root)
        defender = CompletePlayer(complete_cfr, complete_root)

    else:
        defender = SplitPlayer(split_selection_cfr, split_main_cfr, split_selection_root, split_main_root)
        attacker = CompletePlayer(complete_cfr, complete_root)

    node = attacker.get_subgame_root()

    return run_game(node, attacker, defender )

def run_game_iteration(complete_root, complete_cfr,
                       split_selection_root, split_selection_cfr,
                       split_main_root, split_main_cfr,
                       attacker_alg, defender_alg):

    if attacker_alg == 'SPLIT':
        attacker = SplitPlayer(split_selection_cfr, split_main_cfr, split_selection_root, split_main_root)
    else:
        attacker = CompletePlayer(complete_cfr, complete_root)

    if defender_alg == 'SPLIT':
        defender = SplitPlayer(split_selection_cfr, split_main_cfr, split_selection_root, split_main_root)
    else:
        defender = CompletePlayer(complete_cfr, complete_root)


    attcker_type, node = attacker.get_subgame_root()

    return attcker_type, run_game(node, attacker, defender)


def run_game_iterations(complete_root, complete_cfr,
                       split_selection_root, split_selection_cfr,
                       split_main_root, split_main_cfr,
                       attacker_alg, defender_alg, attacker_types,  rounds = 100000):
    value_sum = {str(x):[] for x in attacker_types}
    value_sum.update({'defender' : []})
    for i in range(0,rounds):
        attacker_type, value = run_game_iteration(complete_root, complete_cfr,
                       split_selection_root, split_selection_cfr,
                       split_main_root, split_main_cfr,
                       attacker_alg, defender_alg)
        value_sum['defender'].append(value)
        value_sum[str(attacker_type)].append(value)
    avg_value = {k: mean(v) for k,v in value_sum.items()}
    return avg_value


def run_sanity_iterations(attacker_root, defender_root, attacker_complete_cfr,
                          defender_complete_cfr, attacker_types, rounds = 1000):

    value_sum = {str(x):[] for x in attacker_types}
    value_sum.update({'defender' : []})
    for i in range(0,rounds):
        attacker = CompletePlayer(attacker_complete_cfr, attacker_root)
        defender = CompletePlayer(defender_complete_cfr, defender_root)
        attacker_type, node = attacker.get_subgame_root()
        value = run_game(node, attacker, defender)
        value_sum['defender'].append(value)
        value_sum[attacker_type].append(value)
    avg_value = {k: mean(v) for k, v in value_sum.items()}
    return avg_value

def get_complete_game_cfr(root_generator, time_allocated):
    vanilla_cfr = VanillaCFR(root_generator.get_complete_game_root())
    iterations = vanilla_cfr.run_with_time_limit(time_allocated)
    return vanilla_cfr, iterations


def get_split_cfr(params, root_generator, time_allocated):
    split_game_cfr = SplitGameCFR()
    root = root_generator.get_split_main_game_root()

    return split_game_cfr.run_with_time_limit(time_limit=time_allocated, main_game_root=root,  attacker_types=params['attacker_budgets'],
                                     attacks_in_budget_dict=root_generator.get_attack_costs(),
                                     subgame_keys=root_generator.get_attack_keys())

def run_utility_cmp(root_generator, res_dir, params,
                        min_time, max_time, jump, game_size, game_name):

    fieldnames = ['time allocated', 'attacker algorithm', 'defender algorithm', 'complete game iterations',
                  'split game iterations', 'expected utility']

    file_name = res_dir + game_name + '_utility_cmp' + '_' + str(game_size)+'.csv'
    with open(file_name,'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    time_allocated = min_time
    root_generator.gen_roots(game_size)

    settings = [{'attacker_alg': 'COMPLETE', 'defender_alg': 'COMPLETE'},
                {'attacker_alg': 'SPLIT', 'defender_alg': 'SPLIT'},
                {'attacker_alg': 'COMPLETE', 'defender_alg': 'SPLIT'},
                {'attacker_alg': 'SPLIT', 'defender_alg': 'COMPLETE'},
               ]

    while time_allocated <= max_time:
        main_game_results, selector_game_result = get_split_cfr(params, root_generator, time_allocated)
        complete_cfr, complete_iterations = get_complete_game_cfr(root_generator, time_allocated)
        for setting in settings:
            utility = run_game_iterations(complete_root=root_generator.get_complete_game_root(),
                                          complete_cfr=complete_cfr,
                                          split_selection_root=selector_game_result['root'],
                                          split_selection_cfr=selector_game_result['cfr'],
                                          split_main_root=root_generator.get_split_main_game_root(),
                                          split_main_cfr=main_game_results['cfr'],
                                          attacker_alg=setting['attacker_alg'],
                                          defender_alg=setting['defender_alg'],
                                          rounds=1000)

            row = {'time allocated': time_allocated,
                   'attacker algorithm': setting['attacker_alg'],
                   'defender algorithm': setting['defender_alg'],
                   'complete game iterations': complete_iterations,
                   'split game iterations': 1 + main_game_results['iterations'],
                   'expected utility': utility}

            with open(file_name, 'a', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow(row)

        time_allocated += jump

    return res_dir


def run_utility_cmp_nodes_iterations(root_generator, res_dir, params,
                        min_nodes, max_nodes, jump, game_size, game_name, ratio):

    fieldnames = ['nodes allocated', 'attacker algorithm', 'defender algorithm', 'attacker game iterations',
                  'defender game iterations', 'defender utility']
    num_attacker = len(params['attacker_budgets'])
    for a in params['attacker_budgets']:
        fieldnames.append('attacker ' + str(a) + ' utility')

    file_name = res_dir + game_name + '_utility_cmp' + '_' + str(game_size)+'.csv'
    with open(file_name,'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    nodes_allocated = min_nodes


    settings = [{'attacker_alg': 'SPLIT', 'defender_alg': 'SPLIT'},
                {'attacker_alg': 'COMPLETE', 'defender_alg': 'COMPLETE'},
                {'attacker_alg': 'COMPLETE2', 'defender_alg': 'COMPLETE'},
                {'attacker_alg': 'COMPLETE', 'defender_alg': 'COMPLETE2'},
                {'attacker_alg': 'COMPLETE', 'defender_alg': 'SPLIT'},
                {'attacker_alg': 'SPLIT', 'defender_alg': 'COMPLETE'}]
    print('Generating Roots')
    root_generator.gen_roots(game_size)
    print('Done Generating Roots')

    nodes_allocated = root_generator.get_complete_game_root().tree_size * 100
    print(nodes_allocated)
    jump = nodes_allocated
    max_nodes = jump*10
    while nodes_allocated <= max_nodes:
        split_game_cfr = SplitGameCFR()
        split_overall_nodes_num = root_generator.get_split_main_game_root().tree_size + 1 + \
                                  len(params['attacker_budgets']) + \
                                  sum([len(v) for k, v, in root_generator.get_attack_costs().items()])



        split_iterations = int(floor(nodes_allocated / split_overall_nodes_num))
     #   nodes_allocated = int(split_iterations/ split_overall_nodes_num)
        print(root_generator.get_complete_game_root().tree_size)
        print("nodes allocated:" + str(nodes_allocated))
        print(nodes_allocated  / root_generator.get_complete_game_root().tree_size )
        complete_iterations = int(floor(nodes_allocated/root_generator.get_complete_game_root().tree_size ))
        print('complete_iterations:' + str(complete_iterations))
        complete_cfr = VanillaCFR(root_generator.get_complete_game_root())
        complete_cfr.run( round = 0, iterations = complete_iterations)
        complete_cfr.compute_nash_equilibrium()

        print('complete_iterations_2:' + str(complete_iterations*2))
        complete_cfr2 = VanillaCFR(root_generator.get_complete_game_root())
        complete_cfr2.run( round = 0, iterations = complete_iterations*2)
        complete_cfr2.compute_nash_equilibrium()


        print('split_iterations:' + str(split_iterations))
        params['iterations'] = split_iterations
        (main_game_cfr, selector_cfr) = split_game_cfr.run_split_cfr(root_generator, params)
        selector_game_result = split_game_cfr.get_selector_stats(main_game_cfr, selector_cfr, split_iterations,
                                                                 params['attacker_budgets'],
                                                                 root_generator.get_attack_costs())
        main_game_results = split_game_cfr.get_main_results_stats(main_game_cfr, params['iterations'])

        for setting in settings:
            print(setting)
            if setting['attacker_alg'] == 'COMPLETE2':
                attacker_iterations = complete_iterations*2
                defender_iterations  = complete_iterations
                utilities= run_sanity_iterations(complete_root=root_generator.get_complete_game_root(),
                                          attacker_complete_cfr=complete_cfr,
                                          defender_complete_cfr=complete_cfr2,
                                          attacker_types=params['attacker_budgets'])
            elif setting['defender_alg'] == 'COMPLETE2':
                attacker_iterations = complete_iterations
                defender_iterations = complete_iterations*2

                utilities =run_sanity_iterations(complete_root=root_generator.get_complete_game_root(),
                                          attacker_complete_cfr=complete_cfr,
                                          defender_complete_cfr=complete_cfr2,
                                          attacker_types=params['attacker_budgets'])

            else:
                if setting['attacker_alg'] == 'COMPLETE':
                    attacker_iterations = complete_iterations
                    defender_iterations = split_iterations
                else:
                    attacker_iterations = split_iterations
                    defender_iterations = complete_iterations

                utilities = run_game_iterations(complete_root=root_generator.get_complete_game_root(),
                                              complete_cfr=complete_cfr,
                                              split_selection_root=selector_game_result['root'],
                                              split_selection_cfr=selector_game_result['cfr'],
                                              split_main_root=root_generator.get_split_main_game_root(),
                                              split_main_cfr=main_game_results['cfr'],
                                              attacker_alg=setting['attacker_alg'],
                                              defender_alg = setting['defender_alg'],
                                              attacker_types=  params['attacker_budgets'],
                                                rounds=1000)

            row = {'nodes allocated': nodes_allocated,
                   'attacker algorithm': setting['attacker_alg'],
                   'defender algorithm': setting['defender_alg'],
                   'attacker game iterations': attacker_iterations,
                   'defender game iterations': defender_iterations,
                   'defender utility': utilities['defender']}
            for a in params['attacker_budgets']:
                k = 'attacker ' + str(a) + ' utility'
                row.update({k: utilities[str(a)]})

            with open(file_name, 'a', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow(row)

        nodes_allocated += jump

    return res_dir



def run_utility_cmp_iterations(root_generator, res_dir, params,
                               min_iterations, max_iterations, jump, game_size, game_name, ratio):

    fieldnames = ['nodes allocated', 'attacker algorithm', 'defender algorithm', 'attacker game iterations',
                  'defender game iterations', 'defender utility']
    for a in params['attacker_budgets']:
        fieldnames.append('attacker ' + str(a) + ' utility')

    file_name = res_dir + game_name + '_utility_cmp' + '_' + str(game_size)+'.csv'
    with open(file_name,'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    settings = [#{'attacker_alg': 'SPLIT', 'defender_alg': 'SPLIT'},
                {'attacker_alg': 'COMPLETE', 'defender_alg': 'COMPLETE'},
#                {'attacker_alg': 'COMPLETE' + str(ratio), 'defender_alg': 'COMPLETE'},
#                {'attacker_alg': 'COMPLETE', 'defender_alg': 'COMPLETE' + str(ratio)},
                {'attacker_alg': 'COMPLETE', 'defender_alg': 'SPLIT'},
                {'attacker_alg': 'SPLIT', 'defender_alg': 'COMPLETE'}]

    complete_iterations = min_iterations
    while complete_iterations <= max_iterations:

        print('Generating Roots')
        root_generator.gen_roots(game_size)
        print('Done Generating Roots')

        nodes_allocated = root_generator.get_complete_game_root().tree_size * complete_iterations
        split_overall_nodes_num = root_generator.get_split_main_game_root().tree_size + 1 + \
                                  len(params['attacker_budgets']) + \
                                  sum([len(v) for k, v, in root_generator.get_attack_costs().items()])

        split_iterations = int(floor(nodes_allocated / split_overall_nodes_num))

        print('complete_iterations:' + str(complete_iterations))
        print("nodes allocated:" + str(nodes_allocated))
        print('split_iterations:' + str(split_iterations))

        params['iterations'] = split_iterations

        split_game_cfr = SplitGameCFR()
        (main_game_cfr, selector_cfr) = split_game_cfr.run_split_cfr(root_generator, params)
        selector_game_result = split_game_cfr.get_selector_stats(main_game_cfr, selector_cfr, split_iterations,
                                                                 params['attacker_budgets'],
                                                                 root_generator.get_attack_costs())
        main_game_results = split_game_cfr.get_main_results_stats(main_game_cfr, params['iterations'])

#        print(root_generator.get_complete_game_root().tree_size)
#        print(nodes_allocated  / root_generator.get_complete_game_root().tree_size )
 #       complete_iterations = int(floor(nodes_allocated/root_generator.get_complete_game_root().tree_size ))


        complete_cfr = VanillaCFR(root_generator.get_complete_game_root())
        complete_cfr.run( round = 0, iterations = complete_iterations)
        complete_cfr.compute_nash_equilibrium()
        complete_cfr2 = None
 #        print('complete_iterations_'+str(ratio) + ':' + str(complete_iterations*ratio))
 #       complete_cfr2 = VanillaCFR(root_generator.get_complete_game_root())
 #       complete_cfr2.run( round = 0, iterations = complete_iterations*ratio)
 #       complete_cfr2.compute_nash_equilibrium()


        for setting in settings:
            print(setting)
            if setting['attacker_alg'] == 'COMPLETE'+str(ratio):
                attacker_iterations = complete_iterations*ratio
                defender_iterations  = complete_iterations
                utilities= run_sanity_iterations(attacker_root=root_generator.get_complete_game_root(),
                                                 defender_root=root_generator.get_complete_game_root(),
                                          attacker_complete_cfr=complete_cfr2,
                                          defender_complete_cfr=complete_cfr,
                                          attacker_types=params['attacker_budgets'])
            elif setting['defender_alg'] == 'COMPLETE'+str(ratio):
                attacker_iterations = complete_iterations
                defender_iterations = complete_iterations*ratio

                utilities =run_sanity_iterations(attacker_root=root_generator.get_complete_game_root(),
                                                 defender_root=root_generator.get_complete_game_root(),
                                          attacker_complete_cfr=complete_cfr,
                                          defender_complete_cfr=complete_cfr2,
                                          attacker_types=params['attacker_budgets'])

            else:
                if setting['attacker_alg'] == 'COMPLETE':
                    attacker_iterations = complete_iterations
                    defender_iterations = split_iterations
                else:
                    attacker_iterations = split_iterations
                    defender_iterations = complete_iterations

                utilities = run_game_iterations(complete_root=root_generator.get_complete_game_root(),
                                              complete_cfr=complete_cfr,
                                              split_selection_root=selector_game_result['root'],
                                              split_selection_cfr=selector_game_result['cfr'],
                                              split_main_root=root_generator.get_split_main_game_root(),
                                              split_main_cfr=main_game_results['cfr'],
                                              attacker_alg=setting['attacker_alg'],
                                              defender_alg = setting['defender_alg'],
                                              attacker_types=  params['attacker_budgets'],
                                                rounds=1000)

            row = {'nodes allocated': nodes_allocated,
                   'attacker algorithm': setting['attacker_alg'],
                   'defender algorithm': setting['defender_alg'],
                   'attacker game iterations': attacker_iterations,
                   'defender game iterations': defender_iterations,
                   'defender utility': utilities['defender']}
            for a in params['attacker_budgets']:
                k = 'attacker ' + str(a) + ' utility'
                row.update({k: utilities[str(a)]})

            with open(file_name, 'a', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow(row)

        complete_iterations += jump

    return res_dir


def run_sanity_cmp_iterations(root_generator, res_dir, params,
                               min_iterations, max_iterations, jump, game_size, game_name, ratio):

    fieldnames = ['nodes allocated', 'attacker algorithm', 'defender algorithm', 'attacker game iterations',
                  'defender game iterations', 'defender utility']
    num_attacker = len(params['attacker_budgets'])
    for a in params['attacker_budgets']:
        fieldnames.append('attacker ' + str(a) + ' utility')

    file_name = res_dir + game_name + '_utility_cmp' + '_' + str(game_size)+'.csv'
    with open(file_name,'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()



    settings = [
                {'attacker_alg': 'COMPLETE' + str(ratio), 'defender_alg': 'COMPLETE'},
                {'attacker_alg': 'COMPLETE', 'defender_alg': 'COMPLETE' + str(ratio)}]


    #nodes_allocated = root_generator.get_complete_game_root().tree_size * 100
    #print(nodes_allocated)

    #jump = nodes_allocated
    #max_nodes = jump*10

    completer_iterations = min_iterations
    while completer_iterations <= max_iterations:
        print('Generating Roots')
        root_generator.gen_roots(game_size)
        root1 = root_generator.get_complete_game_root()
        root2 = root_generator.complete_root2

        print('Done Generating Roots')

        nodes_allocated = root1.tree_size * completer_iterations
        complete_iterations = int(floor(nodes_allocated/root1.tree_size ))
        complete_cfr = VanillaCFR(root1)
        complete_cfr.run( round = 0, iterations = complete_iterations)
        complete_cfr.compute_nash_equilibrium()

        print('complete_iterations_'+str(ratio) + ':' + str(complete_iterations*ratio))
        complete_cfr2 = VanillaCFR(root2)
        complete_cfr2.run( round = 0, iterations = complete_iterations*ratio)
        complete_cfr2.compute_nash_equilibrium()


        for setting in settings:
            print(setting)
            if setting['attacker_alg'] == 'COMPLETE'+str(ratio):
                attacker_iterations = complete_iterations*ratio
                defender_iterations  = complete_iterations
                utilities= run_sanity_iterations(attacker_root=root2,
                                                 defender_root=root1,
                                          attacker_complete_cfr=complete_cfr2,
                                          defender_complete_cfr=complete_cfr,
                                          attacker_types=params['attacker_budgets'])
            elif setting['defender_alg'] == 'COMPLETE'+str(ratio):
                attacker_iterations = complete_iterations
                defender_iterations = complete_iterations*ratio

                utilities =run_sanity_iterations(attacker_root=root1,
                                                 defender_root=root2,
                                          attacker_complete_cfr=complete_cfr,
                                          defender_complete_cfr=complete_cfr2,
                                          attacker_types=params['attacker_budgets'])

            row = {'nodes allocated': nodes_allocated,
                   'attacker algorithm': setting['attacker_alg'],
                   'defender algorithm': setting['defender_alg'],
                   'attacker game iterations': attacker_iterations,
                   'defender game iterations': defender_iterations,
                   'defender utility': utilities['defender']}
            for a in params['attacker_budgets']:
                k = 'attacker ' + str(a) + ' utility'
                row.update({k: utilities[str(a)]})

            with open(file_name, 'a', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow(row)

        completer_iterations += jump

    return res_dir

def run_utility_cmp_nodes(root_generator, res_dir, params,
                           game_size, game_name):

    fieldnames = ['nodes allocated', 'attacker algorithm', 'defender algorithm', 'attacker game iterations',
                  'defender game iterations', 'defender utility']
    num_attacker = len(params['attacker_budgets'])
    for a in params['attacker_budgets']:
        fieldnames.append('attacker ' + str(a) + ' utility')

    file_name = res_dir + game_name + '_utility_cmp' + '_' + str(game_size)+'.csv'
    with open(file_name,'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    settings = [{'attacker_alg': 'SPLIT', 'defender_alg': 'SPLIT'},
  #              {'attacker_alg': 'COMPLETE', 'defender_alg': 'COMPLETE'},
  #              {'attacker_alg': 'COMPLETE2', 'defender_alg': 'COMPLETE'},
  #              {'attacker_alg': 'COMPLETE', 'defender_alg': 'COMPLETE2'},
                {'attacker_alg': 'COMPLETE', 'defender_alg': 'SPLIT'},
                {'attacker_alg': 'SPLIT', 'defender_alg': 'COMPLETE'}]

    root_generator.gen_roots(game_size)
    split_game_cfr = SplitGameCFR()
    split_overall_nodes_num = root_generator.get_split_main_game_root().tree_size + 1 + \
                              num_attacker + \
                              sum([len(v) for k, v, in root_generator.get_attack_costs().items()])


    complete_iterations = 10
    nodes_allocated =  int(complete_iterations * root_generator.get_complete_game_root().tree_size)
    split_iterations = int(nodes_allocated / split_overall_nodes_num)
    #complete_iterations = split_iterations
    print('complete_iterations:' + str(complete_iterations))
    complete_cfr = VanillaCFR(root_generator.get_complete_game_root())
    complete_cfr.run( round = 0, iterations = complete_iterations)
    complete_cfr.compute_nash_equilibrium()

    print('complete_iterations_2:' + str(complete_iterations*5))
    complete_cfr2 = VanillaCFR(root_generator.get_complete_game_root())
    complete_cfr2.run( round = 0, iterations = complete_iterations*5)
    complete_cfr2.compute_nash_equilibrium()


    print('split_iterations:' + str(split_iterations))
    params['iterations'] = split_iterations
    (main_game_cfr, selector_cfr) = split_game_cfr.run_split_cfr(root_generator, params)
    selector_game_result = split_game_cfr.get_selector_stats(main_game_cfr, selector_cfr, split_iterations,
                                                             params['attacker_budgets'],
                                                             root_generator.get_attack_costs())
    main_game_results = split_game_cfr.get_main_results_stats(main_game_cfr, params['iterations'])

    for setting in settings:
        print(setting)
        if setting['attacker_alg'] == 'COMPLETE2':
            attacker_iterations = complete_iterations*2
            defender_iterations  = complete_iterations
            utilities= run_sanity_iterations(complete_root=root_generator.get_complete_game_root(),
                                      attacker_complete_cfr=complete_cfr,
                                      defender_complete_cfr=complete_cfr2,
                                      attacker_types=params['attacker_budgets'],)
        elif setting['defender_alg'] == 'COMPLETE2':
            attacker_iterations = complete_iterations
            defender_iterations = complete_iterations*2

            utilities =run_sanity_iterations(complete_root=root_generator.get_complete_game_root(),
                                      attacker_complete_cfr=complete_cfr,
                                      defender_complete_cfr=complete_cfr2,
                                      attacker_types=params['attacker_budgets'])

        else:
            if setting['attacker_alg'] == 'COMPLETE':
                attacker_iterations = complete_iterations
                defender_iterations = split_iterations
            else:
                attacker_iterations = split_iterations
                defender_iterations = complete_iterations

            utilities = run_game_iterations(complete_root=root_generator.get_complete_game_root(),
                                          complete_cfr=complete_cfr,
                                          split_selection_root=selector_game_result['root'],
                                          split_selection_cfr=selector_game_result['cfr'],
                                          split_main_root=root_generator.get_split_main_game_root(),
                                          split_main_cfr=main_game_results['cfr'],
                                          attacker_alg=setting['attacker_alg'],
                                          defender_alg = setting['defender_alg'],
                                          attacker_types=params['attacker_budgets'],
                                          rounds=1000)

        row = {'nodes allocated': nodes_allocated,
               'attacker algorithm': setting['attacker_alg'],
               'defender algorithm': setting['defender_alg'],
               'attacker game iterations': attacker_iterations,
               'defender game iterations': defender_iterations,
               'defender utility': utilities['defender']}
        for a in params['attacker_budgets']:
            k = 'attacker ' + str(a) + ' utility'
            row.update({k : utilities[str(a)]})

        with open(file_name, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow(row)


    return res_dir


def run_utility_cmp_nodes_sanity(root_generator, res_dir, params,
                        min_nodes, max_nodes, jump, game_size, game_name, rounds = 10000):

    fieldnames = ['defender_iterations', 'attacker_iterations', 'expected utility']

    file_name = res_dir + game_name + '_utility_cmp' + '_' + str(game_size)+'.csv'
    with open(file_name,'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    nodes_allocated = min_nodes


    while nodes_allocated <= max_nodes:
        root_generator.gen_roots(game_size)
        r1 = root_generator.get_complete_game_root()
        c1_it = int(floor(nodes_allocated /root_generator.get_complete_game_root().tree_size))
        c2_it = 2*c1_it
        print('complete_iterations:' + str(c1_it))
        complete_cfr1 = VanillaCFR(r1)
        complete_cfr1.run( round = 0, iterations = c1_it)
        complete_cfr1.compute_nash_equilibrium()

        r2 = root_generator.get_complete_game_root()
        complete_cfr2 = VanillaCFR(r2)
        complete_cfr2.run(round=0, iterations=c2_it)
        complete_cfr2.compute_nash_equilibrium()
        params['iterations'] = c1_it
        roots = [r1,r2]
        cfr = [complete_cfr1, complete_cfr2]
        iterations = [c1_it, c2_it]
        for j in range (0,2):
            value_sum = 0
            for i in range(0, rounds):
                defender = CompletePlayer(cfr[j], roots[j])
                attacker = CompletePlayer(cfr[(j+1)%2], roots[(j+1)%2])
                node = attacker.get_subgame_root()
                value_sum +=run_game(node, attacker, defender)
            avg_value = value_sum / rounds
            row = {
                   'defender_iterations': str(iterations[j]),
                   'attacker_iterations': str(iterations[(j+1)%2]),
                   'expected utility': avg_value}

            with open(file_name, 'a', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow(row)

        nodes_allocated += jump

    return res_dir



def run_fc_utility_cmp():
    res_dir = setup_dir('flash_crash')
    exp_params = {'main_game_iteration_portion': 1.0,
                  'min_iterations': 100,
                  'max_iterations': 1100,
                  'game_size': 3,
                  'jump': 100,
                  'defender_budget': 2000000000,
                  #'attacker_budgets': [4000000000, 6000000000,  8000000000 ],
                  'attacker_budgets': [4000000000, 8000000000,  12000000000],
                  'step_order_size': SysConfig.get("STEP_ORDER_SIZE")*2 ,
                  'max_order_num': 1}

#    with open(res_dir+'params.json', 'w') as fp:
#        json.dump(exp_params, fp)

    root_generator = FlashCrashRootGenerator(exp_params)

    run_utility_cmp(root_generator, res_dir, exp_params,
                    10, 50, 10, exp_params['game_size'], 'flash_crash')


def run_fc_utility_cmp_nodes(game_size):
    res_dir = setup_dir('flash_crash')
    exp_params = {
                  'game_size': game_size,
                  'defender_budget': 400000,
                  #'attacker_budgets': [4000000000,   8000000000],
                  'attacker_budgets': [450000,  600000,  900000],
                  'step_order_size': SysConfig.get("STEP_ORDER_SIZE")*2 ,
                  'max_order_num': 1}

#    with open(res_dir+'params.json', 'w') as fp:
#        json.dump(exp_params, fp)

    root_generator = FlashCrashRootGenerator(exp_params)

   # run_utility_cmp_nodes(root_generator, res_dir, exp_params,exp_params['game_size'], 'flash_crash')
    run_utility_cmp_iterations(root_generator=root_generator,
                                     res_dir=res_dir,
                                     params=exp_params,
                                     min_iterations=1,
                                     max_iterations=100,
                                     jump=10,
                                     game_size=exp_params['game_size'],
                                     game_name='flash_crash',
                                     ratio = 2)

#    run_sanity_cmp_iterations(root_generator=root_generator,
#                                     res_dir=res_dir,
#                                     params=exp_params,
#                                     min_iterations=1,
#                                     max_iterations=1000,
#                                     jump=100,
#                                     game_size=exp_params['game_size'],
#                                     game_name='flash_crash',
#                                     ratio = 10)


def run_search_utility_cmp():
    res_dir = setup_dir('search')
    exp_params = {'main_game_iteration_portion': 1.0,
                  'min_iterations': 100,
                  'max_iterations': 10001,
                  'game_size': 5,
                  'jump': 1000,
                  'attacker_budgets': [4,  11]}


    root_generator = SearchRootGenerator(exp_params)
    run_utility_cmp(root_generator, res_dir, exp_params,
                    100000000, 100000000, 100000000, exp_params['game_size'], 'search')
    return


def run_search_utility_cmp_nodes(game_size):
    res_dir = setup_dir('search')
    exp_params = {'game_size': game_size,
                  'attacker_budgets': [4, 5, 11],
                  'binary':True}

    #2500000
    root_generator = SearchRootGenerator(exp_params)

    run_utility_cmp_iterations(root_generator=root_generator,
    #run_sanity_cmp_iterations(root_generator=root_generator,
                          res_dir=res_dir,
                          params =exp_params,
                          min_iterations=1,
                          max_iterations=100,
                          jump=10,
                          game_size=exp_params['game_size'],
                          game_name='search',
                          ratio = 10)

    return

def search_sanitty():
    res_dir = setup_dir('search')
    exp_params = {'main_game_iteration_portion': 1.0,
                  'min_iterations': 100,
                  'max_iterations': 10001,
                  'game_size': 5,
                  'jump': 1000,
                  'attacker_budgets': [4, 5, 11]}

    root_generator = SearchRootGenerator(exp_params)
    run_utility_cmp_nodes_sanity(root_generator, res_dir, exp_params,
                    1000000, 10000000, 1000000, exp_params['game_size'], 'search')

if __name__ == "__main__":
    run_search_utility_cmp_nodes(5)
    #run_fc_utility_cmp_nodes(4)
