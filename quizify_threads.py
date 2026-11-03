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


# ---- 投稿の見た目(2026/11/2〜):前に伸びた型(帯+罫線+「これ解ける❓」+「正解はこちら👇👇」)にそろえる ----
BAR = "━━━━━━━━━━━━━━━━━━"


def banner(label, ask, body):
    return f"▂▅▇　{label}　▇▅▂\n\n━━━━＼ {ask} ／━━━━━━\n{body}\n{BAR}\n\n正解はこちら👇👇"


def fill_black(it, pool):
    """黒の例文の単語を( )にして、①② の2択。pool は ほかの単語(活用形)の候補"""
    stem = it["word"].lower()[:5]
    toks = it["en"].split()
    for i, t in enumerate(toks):
        core = re.sub(r"[^A-Za-z]", "", t)
        if core.lower().startswith(stem):
            wrong = random.Random(it["word"]).choice([p for p in pool if p.lower()[:4] != core.lower()[:4]])
            q = " ".join(toks[:i] + [t.replace(core, "(　　)")] + toks[i + 1:])
            opts = [core, wrong] if random.Random(it["en"]).random() < 0.5 else [wrong, core]
            return q, core, opts
    return None


def answer_reply(ans_line, en, ja, gloss, kind):
    return f"✅ 正解:{ans_line}\n\n{en}\n({ja})\n\n{gloss}\n\n音声つきで復習するなら🔊\n{link(kind)}"


QUOTES = [
    ("Imagination is more important than knowledge.", "Albert Einstein", "imagination:想像力", "想像力は知識よりも大切だ。"),
    ("Stay hungry, stay foolish.", "Steve Jobs", "foolish:愚かな、ばかげた", "ハングリーであれ。愚か者であれ。"),
    ("The unexamined life is not worth living.", "Socrates", "unexamined:吟味されていない\nbe worth ~ing:〜する価値がある", "吟味されない人生は、生きる価値がない。"),
    ("That which does not kill us makes us stronger.", "Friedrich Nietzsche", "that which ~:〜するもの", "私たちを殺さないものは、私たちをより強くする。"),
    ("Genius is one percent inspiration and ninety-nine percent perspiration.", "Thomas Edison", "inspiration:ひらめき\nperspiration:汗、努力", "天才とは1%のひらめきと99%の努力である。"),
    ("The best way to predict the future is to invent it.", "Alan Kay", "predict:予測する\ninvent:発明する、生み出す", "未来を予測する最善の方法は、それを発明することだ。"),
    ("Life is what happens to you while you're busy making other plans.", "John Lennon", "be busy ~ing:〜するのに忙しい", "人生とは、ほかの計画を立てるのに忙しいあいだに起こるものだ。"),
    ("The only thing we have to fear is fear itself.", "Franklin D. Roosevelt", "fear:恐れる、恐怖\nitself:それ自体", "私たちが恐れるべき唯一のものは、恐怖そのものだ。"),
    ("Not everything that is faced can be changed, but nothing can be changed until it is faced.", "James Baldwin", "face:向き合う", "向き合ったものすべてが変えられるわけではない。しかし、向き合うまでは何も変えられない。"),
    ("Education is the most powerful weapon which you can use to change the world.", "Nelson Mandela", "weapon:武器\npowerful:強力な", "教育は、世界を変えるために使える最も強力な武器だ。"),
    ("We are what we repeatedly do.", "Will Durant", "repeatedly:くり返し", "私たちは、くり返し行うことの積み重ねでできている。"),
    ("Knowledge is power.", "Francis Bacon", "knowledge:知識", "知識は力なり。"),
    ("The journey of a thousand miles begins with one step.", "Lao Tzu(老子)", "journey:旅\na thousand miles:千マイル", "千里の道も一歩から。"),
    ("I think, therefore I am.", "René Descartes", "therefore:それゆえに", "我思う、ゆえに我あり。"),
]


