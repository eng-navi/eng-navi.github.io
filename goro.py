"""語呂合わせ英単語の、ストップモーション風リール(試作)。

    .venv-tts/bin/python goro.py abandon     # out/goro/abandon.mp4
    .venv-tts/bin/python goro.py bury        # out/goro/bury.mp4

見た目:左右対称の舞台・パステルカラー・フェルト/紙の質感・1秒12コマのわずかなカクつき(手作り感)。
キャラは 4コマと同じ ナビ(フクロウ)とペン(ペンギン)。語呂合わせと例文はオリジナル。
"""
import math
import random
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import manga as m

ROOT = Path(__file__).parent
OUT = ROOT / "out" / "goro"
W, H, FPS, SR = 1080, 1920, 12, 24000
WALL = (246, 214, 200)      # くすみピンクの壁
WALL2 = (238, 200, 186)
FLOOR = (196, 214, 196)     # セージグリーンの床
FRAME_C = (232, 190, 120)   # 額縁のからし色
INK = m.INK


def felt(seed):
    """フェルトのザラザラ。フレームごとに少しずらして“ゆらぎ”を出す。"""
    r = random.Random(seed)
    n = Image.effect_noise((W // 3, H // 3), 28).resize((W, H), Image.BILINEAR)
    return n.rotate(r.uniform(-0.6, 0.6)).convert("L")


def stage(seed):
    """左右対称の舞台:壁・額縁・床・カーテン。"""
    img = Image.new("RGB", (W, H), WALL)
    d = ImageDraw.Draw(img)
    for x in range(0, W, 90):  # 壁のストライプ
        d.rectangle([x, 0, x + 45, 1250], fill=WALL2)
    d.rectangle([0, 1250, W, H], fill=FLOOR)
    d.line(m.wob([(0, 1250), (W, 1250)], amp=2, seed=seed), fill=INK, width=6)
    # 中央の額縁(左右対称)
    m.shape(d, m.rrect_pts(340, 300, 740, 600, 10), FRAME_C, seed=seed + 1)
    d.rectangle([370, 330, 710, 570], fill=(250, 240, 220))
    d.text((540, 450), "eng", font=m.EN(70), fill=(200, 150, 120), anchor="mm")
    # 左右のカーテン
    for side in (-1, 1):
        x0 = 0 if side < 0 else W - 120
        m.shape(d, [(x0, 0), (x0 + 120, 0), (x0 + 120 - side * 30 if side < 0 else x0 + 30, 1250), (x0, 1250)] if side < 0
                else [(x0, 0), (x0 + 120, 0), (x0 + 120, 1250), (x0 + 30, 1250)], (214, 120, 120), seed=seed + 2 + side)
    return img


def finish(img, seed):
    """フェルトの質感と、ふちのやわらかい影をのせる。"""
    tex = felt(seed)
    shade = Image.new("RGB", (W, H), (60, 40, 30))
    img = Image.composite(shade, img, tex.point(lambda v: int(v * 0.10)))
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse([-300, -200, W + 300, H + 200], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(160))
    dark = Image.new("RGB", (W, H), (40, 30, 30))
    return Image.composite(img, dark, vig.point(lambda v: int(140 + v * 115 / 255)))


def jsfx(img, xy, text, size, color, angle):
    """日本語の効果音(ポイッ・ドン!)。白いふちどりで目立たせる。"""
    layer = Image.new("RGBA", (int(size * len(text) * 1.3), int(size * 2)), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((layer.width / 2, layer.height / 2), text, font=m.JP(size), fill=color, anchor="mm",
                               stroke_width=int(size * 0.08), stroke_fill=(255, 255, 255))
    layer = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    img.paste(layer, (int(xy[0] - layer.width / 2), int(xy[1] - layer.height / 2)), layer)


def shadow(d, cx, y, w):
    d.ellipse([cx - w / 2, y - 14, cx + w / 2, y + 14], fill=(150, 170, 150))


def table(d, seed):
    m.shape(d, m.rrect_pts(300, 1180, 780, 1230, 10), (206, 160, 110), seed=seed)
    for x in (340, 740):
        d.line([(x, 1230), (x, 1420)], fill=INK, width=8)


def bowl(d, cx, cy, s, seed, tilt=0):
    pts = [(cx - s, cy), (cx + s, cy), (cx + s * 0.7, cy + s * 0.7), (cx - s * 0.7, cy + s * 0.7)]
    pts = [(x + tilt * (y - cy) * 0.3, y) for x, y in pts]
    m.shape(d, pts, (240, 240, 245), seed=seed)
    d.ellipse([cx - s * 0.9, cy - s * 0.35, cx + s * 0.9, cy + s * 0.25], fill=(250, 220, 150), outline=INK, width=4)
    for i in range(3):  # 湯気
        x = cx - s * 0.4 + i * s * 0.4
        d.line(m.wob([(x, cy - s * 0.5), (x + 8, cy - s * 0.8), (x - 6, cy - s * 1.1)], amp=1.5, seed=seed + i), fill=(200, 200, 200), width=5)


def trash(d, cx, cy, s, seed):
    m.shape(d, [(cx - s * 0.5, cy - s * 0.6), (cx + s * 0.5, cy - s * 0.6), (cx + s * 0.4, cy + s * 0.6), (cx - s * 0.4, cy + s * 0.6)], (150, 170, 190), seed=seed)
    m.shape(d, m.rrect_pts(cx - s * 0.58, cy - s * 0.72, cx + s * 0.58, cy - s * 0.58, 6), (130, 150, 170), seed=seed + 1)
    for k in (-0.2, 0, 0.2):
        d.line([(cx + k * s, cy - s * 0.45), (cx + k * s * 0.8, cy + s * 0.5)], fill=(110, 130, 150), width=4)


def caption(d, text, y, size=64, color=INK, box=True):
    f = m.JP(size)
    w = f.getlength(text)
    if box:
        d.rounded_rectangle([W / 2 - w / 2 - 36, y - size * 0.85, W / 2 + w / 2 + 36, y + size * 0.6], radius=26, fill=(255, 252, 245), outline=INK, width=5)
    d.text((W / 2, y), text, font=f, fill=color, anchor="ms")


def big_word(d, parts, y, active):
    """「あ・ばん・どん」を色分けして見せ、下に abandon を対応させる。"""
    colors = [(230, 120, 110), (110, 160, 210), (120, 170, 120)]
    f = m.JP(120)
    widths = [f.getlength(p) for p, _ in parts]
    x = W / 2 - (sum(widths) + 40 * (len(parts) - 1)) / 2
    fe = m.EN(130)
    en_w = sum(fe.getlength(e) for _, e in parts)
    xe = W / 2 - en_w / 2
    for i, ((jp, en), w) in enumerate(zip(parts, widths)):
        c = colors[i] if i < active else (210, 205, 200)
        d.text((x, y), jp, font=f, fill=c, anchor="ls")
        x += w + 40
        d.text((xe, y + 160), en, font=fe, fill=c, anchor="ls")
        xe += fe.getlength(en)


# ---- シーン(秒数, 描く関数(frame番号)) ----
def scene_hook(i):
    img = stage(100 + i % 3)
    d = ImageDraw.Draw(img)
    shadow(d, 540, 1400, 260)
    m.penguin(d, 540, 1150, 300, "shock", hat_on=False, seed=51 + i % 3)
    m.sweat(d, 700, 1000, 30)
    caption(d, "abandon、", 820, 96, box=False)
    caption(d, "1秒で覚えられる?", 950, 80, color=(200, 52, 48), box=False)
    return img


def scene_dinner(i):
    img = stage(110 + i % 3)
    d = ImageDraw.Draw(img)
    table(d, 120 + i % 3)
    bowl(d, 540, 1120, 90, 130 + i % 3)
    shadow(d, 300, 1440, 200)
    m.penguin(d, 300, 1230, 210, "happy", hat_on=False, seed=51 + i % 3)
    shadow(d, 790, 1440, 200)
    m.owl(d, 790, 1230, 200, "normal", seed=41 + i % 3)
    caption(d, "今日の晩ごはん、楽しみ〜", 1640, 58)
    return img


def scene_toss(i, n):
    img = stage(140 + i % 3)
    d = ImageDraw.Draw(img)
    t = min(1, i / max(1, n - 3))
    shadow(d, 230, 1440, 180)
    m.penguin(d, 230, 1240, 190, "shock", hat_on=False, seed=51 + i % 3)
    shadow(d, 520, 1440, 180)
    m.owl(d, 520, 1240, 180, "smug", seed=41 + i % 3)
    trash(d, 850, 1300, 220, 150 + i % 3)
    # 晩ごはんがゴミ箱へ飛んでいく(放物線)
    x = 560 + (850 - 560) * t
    y = 1080 - 300 * math.sin(math.pi * t) + 120 * t
    if t < 1:
        bowl(d, x, y, 80, 160 + i % 3, tilt=t * 2)
    if t < 1:
        jsfx(img, (700, 820), "ポイッ", 90, (220, 90, 70), -10)
    caption(d, "あ、晩(ばん)ごはん…", 1640, 64)
    return img


def scene_don(i):
    img = stage(170 + i % 3)
    d = ImageDraw.Draw(img)
    trash(d, 830, 1300, 230, 150 + i % 3)
    shadow(d, 330, 1440, 220)
    m.penguin(d, 330, 1230, 230, "shock", hat_on=False, seed=51 + i % 3)
    jsfx(img, (640, 1120), "ドン!", 120, (220, 60, 50), -8)
    d.rounded_rectangle([90, 640, W - 90, 1000], radius=40, fill=(255, 252, 245), outline=INK, width=6)
    big_word(d, [("あ", "a"), ("ばん", "ban"), ("どん!", "don")], 790, active=min(3, 1 + i // 4))
    return img


def scene_meaning(i):
    img = stage(190 + i % 3)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([110, 640, W - 110, 1180], radius=40, fill=(255, 252, 245), outline=INK, width=6)
    d.text((W / 2, 800), "abandon", font=m.EN(150), fill=INK, anchor="ms")
    d.text((W / 2, 920), "= 捨てる、あきらめる", font=m.JP(66), fill=(200, 52, 48), anchor="ms")
    m.draw_fit(d, (W / 2, 1010), "They abandoned the old boat.", m.EN(52), INK, width=W - 300)
    m.draw_fit(d, (W / 2, 1100), "(彼らは古いボートを捨てた)", m.JP(38), (110, 110, 110), width=W - 300, jp=True)
    shadow(d, 260, 1440, 180)
    m.owl(d, 260, 1260, 180, "happy", seed=41 + i % 3)
    shadow(d, 820, 1440, 180)
    m.penguin(d, 820, 1260, 170, "smug", hat_on=False, seed=51 + i % 3)
    caption(d, "あ・ばん・どん で abandon!", 1640, 58)
    d.text((W - 60, H - 60), m.HANDLE, font=m.EN(40), fill=(120, 110, 100), anchor="rm")
    return img


# ---- bury(埋める):発音は berry と同じ。「ベリーを うめる」 ----
def berry(d, cx, cy, r, seed):
    m.shape(d, [(cx + r * math.cos(a), cy + r * 1.1 * math.sin(a) + (r * 0.25 if math.sin(a) > 0 else 0))
                for a in (k * math.pi / 12 for k in range(25))], (220, 70, 80), w=3, seed=seed)
    for k in range(5):
        a = k * 1.3
        d.ellipse([cx + r * 0.45 * math.cos(a) - 3, cy + r * 0.45 * math.sin(a) - 2, cx + r * 0.45 * math.cos(a) + 3, cy + r * 0.45 * math.sin(a) + 2], fill=(250, 220, 120))
    d.polygon([(cx - r * 0.6, cy - r * 0.95), (cx, cy - r * 0.6), (cx + r * 0.6, cy - r * 0.95), (cx, cy - r * 1.25)], fill=(110, 170, 100))


def basket(d, cx, cy, s, seed, n=5):
    for k in range(n):
        berry(d, cx - s * 0.45 + k * s * 0.22, cy - s * 0.18 - (k % 2) * 14, s * 0.13, seed + k)
    m.shape(d, [(cx - s * 0.6, cy - s * 0.15), (cx + s * 0.6, cy - s * 0.15), (cx + s * 0.45, cy + s * 0.35), (cx - s * 0.45, cy + s * 0.35)], (205, 160, 105), seed=seed)
    for k in range(1, 4):
        y = cy - s * 0.15 + k * s * 0.125
        d.line([(cx - s * 0.55 + k * 6, y), (cx + s * 0.55 - k * 6, y)], fill=(170, 125, 80), width=3)


def mound(d, cx, cy, w, seed, h=0.35):
    m.shape(d, [(cx + w / 2 * math.cos(a), cy - w * h * math.sin(a)) for a in (k * math.pi / 16 for k in range(17))], (150, 110, 80), seed=seed)


def shovel(d, x, y, angle):
    a = math.radians(angle)
    x2, y2 = x + 150 * math.sin(a), y + 150 * math.cos(a)
    d.line([(x, y), (x2, y2)], fill=(150, 100, 60), width=10)
    m.shape(d, [(x2 - 24, y2 - 6), (x2 + 24, y2 - 6), (x2 + 16, y2 + 50), (x2 - 16, y2 + 50)], (170, 180, 190), w=4)


def scene_bury_hook(i):
    img = stage(300 + i % 3)
    d = ImageDraw.Draw(img)
    shadow(d, 540, 1400, 260)
    m.penguin(d, 540, 1150, 300, "shock", hat_on=False, seed=51 + i % 3)
    m.sweat(d, 700, 1000, 30)
    caption(d, "bury、", 820, 96, box=False)
    caption(d, "1秒で覚えられる?", 950, 80, color=(200, 52, 48), box=False)
    return img


def scene_bury_pick(i):
    img = stage(310 + i % 3)
    d = ImageDraw.Draw(img)
    shadow(d, 380, 1440, 220)
    m.penguin(d, 380, 1230, 220, "happy", hat_on=False, seed=51 + i % 3)
    basket(d, 690, 1330, 260, 320 + i % 3)
    jsfx(img, (690, 1060), "どっさり", 70, (220, 90, 70), 8)
    caption(d, "ベリー、たくさん取れた〜", 1640, 58)
    return img


def scene_bury_dig(i, n):
    img = stage(330 + i % 3)
    d = ImageDraw.Draw(img)
    t = min(1, i / max(1, n - 4))
    # ベリーが1つずつ土の山にうまっていく
    mound(d, 640, 1330, 300, 340 + i % 3, h=0.2 + 0.25 * t)
    for k in range(max(0, 4 - int(t * 4))):
        berry(d, 560 + k * 55, 1290 - k % 2 * 10, 26, 350 + k)
    shadow(d, 300, 1440, 200)
    m.penguin(d, 300, 1230, 210, "smug", hat_on=False, seed=51 + i % 3)
    shovel(d, 400, 1060, 35 + 12 * math.sin(i * 1.2))
    shadow(d, 880, 1440, 160)
    m.owl(d, 880, 1250, 160, "shock", seed=41 + i % 3)
    jsfx(img, (620, 1060), "ザクザク", 80, (150, 100, 60), -8)
    caption(d, "えっ、ベリーを うめてる!?", 1640, 58)
    return img


def scene_bury_word(i):
    img = stage(360 + i % 3)
    d = ImageDraw.Draw(img)
    mound(d, 830, 1330, 260, 340)
    shadow(d, 300, 1440, 220)
    m.penguin(d, 300, 1230, 230, "happy", hat_on=False, seed=51 + i % 3)
    jsfx(img, (700, 1130), "ポン!", 110, (220, 60, 50), -8)
    d.rounded_rectangle([90, 600, W - 90, 1020], radius=40, fill=(255, 252, 245), outline=INK, width=6)
    # 上:「ベリー を うめる」を順に色づけ / 下:bury = 埋める
    step = min(3, 1 + i // 4)
    parts = [("ベリー", (230, 120, 110)), ("を", (150, 140, 130)), ("うめる", (110, 160, 210))]
    f = m.JP(104)
    x = W / 2 - (sum(f.getlength(p) for p, _ in parts) + 30 * 2) / 2
    for k, (p, c) in enumerate(parts):
        d.text((x, 740), p, font=f, fill=c if k < step else (215, 210, 205), anchor="ls")
        x += f.getlength(p) + 30
    if step >= 3:
        fe = m.EN(120)
        line = [("bury", (230, 120, 110)), (" = ", INK), ("埋める", (110, 160, 210))]
        fonts = [fe, m.EN(90), m.JP(84)]
        x = W / 2 - sum(ff.getlength(t) for (t, _), ff in zip(line, fonts)) / 2
        for (t, c), ff in zip(line, fonts):
            d.text((x, 885), t, font=ff, fill=c, anchor="ls")
            x += ff.getlength(t)
    d.text((W / 2, 975), "発音は berry(ベリー)と同じ!", font=m.JP(44), fill=(110, 110, 110), anchor="ms")
    return img


def scene_bury_meaning(i):
    img = stage(380 + i % 3)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([110, 640, W - 110, 1180], radius=40, fill=(255, 252, 245), outline=INK, width=6)
    d.text((W / 2, 800), "bury", font=m.EN(150), fill=INK, anchor="ms")
    d.text((W / 2, 920), "= 埋める", font=m.JP(66), fill=(200, 52, 48), anchor="ms")
    m.draw_fit(d, (W / 2, 1010), "The dog buried a bone in the yard.", m.EN(52), INK, width=W - 300)
    m.draw_fit(d, (W / 2, 1100), "(犬が庭に骨を埋めた)", m.JP(38), (110, 110, 110), width=W - 300, jp=True)
    shadow(d, 260, 1440, 180)
    m.owl(d, 260, 1260, 180, "happy", seed=41 + i % 3)
    shadow(d, 820, 1440, 180)
    m.penguin(d, 820, 1260, 170, "smug", hat_on=False, seed=51 + i % 3)
    caption(d, "ベリーを うめる で bury!", 1640, 58)
    d.text((W - 60, H - 60), m.HANDLE, font=m.EN(40), fill=(120, 110, 100), anchor="rm")
    return img


def scene_bury_goro(i):
    """最後:「ベリーを うめる」を大きく出して、声に出して2回。"""
    img = stage(390 + i % 3)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([90, 640, W - 90, 1060], radius=40, fill=(255, 252, 245), outline=INK, width=6)
    s = 1.0 + max(0, 0.25 - i / FPS) * 0.6  # 出た瞬間だけ少し大きく
    f = m.JP(int(118 * s))
    parts = [("ベリーを", (230, 120, 110)), ("うめる", (110, 160, 210))]
    x = W / 2 - (sum(f.getlength(p) for p, _ in parts) + 36) / 2
    for p, c in parts:
        d.text((x, 860), p, font=f, fill=c, anchor="ls")
        x += f.getlength(p) + 36
    d.text((W / 2, 985), "= bury(埋める)", font=m.JP(52), fill=INK, anchor="ms")
    shadow(d, 300, 1440, 200)
    m.penguin(d, 300, 1240, 210, "happy", hat_on=False, seed=51 + i % 3)
    shadow(d, 790, 1440, 200)
    m.owl(d, 790, 1240, 200, "happy", seed=41 + i % 3)
    jsfx(img, (545, 1180), "せーの!", 70, (220, 90, 70), 6)
    caption(d, "声に出して、もう1回!", 1640, 58)
    d.text((W - 60, H - 60), m.HANDLE, font=m.EN(40), fill=(120, 110, 100), anchor="rm")
    return img


# ---- scold(叱る):「スコールみたいに しかるど!」 ----
def cloud(d, cx, cy, s, seed, rain=True, t=0):
    for dx, dy, r in ((-0.45, 0.1, 0.32), (-0.1, -0.12, 0.42), (0.3, 0.02, 0.36), (0.55, 0.15, 0.25)):
        m.shape(d, [(cx + s * dx + s * r * math.cos(a), cy + s * dy + s * r * 0.8 * math.sin(a)) for a in (k * math.pi / 12 for k in range(25))],
                (150, 155, 170), w=4, seed=seed)
    if rain:
        r = random.Random(seed + t)
        for k in range(14):
            x = cx - s * 0.6 + k * s * 0.09 + r.uniform(-6, 6)
            y = cy + s * 0.35 + r.uniform(0, s * 0.6)
            d.line([(x, y), (x - 10, y + 46)], fill=(120, 160, 210), width=5)


def anger(d, x, y, s=26):
    """怒りマーク(💢)"""
    for a in (45, 135, 225, 315):
        r = math.radians(a)
        cx, cy = x + s * 0.55 * math.cos(r), y + s * 0.55 * math.sin(r)
        d.arc([cx - s * 0.5, cy - s * 0.5, cx + s * 0.5, cy + s * 0.5], a + 90, a + 270, fill=(220, 60, 50), width=6)


def scene_scold_hook(i):
    img = stage(400 + i % 3)
    d = ImageDraw.Draw(img)
    shadow(d, 540, 1400, 260)
    m.penguin(d, 540, 1150, 300, "shock", hat_on=False, seed=51 + i % 3)
    m.sweat(d, 700, 1000, 30)
    caption(d, "scold、", 820, 96, box=False)
    caption(d, "1秒で覚えられる?", 950, 80, color=(200, 52, 48), box=False)
    return img


def scene_scold_eat(i):
    img = stage(410 + i % 3)
    d = ImageDraw.Draw(img)
    table(d, 420 + i % 3)
    for k, x in enumerate((420, 520, 620)):  # 食べつくした魚の骨
        d.line([(x - 40, 1150), (x + 40, 1150)], fill=(120, 120, 130), width=5)
        for j in range(3):
            d.line([(x - 20 + j * 18, 1135), (x - 14 + j * 18, 1150), (x - 20 + j * 18, 1165)], fill=(120, 120, 130), width=4)
    shadow(d, 300, 1440, 200)
    m.penguin(d, 300, 1230, 210, "happy", hat_on=False, seed=51 + i % 3)
    jsfx(img, (560, 1000), "ペロリ", 80, (220, 90, 70), 8)
    caption(d, "部長のおやつ、ぜんぶ食べちゃった", 1640, 54)
    return img


def scene_scold_rain(i, n):
    img = stage(430 + i % 3)
    d = ImageDraw.Draw(img)
    shadow(d, 330, 1440, 200)
    m.penguin(d, 330, 1240, 200, "shock", hat_on=False, seed=51 + i % 3)
    cloud(d, 330, 820, 260, 440, rain=True, t=i)
    shadow(d, 790, 1440, 200)
    m.owl(d, 790, 1230, 210, "shock", seed=41 + i % 3)
    anger(d, 900, 1030, 46)
    jsfx(img, (560, 700), "ザーッ!", 90, (90, 130, 200), -6)
    caption(d, "ナビのお説教が、スコール級!", 1640, 58)
    return img


def scene_scold_word(i):
    img = stage(450 + i % 3)
    d = ImageDraw.Draw(img)
    shadow(d, 300, 1440, 220)
    m.penguin(d, 300, 1230, 230, "shock", hat_on=False, seed=51 + i % 3)
    jsfx(img, (720, 1150), "ドン!", 110, (220, 60, 50), -8)
    d.rounded_rectangle([90, 600, W - 90, 1020], radius=40, fill=(255, 252, 245), outline=INK, width=6)
    step = min(3, 1 + i // 4)
    parts = [("スコール", (110, 160, 210)), ("ど!", (230, 120, 110))]
    f = m.JP(110)
    x = W / 2 - (sum(f.getlength(p) for p, _ in parts) + 24) / 2
    for k, (p, c) in enumerate(parts):
        d.text((x, 740), p, font=f, fill=c if k < step else (215, 210, 205), anchor="ls")
        x += f.getlength(p) + 24
    if step >= 3:
        line = [("scold", (110, 160, 210)), (" = ", INK), ("叱る", (230, 120, 110))]
        fonts = [m.EN(120), m.EN(90), m.JP(84)]
        x = W / 2 - sum(ff.getlength(t) for (t, _), ff in zip(line, fonts)) / 2
        for (t, c), ff in zip(line, fonts):
            d.text((x, 885), t, font=ff, fill=c, anchor="ls")
            x += ff.getlength(t)
    d.text((W / 2, 975), "発音は「スコウルド」", font=m.JP(44), fill=(110, 110, 110), anchor="ms")
    return img


def scene_scold_meaning(i):
    img = stage(470 + i % 3)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([110, 640, W - 110, 1180], radius=40, fill=(255, 252, 245), outline=INK, width=6)
    d.text((W / 2, 800), "scold", font=m.EN(150), fill=INK, anchor="ms")
    d.text((W / 2, 920), "= 叱る", font=m.JP(66), fill=(200, 52, 48), anchor="ms")
    m.draw_fit(d, (W / 2, 1010), "My mom scolded me for coming home late.", m.EN(50), INK, width=W - 300)
    m.draw_fit(d, (W / 2, 1100), "(帰りが遅くて、母に叱られた)", m.JP(38), (110, 110, 110), width=W - 300, jp=True)
    shadow(d, 260, 1440, 180)
    m.owl(d, 260, 1260, 180, "smug", seed=41 + i % 3)
    shadow(d, 820, 1440, 180)
    m.penguin(d, 820, 1260, 170, "shock", hat_on=False, seed=51 + i % 3)
    m.sweat(d, 900, 1180, 22)
    caption(d, "スコールど! で scold!", 1640, 58)
    return img


def scene_scold_goro(i):
    img = stage(490 + i % 3)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([90, 640, W - 90, 1060], radius=40, fill=(255, 252, 245), outline=INK, width=6)
    s = 1.0 + max(0, 0.25 - i / FPS) * 0.6
    f = m.JP(int(96 * s))
    parts = [("スコールみたいに", (110, 160, 210)), ("しかるど!", (230, 120, 110))]
    for k, (p, c) in enumerate(parts):
        d.text((W / 2, 800 + k * 120), p, font=f, fill=c, anchor="ms")
    d.text((W / 2, 1025), "= scold(叱る)", font=m.JP(48), fill=INK, anchor="ms")
    shadow(d, 300, 1440, 200)
    m.penguin(d, 300, 1240, 210, "happy", hat_on=False, seed=51 + i % 3)
    shadow(d, 790, 1440, 200)
    m.owl(d, 790, 1240, 200, "happy", seed=41 + i % 3)
    jsfx(img, (545, 1180), "せーの!", 70, (220, 90, 70), 6)
    caption(d, "声に出して、もう1回!", 1640, 58)
    d.text((W - 60, H - 60), m.HANDLE, font=m.EN(40), fill=(120, 110, 100), anchor="rm")
    return img


# ---- flee(逃げる):「フリーで、にげる!」 ----
def paper_pile(d, cx, bottom, n, seed):
    r = random.Random(seed)
    for k in range(n):
        y = bottom - k * 22
        dx = r.uniform(-14, 14)
        m.shape(d, m.rrect_pts(cx - 110 + dx, y - 22, cx + 110 + dx, y, 4), (252, 250, 244), w=4, seed=seed + k)


def scene_flee_hook(i):
    img = stage(500 + i % 3)
    d = ImageDraw.Draw(img)
    shadow(d, 540, 1400, 260)
    m.penguin(d, 540, 1150, 300, "shock", hat_on=False, seed=51 + i % 3)
    m.sweat(d, 700, 1000, 30)
    caption(d, "flee、", 820, 96, box=False)
    caption(d, "1秒で覚えられる?", 950, 80, color=(200, 52, 48), box=False)
    return img


def scene_flee_work(i):
    img = stage(510 + i % 3)
    d = ImageDraw.Draw(img)
    paper_pile(d, 540, 1400, 4 + min(10, i // 2), 520)
    shadow(d, 260, 1440, 200)
    m.penguin(d, 260, 1230, 210, "shock", hat_on=False, seed=51 + i % 3)
    m.sweat(d, 380, 1080, 26)
    shadow(d, 820, 1440, 220)
    m.capybara(d, 840, 1300, 260, "calm", seed=91 + i % 3)
    jsfx(img, (560, 900), "ドサッ", 80, (150, 120, 90), -6)
    caption(d, "部長から、仕事が山盛り…", 1640, 58)
    return img


def scene_flee_run(i, n):
    img = stage(530 + i % 3)
    d = ImageDraw.Draw(img)
    paper_pile(d, 300, 1400, 14, 520)
    x = 360 + (i / max(1, n - 1)) * 640
    for k in range(4):  # スピード線
        y = 1120 + k * 60
        d.line([(x - 300, y), (x - 140, y)], fill=(150, 140, 130), width=6)
    shadow(d, x, 1440, 200)
    m.penguin(d, x, 1230, 210, "happy", hat_on=False, seed=51 + i % 3)
    jsfx(img, (560, 760), "定時!", 90, (200, 52, 48), -6)
    jsfx(img, (x - 60, 960), "ダーッ!", 70, (90, 130, 200), 8)
    caption(d, "定時になった瞬間、フリーになって…", 1640, 54)
    return img


def scene_flee_word(i):
    img = stage(550 + i % 3)
    d = ImageDraw.Draw(img)
    shadow(d, 780, 1440, 220)
    m.penguin(d, 780, 1230, 230, "happy", hat_on=False, seed=51 + i % 3)
    jsfx(img, (300, 1150), "ドン!", 110, (220, 60, 50), -8)
    d.rounded_rectangle([90, 600, W - 90, 1020], radius=40, fill=(255, 252, 245), outline=INK, width=6)
    step = min(3, 1 + i // 4)
    parts = [("フリーで", (110, 160, 210)), ("にげる!", (230, 120, 110))]
    f = m.JP(110)
    x = W / 2 - (sum(f.getlength(p) for p, _ in parts) + 24) / 2
    for k, (p, c) in enumerate(parts):
        d.text((x, 740), p, font=f, fill=c if k < step else (215, 210, 205), anchor="ls")
        x += f.getlength(p) + 24
    if step >= 3:
        line = [("flee", (110, 160, 210)), (" = ", INK), ("逃げる", (230, 120, 110))]
        fonts = [m.EN(120), m.EN(90), m.JP(84)]
        x = W / 2 - sum(ff.getlength(t) for (t, _), ff in zip(line, fonts)) / 2
        for (t, c), ff in zip(line, fonts):
            d.text((x, 885), t, font=ff, fill=c, anchor="ls")
            x += ff.getlength(t)
    d.text((W / 2, 975), "発音は「フリー」(free とは別の単語)", font=m.JP(40), fill=(110, 110, 110), anchor="ms")
    return img


def scene_flee_meaning(i):
    img = stage(570 + i % 3)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([110, 640, W - 110, 1180], radius=40, fill=(255, 252, 245), outline=INK, width=6)
    d.text((W / 2, 800), "flee", font=m.EN(150), fill=INK, anchor="ms")
    d.text((W / 2, 920), "= 逃げる(過去形は fled)", font=m.JP(58), fill=(200, 52, 48), anchor="ms")
    m.draw_fit(d, (W / 2, 1010), "The birds fled when the dog barked.", m.EN(50), INK, width=W - 300)
    m.draw_fit(d, (W / 2, 1100), "(犬がほえると、鳥たちは逃げた)", m.JP(38), (110, 110, 110), width=W - 300, jp=True)
    shadow(d, 260, 1440, 180)
    m.capybara(d, 280, 1300, 220, "shock", seed=91 + i % 3)
    shadow(d, 820, 1440, 180)
    m.penguin(d, 820, 1260, 170, "happy", hat_on=False, seed=51 + i % 3)
    caption(d, "フリーで にげる! で flee!", 1640, 58)
    return img


def scene_flee_goro(i):
    img = stage(590 + i % 3)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([90, 640, W - 90, 1060], radius=40, fill=(255, 252, 245), outline=INK, width=6)
    s = 1.0 + max(0, 0.25 - i / FPS) * 0.6
    f = m.JP(int(96 * s))
    parts = [("フリーで", (110, 160, 210)), ("にげる!", (230, 120, 110))]
    for k, (p, c) in enumerate(parts):
        d.text((W / 2, 800 + k * 120), p, font=f, fill=c, anchor="ms")
    d.text((W / 2, 1025), "= flee(逃げる)", font=m.JP(48), fill=INK, anchor="ms")
    shadow(d, 300, 1440, 200)
    m.penguin(d, 300, 1240, 210, "happy", hat_on=False, seed=51 + i % 3)
    shadow(d, 790, 1440, 200)
    m.owl(d, 790, 1240, 200, "happy", seed=41 + i % 3)
    jsfx(img, (545, 1180), "せーの!", 70, (220, 90, 70), 6)
    caption(d, "声に出して、もう1回!", 1640, 58)
    d.text((W - 60, H - 60), m.HANDLE, font=m.EN(40), fill=(120, 110, 100), anchor="rm")
    return img


def voice(who, text, speed=1.0):
    """4コマと同じ ElevenLabs のキャラの声(ナビ=Teddy、ペン=Mia)。大きさをそろえる。保存ずみなら使い回す"""
    import manga_reel as mr
    a = mr.eleven(who, text, speed)
    a = a * (0.07 / (float(np.sqrt(np.mean(a ** 2))) or 1.0))
    return (a * min(1.0, 0.95 / (float(np.max(np.abs(a))) or 1.0))).astype(np.float32)


def say(pipe, text, voice):
    return np.concatenate([a for _, _, a in pipe(text, voice=voice, speed=0.9)])


def tone(freq, dur, vol=0.06, decay=14):
    t = np.arange(int(SR * dur)) / SR
    return (vol * np.sin(2 * np.pi * freq * t) * np.exp(-t * decay)).astype(np.float32)


def mr_env():
    import manga_reel as mr
    mr.load_env()


def plans(pipe):
    gap = lambda s: np.zeros(int(SR * s), dtype=np.float32)
    # 単語ごとの (秒, シーン, その場面の音)
    return {
        "abandon": [
            (1.3, lambda i: scene_hook(i), [tone(660, 0.15), gap(0.2)]),
            (1.8, lambda i: scene_dinner(i), [tone(880, 0.12, 0.04)]),
            (1.8, lambda i: scene_toss(i, int(1.8 * FPS)), [tone(1100, 0.1, 0.04)]),
            (2.4, lambda i: scene_don(i), [tone(90, 0.4, 0.25, 6), gap(0.3), say(pipe, "abandon", "bf_emma")]),
            (4.2, lambda i: scene_meaning(i), [gap(0.2), say(pipe, "Abandon.", "bm_george"), gap(0.4), say(pipe, "They abandoned the old boat.", "bf_emma")]),
        ],
        "scold": [
            (1.3, lambda i: scene_scold_hook(i), [tone(660, 0.15), gap(0.2)]),
            (1.8, lambda i: scene_scold_eat(i), [tone(880, 0.12, 0.04)]),
            (2.0, lambda i: scene_scold_rain(i, int(2.0 * FPS)), [tone(1100, 0.1, 0.04)]),
            (2.6, lambda i: scene_scold_word(i), [tone(90, 0.4, 0.25, 6), gap(0.3), voice("navi", "Scold!"), gap(0.3), voice("pen", "Scold...")]),
            (4.4, lambda i: scene_scold_meaning(i), [gap(0.2), voice("navi", "Scold."), gap(0.4), voice("pen", "My mom scolded me for coming home late.")]),
            (3.2, lambda i: scene_scold_goro(i), [tone(660, 0.15), gap(0.15), voice("pen", "スコールみたいに、しかるど!"), gap(0.35), voice("navi", "スコールみたいに、しかるど!"), gap(0.6)]),
        ],
        "flee": [
            (1.3, lambda i: scene_flee_hook(i), [tone(660, 0.15), gap(0.2)]),
            (1.8, lambda i: scene_flee_work(i), [tone(880, 0.12, 0.04)]),
            (2.0, lambda i: scene_flee_run(i, int(2.0 * FPS)), [tone(1100, 0.1, 0.04)]),
            (2.6, lambda i: scene_flee_word(i), [tone(90, 0.4, 0.25, 6), gap(0.3), voice("navi", "Flee!"), gap(0.3), voice("pen", "Flee!")]),
            (4.4, lambda i: scene_flee_meaning(i), [gap(0.2), voice("navi", "Flee."), gap(0.4), voice("pen", "The birds fled when the dog barked.")]),
            (3.2, lambda i: scene_flee_goro(i), [tone(660, 0.15), gap(0.15), voice("pen", "フリーで、にげる!"), gap(0.35), voice("navi", "フリーで、にげる!"), gap(0.6)]),
        ],
        "bury": [
            (1.3, lambda i: scene_bury_hook(i), [tone(660, 0.15), gap(0.2)]),
            (1.8, lambda i: scene_bury_pick(i), [tone(880, 0.12, 0.04)]),
            (2.0, lambda i: scene_bury_dig(i, int(2.0 * FPS)), [tone(1100, 0.1, 0.04)]),
            (2.6, lambda i: scene_bury_word(i), [tone(90, 0.4, 0.25, 6), gap(0.3), voice("pen", "Bury."), gap(0.3), voice("navi", "Berry!")]),
            (4.4, lambda i: scene_bury_meaning(i), [gap(0.2), voice("navi", "Bury."), gap(0.4), voice("pen", "The dog buried a bone in the yard.")]),
            (3.2, lambda i: scene_bury_goro(i), [tone(660, 0.15), gap(0.15), voice("pen", "ベリーを、うめる!"), gap(0.35), voice("navi", "ベリーを、うめる!"), gap(0.6)]),
        ],
    }


def main():
    from kokoro import KPipeline
    import soundfile as sf
    name = sys.argv[1] if len(sys.argv) > 1 else "abandon"
    pipe = KPipeline(lang_code="b", repo_id="hexgrad/Kokoro-82M")
    gap = lambda s: np.zeros(int(SR * s), dtype=np.float32)
    mr_env()
    plan = plans(pipe)[name]
    OUT.mkdir(parents=True, exist_ok=True)
    frames, audio = [], []
    for dur, draw, sounds in plan:
        clip = np.concatenate(sounds)
        n = int(np.ceil(max(dur, len(clip) / SR + 0.15) * FPS))  # 音が長いときは映像ものばして、ずれないように
        audio.append(np.concatenate([clip, gap(n / FPS - len(clip) / SR)]))
        for i in range(n):
            img = draw(i)
            frames.append(finish(img, len(frames)))
    total = len(frames) / FPS
    out = OUT / f"{name}.mp4"
    with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
        sf.write(wav.name, np.concatenate(audio), SR)
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-i", wav.name, "-stream_loop", "-1", "-i", str(ROOT / "assets" / "manga_bgm" / "cozy-places.mp3"),
               "-filter_complex", f"[2:a]volume=0.06[b];[1:a]aresample=44100,volume=1.6[v];[v][b]amix=inputs=2:duration=first:normalize=0[a]",
               "-map", "0:v", "-map", "[a]", "-t", f"{total:.2f}", "-r", "30",
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "aac", "-movflags", "+faststart", str(out)]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for f in frames:
            p.stdin.write(f.tobytes())
        p.stdin.close()
        p.wait()
    print(f"✓ {out}({total:.1f}秒)")


if __name__ == "__main__":
    main()
