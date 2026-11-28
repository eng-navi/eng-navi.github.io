"""YouTube 長い動画(解説型・横長 1920x1080)。見た目・声は「差がつく英文読解」と同じ(白い方眼・青の選択枠・Otani/Liam/Jessica)。

    python3 yt_explain.py test     # 1問だけのテスト版 → out/yt_explain/test.mp4

流れ(1問):問題(英文+2択、考える時間)→ 正解(英文を英語で読む。男女は1問ごとに交互)→ 解説(なぜそうなるか)
動画全体:冒頭で「この動画で分かること」→ 問題を順に → 6割あたりと最後に案内(PR。説明欄へ。キャンペーンがあれば一言)
"""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

import seidoku_reel as sr  # 声(Otani/Liam/Jessica・日本語1.45倍)と tts、selbox など
import grammar_reel as gr

ROOT = Path(__file__).parent
OUT = ROOT / "out" / "yt_explain"
W, H, FPS = 1920, 1080, 30
BLUE, INK, GRAY, LIGHT = sr.BLUE, sr.INK, sr.GRAY, (232, 239, 255)
MINT = sr.ORANGE
DISP = {"トゥー・ウィークス・アゴー": "two weeks ago", "アゴー": "ago", "イエスタデイ": "yesterday", "ビジテッド": "visited",
        "ハブ・ビジテッド": "have visited"}


def bg():
    im = Image.new("RGB", (W, H), (247, 247, 245))
    d = ImageDraw.Draw(im)
    for x in range(0, W, 64): d.line([(x, 0), (x, H)], fill=(230, 230, 228), width=2)
    for y in range(0, H, 64): d.line([(0, y), (W, y)], fill=(230, 230, 228), width=2)
    return im.convert("RGBA")


def appear(base, lay, x, y, t, d=0.0, dur=0.35, rise=30):
    if t < d: return
    k = gr.ease((t - d) / dur)
    if k < 1:
        lay = lay.filter(ImageFilter.GaussianBlur((1 - k) * 10))
        lay.putalpha(lay.split()[3].point(lambda v: int(v * k)))
    base.alpha_composite(lay, (int(x), int(y + (1 - k) * rise)))


def card(w, h, title=None):
    lay = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", lay.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([20, 28, w + 20, h + 28], 26, fill=(0, 0, 0, 30))
    lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    g = ImageDraw.Draw(lay)
    g.rounded_rectangle([20, 20, w + 20, h + 20], 26, fill=(255, 255, 255, 255), outline=(232, 232, 232, 255), width=2)
    if title: g.text((60, 44), title, font=gr.jp(30), fill=(150, 150, 150, 255))
    return lay, g


def segs(s):
    return [(x, i % 2 == 1) for i, x in enumerate(s.split("*")) if x]


def header(base, t, l1, l2, y=50, s1=40, s2=60):
    f1, f2 = gr.jp(s1, bold=False), gr.jp(s2)
    lay1 = Image.new("RGBA", (W, int(s1 * 1.6)), (0, 0, 0, 0))
    ImageDraw.Draw(lay1).text((W / 2, s1 * 0.8), l1, font=f1, fill=GRAY + (255,), anchor="mm")
    appear(base, lay1, 0, y, t, 0.0, rise=14)
    lay = Image.new("RGBA", (W, int(s2 * 1.9)), (0, 0, 0, 0)); g = ImageDraw.Draw(lay)
    ss = segs(l2); x = (W - sum(f2.getlength(a) for a, _ in ss)) / 2
    for a, kw in ss:
        w = f2.getlength(a)
        if kw: sr.selbox(g, x - 12, s2 * 0.25, x + w + 12, s2 * 1.65, 7)
        g.text((x, s2 * 0.18), a, font=f2, fill=INK + (255,)); x += w
    appear(base, lay, 0, y + s1 * 1.5, t, 0.2, rise=14)


