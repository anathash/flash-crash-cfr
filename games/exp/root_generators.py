import copy
import json

from ActionsManager import ActionsManager
from SerializableState import load_from_file, fill_ser_state, load_state_rec
from exp.network_generators import gen_new_network, get_network_from_dir
from flash_crash_players_portfolio_cfr import PortfolioFlashCrashRootChanceGameState
from flash_crash_players_portfolio_per_attacker_cfr import PPAFlashCrashRootChanceGameState
from search.BinaryGrid import BinaryGrid
from search.ProbsGrid import ProbsGrid

from search.search_players_complete_game import SearchCompleteGameRootChanceGameState
from search.search_players_split_main_game import SearchMainGameRootChanceGameState


class RootGenerator:
    def __init__(self, exp_params):
        self.params = exp_params
        self.complete_root = None
#        self.complete_actions_mgr = None
#        self.split_actions_mgr = None
        self.split_root = None
        self.attack_costs = None
        self.attack_keys = None
        self.loaded_from_file = False
        if 'trees_file' in exp_params:
            self.trees_file = exp_params['trees_file']
        else:
            self.trees_file = None

#    @classmethod
#    def load_root_generator(cls, filename):
#        rg = cls({})
#        rg.__load_roots(filename)
#        rg.loaded_from_file = True
#        return rg


    def get_complete_game_root(self):
        return self.complete_root

    def get_split_main_game_root(self):
        return self.split_root

    def get_attack_keys(self):
        return self.attack_keys

    def save_roots_to_file(self, filename ):
        root_gen_dic = {}
        root_gen_dic['complete_root'] = fill_ser_state(tree_size= self.complete_root.tree_size, to_move= self.complete_root.to_move, actions= self.complete_root.actions,
                       children= self.complete_root.children, inf_set= self.complete_root.inf_set(), chance_prob= self.complete_root.chance_prob())
        root_gen_dic['split_root'] =  fill_ser_state(tree_size= self.split_root.tree_size, to_move= self.split_root.to_move, actions= self.split_root.actions,
                       children= self.split_root.children, inf_set= self.split_root.inf_set(), chance_prob= self.split_root.chance_prob())
        root_gen_dic['attack_costs'] = self.attack_costs
        root_gen_dic['attack_keys'] = list(self.attack_keys)
        with open(filename, 'w') as fp:
            json.dump(root_gen_dic, fp)

    def __load_roots(self, filename):
        with open(filename, 'r') as f:
            root_gen_dic = json.load(f)

        self.complete_root = load_state_rec(root_gen_dic['complete_root'], None)
        self.split_root = load_state_rec( root_gen_dic['split_root'], None)
        self.attack_costs = {int(x):y for x,y in root_gen_dic['attack_costs'].items()}
        self.attack_keys = root_gen_dic['attack_keys']

    def gen_roots(self, game_size, test = False):
 #       self.complete_actions_mgr = None
        self.complete_root = None
 #       self.split_actions_mgr = None
        self.split_root = None
        self.attack_costs = None
        self.attack_keys = None
        if self.trees_file:
            self.__load_roots(self.trees_file)
        else:
            self._gen_roots(game_size, test)

    def get_attack_costs(self):
        return self.attack_costs

    def _gen_roots(self, game_size, test=False):
        raise NotImplementedError


class FlashCrashRootGenerator(RootGenerator):

    def __init__(self,exp_params):
        super().__init__(exp_params)
        if 'net_type' in exp_params:
            self.net_type = exp_params['net_type']
        else:
            self.net_type = None
        if 'net_file' in exp_params:
            self.net_file = exp_params['net_file']
        else:
            self.net_file = None

    def _gen_roots(self, game_size, test=False):
        if test:
            if game_size == 4:
                dirname = '../../results/networks/Fri_Sep_11_10_00_15_2020/' #4X4
                network = get_network_from_dir(dirname, test=True)
            if game_size == 3:
                dirname = '../../results/networks/Fri_Sep_11_09_33_08_2020/' #3X3
                network = get_network_from_dir(dirname, test=True)
        #        dirname, network = gen_new_network(game_size)
        elif self.net_file:
            network = get_network_from_dir(self.net_file, test=False)
        else:
            #network = get_network_from_dir( '../../results/networks/', test)
            dirname, network = gen_new_network(game_size, self.net_type)
        actions_mgr = ActionsManager(assets=network.assets,
                                           step_order_size=self.params['step_order_size'],
                                           max_order_num=self.params['max_order_num'],
                                           attacker_budgets=self.params['attacker_budgets'])
        self.attack_costs = actions_mgr.get_portfolios_in_budget_dict()
        self.attack_keys = actions_mgr.get_probable_portfolios().keys()
        self._gen_split_main_game_root(network, actions_mgr)
        self._gen_complete_game_root(network, copy.deepcopy(actions_mgr))

    def _gen_complete_game_root(self, network, actions_mgr):
        self.complete_root = PPAFlashCrashRootChanceGameState(action_mgr = actions_mgr , af_network=network,
                                                defender_budget=self.params['defender_budget'],
                                                attacker_budgets=self.params['attacker_budgets'])


    def _gen_split_main_game_root(self, network, actions_mgr):
        self.split_root = PortfolioFlashCrashRootChanceGameState(action_mgr= actions_mgr, af_network=network,
                                                                 defender_budget=self.params['defender_budget'])


class SearchRootGenerator(RootGenerator):

    def __init__(self,exp_params):
        self.__grid = None
        self.binary = exp_params['binary']
        super().__init__(exp_params)

    def _gen_roots(self, game_size, test=False):
        if self.binary:
            self.__grid = BinaryGrid(rounds_left=game_size)
        else:
            self.__grid = ProbsGrid(rounds_left=game_size)
        self._gen_complete_game_root(game_size)
        self._gen_split_main_game_root(game_size)
        self.attack_keys = [str(x) for x in self.__goal_probs.keys()]

    def _gen_complete_game_root(self, game_size):
        grid = copy.deepcopy(self.__grid)
        self.complete_root = SearchCompleteGameRootChanceGameState(grid, self.params['attacker_budgets'], game_size)
        self.complete_root2 = SearchCompleteGameRootChanceGameState(grid, self.params['attacker_budgets'], game_size)
        self.attack_costs = grid.get_attacks_in_budget_dict(self.params['attacker_budgets'])

    def _gen_split_main_game_root(self, game_size):
        grid = copy.deepcopy(self.__grid)
        self.__goal_probs = grid.get_attacks_probabilities(self.params['attacker_budgets'])

        self.split_root = SearchMainGameRootChanceGameState(rounds_left=game_size,
                                                 grid=grid,
                                                 goal_probs=self.__goal_probs)




