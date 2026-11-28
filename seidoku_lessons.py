"""@seidoku.lab の台本の続き(No.4〜)。1週間ずつここに足す(seidoku_reel.py / seidoku_post.py は読まなくてよい)。
LESSONS の書き方は seidoku_reel.py の No.1 と同じ。TEXTS は投稿のキャプションとコメント(毎回書き下ろす)。
英文はオリジナル(本は構文パターンの参考だけ)。台本の英単語はカタカナで書き、DISP に表示用の英字を足す。
"""
DISP = {"ラーニング": "Learning", "キャン・プロテクト": "can protect", "ザ・タイム": "the time", "ユー・ニード": "you need", "ウィッチ・ランゲージ": "Which language", "マターズ": "matters", "マター": "matter", "ザン": "than", "ハウ・オフン": "how often", "イット": "It", "トゥー・リメンバー": "to remember", "リメンバー": "remember", "リメイン・アンクリア": "remain unclear", "リメインズ": "remains", "ルールズ": "rules", "イントロデュースト": "introduced",
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

LESSONS += [{'no': 7, 'theme': '動名詞の長いS+関係詞の省略', 'hook': ('文頭の -ing、', '訳せる?'), 'en': 'Learning to say no to small requests at work can protect the time you need for important tasks.', 'lines': [[('(Learning to say no', 'S')], [('to small requests at work)', 'S')], [('can protect', 'V'), (' the time', 'O')], [('[you need for important tasks].', 'R')]], 'labels': {'S': 'S(〜すること)', 'R': '関係詞の省略'}, 'steps': [('01', '-ing', '文頭の -ing は', '*〜すること*', {'S'}, 'いちばん最初のラーニング。文の頭のイング形は、*「すること」*。ここから、*長い主語*が始まります。'), ('02', '動詞', 'can protect が', '*文の動詞*', {'V', 'S', 'O'}, '動詞は、キャン・プロテクト。その手前までが*主語*。断れるようになることが、時間を守る、という文です。'), ('03', '省略', '名詞のすぐあとに SV', '*関係詞の省略*', {'V', 'S', 'R', 'O'}, 'ザ・タイムのすぐあとに、ユー・ニード。名詞のあとに主語と動詞が続くのは、*関係詞の省略*。大事な仕事に必要な時間、です。')], 'ja': ['職場の小さな頼みに', '*ノーと言えるようになること*は、', '大事な仕事に*必要な時間*を', '守ってくれる。'], 'ja_say': '職場の小さな頼みに、ノーと言えるようになることは、大事な仕事に必要な時間を、守ってくれる。', 'q': {'en': ['Writing down three good things', 'every night can change the way', 'you see your day.'], 'chs': [['毎晩、よかったことを3つ書くことで、', '1日の見え方が変わることがある'], ['毎晩3つの良いことを書いている人は、', '1日を見る方法を変えられる']], 'answer': 1}}, {'no': 8, 'theme': 'Which の長いS+matter(重要である)+how often', 'hook': ('文頭の Which、', '訳せる?'), 'en': 'Which language you learn first matters less than how often you actually use it.', 'lines': [[('(Which language you learn first)', 'S')], [('matters less', 'V')], [('than [how often you actually', 'M')], [('use it].', 'M')]], 'labels': {'S': 'S(どの〜を…か)', 'V': 'V(重要である)'}, 'steps': [('01', 'Which', '文頭の Which は', '*どの〜を…か*', {'S'}, 'いちばん最初のウィッチ・ランゲージ。*どの言語を、か*、というカタマリで、*長い主語*になります。'), ('02', 'matter', 'matter は動詞で', '*重要である*', {'V', 'S'}, '動詞は、マターズ。マターは、動詞だと*「重要である」*。どの言語を最初に学ぶかは、それほど重要ではない、となります。'), ('03', 'how often', 'than のあとは', '*どれくらい〜か*', {'M', 'V', 'S'}, 'ザンのあとの、ハウ・オフン。実際に*どれくらい使うか*、ほど重要ではない、という比べ方です。')], 'ja': ['*どの言語*を最初に学ぶかは、', '実際に*どれくらい使うか*ほど', '*重要ではない*。'], 'ja_say': 'どの言語を最初に学ぶかは、実際にどれくらい使うかほど、重要ではない。', 'q': {'en': ['Who you study with can matter', 'as much as what you study.'], 'chs': [['だれと勉強するかは、何を勉強するかと', '同じくらい大事なことがある'], ['一緒に勉強する人は、勉強する内容と', '同じくらい問題を起こす']], 'answer': 1}}, {'no': 9, 'theme': '形式主語の It+to 不定詞+that 節', 'hook': ('この It、', '何を指す?'), 'en': 'It is important to remember that small daily habits often matter more than long weekend study sessions.', 'lines': [[('It', 'I'), (' is important', 'V')], [('(to remember', 'S')], [('[that small daily habits often', 'O')], [('matter more than long', 'O')], [('weekend study sessions]', 'O'), (').', 'S')]], 'labels': {'I': '形式主語', 'S': '真主語(〜すること)', 'O': 'O(〜ということ)'}, 'steps': [('01', 'It', '文頭の It は', '*形式主語*', {'I'}, 'いちばん最初のイット。これは、*あとの内容を指す*イット、形式主語です。「それは」とは訳しません。'), ('02', 'to', '本当の主語は', '*to 以下*', {'I', 'V', 'S'}, '本当の主語は、*トゥー・リメンバー*以下。覚えておくことは、大切だ、となります。'), ('03', 'that', 'remember のあとの that は', '*〜ということ*', {'I', 'V', 'S', 'O'}, 'リメンバーのあとのザットは、*「ということ」*。毎日の小さな習慣は、週末の長い勉強より大事なことが多い、ということです。')], 'ja': ['*毎日の小さな習慣*は、', '週末の長い勉強より大事なことが多い', 'ということを、*覚えておくことが大切だ*。'], 'ja_say': '毎日の小さな習慣は、週末の長い勉強より、大事なことが多い。ということを、覚えておくことが、大切だ。', 'q': {'en': ['It is easy to forget that most', 'experts were once beginners too.'], 'chs': [['ほとんどの専門家も、かつては初心者だった', 'ということは、忘れやすい'], ['それは簡単だ。ほとんどの専門家が', '初心者だったことを忘れるのは']], 'answer': 1}}]

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
    7: {'caption': '文頭の Learning、「学んでいる」と訳してない?🤔\n文の頭の -ing は「〜すること」で長い主語に。名詞のすぐあとの SV(関係詞の省略)まで、英文解釈の基本を1文で。\n正しい訳は 1 か 2 か、コメントで👇\n\n#英文解釈 #動名詞 #大学受験 #英検準1級 #精読', 'comment': '✅ 正解は 1\nWriting down three good things every night can change the way you see your day.\n毎晩、よかったことを3つ書くことで、1日の見え方が変わることがある。\n\n━━ 詳しい解説 ━━\n① 文頭の Writing は動名詞「書くこと」。動詞 can change の手前までが長い S。\n\n② the way you see your day:名詞 the way のすぐあとに you see(SV)→ 関係詞の省略。「1日の見え方」。\n\n✗ 2 は Writing を「書いている人」と読んだワナ。文頭の -ing のあとに動詞が来たら、-ing のカタマリが主語。\n\n📝 動画の英文\nLearning to say no to small requests at work can protect the time you need for important tasks.\n職場の小さな頼みにノーと言えるようになることは、大事な仕事に必要な時間を守ってくれる。'},
    8: {'caption': '文頭の Which、「どれ?」と聞いてない?🤔\nWhich language you learn first(どの言語を最初に学ぶか)が主語。matter は動詞で「重要である」。長文で迷わない読み方を1文で。\n正しい訳は 1 か 2 か、コメントで👇\n\n#英文読解 #大学受験英語 #英語長文 #英検準1級 #英語の勉強', 'comment': '✅ 正解は 1\nWho you study with can matter as much as what you study.\nだれと勉強するかは、何を勉強するかと同じくらい大事なことがある。\n\n━━ 詳しい解説 ━━\n① 文頭の Who you study with =「だれと勉強するか」(疑問詞のカタマリ)が S。\n\n② matter は動詞で「重要である」。can matter as much as 〜 =「〜と同じくらい重要でありうる」。\n\n③ what you study =「何を勉強するか」。\n\n✗ 2 は matter を「問題」と読み、Who を「〜する人」と読んだワナ。\n\n📝 動画の英文\nWhich language you learn first matters less than how often you actually use it.\nどの言語を最初に学ぶかは、実際にどれくらい使うかほど重要ではない。'},
    9: {'caption': 'この It、「それは」と訳してない?🤔\n文頭の It が to 以下を指す「形式主語」。remember のあとの that 節まで、和訳問題で差がつく形を1文で。\n正しい訳は 1 か 2 か、コメントで👇\n\n#英文解釈 #形式主語 #大学受験 #英検2級 #和訳', 'comment': '✅ 正解は 1\nIt is easy to forget that most experts were once beginners too.\nほとんどの専門家も、かつては初心者だったということは、忘れやすい。\n\n━━ 詳しい解説 ━━\n① It is easy to 〜:It は to 以下を指す形式主語。「〜するのは簡単だ」。\n\n② forget のあとの that は「〜ということ」。to forget that 〜 =「〜ということを忘れる」。\n\n✗ 2 は It を「それは」と訳したワナ。It is 形容詞 to 〜 / that 〜 の形なら、It はあとの内容を指す。\n\n📝 動画の英文\nIt is important to remember that small daily habits often matter more than long weekend study sessions.\n毎日の小さな習慣は、週末の長い勉強より大事なことが多い、ということを覚えておくのが大切だ。'},
}
