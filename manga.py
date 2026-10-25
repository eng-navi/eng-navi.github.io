"""イディオムのギャグ4コマ(カルーセル2枚:4コマ + 解説)。キャラクターは eng_navi オリジナル。

    python3 manga.py inside_out     # out/manga/inside_out_1.png, _2.png

ナビ:フクロウ(ツッコミ役)/ ペン:ペンギン(ボケ役)。参考にした漫画に出る動物(うさぎ・猫など)は使わない
"""
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
F = ROOT / "fonts"
OUT = ROOT / "out" / "manga"
W, H = 1080, 1350
INK = (45, 40, 38)
PAPER = (255, 253, 248)
YELLOW = (255, 214, 102)
PINK = (247, 168, 176)
METAL = (190, 190, 196)
WOOD = (238, 200, 150)
GREEN = (120, 170, 120)
CREAM = (250, 244, 228)
BLUSH = (250, 170, 170)

EN = lambda s: ImageFont.truetype(str(F / "Kalam-Bold.ttf"), s)
JP = lambda s: ImageFont.truetype(str(F / "KleeOne-SemiBold.ttf"), s)
SFX = lambda s: ImageFont.truetype(str(F / "PermanentMarker-Regular.ttf"), s)


def wob(pts, amp=1.6, seed=0):
    """手描き風に、線を少しだけ揺らす。"""
    r = random.Random(seed)
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 14))
        for i in range(n):
            t = i / n
            out.append((x0 + (x1 - x0) * t + r.uniform(-amp, amp), y0 + (y1 - y0) * t + r.uniform(-amp, amp)))
    out.append(pts[-1])
    return out


def rrect_pts(x0, y0, x1, y1, r, n=8):
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts + [pts[0]]


def shape(d, pts, fill, w=5, seed=0):
    d.polygon(pts, fill=fill)
    d.line(wob(pts, seed=seed), fill=INK, width=w, joint="curve")


def face(d, cx, cy, s, expr):
    ex, ey, er = s * 0.2, s * 0.02, max(4, s * 0.045)
    for side in (-1, 1):
        x = cx + side * ex
        if expr == "happy":
            d.arc([x - er * 2, ey + cy - er * 1.5, x + er * 2, ey + cy + er * 1.5], 200, 340, fill=INK, width=4)
        elif expr == "smug":
            d.line([(x - er * 1.8, cy + ey), (x + er * 1.8, cy + ey)], fill=INK, width=4)
        elif expr == "shock":
            d.ellipse([x - er * 2, cy + ey - er * 2, x + er * 2, cy + ey + er * 2], fill=(255, 255, 255), outline=INK, width=3)
            d.ellipse([x - er * 0.8, cy + ey - er * 0.8, x + er * 0.8, cy + ey + er * 0.8], fill=INK)
        else:
            d.ellipse([x - er, cy + ey - er * 1.2, x + er, cy + ey + er * 1.2], fill=INK)
        d.ellipse([x - s * 0.09 + side * s * 0.04, cy + s * 0.1, x + s * 0.05 + side * s * 0.04, cy + s * 0.16], fill=BLUSH)
    my = cy + s * 0.14
    if expr == "shock":
        d.ellipse([cx - s * 0.04, my, cx + s * 0.04, my + s * 0.08], fill=INK)
    elif expr == "smug":
        d.line([(cx - s * 0.05, my + 4), (cx + s * 0.06, my - 2)], fill=INK, width=4)
    else:
        d.arc([cx - s * 0.06, my - s * 0.05, cx + s * 0.06, my + s * 0.04], 20, 160, fill=INK, width=4)


def navi(d, cx, cy, s, expr="normal", cap_back=False, seed=1):
    """えんぴつの子。cy は顔の中心。"""
    bw = s * 0.62
    top, bottom = cy - s * 0.45, cy + s * 0.5
    # 消しゴム帽子と金具(裏返しのときは、金具が上で消しゴムが下)
    cap_color, band_color = (METAL, PINK) if cap_back else (PINK, METAL)
    shape(d, rrect_pts(cx - bw / 2 + 6, top - s * 0.32, cx + bw / 2 - 6, top - s * 0.08, s * 0.1), cap_color, seed=seed)
    shape(d, rrect_pts(cx - bw / 2, top - s * 0.12, cx + bw / 2, top + s * 0.04, 4), band_color, seed=seed + 1)
    shape(d, rrect_pts(cx - bw / 2, top, cx + bw / 2, bottom, s * 0.08), YELLOW, seed=seed + 2)
    for k in (-1, 1):
        d.line([(cx + k * bw * 0.18, top + 10), (cx + k * bw * 0.18, bottom - 10)], fill=(235, 190, 80), width=3)
    shape(d, [(cx - bw / 2, bottom - 4), (cx + bw / 2, bottom - 4), (cx, bottom + s * 0.42)], WOOD, seed=seed + 3)
    shape(d, [(cx - bw * 0.14, bottom + s * 0.29), (cx + bw * 0.14, bottom + s * 0.29), (cx, bottom + s * 0.42)], INK, w=3, seed=seed + 4)
    face(d, cx, cy, s, expr)


