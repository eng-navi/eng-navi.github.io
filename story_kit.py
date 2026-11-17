"""リンクスタンプつきストーリーの「半自動キット」。スマホで /kit/ を開き、画像を保存 → リンクをコピー → Instagram で貼るだけ。

    .venv-tts/bin/python story_kit.py      # kit.json から画像とページ(docs/kit/)を作る → push

リンクスタンプは Instagram の API では付けられないので、投稿だけ手でやる。
画像の下の方(y=1350〜1650)はリンクスタンプを置く場所として空けておく。
"""
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
KITS = ROOT / "kit.json"
OUT = ROOT / "docs" / "kit"
W, H = 1080, 1920
JP = "/System/Library/Fonts/ヒラギノ角ゴシック W7.ttc"
JP_R = "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc"


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(d, text, f, width):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n" or d.textlength(cur + ch, font=f) > width:
            lines.append(cur)
            cur = "" if ch == "\n" else ch
        else:
            cur += ch
    return lines + [cur]


def card(kit, path):
    im = Image.new("RGB", (W, H), "#f6f1e7")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 300], fill="#1f2a44")
    d.text((W // 2, 170), kit["badge"], font=font(JP, 64), fill="#ffd23f", anchor="mm")
    y = 420
    for ln in wrap(d, kit["hook"], font(JP, 84), W - 200):
        d.text((W // 2, y), ln, font=font(JP, 84), fill="#1f2a44", anchor="mm")
        y += 110
    y += 40
    d.rounded_rectangle([110, y, W - 110, y + 360], 36, fill="#ffffff", outline="#1f2a44", width=6)
    ty = y + 80
    for ln in wrap(d, kit["book"], font(JP, 54), W - 320)[:3]:
        d.text((W // 2, ty), ln, font=font(JP, 54), fill="#1f2a44", anchor="mm")
        ty += 72
    for ln in wrap(d, kit["note"], font(JP_R, 40), W - 320)[:2]:
        d.text((W // 2, ty + 10), ln, font=font(JP_R, 40), fill="#555", anchor="mm")
        ty += 56
    d.text((W // 2, 1300), "▼ リンクからチェック ▼", font=font(JP, 56), fill="#e8332a", anchor="mm")
    # y=1360〜1640 はリンクスタンプを置く場所として空けておく
    d.text((W // 2, 1800), kit.get("pr", "#PR"), font=font(JP_R, 36), fill="#888", anchor="mm")
    im.save(path, quality=92)


PAGE = """<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>ストーリーキット</title>
<style>body{{font-family:-apple-system,sans-serif;background:#f6f1e7;margin:0;padding:16px;color:#1f2a44}}
.k{{background:#fff;border-radius:16px;padding:16px;margin:0 0 20px}}img{{width:100%;border-radius:12px}}
button{{font-size:17px;padding:12px 16px;border-radius:10px;border:0;background:#1f2a44;color:#fff;margin:8px 8px 0 0}}
.s{{font-size:14px;color:#666;word-break:break-all}}</style></head><body>
<h1 style="font-size:22px">ストーリーキット(リンクスタンプ用)</h1>
<p class="s">① 画像を長押しして保存 → ② 「リンクをコピー」 → ③ Instagram のストーリーで画像を選び、リンクスタンプに貼る</p>
{items}
<script>function cp(t,b){{navigator.clipboard.writeText(t).then(()=>{{b.textContent="コピーしました✓"}})}}</script>
</body></html>"""


def build():
    kits = json.loads(KITS.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    items = []
    for k in sorted(kits, key=lambda k: k["date"], reverse=True):
        img = f"{k['id']}.jpg"
        card(k, OUT / img)
        items.append(f"""<div class="k"><b>{k['date']}|{k['account']}</b><br><img src="{img}" alt="">
<button onclick="cp('{k['link']}',this)">リンクをコピー</button><button onclick="cp('{k['sticker']}',this)">スタンプの文字をコピー</button>
<p class="s">スタンプの文字:{k['sticker']}<br>リンク:{k['link']}</p></div>""")
    (OUT / "index.html").write_text(PAGE.format(items="\n".join(items)))
    print(f"✓ {len(kits)} 件 → docs/kit/")


if __name__ == "__main__":
    build()
    subprocess.run(["git", "add", "docs/kit", "kit.json"], cwd=ROOT)
