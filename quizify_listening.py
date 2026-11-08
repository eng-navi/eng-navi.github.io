"""@quizify_english の青い「リスニング問題」リールを作る。1本に2問(短い1文=Part 2 風、会話・トーク=Part 3/4 風)。

1問ごとに カウントダウン(3・2・1)→ マイクの画面で英語を1回 → 日本語訳 A/B(片方はすり替えたひっかけ)。
答えは説明欄(キャプションの後半)に、元の投稿と同じ形で入れる(answer_text)。間と配置は 2024年の元動画(77・78 / 143・144)を 0.01 秒単位で測った値。

  .venv-tts/bin/python quizify_listening.py [番号...]   → out/quizify/listening_<最初の番号>.mp4 と .txt(説明欄の全文)

カウントダウンの音は元動画(本人のアカウント)から切り出したもの(assets/quizify/countdown.wav)。
"""
import math
import subprocess
import tempfile

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter

import manga_reel as mr
import quizify_black as qb

OUT, SR, W, H, FPS = qb.OUT, qb.SR, qb.W, qb.H, qb.FPS
COUNTDOWN = qb.ROOT / "assets" / "quizify" / "countdown.wav"

# 声(ElevenLabs の標準の声)。本番の TOEIC と同じく国も混ぜ、順番に回す(同じ声が続かないように)。
# 1本の中では男女を分け、1問目が男性の回と女性の回を交互にする。元動画は1問目男性・2問目女性
MALE = [("nPczCjzI2devNBz1zQrb", "Brian", "🇺🇸", "アメリカ英語"), ("JBFqnCBsd6RMkjVDRZzb", "George", "🇬🇧", "イギリス英語"),
        ("IKne3meq5aSn9XLyUdCD", "Charlie", "🇦🇺", "オーストラリア英語"), ("cjVigY5qzO86Huf0OWal", "Eric", "🇺🇸", "アメリカ英語"),
        ("onwK4e9ZLuTAKqWW03F9", "Daniel", "🇬🇧", "イギリス英語"), ("iP95p4xoKVk53GoZ742B", "Chris", "🇺🇸", "アメリカ英語")]
FEMALE = [("Xb7hH8MSUJpSbSDYk0k2", "Alice", "🇬🇧", "イギリス英語"), ("EXAVITQu4vr4xnSDxMaL", "Sarah", "🇺🇸", "アメリカ英語"),
          ("pFZP5JQG7iQjIQuC4Bku", "Lily", "🇬🇧", "イギリス英語"), ("XrExE9yKIg1WjnnlVkGX", "Matilda", "🇺🇸", "アメリカ英語"),
          ("hpp4J3VqNfWAUOO0d1Us", "Bella", "🇺🇸", "アメリカ英語")]
SPEED = 1.0
for v in MALE + FEMALE:
    qb.LEVEL[v[0]] = 0.2  # 元動画の声は -13dB 前後と大きめ


def voice_for(no, k):
    """番号と何問目か(0・1)から声を決める。2問で1本(145・146 のように奇数から始まる)なので、何本目か = (no - 1) // 2。"""
    reel = (no - 1) // 2
    male_first = reel % 2 == 0
    pool = MALE if (k == 0) == male_first else FEMALE
    return pool[reel % len(pool)]


# 間(秒)
CD = 2.50          # カウントダウン → マイクの画面
VOICE_IN = (0.25, 0.16)  # マイクの画面 → 声(1問目・2問目)
OPT_AFTER = 0.30   # 声の終わり → 訳の画面
Q2_AT = 8.90       # 2問目のカウントダウンが始まる時刻(元動画は 8.83・9.00)
OPT_FADE = 0.30    # 2問目の訳はふわっと出る
PER_CHAR = 0.077   # 最後の訳を見せる長さ(長いほうの訳の1文字あたり)。最短 4 秒

LEFT, RIGHT = (186, 238, 219), (146, 188, 247)  # 横のグラデーション(左ミント → 右水色)
INK = (33, 33, 33)
NUM = qb.font("EBGaramond-Italic%5Bwght%5D.ttf", 54, [500])
TITLE = qb.font("KiwiMaru-Medium.ttf", 75)
OPT = qb.font("KiwiMaru-Medium.ttf", 26)
FOOT = qb.font("KiwiMaru-Medium.ttf", 31)
DIGIT = qb.font("OpenSans%5Bwdth,wght%5D.ttf", 58, [600, 100])

