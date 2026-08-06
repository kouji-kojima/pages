#!/usr/bin/env python3
"""4つの言語別翻訳ファイル（tr_en.json/tr_ko.json/tr_zh_TW.json/tr_zh_HK.json、
{原文: 訳文} の単純なマッピング）を、build_site.py が読み込む
translations.json（{原文: {en:..., ko:..., zh_TW:..., zh_HK:...}}）へマージする。
source_strings.json（build_site.py実行時に自動生成される全原文リスト）に対して、
各言語ファイルにキー欠落・余剰が無いかも検証する。
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(HERE, "source_strings.json")
OUT_PATH = os.path.join(HERE, "translations.json")
LANG_FILES = {
    "en": "tr_en.json",
    "ko": "tr_ko.json",
    "zh_TW": "tr_zh_TW.json",
    "zh_HK": "tr_zh_HK.json",
}

def main():
    with open(SRC_PATH, encoding="utf-8") as f:
        source_strings = set(json.load(f))
    print(f"source strings: {len(source_strings)}")

    # 4言語すべて揃うのを待たず、翻訳が届いた言語から順にtranslations.jsonへ反映できるよう、
    # ファイルが無い言語はエラーにせず単にスキップする（その言語はbuild_site.py側で日本語へ
    # フォールバックしたまま）。届いているファイルの中身（キー欠落・空値）はこれまでどおり厳格に検証する
    per_lang = {}
    ok = True
    for lang, fname in LANG_FILES.items():
        path = os.path.join(HERE, fname)
        if not os.path.exists(path):
            print(f"[SKIP] {fname} が未生成のためスキップ（日本語へフォールバック）")
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        per_lang[lang] = data
        keys = set(data.keys())
        missing = source_strings - keys
        extra = keys - source_strings
        empty = [k for k, v in data.items() if not v or not v.strip()]
        print(f"{lang}: {len(data)} keys, missing={len(missing)}, extra={len(extra)}, empty_values={len(empty)}")
        if missing:
            print(f"  missing sample: {list(missing)[:5]}")
            ok = False
        if empty:
            print(f"  empty sample: {empty[:5]}")
            ok = False

    if not ok:
        print("\n[FAIL] 検証エラーがあります。マージを中止しました。translations.jsonは更新していません。")
        sys.exit(1)

    merged = {}
    for text in source_strings:
        merged[text] = {}
        for lang in LANG_FILES:
            if text in per_lang.get(lang, {}):
                merged[text][lang] = per_lang[lang][text]

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2, sort_keys=True)
    print(f"\n[OK] {OUT_PATH} に{len(merged)}件をマージしました")

if __name__ == "__main__":
    main()
