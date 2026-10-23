"""無料アーカイブ(サイト)を紹介するリールを作る。

    python3 promo.py      # out/promo/promo_archive.mp4

画面素材は out/promo/s1〜s5.png(サイトのスクリーンショット)。
"""
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).parent
FONTS = ROOT / "fonts"
DIR = ROOT / "out" / "promo"
# 場面の切り替わりに拍が来るよう、曲と開始位置を選んでいる(拍の解析結果)
BGM = ROOT / "docs" / "bgm" / "the-waves.mp3"
BGM_START = 4.56
W, H, FPS, DURATION = 1080, 1920, 30, 15.5

BG = (253, 253, 253)
INK = (30, 30, 30)
SUB = (110, 110, 110)
G, P, B = (69, 97, 66), (247, 182, 186), (173, 200, 209)
B_INK = (95, 138, 153)


def font(name, size, weight=None):
    f = ImageFont.truetype(str(FONTS / name), size)
    if weight:
        f.set_variation_by_axes([weight])
    return f


JP_B = lambda s: font("NotoSansJP.ttf", s, 700)
JP = lambda s: font("NotoSansJP.ttf", s, 500)
EN_I = lambda s: font("CrimsonText-Italic.ttf", s)


def clamp(x):
    return max(0.0, min(1.0, x))


def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def window(t, start, end, fade=0.35):
    """start〜end の間だけ見える。前後 fade 秒でフェード。"""
    return clamp((t - start) / fade) * clamp((end - t) / fade)


def text(layer, xy, s, f, fill, alpha=1.0, dy=0, anchor="la"):
    if alpha <= 0:
        return
    d = ImageDraw.Draw(layer)
    d.text((xy[0], xy[1] + dy), s, font=f, fill=fill + (int(255 * alpha),), anchor=anchor)


# ---- スマホの枠と画面 ----
SCREEN_W = 600
shots = [Image.open(DIR / f"s{i}.png").convert("RGB") for i in range(1, 6)]
shots = [s.resize((SCREEN_W, int(s.height * SCREEN_W / s.width))) for s in shots]
SCREEN_H = min(s.height for s in shots)
shots = [s.crop((0, 0, SCREEN_W, SCREEN_H)) for s in shots]
BEZEL = 16
PW, PH = SCREEN_W + BEZEL * 2, SCREEN_H + BEZEL * 2
screen_mask = Image.new("L", (SCREEN_W, SCREEN_H), 0)
ImageDraw.Draw(screen_mask).rounded_rectangle([0, 0, SCREEN_W, SCREEN_H], radius=56, fill=255)
phone_shadow = Image.new("RGBA", (PW + 160, PH + 160), (0, 0, 0, 0))
ImageDraw.Draw(phone_shadow).rounded_rectangle([80, 100, PW + 80, PH + 100], radius=72, fill=(0, 0, 0, 55))
phone_shadow = phone_shadow.filter(ImageFilter.GaussianBlur(36))

# 画面ごとの表示時間と、上に出す一言
SCREENS = [
    (4.3, "目的からえらんで"),
    (5.6, "タップで答え合わせ"),
    (6.8, "正解・不正解がすぐわかる"),
    (8.0, "イディオムは意味と解説も"),
    (9.2, "解説と英文の音声つき"),
]
PHONE_IN, PHONE_OUT = 4.0, 10.6


def phone_frame(t):
    """今の時刻のスマホ画面(画面の切り替えはクロスフェード)。"""
    img = Image.new("RGB", (SCREEN_W, SCREEN_H))
    for i, (start, _) in enumerate(SCREENS):
        a = clamp((t - start) / 0.35) if i else 1.0
        if a <= 0:
            break
        shot = shots[i]
        img = Image.blend(img, shot, a) if i else shot.copy()
    phone = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
    ImageDraw.Draw(phone).rounded_rectangle([0, 0, PW, PH], radius=70, fill=INK + (255,))
    phone.paste(img, (BEZEL, BEZEL), screen_mask)
    return phone


def stripes(layer, t):
    """3色の線:最初は中央に大きく、そのあと左端の帯になる。"""
    d = ImageDraw.Draw(layer)
    grow = ease(t / 0.8)
    move = ease((t - 1.6) / 0.7)
    for i, c in enumerate((G, P, B)):
        # 中央の3本線
        x0 = 380 + i * 120
        h = 520 * grow
        cx0 = x0 + (0 - x0) * move
        cw = 90 + (40 - 90) * move
        cy0 = (700 - h / 2) + ((i * H / 3) - (700 - h / 2)) * move
        cy1 = (700 + h / 2) + (((i + 1) * H / 3) - (700 + h / 2)) * move
        d.rectangle([cx0, cy0, cx0 + cw, cy1], fill=c + (255,))


