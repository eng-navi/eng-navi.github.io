"""フィード用カルーセル「英語の参考書、迷ったらこの3冊」(5枚、1080×1350)。

    python3 feed_books.py      # out/feed/books_1.png 〜 books_5.png

フィードは残り続けるので、値段や割引率は入れない(セール情報はストーリーで)。
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

import story_book as sb

ROOT = Path(__file__).parent
OUT = ROOT / "out" / "feed"
COVERS = ROOT / "out" / "story"
W, H = 1080, 1350
GREEN = (69, 97, 66)

BOOKS = [
    dict(cover="_cover_horikoshi.png", tag="長文で迷子になる人へ", title="堀越先生の 英文読解ガチ講義",
         notes=[("Point", ["英文を", "カタマリで", "読む"]), ("動画", ["授業動画", "42本つき"])],
         lines=["単語も文法もわかるのに、長文で手が止まる", "なんとなく訳してしまう", "大人の学び直しにも"]),
    dict(cover="_cover_brushup.png", tag="読解の仕上げに", title="英語リーディング・ブラッシュアップ",
         notes=[("Point", ["1テーマ", "見開きで", "サクッと"]), ("130", ["入試英文", "130題"])],
         lines=["つまずきやすい所だけ、短期間で", "長文に入る前の最後のひと磨き", "読めたつもりをチェックしたい"]),
    dict(cover="_cover_idiomatic.png", tag="言い回しを覚えたい人へ", title="大学入試 飛躍のフレーズ IDIOMATIC 300",
         notes=[("Phrase", ["よくある", "言い回しを", "英文ごと"]), ("300", ["空所補充と", "並べ替えで", "300問"])],
         lines=["ピンクの「これ↓読める？」が難しい", "空所補充で迷う", "単語は覚えたのに読めない"]),
]


def base():
    img = Image.new("RGB", (W, H), sb.PAPER)
    d = ImageDraw.Draw(img)
    for x in range(0, W, 54):
        d.line([(x, 0), (x, H)], fill=sb.GRID, width=2)
    for y in range(0, H, 54):
        d.line([(0, y), (W, y)], fill=sb.GRID, width=2)
    return img, d


def paste_cover(img, path, cx, cy, width, angle):
    cov = Image.open(path).convert("RGB")
    cov = cov.resize((width, int(cov.height * width / cov.width)))
    framed = Image.new("RGB", (cov.width + 22, cov.height + 22), (255, 255, 255))
    framed.paste(cov, (11, 11))
    sh = Image.new("RGBA", (framed.width + 100, framed.height + 100), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([50, 62, framed.width + 50, framed.height + 62], fill=(0, 0, 0, 70))
    sh = sh.filter(ImageFilter.GaussianBlur(22)).rotate(angle, expand=True, resample=Image.BICUBIC)
    fr = framed.convert("RGBA").rotate(angle, expand=True, resample=Image.BICUBIC)
    img.paste(sh, (cx - sh.width // 2, cy - sh.height // 2 + 8), sh)
    img.paste(fr, (cx - fr.width // 2, cy - fr.height // 2), fr)


def pager(d, i):
    d.text((W - 60, 80), "PR", font=sb.EN(38), fill=(120, 120, 120), anchor="ms")
    d.text((W // 2, H - 50), f"{i} / 5", font=sb.EN(34), fill=(140, 140, 140), anchor="ms")


def slide_cover():
    img, d = base()
    d.text((W // 2, 190), "Book Review", font=sb.EN(100), fill=sb.INK, anchor="ms")
    d.text((W // 2, 320), "英語の参考書、", font=sb.JP(84), fill=sb.INK, anchor="ms")
    d.text((W // 2, 430), "迷ったらこの3冊", font=sb.JP(84), fill=sb.INK, anchor="ms")
    sb.underline(d, 210, 870, 455, w=6)
    for (b, cx, cy, ang) in zip(BOOKS, (290, 540, 790), (820, 780, 820), (-7, 0, 7)):
        paste_cover(img, COVERS / b["cover"], cx, cy, 270, ang)
    d = ImageDraw.Draw(img)
    d.text((W // 2, 1160), "長文・読解・言い回し、目的別に紹介します", font=sb.JP(40), fill=sb.INK, anchor="ms")
    d.text((W // 2, 1230), "保存して、本屋さんで見返してね →", font=sb.JP(34), fill=sb.RED, anchor="ms")
    sb.star(d, 120, 120, 24)
    sb.star(d, 170, 175, 14)
    pager(d, 1)
    return img


def slide_book(i, b):
    img, d = base()
    tw = d.textlength(b["tag"], font=sb.JP(52)) / 2 + 40
    d.text((W // 2, 150), b["tag"], font=sb.JP(52), fill=sb.RED, anchor="ms")
    d.ellipse([W // 2 - tw, 88, W // 2 + tw, 180], outline=sb.RED, width=4)
    paste_cover(img, COVERS / b["cover"], W // 2, 560, 400, -2)
    d = ImageDraw.Draw(img)
    (t1, b1), (t2, b2) = b["notes"]
    sb.note(d, (140, 330), t1, b1)
    sb.arrow(d, sb.curve((190, 330 + 70 + len(b1) * 52 - 20), (215, 560), (300, 580)))
    sb.note(d, (945, 430), t2, b2)
    sb.arrow(d, sb.curve((945, 430 + 70 + len(b2) * 52 - 20), (930, 640), (790, 660)))
    d.text((W // 2, 930), b["title"], font=sb.JP(42), fill=sb.INK, anchor="ms")
    d.text((140, 1030), "こんな人に", font=sb.JP(44), fill=sb.INK, anchor="ls")
    sb.underline(d, 136, 360, 1045)
    for j, line in enumerate(b["lines"]):
        y = 1110 + j * 66
        # チェックマーク(フォントに無いので線で描く)
        d.line([(150, y - 18), (163, y - 4), (188, y - 34)], fill=sb.RED, width=6, joint="curve")
        d.text((205, y), line, font=sb.JP(40), fill=sb.INK, anchor="ls")
    pager(d, i)
    return img


def slide_cta():
    img, d = base()
    d.text((W // 2, 240), "もっと見たい人は", font=sb.JP(64), fill=sb.INK, anchor="ms")
    d.text((W // 2, 340), "プロフィールのハイライトへ", font=sb.JP(64), fill=sb.INK, anchor="ms")
    sb.underline(d, 170, 910, 365, w=6)
    # ハイライトの丸を2つ描く(おすすめ教材・無料アーカイブ)
    circles = [(350, "おすすめ教材"), (730, "無料アーカイブ")]
    for cx, label in circles:
        cy, r = 650, 140
        d.ellipse([cx - r - 14, cy - r - 14, cx + r + 14, cy + r + 14], outline=(200, 200, 200), width=5)
        if label == "おすすめ教材":
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GREEN)
            d.text((cx, cy - 10), "Books", font=sb.EN(78), fill=(247, 244, 237), anchor="mm")
        else:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(253, 253, 253))
            for k, c in enumerate(((69, 97, 66), (247, 182, 186), (173, 200, 209))):
                x = cx - 78 + k * 58
                d.rectangle([x, cy - 80, x + 44, cy + 80], fill=c)
        d.text((cx, cy + r + 70), label, font=sb.JP(40), fill=sb.INK, anchor="ms")
    sb.arrow(d, sb.curve((250, 460), (230, 500), (270, 540)), color=sb.RED, w=5)
    d.text((W // 2, 1000), "おすすめの本は「おすすめ教材」", font=sb.JP(42), fill=sb.INK, anchor="ms")
    d.text((W // 2, 1075), "過去の問題100問以上は「無料アーカイブ」", font=sb.JP(42), fill=sb.INK, anchor="ms")
    d.text((W // 2, 1180), "毎日のクイズは、フォローしてチェック", font=sb.JP(38), fill=sb.RED, anchor="ms")
    pager(d, 5)
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    slides = [slide_cover()] + [slide_book(i + 2, b) for i, b in enumerate(BOOKS)] + [slide_cta()]
    for i, s in enumerate(slides, 1):
        s.save(OUT / f"books_{i}.png")
    print(f"✓ {OUT}/books_1〜5.png")


if __name__ == "__main__":
    main()
