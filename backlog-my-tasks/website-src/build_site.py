#!/usr/bin/env python3
"""Backlog My Tasks 紹介サイト ジェネレーター。
docs/build_deck.py（紹介PPT）と同じ「Pythonでコンポーネントを組み立てて静的出力する」方針。
出力は docs/website-src/dist/ 配下（そのまま GitHub Pages の gh-pages ブランチ直下へコピーする）。

多言語対応（v2）: 拡張機能本体（src/i18n.js）と同じ5言語（ja/en/ko/zh_TW/zh_HK）に対応する。
- 文言は日本語版の page_xxx() 関数をそのまま「原文（翻訳キー）」として使い、helper関数
  （feature_grid/showcase/section_head 等）とpage_xxx()内の生テキストを _() でラップする。
  _() は i18n/translations.json（{原文: {en:..., ko:..., zh_TW:..., zh_HK:...}}）を引く
  ヘルパーで、訳が無ければ日本語原文にフォールバックする（欠落を静かに握りつぶさないよう、
  フォールバックしたキーは MISSING に集計してビルド末尾に警告表示する）。
- 出力先はロケールごとに ja=dist/直下（既存URLを維持）、他は dist/<dir>/ 配下
  （en/ko/zh-TW/zh-HK）。アセット（assets/）は dist/assets/ に1つだけ配置し、
  サブディレクトリのページからは ../assets/... で参照する。
- ヘッダーに <details> ベース（JS不要）の言語切り替えメニューを追加し、
  hreflang alternate タグ・og:locale・canonical も言語ごとに出力する。
"""
import os, shutil, html, json

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, "dist")
ASSETS_SRC = os.path.join(HERE, "assets")
I18N_PATH = os.path.join(HERE, "i18n", "translations.json")

STORE_URL = "https://chromewebstore.google.com/detail/backlog-my-tasks/cangphedocncgiloahgkahplfppmfkhi"
SITE_NAME = "Backlog My Tasks"
SITE_TAGLINE = "Backlogを、もっと速く・もっと楽しく。"
# GitHub Pages の既定URL（カスタムドメイン未設定のため。CNAME等を追加したら要更新。
# README.mdの紹介サイトリンクと同じURLに揃えている）
BASE_URL = "https://kouji-kojima.github.io/pages/backlog-my-tasks/website-src/dist"

# ════════════════════════════════════════════════════════════
# 多言語設定
# ════════════════════════════════════════════════════════════
LANGS = ["ja", "en", "ko", "zh_TW", "zh_HK"]
LANG_INFO = {
    "ja":    {"html_lang": "ja",         "dir": ""},
    "en":    {"html_lang": "en",         "dir": "en"},
    "ko":    {"html_lang": "ko",         "dir": "ko"},
    "zh_TW": {"html_lang": "zh-Hant-TW", "dir": "zh-TW"},
    "zh_HK": {"html_lang": "zh-Hant-HK", "dir": "zh-HK"},
}
# 言語名は自言語表記（endonym）。サイトの表示言語に関わらず変えない（国際的な慣習）
LANG_ENDONYM = {
    "ja":    ("🇯🇵", "日本語"),
    "en":    ("🇺🇸", "English"),
    "ko":    ("🇰🇷", "한국어"),
    "zh_TW": ("🇹🇼", "繁體中文"),
    "zh_HK": ("🇭🇰", "繁體中文（香港）"),
}

try:
    with open(I18N_PATH, encoding="utf-8") as f:
        TR = json.load(f)
except FileNotFoundError:
    TR = {}

CURRENT_LANG = "ja"
CURRENT_ASSET_PREFIX = ""
ALL_STRINGS = set()  # _()に渡された全原文（翻訳対象の棚卸し用）
MISSING = set()      # (lang, text) — 訳が無く原文フォールバックしたもの


def _(text):
    """翻訳ヘルパー。TR[原文][lang] があればそれを、無ければ原文（日本語）を返す。"""
    if text is None or text == "":
        return text
    ALL_STRINGS.add(text)
    if CURRENT_LANG == "ja":
        return text
    entry = TR.get(text)
    if entry and entry.get(CURRENT_LANG):
        return entry[CURRENT_LANG]
    MISSING.add((CURRENT_LANG, text))
    return text


def lang_switch_href(target_lang, current_lang, filename):
    cur_dir = LANG_INFO[current_lang]["dir"]
    tgt_dir = LANG_INFO[target_lang]["dir"]
    prefix = "../" if cur_dir else ""
    return f"{prefix}{tgt_dir + '/' if tgt_dir else ''}{filename}"


# ════════════════════════════════════════════════════════════
# ナビゲーション定義（原文＝日本語。表示時に _() で訳す）
# ════════════════════════════════════════════════════════════
HEADER_NAV = [
    ("index.html", "ホーム"),
    ("views.html", "表示ビュー"),
    ("daily-features.html", "便利機能"),
    ("dashboard.html", "ダッシュボード"),
    ("game.html", "Backlog Quest"),
    ("use-cases.html", "活用シーン"),
    ("get-started.html", "導入方法"),
]

FOOTER_COLS = [
    ("表示ビュー", [
        ("views.html", "7つの表示ビュー"),
        ("view-list.html", "リスト"),
        ("view-matrix.html", "マトリックス"),
        ("view-kanban.html", "カンバン"),
        ("view-gantt.html", "ガント"),
        ("view-calendar.html", "カレンダー"),
        ("reports.html", "バーンダウン／ワークロード"),
    ]),
    ("便利機能", [
        ("daily-features.html", "毎日が変わる便利機能"),
        ("speed-features.html", "もっと速く・見える化"),
        ("task-creation.html", "作る・取り込む・使い回す"),
    ]),
    ("ダッシュボード", [
        ("dashboard.html", "ダッシュボード概要"),
        ("dashboard-project.html", "プロジェクト別ダッシュボード"),
        ("dashboard-gantt.html", "プロジェクト全体ガント"),
        ("dashboard-cross-space.html", "スペース横断／ユーザ棚卸"),
        ("dashboard-organization.html", "組織（部門管理）"),
    ]),
    ("その他", [
        ("game.html", "Backlog Quest"),
        ("use-cases.html", "活用シーン"),
        ("security-i18n.html", "多言語・セキュリティ"),
        ("feature-map.html", "全機能マップ"),
        ("get-started.html", "導入方法"),
    ]),
]

PAGE_META = {}  # filename -> (title, description) 登録用（ja分のみ集計）


# ════════════════════════════════════════════════════════════
# 基礎コンポーネント
# ════════════════════════════════════════════════════════════
def e(s):
    return html.escape(s, quote=False)


