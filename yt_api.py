"""YouTube Data API(説明欄の書きかえ用。アップロードには使わない)。

    .venv-tts/bin/python yt_api.py login              # 初回・許可が切れたとき(ブラウザで「許可」)
    .venv-tts/bin/python yt_api.py list               # 動画を再生回数の多い順に → out/yt_desc/videos.json
    .venv-tts/bin/python yt_api.py update <動画ID> <説明文のファイル>

- 鍵は client_secret.json、許可は youtube_token.json(どちらも公開しない・.gitignore 済み)
- Google Cloud のプロジェクト eng-navi-youtube(テスト中なので、許可は7日ほどで切れることがある → login し直す)
- 無料。1日の上限(10,000ユニット)を超えると止まるだけ。説明欄の書きかえは1本50ユニット
"""
import json
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

ROOT = Path(__file__).parent
SECRET = ROOT / "client_secret.json"
TOKEN = ROOT / "youtube_token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]


def creds(interactive=False):
    c = Credentials.from_authorized_user_file(str(TOKEN), SCOPES) if TOKEN.exists() else None
    if c and c.expired and c.refresh_token:
        try:
            c.refresh(Request())
        except Exception:
            c = None
    if not c or not c.valid:
        if not interactive:
            sys.exit("YouTube の許可が切れています。yt_api.py login をしてください")
        c = InstalledAppFlow.from_client_secrets_file(str(SECRET), SCOPES).run_local_server(port=0, open_browser=True)
    TOKEN.write_text(c.to_json())
    TOKEN.chmod(0o600)
    return c


def yt(interactive=False):
    return build("youtube", "v3", credentials=creds(interactive))


def list_videos():
    y = yt()
    ch = y.channels().list(part="contentDetails,snippet", mine=True).execute()["items"][0]
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, tok = [], None
    while True:
        r = y.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50, pageToken=tok).execute()
        ids += [i["contentDetails"]["videoId"] for i in r["items"]]
        tok = r.get("nextPageToken")
        if not tok:
            break
    vids = []
    for k in range(0, len(ids), 50):
        r = y.videos().list(part="snippet,statistics,contentDetails", id=",".join(ids[k:k + 50])).execute()
        for v in r["items"]:
            vids.append(dict(id=v["id"], title=v["snippet"]["title"], views=int(v["statistics"].get("viewCount", 0)),
                             duration=v["contentDetails"]["duration"], published=v["snippet"]["publishedAt"][:10],
                             description=v["snippet"]["description"]))
    vids.sort(key=lambda v: -v["views"])
    out = ROOT / "out" / "yt_desc" / "videos.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(vids, ensure_ascii=False, indent=1))
    print(f"{ch['snippet']['title']}:{len(vids)}本")
    for v in vids[:15]:
        print(v["views"], v["duration"], v["id"], v["title"][:50])


def update(video_id, text):
    """説明欄だけを書きかえる(タイトル・カテゴリなどはそのまま)。"""
    y = yt()
    v = y.videos().list(part="snippet", id=video_id).execute()["items"][0]
    sn = v["snippet"]
    old = sn.get("description", "")
    sn["description"] = text
    body = {"id": video_id, "snippet": {k: sn[k] for k in ("title", "description", "categoryId", "tags", "defaultLanguage") if k in sn}}
    y.videos().update(part="snippet", body=body).execute()
    backup = ROOT / "out" / "yt_desc" / "backup"
    backup.mkdir(parents=True, exist_ok=True)
    (backup / f"{video_id}.txt").write_text(old)  # 元に戻せるように、前の説明欄を残す
    print(f"✓ {video_id} の説明欄を書きかえました(前の文は out/yt_desc/backup/ に保存)")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "login":
        yt(interactive=True)
        print("✓ YouTube につながりました")
    elif cmd == "list":
        list_videos()
    elif cmd == "update":
        update(sys.argv[2], Path(sys.argv[3]).read_text().strip())
