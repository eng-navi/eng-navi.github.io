"""@quizify_english の黒い「瞬間英作文クイズ」リール(準1級の単語)を作る。

1語ごとに 英単語 → 日本語の意味 → 日本語の例文 → (考える間) → 英語の例文 の順。
間は 2024年の元動画(274〜276)を 0.01 秒単位で測った値。声は前後の無音を切ってから、この間で並べる。

  .venv-tts/bin/python quizify_black.py [番号...]   → out/quizify/black_<最初の番号>.mp4 と .txt(説明欄の全文)

作る前に quizify_words.json(黒で使った単語)と照らし合わせ、かぶっていたら止まる。作った単語は「予定」として記録する。
"""
import hashlib
import re
import json
import os
import subprocess
import tempfile
import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont

import manga_reel as mr

ROOT = Path(__file__).parent
OUT = ROOT / "out" / "quizify"
CACHE = ROOT / "out" / "voice_cache"
FONTS = ROOT / "assets" / "fonts"
SR = 44100
W, H, FPS = 720, 1280, 30

# 声(ElevenLabs)。元動画にいちばん近かったもの。速さは元の読む長さに合わせた
EN_VOICE, EN_SPEED = "pFZP5JQG7iQjIQuC4Bku", 1.07  # Lily(イギリス英語・女性)
# 日本語は音読さんの「ななみ(案内)」= Microsoft の Nanami。元は速度 ×1.3 だが、長さを測ると 1.22 倍が同じになる
JA_VOICE, JA_SPEED = "ja-JP-NanamiNeural", 1.22

# 間(秒)。声が聞こえ始める・聞こえなくなる瞬間どうしの間隔
LEAD = 0.63        # 動画の頭 → 英単語
WORD_MEAN = 0.95   # 英単語 → 意味
MEAN_JA = 0.86     # 意味 → 日本語の例文
JA_EN = 1.67       # 日本語の例文 → 英語の例文(考える間)
EN_NEXT = 0.95     # 英語の例文 → 次の英単語
TAIL = 0.65        # 最後の英語の例文 → 動画の終わり
# 画面は声より少し先に切り替わる
SHOW_EARLY = 0.12  # 意味・日本語の例文
EN_EARLY = 0.18    # 英語の例文
NEXT_AFTER = 0.40  # 英語の例文が終わってから次の単語の画面へ

BG = (29, 29, 29)
MINT = (160, 228, 195)
WHITE = (251, 251, 251)

