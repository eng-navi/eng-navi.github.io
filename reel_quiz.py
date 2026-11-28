"""カルーセルの問題ページを使って、タイマー付きのリールを作る(TOEIC / 英検)。
    python3 reel_quiz.py toeic 3     → out/reels/toeic_003.mp4
    python3 reel_quiz.py eiken 9
流れ:暗い画面の一言(1.2秒)→ 問題ページ+タイマー → 「答えはコメントで」(2秒)。BGM は Uppbeat(キャプションにクレジット)。"""
import subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw
from toeic_cover import font, anton
ROOT = Path(__file__).parent; OUT = ROOT / "out" / "reels"; OUT.mkdir(parents=True, exist_ok=True)
W, H, FPS = 1080, 1920, 10
def jp(s, w=900):
    f = font("NotoSansJP.ttf", s); f.set_variation_by_axes([w]); return f
CFG = {
 "toeic": dict(src="out/toeic_reading/no{:03d}/02_question.png", sec=20, bg=(238, 232, 214), ink=(11, 11, 11), acc=(207, 62, 34), dark=(11, 11, 11),
               lines=["TOEIC Part 7", "30秒で解けたら", "上級者"], tag="目安30秒 → 20秒で挑戦", bgm="lantern", credit="Lantern / all:ambient", lofi=True),
 "eiken": dict(src="out/eiken/no{:03d}/02_question.png", sec=30, bg=(247, 241, 224), ink=(31, 55, 92), acc=(214, 190, 150), dark=(20, 34, 62),
               lines=["英検準1級", "この空所、", "30秒で解ける?"], tag="目安60秒 → 30秒で挑戦", bgm="vapour", credit="Vapour / Simon Folwar"),
}
def setup(kind, no):
    """問題ごとの目安時間に合わせる(リールは目安の約3分の2)"""
    if kind == "toeic":
        from toeic_problems import PROBLEMS; Q = next(q for q in PROBLEMS if q["no"] == no); sec = Q["sec"]
        return dict(sec=7, tag=f"目安{sec}秒|長押しで止めて解いてね", lines=["TOEIC Part 7", f"{sec}秒で解けたら", "上級者"], ans="A か B を書いてね")
    from eiken_problems import PROBLEMS; Q = next(q for q in PROBLEMS if q["no"] == no); sec = Q["sec"]
    return dict(sec=7, tag=f"目安{sec}秒|長押しで止めて解いてね", lines=["英検準1級", "この空所、", f"{sec}秒で解ける?"], ans="1 か 2 を書いてね")

# lo-fi(英文法と同じ3曲)。drop=曲が盛り上がる位置。選択肢がスライドインする HIT 秒に合わせる(TOEIC で試験中 2026-11-28〜)
LOFI = [("golden_age", 26.8, "Golden Age / Walz"), ("days_off", 85.3, "Days Off / Matrika"), ("jasmine", 27.7, "Jasmine / 92elm")]
HIT = 0.45


def bgm_path(name):
    for d in ("docs/bgm", "assets/bgm"):
        p = ROOT / d / f"{name}.mp3"
        if p.exists(): return p
def ease(t): t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3

