---
id: Pareto权衡前沿
名称: Pareto 权衡前沿与折中方案
说明: 同时展示双目标可行解、非支配前沿和经明确规则选择的折中方案
数据类型: 截面分组
方法类型: 优化与决策
数据契约: 每行一个可行方案，至少含两个同向最小化目标；可附方案编号，折中点必须由预先声明的规则计算
来源项目: 内部研究或优秀论文案例（已脱敏）
原始脚本: 本次复现重构
验证状态: 已验证
验证日期: 2026-09-05
验证环境: matplotlib 3.8.4 / numpy 1.26.4
入库日期: 2026-09-05
---

## 图表说明

灰点是全部可行解，蓝线是非支配前沿，橙色菱形是按“到理想点的标准化距离最小”选出的折中方案。必须说明目标方向和折中规则；若目标超过两个，应改用平行坐标或分面对照，不能只投影后声称获得完整 Pareto 关系。

```python
# -*- coding: utf-8 -*-
# 数据契约：方案×两个同向最小化目标；折中点由显式规则计算
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

mpl.rcParams.update({"font.family":"sans-serif","font.sans-serif":["Microsoft YaHei","SimHei"],"axes.unicode_minus":False,"font.size":10.5,"axes.spines.top":False,"axes.spines.right":False,"axes.grid":True,"grid.color":"#D9D9D9","savefig.dpi":300,"savefig.bbox":"tight","legend.frameon":False})
OI=["#0072B2","#E69F00","#009E73","#D55E00","#CC79A7","#56B4E9","#F0E442","#999999"]
rng=np.random.default_rng(12)
x=np.linspace(18,92,110)
y=118-0.82*x+0.0055*(x-55)**2+rng.normal(0,5.2,len(x))
y=np.clip(y,20,None)

# 非支配判定：两个目标均越小越好
order=np.argsort(x); best=np.inf; front=[]
for i in order:
    if y[i] < best:
        front.append(i); best=y[i]
front=np.array(front)
fx,fy=x[front],y[front]
zx=(fx-fx.min())/(fx.max()-fx.min()); zy=(fy-fy.min())/(fy.max()-fy.min())
k=np.argmin(np.hypot(zx,zy)); chosen=front[k]

fig,ax=plt.subplots(figsize=(7.4,5.2))
ax.scatter(x,y,s=22,color="#B7BEC6",alpha=.65,label="可行方案")
ax.plot(fx,fy,color=OI[0],lw=2.2,marker="o",ms=3.5,label="Pareto 前沿")
ax.scatter(x[chosen],y[chosen],s=95,marker="D",color=OI[1],edgecolor="white",lw=1.2,zorder=5,label="折中方案")
ax.annotate(f"方案 {chosen+1}\n({x[chosen]:.1f}, {y[chosen]:.1f})",(x[chosen],y[chosen]),xytext=(18,18),textcoords="offset points",arrowprops={"arrowstyle":"->","color":OI[1]},color="#7A4B00")
ax.set_xlabel("成本目标（越低越好）"); ax.set_ylabel("风险目标（越低越好）")
ax.legend(loc="upper right")
fig.savefig("Pareto权衡前沿.png"); plt.close(fig)
print("已输出：Pareto权衡前沿.png")
```
