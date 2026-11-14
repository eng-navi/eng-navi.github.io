"""Ifverse 風のリスニングクイズ・ショート(英検2級〜準1級・10〜30秒)。参考動画の見せ方をまねた型。

    .venv-tts/bin/python if_short.py compound      # out/if_short/compound.mp4 と .txt(コメント欄用)

参考動画がリッチに見える理由と、この型での対応:
  ・2〜3秒ごとにカット(1行=1カット)         → SHORTS の shots に1行ずつ書く
  ・構図が毎回ちがう(顔・目・全身・2人・物・遠景) → type を face / eyes / full / two / insert / wide から選ぶ
  ・表情がころころ変わる                        → eyes(8種類)と mouth(6種類)
  ・字幕は1〜3語ずつ、大事な語は黄色             → ElevenLabs の単語ごとのタイミングで自動
  ・効果音(カットごとのシュッ、数字のポン、衝撃) → 自動で入れる
  ・数字が増えていく表示                         → hud
流れ:時計の 3・2・1 と問題 → 物語 → 2択+4・3・2・1 →「正解はコメント欄で」

台本のルール(全部の回で守る):
  ・正解は音声の言い換え。まちがいの選択肢に、音声と同じ単語を入れる(英検と同じ。聞けた人だけ当たる)
  ・正解は A と B を回ごとに入れ替える
  ・台本は8行前後、全体で25秒以内(超えたら警告を出す)
  ・テーマとは別に、英検2級〜1級の単語を毎回6〜8個まんべんなく入れ、hl(黄色の字幕)と gloss(コメント欄の単語リスト)に載せる
  ・問題の日本語は大きく上、英語は小さく下。改行位置は q_ja に \n で入れる

効果音:assets/sfx/ に whoosh / pop / boom / tick / laugh / cash / gasp / ding(.wav か .mp3)を置くとそちらを使う。
無いものはプログラムで作った音で代用する。カットに sfx="laugh" のように書くと、そのカットで鳴らす。
"""
import base64
import hashlib
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf

import manga_reel as mr

ROOT = Path(__file__).parent
V3D = ROOT / "video3d"
PUB = V3D / "public" / "if"
OUT = ROOT / "out" / "if_short"
CACHE = ROOT / "out" / "voice_cache"
SR = 44100
INTRO, CHOICE, END = 3.0, 4.2, 1.8
SPEED = 1.1
SFX_DIR = ROOT / "assets" / "sfx"
MAX_SEC = 25

