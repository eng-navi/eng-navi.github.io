"""Instagram ストーリーの予約投稿(予約表 stories.json、日時は日本時間)。

    python3 stories.py list    # 予約と投稿済みの一覧
    python3 stories.py run     # 時間になった予約を投稿(GitHub Actions の予約投稿と一緒に実行)

1件 = 問題の画像(docs/stories/<id>_<n>_q.png)→ 1分あけて答えの動画(<id>_<n>_a.mp4)。
素材は story_idiom.py で作り、docs/stories/ に置いて push しておく。
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import post

ROOT = Path(__file__).parent
SCHEDULE = ROOT / "stories.json"
LOG = ROOT / "stories_posted.json"


def load(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def story(**media):
    user = post.os.environ["IG_USER_ID"]
    cid = post.api("POST", f"{user}/media", media_type="STORIES", **media)["id"]
    post.wait_until_ready(cid)
    return post.api("POST", f"{user}/media_publish", creation_id=cid)["id"]


def run():
    post.load_env()
    base = post.os.environ.get("SITE_URL", "https://eng-navi.github.io").rstrip("/")
    log = load(LOG, {})
    now = datetime.now(post.JST)
    for item in sorted(load(SCHEDULE, []), key=lambda s: s["at"]):
        key = item["key"]
        if key in log or datetime.strptime(item["at"], "%Y-%m-%d %H:%M").replace(tzinfo=post.JST) > now:
            continue
        q = story(image_url=f"{base}/stories/{key}_q.png")
        time.sleep(60)  # 問題を読む時間をあけてから答えを出す
        a = story(video_url=f"{base}/stories/{key}_a.mp4")
        log[key] = {"ids": [q, a], "posted_at": datetime.now(post.JST).isoformat(timespec="seconds")}
        LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
        print(f"✓ ストーリー {key} を投稿")


def show():
    log = load(LOG, {})
    for s in sorted(load(SCHEDULE, []), key=lambda s: s["at"]):
        print(f"{s['at']}  {s['key']:<6} {'投稿済み' if s['key'] in log else '予約中'}")


if __name__ == "__main__":
    run() if sys.argv[1:] == ["run"] else show()
