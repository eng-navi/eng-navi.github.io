"""テンポの速い4コマ(ストップモーション風の揺れつき)。1本につきターゲット単語は1つ、ほかにも使える単語を数個。

    .venv-tts/bin/python manga_fast.py procrastinate      # out/manga/procrastinate_fast.mp4 と 4コマ・解説の画像
    .venv-tts/bin/python manga_fast.py procrastinate --hook   # 冒頭を変えた版(procrastinate_fast_hook.mp4)

・--hook:文字だけのタイトル画面をやめて、0秒目から1コマ目。問いかけは1コマ目のあいだ上に大きく重ねる

・最初の約1秒でターゲット単語を見せる(つかみ)。コマの切り替えは「パッ」と寄って止まる
・画面は揺らさない。声の大きさはそろえ、後ろにかすかなBGM
・セリフはコマごとに1〜2つ。ElevenLabs の声を少し速め(speed 1.1)で
"""
import math
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
W, H, FPS, SR = 1080, 1920, 30, 24000  # 帯のアニメを滑らかにするため30コマ(絵は止まっているので見た目は同じ)
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


def sweater(d, cx, cy, w, seed=340):
    """しましまのセーター。cy は胴の中心。"""
    h = w * 0.8
    for k in (-1, 1):  # そで
        m.shape(d, [(cx + k * w * 0.42, cy - h * 0.42), (cx + k * w * 0.78, cy + h * 0.1), (cx + k * w * 0.6, cy + h * 0.22),
                    (cx + k * w * 0.4, cy - h * 0.05)], (230, 120, 110), w=3, seed=seed + 1 + k)
    m.shape(d, m.rrect_pts(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, w * 0.14), (230, 120, 110), w=4, seed=seed)
    for i in (1, 2):
        y = cy - h / 2 + i * h / 3
        d.line([(cx - w / 2 + 6, y), (cx + w / 2 - 6, y)], fill=(255, 225, 200), width=max(4, int(w * 0.06)))


def outgrow():
    img, boxes, pw, ph = m.comic("outgrow")
    # 1:お気に入りのセーター
    x0, y0, x1, y1 = boxes[0]
    d = m.panel(img, boxes[0], 71)
    m.penguin(d, x0 + pw * 0.34, y0 + ph * 0.66, 150, "happy", hat_on=False)
    sweater(d, x0 + pw * 0.74, y0 + ph * 0.7, 120)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.34, y0 + 210),
                 "Look! My favorite\nsweater!", "見て!お気に入りのセーター!", 1)
    m.sfx(img, (x0 + pw * 0.86, y0 + ph * 0.46), "♪", 44, (220, 120, 120), 8)
    # 2:着てみたら、きつい
    x0, y0, x1, y1 = boxes[1]
    d = m.panel(img, boxes[1], 72)
    cx, cy, s = x0 + pw * 0.5, y0 + ph * 0.64, 175
    m.penguin(d, cx, cy, s, "shock", hat_on=False)
    sweater(d, cx, cy + s * 0.12, s * 0.62, 341)
    m.sweat(d, cx + s * 0.5, cy - s * 0.3)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (cx, y0 + 190), "Huh?\nIt's so tight...", "あれ?きつい…", 2)
    m.sfx(img, (x0 + pw * 0.2, y0 + ph * 0.9), "*squeeze*", 28, (200, 140, 60), 8)
    # 3:大きくなって着られなくなった(ターゲット)
    x0, y0, x1, y1 = boxes[2]
    d = m.panel(img, boxes[2], 73)
    m.owl(d, x0 + pw * 0.3, y0 + ph * 0.66, 150, "smug")
    m.penguin(d, x0 + pw * 0.74, y0 + ph * 0.7, 120, "shock", hat_on=False)
    sweater(d, x0 + pw * 0.74, y0 + ph * 0.7 + 14, 74, 342)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.3, y0 + 190),
                 "You've outgrown it.", "大きくなって、着られなくなったね", 3)
    # 4:部長がぴったり着ている
    x0, y0, x1, y1 = boxes[3]
    d = m.panel(img, boxes[3], 74)
    cx, cy, s = x0 + pw * 0.62, y0 + ph * 0.66, 200
    m.capybara(d, cx, cy, s, "calm")
    m.shape(d, m.rrect_pts(cx - s * 0.12, cy - s * 0.24, cx + s * 0.5, cy + s * 0.38, s * 0.12), (230, 120, 110), w=4, seed=343)
    for i in (1, 2):
        y = cy - s * 0.24 + i * s * 0.62 / 3
        d.line([(cx - s * 0.1, y), (cx + s * 0.48, y)], fill=(255, 225, 200), width=8)
    m.owl(d, x0 + pw * 0.16, y0 + ph * 0.84, 90, "shock")
    bot = small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (cx, y0 + ph * 0.5), "Fits perfectly.", "ぴったりだ", 4)
    small_bubble(d, (x0 + 12, bot + 14, x0 + pw * 0.5, 0), (x0 + pw * 0.16, y0 + ph * 0.72), "Boss?!", "部長!?", 5)
    m.sfx(img, (x0 + pw * 0.88, y0 + ph * 0.92), "*snug*", 30, (200, 140, 60), 8)
    return m._end(img)


