"""@quizify_english の青い「リスニング問題」リールを作る。1本に2問(短い1文=Part 2 風、会話・トーク=Part 3/4 風)。

1問ごとに カウントダウン(3・2・1)→ マイクの画面で英語を1回 → 日本語訳 A/B(片方はすり替えたひっかけ)。
答えは説明欄(キャプションの後半)に、元の投稿と同じ形で入れる(answer_text)。間と配置は 2024年の元動画(77・78 / 143・144)を 0.01 秒単位で測った値。

  .venv-tts/bin/python quizify_listening.py      → out/quizify/listening_<最初の番号>.mp4 と、説明欄の答え

カウントダウンの音は元動画(本人のアカウント)から切り出したもの(assets/quizify/countdown.wav)。
"""
import math
import subprocess
import tempfile

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter

import manga_reel as mr
import quizify_black as qb

OUT, SR, W, H, FPS = qb.OUT, qb.SR, qb.W, qb.H, qb.FPS
COUNTDOWN = qb.ROOT / "assets" / "quizify" / "countdown.wav"

# 声(ElevenLabs)。元動画は2本とも 1問目が男性(約107Hz)、2問目が女性(約219Hz)
SHORT_VOICE = "nPczCjzI2devNBz1zQrb"  # Brian(アメリカ・男性)
TALK_VOICE = "Xb7hH8MSUJpSbSDYk0k2"   # Alice(イギリス・女性)
SPEED = 1.0
qb.LEVEL[SHORT_VOICE] = qb.LEVEL[TALK_VOICE] = 0.2  # 元動画の声は -13dB 前後と大きめ

# 間(秒)
CD = 2.50          # カウントダウン → マイクの画面
VOICE_IN = (0.25, 0.16)  # マイクの画面 → 声(1問目・2問目)
OPT_AFTER = 0.30   # 声の終わり → 訳の画面
Q2_AT = 8.90       # 2問目のカウントダウンが始まる時刻(元動画は 8.83・9.00)
OPT_FADE = 0.30    # 2問目の訳はふわっと出る
PER_CHAR = 0.077   # 最後の訳を見せる長さ(長いほうの訳の1文字あたり)。最短 4 秒

LEFT, RIGHT = (186, 238, 219), (146, 188, 247)  # 横のグラデーション(左ミント → 右水色)
INK = (33, 33, 33)
NUM = qb.font("EBGaramond-Italic%5Bwght%5D.ttf", 54, [500])
TITLE = qb.font("KiwiMaru-Medium.ttf", 75)
OPT = qb.font("KiwiMaru-Medium.ttf", 26)
FOOT = qb.font("KiwiMaru-Medium.ttf", 31)
DIGIT = qb.font("OpenSans%5Bwdth,wght%5D.ttf", 58, [600, 100])

ITEMS = [
    # 番号, 声, 英文, 訳A, 訳B, 正解(A/B), 語句(説明欄に載せる「語句：意味」)
    (145, SHORT_VOICE, "When is the new branch scheduled to open?",
     "新しい支店はいつ開店予定ですか。", "新しい支店はどこに開店予定ですか。", "A",
     ["branch：支店", "be scheduled to do：…する予定である"]),
    (146, TALK_VOICE, "Kevin, do you have a minute? I'm updating the slides for Friday's client presentation. "
     "My manager asked me to add the latest sales figures. Could you send me the report from last quarter?",
     "ケビン、ちょっといい？金曜日の社内会議のスライドを作り直しているの。部長から、最新の売上目標を加えるように言われて。先月の報告書を送ってもらえる？",
     "ケビン、ちょっといい？金曜日の顧客向けプレゼンのスライドを更新しているの。上司から、最新の売上の数字を加えるように言われて。前の四半期の報告書を送ってもらえる？",
     "B",
     ["Do you have a minute?：ちょっといい？", "update：更新する", "client：顧客", "presentation：発表、プレゼン",
      "add A to B：BにAを加える", "sales figures：売上の数字", "quarter：四半期"]),
]


def background():
    x = np.linspace(0, 1, W)[None, :, None]
    row = np.array(LEFT)[None, None, :] * (1 - x) + np.array(RIGHT)[None, None, :] * x
    return Image.fromarray(np.repeat(row, H, axis=0).astype(np.uint8))


BG = background()
NO_BREAK_START = "、。?!)」ーぁぃぅぇぉっゃゅょァィゥェォッャュョ"


def wrap_chars(d, text, f, width, track):
    """1文字ずつ詰めて折り返す(元動画と同じ)。句読点や小さい字は行頭に来ないようにする。"""
    lines, cur = [], ""
    for ch in text:
        if cur and qb.spaced_width(d, cur + ch, f, track) > width and ch not in NO_BREAK_START:
            lines.append(cur)
            cur = ""
        cur += ch
    return lines + [cur] if cur else lines


def bold(d, xy, text, f, track):
    """字間をあけて、少し太く(1px ずらして重ねる)書く。"""
    for dx in (0, 0.7):
        qb.spaced(d, (xy[0] + dx, xy[1]), text, f, INK, track)


def mic(d, cx, cy):
    w = (255, 255, 255)
    d.ellipse([cx - 131, cy - 131, cx + 131, cy + 131], outline=w, width=7)
    d.rounded_rectangle([cx - 28, cy - 84, cx + 28, cy + 22], radius=28, outline=w, width=8)
    d.line([(cx - 28, cy - 22), (cx + 28, cy - 22)], fill=w, width=7)
    d.arc([cx - 58, cy - 44, cx + 58, cy + 56], 0, 180, fill=w, width=8)
    d.line([(cx, cy + 56), (cx, cy + 84)], fill=w, width=8)
    d.line([(cx - 38, cy + 86), (cx + 38, cy + 86)], fill=w, width=8)