def quote_post(idx):
    en, who, gloss, ja = QUOTES[idx % len(QUOTES)]
    head = banner("英検準1級でよく出る↓", "これ読める❓", f"{en}\n——— {who}")
    reply = f"✅ 訳\n{ja}\n\n{gloss}\n\n英検準1級の単語を、音声つきで🔊\n{link('black')}"
    return [(head, {}), reply]


def phrase_post(idx):
    """Threads の5選から1つ:日本語 → 英語(ひとこと)"""
    lists = json.loads((ROOT / "threads_lists.json").read_text())
    items = [it for l in lists if "TOEIC" not in l["title"] and not l.get("reveal") for it in l["items"]]
    it = items[(idx * 7) % len(items)]
    head = banner("ネイティブがよく使う↓", "英語で言える❓", f"「{it[1]}」\n\nヒント:{it[0][0]}…")
    reply = f"✅ 正解:{it[0]}\n\n{it[2]}\n({it[3]})\n\nほかのフレーズも音声つきで🔊\n{SITE}/list/?utm_source=threads&utm_medium=social&utm_campaign=quizify"
    return [(head, {}), reply]


def posts(key, items):
    """Instagram に出た回 → [(本文, 追加パラメータ), 返信]"""
    kind = key.split("_")[0]
    if kind == "listening":
        a = items[0]
        head = banner("TOEIC・英検リスニング↓", "聞き取れる❓", f"1回だけ聞いて、正しい訳はどっち?\n\n① {a['a']}\n② {a['b']}")
        reply = answer_reply("①" if a["ans"] == "A" else "②", a["en"], a["a"] if a["ans"] == "A" else a["b"], "2問目(長めの会話)は、サイトで解けます", kind)
        return [(head, {"video": items[0].get("_video")}), reply]
    if kind == "white":
        it = items[0]
        b = blank(it["word"])
        if b and it.get("en"):
            q, ans, wrong = b
            sent = re.sub(rf"\b{ans}\b", "(　　)", it["en"], count=1)
            opts = [ans, wrong] if random.Random(it.get("no") or it["word"]).random() < 0.5 else [wrong, ans]
            head = banner("英検2級でよく出る↓", "これ解ける❓", f"{sent}\n\n① {opts[0]}　　② {opts[1]}")
            return [(head, {}), answer_reply(f"{'①' if opts[0] == ans else '②'} {ans}", it["en"], it["ja"], f"{it['word']}:{it['mean']}", kind)]
    if kind == "black":
        pool = [re.sub(r"[^A-Za-z]", "", t) for x in items for t in x["en"].split() if re.sub(r"[^A-Za-z]", "", t).lower()[:5] == x["word"][:5]]
        it = items[0]
        f = fill_black(it, pool or [items[-1]["word"]])
        if f:
            q, ans, opts = f
            head = banner("英検準1級でよく出る↓", "これ解ける❓", f"{q}\n\n① {opts[0]}　　② {opts[1]}")
            return [(head, {}), answer_reply(f"{'①' if opts[0] == ans else '②'} {ans}", it["en"], it["ja"], f"{it['word']}:{it['mean']}", kind)]
    it = items[0]
    head = banner("英検でよく出る↓", "英語で言える❓", f"「{it['ja']}」\n\nヒント:{it['word']}")
    return [(head, {}), answer_reply(it["word"], it["en"], it["ja"], f"{it['word']}:{it['mean']}", kind)]


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
    kind, idx = item["kind"], item["idx"]
    if kind.startswith("list5_"):
        return list5_posts(kind[6:], idx)
    if kind == "quote":
        return quote_post(idx)
    if kind == "phrase":
        return phrase_post(idx)
    src = "black" if kind == "fill_black" else "white"
    data = json.loads(DATA.read_text())  # 読み取りミスのない今の回を先に、そのあと過去の投稿
    its = [x for k, v in data.items() if k.startswith(src) for x in v]
    its += [x for x in archive_items(src) if x.get("en") and "  " not in x["en"] and not re.search(r"[a-z]'[a-z]{2,}we|don'tw", x["en"])]
    it = its[idx % len(its)]
    return posts(f"{src}_x", [it] + [x for x in its if x is not it][:6])


