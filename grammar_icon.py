"""やさしい英文法アカウントのプロフィール画像(3案)。円形に切り抜かれても読めるよう中央に大きく。
    python3 grammar_icon.py   → out/grammar/icon_1〜3.png と並べた確認用 icons_preview.png
"""
from PIL import Image, ImageDraw
import grammar_reel as g

S = 1080
OUT = g.OUT


def canvas(theme):
    bg = g.background(theme).crop((0, 400, 1080, 1480)).convert("RGBA")
    return bg


def center_text(im, s, y, size, color, font=None):
    f = font or g.DELA(size)
    w = g.text_w(f, s); b = f.getbbox(s)
    ImageDraw.Draw(im).text(((S - w) / 2 - b[0], y - (b[3] + b[1]) / 2), s, font=f, fill=color)


def icon1():  # 青:英文法 を特大+「やさしい」テープ
    T = g.THEMES["blue"]; im = canvas("blue")
    center_text(im, "英文法", 600, 300, T["big"])
    g.tape(im, T, 1.0, "やさしい", 540, 370, angle=-5, size=100)
    return im


def icon2():  # 青:文法 + 緑の手書き丸
    T = g.THEMES["blue"]; im = canvas("blue")
    center_text(im, "文法", 560, 380, T["big"])
    g.scribble(im, T, 1.0, 540, 560, 400, 260, width=22)
    g.tape(im, T, 1.0, "やさしい", 540, 830, angle=4, size=90)
    return im


def icon3():  # クリーム:やさしい/英文法 2段+青
    T = dict(g.THEMES["cream"]); blue = g.THEMES["blue"]["bg"]
    im = canvas("cream")
    ImageDraw.Draw(im).ellipse([140, 140, 940, 940], fill=blue)
    center_text(im, "英文法", 610, 230, g.THEMES["blue"]["big"])
    T2 = dict(g.THEMES["blue"]); T2["tape"] = (124, 252, 90)
    g.tape(im, T2, 1.0, "やさしい", 540, 400, angle=-4, size=86)
    return im


if __name__ == "__main__":
    ims = [icon1(), icon2(), icon3()]
    prev = Image.new("RGB", (3 * 380 + 40, 420), (250, 250, 250))
    for i, im in enumerate(ims, 1):
        im.convert("RGB").save(OUT / f"icon_{i}.png")
        small = im.resize((340, 340), Image.LANCZOS)
        m = Image.new("L", (340, 340), 0); ImageDraw.Draw(m).ellipse([0, 0, 339, 339], fill=255)
        prev.paste(small, (20 + (i - 1) * 380 + 20, 20), m)
        tiny = im.resize((110, 110), Image.LANCZOS)  # 遠目(小さく表示)の確認用
        m2 = Image.new("L", (110, 110), 0); ImageDraw.Draw(m2).ellipse([0, 0, 109, 109], fill=255)
    prev.save(OUT / "icons_preview.png")
    print("ok")
