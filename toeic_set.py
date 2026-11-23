"""TOEIC リーディングのカルーセル1セット(表紙→問題→答え・解説→和訳→単語→案内)。
英文はすべてオリジナル。上半分=英文(固定)、下半分=解説 の形。"""
from PIL import Image, ImageDraw
from pathlib import Path
import sys
from toeic_problems import PROBLEMS, EXPLAIN_TITLES
from toeic_cover import W, H, CREAM, BLACK, RED, font, anton, jp, text_img, zabuton, paste, stopwatch, arrow, asterisk, make

ROOT = Path(__file__).parent
PAPER = (250, 247, 238); MARK = (240, 178, 160); GREY = (110, 106, 98)
def serif(s, w=500):
    f = font("SourceSerif4.ttf", s)
    f.set_variation_by_axes([w, 18])  # 太め・小さい字向けの字形でスマホでも読みやすく
    return f
BOTTOM = H - 104
TOP = 50  # 下の案内より上に収める

def fit(P, top, room, hi, lo=30, hl=()):
    """英文カードが room(px) に収まる一番大きい字の大きさ"""
    for size in range(hi, lo - 1, -1):
        if passage(Image.new("RGBA", (W, H)), 64, top, W - 128, P, size, hl) <= room: return size
    return lo
NUM = "❶❷❸❹❺"

def wrap_jp(d, text, f, width):
    """日本語は1文字ずつ、英単語(と記号の続き)は途中で切らずに折り返す"""
    import re
    lines = []
    for para in text.split("\n"):
        toks = re.findall(r"[A-Za-z0-9'’.,:;!?()\-/~〜]+ ?|.", para)
        cur = ""
        for t in toks:
            if d.textlength(cur + t.rstrip(), font=f) > width and cur and t not in "、。」）)":
                lines.append(cur.rstrip()); cur = t.lstrip()
            else: cur += t
        lines.append(cur.rstrip())
    return lines

def passage(base, x, y, w, P, size=29, hl=(), card=True, label="", timer=None):
    """P = {"kind":"E-MAIL", "head":[...], "body":[[(text, tag), ...], ...]} を描く。高さを返す"""
    d = ImageDraw.Draw(base); fs = serif(size); fh = jp(size - 6, 600); lh = int(size * 1.42)
    pad = 30; cx = x + pad; cy = y + pad + 52
    if card:
        d.rectangle((x, y, x + w, y + 10), fill=BLACK)
    for t in P["head"]:
        d.text((cx, cy), t, font=fh, fill=GREY); cy += int(lh * 0.95)
    cy += 10
    for para in P["body"]:
        px = cx
        for text, tag in para:
            words = text.split(" ")
            if tag: words = [NUM[tag - 1]] + words
            for i, wd in enumerate(words):
                if not wd: continue
                isnum = wd in NUM
                f = jp(size - 4, 800) if isnum else (jp(size - 2, 600) if any(c in "①②③" for c in wd) else fs)
                ww = d.textlength(wd, font=f); sp = d.textlength(" ", font=fs)
                if px + ww > x + w - pad: px = cx; cy += lh
                if tag in hl: d.rectangle((px - 2, cy + 4, px + ww + (sp if i < len(words) - 1 else 0) + 2, cy + lh - 2), fill=MARK)
                d.text((px, cy + (3 if isnum else 0)), wd, font=f, fill=RED if isnum else BLACK)
                px += ww + sp
        cy += lh + 12
    h = cy - y + pad - 12
    if card:  # 紙のカード(後ろに敷く)
        bg = Image.new("RGBA", (w, h), PAPER + (255,)); ImageDraw.Draw(bg).rectangle((0, 0, w - 1, h - 1), outline=BLACK, width=3)
        bd = ImageDraw.Draw(bg); bd.rectangle((0, 0, w, 60), fill=BLACK)
        bd.text((24, 30), P["kind"], font=anton(32), fill=CREAM, anchor="lm")
        if timer:
            stopwatch(bd, w - 44, 33, 15, CREAM, RED); bd.text((w - 74, 30), f"目安{timer}秒", font=jp(30, 800), fill=CREAM, anchor="rm")
        elif label:
            bd.text((w - 24, 30), label, font=jp(28, 800), fill=CREAM, anchor="rm")
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0)); layer.alpha_composite(bg, (x, y))
        tmp = base.copy(); base.paste(layer, (0, 0), layer)
        return passage(base, x, y, w, P, size, hl, card=False)
    return h

