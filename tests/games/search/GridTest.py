import unittest
from math import inf
from search.Grid import Grid, Actions, OCCUPANTS, Node


class TestGrid  (unittest.TestCase):

    def test_set_attacker_goal_ok(self):
        grid = Grid()
        goal = (4,0)
        self.assertIsNone(grid.attacker_goal)
        goal_grid = grid.set_attacker_goal(goal)
        self.assertEqual(goal, goal_grid.attacker_goal)
        self.assertIsNone(grid.attacker_goal)

    def test_set_attacker_goal_raises_error(self):
        grid = Grid()
        self.assertIsNone(grid.attacker_goal)
        with self.assertRaises(ValueError):
            grid.set_attacker_goal((2,0))

    def test_get_attacker_actions(self):
        grid = Grid()
        self.assertCountEqual(grid.get_attacker_actions(), [Actions.NORTH_EAST, Actions.EAST, Actions.SOUTH_EAST])
        grid.locations[OCCUPANTS.ATTACKER] = (1,0)
        self.assertCountEqual(grid.get_attacker_actions(), [Actions.STAY, Actions.EAST])
        grid.locations[OCCUPANTS.ATTACKER] = (1,1)
        self.assertCountEqual(grid.get_attacker_actions(), [Actions.STAY, Actions.EAST])
        grid.locations[OCCUPANTS.ATTACKER] = (1,2)
        self.assertCountEqual(grid.get_attacker_actions(), [Actions.STAY, Actions.EAST])
        grid.locations[OCCUPANTS.ATTACKER] = (2,0)
        self.assertCountEqual(grid.get_attacker_actions(), [Actions.STAY, Actions.EAST, Actions.NORTH])
        grid.locations[OCCUPANTS.ATTACKER] = (2,1)
        self.assertCountEqual(grid.get_attacker_actions(), [Actions.STAY, Actions.EAST])
        grid.locations[OCCUPANTS.ATTACKER] = (2,2)
        self.assertCountEqual(grid.get_attacker_actions(), [Actions.STAY, Actions.EAST, Actions.SOUTH])
        grid.locations[OCCUPANTS.ATTACKER] = (3,0)
        self.assertCountEqual(grid.get_attacker_actions(), [Actions.STAY, Actions.EAST])
        grid.locations[OCCUPANTS.ATTACKER] = (3,1)
        self.assertCountEqual(grid.get_attacker_actions(), [Actions.STAY, Actions.EAST])
        grid.locations[OCCUPANTS.ATTACKER] = (3,2)
        self.assertCountEqual(grid.get_attacker_actions(), [Actions.STAY, Actions.EAST])
        grid.locations[OCCUPANTS.ATTACKER] = (4,0)
        self.assertCountEqual(grid.get_attacker_actions(), [])
        grid.locations[OCCUPANTS.ATTACKER] = (4,1)
        self.assertCountEqual(grid.get_attacker_actions(), [])
        grid.locations[OCCUPANTS.ATTACKER] = (4,2)
        self.assertCountEqual(grid.get_attacker_actions(), [])

    def test_get_patroller_actions(self):
        grid = Grid()
        self.assertCountEqual(grid.get_patroller_actions((1, 0)), [Actions.NORTH])
        self.assertCountEqual(grid.get_patroller_actions((1, 1)), [Actions.NORTH, Actions.SOUTH])
        self.assertCountEqual(grid.get_patroller_actions((1, 2)), [Actions.SOUTH])
        self.assertCountEqual(grid.get_patroller_actions((3, 0)), [Actions.NORTH])
        self.assertCountEqual(grid.get_patroller_actions((3, 1)), [Actions.NORTH, Actions.SOUTH])
        self.assertCountEqual(grid.get_patroller_actions((3, 2)), [Actions.SOUTH])

    def test_get_patroller_actions_raises_error(self):
            grid = Grid()
            with self.assertRaises(ValueError):
                grid.get_patroller_actions((2,0))

    def test_get_defender_actions(self):
        grid = Grid()
        grid.locations[OCCUPANTS.P1] = (1, 0)
        grid.locations[OCCUPANTS.P2] = (3, 0)
        self.assertCountEqual(grid.get_defender_actions(), [(Actions.NORTH, Actions.NORTH)])
        grid.locations[OCCUPANTS.P2] = (3, 1)
        self.assertCountEqual(grid.get_defender_actions(), [(Actions.NORTH, Actions.NORTH),
                                                            (Actions.NORTH, Actions.SOUTH)])
        grid.locations[OCCUPANTS.P2] = (3, 2)
        self.assertCountEqual(grid.get_defender_actions(), [(Actions.NORTH, Actions.SOUTH)])

        grid.locations[OCCUPANTS.P1] = (1, 1)
        grid.locations[OCCUPANTS.P2] = (3, 0)
        self.assertCountEqual(grid.get_defender_actions(), [(Actions.NORTH, Actions.NORTH),
                                                            (Actions.SOUTH, Actions.NORTH)])
        grid.locations[OCCUPANTS.P2] = (3, 1)
        self.assertCountEqual(grid.get_defender_actions(), [(Actions.NORTH, Actions.NORTH),
                                                            (Actions.SOUTH, Actions.NORTH),
                                                            (Actions.NORTH, Actions.SOUTH),
                                                            (Actions.SOUTH, Actions.SOUTH)
                                                            ])
        grid.locations[OCCUPANTS.P2] = (3, 2)
        self.assertCountEqual(grid.get_defender_actions(), [(Actions.NORTH, Actions.SOUTH),
                                                            (Actions.SOUTH, Actions.SOUTH)])

        grid.locations[OCCUPANTS.P1] = (1, 2)
        grid.locations[OCCUPANTS.P2] = (3, 0)
        self.assertCountEqual(grid.get_defender_actions(), [(Actions.SOUTH, Actions.NORTH)])
        grid.locations[OCCUPANTS.P2] = (3, 1)
        self.assertCountEqual(grid.get_defender_actions(), [(Actions.SOUTH, Actions.NORTH),
                                                            (Actions.SOUTH, Actions.SOUTH)])
        grid.locations[OCCUPANTS.P2] = (3, 2)
        self.assertCountEqual(grid.get_defender_actions(), [(Actions.SOUTH, Actions.SOUTH)])


    def test_get_new_location(self):
        grid = Grid()
        self.assertEqual(grid.get_new_location(2,2, Actions.NORTH_EAST), (3,3))
        self.assertEqual(grid.get_new_location(2,2, Actions.SOUTH_EAST), (3,1))
        self.assertEqual(grid.get_new_location(2,2, Actions.NORTH), (2,3))
        self.assertEqual(grid.get_new_location(2,2, Actions.SOUTH), (2,1))
        self.assertEqual(grid.get_new_location(2,2, Actions.EAST),  (3,2))
        self.assertEqual(grid.get_new_location(2,2, Actions.STAY),  (2,2))

    def test_attacker_caghut(self):
        grid = Grid()
        grid.locations[OCCUPANTS.ATTACKER] = (1, 1)
        grid.locations[OCCUPANTS.P1] = (1, 1)
        grid.locations[OCCUPANTS.P2] = (2, 1)
        self.assertTrue(grid.attacker_caught())
        grid.locations[OCCUPANTS.P1] = (1, 2)
        self.assertFalse(grid.attacker_caught())
        grid.locations[OCCUPANTS.P2] = (1, 1)
        self.assertTrue(grid.attacker_caught())

    def test_get_games_values(self):
        grid = Grid()
        self.assertEqual(grid.get_game_value(), -inf)
        grid.locations[OCCUPANTS.ATTACKER] = (1, 1)
        grid.locations[OCCUPANTS.P1] = (1, 1)
        grid.locations[OCCUPANTS.P2] = (2, 1)
        self.assertEqual(grid.get_game_value(), 0)
        grid.locations[OCCUPANTS.ATTACKER] = (4, 0)
        grid = grid.set_attacker_goal((4,0))
        self.assertEqual(grid.get_game_value(), 3)
        grid = grid.set_attacker_goal((4, 1))
        self.assertEqual(grid.get_game_value(), -inf)
        grid = grid.set_attacker_goal((4, 2))
        self.assertEqual(grid.get_game_value(), -inf)
        grid.locations[OCCUPANTS.ATTACKER] = (4, 1)
        grid = grid.set_attacker_goal((4,0))
        self.assertEqual(grid.get_game_value(), -inf)
        grid = grid.set_attacker_goal((4, 1))
        self.assertEqual(grid.get_game_value(), 10)
        grid = grid.set_attacker_goal((4, 2))
        self.assertEqual(grid.get_game_value(), -inf)
        grid.locations[OCCUPANTS.ATTACKER] = (4, 2)
        grid = grid.set_attacker_goal((4,0))
        self.assertEqual(grid.get_game_value(), -inf)
        grid = grid.set_attacker_goal((4, 1))
        self.assertEqual(grid.get_game_value(), -inf)
        grid = grid.set_attacker_goal((4, 2))
        self.assertEqual(grid.get_game_value(), 5)

    def test_update_matrix(self):
        grid = Grid()
        two_one = grid.matrix[(2, 1)]
        zero_one = grid.matrix[(0, 1)]
        self.assertCountEqual(zero_one.occupants , [OCCUPANTS.ATTACKER])
        self.assertIsNone(zero_one.payoff)
        self.assertFalse(zero_one.tracks)
        #attacker moves from (0,1) to (1,1)
        grid.update_matrix(OCCUPANTS.ATTACKER, Actions.EAST)
        self.assertListEqual(zero_one.occupants,[])
        self.assertIsNone(zero_one.payoff)
        self.assertFalse(zero_one.tracks)
        one_one = grid.matrix[(1, 1)]
        self.assertCountEqual(one_one.occupants,[OCCUPANTS.ATTACKER, OCCUPANTS.P1])
        self.assertIsNone(one_one.payoff)
        self.assertFalse(one_one.tracks)

        three_one = grid.matrix[(3, 1)]
        self.assertCountEqual(three_one.occupants,[OCCUPANTS.P2])
        three_zero = grid.matrix[(3, 0)]
        self.assertCountEqual(three_zero.occupants, [])
        #P2 moves from (3,1) t0 (3,0)

        grid.update_matrix(OCCUPANTS.P2, Actions.SOUTH)
        self.assertListEqual(three_one.occupants,[])
        self.assertIsNone(three_one.payoff)
        self.assertFalse(three_one.tracks)

        self.assertCountEqual(three_zero.occupants,[OCCUPANTS.P2])
        self.assertIsNone(three_zero.payoff)
        self.assertFalse(three_zero.tracks)
        # attacker moves from (1,1) to (2,1)
        grid.update_matrix(OCCUPANTS.ATTACKER, Actions.EAST, True)
        two_one = grid.matrix[(2, 1)]
        self.assertListEqual(one_one.occupants,[OCCUPANTS.P1])
        self.assertIsNone(one_one.payoff)
        self.assertTrue(one_one.tracks)

        self.assertCountEqual(two_one.occupants,[OCCUPANTS.ATTACKER])
        self.assertIsNone(two_one.payoff)
        self.assertFalse(two_one.tracks)

    def test_apply_attacker_action(self):
        grid = Grid()
        new_grid = grid.apply_attacker_action(Actions.EAST)
        self.assertEqual(grid.locations[OCCUPANTS.ATTACKER], (0,1))
        self.assertEqual(grid.locations[OCCUPANTS.P1], (1,1))
        self.assertEqual(grid.locations[OCCUPANTS.P2], (3,1))
        self.assertListEqual(grid.matrix[(0, 1)].occupants, [OCCUPANTS.ATTACKER])
        self.assertListEqual(grid.matrix[(1, 1)].occupants, [OCCUPANTS.P1])
        self.assertListEqual(grid.matrix[(3, 1)].occupants, [OCCUPANTS.P2])

        self.assertEqual(new_grid.locations[OCCUPANTS.ATTACKER], (1,1))
        self.assertEqual(new_grid.locations[OCCUPANTS.P1], (1,1))
        self.assertEqual(new_grid.locations[OCCUPANTS.P2], (3,1))
        self.assertCountEqual(new_grid.matrix[(0, 1)].occupants, [])
        self.assertCountEqual(new_grid.matrix[(1, 1)].occupants, [OCCUPANTS.P1, OCCUPANTS.ATTACKER])
        self.assertListEqual(new_grid.matrix[(3, 1)].occupants, [OCCUPANTS.P2])

    def test_apply_defender_action(self):
        grid = Grid()
        new_grid = grid.apply_defender_action(Actions.NORTH, Actions.SOUTH)
        self.assertEqual(grid.locations[OCCUPANTS.ATTACKER], (0, 1))
        self.assertEqual(grid.locations[OCCUPANTS.P1], (1, 1))
        self.assertEqual(grid.locations[OCCUPANTS.P2], (3, 1))
        self.assertListEqual(grid.matrix[(0, 1)].occupants, [OCCUPANTS.ATTACKER])
        self.assertListEqual(grid.matrix[(1, 1)].occupants, [OCCUPANTS.P1])
        self.assertListEqual(grid.matrix[(3, 1)].occupants, [OCCUPANTS.P2])

        self.assertEqual(new_grid.locations[OCCUPANTS.ATTACKER], (0, 1))
        self.assertEqual(new_grid.locations[OCCUPANTS.P1], (1, 2))
        self.assertEqual(new_grid.locations[OCCUPANTS.P2], (3, 0))
        self.assertCountEqual(new_grid.matrix[(1, 1)].occupants, [])
        self.assertListEqual(new_grid.matrix[(3, 1)].occupants, [])
        self.assertCountEqual(new_grid.matrix[(0, 1)].occupants, [OCCUPANTS.ATTACKER])
        self.assertCountEqual(new_grid.matrix[(1, 2)].occupants, [OCCUPANTS.P1])
        self.assertListEqual(new_grid.matrix[(3, 0)].occupants, [OCCUPANTS.P2])

    def test_get_attacks_in_budget_dict(self):
        grid = Grid()
        budgets = [4, 5, 11]
        expected_dict = {4:[(4,0)],5:[(4,0),(4,2)],11:[(4,0),(4,1), (4,2)]}
        self.assertDictEqual(expected_dict, grid.get_attacks_in_budget_dict(budgets))

    def test_get_attacks_probabilities(self):
        grid = Grid()
        budgets = [4, 5, 11]
        expected_probs = {(4,0):11./18., (4, 1):2./18, (4, 2): 5./18}
        self.assertDictEqual(expected_probs, grid.get_attacks_probabilities(budgets))

    def test_attacker_reached_her_goal(self):
        grid = Grid().set_attacker_goal((4, 0))
        self.assertFalse(grid.attacker_reached_her_goal())
        grid.locations[OCCUPANTS.ATTACKER] = (4, 0)
        self.assertTrue(grid.attacker_reached_her_goal())

    def test_attacker_caught(self):
        grid = Grid()
        self.assertFalse(grid.attacker_caught())
        grid.locations[OCCUPANTS.ATTACKER] = (1,1)
        self.assertTrue(grid.attacker_caught())
        grid.locations[OCCUPANTS.ATTACKER] = (1, 0)
        self.assertFalse(grid.attacker_caught())
        grid.locations[OCCUPANTS.ATTACKER] = (3, 1)
        self.assertTrue(grid.attacker_caught())


if __name__ == '__main__':
    unittest.main()
