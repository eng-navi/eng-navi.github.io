"""@quizify_english の Threads。Instagram に投稿した回を、30分後に Threads 向けの形で投稿する(予約表はいらない)。

    python3 quizify_threads.py run          # 時間になった回を投稿(GitHub Actions が15分おきに実行)
    python3 quizify_threads.py show black_280   # 投稿する文の確認だけ

・青(リスニング):動画+「A・B どっち?」→ 答えはツリーの返信で
・白:前置詞などを2択の投票に(作れない表現は、日本語→英語の形)→ 答えはツリーで
・黒:「この日本語、英語で言える?」→ 答えはツリーで
答えの返信の最後に、サイトの復習ページへのリンクをつける。データは quizify_site_data.json(build_quizify_site.py が作る)
"""
import json
import os
import random
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import threads as th

ROOT = Path(__file__).parent
DATA = ROOT / "quizify_site_data.json"
IG_LOG = ROOT / "quizify_posted.json"
LOG = ROOT / "quizify_threads_posted.json"
SITE = "https://eng-navi.github.io"
START = "2026-11-02"  # この日以降に Instagram に出た回から
DELAY = timedelta(minutes=30)
PREPS = ["in", "on", "to", "with", "for", "of", "about", "from", "at", "into"]
PAGE = {"black": "tango-advanced", "white": "tango", "listening": "listening"}


def use_account():
    th.load_env()
    os.environ["THREADS_USER_ID"] = os.environ["QUIZIFY_THREADS_USER_ID"]
    os.environ["THREADS_ACCESS_TOKEN"] = os.environ["QUIZIFY_THREADS_ACCESS_TOKEN"]


def link(kind):
    return f"{SITE}/{PAGE[kind]}/?utm_source=threads&utm_medium=social&utm_campaign=quizify"


def blank(word):
    """be involved in A → ('be involved ( ) A', 'in', 'on')。前置詞がなければ None"""
    toks = word.split()
    for i, t in enumerate(toks):
        if t in PREPS:
            wrong = random.Random(word).choice([p for p in PREPS[:7] if p != t])
            return " ".join(toks[:i] + ["( )"] + toks[i + 1:]), t, wrong
    return None


def posts(key, items):
    """[(本文, 追加パラメータ), 返信の文]"""
    kind = key.split("_")[0]
    if kind == "listening":
        a = items[0]
        head = (f"🎧 リスニング問題(TOEIC・英検)\n1回だけ聞いて、正しい訳はどっち?\n\n"
                f"A) {a['a']}\nB) {a['b']}\n\n答えはツリーへ👇")
        body = [f"【{it['no']}】 答え:{it['ans']}\n{it['en']}\n({it['a'] if it['ans'] == 'A' else it['b']})" for it in items]
        reply = "✅ 答え合わせ\n\n" + "\n\n".join(body[:1]) + f"\n\n2問目(長めの会話)は、サイトで音声つきで解けます👇\n{link(kind)}"
        return [(head, {"video": items[0].get("_video")}), reply]
    if kind == "white":
        it = items[0]
        b = blank(it["word"])
        if b:
            q, ans, wrong = b
            opts = [ans, wrong] if random.Random(it["no"]).random() < 0.5 else [wrong, ans]
            head = f"📗 英単語クイズ(英検3級〜2級)\n\n「{it['mean']}」を英語で言うと?\n{q}\n\n( )に入るのはどっち?答えはツリーへ👇"
            extra = {"poll_attachment": json.dumps({"option_a": opts[0], "option_b": opts[1]})}
            reply = (f"✅ 正解は {ans}\n\n{it['word']}:{it['mean']}\n{it['en']}\n({it['ja']})"
                     + "".join(f"\n\n{x['word']}:{x['mean']}\n{x['en']}\n({x['ja']})" for x in items[1:])
                     + f"\n\n例文の音声はこちら🔊\n{link(kind)}")
            return [(head, extra), reply]
    # 黒(と前置詞のない白):日本語 → 英語
    label = "📕 瞬間英作文(英検2級〜準1級)" if kind == "black" else "📗 英単語(英検3級〜2級)"
    head = f"{label}\nこの日本語、英語で言える?\n\n" + "\n".join(f"{i + 1}. {it['ja']}({it['word']})" for i, it in enumerate(items)) + "\n\n答えはツリーへ👇"
    reply = "✅ 答え\n\n" + "\n".join(f"{i + 1}. {it['en']}" for i, it in enumerate(items)) + f"\n\n音声つきで復習するなら🔊\n{link(kind)}"
    return [(head, {}), reply]


