"""TOEIC読解(@toeic_read30)のリール(新形式・テスト)。
流れは英検の新形式(eiken_easy.py)と同じ、見た目・声は「差がつく英文読解」(seidoku_reel.py)をそのまま使う。

    python3 toeic_easy.py 6        # → out/toeic_easy/toeic_006.mp4(作成+読みチェック)

流れ:問題(本文+設問+(A)(B))→ 約2秒で「解くなら、ここで止めてね」→ 設問のキーワード → 根拠 → 正解(言いかえ)→ ワナ → 応用問題(答えはコメント)。
"""
import re
import subprocess
import sys
import types
from pathlib import Path

from PIL import Image, ImageDraw

import seidoku_reel as sr  # 見た目・声・字幕・切り替えはこちら(import で grammar_reel の声と背景が seidoku 用になる)
import grammar_reel as gr

ROOT = Path(__file__).parent
OUT = ROOT / "out" / "toeic_easy"
W = gr.W
BLUE, INK, GRAY = sr.BLUE, sr.INK, sr.GRAY
LIGHT = (232, 239, 255)
NUM = "❶❷❸❹"
sr.DISP.update({"プロブレム": "problem", "バット": "but", "アーリアー・ザン・エクスペクテッド": "earlier than expected",
                "ビーが": "(B) が", "エーの": "(A) の"})


def _wrap(text, f, maxw):
    out, cur = [], ""
    for w in text.split(" "):
        if f.getlength((cur + " " + w).strip()) > maxw and cur:
            out.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    return out + [cur]


def passage(base, t, P, y, d=0.0, hl=None, dim=None, size=36):
    """本文カード(左上に文書の種類)。hl={文番号: 語句} は青字+うすい青の地、dim の文は薄く"""
    hl, dim = hl or {}, dim or set()
    f, fn, fh = gr.serif(size, 600), gr.jp(size - 6), gr.serif(size - 8, 500)
    maxw = sr.CARD_W - 130
    rows = [("h", x, 0, None) for x in P.get("head", [])]
    for text, n in P["body"][0]:
        ph = hl.get(n)
        hs = text.index(ph) if ph and ph in text else -1
        off = 0
        for i, line in enumerate(_wrap(text, f, maxw)):
            st = text.index(line, off); off = st + len(line)
            rng = (max(hs, st) - st, min(hs + len(ph), off) - st) if hs >= 0 and hs < off and hs + len(ph) > st else None
            rows.append(("s", line, n, rng, i == 0))
    lh = int(size * 1.5)
    hgt = 96 + sum(lh if r[0] == "s" else int(lh * 0.8) for r in rows) + 24
    lay, g = sr._card(sr.CARD_W, hgt, P["kind"])
    yy = 92
    prev = None
    for r in rows:
        if r[0] == "h":
            x = 64
            for part in re.split(r"([★☆]+)", r[1]):  # ★ は英字フォントにないので日本語フォントで
                ff = gr.jp(size - 10) if part and part[0] in "★☆" else fh
                g.text((x, yy + (2 if ff is not fh else 0)), part, font=ff, fill=(130, 130, 130, 255)); x += ff.getlength(part)
            yy += int(lh * 0.8); continue
        _, line, n, rng, first = r
        if prev is not None and n != prev: yy += 8
        col = (195, 195, 195) if n in dim else INK
        if first:
            g.text((62, yy + 4), NUM[n - 1], font=fn, fill=(BLUE if n not in dim else col) + (255,))
        x = 110
        if rng:
            x0, x1 = x + f.getlength(line[:rng[0]]), x + f.getlength(line[:rng[1]])
            g.rectangle([x0 - 4, yy + 4, x1 + 4, yy + lh - 6], fill=LIGHT + (255,))
        if rng:
            a, b = rng
            for seg, c in ((line[:a], col), (line[a:b], BLUE), (line[b:], col)):
                g.text((x, yy), seg, font=f, fill=c + (255,)); x += f.getlength(seg)
        else:
            g.text((x, yy), line, font=f, fill=col + (255,))
        yy += lh; prev = n
    sr.appear(base, lay, sr.CARD_X - 20, y, t, d)
    return y + hgt + 40


