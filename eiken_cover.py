"""英検リーディング部の表紙。A(ネイビー地)とB(クリーム地)を交互に出す。写真は青い2色刷りにして世界観をそろえる。"""
from PIL import Image, ImageDraw, ImageOps, ImageFilter
from pathlib import Path
import math
from eiken_icon import NAVY, BLUE, CREAM, SAND, pf, mc, go, sparkle, flower, pill
ROOT = Path(__file__).parent; W, H = 1080, 1350
PH = ROOT / "assets" / "toeic_photos"

def duo(path, w, h, dark=NAVY, light=CREAM):
    im = Image.open(path).convert("L"); r = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1)); x, y = (im.width - w) // 2, (im.height - h) // 2
    return ImageOps.colorize(ImageOps.autocontrast(im.crop((x, y, x + w, y + h)), cutoff=2), dark, light).convert("RGBA")

def header(d, fg, no, level):
    d.text((70, 66), "英検", font=mc(120), fill=fg)
    d.text((W - 70, 78), f"No.{no:02d}", font=pf(44), fill=fg, anchor="ra")
    d.text((W - 70, 132), f"{level} 長文", font=go(28, 700), fill=fg, anchor="ra")

def make(kind, photo, no, small, big, sub, level="準1級", out=None):
    if kind == "A":  # ネイビー地+右に写真(角丸)、筆記体の大見出しはクリーム
        im = Image.new("RGBA", (W, H), NAVY + (255,)); d = ImageDraw.Draw(im)
        p = duo(photo, 520, 640, (20, 36, 64), (170, 192, 220))
        m = Image.new("L", p.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, *p.size), 260, fill=255)
        im.paste(p, (W - 520 - 60, 230), m); d = ImageDraw.Draw(im)
        header(d, CREAM, no, level)
        flower(d, W - 120, 860, 60, SAND, 6); sparkle(d, 520, 330, 40, SAND); sparkle(d, 120, 1180, 30, SAND)
        fg, sm, pbg, pfg = CREAM, SAND, SAND, NAVY
    else:  # クリーム地+左上に写真(楕円)、見出しはネイビー
        im = Image.new("RGBA", (W, H), CREAM + (255,)); d = ImageDraw.Draw(im)
        p = duo(photo, 560, 600, NAVY, (226, 232, 240))
        m = Image.new("L", p.size, 0); ImageDraw.Draw(m).ellipse((0, 0, *p.size), fill=255)
        im.paste(p, (W - 560 - 50, 210), m); d = ImageDraw.Draw(im)
        header(d, NAVY, no, level)
        flower(d, 140, 380, 62, BLUE, 6); sparkle(d, W - 110, 880, 40, SAND); sparkle(d, 470, 260, 30, BLUE)
        fg, sm, pbg, pfg = NAVY, BLUE, NAVY, CREAM
    d.text((76, 905), small, font=go(46, 700), fill=sm, anchor="ls")
    f = pf(170, 800)
    while d.textlength(big, font=f) > W - 140: f = pf(f.size - 8, 800)
    d.text((70, 1080), big, font=f, fill=fg, anchor="ls")
    l = d.textbbox((0, 0), sub, font=go(46, 800)); pill(d, 76 + (l[2] - l[0]) / 2 + 36, 1160, sub, go(46, 800), pfg, pbg, 36, 14)
    d.text((76, H - 70), "目安 60秒", font=go(30, 700), fill=fg, anchor="ls")
    d.text((W - 70, H - 70), "swipe →", font=pf(46), fill=fg, anchor="rs")
    im.convert("RGB").save(out); return out

if __name__ == "__main__":
    O = ROOT / "out" / "eiken"; O.mkdir(parents=True, exist_ok=True)
    S = [("A", "open_book", 1, "空所に入る接続語は?", "In fact", "前後の関係で決まる"),
         ("B", "cafe_reading", 2, "ポジかネガか、", "Positive?", "段落の最後まで読む"),
         ("A", "reading_glasses", 3, "however のあとが", "However", "答えのありか"),
         ("B", "books", 4, "具体例をまとめると", "Summary", "選択肢は言い換え"),
         ("A", "notebook_desk", 5, "Therefore の後ろは", "Therefore", "前の内容のまとめ"),
         ("B", "writing", 6, "推測型は", "Read between", "行間を読む")]
    fs = [make(k, PH / f"{p}.jpg", n, a, b, c, out=O / f"cover_{n:02d}_{k}.png") for k, p, n, a, b, c in S]
    t = 360; g = Image.new("RGB", (t * 3 + 8, int(t * 1.25) * 2 + 4), "white")
    for i, f in enumerate(fs): g.paste(Image.open(f).resize((t, int(t * 1.25))), ((i % 3) * (t + 4), (i // 3) * (int(t * 1.25) + 4)))
    g.save(O / "grid_preview.png")
