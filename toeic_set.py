"""TOEIC リーディングのカルーセル1セット(表紙→問題→答え・解説→和訳→単語→案内)。
英文はすべてオリジナル。上半分=英文(固定)、下半分=解説 の形。"""
from PIL import Image, ImageDraw
from pathlib import Path
import sys
from toeic_cover import W, H, CREAM, BLACK, RED, font, anton, jp, text_img, zabuton, paste, stopwatch, arrow, asterisk, make

ROOT = Path(__file__).parent
PAPER = (250, 247, 238); MARK = (240, 178, 160); GREY = (110, 106, 98)
def serif(s): return font("EBGaramond.ttf", s)
NUM = "❶❷❸❹❺"

def wrap_jp(d, text, f, width):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for ch in para:
            if d.textlength(cur + ch, font=f) > width and ch not in "、。」）":
                lines.append(cur); cur = ch
            else: cur += ch
        lines.append(cur)
    return lines

def passage(base, x, y, w, P, size=29, hl=(), card=True):
    """P = {"kind":"E-MAIL", "head":[...], "body":[[(text, tag), ...], ...]} を描く。高さを返す"""
    d = ImageDraw.Draw(base); fs = serif(size); fh = jp(size - 6, 600); lh = int(size * 1.32)
    pad = 30; cx = x + pad; cy = y + pad + 34
    if card:
        d.rectangle((x, y, x + w, y + 10), fill=BLACK)
    for t in P["head"]:
        d.text((cx, cy), t, font=fh, fill=GREY); cy += int(lh * 0.95)
    cy += 10
    for para in P["body"]:
        px = cx
        for text, tag in para:
            words = text.split(" ")
            if tag: words = [NUM[tag - 1]] + words
            for i, wd in enumerate(words):
                if not wd: continue
                isnum = wd in NUM
                f = jp(size - 4, 800) if isnum else fs
                ww = d.textlength(wd, font=f); sp = d.textlength(" ", font=fs)
                if px + ww > x + w - pad: px = cx; cy += lh
                if tag in hl: d.rectangle((px - 2, cy + 4, px + ww + (sp if i < len(words) - 1 else 0) + 2, cy + lh - 2), fill=MARK)
                d.text((px, cy + (3 if isnum else 0)), wd, font=f, fill=RED if isnum else BLACK)
                px += ww + sp
        cy += lh + 12
    h = cy - y + pad - 12
    if card:  # 紙のカード(後ろに敷く)
        bg = Image.new("RGBA", (w, h), PAPER + (255,)); ImageDraw.Draw(bg).rectangle((0, 0, w - 1, h - 1), outline=BLACK, width=3)
        ImageDraw.Draw(bg).rectangle((0, 0, w, 44), fill=BLACK)
        ImageDraw.Draw(bg).text((22, 22), P["kind"], font=anton(24), fill=CREAM, anchor="lm")
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0)); layer.alpha_composite(bg, (x, y))
        tmp = base.copy(); base.paste(layer, (0, 0), layer)
        return passage(base, x, y, w, P, size, hl, card=False) if True else h
    return h

def frame(no, label, page, total):
    im = Image.new("RGBA", (W, H), CREAM + (255,)); d = ImageDraw.Draw(im)
    d.text((64, 50), "@toeic_read30", font=anton(30), fill=BLACK)
    d.text((W - 64, 50), f"No.{no:02d}  {page}/{total}", font=anton(30), fill=BLACK, anchor="ra")
    paste(im, zabuton(text_img(label, jp(34), CREAM), BLACK, 18, 10), (64, 100), 2)
    return im

def bottom_note(d, left, right="SWIPE"):
    d.text((64, H - 70), left, font=jp(28, 700), fill=BLACK, anchor="lm")
    if right:
        d.text((W - 130, H - 70), right, font=anton(40), fill=BLACK, anchor="rm"); arrow(d, W - 120, H - 68, W - 64, RED)

