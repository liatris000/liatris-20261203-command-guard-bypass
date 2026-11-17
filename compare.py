"""3 方式に同じ入力を流して、止めた・通した・誤って止めたを表にする。"""

from __future__ import annotations

import argparse

from cases import CASES
from guards import GUARDS


def mark(kind: str, blocked: bool) -> str:
    if kind == "block":
        return "止めた" if blocked else "**抜けた**"
    return "**誤って止めた**" if blocked else "通した"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--markdown", action="store_true", help="Markdown の表で出す")
    opts = parser.parse_args()

    names = list(GUARDS)
    totals = {n: {"missed": 0, "false": 0} for n in names}
    rows = []
    for kind, label, command in CASES:
        results = []
        for n in names:
            blocked = GUARDS[n](command) is not None
            if kind == "block" and not blocked:
                totals[n]["missed"] += 1
            if kind == "allow" and blocked:
                totals[n]["false"] += 1
            results.append(mark(kind, blocked))
        rows.append((kind, label, command, results))

    n_block = sum(1 for c in CASES if c[0] == "block")
    n_allow = len(CASES) - n_block
    if opts.markdown:
        print("| 種別 | 書き方 | " + " | ".join(names) + " |")
        print("|---|---|" + "---|" * len(names))
        for kind, label, _command, results in rows:
            print(f"| {kind} | {label} | " + " | ".join(results) + " |")
    else:
        for kind, label, command, results in rows:
            shown = command.replace("\n", "\\n")
            print(f"{kind:5} {label:24} " + "  ".join(f"{r.strip('*'):8}" for r in results) + f"  {shown}")
    print()
    print(f"止めたい {n_block} 件 / 止めてはいけない {n_allow} 件")
    for n in names:
        t = totals[n]
        print(f"{n:6} 抜けた {t['missed']:2} 件 / 誤って止めた {t['false']:2} 件")


if __name__ == "__main__":
    main()
