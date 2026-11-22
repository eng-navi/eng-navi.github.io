"""YouTube の長い動画:テーマ別のまとめ(検索のロングテール向け)。

    python3 yt_theme.py list            # テーマと問題数(投稿済みのものだけ)
    python3 yt_theme.py build tense     # 1本作る → out/yt_compile/theme_<id>.mp4 / _thumb.jpg / .txt
    python3 yt_theme.py week            # まだ作っていないテーマから7本

- 中身は eng_navi のショート(番号の動画)+答えの画面、25問ごとにサイトの案内、チャプター
- インスタに出ていない番号は入れない(答えを先に見せない)
- タイトルは「大きなキーワード+絞ったキーワード+具体的な語」。説明欄は最初の2行にサイト、おすすめは3つ以上
- 長い動画は Buffer で出せないので、本人が YouTube Studio で上げて毎日1本ずつ予約する
"""
import json
import subprocess
import sys
from pathlib import Path

import yt_compile as yc

ROOT = Path(__file__).parent
OUT = ROOT / "out" / "yt_compile"
CACHE = OUT / "_parts_eng_navi"
AMZ = lambda asin, lid: f"https://www.amazon.co.jp/dp/{asin}?tag=mokumoku70e-22&linkCode=ll2&linkId={lid}&language=ja_JP&ref_=as_li_ss_tl"
OSU = "https://eng-navi.github.io/osusume/?from=yt"
B = {  # 本(Amazon 直リンク)
    "shortcuts": ("『大学受験 英文法・語法SHORTCUTS』", "よく出る良問254問。全問に正解率つきで、苦手がわかる", "https://link.amazon/B0bwqM40M"),
    "scramble": ("『スクランブル英文法・語法 5th Edition』", "入試頻出の文法・語法を1冊で。解説が簡潔で音声つき", AMZ("B0G47KNCKX", "0ce4d1d04fdd489440ff1dce4f987caf")),
    "hanon": ("『英語のハノン 初級』", "わかる文法を、口から出る英語に\n▶ 実際に使った感想:https://note.com/english__nonono/n/n8b3b665fef6a", AMZ("B09NY53725", "aaa9fc05b00ffc5bcfd72de9d08bdca0")),
    "kikufure": ("『TOEIC L&Rテスト 聞いて覚える頻出英語フレーズ キクフレ』", "TOEICによく出るフレーズを音声つきで", "https://link.amazon/B09qOB6Ou"),
    "idiomatic": ("『飛躍のフレーズ IDIOMATIC 300』", "よくある言い回しを英文ごと覚えられる。問題300問つき", "https://link.amazon/B0eHBRPkB"),
    "eureka": ("『大学入試 英文法 Eureka!』", "「差がつく」文法問題で、もう一段上へ", None),
}
S = {  # アプリ・サービス(/osusume/ 経由)
    "speak": ("🗣 スピーク(AI英会話アプリ)", "覚えた英語を、AI相手に声に出して練習\n▶ 600分使ってみた体験記:https://note.com/english__nonono/n/n99960bcd7af3", "speak"),
    "studysapuri": ("📱 スタディサプリENGLISH TOEIC対策コース", "文法の学び直しからパート別の対策まで、スマホで", "studysapuri"),
    "torabit": ("🗣 TORAbit(トラビット)", "シャドーイングと瞬間英作文を、AIの採点つきで", "torabit"),
    "progrit": ("🏆 PROGRIT(英語コーチング)", "本気で伸ばしたい人へ。何をどれだけやるかを一緒に決めてくれる", "progrit"),
}

