# クイズショートの作り方(量産用の説明書)

台本を `if_short.py` の `SHORTS` に1つ書く → 1コマンドで動画とコメント欄の文ができる → 1コマンドで予約。
新しい回を作るときは、この説明書のルールを必ず守る。

## シリーズ

| シリーズ | アカウント | 声(固定) | 単語のレベル | 長さ | 冒頭 / 2択 | 出力先 | 予約 |
|---|---|---|---|---|---|---|---|
| 25秒リスニングクイズ | 旧4コマ(MANGA_IG_*) | Brian / Lily | 英検2級〜1級 | 25秒前後(上限30) | 3秒の時計 / 4秒 | out/if_short/ | `python3 manga_post.py addif <name> "YYYY-MM-DD HH:MM"` |
| 名探偵アイビーの謎解き | @vocab_flicks(IVY_IG_*) | Alice(イギリス英語・女性)、探偵の一人称 | 英検2級〜1級+文の形1つ | 25秒前後(上限30) | 3秒の時計+CASE番号 / 4秒 | out/ivy_short/ | `python3 ivy_post.py add <name> "..."` |
| やさしい英語の科学クイズ | 未接続(使っていない古いアカウントをつなぐ予定) | Sarah(アメリカ英語・女性)、0.7倍+文のあいだ0.7秒(約110語/分)、博士のキャラ、曲は Cycles / Tunnel / Vapour を回して反応を見る(assets/bgm/、公開しない) | 英検3級〜準2級 | 10〜15秒 | 1.5秒の謎の絵 / 3秒 | out/sci_short/ | つないだら ivy_post.py と同じ形で作る |

共通の設定は `IVY = dict(...)` `SCI = dict(...)` にまとめてある。新しい回は `dict(IVY, ...)` のように書く。

## 1本の台本に書く項目

- `q` / `q_ja`:問題(英語 / 日本語)。日本語は意味の切れ目で `\n` を入れる(冒頭と2択の画面の改行位置)
- `choices`(2つ)、`answer`(1 か 2)、`answer_ja`:正解の和訳(コメント欄に出す)
- `shots`:`("ナレーション1行", dict(構図))` のリスト。**1行=1カット**
- `ja`:各行の和訳(shots と同じ数)
- `hl`:黄色の字幕にする単語。`gloss`:`"単語:意味"`(コメント欄の注釈。1文に3個まで自動で振り分け)
- `hook`:キャプションの一言目。`tags`:ハッシュタグ
- アイビーだけ:`caseNo="CASE #04"`、`grammar=[形, 説明, 例文]`
- 科学だけ:`no="#003"`、`mystery`(冒頭と最後のループに使う絵。Insert の種類)。1文は短く(3〜6語)、2〜3文
- 任意:`bgm`(docs/bgm/<id>.mp3。クレジットは if_short.py の MUSICS に足す)、`gap`(1文ずつ読んで間を入れる秒数)、`speed`(0.7〜1.2)

## 構図(shots の dict)

- `type`:face(顔のアップ)/ eyes(目の超アップ)/ full(全身)/ two(2人)/ wide(遠景で走る)/ insert(物のアップ)/ lens(虫めがねで拡大)/ split(左右に分けて比べる、`left` `right` に文字)/ silhouette(逆光のシルエット)/ ots(肩越し)
- `cam`:push(寄る)/ pull(引く)/ pan(横に流れる)/ shake(揺れる)/ whip(横から素早く入る)/ tilt(傾く)/ snap(途中で一気に寄る)/ rise(下から上へ)
- `wipe`:iris(丸く開く)/ slide(横から滑り込む)
- `bg`:room / street / bank / dark / office / bedroom / lab
- `insert`:coin / chart / phone / brain / clock / card / menu / strawberry / prism(`value` に文字)
- キャラ:`eyes`(normal / shock / worried / smug / happy / squint / angry / glasses)、`mouth`(smile / o / flat / grin / wavy / none)、`color`、2人目は `eyes2` `mouth2` `color2`
- 探偵の見た目は `det=True`、博士は `sci=True`
- 演出:`hud`(上に数字)、`stamp`(「CLUE 1」「SOLVED」)、`mark=[x, y, 半径]`(赤丸)、`zoom`(正体を隠す拡大)、`focus=[x, y]`(lens でのぞく位置)、`sfx`(laugh / cash / gasp / ding / boom)

## 台本のルール(全シリーズ)

1. **正解は音声の言い換え**にする。**まちがいの選択肢には、音声と同じ単語**を入れる(英検と同じ。聞けた人だけ当たる)
2. 正解の A / B は回ごとに入れ替える
3. 単語:そのシリーズのレベルの単語を、テーマとは別に**6〜8個**(科学は3〜4個)まんべんなく入れ、`hl` と `gloss` に載せる
4. 長さ:リスニングとアイビーは7行前後で25秒前後、科学は3行(15〜20語)で15秒以内。超えたら台本を削る(警告が出る)
5. **同じ type と cam を2カット続けない**。1本の中で構図を5種類以上使う(アイビー・リスニング)
6. 事実は本当のことだけ。心理学・科学は実際の研究や定説にもとづく(数字は確かめる)
7. 本の文の写しは使わない。全部オリジナルの文
8. アイビーは一人称(I / my)で語る。決めゼリフで締める(Elementary / Case closed)
9. 科学の「これ何?」の回は、物語の中で正体の全体を見せない(`zoom` で隠す)

## コメント欄(自動で作られる。形を変えない)

- 空行には全角スペースを入れる(無いと Instagram で改行が消える)
- 答えは3行:「答え:B」→ 英文 → 日本語
- 【全文と和訳】:①英文 → 和訳 → 「　▶ 単語 … 意味」(1文に3個まで)→ 空行
- アイビーは最後に【今日の文の形】

## 手順

1. `SHORTS` に台本を書く(上のルールを確認)
2. `.venv-tts/bin/python if_short.py <name>`(複数も可)で、動画・コメント欄の文(.txt)・props(.json)ができる
3. 何コマか切り出して、絵・字幕・改行を確認する(ffmpeg で tile)
4. 予約する(上の表のコマンド)。投稿時にコメントが自動で付く
5. Threads に連動する5選を出すなら、quizify_threads_queue.json に `kind: "reel5"` を足す
6. コミットして push する

## 効果音

`assets/sfx/` に whoosh / pop / boom / tick / laugh / cash / gasp / ding(.wav か .mp3)を置くと、全シリーズでそちらを使う。無いものはプログラムで作った音。
