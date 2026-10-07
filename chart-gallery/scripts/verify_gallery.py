# -*- coding: utf-8 -*-
"""Execute every embedded chart template in isolation without modifying the library."""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "library"
CODE_BLOCK = re.compile(r"```python\s*\n(.*?)```", re.S)


def verify_one(note: Path) -> tuple[bool, str]:
    text = note.read_text(encoding="utf-8")
    hit = CODE_BLOCK.search(text)
    if not hit:
        return False, "missing python code block"
    with tempfile.TemporaryDirectory(prefix="chart-gallery-") as tmp:
        work = Path(tmp)
        script = work / "render.py"
        script.write_text(hit.group(1), encoding="utf-8")
        env = {**os.environ, "MPLBACKEND": "Agg", "PYTHONIOENCODING": "utf-8"}
        result = subprocess.run(
            [sys.executable, str(script)], cwd=work, env=env,
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300,
        )
        output = work / f"{note.stem}.png"
        if result.returncode != 0 or not output.exists():
            tail = (result.stderr or result.stdout or "no output").strip().splitlines()[-1:]
            return False, tail[0] if tail else "render failed"
        try:
            with Image.open(output) as image:
                image.verify()
            return True, f"{output.stat().st_size // 1024} KB"
        except Exception as exc:
            return False, f"invalid PNG: {exc}"


def main() -> int:
    notes = sorted(p for p in LIBRARY.glob("*.md") if not p.name.startswith("_"))
    failures = []
    for index, note in enumerate(notes, 1):
        ok, detail = verify_one(note)
        print(f"[{index:02d}/{len(notes):02d}] {'PASS' if ok else 'FAIL'} {note.stem}: {detail}")
        if not ok:
            failures.append((note.stem, detail))
    print(f"SUMMARY total={len(notes)} passed={len(notes) - len(failures)} failed={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
