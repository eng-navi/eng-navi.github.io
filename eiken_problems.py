"""英検リーディング部の問題(準1級・長文の空所補充)。英文はすべてオリジナル。1投稿=1段落+空所1つ。"""
PROBLEMS = [
    {
        "no": 1, "sec": 60, "level": "準1級", "answer": 2, "layout": 1, "photo": "girl_glasses",
        "cover": ("解けたら準1級レベル", "Contrary?", "空所に入る“つなぎ”は?"),
        "title": "Rooftop Beekeeping",
        "body": [[("In recent years, beekeeping has spread from the countryside to the rooftops of large cities.", 1),
                  ("Many people assume that urban areas are too polluted for bees to survive.", 2),
                  ("( ① ), city bees often produce more honey than those kept on farms.", 3),
                  ("This is largely because parks and gardens offer a wide variety of flowers, whereas modern farms tend to grow a single crop over vast areas.", 4)]],
        "q": "Choose the best phrase to fill in the blank.", "q_ja": "空所①に入る最も適切なものを選びなさい。",
        "choices": [("As a result", "その結果"), ("Contrary to this belief", "この考えに反して"), ("In other words", "言い換えると"), ("For this reason", "このため")],
        "explain": [
            {"hl": (2, 3), "text": "❷「都市は汚れていて、蜂は生きられないと思われている」→ ❸「都市の蜂のほうが多くの蜜を作る」。\n予想と逆の事実が続くので、「この考えに反して」の 2 が正解。"},
            {"hl": (2,), "text": "1 As a result と 4 For this reason は「原因 → 結果」。\n「汚れている → 蜜が多い」ではつながりません。3 In other words は言い換えなので、内容が逆になる今回は×。"},
            {"hl": (3, 4), "text": "空所の文だけで決めず、次の❹まで読むのがコツ。\n❹で「花の種類が多いから」と理由が続くので、「意外な事実 → その理由」の流れが確定します。準1級は空所の前後1文ずつ読もう。"},
        ],
        "ja": "屋上での養蜂\n❶近年、養蜂は田舎から大都市のビルの屋上にまで広がっている。❷多くの人は、都市は汚染されすぎていて蜂は生きられないと思い込んでいる。❸( ① )、都市の蜂は、農場で飼われる蜂よりも多くの蜜を作ることが多い。❹これは主に、公園や庭にはさまざまな花がある一方で、現代の農場は広い土地で一種類の作物だけを育てる傾向があるからだ。",
        "words": [("beekeeping", "養蜂"), ("assume", "思い込む"), ("polluted", "汚染された"), ("contrary to A", "Aに反して"), ("a wide variety of A", "多種多様なA"), ("whereas", "〜である一方で")],
    },
]
