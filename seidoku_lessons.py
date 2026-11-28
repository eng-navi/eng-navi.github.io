"""@seidoku.lab の台本の続き(No.4〜)。1週間ずつここに足す(seidoku_reel.py / seidoku_post.py は読まなくてよい)。
LESSONS の書き方は seidoku_reel.py の No.1 と同じ。TEXTS は投稿のキャプションとコメント(毎回書き下ろす)。
英文はオリジナル(本は構文パターンの参考だけ)。台本の英単語はカタカナで書き、DISP に表示用の英字を足す。
"""
DISP = {"リメイン・アンクリア": "remain unclear", "リメインズ": "remains", "ルールズ": "rules", "イントロデュースト": "introduced",
        "ジ・アビリティ": "the ability", "トゥー・ラーフ": "to laugh", "シームズ・トゥー・ビー": "seems to be", "トゥー": "to",
        "オルゾウ": "although", "ウィッチ・ミステイクス": "which mistakes", "ア・ウーマン": "a woman", "フーズ": "whose", "ハウ": "How"}

LESSONS = [
    dict(no=4, theme="How の長いS+過去分詞の修飾+remain C",
         hook=("文頭の How、", "訳せる?"),
         en="How the new rules introduced last spring will affect small shops remains unclear.",
         lines=[[("(How the new rules", "S")],
                [("introduced last spring", "P")],
                [("will affect small shops)", "S")],
                [("remains", "V"), (" unclear.", "C")]],
         labels={"S": "S(どのように〜か)", "P": "過去分詞(〜された)", "V": "V(〜のままだ)"},
         steps=[
             ("01", "How", "文頭の How は", "*どのように〜か*", {"S"},
              "いちばん最初のハウは、*「どのように、か」*。文の動詞はリメインズ。その手前までが、*長い主語*です。"),
             ("02", "過去分詞", "名詞のうしろの過去分詞", "*〜された*", {"S", "P"},
              "ルールズのうしろの、イントロデュースト。名詞のうしろの過去分詞は、*「された」*と前の名詞を説明します。去年の春に導入された、ルール。"),
             ("03", "remain", "remain C は", "*Cのままだ*", {"S", "P", "V", "C"},
              "リメイン・アンクリアは、*「はっきりしないままだ」*。"),
         ],
         ja=["去年の春に導入された新しいルールが、", "小さな店に*どのように影響するか*は、", "*まだはっきりしない*。"],
         ja_say="きょねんの春に導入された新しいルールが、小さな店に、どのように影響するかは、まだはっきりしない。",
         q=dict(en=["How the plan announced yesterday", "will change our commute", "remains unclear."],
                chs=[["昨日発表された計画が、通勤を", "どう変えるかは、まだはっきりしない"],
                     ["その計画が昨日、通勤をどう変えると", "発表したかは、不明のままだ"]],
                answer=1)),
    dict(no=5, theme="名詞+to不定詞+seem to be+although 中の疑問形容詞 which",
         hook=("この which、", "訳せる?"),
         en="The ability to laugh at small mistakes seems to be useful everywhere, although which mistakes people find funny depends on the culture.",
         lines=[[("The ability", "S"), (" (to laugh at", "T")],
                [("small mistakes)", "T"), (" seems to be", "V")],
                [("useful everywhere,", "C"), (" [although", "M")],
                [("which mistakes", "W"), (" people find funny", "M")],
                [("depends on the culture].", "M")]],
         labels={"T": "不定詞(〜する)", "V": "V(〜のようだ)", "W": "疑問形容詞(どの〜)"},
         steps=[
             ("01", "to", "名詞のうしろの to は", "*〜する* 能力", {"S", "T"},
              "ジ・アビリティのうしろの、トゥー・ラーフ。名詞のうしろのトゥーは、*「する」*と説明する形。小さな失敗を笑う、能力です。"),
             ("02", "seem", "seem to be C は", "*Cのようだ*", {"S", "T", "V", "C"},
              "シームズ・トゥー・ビーは、*「のようだ」*。どこでも役に立つように思える、となります。"),
             ("03", "which", "although の中の which は", "*どの〜か*", {"S", "T", "V", "C", "M", "W"},
              "オルゾウのうしろの、ウィッチ・ミステイクス。これは*「どの失敗を、か」*。どの失敗をおかしいと思うかは、*文化次第*です。"),
         ],
         ja=["小さな失敗を*笑う能力*は、", "どこでも役に立つ*ようだ*。", "もっとも、*どの失敗*を", "おかしいと思うかは、文化次第だ。"],
         ja_say="小さな失敗を笑う能力は、どこでも役に立つようだ。もっとも、どの失敗をおかしいと思うかは、文化しだいだ。",
         q=dict(en=["The chance to travel abroad", "seems exciting, although which", "country people choose depends", "on their budget."],
                chs=[["海外へ旅する機会はわくわくするものだ。", "もっとも、どの国を選ぶかは予算次第だ"],
                     ["海外へ旅する機会はわくわくするが、", "その国の人々は予算で選ばれる"]],
                answer=1)),
    dict(no=6, theme="That の長いS+whose の関係詞節",
         hook=("この長い主語、", "どこまで?"),
         en="That the town's first doctor was a woman whose letters were later turned into a popular novel is rarely mentioned in history books.",
         lines=[[("(That the town's first doctor", "S")],
                [("was a woman", "S"), (" [whose letters were later", "R")],
                [("turned into a popular novel]", "R"), (")", "S")],
                [("is rarely mentioned", "V"), (" in history books.", "X")]],
         labels={"S": "S(〜ということ)", "R": "whose(その〜が)", "V": "V(めったに〜されない)"},
         steps=[
             ("01", "That", "That のうしろに SV。", "*〜ということ* が S", {"S"},
              "ザットのうしろに、主語と動詞。*「ということ」*のザットで、長い主語のはじまりです。"),
             ("02", "whose", "名詞+whose は", "*その〜が*", {"S", "R"},
              "ア・ウーマンのうしろのフーズは、*「その女性の」*。その女性の手紙が、のちに人気の小説になった、と説明しています。"),
             ("03", "動詞", "2つ目の動詞", "*is の手前* までが S", {"S", "R", "V"},
              "ふたつめの動詞、イズの手前までが主語。歴史の本では*めったにふれられない*、という文です。"),
         ],
         ja=["町で最初の医者が、", "のちに手紙が*人気の小説になった*", "女性だったということは、", "歴史の本では*めったに触れられない*。"],
         ja_say="町で最初の医者が、のちに手紙が人気の小説になった女性だった、ということは、歴史の本では、めったにふれられない。",
         q=dict(en=["That the winner was a student", "whose paintings had never been", "shown is rarely reported."],
                chs=[["優勝者が、絵を一度も展示されたことの", "ない学生だったことは、ほぼ報じられない"],
                     ["あの優勝者は学生で、その絵は一度も", "展示されず、ほとんど報じられない"]],
                answer=1)),
]