def page_shell(lang, filename, title, description, body, og_image="assets/img/13_game.jpg"):
    info = LANG_INFO[lang]
    ap = CURRENT_ASSET_PREFIX
    active_cls = ' class="active"'
    nav_html = "\n".join(
        f'<a href="{href}"{active_cls if href == filename else ""}>{e(_(label))}</a>'
        for href, label in HEADER_NAV
    )
    footer_cols = ""
    for col_title, links in FOOTER_COLS:
        items = "\n".join(f'<li><a href="{href}">{e(_(label))}</a></li>' for href, label in links)
        footer_cols += f'<div><h5>{e(_(col_title))}</h5><ul>{items}</ul></div>\n'

    site_tagline = _(SITE_TAGLINE)
    full_title = f"{title} | {SITE_NAME}" if title != SITE_NAME else f"{SITE_NAME} — {site_tagline}"

    page_path = f"{info['dir']}/{filename}" if info["dir"] else filename
    canonical = f"{BASE_URL}/{page_path}"
    og_image_abs = f"{BASE_URL}/{og_image}"
    hreflang_links = "\n".join(
        f'<link rel="alternate" hreflang="{LANG_INFO[l]["html_lang"]}" href="{BASE_URL}/{(LANG_INFO[l]["dir"] + "/") if LANG_INFO[l]["dir"] else ""}{filename}">'
        for l in LANGS
    )
    hreflang_links += f'\n<link rel="alternate" hreflang="x-default" href="{BASE_URL}/{filename}">'

    def _switch_item(l):
        active_attr = ' class="active"' if l == lang else ""
        return f'<a href="{lang_switch_href(l, lang, filename)}"{active_attr}>{LANG_ENDONYM[l][0]} {e(LANG_ENDONYM[l][1])}</a>'
    switch_items = "\n".join(_switch_item(l) for l in LANGS)

    return f"""<!doctype html>
<html lang="{info['html_lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{canonical}">
{hreflang_links}
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:image" content="{og_image_abs}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<meta property="og:locale" content="{info['html_lang'].replace('-', '_')}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{ap}assets/img/favicon.png">
<link rel="stylesheet" href="{ap}assets/css/style.css">
</head>
<body>
<header id="site-header">
  <div class="wrap bar">
    <a href="index.html" class="brand"><img src="{ap}assets/img/logo.png" alt=""><span>{SITE_NAME}</span></a>
    <nav id="site-nav">
      {nav_html}
    </nav>
    <details class="lang-switch">
      <summary>{LANG_ENDONYM[lang][0]} {e(LANG_ENDONYM[lang][1])}</summary>
      <div class="lang-switch-menu">{switch_items}</div>
    </details>
    <a class="btn btn-primary header-cta" href="{STORE_URL}" target="_blank" rel="noopener">{e(_("Chromeに追加"))}</a>
    <button id="nav-toggle" aria-label="{e(_("メニュー"))}">☰</button>
  </div>
</header>

{body}

<footer id="site-footer">
  <div class="wrap">
    <div class="fgrid">
      <div>
        <div class="fbrand"><img src="{ap}assets/img/logo.png" alt="">{SITE_NAME}</div>
        <p>{_("Backlog の自分担当タスクを、複数スペース横断でまとめて確認・操作できる Chrome 拡張機能。7つの表示ビューとプロジェクトダッシュボードで、日々のタスク管理とチームの進捗把握をもっと楽に。")}</p>
      </div>
      {footer_cols}
    </div>
    <div class="fbottom">
      <span>&copy; Backlog My Tasks</span>
      <span><a href="{STORE_URL}" target="_blank" rel="noopener">{e(_("Chrome ウェブストア"))}</a></span>
    </div>
  </div>
</footer>
<script src="{ap}assets/js/main.js"></script>
</body>
</html>
"""


def page_hero(eyebrow, title, lead, crumb=None):
    crumb_html = f'<div class="breadcrumb"><a href="index.html">{e(_("ホーム"))}</a> / {e(_(crumb))}</div>' if crumb else ""
    return f"""<section class="page-hero">
  <div class="wrap inner">
    {crumb_html}
    <div class="eyebrow">{e(_(eyebrow))}</div>
    <h1>{_(title)}</h1>
    <p class="lead">{_(lead)}</p>
  </div>
</section>
"""


def section_head(eyebrow, title, lead=""):
    lead_html = f"<p>{_(lead)}</p>" if lead else ""
    return f"""<div class="section-head">
      <div class="eyebrow">{e(_(eyebrow))}</div>
      <h2>{_(title)}</h2>
      {lead_html}
    </div>"""


def feature_grid(items, cols=4, dark=False):
    """items: list of (emoji, title, desc)"""
    cls = "card on-dark" if dark else "card"
    cards = ""
    for emoji, title, desc in items:
        cards += f"""<div class="{cls}">
          <div class="icon">{emoji}</div>
          <h3>{e(_(title))}</h3>
          <p>{_(desc)}</p>
        </div>\n"""
    return f'<div class="grid grid-{cols}">\n{cards}</div>'


def showcase(img, alt, bullets, reverse=False):
    """bullets: list of (title, desc)"""
    b_html = ""
    for title, desc in bullets:
        b_html += f"""<div class="bullet">
          <div class="dot"></div>
          <div><h4>{e(_(title))}</h4><p>{_(desc)}</p></div>
        </div>\n"""
    rev = " reverse" if reverse else ""
    return f"""<div class="showcase{rev}">
      <div class="frame"><img src="{CURRENT_ASSET_PREFIX}assets/img/{img}" alt="{e(_(alt))}" loading="lazy"></div>
      <div class="bullets">{b_html}</div>
    </div>"""


def stat_bar(stats):
    """stats: list of (num, label)"""
    items = "".join(f'<div class="stat"><div class="num">{e(n)}</div><div class="lbl">{e(_(l))}</div></div>' for n, l in stats)
    return f'<div class="stat-bar">{items}</div>'


def pain_grid(items):
    """items: list of (emoji, title, desc)"""
    cards = "".join(
        f'<div class="pain"><div class="emoji">{emoji}</div><h4>{e(_(title))}</h4><p>{_(desc)}</p></div>'
        for emoji, title, desc in items
    )
    return f'<div class="pain-grid">{cards}</div>'


def scenario(emoji, tag, title, scene, howto, result):
    """howto: list of (title, desc)"""
    howto_html = "".join(f'<div><strong>{e(_(t))}</strong><p>{_(d)}</p></div>' for t, d in howto)
    return f"""<div class="scenario">
      <div class="sc-head"><span class="emoji">{emoji}</span><h3>{e(_(title))}</h3><span class="tag">{e(_(tag))}</span></div>
      <div class="sc-row scene"><div class="sc-label">😩 {e(_("よくあるシーン"))}</div><p>{_(scene)}</p></div>
      <div class="sc-row howto"><div class="sc-label">💡 {e(_("こう使う"))}</div><div class="howto-list">{howto_html}</div></div>
      <div class="sc-row result"><div class="sc-label">🎉 {e(_("効果"))}</div><p>{_(result)}</p></div>
    </div>"""


def steps(items):
    """items: list of (title, desc)"""
    s = ""
    for i, (title, desc) in enumerate(items, 1):
        s += f"""<div class="step">
          <div class="num">{i}</div>
          <h3>{e(_(title))}</h3>
          <p>{_(desc)}</p>
        </div>\n"""
    return f'<div class="steps">{s}</div>'


def cta_band(title, lead, primary_label="Chromeに追加", secondary=None):
    sec_html = ""
    if secondary:
        href, label = secondary
        sec_html = f'<a class="btn btn-ghost" style="background:rgba(255,255,255,.12);color:#fff;border-color:rgba(255,255,255,.3)" href="{href}">{e(_(label))}</a>'
    return f"""<div class="cta-band">
      <h2>{_(title)}</h2>
      <p>{_(lead)}</p>
      <div class="cta-row">
        <a class="btn btn-on-dark" href="{STORE_URL}" target="_blank" rel="noopener">{e(_(primary_label))}</a>
        {sec_html}
      </div>
    </div>"""


def lang_grid():
    # 言語名は自言語表記のため翻訳しない（LANG_ENDONYMと同じ一覧をそのまま流用）
    items = "".join(
        f'<div class="lang"><div class="flag">{f}</div><div class="name">{e(n)}</div><div class="code">{c}</div></div>'
        for c, (f, n) in LANG_ENDONYM.items()
    )
    return f'<div class="lang-grid">{items}</div>'


def map_card(emoji, title, items):
    lis = "".join(f"<li>{e(_(i))}</li>" for i in items)
    return f'<div class="map-card"><h3>{emoji} {e(_(title))}</h3><ul>{lis}</ul></div>'


def linked_grid(items, cols=4):
    """items: list of (href, emoji, title, desc) — カード全体がリンクになるバージョン"""
    cards = ""
    for href, emoji, title, desc in items:
        cards += f"""<a class="card" href="{href}">
          <div class="icon">{emoji}</div>
          <h3>{e(_(title))}</h3>
          <p>{_(desc)}</p>
        </a>\n"""
    return f'<div class="grid grid-{cols}">\n{cards}</div>'


def write_page(lang, filename, title, description, body, og_image="assets/img/13_game.jpg"):
    title_t = title if title == SITE_NAME else _(title)
    desc_t = _(description)
    if lang == "ja":
        PAGE_META[filename] = (title_t, desc_t)
    out_dir = os.path.join(DIST, LANG_INFO[lang]["dir"]) if LANG_INFO[lang]["dir"] else DIST
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, filename), "w", encoding="utf-8") as f:
        f.write(page_shell(lang, filename, title_t, desc_t, body, og_image))
    print("WROTE", lang, filename)


