---
id: PCA双标图
名称: PCA 得分—载荷双标图
说明: 同时展示样本在主成分空间中的分组结构和原始变量的方向贡献
数据类型: 截面分组
方法类型: 多元统计
数据契约: 行为样本、列为连续指标的数值矩阵，可附分组标签；进入 PCA 前必须说明标准化、缺失处理和变量方向
来源项目: 内部研究或优秀论文案例（已脱敏）
原始脚本: 本次复现重构
验证状态: 已验证
验证日期: 2026-09-05
验证环境: matplotlib 3.8.4 / numpy 1.26.4
入库日期: 2026-09-05
---

## 图表说明

点表示样本得分，箭头表示变量载荷方向；夹角近似反映变量相关方向，箭头长度只在当前缩放规则下比较。图中明确给出 PC1、PC2 的解释方差比例；若前两维解释率过低，双标图只能作为局部投影，不能概括全部结构。

```python
# -*- coding: utf-8 -*-
# 数据契约：样本×连续指标矩阵 + 可选分组标签
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Ellipse
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

mpl.rcParams.update({"font.family":"sans-serif","font.sans-serif":["Microsoft YaHei","SimHei"],"axes.unicode_minus":False,"font.size":10.5,"axes.spines.top":False,"axes.spines.right":False,"axes.grid":True,"grid.color":"#D9D9D9","savefig.dpi":300,"savefig.bbox":"tight","legend.frameon":False})
OI=["#0072B2","#E69F00","#009E73","#D55E00","#CC79A7","#56B4E9","#F0E442","#999999"]
rng=np.random.default_rng(4); names=["效率","稳定性","舒适度","成本","响应速度"]
groups=np.repeat(["方案甲","方案乙","方案丙"],35)
means=np.array([[1.2,.8,.4,-.7,1.0],[-.4,.9,1.1,.3,-.2],[.2,-.8,-.4,1.0,.5]])
X=np.vstack([rng.normal(means[i],.65,(35,len(names))) for i in range(3)])
pca=PCA(n_components=2); scores=pca.fit_transform(StandardScaler().fit_transform(X)); load=pca.components_.T

fig,ax=plt.subplots(figsize=(7.8,5.8))
for label,color in zip(np.unique(groups),OI):
    pts=scores[groups==label]; ax.scatter(pts[:,0],pts[:,1],s=24,alpha=.68,color=color,label=label)
    cov=np.cov(pts.T); vals,vecs=np.linalg.eigh(cov); order=vals.argsort()[::-1]; vals,vecs=vals[order],vecs[:,order]
    angle=np.degrees(np.arctan2(vecs[1,0],vecs[0,0])); width,height=2*1.6*np.sqrt(vals)
    ax.add_patch(Ellipse(pts.mean(0),width,height,angle=angle,facecolor="none",edgecolor=color,lw=1.3,alpha=.8))
scale=min(np.ptp(scores[:,0]),np.ptp(scores[:,1]))*.42
for (lx,ly),name in zip(load,names):
    ax.arrow(0,0,lx*scale,ly*scale,color="#333333",width=.008,head_width=.09,length_includes_head=True)
    ax.text(lx*scale*1.12,ly*scale*1.12,name,ha="center",va="center",fontsize=9)
ax.axhline(0,color="#888888",lw=.7); ax.axvline(0,color="#888888",lw=.7)
ax.set_xlabel(f"PC1（{pca.explained_variance_ratio_[0]:.1%}）"); ax.set_ylabel(f"PC2（{pca.explained_variance_ratio_[1]:.1%}）"); ax.legend()
fig.savefig("PCA双标图.png"); plt.close(fig)
print("已输出：PCA双标图.png")
```
