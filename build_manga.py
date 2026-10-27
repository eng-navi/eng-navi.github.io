"""4コマのページ(docs/manga/<key>/)と一覧(docs/manga/)を書き出す。

リールで流したキャラの声(ElevenLabs、out/voice_cache に保存ずみ)をコマごとの mp3 にして、
タップで聞き直し・通して聞く・聞き流し・意味クイズができるようにする。最後にマイクロコピーつきのおすすめ。
対象は manga_schedule.json に入っている4コマ(語呂合わせは除く)と inside_out。

    .venv-tts/bin/python build_manga.py
"""
import html
import json
import random
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image

import manga as m
import manga_fast as mf
import manga_reel as mr
import tts

ROOT = Path(__file__).parent
SITE = ROOT / "docs"
SITE_URL = "https://eng-navi.github.io"
VOICES = {"us_f": "🇺🇸 女性", "us_m": "🇺🇸 男性", "uk_f": "🇬🇧 女性", "uk_m": "🇬🇧 男性"}
NAMES = {"navi": "ナビ", "pen": "ペン", "boss": "部長"}
# 分類ごとのおすすめ(本, サービス)。キーは docs/recommend.js の ITEMS
PICKS = {"toeic": ("kikufure", "studysapuri"), "daily": ("setphrase", "speak")}
SPEED = 1.1  # テンポの速い版と同じ速さ


def e(s):
    return html.escape(str(s), quote=True)


def comics():
    """ページにする4コマの一覧(予約順)。"""
    sched = json.loads((ROOT / "manga_schedule.json").read_text())
    caps = {s["key"]: s["caption"] for s in sched}
    keys = [s["key"] for s in sched] + ["inside_out"]
    out = []
    for k in dict.fromkeys(keys):
        cap = caps.get(k, "")
        if k in mf.SCRIPTS:
            sc = mf.SCRIPTS[k]
            c = dict(word=sc["word"], meaning=sc["meaning"], level=sc["level"], hook=sc["hook"], ex_en=sc["ex_en"],
                     ex_ja=sc["ex_ja"], words=sc["words"], panels=sc["panels"])
        elif k in mr.SCRIPTS and k in m.SCRIPTS:
            _, (word, meaning, ex_en, ex_ja, _) = m.SCRIPTS[k]
            c = dict(word=word, meaning=meaning, level="", hook=cap.split("\n")[0] if cap else "", ex_en=ex_en,
                     ex_ja=ex_ja, words=[], panels=[[line] for line in mr.SCRIPTS[k]["lines"]])
        else:
            continue
        if not (ROOT / "out" / "manga" / f"{k}_1.png").exists():
            continue
        c["key"] = k
        c["series"] = "toeic" if "#TOEIC" in cap or "TOEIC" in c["level"] else "daily"
        out.append(c)
    return out


def voice(who, text):
    # リールと同じく、声ごとの大きさをそろえる
    a = mr.eleven(who, text, SPEED)
    rms = float(np.sqrt(np.mean(a ** 2))) or 1.0
    a = a * (0.09 / rms)
    return a * min(1.0, 0.95 / (float(np.max(np.abs(a))) or 1.0))


def mp3(audio, out):
    with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
        sf.write(wav.name, audio.astype(np.float32), mr.SR)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav.name, "-ac", "1", "-b:a", "64k", str(out)], check=True)


def assets(c):
    d = SITE / "manga" / c["key"]
    d.mkdir(parents=True, exist_ok=True)
    img = d / "comic.jpg"
    if not img.exists():
        Image.open(ROOT / "out" / "manga" / f"{c['key']}_1.png").convert("RGB").resize((720, 900), Image.LANCZOS).save(img, quality=82)
    for i, lines in enumerate(c["panels"], 1):
        out = d / f"p{i}.mp3"
        if out.exists():
            continue
        parts = []
        for who, text in lines:
            parts += [voice(who, text), np.zeros(int(mr.SR * 0.3), np.float32)]
        mp3(np.concatenate(parts), out)
    engine = None
    for v in VOICES:
        for name, text in (("word", c["word"]), ("ex", c["ex_en"])):
            out = d / f"{name}_{v}.mp3"
            if not out.exists():
                engine = engine or tts.Kokoro()
                engine(text, out, v)