def kotatsu(d, cx, top, w, seed=350):
    """コタツ(天板+ふとん)。キャラを描いたあとに描くと、下半身がふとんに隠れる。"""
    m.shape(d, m.rrect_pts(cx - w / 2, top + 14, cx + w / 2, top + w * 0.42, 18), (240, 180, 120), seed=seed)
    for k in (-0.25, 0, 0.25):
        d.line([(cx + k * w, top + 30), (cx + k * w, top + w * 0.4)], fill=(225, 150, 100), width=3)
    m.shape(d, m.rrect_pts(cx - w * 0.56, top, cx + w * 0.56, top + 22, 6), (190, 140, 95), seed=seed + 1)


def cant_bring_myself_to():
    img, boxes, pw, ph = m.comic("can't bring myself to")
    # 1:勉強の時間だよ
    x0, y0, x1, y1 = boxes[0]
    d = m.panel(img, boxes[0], 75)
    m.owl(d, x0 + pw * 0.24, y0 + ph * 0.66, 140, "normal")
    m.penguin(d, x0 + pw * 0.68, y0 + ph * 0.62, 120, "happy", hat_on=False)
    kotatsu(d, x0 + pw * 0.68, y0 + ph * 0.7, 250)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.24, y0 + 190), "Time to study!", "勉強の時間だよ!", 1)
    # 2:コタツから出る気になれない(ターゲット)
    x0, y0, x1, y1 = boxes[1]
    d = m.panel(img, boxes[1], 76)
    m.penguin(d, x0 + pw * 0.5, y0 + ph * 0.6, 170, "happy", hat_on=False)
    kotatsu(d, x0 + pw * 0.5, y0 + ph * 0.72, 330, 351)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.5, y0 + 220),
                 "I can't bring myself\nto leave the kotatsu.", "コタツから出る気になれない…", 2)
    m.sfx(img, (x0 + pw * 0.84, y0 + ph * 0.5), "*cozy*", 30, (220, 120, 90), 8)
    # 3:ほら、出て!
    x0, y0, x1, y1 = boxes[2]
    d = m.panel(img, boxes[2], 77)
    m.owl(d, x0 + pw * 0.26, y0 + ph * 0.66, 140, "shock")
    m.penguin(d, x0 + pw * 0.7, y0 + ph * 0.62, 120, "shock", hat_on=False)
    kotatsu(d, x0 + pw * 0.7, y0 + ph * 0.7, 240, 352)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.26, y0 + 190), "Come on! Get out!", "ほら、出て!", 3)
    m.sfx(img, (x0 + pw * 0.48, y0 + ph * 0.5), "*tug*", 34, (200, 140, 60), -8)
    # 4:ナビも入って、あと5分
    x0, y0, x1, y1 = boxes[3]
    d = m.panel(img, boxes[3], 78)
    m.owl(d, x0 + pw * 0.32, y0 + ph * 0.6, 130, "happy")
    m.penguin(d, x0 + pw * 0.7, y0 + ph * 0.62, 120, "happy", hat_on=False)
    kotatsu(d, x0 + pw * 0.5, y0 + ph * 0.72, 380, 353)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.32, y0 + 210),
                 "...Okay.\nFive more minutes.", "…あと5分だけね", 4)
    m.sfx(img, (x0 + pw * 0.86, y0 + ph * 0.5), "*warm*", 30, (220, 120, 90), 8)
    return m._end(img)


def get_stuck_in_traffic():
    img, boxes, pw, ph = m.comic("get stuck in traffic", series="toeic")
    # 1:会議なのに部長がいない
    x0, y0, x1, y1 = boxes[0]
    d = m.panel(img, boxes[0], 85)
    m.clock(d, x0 + pw * 0.8, y0 + ph * 0.5, 42)
    m.owl(d, x0 + pw * 0.34, y0 + ph * 0.68, 150, "normal")
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.34, y0 + 220),
                 "The meeting starts at 10.\nWhere's the boss?", "会議は10時から。部長は?", 1)
    # 2:渋滞にはまったって(ターゲット)
    x0, y0, x1, y1 = boxes[1]
    d = m.panel(img, boxes[1], 86)
    m.penguin(d, x0 + pw * 0.44, y0 + ph * 0.66, 165, "normal", hat_on=False)
    phone(d, x0 + pw * 0.62, y0 + ph * 0.58)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.44, y0 + 220),
                 "He says he got stuck\nin traffic.", "渋滞にはまったって", 2)
    m.sfx(img, (x0 + pw * 0.84, y0 + ph * 0.5), "*ring*", 30, (110, 120, 140), 8)
    # 3:徒歩通勤なのに?
    x0, y0, x1, y1 = boxes[2]
    d = m.panel(img, boxes[2], 87)
    m.owl(d, x0 + pw * 0.3, y0 + ph * 0.66, 150, "shock")
    m.penguin(d, x0 + pw * 0.74, y0 + ph * 0.7, 115, "normal", hat_on=False)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.3, y0 + 220),
                 "Again?\nHe walks to work!", "また?歩いて通勤なのに!", 3)
    m.sfx(img, (x0 + pw * 0.56, y0 + ph * 0.46), "?!", 50, (220, 80, 70), 10)
    # 4:カピバラの行列で、道が渋滞
    x0, y0, x1, y1 = boxes[3]
    d = m.panel(img, boxes[3], 88)
    d.rectangle([x0 + 6, y0 + ph * 0.6, x1 - 6, y0 + ph * 0.94], fill=(185, 185, 190))
    for k in range(5):
        xx = x0 + 20 + k * pw / 5
        d.line([(xx, y0 + ph * 0.77), (xx + pw / 10, y0 + ph * 0.77)], fill=(255, 255, 255), width=6)
    for k, fx in enumerate((0.2, 0.5, 0.8)):
        m.capybara(d, x0 + pw * fx, y0 + ph * 0.72, 125, "calm", seed=91 + k * 7)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.5, y0 + ph * 0.6),
                 "Heavy traffic today.", "今日は混んでるねぇ", 4)
    m.sfx(img, (x0 + pw * 0.5, y0 + ph * 0.5), "*slow*", 30, (110, 120, 140), -6)
    return m._end(img)


