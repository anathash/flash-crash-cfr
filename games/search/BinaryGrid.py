import copy

from search.GridBase import GridBase, OCCUPANTS, AgentLocationError, MAX_X, GoalNotSetError, MAX_VALUE


class BinaryGrid(GridBase):
    def __init__(self, rounds_left):
        super().__init__(rounds_left=rounds_left)

    def set_attacker_goal(self, goal):
        new_grid = copy.deepcopy(self)
        if goal[0] != MAX_X:
            raise AgentLocationError
        new_grid.attacker_goal = goal
        return new_grid

    def attacker_reached_her_goal(self):
        if not self.attacker_goal:
            raise GoalNotSetError
        return self.attacker_goal == self.locations[OCCUPANTS.ATTACKER]

    def get_game_value(self):
        #defender caught attacker
        if self.attacker_caught():
            return 0
        # attacker reached its goal node
        if self.attacker_reached_her_goal():
            x = self.locations[OCCUPANTS.ATTACKER][0]
            y = self.locations[OCCUPANTS.ATTACKER][1]
            return -1*self.matrix[(x,y)].payoff

        #reached a goal node not its own
        if self.attacker_reached_goal_nodes():
            return MAX_VALUE

        return MAX_VALUE

    def get_attacks_in_budget_dict(self, attacker_budgets, to_str=True):
        attacks_in_budget_dict = {x: [] for x in attacker_budgets}
        for goal, cost in self.costs.items():
            for budget in attacker_budgets:
                if budget >= cost:
                    if to_str:
                        attacks_in_budget_dict[budget].append(str(goal))
                    else:
                        attacks_in_budget_dict[budget].append(goal)

        return attacks_in_budget_dict

    def get_attacks_probabilities(self, attacker_budgets):
        attacks_in_budget = self.get_attacks_in_budget_dict(attacker_budgets, False)
        probs = {x:0 for x in self.costs.keys()}
        for budget, attack_list in attacks_in_budget.items():
            for attack in attack_list:
                probs[attack] += 1/(len(attacker_budgets)*len(attack_list))
        return probs

    def set_attacker_action(self, action):
        self.round_actions[OCCUPANTS.ATTACKER] = action

    def set_defender_action(self, p1_action, p2_action):
        self.round_actions[OCCUPANTS.P1] = p1_action
        self.round_actions[OCCUPANTS.P2] = p2_action

    def is_terminal(self):
        return self.rounds_left == 0 or self.attacker_caught() or self.attacker_reached_goal_nodes()

    def get_curr_locations_strs(self):
        p1_loc = self.locations[OCCUPANTS.P1]
        p2_loc = self.locations[OCCUPANTS.P2]
        defender_curr_locations = str(((p1_loc, self.matrix[p1_loc].tracks),
                                       (p2_loc, self.matrix[p2_loc].tracks)))
        attacker_curr_location = str(self   .locations[OCCUPANTS.ATTACKER])

        return defender_curr_locations, attacker_curr_location
