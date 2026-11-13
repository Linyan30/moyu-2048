"""摸鱼统计：只写本地 JSON，不发任何网络请求。

数据默认放在 ``~/.moyu2048/stats.json``；设置环境变量 ``MOYU2048_HOME``
可以换到别的目录，想完全不留痕时很有用：

    MOYU2048_HOME=$(mktemp -d) moyu
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

APP_DIR_ENV = "MOYU2048_HOME"
DEFAULT_RATE = 50.0


def data_dir():
    override = os.environ.get(APP_DIR_ENV)
    if override:
        return Path(override).expanduser()
    return Path.home() / ".moyu2048"


def stats_path():
    return data_dir() / "stats.json"


@dataclass
class Stats:
    games: int = 0
    moves: int = 0
    seconds: float = 0.0
    best: dict = field(default_factory=dict)

    @classmethod
    def load(cls, path=None):
        path = Path(path) if path is not None else stats_path()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls()
        if not isinstance(raw, dict):
            return cls()
        best = {}
        for key, value in (raw.get("best") or {}).items():
            try:
                best[int(key)] = int(value)
            except (TypeError, ValueError):
                continue
        try:
            return cls(
                games=int(raw.get("games", 0)),
                moves=int(raw.get("moves", 0)),
                seconds=float(raw.get("seconds", 0.0)),
                best=best,
            )
        except (TypeError, ValueError):
            return cls()

    def save(self, path=None):
        path = Path(path) if path is not None else stats_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "games": self.games,
            "moves": self.moves,
            "seconds": round(self.seconds, 1),
            "best": {str(key): value for key, value in sorted(self.best.items())},
        }
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)

    def best_for(self, size):
        return int(self.best.get(size, 0))

    def record_game(self, size, score, moves):
        self.games += 1
        self.moves += int(moves)
        if score > self.best_for(size):
            self.best[size] = int(score)

    def add_seconds(self, seconds):
        self.seconds += max(0.0, float(seconds))

    def render(self, rate=DEFAULT_RATE):
        best = max(self.best.values()) if self.best else 0
        return "\n".join(
            [
                f" 累计摸鱼  {format_duration(self.seconds)}",
                f" 完成对局  {self.games} 局",
                f" 累计步数  {self.moves:,}",
                f" 最高分    {best:,}",
                f" 按时薪 {rate:g} 元算，你已经摸回 {format_money(self.seconds, rate)}",
            ]
        )


def format_duration(seconds):
    seconds = max(0, int(seconds))
    if seconds < 60:
        return f"{seconds} 秒"
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes} 分 {seconds} 秒"
    hours, minutes = divmod(minutes, 60)
    return f"{hours} 小时 {minutes} 分"


def format_money(seconds, rate=DEFAULT_RATE):
    return f"¥{seconds / 3600 * rate:,.0f}"
