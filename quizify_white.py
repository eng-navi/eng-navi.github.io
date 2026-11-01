"""@quizify_english の白い「英単語(初級)」リールを作る。1本に2語(受験・英検で問われるやさしめのコロケーション)。

1語ごとに 英語 → 日本語の意味 → 日本語の例文 → (考える間) → 英語の例文(女性)→ 英語の例文(男性)の順。黒とほぼ同じで、
英語の例文を2回読むのが違い。間と配置は 2024年の元動画(159・161)の4語分を 0.01 秒単位で測った値の平均。

  .venv-tts/bin/python quizify_white.py      → out/quizify/white_<最初の番号>.mp4 と .txt(説明欄の全文)

作る前に quizify_words.json(白で使った単語)と照らし合わせ、同じ表現なら止まる。作った表現は「予定」として記録する。
"""
import subprocess
import tempfile

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw

import manga_reel as mr
import quizify_black as qb

ROOT, OUT, SR, W, H, FPS = qb.ROOT, qb.OUT, qb.SR, qb.W, qb.H, qb.FPS

# 声。英語1回目と日本語は黒と同じ(元動画も同じ声)。2回目は男性(元動画は約100Hz の低めの声)
EN_VOICE, EN_SPEED = qb.EN_VOICE, qb.EN_SPEED        # Lily(イギリス・女性)
EN2_VOICE = "onwK4e9ZLuTAKqWW03F9"                   # Daniel(イギリス・男性)
JA_VOICE, JA_SPEED = qb.JA_VOICE, qb.JA_SPEED        # Nanami(音読さんの「ななみ」)
# 音量(RMS)。元動画は英語 -14dB、日本語 -12dB 前後
LEVEL = {EN_VOICE: 0.18, EN2_VOICE: 0.18, JA_VOICE: 0.23}

# 間(秒)
LEAD = 0.55        # 動画の頭 → 英語
WORD_MEAN = 0.95   # 英語 → 意味
MEAN_JA = 0.81     # 意味 → 日本語の例文
JA_EN = 1.58       # 日本語の例文 → 英語の例文(考える間)
EN_EN = 1.03       # 英語の例文(女性)→ 英語の例文(男性)
EN_NEXT = 0.90     # 英語の例文(男性)→ 次の英語
TAIL = 0.36        # 最後の英語の例文 → 動画の終わり
SHOW_EARLY = 0.12  # 意味・日本語の例文の画面は声より少し先
EN_EARLY = 0.07    # 英語の例文の画面
NEXT_AFTER = 0.38  # 英語の例文(男性)が終わってから次の画面へ

BG = (241, 244, 241)
INK = (17, 19, 17)
NUM = qb.font("EBGaramond-Italic%5Bwght%5D.ttf", 60, [400])
TITLE = qb.font("MPLUSRounded1c-Bold.ttf", 48)
MEAN = qb.font("MPLUSRounded1c-Bold.ttf", 37)
JA = qb.font("MPLUSRounded1c-Bold.ttf", 32)
EN = qb.font("EBGaramond%5Bwght%5D.ttf", 48, [600])

ITEMS = [
    # 番号, 表現, 画面の意味, 読む意味, 日本語の例文, 英語の例文, 豆知識(説明欄に載せる)
    (163, "be involved in A", "〜に関わる、〜に参加する", "に関わる",
     "多くの学生がボランティア活動に関わっている。", "Many students are involved in volunteer work.",
     ["前置詞は in。「〜の中に入り込んでいる」イメージ", "get involved in A で「〜に関わるようになる」",
      "名詞は involvement(関与)"]),
    (164, "be related to A", "〜に関係がある", "に関係がある",
     "健康は睡眠と深く関係している。", "Health is closely related to sleep.",
     ["前置詞は to。with にしないよう注意", "closely(密接に)と一緒によく使います",
      "名詞は relation / relationship(関係)"]),
]


