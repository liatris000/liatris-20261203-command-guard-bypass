"""Claude Code の PreToolUse hook。Bash ツールのコマンドを解析方式で判定する。

標準入力に hook の JSON を受け取り、止めるときは理由を標準エラーに出して終了コード 2 で終わる。
"""

from __future__ import annotations

import json
import sys

from guards import parse_guard


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("hook: 入力の JSON を読めないため止めました", file=sys.stderr)
        return 2
    if payload.get("tool_name") != "Bash":
        return 0
    command = payload.get("tool_input", {}).get("command", "")
    reason = parse_guard(command)
    if reason:
        print(f"このコマンドは止めています ({reason})。必要なら人に頼んでください", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
