"""英検リーディング部の表紙。濃い地(ネイビー/青)と明るい地(クリーム)を交互にして市松模様に。
レイアウトは6種を順番に使う。どの表紙にも「解けたら〇級」の一言と、時計+「Q. 問題へ」を入れてクイズだと分かるように。"""
from PIL import Image, ImageDraw, ImageOps, ImageFilter
from pathlib import Path
import math, random
from eiken_icon import NAVY, CREAM, SAND, pf, mc, go
ROOT = Path(__file__).parent; W, H = 1080, 1350; PH = ROOT / "assets" / "toeic_photos"
BLUE, SKY, INK = (79, 117, 163), (168, 193, 222), (20, 34, 62)

def duo(name, w, h, dark=INK, light=(226, 233, 242)):
    im = Image.open(PH / f"{name}.jpg").convert("L"); r = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1)); x, y = (im.width - w) // 2, (im.height - h) // 2
    return ImageOps.colorize(ImageOps.autocontrast(im.crop((x, y, x + w, y + h)), cutoff=2), dark, light).convert("RGBA")
def shape(p, kind, r=60):
    m = Image.new("L", p.size, 0); d = ImageDraw.Draw(m)
    if kind == "oval": d.ellipse((0, 0, *p.size), fill=255)
    elif kind == "arch": d.rounded_rectangle((0, 0, p.width, p.height + p.width // 2), p.width // 2, fill=255)
    else: d.rounded_rectangle((0, 0, *p.size), r, fill=255)
    p.putalpha(m); return p
def put(base, im, xy, ang=0):
    if ang: im = im.rotate(ang, resample=Image.BICUBIC, expand=True)
    base.alpha_composite(im, (int(xy[0]), int(xy[1])))
def text_im(t, f, fill, pad=(0, 0), bg=None):
    l, tp, r, b = f.getbbox(t); im = Image.new("RGBA", (r - l + pad[0] * 2, b - tp + pad[1] * 2), (bg + (255,)) if bg else (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad[0] - l, pad[1] - tp), t, font=f, fill=fill); return im
def zab(t, size, fg, bg, ang=0): return text_im(t, go(size, 800), fg, (22, 12), bg), ang
# あしらい
def star(d, cx, cy, r, col, w=6, fill=False, seed=0):
    rnd = random.Random(seed); pts = []
    for i in range(8):
        a = math.radians(i * 45 - 90 + rnd.uniform(-6, 6)); rr = (r if i % 2 == 0 else r * 0.32) * rnd.uniform(.9, 1.1)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=col) if fill else d.line(pts + [pts[0]], fill=col, width=w, joint="curve")
def flower(d, cx, cy, r, col, w=7):
    for i in range(6):
        a = math.radians(i * 60); px, py = cx + r * .55 * math.cos(a), cy + r * .55 * math.sin(a)
        d.ellipse((px - r * .45, py - r * .3, px + r * .45, py + r * .3), outline=col, width=w)
    d.ellipse((cx - r * .14, cy - r * .14, cx + r * .14, cy + r * .14), fill=col)
def branch(d, x, y, L, ang, col):
    a = math.radians(ang); x2, y2 = x + L * math.cos(a), y + L * math.sin(a); d.line((x, y, x2, y2), fill=col, width=5)
    for k in range(1, 6):
        t = k / 6; px, py = x + (x2 - x) * t, y + (y2 - y) * t
        for s in (1, -1):
            b = a + s * math.radians(50); lx, ly = px + 46 * math.cos(b), py + 46 * math.sin(b)
            d.line((px, py, lx, ly), fill=col, width=14)
def tape(base, x, y, w, ang, col=(232, 220, 196, 210)):
    t = Image.new("RGBA", (w, 46), col); put(base, t, (x, y), ang)
def sparkle(d, cx, cy, r, col): star(d, cx, cy, r, col, fill=True)
def watch(d, cx, cy, r, col, acc):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col, width=5); d.rectangle((cx - 7, cy - r - 14, cx + 7, cy - r), fill=col)
    d.pieslice((cx - r + 10, cy - r + 10, cx + r - 10, cy + r - 10), -90, 0, fill=acc)
