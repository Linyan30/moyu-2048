import unittest

from moyu2048.camouflage import FRAME_COUNT, render_camouflage
from moyu2048.render import strip_ansi


class CamouflageTest(unittest.TestCase):
    def test_every_frame_renders(self):
        for index in range(FRAME_COUNT):
            plain = strip_ansi(render_camouflage(index))
            self.assertTrue(plain.strip())

    def test_no_escape_codes_left(self):
        for index in range(FRAME_COUNT):
            self.assertNotIn("\x1b", strip_ansi(render_camouflage(index)))

    def test_index_wraps_around(self):
        self.assertEqual(
            strip_ansi(render_camouflage(0)),
            strip_ansi(render_camouflage(FRAME_COUNT)),
        )

    def test_looks_like_a_shell(self):
        self.assertIn("$ git", strip_ansi(render_camouflage(0)))


if __name__ == "__main__":
    unittest.main()
