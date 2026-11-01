"""@quizify_english で使った英単語の記録(黒・白それぞれ)。同じ色の中で単語がかぶらないようにする。

記録は quizify_words.json。黒(瞬間英作文クイズ・旧 TOEIC頻出英単語クイズ)と白(英単語(初級))は別々に数え、
黒と白で同じ単語はかまわない。本が変わっても単語そのもので照合するので、別の本から同じ単語を出すのを防げる。

    python3 quizify_words.py check black scrutinize plausible   # 使ったことがあるか(かぶりは × と表示)
    python3 quizify_words.py list white                          # 白で使った単語の一覧
    .venv-tts/bin/python quizify_words.py scan                   # 過去の投稿の表紙を読み直して記録を作り直す(Mac の OCR)

・照合は小文字にして、A・B・SV・do・Ving・〜 などの記号を除いた形で行う(be about to do = be about to)
・表現全体が同じなら×。中心の単語が同じもの(deadline と meet the deadline)は注意(△)。白はできれば避けるが、試験で問う意義がある別の表現なら出してよい
・つづりの前半7文字が同じもの(deteriorate / deterioration など)は「似ている」として注意を出す
・作成スクリプト(quizify_black.py など)は作る前に check し、作った単語を「予定」として記録する。投稿したら「投稿済み」になる
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
FILE = ROOT / "quizify_words.json"
KINDS = ("black", "white")
PLACEHOLDERS = {"a", "b", "sv", "v", "do", "ving", "pp", "人", "+人+v", "~", "〜", "one's", "oneself"}
# 表紙の OCR の読み間違いを直す
OCR_FIX = {"Why don'twe ~": "Why don't we ~", "cannot help （Ving": "cannot help Ving", "Intoxicated": "intoxicated",
           "Cross out": "cross out", "untamiliar": "unfamiliar", "upP to A": "up to A", "issule": "issue",
           "be ashamed ofA": "be ashamed of A"}


def key(word):
    """照合用の形(小文字、記号やプレースホルダーを除く)。"""
    w = word.lower().replace("’", "'").replace("（", " ").replace("）", " ").replace("+", " ")
    parts = [p for p in re.split(r"[\s/,.]+", w) if p and p not in PLACEHOLDERS]
    return " ".join(parts)


def load():
    return json.loads(FILE.read_text()) if FILE.exists() else {k: [] for k in KINDS}


def save(data):
    for k in KINDS:
        data[k].sort(key=lambda x: (x.get("date") or "9999", x.get("no") or 0))
    FILE.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")


# 中心の単語を取り出すときに無視する語(前置詞・冠詞・be など)
FUNCTION = {"be", "a", "an", "the", "to", "of", "with", "for", "in", "on", "at", "about", "from", "into", "as",
            "up", "out", "down", "off", "by", "it", "one", "some", "someone", "something",
            # 基本動詞(make out と make an effort のように、中心は別の語になることが多い)
            "make", "take", "get", "have", "give", "go", "come", "look", "turn", "fill", "put", "keep", "do"}


def core(k):
    """照合用の形から、中心の単語(前置詞などを除いた語)の集合を取り出す。"""
    return {t for t in k.split() if t not in FUNCTION}


def check(kind, words, ignore_no=None):
    """かぶり(同じ単語)と、似ている単語を返す。ignore_no はその番号の自分の予定を無視する(作り直し用)。
    表現全体が同じなら×(止める)。中心の単語が同じもの(deadline と meet the deadline など)は「似ている」として注意を出す。
    白はできれば避けるが、英検・大学受験で問う意義がある別の表現なら出してよい(本人の希望)。"""
    used = [e for e in load()[kind] if not (ignore_no is not None and e.get("no") == ignore_no and e["status"] == "予定")]
    same, similar = [], []
    for w in words:
        k = key(w)
        for e in used:
            ek = key(e["word"])
            if ek == k:
                same.append((w, e))
            elif core(k) & core(ek):
                similar.append((w, e))
            elif len(k) >= 7 and len(ek) >= 7 and " " not in k and k[:7] == ek[:7]:
                similar.append((w, e))
    return same, similar


def add(kind, word, no=None, status="予定", source=None):
    data = load()
    for e in data[kind]:
        if key(e["word"]) == key(word):
            if e["status"] == "予定" and status == "投稿済み":
                e["status"] = status
                save(data)
            return
    data[kind].append(dict(word=word, no=no, status=status, date=date.today().isoformat(), source=source))
    save(data)


def guard(kind, items):
    """作成スクリプト用:items = [(番号, 単語)]。かぶりがあれば止め、似ている単語は注意を出す。"""
    stop = False
    for no, w in items:
        same, similar = check(kind, [w], ignore_no=no)
        for _, e in same:
            print(f"× {w}:{kind} で使用済み({e['status']} {e.get('no')}番 {e.get('date')})")
            stop = True
        for _, e in similar:
            print(f"△ {w}:似ている単語 {e['word']}({e['status']} {e.get('no')}番)")
    if stop:
        sys.exit("かぶっている単語を差し替えてから作り直してください(quizify_words.py check で確認できます)")


def scan():
    """過去の投稿の表紙を API で取り、Mac の OCR で黒・白と単語を読み取って、記録を作り直す(予定の分は残す)。"""
    import os
    import urllib.request
    from ocrmac import ocrmac
    sys.path.insert(0, str(ROOT))
    import manga_reel as mr
    mr.load_env()
    tok = os.environ["QUIZIFY_IG_ACCESS_TOKEN"]
    url = ("https://graph.instagram.com/v21.0/me/media?fields=id,media_type,thumbnail_url,permalink,timestamp"
           f"&limit=100&access_token={tok}")
    media = []
    while url:
        d = json.load(urllib.request.urlopen(url))
        media += d["data"]
        url = d.get("paging", {}).get("next")
    thumbs = ROOT / "out" / "quizify" / "scan" / "thumbs"
    thumbs.mkdir(parents=True, exist_ok=True)
    data = load()
    new = {k: [e for e in data[k] if e["status"] == "予定"] for k in KINDS}
    for x in media:
        if x["media_type"] != "VIDEO" or not x.get("thumbnail_url"):
            continue
        p = thumbs / f"{x['id']}.jpg"
        if not p.exists():
            urllib.request.urlretrieve(x["thumbnail_url"], p)
        lines = [r[0].strip() for r in ocrmac.OCR(str(p), language_preference=["ja-JP", "en-US"]).recognize()]
        text = " ".join(lines)
        if "瞬間英作文" in text or "英単語クイズ" in text:
            kind, label = "black", ("瞬間英作文" if "瞬間英作文" in text else "英単語クイズ")
        elif "英単語（初級）" in text or "英単語(初級)" in text:
            kind, label = "white", "初級"
        else:
            continue  # リスニング・空欄クイズ・本の紹介
        i = next(i for i, l in enumerate(lines) if label in l)
        word = " ".join(l for l in lines[i + 1:] if re.search("[A-Za-z]", l) and "クイズ" not in l).strip()
        if not word:
            continue
        word = OCR_FIX.get(word, word)
        m = re.search(r"(\d+)", " ".join(lines[:i]))
        no = int(m.group(1)) if m else None
        if no and no > 300 and kind == "black":  # 「145日目」が「1458 目」と読まれることがある
            no //= 10
        if any(key(e["word"]) == key(word) for e in new[kind]):
            continue
        new[kind].append(dict(word=word, no=no, status="投稿済み", date=x["timestamp"][:10], link=x["permalink"]))
    save(new)
    for k in KINDS:
        print(f"{k}: {len(new[k])} 語")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "scan":
        scan()
    elif cmd == "list":
        kinds = [sys.argv[2]] if len(sys.argv) > 2 else KINDS
        for k in kinds:
            es = load()[k]
            print(f"--- {k}({len(es)} 語)")
            for e in es:
                print(f"{e.get('date')}  {str(e.get('no') or ''):>4}  {e['status']}  {e['word']}")
    elif cmd == "check":
        kind, words = sys.argv[2], sys.argv[3:]
        same, similar = check(kind, words)
        hit = {w for w, _ in same}
        for w, e in same:
            print(f"× {w}:使用済み({e['status']} {e.get('no')}番 {e.get('date')})")
        for w, e in similar:
            print(f"△ {w}:似ている単語 {e['word']}({e.get('no')}番)")
        for w in words:
            if w not in hit:
                print(f"○ {w}")


if __name__ == "__main__":
    main()
