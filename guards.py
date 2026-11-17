"""危険なコマンドを止めるガードを 3 方式で実装する。

どの関数も、止めるなら理由の文字列を、通すなら None を返す。
止める対象は次の 3 つの操作:

- git commit
- git push の強制 (--force / -f / +refspec)
- rm の再帰削除 (-r / -R / --recursive)
"""

from __future__ import annotations

import os
import re
import shlex

# ---------------------------------------------------------------------------
# (1) 前方一致: コマンド全体の先頭が、登録した文字列で始まるかだけを見る
# ---------------------------------------------------------------------------

PREFIX_RULES = [
    "git commit",
    "git push --force",
    "git push -f",
    "rm -rf",
    "rm -fr",
    "rm -r",
    "rm -R",
]


def prefix_guard(command: str) -> str | None:
    cmd = command.strip()
    for rule in PREFIX_RULES:
        # "git commit-graph" を "git commit" と見なさないよう、直後が空白か終端のときだけ一致とする
        if cmd == rule or cmd.startswith(rule + " "):
            return f"prefix: {rule}"
    return None


# ---------------------------------------------------------------------------
# (2) 正規表現: 文字列全体のどこかに、危険な形が現れるかを探す
# ---------------------------------------------------------------------------

REGEX_RULES = [
    ("git commit", re.compile(r"\bgit\s+commit\b")),
    ("git push --force", re.compile(r"\bgit\s+push\b.*\s(--force|-f)\b")),
    ("rm -r", re.compile(r"\brm\s+(-\S+\s+)*-[a-zA-Z]*[rR]")),
    ("rm --recursive", re.compile(r"\brm\b.*\s--recursive\b")),
]


def regex_guard(command: str) -> str | None:
    for name, pattern in REGEX_RULES:
        if pattern.search(command):
            return f"regex: {name}"
    return None


# ---------------------------------------------------------------------------
# (3) 解析: 字句解析 → 複合コマンドを分ける → ラッパーを剥がす → オプションを飛ばして判定
# ---------------------------------------------------------------------------

SEPARATORS = {";", "&", "&&", "|", "||", "|&", "(", ")", "\n", ";;"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
# 後ろに続くコマンドをそのまま実行するだけのコマンド。値を取るオプションの名前を添える
WRAPPERS = {
    "env": {"-u", "--unset", "-C", "--chdir"},
    "sudo": {"-u", "-g", "-C", "-D", "-h", "-p", "-U", "-r", "-t"},
    "command": set(),
    "exec": {"-a"},
    "nohup": set(),
    "nice": {"-n"},
    "time": set(),
    "xargs": {"-I", "-n", "-P", "-L", "-d", "-a", "-E", "-s"},
}
# git のサブコマンドより前に置けるオプションのうち、値を別の引数で取るもの
GIT_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env"}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SUBSTITUTION = re.compile(r"\$\(([^()]*)\)|`([^`]*)`")
MAX_DEPTH = 5


def tokenize(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()\n")
    lexer.whitespace = " \t\r"  # 改行はコマンドの区切りとして残す
    lexer.whitespace_split = True
    lexer.commenters = ""  # 「#」をコメント扱いすると、後ろのコマンドを見落とす向きに倒れるので扱わない
    return list(lexer)


def split_segments(tokens: list[str]) -> list[list[str]]:
    segments, current = [], []
    for tok in tokens:
        if tok in SEPARATORS:
            if current:
                segments.append(current)
            current = []
        else:
            current.append(tok)
    if current:
        segments.append(current)
    return segments


def unwrap(argv: list[str]) -> list[str]:
    """環境変数の前置きとラッパーを剥がし、実際に動くコマンドを先頭に持ってくる。"""
    i = 0
    while i < len(argv):
        word = argv[i]
        if ASSIGNMENT.match(word):
            i += 1
            continue
        name = os.path.basename(word)
        if name == "timeout":
            i += 1
            while i < len(argv) and argv[i].startswith("-"):
                i += 1
            i += 1  # 秒数
            continue
        if name in WRAPPERS:
            with_value = WRAPPERS[name]
            i += 1
            while i < len(argv) and argv[i].startswith("-"):
                i += 2 if argv[i] in with_value else 1
            continue
        break
    rest = argv[i:]
    if rest:
        rest = [os.path.basename(rest[0])] + rest[1:]
    return rest


def check_git(args: list[str]) -> str | None:
    i = 0
    while i < len(args) and args[i].startswith("-"):
        i += 2 if args[i] in GIT_OPTS_WITH_VALUE else 1
    if i >= len(args):
        return None
    sub, rest = args[i], args[i + 1:]
    if sub == "commit":
        return "parse: git commit"
    if sub == "push":
        for arg in rest:
            if arg == "--":
                break
            if arg == "--force" or (re.fullmatch(r"-[a-zA-Z]+", arg) and "f" in arg):
                return "parse: git push --force"
        positional = [a for a in rest if not a.startswith("-")]
        if any(p.startswith("+") for p in positional[1:]):
            return "parse: git push +refspec"
    return None


def check_rm(args: list[str]) -> str | None:
    for arg in args:
        if arg == "--":
            break
        if arg == "--recursive" or (re.fullmatch(r"-[a-zA-Z]+", arg) and ("r" in arg or "R" in arg)):
            return "parse: rm -r"
    return None


def check_argv(argv: list[str], depth: int) -> str | None:
    argv = unwrap(argv)
    if not argv:
        return None
    name, args = argv[0], argv[1:]
    if name in SHELLS and "-c" in args:
        idx = args.index("-c")
        if idx + 1 < len(args):
            return check(args[idx + 1], depth + 1)
    if name == "eval":
        return check(" ".join(args), depth + 1)
    if name == "git":
        return check_git(args)
    if name == "rm":
        return check_rm(args)
    return None


def check(command: str, depth: int = 0) -> str | None:
    if depth > MAX_DEPTH:
        return "parse: 入れ子が深すぎる"
    # 引用符の中のコマンド置換も実行されるので、中身を取り出して先に調べる
    for m in SUBSTITUTION.finditer(command):
        reason = check(m.group(1) if m.group(1) is not None else m.group(2), depth + 1)
        if reason:
            return reason
    try:
        tokens = tokenize(command)
    except ValueError as e:
        # 引用符が閉じていないなど、解析できない入力は止める側に倒す
        return f"parse: 解析できない ({e})"
    for segment in split_segments(tokens):
        reason = check_argv(segment, depth)
        if reason:
            return reason
    return None


def parse_guard(command: str) -> str | None:
    return check(command)


GUARDS = {
    "prefix": prefix_guard,
    "regex": regex_guard,
    "parse": parse_guard,
}