# ════════════════════════════════════════════════════════════
# 01. index.html ── ホーム（メリット訴求 → 概要）
# ════════════════════════════════════════════════════════════
def page_index(lang):
    body = f"""
<section class="hero">
  <div class="wrap">
    <div class="kicker">{_("🧩 Chrome拡張機能・7つの表示ビュー・5言語対応")}</div>
    <h1>{_('毎日のタスク管理を、<br><span class="accent">もっと速く・もっと楽に。</span>')}</h1>
    <p class="lead">{_("Backlog の自分担当タスクを、複数スペース横断でまとめて確認・操作できる Chrome 拡張機能。ブラウザのポップアップを開くだけで、状態変更もコメント返信も、これ1つで完結します。")}</p>
    <div class="cta-row">
      <a class="btn btn-primary" href="{STORE_URL}" target="_blank" rel="noopener">{e(_("Chromeに追加"))}</a>
      <a class="btn btn-ghost" style="background:rgba(255,255,255,.08);color:#fff;border-color:rgba(255,255,255,.28)" href="get-started.html">{e(_("導入方法を見る"))}</a>
    </div>
    <p class="fineprint">{_("APIキーは端末内でAES-256暗号化・外部サーバーへの送信ゼロ。導入は3ステップ、すぐ使えます。")}</p>
  </div>
</section>

<section class="tint">
  <div class="wrap">
    {section_head("こんな悩み、ありませんか？", "Backlogは便利。でも、毎日の確認はちょっと大変。")}
    {pain_grid([
        ("😵","タスクが多すぎる","複数プロジェクト・複数スペースに散らばって、今日やるべきことが分からない"),
        ("⏰","期限を見落とす","気づいたら期限切れ。Backlogを開くまで通知に気づけない"),
        ("💬","コメントに気づかない","返信が来ていたのに、タスクを開くまで分からなかった"),
        ("📊","進捗が見えない","チーム全体の状況や遅延プロジェクトを把握するのに時間がかかる"),
    ])}
    <div class="pain-arrow">{_('→ Backlog My Tasks なら、その全部を<br class="pain-arrow-br">ブラウザのポップアップだけで解決できます。')}</div>
  </div>
</section>

<section>
  <div class="wrap">
    {section_head("Backlog My Tasks とは", "Backlogに蓄積されたタスクを、ワンクリックで。", "ブラウザのポップアップを開くだけで、素早く確認・操作できる Chrome 拡張機能です。")}
    {stat_bar([("7","表示ビュー"),("10","スペース同時管理"),("5","対応言語"),("6","プロジェクトダッシュボード")])}
    <div class="mt">
    {feature_grid([
        ("🚀","ワンクリックでタスク確認","Backlogを開かず状態変更・期限変更・コメントまで完結"),
        ("🔒","APIキーはAES-256暗号化","端末外へのデータ送信ゼロ。Backlogとのみ通信"),
        ("⚡","並列取得＋キャッシュ活用","データ管理・ワークロード・コメント取得を並列化。IndexedDBキャッシュで2回目以降は即時表示"),
    ], cols=3)}
    </div>
  </div>
</section>

<section class="tint">
  <div class="wrap">
    {section_head("表示ビュー", "自由に見える化できる、7つの表示ビュー", "リスト・カレンダー・マトリックス・ガント・カンバン・サマリー・バーンダウン。タブ切替でいつでも視点を変えられます。")}
    {linked_grid([
        ("view-list.html","📋","リスト","期限別グループ表示"),
        ("view-calendar.html","📅","カレンダー","月単位で期限を俯瞰"),
        ("view-matrix.html","⊞","マトリックス","緊急度×重要度の4象限"),
        ("view-gantt.html","🌳","ガント","親子タスクの階層ツリー"),
        ("view-kanban.html","🗂","カンバン","ステータス別D&D"),
        ("daily-features.html","📝","サマリー","テキストでコピー可"),
        ("reports.html","📉","バーンダウン","予定実績2ラインで即時表示"),
    ], cols=4)}
  </div>
</section>

<section class="dark">
  <div class="wrap">
    {section_head("🎮 Backlog Quest", "Backlogを使うほど、キャラクターが育っていく。", "日々のタスク処理が、そのまま経験値になる実績連動RPG。正式リリース済み・デフォルトONで、不要ならオプションからいつでもオフにできます。")}
    {feature_grid([
        ("⚔️","8つの職業から選択","戦士・魔法使い・武道家・アイドル・歌手・俳優・サッカー選手・野球選手"),
        ("⬆️","レベルアップ＆称号","ログイン・タスク完了・コメントで経験値を獲得。相棒のペットも一緒に育つ"),
        ("🛡️","装備でアバターが変化","武器・防具・兜・盾を全11〜12段階で収集。装備すると見た目にも即反映"),
        ("🐲","ボス戦・隠しボス","10Lvごとにボスが出現。条件達成で隠しボスも姿を現す"),
    ], cols=4, dark=True)}
    <p class="center mt"><a class="btn btn-on-dark" href="game.html">{e(_("Backlog Questをもっと見る →"))}</a></p>
  </div>
</section>

<section>
  <div class="wrap">
    {cta_band("さあ、今日から使ってみよう！", "Backlogを開く回数が、きっと減ります。タスク管理も、チームの進捗把握も、これ1つで。", secondary=("get-started.html","導入方法を見る"))}
  </div>
</section>
"""
    write_page(lang, "index.html", SITE_NAME,
               "Backlogの自分担当タスクを複数スペース横断でまとめて管理するChrome拡張機能。7つの表示ビュー・プロジェクトダッシュボード・5言語対応。",
               body, "assets/img/01_list.jpg")


# ════════════════════════════════════════════════════════════
# 02. views.html ── 表示ビュー ハブ
# ════════════════════════════════════════════════════════════
def page_views(lang):
    body = f"""
{page_hero("表示ビュー", "7つの表示ビューで、自由に見える化。", "同じタスクを、リスト・カレンダー・マトリックス・ガント・カンバン・サマリー・バーンダウンの7つの視点で。タブ切替でいつでも視点を切り替えられます。", "表示ビュー")}
<section>
  <div class="wrap">
    {linked_grid([
        ("view-list.html","📋","リスト","期限別グループ表示。一番よく使うメインビュー"),
        ("view-calendar.html","📅","カレンダー","月単位で期限を俯瞰。7週間ローリング表示も選択可"),
        ("view-matrix.html","⊞","マトリックス","緊急度×重要度の4象限バブルチャート"),
        ("view-gantt.html","🌳","ガント","親子タスクの階層ツリー＋依存関係・クリティカルパス"),
        ("view-kanban.html","🗂","カンバン","ステータス別カードをドラッグ＆ドロップで移動"),
        ("daily-features.html","📝","サマリー","テキストでコピー可。日報・週報ドラフトも自動生成"),
        ("reports.html","📉","バーンダウン／ワークロード","予定実績2ラインの進捗管理と担当者別工数の可視化"),
    ], cols=4)}
    <div class="mt">{cta_band("まずは自分のタスクで試してみましょう", "ワンクリックでビューを切り替えられます。", secondary=("get-started.html","導入方法を見る"))}</div>
  </div>
</section>
"""
    write_page(lang, "views.html", "7つの表示ビュー",
               "リスト・カレンダー・マトリックス・ガント・カンバン・サマリー・バーンダウン。タブ切替で自由に視点を変えられます。",
               body, "assets/img/01_list.jpg")


# ════════════════════════════════════════════════════════════
# 03. view-list.html
# ════════════════════════════════════════════════════════════
def page_view_list(lang):
    body = f"""
{page_hero("表示ビュー ─ リスト", "リスト ─ 一番使う、メインビュー。", "毎朝の確認をワンクリックで。期限別に自動整列されたタスク一覧から、状態変更・コメント返信までここで完結します。", "リスト")}
<section>
  <div class="wrap">
    {showcase("01_list.jpg", "リストビューのスクリーンショット", [
        ("期限別グループで一目瞭然","期限切れ・本日・1週間以内…と自動でグループ分け。色で危険度がすぐ分かる"),
        ("クイックフィルター＆全文検索","ワンクリック絞り込み（キー1〜5）。件名・キー・担当者まで横断検索"),
        ("一括操作＆右クリックメニュー","複数選択して状態・期限・担当者をまとめて変更。右クリックで件名・詳細の編集や完了・期限変更などを即操作"),
        ("コメント通知でゼロ見落とし","他者の新着コメントはリスト最上部へ自動浮上。💬ボタンが黄色点灯して即気づける"),
    ])}
    <div class="mt">{cta_band("朝の確認を1分に。", "開くだけで期限別に自動整列されているので、迷わず今日やることから着手できます。", secondary=("use-cases.html","活用シーンを見る"))}</div>
  </div>
</section>
"""
    write_page(lang, "view-list.html", "リストビュー",
               "期限別グループ表示・クイックフィルター・全文検索・一括操作・コメント通知でゼロ見落としを実現するメインビュー。",
               body, "assets/img/01_list.jpg")


