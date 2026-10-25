"""Threads に投票クイズを出し、数時間後に答えを返信で付ける。

    python3 threads.py poll 103 [--dry-run]   # 103番を投票クイズとして投稿
    python3 threads.py answer [--dry-run]     # 投稿から ANSWER_AFTER 時間たったクイズに、答えと正答率を返信
    python3 threads.py refresh-token          # トークンを延長(60日)

投稿の記録は threads_posted.json。問題は quizzes.json の2択(options のあるもの)を流用する。
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent
LOG = ROOT / "threads_posted.json"
API = "https://graph.threads.net/v1.0"
JST = timezone(timedelta(hours=9))
ANSWER_AFTER = timedelta(hours=4)
TOPIC = "英語学習"
SERIES = {2: "🟩英検2級", 0: "🩷イディオム", 1: "🟦TOEIC"}
LETTERS = "abcd"
CIRCLED = "①②③④"


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def api(method, path, **params):
    params["access_token"] = os.environ["THREADS_ACCESS_TOKEN"]
    data = urllib.parse.urlencode(params)
    url = f"{API}/{path}"
    req = urllib.request.Request(url + ("?" + data if method == "GET" else ""),
                                 data=None if method == "GET" else data.encode(), method=method)
    try:
        with urllib.request.urlopen(req) as res:
            return json.load(res)
    except urllib.error.HTTPError as e:
        sys.exit(f"Threads API エラー: {e.read().decode()[:300]}")


def quiz(no):
    q = next((q for q in json.loads((ROOT / "quizzes.json").read_text()) if q["no"] == no), None)
    if not q or "options" not in q:
        sys.exit(f"{no} は2択の問題ではありません")
    return q


def poll_text(q):
    question = re.sub(r"\(\s*\)", "(　　　)", q["question"])
    return f"{SERIES[q['no'] % 3]}でよく出る英文法\n\n{question}\n\nどっちが入る？👇 答えはあとでこのスレッドに"


def answer_text(q, result):
    right = q["answer"] - 1
    sentence = re.sub(r"\(\s*\)", q["options"][right], q["question"])
    rate = ""
    if result and result.get("total_votes"):
        pct = result.get(f"option_{LETTERS[right]}_votes_percentage") or 0
        rate = f"(正解率 {round(pct * 100) if pct <= 1 else round(pct)}%・{result['total_votes']}票)\n"
    # 解説は最初の段落と最後の一文だけ(長くしすぎない)
    paras = [p for p in q["explanation"].split("\n\n") if p.strip()]
    exp = paras[0] if len(paras) == 1 else paras[0] + "\n" + paras[-1]
    return f"正解は {CIRCLED[right]} {q['options'][right]}\n{rate}\n{sentence}\n{q['translation']}\n\n{exp}"[:490]


def load_log():
    return json.loads(LOG.read_text()) if LOG.exists() else []


def publish(text, **extra):
    user = os.environ["THREADS_USER_ID"]
    cid = api("POST", f"{user}/threads", media_type="TEXT", text=text, **extra)["id"]
    time.sleep(3)  # 公式の推奨:作成から公開まで少し待つ
    return api("POST", f"{user}/threads_publish", creation_id=cid)["id"]


def poll(no, dry):
    q = quiz(no)
    opts = {f"option_{LETTERS[i]}": o for i, o in enumerate(q["options"])}
    text = poll_text(q)
    if dry:
        print(text, "\n", opts)
        return
    mid = publish(text, poll_attachment=json.dumps(opts), topic_tag=TOPIC)
    link = api("GET", mid, fields="permalink").get("permalink")
    log = load_log()
    log.append({"no": no, "media_id": mid, "permalink": link, "posted_at": datetime.now(JST).isoformat(timespec="seconds")})
    LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
    print(f"✓ 投票クイズ {no} を投稿 {link}")


def answer(dry):
    log = load_log()
    now = datetime.now(JST)
    for item in log:
        if item.get("answered") or now - datetime.fromisoformat(item["posted_at"]) < ANSWER_AFTER:
            continue
        q = quiz(item["no"])
        fields = "poll_attachment{total_votes," + ",".join(f"option_{c}_votes_percentage" for c in LETTERS[:len(q["options"])]) + "}"
        result = api("GET", item["media_id"], fields=fields).get("poll_attachment")
        text = answer_text(q, result)
        if dry:
            print(text)
            continue
        publish(text, reply_to_id=item["media_id"])
        item["answered"] = now.isoformat(timespec="seconds")
        print(f"✓ {item['no']} に答えを返信")
    if not dry:
        LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")


def refresh_token():
    res = api("GET", "refresh_access_token", grant_type="th_refresh_token")
    out = os.environ.get("TOKEN_OUT")
    if out:
        Path(out).write_text(res["access_token"])
    else:
        env = ROOT / ".env"
        lines = [l for l in env.read_text().splitlines() if not l.startswith("THREADS_ACCESS_TOKEN=")]
        env.write_text("\n".join(lines + [f"THREADS_ACCESS_TOKEN={res['access_token']}"]) + "\n")
    print(f"✓ Threads のトークンを更新しました(残り {res['expires_in'] // 86400} 日)")


def main():
    load_env()
    dry = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args[:1] == ["poll"]:
        poll(int(args[1]), dry)
    elif args[:1] == ["answer"]:
        answer(dry)
    elif args[:1] == ["refresh-token"]:
        refresh_token()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
