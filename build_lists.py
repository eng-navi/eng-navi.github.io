"""Threads の「10選」に対応するサイトのページ(docs/list/<id>/)と、例文の音声を作る。

    .venv-tts/bin/python build_lists.py     # 音声(無い分だけ)とページを作る
    python3 build_lists.py --pages          # ページだけ作り直す(音声は作らない)
"""
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "docs"
SITE_URL = "https://eng-navi.github.io"
VOICES = {"us_f": "🇺🇸 女性", "us_m": "🇺🇸 男性", "uk_f": "🇬🇧 女性", "uk_m": "🇬🇧 男性"}


def e(s):
    return html.escape(str(s), quote=True)


def audio(list_id, n, voice):
    return SITE / "audio" / "list" / str(list_id) / voice / f"{n}.mp3"


def make_audio(lists):
    import tts
    engine = None
    for lst in lists:
        for n, (_, _, en, *_) in enumerate(lst["items"], 1):
            for v in VOICES:
                out = audio(lst["id"], n, v)
                if out.exists():
                    continue
                engine = engine or tts.Kokoro()
                engine(en, out, v)
    print("✓ 音声")


def page(lst):
    rows = ""
    for n, (phrase, ja, en, en_ja, *_) in enumerate(lst["items"], 1):
        rows += f"""
    <li>
      <p class="ph"><span class="n">{n:02d}</span>{e(phrase)}<small class="hide">{e(ja)}</small></p>
      <p class="ex">{e(en)}</p>
      <p class="ja hide">{e(en_ja)}</p>
      <div class="btns"><button class="reveal">意味を見る</button><button class="play" data-n="{n}">▶ 聞く</button></div>
    </li>"""
    b = lst.get("book")
    book = f"""
  <section class="book">
    <p class="bk-h">このフレーズをもっと覚えるなら <span>PR</span></p>
    <a href="{e(b['url'])}" target="_blank" rel="noopener sponsored nofollow"><b>{e(b['name'])}</b><small>{e(b['note'])}</small></a>
  </section>""" if b else ""
    voices = "".join(f'<button data-v="{k}">{v}</button>' for k, v in VOICES.items())
    title = f"{lst['title']}|音声つき|eng_navi"
    desc = "・".join(i[0] for i in lst["items"][:5]) + f" など{len(lst['items'])}の表現を、例文と音声(アメリカ・イギリス英語)で。"
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{SITE_URL}/list/{lst['id']}/">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{SITE_URL}/ogp.png">
<link href="https://fonts.googleapis.com/css2?family=Kalam:wght@700&family=EB+Garamond:wght@400;500&family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #f5f3ef; background-image: linear-gradient(#dedcd7 1px, transparent 1px), linear-gradient(90deg, #dedcd7 1px, transparent 1px); background-size: 27px 27px; color: #282828; font-family: "Noto Sans JP", system-ui, sans-serif; }}
  main {{ max-width: 560px; margin: 0 auto; padding: 28px 20px 48px; }}
  .crumb {{ font-size: 12px; color: #888; }} .crumb a {{ color: inherit; }}
  h1 {{ font-size: 23px; line-height: 1.5; margin-top: 18px; }}
  .lead {{ margin-top: 10px; font-size: 14px; color: #666; line-height: 1.8; }}
  .voices {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }}
  .voices button {{ border: 1px solid #ccc; background: #fff; border-radius: 999px; padding: 7px 13px; font-size: 13px; cursor: pointer; }}
  .voices button[aria-pressed="true"] {{ background: #c83430; border-color: #c83430; color: #fff; }}
  ol {{ list-style: none; margin-top: 20px; display: grid; gap: 12px; }}
  li {{ background: #fff; border-radius: 14px; padding: 16px 16px 14px; box-shadow: 0 2px 8px rgba(0,0,0,.05); }}
  .ph {{ font-family: "Kalam", cursive; font-size: 24px; display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 10px; }}
  .ph .n {{ font-family: system-ui; font-size: 12px; color: #c83430; font-weight: 700; }}
  .ph small {{ font-family: "Noto Sans JP"; font-size: 14px; color: #c83430; }}
  .ex {{ font-family: "EB Garamond", serif; font-size: 19px; margin-top: 8px; line-height: 1.5; }}
  .ja {{ font-size: 13px; color: #777; margin-top: 4px; }}
  .modes {{ display: grid; grid-template-columns: repeat(3, 1fr); margin-top: 18px; background: #fff; border-radius: 12px; padding: 4px; box-shadow: 0 1px 4px rgba(0,0,0,.06); }}
  .modes button {{ border: 0; background: none; padding: 9px 0; border-radius: 9px; font-size: 14px; font-weight: 500; color: #666; cursor: pointer; }}
  .modes button[aria-pressed="true"] {{ background: #282828; color: #fff; }}
  .mode-note {{ margin-top: 8px; font-size: 12px; color: #888; }}
  .btns {{ display: flex; gap: 8px; }}
  .reveal {{ display: none; margin-top: 10px; border: 1px solid #c83430; background: #fff; color: #c83430; border-radius: 999px; padding: 7px 16px; font-size: 13px; cursor: pointer; }}
  body.quiz li:not(.open) .hide {{ visibility: hidden; }}
  body.quiz li:not(.open) .reveal {{ display: inline-block; }}
  body.listen li.now {{ outline: 3px solid #c83430; }}
  .book {{ margin-top: 22px; background: #fff; border-radius: 14px; padding: 16px; }}
  .bk-h {{ font-size: 13px; font-weight: 700; color: #c83430; }} .bk-h span {{ float: right; font-size: 10px; color: #aaa; font-weight: 400; }}
  .book a {{ display: block; margin-top: 10px; padding: 12px 14px; border-radius: 12px; background: #f5f3ef; text-decoration: none; color: #282828; }}
  .book a b {{ display: block; font-size: 15px; }} .book a small {{ display: block; margin-top: 3px; font-size: 12px; color: #777; }}
  .play {{ margin-top: 10px; border: 0; background: #282828; color: #fff; border-radius: 999px; padding: 7px 16px; font-size: 13px; cursor: pointer; }}
  .all {{ display: block; width: 100%; margin-top: 18px; padding: 14px; border: 0; border-radius: 14px; background: #c83430; color: #fff; font-size: 15px; font-weight: 700; cursor: pointer; }}
  .cta {{ display: block; margin-top: 12px; padding: 14px; border-radius: 14px; background: #282828; color: #fff; text-align: center; text-decoration: none; font-weight: 500; }}
  .sub {{ display: block; margin-top: 10px; padding: 13px; border-radius: 14px; border: 1px solid #ccc; background: #fff; text-align: center; text-decoration: none; color: #555; font-size: 14px; }}
  .foot {{ margin-top: 26px; font-size: 10px; color: #aaa; text-align: center; line-height: 1.7; }} .foot a {{ color: inherit; }}
</style>
</head>
<body>
<main>
  <p class="crumb"><a href="/">eng_navi 英語クイズ</a> › フレーズ集 No.{lst['id']}</p>
  <h1>{e(lst['title'])}</h1>
  <p class="lead">Threads で紹介した表現を、例文と音声でまとめました。声を選んで、▶ で聞けます。</p>
  <div class="modes"><button data-m="list">一覧</button><button data-m="quiz">クイズ</button><button data-m="listen">聞き流し</button></div>
  <p class="mode-note" id="mode-note"></p>
  <div class="voices">{voices}</div>
  <ol>{rows}
  </ol>
  <button class="all" id="all">▶ {len(lst['items'])}個まとめて聞く</button>
  {book}
  <a class="cta" href="/">英文法クイズに挑戦する(無料・100問以上)</a>
  <a class="sub" href="https://www.threads.net/@eng_navi" target="_blank" rel="noopener">Threads で毎日1つ @eng_navi</a>
  <p class="foot">Instagram・Threads <a href="https://www.instagram.com/eng_navi/" target="_blank" rel="noopener">@eng_navi</a></p>
</main>
<script src="/recommend.js"></script>
<script>
  if (window.ANALYTICS_ID) {{
    const t = document.createElement("script"); t.async = true;
    t.src = "https://www.googletagmanager.com/gtag/js?id=" + window.ANALYTICS_ID; document.head.appendChild(t);
    window.dataLayer = window.dataLayer || []; window.gtag = function () {{ dataLayer.push(arguments); }};
    gtag("js", new Date()); gtag("config", window.ANALYTICS_ID);
  }}
  let voice = "us_f";
  try {{ voice = localStorage.getItem("voice") || "us_f"; }} catch (e) {{}}
  const btns = document.querySelectorAll("[data-v]");
  const mark = () => btns.forEach((b) => b.setAttribute("aria-pressed", b.dataset.v === voice));
  btns.forEach((b) => (b.onclick = () => {{ voice = b.dataset.v; try {{ localStorage.setItem("voice", voice); }} catch (e) {{}} mark(); }}));
  mark();
  let player = null, queue = [];
  const src = (n) => `/audio/list/{lst['id']}/${{voice}}/${{n}}.mp3`;
  function play(n, next) {{
    if (player) player.pause();
    player = new Audio(src(n));
    player.onended = () => next && next();
    player.play();
    if (window.gtag) gtag("event", "list_play", {{ list: {lst['id']}, n, voice }});
  }}
  document.querySelectorAll(".play").forEach((b) => (b.onclick = () => play(Number(b.dataset.n))));
  // モード:一覧(全部見える)/クイズ(意味を隠してタップで表示)/聞き流し(順番に再生して今の表現を目立たせる)
  const NOTES = {{ list: "意味と例文をまとめて確認できます。", quiz: "意味が隠れています。考えてから「意味を見る」で答え合わせ。", listen: "{len(lst['items'])}個を順番に再生します。画面を見ずに聞き流してもOK。" }};
  const cards = [...document.querySelectorAll("li")];
  document.querySelectorAll(".reveal").forEach((b, i) => (b.onclick = () => {{ cards[i].classList.add("open"); play(i + 1); }}));
  function setMode(m) {{
    document.body.className = m;
    cards.forEach((c) => c.classList.remove("open", "now"));
    document.querySelectorAll("[data-m]").forEach((b) => b.setAttribute("aria-pressed", b.dataset.m === m));
    document.getElementById("mode-note").textContent = NOTES[m];
    if (m === "listen") document.getElementById("all").click();
    else if (player) player.pause();
    if (window.gtag) gtag("event", "list_mode", {{ list: {lst['id']}, mode: m }});
  }}
  document.querySelectorAll("[data-m]").forEach((b) => (b.onclick = () => setMode(b.dataset.m)));
  document.body.className = "list";
  document.querySelectorAll("[data-m]").forEach((b) => b.setAttribute("aria-pressed", b.dataset.m === "list"));
  document.getElementById("mode-note").textContent = NOTES.list;
  document.getElementById("all").onclick = () => {{
    queue = {list(range(1, len(lst['items']) + 1))};
    const step = () => {{
      cards.forEach((c) => c.classList.remove("now"));
      const n = queue.shift();
      if (!n) return;
      cards[n - 1].classList.add("now");
      cards[n - 1].scrollIntoView({{ behavior: "smooth", block: "center" }});
      play(n, () => setTimeout(step, 600));
    }};
    step();
  }};
</script>
</body>
</html>
"""


def main():
    lists = json.loads((ROOT / "threads_lists.json").read_text())
    if "--pages" not in sys.argv:
        make_audio(lists)
    for lst in lists:
        d = SITE / "list" / str(lst["id"])
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(page(lst))
    # docs/list/ は最新の10選へ(ストーリーの「プロフィールのリンクから」の行き先)
    stories = ROOT / "stories.json"
    latest = max(int(x["key"].split("_")[0]) for x in json.loads(stories.read_text())) if stories.exists() else max(l["id"] for l in lists)
    items = "".join(f'<li><a href="{l["id"]}/">{e(l["title"])}</a></li>' for l in sorted(lists, key=lambda l: -l["id"]))
    (SITE / "list" / "index.html").write_text(f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>フレーズ10選|eng_navi</title>
<meta http-equiv="refresh" content="0; url={latest}/"><link rel="canonical" href="{SITE_URL}/list/{latest}/"></head>
<body><p>最新の10選へ移動します…</p><ul>{items}</ul></body></html>""")
    print(f"✓ 10選のページ {len(lists)} 件")


if __name__ == "__main__":
    main()
