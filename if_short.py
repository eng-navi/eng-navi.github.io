"""Ifverse 風のリスニングクイズ・ショート(英検2級〜準1級・10〜30秒)。参考動画の見せ方をまねた型。

    .venv-tts/bin/python if_short.py compound      # out/if_short/compound.mp4 と .txt(コメント欄用)

参考動画がリッチに見える理由と、この型での対応:
  ・2〜3秒ごとにカット(1行=1カット)         → SHORTS の shots に1行ずつ書く
  ・構図が毎回ちがう(顔・目・全身・2人・物・遠景) → type を face / eyes / full / two / insert / wide から選ぶ
  ・表情がころころ変わる                        → eyes(8種類)と mouth(6種類)
  ・字幕は1〜3語ずつ、大事な語は黄色             → ElevenLabs の単語ごとのタイミングで自動
  ・効果音(カットごとのシュッ、数字のポン、衝撃) → 自動で入れる
  ・数字が増えていく表示                         → hud
流れ:時計の 3・2・1 と問題 → 物語 → 2択+4・3・2・1 →「正解はコメント欄で」
"""
import base64
import hashlib
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf

import manga_reel as mr

ROOT = Path(__file__).parent
V3D = ROOT / "video3d"
PUB = V3D / "public" / "if"
OUT = ROOT / "out" / "if_short"
CACHE = ROOT / "out" / "voice_cache"
SR = 44100
INTRO, CHOICE, END = 3.0, 4.2, 2.4

SHORTS = {
    "compound": dict(
        voice="nPczCjzI2devNBz1zQrb",  # Brian
        q="Why does Sam's money grow so fast?", q_ja="サムのお金が、どんどん増えるのはなぜ?",
        choices=["He won the lottery.", "His interest earns interest."], answer=2,
        hl=["doubled", "interest", "compound", "nobody", "laughing"],
        shots=[
            ("What if your money doubled every day?", dict(type="face", bg="room", eyes="shock", mouth="o", hud="DAY 1 · $1")),
            ("Sam starts with one dollar.", dict(type="insert", bg="dark", insert="coin", value="$1")),
            ("Day five. Sixteen dollars.", dict(type="full", bg="room", eyes="smug", mouth="smile", hud="DAY 5 · $16")),
            ("His friends laugh at him.", dict(type="two", bg="street", eyes="worried", mouth="wavy", eyes2="squint", mouth2="grin")),
            ("Day fifteen.", dict(type="wide", bg="street", eyes="normal", mouth="flat", hud="DAY 15 · $16,384", cam="pan")),
            ("Sixteen thousand dollars!", dict(type="eyes", bg="dark", eyes="shock", cam="shake")),
            ("Day twenty-one. Over a million.", dict(type="insert", bg="bank", insert="phone", value="$1,048,576", hud="DAY 21")),
            ("Now nobody is laughing.", dict(type="two", bg="bank", eyes="glasses", mouth="grin", eyes2="shock", mouth2="o")),
            ("The secret? Interest that earns interest.", dict(type="insert", bg="bank", insert="chart", value="INTEREST × INTEREST")),
            ("It's called compound interest.", dict(type="face", bg="bank", eyes="glasses", mouth="grin", cam="pull")),
        ],
        ja=["もしお金が毎日2倍になったら?", "サムは1ドルから始める。", "5日目、16ドル。", "友だちは彼を笑う。", "15日目。",
            "1万6千ドル!", "21日目、100万ドル超え。", "もう誰も笑っていない。", "秘密は?利子が利子を生むこと。", "それは「複利」と呼ばれる。"],
        gloss=["double:2倍になる", "laugh at A:Aを笑う", "nobody:誰も〜ない", "interest:利子、利息", "earn:(お金を)生む、稼ぐ", "compound interest:複利"],
        tags="#英語リスニング #英検準1級 #お金の勉強"),
}


def tts_words(voice, text):
    """ElevenLabs で読み上げ、音声と単語ごとの時刻を返す(保存して使い回す)"""
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(f"ts|{voice}|{text}".encode()).hexdigest()[:14]
    js, mp3 = CACHE / f"ts_{key}.json", CACHE / f"ts_{key}.mp3"
    if not js.exists():
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128",
            data=json.dumps({"text": text, "model_id": "eleven_multilingual_v2",
                             "voice_settings": {"stability": 0.45, "similarity_boost": 0.75, "speed": 1.0}}).encode(),
            headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"})
        d = json.load(urllib.request.urlopen(req))
        mp3.write_bytes(base64.b64decode(d["audio_base64"]))
        js.write_text(json.dumps(d["alignment"]))
    al = json.loads(js.read_text())
    words, cur, st = [], "", None
    for ch, s, e in zip(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]):
        if ch == " ":
            if cur:
                words.append([cur, st, last])
            cur, st = "", None
            continue
        if st is None:
            st = s
        cur, last = cur + ch, e
    if cur:
        words.append([cur, st, last])
    return mp3, words


