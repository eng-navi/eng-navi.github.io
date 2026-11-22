"""YouTube の「まとめ動画」(ショートを番号順につないだ長い動画)とサムネイルを作る。

    python3 yt_compile.py thumb  eng_navi 101 200      # サムネイルだけ
    python3 yt_compile.py video  eng_navi 101 200      # 動画+サムネ+タイトル・説明欄(チャプターつき)

- 動画は縦長のまま(元が縦長なので)。出力は out/yt_compile/
- YouTube の長い動画は Buffer で投稿できないので、YouTube Studio から手で上げる
- サムネイルは過去のまとめ動画と同じ形(暗い煙の背景・大きな白い見出し・中央にキャラ・右下に黄色の文字・金の数字・左上のリボン)。
  人物の写真は使わず、eng_navi のキャラ(フクロウのナビ・ペンギンのペン)を描く
"""
import json
import math
import random
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import manga

ROOT = Path(__file__).parent
OUT = ROOT / "out" / "yt_compile"
HV = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"
HM = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
GOLD_FONT = str(ROOT / "fonts" / "EBGaramond.ttf")
TW, TH = 1280, 720

# まとめる種類ごとの設定
KINDS = {
    "eng_navi": dict(files=lambda n: ROOT / "out" / "eng_navi" / f"q{n}.mp4", head="英文法", sub=("英検・TOEIC", "2択クイズ"),
                     title="【英文法クイズ{a}〜{b}】英検・TOEICによく出る文法とイディオム｜聞き流しOK",
                     char="owl"),
    "listening": dict(files=lambda n: ROOT / "out" / "quizify" / f"listening_{n}.mp4", head="リスニング",
                      sub=("TOEIC", "1回で聞き取る"), title="【TOEICリスニング{a}〜{b}】1回で聞き取れる?英語耳トレーニング",
                      char="penguin"),
    "white": dict(files=lambda n: ROOT / "out" / "quizify" / f"white_{n}.mp4", head="英単語", sub=("入試・英検", "よく出る形"),
                  title="【英単語{a}〜{b}】入試・英検でよく出る表現｜例文つき聞き流し", char="owl"),
    "black": dict(files=lambda n: ROOT / "out" / "quizify" / f"black_{n}.mp4", head="英検準1級", sub=("瞬間", "英作文"),
                  title="【瞬間英作文{a}〜{b}】英検準1級の単語｜例文つき聞き流し", char="penguin"),
}


def smoke_bg():
    random.seed(7)
    im = Image.new("RGB", (TW, TH), (28, 31, 36))
    fog = Image.new("L", (TW, TH), 0)
    d = ImageDraw.Draw(fog)
    for _ in range(70):  # 下ほど濃い煙
        x, y = random.uniform(-100, TW + 100), random.uniform(TH * 0.25, TH + 80)
        r = random.uniform(60, 190)
        d.ellipse([x - r, y - r * 0.7, x + r, y + r * 0.7], fill=int(random.uniform(40, 95) * (y / TH)))
    fog = fog.filter(ImageFilter.GaussianBlur(38))
    im.paste((175, 180, 188), (0, 0), fog)
    return im


def gold_text(base, xy, text, size):
    f = ImageFont.truetype(GOLD_FONT, size)
    mask = Image.new("L", base.size, 0)
    ImageDraw.Draw(mask).text(xy, text, font=f, fill=255, anchor="ls")
    grad = Image.new("RGB", base.size)
    gd = ImageDraw.Draw(grad)
    top = xy[1] - size
    for y in range(base.size[1]):
        t = min(1, max(0, (y - top) / size))
        c = (int(250 - 70 * t), int(220 - 90 * t), int(120 - 80 * t)) if t < 0.55 else (int(230 - 60 * (t - .55)), int(170 - 40 * (t - .55)), 60)
        gd.line([(0, y), (base.size[0], y)], fill=c)
    shadow = mask.filter(ImageFilter.GaussianBlur(4))
    base.paste((0, 0, 0), (4, 5), shadow)
    base.paste(grad, (0, 0), mask)


