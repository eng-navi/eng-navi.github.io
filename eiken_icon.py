"""@eiken_reading_club(英検リーディング部)のプロフィール画像候補。配色はネイビー/青/クリーム/サンド。"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math
ROOT = Path(__file__).parent; F = ROOT / "fonts"
OUT = ROOT / "out" / "eiken" / "icons"; OUT.mkdir(parents=True, exist_ok=True)
NAVY, BLUE, CREAM, SAND = (31, 55, 92), (92, 126, 166), (244, 239, 228), (214, 190, 150)
S = 1080; C = S // 2
def pf(s, w=700):
    f = ImageFont.truetype(str(F / "PlayfairDisplay-Italic.ttf"), s); f.set_variation_by_axes([w]); return f
def mc(s): return ImageFont.truetype(str(F / "ShipporiMinchoB1-ExtraBold.ttf"), s)
def go(s, w=900):
    f = ImageFont.truetype(str(F / "NotoSansJP.ttf"), s); f.set_variation_by_axes([w]); return f
def canvas(bg): im = Image.new("RGB", (S, S), bg); return im, ImageDraw.Draw(im)
def sparkle(d, cx, cy, r, col):
    pts = []
    for i in range(8):
        a = math.radians(i * 45 - 90); rr = r if i % 2 == 0 else r * 0.28
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=col)
def flower(d, cx, cy, r, col, w=8):
    for i in range(5):
        a = math.radians(i * 72 - 90); px, py = cx + r * 0.62 * math.cos(a), cy + r * 0.62 * math.sin(a)
        d.ellipse((px - r * .42, py - r * .42, px + r * .42, py + r * .42), outline=col, width=w)
    d.ellipse((cx - r * .18, cy - r * .18, cx + r * .18, cy + r * .18), fill=col)
def pill(d, cx, cy, text, f, fg, bg, padx=40, pady=16):
    l, t, r, b = d.textbbox((0, 0), text, font=f); w, h = r - l, b - t
    d.rounded_rectangle((cx - w / 2 - padx, cy - h / 2 - pady, cx + w / 2 + padx, cy + h / 2 + pady), radius=h, fill=bg)
    d.text((cx, cy), text, font=f, fill=fg, anchor="mm")

# 1 ネイビー地・明朝の「英検」+サンドの「読」バッジ感
im, d = canvas(NAVY)
d.text((C, C - 70), "英検", font=mc(330), fill=CREAM, anchor="mm")
pill(d, C, C + 200, "リーディング部", go(70, 800), NAVY, SAND)
sparkle(d, 250, 270, 46, SAND); sparkle(d, 840, 820, 34, SAND); im.save(OUT / "icon1_navy_eiken.png")
# 2 クリーム地・筆記体 Reading + 英検 の札
im, d = canvas(CREAM)
d.text((C, C - 40), "Reading", font=pf(250, 800), fill=NAVY, anchor="mm")
pill(d, C, C + 170, "英検 部", go(96, 900), CREAM, NAVY, 50, 18)
flower(d, 260, 300, 70, BLUE, 7); sparkle(d, 830, 300, 42, SAND); im.save(OUT / "icon2_cream_reading.png")
# 3 青地・本の絵+「英」
im, d = canvas(BLUE)
cy = C + 10
d.polygon([(C, cy - 190), (C - 330, cy - 250), (C - 330, cy + 160), (C, cy + 220)], fill=CREAM)
d.polygon([(C, cy - 190), (C + 330, cy - 250), (C + 330, cy + 160), (C, cy + 220)], fill=(232, 224, 207))
d.line((C, cy - 190, C, cy + 220), fill=NAVY, width=10)
d.text((C - 165, cy - 15), "英", font=mc(260), fill=NAVY, anchor="mm")
d.text((C + 165, cy - 15), "検", font=mc(260), fill=NAVY, anchor="mm")
sparkle(d, 860, 200, 50, CREAM); sparkle(d, 210, 870, 34, SAND); im.save(OUT / "icon3_book.png")
# 4 ネイビー丸バッジ・大きい「部」(部活感)
im, d = canvas(CREAM)
d.ellipse((90, 90, S - 90, S - 90), fill=NAVY); d.ellipse((130, 130, S - 130, S - 130), outline=SAND, width=8)
d.text((C, C - 40), "部", font=mc(440), fill=CREAM, anchor="mm")
d.text((C, C + 225), "Eiken Reading", font=pf(64, 700), fill=SAND, anchor="mm")
sparkle(d, 300, 300, 34, SAND); sparkle(d, 790, 300, 34, SAND); im.save(OUT / "icon4_bu_badge.png")
# 5 サンド地・筆記体 Eiken + 準1・2級
im, d = canvas(SAND)
d.text((C, C - 80), "Eiken", font=pf(300, 800), fill=NAVY, anchor="mm")
pill(d, C, C + 170, "準1級・2級", go(84, 900), CREAM, NAVY, 46, 16)
flower(d, 830, 260, 64, CREAM, 7); sparkle(d, 230, 820, 44, NAVY); im.save(OUT / "icon5_sand_eiken.png")
# 丸く切り抜いた一覧
fs = sorted(OUT.glob("icon*.png")); t = 300; sheet = Image.new("RGB", (t * 5 + 120, t + 40), "white")
mask = Image.new("L", (t, t), 0); ImageDraw.Draw(mask).ellipse((0, 0, t - 1, t - 1), fill=255)
for i, f in enumerate(fs): sheet.paste(Image.open(f).resize((t, t)), (20 + i * (t + 20), 20), mask)
sheet.save(OUT / "preview.png")
