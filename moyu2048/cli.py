"""命令行入口：参数解析和交互循环。"""

from __future__ import annotations

import argparse
import random
import shutil
import sys
import time

from . import __version__
from .camouflage import FRAME_COUNT, render_camouflage
from .game import DIRECTIONS, Game
from .input import KeyReader
from .render import clip_line, render_game, render_summary, strip_ansi
from .stats import Stats, stats_path

# Windows 控制台默认不解释 ANSI，需要打开「虚拟终端处理」。
_ENABLE_VT = 0x0004

# vim 用户的习惯键位，和方向键等价。
VIM_KEYS = {"h": "left", "j": "down", "k": "up", "l": "right"}


def build_parser():
    parser = argparse.ArgumentParser(
        prog="moyu",
        description="摸鱼 2048：一个会伪装成 git log 的终端小游戏。",
    )
    parser.add_argument(
        "--size", type=int, default=4, choices=range(3, 9), metavar="N",
        help="棋盘边长，3-8，默认 4",
    )
    parser.add_argument(
        "--color", action="store_true", help="彩色方块（默认灰阶，更低调）",
    )
    parser.add_argument(
        "--unicode", action="store_true",
        help="用制表符画边框（更好看，但部分中文终端会把制表符渲染成两格宽）",
    )
    parser.add_argument(
        "--boss", action="store_true", help="一启动就进入伪装画面",
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="固定随机种子，方便复现",
    )
    parser.add_argument(
        "--demo", type=int, metavar="N", default=None,
        help="自动随机走 N 步后打印棋盘并退出（给 CI 用）",
    )
    parser.add_argument(
        "--stats", action="store_true", help="打印摸鱼统计后退出",
    )
    parser.add_argument(
        "--reset", action="store_true", help="清空摸鱼统计",
    )
    parser.add_argument(
        "--rate", type=float, default=50.0,
        help="时薪，用来把摸鱼时长折算成收益，默认 50",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}",
    )
    return parser


class Screen:
    """真终端里用备用屏幕，退出时回到原来的滚屏内容。"""

    def __init__(self, interactive):
        self.interactive = interactive

    def __enter__(self):
        if self.interactive:
            self._write("\x1b[?1049h\x1b[?25l\x1b[2J")
        return self

    def draw(self, text):
        if not self.interactive:
            print(text)
            return
        width = max(20, shutil.get_terminal_size((80, 24)).columns)
        # 每行结尾擦到行尾，否则上一屏更长的行会在右边留下残字。
        body = "\n".join(
            clip_line(line, width) + "\x1b[K" for line in text.split("\n")
        )
        self._write("\x1b[H" + body + "\x1b[J")

    def __exit__(self, *exc_info):
        if self.interactive:
            self._write("\x1b[?25h\x1b[?1049l")

    @staticmethod
    def _write(text):
        sys.stdout.write(text)
        sys.stdout.flush()


def run_game(args):
    stats = Stats.load()
    game = Game(args.size, seed=args.seed)
    theme = "color" if args.color else "mono"
    borders = args.unicode
    best = stats.best_for(args.size)
    interactive = sys.stdout.isatty() and sys.stdin.isatty()
    started = time.monotonic()
    elapsed = 0.0

    show_camouflage = args.boss
    frame = random.randrange(FRAME_COUNT)
    message = None
    won_announced = game.won

    try:
        with Screen(interactive) as screen, KeyReader() as keys:
            while True:
                if show_camouflage:
                    screen.draw(render_camouflage(frame))
                else:
                    screen.draw(render_game(game, best, theme, borders, message))

                key = keys.read()
                key = VIM_KEYS.get(key, key)
                if key in ("q", "quit"):
                    break
                if key == "esc":
                    show_camouflage = not show_camouflage
                    if show_camouflage:
                        frame = random.randrange(FRAME_COUNT)
                    message = None
                    continue
                if show_camouflage:
                    continue
                if key in DIRECTIONS:
                    result = game.move(key)
                    if not result.changed:
                        continue
                    message = None
                    if game.score > best:
                        best = game.score
                    if game.won and not won_announced:
                        won_announced = True
                        message = f"已经 {game.target} 了！继续冲 {game.target * 2}，或按 n 开新局"
                    elif game.over:
                        message = "无处可走了 —— u 撤销 / n 新局 / q 退出"
                    continue
                if key == "u":
                    if game.undo():
                        won_announced = game.won
                        message = None
                    else:
                        message = "没有可以撤销的步数"
                elif key == "n":
                    stats.record_game(args.size, game.score, game.moves)
                    game = Game(args.size)
                    best = max(best, stats.best_for(args.size))
                    won_announced = False
                    message = None
    finally:
        elapsed = time.monotonic() - started
        stats.record_game(args.size, game.score, game.moves)
        stats.add_seconds(elapsed)
        try:
            stats.save()
        except OSError:
            pass

    print()
    print(render_summary(game.score, best, elapsed, stats.seconds, args.rate))
    return 0


def run_demo(args):
    game = Game(args.size, seed=args.seed)
    rng = random.Random(args.seed)
    for _ in range(max(0, args.demo)):
        if game.over:
            break
        for _ in range(64):
            if game.move(rng.choice(DIRECTIONS)).changed:
                break
        else:
            break

    text = render_game(
        game, game.score, "color" if args.color else "mono", args.unicode
    )
    if not sys.stdout.isatty():
        text = strip_ansi(text)
    print(text)
    return 0


def _enable_ansi():
    if sys.platform != "win32":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | _ENABLE_VT)
    except Exception:  # 拿不到句柄就交给终端自己处理
        pass


def _configure_stdout():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def main(argv=None):
    args = build_parser().parse_args(argv)
    _configure_stdout()
    _enable_ansi()

    if args.reset:
        try:
            stats_path().unlink()
        except OSError:
            pass
        print("摸鱼记录已清空。")
        return 0
    if args.stats:
        print(Stats.load().render(rate=args.rate))
        return 0
    if args.demo is not None:
        return run_demo(args)

    try:
        return run_game(args)
    except KeyboardInterrupt:
        return 130
