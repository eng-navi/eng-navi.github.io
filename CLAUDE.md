# insta-quiz

Instagram (@eng_navi) 向けの英語クイズ動画を作るプロジェクト。

## 問題作成のルール
- ネタ元は市販の問題集。`source/` に置かれたページのスクショから「何を問う問題か」(文法・語彙ポイント)だけを読み取る。
- 英文は必ずオリジナルで作る。本の英文・固有名詞・言い回しを流用しない。
- 解説も本の文章を写さず、作った英文に合わせて書き下ろす。
- 形式は2択。`options` は2つ、`answer` は正解の番号(1 or 2)。
- 番号 `no` は `quizzes.json` の最大値の続きから振る。

## 作業の流れ
1. `source/` のスクショを読み、出題ポイントを拾う
2. `quizzes.json` に追記(question は括弧を `( )` で書く)
3. `python3 render.py quizzes.json <no>` で動画を書き出す → `out/q<no>.mp4`

## 投稿の文章
キャプションは毎回書き下ろす(同じ文の使い回しは凍結・シャドウバンの原因になるため禁止)。quizzes.json の `caption` に入れる。
- 2〜3行の短い文。その回の文法・表現に触れ、検索されやすい語(TOEIC、英検、文法項目名など)を自然に含める
- ハッシュタグはその回に合うものを3つ程度。毎回同じ組み合わせにしない
- 例(76):「🌈 英文法を楽しみながら、英語の深みを体験しよう！共通テストやTOEICリーディングの解答テクニックをシェアして、英語力を効果的に向上させましょう！✨」

投稿直後に自分でつけるコメント(答え+解説)。quizzes.json の `translation` と `explanation` から作る:
```
--------------------------------------
【97】
I thought about taking advantage of the opportunity to study overseas.
海外留学の機会を活かすことを考えました。

【解説】
「〜することを考える」は、〈think about + 動名詞〉で表します。

think は、目的語として節を取る場合は、基本的に that節を取ります。

動名詞を続ける場合は、about や of を使います。
ここでは think about taking 〜 の形になるので、①about taking が正解。
--------------------------------------
```
- 1行目の英文は括弧に正解を入れた完成文。
- 解説は簡潔に。ネタ元の解説の流れ(どこに注目するか)は参考にしてよいが、文章は作った英文に合わせて書き下ろす。
- 解説の最後は「〜なので、①◯◯ が正解。」で締める。

## クイズページ (docs/ = GitHub Pages で公開)
- `python3 build_site.py` で quizzes.json の最新10問を `docs/data.js` に書き出す。
- 結果画面のおすすめ(アフィリエイト)は `docs/recommend.js` を編集。category ごとに出し分け、なければ default。
- quizzes.json の各問には `category`(品詞・前置詞・時制など)、`translation`、`explanation` を必ず入れる。

## 色のローテーション(厳守)
番号ごとに 緑 → ピンク → 青 の3つで1セット。3列グリッドで縦に色がそろう。
- `no % 3 == 2` → 緑 「英検2級でよく出る」 クイズ形式(2択)
- `no % 3 == 0` → ピンク 「英検頻出！ / これ↓読める？」 クイズではない。難しいイディオム・読解表現を1つ取り上げ、英文中のその部分にハイライトを引いて解説する。ネタ元はイディオムの本(文法の本とは別)
- `no % 3 == 1` → 青 「TOEICでよく出る」 クイズ形式(2択)
例: 98 緑 / 99 ピンク / 100 青 / 101 緑 / 102 ピンク / 103 青

quizzes.json の形式:
- 緑・青: `no, category, question(括弧は ( )), options(2つ), answer, translation, explanation, caption`
- ピンク: `no, text(改行は \\n), target(ハイライトする表現。text 中の文字列と完全一致), translation, glossary(["表現：意味", ...]), explanation, caption`

BGM は全色共通で assets/bgm.m4a(フリー素材、本人確認済み)。尺も同じ。

### ピンクのコメント形式(例: 99)
```
--------------------------------------
"I can't stand it," she said, closing her laptop as if to say work could wait.
「もう無理」と言って、彼女はパソコンを閉じた。仕事は後でいい、と言うように。

can't stand it：もう耐えられない
close her laptop：パソコンを閉じる
as if to say：まるで〜と言うかのように
work could wait：仕事は後回しにできる

【解説】
「I can't stand it」は「もう耐えられない」という意味です。
ここでの it は、続けていた仕事やその状況を指します。

「as if to say work could wait」は、パソコンを閉じる様子が「仕事は後でいい」と言っているように見えた、という意味です。
--------------------------------------
```
ピンクのキャプションは毎回書き下ろし(場面の一言紹介+2行目で例文の見どころ)+ `#英語フレーズ #英語学習のコツ #英検準1級`。
- サイトに載るのは posted.json の最新番号まで(未投稿の答えを先に見せない)。投稿後に build_site.py → commit → push で反映。

