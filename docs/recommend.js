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
  studysapuri: { name: "スタディサプリENGLISH TOEIC対策コース", note: "文法の学び直しからパート別の対策まで、スマホで。7日間無料で試せます", ...A8("3BDQJ0+CTF05E+3AQG+C6QR6", "www19") },
  hanon: { name: "英語のハノン 初級", note: "わかる文法を「口から出る」ところまで落とし込むドリル", url: AMAZON("B09NY53725", "aaa9fc05b00ffc5bcfd72de9d08bdca0") },
  progrit: { name: "PROGRIT(プログリット)", note: "何をどれだけやるかを一緒に決めてくれる英語コーチング", ...A8("3H5XC5+AUKF5U+3NP4+60OXE", "www19") },
  liberty: { name: "LIBERTY ENGLISH", note: "TOEIC・TOEFL・大学受験のハイスコアを目指す人向けの英語スクール", ...A8("3Z6RWJ+CTF05E+4MWC+5YRHE", "www11") },
  scramble: { name: "スクランブル英文法・語法 5th Edition", note: "eng_navi の文法クイズは、この本の出題ポイントをもとに作っています", url: AMAZON("B0G47KNCKX", "0ce4d1d04fdd489440ff1dce4f987caf") },
  eureka: { name: "大学入試 英文法 Eureka!", note: "暗記だけでは解けない「差がつく」文法問題を約250問", url: AMAZON("B09MTFCF6W", "ba588e8cadb139770f883ff2963f9530") },
  idiomatic: { name: "飛躍のフレーズ IDIOMATIC 300", note: "eng_navi のイディオム問題のネタ元。よくある言い回しを英文ごと覚えられる", url: AMAZON("B0DCY6K8P2", "9adf5e34e9b1aabc41601bfe20eb0ccc") },
  reading: { name: "基本文法から学ぶ 英語リーディング教本", note: "文法を土台に、英文を正確に読めるようになる定番の1冊", url: AMAZON("B0B2VJ8BL5", "d769300620a82fda9aee29d46db9f42e") },
  realize: { name: "Realize 英文「解釈」演習99 発展レベル", note: "難関大の和訳問題で、意味を正確につかむ練習", url: AMAZON("B0FYMTW7XT", "0962d322f17bca5063631e367e0dd55a") },
  pinnacle: { name: "大学入試 無敵の難単語 PINNACLE 420", note: "難しい単語で読む手が止まる人に", url: AMAZON("B0CK4HSRZN", "8ecd3ddef08dd6642b8ef647882ce7d7") },
  speak: { name: "スピーク(AI英会話アプリ)", note: "AIを相手に、声に出して英会話の練習。7日間無料で試せます", ...A8("45KI4S+B1PKVM+5PZU+5YRHE", "www10") },
  torabit: { name: "TORAbit(トラビット)", note: "シャドーイングと瞬間英作文を、AIの採点つきで1日5分から", ...A8("3ZI1Y9+3LSK76+3N0O+TS3OI", "www11") },
  yumekana: { name: "夢カナ留学", note: "ワーホリ・留学の無料カウンセリング(18〜30歳が対象)", ...A8("3Z2Q3B+AL1HHE+4Q46+5YJRM", "www19") },
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
    items: [ITEMS.scramble],
    up: { title: "標準レベルから一歩抜け出したい人へ", items: [ITEMS.eureka, ITEMS.scramble] },
  },
  "読解・イディオム": {
    title: "こういう表現を、もっと読めるようになるなら",
    items: [ITEMS.idiomatic, ITEMS.reading, ITEMS.pinnacle],
    up: { title: "難しい英文も読み切りたい人へ", items: [ITEMS.realize, ITEMS.oversight] },
  },
  default: {
    title: "英文法をまとめて固めるなら",
    items: [ITEMS.scramble, ITEMS.studysapuri],
  },
};

// 結果画面で、どのシリーズでも出す「次は話せる英語へ」
window.SPEAK = {
  title: "「わかるのに、話せない」を卒業するなら",
  items: [ITEMS.speak, ITEMS.torabit],
};
// 結果画面のいちばん下に、さりげなく1行
window.ABROAD = {
  lead: "ワーホリや留学にちょっとでも興味があるなら、話を聞いてみるだけでも。どんな選択肢があるかがわかります。",
  item: ITEMS.yumekana,
};

// Google アナリティクス(GA4)の測定ID。空なら計測しない。例: "G-XXXXXXXXXX"
window.ANALYTICS_ID = "";

// 結果画面の下に出すリンク
window.LINKS = {
  instagram: "https://www.instagram.com/eng_navi/",
};
