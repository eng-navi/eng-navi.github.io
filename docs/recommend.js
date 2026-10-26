// サイトに出すおすすめ(元データと選定理由は affiliates.md)。
// キーはシリーズ名(TOEIC / 英検2級 / 読解・イディオム)。文法の項目名(時制など)をキーにすると、その項目だけ出し分けられる。
//   title / items … 間違えた・読めなかった人向け(items[0] は解説の下にも1行で出る)
//   up            … 全問正解した人向けの「次の一歩」
// A8 のリンクは計測用画像(pixel)とセットで置く。
const A8 = (id, host) => ({
  url: `https://px.a8.net/svt/ejp?a8mat=${id}`,
  pixel: `https://${host}.a8.net/0.gif?a8mat=${id}`,
});
const AMAZON = (asin, linkId) => `https://www.amazon.co.jp/dp/${asin}?tag=mokumoku70e-22&linkCode=ll2&linkId=${linkId}&language=ja_JP&ref_=as_li_ss_tl`;

const ITEMS = {
  crack10: { name: "難関大に合格する 英語長文 Crack10", note: "長文を「文と文の流れ」で読む10のルール。難関大の設問の解き方まで", url: "https://link.amazon/B0imP6GsX" },
  shortcuts: { name: "大学受験 英文法・語法SHORTCUTS", note: "よく出る良問だけの254問。全問に正解率つきで、苦手の見極めがしやすい", url: "https://link.amazon/B0bwqM40M" },
  takeoka_drill: { name: "読むため書くための英文法ドリル Advanced", note: "約1200問の短い記述で、文法の抜けを1つずつ確認できる", url: "https://link.amazon/B05lGU2Kg" },
  classic_basic: { name: "基礎からの英文解釈クラシック", note: "品詞・文型・句と節を固めて、英文を「自動で」正しく読めるように", url: "https://link.amazon/B0iALvSYs" },
  basic_lecture: { name: "Basic Lecture 動画でわかる英文法[読解入門編]", note: "いちばん最初の英文解釈に。短期間で読み切れて、動画つき", url: "https://link.amazon/B0ba1uAVC" },
  takeoka_handbook: { name: "読むため書くための英文法ハンドブック", note: "1ポイント1ページ。竹岡先生の音声講義つきで、辞書のように引ける", url: "https://link.amazon/B00KjCWDz" },
  jokyu: { name: "読解のための上級英文法", note: "ふつうの参考書では見落としがちな文法・語法168項目を入試の実例で", url: "https://link.amazon/B01CRYH2s" },
  oni100: { name: "英語リーディングの鬼100則", note: "構造を論理的に読み解く100のルール。最難関・原書レベルを目指す人に", url: "https://link.amazon/B0cLN35ZV" },
  hanon_phrase: { name: "英語のハノン フレーズ編", note: "会話劇の中のフレーズを、くり返しの口頭練習で身につける", url: "https://link.amazon/B02PMFSik" },
  setphrase: { name: "英語の壁を乗り越えるセットフレーズ1000", note: "知ってる単語なのに意味が変わるフレーズを、穴埋めクイズで", url: "https://link.amazon/B0159dCGh" },
  kikufure: { name: "TOEIC L&Rテスト 聞いて覚える頻出英語フレーズ キクフレ", note: "TOEICによく出るフレーズを、音声つきで", url: "https://link.amazon/B09qOB6Ou" },
  horikoshi: { name: "堀越先生の 英文読解ガチ講義", note: "英文を「カタマリ」で読む。授業動画つき", url: "https://link.amazon/B01zLDQpI" },
  brushup: { name: "英語リーディング・ブラッシュアップ(登木健司)", note: "読解のつまずきポイントを見開きでサクッと", url: "https://link.amazon/B0jeP08qp" },
  studysapuri: { name: "スタディサプリENGLISH TOEIC対策コース", note: "文法の学び直しからパート別の対策まで、スマホで。7日間無料で試せます", ...A8("3BDQJ0+CTF05E+3AQG+C6QR6", "www19") },
  hanon: { name: "英語のハノン 初級", note: "わかる文法を「口から出る」ところまで落とし込むドリル", url: AMAZON("B09NY53725", "aaa9fc05b00ffc5bcfd72de9d08bdca0") },
  progrit: { name: "PROGRIT(プログリット)", note: "何をどれだけやるかを一緒に決めてくれる英語コーチング", ...A8("3H5XC5+AUKF5U+3NP4+60OXE", "www19") },
  liberty: { name: "LIBERTY ENGLISH", note: "TOEIC・TOEFL・大学受験のハイスコアを目指す人向けの英語スクール", ...A8("3Z6RWJ+CTF05E+4MWC+5YRHE", "www11") },
  scramble: { name: "スクランブル英文法・語法 5th Edition", note: "入試頻出の文法・語法を1冊で。解説が簡潔で、音声つき", url: AMAZON("B0G47KNCKX", "0ce4d1d04fdd489440ff1dce4f987caf") },
  eureka: { name: "大学入試 英文法 Eureka!", note: "暗記だけでは解けない「差がつく」文法問題を約250問", url: AMAZON("B09MTFCF6W", "ba588e8cadb139770f883ff2963f9530") },
  idiomatic: { name: "飛躍のフレーズ IDIOMATIC 300", note: "よくある言い回しを、英文ごと覚えられる。問題300問つき", url: "https://link.amazon/B0eHBRPkB" },
  reading: { name: "基本文法から学ぶ 英語リーディング教本", note: "文法を土台に、英文を正確に読めるようになる定番の1冊", url: AMAZON("B0B2VJ8BL5", "d769300620a82fda9aee29d46db9f42e") },
  realize: { name: "Realize 英文「解釈」演習99 発展レベル", note: "難関大の和訳問題で、意味を正確につかむ練習", url: AMAZON("B0FYMTW7XT", "0962d322f17bca5063631e367e0dd55a") },
  pinnacle: { name: "大学入試 無敵の難単語 PINNACLE 420", note: "難しい単語で読む手が止まる人に", url: AMAZON("B0CK4HSRZN", "8ecd3ddef08dd6642b8ef647882ce7d7") },
  speak: { name: "スピーク(AI英会話アプリ)", note: "AIを相手に、声に出して英会話の練習。7日間無料で試せます", ...A8("45KI4S+B1PKVM+5PZU+5YRHE", "www10") },
  torabit: { name: "TORAbit(トラビット)", note: "シャドーイングと瞬間英作文を、AIの採点つきで1日5分から", ...A8("3ZI1Y9+3LSK76+3N0O+TS3OI", "www11") },
  yumekana: { name: "夢カナ留学", note: "ワーホリ・留学の無料カウンセリング(18〜30歳が対象)", ...A8("3Z2Q3B+AL1HHE+4Q46+5YJRM", "www19") },
  nativecamp: { name: "ネイティブキャンプ(オンライン英会話)", note: "予約なしで、話したいときにすぐレッスン。7日間無料で試せます", ...A8("3BDOYJ+6NCBIA+35VG+64JTE", "www13") },
  sankei: { name: "産経オンライン英会話Plus", note: "日本人講師も選べる。無料体験レッスン4回つき", ...A8("3H3U53+6W9TKY+2TV8+HWXLE", "www15") },
  audible: { name: "Audible(オーディオブック)", note: "洋書の朗読を聞き流して、英語の耳をつくる。30日間無料体験", ...A8("4B1K5S+AJUM9U+5TB0+5YRHE", "www10") },
  dive: { name: "リゾートバイト ダイブ", note: "住み込みで働きながら、英語を使う職場もさがせる", ...A8("4BEOXU+8C4SI+4Z92+626XU", "www15") },
  oversight: { name: "大学入試英単語 OVERSIGHT", note: "「見たことはあるのに訳せない」300語をクイズ形式で", url: AMAZON("B0H2BMN624", "c9b5d7da796b8d08904c91469500b648") },
};

