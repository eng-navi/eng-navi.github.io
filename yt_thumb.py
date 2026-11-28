"""YouTube 長い動画のサムネ(2026-11-28 ユーザーが選んだ「案A 黒×スモーク」)。

    python3 yt_thumb.py   # out/yt_compile の動画のサムネを THUMBS の内容で作り直す

形:暗い背景+スモーク、左上に赤い角、左に白の特大キーワード、黄色のサブ、金の数字+「問で総まとめ」、右に欧米人の写真(切り抜き)。
写真は assets/thumb_people/(StockSnap の CC0。切り抜きは Mac の Vision:`swift assets/thumb_people/seg.swift 写真.jpg 写真_mask.png`)。
人物は動画ごとに順番に変える(毎回同じにしない)。flip=写真の端で切れている人を左右反転して画面の端に合わせる。
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).parent
P = ROOT / "assets" / "thumb_people"
OUT = ROOT / "out" / "yt_compile"
W, H = 1280, 720
PEOPLE = [("person1", False), ("person2", False), ("person3", False), ("person4", False), ("person5", True), ("person6", True), ("person7", False)]


def jp(s, w=900):
    f = ImageFont.truetype(str(ROOT / "fonts" / "NotoSansJP.ttf"), s)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f


def dela(s): return ImageFont.truetype(str(ROOT / "fonts" / "DelaGothicOne-Regular.ttf"), s)
def anton(s): return ImageFont.truetype(str(ROOT / "fonts" / "Anton-Regular.ttf"), s)


def cut(name, h, flip=False):
    im = Image.open(P / f"{name}.jpg").convert("RGBA")
    m = Image.open(P / f"{name}_mask.png").convert("L").resize(im.size)
    im.putalpha(m.point(lambda v: 255 if v > 110 else 0).filter(ImageFilter.GaussianBlur(1.2)))
    if flip: im = ImageOps.mirror(im)
    im = im.crop(im.split()[3].getbbox())
    return im.resize((int(im.width * h / im.height), h), Image.LANCZOS)


def make(big, sub, n, unit, person, out, seed=3):
    rnd = random.Random(seed)
    a = Image.new("RGBA", (W, H), (24, 26, 30, 255))
    sm = Image.new("L", (W, H), 0); g = ImageDraw.Draw(sm)
    for _ in range(60):
        x, y = rnd.randint(0, W), rnd.randint(H // 3, H); r = rnd.randint(60, 200)
        g.ellipse([x - r, y - r, x + r, y + r], fill=rnd.randint(20, 60))
    a = Image.composite(Image.new("RGBA", (W, H), (95, 100, 112, 255)), a, sm.filter(ImageFilter.GaussianBlur(50)))
    d = ImageDraw.Draw(a)
    size = 330
    while d.textlength(big, font=dela(size)) > 720 and size > 120: size -= 10
    d.text((40, 0 + (330 - size) // 3), big, font=dela(size), fill=(255, 255, 255))
    name, flip = person
    p = cut(name, 640 if not flip else 660, flip)
    x = W - p.width - (0 if flip else 60)
    sh = Image.new("RGBA", p.size, (0, 0, 0, 0)); sh.putalpha(p.split()[3].point(lambda v: v * 100 // 255))
    a.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)), (x - 14, H - p.height + 10)); a.alpha_composite(p, (x, H - p.height))
    d = ImageDraw.Draw(a)
    d.polygon([(0, 0), (150, 0), (0, 150)], fill=(220, 40, 40))
    fs = 54
    while d.textlength(sub, font=jp(fs)) > 640 and fs > 34: fs -= 2
    d.text((48, 440), sub, font=jp(fs), fill=(255, 214, 0), stroke_width=6, stroke_fill=(24, 26, 30))
    d.text((48, 500), n, font=anton(150), fill=(232, 190, 90), stroke_width=6, stroke_fill=(24, 26, 30))
    d.text((48 + d.textlength(n, font=anton(150)) + 8, 562), unit, font=jp(64), fill=(255, 255, 255), stroke_width=6, stroke_fill=(24, 26, 30))
    a.convert("RGB").save(out, quality=92)
    return out


# 動画ごとの文字(大きいキーワード, 黄色のサブ, 数字, 単位)
THUMBS = {
    "theme_tense": ("時制", "現在完了・過去完了", "23", "問で総まとめ"),
    "theme_passive": ("受動態", "be given・have O done", "13", "問で総まとめ"),
    "theme_prep_conj": ("前置詞", "because と because of の違い", "10", "問で見分ける"),
    "theme_grammar_mix": ("英文法", "比較・仮定法・関係詞", "22", "問で総まとめ"),
    "eng_navi_1-150": ("英文法", "聞き流しクイズ|英検・TOEIC", "150", "問"),
    "eng_navi_101-200": ("英文法", "イディオムも聞き流し", "100", "問"),
    "listening_145-185": ("リスニング", "1回で聞き取れる?", "41", "問"),
}

if __name__ == "__main__":
    for i, (k, v) in enumerate(THUMBS.items()):
        print(make(*v, PEOPLE[i % len(PEOPLE)], OUT / f"{k}_thumb.jpg"))
