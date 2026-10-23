"""quizzes.json からクイズページ用のデータ (docs/data.js) を書き出す。

使い方:
    python3 build_site.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "docs"
FIELDS = ["no", "category", "question", "options", "answer", "translation", "explanation"]


def main():
    quizzes = sorted(json.loads((ROOT / "quizzes.json").read_text()), key=lambda q: q["no"])
    # まだ Instagram に出していない問題の答えがサイトで先に見えないよう、投稿済みの番号までに絞る
    log = ROOT / "posted.json"
    if log.exists():
        latest = max(p["no"] for p in json.loads(log.read_text()))
        quizzes = [q for q in quizzes if q["no"] <= latest]
    data = []
    for q in quizzes:
        if "options" not in q:
            continue  # ピンク(イディオム紹介)はクイズではないので載せない
        item = {k: q[k] for k in FIELDS if k in q}
        # tts.py で作った音声があれば使う
        if (SITE / "audio" / f"q{q['no']}.mp3").exists():
            item["audio"] = f"audio/q{q['no']}.mp3"
        data.append(item)
    out = SITE / "data.js"
    out.write_text("window.QUIZZES = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n")
    voiced = sum(1 for d in data if "audio" in d)
    print(f"✓ {out}({len(data)}問、うち音声あり {voiced}問)")


if __name__ == "__main__":
    main()
