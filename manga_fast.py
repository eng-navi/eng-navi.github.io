"""テンポの速い4コマ(ストップモーション風の揺れつき)。1本につきターゲット単語は1つ、ほかにも使える単語を数個。

    .venv-tts/bin/python manga_fast.py procrastinate      # out/manga/procrastinate_fast.mp4 と 4コマ・解説の画像
    .venv-tts/bin/python manga_fast.py procrastinate --hook   # 冒頭を変えた版(procrastinate_fast_hook.mp4)

・--hook:文字だけのタイトル画面をやめて、0秒目から絵。オチを0.6秒ちらっと見せてから1コマ目へ。問いかけは1コマ目まで上に大きく重ねる

・最初の約1秒でターゲット単語を見せる(つかみ)。コマの切り替えは「パッ」と寄って止まる
・画面は揺らさない。声の大きさはそろえ、後ろにかすかなBGM
・セリフはコマごとに1〜2つ。ElevenLabs の声を少し速め(speed 1.1)で
"""
import random
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import manga as m
import manga_reel as mr

ROOT = Path(__file__).parent
OUT = ROOT / "out" / "manga"
W, H, FPS, SR = 1080, 1920, 12, 24000
SPEED = 1.1
# 後ろでかすかに流す曲(Uppbeat の Cozy Places / Yokonap。クレジットはキャプションに)
BGM = ROOT / "assets" / "manga_bgm" / "cozy-places.mp3"
BGM_VOLUME = 0.06
BG = (244, 241, 234)


def small_bubble(d, box, tail, en, ja, seed=0):
    """文字に合わせた角丸の吹き出し(英語32px・和訳21px)。box はおおよその置き場所(中心をそろえる)。"""
    x0, y0, x1, y1 = box
    fe, fj = m.EN(32), m.JP(21)
    lines = en.split("\n")
    w = max([fe.getlength(l) for l in lines] + [fj.getlength(ja) if ja else 0]) + 40
    h = len(lines) * 37 + (28 if ja else 0) + 26
    cx = min(max((x0 + x1) / 2, x0 + w / 2), x1 - w / 2) if w < x1 - x0 else (x0 + x1) / 2
    bx0, by0 = cx - w / 2, y0
    pts = m.rrect_pts(bx0, by0, bx0 + w, by0 + h, 26)
    tx = min(max(tail[0], bx0 + 30), bx0 + w - 30)
    tail_pts = [(tx - 13, by0 + h - 2), tail, (tx + 13, by0 + h - 2)]
    d.polygon(pts, fill=(255, 255, 255))
    d.polygon(tail_pts, fill=(255, 255, 255))
    d.line(m.wob(pts, amp=1.0, seed=seed), fill=m.INK, width=4, joint="curve")
    d.line(tail_pts, fill=m.INK, width=4)
    y = by0 + 13 + 18
    for line in lines:
        d.text((cx, y), line, font=fe, fill=m.INK, anchor="mm")
        y += 37
    if ja:
        d.text((cx, y - 4), ja, font=fj, fill=(120, 110, 105), anchor="mm")
    return by0 + h


def papers(d, cx, bottom, n=7, seed=300):
    r = random.Random(seed)
    for i in range(n):
        y = bottom - i * 14
        dx = r.uniform(-8, 8)
        m.shape(d, m.rrect_pts(cx - 70 + dx, y - 14, cx + 70 + dx, y, 3), (252, 250, 244), w=3, seed=seed + i)


def beanbag(d, cx, cy, s, seed=310):
    m.shape(d, m.rrect_pts(cx - s * 0.75, cy - s * 0.3, cx + s * 0.75, cy + s * 0.32, s * 0.3), (240, 180, 120), seed=seed)


def phone(d, x, y):
    d.rounded_rectangle([x, y, x + 34, y + 56], radius=6, fill=(60, 60, 70), outline=m.INK, width=3)
    d.rectangle([x + 5, y + 7, x + 29, y + 46], fill=(160, 210, 240))


