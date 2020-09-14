import csv
from math import ceil

from numpy import random

from cfr import VanillaCFR
from split_game_cfr import SplitGameCFR


class Player:
    @staticmethod
    def select_action_from_strategy(cfr, inf_set):
        sigma = cfr.nash_equilibrium[inf_set]
        return random.choice(sigma.keys(), 1, sigma.values())

    def get_next_action(self, inf_set):
        raise NotImplementedError

    def get_subgame_root(self):
        raise NotImplementedError



class SplitPlayer(Player):
    def __init__(self, selection_cfr, main_cfr, selection_root, main_root):
        self.select__get_subgame_rootion_cfr = selection_cfr
        self.main_cfr = main_cfr
        self.selection_root = selection_root
        self.main_root = main_root

    def get_next_action(self, inf_set):
        return self.select_action_from_strategy(self.main_cfr, inf_set)

    def get_subgame_root(self, root):
        nature_action = self.select_action_from_strategy(self.selection_cfr, '.')
        attacker_root = self.selection_root.children[nature_action]
        subgame_action = self.select_action_from_strategy(self.selection_cfr, attacker_root.inf_set())
        return self.main_game_root.children[subgame_action]


class CompletePlayer:
    def __init__(self, cfr, root):
        self.cfr = cfr
        self.root  = root

    def get_next_action(self, inf_set):
        return self.select_action_from_strategy(self.cfr, inf_set)

    def get_subgame_root(self):
        nature_action = self.select_action_from_strategy(self.cfr,'.')
        attacker_root = self.root.children[nature_action]
        subgame_action = self.select_action_from_strategy(self.cfr, attacker_root.inf_set())
        return self.root.children[subgame_action]


def run_game_iteration(complete_root, complete_cfr,
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

    while not node.is_terminal():
            attacker_action = attacker.get_attacker_action(node.inf_set())
            node = node.children[attacker_action]
            defender_action = defender.get_defender_action(node.inf_set())
            node = node.children[defender_action]
            #market or grid
            defender_action = defender.get_chance_action(node.inf_set())
            node = node.children[defender_action]

    return node.get_value()


def run_game_iterations(complete_root, complete_cfr,
                       split_selection_root, split_selection_cfr,
                       split_main_root, split_main_cfr,
                       attacker_alg, rounds = 1000):
    value_sum = 0
    for i in range(0,rounds):
        value_sum += run_game_iteration(complete_root, complete_cfr,
                       split_selection_root, split_selection_cfr,
                       split_main_root, split_main_cfr,
                       attacker_alg)
    avg_value = value_sum / rounds
    return avg_value


def get_complete_game_cfr(root_generator, time_allocated):
    vanilla_cfr = VanillaCFR(root_generator.complete_game_root)
    iterations = vanilla_cfr.run_with_time_limit(time_allocated)
    return vanilla_cfr, iterations


def get_split_cfr(params, root_generator, time_allocated):
    split_game_cfr = SplitGameCFR()
    root = root_generator.get_split_main_game_root()

    return split_game_cfr.run_with_time_limit(main_game_root=root, time_limit=time_allocated, attacker_types=params['attacker_budgets'],
                                     attacks_in_budget_dict=root_generator.get_attack_costs(),
                                     subgame_keys=root_generator.get_attack_keys())

def run_utility_cmp(root_generator, res_dir, params,
                        min_time, max_time, jump, game_size, game_name):

    fieldnames = ['time_allocated']
    fieldnames.append('attacker algorithm')
    fieldnames.append('defender algorithm')
    fieldnames.append('attacker iterations')
    fieldnames.append('expected_utility')

    file_name = res_dir + game_name + '_utility_cmp' + '_' + str(game_size)+'.csv'
    with open(file_name,'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    time_allocated = min_time
    root_generator.gen_roots(game_size)

    settings = [{'attacker_alg':'SPLIT', 'defender_alg':'COMPLETE'},
               {'attacker_alg': 'COMPLETE', 'defender_alg': 'SPLIT'}]

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
                                          attacker_alg=setting['attacker_alg'], rounds=1000)

            row = {'time_alllocated': time_allocated,
                   'attacker algorithm': setting['attacker_alg'],
                   'defender algorithm': setting['defender_alg'],
                   'complete game iterations': complete_iterations,
                   'split game iterations': 1 + main_game_results['iterations'],
                   'expected_utility': utility}

            with open(file_name, 'a', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow(row)

        time_allocated += jump






