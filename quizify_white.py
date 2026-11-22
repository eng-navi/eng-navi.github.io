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
    # ---- 11/16〜(ターゲット1900 Section 2 の見出し語から、入試で問われる形を。例文はオリジナル)----
    dict(intro="前置詞いる?いらない?ひっかけ注意⚠️\n今日は「気づく」「言及する」の2つです。", tags="#英単語 #英語学習 #大学受験",
         items=[
             (191, "notice A doing", "Aが〜しているのに気づく", "がしているのに気づく",
              "私は男の子が泣いているのに気づいた。", "I noticed a boy crying.",
              ["notice A do(〜するのに気づく)の形もある", "名詞の notice は「通知、掲示」", "at short notice で「急な知らせで」"]),
             (192, "refer to A", "Aに言及する、Aを参照する", "に言及する",
              "その記事は新しい研究に言及している。", "The article refers to a new study.",
              ["前置詞は to", "refer to A as B で「AをBと呼ぶ」", "名詞は reference(言及、参照)"]),
         ]),
    dict(intro="to をつけたら×!入試の定番ミスです✍️\n今日は「近づく」「〜かなと思う」の2つ。", tags="#英語学習 #英検2級 #共通テスト",
         items=[
             (193, "approach A", "Aに近づく", "に近づく",
              "電車が駅に近づいた。", "The train approached the station.",
              ["approach to A は×。前置詞なしで目的語をとる", "名詞の approach は「取り組み方」", "an approach to A なら「Aへの取り組み方」でOK"]),
             (194, "wonder if ~", "〜かなと思う", "かなと思う",
              "明日は雨が降るかなと思う。", "I wonder if it will rain tomorrow.",
              ["if の代わりに why / how なども使える", "wonder at A で「Aに驚く」", "wander(歩き回る)とつづりを区別"]),
         ]),
    dict(intro="問題は solve、質問は answer📝\n今日は「解く」「ふと思いつく」の2つです。", tags="#英単語 #英文法 #大学受験",
         items=[
             (195, "solve a problem", "問題を解く、解決する", "問題を解く",
              "彼女はすぐにその問題を解いた。", "She solved the problem quickly.",
              ["「質問に答える」は answer a question(solve は×)", "名詞は solution(解決法)", "a solution to A で「Aの解決法」"]),
             (196, "It occurs to A that ~", "Aに〜という考えが浮かぶ", "に…という考えが浮かぶ",
              "鍵を忘れたことが、ふと頭に浮かんだ。", "It occurred to me that I had forgotten my key.",
              ["主語は It。人は to のあと", "occur には「起こる」の意味も", "名詞は occurrence(発生)"]),
         ]),
    dict(intro="「主張する」の使い分け、わかる?🤔\n今日は argue と claim の2つです。", tags="#英語学習 #英作文 #英検2級",
         items=[
             (197, "argue that ~", "〜だと主張する", "だと主張する",
              "彼は会議を短くすべきだと主張した。", "He argued that meetings should be shorter.",
              ["「理由を挙げて主張する」感じ", "argue for / against A で「Aに賛成/反対の意見を述べる」", "名詞は argument(論争、論拠)"]),
             (198, "claim that ~", "〜だと(根拠なく)主張する", "だと主張する",
              "彼はその宝石は自分のものだと主張している。", "He claims that the jewel is his.",
              ["「まだ証明されていないこと」を主張するときによく使う", "日本語の「クレーム(苦情)」は complaint", "claim A from B で「BにAを要求する」"]),
         ]),
    dict(intro="英作文で使える2つの表現💡\n今日は「自分の考えを述べる」「結論を出す」です。", tags="#英作文 #英単語 #大学受験",
         items=[
             (199, "express oneself", "自分の考えを述べる", "自分の考えを述べる",
              "英語で自分の考えを述べるのは難しい。", "It is hard to express myself in English.",
              ["oneself は主語に合わせて変える(myself など)", "名詞は expression(表現、表情)", "express には「急行の」の意味も"]),
             (200, "draw a conclusion", "結論を出す", "結論を出す",
              "その結果から結論を出すのはまだ早い。", "It's too early to draw a conclusion from the results.",
              ["動詞は draw(make も使える)", "draw attention to A で「Aに注意を引く」", "from A で「Aから」を加えられる"]),
         ]),
    dict(intro="A と B の位置に注意!並べかえの定番です🔁\n今日は「供給する」「〜のほうを好む」の2つ。", tags="#英単語 #英文法 #共通テスト",
         items=[
             (201, "supply A with B", "AにBを供給する", "AにBを供給する",
              "その農場は町に野菜を供給している。", "The farm supplies the town with vegetables.",
              ["supply B to A と言いかえられる", "名詞の supply は「供給」。反対は demand(需要)", "in short supply で「不足して」"]),
             (202, "prefer A to B", "BよりAを好む", "BよりAを好む",
              "私はコーヒーより紅茶のほうが好きだ。", "I prefer tea to coffee.",
              ["比べる相手は than ではなく to", "prefer to do で「〜するほうを好む」", "名詞は preference(好み)"]),
         ]),
    dict(intro="about や to をつけていない?⚠️\n今日は「〜について話す」「連絡を取る」の2つです。", tags="#英語学習 #英検2級 #大学受験",
         items=[
             (203, "mention A", "Aについて話す、触れる", "について話す",
              "彼は新しい計画について話した。", "He mentioned the new plan.",
              ["mention about A は×。前置詞なしで目的語をとる", "not to mention A で「Aは言うまでもなく」", "Don't mention it. で「どういたしまして」"]),
             (204, "contact A", "Aに連絡を取る", "に連絡を取る",
              "質問があれば私に連絡してください。", "Please contact me if you have any questions.",
              ["contact to A は×", "名詞では contact with A(Aとの接触)", "a contact number で「連絡先の電話番号」"]),
         ]),
    dict(intro="前置詞までセットで覚えよう✍️\n今日は「申し込む」「探す」の2つです。", tags="#英単語 #英語学習 #大学受験",
         items=[
             (205, "apply for A", "Aに申し込む", "に申し込む",
              "彼女はその仕事に申し込んだ。", "She applied for the job.",
              ["apply A to B なら「AをBに適用する」", "名詞は application(申し込み)、applicant(応募者)", "appliance は「(家庭用の)電気器具」"]),
             (206, "search for A", "Aを探す", "を探す",
              "私たちはなくした財布を探した。", "We searched for the lost wallet.",
              ["search A for B は「Bを求めてA(場所)を捜す」", "search the room なら「部屋の中を捜す」", "in search of A で「Aを探して」"]),
         ]),
    dict(intro="to と from、どっちを使う?🧩\n今日は「つなぐ」「苦しむ」の2つです。", tags="#英単語 #英文法 #英検2級",
         items=[
             (207, "connect A to B", "AをBにつなぐ", "AをBにつなぐ",
              "パソコンをプリンターにつないで。", "Please connect the computer to the printer.",
              ["to の代わりに with も使える", "名詞は connection(関連、接続)", "in connection with A で「Aに関連して」"]),
             (208, "suffer from A", "A(病気など)で苦しむ", "で苦しむ",
              "多くの人が花粉症に苦しんでいる。", "Many people suffer from hay fever.",
              ["前置詞は from", "be suffering from A で「(今)Aにかかっている」", "名詞は suffering(苦しみ)"]),
         ]),
    dict(intro="長文でよく出る2つの表現📚\n今日は「利用する」「影響を与える」です。", tags="#英語学習 #共通テスト #大学受験",
         items=[
             (209, "take advantage of A", "Aを利用する", "を利用する",
              "このセールを利用しよう。", "Let's take advantage of this sale.",
              ["「(人)につけこむ」という悪い意味にもなる", "advantage は「利点」。反対は disadvantage", "形容詞は advantageous(有利な)"]),
             (210, "have an impact on A", "Aに影響を与える", "に影響を与える",
              "スマホは私たちの生活に大きな影響を与えた。", "Smartphones have had a big impact on our lives.",
              ["前置詞は on", "have an effect on A とほぼ同じ意味", "impact には「衝突、衝撃」の意味も"]),
         ]),
    {'intro': '学校や部活でよく使う表現🏫\n今日は「〜に所属する」「〜を卒業する」です。', 'tags': '#英語学習 #大学受験 #英単語', 'items': [(211, 'belong to A', 'Aに所属する、Aのものである', 'に所属する', '私の妹はテニス部に所属している。', 'My sister belongs to the tennis club.', ['進行形にしない(× is belonging)', '「〜のものだ」の意味も:This bag belongs to me.', '名詞 belongings は「持ち物」']), (212, 'graduate from A', 'Aを卒業する', 'を卒業する', '兄は去年大学を卒業した。', 'My brother graduated from college last year.', ['from を忘れやすい(× graduate college は避ける)', '名詞は graduation(卒業)', 'graduate は名詞で「卒業生」'])]},
    {'intro': '気持ちを伝える2つの表現💬\n今日は「AにBのことで謝る」「〜を楽しみにする」です。', 'tags': '#英会話 #英検3級 #英文法', 'items': [(213, 'apologize to A for B', 'AにBのことで謝る', 'に謝る', '遅れたことを先生に謝った。', 'I apologized to my teacher for being late.', ['人の前は to、理由の前は for', '名詞は apology(謝罪)', '× apologize A(前置詞が必要)']), (214, 'look forward to doing', '〜するのを楽しみにする', 'を楽しみにする', 'またお会いできるのを楽しみにしています。', 'I look forward to seeing you again.', ['to の後ろは動名詞(× to see)', 'メールの結びの定番', "進行形 I'm looking forward to も自然"])]},
    {'intro': '長文でよく出る「〜からなる」と「〜に頼る」📚', 'tags': '#共通テスト #大学受験 #英語長文', 'items': [(215, 'consist of A', 'Aから成る', 'から成る', 'チームは5人のメンバーから成る。', 'The team consists of five members.', ['受け身にしない(× is consisted of)', 'be made up of A とほぼ同じ', 'consist in A は「Aにある」で別の意味']), (216, 'rely on A', 'Aに頼る', 'に頼る', '私たちは毎日スマホに頼っている。', 'We rely on our phones every day.', ['depend on A とほぼ同じ', '形容詞は reliable(信頼できる)', 'rely on A for B で「BをAに頼る」'])]},
    {'intro': '責任と能力を表す2つの表現💪\n今日は「〜に責任がある」「〜ができる」です。', 'tags': '#英検準2級 #英単語 #英語学習', 'items': [(217, 'be responsible for A', 'Aに責任がある、Aを担当している', 'に責任がある', '彼はこの企画を担当している。', 'He is responsible for this project.', ['for の後ろは担当すること・原因', '名詞は responsibility(責任)', 'take responsibility for A で「Aの責任をとる」']), (218, 'be capable of doing', '〜する能力がある', 'ができる', 'このロボットは会話をすることができる。', 'This robot is capable of having a conversation.', ['of の後ろは動名詞', 'be able to do と言い換えられる', '名詞は capability(能力)'])]},
    {'intro': '入試の並べかえで出る形📝\n今日は「AにBを思い出させる」「AをBと取りかえる」です。', 'tags': '#大学受験 #英文法 #並べかえ', 'items': [(219, 'remind A of B', 'AにBを思い出させる', 'に思い出させる', 'この歌を聞くと夏休みを思い出す。', 'This song reminds me of summer vacation.', ['人が A、思い出す内容が B', 'remind A to do は「Aに〜するよう念を押す」', '主語は物でよく使う']), (220, 'replace A with B', 'AをBと取りかえる', 'を取りかえる', '古い電池を新しいものと交換した。', 'I replaced the old battery with a new one.', ['A が古いもの、B が新しいもの', '名詞は replacement(交換、後任)', '受け身 A is replaced with B もよく出る'])]},
    {'intro': '気持ちの向きを表す前置詞👀\n今日は「〜に賛成する」「〜を言い張る」です。', 'tags': '#英検2級 #英単語 #前置詞', 'items': [(221, 'approve of A', 'Aに賛成する、Aを認める', 'に賛成する', '両親は私の計画に賛成してくれた。', 'My parents approved of my plan.', ['of を忘れやすい', '反対は disapprove of A', 'approve A(of なし)は「正式に承認する」']), (222, 'insist on doing', '〜すると言い張る', 'を言い張る', '彼は全部自分で払うと言い張った。', 'He insisted on paying for everything.', ['on の後ろは動名詞', 'insist that S (should) do の形もある', '名詞は insistence'])]},
    {'intro': '参加と出席、ちがいわかる?🎤\n今日は「〜に参加する」「〜に出席する」です。', 'tags': '#英語学習 #TOEIC #英単語', 'items': [(223, 'participate in A', 'Aに参加する', 'に参加する', '多くの生徒がボランティア活動に参加した。', 'Many students participated in the volunteer work.', ['in が必要', 'take part in A と同じ意味', '名詞は participation、参加者は participant']), (224, 'attend A', 'Aに出席する', 'に出席する', '明日の会議に出席します。', 'I will attend the meeting tomorrow.', ['前置詞はいらない(× attend to the meeting)', 'attend to A は「Aの世話をする、対応する」', '名詞は attendance(出席)'])]},
    {'intro': 'うまくいく・なじむの2つ🌱\n今日は「〜に成功する」「〜に適応する」です。', 'tags': '#英検2級 #大学受験 #英単語', 'items': [(225, 'succeed in doing', '〜することに成功する', 'に成功する', '彼女は試験に合格することに成功した。', 'She succeeded in passing the exam.', ['in の後ろは動名詞', 'succeed to A は「Aを受けつぐ」', '名詞 success、形容詞 successful']), (226, 'adapt to A', 'Aに適応する、なじむ', 'に適応する', '新しい学校にすぐなじんだ。', 'I quickly adapted to my new school.', ['adopt(採用する)と間違えやすい', 'adapt oneself to A の形もある', '名詞は adaptation'])]},
    {'intro': '見分ける・責める、入試頻出の形⚖️\n今日は「AとBを区別する」「BのことでAを責める」です。', 'tags': '#大学受験 #英文法 #共通テスト', 'items': [(227, 'distinguish A from B', 'AとBを区別する', 'を区別する', '本物と偽物を区別するのは難しい。', 'It is hard to distinguish real ones from fakes.', ['tell A from B と同じ意味', 'distinguish between A and B の形もある', '形容詞 distinguished は「著名な」']), (228, 'blame A for B', 'BのことでAを責める', 'を責める', '彼は失敗を天気のせいにした。', 'He blamed the weather for his failure.', ['責める相手が A、理由が B', 'blame B on A でも同じ意味', 'be to blame for A で「Aの責任がある」'])]},
    {'intro': '毎日使える2つの表現🧹\n今日は「〜を取り除く」「〜をよく知っている」です。', 'tags': '#英会話 #英検準2級 #英語学習', 'items': [(229, 'get rid of A', 'Aを取り除く、処分する', 'を取り除く', '古い服を処分した。', 'I got rid of my old clothes.', ['rid は過去形・過去分詞も rid', 'throw away A より広く「なくす」', 'get rid of a cold で「風邪を治す」']), (230, 'be familiar with A', 'Aをよく知っている', 'をよく知っている', '彼はこのあたりの道をよく知っている。', 'He is familiar with the streets around here.', ['人が主語なら with', '物が主語なら be familiar to 人', '名詞は familiarity'])]},
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
