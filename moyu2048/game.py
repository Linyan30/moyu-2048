"""2048 的核心规则：纯逻辑，不读键盘、不打印，方便单元测试。"""

from __future__ import annotations

import random
from dataclasses import dataclass

DIRECTIONS = ("up", "down", "left", "right")
DEFAULT_SIZE = 4
MIN_SIZE = 3
MAX_SIZE = 8
WIN_VALUE = 2048
SPAWN_FOUR_RATE = 0.1
MAX_UNDO = 20


def merge_line(values):
    """向行首压缩并合并一行，返回 ``(新行, 得分)``。

    每个方块在一次移动里最多只合并一次，所以 ``[2, 2, 2, 2]`` 得到
    ``[4, 4, 0, 0]``，而不会一路合成一个 8。
    """
    tiles = [value for value in values if value]
    merged = []
    gained = 0
    index = 0
    while index < len(tiles):
        if index + 1 < len(tiles) and tiles[index] == tiles[index + 1]:
            value = tiles[index] * 2
            merged.append(value)
            gained += value
            index += 2
        else:
            merged.append(tiles[index])
            index += 1
    return merged + [0] * (len(values) - len(merged)), gained


@dataclass(frozen=True)
class MoveResult:
    """一次移动的结果。``changed`` 为 False 时棋盘没有变化。"""

    changed: bool
    gained: int = 0
    spawned: bool = False


class Game:
    """一局 2048。``rows`` 用于测试或复现指定局面。"""

    def __init__(
        self,
        size=DEFAULT_SIZE,
        seed=None,
        target=WIN_VALUE,
        rows=None,
        auto_spawn=True,
    ):
        if not MIN_SIZE <= size <= MAX_SIZE:
            raise ValueError(f"棋盘大小必须在 {MIN_SIZE} 到 {MAX_SIZE} 之间")
        self.size = size
        self.target = target
        self.rng = random.Random(seed)
        self.auto_spawn = auto_spawn
        self.grid = [[0] * size for _ in range(size)]
        self.score = 0
        self.moves = 0
        self._undo_stack = []
        if rows is not None:
            self._load_rows(rows)
        else:
            self.spawn()
            self.spawn()
        self.won = self.max_tile() >= self.target
        self.over = not self.can_move()

    # -- 基本操作 -------------------------------------------------------
    def _load_rows(self, rows):
        if len(rows) != self.size or any(len(row) != self.size for row in rows):
            raise ValueError("rows 的形状必须和棋盘大小一致")
        self.grid = [[int(value) for value in row] for row in rows]

    def empty_cells(self):
        return [
            (row, col)
            for row in range(self.size)
            for col in range(self.size)
            if self.grid[row][col] == 0
        ]

    def spawn(self):
        """在随机空位放一个 2（10% 概率是 4），返回坐标或 None。"""
        cells = self.empty_cells()
        if not cells:
            return None
        row, col = self.rng.choice(cells)
        self.grid[row][col] = 4 if self.rng.random() < SPAWN_FOUR_RATE else 2
        return (row, col)

    def max_tile(self):
        return max(max(row) for row in self.grid)

    def can_move(self):
        """还有空格，或者存在相邻的相同数字，就还能走。"""
        size = self.size
        for row in range(size):
            for col in range(size):
                value = self.grid[row][col]
                if value == 0:
                    return True
                if col + 1 < size and self.grid[row][col + 1] == value:
                    return True
                if row + 1 < size and self.grid[row + 1][col] == value:
                    return True
        return False

    def _line_coords(self, index, direction):
        """返回第 index 条线在移动方向上的坐标，顺序为「先撞墙」优先。"""
        size = self.size
        if direction == "left":
            return [(index, col) for col in range(size)]
        if direction == "right":
            return [(index, col) for col in range(size - 1, -1, -1)]
        if direction == "up":
            return [(row, index) for row in range(size)]
        return [(row, index) for row in range(size - 1, -1, -1)]

    # -- 移动 -----------------------------------------------------------
    def move(self, direction):
        if direction not in DIRECTIONS:
            raise ValueError(f"未知方向：{direction!r}")
        if self.over:
            return MoveResult(changed=False)

        before = [row[:] for row in self.grid]
        gained = 0
        for index in range(self.size):
            coords = self._line_coords(index, direction)
            values = [self.grid[row][col] for row, col in coords]
            merged, line_gain = merge_line(values)
            gained += line_gain
            for (row, col), value in zip(coords, merged):
                self.grid[row][col] = value

        if self.grid == before:
            return MoveResult(changed=False)

        self._undo_stack.append((before, self.score, self.moves))
        if len(self._undo_stack) > MAX_UNDO:
            self._undo_stack.pop(0)
        self.score += gained
        self.moves += 1
        spawned = self.auto_spawn and self.spawn() is not None
        if not self.won and self.max_tile() >= self.target:
            self.won = True
        self.over = not self.can_move()
        return MoveResult(changed=True, gained=gained, spawned=spawned)

    def undo(self):
        """撤回上一步，没有可撤回的步数时返回 False。"""
        if not self._undo_stack:
            return False
        grid, score, moves = self._undo_stack.pop()
        self.grid = [row[:] for row in grid]
        self.score = score
        self.moves = moves
        self.over = False
        self.won = self.max_tile() >= self.target
        return True

    # -- 存档 -----------------------------------------------------------
    def to_dict(self):
        return {
            "size": self.size,
            "target": self.target,
            "grid": [row[:] for row in self.grid],
            "score": self.score,
            "moves": self.moves,
        }

    @classmethod
    def from_dict(cls, data):
        game = cls(
            size=int(data["size"]),
            target=int(data.get("target", WIN_VALUE)),
            rows=data["grid"],
            auto_spawn=False,
        )
        game.score = int(data.get("score", 0))
        game.moves = int(data.get("moves", 0))
        return game
