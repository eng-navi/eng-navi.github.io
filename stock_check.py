"""予約の残りが少ないとき、GitHub の Issue でお知らせする(GitHub Actions が毎日実行)。

残り3日以下 → 「予約が少なくなっています」の Issue を作る(既に開いていれば残り日数を追記)
残り4日以上 → 開いているお知らせを閉じる
"""
import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent
JST = timezone(timedelta(hours=9))
LABEL = "予約切れ注意"
THRESHOLD_DAYS = 3


def gh(*args):
    return subprocess.run(["gh", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def main():
    schedule = json.loads((ROOT / "schedule.json").read_text())
    posted = {p["no"] for p in json.loads((ROOT / "posted.json").read_text())}
    left = [s for s in schedule if s["no"] not in posted]
    now = datetime.now(JST)
    if left:
        last = max(datetime.strptime(s["at"], "%Y-%m-%d %H:%M").replace(tzinfo=JST) for s in left)
        days = (last - now).total_seconds() / 86400
    else:
        last, days = None, -1
    print(f"未投稿の予約 {len(left)} 件 / 残り {days:.1f} 日")

    subprocess.run(["gh", "label", "create", LABEL, "--color", "D93F0B", "--force"], cwd=ROOT, capture_output=True)
    open_issues = json.loads(gh("issue", "list", "--label", LABEL, "--state", "open", "--json", "number"))

    if days > THRESHOLD_DAYS:
        for i in open_issues:
            gh("issue", "close", str(i["number"]), "--comment", f"予約が補充されました(残り {days:.0f} 日)。")
        return

    head = "予約がありません。投稿が止まっています。" if last is None else f"予約はあと {max(days, 0):.1f} 日({last:%m/%d %H:%M} まで)です。"
    body = (f"📸 {head}\n\n"
            "次の週の本のスクショ(Scramble と IDIOMATIC 300、合わせて10ページほど)を `~/insta-quiz/source/` に入れて、"
            "Claude Code に「次の週の問題を作って」と伝えてください。\n\n予約が補充されると、このお知らせは自動で閉じます。")
    if open_issues:
        gh("issue", "comment", str(open_issues[0]["number"]), "--body", body)
    else:
        gh("issue", "create", "--title", f"📸 予約が少なくなっています(あと {max(days, 0):.0f} 日)", "--label", LABEL, "--body", body)


if __name__ == "__main__":
    main()
