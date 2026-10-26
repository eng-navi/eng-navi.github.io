"""語呂合わせ英単語の、ストップモーション風リール(試作)。

    .venv-tts/bin/python goro.py abandon     # out/goro/abandon.mp4

見た目:左右対称の舞台・パステルカラー・フェルト/紙の質感・1秒12コマのわずかなカクつき(手作り感)。
キャラは 4コマと同じ ナビ(フクロウ)とペン(ペンギン)。語呂合わせと例文はオリジナル。
"""
import math
import random
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import manga as m

ROOT = Path(__file__).parent
OUT = ROOT / "out" / "goro"
W, H, FPS, SR = 1080, 1920, 12, 24000
WALL = (246, 214, 200)      # くすみピンクの壁
WALL2 = (238, 200, 186)
FLOOR = (196, 214, 196)     # セージグリーンの床
FRAME_C = (232, 190, 120)   # 額縁のからし色
INK = m.INK


def felt(seed):
    """フェルトのザラザラ。フレームごとに少しずらして“ゆらぎ”を出す。"""
    r = random.Random(seed)
    n = Image.effect_noise((W // 3, H // 3), 28).resize((W, H), Image.BILINEAR)
    return n.rotate(r.uniform(-0.6, 0.6)).convert("L")


def stage(seed):
    """左右対称の舞台:壁・額縁・床・カーテン。"""
    img = Image.new("RGB", (W, H), WALL)
    d = ImageDraw.Draw(img)
    for x in range(0, W, 90):  # 壁のストライプ
        d.rectangle([x, 0, x + 45, 1250], fill=WALL2)
    d.rectangle([0, 1250, W, H], fill=FLOOR)
    d.line(m.wob([(0, 1250), (W, 1250)], amp=2, seed=seed), fill=INK, width=6)
    # 中央の額縁(左右対称)
    m.shape(d, m.rrect_pts(340, 300, 740, 600, 10), FRAME_C, seed=seed + 1)
    d.rectangle([370, 330, 710, 570], fill=(250, 240, 220))
    d.text((540, 450), "eng", font=m.EN(70), fill=(200, 150, 120), anchor="mm")
    # 左右のカーテン
    for side in (-1, 1):
        x0 = 0 if side < 0 else W - 120
        m.shape(d, [(x0, 0), (x0 + 120, 0), (x0 + 120 - side * 30 if side < 0 else x0 + 30, 1250), (x0, 1250)] if side < 0
                else [(x0, 0), (x0 + 120, 0), (x0 + 120, 1250), (x0 + 30, 1250)], (214, 120, 120), seed=seed + 2 + side)
    return img


def finish(img, seed):
    """フェルトの質感と、ふちのやわらかい影をのせる。"""
    tex = felt(seed)
    shade = Image.new("RGB", (W, H), (60, 40, 30))
    img = Image.composite(shade, img, tex.point(lambda v: int(v * 0.10)))
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse([-300, -200, W + 300, H + 200], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(160))
    dark = Image.new("RGB", (W, H), (40, 30, 30))
    return Image.composite(img, dark, vig.point(lambda v: int(140 + v * 115 / 255)))


def jsfx(img, xy, text, size, color, angle):
    """日本語の効果音(ポイッ・ドン!)。白いふちどりで目立たせる。"""
    layer = Image.new("RGBA", (int(size * len(text) * 1.3), int(size * 2)), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((layer.width / 2, layer.height / 2), text, font=m.JP(size), fill=color, anchor="mm",
                               stroke_width=int(size * 0.08), stroke_fill=(255, 255, 255))
    layer = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    img.paste(layer, (int(xy[0] - layer.width / 2), int(xy[1] - layer.height / 2)), layer)


def shadow(d, cx, y, w):
    d.ellipse([cx - w / 2, y - 14, cx + w / 2, y + 14], fill=(150, 170, 150))


def table(d, seed):
    m.shape(d, m.rrect_pts(300, 1180, 780, 1230, 10), (206, 160, 110), seed=seed)
    for x in (340, 740):
        d.line([(x, 1230), (x, 1420)], fill=INK, width=8)


def bowl(d, cx, cy, s, seed, tilt=0):
    pts = [(cx - s, cy), (cx + s, cy), (cx + s * 0.7, cy + s * 0.7), (cx - s * 0.7, cy + s * 0.7)]
    pts = [(x + tilt * (y - cy) * 0.3, y) for x, y in pts]
    m.shape(d, pts, (240, 240, 245), seed=seed)
    d.ellipse([cx - s * 0.9, cy - s * 0.35, cx + s * 0.9, cy + s * 0.25], fill=(250, 220, 150), outline=INK, width=4)
    for i in range(3):  # 湯気
        x = cx - s * 0.4 + i * s * 0.4
        d.line(m.wob([(x, cy - s * 0.5), (x + 8, cy - s * 0.8), (x - 6, cy - s * 1.1)], amp=1.5, seed=seed + i), fill=(200, 200, 200), width=5)


def trash(d, cx, cy, s, seed):
    m.shape(d, [(cx - s * 0.5, cy - s * 0.6), (cx + s * 0.5, cy - s * 0.6), (cx + s * 0.4, cy + s * 0.6), (cx - s * 0.4, cy + s * 0.6)], (150, 170, 190), seed=seed)
    m.shape(d, m.rrect_pts(cx - s * 0.58, cy - s * 0.72, cx + s * 0.58, cy - s * 0.58, 6), (130, 150, 170), seed=seed + 1)
    for k in (-0.2, 0, 0.2):
        d.line([(cx + k * s, cy - s * 0.45), (cx + k * s * 0.8, cy + s * 0.5)], fill=(110, 130, 150), width=4)


def caption(d, text, y, size=64, color=INK, box=True):
    f = m.JP(size)
    w = f.getlength(text)
    if box:
        d.rounded_rectangle([W / 2 - w / 2 - 36, y - size * 0.85, W / 2 + w / 2 + 36, y + size * 0.6], radius=26, fill=(255, 252, 245), outline=INK, width=5)
    d.text((W / 2, y), text, font=f, fill=color, anchor="ms")


def big_word(d, parts, y, active):
    """「あ・ばん・どん」を色分けして見せ、下に abandon を対応させる。"""
    colors = [(230, 120, 110), (110, 160, 210), (120, 170, 120)]
    f = m.JP(120)
    widths = [f.getlength(p) for p, _ in parts]
    x = W / 2 - (sum(widths) + 40 * (len(parts) - 1)) / 2
    fe = m.EN(130)
    en_w = sum(fe.getlength(e) for _, e in parts)
    xe = W / 2 - en_w / 2
    for i, ((jp, en), w) in enumerate(zip(parts, widths)):
        c = colors[i] if i < active else (210, 205, 200)
        d.text((x, y), jp, font=f, fill=c, anchor="ls")
        x += w + 40
        d.text((xe, y + 160), en, font=fe, fill=c, anchor="ls")
        xe += fe.getlength(en)


# ---- シーン(秒数, 描く関数(frame番号)) ----
def scene_hook(i):
    img = stage(100 + i % 3)
    d = ImageDraw.Draw(img)
    shadow(d, 540, 1400, 260)
    m.penguin(d, 540, 1150, 300, "shock", hat_on=False, seed=51 + i % 3)
    m.sweat(d, 700, 1000, 30)
    caption(d, "abandon、", 820, 96, box=False)
    caption(d, "1秒で覚えられる?", 950, 80, color=(200, 52, 48), box=False)
    return img


def scene_dinner(i):
    img = stage(110 + i % 3)
    d = ImageDraw.Draw(img)
    table(d, 120 + i % 3)
    bowl(d, 540, 1120, 90, 130 + i % 3)
    shadow(d, 300, 1440, 200)
    m.penguin(d, 300, 1230, 210, "happy", hat_on=False, seed=51 + i % 3)
    shadow(d, 790, 1440, 200)
    m.owl(d, 790, 1230, 200, "normal", seed=41 + i % 3)
    caption(d, "今日の晩ごはん、楽しみ〜", 1640, 58)
    return img


def scene_toss(i, n):
    img = stage(140 + i % 3)
    d = ImageDraw.Draw(img)
    t = min(1, i / max(1, n - 3))
    shadow(d, 230, 1440, 180)
    m.penguin(d, 230, 1240, 190, "shock", hat_on=False, seed=51 + i % 3)
    shadow(d, 520, 1440, 180)
    m.owl(d, 520, 1240, 180, "smug", seed=41 + i % 3)
    trash(d, 850, 1300, 220, 150 + i % 3)
    # 晩ごはんがゴミ箱へ飛んでいく(放物線)
    x = 560 + (850 - 560) * t
    y = 1080 - 300 * math.sin(math.pi * t) + 120 * t
    if t < 1:
        bowl(d, x, y, 80, 160 + i % 3, tilt=t * 2)
    if t < 1:
        jsfx(img, (700, 820), "ポイッ", 90, (220, 90, 70), -10)
    caption(d, "あ、晩(ばん)ごはん…", 1640, 64)
    return img


def scene_don(i):
    img = stage(170 + i % 3)
    d = ImageDraw.Draw(img)
    trash(d, 830, 1300, 230, 150 + i % 3)
    shadow(d, 330, 1440, 220)
    m.penguin(d, 330, 1230, 230, "shock", hat_on=False, seed=51 + i % 3)
    jsfx(img, (640, 1120), "ドン!", 120, (220, 60, 50), -8)
    d.rounded_rectangle([90, 640, W - 90, 1000], radius=40, fill=(255, 252, 245), outline=INK, width=6)
    big_word(d, [("あ", "a"), ("ばん", "ban"), ("どん!", "don")], 790, active=min(3, 1 + i // 4))
    return img


def scene_meaning(i):
    img = stage(190 + i % 3)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([110, 640, W - 110, 1180], radius=40, fill=(255, 252, 245), outline=INK, width=6)
    d.text((W / 2, 800), "abandon", font=m.EN(150), fill=INK, anchor="ms")
    d.text((W / 2, 920), "= 捨てる、あきらめる", font=m.JP(66), fill=(200, 52, 48), anchor="ms")
    d.text((W / 2, 1030), "They abandoned the old boat.", font=m.EN(52), fill=INK, anchor="ms")
    d.text((W / 2, 1100), "(彼らは古いボートを捨てた)", font=m.JP(38), fill=(110, 110, 110), anchor="ms")
    shadow(d, 260, 1440, 180)
    m.owl(d, 260, 1260, 180, "happy", seed=41 + i % 3)
    shadow(d, 820, 1440, 180)
    m.penguin(d, 820, 1260, 170, "smug", hat_on=False, seed=51 + i % 3)
    caption(d, "あ・ばん・どん で abandon!", 1640, 58)
    d.text((W - 60, H - 60), m.HANDLE, font=m.EN(40), fill=(120, 110, 100), anchor="rm")
    return img


def say(pipe, text, voice):
    return np.concatenate([a for _, _, a in pipe(text, voice=voice, speed=0.9)])


def tone(freq, dur, vol=0.06, decay=14):
    t = np.arange(int(SR * dur)) / SR
    return (vol * np.sin(2 * np.pi * freq * t) * np.exp(-t * decay)).astype(np.float32)


def main():
    from kokoro import KPipeline
    import soundfile as sf
    pipe = KPipeline(lang_code="b", repo_id="hexgrad/Kokoro-82M")
    gap = lambda s: np.zeros(int(SR * s), dtype=np.float32)

    # (秒, シーン, その場面の音)
    plan = [
        (1.3, lambda i: scene_hook(i), [tone(660, 0.15), gap(0.2)]),
        (1.8, lambda i: scene_dinner(i), [tone(880, 0.12, 0.04)]),
        (1.8, lambda i: scene_toss(i, int(1.8 * FPS)), [tone(1100, 0.1, 0.04)]),
        (2.4, lambda i: scene_don(i), [tone(90, 0.4, 0.25, 6), gap(0.3), say(pipe, "abandon", "bf_emma")]),
        (4.2, lambda i: scene_meaning(i), [gap(0.2), say(pipe, "Abandon.", "bm_george"), gap(0.4), say(pipe, "They abandoned the old boat.", "bf_emma")]),
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    frames, audio = [], []
    for dur, draw, sounds in plan:
        n = int(dur * FPS)
        clip = np.concatenate(sounds)
        need = int(dur * SR)
        audio.append(np.concatenate([clip, gap(max(0, need - len(clip)) / SR)])[:max(need, len(clip))])
        for i in range(n):
            img = draw(i)
            frames.append(finish(img, len(frames)))
    total = len(frames) / FPS
    out = OUT / "abandon.mp4"
    with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
        sf.write(wav.name, np.concatenate(audio), SR)
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-i", wav.name, "-stream_loop", "-1", "-i", str(ROOT / "assets" / "manga_bgm" / "cozy-places.mp3"),
               "-filter_complex", f"[2:a]volume=0.06[b];[1:a]aresample=44100,volume=1.6[v];[v][b]amix=inputs=2:duration=first:normalize=0[a]",
               "-map", "0:v", "-map", "[a]", "-t", f"{total:.2f}", "-r", "30",
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "aac", "-movflags", "+faststart", str(out)]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for f in frames:
            p.stdin.write(f.tobytes())
        p.stdin.close()
        p.wait()
    print(f"✓ {out}({total:.1f}秒)")


if __name__ == "__main__":
    main()