def publish_video(text, url):
    user = os.environ["THREADS_USER_ID"]
    cid = th.api("POST", f"{user}/threads", media_type="VIDEO", video_url=url, text=text, topic_tag=th.TOPIC)["id"]
    for _ in range(40):  # 動画の処理を待つ
        st = th.api("GET", cid, fields="status").get("status")
        if st == "FINISHED":
            break
        if st == "ERROR":
            raise RuntimeError("Threads の動画処理に失敗")
        time.sleep(10)
    return th.api("POST", f"{user}/threads_publish", creation_id=cid)["id"]


def post(key, data):
    items = [dict(x) for x in data[key]]
    if key.startswith("listening"):
        items[0]["_video"] = f"{SITE}/quizify/{key}.mp4"
    (head, extra), reply = posts(key, items)
    assert len(head) <= 500 and len(reply) <= 500, key
    if extra.get("video"):
        mid = publish_video(head, extra["video"])
    else:
        mid = th.publish(head, topic_tag=th.TOPIC, **{k: v for k, v in extra.items() if k != "video"})
    time.sleep(5)
    th.publish(reply, reply_to_id=mid)
    return th.api("GET", mid, fields="permalink").get("permalink")


# ---- 過去の投稿(アーカイブ)からの追加投稿。予約表 quizify_threads_queue.json ----
QUEUE = ROOT / "quizify_threads_queue.json"
ARCHIVE = ROOT / "quizify_archive.json"


def archive_items(kind):
    d = json.loads(ARCHIVE.read_text())
    return [it for v in sorted(d[kind].values(), key=lambda v: v["date"]) for it in v.get("items", [])]


def extra_posts(item):
    """予約表の1件 {key, at, kind, idx} → [(本文, 追加パラメータ), 返信]"""
    kind, idx = item["kind"], item["idx"]
    its = archive_items(kind)
    if kind == "listening":  # 文字で読む版:英文 → 正しい訳はどっち?
        it = its[idx]
        head = f"📖 この英文の意味はどっち?(TOEIC・英検)\n\n{it['en']}\n\n答えはツリーへ👇"
        opts = {"option_a": "A) " + it["a"][:22], "option_b": "B) " + it["b"][:22]}
        reply = f"✅ 正解は {it['ans']}\n\n{it['en']}\n({it['ja']})\n\n音声つきのリスニング問題はこちら🎧\n{link('listening')}"
        return [(f"{head}\n\nA) {it['a']}\nB) {it['b']}", {"poll_attachment": json.dumps({"option_a": "A", "option_b": "B"})}), reply]
    if kind == "black":  # 単語の意味:2択の投票
        it = its[idx]
        pool = [x for x in its if x.get("mean") and x["mean"] != it.get("mean") and len(x["mean"]) <= 20]
        wrong = random.Random(it["word"]).choice(pool)["mean"]
        right = it["mean"][:24]
        opts = [right, wrong[:24]] if random.Random(idx).random() < 0.5 else [wrong[:24], right]
        head = f"📕 英検準1級の単語、意味わかる?\n\n{it['word']}\n\n答えはツリーへ👇"
        ex = f"\n{it['en']}\n({it['ja']})" if it.get("en") else ""
        reply = f"✅ 正解は「{it['mean']}」\n\n{it['word']}:{it['mean']}{ex}\n\n準1級の単語をもっと🔊\n{link('black')}"
        return [(head, {"poll_attachment": json.dumps({"option_a": opts[0], "option_b": opts[1]})}), reply]
    it = its[idx]  # 白:前置詞の2択(なければ日本語→英語)
    b = blank(it["word"])
    if b and it.get("en"):
        q, ans, wrong = b
        opts = [ans, wrong] if random.Random(idx).random() < 0.5 else [wrong, ans]
        head = f"📗 英単語クイズ(英検3級〜2級)\n\n「{it['mean']}」を英語で言うと?\n{q}\n\n( )に入るのはどっち?答えはツリーへ👇"
        reply = f"✅ 正解は {ans}\n\n{it['word']}:{it['mean']}\n{it['en']}\n({it['ja']})\n\n例文の音声はこちら🔊\n{link('white')}"
        return [(head, {"poll_attachment": json.dumps({"option_a": opts[0], "option_b": opts[1]})}), reply]
    head = f"📗 この日本語、英語で言える?\n\n{it['ja']}\n(ヒント:{it['word']})\n\n答えはツリーへ👇"
    reply = f"✅ 答え\n\n{it['en']}\n\n{it['word']}:{it['mean']}\n\n例文の音声はこちら🔊\n{link('white')}"
    return [(head, {}), reply]


