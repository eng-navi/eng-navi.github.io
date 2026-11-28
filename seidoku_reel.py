"""@seidoku.lab「差がつく英文読解」のリール。grammar_reel.py の書き出し(声・BGM・効果音)を使う。

    python3 seidoku_reel.py 1        # → out/seidoku/seidoku_001.mp4
    .venv-tts/bin/python yomi_check.py out/seidoku/seidoku_001.voice.json

デザイン(2026-11-28 ユーザー指定・参考動画の雰囲気):白い方眼の背景、上にグレー+太字黒の見出し(キーワードは青の選択枠)、
左に青の縦線と「01 主語」のステップ札、白いカード。英文は黒字で、ポイントは青字+下線+札。
流れ:冒頭タイトル → 難しい1文(英文の読み上げは1回だけ)→ 分解 → 和訳 → 和訳クイズ(答えはコメント)。
英文はすべてオリジナル。本は「構文パターン」の参考だけ(本の英文・訳・場面は使わない)。
"""
import sys
import types
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

import grammar_reel as gr

ROOT = Path(__file__).parent
OUT = ROOT / "out" / "seidoku"
W, H = gr.W, gr.H

BLUE = (46, 98, 232)
INK = (24, 24, 24)
GRAY = (125, 125, 125)
gr.THEMES["seidoku"] = dict(bg=(247, 247, 245), big=INK, sub=INK, accent=BLUE, tape=BLUE, ink=(255, 255, 255))
# 声(2026-11-28 聞き比べで決定):日本語=Otani(男性・eleven_v3)、英文=アメリカ英語の若い男女 Liam / Jessica(v2)
gr.VOICE.update({"ja": "3JDquces8E8bkmvbh6Bc", "m": "TX3LPaxmHKxFdv7VOQHJ", "f": "cgSgspJ2msm6clMCkdW9"})
gr.SPEED.update({"m": 0.92, "f": 0.92})

LINE_X, PILL_Y = 96, 560


def background(theme):
    im = Image.new("RGB", (W, H), (247, 247, 245))
    d = ImageDraw.Draw(im)
    for x in range(0, W, 72):
        d.line([(x, 0), (x, H)], fill=(230, 230, 228), width=2)
    for y in range(0, H, 72):
        d.line([(0, y), (W, y)], fill=(230, 230, 228), width=2)
    return im


gr.background = background


# ---------- 部品 ----------
def appear(base, lay, x, y, t, d=0.0, dur=0.35, rise=40, dx=0):
    """ぼかしからふわっと出す(参考動画の切り替え)。x, y は左上"""
    if t < d: return
    k = gr.ease((t - d) / dur)
    if k < 1:
        lay = lay.filter(ImageFilter.GaussianBlur((1 - k) * 10))
        a = lay.split()[3].point(lambda v: int(v * k))
        lay.putalpha(a)
    base.alpha_composite(lay, (int(x + (1 - k) * dx), int(y + (1 - k) * rise)))


def _segs(s):
    parts = s.split("*")
    return [(x, i % 2 == 1) for i, x in enumerate(parts) if x]


