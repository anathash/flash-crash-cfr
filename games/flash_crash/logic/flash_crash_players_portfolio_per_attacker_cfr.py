import copy

from AssetFundNetwork import AssetFundsNetwork
import random

from constants import ATTACKER, CHANCE, DEFENDER, MARKET, BUY, SELL, SIM_TRADE
from games.bases import GameStateBase
from solvers.common import copy_network


class PPAPlayersHiddenInfo:
    def __init__(self,attacker_attack, attacker_pid, defender_budget, attacker_budget):
        self.attacker_attack = attacker_attack
        self.attacker_pid = attacker_pid
        self.defender = defender_budget
        self.attacker_budget = attacker_budget

    def __eq__(self, other):
        return isinstance(other, PPAPlayersHiddenInfo) and self.defender == other.defender and \
               self.attacker_attack == other.attacker_attack and self.attacker_pid == other.attacker_pid


class PPAFlashCrashGameStateBase(GameStateBase):

    def __init__(self, parent, to_move, actions, af_network, players_info, actions_history):
        super().__init__(parent=parent, to_move = to_move,actions=actions)
        self.actions_history=actions_history
        self.af_network = af_network
        self.players_info = players_info
        self.children = {}

    def inf_set(self):
        return self._information_set

    def evaluation(self):
        if not self.is_terminal():
            raise RuntimeError("trying to evaluate non-terminal node")

        return -1*self.af_network.count_margin_calls()


class PPAFlashCrashRootChanceGameState(GameStateBase):
    def __init__(self, action_mgr, af_network:AssetFundsNetwork, defender_budget, attacker_budgets):
        super().__init__(parent=None, to_move=CHANCE, actions = [str(x) for x in attacker_budgets])
        self.af_network = af_network
        self.children = {
            str(attacker_budget): PPASelectorGameState(
                parent=self,  actions_manager=action_mgr, to_move=ATTACKER,
                af_network=af_network,defender_budget=defender_budget, attacker_budget=attacker_budget
            ) for attacker_budget in attacker_budgets
        }

        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])
        self._chance_prob = 1./len(attacker_budgets)


    def is_terminal(self):
        return False

    def inf_set(self):
        return "."

    def chance_prob(self):
        return self._chance_prob

    def sample_one(self):
        return random.choice(list(self.children.values()))


class PPASelectorGameState(GameStateBase):
    def __init__(self, parent, actions_manager, to_move,
                 af_network:AssetFundsNetwork, defender_budget, attacker_budget):
        portfolios_in_budget = actions_manager.get_portfolios_in_budget(attacker_budget)
        portfolios = {x: y.order_set for x, y in actions_manager.get_portfolios().items() if x in portfolios_in_budget}
        super().__init__(parent=parent, to_move=to_move, actions=portfolios.keys())
        self.af_network = af_network
        self.children = {
            str(p_id): PPAAttackerMoveGameState(
                parent=self,  actions_manager=actions_manager, to_move=ATTACKER,
                players_info=PPAPlayersHiddenInfo(p, p_id, defender_budget, attacker_budget),
                af_network=af_network,
                actions_history={BUY:[],SELL:[],SIM_TRADE:[]}
            ) for p_id, p in portfolios.items()
        }

        self._information_set = ".{0}".format(str(attacker_budget))
        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])

    def is_terminal(self):
        return False

    def inf_set(self):
        return self._information_set



class PPAMarketMoveGameState(PPAFlashCrashGameStateBase):

    def __init__(self, parent,  actions_manager, to_move, players_info, af_network, actions_history):
        self.terminal = af_network.no_more_sell_orders()
        if self.terminal:
            actions = []
        else:
            net2 = copy_network(af_network)
            actions = [str(net2.simulate_trade())]

        super().__init__(parent = parent, to_move = to_move, actions=actions,
                         af_network = af_network, players_info=players_info, actions_history=actions_history)

        self._information_set = ".{0}.{1}.{2}".format('MARKET_HISTORY:' + str(actions_history[SIM_TRADE])
                                                     ,'BUY:'+str(af_network.buy_orders), 'SELL:'+str(af_network.sell_orders))

        if actions:
            action = actions[0]
            actions_history2 = copy.deepcopy(actions_history)
            actions_history2[SELL].append(action)
            actions_history2[BUY].append(action)
            actions_history2[SIM_TRADE].append(action)
            self.children[action] = PPAAttackerMoveGameState(
                    self,
                    actions_manager,
                    ATTACKER,
                    players_info,
                    net2,
                    actions_history2
                )
        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])

    def chance_prob(self):
        return 1

    def is_terminal(self):
        return self.terminal


class PPAAttackerMoveGameState(PPAFlashCrashGameStateBase):
    def __init__(self, parent, actions_manager, to_move, players_info, af_network, actions_history):
        actions = actions_manager.get_possible_attacks_from_portfolio(players_info.attacker_attack, af_network.no_more_sell_orders())
        self.terminal = not actions

        super().__init__(parent=parent,  to_move=to_move, actions = [str(x['action_subset']) for x in actions ],
                          af_network=af_network, players_info=players_info, actions_history=actions_history)

        for action in actions:
            order_set = action['action_subset']
            net2 = copy_network(af_network)
            net2.submit_sell_orders(order_set)
            actions_history2 = copy.deepcopy(actions_history)
            actions_history2[SELL].append(str(order_set))
            self.children[str(order_set)] = PPADefenderMoveGameState(
                self,
                actions_manager,
                DEFENDER,
                PPAPlayersHiddenInfo(action['remaining_orders'], players_info.attacker_pid, players_info.defender,
                                     players_info.attacker_budget),
                net2,
                actions_history2,
            )

        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])
        self._information_set = ".{0}.{1}.{2}".format(str(players_info.attacker_budget), players_info.attacker_pid, 'A_HISTORY:' + str(actions_history[SELL]))

    def is_terminal(self):
        return self.terminal


class PPADefenderMoveGameState(PPAFlashCrashGameStateBase):

    def __init__(self, parent, actions_manager, to_move, players_info, af_network, actions_history):
        defenses = actions_manager.get_possible_defenses(af_network, players_info.defender)
        str_order_sets = [str(x[0]) for x in defenses]
        super().__init__(parent=parent, to_move=to_move, actions=str_order_sets,
                         af_network=af_network, players_info=players_info, actions_history=actions_history)

#        if not defenses:
#            self.budget.defender = 0 #in case there is only a small amount of money
 #       else:
        for order_set, cost in defenses:
            net2 = copy_network(af_network)
            net2.submit_buy_orders(order_set)
            actions_history2 = copy.deepcopy(actions_history)
            actions_history2[BUY].append(str(order_set))
            self.children[str(order_set)] = PPAMarketMoveGameState(
                self,
                actions_manager,
                MARKET,
                PPAPlayersHiddenInfo(players_info.attacker_attack, players_info.attacker_pid, players_info.defender - cost,
                                     players_info.attacker_budget),
                net2,
                actions_history2
            )
        self._information_set = ".{0}.{1}".format(players_info.defender, 'D_HISTORY:' + str(actions_history[BUY]))
        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])

    def is_terminal(self):
        return False