def question(base, t, q, y, d=0.0, key=None, size=38):
    """設問カード。key の語は青字+下線"""
    f = gr.serif(size, 700)
    lines = _wrap(q, f, sr.CARD_W - 110)
    lh = int(size * 1.45)
    lay, g = sr._card(sr.CARD_W, 92 + lh * len(lines) + 10, "設問")
    yy = 90
    for line in lines:
        x = 64
        for part in re.split(f"({re.escape(key)})" if key else "(?!)", line):
            on = key and part == key
            g.text((x, yy), part, font=f, fill=(BLUE if on else INK) + (255,))
            if on:
                g.line([(x, yy + size * 1.25), (x + f.getlength(part), yy + size * 1.25)], fill=BLUE + (255,), width=4)
            x += f.getlength(part)
        yy += lh
    sr.appear(base, lay, sr.CARD_X - 20, y, t, d)
    return y + 92 + lh * len(lines) + 10 + 40


def choices(base, t, chs, y, d=0.0, mark=None, size=36):
    """(A)(B) の選択肢。mark={"A": "o"/"x"}"""
    f, fl = gr.serif(size, 600), gr.serif(size, 700)
    h = 84
    lay = Image.new("RGBA", (sr.CARD_W + 40, 2 * h + 60), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    for i, (en, _) in enumerate(chs):
        L = "AB"[i]
        on = (mark or {}).get(L)
        yy = 20 + i * (h + 16)
        g.rounded_rectangle([20, yy, sr.CARD_W + 20, yy + h], 16, fill=(LIGHT if on == "o" else (255, 255, 255)) + (255,),
                            outline=(BLUE if on == "o" else (226, 226, 226)) + (255,), width=3 if on == "o" else 2)
        g.text((48, yy + 18), f"({L})", font=fl, fill=BLUE + (255,))
        col = (170, 170, 170) if on == "x" else INK
        g.text((130, yy + 18), en, font=f, fill=col + (255,))
        if on == "x":
            g.line([(124, yy + h / 2 + 2), (136 + f.getlength(en), yy + h / 2 + 2)], fill=(222, 76, 64, 255), width=5)
        if on == "o":
            g.rounded_rectangle([sr.CARD_W - 110, yy + 20, sr.CARD_W, yy + h - 20], 22, fill=BLUE + (255,))
            g.text((sr.CARD_W - 55, yy + h / 2), "正解", font=gr.jp(26), fill=(255, 255, 255, 255), anchor="mm")
    sr.appear(base, lay, sr.CARD_X - 20, y, t, d)
    return y + 2 * h + 60


def ja_card(base, t, ja, y, d=0.0, hl=None, dim=None, size=30):
    """和訳(❶❷❸ごと)。本文と同じ文を青字/薄く"""
    hl, dim = hl or {}, dim or set()
    f = gr.jp(size, bold=False)
    body = ja.split("\n", 1)[-1] if "❶" not in ja.split("\n", 1)[0] else ja
    parts = [(NUM.index(m) + 1, x.strip()) for m, x in re.findall(r"([❶❷❸❹])([^❶❷❸❹]+)", body)]
    maxw, lh = sr.CARD_W - 130, int(size * 1.6)
    rows = []
    for n, x in parts:
        line = ""
        for ch in x:
            if f.getlength(line + ch) > maxw and ch not in "、。」)":
                rows.append((n, line)); line = ch
            else:
                line += ch
        rows.append((n, line))
    lay, g = sr._card(sr.CARD_W, 92 + lh * len(rows) + 8 * len(parts) + 10, "和訳")
    yy, prev = 90, None
    for n, line in rows:
        if prev is not None and n != prev: yy += 8
        col = (195, 195, 195) if n in dim else INK
        if n != prev:
            g.text((62, yy + 2), NUM[n - 1], font=gr.jp(size - 2), fill=(BLUE if n not in dim else col) + (255,))
        ph = hl.get(n)
        x = 110
        if ph and ph in line:
            a = line.index(ph)
            for seg, c in ((line[:a], col), (ph, BLUE), (line[a + len(ph):], col)):
                g.text((x, yy), seg, font=f, fill=c + (255,)); x += f.getlength(seg)
        else:
            g.text((x, yy), line, font=f, fill=col + (255,))
        yy += lh; prev = n
    sr.appear(base, lay, sr.CARD_X - 20, y, t, d)


def pause_tip(base, t, y, d=0.6):
    """「解きたい人は、ここで一時停止」:青いピル+白い一時停止アイコン(ゆっくり脈打つ)"""
    if t < d: return
    import math
    f = gr.jp(38)
    s = "解きたい人は、ここで一時停止"
    w, h = int(f.getlength(s)) + 150, 84
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    g.rounded_rectangle([0, 0, w - 1, h - 1], h // 2, fill=BLUE + (255,))
    g.ellipse([14, 12, 74, 72], fill=(255, 255, 255, 255))
    for x0 in (32, 48):
        g.rounded_rectangle([x0, 28, x0 + 9, 56], 3, fill=BLUE + (255,))
    g.text((96, h / 2), s, font=f, fill=(255, 255, 255, 255), anchor="lm")
    k = gr.back((t - d) / 0.3) * (1 + 0.04 * math.sin((t - d) * 6))
    gr.paste_rot(base, lay, sr.CARD_X + sr.CARD_W / 2, y, 0, scale=max(0.01, k))


# ---------- 台本(1問ずつ書く。応用問題の答えは「同じ発想」でちがう場面) ----------
SCRIPTS = {
    6: dict(
        key=("problem", "問題点"),
        steps=[
            dict(no="01", tag="設問", l1="設問のキーワードは", l2="*problem*(問題点)", kind="q",
                 say="設問のキーワードは、*プロブレム*。レビューを書いた人の、*問題点*を聞いています。"),
            dict(no="02", tag="根拠", l1="but のあとに", l2="*不満* が書いてある", kind="p",
                 hl={2: "the instructions were only in French"}, hl_ja={2: "説明書がフランス語だけ"}, dim={1, 3},
                 say="2文目の*バット*のあと。説明書が*フランス語だけ*で、組み立てに時間がかかった。これが問題点です。"),
            dict(no="03", tag="正解", l1="言いかえに注目", l2="*(B)* が正解", kind="o",
                 say="これを、*使いにくい*と言いかえた、ビーが正解。"),
            dict(no="04", tag="ワナ", l1="(A) は逆", l2="*早く* 届いている", kind="p",
                 hl={1: "two days earlier than expected"}, hl_ja={1: "予定より2日早く届きました"}, dim={2, 3},
                 say="エーの、配達が遅れた、はワナ。*アーリアー・ザン・エクスペクテッド*は、予定より*早く*、です。"),
        ],
        app=dict(P={"kind": "CUSTOMER REVIEW", "head": ["★★★☆☆  Reviewed by Mia T."],
                    "body": [[("The hotel staff were friendly, and my room was cleaner than I expected.", 1),
                              ("Unfortunately, the Wi-Fi stopped working every evening, so I could not finish my work.", 2)]]},
                 q="What problem did the guest have?",
                 chs=[("The room was dirty.", ""), ("The Internet connection was unreliable.", "")], ans="B"),
        caption="""TOEIC Part 7、レビューの「問題点」はどこに書いてある?🤔
設問の problem を見たら but / unfortunately のあとを探す。言いかえと earlier / later のワナまで、TOEICリーディングの解き方を1問で。
解きたい人は一時停止してね⏸ 応用問題の答えはコメント欄に👇

#TOEIC #TOEICリーディング #Part7 #TOEIC勉強 #英語学習""",
        comment="""✅ 応用問題の正解は (B)

The hotel staff were friendly, and my room was cleaner than I expected. Unfortunately, the Wi-Fi stopped working every evening, so I could not finish my work.
ホテルのスタッフは親切で、部屋も思ったよりきれいだった。残念ながら、Wi-Fiが毎晩止まってしまい、仕事を終えられなかった。

What problem did the guest have?(この客にはどんな問題がありましたか)
(A) The room was dirty.(部屋が汚かった)
(B) The Internet connection was unreliable.(ネット接続が不安定だった)

━━ 解説 ━━
problem(問題点)を聞かれたら、but / however / unfortunately のあとを探す。
❷ Unfortunately のあと「Wi-Fiが毎晩止まった」→ unreliable(当てにならない)と言いかえた (B)。
(A) は ❶ の cleaner than I expected(思ったよりきれい)と逆なので×。

━━ 動画の問題の全文 ━━
I ordered a desk lamp from Brightway Home, and it arrived two days earlier than expected. The lamp itself works well, but the instructions were only in French, so assembly took longer than I had hoped. Customer service quickly e-mailed me an English version.
ブライトウェイ・ホームでデスクライトを注文したら、予定より2日早く届きました。ライト自体はよく使えますが、説明書がフランス語だけだったので、組み立てに思ったより時間がかかりました。カスタマーサービスが、すぐに英語版をメールで送ってくれました。

📝 単語
than expected 予想より / instructions 説明書 / assembly 組み立て / unfortunately 残念ながら / unreliable 当てにならない / connection 接続""",
    ),
}


def build(L):
    import toeic_problems as tp
    Q = next(q for q in tp.PROBLEMS if q["no"] == L["no"])
    sc = SCRIPTS[L["no"]]
    P, chs = Q["passage"], Q["choices"]
    ansL = Q["answer"].strip("()")
    S = []
    # 0〜約2.5秒:問題 → 「止めてね」→ すぐ解説へ
    def problem(bb, t):
        sr.headline(bb, t, "TOEIC Part 7、", "*解ける?*")
        y = passage(bb, t, P, 640, d=0.1, size=34)
        y = question(bb, t, Q["q"], y - 16, d=0.2, size=34)
        y = choices(bb, t, chs, y - 34, d=0.3, size=34)
        pause_tip(bb, t, y + 40, d=0.6)
    sr.scene(S, problem, [("ja", "どっちが正解?解くなら、ここで止めてね。")], ("00", "問題"))
    for st in sc["steps"]:
        def content(bb, t, st=st):
            sr.headline(bb, t, st["l1"], st["l2"])
            if st["kind"] == "q":
                question(bb, t, Q["q"], 650, key=sc["key"][0], size=44)
            elif st["kind"] == "p":
                y = passage(bb, t, P, 600, hl=st["hl"], dim=st["dim"], size=30)
                ja_card(bb, t, Q["ja"], y - 20, d=0.25, hl=st.get("hl_ja"), dim=st["dim"], size=26)
            else:
                choices(bb, t, chs, 650, mark={ansL: "o", ("A" if ansL == "B" else "B"): "x"})
            sr.subtitle(bb, t, st["say"], sr.dur("ja", st["say"]), y=1570)
        sr.scene(S, content, [("ja", st["say"])], (st["no"], st["tag"]))
    ap = sc["app"]
    def app(bb, t):
        sr.headline(bb, t, "同じ発想で、", "*解ける?*")
        y = passage(bb, t, ap["P"], 640, d=0.1, size=34)
        y = question(bb, t, ap["q"], y - 16, d=0.2, size=34)
        choices(bb, t, ap["chs"], y - 34, d=0.3, size=34)
        sr.cta(bb, t, d=0.8, y=1480)
    sr.scene(S, app, [("ja", "最後に*応用問題*。同じ発想で、*解けるかな?*")], ("Q", "応用問題"))
    return "seidoku", S


def render(no):
    sys.modules["grammar_lessons"] = types.SimpleNamespace(LESSONS=[{"no": no}])
    gr.lesson = build
    OUT.mkdir(parents=True, exist_ok=True)
    out, _ = gr.render(0, no, OUT / f"toeic_{no:03d}.mp4")
    r = subprocess.run([str(ROOT / ".venv-tts/bin/python"), str(ROOT / "yomi_check.py"), str(out.with_suffix(".voice.json")), "--quiet"],
                       capture_output=True, text=True).stdout.strip()
    print(r)
    return out


if __name__ == "__main__":
    for a in sys.argv[1:] or ["6"]:
        render(int(a))
