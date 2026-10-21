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
キャプションは毎回共通:
```
英文法を少しずつ身につけて、英語の理解を深めよう！📘✨
共通テストやTOEICのリーディングにも役立つ文法ポイントを、わかりやすく紹介しています。

#英文法 #TOEIC対策 #共通テスト英語 #英語力アップ
```

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
- 解説の最後は「〜なので、①◯◯ が正解。」で締める。

## クイズページ (site/)
- `python3 build_site.py` で quizzes.json の最新10問を `site/data.js` に書き出す。
- 結果画面のおすすめ(アフィリエイト)は `site/recommend.js` を編集。category ごとに出し分け、なければ default。
- quizzes.json の各問には `category`(品詞・前置詞・時制など)、`translation`、`explanation` を必ず入れる。
