# 60图高级图表库

`library` 中包含60个模板。每个模板由同名Markdown、PNG预览和 `_thumb.png` 缩略图组成；Markdown内含适用场景、数据契约、表达边界和完整Python代码。

源码启动：

```powershell
python -m pip install -r requirements.txt
python portable_run.py
```

全量复现测试：

```powershell
python scripts/verify_gallery.py
python portable_run.py --smoke-test
```

Windows EXE构建：

```powershell
.\build.ps1 -Python python
```

构建产物默认位于 `dist/MathModelingChartGallery.exe`。发布包中应让EXE与 `library` 文件夹保持同级。
