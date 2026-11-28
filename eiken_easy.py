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
DISP = {"ハウエバー": "However", "ノット・オール": "not all", "ばつ": "×", "イン・アディション": "In addition", "ラザー・ザン": "Rather than"}


def psub(base, t, items, y=1510):
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
    sents = [(re.sub(r"\(\s*①\s*\)", "(\u00a0①\u00a0)", x), n) for x, n in sents]
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
    """「解きたい人は、ここで一時停止」+一時停止アイコン(丸に2本線。ゆっくり脈打つ)"""
    if t < d: return
    s = "解きたい人は、ここで一時停止"
    tw = gr.jp(48).getlength(s) + 90
    cx = 540 + 60  # アイコンのぶん右へ
    gr.tape(base, T, t, s, cx, y, angle=-2, d=d, size=48)
    import math
    k = gr.back((t - d) / 0.3) * (1 + 0.06 * math.sin((t - d) * 6))
    r = 50
    lay = Image.new("RGBA", (2 * r + 8, 2 * r + 8), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    g.ellipse([4, 4, 2 * r + 4, 2 * r + 4], fill=GREEN + (255,), outline=(20, 20, 20, 255), width=5)
    for x0 in (r - 22, r + 8):
        g.rounded_rectangle([x0 + 4, r - 22 + 4, x0 + 18, r + 22 + 4], 4, fill=(20, 20, 20, 255))
    gr.paste_rot(base, lay, cx - tw / 2 - 40, y + 2, 0, scale=max(0.01, k))


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
        # 応用問題:答えは However にしない。「前と逆の向き」を読む同じ発想で、合図の言葉を変える
        app=dict(sents=[("Many people think staying late at the office shows hard work.", 1), ("In reality, ( ① ).", 2)],
                 chs=[("it often lowers the quality of work", "仕事の質を下げることが多い"), ("it is the fastest way to get promoted", "いちばん早く昇進できる方法だ")], ans=1),
        comment="""✅ 応用問題の正解は 1

Many people think staying late at the office shows hard work. In reality, it often lowers the quality of work.
多くの人は、遅くまで会社に残ることが勤勉さの表れだと思っている。実際には、それは仕事の質を下げることが多い。

━━ 解説 ━━
In reality(実際には)は、前の「みんなが思っていること」をひっくり返す合図。
❶ の「残業=がんばっている」というプラスの考えに対して、空所はマイナスの内容 → 1。
2 は ❶ と同じ向きなので×。

However / In reality / Actually / Yet など「前と逆の向き」の合図を見つけたら、空所は前と反対の内容を選ぼう。

━━ 動画の問題の全文 ━━
Many shoppers trust online reviews when choosing products. However, not all reviews are honest. Some companies pay people to write positive comments, and others post negative reviews of their rivals.
多くの買い物客は、商品を選ぶときにネットのレビューを信頼している。しかし、すべてのレビューが正直なわけではない。お金を払って良いコメントを書かせる会社もあれば、ライバルの悪いレビューを投稿する会社もある。

📝 単語
trust 信頼する / honest 正直な / positive 良い、肯定的な / negative 悪い、否定的な / rival ライバル / in reality 実際には""",
    ),
    6: dict(
        signal=("In addition", "さらに"),
        signal_say="ポイントは、*イン・アディション*。さらに、と*メリットを足す*合図です。",
        steps=[
            dict(tag="メリット", hl={2: "join a class from home"}, hl_ja={2: "自宅から授業に参加でき"}, dim={1, 3},
                 say="2文目。自宅から参加できて、*あとで復習*もできる。どれも*メリット*の話です。"),
            dict(tag="根拠", hl={3: "teachers do not need classrooms"}, hl_ja={3: "教室を必要としない"}, dim={1, 2},
                 say="3文目。先生は*教室がいらない*。つまり、家賃などの*費用が減る*、ということ。"),
        ],
        answer_say="だから*正解は1*。安い料金で提供できる。本文に書いていないことを*推測する*問題です。",
        trap_say="2の、先生を減らせる、は*教室と関係ない*ので、ばつ。",
        app=dict(sents=[("Working from home saves employees the time they used to spend commuting.", 1),
                        ("What is more, since they do not need office clothes, they can ( ① ).", 2)],
                 chs=[("spend less money on clothing", "服にかけるお金を減らせる"), ("work longer hours every day", "毎日もっと長く働ける")], ans=1),
        caption="""In addition のあと、何が入る?🤔
本文に書いていないことを読む「推測型」の空所補充。英検準1級・2級の長文で差がつくポイントを解説します。
解きたい人は一時停止してね⏸ 応用問題の答えはコメント欄に👇

#英検準1級 #英検 #英語長文 #空所補充 #英語学習""",
        comment="""✅ 応用問題の正解は 1

Working from home saves employees the time they used to spend commuting. What is more, since they do not need office clothes, they can spend less money on clothing.
在宅勤務なら、社員は通勤に使っていた時間を節約できる。さらに、仕事用の服がいらないので、服にかけるお金を減らせる。

━━ 解説 ━━
What is more(さらに)は In addition と同じ「メリットを足す」合図。
「仕事用の服がいらない」→ 服代が減る、と推測して 1。
2「もっと長く働ける」は、服がいらないこととは関係ないので×。

推測型は「書いてあること → その結果どうなる?」を考えよう。

━━ 動画の問題の全文 ━━
Online language lessons are becoming popular among busy adults. Students can join a class from home, and lessons are often recorded so they can be reviewed later. In addition, because teachers do not need classrooms, schools can offer lessons at lower prices.
忙しい大人の間で、オンラインの語学レッスンが人気になっている。生徒は自宅から授業に参加でき、レッスンは録画されることが多いので、あとで復習できる。さらに、先生は教室を必要としないため、学校は安い料金でレッスンを提供できる。

📝 単語
record 録画する / review 復習する / in addition さらに / offer 提供する / hire 雇う / what is more さらに / commute 通勤する""",
    ),
    7: dict(
        signal=("Rather than", "〜ではなく"),
        signal_say="ポイントは、*ラザー・ザン*。閉館する*のではなく*、と逆の内容が来る合図です。",
        steps=[
            dict(tag="マイナスの話", hl={1: "lending fewer books"}, hl_ja={1: "本の貸し出しが減っている"}, dim={2, 3},
                 say="まず1文目。図書館の、本の*貸し出しが減っている*。マイナスの話です。"),
            dict(tag="具体例", hl={3: "quiet study rooms"}, hl_ja={3: "静かな自習室"}, dim={1, 2},
                 say="3文目に、自習室、無料のネット、講座と、*新しいサービス*がならんでいる。空所はその*まとめ*です。"),
        ],
        answer_say="だから*正解は1*。地域の役に立つ、*新しい方法*を見つけた。",
        trap_say="2は、1文目から想像した*ワナ*。本を買うのをやめたとは、書いていないので、ばつ。",
        app=dict(sents=[("Fewer people visit the old shopping street these days.", 1),
                        ("Instead of giving up, the shop owners have ( ① ).", 2),
                        ("They hold weekend markets, music events, and cooking classes for kids.", 3)],
                 chs=[("started new events to bring people back", "人を呼び戻す新しい催しを始めた"), ("decided to close their shops", "店を閉めることにした")], ans=1),
        caption="""Rather than のあと、何が入る?🤔
空所のあとに具体例が並んだら「まとめ」を選ぶ。英検2級・準1級の長文読解でそのまま使える解き方です。
先に解きたい人は一時停止してね⏸ 応用問題の答えはコメント欄に👇

#英検2級 #英検対策 #長文読解 #英語勉強 #英検準1級""",
        comment="""✅ 応用問題の正解は 1

Fewer people visit the old shopping street these days. Instead of giving up, the shop owners have started new events to bring people back. They hold weekend markets, music events, and cooking classes for kids.
最近、古い商店街を訪れる人が減っている。あきらめるのではなく、店主たちは人を呼び戻す新しい催しを始めた。週末の市場や音楽イベント、子ども向けの料理教室を開いている。

━━ 解説 ━━
Instead of A(Aではなく)は Rather than と同じ「逆の内容が来る」合図。
あきらめる ↔ 新しいことを始める。さらに ❸ の「市場・音楽イベント・料理教室」をまとめると 1。
2「店を閉める」は giving up と同じ向きなので×。

空所のあとに具体例が並んでいたら、空所はそのまとめ(サマリー型)。

━━ 動画の問題の全文 ━━
Many public libraries are lending fewer books than they did ten years ago. Rather than closing, however, some libraries have found new ways to serve their communities. They now offer quiet study rooms, free internet access, and classes on topics such as job hunting and cooking.
多くの公立図書館では、10年前に比べて本の貸し出しが減っている。しかし、閉館するのではなく、地域の役に立つ新しい方法を見つけた図書館もある。今では静かな自習室や無料のネット接続、就職活動や料理などの講座を提供しているのだ。

📝 単語
lend 貸す / rather than A Aではなく / serve 役に立つ / community 地域社会 / access 利用 / instead of A Aではなく / give up あきらめる""",
    ),

}