def build(Q, photos, out):
    out.mkdir(parents=True, exist_ok=True); no = Q["no"]; total = 5 + len(Q["explain"]); files = []
    files.append(make(Q["cover"]["kind"], photos / f'{Q["cover"]["photo"]}.jpg', no, *Q["cover"]["lines"], Q["sec"], out / "01_cover.png"))
    PX, PW = 64, W - 128
    # 2 問題:英文+設問+2択
    im = frame(no, "問題", 2, total); h = passage(im, PX, 190, PW, Q["passage"], 32); d = ImageDraw.Draw(im)
    stopwatch(d, W - 110, 130, 30, BLACK, RED); d.text((W - 160, 130), f"目安{Q['sec']}秒", font=jp(28, 800), fill=RED, anchor="rm")
    y = 190 + h + 40
    for ln in wrap_jp(d, Q["q"], serif(36), PW): d.text((PX, y), ln, font=serif(36), fill=BLACK); y += 46
    y += 24
    for i, (c, cj) in enumerate(Q["choices"]):
        paste(im, zabuton(text_img("AB"[i], anton(40), CREAM, 1.0), BLACK, 16, 6), (PX, y)); d = ImageDraw.Draw(im)
        d.text((PX + 80, y + 4), c, font=serif(34), fill=BLACK); y += 74
    bottom_note(d, "AかBか、コメントで答えてね")
    im.convert("RGB").save(out / "02_question.png")
    # 3 全文の和訳(答えの前に。もう一度考えてもらう)
    im = frame(no, "全文の和訳", 3, total); h = passage(im, PX, 190, PW, Q["passage"], 27); d = ImageDraw.Draw(im); y = 190 + h + 32
    for ln in wrap_jp(d, Q["ja"], jp(27, 400), PW): d.text((PX, y), ln, font=jp(27, 400), fill=BLACK); y += 41
    y += 14; d.line((PX, y, W - PX, y), fill=(210, 203, 185), width=2); y += 18
    for ln in [f"設問:{Q['q_ja']}"] + [f"({'AB'[i]}) {cj}" for i, (c, cj) in enumerate(Q["choices"])]:
        d.text((PX, y), ln, font=jp(27, 600), fill=BLACK); y += 41
    bottom_note(d, "もう一度考えてみて。答えは次へ"); im.convert("RGB").save(out / "03_ja.png")
    # 4〜 解説(上=英文固定、下=解説)
    exps = Q["explain"]
    for k, e in enumerate(exps):
        im = frame(no, e["title"], 4 + k, total); h = passage(im, PX, 190, PW, Q["passage"], 27, hl=e["hl"]); d = ImageDraw.Draw(im)
        y = 190 + h + 36
        if k == 0:
            paste(im, zabuton(text_img(f"答え  {Q['answer']}", jp(56), CREAM), RED, 22, 12), (PX, y), 2); d = ImageDraw.Draw(im); y += 110
        for ln in wrap_jp(d, e["text"], jp(34, 500), PW):
            # 「」内の英語や → の行も同じ大きさで
            d.text((PX, y), ln, font=jp(34, 500), fill=BLACK); y += 56
        bottom_note(d, f"解説 {k + 1}/{len(exps)}")
        im.convert("RGB").save(out / f"0{4 + k}_explain{k + 1}.png")
    p = 4 + len(exps)
    # 単語
    im = frame(no, "この問題の単語", p, total); d = ImageDraw.Draw(im); y = 230
    for en, ja in Q["words"]:
        d.text((PX, y), en, font=serif(54), fill=BLACK); d.text((PX, y + 70), ja, font=jp(32, 500), fill=GREY)
        d.line((PX, y + 128, W - PX, y + 128), fill=(210, 203, 185), width=2); y += 150
    asterisk(d, W - 110, 260, 30, RED)
    bottom_note(d, "保存して、単語帳がわりに"); im.convert("RGB").save(out / f"0{p}_words.png"); p += 1
    # 案内(黒地)
    im = Image.new("RGBA", (W, H), BLACK + (255,)); d = ImageDraw.Draw(im)
    d.text((64, 50), "@toeic_read30", font=anton(30), fill=CREAM)
    d.text((W - 64, 50), f"No.{no:02d}  {p}/{total}", font=anton(30), fill=CREAM, anchor="ra")
    paste(im, text_img("毎日1問、", jp(110), CREAM), (64, 300))
    paste(im, zabuton(text_img("30秒", jp(170), CREAM), RED, 18, 6), (64, 450), 3)
    paste(im, text_img("で読む力をつける。", jp(96), CREAM), (64, 700)); d = ImageDraw.Draw(im)
    for i, t in enumerate(["🔖 保存して、本番前に見返す", "👤 フォローで毎日1問とどく", "🔗 プロフィールから無料の復習ページへ"]):
        d.text((70, 920 + i * 70), t.split(" ", 1)[1], font=jp(36, 700), fill=CREAM)
        d.ellipse((40 - 10, 942 + i * 70 - 10, 40 + 10, 942 + i * 70 + 10), fill=RED)
    asterisk(d, W - 130, 360, 40, RED)
    im.convert("RGB").save(out / f"0{p}_cta.png")
    return sorted(out.glob("0*.png"))

