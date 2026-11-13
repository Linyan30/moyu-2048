"""极简的跨平台按键读取：方向键、ESC、普通字符。"""

from __future__ import annotations

import os
import sys

# Windows 下方向键的第二字节；xterm 下 CSI 的最后一个字母。
_ARROWS = {
    "H": "up",
    "P": "down",
    "K": "left",
    "M": "right",
    "A": "up",
    "B": "down",
    "C": "right",
    "D": "left",
}


class KeyReader:
    """上下文管理器：进入时关掉行缓冲和回显，退出时恢复。"""

    def __init__(self):
        self._fd = None
        self._saved = None

    def __enter__(self):
        if os.name != "nt":
            try:
                import termios
                import tty

                self._fd = sys.stdin.fileno()
                self._saved = termios.tcgetattr(self._fd)
                tty.setcbreak(self._fd)
            except Exception:  # 不是真终端时退化成读整行
                self._fd = None
                self._saved = None
        return self

    def __exit__(self, *exc_info):
        if self._fd is not None and self._saved is not None:
            import termios

            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._saved)
        self._fd = None

    def read(self):
        if os.name == "nt":
            return self._read_windows()
        return self._read_posix()

    # -- Windows --------------------------------------------------------
    @staticmethod
    def _read_windows():
        import msvcrt

        char = msvcrt.getwch()
        if char in ("\x00", "\xe0"):
            return _ARROWS.get(msvcrt.getwch().upper(), "")
        return translate(char)

    # -- POSIX ----------------------------------------------------------
    def _read_posix(self):
        while True:
            data = os.read(self._fd or 0, 1)
            if not data:
                return "quit"
            char = data.decode("utf-8", "ignore")
            if char == "\x1b":
                return self._read_escape()
            key = translate(char)
            if key:
                return key

    def _read_escape(self):
        """ESC 后面如果跟着 ``[A`` 之类就是方向键，否则当成单独的 ESC。"""
        import select

        fd = self._fd or 0
        sequence = b""
        while len(sequence) < 8 and select.select([fd], [], [], 0.05)[0]:
            sequence += os.read(fd, 1)
        if sequence[:1] in (b"[", b"O"):
            return _ARROWS.get(sequence[-1:].decode("latin-1"), "") or "esc"
        return "esc"


def translate(char):
    if char == "\x1b":
        return "esc"
    if char in ("\r", "\n"):
        return "enter"
    if char == "\x03":
        return "quit"
    if char == " ":
        return "space"
    if len(char) == 1 and char.isprintable():
        return char.lower()
    return ""