SHORTS = {
    "compound": dict(
        voice="nPczCjzI2devNBz1zQrb",  # Brian
        q="Why did Sam's savings grow so rapidly?", q_ja="サムの貯金が、\nなぜ急に増えたの?",
        choices=["His colleagues invested in him.", "His gains kept producing new gains."], answer=2,
        answer_ja="利益が、次々と新しい利益を生み続けたから。", hook="貯金が毎日2倍になったら…?💰",
        hl=["savings", "deposit", "modest", "colleagues", "ridicule", "astonishing", "generate", "economists"],
        shots=[
            ("What if your savings doubled daily?", dict(type="face", bg="room", eyes="shock", mouth="o", hud="DAY 1 · $1")),
            ("Sam deposits a modest one dollar.", dict(type="insert", bg="dark", insert="coin", value="$1", sfx="ding")),
            ("Colleagues ridicule him.", dict(type="two", bg="office", eyes="worried", mouth="wavy", eyes2="squint", mouth2="grin", sfx="laugh")),
            ("Day fifteen: sixteen thousand dollars!", dict(type="eyes", bg="dark", eyes="shock", hud="DAY 15 · $16,384", cam="shake")),
            ("Day twenty-one: an astonishing million.", dict(type="insert", bg="bank", insert="phone", value="$1,048,576", hud="DAY 21", sfx="cash")),
            ("Returns generate more returns.", dict(type="insert", bg="bank", insert="chart", value="RETURNS → RETURNS")),
            ("Economists call it compound interest.", dict(type="face", bg="bank", eyes="glasses", mouth="grin", cam="pull")),
        ],
        ja=["もし貯金が毎日2倍になったら?", "サムは、ささやかな1ドルを預ける。", "同僚たちは彼をあざ笑う。", "15日目、1万6千ドル!",
            "21日目、驚きの100万ドル。", "利益がさらに利益を生む。", "経済学者はそれを「複利」と呼ぶ。"],
        gloss=["savings:貯金", "deposit:預金する", "modest:ささやかな、控えめな", "colleague:同僚", "ridicule:あざ笑う",
               "astonishing:驚くべき", "return:(投資の)利益", "generate:生み出す", "economist:経済学者",
               "compound interest:複利"],
        tags="#英語リスニング #英検準1級 #お金の勉強"),
    "spotlight": dict(
        voice="pFZP5JQG7iQjIQuC4Bku",  # Lily
        q="Why was Emma's worry unnecessary?", q_ja="エマの心配が\nいらなかったのはなぜ?",
        choices=["People notice us far less than we assume.", "Everyone was staring at her coffee."], answer=1,
        answer_ja="人は、私たちが思うほど他人を見ていないから。", hook="服にコーヒーをこぼしたら、みんな見てる…?☕",
        hl=["spills", "convinced", "staring", "crimson", "embarrassment", "hardly", "vastly", "overestimate", "observe"],
        shots=[
            ("Emma spills coffee on her shirt.", dict(type="full", bg="office", eyes="shock", mouth="o", color="#d6457a", sfx="gasp")),
            ("She's convinced everyone is staring.", dict(type="eyes", bg="dark", eyes="worried", cam="shake", color="#d6457a")),
            ("Her face turns crimson with embarrassment.", dict(type="face", bg="office", eyes="squint", mouth="wavy", color="#d6457a", rim="#ff5a5a")),
            ("In reality, hardly anyone noticed.", dict(type="two", bg="office", eyes="worried", mouth="flat", eyes2="normal", mouth2="smile", color="#d6457a")),
            ("We vastly overestimate how much others observe us.", dict(type="insert", bg="dark", insert="card", value="OVERESTIMATE")),
            ("Psychologists call it the spotlight effect.", dict(type="face", bg="office", eyes="glasses", mouth="smile", color="#d6457a", cam="pull")),
        ],
        ja=["エマはシャツにコーヒーをこぼす。", "みんなに見られていると思い込む。", "恥ずかしさで顔が真っ赤になる。",
            "実際には、ほとんど誰も気づいていなかった。", "私たちは、他人にどれだけ見られているかを大きく見積もりすぎる。", "心理学者はそれを「スポットライト効果」と呼ぶ。"],
        gloss=["spill:こぼす", "be convinced (that) ~:〜だと思い込む", "stare:じっと見る", "crimson:真っ赤な", "embarrassment:恥ずかしさ",
               "hardly:ほとんど〜ない", "vastly:大幅に", "overestimate:過大評価する", "observe:観察する"],
        tags="#英語リスニング #英検準1級 #心理学"),
    "twominute": dict(
        voice="nPczCjzI2devNBz1zQrb",
        q="What finally helped Ken start exercising?", q_ja="ケンが運動を\n始められたのはなぜ?",
        choices=["He spent thirty minutes at the gym.", "He made the first step ridiculously small."], answer=2,
        answer_ja="最初の一歩を、ばかばかしいほど小さくしたから。", hook="運動が続かない人、これ試して🏃",
        hl=["procrastinates", "daunting", "threshold", "trivial", "momentum", "consistency", "intensity"],
        shots=[
            ("Ken always procrastinates on exercise.", dict(type="full", bg="room", eyes="squint", mouth="flat")),
            ("Thirty minutes at the gym feels daunting.", dict(type="insert", bg="dark", insert="clock", value="30:00", sfx="boom")),
            ("So he lowers the threshold: two minutes.", dict(type="insert", bg="dark", insert="clock", value="2:00", sfx="ding")),
            ("Shoes on. One push-up. Done.", dict(type="face", bg="room", eyes="happy", mouth="grin", hud="DAY 1")),
            ("The trivial start builds momentum.", dict(type="wide", bg="street", eyes="happy", mouth="smile", hud="DAY 7", cam="pan")),
            ("Consistency beats intensity: the two-minute rule.", dict(type="face", bg="street", eyes="glasses", mouth="grin", cam="pull")),
        ],
        ja=["ケンはいつも運動を先延ばしにする。", "ジムで30分は、気が重い。", "そこで、ハードルを下げる。2分だけ。", "靴をはく。腕立て1回。終わり。",
            "ささいな始まりが、勢いを生む。", "激しさより継続。それが「2分ルール」。"],
        gloss=["procrastinate:先延ばしにする", "daunting:気が重くなる、ひるませる", "threshold:基準、しきい値", "trivial:ささいな",
               "momentum:勢い", "consistency:継続、一貫性", "intensity:激しさ"],
        tags="#英語リスニング #英検準1級 #自己啓発"),
    "sleep": dict(
        voice="pFZP5JQG7iQjIQuC4Bku",
        q="Why did Ana get a better score?", q_ja="アナのほうが\n点数が高かったのはなぜ?",
        choices=["Her brain kept learning while she rested.", "She stayed up all night reviewing."], answer=1,
        answer_ja="休んでいるあいだも、脳が学び続けていたから。", hook="徹夜 vs 早寝、点数が高いのはどっち?😴",
        hl=["cram", "consolidates", "neurons", "outperforms", "idle", "retain"],
        shots=[
            ("Two students cram for the same exam.", dict(type="two", bg="room", eyes="worried", mouth="flat", eyes2="normal", mouth2="smile", color2="#d6457a")),
            ("Lee stays up all night.", dict(type="eyes", bg="dark", eyes="squint", hud="3:00 AM")),
            ("Ana goes to bed early.", dict(type="full", bg="bedroom", eyes="happy", mouth="smile", color="#d6457a")),
            ("Asleep, her neurons consolidate memories.", dict(type="insert", bg="dark", insert="brain", value="SAVING...")),
            ("Next day, Ana outperforms Lee.", dict(type="two", bg="room", eyes="shock", mouth="o", eyes2="happy", mouth2="grin", color2="#d6457a", hud="LEE 61 · ANA 92", sfx="gasp")),
            ("Sleep isn't idle. It's how we retain knowledge.", dict(type="face", bg="lab", eyes="glasses", mouth="smile", color="#d6457a", cam="pull")),
        ],
        ja=["2人の学生が同じ試験のために詰め込み勉強をする。", "リーは徹夜する。", "アナは早く寝る。", "眠っているあいだ、神経細胞が記憶を定着させる。",
            "翌日、アナはリーより良い成績をとる。", "睡眠はむだではない。知識を保つための時間だ。"],
        gloss=["cram:詰め込み勉強をする", "stay up all night:徹夜する", "consolidate:強化する、定着させる", "neuron:神経細胞",
               "outperform:〜より良い成績をあげる", "idle:何もしていない、むだな", "retain:保持する"],
        tags="#英語リスニング #英検準1級 #科学"),
}