# ════════════════════════════════════════════════════════════
# 04. view-matrix.html
# ════════════════════════════════════════════════════════════
def page_view_matrix(lang):
    body = f"""
{page_hero("表示ビュー ─ マトリックス", "マトリックス ─ 優先順位を直感で。", "アイゼンハワーの4象限で、緊急度×重要度からタスクを自動配置。どれから手をつけるべきかが一目で分かります。", "マトリックス")}
<section>
  <div class="wrap">
    {showcase("03_matrix.jpg", "マトリックスビューのスクリーンショット", [
        ("アイゼンハワーの4象限","緊急度（期限の近さ）×重要度（優先度）でタスクを自動配置"),
        ("優先度は宝石カラーで一目瞭然","ルビー赤（高）／アンバー黄（中）／サファイア青（低）。星の大きさ＝予定工数"),
        ("象限クリックでタスク一覧","右パネルに課題キー（同じ宝石カラー）付きで表示"),
    ])}
    <div class="mt">{cta_band("優先順位に迷わない。", "マトリックスを開くだけで4象限に自動でプロット。右上の象限から順に着手すればOKです。", secondary=("use-cases.html","活用シーンを見る"))}</div>
  </div>
</section>
"""
    write_page(lang, "view-matrix.html", "マトリックスビュー",
               "アイゼンハワーの4象限で緊急度×重要度からタスクを自動配置。優先度は宝石カラーで一目瞭然。",
               body, "assets/img/03_matrix.jpg")


# ════════════════════════════════════════════════════════════
# 05. view-kanban.html
# ════════════════════════════════════════════════════════════
def page_view_kanban(lang):
    body = f"""
{page_hero("表示ビュー ─ カンバン", "カンバン ─ ドラッグ＆ドロップで状態変更。", "未対応・処理中・処理済み・完了の4列でチーム全体の進捗をひと目で把握。カードを動かすだけでBacklogへ即反映されます。", "カンバン")}
<section>
  <div class="wrap">
    {showcase("08_kanban.jpg", "カンバンビューのスクリーンショット", [
        ("ステータス別カード表示","未対応・処理中・処理済み・完了をひと目で把握"),
        ("D&Dでステータス移動","カードを掴んで動かすだけ。Backlogへ即反映"),
        ("遅延・本日期限をハイライト","期限切れ=ピンク、本日=黄色で危険タスクが目立つ"),
        ("列ごとのWIP制限","同時進行の上限件数を列ごとに設定でき、超過時は列ヘッダーを警告色で表示"),
    ])}
    <div class="mt">{cta_band("朝会が5分で終わる。", "画面共有するだけで全員の状況が一目。ステータス変更もその場でD&Dできます。", secondary=("use-cases.html","活用シーンを見る"))}</div>
  </div>
</section>
"""
    write_page(lang, "view-kanban.html", "カンバンビュー",
               "未対応・処理中・処理済み・完了をドラッグ＆ドロップで移動。WIP制限や遅延ハイライトにも対応。",
               body, "assets/img/08_kanban.jpg")


# ════════════════════════════════════════════════════════════
# 06. view-gantt.html
# ════════════════════════════════════════════════════════════
def page_view_gantt(lang):
    body = f"""
{page_hero("表示ビュー ─ ガント", "ガント ─ 親子タスクを時系列で。", "階層ツリーとタイムラインで、期間・依存関係・進捗をまとめて可視化。バーをドラッグするだけで日程調整が完結します。", "ガント")}
<section>
  <div class="wrap">
    {showcase("07_gantt.jpg", "ガントビューのスクリーンショット", [
        ("階層ツリー＋タイムライン","親子タスクの構造を保ちながら期間を可視化。完了タスク非表示も対応"),
        ("バーをドラッグして日程変更","開始日・期限日をドラッグで直接変更。Backlogへ即反映。依存する後続タスクへの自動日程シフトも確認付きで実行"),
        ("カミナリ線で進捗が一目","各タスクの進捗ラインをつなぐカミナリ線で、遅れ・先行をすぐ把握"),
        ("依存関係とクリティカルパス","タスク間の先行→後続を矢印で可視化。遅延警告と最長経路の強調表示"),
        ("マイルストーン◆・進捗ロールアップ・高速表示","マイルストーン期限を可視化し、親タスクには子の完了率を表示。大規模プロジェクトも仮想スクロールで軽快に動作"),
    ])}
    <div class="mt">{cta_band("スケジュール調整をその場で。", "バーをドラッグして期限変更、後続タスクへの自動シフトまでガント画面だけで完結します。", secondary=("use-cases.html","活用シーンを見る"))}</div>
  </div>
</section>
"""
    write_page(lang, "view-gantt.html", "ガントビュー",
               "親子タスクの階層ツリー、バードラッグでの日程変更、依存関係とクリティカルパス、マイルストーン表示に対応。",
               body, "assets/img/07_gantt.jpg")


# ════════════════════════════════════════════════════════════
# 07. view-calendar.html
# ════════════════════════════════════════════════════════════
def page_view_calendar(lang):
    body = f"""
{page_hero("表示ビュー ─ カレンダー", "カレンダー ─ 月単位で期限を俯瞰。", "タスクを期限日のマスに配置。当月の締切バランスがひと目で分かり、月末の慌てもなくなります。", "カレンダー")}
<section>
  <div class="wrap">
    {showcase("02_calendar.jpg", "カレンダービューのスクリーンショット", [
        ("月カレンダーで期限を配置","タスクを期限日のマスに表示。当月の締切バランスがひと目で分かる"),
        ("危険度をカラー表示","期限切れ=赤、本日期限=橙でハイライト。見落としを防ぐ"),
        ("月末でも先の予定が丸わかり","今月／来月の件数バッジ＋前後月セルにも実タスクを表示。先週分も見える7週間ローリング表示も選択可"),
        ("クリックでBacklogへ","タスクをクリックすると該当課題をすぐに開ける"),
    ])}
    <div class="mt">{cta_band("締切ラッシュを先読み。", "月カレンダーで締切の偏りに早めに気づき、前倒しで余裕を持って着手できます。", secondary=("use-cases.html","活用シーンを見る"))}</div>
  </div>
</section>
"""
    write_page(lang, "view-calendar.html", "カレンダービュー",
               "月単位・7週間ローリング表示で期限を俯瞰。危険度をカラー表示し、締切の偏りに早めに気づけます。",
               body, "assets/img/02_calendar.jpg")


# ════════════════════════════════════════════════════════════
# 08. reports.html ── バーンダウン／ワークロード
# ════════════════════════════════════════════════════════════
def page_reports(lang):
    body = f"""
{page_hero("表示ビュー ─ レポート", "レポート ─ 予実と工数を可視化。", "バーンダウンで進捗の予定と実績を追い、ワークロードで担当者ごとの負荷をひと目で把握できます。", "レポート")}
<section>
  <div class="wrap">
    {showcase("05_burndown.jpg", "バーンダウンチャートのスクリーンショット", [
        ("📉 予定・実績の2ラインで進捗を追跡","プロジェクト全体はキャッシュから即時表示（API不要）"),
        ("マイルストーン／カテゴリーで絞り込み","見たい範囲だけを切り出してチャートを確認できる"),
    ])}
    <div class="divider"></div>
    {showcase("06_workload.jpg", "ワークロード（負荷ヒートマップ）のスクリーンショット", [
        ("👤 担当者別の残時間／完了時間","残時間（青）・完了時間（緑）を積み上げグラフで表示"),
        ("「処理済みも完了扱い」トグルに連動","チームの運用ルールに合わせて集計を切り替えられる"),
        ("ページ並列取得で大人数チームも高速表示","APIを並列に呼び出すことで待ち時間を短縮"),
    ], reverse=True)}
    <div class="mt">{cta_band("週次報告が数分で完了。", "健全性スコア・完了率・遅延hが自動集計され、横並びで比較できます。", secondary=("dashboard.html","ダッシュボードを見る"))}</div>
  </div>
</section>
"""
    write_page(lang, "reports.html", "バーンダウン／ワークロード",
               "予定・実績の2ラインで進捗を追跡するバーンダウンと、担当者別の負荷を可視化するワークロード。",
               body, "assets/img/05_burndown.jpg")


