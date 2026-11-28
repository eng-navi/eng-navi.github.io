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


_tts = gr.tts
gr.tts = lambda kind, text: _tts(kind, text.replace("*", ""))  # 台本の *強調* は字幕用。読み上げでは外す


def dur(kind, text):
    _, d = gr.tts(kind, text)
    gr.MANIFEST.pop()
    return d


# 字幕は画面用の表記に(読み上げ用のカタカナ → 英字)
DISP = {"ハウエバー": "However", "ノット・オール": "not all", "ばつ": "×"}


def psub(base, t, items, y=1440):
    """参考動画(reference/grammar_style)の字幕:ひとことずつ、ポンと出る。*強調* は黄緑。items=[(開始秒, 台本, 長さ)]"""
    phrases = []
    for st, text, d in items:
        for k, v in DISP.items():
            text = text.replace(k, v)
        ps = [x for x in re.split(r"(?<=[、。?])", text) if x.strip()]
        n = sum(len(x.replace("*", "")) for x in ps)
        acc = st
        for x in ps:
            phrases.append((acc, x)); acc += d * len(x.replace("*", "")) / n
    cur = [p for p in phrases if p[0] <= t]
    if not cur: return
    t0, text = cur[-1]
    text = text.rstrip("、。")
    f = gr.jp(54)
    segs = [(x, i % 2 == 1) for i, x in enumerate(text.split("*")) if x]
    w = sum(f.getlength(x) for x, _ in segs)
    lay = Image.new("RGBA", (int(w) + 40, 90), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    x = 20
    for s, em in segs:
        g.text((x, 8), s, font=f, fill=(GREEN if em else (255, 255, 255)) + (255,), stroke_width=2, stroke_fill=(20, 30, 120, 255))
        x += f.getlength(s)
    k = gr.back((t - t0) / 0.22)
    sc = 0.82 + 0.18 * k
    if t - t0 < 0.12:
        lay = lay.filter(ImageFilter.GaussianBlur(4 * (1 - (t - t0) / 0.12)))
    gr.paste_rot(base, lay, W / 2, y, 0, scale=sc)


def zigzag(base, t, x, y, d=0.0, n=4, size=26, angle=0):
    """黄緑のギザギザ(参考動画の飾り)。描かれていき、少しゆれる"""
    if t < d: return
    p = gr.ease((t - d) / 0.3)
    import math
    j = 3 * math.sin((t - d) * 9)
    pts = [(x + i * size, y + (size * 0.6 if i % 2 else 0) + j) for i in range(int((n * 2) * p) + 1)]
    if len(pts) > 1:
        ImageDraw.Draw(base).line(pts, fill=GREEN, width=9, joint="curve")


def burst(base, t, cx, cy, r=230, d=0.0, n=12):
    """正解の数字のまわりに集中線がはじける"""
    if t < d: return
    import math
    p = gr.ease((t - d) / 0.35)
    g = ImageDraw.Draw(base)
    for i in range(n):
        a = i / n * 2 * math.pi + 0.2
        r0, r1 = r * (0.8 + 0.25 * p), r * (0.8 + 0.6 * p)
        g.line([(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + r1 * math.cos(a), cy + r1 * math.sin(a))], fill=GREEN, width=10)


def step_tag(base, t, no, name, d=0.0):
    """右上のテープ札「01 合図」(横からすべり込む)"""
    if t < d: return
    k = gr.ease((t - d) / 0.3)
    f1, f2 = gr.font("Anton-Regular.ttf", 44), gr.jp(40)
    w = int(f1.getlength(no) + f2.getlength(name) + 80)
    lay = Image.new("RGBA", (w, 84), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    g.rectangle([0, 6, w - 1, 78], fill=CREAM + (250,))
    g.text((24, 14), no, font=f1, fill=(20, 20, 20, 255))
    g.text((24 + f1.getlength(no) + 18, 16), name, font=f2, fill=(20, 20, 20, 255))
    gr.paste_rot(base, lay, 1080 - w / 2 - 50 + (1 - k) * 300, 250, 3)


def float_y(t, amp=5):
    import math
    return amp * math.sin(t * 2.2)


def scene(S, content, parts, default=2.0, outro=0.28):
    """場面の終わりで、前の画面がぼけながら上へ消える。字幕は日本語ナレーションから自動で"""
    ds = [dur(k, x) for k, x in parts]
    D = max(1.3, 0.08 + sum(d + 0.08 for d in ds) + 0.12) if parts else default
    subs, acc = [], 0.08
    for (k, x), d in zip(parts, ds):
        if k == "ja": subs.append((acc, x, d))
        acc += d + 0.08

    def draw(bb, t):
        content(bb, t)
        psub(bb, t, subs)

    def f(bb, TT, t):
        ko = max(0.0, (t - (D - outro)) / outro)
        if ko <= 0:
            draw(bb, t); return
        k = gr.ease(ko)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw(lay, t)
        lay = lay.filter(ImageFilter.GaussianBlur(10 * k))
        lay.putalpha(lay.split()[3].point(lambda v: int(v * (1 - k))))
        bb.alpha_composite(lay.crop((0, int(70 * k), W, H)), (0, 0))
    S.append((D, "", f, parts))


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


def ja_card(base, t, ja, y, d=0.0, hl=None, dim=None, size=34):
    """和訳のブロック(❶❷❸ごと)。止めてじっくり見る人のために、本文と同じ文を同じように強調・薄く"""
    hl, dim = hl or {}, dim or set()
    f, fn = gr.jp(size, bold=False), gr.jp(size - 2)
    body = ja.split("\n", 1)[-1]
    parts = [(NUM.index(m) + 1, x.strip()) for m, x in re.findall(r"([❶❷❸❹])([^❶❷❸❹]+)", body)]
    maxw, lh = 920 - 120, int(size * 1.55)
    rows = []
    for n, x in parts:
        line = ""
        for ch in x:
            if f.getlength(line + ch) > maxw and ch not in "、。」)":  # 句読点は行頭に置かない
                rows.append((n, line)); line = ch
            else:
                line += ch
        rows.append((n, line))
    hgt = 40 + lh * len(rows) + 10 * len(parts) + 20
    lay = Image.new("RGBA", (920, hgt), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    g.rounded_rectangle([0, 0, 919, hgt - 1], 18, fill=(236, 230, 214, 255))
    g.text((24, 14), "和訳", font=gr.jp(26), fill=(120, 110, 90, 255))
    yy, prev = 52, None
    for n, line in rows:
        if prev is not None and n != prev: yy += 10
        col = (165, 158, 140) if n in dim else (25, 25, 25)
        if n != prev:
            g.text((28, yy + 2), NUM[n - 1], font=fn, fill=gr.THEMES["blue"]["bg"] if n not in dim else col)
        ph = hl.get(n)
        if ph and ph in line:
            a = line.index(ph)
            g.rectangle([80 + f.getlength(line[:a]) - 3, yy + 6, 80 + f.getlength(line[:a + len(ph)]) + 3, yy + lh - 6], fill=YEL + (255,))
        g.text((80, yy), line, font=f, fill=col)
        yy += lh; prev = n
    appear(base, lay, (W - 920) / 2, y, t, d)


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
        signal=("However", "しかし"),
        signal_say="ポイントは、*ハウエバー*。前と*逆の流れ*になる合図です。",
        steps=[
            dict(tag="プラスの話", hl={1: "trust online reviews"}, hl_ja={1: "信頼している"}, dim={2, 3},
                 say="まず1文目。買い物客は、ネットのレビューを*信頼している*。*プラスの話*です。"),
            dict(tag="根拠", hl={3: "pay people to write positive comments"}, hl_ja={3: "お金を払って良いコメントを書かせる"}, dim={1, 2},
                 say="次に3文目。*お金をはらって*、良いコメントを書かせる会社がある。つまり、*うそのレビュー*もある、ということ。"),
        ],
        answer_say="だから*正解は1*。*ノット・オール*は、すべてがそうとは限らない、という*部分否定*です。",
        trap_say="2は、ハウエバーの前と*同じ向き*なので、ばつ。",
    ),
}


def build(L):
    import eiken_problems as ep
    Q = next(q for q in ep.PROBLEMS if q["no"] == L["no"])
    sc = SCRIPTS[L["no"]]
    sents = [(re.sub(r"\(\s*①\s*\)", "( ① )", s), n) for s, n in Q["body"][0]]
    chs, ans = Q["choices"], Q["answer"]
    S = []
    # 0〜約2.5秒:問題 → 「止めてね」→ すぐ解説へ
    scene(S, lambda bb, t: (
        label(bb, t, "英検 空所補充", 300, size=46, color=GREEN),
        label(bb, t, "( ① ) に入るのは?", 370, d=0.1, size=64),
        choices(bb, t, chs, passage(bb, t, sents, y=490, d=0.15) + 30, d=0.3),
        zigzag(bb, t, 70, 330, d=0.4), zigzag(bb, t, 860, 330, d=0.5),
        pause_tip(bb, t, d=0.6, y=1330)),
        [("ja", "どっちが入る?解くなら、ここで止めてね。")])
    sig, sig_ja = sc["signal"]
    scene(S, lambda bb, t: (
        step_tag(bb, t, "01", "合図の言葉"),
        gr.big(bb, T, t, sig, 700 + float_y(t), size=230),
        gr.tape(bb, T, t, sig_ja, 540, 960, angle=-4, d=0.3, size=80),
        gr.scribble(bb, T, t, 540, 960, 300, 110, d=0.7),
        zigzag(bb, t, 120, 560, d=0.5), zigzag(bb, t, 800, 1100, d=0.8, angle=0)),
        [("ja", sc["signal_say"])])
    for i, st in enumerate(sc["steps"]):
        scene(S, lambda bb, t, st=st, i=i: (
            step_tag(bb, t, f"{i + 2:02d}", st["tag"]),
            ja_card(bb, t, Q["ja"], passage(bb, t, sents, y=340 + float_y(t, 3), hl=st["hl"], dim=st["dim"]) + 24,
                    d=0.25, hl=st.get("hl_ja"), dim=st["dim"])),
            [("ja", st["say"])])
    good = chs[ans - 1]
    n0 = len(sc["steps"]) + 2
    scene(S, lambda bb, t: (
        step_tag(bb, t, f"{n0:02d}", "正解"),
        burst(bb, t, 540, 600, d=0.15),
        gr.big(bb, T, t, str(ans), 600, size=300, color=GREEN),
        gr.tape(bb, T, t, good[0], 540, 930, angle=-3, d=0.25, size=min(60, gr._tape_size(good[0], 60))),
        gr.tape(bb, T, t, good[1], 540, 1090, angle=2, d=0.5, size=52),
        gr.scribble(bb, T, t, 540, 930, 470, 100, d=0.8)),
        [("ja", sc["answer_say"])])
    scene(S, lambda bb, t: (
        step_tag(bb, t, f"{n0 + 1:02d}", "ひっかけ"),
        choices(bb, t, chs, 640 + float_y(t, 3), mark={ans: "o", 3 - ans: "x"}),
        gr.cross(bb, T, t, 540, 790 if ans == 1 else 690, s=60, d=0.4),
        zigzag(bb, t, 90, 560, d=0.5)),
        [("ja", sc["trap_say"])])
    scene(S, lambda bb, t: (
        label(bb, t, "全文の訳・単語はコメント欄に", 560, size=48),
        gr.big(bb, T, t, "保存して復習", 820 + float_y(t), size=120, d=0.2, color=GREEN),
        gr.tape(bb, T, t, "次は自力で解いてみよう", 540, 1060, angle=-2, d=0.5, size=56),
        zigzag(bb, t, 120, 700, d=0.6), zigzag(bb, t, 820, 940, d=0.7)),
        [("ja", "*保存して*、あとで自分で解いてみてね。")])
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
