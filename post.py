"""クイズ動画をリールとして投稿し、答えと解説をコメントする。

動画は docs/videos/ に置いて GitHub Pages に push し、その公開URLから Instagram に取り込まれる。

使い方:
    python3 post.py 101 --dry-run    # キャプションとコメントを表示するだけ
    python3 post.py 101              # 投稿する
    python3 post.py --refresh-token  # トークンの有効期限を延長する
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent
API = "https://graph.instagram.com"
LOG = ROOT / "posted.json"
JST = timezone(timedelta(hours=9))

RULE = "--------------------------------------"
# 答えのコメントの最後に添える一文(サイトへの案内。解説の邪魔をしない短さで)
SITE_NOTE = "📚 過去の問題100問以上は、プロフィールのリンクから無料で解けます"


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def api(method, path, **params):
    params["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    query = urllib.parse.urlencode(params)
    if method == "GET":
        req = urllib.request.Request(f"{API}/{path}?{query}")
    else:
        req = urllib.request.Request(f"{API}/{path}", data=query.encode(), method="POST")
    try:
        with urllib.request.urlopen(req) as res:
            return json.load(res)
    except urllib.error.HTTPError as e:
        sys.exit(f"API エラー ({path}): {e.read().decode()}")


def build_comment(q):
    if "options" not in q:
        # ピンク(イディオム紹介):番号なし、語句の意味を並べてから解説
        return "\n".join([
            RULE,
            q["text"].replace("\n", " "),
            q["translation"],
            "",
            *q["glossary"],
            "",
            "【解説】",
            q["explanation"],
            "",
            SITE_NOTE,
            RULE,
        ])
    answer = q["options"][q["answer"] - 1]
    sentence = re.sub(r"\(\s*\)", answer, q["question"])
    return "\n".join([
        RULE,
        f"【{q['no']}】",
        sentence,
        q["translation"],
        "",
        # 語句の意味(任意。例: "by the time：…する時までに")
        *([*q["glossary"], ""] if q.get("glossary") else []),
        "【解説】",
        q["explanation"],
        "",
        SITE_NOTE,
        RULE,
    ])


def wait_until_ready(container_id, timeout=300):
    """動画の取り込みが終わるまで待つ。"""
    start = time.time()
    while time.time() - start < timeout:
        status = api("GET", container_id, fields="status_code,status")
        code = status.get("status_code")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            sys.exit(f"動画の取り込みに失敗: {status}")
        time.sleep(10)
    sys.exit("動画の取り込みがタイムアウトしました")


def git(*args):
    subprocess.run(["git", *args], cwd=ROOT, check=True)


def publish_video(no):
    """動画を docs/videos/ に置いて push する(まだなら書き出しから)。"""
    dst = ROOT / "docs" / "videos" / f"q{no}.mp4"
    if dst.exists():
        return
    src = ROOT / "out" / dst.name
    if not src.exists():
        subprocess.run([sys.executable, "render.py", "quizzes.json", str(no)], cwd=ROOT, check=True)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dst)
    git("add", str(dst))
    git("commit", "-q", "-m", f"動画 q{no} を追加")
    git("push", "-q")


def stage_video(no, timeout=600):
    """動画を公開し、公開URLで取得できるまで待つ。"""
    publish_video(no)
    url = f"{os.environ['SITE_URL'].rstrip('/')}/videos/q{no}.mp4"

    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method="HEAD")) as res:
                if res.status == 200:
                    return url
        except urllib.error.HTTPError:
            pass
        time.sleep(15)
    sys.exit(f"動画が公開URLに反映されませんでした: {url}")


def post(q):
    print("0/4 動画を公開URLに配置")
    video_url = stage_video(q["no"])
    user = os.environ["IG_USER_ID"]

    print(f"1/4 動画を送信: {video_url}")
    container = api("POST", f"{user}/media", media_type="REELS", video_url=video_url,
                    caption=q["caption"], share_to_feed="true")["id"]

    print("2/4 Instagram 側の処理を待機中…")
    wait_until_ready(container)

    print("3/4 公開")
    media_id = api("POST", f"{user}/media_publish", creation_id=container)["id"]

    print("4/4 答えをコメント")
    api("POST", f"{media_id}/comments", message=build_comment(q))

    permalink = api("GET", media_id, fields="permalink").get("permalink")
    log = json.loads(LOG.read_text()) if LOG.exists() else []
    log.append({"no": q["no"], "media_id": media_id, "permalink": permalink,
                "posted_at": datetime.now(JST).isoformat(timespec="seconds")})
    LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
    print(f"✓ 投稿完了 {permalink}")


def refresh_token():
    res = api("GET", "refresh_access_token", grant_type="ig_refresh_token")
    out = os.environ.get("TOKEN_OUT")
    if out:  # GitHub Actions:ログに出さずファイルに書き、Secret の更新に使う
        Path(out).write_text(res["access_token"])
        print(f"✓ トークンを更新しました(残り {res['expires_in'] // 86400} 日)")
        return
    env = ROOT / ".env"
    lines = [l for l in env.read_text().splitlines() if not l.startswith("IG_ACCESS_TOKEN=")]
    lines.append(f"IG_ACCESS_TOKEN={res['access_token']}")
    env.write_text("\n".join(lines) + "\n")
    print(f"✓ トークンを更新しました(残り {res['expires_in'] // 86400} 日)")


def main():
    load_env()
    if "--refresh-token" in sys.argv:
        return refresh_token()
    no = int(sys.argv[1])
    q = next(q for q in json.loads((ROOT / "quizzes.json").read_text()) if q["no"] == no)
    if not q.get("caption"):
        sys.exit(f"{no} に caption がありません(同じキャプションの使い回しは避ける)")
    if "--dry-run" in sys.argv:
        print("=== キャプション ===\n" + q["caption"] + "\n\n=== コメント ===\n" + build_comment(q))
        return
    post(q)


if __name__ == "__main__":
    main()
