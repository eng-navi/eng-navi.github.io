"""差がつく英文読解のプロフィール画像(3案)。黒×白×黄色のクールな雰囲気。円形でも読めるよう中央に大きく。"""
from PIL import Image, ImageDraw
import grammar_reel as g

S = 1080
BLACK, WHITE, YEL = (14, 14, 16), (245, 243, 236), (255, 214, 0)


def ctext(im, s, y, size, color):
    f = g.DELA(size); b = f.getbbox(s)
    ImageDraw.Draw(im).text(((S - (b[2] - b[0])) / 2 - b[0], y - (b[3] + b[1]) / 2), s, font=f, fill=color)


def icon1():  # 黒地に「読解」+黄色の蛍光ペン、上に「差がつく」
    im = Image.new("RGBA", (S, S), BLACK + (255,)); d = ImageDraw.Draw(im)
    d.rectangle([170, 600, 910, 700], fill=YEL)
    ctext(im, "読解", 560, 330, WHITE)
    ctext(im, "差がつく", 300, 110, YEL)
    return im


def icon2():  # 黄色地に黒の「差がつく」2段
    im = Image.new("RGBA", (S, S), YEL + (255,))
    ctext(im, "差が", 430, 250, BLACK)
    ctext(im, "つく", 690, 250, BLACK)
    d = ImageDraw.Draw(im); d.line([(250, 860), (830, 860)], fill=BLACK, width=18)
    return im


def icon3():  # 黒地に「英文/読解」+黄色テープ「差がつく」
    im = Image.new("RGBA", (S, S), BLACK + (255,))
    ctext(im, "英文", 500, 230, WHITE)
    ctext(im, "読解", 740, 230, WHITE)
    T = dict(g.THEMES["blue"]); T["tape"] = YEL; T["ink"] = BLACK
    g.tape(im, T, 1.0, "差がつく", 540, 270, angle=-5, size=90)
    return im


if __name__ == "__main__":
    ims = [icon1(), icon2(), icon3()]
    prev = Image.new("RGB", (3 * 380 + 40, 400), (250, 250, 250))
    for i, im in enumerate(ims, 1):
        im.convert("RGB").save(f"/Users/tsuji/Downloads/seidoku_icon_{i}.png")
        sm = im.resize((340, 340), Image.LANCZOS); m = Image.new("L", (340, 340), 0)
        ImageDraw.Draw(m).ellipse([0, 0, 339, 339], fill=255); prev.paste(sm, (40 + (i - 1) * 380, 30), m)
    prev.save(g.OUT / "seidoku_icons_preview.png")
