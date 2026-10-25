"""「BOOK PICK!」系の本紹介ストーリー(手書きの味を強めた3案)。

    python3 story_pick.py      # out/story/pick_1.png / pick_2.png / pick_3.png

大きな文字はマーカー、メモはペン書き、線は少し揺れる手書きの線。下はリンクスタンプ用の赤い帯。
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).parent
F = ROOT / "fonts"
OUT = ROOT / "out" / "story"
COVER = OUT / "_cover_horikoshi.png"
W, H = 1080, 1920
WALL = (236, 234, 230)
INK = (22, 22, 22)
BROWN = (176, 98, 32)
BLUE = (48, 66, 170)
RED = (206, 70, 62)


def font(name, size, weight=None):
    f = ImageFont.truetype(str(F / name), size)
    if weight:
        f.set_variation_by_axes([weight])
    return f


MARKER = lambda s: font("PermanentMarker-Regular.ttf", s)
PEN = lambda s: font("Caveat.ttf", s, 600)
JP = lambda s: font("ZenKurenaido-Regular.ttf", s)


# ---- 手書きの線 ----
def wobble(pts, amp=2.2, seed=0):
    """点の列を少し揺らして、手で引いた線にする。"""
    rnd = random.Random(seed)
    out, phase = [], rnd.random() * 6
    for i, (x, y) in enumerate(pts):
        out.append((x + amp * math.sin(i * 0.7 + phase) + rnd.uniform(-0.6, 0.6),
                    y + amp * math.cos(i * 0.55 + phase) + rnd.uniform(-0.6, 0.6)))
    return out


def bezier(p0, p1, p2, n=40):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]


def pen_line(d, pts, color, w=4, seed=0):
    d.line(wobble(pts, seed=seed), fill=color, width=w, joint="curve")


def pen_arrow(d, p0, p1, p2, color, w=4, seed=0):
    pts = wobble(bezier(p0, p1, p2), seed=seed)
    d.line(pts, fill=color, width=w, joint="curve")
    (x0, y0), (x1, y1) = pts[-5], pts[-1]
    a = math.atan2(y1 - y0, x1 - x0)
    for s, ln in ((0.5, 22), (-0.62, 18)):  # 左右で少し長さを変えて手書きっぽく
        d.line([(x1, y1), (x1 - ln * math.cos(a + s), y1 - ln * math.sin(a + s))], fill=color, width=w)


def pen_ellipse(d, cx, cy, rx, ry, color, w=4, seed=0, tilt=-0.15):
    """少しずれて閉じる、手で描いた楕円。"""
    rnd = random.Random(seed)
    pts = []
    for i in range(0, 380, 6):
        a = math.radians(i)
        r = 1 + 0.04 * math.sin(a * 3 + seed)
        x, y = rx * r * math.cos(a), ry * r * math.sin(a)
        pts.append((cx + x * math.cos(tilt) - y * math.sin(tilt), cy + x * math.sin(tilt) + y * math.cos(tilt) + i * 0.02))
    d.line(wobble(pts, amp=1.2, seed=rnd.randint(0, 99)), fill=color, width=w, joint="curve")


def heart(d, cx, cy, s, color, w=4):
    pts = [(cx + s * 16 * math.sin(t) ** 3 / 16, cy - s * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 16)
           for t in (i / 30 * 2 * math.pi for i in range(31))]
    d.line(wobble(pts, amp=0.8), fill=color, width=w, joint="curve")


def asterisk(d, cx, cy, r, color, w=4):
    for a in (0, 60, 120):
        t = math.radians(a)
        d.line([(cx - r * math.cos(t), cy - r * math.sin(t)), (cx + r * math.cos(t), cy + r * math.sin(t))], fill=color, width=w)


# ---- 文字 ----
def tilted(img, xy, text, f, color, angle, anchor="mm"):
    """文字を傾けて置く(マーカーで書いた大きな文字に使う)。"""
    box = ImageDraw.Draw(img).textbbox((0, 0), text, font=f)
    w, h = box[2] - box[0] + 40, box[3] - box[1] + 40
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((20 - box[0], 20 - box[1]), text, font=f, fill=color)
    layer = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    x, y = xy
    img.paste(layer, (int(x - layer.width / 2), int(y - layer.height / 2)), layer)


def arc_text(img, text, cx, cy, r, start, end, f, color, side):
    """円弧に沿って1文字ずつ並べる(お手本の LATEST READS! のように本を囲む)。
    side="left" は下から上へ、side="right" は上から下へ読む。角度は画面座標(下向きが正)。"""
    n = len(text)
    for i, ch in enumerate(text):
        deg = start + (end - start) * (i / max(1, n - 1))
        a = math.radians(deg)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        rot = 270 - deg if side == "left" else -90 - deg
        tilted(img, (x, y), ch, f, color, rot)


def note(d, xy, text, f, color, spacing=6, rot=None):
    d.multiline_text(xy, text, font=f, fill=color, spacing=spacing)


# ---- 部品 ----
def wall():
    rnd = random.Random(5)
    img = Image.new("RGB", (W, H), WALL)
    px = img.load()
    for _ in range(110000):
        x, y = rnd.randrange(W), rnd.randrange(H)
        v = rnd.randint(-10, 10)
        r, g, b = px[x, y]
        px[x, y] = (r + v, g + v, b + v)
    img = img.filter(ImageFilter.GaussianBlur(2.4))
    shade = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shade).ellipse([-500, -200, 400, H + 200], fill=70)
    return Image.composite(Image.new("RGB", (W, H), (205, 203, 199)), img, shade.filter(ImageFilter.GaussianBlur(200)))


def cover(img, cx, cy, width, angle):
    cov = Image.open(COVER).convert("RGB")
    cov = cov.resize((width, int(cov.height * width / cov.width)))
    sh = Image.new("RGBA", (cov.width + 160, cov.height + 160), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([80, 100, cov.width + 80, cov.height + 104], fill=(0, 0, 0, 105))
    sh = sh.filter(ImageFilter.GaussianBlur(30)).rotate(angle, expand=True, resample=Image.BICUBIC)
    cv = cov.convert("RGBA").rotate(angle, expand=True, resample=Image.BICUBIC)
    img.paste(sh, (cx - sh.width // 2 + 12, cy - sh.height // 2 + 16), sh)
    img.paste(cv, (cx - cv.width // 2, cy - cv.height // 2), cv)
    return cv.size


def button(img, top, lead1="＼ 今だけ Kindle版が半額 ／", lead2="期間限定・残り11日(10/25時点)"):
    d = ImageDraw.Draw(img)
    d.text((W // 2, top - 70), lead1, font=JP(50), fill=RED, anchor="ms")
    d.text((W // 2, top - 22), lead2, font=JP(30), fill=(70, 70, 70), anchor="ms")
    d.rectangle([0, top, W, top + 240], fill=RED)
    d.text((W // 2, top + 70), "▼ 中身をのぞいてみる", font=JP(46), fill=(255, 255, 255), anchor="ms")
    bx0, by0, bx1, by1 = W // 2 - 240, top + 108, W // 2 + 240, top + 198
    for x in range(bx0, bx1, 22):
        d.line([(x, by0), (min(x + 11, bx1), by0)], fill=(255, 255, 255), width=3)
        d.line([(x, by1), (min(x + 11, bx1), by1)], fill=(255, 255, 255), width=3)
    for y in range(by0, by1, 22):
        d.line([(bx0, y), (bx0, min(y + 11, by1))], fill=(255, 255, 255), width=3)
        d.line([(bx1, y), (bx1, min(y + 11, by1))], fill=(255, 255, 255), width=3)
    d.text((W // 2, (by0 + by1) // 2 + 12), "ここにリンクスタンプ", font=JP(34), fill=(255, 232, 228), anchor="ms")
    d.text((W - 60, 96), "PR", font=MARKER(36), fill=INK, anchor="ms")


def bubble(d, cx, cy, tag, color, seed):
    pen_ellipse(d, cx, cy, 78, 44, color, seed=seed)
    d.text((cx, cy + 14), tag, font=PEN(52), fill=color, anchor="ms")


# ---- 案1:お手本どおり、本を囲む弧の文字+吹き出し ----
def pick_1():
    img = wall()
    cover(img, 540, 990, 390, -4)
    arc_text(img, "BOOK", 540, 990, 410, 145, 213, MARKER(138), INK, "left")
    arc_text(img, "PICK!", 540, 990, 410, -42, 42, MARKER(138), INK, "right")
    d = ImageDraw.Draw(img)
    asterisk(d, 960, 600, 18, INK)
    bubble(d, 200, 380, "Video", BROWN, 1)
    note(d, (290, 330), "授業動画が42本!\n本だけで終わらない", JP(40), BROWN)
    pen_arrow(d, (210, 430), (230, 560), (330, 650), BROWN, seed=2)
    bubble(d, 640, 210, "Read", BLUE, 3)
    note(d, (730, 160), "英文を\n「カタマリ」で\nつかめる", JP(40), BLUE)
    pen_arrow(d, (640, 260), (560, 420), (560, 600), BLUE, seed=4)
    bubble(d, 190, 1370, "For", BROWN, 5)
    note(d, (285, 1325), "長文で迷子になる人へ。\n大人の学び直しにも♡", JP(40), BROWN)
    pen_arrow(d, (200, 1325), (230, 1290), (300, 1275), BROWN, seed=6)
    tilted(img, (790, 1520), "Kindle 50% OFF", MARKER(52), RED, -5)
    button(img, 1680)
    return img


# ---- 案2:ビフォー・アフター(読み方が変わる) ----
def pick_2():
    img = wall()
    cover(img, 560, 960, 430, 5)
    tilted(img, (300, 210), "BEFORE", MARKER(110), INK, 4)
    tilted(img, (790, 1460), "AFTER!", MARKER(120), INK, -4)
    d = ImageDraw.Draw(img)
    note(d, (110, 300), "単語も文法もわかるのに、\n長い英文で迷子になる…", JP(42), BROWN)
    pen_line(d, bezier((110, 410), (300, 425), (520, 405)), BROWN, seed=1)
    pen_arrow(d, (200, 430), (180, 560), (330, 650), BROWN, seed=2)
    heart(d, 960, 560, 2.2, RED)
    note(d, (90, 1230), "英文が\n「カタマリ」で\n見えるように!", JP(44), BLUE)
    pen_arrow(d, (240, 1220), (300, 1150), (360, 1120), BLUE, seed=3)
    bubble(d, 860, 600, "Video", BLUE, 4)
    note(d, (770, 660), "解説動画\n42本つき", JP(40), BLUE)
    pen_arrow(d, (820, 760), (800, 800), (770, 820), BLUE, seed=5)
    asterisk(d, 110, 1150, 16, INK)
    tilted(img, (270, 1495), "Kindle 50% OFF", MARKER(52), RED, -5)
    button(img, 1680)
    return img


# ---- 案3:My notes(本に付せんとメモを貼った感じ) ----
def sticky(img, x, y, w, h, color, angle, lines, f, ink):
    pad = Image.new("RGBA", (w, h), color + (255,))
    pd = ImageDraw.Draw(pad)
    pd.multiline_text((24, 22), lines, font=f, fill=ink, spacing=8)
    # 上にマスキングテープ
    tape = Image.new("RGBA", (130, 38), (255, 255, 255, 150))
    pad.alpha_composite(tape, ((w - 130) // 2, 0))
    sh = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([30, 38, w + 30, h + 38], fill=(0, 0, 0, 55))
    sh = sh.filter(ImageFilter.GaussianBlur(12)).rotate(angle, expand=True, resample=Image.BICUBIC)
    pad = pad.rotate(angle, expand=True, resample=Image.BICUBIC)
    img.paste(sh, (x - 30, y - 22), sh)
    img.paste(pad, (x, y), pad)


def pick_3():
    img = wall()
    cover(img, 560, 940, 470, -3)
    tilted(img, (540, 200), "MY NOTES", MARKER(120), INK, -3)
    d = ImageDraw.Draw(img)
    pen_line(d, bezier((300, 270), (540, 290), (790, 262)), RED, w=6, seed=1)
    sticky(img, 60, 430, 330, 230, (255, 236, 160), 5, "英文を\n「カタマリ」で\n読む練習", JP(40), INK)
    sticky(img, 720, 520, 310, 200, (205, 226, 240), -6, "授業動画\n42本つき!", JP(42), INK)
    sticky(img, 70, 1230, 360, 220, (250, 212, 214), -4, "長文で迷子に\nなる人に\nいちばん効く", JP(40), INK)
    d = ImageDraw.Draw(img)
    note(d, (740, 1250), "Would I\nrecommend?", PEN(58), BLUE, spacing=0)
    d.text((770, 1440), "YES", font=MARKER(54), fill=BLUE)
    pen_ellipse(d, 822, 1474, 82, 46, BLUE, seed=7)
    d.text((910, 1440), "no", font=PEN(52), fill=BLUE)
    heart(d, 990, 1250, 2, RED)
    tilted(img, (500, 1500), "Kindle 50% OFF", MARKER(54), RED, 2)
    button(img, 1680)
    return img


if __name__ == "__main__":
    for i, fn in enumerate((pick_1, pick_2, pick_3), 1):
        fn().save(OUT / f"pick_{i}.png")
        print(f"✓ out/story/pick_{i}.png")
