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
               lines=["TOEIC Part 7", "30秒で解けたら", "上級者"], tag="目安30秒 → 20秒で挑戦", bgm="lantern", credit="Lantern / all:ambient"),
 "eiken": dict(src="out/eiken/no{:03d}/02_question.png", sec=30, bg=(247, 241, 224), ink=(31, 55, 92), acc=(214, 190, 150), dark=(20, 34, 62),
               lines=["英検準1級", "この空所、", "30秒で解ける?"], tag="目安60秒 → 30秒で挑戦", bgm="vapour", credit="Vapour / Simon Folwar"),
}
def setup(kind, no):
    """問題ごとの目安時間に合わせる(リールは目安の約3分の2)"""
    if kind == "toeic":
        from toeic_problems import PROBLEMS; Q = next(q for q in PROBLEMS if q["no"] == no); sec = Q["sec"]
        return dict(sec=round(sec * 2 / 3), tag=f"目安{sec}秒 → {round(sec * 2 / 3)}秒で挑戦", lines=["TOEIC Part 7", f"{sec}秒で解けたら", "上級者"], ans="A か B を書いてね")
    from eiken_problems import PROBLEMS; Q = next(q for q in PROBLEMS if q["no"] == no); sec = Q["sec"]
    return dict(sec=sec // 2, tag=f"目安{sec}秒 → {sec // 2}秒で挑戦", lines=["英検準1級", "この空所、", f"{sec // 2}秒で解ける?"], ans="1 か 2 を書いてね")

def bgm_path(name):
    for d in ("docs/bgm", "assets/bgm"):
        p = ROOT / d / f"{name}.mp3"
        if p.exists(): return p
def frames(kind, no):
    c = dict(CFG[kind]); c.update(setup(kind, no)); q = Image.open(ROOT / c["src"].format(no)).convert("RGB"); q = q.crop((0, 0, q.width, q.height - 120))  # 下の「swipe」案内は外す
    # 1) 暗い画面の一言
    intro = Image.new("RGB", (W, H), c["dark"]); d = ImageDraw.Draw(intro)
    for i, t in enumerate(c["lines"]):
        f = jp(150 if i == 2 else 96); col = c["acc"] if i == 2 else (245, 240, 228)
        d.text((W // 2, 700 + i * 190), t, font=f, fill=col, anchor="mm")
    d.text((W // 2, 1320), "2択クイズ", font=jp(54, 700), fill=(200, 200, 200), anchor="mm")
    for _ in range(12): yield intro
    # 2) 問題+タイマー
    base = Image.new("RGB", (W, H), c["bg"]); base.paste(q, (0, 330))
    d = ImageDraw.Draw(base)
    d.text((64, 120), c["tag"], font=jp(52, 800), fill=c["ink"]); watch_x = 0
    d.text((64, 1740), "一時停止してじっくり解いてもOK", font=jp(40, 600), fill=c["ink"])
    n = c["sec"] * FPS
    for k in range(n):
        im = base.copy(); d = ImageDraw.Draw(im); left = (n - k) / FPS
        d.rounded_rectangle((64, 220, W - 64, 262), 21, fill=(210, 203, 185))
        d.rounded_rectangle((64, 220, 64 + int((W - 128) * (n - k) / n), 262), 21, fill=c["acc"] if left > 5 else (207, 62, 34))
        d.text((W - 64, 150), f"{int(left + 0.999):02d}", font=anton(110), fill=c["ink"], anchor="rm")
        yield im
    # 3) 答えはコメントで
    end = Image.new("RGB", (W, H), c["dark"]); d = ImageDraw.Draw(end)
    d.text((W // 2, 820), "TIME UP", font=anton(200), fill=c["acc"], anchor="mm")
    d.text((W // 2, 1040), "答えは?コメントで", font=jp(84), fill=(245, 240, 228), anchor="mm")
    d.text((W // 2, 1160), c["ans"], font=jp(84), fill=(245, 240, 228), anchor="mm")
    d.text((W // 2, 1340), "解説・全文和訳はカルーセルに", font=jp(48, 600), fill=(200, 200, 200), anchor="mm")
    for _ in range(25): yield end
def build(kind, no):
    c = dict(CFG[kind]); c.update(setup(kind, no)); out = OUT / f"{kind}_{no:03d}.mp4"; tmp = OUT / "_v.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-", "-c:v", "libx264",
                          "-pix_fmt", "yuv420p", "-r", "30", str(tmp)], stdin=subprocess.PIPE)
    total = 0
    for im in frames(kind, no): im.save(p.stdin, "PNG"); total += 1
    p.stdin.close(); p.wait(); dur = total / FPS
    tick = f"aevalsrc='0.25*sin(2*PI*1800*t)*exp(-60*mod(t,1))':d={c['sec']}:s=44100"  # 秒針のような小さな音
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp), "-stream_loop", "-1", "-i", str(bgm_path(c["bgm"])),
                    "-f", "lavfi", "-i", tick, "-filter_complex",
                    f"[1:a]volume=0.35,afade=t=out:st={dur - 1.5}:d=1.5[m];[2:a]adelay=1200|1200,volume=0.5[t];"
                    f"[m][t]amix=inputs=2:normalize=0,alimiter=limit=0.9:level=disabled[a]",
                    "-map", "0:v", "-map", "[a]", "-t", str(dur), "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", str(out)], check=True)
    tmp.unlink(); return out, c["credit"]
if __name__ == "__main__":
    print(build(sys.argv[1], int(sys.argv[2])))