SCRIPTS.update({
    "outgrow": dict(
        draw=outgrow, word="outgrow", hook="「服が着られなくなった」英語で?",
        meaning="(成長して)〜が合わなくなる", level="英検2級レベル",
        ex_en="Kids outgrow their shoes so fast.", ex_ja="子どもはすぐに靴が合わなくなる",
        words=[("favorite", "お気に入りの"), ("tight", "きつい"), ("outgrown", "outgrow の過去分詞"),
               ("fit", "(サイズが)合う"), ("perfectly", "ぴったり、完璧に")],
        panels=[[("pen", "Look! My favorite sweater!")], [("pen", "Huh? It's so tight...")],
                [("navi", "You've outgrown it.")], [("boss", "Fits perfectly."), ("navi", "Boss?!")]],
        explain=[("navi", "Outgrow."), ("pen", "Kids outgrow their shoes so fast.")],
    ),
    "cant_bring_myself_to": dict(
        draw=cant_bring_myself_to, word="can't bring myself to", hook="「コタツから出られない」英語で?",
        meaning="どうしても〜する気になれない", level="英検準1級レベル",
        ex_en="I can't bring myself to delete old photos.", ex_ja="昔の写真を、どうしても消す気になれない",
        words=[("Time to ~", "〜の時間だ"), ("leave", "〜から出る、離れる"), ("Come on!", "ほら、さあ"),
               ("get out", "外に出る"), ("five more minutes", "あと5分")],
        panels=[[("navi", "Time to study!")], [("pen", "I can't bring myself to leave the kotatsu.")],
                [("navi", "Come on! Get out!")], [("navi", "...Okay. Five more minutes.")]],
        explain=[("navi", "Can't bring myself to."), ("pen", "I can't bring myself to delete old photos.")],
    ),
    "get_stuck_in_traffic": dict(
        draw=get_stuck_in_traffic, word="get stuck in traffic", hook="「渋滞にはまる」英語で?",
        meaning="渋滞にはまる", level="TOEIC頻出",
        ex_en="I got stuck in traffic this morning.", ex_ja="今朝、渋滞にはまった",
        words=[("meeting", "会議"), ("start at ~", "〜時に始まる"), ("He says ~", "〜だって(伝え聞き)"),
               ("walk to work", "歩いて通勤する"), ("heavy traffic", "ひどい渋滞")],
        panels=[[("navi", "The meeting starts at ten. Where's the boss?")], [("pen", "He says he got stuck in traffic.")],
                [("navi", "Again? He walks to work!")], [("boss", "Heavy traffic today.")]],
        explain=[("navi", "Get stuck in traffic."), ("pen", "I got stuck in traffic this morning.")],
    ),
})


def backpack(d, cx, cy, s, seed=360):
    """大荷物のリュック(傘と浮き輪つき)。ペンより先に描く。"""
    m.umbrella(d, cx + s * 0.2, cy - s * 0.95, s * 0.5)
    m.shape(d, m.rrect_pts(cx - s * 0.45, cy - s * 0.6, cx + s * 0.45, cy + s * 0.55, s * 0.18), (150, 120, 90), seed=seed)
    d.line([(cx - s * 0.3, cy - s * 0.1), (cx + s * 0.3, cy - s * 0.1)], fill=(110, 85, 60), width=4)
    r = s * 0.3
    d.ellipse([cx + s * 0.25 - r, cy + s * 0.15 - r, cx + s * 0.25 + r, cy + s * 0.15 + r], fill=(240, 110, 100), outline=m.INK, width=4)
    d.ellipse([cx + s * 0.25 - r * 0.45, cy + s * 0.15 - r * 0.45, cx + s * 0.25 + r * 0.45, cy + s * 0.15 + r * 0.45], fill=(150, 120, 90), outline=m.INK, width=3)


def shop(d, cx, bottom, w, seed=370):
    h = w * 0.8
    m.shape(d, m.rrect_pts(cx - w / 2, bottom - h, cx + w / 2, bottom, 6), (250, 246, 236), seed=seed)
    for k in range(6):  # しましまのひさし
        x = cx - w / 2 + k * w / 6
        d.rectangle([x, bottom - h, x + w / 6, bottom - h + w * 0.16], fill=(120, 180, 140) if k % 2 else (255, 255, 255), outline=m.INK, width=2)
    d.text((cx, bottom - h + w * 0.3), "STORE", font=m.EN(int(w * 0.16)), fill=(70, 110, 170), anchor="mm")
    d.rectangle([cx - w * 0.16, bottom - h * 0.48, cx + w * 0.16, bottom], fill=(190, 220, 235), outline=m.INK, width=3)


