"""30秒TOEIC読解(@toeic_read30)にカルーセルを予約投稿する。トークンは IVY_IG_*(旧アイビーのアカウントを着せ替え)。

    python3 toeic_post.py add 1 "2026-11-24 07:30"   # toeic_set.py の画像を docs/toeic/ に公開して予約(Mac で実行)
    python3 toeic_post.py plan 1 6 "2026-11-24"      # No.1〜6 を 1日3本(07:30/12:30/20:30)で順に予約
    python3 toeic_post.py list
    python3 toeic_post.py run                         # 時間になった予約を投稿(GitHub Actions)
音楽は付かない(API ではカルーセルに音楽を付けられない)。
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import manga_post as mp
import post

ROOT = Path(__file__).parent
SCHEDULE = ROOT / "toeic_schedule.json"
LOG = ROOT / "toeic_posted.json"
SITE = os.environ.get("SITE_URL", "https://eng-navi.github.io")
SLOTS = ["07:30", "12:30", "20:30"]
TAGS = "#TOEIC #TOEICリーディング #Part7 #TOEIC勉強 #TOEIC900 #英語学習 #社会人の勉強 #英語長文"


def use_account():
    post.load_env()
    os.environ["IG_USER_ID"] = os.environ["IVY_IG_USER_ID"]
    os.environ["IG_ACCESS_TOKEN"] = os.environ["IVY_IG_ACCESS_TOKEN"]


def english(Q):
    P = Q["passage"]
    lines = list(P["head"]) + [" ".join(t for t, _ in para) for para in P["body"]]
    return "\n".join(lines)


def caption(Q):
    from toeic_problems import PROBLEMS  # noqa
    cred = json.loads((ROOT / "assets" / "toeic_photos" / "credits.json").read_text())[Q["photo"]]
    B = "　"
    return "\n".join([
        f"⏱ 目安{Q['sec']}秒。解けた?", "AかBか、コメントで👇", B,
        f"{Q['emoji']} 今回は{Q['type']}", f"💡 {Q['point']}", B,
        "📖 和訳・答え・ワナは、めくって確認", "🔖 保存して、本番前にもう一度", B,
        "━━━━━━", "📝 英文(全文)", english(Q), "━━━━━━", B,
        "📚 Part 7 をもっと解きたい人へ", "おすすめの問題集とアプリは、プロフィールのリンクにまとめています",
        "🔗 和訳つきの復習ページ(無料)もプロフィールから", B,
        TAGS, f"📷 {cred['creator']} / StockSnap(CC0)",
    ])


def add(no, at):
    from PIL import Image  # Mac でだけ使う(CI には Pillow がない)
    from toeic_problems import PROBLEMS
    Q = next(q for q in PROBLEMS if q["no"] == int(no))
    src = ROOT / "out" / "toeic_reading" / f"no{Q['no']:03d}"
    pngs = sorted(src.glob("0*.png"))
    if len(pngs) < 2:
        sys.exit(f"{src} に画像がありません(toeic_set.py {no} で作ってください)")
    key = f"toeic_{Q['no']:03d}"
    dst = ROOT / "docs" / "toeic" / key
    dst.mkdir(parents=True, exist_ok=True)
    urls, paths = [], []
    for i, p in enumerate(pngs, 1):
        out = dst / f"{i:02d}.jpg"
        Image.open(p).convert("RGB").save(out, quality=92)
        urls.append(f"{SITE}/toeic/{key}/{i:02d}.jpg"); paths.append(str(out))
    items = [s for s in mp.load(SCHEDULE, []) if s["key"] != key]
    items.append({"key": key, "at": at, "caption": caption(Q), "images": urls})
    items.sort(key=lambda s: s["at"])
    SCHEDULE.write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n")
    return paths + [str(SCHEDULE)]


def plan(a, b, day):
    d = datetime.strptime(day, "%Y-%m-%d"); paths = []
    for k, no in enumerate(range(int(a), int(b) + 1)):
        at = f"{(d + timedelta(days=k // len(SLOTS))):%Y-%m-%d} {SLOTS[k % len(SLOTS)]}"
        paths += add(no, at); print(f"No.{no} → {at}")
    import subprocess; subprocess.run([sys.executable, str(ROOT / "build_reading.py")], check=True)  # 復習ページも更新
    mp.push(paths + [str(ROOT / "docs" / "reading")], f"TOEIC読解 No.{a}〜{b} を予約")


def wait(cid, timeout=180):
    t = time.time()
    while time.time() - t < timeout:
        st = post.api("GET", cid, fields="status_code").get("status_code")
        if st == "FINISHED": return
        if st in ("ERROR", "EXPIRED"): sys.exit(f"取り込み失敗 {cid}: {st}")
        time.sleep(4)
    sys.exit(f"取り込みがタイムアウト {cid}")


def publish(s):
    user = os.environ["IG_USER_ID"]
    kids = []
    for u in s["images"]:
        c = post.api("POST", f"{user}/media", image_url=u, is_carousel_item="true")["id"]; wait(c); kids.append(c)
    car = post.api("POST", f"{user}/media", media_type="CAROUSEL", children=",".join(kids), caption=s["caption"])["id"]
    wait(car)
    mid = post.api("POST", f"{user}/media_publish", creation_id=car)["id"]
    link = post.api("GET", mid, fields="permalink").get("permalink", "")
    log = mp.load(LOG, {})
    log[s["key"]] = {"media_id": mid, "permalink": link, "posted_at": datetime.now(post.JST).isoformat(timespec="seconds")}
    LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
    print(f"✓ {s['key']} を投稿しました {link}")


def run():
    if os.environ.get("CI"):
        post.git("config", "user.name", "github-actions[bot]")
        post.git("config", "user.email", "41898299+github-actions[bot]@users.noreply.github.com")
    use_account()
    done = mp.load(LOG, {}); now = datetime.now(post.JST)
    due = [s for s in mp.load(SCHEDULE, []) if s["key"] not in done
           and datetime.strptime(s["at"], "%Y-%m-%d %H:%M").replace(tzinfo=post.JST) <= now]
    if not due:
        print("時間になったTOEIC読解の予約はありません"); return
    publish(min(due, key=lambda s: s["at"]))  # 1回に1本
    mp.push([str(LOG)], "TOEIC読解を投稿")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "add":
        mp.push(add(sys.argv[2], sys.argv[3]), f"TOEIC読解 No.{sys.argv[2]} を予約")
    elif cmd == "plan":
        plan(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "run":
        run()
    else:
        done = mp.load(LOG, {})
        for s in mp.load(SCHEDULE, []):
            print(f"{s['at']}  {s['key']:<12} {'投稿済み' if s['key'] in done else '予約中'}")