def step_pill(base, t, no, label, x=70, y=60):
    fn, fl = gr.jp(28), gr.jp(34)
    w = 100 + int(fl.getlength(label)) + 40
    lay = Image.new("RGBA", (w, 70), (0, 0, 0, 0)); g = ImageDraw.Draw(lay)
    g.rounded_rectangle([0, 0, w - 1, 69], 35, fill=BLUE + (255,))
    g.rounded_rectangle([14, 13, 86, 57], 12, fill=(108, 148, 242, 255))
    g.text((50, 35), no, font=fn, fill=(255, 255, 255, 255), anchor="mm")
    g.text((104, 35), label, font=fl, fill=(255, 255, 255, 255), anchor="lm")
    appear(base, lay, x, y, t, 0.0, rise=0)


def wrap(text, f, maxw):
    out, cur = [], ""
    for w in text.split(" "):
        if f.getlength((cur + " " + w).strip()) > maxw and cur: out.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    return out + [cur]


def q_card(base, t, Q, state, x=90, y=250, d=0.1, hl=None):
    """左:英文と選択肢。state: "q"(空所)/"a"(正解を入れる)。hl=英文で青くする語句"""
    f, fc = gr.serif(62, 600), gr.serif(52, 600)
    ans = Q["options"][Q["answer"] - 1]
    text = Q["question"].replace("( )", ans if state == "a" else "(   )")
    lines = wrap(text, f, 820)
    lh = 92
    hgt = 110 + lh * len(lines) + 60 + 2 * 96 + 30
    lay, g = card(900, hgt, "英文")
    yy = 100
    for line in lines:
        xx = 60
        marks = [m for m in ([ans] if state == "a" else []) + ([hl] if hl else []) if m and m in line]
        parts = re.split("(" + "|".join(map(re.escape, marks)) + ")", line) if marks else [line]
        for p in parts:
            on = p in marks
            if on:
                g.rectangle([xx - 4, yy + 8, xx + f.getlength(p) + 4, yy + lh - 8], fill=LIGHT + (255,))
            g.text((xx, yy), p, font=f, fill=(BLUE if on else INK) + (255,)); xx += f.getlength(p)
        yy += lh
    yy += 40
    for i, opt in enumerate(Q["options"]):
        ok = state == "a" and i + 1 == Q["answer"]
        g.rounded_rectangle([60, yy, 880, yy + 80], 18, fill=(LIGHT if ok else (246, 246, 246)) + (255,),
                            outline=(BLUE if ok else (230, 230, 230)) + (255,), width=3 if ok else 2)
        g.text((96, yy + 40), "①②"[i], font=gr.jp(44), fill=BLUE + (255,), anchor="lm")
        col = INK if (state != "a" or ok) else (175, 175, 175)
        g.text((160, yy + 40), opt, font=fc, fill=col + (255,), anchor="lm")
        yy += 96
    appear(base, lay, x, y, t, d)


def right_card(base, t, title, rows, x=1030, y=200, d=0.2, w=840):
    rows = [r if isinstance(r, tuple) else (r, 37, True) for r in rows]
    """右:和訳・解説。rows=[(文, 大きさ, 太字?)]。*語* は青"""
    lay, g = card(w, 10, title)  # 高さはあとで
    ys, tot = [], 100
    out = []
    for text, size, bold in rows:
        f = gr.jp(size, bold=bold)
        line, lines = "", []
        plain = text
        for ch in plain:
            if f.getlength((line + ch).replace("*", "")) > w - 110 and ch not in "、。」)":
                lines.append(line); line = ch
            else:
                line += ch
        lines.append(line)
        out.append((lines, f, size)); tot += int(size * 1.6) * len(lines) + 14
    lay, g = card(w, tot + 20, title)
    yy = 100
    em = False
    for lines, f, size in out:
        for line in lines:
            xx = 60
            for i, p in enumerate(line.split("*")):
                if i: em = not em
                if p:
                    g.text((xx, yy), p, font=f, fill=(BLUE if em else INK) + (255,)); xx += f.getlength(p)
            yy += int(size * 1.6)
        yy += 14; em = False
    appear(base, lay, x, y, t, d)


