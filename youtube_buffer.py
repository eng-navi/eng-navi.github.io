"""インスタに出した動画を、Buffer 経由で YouTube ショートにも出す。

    python3 youtube_buffer.py test <動画URL>   # 非公開で1本試す

- YouTube の公式 API は審査が通るまで動画が非公開に制限されるので、審査済みの Buffer を通す。
- 鍵は BUFFER_API_KEY(.env と GitHub の Secrets)。期限は 2027/11/22(作り直すときは Buffer の Settings → API)。
- 無料プランは予約が10件まで、YouTube は1日2本まで。まとめて予約せず、インスタに出たときに shareNow で送る。
- 失敗してもインスタの投稿は止めない(ログだけ出す)。
"""
import json
import os
import re
import sys
import urllib.request

API = "https://api.buffer.com"
TIKTOK = "6b026f288541f09ecb5e0c42"  # TikTok @quizify_english(名前は quizify だが、中身は eng_navi の動画。緑→ピンク→青のグリッドを守る)
CHANNEL = "6b02693d8541f09ecb5dca6f"  # 英語クイズ | サクサク英会話・瞬間英作文トレ(eng_navi とクイズファイを両方流す)
SITE = "https://eng-navi.github.io/"
MUTATION = """mutation($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess { post { id } }
    ... on MutationError { message }
  }
}"""