# 1本ずつ:紹介文(毎回書き下ろし)、ハッシュタグ、2問(短い1文=Part 2 風、会話・トーク=Part 3/4 風)
# 問題:番号, 声(None なら順番に回す), 英文, 訳A, 訳B, 正解(A/B), 語句(説明欄に載せる「語句：意味」)
# 英文は TOEIC の問題集から場面・流れ・問われる語句だけを借りてオリジナルで書き、場面も変えている
REELS = [
    dict(intro="🎧 1回だけ聞いて、正しい訳を選べる?\n今日は「担当者を聞く質問」と「予定変更の電話」です。",
         tags="#TOEICリスニング #TOEIC600点 #英語耳",
         items=[
             (145, None, "Who's in charge of ordering office supplies?",
              "事務用品の注文を担当しているのは誰ですか。", "事務用品の配達を担当しているのは誰ですか。", "A",
              ["be in charge of A：Aを担当している", "order：注文する", "office supplies：事務用品"]),
             (146, None, "Hi, Tom. My train is delayed because of a signal problem, so I won't get to the office by ten. "
              "Could we push the client meeting back by an hour? If that doesn't work, please start without me.",
              "トム、事故で電車が止まっていて、9時までに会社に着けそうにないんだ。顧客との打ち合わせを1時間早めてもらえるかな？無理なら、中止にして。",
              "トム、信号トラブルで電車が遅れていて、10時までに会社に着けそうにないんだ。顧客との打ち合わせを1時間遅らせてもらえるかな？無理なら、僕抜きで始めて。",
              "B",
              ["delayed：遅れている", "signal problem：信号トラブル", "get to A：Aに着く", "push back：(予定を)遅らせる",
               "client：顧客", "work：うまくいく、都合がつく", "without A：Aなしで"]),
         ]),
    dict(intro="🎧 聞き取れたら上級者!\n今日は「承認されたか確認する質問」と「同僚へのお願い」です。",
         tags="#TOEIC #リスニング対策 #ビジネス英語",
         items=[
             (147, None, "Has the new marketing plan been approved yet?",
              "新しいマーケティング計画はもう提出されましたか。", "新しいマーケティング計画はもう承認されましたか。", "B",
              ["marketing plan：マーケティング計画", "approve：承認する", "yet：(疑問文で)もう"]),
             (148, None, "Hi, Ben. Could you check the sales report before I send it to the director? "
              "I think some numbers in the second table are wrong. Also, could you pick up the cake for tomorrow's welcome lunch?",
              "ベン、部長に送る前に売上報告書を確認してもらえる？2つ目の表の数字がいくつか間違っていると思うの。それと、明日の歓迎ランチのケーキを受け取ってきてもらえる？",
              "ベン、部長に送る前に売上報告書を書き直してもらえる？最初の表の数字がいくつか抜けていると思うの。それと、明日の歓迎ディナーのケーキを受け取ってきてもらえる？",
              "A",
              ["sales report：売上報告書", "director：部長、取締役", "table：表", "pick up：受け取る", "welcome lunch：歓迎ランチ"]),
         ]),
    dict(intro="🎧 1回で聞き取れるか、試してみよう。\n今日は「届くはずの物」と「ビルからのお知らせ」です。",
         tags="#TOEICリスニング #英語学習 #スキマ時間",
         items=[
             (149, None, "Weren't the new chairs supposed to arrive this morning?",
              "新しい椅子は今朝届く予定ではなかったのですか。", "新しい机は今朝届く予定ではなかったのですか。", "A",
              ["be supposed to do：…することになっている", "arrive：届く、到着する"]),
             (150, None, "Good morning. This is the building management office. The air conditioning on the third floor "
              "will be shut down for repairs from one to three this afternoon. During that time, the conference rooms on the fifth floor will be available.",
              "おはようございます。ビル管理事務所です。3階の照明は、点検のため今日の午後1時から3時まで止まります。その間は、5階の休憩室をお使いいただけます。",
              "おはようございます。ビル管理事務所です。3階のエアコンは、修理のため今日の午後1時から3時まで止まります。その間は、5階の会議室をお使いいただけます。",
              "B",
              ["building management office：ビル管理事務所", "air conditioning：エアコン", "shut down：止める、停止する",
               "repair：修理", "conference room：会議室", "available：利用できる"]),
         ]),
    dict(intro="🎧 似ている訳にだまされないで!\n今日は「忘れ物」と「売上についての会議」です。",
         tags="#TOEIC #英語リスニング #社会人の勉強",
         items=[
             (151, None, "I think I left my umbrella in the lobby.",
              "ロビーに傘を忘れてきたと思います。", "受付に傘を忘れてきたと思います。", "A",
              ["leave：置き忘れる(過去形は left)", "lobby：ロビー"]),
             (152, None, "Let's start with this year's sales. Sales of our shampoo have dropped by ten percent since spring. "
              "Customer surveys show that many people find the bottle hard to open. So we need a new design by the end of the month.",
              "まずは今年の売上から始めましょう。当社のシャンプーの売上は、春から10パーセント落ちています。顧客アンケートでは、ボトルが開けにくいという声が多いです。そこで、今月末までに新しいデザインが必要です。",
              "まずは今年の売上から始めましょう。当社のシャンプーの売上は、夏から20パーセント落ちています。顧客アンケートでは、ボトルが重いという声が多いです。そこで、来月末までに新しいデザインが必要です。",
              "A",
              ["sales：売上", "drop：落ちる、下がる", "survey：アンケート、調査", "find A hard to do：Aが…しにくいと感じる",
               "by the end of the month：月末までに"]),
         ]),
    dict(intro="🎧 When と Where、聞き分けられる?\n今日は「いつ届くか」と「歯医者からの電話」です。",
         tags="#TOEICリスニング #TOEIC対策 #英語耳",
         items=[
             (153, None, "When can you send me the final draft?",
              "最終稿をどこに送ればいいですか。", "最終稿をいつ送ってもらえますか。", "B",
              ["final draft：最終稿", "send A B：AにBを送る"]),
             (154, None, "Hello, this is Green Dental Clinic calling for Mr. Park. Dr. Wilson will be at a conference on Thursday, "
              "so we need to change your appointment. Could you come in on Friday at the same time instead?",
              "もしもし、グリーン歯科です。パーク様でしょうか。ウィルソン先生が木曜日に学会に出席するため、ご予約を変更させていただく必要があります。代わりに金曜日の同じ時間にお越しいただけますか？",
              "もしもし、グリーン歯科です。パーク様でしょうか。ウィルソン先生が木曜日に出張するため、ご予約を取り消させていただく必要があります。代わりに金曜日の午前中にお越しいただけますか？",
              "A",
              ["dental clinic：歯科医院", "conference：学会、会議", "appointment：予約", "come in：来院する、来る", "instead：代わりに"]),
         ]),
    dict(intro="🎧 選ぶ質問、聞き取れる?\n今日は「どちらの席がいいか」と「美術館の案内」です。",
         tags="#TOEIC #リスニング #旅行英語",
         items=[
             (155, None, "Would you prefer a window seat or an aisle seat?",
              "窓側の席と前方の席、どちらがよろしいですか。", "窓側の席と通路側の席、どちらがよろしいですか。", "B",
              ["prefer：…のほうを好む", "window seat：窓側の席", "aisle seat：通路側の席"]),
             (156, None, "Welcome to the City Art Museum. Our special exhibition of travel photography is on the third floor "
              "and runs until the end of this month. Please note that flash photography is not allowed in the gallery.",
              "市立美術館へようこそ。旅行写真の特別展は3階で、今月末まで開催しています。展示室内でのフラッシュ撮影は禁止されていますのでご注意ください。",
              "市立美術館へようこそ。旅行写真の特別展は2階で、来月末まで開催しています。展示室内での撮影はすべて禁止されていますのでご注意ください。",
              "A",
              ["special exhibition：特別展", "photography：写真(撮影)", "run：(展示などが)続く、開催される",
               "note that ~：…に注意する", "allow：許可する", "gallery：展示室"]),
         ]),
    dict(intro="🎧 始まる?終わる?ちゃんと聞き取れるかな。\n今日は「研修の時間」と「送別のあいさつ」です。",
         tags="#TOEICリスニング #ビジネス英語 #英語学習",
         items=[
             (157, None, "Isn't the training session supposed to end at four?",
              "研修は4時に始まる予定ではなかったのですか。", "研修は4時に終わる予定ではなかったのですか。", "B",
              ["training session：研修", "be supposed to do：…することになっている"]),
             (158, None, "Before we close the meeting, I'd like to thank Emma Hill, who will move to our Singapore office next month. "
              "Over the past six years, she has trained more than fifty new employees. Please join us for her farewell party on Friday evening.",
              "会議を終える前に、来月シンガポール支社へ異動するエマ・ヒルさんにお礼を言いたいと思います。この6年間で、彼女は50人以上の新入社員を指導してくれました。金曜日の夜の送別会にぜひご参加ください。",
              "会議を終える前に、来月シドニー支社へ異動するエマ・ヒルさんにお礼を言いたいと思います。この5年間で、彼女は15人以上の新入社員を採用してくれました。金曜日の昼の送別会にぜひご参加ください。",
              "A",
              ["move to A：Aへ移る、異動する", "over the past ~ years：この…年間で", "train：指導する、研修する",
               "employee：社員", "farewell party：送別会"]),
         ]),
    dict(intro="🎧 open と closed、聞き間違えないで!\n今日は「新しいお店」と「ラジオの交通情報」です。",
         tags="#TOEIC #英語リスニング #スキマ時間",
         items=[
             (159, None, "I heard the new café on the first floor is open.",
              "1階の新しいカフェが開店したそうですね。", "1階の新しいカフェが閉店したそうですね。", "A",
              ["I heard ~：…だと聞いた", "first floor：1階", "open：営業している"]),
             (160, None, "Good evening. This is the traffic update from City Radio. Because of strong winds, the Blue Line "
              "between Central Station and the airport has been suspended. Service is expected to resume early tomorrow morning.",
              "こんばんは。シティ・ラジオの交通情報です。大雨のため、中央駅と空港の間のブルーラインは運転を見合わせています。運転再開は明日の昼の見込みです。",
              "こんばんは。シティ・ラジオの交通情報です。強風のため、中央駅と空港の間のブルーラインは運転を見合わせています。運転再開は明日の早朝の見込みです。",
              "B",
              ["traffic update：交通情報", "strong wind：強風", "suspend：一時停止する、見合わせる", "service：運行",
               "be expected to do：…する見込みである", "resume：再開する"]),
         ]),
    dict(intro="🎧 1回だけ聞いて、正しい訳を選べる?\n今日は「場所をたずねる質問」と「会議室の予約」です。", tags="#TOEICリスニング #TOEIC対策 #英語耳",
         items=[
             (161, None, "Where should I put these boxes?",
              "この箱はどこに置けばいいですか。", "この箱はいつ運べばいいですか。", "A",
              ["put：置く", "box：箱"]),
             (162, None, "Hi, this is Lisa from the sales team. I'd like to book the large conference room for Thursday afternoon. "
              "We're expecting about twenty visitors from a client company. Could you also set up a projector for us?",
              "営業チームのリサです。木曜日の午後に大会議室を予約したいのですが。取引先から20人ほど来客があります。プロジェクターの準備もお願いできますか。",
              "営業チームのリサです。金曜日の午前に小会議室を予約したいのですが。取引先から10人ほど来客があります。マイクの準備もお願いできますか。",
              "A",
              ["book：予約する", "conference room：会議室", "expect：(来客などを)見込む", "client：取引先、顧客", "set up：準備する、設置する", "projector：プロジェクター"]),
         ]),
    dict(intro="🎧 聞き取れたら上級者!\n今日は「提案への返事」と「店内アナウンス」です。", tags="#TOEIC #リスニング対策 #スキマ時間",
         items=[
             (163, None, "Why don't we take a short break?",
              "少し休憩しませんか。", "少し早く帰りませんか。", "A",
              ["Why don't we ~?：〜しませんか", "take a break：休憩する"]),
             (164, None, "Attention, shoppers. Our store will close in thirty minutes. Please bring your items to the registers on the first floor. "
              "Also, all winter coats are twenty percent off until the end of the day.",
              "お客様にお知らせします。当店はあと1時間で閉店いたします。商品は2階のレジへお持ちください。また、冬物の靴は本日に限り半額です。",
              "お客様にお知らせします。当店はあと30分で閉店いたします。商品は1階のレジへお持ちください。また、冬物のコートは本日中20パーセント引きです。",
              "B",
              ["Attention, shoppers.：お客様にお知らせします", "close：閉店する", "register：レジ", "item：商品", "~ percent off：〜パーセント引き"]),
         ]),
    dict(intro="🎧 似ている訳にだまされないで!\n今日は「誰の担当か」と「工場見学の案内」です。", tags="#TOEICリスニング #ビジネス英語 #英語学習",
         items=[
             (165, None, "Who's going to lead the training session?",
              "研修を担当するのは誰ですか。", "研修に参加するのは誰ですか。", "A",
              ["lead：(会などを)担当する、進める", "training session：研修"]),
             (166, None, "Welcome to our factory tour. Today, you'll see how we make our chocolate, from the beans to the final package. "
              "For safety reasons, please wear the hair nets we handed out and don't touch any of the machines.",
              "工場見学へようこそ。今日は、豆から最後の包装まで、チョコレートの作り方をご覧いただきます。安全のため、お配りした帽子をかぶり、機械には触れないでください。",
              "工場見学へようこそ。今日は、豆から最後の包装まで、チョコレートの作り方をご覧いただきます。安全のため、お配りしたヘアネットをつけ、機械には一切触れないでください。",
              "B",
              ["factory tour：工場見学", "package：包装", "for safety reasons：安全のため", "hair net：ヘアネット", "hand out：配る", "machine：機械"]),
         ]),
]


