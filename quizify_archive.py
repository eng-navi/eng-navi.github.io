"""過去の @quizify_english(2023〜2024年)の投稿を、復習ページ用のデータ(quizify_archive.json)にする。毎日少しずつ。

    .venv-tts/bin/python quizify_archive.py 5 8 6     # リスニング5本・黒8本・白6本ぶん、まだのものを古い順に取り込む

・リスニング:説明欄に英文・訳・語句・答えがあるので、それを使う。A/B の訳は画面の文字(OCR)。音声は元の動画から切り出す
・黒・白:画面の文字(OCR)から、単語・意味・日本語の例文・英語の例文を拾う。音声は英語の例文の部分を切り出す
取り込んだ単語は quizify_words.json にも足す(表紙には1語目しか出ていないため、2語目・3語目もかぶりチェックに入れる)
"""
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent
SCAN = ROOT / "out" / "quizify" / "scan"
VID = SCAN / "videos"
OUT = ROOT / "quizify_archive.json"
AUDIO = ROOT / "docs" / "quizify" / "audio" / "archive"
SR = 16000


def media_url(mid):
    import manga_reel as mr
    mr.load_env()
    tok = os.environ["QUIZIFY_IG_ACCESS_TOKEN"]
    return json.load(urllib.request.urlopen(f"https://graph.instagram.com/v21.0/{mid}?fields=media_url&access_token={tok}"))["media_url"]


def video(mid):
    VID.mkdir(parents=True, exist_ok=True)
    p = VID / f"{mid}.mp4"
    if not p.exists():
        urllib.request.urlretrieve(media_url(mid), p)
    return p


def pcm(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def segments(a):
    """声のかたまり(秒)。-45dB 以上、0.15秒未満のすき間はつなぐ、0.05秒未満は捨てる。"""
    n = len(a) // 160
    db = 20 * np.log10(np.sqrt((a[:n * 160].reshape(n, 160) ** 2).mean(1)) + 1e-9)
    segs, s = [], None
    for i, on in enumerate(db > -45):
        if on and s is None:
            s = i
        if not on and s is not None:
            segs.append([s, i])
            s = None
    if s is not None:
        segs.append([s, n])
    merged = []
    for x in segs:
        if merged and x[0] - merged[-1][1] < 15:
            merged[-1][1] = x[1]
        else:
            merged.append(x)
    return [(a0 / 100, b0 / 100) for a0, b0 in merged if b0 - a0 >= 5]


def clip(src, start, end, name):
    AUDIO.mkdir(parents=True, exist_ok=True)
    dst = AUDIO / f"{name}.mp3"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, start - 0.05):.2f}", "-to", f"{end + 0.1:.2f}", "-i", str(src),
                    "-vn", "-ac", "1", "-b:a", "64k", str(dst)], check=True)
    return f"audio/archive/{dst.name}"


def ocr_at(p, t):
    from ocrmac import ocrmac
    img = SCAN / "frame.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(p), "-frames:v", "1", str(img)], check=True)
    return [(r[0].strip(), r[2]) for r in ocrmac.OCR(str(img), language_preference=["ja-JP", "en-US"]).recognize()]


def listening(x, cap):
    """説明欄の答えの部分を2問に分ける。A/B は画面から読む。"""
    blocks = [b for b in re.split(r"-{10,}", cap) if "【" in b and "正解" in b]
    p = video(x["id"])
    segs = segments(pcm(p))
    out = []
    for k, b in enumerate(blocks[:2]):
        lines = [l.strip() for l in b.split("\n") if l.strip() and l.strip() not in ("　", "\t")]
        no = int(re.search(r"【(\d+)】", lines[0]).group(1))
        en, ja = lines[1], lines[2]
        words = [l for l in lines[3:] if "：" in l]
        ans = re.search(r"\(?([AB])\)?\s*が正解", b).group(1)
        out.append(dict(no=no, en=en, ja=ja, words=words, ans=ans))
    # 声:カウントダウンのあとの英語。1問目=最初の長めのかたまり、2問目=後半のかたまりをまとめる
    voice = [s for s in segs if s[0] > 2.6]
    if len(out) == 2 and voice:
        q2_start = next((s for s in voice if s[0] > 8.5), None)
        q1 = [s for s in voice if q2_start is None or s[0] < q2_start[0]]
        q2 = [s for s in voice if q2_start and s[0] >= q2_start[0]]
        # 2問目の最後の小さい音(「Thank you for watching」など)は、長さで判断せず訳の画面より前までにする
        for item, ss in ((out[0], q1), (out[1], q2)):
            if ss:
                item["audio"] = clip(p, ss[0][0], ss[-1][1] if item is out[0] else min(ss[-1][1], ss[0][0] + 14), f"L{item['no']}")
        # A/B の訳(1問目は 1問目の声の直後、2問目は動画の最後のほう)
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                   capture_output=True, text=True).stdout)
        for item, base in ((out[0], (q1[-1][1] + 0.6) if q1 else 6.0), (out[1], dur - 2.5)):
            for dt in (0.6, 1.4, 2.2, 3.0):  # 訳が出るまで少しずつ後ろを見る
                item["a"], item["b"] = ab(ocr_at(p, min(base + dt, dur - 0.1)))
                if item["a"] and item["b"]:
                    break
    return out


