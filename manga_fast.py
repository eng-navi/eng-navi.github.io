"""テンポの速い4コマ(ストップモーション風の揺れつき)。1本につきターゲット単語は1つ、ほかにも使える単語を数個。

    .venv-tts/bin/python manga_fast.py procrastinate      # out/manga/procrastinate_fast.mp4 と 4コマ・解説の画像

・最初の約1秒でターゲット単語を見せる(つかみ)。コマの切り替えは「パッ」と寄って止まる
・1秒12コマで、絵がわずかに揺れる(語呂合わせリールと同じ手作り感)
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


def explain_card():
    """解説:ターゲット単語+例文+今回出てきた単語。"""
    img = Image.new("RGB", (m.W, m.H), BG)
    d = ImageDraw.Draw(img)
    for x in range(0, m.W, 54):
        d.line([(x, 0), (x, m.H)], fill=(225, 220, 212), width=2)
    for y in range(0, m.H, 54):
        d.line([(0, y), (m.W, y)], fill=(225, 220, 212), width=2)
    d.text((m.W // 2, 200), "procrastinate", font=m.EN(118), fill=m.INK, anchor="mm")
    d.line(m.wob([(200, 270), (880, 264)], amp=2), fill=(200, 52, 48), width=7)
    d.text((m.W // 2, 350), "= (やるべきことを)先延ばしにする", font=m.JP(52), fill=(200, 52, 48), anchor="mm")
    d.text((m.W // 2, 450), "英検準1級レベル", font=m.JP(30), fill=(130, 120, 110), anchor="mm")
    d.text((m.W // 2, 560), "I always procrastinate on my taxes.", font=m.EN(42), fill=m.INK, anchor="mm")
    d.text((m.W // 2, 615), "(税金の手続きを、いつも後回しにしてしまう)", font=m.JP(30), fill=(120, 110, 105), anchor="mm")
    d.text((140, 740), "今回出てきた単語", font=m.JP(36), fill=m.INK, anchor="lm")
    words = [("due", "(提出物などが)期限の"), ("under pressure", "追い込まれて、プレッシャーの中で"),
             ("priorities", "優先順位、優先事項"), ("merely", "ただ〜にすぎない"), ("deadline", "締め切り")]
    for i, (en, ja) in enumerate(words):
        y = 820 + i * 78
        d.text((160, y), en, font=m.EN(44), fill=m.INK, anchor="lm")
        d.text((560, y), ja, font=m.JP(30), fill=(110, 100, 95), anchor="lm")
    d.text((m.W // 2, 1250), "保存して、使ってみてね", font=m.JP(32), fill=(200, 52, 48), anchor="mm")
    d.text((m.W - 50, m.H - 30), "@yonkoma_eigo", font=m.EN(30), fill=(160, 150, 140), anchor="rm")
    return img


SCRIPTS = {
    "procrastinate": dict(
        draw=procrastinate, word="procrastinate", hook="先延ばしグセ、ある?",
        panels=[[("navi", "Your report is due tomorrow. Shouldn't you get started?"), ("pen", "Relax. I work better under pressure.")],
                [("navi", "You said that yesterday! Stop procrastinating!")],
                [("pen", "I'm not procrastinating. I'm just reorganizing my priorities.")],
                [("boss", "Zzz... deadlines are merely suggestions."), ("navi", "Not you too, Boss!")]],
        explain=[("navi", "Procrastinate."), ("pen", "I always procrastinate on my taxes.")],
    ),
}


def jitter(src, rng, scale=1.0, area=(980, 1350), top=300):
    """1コマごとに、わずかにずらして傾ける(ストップモーション風)。"""
    tw = int(area[0] * scale)
    th = int(src.height * tw / src.width)
    im = src.resize((tw, th), Image.LANCZOS).rotate(rng.uniform(-0.6, 0.6), resample=Image.BICUBIC, fillcolor=BG)
    img = Image.new("RGB", (W, H), BG)
    x = (W - tw) // 2 + int(rng.uniform(-4, 4))
    y = top + (area[1] - th) // 2 + int(rng.uniform(-4, 4))
    img.paste(im, (x, y))
    return img


def title_frame(word, hook, t, rng):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    s = 1.0 + max(0, 0.25 - t) * 0.8  # 出てきた瞬間だけ少し大きく
    f = m.EN(int(120 * s))
    while f.getlength(word) > W - 160:
        f = m.EN(f.size - 4)
    d.text((W // 2 + rng.uniform(-3, 3), 820 + rng.uniform(-3, 3)), word, font=f, fill=m.INK, anchor="mm")
    d.line(m.wob([(200, 900), (880, 894)], amp=2, seed=int(t * 12)), fill=(200, 52, 48), width=8)
    d.text((W // 2, 1010), hook, font=m.JP(58), fill=(200, 52, 48), anchor="mm")
    d.text((W // 2, 1100), "4コマで覚える英語", font=m.JP(34), fill=(150, 140, 130), anchor="mm")
    return img


def panel_frame(src, t, rng, label):
    # 切り替えた瞬間は少し寄って、0.15秒で止まる
    scale = 1.06 if t < 0.15 else 1.0
    img = jitter(src, rng, scale)
    d = ImageDraw.Draw(img)
    d.text((W // 2, 170), label, font=m.EN(80), fill=m.INK, anchor="mm")
    d.text((W // 2, 245), "4コマで覚える英語", font=m.JP(36), fill=(150, 140, 130), anchor="mm")
    return img


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "procrastinate"
    sc = SCRIPTS[name]
    OUT.mkdir(parents=True, exist_ok=True)
    comic = sc["draw"]()
    boxes = comic.info["boxes"]
    card = explain_card()
    comic.save(OUT / f"{name}_1.png")
    card.save(OUT / f"{name}_2.png")
    mr.load_env()
    voice = lambda who, text: mr.eleven(who, text, SPEED)

    scenes, audio = [], []  # (種類, 画像, 秒)
    hook_len = 1.1
    scenes.append(("title", None, hook_len))
    audio += [mr.pop(), mr.silence(hook_len - len(mr.pop()) / SR)]
    for box, lines in zip(boxes, sc["panels"]):
        clips = []
        for who, text in lines:
            clips += [voice(who, text), mr.silence(0.18)]
        clip = np.concatenate([mr.pop(), mr.silence(0.12)] + clips)
        scenes.append(("panel", comic.crop(tuple(int(v) for v in box)), len(clip) / SR))
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

    out = OUT / f"{name}_fast.mp4"
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
               "-i", wav.name, "-map", "0:v", "-map", "1:a", "-af", "volume=1.5", "-t", f"{total:.2f}",
               "-r", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "aac", "-movflags", "+faststart", str(out)]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for kind, src, dur in scenes:
            for i in range(round(dur * FPS)):
                t = i / FPS
                if kind == "title":
                    f = title_frame(sc["word"], sc["hook"], t, rng)
                elif kind == "explain":
                    f = grid_bg.copy()
                    im = src.rotate(rng.uniform(-0.5, 0.5), resample=Image.BICUBIC, fillcolor=BG)
                    f.paste(im, (int(rng.uniform(-4, 4)), 285 + int(rng.uniform(-4, 4))))
                else:
                    f = panel_frame(src, t, rng, sc["word"])
                proc.stdin.write(f.tobytes())
        proc.stdin.close()
        proc.wait()
    print(f"✓ {out}({total:.1f}秒)/ 4コマ {name}_1.png・解説 {name}_2.png")


if __name__ == "__main__":
    main()
