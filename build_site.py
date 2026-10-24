"""quizzes.json からクイズページ用のデータ (docs/data.js) を書き出す。

使い方:
    python3 build_site.py
"""
import json
from pathlib import Path

import build_pages

ROOT = Path(__file__).parent
SITE = ROOT / "docs"
FIELDS = ["no", "category", "question", "options", "answer", "text", "target", "glossary", "translation", "explanation", "permalink"]


def main():
    quizzes = sorted(json.loads((ROOT / "quizzes.json").read_text()), key=lambda q: q["no"])
    # まだ Instagram に出していない問題の答えがサイトで先に見えないよう、投稿済みの番号までに絞る
    log = ROOT / "posted.json"
    if log.exists():
        latest = max(p["no"] for p in json.loads(log.read_text()))
        quizzes = [q for q in quizzes if q["no"] <= latest]
    data = []
    for q in quizzes:
        item = {k: q[k] for k in FIELDS if k in q}
        # tts.py で作った音声があれば使う
        if (SITE / "audio" / f"q{q['no']}.mp3").exists():
            item["audio"] = f"audio/q{q['no']}.mp3"
        # 選べる声(us_f 以外は audio/<声>/q<no>.mp3)
        item["voices"] = ["us_f"] * ("audio" in item) + [v for v in ("us_m", "uk_f", "uk_m") if (SITE / "audio" / v / f"q{q['no']}.mp3").exists()]
        data.append(item)
    out = SITE / "data.js"
    out.write_text("window.QUIZZES = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n")
    voiced = sum(1 for d in data if "audio" in d)
    print(f"✓ {out}({len(data)}問、うち音声あり {voiced}問)")
    pages = build_pages.build(SITE, quizzes)
    print(f"✓ 問題ごとのページ {pages} 件、一覧ページ、sitemap.xml、robots.txt")


if __name__ == "__main__":
    main()
