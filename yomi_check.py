"""ナレーションの読みチェック。音声を Whisper で聞き取り、読ませたい文とひらがなで比べる。

    .venv-tts/bin/python yomi_check.py out/grammar/grammar_1.voice.json
ずれがあれば ✗ を出す → grammar_reel.py の YOMI にひらがなを足して作り直し、もう一度チェック。
"""
import difflib
import json
import os
import re
import sys

import subprocess

import numpy as np
import pykakasi
from faster_whisper import WhisperModel

kks = pykakasi.kakasi()


def kana(s):
    s = "".join(x["hira"] for x in kks.convert(s))
    return re.sub(r"[^ぁ-ゖー0-9a-z]", "", s.lower())


def load(mp3):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", mp3, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32)


def main(path):
    model = WhisperModel(os.environ.get("YOMI_MODEL", "large-v3-turbo"), device="cpu", compute_type="int8")
    items = [x for x in json.load(open(path)) if x["kind"] == "ja"]
    bad = 0
    for x in items:
        segs, _ = model.transcribe(load(x["mp3"]), language="ja", beam_size=5)
        heard = "".join(s.text for s in segs)
        a, b = kana(x["text"]), kana(heard)
        r = difflib.SequenceMatcher(None, a, b).ratio()
        diffs = [(a[i1:i2], b[j1:j2]) for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes() if op != "equal"]
        ok = r >= 0.9
        bad += not ok
        print(f"{'✓' if ok else '✗'} {r:.2f} 文:{x['text']}\n      聞:{heard}" + ("" if ok else f"\n      ずれ:{diffs}"))
    print(f"\n要確認 {bad} / {len(items)}")


if __name__ == "__main__":
    main(sys.argv[1])