def subtitle(base, t, text, total, start=0.08, y=985):
    """下の字幕(参考動画の出方:読点ごとのひとことがふわっと。*語* は青の選択枠)"""
    for k, v in sorted(DISP.items(), key=lambda kv: -len(kv[0])): text = text.replace(k, v)
    for k, v in sorted(sr.DISP.items(), key=lambda kv: -len(kv[0])): text = text.replace(k, v)
    ps = [x for x in re.split(r"(?<=[、。?])", text) if x.strip()]
    n = sum(len(p.replace("*", "")) for p in ps); acc, cur = start, None
    times = []
    for p in ps: times.append(acc); acc += total * len(p.replace("*", "")) / n
    now = max([i for i, s0 in enumerate(times) if s0 <= t] or [0])
    # 文(。)ごとに表示
    sent_start = now
    while sent_start > 0 and not ps[sent_start - 1].rstrip().endswith(("。", "?")): sent_start -= 1
    f = gr.jp(46)
    shown = ps[sent_start:now + 1]
    full = "".join(ps[sent_start:]).split("。")[0]
    xs = (W - f.getlength(full.replace("*", ""))) / 2 if f.getlength(full.replace("*", "")) < 1700 else 110
    x = xs
    em = False
    for j, p in enumerate(shown):
        lay = Image.new("RGBA", (W, 90), (0, 0, 0, 0)); g = ImageDraw.Draw(lay)
        px = x
        for i, a in enumerate(p.split("*")):
            if i: em = not em
            if not a: continue
            w = f.getlength(a)
            if em: sr.selbox(g, px - 6, 10, px + w + 6, 80, 5)
            g.text((px, 10), a, font=f, fill=INK + (255,)); px += w
        appear(base, lay, 0, y - 45, t, times[sent_start + j], dur=0.3, rise=10)
        x = px


def pause_tip(base, t, total, d=0.2, x=1090, y=420):
    """考える時間:一時停止の案内+3秒の円のカウントダウン"""
    if t < d: return
    g = ImageDraw.Draw(base)
    f = gr.jp(40)
    pw = int(f.getlength("考えたい人は、ここで一時停止")) + 150
    lay = Image.new("RGBA", (pw, 96), (0, 0, 0, 0)); q = ImageDraw.Draw(lay)
    q.rounded_rectangle([0, 0, pw - 1, 95], 48, fill=BLUE + (255,))
    q.ellipse([16, 14, 82, 80], fill=(255, 255, 255, 255))
    for x0 in (36, 54): q.rounded_rectangle([x0, 31, x0 + 10, 63], 3, fill=BLUE + (255,))
    q.text((104, 48), "考えたい人は、ここで一時停止", font=f, fill=(255, 255, 255, 255), anchor="lm")
    appear(base, lay, x, y, t, d, rise=0)
    # カウントダウンの円
    k = min(1, max(0, (t - d - 0.6) / max(0.1, total - d - 0.8)))
    cx, cy, r = x + pw / 2, y + 260, 90
    g.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(225, 225, 225), width=14)
    if k > 0: g.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * k, fill=BLUE, width=14)
    left = max(1, math.ceil((1 - k) * 3))
    g.text((cx, cy), str(left), font=gr.font("Anton-Regular.ttf", 90), fill=BLUE, anchor="mm")