def ab(lines):
    """画面の文字から A) … と B) … を取り出す(複数行をつなぐ)。"""
    lines = sorted(lines, key=lambda r: -r[1][1])  # 上から順
    a, b, cur = [], [], None
    for text, _ in lines:
        if "答え" in text or "リスニング" in text or re.fullmatch(r"\d+", text):
            continue
        m_ = re.match(r"^[\(（]?([AB])\s*[\)）]\s*(.*)", text)
        if m_:
            cur = a if m_.group(1) == "A" else b
            cur.append(m_.group(2))
        elif cur is not None:
            cur.append(text)
    return "".join(a), "".join(b)


def words_reel(x, kind):
    """黒・白:1秒ごとに画面を読み、場面ごとに文字をまとめる。声のかたまりから英語の例文の音声を切り出す。"""
    p = video(x["id"])
    a = pcm(p)
    dur = len(a) / SR
    frames = []
    t = 0.3
    while t < dur - 0.2:
        texts = [r[0] for r in sorted(ocr_at(p, t), key=lambda r: -r[1][1])]
        frames.append((t, [s for s in texts if "瞬間英作文" not in s and "英単語" not in s and "クイズ" not in s and "TOEIC" not in s]))
        t += 0.7
    return dict(frames=frames, segs=segments(a))


JA_RE = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")


def parse_words(raw, link, date):
    """画面の文字の並びから、1語ずつ {word, mean, ja, en, word_t, en_t} にする。"""
    items, cur = [], None
    for t, lines in raw["frames"]:
        lines = [l for l in lines if not re.fullmatch(r"[\d\s日目=]+|\d+\s*[日目=].*", l)]
        en = " ".join(l for l in lines if not JA_RE.search(l)).strip()
        ja = "".join(l for l in lines if JA_RE.search(l)).strip()
        key = lambda x: re.sub(r"[^a-z]", "", (x or "").lower())
        if en and not ja:
            if cur is None or (key(en) != key(cur["word"]) and not cur.get("en") and len(en.split()) <= 5 and not key(cur["word"]) in key(en)) or (cur.get("en") and key(en) not in key(cur["en"])):
                cur = dict(word=en, word_t=t)
                items.append(cur)
        elif en and ja:
            if cur and key(en) == key(cur["word"]):
                cur["mean"] = ja
            elif cur and len(en.split()) >= 3:
                cur.setdefault("en", en)
                cur.setdefault("en_t", t)
                if not cur.get("ja"):
                    cur["ja"] = ja
        elif ja and cur:
            if not cur.get("mean"):
                cur["mean"] = ja
            elif not cur.get("en"):
                cur["ja"] = ja
    for it in items:
        it["mean"] = re.sub(r"^[〔［\[].{1,3}[］\]〕]\s*", "", it.get("mean", ""))
    return items


def finish_words(data):
    """取り込み済みの黒・白に、整理した項目と音声をつける(まだのものだけ)。"""
    for kind in ("black", "white"):
        for mid, v in data[kind].items():
            if "items" in v:
                continue
            items = parse_words(v["raw"], v["link"], v["date"])
            p = VID / f"{mid}.mp4"
            segs = v["raw"]["segs"]
            for k, it in enumerate(items):
                ws = next((s for s in segs if s[0] >= it["word_t"] - 1.0), None)
                if ws:
                    it["word_audio"] = clip(p, ws[0], ws[1], f"{kind[0]}{mid}_{k}w")
                if it.get("en_t"):
                    es = next((s for s in segs if s[0] >= it["en_t"] - 0.6), None)
                    if es:
                        it["en_audio"] = clip(p, es[0], es[1], f"{kind[0]}{mid}_{k}e")
            v["items"] = items
            import quizify_words as qw
            for it in items:  # 2語目以降も、かぶりチェックの記録に入れる
                qw.add(kind, it["word"], status="投稿済み", source="過去の投稿")


def main():
    n_l, n_b, n_w = (int(v) for v in sys.argv[1:4])
    ocr = json.loads((SCAN / "ocr.json").read_text())
    media = {m_["id"]: m_ for m_ in json.loads((SCAN / "media.json").read_text())}
    data = json.loads(OUT.read_text()) if OUT.exists() else {"listening": {}, "black": {}, "white": {}}
    for kind, n in (("listening", n_l), ("black", n_b), ("white", n_w)):
        # 白は表紙に表現が読めたものだけ(本の紹介動画などを除く)
        pool = [x for x in ocr if x["kind"] == kind and (kind != "white" or x.get("word"))]
        todo = [x for x in sorted(pool, key=lambda x: x["date"]) if x["id"] not in data[kind]][:n]
        for x in todo:
            try:
                if kind == "listening":
                    data[kind][x["id"]] = dict(date=x["date"], link=x["permalink"], items=listening(x, media[x["id"]].get("caption") or ""))
                else:
                    data[kind][x["id"]] = dict(date=x["date"], link=x["permalink"], raw=words_reel(x, kind))
                print(f"✓ {kind} {x['date']} {x.get('word') or ''}")
            except Exception as e:
                print(f"× {kind} {x['date']} {e}")
            OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    finish_words(data)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    print({k: len(v) for k, v in data.items()})


if __name__ == "__main__":
    main()