# ---- 名探偵アイビーの謎解き(別アカウント・心理学)。声は Alice(イギリス英語・女性)で固定、語りは探偵の一人称 ----
IVY = dict(voice="Xb7hH8MSUJpSbSDYk0k2", account="ivy", kicker="名探偵アイビーの", title="謎解き", endText="推理の答えはコメント欄で🔍",
           bg1="#1f5a46", bg2="#0b1611", speed=1.1)
SHORTS.update({
    "case01_decoy": dict(IVY, caseNo="CASE #01",
        q="Why did large popcorn sales suddenly soar?", q_ja="Lサイズのポップコーンが\n急に売れたのはなぜ?",
        choices=["A pricey medium made the large look like a bargain.", "The large popcorn suddenly became cheaper."], answer=1,
        answer_ja="高いMサイズを置いたことで、Lサイズがお得に見えたから。",
        hl=["tripled", "baffled", "pricey", "bargain", "soared", "deliberately", "inferior", "steers", "decoy"],
        shots=[
            ("What if one tiny change tripled your sales?", dict(type="face", bg="dark", det=True, color="#2d6a4f", eyes="smug", mouth="smile", cam="whip")),
            ("A baffled owner couldn't sell large popcorn.", dict(type="insert", bg="room", insert="menu", value="SMALL $3|LARGE $7", cam="pan", stamp="CLUE 1")),
            ("So I added a pricey medium.", dict(type="lens", bg="room", insert="menu", value="SMALL $3|MEDIUM $6.50|LARGE $7", wipe="slide", focus=[640, 960])),
            ("Suddenly, the large seemed like a bargain.", dict(type="split", bg="dark", left="$6.50", right="$7", eyes="worried", mouth="flat", eyes2="happy", mouth2="grin", cam="tilt")),
            ("Sales soared overnight.", dict(type="insert", bg="bank", insert="chart", value="LARGE SALES", hud="+300%", cam="snap")),
            ("A deliberately inferior option steers our choice.", dict(type="ots", bg="room", det=True, color="#2d6a4f", eyes2="shock", mouth2="o", cam="push", mark=[560, 1140, 170])),
            ("Elementary: the decoy effect.", dict(type="silhouette", bg="dark", det=True, eyes="smug", wipe="iris", stamp="SOLVED")),
        ],
        ja=["もし、ほんの小さな変化で売上が3倍になったら?", "困り果てた店主は、Lサイズのポップコーンを売れずにいた。", "そこで私は、高めのMサイズを加えた。",
            "すると突然、Lサイズがお買い得に見えた。", "売上は一夜で急上昇。", "わざと劣った選択肢を置くと、私たちの選択は誘導される。", "初歩的なことだよ。「おとり効果」だ。"],
        gloss=["triple:3倍にする", "baffled:困惑した、途方に暮れた", "pricey:値段が高い", "bargain:お買い得品", "soar:急上昇する",
               "deliberately:わざと、意図的に", "inferior:劣った", "steer:(ある方向へ)導く", "decoy:おとり", "elementary:初歩的な"],
        grammar=["What if + 過去形 〜?", "「もし〜したらどうなる?」と、仮の話を持ちかける形。", "動詞を過去形(tripled)にすると「現実ではないけれど、もしも」の気持ちが出る。"],
        hook="映画館のポップコーン、Lだけ急に売れた理由は?🍿", tags="#英語リスニング #心理学 #謎解き"),
    "case02_mint": dict(IVY, caseNo="CASE #02",
        q="Why did Leo's tips suddenly increase?", q_ja="レオのチップが、\n急に増えたのはなぜ?",
        choices=["Customers loved the taste of the mints.", "Customers felt they owed him something."], answer=2,
        answer_ja="お客さんが「お返しをしなきゃ」と感じたから。",
        hl=["meager", "scrutinized", "sooner", "fourteen", "triggers", "urge", "reciprocate", "reciprocity"],
        shots=[
            ("Leo the waiter earned meager tips.", dict(type="full", bg="room", eyes="worried", mouth="flat", color="#2f6fd6", hud="TIPS $", wipe="iris")),
            ("So I scrutinized his routine.", dict(type="ots", bg="room", det=True, color="#2d6a4f", eyes2="worried", mouth2="flat", color2="#2f6fd6", cam="tilt")),
            ("My advice? Offer a free mint.", dict(type="face", bg="dark", det=True, color="#2d6a4f", eyes="smug", mouth="grin", cam="whip", stamp="CLUE 1")),
            ("No sooner had he done so than tips rose.", dict(type="insert", bg="bank", insert="coin", value="+3%", cam="push")),
            ("Two mints? Tips jumped fourteen percent.", dict(type="split", bg="dark", left="1 MINT", right="2 MINTS", eyes="normal", mouth="smile", eyes2="shock", mouth2="o", color="#2f6fd6", color2="#2f6fd6", cam="snap")),
            ("A gift triggers an urge to reciprocate.", dict(type="lens", bg="dark", insert="card", value="RECIPROCATE", focus=[540, 1010])),
            ("Case closed: reciprocity.", dict(type="silhouette", bg="dark", det=True, eyes="smug", wipe="iris", stamp="SOLVED")),
        ],
        ja=["ウェイターのレオは、わずかなチップしかもらえなかった。", "そこで私は、彼の仕事ぶりを細かく調べた。", "私の助言?無料のミントを出すこと。",
            "そうするとすぐに、チップが増えた。", "ミント2つなら?チップは14%も跳ね上がった。", "贈り物は、お返しをしたい衝動を引き起こす。", "事件解決。「返報性」だ。"],
        gloss=["meager:わずかな、乏しい", "scrutinize:細かく調べる", "routine:いつもの手順", "trigger:引き起こす",
               "urge:衝動", "reciprocate:お返しをする", "reciprocity:返報性、相互関係"],
        grammar=["No sooner had A 過去分詞 than B 過去形", "「AするとすぐにB」。No sooner が文頭に来るので、had he done のように語順が入れ替わる(倒置)。",
                 "No sooner had he done so than tips rose.(そうするとすぐに、チップが増えた)"],
        hook="ミントを1つ配っただけで、チップが増えた?🍬", tags="#英語リスニング #心理学 #謎解き"),
    "case03_foot": dict(IVY, caseNo="CASE #03",
        q="Why did the homeowners finally say yes?", q_ja="住人たちが最後に\nOKしたのはなぜ?",
        choices=["The tiny sticker was a modest gift.", "A small yes made the big yes easier."], answer=2,
        answer_ja="小さなお願いにOKしたことで、大きなお願いにもOKしやすくなったから。",
        hl=["lawn", "flatly", "modest", "favor", "complied", "commit", "strive", "consistent"],
        shots=[
            ("Would you allow an ugly sign on your lawn?", dict(type="face", bg="dark", det=True, color="#2d6a4f", eyes="smug", mouth="smile", cam="whip")),
            ("Most homeowners flatly refused.", dict(type="two", bg="street", det=True, color="#2d6a4f", eyes="worried", mouth="flat", eyes2="angry", mouth2="flat", hud="YES 17%", cam="pan")),
            ("So I began with a modest favor: a tiny sticker.", dict(type="lens", bg="street", insert="card", value="DRIVE SAFELY", focus=[540, 1010], wipe="slide")),
            ("Two weeks later, I asked for the sign.", dict(type="insert", bg="dark", insert="clock", value="2 WEEKS", cam="rise")),
            ("This time, most of them complied!", dict(type="split", bg="dark", left="17%", right="76%", eyes="worried", mouth="flat", eyes2="happy", mouth2="grin", cam="snap")),
            ("Once we commit, we strive to stay consistent.", dict(type="ots", bg="street", det=True, color="#2d6a4f", eyes2="normal", mouth2="smile", cam="tilt", mark=[560, 1140, 170])),
            ("The foot-in-the-door technique. Case closed.", dict(type="silhouette", bg="dark", det=True, eyes="smug", wipe="iris", stamp="SOLVED")),
        ],
        ja=["芝生に、見苦しい看板を置かせてくれる?", "ほとんどの住人は、きっぱり断った。", "そこで私は、ささやかなお願いから始めた。小さなシールだ。",
            "2週間後、看板をお願いした。", "今度は、ほとんどの人が応じた!", "いったん引き受けると、私たちは一貫した態度でいようと努める。", "「フット・イン・ザ・ドア」の手法。事件解決。"],
        gloss=["lawn:芝生", "homeowner:家主、住人", "flatly:きっぱりと", "modest:ささやかな", "favor:お願い", "comply:応じる、従う",
               "commit:(約束して)関わる", "strive:努力する", "consistent:一貫した", "technique:手法"],
        grammar=["Once + 主語 + 動詞, 〜", "「いったん〜すると」。once は「一度」のほかに、接続詞として「いったん〜すると」の意味になる。",
                 "Once we commit, we strive to stay consistent.(いったん引き受けると、一貫していようと努める)"],
        hook="小さなシール1枚で、OKが4倍に?🏠", tags="#英語リスニング #心理学 #謎解き"),
})

