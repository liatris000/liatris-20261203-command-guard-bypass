"""同じ操作を書き方だけ変えて並べたテストケース。

kind:
  block   止めたい操作
  allow   止めてはいけない普通のコマンド
"""

CASES = [
    # --- git commit ---
    ("block", "基本形", 'git commit -m "wip"'),
    ("block", "空白を 2 つ", 'git  commit -m "wip"'),
    ("block", "グローバルオプション -C", 'git -C /repo commit -m "wip"'),
    ("block", "グローバルオプション -c", 'git -c user.name=x commit -m "wip"'),
    ("block", "グローバルオプション --no-pager", 'git --no-pager commit -m "wip"'),
    ("block", "絶対パス", '/usr/bin/git commit -m "wip"'),
    ("block", "環境変数の前置き", 'GIT_AUTHOR_NAME=x git commit -m "wip"'),
    ("block", "ラッパー command", 'command git commit -m "wip"'),
    ("block", "&& でつなぐ", 'cd /repo && git commit -m "wip"'),
    ("block", "; でつなぐ", 'git status; git commit -m "wip"'),
    ("block", "改行でつなぐ", 'git status\ngit commit -m "wip"'),
    ("block", "bash -c", 'bash -c "git commit -m wip"'),
    ("block", "sh -c の中で &&", "sh -c 'cd /repo && git commit -m wip'"),
    ("block", "コマンド置換", 'echo "$(git commit -m wip)"'),
    ("block", "eval", 'eval "git commit -m wip"'),
    ("block", "引用符で単語を割る", "git c''ommit -m wip"),
    ("block", "変数に入れて展開", 'g=git; $g commit -m "wip"'),
    ("block", "エイリアス", 'git -c alias.ci=commit ci -m "wip"'),
    ("block", "標準入力からシェルへ", "echo 'git commit -m wip' | bash"),
    ("block", "スクリプトファイル経由", "bash ./commit.sh"),
    # --- git push の強制 ---
    ("block", "push 基本形", "git push --force origin main"),
    ("block", "push 短いフラグ", "git push -f origin main"),
    ("block", "push フラグを後ろに", "git push origin main --force"),
    ("block", "push +refspec", "git push origin +main"),
    ("block", "push 短いフラグの結合", "git push -uf origin main"),
    ("block", "push グローバルオプション -C", "git -C /repo push -f origin main"),
    # --- rm の再帰削除 ---
    ("block", "rm 基本形", "rm -rf /tmp/work"),
    ("block", "rm フラグの順序", "rm -fr /tmp/work"),
    ("block", "rm フラグを分ける", "rm -f -r /tmp/work"),
    ("block", "rm 長いオプション", "rm --recursive --force /tmp/work"),
    ("block", "rm 絶対パス", "/bin/rm -rf /tmp/work"),
    ("block", "rm 別コマンド find", "find /tmp/work -delete"),
    ("block", "rm 別言語 python", "python3 -c \"import shutil; shutil.rmtree('/tmp/work')\""),
    # --- 止めてはいけない ---
    ("allow", "git status", "git status"),
    ("allow", "git log -C", "git log -C --oneline"),
    ("allow", "git log の引数に文字列", 'git log --grep="git commit"'),
    ("allow", "echo の引数に文字列", 'echo "git commit を止める hook"'),
    ("allow", "git commit-graph", "git commit-graph write"),
    ("allow", "通常の push", "git push origin main"),
    ("allow", "push の後ろに rm -f", "git push origin main && rm -f /tmp/out.log"),
    ("allow", "rm -f", "rm -f /tmp/out.log"),
    ("allow", "grep -r の引数に文字列", 'grep -r "rm -rf" docs/'),
]