def cta(base, t, deal=None):
    """案内(PR):目的別のおすすめは説明欄に。キャンペーンがあれば一言。ピルは文字の左右にたっぷり余白(窮屈に見せない)"""
    CW = 1500
    lay, g = card(CW, 500 if deal else 410)
    g.rounded_rectangle([70, 56, 160, 100], 12, fill=(150, 150, 150, 255))
    g.text((115, 78), "PR", font=gr.jp(28), fill=(255, 255, 255, 255), anchor="mm")
    g.text((CW / 2 + 20, 175), "目的別のおすすめ教材は 説明欄に", font=gr.jp(60), fill=INK + (255,), anchor="mm")
    fp = gr.jp(32, bold=False)
    labels = ["最短で結果を出したい", "自分のペースで解きたい", "スキマ時間に続けたい"]
    pw = [int(fp.getlength(s)) + 120 for s in labels]
    gap = 44
    xx = CW / 2 + 20 - (sum(pw) + gap * 2) / 2
    for s, w in zip(labels, pw):
        g.rounded_rectangle([xx, 262, xx + w, 346], 42, fill=(244, 247, 255, 255), outline=(150, 178, 240, 255), width=2)
        g.text((xx + w / 2, 304), s, font=fp, fill=BLUE + (255,), anchor="mm")
        xx += w + gap
    if deal:
        g.text((CW / 2 + 20, 430), deal, font=gr.jp(38), fill=(222, 76, 64, 255), anchor="mm")
    appear(base, lay, (W - CW - 40) / 2, 250, t, 0.1)
    # 説明欄を指す矢印(下へ)
    bob = 10 * math.sin(t * 6)
    gg = ImageDraw.Draw(base)
    gg.polygon([(W / 2 - 40, 840 + bob), (W / 2 + 40, 840 + bob), (W / 2, 900 + bob)], fill=BLUE)


def summary_card(base, t, rows, y=130):
    """まとめ:時を表す言葉 → 時制 → 例"""
    CW = 1500
    RH = 132 if len(rows) <= 4 else 118
    lay, g = card(CW, 130 + RH * len(rows), "まとめ:時を表す言葉で、時制が決まる")
    yy = 110
    for i, (words, tense, ex) in enumerate(rows):
        g.rounded_rectangle([60, yy, CW - 20, yy + RH - 14], 20, fill=(248, 250, 255, 255) if i % 2 == 0 else (255, 255, 255, 255))
        cy = yy + (RH - 14) / 2
        fw = gr.serif(44, 700)
        while fw.getlength(words) > 600: fw = gr.serif(fw.size - 2, 700)
        g.text((100, cy), words, font=fw, fill=BLUE + (255,), anchor="lm")
        g.text((740, cy), "→", font=gr.jp(44), fill=GRAY + (255,), anchor="mm")
        g.text((800, cy), tense, font=gr.jp(46), fill=INK + (255,), anchor="lm")
        g.text((1110, cy), ex, font=gr.serif(36, 500), fill=(120, 120, 120, 255), anchor="lm")
        yy += RH
    appear(base, lay, (W - CW - 40) / 2, y, t, 0.1)


# ---------- 1問の台本(英文法クイズの問題を使い、解説は書き下ろす) ----------
TEST = dict(
    no=101, voice="m",
    intro=("なんとなくで選んでない?", "*現在完了* と *過去形* の違い",
           "現在完了と過去形、*なんとなく*で選んでいませんか?この動画では、*時を表す言葉*から、時制を決めるコツを解説します。"),
    ja="私たちは2週間前に、新しい科学博物館を訪れました。",
    hl="two weeks ago",
    exp_rows=[("① *two weeks ago*(2週間前)は、はっきり過去の時を表す言葉", 37, True),
              ("② 現在完了は、過去のことを *今とつなげて* 話す形", 37, True),
              ("③ だから *ago・yesterday・last 〜* のような「過去の一点」とは一緒に使えない", 37, True),
              ("時制の問題は、まず *時を表す言葉* をさがそう", 34, False)],
    exp_say="ポイントは、*トゥー・ウィークス・アゴー*。はっきり*過去の時*を表す言葉です。現在完了は、過去のことを、*今とつなげて*話す形。だから、アゴーや、イエスタデイのように、*過去の一点*を表す言葉とは、一緒に使えません。時制の問題は、まず、*時を表す言葉*を、さがしましょう。",
)