def app_body(bb, t, ap):
    """応用問題:本文 → 選択肢 → その下に「答えはコメント欄に」と「保存」(本文の長さに合わせて位置を決める)"""
    yb = passage(bb, t, ap["sents"], y=440, d=0.15) + 30
    choices(bb, t, ap["chs"], yb, d=0.35)
    gr.comment_cta(bb, T, t, d=0.7, y=yb + 182 + 90)
    gr.tape(bb, T, t, "保存して、あとで復習", 540, yb + 182 + 230, angle=-2, d=1.0, size=44)


def build(L):
    import eiken_problems as ep
    Q = next(q for q in ep.PROBLEMS if q["no"] == L["no"])
    sc = SCRIPTS[L["no"]]
    sents = [(re.sub(r"\(\s*①\s*\)", "(\u00a0①\u00a0)", s), n) for s, n in Q["body"][0]]
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
    # 最後に応用問題(同じ発想・ちがう合図の言葉)。答え・全文・解説はコメント欄 → 最後まで見る+コメントが増える
    ap = sc["app"]
    scene(S, lambda bb, t: (
        step_tag(bb, t, f"{n0 + 2:02d}", "応用問題"),
        label(bb, t, "同じ発想で、解ける?", 330, size=60, color=GREEN),
        app_body(bb, t, ap)),
        [("ja", "最後に*応用問題*。同じ発想で、*解けるかな?*")])  # リーディングなので英文は読まない。ここでサクッと終える
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


