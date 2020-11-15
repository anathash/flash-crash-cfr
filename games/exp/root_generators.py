import copy

from ActionsManager import ActionsManager
from exp.network_generators import gen_new_network, get_network_from_dir
from flash_crash_players_portfolio_cfr import PortfolioFlashCrashRootChanceGameState
from flash_crash_players_portfolio_per_attacker_cfr import PPAFlashCrashRootChanceGameState
from search.Grid import Grid
from search.search_players_complete_game import SearchCompleteGameRootChanceGameState
from search.search_players_split_main_game import SearchMainGameRootChanceGameState


class RootGenerator:
    def __init__(self, exp_params):
        self.params = exp_params
        self.complete_actions_mgr = None
        self.complete_root = None
        self.split_actions_mgr = None
        self.split_root = None

    def get_complete_game_root(self):
        return self.complete_root

    def get_split_main_game_root(self):
        return self.split_root

    def get_attack_keys(self):
        return self.split_actions_mgr.get_probable_portfolios().keys()
    #    return self.split_actions_mgr.get_portfolios_prob().keys()

    def gen_roots(self, game_size):
        self.complete_actions_mgr = None
        self.complete_root = None
        self.split_actions_mgr = None
        self.split_root = None
        self._gen_roots(game_size)

    def duplicate_root(self):
        raise NotImplementedError

    def get_attack_costs(self):
        raise NotImplementedError

    def _gen_roots(self, game_size):
        raise NotImplementedError


class FlashCrashRootGenerator(RootGenerator):

    def __init__(self,exp_params):
        super().__init__(exp_params)




    def _gen_roots(self, game_size):
        if game_size == 4:
            dirname = '../../results/networks/Fri_Sep_11_10_00_15_2020/' #4X4
           #    network = get_network_from_dir(dirname)
            self.dirname, network = gen_new_network(num_assets=4,uniform=False)

        if game_size == 3:
            #dirname = '../../results/networks/Fri_Sep_11_09_33_08_2020/' #3X3
            dirname = '../../results/three_assets_net/'
            network = get_network_from_dir(dirname)
            #self.dirname, network = gen_new_network(num_assets=3, uniform=False)

        #        dirname, network = gen_new_network(game_size)
        self.split_actions_mgr = ActionsManager(assets=network.assets,
                                     step_order_size=self.params['step_order_size'],
                                     max_order_num=self.params['max_order_num'],
                                     attacker_budgets=self.params['attacker_budgets'])
        self._gen_complete_game_root(network)
        self._gen_split_main_game_root(network)

    def _gen_complete_game_root(self, network):
        self.complete_root = PPAFlashCrashRootChanceGameState(action_mgr=self.split_actions_mgr , af_network=network,
                                                defender_budget=self.params['defender_budget'],
                                                attacker_budgets=self.params['attacker_budgets'])

     #   self.complete_root2 = PPAFlashCrashRootChanceGameState(action_mgr=self.split_actions_mgr , af_network=network,
      #                                          defender_budget=self.params['defender_budget'],
      #                                          attacker_budgets=self.params['attacker_budgets'])

    def _gen_split_main_game_root(self, network):
        self.split_root = PortfolioFlashCrashRootChanceGameState(action_mgr=self.split_actions_mgr, af_network=network,
                                                                 defender_budget=self.params['defender_budget'])

  #  def get_complete_game_action_mgr(self):
  #      return self.complete_actions_mgr

#    def get_split_game_action_mgr(self):
#        return self.split_actions_mgr

    def get_attack_costs(self):
        return self.split_actions_mgr.get_portfolios_in_budget_dict()


class SearchRootGenerator(RootGenerator):

    def __init__(self,exp_params):
        self.__grid = None
        super().__init__(exp_params)

    def _gen_roots(self, game_size):
        self.__grid = Grid(rounds_left=game_size)
        self._gen_complete_game_root(game_size)
        self._gen_split_main_game_root(game_size)


    def _gen_complete_game_root(self, game_size):
        grid = copy.deepcopy(self.__grid)
        self.complete_root = SearchCompleteGameRootChanceGameState(grid, self.params['attacker_budgets'], game_size)
        self.complete_root2 = SearchCompleteGameRootChanceGameState(grid, self.params['attacker_budgets'], game_size)

    def _gen_split_main_game_root(self, game_size):
        grid = copy.deepcopy(self.__grid)
        self.__goal_probs = grid.get_attacks_probabilities(self.params['attacker_budgets'])

        self.split_root = SearchMainGameRootChanceGameState(rounds_left=game_size,
                                                 grid=grid,
                                                 goal_probs=self.__goal_probs)

    def get_attack_costs(self):
        return self.__grid.get_attacks_in_budget_dict(self.params['attacker_budgets'])

    def get_attack_keys(self):
        return [str(x) for x in self.__goal_probs.keys()]