def build_test():
    Q = next(x for x in json.loads((ROOT / "quizzes.json").read_text()) if x["no"] == TEST["no"])
    import yt_cta
    deal = yt_cta.deals().get("speak", "").split("(")[0]
    deal_line = f"スピークは、{deal}(11/22時点)" if deal else None
    S = []

    def scene(content, parts, default=2.0, outro=0.3):
        ds = [float(x) if k == "gap" else sr.dur(k, x) for k, x in parts]
        D = max(1.3, 0.08 + sum(x + 0.08 for x in ds) + 0.12) if parts else default
        subs, acc = [], 0.08
        for (k, x), dd in zip(parts, ds):
            if k == "ja": subs.append((acc, x, dd))
            acc += dd + 0.08

        def f(bb, t):
            def draw(b):
                content(b, t, D)
                for st, x, dd in subs:
                    if st <= t < st + dd + 0.5: subtitle(b, t, x, dd, start=st)
            ko = max(0.0, (t - (D - outro)) / outro)
            if ko <= 0: draw(bb); return
            k = gr.ease(ko); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); draw(lay)
            lay = lay.filter(ImageFilter.GaussianBlur(10 * k)); lay.putalpha(lay.split()[3].point(lambda v: int(v * (1 - k))))
            bb.alpha_composite(lay.crop((0, int(60 * k), W, H)), (0, 0))
        S.append((D, f, parts))

    l1, l2, say = TEST["intro"]
    scene(lambda b, t, D: (header(b, t, l1, l2, y=280, s1=64, s2=110),
                           step_pill(b, t, "英", "英文法・英検2級・TOEIC", x=(W - 560) / 2, y=600)), [("ja", say)])
    scene(lambda b, t, D: (step_pill(b, t, "Q1", "問題"), q_card(b, t, Q, "q", hl=TEST["hl"] if False else None),
                           pause_tip(b, t, D, d=1.6)),
          [("ja", "第1問。かっこに入るのは、どっち?"), ("gap", "3.2")])
    ans = Q["options"][Q["answer"] - 1]
    full = Q["question"].replace("( )", ans)
    scene(lambda b, t, D: (step_pill(b, t, "Q1", "正解"), q_card(b, t, Q, "a"),
                           right_card(b, t, "和訳", [(f"正解は *{'①②'[Q['answer'] - 1]} {ans}*", 46, True), (TEST["ja"], 36, False)])),
          [("ja", f"正解は、{Q['answer']}の、*{ans}*。"), (TEST["voice"], full), ("ja", "わたしたちは、2週間前に、新しい科学博物館を訪れました。")])
    scene(lambda b, t, D: (step_pill(b, t, "Q1", "解説"), q_card(b, t, Q, "a", hl=TEST["hl"]),
                           right_card(b, t, "なぜ?", TEST["exp_rows"])),
          [("ja", TEST["exp_say"])])
    cta_say = "時を表す言葉から時制を決める練習を、*もっとしたい人*は、*説明欄*を見てください。目的別に、おすすめを紹介しています。" + \
              ("いまスピークは、*お得なキャンペーン中*です。" if deal_line else "")
    scene(lambda b, t, D: cta(b, t, deal_line), [("ja", cta_say)])
    return S