def book(d, cx, cy, s, expr="normal", flipped=False, seed=7):
    """本の子。flipped=True で表紙が裏返し(ページ側が外)。"""
    bw, bh = s * 0.86, s * 1.0
    x0, y0, x1, y1 = cx - bw / 2, cy - bh * 0.5, cx + bw / 2, cy + bh * 0.5
    cover = CREAM if flipped else GREEN
    shape(d, rrect_pts(x0, y0, x1, y1, s * 0.08), cover, seed=seed)
    if flipped:  # 本文の行(中身が外に出ている)と、ページのしま模様、内側にちらっと見える緑
        for i in range(1, 9):
            yy = y0 + (y1 - y0) * i / 9
            if abs(yy - (cy + s * 0.08)) > s * 0.17:
                d.line(wob([(x0 + s * 0.1, yy), (x1 - s * 0.22, yy)], amp=0.8, seed=seed + 20 + i), fill=(205, 198, 182), width=3)
        for i in range(1, 7):
            yy = y0 + (y1 - y0) * i / 7
            d.line(wob([(x1 - 6, yy), (x1 - s * 0.16, yy)], seed=seed + i), fill=(200, 190, 170), width=3)
        d.rectangle([x0 + 8, y1 - 18, x0 + 40, y1 - 8], fill=GREEN)
    else:
        d.line(wob([(x0 + s * 0.12, y0 + 8), (x0 + s * 0.12, y1 - 8)], seed=seed + 1), fill=(90, 135, 90), width=5)
        d.rectangle([cx - s * 0.16, y0 + s * 0.12, cx + s * 0.22, y0 + s * 0.2], fill=(200, 225, 200))
    face(d, cx + s * 0.04, cy + s * 0.05, s * 0.9, expr)

OWL = (176, 132, 96)
OWL_LIGHT = (232, 210, 180)
NAVY = (70, 82, 110)
ORANGE = (245, 160, 70)
HAT = (110, 160, 200)
HAT_IN = (190, 215, 232)


def hat(d, cx, top, w, flipped=False, seed=30):
    """ニット帽。flipped=True で裏返し(色が薄く、縫い目とタグが外に見える)。"""
    color = HAT_IN if flipped else HAT
    pts = [(cx - w / 2, top + w * 0.42)] + [(cx + w / 2 * math.cos(a), top + w * 0.42 - w * 0.48 * math.sin(a))
                                            for a in (math.pi - i * math.pi / 16 for i in range(17))]
    shape(d, pts + [pts[0]], color, seed=seed)
    shape(d, rrect_pts(cx - w / 2 - 6, top + w * 0.36, cx + w / 2 + 6, top + w * 0.52, 8), color, seed=seed + 1)
    if flipped:
        d.line(wob([(cx, top - w * 0.04), (cx, top + w * 0.36)], amp=1), fill=(140, 170, 190), width=3)
        tx, ty = cx + w * 0.18, top + w * 0.5
        shape(d, [(tx, ty), (tx + w * 0.16, ty), (tx + w * 0.16, ty + w * 0.22), (tx, ty + w * 0.22), (tx, ty)], (255, 255, 255), w=3, seed=seed + 2)
        d.text((tx + w * 0.08, ty + w * 0.11), "M", font=EN(int(w * 0.13)), fill=INK, anchor="mm")
    else:
        d.ellipse([cx - w * 0.1, top - w * 0.2, cx + w * 0.1, top], fill=(250, 250, 250), outline=INK, width=4)


