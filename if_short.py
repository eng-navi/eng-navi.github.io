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

# ---- 25秒リスニングクイズの新しい回(11/15〜):科学クイズと同じ 1.5秒の謎の絵で入る。mystery / hint を必ず書く
LISTEN = dict(voice="nPczCjzI2devNBz1zQrb", intro=1.5, mysteryBg="dark", kicker="リスニング", title="クイズ", speed=0.9, gap=0.3)  # 少しゆっくり(約115〜120語/分)

# ---- 名探偵アイビーの謎解き(別アカウント・心理学)。声は Alice(イギリス英語・女性)で固定、語りは探偵の一人称 ----
IVY = dict(voice="Xb7hH8MSUJpSbSDYk0k2", account="ivy", intro=1.5, mysteryBg="room", kicker="名探偵アイビーの", title="謎解き", endText="推理の答えはコメント欄で🔍",
           bg1="#1f5a46", bg2="#0b1611", speed=0.9, gap=0.3)  # 11/15〜 少しゆっくり
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
    "case03_foot": dict(IVY, caseNo="CASE #03", mystery="card", mysteryValue="DRIVE SAFELY", hint="👂ヒント:2回目のお願いに注目",
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

# ---- やさしい英語の科学クイズ(別アカウント)。英検3級〜準2級の単語、ゆっくり(0.7倍+文のあいだに0.7秒、約105語/分)、短い2〜3文で15秒前後。声は Sarah(アメリカ英語・女性)、博士のキャラ ----
SCI = dict(voice="EXAVITQu4vr4xnSDxMaL", account="sci", speed=0.7, gap=0.7, bgm="cycles", kicker="やさしい英語の", title="科学クイズ", jaHints=True,
           intro=1.5, choice=3.2, end=1.4, endText="答えはコメント欄で👇", bg1="#1b4f7a", bg2="#0a1624")
SHORTS.update({
    "sci001_strawberry": dict(SCI, no="#001", mystery="strawberry",
        q="What is this?", q_ja="これ、なんでしょう?",
        choices=["A strawberry", "A tomato"], answer=1, answer_ja="イチゴ",
        hl=["sweet", "seeds", "outside"],
        shots=[
            ("It is red.", dict(type="insert", bg="dark", insert="strawberry", cam="pull", zoom=2.8)),
            ("It is sweet.", dict(type="insert", bg="dark", insert="strawberry", hud="200 SEEDS", cam="push", zoom=1.9)),
            ("Its seeds are on the outside!", dict(type="face", bg="lab", sci=True, color="#f4f4f0", eyes="shock", mouth="o", cam="whip")),
        ],
        ja=["赤い。", "甘い。", "種が外側についている!"],
        gloss=["sweet:甘い", "seed:種", "outside:外側"],
        hook="これ、なんだかわかる?🔍", tags="#英語リスニング #やさしい英語 #科学クイズ"),
    "sci002_sky": dict(SCI, no="#002", mystery="prism", bgm="vapour",
        q="Why is the sky blue?", q_ja="空が青いのはなぜ?",
        choices=["Sunlight is only blue.", "Blue light bounces around the most."], answer=2, answer_ja="青い光が、いちばんあちこちに跳ね返るから。",
        hl=["sunlight", "colors", "spreads", "looks"],
        shots=[
            ("Sunlight has many colors.", dict(type="insert", bg="dark", insert="prism", cam="push")),
            ("Blue light spreads out the most.", dict(type="face", bg="lab", sci=True, color="#f4f4f0", eyes="happy", mouth="grin", cam="whip")),
            ("So the sky looks blue!", dict(type="wide", bg="street", sci=True, color="#f4f4f0", eyes="happy", mouth="smile", cam="pan")),
        ],
        ja=["太陽の光には、たくさんの色がある。", "青い光が、いちばん散らばる。", "だから、空は青く見える!"],
        gloss=["sunlight:太陽の光", "color:色", "spread out:広がる、散らばる", "look:〜に見える"],
        hook="空が青い理由、英語で言える?☀️", tags="#英語リスニング #やさしい英語 #科学クイズ"),
    "sci003_octopus": dict(SCI, no="#003", mystery="octopus", bgm="tunnel", cover=0,
        q="How many hearts does an octopus have?", q_ja="タコの心臓はいくつ?",
        choices=["Three", "Eight"], answer=1, answer_ja="3つ",
        hl=["arms", "blood", "heart"],
        shots=[
            ("An octopus has eight arms.", dict(type="insert", bg="dark", insert="octopus", value="8 ARMS", cam="pull")),
            ("Its blood is blue.", dict(type="face", bg="lab", sci=True, color="#f4f4f0", eyes="shock", mouth="o", cam="whip")),
            ("And it has more than one heart!", dict(type="insert", bg="dark", insert="octopus", value="? HEARTS", cam="push")),
        ],
        ja=["タコには、8本の腕(足)がある。", "血は青い。", "しかも、心臓が1つではない!"],
        gloss=["arm:腕(タコの足)", "blood:血", "heart:心臓"],
        hook="タコの心臓、いくつあると思う?🐙", tags="#英語リスニング #やさしい英語 #科学クイズ"),
})

# ---- ゆっくり英語の海クイズ(別アカウント)。海の生き物だけ。英検3級〜準1級の単語を混ぜる(やさしい2+難しい1、難しい語は日本語ヒント)
# 声は男女を交互に(George / Matilda)して反応を比べる。0.75倍+文のあいだ0.6秒
GEORGE, MATILDA = "JBFqnCBsd6RMkjVDRZzb", "XrExE9yKIg1WjnnlVkGX"
SEA = dict(account="sea", speed=0.7, gap=0.8, bgm="lantern", mysteryBg="ocean", kicker="ゆっくり英語の", title="海クイズ", jaHints=True,
           intro=1.5, choice=3.2, end=1.4, endText="答えはコメント欄で👇", bg1="#0b6a8f", bg2="#031a2c")
SHORTS.update({
    "sea001_seahorse": dict(SEA, voice=GEORGE, no="#001", mystery="seahorse", cover=0,
        q="Who gives birth to baby seahorses?", q_ja="タツノオトシゴの赤ちゃんを\n産むのはどっち?",
        choices=["The father", "The mother"], answer=1, answer_ja="お父さん",
        hl=["gentle", "pouch", "birth"],
        shots=[
            ("Seahorses are tiny, gentle fish.", dict(type="insert", bg="ocean", insert="seahorse", cam="pull", sonar="SEAHORSE")),
            ("The mother puts her eggs in the father's pouch.", dict(type="lens", bg="ocean", insert="seahorse", focus=[520, 950], wipe="slide")),
            ("Weeks later, he gives birth!", dict(type="insert", bg="ocean", insert="seahorse", value="DAD!", cam="snap")),
        ],
        ja=["タツノオトシゴは、小さくておだやかな魚。", "お母さんは、お父さんのおなかの袋に卵を入れる。", "数週間後、お父さんが出産する!"],
        gloss=["gentle:おだやかな", "pouch:(おなかの)袋", "give birth:出産する"],
        hook="タツノオトシゴ、産むのはどっち?🌊", tags="#英語リスニング #やさしい英語 #海の生き物"),
    "sea002_dolphin": dict(SEA, voice=MATILDA, no="#002", mystery="dolphin", cover=0, bgm="sailing",
        q="How do dolphins sleep?", q_ja="イルカは、\nどうやって眠る?",
        choices=["Half of the brain sleeps at a time.", "They stay alert and never rest."], answer=1, answer_ja="脳の半分ずつ眠る。",
        hl=["breathe", "rests", "alert"],
        shots=[
            ("Dolphins must breathe air.", dict(type="insert", bg="ocean", insert="dolphin", cam="pan", sonar="DOLPHIN")),
            ("One half of the brain rests.", dict(type="insert", bg="ocean", insert="brain", value="ZZZ…", cam="push", wipe="iris")),
            ("The other half stays alert!", dict(type="insert", bg="ocean", insert="dolphin", value="ON ALERT", cam="push")),
        ],
        ja=["イルカは、空気を吸わないといけない。", "脳の半分が休む。", "もう半分は、起きて見張っている!"],
        gloss=["breathe:呼吸する", "rest:休む", "alert:油断なく見張っている"],
        hook="イルカって、どうやって眠るの?🐬", tags="#英語リスニング #やさしい英語 #海の生き物"),
    "sea003_orca": dict(SEA, voice=GEORGE, no="#003", mystery="orca", cover=0, bgm="whales",
        q="What is special about orca families?", q_ja="シャチの家族の、\nふしぎなところは?",
        choices=["Scientists live with orca families.", "Each family has its own way of talking."], answer=2, answer_ja="家族ごとに、話し方がちがう。",
        hl=["close", "calls", "dialects"],
        shots=[
            ("Orcas live in close family groups.", dict(type="insert", bg="ocean", insert="orca", cam="pan", sonar="ORCA POD")),
            ("Each family has its own calls.", dict(type="insert", bg="ocean", insert="orca", value="♪ ♫ ♪", cam="push", wipe="slide")),
            ("Scientists call them dialects!", dict(type="insert", bg="ocean", insert="card", value="DIALECTS", cam="snap")),
        ],
        ja=["シャチは、仲のいい家族の群れでくらす。", "家族ごとに、自分たちの鳴き声がある。", "科学者は、それを「方言」と呼ぶ!"],
        gloss=["close:仲のいい、親しい", "call:鳴き声", "dialect:方言"],
        hook="シャチの家族には、○○がある?🐋", tags="#英語リスニング #やさしい英語 #海の生き物"),
})

# ==== 11/15 分 ====
SHORTS["twominute"].update({k: v for k, v in LISTEN.items() if k != "voice"}, mystery="clock", mysteryValue="2:00", hint="👂ヒント:3文目をよく聞こう")
LS = "#英語リスニング #英検準1級"
SHORTS.update({
    "sunkcost": dict(LISTEN, mystery="coin", mysteryValue="$20", hint="👂ヒント:3文目をよく聞こう",
        q="Why did Mia stay until the end of the boring movie?", q_ja="ミアが退屈な映画を\n最後まで見たのはなぜ?",
        choices=["She didn't want her ticket money to feel wasted.", "The movie got exciting after ten minutes."], answer=1,
        answer_ja="チケット代を無駄にしたと感じたくなかったから。",
        hl=["painfully", "dull", "wasting", "endured", "miserable", "fallacy", "dictate"],
        shots=[
            ("Mia paid twenty dollars for a movie ticket.", dict(type="insert", bg="room", insert="coin", value="$20", cam="whip")),
            ("Ten minutes in, it was painfully dull.", dict(type="face", bg="room", eyes="squint", mouth="flat", color="#d6457a", cam="pan")),
            ("Leaving felt like wasting her money.", dict(type="split", bg="dark", left="STAY", right="LEAVE", eyes="worried", mouth="wavy", color="#d6457a", color2="#d6457a", eyes2="normal", mouth2="flat", cam="push")),
            ("So she endured two more miserable hours.", dict(type="insert", bg="dark", insert="clock", value="+2 HOURS", cam="rise")),
            ("Economists call this the sunk cost fallacy.", dict(type="lens", bg="dark", insert="card", value="SUNK COST", focus=[540, 1010], wipe="slide")),
            ("Money already spent shouldn't dictate your next move.", dict(type="silhouette", bg="dark", eyes="smug", wipe="iris")),
        ],
        ja=["ミアは映画のチケットに20ドル払った。", "10分で、ひどく退屈になった。", "出ていくのは、お金を無駄にするように感じた。",
            "だから、つらい2時間をさらに耐えた。", "経済学者は、これを「サンクコストの誤り」と呼ぶ。", "もう使ったお金に、次の行動を決めさせてはいけない。"],
        gloss=["painfully:ひどく", "dull:退屈な", "waste:無駄にする", "endure:耐える", "miserable:みじめな、つらい",
               "sunk cost:埋没費用(取り戻せない出費)", "fallacy:誤った考え", "dictate:決定づける"],
        hook="つまらない映画、途中で帰れる?🎬", tags=f"{LS} #心理学"),
    "flamingo": dict(LISTEN, mystery="flamingo", cover=0, hint="👂ヒント:4文目と5文目に注目",
        q="Why are flamingos pink?", q_ja="フラミンゴが\nピンク色なのはなぜ?",
        choices=["They are born with pink feathers.", "Their food slowly colors their feathers."], answer=2,
        answer_ja="食べ物が、少しずつ羽を色づけるから。",
        hl=["chicks", "vivid", "lies", "diet", "devour", "algae", "pigments", "gradually", "fade"],
        shots=[
            ("Flamingo chicks are born grey.", dict(type="insert", bg="street", insert="flamingo", value="GREY?", cam="pull")),
            ("Yet adults glow a vivid pink.", dict(type="insert", bg="street", insert="flamingo", hud="PINK!", cam="snap")),
            ("The secret lies in their diet.", dict(type="face", bg="lab", eyes="smug", mouth="smile", cam="whip")),
            ("They devour tiny shrimp and algae.", dict(type="lens", bg="dark", insert="card", value="SHRIMP + ALGAE", focus=[540, 1010])),
            ("These contain natural pigments called carotenoids.", dict(type="insert", bg="lab", insert="card", value="CAROTENOIDS", cam="push", wipe="slide")),
            ("No shrimp, and their feathers gradually fade.", dict(type="insert", bg="street", insert="flamingo", value="FADING…", cam="pan")),
        ],
        ja=["フラミンゴのひなは、灰色で生まれる。", "でも大人は、あざやかなピンクに輝く。", "秘密は、食べ物にある。",
            "小さなエビや藻をたくさん食べる。", "それには「カロテノイド」という天然の色素が入っている。", "エビを食べないと、羽はだんだん色あせる。"],
        gloss=["chick:ひな", "vivid:あざやかな", "lie in A:Aにある", "diet:(ふだんの)食事", "devour:むさぼり食う", "algae:藻",
               "pigment:色素", "gradually:だんだん", "fade:色あせる"],
        hook="フラミンゴ、生まれた時は何色?🦩", tags=f"{LS} #科学"),
    "case04_anchor": dict(IVY, caseNo="CASE #04", mystery="card", mysteryValue="WAS $300", hint="🔍手がかり:新しい値札",
        q="Why did the $150 jacket suddenly sell out?", q_ja="150ドルのジャケットが\n急に売り切れたのはなぜ?",
        choices=["The old price made the real price look cheap.", "Customers gasped and the shop lowered the price."], answer=1,
        answer_ja="前の値段のせいで、今の値段が安く見えたから。",
        hl=["boutique", "scribbled", "glanced", "gasped", "vanished", "anchors", "judgment"],
        shots=[
            ("A boutique couldn't sell a hundred-fifty-dollar jacket.", dict(type="two", bg="office", det=True, color="#2d6a4f", eyes="normal", mouth="flat", eyes2="worried", mouth2="wavy", cam="pan")),
            ("So I scribbled a new tag: was three hundred.", dict(type="lens", bg="office", insert="card", value="WAS $300", focus=[540, 1010], stamp="CLUE 1")),
            ("Customers glanced at it and gasped.", dict(type="eyes", bg="dark", eyes="shock", cam="shake")),
            ("Within days, every jacket had vanished.", dict(type="insert", bg="bank", insert="chart", value="SOLD OUT", hud="0 LEFT", cam="snap")),
            ("That first number anchors our judgment.", dict(type="ots", bg="office", det=True, color="#2d6a4f", eyes2="shock", mouth2="o", cam="tilt", mark=[560, 1140, 170])),
            ("Elementary. The anchoring effect.", dict(type="silhouette", bg="dark", det=True, eyes="smug", wipe="iris", stamp="SOLVED")),
        ],
        ja=["あるブティックは、150ドルのジャケットを売れずにいた。", "そこで私は、新しい値札を走り書きした。「元値300ドル」。", "お客はちらっと見て、息をのんだ。",
            "数日のうちに、ジャケットはすべて消えていた。", "最初に見た数字が、私たちの判断をしばりつける。", "初歩的なことだよ。「アンカリング効果」だ。"],
        gloss=["boutique:洋品店", "scribble:走り書きする", "glance:ちらっと見る", "gasp:息をのむ", "vanish:消える",
               "anchor:つなぎとめる、固定する", "judgment:判断"],
        grammar=["無生物主語(物が主語の文)", "That first number anchors our judgment. のように「物」が主語になる形。", "「その数字のせいで、判断が固定される」と、原因として訳すと自然。"],
        hook="値札を1枚変えただけで、完売?🏷️", tags="#英語リスニング #心理学 #謎解き"),
    "case05_scarcity": dict(IVY, caseNo="CASE #05", mystery="card", mysteryValue="2 vs 10", hint="🔍手がかり:クッキーの数",
        q="Why did the cookies from the nearly empty jar taste better?", q_ja="ほぼ空のビンのクッキーが\nおいしく感じたのはなぜ?",
        choices=["The jar with two cookies held tastier ones.", "Rare things feel more valuable to us."], answer=2,
        answer_ja="少ないものほど、価値があるように感じるから。",
        hl=["identical", "rated", "scarce", "rarity", "precious", "hence", "scarcity"],
        shots=[
            ("Two jars held identical cookies.", dict(type="split", bg="dark", left="10", right="2", eyes="normal", mouth="smile", eyes2="normal", mouth2="smile", cam="push")),
            ("One was full. The other held just two.", dict(type="lens", bg="room", insert="card", value="ONLY 2 LEFT", focus=[540, 1010], wipe="slide")),
            ("Volunteers rated the scarce ones far tastier.", dict(type="two", bg="room", det=True, color="#2d6a4f", eyes="smug", mouth="smile", eyes2="happy", mouth2="grin", cam="pan", stamp="CLUE 1")),
            ("Rarity makes things seem more precious.", dict(type="insert", bg="dark", insert="card", value="RARE = PRECIOUS", cam="snap")),
            ("Hence, limited time only signs everywhere.", dict(type="insert", bg="street", insert="card", value="LIMITED TIME!", cam="pan")),
            ("Case closed: the scarcity principle.", dict(type="silhouette", bg="dark", det=True, eyes="smug", wipe="iris", stamp="SOLVED")),
        ],
        ja=["2つのビンに、まったく同じクッキーが入っていた。", "1つは満杯。もう1つは、たった2枚。", "参加者は、少ないほうをずっとおいしいと評価した。",
            "珍しさは、物をより貴重に見せる。", "だからこそ、あちこちに「期間限定」の看板がある。", "事件解決。「希少性の原理」だ。"],
        gloss=["identical:まったく同じ", "rate:評価する", "scarce:少ない、乏しい", "rarity:珍しさ", "precious:貴重な", "hence:それゆえ", "scarcity:希少性"],
        grammar=["Hence, 〜", "「それゆえ〜/だから〜」。前の文の結果を、かたい言い方でつなぐ。", "名詞だけを続けることもある(Hence, limited time only signs everywhere.)"],
        hook="クッキー2枚のほうが、おいしい?🍪", tags="#英語リスニング #心理学 #謎解き"),
    "case06_pygmalion": dict(IVY, caseNo="CASE #06", mystery="card", mysteryValue="GIFTED?", hint="🔍手がかり:先生に伝えた一言",
        q="Why did the randomly chosen students improve the most?", q_ja="適当に選ばれた生徒が\nいちばん伸びたのはなぜ?",
        choices=["Teachers expected more and helped them more.", "The students were gifted, as researchers knew."], answer=1,
        answer_ja="先生が期待して、その生徒をより手助けしたから。",
        hl=["random", "gifted", "flourished", "unconsciously", "encouraged", "expectations"],
        shots=[
            ("Researchers picked students completely at random.", dict(type="insert", bg="office", insert="card", value="RANDOM", cam="pan")),
            ("Yet they told teachers these kids were gifted.", dict(type="two", bg="office", det=True, color="#2d6a4f", eyes="smug", mouth="smile", eyes2="shock", mouth2="o", cam="push", stamp="CLUE 1")),
            ("By year's end, those students had flourished.", dict(type="insert", bg="bank", insert="chart", value="SCORES", hud="UP!", cam="snap")),
            ("Teachers had unconsciously encouraged them more.", dict(type="ots", bg="office", det=True, color="#2d6a4f", eyes2="happy", mouth2="grin", cam="tilt", mark=[560, 1140, 170])),
            ("High expectations can become reality.", dict(type="face", bg="dark", det=True, color="#2d6a4f", eyes="smug", mouth="grin", cam="whip")),
            ("Elementary: the Pygmalion effect.", dict(type="silhouette", bg="dark", det=True, eyes="smug", wipe="iris", stamp="SOLVED")),
        ],
        ja=["研究者は、生徒をまったくの無作為に選んだ。", "それなのに、先生には「この子たちは才能がある」と伝えた。", "年度末までに、その生徒たちはぐんと伸びていた。",
            "先生が、無意識にその生徒たちをより励ましていたのだ。", "高い期待は、現実になりうる。", "初歩的なことだよ。「ピグマリオン効果」だ。"],
        gloss=["at random:無作為に", "gifted:才能のある", "flourish:伸びる、栄える", "unconsciously:無意識に", "encourage:励ます", "expectation:期待"],
        grammar=["By + 時, 主語 + had + 過去分詞", "「〜までには…していた」。期限の時点で、もう完了していたことを表す(過去完了)。",
                 "By year's end, those students had flourished.(年度末までに、その生徒たちは伸びていた)"],
        hook="先生の思い込みで、成績が伸びる?📈", tags="#英語リスニング #心理学 #謎解き"),
    "sci004_onion": dict(SCI, no="#004", mystery="onion", bgm="cycles", cover=1,
        q="Why do onions make us cry?", q_ja="タマネギを切ると\n涙が出るのはなぜ?",
        choices=["The onion cries too.", "A gas from the onion hurts your eyes."], answer=2, answer_ja="タマネギから出る気体が、目をしげきするから。",
        hl=["gas", "tears", "wash"],
        shots=[
            ("Cut an onion.", dict(type="insert", bg="dark", insert="onion", cam="pull", zoom=1.6)),
            ("A gas comes out.", dict(type="insert", bg="dark", insert="onion", value="GAS!", cam="push")),
            ("Your eyes make tears to wash it away!", dict(type="face", bg="lab", sci=True, color="#f4f4f0", eyes="squint", mouth="wavy", cam="whip")),
        ],
        ja=["タマネギを切る。", "気体が出てくる。", "目は、それを洗い流すために涙を出す!"],
        gloss=["gas:気体、ガス", "tear:涙", "wash away:洗い流す"],
        hook="タマネギで涙が出る理由、知ってる?🧅", tags="#英語リスニング #やさしい英語 #科学クイズ"),
    "sci005_sunflower": dict(SCI, no="#005", mystery="sunflower", bgm="vapour", cover=0,
        q="Do young sunflowers move?", q_ja="若いヒマワリは\n動く?",
        choices=["Yes, they follow the sun.", "No, they never turn."], answer=1, answer_ja="はい、太陽を追いかける。",
        hl=["morning", "west", "night"],
        shots=[
            ("Young sunflowers face east in the morning.", dict(type="insert", bg="street", insert="sunflower", value="EAST", cam="pull")),
            ("They turn west with the sun.", dict(type="insert", bg="street", insert="sunflower", value="WEST", cam="pan")),
            ("At night, they turn back!", dict(type="face", bg="lab", sci=True, color="#f4f4f0", eyes="shock", mouth="o", cam="whip")),
        ],
        ja=["若いヒマワリは、朝は東を向く。", "太陽と一緒に、西へ向きを変える。", "夜になると、また東へ戻る!"],
        gloss=["morning:朝", "west:西", "night:夜"],
        hook="ヒマワリって、動くの?🌻", tags="#英語リスニング #やさしい英語 #科学クイズ"),
    "sci006_salt": dict(SCI, no="#006", mystery="card", mysteryValue="SALTY?", bgm="tunnel",
        q="Why is the sea salty?", q_ja="海の水が\nしょっぱいのはなぜ?",
        choices=["Rain is very salty.", "Rivers carry salt from rocks."], answer=2, answer_ja="川が、岩の塩分を運ぶから。",
        hl=["rocks", "carries", "rivers"],
        shots=[
            ("Rain falls on rocks.", dict(type="insert", bg="street", insert="card", value="RAIN → ROCKS", cam="pull")),
            ("It carries salt into rivers.", dict(type="insert", bg="ocean", insert="card", value="SALT → RIVERS", cam="pan")),
            ("Rivers bring the salt to the sea!", dict(type="face", bg="lab", sci=True, color="#f4f4f0", eyes="happy", mouth="grin", cam="whip")),
        ],
        ja=["雨が岩にふる。", "雨は塩分を川へ運ぶ。", "川がその塩を海へ運ぶ!"],
        gloss=["rock:岩", "carry:運ぶ", "river:川"],
        hook="海がしょっぱい理由、英語で言える?🌊", tags="#英語リスニング #やさしい英語 #科学クイズ"),
    "sea004_jellyfish": dict(SEA, voice=MATILDA, no="#004", mystery="jellyfish", cover=0, bgm="lantern",
        q="What can this jellyfish do?", q_ja="このクラゲが\nできることは?",
        choices=["It can become young again.", "It can grow bigger than a fingernail."], answer=1, answer_ja="若返ることができる。",
        hl=["tiny", "fingernail", "immortal"],
        shots=[
            ("This tiny jellyfish is smaller than a fingernail.", dict(type="insert", bg="ocean", insert="jellyfish", cam="pull", sonar="JELLYFISH")),
            ("When it gets old, it turns young again.", dict(type="lens", bg="ocean", insert="jellyfish", focus=[540, 880], wipe="slide")),
            ("Scientists call it the immortal jellyfish!", dict(type="insert", bg="ocean", insert="card", value="IMMORTAL", cam="snap")),
        ],
        ja=["この小さなクラゲは、つめよりも小さい。", "年をとると、また若い姿にもどる。", "科学者は、それを「不老不死のクラゲ」と呼ぶ!"],
        gloss=["tiny:とても小さい", "fingernail:(手の)つめ", "immortal:不死の"],
        hook="年をとると、若返るクラゲ?🪼", tags="#英語リスニング #やさしい英語 #海の生き物"),
})

# ---- ゆっくり英語の地理クイズ(試作)。衛星写真の地図アニメ。英検3級〜準1級の単語を混ぜる。声は Daniel(イギリス英語・ニュース風)
GEO = dict(voice="onwK4e9ZLuTAKqWW03F9", account="geo", speed=0.8, gap=0.4, bgm="tunnel", kicker="ゆっくり英語の", title="地理クイズ", jaHints=True,
           intro=1.5, choice=4.2, end=1.4, endText="答えはコメント欄で👇", bg1="#123a5a", bg2="#06131f", mystery="map")
SHORTS.update({
    "geo001_quake": dict(GEO, no="#001", mysteryMap=dict(from_=None), cover=3, hint="👂ヒント:3文目に注目",
        q="Why does Japan have so many earthquakes?", q_ja="日本で地震が\n多いのはなぜ?",
        choices=["Japan lies where moving plates collide.", "Japan has four huge mountains."], answer=1,
        answer_ja="動くプレートが、ぶつかり合う場所にあるから。",
        hl=["huge", "plates", "centimeters", "collide", "pressure", "slips", "quakes"],
        shots=[
            ("Japan sits on four huge plates.", dict(type="map", bg="dark", map={"from": [135, 30, 1.3], "to": [138, 36, 8], "hl": ["392"], "overlay": "jp_plates",
                                                                              "labels": [[138.5, 38, "JAPAN"]]})),
            ("They move a few centimeters each year.", dict(type="map", bg="dark", hud="≈ 8 cm / YEAR", map={"from": [140, 35, 7], "to": [140, 35, 7.6], "overlay": "jp_plates",
                "arrows": [[158, 36, 149, 37.5], [137, 23, 133.5, 27.5]],
                "labels": [[152, 31, "PACIFIC"], [132, 22, "PHILIPPINE SEA"], [125, 40, "EURASIAN"], [146, 46.5, "N. AMERICAN"]]})),
            ("Where they collide, pressure builds.", dict(type="map", bg="dark", map={"from": [141.5, 37.5, 13], "to": [142, 37.5, 16], "overlay": "jp_plates",
                "arrows": [[149, 37.5, 144.2, 37.8]], "labels": [[145.5, 41.2, "JAPAN TRENCH"]]})),
            ("Then the rock slips, and the ground shakes!", dict(type="map", bg="dark", map={"from": [138, 36, 9.5], "hl": ["392"], "shake": True,
                "dots": [[142.4, 38.3], [135.0, 34.6], [136.9, 37.5], [130.8, 32.8], [141.0, 42.7]]})),
            ("So Japan gets one-fifth of the world's strong quakes.", dict(type="map", bg="dark", hud="≈ 1/5 OF M6+ QUAKES", map={"from": [138, 36, 8], "to": [140, 33, 3.8], "hl": ["392"],
                "dots": [[142.4, 38.3], [135.0, 34.6], [136.9, 37.5], [130.8, 32.8]]})),
        ],
        ja=["日本は、4枚の巨大なプレートの上にある。", "プレートは、1年に数センチ動く。", "ぶつかり合う所で、圧力がたまる。",
            "そして岩がずれて、地面がゆれる!", "だから日本では、世界の強い地震の約5分の1が起きる。"],
        gloss=["huge:巨大な", "plate:プレート(地球の表面をおおう岩の板)", "collide:ぶつかり合う", "pressure:圧力", "slip:すべる、ずれる",
               "quake:地震(earthquake の短い言い方)"],
        hook="日本で地震が多い理由、英語で言える?🌏", tags="#英語リスニング #やさしい英語 #地理"),
})
SHORTS["geo001_quake"]["mysteryMap"] = {"from": [138, 36, 6], "hl": ["392"], "overlay": "jp_plates"}

SHORTS.update({
    "geo002_length": dict(GEO, no="#002", cover=3, hint="👂ヒント:2文目の数字に注目", mysteryMap={"from": [137, 35, 5], "hl": ["392"]},
        q="Why is January so different in Okinawa and Hokkaido?", q_ja="1月の沖縄と北海道、\nなぜこんなにちがう?",
        choices=["Sapporo enjoys mild weather in January.", "Japan stretches a long way from north to south."], answer=2,
        answer_ja="日本が、南北にとても長いから。",
        hl=["narrow", "stretches", "kilometers", "freezing", "meanwhile", "mild", "climates"],
        shots=[
            ("Japan is a long, narrow country.", dict(type="map", bg="dark", map={"from": [138, 36, 4.5], "to": [136, 35, 6], "hl": ["392"]})),
            ("It stretches about three thousand kilometers.", dict(type="map", bg="dark", hud="≈ 3,000 km", map={"from": [136, 35, 6], "hl": ["392"],
                "arrows": [[127.7, 26.2, 145.5, 44.2]]})),
            ("In January, Sapporo is freezing.", dict(type="map", bg="dark", map={"from": [142, 43.5, 9], "to": [141.4, 43.1, 15], "hl": ["392"],
                "dots": [[141.35, 43.06]], "labels": [[141.35, 44.0, "SAPPORO  −3°C"]]})),
            ("Meanwhile, Naha enjoys a mild seventeen degrees.", dict(type="map", bg="dark", map={"from": [128.5, 27, 9], "to": [127.7, 26.3, 15], "hl": ["392"],
                "dots": [[127.68, 26.21]], "labels": [[127.68, 27.0, "NAHA  17°C"]]})),
            ("One country, two completely different climates.", dict(type="map", bg="dark", map={"from": [135, 35, 7], "to": [135, 35, 5], "hl": ["392"],
                "dots": [[141.35, 43.06], [127.68, 26.21]], "labels": [[141.35, 44.6, "−3°C"], [127.68, 27.6, "17°C"]]})),
        ],
        ja=["日本は、細長い国だ。", "南北におよそ3,000キロのびている。", "1月の札幌は、凍えるほど寒い。",
            "一方で那覇は、おだやかな17度。", "1つの国に、まったくちがう2つの気候。"],
        gloss=["narrow:細長い、狭い", "stretch:のびる、広がる", "freezing:凍えるほど寒い", "meanwhile:一方で", "mild:おだやかな", "climate:気候"],
        hook="1月の沖縄と北海道、気温差は何度?❄️☀️", tags="#英語リスニング #やさしい英語 #地理"),
    "geo003_typhoon": dict(GEO, no="#003", cover=3, hint="👂ヒント:3文目と4文目に注目", mysteryMap={"from": [132, 22, 4.5], "dots": [[135, 15]]},
        q="Why do so many typhoons hit Japan in late summer?", q_ja="夏の終わりに台風が\n日本へ来るのはなぜ?",
        choices=["Warm seas create them, and winds carry them north.", "Japan heats the ocean near the Philippines."], answer=1,
        answer_ja="暖かい海で生まれ、風に北へ運ばれるから。",
        hl=["born", "tropical", "heats", "steering", "curve", "season"],
        shots=[
            ("Typhoons are born over warm tropical seas.", dict(type="map", bg="dark", map={"from": [134, 20, 4.5], "to": [135, 17, 6.5],
                "dots": [[135, 15], [140, 17], [130, 14]], "labels": [[136, 12, "WARM SEA"]]})),
            ("Late summer heats the ocean near the Philippines.", dict(type="map", bg="dark", hud="≈ 30°C", map={"from": [128, 15, 6], "to": [127, 15, 7],
                "hl": ["608"], "labels": [[122, 9, "PHILIPPINES"]]})),
            ("Steering winds then push them north.", dict(type="map", bg="dark", map={"from": [131, 22, 5.5], "dots": [[133, 16]],
                "arrows": [[133, 16, 128, 23], [128, 23, 129, 29]]})),
            ("Many curve straight toward Japan.", dict(type="map", bg="dark", map={"from": [132, 28, 5.5], "to": [134, 31, 6.5], "hl": ["392"],
                "arrows": [[128, 24, 131, 31], [131, 31, 139, 36]]})),
            ("So late summer means typhoon season.", dict(type="map", bg="dark", hud="AUG–SEP", map={"from": [134, 30, 5], "to": [134, 28, 4], "hl": ["392"],
                "dots": [[133, 16], [129, 24], [133, 31]]})),
        ],
        ja=["台風は、暖かい熱帯の海の上で生まれる。", "夏の終わりには、フィリピン近くの海があたたまる。", "そして、風が台風を北へ押し流す。",
            "その多くが、日本に向かってカーブする。", "だから夏の終わりは、台風の季節になる。"],
        gloss=["be born:生まれる", "tropical:熱帯の", "heat:温める", "steer:(向きを)導く", "curve:曲がる", "season:季節"],
        hook="台風が夏の終わりに来る理由、英語で言える?🌀", tags="#英語リスニング #やさしい英語 #地理"),
})

# ==== 11/16 分 ====
def _m(**kw): return kw
SHORTS.update({
    "inflation": dict(LISTEN, mystery="coin", mysteryValue="$100", hint="👂ヒント:3文目に注目",
        q="Why does the same $100 buy less over time?", q_ja="同じ100ドルで、\n買える物が減るのはなぜ?",
        choices=["Prices keep rising, so each dollar is worth less.", "The hundred-dollar bill itself shrinks over time."], answer=1,
        answer_ja="物価が上がり続けて、1ドルの価値が下がるから。",
        hl=["cart", "gradually", "economy", "steady", "inflation", "shrink", "value"],
        shots=[
            ("Ten years ago, a hundred dollars filled a whole cart.", dict(type="insert", bg="room", insert="coin", value="$100", cam="whip")),
            ("Today, the same bill buys far less.", dict(type="face", bg="room", eyes="shock", mouth="o", cam="pan")),
            ("Prices gradually rise across the economy.", dict(type="insert", bg="bank", insert="chart", value="PRICES", cam="push")),
            ("Economists call this steady climb inflation.", dict(type="lens", bg="dark", insert="card", value="INFLATION", focus=[540, 1010], wipe="slide")),
            ("Your money doesn't shrink, but its value does.", dict(type="split", bg="dark", left="$100", right="VALUE ↓", eyes="normal", mouth="flat", eyes2="worried", mouth2="wavy", cam="snap")),
            ("That's why saving alone isn't always enough.", dict(type="silhouette", bg="dark", eyes="smug", wipe="iris")),
        ],
        ja=["10年前、100ドルでカートがいっぱいになった。", "今は、同じお札で買える物がずっと少ない。", "物価は、経済全体でだんだん上がる。",
            "経済学者は、この着実な上昇を「インフレ」と呼ぶ。", "お金は縮まないが、その価値は縮む。", "だから、貯金だけでは足りないこともある。"],
        gloss=["cart:(買い物)カート", "gradually:だんだん", "economy:経済", "steady:着実な", "inflation:インフレ(物価の上昇)", "shrink:縮む", "value:価値"],
        hook="同じ100ドル、なぜ買える物が減る?💸", tags=f"{LS} #お金の勉強"),
    "exposure": dict(LISTEN, mystery="card", mysteryValue="25×", hint="👂ヒント:5文目に注目",
        q="Why did people like the faces they saw most often?", q_ja="よく見た顔ほど\n好きになったのはなぜ?",
        choices=["The faces belonged to twenty-five strangers.", "Seeing something often makes us like it more."], answer=2,
        answer_ja="何度も見るものほど、好きになるから。",
        hl=["flashed", "strangers", "rated", "familiar", "mere", "repetition", "breeds", "affection"],
        shots=[
            ("Researchers flashed photos of strangers' faces.", dict(type="insert", bg="office", insert="card", value="STRANGERS", cam="pan")),
            ("Some appeared once. Others, twenty-five times.", dict(type="split", bg="dark", left="1×", right="25×", eyes="normal", mouth="flat", eyes2="happy", mouth2="smile", cam="push")),
            ("Later, people rated how much they liked each face.", dict(type="two", bg="office", eyes="normal", mouth="smile", eyes2="happy", mouth2="grin", cam="pan")),
            ("The most familiar faces won, by far.", dict(type="insert", bg="bank", insert="chart", value="LIKING", cam="snap")),
            ("Mere repetition breeds affection.", dict(type="lens", bg="dark", insert="card", value="MERE EXPOSURE", focus=[540, 1010])),
            ("So keep showing up. It works.", dict(type="face", bg="room", eyes="smug", mouth="grin", cam="whip")),
        ],
        ja=["研究者は、知らない人の顔写真をさっと見せた。", "1回だけの顔もあれば、25回の顔もあった。", "あとで、それぞれの顔をどれくらい好きか評価した。",
            "いちばん見慣れた顔が、断然勝った。", "単なるくり返しが、好意を生む。", "だから、顔を出し続けよう。効果がある。"],
        gloss=["flash:さっと見せる", "stranger:知らない人", "rate:評価する", "familiar:見慣れた", "by far:断然", "mere:単なる", "repetition:くり返し",
               "breed:生む", "affection:好意"],
        hook="よく見る顔ほど、好きになる?👀", tags=f"{LS} #心理学"),
    "cat": dict(LISTEN, mystery="card", mysteryValue="CAT?", hint="👂ヒント:3文目に注目",
        q="How do cats land on their feet?", q_ja="猫が足から\n着地できるのはなぜ?",
        choices=["Its bendy back lets it turn in the air.", "It has a flexible head that absorbs the impact."], answer=1,
        answer_ja="柔らかい背中で、空中で体の向きを変えるから。",
        hl=["upside", "swiftly", "flexible", "spine", "twists", "absorb", "impact", "reflex"],
        shots=[
            ("When a cat falls upside down, watch closely.", dict(type="face", bg="room", eyes="shock", mouth="o", color="#f2994a", cam="whip")),
            ("First, it swiftly turns its head.", dict(type="eyes", bg="dark", eyes="shock", cam="shake")),
            ("Then its flexible spine twists the body.", dict(type="insert", bg="dark", insert="card", value="TWIST!", cam="snap")),
            ("Its legs stretch out to absorb the impact.", dict(type="full", bg="room", eyes="happy", mouth="grin", color="#f2994a", cam="rise")),
            ("Scientists call it the righting reflex.", dict(type="lens", bg="lab", insert="card", value="RIGHTING REFLEX", focus=[540, 1010])),
            ("It's built in from just a few weeks old.", dict(type="face", bg="room", eyes="smug", mouth="smile", color="#f2994a", cam="pull")),
        ],
        ja=["猫がさかさまに落ちるとき、よく見てほしい。", "まず、すばやく頭を回す。", "次に、柔らかい背骨が体をねじる。",
            "脚をのばして、衝撃を吸収する。", "科学者は、これを「立ち直り反射」と呼ぶ。", "生後わずか数週間で身につく。"],
        gloss=["upside down:さかさまに", "swiftly:すばやく", "flexible:柔らかい", "spine:背骨", "twist:ねじる", "absorb:吸収する", "impact:衝撃", "reflex:反射"],
        hook="猫が足から着地できる理由、知ってる?🐈", tags=f"{LS} #科学"),
    "case07_halo": dict(IVY, caseNo="CASE #07", mystery="card", mysteryValue="WARM / COLD", hint="🔍手がかり:2本のビデオのちがい",
        q="Why did students rate the same lecturer so differently?", q_ja="同じ講師なのに\n評価が分かれたのはなぜ?",
        choices=["Both classes adored his accent.", "His friendliness shaped how they saw everything else."], answer=2,
        answer_ja="親しみやすさが、ほかの見方まで左右したから。",
        hl=["lecturer", "distant", "adored", "accent", "trait", "impression", "halo"],
        shots=[
            ("Two classes watched the same lecturer on video.", dict(type="two", bg="office", det=True, color="#2d6a4f", eyes="normal", mouth="flat", eyes2="normal", mouth2="smile", cam="pan")),
            ("In one clip, he was warm and friendly.", dict(type="face", bg="office", eyes="happy", mouth="grin", cam="push")),
            ("In the other, he seemed cold and distant.", dict(type="face", bg="dark", eyes="squint", mouth="flat", cam="pull")),
            ("The warm group adored even his accent.", dict(type="insert", bg="dark", insert="card", value="♥ ACCENT", cam="snap", stamp="CLUE 1")),
            ("One good trait colored their whole impression.", dict(type="ots", bg="office", det=True, color="#2d6a4f", eyes2="shock", mouth2="o", cam="tilt", mark=[560, 1140, 170])),
            ("Elementary: the halo effect.", dict(type="silhouette", bg="dark", det=True, eyes="smug", wipe="iris", stamp="SOLVED")),
        ],
        ja=["2つのクラスが、同じ講師のビデオを見た。", "一方のビデオでは、彼は温かく親しみやすかった。", "もう一方では、冷たくよそよそしく見えた。",
            "「温かい」ほうを見たクラスは、彼のなまりまで気に入った。", "1つの良い特徴が、印象全体を染めた。", "初歩的なことだよ。「ハロー効果」だ。"],
        gloss=["lecturer:講師", "distant:よそよそしい", "adore:大好きである", "accent:なまり", "trait:特徴", "impression:印象", "halo:後光"],
        grammar=["one 〜, the other …", "2つのうち「一方は〜、もう一方は…」。In one clip, ... In the other, ... のように使う。", "3つ以上なら one 〜, another …, the others … になる。"],
        hook="同じ講師、評価が真っ二つ?🎓", tags="#英語リスニング #心理学 #謎解き"),
    "case08_towels": dict(IVY, caseNo="CASE #08", mystery="card", mysteryValue="MOST GUESTS…", hint="🔍手がかり:書き直したカード",
        q="Why did more hotel guests reuse their towels?", q_ja="ホテルの客が\nタオルを再利用したのはなぜ?",
        choices=["They copied what most other guests did.", "The planet card made them save towels."], answer=1,
        answer_ja="ほかの多くの客がしていることを、まねたから。",
        hl=["begged", "reuse", "rewrote", "rates", "quarter", "instinctively", "crowd"],
        shots=[
            ("A hotel begged guests to reuse their towels.", dict(type="insert", bg="room", insert="card", value="REUSE TOWELS", cam="pan")),
            ("Save the planet, the card said. Few listened.", dict(type="face", bg="room", eyes="worried", mouth="wavy", cam="push")),
            ("So I rewrote it: most guests here reuse towels.", dict(type="lens", bg="room", insert="card", value="MOST GUESTS REUSE", focus=[540, 1010], stamp="CLUE 1")),
            ("Reuse rates jumped by about a quarter.", dict(type="insert", bg="bank", insert="chart", value="+26%", cam="snap")),
            ("We instinctively follow the crowd.", dict(type="two", bg="room", det=True, color="#2d6a4f", eyes="smug", mouth="smile", eyes2="happy", mouth2="grin", cam="pan")),
            ("Case closed: social proof.", dict(type="silhouette", bg="dark", det=True, eyes="smug", wipe="iris", stamp="SOLVED")),
        ],
        ja=["あるホテルは、タオルの再利用を客に頼みこんだ。", "「地球を守ろう」とカードにあった。聞く人は少なかった。", "そこで私は書き直した。「ここの客のほとんどはタオルを再利用しています」。",
            "再利用の割合は、約4分の1も増えた。", "私たちは、本能的にみんなに従う。", "事件解決。「社会的証明」だ。"],
        gloss=["beg:頼みこむ", "reuse:再利用する", "rewrite:書き直す", "rate:割合", "quarter:4分の1", "instinctively:本能的に", "crowd:多くの人々"],
        grammar=["most + 複数名詞", "「ほとんどの〜」。most guests(ほとんどの客)。", "特定のグループなら most of the guests(その客のほとんど)のように of the が入る。"],
        hook="カード1枚で、タオル再利用が増えた?🏨", tags="#英語リスニング #心理学 #謎解き"),
    "case09_framing": dict(IVY, caseNo="CASE #09", mystery="card", mysteryValue="90% / 10%", hint="🔍手がかり:2つの言い方",
        q="Why did more patients choose the same surgery?", q_ja="同じ手術なのに\n選ぶ人が増えたのはなぜ?",
        choices=["Ten percent more patients survived.", "The positive wording made it sound safer."], answer=2,
        answer_ja="前向きな言い方のほうが、安全に聞こえたから。",
        hl=["described", "survive", "identical", "odds", "phrase", "shapes", "decisions"],
        shots=[
            ("Doctors described one surgery in two ways.", dict(type="two", bg="office", det=True, color="#2d6a4f", eyes="normal", mouth="flat", eyes2="worried", mouth2="flat", color2="#f4f4f0", cam="pan")),
            ("Version one: ninety percent survive.", dict(type="insert", bg="dark", insert="card", value="90% SURVIVE", cam="push")),
            ("Version two: ten percent die.", dict(type="insert", bg="dark", insert="card", value="10% DIE", cam="snap")),
            ("Identical odds, yet far more chose version one.", dict(type="split", bg="dark", left="90% LIVE", right="10% DIE", eyes="happy", mouth="grin", eyes2="worried", mouth2="wavy", cam="push", stamp="CLUE 1")),
            ("How we phrase facts shapes our decisions.", dict(type="ots", bg="office", det=True, color="#2d6a4f", eyes2="shock", mouth2="o", cam="tilt", mark=[560, 1140, 170])),
            ("Elementary. It's the framing effect.", dict(type="silhouette", bg="dark", det=True, eyes="smug", wipe="iris", stamp="SOLVED")),
        ],
        ja=["医師は、1つの手術を2通りに説明した。", "1つめ:90%が助かる。", "2つめ:10%が亡くなる。",
            "確率はまったく同じ。それでも、1つめを選ぶ人がずっと多かった。", "事実をどう言い表すかが、決断を形づくる。", "初歩的なことだよ。「フレーミング効果」だ。"],
        gloss=["describe:説明する", "survive:生き残る", "identical:まったく同じ", "odds:確率", "phrase:言い表す", "shape:形づくる", "decision:決断"],
        grammar=["How + 主語 + 動詞(が主語になる)", "How we phrase facts(事実をどう言い表すか)が文の主語。", "動詞は shapes と単数形になる点に注意。"],
        hook="同じ手術、言い方で選ぶ人が変わる?🏥", tags="#英語リスニング #心理学 #謎解き"),
    "sci007_honey": dict(SCI, no="#007", mystery="card", mysteryValue="HONEY?", bgm="cycles",
        q="Can honey last for thousands of years?", q_ja="ハチミツは\n何千年ももつ?",
        choices=["Yes, it can last a very long time.", "No, germs live in it."], answer=1, answer_ja="はい、とても長くもつ。",
        hl=["sweet", "germs", "Egypt"],
        shots=[
            ("Honey is very sweet.", dict(type="insert", bg="dark", insert="card", value="HONEY", cam="pull")),
            ("Germs can't live in it.", dict(type="insert", bg="dark", insert="card", value="NO GERMS", cam="push")),
            ("Old honey in Egypt was still good!", dict(type="face", bg="lab", sci=True, color="#f4f4f0", eyes="shock", mouth="o", cam="whip")),
        ],
        ja=["ハチミツはとても甘い。", "ばい菌は、その中で生きられない。", "エジプトの古いハチミツは、まだ食べられた!"],
        gloss=["sweet:甘い", "germ:ばい菌", "Egypt:エジプト"],
        hook="何千年も腐らない食べ物がある?🍯", tags="#英語リスニング #やさしい英語 #科学クイズ"),
    "sci008_kilo": dict(SCI, no="#008", mystery="card", mysteryValue="1 kg vs 1 kg", bgm="vapour",
        q="Which is heavier: 1 kg of feathers or 1 kg of iron?", q_ja="1kgの羽と1kgの鉄、\n重いのはどっち?",
        choices=["The iron is heavier.", "They weigh the same."], answer=2, answer_ja="同じ重さ。",
        hl=["soft", "heavy", "always"],
        shots=[
            ("Feathers are soft and light.", dict(type="insert", bg="dark", insert="card", value="FEATHERS", cam="pull")),
            ("Iron is hard and heavy.", dict(type="insert", bg="dark", insert="card", value="IRON", cam="push")),
            ("But one kilo is always one kilo!", dict(type="face", bg="lab", sci=True, color="#f4f4f0", eyes="smug", mouth="grin", cam="whip")),
        ],
        ja=["羽は、やわらかくて軽い。", "鉄は、かたくて重い。", "でも、1キロはいつでも1キロ!"],
        gloss=["soft:やわらかい", "heavy:重い", "always:いつも"],
        hook="1kgの羽と1kgの鉄、重いのは?🪶", tags="#英語リスニング #やさしい英語 #科学クイズ"),
    "sci009_banana": dict(SCI, no="#009", mystery="strawberry", bgm="tunnel",
        q="Is a banana a berry?", q_ja="バナナは\nベリーの仲間?",
        choices=["Yes, it is.", "No, only strawberries are."], answer=1, answer_ja="はい、ベリーの仲間。",
        hl=["berries", "seeds", "inside"],
        shots=[
            ("Strawberries are not true berries.", dict(type="insert", bg="dark", insert="strawberry", cam="pull")),
            ("But bananas are!", dict(type="insert", bg="dark", insert="card", value="BANANA = BERRY", cam="snap")),
            ("A true berry has its seeds inside.", dict(type="face", bg="lab", sci=True, color="#f4f4f0", eyes="happy", mouth="grin", cam="whip")),
        ],
        ja=["イチゴは、本当のベリーではない。", "でも、バナナはベリー!", "本当のベリーは、種が内側にある。"],
        gloss=["berry:ベリー(液果)", "seed:種", "inside:内側に"],
        hook="バナナはベリー、イチゴはちがう?🍌", tags="#英語リスニング #やさしい英語 #科学クイズ"),
    "sea005_octopus": dict(SEA, voice=GEORGE, no="#005", mystery="octopus", cover=0, bgm="lantern",
        q="What color is octopus blood?", q_ja="タコの血は\n何色?",
        choices=["Red, because it uses iron.", "Blue."], answer=2, answer_ja="青",
        hl=["smart", "copper", "blue"],
        shots=[
            ("Octopuses are smart, soft animals.", dict(type="insert", bg="ocean", insert="octopus", cam="pull", sonar="OCTOPUS")),
            ("Their blood uses copper, not iron.", dict(type="lens", bg="ocean", insert="octopus", focus=[540, 860], wipe="slide")),
            ("So it looks blue!", dict(type="insert", bg="ocean", insert="octopus", value="BLUE!", cam="push")),
        ],
        ja=["タコは、かしこくてやわらかい生き物。", "血には、鉄ではなく銅が使われている。", "だから、青く見える!"],
        gloss=["smart:かしこい", "copper:銅", "iron:鉄"],
        hook="タコの血の色、知ってる?🐙", tags="#英語リスニング #やさしい英語 #海の生き物"),
    "sea006_names": dict(SEA, voice=MATILDA, no="#006", mystery="dolphin", cover=0, bgm="sailing",
        q="How do dolphins call each other?", q_ja="イルカは\nどうやって呼び合う?",
        choices=["With a whistle that works like a name.", "They copy their friends' faces."], answer=1, answer_ja="名前のような口笛の音で。",
        hl=["special", "whistle", "copy"],
        shots=[
            ("Each dolphin makes its own special whistle.", dict(type="insert", bg="ocean", insert="dolphin", cam="pan", sonar="DOLPHIN")),
            ("Friends copy it to call that dolphin.", dict(type="insert", bg="ocean", insert="dolphin", value="♪ ♫ ♪", cam="push")),
            ("It works just like a name!", dict(type="insert", bg="ocean", insert="card", value="NAME", cam="snap")),
        ],
        ja=["イルカは1頭ずつ、自分だけの特別な口笛の音を出す。", "仲間はそれをまねして、そのイルカを呼ぶ。", "まるで名前のように使われている!"],
        gloss=["special:特別な", "whistle:口笛(のような音)", "copy:まねる"],
        hook="イルカにも名前がある?🐬", tags="#英語リスニング #やさしい英語 #海の生き物"),
    "geo004_fuji": dict(GEO, no="#004", cover=0, hint="👂ヒント:4文目に注目", mysteryMap={"from": [138.73, 35.36, 12]},
        q="What kind of mountain is Mount Fuji?", q_ja="富士山は\nどんな山?",
        choices=["It is just a quiet, ordinary mountain.", "It is a volcano that can still erupt."], answer=2,
        answer_ja="まだ噴火するかもしれない火山。",
        hl=["highest", "peak", "rises", "active", "volcano", "eruption"],
        shots=[
            ("Mount Fuji is Japan's highest peak.", dict(type="map", bg="dark", map={"from": [137, 36, 6], "to": [138.7, 35.4, 13], "hl": ["392"], "labels": [[138.73, 35.95, "MT. FUJI"]]})),
            ("It rises three thousand seven hundred seventy-six meters.", dict(type="map", bg="dark", hud="3,776 m", map={"from": [138.73, 35.36, 15], "dots": [[138.73, 35.36]]})),
            ("But it isn't just a mountain.", dict(type="map", bg="dark", map={"from": [138.73, 35.4, 13], "to": [138.73, 35.4, 11]})),
            ("It's an active volcano.", dict(type="map", bg="dark", map={"from": [138.73, 35.36, 14], "shake": True, "dots": [[138.73, 35.36]], "labels": [[138.73, 35.9, "ACTIVE VOLCANO"]]})),
            ("Its last eruption was in seventeen oh seven.", dict(type="map", bg="dark", hud="LAST ERUPTION: 1707", map={"from": [138.73, 35.36, 12], "to": [138, 36, 7], "hl": ["392"], "dots": [[138.73, 35.36]]})),
        ],
        ja=["富士山は、日本でいちばん高い山。", "高さは3,776メートル。", "でも、ただの山ではない。", "活火山だ。", "最後の噴火は1707年。"],
        gloss=["peak:山頂、峰", "rise:そびえる", "active:活動している", "volcano:火山", "eruption:噴火"],
        hook="富士山は、ただの山じゃない?🗻", tags="#英語リスニング #やさしい英語 #地理"),
    "geo005_snow": dict(GEO, no="#005", cover=4, hint="👂ヒント:3文目に注目", mysteryMap={"from": [134, 40, 5]},
        q="Why does so much snow fall on the Sea of Japan side?", q_ja="日本海側に\n雪が多いのはなぜ?",
        choices=["Wet winds from the sea hit the mountains and drop snow.", "Freezing winds blow snow from Siberia's mountains."], answer=1,
        answer_ja="海で湿った風が山にぶつかり、雪を降らせるから。",
        hl=["freezing", "Siberia", "cross", "soak", "moisture", "force", "heavy"],
        shots=[
            ("In winter, freezing winds blow from Siberia.", dict(type="map", bg="dark", map={"from": [128, 47, 4.2], "to": [130, 45, 4.8], "arrows": [[115, 52, 130, 44]], "labels": [[112, 56, "SIBERIA"]]})),
            ("They cross the warmer Sea of Japan.", dict(type="map", bg="dark", map={"from": [134, 40, 6], "arrows": [[128, 44, 136, 39]], "labels": [[134, 41.5, "SEA OF JAPAN"]]})),
            ("There, they soak up lots of moisture.", dict(type="map", bg="dark", map={"from": [134, 40, 7], "to": [135, 39, 8], "dots": [[133, 41], [135.5, 40], [137, 39.3]]})),
            ("Mountains force the air upward.", dict(type="map", bg="dark", map={"from": [139, 37.5, 9], "hl": ["392"], "arrows": [[136, 39, 139, 37.4]]})),
            ("The moisture falls as heavy snow.", dict(type="map", bg="dark", hud="❄ HEAVY SNOW", map={"from": [139.5, 38, 9], "to": [139, 37.5, 10], "hl": ["392"],
                "dots": [[139.0, 37.9], [137.2, 36.7], [140.7, 40.8]], "labels": [[139.0, 38.5, "NIIGATA"], [140.7, 41.4, "AOMORI"]]})),
        ],
        ja=["冬、シベリアから凍える風が吹く。", "風は、比較的暖かい日本海を渡る。", "そこで、たくさんの水分を吸い込む。", "山が、その空気を上へ押し上げる。", "水分は、大雪になって降る。"],
        gloss=["freezing:凍えるほど寒い", "Siberia:シベリア", "cross:横切る、渡る", "soak up:吸い込む", "moisture:水分", "force:無理に動かす"],
        hook="日本海側だけ大雪になる理由は?❄️", tags="#英語リスニング #やさしい英語 #地理"),
    "geo006_onsen": dict(GEO, no="#006", cover=3, hint="👂ヒント:3文目に注目", mysteryMap={"from": [138.6, 36.6, 10], "dots": [[138.6, 36.62]]},
        q="Why does Japan have so many hot springs?", q_ja="日本に温泉が\n多いのはなぜ?",
        choices=["Japan builds twenty-seven thousand baths.", "Underground heat from volcanoes warms the water."], answer=2,
        answer_ja="火山の地下の熱が、水を温めるから。",
        hl=["sources", "underground", "magma", "heats", "cracks", "volcanoes"],
        shots=[
            ("Japan has over twenty-seven thousand hot spring sources.", dict(type="map", bg="dark", hud="27,000+ ♨", map={"from": [138, 36, 5], "to": [137, 36, 6.5], "hl": ["392"]})),
            ("The secret lies deep underground.", dict(type="map", bg="dark", map={"from": [137, 36, 7], "dots": [[131.5, 33.28], [138.6, 36.62], [139.0, 35.23], [141.1, 42.5]]})),
            ("Magma heats rocks and water below.", dict(type="map", bg="dark", map={"from": [138.6, 36.6, 12], "to": [138.6, 36.62, 15], "dots": [[138.6, 36.62]], "labels": [[138.6, 37.1, "KUSATSU"]]})),
            ("The hot water rises through cracks.", dict(type="map", bg="dark", map={"from": [131.5, 33.3, 12], "to": [131.5, 33.28, 15], "dots": [[131.5, 33.28]], "labels": [[131.5, 33.75, "BEPPU"]]})),
            ("Volcanoes give Japan its famous baths.", dict(type="map", bg="dark", map={"from": [137, 36, 7], "to": [137, 36, 5.5], "hl": ["392"],
                "dots": [[131.5, 33.28], [138.6, 36.62], [139.0, 35.23], [141.1, 42.5]]})),
        ],
        ja=["日本には、2万7千以上の温泉の源泉がある。", "秘密は、地下深くにある。", "マグマが、地下の岩と水を温める。", "熱いお湯が、割れ目を通って上がってくる。", "火山が、日本に有名な温泉をくれている。"],
        gloss=["source:源泉", "underground:地下で", "magma:マグマ", "heat:温める", "crack:割れ目", "volcano:火山"],
        hook="日本に温泉がこんなに多い理由は?♨️", tags="#英語リスニング #やさしい英語 #地理"),
})

# ==== 11/17 分 ====
IV = "#英語リスニング #心理学 #謎解き"
SC = "#英語リスニング #やさしい英語 #科学クイズ"
SE = "#英語リスニング #やさしい英語 #海の生き物"
GE = "#英語リスニング #やさしい英語 #地理"
SHORTS.update({
    "habit66": dict(LISTEN, mystery="clock", mysteryValue="66 DAYS", hint="👂ヒント:3文目の数字に注目",
        q="How long does a new habit really take to form?", q_ja="新しい習慣が\n身につくまで何日?",
        choices=["Exactly twenty-one days for everyone.", "About two months on average, but it varies."], answer=2,
        answer_ja="平均で約2か月。でも人によってちがう。",
        hl=["habit", "tracked", "volunteers", "average", "stick", "barely", "patient"],
        shots=[
            ("People often say a habit takes twenty-one days.", dict(type="insert", bg="room", insert="card", value="21 DAYS?", cam="whip")),
            ("A London study tracked volunteers for twelve weeks.", dict(type="two", bg="office", eyes="normal", mouth="smile", eyes2="happy", mouth2="grin", cam="pan")),
            ("On average, habits took sixty-six days to stick.", dict(type="insert", bg="dark", insert="clock", value="66 DAYS", cam="snap")),
            ("Some took only eighteen. Others, over two hundred.", dict(type="split", bg="dark", left="18", right="254", eyes="happy", mouth="grin", eyes2="worried", mouth2="wavy", cam="push")),
            ("Missing a single day barely mattered.", dict(type="face", bg="room", eyes="smug", mouth="smile", cam="pull")),
            ("So be patient, and keep going.", dict(type="wide", bg="street", eyes="happy", mouth="smile", cam="pan")),
        ],
        ja=["習慣は21日で身につく、とよく言われる。", "ロンドンの研究が、参加者を12週間追跡した。", "平均すると、習慣が定着するまで66日かかった。",
            "わずか18日の人もいれば、200日以上の人もいた。", "1日休んでも、ほとんど影響はなかった。", "だから根気強く、続けよう。"],
        gloss=["track:追跡する", "volunteer:(研究の)参加者", "on average:平均して", "stick:定着する", "barely:ほとんど〜ない", "patient:根気強い"],
        hook="習慣が身につくのは21日?それとも…📅", tags=f"{LS} #自己啓発"),
    "goosebumps": dict(LISTEN, mystery="card", mysteryValue="BRRR…", hint="👂ヒント:3文目に注目",
        q="Why do we get goosebumps?", q_ja="鳥肌が\n立つのはなぜ?",
        choices=["It is an old reflex left from our furry ancestors.", "Our muscles become furry when we feel cold."], answer=1,
        answer_ja="毛深かった祖先から残った、古い反射だから。",
        hl=["scared", "bumps", "upright", "muscle", "ancestors", "reflex", "leftover"],
        shots=[
            ("Feel cold or scared, and tiny bumps appear.", dict(type="face", bg="room", eyes="shock", mouth="o", cam="whip")),
            ("Each one is a hair pulled upright by a muscle.", dict(type="lens", bg="dark", insert="card", value="HAIR + MUSCLE", focus=[540, 1010])),
            ("Our furry ancestors puffed up to stay warm.", dict(type="insert", bg="street", insert="card", value="ANCESTORS", cam="pan")),
            ("Fluffed fur also made them look bigger.", dict(type="full", bg="street", eyes="smug", mouth="grin", cam="rise")),
            ("We lost the fur, but kept the reflex.", dict(type="eyes", bg="dark", eyes="shock", cam="shake")),
            ("It's a leftover from our distant past.", dict(type="silhouette", bg="dark", eyes="smug", wipe="iris")),
        ],
        ja=["寒いときやこわいとき、小さなぶつぶつが出てくる。", "1つ1つは、筋肉に引っぱられて立った毛だ。", "毛深い祖先は、毛をふくらませて体を温めた。",
            "ふくらんだ毛は、体を大きく見せる役にも立った。", "毛はなくなったが、反射は残った。", "遠い昔の名残りなのだ。"],
        gloss=["scared:こわがって", "bump:ぶつぶつ", "upright:まっすぐ立った", "muscle:筋肉", "ancestor:祖先", "puff up:ふくらませる", "reflex:反射", "leftover:名残り"],
        hook="鳥肌が立つのは、昔の名残り?🥶", tags=f"{LS} #科学"),
    "leftdigit": dict(LISTEN, mystery="card", mysteryValue="$2.99", hint="👂ヒント:3文目に注目",
        q="Why do so many prices end in 99?", q_ja="値段の最後が\n99なのはなぜ?",
        choices=["Three dollars feels much closer to ninety-nine.", "We focus on the first digit, so it feels cheaper."], answer=2,
        answer_ja="最初の数字に注目するので、安く感じるから。",
        hl=["anchor", "digit", "closer", "noticeably", "boost"],
        shots=[
            ("Why does a price say two ninety-nine, not three?", dict(type="insert", bg="room", insert="card", value="$2.99", cam="whip")),
            ("We read numbers from left to right.", dict(type="face", bg="room", eyes="normal", mouth="smile", cam="pan")),
            ("Our brains anchor on that first digit.", dict(type="lens", bg="dark", insert="card", value="2.99", focus=[480, 1010])),
            ("So two ninety-nine feels much closer to two.", dict(type="split", bg="dark", left="$2.99", right="$3.00", eyes="happy", mouth="grin", eyes2="worried", mouth2="flat", cam="push")),
            ("Researchers call this the left-digit effect.", dict(type="insert", bg="dark", insert="card", value="LEFT-DIGIT EFFECT", cam="snap")),
            ("A single cent can noticeably boost sales.", dict(type="insert", bg="bank", insert="chart", value="SALES", cam="push")),
        ],
        ja=["なぜ値段は3ドルではなく、2ドル99セントなのか?", "私たちは、数字を左から右へ読む。", "脳は、最初の数字をよりどころにする。",
            "だから2.99は、2にずっと近く感じる。", "研究者は、これを「左端の数字効果」と呼ぶ。", "たった1セントで、売上がはっきり伸びることがある。"],
        gloss=["anchor on A:Aをよりどころにする", "digit:(数字の)桁", "close to A:Aに近い", "noticeably:目立って", "boost:押し上げる"],
        hook="値段の最後が99なのは、なぜ?🏷️", tags=f"{LS} #お金の勉強"),
    "case10_endowment": dict(IVY, caseNo="CASE #10", mystery="card", mysteryValue="$7 vs $3", hint="🔍手がかり:持ち主と買い手の値段",
        q="Why did mug owners demand twice the price?", q_ja="マグの持ち主が\n倍の値段をつけたのはなぜ?",
        choices=["Owning the mug made it feel more valuable.", "Buyers barely wanted free mugs."], answer=1,
        answer_ja="自分の物になったことで、価値が高く感じたから。",
        hl=["handed", "demanded", "barely", "overvalue", "endowment"],
        shots=[
            ("Half the students were handed a free mug.", dict(type="insert", bg="office", insert="card", value="FREE MUG", cam="pan")),
            ("The rest could buy one from them.", dict(type="two", bg="office", det=True, color="#2d6a4f", eyes="normal", mouth="flat", eyes2="happy", mouth2="smile", cam="push")),
            ("Owners demanded about seven dollars.", dict(type="insert", bg="dark", insert="card", value="$7", cam="snap", stamp="CLUE 1")),
            ("Buyers would barely pay three.", dict(type="insert", bg="dark", insert="card", value="$3", cam="push")),
            ("The moment we own something, we overvalue it.", dict(type="ots", bg="office", det=True, color="#2d6a4f", eyes2="shock", mouth2="o", cam="tilt", mark=[560, 1140, 170])),
            ("Case closed: the endowment effect.", dict(type="silhouette", bg="dark", det=True, eyes="smug", wipe="iris", stamp="SOLVED")),
        ],
        ja=["学生の半分に、無料のマグカップが手渡された。", "残りの学生は、彼らからマグを買うことができた。", "持ち主は、約7ドルを要求した。",
            "買い手は、3ドルもほとんど払おうとしなかった。", "何かを手にした瞬間、私たちはそれを高く見積もる。", "事件解決。「保有効果」だ。"],
        gloss=["hand:手渡す", "demand:要求する", "barely:ほとんど〜ない", "overvalue:高く見積もりすぎる", "endowment:(持っている)もの、資産"],
        grammar=["The moment + 主語 + 動詞, 〜", "「〜した瞬間に」。the moment が接続詞のように働く。", "The moment we own something, we overvalue it.(手にした瞬間、高く見積もる)"],
        hook="もらったマグ、急に高く感じる?☕", tags=IV),
    "case11_bystander": dict(IVY, caseNo="CASE #11", mystery="card", mysteryValue="SMOKE?", hint="🔍手がかり:まわりの2人",
        q="Why did people ignore smoke when others stayed calm?", q_ja="煙が出ているのに\n誰も動かなかったのはなぜ?",
        choices=["Two strangers reported the smoke first.", "They copied the calm reactions around them."], answer=2,
        answer_ja="まわりの落ち着いた反応を、まねたから。",
        hl=["seeping", "reported", "calm", "alarm", "judge", "bystander"],
        shots=[
            ("Smoke began seeping into a waiting room.", dict(type="insert", bg="office", insert="card", value="SMOKE", cam="rise")),
            ("Alone, most people reported it within minutes.", dict(type="full", bg="office", eyes="shock", mouth="o", cam="push")),
            ("But with two calm strangers, few moved.", dict(type="two", bg="office", eyes="worried", mouth="flat", eyes2="normal", mouth2="smile", cam="pan", stamp="CLUE 1")),
            ("Only one in ten raised the alarm.", dict(type="insert", bg="dark", insert="card", value="1 IN 10", cam="snap")),
            ("We look to others to judge danger.", dict(type="ots", bg="office", det=True, color="#2d6a4f", eyes2="worried", mouth2="flat", cam="tilt", mark=[560, 1140, 170])),
            ("Elementary: the bystander effect.", dict(type="silhouette", bg="dark", det=True, eyes="smug", wipe="iris", stamp="SOLVED")),
        ],
        ja=["待合室に、煙がもれ入ってきた。", "1人のときは、ほとんどの人が数分以内に知らせた。", "でも、落ち着いた見知らぬ2人と一緒だと、動いた人は少なかった。",
            "知らせたのは、10人に1人だけ。", "私たちは、危険かどうかを他人を見て判断する。", "初歩的なことだよ。「傍観者効果」だ。"],
        gloss=["seep:しみ出る、もれ入る", "report:知らせる", "calm:落ち着いた", "raise the alarm:危険を知らせる", "judge:判断する", "bystander:傍観者"],
        grammar=["one in ten", "「10人に1人」。割合を表す言い方。", "Only one in ten raised the alarm.(知らせたのは10人に1人だけ)"],
        hook="煙が出ても、誰も動かない?🚨", tags=IV),
    "case12_zeigarnik": dict(IVY, caseNo="CASE #12", mystery="card", mysteryValue="UNPAID", hint="🔍手がかり:支払いの前と後",
        q="Why did the waiter forget orders right after they were paid?", q_ja="支払いが済んだ注文を\nすぐ忘れたのはなぜ?",
        choices=["Finished tasks leave the mind, but unfinished ones stay.", "The waiter settled every bill perfectly."], answer=1,
        answer_ja="終わったことは忘れ、終わっていないことは覚えているから。",
        hl=["unpaid", "settled", "vanished", "unfinished", "cling", "incomplete"],
        shots=[
            ("A waiter remembered every unpaid order perfectly.", dict(type="full", bg="room", eyes="happy", mouth="grin", cam="push")),
            ("Yet once the bill was settled, it vanished.", dict(type="insert", bg="dark", insert="card", value="PAID ✓", cam="snap")),
            ("A psychologist named Zeigarnik tested this.", dict(type="two", bg="room", det=True, color="#2d6a4f", eyes="smug", mouth="smile", eyes2="normal", mouth2="smile", cam="pan")),
            ("Unfinished tasks stuck far better in memory.", dict(type="insert", bg="dark", insert="brain", value="UNFINISHED", cam="push", stamp="CLUE 1")),
            ("Our minds cling to what's incomplete.", dict(type="ots", bg="room", det=True, color="#2d6a4f", eyes2="shock", mouth2="o", cam="tilt", mark=[560, 1140, 170])),
            ("Case closed: the Zeigarnik effect.", dict(type="silhouette", bg="dark", det=True, eyes="smug", wipe="iris", stamp="SOLVED")),
        ],
        ja=["あるウェイターは、未払いの注文を完ぺきに覚えていた。", "ところが支払いが済むと、すっかり消えた。", "ツァイガルニクという心理学者が、これを確かめた。",
            "終わっていない課題のほうが、ずっとよく記憶に残った。", "心は、終わっていないことにしがみつく。", "事件解決。「ツァイガルニク効果」だ。"],
        gloss=["unpaid:未払いの", "settle:清算する", "vanish:消える", "unfinished:終わっていない", "cling to A:Aにしがみつく", "incomplete:不完全な"],
        grammar=["名詞 + named + 名前", "「〜という名前の…」。過去分詞 named が後ろから名詞を説明する。", "a psychologist named Zeigarnik(ツァイガルニクという名前の心理学者)"],
        hook="支払いが済むと、注文を忘れる?🧾", tags=IV),
    "sci010_brain": dict(SCI, no="#010", mystery="brain", bgm="cycles",
        q="How much of your energy does your brain use?", q_ja="脳は体のエネルギーを\nどれくらい使う?",
        choices=["Only a little, because it is small.", "About one fifth."], answer=2, answer_ja="約5分の1",
        hl=["small", "busy", "energy"],
        shots=[
            ("Your brain is small.", dict(type="insert", bg="dark", insert="brain", cam="pull")),
            ("But it is always busy.", dict(type="insert", bg="dark", insert="brain", value="BUSY!", cam="push")),
            ("It uses about one fifth of your energy!", dict(type="face", bg="lab", sci=True, color="#f4f4f0", eyes="shock", mouth="o", cam="whip", hud="≈ 20%")),
        ],
        ja=["脳は小さい。", "でも、いつもいそがしい。", "体のエネルギーの約5分の1を使う!"],
        gloss=["small:小さい", "busy:いそがしい", "energy:エネルギー"],
        hook="脳はエネルギーをどれくらい使う?🧠", tags=SC),
    "sci011_ice": dict(SCI, no="#011", mystery="card", mysteryValue="ICE?", bgm="vapour",
        q="Why does ice float on water?", q_ja="氷が水に\nうくのはなぜ?",
        choices=["Ice is lighter than water.", "Ice gets heavier when it freezes."], answer=1, answer_ja="氷は水より軽いから。",
        hl=["freezes", "lighter", "floats"],
        shots=[
            ("Water gets bigger when it freezes.", dict(type="insert", bg="dark", insert="card", value="WATER → ICE", cam="pull")),
            ("So ice is lighter than water.", dict(type="insert", bg="dark", insert="card", value="LIGHTER", cam="push")),
            ("That's why it floats!", dict(type="face", bg="lab", sci=True, color="#f4f4f0", eyes="happy", mouth="grin", cam="whip")),
        ],
        ja=["水は、こおると体積が大きくなる。", "だから氷は、水より軽い。", "それで、うくんだ!"],
        gloss=["freeze:こおる", "light:軽い", "float:うく"],
        hook="氷が水にうく理由、言える?🧊", tags=SC),
    "sci012_bones": dict(SCI, no="#012", mystery="card", mysteryValue="300?", bgm="tunnel",
        q="Who has more bones, a baby or an adult?", q_ja="骨が多いのは、\n赤ちゃん?大人?",
        choices=["An adult, because adults grow more bones.", "A baby."], answer=2, answer_ja="赤ちゃん",
        hl=["bones", "grow", "join"],
        shots=[
            ("Babies have about three hundred bones.", dict(type="insert", bg="dark", insert="card", value="BABY: 300", cam="pull")),
            ("As they grow, some bones join together.", dict(type="insert", bg="dark", insert="card", value="JOIN!", cam="push")),
            ("Adults have only two hundred six!", dict(type="face", bg="lab", sci=True, color="#f4f4f0", eyes="shock", mouth="o", cam="whip", hud="ADULT: 206")),
        ],
        ja=["赤ちゃんには、約300個の骨がある。", "成長すると、いくつかの骨がくっつく。", "大人は、206個だけ!"],
        gloss=["bone:骨", "grow:成長する", "join:くっつく"],
        hook="骨が多いのは赤ちゃん?大人?🦴", tags=SC),
    "sea007_orca": dict(SEA, voice=GEORGE, no="#007", mystery="orca", cover=0, bgm="whales",
        q="What kind of animal is an orca?", q_ja="シャチは\n何の仲間?",
        choices=["A real whale, as its name says.", "A very large dolphin."], answer=2, answer_ja="とても大きなイルカ",
        hl=["killer", "whales", "dolphins"],
        shots=[
            ("Orcas are often called killer whales.", dict(type="insert", bg="ocean", insert="orca", cam="pan", sonar="ORCA")),
            ("But they are not really whales.", dict(type="insert", bg="ocean", insert="card", value="WHALE?", cam="push")),
            ("They are the biggest dolphins!", dict(type="insert", bg="ocean", insert="orca", value="DOLPHIN!", cam="snap")),
        ],
        ja=["シャチは、よく「キラーホエール」と呼ばれる。", "でも、本当はクジラではない。", "いちばん大きなイルカの仲間!"],
        gloss=["killer whale:シャチ(英語の呼び名)", "whale:クジラ", "dolphin:イルカ"],
        hook="シャチはクジラじゃない?🐋", tags=SE),
    "sea008_nobrain": dict(SEA, voice=MATILDA, no="#008", mystery="jellyfish", cover=0, bgm="lantern",
        q="Do jellyfish have a brain?", q_ja="クラゲに\n脳はある?",
        choices=["No, they don't.", "Yes, a brain and a heart."], answer=1, answer_ja="いいえ、ない。",
        hl=["millions", "brain", "nerves"],
        shots=[
            ("Jellyfish have lived for millions of years.", dict(type="insert", bg="ocean", insert="jellyfish", cam="pull", sonar="JELLYFISH")),
            ("They have no brain and no heart.", dict(type="lens", bg="ocean", insert="jellyfish", focus=[540, 880], wipe="slide")),
            ("Simple nerves help them move!", dict(type="insert", bg="ocean", insert="card", value="NO BRAIN", cam="snap")),
        ],
        ja=["クラゲは、何百万年も生きのびてきた。", "脳も心臓もない。", "シンプルな神経のおかげで動ける!"],
        gloss=["million:百万", "brain:脳", "nerve:神経"],
        hook="脳がないのに動けるクラゲ?🪼", tags=SE),
    "geo007_islands": dict(GEO, no="#007", cover=3, hint="👂ヒント:4文目の数字に注目", mysteryMap={"from": [137, 37, 5]},
        q="How many islands does Japan have?", q_ja="日本には\nいくつの島がある?",
        choices=["Over fourteen thousand.", "Just the four main ones."], answer=1, answer_ja="1万4千以上",
        hl=["main", "recent", "count", "tiny", "uninhabited"],
        shots=[
            ("Most people think of four main islands.", dict(type="map", bg="dark", map={"from": [137, 37, 4.5], "to": [137, 37, 5.2], "hl": ["392"]})),
            ("Hokkaido, Honshu, Shikoku, and Kyushu.", dict(type="map", bg="dark", map={"from": [137, 37, 5.5], "hl": ["392"],
                "labels": [[143, 44.3, "HOKKAIDO"], [138.5, 37.5, "HONSHU"], [133.5, 32.9, "SHIKOKU"], [130.8, 31.6, "KYUSHU"]]})),
            ("But a recent count found far more.", dict(type="map", bg="dark", map={"from": [129, 28, 7], "to": [128, 27, 9], "hl": ["392"]})),
            ("Japan has over fourteen thousand islands.", dict(type="map", bg="dark", hud="14,125 ISLANDS", map={"from": [132, 31, 6], "to": [134, 32, 5], "hl": ["392"]})),
            ("Most are tiny and uninhabited.", dict(type="map", bg="dark", map={"from": [129.5, 28.4, 11], "to": [129.5, 28.4, 14], "hl": ["392"]})),
        ],
        ja=["多くの人は、4つの主な島を思いうかべる。", "北海道、本州、四国、九州。", "でも、最近数え直したら、ずっと多かった。", "日本には、1万4千以上の島がある。", "そのほとんどは、小さな無人島だ。"],
        gloss=["main:主な", "recent:最近の", "count:数えること", "tiny:とても小さい", "uninhabited:人が住んでいない"],
        hook="日本の島、いくつあると思う?🏝️", tags=GE),
    "geo008_biwa": dict(GEO, no="#008", cover=0, hint="👂ヒント:4文目に注目", mysteryMap={"from": [136.08, 35.25, 20]},
        q="Why is Lake Biwa so important?", q_ja="琵琶湖が\n大切なのはなぜ?",
        choices=["Fourteen million people live on the lake.", "It supplies water to millions of people."], answer=2,
        answer_ja="何百万人もの人に、水を届けているから。",
        hl=["largest", "oldest", "flows", "depend", "locals"],
        shots=[
            ("Lake Biwa is Japan's largest lake.", dict(type="map", bg="dark", map={"from": [136, 35.5, 8], "to": [136.08, 35.25, 22], "hl": ["392"], "labels": [[136.08, 35.75, "LAKE BIWA"]]})),
            ("It's also one of the oldest on Earth.", dict(type="map", bg="dark", hud="≈ 4,000,000 YEARS", map={"from": [136.08, 35.25, 24]})),
            ("Its water flows down to Kyoto and Osaka.", dict(type="map", bg="dark", map={"from": [135.8, 35.0, 18], "arrows": [[136.0, 35.05, 135.55, 34.72]],
                "dots": [[135.77, 35.01], [135.5, 34.69]], "labels": [[135.77, 35.15, "KYOTO"], [135.5, 34.55, "OSAKA"]]})),
            ("About fourteen million people depend on it.", dict(type="map", bg="dark", hud="≈ 14,000,000 PEOPLE", map={"from": [135.8, 35, 14], "to": [135.8, 35, 11],
                "dots": [[135.77, 35.01], [135.5, 34.69], [135.2, 34.69]]})),
            ("That's why locals call it the water jar of Kansai.", dict(type="map", bg="dark", map={"from": [136, 35.2, 12], "hl": ["392"], "labels": [[136.08, 35.75, "WATER JAR"]]})),
        ],
        ja=["琵琶湖は、日本でいちばん大きな湖。", "世界でも、もっとも古い湖の1つ。", "その水は、京都や大阪へ流れていく。", "約1,400万人が、この水に頼っている。", "だから地元では「近畿の水がめ」と呼ばれる。"],
        gloss=["largest:いちばん大きい", "oldest:いちばん古い", "flow:流れる", "depend on A:Aに頼る", "local:地元の人", "jar:かめ、つぼ"],
        hook="琵琶湖が\n「近畿の水がめ」なのはなぜ?💧", tags=GE),
    "geo009_sakura": dict(GEO, no="#009", cover=3, hint="👂ヒント:4文目に注目", mysteryMap={"from": [139.7, 35.7, 9]},
        q="Why does the cherry blossom season move north?", q_ja="桜の開花が\n北へ進むのはなぜ?",
        choices=["The flowers follow warm weather as it spreads north.", "Hokkaido's flowers open first, in January."], answer=1,
        answer_ja="暖かさが北へ広がるのを、花が追いかけるから。",
        hl=["blossoms", "bloom", "wait", "warmth", "northward", "front"],
        shots=[
            ("In Okinawa, cherry blossoms open in January.", dict(type="map", bg="dark", map={"from": [128.5, 27, 9], "to": [127.7, 26.3, 13], "dots": [[127.68, 26.21]], "labels": [[127.68, 26.9, "JAN"]]})),
            ("In Tokyo, they bloom in late March.", dict(type="map", bg="dark", map={"from": [139.5, 35.8, 9], "to": [139.7, 35.7, 13], "dots": [[139.69, 35.69]], "labels": [[139.69, 36.3, "LATE MAR"]]})),
            ("Hokkaido has to wait until May.", dict(type="map", bg="dark", map={"from": [142, 43.5, 9], "to": [141.4, 43.1, 13], "dots": [[141.35, 43.06]], "labels": [[141.35, 43.7, "MAY"]]})),
            ("The flowers follow the warmth northward.", dict(type="map", bg="dark", map={"from": [136, 35, 5.5], "hl": ["392"], "arrows": [[128, 26.5, 139, 35.5], [139, 36, 141.5, 42.6]]})),
            ("People call it the cherry blossom front.", dict(type="map", bg="dark", hud="🌸 SAKURA FRONT", map={"from": [137, 36, 5.5], "to": [137, 36, 5], "hl": ["392"],
                "dots": [[127.68, 26.21], [139.69, 35.69], [141.35, 43.06]], "labels": [[127.68, 27.1, "JAN"], [139.69, 36.6, "MAR"], [141.35, 44.0, "MAY"]]})),
        ],
        ja=["沖縄では、桜は1月に咲く。", "東京では、3月下旬に咲く。", "北海道は、5月まで待たなければならない。", "花は、暖かさを追いかけて北へ進む。", "これを「桜前線」と呼ぶ。"],
        gloss=["blossom:(木の)花", "bloom:咲く", "warmth:暖かさ", "northward:北へ", "front:前線"],
        hook="桜前線、英語で説明できる?🌸", tags=GE),
})

# ==== 11/18 分 ====
SHORTS.update({
    "autumn": dict(LISTEN, mystery="card", mysteryValue="AUTUMN?", hint="👂ヒント:4文目に注目",
        q="Why do leaves turn red and yellow in autumn?", q_ja="秋に葉が\n赤や黄色になるのはなぜ?",
        choices=["The green fades, so other colors show through.", "Trees paint their leaves red in summer."], answer=1,
        answer_ja="緑が薄れて、ほかの色が見えてくるから。",
        hl=["chlorophyll", "captures", "shorten", "producing", "fades", "revealing", "pigments"],
        shots=[
            ("All summer, leaves are packed with green chlorophyll.", dict(type="insert", bg="street", insert="card", value="CHLOROPHYLL", cam="whip")),
            ("It captures sunlight to make food.", dict(type="insert", bg="dark", insert="prism", cam="push")),
            ("As days shorten, trees stop producing it.", dict(type="insert", bg="dark", insert="clock", value="SHORT DAYS", cam="snap")),
            ("The green fades, revealing hidden yellows.", dict(type="lens", bg="street", insert="card", value="YELLOW", focus=[540, 1010])),
            ("Some trees also create brand-new red pigments.", dict(type="insert", bg="street", insert="card", value="NEW RED", cam="push", wipe="slide")),
            ("So autumn colors were partly there all along.", dict(type="face", bg="street", eyes="smug", mouth="smile", cam="pull")),
        ],
        ja=["夏のあいだ、葉は緑の葉緑素でいっぱいだ。", "葉緑素は、日光をとらえて栄養を作る。", "日が短くなると、木はそれを作るのをやめる。",
            "緑が薄れて、かくれていた黄色があらわれる。", "新しく赤い色素を作る木もある。", "つまり秋の色の一部は、最初からそこにあったのだ。"],
        gloss=["chlorophyll:葉緑素", "capture:とらえる", "shorten:短くなる", "produce:作り出す", "fade:薄れる", "reveal:あらわにする", "pigment:色素", "all along:最初からずっと"],
        hook="紅葉の色、実は最初から葉の中に?🍁", tags=f"{LS} #科学"),
    "walking": dict(LISTEN, mystery="brain", mysteryValue="WALK?", hint="👂ヒント:4文目に注目",
        q="What did a year of walking do to older adults' brains?", q_ja="1年間のウォーキングで\n脳はどう変わった?",
        choices=["The stretchers' memory center grew the most.", "Walking made part of the brain bigger."], answer=2,
        answer_ja="ウォーキングで、脳の一部が大きくなった。",
        hl=["adults", "gentle", "scanned", "memory", "grown", "shrunk", "reverse"],
        shots=[
            ("Scientists asked older adults to walk three times a week.", dict(type="wide", bg="street", eyes="happy", mouth="smile", cam="pan")),
            ("Another group only did gentle stretching.", dict(type="full", bg="room", eyes="normal", mouth="smile", color="#d6457a", cam="push")),
            ("After a year, they scanned everyone's brains.", dict(type="insert", bg="lab", insert="brain", value="SCAN", cam="push")),
            ("The walkers' memory center had grown by two percent.", dict(type="insert", bg="lab", insert="brain", value="+2%", cam="snap")),
            ("The stretchers' had actually shrunk a little.", dict(type="split", bg="dark", left="WALK +2%", right="STRETCH −", eyes="happy", mouth="grin", eyes2="worried", mouth2="wavy", cam="push")),
            ("Exercise can reverse brain aging, at least partly.", dict(type="face", bg="street", eyes="smug", mouth="grin", cam="pull")),
        ],
        ja=["科学者は、高齢者に週3回歩いてもらった。", "別のグループは、軽いストレッチだけをした。", "1年後、全員の脳を調べた。",
            "歩いたグループの記憶の中枢は、2%大きくなっていた。", "ストレッチのグループは、むしろ少し縮んでいた。", "運動は、脳の老化を少なくとも一部、逆戻りさせられる。"],
        gloss=["older adult:高齢者", "gentle:軽い、おだやかな", "scan:(画像で)調べる", "memory center:記憶の中枢(海馬)", "grow:大きくなる", "shrink:縮む", "reverse:逆戻りさせる", "aging:老化"],
        hook="1年歩くと、脳が若返る?🚶", tags=f"{LS} #自己啓発"),
    "because": dict(LISTEN, mystery="card", mysteryValue="BECAUSE…", hint="👂ヒント:5文目に注目",
        q="Why did more people let a stranger cut in line?", q_ja="列への割り込みを\n許す人が増えたのはなぜ?",
        choices=["Just hearing a reason made them say yes.", "They were in a rush to make copies."], answer=1,
        answer_ja="理由を聞いただけで、OKしたくなったから。",
        hl=["copier", "reason", "rush", "triggered", "compliance", "favor"],
        shots=[
            ("A researcher asked to cut in line at a copier.", dict(type="two", bg="office", eyes="normal", mouth="smile", eyes2="worried", mouth2="flat", cam="pan")),
            ("With no reason, sixty percent agreed.", dict(type="insert", bg="dark", insert="card", value="60%", cam="push")),
            ("Adding because I'm in a rush raised it to ninety-four.", dict(type="insert", bg="dark", insert="card", value="94%", cam="snap")),
            ("Even because I need to make copies worked.", dict(type="lens", bg="office", insert="card", value="BECAUSE…", focus=[540, 1010])),
            ("The word because alone triggered compliance.", dict(type="eyes", bg="dark", eyes="shock", cam="shake")),
            ("Next time you ask a favor, give a reason.", dict(type="face", bg="office", eyes="smug", mouth="grin", cam="whip")),
        ],
        ja=["研究者が、コピー機の列に割り込ませてほしいと頼んだ。", "理由なしだと、60%がOKした。", "「急いでいるので」を足すと、94%に上がった。",
            "「コピーをとりたいので」でさえ、うまくいった。", "「なぜなら」という言葉だけで、承諾が引き出された。", "次にお願いするときは、理由を添えよう。"],
        gloss=["cut in line:列に割り込む", "copier:コピー機", "reason:理由", "in a rush:急いで", "trigger:引き起こす", "compliance:承諾", "favor:お願い"],
        hook="「なぜなら」の一言で、OKが増える?🗣️", tags=f"{LS} #心理学"),
    "case13_peakend": dict(IVY, caseNo="CASE #13", mystery="card", mysteryValue="60s vs 90s", hint="🔍手がかり:最後の30秒",
        q="Why did people choose the longer, colder trial?", q_ja="長いほうの冷水を\nもう一度選んだのはなぜ?",
        choices=["Trial one was slightly warmer at the end.", "Its gentler ending left a better memory."], answer=2,
        answer_ja="終わりがやさしかったので、良い記憶が残ったから。",
        hl=["dipped", "icy", "painful", "slightly", "repeat", "peak"],
        shots=[
            ("Volunteers dipped a hand in icy water twice.", dict(type="insert", bg="lab", insert="card", value="ICY WATER", cam="rise")),
            ("Trial one: sixty painful seconds.", dict(type="insert", bg="dark", insert="clock", value="60 s", cam="snap")),
            ("Trial two: the same, plus thirty slightly warmer ones.", dict(type="insert", bg="dark", insert="clock", value="+30 s", cam="push", stamp="CLUE 1")),
            ("Most chose to repeat the longer trial.", dict(type="two", bg="lab", det=True, color="#2d6a4f", eyes="smug", mouth="smile", eyes2="happy", mouth2="grin", cam="pan")),
            ("We judge experiences by their peak and their ending.", dict(type="ots", bg="lab", det=True, color="#2d6a4f", eyes2="shock", mouth2="o", cam="tilt", mark=[560, 1140, 170])),
            ("Elementary: the peak-end rule.", dict(type="silhouette", bg="dark", det=True, eyes="smug", wipe="iris", stamp="SOLVED")),
        ],
        ja=["参加者は、氷のように冷たい水に手を2回ひたした。", "1回目:つらい60秒。", "2回目:同じ60秒に、少しだけ温かい30秒を足したもの。",
            "ほとんどの人が、長いほうをもう一度選んだ。", "私たちは、経験をピークと終わり方で判断する。", "初歩的なことだよ。「ピーク・エンドの法則」だ。"],
        gloss=["dip:ひたす", "icy:氷のように冷たい", "painful:つらい", "slightly:わずかに", "repeat:くり返す", "peak:ピーク、いちばん強いところ"],
        grammar=["judge A by B", "「B で A を判断する」。by は判断の基準を表す。", "We judge experiences by their peak and their ending.(経験をピークと終わり方で判断する)"],
        hook="長くて冷たいほうを選んだのはなぜ?🧊", tags=IV),
    "case14_ikea": dict(IVY, caseNo="CASE #14", mystery="card", mysteryValue="DIY?", hint="🔍手がかり:組み立てたかどうか",
        q="Why did people value their own IKEA boxes more?", q_ja="自分で組み立てた箱を\n高く評価したのはなぜ?",
        choices=["Building it themselves made it feel special.", "The boxes were already built and special."], answer=1,
        answer_ja="自分で組み立てたことで、特別に感じたから。",
        hl=["assembled", "plain", "identical", "bid", "sweat", "effort", "breeds"],
        shots=[
            ("Some volunteers assembled plain IKEA boxes themselves.", dict(type="insert", bg="room", insert="card", value="ASSEMBLE", cam="pan")),
            ("Others received identical boxes, already built.", dict(type="insert", bg="room", insert="card", value="ALREADY BUILT", cam="push")),
            ("The builders bid about sixty percent more.", dict(type="insert", bg="bank", insert="chart", value="+63%", cam="snap", stamp="CLUE 1")),
            ("Their own sweat made the box feel special.", dict(type="face", bg="room", det=True, color="#2d6a4f", eyes="smug", mouth="grin", cam="whip")),
            ("Effort breeds love for what we create.", dict(type="ots", bg="room", det=True, color="#2d6a4f", eyes2="happy", mouth2="grin", cam="tilt", mark=[560, 1140, 170])),
            ("Case closed: the IKEA effect.", dict(type="silhouette", bg="dark", det=True, eyes="smug", wipe="iris", stamp="SOLVED")),
        ],
        ja=["一部の参加者は、シンプルなイケアの箱を自分で組み立てた。", "ほかの参加者は、組み立て済みの同じ箱をもらった。", "組み立てた人は、約60%高い値をつけた。",
            "自分の汗が、その箱を特別に感じさせた。", "努力は、自分が作ったものへの愛着を生む。", "事件解決。「イケア効果」だ。"],
        gloss=["assemble:組み立てる", "plain:飾りのない", "identical:まったく同じ", "bid:値をつける", "sweat:汗、苦労", "effort:努力", "breed:生む"],
        grammar=["再帰代名詞 themselves", "「自分たちで」。assembled the boxes themselves(箱を自分たちで組み立てた)。", "主語と同じ人を指す。myself / yourself / himself なども同じ使い方。"],
        hook="自分で作ると、価値が上がる?🔧", tags=IV),
    "case15_jam": dict(IVY, caseNo="CASE #15", mystery="card", mysteryValue="24 vs 6", hint="🔍手がかり:種類の数",
        q="Why did fewer people buy jam from the bigger display?", q_ja="ジャムの種類が多いほど\n売れなかったのはなぜ?",
        choices=["The big display drew three percent of the crowd.", "Too many choices made it hard to decide."], answer=2,
        answer_ja="選択肢が多すぎて、決められなくなったから。",
        hl=["tasting", "flavors", "display", "drew", "options", "paralyze", "overload"],
        shots=[
            ("A store set up a jam tasting table.", dict(type="insert", bg="room", insert="card", value="JAM TASTING", cam="pan")),
            ("Some days it offered twenty-four flavors. Other days, six.", dict(type="split", bg="dark", left="24", right="6", eyes="happy", mouth="grin", eyes2="normal", mouth2="smile", cam="push")),
            ("The big display drew bigger crowds.", dict(type="two", bg="room", det=True, color="#2d6a4f", eyes="smug", mouth="smile", eyes2="happy", mouth2="grin", cam="push")),
            ("Yet only three percent of them bought jam.", dict(type="insert", bg="dark", insert="card", value="3%", cam="snap", stamp="CLUE 1")),
            ("With six flavors, ten times as many bought.", dict(type="insert", bg="dark", insert="card", value="30%", cam="push")),
            ("Too many options paralyze us. Choice overload.", dict(type="silhouette", bg="dark", det=True, eyes="smug", wipe="iris", stamp="SOLVED")),
        ],
        ja=["あるお店が、ジャムの試食コーナーを作った。", "24種類の日もあれば、6種類の日もあった。", "大きな陳列のほうが、多くの人を集めた。",
            "ところが、買ったのはその3%だけ。", "6種類のときは、10倍の人が買った。", "選択肢が多すぎると、私たちは動けなくなる。「選択過多」だ。"],
        gloss=["tasting:試食", "flavor:味、種類", "display:陳列", "draw:引きつける", "option:選択肢", "paralyze:動けなくする", "overload:過多"],
        grammar=["〜 times as many (as …)", "「(…の)〜倍の数」。ten times as many bought(10倍の人が買った)。", "量なら ten times as much、大きさなら ten times as big のようになる。"],
        hook="種類が多いほど、売れない?🍓", tags=IV),
    "sci013_lightning": dict(SCI, no="#013", mystery="card", mysteryValue="FLASH!", bgm="cycles",
        q="Why do we see lightning before we hear thunder?", q_ja="雷の光が\n音より先なのはなぜ?",
        choices=["Light travels faster than sound.", "Sound is faster than light."], answer=1, answer_ja="光は音より速いから。",
        hl=["light", "fast", "slower"],
        shots=[
            ("Lightning makes light and sound.", dict(type="insert", bg="dark", insert="card", value="FLASH!", cam="pull")),
            ("Light is very, very fast.", dict(type="insert", bg="dark", insert="card", value="LIGHT: FAST", cam="push")),
            ("Sound is much slower!", dict(type="face", bg="lab", sci=True, color="#f4f4f0", eyes="shock", mouth="o", cam="whip", hud="SOUND: SLOW")),
        ],
        ja=["雷は、光と音を出す。", "光は、とてもとても速い。", "音は、ずっと遅い!"],
        gloss=["light:光", "fast:速い", "slow:遅い"],
        hook="雷の光が先に見える理由は?⚡", tags=SC),
    "sci014_venus": dict(SCI, no="#014", mystery="card", mysteryValue="VENUS", bgm="vapour",
        q="On Venus, which is longer: a day or a year?", q_ja="金星では、\n1日と1年どっちが長い?",
        choices=["The year, because Venus turns quickly.", "The day."], answer=2, answer_ja="1日のほうが長い。",
        hl=["slowly", "day", "year"],
        shots=[
            ("Venus turns very slowly.", dict(type="insert", bg="dark", insert="card", value="VENUS", cam="pull")),
            ("One day there is two hundred forty-three Earth days.", dict(type="insert", bg="dark", insert="clock", value="243 DAYS", cam="push")),
            ("Its year is only two hundred twenty-five!", dict(type="face", bg="lab", sci=True, color="#f4f4f0", eyes="shock", mouth="o", cam="whip", hud="YEAR: 225")),
        ],
        ja=["金星は、とてもゆっくり回る。", "そこでの1日は、地球の243日分。", "1年は、たった225日!"],
        gloss=["slowly:ゆっくり", "day:1日", "year:1年"],
        hook="1日が1年より長い星がある?🪐", tags=SC),
    "sci015_heart": dict(SCI, no="#015", mystery="card", mysteryValue="♥ ?", bgm="tunnel",
        q="About how many times does your heart beat in a day?", q_ja="心臓は1日に\nだいたい何回動く?",
        choices=["About one hundred thousand.", "About seventy."], answer=1, answer_ja="約10万回",
        hl=["chest", "beats", "thousand"],
        shots=[
            ("Put your hand on your chest.", dict(type="face", bg="lab", sci=True, color="#f4f4f0", eyes="happy", mouth="smile", cam="pull")),
            ("Your heart beats about seventy times a minute.", dict(type="insert", bg="dark", insert="clock", value="70 / MIN", cam="push")),
            ("That's about one hundred thousand times a day!", dict(type="insert", bg="dark", insert="card", value="100,000 / DAY", cam="snap")),
        ],
        ja=["胸に手を当ててみよう。", "心臓は、1分に約70回動く。", "1日では、約10万回!"],
        gloss=["chest:胸", "beat:(心臓が)打つ", "thousand:千"],
        hook="心臓は1日に何回動く?❤️", tags=SC),
    "sea009_slow": dict(SEA, voice=GEORGE, no="#009", mystery="seahorse", cover=0, bgm="lantern",
        q="Which fish is one of the slowest swimmers?", q_ja="泳ぐのがとても\nおそい魚は?",
        choices=["A fish with big, fast fins.", "The seahorse."], answer=2, answer_ja="タツノオトシゴ",
        hl=["standing", "fins", "flutter"],
        shots=[
            ("Seahorses swim standing up.", dict(type="insert", bg="ocean", insert="seahorse", cam="pull", sonar="SEAHORSE")),
            ("Their tiny fins flutter very fast.", dict(type="lens", bg="ocean", insert="seahorse", focus=[520, 950], wipe="slide")),
            ("But some move only about one and a half meters an hour!", dict(type="insert", bg="ocean", insert="seahorse", value="1.5 m / HOUR", cam="push")),
        ],
        ja=["タツノオトシゴは、立ったまま泳ぐ。", "小さなひれを、とても速くぱたぱた動かす。", "でも、1時間に1.5メートルほどしか進まない種類もいる!"],
        gloss=["stand up:立つ", "fin:ひれ", "flutter:ぱたぱた動く"],
        hook="1時間に1.5mしか進まない魚?🐠", tags=SE),
    "sea010_bluewhale": dict(SEA, voice=MATILDA, no="#010", mystery="card", mysteryValue="BIGGEST?", cover=1, bgm="whales",
        q="What is the biggest animal that has ever lived?", q_ja="これまでで\nいちばん大きな動物は?",
        choices=["The blue whale.", "A huge dinosaur."], answer=1, answer_ja="シロナガスクジラ",
        hl=["huge", "even", "largest"],
        shots=[
            ("Dinosaurs were huge.", dict(type="insert", bg="ocean", insert="card", value="DINOSAUR", cam="pull")),
            ("But the blue whale is even bigger.", dict(type="insert", bg="ocean", insert="card", value="BLUE WHALE", cam="push", sonar="BLUE WHALE")),
            ("It is the largest animal ever!", dict(type="insert", bg="ocean", insert="card", value="LARGEST EVER", cam="snap")),
        ],
        ja=["恐竜は巨大だった。", "でも、シロナガスクジラはさらに大きい。", "これまででいちばん大きな動物!"],
        gloss=["huge:巨大な", "even:さらに(比べる言葉を強める)", "largest:いちばん大きい"],
        hook="恐竜より大きい動物がいる?🐳", tags=SE),
    "geo010_tokyo": dict(GEO, no="#010", cover=1, hint="👂ヒント:2文目の数字に注目", mysteryMap={"from": [139.75, 35.68, 16]},
        q="What is special about Greater Tokyo?", q_ja="東京圏の\nすごいところは?",
        choices=["It is still a small fishing village.", "Tens of millions of people live there."], answer=2,
        answer_ja="何千万人もの人が住んでいる。",
        hl=["fishing", "village", "area", "million", "commuters"],
        shots=[
            ("Tokyo started as a small fishing village called Edo.", dict(type="map", bg="dark", map={"from": [139.5, 35.7, 12], "to": [139.75, 35.68, 20], "dots": [[139.75, 35.68]], "labels": [[139.75, 35.95, "EDO"]]})),
            ("Today, Greater Tokyo holds about thirty-seven million people.", dict(type="map", bg="dark", hud="≈ 37,000,000", map={"from": [139.7, 35.7, 15], "to": [139.7, 35.7, 12],
                "dots": [[139.7, 35.69], [139.64, 35.44], [139.65, 35.86], [140.12, 35.61]]})),
            ("That's more people than in all of Australia.", dict(type="map", bg="dark", hud="> AUSTRALIA", map={"from": [139.7, 35.7, 10], "hl": ["392"]})),
            ("It's one of the biggest city areas on Earth.", dict(type="map", bg="dark", map={"from": [139.7, 35.7, 8], "to": [139.7, 35.7, 6], "hl": ["392"], "dots": [[139.7, 35.69]]})),
            ("Trains carry millions of commuters every day.", dict(type="map", bg="dark", map={"from": [139.7, 35.7, 16],
                "arrows": [[139.35, 35.95, 139.68, 35.72], [140.15, 35.6, 139.78, 35.68], [139.55, 35.4, 139.7, 35.64]]})),
        ],
        ja=["東京は、江戸という小さな漁村から始まった。", "今、東京圏には約3,700万人が住んでいる。", "オーストラリア全体の人口より多い。", "地球上で最大級の都市圏の1つだ。", "電車が、毎日何百万人もの通勤客を運ぶ。"],
        gloss=["fishing village:漁村", "area:地域", "hold:(人を)かかえる", "million:百万", "commuter:通勤・通学する人"],
        hook="東京圏の人口、オーストラリアより多い?🏙️", tags=GE),
    "geo011_tsushima": dict(GEO, no="#011", cover=1, hint="👂ヒント:2文目の数字に注目", mysteryMap={"from": [129.3, 34.8, 12]},
        q="How close is Japan to South Korea?", q_ja="日本と韓国は、\nどれくらい近い?",
        choices=["About fifty kilometers at the closest point.", "Over a thousand kilometers."], answer=1,
        answer_ja="いちばん近い所で約50キロ。",
        hl=["sits", "tip", "clear", "neighbor", "capital"],
        shots=[
            ("Tsushima sits between Kyushu and Korea.", dict(type="map", bg="dark", map={"from": [130, 34, 8], "to": [129.4, 34.6, 13], "hl": ["392", "410"],
                "labels": [[129.3, 34.2, "TSUSHIMA"], [130.8, 33.0, "KYUSHU"], [128.2, 35.8, "KOREA"]]})),
            ("From its tip, Busan is just fifty kilometers away.", dict(type="map", bg="dark", hud="≈ 50 km", map={"from": [129.3, 34.95, 18],
                "arrows": [[129.47, 34.7, 129.1, 35.13]], "dots": [[129.07, 35.18]], "labels": [[128.9, 35.35, "BUSAN"]]})),
            ("On clear days, you can see Korea.", dict(type="map", bg="dark", map={"from": [129.3, 34.9, 16], "to": [129.2, 35.0, 19], "hl": ["410"]})),
            ("Tokyo is over a thousand kilometers away.", dict(type="map", bg="dark", hud="1,000+ km", map={"from": [134, 35, 5.5], "hl": ["392"],
                "arrows": [[129.3, 34.4, 139.6, 35.7]], "dots": [[139.69, 35.69]], "labels": [[139.69, 36.4, "TOKYO"]]})),
            ("Your neighbor can be closer than your capital.", dict(type="map", bg="dark", map={"from": [133, 35, 6], "to": [130, 34.8, 8], "hl": ["392", "410"]})),
        ],
        ja=["対馬は、九州と韓国のあいだにある。", "島の先端から釜山まで、たった50キロ。", "晴れた日には、韓国が見える。", "東京までは、1,000キロ以上ある。", "となりの国のほうが、自分の国の首都より近いこともある。"],
        gloss=["sit:位置する", "tip:先端", "clear:晴れた", "neighbor:となりの国、となりの人", "capital:首都"],
        hook="日本から韓国が見える場所がある?👀", tags=GE),
    "geo012_kuroshio": dict(GEO, no="#012", cover=1, hint="👂ヒント:3文目に注目", mysteryMap={"from": [133, 30, 5]},
        q="What keeps Japan's Pacific coast warm?", q_ja="日本の太平洋側を\n暖かくしているのは?",
        choices=["Rich fishing grounds that warm the coast.", "A warm current flowing up from the tropics."], answer=2,
        answer_ja="熱帯から流れてくる、暖かい海流。",
        hl=["powerful", "current", "flows", "tropics", "warmth", "softens", "grounds"],
        shots=[
            ("A powerful ocean current flows past Japan.", dict(type="map", bg="dark", map={"from": [133, 30, 5], "to": [133, 30, 5.6], "arrows": [[123, 22, 127, 27], [127, 27, 131, 31]]})),
            ("It's called the Kuroshio, or black current.", dict(type="map", bg="dark", map={"from": [132, 30, 6],
                "arrows": [[123, 22, 127, 27], [127, 27, 131, 31], [131, 31, 136, 33.3], [136, 33.3, 141, 35.3]], "labels": [[129.5, 28.0, "KUROSHIO"]]})),
            ("It carries warm water up from the tropics.", dict(type="map", bg="dark", hud="≈ 25°C", map={"from": [127, 22, 6], "to": [128, 25, 6.5],
                "arrows": [[123, 18, 125, 23], [125, 23, 128, 27]], "labels": [[124, 15.5, "TROPICS"]]})),
            ("That warmth softens winters along the Pacific coast.", dict(type="map", bg="dark", map={"from": [136, 34, 8], "hl": ["392"],
                "arrows": [[131, 31, 136, 33.3], [136, 33.3, 141, 35.3]]})),
            ("It also brings rich fishing grounds.", dict(type="map", bg="dark", map={"from": [140, 35.5, 9], "to": [140.5, 36, 10],
                "dots": [[141.3, 36.6], [140.5, 34.9], [138.5, 34.5]], "labels": [[141.9, 37.3, "FISH!"]]})),
        ],
        ja=["力強い海流が、日本のそばを流れている。", "「黒潮」と呼ばれる。", "熱帯から、暖かい水を運んでくる。", "その暖かさが、太平洋側の冬をやわらげる。", "豊かな漁場ももたらす。"],
        gloss=["powerful:力強い", "current:海流", "flow:流れる", "tropics:熱帯", "warmth:暖かさ", "soften:やわらげる", "fishing ground:漁場"],
        hook="日本の冬を暖める、黒い流れ?🌊", tags=GE),
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


MUSICS = {"the-waves": "The Waves / Otto.mp3", "just-flow": "Just Flow / Hartzmann", "lefty": "Lefty / Blue Wednesday",
          "tokyo-spring": "Tokyo Spring (wooll Remix) / Yawnathan", "darkside": "Darkside / Oliver Michael",
          "to-the-moon": "To The Moon / 21 On The Block", "funk-formula": "Funk Formula / Nick Petrov",
          "cycles": "Cycles / DADA", "tunnel": "Tunnel / Danijel Zambo", "vapour": "Vapour / Simon Folwar",
          "whales": "Death Of The Whales / Sky Cassette", "lantern": "Lantern / all:ambient", "sailing": "Sailing Home / Oliver Massa"}  # cycles 以降は assets/bgm/(公開しない)
MUSIC = "Music: The Waves / Otto.mp3 — Music from #Uppbeat (free for Creators!)"


def caption(sc):
    sp = "\u3000"
    return "\n".join([sc["hook"], sp, "🎧 25秒の英語、聞き取れる?", "AとBどっち?コメントで答えてね👇",
                      "正解・全文和訳・単語の意味はコメント欄に📌", sp, sc["tags"], sp,
                      f"Music: {MUSICS[sc.get('bgm', 'the-waves')]} — Music from #Uppbeat (free for Creators!)"])


def cover(name, sc, props, shots, out_dir):
    """カバー画像(out_dir/<name>_cover.jpg)。cover=カット番号で指定、無ければ顔・虫めがね・分割・目のアップの最初のカット"""
    k = sc.get("cover")
    if k is None:  # 顔 > 虫めがね > 分割 > 目のアップ の順で、最初に出てくるカット
        k = next((i for t in ("face", "lens", "split", "eyes") for i, s in enumerate(shots) if s["type"] == t), 0)
    hook = sc["hook"]
    if "\n" not in hook and len(hook) > 9:  # 読点か「vs」のあと、無ければ真ん中に近い助詞のあとで改行
        if "、" in hook:
            hook = hook.replace("、", "、\n", 1)
        elif " vs " in hook:
            hook = hook.replace(" vs ", "\nvs ", 1)
        else:
            cut = [i + 1 for i, ch in enumerate(hook[:-3]) if ch in "のはがをにでも" and i >= 3]
            if cut:
                i = min(cut, key=lambda i: abs(i - len(hook) / 2))
                hook = hook[:i] + "\n" + hook[i:]
    cp = dict(props, coverShot=shots[k], hook=hook, badge=sc.get("caseNo") or sc.get("no"))
    pf = out_dir / f"{name}_cover.json"
    pf.write_text(json.dumps(cp, ensure_ascii=False))
    subprocess.run(["npx", "remotion", "still", "src/index.ts", "IfCover", str(out_dir / f"{name}_cover.jpg"), f"--props={pf}",
                    "--image-format=jpeg", "--jpeg-quality=90"], cwd=V3D, check=True, stdout=subprocess.DEVNULL)


def build(name):
    sc = SHORTS[name]
    mr.load_env()
    out_dir = ROOT / "out" / {"ivy": "ivy_short", "sci": "sci_short", "sea": "sea_short", "geo": "geo_short"}.get(sc.get("account"), "if_short")
    T_IN, T_CH, T_END = sc.get("intro", INTRO), sc.get("choice", CHOICE), sc.get("end", END)  # 冒頭・2択・最後の秒数(回ごとに変えられる)
    PUB.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [ln for ln, _ in sc["shots"]]
    if sc.get("gap"):  # 1文ずつ読み、文のあいだに間を入れる(ゆっくり聞こえる)
        parts, words, t0 = [], [], 0.0
        for ln in lines:
            mp3, ws = tts_words(sc["voice"], ln, sc.get("speed"))
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp3), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                                 capture_output=True, check=True).stdout
            a = np.frombuffer(raw, np.float32)
            words += [[w, st + t0, en + t0] for w, st, en in ws]
            parts += [a, np.zeros(int(SR * sc["gap"]), np.float32)]
            t0 += len(a) / SR + sc["gap"]
        story = PUB / f"{name}_story.wav"
        sf.write(story, np.concatenate(parts[:-1]), SR)
    else:
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
        ja = {g.split(":")[0].lower(): g.split(":", 1)[1].split("、")[0].split("(")[0] for g in sc["gloss"] if " " not in g.split(":")[0]}
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
    bgm_id = sc.get("bgm", "the-waves")  # docs/bgm/<id>.mp3。クレジットは MUSICS
    bgm = PUB / f"bgm_{bgm_id}.mp3"
    if not bgm.exists():
        src = ROOT / "docs" / "bgm" / f"{bgm_id}.mp3"
        bgm.write_bytes((src if src.exists() else ROOT / "assets" / "bgm" / f"{bgm_id}.mp3").read_bytes())
    tick = PUB / "tick.wav"
    sf.write(tick, np.zeros(int(SR * 0.1), np.float32), SR)  # 時計の音は sfx に入れたので無音
    props = dict(q=sc["q"], q_ja=sc["q_ja"], choices=sc["choices"], answer=sc["answer"], words=wlist, intro=T_IN,
                 scenes=[], shots=shots, choiceAt=round(choice_at, 3), answerAt=round(choice_at + T_CH, 3), total=round(total, 3),
                 story=f"if/{story.name}", sfx=f"if/{name}_sfx.wav", tick="if/tick.wav", bgm=f"if/{bgm.name}",
                 choiceSec=int(T_CH), **{k: sc[k] for k in ("kicker", "title", "caseNo", "endText", "bg1", "bg2", "no", "mystery", "mysteryBg", "mysteryValue", "mysteryMap", "jaHints", "hint") if k in sc})
    pf = out_dir / f"{name}.json"
    pf.write_text(json.dumps(props, ensure_ascii=False))
    out = out_dir / f"{name}.mp4"
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "IfShort", str(out), f"--props={pf}"], cwd=V3D, check=True,
                   stdout=subprocess.DEVNULL)
    cover(name, sc, props, shots, out_dir)
    out.with_suffix(".txt").write_text(comment(sc))
    warn = f"  ⚠ {MAX_SEC}秒を超えています。台本を短くしてください" if total > MAX_SEC else ""
    print(f"✓ {out}({total:.1f}秒・{len(shots)}カット){warn}")


if __name__ == "__main__":
    for n in (sys.argv[1:] or ["compound"]):
        build(n)