def build(key):
    """本番:yt_explain_data.VIDEOS[key] から作る。返り値:(場面, チャプター)"""
    import yt_explain_data as yd
    import yt_cta
    DISP.update(yd.DISP)
    V = yd.VIDEOS[key]
    QS = {x["no"]: x for x in json.loads((ROOT / "quizzes.json").read_text())}
    deal = yt_cta.deals().get("speak", "").split("(")[0]
    deal_line = f"スピークは、{deal}(11/22時点)" if deal else None
    S, chapters = [], []

    def scene(content, parts, default=2.0, outro=0.3, chap=None):
        ds = [float(x) if k == "gap" else sr.dur(k, x) for k, x in parts]
        D = max(1.3, 0.08 + sum(x + 0.08 for x in ds) + 0.12) if parts else default
        subs, acc = [], 0.08
        for (k, x), dd in zip(parts, ds):
            if k == "ja": subs.append((acc, x, dd))
            acc += dd + 0.08
        if chap: chapters.append((sum(s0[0] for s0 in S), chap))

        def f(bb, t):
            def draw(b):
                content(b, t, D)
                for st, x, dd in subs:
                    if st <= t < st + dd + 0.5: subtitle(b, t, x, dd, start=st)
            ko = max(0.0, (t - (D - outro)) / outro)
            if ko <= 0: draw(bb); return
            k = gr.ease(ko); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); draw(lay)
            lay = lay.filter(ImageFilter.GaussianBlur(10 * k)); lay.putalpha(lay.split()[3].point(lambda v: int(v * (1 - k))))
            bb.alpha_composite(lay.crop((0, int(60 * k), W, H)), (0, 0))
        S.append((D, f, parts))

    l1, l2, say = V["intro"]
    scene(lambda b, t, D: (header(b, t, l1, l2, y=280, s1=64, s2=110),
                           step_pill(b, t, "英", "英文法・英検2級・TOEIC", x=(W - 560) / 2, y=600)), [("ja", say)], chap="はじめに")
    for i, q in enumerate(V["qs"], 1):
        Q = QS[q["no"]]
        voice = "m" if i % 2 == 1 else "f"  # 英文は男女を1問ごとに交互
        ans = Q["options"][Q["answer"] - 1]
        full = Q["question"].replace("( )", ans)
        rows = [(r, 37, True) for r in q["rows"]]
        scene(lambda b, t, D, Q=Q, i=i: (step_pill(b, t, f"Q{i}", "問題"), q_card(b, t, Q, "q"), pause_tip(b, t, D, d=1.6)),
              [("ja", f"第{i}問。かっこに入るのは、どっち?"), ("gap", "3.2")], chap=f"第{i}問 {q.get('chap', q['hl'])}")
        scene(lambda b, t, D, Q=Q, i=i, ans=ans, q=q: (step_pill(b, t, f"Q{i}", "正解"), q_card(b, t, Q, "a"),
              right_card(b, t, "和訳", [(f"正解は *{'①②'[Q['answer'] - 1]} {ans}*", 46, True), (Q["translation"], 36, False)])),
              [("ja", f"正解は、{Q['answer']}番。"), (voice, full), ("ja", q["ja_say"])])
        scene(lambda b, t, D, Q=Q, i=i, q=q, rows=rows: (step_pill(b, t, f"Q{i}", "解説"), q_card(b, t, Q, "a", hl=q["hl"]),
              right_card(b, t, "なぜ?", rows)), [("ja", q["say"])])
        if i == V.get("mid_after"):
            scene(lambda b, t, D: cta(b, t, None), [("ja", V["mid_say"])])
    scene(lambda b, t, D: summary_card(b, t, V["summary"]), [("ja", V["summary_say"])], chap="まとめ")
    scene(lambda b, t, D: cta(b, t, deal_line), [("ja", V["end_say"] + ("いまスピークは、*お得なキャンペーン中*です。" if deal_line else ""))],
          chap="おすすめ教材(PR)")
    return S, chapters, V