# 1本ずつ:紹介文とハッシュタグ(毎回書き下ろし)、3語。英検準1級 単熟語EX の見出し語(例文はオリジナル)
# 単語:番号, 英単語, 画面の意味, 読む意味, 日本語の例文, 英語の例文, 豆知識(説明欄に載せる)
REELS = [
    dict(intro="準1級の単語を、瞬間英作文で覚えよう✍️\n今日は「弱い」「気をつける」「傍観者」の3語です。", tags="#英検準1級 #瞬間英作文 #英単語",
         items=[
             (277, "vulnerable", "傷つきやすい、かかりやすい", "傷つきやすい", "子どもは寒さに弱い。", "Children are vulnerable to the cold.",
              ["be vulnerable to A で「Aに弱い、Aを受けやすい」", "名詞は vulnerability(弱さ、脆弱性)", "ITの記事では「システムの脆弱性」の意味でよく出ます"]),
             (278, "heed", "〜に気をつける、心に留める", "気をつける", "彼は医者の助言に従った。", "He heeded his doctor's advice.",
              ["pay heed to A でも同じ意味", "advice・warning(警告)と一緒によく使います", "形容詞は heedless(不注意な)"]),
             (279, "bystander", "傍観者、見物人", "傍観者", "数人の見物人が事故を目撃した。", "Several bystanders witnessed the accident.",
              ["stand by(そばに立つ、傍観する)から", "似た語は onlooker(見物人)", "innocent bystander で「巻き添えになった人」"]),
         ]),
    dict(intro="長文によく出る準1級単語、瞬間英作文で言えるかな?🗣️\n今日は「混雑」「捨てる」「炎」の3語です。", tags="#英検準1級 #英単語 #英語学習",
         items=[
             (280, "congestion", "(交通・場所などの)混雑", "混雑", "新しい道路で渋滞が減った。", "The new road reduced traffic congestion.",
              ["traffic congestion で「交通渋滞」", "形容詞は congested(混雑した)", "nasal congestion は「鼻づまり」"]),
             (281, "discard", "〜を捨てる、処分する", "捨てる", "私は古い服を捨てた。", "I discarded my old clothes.",
              ["throw away とほぼ同じ意味", "dis(離す)+ card(カード):トランプでカードを捨てるイメージ", "名詞で「捨てられた物」の意味もあります"]),
             (282, "blaze", "(燃え盛る)炎、火炎", "炎", "消防士たちは火をすぐに消した。", "Firefighters quickly put out the blaze.",
              ["fire より「激しく燃え上がる炎」", "動詞で「燃え上がる」", "blazing hot で「焼けつくように暑い」"]),
         ]),
    dict(intro="日常でも使える準1級単語です✨\n今日は「不器用な」「取り除く」「認める」の3語。", tags="#英検準1級 #パス単 #瞬間英作文",
         items=[
             (283, "clumsy", "不器用な、ぎこちない", "不器用な", "彼は箸の使い方が不器用だ。", "He is clumsy with chopsticks.",
              ["be clumsy with A で「Aの扱いが不器用だ」", "名詞は clumsiness(不器用さ)", "反対は skillful(器用な)"]),
             (284, "eliminate", "〜を取り除く、敗退させる", "取り除く", "この薬は痛みを取り除く。", "This medicine eliminates the pain.",
              ["remove / get rid of と近い意味", "受け身 be eliminated で「(試合で)敗退する」", "名詞は elimination(除去、敗退)"]),
             (285, "acknowledge", "〜を認める", "認める", "彼女は自分の間違いを認めた。", "She acknowledged her mistake.",
              ["admit と近い意味。acknowledge that ~ の形も", "名詞は acknowledgment(承認、感謝)", "本のあとがきの Acknowledgments は「謝辞」"]),
         ]),
    dict(intro="1語で意味が広がる単語をセットで✍️\n今日は「養う」「期限切れ」「登録」の3語です。", tags="#英検準1級 #英単語 #大人の勉強",
         items=[
             (286, "cultivate", "〜を耕す、(能力)を養う", "養う", "読書は想像力を養う。", "Reading cultivates the imagination.",
              ["土地を耕す → 能力・関係を育てる、と意味が広がります", "名詞は cultivation(耕作、育成)", "culture(文化)と同じ語源"]),
             (287, "overdue", "(支払い・返却の)期限が過ぎた", "期限が過ぎた", "その本は返却期限が過ぎている。", "The library book is overdue.",
              ["due(期限の)+ over(過ぎて)", "「とっくに〜されるべき」の意味もあります", "an overdue bill で「未払いの請求書」"]),
             (288, "enrollment", "登録、入学", "登録", "今年は入学者数が増えた。", "Enrollment increased this year.",
              ["動詞は enroll(登録する、入学する)", "enroll in A で「Aに入学する、Aに登録する」", "イギリスでは enrolment とつづります"]),
         ]),
    dict(intro="ニュースでよく見る準1級単語です📰\n今日は「入隊する」「無秩序」「気が進まない」の3語。", tags="#英検準1級 #時事英語 #瞬間英作文",
         items=[
             (289, "enlist", "(援助など)を得る、入隊する", "入隊する", "彼女は軍隊に入隊した。", "She enlisted in the army.",
              ["enlist in A で「Aに入隊する」", "enlist the help of A で「Aの協力を得る」", "en(中に)+ list(名簿):名簿に入れる"]),
             (290, "anarchy", "無政府状態、無秩序", "無秩序", "停電で町は大混乱になった。", "The blackout turned the city into anarchy.",
              ["アクセントは最初の a(アナーキー)", "an(ない)+ arch(支配者)", "形容詞は anarchic(無秩序な)"]),
             (291, "reluctant", "気乗りがしない、しぶしぶの", "気乗りがしない", "彼は謝りたがらなかった。", "He was reluctant to apologize.",
              ["be reluctant to do の形でよく出ます", "名詞は reluctance(気が進まないこと)", "副詞 reluctantly は「しぶしぶ」"]),
         ]),
    dict(intro="身の回りの物や人にも使える単語です🧳\n今日は「壊れやすい」「評価する」「疲れきった」の3語。", tags="#英検準1級 #英単語 #英語学習",
         items=[
             (292, "fragile", "壊れやすい、不安定な", "壊れやすい", "このグラスはとても壊れやすい。", "These glasses are very fragile.",
              ["荷物の「取扱注意」シールは FRAGILE", "反対は sturdy / tough(丈夫な)", "「(状態が)不安定な」の意味もあります"]),
             (293, "evaluate", "〜を評価する", "評価する", "先生は生徒の作文を評価した。", "The teacher evaluated the students' essays.",
              ["assess とほぼ同じ意味", "名詞は evaluation(評価)", "中に value(価値)が入っています"]),
             (294, "weary", "ひどく疲れた、飽き飽きして", "ひどく疲れた", "長い会議のあと、私たちは疲れきっていた。", "We were weary after the long meeting.",
              ["tired / exhausted と近い意味", "be weary of A で「Aに飽き飽きしている」", "発音は「ウィアリ」"]),
         ]),
    dict(intro="準1級の社会・政治の長文でよく出ます🏛️\n今日は「拘置」「連合」「穏やかな」の3語です。", tags="#英検準1級 #長文読解 #瞬間英作文",
         items=[
             (295, "custody", "保護、親権、拘置", "拘置", "容疑者は警察に拘束された。", "The suspect was taken into custody.",
              ["take A into custody で「Aを拘束する」", "離婚の話では「親権」の意味", "in custody で「拘留されて」"]),
             (296, "coalition", "(政党などの)連立、連合", "連合", "環境団体は川を守るために連合を作った。", "Environmental groups formed a coalition to protect the river.",
              ["coalition government で「連立政権」", "coali(合体する)+ tion", "政治・社会の長文に出やすい単語です"]),
             (297, "tranquil", "静かな、穏やかな", "穏やかな", "私たちは静かな村で休暇を過ごした。", "We spent our holiday in a tranquil village.",
              ["calm / peaceful / serene と近い意味", "名詞は tranquility(静けさ)", "tranquilizer は「精神安定剤」"]),
         ]),
    dict(intro="社会・政治の長文で差がつく準1級単語です🏛️\n今日は「取り締まる」「変装する」「黒字」の3語。", tags="#英検準1級 #英単語 #瞬間英作文",
         items=[
             (298, "enforce", "(法律などを)施行する、守らせる", "取り締まる", "警察は速度制限を厳しく取り締まっている。", "The police enforce the speed limit strictly.",
              ["名詞は enforcement(施行、取り締まり)", "law enforcement で「警察などの法執行機関」", "in(中に)+ force(力)で「力を持たせる」"]),
             (299, "disguise", "変装させる、隠す", "変装させる", "彼女はウェイターに変装した。", "She disguised herself as a waiter.",
              ["disguise oneself as A で「Aに変装する」", "名詞で「変装」:in disguise(変装して)", "a blessing in disguise は「災い転じて福となる」"]),
             (300, "surplus", "余り、黒字", "黒字", "その会社は今年、予算が黒字だった。", "The company had a budget surplus this year.",
              ["反対は deficit(赤字、不足)", "trade surplus で「貿易黒字」", "sur(上に)+ plus(より多く)"]),
         ]),
    dict(intro="長文で差がつく準1級単語です📖\n今日は「嘆願書」「習慣的な」「大胆な」の3語。", tags="#英検準1級 #英単語 #瞬間英作文",
         items=[
             (301, "petition", "嘆願書、請願", "嘆願書", "1,000人以上が嘆願書に署名した。", "Over 1,000 people signed the petition.",
              ["sign a petition で「嘆願書に署名する」", "動詞で「請願する」", "社会問題の長文によく出ます"]),
             (302, "habitual", "習慣的な、いつもの", "習慣的な", "彼はいつも朝寝坊だ。", "He is a habitual late riser.",
              ["名詞は habit(習慣)", "habitually で「習慣的に」", "a habitual smoker で「常習的な喫煙者」"]),
             (303, "daring", "大胆な、思い切った", "大胆な", "それは大胆な計画だった。", "It was a daring plan.",
              ["動詞の dare(思い切って〜する)から", "bold とほぼ同じ意味", "名詞で「大胆さ」の意味も"]),
         ]),
    dict(intro="ニュースでよく見る準1級単語です📰\n今日は「繁栄する」「収納場所」「加速する」の3語。", tags="#英検準1級 #時事英語 #英単語",
         items=[
             (304, "thrive", "繁栄する、元気に育つ", "繁栄する", "この植物は暖かい気候でよく育つ。", "These plants thrive in warm weather.",
              ["flourish・prosper と近い意味", "thrive on A で「Aを糧にして元気になる」", "ビジネスの記事では「(会社が)成長する」"]),
             (305, "compartment", "区画、仕切り", "区画", "かばんは頭上の収納棚に入れてください。", "Put your bag in the overhead compartment.",
              ["飛行機の overhead compartment(頭上の収納棚)でよく出ます", "電車の「車室」の意味も", "part(部分)が入っています"]),
             (306, "accelerate", "加速する、早める", "加速する", "新しいシステムで作業が速くなる。", "The new system will accelerate the process.",
              ["名詞は acceleration(加速)", "車のアクセルは accelerator", "反対は slow down / decelerate"]),
         ]),
    dict(intro="理系の長文にも出る準1級単語です🔬\n今日は「子孫」「腐る」「洗練する」の3語。", tags="#英検準1級 #長文読解 #瞬間英作文",
         items=[
             (307, "descendant", "子孫", "子孫", "彼はその有名な画家の子孫だ。", "He is a descendant of the famous painter.",
              ["反対は ancestor(祖先)", "動詞の descend(下る)から:代々下っていく人", "a descendant of A で「Aの子孫」"]),
             (308, "decay", "腐る、衰える", "腐る", "砂糖は虫歯の原因になる。", "Sugar can cause your teeth to decay.",
              ["tooth decay で「虫歯」", "rot とほぼ同じ意味", "建物や制度が「衰える」にも使えます"]),
             (309, "refine", "洗練する、改良する", "洗練する", "彼女はイベントの前にスピーチを磨いた。", "She refined her speech before the event.",
              ["形容詞 refined は「洗練された、精製された」", "refined sugar で「精製糖」", "名詞は refinement(改良、洗練)"]),
         ]),
    dict(intro="体や形の変化を表す準1級単語です🩹\n今日は「腫れる」「部分」「賄賂」の3語。", tags="#英検準1級 #英単語 #瞬間英作文",
         items=[
             (310, "swell", "ふくらむ、腫れる", "腫れる", "転んだあと足首が腫れた。", "My ankle swelled after the fall.",
              ["名詞は swelling(腫れ)", "過去分詞は swollen / swelled", "人数などが「増える」にも使えます"]),
             (311, "segment", "部分、区分", "部分", "若者は市場の大きな部分を占めている。", "Young people make up a large segment of the market.",
              ["market segment で「市場区分」", "動詞で「区分する」", "part・section と近い意味"]),
             (312, "bribe", "賄賂(を贈る)", "賄賂", "その役人は賄賂を受け取ったとして告発された。", "The official was accused of taking bribes.",
              ["take a bribe で「賄賂を受け取る」", "名詞は bribery(贈収賄)", "政治・事件の長文に出ます"]),
         ]),
    dict(intro="気持ちや社会を表す準1級単語です🏛️\n今日は「夢中な」「支持する」「打倒する」の3語。", tags="#英検準1級 #時事英語 #英単語",
         items=[
             (313, "obsessed", "取りつかれた、夢中な", "夢中な", "弟はゲームに夢中だ。", "My brother is obsessed with video games.",
              ["be obsessed with A で「Aに夢中だ」", "名詞は obsession(執着)", "良くも悪くも「頭から離れない」イメージ"]),
             (314, "uphold", "支持する、守る", "支持する", "裁判所はその判決を支持した。", "The court upheld the decision.",
              ["過去形は upheld", "uphold the law で「法を守る」", "support より固い言い方"]),
             (315, "overthrow", "打倒する、ひっくり返す", "打倒する", "国民は独裁者を打倒した。", "The people overthrew the dictator.",
              ["過去形は overthrew、過去分詞は overthrown", "over(上から)+ throw(投げる)", "歴史の長文によく出ます"]),
         ]),
    dict(intro="旅行やルールの話でも使える準1級単語です✈️\n今日は「旅程」「かすかな」「明確な」の3語。", tags="#英検準1級 #長文読解 #瞬間英作文",
         items=[
             (316, "itinerary", "旅程(表)", "旅程表", "旅行の旅程表をメールで送ります。", "I'll email you the itinerary for the trip.",
              ["発音は「アイティナラリ」", "TOEIC の出張の場面でもよく出ます", "schedule より「旅の計画」に限った言い方"]),
             (317, "faint", "かすかな、気を失う", "かすかな", "外でかすかな音が聞こえた。", "I heard a faint sound outside.",
              ["動詞で「気を失う」", "a faint hope で「かすかな望み」", "反対は clear・strong"]),
             (318, "explicit", "明確な、はっきりした", "明確な", "スマホの使用についてのルールは明確だ。", "The rules are explicit about phone use.",
              ["反対は implicit(暗黙の)", "副詞は explicitly(はっきりと)", "be explicit about A で「Aについて明確だ」"]),
         ]),
    # ---- 11/16〜(英検準1級 単熟語EX Unit 1〜2 から。例文はオリジナル)----
    dict(intro='ビジネスニュースで出る準1級単語💼\n今日は「倒産した」「評価する」「相殺する」の3語です。', tags='#英検準1級 #瞬間英作文 #英単語',
         items=[
             (319, 'bankrupt', '破産した、倒産した', '倒産した', 'その小さな書店は昨年倒産した。', 'The small bookstore went bankrupt last year.',
              ['go bankrupt で「倒産する」の形でよく出る', '名詞は bankruptcy(倒産)', 'bank(銀行)+ rupt(壊れた)が語源']),
             (320, 'assess', '〜を評価する、査定する', '評価する', '専門家が被害を評価した。', 'Experts assessed the damage.',
              ['名詞は assessment(評価)', 'evaluate とほぼ同じ意味', 'assess the situation で「状況を判断する」']),
             (321, 'offset', '〜を相殺する、埋め合わせる', '相殺する', '値上げで費用の増加を埋め合わせた。', 'The price increase offset the higher costs.',
              ['過去形・過去分詞も offset', '名詞は「埋め合わせ」', 'アクセントは動詞が後ろ、名詞が前']),
         ]),
    dict(intro='長文でよく出る準1級単語、言えるかな?🗣️\n今日は「豊富な」「満場一致で」「名誉ある」の3語。', tags='#英検準1級 #英単語 #英語学習',
         items=[
             (322, 'abundant', '豊富な、たくさんの', '豊富な', 'この地域は雨が豊富だ。', 'This area has abundant rainfall.',
              ['名詞は abundance(豊富さ)', '似た語は plentiful', '反対は scarce(乏しい)']),
             (323, 'unanimously', '満場一致で', '満場一致で', 'その案は満場一致で可決された。', 'The plan was approved unanimously.',
              ['形容詞は unanimous(満場一致の)', 'un(1つ)+ anim(心)が語源', 'a unanimous decision で「全会一致の決定」']),
             (324, 'prestigious', '名誉ある、名高い', '名誉ある', '彼女は名誉ある賞を受賞した。', 'She won a prestigious award.',
              ['名詞は prestige(名声)', 'a prestigious university で「名門大学」', 'famous より「格が高い」感じ']),
         ]),
    dict(intro='会話でも使える準1級単語です😊\n今日は「魅力的な」「回り道」「打ち込んでいる」の3語。', tags='#英検準1級 #瞬間英作文 #英会話',
         items=[
             (325, 'tempting', '魅力的な、心をそそる', '魅力的な', 'その申し出はとても魅力的だった。', 'The offer was very tempting.',
              ['動詞は tempt(誘惑する)', '名詞は temptation(誘惑)', '食べ物にもよく使う(tempting dessert)']),
             (326, 'detour', '回り道、迂回路', '回り道', '工事のため、回り道をしなければならなかった。', 'We had to take a detour because of the construction.',
              ['take a detour で「回り道をする」', 'de(離れて)+ tour(回る)', 'TOEIC の交通情報でも頻出']),
             (327, 'dedicated', '献身的な、打ち込んでいる', '打ち込んでいる', '彼は仕事に打ち込んでいる。', 'He is dedicated to his work.',
              ['be dedicated to A(名詞・動名詞)', '動詞は dedicate(ささげる)', '名詞は dedication(献身)']),
         ]),
    dict(intro='ニュースで出る準1級単語🗞️\n今日は「義務的な」「解放する」「危険な」の3語です。', tags='#英検準1級 #長文読解 #英単語',
         items=[
             (328, 'compulsory', '義務的な、必修の', '義務的な', 'この国では制服が義務になっている。', 'School uniforms are compulsory in this country.',
              ['似た語は mandatory', '反対は optional(任意の)', 'compulsory education で「義務教育」']),
             (329, 'liberate', '〜を解放する、自由にする', '解放する', 'その法律は多くの人々を解放した。', 'The law liberated many people.',
              ['名詞は liberation(解放)', 'liberal(自由な)、liberty(自由)も仲間', 'liberate A from B で「AをBから解放する」']),
             (330, 'perilous', '危険な', '危険な', '山を越える道は危険だった。', 'The road over the mountain was perilous.',
              ['似た語は dangerous', '名詞は peril(危険)', '文語的でかたい言い方']),
         ]),
    dict(intro='準1級の語彙問題で出る単語✍️\n今日は「従う」「あぜんとした」「無効の」の3語。', tags='#英検準1級 #瞬間英作文 #英単語',
         items=[
             (331, 'comply', '(規則などに)従う', '従う', 'すべての客はルールに従わなければならない。', 'All guests must comply with the rules.',
              ['comply with A の形で覚える', '名詞は compliance(順守)', '企業の「コンプライアンス」はこの名詞']),
             (332, 'stunned', 'あぜんとした、ぼうぜんとした', 'あぜんとした', 'その知らせに私たちはあぜんとした。', 'We were stunned by the news.',
              ['stunning は「見事な、驚くほど美しい」', 'be stunned to do でも使う', 'shocked より強い驚き']),
             (333, 'invalid', '無効の', '無効の', 'このクーポンは期限切れで無効だ。', 'This coupon is expired and invalid.',
              ['反対は valid(有効な)', 'in(否定)+ valid', '名詞の invalid(病人)は発音が違う']),
         ]),
    dict(intro='ITやビジネスでも使える準1級単語💡\n今日は「明らかにする」「称賛する」「しおれる」の3語です。', tags='#英検準1級 #英単語 #英語学習',
         items=[
             (334, 'clarify', '〜を明らかにする', '明らかにする', 'その点を明らかにしてもらえますか。', 'Could you clarify that point?',
              ['名詞は clarification(説明)、clarity(明快さ)', 'clear(はっきりした)が語源', '会議で聞き返すときに便利']),
             (335, 'commend', '〜を称賛する、表彰する', '称賛する', '市長はボランティアの努力を称賛した。', 'The mayor commended the volunteers for their efforts.',
              ['commend A for B で「BのことでAをほめる」', '似た語は praise', '形容詞は commendable(称賛に値する)']),
             (336, 'wither', 'しぼむ、枯れる', 'しおれる', '水がなくて花がしおれた。', 'The flowers withered without water.',
              ['似た語は wilt・fade', 'wither away で「衰える」', 'weather(天気)とつづりを区別']),
         ]),
    dict(intro='英作文でも使える準1級単語🗣️\n今日は「不足」「正確さ」「冷静な」の3語。', tags='#英検準1級 #英作文 #瞬間英作文',
         items=[
             (337, 'scarcity', '不足、欠乏', '不足', 'その町は水不足に苦しんでいる。', 'The town is suffering from a scarcity of water.',
              ['形容詞は scarce(乏しい)', '似た語は shortage', '経済の「希少性」もこの単語']),
             (338, 'precision', '正確さ、精度', '正確さ', 'この仕事には正確さが必要だ。', 'This job requires precision.',
              ['形容詞は precise(正確な)', 'with precision で「正確に」', '似た語は accuracy']),
             (339, 'composed', '落ち着いた、冷静な', '冷静な', '彼女は面接中ずっと冷静だった。', 'She stayed composed during the interview.',
              ['似た語は calm', 'remain composed で「冷静さを保つ」', 'compose は「構成する、作曲する」']),
         ]),
    dict(intro='ニュースでよく見る準1級単語📺\n今日は「時代遅れの」「懐疑的な」「有効期限が切れる」の3語です。', tags='#英検準1級 #長文読解 #英単語',
         items=[
             (340, 'obsolete', '時代遅れの、廃れた', '時代遅れの', 'その技術はすっかり時代遅れになった。', 'That technology has become obsolete.',
              ['似た語は outdated', 'become obsolete で「廃れる」', 'IT・製品の話でよく出る']),
             (341, 'skeptical', '懐疑的な', '懐疑的な', '多くの人がその主張に懐疑的だ。', 'Many people are skeptical about the claim.',
              ['be skeptical about / of A', '名詞は skepticism(懐疑)', 'イギリス英語では sceptical']),
             (342, 'expire', '有効期限が切れる', '期限が切れる', '私のパスポートは来月期限が切れる。', 'My passport expires next month.',
              ['名詞は expiration(満了)', 'expiration date で「有効期限」', 'ex(外に)+ pire(息をする)が語源']),
         ]),
    dict(intro='ビジネスで使える準1級単語💼\n今日は「従来の」「通知する」「仮定」の3語。', tags='#英検準1級 #ビジネス英語 #瞬間英作文',
         items=[
             (343, 'conventional', '従来の、型にはまった', '従来の', '従来の方法ではうまくいかなかった。', 'Conventional methods did not work.',
              ['似た語は traditional', '反対は unconventional(型破りな)', '名詞の convention は「慣習、大会」']),
             (344, 'notify', '〜に通知する、知らせる', '通知する', '結果はメールでお知らせします。', 'We will notify you of the results by email.',
              ['notify A of B で「AにBを知らせる」', '名詞は notification(通知)', 'スマホの「通知」もこの名詞']),
             (345, 'assumption', '仮定、思い込み', '仮定', 'それは間違った思い込みだ。', 'That is a wrong assumption.',
              ['動詞は assume(仮定する)', 'on the assumption that ~ で「〜と仮定して」', 'make an assumption で「推測する」']),
         ]),
    dict(intro='長文の頻出単語で締めくくり📚\n今日は「偏見」「つかむ」「衝動」の3語です。', tags='#英検準1級 #英単語 #長文読解',
         items=[
             (346, 'prejudice', '偏見、先入観', '偏見', '私たちは偏見と戦わなければならない。', 'We must fight against prejudice.',
              ['似た語は bias', 'pre(前に)+ judice(判断)', 'prejudice against A で「Aへの偏見」']),
             (347, 'seize', '〜をつかむ、捕らえる', 'つかむ', '彼はチャンスをつかんだ。', 'He seized the chance.',
              ['seize the opportunity でよく使う', '名詞は seizure(つかむこと、押収)', '発音は「シーズ」']),
             (348, 'impulse', '衝動', '衝動', '彼女は衝動的にその靴を買った。', 'She bought the shoes on impulse.',
              ['on impulse で「衝動的に」', '形容詞は impulsive(衝動的な)', 'impulse buying で「衝動買い」']),
         ]),
    {'intro': '仕事ぶりを表す準1級単語🧐\n今日は「几帳面な」「厳密な」「多才な」の3語です。', 'tags': '#英検準1級 #瞬間英作文 #英単語', 'items': [(349, 'meticulous', '几帳面な、細心の', '几帳面な', '彼女は仕事に几帳面だ。', 'She is meticulous about her work.', ['be meticulous about A の形でよく使う', 'careful より強い', '副詞は meticulously']), (350, 'rigorous', '厳密な、厳しい', '厳密な', 'その薬は厳密な検査を受けた。', 'The medicine went through rigorous testing.', ['rigorous training で「厳しい訓練」', 'strict とほぼ同じ', '副詞は rigorously']), (351, 'versatile', '多才な、用途の広い', '多才な', '彼は多才な俳優だ。', 'He is a versatile actor.', ['人にも物にも使える', 'a versatile tool で「万能な道具」', '名詞は versatility'])]},
    {'intro': '悪くなる・減るの3語📉\n今日は「悪化する」「減少する」「使い果たす」です。', 'tags': '#英検準1級 #英単語 #長文読解', 'items': [(352, 'deteriorate', '悪化する', '悪化する', '祖父の健康が悪化した。', "My grandfather's health deteriorated.", ['反対は improve', '名詞は deterioration', 'worsen とほぼ同じ']), (353, 'diminish', '減少する、〜を減らす', '減少する', '彼の人気は年々減っていった。', 'His popularity diminished year by year.', ['decrease よりかたい言い方', '自動詞・他動詞の両方', 'diminishing returns で「収穫逓減」']), (354, 'deplete', '〜を使い果たす、枯渇させる', '使い果たす', '私たちは水の蓄えを使い果たした。', 'We depleted our water supply.', ['受け身 be depleted もよく出る', '名詞は depletion', 'ozone depletion で「オゾン層の破壊」'])]},
    {'intro': '会議・ニュースで出る準1級単語🗞️\n今日は「承認する」「課す」「さし迫った」の3語です。', 'tags': '#英検準1級 #瞬間英作文 #ニュース英語', 'items': [(355, 'endorse', '〜を支持する、推薦する', '支持する', '多くの医師がその計画を支持した。', 'Many doctors endorsed the plan.', ['有名人が商品を宣伝するときにも使う', '名詞は endorsement', 'support よりかたい']), (356, 'impose', '〜を課す、押しつける', '課す', '政府は新しい税を課した。', 'The government imposed a new tax.', ['impose A on B で「BにAを課す」', 'imposing は「堂々とした」', '名詞は imposition']), (357, 'imminent', 'さし迫った', 'さし迫った', '嵐がさし迫っている。', 'A storm is imminent.', ['危険や悪いことによく使う', 'imminent danger で「差し迫った危険」', 'eminent(著名な)と区別'])]},
    {'intro': 'お金にまつわる準1級単語💰\n今日は「もうかる」「質素な」「停滞した」の3語です。', 'tags': '#英検準1級 #英単語 #経済英語', 'items': [(358, 'lucrative', 'もうかる', 'もうかる', '彼はもうかる仕事を見つけた。', 'He found a lucrative job.', ['profitable とほぼ同じ', 'a lucrative business でよく使う', 'ポジティブな意味で使う']), (359, 'frugal', '質素な、倹約的な', '質素な', '祖母はとても質素な生活を送っている。', 'My grandmother lives a very frugal life.', ['stingy(けちな)と違ってほめ言葉', '名詞は frugality', 'a frugal meal で「質素な食事」']), (360, 'stagnant', '停滞した、よどんだ', '停滞した', '経済は何年も停滞している。', 'The economy has been stagnant for years.', ['もとは「水がよどんだ」', '動詞は stagnate', '名詞は stagnation(不況、停滞)'])]},
    {'intro': '話し方・考え方を表す3語🗣️\n今日は「雄弁な」「筋の通った」「もっともらしい」です。', 'tags': '#英検準1級 #瞬間英作文 #英単語', 'items': [(361, 'eloquent', '雄弁な', '雄弁な', '彼女は雄弁なスピーチをした。', 'She gave an eloquent speech.', ['名詞は eloquence', 'an eloquent speaker でもよく使う', '表情などが「多くを物語る」の意味も']), (362, 'coherent', '筋の通った、首尾一貫した', '筋の通った', '彼の説明は筋が通っていた。', 'His explanation was coherent.', ['反対は incoherent', '名詞は coherence', '英作文の採点でも使われる語']), (363, 'plausible', 'もっともらしい、妥当な', 'もっともらしい', '彼女の話はもっともらしく聞こえた。', 'Her story sounded plausible.', ['反対は implausible', 'a plausible explanation でよく使う', '「信じられそう」というニュアンス'])]},
    {'intro': 'じゃまする・弱める・隠すの3語🚧', 'tags': '#英検準1級 #英単語 #長文読解', 'items': [(364, 'hinder', '〜を妨げる', '妨げる', '騒音が私の勉強を妨げた。', 'The noise hindered my studies.', ['hinder A from doing の形もある', '名詞は hindrance', 'prevent よりやや弱い']), (365, 'undermine', '〜をむしばむ、徐々に弱める', '弱める', 'うわさが彼の評判を弱めた。', 'Rumors undermined his reputation.', ['under(下)+ mine(掘る)が語源', '信頼・自信などによく使う', 'じわじわ弱めるイメージ']), (366, 'conceal', '〜を隠す', '隠す', '彼は本当の気持ちを隠した。', 'He concealed his true feelings.', ['hide よりかたい', '名詞は concealment', 'conceal A from B で「BにAを隠す」'])]},
    {'intro': 'ふだん使える準1級の形容詞☀️\n今日は「立ち直りが早い」「時々起こる」「自然発生的な」の3語です。', 'tags': '#英検準1級 #瞬間英作文 #英単語', 'items': [(367, 'resilient', '立ち直りが早い、回復力のある', '立ち直りが早い', '子どもは立ち直りが早い。', 'Children are resilient.', ['名詞 resilience は近年よく見る語', '物なら「弾力のある」', '困難から回復する力を表す']), (368, 'sporadic', '時々起こる、散発的な', '時々起こる', '今日は時々にわか雨が降るだろう。', 'There will be sporadic showers today.', ['天気予報の定番', '副詞は sporadically', 'occasional とほぼ同じ']), (369, 'spontaneous', '自然に起こる、その場の', 'その場の', '観客から自然に拍手が起こった。', 'There was spontaneous applause from the audience.', ['計画していない、というニュアンス', '副詞は spontaneously', '人なら「気さくで自由な」'])]},
    {'intro': '仮・初心・ふつうの3語🔰\n今日は「仮の」「初心者」「平凡な」です。', 'tags': '#英検準1級 #英単語 #英語学習', 'items': [(370, 'tentative', '仮の、暫定的な', '仮の', '会議の日程は仮のものだ。', 'The meeting date is tentative.', ['a tentative plan で「仮の計画」', '副詞 tentatively で「ためらいがちに」', '正式に決まる前に使う']), (371, 'novice', '初心者', '初心者', '私は料理の初心者だ。', "I'm a novice at cooking.", ['beginner とほぼ同じ', 'a novice at A / in A', '形容詞的に a novice driver']), (372, 'mediocre', '平凡な、二流の', '平凡な', 'その映画は平凡だった。', 'The movie was mediocre.', ['ほめ言葉ではない', '名詞は mediocrity', 'average より否定的'])]},
    {'intro': '和らげる・引き起こす・控えるの3語🌿\n今日は「和らげる」「引き起こす」「控える」です。', 'tags': '#英検準1級 #瞬間英作文 #英単語', 'items': [(373, 'alleviate', '〜を和らげる', '和らげる', 'この薬は痛みを和らげる。', 'This medicine alleviates pain.', ['relieve とほぼ同じ', 'alleviate poverty で「貧困を緩和する」', '名詞は alleviation']), (374, 'provoke', '〜を引き起こす、怒らせる', '引き起こす', '彼の発言は怒りを引き起こした。', 'His remark provoked anger.', ['形容詞 provocative は「挑発的な」', 'provoke A into doing の形もある', '名詞は provocation']), (375, 'refrain', '控える', '控える', '車内での通話はお控えください。', 'Please refrain from talking on the phone on the train.', ['refrain from doing の形で使う', 'アナウンスの定番', '名詞で「(歌の)くり返し」の意味も'])]},
    {'intro': '長文で差がつく準1級単語🏁\n今日は「避けられない」「実行可能な」「調べる」の3語です。', 'tags': '#英検準1級 #英単語 #長文読解', 'items': [(376, 'inevitable', '避けられない', '避けられない', '変化は避けられない。', 'Change is inevitable.', ['It is inevitable that 〜 の形も', '副詞は inevitably', 'unavoidable とほぼ同じ']), (377, 'feasible', '実行可能な', '実行可能な', 'その計画は実行可能だ。', 'The plan is feasible.', ['名詞は feasibility', 'a feasibility study で「実現可能性調査」', 'possible よりかたい']), (378, 'scrutinize', '〜を綿密に調べる', '綿密に調べる', '弁護士は契約書を綿密に調べた。', 'The lawyer scrutinized the contract.', ['名詞は scrutiny(精査)', 'under scrutiny で「厳しい目で見られて」', 'examine より細かく見る'])]},
]
ITEMS = [it for r in REELS for it in r["items"]]