def owl(d, cx, cy, s, expr="normal", hat_on=False, hat_flipped=False, seed=41):
    """フクロウのナビ(ツッコミ役)。cy は顔の中心。"""
    body = [(cx + s * 0.5 * math.cos(a), cy + s * 0.1 + s * 0.58 * math.sin(a)) for a in (i * math.pi / 24 for i in range(49))]
    shape(d, body, OWL, seed=seed)
    d.ellipse([cx - s * 0.3, cy + s * 0.15, cx + s * 0.3, cy + s * 0.62], fill=OWL_LIGHT)
    for k in (-1, 1):  # 耳(羽角)
        shape(d, [(cx + k * s * 0.18, cy - s * 0.42), (cx + k * s * 0.42, cy - s * 0.62), (cx + k * s * 0.4, cy - s * 0.3)], OWL, seed=seed + 3 + k)
        d.ellipse([cx + k * s * 0.2 - s * 0.17, cy - s * 0.2, cx + k * s * 0.2 + s * 0.17, cy + s * 0.14], fill=OWL_LIGHT)
    shape(d, [(cx - s * 0.06, cy + s * 0.06), (cx + s * 0.06, cy + s * 0.06), (cx, cy + s * 0.17)], ORANGE, w=3, seed=seed + 6)
    for k in (-1, 1):  # 足
        d.line([(cx + k * s * 0.16, cy + s * 0.66), (cx + k * s * 0.16, cy + s * 0.74)], fill=ORANGE, width=6)
    face_eyes(d, cx, cy - s * 0.03, s, expr)
    if hat_on:
        hat(d, cx, cy - s * 0.78, s * 0.72, hat_flipped, seed=seed + 9)


def penguin(d, cx, cy, s, expr="normal", hat_on=True, hat_flipped=False, seed=51):
    """ペンギンのペン(ボケ役)。cy は顔の中心。"""
    body = [(cx + s * 0.46 * math.cos(a), cy + s * 0.15 + s * 0.62 * math.sin(a)) for a in (i * math.pi / 24 for i in range(49))]
    shape(d, body, NAVY, seed=seed)
    belly = [(cx + s * 0.32 * math.cos(a), cy + s * 0.2 + s * 0.48 * math.sin(a)) for a in (i * math.pi / 24 for i in range(49))]
    d.polygon(belly, fill=(252, 250, 245))
    for k in (-1, 1):  # 羽と足
        shape(d, [(cx + k * s * 0.44, cy), (cx + k * s * 0.62, cy + s * 0.32), (cx + k * s * 0.42, cy + s * 0.38)], NAVY, seed=seed + 2 + k)
        shape(d, rrect_pts(cx + k * s * 0.18 - s * 0.1, cy + s * 0.72, cx + k * s * 0.18 + s * 0.1, cy + s * 0.8, 6), ORANGE, w=3, seed=seed + 5 + k)
    shape(d, [(cx - s * 0.07, cy + s * 0.05), (cx + s * 0.07, cy + s * 0.05), (cx, cy + s * 0.15)], ORANGE, w=3, seed=seed + 8)
    face_eyes(d, cx, cy - s * 0.04, s * 0.85, expr, white=False)
    if hat_on:
        hat(d, cx, cy - s * 0.82, s * 0.8, hat_flipped, seed=seed + 9)


def face_eyes(d, cx, cy, s, expr, white=True):
    """動物用の目とほっぺ(くちばしは本体側で描く)。"""
    ex, er = s * 0.2, max(5, s * 0.055)
    for k in (-1, 1):
        x = cx + k * ex
        if expr == "happy":
            d.arc([x - er * 1.8, cy - er * 1.4, x + er * 1.8, cy + er * 1.4], 200, 340, fill=INK, width=5)
        elif expr == "smug":
            d.line([(x - er * 1.6, cy), (x + er * 1.6, cy)], fill=INK, width=5)
        elif expr == "shock":
            d.ellipse([x - er * 1.9, cy - er * 1.9, x + er * 1.9, cy + er * 1.9], fill=(255, 255, 255), outline=INK, width=3)
            d.ellipse([x - er * 0.7, cy - er * 0.7, x + er * 0.7, cy + er * 0.7], fill=INK)
        else:
            d.ellipse([x - er, cy - er * 1.2, x + er, cy + er * 1.2], fill=INK)
            d.ellipse([x - er * 0.4, cy - er * 0.9, x, cy - er * 0.4], fill=(255, 255, 255))
        d.ellipse([x - s * 0.08, cy + s * 0.1, x + s * 0.08, cy + s * 0.16], fill=BLUSH)


def bubble(d, box, tail, en, ja, seed=0):
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    pts = [(cx + (x1 - x0) / 2 * math.cos(a), cy + (y1 - y0) / 2 * math.sin(a)) for a in (i * math.pi / 24 for i in range(49))]
    base = min(pts, key=lambda p: math.hypot(p[0] - tail[0], p[1] - tail[1]))
    tail_pts = [(base[0] - 16, base[1]), tail, (base[0] + 16, base[1])]
    d.polygon(pts, fill=(255, 255, 255))
    d.polygon(tail_pts, fill=(255, 255, 255))
    d.line(wob(pts, amp=1.2, seed=seed), fill=INK, width=4, joint="curve")
    d.line(tail_pts, fill=INK, width=4)
    lines = en.split("\n")
    total = len(lines) * 46 + (34 if ja else 0)
    y = cy - total / 2 + 23
    for line in lines:
        d.text((cx, y), line, font=EN(40), fill=INK, anchor="mm")
        y += 46
    if ja:
        d.text((cx, y - 6), ja, font=JP(24), fill=(120, 110, 105), anchor="mm")


