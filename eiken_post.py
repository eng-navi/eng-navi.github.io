"""英検リーディング部(@eiken_reading_club)にカルーセルを予約投稿する。トークンは SEA_IG_*(旧・海クイズのアカウント)。
    python3 eiken_post.py plan 1 6 "2026-11-24"   # 1日3本(07:00/12:00/21:00)で予約
    python3 eiken_post.py now 1                   # すぐ投稿
    python3 eiken_post.py run                     # GitHub Actions
"""
import json, os, sys
from datetime import datetime, timedelta
from pathlib import Path
import manga_post as mp, post, toeic_post as tp
ROOT = Path(__file__).parent
SCHEDULE, LOG = ROOT / "eiken_schedule.json", ROOT / "eiken_posted.json"
SITE = os.environ.get("SITE_URL", "https://eng-navi.github.io")
SLOTS = ["07:00", "12:00", "21:00"]
TAGS = "#英検 #英検準1級 #英検2級 #英検対策 #英語長文 #英語学習 #大学受験英語 #英検リーディング"

def use_account():
    post.load_env()
    os.environ["IG_USER_ID"] = os.environ["SEA_IG_USER_ID"]; os.environ["IG_ACCESS_TOKEN"] = os.environ["SEA_IG_ACCESS_TOKEN"]

def caption(Q):
    creds = {}
    for d in ("eiken_photos", "toeic_photos"):
        f = ROOT / "assets" / d / "credits.json"
        if f.exists(): creds.update(json.loads(f.read_text()))
    c = creds.get(Q["photo"], {}); B = "　"
    eng = " ".join(t for para in Q["body"] for t, _ in para)
    return "\n".join([f"⏱ 目安{Q['sec']}秒。{Q['level']}レベルの長文、解ける?", "1か2か、コメントで👇", B,
        f"📖 テーマ:{Q['title']}", f"💡 {Q['cover'][2]}", B,
        "📝 和訳・答え・ワナは、めくって確認", "🔖 保存して、試験前にもう一度", B,
        "━━━━━━", "英文(全文)", eng, "━━━━━━", B,
        "📚 英検の単語帳・問題集のおすすめは、プロフィールのリンクから", "🔗 無料の復習ページもプロフィールから", B,
        TAGS, f"📷 {c.get('creator', '')} / CC0"])

def add(no, at):
    from PIL import Image
    from eiken_problems import PROBLEMS
    Q = next(q for q in PROBLEMS if q["no"] == int(no))
    src = ROOT / "out" / "eiken" / f"no{Q['no']:03d}"; key = f"eiken_{Q['no']:03d}"
    dst = ROOT / "docs" / "eiken" / key; dst.mkdir(parents=True, exist_ok=True); urls, paths = [], []
    for i, p in enumerate(sorted(src.glob("0*.png")), 1):
        o = dst / f"{i:02d}.jpg"; Image.open(p).convert("RGB").save(o, quality=92)
        urls.append(f"{SITE}/eiken/{key}/{i:02d}.jpg"); paths.append(str(o))
    items = [s for s in mp.load(SCHEDULE, []) if s["key"] != key]
    items.append({"key": key, "at": at, "caption": caption(Q), "images": urls}); items.sort(key=lambda s: s["at"])
    SCHEDULE.write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n"); return paths + [str(SCHEDULE)]

def publish(s):
    tp.LOG = LOG; tp.publish(s)

def run():
    if os.environ.get("CI"):
        post.git("config", "user.name", "github-actions[bot]"); post.git("config", "user.email", "41898299+github-actions[bot]@users.noreply.github.com")
    use_account(); done = mp.load(LOG, {}); now = datetime.now(post.JST)
    due = [s for s in mp.load(SCHEDULE, []) if s["key"] not in done and datetime.strptime(s["at"], "%Y-%m-%d %H:%M").replace(tzinfo=post.JST) <= now]
    if not due: print("時間になった英検の予約はありません"); return
    publish(min(due, key=lambda s: s["at"])); mp.push([str(LOG)], "英検リーディング部を投稿")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "plan":
        a, b, day = int(sys.argv[2]), int(sys.argv[3]), datetime.strptime(sys.argv[4], "%Y-%m-%d"); paths = []
        for k, no in enumerate(range(a, b + 1)):
            at = f"{day + timedelta(days=k // 3):%Y-%m-%d} {SLOTS[k % 3]}"; paths += add(no, at); print(no, at)
        mp.push(paths, f"英検 No.{a}〜{b} を予約")
    elif cmd == "now":
        no = int(sys.argv[2]); paths = add(no, datetime.now(post.JST).strftime("%Y-%m-%d %H:%M")); mp.push(paths, f"英検 No.{no} を公開")
    elif cmd == "run": run()
    else:
        done = mp.load(LOG, {})
        for s in mp.load(SCHEDULE, []): print(s["at"], s["key"], "投稿済み" if s["key"] in done else "予約中")
