"""本の紹介ストーリー(Book Review 風)を作る。

    python3 story_book.py      # out/story/sale_horikoshi.png

方眼の背景に、手書き風の見出しと短いコメント。下はリンクスタンプ(白地に青字)を置く帯。
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).parent
F = ROOT / "fonts"
W, H = 1080, 1920
PAPER = (245, 243, 239)
GRID = (222, 220, 215)
INK = (40, 40, 40)
RED = (200, 52, 48)
BAND = (210, 72, 66)  # リンクスタンプを置く帯(白いスタンプが映える色)


def font(name, size):
    return ImageFont.truetype(str(F / name), size)


EN = lambda s: font("Kalam-Bold.ttf", s)
JP = lambda s: font("KleeOne-SemiBold.ttf", s)


def curve(p0, p1, p2, n=30):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]


def arrow(d, pts, color=INK, w=4, head=20):
    d.line(pts, fill=color, width=w, joint="curve")
    (x0, y0), (x1, y1) = pts[-3], pts[-1]
    a = math.atan2(y1 - y0, x1 - x0)
    for s in (0.55, -0.55):
        d.line([(x1, y1), (x1 - head * math.cos(a + s), y1 - head * math.sin(a + s))], fill=color, width=w)


def underline(d, x0, x1, y, color=RED, w=4):
    d.line(curve((x0, y + 2), ((x0 + x1) / 2, y - 6), (x1, y + 3)), fill=color, width=w)


def star(d, cx, cy, r, color=RED, w=3):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.line(pts + [pts[0]], fill=color, width=w, joint="curve")


def note(d, xy, title, body, anchor_x="mm"):
    x, y = xy
    d.text((x, y), title, font=JP(42), fill=INK, anchor="ms")
    tw = d.textlength(title, font=JP(42))
    underline(d, x - tw / 2 - 6, x + tw / 2 + 6, y + 12)
    for i, line in enumerate(body):
        d.text((x, y + 70 + i * 52), line, font=JP(38), fill=INK, anchor="ms")


def main(cover_path, out_path):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    for x in range(0, W, 54):
        d.line([(x, 0), (x, H)], fill=GRID, width=2)
    for y in range(0, H, 54):
        d.line([(0, y), (W, y)], fill=GRID, width=2)

    # 見出し
    d.text((W // 2, 230), "Book Review", font=EN(122), fill=INK, anchor="ms")
    for side in (-1, 1):
        cx = W // 2 + side * 365
        for dy, ln in ((-62, 46), (-30, 56), (2, 46)):
            ang = dy / 140
            d.line([(cx, 190 + dy), (cx + side * ln * math.cos(ang), 190 + dy + ln * math.sin(ang) * 0.6)], fill=RED, width=6)
    d.text((W // 2, 330), "10月のおすすめ", font=JP(50), fill=RED, anchor="ms")
    d.ellipse([W // 2 - 205, 270, W // 2 + 205, 360], outline=RED, width=4)
    d.text((W - 70, 120), "PR", font=EN(40), fill=(120, 120, 120), anchor="ms")
    star(d, 110, 330, 22)
    star(d, 160, 380, 13)
    star(d, 960, 330, 18)

    # 表紙(白いふち+影)
    cov = Image.open(cover_path).convert("RGB")
    cw = 480
    cov = cov.resize((cw, int(cov.height * cw / cov.width)))
    framed = Image.new("RGB", (cov.width + 28, cov.height + 28), (255, 255, 255))
    framed.paste(cov, (14, 14))
    sh = Image.new("RGBA", (framed.width + 120, framed.height + 120), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([60, 74, framed.width + 60, framed.height + 74], fill=(0, 0, 0, 70))
    sh = sh.filter(ImageFilter.GaussianBlur(26)).rotate(-2, expand=True, resample=Image.BICUBIC)
    fr = framed.convert("RGBA").rotate(-2, expand=True, resample=Image.BICUBIC)
    cx, cy = W // 2, 880
    img.paste(sh, (cx - sh.width // 2, cy - sh.height // 2 + 8), sh)
    img.paste(fr, (cx - fr.width // 2, cy - fr.height // 2), fr)
    d = ImageDraw.Draw(img)

    # まわりのメモ(左右2つずつ、余白をたっぷり)
    note(d, (150, 560), "Point", ["英文を", "カタマリで", "読む"])
    arrow(d, curve((205, 745), (225, 800), (270, 820)))
    note(d, (935, 680), "動画", ["授業動画", "42本つき"])
    arrow(d, curve((935, 810), (920, 860), (840, 880)))
    note(d, (150, 1080), "For", ["長文で", "迷子に", "なる人"])
    arrow(d, curve((215, 1270), (250, 1300), (270, 1250)))
    note(d, (935, 1120), "Would I", ["recommend?"])
    d.text((875, 1255), "Yes", font=EN(46), fill=INK, anchor="ms")
    d.ellipse([826, 1205, 926, 1272], outline=RED, width=4)
    d.text((990, 1255), "No", font=EN(46), fill=INK, anchor="ms")

    # ひとこと
    d.text((W // 2, 1395), "「なんとなく読む」を卒業したい人へ", font=JP(44), fill=INK, anchor="ms")
    underline(d, 200, 880, 1415, w=3)

    # 割引のバッジ(表紙の右上に貼ったシール風)
    bx, by, br = 830, 470, 92
    d.ellipse([bx - br, by - br, bx + br, by + br], fill=RED)
    d.ellipse([bx - br + 9, by - br + 9, bx + br - 9, by + br - 9], outline=(255, 255, 255), width=3)
    d.text((bx, by - 22), "Kindle版", font=JP(28), fill=(255, 255, 255), anchor="ms")
    d.text((bx, by + 30), "50%", font=EN(62), fill=(255, 255, 255), anchor="ms")
    d.text((bx, by + 62), "OFF", font=EN(30), fill=(255, 255, 255), anchor="ms")

    # ボタンの上のマイクロコピー(背中を押す一言)
    d.text((W // 2, 1490), "＼ 今だけ Kindle版が半額 ／", font=JP(48), fill=RED, anchor="ms")
    d.text((W // 2, 1540), "期間限定キャンペーン・残り11日(10/25時点)", font=JP(30), fill=(110, 110, 110), anchor="ms")

    # リンクスタンプを置く帯(左右いっぱい)
    top = 1590
    d.rectangle([0, top, W, top + 250], fill=BAND)
    d.text((W // 2, top + 70), "▼ 中身をのぞいてみる", font=JP(44), fill=(255, 255, 255), anchor="ms")
    bx0, by0, bx1, by1 = W // 2 - 250, top + 110, W // 2 + 250, top + 205
    for x in range(bx0, bx1, 22):
        d.line([(x, by0), (min(x + 11, bx1), by0)], fill=(255, 255, 255), width=3)
        d.line([(x, by1), (min(x + 11, bx1), by1)], fill=(255, 255, 255), width=3)
    for y in range(by0, by1, 22):
        d.line([(bx0, y), (bx0, min(y + 11, by1))], fill=(255, 255, 255), width=3)
        d.line([(bx1, y), (bx1, min(y + 11, by1))], fill=(255, 255, 255), width=3)
    d.text((W // 2, (by0 + by1) // 2 + 12), "ここにリンクスタンプ", font=JP(34), fill=(255, 235, 233), anchor="ms")

    img.save(out_path)
    print(f"✓ {out_path}")


if __name__ == "__main__":
    main(ROOT / "out" / "story" / "_cover_horikoshi.png", ROOT / "out" / "story" / "sale_horikoshi.png")
