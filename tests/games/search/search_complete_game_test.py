import unittest
from math import inf

from constants import CHANCE, ATTACKER, DEFENDER
from search.Grid import Grid, Actions, MAX_VALUE
from search.search_common_players import SearchAttackerMoveGameState, SearchDefenderMoveGameState, \
    SearchGridMoveGameState
from search.search_players_complete_game import SearchCompleteGameRootChanceGameState, \
    SearchCompleteGameSelectorGameState


class TestSearchCompleteGame  (unittest.TestCase):

    def setup_tree(self, rounds_left):
        grid = Grid(rounds_left)
        attacker_budgets = [4, 5, 11]

        root = SearchCompleteGameRootChanceGameState(grid=grid, attacker_budgets=attacker_budgets, rounds_left= rounds_left)
        return root

    def test_chance_root_ok(self):
        root = self.setup_tree(1)
        self.assertEqual(root.tree_size, 172) #28*6 +3 +1
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
        self.assertEqual(node.tree_size, 57)
        self.assertEqual(node.parent, root)
        self.assertEqual(node.to_move, ATTACKER)
        self.assertEqual(node.rounds_left, 1)
        self.assertEqual(node.location_history, {ATTACKER: ['5'],
                                                 DEFENDER: []})
        self.assertCountEqual(node.actions,['(4, 0)', '(4, 2)'])
        self.assertCountEqual(list(node.children.keys()), ['(4, 0)', '(4, 2)'])
        self.assertEqual(node.inf_set(), '.5')
        for child in node.children.values():
            self.assertTrue(isinstance(child, SearchAttackerMoveGameState))

    def test_non_terminal_attacker_node(self):
        root = self.setup_tree(1)
        parent = root.children['4']
        node = parent.children['(4, 0)']
        self.assertFalse(node.is_terminal())
        self.assertFalse(node.terminal)
        self.assertEqual(node.tree_size, 28)
        self.assertEqual(node.parent, parent)
        self.assertEqual(node.to_move, ATTACKER)
        self.assertEqual(node.rounds_left, 1)
        self.assertEqual(node.location_history, {ATTACKER:['4', 'g:(4, 0)', '(0, 1)'],
                                                 DEFENDER:['(((1, 1), False), ((3, 1), False))']})
        self.assertCountEqual(node.actions,
                              ['EAST','NORTH_EAST', 'SOUTH_EAST'])
        self.assertCountEqual(list(node.children.keys()),
                              ['EAST','NORTH_EAST', 'SOUTH_EAST'])
        self.assertEqual(node.inf_set(), ".4.g:(4, 0).(0, 1).False")
        for child in node.children.values():
            self.assertTrue(isinstance(child, SearchDefenderMoveGameState))

    def test_non_terminal_defender_node(self):
        root = self.setup_tree(1)
        parent = root.children['4'].children['(4, 0)']
        node = parent.children['EAST']

        self.assertFalse(node.is_terminal())
        self.assertFalse(node.terminal)
        self.assertEqual(node.tree_size, 9)
        self.assertEqual(node.parent, parent)
        self.assertEqual(node.to_move, DEFENDER)
        self.assertEqual(node.rounds_left, 1)
        self.assertEqual(node.location_history, {ATTACKER:['4', 'g:(4, 0)', '(0, 1)'],
                                                 DEFENDER:['(((1, 1), False), ((3, 1), False))']})
        actions = ['(NORTH, NORTH)',
                   '(NORTH, SOUTH)',
                   '(SOUTH, NORTH)',
                   '(SOUTH, SOUTH)']

        self.assertCountEqual(node.actions,actions)
        self.assertCountEqual(list(node.children.keys()), actions)
        self.assertEqual(node.inf_set(), ".(((1, 1), False), ((3, 1), False))")
        for child in node.children.values():
            self.assertTrue(isinstance(child, SearchGridMoveGameState))

    def test_terminal_attacker_node_not_caught(self):
        root = self.setup_tree(1)
        parent = root.children['4'].children['(4, 0)'].children['EAST'].children['(NORTH, NORTH)']
        node = parent.children['GRID']

        self.assertTrue(node.is_terminal())
        self.assertTrue(node.terminal)
        self.assertEqual(node.tree_size , 1)
        self.assertEqual(node.parent, parent)
        self.assertEqual(node.to_move , ATTACKER)
        self.assertEqual(node.rounds_left, 0)
        self.assertEqual(node.location_history, {ATTACKER:['4', 'g:(4, 0)', '(0, 1)', '(1, 1)'],
                                                 DEFENDER:['(((1, 1), False), ((3, 1), False))',
                                                           '(((1, 2), False), ((3, 2), False))']})
        self.assertEqual(node.actions, [])
        self.assertEqual(node.children, {})
        self.assertEqual(node.inf_set(), '.4.g:(4, 0).(0, 1).(1, 1).False')
        self.assertEqual(node.evaluation(), MAX_VALUE)

    def test_terminal_attacker_node_caught(self):
        root = self.setup_tree(1)
        parent = root.children['4'].children['(4, 0)'].children['NORTH_EAST'].children['(NORTH, NORTH)']
        node = parent.children['GRID']

        self.assertTrue(node.is_terminal())
        self.assertTrue(node.terminal)
        self.assertEqual(node.tree_size, 1)
        self.assertEqual(node.parent, parent)
        self.assertEqual(node.to_move, ATTACKER)
        self.assertEqual(node.rounds_left, 0)
        self.assertEqual(node.location_history, {ATTACKER: ['4', 'g:(4, 0)', '(0, 1)', '(1, 2)'],
                                                 DEFENDER: ['(((1, 1), False), ((3, 1), False))',
                                                            '(((1, 2), False), ((3, 2), False))']})
        self.assertEqual(node.actions, [])
        self.assertEqual(node.children, {})
        self.assertEqual(node.inf_set(), '.4.g:(4, 0).(0, 1).(1, 2).True')
        self.assertEqual(node.evaluation(), 0)

    def test_terminal_attacker_caught_in_mid_game(self):
        root = self.setup_tree(2)
        parent = root.children['4'].children['(4, 0)'].children['NORTH_EAST'].children['(NORTH, NORTH)']
        node = parent.children['GRID']

        self.assertTrue(node.is_terminal())
        self.assertTrue(node.terminal)
        self.assertEqual(node.tree_size, 1)
        self.assertEqual(node.parent, parent)
        self.assertEqual(node.to_move , ATTACKER)
        self.assertEqual(node.rounds_left, 1)
        self.assertEqual(node.location_history, {ATTACKER: ['4', 'g:(4, 0)', '(0, 1)', '(1, 2)'],
                                                 DEFENDER: ['(((1, 1), False), ((3, 1), False))',
                                                            '(((1, 2), False), ((3, 2), False))']})
        self.assertEqual(node.actions, [])
        self.assertEqual(node.children, {})
        self.assertEqual(node.inf_set(), '.4.g:(4, 0).(0, 1).(1, 2).True')
        self.assertEqual(node.evaluation(), 0)

    def assert_terminal_attacker_reached_her_goal(self, node, parent):
        self.assertTrue(node.is_terminal())
        self.assertTrue(node.terminal)
        self.assertEqual(node.tree_size , 1)
        self.assertEqual(node.parent, parent)
        self.assertEqual(node.to_move , ATTACKER)
        self.assertEqual(node.rounds_left, 1)

        self.assertEqual(node.location_history,
                         {ATTACKER: ['11', 'g:(4, 1)', '(0, 1)', '(1, 1)','(2, 1)','(3, 1)','(4, 1)'],
                          DEFENDER: ['(((1, 1), False), ((3, 1), False))',
                                     '(((1, 2), False), ((3, 2), False))',
                                     '(((1, 1), True), ((3, 1), False))',
                                     '(((1, 2), False), ((3, 2), False))',
                                     '(((1, 1), True), ((3, 1), True))']})


        self.assertEqual(node.actions, [])
        self.assertEqual(node.children, {})
        self.assertEqual(node.inf_set(), '.11.g:(4, 1).(0, 1).(1, 1).(2, 1).(3, 1).(4, 1).False')
        self.assertEqual(node.evaluation(), -10)

    def assert_terminal_attacker_reached_other_goal(self, node, parent):
        self.assertTrue(node.is_terminal())
        self.assertTrue(node.terminal)
        self.assertEqual(node.tree_size , 1)
        self.assertEqual(node.parent, parent)
        self.assertEqual(node.to_move , ATTACKER)
        self.assertEqual(node.rounds_left, 1)
        self.assertEqual(node.location_history,
                         {ATTACKER: ['11', 'g:(4, 0)', '(0, 1)', '(1, 1)', '(2, 1)', '(3, 1)', '(4, 1)'],
                          DEFENDER: ['(((1, 1), False), ((3, 1), False))',
                                     '(((1, 2), False), ((3, 2), False))',
                                     '(((1, 1), True), ((3, 1), False))',
                                     '(((1, 2), False), ((3, 2), False))',
                                     '(((1, 1), True), ((3, 1), True))']})

        self.assertEqual(node.actions, [])
        self.assertEqual(node.children, {})
        self.assertEqual(node.inf_set(), '.11.g:(4, 0).(0, 1).(1, 1).(2, 1).(3, 1).(4, 1).False')
        self.assertEqual(node.evaluation(), MAX_VALUE)

    def test_terminal_attacker_reached_goal(self):
        root = self.setup_tree(5)
        parent1 = root.children['11'].children['(4, 1)'].children['EAST'].children['(NORTH, NORTH)'].children['GRID'] \
            .children['EAST'].children['(SOUTH, SOUTH)'].children['GRID'] \
            .children['EAST'].children['(NORTH, NORTH)'].children['GRID'] \
            .children['EAST'].children['(SOUTH, SOUTH)']

        node1 = parent1.children['GRID']
        self.assert_terminal_attacker_reached_her_goal(node1, parent1)

        parent2 = root.children['11'].children['(4, 0)'].children['EAST'].children['(NORTH, NORTH)'].children['GRID'] \
            .children['EAST'].children['(SOUTH, SOUTH)'].children['GRID'] \
            .children['EAST'].children['(NORTH, NORTH)'].children['GRID'] \
            .children['EAST'].children['(SOUTH, SOUTH)']

        node2 = parent2.children['GRID']
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
