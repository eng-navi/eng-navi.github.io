"""@seidoku.lab「差がつく英文読解」のリール。grammar_reel.py の部品を使い、黒×白×黄色で作る。

    python3 seidoku_reel.py 1        # → out/seidoku/seidoku_001.mp4
    .venv-tts/bin/python yomi_check.py out/seidoku/seidoku_001.voice.json

流れ:冒頭タイトル → 難しい1文 → 分解(長いS → V → like など)→ 和訳 → 和訳クイズ(答えはコメント)。
英文はすべてオリジナル。本は「構文パターン」の参考だけ(本の英文・訳・場面は使わない)。
"""
import random
import sys
import types
from pathlib import Path

from PIL import Image, ImageDraw

import grammar_reel as gr

ROOT = Path(__file__).parent
OUT = ROOT / "out" / "seidoku"

YEL = (255, 214, 0)
gr.THEMES["seidoku"] = dict(bg=(14, 14, 14), big=(255, 255, 255), sub=(255, 255, 255), accent=YEL, tape=YEL, ink=(14, 14, 14))
# 声(仮。聞き比べで決める):日本語=Kozy(男性・v3)、英文=アメリカ英語の若い男女 Liam / Jessica(v2)
gr.VOICE.update({"ja": "GxxMAMfQkDlnqjpzjLHH", "m": "TX3LPaxmHKxFdv7VOQHJ", "f": "cgSgspJ2msm6clMCkdW9"})
gr.SPEED.update({"m": 0.95, "f": 0.95})


def background(theme):
    im = Image.new("RGB", (gr.W, gr.H), (14, 14, 14))
    noise = Image.effect_noise((gr.W, gr.H), 14).convert("L")
    im = Image.composite(Image.new("RGB", (gr.W, gr.H), (60, 60, 60)), im, noise.point(lambda v: int(max(0, v - 128) * 0.18)))
    d = ImageDraw.Draw(im)
    # 左上のロゴ帯(黄色)
    d.rectangle([0, 150, 18, 260], fill=YEL)
    d.text((44, 160), "差がつく英文読解", font=gr.jp(44), fill=(255, 255, 255))
    d.text((44, 222), "seidoku.lab", font=gr.serif(30, 500), fill=(170, 170, 170))
    return im


gr.background = background


# ---------- 構文の図解カード ----------
LABEL = {"S": "S", "V": "V", "C": "C", "O": "O", "M": "M"}


