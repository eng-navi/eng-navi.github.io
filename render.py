"""eng_navi 型のクイズ動画を生成する。

使い方:
    python3 render.py quizzes.json          # 全問を out/ に書き出す
    python3 render.py quizzes.json 100      # 番号 100 だけ書き出す
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
FONTS = ROOT / "fonts"
OUT = ROOT / "out"
BGM = ROOT / "assets" / "bgm.m4a"

W, H, FPS, DURATION = 1080, 1920, 30, 6.25

# 色(サンプル動画から採取)
BG = (253, 253, 253)
BAR = (173, 200, 209)
HIGHLIGHT = (222, 233, 237)
ACCENT = (172, 199, 209)  # 番号・見出し
INK = (30, 30, 30)

# レイアウト
BAR_W = 88
X = 172
TEXT_MAX_W = W - X - 80
NUM_Y = 96
TITLE_Y = 384
Q_Y = 668  # 1行目のベースライン
Q_LINE_H = 78
OPT_Y = 1034
OPT_GAP = 144
CIRCLE_D = 108

# タイミング(秒)
HL_START, HL_END = 0.35, 0.7
OPT_START, OPT_STEP = 0.55, 0.2
OPT_FADE = 0.3
TITLE_SWITCH = 3.6
TITLE_CHAR_DUR = 0.13

TITLE_BEFORE = "TOEICでよく出る"
TITLE_AFTER = "答えはコメント欄で"
BLANK = "(\u2002\u2002\u2009)"


def font(name, size, weight=None):
    f = ImageFont.truetype(str(FONTS / name), size)
    if weight is not None:
        f.set_variation_by_axes([weight])
    return f


F_NUM = font("EBGaramond-Italic.ttf", 96, 400)
F_TITLE = font("NotoSansJP.ttf", 80, 500)
F_Q = font("EBGaramond.ttf", 64, 400)
F_OPT = font("EBGaramond.ttf", 88, 400)
F_CIRCLE = font("NotoSansJP.ttf", 72, 500)
TITLE_TRACKING = 6


def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def wrap(text, f, max_w):
    lines, cur = [], ""
    for word in text.split(" "):
        trial = f"{cur} {word}".strip()
        if f.getlength(trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def draw_tracked(draw, xy, text, f, fill, tracking):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=f, fill=fill)
        x += f.getlength(ch) + tracking


def build_base(q):
    """アニメーションしない要素だけを描いた画像。"""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, BAR_W, H], fill=BAR)
    d.text((X - 16, NUM_Y), str(q["no"]), font=F_NUM, fill=ACCENT)
    for i in range(len(q["options"])):
        cy = OPT_Y + i * OPT_GAP
        cx = X + CIRCLE_D // 2
        r = CIRCLE_D // 2
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INK, width=5)
        # 字形そのものの外接矩形で中央に置く
        l, t, r, b = F_CIRCLE.getbbox(str(i + 1), anchor="ls")
        d.text((cx - (l + r) / 2, cy - (t + b) / 2), str(i + 1), font=F_CIRCLE, fill=INK, anchor="ls")
    return img


def render_frame(base, q, lines, t):
    img = base.copy()
    d = ImageDraw.Draw(img, "RGBA")

    # 1行目のハイライト(左から右へ伸びる)
    if t >= HL_START:
        hl = next((i for i, line in enumerate(lines) if "(" in line), 0)
        # 括弧の高さ(アセンダ〜ディセンダ)を基準に、文字がすっぽり収まる帯にする
        _, top, _, bottom = F_Q.getbbox("(", anchor="ls")
        y = Q_Y + hl * Q_LINE_H
        full_w = F_Q.getlength(lines[hl]) + 24
        p = ease_in_out((t - HL_START) / (HL_END - HL_START))
        d.rectangle([X - 12, y + top - 8, X - 12 + full_w * p, y + bottom + 8], fill=HIGHLIGHT)

    for i, line in enumerate(lines):
        d.text((X, Q_Y + i * Q_LINE_H), line, font=F_Q, fill=INK, anchor="ls")

    # 選択肢(左からフェードイン)
    for i, opt in enumerate(q["options"]):
        p = ease_in_out((t - OPT_START - OPT_STEP * i) / OPT_FADE)
        if p <= 0:
            continue
        x = X + CIRCLE_D + 72 - int(40 * (1 - p))
        cy = OPT_Y + i * OPT_GAP
        d.text((x, cy - 4), opt, font=F_OPT, fill=INK + (int(255 * p),), anchor="lm")

    # 見出し(途中で「答えはコメント欄で」にタイプ表示で切り替え)
    if t < TITLE_SWITCH:
        draw_tracked(d, (X, TITLE_Y), TITLE_BEFORE, F_TITLE, ACCENT, TITLE_TRACKING)
    else:
        n = (t - TITLE_SWITCH) / TITLE_CHAR_DUR
        shown = TITLE_AFTER[: int(n) + 1]
        draw_tracked(d, (X, TITLE_Y), shown, F_TITLE, ACCENT, TITLE_TRACKING)
    return img


def render(q):
    OUT.mkdir(exist_ok=True)
    out = OUT / f"q{q['no']}.mp4"
    question = q["question"].replace("( )", BLANK).replace("()", BLANK)
    lines = wrap(question, F_Q, TEXT_MAX_W)
    base = build_base(q)

    cmd = ["ffmpeg", "-v", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if BGM.exists():
        cmd += ["-i", str(BGM), "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-shortest"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart", str(out)]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(DURATION * FPS)):
        proc.stdin.write(render_frame(base, q, lines, i / FPS).tobytes())
    proc.stdin.close()
    proc.wait()
    print(f"✓ {out}")
    return out


def main():
    quizzes = json.loads(Path(sys.argv[1]).read_text())
    if len(sys.argv) > 2:
        quizzes = [q for q in quizzes if str(q["no"]) == sys.argv[2]]
    for q in quizzes:
        render(q)


if __name__ == "__main__":
    main()
