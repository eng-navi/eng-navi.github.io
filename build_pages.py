"""問題ごとの静的ページ(docs/q/<no>/)、一覧ページ(docs/q/)、sitemap.xml、robots.txt を書き出す。

クイズ画面(docs/index.html)は JavaScript で1ページの中身を切り替えるため、Google からは1ページにしか見えない。
問題ごとに文字で読めるページを用意して、検索と「問題ごとのリンク」に対応する。build_site.py から呼ばれる。
"""
import html
import re
from datetime import date

SITE_URL = "https://eng-navi.github.io"
SERIES = {
    "green": {"name": "英検2級", "title": "英検2級でよく出る", "bar": "#456142", "bg": "#f7f4ed", "accent": "#456142", "ink": "#456142", "hl": "#afbbab"},
    "pink": {"name": "イディオム", "title": "英検頻出！これ↓読める？", "bar": "#f7b6ba", "bg": "#fdfdfd", "accent": "#f7b6ba", "ink": "#d98088", "hl": "#fce2e4"},
    "blue": {"name": "TOEIC", "title": "TOEICでよく出る", "bar": "#adc8d1", "bg": "#fdfdfd", "accent": "#acc7d1", "ink": "#5f8a99", "hl": "#dee9ed"},
}
CIRCLED = "①②③④"


def series_of(q):
    return ["pink", "blue", "green"][q["no"] % 3]


def e(s):
    return html.escape(str(s), quote=True)


def completed(q):
    if "options" not in q:
        return q["text"].replace("\n", " ")
    return re.sub(r"\(\s*\)", q["options"][q["answer"] - 1], q["question"])


def page_title(q):
    s = SERIES[series_of(q)]
    if "options" in q:
        head = f"{q['category']}の問題" if q.get("category") else "英文法クイズ"
        opts = "/".join(q["options"])
        return f"【{s['name']}】{head}:{opts}|No.{q['no']} eng_navi"
    return f"【{s['name']}】{q['target']} の意味と使い方|No.{q['no']} eng_navi"


def description(q):
    first = q.get("explanation", "").split("\n")[0]
    return f"{completed(q)}({q.get('translation', '')}){first}"[:150]


STYLE = """
  :root { --bar: %(bar)s; --bg: %(bg)s; --accent: %(accent)s; --ink-accent: %(ink)s; --hl: %(hl)s; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: #1e1e1e; font-family: "Noto Sans JP", system-ui, sans-serif; -webkit-font-smoothing: antialiased; }
  main { position: relative; max-width: 560px; margin: 0 auto; padding: 24px 20px 40px calc(min(8vw, 38px) + 22px); min-height: 100dvh; }
  main::before { content: ""; position: absolute; inset: 0 auto 0 0; width: min(8vw, 38px); background: var(--bar); }
  a { color: var(--ink-accent); }
  .crumb { font-size: 12px; color: #8a8a8a; }
  .crumb a { color: inherit; }
  .num { font-family: "Crimson Text", serif; font-style: italic; font-size: 36px; color: var(--accent); margin-top: 18px; }
  .series { font-size: 22px; font-weight: 700; color: var(--accent); margin-top: 14px; }
  h1 { font-family: "EB Garamond", serif; font-weight: 400; font-size: 25px; line-height: 1.6; margin-top: 22px; }
  h1 .mark { background: var(--hl); padding: 1px 4px; -webkit-box-decoration-break: clone; box-decoration-break: clone; }
  ol { list-style: none; margin-top: 22px; display: grid; gap: 10px; }
  ol li { font-family: "EB Garamond", serif; font-size: 24px; display: flex; gap: 14px; align-items: center; }
  ol li span { font-family: system-ui, sans-serif; font-size: 20px; }
  details { margin-top: 26px; border-top: 1px solid #e6ecee; border-bottom: 1px solid #e6ecee; }
  summary { cursor: pointer; padding: 16px 0; font-weight: 700; color: var(--ink-accent); list-style: none; }
  summary::-webkit-details-marker { display: none; }
  .ans { font-size: 20px; font-weight: 700; color: var(--ink-accent); }
  .full { font-family: "EB Garamond", serif; font-size: 20px; line-height: 1.6; margin-top: 10px; }
  .ja { color: #6b6b6b; line-height: 1.8; margin-top: 8px; font-size: 15px; }
  .ja-tag { display: inline-block; margin-right: 8px; padding: 0 7px; border-radius: 4px; font-size: 11px; line-height: 1.8; color: var(--ink-accent); background: var(--hl); font-weight: 500; }
  .gloss { margin-top: 12px; display: grid; gap: 6px; font-size: 14px; line-height: 1.6; }
  .gloss li { list-style: none; padding-left: 12px; border-left: 3px solid var(--hl); }
  .exp { margin: 14px 0 18px; line-height: 1.9; white-space: pre-line; font-size: 15px; }
  .tag { display: inline-block; font-size: 11px; color: var(--ink-accent); background: var(--hl); padding: 2px 8px; border-radius: 4px; }
  audio { width: 100%%; margin-top: 12px; }
  .cta { display: block; margin-top: 26px; padding: 16px; border-radius: 14px; background: #1e1e1e; color: #fff; text-align: center; text-decoration: none; font-weight: 500; letter-spacing: .05em; }
  .sub { display: block; margin-top: 10px; padding: 13px; border-radius: 14px; border: 1px solid #e6ecee; text-align: center; text-decoration: none; color: #6b6b6b; font-size: 14px; }
  .pager { display: flex; justify-content: space-between; margin-top: 22px; font-size: 13px; }
  .nudge { display: flex; gap: 10px; align-items: center; margin-top: 14px; padding: 12px 14px; border-radius: 12px; background: color-mix(in srgb, var(--hl) 45%%, transparent); text-decoration: none; color: #1e1e1e; font-size: 13px; line-height: 1.5; }
  .nudge small { font-size: 10px; color: #9a9a9a; letter-spacing: .1em; }
  .nudge b { font-weight: 500; }
  .foot { margin-top: 30px; font-size: 10px; line-height: 1.7; color: #b8b8b8; text-align: center; }
  .foot a { color: inherit; }
  .list h2 { margin-top: 30px; font-size: 15px; color: var(--ink-accent); }
  .list ul { list-style: none; margin-top: 8px; border-top: 1px solid #e6ecee; }
  .list li a { display: block; padding: 12px 0; border-bottom: 1px solid #e6ecee; color: #1e1e1e; text-decoration: none; font-family: "EB Garamond", serif; font-size: 17px; line-height: 1.5; }
  .list li a small { font-family: system-ui, sans-serif; font-size: 11px; color: #9a9a9a; margin-right: 8px; }
"""

