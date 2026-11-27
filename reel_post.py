"""TOEIC読解・英検リーディング部のタイマー付きリールを予約投稿する。
    python3 reel_post.py plan toeic 1 10 "2026-11-28"   # No.1〜10 を1日2本(SLOTS)で予約(Mac で実行)
    python3 reel_post.py add toeic 1 "2026-11-27 14:10"
    python3 reel_post.py run toeic                       # GitHub Actions(アカウントごと)
リールは share_to_feed=false(フィードのグリッドには出さず、リール欄だけ)。答えはコメント欄に。"""
import json, os, shutil, sys
from datetime import datetime, timedelta
from pathlib import Path
import manga_post as mp, post
ROOT = Path(__file__).parent
SITE = os.environ.get("SITE_URL", "https://eng-navi.github.io")
SCHEDULE, LOG = ROOT / "reel_schedule.json", ROOT / "reel_posted.json"
SLOTS = {"toeic": ["10:00", "18:30"], "eiken": ["09:30", "18:00"]}
ENV = {"toeic": "IVY", "eiken": "SEA"}
TAGS = {"toeic": "#TOEIC #TOEICリーディング #Part7 #TOEIC勉強 #英語学習", "eiken": "#英検 #英検準1級 #英検2級 #英検対策 #英語長文"}

def use(kind):
    post.load_env(); e = ENV[kind]
    os.environ["IG_USER_ID"] = os.environ[f"{e}_IG_USER_ID"]; os.environ["IG_ACCESS_TOKEN"] = os.environ[f"{e}_IG_ACCESS_TOKEN"]

def texts(kind, no, credit):
    B = "　"
    if kind == "toeic":
        from toeic_problems import PROBLEMS; Q = next(q for q in PROBLEMS if q["no"] == no)
        ans, hook = Q["answer"], f"TOEIC Part 7|{Q['type']}、時間内に解ける?⏱"
        pick = "AかBか"
    else:
        from eiken_problems import PROBLEMS; Q = next(q for q in PROBLEMS if q["no"] == no)
        ans, hook = f"{Q['answer']}. {Q['choices'][Q['answer'] - 1][0]}", f"英検準1級|長文の空所「{Q['title']}」、時間内に解ける?⏱"
        pick = "1か2か"
    cap = "\n".join([hook, f"{pick}、コメントで答えてね👇", B, "✅ 答えはコメント欄に", "📖 全文和訳・ワナ・解き方のコツは、同じ問題のカルーセル投稿で(プロフィールから)", "🔖 保存して、あとでもう一度", B, TAGS[kind], B, f"Music: {credit} — Music from #Uppbeat (free for Creators!)"])
    words = "\n".join(f"▶ {a} … {b}" for a, b in Q["words"])
    com = "\n".join([f"✅ 正解:{ans}", Q["explain"][0]["text"].split("\n")[0], B,
                      "━━ 詳しい解説 ━━", B, "【根拠】", Q["explain"][0]["text"], B, "【ワナの選択肢】", Q["explain"][1]["text"], B,
                      "【解き方のコツ】", Q["explain"][2]["text"], B, "【全文和訳】", Q["ja"], B, "【単語】", words, B,
                      "🔖 保存して、あとで見返してね"])[:2150]
    return cap, com

def add(kind, no, at):
    import reel_quiz
    src, credit = reel_quiz.build(kind, int(no))
    dst = ROOT / "docs" / "reels" / f"{kind}_{int(no):03d}.mp4"; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy(src, dst)
    cap, com = texts(kind, int(no), credit); key = f"{kind}_{int(no):03d}"
    items = [s for s in mp.load(SCHEDULE, []) if s["key"] != key]
    items.append({"key": key, "kind": kind, "at": at, "video": f"{SITE}/reels/{dst.name}", "caption": cap, "comment": com})
    items.sort(key=lambda s: s["at"]); SCHEDULE.write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n")
    return [str(dst), str(SCHEDULE)]

def publish(s):
    use(s["kind"]); user = os.environ["IG_USER_ID"]
    c = post.api("POST", f"{user}/media", media_type="REELS", video_url=s["video"], caption=s["caption"], share_to_feed="false")["id"]
    post.wait_until_ready(c)
    mid = post.api("POST", f"{user}/media_publish", creation_id=c)["id"]
    post.api("POST", f"{mid}/comments", message=s["comment"])
    link = post.api("GET", mid, fields="permalink").get("permalink", "")
    log = mp.load(LOG, {}); log[s["key"]] = {"media_id": mid, "permalink": link, "posted_at": datetime.now(post.JST).isoformat(timespec="seconds")}
    LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n"); print(f"✓ {s['key']} {link}")

def run(kind):
    if os.environ.get("CI"):
        post.git("config", "user.name", "github-actions[bot]"); post.git("config", "user.email", "41898299+github-actions[bot]@users.noreply.github.com")
    done = mp.load(LOG, {}); now = datetime.now(post.JST)
    due = [s for s in mp.load(SCHEDULE, []) if s["kind"] == kind and s["key"] not in done and datetime.strptime(s["at"], "%Y-%m-%d %H:%M").replace(tzinfo=post.JST) <= now]
    if not due: print(f"時間になった{kind}リールはありません"); return
    publish(min(due, key=lambda s: s["at"])); mp.push([str(LOG)], f"{kind}リールを投稿")

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "add": mp.push(add(sys.argv[2], sys.argv[3], sys.argv[4]), f"{sys.argv[2]}リール No.{sys.argv[3]} を予約")
    elif cmd == "plan":
        kind, a, b, day = sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), datetime.strptime(sys.argv[5], "%Y-%m-%d"); paths = []
        for k, no in enumerate(range(a, b + 1)):
            at = f"{day + timedelta(days=k // 2):%Y-%m-%d} {SLOTS[kind][k % 2]}"; paths += add(kind, no, at); print(kind, no, at)
        mp.push(paths, f"{kind}リール No.{a}〜{b} を予約")
    elif cmd == "run": run(sys.argv[2])