Q3 = {
    "no": 3, "sec": 30, "answer": "(A)",
    "cover": {"kind": "cream", "photo": "p11", "lines": ("この1問、", [("30秒", "a"), ("で", "n")], "解けたら上級者")},
    "passage": {"kind": "E-MAIL", "head": ["To: All Staff", "From: Facilities Team", "Subject: East parking lot closure"],
        "body": [[("Hello everyone,", 0)],
                 [("The east parking lot will be closed from March 10 to 14 while it is repaved.", 1),
                  ("During this period, please park in the north garage on Elm Street.", 0),
                  ("Because the garage has fewer spaces, we encourage you to carpool or take the shuttle bus from Central Station.", 2),
                  ("Garage permits can be picked up at the front desk starting this Friday.", 3)],
                 [("Thank you for your cooperation.", 0)]]},
    "q": "What is suggested about the north garage?",
    "q_ja": "北の駐車場について何が分かりますか。",
    "choices": [("It has limited parking spaces.", "台数が限られている。"), ("It will be closed next week.", "来週閉鎖される。")],
    "explain": [
        {"title": "答えと根拠", "hl": (2,), "text": "❷「the garage has fewer spaces(駐車場は台数が少ない)」が根拠。\nfewer spaces → limited parking spaces(限られた台数)と言い換えた (A) が正解。"},
        {"title": "ワナの選択肢", "hl": (1,), "text": "(B)「来週閉鎖される」のは、❶の east parking lot(東の駐車場)のほう。\n北の駐車場の話ではありません。closed という同じ単語につられないように、「どこの話か」を必ず確かめよう。"},
        {"title": "解き方のコツ", "hl": (2, 3), "text": "suggested(示唆されている)の問題は、本文の語がそのまま選択肢に出ることは少なく、たいてい言い換えになっています。\n設問のキーワード(north garage)を本文で探して、その前後だけを読めば30秒で解けます。"},
    ],
    "ja": "宛先:全従業員/差出人:施設管理チーム/件名:東駐車場の閉鎖\n皆さん、こんにちは。❶東駐車場は舗装工事のため、3月10日から14日まで閉鎖されます。この期間は、エルム通りにある北の駐車場をご利用ください。❷北の駐車場は台数が少ないため、相乗りや、セントラル駅からのシャトルバスの利用をおすすめします。❸駐車場の許可証は、今週金曜日から受付で受け取れます。ご協力をお願いします。",
    "words": [("repave", "舗装し直す"), ("garage", "(屋内の)駐車場、車庫"), ("encourage A to do", "Aに〜するよう勧める"), ("carpool", "相乗りする"), ("permit", "許可証"), ("limited", "限られた")],
}

if __name__ == "__main__":
    fs = build(Q3, Path(sys.argv[1]), ROOT / "out" / "toeic_reading" / "set_03")
    tw = 270; sheet = Image.new("RGB", (tw * 4 + 12, int(tw * 1.25) * 2 + 4), "white")
    for i, f in enumerate(fs):
        sheet.paste(Image.open(f).resize((tw, int(tw * 1.25))), ((i % 4) * (tw + 4), (i // 4) * (int(tw * 1.25) + 4)))
    sheet.save(ROOT / "out" / "toeic_reading" / "set_03" / "overview.png"); print(len(fs))