HEAD = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="eng_navi 英語クイズ">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{site}/ogp.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Crimson+Text:ital@1&family=EB+Garamond:wght@400;500&family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
<style>{style}</style>
</head>
"""

FOOT = """
  <p class="foot">
    Instagram <a href="https://www.instagram.com/eng_navi/" target="_blank" rel="noopener">@eng_navi</a> のリールの問題をまとめたサイトです。<br>
    Amazonのアソシエイトとして、eng_naviは適格販売により収入を得ています。
  </p>
</main>
<script src="/recommend.js"></script>
<script>
  // アクセス解析とおすすめ(クイズ画面と同じ設定を使う)
  if (window.ANALYTICS_ID) {
    const t = document.createElement("script"); t.async = true;
    t.src = "https://www.googletagmanager.com/gtag/js?id=" + window.ANALYTICS_ID; document.head.appendChild(t);
    window.dataLayer = window.dataLayer || []; window.gtag = function () { dataLayer.push(arguments); };
    gtag("js", new Date()); gtag("config", window.ANALYTICS_ID);
  }
  const box = document.getElementById("nudge");
  if (box && window.PICKS) {
    const pool = (box.dataset.category && PICKS.CATEGORY[box.dataset.category]) || PICKS.SERIES[box.dataset.series] || [];
    const key = pool[Math.floor(Number(box.dataset.no) / 3) % pool.length];
    const it = key && ITEMS[key];
    if (it) box.outerHTML = `<a class="nudge" href="${it.url}" target="_blank" rel="noopener sponsored nofollow"><small>PR</small><span>${nb(HOOKS[key] || "")}<br><b>${nb(it.name)}</b></span></a>` +
      (it.pixel ? `<img src="${it.pixel}" width="1" height="1" alt="" style="position:absolute;opacity:0">` : "");
  }
  document.addEventListener("click", (ev) => {
    const a = ev.target.closest("a[href]");
    if (a && window.gtag) gtag("event", "link_click", { place: a.classList.contains("nudge") ? "page_explanation" : "page", label: a.textContent.trim().slice(0, 80) });
  });
