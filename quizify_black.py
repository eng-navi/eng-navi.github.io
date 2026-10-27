"""@quizify_english の黒い「瞬間英作文クイズ」リール(準1級の単語)を作る。

1語ごとに 英単語 → 日本語の意味 → 日本語の例文 → (考える間) → 英語の例文 の順。
間は 2024年の元動画(274〜276)を 0.01 秒単位で測った値。声は前後の無音を切ってから、この間で並べる。

  .venv-tts/bin/python quizify_black.py      → out/quizify/black_<最初の番号>.mp4
"""
import hashlib
import json
import os
import subprocess
import tempfile
import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont

import manga_reel as mr

ROOT = Path(__file__).parent
OUT = ROOT / "out" / "quizify"
CACHE = ROOT / "out" / "voice_cache"
FONTS = ROOT / "assets" / "fonts"
SR = 44100
W, H, FPS = 720, 1280, 30

# 声(ElevenLabs)。元動画にいちばん近かったもの。速さは元の読む長さに合わせた
EN_VOICE, EN_SPEED = "pFZP5JQG7iQjIQuC4Bku", 1.07  # Lily(イギリス英語・女性)
# 日本語は音読さんの「ななみ(案内)」= Microsoft の Nanami。元は速度 ×1.3 だが、長さを測ると 1.22 倍が同じになる
JA_VOICE, JA_SPEED = "ja-JP-NanamiNeural", 1.22

# 間(秒)。声が聞こえ始める・聞こえなくなる瞬間どうしの間隔
LEAD = 0.63        # 動画の頭 → 英単語
WORD_MEAN = 0.95   # 英単語 → 意味
MEAN_JA = 0.86     # 意味 → 日本語の例文
JA_EN = 1.67       # 日本語の例文 → 英語の例文(考える間)
EN_NEXT = 0.95     # 英語の例文 → 次の英単語
TAIL = 0.65        # 最後の英語の例文 → 動画の終わり
# 画面は声より少し先に切り替わる
SHOW_EARLY = 0.12  # 意味・日本語の例文
EN_EARLY = 0.18    # 英語の例文
NEXT_AFTER = 0.40  # 英語の例文が終わってから次の単語の画面へ

BG = (29, 29, 29)
MINT = (160, 228, 195)
WHITE = (251, 251, 251)

ITEMS = [
    # 番号, 英単語, 画面の意味, 読む意味, 日本語の例文, 英語の例文
    (277, "scrutinize", "精査する、詳しく調べる", "精査する",
     "委員会は予算案を精査した。", "The committee scrutinized the budget."),
    (278, "plausible", "もっともらしい", "もっともらしい",
     "彼の説明はもっともらしい。", "His explanation sounds plausible."),
    (279, "deteriorate", "悪化する", "悪化する",
     "天気が急に悪化した。", "The weather suddenly deteriorated."),
]


def font(name, size, weight=None):
    f = ImageFont.truetype(str(FONTS / name), size)
    if weight:
        f.set_variation_by_axes(weight)
    return f


NUM = font("EBGaramond-Italic%5Bwght%5D.ttf", 60, [400])
TITLE = font("MPLUSRounded1c-Light.ttf", 47)
MEAN = font("MPLUSRounded1c-Light.ttf", 37)
JA = font("MPLUSRounded1c-Light.ttf", 31)
WORD = font("OpenSans%5Bwdth,wght%5D.ttf", 40, [700, 100])
EN = font("OpenSans%5Bwdth,wght%5D.ttf", 37, [700, 100])


# 音量(RMS)。元動画は日本語のほうが英語より 5dB ほど大きい
LEVEL = {EN_VOICE: 0.092, JA_VOICE: 0.163}


def tts(vid, text, speed):
    CACHE.mkdir(parents=True, exist_ok=True)
    mp3 = CACHE / f"{vid}_{hashlib.sha1(f'{text}|{speed}'.encode()).hexdigest()[:12]}.mp3"
    if not mp3.exists() and vid.startswith("ja-JP-"):
        subprocess.run([str(ROOT / ".venv-tts" / "bin" / "edge-tts"), "--voice", vid, f"--rate=+{round((speed - 1) * 100)}%",
                        "--text", text, "--write-media", str(mp3)], check=True, capture_output=True)
    if not mp3.exists():
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_128",
            data=json.dumps({"text": text, "model_id": "eleven_multilingual_v2",
                             "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "speed": speed}}).encode(),
            headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"})
        mp3.write_bytes(urllib.request.urlopen(req).read())
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp3), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32).copy()
    a = a * (LEVEL[vid] / (float(np.sqrt(np.mean(a ** 2))) or 1.0))
    a = np.tanh(a * 1.2) / 1.2  # 大きく入れても割れないように、山だけやわらかく抑える
    # 音量をそろえてから、前後の無音を切る(-45dB より小さいところ)
    # 測ったときと同じく 16kHz に直したもので調べる
    a16 = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                          "-ar", "16000", "-f", "f32le", "-"], input=a.tobytes(), capture_output=True, check=True).stdout
    a16 = np.frombuffer(a16, np.float32)
    db = 20 * np.log10(np.array([np.sqrt(np.mean(a16[i:i + 160] ** 2)) for i in range(0, len(a16) - 160, 160)]) + 1e-9)
    hop = int(SR * 0.01)
    # 元動画を測ったときと同じ決まりで、声の始まりと終わりを決める
    # (-45dB 以上を声とし、0.15秒未満のすき間はつなげ、0.05秒未満の小さな音は息として数えない)
    segs, start = [], None
    for i, loud in enumerate(db > -45):
        if loud and start is None:
            start = i
        if not loud and start is not None:
            segs.append([start, i])
            start = None
    if start is not None:
        segs.append([start, len(db)])
    merged = [segs[0]]
    for s0, s1 in segs[1:]:
        if s0 - merged[-1][1] < 15:
            merged[-1][1] = s1
        else:
            merged.append([s0, s1])
    merged = [m for m in merged if m[1] - m[0] >= 5]
    return a[merged[0][0] * hop:merged[-1][1] * hop]


