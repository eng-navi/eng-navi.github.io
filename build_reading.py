"""TOEIC読解の復習ページ docs/reading/ を toeic_problems.py から作る(投稿済み・予約分)。"""
import json, html
from pathlib import Path
from toeic_problems import PROBLEMS
ROOT = Path(__file__).parent; OUT = ROOT / "docs" / "reading"; OUT.mkdir(parents=True, exist_ok=True)
sched = {s["key"] for s in json.loads((ROOT / "toeic_schedule.json").read_text())}
e = html.escape
CSS = """:root{--bg:#EEE8D6;--card:#FAF7EE;--ink:#0B0B0B;--red:#CF3E22;--sub:#6e6a62;--mark:#F0B2A0}
*{box-sizing:border-box;margin:0;padding:0}body{background:var(--bg);color:var(--ink);font-family:"Noto Sans JP",system-ui,sans-serif;line-height:1.8}
main{max-width:720px;margin:0 auto;padding:24px 16px 64px}h1{font-size:26px;margin:8px 0 4px}h2{font-size:18px;margin:28px 0 8px}
.lead{color:var(--sub);font-size:14px}.q{background:var(--card);border:2px solid var(--ink);margin-top:14px}
.q .bar{background:var(--ink);color:#EEE8D6;font-weight:700;padding:6px 14px;display:flex;justify-content:space-between;font-size:14px}
.q .body{padding:16px;font-family:"Source Serif 4",Georgia,serif;font-size:18px}.q .head{color:var(--sub);font-size:15px}
mark{background:var(--mark)}.n{color:var(--red);font-weight:700}details{margin-top:10px;background:var(--card);border-radius:10px;padding:10px 14px}
summary{cursor:pointer;font-weight:700}.ans{display:inline-block;background:var(--red);color:#fff;padding:0 10px;font-weight:700;margin:6px 0}
.list a{display:flex;gap:10px;background:var(--card);margin-top:8px;padding:12px 14px;border-radius:10px;color:var(--ink);text-decoration:none}
.list b{color:var(--red);min-width:52px}.pr{margin-top:28px;font-size:14px}.pr a{color:var(--red)}"""
def page(title, desc, body):
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&family=Source+Serif+4:wght@400;600&display=swap" rel="stylesheet"><style>{CSS}</style></head>
<body><script src="/nav.js"></script><main>{body}
<p class="pr">📚 Part 7 の問題集・アプリは <a href="/go/?from=reading#toeic">おすすめ教材</a> から(PR)</p></main><script src="/recommend.js"></script></body></html>"""
def passage(Q, hl=()):
    out = [f'<div class="head">{e(h)}</div>' for h in Q["passage"]["head"]]
    for para in Q["passage"]["body"]:
        s = " ".join((f'<span class="n">{"❶❷❸❹❺"[t-1]}</span> ' if t else "") + (f"<mark>{e(x)}</mark>" if t in hl else e(x)) for x, t in para)
        out.append(f"<p>{s}</p>")
    return "".join(out)
items = []
for Q in PROBLEMS:
    key = f"toeic_{Q['no']:03d}"
    if key not in sched: continue
    hl = Q["explain"][0]["hl"]
    ch = "".join(f"<p>({'AB'[i]}) {e(c)}</p>" for i, (c, _) in enumerate(Q["choices"]))
    ex = "".join(f"<details{' open' if k == 0 else ''}><summary>{t}</summary><p>{e(x['text']).replace(chr(10), '<br>')}</p></details>"
                 for k, (t, x) in enumerate(zip(("答えと根拠", "ワナの選択肢", "解き方のコツ"), Q["explain"])))
    words = "".join(f"<p><b>{e(a)}</b> … {e(b)}</p>" for a, b in Q["words"])
    body = f"""<p class="lead"><a href="/reading/">← 30秒TOEIC読解の一覧</a></p><h1>No.{Q['no']:02d} {e(Q['type'])}</h1>
<p class="lead">目安{Q['sec']}秒。英文を読んで、AかBか選んでみよう。</p>
<div class="q"><div class="bar"><span>{e(Q['passage']['kind'])}</span><span>⏱ 目安{Q['sec']}秒</span></div><div class="body">{passage(Q)}
<p style="margin-top:12px"><b>{e(Q['q'])}</b></p>{ch}</div></div>
<details><summary>答えを見る</summary><span class="ans">答え {Q['answer']}</span><div class="q"><div class="body">{passage(Q, hl)}</div></div>{ex}</details>
<details><summary>全文の和訳</summary><p>{e(Q['ja']).replace(chr(10), '<br>')}</p><p>設問:{e(Q['q_ja'])}</p>{''.join(f"<p>({'AB'[i]}) {e(c[1])}</p>" for i, c in enumerate(Q['choices']))}</details>
<h2>この問題の単語</h2>{words}"""
    (OUT / f"{Q['no']:03d}.html").write_text(page(f"TOEIC Part7 No.{Q['no']} {Q['type']}|30秒TOEIC読解", f"TOEIC Part 7 の{Q['type']}。和訳・根拠・ワナの解説つき。", body))
    items.append(f'<a href="/reading/{Q["no"]:03d}.html"><b>No.{Q["no"]:02d}</b><span>{e(Q["type"])}|{e(Q["point"].splitlines()[0])}</span></a>')
(OUT / "index.html").write_text(page("30秒TOEIC読解|Part7 長文リーディングの復習", "Instagram @toeic_read30 の問題を、和訳・根拠・ワナの解説つきで復習できるページ。",
    '<h1>30秒TOEIC読解</h1><p class="lead">Instagram @toeic_read30 の問題を、英文・和訳・解説つきで復習できます。すべてオリジナル問題です。</p><div class="list">' + "".join(reversed(items)) + "</div>"))
print(len(items), "pages")