</script>
</body>
</html>
"""

SERIES_KEY = {"green": "英検2級", "pink": "読解・イディオム", "blue": "TOEIC"}


def question_page(q, prev_no, next_no, has_audio):
    s = series_of(q)
    t = SERIES[s]
    url = f"{SITE_URL}/q/{q['no']}/"
    if "options" in q:
        parts = re.split(r"\(\s*\)", q["question"])
        body_q = f'<h1><span class="mark">{e(parts[0])}(  ){e(parts[1] if len(parts) > 1 else "")}</span></h1>'
        opts = "".join(f"<li><span>{CIRCLED[i]}</span>{e(o)}</li>" for i, o in enumerate(q["options"]))
        body_q += f"<ol>{opts}</ol>"
        answer = f'<p class="ans">正解:{CIRCLED[q["answer"] - 1]} {e(q["options"][q["answer"] - 1])}</p>'
        summary = "答えと解説を見る"
    else:
        text = e(q["text"]).replace(e(q["target"]), f'<span class="mark">{e(q["target"])}</span>', 1)
        body_q = f'<h1 style="white-space:pre-line">{text}</h1>'
        answer = ""
        summary = "意味と解説を見る"
    gloss = "".join(f"<li>{e(g)}</li>" for g in q.get("glossary", []))
    audio = f'<audio controls preload="none" src="/audio/q{q["no"]}.mp3"></audio>' if has_audio else ""
    tag = f'<span class="tag">{e(q["category"])}</span>' if q.get("category") else ""
    pager = '<nav class="pager">' + (f'<a href="/q/{prev_no}/">‹ No.{prev_no}</a>' if prev_no else "<span></span>") + \
        (f'<a href="/q/{next_no}/">No.{next_no} ›</a>' if next_no else "<span></span>") + "</nav>"
    reel = f'<a class="sub" href="{e(q["permalink"])}" target="_blank" rel="noopener">▶ このリールを Instagram で見る</a>' if q.get("permalink") else ""
    style = STYLE % t
    return HEAD.format(title=e(page_title(q)), desc=e(description(q)), url=url, site=SITE_URL, style=style) + f"""<body>
<main>
  <p class="crumb"><a href="/">eng_navi 英語クイズ</a> › <a href="/q/">問題一覧</a> › No.{q['no']}</p>
  <p class="num">{q['no']}</p>
  <p class="series">{e(t['title'])}</p>
  {body_q}
  <details>
    <summary>{summary}</summary>
    {answer}
    <p class="full">{e(completed(q))}</p>
    <p class="ja"><span class="ja-tag">訳</span>{e(q.get('translation', ''))}</p>
    {audio}
    {f'<ul class="gloss">{gloss}</ul>' if gloss else ''}
    <div class="exp">{tag}
{e(q.get('explanation', ''))}</div>
    <div id="nudge" data-no="{q['no']}" data-series="{SERIES_KEY[s]}" data-category="{e(q.get('category', ''))}"></div>
  </details>
  <a class="cta" href="/?q={q['no']}">この問題からクイズで解く</a>
  {reel}
  {pager}
""" + FOOT


def index_page(quizzes):
    groups = {k: [q for q in quizzes if series_of(q) == k] for k in ("blue", "green", "pink")}
    blocks = ""
    for k, qs in groups.items():
        items = "".join(
            f'<li><a href="/q/{q["no"]}/"><small>No.{q["no"]}</small>{e(q["question"] if "options" in q else q["target"])}</a></li>'
            for q in reversed(qs))
        blocks += f'<section class="list"><h2>{e(SERIES[k]["title"])}({len(qs)}問)</h2><ul>{items}</ul></section>'
    style = STYLE % SERIES["blue"]
    title = f"問題一覧|TOEIC・英検の英文法クイズ{len(quizzes)}問|eng_navi"
    desc = f"Instagram @eng_navi のリールで出題した英文法クイズ{len(quizzes)}問の一覧。TOEIC・英検2級・イディオムの問題を、答えと解説つきで無料公開しています。"
    return HEAD.format(title=e(title), desc=e(desc), url=f"{SITE_URL}/q/", site=SITE_URL, style=style) + f"""<body>
<main>
  <p class="crumb"><a href="/">eng_navi 英語クイズ</a> › 問題一覧</p>
  <h1 style="font-family:inherit;font-weight:700;font-size:24px">英文法クイズ 問題一覧</h1>
  <p class="ja">{e(desc)}</p>
  <a class="cta" href="/">クイズで解く</a>
  {blocks}
""" + FOOT


def build(site, quizzes):
    nos = [q["no"] for q in quizzes]
    for i, q in enumerate(quizzes):
        d = site / "q" / str(q["no"])
        d.mkdir(parents=True, exist_ok=True)
        prev_no = nos[i - 1] if i > 0 else None
        next_no = nos[i + 1] if i + 1 < len(nos) else None
        (d / "index.html").write_text(question_page(q, prev_no, next_no, (site / "audio" / f"q{q['no']}.mp3").exists()))
    (site / "q" / "index.html").write_text(index_page(quizzes))
    today = date.today().isoformat()
    urls = [f"{SITE_URL}/", f"{SITE_URL}/q/"] + [f"{SITE_URL}/q/{n}/" for n in nos]
    # フレーズ集・4コマのページも載せる
    for sub in ("list", "manga"):
        if (site / sub / "index.html").exists():
            urls.append(f"{SITE_URL}/{sub}/")
        urls += [f"{SITE_URL}/{sub}/{d.name}/" for d in sorted((site / sub).glob("*/")) if (d / "index.html").exists()]
    (site / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    (site / "robots.txt").write_text(f"User-agent: *\nAllow: /\nDisallow: /links/\nSitemap: {SITE_URL}/sitemap.xml\n")
    return len(nos)
