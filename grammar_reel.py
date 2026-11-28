"""初心者向け 英文法ショート動画(見本)。テキスト+効果音+BGM。ナレーションなし。

    python3 grammar_reel.py 1   # 青コラージュ:命令文, and / or
    python3 grammar_reel.py 2   # 方眼紙リスト:時の接続詞5つ
    python3 grammar_reel.py 3   # クリーム:both / either / neither
例文はすべてオリジナル(参考書は題材選びのみ)。
"""
import math
import random
import subprocess
import sys
import wave
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).parent
F = ROOT / "fonts"
W, H, FPS = 1080, 1920, 30
OUT = ROOT / "out" / "grammar"


def font(name, size):
    return ImageFont.truetype(str(F / name), size)


def jp(size, bold=True):
    f = ImageFont.truetype(str(F / "NotoSansJP.ttf"), size)
    try:
        f.set_variation_by_axes([800 if bold else 500])
    except Exception:
        pass
    return f


def serif(size, w=600):
    f = ImageFont.truetype(str(F / "SourceSerif4.ttf"), size)
    try:
        f.set_variation_by_axes([w, 20])
    except Exception:
        pass
    return f


DELA = lambda s: font("DelaGothicOne-Regular.ttf", s)

THEMES = {
    "blue": dict(bg=(28, 58, 200), big=(232, 225, 207), sub=(255, 255, 255), accent=(124, 252, 90), tape=(236, 230, 214), ink=(20, 20, 20)),
    "cream": dict(bg=(238, 232, 214), big=(15, 15, 15), sub=(15, 15, 15), accent=(207, 62, 34), tape=(15, 15, 15), ink=(238, 232, 214)),
    "grid": dict(bg=(250, 250, 248), big=(20, 20, 20), sub=(20, 20, 20), accent=(37, 99, 235), tape=(37, 99, 235), ink=(255, 255, 255)),
}


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def back(x):
    x = max(0.0, min(1.0, x))
    c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


# ---------- 背景 ----------
def background(theme):
    T = THEMES[theme]
    im = Image.new("RGB", (W, H), T["bg"])
    d = ImageDraw.Draw(im)
    rnd = random.Random(7)
    if theme == "grid":
        for x in range(0, W, 54):
            d.line([(x, 0), (x, H)], fill=(228, 230, 236), width=2)
        for y in range(0, H, 54):
            d.line([(0, y), (W, y)], fill=(228, 230, 236), width=2)
        return im
    # 紙の質感:ノイズ+薄い引っかき線
    noise = Image.effect_noise((W, H), 18).convert("L")
    tint = Image.new("RGB", (W, H), (255, 255, 255) if theme == "blue" else (120, 100, 70))
    im = Image.composite(tint, im, noise.point(lambda v: int(max(0, v - 128) * 0.22)))
    d = ImageDraw.Draw(im)
    for _ in range(26):
        x, y = rnd.randint(0, W), rnd.randint(0, H)
        pts = [(x, y)]
        for _ in range(4):
            x += rnd.randint(-60, 60); y += rnd.randint(30, 90); pts.append((x, y))
        col = tuple(min(255, c + 30) for c in T["bg"]) if theme == "blue" else tuple(max(0, c - 22) for c in T["bg"])
        d.line(pts, fill=col, width=2)
    return im


# ---------- 部品 ----------
def text_w(f, s):
    b = f.getbbox(s)
    return b[2] - b[0]


def paste_rot(base, layer, cx, cy, angle, alpha=1.0, scale=1.0):
    if scale != 1.0:
        layer = layer.resize((max(1, int(layer.width * scale)), max(1, int(layer.height * scale))), Image.LANCZOS)
    layer = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    if alpha < 1:
        a = layer.split()[3].point(lambda v: int(v * alpha))
        layer.putalpha(a)
    base.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


