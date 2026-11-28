"""TOEIC リールの新形式(toeic_easy.py)の台本の続き。1週間ずつここに足す(toeic_easy.py は読まなくてよい)。
steps:01 設問(kind="q")→ 02 根拠(kind="p":hl=本文で青、hl_ja=和訳で青、dim=薄くする文。番号なしの文は 0)→ 03 正解(kind="o")→ 04 ワナ。
app=応用問題(同じ発想・ちがう場面)、caption、comment。台本の英単語はカタカナで書き、DISP に表示用の英字を足す。
"""
DISP = {"プリンター・ペーパー": "printer paper", "ディスコンティニュード": "discontinued", "アウト・オブ・ストック": "out of stock",
        "エンカレッジド": "encouraged", "プリーズ": "please", "リザーブ": "reserve", "ブック": "book", "イン・アドバンス": "in advance",
        "ビフォーハンド": "beforehand", "アドミッション・イズ・フリー": "Admission is free", "ハウエバー": "However", "アーリー": "early"}

MORE = {
    9: dict(
        key=("printer paper", "用紙について"),
        steps=[
            dict(no="01", tag="設問", l1="設問は", l2="*用紙* について", kind="q",
                 say="設問は、*プリンター・ペーパー*、つまり*用紙*について、何が書かれているか。"),
            dict(no="02", tag="根拠", l1="❷ に用紙の話", l2="*別便* で届く", kind="p",
                 hl={2: "it will be sent separately"}, hl_ja={2: "別便でお送りし"}, dim={0, 1, 3},
                 say="2文目。用紙は在庫切れで、*別便*で送られる。インクは、*もう発送済み*です。"),
            dict(no="03", tag="正解", l1="つまり", l2="*(A)* が正解", kind="o",
                 say="つまり、用紙は*インクより後*に届く。エーが正解。"),
            dict(no="04", tag="ワナ", l1="(B) は", l2="*生産終了ではない*", kind="p",
                 hl={2: "currently out of stock"}, hl_ja={2: "在庫切れ"}, dim={0, 1, 3},
                 say="ビーの、ディスコンティニュードは、*生産終了*。アウト・オブ・ストックは、*今は在庫がない*だけなので、ばつ。"),
        ],
        app=dict(P={"kind": "E-MAIL", "head": ["Subject: Your Order #5531"],
                    "body": [[("Your chairs were shipped today.", 1),
                              ("The matching desk is temporarily out of stock, so it will be delivered next month.", 2)]]},
                 q="What is indicated about the desk?",
                 chs=[("It will arrive after the chairs.", ""), ("It is no longer sold.", "")], ans="A"),
        caption="""out of stock と discontinued、違いわかる?🤔
「在庫切れ」と「生産終了」はTOEICの定番ワナ。注文確認メールで「何が後から届くか」を読む、Part 7 の解き方を1問で。
解きたい人は一時停止してね⏸ 応用問題の答えはコメント欄に👇

#TOEIC #TOEICリーディング #Part7 #TOEIC単語 #ビジネス英語""",
        comment="""✅ 応用問題の正解は (A)

Your chairs were shipped today. The matching desk is temporarily out of stock, so it will be delivered next month.
椅子は本日発送しました。おそろいの机は一時的に在庫切れのため、来月お届けします。

What is indicated about the desk?(机について何が述べられていますか)
(A) It will arrive after the chairs.(椅子より後に届く)
(B) It is no longer sold.(もう販売されていない)

━━ 解説 ━━
❶ 椅子は今日発送 → ❷ 机は来月 → 椅子より後に届く (A)。
temporarily out of stock(一時的に在庫切れ)は、また入荷するという意味。
(B) no longer sold = discontinued(生産・販売終了)とは違うので×。

━━ 動画の問題の全文 ━━
Thank you for shopping at Pinewood Office Supply. Your order of five ink cartridges and two packs of printer paper has been processed, and the ink cartridges have been shipped. Because the paper is currently out of stock at our main warehouse, it will be sent separately and should arrive within a week. You will receive a tracking number by e-mail for each package.
インクカートリッジ5個とコピー用紙2パックのご注文を承り、インクは発送しました。用紙は現在、本社倉庫で在庫切れのため別便でお送りし、1週間以内に届く予定です。各荷物の追跡番号はメールでお知らせします。

📝 単語
process 処理する / ship 発送する / out of stock 在庫切れ / separately 別々に / discontinued 生産終了の / temporarily 一時的に"""),
    10: dict(
        key=("encouraged", "勧められていること"),
        steps=[
            dict(no="01", tag="設問", l1="設問のキーワードは", l2="*encouraged*(勧められる)", kind="q",
                 say="設問のキーワードは、*エンカレッジド*。来場者が*勧められていること*を聞いています。"),
            dict(no="02", tag="根拠", l1="please のあとに", l2="*お願い* がある", kind="p",
                 hl={3: "please reserve a seat online in advance"}, hl_ja={3: "前もってオンラインで席をご予約ください"}, dim={1, 2},
                 say="3文目の*プリーズ*のあと。前もって、*オンラインで席を予約*してください。"),
            dict(no="03", tag="正解", l1="言いかえに注目", l2="*(A)* が正解", kind="o",
                 say="リザーブをブック、イン・アドバンスを*ビフォーハンド*と言いかえた、エーが正解。"),
            dict(no="04", tag="ワナ", l1="(B) は逆", l2="*入場は無料*", kind="p",
                 hl={3: "Admission is free"}, hl_ja={3: "入場は無料"}, dim={1, 2},
                 say="ビーの、入場料を払う、はワナ。*アドミッション・イズ・フリー*、入場は*無料*です。"),
        ],
        app=dict(P={"kind": "NOTICE", "head": ["City Hall — Free Tax Workshop"],
                    "body": [[("The workshop on May 12 is open to all residents at no charge.", 1),
                              ("Space is limited, so please sign up at the front desk by May 5.", 2)]]},
                 q="What are residents asked to do?",
                 chs=[("Pay a small fee", ""), ("Register in advance", "")], ans="B"),
        caption="""TOEIC の「勧められていること」はどこを見る?🤔
encouraged / asked を見たら please のあとを探す。reserve → book、in advance → beforehand の言いかえまで、Part 7 のイベント告知を1問で。
解きたい人は一時停止してね⏸ 応用問題の答えはコメント欄に👇

#TOEIC #TOEIC対策 #Part7 #言い換え #英語学習""",
        comment="""✅ 応用問題の正解は (B)

The workshop on May 12 is open to all residents at no charge. Space is limited, so please sign up at the front desk by May 5.
5月12日の講座は、すべての住民が無料で参加できます。定員があるため、5月5日までに受付でお申し込みください。

What are residents asked to do?(住民は何をするよう求められていますか)
(A) Pay a small fee(少しの料金を払う)
(B) Register in advance(前もって申し込む)

━━ 解説 ━━
asked(求められている)も encouraged と同じく please のあとを探す。
❷ please sign up 〜 by May 5 → sign up を register、by May 5 を in advance と言いかえた (B)。
(A) は ❶ at no charge(無料で)と逆なので×。

free / at no charge / complimentary =「無料」。お金の話はワナになりやすい。

━━ 動画の問題の全文 ━━
The fair will be held in the main hall from July 8 to July 10. Local authors will give talks each afternoon at 2:00 P.M., and copies of their books will be available for purchase. Admission is free, but seating for the talks is limited, so please reserve a seat online in advance.
フェアは7月8日から10日まで、メインホールで開かれます。毎日午後2時から地元の作家による講演があり、作家の本も購入できます。入場は無料ですが、講演の座席には限りがあるため、前もってオンラインで席をご予約ください。

📝 単語
admission 入場 / limited 限られた / reserve 予約する / in advance 前もって / beforehand 前もって / at no charge 無料で / sign up 申し込む"""),
    11: dict(
        key=("avoid the price increase", "値上げを避ける方法"),
        steps=[
            dict(no="01", tag="設問", l1="設問は", l2="*値上げを避ける* 方法", kind="q",
                 say="設問は、パテルさんが*値上げを避ける方法*。"),
            dict(no="02", tag="根拠", l1="However のあとに", l2="*例外* がある", kind="p",
                 hl={3: "before August 31"}, hl_ja={3: "8月31日より前に"}, dim={1, 2},
                 say="3文目の*ハウエバー*のあと。*8月31日より前*に更新すれば、*今の料金のまま*。"),
            dict(no="03", tag="正解", l1="言いかえに注目", l2="*(A)* が正解", kind="o",
                 say="8月31日より前を、*アーリー*、早めに、と言いかえた、エーが正解。"),
            dict(no="04", tag="ワナ", l1="(B) の電子版は", l2="*本文にない*", kind="p", hl={}, dim=set(),
                 say="ビーの、電子版に切りかえる、は*本文のどこにもない*ので、ばつ。"),
        ],
        app=dict(P={"kind": "LETTER", "head": ["Dear Mr. Lopez,"],
                    "body": [[("Starting next month, our gym membership fee will rise to $50.", 1),
                              ("Members who pay for six months in advance by March 15 will continue to pay $45.", 2)]]},
                 q="How can Mr. Lopez keep paying $45?",
                 chs=[("By paying in advance", ""), ("By bringing a friend", "")], ans="A"),
        caption="""値上げを避ける方法、どこに書いてある?🤔
However のあとの「例外」に答えがある。before August 31 → early の言いかえも定番。TOEIC Part 7 の手紙問題を1問で解説します。
解きたい人は一時停止してね⏸ 応用問題の答えはコメント欄に👇

#TOEIC #TOEIC勉強 #Part7 #TOEICリーディング #社会人の勉強""",
        comment="""✅ 応用問題の正解は (A)

Starting next month, our gym membership fee will rise to $50. Members who pay for six months in advance by March 15 will continue to pay $45.
来月からジムの会費は50ドルに上がります。3月15日までに6か月分を前払いした会員は、45ドルのままです。

How can Mr. Lopez keep paying $45?(Lopez さんはどうすれば45ドルのままでいられますか)
(A) By paying in advance(前払いすることで)
(B) By bringing a friend(友達を連れてくることで)

━━ 解説 ━━
❷ pay for six months in advance by March 15 → 前払いすれば45ドルのまま → (A)。
(B) 友達の紹介は本文にないので×。
「値上げ → でも例外あり」は TOEIC の手紙・お知らせの定番の流れ。However / but / if you 〜 のあとを探そう。

━━ 動画の問題の全文 ━━
Thank you for subscribing to Urban Living magazine for the past three years. Starting in September, the monthly price will increase from $6 to $7 due to rising printing costs. However, if you renew your subscription for one year before August 31, you can keep the current price.
この3年間、『アーバン・リビング』誌をご購読いただき、ありがとうございます。印刷費の値上がりにより、9月から月額料金が6ドルから7ドルに上がります。ただし、8月31日より前に1年間の購読を更新していただければ、現在の料金のままご購読いただけます。

📝 単語
subscribe 定期購読する / due to 〜のため / renew 更新する / current 現在の / in advance 前もって / membership fee 会費"""),
}