def synth(kind, dur):
    t = np.arange(int(SR * dur)) / SR
    if kind == "whoosh":  # 帯域を動かしたノイズ
        n = np.random.default_rng(1).standard_normal(len(t))
        env = np.sin(np.pi * t / dur) ** 2
        k = np.convolve(n, np.ones(30) / 30, "same")
        return (0.18 * k * env).astype(np.float32)
    if kind == "pop":
        return (0.28 * np.sin(2 * np.pi * (500 + 900 * t / dur) * t) * np.exp(-t * 25)).astype(np.float32)
    if kind == "boom":
        return (0.5 * np.sin(2 * np.pi * (90 - 40 * t) * t) * np.exp(-t * 6)).astype(np.float32)
    if kind == "tick":
        return (0.25 * np.sin(2 * np.pi * 1400 * t) * np.exp(-t * 60)).astype(np.float32)
    return np.zeros(len(t), np.float32)


def build(name):
    sc = SHORTS[name]
    mr.load_env()
    PUB.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    lines = [ln for ln, _ in sc["shots"]]
    mp3, words = tts_words(sc["voice"], " ".join(lines))
    story = PUB / f"{name}_story.mp3"
    story.write_bytes(mp3.read_bytes())
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(story)],
                               capture_output=True, text=True).stdout)
    # 1行=1カット:その行の最初の単語の時刻で切り替える
    shots, wi = [], 0
    for k, (ln, spec) in enumerate(sc["shots"]):
        start = words[wi][1]
        wi += len(ln.split())
        shots.append({**spec, "start": INTRO + (0 if k == 0 else start - 0.08)})
    for k, s in enumerate(shots):
        end = shots[k + 1]["start"] if k + 1 < len(shots) else INTRO + dur + 0.3
        s["dur"] = round(end - s["start"], 3)
        s["start"] = round(s["start"], 3)
    choice_at = INTRO + dur + 0.3
    total = choice_at + CHOICE + END
    hl = [h.lower() for h in sc["hl"]]
    wlist = [dict(text=w, start=round(s, 3), end=round(e, 3),
                  hl=any("".join(c for c in w.lower() if c.isalpha()).startswith(h[:5]) for h in hl)) for w, s, e in words]
    # 効果音:カットごとにシュッ、数字が出たらポン、目のアップはドン
    sfx = np.zeros(int(SR * (total + 1)), np.float32)

    def put(a, t):
        i = int(t * SR)
        sfx[i:i + len(a)] += a[:len(sfx) - i]
    for s in shots:
        put(synth("whoosh", 0.35), max(0, s["start"] - 0.12))
        if s.get("hud"):
            put(synth("pop", 0.15), s["start"] + 0.1)
        if s["type"] == "eyes":
            put(synth("boom", 0.6), s["start"])
    for k in range(3):
        put(synth("tick", 0.06), k * 1.0)
    for k in range(4):
        put(synth("tick", 0.06), choice_at + k * 1.0)
    sf.write(PUB / f"{name}_sfx.wav", sfx, SR)
    bgm = PUB / "bgm.mp3"
    if not bgm.exists():
        src = ROOT / "docs" / "bgm" / "the-waves.mp3"
        bgm.write_bytes((src if src.exists() else ROOT / "assets" / "manga_bgm" / "cozy-places.mp3").read_bytes())
    tick = PUB / "tick.wav"
    sf.write(tick, np.zeros(int(SR * 0.1), np.float32), SR)  # 時計の音は sfx に入れたので無音
    props = dict(q=sc["q"], q_ja=sc["q_ja"], choices=sc["choices"], answer=sc["answer"], words=wlist, intro=INTRO,
                 scenes=[], shots=shots, choiceAt=round(choice_at, 3), answerAt=round(choice_at + CHOICE, 3), total=round(total, 3),
                 story=f"if/{story.name}", sfx=f"if/{name}_sfx.wav", tick="if/tick.wav", bgm="if/bgm.mp3")
    pf = OUT / f"{name}.json"
    pf.write_text(json.dumps(props, ensure_ascii=False))
    out = OUT / f"{name}.mp4"
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "IfShort", str(out), f"--props={pf}"], cwd=V3D, check=True,
                   stdout=subprocess.DEVNULL)
    sp = "　"
    txt = ["--------------------------------------", f"Q. {sc['q']}", f"({sc['q_ja']})", sp,
           f"答え:{'AB'[sc['answer'] - 1]} {sc['choices'][sc['answer'] - 1]}", sp]
    for ln, ja in zip(lines, sc["ja"]):
        txt += [ln, ja, sp]
    txt += sc["gloss"] + ["--------------------------------------"]
    out.with_suffix(".txt").write_text("\n".join(txt) + "\n")
    print(f"✓ {out}({total:.1f}秒・{len(shots)}カット)")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "compound")
