import io
import os
import shutil
import tempfile
import unittest
import uuid
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from moyu2048 import cli as cli_module
from moyu2048 import stats as stats_module
from moyu2048.cli import build_parser, main


def make_temp_dir(prefix="moyu2048-test-"):
    path = Path(tempfile.gettempdir()) / f"{prefix}{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    return path


class FakeKeys:
    """按顺序吐出预设按键，模拟 KeyReader。"""

    def __init__(self, keys):
        self._keys = list(keys)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def read(self):
        return self._keys.pop(0) if self._keys else "quit"


class ParserTest(unittest.TestCase):
    def test_defaults(self):
        args = build_parser().parse_args([])
        self.assertEqual(args.size, 4)
        self.assertFalse(args.color)
        self.assertFalse(args.boss)
        self.assertFalse(args.unicode)
        self.assertIsNone(args.demo)

    def test_board_size_is_validated(self):
        with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()):
            build_parser().parse_args(["--size", "9"])


class MainTest(unittest.TestCase):
    def setUp(self):
        self.home_dir = make_temp_dir()
        self.home = os.environ.get(stats_module.APP_DIR_ENV)
        os.environ[stats_module.APP_DIR_ENV] = str(self.home_dir)
        self.addCleanup(self.restore_home)

    def restore_home(self):
        if self.home is None:
            os.environ.pop(stats_module.APP_DIR_ENV, None)
        else:
            os.environ[stats_module.APP_DIR_ENV] = self.home
        shutil.rmtree(self.home_dir, ignore_errors=True)

    def run_main(self, argv):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(argv)
        return code, output.getvalue()

    def test_demo_mode_is_deterministic_and_plain(self):
        code, output = self.run_main(["--demo", "80", "--seed", "7"])
        self.assertEqual(code, 0)
        self.assertIn("moyu-2048", output)
        self.assertNotIn("\x1b", output)

    def test_demo_does_not_touch_stats(self):
        self.run_main(["--demo", "20", "--seed", "1"])
        self.assertEqual(stats_module.Stats.load().games, 0)

    def test_stats_command(self):
        code, output = self.run_main(["--stats"])
        self.assertEqual(code, 0)
        self.assertIn("累计摸鱼", output)

    def test_reset_removes_stats_file(self):
        stats_module.Stats().save()
        self.assertTrue(stats_module.stats_path().exists())
        code, _ = self.run_main(["--reset"])
        self.assertEqual(code, 0)
        self.assertFalse(stats_module.stats_path().exists())

    def run_with_keys(self, keys):
        args = build_parser().parse_args([])
        output = io.StringIO()
        with mock.patch.object(
            cli_module, "KeyReader", return_value=FakeKeys(keys)
        ), redirect_stdout(output):
            code = cli_module.run_game(args)
        return code, output.getvalue()

    def test_q_quits(self):
        code, output = self.run_with_keys(["q"])
        self.assertEqual(code, 0)
        self.assertIn("本次", output)

    def test_escape_toggles_camouflage(self):
        _, output = self.run_with_keys(["esc", "q"])
        self.assertIn("[esc]", output)


if __name__ == "__main__":
    unittest.main()