# ---- 5選(2026/11/3〜):eng_navi で伸びている型を、試験・レベル別の中身で ----
EMO = ["🔥", "💡", "📌", "✨", "🎯", "🧠", "📚", "⚡", "🌟", "✅"]
LIST_TITLES = {
    "black": [("英検準1級によく出る単語5選", "知ってたら一気に読める、準1級の頻出語📕"),
              ("「知ってるけど言えない」準1級の単語5選", "読めても、英作文で出てこない単語たち🧠"),
              ("長文で差がつく 準1級の単語5選", "ここが読めると、長文がスラスラ📖"),
              ("ニュースによく出る 準1級の単語5選", "英字ニュースでよく見るやつ📰")],
    "white": [("前置詞までセットで覚える熟語5選", "英検2級・共通テストで問われる形📗"),
              ("入試の並べかえで出る 熟語5選", "この形、そのまま覚えると強い✍️"),
              ("英検2級で差がつく 熟語5選", "前置詞をまちがえやすいもの中心に🎯")],
    "listening": [("TOEIC Part 3・4 によく出る表現5選", "会話・説明文でよく聞く表現🎧"),
                  ("TOEICリスニングで聞き取りたい表現5選", "聞こえた瞬間わかると、スコアが上がる📈"),
                  ("ビジネス英語でそのまま使える表現5選", "TOEICにも仕事にも効く💼")],
}


def pool(src):
    data = json.loads(DATA.read_text())
    if src == "listening":
        seen, out = set(), []
        for k, v in data.items():
            if not k.startswith("listening"):
                continue
            for it in v:
                for w in it["words"]:
                    en, ja = w.split("：", 1)
                    if en.lower() not in seen and len(en) <= 30 and len(en.split()) >= 2:  # 1語だけのものは5選に向かないので外す
                        seen.add(en.lower())
                        ex = next((m.strip() for m in re.findall(r"[^.?!]+[.?!]", it["en"]) if en.split()[0].lower() in m.lower()), "")
                        out.append(dict(word=en, mean=ja, en=ex[:120], ja=""))
        return out
    its = [x for k, v in data.items() if k.startswith(src) for x in v]
    its += [x for x in archive_items(src) if x.get("mean") and len(x["mean"]) <= 24 and (not x.get("en") or not re.search(r"don'tw|  ", x["en"]))]
    seen, out = set(), []
    for x in its:
        if x["word"].lower() not in seen:
            seen.add(x["word"].lower())
            out.append(x)
    return out


def list5_posts(src, idx):
    p = pool(src)
    items = [p[(idx * 5 + i) % len(p)] for i in range(5)]
    title, hook = LIST_TITLES[src][idx % len(LIST_TITLES[src])]
    emo = EMO[idx % 5: idx % 5 + 5]
    head = f"{hook}\n\n【{title}】\n\n" + "\n".join(f"{emo[i]} {it['word']} = {it['mean'][:20]}" for i, it in enumerate(items))
    used, blocks = set(), []
    for i, it in enumerate(items):  # 同じ例文は1回だけ
        if it.get("en") and it["en"] not in used:
            used.add(it["en"])
            blocks.append(f"{emo[i]} {it['word']}\n{it['en']}" + (f"\n({it['ja']})" if it.get("ja") else ""))
    reply = ("例文で覚えよう✍️\n\n" + "\n\n".join(blocks) if blocks else "保存して、すきま時間に見返してね📌")
    tail = f"\n\n音声つきで復習するなら🔊\n{link(src)}"
    if len(reply) + len(tail) > 500:
        reply = reply[: 500 - len(tail) - 1].rsplit("\n\n", 1)[0]
    return [(head, {}), reply + tail]


def post_extra(item):
    (head, extra), reply = extra_posts(item)
    assert len(head) <= 500 and len(reply) <= 500, item
    mid = th.publish(head, topic_tag=th.TOPIC, **{k: v for k, v in extra.items() if k != "video"})
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