# ════════════════════════════════════════════════════════════
# 09. daily-features.html
# ════════════════════════════════════════════════════════════
def page_daily_features(lang):
    body = f"""
{page_hero("便利機能", "毎日が変わる、便利機能たち。", "コメント検知・タイマー・通知・オフライン対応など、地味だけど毎日効いてくる機能を集めました。", "毎日が変わる便利機能")}
<section>
  <div class="wrap">
    {feature_grid([
        ("💬","新着コメント自動検知","前回確認後に届いたコメントをリスト最上部に自動でピックアップ"),
        ("⏱","タイムトラッキング","ボタン1つで作業時間を計測。停止時にBacklog実績時間へ反映"),
        ("💤","スヌーズ","指定日まで一覧・バッジ・通知から一時的に非表示にできる"),
        ("🔔","多彩な通知","期限デスクトップ通知は都度／1日1回から選択可。メンション未読バッジ＋Slack／Teams Webhook連携"),
        ("📴","オフライン対応","圏外での変更はキューに保存し、復帰後に自動送信"),
        ("🌛","ダークモード","ライト／ダーク切替。OS設定への自動追従も対応"),
    ], cols=3)}
  </div>
</section>
<section class="tint">
  <div class="wrap">
    {section_head("さらに便利に", "新しくできること")}
    {feature_grid([
        ("📌","Backlogページ常駐タブ","ページ右端のタブから全画面オーバーレイで開閉できる"),
        ("📝","日報・週報ドラフト","完了・対応中・期限超過をもとに下書きを自動生成、そのままコピー"),
        ("🏥","プロジェクト健全性スコア","期限切れ率・停滞数・担当偏りから0〜100点で自動採点。直近30日の推移スパークライン付き"),
        ("🐢","フォロータスク検出","期限1週間以内・未完了のタスクを一覧化。全タスクと同じインライン編集＋ワンクリックでフォローコメント"),
        ("🔀","依存関係の自動日程シフト","ガントで先行タスクの期限を変更すると後続タスクの日程も確認のうえ自動で移動"),
        ("📆","週次ふりかえりレポート","今週の完了・新規・持ち越し・遵守率を先週比のKPIカードとグラフで表示"),
    ], cols=3)}
    <div class="mt">{cta_band("見落としがゼロになる毎日へ。", "新着コメントも期限も、気づく前に教えてくれます。", secondary=("speed-features.html","もっと速く・見える化を見る"))}</div>
  </div>
</section>
"""
    write_page(lang, "daily-features.html", "毎日が変わる便利機能",
               "新着コメント自動検知・タイマー・スヌーズ・通知・オフライン対応・健全性スコア・日報週報ドラフトなど、日々のタスク管理を支える機能。",
               body, "assets/img/04_summary.jpg")


# ════════════════════════════════════════════════════════════
# 10. speed-features.html
# ════════════════════════════════════════════════════════════
def page_speed_features(lang):
    body = f"""
{page_hero("便利機能", "もっと速く、もっと見える化。", "登録も分析も、数秒で終わらせる機能たち。1件のタスクから多くの操作がその場で完結します。", "もっと速く・見える化")}
<section>
  <div class="wrap">
    {feature_grid([
        ("⚡","クイック登録バー","「資料作成 7/25」のように1行入力してEnterで即タスク登録"),
        ("📄","複製登録","既存タスクの内容を引き継いでフォームを開き、確認してから登録"),
        ("🗓","負荷ヒートマップ","担当者×週の負荷を色の濃淡で表示。ドラッグ＆ドロップで担当者を変更"),
        ("⏱","リードタイム分析","完了までの日数をヒストグラム表示。優先度別の平均リードタイムも一覧"),
        ("🚧","カンバンWIP制限","列ごとに同時進行の上限件数を設定し、超過時は列ヘッダーを警告色で表示"),
        ("☑️","全タスク一括操作","チェックボックスで複数選択し、状態・担当者・優先度をまとめて変更"),
    ], cols=3)}
  </div>
</section>
<section class="tint">
  <div class="wrap">
    {section_head("✏️ クイック編集", "1つのモーダルでまとめて編集", "状態・担当者・優先度をその場で、Backlogを開かずモーダル内で変更して保存。開始日・期限日も同時に編集でき、変更した項目だけ更新するので余分なAPIリクエストも出しません。")}
    {feature_grid([
        ("✅","状態変更",""),("👤","担当者変更","「私が担当」ボタンでワンクリックセットも可能"),
        ("📅","期限変更","開始日・期限日を1リクエストで更新し検証エラーを回避"),
        ("⏱","タイマー計測",""),("💬","コメント投稿",""),("📌","ピン留め",""),
        ("💤","スヌーズ",""),("📄","タスク複製",""),("📝","ローカルメモ",""),
    ], cols=3)}
    <div class="mt">{cta_band("タスク1件からできることを、もっと。", "右クリック／ホバーから、必要な操作にすぐ手が届きます。", secondary=("task-creation.html","作る・取り込む・使い回すを見る"))}</div>
  </div>
</section>
"""
    write_page(lang, "speed-features.html", "もっと速く・見える化",
               "クイック登録バー・複製登録・負荷ヒートマップ・リードタイム分析・カンバンWIP制限・クイック編集モーダルなど、スピードを上げる機能。",
               body, "assets/img/04_summary.jpg")


# ════════════════════════════════════════════════════════════
# 11. task-creation.html
# ════════════════════════════════════════════════════════════
def page_task_creation(lang):
    body = f"""
{page_hero("便利機能", "作る・取り込む・使い回す。", "新規作成もCSV一括登録も、テンプレートの使い回しも自在に。毎回ゼロから入力する手間をなくします。", "登録・テンプレート")}
<section>
  <div class="wrap">
    {feature_grid([
        ("📝","タスク作成","プロジェクト・種別・担当者・マイルストーン・親課題を指定して新規作成"),
        ("📥","CSV一括登録","CSVから複数タスクをまとめて登録。テンプレCSVのダウンロードにも対応"),
        ("📤","CSV出力","現在の一覧をBOM付きUTF-8で出力。参照列＋一括登録用列を1ファイルに"),
        ("💬","コメントテンプレート","よく使う返信を保存し、メンション付きで素早く投稿"),
        ("🔖","フィルタープリセット","フィルター・検索・グループ設定を名前付きで保存・呼び出し"),
        ("📌","ピン留め","重要タスクを最上部に固定＋Backlogのウォッチにも自動登録"),
    ], cols=3)}
    <div class="mt">{cta_band("登録の手間を、限りなくゼロに。", "既存タスクの複製・CSV一括登録・テンプレートで、毎回の入力作業を減らせます。", secondary=("dashboard.html","ダッシュボードを見る"))}</div>
  </div>
</section>
"""
    write_page(lang, "task-creation.html", "作る・取り込む・使い回す",
               "タスク作成・CSV一括登録／出力・コメントテンプレート・フィルタープリセット・ピン留めなど、登録と使い回しを効率化する機能。",
               body, "assets/img/04_summary.jpg")


