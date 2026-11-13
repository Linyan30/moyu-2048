import unittest

from moyu2048.game import Game
from moyu2048.render import (
    board_lines,
    clip_line,
    format_duration,
    format_money,
    render_game,
    strip_ansi,
)

EMPTY_ROW = [0, 0, 0, 0]


class BoardRenderTest(unittest.TestCase):
    def setUp(self):
        self.game = Game(
            rows=[[2, 4, 0, 0], EMPTY_ROW, EMPTY_ROW, EMPTY_ROW],
            auto_spawn=False,
        )

    def test_line_count(self):
        lines = board_lines(self.game)
        self.assertEqual(len(lines), self.game.size * 2 + 1)

    def test_default_border_is_ascii(self):
        lines = board_lines(self.game)
        self.assertTrue(lines[0].startswith("+"))
        self.assertNotIn("│", "\n".join(lines))

    def test_unicode_border(self):
        lines = board_lines(self.game, unicode_borders=True)
        self.assertTrue(lines[0].startswith("┌"))
        self.assertNotIn("+", "\n".join(lines))

    def test_empty_cell_marker(self):
        self.assertIn(".", "\n".join(board_lines(self.game)))
        self.assertIn("·", "\n".join(board_lines(self.game, unicode_borders=True)))


class FrameTest(unittest.TestCase):
    def setUp(self):
        self.game = Game(
            rows=[[2, 4, 0, 0], EMPTY_ROW, EMPTY_ROW, EMPTY_ROW],
            auto_spawn=False,
        )

    def test_frame_contains_score_and_best(self):
        text = render_game(self.game, 8932)
        self.assertIn("分数", text)
        self.assertIn("8932", text)

    def test_frame_has_no_escape_codes_left(self):
        text = render_game(self.game, 100, theme="color")
        self.assertNotIn("\x1b", strip_ansi(text))

    def test_message_is_shown(self):
        text = render_game(self.game, 100, message="无处可走了")
        self.assertIn("无处可走了", text)


class ClipLineTest(unittest.TestCase):
    def test_short_line_is_unchanged(self):
        self.assertEqual(strip_ansi(clip_line("hello", 10)), "hello")

    def test_long_line_is_cut(self):
        self.assertEqual(strip_ansi(clip_line("hello world", 5)), "hello")

    def test_wide_characters_take_two_cells(self):
        self.assertEqual(strip_ansi(clip_line("中文字", 4)), "中文")

    def test_ansi_is_kept(self):
        clipped = clip_line("\x1b[31mhello", 2)
        self.assertTrue(clipped.startswith("\x1b[31m"))
        self.assertEqual(strip_ansi(clipped), "he")

    def test_zero_width_returns_empty(self):
        self.assertEqual(clip_line("hello", 0), "")


class FormatTest(unittest.TestCase):
    def test_duration(self):
        self.assertEqual(format_duration(0), "0 秒")
        self.assertEqual(format_duration(59), "59 秒")
        self.assertEqual(format_duration(125), "2 分 5 秒")
        self.assertEqual(format_duration(3660), "1 小时 1 分")

    def test_money(self):
        self.assertEqual(format_money(3600, 50), "¥50")
        self.assertEqual(format_money(0, 50), "¥0")


if __name__ == "__main__":
    unittest.main()