def font(name, size, weight=None):
    f = ImageFont.truetype(str(FONTS / name), size)
    if weight:
        f.set_variation_by_axes(weight)
    return f


NUM = font("EBGaramond-Italic%5Bwght%5D.ttf", 60, [400])
TITLE = font("MPLUSRounded1c-Light.ttf", 47)
MEAN = font("MPLUSRounded1c-Light.ttf", 37)
JA = font("MPLUSRounded1c-Light.ttf", 31)
WORD = font("OpenSans%5Bwdth,wght%5D.ttf", 40, [700, 100])
EN = font("OpenSans%5Bwdth,wght%5D.ttf", 37, [700, 100])


# 音量(RMS)。元動画は日本語のほうが英語より 5dB ほど大きい
LEVEL = {EN_VOICE: 0.092, JA_VOICE: 0.163}


def tts(vid, text, speed):
    CACHE.mkdir(parents=True, exist_ok=True)
    mp3 = CACHE / f"{vid}_{hashlib.sha1(f'{text}|{speed}'.encode()).hexdigest()[:12]}.mp3"
    if not mp3.exists() and vid.startswith("ja-JP-"):
        subprocess.run([str(ROOT / ".venv-tts" / "bin" / "edge-tts"), "--voice", vid, f"--rate=+{round((speed - 1) * 100)}%",
                        "--text", text, "--write-media", str(mp3)], check=True, capture_output=True)
    if not mp3.exists():
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_128",
            data=json.dumps({"text": text, "model_id": "eleven_multilingual_v2",
                             "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "speed": speed}}).encode(),
            headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"})
        mp3.write_bytes(urllib.request.urlopen(req).read())
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp3), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32).copy()
    a = a * (LEVEL[vid] / (float(np.sqrt(np.mean(a ** 2))) or 1.0))
    a = np.tanh(a * 1.2) / 1.2  # 大きく入れても割れないように、山だけやわらかく抑える
    # 音量をそろえてから、前後の無音を切る(-45dB より小さいところ)
    # 測ったときと同じく 16kHz に直したもので調べる
    a16 = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                          "-ar", "16000", "-f", "f32le", "-"], input=a.tobytes(), capture_output=True, check=True).stdout
    a16 = np.frombuffer(a16, np.float32)
    db = 20 * np.log10(np.array([np.sqrt(np.mean(a16[i:i + 160] ** 2)) for i in range(0, len(a16) - 160, 160)]) + 1e-9)
    hop = int(SR * 0.01)
    # 元動画を測ったときと同じ決まりで、声の始まりと終わりを決める
    # (-45dB 以上を声とし、0.15秒未満のすき間はつなげ、0.05秒未満の小さな音は息として数えない)
    segs, start = [], None
    for i, loud in enumerate(db > -45):
        if loud and start is None:
            start = i
        if not loud and start is not None:
            segs.append([start, i])
            start = None
    if start is not None:
        segs.append([start, len(db)])
    merged = [segs[0]]
    for s0, s1 in segs[1:]:
        if s0 - merged[-1][1] < 15:
            merged[-1][1] = s1
        else:
            merged.append([s0, s1])
    merged = [m for m in merged if m[1] - m[0] >= 5]
    return a[merged[0][0] * hop:merged[-1][1] * hop]


