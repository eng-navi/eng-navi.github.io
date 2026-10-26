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


def sale_check(now):
    """サイトのセール文言(docs/recommend.js の SALES)が古くなっていないか確かめる"""
    import re
    js = (ROOT / "docs" / "recommend.js").read_text()
    m = re.search(r"window\.SALES = \{(.*?)\n\};", js, re.S)
    stale = []
    for key, text, until, checked in re.findall(r'(\w+): \{ text: "([^"]+)", until: "([\d-]+)", checked: "([\d-]+)" \}', m.group(1) if m else ""):
        u = datetime.strptime(until, "%Y-%m-%d").replace(tzinfo=JST)
        c = datetime.strptime(checked, "%Y-%m-%d").replace(tzinfo=JST)
        if u < now:
            stale.append(f"- {key}「{text}」:{until} で終了(サイトでは自動で非表示。SALES から消してOK)")
        elif (now - c).days >= 3:
            stale.append(f"- {key}「{text}」:最終確認 {checked}。まだセール中か Amazon で確認してください")
    label = "セール確認"
    subprocess.run(["gh", "label", "create", label, "--color", "FBCA04", "--force"], cwd=ROOT, capture_output=True)
    open_issues = json.loads(gh("issue", "list", "--label", label, "--state", "open", "--json", "number"))
    if not stale:
        for i in open_issues:
            gh("issue", "close", str(i["number"]), "--comment", "セール情報は最新です。")
        return
    print("\n".join(stale))
    body = ("🏷 サイトの「今だけ◯%OFF」の吹き出しを確認してください。\n\n" + "\n".join(stale) +
            "\n\nClaude Code に「セール確認したよ、〇〇はまだ半額/終わってた」と伝えれば更新します。")
    if open_issues:
        gh("issue", "comment", str(open_issues[0]["number"]), "--body", body)
    else:
        gh("issue", "create", "--title", "🏷 セール情報の確認をお願いします", "--label", label, "--body", body)


def main():
    schedule = json.loads((ROOT / "schedule.json").read_text())
    posted = {p["no"] for p in json.loads((ROOT / "posted.json").read_text())}
    left = [s for s in schedule if s["no"] not in posted]
    now = datetime.now(JST)
    sale_check(now)
    if left:
        last = max(datetime.strptime(s["at"], "%Y-%m-%d %H:%M").replace(tzinfo=JST) for s in left)
        days = (last - now).total_seconds() / 86400
    else:
        last, days = None, -1
    print(f"未投稿の予約 {len(left)} 件 / 残り {days:.1f} 日")

    # Threads(4コマ・10選・投票クイズ)の予約も、種類ごとに残りを確かめる
    notes = []
    tq, tl = ROOT / "threads_queue.json", ROOT / "threads_queue_posted.json"
    if tq.exists():
        tdone = json.loads(tl.read_text()) if tl.exists() else {}
        kinds = {"carousel": "4コマ", "list": "10選", "poll": "投票クイズ", "quiz": "投票クイズ"}
        last_by = {}
        for it in json.loads(tq.read_text()):
            if it["key"] in tdone or it["type"] not in kinds:
                continue
            at = datetime.strptime(it["at"], "%Y-%m-%d %H:%M").replace(tzinfo=JST)
            k = kinds[it["type"]]
            last_by[k] = max(last_by.get(k, at), at)
        for k in ("4コマ", "10選", "投票クイズ"):
            d2 = (last_by[k] - now).total_seconds() / 86400 if k in last_by else -1
            if d2 <= THRESHOLD_DAYS:
                notes.append(f"- Threads の{k}:" + ("予約がありません" if d2 < 0 else f"あと {d2:.1f} 日"))
    if notes:
        print("\n".join(notes))
        days = min(days, THRESHOLD_DAYS)  # Threads 側が少ないときもお知らせを出す

    subprocess.run(["gh", "label", "create", LABEL, "--color", "D93F0B", "--force"], cwd=ROOT, capture_output=True)
    open_issues = json.loads(gh("issue", "list", "--label", LABEL, "--state", "open", "--json", "number"))

    if days > THRESHOLD_DAYS:
        for i in open_issues:
            gh("issue", "close", str(i["number"]), "--comment", f"予約が補充されました(残り {days:.0f} 日)。")
        return

    head = "予約がありません。投稿が止まっています。" if last is None else f"予約はあと {max(days, 0):.1f} 日({last:%m/%d %H:%M} まで)です。"
    body = (f"📸 {head}\n" + ("\n".join(notes) + "\n" if notes else "") + "\n"
            "次の週の本のスクショ(Scramble と IDIOMATIC 300、合わせて10ページほど)を `~/insta-quiz/source/` に入れて、"
            "Claude Code に「次の週の問題を作って」と伝えてください。"
            "4コマ・10選の材料は、セットフレーズ1000 やキクフレを離れたページから10見開きほど。\n\n予約が補充されると、このお知らせは自動で閉じます。")
    if open_issues:
        gh("issue", "comment", str(open_issues[0]["number"]), "--body", body)
    else:
        gh("issue", "create", "--title", f"📸 予約が少なくなっています(あと {max(days, 0):.0f} 日)", "--label", LABEL, "--body", body)


if __name__ == "__main__":
    main()
