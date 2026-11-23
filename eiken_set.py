"""英検リーディング部のカルーセル1セット。中のページは試験の紙に近いクリーム地+濃い字。型は TOEIC の確定版と同じ。"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
import toeic_set as ts
from eiken_problems import PROBLEMS
from eiken_cover import make as cover, NAVY, BLUE, SKY, SAND, watch, text_im, put, pf, go, star, flower
ROOT = Path(__file__).parent
PAPER_BG = (247, 241, 224)
ts.NUM_GAP = 14
ts.BLACK, ts.RED, ts.PAPER, ts.MARK, ts.CREAM, ts.GREY = NAVY, BLUE, (253, 250, 242), (200, 218, 240), (247, 241, 224), (110, 116, 130)
TITLES = ("答えと根拠", "ワナの選択肢", "解き方のコツ")
W, H, PX, PW, TOP, BOTTOM = ts.W, ts.H, 64, ts.W - 128, ts.TOP, ts.BOTTOM

def P(Q): return {"kind": Q["title"].upper(), "head": [], "body": Q["body"]}
def base(): return Image.new("RGBA", (W, H), PAPER_BG + (255,))
def note(d, left, swipe=True):
    d.text((64, H - 58), left, font=ts.jp(30, 700), fill=NAVY, anchor="lm")
    if swipe: d.text((W - 64, H - 58), "swipe →", font=pf(44), fill=NAVY, anchor="rm")

def build(Q, out):
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("0*.png"): f.unlink()
    v, (teaser, word, line) = Q["layout"], Q["cover"]
    cover(v, Q["photo"], Q["no"], teaser, word, line, Q["level"], out / "01_cover.png")
    d0 = ImageDraw.Draw(base()); QF, CF, EF = ts.serif(42, 600), ts.serif(40), ts.jp(37, 500)
    ql = ts.wrap_jp(d0, Q["q"], QF, PW); els = [ts.wrap_jp(d0, e["text"], EF, PW) for e in Q["explain"]]
    rooms = [BOTTOM - TOP - 40 - len(ql) * 54 - 20 - len(Q["choices"]) * 86] + [BOTTOM - TOP - 36 - (116 if k == 0 else 0) - len(el) * 60 for k, el in enumerate(els)]
    size = min(ts.fit(P(Q), TOP, r, 52, 30) for r in rooms)
    # 2 問題
    im = base(); h = ts.passage(im, PX, TOP, PW, P(Q), size, timer=Q["sec"]); d = ImageDraw.Draw(im); y = TOP + h + 40
    for ln in ql: d.text((PX, y), ln, font=QF, fill=NAVY); y += 54
    y += 20
    for i, (c, _) in enumerate(Q["choices"]):
        put(im, text_im(str(i + 1), go(40, 900), PAPER_BG, (18, 4), NAVY), (PX, y + 4)); d = ImageDraw.Draw(im)
        d.text((PX + 80, y), c, font=ts.serif(44), fill=NAVY); y += 86
    note(d, "1か2か、コメントで答えてね"); im.convert("RGB").save(out / "02_question.png")
    # 3 和訳
    hP = ts.passage(base(), PX, TOP, PW, P(Q), size)
    def ja_fit():
        for withq, lo in ((True, 29), (False, 26)):
            for js in range(33, lo - 1, -1):
                JF = ts.jp(js, 600); jl = ts.wrap_jp(d0, Q["ja"], JF, PW)
                qj = [l for t in [f"設問:{Q['q_ja']}"] + [f"{i + 1}. {c[1]}" for i, c in enumerate(Q["choices"])] for l in ts.wrap_jp(d0, t, ts.jp(js - 1, 600), PW)] if withq else []
                if TOP + hP + 32 + len(jl) * int(js * 1.5) + (34 + len(qj) * int(js * 1.45) if qj else 0) <= BOTTOM: return js, JF, jl, qj
        return js, JF, jl, []
    js, JF, jl, qj = ja_fit()
    im = base(); ts.passage(im, PX, TOP, PW, P(Q), size, label="全文の和訳"); d = ImageDraw.Draw(im); y = TOP + hP + 32
    for l in jl: d.text((PX, y), l, font=JF, fill=NAVY); y += int(js * 1.5)
    if qj: y += 14; d.line((PX, y, W - PX, y), fill=SKY, width=2); y += 20
    for l in qj: d.text((PX, y), l, font=ts.jp(js - 1, 600), fill=NAVY); y += int(js * 1.45)
    note(d, "もう一度考えてみて。答えは次へ"); im.convert("RGB").save(out / "03_ja.png")
    # 4〜6 解説
    for k, e in enumerate(Q["explain"]):
        im = base(); h = ts.passage(im, PX, TOP, PW, P(Q), size, hl=e["hl"], label=f"{TITLES[k]}  {k + 1}/3"); d = ImageDraw.Draw(im); y = TOP + h + 36
        if k == 0:
            put(im, text_im(f"答え  {Q['answer']}. {Q['choices'][Q['answer'] - 1][0]}", go(46, 800), PAPER_BG, (22, 12), NAVY), (PX, y)); d = ImageDraw.Draw(im); y += 116
        for l in els[k]: d.text((PX, y), l, font=EF, fill=NAVY); y += 60
        note(d, f"解説 {k + 1}/3"); im.convert("RGB").save(out / f"0{4 + k}_explain{k + 1}.png")
    # 7 単語
    im = base(); d = ImageDraw.Draw(im)
    put(im, text_im("この問題の単語", go(40, 800), PAPER_BG, (20, 12), NAVY), (64, 64)); d = ImageDraw.Draw(im); y = 200
    for en, ja in Q["words"]:
        d.text((PX, y), en, font=ts.serif(58, 600), fill=NAVY); d.text((PX, y + 76), ja, font=ts.jp(36, 500), fill=ts.GREY)
        d.line((PX, y + 138, W - PX, y + 138), fill=SKY, width=2); y += 162
    star(d, W - 110, 110, 40, SAND, 7); note(d, "保存して、単語帳がわりに"); im.convert("RGB").save(out / "07_words.png")
    # 8 案内(これもクリーム地)
    im = base(); d = ImageDraw.Draw(im)
    d.text((70, 330), "毎日1問、", font=go(100, 900), fill=NAVY)
    put(im, text_im("長文の空所", go(130, 900), PAPER_BG, (24, 10), NAVY).rotate(2, expand=True, resample=Image.BICUBIC), (64, 470))
    d = ImageDraw.Draw(im); d.text((70, 820), "に強くなる。", font=go(100, 900), fill=NAVY)
    for i, t in enumerate(["保存して、試験前に見返す", "フォローで毎日1問とどく", "プロフィールから無料の復習ページへ"]):
        d.ellipse((60, 1004 + i * 70, 80, 1024 + i * 70), fill=BLUE); d.text((100, 1014 + i * 70), t, font=go(36, 700), fill=NAVY, anchor="lm")
    flower(d, W - 160, 300, 70, SAND); star(d, W - 140, 800, 46, BLUE, seed=9)
    im.convert("RGB").save(out / "08_cta.png")
    return sorted(out.glob("0*.png"))

if __name__ == "__main__":
    for Q in PROBLEMS:
        if len(sys.argv) > 1 and str(Q["no"]) not in sys.argv[1:]: continue
        d = ROOT / "out" / "eiken" / f"no{Q['no']:03d}"; fs = build(Q, d)
        t = 270; s = Image.new("RGB", (t * 4 + 12, int(t * 1.25) * 2 + 4), "white")
        for i, f in enumerate(fs): s.paste(Image.open(f).resize((t, int(t * 1.25))), ((i % 4) * (t + 4), (i // 4) * (int(t * 1.25) + 4)))
        s.save(d / "overview.png"); print(Q["no"], len(fs))
