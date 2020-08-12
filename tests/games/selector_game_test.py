import unittest

from constants import CHANCE, ATTACKER
from split_selector_game import SelectorRootChanceGameState


class SelectorGame  (unittest.TestCase):

    @staticmethod
    def fill_dict(tree_size, to_move, actions, inf_set, terminal, eval):
        return{'tree_size':tree_size, 'to_move':to_move,'actions':actions,
               'inf_set':inf_set,
               'terminal':terminal, 'eval':eval}

    def cmp_node(self, expected_node, actual_node):
        self.assertEqual(expected_node['tree_size'], actual_node.tree_size)
        self.assertEqual(expected_node['to_move'], actual_node.to_move)
        self.assertCountEqual(expected_node['actions'], actual_node.actions)
        self.assertEqual(expected_node['inf_set'], actual_node.inf_set())
        self.assertEqual(expected_node['terminal'], actual_node.is_terminal())
        if actual_node.is_terminal():
            self.assertEqual(expected_node['eval'], actual_node.evaluation())


    def cmp_tree(self, expected_tree, actual_tree):
        self.cmp_node(expected_tree, actual_tree)
        kids_sort1 = sorted(actual_tree.children.keys())
        kids_sort2 = sorted(expected_tree['children'].keys())
        self.assertEqual(kids_sort1, kids_sort2)
        for k in kids_sort1:
            self.cmp_tree(expected_tree['children'][k], actual_tree.children[k])

    def test_tree(self):
        attacker_budgets = [10, 20]
        attack_utilities = {'p1':0, 'p2':-1}
        actual_tree = SelectorRootChanceGameState(attacker_budgets, attack_utilities,
                                                                     {10:['p1', 'p2'], 20:['p1', 'p2']})
        expected_tree = self.gen_tree()
        self.assertEqual(actual_tree.chance_prob(), 1./2)
        self.cmp_tree(expected_tree, actual_tree)

    def test_tree2(self):
        attacker_budgets = [10, 20]
        attack_utilities = {'p1':0, 'p2':-1}
        actual_tree = SelectorRootChanceGameState(attacker_budgets, attack_utilities,
                                                                     {10:['p1', 'p2'], 20:['p1']})
        expected_tree = self.gen_tree2()
        self.assertEqual(actual_tree.chance_prob(), 1./2)
        self.cmp_tree(expected_tree, actual_tree)

    def gen_tree2(self,):
        root = {'tree_size':6,'to_move':CHANCE,'actions':['10','20'],  'inf_set':'.', 'terminal':False }

        node_1_0 = self.fill_dict(tree_size=3, to_move=ATTACKER, actions = ['p1','p2'],
                                  inf_set='.10',
                                  terminal=False, eval=None)

        node_1_0_0 = self.fill_dict(tree_size=1, to_move='ATTACK', actions = [],
                                  inf_set = '.10.p1',
                                  terminal = True, eval=0)

        node_1_0_1 = self.fill_dict(tree_size=1, to_move='ATTACK', actions = [],
                                  inf_set = '.10.p2',
                                  terminal = True, eval=-1)

        node_1_1 = self.fill_dict(tree_size=2, to_move=ATTACKER, actions=['p1'],
                                  inf_set='.20',
                                  terminal=False, eval=None)

        node_1_1_0 = self.fill_dict(tree_size=1, to_move='ATTACK', actions = [],
                                  inf_set = '.20.p1',
                                  terminal = True, eval=0)


        root['children'] = {'10': node_1_0, '20': node_1_1}
        node_1_0['children'] = {'p1': node_1_0_0, 'p2': node_1_0_1}
        node_1_1['children'] = {'p1': node_1_1_0}
        node_1_0_0['children'] = {}
        node_1_0_1['children'] = {}
        node_1_1_0['children'] = {}
        return root

    def gen_tree(self):
        root = {'tree_size':7,'to_move':CHANCE,'actions':['10','20'],  'inf_set':'.', 'terminal':False }

        node_1_0 = self.fill_dict(tree_size=3, to_move=ATTACKER, actions = ['p1','p2'],
                                  inf_set='.10',
                                  terminal=False, eval=None)

        node_1_1 = self.fill_dict(tree_size=3, to_move=ATTACKER, actions = ['p1','p2'],
                                  inf_set='.20',
                                  terminal=False, eval=None)

        node_1_0_0 = self.fill_dict(tree_size=1, to_move='ATTACK', actions = [],
                                  inf_set = '.10.p1',
                                  terminal = True, eval=0)

        node_1_0_1 = self.fill_dict(tree_size=1, to_move='ATTACK', actions = [],
                                  inf_set = '.10.p2',
                                  terminal = True, eval=-1)

        node_1_1_0 = self.fill_dict(tree_size=1, to_move='ATTACK', actions = [],
                                  inf_set = '.20.p1',
                                  terminal = True, eval=0)

        node_1_1_1 = self.fill_dict(tree_size=1, to_move='ATTACK', actions = [],
                                  inf_set = '.20.p2',
                                  terminal = True, eval=-1)

        root['children'] = {'10': node_1_0, '20': node_1_1}
        node_1_0['children'] = {'p1': node_1_0_0, 'p2': node_1_0_1}
        node_1_1['children'] = {'p1': node_1_1_0, 'p2': node_1_1_1}
        node_1_0_0['children'] = {}
        node_1_0_1['children'] = {}
        node_1_1_0['children'] = {}
        node_1_1_1['children'] = {}
        return root