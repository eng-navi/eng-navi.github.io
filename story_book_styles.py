"""本の紹介ストーリーの別デザイン3種(参考:写真+手書きの書き込み)。

    python3 story_book_styles.py   # out/story/style_a.png / style_b.png / style_c.png

背景は質感を作って代用している。実物の本の写真を out/story/_photo_*.jpg に置けば、より本物らしくなる。
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
RED = (210, 72, 66)

EN = lambda s: ImageFont.truetype(str(F / "Kalam-Bold.ttf"), s)
ENR = lambda s: ImageFont.truetype(str(F / "Kalam-Regular.ttf"), s)
JP = lambda s: ImageFont.truetype(str(F / "KleeOne-SemiBold.ttf"), s)


def curve(p0, p1, p2, n=30):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]


def arrow(d, p0, p1, p2, color, w=4, head=20, loop=False):
    pts = curve(p0, p1, p2)
    if loop:  # 途中にくるっと輪っか
        mx, my = pts[12]
        ring = [(mx + 22 * math.cos(a / 10 * 2 * math.pi), my - 22 + 22 * math.sin(a / 10 * 2 * math.pi)) for a in range(11)]
        pts = pts[:12] + ring + pts[12:]
    d.line(pts, fill=color, width=w, joint="curve")
    (x0, y0), (x1, y1) = pts[-4], pts[-1]
    a = math.atan2(y1 - y0, x1 - x0)
    for s in (0.55, -0.55):
        d.line([(x1, y1), (x1 - head * math.cos(a + s), y1 - head * math.sin(a + s))], fill=color, width=w)


def star(d, cx, cy, r, color, w=3):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.line(pts + [pts[0]], fill=color, width=w, joint="curve")


def sparkle(d, cx, cy, color):
    for a in (-60, -30, 0, 30, 60):
        r = math.radians(a - 90)
        d.line([(cx + 18 * math.cos(r), cy + 18 * math.sin(r)), (cx + 38 * math.cos(r), cy + 38 * math.sin(r))], fill=color, width=4)


def lines(d, x, y, text, font, color, spacing=12, anchor="la"):
    d.multiline_text((x, y), text, font=font, fill=color, spacing=spacing, align="center" if anchor[0] == "m" else "left", anchor=anchor)


def texture(base, amount, blur, seed=1, streaks=None):
    random.seed(seed)
    img = Image.new("RGB", (W, H), base)
    px = img.load()
    for _ in range(amount):
        x, y = random.randrange(W), random.randrange(H)
        v = random.randint(-18, 18)
        r, g, b = px[x, y]
        px[x, y] = (r + v, g + v, b + v)
    d = ImageDraw.Draw(img)
    if streaks:  # 布のしわ・光
        for _ in range(streaks):
            x = random.randrange(-200, W)
            c = tuple(min(255, ch + random.randint(10, 30)) for ch in base)
            d.line([(x, 0), (x + random.randint(200, 600), H)], fill=c, width=random.randint(30, 90))
    return img.filter(ImageFilter.GaussianBlur(blur))


def place_cover(img, cx, cy, width, angle):
    cov = Image.open(COVER).convert("RGB")
    cov = cov.resize((width, int(cov.height * width / cov.width)))
    sh = Image.new("RGBA", (cov.width + 160, cov.height + 160), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([80, 100, cov.width + 80, cov.height + 100], fill=(0, 0, 0, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(30)).rotate(angle, expand=True, resample=Image.BICUBIC)
    cv = cov.convert("RGBA").rotate(angle, expand=True, resample=Image.BICUBIC)
    img.paste(sh, (cx - sh.width // 2 + 10, cy - sh.height // 2 + 14), sh)
    img.paste(cv, (cx - cv.width // 2, cy - cv.height // 2), cv)


def button(img, top, label="▼ 中身をのぞいてみる", lead=("＼ 今だけ Kindle版が半額 ／", "期間限定・残り11日(10/25時点)"), on_dark=False):
    d = ImageDraw.Draw(img)
    fg = (255, 255, 255) if on_dark else (40, 40, 40)
    d.text((W // 2, top - 70), lead[0], font=JP(46), fill=(255, 214, 92) if on_dark else RED, anchor="ms")
    d.text((W // 2, top - 22), lead[1], font=JP(28), fill=fg, anchor="ms")
    d.rectangle([0, top, W, top + 240], fill=RED)
    d.text((W // 2, top + 68), label, font=JP(42), fill=(255, 255, 255), anchor="ms")
    bx0, by0, bx1, by1 = W // 2 - 240, top + 105, W // 2 + 240, top + 195
    for x in range(bx0, bx1, 22):
        d.line([(x, by0), (min(x + 11, bx1), by0)], fill=(255, 255, 255), width=3)
        d.line([(x, by1), (min(x + 11, bx1), by1)], fill=(255, 255, 255), width=3)
    for y in range(by0, by1, 22):
        d.line([(bx0, y), (bx0, min(y + 11, by1))], fill=(255, 255, 255), width=3)
        d.line([(bx1, y), (bx1, min(y + 11, by1))], fill=(255, 255, 255), width=3)
    d.text((W // 2, (by0 + by1) // 2 + 12), "ここにリンクスタンプ", font=JP(32), fill=(255, 235, 233), anchor="ms")
    d.text((W - 60, 100), "PR", font=EN(38), fill=fg, anchor="ms")


def style_a():
    """布の上に置いた本+黒い手書き+黄色いマーカー(参考1)"""
    img = texture((176, 190, 205), 160000, 2.2, seed=4, streaks=14)
    # ゆるい光
    glow = Image.new("RGB", (W, H), (255, 255, 255))
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).ellipse([-300, -500, 900, 700], fill=90)
    img = Image.composite(glow, img, mask.filter(ImageFilter.GaussianBlur(160)))
    place_cover(img, 620, 900, 440, -6)
    d = ImageDraw.Draw(img)
    INK, Y = (25, 25, 30), (240, 196, 46)
    d.text((90, 290), "英文読解", font=JP(92), fill=INK)
    d.line(curve((90, 410), (300, 390), (520, 405)), fill=Y, width=12)
    sparkle(d, 120, 270, Y)
    d.text((560, 430), "♡", font=JP(48), fill=Y)
    lines(d, 650, 250, "読めない原因は\n単語じゃなくて\n「カタマリ」かも", JP(38), INK)
    d.line([(770, 390), (930, 380)], fill=Y, width=8)
    arrow(d, (860, 410), (920, 480), (840, 560), INK, loop=True)
    lines(d, 60, 720, "動画が42本。\nひとりで\n読んでる感じが\nしない", JP(36), INK)
    d.line([(60, 830), (200, 826)], fill=Y, width=8)
    arrow(d, (150, 920), (230, 990), (380, 960), INK)
    star(d, 110, 990, 22, Y)
    lines(d, 60, 1230, "長文で\n迷子になる人に\nいちばん効く", JP(36), INK)
    arrow(d, (230, 1225), (300, 1160), (390, 1150), INK)
    star(d, 300, 1380, 22, Y)
    d.text((690, 1300), "Kindle 50% OFF", font=EN(54), fill=INK)
    d.line([(690, 1380), (1010, 1372)], fill=Y, width=10)
    d.text((980, 1450), "♡", font=JP(48), fill=Y)
    button(img, 1620)
    return img


def style_b():
    """暗い机の上+黄色い手書き(参考2)"""
    img = texture((72, 72, 74), 220000, 1.6, seed=7)
    d = ImageDraw.Draw(img)
    # 机の手前の明るい面
    d.polygon([(0, 1250), (W, 1180), (W, H), (0, H)], fill=(96, 92, 88))
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    place_cover(img, 560, 840, 540, 8)
    d = ImageDraw.Draw(img)
    Y = (246, 232, 98)
    d.ellipse([560, 170, 930, 290], outline=Y, width=5)
    d.text((745, 248), "42 videos", font=EN(60), fill=Y, anchor="ms")
    sparkle(d, 520, 200, Y)
    star(d, 960, 330, 18, Y, w=3)
    lines(d, 70, 340, "単語は\nわかるのに\n読めない…\nの正体", JP(40), Y)
    arrow(d, (190, 560), (250, 640), (300, 640), Y)
    lines(d, 820, 470, "「カタマリ」\nで読む", JP(40), Y)
    arrow(d, (860, 580), (860, 640), (800, 660), Y)
    lines(d, 60, 1080, "読めた！って\n実感できる\nのが良い", JP(38), Y)
    arrow(d, (230, 1070), (260, 1010), (310, 990), Y)
    lines(d, 780, 1210, "大人の\n学び直しにも", JP(38), Y)
    arrow(d, (830, 1200), (830, 1150), (800, 1120), Y)
    d.text((W // 2, 1440), "Kindle 50% OFF!!", font=EN(66), fill=Y, anchor="ms")
    d.line(curve((300, 1462), (540, 1450), (780, 1466)), fill=Y, width=5)
    button(img, 1640, on_dark=True)
    return img


def style_c():
    """白い壁+大きな手書き文字+吹き出し(参考3)"""
    img = texture((236, 234, 230), 120000, 3.0, seed=9)
    shade = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shade).rectangle([0, 0, 260, H], fill=60)
    img = Image.composite(Image.new("RGB", (W, H), (200, 198, 194)), img, shade.filter(ImageFilter.GaussianBlur(180)))
    place_cover(img, 540, 960, 470, -3)
    d = ImageDraw.Draw(img)
    INK, BLUE, ORANGE = (20, 20, 20), (52, 74, 168), (196, 112, 40)
    # 縦に大きく
    for i, ch in enumerate("BOOK"):
        d.text((105, 620 + i * 150), ch, font=EN(150), fill=INK, anchor="mm")
    for i, ch in enumerate("PICK!"):
        d.text((975, 600 + i * 140), ch, font=EN(140), fill=INK, anchor="mm")
    # 吹き出し
    def bubble(x, y, w, h, tag, text, color, tail):
        d.ellipse([x - 70, y - 40, x + 50, y + 40], outline=color, width=4)
        d.text((x - 10, y + 12), tag, font=EN(34), fill=color, anchor="ms")
        lines(d, x + 70, y - 40, text, JP(34), color)
        d.line(curve(tail[0], tail[1], tail[2]), fill=color, width=4)
    bubble(190, 300, 300, 160, "Video", "授業動画が42本。\n本だけで終わらない", ORANGE, ((200, 345), (240, 470), (320, 560)))
    bubble(560, 220, 300, 160, "Read", "英文を「カタマリ」で\nつかむ練習ができる", BLUE, ((610, 330), (600, 430), (560, 520)))
    bubble(640, 1370, 300, 160, "For", "長文で迷子になる人\n大人の学び直しにも", BLUE, ((680, 1330), (690, 1310), (660, 1290)))
    d.text((130, 1460), "Kindle 50% OFF", font=EN(56), fill=RED)
    button(img, 1660)
    return img


if __name__ == "__main__":
    for name, fn in (("style_a", style_a), ("style_b", style_b), ("style_c", style_c)):
        fn().save(OUT / f"{name}.png")
        print(f"✓ out/story/{name}.png")
