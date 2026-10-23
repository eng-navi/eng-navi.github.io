// 結果画面に出すおすすめ。間違えた問題の category に合わせて表示する。
// url はアフィリエイトリンクに差し替える。該当カテゴリがなければ default を使う。
window.RECOMMEND = {
  default: {
    title: "TOEIC文法をまとめて固めたい人へ",
    items: [
      { name: "(ここに文法問題集の名前)", note: "Part5の頻出ポイントを1冊で", url: "#" },
      { name: "(ここに英語学習サービスの名前)", note: "無料体験あり", url: "#" },
    ],
  },
  品詞: {
    title: "品詞問題をミスした人へ",
    items: [{ name: "(品詞に強い問題集)", note: "形容詞・副詞の見分けを徹底", url: "#" }],
  },
  時制: {
    title: "時制で迷った人へ",
    items: [{ name: "(時制がわかる文法書)", note: "完了形をイメージで理解", url: "#" }],
  },
};

// 結果画面の下に出すリンク
window.LINKS = {
  instagram: "https://www.instagram.com/eng_navi/",
};
