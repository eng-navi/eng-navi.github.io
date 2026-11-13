"""@quizify_english の白い「英単語(初級)」リールを作る。1本に2語(受験・英検で問われるやさしめのコロケーション)。

1語ごとに 英語 → 日本語の意味 → 日本語の例文 → (考える間) → 英語の例文(女性)→ 英語の例文(男性)の順。黒とほぼ同じで、
英語の例文を2回読むのが違い。間と配置は 2024年の元動画(159・161)の4語分を 0.01 秒単位で測った値の平均。

  .venv-tts/bin/python quizify_white.py [番号...]   → out/quizify/white_<最初の番号>.mp4 と .txt(説明欄の全文)

作る前に quizify_words.json(白で使った単語)と照らし合わせ、同じ表現なら止まる。作った表現は「予定」として記録する。
"""
import subprocess
import tempfile

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont

import manga_reel as mr
import quizify_black as qb

ROOT, OUT, SR, W, H, FPS = qb.ROOT, qb.OUT, qb.SR, qb.W, qb.H, qb.FPS

# 声。英語1回目と日本語は黒と同じ。2回目は元動画と同じく低い男性(声くらべで本人が選んだ Charlie)
EN_VOICE, EN_SPEED = qb.EN_VOICE, qb.EN_SPEED        # Lily(イギリス・女性)
EN2_VOICE, EN2_SPEED = "IKne3meq5aSn9XLyUdCD", 0.94   # Charlie(男性)。元の読む長さに合わせて少しゆっくり
JA_VOICE, JA_SPEED = qb.JA_VOICE, qb.JA_SPEED        # Nanami(音読さんの「ななみ」)
# 音量(RMS)は黒と同じ。大きくすると山が抑えられて声が割れて聞こえるため
LEVEL = {EN_VOICE: 0.092, EN2_VOICE: 0.092, JA_VOICE: 0.163}

# 間(秒)
LEAD = 0.55        # 動画の頭 → 英語
WORD_MEAN = 0.95   # 英語 → 意味
MEAN_JA = 0.81     # 意味 → 日本語の例文
JA_EN = 1.58       # 日本語の例文 → 英語の例文(考える間)
EN_EN = 1.03       # 英語の例文(女性)→ 英語の例文(男性)
EN_NEXT = 0.90     # 英語の例文(男性)→ 次の英語
TAIL = 0.36        # 最後の英語の例文 → 動画の終わり
SHOW_EARLY = 0.12  # 意味・日本語の例文の画面は声より少し先
EN_EARLY = 0.07    # 英語の例文の画面
NEXT_AFTER = 0.38  # 英語の例文(男性)が終わってから次の画面へ

BG = (241, 244, 241)
INK = (17, 19, 17)
# フォントは元の Canva と同じ:英語 Cardo、日本語 筑紫A丸ゴシック(macOS の標準フォント。ダウンロードして使う)
TSUKUSHI = "/System/Library/AssetsV2/com_apple_MobileAsset_Font7/d9a8a6ae726910080d90232eaf0edb06da712758.asset/AssetData/TsukushiAMaruGothic.ttc"
NUM = qb.font("Cardo-Italic.ttf", 52)
TITLE = ImageFont.truetype(TSUKUSHI, 53, index=1)
MEAN = ImageFont.truetype(TSUKUSHI, 40, index=1)
JA = ImageFont.truetype(TSUKUSHI, 34, index=1)
EN = qb.font("Cardo-Bold.ttf", 44)

