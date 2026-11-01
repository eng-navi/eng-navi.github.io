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
    return f'<button class="play" data-src="/quizify/{e(src)}">{label}</button>' if src else ""


def word_card(it, kind):
    tips = "".join(f"<li>{e(t)}</li>" for t in it.get("tips", []))
    head = (f'<li class="card"><p class="no">{it.get("no", "")}</p><p class="w">{e(it["word"])} {play(it.get("word_audio"), "▶")}</p>'
            f'<p class="m">{e(it.get("mean", ""))}</p>')
    if not it.get("en"):  # 例文のない回(2023年の単語リスト)
        return head + "</li>"
    return (head + f'<p class="ja">{e(it.get("ja", ""))}</p><button class="reveal">英語で言えたら、答えを見る</button>'
            f'<div class="ans"><p class="en">{e(it["en"])}</p>{play(it.get("en_audio"))}<ul class="tips">{tips}</ul></div></li>')


def listen_card(it):
    words = "".join(f"<li>{e(w)}</li>" for w in it["words"])
    return (f'<li class="card" data-ans="{it["ans"]}"><p class="no">{it["no"]} <span>{e(it.get("accent", ""))}</span></p>'
            f'{play(it["audio"], "▶ 1回だけ聞いてみる")}'
            f'<button class="opt" data-c="A">A) {e(it["a"])}</button><button class="opt" data-c="B">B) {e(it["b"])}</button>'
            f'<div class="ans"><p class="res"></p><p class="en">{e(it["en"])}</p><ul class="tips">{words}</ul></div></li>')


# 色ごとのページ。対象のレベルをはっきり書く(見る人にも検索にもわかりやすく)
PAGES = {
    "listening": dict(path="listening", icon="🎧", name="英語リスニング問題",
                      title="英語リスニング問題|TOEIC Part 3・4/英検準1級・2級|音声つき",
                      desc="TOEIC Part 3・4、英検準1級〜2級レベルのリスニング問題を音声つきで。1回だけ聞いて、正しい訳を選ぶ2択クイズ。TOEIC 800〜900点を目指す人に。",
                      h1="英語リスニング問題(TOEIC Part 3・4/英検準1級〜2級)",
                      lead="TOEIC で差がつく Part 3・4(会話・説明文)と、英検準1級〜2級レベルのリスニング。音声を1回だけ聞いて、正しい訳を選ぼう。TOEIC 800〜900点を目指す人におすすめです。"),
    "white": dict(path="tango", icon="📗", name="英単語・熟語(英検3級〜2級)",
                  title="英単語・熟語クイズ|英検3級〜2級・大学受験|例文と音声つき",
                  desc="英検3級〜2級・大学受験でよく問われる英単語と熟語(コロケーション)を、例文と音声で。日本語を見て英語で言えるか、瞬間英作文で確認。",
                  h1="英単語・熟語(英検3級〜2級・大学受験)",
                  lead="英検3級〜2級・大学受験でよく問われる、前置詞までセットの熟語や基本の単語。日本語の例文を見て、英語で言えたら答えを見よう。"),
    "black": dict(path="tango-advanced", icon="📕", name="瞬間英作文(英検2級〜準1級)",
                  title="瞬間英作文|英検2級〜準1級・TOEIC高得点の英単語|例文と音声つき",
                  desc="英検2級〜準1級、TOEIC 800点以上を目指す人向けの英単語を、瞬間英作文で。日本語の例文をすぐ英語にして、音声で答え合わせ。",
                  h1="瞬間英作文(英検2級〜準1級・TOEIC高得点)",
                  lead="英検2級〜準1級、TOEIC 800点以上を目指す人向けの英単語。日本語の例文を見て、すぐに英語で言ってみよう。"),
}


def page_cards(kind, data, keys, archive):
    cards = "".join(listen_card(it) if kind == "listening" else word_card(it, kind)
                    for k in keys if k.startswith(kind) for it in data[k])
    # 過去の投稿(2023〜2024年)。quizify_archive.py で毎日少しずつ取り込んでいる
    old = sorted(archive.get(kind, {}).values(), key=lambda v: v["date"], reverse=True)
    old_items = [it for v in old for it in v.get("items", []) if kind != "listening" or (it.get("a") and it.get("b"))]
    if old_items:
        cards += f'<li class="era">過去の問題(2023〜2024年)・{len(old_items)}問</li>' + "".join(
            listen_card({**it, "words": it.get("words", [])}) if kind == "listening" else word_card(it, kind) for it in old_items)
    n = sum(len(data[k]) for k in keys if k.startswith(kind)) + len(old_items)
    return cards or "<li class=empty>近日公開</li>", n


def fill(**kw):
    out = TEMPLATE
    for k, v in kw.items():
        out = out.replace("{{" + k + "}}", str(v))
    return out


