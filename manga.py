"""イディオムのギャグ4コマ(カルーセル2枚:4コマ + 解説)。キャラクターは eng_navi オリジナル。

    python3 manga.py inside_out     # out/manga/inside_out_1.png, _2.png

ナビ:えんぴつの子(黄色い体、ピンクの消しゴム帽子)/ ブック:本の子(緑の表紙)
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


def inside_out():
    img = Image.new("RGB", (W, H), (244, 241, 234))
    d = ImageDraw.Draw(img)
    d.text((W // 2, 70), "inside out", font=EN(64), fill=INK, anchor="mm")
    d.text((W // 2, 120), "4コマで覚える英語", font=JP(30), fill=(150, 140, 130), anchor="mm")
    pad, top, gap = 40, 160, 22
    pw, ph = (W - pad * 2 - gap) / 2, (H - top - pad - gap - 40) / 2
    boxes = [(pad + c * (pw + gap), top + r * (ph + gap), pad + c * (pw + gap) + pw, top + r * (ph + gap) + ph) for r in (0, 1) for c in (0, 1)]

    # 1:あいさつ。ブックは表紙が裏返し(中身が外)
    x0, y0, x1, y1 = boxes[0]
    d = panel(img, boxes[0], 11)
    book(d, x0 + pw * 0.3, y0 + ph * 0.66, 190, "happy", flipped=True)
    navi(d, x0 + pw * 0.76, y0 + ph * 0.58, 150, "happy")
    bubble(d, (x0 + 20, y0 + 22, x0 + pw * 0.6, y0 + 132), (x0 + pw * 0.3, y0 + 175), "Morning!", "おはよう!", 1)
    # 2:ナビが気づく
    x0, y0, x1, y1 = boxes[1]
    d = panel(img, boxes[1], 12)
    navi(d, x0 + pw * 0.3, y0 + ph * 0.62, 150, "shock")
    sweat(d, x0 + pw * 0.48, y0 + ph * 0.42)
    book(d, x0 + pw * 0.76, y0 + ph * 0.7, 165, "normal", flipped=True)
    bubble(d, (x0 + 14, y0 + 18, x0 + pw - 14, y0 + 168), (x0 + pw * 0.32, y0 + 205),
           "Your cover is\ninside out!", "表紙、裏返しだよ!", 2)
    sfx(img, (x0 + pw * 0.88, y0 + ph * 0.42), "!?", 60, (220, 80, 70), -10)
    # 3:ブックは平然と
    x0, y0, x1, y1 = boxes[2]
    d = panel(img, boxes[2], 13)
    book(d, x0 + pw * 0.5, y0 + ph * 0.66, 230, "smug", flipped=True)
    bubble(d, (x0 + 18, y0 + 18, x0 + pw - 18, y0 + 168), (x0 + pw * 0.5, y0 + 205),
           "I know.\nIt's the new trend.", "知ってる。今の流行り", 3)
    sfx(img, (x0 + pw * 0.84, y0 + ph * 0.92), "*shine*", 34, (200, 160, 60), 8)
    # 4:ナビも帽子を裏返す
    x0, y0, x1, y1 = boxes[3]
    d = panel(img, boxes[3], 14)
    navi(d, x0 + pw * 0.3, y0 + ph * 0.62, 150, "smug", cap_back=True)
    book(d, x0 + pw * 0.75, y0 + ph * 0.7, 160, "happy", flipped=True)
    bubble(d, (x0 + 14, y0 + 20, x0 + pw * 0.62, y0 + 130), (x0 + pw * 0.28, y0 + 175),
           "...Me too.", "…ぼくも", 4)
    sfx(img, (x0 + pw * 0.82, y0 + ph * 0.3), "*flip*", 40, (220, 80, 70), -12)
    d = ImageDraw.Draw(img)
    d.text((W - 50, H - 30), "@eng_navi", font=EN(30), fill=(160, 150, 140), anchor="rm")
    return img


def explain(phrase, meaning, en, ja, tip):
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
    book(d, 330, 930, 170, "normal")
    book(d, 750, 930, 170, "happy", flipped=True)
    d.text((330, 1060), "ふだん", font=JP(34), fill=(120, 110, 105), anchor="mm")
    d.text((750, 1060), "inside out", font=EN(40), fill=(200, 52, 48), anchor="mm")
    sb_arrow = [(450, 930), (630, 930)]
    d.line(wob(sb_arrow, amp=1.5), fill=INK, width=5)
    d.line([(630, 930), (605, 915)], fill=INK, width=5)
    d.line([(630, 930), (605, 945)], fill=INK, width=5)
    d.text((W // 2, 1180), "🔊 音声つきの10選は、プロフィールのリンクから".replace("🔊 ", ""), font=JP(36), fill=INK, anchor="mm")
    d.text((W // 2, 1240), "保存して、使ってみてね", font=JP(32), fill=(200, 52, 48), anchor="mm")
    d.text((W - 50, H - 30), "@eng_navi", font=EN(30), fill=(160, 150, 140), anchor="rm")
    return img


SCRIPTS = {
    "inside_out": (inside_out, ("inside out", "裏返しに", "My son wore his sweater inside out.",
                                "息子はセーターを裏返しに着ていた", "turn it\ninside out!")),
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
