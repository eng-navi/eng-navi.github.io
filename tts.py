"""ElevenLabs で各問題の完成文を読み上げた mp3 を作る(まだ無い分だけ)。

準備: .env に以下を書く
    ELEVENLABS_API_KEY=xxxxxxxx
    ELEVENLABS_VOICE_ID=xxxxxxxx   # 省略時は下の DEFAULT_VOICE

使い方:
    python3 tts.py           # 音声が無い問題をすべて生成
    python3 tts.py 101       # 番号 101 だけ作り直す
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
AUDIO = ROOT / "docs" / "audio"
DEFAULT_VOICE = "21m00Tcm4TlvDq8ikWAM"  # Rachel(米国英語・落ち着いた女性)
MODEL = "eleven_multilingual_v2"


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def completed(q):
    return re.sub(r"\(\s*\)", q["options"][q["answer"] - 1], q["question"])


def synthesize(text, out, key, voice):
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128",
        data=json.dumps({"text": text, "model_id": MODEL}).encode(),
        headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
    )
    with urllib.request.urlopen(req) as res:
        out.write_bytes(res.read())


def main():
    load_env()
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit(".env に ELEVENLABS_API_KEY を設定してください")
    voice = os.environ.get("ELEVENLABS_VOICE_ID", DEFAULT_VOICE)

    AUDIO.mkdir(parents=True, exist_ok=True)
    quizzes = json.loads((ROOT / "quizzes.json").read_text())
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for q in quizzes:
        out = AUDIO / f"q{q['no']}.mp3"
        if only and str(q["no"]) != only:
            continue
        if out.exists() and not only:
            continue
        synthesize(completed(q), out, key, voice)
        print(f"✓ {out.name}  {completed(q)}")


if __name__ == "__main__":
    main()
