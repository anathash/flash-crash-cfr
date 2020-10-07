from datetime import datetime

from constants import ATTACKER, DEFENDER
from utils import init_sigma, init_empty_node_maps, init_empty_node


class CounterfactualRegretMinimizationBase:

    def __init__(self, root, chance_sampling = False):
        self.root = root
        self.sigma = init_sigma(root)
        self.cumulative_regrets = init_empty_node_maps(root)
        self.cumulative_immediate_pos_regret = init_empty_node(root)
        self.cumulative_sigma = init_empty_node_maps(root)
        self.cumulative_reach = init_empty_node(root)
        self.nash_equilibrium = init_empty_node_maps(root)
        self.chance_sampling = chance_sampling

    def _update_sigma(self, i):
        rgrt_sum = sum(filter(lambda x : x > 0, self.cumulative_regrets[i].values()))
        for a in self.cumulative_regrets[i]:
            self.sigma[i][a] = max(self.cumulative_regrets[i][a], 0.) / rgrt_sum if rgrt_sum > 0 else 1. / len(self.cumulative_regrets[i].keys())

    def compute_nash_equilibrium(self):
        self.__compute_ne_rec(self.root)

    def __compute_ne_rec(self, node):
        if node.is_terminal():
            return
        i = node.inf_set()
        if node.is_chance() or node.is_market():
            chance_probs = node.chance_prob()
            if isinstance(chance_probs, dict):
                self.nash_equilibrium[i] = {a:chance_probs[a] for a in node.actions}
            else:

                self.nash_equilibrium[i] = {a: chance_probs for a in node.actions}
        else:
            sigma_sum = sum(self.cumulative_sigma[i].values())
            if(sigma_sum == 0):
                print(i)
            self.nash_equilibrium[i] = {a: self.cumulative_sigma[i][a] / sigma_sum for a in node.actions}
           # self.nash_equilibrium[i] = {a: self.cumulative_sigma[i][a] / self.cumulative_reach[i] for a in node.actions}
        # go to subtrees
        for k in node.children:
            self.__compute_ne_rec(node.children[k])

    def _cumulate_cfr_regret(self, information_set, action, regret):
        self.cumulative_regrets[information_set][action] += regret

    def _cumulate_imm_pos_regret(self, information_set, max_pos_regret):
        self.cumulative_immediate_pos_regret[information_set] += max_pos_regret

    def _cumulate_reach(self, information_set, reach):
        self.cumulative_reach[information_set] += reach

    def _cumulate_sigma(self, information_set, action, prob):
        if prob < 0:
            print(str(information_set))
            print(str(action))
        self.cumulative_sigma[information_set][action] += prob
#        x = sum(self.cumulative_sigma[information_set].values())
#        if x <=0:
#            print(x)
#        y = sum(self.cumulative_sigma[".{'AAPL': 240.0149968, 'AMZN': 1860.105825, 'BABA': 185.7262497, 'FB': 190.2608338, 'GOOGL': 1236.770854, 'JNJ': 135.4142235463039, 'MSFT': 145.6558325, 'PG': 116.5833341, 'V': 177.5908353, 'WMT': 112.14958601110506}.SELL:[['[Sell JNJ 1208076]'], ['[]'], ['[]'], ['[]'], ['[]'], ['[]'], ['[]'], ['[]'], ['[Sell WMT 979217]'], ['[]'], ['[]'], ['[]'], ['[]'], ['[]'], ['[]'], ['[]']]"].values())
#        print(y)

    def average_total_imm_regret(self, iterations):
        return sum(self.cumulative_immediate_pos_regret.values())/iterations

    def total_positive_regret(self):
        pos_r = 0
        ## sum? look in paper
        for actions_regret_dict in self.cumulative_regrets.values():
            pos_r += sum([max(x,0) for x in actions_regret_dict.values()])
        return  pos_r

    def run(self, iterations):
        raise NotImplementedError("Please implement run method")

    def value_of_the_game(self):
        return self.__value_of_the_game_state_recursive(self.root)

    def _cfr_utility_recursive(self, state, reach_attacker, reach_defender):
        children_states_utilities = {}
    #    if state.inf_set() == '.(((1, 1), False), ((3, 1), False)).(((1, 0), False), ((3, 2), False)).(((1, 1), False), ((3, 1), False))':
    #        print("reach_attacker=" + str(reach_attacker))
    #        print("reach_defender=" + str(reach_defender))
   #     if '.2000000000.D_HISTORY' in state.inf_set() and '238.8298582629332' in state.inf_set():
   #         print(type(state))
   #         print(state.inf_set())
        if state.is_terminal():
            # evaluate terminal node according to the game result
            val = state.evaluation()
            return val
            #return state.evaluation()
        if state.is_chance():
            if self.chance_sampling:
                # if node is a chance node, lets sample one child node and proceed normally
                return self._cfr_utility_recursive(state.sample_one(), reach_attacker, reach_defender)
            else:
                chance_probs = state.chance_prob()

                if isinstance(chance_probs, dict):
                    utilities = {action: self._cfr_utility_recursive(state.play(action), chance_probs[action], reach_defender)
                                 for action in state.actions}
                    return utilities
                    #return sum([chance_probs[action] *utilities[action] for action in state.actions])
                else:
                    utilities = {action: self._cfr_utility_recursive(state.play(action), chance_probs,
                                                                     reach_defender) for action in state.actions}
                    return utilities
