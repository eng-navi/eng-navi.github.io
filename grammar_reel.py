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
    S.append((3.0, "今出なさい、\nそうすればバスに間に合うよ", lambda b, T, t: (
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
    S.append((3.0, "今出なさい、\nさもないとバスに乗り遅れるよ", lambda b, T, t: (
        card(b, T, t, [([("Leave now, ", False), ("or", True), (" you'll miss", False)], "en"), ([("the bus.", False)], "en"),
                       ([("今出なさい、", False), ("さもないと", True), ("乗り遅れるよ", False)], "ja")], 980, angle=2))))
    S.append((4.4, "( ) に入るのは?\n答えはコメントで 1 か 2", lambda b, T, t: (
        big(b, T, t, "Q.", 520, size=200, color=THEMES["blue"]["accent"]),
        card(b, T, t, [([("Be quiet, (    ) the", False)], "en"), ([("baby will wake up.", False)], "en"),
                       ([("1  and      2  or", False)], "q")], 880, d=0.2, angle=-1),
        tape(b, T, t, "静かにして、さもないと赤ちゃんが起きる", 540, 1200, angle=-2, d=0.8, size=46))))
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


def render(no):
    theme, S = {1: V1, 2: V2, 3: V3}[no]()
    T = THEMES[theme]
    bg = background(theme).convert("RGBA")
    OUT.mkdir(parents=True, exist_ok=True)
    total = sum(s[0] for s in S)
    out = OUT / f"grammar_{no}.mp4"
    starts, acc = [], 0.0
    for s in S: starts.append(acc); acc += s[0]
    wav = OUT / f"sfx_{no}.wav"
    sfx(wav, [x + 0.05 for x in starts], total)
    bgm = ROOT / "assets" / "bgm" / ("cycles.mp3" if no != 2 else "sailing.mp3")
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-",
           "-i", str(wav), "-stream_loop", "-1", "-i", str(bgm),
           "-filter_complex", f"[2:a]volume=0.22,afade=t=out:st={total-1}:d=1[m];[1:a][m]amix=inputs=2:normalize=0,alimiter=limit=0.9[a]",
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
    print(out, f"{total:.1f}s")


if __name__ == "__main__":
    for a in sys.argv[1:] or ["1", "2", "3"]:
        render(int(a))