def spaced(d, xy, text, f, fill, track):
    """字間をあけて書く(日本語)。"""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill, anchor="ls")
        x += d.textlength(ch, font=f) + track


def spaced_width(d, text, f, track):
    return sum(d.textlength(ch, font=f) + track for ch in text) - track


def ja_chunks(text):
    """日本語を文節のまとまりに分ける。漢字・カタカナのあとの助詞と「、」で区切り、「。」は前にくっつける。"""
    return [c for c in re.split(r"(?<=[一-龯ァ-ヶーA-Za-z0-9][はがをにでとものへな])(?![すしたあ関対つよ])|(?<=、)", text) if c]


def wrap_ja(d, text, f, width, track):
    """日本語は文節のまとまりで、行の長さがなるべくそろうように折り返す。"""
    from itertools import combinations
    chunks = ja_chunks(text)
    size = lambda t: spaced_width(d, t, f, track)
    for n in range(1, len(chunks) + 1):
        best = None
        for cut in combinations(range(1, len(chunks)), n - 1):
            idx = (0, *cut, len(chunks))
            lines = ["".join(chunks[a:b]) for a, b in zip(idx, idx[1:])]
            widest = max(size(l) for l in lines)
            if widest <= width and (best is None or widest < best[0]):
                best = (widest, lines)
        if best:
            return best[1]
    return chunks


