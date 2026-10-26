"""4コマを紙芝居リールにする(コマを1つずつ大きく見せ、セリフを読み上げる)。

    .venv-tts/bin/python manga_reel.py inside_out            # out/manga/inside_out_reel.mp4(やわらかい効果音)
    .venv-tts/bin/python manga_reel.py inside_out --no-sfx   # out/manga/inside_out_reel_nosfx.mp4(効果音なし)

声:ElevenLabs(ナビ=Teddy・ペン=Candy・部長=Gappu。ELEVEN 参照)。--kokoro で無料の Kokoro に戻す。後ろにかすかなBGM(--bgm cozy-places などで指定)。
コマの切り替えにやわらかい効果音、ズームはしない。投稿はリールのみ(カルーセルはなし)
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
# 声(Kokoro の声, 声の高さの倍率)。かわいい系も試したが、元の声のほうが良いとのことで戻した
VOICE = {
    "navi": ("b", "bm_george", 1.0),  # フクロウのナビ:イギリス英語・男性
    "pen": ("b", "bf_emma", 1.0),     # ペンギンのペン:イギリス英語・女性
    "boss": ("a", "am_michael", 1.0), # カピバラ部長
}
# 後ろでかすかに流す曲(Uppbeat)。回ごとに順番に使う
BGM = [("cozy-places", "Cozy Places", "Yokonap"), ("sketch-book", "Sketch Book", "Prigida"), ("summer-vibes", "Summer Vibes", "Movediz")]
BGM_VOLUME = 0.07

# コマごとに読み上げるセリフ(話す人, 英語)。最後は解説の画面
SCRIPTS = {
    "the_thing_is": dict(lines=[("navi", "Let's go to the beach!"), ("pen", "I'd love to, but the thing is..."),
                                ("pen", "I melt in summer."), ("navi", "You're not ice cream!")],
                         explain=[("navi", "The thing is."), ("pen", "I'd love to help, but the thing is, I'm busy today.")]),
    "by_far": dict(lines=[("navi", "Which snack do you like?"), ("pen", "This one is by far the best."),
                          ("navi", "That's a fish."), ("pen", "Fish is a snack.")],
                   explain=[("navi", "By far."), ("pen", "Summer is by far my favorite season.")]),
    "lead_a_workshop": dict(lines=[("boss", "Today, I'll lead a workshop."), ("navi", "The topic is...?"),
                                   ("boss", "Step one: sleep."), ("navi", "Great workshop.")],
                            explain=[("navi", "Lead a workshop."), ("boss", "I'll lead a short workshop for new staff next week.")]),
    "make_an_appointment": dict(lines=[("navi", "Did you make an appointment?"), ("pen", "Yes! Today at three."),
                                       ("pen", "Hello...?"), ("navi", "Pen... today is Sunday.")],
                                explain=[("navi", "Make an appointment."), ("pen", "I need to make an appointment with my dentist.")]),
    "from_time_to_time": dict(lines=[("navi", "Do you exercise?"), ("pen", "From time to time."),
                                     ("pen", "This is my workout."), ("navi", "That's just sliding!")],
                              explain=[("navi", "From time to time."), ("pen", "We still meet for coffee from time to time.")]),
    "company_cafeteria": dict(
        lines=[("navi", "Where's the boss?"), ("pen", "Probably in the company cafeteria."),
               ("boss", "This is my office."), ("navi", "Boss, it's 10 a.m.!")],
        explain=[("navi", "The company cafeteria."), ("pen", "The company cafeteria gets crowded at noon.")],
    ),
    "baggage_claim": dict(
        lines=[("navi", "Let's go to baggage claim."), ("pen", "Where's my suitcase?"),
               ("boss", "Ahh... nice ride."), ("navi", "Boss! That's not a ride!")],
        explain=[("navi", "Baggage claim."), ("boss", "I waited at baggage claim for twenty minutes.")],
    ),
    "wet_to_the_skin": dict(
        lines=[("navi", "It's raining! Take an umbrella."), ("pen", "No need. I'm a penguin."),
               ("navi", "You're wet to the skin!"), ("pen", "I like the sea... not the rain.")],
        explain=[("navi", "Wet to the skin."), ("pen", "I forgot my umbrella and got wet to the skin.")],
    ),
    "inside_out": dict(
        lines=[("pen", "Morning!"), ("navi", "Your hat is inside out!"), ("pen", "I know. It's the new trend."), ("navi", "Me too.")],
        explain=[("navi", "Inside out."), ("pen", "My son wore his sweater inside out.")],
    ),
}


# ElevenLabs の声(ボイスライブラリ・商用可)。.env に ELEVENLABS_API_KEY があれば使う。--kokoro で無料の声に戻す
ELEVEN = {
    "navi": "XjGYkUkzth8BPs29fmcV",  # Teddy Twinkle(かわいい男の子)
    "pen": "Nggzl2QAXh3OijoXD116",   # Candy(若くてかわいい女性)
    "boss": "tBPQ3sUKpdLEVpyeCHyk",  # Gappu ka Bhai(のんびりした声)
}
ELEVEN_CACHE = ROOT / "out" / "voice_cache"


def eleven(who, text):
    """ElevenLabs で読み上げ、24kHz の波形を返す。同じセリフはキャッシュして、クレジットを使い直さない。"""
    import hashlib
    import json
    import os
    import urllib.request
    vid = ELEVEN[who]
    ELEVEN_CACHE.mkdir(parents=True, exist_ok=True)
    mp3 = ELEVEN_CACHE / f"{vid}_{hashlib.sha1(text.encode()).hexdigest()[:12]}.mp3"
    if not mp3.exists():
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_128",
            data=json.dumps({"text": text, "model_id": "eleven_multilingual_v2"}).encode(),
            headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json", "Accept": "audio/mpeg"})
        mp3.write_bytes(urllib.request.urlopen(req).read())
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp3), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def load_env():
    import os
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


class Voice:
    def __init__(self):
        import os
        load_env()
        self.use_eleven = bool(os.environ.get("ELEVENLABS_API_KEY")) and "--kokoro" not in sys.argv
        self.pipes = {}
        if not self.use_eleven:
            from kokoro import KPipeline
            self.KPipeline = KPipeline

    def __call__(self, who, text):
        if self.use_eleven:
            return eleven(who, text)
        lang, name, pitch = VOICE[who]
        if lang not in self.pipes:
            self.pipes[lang] = self.KPipeline(lang_code=lang, repo_id="hexgrad/Kokoro-82M")
        # 少しゆっくり読ませてから詰めることで、速さを保ったまま声を高くする
        a = np.concatenate([x for _, _, x in self.pipes[lang](text, voice=name, speed=0.9 / pitch)])
        idx = np.arange(0, len(a) - 1, pitch)
        return np.interp(idx, np.arange(len(a)), a).astype(np.float32)


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
    d.text((W - 60, H - 70), manga.HANDLE, font=manga.EN(40), fill=(160, 150, 140), anchor="rm")
    return img


SFX_MODE = "soft"  # soft:やわらかい木琴風の音 / none:音なし


def pop():
    """コマが切り替わるときの効果音。木琴(マリンバ)風の2音を小さく。none なら無音。"""
    if SFX_MODE == "none":
        return silence(0.01)
    out = []
    for f0, dur in ((1046.5, 0.09), (1318.5, 0.22)):  # ド→ミ
        t = np.arange(int(SR * dur)) / SR
        env = np.minimum(1, t / 0.004) * np.exp(-t * 14)
        tone = np.sin(2 * np.pi * f0 * t) + 0.35 * np.sin(2 * np.pi * f0 * 4 * t) * np.exp(-t * 40)
        out.append((0.07 * tone * env).astype(np.float32))
    return np.concatenate(out)


def main():
    global SFX_MODE
    argv = sys.argv[1:]
    if "--bgm" in argv:
        i = argv.index("--bgm"); argv = argv[:i] + argv[i + 2:]
    args = [a for a in argv if not a.startswith("--")]
    name = args[0] if args else "inside_out"
    SFX_MODE = "none" if "--no-sfx" in sys.argv else "soft"
    draw, ex = manga.SCRIPTS[name]
    comic = draw()
    boxes = comic.info["boxes"]
    explain = manga.explain(*ex)
    sc = SCRIPTS[name]
    voice = Voice()
    bgm = BGM[sorted(SCRIPTS).index(name) % len(BGM)] if "--bgm" not in " ".join(sys.argv) else \
        next(b for b in BGM if b[0] == sys.argv[sys.argv.index("--bgm") + 1])

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
    out = OUT / f"{name}_reel{'_nosfx' if SFX_MODE == 'none' else ''}.mp4"
    with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
        import soundfile as sf
        sf.write(wav.name, np.concatenate(audio), SR)
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-i", wav.name, "-stream_loop", "-1", "-i", str(ROOT / "assets" / "manga_bgm" / f"{bgm[0]}.mp3"),
               "-filter_complex", f"[2:a]volume={BGM_VOLUME},afade=t=in:d=1,afade=t=out:st={total - 1.5}:d=1.5[b];"
               "[1:a]aresample=44100,volume=1.6[v];[v][b]amix=inputs=2:duration=first:normalize=0[a]",
               "-map", "0:v", "-map", "[a]", "-t", f"{total:.2f}",
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
    print(f"✓ {out}({total:.1f}秒・BGM: {bgm[1]} / {bgm[2]})")


if __name__ == "__main__":
    main()