# ---- やさしい英語の科学クイズ(別アカウント)。英検3級〜準2級の単語、ゆっくり(0.85倍)、15秒前後。声は Sarah(アメリカ英語・女性)、博士のキャラ ----
SCI = dict(voice="EXAVITQu4vr4xnSDxMaL", account="sci", speed=0.85, kicker="やさしい英語の", title="科学クイズ", jaHints=True,
           intro=1.5, choice=3.2, end=1.4, endText="答えはコメント欄で👇", bg1="#1b4f7a", bg2="#0a1624")
SHORTS.update({
    "sci001_strawberry": dict(SCI, no="#001", mystery="strawberry",
        q="What is this?", q_ja="これ、なんでしょう?",
        choices=["A strawberry", "A tomato"], answer=1, answer_ja="イチゴ",
        hl=["sweet", "seeds", "outside"],
        shots=[
            ("It is red and sweet.", dict(type="insert", bg="dark", insert="strawberry", cam="pull", zoom=2.8)),
            ("It has about two hundred seeds.", dict(type="insert", bg="dark", insert="strawberry", hud="200 SEEDS", cam="push", zoom=1.9)),
            ("And the seeds are on the outside!", dict(type="face", bg="lab", sci=True, color="#f4f4f0", eyes="shock", mouth="o", cam="whip")),
        ],
        ja=["赤くて、甘い。", "種がおよそ200個ある。", "しかも、種が外側についている!"],
        gloss=["sweet:甘い", "seed:種", "outside:外側"],
        hook="これ、なんだかわかる?🔍", tags="#英語リスニング #やさしい英語 #科学クイズ"),
    "sci002_sky": dict(SCI, no="#002", mystery="prism",
        q="Why is the sky blue?", q_ja="空が青いのはなぜ?",
        choices=["The sea paints it blue.", "Blue light spreads out the most."], answer=2, answer_ja="青い光が、いちばん散らばるから。",
        hl=["sunlight", "colors", "spreads", "everywhere"],
        shots=[
            ("Sunlight has many colors.", dict(type="insert", bg="dark", insert="prism", cam="push")),
            ("Blue light spreads out the most.", dict(type="face", bg="lab", sci=True, color="#f4f4f0", eyes="happy", mouth="grin", cam="whip")),
            ("So we see blue everywhere!", dict(type="wide", bg="street", sci=True, color="#f4f4f0", eyes="happy", mouth="smile", cam="pan")),
        ],
        ja=["太陽の光には、たくさんの色がある。", "青い光が、いちばん散らばる。", "だから、どこを見ても青く見える!"],
        gloss=["sunlight:太陽の光", "color:色", "spread out:広がる、散らばる", "everywhere:どこでも"],
        hook="空が青い理由、英語で言える?☀️", tags="#英語リスニング #やさしい英語 #科学クイズ"),
})


