// サイト共通のヘッダー(左上:ロゴ=トップへ/右上:メニュー)。各ページの <body> の直後で読み込む:
//   <script src="/nav.js"></script>
(function () {
  if (document.querySelector(".en-nav")) return;
  const LINKS = [
    { group: "無料で復習(音声つき)" },
    { href: "/", label: "英文法クイズ", note: "英検・TOEICの2択" },
    { href: "/q/", label: "問題の一覧", note: "番号から探す" },
    { href: "/listening/", label: "リスニング", note: "1回で聞き取る" },
    { href: "/tango/", label: "英単語(基本)", note: "入試・英検の頻出" },
    { href: "/tango-advanced/", label: "英単語(上級)", note: "英検準1級の瞬間英作文" },
    { href: "/list/", label: "フレーズ集", note: "テーマ別の5選・10選" },
    { href: "/reading/", label: "TOEIC読解", note: "Part7を30秒で" },
    { group: "おすすめ" },
    { href: "/go/#tango", label: "おすすめ教材・サービス", note: "単語・文法・TOEIC・英会話・留学", pr: true },
  ];
  const css = `
  .en-nav{position:relative;z-index:50;display:flex;align-items:center;justify-content:space-between;height:52px;padding:0 14px;background:#fffdf8;border-bottom:1px solid #e3ddd0;font-family:"Noto Sans JP",system-ui,-apple-system,"Hiragino Sans",sans-serif}
  .en-nav .en-logo{font-family:"EB Garamond",Georgia,serif;font-style:italic;font-weight:500;font-size:23px;color:#45613f;text-decoration:none;letter-spacing:.01em;line-height:1}
  .en-nav .en-menu-btn{display:flex;align-items:center;gap:7px;font:600 14px/1 inherit;font-family:inherit;color:#1b211d;background:#fff;border:1px solid #e3ddd0;border-radius:99px;padding:8px 13px;cursor:pointer}
  .en-nav .en-bars{display:inline-block;width:15px;height:10px;background:linear-gradient(#1b211d 0 0) top/100% 2px no-repeat,linear-gradient(#1b211d 0 0) center/100% 2px no-repeat,linear-gradient(#1b211d 0 0) bottom/100% 2px no-repeat}
  .en-nav .en-panel{position:absolute;top:58px;right:10px;width:min(320px,calc(100vw - 20px));max-height:calc(100vh - 80px);overflow:auto;background:#fffdf8;border:1px solid #e3ddd0;border-radius:16px;box-shadow:0 14px 40px rgba(0,0,0,.14);padding:8px;display:none}
  .en-nav.open .en-panel{display:block}
  .en-nav .en-group{font-size:11px;color:#6a6f69;letter-spacing:.06em;padding:10px 10px 4px}
  .en-nav .en-link{display:block;padding:9px 10px;border-radius:10px;text-decoration:none;color:#1b211d}
  .en-nav .en-link:hover{background:#f1ede3}
  .en-nav .en-link.cur{background:#e9efe6}
  .en-nav .en-link b{display:block;font-size:15px;font-weight:700}
  .en-nav .en-link span{display:block;font-size:12px;color:#6a6f69}
  .en-nav .en-pr{font-size:10px;font-weight:700;color:#b5473f;border:1px solid #b5473f;border-radius:4px;padding:0 4px;margin-left:6px;vertical-align:2px}`;
  const style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);
  const path = location.pathname.replace(/index\.html$/, "");
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const items = LINKS.map((l) => l.group ? `<div class="en-group">${esc(l.group)}</div>`
    : `<a class="en-link${(l.href === "/" ? path === "/" : path.startsWith(l.href.split("#")[0])) ? " cur" : ""}" href="${l.href}"><b>${esc(l.label)}${l.pr ? '<span class="en-pr" style="display:inline">PR</span>' : ""}</b><span>${esc(l.note)}</span></a>`).join("");
  const nav = document.createElement("header");
  nav.className = "en-nav";
  nav.innerHTML = `<a class="en-logo" href="/" aria-label="eng_navi トップへ">eng_navi</a>
    <button class="en-menu-btn" aria-expanded="false" aria-label="メニューを開く"><span class="en-bars"></span>メニュー</button>
    <nav class="en-panel">${items}</nav>`;
  document.body.prepend(nav);
  const btn = nav.querySelector(".en-menu-btn");
  const toggle = (open) => { nav.classList.toggle("open", open); btn.setAttribute("aria-expanded", open); };
  btn.addEventListener("click", (e) => { e.stopPropagation(); toggle(!nav.classList.contains("open")); });
  document.addEventListener("click", (e) => { if (!nav.contains(e.target)) toggle(false); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") toggle(false); });
  nav.addEventListener("click", (e) => {
    const a = e.target.closest("a");
    if (a && window.gtag) gtag("event", "nav_click", { label: a.getAttribute("href"), from: path });
  });
})();