window.RECOMMEND = {
  TOEIC: {
    title: "TOEICの文法を、スキマ時間で固めるなら",
    items: [ITEMS.studysapuri, ITEMS.hanon],
    up: { title: "スコアをもう一段上げたい人へ", items: [ITEMS.progrit, ITEMS.liberty] },
  },
  英検2級: {
    title: "この文法を1冊で体系的に固めるなら",
    items: [ITEMS.scramble, ITEMS.shortcuts],
    up: { title: "標準レベルから一歩抜け出したい人へ", items: [ITEMS.eureka, ITEMS.takeoka_drill] },
  },
  "読解・イディオム": {
    title: "こういう表現を、もっと読めるようになるなら",
    items: [ITEMS.idiomatic, ITEMS.basic_lecture, ITEMS.classic_basic],
    up: { title: "難しい英文も読み切りたい人へ", items: [ITEMS.crack10, ITEMS.oni100] },
  },
  default: {
    title: "英文法をまとめて固めるなら",
    items: [ITEMS.scramble, ITEMS.shortcuts],
  },
};

// 解説の下に出す1件を、問題ごとに選ぶためのルール。
//   hook   … 商品ごとの誘い文句
//   SERIES … シリーズごとの候補。問題番号で順番に出し分ける(同じリンクばかり続かないように)
//   CATEGORY … 文法の項目に合う商品があれば、そちらを優先
window.HOOKS = {
  studysapuri: "TOEICの文法を、スキマ時間で固めるなら",
  hanon: "わかる文法を、話せる英語に変えるなら",
  scramble: "この文法を1冊で体系的に固めるなら",
  eureka: "もう一段むずかしい文法問題に挑むなら",
  idiomatic: "こういう言い回しを、もっと読めるようになるなら",
  reading: "英文を正確に読む力をつけるなら",
  pinnacle: "難しい単語で読む手が止まらないように",
  oversight: "知っている単語の「意外な訳」を押さえるなら",
  realize: "難しい英文の意味を、正確につかむなら",
};
window.PICKS = {
  SERIES: {
    TOEIC: ["studysapuri", "shortcuts", "scramble", "hanon", "takeoka_handbook"],
    英検2級: ["scramble", "shortcuts", "takeoka_drill", "eureka", "takeoka_handbook"],
    "読解・イディオム": ["idiomatic", "basic_lecture", "classic_basic", "reading", "crack10", "realize", "oni100", "jokyu", "pinnacle", "oversight"],
  },
  CATEGORY: {
    イディオム: ["idiomatic", "hanon_phrase"],
    名詞: ["oversight", "takeoka_handbook"],
    品詞: ["classic_basic", "scramble"],
    倒置: ["eureka", "jokyu"],
    関係詞: ["shortcuts", "takeoka_handbook"],
    仮定法: ["takeoka_handbook", "shortcuts"],
    時制: ["shortcuts", "takeoka_drill"],
    比較: ["takeoka_drill", "eureka"],
  },
};
window.ITEMS = ITEMS;