#                    chance_outcomes = {state.play(action) for action in state.actions}
#                    return chance_probs * sum([self._cfr_utility_recursive(outcome, reach_attacker, reach_defender) for outcome in chance_outcomes])

        if state.is_market():
            return self._cfr_utility_recursive(state.play(state.actions[0]), reach_attacker, reach_defender)

        # sum up all utilities for playing actions in our game state
        value = 0.
        for action in state.actions:

            child_reach_attacker = reach_attacker * (self.sigma[state.inf_set()][action] if state.to_move == ATTACKER else 1)
            child_reach_defender = reach_defender * (self.sigma[state.inf_set()][action] if state.to_move == DEFENDER else 1)
            # value as if child state implied by chosen action was a game tree root
            child_state_utility = self._cfr_utility_recursive(state.play(action), child_reach_attacker, child_reach_defender)
            # value computation for current node
            value +=  self.sigma[state.inf_set()][action] * child_state_utility
            # values for chosen actions (child nodes) are kept here
            children_states_utilities[action] = child_state_utility
        # we are computing regrets for both players simultaneously, therefore we need to relate reach,reach_opponent to the player acting
        # in current node, for player A, it is different than for player B
        #cfr_reach = pi_{-i}^{\sigma}
        (cfr_reach, reach) = (reach_defender, reach_attacker) if state.to_move == ATTACKER else (reach_attacker, reach_defender)
        max_pos_regret = 0
        for action in state.actions:
            # we multiply regret by -1 for player defender, this is because value is computed from player A perspective
            # again we need that perspective switch
            #action_cfr_regret = probabaility_of_reaching_action*(utilities_diff)*sign_value(-1/1 fora attacker or defender)
            action_cfr_regret = state.to_move * cfr_reach * (children_states_utilities[action] - value)
            max_pos_regret = max(max_pos_regret, action_cfr_regret)
            self._cumulate_cfr_regret(state.inf_set(), action, action_cfr_regret)
            self._cumulate_sigma(state.inf_set(), action, reach * self.sigma[state.inf_set()][action])
        self._cumulate_imm_pos_regret(state.inf_set(), max_pos_regret)
        self._cumulate_reach(state.inf_set(), reach)
        if self.chance_sampling:
            # update sigma according to cumulative regrets - we can do it here because we are using chance sampling
            # and so we only visit single game_state from an information set (chance is sampled once)
            self._update_sigma(state.inf_set())
        return value

    def __value_of_the_game_state_recursive(self, node):
        value = 0.
        if node.is_terminal():
            value = node.evaluation()
            node.set_value(value)
            return value
        for action in node.actions:
            value +=  self.nash_equilibrium[node.inf_set()][action] * self.__value_of_the_game_state_recursive(node.play(action))
        node.set_value(value)
        return value


class VanillaCFR(CounterfactualRegretMinimizationBase):

    def __init__(self, root):
        super().__init__(root = root, chance_sampling = False)

    def run_with_time_limit(self, time_limit):
        time_elapsed = 0
        start = datetime.now()
        iteration = 2
        while time_elapsed <= time_limit:
            print('iteration ' + str(iteration))
            u = self._cfr_utility_recursive(self.root, 1, 1)
            # since we do not update sigmas in each information set while traversing, we need to
            # traverse the tree to perform to update it now
            self.__update_sigma_recursively(self.root)
            iteration += 1
            time_elapsed = (datetime.now() - start).seconds
        self.iterations = iteration
        return iteration

    def run(self, round = 0, iterations = 1):
        self.iterations = iterations
        for i in range(0, iterations):
            print('iteration ' + str(round) + '_' + str(i))
            u = self._cfr_utility_recursive(self.root, 1, 1)
            # since we do not update sigmas in each information set while traversing, we need to
            # traverse the tree to perform to update it now
            self.__update_sigma_recursively(self.root)
        return u

    def __update_sigma_recursively(self, node):
        # stop traversal at terminal node
        if node.is_terminal():
            return
        # omit chance
        if not (node.is_chance() or node.is_market()):
            self._update_sigma(node.inf_set())
        # go to subtrees
        for k in node.children:
            self.__update_sigma_recursively(node.children[k])


class ChanceSamplingCFR(CounterfactualRegretMinimizationBase):

    def __init__(self, root):
        super().__init__(root = root, chance_sampling = True)

    def run(self, iterations = 1):
        for _ in range(0, iterations):
            self._cfr_utility_recursive(self.root, 1, 1)
