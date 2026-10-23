"""問題の英文(完成文)を読み上げた mp3 を docs/audio/ に作る(まだ無い分だけ)。

標準は Kokoro(このMacで動く無料の読み上げAI。声は af_heart)。専用の環境で動かす:
    .venv-tts/bin/python tts.py           # 音声が無い問題をすべて生成
    .venv-tts/bin/python tts.py 101       # 番号 101 だけ作り直す

ElevenLabs に切り替える場合は .env に ELEVENLABS_API_KEY を書いて --elevenlabs を付ける。
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
AUDIO = ROOT / "docs" / "audio"
KOKORO_VOICE = "af_heart"
KOKORO_SPEED = 0.95
ELEVEN_VOICE = "21m00Tcm4TlvDq8ikWAM"


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def sentence(q):
    if "options" not in q:
        return q["text"].replace("\n", " ")
    return re.sub(r"\(\s*\)", q["options"][q["answer"] - 1], q["question"])


class Kokoro:
    def __init__(self):
        from kokoro import KPipeline
        self.pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")

    def __call__(self, text, out):
        import numpy as np
        import soundfile as sf
        audio = np.concatenate([a for _, _, a in self.pipe(text, voice=KOKORO_VOICE, speed=KOKORO_SPEED)])
        with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
            sf.write(wav.name, audio, 24000)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav.name, "-b:a", "96k", str(out)], check=True)


class ElevenLabs:
    def __init__(self):
        self.key = os.environ.get("ELEVENLABS_API_KEY") or sys.exit(".env に ELEVENLABS_API_KEY を設定してください")
        self.voice = os.environ.get("ELEVENLABS_VOICE_ID", ELEVEN_VOICE)

    def __call__(self, text, out):
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice}?output_format=mp3_44100_128",
            data=json.dumps({"text": text, "model_id": "eleven_multilingual_v2"}).encode(),
            headers={"xi-api-key": self.key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
        )
        with urllib.request.urlopen(req) as res:
            out.write_bytes(res.read())


def main():
    load_env()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    only = args[0] if args else None
    AUDIO.mkdir(parents=True, exist_ok=True)
    todo = [q for q in json.loads((ROOT / "quizzes.json").read_text())
            if (str(q["no"]) == only if only else not (AUDIO / f"q{q['no']}.mp3").exists())]
    if not todo:
        print("新しく作る音声はありません")
        return
    engine = ElevenLabs() if "--elevenlabs" in sys.argv else Kokoro()
    for q in todo:
        engine(sentence(q), AUDIO / f"q{q['no']}.mp3")
        print(f"✓ q{q['no']}.mp3  {sentence(q)}")


if __name__ == "__main__":
    main()