def tts_words(voice, text, speed=None):
    """ElevenLabs で読み上げ、音声と単語ごとの時刻を返す(保存して使い回す)"""
    CACHE.mkdir(parents=True, exist_ok=True)
    speed = speed or SPEED
    key = hashlib.sha1(f"ts|{voice}|{speed}|{text}".encode()).hexdigest()[:14]
    js, mp3 = CACHE / f"ts_{key}.json", CACHE / f"ts_{key}.mp3"
    if not js.exists():
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128",
            data=json.dumps({"text": text, "model_id": "eleven_multilingual_v2",
                             "voice_settings": {"stability": 0.45, "similarity_boost": 0.75, "speed": speed}}).encode(),
            headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"})
        d = json.load(urllib.request.urlopen(req))
        mp3.write_bytes(base64.b64decode(d["audio_base64"]))
        js.write_text(json.dumps(d["alignment"]))
    al = json.loads(js.read_text())
    words, cur, st = [], "", None
    for ch, s, e in zip(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]):
        if ch == " ":
            if cur:
                words.append([cur, st, last])
            cur, st = "", None
            continue
        if st is None:
            st = s
        cur, last = cur + ch, e
    if cur:
        words.append([cur, st, last])
    return mp3, words


_SFX = {}


def sample(kind, dur):
    """assets/sfx/ に素材があればそれを、無ければ synth の音を返す"""
    if kind not in _SFX:
        f = next((p for p in [SFX_DIR / f"{kind}.wav", SFX_DIR / f"{kind}.mp3"] if p.exists()), None)
        if f:
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                                 capture_output=True, check=True).stdout
            _SFX[kind] = 0.6 * np.frombuffer(raw, np.float32)
        else:
            _SFX[kind] = synth(kind, dur)
    return _SFX[kind]