def countdown(img, t):
    """白い円盤に 3・2・1。まわりの細い輪が回る。下に影。"""
    cx, cy = 190, 971
    n = 3 if t < 0.5 else 2 if t < 1.5 else 1
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse([cx - 52, cy - 46, cx + 52, cy + 58], fill=(20, 40, 50, 190))
    img.paste(shadow.filter(ImageFilter.GaussianBlur(5)), (0, 0), shadow.filter(ImageFilter.GaussianBlur(5)))
    d = ImageDraw.Draw(img)
    d.ellipse([cx - 50, cy - 50, cx + 50, cy + 50], fill=(246, 246, 246))
    d.arc([cx - 50, cy - 50, cx + 50, cy + 50], 15, 165, fill=(120, 130, 135), width=5)
    a = (t * 360) % 360
    d.arc([cx - 70, cy - 70, cx + 70, cy + 70], a, a + 300, fill=(255, 255, 255), width=3)
    d.text((cx, cy + 2), str(n), font=DIGIT, fill=INK, anchor="mm")


def frame(item, stage, t=0.0, fade=1.0):
    no, _, _, opt_a, opt_b = item[:5]
    img = BG.copy()
    d = ImageDraw.Draw(img)
    d.text((110, 176), str(no), font=NUM, fill=INK, anchor="ls")
    for dx in (0, 1):  # 元動画の文字は少し太いので、1px ずらして重ねる
        d.text((86 + dx, 450), "リスニング問題", font=TITLE, fill=INK, anchor="ls")
    foot_y = 988
    if stage == "count":
        countdown(img, t)
        return img
    if stage == "mic":
        mic(d, 360, 711)
    else:
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        a_lines = wrap_chars(ld, f"A) {opt_a}", OPT, 540, 2.5)
        b_lines = wrap_chars(ld, f"B) {opt_b}", OPT, 540, 2.5)
        y = 591 if len(a_lines) == 1 else 568
        for line in a_lines:
            bold(ld, (104, y), line, OPT, 2.5)
            y += 37.5
        y += 128 - 37.5 + 24
        for line in b_lines:
            bold(ld, (104, y), line, OPT, 2.5)
            y += 37.5
        foot_y = max(988, int(y - 37.5 + 131 + 33))
        if fade < 1:
            layer.putalpha(layer.getchannel("A").point(lambda v: int(v * fade)))
        img.paste(layer, (0, 0), layer)
    bold(d, (104, foot_y), "→ 答えは【説明・コメント欄】", FOOT, 5.0)
    return img


def build(items, out):
    cd, _ = sf.read(COUNTDOWN, dtype="float32")
    if cd.ndim > 1:
        cd = cd.mean(axis=1)
    scenes, track = [], np.zeros(int(SR * 60), np.float32)

    def put(a, t):
        i = int(t * SR)
        track[i:i + len(a)] += a[:len(track) - i]

    t = 0.0
    for k, item in enumerate(items):
        voice = qb.tts(item[1], item[2], SPEED)
        if k == 1:
            t = max(t, Q2_AT)
        put(cd, t)
        scenes.append((t, item, "count"))
        t += CD
        scenes.append((t, item, "mic"))
        t += VOICE_IN[k]
        put(voice, t)
        t += len(voice) / SR + OPT_AFTER
        scenes.append((t, item, "opt" if k == 0 else "opt_fade"))
        if k == 0:
            t += 2.9  # 2問目まで最低これだけ見せる
    end = scenes[-1][0] + max(4.0, PER_CHAR * max(len(items[-1][3]), len(items[-1][4])))
    track = track[:int(end * SR)]
    with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
        sf.write(wav.name, track, SR)
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-i", wav.name, "-map", "0:v", "-map", "1:a", "-t", f"{end:.2f}", "-c:v", "libx264",
                              "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)],
                             stdin=subprocess.PIPE)
        still = {}
        for i in range(int(round(end * FPS))):
            now = i / FPS
            start, item, stage = [s for s in scenes if s[0] <= now + 1e-6][-1]
            if stage == "count":
                img = frame(item, "count", now - start)
            elif stage == "opt_fade" and now - start < OPT_FADE:
                img = frame(item, "opt", fade=(now - start) / OPT_FADE)
            else:
                key = (item[0], stage)
                if key not in still:
                    still[key] = frame(item, "opt" if stage.startswith("opt") else stage)
                img = still[key]
            p.stdin.write(img.tobytes())
        p.stdin.close()
        p.wait()
    print(f"✓ {out}({end:.2f}秒)")
    for start, item, stage in scenes:
        print(f"  {start:6.2f}  {item[0]} {stage}")


def answer_text(items):
    """説明欄(キャプション)の後半に入れる答え。元の投稿と同じ形。空行には全角スペースを入れる(Instagram が空行を詰めるため)。"""
    sp = "\u3000\u3000"
    out = [sp, "--------------------------------------"]
    for no, _, en, a, b, ans, words in items:
        out += [f"【{no}】", en, a if ans == "A" else b, sp, *words, sp, f" {sp}", f"{ans}が正解。",
                "--------------------------------------"]
    return "\n".join(out)


if __name__ == "__main__":
    mr.load_env()
    build(ITEMS, OUT / f"listening_{ITEMS[0][0]}.mp4")
    print(answer_text(ITEMS))
