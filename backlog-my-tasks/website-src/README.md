# 紹介サイト（GitHub Pages）ソース

`docs/build_deck.py`（紹介PPT）と同じ方針で、Pythonでコンポーネントを組み立てて静的HTMLを出力するジェネレーター。

## ビルド方法

```
python3 docs/website-src/build_site.py
```

`docs/website-src/dist/` に20ページの静的サイト（HTML/CSS/JS/画像）が生成される。`dist/` は生成物だが
mainブランチでもgit管理する（レビュー時に生成結果をそのまま差分で確認できるようにするため）。
**内容を変更したら必ずビルドし直してから `dist/` ごとコミットすること。**

## デプロイ方法

生成した `dist/` の中身を `gh-pages` ブランチのルート直下にコピーしてpushする。

```
python3 docs/website-src/build_site.py
git checkout gh-pages   # 無ければ --orphan で新規作成
rm -rf ./* .nojekyll    # 既存ファイルを一旦クリア（.git は残る）
cp -r docs/website-src/dist/. .
git add -A && git commit -m "サイト更新" && git push origin gh-pages
git checkout -          # 元のブランチに戻る
```

GitHub リポジトリの Settings → Pages → Source を「Deploy from a branch」→ `gh-pages` / `/(root)` に設定すると公開される（初回のみ手動設定が必要）。

## 内容を更新するとき

- 新機能を追加したら `docs/build_deck.py`（紹介PPT）と同様、このサイトにも反映することを検討する。
- 文言・画像は `docs/build_deck.py` のスライド内容および `docs/store/screenshots/` のスクリーンショットを流用している。
- 色は拡張機能アイコン（`src/icons/`）のティール系グリーン（`#3FD4AD`）を基調にしている。
