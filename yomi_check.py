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


# 漢字で書くと読み間違えやすく、しかも聞き取り側も漢字で書き戻すので ✗ にならない(すり抜ける)語。
# 台本(読ませる文)にこれが残っていたら ⚠ を出す → grammar_reel.py の YOMI でひらがなにする
RISKY = ["訳", "方", "何", "今日", "明日", "昨日", "一日", "上手", "下手", "辛", "生", "行った", "間"]
OK_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache", "yomi_ok.json")


def english_only(diffs):
    """ずれが「カタカナで書いた英単語 → 聞き取りは英字」だけなら OK(例:ライク → like)"""
    return diffs and all(re.fullmatch(r"[a-z ]+", b or "") and re.fullmatch(r"[ぁ-ゖー]+", a or "") for a, b in diffs)


def main(path):
    """--quiet:✓ は出さず、要確認だけ出す(トークン節約)。一度 ✓ になった音声は cache/yomi_ok.json に覚えて飛ばす"""
    quiet = "--quiet" in sys.argv
    ok_cache = set(json.load(open(OK_CACHE))) if os.path.exists(OK_CACHE) else set()
    items = [x for x in json.load(open(path)) if x["kind"] == "ja"]
    for x in items:
        hit = [w for w in RISKY if w in x["text"]]
        if hit:
            print(f"⚠ 読み間違えやすい漢字 {hit}:{x['text']}")
    todo = [x for x in items if x["mp3"] not in ok_cache]
    model = WhisperModel(os.environ.get("YOMI_MODEL", "large-v3-turbo"), device="cpu", compute_type="int8") if todo else None
    bad = 0
    for x in todo:
        segs, _ = model.transcribe(load(x["mp3"]), language="ja", beam_size=5)
        heard = "".join(s.text for s in segs)
        a, b = kana(x["text"]), kana(heard)
        r = difflib.SequenceMatcher(None, a, b).ratio()
        diffs = [(a[i1:i2], b[j1:j2]) for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes() if op != "equal"]
        ok = r >= 0.9 or english_only(diffs)
        bad += not ok
        if ok:
            ok_cache.add(x["mp3"])
        if not (quiet and ok):
            print(f"{'✓' if ok else '✗'} {r:.2f} 文:{x['text']}\n      聞:{heard}" + ("" if ok else f"\n      ずれ:{diffs}"))
    os.makedirs(os.path.dirname(OK_CACHE), exist_ok=True)
    json.dump(sorted(ok_cache), open(OK_CACHE, "w"))
    print(f"要確認 {bad} / {len(items)}(新しく調べた {len(todo)})")


if __name__ == "__main__":
    main(sys.argv[1])