// 結果画面で、どのシリーズでも出す「次は話せる英語へ」
// 候補(pool)から毎回2つを選んで出す。GA4 の link_click(label)で、どれが押されているかを比べる
window.SPEAK = {
  title: "「わかるのに、話せない」を卒業するなら",
  pool: [ITEMS.speak, ITEMS.nativecamp, ITEMS.sankei, ITEMS.torabit],
};
window.SPEAK.items = window.SPEAK.pool.map((it) => [Math.random(), it]).sort((a, b) => a[0] - b[0]).slice(0, 2).map((x) => x[1]);
// フレーズ集のページの下に出す「聞き流し」の一言
window.LISTEN = { lead: "移動中に英語を聞き流すなら", item: ITEMS.audible };
// 結果画面のいちばん下に、さりげなく1行
window.ABROAD = {
  lead: "ワーホリや留学にちょっとでも興味があるなら、話を聞いてみるだけでも。どんな選択肢があるかがわかります。",
  item: ITEMS.yumekana,
};

// Google アナリティクス(GA4)の測定ID。空なら計測しない。例: "G-XXXXXXXXXX"
window.ANALYTICS_ID = "G-3FH38ZQJDF";

// 結果画面の下に出すリンク
window.LINKS = {
  instagram: "https://www.instagram.com/eng_navi/",
};