def frame(t):
    img = Image.new("RGBA", (W, H), BG + (255,))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    stripes(layer, t)
    X = 110

    # 0〜2.3 秒:リールの続き、
    a = window(t, 0.9, 2.3)
    text(layer, (W // 2, 1150), "リールの続き、", JP_B(92), INK, a, dy=30 * (1 - ease((t - 0.9) / 0.5)), anchor="mm")

    # 2.3〜4.1 秒:100問以上、ぜんぶ無料で。
    a = window(t, 2.3, 4.1)
    rise = 40 * (1 - ease((t - 2.3) / 0.6))
    text(layer, (X, 620), "100", EN_I(230), B, a, dy=rise)
    text(layer, (X, 900), "問以上、", JP_B(110), INK, a, dy=rise)
    a2 = window(t, 2.6, 4.1)
    text(layer, (X, 1060), "ぜんぶ無料で。", JP_B(110), INK, a2, dy=40 * (1 - ease((t - 2.6) / 0.6)))
    text(layer, (X + 4, 1250), "Instagram の問題を、サイトでまとめて。", JP(40), SUB, a2)

    # 4.0〜10.6 秒:スマホでサイトを使う様子
    if PHONE_IN - 0.1 < t < PHONE_OUT + 0.5:
        enter = ease((t - PHONE_IN) / 0.7)
        leave = ease((t - PHONE_OUT) / 0.5)
        py = int(H - (H - 470) * enter + 300 * leave)
        px = (W - PW) // 2
        alpha = 1 - leave
        ph = phone_frame(t)
        if alpha < 1:
            ph.putalpha(ph.getchannel("A").point(lambda v: int(v * alpha)))
        sh = phone_shadow.copy()
        sh.putalpha(sh.getchannel("A").point(lambda v: int(v * alpha)))
        layer.alpha_composite(sh, (px - 80, py - 80))
        layer.alpha_composite(ph, (px, py))
        for i, (start, cap) in enumerate(SCREENS):
            end = SCREENS[i + 1][0] if i + 1 < len(SCREENS) else PHONE_OUT
            ca = window(t, start + 0.1, end + 0.1, 0.25) * (1 - leave)
            text(layer, (W // 2, 330), cap, JP_B(64), INK, ca, dy=16 * (1 - ease((t - start - 0.1) / 0.3)), anchor="mm")

    # 10.8〜12.9 秒:3シリーズと特徴
    rows = [("TOEIC", "34", B, B_INK), ("英検2級", "34", G, G), ("イディオム", "33", P, (217, 128, 136))]
    for i, (name, n, c, ink) in enumerate(rows):
        s = 10.8 + i * 0.18
        a = window(t, s, 12.9)
        x = X + 60 * (1 - ease((t - s) / 0.5))
        y = 620 + i * 190
        d = ImageDraw.Draw(layer)
        if a > 0:
            d.rectangle([x, y, x + 18, y + 120], fill=c + (int(255 * a),))
        text(layer, (x + 60, y + 6), name, JP_B(84), ink, a)
        text(layer, (x + 60 + 540, y + 22), n, EN_I(80), SUB, a)
        text(layer, (x + 60 + 640, y + 40), "問", JP(48), SUB, a)
    a = window(t, 11.5, 12.9)
    text(layer, (X, 1270), "音声つき ・ 登録不要 ・ 無料", JP(48), SUB, a)

    # 13.0〜15.5 秒:ハイライト「無料アーカイブ」から
    a = clamp((t - 13.0) / 0.4)
    if a > 0:
        rise = 30 * (1 - ease((t - 13.0) / 0.6))
        text(layer, (W // 2, 560), "プロフィールの", JP_B(76), INK, a, dy=rise, anchor="mm")
        text(layer, (W // 2, 680), "ハイライトから、どうぞ", JP_B(76), INK, a, dy=rise, anchor="mm")
        # ハイライトの丸(3本線のカバー)
        cx, cy, r = W // 2, 1000, 150
        d = ImageDraw.Draw(layer)
        pulse = (t - 13.6) % 1.4 / 1.4 if t > 13.6 else 0
        if pulse:
            rr = r + 14 + 60 * pulse
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=B + (int(160 * (1 - pulse) * a),), width=6)
        d.ellipse([cx - r - 14, cy - r - 14, cx + r + 14, cy + r + 14], outline=(220, 220, 220, int(255 * a)), width=4)
        circle = Image.new("RGBA", (r * 2, r * 2), BG + (255,))
        cd = ImageDraw.Draw(circle)
        for i, c in enumerate((G, P, B)):
            cd.rectangle([r - 108 + i * 78, r - 105, r - 108 + i * 78 + 60, r + 105], fill=c)
        m = Image.new("L", (r * 2, r * 2), 0)
        ImageDraw.Draw(m).ellipse([0, 0, r * 2, r * 2], fill=int(255 * a))
        layer.paste(circle, (cx - r, cy - r), m)
        text(layer, (cx, cy + r + 70), "無料アーカイブ", JP(46), INK, a, anchor="mm")
        text(layer, (cx, 1500), "@eng_navi", EN_I(64), B_INK, clamp((t - 13.6) / 0.4), anchor="mm")

    img.alpha_composite(layer)
    return img.convert("RGB")


def main():
    out = DIR / "promo_archive.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-ss", str(BGM_START), "-i", str(BGM), "-map", "0:v", "-map", "1:a",
           "-af", f"afade=t=in:d=0.6,afade=t=out:st={DURATION - 1.5}:d=1.5,loudnorm=I=-16:TP=-1.5",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "aac", "-shortest",
           "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(DURATION * FPS)):
        proc.stdin.write(frame(i / FPS).tobytes())
    proc.stdin.close()
    proc.wait()
    print(f"✓ {out}")


if __name__ == "__main__":
    main()
