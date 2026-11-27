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
KEYWORDS = {
    "grammar": ["英文法 問題 高校", "英検2級 文法", "共通テスト 英語 文法", "大学受験 英文法", "中学英語 文法 復習", "TOEIC 文法問題",
                "英文法 ひっかけ問題", "時制 問題 英語", "英語 文法 独学", "高校英語 文法 確認"],
    "idiom": ["英熟語 意味 クイズ", "英語 イディオム 日常会話", "ネイティブ 英語表現", "英検準1級 熟語", "使える 英語フレーズ",
              "英会話 フレーズ 初心者", "英語 言い回し 意味", "海外ドラマ 英語表現"],
    "toeic": ["TOEIC 頻出 単語", "TOEIC Part5 対策", "TOEIC 600点 単語", "TOEIC 文法 問題", "TOEIC 900 語彙", "TOEIC 独学 スキマ時間",
              "TOEIC 言い換え 単語", "ビジネス英語 単語"],
    "white": ["大学受験 英熟語", "英熟語 頻出 高校", "英検2級 熟語", "共通テスト 英熟語", "英熟語 覚え方", "入試 英語 熟語"],
    "black": ["英検準1級 単語", "準1級 語彙 問題", "英単語 上級 クイズ", "英検 単語 覚え方", "大人の英単語 難しい", "英検準1級 対策"],
    "listening": ["英語 リスニング 練習", "TOEIC リスニング 対策", "イギリス英語 リスニング", "リスニング 聞き取り 1回", "英語耳 トレーニング", "英会話 聞き取り 初心者"],
}
GRAMMAR_CATS = {"時制", "助動詞", "語法", "前置詞", "品詞", "受動態", "分詞", "不定詞", "動名詞", "関係詞", "比較", "仮定法", "接続詞"}

def topic_of_quiz(q):
    """eng_navi の問題の種類(緑=文法/ピンク=イディオム/青=TOEIC)"""
    cat = q.get("category") or ""
    if cat in GRAMMAR_CATS: return "grammar"
    if "TOEIC" in cat or "toeic" in cat.lower(): return "toeic"
    if cat: return "idiom"
    return ["idiom", "toeic", "grammar"][q["no"] % 3]

def keyword(topic, n, k=0):
    pool = KEYWORDS.get(topic) or KEYWORDS["grammar"]
    return pool[(n * 3 + k) % len(pool)]  # 番号ごとにずらす

def make_title(caption, topic=None, n=0):
    """キャプションの1行目+検索キーワード(100字まで)。"""
    first = next((l.strip() for l in caption.splitlines() if l.strip()), "英語クイズ")
    first = re.sub(r"#\S+", "", first).strip()
    tail = (f"|{keyword(topic, n)}" if topic else "") + " #shorts"
    return first[: 100 - len(tail)] + tail


def make_description(caption, topic=None, n=0):
    # インスタ向けの案内(プロフィールのリンク・ハイライト)は YouTube では通じないので外す
    lines = [l.rstrip() for l in caption.replace("　", "").splitlines()
             if "プロフィールのリンク" not in l and "ハイライト" not in l]
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    # ショートの説明欄のリンクは押せない(YouTube の仕様)ので、チャンネルのプロフィールのリンク(/go/)に案内する
    head = "📚 答え合わせ・音声つき復習(無料)と、おすすめの単語集・英会話アプリは、チャンネル名を押して出るプロフィールのリンクから\n\n"
    if topic:
        head = f"🔎 {keyword(topic, n, 1)}/{keyword(topic, n, 2)}\n" + head
    note = "\n\n🔗 eng-navi.github.io/go"
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
            "metadata": {"youtube": {"title": (title + (f"|{keyword(topic, n)}" if topic else "")) if title else make_title(caption, topic, n), "categoryId": "27",
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