def just_in_case():
    img, boxes, pw, ph = m.comic("just in case")
    # 1:準備できた!
    x0, y0, x1, y1 = boxes[0]
    d = m.panel(img, boxes[0], 91)
    backpack(d, x0 + pw * 0.62, y0 + ph * 0.66, 170)
    m.penguin(d, x0 + pw * 0.42, y0 + ph * 0.68, 140, "happy", hat_on=False)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.42, y0 + 170), "I'm ready to go!", "準備できた!", 1)
    # 2:なんで大荷物?念のため(ターゲット)
    x0, y0, x1, y1 = boxes[1]
    d = m.panel(img, boxes[1], 92)
    m.owl(d, x0 + pw * 0.22, y0 + ph * 0.76, 110, "shock")
    backpack(d, x0 + pw * 0.74, y0 + ph * 0.74, 130, 361)
    m.penguin(d, x0 + pw * 0.6, y0 + ph * 0.76, 110, "smug", hat_on=False)
    bot = small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.22, y0 + 140),
                       "Why is your bag so big?", "なんでそんなに大荷物?", 2)
    small_bubble(d, (x0 + pw * 0.3, bot + 10, x0 + pw - 12, 0), (x0 + pw * 0.6, y0 + ph * 0.6), "Just in case.", "念のため", 3)
    # 3:どこに行くの?
    x0, y0, x1, y1 = boxes[2]
    d = m.panel(img, boxes[2], 93)
    m.owl(d, x0 + pw * 0.3, y0 + ph * 0.66, 150, "normal")
    backpack(d, x0 + pw * 0.8, y0 + ph * 0.72, 120, 362)
    m.penguin(d, x0 + pw * 0.68, y0 + ph * 0.74, 105, "happy", hat_on=False)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.3, y0 + 190), "Where are you going?", "どこに行くの?", 4)
    # 4:隣のお店まで
    x0, y0, x1, y1 = boxes[3]
    d = m.panel(img, boxes[3], 94)
    shop(d, x0 + pw * 0.74, y0 + ph * 0.92, 210)
    backpack(d, x0 + pw * 0.4, y0 + ph * 0.72, 120, 363)
    m.penguin(d, x0 + pw * 0.28, y0 + ph * 0.74, 105, "happy", hat_on=False)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.28, y0 + 160), "To the store next door.", "隣のお店まで", 5)
    m.sfx(img, (x0 + pw * 0.56, y0 + ph * 0.94), "5 m", 30, (110, 120, 140), 0)
    return m._end(img)


def hearts(img, x, y):
    d = ImageDraw.Draw(img)
    for dx, dy, r in ((0, 0, 16), (44, -36, 12), (-36, -50, 10)):
        cx, cy = x + dx, y + dy
        d.ellipse([cx - r * 2, cy - r, cx, cy + r], fill=(235, 110, 140))
        d.ellipse([cx, cy - r, cx + r * 2, cy + r], fill=(235, 110, 140))
        d.polygon([(cx - r * 1.95, cy + r * 0.3), (cx + r * 1.95, cy + r * 0.3), (cx, cy + r * 2.4)], fill=(235, 110, 140))


def have_a_crush_on():
    img, boxes, pw, ph = m.comic("have a crush on")
    # 1:好きな人がいるの(ターゲット)
    x0, y0, x1, y1 = boxes[0]
    d = m.panel(img, boxes[0], 95)
    m.penguin(d, x0 + pw * 0.5, y0 + ph * 0.66, 170, "happy", hat_on=False)
    hearts(img, x0 + pw * 0.8, y0 + ph * 0.5)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.5, y0 + 200),
                 "I have a crush\non someone...", "好きな人がいるの…", 1)
    # 2:えっ、誰?
    x0, y0, x1, y1 = boxes[1]
    d = m.panel(img, boxes[1], 96)
    m.owl(d, x0 + pw * 0.5, y0 + ph * 0.66, 170, "shock")
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.5, y0 + 180), "Really? Who?", "えっ、誰?", 2)
    m.sfx(img, (x0 + pw * 0.84, y0 + ph * 0.44), "!?", 50, (220, 80, 70), 10)
    # 3:クールで、つやつやで、銀色で…
    x0, y0, x1, y1 = boxes[2]
    d = m.panel(img, boxes[2], 97)
    m.penguin(d, x0 + pw * 0.5, y0 + ph * 0.68, 160, "happy", hat_on=False)
    hearts(img, x0 + pw * 0.18, y0 + ph * 0.52)
    hearts(img, x0 + pw * 0.84, y0 + ph * 0.56)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.5, y0 + 220),
                 "He's cool, shiny,\nand silver...", "クールで、つやつやで、銀色で…", 3)
    # 4:正体はマグロ
    x0, y0, x1, y1 = boxes[3]
    d = m.panel(img, boxes[3], 98)
    m.fish(d, x0 + pw * 0.62, y0 + ph * 0.7, 220)
    m.penguin(d, x0 + pw * 0.46, y0 + ph * 0.68, 120, "happy", hat_on=False)
    m.owl(d, x0 + pw * 0.16, y0 + ph * 0.8, 90, "shock")
    hearts(img, x0 + pw * 0.8, y0 + ph * 0.5)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.2, y0 + ph * 0.64), "That's your lunch!", "それ、お昼ごはん!", 4)
    return m._end(img)