def frame(item, stage):
    """stage: word / mean / ja / en"""
    no, word, mean, _, ja, en = item[:6]
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((104, 176), str(no), font=NUM, fill=INK, anchor="ls")
    qb.spaced(d, (104, 447), "英単語（初級）", TITLE, INK, 0)
    if stage in ("word", "mean"):
        d.text((103, 620), word, font=EN, fill=INK, anchor="ls")
        if stage == "mean":
            qb.spaced(d, (107, 784), mean, MEAN, INK, 4)
        return im
    for i, line in enumerate(qb.wrap_ja(d, ja, JA, 460, 3)):
        qb.spaced(d, (103, 860 + i * 60), line, JA, INK, 3)
    if stage == "en":
        lines = qb.wrap(d, en, EN, 470)
        top = 658 - (len(lines) - 1) * 35
        for i, line in enumerate(lines):
            d.text((103, top + i * 70), line, font=EN, fill=INK, anchor="ls")
    return im


def build(items, out):
    qb.LEVEL.update(LEVEL)
    voice, cuts = [np.zeros(int(SR * LEAD), np.float32)], []  # cuts: (秒, item, stage)
    t, last_end = LEAD, 0.0
    for k, item in enumerate(items):
        _, word, _, said, ja, en = item[:6]
        parts = [(qb.tts(EN_VOICE, word, EN_SPEED), WORD_MEAN, "word"),
                 (qb.tts(JA_VOICE, said, JA_SPEED), MEAN_JA, "mean"),
                 (qb.tts(JA_VOICE, ja, JA_SPEED), JA_EN, "ja"),
                 (qb.tts(EN_VOICE, en, EN_SPEED), EN_EN, "en"),
                 (qb.tts(EN2_VOICE, en, EN_SPEED), TAIL if k == len(items) - 1 else EN_NEXT, None)]
        for clip, gap, stage in parts:
            if stage == "word":
                cuts.append((0.0 if k == 0 else last_end + NEXT_AFTER, item, stage))
            elif stage:
                cuts.append((t - (EN_EARLY if stage == "en" else SHOW_EARLY), item, stage))
            voice += [clip, np.zeros(int(SR * gap), np.float32)]
            t += len(clip) / SR
            if stage is None:
                last_end = t
            t += gap
    audio = np.concatenate(voice)
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
            cur = max((c for c in cuts if c[0] <= n / FPS), key=lambda c: c[0])
            key = (cur[1][0], cur[2])
            if key not in frames:
                frames = {key: frame(cur[1], cur[2]).tobytes()}
            p.stdin.write(frames[key])
        p.stdin.close()
        p.wait()
    print(f"✓ {out.relative_to(ROOT)}({total:.2f}秒)")
    for c in cuts:
        print(f"  {c[0]:6.2f}  {c[1][0]} {c[2]}")


def caption_text(items, intro, tags):
    """説明欄。黒と同じ形(【番号】表現:意味 → 英文 → 訳 → 💡 豆知識)。空行には全角スペース。紹介文とハッシュタグは毎回書き下ろす。"""
    sp = "　　"
    out = [intro, sp, "--------------------------------------"]
    for no, word, mean, _, ja, en, tips in items:
        out += [f"【{no}】{word}:{mean}", en, ja, sp, "💡 豆知識", *[f"・{t}" for t in tips], "--------------------------------------"]
    return "\n".join(out + [sp, "保存して、あとで復習してね📌", sp, tags])


if __name__ == "__main__":
    import quizify_words as qw
    qw.guard("white", [(it[0], it[1]) for it in ITEMS])  # 白で使った表現とかぶっていたら止める
    mr.load_env()
    out = OUT / f"white_{ITEMS[0][0]}.mp4"
    build(ITEMS, out)
    out.with_suffix(".txt").write_text(caption_text(
        ITEMS, "前置詞までセットで覚えよう✍️\n今日は「関わる」「関係がある」の2つです。", "#英単語 #英語学習 #大学受験") + "\n")
    for it in ITEMS:
        qw.add("white", it[1], no=it[0])
