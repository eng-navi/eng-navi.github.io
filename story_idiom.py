"""10選の表現をストーリー2枚にする(1枚目:問題の画像、2枚目:答えの動画+イギリス英語の音声)。

    .venv-tts/bin/python story_idiom.py 1 1     # 10選1 の 1個目 → out/story_idiom/1_1_q.png, 1_1_a.mp4
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

import story_book as sb

ROOT = Path(__file__).parent
OUT = ROOT / "out" / "story_idiom"
W, H = 1080, 1920
GAP = 0.6  # 読み上げの間の無音(秒)
VOICES = [("uk_f", "イギリス英語・女性"), ("uk_m", "イギリス英語・男性")]


def paper():
    img = Image.new("RGB", (W, H), sb.PAPER)
    d = ImageDraw.Draw(img)
    for x in range(0, W, 54):
        d.line([(x, 0), (x, H)], fill=sb.GRID, width=2)
    for y in range(0, H, 54):
        d.line([(0, y), (W, y)], fill=sb.GRID, width=2)
    return img, d


def fit(d, text, font_fn, size, max_w):
    while size > 40 and d.textlength(text, font=font_fn(size)) > max_w:
        size -= 4
    return font_fn(size)


def speaker(d, x, y, color, s=1.0):
    d.polygon([(x, y - 14 * s), (x + 14 * s, y - 14 * s), (x + 32 * s, y - 30 * s), (x + 32 * s, y + 30 * s),
               (x + 14 * s, y + 14 * s), (x, y + 14 * s)], fill=color)
    for r in (22, 38):
        d.arc([x + 32 * s - r * s, y - r * s, x + 32 * s + r * s, y + r * s], -45, 45, fill=color, width=int(5 * s))


def wrap(d, text, font, max_w):
    lines, cur = [], ""
    for w in text.split(" "):
        t = f"{cur} {w}".strip()
        if d.textlength(t, font=font) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + [cur]


def question(phrase):
    img, d = paper()
    d.text((W // 2, 300), "Q.", font=sb.EN(150), fill=sb.RED, anchor="ms")
    f = fit(d, phrase, sb.EN, 170, 900)
    d.text((W // 2, 820), phrase, font=f, fill=sb.INK, anchor="ms")
    tw = d.textlength(phrase, font=f) / 2
    sb.underline(d, W // 2 - tw - 10, W // 2 + tw + 10, 860, w=8)
    d.text((W // 2, 1000), "ってどういう意味？", font=sb.JP(80), fill=sb.INK, anchor="ms")
    sb.star(d, 170, 560, 30)
    sb.star(d, 900, 1130, 24)
    d.text((W // 2, 1420), "考えてから、次のストーリーへ", font=sb.JP(50), fill=sb.INK, anchor="ms")
    sb.arrow(d, sb.curve((W // 2 - 80, 1480), (W // 2, 1560), (W // 2 + 90, 1500)), color=sb.RED, w=6, head=26)
    d.text((W // 2, 1700), "答えは音声つき", font=sb.JP(40), fill=(120, 120, 120), anchor="ms")
    d.text((W // 2, 1820), "@eng_navi", font=sb.EN(40), fill=(150, 150, 150), anchor="ms")
    return img


def answer(phrase, ja, en, en_ja, active):
    img, d = paper()
    speaker(d, 330, 170, sb.RED, 0.9)
    d.text((395, 190), "音声つき", font=sb.JP(46), fill=sb.RED, anchor="ls")
    d.text((W // 2, 400), "A.", font=sb.EN(120), fill=sb.RED, anchor="ms")
    f = fit(d, phrase, sb.EN, 140, 920)
    d.text((W // 2, 620), phrase, font=f, fill=sb.INK, anchor="ms")
    jf = fit(d, ja, sb.JP, 84, 920)
    d.text((W // 2, 790), ja, font=jf, fill=sb.RED, anchor="ms")
    tw = d.textlength(ja, font=jf) / 2
    sb.underline(d, W // 2 - tw - 10, W // 2 + tw + 10, 820, w=7)
    d.rounded_rectangle([90, 920, W - 90, 1420], radius=28, fill=(255, 255, 255))
    d.text((140, 990), "例文", font=sb.JP(40), fill=(150, 150, 150), anchor="ls")
    ef = sb.EN(60)
    y = 1080
    for line in wrap(d, en, ef, 800):
        d.text((W // 2, y), line, font=ef, fill=sb.INK, anchor="ms")
        y += 80
    for line in wrap(d, en_ja, sb.JP(40), 820) if " " in en_ja else [en_ja]:
        d.text((W // 2, y + 30), line, font=sb.JP(40), fill=(110, 110, 110), anchor="ms")
        y += 56
    # どちらの声が読んでいるか
    for i, (_, label) in enumerate(VOICES):
        x0, y0 = 120 + i * 440, 1530
        on = i == active
        d.rounded_rectangle([x0, y0, x0 + 400, y0 + 110], radius=55,
                            fill=sb.RED if on else (255, 255, 255), outline=sb.RED, width=4)
        speaker(d, x0 + 40, y0 + 55, (255, 255, 255) if on else sb.RED, 0.6)
        d.text((x0 + 235, y0 + 70), label, font=sb.JP(34), fill=(255, 255, 255) if on else sb.RED, anchor="ms")
    # URL は貼れないので、プロフィールのリンク(サイトのトップに今週の10選がある)へ案内する
    note = "10個まとめて音声で → プロフィールのリンクから"
    nx = (W - (d.textlength(note, font=sb.JP(36)) + 50)) / 2
    speaker(d, nx, 1745, sb.INK, 0.55)
    d.text((nx + 50, 1760), note, font=sb.JP(36), fill=sb.INK, anchor="ls")
    d.text((W // 2, 1860), "@eng_navi", font=sb.EN(38), fill=(150, 150, 150), anchor="ms")
    return img


def duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                                capture_output=True, text=True).stdout)


def main(list_id, n, engine=None):
    import tts
    item = next(l for l in json.loads((ROOT / "threads_lists.json").read_text()) if l["id"] == list_id)["items"][n - 1]
    phrase, ja, en, en_ja = item
    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / f"{list_id}_{n}"
    question(phrase).save(f"{stem}_q.png")
    engine = engine or tts.Kokoro()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        parts, frames = [], []
        for i, (v, _) in enumerate(VOICES):
            clip = tmp / f"{v}.mp3"
            engine(f"{phrase}. {en}", clip, v)  # 表現 → 例文
            parts.append(clip)
            frame = tmp / f"{v}.png"
            answer(phrase, ja, en, en_ja, i).save(frame)
            frames.append((frame, duration(clip) + GAP + (0.8 if i == 0 else 1.5)))
        # 頭に0.8秒の間を入れて、声と表示を切り替える
        listing = tmp / "frames.txt"
        listing.write_text("".join(f"file '{f}'\nduration {d:.2f}\n" for f, d in frames) + f"file '{frames[-1][0]}'\n")
        audio = tmp / "audio.m4a"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-t", "0.8", "-i", "anullsrc=r=24000:cl=mono",
                        "-i", str(parts[0]), "-f", "lavfi", "-t", str(GAP + 0.8), "-i", "anullsrc=r=24000:cl=mono",
                        "-i", str(parts[1]), "-f", "lavfi", "-t", "1.5", "-i", "anullsrc=r=24000:cl=mono",
                        "-filter_complex", "[0][1][2][3][4]concat=n=5:v=0:a=1,aresample=44100", "-c:a", "aac", str(audio)], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-i", str(audio),
                        "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-c:a", "copy", "-shortest",
                        "-movflags", "+faststart", f"{stem}_a.mp4"], check=True)
    print(f"✓ {stem}_q.png / {stem}_a.mp4")


if __name__ == "__main__":
    import tts
    lid = int(sys.argv[1])
    nums = [int(sys.argv[2])] if len(sys.argv) > 2 else range(1, 11)
    eng = tts.Kokoro()
    for k in nums:
        main(lid, k, eng)
