"""@seidoku.lab「差がつく英文読解」にリールを投稿する。トークンは GEO_IG_*(旧 地理クイズを着せ替え)。

    python3 seidoku_post.py add 1 "2026-11-29 07:30"   # 動画を docs/seidoku に公開して予約表へ(push は別)
    python3 seidoku_post.py now 1                      # すぐ投稿(動画は先に push して公開済みのこと)
    python3 seidoku_post.py run                        # 時間になった予約を投稿(GitHub Actions 用)
キャプション・コメントは TEXTS に毎回書き下ろす(使い回し禁止)。正解と詳しい解説はコメント欄。
"""
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

import manga_post as mp
import post

ROOT = Path(__file__).parent
SITE = os.environ.get("SITE_URL", "https://eng-navi.github.io")
SCHEDULE, LOG = ROOT / "seidoku_schedule.json", ROOT / "seidoku_posted.json"

TEXTS = {
    1: dict(
        caption="""この長い主語、見抜ける?🔍
That で始まる名詞節が主語+接続詞の like。難関大・英検準1級の長文で差がつく「SVの発見」を、1文で練習しよう。
正しい訳は 1 か 2 か、コメントで教えてね👇

#英文読解 #大学受験英語 #英検準1級 #構文解析 #英語長文

Music: Days Off / Matrika — Music from #Uppbeat (free for Creators!)""",
        comment="""✅ 正解は 1
That he said nothing was wise, much like a good player waits for the right moment.
彼が何も言わなかったのは賢明だった。よい選手が好機を待つのとほぼ同じように。

━━ 詳しい解説 ━━
① That のうしろに he said と SV が続く → 名詞節の that「〜ということ」。
1つの節に動詞は1つなので、2つ目の動詞 was の手前までが長い S。

② was wise で「賢明だった」(SVC)。

③ like のうしろにも a good player waits と SV が続く → 接続詞の like「〜のように」。
前の much は「ほぼ」。

✗ 2 は like を動詞「好む」と読んだひっかけ。like のうしろに SV があれば接続詞。

📝 動画の英文
That young children ask endless questions is entirely healthy, much like scientists test ideas they cannot yet explain.
幼い子どもが質問ばかりするのは、まったく健全なことだ。科学者が、まだ説明できない考えを試すのとほぼ同じように。"""),
    2: dict(
        caption="""この What、「何」と訳してない?🤔
文頭の What は「〜すること」で長い主語に。was のあとの that 節、名詞のすぐあとの SV(関係詞の省略)まで、英文解釈の基本を1文で。
正しい訳は 1 か 2 か、コメントで教えてね👇

#英文解釈 #関係代名詞 #大学受験 #英検準1級 #英語の勉強

Music: Jasmine / 92elm — Music from #Uppbeat (free for Creators!)""",
        comment="""✅ 正解は 1
What worried the coach was that the players he had trained seemed tired.
コーチが心配したのは、自分が鍛えた選手たちが疲れて見えたことだった。

━━ 詳しい解説 ━━
① 文頭の What は「〜すること」。2つ目の動詞 was の手前までが長い S。
What worried the coach =「コーチを心配させたこと」→「コーチが心配したのは」。

② was のあとの that は「〜ということ」。文の最後までが C。

③ the players he had trained:名詞 the players のすぐあとに he had trained(SV)→ 関係詞の省略。「彼が鍛えた選手たち」。

✗ 2 は he を trained の目的語のように読んだワナ。名詞+SV は「SがVする名詞」。

📝 動画の英文
What surprised the visitors most was that the old town they had read about looked completely modern.
訪問者をいちばん驚かせたのは、本で読んでいた古い町が、すっかり現代的に見えたことだった。"""),
    3: dict(
        caption="""文頭の Whether、「天気」じゃないよ☁️
Whether が主語のカタマリを作ると「〜かどうか」。depend on(〜次第だ)と how 節まで、長文読解でよく出る形を1文で練習しよう。
正しい訳は 1 か 2 か、コメントで👇

#英文読解 #英語長文 #大学受験英語 #英検2級 #英文法

Music: Golden Age / Walz — Music from #Uppbeat (free for Creators!)""",
        comment="""✅ 正解は 1
Whether the team wins depends on how well the new players work together.
チームが勝つかどうかは、新しい選手がどれだけうまく協力できるか次第だ。

━━ 詳しい解説 ━━
① 文頭の Whether のカタマリが S なら「〜かどうか」。2つ目の動詞 depends の手前までが S。

② depend on のうしろが人以外なら「〜次第だ」(人なら「〜に頼る」)。

③ how well 〜 together が depend on の目的語。「どれだけうまく〜か」。

✗ 2 は Whether を「〜であろうとなかろうと」(副詞のカタマリ)と読んだワナ。
Whether のカタマリのすぐあとに動詞 depends が来ているので、カタマリは主語 →「〜かどうか」。

📝 動画の英文
Whether the new library will open on time depends on how quickly the workers can finish the roof.
新しい図書館が予定どおり開館するかどうかは、作業員がどれだけ早く屋根を仕上げられるか次第だ。"""),
}


