"""やさしい英文法のレッスン一覧。中身は lessons_grammar/*.py(1ファイル=1〜2週間分)に分けてある。
新しいレッスンは、新しいファイル(例:lessons_grammar/week02.py に LESSONS = [dict(no=17, ...), ...])を作って足す。
既存のファイルを全部読まなくてよいように、書き方は lessons_grammar/week01.py の最後の1件だけ見れば十分。
"""
import importlib.util
from pathlib import Path

LESSONS = []
for f in sorted((Path(__file__).parent / "lessons_grammar").glob("*.py")):
    spec = importlib.util.spec_from_file_location(f.stem, f)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    LESSONS += m.LESSONS
LESSONS.sort(key=lambda L: L["no"])