def frames(kind, no):
    """約7秒。1コマ目から問題を見せ、見出しと選択肢をすっと出す。最後も同じ画面のまま(ループしやすい)"""
    c = dict(CFG[kind]); c.update(setup(kind, no))
    q = Image.open(ROOT / c["src"].format(no)).convert("RGB"); q = q.crop((0, 0, q.width, q.height - 120))
    px = q.load(); cut = 0
    for y in range(q.height - 1, 0, -1):  # 英文カードの下端(全幅の濃い線)
        dark = sum(1 for x in range(80, q.width - 80, 20) if sum(px[x, y]) < 200)
        if dark > (q.width - 160) / 20 * 0.9: cut = y + 6; break
    bgc = px[5, q.height - 5]; bottom = q.height
    for y in range(q.height - 1, cut, -1):  # 選択肢の下の余白を切る
        if any(sum(abs(a - b) for a, b in zip(px[x, y], bgc)) > 60 for x in range(40, q.width - 40, 8)): bottom = y + 40; break
    card, rest = q.crop((0, 0, q.width, cut)), q.crop((0, cut, q.width, bottom))
    Y0 = max(360, (H - bottom) // 2 + 40)  # 縦の真ん中あたりに置く
    base = Image.new("RGB", (W, H), c["bg"]); base.paste(card, (0, Y0))
    head = Image.new("RGB", (W - 128, 150), c["dark"]); hd = ImageDraw.Draw(head)
    t1 = f"{c['lines'][0]}|{c['lines'][1]}{c['lines'][2]}"; f = jp(58)
    while f.getlength(t1) > W - 220: f = jp(f.size - 4)
    hd.text(((W - 128) // 2, 75), t1, font=f, fill=(245, 240, 228), anchor="mm")
    FR = 30; n = int(7.0 * FR)
    for k in range(n):
        t = k / FR; im = base.copy(); d = ImageDraw.Draw(im)
        im.paste(head, (64, int(-160 + (Y0 - 210 + 160) * ease(t / 0.35))))
        im.paste(rest, (int(W * (1 - ease((t - 0.45) / 0.35))), Y0 + cut))
        if t >= 0.8:
            left = max(0.0, 1 - (t - 0.8) / 5.0)
            d.rounded_rectangle((64, Y0 - 44, W - 64, Y0 - 20), 12, fill=(210, 203, 185))
            d.rounded_rectangle((64, Y0 - 44, 64 + max(24, int((W - 128) * left)), Y0 - 20), 12, fill=c["acc"] if left > 0.3 else (207, 62, 34))
        if t < 5.8: d.text((W // 2, Y0 + bottom + 70), "長押しで一時停止して、じっくり解いてね", font=jp(40, 700), fill=c["ink"], anchor="mm")
        if t >= 5.8:
            a = ease((t - 5.8) / 0.3); band = Image.new("RGB", (W - 128, 130), c["dark"]); bd = ImageDraw.Draw(band)
            bd.text(((W - 128) // 2, 65), "答えは?コメントで " + c["ans"].replace(" を書いてね", ""), font=jp(54), fill=(245, 240, 228), anchor="mm")
            im.paste(band, (64, int(H - (H - Y0 - bottom - 20) * a)))
        yield im

def build(kind, no):
    c = dict(CFG[kind]); c.update(setup(kind, no)); out = OUT / f"{kind}_{no:03d}.mp4"; tmp = OUT / "_v.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "image2pipe", "-framerate", "30", "-i", "-", "-c:v", "libx264",
                          "-pix_fmt", "yuv420p", "-r", "30", str(tmp)], stdin=subprocess.PIPE)
    total = 0
    for im in frames(kind, no): im.save(p.stdin, "PNG"); total += 1
    p.stdin.close(); p.wait(); dur = total / 30
    tick = "aevalsrc='0.12*sin(2*PI*520*t)*exp(-35*mod(t,1))*gte(t,0.8)*lte(t,5.8)+0.18*sin(2*PI*660*t)*exp(-25*(t-0.5))*gte(t,0.5)*lte(t,0.9)':d=7:s=44100,lowpass=f=1500"  # 選択肢でやわらかい「ポン」、タイマー中は控えめな秒針
    bgm, ss, credit, vol = c["bgm"], 0.0, c["credit"], 0.35
    if c.get("lofi"):
        bgm, drop, credit = LOFI[no % len(LOFI)]; ss, vol = drop - HIT, 0.32
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp), "-stream_loop", "-1", "-ss", f"{ss:.2f}", "-i", str(bgm_path(bgm)),
                    "-f", "lavfi", "-i", tick, "-filter_complex",
                    f"[1:a]volume={vol},afade=t=out:st={dur - 1.5}:d=1.5[m];[2:a]volume=0.5[t];"
                    f"[m][t]amix=inputs=2:normalize=0,alimiter=limit=0.9:level=disabled[a]",
                    "-map", "0:v", "-map", "[a]", "-t", str(dur), "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", str(out)], check=True)
    tmp.unlink(); return out, credit
if __name__ == "__main__":
    print(build(sys.argv[1], int(sys.argv[2])))
