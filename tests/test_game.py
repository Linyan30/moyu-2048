import unittest

from moyu2048.game import Game, merge_line

EMPTY_ROW = [0, 0, 0, 0]


def make(rows, score=0):
    return Game(rows=rows, auto_spawn=False, size=len(rows))


class MergeLineTest(unittest.TestCase):
    def test_pushes_tiles_to_the_front(self):
        self.assertEqual(merge_line([0, 2, 0, 4]), ([2, 4, 0, 0], 0))

    def test_merges_equal_pair(self):
        self.assertEqual(merge_line([2, 2, 0, 0]), ([4, 0, 0, 0], 4))

    def test_each_tile_merges_at_most_once(self):
        self.assertEqual(merge_line([2, 2, 2, 2]), ([4, 4, 0, 0], 8))

    def test_merges_closest_pair_first(self):
        self.assertEqual(merge_line([0, 2, 2, 4]), ([4, 4, 0, 0], 4))

    def test_full_row(self):
        self.assertEqual(merge_line([4, 4, 4, 4]), ([8, 8, 0, 0], 16))

    def test_empty_row(self):
        self.assertEqual(merge_line([0, 0, 0, 0]), ([0, 0, 0, 0], 0))


class GameTest(unittest.TestCase):
    def test_new_game_has_two_tiles(self):
        game = Game(seed=1)
        self.assertEqual(len(game.empty_cells()), 14)
        self.assertEqual(game.score, 0)
        self.assertEqual(game.moves, 0)

    def test_spawn_only_places_two_or_four(self):
        values = {value for row in Game(seed=3).grid for value in row if value}
        self.assertTrue(values <= {2, 4})

    def test_move_left_merges(self):
        game = make([[2, 2, 0, 0], EMPTY_ROW, EMPTY_ROW, EMPTY_ROW])
        result = game.move("left")
        self.assertTrue(result.changed)
        self.assertEqual(result.gained, 4)
        self.assertEqual(game.grid[0], [4, 0, 0, 0])
        self.assertEqual(game.score, 4)
        self.assertEqual(game.moves, 1)

    def test_move_right(self):
        game = make([[2, 2, 4, 0], EMPTY_ROW, EMPTY_ROW, EMPTY_ROW])
        game.move("right")
        self.assertEqual(game.grid[0], [0, 0, 4, 4])

    def test_move_up(self):
        game = make([[2, 0, 0, 0], [2, 0, 0, 0], EMPTY_ROW, EMPTY_ROW])
        game.move("up")
        self.assertEqual(game.grid[0][0], 4)
        self.assertEqual(game.grid[1][0], 0)

    def test_move_down(self):
        game = make([[2, 0, 0, 0], [2, 0, 0, 0], EMPTY_ROW, EMPTY_ROW])
        game.move("down")
        self.assertEqual(game.grid[3][0], 4)
        self.assertEqual(game.grid[2][0], 0)

    def test_no_double_merge(self):
        game = make([[2, 2, 2, 0], EMPTY_ROW, EMPTY_ROW, EMPTY_ROW])
        game.move("left")
        self.assertEqual(game.grid[0], [4, 2, 0, 0])
        self.assertEqual(game.score, 4)

    def test_blocked_move_reports_unchanged(self):
        game = make([[2, 4, 8, 16], EMPTY_ROW, EMPTY_ROW, EMPTY_ROW])
        result = game.move("left")
        self.assertFalse(result.changed)
        self.assertEqual(game.score, 0)
        self.assertEqual(game.moves, 0)

    def test_unknown_direction(self):
        with self.assertRaises(ValueError):
            Game(seed=1).move("diagonal")

    def test_undo_restores_board_and_score(self):
        game = make([[2, 2, 0, 0], EMPTY_ROW, EMPTY_ROW, EMPTY_ROW])
        before = [row[:] for row in game.grid]
        game.move("left")
        self.assertTrue(game.undo())
        self.assertEqual(game.grid, before)
        self.assertEqual(game.score, 0)
        self.assertEqual(game.moves, 0)

    def test_undo_without_history(self):
        game = make([[2, 0, 0, 0], EMPTY_ROW, EMPTY_ROW, EMPTY_ROW])
        self.assertFalse(game.undo())

    def test_game_over_on_full_blocked_board(self):
        rows = [
            [2, 4, 2, 4],
            [4, 2, 4, 2],
            [2, 4, 2, 4],
            [4, 2, 4, 2],
        ]
        game = make(rows)
        self.assertTrue(game.over)
        self.assertFalse(game.can_move())
        self.assertFalse(game.move("left").changed)

    def test_not_over_while_a_merge_is_available(self):
        game = make(
            [
                [2, 2, 4, 8],
                [4, 8, 16, 32],
                [8, 16, 32, 64],
                [16, 32, 64, 128],
            ]
        )
        self.assertFalse(game.over)
        self.assertTrue(game.can_move())

    def test_win_sets_flag(self):
        game = make([[1024, 1024, 0, 0], EMPTY_ROW, EMPTY_ROW, EMPTY_ROW])
        game.move("left")
        self.assertTrue(game.won)
        self.assertEqual(game.max_tile(), 2048)

    def test_spawn_on_full_board_returns_none(self):
        game = make(
            [
                [2, 4, 2, 4],
                [4, 2, 4, 2],
                [2, 4, 2, 4],
                [4, 2, 4, 2],
            ]
        )
        self.assertIsNone(game.spawn())

    def test_size_bounds(self):
        with self.assertRaises(ValueError):
            Game(size=2)
        with self.assertRaises(ValueError):
            Game(size=9)

    def test_rows_shape_must_match_size(self):
        with self.assertRaises(ValueError):
            Game(size=3, rows=[[0, 0, 0]])

    def test_dict_roundtrip(self):
        game = make([[2, 2, 0, 0], EMPTY_ROW, EMPTY_ROW, EMPTY_ROW])
        game.move("left")
        restored = Game.from_dict(game.to_dict())
        self.assertEqual(restored.grid, game.grid)
        self.assertEqual(restored.score, game.score)
        self.assertEqual(restored.size, game.size)


if __name__ == "__main__":
    unittest.main()