def procrastinate():
    img, boxes, pw, ph = m.comic("procrastinate")
    # 1:締め切り前なのに、ペンはスマホ
    x0, y0, x1, y1 = boxes[0]
    d = m.panel(img, boxes[0], 41)
    beanbag(d, x0 + pw * 0.3, y0 + ph * 0.86, 150)
    m.penguin(d, x0 + pw * 0.3, y0 + ph * 0.68, 115, "happy", hat_on=False)
    phone(d, x0 + pw * 0.36, y0 + ph * 0.66)
    m.owl(d, x0 + pw * 0.78, y0 + ph * 0.74, 110, "normal")
    papers(d, x0 + pw * 0.78, y0 + ph * 0.5, 4)
    bot = small_bubble(d, (x0 + 12, y0 + 12, x0 + pw - 12, 0), (x0 + pw * 0.76, y0 + ph * 0.6),
                       "Your report is due tomorrow.\nShouldn't you get started?", "レポート、明日締め切りだよ?", 1)
    small_bubble(d, (x0 + 12, bot + 10, x0 + pw * 0.7, 0), (x0 + pw * 0.3, y0 + ph * 0.54),
                 "Relax. I work better\nunder pressure.", "平気。追い込まれた方がはかどるの", 2)
    # 2:ナビのツッコミ(ターゲット単語)
    x0, y0, x1, y1 = boxes[1]
    d = m.panel(img, boxes[1], 42)
    m.owl(d, x0 + pw * 0.34, y0 + ph * 0.7, 150, "shock")
    m.sweat(d, x0 + pw * 0.52, y0 + ph * 0.46)
    m.penguin(d, x0 + pw * 0.76, y0 + ph * 0.72, 110, "smug", hat_on=False)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.34, y0 + 230),
                 "You said that yesterday!\nStop procrastinating!", "それ昨日も!先延ばしはやめて!", 3)
    m.sfx(img, (x0 + pw * 0.86, y0 + ph * 0.42), "!!", 54, (220, 80, 70), -10)
    # 3:なぜか急に部屋の片付け
    x0, y0, x1, y1 = boxes[2]
    d = m.panel(img, boxes[2], 43)
    for i, (bx, col) in enumerate(((0.62, (120, 170, 120)), (0.72, (230, 150, 120)), (0.82, (120, 160, 210)))):
        d.rectangle([x0 + pw * bx, y0 + ph * 0.6, x0 + pw * bx + 40, y0 + ph * 0.86], fill=col, outline=m.INK, width=3)
    m.penguin(d, x0 + pw * 0.34, y0 + ph * 0.7, 140, "happy", hat_on=False)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.34, y0 + 250),
                 "I'm not procrastinating.\nI'm just reorganizing\nmy priorities.", "優先順位を整理してるだけ", 4)
    m.sfx(img, (x0 + pw * 0.8, y0 + ph * 0.48), "*tidy tidy*", 28, (200, 140, 60), 8)
    # 4:部長も、紙の山の上で昼寝
    x0, y0, x1, y1 = boxes[3]
    d = m.panel(img, boxes[3], 44)
    papers(d, x0 + pw * 0.62, y0 + ph * 0.9, 8, seed=320)
    m.capybara(d, x0 + pw * 0.62, y0 + ph * 0.7, 150, "calm")
    m.owl(d, x0 + pw * 0.2, y0 + ph * 0.78, 95, "shock")
    bot = small_bubble(d, (x0 + 12, y0 + 12, x0 + pw - 12, 0), (x0 + pw * 0.6, y0 + ph * 0.52),
                       "Zzz... deadlines are\nmerely suggestions.", "締め切りなんて、ただの目安さ", 5)
    small_bubble(d, (x0 + 12, bot + 10, x0 + pw * 0.5, 0), (x0 + pw * 0.2, y0 + ph * 0.66),
                 "Not you too, Boss!", "部長まで!", 6)
    m.sfx(img, (x0 + pw * 0.86, y0 + ph * 0.58), "Zzz", 34, (110, 120, 140), -8)
    d = ImageDraw.Draw(img)
    d.text((m.W - 50, m.H - 30), "@yonkoma_eigo", font=m.EN(30), fill=(160, 150, 140), anchor="rm")
    return img