def panel(img, box, seed):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=PAPER)
    d.line(wob([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], amp=1.4, seed=seed), fill=INK, width=6, joint="curve")
    return d


def sfx(img, xy, text, size, color, angle):
    layer = Image.new("RGBA", (size * len(text), size * 2), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((layer.width / 2, layer.height / 2), text, font=SFX(size), fill=color, anchor="mm")
    layer = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    img.paste(layer, (int(xy[0] - layer.width / 2), int(xy[1] - layer.height / 2)), layer)


def sweat(d, x, y, s=18):
    d.polygon([(x, y - s), (x - s * 0.6, y + s * 0.3), (x + s * 0.6, y + s * 0.3)], fill=(160, 200, 240))
    d.ellipse([x - s * 0.6, y - s * 0.1, x + s * 0.6, y + s * 0.8], fill=(160, 200, 240))


TOEIC_BG = (231, 238, 243)
TOEIC_TAG = (70, 120, 170)


def comic(title, series=None):
    """4コマの土台(見出しと2×2のコマ)。boxes はコマの位置(紙芝居リールでも使う)。series="toeic" で TOEIC編。"""
    img = Image.new("RGB", (W, H), TOEIC_BG if series == "toeic" else (244, 241, 234))
    d = ImageDraw.Draw(img)
    d.text((W // 2, 70), title, font=EN(64), fill=INK, anchor="mm")
    if series == "toeic":
        d.rounded_rectangle([W // 2 - 250, 100, W // 2 - 90, 142], radius=20, fill=TOEIC_TAG)
        d.text((W // 2 - 170, 121), "TOEIC編", font=JP(26), fill=(255, 255, 255), anchor="mm")
        d.text((W // 2 + 60, 121), "4コマで覚える英語", font=JP(30), fill=(120, 130, 140), anchor="mm")
    else:
        d.text((W // 2, 120), "4コマで覚える英語", font=JP(30), fill=(150, 140, 130), anchor="mm")
    pad, top, gap = 40, 160, 22
    pw, ph = (W - pad * 2 - gap) / 2, (H - top - pad - gap - 40) / 2
    boxes = [(pad + c * (pw + gap), top + r * (ph + gap), pad + c * (pw + gap) + pw, top + r * (ph + gap) + ph) for r in (0, 1) for c in (0, 1)]
    img.info["boxes"] = boxes
    return img, boxes, pw, ph


def inside_out():
    img, boxes, pw, ph = comic("inside out")

    # 1:あいさつ。ペンのニット帽は裏返し(タグが外)
    x0, y0, x1, y1 = boxes[0]
    d = panel(img, boxes[0], 11)
    penguin(d, x0 + pw * 0.3, y0 + ph * 0.6, 160, "happy", hat_flipped=True)
    owl(d, x0 + pw * 0.75, y0 + ph * 0.68, 150, "happy")
    bubble(d, (x0 + 20, y0 + 18, x0 + pw * 0.62, y0 + 120), (x0 + pw * 0.34, y0 + 158), "Morning!", "おはよう!", 1)
    # 2:ナビが気づく
    x0, y0, x1, y1 = boxes[1]
    d = panel(img, boxes[1], 12)
    owl(d, x0 + pw * 0.3, y0 + ph * 0.66, 160, "shock")
    sweat(d, x0 + pw * 0.5, y0 + ph * 0.44)
    penguin(d, x0 + pw * 0.76, y0 + ph * 0.66, 140, "normal", hat_flipped=True)
    bubble(d, (x0 + 14, y0 + 16, x0 + pw - 14, y0 + 166), (x0 + pw * 0.32, y0 + 200),
           "Your hat is\ninside out!", "帽子、裏返しだよ!", 2)
    sfx(img, (x0 + pw * 0.9, y0 + ph * 0.46), "!?", 56, (220, 80, 70), -10)
    # 3:ペンは平然と
    x0, y0, x1, y1 = boxes[2]
    d = panel(img, boxes[2], 13)
    penguin(d, x0 + pw * 0.5, y0 + ph * 0.66, 200, "smug", hat_flipped=True)
    bubble(d, (x0 + 18, y0 + 16, x0 + pw - 18, y0 + 166), (x0 + pw * 0.5, y0 + 200),
           "I know.\nIt's the new trend.", "知ってる。今の流行り", 3)
    sfx(img, (x0 + pw * 0.84, y0 + ph * 0.93), "*shine*", 34, (200, 160, 60), 8)
    # 4:ナビも帽子を裏返しにかぶってくる
    x0, y0, x1, y1 = boxes[3]
    d = panel(img, boxes[3], 14)
    owl(d, x0 + pw * 0.3, y0 + ph * 0.7, 150, "smug", hat_on=True, hat_flipped=True)
    penguin(d, x0 + pw * 0.76, y0 + ph * 0.68, 140, "happy", hat_flipped=True)
    bubble(d, (x0 + 14, y0 + 16, x0 + pw * 0.62, y0 + 116), (x0 + pw * 0.26, y0 + 150),
           "...Me too.", "…ぼくも", 4)
    sfx(img, (x0 + pw * 0.84, y0 + ph * 0.28), "*flip*", 40, (220, 80, 70), -12)
    d = ImageDraw.Draw(img)
    d.text((W - 50, H - 30), "@eng_navi", font=EN(30), fill=(160, 150, 140), anchor="rm")
    return img


def explain(phrase, meaning, en, ja, visual):
    img = Image.new("RGB", (W, H), (244, 241, 234))
    d = ImageDraw.Draw(img)
    for x in range(0, W, 54):
        d.line([(x, 0), (x, H)], fill=(225, 220, 212), width=2)
    for y in range(0, H, 54):
        d.line([(0, y), (W, y)], fill=(225, 220, 212), width=2)
    d.text((W // 2, 230), phrase, font=EN(130), fill=INK, anchor="mm")
    d.line(wob([(220, 310), (860, 304)], amp=2), fill=(200, 52, 48), width=7)
    d.text((W // 2, 400), f"= {meaning}", font=JP(70), fill=(200, 52, 48), anchor="mm")
    d.text((W // 2, 590), en, font=EN(46), fill=INK, anchor="mm")
    d.text((W // 2, 650), f"({ja})", font=JP(34), fill=(120, 110, 105), anchor="mm")
    visual(d)
    d.text((W // 2, 1200), "🔊 音声つきの10選は、プロフィールのリンクから".replace("🔊 ", ""), font=JP(36), fill=INK, anchor="mm")
    d.text((W // 2, 1255), "保存して、使ってみてね", font=JP(32), fill=(200, 52, 48), anchor="mm")
    d.text((W - 50, H - 30), "@eng_navi", font=EN(30), fill=(160, 150, 140), anchor="rm")
    return img


def compare(d, left, right, label):
    """解説の「ふだん → この表現」の絵。left/right はキャラを描く関数。"""
    left(d, 330, 960)
    right(d, 750, 960)
    d.text((330, 1125), "ふだん", font=JP(34), fill=(120, 110, 105), anchor="mm")
    d.text((750, 1125), label, font=EN(40), fill=(200, 52, 48), anchor="mm")
    d.line(wob([(450, 930), (630, 930)], amp=1.5), fill=INK, width=5)
    d.line([(630, 930), (605, 915)], fill=INK, width=5)
    d.line([(630, 930), (605, 945)], fill=INK, width=5)


def umbrella(d, cx, top, w, color=(240, 120, 120), seed=60):
    pts = [(cx + w / 2 * math.cos(a), top + w * 0.42 - w * 0.42 * math.sin(a)) for a in (i * math.pi / 16 for i in range(17))]
    shape(d, pts + [pts[0]], color, seed=seed)
    for k in (-0.25, 0, 0.25):
        d.line([(cx + k * w * 0.9, top + w * 0.42), (cx + k * w * 0.4, top + w * 0.05)], fill=INK, width=3)
    d.line(wob([(cx, top + w * 0.42), (cx, top + w * 0.95)], amp=0.8), fill=INK, width=5)
    d.arc([cx - w * 0.12, top + w * 0.85, cx + w * 0.04, top + w * 1.02], 0, 180, fill=INK, width=5)


def rain(d, box, n=28, seed=70):
    import random as _r
    r = _r.Random(seed)
    x0, y0, x1, y1 = box
    for _ in range(n):
        x, y = r.uniform(x0 + 10, x1 - 20), r.uniform(y0 + 10, y1 - 30)
        d.line([(x, y), (x - 8, y + 26)], fill=(130, 175, 220), width=4)


def drips(d, cx, cy, s):
    for dx, dy in ((-0.55, -0.1), (0.6, 0.05), (-0.45, 0.45), (0.5, 0.5), (0.05, -0.75)):
        sweat(d, cx + dx * s, cy + dy * s, s * 0.09)
    d.ellipse([cx - s * 0.6, cy + s * 0.92, cx + s * 0.6, cy + s * 1.02], fill=(170, 205, 235))


def shiver(d, cx, cy, s):
    for k in (-1, 1):
        for i in range(3):
            x = cx + k * (s * 0.62 + i * 10)
            d.line([(x, cy - s * 0.2 + i * 8), (x + k * 6, cy + s * 0.05 + i * 8)], fill=INK, width=3)


def towel(d, cx, cy, s, seed=80):
    pts = rrect_pts(cx - s * 0.55, cy + s * 0.05, cx + s * 0.55, cy + s * 0.7, s * 0.15)
    shape(d, pts, (250, 225, 150), seed=seed)
    for i in range(1, 4):
        d.line([(cx - s * 0.5, cy + s * 0.05 + i * s * 0.16), (cx + s * 0.5, cy + s * 0.05 + i * s * 0.16)], fill=(225, 190, 110), width=3)


def wet_to_the_skin():
    img, boxes, pw, ph = comic("wet to the skin")
    # 1:ナビが傘を持って、雨だよ
    x0, y0, x1, y1 = boxes[0]
    d = panel(img, boxes[0], 21)
    rain(d, boxes[0], seed=71)
    umbrella(d, x0 + pw * 0.7, y0 + ph * 0.4, 150)
    owl(d, x0 + pw * 0.7, y0 + ph * 0.76, 125, "normal")
    penguin(d, x0 + pw * 0.26, y0 + ph * 0.74, 120, "normal", hat_on=False)
    bubble(d, (x0 + 14, y0 + 14, x0 + pw - 14, y0 + 164), (x0 + pw * 0.62, y0 + 196),
           "It's raining!\nTake an umbrella.", "雨だよ!傘持っていきな", 1)
    # 2:ペンはドヤ顔で、雨の中へ
    x0, y0, x1, y1 = boxes[1]
    d = panel(img, boxes[1], 22)
    rain(d, boxes[1], seed=72)
    penguin(d, x0 + pw * 0.5, y0 + ph * 0.66, 190, "smug", hat_on=False)
    bubble(d, (x0 + 18, y0 + 16, x0 + pw - 18, y0 + 166), (x0 + pw * 0.5, y0 + 205),
           "No need.\nI'm a penguin.", "いらない。ペンギンだし", 2)
    sfx(img, (x0 + pw * 0.86, y0 + ph * 0.88), "*waddle*", 32, (110, 150, 200), 8)
    # 3:ずぶぬれで震えるペンに、ナビがツッコむ
    x0, y0, x1, y1 = boxes[2]
    d = panel(img, boxes[2], 23)
    penguin(d, x0 + pw * 0.3, y0 + ph * 0.66, 150, "shock", hat_on=False)
    drips(d, x0 + pw * 0.3, y0 + ph * 0.66, 150)
    shiver(d, x0 + pw * 0.3, y0 + ph * 0.66, 150)
    owl(d, x0 + pw * 0.76, y0 + ph * 0.7, 135, "shock")
    bubble(d, (x0 + pw * 0.3, y0 + 16, x0 + pw - 14, y0 + 166), (x0 + pw * 0.72, y0 + 210),
           "You're wet\nto the skin!", "ずぶぬれじゃん!", 3)
    sfx(img, (x0 + pw * 0.14, y0 + ph * 0.22), "*shiver*", 34, (110, 150, 200), -10)
    # 4:タオルにくるまって、言い訳
    x0, y0, x1, y1 = boxes[3]
    d = panel(img, boxes[3], 24)
    penguin(d, x0 + pw * 0.5, y0 + ph * 0.64, 180, "smug", hat_on=False)
    towel(d, x0 + pw * 0.5, y0 + ph * 0.64, 180)
    bubble(d, (x0 + 18, y0 + 16, x0 + pw - 18, y0 + 166), (x0 + pw * 0.5, y0 + 200),
           "I like the sea...\nnot the rain.", "好きなのは海…雨じゃない", 4)
    d = ImageDraw.Draw(img)
    d.text((W - 50, H - 30), "@eng_navi", font=EN(30), fill=(160, 150, 140), anchor="rm")
    return img


CAPY = (176, 128, 86)
CAPY_DARK = (140, 98, 62)
SUIT = (90, 170, 170)


def capybara(d, cx, cy, s, expr="calm", seed=91):
    """カピバラ部長(マイペースな上司)。横長の体。cy は顔の中心。"""
    body = rrect_pts(cx - s * 0.62, cy - s * 0.28, cx + s * 0.55, cy + s * 0.42, s * 0.28)
    shape(d, body, CAPY, seed=seed)
    for k in (-0.38, 0.32):  # 足
        shape(d, rrect_pts(cx + k * s - s * 0.07, cy + s * 0.36, cx + k * s + s * 0.07, cy + s * 0.5, 5), CAPY_DARK, w=3, seed=seed + 1)
    shape(d, [(cx - s * 0.5, cy - s * 0.24), (cx - s * 0.42, cy - s * 0.38), (cx - s * 0.34, cy - s * 0.26)], CAPY_DARK, w=3, seed=seed + 2)
    shape(d, [(cx - s * 0.2, cy - s * 0.28), (cx - s * 0.12, cy - s * 0.4), (cx - s * 0.04, cy - s * 0.28)], CAPY_DARK, w=3, seed=seed + 3)
    # 鼻先(左向き)
    shape(d, rrect_pts(cx - s * 0.72, cy - s * 0.06, cx - s * 0.4, cy + s * 0.2, s * 0.12), CAPY_DARK, w=4, seed=seed + 4)
    d.ellipse([cx - s * 0.66, cy + s * 0.02, cx - s * 0.6, cy + s * 0.07], fill=INK)
    for k in (-0.36, -0.18):
        x = cx + k * s
        if expr == "shock":
            d.ellipse([x - 8, cy - s * 0.12, x + 8, cy - s * 0.12 + 16], fill=(255, 255, 255), outline=INK, width=3)
            d.ellipse([x - 3, cy - s * 0.12 + 5, x + 3, cy - s * 0.12 + 11], fill=INK)
        else:  # いつも眠そうな目
            d.arc([x - 9, cy - s * 0.12, x + 9, cy - s * 0.12 + 12], 0, 180, fill=INK, width=4)
    d.ellipse([cx - s * 0.32, cy + s * 0.02, cx - s * 0.2, cy + s * 0.08], fill=BLUSH)
    # ネクタイ(部長らしく)
    shape(d, [(cx - s * 0.08, cy + s * 0.12), (cx + s * 0.02, cy + s * 0.12), (cx + s * 0.04, cy + s * 0.34), (cx - s * 0.03, cy + s * 0.4), (cx - s * 0.1, cy + s * 0.34)], (200, 80, 80), w=3, seed=seed + 5)


def suitcase(d, cx, cy, w, color=SUIT, seed=95):
    h = w * 0.7
    shape(d, rrect_pts(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, w * 0.1), color, seed=seed)
    d.arc([cx - w * 0.16, cy - h / 2 - w * 0.16, cx + w * 0.16, cy - h / 2 + w * 0.06], 180, 360, fill=INK, width=5)
    for k in (-0.25, 0.25):
        d.line([(cx + k * w, cy - h / 2 + 6), (cx + k * w, cy + h / 2 - 6)], fill=(60, 130, 130), width=4)


def conveyor(d, box, y):
    x0, _, x1, _ = box
    shape(d, [(x0 + 8, y), (x1 - 8, y), (x1 - 8, y + 34), (x0 + 8, y + 34), (x0 + 8, y)], (170, 172, 178), w=4, seed=97)
    for i in range(int((x1 - x0) / 40)):
        d.line([(x0 + 20 + i * 40, y + 6), (x0 + 20 + i * 40, y + 28)], fill=(130, 132, 140), width=3)


def baggage_claim():
    img, boxes, pw, ph = comic("baggage claim", series="toeic")
    # 1:ナビが「手荷物受取所へ」
    x0, y0, x1, y1 = boxes[0]
    d = panel(img, boxes[0], 31)
    owl(d, x0 + pw * 0.3, y0 + ph * 0.66, 140, "happy")
    penguin(d, x0 + pw * 0.72, y0 + ph * 0.66, 135, "normal", hat_on=False)
    d.rounded_rectangle([x0 + pw * 0.56, y0 + ph * 0.3, x0 + pw * 0.95, y0 + ph * 0.4], radius=6, fill=(255, 215, 90), outline=INK, width=3)
    d.text((x0 + pw * 0.755, y0 + ph * 0.35), "BAGGAGE CLAIM", font=EN(22), fill=INK, anchor="mm")
    bubble(d, (x0 + 14, y0 + 14, x0 + pw - 14, y0 + 166), (x0 + pw * 0.3, y0 + 200),
           "Let's go to\nbaggage claim.", "手荷物受取所に行こう", 1)
    # 2:ペンがベルトの前で待つ
    x0, y0, x1, y1 = boxes[1]
    d = panel(img, boxes[1], 32)
    conveyor(d, boxes[1], y0 + ph * 0.8)
    suitcase(d, x0 + pw * 0.2, y0 + ph * 0.8 - 32, 70, (230, 150, 120), seed=96)
    penguin(d, x0 + pw * 0.62, y0 + ph * 0.56, 140, "normal", hat_on=False)
    bubble(d, (x0 + 14, y0 + 14, x0 + pw - 14, y0 + 166), (x0 + pw * 0.62, y0 + 200),
           "Where's my\nsuitcase...?", "ぼくのスーツケース、どこ…?", 2)
    sfx(img, (x0 + pw * 0.86, y0 + ph * 0.68), "*stare*", 30, (110, 120, 140), 6)
    # 3:部長がペンのスーツケースに乗って回ってくる
    x0, y0, x1, y1 = boxes[2]
    d = panel(img, boxes[2], 33)
    conveyor(d, boxes[2], y0 + ph * 0.8)
    suitcase(d, x0 + pw * 0.52, y0 + ph * 0.8 - 44, 150)
    capybara(d, x0 + pw * 0.55, y0 + ph * 0.8 - 160, 170, "calm")
    bubble(d, (x0 + 14, y0 + 14, x0 + pw - 14, y0 + 166), (x0 + pw * 0.4, y0 + 210),
           "Ahh...\nnice ride.", "あ〜、いい乗り心地", 3)
    sfx(img, (x0 + pw * 0.8, y0 + ph * 0.4), "*round*", 30, (200, 140, 60), -8)
    # 4:ナビのツッコミ
    x0, y0, x1, y1 = boxes[3]
    d = panel(img, boxes[3], 34)
    owl(d, x0 + pw * 0.28, y0 + ph * 0.68, 145, "shock")
    sweat(d, x0 + pw * 0.46, y0 + ph * 0.46)
    penguin(d, x0 + pw * 0.74, y0 + ph * 0.68, 130, "shock", hat_on=False)
    bubble(d, (x0 + 14, y0 + 14, x0 + pw - 14, y0 + 166), (x0 + pw * 0.3, y0 + 205),
           "Boss!\nThat's not a ride!", "部長!それ乗り物じゃないです!", 4)
    d = ImageDraw.Draw(img)
    d.text((W - 50, H - 30), "@eng_navi", font=EN(30), fill=(160, 150, 140), anchor="rm")
    return img


def _baggage_visual(d):
    conveyor(d, (180, 0, 900, 0), 1010)
    suitcase(d, 380, 978, 110)
    suitcase(d, 620, 978, 110, (230, 150, 120), seed=96)
    d.rounded_rectangle([370, 820, 710, 880], radius=8, fill=(255, 215, 90), outline=INK, width=4)
    d.text((540, 850), "BAGGAGE CLAIM", font=EN(34), fill=INK, anchor="mm")
    d.text((540, 1110), "空港で、預けた荷物を受け取る場所", font=JP(34), fill=(120, 110, 105), anchor="mm")


def _wet_visual(d):
    def soaked(d, x, y):
        penguin(d, x, y, 160, "shock", hat_on=False)
        drips(d, x, y, 160)
    compare(d, lambda d, x, y: penguin(d, x, y, 160, "happy", hat_on=False), soaked, "wet to the skin")


def _inside_visual(d):
    compare(d, lambda d, x, y: penguin(d, x, y, 160, "normal"),
            lambda d, x, y: penguin(d, x, y, 160, "happy", hat_flipped=True), "inside out")


SCRIPTS = {
    "inside_out": (inside_out, ("inside out", "裏返しに", "My son wore his sweater inside out.",
                                "息子はセーターを裏返しに着ていた", _inside_visual)),
    "baggage_claim": (baggage_claim, ("baggage claim", "手荷物受取所", "I waited at baggage claim for twenty minutes.",
                                      "手荷物受取所で20分待った", _baggage_visual)),
    "wet_to_the_skin": (wet_to_the_skin, ("wet to the skin", "ずぶぬれ", "I forgot my umbrella and got wet to the skin.",
                                          "傘を忘れて、ずぶぬれになった", _wet_visual)),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    name = sys.argv[1] if len(sys.argv) > 1 else "inside_out"
    draw, ex = SCRIPTS[name]
    draw().save(OUT / f"{name}_1.png")
    explain(*ex).save(OUT / f"{name}_2.png")
    print(f"✓ {OUT}/{name}_1.png, _2.png")


if __name__ == "__main__":
    main()
