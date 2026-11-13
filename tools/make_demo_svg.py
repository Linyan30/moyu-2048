#!/usr/bin/env python3
"""把真实的渲染结果画成 README 用的演示图（SVG）。

用法：

    python tools/make_demo_svg.py

图片内容全部来自 ``moyu2048`` 的渲染函数，所以改了配色或文案之后重跑一遍，
README 里的图就和程序一致了。
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from moyu2048.camouflage import render_camouflage  # noqa: E402
from moyu2048.game import Game  # noqa: E402
from moyu2048.render import render_game  # noqa: E402

WIDTH = 1232
HEIGHT = 520
PANE_W = 580
PANE_H = 440
PANE_Y = 24
LEFT_X = 24
RIGHT_X = 628

FONT = (
    "ui-monospace, SFMono-Regular, 'Cascadia Code', Consolas, "
    "Menlo, 'DejaVu Sans Mono', monospace"
)
FONT_SIZE = 14.0
CHAR_W = FONT_SIZE * 0.6
LINE_H = 20.0
PAD_X = 18

PAGE = "#0d1117"
PANE_BG = "#161b22"
BAR_BG = "#21262d"
BORDER = "#30363d"
TEXT = "#c9d1d9"
MUTED = "#8b949e"

SGR = re.compile(r"\x1b\[([0-9;]*)m")

BASE_COLORS = [
    "#000000", "#800000", "#008000", "#808000",
    "#000080", "#800080", "#008080", "#c0c0c0",
    "#808080", "#ff0000", "#00ff00", "#ffff00",
    "#0000ff", "#ff00ff", "#00ffff", "#ffffff",
]


def color_256(index):
    index = max(0, min(255, index))
    if index < 16:
        return BASE_COLORS[index]
    if index < 232:
        index -= 16
        levels = [0, 95, 135, 175, 215, 255]
        red = levels[index // 36]
        green = levels[(index % 36) // 6]
        blue = levels[index % 6]
        return f"#{red:02x}{green:02x}{blue:02x}"
    level = 8 + (index - 232) * 10
    return f"#{level:02x}{level:02x}{level:02x}"


def styled_runs(line):
    """把一行带 ANSI 的文本拆成 (文字, 样式) 片段。"""
    runs = []
    style = {"color": None, "bold": False, "dim": False}
    position = 0
    for match in SGR.finditer(line):
        if match.start() > position:
            runs.append((line[position:match.start()], dict(style)))
        params = [int(part) for part in match.group(1).split(";") if part] or [0]
        index = 0
        while index < len(params):
            code = params[index]
            if code == 0:
                style = {"color": None, "bold": False, "dim": False}
            elif code == 1:
                style["bold"] = True
            elif code == 2:
                style["dim"] = True
            elif code == 22:
                style["bold"] = False
                style["dim"] = False
            elif code == 39:
                style["color"] = None
            elif code == 38 and params[index + 1:index + 2] == [5]:
                style["color"] = color_256(params[index + 2])
                index += 2
            index += 1
        position = match.end()
    if position < len(line):
        runs.append((line[position:], dict(style)))
    return runs


def tspan(text, style):
    fill = MUTED if style["dim"] else (style["color"] or TEXT)
    attrs = [f'fill="{fill}"']
    if style["bold"]:
        attrs.append('font-weight="600"')
    return f"<tspan {' '.join(attrs)}>{escape(text)}</tspan>"


def max_cells(lines):
    widest = 0
    for line in lines:
        plain = re.sub(r"\x1b\[[0-9;]*m", "", line)
        width = 0
        for char in plain:
            width += 2 if unicodedata.east_asian_width(char) in "WF" else 1
        widest = max(widest, width)
    return widest


def text_block(lines, pane_x, pane_y, pane_h):
    block = len(lines) * LINE_H
    area = pane_h - 32
    first = pane_y + 32 + max(14.0, (area - block) / 2 + FONT_SIZE)
    out = []
    y = first
    for line in lines:
        runs = styled_runs(line)
        if runs:
            spans = "".join(tspan(text, style) for text, style in runs)
            out.append(
                f'<text x="{pane_x + PAD_X}" y="{y:.1f}" xml:space="preserve">{spans}</text>'
            )
        y += LINE_H
    return "\n      ".join(out)


def window(x, y, w, h, title, body):
    return f"""<g>
      <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{PANE_BG}" stroke="{BORDER}"/>
      <rect x="{x}" y="{y}" width="{w}" height="32" rx="12" fill="{BAR_BG}"/>
      <rect x="{x}" y="{y + 20}" width="{w}" height="12" fill="{BAR_BG}"/>
      <circle cx="{x + 18}" cy="{y + 16}" r="4.5" fill="#ff5f56"/>
      <circle cx="{x + 34}" cy="{y + 16}" r="4.5" fill="#ffbd2e"/>
      <circle cx="{x + 50}" cy="{y + 16}" r="4.5" fill="#27c93f"/>
      <text x="{x + 70}" y="{y + 21}" font-size="12" fill="{MUTED}">{escape(title)}</text>
      <g font-family="{FONT}" font-size="{FONT_SIZE}">
      {body}
      </g>
    </g>"""


def build():
    game = Game(
        rows=[
            [2, 128, 0, 4],
            [0, 16, 8, 512],
            [4, 64, 32, 2],
            [1024, 8, 0, 2],
        ],
        auto_spawn=False,
    )
    game.score = 1250

    left = render_game(game, 8932, theme="mono", unicode_borders=False).splitlines()
    right = render_camouflage(0).splitlines()

    for name, lines in (("left", left), ("right", right)):
        cells = max_cells(lines)
        if cells * CHAR_W + PAD_X * 2 > PANE_W:
            print(f"warning: {name} 内容 {cells} 列，可能超出窗口", file=sys.stderr)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="moyu-2048：左边是灰阶棋盘，按 ESC 后变成 git log">
  <title>moyu-2048 演示</title>
  <rect width="{WIDTH}" height="{HEIGHT}" rx="16" fill="{PAGE}"/>
  {window(LEFT_X, PANE_Y, PANE_W, PANE_H, "moyu-2048 — 摸鱼模式", text_block(left, LEFT_X, PANE_Y, PANE_H))}
  {window(RIGHT_X, PANE_Y, PANE_W, PANE_H, "PowerShell — git log", text_block(right, RIGHT_X, PANE_Y, PANE_H))}
  <text x="{LEFT_X + PANE_W / 2}" y="{PANE_Y + PANE_H + 34}" font-family="{FONT}" font-size="13" fill="{MUTED}" text-anchor="middle">← 摸鱼模式，默认灰阶，远看只是数字 →</text>
  <text x="{RIGHT_X + PANE_W / 2}" y="{PANE_Y + PANE_H + 34}" font-family="{FONT}" font-size="13" fill="{MUTED}" text-anchor="middle">← 按 ESC：一键伪装成工作画面 →</text>
</svg>
"""
    return svg


def main():
    output = ROOT / "assets" / "demo.svg"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build(), encoding="utf-8")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
