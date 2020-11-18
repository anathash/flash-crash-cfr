import copy
from search.GridBase import GridBase, OCCUPANTS, MAX_X, AgentLocationError, GoalNotSetError, MAX_VALUE


class ProbsGrid(GridBase):
    def __init__(self, rounds_left):
        super().__init__(rounds_left=rounds_left)

    def set_attacker_goal(self, goal):
        new_grid = copy.deepcopy(self)
        if goal[1][0] != MAX_X:
            raise AgentLocationError
        new_grid.attacker_goal = goal
        return new_grid

    def attacker_reached_her_goal(self):
        if not self.attacker_goal:
            raise GoalNotSetError
        return self.attacker_goal[1] == self.locations[OCCUPANTS.ATTACKER]

    def get_game_value(self):
        #defender caught attacker
        if self.attacker_caught():
            return 0
        # attacker reached its goal node
        if self.attacker_reached_her_goal():
            x = self.locations[OCCUPANTS.ATTACKER][0]
            y = self.locations[OCCUPANTS.ATTACKER][1]
            payoff = min(self.matrix[(x,y)].payoff, self.attacker_goal[0])
            return -1*payoff


        #reached a goal node not its own
        if self.attacker_reached_goal_nodes():
            return MAX_VALUE

        return MAX_VALUE

    def get_attacks_in_budget_dict(self, attacker_budgets, to_str=True):
        attacks_in_budget_dict = {x: [] for x in attacker_budgets}
        for goal, cost in self.costs.items():
            for budget in attacker_budgets:
                resources = min(budget, cost)
                if to_str:
                    attacks_in_budget_dict[budget].append(str((resources, goal)))
                else:
                    attacks_in_budget_dict[budget].append((resources, goal))

        return attacks_in_budget_dict

    def get_attacks_probabilities(self, attacker_budgets):
        attacks_in_budget = self.get_attacks_in_budget_dict(attacker_budgets, False)
        attacks = list(attacks_in_budget.values())
        all_attacks = set([item for sublist in attacks for item in sublist])
        probs = {x:0 for x in all_attacks}
        for budget, attack_list in attacks_in_budget.items():
            for attack in attack_list:
                probs[attack] += 1/(len(attacker_budgets)*len(attack_list))
        return probs
