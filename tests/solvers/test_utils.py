import numpy

from constants import ATTACKER
from split_game_cfr import SplitGameCFR
from exp.archive.cfr_experiment_runner import compute_cfr_equilibrium, compute_complete_game_equilibrium

def cmp_subtree(ut, split_node, complete_node, split_cfr, complete_cfr, attacker_type):
#        self.assertCountEqual(list(complete_node.children.keys()), list(split_node.children.keys()))
        for k in complete_node.children:
            cmp_subtree(ut, split_node.children[k], complete_node.children[k], split_cfr, complete_cfr, attacker_type)
        if complete_node.inf_set() == '.' or complete_node.inf_set() == '.'+str(attacker_type):
            return
        for action, eq in complete_cfr.nash_equilibrium[complete_node.inf_set()].items():
            if complete_node.to_move != ATTACKER:
                ut.assertAlmostEqual(eq, split_cfr.nash_equilibrium[split_node.inf_set()][action], 5)
            else:
                if not numpy.isclose(eq, split_cfr.nash_equilibrium[split_node.inf_set()][attacker_type][action], rtol=1e-04, atol=1e-04, equal_nan=False):
                    print('inf sets')
                    print(complete_node.inf_set())
                    print(split_node.inf_set())

                    print('sigma')
                    print(complete_cfr.sigma[complete_node.inf_set()])
                    print(split_cfr.sigma[split_node.inf_set()])
                    print('cumulative sigma')
                    print(complete_cfr.cumulative_sigma[complete_node.inf_set()])
                    print(split_cfr.cumulative_sigma[split_node.inf_set()])
                    print('eq')
                    print(complete_cfr.nash_equilibrium[complete_node.inf_set()])
                    print(split_cfr.nash_equilibrium[split_node.inf_set()])
                    print('------------------------------------')
                    ut.assertTrue(False)


def compare_equilibrium(ut, game_size, iterations, root_generator, attacker_budgets):

    exp_params = {'attacker_budgets':attacker_budgets, 'iterations':iterations}
    root_generator.gen_roots(game_size)

    split_game_cfr = SplitGameCFR()
    main_game_cfr, selector_cfr = split_game_cfr.run_split_cfr(root_generator, exp_params)
    selector_game_result = split_game_cfr.get_selector_stats(main_game_cfr, selector_cfr, iterations, \
                                                             attacker_budgets,
                                                             root_generator.get_attack_costs())

    vanilla_results = compute_complete_game_equilibrium(root_generator.get_complete_game_root(),
                                                        attacker_budgets, iterations)

    complete_game_root = root_generator.get_complete_game_root()
    complete_cfr = vanilla_results['cfr']
    for b in attacker_budgets:
        inf_set = '.'+str(b)
        node = complete_game_root.children[str(b)]
        for action in node.actions:
            sigma = complete_cfr.nash_equilibrium[inf_set][action]
            #sigma = complete_cfr.sigma[inf_set][action]
           # if not numpy.isclose(sigma, 0, rtol=1e-05, atol=1e-08, equal_nan=False):

            ut.assertAlmostEqual(complete_cfr.nash_equilibrium[inf_set][action], selector_cfr.nash_equilibrium[inf_set][action], 5)

            cmp_subtree(ut=ut, split_node = root_generator.get_split_main_game_root().children[action],
                             complete_node =  node.children[action],
                             split_cfr = main_game_cfr,
                             complete_cfr = vanilla_results['cfr'],
                             attacker_type=b)

