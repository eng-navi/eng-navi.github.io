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
KOKORO_SPEED = 0.95
# サイトで選べる声。us_f は従来どおり docs/audio/q<no>.mp3、ほかは docs/audio/<声>/q<no>.mp3
VOICES = {
    "us_f": ("a", "af_heart"),    # アメリカ英語・女性
    "us_m": ("a", "am_michael"),  # アメリカ英語・男性
    "uk_f": ("b", "bf_emma"),     # イギリス英語・女性
    "uk_m": ("b", "bm_george"),   # イギリス英語・男性
}


def audio_path(voice, no):
    return AUDIO / f"q{no}.mp3" if voice == "us_f" else AUDIO / voice / f"q{no}.mp3"
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
        self.pipes = {}

    def __call__(self, text, out, voice="us_f"):
        import numpy as np
        import soundfile as sf
        from kokoro import KPipeline
        lang, name = VOICES[voice]
        if lang not in self.pipes:
            self.pipes[lang] = KPipeline(lang_code=lang, repo_id="hexgrad/Kokoro-82M")
        out.parent.mkdir(parents=True, exist_ok=True)
        audio = np.concatenate([a for _, _, a in self.pipes[lang](text, voice=name, speed=KOKORO_SPEED)])
        with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
            sf.write(wav.name, audio, 24000)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav.name, "-b:a", "96k", str(out)], check=True)


class ElevenLabs:
    def __init__(self):
        self.key = os.environ.get("ELEVENLABS_API_KEY") or sys.exit(".env に ELEVENLABS_API_KEY を設定してください")
        self.voice = os.environ.get("ELEVENLABS_VOICE_ID", ELEVEN_VOICE)

    def __call__(self, text, out, voice="us_f"):
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
    quizzes = json.loads((ROOT / "quizzes.json").read_text())
    # ElevenLabs は1つの声だけ(us_f の位置に置く)
    voices = ["us_f"] if "--elevenlabs" in sys.argv else list(VOICES)
    todo = [(q, v) for q in quizzes for v in voices
            if (str(q["no"]) == only if only else not audio_path(v, q["no"]).exists())]
    if not todo:
        print("新しく作る音声はありません")
        return
    engine = ElevenLabs() if "--elevenlabs" in sys.argv else Kokoro()
    for q, v in todo:
        engine(sentence(q), audio_path(v, q["no"]), v)
    print(f"✓ 音声 {len(todo)} 件を作成")


if __name__ == "__main__":
    main()