## 予約投稿(GitHub Actions)
- 予約: `python3 schedule.py add <no> "YYYY-MM-DD HH:MM"`(日本時間)。動画を docs/videos に公開してから schedule.json に追加する
- `.github/workflows/post.yml` が15分おきに `schedule.py run` を実行し、時間になった予約を1件投稿 → posted.json とサイトを更新して push
- 前の番号が未投稿なら投稿しない(色のローテーション保護)
- Secrets: IG_USER_ID, IG_ACCESS_TOKEN。トークンは refresh-token.yml が毎週延長(GH_PAT が必要)
- Instagram は空行を詰めるため、コメント・キャプションの空行には全角スペースを1文字入れる(post.py の keep_blank_lines で自動)。
- build_site.py は問題ごとのページ(docs/q/<no>/)、一覧(docs/q/)、sitemap.xml、robots.txt も書き出す(build_pages.py)。/?q=<no> でその問題からクイズを始められる。
- docs/index.html の google-site-verification のメタタグは Search Console の所有権確認用。削除しないこと。

## 本の紹介ストーリー(story_book.py)
- 方眼の背景+手書き風フォント(Kalam/Klee One)。下は左右いっぱいの赤い帯にリンクスタンプ(白地・青字)を置く
- 割引はバッジとボタン上のマイクロコピーで。値段・割引率には必ず「Kindle版」と日付(〇/〇時点)を添える
- 紹介文やストーリーに「ネタ元」という言葉は使わない(本人の希望)。

## 週刊リサーチ(クラウドの定期実行)
- 毎週月曜 8:00(日本時間)に、新刊・語学書セール・TOEIC/英検の公式日程を Web で調べ、実行結果(claude.ai の routines 画面の実行履歴)にレポートを書き、スマホに通知する。クラウド環境からは公式サイトに直接アクセスできないことがあり、その場合は「公式未確認」と書かれる
- 管理・停止: https://claude.ai/code/routines/trig_01BPeiVpLe4SGi4rhh8STQRF
- 結果から「今月のお得」ストーリー(story_book.py)や Threads・フィードの投稿を作る。値段・割引率は日付つきで扱う

## Threads(threads.py)
- 投票クイズ: `python3 threads.py poll <no>`(2択の問題を流用、トピック「英語学習」)。記録は threads_posted.json
- 答え: 投票クイズの直後に、同じツリーの返信として「正解・完成文・和訳・解説の要点」を投稿(すぐ見られるように)
- .env: THREADS_USER_ID, THREADS_ACCESS_TOKEN(12/24期限。refresh-token で延長)

## スクショのリマインド(しつこく)
- 予約が切れると投稿が止まる。本人の希望で、残りが少ないときはしつこくリマインドする
- GitHub Actions「予約の残りチェック」が毎日21:00に確認し、残り3日以下なら Issue(ラベル「予約切れ注意」)を作って通知する
- Claude は insta-quiz の作業を始めるたびに、未投稿の予約が何日分残っているかを確認し、5日以下なら返答の最初に「次の週のスクショを送ってください」と伝える
- 対象は eng_navi のリール(schedule.json)と、Threads の4コマ・10選・投票クイズ(threads_queue.json)。4コマのリールは2〜3日分ずつまとめて作るので、残り2日を切ったら毎回リマインドする

## ストーリー(10選の表現を1日2問・4枚)
- story_idiom.py で問題の画像と、イギリス英語(女性→男性)の音声つき答え動画を作り docs/stories/ に置く。stories.json に予約、stories.py run で投稿(問題→1分後に答え)
- スタンプ・ハイライト追加は API 不可。ハイライトは本人が毎日手動。GitHub Actions「ハイライト追加リマインド」が毎日21:00に Issue で知らせる(閉じるまで毎日追記)
- 2枚目の下に「10個まとめて音声で → プロフィールのリンクから」。サイトのトップ →「フレーズ集」(/list/)。一番上に最新(NEW)、その下は 日常会話/TOEIC/イディオム/単語 のタブで切り替え(分類は build_lists.py の group_of がタイトルから決める)

## 4コマのアカウント(別アカウントで運用予定)
- フクロウのナビ(ツッコミ・🇬🇧男性 bm_george)とペンギンのペン(ボケ・🇬🇧女性 bf_emma)。参考にした漫画の動物(うさぎ・猫など)は使わない
- manga.py で4コマ+解説(カルーセル2枚)、manga_reel.py で紙芝居リール(BGMなし、ズームなし、切り替えにやわらかい木琴風の音。回によって --no-sfx)
- 表現は Threads の10選(threads_lists.json)から選び、話・セリフ・例文はオリジナル
- Instagram は別アカウント、Threads は eng_navi に集約。新アカウント名が決まったら画像の「@eng_navi」と案内文を差し替える