def background():
    x = np.linspace(0, 1, W)[None, :, None]
    row = np.array(LEFT)[None, None, :] * (1 - x) + np.array(RIGHT)[None, None, :] * x
    return Image.fromarray(np.repeat(row, H, axis=0).astype(np.uint8))


BG = background()
NO_BREAK_START = "、。?!)」ーぁぃぅぇぉっゃゅょァィゥェォッャュョ"


def wrap_chars(d, text, f, width, track):
    """1文字ずつ詰めて折り返す(元動画と同じ)。句読点や小さい字は行頭に来ないようにする。"""
    lines, cur = [], ""
    for ch in text:
        if cur and qb.spaced_width(d, cur + ch, f, track) > width and ch not in NO_BREAK_START:
            lines.append(cur)
            cur = ""
        cur += ch
    return lines + [cur] if cur else lines


def bold(d, xy, text, f, track):
    """字間をあけて、少し太く(1px ずらして重ねる)書く。"""
    for dx in (0, 0.7):
        qb.spaced(d, (xy[0] + dx, xy[1]), text, f, INK, track)


def mic(d, cx, cy):
    w = (255, 255, 255)
    d.ellipse([cx - 131, cy - 131, cx + 131, cy + 131], outline=w, width=7)
    d.rounded_rectangle([cx - 28, cy - 84, cx + 28, cy + 22], radius=28, outline=w, width=8)
    d.line([(cx - 28, cy - 22), (cx + 28, cy - 22)], fill=w, width=7)
    d.arc([cx - 58, cy - 44, cx + 58, cy + 56], 0, 180, fill=w, width=8)
    d.line([(cx, cy + 56), (cx, cy + 84)], fill=w, width=8)
    d.line([(cx - 38, cy + 86), (cx + 38, cy + 86)], fill=w, width=8)


