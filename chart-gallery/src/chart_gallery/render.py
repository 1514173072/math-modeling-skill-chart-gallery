# -*- coding: utf-8 -*-
"""重渲染：把条目代码写到库目录临时脚本，用配置的解释器现场跑，刷新同名 PNG。"""
import subprocess
import time
from pathlib import Path

import os


def render_entry(entry, lib_dir: str, python_exe: str, timeout: int = 300):
    """返回 (ok, message)。成功时同名 PNG 已刷新。"""
    lib = Path(lib_dir)
    png = Path(entry.png)
    if png.exists():
        png.unlink()
    script = lib / f"_render_{entry.stem}.py"
    script.write_text(entry.code, encoding="utf-8")
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "MPLBACKEND": "Agg"}
    t0 = time.time()
    try:
        r = subprocess.run([python_exe, script.name], cwd=lib, capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, env=env)
        if r.returncode == 0 and png.exists():
            return True, f"渲染成功（{time.time() - t0:.1f}s）"
        tail = [ln for ln in (r.stderr or "").strip().splitlines() if ln.strip()][-5:]
        return False, "\n".join(tail) or f"returncode={r.returncode}"
    except subprocess.TimeoutExpired:
        return False, f"超时（>{timeout}s）"
    finally:
        script.unlink(missing_ok=True)