# テーマ:(id, 分野の条件, タイトル, 一言, サムネの見出し, サムネの黄色い字, キャラ, おすすめ, タグ)
THEMES = [
    ("tense", lambda q: q.get("category") == "時制",
     "英文法 時制の問題|英検2級・TOEICによく出る{n}問(現在完了・過去完了・未来完了)【解説つき】",
     "時制(現在完了・過去完了・未来完了・進行形)の問題だけを集めました。英検2級・TOEIC Part5 によく出る形です。",
     "時制", ("現在完了", "過去完了"), "owl", ["shortcuts", "hanon"], ["speak", "progrit"], "#英文法 #時制 #現在完了 #英検2級 #TOEIC"),
    ("prep_conj", lambda q: q.get("category") in ("前置詞", "前置詞・接続詞", "接続詞"),
     "TOEIC Part5 前置詞と接続詞の見分け方|because と because of・during と while など{n}問",
     "TOEIC Part5 で毎回出る「前置詞か接続詞か」の問題を集めました。空所の後ろが名詞か、主語+動詞かで見分けます。",
     "TOEIC", ("前置詞と", "接続詞"), "penguin", ["kikufure", "shortcuts"], ["studysapuri", "progrit"], "#TOEIC #TOEICPart5 #前置詞 #接続詞 #TOEIC対策"),
    ("modal", lambda q: q.get("category") == "助動詞",
     "英検2級 助動詞の問題{n}問|should have done・need not have done・had better【解説つき】",
     "助動詞(must・cannot・should have done・would rather など)の問題を集めました。英検2級・大学入試によく出る形です。",
     "助動詞", ("英検2級", "頻出"), "owl", ["scramble", "hanon"], ["speak", "progrit"], "#英文法 #助動詞 #英検2級 #大学受験"),
    ("passive", lambda q: q.get("category") in ("受動態", "分詞"),
     "英文法 受動態と分詞の問題{n}問|be given・have O done・made in の見分け方【英検・TOEIC】",
     "受動態と分詞(現在分詞・過去分詞)の問題を集めました。「する側」か「される側」かで見分けるのがコツです。",
     "受動態", ("受動態と", "分詞"), "penguin", ["scramble", "shortcuts"], ["studysapuri", "progrit"], "#英文法 #受動態 #分詞 #英検 #TOEIC"),
    ("toeic_vocab", lambda q: q["no"] % 3 == 1 and q.get("category") in ("品詞", "語彙", "語法", "代名詞", "関係詞"),
     "TOEIC Part5 品詞・語彙問題{n}問|1問10秒で解くコツ【解説つき・聞き流しOK】",
     "TOEIC Part5 の品詞・語彙・語法の問題を集めました。空所の前後だけを見て、すばやく解く練習にどうぞ。",
     "TOEIC", ("Part5", "品詞・語彙"), "owl", ["kikufure", "shortcuts"], ["studysapuri", "progrit"], "#TOEIC #TOEICPart5 #TOEIC文法 #TOEIC単語"),
    ("idiom", lambda q: "text" in q,
     "英検準1級 イディオム{n}選|ネイティブの例文で覚える英熟語【和訳・解説つき】",
     "英検準1級・難関大の長文によく出るイディオムを、例文と一緒に集めました。和訳と解説つきです。",
     "イディオム", ("英検準1級", "英熟語"), "penguin", ["idiomatic", "hanon"], ["speak", "progrit"], "#英検準1級 #イディオム #英熟語 #英語長文"),
    ("grammar_mix", lambda q: q["no"] % 3 == 2 and q.get("category") in ("比較", "仮定法", "関係詞", "動名詞", "不定詞", "語法", "数量"),
     "英文法 比較・仮定法・関係詞・不定詞・動名詞{n}問|英検2級でよく出る形をまとめて復習",
     "英検2級によく出る、比較・仮定法・関係詞・不定詞・動名詞の問題をまとめました。",
     "英文法", ("英検2級", "まとめ"), "owl", ["shortcuts", "scramble"], ["speak", "progrit"], "#英文法 #英検2級 #仮定法 #関係詞 #大学受験"),
]


def posted_max():
    return max(x["no"] for x in json.loads((ROOT / "posted.json").read_text()))


