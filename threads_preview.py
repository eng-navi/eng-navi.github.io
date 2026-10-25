"""Threads の投稿3種類の試作(投稿はしない)。

    python3 threads_preview.py     # 文章を表示し、イディオム画像を out/threads/ に書き出す
"""
from pathlib import Path

from PIL import Image, ImageDraw

import story_book as sb

OUT = Path(__file__).parent / "out" / "threads"
TOPIC = "英語学習"

# ② 投票クイズ(リールの115番を流用。選択肢は1つ25文字まで)
POLL = dict(
    text="TOEICでよく出る📝\n\nThe company ___ its new headquarters in Osaka three years ago.\n\nどれが正解?",
    options=["opened", "has opened", "had opened"],
    reply="正解は「opened」でした！(〇%の人が正解)\n\nthree years ago(3年前)は、はっきり過去を示す語句。\n現在完了(has opened)とは一緒に使えません。",
)

# ① 表現まとめ10選(長いので2つに分ける。1つ目の返信に続きを書く)
LIST_1 = """【知ってる単語なのに、意味がちがう英語10選】

① break the ice = 場をなごませる
② a piece of cake = 楽勝
③ hit the books = 猛勉強する
④ under the weather = 体調がすぐれない
⑤ spill the beans = 秘密をもらす"""
LIST_2 = """⑥ cost an arm and a leg = とても高い
⑦ once in a blue moon = めったにない
⑧ the ball is in your court = 次はあなたの番
⑨ call it a day = 今日はここまで
⑩ cut corners = 手を抜く

保存して、使えそうなものから1つずつ😊"""


def idiom_card():
    """③ イディオム画像:「直訳」と「本当の意味」のギャップを1枚で見せる(1080×1350)。"""
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), sb.PAPER)
    d = ImageDraw.Draw(img)
    for x in range(0, W, 54):
        d.line([(x, 0), (x, H)], fill=sb.GRID, width=2)
    for y in range(0, H, 54):
        d.line([(0, y), (W, y)], fill=sb.GRID, width=2)
    d.text((W // 2, 200), "break the ice", font=sb.EN(140), fill=sb.INK, anchor="ms")
    sb.underline(d, 180, 900, 230, w=7)
    # 氷のかたまりとヒビ(線画)
    cx, cy = W // 2, 520
    ice = [(cx - 190, cy - 120), (cx + 160, cy - 150), (cx + 210, cy + 130), (cx - 160, cy + 160)]
    d.polygon(ice, fill=(222, 238, 246), outline=(120, 160, 180))
    d.line(ice + [ice[0]], fill=(120, 160, 180), width=6, joint="curve")
    d.line([(cx - 20, cy - 135), (cx + 10, cy - 40), (cx - 40, cy + 30), (cx + 20, cy + 145)], fill=(80, 120, 140), width=6, joint="curve")
    d.line([(cx + 10, cy - 40), (cx + 120, cy - 10)], fill=(80, 120, 140), width=5)
    for dx, dy in ((-250, -170), (250, -190), (-260, 150)):
        sb.star(d, cx + dx, cy + dy, 20, color=(120, 160, 180))
    # 直訳 → 本当の意味
    d.text((W // 2, 800), "直訳:氷を割る", font=sb.JP(54), fill=(130, 130, 130), anchor="ms")
    sb.arrow(d, sb.curve((W // 2, 830), (W // 2 + 20, 870), (W // 2, 910)), w=5)
    d.text((W // 2, 1000), "本当の意味:場をなごませる", font=sb.JP(64), fill=sb.RED, anchor="ms")
    d.text((W // 2, 1120), "He told a joke to break the ice.", font=sb.EN(50), fill=sb.INK, anchor="ms")
    d.text((W // 2, 1185), "(彼は場をなごませようと冗談を言った)", font=sb.JP(36), fill=(110, 110, 110), anchor="ms")
    d.text((W // 2, 1290), "@eng_navi", font=sb.EN(36), fill=(150, 150, 150), anchor="ms")
    return img


IDIOM_TEXT = "直訳すると「氷を割る」🧊\n実は「場をなごませる」という意味です。\n\n初対面の人と話すとき、使ってみてね。"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    idiom_card().save(OUT / "idiom_break_the_ice.png")
    print("=== ② 投票クイズ ===")
    print(POLL["text"])
    for i, o in enumerate(POLL["options"]):
        print(f"  [投票{'ABC'[i]}] {o}")
    print(f"\n  └ (数時間後に返信) {POLL['reply']}")
    print(f"\n=== ① 表現まとめ10選(1/2 → 返信で 2/2)===\n{LIST_1}\n\n  └ {LIST_2}")
    print(f"\n=== ③ イディオム画像 ===\n{IDIOM_TEXT}\n  [画像] {OUT / 'idiom_break_the_ice.png'}")
    print(f"\n(どの投稿にもトピック「{TOPIC}」を付ける)")


if __name__ == "__main__":
    main()
