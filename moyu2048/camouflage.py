"""老板键：把屏幕换成一份看起来很正常的终端输出。

四份素材轮换，都是日常开发里最不显眼的命令输出。
"""

from __future__ import annotations

DIM = "\x1b[2m"
RESET = "\x1b[0m"

FRAMES = [
    (
        "git log",
        [
            "$ git log --oneline --stat -4",
            "a3f9c21 fix(order): skip empty refund batch",
            " order/service.py      | 18 +++++++++------",
            " order/refund_test.py  |  9 ++++---",
            " 2 files changed, 16 insertions(+), 11 deletions(-)",
            "",
            "7c2e104 chore(deps): bump requests to 2.32.3",
            " requirements.txt      |  2 +-",
            " 1 file changed, 1 insertion(+), 1 deletion(-)",
            "",
            "d81b0ef refactor: extract retry policy into helper",
            " core/retry.py         | 42 +++++++++++++++++++-------",
            " core/retry_test.py    | 27 ++++++++++++++++++",
            " 3 files changed, 58 insertions(+), 11 deletions(-)",
            "",
            "$ ",
        ],
    ),
    (
        "pytest",
        [
            "$ pytest -q --cov=app --cov-report=term-missing",
            "................................................................ [ 88%]",
            "........                                                         [100%]",
            "",
            "Name                     Stmts   Miss  Cover   Missing",
            "------------------------------------------------------",
            "app/order/service.py       142     11    92%   88-93, 120",
            "app/core/retry.py           67      3    96%   54",
            "app/api/schemas.py          51      0   100%",
            "------------------------------------------------------",
            "TOTAL                      260     14    95%",
            "",
            "47 passed, 2 warnings in 4.31s",
            "$ ",
        ],
    ),
    (
        "docker build",
        [
            "$ docker compose build api",
            "[+] Building 18.4s (12/12) FINISHED",
            " => [internal] load build definition from Dockerfile     0.0s",
            " => [1/6] FROM python:3.12-slim                          0.4s",
            " => [2/6] WORKDIR /app                                    0.1s",
            " => [3/6] COPY requirements.txt .                         0.0s",
            " => [4/6] RUN pip install -r requirements.txt            11.2s",
            " => [5/6] COPY . .                                        0.1s",
            " => [6/6] RUN python -m compileall -q app                 0.6s",
            " => exporting to image                                    0.3s",
            " => => naming to docker.io/library/payment-api:latest     0.0s",
            "",
            " Use 'docker scan' to run Snyk tests against images",
            "$ ",
        ],
    ),
    (
        "git status",
        [
            "$ git status",
            "On branch feature/refund-batch",
            "Your branch is up to date with 'origin/feature/refund-batch'.",
            "",
            "Changes not staged for commit:",
            '  (use "git add <file>..." to update what will be committed)',
            '  (use "git restore <file>..." to discard changes in working directory)',
            "        modified:   order/service.py",
            "        modified:   tests/test_refund.py",
            "",
            'no changes added to commit (use "git add" and/or "git commit -a")',
            "$ git diff --stat",
            " order/service.py     | 18 ++++++++++++------",
            " tests/test_refund.py |  9 ++++++---",
            " 2 files changed, 20 insertions(+), 7 deletions(-)",
            "$ ",
        ],
    ),
]

FRAME_COUNT = len(FRAMES)


def render_camouflage(index=0):
    """返回一整屏伪装内容（不带结尾换行）。"""
    _, lines = FRAMES[index % FRAME_COUNT]
    body = []
    for line in lines:
        # 缩进的 stat / 提示行压暗，看起来更像普通终端输出。
        if line.startswith(" "):
            body.append(f"{DIM}{line}{RESET}")
        else:
            body.append(line)
    body.append("")
    body.append(f"{DIM}  [esc]{RESET}")
    return "\n".join(body)
