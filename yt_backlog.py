"""YouTube に出ていない eng_navi の昔の回を、1日2本ずつ番号順に YouTube ショートへ(穴埋め)。

    python3 yt_backlog.py run       # GitHub Actions が15分おきに実行(10:30 と 16:30 の枠)
    python3 yt_backlog.py status

- 新しい回(インスタに出たもの)は post.py がその場で YouTube にも送る。ここは #1 からの昔の回だけ
- 1日の YouTube ショートは 新しい分6本+ここの2本=8本までにする(出しすぎない)
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import post
import tiktok_eng
import youtube_buffer

ROOT = Path(__file__).parent
STATE = ROOT / "yt_backlog_posted.json"
SLOTS = ["10:30", "16:30"]
FIRST_NEW = 185  # これ以降は post.py が送っている


def load():
    return json.loads(STATE.read_text()) if STATE.exists() else {"last": 0, "log": []}


def run():
    st = load()
    now = datetime.now(post.JST)
    today = now.strftime("%Y-%m-%d")
    done = sum(1 for e in st["log"] if e["at"].startswith(today))
    due = sum(1 for s in SLOTS if s <= now.strftime("%H:%M"))
    nxt = st["last"] + 1
    if nxt >= FIRST_NEW:
        print("YouTube 穴埋め:昔の回はすべて出しました")
        return False
    if done >= due:
        print(f"YouTube 穴埋め:次の枠まで待ちます(今日 {done} 本)")
        return False
    if not (ROOT / "docs" / "videos" / f"q{nxt}.mp4").exists():
        post.publish_video(nxt)
    q = {x["no"]: x for x in json.loads((ROOT / "quizzes.json").read_text())}[nxt]
    cap = tiktok_eng.caption_for(q)  # 昔の回のキャプションがない分も作る(答えつき)
    site = os.environ.get("SITE_URL", "https://eng-navi.github.io").rstrip("/")
    kind = q.get("category") or "英語"
    pid = youtube_buffer.send(f"{site}/videos/q{nxt}.mp4", cap, title=f"{kind}クイズ No.{nxt}|①と②、どっち?🧠", topic=youtube_buffer.topic_of_quiz(q), n=nxt)  # 同じタイトルが並ばないように番号を入れる
    if not pid:
        return False
    st["last"] = nxt
    st["log"].append({"no": nxt, "post": pid, "at": now.isoformat(timespec="seconds")})
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n")
    print(f"✓ YouTube 穴埋め:{nxt} を出しました")
    return True


if __name__ == "__main__":
    if (sys.argv[1:] or ["status"])[0] == "run":
        if os.environ.get("CI"):
            post.git("config", "user.name", "github-actions[bot]")
            post.git("config", "user.email", "41898299+github-actions[bot]@users.noreply.github.com")
        if run():
            import manga_post as mp
            mp.push([str(STATE)], "YouTube 穴埋め")
    else:
        st = load()
        print(f"YouTube 穴埋め:{st['last']} まで / {FIRST_NEW - 1} 本中")
