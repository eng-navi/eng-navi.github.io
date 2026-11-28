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
sr.PILL_Y = 300  # TOEIC は英文が多いので、見出しと札を上に寄せて真ん中の枠を広く(2026-11-28)
TOP = 370        # カードの開始位置


def header(base, t, l1, l2, y=96):
    """小さめの見出し(1行目グレー → 2行目太字。*語* は青の選択枠)"""
    f1, f2 = gr.jp(42, bold=False), gr.jp(54)
    lay1 = Image.new("RGBA", (W, 64), (0, 0, 0, 0))
    ImageDraw.Draw(lay1).text((W / 2 + 30, 32), l1, font=f1, fill=GRAY + (255,), anchor="mm")
    sr.appear(base, lay1, 0, y, t, 0.0, rise=16)
    lay = Image.new("RGBA", (W, 100), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    segs = sr._segs(l2)
    x = (W + 60 - sum(f2.getlength(a) for a, _ in segs)) / 2
    for a, kw in segs:
        w = f2.getlength(a)
        if kw:
            sr.selbox(g, x - 10, 12, x + w + 10, 90, 6)
        g.text((x, 10), a, font=f2, fill=INK + (255,))
        x += w
    sr.appear(base, lay, 0, y + 62, t, 0.2, rise=16)


sr.DISP.update({"プロブレム": "problem", "バット": "but", "アーリアー・ザン・エクスペクテッド": "earlier than expected",
                "ビーが": "(B) が", "エーの": "(A) の", "エーが": "(A) が", "ビーの": "(B) の",
                "プリファード・バット・ノット・リクワイアード": "preferred but not required", "リクワイアメント": "requirement",
                "マスト": "must", "ホワイ": "Why", "アラウ": "allow", "レント": "rent"})


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
    h = int(size * 2.3)
    lay = Image.new("RGBA", (sr.CARD_W + 40, 2 * h + 60), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    for i, (en, _) in enumerate(chs):
        L = "AB"[i]
        on = (mark or {}).get(L)
        yy = 20 + i * (h + 16)
        g.rounded_rectangle([20, yy, sr.CARD_W + 20, yy + h], 16, fill=(LIGHT if on == "o" else (255, 255, 255)) + (255,),
                            outline=(BLUE if on == "o" else (226, 226, 226)) + (255,), width=3 if on == "o" else 2)
        g.text((48, yy + h / 2), f"({L})", font=fl, fill=BLUE + (255,), anchor="lm")
        col = (170, 170, 170) if on == "x" else INK
        tx = 48 + fl.getlength("(A)") + 22
        g.text((tx, yy + h / 2), en, font=f, fill=col + (255,), anchor="lm")
        if on == "x":
            g.line([(tx - 6, yy + h / 2 + 2), (tx + 6 + f.getlength(en), yy + h / 2 + 2)], fill=(222, 76, 64, 255), width=5)
    sr.appear(base, lay, sr.CARD_X - 20, y, t, d)
    return y + 2 * h + 60


def ja_card(base, t, ja, y, d=0.0, hl=None, dim=None, size=30):
    """和訳(❶❷❸ごと)。本文と同じ文を青字/薄く"""
    hl, dim = hl or {}, dim or set()
    f = gr.jp(size, bold=False)
    body = ja.split("\n", 1)[-1] if "❶" not in ja.split("\n", 1)[0] else ja
    parts = [(NUM.index(m) + 1, x.strip()) for m, x in re.findall(r"([❶❷❸❹])([^❶❷❸❹]+)", body)]
    parts = [(n, x.split("。")[0] + "。" if "。" in x else x) for n, x in parts]  # 番号のない後ろの段落(応募方法など)は出さない
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
    7: dict(
        key=("requirement", "必須条件"),
        steps=[
            dict(no="01", tag="設問", l1="設問のキーワードは", l2="*requirement*(必須条件)", kind="q",
                 say="設問のキーワードは、*リクワイアメント*。仕事の*必須条件*を聞いています。"),
            dict(no="02", tag="根拠", l1="must の文に", l2="*必須条件* がある", kind="p",
                 hl={2: "must have at least two years of experience"}, hl_ja={2: "接客の経験が2年以上必要"}, dim={1, 3},
                 say="2文目の*マスト*。接客の経験が、*2年以上必要*。マストは、必須条件のサインです。"),
            dict(no="03", tag="正解", l1="言いかえに注目", l2="*(A)* が正解", kind="o",
                 say="これを、*接客の経験*と言いかえた、エーが正解。"),
            dict(no="04", tag="ワナ", l1="(B) は", l2="*必須ではない*", kind="p",
                 hl={3: "preferred but not required"}, hl_ja={3: "必須ではありません"}, dim={1, 2},
                 say="ビーの、第二言語はワナ。*プリファード・バット・ノット・リクワイアード*は、あれば望ましいが、*必須ではない*、です。"),
        ],
        app=dict(P={"kind": "NOTICE", "head": ["Volunteer Guides Wanted — City Museum"],
                    "body": [[("Volunteers must be available on at least two weekends a month.", 1),
                              ("Experience in teaching is a plus but not necessary.", 2)]]},
                 q="What is required of volunteers?",
                 chs=[("Teaching experience", ""), ("Weekend availability", "")], ans="B"),
        caption="""求人広告の「必須条件」、どこを見る?🤔
must は必須、preferred は「あれば尚可」。TOEIC Part 7 の求人広告で必ず出るワナを1問で解説します。
解きたい人は一時停止してね⏸ 応用問題の答えはコメント欄に👇

#TOEIC #TOEIC対策 #Part7 #TOEICリーディング #ビジネス英語""",
        comment="""✅ 応用問題の正解は (B)

Volunteer Guides Wanted — City Museum
Volunteers must be available on at least two weekends a month. Experience in teaching is a plus but not necessary.
ボランティアガイド募集 — 市立博物館
ボランティアは、月に少なくとも2回の週末に参加できる必要があります。教えた経験があれば歓迎ですが、必須ではありません。

What is required of volunteers?(ボランティアに求められていることは何ですか)
(A) Teaching experience(教えた経験)
(B) Weekend availability(週末に参加できること)

━━ 解説 ━━
❶ must be available on 〜 weekends → 週末に参加できることが必須 → (B)。
(A) は ❷ で a plus but not necessary(あれば歓迎だが必須ではない)なので×。

must / required / necessary =「必須」、preferred / a plus / desirable =「あれば尚可」。設問が requirement / required なら must の文を探そう。

━━ 動画の問題の全文 ━━
Front Desk Coordinator — Lakeside Hotel
Lakeside Hotel is looking for a front desk coordinator to join our team in May. Applicants must have at least two years of experience in customer service. Knowledge of a second language is preferred but not required.
レイクサイド・ホテルでは、5月から一緒に働くフロント・コーディネーターを募集しています。応募者は、接客の経験が2年以上必要です。第二言語の知識があれば望ましいですが、必須ではありません。

📝 単語
applicant 応募者 / at least 少なくとも / preferred 望ましい / required 必須の / requirement 必要条件 / available 都合がつく / a plus 歓迎される点""",
    ),
    8: dict(
        key=("moving", "移転の理由"),
        steps=[
            dict(no="01", tag="設問", l1="設問は Why", l2="*移転の理由*", kind="q",
                 say="設問は、ホワイ。カフェが*移転する理由*を聞いています。"),
            dict(no="02", tag="根拠", l1="allow A to do は", l2="*理由* のサイン", kind="p",
                 hl={2: "allow the café to host cooking classes"}, hl_ja={2: "夜に料理教室を開けるようになる"}, dim={1, 3},
                 say="2文目の*アラウ*。新しい店では、*夜に料理教室*を開けるようになる。これが移転の理由です。"),
            dict(no="03", tag="正解", l1="言いかえに注目", l2="*(A)* が正解", kind="o",
                 say="これを、*夜に教室を開くため*と言いかえた、エーが正解。"),
            dict(no="04", tag="ワナ", l1="(B) の家賃は", l2="*本文にない*", kind="p", hl={}, dim=set(),
                 say="ビーの、家賃を下げるため、はワナ。*レント*は、本文のどこにもありません。*書いていないもの*は選ばない。"),
        ],
        app=dict(P={"kind": "E-MAIL", "head": ["To: All Staff   From: Facilities Team"],
                    "body": [[("The third-floor meeting room will be closed next week.", 1),
                              ("New screens are being installed so that teams can hold video meetings more easily.", 2)]]},
                 q="Why will the meeting room be closed?",
                 chs=[("To install new equipment", ""), ("To save electricity", "")], ans="A"),
        caption="""Why 問題の「理由」、どこにある?🤔
because だけじゃない。allow A to do も理由のサイン。書いていない「ありそうな理由」を選ばないのが TOEIC Part 7 の鉄則です。
解きたい人は一時停止してね⏸ 応用問題の答えはコメント欄に👇

#TOEIC #TOEIC勉強 #Part7 #英語学習 #TOEIC800点""",
        comment="""✅ 応用問題の正解は (A)

The third-floor meeting room will be closed next week. New screens are being installed so that teams can hold video meetings more easily.
3階の会議室は来週閉鎖されます。チームがもっと簡単にビデオ会議を開けるよう、新しいスクリーンを取り付けるためです。

Why will the meeting room be closed?(会議室はなぜ閉鎖されますか)
(A) To install new equipment(新しい機器を取り付けるため)
(B) To save electricity(電気を節約するため)

━━ 解説 ━━
❷ New screens are being installed(新しいスクリーンを取り付ける)→ new equipment と言いかえた (A)。
so that 〜(〜できるように)も理由・目的のサイン。
(B) の電気の節約は、本文に書かれていないので×。

━━ 動画の問題の全文 ━━
Greenleaf Café, which opened on Main Street ten years ago, will move to a larger location on River Road next month. Owner Maria Chen said the new space will allow the café to host cooking classes in the evenings. The current location will close on June 1, and the new café will open on June 15.
10年前にメイン通りで開店したグリーンリーフ・カフェが、来月リバー通りのより広い場所へ移転する。オーナーのマリア・チェン氏によると、新しい店舗では夜に料理教室を開けるようになるという。現在の店舗は6月1日に閉店し、新しいカフェは6月15日にオープンする。

📝 単語
location 場所、店舗 / allow A to do Aが〜できるようにする / host 開く、主催する / current 現在の / install 取り付ける / equipment 機器 / so that 〜できるように""",
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
        header(bb, t, "TOEIC Part 7、", "*解ける?*")
        y = passage(bb, t, P, TOP, d=0.1, size=38)
        y = question(bb, t, Q["q"], y - 20, d=0.2, size=40)
        y = choices(bb, t, chs, y - 34, d=0.3, size=40)
        pause_tip(bb, t, y + 40, d=0.6)
    # 本文は読み上げない(16秒の待ち時間で離脱されるため。解きたい人は一時停止する)。設問だけ英語で読んで、次の「設問のキーワード」へつなぐ
    sr.scene(S, problem, [("ja", "どっちが正解?解くなら、ここで止めてね。")], ("00", "問題"))  # 英文の読み上げはしない(2026-11-28)
    for st in sc["steps"]:
        def content(bb, t, st=st):
            header(bb, t, st["l1"], st["l2"])
            if st["kind"] == "q":
                question(bb, t, Q["q"], TOP + 80, key=sc["key"][0], size=56)
            elif st["kind"] == "p":
                y = passage(bb, t, P, TOP - 10, hl=st["hl"], dim=st["dim"], size=38)
                ja_card(bb, t, Q["ja"], y - 28, d=0.25, hl=st.get("hl_ja"), dim=st["dim"], size=29)
            else:
                choices(bb, t, chs, TOP + 80, mark={ansL: "o", ("A" if ansL == "B" else "B"): "x"}, size=44)
            sr.subtitle(bb, t, st["say"], sr.dur("ja", st["say"]), y=1570)
        sr.scene(S, content, [("ja", st["say"])], (st["no"], st["tag"]))
    ap = sc["app"]
    def app(bb, t):
        header(bb, t, "同じ発想で、", "*解ける?*")
        y = passage(bb, t, ap["P"], TOP, d=0.1, size=40)
        y = question(bb, t, ap["q"], y - 20, d=0.2, size=42)
        y = choices(bb, t, ap["chs"], y - 34, d=0.3, size=42)
        sr.cta(bb, t, d=0.8, y=y + 60)
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


def add(no, at):
    """docs/reels に公開して reel_schedule.json へ(CI の reel_post.py run toeic が投稿)。カバーは問題の画面"""
    import eiken_easy
    eiken_easy.add_reel("toeic", int(no), at, OUT / f"toeic_{int(no):03d}.mp4", SCRIPTS[int(no)])


if __name__ == "__main__":
    if sys.argv[1:2] == ["add"]:  # python3 toeic_easy.py add 6 "2026-11-28 20:00"
        add(sys.argv[2], sys.argv[3])
    else:
        for a in sys.argv[1:] or ["6"]:
            render(int(a))