def controller(d, cx, cy, w, seed=380):
    m.shape(d, m.rrect_pts(cx - w / 2, cy - w * 0.25, cx + w / 2, cy + w * 0.25, w * 0.22), (90, 95, 110), w=3, seed=seed)
    d.line([(cx - w * 0.3, cy), (cx - w * 0.14, cy)], fill=(240, 240, 240), width=5)
    d.line([(cx - w * 0.22, cy - w * 0.08), (cx - w * 0.22, cy + w * 0.08)], fill=(240, 240, 240), width=5)
    for dx, col in ((0.18, (230, 90, 80)), (0.3, (90, 170, 220))):
        d.ellipse([cx + w * dx - 6, cy - 6, cx + w * dx + 6, cy + 6], fill=col)


def stay_up_all_night():
    img, boxes, pw, ph = m.comic("stay up all night")
    # 1:眠そうだね
    x0, y0, x1, y1 = boxes[0]
    d = m.panel(img, boxes[0], 101)
    m.owl(d, x0 + pw * 0.28, y0 + ph * 0.68, 140, "normal")
    m.penguin(d, x0 + pw * 0.72, y0 + ph * 0.7, 125, "smug", hat_on=False)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.28, y0 + 170), "You look tired.", "眠そうだね", 1)
    m.sfx(img, (x0 + pw * 0.86, y0 + ph * 0.48), "*yawn*", 30, (110, 120, 160), 8)
    # 2:徹夜したんだ(ターゲット)
    x0, y0, x1, y1 = boxes[1]
    d = m.panel(img, boxes[1], 102)
    m.penguin(d, x0 + pw * 0.5, y0 + ph * 0.66, 175, "smug", hat_on=False)
    m.sweat(d, x0 + pw * 0.72, y0 + ph * 0.48)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.5, y0 + 180), "I stayed up all night.", "徹夜したんだ", 2)
    # 3:テスト勉強?えらい!
    x0, y0, x1, y1 = boxes[2]
    d = m.panel(img, boxes[2], 103)
    m.owl(d, x0 + pw * 0.3, y0 + ph * 0.66, 150, "happy")
    m.penguin(d, x0 + pw * 0.74, y0 + ph * 0.7, 115, "smug", hat_on=False)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.3, y0 + 180),
                 "Studying for the test?", "テスト勉強?えらい!", 3)
    sparkle(d, x0 + pw * 0.56, y0 + ph * 0.46)
    sparkle(d, x0 + pw * 0.6, y0 + ph * 0.56, 9)
    # 4:ゲームしてた。部長も
    x0, y0, x1, y1 = boxes[3]
    d = m.panel(img, boxes[3], 104)
    m.penguin(d, x0 + pw * 0.3, y0 + ph * 0.66, 125, "smug", hat_on=False)
    controller(d, x0 + pw * 0.3, y0 + ph * 0.84, 90)
    m.capybara(d, x0 + pw * 0.74, y0 + ph * 0.72, 150, "calm")
    controller(d, x0 + pw * 0.66, y0 + ph * 0.9, 80, 381)
    bot = small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.3, y0 + ph * 0.48), "...Playing games.", "…ゲームしてた", 4)
    small_bubble(d, (x0 + pw * 0.4, bot + 10, x0 + pw - 12, 0), (x0 + pw * 0.74, y0 + ph * 0.6), "Rematch tonight.", "今夜もリベンジな", 5)
    return m._end(img)


SCRIPTS.update({
    "just_in_case": dict(
        draw=just_in_case, word="just in case", hook="「念のため」って英語で?",
        meaning="念のため、万一に備えて", level="英検準2級〜2級レベル",
        ex_en="I saved the file twice, just in case.", ex_ja="念のため、ファイルを2回保存した",
        words=[("be ready to ~", "〜する準備ができた"), ("so big", "そんなに大きい"), ("Where are you going?", "どこに行くの?"),
               ("next door", "隣の"), ("store", "お店")],
        panels=[[("pen", "I'm ready to go!")], [("navi", "Why is your bag so big?"), ("pen", "Just in case.")],
                [("navi", "Where are you going?")], [("pen", "To the store next door.")]],
        explain=[("navi", "Just in case."), ("pen", "I saved the file twice, just in case.")],
    ),
    "have_a_crush_on": dict(
        draw=have_a_crush_on, word="have a crush on", hook="「片思い」って英語で?",
        meaning="〜に片思いしている、〜が好き", level="英検2級レベル",
        ex_en="She has a crush on her classmate.", ex_ja="彼女はクラスメートに片思いしている",
        words=[("someone", "だれか"), ("Really?", "本当?"), ("cool", "かっこいい、冷たい"),
               ("shiny", "つやつやした"), ("silver", "銀色の")],
        panels=[[("pen", "I have a crush on someone...")], [("navi", "Really? Who?")],
                [("pen", "He's cool, shiny, and silver...")], [("navi", "That's your lunch!")]],
        explain=[("navi", "Have a crush on."), ("pen", "She has a crush on her classmate.")],
    ),
    "stay_up_all_night": dict(
        draw=stay_up_all_night, word="stay up all night", hook="「徹夜した」って英語で?",
        meaning="徹夜する", level="英検準2級レベル",
        ex_en="I stayed up all night finishing my report.", ex_ja="レポートを仕上げるために徹夜した",
        words=[("look tired", "疲れて見える"), ("stayed", "stay の過去形"), ("study for ~", "〜の勉強をする"),
               ("play games", "ゲームをする"), ("rematch", "再試合、リベンジ")],
        panels=[[("navi", "You look tired.")], [("pen", "I stayed up all night.")],
                [("navi", "Studying for the test?")], [("pen", "...Playing games."), ("boss", "Rematch tonight.")]],
        explain=[("navi", "Stay up all night."), ("pen", "I stayed up all night finishing my report.")],
    ),
})


