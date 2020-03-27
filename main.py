from GameConfig import GameConfig
from NetworkGenerator import generate_rand_network
from constants import BUDGETS
from flash_crash_players_cfr import FlashCrashRootChanceGameState
from games.cfr import ChanceSamplingCFR, VanillaCFR


def play_flash_crash():

    config = GameConfig()
    config.num_assets = 10
    config.num_funds = 10
    network = generate_rand_network(config)
    root = FlashCrashRootChanceGameState(network, BUDGETS)
    chance_sampling_cfr = ChanceSamplingCFR(root)
    chance_sampling_cfr.run(iterations=1000)
    chance_sampling_cfr.compute_nash_equilibrium()
    # read Nash-Equilibrum via chance_sampling_cfr.nash_equilibrium member
    # try chance_sampling_cfr.value_of_the_game() function to get value of the game (-1/18)

    # vanilla cfr
    vanilla_cfr = VanillaCFR(root)
    vanilla_cfr.run(iterations=1000)
    vanilla_cfr.compute_nash_equilibrium()

if __name__ == "__main__":
    play_flash_crash()