# 1本ずつ:紹介文とハッシュタグ(毎回書き下ろし)、2表現。英単語ターゲット1900 の見出し語から、受験・英検で問われる形にして作る(例文はオリジナル)
# 表現:番号, 表現, 画面の意味, 読む意味, 日本語の例文, 英語の例文, 豆知識(説明欄に載せる)
REELS = [
    dict(intro="前置詞までセットで覚えよう✍️\n今日は「関わる」「関係がある」の2つです。", tags="#英単語 #英語学習 #大学受験",
         items=[
             (163, "be involved in A", "〜に関わる、〜に参加する", "に関わる",
              "多くの学生がボランティア活動に関わっている。", "Many students are involved in volunteer work.",
              ["前置詞は in。「〜の中に入り込んでいる」イメージ", "get involved in A で「〜に関わるようになる」", "名詞は involvement(関与)"]),
             (164, "be related to A", "〜に関係がある", "に関係がある",
              "健康は睡眠と深く関係している。", "Health is closely related to sleep.",
              ["前置詞は to。with にしないよう注意", "closely(密接に)と一緒によく使います", "名詞は relation / relationship(関係)"]),
         ]),
    dict(intro="入試の並べかえ問題でよく出る形です📝\n今日は「比べる」「勧める」の2つ。", tags="#英語学習 #英検2級 #共通テスト",
         items=[
             (165, "compare A with B", "AをBと比べる", "AをBと比べる",
              "他人と自分を比べないで。", "Don't compare yourself with others.",
              ["with の代わりに to も使えます", "compare A to B は「AをBにたとえる」の意味にもなります", "名詞は comparison(比較)"]),
             (166, "encourage A to do", "Aに〜するよう勧める、励ます", "Aにするよう勧める",
              "先生は私に留学するよう勧めた。", "My teacher encouraged me to study abroad.",
              ["to のあとは動詞の原形", "反対は discourage A from doing(Aに〜する気をなくさせる)", "名詞は encouragement(励まし)"]),
         ]),
    dict(intro="「人+to+動詞」の形、セットで言えるかな?🗣️\n今日は「許す」「影響を与える」の2つです。", tags="#英単語 #英文法 #大学受験",
         items=[
             (167, "allow A to do", "Aが〜するのを許す", "Aがするのを許す",
              "父は私が夜遅くに出かけるのを許さない。", "My father doesn't allow me to go out late at night.",
              ["let A do と同じ意味。let のあとは to がつきません", "受け身は A is allowed to do(Aは〜してよい)", "名詞は allowance(おこづかい、許容量)"]),
             (168, "have an effect on A", "〜に影響を与える", "に影響を与える",
              "音楽は気分に良い影響を与える。", "Music has a good effect on our mood.",
              ["前置詞は on。good / bad / big などを effect の前に入れられます", "動詞の affect(影響する)と混同しやすいので注意", "形容詞は effective(効果的な)"]),
         ]),
    dict(intro="英作文でそのまま使える表現です✨\n今日は「重要な役割」「似ている」の2つ。", tags="#英作文 #英語学習 #英検",
         items=[
             (169, "play an important role in A", "〜で重要な役割を果たす", "で重要な役割を果たす",
              "睡眠は記憶において重要な役割を果たす。", "Sleep plays an important role in memory.",
              ["role(役割)と roll(転がる)は同じ発音", "important の代わりに key / major もよく使います", "part を使って play an important part in A とも言えます"]),
             (170, "be similar to A", "〜に似ている", "に似ている",
              "私の意見はあなたの意見に似ている。", "My opinion is similar to yours.",
              ["前置詞は to。with にしないよう注意", "yours(あなたのもの)のように、比べるものの形をそろえます", "名詞は similarity(類似点)"]),
         ]),
    dict(intro="to のあとに来る形、まちがえやすいので注意⚠️\n今日は「反対する」「決める」の2つです。", tags="#英文法 #英単語 #大学受験",
         items=[
             (171, "object to A", "〜に反対する", "に反対する",
              "多くの住民が新しい道路の計画に反対した。", "Many residents objected to the new road plan.",
              ["この to は前置詞。動詞を続けるときは object to doing の形", "名詞の object(物、目的)とアクセントの位置が違います", "名詞は objection(反対)"]),
             (172, "decide to do", "〜することに決める", "することに決める",
              "私は毎朝走ることに決めた。", "I decided to run every morning.",
              ["to のあとは動詞の原形。decide doing とは言いません", "decide not to do で「〜しないことに決める」", "名詞は decision(決定)"]),
         ]),
    dict(intro="自己紹介や面接でも使える表現です🙋\n今日は「興味がある」「危険を減らす」の2つ。", tags="#英会話 #英語学習 #英検2級",
         items=[
             (173, "have an interest in A", "〜に興味がある", "に興味がある",
              "彼は日本の歴史に興味を持っている。", "He has an interest in Japanese history.",
              ["be interested in A と同じ意味", "前置詞は in", "interesting(おもしろい)と interested(興味がある)の違いも大切"]),
             (174, "reduce the risk of A", "〜の危険を減らす", "の危険を減らす",
              "運動はけがの危険を減らす。", "Exercise reduces the risk of injury.",
              ["risk of A で「Aの危険」", "反対は increase the risk of A(〜の危険を高める)", "名詞は reduction(減少)"]),
         ]),
    dict(intro="長文読解で意味をまちがえやすい表現です🔍\n今日は「予定である」「避ける」の2つ。", tags="#長文読解 #英単語 #大学受験",
         items=[
             (175, "be due to do", "〜する予定である", "する予定である",
              "会議は3時に始まる予定だ。", "The meeting is due to start at three.",
              ["due to A(Aのせいで)と形が似ているので注意", "締め切りの「〜が期限で」の意味もあります", "The report is due tomorrow.(レポートは明日が締め切り)"]),
             (176, "avoid doing", "〜するのを避ける", "するのを避ける",
              "彼は甘い物を食べるのを避けている。", "He avoids eating sweets.",
              ["avoid のあとは doing。to do は使いません", "同じ仲間:enjoy / finish / mind doing", "形容詞は unavoidable(避けられない)"]),
         ]),
    dict(intro="動名詞か不定詞か、迷いやすい形です🤔\n今日は「〜しようかと考える」「影響を与える」の2つ。", tags="#英文法 #英単語 #大学受験",
         items=[
             (177, "consider doing", "〜しようかと考える", "しようかと考える",
              "私は留学しようかと考えている。", "I'm considering studying abroad.",
              ["consider のあとは doing。to do にしないよう注意", "名詞は consideration(考慮)", "take A into consideration で「Aを考慮に入れる」"]),
             (178, "have an influence on A", "〜に影響を与える", "に影響を与える",
              "その先生は私の人生に大きな影響を与えた。", "The teacher had a great influence on my life.",
              ["前置詞は on", "effect は「結果としての影響」、influence は「人や考え方への影響」のイメージ", "形容詞は influential(影響力のある)"]),
         ]),
    dict(intro="to のあとの形、セットで言えるかな?🗣️\n今日は「〜しがち」「〜することを求められる」の2つです。", tags="#英単語 #英文法 #英検2級",
         items=[
             (179, "tend to do", "〜しがちである、〜する傾向がある", "しがちである",
              "私は週末に夜ふかししがちだ。", "I tend to stay up late on weekends.",
              ["to のあとは動詞の原形", "名詞は tendency(傾向)", "have a tendency to do でも同じ意味"]),
             (180, "be required to do", "〜することを求められる", "することを求められる",
              "乗客はシートベルトを締めることが求められている。", "Passengers are required to wear seat belts.",
              ["require A to do(Aに〜することを求める)の受け身", "名詞は requirement(必要条件)", "TOEIC の注意書きによく出ます"]),
         ]),
    dict(intro="入試・英検でよく問われる形です📝\n今日は「AをBと言う」「〜から利益を得る」の2つ。", tags="#英単語 #大学受験 #共通テスト",
         items=[
             (181, "describe A as B", "AをBと言う、AをBだと説明する", "AをBと言う",
              "多くの人が彼を天才だと言う。", "Many people describe him as a genius.",
              ["as のあとには名詞や形容詞", "regard A as B(AをBとみなす)と同じ形", "名詞は description(説明)"]),
             (182, "benefit from A", "〜から利益を得る、〜で得をする", "から利益を得る",
              "生徒たちは新しいプログラムから恩恵を受けた。", "Students benefited from the new program.",
              ["前置詞は from", "benefit A で「Aのためになる」の形も", "形容詞は beneficial(有益な)"]),
         ]),
    dict(intro="会話でも長文でも使える表現です✨\n今日は「〜に限られる」「何があっても」の2つ。", tags="#英単語 #英会話 #英検2級",
         items=[
             (183, "be limited to A", "〜に限られている", "に限られている",
              "参加者は30人に限られている。", "The number of participants is limited to thirty.",
              ["前置詞は to", "limited edition で「限定版」", "名詞は limit(限度)・limitation(制限)"]),
             (184, "no matter what", "何があっても、たとえ何が〜でも", "何があっても",
              "何があっても、あなたの味方だよ。", "I'll support you no matter what.",
              ["no matter what happens(何が起きても)の happens が省略された形", "no matter how / where / who も同じ仲間", "whatever とほぼ同じ意味"]),
         ]),
    dict(intro="人との関わりで使える熟語です🤝\n今日は「〜に我慢強い」「〜の観点から」の2つ。", tags="#英単語 #英検2級 #大学受験",
         items=[
             (185, "be patient with A", "Aに対して我慢強い、辛抱強い", "に我慢強い",
              "その先生は生徒にとても辛抱強い。", "The teacher is very patient with her students.",
              ["前置詞は with", "名詞の patient は「患者」の意味", "反対は impatient(短気な)"]),
             (186, "in terms of A", "Aの観点から、Aの点では", "の観点から",
              "値段の点では、こちらの方がいい。", "In terms of price, this one is better.",
              ["長文で「〜の面では」と訳すとスムーズ", "term は「言葉、期間、条件」など意味が多い", "in the long term で「長い目で見れば」"]),
         ]),
    dict(intro="TOEICにも出る、使える熟語です💼\n今日は「〜に都合がつく」「〜しようと申し出る」の2つ。", tags="#英単語 #TOEIC #英語学習",
         items=[
             (187, "be available for A", "Aに都合がつく、Aに対応できる", "に都合がつく",
              "明日の打ち合わせに都合はつきますか。", "Are you available for a meeting tomorrow?",
              ["人に使うと「手が空いている」", "物に使うと「手に入る、利用できる」", "名詞は availability(空き状況)"]),
             (188, "offer to do", "〜しようと申し出る", "しようと申し出る",
              "彼は駅まで送ると申し出てくれた。", "He offered to drive me to the station.",
              ["to のあとは動詞の原形", "offer A B で「AにBを提供する」の形も", "名詞で「申し出、提案」"]),
         ]),
    dict(intro="英作文でも使える熟語です✍️\n今日は「きっと〜する」「心に留めておく」の2つ。", tags="#英作文 #英単語 #英検2級",
         items=[
             (189, "be certain to do", "きっと〜する", "きっとする",
              "彼女はきっと試験に合格するだろう。", "She is certain to pass the exam.",
              ["be sure to do とほぼ同じ意味", "be certain of A で「Aを確信している」", "副詞は certainly(確かに)"]),
             (190, "bear A in mind", "Aを心に留めておく", "を心に留めておく",
              "安全が第一だということを心に留めておいて。", "Please bear in mind that safety comes first.",
              ["keep A in mind と同じ意味", "A が長いときは bear in mind that ~ の形になる", "bear には「運ぶ、耐える」などの意味も"]),
         ]),
]
ITEMS = [it for r in REELS for it in r["items"]]