def pumpkin(d, cx, cy, r, face=True, seed=390):
    """ハロウィンのカボチャ(ジャック・オー・ランタン)。"""
    for dx in (-0.45, 0.45, 0):
        m.shape(d, [(cx + r * dx + r * 0.62 * math.cos(a), cy + r * 0.8 * math.sin(a)) for a in (k * math.pi / 12 for k in range(25))],
                (240, 150, 60), w=4, seed=seed + int(dx * 10))
    m.shape(d, m.rrect_pts(cx - r * 0.1, cy - r * 1.0, cx + r * 0.1, cy - r * 0.7, 4), (110, 140, 70), w=3, seed=seed + 5)
    if face:
        for k in (-1, 1):
            d.polygon([(cx + k * r * 0.35, cy - r * 0.3), (cx + k * r * 0.18, cy - r * 0.02), (cx + k * r * 0.52, cy - r * 0.02)], fill=(70, 50, 40))
        d.chord([cx - r * 0.5, cy - r * 0.2, cx + r * 0.5, cy + r * 0.5], 0, 180, fill=(70, 50, 40))


def witch_hat(d, cx, top, w, seed=395):
    m.shape(d, [(cx - w * 0.3, top + w * 0.7), (cx + w * 0.05, top), (cx + w * 0.3, top + w * 0.7)], (120, 80, 160), w=4, seed=seed)
    m.shape(d, m.rrect_pts(cx - w * 0.55, top + w * 0.66, cx + w * 0.55, top + w * 0.8, 6), (120, 80, 160), w=4, seed=seed + 1)


def candy(d, cx, cy, s, col, seed=0):
    d.ellipse([cx - s, cy - s * 0.7, cx + s, cy + s * 0.7], fill=col, outline=m.INK, width=3)
    for k in (-1, 1):
        d.polygon([(cx + k * s, cy), (cx + k * s * 1.7, cy - s * 0.6), (cx + k * s * 1.7, cy + s * 0.6)], fill=col, outline=m.INK)


def dumbbell(d, cx, cy, w):
    d.line([(cx - w / 2, cy), (cx + w / 2, cy)], fill=(120, 120, 130), width=8)
    for k in (-1, 1):
        d.rounded_rectangle([cx + k * w / 2 - 12, cy - 22, cx + k * w / 2 + 12, cy + 22], radius=5, fill=(80, 85, 95), outline=m.INK, width=3)


def might_as_well():
    img, boxes, pw, ph = m.comic("might as well")
    # 1:ハロウィンだよ!仮装は?
    x0, y0, x1, y1 = boxes[0]
    d = m.panel(img, boxes[0], 111)
    m.owl(d, x0 + pw * 0.3, y0 + ph * 0.68, 140, "happy")
    witch_hat(d, x0 + pw * 0.3, y0 + ph * 0.68 - 170, 120)
    m.penguin(d, x0 + pw * 0.74, y0 + ph * 0.72, 115, "normal", hat_on=False)
    pumpkin(d, x0 + pw * 0.12, y0 + ph * 0.9, 34)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.3, y0 + 200),
                 "It's Halloween!\nWhere's your costume?", "ハロウィンだよ!仮装は?", 1)
    # 2:買うの忘れた
    x0, y0, x1, y1 = boxes[1]
    d = m.panel(img, boxes[1], 112)
    m.penguin(d, x0 + pw * 0.5, y0 + ph * 0.66, 170, "shock", hat_on=False)
    m.sweat(d, x0 + pw * 0.7, y0 + ph * 0.46)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.5, y0 + 180), "I forgot to buy one...", "買うの忘れた…", 2)
    # 3:どうせなら、ペンギンの仮装で(ターゲット)
    x0, y0, x1, y1 = boxes[2]
    d = m.panel(img, boxes[2], 113)
    m.penguin(d, x0 + pw * 0.5, y0 + ph * 0.66, 170, "smug", hat_on=False)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.5, y0 + 200),
                 "I might as well\ngo as a penguin.", "どうせなら、ペンギンの仮装で行こう", 3)
    m.sfx(img, (x0 + pw * 0.84, y0 + ph * 0.5), "*idea*", 30, (200, 160, 60), 8)
    # 4:部長「本物みたい!」
    x0, y0, x1, y1 = boxes[3]
    d = m.panel(img, boxes[3], 114)
    m.penguin(d, x0 + pw * 0.28, y0 + ph * 0.7, 125, "happy", hat_on=False)
    m.capybara(d, x0 + pw * 0.72, y0 + ph * 0.72, 160, "calm")
    pumpkin(d, x0 + pw * 0.72, y0 + ph * 0.72 - 90, 40)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.72, y0 + ph * 0.5),
                 "Great costume!\nSo real!", "本物みたい!よくできてる!", 4)
    m.sfx(img, (x0 + pw * 0.2, y0 + ph * 0.46), "*proud*", 28, (200, 160, 60), 8)
    return m._end(img)


