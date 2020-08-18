from math import inf

from SysConfig import SysConfig
from cfr import VanillaCFR
from exp.network_generators import get_network_from_dir
from flash_crash_players_portfolio_cfr import PortfolioFlashCrashRootChanceGameState
from ActionsManager import ActionsManager
from split_selector_game import SelectorRootChanceGameState


class SplitGameCFR:

    def compute_main_game_utilities(self, root, sub_game_keys, iterations):
        vanilla_cfr = VanillaCFR(root)
        vanilla_cfr.run(iterations=iterations)
        vanilla_cfr.compute_nash_equilibrium()
        # generate portfolio utility table
        vanilla_cfr.value_of_the_game()
        utilities = {pid: root.children[pid].get_value() for pid in sub_game_keys}
        cumulative_pos_regret = vanilla_cfr.average_total_imm_regret(iterations)
        return {'utilities':utilities,'pos_regret': cumulative_pos_regret, 'exploitability': 2* cumulative_pos_regret}



    def compute_game_mixed_equilibrium(self, attacker_types, subgame_utilities, iterations, attacks_in_budget_dict):
        p_selector_root = SelectorRootChanceGameState(attacker_types, subgame_utilities, attacks_in_budget_dict)
        cfr = VanillaCFR(p_selector_root)
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
                  'portfolios_dist':nash_eq, 'sigma':sigma}


    def compute_pure_game_equilibrium(self, attacker_types, subgame_utilities, attacks_in_budget_dict):
        iterations = 1
        p_selector_root = SelectorRootChanceGameState(attacker_types, subgame_utilities, attacks_in_budget_dict)
        cfr = VanillaCFR(p_selector_root)
        for attacker in attacker_types:
            min_utility = inf
            choice = None
            for action in cfr.sigma['.'+str(attacker)].keys():
                if subgame_utilities[action] < min_utility:
                    min_utility = subgame_utilities[action]
                    choice = action
            for action in cfr.sigma['.'+str(attacker)].keys():
                if action == choice:
                    cfr.sigma['.' + str(attacker)][action] = 1
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
                  'portfolios_dist':nash_eq, 'sigma':sigma}

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

    def run(self, main_game_root, attacker_types, game1_iterations,
            game2_iterations, attacks_in_budget_dict, subgame_keys):
        main_game_results = self.compute_main_game_utilities(main_game_root, subgame_keys, game1_iterations)
        selector_game_result = self.compute_pure_game_equilibrium(attacker_types=attacker_types,
                                                             subgame_utilities=main_game_results['utilities'],
                                                             attacks_in_budget_dict=attacks_in_budget_dict)
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