def post_extra(item):
    (head, extra), reply = extra_posts(item)
    assert len(head) <= 500 and len(reply) <= 500, item
    mid = th.publish(head, topic_tag=th.TOPIC, **extra)
    time.sleep(5)
    th.publish(reply, reply_to_id=mid)
    return th.api("GET", mid, fields="permalink").get("permalink")


def run():
    import manga_post as mp
    if os.environ.get("CI"):
        import post as p
        p.git("config", "user.name", "github-actions[bot]")
        p.git("config", "user.email", "41898299+github-actions[bot]@users.noreply.github.com")
    use_account()
    ig = mp.load(IG_LOG, {})
    done = mp.load(LOG, {})
    data = json.loads(DATA.read_text())
    now = datetime.now(th.JST)
    due = sorted((k for k, v in ig.items() if k not in done and k in data and v["posted_at"][:10] >= START
                  and datetime.fromisoformat(v["posted_at"]) + DELAY <= now), key=lambda k: ig[k]["posted_at"])
    if not due:  # Instagram の回がなければ、アーカイブの予約を見る
        q = [x for x in mp.load(QUEUE, []) if x["key"] not in done
             and datetime.strptime(x["at"], "%Y-%m-%d %H:%M").replace(tzinfo=th.JST) <= now]
        if not q:
            print("時間になった quizify の Threads はありません")
            return
        x = min(q, key=lambda x: x["at"])
        done[x["key"]] = {"permalink": post_extra(x), "posted_at": now.isoformat(timespec="seconds")}
        LOG.write_text(json.dumps(done, ensure_ascii=False, indent=2) + "\n")
        print(f"✓ Threads {x['key']} {done[x['key']]['permalink']}")
        mp.push([str(LOG)], "quizify の Threads を投稿")
        return
    k = due[0]  # 1回に1本
    done[k] = {"permalink": post(k, data), "posted_at": now.isoformat(timespec="seconds")}
    LOG.write_text(json.dumps(done, ensure_ascii=False, indent=2) + "\n")
    print(f"✓ Threads {k} {done[k]['permalink']}")
    mp.push([str(LOG)], "quizify の Threads を投稿")


if __name__ == "__main__":
    if sys.argv[1:2] == ["showx"]:
        for x in json.loads(QUEUE.read_text())[: int(sys.argv[2]) if len(sys.argv) > 2 else 3]:
            (h, e), r = extra_posts(x)
            print("=====", x["at"], x["kind"], "\n" + h, e, "\n--- 返信 ---\n" + r)
    elif sys.argv[1:2] == ["show"]:
        data = json.loads(DATA.read_text())
        items = [dict(x) for x in data[sys.argv[2]]]
        (head, extra), reply = posts(sys.argv[2], items)
        print(head, "\n", {k: v for k, v in extra.items()}, "\n----- 返信 -----\n" + reply)
    else:
        run()