# 共通の部品
def header(d, fg, no, level):
    d.text((66, 58), "英検", font=mc(112), fill=fg)
    d.text((W - 66, 66), f"No.{no:02d}", font=pf(42), fill=fg, anchor="ra")
    d.text((W - 66, 120), f"{level}・長文の空所", font=go(26, 700), fill=fg, anchor="ra")
def footer(base, fg, pill_bg, pill_fg, acc, sec=60):
    d = ImageDraw.Draw(base); watch(d, 104, H - 92, 30, fg, acc)
    d.text((152, H - 92), f"目安 {sec}秒", font=go(36, 800), fill=fg, anchor="lm")
    put(base, text_im("Q. 問題はこちら →", go(36, 800), pill_fg, (28, 16), pill_bg), (W - 66 - 400, H - 128))
def big(base, word, xy, size, fill, maxw=W - 120):
    f = pf(size, 800)
    while f.getlength(word) > maxw: f = pf(f.size - 6, 800)
    ImageDraw.Draw(base).text(xy, word, font=f, fill=fill, anchor="ls"); return f.size

def make(v, photo, no, teaser, word, line, level="準1級", out=None):
    if v == 1:  # ネイビー地。左に縦長アーチの写真、見出しは写真に重ねる
        im = Image.new("RGBA", (W, H), NAVY + (255,)); d = ImageDraw.Draw(im)
        put(im, shape(duo(photo, 470, 700), "arch"), (66, 250)); d = ImageDraw.Draw(im)
        flower(d, 900, 330, 80, SAND); star(d, 610, 270, 46, SKY, seed=1); branch(d, 660, 640, 300, -35, BLUE)
        put(im, zab(teaser, 40, NAVY, SAND)[0].rotate(3, expand=True, resample=Image.BICUBIC), (300, 790))
        big(im, word, (300, 1050), 190, CREAM, W - 360); d = ImageDraw.Draw(im)
        d.text((306, 1110), line, font=go(40, 700), fill=SKY, anchor="ls"); header(d, CREAM, no, level)
        footer(im, CREAM, SAND, NAVY, SAND)
    elif v == 2:  # クリーム地。中央に丸い写真、見出しを写真の前に大きく
        im = Image.new("RGBA", (W, H), CREAM + (255,)); d = ImageDraw.Draw(im)
        star(d, 210, 420, 120, SAND, 10, seed=2); flower(d, 900, 1000, 70, BLUE)
        put(im, shape(duo(photo, 560, 560), "oval"), (260, 250)); d = ImageDraw.Draw(im)
        put(im, text_im(teaser, go(40, 800), CREAM, (22, 12), NAVY).rotate(-3, expand=True, resample=Image.BICUBIC), (130, 230))
        big(im, word, (90, 930), 210, NAVY); d = ImageDraw.Draw(im)
        put(im, text_im(line, go(42, 800), NAVY, (20, 10), SKY), (96, 970)); header(d, NAVY, no, level)
        footer(im, NAVY, NAVY, CREAM, BLUE)
    elif v == 3:  # 青地。写真を全面に敷いて、ネイビーの座布団で見出し
        im = duo(photo, W, H, (30, 50, 90), SKY); d = ImageDraw.Draw(im)
        ov = Image.new("RGBA", (W, H), BLUE + (110,)); im.alpha_composite(ov); d = ImageDraw.Draw(im)
        put(im, text_im(teaser, go(42, 800), NAVY, (22, 12), SAND).rotate(2, expand=True, resample=Image.BICUBIC), (66, 600))
        put(im, text_im(word, pf(160, 800), CREAM, (30, 18), NAVY).rotate(-2, expand=True, resample=Image.BICUBIC), (60, 700))
        d = ImageDraw.Draw(im); d.text((76, 1010), line, font=go(44, 800), fill=CREAM, anchor="ls")
        star(d, 940, 560, 50, CREAM, seed=3); sparkle(d, 880, 980, 30, SAND); header(d, CREAM, no, level)
        footer(im, CREAM, NAVY, CREAM, SAND)
    elif v == 4:  # クリーム地。写真は右上に斜めに貼る(テープ)、見出しは左下に積む
        im = Image.new("RGBA", (W, H), CREAM + (255,)); d = ImageDraw.Draw(im)
        branch(d, 80, 600, 320, -20, SKY)
        put(im, shape(duo(photo, 470, 560), "rect", 8), (520, 210), -5); tape(im, 640, 190, 200, 4); d = ImageDraw.Draw(im)
        put(im, text_im(teaser, go(40, 800), CREAM, (22, 12), BLUE), (66, 760))
        big(im, word, (60, 990), 200, NAVY); d = ImageDraw.Draw(im)
        d.text((70, 1060), line, font=go(42, 700), fill=BLUE, anchor="ls"); star(d, 960, 900, 56, SAND, 8, seed=4)
        header(d, NAVY, no, level); footer(im, NAVY, NAVY, CREAM, SAND)
    elif v == 5:  # ネイビー地。見出しが上、写真2枚をポラロイド風に下へ
        im = Image.new("RGBA", (W, H), NAVY + (255,)); d = ImageDraw.Draw(im)
        put(im, text_im(teaser, go(40, 800), NAVY, (22, 12), SKY).rotate(-2, expand=True, resample=Image.BICUBIC), (66, 220))
        big(im, word, (60, 470), 200, CREAM); d = ImageDraw.Draw(im)
        d.text((70, 540), line, font=go(42, 700), fill=SAND, anchor="ls")
        for (x, y, a, nm) in ((120, 640, -6, photo), (560, 680, 5, "desk_top")):
            card = Image.new("RGBA", (400, 470), CREAM + (255,)); card.alpha_composite(duo(nm, 360, 360), (20, 20)); put(im, card, (x, y), a)
        tape(im, 230, 620, 180, -8); tape(im, 680, 660, 180, 6); d = ImageDraw.Draw(im)
        sparkle(d, 960, 300, 36, SAND); star(d, 980, 600, 44, SKY, seed=5); header(d, CREAM, no, level)
        footer(im, CREAM, SAND, NAVY, SAND)
    else:  # クリーム地。下半分に水色の帯+写真、帯の上にネイビーの座布団
        im = Image.new("RGBA", (W, H), CREAM + (255,)); d = ImageDraw.Draw(im)
        d.rectangle((0, 760, W, H), fill=SKY)
        put(im, shape(duo(photo, 420, 520), "arch"), (600, 300)); d = ImageDraw.Draw(im)
        flower(d, 160, 380, 70, SAND); star(d, 470, 300, 40, BLUE, seed=6)
        big(im, word, (60, 700), 180, NAVY, 560 if len(word) > 9 else W - 120); d = ImageDraw.Draw(im)
        put(im, text_im(teaser, go(42, 800), CREAM, (22, 12), NAVY).rotate(2, expand=True, resample=Image.BICUBIC), (66, 820))
        d.text((76, 1010), line, font=go(44, 800), fill=NAVY, anchor="ls"); header(d, NAVY, no, level)
        footer(im, NAVY, NAVY, CREAM, BLUE)
    im.convert("RGB").save(out); return out