def gql(query, variables, key=None):
    req = urllib.request.Request(API, data=json.dumps({"query": query, "variables": variables}).encode(),
                                 headers={"Authorization": f"Bearer {key or os.environ['BUFFER_API_KEY']}",
                                          "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


# 検索で引っかかる2〜3語のキーワード。動画の番号で順番に回し、同じ言い回しが続かないようにする
# タイトルの後半(キーワード2つを含む自然な一文)と、説明欄の2〜3文。動画の番号で順番に回す
TITLE = {
    "grammar": ["英検2級・大学受験によく出る英文法", "高校英語とTOEICで差がつく文法", "中学・高校で習う英文法の確認に", "共通テストにも出る英文法の2択"],
    "idiom": ["ネイティブが日常会話で使う英語表現", "海外ドラマにも出る英語フレーズ", "英検準1級にも出る便利な英熟語", "英会話ですぐ使えるイディオム"],
    "toeic": ["TOEIC Part 5によく出る単語と文法", "TOEIC 600点を目指す人の頻出語", "ビジネス英語とTOEICで使える単語"],
    "white": ["大学受験・英検2級によく出る英熟語", "高校英語で覚えたい頻出の英熟語", "共通テストにも出る英熟語クイズ"],
    "black": ["英検準1級によく出る英単語クイズ", "大人の語彙力アップに英検準1級の単語", "英検準1級の語彙問題に強くなる"],
    "listening": ["イギリス英語のリスニング練習", "TOEICリスニング対策にもなる英語", "英語耳を鍛える1回聞き取りクイズ"],
}
DESC = {
    "grammar": ["英検2級や大学受験によく出る英文法の2択クイズです。1日1問で、迷いやすいポイントを確認しましょう。TOEICの文法問題(Part 5)の練習にも使えます。",
                "高校で習う英文法を、2択でサクッと確認できるクイズです。共通テストや英検の文法対策に。答えと解説はコメント欄・プロフィールのリンクから。"],
    "idiom": ["ネイティブが日常会話でよく使う英語表現を、2択クイズで覚えましょう。海外ドラマや英会話でもよく出てくる言い回しです。",
              "知っていると便利な英熟語・イディオムのクイズです。英検やTOEICの語彙対策にも、英会話の練習にも使えます。"],
    "toeic": ["TOEICによく出る単語と文法の2択クイズです。Part 5の対策や、スキマ時間の語彙力アップにどうぞ。ビジネス英語でもよく使う表現です。",
              "TOEIC 600点〜800点を目指す人向けの頻出問題です。1日1問、通勤時間などのスキマ時間で続けましょう。"],
    "white": ["大学受験や英検2級によく出る英熟語のクイズです。例文ごと覚えると、長文読解でもすぐ意味がわかるようになります。",
              "高校英語の頻出の英熟語を、例文といっしょに確認しましょう。共通テストや英検の対策にも使えます。"],
    "black": ["英検準1級によく出る英単語のクイズです。例文ごと覚えて、長文読解と語彙問題に強くなりましょう。大人の語彙力アップにもどうぞ。",
              "英検準1級の語彙問題に出る、少し難しい英単語を1日1語。英作文やスピーキングで使える例文つきです。"],
    "listening": ["イギリス英語のリスニング練習です。1回で聞き取れるか挑戦してみましょう。TOEICのリスニング対策にも使えます。",
                  "英語の耳を鍛える、短いリスニングクイズです。毎日少しずつ聞いて、英語の音に慣れましょう。"],
}
TAGS = {"grammar": "#英文法", "idiom": "#英語表現", "toeic": "#TOEIC", "white": "#英熟語", "black": "#英検準1級", "listening": "#英語リスニング"}
GRAMMAR_CATS = {"時制", "助動詞", "語法", "前置詞", "品詞", "受動態", "分詞", "不定詞", "動名詞", "関係詞", "比較", "仮定法", "接続詞"}

def topic_of_quiz(q):
    """eng_navi の問題の種類(緑=文法/ピンク=イディオム/青=TOEIC)"""
    cat = q.get("category") or ""
    if cat in GRAMMAR_CATS: return "grammar"
    if "TOEIC" in cat or "toeic" in cat.lower(): return "toeic"
    if cat: return "idiom"
    return ["idiom", "toeic", "grammar"][q["no"] % 3]

def pick(table, topic, n):
    pool = table.get(topic) or table["grammar"]
    return pool[n % len(pool)]

def make_title(caption, topic=None, n=0):
    """問題の一言+キーワード2つを含む自然な一文(45字前後まで)。"""
    first = next((l.strip() for l in caption.splitlines() if l.strip()), "英語クイズ")
    first = re.sub(r"#\S+", "", first).strip()
    if not topic:
        return first[:90] + " #shorts"
    rest = pick(TITLE, topic, n)
    first = first[: max(8, 46 - len(rest))]
    return f"{first} {rest} #shorts"

def make_description(caption, topic=None, n=0):
    # インスタ向けの案内(プロフィールのリンク・ハイライト)と、ハッシュタグは外す(タグは最後に3つまで)
    lines = [re.sub(r"#\S+", "", l).rstrip() for l in caption.replace("　", "").splitlines()
             if "プロフィールのリンク" not in l and "ハイライト" not in l]
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    # ショートの説明欄のリンクは押せない(YouTube の仕様)ので、チャンネルのプロフィールのリンク(/go/)に案内する
    head = "📚 答え合わせ・音声つき復習(無料)と、おすすめの単語集・英会話アプリは、チャンネル名を押して出るプロフィールのリンクから\n\n"
    if topic:
        head = pick(DESC, topic, n) + "\n\n" + head  # 自然な2〜3文(キーワード3〜4つ)
    note = "\n\n🔗 eng-navi.github.io/go" + (f"\n\n{TAGS.get(topic, '#英語学習')} #英語学習 #shorts" if topic else "")
    return head + text[: 4800 - len(note) - len(head)] + note


def send(video_url, caption, title=None, privacy="public", due=None, topic=None, n=0):
    if not os.environ.get("BUFFER_API_KEY"):
        print("YouTube: BUFFER_API_KEY がないので送りません")
        return None
    try:
        desc = make_description(caption, topic, n)
        res = gql(MUTATION, {"input": {
            "channelId": CHANNEL, "text": desc, "schedulingType": "automatic",
            **({"mode": "customScheduled", "dueAt": due} if due else {"mode": "shareNow"}),
            "assets": [{"video": {"url": video_url}}],
            "metadata": {"youtube": {"title": make_title(title or caption, topic, n), "categoryId": "27",
                                     "privacy": privacy, "madeForKids": False, "notifySubscribers": True}},
        }})
        out = (res.get("data") or {}).get("createPost") or {}
        if out.get("post"):
            print(f"✓ YouTube(Buffer)に送りました {out['post']['id']}")
            return out["post"]["id"]
        print(f"YouTube(Buffer)の送信に失敗: {out.get('message') or res.get('errors')}")
    except Exception as e:  # インスタの投稿は止めない
        print(f"YouTube(Buffer)の送信に失敗: {e}")
    return None


def tiktok_text(caption):
    """TikTok の説明文(2200字まで)。リンクは押せないので「プロフィールから」と書く。"""
    lines = [l.rstrip() for l in caption.replace("\u3000", "").splitlines()
             if "プロフィールのリンク" not in l and "ハイライト" not in l]
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    first, _, rest = text.partition("\n")  # 2行目に短く案内(「もっと見る」を開く前に見える位置)
    text = f"{first}\n📚 答え合わせ・おすすめ教材はプロフィールのリンクから\n{rest}"
    note = "\n\n📚 無料のクイズ・音声つき復習と、おすすめの単語集・英会話アプリは、プロフィールのリンクのページにまとめています"
    return text[: 2150 - len(note)] + note


def tiktok_channel(key):
    """TikTok 用の Buffer アカウント(無料)から、TikTok のチャンネル ID を探す。"""
    q = "{ account { organizations { id } } }"
    org = gql(q, {}, key)["data"]["account"]["organizations"][0]["id"]
    chs = gql("query($o: OrganizationId!) { channels(input:{organizationId:$o}) { id service } }", {"o": org}, key)["data"]["channels"]
    return next(c["id"] for c in chs if c["service"] == "tiktok")


def send_tiktok(video_url, caption, due=None):
    key = os.environ.get("BUFFER_TIKTOK_API_KEY")  # TikTok は別の無料アカウント(YouTube だけ有料のアカウントに置いている)
    if not key:
        print("TikTok: BUFFER_TIKTOK_API_KEY がないので送りません")
        return None
    try:
        res = gql(MUTATION, {"input": {
            "channelId": tiktok_channel(key), "text": tiktok_text(caption), "schedulingType": "automatic",
            **({"mode": "customScheduled", "dueAt": due} if due else {"mode": "shareNow"}),
            "assets": [{"video": {"url": video_url}}],
        }}, key)
        out = (res.get("data") or {}).get("createPost") or {}
        if out.get("post"):
            print(f"✓ TikTok(Buffer)に送りました {out['post']['id']}")
            return out["post"]["id"]
        print(f"TikTok(Buffer)の送信に失敗: {out.get('message') or res.get('errors')}")
    except Exception as e:
        print(f"TikTok(Buffer)の送信に失敗: {e}")
    return None


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "test":
        send(sys.argv[2], "テスト投稿です(あとで消します)\n動作確認", title="テスト #shorts", privacy="private")
