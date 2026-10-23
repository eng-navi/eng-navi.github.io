"""eng_navi 型のクイズ動画を生成する。色(テーマ)は番号から自動で決まる。

    no % 3 == 2 → 緑「英検2級でよく出る」(2択クイズ)
    no % 3 == 0 → ピンク「英検頻出!これ↓読める?」(イディオム紹介。選択肢なし)
    no % 3 == 1 → 青「TOEICでよく出る」(2択クイズ)

使い方:
    python3 render.py quizzes.json          # 全問を out/ に書き出す
    python3 render.py quizzes.json 100      # 番号 100 だけ書き出す
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).parent
FONTS = ROOT / "fonts"
OUT = ROOT / "out"
BGM = ROOT / "assets" / "bgm.m4a"

W, H, FPS, DURATION = 1080, 1920, 30, 6.25
BAR_W = 88

# タイミング(秒)。3色とも共通(元動画から計測)
HL_START, HL_END = 0.42, 0.82
OPT_START, OPT_STEP, OPT_FADE = 0.65, 0.2, 0.35
TITLE_SWITCH = 3.65
TITLE_WIPE_DUR = 1.15   # 「答えはコメント欄で」が左から現れきるまで
TITLE_WIPE_FEATHER = 70  # 現れる境目のぼかし幅(px)
TITLE_AFTER = "答えはコメント欄で"
BLANK = "(   )"

# 色とレイアウト(元動画からピクセル単位で採取)
THEMES = {
    "green": dict(
        bar=(69, 97, 66), bg=(247, 244, 237), accent=(69, 97, 66), hl=(175, 187, 171), ink=(24, 28, 24),
        x=172, num_dx=-5, title=["英検2級でよく出る"], title_size=85, title_weight=700,
        q_size=97, q_pitch=120, q_max_w=850, blank="(\u2002\u2009)", hl_style="under",
        opt_size=71, opt_max_w=640, opt_pitch=88,
    ),
    "pink": dict(
        bar=(247, 182, 186), bg=(253, 253, 253), accent=(247, 182, 186), hl=(252, 226, 228), ink=(5, 5, 5),
        x=192, num_dx=-7, title=["英検頻出！", "これ↓読める？"], title_size=86, title_weight=500,
        q_size=75, q_pitch=88, q_max_w=740, q_top=756, hl_style="phrase",
    ),
    "blue": dict(
        bar=(173, 200, 209), bg=(253, 253, 253), accent=(172, 199, 209), hl=(222, 233, 237), ink=(30, 30, 30),
        x=172, num_dx=-20, title=["TOEICでよく出る"], title_size=86, title_weight=500,
        q_size=67, q_pitch=82, q_max_w=828, hl_style="full",
        opt_size=88, opt_max_w=760, opt_pitch=100,
    ),
}
NUM_TOP = 128
NUM_TRACKING = 9
TITLE_TOP = 406
TITLE_PITCH = 123
Q_TOP = 612
CIRCLE_D = 113
OPT_MIN_Y = 963      # 1つ目の丸の中心の最小位置
OPT_BELOW_Q = 225    # 問題文の最終行の中心から1つ目の丸の中心まで
OPT_GAP = 143


def theme_name(no):
    return {2: "green", 0: "pink", 1: "blue"}[no % 3]


def font(name, size, weight=None):
    f = ImageFont.truetype(str(FONTS / name), size)
    if weight is not None:
        f.set_variation_by_axes([weight])
    return f


def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def wrap(text, f, max_w):
    """改行(\\n)を残しつつ、幅を超えたら単語単位で折り返す。"""
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            trial = f"{cur} {word}".strip()
            if f.getlength(trial) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def cap_top(f):
    """ベースラインから大文字の上端までの距離(負の値)。"""
    return f.getbbox("H", anchor="ls")[1]


class Video:
    def __init__(self, q):
        self.q = q
        self.t = THEMES[theme_name(q["no"])]
        t = self.t
        self.x = t["x"]
        self.f_num = font("CrimsonText-Italic.ttf", 93)
        self.f_title = font("NotoSansJP.ttf", t["title_size"], t["title_weight"])
        self.f_q = font("EBGaramond.ttf", t["q_size"], 400)

        is_quiz = "options" in q
        blank = t.get("blank", BLANK)
        text = q["question"].replace("( )", blank).replace("()", blank) if is_quiz else q["text"]
        self.lines = wrap(text, self.f_q, t["q_max_w"])
        top = t.get("q_top", Q_TOP)
        self.baselines = [top - cap_top(self.f_q) + i * t["q_pitch"] for i in range(len(self.lines))]

        # 見出しのベースライン(漢字の上端を TITLE_TOP に合わせる)
        title_cap = self.f_title.getbbox("国", anchor="ls")[1]
        self.title_baselines = [TITLE_TOP - title_cap + i * TITLE_PITCH for i in range(len(t["title"]))]

        self.options = []
        if is_quiz:
            self.f_opt = font("EBGaramond.ttf", t["opt_size"], 400)
            self.f_circle = font("NotoSansJP.ttf", 72, 600)
            last_center = self.baselines[-1] + cap_top(self.f_q) / 2
            cy = max(OPT_MIN_Y, last_center + OPT_BELOW_Q)
            for opt in q["options"]:
                opt_lines = wrap(opt, self.f_opt, t["opt_max_w"])
                self.options.append((cy, opt_lines))
                cy += OPT_GAP + t["opt_pitch"] * (len(opt_lines) - 1)
        self.base = self.build_base()
        self.after_alpha, self.after_box = self.build_title_after()

    def build_base(self):
        """アニメーションしない要素だけを描いた画像。"""
        t = self.t
        img = Image.new("RGB", (W, H), t["bg"])
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, BAR_W, H], fill=t["bar"])
        num_base = NUM_TOP - self.f_num.getbbox("0", anchor="ls")[1]
        x = self.x + t["num_dx"]
        for ch in str(self.q["no"]):  # 元動画は数字の間隔が少し広い
            d.text((x, num_base), ch, font=self.f_num, fill=t["accent"], anchor="ls")
            x += self.f_num.getlength(ch) + NUM_TRACKING
        for i, (cy, _) in enumerate(self.options):
            cx = self.x + CIRCLE_D / 2
            r = CIRCLE_D / 2
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(20, 20, 20), width=6)
            # 字形そのものの外接矩形で中央に置く
            l, tp, rt, b = self.f_circle.getbbox(str(i + 1), anchor="ls")
            d.text((cx - (l + rt) / 2, cy - (tp + b) / 2), str(i + 1), font=self.f_circle, fill=(20, 20, 20), anchor="ls")
        return img

    def build_title_after(self):
        """「答えはコメント欄で」の文字の形(アルファ)。左からなめらかに見せるのに使う。"""
        alpha = Image.new("L", (W, H), 0)
        base = self.title_baselines[-1]
        ImageDraw.Draw(alpha).text((self.x, base), TITLE_AFTER, font=self.f_title, fill=255, anchor="ls")
        return alpha, alpha.getbbox()

    def wipe_mask(self, p):
        """左から右へ、境目をぼかしながら広がるマスク。"""
        left, top, right, bottom = self.after_box
        edge = left + (right - left + TITLE_WIPE_FEATHER) * p
        mask = Image.new("L", (W, H), 0)
        solid = int(edge - TITLE_WIPE_FEATHER)
        if solid > left:
            mask.paste(255, (left, top, solid, bottom))
        ramp = Image.linear_gradient("L").rotate(90, expand=True).resize((TITLE_WIPE_FEATHER, bottom - top))
        mask.paste(ramp, (solid, top))
        return mask

    def highlight(self, d, p):
        t, f = self.t, self.f_q
        if t["hl_style"] == "phrase":
            # ピンク:ターゲットの表現だけを囲む(行をまたぐ場合は行ごとに)
            target = self.q["target"]
            for line, base in zip(self.lines, self.baselines):
                start = line.find(target) if target in line else -1
                if start < 0:
                    continue
                x0 = self.x + f.getlength(line[:start]) - 8
                x1 = self.x + f.getlength(line[: start + len(target)]) + 8
                top = base + cap_top(f) - 8
                d.rectangle([x0, top, x0 + (x1 - x0) * p, base + f.size * 0.25], fill=t["hl"])
            return
        # 緑・青:括弧のある行
        i = next((i for i, line in enumerate(self.lines) if "(" in line), 0)
        base, width = self.baselines[i], f.getlength(self.lines[i])
        if t["hl_style"] == "under":
            # 緑:ベースラインから下側に引くマーカー
            d.rectangle([self.x + 3, base, self.x + 3 + (width - 5) * p, base + f.size * 0.35], fill=t["hl"])
        else:
            # 青:文字がすっぽり収まる帯
            _, top, _, bottom = f.getbbox("(", anchor="ls")
            d.rectangle([self.x - 12, base + top - 8, self.x - 12 + (width + 24) * p, base + bottom + 8], fill=t["hl"])

    def frame(self, sec):
        t = self.t
        img = self.base.copy()
        d = ImageDraw.Draw(img, "RGBA")

        if sec >= HL_START:
            self.highlight(d, ease_in_out((sec - HL_START) / (HL_END - HL_START)))
        for line, base in zip(self.lines, self.baselines):
            d.text((self.x, base), line, font=self.f_q, fill=t["ink"], anchor="ls")

        # 選択肢(左からフェードイン)
        for i, (cy, opt_lines) in enumerate(self.options):
            p = ease_in_out((sec - OPT_START - OPT_STEP * i) / OPT_FADE)
            if p <= 0:
                continue
            x = self.x + CIRCLE_D + 70 - int(40 * (1 - p))
            for j, line in enumerate(opt_lines):
                d.text((x, cy - 4 + j * t["opt_pitch"]), line, font=self.f_opt, fill=t["ink"] + (int(255 * p),), anchor="lm")

        # 見出し(途中で「答えはコメント欄で」に1文字ずつ切り替え。2行の場合は2行目の位置に出す)
        if sec < TITLE_SWITCH:
            for text, base in zip(t["title"], self.title_baselines):
                d.text((self.x, base), text, font=self.f_title, fill=t["accent"], anchor="ls")
        else:
            p = min(1.0, (sec - TITLE_SWITCH) / TITLE_WIPE_DUR)
            img.paste(t["accent"], mask=ImageChops.multiply(self.after_alpha, self.wipe_mask(p)))
        return img


def render(q):
    OUT.mkdir(exist_ok=True)
    out = OUT / f"q{q['no']}.mp4"
    video = Video(q)

    cmd = ["ffmpeg", "-v", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if BGM.exists():
        cmd += ["-i", str(BGM), "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-shortest"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart", str(out)]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(DURATION * FPS)):
        proc.stdin.write(video.frame(i / FPS).tobytes())
    proc.stdin.close()
    proc.wait()
    print(f"✓ {out}({theme_name(q['no'])})")
    return out


def main():
    quizzes = json.loads(Path(sys.argv[1]).read_text())
    if len(sys.argv) > 2:
        quizzes = [q for q in quizzes if str(q["no"]) == sys.argv[2]]
    for q in quizzes:
        render(q)


if __name__ == "__main__":
    main()
