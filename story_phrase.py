"""フレーズのストーリー(eng_navi):1枚目「この英語、わかる?」(画像)→ 2枚目 答え+例文の動画(🇬🇧女性・男性の音声)。

    .venv-tts/bin/python story_phrase.py build     # STORIES の分を docs/stories/ に書き出す
    python3 story_phrase.py run                     # 予約(story_queue.json)の時間になった分を投稿(GitHub Actions)
    python3 story_phrase.py list

スタンプは使わないので、API で自動投稿できる。
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "docs" / "stories"
QUEUE = ROOT / "story_queue.json"
LOG = ROOT / "story_posted.json"
W, H, FPS, SR = 1080, 1920, 30, 24000

# (key, 表現, 意味, 例文, 和訳, ひとこと)
STORIES = [
    ("just_in_case", "just in case", "念のため", "Take a jacket, just in case.", "念のため上着持っていきな", "出かける前のひとことに"),
    ("drive_me_crazy", "drive me crazy", "イライラさせる", "This slow Wi-Fi is driving me crazy.", "この遅いWi-Fi、ほんとイライラする", "crazy でも「頭がおかしい」じゃないよ"),
    ("couldnt_be_better", "couldn't be better", "最高だよ", "How's your new job? Couldn't be better!", "新しい仕事どう?— 最高!", "これ以上よくなれない=最高"),
    ("what_a_shame", "What a shame!", "それは残念!", "The festival was canceled? What a shame!", "お祭り中止?残念!", "shame=恥 ではなく「残念」"),
    ("stuck_in_traffic", "get stuck in traffic", "渋滞につかまる", "Sorry I'm late. I got stuck in traffic.", "遅れてごめん、渋滞にはまってた", "遅刻の言い訳の定番"),
    ("keep_me_awake", "keep me awake", "目がさえる", "Coffee at night keeps me awake.", "夜にコーヒー飲むと眠れなくなる", "keep+人+状態=〜のままにする"),
    ("free_of_charge", "free of charge", "無料で", "Parking is free of charge after 6 p.m.", "18時以降は駐車無料", "TOEICの定番。free だけでもOK"),
    ("might_as_well", "might as well", "(どうせなら)〜しようか", "The bus is late. We might as well walk.", "バス来ないね。歩いちゃおうか", "「どっちでもいいけど」くらいの軽い提案"),
    ("bring_myself", "can't bring myself to", "〜する気になれない", "I can't bring myself to clean my room.", "部屋を片づける気になれない", "bring myself=自分を連れていく"),
    ("hit_it_off", "hit it off", "すぐ意気投合する", "We hit it off at the party.", "パーティーですぐ意気投合した", "初対面で気が合ったときに"),
    ("on_my_way", "I'm on my way.", "今向かってる", "I'm on my way! Be there in five.", "今向かってる!5分で着く", "待ち合わせの神フレーズ"),
    ("go_viral", "go viral", "バズる", "Her cat video went viral overnight.", "彼女の猫動画、一晩でバズった", "viral=ウイルスのように広がる"),
    ("call_it_a_day", "call it a day", "今日はここまでにする", "It's late. Let's call it a day.", "遅いし、今日はここまでにしよう", "仕事の終わりにひとこと"),
    ("rain_check", "take a rain check", "また今度にする", "Can I take a rain check on dinner?", "夕食、また今度にしてもいい?", "雨で中止の試合の振替券が由来"),
    ("piece_of_cake", "a piece of cake", "楽勝", "The test was a piece of cake.", "テストは楽勝だった", "ケーキ1切れくらい簡単"),
    ("hold_your_horses", "Hold your horses!", "ちょっと落ち着いて", "Hold your horses! We haven't decided yet.", "落ち着いて!まだ決めてないよ", "馬をおさえて=はやる気持ちを抑えて"),
    ("nailed_it", "You nailed it!", "完ぺき!", "Your speech was great. You nailed it!", "スピーチ最高。完ぺき!", "nail=くぎを一発で打ち込む"),
    ("from_what_i_hear", "from what I hear", "聞いたところでは", "From what I hear, the new cafe is great.", "聞いた話だと、新しいカフェすごくいいらしい", "うわさ話の前置きに"),
    ("stay_fit", "stay fit", "健康を保つ", "I walk to work to stay fit.", "健康のために歩いて通勤してる", "fit=体の調子がいい"),
]


def card(phrase, top, mid, bottom, accent=False):
    import story_book as sb
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (W, H), sb.PAPER)
    d = ImageDraw.Draw(img)
    for x in range(0, W, 54):
        d.line([(x, 0), (x, H)], fill=sb.GRID, width=2)
    for y in range(0, H, 54):
        d.line([(0, y), (W, y)], fill=sb.GRID, width=2)
    d.text((W // 2, 360), top, font=sb.JP(64), fill=sb.RED, anchor="ms")
    size = 150
    while sb.EN(size).getlength(phrase) > W - 2 * 120:
        size -= 6
    d.text((W // 2, 760), phrase, font=sb.EN(size), fill=sb.INK, anchor="ms")
    lw = sb.EN(size).getlength(phrase) / 2
    sb.underline(d, W // 2 - lw, W // 2 + lw, 800, w=8)
    import manga as m
    y = 1000
    for i, line in enumerate(mid):
        f = sb.JP(70) if i == 0 and accent else sb.JP(48)
        jp = any(ord(c) > 0x3000 for c in line)
        h = m.draw_fit(d, (W // 2, y), line, f, sb.RED if i == 0 and accent else sb.INK, width=W - 240, jp=jp) if line else 60
        y += h + 20
    d.text((W // 2, 1620), bottom, font=sb.JP(40), fill=(120, 120, 120), anchor="ms")
    d.text((W // 2, 1780), "@eng_navi", font=sb.EN(46), fill=(150, 150, 150), anchor="ms")
    sb.star(d, 150, 260, 26)
    sb.star(d, 930, 230, 20)
    return img


def build():
    import numpy as np
    import soundfile as sf
    from kokoro import KPipeline
    pipe = KPipeline(lang_code="b", repo_id="hexgrad/Kokoro-82M")
    say = lambda t, v: np.concatenate([a for _, _, a in pipe(t, voice=v, speed=0.9)])
    gap = lambda s: np.zeros(int(SR * s), dtype=np.float32)
    OUT.mkdir(parents=True, exist_ok=True)
    for key, phrase, ja, en, eja, tip in STORIES:
        card(phrase, "この英語、わかる?", ["", "答えは次のストーリーで👉".replace("👉", "→")], "保存して、あとで見返してね").save(OUT / f"{key}_q.png")
        ans = card(phrase, "答え", [f"= {ja}", "", en, f"({eja})"], tip, accent=True)
        audio = np.concatenate([gap(0.5), say(phrase, "bf_emma"), gap(0.6), say(en, "bf_emma"), gap(0.9),
                                say(phrase, "bm_george"), gap(0.6), say(en, "bm_george"), gap(0.8)])
        dur = len(audio) / SR
        with tempfile.TemporaryDirectory() as tmp:
            png, wav = Path(tmp) / "a.png", Path(tmp) / "a.wav"
            ans.save(png)
            sf.write(wav, audio, SR)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(png), "-i", str(wav), "-t", f"{dur:.2f}",
                            "-r", str(FPS), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-af", "volume=1.6",
                            "-movflags", "+faststart", str(OUT / f"{key}_a.mp4")], check=True)
        print(f"✓ {key}({dur:.1f}秒)")


def run():
    import post
    post.load_env()
    if os.environ.get("CI"):
        post.git("config", "user.name", "github-actions[bot]")
        post.git("config", "user.email", "41898299+github-actions[bot]@users.noreply.github.com")
    done = json.loads(LOG.read_text()) if LOG.exists() else {}
    now = datetime.now(post.JST)
    user = os.environ["IG_USER_ID"]
    base = os.environ.get("SITE_URL", "https://eng-navi.github.io").rstrip("/")
    for item in json.loads(QUEUE.read_text()):
        if item["key"] in done or datetime.strptime(item["at"], "%Y-%m-%d %H:%M").replace(tzinfo=post.JST) > now:
            continue
        ids = []
        c = post.api("POST", f"{user}/media", media_type="STORIES", image_url=f"{base}/stories/{item['key']}_q.png")["id"]
        post.wait_until_ready(c)
        ids.append(post.api("POST", f"{user}/media_publish", creation_id=c)["id"])
        time.sleep(20)  # 1枚目を見てもらう間をあける
        c = post.api("POST", f"{user}/media", media_type="STORIES", video_url=f"{base}/stories/{item['key']}_a.mp4")["id"]
        post.wait_until_ready(c)
        ids.append(post.api("POST", f"{user}/media_publish", creation_id=c)["id"])
        done[item["key"]] = {"ids": ids, "posted_at": datetime.now(post.JST).isoformat(timespec="seconds")}
        LOG.write_text(json.dumps(done, ensure_ascii=False, indent=2) + "\n")
        print(f"✓ ストーリー {item['key']}")
        post.git("add", str(LOG))
        post.git("commit", "-q", "-m", f"ストーリー {item['key']} を投稿")
        post.git("pull", "-q", "--rebase", "--autostash")
        post.git("push", "-q")
        break  # 1回に1組


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "build":
        build()
    elif cmd == "run":
        run()
    else:
        done = json.loads(LOG.read_text()) if LOG.exists() else {}
        for i in json.loads(QUEUE.read_text()):
            print(f"{i['at']}  {i['key']:<20} {'投稿済み' if i['key'] in done else '予約中'}")


if __name__ == "__main__":
    main()
