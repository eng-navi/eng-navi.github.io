"""eng_navi の動画を TikTok(@quizify_english、中身は eng_navi のグリッド)に、番号順に1本ずつ出す。

    python3 tiktok_eng.py run      # GitHub Actions が15分おきに実行
    python3 tiktok_eng.py status

- TikTok の最後は 62(緑)だったので、63 から順に出す。インスタの最新番号に追いつくまで、1日 PER_DAY 本のペースで
  (追いついたら、インスタに出た番号を順に出すだけになる)。番号順を守るので、緑 → ピンク → 青 の並びが崩れない
- インスタでまだ出ていない番号は出さない(答えを先に見せない)
- 動画は docs/videos/q<番号>.mp4(公開URL)を Buffer に渡す。説明文はキャプション+答え(TikTok は自分でコメントを付けられないので)
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import post
import youtube_buffer

ROOT = Path(__file__).parent
STATE = ROOT / "tiktok_eng_posted.json"
SLOTS = ["07:30", "10:00", "12:30", "15:00", "17:30", "20:00", "22:30"]  # 1日の投稿時刻(追いつくまでは全部使う)
PER_DAY = len(SLOTS)
SITE = os.environ.get("SITE_URL", "https://eng-navi.github.io").rstrip("/")
TAGS = {2: "#英検2級 #英文法 #英語学習", 0: "#英語フレーズ #英検準1級 #英語学習", 1: "#TOEIC #TOEIC文法 #英語学習"}


def load():
    return json.loads(STATE.read_text()) if STATE.exists() else {"last": 62, "log": []}


def caption_for(q):
    cap = q.get("caption") or ""
    if not cap:  # 昔の回はキャプションが残っていないので作る
        head = "この英語、読める?📖" if "text" in q else "①と②、どっち?🧠"
        cap = f"{head}\n{q.get('category') or ('イディオム' if 'text' in q else '英文法')}の問題です。\n\n{TAGS[q['no'] % 3]}"
    return cap + "\n\n👇 答えと解説\n" + post.build_comment(q)


def run():
    st = load()
    now = datetime.now(post.JST)
    today = now.strftime("%Y-%m-%d")
    done_today = sum(1 for e in st["log"] if e["at"].startswith(today))
    due = sum(1 for s in SLOTS if s <= now.strftime("%H:%M"))
    nxt = st["last"] + 1
    latest = max(x["no"] for x in json.loads((ROOT / "posted.json").read_text()))
    if nxt > latest:
        print(f"TikTok: インスタに追いついています(次は {nxt})")
        return False
    if st["log"] and (now - datetime.fromisoformat(st["log"][-1]["at"])).total_seconds() < 2 * 3600:
        print("TikTok: 前の投稿から2時間たっていないので待ちます")  # まとめて出さない
        return False
    if done_today >= due:
        print(f"TikTok: 次の時刻まで待ちます(今日 {done_today} 本)")
        return False
    if not (ROOT / "docs" / "videos" / f"q{nxt}.mp4").exists():
        post.publish_video(nxt)
    quizzes = {q["no"]: q for q in json.loads((ROOT / "quizzes.json").read_text())}
    pid = youtube_buffer.send_tiktok(f"{SITE}/videos/q{nxt}.mp4", caption_for(quizzes[nxt]))
    if not pid:
        return False
    st["last"] = nxt
    st["log"].append({"no": nxt, "post": pid, "at": now.isoformat(timespec="seconds")})
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n")
    print(f"✓ TikTok に {nxt} を出しました(インスタは {latest} まで)")
    return True


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "run":
        if os.environ.get("CI"):
            post.git("config", "user.name", "github-actions[bot]")
            post.git("config", "user.email", "41898299+github-actions[bot]@users.noreply.github.com")
        if run():
            import manga_post as mp
            mp.push([str(STATE)], "TikTok に eng_navi を投稿")
    else:
        st = load()
        latest = max(x["no"] for x in json.loads((ROOT / "posted.json").read_text()))
        print(f"TikTok の最後: {st['last']} / インスタ: {latest} / 残り {latest - st['last']} 本")
