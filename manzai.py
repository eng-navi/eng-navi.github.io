"""4コマのアカウントの新しい型(試作):ペンとナビの漫才 → 最後に2択のリスニング問題。

    .venv-tts/bin/python manzai.py vacuum          # out/manzai/vacuum.mp4(リール)と vacuum_1〜4.png(カルーセル)

・0秒目から問題を見せる(何を聞き取ればいいかわかるので、最後まで聞いてもらえる)
・セリフは英検2級〜準1級の単語を3〜5個。字幕の単語に色をつけ、最後に「今回の単語」でまとめる
・答えはコメント欄(リール)/4枚目(カルーセル)
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw

import goro as g
import manga as m
import manga_reel as mr

ROOT = Path(__file__).parent
OUT = ROOT / "out" / "manzai"
W, H, FPS, SR = 1080, 1920, 30, 24000
INK = m.INK
RED = (200, 52, 48)
HL = (110, 160, 210)  # 単語の色

SCRIPTS = {
    "vacuum": dict(
        q="ペンが週末に買ったのは?", q_en="What did Pen buy?",
        lines=[("navi", "You look exhausted. What happened?"),
               ("pen", "I spent the whole weekend comparing vacuum cleaners."),
               ("navi", "Wow, that's real commitment. Which one did you buy?"),
               ("pen", "None. I got so overwhelmed that I bought a cake instead."),
               ("navi", "...What a remarkable decision.")],
        ja=["疲れ切ってるね。どうしたの?", "週末ずっと、掃除機を比べてたの。", "わあ、本気だね。どれを買ったの?",
            "どれも。迷いすぎて、代わりにケーキを買っちゃった。", "…すごい決断だね。"],
        choices=["掃除機", "ケーキ"], answer=2,
        words=[("exhausted", "疲れ切った"), ("compare", "比べる"), ("commitment", "本気の取り組み、献身"),
               ("overwhelmed", "圧倒された、いっぱいいっぱいの"), ("remarkable", "驚くべき、注目すべき")],
        level="英検2級〜準1級"),
}


def highlight(d, xy, text, words, font, width):
    """英文を折り返して書き、words に入っている単語だけ色をつける。中央ぞろえ。"""
    keys = {w.lower() for w, _ in words}
    stems = [k[:5] for k in keys]
    lines, cur = [], ""
    for tok in text.split():
        nxt = (cur + " " + tok).strip()
        if cur and font.getlength(nxt) > width:
            lines.append(cur)
            cur = tok
        else:
            cur = nxt
    lines.append(cur)
    x0, y = xy
    for line in lines:
        x = x0 - font.getlength(line) / 2
        for tok in line.split():
            core = "".join(c for c in tok.lower() if c.isalpha())
            col = HL if any(core.startswith(s) for s in stems if len(core) >= 4) else INK
            d.text((x, y), tok, font=font, fill=col, anchor="ls")
            x += font.getlength(tok + " ")
        y += font.size * 1.25
    return y


def q_banner(d, sc):
    d.rounded_rectangle((60, 140, W - 60, 330), radius=36, fill=RED)
    d.text((W / 2, 205), "Q. " + sc["q"], font=m.JP(58), fill=(255, 255, 255), anchor="mm")
    d.text((W / 2, 280), sc["q_en"], font=m.EN(44), fill=(255, 230, 225), anchor="mm")


def stage_frame(sc, k, t, i):
    """k 番目のセリフを話している場面。話している方が少し跳ねる"""
    img = g.stage(700 + i % 3)
    d = ImageDraw.Draw(img)
    q_banner(d, sc)
    who, text = sc["lines"][k]
    hop = lambda w: -18 if (w == who and (t * 6) % 2 < 1) else 0
    g.shadow(d, 300, 1440, 220)
    m.penguin(d, 300, 1210 + hop("pen"), 260, "shock" if "None" in text else "happy" if who == "pen" else "normal", hat_on=False, seed=51 + i % 3)
    g.shadow(d, 790, 1440, 220)
    m.owl(d, 790, 1200 + hop("navi"), 250, "smug" if text.startswith("...") else "shock" if "exhausted" in text else "normal", seed=41 + i % 3)
    # 吹き出し(話している方の上)
    cx = 300 if who == "pen" else 790
    d.rounded_rectangle((70, 440, W - 70, 860), radius=40, fill=(255, 252, 245), outline=INK, width=6)
    d.polygon([(cx - 30, 858), (cx + 30, 858), (cx, 930)], fill=(255, 252, 245))
    d.line([(cx - 30, 858), (cx, 930), (cx + 30, 858)], fill=INK, width=6)
    highlight(d, (W / 2, 560), text, sc["words"], m.EN(62), W - 220)
    d.text((W - 60, H - 60), m.HANDLE, font=m.EN(40), fill=(120, 110, 100), anchor="rm")
    return img


def choice_frame(sc, t, carousel=False):
    img = g.stage(760)
    d = ImageDraw.Draw(img)
    q_banner(d, sc)
    for n, c in enumerate(sc["choices"]):
        y = 620 + n * 260
        d.rounded_rectangle((120, y, W - 120, y + 200), radius=40, fill=(255, 252, 245), outline=INK, width=6)
        d.text((220, y + 100), "①②"[n], font=m.JP(90), fill=RED, anchor="mm")
        d.text((W / 2 + 60, y + 100), c, font=m.JP(76), fill=INK, anchor="mm")
    left = max(0, 3 - int(t))
    if carousel:
        g.caption(d, "スワイプして答え合わせ →", 1340, 60)
    elif left:
        d.ellipse((W / 2 - 90, 1230, W / 2 + 90, 1410), fill=RED)
        d.text((W / 2, 1320), str(left), font=m.EN(110), fill=(255, 255, 255), anchor="mm")
    else:
        g.caption(d, "答えはコメント欄で👇", 1340, 64)
    d.text((W - 60, H - 60), m.HANDLE, font=m.EN(40), fill=(120, 110, 100), anchor="rm")
    return img


def words_frame(sc, answer=False):
    img = Image.new("RGB", (W, H), (244, 241, 234))
    d = ImageDraw.Draw(img)
    for x in range(0, W, 54):
        d.line([(x, 0), (x, H)], fill=(225, 220, 212), width=2)
    for y in range(0, H, 54):
        d.line([(0, y), (W, y)], fill=(225, 220, 212), width=2)
    y = 220
    if answer:
        d.text((W / 2, y), f"答え:{'①②'[sc['answer'] - 1]} {sc['choices'][sc['answer'] - 1]}", font=m.JP(80), fill=RED, anchor="mm")
        y += 120
    d.text((W / 2, y), "今回の単語", font=m.JP(64), fill=INK, anchor="mm")
    d.text((W / 2, y + 80), sc["level"], font=m.JP(36), fill=(130, 120, 110), anchor="mm")
    y += 200
    for w, mean in sc["words"]:
        d.text((150, y), w, font=m.EN(66), fill=HL, anchor="lm")
        d.text((150, y + 70), mean, font=m.JP(40), fill=(90, 85, 80), anchor="lm")
        y += 170
    d.rounded_rectangle((W / 2 - 330, y + 20, W / 2 + 330, y + 110), radius=45, fill=RED)
    d.text((W / 2, y + 65), "保存して、あとで復習しよう", font=m.JP(40), fill=(255, 255, 255), anchor="mm")
    d.text((W - 60, H - 60), m.HANDLE, font=m.EN(40), fill=(120, 110, 100), anchor="rm")
    return img


def script_card(sc):
    """カルーセル2枚目:漫才の台本(英語+和訳)"""
    img = Image.new("RGB", (W, H), (244, 241, 234))
    d = ImageDraw.Draw(img)
    q_banner(d, sc)
    y = 440
    for (who, text), ja in zip(sc["lines"], sc["ja"]):
        name = "ペン" if who == "pen" else "ナビ"
        d.text((90, y), name, font=m.JP(40), fill=RED if who == "pen" else (90, 130, 200), anchor="ls")
        y = highlight(d, (W / 2 + 60, y), text, sc["words"], m.EN(46), W - 320) + 4
        y += 40
    d.text((W / 2, H - 140), "答えは最後のページ →", font=m.JP(44), fill=INK, anchor="mm")
    return img


def build(name):
    sc = SCRIPTS[name]
    OUT.mkdir(parents=True, exist_ok=True)
    mr.load_env()

    def voice(who, text):
        a = mr.eleven(who, text, 1.05)
        a = a * (0.09 / (float(np.sqrt(np.mean(a ** 2))) or 1.0))
        return (a * min(1.0, 0.95 / (float(np.max(np.abs(a))) or 1.0))).astype(np.float32)

    gap = lambda s: np.zeros(int(SR * s), np.float32)
    scenes, audio = [], []
    lead = np.concatenate([g.tone(660, 0.15), gap(0.85)])  # 問題を読む時間
    scenes.append(("stage", 0, len(lead) / SR))
    audio.append(lead)
    for k, (who, text) in enumerate(sc["lines"]):
        clip = np.concatenate([voice(who, text), gap(0.35)])
        scenes.append(("stage", k, len(clip) / SR))
        audio.append(clip)
    ch = np.concatenate([g.tone(880, 0.12, 0.05), gap(3.9)])
    scenes.append(("choice", None, len(ch) / SR))
    audio.append(ch)
    wd = gap(3.5)
    scenes.append(("words", None, len(wd) / SR))
    audio.append(wd)
    total = sum(s[2] for s in scenes)
    out = OUT / f"{name}.mp4"
    with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
        sf.write(wav.name, np.concatenate(audio), SR)
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-i", wav.name, "-stream_loop", "-1", "-i", str(ROOT / "assets" / "manga_bgm" / "cozy-places.mp3"),
                              "-filter_complex", "[2:a]volume=0.05[b];[1:a]aresample=44100,volume=1.5[v];[v][b]amix=inputs=2:duration=first:normalize=0[a]",
                              "-map", "0:v", "-map", "[a]", "-t", f"{total:.2f}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                              "-c:a", "aac", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
        n = 0
        for kind, k, dur in scenes:
            for i in range(round(dur * FPS)):
                t = i / FPS
                img = stage_frame(sc, k, t, n // 4) if kind == "stage" else choice_frame(sc, t) if kind == "choice" else words_frame(sc)
                p.stdin.write(img.tobytes())
                n += 1
        p.stdin.close()
        p.wait()
    # カルーセル版:1 問題と選択肢 / 2 漫才の台本 / 3 今回の単語 / 4 答え
    choice_frame(sc, 0, carousel=True).save(OUT / f"{name}_1.png")
    script_card(sc).save(OUT / f"{name}_2.png")
    words_frame(sc).save(OUT / f"{name}_3.png")
    words_frame(sc, answer=True).save(OUT / f"{name}_4.png")
    print(f"✓ {out}({total:.1f}秒)と カルーセル4枚")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "vacuum")
