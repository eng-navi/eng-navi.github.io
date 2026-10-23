"""予約投稿。予約表は schedule.json(日時は日本時間)。

使い方:
    python3 schedule.py add 102 "2026-10-24 20:00"   # 動画を公開して予約表に追加(Mac で実行)
    python3 schedule.py list                         # 予約と投稿済みの一覧
    python3 schedule.py remove 102                   # 予約を取り消す
    python3 schedule.py run                          # 時間になった予約を1件投稿(GitHub Actions が15分おきに実行)
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import post

ROOT = Path(__file__).parent
SCHEDULE = ROOT / "schedule.json"


def load(path):
    return json.loads(path.read_text()) if path.exists() else []


def save_schedule(items):
    items.sort(key=lambda s: s["no"])
    SCHEDULE.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n")


def parse_at(text):
    return datetime.strptime(text, "%Y-%m-%d %H:%M").replace(tzinfo=post.JST)


def posted_nos():
    return {p["no"] for p in load(post.LOG)}


def quiz(no):
    q = next((q for q in load(ROOT / "quizzes.json") if q["no"] == no), None)
    if q is None:
        sys.exit(f"{no} が quizzes.json にありません")
    if not q.get("caption"):
        sys.exit(f"{no} に caption がありません")
    return q


def push(paths, message):
    post.git("add", *paths)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0:
        return
    post.git("commit", "-q", "-m", message)
    post.git("pull", "-q", "--rebase")
    post.git("push", "-q")


def add(no, at):
    quiz(no)
    items = [s for s in load(SCHEDULE) if s["no"] != no]
    if no in posted_nos():
        sys.exit(f"{no} は投稿済みです")
    # 色の順番を崩さないよう、番号の順と時刻の順が一致しているか確認する
    when = parse_at(at)
    for s in items:
        if (s["no"] < no) != (parse_at(s["at"]) < when):
            sys.exit(f"番号と時刻の順番が逆になります({s['no']} は {s['at']})")
    post.publish_video(no)
    # サイトで流す英文の音声(Kokoro)。専用の環境があるときだけ作る
    venv = ROOT / ".venv-tts" / "bin" / "python"
    if venv.exists():
        subprocess.run([str(venv), "tts.py", str(no)], cwd=ROOT, check=True)
    items.append({"no": no, "at": at})
    save_schedule(items)
    audio = ROOT / "docs" / "audio" / f"q{no}.mp3"
    push([str(SCHEDULE)] + ([str(audio)] if audio.exists() else []), f"{no} を {at} に予約")
    print(f"✓ {no} を {at} に予約しました({theme(no)})")


def theme(no):
    return {2: "緑", 0: "ピンク", 1: "青"}[no % 3]


def remove(no):
    save_schedule([s for s in load(SCHEDULE) if s["no"] != no])
    push([str(SCHEDULE)], f"{no} の予約を取り消し")
    print(f"✓ {no} の予約を取り消しました")


def show():
    done = {p["no"]: p for p in load(post.LOG)}
    for s in load(SCHEDULE):
        mark = "投稿済み" if s["no"] in done else "予約中"
        print(f"{s['no']:>4} {theme(s['no'])}  {s['at']}  {mark}")


def run():
    if os.environ.get("CI"):
        post.git("config", "user.name", "github-actions[bot]")
        post.git("config", "user.email", "41898299+github-actions[bot]@users.noreply.github.com")
    done = posted_nos()
    now = datetime.now(post.JST)
    due = [s for s in load(SCHEDULE) if s["no"] not in done and parse_at(s["at"]) <= now]
    if not due:
        print("時間になった予約はありません")
        return
    item = min(due, key=lambda s: s["no"])
    # 前の番号が未投稿なら止める(色のローテーションを守るため)
    if done and item["no"] != max(done) + 1:
        sys.exit(f"{item['no']} の前に {max(done) + 1} が投稿されていません。予約を確認してください")
    print(f"▶ {item['no']}({item['at']} 予約)を投稿します")
    post.load_env()
    post.post(quiz(item["no"]))
    subprocess.run([sys.executable, "build_site.py"], cwd=ROOT, check=True)
    push([str(post.LOG), "docs/data.js"], f"{item['no']} を投稿")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "add":
        post.load_env()
        add(int(sys.argv[2]), sys.argv[3])
    elif cmd == "remove":
        remove(int(sys.argv[2]))
    elif cmd == "run":
        run()
    else:
        show()


if __name__ == "__main__":
    main()