def add(no, at):
    """docs/reels に公開して reel_schedule.json(GitHub Actions が reel_post.py run eiken で投稿)へ。push は別"""
    import json, shutil
    import post
    no = int(no)
    sc = SCRIPTS[no]
    src = OUT / f"eiken_{no:03d}.mp4"
    dst = ROOT / "docs" / "reels" / f"eiken_easy_{no:03d}.mp4"
    shutil.copy(src, dst)
    cap = sc["caption"] + "\n\n" + gr.track_for(no)["credit"]
    key = f"eiken_easy_{no:03d}"
    sch = ROOT / "reel_schedule.json"
    items = [s for s in json.loads(sch.read_text()) if s["key"] != key]
    items.append({"key": key, "kind": "eiken", "at": at, "video": f"https://eng-navi.github.io/reels/{dst.name}",
                  "caption": post.keep_blank_lines(cap), "comment": post.keep_blank_lines(sc["comment"])})
    items.sort(key=lambda s: s["at"])
    sch.write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n")
    print("予約:", key, at)


if __name__ == "__main__":
    if sys.argv[1:2] == ["add"]:  # python3 eiken_easy.py add 6 "2026-11-28 21:00"
        add(sys.argv[2], sys.argv[3])
    else:
        for a in sys.argv[1:] or ["31"]:
            render(int(a))
