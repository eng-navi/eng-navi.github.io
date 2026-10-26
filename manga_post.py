"""4コマのアカウント(@yonkoma_eigo)にリールを予約投稿する。予約表は manga_schedule.json(日本時間)。

    python3 manga_post.py add company_cafeteria "2026-10-26 19:00"   # 動画を公開して予約に追加(Mac で実行)
    python3 manga_post.py list
    python3 manga_post.py run       # 時間になった予約を投稿(GitHub Actions が15分おきに実行)

各予約は {key, at, caption}。動画は out/manga/<key>_reel.mp4 を docs/manga/ に公開して使う。
eng_navi と同じ post.py の仕組みを、4コマ用のトークン(MANGA_IG_*)で使う。
"""
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

import post

ROOT = Path(__file__).parent
SCHEDULE = ROOT / "manga_schedule.json"
LOG = ROOT / "manga_posted.json"


def use_manga_account():
    post.load_env()
    os.environ["IG_USER_ID"] = os.environ["MANGA_IG_USER_ID"]
    os.environ["IG_ACCESS_TOKEN"] = os.environ["MANGA_IG_ACCESS_TOKEN"]


def load(p, empty):
    return json.loads(p.read_text()) if p.exists() else empty


def push(paths, msg):
    post.git("add", *paths)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0:
        return
    post.git("commit", "-q", "-m", msg)
    post.git("pull", "-q", "--rebase", "--autostash")
    post.git("push", "-q")


def add(key, at, caption):
    src = ROOT / "out" / "manga" / f"{key}_reel.mp4"
    if not src.exists():
        sys.exit(f"{src} がありません(manga_reel.py で作ってください)")
    dst = ROOT / "docs" / "manga" / f"{key}_reel.mp4"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dst)
    items = [s for s in load(SCHEDULE, []) if s["key"] != key]
    items.append({"key": key, "at": at, "caption": caption})
    items.sort(key=lambda s: s["at"])
    SCHEDULE.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n")
    push([str(dst), str(SCHEDULE)], f"4コマ {key} を {at} に予約")
    print(f"✓ {key} を {at} に予約しました")


PAGE_NOTE = "🔊 セリフを何回でも聞ける音声ページは、プロフィールのリンクから"


def with_page_note(item):
    """サイトに4コマのページ(docs/manga/<key>/)があれば、Music の行の前に案内を1行入れる"""
    cap = item["caption"]
    if not (ROOT / "docs" / "manga" / item["key"] / "index.html").exists() or PAGE_NOTE in cap:
        return cap
    if "\nMusic:" in cap:
        head, tail = cap.split("\nMusic:", 1)
        return f"{head.rstrip()}\n\n{PAGE_NOTE}\n\nMusic:{tail}"
    return f"{cap.rstrip()}\n\n{PAGE_NOTE}"


def publish(item):
    url = f"{os.environ.get('SITE_URL', 'https://eng-navi.github.io').rstrip('/')}/manga/{item['key']}_reel.mp4"
    for _ in range(40):  # 公開URLに反映されるまで待つ
        try:
            if urllib.request.urlopen(urllib.request.Request(url, method="HEAD")).status == 200:
                break
        except Exception:
            pass
        time.sleep(15)
    user = os.environ["IG_USER_ID"]
    c = post.api("POST", f"{user}/media", media_type="REELS", video_url=url,
                 caption=post.keep_blank_lines(with_page_note(item)), share_to_feed="true")["id"]
    post.wait_until_ready(c)
    mid = post.api("POST", f"{user}/media_publish", creation_id=c)["id"]
    story = post.post_story(url)
    link = post.api("GET", mid, fields="permalink").get("permalink")
    log = load(LOG, {})
    log[item["key"]] = {"media_id": mid, "story_id": story, "permalink": link, "posted_at": datetime.now(post.JST).isoformat(timespec="seconds")}
    LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
    print(f"✓ {item['key']} を投稿 {link}")


def run():
    if os.environ.get("CI"):
        post.git("config", "user.name", "github-actions[bot]")
        post.git("config", "user.email", "41898299+github-actions[bot]@users.noreply.github.com")
    use_manga_account()
    done = load(LOG, {})
    now = datetime.now(post.JST)
    due = [s for s in load(SCHEDULE, []) if s["key"] not in done
           and datetime.strptime(s["at"], "%Y-%m-%d %H:%M").replace(tzinfo=post.JST) <= now]
    if not due:
        print("時間になった4コマの予約はありません")
        return
    publish(min(due, key=lambda s: s["at"]))  # 1回に1本(連投しない)
    push([str(LOG)], "4コマを投稿")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "add":
        add(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else sys.stdin.read())
    elif cmd == "run":
        run()
    else:
        done = load(LOG, {})
        for s in load(SCHEDULE, []):
            print(f"{s['at']}  {s['key']:<20} {'投稿済み' if s['key'] in done else '予約中'}")


if __name__ == "__main__":
    main()