# ════════════════════════════════════════════════════════════
# 12. dashboard.html ── ダッシュボード ハブ
# ════════════════════════════════════════════════════════════
def page_dashboard(lang):
    body = f"""
{page_hero("👑 ダッシュボード", "プロジェクトダッシュボードで、チーム全体を俯瞰。", "全ユーザーに表示される管理タブ（ユーザ棚卸のみ管理者専用）。所属プロジェクトが自動表示され、API呼び出しはデータ管理タブのみです。", "ダッシュボード")}
<section>
  <div class="wrap">
    {linked_grid([
        ("dashboard-project.html","📊","プロジェクト別ダッシュボード","KPIカード（完了率・健全性スコア）／ベロシティ・優先度マトリックス／前回・先週との差分ビュー"),
        ("dashboard-project.html","📋","全タスク","プロジェクト全タスクを一覧表示。セル内インライン編集・ピン止めボタンも搭載"),
        ("dashboard-gantt.html","📈","ガント","プロジェクト全体のガントチャート。個人ガントと同じUI（イナズマ線つき）"),
        ("dashboard-cross-space.html","🌐","スペース横断サマリー","キャッシュから即時集計。リスクプロジェクト自動検出・マイルストーン横断ビュー"),
        ("dashboard-cross-space.html","👥","全員ワークロード","スペース全担当者の工数を集計。残業h／完了h横棒グラフ、API追加呼び出しゼロ"),
        ("dashboard.html","📦","データ管理","API呼び出しはこのタブだけ。アクティブ／非アクティブ分類で取得不要プロジェクトを除外"),
        ("dashboard-cross-space.html","👤","ユーザ棚卸（管理者専用）","全ユーザの最終ログイン状況。1年以上未ログインを赤強調し、スペースから削除も可能"),
        ("dashboard-organization.html","🏢","組織（部門管理）","部門ツリーを登録してプロジェクトを割り当て、部門単位でプロジェクトを分析"),
    ], cols=4)}
    <div class="mt">{cta_band("週次報告の準備を、数分で。", "健全性スコア・完了率・遅延hが自動集計され、横並びで比較できます。", secondary=("dashboard-cross-space.html","スペース横断サマリーを見る"))}</div>
  </div>
</section>
"""
    write_page(lang, "dashboard.html", "プロジェクトダッシュボード",
               "プロジェクト別ダッシュボード・全タスク・ガント・スペース横断サマリー・全員ワークロード・データ管理・ユーザ棚卸をまとめた管理タブ。",
               body, "assets/img/09_admin_project.jpg")


# ════════════════════════════════════════════════════════════
# 13. dashboard-project.html
# ════════════════════════════════════════════════════════════
def page_dashboard_project(lang):
    body = f"""
{page_hero("ダッシュボード", "プロジェクト別ダッシュボード ─ KPIを一画面で。", "総タスク数から健全性スコアまで、プロジェクトの状態がひと目で分かります。", "プロジェクト別ダッシュボード")}
<section>
  <div class="wrap">
    {showcase("09_admin_project.jpg", "プロジェクト別ダッシュボードのスクリーンショット", [
        ("KPIを一画面で","総タスク・未完了・遅延・完了率・予定時間・健全性スコア（A〜F）"),
        ("前回／先週 差分ビュー","優先度・マイルストーン・カテゴリー・開始日など7種類の変更をテーブル形式で表示"),
        ("ベロシティで勢いを把握","直近12週の完了時間を棒グラフ化。平均線つき"),
        ("未アサインをその場で解消","担当者プルダウンで即時割り当て。親タスクでグルーピング表示"),
    ])}
    <div class="mt">{cta_band("プロジェクトの今を、一画面で。", "健全性スコアと差分ビューで、報告前の状況確認がぐっと速くなります。", secondary=("dashboard-gantt.html","プロジェクト全体ガントを見る"))}</div>
  </div>
</section>
"""
    write_page(lang, "dashboard-project.html", "プロジェクト別ダッシュボード",
               "KPIカード・前回／先週の差分ビュー・ベロシティグラフ・未アサインのその場解消など、プロジェクトの状態を一画面で確認。",
               body, "assets/img/09_admin_project.jpg")


# ════════════════════════════════════════════════════════════
# 14. dashboard-gantt.html
# ════════════════════════════════════════════════════════════
def page_dashboard_gantt(lang):
    body = f"""
{page_hero("ダッシュボード", "ガント（プロジェクト全体） ─ 時系列で俯瞰。", "選択プロジェクトの全タスク（全担当者）を1枚のガントに集約。個人ガントと同じUIで、そのまま日程調整までできます。", "プロジェクト全体ガント")}
<section>
  <div class="wrap">
    {showcase("07_gantt.jpg", "プロジェクト全体ガントのスクリーンショット", [
        ("プロジェクト全体を時系列で","選択プロジェクトの全タスク（全担当者）を1枚のガントに集約"),
        ("個人ガントと同じUI","親子ツリー・今日線・進捗ライン（イナズマ線）・バー端ドラッグで日付変更（依存タスクの自動シフトも共通）"),
        ("自在に絞り込み","期間・担当者・自分・ステータス・キーワード検索で対象を絞る"),
        ("キャッシュから即時表示","データ管理で取得済みならAPI呼び出しゼロで描画"),
    ])}
    <div class="mt">{cta_band("プロジェクト全体の日程調整を、1画面で。", "誰かの遅れが他のタスクへどう影響するかも、ガント上でその場に完結します。", secondary=("dashboard-cross-space.html","スペース横断サマリーを見る"))}</div>
  </div>
</section>
"""
    write_page(lang, "dashboard-gantt.html", "プロジェクト全体ガント",
               "選択プロジェクトの全タスク・全担当者を1枚のガントに集約。個人ガントと同じUIで日程調整もその場で完結。",
               body, "assets/img/07_gantt.jpg")


# ════════════════════════════════════════════════════════════
# 15. dashboard-cross-space.html
# ════════════════════════════════════════════════════════════
def page_dashboard_cross_space(lang):
    body = f"""
{page_hero("ダッシュボード", "スペース横断で、全プロジェクトを俯瞰。", "複数スペースの状態をまとめて比較し、休眠アカウントも一目で見つけられます。", "スペース横断・ユーザ棚卸")}
<section>
  <div class="wrap">
    {showcase("10_admin_space.jpg", "スペース横断サマリーのスクリーンショット", [
        ("全プロジェクトを俯瞰","完了率・遅延h・健全性スコアを横並びで比較"),
        ("リスクを自動検出","遅延率50%以上=🔴、20%以上=🟡で自動フラグ"),
        ("マイルストーン横断ビュー","全プロジェクトの締切と完了率をまとめて確認"),
    ])}
    <div class="divider"></div>
    {showcase("12_admin_users.jpg", "ユーザ棚卸のスクリーンショット", [
        ("最終ログインを可視化","全ユーザのログイン日と経過日数を一覧表示"),
        ("休眠アカウントを発見","1年以上未ログインを赤でハイライト＆自動ソート"),
        ("ライセンス棚卸に最適","不要アカウントはその場でスペースから削除（スペース管理者専用）"),
    ], reverse=True)}
    <div class="mt">{cta_band("危険プロジェクトに、早期着手。", "遅延率で自動フラグが立つので、手を打つべきプロジェクトがひと目で分かります。", secondary=("dashboard-organization.html","組織（部門管理）を見る"))}</div>
  </div>
</section>
"""
    write_page(lang, "dashboard-cross-space.html", "スペース横断サマリー／ユーザ棚卸",
               "全プロジェクトの完了率・遅延h・健全性スコアを横並びで比較。ユーザ棚卸で休眠アカウントも発見できます。",
               body, "assets/img/10_admin_space.jpg")


# ════════════════════════════════════════════════════════════
# 15.5. dashboard-organization.html
# ════════════════════════════════════════════════════════════
def page_dashboard_organization(lang):
    body = f"""
{page_hero("ダッシュボード", "組織 ─ 部門ごとに、プロジェクトを見える化。", "部門ツリーを登録してプロジェクトを割り当てると、部門単位での進捗把握やスペース横断の絞り込みに使えます。組織データはブラウザだけに保存され、外部には送信されません。", "組織（部門管理）")}
<section>
  <div class="wrap">
    {showcase("14_admin_org.jpg", "組織タブのスクリーンショット", [
        ("親子関係を自由に設定できる部門ツリー","親部門を選んで名前を入力するだけで、何階層でも部門を追加。表示順の並び替え・折りたたみ・削除にも対応"),
        ("一覧表示とグラフィカルな組織図を切り替え","箱＋接続線で部門構成を可視化する組織図モードも搭載"),
        ("プロジェクトを部門に割り当てて分析","データ管理タブのプルダウンから部門を割り当てるだけで、部門別プロジェクト分析やスペース横断の部門フィルターで活用できる"),
        ("配下の部門もまとめて集計","部門を選ぶと、その部門と子・孫部門のプロジェクトをまとめて進捗率・遅延工数などを集計"),
        ("組織データはブラウザにローカル保存","Backlog側やアカウント間で同期されないため、安心して社内の組織構成をそのまま登録できる。エクスポート／インポートで他のPCへの持ち出しも可能"),
    ])}
    <div class="mt">{cta_band("部門ごとの進捗を、迷わず把握。", "組織ツリーを作れば、あとはプロジェクトを紐づけるだけ。部門別の状況がいつでも一目で分かります。", secondary=("dashboard-cross-space.html","スペース横断サマリーを見る"))}</div>
  </div>
</section>
"""
    write_page(lang, "dashboard-organization.html", "組織（部門管理）",
               "部門ツリーを登録し、プロジェクトを部門に割り当てて部門単位で進捗を分析できる管理者機能。組織データはブラウザにローカル保存され外部に送信されません。",
               body, "assets/img/14_admin_org.jpg")


