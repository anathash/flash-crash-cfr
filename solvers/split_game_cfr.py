from datetime import datetime
from math import inf

from SysConfig import SysConfig
from cfr import VanillaCFR
from exp.network_generators import get_network_from_dir
from flash_crash_players_portfolio_cfr import PortfolioFlashCrashRootChanceGameState
from ActionsManager import ActionsManager
from split_selector_game import SelectorRootChanceGameState


class SplitGameCFR:

    def compute_main_game_utilities(self, root, sub_game_keys, iterations, time_limit=None):
        vanilla_cfr = VanillaCFR(root)
        if time_limit:
            iterations = vanilla_cfr.run_with_time_limit(time_limit)
        else:
            utilities = vanilla_cfr.run(iterations=iterations)
        t= datetime.now()
    #    vanilla_cfr.compute_nash_equilibrium()
        # generate portfolio utility table
     #   vanilla_cfr.value_of_the_game()
#        utilities = {pid: root.children[pid].get_value() for pid in sub_game_keys}
        cumulative_pos_regret = vanilla_cfr.average_total_imm_regret(iterations)
        print(str((datetime.now() - t).microseconds * 0.000001))
        return {'utilities':utilities,'pos_regret': cumulative_pos_regret, 'exploitability': 2* cumulative_pos_regret,
                'cfr':vanilla_cfr, 'iterations':iterations}


    def compute_game_mixed_equilibrium(self, attacker_types, subgame_utilities, iterations, attacks_in_budget_dict):
        p_selector_root = SelectorRootChanceGameState(attacker_types, subgame_utilities, attacks_in_budget_dict)
        cfr = VanillaCFR(p_selector_root)
        cfr.run(iterations=iterations)
        cfr.compute_nash_equilibrium()
        pids = subgame_utilities.keys()
        nash_eq = {pid:0 for pid in pids}
        sigma = {b:0 for b in attacker_types}
        attackers_eq = {}
        defender_eq = cfr.value_of_the_game()
        for attacker in attacker_types:
            inf_set = ".{0}".format(attacker)
            sigma[attacker] = cfr.sigma[inf_set]
            for pid in attacks_in_budget_dict[attacker]:
                nash_eq[pid] += cfr.nash_equilibrium[inf_set][pid]*1/len(attacker_types)


        for attacker in attacker_types:
            attackers_eq[attacker] = p_selector_root.children[str(attacker)].get_value()
            #regrets[attacker] = cfr.cumulative_regrets[p_selector_root.children[str(attacker)].inf_set()]
            #'regrets':regrets

        cumulative_pos_regret = cfr.average_total_imm_regret(iterations)
        return {'pos_regret': cumulative_pos_regret, 'exploitability': 2* cumulative_pos_regret,
                  'defender':defender_eq, 'attackers':attackers_eq,
                  'portfolios_dist':nash_eq, 'sigma':sigma, 'root':p_selector_root,'cfr':cfr}


    def compute_pure_game_equilibrium(self, attacker_types, subgame_utilities, attacks_in_budget_dict):
        iterations = 1
        p_selector_root = SelectorRootChanceGameState(attacker_types, subgame_utilities, attacks_in_budget_dict)
        cfr = VanillaCFR(p_selector_root)
        for attacker in attacker_types:
            min_utility = inf
            choices = []
            for action in cfr.sigma['.'+str(attacker)].keys():
                if subgame_utilities[action] < min_utility:
                    choices = []
                    min_utility = subgame_utilities[action]
                    choices.append(action)
                elif min_utility == subgame_utilities[action]:
                    choices.append(action)
            num_choices = len(choices)
            for action in cfr.sigma['.'+str(attacker)].keys():
                if subgame_utilities[action] == min_utility:
                    cfr.sigma['.' + str(attacker)][action] = 1/num_choices
                else:
                    cfr.sigma['.' + str(attacker)][action] = 0

        cfr.run(iterations=1)
        cfr.compute_nash_equilibrium()
        pids = subgame_utilities.keys()
        nash_eq = {pid:0 for pid in pids}
        sigma = {b:0 for b in attacker_types}
        attackers_eq = {}
        defender_eq = cfr.value_of_the_game()
        for attacker in attacker_types:
            inf_set = ".{0}".format(attacker)
            sigma[attacker] = cfr.sigma[inf_set]
            for pid in attacks_in_budget_dict[attacker]:
                nash_eq[pid] += cfr.nash_equilibrium[inf_set][pid]*1/len(attacker_types)


        for attacker in attacker_types:
            attackers_eq[attacker] = p_selector_root.children[str(attacker)].get_value()
            #regrets[attacker] = cfr.cumulative_regrets[p_selector_root.children[str(attacker)].inf_set()]
            #'regrets':regrets

        cumulative_pos_regret = cfr.average_total_imm_regret(iterations)
        return {'pos_regret': cumulative_pos_regret, 'exploitability': 2* cumulative_pos_regret,
                  'defender':defender_eq, 'attackers':attackers_eq,
                  'portfolios_dist':nash_eq, 'sigma':sigma,'root':p_selector_root,'cfr':cfr
                }

    def iterate(self, network, defender_budget, game1_iterations, game2_iterations, max_iterations, regret_epsilon):
        network.limit_trade_step = True
        action_mgr = ActionsManager(network.assets, SysConfig.get("STEP_ORDER_SIZE"), 1)
        regret = inf
        total_iterations = 0
        portfolios_dist = action_mgr.uniform_portfolios()
        round_index = 1
        while (total_iterations < max_iterations) and (regret >= regret_epsilon):
            action_mgr.update_portfolios(portfolios_dist)
            results = self.run_split_cfr(action_mgr, network, defender_budget, game1_iterations, game2_iterations, round_index)
            total_iterations += game1_iterations + game2_iterations
            portfolios_dist = results['portfolios_dist']
            regret = results ['cumulative_pos_regret']
            self.print_eq_info(total_iterations, results)
            round_index += 1
        return results

    def print_eq_info(self, total_iterations, results):
        print('run {0} iterations'.format(total_iterations))
        print('cumulative regret is '.format(results['cumulative_regret']))
        print('defender equilibrium value is  '.format(results['defender']))
        print('attackers equilibrium values are  '.format(results['attackers']))

    def run_old(self, action_mgr, network, defender_budget, attacker_budgets, game1_iterations, game2_iterations, round):
        root = PortfolioFlashCrashRootChanceGameState(action_mgr=action_mgr,
                                                      af_network=network,
                                                      defender_budget=defender_budget)
        main_game_results = self.compute_portfolio_utilities(root, round, action_mgr.get_probable_portfolios().keys(), game1_iterations)
        selector_game_result = self.compute_game_equilibrium(attacker_budgets, main_game_results['utilities'], game2_iterations, action_mgr)
        return (main_game_results, selector_game_result)

    def run_split_cfr(self, root_generator, params):
        root = root_generator.get_split_main_game_root()
        iterations = params['iterations']
        return self.run(main_game_root=root,
                                  attacker_types=params['attacker_budgets'],
                                  iterations=iterations,
                                  attacks_in_budget_dict=root_generator.get_attack_costs(),
                                  subgame_keys=root_generator.get_attack_keys())

    def run_old(self, main_game_root, attacker_types, game1_iterations,
            game2_iterations, attacks_in_budget_dict, subgame_keys, game_2_pure):
        main_game_results = self.compute_main_game_utilities(main_game_root, subgame_keys, game1_iterations)
        if game_2_pure:
            selector_game_result = self.compute_pure_game_equilibrium(attacker_types=attacker_types,
                                                                 subgame_utilities=main_game_results['utilities'],
                                                                 attacks_in_budget_dict=attacks_in_budget_dict)
        else:
            selector_game_result = self.compute_game_mixed_equilibrium(attacker_types=attacker_types,
                                                                 subgame_utilities=main_game_results['utilities'],
                                                                 iterations=game1_iterations,
                                                                 attacks_in_budget_dict=attacks_in_budget_dict)

        return (main_game_results, attacker_types, selector_game_result)

    @staticmethod
    def update_probs(split_cfr, subgame_keys, attacker_types):
        probs = {g:0 for g in subgame_keys}
        sigma = split_cfr.sigma
        for attacker_type in attacker_types:
            for g in subgame_keys:
                inf_set = '.' + str(attacker_type)
                if str(g) in sigma[inf_set]:
                    probs[g] += sigma['.'][str(attacker_type)]*sigma[inf_set][str(g)]
        return probs

    @staticmethod
    def get_probs_prefixes(sigma, subgame_keys, attacker_types):
        probs = {k: {} for k in subgame_keys}
        sigma = sigma
        for k in subgame_keys:
            for attacker_type in attacker_types:
                inf_set = '.' + str(attacker_type)
                if str(k) in sigma[inf_set]:
                    probs[k][attacker_type] = sigma['.'][str(attacker_type)] * sigma[inf_set][str(k)]
        return probs

    @staticmethod
    def get_selector_stats(main_game_cfr, selector_cfr, iterations, attacker_types, attacks_in_budget_dict):
        main_game_cfr.compute_nash_equilibrium()
      #  main_game_cfr.value_of_the_game()
        utilities = main_game_cfr.attackers_cfr_utilities()
        #utilities = {x:y.value for x,y in main_game_cfr.root.children.items()}
        p_selector_root = SelectorRootChanceGameState(attacker_types, utilities, attacks_in_budget_dict)
        selector_cfr.root = p_selector_root
        selector_cfr.compute_nash_equilibrium()
        nash_eq = {}
        sigma = {b: 0 for b in attacker_types}
        attackers_eq = {}
        defender_eq = selector_cfr.value_of_the_game()
        for attacker in attacker_types:
            inf_set = ".{0}".format(attacker)
            sigma[attacker] = selector_cfr.sigma[inf_set]
            for pid in attacks_in_budget_dict[attacker]:
                if pid not in nash_eq:
                    nash_eq[pid] = 0
                nash_eq[pid] += selector_cfr.nash_equilibrium[inf_set][pid] * 1 / len(attacker_types)

        for attacker in attacker_types:
            attackers_eq[attacker] = selector_cfr.root.children[str(attacker)].get_value()

        cumulative_pos_regret = selector_cfr.average_total_imm_regret(iterations)
        return {'pos_regret': cumulative_pos_regret, 'exploitability': 2 * cumulative_pos_regret,
                            'defender': defender_eq, 'attackers': attackers_eq,
                            'portfolios_dist': nash_eq, 'sigma': sigma, 'root': selector_cfr.root,
                            'cfr':selector_cfr}

    @staticmethod
    def get_main_results_stats(main_cfr, iterations):
        cumulative_pos_regret = main_cfr.average_total_imm_regret(iterations)
        return  { 'pos_regret': cumulative_pos_regret,
                             'exploitability': 2 * cumulative_pos_regret,
                             'cfr': main_cfr, 'iterations': iterations}


    def run(self, main_game_root, attacker_types, iterations,
             attacks_in_budget_dict, subgame_keys):
        vanilla_cfr = VanillaCFR(main_game_root)
        split_cfr = None
        for i in range(0, iterations):
            if split_cfr:
                probs_prefixes = self.get_probs_prefixes(split_cfr.sigma, subgame_keys, attacker_types)
            else:
                dummy_sigma = {'.': {}}
                for attacker_type in attacker_types:
                    dummy_sigma['.'][str(attacker_type)] = 1 / len(attacker_types)
                    dummy_sigma['.' + str(attacker_type)] = {}
                    num_attacks_in_budget = len(attacks_in_budget_dict[attacker_type])
                    for attack in attacks_in_budget_dict[attacker_type]:
                        dummy_sigma['.' + str(attacker_type)][attack] = 1 / num_attacks_in_budget
                probs_prefixes = self.get_probs_prefixes(dummy_sigma, subgame_keys, attacker_types)
            utilities = vanilla_cfr.run(round = i, iterations=1, probs_prefix=probs_prefixes)
            p_selector_root = SelectorRootChanceGameState(attacker_types, utilities, attacks_in_budget_dict)
            if not split_cfr:
                split_cfr = VanillaCFR(p_selector_root)
            else:
                split_cfr.root = p_selector_root
            split_cfr.run(round = i, iterations=1)
            #set chance node of game
            new_probs = self.update_probs(split_cfr, subgame_keys, attacker_types)
            main_game_root.update_chance_probs(new_probs)
        return vanilla_cfr, split_cfr



    def run_with_time_limit(self, time_limit, main_game_root, attacker_types,
             attacks_in_budget_dict, subgame_keys):
        main_game_results = self.compute_main_game_utilities(root=main_game_root, sub_game_keys=subgame_keys,
                                                             iterations=None, time_limit=time_limit -1)
        t = datetime.now()