def stay_fit():
    img, boxes, pw, ph = m.comic("stay fit")
    # 1:体型をキープしてるんだ(ターゲット)
    x0, y0, x1, y1 = boxes[0]
    d = m.panel(img, boxes[0], 115)
    m.owl(d, x0 + pw * 0.5, y0 + ph * 0.66, 160, "smug")
    dumbbell(d, x0 + pw * 0.5, y0 + ph * 0.66 + 60, 220)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.5, y0 + 180), "I'm trying to stay fit.", "体型をキープしてるんだ", 1)
    m.sfx(img, (x0 + pw * 0.86, y0 + ph * 0.5), "*huff*", 30, (110, 120, 140), 8)
    # 2:お菓子いる?
    x0, y0, x1, y1 = boxes[1]
    d = m.panel(img, boxes[1], 116)
    m.penguin(d, x0 + pw * 0.4, y0 + ph * 0.66, 160, "happy", hat_on=False)
    pumpkin(d, x0 + pw * 0.76, y0 + ph * 0.8, 60, seed=391)
    for k, col in enumerate(((230, 90, 80), (90, 170, 220), (240, 200, 70))):
        candy(d, x0 + pw * (0.66 + k * 0.1), y0 + ph * 0.62 - k * 10, 16, col)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.4, y0 + 200),
                 "Want some\nHalloween candy?", "ハロウィンのお菓子いる?", 2)
    # 3:遠慮しとく
    x0, y0, x1, y1 = boxes[2]
    d = m.panel(img, boxes[2], 117)
    m.owl(d, x0 + pw * 0.3, y0 + ph * 0.66, 150, "smug")
    m.penguin(d, x0 + pw * 0.74, y0 + ph * 0.7, 115, "shock", hat_on=False)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.3, y0 + 180), "No thanks. I'll pass.", "遠慮しとく", 3)
    # 4:部長「私もキープ中。お菓子がプロテイン」
    x0, y0, x1, y1 = boxes[3]
    d = m.panel(img, boxes[3], 118)
    import random as _r
    rr = _r.Random(5)
    for k in range(9):
        candy(d, x0 + pw * rr.uniform(0.35, 0.95), y0 + ph * rr.uniform(0.84, 0.95), 14,
              ((230, 90, 80), (90, 170, 220), (240, 200, 70))[k % 3])
    m.capybara(d, x0 + pw * 0.64, y0 + ph * 0.68, 170, "calm")
    m.owl(d, x0 + pw * 0.16, y0 + ph * 0.8, 90, "shock")
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.6, y0 + ph * 0.5),
                 "Me too.\nCandy is my protein.", "私もだ。お菓子が私のプロテイン", 4)
    m.sfx(img, (x0 + pw * 0.88, y0 + ph * 0.56), "*munch*", 28, (200, 140, 60), 8)
    return m._end(img)