def big(base, T, t, s, y, size=190, d=0.0, color=None):
    if t < d: return
    k = back((t - d) / 0.35)
    f = DELA(size)
    while text_w(f, s) > W - 100: size -= 8; f = DELA(size)
    lay = Image.new("RGBA", (text_w(f, s) + 40, int(size * 1.4)), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((20, 0), s, font=f, fill=color or T["big"])
    paste_rot(base, lay, W / 2, y, 0, alpha=min(1, (t - d) / 0.15), scale=0.6 + 0.4 * k)


def tape(base, T, t, s, cx, cy, angle=-4, d=0.0, size=64, f=None):
    if t < d: return
    k = back((t - d) / 0.3)
    f = f or jp(size)
    tw = text_w(f, s)
    lay = Image.new("RGBA", (tw + 90, size + 60), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    rnd = random.Random(len(s))
    L, R = 8, lay.width - 8
    poly = [(L + rnd.randint(-4, 6), 8 + i * 10) for i in range((lay.height - 16) // 10 + 1)]
    poly += [(R + rnd.randint(-6, 4), lay.height - 8 - i * 10) for i in range((lay.height - 16) // 10 + 1)]
    g.polygon(poly, fill=T["tape"] + (245,))
    g.text((45, 22), s, font=f, fill=T["ink"])
    sh = Image.new("RGBA", lay.size, (0, 0, 0, 0)); sh.putalpha(lay.split()[3].point(lambda v: v // 3))
    sh = sh.filter(ImageFilter.GaussianBlur(6))
    paste_rot(base, sh, cx + 8, cy + 10, angle, scale=0.7 + 0.3 * k)
    paste_rot(base, lay, cx, cy, angle, scale=0.7 + 0.3 * k)


def scribble(base, T, t, cx, cy, rx, ry, d=0.0, dur=0.45, width=12):
    if t < d: return
    p = ease((t - d) / dur)
    g = ImageDraw.Draw(base)
    n = int(80 * 1.15 * p)
    pts = []
    for i in range(n + 1):
        a = -2.4 + i / 80 * 2 * math.pi
        r = 1 + 0.06 * math.sin(i / 6) + 0.05 * i / 80
        pts.append((cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)))
    if len(pts) > 1:
        g.line(pts, fill=T["accent"], width=width, joint="curve")


def cross(base, T, t, cx, cy, s=70, d=0.0, width=16):
    if t < d: return
    p = ease((t - d) / 0.3)
    g = ImageDraw.Draw(base)
    a = min(1, p * 2); b = max(0, p * 2 - 1)
    g.line([(cx - s, cy - s), (cx - s + 2 * s * a, cy - s + 2 * s * a)], fill=T["accent"], width=width)
    if b > 0:
        g.line([(cx + s, cy - s), (cx + s - 2 * s * b, cy - s + 2 * s * b)], fill=T["accent"], width=width)


def card(base, T, t, rows, cy, d=0.0, angle=2, wmax=980, hl=(255, 232, 92)):
    """rows: [(segments, kind)]  segments=[(text, highlighted)]  kind: en / ja"""
    if t < d: return
    k = ease((t - d) / 0.35)
    fonts = {"en": serif(60), "ja": jp(42, bold=False), "q": jp(48)}
    gap = {"en": 88, "ja": 72, "q": 78}
    hgt = 60 + sum(gap[r[1]] for r in rows) + 20
    lay = Image.new("RGBA", (wmax, hgt), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    g.rounded_rectangle([0, 0, wmax - 1, hgt - 1], 18, fill=(255, 255, 255, 255))
    y = 40
    for segs, kind in rows:
        f = fonts[kind]
        x = 50
        for s, h in segs:
            w = text_w(f, s)
            if h:
                g.rectangle([x - 4, y + 8, x + w + 4, y + gap[kind] - 12], fill=hl + (255,))
            g.text((x, y), s, font=f, fill=(20, 20, 20) if kind != "ja" else (90, 90, 90))
            x += w
        y += gap[kind]
    sh = Image.new("RGBA", lay.size, (0, 0, 0, 0)); sh.putalpha(lay.split()[3].point(lambda v: v // 3))
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    off = (1 - k) * 260
    paste_rot(base, sh, W / 2 + 10, cy + off + 14, angle, alpha=k)
    paste_rot(base, lay, W / 2, cy + off, angle, alpha=k)


def subtitle(base, T, s, y=1400):
    if not s: return
    g = ImageDraw.Draw(base)
    f = jp(54)
    for i, line in enumerate(s.split("\n")):
        w = text_w(f, line)
        g.text(((W - w) / 2, y + i * 78), line, font=f, fill=T["sub"])


# ---------- 方眼紙用 ----------
def timeline(base, T, prog, x=60):
    g = ImageDraw.Draw(base)
    g.line([(x, 230), (x, 1560)], fill=(215, 220, 232), width=8)
    y = 230 + (1560 - 230) * prog
    g.line([(x, 230), (x, y)], fill=T["accent"], width=8)
    g.ellipse([x - 22, y - 22, x + 22, y + 22], fill=(255, 255, 255), outline=T["accent"], width=7)


def caption_top(base, T, s, t, y=330):
    g = ImageDraw.Draw(base)
    f = jp(64)
    for i, line in enumerate(s.split("\n")):
        n = len(line)
        shown = line[: max(0, min(n, int(n * t / 0.5) + 1))]
        w = text_w(f, line)
        g.text(((W - w) / 2, y + i * 74), shown, font=f, fill=T["big"])


def numcard(base, T, t, no, word, mean, en, ja, cy=900, d=0.1):
    if t < d: return
    k = ease((t - d) / 0.35)
    w, h = 900, 700
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    g.rounded_rectangle([0, 0, w - 1, h - 1], 26, fill=(255, 255, 255, 255), outline=(225, 228, 236, 255), width=3)
    g.text((40, 20), f"{no:02d}", font=font("Anton-Regular.ttf", 150), fill=(255, 255, 255, 255), stroke_width=4, stroke_fill=T["accent"] + (255,))
    g.text((230, 46), word, font=serif(96, 700), fill=(20, 20, 20, 255))
    g.text((236, 160), mean, font=jp(44), fill=T["accent"] + (255,))
    g.rounded_rectangle([40, 270, w - 40, h - 40], 18, fill=(246, 247, 251, 255))
    # 例文:word を蛍光ペン
    f = serif(50 if text_w(serif(50, 500), "".join(a for a, _ in en)) < w - 140 else 44, 500)
    x, y = 70, 310
    for part in en:
        s, hlt = part
        pw = text_w(f, s)
        if x + pw > w - 60 and not s.startswith(" "):
            pass
        if hlt:
            g.rectangle([x - 3, y + 10, x + pw + 3, y + 58], fill=(255, 232, 92, 255))
        g.text((x, y), s, font=f, fill=(20, 20, 20, 255))
        x += pw
    g.text((70, 420), ja, font=jp(42, bold=False), fill=(80, 80, 80, 255))
    tag = jp(28)
    g.rounded_rectangle([70, 540, 70 + text_w(tag, "例文") + 40, 590], 25, fill=T["accent"] + (255,))
    g.text((90, 542), "例文", font=tag, fill=(255, 255, 255, 255))
    sh = Image.new("RGBA", lay.size, (0, 0, 0, 0)); sh.putalpha(lay.split()[3].point(lambda v: v // 5))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    off = (1 - k) * 120
    paste_rot(base, sh, W / 2 + 30, cy + off + 16, 0, alpha=k)
    paste_rot(base, lay, W / 2 + 30, cy + off, 0, alpha=k)


# ---------- 台本 ----------
def V1():
    """命令文, and / or(青コラージュ)"""
    S = []
    S.append((2.6, "この英語、\n意味わかる?", lambda b, T, t: (
        card(b, T, t, [([("Leave now, ", False), ("and", True), (" you'll catch", False)], "en"), ([("the bus.", False)], "en")], 900, d=0.1, angle=-2))))
    S.append((2.2, "and は「そして」…?", lambda b, T, t: (
        big(b, T, t, "and", 700, size=260, d=0.0),
        tape(b, T, t, "そして", 540, 980, angle=5, d=0.5, size=70),
        cross(b, T, t, 540, 980, s=90, d=1.2))))
    S.append((2.8, "命令文のあとの and は\n「そうすれば」", lambda b, T, t: (
        big(b, T, t, "and", 700, size=260),
        tape(b, T, t, "そうすれば", 540, 980, angle=-4, d=0.2, size=80),
        scribble(b, T, t, 540, 980, 330, 110, d=0.8))))
    S.append((3.0, "今出なさい、\nそうすれば間に合うよ", lambda b, T, t: (
        card(b, T, t, [([("Leave now, ", False), ("and", True), (" you'll catch", False)], "en"), ([("the bus.", False)], "en"),
                       ([("今出なさい、", False), ("そうすれば", True), ("バスに間に合うよ", False)], "ja")], 900, d=0.0, angle=-2))))
    S.append((2.2, "じゃあ or は?", lambda b, T, t: (
        big(b, T, t, "or", 700, size=320),
        tape(b, T, t, "または", 540, 980, angle=4, d=0.5, size=70),
        cross(b, T, t, 540, 980, s=90, d=1.1))))
    S.append((2.8, "命令文のあとの or は\n「さもないと」", lambda b, T, t: (
        big(b, T, t, "or", 700, size=320),
        tape(b, T, t, "さもないと", 540, 980, angle=-3, d=0.2, size=80),
        scribble(b, T, t, 540, 980, 330, 110, d=0.8))))
    S.append((3.0, "さもないと、乗り遅れるよ", lambda b, T, t: (
        card(b, T, t, [([("Leave now, ", False), ("or", True), (" you'll miss", False)], "en"), ([("the bus.", False)], "en"),
                       ([("今出なさい、", False), ("さもないと", True), ("乗り遅れるよ", False)], "ja")], 980, angle=2))))
    S.append((4.4, "( ) に入るのは?\n答えはコメントで 1 か 2", lambda b, T, t: (
        big(b, T, t, "Q.", 520, size=200, color=THEMES["blue"]["accent"]),
        card(b, T, t, [([("Be quiet, (    ) the", False)], "en"), ([("baby will wake up.", False)], "en"),
                       ([("1  and      2  or", False)], "q")], 880, d=0.2, angle=-1),
        tape(b, T, t, "静かにして、さもないと赤ちゃんが起きる", 540, 1200, angle=-2, d=0.8, size=46))))
    NAR = {0: [('ja', 'この英語、わかりますか?'), ('m', "Leave now, and you'll catch the bus.")], 1: [('ja', 'アンドは「そして」?')], 2: [('ja', '実は、命令文のあとだと「そうすれば」なんです。')], 3: [('f', "Leave now, and you'll catch the bus."), ('ja', '今出なさい、そうすれば間に合うよ。')], 4: [('ja', 'じゃあ、オアのほうは、どうでしょう?')], 5: [('ja', '命令文のあとのオアは、「さもないと」という意味です。')], 6: [('m', "Leave now, or you'll miss the bus."), ('f', "Leave now, or you'll miss the bus."), ('ja', 'さもないと、乗り遅れるよ。')], 7: [('ja', '問題です。1のアンドか、2のオアか。答えは、コメントで教えてね。')]}
    S = [x + (NAR.get(i, []),) for i, x in enumerate(S)]
    return "blue", S


def V2():
    """時を表す接続詞5つ(方眼紙リスト)"""
    items = [
        (1, "when", "〜するとき", [("Call me ", False), ("when", True), (" you get home.", False)], "家に着いたら電話してね。"),
        (2, "while", "〜する間に", [("I fell asleep ", False), ("while", True), (" I was reading.", False)], "読んでいる間に寝てしまった。"),
        (3, "before", "〜する前に", [("Wash your hands ", False), ("before", True), (" you eat.", False)], "食べる前に手を洗ってね。"),
        (4, "after", "〜したあとで", [("Let's go out ", False), ("after", True), (" it stops raining.", False)], "雨がやんだら出かけよう。"),
        (5, "since", "〜からずっと", [("I've lived here ", False), ("since", True), (" I was ten.", False)], "10歳からずっとここに住んでいる。"),
    ]
    S = []
    S.append((2.6, "", lambda b, T, t: (
        caption_top(b, T, "「〜するとき」の仲間\n5つ言える?", t, y=560),
        big(b, T, t, "5", 1100, size=460, d=0.5, color=THEMES["grid"]["accent"]))))
    for i, (no, w_, m, en, ja) in enumerate(items):
        def f(b, T, t, no=no, w_=w_, m=m, en=en, ja=ja, i=i):
            caption_top(b, T, f"{no}つ目、{w_}", t)
            numcard(b, T, t, no, w_, m, en, ja)
        S.append((3.0, "", f))
    S.append((3.6, "", lambda b, T, t: (
        caption_top(b, T, "注意:since には\n「〜なので」の意味も", t, y=480),
        tape(b, T, t, "Since it was late, I went home.", 540, 860, angle=-2, d=0.4, size=54, f=serif(54)),
        tape(b, T, t, "遅かったので、家に帰った", 540, 1030, angle=2, d=0.9, size=52),
        big(b, T, t, "保存して復習", 1300, size=110, d=1.6, color=THEMES["grid"]["accent"]))))
    return "grid", S


def V3():
    """both / either / neither(クリーム)"""
    red = THEMES["cream"]["accent"]
    S = []
    S.append((2.4, "セットで覚える\n3兄弟", lambda b, T, t: (
        big(b, T, t, "both", 620, size=180), big(b, T, t, "either", 880, size=180, d=0.3), big(b, T, t, "neither", 1140, size=180, d=0.6, color=red))))
    trio = [
        ("both", "A and B", "AもBも両方", [("I like ", False), ("both", True), (" cats ", False), ("and", True), (" dogs.", False)], "猫も犬も両方好き。"),
        ("either", "A or B", "AかBのどちらか", [("You can have ", False), ("either", True), (" tea ", False), ("or", True), (" coffee.", False)], "紅茶かコーヒーのどちらかをどうぞ。"),
        ("neither", "A nor B", "AもBも〜ない", [("This soup is ", False), ("neither", True), (" hot ", False), ("nor", True), (" cold.", False)], "このスープは熱くも冷たくもない。"),
    ]
    for w_, pair, m, en, ja in trio:
        def f(b, T, t, w_=w_, pair=pair, m=m, en=en, ja=ja):
            big(b, T, t, f"{w_}", 520, size=220)
            big(b, T, t, pair, 730, size=120, d=0.2, color=red)
            tape(b, T, t, m, 540, 920, angle=-3, d=0.5, size=70)
            # 1行に収まらない例文は2行に
            card(b, T, t, [(en, "en"), ([(ja, False)], "ja")], 1220, d=0.9, angle=1, wmax=1020, hl=(245, 196, 180))
        S.append((3.4, "", f))
    S.append((4.4, "", lambda b, T, t: (
        big(b, T, t, "Q.", 520, size=200, color=red),
        tape(b, T, t, "私は肉も魚も食べない", 540, 760, angle=-2, d=0.2, size=60),
        card(b, T, t, [([("I eat (    ) meat (    ) fish.", False)], "en"), ([("1  either / or     2  neither / nor", False)], "q")], 1020, d=0.5, angle=1, wmax=1000),
        subtitle(b, T, "答えはコメントで 1 か 2", y=1300))))
    return "cream", S


# ---------- レッスンのひな型(grammar_lessons.py) ----------
def _segs(line):
    parts = line.split("*")
    return [(x, i % 2 == 1) for i, x in enumerate(parts) if x]


def rows(s, kind):
    return [(_segs(l), kind) for l in s.split("|")]


def plain(s):
    return s.replace("*", "").replace("|", " ")


def _tape_size(s, base=80):
    size = base
    while text_w(jp(size), s) > 860 and size > 40: size -= 4
    return size

HOOK = 1.3  # 冒頭フックの長さ(秒)。BGM の盛り上がりをここに合わせる
# 英文法リールの BGM(Uppbeat)。drop = 曲の中で急に盛り上がる位置(秒)
TRACKS = [
    dict(file="golden_age.mp3", drop=26.8, credit="Music: Golden Age / Walz — Music from #Uppbeat (free for Creators!)"),
    dict(file="days_off.mp3", drop=85.3, credit="Music: Days Off / Matrika — Music from #Uppbeat (free for Creators!)"),
    dict(file="jasmine.mp3", drop=27.7, credit="Music: Jasmine / 92elm — Music from #Uppbeat (free for Creators!)"),
]
JA_TEMPO = 1.45  # 日本語ナレーションの速さ(2026-11-28 ユーザー「この速さで」→ 全アカウント共通。v3 は速さ設定がないため atempo)


def track_for(no):
    return TRACKS[no % len(TRACKS)]


def hook_title(bb, T, t, title):
    import re
    parts = [x for x in re.split(r"(?<=[、?])", title) if x.strip()]
    if len(parts) == 1 and len(title) > 10:
        k = title.find(" ", len(title) // 2 - 3)
        parts = [title[:k], title[k:]] if k > 0 else [title]
    ys = [780] if len(parts) == 1 else [700, 880]
    for i, (line, y) in enumerate(zip(parts[:2], ys)):
        big(bb, T, t, line.strip(), y, size=120, d=0.08 * i)
    scribble(bb, T, t, 540, ys[-1] + 20, 470, 110, d=0.5, dur=0.5)



def comment_cta(bb, T, t, d=0.6, y=1340):
    """「答えと解説はコメント欄に →」右側のコメントボタンを指す(リールのコメントは画面右・高さ約70%)"""
    if t < d: return
    k = back((t - d) / 0.35)
    f = jp(46)
    s = "答えと解説はコメント欄に"
    w = text_w(f, s) + 150
    lay = Image.new("RGBA", (w, 110), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    g.rounded_rectangle([0, 0, w - 1, 109], 55, fill=T["accent"] + (255,))
    # 吹き出しアイコン
    g.ellipse([30, 28, 84, 76], outline=(20, 20, 20, 255), width=6)
    g.polygon([(38, 70), (34, 90), (54, 74)], fill=(20, 20, 20, 255))
    g.text((104, 22), s, font=f, fill=(20, 20, 20, 255))
    x0 = 900 - w / 2 * (0.6 + 0.4 * k)
    paste_rot(bb, lay, 900 - w / 2, y, 0, scale=0.6 + 0.4 * k)
    # 右へ動く矢印
    bob = 14 * math.sin((t - d) * 7)
    ax = 905 + bob
    gg = ImageDraw.Draw(bb)
    gg.line([(ax, y), (ax + 60, y)], fill=T["accent"], width=12)
    gg.polygon([(ax + 85, y), (ax + 52, y - 26), (ax + 52, y + 26)], fill=T["accent"])


def lesson(L):
    a, b2, q = L["a"], L["b"], L["q"]
    A = THEMES["blue"]["accent"]
    S = []
    # 0〜HOOK秒:タイトルを大きく(声なし)。HOOK秒で曲の盛り上がりと同時に本編へ
    S.append((HOOK, "", lambda bb, T, t: hook_title(bb, T, t, L.get("hook_big", L["title"])), []))
    S.append((2.6, L.get("hook_sub", "この英語、\n意味わかる?"), lambda bb, T, t: card(bb, T, t, rows(L["hook"], "en"), 900, d=0.0, angle=-2),
              [("ja", L.get("hook_say", "この英語、わかる?")), ("m", plain(L["hook"]))]))

    def ask(P, wrong_angle):
        def f(bb, T, t):
            big(bb, T, t, P["key"], 700, size=260)
            if P.get("wrong"):
                sz = _tape_size(P["wrong"], 70)
                tape(bb, T, t, P["wrong"], 540, 980, angle=wrong_angle, d=0.5, size=sz)
                cross(bb, T, t, 540, 980, s=90, d=1.1)
        return f

    def right(P, ang):
        def f(bb, T, t):
            big(bb, T, t, P["key"], 700, size=260)
            sz = _tape_size(P["right"])
            tape(bb, T, t, P["right"], 540, 980, angle=ang, d=0.2, size=sz)
            rx = min(500, text_w(jp(sz), P["right"]) / 2 + 90)
            scribble(bb, T, t, 540, 980, rx, 110, d=0.8)
        return f

    def ex(P, ang):
        return lambda bb, T, t: card(bb, T, t, rows(P["en"], "en") + rows(P["ja"], "ja"), 900, angle=ang)

    S.append((2.2, a.get("ask_sub", f"{a['key']} は「{a['wrong']}」…?"), ask(a, 5), [("ja", a.get("ask", f"{a['kana']}は「{a['wrong']}」?"))]))
    S.append((2.8, a["sub"], right(a, -4), [("ja", a["say"])]))
    S.append((3.0, plain(a["ja"]), ex(a, -2), [("f", plain(a["en"])), ("ja", a["ja_say"])]))
    S.append((2.2, b2.get("ask_sub", f"じゃあ {b2['key']} は?"), ask(b2, 4), [("ja", b2.get("ask", f"じゃあ、{b2['kana']}のほうは、どうでしょう?"))]))
    S.append((2.8, b2["sub"], right(b2, -3), [("ja", b2["say"])]))
    S.append((3.0, plain(b2["ja"]), ex(b2, 2), [("m", plain(b2["en"])), ("f", plain(b2["en"])), ("ja", b2["ja_say"])]))
    S.append((4.4, "", lambda bb, T, t: (
        comment_cta(bb, T, t, d=0.9),
        big(bb, T, t, "Q.", 520, size=200, color=A),
        card(bb, T, t, rows(q["en"], "en") + [([(q["choices"], False)], "q")], 880, d=0.2, angle=-1),
        tape(bb, T, t, q["ja"], 540, 1200, angle=-2, d=0.8, size=min(46, _tape_size(q["ja"], 46)))),
        [("ja", q.get("say_short", "どっちが正しい?答えと解説は、コメント欄にあるよ。"))]))
    return "blue", S


# ---------- 書き出し ----------
def sfx(path, times, dur):
    sr = 44100
    n = int(sr * dur)
    buf = [0.0] * n
    for t0 in times:
        s0 = int(t0 * sr)
        for i in range(int(sr * 0.12)):
            if s0 + i >= n: break
            tt = i / sr
            buf[s0 + i] += 0.28 * math.sin(2 * math.pi * (900 - 2500 * tt) * tt) * math.exp(-38 * tt)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 32767)) for v in buf))



VOICE = {"ja": "WQz3clzUdMqvBf0jswZQ", "m": "onwK4e9ZLuTAKqWW03F9", "f": "Xb7hH8MSUJpSbSDYk0k2"}  # Shizuka / Daniel(UK) / Alice(UK)
SPEED = {"ja": 1.12, "m": 0.92, "f": 0.92}
# 日本語は eleven_v3(漢字の読みが正確。2026-11-28 比較で v2 2/10 → v3 8/10)。英語は v2(安定・速さ調整できる)
MODEL = {"ja": "eleven_v3", "m": "eleven_multilingual_v2", "f": "eleven_multilingual_v2"}


# 読み間違える語 → 読ませたい形(ひらがな)。yomi_check.py で間違いが見つかったらここに足す
YOMI = {
    "今出なさい": "いまでなさい",
    # 「訳」は「わけ」と読まれる。聞き取り側も「訳」と書き戻すのでチェックをすり抜ける → 先にひらがなに
    "言い訳": "いいわけ",
    "和訳": "わやく",
    "訳": "やく",
    "空所": "くうしょ",
    "文目": "ぶんめ",  # 「3文目」が「さんもんめ」寄りに聞こえた(2026-11-28)  # 「からそ」と読まれた(2026-11-28)
}
MANIFEST = []  # (kind, 読ませた文, mp3) … yomi_check.py が使う


def speech(kind, text):
    if kind == "ja":
        for k, v in YOMI.items():
            text = text.replace(k, v)
    return text


def tts(kind, text):
    """ElevenLabs で読み上げ(キャッシュ)。失敗したら止める(声の差し替えはしない)"""
    text = speech(kind, text)
    import hashlib, json, os, urllib.request, urllib.error
    import tts as _t
    _t.load_env()
    cache = ROOT / "cache" / "grammar_tts"; cache.mkdir(parents=True, exist_ok=True)
    mp3 = cache / (hashlib.sha1(f"{VOICE[kind]}|{SPEED[kind]}|{text}{'|v3' if kind == 'ja' else ''}".encode()).hexdigest()[:14] + ".mp3")
    if not mp3.exists():
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE[kind]}?output_format=mp3_44100_128",
            data=json.dumps({"text": text, "model_id": MODEL[kind],
                             "voice_settings": {"stability": 0.5, "similarity_boost": 0.75} if MODEL[kind] == "eleven_v3"
                             else {"stability": 0.5, "similarity_boost": 0.75, "speed": SPEED[kind]}}).encode(),
            headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"})
        try:
            mp3.write_bytes(urllib.request.urlopen(req).read())
        except urllib.error.HTTPError as e:
            sys.exit(f"ElevenLabs エラー {e.code}: {e.read()[:200]} (クレジット切れの可能性。声の差し替えはしません)")
    # 前後の無音を削る(+日本語は少し速く)。テンポを詰めるため
    trim = mp3.with_name(mp3.stem + (f"_t{int(JA_TEMPO*100)}" if kind == "ja" else "_t") + ".wav")
    if not trim.exists():
        af = "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse"
        if kind == "ja":
            af += f",atempo={JA_TEMPO}"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp3), "-af", af, "-ar", "44100", str(trim)], check=True)
    MANIFEST.append({"kind": kind, "text": text, "mp3": str(mp3)})
    mp3 = trim
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp3)],
                             capture_output=True, text=True).stdout)
    return mp3, d


def render(no, lesson_no=None, out=None):
    if lesson_no:
        from grammar_lessons import LESSONS
        theme, S = lesson(next(L for L in LESSONS if L["no"] == lesson_no))
    else:
        theme, S = {1: V1, 2: V2, 3: V3}[no]()
    T = THEMES[theme]
    bg = background(theme).convert("RGBA")
    OUT.mkdir(parents=True, exist_ok=True)
    clips = []  # (開始秒, mp3)
    S2, acc = [], 0.0
    for s in S:
        dur, sub, fn = s[:3]
        parts = s[3] if len(s) > 3 else []
        t = acc + 0.08
        for kind, text in parts:
            mp3, d = tts(kind, text)
            if kind != "gap":  # gap = 無音の間(音声ファイルは混ぜない。雑音の原因になるため)
                clips.append((t, mp3, kind))
            t += d + 0.08
        dur = max(1.3, t - acc + 0.12) if parts else dur
        S2.append((dur, sub, fn)); acc += dur
    S = S2
    total = sum(s[0] for s in S)
    out = Path(out) if out else OUT / f"grammar_{no}.mp4"
    starts, acc = [], 0.0
    for s in S: starts.append(acc); acc += s[0]
    wav = OUT / f"sfx_{no}.wav"
    sfx(wav, [x + 0.05 for x in starts], total)
    if lesson_no:
        tr = track_for(lesson_no)
        bgm, ss, vol = ROOT / "assets" / "bgm" / tr["file"], max(0.0, tr["drop"] - HOOK), 0.14
    else:
        bgm, ss, vol = ROOT / "assets" / "bgm" / ("cycles.mp3" if no != 2 else "sailing.mp3"), 0.0, (0.10 if clips else 0.22)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-",
           "-i", str(wav), "-stream_loop", "-1", "-ss", f"{ss:.2f}", "-i", str(bgm)]
    fc = f"[2:a]volume={vol},afade=t=out:st={total-1}:d=1[m];"
    mix = "[1:a][m]"
    for i, (t0, mp3, kind) in enumerate(clips):
        cmd += ["-i", str(mp3)]
        fc += f"[{3+i}:a]loudnorm=I=-19:TP=-3:LRA=7,aresample=44100,adelay={int(t0*1000)}:all=1[v{i}];"; mix += f"[v{i}]"  # 声の大きさをそろえる
    fc += f"{mix}amix=inputs={2+len(clips)}:normalize=0,alimiter=limit=0.9[a]"
    cmd += ["-filter_complex", fc,
           "-map", "0:v", "-map", "[a]", "-t", f"{total}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
           "-c:a", "aac", "-b:a", "160k", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    total_frames = int(total * FPS)
    for fi in range(total_frames):
        tg = fi / FPS
        k = max(i for i, s0 in enumerate(starts) if s0 <= tg)
        dur, sub, fn = S[k]
        t = tg - starts[k]
        frame = bg.copy()
        if theme == "grid":
            timeline(frame, T, min(1, tg / total))
        fn(frame, T, t)
        subtitle(frame, T, sub)
        frame.convert("RGB").save(p.stdin, "JPEG", quality=92)
    p.stdin.close(); p.wait()
    wav.unlink()
    import json
    (out.with_suffix(".voice.json")).write_text(json.dumps(MANIFEST, ensure_ascii=False, indent=1))
    MANIFEST.clear()
    out.with_suffix(".starts.json").write_text(json.dumps(starts))
    print(out, f"{total:.1f}s")
    return out, starts


if __name__ == "__main__":
    if sys.argv[1:2] == ["lesson"]:  # python3 grammar_reel.py lesson 2 3 …
        for a in sys.argv[2:]:
            render(0, int(a), OUT / f"lesson_{int(a):03d}.mp4")
    else:
        for a in sys.argv[1:] or ["1", "2", "3"]:
            render(int(a))