## 例文を作るときのルール(10選・4コマ・クイズ共通)
- 本の例文と、同じ形(例:X is by far the best Y / lead a workshop on X)・同じ場面・同じ主語を避ける。表現だけを使い、場面ごと変える
- 同じ本の同じ範囲から続けて選ばない。複数の本・離れたページから混ぜる
- 10選の一覧は、1行に1つ、表現のイメージに合う絵文字を付ける

## 毎日の投稿(3本柱。どれかが足りなければリマインド)
1. Instagram リール(eng_navi):1日3本(8:00/13:00/19:00)。schedule.json → GitHub Actions
2. Instagram ストーリー(eng_navi):リール投稿のたびに同じ動画を自動でストーリーにも流す(post.py の post_story)。クイズ・リンクのスタンプは API で付けられないので、本の紹介(Book Review)やリンク付きは手動
3. Threads(eng_navi):投票クイズ・10選・4コマ。threads_queue.json
- 4コマ用の Instagram アカウントは別(作成待ち)。TOEIC編はカピバラ部長が登場
- 4コマは manga_post.py(予約表 manga_schedule.json、トークンは MANGA_IG_*)。@yonkoma_eigo に投稿し、同じ動画をストーリーにも流す
- Threads の5選:threads_lists.json(items は [表現, 意味, 例文, 和訳, 絵文字])。一覧の頭に hook(つかみの一言)、絵文字つき。音声ページは build_lists.py
- フレーズのストーリー(eng_navi):story_phrase.py。1枚目「この英語、わかる?」→ 2枚目 答えと例文の動画(🇬🇧女性・男性)。スタンプなしで自動投稿。予約は story_queue.json(毎日18:00)

## アフィリエイトの運用
- 元データとメモは affiliates.md、サイトに出すものは docs/recommend.js(リンク集ページ docs/links/ も自動で同じ内容)
- 「話せない」枠は4候補(スピーク・ネイティブキャンプ・産経・TORAbit)から毎回2つ。GA4 の link_click(label)で比べ、押されないものは入れ替える
- キャンペーン確認:3日に1回の cloud routine(https://claude.ai/code/routines/trig_01FsPKuKzzuTDpM4XSCa8S4F)がスマホに通知。「キャンペーンの素材を作って」と言われたら、Book Review 系のストーリーと Threads の #PR 投稿を作る
- Threads の型:5選・10選(list)/「知らないとまずい」「スコアの壁」「意外な意味」(list の reveal:最初は単語だけ、意味はツリーで)/投票クイズ/イディオム画像/4コマ。同じ型を続けない
- 動画・画像の文字は左右に余白(manga.SAFE=120px)をとり、はみ出す場合は manga.draw_fit で改行する(iPhone SE で英文が欠けたため)
- 4コマの声は ElevenLabs(Starter・月30,000クレジット上限のキー)。ナビ=Teddy Twinkle、ペン=Mia、部長=Gappu ka Bhai(manga_reel.py の ELEVEN)。同じセリフは out/voice_cache に保存して使い回す。--kokoro で無料の声に戻せる。ElevenLabs のプランは 11/26 に自動更新されない設定
- テンポの速い4コマ:manga_fast.py(最初の1.1秒でターゲット単語+つかみの一言、画面は揺らさない(コマ切り替えだけ一瞬寄る)、声の大きさをそろえる、かすかなBGM(Cozy Places)、ElevenLabs を speed 1.1)。1本につきターゲット単語1つ(英検2級〜準1級)+使える単語を数個、解説の画像に「今回出てきた単語」

## セール・無料体験の吹き出し(サイト)
- `docs/recommend.js` の `window.SALES`(本のセール。text / until / checked)と `window.PERKS`(サービスの無料体験の一言)が、サイトのおすすめカードのボタン上に吹き出しで出る。セールは赤、until を過ぎると自動で消える。
- **毎回のセッションの最初に**、SALES のうち checked から3日以上たったもの・until が近いものをユーザーに伝え、Amazon / A8 で本当にセール中か確認してもらう。確認できたら checked を今日に、終わっていたら削除する。
- 割引率・期限は必ず確認した日付つき(吹き出しに「M/D時点」と出る)。確認できない割引は書かない。
- 毎日 21:00 の 予約の残りチェック でも、古いセールがあれば「セール確認」ラベルの Issue が立つ。

## 変更の履歴(git)
- ファイルを変えたら、**作業のひと区切りごとに必ず commit して push** する(メッセージは日本語で、何を変えたか一目でわかるように)。まとめて最後に、ではなく、その都度。
- ユーザーが「◯日前に戻したい」「前のデザインに戻して」と言ったら、`git log` で該当の commit を探し、`git revert` か該当ファイルだけ `git checkout <commit> -- <file>` で戻す(履歴は消さない。`reset --hard` や force push はしない)。