def headline(base, t, l1, l2, y=250, d=0.0):
    """1行目:グレー、2行目:太字の黒(0.25秒おくれて出る)。2行目の *語* は青の選択枠(角に小さな四角)"""
    f1, f2 = gr.jp(58, bold=False), gr.jp(70)
    if l1:
        lay1 = Image.new("RGBA", (W, 90), (0, 0, 0, 0))
        ImageDraw.Draw(lay1).text(((W - gr.text_w(f1, l1)) / 2, 0), l1, font=f1, fill=GRAY + (255,))
        appear(base, lay1, 0, y, t, d, rise=20)
    lay = Image.new("RGBA", (W, 130), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    segs = _segs(l2)
    tw = sum(gr.text_w(f2, s) for s, _ in segs)
    x, yy = (W - tw) / 2, 10
    for s, kw in segs:
        w = gr.text_w(f2, s)
        if kw:
            selbox(g, x - 12, yy + 4, x + w + 12, yy + 104, 7)
        g.text((x, yy), s, font=f2, fill=INK + (255,))
        x += w
    appear(base, lay, 0, y + (86 if l1 else 30), t, d + (0.25 if l1 else 0), rise=20)


def selbox(g, x0, y0, x1, y1, c=7):
    """参考動画の「選択枠」:うすい青の地+青い枠+角の小さな白い四角"""
    g.rectangle([x0, y0, x1, y1], fill=(232, 239, 255, 255), outline=BLUE + (255,), width=3)
    for cx, cy in [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]:
        g.rectangle([cx - c, cy - c, cx + c, cy + c], fill=(255, 255, 255, 255), outline=BLUE + (255,), width=3)


def rail(base, t, no, label, d=0.0, k_out=0.0):
    """左の縦線(上が青)と、丸の「読」+ステップ札「01 That」。文字はすべて中央そろえ(anchor="mm")で余白をとる"""
    g = ImageDraw.Draw(base)
    g.line([(LINE_X, 0), (LINE_X, H)], fill=(222, 222, 218), width=8)
    py = PILL_Y + 420 * k_out  # 切り替えで丸が下りる → 次の画面でまた上から
    g.line([(LINE_X, 0), (LINE_X, py)], fill=BLUE, width=8)
    r = 42
    g.ellipse([LINE_X - r - 6, py - r - 6, LINE_X + r + 6, py + r + 6], fill=(255, 255, 255))
    g.ellipse([LINE_X - r, py - r, LINE_X + r, py + r], fill=BLUE)
    g.text((LINE_X, py), "読", font=gr.jp(38), fill=(255, 255, 255), anchor="mm")
    if k_out > 0:
        return
    fn, fl = gr.jp(28), gr.jp(36)
    h, pad = 76, 14
    nb = max(56, gr.text_w(fn, no) + 28)
    w = pad + nb + 20 + gr.text_w(fl, label) + 34
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    q = ImageDraw.Draw(lay)
    q.rounded_rectangle([0, 0, w - 1, h - 1], h // 2, fill=BLUE + (255,))
    q.rounded_rectangle([pad, 14, pad + nb, h - 14], 12, fill=(108, 148, 242, 255))
    q.text((pad + nb / 2, h / 2), no, font=fn, fill=(255, 255, 255, 255), anchor="mm")
    q.text((pad + nb + 20, h / 2), label, font=fl, fill=(255, 255, 255, 255), anchor="lm")
    appear(base, lay, LINE_X + r + 22, PILL_Y - h / 2, t, d, rise=0, dx=-30)


def _card(w, h, title):
    lay = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", lay.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([20, 26, w + 20, h + 26], 22, fill=(0, 0, 0, 34))
    lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    g = ImageDraw.Draw(lay)
    g.rounded_rectangle([20, 20, w + 20, h + 20], 22, fill=(255, 255, 255, 255), outline=(232, 232, 232, 255), width=2)
    if title:
        g.text((56, 42), title, font=gr.jp(30), fill=(150, 150, 150, 255))
    return lay, g


CARD_X, CARD_W = 150, 890
LABEL = {"S": "S", "V": "V", "C": "C", "O": "O", "M": "M"}


ORANGE = (22, 163, 148)  # カタマリの括弧の色:ミント(2026-11-28 4案からユーザーが選択)
BRACKETS = "()[]"


def sentence_card(base, t, lines, show, labels=None, y=650, d=0.1, title="英文", size=52):
    """英文は黒字。show の tag は青字+下線、下に青い札(tag ごとに最初の1回)。
    括弧 ( ) [ ] はその tag が show に入ったときだけオレンジで出す(最初の画面は問題文と同じく括弧なし)。
    tag "M" は括弧だけ(青字・札なし)。"""
    labels = {**LABEL, **(labels or {})}

    def vis(s, tag):
        return s if tag in show else "".join(c for c in s if c not in BRACKETS)

    while max(gr.text_w(gr.serif(size, 600), "".join(vis(s, tg) for s, tg in segs)) for segs in lines) > CARD_W - 90: size -= 2
    f, lf = gr.serif(size, 600), gr.jp(26)
    gap = int(size * 2.45)
    lay, g = _card(CARD_W, 100 + gap * len(lines), title)
    done, yy = set(), 104
    for segs in lines:
        x = 64
        for s, tag in segs:
            s = vis(s, tag)
            w = gr.text_w(f, s)
            on = tag in show and tag != "M"
            cx = x
            for ch in s:
                br = ch in BRACKETS
                g.text((cx, yy), ch, font=f, fill=(ORANGE if br else BLUE if on else INK) + (255,),
                       stroke_width=1 if br else 0, stroke_fill=(ORANGE + (255,)) if br else None)
                cx += f.getlength(ch)
            w = cx - x
            if on:
                lead = f.getlength(s[:len(s) - len(s.lstrip())])
                g.line([(x + lead, yy + size * 1.32), (x + w, yy + size * 1.32)], fill=BLUE + (255,), width=4)
                if tag not in done:
                    done.add(tag)
                    lab = labels.get(tag, tag)
                    lw, lh = gr.text_w(lf, lab) + 36, 44
                    lx, ly = x + lead + (w - lead) / 2 - lw / 2, yy + size * 1.5
                    g.rounded_rectangle([lx, ly, lx + lw, ly + lh], lh // 2, fill=BLUE + (255,))
                    g.text((lx + lw / 2, ly + lh / 2), lab, font=lf, fill=(255, 255, 255, 255), anchor="mm")
            x += w
        yy += gap
    appear(base, lay, CARD_X - 20, y, t, d)


def text_card(base, t, rows, y=650, d=0.1, title="和訳", size=46):
    """日本語のカード。*語* は青字"""
    f = gr.jp(size)
    lay, g = _card(CARD_W, 100 + int(size * 1.7) * len(rows), title)
    yy = 104
    for r in rows:
        x = 64
        for s, kw in _segs(r):
            g.text((x, yy), s, font=f, fill=(BLUE if kw else INK) + (255,))
            x += gr.text_w(f, s)
        yy += int(size * 1.7)
    appear(base, lay, CARD_X - 20, y, t, d)


def quiz_card(base, t, en, chs, y=640, d=0.1):
    fe, fj, fn = gr.serif(46, 600), gr.jp(36, bold=False), gr.jp(44)
    h = 100 + 70 * len(en) + 30 + sum(34 + 54 * len(c) + 20 for c in chs)
    lay, g = _card(CARD_W, h, "英文")
    yy = 104
    for r in en:
        g.text((64, yy), r, font=fe, fill=INK + (255,)); yy += 70
    yy += 30
    for i, c in enumerate(chs):
        hh = 34 + 54 * len(c)
        g.rounded_rectangle([50, yy, CARD_W - 10, yy + hh], 16, fill=(244, 247, 255, 255), outline=(214, 225, 252, 255), width=2)
        g.text((76, yy + 12), str(i + 1), font=fn, fill=BLUE + (255,))
        for j, line in enumerate(c):
            g.text((140, yy + 16 + 54 * j), line, font=fj, fill=INK + (255,))
        yy += hh + 20
    appear(base, lay, CARD_X - 20, y, t, d)


def cta(base, t, d=0.9, y=1420):
    """答えはコメント欄に →(右のコメントボタンを指す)"""
    if t < d: return
    f = gr.jp(40)
    s = "答えと解説はコメント欄に"
    w = gr.text_w(f, s) + 70
    lay = Image.new("RGBA", (w, 84), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    g.rounded_rectangle([0, 0, w - 1, 83], 42, fill=BLUE + (255,))
    g.text((35, 14), s, font=f, fill=(255, 255, 255, 255))
    appear(base, lay, 900 - w, y - 42, t, d, rise=0)
    import math
    ax = 915 + 12 * math.sin((t - d) * 7)
    gg = ImageDraw.Draw(base)
    gg.line([(ax, y), (ax + 50, y)], fill=BLUE, width=10)
    gg.polygon([(ax + 74, y), (ax + 44, y - 24), (ax + 44, y + 24)], fill=BLUE)


def hook(base, t, l1, l2):
    f1, f2 = gr.jp(76, bold=False), gr.jp(110)
    lay = Image.new("RGBA", (W, 400), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    g.text(((W - gr.text_w(f1, l1)) / 2, 20), l1, font=f1, fill=GRAY + (255,))
    w = gr.text_w(f2, l2)
    x, yy = (W - w) / 2, 150
    g.rectangle([x - 18, yy + 6, x + w + 18, yy + 160], fill=(232, 239, 255, 255), outline=BLUE + (255,), width=4)
    for cx, cy in [(x - 18, yy + 6), (x + w + 18, yy + 6), (x - 18, yy + 160), (x + w + 18, yy + 160)]:
        g.rectangle([cx - 9, cy - 9, cx + 9, cy + 9], fill=(255, 255, 255, 255), outline=BLUE + (255,), width=4)
    g.text((x, yy), l2, font=f2, fill=INK + (255,))
    appear(base, lay, 0, 700, t, 0.0, dur=0.4)


# ---------- 台本 ----------
LESSONS = [
    dict(no=1, theme="長いS+接続詞の like",
         hook=("この長い主語、", "見抜ける?"),
         en="That young children ask endless questions is entirely healthy, much like scientists test ideas they cannot yet explain.",
         lines=[[("(That young children ask endless", "S")],
                [("questions)", "S"), (" is", "V"), (" entirely healthy,", "C")],
                [("[much ", "M"), ("like", "L"), (" scientists test ideas", "M")],
                [("they cannot yet explain].", "M")]],
         labels={"S": "S(長い主語)", "L": "接続詞"},
         steps=[
             ("01", "That", "That のうしろに SV。", "*長い主語* のはじまり", {"S"},
              "まず、ザットのうしろに、*主語と動詞*が続いています。だからこのザットは、*「ということ」*と訳すザット。*長い主語*のはじまりです。"),
             ("02", "動詞", "2つ目の動詞", "*is の手前* までが S", {"S", "V", "C"},
              "ふたつめの動詞、*イズの手前*までが、主語になります。ひとつの節に、*動詞はひとつ*。"),
             ("03", "like", "like のうしろにも SV。", "*接続詞* の like", {"S", "V", "C", "L", "M"},
              "つぎに、ライク。うしろに*主語と動詞*が続くので、このライクは*接続詞*で、「のように」。まえのマッチは、*「ほぼ」*という意味です。"),
         ],
         ja=["幼い子どもが質問ばかりするのは、", "まったく*健全なこと*だ。", "科学者が、まだ説明できない考えを", "試すのと*ほぼ同じように*。"],
         ja_say="おさない子どもが、しつもんばかりするのは、まったく、けんぜんなことだ。かがくしゃが、まだ説明できない考えを、ためすのと、ほぼ同じように。",
         q=dict(en=["That he said nothing was wise,", "much like a good player waits", "for the right moment."],
                chs=[["彼が何も言わなかったのは賢明だった。", "よい選手が好機を待つのとほぼ同じように"],
                     ["彼が何も言わなかったのは、よい選手が", "好機を待つのを好むほど賢明だった"]],
                answer=1)),
    dict(no=2, theme="What の長いS+that節のC+関係詞の省略",
         hook=("この What、", "訳せる?"),
         en="What surprised the visitors most was that the old town they had read about looked completely modern.",
         lines=[[("(What surprised the visitors most)", "S")],
                [("was", "V"), (" [that the old town", "C")],
                [("they had read about", "R")],
                [("looked completely modern].", "C")]],
         labels={"S": "S(〜すること)", "C": "C(〜ということ)", "R": "関係詞の省略"},
         steps=[
             ("01", "What", "文頭の What は", "*〜すること* のカタマリ", {"S"},
              "まず、ワット。ここでは「すること」をあらわすワットです。ふたつめの動詞、*ワズの手前*までが、長い主語になります。"),
             ("02", "that", "was のあとの that は", "*〜ということ* が C", {"S", "V", "C"},
              "ワズのあとのザットは、*「ということ」*。ここから文の最後までが、補語のカタマリです。"),
             ("03", "省略", "名詞のすぐあとに SV", "*関係詞の省略*", {"S", "V", "C", "R"},
              "ジ・オールド・タウンのすぐあとに、ゼイ・ハド・レッド。名詞のあとに、主語と動詞が続くのは*関係詞の省略*。本で読んでいた古い町、となります。"),
         ],
         ja=["訪問者をいちばん驚かせたのは、", "本で読んでいた*古い町*が、", "すっかり*現代的に見えた*ことだった。"],
         ja_say="ほうもんしゃを、いちばんおどろかせたのは、本で読んでいた古い町が、すっかり現代的に見えたことだった。",
         q=dict(en=["What worried the coach was that", "the players he had trained", "seemed tired."],
                chs=[["コーチが心配したのは、自分が鍛えた", "選手たちが疲れて見えたことだった"],
                     ["何がコーチを心配させたかというと、", "選手が彼を鍛えて疲れたことだった"]],
                answer=1)),
    dict(no=3, theme="Whether の長いS+depend on+how節",
         hook=("文頭の Whether、", "訳せる?"),
         en="Whether the new library will open on time depends on how quickly the workers can finish the roof.",
         lines=[[("(Whether the new library will", "S")],
                [("open on time)", "S"), (" depends on", "V")],
                [("[how quickly the workers can", "O")],
                [("finish the roof].", "O")]],
         labels={"S": "S(〜かどうか)", "V": "V(〜次第だ)", "O": "O(どれだけ〜か)"},
         steps=[
             ("01", "Whether", "文頭の Whether は", "*〜かどうか*", {"S"},
              "いちばん最初のウェザーは、*「かどうか」*。ふたつめの動詞、ディペンズの手前までが、長い主語です。"),
             ("02", "depend on", "depend on + 人以外", "*〜次第だ*", {"S", "V"},
              "ディペンド・オンは、うしろに人以外が来ると、*「次第だ」*という意味になります。"),
             ("03", "how", "how のカタマリは", "*どれだけ〜か*", {"S", "V", "O"},
              "ハウ・クイックリーから最後までが、*「どれだけ早く、できるか」*。ディペンド・オンの目的語です。"),
         ],
         ja=["新しい図書館が予定どおり", "開館する*かどうか*は、", "作業員がどれだけ早く屋根を", "仕上げられるか*次第だ*。"],
         ja_say="新しい図書館が、予定どおり開館するかどうかは、作業員が、どれだけはやく屋根をしあげられるか、しだいだ。",
         q=dict(en=["Whether the team wins depends", "on how well the new players", "work together."],
                chs=[["チームが勝つかどうかは、新しい選手が", "どれだけうまく協力できるか次第だ"],
                     ["チームが勝とうと負けようと、新しい", "選手がうまく協力することに頼る"]],
                answer=1)),
]


import seidoku_lessons as _sl  # 台本の続き(1週間ずつ seidoku_lessons.py に足す)
LESSONS += _sl.LESSONS

# ---------- 間(無音)と字幕 ----------
_tts = gr.tts


def tts(kind, text):
    """kind "gap" は無音の間(text=秒)。音声は混ぜず、時間だけあける(grammar_reel.render が gap を飛ばす)"""
    if kind == "gap":
        return None, float(text)
    return _tts(kind, text.replace("*", ""))


gr.tts = tts


def dur(kind, text):
    """読み上げの長さ(キャッシュ。読みチェック用の記録には残さない)"""
    if kind == "gap":
        return float(text)
    _, d = _tts(kind, text.replace("*", ""))
    gr.MANIFEST.pop()
    return d


def scene_dur(parts, default):
    """grammar_reel.render と同じ計算で場面の長さを出す(切り替えのアニメーションに使う)"""
    if not parts:
        return default
    t = 0.08
    for k, x in parts:
        t += dur(k, x) + 0.08
    return max(1.3, t + 0.12)


# 字幕は画面用の表記に戻す(読み上げ用のカタカナ・ひらがな → 英字・漢字)
DISP = {"ディペンド・オン": "depend on", "ディペンズ": "depends", "ハウ・クイックリー": "how quickly", "ウェザー": "Whether",
        "ジ・オールド・タウン": "the old town", "ゼイ・ハド・レッド": "they had read", "ワット": "What", "ワズ": "was", "ザット": "That", "ライク": "like", "イズ": "is", "マッチ": "much", "ふたつめ": "2つ目", "ひとつ": "1つ",
        "やく": "訳", "つぎに": "次に", "まえの": "前の", "うしろ": "後ろ"}
DISP.update(_sl.DISP)
SUB_F = None


def _tokens(text):
    """[(文字 or 英単語, 強調?)]。*〜* が強調"""
    import re
    for k, v in sorted(DISP.items(), key=lambda kv: -len(kv[0])):  # 長い語句から先に置きかえる
        text = text.replace(k, v)
    out, em = [], False
    for m in re.findall(r"\*|[A-Za-z0-9']+|.", text):
        if m == "*":
            em = not em
        else:
            out.append((m, em))
    return out


def subtitle(base, t, text, total, start=0.08, y=1440):
    """参考動画の字幕:文(。)ごとに、読点ごとのひとことが順にぼかしからふわっと出る。*強調* は青の選択枠"""
    f = gr.jp(44)
    toks = _tokens(text)
    # ひとこと(読点・句点まで)と文に分ける
    phrases, cur = [], []
    for tk in toks:
        cur.append(tk)
        if tk[0] in "、。?":
            phrases.append(cur); cur = []
    if cur: phrases.append(cur)
    n = sum(len(tk[0]) for p in phrases for tk in p)
    times, acc = [], start
    for p in phrases:
        times.append(acc); acc += total * sum(len(tk[0]) for tk in p) / n
    sents, cur = [], []
    for i, p in enumerate(phrases):
        cur.append(i)
        if p[-1][0] in "。?":
            sents.append(cur); cur = []
    if cur: sents.append(cur)
    now = max([i for i, s0 in enumerate(times) if s0 <= t] or [0])
    sent = next(s for s in sents if now in s)
    shown = [i for i in sent if i <= now]
    # 文全体で2行に割って位置を決める(あとから出る語の位置も固定)
    toks = [tk + (i,) for i in sent for tk in phrases[i]]
    plain = "".join(tk[0] for tk in toks)
    lines = wrap2(plain, f, 800)
    cut, line_of, c = len(lines[0]), [], 0
    for tk in toks:
        line_of.append(0 if c < cut else 1); c += len(tk[0])
    lw = [sum(f.getlength(tk[0]) for tk, l in zip(toks, line_of) if l == li) for li in range(len(lines))]
    cx = CARD_X + CARD_W / 2
    pos, xs = [], [cx - w / 2 for w in lw]
    for tk, li in zip(toks, line_of):
        pos.append((xs[li], li)); xs[li] += f.getlength(tk[0])
    lh, top = 76, y - 76 * len(lines) / 2 - 20
    for pi in shown:
        lay = Image.new("RGBA", (W, int(lh * len(lines) + 40)), (0, 0, 0, 0))
        g = ImageDraw.Draw(lay)
        idx = [j for j, tk in enumerate(toks) if tk[2] == pi]
        # 強調の連なりごとに選択枠
        j = 0
        while j < len(idx):
            if toks[idx[j]][1]:
                k = j
                while k + 1 < len(idx) and toks[idx[k + 1]][1] and pos[idx[k + 1]][1] == pos[idx[j]][1]: k += 1
                x0 = pos[idx[j]][0]; x1 = pos[idx[k]][0] + f.getlength(toks[idx[k]][0]); ly = 20 + lh * pos[idx[j]][1]
                selbox(g, x0 - 8, ly + 2, x1 + 8, ly + 66, 5)
                j = k + 1
            else:
                j += 1
        for jj in idx:
            x, li = pos[jj]
            g.text((x, 20 + lh * li), toks[jj][0], font=f, fill=INK + (255,))
        appear(base, lay, 0, top, t, times[pi], dur=0.3, rise=14)


def wrap2(text, f, maxw):
    """1行に収まらなければ2行に。左右の幅がそろう位置で、読点・助詞のあとを優先して切る(英単語の途中では切らない)"""
    import re
    if gr.text_w(f, text) <= maxw:
        return [text]
    atoms = re.findall(r"[A-Za-z0-9']+|.", text)
    best = None
    for i in range(1, len(atoms)):
        l, r = "".join(atoms[:i]), "".join(atoms[i:])
        if r[0] in "。、」?)" or l.count("「") > l.count("」") or gr.text_w(f, l) > maxw or gr.text_w(f, r) > maxw:
            continue
        score = abs(gr.text_w(f, l) - gr.text_w(f, r))
        if l[-1] in "、。":
            score -= 400
        elif l[-1] in "はがをにでとのもへ」":
            score -= 90
        if best is None or score < best[0]:
            best = (score, [l, r])
    return best[1] if best else [text]


OUTRO = 0.3  # 切り替え:前の画面がぼけながら上へ消え、丸が線にそって下りる


def scene(S, content, parts, rail_args=None, default=2.6):
    D = scene_dur(parts, default)

    def f(bb, T, t):
        ko = max(0.0, (t - (D - OUTRO)) / OUTRO)
        if ko <= 0:
            if rail_args: rail(bb, t, *rail_args)
            content(bb, t)
            return
        k = gr.ease(ko)
        if rail_args: rail(bb, t, *rail_args, k_out=k)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        content(lay, t)
        lay = lay.filter(ImageFilter.GaussianBlur(10 * k))
        lay.putalpha(lay.split()[3].point(lambda v: int(v * (1 - k))))
        sh = int(70 * k)
        bb.alpha_composite(lay.crop((0, sh, W, H)), (0, 0))
    S.append((D, "", f, parts))


def build(L):
    ALL = set().union(*(st[4] for st in L["steps"]))
    S = []
    scene(S, lambda bb, t: hook(bb, t, *L["hook"]), [], default=gr.HOOK)
    # 英文の読み上げは、解説に入る前の1回だけ。「訳せますか?」のあと少し間をあける
    scene(S, lambda bb, t: (
        headline(bb, t, "この英文、", "*訳せる?*"),
        sentence_card(bb, t, L["lines"], set(), L["labels"], d=0.15)),
        [("ja", "この英文、やくせますか?"), ("gap", "0.6"), ("m", L["en"])], ("00", "英文"))
    for no, name, l1, l2, show, say in L["steps"]:
        scene(S, lambda bb, t, l1=l1, l2=l2, show=show, say=say, sd=dur("ja", say): (
            headline(bb, t, l1, l2),
            sentence_card(bb, t, L["lines"], show, L["labels"], d=0.0),
            subtitle(bb, t, say, sd)),
            [("ja", say)], (no, name))
    n = f"{len(L['steps']) + 1:02d}"
    scene(S, lambda bb, t: (
        headline(bb, t, "つまり、", "*こういう意味*"),
        sentence_card(bb, t, L["lines"], ALL, L["labels"], y=630, d=0.1, size=42),
        text_card(bb, t, L["ja"], y=1170, size=42, d=0.35)),
        [("ja", L["ja_say"])], (n, "和訳"))
    q = L["q"]
    # 和訳のあと:つなぎの一言 → 少し間 → 応用の英文 → 問いかけ
    scene(S, lambda bb, t: (
        headline(bb, t, "同じ形で、", "*正しい訳は?*"),
        quiz_card(bb, t, q["en"], q["chs"], d=0.2),
        cta(bb, t, d=2.0)),
        [("ja", "では、同じ形で、応用問題。この英文の、ただしいやくは?"), ("gap", "0.5"), ("f", " ".join(q["en"])),
         ("gap", "0.3"), ("ja", "1と2、どっち?答えと解説は、コメント欄にあるよ。")], ("Q", "クイズ"))
    return "seidoku", S


def render(no):
    L = next(x for x in LESSONS if x["no"] == no)
    sys.modules["grammar_lessons"] = types.SimpleNamespace(LESSONS=[L])
    gr.lesson = build
    OUT.mkdir(parents=True, exist_ok=True)
    return gr.render(0, no, OUT / f"seidoku_{no:03d}.mp4")


if __name__ == "__main__":
    for a in sys.argv[1:] or ["1"]:
        render(int(a))
