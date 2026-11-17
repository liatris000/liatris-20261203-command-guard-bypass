import json
import pathlib
import subprocess
import sys

import pytest
from cases import CASES
from guards import parse_guard, prefix_guard, regex_guard

ROOT = pathlib.Path(__file__).resolve().parent.parent

# 解析方式でも止められないと分かっている書き方。記事の「結果」の節に対応する
PARSE_KNOWN_MISSES = {
    "変数に入れて展開",
    "エイリアス",
    "標準入力からシェルへ",
    "スクリプトファイル経由",
    "rm 別コマンド find",
    "rm 別言語 python",
}


@pytest.mark.parametrize("kind,label,command", CASES, ids=[c[1] for c in CASES])
def test_parse_guard(kind, label, command):
    blocked = parse_guard(command) is not None
    if kind == "allow" or label in PARSE_KNOWN_MISSES:
        assert not blocked
    else:
        assert blocked


def test_totals():
    def count(guard):
        missed = sum(1 for k, _, c in CASES if k == "block" and guard(c) is None)
        false = sum(1 for k, _, c in CASES if k == "allow" and guard(c) is not None)
        return missed, false

    assert count(prefix_guard) == (28, 0)
    assert count(regex_guard) == (12, 5)
    assert count(parse_guard) == (6, 0)


def test_unbalanced_quote_is_blocked():
    assert parse_guard('git status "') is not None


def run_hook(payload):
    return subprocess.run(
        [sys.executable, str(ROOT / "hook.py")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )


def test_hook_blocks_with_exit_2():
    r = run_hook({"tool_name": "Bash", "tool_input": {"command": "git -C /repo commit -m x"}})
    assert r.returncode == 2
    assert "parse: git commit" in r.stderr


def test_hook_allows():
    r = run_hook({"tool_name": "Bash", "tool_input": {"command": "git status"}})
    assert r.returncode == 0


def test_hook_ignores_other_tools():
    r = run_hook({"tool_name": "Read", "tool_input": {"file_path": "/etc/hosts"}})
    assert r.returncode == 0