def page(c, prev, nxt, others, boxes):
    rng = random.Random(c["key"])
    wrong = rng.sample([o["meaning"] for o in others if o["meaning"] != c["meaning"]], 2)
    data = dict(key=c["key"], word=c["word"], ex=c["ex_en"], panels=len(c["panels"]),
                choices=rng.sample([c["meaning"]] + wrong, 3), answer=c["meaning"], items=PICKS[c["series"]])
    title = f"{c['word']}の意味と使い方|4コマで覚える英語(音声つき)"
    desc = f"{c['word']} = {c['meaning']}。4コマ漫画のセリフを、キャラの声で何回でも聞けます。例文の音声(アメリカ・イギリス英語)とクイズつき。"
    hits = "".join(
        f'<button class="hit" data-p="{i}" aria-label="{i}コマ目を聞く" style="left:{x0:.2f}%;top:{y0:.2f}%;width:{x1 - x0:.2f}%;height:{y1 - y0:.2f}%"></button>'
        for i, (x0, y0, x1, y1) in enumerate(boxes, 1))
    script = "".join(
        f'<li data-p="{i}"><span class="n">{i}</span><div>'
        + "".join(f'<p><b>{NAMES[w]}</b>{e(t)}</p>' for w, t in lines) + "</div></li>"
        for i, lines in enumerate(c["panels"], 1))
    words = "".join(f"<li><b>{e(en)}</b><span>{e(ja)}</span></li>" for en, ja in c["words"])
    voices = "".join(f'<button data-v="{k}">{v}</button>' for k, v in VOICES.items())
    nav = (f'<a href="../{prev["key"]}/">‹ {e(prev["word"])}</a>' if prev else "<span></span>") + '<a href="../">一覧</a>' + \
          (f'<a href="../{nxt["key"]}/">{e(nxt["word"])} ›</a>' if nxt else "<span></span>")
    return (TEMPLATE
            .replace("__TITLE__", e(title)).replace("__DESC__", e(desc)).replace("__KEY__", c["key"])
            .replace("__WORD__", e(c["word"])).replace("__MEANING__", e(c["meaning"]))
            .replace("__HOOK__", e(c["hook"])).replace("__LEVEL__", f'<p class="level">{e(c["level"])}</p>' if c["level"] else "")
            .replace("__HITS__", hits).replace("__SCRIPT__", script).replace("__VOICES__", voices)
            .replace("__EXEN__", e(c["ex_en"])).replace("__EXJA__", e(c["ex_ja"]))
            .replace("__WORDS__", f'<section class="card"><h2>今回出てきた単語 <button class="mini" id="hide-ja">意味をかくす</button></h2><ul class="words" id="words">{words}</ul></section>' if words else "")
            .replace("__NAV__", nav).replace("__DATA__", json.dumps(data, ensure_ascii=False)))


