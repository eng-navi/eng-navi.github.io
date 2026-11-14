"""リスニングクイズのショート動画(Ifverse 風の棒人間+3択)。英検2級〜準1級、10〜30秒。

    .venv-tts/bin/python quiz_short.py zeigarnik      # out/quiz_short/zeigarnik.mp4 と .txt(コメント欄用)

流れ:時計の 3・2・1 と問題 → 物語(ナレーション+字幕)→ 3択+3・2・1 → 答え。
台本は SHORTS に書くだけ。音声は ElevenLabs(保存して使い回す)、仕上げは Remotion(video3d/)。
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

import manga_reel as mr
import quizify_black as qb

ROOT = Path(__file__).parent
V3D = ROOT / "video3d"
PUB = V3D / "public" / "qs"
OUT = ROOT / "out" / "quiz_short"
VOICE, SPEED = "nPczCjzI2devNBz1zQrb", 1.0  # Brian(アメリカ英語・男性)。回ごとに変えてもよい
INTRO, GAP, CHOICE, ANSWER = 3.0, 0.35, 3.4, 2.6

SHORTS = {
    "zeigarnik": dict(
        q="Why can't Mia stop thinking about one task?", q_ja="ミアが1つの仕事を忘れられないのはなぜ?",
        choices=["Her boss called her about it.", "Unfinished tasks stay in our minds.", "She wrote it down."], answer=2,
        words=["unfinished", "psychologists", "effect"],
        scenes=[
            dict(bg="office", text="Mia finished nine tasks today.", people=[dict(x=380, y=1500, color="#2f6fd6", badge="9/10")]),
            dict(bg="bedroom", text="By night, she had forgotten all of them.", people=[dict(x=560, y=1160, color="#2f6fd6", pose="lie")]),
            dict(bg="bedroom", text="But the one unfinished task kept her up all night.", people=[dict(x=420, y=1500, color="#2f6fd6", pose="think")], think="1"),
            dict(bg="lab", text="Psychologists call this the Zeigarnik effect.", people=[dict(x=260, y=1560, color="#f2b33d", badge="DR.")]),
        ],
        ja=["ミアは今日、9つの仕事を終えた。", "夜には、そのすべてを忘れていた。", "でも、やり残した1つの仕事のせいで、一晩中眠れなかった。",
            "心理学者は、これを「ツァイガルニク効果」と呼ぶ。"],
        gloss=["unfinished:終わっていない", "keep A up:Aを眠らせない", "psychologist:心理学者", "effect:効果"],
        tags="#英語リスニング #英検準1級 #心理学"),
}


def tick_track(path):
    """3・2・1 のカチッという音"""
    sr = 44100
    t = np.arange(int(sr * 0.06)) / sr
    click = (0.25 * np.sin(2 * np.pi * 1400 * t) * np.exp(-t * 60)).astype(np.float32)
    out = np.zeros(int(sr * 3.0), np.float32)
    for s in (0.0, 1.0, 2.0):
        out[int(s * sr):int(s * sr) + len(click)] += click
    sf.write(path, out, sr)


def build(name):
    sc = SHORTS[name]
    mr.load_env()
    PUB.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    qb.LEVEL[VOICE] = 0.12
    tick_track(PUB / "tick.wav")
    bgm = PUB / "bgm.mp3"
    if not bgm.exists():
        bgm.write_bytes((ROOT / "assets" / "manga_bgm" / "cozy-places.mp3").read_bytes())
    t, scenes = INTRO, []
    for k, s in enumerate(sc["scenes"]):
        a = qb.tts(VOICE, s["text"], SPEED)
        f = f"{name}_{k}.wav"
        sf.write(PUB / f, a, qb.SR)
        dur = len(a) / qb.SR + GAP
        scenes.append({**s, "audio": f"qs/{f}", "start": round(t, 3), "dur": round(dur, 3)})
        t += dur
    props = dict(q=sc["q"], q_ja=sc["q_ja"], choices=sc["choices"], answer=sc["answer"], words=sc["words"], intro=INTRO,
                 scenes=scenes, choiceAt=round(t, 3), answerAt=round(t + CHOICE, 3), total=round(t + CHOICE + ANSWER, 3),
                 tick="qs/tick.wav", bgm="qs/bgm.mp3")
    pf = OUT / f"{name}.json"
    pf.write_text(json.dumps(props, ensure_ascii=False))
    out = OUT / f"{name}.mp4"
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "QuizShort", str(out), f"--props={pf}"], cwd=V3D, check=True,
                   stdout=subprocess.DEVNULL)
    # コメント欄に入れる文(英文と和訳を並べる。空行は全角スペース)
    sp = "　"
    lines = ["--------------------------------------", f"Q. {sc['q']}", f"({sc['q_ja']})", sp,
             f"答え:{'ABC'[sc['answer'] - 1]} {sc['choices'][sc['answer'] - 1]}", sp]
    for s, ja in zip(sc["scenes"], sc["ja"]):
        lines += [s["text"], ja, sp]
    lines += sc["gloss"] + ["--------------------------------------"]
    out.with_suffix(".txt").write_text("\n".join(lines) + "\n")
    print(f"✓ {out}({props['total']:.1f}秒)")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "zeigarnik")
