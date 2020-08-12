from cfr import VanillaCFR
from flash_crash_players_cfr import FlashCrashRootChanceGameState


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
    cumulative_pos_regret = vanilla_cfr.average_total_imm_regret(iterations)


    return {'defender':defender_eq, 'attackers':attackers_eq, 'regrets':regrets,
            'pos_regret': cumulative_pos_regret, 'exploitability': 2* cumulative_pos_regret}
