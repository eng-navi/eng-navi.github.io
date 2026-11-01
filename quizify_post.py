"""@quizify_english にリールを予約投稿する。予約表は quizify_schedule.json(日本時間)。

    python3 quizify_post.py add black_277 "2026-11-01 19:30"   # 動画を公開して予約に追加(説明欄は out/quizify/<key>.txt)
    python3 quizify_post.py list
    python3 quizify_post.py run      # 時間になった予約を投稿(GitHub Actions が15分おきに実行)

4コマ(manga_post.py)と同じ仕組みを、quizify 用のトークン(QUIZIFY_IG_*)で使う。動画は docs/quizify/ に公開する。
投稿したら答え・解説をコメントにも置き、quizify_words.json の単語を「投稿済み」にする。
"""
import json
import os
import shutil
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

import manga_post as mp
import post

ROOT = Path(__file__).parent
SCHEDULE = ROOT / "quizify_schedule.json"
LOG = ROOT / "quizify_posted.json"
WORDS = ROOT / "quizify_words.json"


def use_quizify_account():
    post.load_env()
    os.environ["IG_USER_ID"] = os.environ["QUIZIFY_IG_USER_ID"]
    os.environ["IG_ACCESS_TOKEN"] = os.environ["QUIZIFY_IG_ACCESS_TOKEN"]


def add(key, at):
    src = ROOT / "out" / "quizify" / f"{key}.mp4"
    cap = src.with_suffix(".txt")
    if not src.exists() or not cap.exists():
        sys.exit(f"{src} か {cap} がありません")
    dst = ROOT / "docs" / "quizify" / f"{key}.mp4"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dst)
    items = [s for s in mp.load(SCHEDULE, []) if s["key"] != key]
    items.append({"key": key, "at": at, "caption": cap.read_text().rstrip()})
    items.sort(key=lambda s: s["at"])
    SCHEDULE.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n")
    return dst


def mark_posted(key):
    """黒・白は、その回の番号の単語を「投稿済み」にする。"""
    kind, first = key.split("_")
    if kind not in ("black", "white") or not WORDS.exists():
        return
    nos = range(int(first), int(first) + (3 if kind == "black" else 2))
    data = json.loads(WORDS.read_text())
    for e in data[kind]:
        if e.get("no") in nos and e["status"] == "予定":
            e["status"] = "投稿済み"
            e["date"] = datetime.now(post.JST).date().isoformat()
    WORDS.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")


def comment_text(caption):
    """説明欄の答え・解説の部分(最初の ----- から最後の ----- まで)。コメントにも同じものを置く。"""
    lines = caption.split("\n")
    marks = [i for i, l in enumerate(lines) if l.startswith("-----")]
    return "\n".join(lines[marks[0]:marks[-1] + 1]) if len(marks) >= 2 else ""


def add_comment(media_id, caption):
    text = comment_text(caption)
    if text:
        post.api("POST", f"{media_id}/comments", message=post.keep_blank_lines(text))


def publish(item):
    url = f"{os.environ.get('SITE_URL', 'https://eng-navi.github.io').rstrip('/')}/quizify/{item['key']}.mp4"
    for _ in range(40):  # 公開URLに反映されるまで待つ
        try:
            if urllib.request.urlopen(urllib.request.Request(url, method="HEAD")).status == 200:
                break
        except Exception:
            pass
        time.sleep(15)
    user = os.environ["IG_USER_ID"]
    c = post.api("POST", f"{user}/media", media_type="REELS", video_url=url,
                 caption=post.keep_blank_lines(item["caption"]), share_to_feed="true")["id"]
    post.wait_until_ready(c)
    mid = post.api("POST", f"{user}/media_publish", creation_id=c)["id"]
    add_comment(mid, item["caption"])  # 答え・解説はコメントにも(タップしやすい)
    story = post.post_story(url)
    link = post.api("GET", mid, fields="permalink").get("permalink")
    log = mp.load(LOG, {})
    log[item["key"]] = {"media_id": mid, "story_id": story, "permalink": link,
                        "posted_at": datetime.now(post.JST).isoformat(timespec="seconds")}
    LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
    mark_posted(item["key"])
    print(f"✓ {item['key']} を投稿 {link}")


def run():
    if os.environ.get("CI"):
        post.git("config", "user.name", "github-actions[bot]")
        post.git("config", "user.email", "41898299+github-actions[bot]@users.noreply.github.com")
    use_quizify_account()
    done = mp.load(LOG, {})
    now = datetime.now(post.JST)
    # グリッドの色(青・白・黒)がそろうよう、必ず予約表の順に1本ずつ。前の1本が出るまで次は出さない
    rest = sorted((s for s in mp.load(SCHEDULE, []) if s["key"] not in done), key=lambda s: s["at"])
    if not rest or datetime.strptime(rest[0]["at"], "%Y-%m-%d %H:%M").replace(tzinfo=post.JST) > now:
        print("時間になった quizify の予約はありません")
        return
    publish(rest[0])
    import build_quizify_site
    build_quizify_site.pages()  # 復習ページに今の回を載せる
    pages = [str(ROOT / "docs" / d / "index.html") for d in ("quizify", "listening", "tango", "tango-advanced")]
    mp.push([str(LOG), str(WORDS)] + pages, "quizify を投稿")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "add":
        dst = add(sys.argv[2], sys.argv[3])
        mp.push([str(dst), str(SCHEDULE)], f"quizify {sys.argv[2]} を {sys.argv[3]} に予約")
        print(f"✓ {sys.argv[2]} を {sys.argv[3]} に予約しました")
    elif cmd == "run":
        run()
    else:
        done = mp.load(LOG, {})
        for s in mp.load(SCHEDULE, []):
            print(f"{s['at']}  {s['key']:<16} {'投稿済み' if s['key'] in done else '予約中'}")


if __name__ == "__main__":
    main()
