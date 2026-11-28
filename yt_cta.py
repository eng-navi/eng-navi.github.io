"""YouTube の長い動画の「おすすめ(松竹梅)」と案内(CTA)。まとめ動画を作るたびに必ずこれを通す(2026-11-28 ユーザー指定)。

    python3 yt_cta.py out/yt_compile/theme_tense.txt ...   # 既存の .txt の説明欄を松竹梅の形に書きかえ、固定コメントを足す

決めごと:
- おすすめは3つまで。「こうしたい人はこれ」と、目的別に並べる(松=最短で結果/竹=自分のペースで本/梅=スキマ時間のアプリ)。
  3つで多すぎないかは、yt の数字(/osusume/?from=yt のクリック)を見て2つと比べる。
- 本は Amazon 直リンク。A8 のサービスも直リンク(2026-11-28〜:A8 のメディアに YouTube チャンネルを登録済み・掲載可を確認済み)。
  A8 にないものだけ /osusume/ 経由。
- 案内は「途中(約1/3・2/3)と最後」に画面で「おすすめ教材は説明欄に」。説明欄の最初の2行はサイト。固定コメントでも1回だけ自然に。
- キーワード:大きい語(英語学習・英文法・英会話・TOEIC・英検)と絞った語(その回のテーマ)を、自然な文章で入れる。誇張しない。
"""
import re
import sys

OSU = "https://eng-navi.github.io/osusume/?from=yt"
SITE = "https://eng-navi.github.io/?utm_source=youtube"

# 竹(本)は動画のテーマに合わせて選ぶ。(書名, ひとこと, URL)
BOOKS = {
    "grammar": ("『大学受験 英文法・語法SHORTCUTS』", "よく出る良問254問。全問に正解率つきで、苦手がひと目でわかる", "https://link.amazon/B0bwqM40M"),
    "speaking": ("『英語のハノン 初級』", "わかる文法を、口から出る英語に変えるドリル",
                 "https://www.amazon.co.jp/dp/B09NY53725?tag=mokumoku70e-22&linkCode=ll2&linkId=aaa9fc05b00ffc5bcfd72de9d08bdca0&language=ja_JP&ref_=as_li_ss_tl"),
    "listening": ("『キクフレ』", "TOEICによく出るフレーズを、音声つきで覚えられる", "https://link.amazon/B09qOB6Ou"),
    "vocab": ("『大学入試英単語 OVERSIGHT』", "「見たことはあるのに訳せない」単語をなくす",
              "https://www.amazon.co.jp/dp/B0H2BMN624?tag=mokumoku70e-22&linkCode=ll2&linkId=c9b5d7da796b8d08904c91469500b648&language=ja_JP&ref_=as_li_ss_tl"),
}


# ---------- おすすめの候補(docs/recommend.js の ITEMS から読む。A8=サービス、Amazon=本)----------
# 松=人と一緒に最短で/梅=スキマ時間・アプリやオンライン/竹=テーマに合う本。動画ごとに選び分けて、毎回同じにならないように。
MATSU = {"default": ["progrit", "liberty"], "toeic": ["liberty", "progrit"]}
UME = {"default": ["speak", "torabit", "nativecamp", "sankei"], "toeic": ["studysapuri", "speak", "torabit"],
       "listening": ["audible", "torabit", "studysapuri"], "speaking": ["speak", "nativecamp", "torabit", "sankei"]}
TAKE = {"grammar": ["shortcuts", "scramble", "eureka"], "toeic": ["kikufure", "setphrase"], "listening": ["kikufure"],
        "idiom": ["idiomatic", "setphrase"], "vocab": ["oversight", "pinnacle"], "speaking": ["hanon", "hanon_phrase"],
        "reading": ["reading", "horikoshi", "brushup", "crack10", "classic_basic", "realize"]}
LEAD = {"matsu": "期限までに最短で結果を出したい人", "take": "自分のペースで、問題をしっかり解きたい人", "ume": "スキマ時間に、続けやすい形で練習したい人"}


