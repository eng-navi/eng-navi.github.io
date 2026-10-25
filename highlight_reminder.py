"""ハイライトへの追加忘れを防ぐリマインド(GitHub Actions が毎日21:00に実行)。

その日にストーリーを投稿していたら、Issue「ハイライトに追加」にコメントする。
Issue は本人が追加し終えたら閉じる。閉じずにたまっていくと、未追加の日数を太字で知らせる。
"""
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent
JST = timezone(timedelta(hours=9))
LABEL = "ハイライト追加"


def gh(*args):
    return subprocess.run(["gh", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def main():
    log = json.loads((ROOT / "stories_posted.json").read_text()) if (ROOT / "stories_posted.json").exists() else {}
    today = datetime.now(JST).date().isoformat()
    keys = [k for k, v in log.items() if v["posted_at"].startswith(today)]
    if not keys:
        print("今日のストーリーはなし")
        return
    lists = {l["id"]: l for l in json.loads((ROOT / "threads_lists.json").read_text())}
    names = []
    for k in keys:
        lid, n = map(int, k.split("_"))
        names.append(lists[lid]["items"][n - 1][0])
    subprocess.run(["gh", "label", "create", LABEL, "--color", "C83430", "--force"], cwd=ROOT, capture_output=True)
    issues = json.loads(gh("issue", "list", "--label", LABEL, "--state", "open", "--json", "number,comments"))
    body = (f"📌 今日({today})のストーリー {len(keys)}問を、ハイライト「フレーズ」に追加してください\n\n"
            + "\n".join(f"- {x}" for x in names)
            + "\n\nストーリーは24時間で消えるので、今日中がおすすめです。追加し終えたら、この Issue を閉じてください。")
    if issues:
        days = len(issues[0]["comments"]) + 2
        gh("issue", "comment", str(issues[0]["number"]), "--body", f"**⚠️ 未追加が {days} 日分たまっています**\n\n" + body)
    else:
        gh("issue", "create", "--title", "📌 ストーリーをハイライトに追加", "--label", LABEL, "--body", body)


if __name__ == "__main__":
    main()
