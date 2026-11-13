"""终端渲染：把局面变成带 ANSI 转义的文本块，不碰输入。"""

from __future__ import annotations

import re
import unicodedata

RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

CELL = 6

# 256 色里挑的一套接近原版 2048 的配色。
TILE_COLORS = {
    2: 252,
    4: 250,
    8: 222,
    16: 214,
    32: 208,
    64: 202,
    128: 196,
    256: 160,
    512: 127,
    1024: 33,
    2048: 21,
    4096: 93,
    8192: 200,
}

# 默认只用 ASCII：中文控制台会把「─」「│」「·」这类字符按两格宽渲染，
# 表格就会错位，而 ASCII 在哪个终端里都只占一格。
ASCII_BORDERS = {
    "top": ("+", "+", "+"),
    "mid": ("+", "+", "+"),
    "bottom": ("+", "+", "+"),
    "h": "-",
    "v": "|",
    "empty": ".",
}

UNICODE_BORDERS = {
    "top": ("┌", "┬", "┐"),
    "mid": ("├", "┼", "┤"),
    "bottom": ("└", "┴", "┘"),
    "h": "─",
    "v": "│",
    "empty": "·",
}


def strip_ansi(text):
    """去掉 ANSI 转义，测试和重定向输出时用。"""
    return ANSI_RE.sub("", text)


def clip_line(text, max_cells):
    """按显示宽度截断一行，保留 ANSI 转义。

    比终端宽的行走到终端里会自动换行，把整块画面顶乱；先截断就不会有这个问题。
    """
    if max_cells <= 0:
        return ""
    pieces = []
    width = 0
    index = 0
    while index < len(text):
        match = ANSI_RE.match(text, index)
        if match is not None:
            pieces.append(match.group(0))
            index = match.end()
            continue
        char = text[index]
        cells = 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
        if width + cells > max_cells:
            break
        pieces.append(char)
        width += cells
        index += 1
    return "".join(pieces) + RESET


def _paint(value, text, theme):
    if value == 0:
        return f"{DIM}{text}{RESET}"
    if theme == "color":
        color = TILE_COLORS.get(value, 231)
        weight = BOLD if value >= 128 else ""
        return f"{weight}\x1b[38;5;{color}m{text}{RESET}"
    weight = BOLD if value >= 1024 else ""
    return f"{weight}{text}{RESET}"


def board_lines(game, theme="mono", unicode_borders=False):
    chars = UNICODE_BORDERS if unicode_borders else ASCII_BORDERS
    horizontal, vertical = chars["h"], chars["v"]
    size = game.size

    def border(left, joint, right):
        return left + joint.join(horizontal * CELL for _ in range(size)) + right

    lines = [border(*chars["top"])]
    for row in range(size):
        if row:
            lines.append(border(*chars["mid"]))
        cells = []
        for col in range(size):
            value = game.grid[row][col]
            if value == 0:
                text = f"{chars['empty']:>{CELL}}"
            else:
                text = f"{value:>{CELL}}"
                if len(text) > CELL:  # 理论上只会在超大棋盘上出现
                    text = f"{value:>{CELL - 1}} "
            cells.append(_paint(value, text, theme))
        lines.append(vertical + vertical.join(cells) + vertical)
    lines.append(border(*chars["bottom"]))
    return lines


def render_game(game, best, theme="mono", unicode_borders=False, message=None):
    """整屏画面：标题、棋盘、提示，最后不带换行。"""
    lines = [
        f"{BOLD}moyu-2048{RESET}   "
        f"{DIM}分数{RESET} {game.score}   "
        f"{DIM}最高{RESET} {best}",
        "",
    ]
    lines.extend(board_lines(game, theme, unicode_borders))
    lines.append("")
    if message:
        lines.append(message)
    move_keys = "←↑→↓ / WASD" if unicode_borders else "方向键 / WASD"
    lines.append(
        f"{DIM}{move_keys} 移动   u 撤销   n 新局   ESC 伪装   q 退出{RESET}"
    )
    return "\n".join(lines)


def render_summary(score, best, session_seconds, total_seconds, rate=50.0):
    """退出时的摸鱼小结，纯文本。"""
    return "\n".join(
        [
            f" 本次 {format_duration(session_seconds)} · 得分 {score} · 最高 {best}",
            f" 累计 {format_duration(total_seconds)} · 折合 {format_money(total_seconds, rate)}",
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


def format_money(seconds, rate=50.0):
    return f"¥{seconds / 3600 * rate:,.0f}"
