"""名探偵アイビーの謎解き(@vocab_flicks)にリールを予約投稿する。予約表は ivy_schedule.json(日本時間)。

    python3 ivy_post.py add case01_decoy "2026-11-15 19:00"   # if_short.py で作った動画を公開して予約に追加(Mac で実行)
    python3 ivy_post.py list
    python3 ivy_post.py run       # 時間になった予約を投稿(GitHub Actions が15分おきに実行)

投稿のしかたは manga_post.py と同じ(リール+ストーリー+正解・和訳のコメント)。トークンは IVY_IG_*。
"""
import json
import os
import shutil
import sys
from pathlib import Path

import manga_post as mp
import post

ROOT = Path(__file__).parent
mp.SCHEDULE = ROOT / "ivy_schedule.json"
mp.LOG = ROOT / "ivy_posted.json"


def use_ivy_account():
    post.load_env()
    os.environ["IG_USER_ID"] = os.environ["IVY_IG_USER_ID"]
    os.environ["IG_ACCESS_TOKEN"] = os.environ["IVY_IG_ACCESS_TOKEN"]


mp.use_manga_account = use_ivy_account


def add(name, at):
    import if_short
    sc = if_short.SHORTS[name]
    src = ROOT / "out" / "ivy_short" / f"{name}.mp4"
    if not src.exists():
        sys.exit(f"{src} がありません(if_short.py で作ってください)")
    key = f"ivy_{name}"
    dst = ROOT / "docs" / "manga" / f"{key}_reel.mp4"
    shutil.copy(src, dst)
    items = [s for s in mp.load(mp.SCHEDULE, []) if s["key"] != key]
    items.append({"key": key, "at": at, "caption": if_short.caption(sc), "comment": if_short.comment(sc)})
    items.sort(key=lambda s: s["at"])
    mp.SCHEDULE.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n")
    mp.push([str(dst), str(mp.SCHEDULE)], f"名探偵アイビー {key} を {at} に予約")
    print(f"✓ {key} を {at} に予約しました")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "add":
        add(sys.argv[2], sys.argv[3])
    elif cmd == "run":
        mp.run()
    else:
        done = mp.load(mp.LOG, {})
        for s in mp.load(mp.SCHEDULE, []):
            print(f"{s['at']}  {s['key']:<24} {'投稿済み' if s['key'] in done else '予約中'}")
