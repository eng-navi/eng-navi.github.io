"""4コマを紙芝居リールにする(コマを1つずつ大きく見せ、セリフを読み上げる)。

    .venv-tts/bin/python manga_reel.py inside_out     # out/manga/inside_out_reel.mp4

声:ナビ(フクロウ)= イギリス英語・男性 / ペン(ペンギン)= イギリス英語・女性
BGMなし(セリフを聞き取りやすく、飽きないように)。コマの切り替えに小さな効果音、ズームはしない
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import manga

ROOT = Path(__file__).parent
OUT = ROOT / "out" / "manga"
W, H, FPS, SR = 1080, 1920, 30, 24000
VOICE = {"navi": ("b", "bm_george"), "pen": ("b", "bf_emma")}

# コマごとに読み上げるセリフ(話す人, 英語)。最後は解説の画面
SCRIPTS = {
    "inside_out": dict(
        lines=[("pen", "Morning!"), ("navi", "Your hat is inside out!"), ("pen", "I know. It's the new trend."), ("navi", "Me too.")],
        explain=[("navi", "Inside out."), ("pen", "My son wore his sweater inside out.")],
    ),
}


class Voice:
    def __init__(self):
        from kokoro import KPipeline
        self.pipes = {}
        self.KPipeline = KPipeline

    def __call__(self, who, text):
        lang, name = VOICE[who]
        if lang not in self.pipes:
            self.pipes[lang] = self.KPipeline(lang_code=lang, repo_id="hexgrad/Kokoro-82M")
        return np.concatenate([a for _, _, a in self.pipes[lang](text, voice=name, speed=0.9)])


def silence(sec):
    return np.zeros(int(SR * sec), dtype=np.float32)


def frame_for(src, t, dur, title):
    """コマを中央に大きく置き、ゆっくりズームする。"""
    img = Image.new("RGB", (W, H), (244, 241, 234))
    d = ImageDraw.Draw(img)
    d.text((W // 2, 170), title, font=manga.EN(90), fill=manga.INK, anchor="mm")
    d.text((W // 2, 250), "4コマで覚える英語", font=manga.JP(40), fill=(150, 140, 130), anchor="mm")
    # ズームはせず、出る瞬間だけ少しふわっと(0.15秒)
    z = 1.0 if t >= 0.15 else 0.96 + 0.04 * (t / 0.15)
    tw = int(980 * z)
    th = int(src.height * tw / src.width)
    im = src.resize((tw, th), Image.LANCZOS)
    img.paste(im, ((W - tw) // 2, 330 + (1320 - th) // 2))
    d.text((W - 60, H - 70), "@eng_navi", font=manga.EN(40), fill=(160, 150, 140), anchor="rm")
    return img


def pop():
    """コマが切り替わるときの小さな「ポン」という音。"""
    t = np.arange(int(SR * 0.12)) / SR
    freq = 880 * np.exp(-t * 18) + 440
    return (0.18 * np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 30)).astype(np.float32)


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "inside_out"
    draw, ex = manga.SCRIPTS[name]
    comic = draw()
    boxes = comic.info["boxes"]
    explain = manga.explain(*ex)
    sc = SCRIPTS[name]
    voice = Voice()

    scenes, audio = [], []  # scenes: (画像, 秒)
    for box, (who, text) in zip(boxes, sc["lines"]):
        clip = voice(who, text)
        dur = len(clip) / SR + 0.9
        p = pop()
        audio += [p, silence(0.35 - len(p) / SR), clip, silence(dur - len(clip) / SR - 0.35)]
        scenes.append((comic.crop(tuple(int(v) for v in box)), dur))
    # 全体の4コマを一瞬見せてから、解説(2人が読み上げる)
    scenes.append((comic, 1.6))
    audio.append(silence(1.6))
    ex_audio = [pop(), silence(0.3)]
    for who, text in sc["explain"]:
        ex_audio += [voice(who, text), silence(0.5)]
    ex_audio.append(silence(0.5))
    ex_clip = np.concatenate(ex_audio)
    scenes.append((explain, len(ex_clip) / SR))
    audio.append(ex_clip)
    total = sum(d for _, d in scenes)

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{name}_reel.mp4"
    with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
        import soundfile as sf
        sf.write(wav.name, np.concatenate(audio), SR)
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-i", wav.name, "-map", "0:v", "-map", "1:a", "-af", "volume=1.6", "-t", f"{total:.2f}",
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "aac", "-movflags", "+faststart", str(out)]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for src, dur in scenes:
            if src.size == (manga.W, manga.H) and src is explain:
                # 解説は縦長の画面に合わせて置く
                img = Image.new("RGB", (W, H), (244, 241, 234))
                g = ImageDraw.Draw(img)
                for x in range(0, W, 54):
                    g.line([(x, 0), (x, H)], fill=(225, 220, 212), width=2)
                for y in range(0, H, 54):
                    g.line([(0, y), (W, y)], fill=(225, 220, 212), width=2)
                img.paste(src, (0, (H - src.height) // 2))
                frame = img.tobytes()
                for i in range(int(dur * FPS)):
                    proc.stdin.write(frame)
                continue
            title = manga.SCRIPTS[name][1][0]
            for i in range(int(dur * FPS)):
                proc.stdin.write(frame_for(src, i / FPS, dur, title).tobytes())
        proc.stdin.close()
        proc.wait()
    print(f"✓ {out}({total:.1f}秒)")


if __name__ == "__main__":
    main()
