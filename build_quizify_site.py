"""@quizify_english の復習ページ(docs/quizify/)を作る。投稿済みの回だけを載せる(答えを先に見せない)。

    .venv-tts/bin/python build_quizify_site.py          # 予約した全回のデータ(quizify_site_data.json)と音声をそろえて、ページを作る(Mac で)
    python3 build_quizify_site.py --pages               # ページだけ作り直す(投稿のたびに GitHub Actions が実行)

音声は動画を作ったときの ElevenLabs の声(out/voice_cache)をそのままコピーするので、クレジットは使わない。
"""
import hashlib
import html
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "quizify_site_data.json"
SITE = ROOT / "docs" / "quizify"
AUDIO = SITE / "audio"
POSTED = ROOT / "quizify_posted.json"
e = html.escape


def cached(vid, text, speed):
    """動画を作ったときの音声ファイル(なければ None)。"""
    p = ROOT / "out" / "voice_cache" / f"{vid}_{hashlib.sha1(f'{text}|{speed}'.encode()).hexdigest()[:12]}.mp3"
    if not p.exists():
        return None
    AUDIO.mkdir(parents=True, exist_ok=True)
    shutil.copy(p, AUDIO / p.name)
    return f"audio/{p.name}"


def collect():
    import quizify_black as qb
    import quizify_listening as ql
    import quizify_white as qw
    data = {}
    for kind, mod in (("black", qb), ("white", qw)):
        for r in mod.REELS:
            key = f"{kind}_{r['items'][0][0]}"
            data[key] = [dict(no=no, word=w, mean=m, ja=ja, en=en, tips=tips,
                              word_audio=cached(qb.EN_VOICE, w, qb.EN_SPEED), en_audio=cached(qb.EN_VOICE, en, qb.EN_SPEED))
                         for no, w, m, _, ja, en, tips in r["items"]]
    for r in ql.REELS:
        key = f"listening_{r['items'][0][0]}"
        data[key] = []
        for k, (no, vid, en, a, b, ans, words) in enumerate(r["items"]):
            v = ql.voice_for(no, k)
            data[key].append(dict(no=no, en=en, a=a, b=b, ans=ans, words=words, accent=f"{v[2]} {v[3]}",
                                  audio=cached(vid or v[0], en, ql.SPEED)))
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")


def play(src, label="▶ 聞く"):
    return f'<button class="play" data-src="{e(src)}">{label}</button>' if src else ""


def word_card(it, kind):
    tips = "".join(f"<li>{e(t)}</li>" for t in it["tips"])
    return (f'<li class="card"><p class="no">{it["no"]}</p><p class="w">{e(it["word"])} {play(it["word_audio"], "▶")}</p>'
            f'<p class="m">{e(it["mean"])}</p><p class="ja">{e(it["ja"])}</p>'
            f'<button class="reveal">英語で言えたら、答えを見る</button>'
            f'<div class="ans"><p class="en">{e(it["en"])}</p>{play(it["en_audio"])}<ul class="tips">{tips}</ul></div></li>')


def listen_card(it):
    words = "".join(f"<li>{e(w)}</li>" for w in it["words"])
    return (f'<li class="card" data-ans="{it["ans"]}"><p class="no">{it["no"]} <span>{e(it["accent"])}</span></p>'
            f'{play(it["audio"], "▶ 1回だけ聞いてみる")}'
            f'<button class="opt" data-c="A">A) {e(it["a"])}</button><button class="opt" data-c="B">B) {e(it["b"])}</button>'
            f'<div class="ans"><p class="res"></p><p class="en">{e(it["en"])}</p><ul class="tips">{words}</ul></div></li>')


TABS = [("listening", "🎧 リスニング", "TOEIC Part 2〜4 風。音声を聞いて、正しい訳を選ぼう"),
        ("white", "📗 英単語(初級)", "受験・英検で問われるコロケーション。日本語を見て英語で言ってみよう"),
        ("black", "📕 瞬間英作文", "英検準1級の単語。日本語を見て、すぐ英語にしてみよう")]


def pages():
    data = json.loads(DATA.read_text())
    posted = json.loads(POSTED.read_text()) if POSTED.exists() else {}
    keys = sorted((k for k in posted if k in data), key=lambda k: posted[k]["posted_at"], reverse=True)
    secs, nav = [], []
    for kind, label, note in TABS:
        cards = "".join(listen_card(it) if kind == "listening" else word_card(it, kind)
                        for k in keys if k.startswith(kind) for it in data[k])
        nav.append(f'<button data-t="{kind}">{label}</button>')
        secs.append(f'<section id="{kind}"><p class="note">{note}</p><ol>{cards or "<li class=empty>近日公開</li>"}</ol></section>')
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "index.html").write_text(TEMPLATE.replace("{{nav}}", "".join(nav)).replace("{{secs}}", "".join(secs)))
    print(f"✓ quizify の復習ページ({len(keys)} 本分)")