def character(kind, s=300):
    """キャラを透明の板に大きく描く(2倍で描いて縮める)。"""
    k = 2
    layer = Image.new("RGBA", (int(s * 1.6 * k), int(s * 1.9 * k)), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = layer.width // 2, int(layer.height * 0.42)
    if kind == "owl":
        manga.owl(d, cx, cy, s * k, expr="happy", hat_on=True)
    else:
        manga.penguin(d, cx, cy, s * k, expr="normal", hat_on=True)
    return layer.resize((layer.width // k, layer.height // k), Image.LANCZOS)


def thumbnail(kind, a, b, path):
    cfg = KINDS[kind]
    im = smoke_bg()
    d = ImageDraw.Draw(im)
    # 見出し(大きな白い字)
    head = cfg["head"]
    size = 250 if len(head) <= 4 else 200
    f = ImageFont.truetype(HV, size)
    while d.textlength(head, font=f) > TW - 80:
        size -= 10
        f = ImageFont.truetype(HV, size)
    d.text((TW // 2 + 4, 40 + 6), head, font=f, fill=(0, 0, 0), anchor="mt")
    d.text((TW // 2, 40), head, font=f, fill=(255, 255, 255), anchor="mt")
    # キャラ(中央、見出しに少しかぶせる)
    ch = character(cfg["char"], 300)
    sh = Image.new("RGBA", ch.size, (0, 0, 0, 0))
    sh.putalpha(ch.getchannel("A").point(lambda v: v * 0.5).filter(ImageFilter.GaussianBlur(12)))
    x, y = TW // 2 - ch.width // 2, TH - ch.height + 40
    im.paste(sh, (x + 10, y + 14), sh)
    im.paste(ch, (x, y), ch)
    # 右下の黄色い字
    fy = ImageFont.truetype(HM, 64)
    for i, line in enumerate(cfg["sub"]):
        d.text((TW - 70, 470 + i * 92), line, font=fy, fill=(0, 0, 0), anchor="rt", stroke_width=6, stroke_fill=(0, 0, 0))
        d.text((TW - 70, 470 + i * 92), line, font=fy, fill=(255, 214, 80), anchor="rt")
    # 金の数字(左下)
    gold_text(im, (60, 660), f"{a}-{b}", 120)
    # 左上のリボン
    rib = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    ImageDraw.Draw(rib).polygon([(0, 70), (70, 0), (130, 0), (0, 130)], fill=(220, 30, 30))
    im.paste(rib, (0, 0), rib)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, quality=92)
    return path


def duration(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                                capture_output=True, text=True, check=True).stdout.strip())


def stamp(t):
    t = int(t)
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60}:{t % 60:02d}"


def video(kind, a, b):
    """番号 a〜b の動画を順につなぐ(縦長のまま)。足りない番号は飛ばす。"""
    cfg = KINDS[kind]
    files = [(n, cfg["files"](n)) for n in range(a, b + 1) if cfg["files"](n).exists()]
    if not files:
        sys.exit("動画が見つかりません")
    work = OUT / f"_{kind}_{a}-{b}"
    work.mkdir(parents=True, exist_ok=True)
    parts, chapters, t = [], [], 0.0
    for n, f in files:  # 解像度・fps・音声をそろえてから、つなぐ
        out = work / f"{n}.mp4"
        if not out.exists():
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(f), "-vf",
                            "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "160k",
                            str(out)], check=True)
        chapters.append((t, n))
        t += duration(out)
        parts.append(out)
    lst = work / "list.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in parts))
    dst = OUT / f"{kind}_{a}-{b}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                    "-movflags", "+faststart", str(dst)], check=True)
    first, last = files[0][0], files[-1][0]
    thumbnail(kind, first, last, OUT / f"{kind}_{a}-{b}_thumb.jpg")
    title = cfg["title"].format(a=first, b=last)
    desc = (f"{title}\n\nショートで出したクイズを、番号順にまとめました。通しで聞き流しても、気になる回だけ見てもOKです。\n\n"
            "🔊 音声つきの復習・過去の問題はこちら(無料)\nhttps://eng-navi.github.io/\n\n"
            "▼ チャプター\n" + "\n".join(f"{stamp(ct)} {n}" for ct, n in chapters) + "\n\n#英語学習 #聞き流し #英検 #TOEIC")
    (OUT / f"{kind}_{a}-{b}.txt").write_text(f"タイトル:\n{title}\n\n説明欄:\n{desc}\n")
    missing = [n for n in range(a, b + 1) if not cfg["files"](n).exists()]
    print(f"✓ {dst}({stamp(t)}・{len(files)}本)" + (f" 見つからない番号: {missing[:20]}" if missing else ""))


if __name__ == "__main__":
    cmd, kind, a, b = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    if cmd == "thumb":
        print(thumbnail(kind, a, b, OUT / f"{kind}_{a}-{b}_thumb.jpg"))
    elif cmd == "video":
        video(kind, a, b)