TEXTS = {
    4: dict(
        caption="""文頭の How、「どうやって」で止まってない?🤔
How のカタマリが主語、名詞のうしろの過去分詞、remain C(Cのままだ)。長文で主語を見失わないための読み方を1文で。
正しい訳は 1 か 2 か、コメントで👇

#英文解釈 #英語長文 #大学受験 #英検準1級 #精読""",
        comment="""✅ 正解は 1
How the plan announced yesterday will change our commute remains unclear.
昨日発表された計画が通勤をどう変えるかは、まだはっきりしない。

━━ 詳しい解説 ━━
① 文頭の How のカタマリが S なら「どのように〜か」。文の動詞は remains、その手前までが S。

② the plan announced yesterday:名詞のうしろの過去分詞 → 「昨日発表された計画」。

③ remain unclear =「はっきりしないままだ」(remain C =「Cのままだ」)。

✗ 2 は announced を文の動詞(〜と発表した)と読んだワナ。will change があるので、announced は名詞を説明する過去分詞。

📝 動画の英文
How the new rules introduced last spring will affect small shops remains unclear.
去年の春に導入された新しいルールが、小さな店にどのように影響するかは、まだはっきりしない。"""),
    5: dict(
        caption="""この which、関係代名詞じゃないって気づける?🤔
名詞+to 不定詞、seem to be C、although の中の「どの〜か」の which。難関大の長文で差がつく1文です。
正しい訳は 1 か 2 か、コメントで👇

#英文読解 #不定詞 #大学受験英語 #英検準1級 #英語の勉強""",
        comment="""✅ 正解は 1
The chance to travel abroad seems exciting, although which country people choose depends on their budget.
海外へ旅する機会はわくわくするものだ。もっとも、どの国を選ぶかは予算次第だ。

━━ 詳しい解説 ━━
① The chance to travel abroad:名詞のうしろの to 不定詞 →「海外へ旅する機会」。

② seems exciting =「わくわくするようだ」(seem C)。

③ although のうしろの which country people choose が S、depends が V。
which country =「どの国を〜か」(疑問形容詞)。depend on =「〜次第だ」。
文の途中の although は「もっとも〜」と訳すと自然。

✗ 2 は which を関係代名詞と読み、country people を「その国の人々」とつなげたワナ。

📝 動画の英文
The ability to laugh at small mistakes seems to be useful everywhere, although which mistakes people find funny depends on the culture.
小さな失敗を笑う能力は、どこでも役に立つようだ。もっとも、どの失敗をおかしいと思うかは、文化次第だ。"""),
    6: dict(
        caption="""この長い主語、どこまでかわかる?🤔
That 節の主語の中に whose の関係詞節。2つ目の動詞 is を見つければ、長い主語の終わりが見える。英文解釈の練習に。
正しい訳は 1 か 2 か、コメントで👇

#英文解釈 #関係代名詞 #英語長文 #大学受験 #英検準1級""",
        comment="""✅ 正解は 1
That the winner was a student whose paintings had never been shown is rarely reported.
優勝者が、絵を一度も展示されたことのない学生だったことは、ほとんど報じられない。

━━ 詳しい解説 ━━
① That のうしろに the winner was(SV)→ 名詞節の that「〜ということ」。

② a student whose paintings 〜:whose =「その〜が」。「絵が一度も展示されたことのない学生」。

③ 2つ目の動詞 is の手前までが長い S。is rarely reported =「めったに報じられない」。

✗ 2 は That を「あの」と読んだワナ。That のうしろに SV が続いたら、名詞節の that。

📝 動画の英文
That the town's first doctor was a woman whose letters were later turned into a popular novel is rarely mentioned in history books.
町で最初の医者が、のちに手紙が人気の小説になった女性だったということは、歴史の本ではめったに触れられない。"""),
}