def parse_card(bb, T, t, lines, show, cy=860, d=0.0, labels=None):
    """lines: [[(text, tag), ...], ...]。show に入っている tag を黄色でハイライトし、下に S/V/C などの札。
    labels: {tag: 札の文字}(既定は S/V/C/M)。札は tag ごとに最初の1回だけ。"""
    if t < d: return
    k = gr.ease((t - d) / 0.35)
    labels = {**LABEL, **(labels or {})}
    f = gr.serif(54, 600)
    lf = gr.jp(30)
    wmax, gap = 1000, 140
    hgt = 50 + gap * len(lines) + 10
    lay = Image.new("RGBA", (wmax, hgt), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    g.rounded_rectangle([0, 0, wmax - 1, hgt - 1], 18, fill=(255, 255, 255, 255))
    done = set()
    y = 34
    for segs in lines:
        x = 44
        for s, tag in segs:
            w = gr.text_w(f, s)
            if tag in show:
                lead = len(s) - len(s.lstrip())
                x0 = x + gr.text_w(f, s[:lead]) if lead else x
                g.rectangle([x0 - 2, y + 10, x + w + 2, y + 70], fill=YEL + (255,))
            g.text((x, y), s, font=f, fill=(20, 20, 20))
            if tag in show and tag not in done:
                done.add(tag)
                lab = labels.get(tag, tag)
                lw = gr.text_w(lf, lab) + 26
                lx = x + w / 2 - lw / 2
                g.rounded_rectangle([lx, y + 74, lx + lw, y + 112], 19, fill=(20, 20, 20, 255))
                g.text((lx + 13, y + 74), lab, font=lf, fill=YEL + (255,))
            x += w
        y += gap
    off = (1 - k) * 200
    gr.paste_rot(bb, lay, gr.W / 2, cy + off, 0, alpha=k)


def choices_card(bb, T, t, en_rows, chs, cy=930, d=0.0):
    """和訳クイズ:英文(白カード)+ 1/2 の訳(黒地に白字の枠)"""
    if t < d: return
    k = gr.ease((t - d) / 0.35)
    fe, fj, fn = gr.serif(50, 600), gr.jp(38, bold=False), gr.font("Anton-Regular.ttf", 64)
    wmax = 1000
    hgt = 40 + 76 * len(en_rows) + 30 + sum(40 + 58 * len(c) for c in chs) + 20
    lay = Image.new("RGBA", (wmax, hgt), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    g.rounded_rectangle([0, 0, wmax - 1, hgt - 1], 18, fill=(255, 255, 255, 255))
    y = 30
    for r in en_rows:
        g.text((44, y), r, font=fe, fill=(20, 20, 20)); y += 76
    y += 20
    for i, c in enumerate(chs):
        h = 20 + 58 * len(c)
        g.rounded_rectangle([30, y, wmax - 30, y + h], 14, fill=(20, 20, 20, 255))
        g.text((56, y + 6), str(i + 1), font=fn, fill=YEL + (255,))
        for j, line in enumerate(c):
            g.text((120, y + 10 + 58 * j), line, font=fj, fill=(255, 255, 255, 255))
        y += h + 20
    off = (1 - k) * 200
    gr.paste_rot(bb, lay, gr.W / 2, cy + off, 0, alpha=k)


# ---------- 台本 ----------
LESSONS = [
    dict(no=1, theme="長いS+接続詞の like",
         hook_big="長い主語、見抜ける?",
         en="That young children ask endless questions is entirely healthy, much like scientists test ideas they cannot yet explain.",
         lines=[[("(That young children ask endless", "S")],
                [("questions)", "S"), (" is", "V"), (" entirely healthy,", "C")],
                [("[much ", "M"), ("like", "L"), (" scientists test ideas", "M")],
                [("they cannot yet explain].", "M")]],
         labels={"S": "S(長い主語)", "L": "接続詞"},
         steps=[
             ("That のうしろに SV\n→「〜ということ」のカタマリ", {"S"},
              "まず、ザットのうしろに、主語と動詞が続いています。だからこのザットは、「ということ」と訳すザット。長い主語のはじまりです。"),
             ("2つ目の動詞 is の手前まで\n= 長い S", {"S", "V", "C"},
              "ひとつの節に、動詞はひとつ。ふたつめの動詞、イズの手前までが、主語になります。"),
             ("like のうしろにも SV\n→ 接続詞「〜のように」", {"S", "V", "C", "L"},
              "つぎに、ライク。うしろに主語と動詞が続くので、このライクは接続詞で、「のように」。まえのマッチは、「ほぼ」という意味です。"),
         ],
         ja="幼い子どもが質問ばかりするのは、|まったく健全なことだ。|科学者が、まだ説明できない考えを|試すのとほぼ同じように。",
         ja_say="おさない子どもが、しつもんばかりするのは、まったく、けんぜんなことだ。かがくしゃが、まだ説明できない考えを、ためすのと、ほぼ同じように。",
         q=dict(en=["That he said nothing was wise,", "much like a good player waits", "for the right moment."],
                chs=[["彼が何も言わなかったのは賢明だった。", "よい選手が好機を待つのとほぼ同じように"],
                     ["彼が何も言わなかったのは、よい選手が", "好機を待つのを好むほど賢明だった"]],
                answer=1)),
]


def build(L):
    S = []
    S.append((gr.HOOK, "", lambda bb, T, t: gr.hook_title(bb, T, t, L["hook_big"]), []))
    S.append((2.6, "この英文、訳せる?", lambda bb, T, t: parse_card(bb, T, t, L["lines"], set(), labels=L["labels"]),
              [("ja", "この英文、やくせますか?"), ("m", L["en"])]))
    for sub, show, say in L["steps"]:
        S.append((2.8, sub, lambda bb, T, t, show=show: parse_card(bb, T, t, L["lines"], show, labels=L["labels"]),
                  [("ja", say)]))
    ja_rows = [([(x, False)], "ja") for x in L["ja"].split("|")]
    S.append((3.0, "", lambda bb, T, t: (
        gr.big(bb, T, t, "和訳", 470, size=120, color=YEL),
        gr.card(bb, T, t, [([(x, False)], "en") for x in _wrap(L["en"])] + ja_rows, 900, angle=0, hl=YEL)),
        [("f", L["en"]), ("ja", L["ja_say"])]))
    q = L["q"]
    S.append((4.4, "", lambda bb, T, t: (
        gr.big(bb, T, t, "Q. 正しい訳は?", 430, size=100, color=YEL),
        choices_card(bb, T, t, q["en"], q["chs"], cy=880, d=0.2),
        gr.comment_cta(bb, T, t, d=0.9, y=1400)),
        [("m", " ".join(q["en"])), ("ja", "ただしい訳は、1と2、どっち?答えと解説は、コメント欄にあるよ。")]))
    return "seidoku", S


def _wrap(s, n=31):
    out, cur = [], ""
    for w in s.split():
        if len(cur) + len(w) + 1 > n and cur:
            out.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    return out + [cur]


def render(no):
    L = next(x for x in LESSONS if x["no"] == no)
    sys.modules["grammar_lessons"] = types.SimpleNamespace(LESSONS=[L])
    gr.lesson = build
    OUT.mkdir(parents=True, exist_ok=True)
    return gr.render(0, no, OUT / f"seidoku_{no:03d}.mp4")


if __name__ == "__main__":
    for a in sys.argv[1:] or ["1"]:
        render(int(a))