def items(theme):
    qs = json.loads((ROOT / "quizzes.json").read_text())
    top = posted_max()
    return [q["no"] for q in qs if q["no"] <= top and theme[1](q) and (ROOT / "out" / "eng_navi" / f"q{q['no']}.mp4").exists()]


def recs(books, svcs):
    out = ["🎁 この動画と一緒に使うなら(PR)"]
    for k in books:
        b = B[k]
        if b[2]:
            out.append(f"📗 本:{b[0]}\n{b[1]}\n{b[2]}")
    for k in svcs:
        s = S[k]
        out.append(f"{s[0]}\n{s[1]}\n→ {OSU}#{s[2]}")
    return "\n\n".join(out)


LILY, GEORGE = "pFZP5JQG7iQjIQuC4Bku", "JBFqnCBsd6RMkjVDRZzb"  # イギリス英語(女性・男性)。ElevenLabs
PLAYLIST = ["sailing", "lantern", "vapour", "whales", "tunnel"]  # 長い動画の BGM(1曲を流しっぱなし、つなぎ目はクロスフェード)
CREDITS = {"sailing": "Sailing Home / Oliver Massa", "lantern": "Lantern / all:ambient", "vapour": "Vapour / Simon Folwar",
           "whales": "Death Of The Whales / Sky Cassette", "tunnel": "Tunnel / Danijel Zambo"}
SR = 44100
Q_CUT = 3.55  # 元のショートは 3.65 秒で見出しが「答えはコメント欄で」に変わる


def sentence(q):
    if "options" in q:
        return q["question"].replace("( )", q["options"][q["answer"] - 1])
    return q["text"].replace("\\n", " ").replace("\n", " ")


def voice(text, vid):
    import quizify_black as qb
    qb.LEVEL.setdefault(vid, qb.LEVEL[qb.EN_VOICE])
    return qb.tts(vid, text, 1.0)  # キャッシュあり・歪ませないリミッター(クリアな音)


def wrap_mixed(d, text, font, width):
    """日本語は1文字ずつ、英単語は単語ごとに折り返す(英単語の途中で切らない)。"""
    import re
    toks = re.findall(r"[A-Za-z0-9'’\-.,/~]+|\s+|.", text)
    lines, cur = [], ""
    for tk in toks:
        if cur and d.textlength(cur + tk, font=font) > width and tk not in "、。」)":
            lines.append(cur.rstrip())
            cur = tk.lstrip()
        else:
            cur += tk
    return lines + ([cur] if cur else [])


def explain_card(q, path):
    """答えのあとの解説(要点2〜3行)+くわしい解説のページの URL。"""
    import render
    from PIL import Image, ImageDraw
    t = render.THEMES[render.theme_name(q["no"])]
    im = Image.new("RGB", (1080, 1920), t["bg"])
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, render.BAR_W, 1920], fill=t["bar"])
    x = 172
    d.text((x, 228), str(q["no"]), font=render.font("CrimsonText-Italic.ttf", 93), fill=t["accent"], anchor="ls")
    d.text((x, 420), "解説", font=render.font("NotoSansJP.ttf", 86, 700), fill=t["accent"], anchor="ls")
    f = render.font("NotoSansJP.ttf", 56, 400)
    fb = render.font("NotoSansJP.ttf", 58, 700)
    lines = []
    if "options" in q:
        lines = [l for l in q["explanation"].split("\n") if l.strip() and not l.startswith("したがって")][:3]
    else:
        lines = [g for g in q.get("glossary", [])[:3]] + [q["explanation"].split("\n")[0]]
    y = 600
    for k, l in enumerate(lines):
        font = fb if ("options" not in q and k < len(lines) - 1) else f
        for w in wrap_mixed(d, l, font, 820):
            d.text((x, y), w, font=font, fill=t["ink"], anchor="ls")
            y += 84
        y += 30
    d.text((x, 1640), "くわしい解説・音声", font=render.font("NotoSansJP.ttf", 40, 500), fill=(110, 110, 110), anchor="ls")
    d.text((x, 1705), f"eng-navi.github.io/q/{q['no']}", font=render.font("NotoSansJP.ttf", 48, 700), fill=t["accent"], anchor="ls")
    im.save(path)
    return path