def wrap(d, text, f, width, track=0, words=True):
    lines, cur = [], ""
    for tok in (text.split(" ") if words else ja_chunks(text)):
        nxt = (cur + " " + tok).strip() if words else cur + tok
        w = d.textlength(nxt, font=f) if words else spaced_width(d, nxt, f, track)
        if cur and w > width:
            lines.append(cur)
            cur = tok
        else:
            cur = nxt
    return lines + [cur]


def frame(item, stage):
    """stage: word / mean / ja / en"""
    no, word, mean, _, ja, en = item[:6]
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    spaced(d, (104, 451), "瞬間英作文クイズ", TITLE, MINT, 5)
    if stage in ("word", "mean"):
        d.text((101, 176), str(no), font=NUM, fill=MINT, anchor="ls")
        d.text((104, 620), word, font=WORD, fill=WHITE, anchor="ls")
        if stage == "mean":
            spaced(d, (104, 786), mean, MEAN, MINT, 3)
        return im
    for i, line in enumerate(wrap_ja(d, ja, JA, 430, 3)):
        spaced(d, (104, 777 + i * 58), line, JA, MINT, 3)
    if stage == "en":
        lines = wrap(d, en, EN, 440)
        top = 611 - (len(lines) - 1) * 31
        for i, line in enumerate(lines):
            d.text((103, top + i * 62), line, font=EN, fill=WHITE, anchor="ls")
    return im