def synth(kind, dur):
    t = np.arange(int(SR * dur)) / SR
    if kind == "whoosh":  # 帯域を動かしたノイズ
        n = np.random.default_rng(1).standard_normal(len(t))
        env = np.sin(np.pi * t / dur) ** 2
        k = np.convolve(n, np.ones(30) / 30, "same")
        return (0.18 * k * env).astype(np.float32)
    if kind == "pop":
        return (0.28 * np.sin(2 * np.pi * (500 + 900 * t / dur) * t) * np.exp(-t * 25)).astype(np.float32)
    if kind == "boom":
        return (0.5 * np.sin(2 * np.pi * (90 - 40 * t) * t) * np.exp(-t * 6)).astype(np.float32)
    if kind == "ding":
        return (0.22 * (np.sin(2 * np.pi * 1320 * t) + 0.5 * np.sin(2 * np.pi * 1980 * t)) * np.exp(-t * 7)).astype(np.float32)
    if kind == "tick":
        return (0.25 * np.sin(2 * np.pi * 1400 * t) * np.exp(-t * 60)).astype(np.float32)
    return np.zeros(len(t), np.float32)


def comment(sc):
    """コメント欄の文。英文→和訳→注釈(1文に3個まで)→全角スペースの行(これが無いと Instagram で改行が消える)"""
    sp = "\u3000"
    left = list(sc["gloss"])
    out = [f"Q. {sc['q_ja'].replace(chr(10), '')}", sc["q"], sp,
           f"{'推理の答え' if sc.get('account') == 'ivy' else '答え'}:{'AB'[sc['answer'] - 1]}", sc["choices"][sc["answer"] - 1], sc["answer_ja"], sp, "【全文と和訳】", sp]
    for k, ((ln, _), ja) in enumerate(zip(sc["shots"], sc["ja"])):
        low = ln.lower()
        mine = [g for g in left if g.split(":")[0].split()[0].lower()[:5] in low][:3]
        left = [g for g in left if g not in mine]
        out += [f"{'①②③④⑤⑥⑦⑧⑨⑩'[k]} {ln}", ja] + [f"　▶ {g.replace(':', ' … ', 1)}" for g in mine] + [sp]
    if sc.get("grammar"):
        out += ["【今日の文の形】", sc["grammar"][0]] + sc["grammar"][1:] + [sp]
    out += ["🎧 わからなかった単語は保存して、もう一度聞いてみてね", sp, sc["tags"]]
    return "\n".join(out) + "\n"