def items():
    import re as _re
    js = open(__file__.replace("yt_cta.py", "docs/recommend.js"), encoding="utf-8").read()
    out = {}
    for m in _re.finditer(r"^  ([a-z_0-9]+): \{(.*?)\},?\s*$", js, _re.M):
        k, body = m.group(1), m.group(2)
        name = _re.search(r'name: "([^"]+)"', body); note = _re.search(r'note: "([^"]+)"', body)
        if not name or k in out: continue
        url = None
        am = _re.search(r'AMAZON\("([A-Z0-9]+)", "([0-9a-f]+)"\)', body)
        if am:
            url = f"https://www.amazon.co.jp/dp/{am.group(1)}?tag=mokumoku70e-22&linkCode=ll2&linkId={am.group(2)}&language=ja_JP&ref_=as_li_ss_tl"
        else:
            u = _re.search(r'url: "(https://(?:link\.amazon|www\.amazon)[^"]+)"', body)
            url = u.group(1) if u else None
        a8 = _re.search(r'A8\("([0-9A-Z+]+)"', body)
        out[k] = dict(name=name.group(1), note=note.group(1) if note else "", amazon=url, a8="A8(" in body,
                      a8url=f"https://px.a8.net/svt/ejp?a8mat={a8.group(1)}" if a8 else None)
    return out


def deals():
    """キャンペーン(recommend.js の SALES=セール、PERKS=無料体験)。ユーザーがくれた情報は正しいものとして使う。
    YouTube の説明欄・動画の案内を書く前に必ずこれを見る。選んだおすすめにキャンペーンがなければ、公式サイトを見て SALES に足す(確認日つき)。"""
    import re as _re, datetime as _dt
    js = open(__file__.replace("yt_cta.py", "docs/recommend.js"), encoding="utf-8").read()
    out = {}
    sales = js[js.index("window.SALES"):js.index("window.PERKS")]
    for m in _re.finditer(r'^  ([a-z_0-9]+): \{ text: "([^"]+)", until: (null|"[0-9-]+"), checked: "([0-9-]+)"(?:, fine: "([^"]+)")?', sales, _re.M):
        k, text, until, checked, fine = m.groups()
        if until != "null" and until.strip('"') < _dt.date.today().isoformat():
            continue
        mm, dd = checked[5:7].lstrip("0"), checked[8:].lstrip("0")
        out[k] = f"{text}({mm}/{dd}時点{'・' + fine if fine else ''})"
    perks = js[js.index("window.PERKS"):]
    for m in _re.finditer(r'^  ([a-z_0-9]+): \["([^"]+)"', perks, _re.M):
        out.setdefault(m.group(1), m.group(2))
    return out


def pick(pool, seed):
    import hashlib
    return pool[int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(pool)]


