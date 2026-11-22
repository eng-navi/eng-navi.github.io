"""インスタに出した動画を、Buffer 経由で YouTube ショートにも出す。

    python3 youtube_buffer.py test <動画URL>   # 非公開で1本試す

- YouTube の公式 API は審査が通るまで動画が非公開に制限されるので、審査済みの Buffer を通す。
- 鍵は BUFFER_API_KEY(.env と GitHub の Secrets)。期限は 2027/11/22(作り直すときは Buffer の Settings → API)。
- 無料プランは予約が10件までなので、まとめて予約せず、インスタに出たときに shareNow で1本ずつ送る。
- 失敗してもインスタの投稿は止めない(ログだけ出す)。
"""
import json
import os
import re
import sys
import urllib.request

API = "https://api.buffer.com"
TIKTOK = "6b026f288541f09ecb5e0c42"  # TikTok @quizify_english(クイズファイの動画を流す)
CHANNEL = "6b02693d8541f09ecb5dca6f"  # 英語クイズ | サクサク英会話・瞬間英作文トレ(eng_navi とクイズファイを両方流す)
SITE = "https://eng-navi.github.io/"
MUTATION = """mutation($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess { post { id } }
    ... on MutationError { message }
  }
}"""


def gql(query, variables):
    req = urllib.request.Request(API, data=json.dumps({"query": query, "variables": variables}).encode(),
                                 headers={"Authorization": f"Bearer {os.environ['BUFFER_API_KEY']}",
                                          "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def make_title(caption):
    """キャプションの1行目からタイトル(100字まで)を作る。"""
    first = next((l.strip() for l in caption.splitlines() if l.strip()), "英語クイズ")
    first = re.sub(r"#\S+", "", first).strip()
    tail = " #shorts"
    return first[: 100 - len(tail)] + tail


def make_description(caption):
    # インスタ向けの案内(プロフィールのリンク・ハイライト)は YouTube では通じないので外す
    lines = [l.rstrip() for l in caption.replace("　", "").splitlines()
             if "プロフィールのリンク" not in l and "ハイライト" not in l]
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    note = f"\n\n🔊 音声つきの復習・過去の問題はこちら(無料)\n{SITE}"
    return text[: 4900 - len(note)] + note


def send(video_url, caption, title=None, privacy="public"):
    if not os.environ.get("BUFFER_API_KEY"):
        print("YouTube: BUFFER_API_KEY がないので送りません")
        return None
    try:
        desc = make_description(caption)
        res = gql(MUTATION, {"input": {
            "channelId": CHANNEL, "text": desc, "schedulingType": "automatic", "mode": "shareNow",
            "assets": [{"video": {"url": video_url}}],
            "metadata": {"youtube": {"title": title or make_title(caption), "categoryId": "27",
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
    note = "\n\n🔊 音声つきの復習は、プロフィールのリンクから"
    return text[: 2150 - len(note)] + note


def send_tiktok(video_url, caption):
    if not os.environ.get("BUFFER_API_KEY"):
        return None
    try:
        res = gql(MUTATION, {"input": {
            "channelId": TIKTOK, "text": tiktok_text(caption), "schedulingType": "automatic", "mode": "shareNow",
            "assets": [{"video": {"url": video_url}}], "metadata": {"tiktok": {"isAiGenerated": True}},
        }})
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
