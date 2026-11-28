"""英検リーディング部のリール(新形式・テスト):問題は eiken_problems.py のまま、作りは「やさしい英文法」(青コラージュ)。

    python3 eiken_easy.py 31        # → out/eiken_easy/eiken_031.mp4(作成+読みチェック)

流れ(2026-11-28 ユーザー案):問題を見せる → 約2秒で「解きたい人はここで止めてね」→ すぐ解説(離脱させない)
→ 合図の語 → 根拠の文 → 正解 → ひっかけ → 保存の呼びかけ。
動き:参考動画(reference/seidoku_style/)のように、ぼかしからふわっと出す・切り替えで前の画面がぼけて上へ消える。
声:日本語=Shizuka(v3・1.45倍)、英文=イギリス英語 Daniel / Alice(英文法リールと同じ)。
"""
import re
import subprocess
import sys
import types
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

import grammar_reel as gr

ROOT = Path(__file__).parent
OUT = ROOT / "out" / "eiken_easy"
W, H = gr.W, gr.H
T = gr.THEMES["blue"]
CREAM, GREEN, YEL = T["big"], T["accent"], (255, 232, 92)


# ---------- 動き(参考動画) ----------
def appear(base, lay, x, y, t, d=0.0, dur=0.35, rise=40):
    if t < d: return
    k = gr.ease((t - d) / dur)
    if k < 1:
        lay = lay.filter(ImageFilter.GaussianBlur((1 - k) * 10))
        lay.putalpha(lay.split()[3].point(lambda v: int(v * k)))
    base.alpha_composite(lay, (int(x), int(y + (1 - k) * rise)))


def dur(kind, text):
    _, d = gr.tts(kind, text)
    gr.MANIFEST.pop()
    return d


def scene(S, content, parts, sub="", default=2.0, outro=0.28):
    """場面の終わりで、前の画面がぼけながら上へ消える"""
    D = max(1.3, 0.08 + sum(dur(k, x) + 0.08 for k, x in parts) + 0.12) if parts else default

    def f(bb, TT, t):
        ko = max(0.0, (t - (D - outro)) / outro)
        if ko <= 0:
            content(bb, t); return
        k = gr.ease(ko)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        content(lay, t)
        gr.subtitle(lay, T, sub)
        lay = lay.filter(ImageFilter.GaussianBlur(10 * k))
        lay.putalpha(lay.split()[3].point(lambda v: int(v * (1 - k))))
        bb.alpha_composite(lay.crop((0, int(70 * k), W, H)), (0, 0))
    # 切り替え中は字幕も一緒に消すので、通常時の字幕は render 側(sub)ではなくここで描く
    def g(bb, TT, t):
        f(bb, TT, t)
        if t < D - outro:
            gr.subtitle(bb, T, sub)
    S.append((D, "", g, parts))


# ---------- 部品 ----------
def wrap(text, f, maxw):
    out, cur = [], ""
    for w in text.split(" "):
        if f.getlength((cur + " " + w).strip()) > maxw and cur:
            out.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    return out + [cur]


NUM = "❶❷❸❹"


