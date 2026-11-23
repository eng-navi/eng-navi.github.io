"""TOEIC リーディング用カルーセルの表紙(クリーム地/黒地を交互に)。
配色: クリーム #EEE8D6 / 黒 #0B0B0B / 赤 #CF3E22。写真は StockSnap(CC0)。"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import math, random
from pathlib import Path
ROOT = Path(__file__).parent
F = ROOT / "fonts"
W, H = 1080, 1350
CREAM, BLACK, RED = (238, 232, 214), (11, 11, 11), (207, 62, 34)

def font(name, size, wght=None):
    f = ImageFont.truetype(str(F / name), size)
    if wght:
        try: f.set_variation_by_axes([wght])
        except Exception: pass
    return f
def anton(s): return font("Anton-Regular.ttf", s)
def jp(s, w=900): return font("NotoSansJP.ttf", s, w)

def text_img(t, f, fill, squeeze=0.86):
    l, tp, r, b = f.getbbox(t)
    im = Image.new("RGBA", (r - l + 4, b - tp + 4), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((2 - l, 2 - tp), t, font=f, fill=fill)
    return im.resize((int(im.width * squeeze), im.height), Image.LANCZOS)

def runs_img(runs, size, squeeze=0.86):
    """[(文字, 色), ...] を横に並べた1行"""
    parts = [text_img(t, jp(size), c, squeeze) for t, c in runs]
    h = max(p.height for p in parts); w = sum(p.width for p in parts) + 6 * (len(parts) - 1)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); x = 0
    for p in parts: im.alpha_composite(p, (x, h - p.height)); x += p.width + 6
    return im

def zabuton(im, bg, px=26, py=20):
    out = Image.new("RGBA", (im.width + 2 * px, im.height + 2 * py), bg + (255,))
    out.alpha_composite(im, (px, py)); return out

def paste(base, im, xy, angle=0):
    if angle: im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    base.alpha_composite(im, (int(xy[0]), int(xy[1])))

def photo(path, w, h, dark=1.0):
    im = Image.open(path).convert("RGB"); r = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    im = im.crop((x, y, x + w, y + h))
    return ImageEnhance.Brightness(im).enhance(dark).convert("RGBA")

def hand_ellipse(d, box, col, w=6, seed=1):
    rnd = random.Random(seed); x0, y0, x1, y1 = box; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = (x1 - x0) / 2, (y1 - y0) / 2
    pts = []
    for i in range(0, 400, 6):
        a = math.radians(i - 20); k = 1 + 0.04 * math.sin(i / 37) + (0.05 if i > 360 else 0)
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a) - (i > 360) * 8))
    d.line(pts, fill=col, width=w, joint="curve")

def asterisk(d, cx, cy, r, col, w=7):
    for k in range(4):
        a = math.radians(k * 45 + 10)
        d.line((cx - r * math.cos(a), cy - r * math.sin(a), cx + r * math.cos(a), cy + r * math.sin(a)), fill=col, width=w)

def stopwatch(d, cx, cy, r, line, fillc):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=line, width=max(4, r // 9))
    d.rounded_rectangle((cx - r * .22, cy - r * 1.38, cx + r * .22, cy - r * 1.14), 4, fill=line)
    d.line((cx, cy - r * 1.14, cx, cy - r), fill=line, width=max(4, r // 8))
    d.pieslice((cx - r * .72, cy - r * .72, cx + r * .72, cy + r * .72), -90, 90, fill=fillc)

def arrow(d, x0, y, x1, col, w=5):
    d.line((x0, y, x1, y), fill=col, width=w)
    d.line((x1, y, x1 - 22, y - 16), fill=col, width=w); d.line((x1, y, x1 - 22, y + 16), fill=col, width=w)

def header(d, fg, no):
    d.text((64, 56), "eng_navi TOEIC", font=anton(30), fill=fg)
    for i, t in enumerate(["PART 7", "READING", f"No.{no:02d}"]):
        d.text((W - 64, 52 + i * 30), t, font=jp(24, 800), fill=fg, anchor="ra")

def make(kind, img, no, l1, l2, l3, sec=30, out=None):
    """l1: 小さい行 / l2: 大きい行 [(文字, 'a'|'n')] a=アクセント / l3: 中くらいの行"""
    if kind == "cream":
        base = Image.new("RGBA", (W, H), CREAM + (255,)); d = ImageDraw.Draw(base)
        # 赤いブラシ+写真(少し傾けたコラージュ)
        blob = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(blob)
        bd.ellipse((520, 250, 1040, 700), fill=RED + (255,)); bd.ellipse((640, 520, 1000, 880), fill=RED + (255,))
        base.alpha_composite(blob.filter(ImageFilter.GaussianBlur(3)))
        paste(base, photo(img, 430, 560), (590, 300), -4)
        header(d, BLACK, no)
        paste(base, text_img("TOEIC", anton(250), BLACK, 1.0), (56, 110))
        paste(base, zabuton(text_img("PART 7", anton(52), CREAM, 1.0), RED, 18, 10), (70, 420), 5)
        # 見出し(黒の座布団にクリーム文字/アクセントは赤)
        y = 690
        for im, ang in [(zabuton(runs_img([(l1, CREAM)], 76), BLACK), 3),
                        (zabuton(runs_img([(t, RED if a == "a" else CREAM) for t, a in l2], 150), BLACK), 3),
                        (zabuton(runs_img([(l3, CREAM)], 100), BLACK), 3)]:
            paste(base, im, (56, y), ang); y += im.height - 4
        d = ImageDraw.Draw(base)
        asterisk(d, 980, 1010, 34, RED)
        stopwatch(d, 104, 1250, 34, BLACK, RED)
        d.text((158, 1250), f"目安 {sec}秒", font=jp(34, 800), fill=BLACK, anchor="lm")
        d.text((W - 130, 1250), "SWIPE", font=anton(44), fill=BLACK, anchor="rm"); arrow(d, W - 120, 1252, W - 64, RED)
    else:
        base = photo(img, W, H, 0.62); g = Image.new("RGBA", (W, H)); gd = ImageDraw.Draw(g)
        for yy in range(H): gd.line((0, yy, W, yy), fill=(0, 0, 0, int(200 * max(0, (yy - 450) / 900))))
        base.alpha_composite(g); d = ImageDraw.Draw(base)
        header(d, CREAM, no)
        paste(base, text_img("TOEIC", anton(250), CREAM, 1.0), (56, 110))
        paste(base, zabuton(text_img("PART 7", anton(52), CREAM, 1.0), RED, 18, 10), (70, 420), 5)
        y = 700
        paste(base, runs_img([(l1, CREAM)], 80), (64, y)); y += 120
        big = runs_img([(t, CREAM) for t, a in l2], 170)
        # アクセント語は赤い座布団
        x = 64
        for t, a in l2:
            im = text_img(t, jp(170), CREAM)
            if a == "a": im = zabuton(im, RED, 14, 6); paste(base, im, (x, y - 6), 3)
            else: paste(base, im, (x, y))
            x += im.width + 8
        y += 230
        paste(base, runs_img([(l3, CREAM)], 108), (64, y))
        d = ImageDraw.Draw(base)
        hand_ellipse(d, (40, y - 30, 64 + runs_img([(l3, CREAM)], 108).width + 30, y + 150), RED, 6)
        stopwatch(d, 104, 1250, 34, CREAM, RED)
        d.text((158, 1250), f"目安 {sec}秒", font=jp(34, 800), fill=CREAM, anchor="lm")
        d.text((W - 130, 1250), "SWIPE", font=anton(44), fill=CREAM, anchor="rm"); arrow(d, W - 120, 1252, W - 64, RED)
    base.convert("RGB").save(out); return out

if __name__ == "__main__":
    import sys
    P = Path(sys.argv[1]); O = ROOT / "out" / "toeic_reading"
    S = [("cream", "p11", 3, "この1問、", [("30秒", "a"), ("で", "n")], "解けたら上級者", 30),
         ("black", "p10", 4, "Part 7、", [("時間", "a"), ("が", "n")], "足りない人へ", 40),
         ("cream", "p02", 5, "「目的」を聞かれたら", [("ここ", "a"), ("だけ", "n")], "読めばいい", 30),
         ("black", "p34", 6, "NOT問題を", [("最速", "a"), ("で", "n")], "解くコツ", 45),
         ("cream", "p22", 7, "チャット問題の", [("意図", "a"), ("を", "n")], "30秒で読む", 30),
         ("black", "p26", 8, "その選択肢、", [("ワナ", "a"), ("です", "n")], "言い換えを見抜け", 40)]
    files = [make(k, P / f"{p}.jpg", n, a, b, c, s, O / f"cover_{n:02d}_{k}.png") for k, p, n, a, b, c, s in S]
    tw = 360; grid = Image.new("RGB", (tw * 3 + 8, int(tw * 1.25) * 2 + 4), "white")
    for i, fp in enumerate(files):
        im = Image.open(fp).resize((tw, int(tw * 1.25)))
        grid.paste(im, ((i % 3) * (tw + 4), (i // 3) * (int(tw * 1.25) + 4)))
    grid.save(O / "grid_preview.png")