def frame(no, label=None, page=0, total=0):
    im = Image.new("RGBA", (W, H), CREAM + (255,))
    if label: paste(im, zabuton(text_img(label, jp(40), CREAM), BLACK, 20, 12), (64, 64), 2)
    return im

def bottom_note(d, left, right="SWIPE"):
    d.text((64, H - 58), left, font=jp(30, 700), fill=BLACK, anchor="lm")
    if right:
        d.text((W - 130, H - 58), right, font=anton(40), fill=BLACK, anchor="rm"); arrow(d, W - 120, H - 56, W - 64, RED)

def build(Q, out):
    out.mkdir(parents=True, exist_ok=True); no = Q["no"]; total = 5 + len(Q["explain"]); files = []
    kind = "cream" if no % 2 else "black"  # 交互にしてグリッドを市松模様に
    files.append(make(kind, ROOT / "assets" / "toeic_photos" / f'{Q["photo"]}.jpg', no, *Q["cover"], Q["sec"], out / "01_cover.png"))
    PX, PW = 64, W - 128
    d0 = ImageDraw.Draw(Image.new("RGBA", (W, H)))
    QF, CF, JF, EF = serif(46, 600), serif(44), jp(33, 400), jp(37, 500)
    qlines = wrap_jp(d0, Q["q"], QF, PW)
    jl = wrap_jp(d0, Q["ja"], JF, PW)
    qj = [ln for t in [f"設問:{Q['q_ja']}"] + [f"({'AB'[i]}) {cj}" for i, (c, cj) in enumerate(Q["choices"])] for ln in wrap_jp(d0, t, jp(32, 600), PW)]
    exps = Q["explain"]; els = [wrap_jp(d0, e["text"], EF, PW) for e in exps]
    rooms = [BOTTOM - TOP - 40 - len(qlines) * 58 - 26 - 2 * 92,
             BOTTOM - TOP - 32 - len(jl) * 50 - 34 - len(qj) * 48]
    rooms += [BOTTOM - TOP - 36 - (116 if k == 0 else 0) - len(el) * 60 for k, el in enumerate(els)]
    size = min(fit(Q["passage"], TOP, r, 52, 32) for i, r in enumerate(rooms) if i != 1)  # 英文はどのページでも同じ大きさ(和訳ページは日本語側を調整)
    hP = passage(Image.new("RGBA", (W, H)), PX, TOP, PW, Q["passage"], size)
    def ja_fit():
        for withq, lo in ((True, 29), (False, 27)):  # 和訳は小さくしすぎない。入らなければ設問の訳は省く
            for js in range(33, lo - 1, -1):
                JF = jp(js, 400); jl = wrap_jp(d0, Q["ja"], JF, PW)
                qj = [ln for t in [f"設問:{Q['q_ja']}"] + [f"({'AB'[i]}) {cj}" for i, (c, cj) in enumerate(Q["choices"])] for ln in wrap_jp(d0, t, jp(js - 1, 600), PW)] if withq else []
                if TOP + hP + 32 + len(jl) * int(js * 1.5) + (34 + len(qj) * int(js * 1.45) if qj else 0) <= BOTTOM: return js, JF, jl, qj
        return js, JF, jl, []
    js, JF, jl, qj = ja_fit()
    # 2 問題:英文+設問+2択
    im = frame(no); h = passage(im, PX, TOP, PW, Q["passage"], size, timer=Q["sec"]); d = ImageDraw.Draw(im)
    y = TOP + h + 40
    for ln in qlines: d.text((PX, y), ln, font=QF, fill=BLACK); y += 58
    y += 26
    for i, (c, cj) in enumerate(Q["choices"]):
        paste(im, zabuton(text_img("AB"[i], anton(44), CREAM, 1.0), BLACK, 18, 6), (PX, y)); d = ImageDraw.Draw(im)
        d.text((PX + 92, y + 2), c, font=CF, fill=BLACK); y += 92
    bottom_note(d, "AかBか、コメントで答えてね")
    im.convert("RGB").save(out / "02_question.png")
    # 3 全文の和訳(答えの前に。もう一度考えてもらう)
    im = frame(no); h = passage(im, PX, TOP, PW, Q["passage"], size, label="全文の和訳"); d = ImageDraw.Draw(im); y = TOP + h + 32
    for ln in jl: d.text((PX, y), ln, font=JF, fill=BLACK); y += int(js * 1.5)
    if qj: y += 14; d.line((PX, y, W - PX, y), fill=(210, 203, 185), width=2); y += 20
    for ln in qj: d.text((PX, y), ln, font=jp(js - 1, 600), fill=BLACK); y += int(js * 1.45)
    bottom_note(d, "もう一度考えてみて。答えは次へ"); im.convert("RGB").save(out / "03_ja.png")
    # 4〜 解説(上=英文固定、下=解説)
    for k, e in enumerate(exps):
        im = frame(no); h = passage(im, PX, TOP, PW, Q["passage"], size, hl=e["hl"], label=f"{EXPLAIN_TITLES[k]}  {k + 1}/{len(exps)}"); d = ImageDraw.Draw(im)
        y = TOP + h + 36
        if k == 0:
            paste(im, zabuton(text_img(f"答え  {Q['answer']}", jp(58), CREAM), RED, 22, 12), (PX, y), 2); d = ImageDraw.Draw(im); y += 116
        for ln in els[k]: d.text((PX, y), ln, font=EF, fill=BLACK); y += 60
        bottom_note(d, f"解説 {k + 1}/{len(exps)}")
        im.convert("RGB").save(out / f"0{4 + k}_explain{k + 1}.png")
    p = 4 + len(exps)
    # 単語
    im = frame(no, "この問題の単語"); d = ImageDraw.Draw(im); y = 200
    for en, ja in Q["words"]:
        d.text((PX, y), en, font=serif(58, 600), fill=BLACK); d.text((PX, y + 76), ja, font=jp(36, 500), fill=GREY)
        d.line((PX, y + 138, W - PX, y + 138), fill=(210, 203, 185), width=2); y += 162
    asterisk(d, W - 110, 260, 30, RED)
    bottom_note(d, "保存して、単語帳がわりに"); im.convert("RGB").save(out / f"0{p}_words.png"); p += 1
    # 案内(黒地)
    im = Image.new("RGBA", (W, H), BLACK + (255,)); d = ImageDraw.Draw(im)
    d.text((64, 50), "@toeic_read30", font=anton(30), fill=CREAM)
    d.text((W - 64, 50), f"No.{no:02d}  {p}/{total}", font=anton(30), fill=CREAM, anchor="ra")
    paste(im, text_img("毎日1問、", jp(110), CREAM), (64, 300))
    paste(im, zabuton(text_img("30秒", jp(170), CREAM), RED, 18, 6), (64, 450), 3)
    paste(im, text_img("で読む力をつける。", jp(96), CREAM), (64, 700)); d = ImageDraw.Draw(im)
    for i, t in enumerate(["🔖 保存して、本番前に見返す", "👤 フォローで毎日1問とどく", "🔗 プロフィールから無料の復習ページへ"]):
        d.text((70, 920 + i * 70), t.split(" ", 1)[1], font=jp(36, 700), fill=CREAM)
        d.ellipse((40 - 10, 942 + i * 70 - 10, 40 + 10, 942 + i * 70 + 10), fill=RED)
    asterisk(d, W - 130, 360, 40, RED)
    im.convert("RGB").save(out / f"0{p}_cta.png")
    return sorted(out.glob("0*.png"))

if __name__ == "__main__":
    for Q in PROBLEMS:
        if len(sys.argv) > 1 and str(Q["no"]) not in sys.argv[1:]: continue
        d = ROOT / "out" / "toeic_reading" / f"no{Q['no']:03d}"
        for f in d.glob("0*.png"): f.unlink()
        fs = build(Q, d)
        tw = 270; sheet = Image.new("RGB", (tw * 4 + 12, int(tw * 1.25) * 2 + 4), "white")
        for i, f in enumerate(fs):
            sheet.paste(Image.open(f).resize((tw, int(tw * 1.25))), ((i % 4) * (tw + 4), (i // 4) * (int(tw * 1.25) + 4)))
        sheet.save(d / "overview.png"); print(Q["no"], len(fs))