TEMPLATE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>quizify_english 復習ページ|リスニング・英単語・瞬間英作文</title>
<meta name="description" content="Instagram @quizify_english の問題を、音声つきでもう一度。TOEIC風リスニング、受験・英検のコロケーション、英検準1級の瞬間英作文。">
<link rel="canonical" href="https://eng-navi.github.io/quizify/">
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:wght@500;600&family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #f5f3ef; background-image: linear-gradient(#dedcd7 1px, transparent 1px), linear-gradient(90deg, #dedcd7 1px, transparent 1px); background-size: 27px 27px; color: #282828; font-family: "Noto Sans JP", sans-serif; }
  main { max-width: 560px; margin: 0 auto; padding: 28px 16px 48px; }
  .crumb { font-size: 12px; color: #888; } .crumb a { color: inherit; }
  h1 { font-size: 22px; line-height: 1.5; margin-top: 16px; }
  .lead { margin-top: 8px; font-size: 14px; color: #666; line-height: 1.8; }
  nav { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px; margin-top: 18px; background: #fff; border-radius: 12px; padding: 4px; box-shadow: 0 1px 4px rgba(0,0,0,.06); }
  nav button { border: 0; background: none; padding: 10px 2px; border-radius: 9px; font-size: 13px; font-weight: 500; color: #666; cursor: pointer; }
  nav button[aria-pressed="true"] { background: #282828; color: #fff; }
  section { display: none; } section.on { display: block; }
  .note { margin-top: 12px; font-size: 13px; color: #777; }
  ol { list-style: none; margin-top: 12px; display: grid; gap: 12px; }
  .card { background: #fff; border-radius: 14px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.05); }
  .no { font-family: "EB Garamond", serif; font-style: italic; color: #999; font-size: 15px; } .no span { font-style: normal; font-family: system-ui; font-size: 12px; margin-left: 6px; }
  .w { font-family: "EB Garamond", serif; font-weight: 600; font-size: 26px; margin-top: 2px; }
  .m { color: #c83430; font-size: 14px; margin-top: 2px; }
  .ja { font-size: 15px; margin-top: 10px; line-height: 1.7; }
  .en { font-family: "EB Garamond", serif; font-size: 20px; line-height: 1.5; margin-top: 10px; }
  .tips { margin-top: 10px; padding-left: 1.2em; font-size: 13px; color: #555; line-height: 1.8; }
  .play { border: 0; background: #282828; color: #fff; border-radius: 999px; padding: 7px 14px; font-size: 13px; cursor: pointer; margin-top: 8px; vertical-align: middle; }
  .w .play { margin: 0 0 0 6px; padding: 4px 10px; font-size: 12px; }
  .reveal { margin-top: 12px; border: 1px solid #c83430; background: #fff; color: #c83430; border-radius: 999px; padding: 8px 16px; font-size: 13px; cursor: pointer; }
  .ans { display: none; } .card.open .ans { display: block; } .card.open .reveal { display: none; }
  .opt { display: block; width: 100%; text-align: left; margin-top: 10px; border: 1px solid #ddd; background: #fafaf8; border-radius: 12px; padding: 12px; font-size: 14px; line-height: 1.6; cursor: pointer; color: #282828; }
  .opt.ok { border-color: #2e8b57; background: #eef8f1; } .opt.ng { border-color: #c83430; background: #fdf0ef; }
  .res { margin-top: 12px; font-weight: 700; }
  .empty { color: #999; font-size: 14px; text-align: center; padding: 20px; }
  .cta { display: block; margin-top: 22px; padding: 14px; border-radius: 14px; background: #282828; color: #fff; text-align: center; text-decoration: none; font-weight: 500; }
  .foot { margin-top: 26px; font-size: 10px; color: #aaa; text-align: center; } .foot a { color: inherit; }
</style>
</head>
<body>
<main>
  <p class="crumb"><a href="/">eng_navi 英語クイズ</a> › quizify_english 復習</p>
  <h1>Instagram の問題を、音声つきでもう一度</h1>
  <p class="lead">@quizify_english に投稿した問題をまとめています。新しい順に並んでいます。</p>
  <nav>{{nav}}</nav>
  {{secs}}
  <a class="cta" href="https://www.instagram.com/quizify_english/">Instagram で毎日の問題を見る →</a>
  <p class="foot"><a href="/">eng_navi 英語クイズ</a></p>
</main>
<script>
const tabs = document.querySelectorAll("nav button"), secs = document.querySelectorAll("section");
const show = (t) => { tabs.forEach((b) => b.setAttribute("aria-pressed", b.dataset.t === t)); secs.forEach((s) => s.classList.toggle("on", s.id === t)); try { localStorage.setItem("qz-tab", t); } catch (e) {} };
tabs.forEach((b) => (b.onclick = () => show(b.dataset.t)));
let start = "listening"; try { start = localStorage.getItem("qz-tab") || start; } catch (e) {}
show(location.hash.slice(1) || start);
const audio = new Audio();
document.querySelectorAll(".play").forEach((b) => (b.onclick = () => { audio.src = b.dataset.src; audio.play(); }));
document.querySelectorAll(".reveal").forEach((b) => (b.onclick = () => b.closest(".card").classList.add("open")));
document.querySelectorAll(".opt").forEach((b) => (b.onclick = () => {
  const card = b.closest(".card"), ans = card.dataset.ans;
  if (card.classList.contains("open")) return;
  card.querySelectorAll(".opt").forEach((o) => o.classList.add(o.dataset.c === ans ? "ok" : "ng"));
  card.querySelector(".res").textContent = b.dataset.c === ans ? "⭕ 正解!" : `❌ 正解は ${ans}`;
  card.classList.add("open");
}));
</script>
</body>
</html>
"""

if __name__ == "__main__":
    if "--pages" not in sys.argv:
        collect()
    pages()