def use():
    post.load_env()
    os.environ["IG_USER_ID"] = os.environ["GEO_IG_USER_ID"]
    os.environ["IG_ACCESS_TOKEN"] = os.environ["GEO_IG_ACCESS_TOKEN"]


def add(no, at):
    no = int(no)
    src = ROOT / "out" / "seidoku" / f"seidoku_{no:03d}.mp4"
    starts = json.loads(src.with_suffix(".starts.json").read_text())
    dst = ROOT / "docs" / "seidoku" / src.name
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dst)
    key = f"seidoku_{no:03d}"
    items = [s for s in mp.load(SCHEDULE, []) if s["key"] != key]
    items.append({"key": key, "at": at, "video": f"{SITE}/seidoku/{dst.name}", "caption": TEXTS[no]["caption"],
                  "comment": TEXTS[no]["comment"], "thumb_ms": int((starts[3] + 2.0) * 1000)})
    items.sort(key=lambda s: s["at"])
    SCHEDULE.write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n")
    print("追加:", key, at, "→ docs/seidoku と seidoku_schedule.json を push してから投稿")


def publish(s):
    use()
    user = os.environ["IG_USER_ID"]
    c = post.api("POST", f"{user}/media", media_type="REELS", video_url=s["video"], caption=post.keep_blank_lines(s["caption"]),
                 share_to_feed="true", thumb_offset=str(s.get("thumb_ms", 12000)))["id"]
    post.wait_until_ready(c)
    mid = post.api("POST", f"{user}/media_publish", creation_id=c)["id"]
    post.api("POST", f"{mid}/comments", message=post.keep_blank_lines(s["comment"]))
    link = post.api("GET", mid, fields="permalink").get("permalink", "")
    log = mp.load(LOG, {})
    log[s["key"]] = {"media_id": mid, "permalink": link, "posted_at": datetime.now(post.JST).isoformat(timespec="seconds")}
    LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
    print(f"✓ {s['key']} {link}")


def run():
    if os.environ.get("CI"):
        post.git("config", "user.name", "github-actions[bot]")
        post.git("config", "user.email", "41898299+github-actions[bot]@users.noreply.github.com")
    done = mp.load(LOG, {})
    now = datetime.now(post.JST)
    due = [s for s in mp.load(SCHEDULE, []) if s["key"] not in done
           and datetime.strptime(s["at"], "%Y-%m-%d %H:%M").replace(tzinfo=post.JST) <= now]
    if not due:
        print("時間になった読解リールはありません"); return
    publish(min(due, key=lambda s: s["at"]))
    mp.push([str(LOG)], "読解リールを投稿")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "add":
        add(sys.argv[2], sys.argv[3])
    elif cmd == "now":
        publish(next(x for x in mp.load(SCHEDULE, []) if x["key"] == f"seidoku_{int(sys.argv[2]):03d}"))
    elif cmd == "run":
        run()
    else:
        done = mp.load(LOG, {})
        for s in mp.load(SCHEDULE, []):
            print(f"{s['at']}  {s['key']}  {'投稿済み' if s['key'] in done else '予約中'}")