def shochikubai(book="grammar", topic="この動画の内容", seed=None, area="default"):
    """説明欄のおすすめ(PR)。目的別に3つ。seed(動画名)ごとに候補から選び分ける。リンクに from=yt_<seed> をつけて比べる"""
    if seed:
        it = items()
        frm = f"https://eng-navi.github.io/osusume/?from={seed if seed.startswith('yt_') else 'yt_' + seed}"
        log = __import__("json")
        lp = __file__.replace("yt_cta.py", "yt_cta_log.json")
        try: d = log.load(open(lp))
        except Exception: d = {}
        # 一度決めた動画はそのまま。新しい動画は、これまでの本数で順番に回す(毎回同じにならないように)
        n = list(d).index(seed) if seed in d else len(d)
        rot = lambda pool, off=0: pool[(n + off) % len(pool)]
        mk = rot(MATSU.get(area, MATSU["default"]))
        tk = rot(TAKE.get(book, TAKE["grammar"]), 1)
        uk = rot(UME.get(area, UME["default"]), 2)
        m, t, u = it[mk], it[tk], it[uk]
        dl = deals()
        tag = lambda k: f"\n🎁 {dl[k]}" if k in dl and dl[k].split("(")[0] not in it[k]["note"] else ""  # 説明と同じなら出さない
        d[seed] = {"matsu": mk, "take": tk, "ume": uk}
        log.dump(d, open(lp, "w"), ensure_ascii=False, indent=1)
        return f"""🎯 {topic}を、目的別にもっと伸ばすなら(PR)

🏆 {LEAD["matsu"]} → {m["name"]}
{m["note"]}{tag(mk)}
→ {m["a8url"] or frm + "#" + mk}

📗 {LEAD["take"]} → 『{t["name"].strip("『』")}』
{t["note"]}
{t["amazon"]}

📱 {LEAD["ume"]} → {u["name"]}
{u["note"]}{tag(uk)}
→ {u["a8url"] or frm + "#" + uk}"""
    b = BOOKS[book]
    return f"""🎯 {topic}を、目的別にもっと伸ばすなら(PR)

🏆 期限までに最短で結果を出したい人 → 英語コーチング PROGRIT
何を・どれだけやるかを一緒に決めて、毎日の学習を管理してくれます。
→ {OSU}#progrit

📗 自分のペースで、問題をしっかり解きたい人 → {b[0]}
{b[1]}
{b[2]}

📱 スキマ時間に、声に出して続けたい人 → AI英会話アプリ スピーク
覚えた英語を、AI相手にすぐ話して練習できます。
→ {OSU}#speak"""


def pinned(topic="この動画の内容"):
    """固定コメント(1つだけ。自然に)"""
    return (f"📌 {topic}の復習用に、全問の答え・解説・音声を無料のサイトにまとめています。\n{SITE}\n"
            "目的別のおすすめ教材(コーチング・問題集・アプリ)は説明欄にあります。")


CTA_CARD = "おすすめ教材は 説明欄に"  # 動画の途中(約1/3・2/3)と最後に出す画面の文言


def rewrite(path, book=None, topic=None):
    """既存の .txt の「🎁 …(PR)」ブロックを松竹梅に置きかえ、固定コメントを足す"""
    s = open(path, encoding="utf-8").read()
    name = path.split("/")[-1]
    book = book or ("listening" if "listening" in name else "vocab" if "vocab" in name else
                    "speaking" if "eng_navi" in name or "idiom" in name else "grammar")
    title = s.split("\n")[1]
    topic = topic or re.sub(r"[|｜【].*", "", re.sub(r"^【[^】]*】", "", title)).strip() or "英文法"
    seed = name.replace(".txt", "")
    area = "listening" if "listening" in name else "toeic" if ("toeic" in name or "TOEIC" in title) else "speaking" if "eng_navi" in name else "default"
    tb = ("idiom" if "idiom" in name else "toeic" if "toeic" in name else "listening" if "listening" in name else
          "speaking" if "eng_navi" in name else "grammar")
    block = shochikubai(tb, topic, seed=seed, area=area)
    s = re.sub(r"\n\n固定コメント\(.*\Z", "\n", s, flags=re.S)  # 作り直すときは固定コメントも入れかえ
    s2 = re.sub(r"(🎁|🎯) [^\n]*\(PR\)\n.*?(?=\n\n▼|\n\nMusic|\Z)", block, s, count=1, flags=re.S)
    if "🎯" not in s and "🎁" not in s:  # おすすめがまだない古い説明欄 → チャプターの前に入れる
        s2 = s.replace("\n▼ チャプター", "\n" + block + "\n\n▼ チャプター", 1)
    if "🎯" not in s2:
        print("× おすすめを入れる場所が見つからない:", path); return
    if "固定コメント" not in s2:
        s2 = s2.rstrip("\n") + f"\n\n固定コメント(投稿後にコメントして「固定」):\n{pinned(topic)}\n"
    s2 = re.sub(r"説明欄(\(\d+字\))?:", "説明欄:", s2, count=1)
    open(path, "w", encoding="utf-8").write(s2)
    print("✓", path)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        rewrite(p)