def on_display():
    img, boxes, pw, ph = m.comic("on display", series="toeic")
    # 1:ロビーにハロウィンの飾り(ターゲット)
    x0, y0, x1, y1 = boxes[0]
    d = m.panel(img, boxes[0], 121)
    m.owl(d, x0 + pw * 0.3, y0 + ph * 0.7, 140, "happy")
    pumpkin(d, x0 + pw * 0.76, y0 + ph * 0.8, 50, seed=392)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.3, y0 + 240),
                 "Halloween decorations\nare on display\nin the lobby.", "ロビーにハロウィンの飾りが展示されてるよ", 1)
    # 2:カボチャがいっぱい!
    x0, y0, x1, y1 = boxes[1]
    d = m.panel(img, boxes[1], 122)
    d.rectangle([x0 + 20, y0 + ph * 0.8, x1 - 20, y0 + ph * 0.86], fill=(206, 160, 110), outline=m.INK, width=3)
    for k, fx in enumerate((0.2, 0.42, 0.64)):
        pumpkin(d, x0 + pw * fx, y0 + ph * 0.8 - 36, 38, seed=393 + k)
    m.penguin(d, x0 + pw * 0.84, y0 + ph * 0.66, 110, "happy", hat_on=False)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.6, y0 + 180), "Wow! So many pumpkins!", "わあ、カボチャがいっぱい!", 2)
    # 3:これ部長にそっくり
    x0, y0, x1, y1 = boxes[2]
    d = m.panel(img, boxes[2], 123)
    d.rectangle([x0 + 20, y0 + ph * 0.8, x1 - 20, y0 + ph * 0.86], fill=(206, 160, 110), outline=m.INK, width=3)
    pumpkin(d, x0 + pw * 0.2, y0 + ph * 0.8 - 36, 38, seed=396)
    m.capybara(d, x0 + pw * 0.56, y0 + ph * 0.8 - 50, 120, "calm")
    m.penguin(d, x0 + pw * 0.86, y0 + ph * 0.66, 100, "normal", hat_on=False)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.6, y0 + 200),
                 "This one looks\njust like the boss.", "これ、部長にそっくり", 3)
    # 4:部長本人も展示中
    x0, y0, x1, y1 = boxes[3]
    d = m.panel(img, boxes[3], 124)
    d.rectangle([x0 + 20, y0 + ph * 0.8, x1 - 20, y0 + ph * 0.86], fill=(206, 160, 110), outline=m.INK, width=3)
    m.capybara(d, x0 + pw * 0.5, y0 + ph * 0.8 - 56, 130, "calm")
    pumpkin(d, x0 + pw * 0.5 - 20, y0 + ph * 0.8 - 128, 30, face=False, seed=397)
    m.penguin(d, x0 + pw * 0.86, y0 + ph * 0.66, 100, "shock", hat_on=False)
    small_bubble(d, (x0 + 12, y0 + 18, x0 + pw - 12, 0), (x0 + pw * 0.46, y0 + ph * 0.5),
                 "I'm on display, too.", "私も展示中だ", 4)
    m.sfx(img, (x0 + pw * 0.18, y0 + ph * 0.6), "?!", 50, (220, 80, 70), 10)
    return m._end(img)


SCRIPTS.update({
    "might_as_well": dict(
        draw=might_as_well, word="might as well", hook="「どうせなら〜しよう」英語で?",
        meaning="どうせなら〜した方がいい", level="英検準1級レベル",
        ex_en="It's raining, so we might as well stay home.", ex_ja="雨だし、家にいた方がいいね",
        words=[("costume", "仮装、衣装"), ("forgot to ~", "〜し忘れた"), ("go as ~", "〜の仮装で行く"),
               ("real", "本物の"), ("Halloween", "ハロウィン")],
        panels=[[("navi", "It's Halloween! Where's your costume?")], [("pen", "I forgot to buy one...")],
                [("pen", "I might as well go as a penguin.")], [("boss", "Great costume! So real!")]],
        explain=[("navi", "Might as well."), ("pen", "It's raining, so we might as well stay home.")],
    ),
    "stay_fit": dict(
        draw=stay_fit, word="stay fit", hook="「体型キープ」って英語で?",
        meaning="体を鍛えておく、健康を保つ", level="英検準2級レベル",
        ex_en="I swim twice a week to stay fit.", ex_ja="体を鍛えるために、週2回泳いでいる",
        words=[("try to ~", "〜しようとする"), ("candy", "お菓子、あめ"), ("No thanks.", "けっこうです"),
               ("I'll pass.", "やめておく"), ("protein", "プロテイン、たんぱく質")],
        panels=[[("navi", "I'm trying to stay fit.")], [("pen", "Want some Halloween candy?")],
                [("navi", "No thanks. I'll pass.")], [("boss", "Me too. Candy is my protein.")]],
        explain=[("navi", "Stay fit."), ("pen", "I swim twice a week to stay fit.")],
    ),
    "on_display": dict(
        draw=on_display, word="on display", hook="「展示されている」英語で?",
        meaning="展示されて、飾られて", level="TOEIC頻出",
        ex_en="Her paintings are on display at the museum.", ex_ja="彼女の絵が美術館に展示されている",
        words=[("decoration", "飾り"), ("lobby", "ロビー"), ("pumpkin", "カボチャ"),
               ("look just like ~", "〜にそっくり"), ("too", "〜も")],
        panels=[[("navi", "Halloween decorations are on display in the lobby.")], [("pen", "Wow! So many pumpkins!")],
                [("pen", "This one looks just like the boss.")], [("boss", "I'm on display, too.")]],
        explain=[("navi", "On display."), ("pen", "Her paintings are on display at the museum.")],
    ),
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
        # 0.5秒かけて下からふわっと浮き上がる(少し行きすぎて戻る)
        k = min(1.0, t / 0.5)
        ease = 1 + 2.2 * (k - 1) ** 3 + 1.2 * (k - 1) ** 2
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        dy = int((1 - ease) * 90)
        ld.rounded_rectangle((40, 95 + dy, W - 40, 285 + dy), radius=28, fill=(200, 52, 48, 255))
        ld.text((W // 2, 190 + dy), hook, font=f, fill=(255, 255, 255, 255), anchor="mm")
        layer.putalpha(layer.getchannel("A").point(lambda a: int(a * min(1.0, t / 0.3))))
        img.paste(layer, (0, 0), layer)
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
    if not hook:
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
                    f = panel_frame(src, t, rng, sc["word"], sc["hook"] if kind == "hooked" else None)
                proc.stdin.write(f.tobytes())
        proc.stdin.close()
        proc.wait()
    print(f"✓ {out}({total:.1f}秒)/ 4コマ {name}_1.png・解説 {name}_2.png")


if __name__ == "__main__":
    main()
