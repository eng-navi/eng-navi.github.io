"""Threads の予約投稿(予約表 threads_queue.json、日時は日本時間)。投稿の仕組みは threads.py を使う。

    python3 threads_queue.py list            # 予約と投稿済みの一覧
    python3 threads_queue.py preview <key>   # 投稿内容を表示(投稿しない)
    python3 threads_queue.py run             # 時間になった予約を投稿

type
    quiz  : quizzes.json の2択を投票クイズに(no)。答えはツリーの返信で続けて出す(threads.py と同じ)
    poll  : オリジナルの投票クイズ(text, options, answer_text)。答えはツリーの返信で続けて出す
    list  : 10選のツリー(list_id → threads_lists.json)。1/3 一覧 → 2/3・3/3 例文 + 音声ページのリンク
    image : 画像つき投稿(text, image = docs/ からのパス)
    carousel : 画像を複数枚まとめた投稿(text, images = docs/ からのパスのリスト, reply = 任意の返信)
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import threads as th

ROOT = Path(__file__).parent
QUEUE = ROOT / "threads_queue.json"
LOG = ROOT / "threads_queue_posted.json"
LISTS = ROOT / "threads_lists.json"
SITE_URL = "https://eng-navi.github.io"
LIMIT = 500
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"


def list_posts(list_id):
    """一覧(絵文字つき)→ 例文の返信(500文字ごとに分ける)→ 締めと音声ページのリンク。"""
    lst = next(l for l in json.loads(LISTS.read_text()) if l["id"] == list_id)
    items = lst["items"]
    mark = lambda i: items[i][4] if len(items[i]) > 4 else CIRCLED[i]
    if lst.get("reveal"):  # 「知らないとまずい」型:最初は単語だけ見せ、意味はツリーで
        head = f"{lst['hook']}\n\n" + "\n".join(f"{mark(i)} {it[0]}" for i, it in enumerate(items)) + "\n\n意味、ぜんぶわかる?答えはツリーへ👇"
        blocks = [f"{mark(i)} {it[0]} = {it[1]}\n{it[2]}\n({it[3]})" for i, it in enumerate(items)]
        cur = "答え合わせ✅"
    else:
        head = (f"{lst['hook']}\n\n" if lst.get("hook") else "") + f"【{lst['title']}】\n\n" + \
            "\n".join(f"{mark(i)} {it[0]} = {it[1]}" for i, it in enumerate(items))
        blocks = [f"{mark(i)} {it[0]}\n{it[2]}\n({it[3]})" for i, it in enumerate(items)]
        cur = "例文で覚えよう✍️"
    posts = []
    for b in blocks:
        if len(cur) + len(b) + 2 > LIMIT:
            posts.append(cur)
            cur = b
        else:
            cur += "\n\n" + b
    link = f"{SITE_URL}/list/{list_id}/?utm_source=threads&utm_medium=social"
    tail = f"{lst['closing']}\n🔊 音声つきで聞けます → {link}"
    posts += [cur + "\n\n" + tail] if len(cur) + len(tail) + 2 <= LIMIT else [cur, tail]
    return [head] + posts


def render(item):
    t = item["type"]
    if t == "list":
        return list_posts(item["list_id"])
    if t == "quiz":
        q = th.quiz(item["no"])
        return [th.poll_text(q), th.answer_text(q, None)]
    if t == "poll":
        return [item["text"], item["answer_text"]]
    return [item["text"]]


def publish(text, reply_to=None, **extra):
    assert len(text) <= LIMIT, f"{len(text)}文字(上限{LIMIT}): {text[:30]}…"
    if reply_to:
        extra["reply_to_id"] = reply_to
    else:
        extra["topic_tag"] = th.TOPIC
    return th.publish(text, **extra)


def post(item, log):
    t, texts = item["type"], render(item)
    if t in ("quiz", "poll"):
        options = th.quiz(item["no"])["options"] if t == "quiz" else item["options"]
        opts = {f"option_{'abcd'[i]}": o for i, o in enumerate(options)}
        ids = [publish(texts[0], poll_attachment=json.dumps(opts, ensure_ascii=False))]
        time.sleep(5)
        ids.append(publish(texts[1], reply_to=ids[0]))
    elif t == "carousel":  # 画像を複数枚まとめた投稿(4コマ+解説など)
        user = th.os.environ["THREADS_USER_ID"]
        children = []
        for path in item["images"]:
            cid = th.api("POST", f"{user}/threads", media_type="IMAGE", image_url=f"{SITE_URL}/{path}", is_carousel_item="true")["id"]
            for _ in range(24):
                if th.api("GET", cid, fields="status").get("status") == "FINISHED":
                    break
                time.sleep(5)
            children.append(cid)
        cid = th.api("POST", f"{user}/threads", media_type="CAROUSEL", children=",".join(children),
                     text=texts[0], topic_tag=th.TOPIC)["id"]
        for _ in range(24):
            if th.api("GET", cid, fields="status").get("status") == "FINISHED":
                break
            time.sleep(5)
        ids = [th.api("POST", f"{user}/threads_publish", creation_id=cid)["id"]]
        if item.get("reply"):
            time.sleep(5)
            ids.append(publish(item["reply"], reply_to=ids[0]))
    elif t == "image":
        user = th.os.environ["THREADS_USER_ID"]
        cid = th.api("POST", f"{user}/threads", media_type="IMAGE", image_url=f"{SITE_URL}/{item['image']}",
                     text=texts[0], topic_tag=th.TOPIC)["id"]
        for _ in range(24):  # 画像の取り込みが終わるまで待つ
            if th.api("GET", cid, fields="status").get("status") == "FINISHED":
                break
            time.sleep(5)
        ids = [th.api("POST", f"{user}/threads_publish", creation_id=cid)["id"]]
    else:  # list:返信をつなげてツリーにする
        ids = [publish(texts[0])]
        for text in texts[1:]:
            time.sleep(5)
            ids.append(publish(text, reply_to=ids[-1]))
    link = th.api("GET", ids[0], fields="permalink").get("permalink")
    log[item["key"]] = {"ids": ids, "permalink": link, "posted_at": datetime.now(th.JST).isoformat(timespec="seconds")}
    LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
    print(f"✓ {item['key']}({t}) {link}")


def main():
    th.load_env()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    queue = sorted(json.loads(QUEUE.read_text()), key=lambda i: i["at"])
    log = json.loads(LOG.read_text()) if LOG.exists() else {}
    if cmd == "preview":
        item = next(i for i in queue if i["key"] == sys.argv[2])
        for n, text in enumerate(render(item), 1):
            print(f"--- {n}({len(text)}文字)\n{text}\n")
        if item["type"] == "poll":
            print("[投票]", " / ".join(item["options"]))
    elif cmd == "run":
        now = datetime.now(th.JST)
        for item in queue:
            due = datetime.strptime(item["at"], "%Y-%m-%d %H:%M").replace(tzinfo=th.JST) <= now
            if due and item["key"] not in log:
                post(item, log)
    else:
        for item in queue:
            print(f"{item['at']}  {item['key']:<14} {item['type']:<6} {'投稿済み' if item['key'] in log else '予約中'}")


if __name__ == "__main__":
    main()