def build(items, out):
    voice, cuts = [], []  # cuts: (秒, item, stage)
    t = LEAD
    voice.append(np.zeros(int(SR * LEAD), np.float32))
    for k, item in enumerate(items):
        _, word, _, said, ja, en = item[:6]
        parts = [(tts(EN_VOICE, word, EN_SPEED), WORD_MEAN, "word"),
                 (tts(JA_VOICE, said, JA_SPEED), MEAN_JA, "mean"),
                 (tts(JA_VOICE, ja, JA_SPEED), JA_EN, "ja"),
                 (tts(EN_VOICE, en, EN_SPEED), TAIL if k == len(items) - 1 else EN_NEXT, "en")]
        for clip, gap, stage in parts:
            early = {"word": 0, "mean": SHOW_EARLY, "ja": SHOW_EARLY, "en": EN_EARLY}[stage]
            if stage == "word":
                cuts.append((0.0 if k == 0 else cuts[-1][3] + NEXT_AFTER, item, stage, None))
            else:
                cuts.append((t - early, item, stage, None))
            voice += [clip, np.zeros(int(SR * gap), np.float32)]
            t += len(clip) / SR
            if stage == "en":
                cuts[-1] = cuts[-1][:3] + (t,)  # 英語の例文が終わった時刻
            t += gap
    audio = np.concatenate(voice)
    print(f"  peak {float(np.max(np.abs(audio))):.2f}")
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
            now = n / FPS
            cur = max((c for c in cuts if c[0] <= now), key=lambda c: c[0])
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
    """説明欄。最初の1〜2行(intro)で何が分かるかを見せ、単語ごとに 例文・訳・豆知識。空行には全角スペースを入れる。
    intro とハッシュタグは毎回書き下ろす(同じ文の使い回しはしない)。"""
    sp = "\u3000\u3000"
    out = [intro, sp, "--------------------------------------"]
    for no, word, mean, _, ja, en, tips in items:
        out += [f"【{no}】{word}:{mean}", en, ja, sp, "💡 豆知識", *[f"・{t}" for t in tips], "--------------------------------------"]
    return "\n".join(out + [sp, "保存して、あとで復習してね📌", sp, tags])


if __name__ == "__main__":
    import sys
    import quizify_words as qw
    want = {int(x) for x in sys.argv[1:]}
    reels = [r for r in REELS if not want or r["items"][0][0] in want]
    qw.guard("black", [(it[0], it[1]) for r in reels for it in r["items"]])  # 黒で使った単語とかぶっていたら止める
    mr.load_env()
    for r in reels:
        out = OUT / f"black_{r['items'][0][0]}.mp4"
        build(r["items"], out)
        out.with_suffix(".txt").write_text(caption_text(r["items"], r["intro"], r["tags"]) + "\n")
        for it in r["items"]:
            qw.add("black", it[1], no=it[0])