def countdown(img, t):
    """白い円盤に 3・2・1。まわりの細い輪が回る。下に影。"""
    cx, cy = 190, 971
    n = 3 if t < 0.5 else 2 if t < 1.5 else 1
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse([cx - 52, cy - 46, cx + 52, cy + 58], fill=(20, 40, 50, 190))
    img.paste(shadow.filter(ImageFilter.GaussianBlur(5)), (0, 0), shadow.filter(ImageFilter.GaussianBlur(5)))
    d = ImageDraw.Draw(img)
    d.ellipse([cx - 50, cy - 50, cx + 50, cy + 50], fill=(246, 246, 246))
    d.arc([cx - 50, cy - 50, cx + 50, cy + 50], 15, 165, fill=(120, 130, 135), width=5)
    a = (t * 360) % 360
    d.arc([cx - 70, cy - 70, cx + 70, cy + 70], a, a + 300, fill=(255, 255, 255), width=3)
    d.text((cx, cy + 2), str(n), font=DIGIT, fill=INK, anchor="mm")


def frame(item, stage, t=0.0, fade=1.0):
    no, _, _, opt_a, opt_b = item[:5]
    img = BG.copy()
    d = ImageDraw.Draw(img)
    d.text((110, 176), str(no), font=NUM, fill=INK, anchor="ls")
    for dx in (0, 1):  # 元動画の文字は少し太いので、1px ずらして重ねる
        d.text((86 + dx, 450), "リスニング問題", font=TITLE, fill=INK, anchor="ls")
    foot_y = 988
    if stage == "count":
        countdown(img, t)
        return img
    if stage == "mic":
        mic(d, 360, 711)
    else:
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        a_lines = wrap_chars(ld, f"A) {opt_a}", OPT, 540, 2.5)
        b_lines = wrap_chars(ld, f"B) {opt_b}", OPT, 540, 2.5)
        y = 591 if len(a_lines) == 1 else 568
        for line in a_lines:
            bold(ld, (104, y), line, OPT, 2.5)
            y += 37.5
        y += 128 - 37.5 + 24
        for line in b_lines:
            bold(ld, (104, y), line, OPT, 2.5)
            y += 37.5
        foot_y = max(988, int(y - 37.5 + 131 + 33))
        if fade < 1:
            layer.putalpha(layer.getchannel("A").point(lambda v: int(v * fade)))
        img.paste(layer, (0, 0), layer)
    bold(d, (104, foot_y), "→ 答えは【説明・コメント欄】", FOOT, 5.0)
    return img