TEMPLATE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<meta name="description" content="__DESC__">
<link rel="canonical" href="https://eng-navi.github.io/manga/__KEY__/">
<meta property="og:title" content="__TITLE__">
<meta property="og:description" content="__DESC__">
<meta property="og:image" content="https://eng-navi.github.io/manga/__KEY__/comic.jpg">
<link href="https://fonts.googleapis.com/css2?family=Kalam:wght@700&family=EB+Garamond:wght@400;500&family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #f5f3ef; background-image: linear-gradient(#dedcd7 1px, transparent 1px), linear-gradient(90deg, #dedcd7 1px, transparent 1px); background-size: 27px 27px; color: #282828; font-family: "Noto Sans JP", system-ui, sans-serif; }
  main { max-width: 560px; margin: 0 auto; padding: 24px 16px 48px; }
  .crumb { font-size: 12px; color: #888; } .crumb a { color: inherit; }
  h1 { margin-top: 14px; font-family: "Kalam", cursive; font-size: 40px; line-height: 1.2; }
  h1 small { display: block; font-family: "Noto Sans JP"; font-size: 17px; color: #c83430; margin-top: 2px; }
  .lead { margin-top: 8px; font-size: 13px; color: #666; line-height: 1.8; }
  .comic { position: relative; margin-top: 14px; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,.08); background: #f4f1ea; }
  .comic img { display: block; width: 100%; height: auto; }
  .hit { position: absolute; border: 0; background: transparent; border-radius: 8px; cursor: pointer; transition: box-shadow .2s, background .2s; }
  .hit.now { box-shadow: 0 0 0 4px #c83430; background: rgba(200,52,48,.06); }
  .tap { position: absolute; left: 50%; bottom: 10px; transform: translateX(-50%); padding: 5px 12px; border-radius: 999px; background: rgba(40,40,40,.78); color: #fff; font-size: 11px; white-space: nowrap; pointer-events: none; transition: opacity .4s; }
  .ctrl { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 12px; }
  .ctrl button { padding: 13px 8px; border: 0; border-radius: 14px; background: #282828; color: #fff; font-size: 14px; font-weight: 700; cursor: pointer; font-family: inherit; }
  .ctrl button + button { background: #c83430; }
  .ctrl button[aria-pressed="true"] { background: #fff; color: #c83430; box-shadow: inset 0 0 0 2px #c83430; }
  .note { margin-top: 6px; font-size: 11px; color: #999; text-align: center; }
  .card { margin-top: 16px; background: #fff; border-radius: 14px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.05); }
  .card h2 { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #c83430; }
  .script { list-style: none; margin-top: 10px; display: grid; gap: 8px; }
  .script li { display: flex; gap: 10px; padding: 8px 10px; border-radius: 10px; cursor: pointer; transition: background .2s; }
  .script li.now { background: #fbeceb; }
  .script .n { flex: none; width: 22px; height: 22px; border-radius: 50%; background: #282828; color: #fff; font-size: 12px; display: grid; place-items: center; margin-top: 2px; }
  .script p { font-family: "EB Garamond", serif; font-size: 18px; line-height: 1.45; }
  .script p b { font-family: "Noto Sans JP"; font-size: 11px; color: #999; font-weight: 500; margin-right: 6px; }
  .phrase { font-family: "Kalam", cursive; font-size: 30px; margin-top: 6px; }
  .meaning { color: #c83430; font-size: 15px; }
  .level { margin-top: 2px; font-size: 11px; color: #999; }
  .voices { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
  .voices button { border: 1px solid #ccc; background: #fff; border-radius: 999px; padding: 6px 12px; font-size: 12px; cursor: pointer; font-family: inherit; }
  .voices button[aria-pressed="true"] { background: #c83430; border-color: #c83430; color: #fff; }
  .ex { margin-top: 12px; font-family: "EB Garamond", serif; font-size: 19px; line-height: 1.5; }
  .exja { font-size: 13px; color: #777; margin-top: 2px; }
  .plays { display: flex; gap: 8px; margin-top: 10px; }
  .plays button, .mini { border: 0; background: #282828; color: #fff; border-radius: 999px; padding: 7px 14px; font-size: 12px; cursor: pointer; font-family: inherit; }
  .mini { margin-left: auto; background: #eee; color: #555; padding: 4px 10px; font-size: 11px; font-weight: 400; }
  .words { list-style: none; margin-top: 8px; }
  .words li { display: flex; gap: 12px; padding: 8px 0; border-top: 1px solid #eee; font-size: 13px; }
  .words b { font-family: "EB Garamond", serif; font-size: 17px; min-width: 40%; }
  .words span { color: #666; transition: opacity .2s; }
  .words.hide span { opacity: 0; }
  .words.hide li.open span { opacity: 1; }
  .q { margin-top: 8px; font-size: 15px; font-weight: 700; }
  .choices { display: grid; gap: 8px; margin-top: 10px; }
  .choices button { text-align: left; padding: 12px 14px; border: 1px solid #ddd; border-radius: 12px; background: #fff; font-size: 14px; cursor: pointer; font-family: inherit; color: #282828; }
  .choices button.ok { border-color: #2e8b57; background: #eaf6ef; }
  .choices button.ng { border-color: #c83430; background: #fbeceb; }
  .result { margin-top: 8px; font-size: 13px; min-height: 1em; }
  .pr { position: relative; }
  .pr .tag { position: absolute; top: 14px; right: 14px; font-size: 10px; color: #aaa; }
  .pr a.item { display: block; margin-top: 4px; padding: 12px 14px; border-radius: 12px; background: #f5f3ef; text-decoration: none; color: #282828; }
  .pr a.item b { display: block; font-size: 15px; } .pr a.item small { display: block; margin-top: 3px; font-size: 12px; color: #777; line-height: 1.6; text-wrap: pretty; }
  .pr a.item i { display: inline-block; margin-top: 8px; font-style: normal; font-size: 12px; font-weight: 700; color: #c83430; }
  .tip { position: relative; display: block; width: fit-content; max-width: 100%; margin: 12px 0 9px; padding: 5px 12px; border-radius: 10px; background: #f3e3c8; color: #8a5a14; font-size: 12px; font-weight: 700; line-height: 1.5; }
  .tip::after { content: ""; position: absolute; left: 22px; bottom: -6px; border: 6px solid transparent; border-bottom: 0; border-top-color: #f3e3c8; }
  .tip small { margin-left: 6px; font-size: 10px; font-weight: 400; opacity: .75; }
  .tip .fine { display: block; margin: 2px 0 0; opacity: .85; line-height: 1.5; }
  .tip.hot { background: #d8433b; color: #fff; font-size: 14px; padding: 7px 13px; }
  .tip.hot small { display: block; margin: 1px 0 0; } .tip.hot::after { border-top-color: #d8433b; }
  .nav { display: flex; justify-content: space-between; gap: 8px; margin-top: 20px; font-size: 13px; }
  .nav a { color: #555; text-decoration: none; padding: 8px 4px; }
  .cta { display: block; margin-top: 14px; padding: 14px; border-radius: 14px; background: #282828; color: #fff; text-align: center; text-decoration: none; font-weight: 500; }
  .cta small { display: block; margin-top: 2px; font-size: 11px; font-weight: 400; opacity: .7; }
  .sub { display: block; margin-top: 10px; padding: 13px; border-radius: 14px; border: 1px solid #ccc; background: #fff; text-align: center; text-decoration: none; color: #555; font-size: 14px; }
  .foot { margin-top: 26px; font-size: 10px; color: #aaa; text-align: center; line-height: 1.7; }
</style>
</head>
<body>
<main>
  <p class="crumb"><a href="/">eng_navi 英語クイズ</a> › <a href="../">4コマで覚える英語</a></p>
  <h1>__WORD__<small>= __MEANING__</small></h1>
  <p class="lead">__HOOK__ コマをタップすると、そのセリフをキャラの声で聞けます。</p>
  <div class="comic"><img src="comic.jpg" width="720" height="900" alt="4コマ漫画「__WORD__」">__HITS__<span class="tap" id="tap">👆 コマをタップで再生</span></div>
  <div class="ctrl"><button id="through">▶ 4コマを通して聞く</button><button id="loop" aria-pressed="false">🔁 聞き流し</button></div>
  <p class="note" id="note">聞き流しは、4コマ → フレーズ → 例文 をくり返します</p>

  <section class="card">
    <h2>セリフ</h2>
    <ol class="script">__SCRIPT__</ol>
  </section>

  <section class="card">
    <h2>今日のフレーズ</h2>
    <p class="phrase">__WORD__</p>
    <p class="meaning">= __MEANING__</p>
    __LEVEL__
    <div class="voices">__VOICES__</div>
    <p class="ex">__EXEN__</p>
    <p class="exja">(__EXJA__)</p>
    <div class="plays"><button data-say="word">▶ フレーズ</button><button data-say="ex">▶ 例文</button></div>
  </section>

  __WORDS__

  <section class="card">
    <h2>クイズ</h2>
    <p class="q" id="q"></p>
    <div class="choices" id="choices"></div>
    <p class="result" id="result"></p>
  </section>

  <section class="card pr" id="pr"></section>

  <div class="nav">__NAV__</div>
  <a class="cta" href="/">英文法クイズに挑戦する<small>無料・100問以上</small></a>
  <a class="sub" href="https://www.instagram.com/yonkoma_eigo/" target="_blank" rel="noopener">Instagram で毎日4コマ @yonkoma_eigo</a>
  <p class="foot">キャラの声は ElevenLabs、例文の音声は Kokoro で作っています。</p>
</main>
<script src="/recommend.js"></script>
<script>
  const D = __DATA__;
  if (window.ANALYTICS_ID) {
    const t = document.createElement("script"); t.async = true;
    t.src = "https://www.googletagmanager.com/gtag/js?id=" + window.ANALYTICS_ID; document.head.appendChild(t);
    window.dataLayer = window.dataLayer || []; window.gtag = function () { dataLayer.push(arguments); };
    gtag("js", new Date()); gtag("config", window.ANALYTICS_ID);
  }
  const ev = (name, p) => { try { if (window.gtag) gtag("event", name, Object.assign({ key: D.key }, p)); } catch (e) {} };

  // ---- 再生 ----
  let voice = "us_f";
  try { voice = localStorage.getItem("voice") || "us_f"; } catch (e) {}
  const vbtn = document.querySelectorAll("[data-v]");
  const markV = () => vbtn.forEach((b) => b.setAttribute("aria-pressed", b.dataset.v === voice));
  vbtn.forEach((b) => (b.onclick = () => { voice = b.dataset.v; try { localStorage.setItem("voice", voice); } catch (e) {} markV(); say("word"); }));
  markV();
  let player = null, run = 0;
  const hits = document.querySelectorAll(".hit"), lines = document.querySelectorAll(".script li");
  const mark = (p) => { hits.forEach((h) => h.classList.toggle("now", +h.dataset.p === p)); lines.forEach((l) => l.classList.toggle("now", +l.dataset.p === p)); };
  function play(src, p) {
    return new Promise((done) => {
      if (player) { player.onended = null; player.pause(); }
      player = new Audio(src);
      mark(p || 0);
      player.onended = () => { mark(0); done(true); };
      player.onerror = () => done(false);
      player.play().catch(() => done(false));
    });
  }
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  function stop() { run++; if (player) { player.onended = null; player.pause(); } mark(0); setLoop(false); }
  const panel = (p) => play(`p${p}.mp3`, p);
  const say = (what) => { stop(); play(`${what}_${voice}.mp3`); ev("manga_play", { part: what, voice }); };
  document.querySelectorAll("[data-say]").forEach((b) => (b.onclick = () => say(b.dataset.say)));
  const hideTap = () => (document.getElementById("tap").style.opacity = 0);
  hits.forEach((h) => (h.onclick = () => { stop(); hideTap(); panel(+h.dataset.p); ev("manga_play", { part: "panel" + h.dataset.p }); }));
  lines.forEach((l) => (l.onclick = () => { stop(); panel(+l.dataset.p); }));
  async function through(id) {
    for (let p = 1; p <= D.panels; p++) { if (id !== run || !(await panel(p))) return false; await wait(250); }
    return id === run;
  }
  document.getElementById("through").onclick = async () => { stop(); hideTap(); const id = run; ev("manga_play", { part: "through" }); await through(id); };
  // 聞き流し:4コマ → フレーズ → 例文 をくり返す
  const loopBtn = document.getElementById("loop");
  function setLoop(on) { loopBtn.setAttribute("aria-pressed", on); loopBtn.textContent = on ? "■ 止める" : "🔁 聞き流し"; }
  loopBtn.onclick = async () => {
    if (loopBtn.getAttribute("aria-pressed") === "true") return stop();
    stop(); hideTap(); setLoop(true); const id = run; ev("manga_play", { part: "loop" });
    while (id === run) {
      if (!(await through(id))) break;
      await wait(500); if (id !== run || !(await play(`word_${voice}.mp3`))) break;
      await wait(500); if (id !== run || !(await play(`ex_${voice}.mp3`))) break;
      await wait(1500);
    }
  };

  // ---- 単語:意味をかくして、タップで1つずつ確認 ----
  const words = document.getElementById("words");
  if (words) {
    const btn = document.getElementById("hide-ja");
    btn.onclick = () => { const on = words.classList.toggle("hide"); words.querySelectorAll("li").forEach((li) => li.classList.remove("open")); btn.textContent = on ? "意味を見せる" : "意味をかくす"; };
    words.querySelectorAll("li").forEach((li) => (li.onclick = () => li.classList.add("open")));
  }

  // ---- クイズ ----
  document.getElementById("q").textContent = `「${D.word}」の意味は?`;
  const box = document.getElementById("choices");
  box.innerHTML = D.choices.map((c) => `<button>${c}</button>`).join("");
  box.querySelectorAll("button").forEach((b) => (b.onclick = () => {
    const ok = b.textContent === D.answer;
    box.querySelectorAll("button").forEach((x) => { x.disabled = true; if (x.textContent === D.answer) x.classList.add("ok"); });
    if (!ok) b.classList.add("ng");
    document.getElementById("result").textContent = ok ? "正解!例文も聞いて、使い方まで覚えよう🔊" : `正解は「${D.answer}」。もう一度4コマを聞いてみよう`;
    ev("manga_quiz", { correct: ok });
  }));

  // ---- おすすめ(ボタンの上にセール・無料体験の一言) ----
  const items = D.items.map((k) => window.ITEMS && ITEMS[k]).filter(Boolean);
  if (items.length) {
    document.getElementById("pr").innerHTML = `<span class="tag">PR</span><h2>このフレーズを、もっと身につけるなら</h2>` + items.map((it) =>
      `${promoTip(it)}<a class="item" href="${it.url}" target="_blank" rel="noopener sponsored nofollow"><b>${nb(it.name)}</b><small>${nb(it.note || "")}</small><i>${/amazon|amzn/.test(it.url) ? "Amazonで中身を見る" : "無料で試してみる"} →</i></a>` +
      (it.pixel ? `<img src="${it.pixel}" width="1" height="1" alt="" style="position:absolute;opacity:0">` : "")).join("");
  } else document.getElementById("pr").remove();
  document.addEventListener("click", (e) => {
    const a = e.target.closest("a[href]");
    if (!a) return;
    const tip = a.previousElementSibling && a.previousElementSibling.classList.contains("tip") ? a.previousElementSibling : null;
    const copy = tip ? tip.dataset.copy : "none";
    const label = (a.querySelector("b") || a).textContent.trim().slice(0, 80);
    ev("link_click", { place: a.classList.contains("item") ? "manga_pr" : "manga_other", label: tip ? `${label} [${copy}]` : label, copy, copy_text: tip ? tip.textContent.trim().slice(0, 60) : "" });
  });
</script>
</body>
</html>
"""


def index_page(cs):
    cards = "".join(
        f'<li><a href="{c["key"]}/"><img src="{c["key"]}/comic.jpg" width="720" height="900" alt="" loading="lazy">'
        f'<b>{e(c["word"])}</b><span>{e(c["meaning"])}</span></a></li>' for c in cs)
    data = json.dumps([dict(key=c["key"], word=c["word"], meaning=c["meaning"], panels=len(c["panels"])) for c in cs], ensure_ascii=False)
    return INDEX.replace("__CARDS__", cards).replace("__DATA__", data).replace("__N__", str(len(cs)))


INDEX = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>4コマで覚える英語|キャラの声で聞ける英語フレーズ|eng_navi</title>
<meta name="description" content="ゆるい4コマ漫画で、英語フレーズを覚える。セリフをキャラの声で何回でも聞けて、聞き流しとクイズもできます。">
<link rel="canonical" href="https://eng-navi.github.io/manga/">
<link href="https://fonts.googleapis.com/css2?family=Kalam:wght@700&family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #f5f3ef; background-image: linear-gradient(#dedcd7 1px, transparent 1px), linear-gradient(90deg, #dedcd7 1px, transparent 1px); background-size: 27px 27px; color: #282828; font-family: "Noto Sans JP", system-ui, sans-serif; }
  main { max-width: 560px; margin: 0 auto; padding: 24px 16px 48px; }
  .crumb { font-size: 12px; color: #888; } .crumb a { color: inherit; }
  h1 { margin-top: 14px; font-size: 22px; line-height: 1.5; }
  .lead { margin-top: 8px; font-size: 13px; color: #666; line-height: 1.8; }
  .player { position: sticky; top: 8px; z-index: 2; margin-top: 14px; display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 14px; background: #282828; color: #fff; box-shadow: 0 6px 18px rgba(0,0,0,.15); }
  .player button { flex: none; border: 0; border-radius: 999px; padding: 9px 14px; background: #c83430; color: #fff; font-size: 13px; font-weight: 700; cursor: pointer; font-family: inherit; }
  .player span { font-size: 12px; opacity: .85; line-height: 1.5; }
  ul { list-style: none; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 14px; }
  li a { display: block; background: #fff; border-radius: 14px; overflow: hidden; text-decoration: none; color: #282828; box-shadow: 0 2px 8px rgba(0,0,0,.05); transition: box-shadow .2s; }
  li a.now { box-shadow: 0 0 0 3px #c83430; }
  li img { display: block; width: 100%; height: auto; aspect-ratio: 720 / 600; object-fit: cover; object-position: top; }
  li b { display: block; padding: 8px 10px 0; font-family: "Kalam", cursive; font-size: 18px; line-height: 1.3; }
  li span { display: block; padding: 0 10px 10px; font-size: 11px; color: #c83430; }
  .cta { display: block; margin-top: 18px; padding: 14px; border-radius: 14px; background: #282828; color: #fff; text-align: center; text-decoration: none; font-weight: 500; }
  .sub { display: block; margin-top: 10px; padding: 13px; border-radius: 14px; border: 1px solid #ccc; background: #fff; text-align: center; text-decoration: none; color: #555; font-size: 14px; }
</style>
</head>
<body>
<main>
  <p class="crumb"><a href="/">eng_navi 英語クイズ</a> › 4コマで覚える英語</p>
  <h1>4コマで覚える英語</h1>
  <p class="lead">ナビ・ペン・部長のゆるい4コマで、英語フレーズを覚えよう。どの4コマも、セリフをキャラの声で何回でも聞けます。</p>
  <div class="player"><button id="all">▶ 全部聞き流し</button><span id="now">__N__本の4コマのセリフとフレーズを、順番に流します</span></div>
  <ul id="list">__CARDS__</ul>
  <a class="cta" href="/">英文法クイズに挑戦する</a>
  <a class="sub" href="https://www.instagram.com/yonkoma_eigo/" target="_blank" rel="noopener">Instagram で毎日4コマ @yonkoma_eigo</a>
</main>
<script src="/recommend.js"></script>
<script>
  const ALL = __DATA__;
  if (window.ANALYTICS_ID) {
    const t = document.createElement("script"); t.async = true;
    t.src = "https://www.googletagmanager.com/gtag/js?id=" + window.ANALYTICS_ID; document.head.appendChild(t);
    window.dataLayer = window.dataLayer || []; window.gtag = function () { dataLayer.push(arguments); };
    gtag("js", new Date()); gtag("config", window.ANALYTICS_ID);
  }
  let voice = "us_f";
  try { voice = localStorage.getItem("voice") || "us_f"; } catch (e) {}
  let player = null, run = 0;
  const cards = document.querySelectorAll("#list a"), btn = document.getElementById("all"), now = document.getElementById("now");
  const play = (src) => new Promise((done) => { player = new Audio(src); player.onended = () => done(true); player.onerror = () => done(false); player.play().catch(() => done(false)); });
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  btn.onclick = async () => {
    if (btn.dataset.on) { run++; if (player) player.pause(); btn.textContent = "▶ 全部聞き流し"; delete btn.dataset.on; cards.forEach((c) => c.classList.remove("now")); return; }
    btn.dataset.on = 1; btn.textContent = "■ 止める"; const id = ++run;
    if (window.gtag) gtag("event", "manga_play", { key: "all", part: "loop" });
    for (let i = 0; id === run; i = (i + 1) % ALL.length) {
      const c = ALL[i];
      cards.forEach((x, j) => x.classList.toggle("now", j === i));
      cards[i].scrollIntoView({ behavior: "smooth", block: "nearest" });
      now.textContent = `${c.word}(${c.meaning})`;
      for (let p = 1; p <= c.panels && id === run; p++) { await play(`${c.key}/p${p}.mp3`); await wait(250); }
      if (id === run) { await wait(400); await play(`${c.key}/word_${voice}.mp3`); }
      if (id === run) { await wait(400); await play(`${c.key}/ex_${voice}.mp3`); }
      await wait(1500);
    }
  };
</script>
</body>
</html>
"""


def main():
    mr.load_env()
    cs = comics()
    img, boxes, pw, ph = m.comic("x")
    pct = [(x0 / m.W * 100, y0 / m.H * 100, x1 / m.W * 100, y1 / m.H * 100) for x0, y0, x1, y1 in boxes]
    for i, c in enumerate(cs):
        assets(c)
        prev = cs[i - 1] if i > 0 else None
        nxt = cs[i + 1] if i + 1 < len(cs) else None
        (SITE / "manga" / c["key"] / "index.html").write_text(page(c, prev, nxt, cs, pct))
    (SITE / "manga" / "index.html").write_text(index_page(cs))
    print(f"✓ 4コマのページ {len(cs)} 件")


if __name__ == "__main__":
    main()