if __name__ == "__main__":
    O = ROOT / "out" / "eiken"; O.mkdir(parents=True, exist_ok=True)
    S = [(1, "man_writing", 1, "解けたら準1級レベル", "In fact?", "空所に入る“つなぎ”は?"),
         (2, "cafe_reading", 2, "2級合格者も迷う", "Positive?", "ポジかネガか、見抜ける?"),
         (3, "reading_glasses", 3, "解けたら準1級レベル", "However,", "このあとに答えがある"),
         (4, "books", 4, "英検2級から挑戦", "Summary", "具体例をひとことで?"),
         (5, "notebook_desk", 5, "解けたら準1級レベル", "Therefore", "空所は“まとめ”の合図"),
         (6, "writing", 6, "上級者でも迷う", "Between", "行間、読めますか?")]
    fs = [make(v, p, n, a, b, c, out=O / f"cover_{n:02d}.png") for v, p, n, a, b, c in S]
    t = 360; g = Image.new("RGB", (t * 3 + 8, int(t * 1.25) * 2 + 4), "white")
    for i, f in enumerate(fs): g.paste(Image.open(f).resize((t, int(t * 1.25))), ((i % 3) * (t + 4), (i // 3) * (int(t * 1.25) + 4)))
    g.save(O / "grid_preview.png")
