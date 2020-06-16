import copy

from AssetFundNetwork import AssetFundsNetwork
import random

from constants import ATTACKER, CHANCE, DEFENDER, MARKET, BUY, SELL, SIM_TRADE
from games.bases import GameStateBase
from solvers.common import copy_network


class Budget:
    def __init__(self,attacker, defender):
        self.attacker = attacker
        self.defender = defender

    def __eq__(self, other):
        return isinstance(other, Budget) and self.defender == other.defender and self.attacker == other.attacker
#parent, actions_manager, to_move, history_assets_dict, budget, af_network, actions_history

class FlashCrashRootChanceGameState(GameStateBase):
    def __init__(self, action_mgr, af_network:AssetFundsNetwork, defender_budget, attacker_budgets):
        self.af_network = af_network
        super().__init__(parent=None, to_move=CHANCE, actions =[str(x) for x in attacker_budgets])
        self.children = {
            str(budget): AttackerMoveGameState(
                parent=self,  actions_manager=action_mgr, to_move=ATTACKER,  history_assets_dict={BUY:{},SELL:{}},
                budget=Budget(attacker=budget,defender=defender_budget),af_network=af_network,
                actions_history={BUY:[],SELL:[],SIM_TRADE:[]}
            ) for budget in attacker_budgets
        }
        self._chance_prob = 1. / len(self.children)
        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])

    def is_terminal(self):
        return False

    def inf_set(self):
        return "."

    def chance_prob(self):
        return self._chance_prob

    def sample_one(self):
        return random.choice(list(self.children.values()))


class FlashCrashGameStateBase(GameStateBase):

    def __init__(self, parent, to_move, actions, history_assets_dict, af_network, budget, actions_history):
        super().__init__(parent = parent, to_move = to_move,actions=actions)
        self.actions_history=actions_history
        self.af_network = af_network
        self.budget = budget
        self.children = {}
        self.history_assets_dict = history_assets_dict


    def inf_set(self):
        return self._information_set

    def evaluation(self):
        if not self.is_terminal():
            raise RuntimeError("trying to evaluate non-terminal node")

        return -1*self.af_network.count_margin_calls()

    def _update_asset_history(self, order_set, buy_sell_key):
        history_assets_dict2 = copy.deepcopy(self.history_assets_dict)
        for order in order_set:
            order_count = history_assets_dict2[buy_sell_key][order.asset_symbol] if order.asset_symbol \
                                                                in history_assets_dict2[buy_sell_key] else 0
            history_assets_dict2[buy_sell_key][order.asset_symbol] = order_count + 1
        return history_assets_dict2


class MarketMoveGameState(FlashCrashGameStateBase):

    def __init__(self, parent,  actions_manager, to_move, history_assets_dict, budget, af_network, actions_history):
        self.terminal = af_network.no_more_sell_orders()
        if self.terminal:
            actions = []
        else:
            net2 = copy_network(af_network)
            actions = [str(net2.simulate_trade())]

        super().__init__(parent = parent, to_move = to_move, actions=actions,history_assets_dict=history_assets_dict,
                         af_network = af_network, budget=budget, actions_history=actions_history)

        self._information_set = ".{0}.{1}.{2}".format('MARKET_HISTORY:' + str(actions_history[SIM_TRADE])
                                                     ,'BUY:'+str(af_network.buy_orders), 'SELL:'+str(af_network.sell_orders))

        if actions:
            action = actions[0]
            actions_history2 = copy.deepcopy(actions_history)
            actions_history2[SELL].append(action)
            actions_history2[BUY].append(action)
            actions_history2[SIM_TRADE].append(action)
            self.children[action] = AttackerMoveGameState(
                    self,
                    actions_manager,
                    ATTACKER,
                    self.history_assets_dict,
                    budget,
                    net2,
                    actions_history2
                )
        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])

    def chance_prob(self):
        return 1

    def is_terminal(self):
        return self.terminal


class AttackerMoveGameState(FlashCrashGameStateBase):
    def __init__(self, parent, actions_manager, to_move, history_assets_dict, budget, af_network, actions_history):
#        if af_network.margin_calls():
#            str_order_sets = []
#        else:
#            attacks = actions_manager.get_possible_attacks(budget.attacker, history_assets_dict)
#            str_order_sets = [str(x[0]) for x in attacks]
        attacks = actions_manager.get_possible_attacks(budget.attacker, history_assets_dict)
        str_order_sets = [str(x[0]) for x in attacks]
        super().__init__(parent=parent,  to_move=to_move, actions = str_order_sets,
                         history_assets_dict=history_assets_dict, af_network=af_network, budget=budget, actions_history=actions_history)
        self._information_set = ".{0}.{1}".format(str(budget.attacker), 'A_HISTORY:' + str(actions_history[SELL]))
        if not str_order_sets:
            return

        for order_set, cost in attacks:
            net2 = copy_network(af_network)
            net2.submit_sell_orders(order_set)
            actions_history2 = copy.deepcopy(actions_history)
            actions_history2[SELL].append(str(order_set))
            self.children[str(order_set)] = DefenderMoveGameState(
                self,
                actions_manager,
                DEFENDER,
                self._update_asset_history(order_set, SELL),
                Budget(budget.attacker - cost, budget.defender),
                net2,
                actions_history2
            )

        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])

    def is_terminal(self):
        return False

class DefenderMoveGameState(FlashCrashGameStateBase):

    def __init__(self, parent, actions_manager, to_move, history_assets_dict, budget, af_network, actions_history):
        defenses = actions_manager.get_possible_defenses(af_network, budget.defender, history_assets_dict)
        str_order_sets = [str(x[0]) for x in defenses]
        super().__init__(parent=parent, to_move=to_move, actions=str_order_sets, history_assets_dict=history_assets_dict,
                         af_network=af_network, budget=budget, actions_history=actions_history)

#        if not defenses:
#            self.budget.defender = 0 #in case there is only a small amount of money
 #       else:
        for order_set, cost in defenses:
            net2 = copy_network(af_network)
            net2.submit_buy_orders(order_set)
            actions_history2 = copy.deepcopy(actions_history)
            actions_history2[BUY].append(str(order_set))
            self.children[str(order_set)] = MarketMoveGameState(
                self,
                actions_manager,
                MARKET,
                self._update_asset_history(order_set, BUY),
                Budget(budget.attacker,budget.defender - cost),
                net2,
                actions_history2
            )
        self._information_set = ".{0}.{1}".format(str(budget.defender), 'D_HISTORY:' + str(actions_history[BUY]))
        self.tree_size = 1 + sum([x.tree_size for x in self.children.values()])

    def is_terminal(self):
        return False




