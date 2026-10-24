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
