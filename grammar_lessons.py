"""やさしい英文法(@uk_easy_grammar)のレッスン。例文はすべてオリジナル。
書き方:'|' で改行、*語* が蛍光ペン。kana は日本語ナレーションでの読み(英単語はカタカナ)。
ナレーションの読みは yomi_check.py で必ず確認する。
"""

LESSONS = [
    dict(no=1, title="命令文のあとの and / or、意味わかる?",
         hook="Leave now, *and* you'll catch|the bus.",
         a=dict(key="and", kana="アンド", wrong="そして", right="そうすれば",
                say="実は、命令文のあとだと「そうすれば」なんです。", sub="命令文のあとの and は\n「そうすれば」",
                en="Leave now, *and* you'll catch|the bus.", ja="今出なさい、*そうすれば*間に合うよ", ja_say="今出なさい、そうすれば間に合うよ。"),
         b=dict(key="or", kana="オア", wrong="または", right="さもないと",
                ask="じゃあ、オアのほうは、どうでしょう?", ask_sub="じゃあ or は?",
                say="命令文のあとのオアは、「さもないと」という意味です。", sub="命令文のあとの or は\n「さもないと」",
                en="Leave now, *or* you'll miss|the bus.", ja="*さもないと*、乗り遅れるよ", ja_say="さもないと、乗り遅れるよ。"),
         q=dict(en="Be quiet, (    ) the|baby will wake up.", choices="1  and      2  or", ja="静かにして、さもないと赤ちゃんが起きる",
                say="問題です。1のアンドか、2のオアか。答えは、コメントで教えてね。", answer=2, word="or"),
         point="命令文のあとの and は「そうすれば」、or は「さもないと」。",
         detail="""■ 命令文 + and …「〜しなさい、そうすれば…」
Leave now, and you'll catch the bus.
(今出なさい、そうすればバスに間に合うよ)

■ 命令文 + or …「〜しなさい、さもないと…」
Leave now, or you'll miss the bus.
(今出なさい、さもないとバスに乗り遅れるよ)

■ 見分けるコツ
後ろが「いいこと」なら and、「困ること」なら or。
問題文は「赤ちゃんが起きる=困ること」なので or。

■ もう2つ例文
Study a little every day, and you'll get better.
(毎日少しずつ勉強すれば、上達するよ)
Take an umbrella, or you'll get wet.
(傘を持っていきなさい、さもないと濡れるよ)

■ 書きかえ
Leave now, and you'll catch the bus.
= If you leave now, you'll catch the bus."""),

    dict(no=2, title="I'm boring. って言ってない?",
         hook="I'm *boring*.", hook_say="この英語、どういう意味だと思いますか?", hook_sub="この英語、\nどういう意味?",
         a=dict(key="boring", kana="ボーリング", wrong="退屈している", right="つまらない",
                ask="ボーリングは「退屈している」?", ask_sub="boring は「退屈している」…?",
                say="実は、ボーリングは「人を退屈させる、つまらない」という意味です。", sub="boring は\n「つまらない」",
                en="The movie was *boring*.", ja="その映画は*つまらなかった*", ja_say="その映画はつまらなかった。"),
         b=dict(key="bored", kana="ボアード", wrong=None, right="退屈している",
                ask="じゃあ、「退屈している」と言いたいときは?", ask_sub="「退屈している」は?",
                say="ボアードを使います。「自分が退屈している」という意味です。", sub="「退屈している」は\nbored",
                en="I'm *bored*. Let's go out.", ja="*退屈だなあ*。出かけようよ", ja_say="退屈だなあ。出かけようよ。"),
         q=dict(en="This game is so (    ).", choices="1  boring      2  bored", ja="このゲーム、すごくつまらない",
                say="問題です。1のボーリングか、2のボアードか。答えは、コメントで教えてね。", answer=1, word="boring"),
         point="boring は「(人を)退屈させる=つまらない」、bored は「(自分が)退屈している」。",
         detail="""■ -ing と -ed のちがい
boring …(物・人が)つまらない、退屈させる
bored …(自分が)退屈している

I'm boring. だと「わたしはつまらない人間です」という意味に。
退屈しているときは I'm bored. と言います。

■ 同じ仲間
interesting(おもしろい)/ interested(興味がある)
exciting(わくわくさせる)/ excited(わくわくしている)
tiring(疲れさせる)/ tired(疲れている)

■ もう2つ例文
The class was interesting.(その授業はおもしろかった)
I'm interested in art.(わたしは美術に興味がある)

■ 覚え方
-ing は「まわりに与える気持ち」、-ed は「自分が受ける気持ち」。"""),

    dict(no=3, title="few と a few、まったく逆の意味?",
         hook="I have *few* friends|here.",
         a=dict(key="few", kana="few", wrong="少しいる", right="ほとんどいない", ask="few は「少しいる」?",
                say="実は、a のつかない few は「ほとんどない」なんです。", sub="a のない few は\n「ほとんどない」",
                en="I have *few* friends|here.", ja="ここには友だちが*ほとんどいない*", ja_say="ここには、ともだちがほとんどいない。"),
         b=dict(key="a few", kana="a few", wrong=None, right="少しある",
                ask="じゃあ、a few だと、どうでしょう?", ask_sub="じゃあ a few は?",
                say="a few なら「少しある」。ポジティブな意味になります。", sub="a few は\n「少しある」",
                en="I have *a few* friends|here.", ja="ここには友だちが*少しいる*", ja_say="ここには、ともだちが少しいる。"),
         q=dict(en="There are (    ) eggs left.|Let's make an omelet!", choices="1  few      2  a few", ja="卵が少し残ってる、オムレツを作ろう",
                say="問題です。1の few か、2の a few か。答えは、コメントで教えてね。", answer=2, word="a few"),
         point="few は「ほとんどない」(否定的)、a few は「少しある」(肯定的)。",
         detail="""■ few と a few
few …ほとんどない(ない方に注目)
a few …少しある(ある方に注目)

問題文は「オムレツを作ろう!」と前向きなので a few。

■ 数えられないものには little / a little
I have little time.(時間がほとんどない)
I have a little time.(時間が少しある)

■ もう2つ例文
Few people came to the party.(パーティーにはほとんど人が来なかった)
I need a few minutes.(数分ください)

■ 覚え方
a がつくと「ちょっとある」と、気持ちが明るくなる。"""),

    dict(no=4, title="He play tennis. どこが間違い?",
         hook="He *play* tennis|every Sunday.", hook_say="この英語、どこが変でしょう?", hook_sub="この英語、\nどこが変?",
         a=dict(key="He play", kana="プレイ", wrong="play", right="plays",
                ask="主語がヒーのとき、プレイのままでいいでしょうか?", ask_sub="主語が he のとき、play のまま…?",
                say="ヒー、シー、イットのときは、動詞にエスをつけて、プレイズにします。", sub="he / she / it のときは\n動詞に s",
                en="He *plays* tennis|every Sunday.", ja="彼は毎週日曜に*テニスをする*", ja_say="彼は毎週日曜にテニスをする。"),
         b=dict(key="doesn't", kana="ダズント", wrong="doesn't plays", right="doesn't play",
                ask="じゃあ、否定の文はどうでしょう?", ask_sub="じゃあ、否定の文は?",
                say="ダズントのあとは、エスをつけません。ダズントがエスを引き受けるイメージです。", sub="doesn't のあとは\ns をつけない",
                en="He *doesn't play* golf.", ja="彼はゴルフを*しない*", ja_say="彼はゴルフをしない。"),
         q=dict(en="My sister (    ) coffee.", choices="1  doesn't drink   2  doesn't drinks", ja="姉はコーヒーを飲まない",
                say="問題です。1ばんと2ばん、正しいのはどっち?答えは、コメントで教えてね。", answer=1, word="doesn't drink"),
         point="主語が he / she / it(3人称・単数)で現在のときは動詞に s。doesn't のあとは s なしの原形。",
         detail="""■ 三単現の s
主語が「わたし・あなた以外の1人(1つ)」で、今のことを言うとき、動詞に s をつけます。
He plays tennis.(彼はテニスをする)
My mother works in a bank.(母は銀行で働いている)

■ 否定・疑問は does に s がうつる
He doesn't play golf.(彼はゴルフをしない)
Does he play golf?(彼はゴルフをする?)
→ does / doesn't のあとは、s のつかない形(原形)。

■ s のつけ方
watch → watches / study → studies / have → has

■ よくある間違い
× He don't like fish. → ○ He doesn't like fish."""),

    dict(no=5, title="「Me too.」が使えないとき",
         hook="A: I don't like natto.|B: *Me too.*", hook_say="この返事、実はちょっと変なんです。わかりますか?", hook_sub="この返事、\nちょっと変?",
         a=dict(key="Me too", kana="ミートゥー", wrong="いつでも使える", right="肯定文への返事",
                ask="ミートゥーは、いつでも使えるでしょうか?", ask_sub="Me too. はいつでも使える…?",
                say="実は、ミートゥーは、すきです、のような、ふつうの文に返すときに使います。", sub="Me too. は\n肯定文への返事",
                en="A: I like sushi.|B: *Me too.*", ja="お寿司が好き。― *わたしも*", ja_say="おすしが好き。わたしも。"),
         b=dict(key="Me neither", kana="ミー・ナイザー", wrong=None, right="わたしも〜ない",
                ask="じゃあ、「わたしも好きじゃない」は?", ask_sub="「わたしも〜ない」は?",
                say="Me neither を使います。否定の文に返すときの「わたしも」です。", sub="否定文への返事は\nMe neither.",
                en="A: I don't like natto.|B: *Me neither.*", ja="納豆が苦手。― *わたしも*", ja_say="なっとうがにがて。わたしも。"),
         q=dict(en="A: I can't swim.|B: Me (    ).", choices="1  too      2  neither", ja="泳げないんだ ― わたしも",
                say="問題です。1ばんの too か、2ばんの neither か。答えは、コメントで教えてね。", answer=2, word="neither"),
         point="肯定文には Me too.、否定文(don't / can't など)には Me neither.",
         detail="""■ Me too. と Me neither.
I like cats. ― Me too.(わたしも好き)
I don't like cats. ― Me neither.(わたしも好きじゃない)

■ neither の読み方
イギリス英語では「ナイザー」、アメリカ英語では「ニーザー」と読まれることが多いです。どちらも正解。

■ もう少していねいに
I do too. / I don't either.
I can't either.(わたしもできない)

■ もう2つ例文
A: I'm hungry. ― B: Me too.
A: I've never been to Paris. ― B: Me neither."""),

    dict(no=6, title="many と much、どう使い分ける?",
         hook="How *much* apples|do you need?", hook_say="この英語、どこが変でしょう?", hook_sub="この英語、\nどこが変?",
         a=dict(key="many", kana="メニー", wrong="どちらでもOK", right="数えられる → many",
                ask="メニーとマッチ、どちらも「たくさん」。どちらでもいいでしょうか?", ask_sub="many と much、どちらでもOK…?",
                say="リンゴのように数えられるものには、メニーを使います。", sub="数えられるものには\nmany",
                en="How *many* apples|do you need?", ja="リンゴは*いくつ*必要?", ja_say="リンゴはいくつ必要?"),
         b=dict(key="much", kana="マッチ", wrong=None, right="数えられない → much",
                ask="じゃあ、マッチはいつ使うのでしょう?", ask_sub="じゃあ much は?",
                say="みずや、おかねのように、かぞえられないものには、マッチです。", sub="数えられないものには\nmuch",
                en="How *much* water|do you drink?", ja="水を*どのくらい*飲む?", ja_say="みずを、どのくらい飲む?"),
         q=dict(en="I don't have (    ) time.", choices="1  many      2  much", ja="あまり時間がない",
                say="問題です。1のメニーか、2のマッチか。答えは、コメントで教えてね。", answer=2, word="much"),
         point="数えられる名詞(apples)には many、数えられない名詞(water / time / money)には much。",
         detail="""■ many と much
many + 数えられる名詞(複数形)…many books / many people
much + 数えられない名詞 …much water / much money / much time

■ 数えられない名詞の例
water, milk, money, time, information, advice, homework

■ How many / How much
How many books do you have?(本を何冊持っている?)
How much is this?(これはいくら?)

■ ふつうの文では a lot of が自然
I have a lot of friends.(友だちがたくさんいる)
much は否定文・疑問文でよく使います。"""),

    dict(no=7, title="Can I と Can you、意味がまったく違う",
         hook="*Can I* open|the window?",
         a=dict(key="Can I", kana="キャンアイ", wrong="わたしはできる?", right="〜してもいい?",
                ask="キャンアイは「わたしはできますか?」…?", ask_sub="Can I は「わたしはできる?」…?",
                say="実は、キャンアイは「〜してもいいですか」と、許可をもらう言い方です。", sub="Can I 〜? は\n「〜してもいい?」",
                en="*Can I* open|the window?", ja="窓を*開けてもいい?*", ja_say="まどを、あけてもいい?"),
         b=dict(key="Can you", kana="キャンユー", wrong=None, right="〜してくれる?",
                ask="じゃあ、キャンユーは?", ask_sub="じゃあ Can you は?",
                say="キャンユーは「〜してくれる?」と、相手にお願いする言い方です。", sub="Can you 〜? は\n「〜してくれる?」",
                en="*Can you* open|the window?", ja="窓を*開けてくれる?*", ja_say="まどを、あけてくれる?"),
         q=dict(en="(    ) help me|with this box?", choices="1  Can I      2  Can you", ja="この箱、手伝ってくれる?",
                say="問題です。1のキャンアイか、2のキャンユーか。答えは、コメントで教えてね。", answer=2, word="Can you"),
         point="Can I 〜? は「〜してもいい?」(許可)、Can you 〜? は「〜してくれる?」(お願い)。",
         detail="""■ Can I 〜? =「(わたしが)〜してもいい?」
Can I sit here?(ここに座ってもいい?)
Can I use your pen?(ペンを借りてもいい?)

■ Can you 〜? =「(あなたが)〜してくれる?」
Can you help me?(手伝ってくれる?)
Can you say that again?(もう一度言ってくれる?)

■ もっとていねいに
Could you 〜?(〜していただけますか)
May I 〜?(〜してもよろしいですか)

■ 答え方
Sure. / Of course.(いいよ)
Sorry, I can't.(ごめん、できない)"""),

    dict(no=8, title="go to home は間違い?",
         hook="I go *to home*|at six.", hook_say="この英語、どこが変でしょう?", hook_sub="この英語、\nどこが変?",
         a=dict(key="home", kana="ホーム", wrong="go to home", right="go home",
                ask="ホームの前に、トゥーは必要でしょうか?", ask_sub="home の前に to はいる…?",
                say="ホームには「いえへ」という意味が入っているので、トゥーはいりません。", sub="go home\n(to はいらない)",
                en="I go *home*|at six.", ja="わたしは6時に*家に帰る*", ja_say="わたしは6時に家に帰る。"),
         b=dict(key="here", kana="ヒア", wrong="come to here", right="come here",
                ask="ヒアとゼアも、おなじなかまです。", ask_sub="here と there も同じ仲間",
                say="カム・ヒア、ゴー・ゼア。どちらも、トゥーをつけません。", sub="come here / go there\n(to はいらない)",
                en="*Come here*,|please.", ja="*こっちに来て*", ja_say="こっちに来て。"),
         q=dict(en="Let's go (    )|together.", choices="1  home      2  to home", ja="一緒に家に帰ろう",
                say="問題です。1ばんと2ばん、正しいのはどっち?答えは、コメントで教えてね。", answer=1, word="home"),
         point="home / here / there は「〜へ」の意味をふくむので、前に to をつけない。",
         detail="""■ to がいらない語
home(家へ)、here(ここへ)、there(そこへ)、abroad(海外へ)、downtown(街の中心へ)

go home(家に帰る)
come here(ここに来る)
go there(そこに行く)
go abroad(海外に行く)

■ 「家で」のときは at home
I stayed at home yesterday.(昨日は家にいた)

■ 場所の名前には to
go to school / go to the station / go to Tokyo

■ よくある間違い
× I arrived to home. → ○ I arrived home."""),

    dict(no=9, title="a hour? an hour?",
         hook="I waited *a hour*.", hook_say="この英語、どこが変でしょう?", hook_sub="この英語、\nどこが変?",
         a=dict(key="an", kana="アン", wrong="a hour", right="an hour",
                ask="アワーの前は、アでいいでしょうか?", ask_sub="hour の前は a でいい…?",
                say="アワーは、エイチを読まずに、ぼいんの音で始まるので、アンをつけます。", sub="母音の音で始まる語には\nan",
                en="I waited *an hour*.", ja="*1時間*待った", ja_say="1時間待った。"),
         b=dict(key="a", kana="ア", wrong="an uniform", right="a uniform",
                ask="じゃあ、ユニフォームはどうでしょう?", ask_sub="じゃあ uniform は?",
                say="ユニフォームは、ユーという音で始まるので、アです。つづりではなく、音で決まります。", sub="つづりではなく\n音で決まる",
                en="I wear *a uniform*|at work.", ja="仕事では*制服*を着る", ja_say="仕事では、せいふくを着る。"),
         q=dict(en="She is (    ) honest|person.", choices="1  a      2  an", ja="彼女は正直な人だ",
                say="問題です。1ばんと2ばん、正しいのはどっち?答えは、コメントで教えてね。", answer=2, word="an"),
         point="a / an は、つづりではなく「最初の音」で決まる。母音の音なら an。",
         detail="""■ a と an
最初の音が母音(ア・イ・ウ・エ・オに近い音)なら an
an apple / an egg / an hour / an honest person

■ つづりは母音でも、音が「ユ」なら a
a uniform / a university / a useful book

■ h を読まない語は an
hour(アワー)、honest(オネスト)

■ 問題の答え
honest は h を読まずに「オ」の音で始まるので an。
She is an honest person.(彼女は正直な人だ)"""),
    dict(no=10, title="I'm agree. は間違い?",
         hook="*I'm agree* with you.", hook_say="この英語、どこが変でしょう?", hook_sub="この英語、\nどこが変?",
         a=dict(key="agree", kana="アグリー", wrong="I'm agree", right="I agree",
                ask="アグリーの前に、アムは必要でしょうか?", ask_sub="agree の前に am はいる…?",
                say="アグリーは「さんせいする」という動詞なので、アムはいりません。", sub="agree は動詞\n→ am はいらない",
                en="*I agree* with you.", ja="*あなたに賛成です*", ja_say="あなたに、さんせいです。"),
         b=dict(key="sure", kana="シュア", wrong="I sure", right="I'm sure",
                ask="じゃあ、シュアはどうでしょう?", ask_sub="じゃあ sure は?",
                say="シュアは「たしかな」という形容詞なので、アムが必要です。", sub="sure は形容詞\n→ am が必要",
                en="*I'm sure* he'll come.", ja="*きっと*彼は来るよ", ja_say="きっと、彼は来るよ。"),
         q=dict(en="I (    ) with your idea.", choices="1  agree      2  am agree", ja="あなたの考えに賛成です",
                say="問題です。1ばんと2ばん、正しいのはどっち?答えは、コメントで教えてね。", answer=1, word="agree"),
         point="agree は動詞なので be 動詞はいらない。sure・happy などの形容詞には be 動詞が必要。",
         detail="""■ 動詞には be 動詞をつけない
I agree.(賛成です)
I like it.(それが好き)
× I'm agree. / × I'm like it.

■ 形容詞には be 動詞が必要
I'm sure.(たしかです)
I'm happy.(うれしい)
× I sure. / × I happy.

■ agree の使い方
agree with 人(人に賛成する)
I agree with you.
agree to 提案(提案に同意する)
They agreed to the plan.

■ 反対は disagree
I disagree.(反対です)"""),

    dict(no=11, title="I very like it. は言えない?",
         hook="I *very like* this song.", hook_say="この英語、どこが変でしょう?", hook_sub="この英語、\nどこが変?",
         a=dict(key="very", kana="ベリー", wrong="I very like it", right="I like it very much",
                ask="ベリーは、ライクの前に、おけるでしょうか?", ask_sub="very は like の前に置ける…?",
                say="ベリーは動詞の前には置けません。文の最後に、ベリー・マッチをつけます。", sub="very は動詞の前に\n置けない",
                en="I like this song|*very much*.", ja="この曲が*とても*好き", ja_say="この曲が、とても好き。"),
         b=dict(key="really", kana="リアリー", wrong=None, right="動詞の前に置ける",
                ask="じゃあ、リアリーならどうでしょう?", ask_sub="じゃあ really なら?",
                say="リアリーは、動詞の前に置けます。会話ではこちらがよく使われます。", sub="really は\n動詞の前に置ける",
                en="I *really like*|this song.", ja="この曲、*ほんとうに*好き", ja_say="この曲、ほんとうに好き。"),
         q=dict(en="I (    ) love|this movie.", choices="1  very      2  really", ja="この映画、ほんとうに大好き",
                say="問題です。1のベリーか、2のリアリーか。答えは、コメントで教えてね。", answer=2, word="really"),
         point="very は動詞の前に置けない(× I very like)。really なら動詞の前に置ける。",
         detail="""■ very の位置
very は形容詞・副詞を強める語。
very big / very fast(とても大きい/とても速い)
動詞を強めるときは very much を文の最後に。
I like it very much.

■ really は動詞の前にOK
I really like it.(ほんとうに好き)
I really want to go.(ほんとうに行きたい)

■ よくある間違い
× I very want it. → ○ I really want it.

■ ほかにも
so much / a lot も使えます。
I like it a lot.(すごく好き)"""),

    dict(no=12, title="on Sunday と in April、なぜ違う?",
         hook="See you *in Sunday*.", hook_say="この英語、どこが変でしょう?", hook_sub="この英語、\nどこが変?",
         a=dict(key="on", kana="オン", wrong="in Sunday", right="on Sunday",
                ask="サンデーの前は、インでいいでしょうか?", ask_sub="Sunday の前は in でいい…?",
                say="ようびや、ひづけには、オンをつかいます。", sub="曜日・日付には\non",
                en="See you *on Sunday*.", ja="*日曜日に*会おうね", ja_say="にちようびに、あおうね。"),
         b=dict(key="in", kana="イン", wrong="on April", right="in April",
                ask="じゃあ、エイプリル、4月はどうでしょう?", ask_sub="じゃあ April(4月)は?",
                say="月や、としのように、ながい期間には、インをつかいます。", sub="月・年には\nin",
                en="School starts *in April*.", ja="学校は*4月に*始まる", ja_say="学校は、しがつに始まる。"),
         q=dict(en="My birthday is (    ) May.", choices="1  on      2  in", ja="わたしの誕生日は5月",
                say="問題です。1のオンか、2のインか。答えは、コメントで教えてね。", answer=2, word="in"),
         point="曜日・日付には on、月・年・季節には in、時刻には at。",
         detail="""■ 時を表す at / on / in
at …時刻(点) at 7:00 / at noon
on …曜日・日付 on Sunday / on May 5
in …月・年・季節(長い期間) in April / in 2026 / in summer

■ イメージ
at(点)→ on(1日)→ in(長い期間)と、だんだん広くなる。

■ 特定の日の朝は on
in the morning(朝に)
on Sunday morning(日曜の朝に)

■ next / last / every の前には何もつけない
× on next Sunday → ○ next Sunday"""),

    dict(no=13, title="I have 20 years old. は間違い?",
         hook="I *have* 20 years old.", hook_say="この英語、どこが変でしょう?", hook_sub="この英語、\nどこが変?",
         a=dict(key="am", kana="アム", wrong="I have 20", right="I'm 20 years old",
                ask="ねんれいを言うとき、ハブでいいでしょうか?", ask_sub="年齢を言うとき、have でいい…?",
                say="ねんれいは、ビー動詞でいいます。アイム・トゥエンティです。", sub="年齢は be 動詞で",
                en="*I'm* 20 years old.", ja="わたしは*20さい*です", ja_say="わたしは、にじゅっさいです。"),
         b=dict(key="have", kana="ハブ", wrong="I'm a cold", right="I have a cold",
                ask="じゃあ、かぜをひいているときは?", ask_sub="じゃあ「かぜをひいている」は?",
                say="かぜや熱は、ハブを使います。アイ・ハブ・ア・コールドです。", sub="かぜ・熱は have",
                en="I *have* a cold.", ja="かぜを*ひいている*", ja_say="かぜを、ひいている。"),
         q=dict(en="My father (    )|45 years old.", choices="1  is      2  has", ja="父は45さいです",
                say="問題です。1のイズか、2のハズか。答えは、コメントで教えてね。", answer=1, word="is"),
         point="年齢は be 動詞(I'm 20.)、かぜ・熱・頭痛は have(I have a cold.)。",
         detail="""■ 年齢は be 動詞
I'm 20 (years old).(20歳です)
How old are you?(何歳?)
× I have 20 years old.

■ 体の具合は have
I have a cold.(かぜをひいている)
I have a fever.(熱がある)
I have a headache.(頭が痛い)

■ be 動詞で言う体の具合
I'm sick.(具合が悪い)
I'm tired.(疲れている)

■ 年齢の「歳」は years old
「20歳の学生」は a 20-year-old student(year に s がつかない)"""),

    dict(no=14, title="play と do、スポーツでの使い分け",
         hook="I *play* judo.", hook_say="この英語、どこが変でしょう?", hook_sub="この英語、\nどこが変?",
         a=dict(key="play", kana="プレイ", wrong="どのスポーツも", right="ボールを使う競技",
                ask="スポーツは、どれでもプレイでいいでしょうか?", ask_sub="スポーツは全部 play でいい…?",
                say="プレイは、テニスやサッカーのように、ボールをつかうスポーツに使います。", sub="play は\nボールを使う競技",
                en="I *play* soccer|on weekends.", ja="週末に*サッカーをする*", ja_say="週末に、サッカーをする。"),
         b=dict(key="do", kana="ドゥー", wrong="play judo", right="do judo",
                ask="じゃあ、じゅうどうはどうでしょう?", ask_sub="じゃあ柔道は?",
                say="じゅうどうや、ヨガのように、ボールを使わないものには、ドゥーを使います。", sub="do は\nボールを使わない運動",
                en="I *do* judo|after school.", ja="放課後に*柔道をする*", ja_say="ほうかごに、じゅうどうをする。"),
         q=dict(en="My sister (    ) yoga|every morning.", choices="1  plays      2  does", ja="姉は毎朝ヨガをする",
                say="問題です。1のプレイズか、2のダズか。答えは、コメントで教えてね。", answer=2, word="does"),
         point="ボールを使う競技は play、武道やヨガなどは do、スキーなどは go 〜ing。",
         detail="""■ play …ボールを使う競技
play tennis / play soccer / play baseball

■ do …ボールを使わない運動・武道
do judo / do karate / do yoga / do exercise

■ go 〜ing …移動する運動
go skiing / go swimming / go running

■ 楽器は play the 〜
play the piano / play the guitar

■ 問題の答え
主語が My sister なので does(do に s がつく形)。
My sister does yoga every morning."""),

    dict(no=15, title="「間違える」は make? do?",
         hook="I *did* a mistake.", hook_say="この英語、どこが変でしょう?", hook_sub="この英語、\nどこが変?",
         a=dict(key="make", kana="メイク", wrong="do a mistake", right="make a mistake",
                ask="ミステイク、間違いには、ドゥーでいいでしょうか?", ask_sub="mistake には do でいい…?",
                say="ミステイクには、メイクを使います。メイク・ア・ミステイクで「間違える」です。", sub="make a mistake\n(間違える)",
                en="I *made* a mistake.", ja="*間違えちゃった*", ja_say="まちがえちゃった。"),
         b=dict(key="do", kana="ドゥー", wrong="make my homework", right="do my homework",
                ask="じゃあ、しゅくだいはどうでしょう?", ask_sub="じゃあ宿題(homework)は?",
                say="しゅくだいには、do をつかいます。do my homework です。", sub="do my homework\n(宿題をする)",
                en="I *do* my homework|after dinner.", ja="夕食のあとに*宿題をする*", ja_say="ゆうしょくのあとに、しゅくだいをする。"),
         q=dict(en="Don't worry. Everyone|(    ) mistakes.", choices="1  makes      2  does", ja="大丈夫、だれでも間違えるよ",
                say="問題です。1のメイクスか、2のダズか。答えは、コメントで教えてね。", answer=1, word="makes"),
         point="mistake・friends・a plan は make、homework・the dishes・my best は do。",
         detail="""■ make …何かを作り出す
make a mistake(間違える)
make friends(友だちを作る)
make a plan(計画を立てる)
make a decision(決める)

■ do …作業・仕事をする
do my homework(宿題をする)
do the dishes(皿洗いをする)
do my best(ベストを尽くす)
do the shopping(買い物をする)

■ 覚え方
新しく「生み出す」なら make、決まった作業を「こなす」なら do。

■ 問題の答え
Everyone は1人あつかいなので makes。"""),

    dict(no=16, title="listen と hear、どう違う?",
         hook="I like *listening music*.", hook_say="この英語、どこが変でしょう?", hook_sub="この英語、\nどこが変?",
         a=dict(key="listen to", kana="リッスン", wrong="listen music", right="listen to music",
                ask="リッスンのあとに、すぐミュージックでいいでしょうか?", ask_sub="listen のすぐあとに music…?",
                say="リッスンのあとには、トゥーがひつようです。リッスン・トゥー・ミュージックです。", sub="listen to 〜\n(to が必要)",
                en="I like *listening to*|music.", ja="音楽を*聞く*のが好き", ja_say="おんがくを、きくのが好き。"),
         b=dict(key="hear", kana="ヒア", wrong=None, right="自然に聞こえる",
                ask="じゃあ、ヒアとのちがいは?", ask_sub="じゃあ hear とのちがいは?",
                say="リッスンは、自分から聞くこと。ヒアは、自然に聞こえることです。", sub="listen は自分から\nhear は自然に聞こえる",
                en="Sorry, I can't *hear*|you.", ja="ごめん、*聞こえない*", ja_say="ごめん、きこえない。"),
         q=dict(en="I like (    ) to the radio|in the car.", choices="1  listening      2  hearing", ja="車でラジオを聞くのが好き",
                say="問題です。1のリスニングか、2のヒアリングか。答えは、コメントで教えてね。", answer=1, word="listening"),
         point="listen to は「(自分から)耳を傾ける」、hear は「(自然に)聞こえる」。",
         detail="""■ listen to …自分から聞く
listen to music(音楽を聞く)
Listen to me.(わたしの話を聞いて)
listen のあとには to が必要。

■ hear …自然に聞こえる
I heard a strange sound.(変な音が聞こえた)
Can you hear me?(聞こえる?)

■ 見る も同じ関係
look at(自分から見る)/ see(自然に見える)
watch(動くものをじっと見る)

■ よくある間違い
× I'm listening music. → ○ I'm listening to music."""),
]
