"""勉強法のページ docs/study/ を study_posts.py から作る。"""
import html
from pathlib import Path
from study_posts import ARTICLES
ROOT = Path(__file__).parent; OUT = ROOT / "docs" / "study"; e = html.escape
CSS = """body{background:#f4f1ea;color:#1b211d;font-family:"Noto Sans JP",system-ui,sans-serif;line-height:1.9;margin:0}
main{max-width:680px;margin:0 auto;padding:24px 16px 64px}h1{font-size:25px;line-height:1.5}h2{font-size:18px;margin-top:28px}
.step{background:#fffdf8;border:1px solid #e3ddd0;border-radius:14px;padding:14px 16px;margin-top:12px}.step b{color:#45613f}
.list a{display:block;background:#fffdf8;border:1px solid #e3ddd0;border-radius:12px;padding:12px 14px;margin-top:10px;color:#1b211d;text-decoration:none}
.lead{color:#6a6f69;font-size:14px}.cta{margin-top:28px;background:#e9efe6;border-radius:12px;padding:14px;font-size:14px}.cta a{color:#45613f;font-weight:700}"""
def page(title, desc, body):
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>
<meta name="description" content="{e(desc)}"><style>{CSS}</style></head><body><script src="/nav.js"></script><main>{body}</main></body></html>"""
LABEL = {"howto": "やり方", "myth": "思い込みをほどく", "check": "チェックリスト"}
for a in ARTICLES:
    d = OUT / a["slug"]; d.mkdir(parents=True, exist_ok=True)
    steps = "".join(f'<div class="step"><b>{i}. {e(h)}</b><br>{e(t)}</div>' for i, (h, t) in enumerate(a["steps"], 1))
    body = f"""<p class="lead"><a href="/study/">← 英語の勉強法</a> ・ {LABEL[a['type']]}</p><h1>{e(a['title'])}</h1>{steps}
<h2>今日からやること</h2><p>{e(a['steps'][0][0])}。まずはこれだけでOK。</p>
<div class="cta">📚 毎日の復習には、無料の <a href="/tango/?utm_source=study">英単語ページ</a>(音声つき)と <a href="/?utm_source=study">英文法クイズ</a>。<br>
単語帳・問題集選びに迷ったら <a href="/go/?from=study#tango">目的別のおすすめ教材</a>(PR)もどうぞ。</div>"""
    (d / "index.html").write_text(page(f"{a['title']}|英語の勉強法", a["steps"][0][1], body))
items = "".join(f'<a href="/study/{a["slug"]}/"><b>{e(a["title"])}</b><br><span class="lead">{LABEL[a["type"]]}</span></a>' for a in ARTICLES)
(OUT / "index.html").write_text(page("英語の勉強法|eng_navi", "英単語の覚え方、続け方、勉強の順番など、すぐ試せる英語の勉強法。",
    '<h1>英語の勉強法</h1><p class="lead">単語の覚え方・続け方・勉強の順番。すぐ試せるものだけを短くまとめています。</p><div class="list">' + items + "</div>"))
print(len(ARTICLES))
