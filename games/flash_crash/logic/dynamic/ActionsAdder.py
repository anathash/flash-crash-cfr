from bases import GameStateBase
from solvers import ActionsManager


class ActionsAdder:
    def __init__(self, actions_manager: ActionsManager, asset_sym, old_price, new_price):
        self.changed_asset = asset_sym
        self.actions_manger = actions_manager
        self.actions_manger.update_asset(asset_sym, old_price, new_price)

    def traverse_tree(self, state: GameStateBase):
        additional_actions = self.actions_manger.get_additional_actions(state)
        if additional_actions:
            return self.create_chance_node(additional_actions, state)
        else:
            for child, child_state in state.children.items():
                state.children[child] = self.traverse_tree[child_state]
            return state

    def add_actions(self, root):
        extended_tree = self.traverse_tree(root)
        w = self.compute_weight()
        #run_weighted_cfr