def passage(base, t, sents, y=430, d=0.0, hl=None, dim=None, size=40):
    """本文カード。hl={文番号: ハイライトする語句}、dim=薄くする文番号の集合"""
    hl, dim = hl or {}, dim or set()
    f, fn = gr.serif(size, 600), gr.jp(size - 4)
    maxw = 880 - 70
    rows = []
    for text, n in sents:
        ph = hl.get(n)
        hs = text.index(ph) if ph and ph in text else -1
        off = 0
        for i, line in enumerate(wrap(text, f, maxw)):
            st = text.index(line, off); off = st + len(line)
            rng = (max(hs, st) - st, min(hs + len(ph), off) - st) if hs >= 0 and hs < off and hs + len(ph) > st else None
            rows.append((NUM[n - 1] if i == 0 else "", line, n, rng))
        rows.append(None)
    rows = rows[:-1]
    lh = int(size * 1.45)
    hgt = 50 + sum(lh if r else 16 for r in rows) + 30
    lay = Image.new("RGBA", (940, hgt + 20), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    g.rounded_rectangle([0, 0, 920, hgt], 18, fill=(255, 255, 255, 255))
    yy = 40
    for r in rows:
        if not r:
            yy += 16; continue
        mark, line, n, rng = r
        col = (185, 185, 185) if n in dim else (20, 20, 20)
        if mark:
            g.text((28, yy + 2), mark, font=fn, fill=gr.THEMES["blue"]["bg"] if n not in dim else col)
        x = 80
        if rng:
            x0 = x + f.getlength(line[:rng[0]]); x1 = x + f.getlength(line[:rng[1]])
            g.rectangle([x0 - 3, yy + 6, x1 + 3, yy + lh - 8], fill=YEL + (255,))
        for part in re.split(r"(①)", line):  # ① は英字フォントにないので日本語フォントで
            ff = fn if part == "①" else f
            g.text((x, yy + (4 if part == "①" else 0)), part, font=ff, fill=col)
            x += ff.getlength(part)
        yy += lh
    appear(base, lay, (W - 920) / 2, y, t, d)
    return y + hgt


def choices(base, t, chs, y, d=0.0, mark=None):
    """選択肢 1 / 2。mark={番号: "o" or "x"}"""
    f, fn = gr.serif(40, 600), gr.font("Anton-Regular.ttf", 56)
    lay = Image.new("RGBA", (920, 200), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    for i, (en, _) in enumerate(chs):
        yy = i * 98
        on = (mark or {}).get(i + 1)
        g.rounded_rectangle([0, yy, 919, yy + 84], 16, fill=(GREEN if on == "o" else (236, 230, 214)) + (255,))
        g.text((26, yy + 6), str(i + 1), font=fn, fill=(20, 20, 20, 255))
        g.text((90, yy + 16), en, font=f, fill=(20, 20, 20, 255) if on != "x" else (150, 150, 150, 255))
        if on == "x":
            g.line([(84, yy + 42), (90 + f.getlength(en) + 6, yy + 42)], fill=(207, 62, 34, 255), width=6)
    appear(base, lay, (W - 920) / 2, y, t, d)


def label(base, t, s, y, d=0.0, size=54, color=None):
    f = gr.jp(size)
    lay = Image.new("RGBA", (W, int(size * 1.5)), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((W / 2, size * 0.75), s, font=f, fill=(color or CREAM) + (255,), anchor="mm")
    appear(base, lay, 0, y, t, d, rise=20)


def pause_tip(base, t, d=0.9, y=1280):
    """「解きたい人は、ここで止めてね」(長押し・タップで止められる)"""
    if t < d: return
    gr.tape(base, T, t, "解きたい人は、ここで一時停止", 540, y, angle=-2, d=d, size=48)


# ---------- 台本 ----------
SCRIPTS = {
    31: dict(
        signal=("However", "しかし", "前と逆の流れになる合図"),
        steps=[
            dict(sub="❶ はプラスの話\n「レビューを信頼している」", hl={1: "trust online reviews"}, dim={2, 3},
                 say="まず1文目。買い物客は、ネットのレビューを信頼している。プラスの話です。"),
            dict(sub="❸ に根拠\n「お金を払って良いコメントを書かせる」", hl={3: "pay people to write positive comments"}, dim={1, 2},
                 say="次に3文目。お金をはらって、良いコメントを書かせる会社がある。つまり、うそのレビューもある、ということ。"),
        ],
        answer_say="だから正解は1。ノット・オールは、すべてがそうとは限らない、という部分否定です。",
        answer_sub="正解は 1\nnot all =「すべてが〜なわけではない」",
        trap_say="2は、ハウエバーの前と同じ向きなので、ばつ。",
        trap_sub="2 は ❶ と同じ向き → ×",
    ),
}


def build(L):
    import eiken_problems as ep
    Q = next(q for q in ep.PROBLEMS if q["no"] == L["no"])
    sc = SCRIPTS[L["no"]]
    sents = [(re.sub(r"\(\s*①\s*\)", "( ① )", s), n) for s, n in Q["body"][0]]
    chs, ans = Q["choices"], Q["answer"]
    S = []
    # 0〜約2秒:問題 → 「止めてね」→ すぐ解説へ
    scene(S, lambda bb, t: (
        label(bb, t, "英検 空所補充", 300, size=46, color=GREEN),
        label(bb, t, "( ① ) に入るのは?", 370, d=0.1, size=64),
        choices(bb, t, chs, passage(bb, t, sents, y=490, d=0.15) + 30, d=0.3),
        pause_tip(bb, t, d=0.6, y=1330)),
        [("ja", "どっちが入る?解くなら、ここで止めてね。")])
    sig, sig_ja, sig_mean = sc["signal"]
    scene(S, lambda bb, t: (
        gr.big(bb, T, t, sig, 700, size=230),
        gr.tape(bb, T, t, sig_ja, 540, 960, angle=-4, d=0.3, size=80),
        gr.scribble(bb, T, t, 540, 960, 300, 110, d=0.7)),
        [("ja", f"ポイントは、{'ハウエバー' if sig == 'However' else sig}。前と逆の流れになる合図です。")],
        sub=f"{sig} =「{sig_ja}」\n{sig_mean}")
    for st in sc["steps"]:
        scene(S, lambda bb, t, st=st: passage(bb, t, sents, y=420, hl=st["hl"], dim=st["dim"]),
              [("ja", st["say"])], sub=st["sub"])
    good, bad = chs[ans - 1], chs[2 - ans]
    scene(S, lambda bb, t: (
        gr.big(bb, T, t, str(ans), 560, size=300, color=GREEN),
        gr.tape(bb, T, t, good[0], 540, 900, angle=-3, d=0.25, size=min(60, gr._tape_size(good[0], 60))),
        gr.tape(bb, T, t, good[1], 540, 1060, angle=2, d=0.5, size=52),
        gr.scribble(bb, T, t, 540, 900, 470, 100, d=0.8)),
        [("ja", sc["answer_say"])], sub=sc["answer_sub"])
    scene(S, lambda bb, t: (
        choices(bb, t, chs, 640, mark={ans: "o", 3 - ans: "x"}),
        gr.cross(bb, T, t, 540, 790 if ans == 1 else 690, s=60, d=0.4)),
        [("ja", sc["trap_say"])], sub=sc["trap_sub"])
    scene(S, lambda bb, t: (
        label(bb, t, "全文の訳・単語はコメント欄に", 560, size=48),
        gr.big(bb, T, t, "保存して復習", 820, size=120, d=0.2, color=GREEN),
        gr.tape(bb, T, t, "次は自力で解いてみよう", 540, 1060, angle=-2, d=0.5, size=56)),
        [("ja", "保存して、あとで自分で解いてみてね。")])
    return "blue", S


def render(no):
    sys.modules["grammar_lessons"] = types.SimpleNamespace(LESSONS=[{"no": no}])
    gr.lesson = build
    OUT.mkdir(parents=True, exist_ok=True)
    out, starts = gr.render(0, no, OUT / f"eiken_{no:03d}.mp4")
    r = subprocess.run([str(ROOT / ".venv-tts/bin/python"), str(ROOT / "yomi_check.py"), str(out.with_suffix(".voice.json")), "--quiet"],
                       capture_output=True, text=True).stdout.strip()
    print(r)
    return out


if __name__ == "__main__":
    for a in sys.argv[1:] or ["31"]:
        render(int(a))