#        selector_game_result = self.compute_pure_game_equilibrium(attacker_types=attacker_types,
#                                                                  subgame_utilities=main_game_results['utilities'],
#                                                                  attacks_in_budget_dict=attacks_in_budget_dict)
        selector_game_result = self.compute_game_mixed_equilibrium(attacker_types=attacker_types,
                                                                  subgame_utilities=main_game_results['utilities'],
                                                                  iterations = 1000,
                                                                  attacks_in_budget_dict=attacks_in_budget_dict)

        print(str((datetime.now() - t).microseconds*0.000001))
        return (main_game_results, selector_game_result)


def main():
    defender_budget = 100000000
    attacker_budgets = [400000000, 800000000]
    dirname ='../../../results/three_assets_net/'
    network = get_network_from_dir(dirname)
    #dirname, network = gen_new_network(3, results_dir = '../../../results/')
    network.limit_trade_step = True
    # assets, step_order_size, max_order_num=1, attacker_budgets
    cfr_actions_mgr = ActionsManager(assets=network.assets, step_order_size=SysConfig.get("STEP_ORDER_SIZE"),
                                     max_order_num=1, attacker_budgets=attacker_budgets)
    root = PortfolioFlashCrashRootChanceGameState(action_mgr=cfr_actions_mgr,
                                                  af_network=network,
                                                  defender_budget=defender_budget)
    split_game_cfr = SplitGameCFR()

    split_game_cfr.run(main_game_root = root, attacker_types=attacker_budgets,
                       attack_costs= cfr_actions_mgr.get_probable_portfolios().keys(),
                       game1_iterations=200,
                       game2_iterations=800,
                       attacks_in_budget_dict = cfr_actions_mgr.get_portfolios_in_budget_dict())


if __name__ == "__main__":
    main()

