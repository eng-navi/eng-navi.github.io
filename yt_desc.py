"""YouTube の説明欄を、シリーズごとの型で作って書きかえる(再生回数の多い順に少しずつ)。

    .venv-tts/bin/python yt_desc.py next 20     # まだ書きかえていない上位20本を書きかえる
    .venv-tts/bin/python yt_desc.py preview <動画ID>

- 型:動画の一言 → サイトの案内 → おすすめ(PR)3つ(本は Amazon 直リンク、アプリ・サービスは /osusume/ 経由)→ 再生リストのリンク(元の説明欄にあれば残す)→ ハッシュタグ
- 書きかえた動画は out/yt_desc/done.json に記録。前の説明欄は out/yt_desc/backup/
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DIR = ROOT / "out" / "yt_desc"
DONE = DIR / "done.json"
SITE = "https://eng-navi.github.io/?utm_source=youtube"
OSU = "https://eng-navi.github.io/osusume/?from=yt"
AMZ = lambda asin, lid: f"https://www.amazon.co.jp/dp/{asin}?tag=mokumoku70e-22&linkCode=ll2&linkId={lid}&language=ja_JP&ref_=as_li_ss_tl"

BOOKS = {
    "pinnacle": ("『大学入試 無敵の難単語 PINNACLE 420』", "難しい単語で手が止まる人に。最難関レベルの語彙をまとめて固められます", AMZ("B0CK4HSRZN", "8ecd3ddef08dd6642b8ef647882ce7d7")),
    "kikufure": ("『TOEIC L&Rテスト 聞いて覚える頻出英語フレーズ キクフレ』", "よく出るフレーズを音声つきで。聞いた英語を本で確認したい人に", "https://link.amazon/B09qOB6Ou"),
    "idiomatic": ("『飛躍のフレーズ IDIOMATIC 300』", "よくある言い回しを英文ごと覚えられる。問題300問つき", "https://link.amazon/B0eHBRPkB"),
    "hanon": ("『英語のハノン 初級』", "わかる英語を「口から出る」ところまで落とし込むドリル", AMZ("B09NY53725", "aaa9fc05b00ffc5bcfd72de9d08bdca0")),
    "oversight": ("『大学入試英単語 OVERSIGHT』", "「見たことはあるのに訳せない」単語をクイズ形式で", AMZ("B0H2BMN624", "c9b5d7da796b8d08904c91469500b648")),
    "shortcuts": ("『大学受験 英文法・語法SHORTCUTS』", "よく出る良問だけの254問。全問に正解率つきで、苦手がわかる", "https://link.amazon/B0bwqM40M"),
}
APPS = {
    "speak": ("🗣 アプリ:スピーク(AI英会話)", "聞いた英語を、AI相手に声に出して使う練習に。24時間・予約なしで、1日5分から", "speak"),
    "torabit": ("🗣 アプリ:TORAbit(トラビット)", "シャドーイングと瞬間英作文を、AIの採点つきで1日5分から", "torabit"),
    "studysapuri": ("📱 アプリ:スタディサプリENGLISH TOEIC対策コース", "文法の学び直しからパート別の対策まで、スマホで。無料体験あり", "studysapuri"),
}
BIG = ("🏆 本気で伸ばしたい人へ:PROGRIT(英語コーチング)", "何をどれだけやるかを一緒に決めて、伴走してくれる英語コーチング", "progrit")

# シリーズ:(タイトルに含まれる語, 一言, 本, アプリ, ハッシュタグ)
SERIES = [
    ("英語耳をつくるリスニング", "ネイティブの自然な英語を聞き取る、リスニングのトレーニングです。1回で聞き取れるか試してみてください。", "kikufure", "speak", "#英語リスニング #英語耳 #shorts"),
    ("必勝パターン", "TOEIC によく出る問題の「解き方の型」を、短いクイズで身につけるシリーズです。", "kikufure", "studysapuri", "#TOEIC #TOEIC対策 #shorts"),
    ("英検準1級の英熟語", "英検準1級によく出る英熟語を、ネイティブの例文で1つずつ覚えるシリーズです。", "idiomatic", "speak", "#英検準1級 #英熟語 #shorts"),
    ("よく使う英単語", "ネイティブが日常でよく使う英単語を、聞き流しで覚えるシリーズです。", "hanon", "speak", "#英単語 #聞き流し #shorts"),
    ("瞬間英作文", "日本語を見て、すぐに英語で言う「瞬間英作文」のトレーニングです。声に出して練習してみてください。", "hanon", "torabit", "#瞬間英作文 #英会話 #shorts"),
    ("英検一級", "英検1級レベルの単語を、イギリス英語で聞き流せる動画です。すきま時間に、耳から語彙を増やしましょう。", "pinnacle", "speak", "#英検1級 #英単語 #聞き流し"),
    ("英検1級", "英検1級レベルの単語を、イギリス英語で聞き流せる動画です。すきま時間に、耳から語彙を増やしましょう。", "pinnacle", "speak", "#英検1級 #英単語 #聞き流し"),
    ("TOEIC", "TOEIC によく出る単語・フレーズを、イギリス英語で聞き流せる動画です。", "kikufure", "studysapuri", "#TOEIC #英単語 #聞き流し"),
    ("", "自然なイギリス英語を聞き流して、英語の耳をつくる動画です。作業中や寝る前のBGMにどうぞ。", "kikufure", "speak", "#英語リスニング #聞き流し #イギリス英語"),
]


def series_of(title):
    return next(s for s in SERIES if s[0] in title)


def make(v):
    _, intro, book, app, tags = series_of(v["title"])
    b, a = BOOKS[book], APPS[app]
    m = re.search(r"(\*🍿 WATCH NEXT:\*.*?)(?=\n\s*\n?\*|\Z)", v.get("description", ""), re.S)
    watch = ("\n\n" + m.group(1).strip()) if m else ""
    return (f"{intro}\n\n📚 単語・フレーズの意味と例文は、サイトでクイズにして復習できます(無料・音声つき)\n{SITE}\n\n"
            f"🎁 あわせておすすめ(PR)\n📗 本:{b[0]}\n{b[1]}\n{b[2]}\n\n{a[0]}\n{a[1]}\n→ {OSU}#{a[2]}\n\n"
            f"{BIG[0]}\n{BIG[1]}\n→ {OSU}#{BIG[2]}{watch}\n\n{tags}")


def main():
    import yt_api
    vids = json.loads((DIR / "videos.json").read_text())
    done = json.loads(DONE.read_text()) if DONE.exists() else ["An68yJqgE9U", "tggOVDA9n_Q", "z5LknIGplVY", "MNXDpCCqcy8", "Ft2ANjkB0MU"]
    if sys.argv[1] == "preview":
        print(make(next(v for v in vids if v["id"] == sys.argv[2])))
        return
    n = int(sys.argv[2])
    for v in [v for v in vids if v["id"] not in done][:n]:
        yt_api.update(v["id"], make(v))
        done.append(v["id"])
        DONE.write_text(json.dumps(done, indent=1))
    print(f"書きかえ済み {len(done)} / {len(vids)} 本")


if __name__ == "__main__":
    main()
