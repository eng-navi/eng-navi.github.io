"""YouTube の長い動画の「おすすめ(松竹梅)」と案内(CTA)。まとめ動画を作るたびに必ずこれを通す(2026-11-28 ユーザー指定)。

    python3 yt_cta.py out/yt_compile/theme_tense.txt ...   # 既存の .txt の説明欄を松竹梅の形に書きかえ、固定コメントを足す

決めごと:
- おすすめは3つまで。「こうしたい人はこれ」と、目的別に並べる(松=最短で結果/竹=自分のペースで本/梅=スキマ時間のアプリ)。
  3つで多すぎないかは、yt の数字(/osusume/?from=yt のクリック)を見て2つと比べる。
- 本は Amazon 直リンク、アプリ・サービスは /osusume/ 経由(A8 のリンクは YouTube に直接貼らない)。
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


def shochikubai(book="grammar", topic="この動画の内容"):
    """説明欄のおすすめ(PR)。目的別に3つ"""
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
    block = shochikubai(book, topic)
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