def countdown_frames(src, n, tmp):
    """問題の最後の画面に 3・2・1 を重ねた画像。"""
    from PIL import Image, ImageDraw, ImageFont
    last = tmp / f"{n}_last.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(Q_CUT - 0.15), "-i", str(src), "-frames:v", "1",
                    "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2", str(last)], check=True)
    out = []
    for k in (3, 2, 1):
        im = Image.open(last).convert("RGB")
        d = ImageDraw.Draw(im)
        d.ellipse([890, 1620, 1040, 1770], fill=(28, 31, 36))
        d.text((965, 1697), str(k), font=ImageFont.truetype(yc.HV, 92), fill=(255, 214, 80), anchor="mm")
        p = tmp / f"{n}_cd{k}.png"
        im.save(p)
        out.append(p)
    return out


def still(png, sec, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", "30", "-t", f"{sec:.3f}", "-i", str(png),
                    "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", str(out)], check=True)


def bgm_bed(total, path):
    """BGM:曲をクロスフェードでつないで、動画の長さまでくり返す。"""
    srcs = [str(ROOT / "assets" / "bgm" / f"{m}.mp3") for m in PLAYLIST]
    inputs, chain, prev = [], "", "[0:a]"
    for k, sp in enumerate(srcs):
        inputs += ["-i", sp]
    for k in range(1, len(srcs)):
        lab = f"[x{k}]"
        chain += f"{prev}[{k}:a]acrossfade=d=4{lab};"
        prev = lab
    once = path.with_suffix(".once.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", chain.rstrip(";"), "-map", prev,
                    "-ar", str(SR), "-ac", "2", str(once)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-stream_loop", "-1", "-i", str(once), "-t", f"{total:.3f}",
                    "-af", f"afade=t=in:d=2,afade=t=out:st={max(0, total - 4):.3f}:d=4", str(path)], check=True)
    once.unlink()


