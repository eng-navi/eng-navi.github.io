"""@seidoku.lab のリールを1コマンドで:動画を作る → 日本語の読みチェック。出力は要点だけ(トークン節約)。

    python3 make_seidoku.py 1 3     # No.1〜3 を作ってチェック
⚠ = 読み間違えやすい漢字が台本に残っている(grammar_reel.py の YOMI でひらがなに)
✗ = 聞き取りと台本がずれた(英字の聞き取りだけのずれは自動で OK にする)
一度 ✓ になった音声は cache/yomi_ok.json に覚えるので、作り直しても新しい声だけ調べる。
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def main():
    a, b = int(sys.argv[1]), int(sys.argv[2] if len(sys.argv) > 2 else sys.argv[1])
    import seidoku_reel as sr
    for no in range(a, b + 1):
        out, _ = sr.render(no)
        r = subprocess.run([str(ROOT / ".venv-tts/bin/python"), str(ROOT / "yomi_check.py"), str(out.with_suffix(".voice.json")), "--quiet"],
                           capture_output=True, text=True).stdout.strip()
        print(f"No.{no}: {r}")


if __name__ == "__main__":
    main()