def frame(item, stage):
    """stage: word / mean / ja / en"""
    no, word, mean, _, ja, en = item[:6]
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((102, 176), str(no), font=NUM, fill=INK, anchor="ls")
    qb.spaced(d, (100, 449), "英単語（初級）", TITLE, INK, 0)
    if stage in ("word", "mean"):
        lines = qb.wrap(d, word, EN, 580)  # 右に余白を残して、それでも長い表現は2行に
        for i, line in enumerate(lines):
            d.text((103, 620 + i * 70), line, font=EN, fill=INK, anchor="ls")
        if stage == "mean":
            qb.spaced(d, (104, 785 + (len(lines) - 1) * 70), mean, MEAN, INK, 1)
        return im
    for i, line in enumerate(qb.wrap_ja(d, ja, JA, 545, 1)):
        qb.spaced(d, (101, 861 + i * 60), line, JA, INK, 1)
    if stage == "en":
        lines = qb.wrap(d, en, EN, 475)
        top = 658 - (len(lines) - 1) * 35
        for i, line in enumerate(lines):
            d.text((103, top + i * 70), line, font=EN, fill=INK, anchor="ls")
    return im


def build(items, out):
    qb.LEVEL.update(LEVEL)
    voice, cuts = [np.zeros(int(SR * LEAD), np.float32)], []  # cuts: (秒, item, stage)
    t, last_end = LEAD, 0.0
    for k, item in enumerate(items):
        _, word, _, said, ja, en = item[:6]
        parts = [(qb.tts(EN_VOICE, word, EN_SPEED), WORD_MEAN, "word"),
                 (qb.tts(JA_VOICE, said, JA_SPEED), MEAN_JA, "mean"),
                 (qb.tts(JA_VOICE, ja, JA_SPEED), JA_EN, "ja"),
                 (qb.tts(EN_VOICE, en, EN_SPEED), EN_EN, "en"),
                 (qb.tts(EN2_VOICE, en, EN2_SPEED), TAIL if k == len(items) - 1 else EN_NEXT, None)]
        for clip, gap, stage in parts:
            if stage == "word":
                cuts.append((0.0 if k == 0 else last_end + NEXT_AFTER, item, stage))
            elif stage:
                cuts.append((t - (EN_EARLY if stage == "en" else SHOW_EARLY), item, stage))
            voice += [clip, np.zeros(int(SR * gap), np.float32)]
            t += len(clip) / SR
            if stage is None:
                last_end = t
            t += gap
    audio = np.concatenate(voice)
    total = len(audio) / SR
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
        sf.write(wav.name, audio, SR)
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                              "-r", str(FPS), "-i", "-", "-i", wav.name, "-t", f"{total:.3f}",
                              "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-c:a", "aac", "-b:a", "192k",
                              "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
        frames = {}
        for n in range(int(round(total * FPS))):
            cur = max((c for c in cuts if c[0] <= n / FPS), key=lambda c: c[0])
            key = (cur[1][0], cur[2])
            if key not in frames:
                frames = {key: frame(cur[1], cur[2]).tobytes()}
            p.stdin.write(frames[key])
        p.stdin.close()
        p.wait()
    print(f"✓ {out.relative_to(ROOT)}({total:.2f}秒)")
    for c in cuts:
        print(f"  {c[0]:6.2f}  {c[1][0]} {c[2]}")


def caption_text(items, intro, tags):
    """説明欄。黒と同じ形(【番号】表現:意味 → 英文 → 訳 → 💡 豆知識)。空行には全角スペース。紹介文とハッシュタグは毎回書き下ろす。"""
    sp = "　　"
    out = [intro, sp, "--------------------------------------"]
    for no, word, mean, _, ja, en, tips in items:
        out += [f"【{no}】{word}:{mean}", en, ja, sp, "💡 豆知識", *[f"・{t}" for t in tips], "--------------------------------------"]
    return "\n".join(out + [sp, "保存して、あとで復習してね📌", sp, tags])


if __name__ == "__main__":
    import sys
    import quizify_words as qw
    want = {int(x) for x in sys.argv[1:]}
    reels = [r for r in REELS if not want or r["items"][0][0] in want]
    qw.guard("white", [(it[0], it[1]) for r in reels for it in r["items"]])  # 白で使った表現とかぶっていたら止める
    mr.load_env()
    for r in reels:
        out = OUT / f"white_{r['items'][0][0]}.mp4"
        build(r["items"], out)
        out.with_suffix(".txt").write_text(caption_text(r["items"], r["intro"], r["tags"]) + "\n")
        for it in r["items"]:
            qw.add("white", it[1], no=it[0])