def pages():
    data = json.loads(DATA.read_text())
    posted = json.loads(POSTED.read_text()) if POSTED.exists() else {}
    arc = ROOT / "quizify_archive.json"
    archive = json.loads(arc.read_text()) if arc.exists() else {}
    keys = sorted((k for k in posted if k in data), key=lambda k: posted[k]["posted_at"], reverse=True)
    count = len(json.loads((ROOT / "posted.json").read_text())) // 10 * 10 + 100  # トップのクイズの問題数(アーカイブ100問+投稿分)。「〇問以上」用に10の位で切り捨て
    hub = []
    for kind, pg in PAGES.items():
        cards, n = page_cards(kind, data, keys, archive)
        others = "".join(f'<a href="/{p2["path"]}/">{p2["icon"]} {p2["name"]}</a>' for k2, p2 in PAGES.items() if k2 != kind)
        body = f'<ol>{cards}</ol><nav class="others"><p>ほかの問題</p>{others}</nav>'
        d = ROOT / "docs" / pg["path"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(fill(title=pg["title"], desc=pg["desc"], path=pg["path"], crumb=pg["name"], h1=pg["h1"],
                                           lead=pg["lead"], body=body, kind=kind, count=count))
        hub.append(f'<a class="hubcard" href="/{pg["path"]}/"><b>{pg["icon"]} {pg["name"]}</b><small>{pg["lead"]}</small><em>{n}問 →</em></a>')
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "index.html").write_text(fill(
        title="リスニング・英単語・瞬間英作文|音声つき英語クイズ|eng_navi",
        desc="TOEIC Part 3・4/英検のリスニング、英検3級〜2級の英単語・熟語、英検準1級・TOEIC高得点の瞬間英作文。音声つきで復習できます。",
        path="quizify", crumb="音声つき英語クイズ", h1="音声つきで、もう一度",
        lead="Instagram @quizify_english の問題を、レベル別にまとめています。", body="".join(hub), kind="", count=count))
    print(f"✓ quizify のページ({len(keys)} 本分+過去の投稿)")


