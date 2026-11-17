# 危険なコマンドを文字列で止めるガードは、どこまで抜けるか

`git commit` / `git push --force` / `rm -r` を止めるガードを 3 方式(前方一致・正規表現・字句解析)で書き、同じ操作を書き方だけ変えた 33 件と、止めてはいけない普通のコマンド 9 件を流して、抜けた件数と誤って止めた件数を数えます。

| ファイル | 中身 |
|---|---|
| `guards.py` | 3 方式のガード |
| `cases.py` | テストケース(書き方の一覧) |
| `compare.py` | 3 方式に同じ入力を流して表を出す |
| `hook.py` | Claude Code の PreToolUse hook(解析方式) |
| `.claude/settings.json` | hook の設定例 |

## 前提

- Python 3.11 以上(3.11.18 で確認)。ガードと hook は標準ライブラリ(`shlex` / `re` / `json`)だけで動く
- テストに pytest 8.3.3(`requirements.txt`)

## 動かし方

```bash
git clone https://github.com/liatris000/liatris-20261203-command-guard-bypass.git
cd liatris-20261203-command-guard-bypass
python3 compare.py            # 表を出す(--markdown で Markdown の表)

# hook 単体の動作確認
echo '{"tool_name":"Bash","tool_input":{"command":"git -C /repo commit -m x"}}' | python3 hook.py; echo "exit=$?"

# テスト
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q
```

Claude Code で使うときは、`hook.py` と `guards.py` をプロジェクトの直下に置き、`.claude/settings.json` の `hooks` を自分の設定に足します。

## 期待される出力

`python3 compare.py` の末尾:

```
止めたい 33 件 / 止めてはいけない 9 件
prefix 抜けた 28 件 / 誤って止めた  0 件
regex  抜けた 12 件 / 誤って止めた  5 件
parse  抜けた  6 件 / 誤って止めた  0 件
```

hook 単体:

```
このコマンドは止めています (parse: git commit)。必要なら人に頼んでください
exit=2
```

pytest:

```
47 passed
```

## 確かめていない範囲

- `hook.py` は、hook の入力と同じ形の JSON を標準入力に流して確かめただけで、Claude Code のセッションに組み込んで動かしてはいない
- 前方一致の方式は「先頭の文字列が一致するか」だけを見る自作の実装で、Claude Code の権限ルール(`Bash(git commit:*)` など)の実際の照合とは同じではない
- 解析方式は bash の文法の一部(区切り記号・引用符・`$(...)` とバッククォート・`bash -c`・`eval`・一部のラッパー)だけを扱う。ヒアドキュメント、関数定義、`$(...)` の入れ子、プロセス置換は扱っていない

## 記事

https://zenn.dev/liatris/articles/20261203-command-guard-bypass

## License

MIT