def build(items, out):
    cd, _ = sf.read(COUNTDOWN, dtype="float32")
    if cd.ndim > 1:
        cd = cd.mean(axis=1)
    scenes, track = [], np.zeros(int(SR * 60), np.float32)

    def put(a, t):
        i = int(t * SR)
        track[i:i + len(a)] += a[:len(track) - i]

    t = 0.0
    for k, item in enumerate(items):
        vid = item[1] or voice_for(item[0], k)[0]
        voice = qb.tts(vid, item[2], SPEED)
        if k == 1:
            t = max(t, Q2_AT)
        put(cd, t)
        scenes.append((t, item, "count"))
        t += CD
        scenes.append((t, item, "mic"))
        t += VOICE_IN[k]
        put(voice, t)
        t += len(voice) / SR + OPT_AFTER
        scenes.append((t, item, "opt" if k == 0 else "opt_fade"))
        if k == 0:
            t += 2.9  # 2問目まで最低これだけ見せる
    end = scenes[-1][0] + max(4.0, PER_CHAR * max(len(items[-1][3]), len(items[-1][4])))
    track = track[:int(end * SR)]
    with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
        sf.write(wav.name, track, SR)
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-i", wav.name, "-map", "0:v", "-map", "1:a", "-t", f"{end:.2f}", "-c:v", "libx264",
                              "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)],
                             stdin=subprocess.PIPE)
        still = {}
        for i in range(int(round(end * FPS))):
            now = i / FPS
            start, item, stage = [s for s in scenes if s[0] <= now + 1e-6][-1]
            if stage == "count":
                img = frame(item, "count", now - start)
            elif stage == "opt_fade" and now - start < OPT_FADE:
                img = frame(item, "opt", fade=(now - start) / OPT_FADE)
            else:
                key = (item[0], stage)
                if key not in still:
                    still[key] = frame(item, "opt" if stage.startswith("opt") else stage)
                img = still[key]
            p.stdin.write(img.tobytes())
        p.stdin.close()
        p.wait()
    print(f"✓ {out}({end:.2f}秒)")
    for start, item, stage in scenes:
        print(f"  {start:6.2f}  {item[0]} {stage}")