# ════════════════════════════════════════════════════════════
# 16. game.html ── Backlog Quest
# ════════════════════════════════════════════════════════════
def page_game(lang):
    body = f"""
{page_hero("🎮 Backlog Quest（ログクエ）", "Backlogを使うほど、キャラクターが育っていく。", "日々のタスク処理が、そのまま経験値になる実績連動RPG。正式リリース済み・デフォルトON。不要な場合はオプション画面からいつでもオフに切替できます。", "Backlog Quest")}
<section>
  <div class="wrap">
    {feature_grid([
        ("⚔️","8つの職業から選択","戦士・魔法使い・武道家・アイドル・歌手・俳優・サッカー選手・野球選手"),
        ("⬆️","レベルアップ＆称号","ログイン・タスク完了・コメントで経験値を獲得。10Lvごとに称号が進化。相棒のペットも一緒にレベルアップ"),
        ("🛡️","装備でアバターが変化","武器・防具・兜・盾を全11〜12段階で収集。装備すると見た目にも即反映"),
        ("🐲","ボス戦・隠しボス","10Lvごとにボスが出現。条件達成で隠しボスも姿を現す"),
    ], cols=4)}
    <div class="mt">
    {showcase("13_game.jpg", "Backlog Questのスクリーンショット", [
        ("リアルな行動がそのまま経験値に","ログイン継続・タスク作成／編集／完了・コメント投稿や感謝コメントで経験値とゴールドを獲得"),
        ("レベルアップで称号とステータスが成長","攻撃力・守備力・素早さ・HPの4ステータスをレーダーチャートで表示。称号は10Lvごとに進化"),
        ("装備を集めてアバターの見た目を変える","武器・防具・兜・盾を全11〜12段階で収集。ショップで購入し装備すると即アバターに反映"),
        ("ボス戦・隠しボス・実績・デイリークエスト","10Lvごとのボス戦はアニメーション演出付き。隠しボスや実績バッジ、日替わりクエストも用意"),
        ("進化する相棒ペット","レベルとともに進化する相棒ペットが同伴。名前付けや見た目の切り替えも可能"),
    ])}
    </div>
    <div class="mt">{cta_band("タスク処理を、冒険に変えよう。", "ログイン・タスク完了・コメント投稿がそのまま経験値に。いつも通り使うだけでキャラクターが育ちます。", secondary=("use-cases.html","活用シーンを見る"))}</div>
  </div>
</section>
"""
    write_page(lang, "game.html", "Backlog Quest（ログクエ）",
               "Backlogの利用状況に応じてXP・ゴールドを獲得しレベルアップする実績連動RPG。8職業・装備収集・ボス戦・進化するペットを搭載。",
               body, "assets/img/13_game.jpg")


# ════════════════════════════════════════════════════════════
# 17. use-cases.html ── 活用シーン
# ════════════════════════════════════════════════════════════
def page_use_cases(lang):
    scenarios = [
        ("📋", "リスト活用術", "朝の確認を1分に",
         "複数プロジェクトに散らばった自分の担当タスクを、毎朝Backlogで1件ずつ開いて確認するのに10分以上かかっていませんか？どれから手をつけるべきかもすぐには分かりません。",
         [("開くだけで期限別に自動整列","期限切れ・本日・1週間以内…とグループ分け済みの状態で表示される"),
          ("クイックフィルター＋検索で今やる分だけ","ワンクリックの絞り込みチップと全文検索で対象を一瞬で絞れる")],
         "朝の確認作業が1分以内に短縮。見落としもゼロになる。"),
        ("📅", "カレンダー活用術", "締切ラッシュを先読み",
         "月末になって「あ、この案件も今週締切だった…」と慌てた経験はありませんか？個別のタスク一覧だけでは、月単位の締切の偏りに気づきにくいものです。",
         [("月カレンダーで締切を可視化","今月・来月のタスクが期限日のマスに並び、締切の偏りが一目で分かる"),
          ("危険度は色で自動表示","期限切れ=赤、本日期限=橙。7週間ローリング表示で先週分も一緒に見える")],
         "締切の偏りに早めに気づき、前倒しで余裕を持って着手できる。"),
        ("⊞", "マトリックス活用術", "優先順位に迷わない",
         "担当タスクが20件、30件と積み上がると、結局どれから手をつければいいのか分からなくなり、目についたものから片付けて重要な仕事を後回しにしがちです。",
         [("緊急度×重要度で自動配置","マトリックスビューを開くだけで4象限に自動でプロットされる"),
          ("右上の象限から順に着手","象限をクリックすればその優先度のタスクだけ右パネルに一覧表示")],
         "優先順位で迷う時間がゼロに。重要タスクの後回しも防げる。"),
        ("🌳", "ガント活用術", "スケジュール調整をその場で",
         "複数人が関わる案件で、誰かのタスクが遅れたときに他のタスクへどう影響するか分からず、スケジュール調整の会議が長引いてしまう。",
         [("バーをドラッグして期限変更","開始日・期限日を直接ドラッグでき、Backlogへ即反映される"),
          ("後続タスクへ自動で日程シフト提案","依存関係のある後続タスクの日程も確認のうえ自動移動。カミナリ線で遅れも一目")],
         "スケジュール調整がガント画面だけでその場に完結する。"),
        ("🗂", "カンバン活用術", "朝会が5分で終わる",
         "朝会で「〇〇さん、進捗どうですか」と一人ずつ聞いていくと、それだけで会議時間の大半を使ってしまう。",
         [("画面共有するだけで全員の状況が一目","未対応・処理中・処理済み・完了の列でチーム全体の進捗が可視化される"),
          ("ステータス変更もその場でD&D","カードをドラッグして移動するだけでBacklogへ即反映され、報告の手間も省ける")],
         "一人ずつ聞き取る必要がなくなり、朝会が5分で終わる。"),
        ("👑", "ダッシュボード活用術", "週次報告が数分で完了",
         "プロジェクトリーダーとして、週次報告のために各プロジェクトの進捗・遅延状況を1つずつ手作業で集計するのが毎週の負担になっていませんか？",
         [("スペース横断サマリーで全プロジェクトを俯瞰","健全性スコア・完了率・遅延hが自動集計され、横並びで比較できる"),
          ("危険プロジェクトは色で自動検出","遅延率50%以上=🔴、20%以上=🟡のフラグで着手すべきプロジェクトが一目")],
         "週次報告の準備が数分で完了し、危険プロジェクトに早期着手できる。"),
        ("🎮", "Backlog Quest活用術", "タスク処理が楽しみに変わる",
         "タスク処理はどうしても義務的になりがちで、地道な作業を続けるモチベーションが続かなくなってしまうことがあります。",
         [("いつも通り使うだけで経験値に","ログイン・タスク作成／編集／完了・コメント投稿が、そのままキャラクターの経験値になる"),
          ("ボス戦や実績解除がちょっとした息抜きに","10Lvごとのボス戦、装備収集、隠しボス・実績バッジが日々の作業に区切りを作る")],
         "タスク処理そのものが楽しみに変わり、継続利用のモチベーションが上がる。"),
    ]
    cards = "".join(scenario(em, "活用シーン", title, scene, howto, result) for em, title, _s, scene, howto, result in
                     [(s[0], s[1], s[2], s[3], s[4], s[5]) for s in scenarios])
    body = f"""
{page_hero("活用シーン", "こんな使い方で、もっと便利に。", "機能を知っているだけでは終わらせない。「よくあるシーン」→「こう使う」→「効果」の3ステップで、現場でそのまま使える活用術を紹介します。", "活用シーン")}
<section>
  <div class="wrap" style="max-width:880px">
    {cards}
    <div class="mt">{cta_band("あなたの毎日にも、当てはめてみませんか。", "使い方を知るほど、Backlog My Tasksはもっと便利になります。", secondary=("get-started.html","導入方法を見る"))}</div>
  </div>
</section>
"""
    write_page(lang, "use-cases.html", "活用シーン",
               "リスト・カレンダー・マトリックス・ガント・カンバン・ダッシュボード・Backlog Questの現場で使える活用術を、シーン→使い方→効果の3ステップで紹介。",
               body, "assets/img/04_summary.jpg")


