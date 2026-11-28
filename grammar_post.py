"""やさしい英文法(@uk_easy_grammar)にリールを予約投稿する。トークンは VOX_IG_*(旧お金とテックを着せ替え)。

    python3 grammar_post.py plan 2 9 "2026-11-28 17:30"   # No.2〜9 を、その時刻から SLOTS の順に予約(Mac で実行)
    python3 grammar_post.py now 1                          # すぐ投稿(Mac で実行。動画は先に公開・push 済みのこと)
    python3 grammar_post.py run                            # 時間になった予約を投稿(GitHub Actions)
動画は grammar_reel.py で作り、日本語の読みを yomi_check.py で確認してから予約する。
リールはフィードにも表示(share_to_feed=true)。正解と詳しい解説はコメント欄に。
"""
import json
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

import manga_post as mp
import post

ROOT = Path(__file__).parent
SITE = os.environ.get("SITE_URL", "https://eng-navi.github.io")
SCHEDULE, LOG = ROOT / "grammar_schedule.json", ROOT / "grammar_posted.json"
SLOTS = ["07:30", "12:30", "20:30"]
TAGS = "#英文法 #中学英語 #英語やり直し #大人の英語学習 #英検 #TOEIC #イギリス英語"
MUSIC = "Music: Cycles / DADA — Music from #Uppbeat (free for Creators!)"


def use():
    post.load_env()
    os.environ["IG_USER_ID"] = os.environ["VOX_IG_USER_ID"]
    os.environ["IG_ACCESS_TOKEN"] = os.environ["VOX_IG_ACCESS_TOKEN"]


def lesson(no):
    from grammar_lessons import LESSONS
    return next(L for L in LESSONS if L["no"] == int(no))


def texts(L):
    B = "　"
    q = L["q"]
    cap = "\n".join([
        f"📘 {L['title']}", B,
        "🇬🇧 例文はイギリス英語の男女が読み上げ",
        "💬 最後のクイズ、1か2か、コメントで答えてね👇",
        "✅ 正解と詳しい解説は、コメント欄に📌",
        "🔖 保存して、あとで見返してね", B,
        TAGS, B, MUSIC,
    ])
    com = "\n".join([
        f"✅ 正解:{q['answer']}. {q['word']}",
        q["en"].replace("|", " ").replace("(    )", q["word"]),
        f"💡 {L['point']}", B,
        "━━ 詳しい解説 ━━", L["detail"].replace("\n\n", f"\n{B}\n"), B,
        "📗 ほかの文法も、プロフィールからどうぞ",
    ])
    return cap, com


def add(no, at):
    import grammar_reel as gr
    no = int(no)
    src = gr.OUT / f"lesson_{no:03d}.mp4"
    if not src.exists():
        gr.render(0, no, src)
    starts = json.loads(src.with_suffix(".starts.json").read_text())
    dst = ROOT / "docs" / "grammar" / f"lesson_{no:03d}.mp4"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dst)
    cap, com = texts(lesson(no))
    key = f"grammar_{no:03d}"
    items = [s for s in mp.load(SCHEDULE, []) if s["key"] != key]
    items.append({"key": key, "at": at, "video": f"{SITE}/grammar/{dst.name}", "caption": cap, "comment": com, "thumb_ms": int((starts[2] + 2.0) * 1000)})
    items.sort(key=lambda s: s["at"])
    SCHEDULE.write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n")
    return [str(dst), str(SCHEDULE)]


def publish(s):
    use()
    user = os.environ["IG_USER_ID"]
    c = post.api("POST", f"{user}/media", media_type="REELS", video_url=s["video"], caption=s["caption"],
                 share_to_feed="true", thumb_offset=str(s.get("thumb_ms", 6500)))["id"]
    post.wait_until_ready(c)
    mid = post.api("POST", f"{user}/media_publish", creation_id=c)["id"]
    post.api("POST", f"{mid}/comments", message=s["comment"])
    link = post.api("GET", mid, fields="permalink").get("permalink", "")
    log = mp.load(LOG, {})
    log[s["key"]] = {"media_id": mid, "permalink": link, "posted_at": datetime.now(post.JST).isoformat(timespec="seconds")}
    LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
    print(f"✓ {s['key']} {link}")


def run():
    if os.environ.get("CI"):
        post.git("config", "user.name", "github-actions[bot]")
        post.git("config", "user.email", "41898299+github-actions[bot]@users.noreply.github.com")
    done = mp.load(LOG, {})
    now = datetime.now(post.JST)
    due = [s for s in mp.load(SCHEDULE, []) if s["key"] not in done
           and datetime.strptime(s["at"], "%Y-%m-%d %H:%M").replace(tzinfo=post.JST) <= now]
    if not due:
        print("時間になった英文法リールはありません"); return
    publish(min(due, key=lambda s: s["at"]))
    mp.push([str(LOG)], "英文法リールを投稿")


def plan(a, b, first):
    """first の時刻から始めて、以降は SLOTS の時刻に順に入れる"""
    t = datetime.strptime(first, "%Y-%m-%d %H:%M")
    paths = []
    for no in range(int(a), int(b) + 1):
        paths += add(no, f"{t:%Y-%m-%d %H:%M}")
        print(f"No.{no} → {t:%Y-%m-%d %H:%M}")
        later = [x for x in SLOTS if x > f"{t:%H:%M}"]
        t = datetime.strptime(f"{t:%Y-%m-%d} {later[0]}", "%Y-%m-%d %H:%M") if later else \
            datetime.strptime(f"{t + timedelta(days=1):%Y-%m-%d} {SLOTS[0]}", "%Y-%m-%d %H:%M")
    mp.push(paths, f"英文法リール No.{a}〜{b} を予約")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "plan":
        plan(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "now":
        s = next(x for x in mp.load(SCHEDULE, []) if x["key"] == f"grammar_{int(sys.argv[2]):03d}")
        publish(s)
        mp.push([str(LOG)], "英文法リールを投稿")
    elif cmd == "run":
        run()
    else:
        done = mp.load(LOG, {})
        for s in mp.load(SCHEDULE, []):
            print(f"{s['at']}  {s['key']}  {'投稿済み' if s['key'] in done else '予約中'}")