MUSIC = "Music: The Waves / Otto.mp3 — Music from #Uppbeat (free for Creators!)"


def caption(sc):
    sp = "\u3000"
    return "\n".join([sc["hook"], sp, "🎧 25秒の英語、聞き取れる?", "AとBどっち?コメントで答えてね👇",
                      "正解・全文和訳・単語の意味はコメント欄に📌", sp, sc["tags"], sp, MUSIC])


def build(name):
    sc = SHORTS[name]
    mr.load_env()
    out_dir = ROOT / "out" / {"ivy": "ivy_short", "sci": "sci_short"}.get(sc.get("account"), "if_short")
    T_IN, T_CH, T_END = sc.get("intro", INTRO), sc.get("choice", CHOICE), sc.get("end", END)  # 冒頭・2択・最後の秒数(回ごとに変えられる)
    PUB.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [ln for ln, _ in sc["shots"]]
    mp3, words = tts_words(sc["voice"], " ".join(lines), sc.get("speed"))
    story = PUB / f"{name}_story.mp3"
    story.write_bytes(mp3.read_bytes())
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(story)],
                               capture_output=True, text=True).stdout)
    # 1行=1カット:その行の最初の単語の時刻で切り替える
    shots, wi = [], 0
    for k, (ln, spec) in enumerate(sc["shots"]):
        start = words[wi][1]
        wi += len(ln.split())
        shots.append({**spec, "start": T_IN + (0 if k == 0 else start - 0.08)})
    for k, s in enumerate(shots):
        end = shots[k + 1]["start"] if k + 1 < len(shots) else T_IN + dur + 0.3
        s["dur"] = round(end - s["start"], 3)
        s["start"] = round(s["start"], 3)
    choice_at = T_IN + dur + 0.3
    total = choice_at + T_CH + T_END
    hl = [h.lower() for h in sc["hl"]]
    wlist = [dict(text=w, start=round(s, 3), end=round(e, 3),
                  hl=any("".join(c for c in w.lower() if c.isalpha()).startswith(h[:5]) for h in hl)) for w, s, e in words]
    if sc.get("jaHints"):  # 黄色の単語の下に、日本語を小さく出す(gloss から)
        ja = {g.split(":")[0].lower(): g.split(":", 1)[1].split("、")[0] for g in sc["gloss"] if " " not in g.split(":")[0]}
        for w in wlist:
            if w["hl"]:
                bare = "".join(c for c in w["text"].lower() if c.isalpha())
                w["ja"] = next((v for k, v in ja.items() if bare.startswith(k[:5])), None)
    # 効果音:カットごとにシュッ、数字が出たらポン、目のアップはドン
    sfx = np.zeros(int(SR * (total + 1)), np.float32)

    def put(a, t):
        i = int(t * SR)
        sfx[i:i + len(a)] += a[:len(sfx) - i]
    for s in shots:
        put(sample("whoosh", 0.35), max(0, s["start"] - 0.12))
        if s.get("hud"):
            put(sample("pop", 0.15), s["start"] + 0.1)
        if s["type"] == "eyes":
            put(sample("boom", 0.6), s["start"])
        if s.get("sfx"):
            put(sample(s.pop("sfx"), 0.5), s["start"] + 0.05)
    put(sample("boom", 0.6), 0.0)
    put(sample("whoosh", 0.35), 0.2)
    for k in range(int(T_IN + 0.5)):
        put(sample("tick", 0.06), k * 1.0)
    for k in range(int(T_CH)):
        put(sample("tick", 0.06), choice_at + k * 1.0)
    put(sample("whoosh", 0.35), choice_at + T_CH - 0.05)  # 「コメント欄で」がシュッと入る
    sf.write(PUB / f"{name}_sfx.wav", sfx, SR)
    bgm = PUB / "bgm.mp3"
    if not bgm.exists():
        src = ROOT / "docs" / "bgm" / "the-waves.mp3"
        bgm.write_bytes((src if src.exists() else ROOT / "assets" / "manga_bgm" / "cozy-places.mp3").read_bytes())
    tick = PUB / "tick.wav"
    sf.write(tick, np.zeros(int(SR * 0.1), np.float32), SR)  # 時計の音は sfx に入れたので無音
    props = dict(q=sc["q"], q_ja=sc["q_ja"], choices=sc["choices"], answer=sc["answer"], words=wlist, intro=T_IN,
                 scenes=[], shots=shots, choiceAt=round(choice_at, 3), answerAt=round(choice_at + T_CH, 3), total=round(total, 3),
                 story=f"if/{story.name}", sfx=f"if/{name}_sfx.wav", tick="if/tick.wav", bgm="if/bgm.mp3",
                 choiceSec=int(T_CH), **{k: sc[k] for k in ("kicker", "title", "caseNo", "endText", "bg1", "bg2", "no", "mystery", "jaHints") if k in sc})
    pf = out_dir / f"{name}.json"
    pf.write_text(json.dumps(props, ensure_ascii=False))
    out = out_dir / f"{name}.mp4"
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "IfShort", str(out), f"--props={pf}"], cwd=V3D, check=True,
                   stdout=subprocess.DEVNULL)
    out.with_suffix(".txt").write_text(comment(sc))
    warn = f"  ⚠ {MAX_SEC}秒を超えています。台本を短くしてください" if total > MAX_SEC else ""
    print(f"✓ {out}({total:.1f}秒・{len(shots)}カット){warn}")


if __name__ == "__main__":
    for n in (sys.argv[1:] or ["compound"]):
        build(n)