# ════════════════════════════════════════════════════════════
# 18. security-i18n.html
# ════════════════════════════════════════════════════════════
def page_security_i18n(lang):
    body = f"""
{page_hero("多言語・セキュリティ", "世界中で、安心して使える。", "5言語に完全対応。プライバシー・ファーストの設計で、大切なAPIキーもしっかり守ります。", "多言語・セキュリティ")}
<section>
  <div class="wrap">
    {section_head("🌏 5言語に完全対応", "ブラウザのロケールを自動検出して表示を切り替え", "設定から手動での言語変更も可能です。")}
    {lang_grid()}
  </div>
</section>
<section class="tint">
  <div class="wrap">
    {section_head("🔒 プライバシー・ファースト", "APIキーも操作データも、あなたの端末の外には出ません。")}
    {feature_grid([
        ("🔒","APIキーはAES-256-GCMで暗号化","ローカルに暗号化して保存。平文では持たない"),
        ("💻","データは端末内で完結","Backlog以外の外部サーバーへ一切送信しない"),
        ("🚫","トラッキングなし","アナリティクス・広告・追跡サービスは不使用"),
        ("📦","リモートコードを実行しない","全コードがパッケージ同梱。ストア審査済み"),
    ], cols=4)}
    <div class="mt">{cta_band("安心して、毎日使えるツールを。", "個人情報も業務データも、あなたとBacklogの間だけで完結します。", secondary=("feature-map.html","全機能マップを見る"))}</div>
  </div>
</section>
"""
    write_page(lang, "security-i18n.html", "多言語・セキュリティ",
               "日本語・英語・韓国語・繁体字中国語（台湾・香港）の5言語対応。APIキーはAES-256-GCM暗号化、外部送信なし、トラッキングなし。",
               body, "assets/img/09_admin_project.jpg")


# ════════════════════════════════════════════════════════════
# 19. feature-map.html
# ════════════════════════════════════════════════════════════
def page_feature_map(lang):
    cats = [
        ("📊", "表示ビュー（7）", ["リスト / カレンダー", "マトリックス / ガント", "カンバン / サマリー", "バーンダウン（タブ切替で全て自動更新）"]),
        ("✏️", "タスク操作", ["状態・担当者・期限変更", "クイック編集 / 一括操作", "右クリックメニュー / 複製", "ピン留め / スヌーズ / メモ"]),
        ("⏱", "計測・通知・検知", ["タイムトラッキング", "新着コメント自動検知", "期限デスクトップ通知", "Slack / Teams 連携 / バッジ"]),
        ("🔍", "検索・フィルター", ["件名・キー全文検索", "スペース / PJ / 担当者", "クイックフィルターチップ", "フィルタープリセット"]),
        ("👑", "ダッシュボード", ["データ管理", "プロジェクト別ダッシュボード", "スペース横断サマリー", "ユーザ棚卸（管理者専用）"]),
        ("⚙️", "基盤・全体設定", ["5言語対応 / ダークモード", "処理済みも完了扱いトグル", "オフライン対応（自動再送）", "APIキー AES-256 暗号化"]),
        ("🎮", "Backlog Quest", ["8職業・レベルアップ", "装備収集・アバター反映", "ボス戦・隠しボス", "ペット育成・実績"]),
    ]
    cards = "".join(map_card(em, title, items) for em, title, items in cats)
    body = f"""
{page_hero("全機能マップ", "これ1つで、完結する。", "表示ビューからBacklog Questまで、Backlog My Tasksの全機能を一覧にまとめました。", "全機能マップ")}
<section>
  <div class="wrap">
    <div class="grid grid-3">{cards}</div>
    <div class="mt">{cta_band("全部、無理なく使いこなせます。", "使う機能から少しずつ。気づけば毎日の相棒になっています。", secondary=("get-started.html","導入方法を見る"))}</div>
  </div>
</section>
"""
    write_page(lang, "feature-map.html", "全機能マップ",
               "表示ビュー・タスク操作・計測通知検知・検索フィルター・ダッシュボード・基盤設定・Backlog Questの全機能を一覧で紹介。",
               body, "assets/img/04_summary.jpg")


# ════════════════════════════════════════════════════════════
# 20. get-started.html ── 導入方法 + 最終CTA
# ════════════════════════════════════════════════════════════
def page_get_started(lang):
    body = f"""
{page_hero("導入方法", "導入はカンタン、3ステップ。", "インストールしてから使い始めるまで、数分もかかりません。", "導入方法")}
<section>
  <div class="wrap">
    {steps([
        ("ストアから追加", 'Chrome ウェブストアの「Backlog My Tasks」ページを開いて「Chromeに追加」'),
        ("スペースURLとAPIキー", "拡張機能アイコンを右クリック → オプション → スペースURLとAPIキーを入力（最大10スペース登録可）"),
        ("アイコンをクリック！", "ツールバーのアイコンをクリック → 自分のタスクが一覧表示、すぐ使えます"),
    ])}
    <p class="center mt" style="font-size:14px;color:var(--sub)">{_("💡 APIキーの取得：Backlog → 個人設定 → API → 「登録」ボタンで発行")}</p>
  </div>
</section>
<section class="dark">
  <div class="wrap">
    {cta_band(
        "さあ、今日から使ってみよう！",
        "Backlogを開く回数が、きっと減ります。タスク管理も、チームの進捗把握も、これ1つで。まずはインストールして、毎日の相棒にしてください。",
        secondary=("use-cases.html", "活用シーンを見る"),
    )}
  </div>
</section>
"""
    write_page(lang, "get-started.html", "導入方法",
               "Chromeウェブストアから追加してスペースURLとAPIキーを入力するだけ。3ステップで今日からBacklog My Tasksが使えます。",
               body, "assets/img/01_list.jpg")


# ════════════════════════════════════════════════════════════
# ビルド実行
# ════════════════════════════════════════════════════════════
PAGE_FUNCS = [
    page_index, page_views, page_view_list, page_view_matrix, page_view_kanban,
    page_view_gantt, page_view_calendar, page_reports, page_daily_features,
    page_speed_features, page_task_creation, page_dashboard, page_dashboard_project,
    page_dashboard_gantt, page_dashboard_cross_space, page_dashboard_organization, page_game, page_use_cases,
    page_security_i18n, page_feature_map, page_get_started,
]


def main():
    global CURRENT_LANG, CURRENT_ASSET_PREFIX

    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)
    shutil.copytree(ASSETS_SRC, os.path.join(DIST, "assets"))
    open(os.path.join(DIST, ".nojekyll"), "w").close()

    for lang in LANGS:
        CURRENT_LANG = lang
        CURRENT_ASSET_PREFIX = "" if not LANG_INFO[lang]["dir"] else "../"
        for fn in PAGE_FUNCS:
            fn(lang)

    print(f"\nTOTAL PAGES: {len(PAGE_META)} x {len(LANGS)} languages = {len(PAGE_META) * len(LANGS)} files")

    # 翻訳の棚卸し：TRに存在しない原文（＝いずれかの非ja言語で日本語のままフォールバックした文言）を警告表示
    if MISSING:
        by_lang = {}
        for lang, text in MISSING:
            by_lang.setdefault(lang, set()).add(text)
        print(f"\n[WARN] 未翻訳（日本語へフォールバック）が {len(MISSING)} 件あります:")
        for lang in sorted(by_lang):
            print(f"  {lang}: {len(by_lang[lang])} 件")
    else:
        print("\n[OK] 全言語で未翻訳フォールバックはありません")

    # 翻訳対象文言の棚卸し出力（翻訳データ作成・更新時に参照する）
    strings_path = os.path.join(HERE, "i18n", "source_strings.json")
    with open(strings_path, "w", encoding="utf-8") as f:
        json.dump(sorted(ALL_STRINGS), f, ensure_ascii=False, indent=2)
    print(f"[INFO] 翻訳対象文言一覧を書き出しました: {strings_path} ({len(ALL_STRINGS)}件)")


if __name__ == "__main__":
    main()