def spaced(d, xy, text, f, fill, track):
    """字間をあけて書く(日本語)。"""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill, anchor="ls")
        x += d.textlength(ch, font=f) + track


def spaced_width(d, text, f, track):
    return sum(d.textlength(ch, font=f) + track for ch in text) - track


def wrap(d, text, f, width, track=0, words=True):
    lines, cur = [], ""
    for tok in (text.split(" ") if words else list(text)):
        nxt = (cur + " " + tok).strip() if words else cur + tok
        w = d.textlength(nxt, font=f) if words else spaced_width(d, nxt, f, track)
        if cur and w > width:
            lines.append(cur)
            cur = tok
        else:
            cur = nxt
    return lines + [cur]


def frame(item, stage):
    """stage: word / mean / ja / en"""
    no, word, mean, _, ja, en = item
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    spaced(d, (104, 451), "瞬間英作文クイズ", TITLE, MINT, 5)
    if stage in ("word", "mean"):
        d.text((101, 176), str(no), font=NUM, fill=MINT, anchor="ls")
        d.text((104, 620), word, font=WORD, fill=WHITE, anchor="ls")
        if stage == "mean":
            spaced(d, (104, 786), mean, MEAN, MINT, 3)
        return im
    for i, line in enumerate(wrap(d, ja, JA, 430, 3, words=False)):
        spaced(d, (104, 777 + i * 58), line, JA, MINT, 3)
    if stage == "en":
        lines = wrap(d, en, EN, 440)
        top = 611 - (len(lines) - 1) * 31
        for i, line in enumerate(lines):
            d.text((103, top + i * 62), line, font=EN, fill=WHITE, anchor="ls")
    return im


def build(items, out):
    voice, cuts = [], []  # cuts: (秒, item, stage)
    t = LEAD
    voice.append(np.zeros(int(SR * LEAD), np.float32))
    for k, item in enumerate(items):
        _, word, _, said, ja, en = item
        parts = [(tts(EN_VOICE, word, EN_SPEED), WORD_MEAN, "word"),
                 (tts(JA_VOICE, said, JA_SPEED), MEAN_JA, "mean"),
                 (tts(JA_VOICE, ja, JA_SPEED), JA_EN, "ja"),
                 (tts(EN_VOICE, en, EN_SPEED), TAIL if k == len(items) - 1 else EN_NEXT, "en")]
        for clip, gap, stage in parts:
            early = {"word": 0, "mean": SHOW_EARLY, "ja": SHOW_EARLY, "en": EN_EARLY}[stage]
            if stage == "word":
                cuts.append((0.0 if k == 0 else cuts[-1][3] + NEXT_AFTER, item, stage, None))
            else:
                cuts.append((t - early, item, stage, None))
            voice += [clip, np.zeros(int(SR * gap), np.float32)]
            t += len(clip) / SR
            if stage == "en":
                cuts[-1] = cuts[-1][:3] + (t,)  # 英語の例文が終わった時刻
            t += gap
    audio = np.concatenate(voice)
    print(f"  peak {float(np.max(np.abs(audio))):.2f}")
    total = len(audio) / SR
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
        sf.write(wav.name, audio, SR)
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                              "-r", str(FPS), "-i", "-", "-i", wav.name, "-t", f"{total:.3f}",
                              "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-c:a", "aac", "-b:a", "192k",
                              "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
        frames = {}
        for n in range(int(round(total * FPS))):
            now = n / FPS
            cur = max((c for c in cuts if c[0] <= now), key=lambda c: c[0])
            key = (cur[1][0], cur[2])
            if key not in frames:
                frames = {key: frame(cur[1], cur[2]).tobytes()}
            p.stdin.write(frames[key])
        p.stdin.close()
        p.wait()
    print(f"✓ {out.relative_to(ROOT)}({total:.2f}秒)")
    for c in cuts:
        print(f"  {c[0]:6.2f}  {c[1][0]} {c[2]}")


if __name__ == "__main__":
    mr.load_env()
    build(ITEMS, OUT / f"black_{ITEMS[0][0]}.mp4")