def explain_card(sc):
    """解説:ターゲット単語+例文+今回出てきた単語。"""
    img = Image.new("RGB", (m.W, m.H), BG)
    d = ImageDraw.Draw(img)
    for x in range(0, m.W, 54):
        d.line([(x, 0), (x, m.H)], fill=(225, 220, 212), width=2)
    for y in range(0, m.H, 54):
        d.line([(0, y), (m.W, y)], fill=(225, 220, 212), width=2)
    f = m.EN(118)
    while f.getlength(sc["word"]) > m.W - 140:
        f = m.EN(f.size - 4)
    d.text((m.W // 2, 200), sc["word"], font=f, fill=m.INK, anchor="mm")
    d.line(m.wob([(200, 270), (880, 264)], amp=2), fill=(200, 52, 48), width=7)
    d.text((m.W // 2, 350), f"= {sc['meaning']}", font=m.JP(52), fill=(200, 52, 48), anchor="mm")
    d.text((m.W // 2, 450), sc["level"], font=m.JP(30), fill=(130, 120, 110), anchor="mm")
    d.text((m.W // 2, 560), sc["ex_en"], font=m.EN(42), fill=m.INK, anchor="mm")
    d.text((m.W // 2, 615), f"({sc['ex_ja']})", font=m.JP(30), fill=(120, 110, 105), anchor="mm")
    d.text((140, 740), "今回出てきた単語", font=m.JP(36), fill=m.INK, anchor="lm")
    for i, (en, ja) in enumerate(sc["words"]):
        y = 820 + i * 78
        d.text((160, y), en, font=m.EN(44), fill=m.INK, anchor="lm")
        d.text((560, y), ja, font=m.JP(30), fill=(110, 100, 95), anchor="lm")
    d.text((m.W // 2, 1250), "保存して、使ってみてね", font=m.JP(32), fill=(200, 52, 48), anchor="mm")
    d.text((m.W - 50, m.H - 30), "@yonkoma_eigo", font=m.EN(30), fill=(160, 150, 140), anchor="rm")
    return img


def mic(d, x, y, s=1.0):
    d.line([(x, y), (x + 34 * s, y + 70 * s)], fill=(60, 60, 70), width=int(10 * s))
    d.ellipse([x - 18 * s, y - 22 * s, x + 18 * s, y + 14 * s], fill=(190, 190, 200), outline=m.INK, width=3)


def sparkle(d, x, y, r=14, col=(240, 190, 60)):
    d.polygon([(x, y - r), (x + r * 0.3, y - r * 0.3), (x + r, y), (x + r * 0.3, y + r * 0.3), (x, y + r),
               (x - r * 0.3, y + r * 0.3), (x - r, y), (x - r * 0.3, y - r * 0.3)], fill=col)


def reluctant():
    img, boxes, pw, ph = m.comic("reluctant")
    # 1:部長のカラオケに誘われる
    x0, y0, x1, y1 = boxes[0]
    d = m.panel(img, boxes[0], 51)
    m.owl(d, x0 + pw * 0.28, y0 + ph * 0.76, 110, "happy")
    m.penguin(d, x0 + pw * 0.74, y0 + ph * 0.76, 110, "normal", hat_on=False)
    bot = small_bubble(d, (x0 + 12, y0 + 12, x0 + pw - 12, 0), (x0 + pw * 0.28, y0 + ph * 0.6),
                       "The boss invited us to his\nkaraoke party tonight.\nAre you coming?", "部長が今夜カラオケに誘ってくれたよ", 1)
    small_bubble(d, (x0 + 12, bot + 10, x0 + pw - 12, 0), (x0 + pw * 0.74, y0 + ph * 0.6),
                 "Hmm... I'm a bit reluctant.", "うーん…ちょっと気が進まない", 2)
    # 2:理由
    x0, y0, x1, y1 = boxes[1]
    d = m.panel(img, boxes[1], 52)
    m.owl(d, x0 + pw * 0.26, y0 + ph * 0.78, 110, "shock")
    m.penguin(d, x0 + pw * 0.74, y0 + ph * 0.76, 120, "smug", hat_on=False)
    m.sweat(d, x0 + pw * 0.88, y0 + ph * 0.56)
    bot = small_bubble(d, (x0 + 12, y0 + 14, x0 + pw * 0.75, 0), (x0 + pw * 0.26, y0 + ph * 0.62),
                       "Why? You love singing!", "なんで?歌うの好きじゃん!", 3)
    small_bubble(d, (x0 + pw * 0.2, bot + 10, x0 + pw - 12, 0), (x0 + pw * 0.74, y0 + ph * 0.6),
                 "He always sings for\nthree hours straight.", "部長、毎回3時間ぶっ通しで歌うの", 4)
    # 3:部長、やる気満々
    x0, y0, x1, y1 = boxes[2]
    d = m.panel(img, boxes[2], 53)
    m.capybara(d, x0 + pw * 0.56, y0 + ph * 0.74, 175, "calm")
    mic(d, x0 + pw * 0.26, y0 + ph * 0.66, 1.2)
    for sx, sy in ((0.14, 0.5), (0.86, 0.52), (0.78, 0.9)):
        sparkle(d, x0 + pw * sx, y0 + ph * sy)
    small_bubble(d, (x0 + 12, y0 + 14, x0 + pw - 12, 0), (x0 + pw * 0.5, y0 + ph * 0.56),
                 "Tonight's set list: 42 songs.\nAttendance is mandatory.", "今夜は42曲。出席は必須だ", 5)
    m.sfx(img, (x0 + pw * 0.82, y0 + ph * 0.42), "*sparkle*", 28, (200, 140, 60), 8)
    # 4:二人とも
    x0, y0, x1, y1 = boxes[3]
    d = m.panel(img, boxes[3], 54)
    m.owl(d, x0 + pw * 0.3, y0 + ph * 0.76, 115, "smug")
    m.penguin(d, x0 + pw * 0.72, y0 + ph * 0.76, 115, "smug", hat_on=False)
    bot = small_bubble(d, (x0 + 12, y0 + 12, x0 + pw * 0.8, 0), (x0 + pw * 0.3, y0 + ph * 0.6),
                       "Now I'm reluctant, too.", "…ぼくも気が進まなくなった", 6)
    small_bubble(d, (x0 + pw * 0.2, bot + 10, x0 + pw - 12, 0), (x0 + pw * 0.72, y0 + ph * 0.6),
                 "...Let's pretend\nwe have a cold.", "…風邪ってことにしよう", 7)
    m.sfx(img, (x0 + pw * 0.52, y0 + ph * 0.6), "*cough*", 28, (110, 120, 140), -6)
    d = ImageDraw.Draw(img)
    d.text((m.W - 50, m.H - 30), "@yonkoma_eigo", font=m.EN(30), fill=(160, 150, 140), anchor="rm")
    return img


def fish_box(d, cx, bottom, w=150, h=90, seed=330):
    """空っぽの魚の箱(FISH と書いた木箱)。"""
    m.shape(d, m.rrect_pts(cx - w / 2, bottom - h, cx + w / 2, bottom, 6), (214, 170, 120), w=4, seed=seed)
    d.line([(cx - w / 2 + 8, bottom - h + 22), (cx + w / 2 - 8, bottom - h + 22)], fill=(150, 110, 70), width=3)
    d.text((cx, bottom - h / 2 + 10), "FISH", font=m.EN(30), fill=(120, 80, 50), anchor="mm")


def fish_bones(d, cx, cy, w=90):
    d.line([(cx - w / 2, cy), (cx + w / 2, cy)], fill=(120, 120, 130), width=4)
    for i in range(4):
        x = cx - w * 0.3 + i * w * 0.18
        d.line([(x, cy - w * 0.16), (x + w * 0.06, cy), (x, cy + w * 0.16)], fill=(120, 120, 130), width=3)
    d.ellipse([cx - w / 2 - 16, cy - 13, cx - w / 2 + 8, cy + 13], outline=(120, 120, 130), width=4)
    d.polygon([(cx + w / 2, cy), (cx + w / 2 + 18, cy - 14), (cx + w / 2 + 18, cy + 14)], outline=(120, 120, 130))


def run_out_of():
    img, boxes, pw, ph = m.comic("run out of")
    # 1:おやつにしよう
    x0, y0, x1, y1 = boxes[0]
    d = m.panel(img, boxes[0], 61)
    m.owl(d, x0 + pw * 0.3, y0 + ph * 0.64, 150, "happy")
    m.penguin(d, x0 + pw * 0.74, y0 + ph * 0.68, 125, "happy", hat_on=False)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.3, y0 + 190),
                 "Let's have a snack!", "おやつにしよう!", 1)
    m.sfx(img, (x0 + pw * 0.86, y0 + ph * 0.42), "♪", 44, (220, 120, 120), 8)
    # 2:魚の箱が空っぽ(ターゲット)
    x0, y0, x1, y1 = boxes[1]
    d = m.panel(img, boxes[1], 62)
    fish_box(d, x0 + pw * 0.7, y0 + ph * 0.9)
    m.penguin(d, x0 + pw * 0.32, y0 + ph * 0.64, 160, "shock", hat_on=False)
    m.sweat(d, x0 + pw * 0.5, y0 + ph * 0.44)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.32, y0 + 225),
                 "Oh no!\nWe ran out of fish!", "えっ!魚、切らしてる!", 2)
    m.sfx(img, (x0 + pw * 0.72, y0 + ph * 0.6), "empty...", 30, (110, 120, 140), -6)
    # 3:誰が食べたの?
    x0, y0, x1, y1 = boxes[2]
    d = m.panel(img, boxes[2], 63)
    m.owl(d, x0 + pw * 0.3, y0 + ph * 0.64, 150, "shock")
    m.penguin(d, x0 + pw * 0.72, y0 + ph * 0.7, 115, "shock", hat_on=False)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.3, y0 + 190),
                 "Who ate them all?", "全部食べたの、誰?", 3)
    m.sfx(img, (x0 + pw * 0.86, y0 + ph * 0.4), "?!", 50, (220, 80, 70), 10)
    # 4:骨の山の横で、部長がしれっと
    x0, y0, x1, y1 = boxes[3]
    d = m.panel(img, boxes[3], 64)
    m.capybara(d, x0 + pw * 0.6, y0 + ph * 0.64, 200, "calm")
    fish_bones(d, x0 + pw * 0.2, y0 + ph * 0.92, 80)
    fish_bones(d, x0 + pw * 0.16, y0 + ph * 0.84, 70)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.46, y0 + 190),
                 "...Not me.", "…私じゃないよ", 4)
    m.sfx(img, (x0 + pw * 0.86, y0 + ph * 0.52), "*munch*", 30, (200, 140, 60), 8)
    d = ImageDraw.Draw(img)
    d.text((m.W - 50, m.H - 30), "@yonkoma_eigo", font=m.EN(30), fill=(160, 150, 140), anchor="rm")
    return img


SCRIPTS = {
    "procrastinate": dict(
        draw=procrastinate, word="procrastinate", hook="先延ばしグセ、ある?",
        meaning="(やるべきことを)先延ばしにする", level="英検準1級レベル",
        ex_en="I always procrastinate on my taxes.", ex_ja="税金の手続きを、いつも後回しにしてしまう",
        words=[("due", "(提出物などが)期限の"), ("under pressure", "追い込まれて、プレッシャーの中で"),
               ("priorities", "優先順位、優先事項"), ("merely", "ただ〜にすぎない"), ("deadline", "締め切り")],
        panels=[[("navi", "Your report is due tomorrow. Shouldn't you get started?"), ("pen", "Relax. I work better under pressure.")],
                [("navi", "You said that yesterday! Stop procrastinating!")],
                [("pen", "I'm not procrastinating. I'm just reorganizing my priorities.")],
                [("boss", "Zzz... deadlines are merely suggestions."), ("navi", "Not you too, Boss!")]],
        explain=[("navi", "Procrastinate."), ("pen", "I always procrastinate on my taxes.")],
    ),
    "reluctant": dict(
        draw=reluctant, word="reluctant", hook="行きたくない誘い、ある?",
        meaning="気が進まない、しぶしぶの", level="英検2級〜準1級レベル",
        ex_en="He was reluctant to admit his mistake.", ex_ja="彼は自分のミスを認めるのに気が進まなかった",
        words=[("invite", "招待する、誘う"), ("~ straight", "〜ぶっ通しで、連続で"), ("attendance", "出席"),
               ("mandatory", "必須の、義務の"), ("pretend", "〜のふりをする")],
        panels=[[("navi", "The boss invited us to his karaoke party tonight. Are you coming?"), ("pen", "Hmm... I'm a bit reluctant.")],
                [("navi", "Why? You love singing!"), ("pen", "He always sings for three hours straight.")],
                [("boss", "Tonight's set list: forty-two songs. Attendance is mandatory.")],
                [("navi", "Now I'm reluctant, too."), ("pen", "...Let's pretend we have a cold.")]],
        explain=[("navi", "Reluctant."), ("pen", "He was reluctant to admit his mistake.")],
    ),
}


# 紙芝居版で作った4コマを、同じ絵のままテンポの速い版にする(1コマ1セリフ)
def _from_reel(name, **kw):
    import manga_reel as mr
    old = mr.SCRIPTS[name]
    return dict(draw=getattr(m, name), panels=[[line] for line in old["lines"]], explain=old["explain"], **kw)


SCRIPTS.update({
    "run_out_of": dict(
        draw=run_out_of, word="run out of", hook="「切らしちゃった」英語で?",
        meaning="〜を切らす、使い果たす", level="英検準2級〜2級レベル",
        ex_en="We ran out of milk, so I went to the store.", ex_ja="牛乳を切らしたので、お店に行った",
        words=[("snack", "おやつ、軽食"), ("ran", "run の過去形"), ("ate", "eat(食べる)の過去形"),
               ("them all", "それらを全部"), ("Not me.", "私じゃないよ")],
        panels=[[("navi", "Let's have a snack!")], [("pen", "Oh no! We ran out of fish!")],
                [("navi", "Who ate them all?")], [("boss", "...Not me.")]],
        explain=[("navi", "Run out of."), ("pen", "We ran out of milk, so I went to the store.")],
    ),
    "baggage_claim": _from_reel(
        "baggage_claim", word="baggage claim", hook="空港の「荷物の受取所」は?",
        meaning="手荷物受取所", level="TOEIC頻出",
        ex_en="I waited at baggage claim for twenty minutes.", ex_ja="手荷物受取所で20分待った",
        words=[("baggage", "手荷物"), ("claim", "(自分の物として)受け取る"), ("suitcase", "スーツケース"),
               ("ride", "乗り物"), ("Let's go to ~", "〜へ行こう")]),
    "wet_to_the_skin": _from_reel(
        "wet_to_the_skin", word="wet to the skin", hook="「ずぶぬれ」って英語で?",
        meaning="ずぶぬれ", level="英検2級レベル",
        ex_en="I forgot my umbrella and got wet to the skin.", ex_ja="傘を忘れて、ずぶぬれになった",
        words=[("umbrella", "傘"), ("No need.", "必要ないよ"), ("penguin", "ペンギン"),
               ("sea", "海"), ("forgot", "forget(忘れる)の過去形")]),
    "from_time_to_time": _from_reel(
        "from_time_to_time", word="from time to time", hook="「ときどき」って英語で?",
        meaning="ときどき", level="英検3級〜準2級レベル",
        ex_en="We still meet for coffee from time to time.", ex_ja="今でもときどきお茶をする",
        words=[("exercise", "運動する"), ("workout", "運動、トレーニング"), ("slide", "すべる"),
               ("just", "ただ〜だけ"), ("still", "今でも")]),
    "lead_a_workshop": _from_reel(
        "lead_a_workshop", word="lead a workshop", hook="研修の担当、英語で?",
        meaning="研修を担当する", level="TOEIC頻出",
        ex_en="I'll lead a short workshop for new staff.", ex_ja="新人向けに短い研修を担当する",
        words=[("lead", "率いる、担当する"), ("workshop", "研修、講習会"), ("topic", "テーマ、話題"),
               ("step one", "その1、最初の手順"), ("staff", "職員、スタッフ")]),
    "make_an_appointment": _from_reel(
        "make_an_appointment", word="make an appointment", hook="「アポを取る」英語で?",
        meaning="(人と会う)約束をする", level="TOEIC頻出",
        ex_en="I need to make an appointment with my dentist.", ex_ja="歯医者さんの予約を取らないと",
        words=[("appointment", "(人と会う)約束、予約"), ("at three", "3時に"), ("Sunday", "日曜日"),
               ("need to ~", "〜する必要がある"), ("dentist", "歯医者")]),
})


def jitter(src, rng, scale=1.0, area=(980, 1350), top=300):
    """1コマごとに、わずかにずらして傾ける(ストップモーション風)。"""
    tw = int(area[0] * scale)
    th = int(src.height * tw / src.width)
    im = src.resize((tw, th), Image.LANCZOS)
    img = Image.new("RGB", (W, H), BG)
    x = (W - tw) // 2
    y = top + (area[1] - th) // 2
    img.paste(im, (x, y))
    return img


def title_frame(word, hook, t, rng):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    s = 1.0 + max(0, 0.25 - t) * 0.8  # 出てきた瞬間だけ少し大きく
    f = m.EN(int(120 * s))
    while f.getlength(word) > W - 160:
        f = m.EN(f.size - 4)
    d.text((W // 2, 820), word, font=f, fill=m.INK, anchor="mm")
    d.line(m.wob([(200, 900), (880, 894)], amp=2, seed=1), fill=(200, 52, 48), width=8)
    d.text((W // 2, 1010), hook, font=m.JP(58), fill=(200, 52, 48), anchor="mm")
    d.text((W // 2, 1100), "4コマで覚える英語", font=m.JP(34), fill=(150, 140, 130), anchor="mm")
    return img


def panel_frame(src, t, rng, label, hook=None):
    # 切り替えた瞬間は少し寄って、0.15秒で止まる
    scale = 1.06 if t < 0.15 else 1.0
    img = jitter(src, rng, scale)
    d = ImageDraw.Draw(img)
    if hook:
        # 問いかけを上に大きく(タイトル画面のかわり)
        f = m.JP(76)
        while f.getlength(hook) > W - 100:
            f = m.JP(f.size - 4)
        d.rounded_rectangle((40, 95, W - 40, 285), radius=28, fill=(200, 52, 48))
        d.text((W // 2, 190), hook, font=f, fill=(255, 255, 255), anchor="mm")
        return img
    d.text((W // 2, 170), label, font=m.EN(80), fill=m.INK, anchor="mm")
    d.text((W // 2, 245), "4コマで覚える英語", font=m.JP(36), fill=(150, 140, 130), anchor="mm")
    return img


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    name = args[0] if args else "procrastinate"
    hook = "--hook" in sys.argv
    sc = SCRIPTS[name]
    OUT.mkdir(parents=True, exist_ok=True)
    comic = sc["draw"]()
    boxes = comic.info["boxes"]
    card = explain_card(sc)
    comic.save(OUT / f"{name}_1.png")
    card.save(OUT / f"{name}_2.png")
    mr.load_env()
    def voice(who, text):
        # 声ごとの大きさの差をなくす(RMS をそろえ、ピークは0.95まで)
        a = mr.eleven(who, text, SPEED)
        rms = float(np.sqrt(np.mean(a ** 2))) or 1.0
        a = a * (0.09 / rms)
        peak = float(np.max(np.abs(a))) or 1.0
        return (a * min(1.0, 0.95 / peak)).astype(np.float32)

    scenes, audio = [], []  # (種類, 画像, 秒)
    crops = [comic.crop(tuple(int(v) for v in box)) for box in boxes]
    if hook:
        # オチを0.6秒だけ見せて「なんでこうなった?」と思わせる
        scenes.append(("tease", crops[3], 0.6))
        audio += [mr.pop(), mr.silence(0.6 - len(mr.pop()) / SR)]
    else:
        hook_len = 1.1
        scenes.append(("title", None, hook_len))
        audio += [mr.pop(), mr.silence(hook_len - len(mr.pop()) / SR)]
    for i, (src, lines) in enumerate(zip(crops, sc["panels"])):
        clips = []
        for who, text in lines:
            clips += [voice(who, text), mr.silence(0.18)]
        clip = np.concatenate([mr.pop(), mr.silence(0.12)] + clips)
        scenes.append(("hooked" if hook and i == 0 else "panel", src, len(clip) / SR))
        audio.append(clip)
    scenes.append(("panel_all", comic, 1.0))
    audio.append(mr.silence(1.0))
    ex = [mr.pop(), mr.silence(0.2)]
    for who, text in sc["explain"]:
        ex += [voice(who, text), mr.silence(0.35)]
    ex.append(mr.silence(1.2))
    ex = np.concatenate(ex)
    scenes.append(("explain", card, len(ex) / SR))
    audio.append(ex)
    total = sum(s[2] for s in scenes)

    out = OUT / f"{name}_fast{'_hook' if hook else ''}.mp4"
    rng = random.Random(7)
    grid_bg = Image.new("RGB", (W, H), BG)
    g = ImageDraw.Draw(grid_bg)
    for x in range(0, W, 54):
        g.line([(x, 0), (x, H)], fill=(225, 220, 212), width=2)
    for y in range(0, H, 54):
        g.line([(0, y), (W, y)], fill=(225, 220, 212), width=2)
    with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
        import soundfile as sf
        sf.write(wav.name, np.concatenate(audio), SR)
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-i", wav.name, "-stream_loop", "-1", "-i", str(BGM),
               "-filter_complex", f"[2:a]volume={BGM_VOLUME},afade=t=in:d=1,afade=t=out:st={total - 1.5}:d=1.5[b];"
               "[1:a]aresample=44100,volume=1.5[v];[v][b]amix=inputs=2:duration=first:normalize=0[a]",
               "-map", "0:v", "-map", "[a]", "-t", f"{total:.2f}",
               "-r", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "aac", "-movflags", "+faststart", str(out)]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for kind, src, dur in scenes:
            for i in range(round(dur * FPS)):
                t = i / FPS
                if kind == "title":
                    f = title_frame(sc["word"], sc["hook"], t, rng)
                elif kind == "explain":
                    f = grid_bg.copy()
                    f.paste(src, (0, 285))
                else:
                    f = panel_frame(src, t, rng, sc["word"], sc["hook"] if kind in ("tease", "hooked") else None)
                proc.stdin.write(f.tobytes())
        proc.stdin.close()
        proc.wait()
    print(f"✓ {out}({total:.1f}秒)/ 4コマ {name}_1.png・解説 {name}_2.png")


if __name__ == "__main__":
    main()
