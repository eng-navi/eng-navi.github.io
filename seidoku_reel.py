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
def appear(base, lay, x, y, t, d=0.0, dur=0.35, rise=40):
    """ぼかしからふわっと出す(参考動画の切り替え)。x, y は左上"""
    if t < d: return
    k = gr.ease((t - d) / dur)
    if k < 1:
        lay = lay.filter(ImageFilter.GaussianBlur((1 - k) * 10))
        a = lay.split()[3].point(lambda v: int(v * k))
        lay.putalpha(a)
    base.alpha_composite(lay, (int(x), int(y + (1 - k) * rise)))


def _segs(s):
    parts = s.split("*")
    return [(x, i % 2 == 1) for i, x in enumerate(parts) if x]


def headline(base, t, l1, l2, y=250, d=0.0):
    """1行目:グレー、2行目:太字の黒。2行目の *語* は青の選択枠(角に小さな四角)"""
    f1, f2 = gr.jp(58, bold=False), gr.jp(70)
    lay = Image.new("RGBA", (W, 230), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    if l1:
        g.text(((W - gr.text_w(f1, l1)) / 2, 0), l1, font=f1, fill=GRAY + (255,))
    segs = _segs(l2)
    tw = sum(gr.text_w(f2, s) for s, _ in segs)
    x, yy = (W - tw) / 2, 96 if l1 else 40
    for s, kw in segs:
        w = gr.text_w(f2, s)
        if kw:
            g.rectangle([x - 12, yy + 4, x + w + 12, yy + 104], fill=(232, 239, 255, 255), outline=BLUE + (255,), width=3)
            for cx, cy in [(x - 12, yy + 4), (x + w + 12, yy + 4), (x - 12, yy + 104), (x + w + 12, yy + 104)]:
                g.rectangle([cx - 7, cy - 7, cx + 7, cy + 7], fill=(255, 255, 255, 255), outline=BLUE + (255,), width=3)
        g.text((x, yy), s, font=f2, fill=INK + (255,))
        x += w
    appear(base, lay, 0, y, t, d)


def rail(base, t, no, label, d=0.0):
    """左の縦線(上が青)とステップ札「01 主語」"""
    g = ImageDraw.Draw(base)
    g.line([(LINE_X, 0), (LINE_X, H)], fill=(222, 222, 218), width=10)
    g.line([(LINE_X, 0), (LINE_X, PILL_Y)], fill=BLUE, width=10)
    g.ellipse([LINE_X - 30, PILL_Y - 30, LINE_X + 30, PILL_Y + 30], fill=BLUE, outline=(255, 255, 255), width=5)
    g.text((LINE_X - 13, PILL_Y - 24), "読", font=gr.jp(30), fill=(255, 255, 255))
    fn, fl = gr.jp(28), gr.jp(36)
    w = 26 + gr.text_w(fn, no) + 40 + gr.text_w(fl, label) + 30
    lay = Image.new("RGBA", (w, 64), (0, 0, 0, 0))
    q = ImageDraw.Draw(lay)
    q.rounded_rectangle([0, 0, w - 1, 63], 32, fill=BLUE + (255,))
    nb = gr.text_w(fn, no) + 20
    q.rounded_rectangle([14, 12, 14 + nb, 52], 10, fill=(120, 158, 245, 255))
    q.text((24, 12), no, font=fn, fill=(255, 255, 255, 255))
    q.text((14 + nb + 18, 6), label, font=fl, fill=(255, 255, 255, 255))
    appear(base, lay, LINE_X + 46, PILL_Y - 32, t, d, rise=0)


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


ORANGE = (236, 120, 24)  # カタマリの括弧の色(青と相性のよい補色)
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
                    lw = gr.text_w(lf, lab) + 28
                    lx = x + lead + (w - lead) / 2 - lw / 2
                    g.rounded_rectangle([lx, yy + size * 1.45, lx + lw, yy + size * 1.45 + 40], 20, fill=BLUE + (255,))
                    g.text((lx + 14, yy + size * 1.45 + 2), lab, font=lf, fill=(255, 255, 255, 255))
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
              "まず、ザットのうしろに、主語と動詞が続いています。だからこのザットは、「ということ」と訳すザット。長い主語のはじまりです。"),
             ("02", "動詞", "2つ目の動詞", "*is の手前* までが S", {"S", "V", "C"},
              "ふたつめの動詞、イズの手前までが、主語になります。ひとつの節に、動詞はひとつ。"),
             ("03", "like", "like のうしろにも SV。", "*接続詞* の like", {"S", "V", "C", "L", "M"},
              "つぎに、ライク。うしろに主語と動詞が続くので、このライクは接続詞で、「のように」。まえのマッチは、「ほぼ」という意味です。"),
         ],
         ja=["幼い子どもが質問ばかりするのは、", "まったく*健全なこと*だ。", "科学者が、まだ説明できない考えを", "試すのと*ほぼ同じように*。"],
         ja_say="おさない子どもが、しつもんばかりするのは、まったく、けんぜんなことだ。かがくしゃが、まだ説明できない考えを、ためすのと、ほぼ同じように。",
         q=dict(en=["That he said nothing was wise,", "much like a good player waits", "for the right moment."],
                chs=[["彼が何も言わなかったのは賢明だった。", "よい選手が好機を待つのとほぼ同じように"],
                     ["彼が何も言わなかったのは、よい選手が", "好機を待つのを好むほど賢明だった"]],
                answer=1)),
]


def build(L):
    ALL = set().union(*(st[4] for st in L["steps"]))
    S = []
    S.append((gr.HOOK, "", lambda bb, T, t: hook(bb, t, *L["hook"]), []))
    # 英文の読み上げは、解説に入る前の1回だけ
    S.append((2.6, "", lambda bb, T, t: (
        rail(bb, t, "00", "英文"),
        headline(bb, t, "この英文、", "*訳せる?*"),
        sentence_card(bb, t, L["lines"], set(), L["labels"])),
        [("ja", "この英文、やくせますか?"), ("m", L["en"])]))
    for no, name, l1, l2, show, say in L["steps"]:
        S.append((2.8, "", lambda bb, T, t, no=no, name=name, l1=l1, l2=l2, show=show: (
            rail(bb, t, no, name),
            headline(bb, t, l1, l2),
            sentence_card(bb, t, L["lines"], show, L["labels"], d=0.0)),
            [("ja", say)]))
    n = f"{len(L['steps']) + 1:02d}"
    S.append((3.0, "", lambda bb, T, t: (
        rail(bb, t, n, "和訳"),
        headline(bb, t, "つまり、", "*こういう意味*"),
        sentence_card(bb, t, L["lines"], ALL, L["labels"], y=630, d=0.0, size=42),
        text_card(bb, t, L["ja"], y=1170, size=42)),
        [("ja", L["ja_say"])]))
    q = L["q"]
    S.append((4.4, "", lambda bb, T, t: (
        rail(bb, t, "Q", "クイズ"),
        headline(bb, t, "同じ形で、", "*正しい訳は?*"),
        quiz_card(bb, t, q["en"], q["chs"]),
        cta(bb, t)),
        [("f", " ".join(q["en"])), ("ja", "ただしいやくは、1と2、どっち?答えと解説は、コメント欄にあるよ。")]))
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
