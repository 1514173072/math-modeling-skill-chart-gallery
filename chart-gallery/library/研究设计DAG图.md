---
id: 研究设计DAG图
名称: 研究设计 DAG+证据分层图
说明: 节点框+箭头手绘因果图，底部三层证据带（描述/观测/干预）交代"什么能识别、什么不能"，观测方向≠do 效应直接写进图
数据类型: 示意与流程
方法类型: 设计与流程
数据契约: 无数据依赖；节点(标签,坐标,颜色)与箭头(起止,虚实)手工布置；证据带文字按研究替换
来源项目: 内部研究或优秀论文案例（已脱敏）
原始脚本: '[本地路径已脱敏]'
验证状态: 已验证
验证日期: 2026-09-05
验证环境: matplotlib 3.8.4 / numpy 1.26.4
入库日期: 2026-08-28
---

## 图表说明

实证论文第一章的研究设计图：上半部是 X→M→Y 的因果图（协变量虚线指入中介），下半部三条高度递增的色带声明证据层级——描述与测量永远可得、观测动力只给方向、干预识别必须过识别门。把"因果分层的概念边界"直接画进图里，审稿人与读者都不容易越界解读。注意：节点坐标手工布置，改字后要目测有无重叠；分层带的宽度即"可识别范围"的设计表态。

```python
# -*- coding: utf-8 -*-
# 图表模板：研究设计 DAG + 证据分层图
# 数据契约：无数据依赖；节点/箭头/证据带按研究手工布置
# 协议：全中文标注；图内不加"XX图"标题；300dpi；末尾输出与笔记同名 PNG
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Source Han Sans SC", "Noto Sans CJK SC", "Microsoft YaHei", "SimHei"],
    "axes.unicode_minus": False,
    "font.size": 10.5, "axes.labelsize": 10.5,
    "xtick.labelsize": 9.5, "ytick.labelsize": 9.5, "legend.fontsize": 9.5,
    "figure.dpi": 110, "savefig.dpi": 300, "savefig.bbox": "tight",
})

# ===== 1. 绘图（无数据，纯布置） =====
fig, ax = plt.subplots(figsize=(11.4, 6.2))
ax.set_xlim(0, 11.5)
ax.set_ylim(0, 7.6)
ax.axis("off")

nodes = {
    "处理 X": (1.2, 5.9, "#dbeafe"),
    "中介 M": (1.2, 3.9, "#e0f2fe"),
    "协变量 C1": (4.1, 7.0, "#fef3c7"),
    "协变量 C2": (4.1, 5.1, "#fef3c7"),
    "观测动力 Z": (5.3, 3.9, "#dcfce7"),
    "结局 Y": (8.3, 3.9, "#fee2e2"),
    "决策 D": (10.5, 3.9, "#ede9fe"),
}

def arrow(ax, start, end, color="#415a77", style="-"):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=13,
                                 linewidth=1.5, linestyle=style, color=color,
                                 connectionstyle="arc3,rad=0.03"))

for label, (x, y, color) in nodes.items():
    ax.add_patch(FancyBboxPatch((x - 0.95, y - 0.38), 1.9, 0.76,
                                boxstyle="round,pad=0.04,rounding_size=0.08",
                                facecolor=color, edgecolor="#334155", linewidth=1.1))
    ax.text(x, y, label, ha="center", va="center", fontsize=10)

arrow(ax, (1.2, 5.5), (1.2, 4.35))                       # X → M
arrow(ax, (2.1, 3.9), (4.35, 3.9))                       # M → Z
arrow(ax, (6.25, 3.9), (7.35, 3.9))                      # Z → Y
arrow(ax, (9.25, 3.9), (9.55, 3.9))                      # Y → D
arrow(ax, (4.1, 6.6), (5.0, 4.35), color="#64748b", style="--")   # C1 ⇢ Z
arrow(ax, (4.1, 5.0), (4.8, 4.3), color="#64748b", style="--")    # C2 ⇢ Z
arrow(ax, (5.3, 3.5), (8.1, 3.5), color="#0f766e", style="--")    # 观测方向旁路
ax.text(6.7, 2.95, "观测因果发现：只识别方向", color="#0f766e", ha="center", fontsize=8.5)

bands = [
    (0.20, 2.75, "描述与测量", "样本、测量、编码", "#dbeafe"),
    (3.10, 2.75, "观测动力", "CCM/RCM、敏感性", "#ccfbf1"),
    (6.00, 2.75, "干预识别", "目标试验 + 效应估计（门通过后）", "#fee2e2"),
]
for x, width, label, detail, color in bands:
    ax.add_patch(FancyBboxPatch((x, 0.35), width - 0.08, 0.82,
                                boxstyle="round,pad=0.02,rounding_size=0.04",
                                facecolor=color, edgecolor="white"))
    ax.text(x + (width - 0.08) / 2, 0.84, label, ha="center", va="center", fontsize=9)
    ax.text(x + (width - 0.08) / 2, 0.56, detail, ha="center", va="center",
            fontsize=7.7, color="#475569")
ax.text(10.15, 0.78, "观测方向 ≠ do 效应", fontsize=9, color="#991b1b", ha="center")
ax.text(10.15, 0.48, "干预层结论以识别门为前提", fontsize=8, color="#991b1b", ha="center")

# ===== 2. 输出（文件名必须与笔记同名） =====
fig.savefig("研究设计DAG图.png")
plt.close(fig)
print("已输出：研究设计DAG图.png")
```
