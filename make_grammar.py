"""英文法リールを1コマンドで:動画を作る → 日本語の読みチェック → (--plan なら)予約。
出力は要点だけ(✗ の行と長さ)。トークン節約のため、途中経過は出さない。

    python3 make_grammar.py 17 24                              # 作成+読みチェックだけ
    python3 make_grammar.py 17 24 --plan "2026-12-02 07:30"    # ✗ がなければそのまま予約まで
    python3 make_grammar.py 17 24 --plan "2026-12-02 07:30" --force   # ✗ を確認済みなら予約する
✗ が出たら:聞き取り結果を見て、本当の読み間違いなら台本(lessons_grammar/*.py)をひらがな等に直して、同じコマンドをもう一度。
(英字で書いた語 few / do / Me neither などは、聞き取りがカタカナや英字になるだけで ✗ になる。読みが合っていれば OK → --force)
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def main():
    a, b = int(sys.argv[1]), int(sys.argv[2])
    plan_at = sys.argv[sys.argv.index("--plan") + 1] if "--plan" in sys.argv else None
    force = "--force" in sys.argv
    import grammar_reel as gr
    report, bad = [], 0
    for no in range(a, b + 1):
        out = gr.OUT / f"lesson_{no:03d}.mp4"
        gr.render(0, no, out)
        r = subprocess.run([str(ROOT / ".venv-tts/bin/python"), str(ROOT / "yomi_check.py"), str(out.with_suffix(".voice.json")), "--quiet"],
                           capture_output=True, text=True).stdout
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                                   capture_output=True, text=True).stdout)
        lines = r.splitlines()
        ng = [ln for i, ln in enumerate(lines) if ln.startswith("✗")]
        bad += len(ng)
        report.append(f"No.{no} {dur:.0f}秒 ✗{len(ng)}")
        for i, ln in enumerate(lines):
            if ln.startswith("✗"):
                report += ["   " + ln] + ["   " + x for x in lines[i + 1:i + 3]]
    print("\n".join(report))
    if plan_at and (bad == 0 or force):
        subprocess.run([sys.executable, str(ROOT / "grammar_post.py"), "plan", str(a), str(b), plan_at], check=True)
        print("予約しました")
    elif plan_at:
        print(f"✗ が {bad} 件あるので予約していません(確認して直すか、問題なければ --force)")


if __name__ == "__main__":
    main()