TEMPLATE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{title}}</title>
<meta name="description" content="{{desc}}">
<link rel="canonical" href="https://eng-navi.github.io/{{path}}/">
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:wght@500;600&family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #f5f3ef; background-image: linear-gradient(#dedcd7 1px, transparent 1px), linear-gradient(90deg, #dedcd7 1px, transparent 1px); background-size: 27px 27px; color: #282828; font-family: "Noto Sans JP", sans-serif; }
  main { max-width: 560px; margin: 0 auto; padding: 28px 16px 48px; }
  .crumb { font-size: 12px; color: #888; } .crumb a { color: inherit; }
  h1 { font-size: 22px; line-height: 1.5; margin-top: 16px; }
  .lead { margin-top: 8px; font-size: 14px; color: #666; line-height: 1.8; }
  .hubcard { display: block; margin-top: 14px; padding: 18px; border-radius: 14px; background: #fff; text-decoration: none; color: #282828; box-shadow: 0 2px 8px rgba(0,0,0,.05); }
  .hubcard b { display: block; font-size: 17px; } .hubcard small { display: block; margin-top: 6px; font-size: 13px; color: #666; line-height: 1.7; }
  .hubcard em { display: inline-block; margin-top: 10px; font-style: normal; font-weight: 700; color: #c83430; font-size: 14px; }
  .others { margin-top: 22px; } .others p { font-size: 13px; color: #888; }
  .others a { display: block; margin-top: 8px; padding: 12px 14px; border-radius: 12px; background: #fff; color: #282828; text-decoration: none; font-size: 14px; }
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
  .era { list-style: none; margin-top: 10px; font-size: 13px; font-weight: 700; color: #888; text-align: center; }
  .empty { color: #999; font-size: 14px; text-align: center; padding: 20px; }
  .cta { display: block; margin-top: 22px; padding: 14px; border-radius: 14px; background: #282828; color: #fff; text-align: center; text-decoration: none; font-weight: 500; }
  .toplink { display: flex; align-items: center; gap: 6px; margin-top: 16px; padding: 12px 14px; border-radius: 14px; border: 2px solid #c83430; background: #fff; color: #282828; text-decoration: none; font-size: 13px; line-height: 1.6; }
  .toplink b { color: #c83430; } .toplink span { margin-left: auto; color: #c83430; font-weight: 700; font-size: 18px; }
  .home { display: block; margin-top: 12px; padding: 16px; border-radius: 14px; background: #c83430; color: #fff; text-decoration: none; text-align: center; }
  .home b { display: block; font-size: 17px; } .home small { display: block; margin-top: 4px; font-size: 12px; opacity: .9; }
  .home span { display: inline-block; margin-top: 10px; padding: 6px 18px; border-radius: 999px; background: #fff; color: #c83430; font-weight: 700; font-size: 14px; }
  .rec { margin-top: 22px; background: #fff; border-radius: 14px; padding: 16px; position: relative; } .rec:empty { display: none; }
  .rec h3 { font-size: 14px; color: #c83430; padding-right: 30px; } .rec .pr { position: absolute; top: 14px; right: 14px; font-size: 10px; color: #aaa; }
  .rec p.lead2 { margin-top: 6px; font-size: 13px; color: #666; line-height: 1.7; }
  .rec a { display: block; margin-top: 10px; padding: 12px 14px; border-radius: 12px; background: #f5f3ef; text-decoration: none; color: #282828; }
  .rec a b { display: block; font-size: 15px; } .rec a small { display: block; margin-top: 3px; font-size: 12px; color: #777; }
  .tip { display: inline-block; margin-bottom: 6px; padding: 3px 10px; border-radius: 999px; background: #c83430; color: #fff; font-size: 12px; font-weight: 700; }
  .tip small { margin-left: 6px; font-weight: 400; opacity: .8; } .tip .fine { display: block; margin: 2px 0 0; }
  .abroad { margin-top: 14px; }
  .foot { margin-top: 26px; font-size: 10px; color: #aaa; text-align: center; } .foot a { color: inherit; }
</style>
</head>
<body>
<main>
  <p class="crumb"><a href="/">eng_navi 英語クイズ</a> › {{crumb}}</p>
  <h1>{{h1}}</h1>
  <p class="lead">{{lead}}</p>
  <a class="toplink" href="/">🎯 トップには<b>英文法クイズが{{count}}問以上</b>。解くほど苦手がわかります<span>→</span></a>
  {{body}}
  <div class="rec" id="rec"></div>
  <a class="cta" href="https://www.instagram.com/quizify_english/">Instagram で毎日の問題を見る →</a>
  <a class="home" href="/"><b>英文法クイズ {{count}}問以上・無料</b><small>1問30秒。英検・TOEIC・大学受験の得点アップに</small><span>トップで挑戦する →</span></a>
  <div class="rec abroad" id="abroad"></div>
  <p class="foot"><a href="/">eng_navi 英語クイズ</a></p>
</main>
<script src="/recommend.js"></script>
<script>
if (window.ANALYTICS_ID) {
  const t = document.createElement("script"); t.async = true;
  t.src = "https://www.googletagmanager.com/gtag/js?id=" + window.ANALYTICS_ID; document.head.appendChild(t);
  window.dataLayer = window.dataLayer || []; window.gtag = function () { dataLayer.push(arguments); };
  gtag("js", new Date()); gtag("config", window.ANALYTICS_ID);
}
// タブごとのおすすめ(上:勉強の続き、下:話す・留学)。ひとことは recommend.js の promoTip(セール > 無料体験の A/B)
const I = window.ITEMS || {};
const RECS = {
  listening: { title: "TOEICのリスニングをもっと伸ばすなら", items: [I.studysapuri, I.kikufure] },
  white: { title: "受験・英検の英語をもっと固めるなら", items: [I.scramble, I.oversight] },
  black: { title: "準1級の単語・長文にもっと強くなるなら", items: [I.pinnacle, I.speak] },
};
const link = (it) => it ? `<a href="${it.url}" target="_blank" rel="noopener sponsored nofollow">${window.promoTip ? window.promoTip(it) : ""}<b>${window.nb(it.name)}</b><small>${window.nb(it.note)}</small></a>` + (it.pixel ? `<img src="${it.pixel}" width="1" height="1" alt="" style="position:absolute;opacity:0">` : "") : "";
const showRec = (t) => {
  const r = RECS[t]; const el = document.getElementById("rec");
  if (el && r) el.innerHTML = `<span class="pr">PR</span><h3>${r.title}</h3>${r.items.map(link).join("")}`;
};
if (window.ABROAD) document.getElementById("abroad").innerHTML = `<span class="pr">PR</span><h3>✈️ 海外で英語を使ってみたい人へ</h3><p class="lead2">${window.ABROAD.lead}</p>${link(window.ABROAD.item)}`;
document.addEventListener("click", (ev) => {
  const a = ev.target.closest("a[href]");
  if (!a || !window.gtag) return;
  const tip = a.querySelector("[data-copy]"), copy = tip ? tip.dataset.copy : "none";
  const label = (a.querySelector("b") || a).textContent.trim().slice(0, 80);
  const place = a.classList.contains("toplink") ? "quizify_top" : a.classList.contains("home") ? "quizify_home" : a.closest(".abroad") ? "quizify_abroad" : a.closest(".rec") ? "quizify_rec" : "quizify_other";
  gtag("event", "link_click", { place, label: tip ? `${label} [${copy}]` : label, copy });
});
showRec("{{kind}}");
// 前の /quizify/#white などのリンクは、色ごとのページへ
const OLD = { listening: "/listening/", white: "/tango/", black: "/tango-advanced/" };
if (!"{{kind}}" && OLD[location.hash.slice(1)]) location.replace(OLD[location.hash.slice(1)]);
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
