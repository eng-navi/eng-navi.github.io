"""@toeic_read30 のプロフィール画像の候補(1080x1080、丸く切り抜かれても収まる配置)"""
from PIL import Image, ImageDraw
from toeic_cover import CREAM, BLACK, RED, anton, jp, text_img, zabuton, paste
from pathlib import Path
S = 1080; C = S // 2; OUT = Path(__file__).parent / "out" / "toeic_reading" / "icons"; OUT.mkdir(parents=True, exist_ok=True)
def canvas(bg): im = Image.new("RGBA", (S, S), bg + (255,)); return im, ImageDraw.Draw(im)
def center(im, part, cx, cy, ang=0):
    if ang: part = part.rotate(ang, resample=Image.BICUBIC, expand=True)
    im.alpha_composite(part, (int(cx - part.width / 2), int(cy - part.height / 2)))
def ring(d, r, w, base, prog, start=-90, deg=180):
    d.ellipse((C - r, C - r, C + r, C + r), outline=base, width=w)
    d.arc((C - r, C - r, C + r, C + r), start, start + deg, fill=prog, width=w)
# 1 クリーム地・大きい「30」+赤いタイマーの輪
im, d = canvas(CREAM); ring(d, 400, 46, BLACK, RED)
center(im, text_img("30", anton(470), BLACK, 1.0), C, C - 40)
center(im, text_img("TOEIC", anton(110), RED, 1.0), C, C + 240); im.save(OUT / "icon1_30ring.png")
# 2 黒地・ストップウォッチ(半分赤)+30
im, d = canvas(BLACK); r = 300; cy = C + 50
d.ellipse((C - r, cy - r, C + r, cy + r), fill=CREAM)
d.pieslice((C - r + 40, cy - r + 40, C + r - 40, cy + r - 40), -90, 90, fill=RED)
d.rounded_rectangle((C - 70, cy - r - 110, C + 70, cy - r - 50), 14, fill=CREAM); d.rectangle((C - 26, cy - r - 60, C + 26, cy - r + 10), fill=CREAM)
center(im, text_img("30", anton(300), BLACK, 1.0), C - 105, cy); im.save(OUT / "icon2_stopwatch.png")
# 3 黒地・TOEIC(クリーム)+赤い「読解」札
im, d = canvas(BLACK)
center(im, text_img("TOEIC", anton(300), CREAM, 1.0), C, C - 80)
center(im, zabuton(text_img("30秒読解", jp(120), CREAM), RED, 30, 16), C, C + 200, 4); im.save(OUT / "icon3_toeic_tag.png")
# 4 赤地・「30秒」+黒の座布団「読解」
im, d = canvas(RED)
center(im, text_img("30秒", jp(330), CREAM), C, C - 110)
center(im, zabuton(text_img("TOEIC読解", jp(130), CREAM), BLACK, 30, 14), C, C + 190, -3); im.save(OUT / "icon4_red.png")
# 5 クリーム地・黒丸の中に「読」+赤い輪(ミニマル)
im, d = canvas(CREAM); ring(d, 420, 34, CREAM, RED, -90, 180)
d.ellipse((C - 330, C - 330, C + 330, C + 330), fill=BLACK)
center(im, text_img("読", jp(400), CREAM, 1.0), C, C - 50)
center(im, text_img("TOEIC 30", anton(90), RED, 1.0), C, C + 230); im.save(OUT / "icon5_yomu.png")
# 丸く切り抜いた見え方の一覧
fs = sorted(OUT.glob("icon*.png")); t = 300; sheet = Image.new("RGB", (t * 5 + 120, t + 60), (255, 255, 255))
mask = Image.new("L", (t, t), 0); ImageDraw.Draw(mask).ellipse((0, 0, t - 1, t - 1), fill=255)
sd = ImageDraw.Draw(sheet)
for i, f in enumerate(fs):
    sheet.paste(Image.open(f).convert("RGB").resize((t, t)), (20 + i * (t + 20), 20), mask)
    sd.text((20 + i * (t + 20) + t // 2, t + 40), str(i + 1), fill="black", font=anton(28), anchor="mm")
sheet.save(OUT / "preview.png")