def write_txt(key, V, chapters, total):
    """タイトル2案・説明欄(サイト→内容→松竹梅+キャンペーン→チャプター→各問のサイト)・タグ・固定コメント・サムネ"""
    import yt_cta, yt_thumb
    stamp = lambda s: f"{int(s // 60)}:{int(s % 60):02d}"
    chap = "\n".join(f"{stamp(t)} {c}" for t, c in chapters)
    links = "\n".join(f"第{i}問 → https://eng-navi.github.io/q/{q['no']}/" for i, q in enumerate(V["qs"], 1))
    desc = (f"📚 全問の答え・くわしい解説と音声は、無料のサイトで復習できます👇\nhttps://eng-navi.github.io/?utm_source=youtube\n\n"
            f"{V['topic']}を、英検2級・TOEIC Part5 によく出る時制の問題{len(V['qs'])}問で解説します。"
            "ago・last・just・ever・since・for などの「時を表す言葉」に注目すると、英文法の時制の問題は迷わず解けます。"
            "英会話で時制を使い分けたい人、大人の英語の学び直しにも。\n"
            "1問ずつ「問題 → 考える時間 → 正解(英語の読み上げ)→ 解説」の順に進みます。\n\n"
            f"{yt_cta.shochikubai(V['book'], V['topic'], seed='yt_explain_' + key)}\n\n▼ チャプター\n{chap}\n\n"
            f"▼ 問題ごとのくわしい解説(サイト)\n{links}\n\n{gr.TRACKS[0]['credit']}\nPhoto: StockSnap (CC0)\n\n"
            "#英文法 #時制 #現在完了")
    tags = "英文法,時制,現在完了,過去形,現在完了と過去形の違い,英検2級,TOEIC,TOEIC Part5,英語学習,英会話,学び直し,since for 違い,have gone have been 違い,過去完了"
    txt = OUT / f"{key}.txt"
    txt.write_text(f"タイトル:\n{V['title']}\n\nタイトル案B(ずらし):\n{V['title_b']}\n\n説明欄:\n{desc}\n\n"
                   f"タグ(詳細設定の「タグ」にそのまま貼る):\n{tags}\n\n固定コメント(投稿後にコメントして「固定」):\n{yt_cta.pinned(V['topic'])}\n")
    yt_thumb.make(*V["thumb"], yt_thumb.PEOPLE[0], OUT / f"{key}_thumb.jpg")
    print(txt, f"{stamp(total)}")


def render(S, out):
    OUT.mkdir(parents=True, exist_ok=True)
    clips, acc = [], 0.0
    for D, f, parts in S:
        t = acc + 0.08
        for k, x in parts:
            if k == "gap": t += float(x) + 0.08; continue
            mp3, dd = gr.tts(k, x); clips.append((t, mp3)); t += dd + 0.08
        acc += D
    total = acc
    starts, a = [], 0.0
    for D, _, _ in S: starts.append(a); a += D
    tr = gr.TRACKS[0]
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-",
           "-stream_loop", "-1", "-i", str(ROOT / "assets" / "bgm" / tr["file"])]
    fc = f"[1:a]volume=0.07,afade=t=out:st={total - 1}:d=1[m];"; mix = "[m]"
    for i, (t0, mp3) in enumerate(clips):
        cmd += ["-i", str(mp3)]
        fc += f"[{2 + i}:a]loudnorm=I=-18:TP=-3:LRA=7,aresample=44100,adelay={int(t0 * 1000)}:all=1[v{i}];"; mix += f"[v{i}]"
    fc += f"{mix}amix=inputs={1 + len(clips)}:normalize=0,alimiter=limit=0.9[a]"
    cmd += ["-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-t", f"{total}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-c:a", "aac", "-b:a", "160k", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    base = bg()
    for fi in range(int(total * FPS)):
        tg = fi / FPS
        k = max(i for i, s0 in enumerate(starts) if s0 <= tg)
        fr = base.copy(); S[k][1](fr, tg - starts[k])
        fr.convert("RGB").save(p.stdin, "JPEG", quality=90)
    p.stdin.close(); p.wait()
    (out.with_suffix(".voice.json")).write_text(json.dumps(gr.MANIFEST, ensure_ascii=False, indent=1)); gr.MANIFEST.clear()
    print(out, f"{total:.1f}s")
    return out


if __name__ == "__main__":
    if sys.argv[1:2] == ["build"]:  # python3 yt_explain.py build tense1
        key = sys.argv[2]
        S, chapters, V = build(key)
        out = render(S, OUT / f"{key}.mp4")
        write_txt(key, V, chapters, sum(x[0] for x in S))
        r = subprocess.run([str(ROOT / ".venv-tts/bin/python"), str(ROOT / "yomi_check.py"), str(out.with_suffix(".voice.json")), "--quiet"],
                           capture_output=True, text=True).stdout.strip()
        print(r)
    if sys.argv[1:2] == ["test"]:
        out = render(build_test(), OUT / "test.mp4")
        r = subprocess.run([str(ROOT / ".venv-tts/bin/python"), str(ROOT / "yomi_check.py"), str(out.with_suffix(".voice.json")), "--quiet"],
                           capture_output=True, text=True).stdout.strip()
        print(r)
