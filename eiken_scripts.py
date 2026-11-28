"""英検リールの新形式(eiken_easy.py)の台本の続き。1週間ずつここに足す(eiken_easy.py は読まなくてよい)。
書き方:signal=(大きく出す語, 意味)、steps=根拠の場面(hl=本文で黄色にする語句、hl_ja=和訳で黄色、dim=薄くする文)、
answer_say / trap_say、app=応用問題(同じ発想・ちがう合図/場面。答えを本問と同じ語にしない)、caption、comment。
台本の *語* は字幕で黄緑。英単語はカタカナで書き、eiken_easy.DISP に表示用の英字を足す。
"""
DISP = {"イン・ショート": "In short", "アイロニカリー": "Ironically", "サプライジングリー": "Surprisingly", "オルゾウ": "Although", "モアオーバー": "Moreover", "ネバーザレス": "Nevertheless", "ウォーン": "warn", "アンレス": "unless"}

MORE = {
    8: dict(
        signal=("Although", "〜だけれども"),
        signal_say="ポイントは、*オルゾウ*。前と後ろが*逆の関係*になる合図です。",
        steps=[
            dict(tag="前半", hl={2: "employees worked fewer hours"}, hl_ja={2: "働く時間は減った"}, dim={1, 3},
                 say="2文目の前半。社員の*働く時間は減った*。ふつうなら、成果も減りそうですよね。"),
            dict(tag="根拠", hl={3: "feeling less tired"}, hl_ja={3: "疲れにくくなった"}, dim={1, 2},
                 say="3文目。*疲れにくくなって*、集中できた。つまり、成果は*落ちていない*。"),
        ],
        answer_say="だから*正解は1*。生産性は、変わらないか、上がった。予想と*逆の内容*です。",
        trap_say="2の、プロジェクトが遅れた、は*予想どおり*の結果なので、ばつ。",
        app=dict(sents=[("The new park has fewer trees than the old one.", 1),
                        ("Even though it has less shade, ( ① ).", 2),
                        ("Its playground and water fountains have become popular with children.", 3)],
                 chs=[("more families visit it than before", "以前より多くの家族が訪れている"), ("fewer people use it in summer", "夏に使う人が減った")], ans=1),
        caption="""Although のあと、何が来る?🤔
「時間が減った → 成果も減った」は予想どおりの流れ。Although(〜だけれども)のあとは予想と逆。英検準1級・2級の長文で使える読み方です。
解きたい人は一時停止してね⏸ 応用問題の答えはコメント欄に👇

#英検準1級 #英検2級 #長文読解 #英検対策 #英語学習""",
        comment="""✅ 応用問題の正解は 1

The new park has fewer trees than the old one. Even though it has less shade, more families visit it than before. Its playground and water fountains have become popular with children.
新しい公園は、前の公園より木が少ない。日陰は少ないけれども、以前より多くの家族が訪れている。遊び場と噴水が子どもたちに人気になっているのだ。

━━ 解説 ━━
Even though(〜だけれども)は Although と同じ「予想と逆」の合図。
「日陰が少ない → 人が減る」が予想どおりなので、空所はその逆 → 1。
❸ の「遊び場と噴水が人気」も 1 の根拠。
2「夏に使う人が減った」は予想どおりの流れなので×。

━━ 動画の問題の全文 ━━
Several companies have tested a four-day work week. Although employees worked fewer hours, their productivity stayed the same or improved. Many reported feeling less tired, which helped them focus better while they were at work.
いくつかの会社が、週4日勤務を試した。社員の働く時間は減ったけれども、生産性は変わらないか、むしろ上がった。多くの人が疲れにくくなったと答え、それが仕事中の集中につながったのだ。

📝 単語
productivity 生産性 / improve 良くなる / report 報告する / focus 集中する / even though 〜だけれども / shade 日陰 / fountain 噴水"""),
    9: dict(
        signal=("A → B", "同じ向き?逆向き?"),
        signal_say="空所は、*つなぎの言葉*。前と後ろが、*同じ向き*か、*逆向き*かを見ます。",
        steps=[
            dict(tag="❶ はメリット", hl={1: "far less greenhouse gas"}, hl_ja={1: "はるかに少ない温室効果ガス"}, dim={2, 3},
                 say="1文目。牛肉より、*温室効果ガスがずっと少ない*。メリットです。"),
            dict(tag="❷ もメリット", hl={2: "much less land and water"}, hl_ja={2: "土地と水もずっと少ない"}, dim={1, 3},
                 say="2文目。作るのに必要な*土地と水も少ない*。これも*メリット*。"),
        ],
        answer_say="メリットにメリットを*足す*ので、*正解は1*。モアオーバー、さらに。",
        trap_say="2の、ネバーザレスは、前と*逆の内容*をつなぐ言葉なので、ばつ。",
        app=dict(sents=[("Cycling to work saves money on gas.", 1),
                        ("( ① ), it is a simple way to get regular exercise.", 2)],
                 chs=[("In addition", "さらに"), ("On the other hand", "一方で")], ans=1),
        caption="""つなぎの言葉の空所、どう選ぶ?🤔
前と後ろが「同じ向き」なら Moreover、「逆向き」なら Nevertheless。英検準1級の長文で毎回出る、つなぎ言葉の選び方を1問で。
解きたい人は一時停止してね⏸ 応用問題の答えはコメント欄に👇

#英検準1級 #英検 #英語長文 #つなぎ言葉 #英検対策""",
        comment="""✅ 応用問題の正解は 1

Cycling to work saves money on gas. In addition, it is a simple way to get regular exercise.
自転車通勤はガソリン代の節約になる。さらに、定期的に運動する簡単な方法でもある。

━━ 解説 ━━
❶「ガソリン代の節約」(メリット)→ ❷「手軽な運動になる」(メリット)。
同じ向き(メリット+メリット)なので、付け足しの In addition(さらに)→ 1。
2 On the other hand(一方で)は逆向きのときに使うので×。

付け足し:Moreover / In addition / Furthermore / Also
逆向き:Nevertheless / However / On the other hand

━━ 動画の問題の全文 ━━
Plant-based meat produces far less greenhouse gas than beef. Moreover, it requires much less land and water to make. For these reasons, some experts believe it could play a key role in fighting climate change.
植物由来の肉は、牛肉よりもはるかに少ない温室効果ガスしか出さない。さらに、作るのに必要な土地と水もずっと少ない。これらの理由から、気候変動との戦いで大きな役割を果たすと考える専門家もいる。

📝 単語
plant-based 植物由来の / greenhouse gas 温室効果ガス / require 必要とする / moreover さらに / nevertheless それにもかかわらず / regular 定期的な"""),
    10: dict(
        signal=("warn", "警告する"),
        signal_say="ポイントは、*ウォーン*。科学者が*警告*しているので、このままだと*悪い結果*になる、という流れです。",
        steps=[
            dict(tag="原因", hl={2: "Rising sea temperatures"}, hl_ja={2: "海水温の上昇"}, dim={1, 3},
                 say="2文目。*海水温の上昇*で、サンゴが死んでしまう。これが原因です。"),
            dict(tag="結果", hl={3: "many reefs may disappear"}, hl_ja={3: "多くのサンゴ礁が消えるかもしれない"}, dim={1, 2},
                 say="3文目。多くのサンゴ礁が*消えるかもしれない*。空所には、その*条件*が入ります。"),
        ],
        answer_say="原因を止めない限り、なので*正解は1*。アンレスは、*しない限り*、という意味です。",
        trap_say="2の、魚が離れていく、は*本文にない理由*なので、ばつ。",
        app=dict(sents=[("Many small bookstores are struggling because more people buy books online.", 1),
                        ("Owners warn that ( ① ), more shops will close next year.", 2)],
                 chs=[("if sales do not recover", "売り上げが回復しなければ"), ("because readers love paper books", "読者は紙の本が好きなので")], ans=1),
        caption="""「警告」の文の空所、何が入る?🤔
warn(警告する)の文は「このままだと悪い結果に」の流れ。原因を止めない限り=unless を選ぶ、英検準1級の長文読解のコツです。
解きたい人は一時停止してね⏸ 応用問題の答えはコメント欄に👇

#英検準1級 #英検対策 #英語長文 #環境問題 #英語学習""",
        comment="""✅ 応用問題の正解は 1

Many small bookstores are struggling because more people buy books online. Owners warn that if sales do not recover, more shops will close next year.
ネットで本を買う人が増え、多くの小さな書店が苦しんでいる。店主たちは、売り上げが回復しなければ、来年はさらに多くの店が閉まると警告している。

━━ 解説 ━━
warn(警告する)の文は「このままだと悪い結果になる」の形。
❶ の原因(ネットで買う人が増えた)が続く → 売り上げが戻らなければ → 閉店、の条件で 1。
2「紙の本が好きなので」は閉店の理由にならず、本文の流れとも合わないので×。

━━ 動画の問題の全文 ━━
Coral reefs are home to about a quarter of all ocean species. Rising sea temperatures, however, cause corals to lose their color and eventually die. Scientists warn that unless ocean warming is slowed, many reefs may disappear within this century.
サンゴ礁には、海の生き物全体の約4分の1がすんでいる。しかし、海水温の上昇によってサンゴは色を失い、やがて死んでしまう。科学者たちは、海の温暖化を遅らせない限り、今世紀中に多くのサンゴ礁が消えるかもしれないと警告している。

📝 単語
coral reef サンゴ礁 / species 種 / eventually やがて / warn 警告する / unless 〜しない限り / struggle 苦しむ / recover 回復する"""),
    11: {'signal': ('In short', '要するに'), 'signal_say': 'ポイントは、*イン・ショート*。要するに、と*前の内容をまとめる*合図です。', 'steps': [{'tag': '❶ 切り替えが速い', 'hl': {1: 'switch between tasks more quickly'}, 'hl_ja': {1: '作業の切り替えが速い'}, 'dim': {2, 3}, 'say': '1文目。バイリンガルの子どもは、*作業の切り替えが速い*。'}, {'tag': '❷ 無視が得意', 'hl': {2: 'ignoring information that is not relevant'}, 'hl_ja': {2: '関係のない情報を無視する'}, 'dim': {1, 3}, 'say': '2文目。*関係のない情報を無視する*のも得意。どちらも、*注意をコントロールする力*です。'}], 'answer_say': 'それをまとめた、*正解は1*。脳の、注意をコントロールする力をきたえる。', 'trap_say': '2の、ほかの教科の学習がおくれる、は*本文にない*ので、ばつ。', 'app': {'sents': [('Workers who take short walks during the day report feeling less stressed.', 1), ('They also tend to come up with more creative ideas.', 2), ('Overall, a brief walk may ( ① ).', 3)], 'chs': [('improve both mood and thinking', '気分と考える力の両方を良くする'), ('make people work fewer hours', '働く時間を減らす')], 'ans': 1}, 'caption': 'In short のあとは、何が来る?🤔\n要するに=前の内容のまとめ。❶と❷の共通点を一言で言いかえた選択肢を選ぶのが、英検準1級の長文のコツです。\n解きたい人は一時停止してね⏸ 応用問題の答えはコメント欄に👇\n\n#英検準1級 #英検 #長文読解 #英検対策 #バイリンガル', 'comment': "✅ 応用問題の正解は 1\n\nWorkers who take short walks during the day report feeling less stressed. They also tend to come up with more creative ideas. Overall, a brief walk may improve both mood and thinking.\n日中に短い散歩をする人は、ストレスが減ったと答えている。さらに、より創造的なアイデアを思いつきやすい。全体として、少しの散歩は気分と考える力の両方を良くするのかもしれない。\n\n━━ 解説 ━━\nOverall(全体として)も In short と同じ「まとめ」の合図。\n❶ ストレスが減る(気分)+❷ アイデアが出る(考える力)→ 両方をまとめた 1。\n2「働く時間が減る」は本文にないので×。\n\n━━ 動画の問題の全文 ━━\nStudies show that bilingual children often switch between tasks more quickly than other children. They are also better at ignoring information that is not relevant. In short, learning two languages may train the brain's ability to control attention.\n研究によると、バイリンガルの子どもは、ほかの子どもより作業の切り替えが速いことが多い。また、関係のない情報を無視するのも得意だ。要するに、2つの言語を学ぶことは、注意をコントロールする脳の力をきたえるのかもしれない。\n\n📝 単語\nbilingual 2か国語を話す / switch 切り替える / relevant 関係のある / in short 要するに / attention 注意 / overall 全体として"},
    12: {'signal': ('Ironically', '皮肉なことに'), 'signal_say': 'ポイントは、*アイロニカリー*。皮肉なことに、と*目的と逆の結果*になる合図です。', 'steps': [{'tag': '目的', 'hl': {1: 'help them use their phones less'}, 'hl_ja': {1: 'スマホを使う時間を減らす'}, 'dim': {2, 3}, 'say': '1文目。アプリの目的は、スマホを*使う時間を減らす*こと。'}, {'tag': '根拠', 'hl': {3: 'check them several times a day'}, 'hl_ja': {3: '1日に何度も'}, 'dim': {1, 2}, 'say': '3文目。そのアプリを、*1日に何度も*確認している。つまり、かえって*スマホを見ている*。'}], 'answer_say': '目的と逆の結果なので、*正解は1*。かえって、スマホをもっと見るようになる。', 'trap_say': '2の、値段が高すぎる、は*本文にない*ので、ばつ。', 'app': {'sents': [('Many people buy large planners to organize their busy schedules.', 1), ('Paradoxically, the planners sometimes ( ① ).', 2), ('Filling in every page takes so much time that users fall further behind.', 3)], 'chs': [('leave people with even less free time', 'かえって自由な時間を減らす'), ('are hard to find in stores', '店で見つけにくい')], 'ans': 1}, 'caption': 'Ironically(皮肉なことに)のあと、何が来る?🤔\n「目的と逆の結果」を読む合図。スマホを減らすアプリの話で、英検準1級・2級の長文によく出る流れを1問で。\n解きたい人は一時停止してね⏸ 応用問題の答えはコメント欄に👇\n\n#英検準1級 #英検2級 #英語長文 #英検対策 #スマホ依存', 'comment': '✅ 応用問題の正解は 1\n\nMany people buy large planners to organize their busy schedules. Paradoxically, the planners sometimes leave people with even less free time. Filling in every page takes so much time that users fall further behind.\n多くの人が、忙しい予定を整理するために大きな手帳を買う。逆説的だが、その手帳がかえって自由な時間を減らすこともある。全ページを埋めるのに時間がかかりすぎて、さらに予定が遅れてしまうのだ。\n\n━━ 解説 ━━\nParadoxically(逆説的に)も Ironically と同じ「目的と逆の結果」の合図。\n目的=予定を整理する → 結果=❸ 時間がかかりすぎて遅れる → 1。\n2「店で見つけにくい」は本文にないので×。\n\n━━ 動画の問題の全文 ━━\nMany people download apps that are designed to help them use their phones less. Ironically, these apps can make people look at their phones even more. Users often check them several times a day to see how much time they have spent on other apps.\nスマホを使う時間を減らすためのアプリをダウンロードする人は多い。皮肉なことに、こうしたアプリはかえってスマホを見る時間を増やすことがある。利用者は、ほかのアプリにどれだけ時間を使ったかを見るために、1日に何度もそのアプリを確認することが多いのだ。\n\n📝 単語\nbe designed to do 〜するために作られている / ironically 皮肉なことに / paradoxically 逆説的に / planner 手帳 / fall behind 遅れる'},
    13: {'signal': ('Surprisingly', '意外にも'), 'signal_say': 'ポイントは、*サプライジングリー*。意外にも、と*予想と逆*の内容が来る合図です。', 'steps': [{'tag': '予想', 'hl': {1: 'expected plastic waste to fall sharply'}, 'hl_ja': {1: '大きく減ると期待していた'}, 'dim': {2, 3}, 'say': '1文目。担当者は、プラスチックごみが*大きく減る*と予想していた。'}, {'tag': '根拠', 'hl': {3: 'they now had to buy bags instead'}, 'hl_ja': {3: '代わりに袋を買う必要が出た'}, 'dim': {1, 2}, 'say': '3文目。家で使う袋を、*代わりに買う*ようになった。だから、ゴミ袋の売上は。'}], 'answer_say': '予想と逆の、*正解は1*。目立って増えた。', 'trap_say': '2の、ゼロになった、は*予想どおり*の方向なので、ばつ。', 'app': {'sents': [('The town expected fewer visitors after the old festival was canceled.', 1), ('Unexpectedly, the number of tourists ( ① ).', 2), ('Many came to enjoy the quiet streets and local cafés instead.', 3)], 'chs': [('actually increased that year', 'その年はむしろ増えた'), ('fell to its lowest level', '過去最低まで減った')], 'ans': 1}, 'caption': 'Surprisingly のあと、増えた?減った?🤔\n「意外にも」は予想と逆の合図。レジ袋禁止でゴミ袋の売上はどうなった?英検準1級の長文で差がつく読み方を1問で。\n解きたい人は一時停止してね⏸ 応用問題の答えはコメント欄に👇\n\n#英検準1級 #長文読解 #英検対策 #環境問題 #英語学習', 'comment': '✅ 応用問題の正解は 1\n\nThe town expected fewer visitors after the old festival was canceled. Unexpectedly, the number of tourists actually increased that year. Many came to enjoy the quiet streets and local cafés instead.\n昔からの祭りが中止になり、町は観光客が減ると予想していた。意外にも、その年の観光客はむしろ増えた。多くの人が、代わりに静かな町並みや地元のカフェを楽しみに来たのだ。\n\n━━ 解説 ━━\nUnexpectedly(予想外にも)も Surprisingly と同じ「予想と逆」の合図。\n予想=❶ 減る → 空所はその逆=増えた(1)。❸ の「多くの人が来た」も根拠。\n2 は予想どおりの方向なので×。\n\n━━ 動画の問題の全文 ━━\nWhen a city banned free plastic bags, officials expected plastic waste to fall sharply. Surprisingly, sales of thicker plastic trash bags rose noticeably. People had been reusing shopping bags at home, so they now had to buy bags instead.\nある市が無料のレジ袋を禁止したとき、担当者はプラスチックごみが大きく減ると期待していた。意外にも、厚手のゴミ袋の売上は目立って増えた。人々は買い物袋を家で使い回していたため、代わりに袋を買う必要が出たのだ。\n\n📝 単語\nban 禁止する / sharply 大きく / surprisingly 意外にも / noticeably 目立って / unexpectedly 予想外に / cancel 中止する'},
}
