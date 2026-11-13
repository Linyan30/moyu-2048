import json
import os
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path

from moyu2048 import stats as stats_module
from moyu2048.stats import Stats


def make_temp_dir(prefix="moyu2048-test-"):
    """在临时目录下建一个普通目录。

    不用 ``tempfile.mkdtemp``，它在某些受限环境里会建出自己都写不进去的目录。
    """
    path = Path(tempfile.gettempdir()) / f"{prefix}{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    return path


class StatsTest(unittest.TestCase):
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

    def test_missing_file_gives_empty_stats(self):
        stats = Stats.load()
        self.assertEqual(stats.games, 0)
        self.assertEqual(stats.best, {})

    def test_roundtrip(self):
        stats = Stats()
        stats.record_game(4, 1250, 88)
        stats.add_seconds(90)
        stats.save()

        restored = Stats.load()
        self.assertEqual(restored.games, 1)
        self.assertEqual(restored.moves, 88)
        self.assertEqual(restored.best_for(4), 1250)
        self.assertAlmostEqual(restored.seconds, 90)

    def test_best_only_grows(self):
        stats = Stats()
        stats.record_game(4, 500, 10)
        stats.record_game(4, 100, 5)
        self.assertEqual(stats.best_for(4), 500)

    def test_best_is_per_board_size(self):
        stats = Stats()
        stats.record_game(3, 300, 10)
        stats.record_game(4, 900, 10)
        self.assertEqual(stats.best_for(3), 300)
        self.assertEqual(stats.best_for(4), 900)
        self.assertEqual(stats.best_for(5), 0)

    def test_corrupt_file_is_ignored(self):
        path = stats_module.stats_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{not json", encoding="utf-8")
        self.assertEqual(Stats.load().games, 0)

    def test_saved_file_is_valid_json(self):
        Stats().save()
        payload = json.loads(stats_module.stats_path().read_text(encoding="utf-8"))
        self.assertEqual(payload["version"], 1)

    def test_render_mentions_time_and_money(self):
        stats = Stats()
        stats.add_seconds(3600)
        text = stats.render(rate=50)
        self.assertIn("1 小时 0 分", text)
        self.assertIn("¥50", text)


if __name__ == "__main__":
    unittest.main()
