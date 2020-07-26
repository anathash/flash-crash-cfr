from math import inf

from SysConfig import SysConfig
from exp.network_generators import get_network_from_dir
from flash_crash_players_portfolio_cfr import PortfolioFlashCrashRootChanceGameState
from flash_crash_portfolios_selector_cfr import PortfolioSelectorFlashCrashRootChanceGameState
from solvers.ActionsManager import ActionsManager
from solvers.cfr import VanillaCFR


class SplitGameCFR:

    def compute_portfolio_utilities(self, root, round, action_mgr, iterations):
        vanilla_cfr = VanillaCFR(root)
        vanilla_cfr.run(iterations=iterations, round=round)
        vanilla_cfr.compute_nash_equilibrium()
        # generate portfolio utility table
        vanilla_cfr.value_of_the_game()
        utilities = {pid: root.children[pid].get_value() for pid in action_mgr.get_probable_portfolios().keys()}
        return utilities

    def compute_game_equilibrium(self, attacker_budgets, portfolios_utilities, iterations,action_mgr):
        p_selector_root = PortfolioSelectorFlashCrashRootChanceGameState(attacker_budgets, portfolios_utilities,
                                                                         action_mgr.get_portfolios_in_budget_dict(attacker_budgets))
        cfr = VanillaCFR(p_selector_root)
        cfr.run(iterations=iterations)
        cfr.compute_nash_equilibrium()
        pids = portfolios_utilities.keys()
        nash_eq = {pid:0 for pid in pids}
        attackers_eq = {}
        defender_eq = cfr.value_of_the_game()
        for attacker_budget in attacker_budgets:
            for pid in action_mgr.get_portfolios_in_budget(attacker_budget):
                inf_set = ".{0}".format(attacker_budget)
                nash_eq[pid] += cfr.nash_equilibrium[inf_set][pid]*1/len(attacker_budgets)

        for attacker in attacker_budgets:
            attackers_eq[attacker] = p_selector_root.children[str(attacker)].get_value()
            #regrets[attacker] = cfr.cumulative_regrets[p_selector_root.children[str(attacker)].inf_set()]
            #'regrets':regrets
        cumulative_pos_regret = cfr.total_positive_regret()
        return {'defender':defender_eq, 'attackers':attackers_eq,  'pos_regret':cumulative_pos_regret/iterations,
                'portfolios_dist':nash_eq}

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

    def run(self, action_mgr, network, defender_budget, attacker_budgets, game1_iterations, game2_iterations, round):
        root = PortfolioFlashCrashRootChanceGameState(action_mgr=action_mgr,
                                                      af_network=network,
                                                      defender_budget=defender_budget)
        utilities = self.compute_portfolio_utilities(root, round, action_mgr, game1_iterations)
        return self.compute_game_equilibrium(attacker_budgets, utilities, game2_iterations, action_mgr)




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

    split_gae_cfr = SplitGameCFR()
    split_gae_cfr.run(action_mgr=cfr_actions_mgr, network=network, defender_budget=defender_budget,
                  attacker_budgets=attacker_budgets,
                  game1_iterations=200,
                  game2_iterations=800,
                  round=1)


if __name__ == "__main__":
    main()