def build(theme_id):
    import numpy as np
    import soundfile as sf
    th = next(t for t in THEMES if t[0] == theme_id)
    tid, _, title_t, intro, head, sub, char, books, svcs, tags = th
    nos = items(th)
    if len(nos) < 8:
        sys.exit(f"{tid}:問題が少なすぎます({len(nos)}問)")
    Q = {q["no"]: q for q in json.loads((ROOT / "quizzes.json").read_text())}
    tmp = OUT / f"_t_{tid}"
    tmp.mkdir(parents=True, exist_ok=True)
    segs, voice_track, chapters, t = [], [], [], 0.0

    def add_seg(path, sec):
        nonlocal t
        segs.append(path)
        t += sec

    for k, n in enumerate(nos, 1):
        q = Q[n]
        if (k - 1) % 5 == 0:
            chapters.append((t, k, n))
        src = ROOT / "out" / "eng_navi" / f"q{n}.mp4"
        qv = tmp / f"{n}_q.mp4"  # 問題(元のショートの映像だけ。「答えはコメント欄で」が出る前で切る。音は全体の BGM に)
        if not qv.exists():
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-t", str(Q_CUT), "-i", str(src), "-vf",
                            "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", str(qv)], check=True)
        add_seg(qv, yc.duration(qv))
        for i, p in enumerate(countdown_frames(src, n, tmp)):  # 考える時間 3・2・1
            cd = tmp / f"{n}_cd{3 - i}.mp4"
            if not cd.exists():
                still(p, 1.0, cd)
            add_seg(cd, 1.0)
        text = sentence(q)
        a, b = voice(text, LILY), voice(text, GEORGE)
        gap = 0.5
        ans_sec = 0.5 + len(a) / SR + gap + len(b) / SR + 0.9
        voice_track.append((t + 0.5, a))
        voice_track.append((t + 0.5 + len(a) / SR + gap, b))
        apng = yc.answer_card(n, tmp / f"{n}_ans.png")
        av = tmp / f"{n}_ans.mp4"
        still(apng, ans_sec, av)
        add_seg(av, ans_sec)
        ev = tmp / f"{n}_exp.mp4"
        still(explain_card(q, tmp / f"{n}_exp.png"), 5.0, ev)
        add_seg(ev, 5.0)
        if k % yc.CTA_EVERY == 0 and k < len(nos):
            cpng = yc.cta_card(k, tmp / f"_cta{k}.png")
            cv = tmp / f"_cta{k}.mp4"
            still(cpng, yc.CTA_SEC, cv)
            add_seg(cv, yc.CTA_SEC)
    # 映像をつなぐ
    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in segs))
    vid = tmp / "video.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(vid)], check=True)
    total = yc.duration(vid)
    # 声のトラック
    track = np.zeros(int(total * SR) + SR, np.float32)
    for st, clip in voice_track:
        i0 = int(st * SR)
        track[i0:i0 + len(clip)] += clip[: len(track) - i0]
    vwav = tmp / "voice.wav"
    sf.write(vwav, track, SR)
    bed = tmp / "bgm.wav"
    bgm_bed(total, bed)
    # BGM は小さめ+声の間はさらに下げる(サイドチェイン)→ 声と合わせる
    dst = OUT / f"theme_{tid}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(vid), "-i", str(bed), "-i", str(vwav), "-filter_complex",
                    "[1:a]volume=0.32[b];[2:a]aformat=channel_layouts=stereo,asplit=2[v1][v2];"
                    "[b][v1]sidechaincompress=threshold=0.015:ratio=10:attack=15:release=350[bd];"
                    "[bd][v2]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}",
                    "-movflags", "+faststart", str(dst)], check=True)
    yc.KINDS["_theme"] = dict(head=head, sub=sub, char=char)
    yc.thumbnail("_theme", 0, 0, OUT / f"theme_{tid}_thumb.jpg", label=f"{len(nos)}問")
    title = title_t.format(n=len(nos))
    chap = "\n".join(f"{yc.stamp(ct)} 第{k}問〜" for ct, k, _ in chapters)
    links = "\n".join(f"第{k}問(#{n}){Q[n].get('category') or 'イディオム'} → https://eng-navi.github.io/q/{n}/" for k, n in enumerate(nos, 1))
    music = "\n".join(f"Music: {CREDITS[m]} — Music from #Uppbeat (free for Creators!)" for m in PLAYLIST)
    desc = (f"📚 全問の答え・くわしい解説と音声は、無料のサイトで復習できます👇\nhttps://eng-navi.github.io/?utm_source=youtube\n\n"
            f"{intro}\n1問ずつ「問題 → 考える時間 → 答え(イギリス英語で2回読み上げ)→ 解説」の順に進みます。解説はスペースキーで止めてじっくりどうぞ。\n\n"
            f"{recs(books, svcs)}\n\n▼ チャプター\n{chap}\n\n▼ 問題ごとのくわしい解説(サイト)\n{links}\n\n{music}\n\n{tags}")
    tagline = ",".join(x.lstrip("#") for x in tags.split()) + ",英語学習,聞き流し,イギリス英語"
    (OUT / f"theme_{tid}.txt").write_text(f"タイトル:\n{title}\n\n説明欄({len(desc)}字):\n{desc}\n\nタグ(詳細設定の「タグ」にそのまま貼る):\n{tagline}\n")
    print(f"✓ theme_{tid}.mp4({yc.stamp(total)}・{len(nos)}問・説明欄 {len(desc)}字)")

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "list":
        for th in THEMES:
            print(th[0], len(items(th)))
    elif cmd == "build":
        build(sys.argv[2])
    elif cmd == "week":
        for th in THEMES:
            if not (OUT / f"theme_{th[0]}.mp4").exists() and len(items(th)) >= 8:
                build(th[0])