def accent_line(items):
    """説明欄の前半に添える「今回の音声」。"""
    return "🔊 今回の音声:" + " / ".join(f"{no} {voice_for(no, k)[2]} {voice_for(no, k)[3]}" if not item[1] else str(no)
                                      for k, item in enumerate(items) for no in [item[0]])


def answer_text(items):
    """説明欄(キャプション)の後半に入れる答え。元の投稿と同じ形。空行には全角スペースを入れる(Instagram が空行を詰めるため)。"""
    sp = "\u3000\u3000"
    out = [sp, "--------------------------------------"]
    for no, _, en, a, b, ans, words in items:
        out += [f"【{no}】", en, a if ans == "A" else b, sp, *words, sp, f" {sp}", f"{ans}が正解。",
                "--------------------------------------"]
    return "\n".join(out)


def caption(reel):
    """説明欄の全文:紹介文 → 今回の音声 → ハッシュタグ → 答え(元の投稿と同じ形)。"""
    return "\n".join([reel["intro"], accent_line(reel["items"]), "\u3000\u3000", reel["tags"], answer_text(reel["items"])])


if __name__ == "__main__":
    import sys
    mr.load_env()
    want = {int(a) for a in sys.argv[1:]}
    for reel in REELS:
        items = reel["items"]
        if want and items[0][0] not in want:
            continue
        out = OUT / f"listening_{items[0][0]}.mp4"
        build(items, out)
        out.with_suffix(".txt").write_text(caption(reel) + "\n")
