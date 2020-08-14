import unittest
from math import inf

from constants import CHANCE, ATTACKER, DEFENDER
from search.Grid import Grid, Actions
from search.search_players_complete_game import SearchCompleteGameRootChanceGameState, \
    SearchCompleteGameAttackerMoveGameState, SearchCompleteGameDefenderMoveGameState, \
    SearchCompleteGameSelectorGameState


class TestSearchCompleteGame  (unittest.TestCase):

    def setup_tree(self, rounds_left):
        grid = Grid()
        attacker_budgets = [4, 5, 11]

        root = SearchCompleteGameRootChanceGameState(grid=grid, attacker_budgets=attacker_budgets, rounds_left=rounds_left)
        return root

    def test_chance_root_ok(self):
        root = self.setup_tree(1)
        self.assertEqual(root.tree_size, 100
                         )
        self.assertIsNone(root.parent)
        self.assertEqual(root.to_move, CHANCE)
        self.assertCountEqual(root.actions, ['4', '5', '11'])
        self.assertCountEqual(list(root.children.keys()), ['4', '5', '11'])
        self.assertEqual(root.inf_set(), '.')
        self.assertFalse(root.is_terminal())
        self.assertEqual(root.chance_prob(), 1/3)
        for child in root.children.values():
            self.assertTrue(isinstance(child, SearchCompleteGameSelectorGameState))

    def test_selector_node_ok(self):
        root = self.setup_tree(1)
        node = root.children['5']
        self.assertFalse(node.is_terminal())
        self.assertFalse(node.terminal)
        self.assertEqual(node.tree_size, 33)
        self.assertEqual(node.parent, root)
        self.assertEqual(node.to_move, ATTACKER)
        self.assertEqual(node.rounds_left, 1)
        self.assertEqual(node.actions_history, {ATTACKER: ['b:5'], DEFENDER: []})
        self.assertCountEqual(node.actions,['(4, 0)', '(4, 2)'])
        self.assertCountEqual(list(node.children.keys()), ['(4, 0)', '(4, 2)'])
        self.assertEqual(node.inf_set(), '.b:5')
        for child in node.children.values():
            self.assertTrue(isinstance(child, SearchCompleteGameAttackerMoveGameState))

    def test_non_terminal_attacker_node(self):
        root = self.setup_tree(1)
        parent = root.children['4']
        node = parent.children['(4, 0)']
        self.assertFalse(node.is_terminal())
        self.assertFalse(node.terminal)
        self.assertEqual(node.tree_size, 16)
        self.assertEqual(node.parent, parent)
        self.assertEqual(node.to_move, ATTACKER)
        self.assertEqual(node.rounds_left, 1)
        self.assertEqual(node.actions_history, {ATTACKER:['b:4', 'g:(4, 0)'], DEFENDER:[]})
        self.assertCountEqual(node.actions,
                              ['EAST','NORTH_EAST', 'SOUTH_EAST'])
        self.assertCountEqual(list(node.children.keys()),
                              ['EAST','NORTH_EAST', 'SOUTH_EAST'])
        self.assertEqual(node.inf_set(), '.b:4.g:(4, 0)')
        for child in node.children.values():
            self.assertTrue(isinstance(child, SearchCompleteGameDefenderMoveGameState))

    def test_non_terminal_defender_node(self):
        root = self.setup_tree(1)
        parent = root.children['4'].children['(4, 0)']
        node = parent.children['EAST']

        self.assertFalse(node.is_terminal())
        self.assertFalse(node.terminal)
        self.assertEqual(node.tree_size, 5)
        self.assertEqual(node.parent, parent)
        self.assertEqual(node.to_move, DEFENDER)
        self.assertEqual(node.rounds_left, 1)
        self.assertEqual(node.actions_history, {ATTACKER:['b:4', 'g:(4, 0)','EAST'], DEFENDER:[]})
        actions = ['(NORTH, NORTH)',
                   '(NORTH, SOUTH)',
                   '(SOUTH, NORTH)',
                   '(SOUTH, SOUTH)']

        self.assertCountEqual(node.actions,actions)
        self.assertCountEqual(list(node.children.keys()),actions)
        self.assertEqual(node.inf_set(), '..')
        for child in node.children.values():
            self.assertTrue(isinstance(child, SearchCompleteGameAttackerMoveGameState))

    def test_terminal_attacker_node_not_caught(self):
        root = self.setup_tree(1)
        parent = root.children['4'].children['(4, 0)'].children['EAST']
        node = parent.children['(NORTH, NORTH)']

        self.assertTrue(node.is_terminal())
        self.assertTrue(node.terminal)
        self.assertEqual(node.tree_size , 1)
        self.assertEqual(node.parent, parent)
        self.assertEqual(node.to_move , ATTACKER)
        self.assertEqual(node.rounds_left, 0)
        self.assertEqual(node.actions_history, {ATTACKER:['b:4','g:(4, 0)','EAST'], DEFENDER:['(NORTH, NORTH)']})
        self.assertEqual(node.actions, [])
        self.assertEqual(node.children, {})
        self.assertEqual(node.inf_set(), '.b:4.g:(4, 0).EAST')
        self.assertEqual(node.evaluation(), -inf)

    def test_terminal_attacker_node_caught(self):
        root = self.setup_tree(1)
        parent = root.children['4'].children['(4, 0)'].children['NORTH_EAST']
        node = parent.children['(NORTH, NORTH)']

        self.assertTrue(node.is_terminal())
        self.assertTrue(node.terminal)
        self.assertEqual(node.tree_size, 1)
        self.assertEqual(node.parent, parent)
        self.assertEqual(node.to_move, ATTACKER)
        self.assertEqual(node.rounds_left, 0)
        self.assertEqual(node.actions_history, {ATTACKER:['b:4','g:(4, 0)','NORTH_EAST'], DEFENDER:['(NORTH, NORTH)']})
        self.assertEqual(node.actions, [])
        self.assertEqual(node.children, {})
        self.assertEqual(node.inf_set(), '.b:4.g:(4, 0).NORTH_EAST')
        self.assertEqual(node.evaluation(), 0)

    def test_terminal_attacker_caught_in_mid_game(self):
        root = self.setup_tree(2)
        parent = root.children['4'].children['(4, 0)'].children['NORTH_EAST']
        node = parent.children['(NORTH, NORTH)']

        self.assertTrue(node.is_terminal())
        self.assertTrue(node.terminal)
        self.assertEqual(node.tree_size , 1)
        self.assertEqual(node.parent, parent)
        self.assertEqual(node.to_move , ATTACKER)
        self.assertEqual(node.rounds_left, 1)
        self.assertEqual(node.actions_history, {ATTACKER:['b:4','g:(4, 0)','NORTH_EAST'], DEFENDER:['(NORTH, NORTH)']})
        self.assertEqual(node.actions, [])
        self.assertEqual(node.children, {})
        self.assertEqual(node.inf_set(), '.b:4.g:(4, 0).NORTH_EAST')
        self.assertEqual(node.evaluation(), 0)

    def assert_terminal_attacker_reached_her_goal(self, node, parent):
        self.assertTrue(node.is_terminal())
        self.assertTrue(node.terminal)
        self.assertEqual(node.tree_size , 1)
        self.assertEqual(node.parent, parent)
        self.assertEqual(node.to_move , ATTACKER)
        self.assertEqual(node.rounds_left, 1)
        self.assertEqual(node.actions_history,
                         {ATTACKER:['b:11','g:(4, 1)','EAST','EAST','EAST','EAST'],
                          DEFENDER:['(NORTH, NORTH)','(SOUTH, SOUTH)',
                                    '(NORTH, NORTH)','(SOUTH, SOUTH)']})

        self.assertEqual(node.actions, [])
        self.assertEqual(node.children, {})
        self.assertEqual(node.inf_set(), '.b:11.g:(4, 1).EAST.EAST.EAST.EAST')
        self.assertEqual(node.evaluation(), 10)

    def assert_terminal_attacker_reached_other_goal(self, node, parent):
        self.assertTrue(node.is_terminal())
        self.assertTrue(node.terminal)
        self.assertEqual(node.tree_size , 1)
        self.assertEqual(node.parent, parent)
        self.assertEqual(node.to_move , ATTACKER)
        self.assertEqual(node.rounds_left, 1)
        self.assertEqual(node.actions_history,
                         {ATTACKER:['b:11','g:(4, 0)','EAST','EAST','EAST','EAST'],
                          DEFENDER:['(NORTH, NORTH)','(SOUTH, SOUTH)',
                                    '(NORTH, NORTH)','(SOUTH, SOUTH)']})

        self.assertEqual(node.actions, [])
        self.assertEqual(node.children, {})
        self.assertEqual(node.inf_set(), '.b:11.g:(4, 0).EAST.EAST.EAST.EAST')
        self.assertEqual(node.evaluation(), -inf)

    def test_terminal_attacker_reached_goal(self):
        root = self.setup_tree(5)
        parent1 = root.children['11'].children['(4, 1)'].children['EAST'].children['(NORTH, NORTH)'] \
            .children['EAST'].children['(SOUTH, SOUTH)'] \
            .children['EAST'].children['(NORTH, NORTH)'] \
            .children['EAST']

        node1 = parent1.children['(SOUTH, SOUTH)']
        self.assert_terminal_attacker_reached_her_goal(node1, parent1)

        parent2 = root.children['11'].children['(4, 0)'].children['EAST'].children['(NORTH, NORTH)'] \
            .children['EAST'].children['(SOUTH, SOUTH)'] \
            .children['EAST'].children['(NORTH, NORTH)'] \
            .children['EAST']

        node2 = parent2.children['(SOUTH, SOUTH)']
        self.assert_terminal_attacker_reached_other_goal(node2, parent2)

    def test_evaluate_non_terminal_node(self):
        root = self.setup_tree(1)
        with self.assertRaises(RuntimeError):
            root.evaluation()
        node = root.children['4'].children['(4, 0)']
        with self.assertRaises(RuntimeError):
            node.evaluation()
        node = root.children['4'].children['(4, 0)'].children['NORTH_EAST']
        with self.assertRaises(RuntimeError):
            node.evaluation()

    def test_attacks_not_in_budget_not_in_tree(self):
        root = self.setup_tree(1)
        self.assertCountEqual(list(root.children['4'].children.keys()), ['(4, 0)'])
        self.assertCountEqual(list(root.children['5'].children.keys()), ['(4, 0)', '(4, 2)'])
        self.assertCountEqual(list(root.children['11'].children.keys()), ['(4, 0)', '(4, 2)', '(4, 1)'])


if __name__ == '__main__':
    unittest.main()
