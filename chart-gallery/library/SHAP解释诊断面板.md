---
id: SHAP解释诊断面板
名称: SHAP全局—依赖—局部解释面板
说明: 将特征重要性、非线性依赖关系和单样本贡献放在同一张证据图中
数据类型: 截面分组
方法类型: 模型解释
数据契约: 样本×特征矩阵＋同形状的真实SHAP值矩阵＋基准输出；两矩阵列顺序必须一致
来源项目: 内部研究或优秀论文案例（已脱敏）
原始脚本: 本次复现重构
验证状态: 已验证
入库日期: 2026-09-05
验证日期: 2026-09-05
验证环境: matplotlib 3.8.4 / numpy 1.26.4
---

## 图表说明

左侧蜂群图展示全局贡献分布，右上展示最重要特征的依赖关系，右下展示一个样本的局部贡献。本模板只负责绘制已经由模型解释器算出的真实 SHAP 值，不能用特征相关系数或随机数替代正式分析结果；示例数据仅用于验证版式。

```python
# -*- coding: utf-8 -*-
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize

mpl.rcParams.update({"font.family":"sans-serif","font.sans-serif":["Microsoft YaHei","SimHei"],"axes.unicode_minus":False,"font.size":10.2,"axes.spines.top":False,"axes.spines.right":False,"axes.grid":True,"grid.color":"#E2E2E2","grid.linewidth":.6,"axes.axisbelow":True,"savefig.dpi":300,"savefig.bbox":"tight"})
rng=np.random.default_rng(19); n=520
names=np.array(["需求强度","服务半径","建设成本","老龄人口","交通可达性","床位密度"])
X=rng.normal(size=(n,len(names)))
S=np.c_[1.2*np.tanh(1.3*X[:,0])+.12*rng.normal(size=n),-.75*X[:,1]+.18*X[:,1]**2,.62*X[:,2],.42*X[:,3]*X[:,0],-.30*X[:,4],.18*X[:,5]]
importance=np.mean(np.abs(S),axis=0); order=np.argsort(importance); top=order[-1]

fig=plt.figure(figsize=(11.4,6.5)); gs=fig.add_gridspec(2,2,width_ratios=[1.12,1],height_ratios=[1.05,.78],wspace=.30,hspace=.42)
ax=fig.add_subplot(gs[:,0]); cmap=mpl.colors.LinearSegmentedColormap.from_list("br",["#0072B2","#F7F7F7","#D55E00"])
for yi,j in enumerate(order):
    vals=S[:,j]; bins=np.digitize(vals,np.quantile(vals,np.linspace(0,1,25))[1:-1]); jit=np.zeros(n)
    for b in np.unique(bins):
        ids=np.flatnonzero(bins==b); jit[ids]=np.linspace(-.22,.22,len(ids))[rng.permutation(len(ids))]
    color=(X[:,j]-np.percentile(X[:,j],2))/(np.percentile(X[:,j],98)-np.percentile(X[:,j],2)); color=np.clip(color,0,1)
    ax.scatter(vals,yi+jit,c=color,cmap=cmap,s=13,alpha=.72,edgecolor="none")
ax.axvline(0,color="#555555",lw=.8); ax.set_yticks(range(len(names)),names[order]); ax.set_xlabel("SHAP值（对模型输出的影响）"); ax.set_title("全局贡献蜂群图",loc="left",weight="bold")
sm=mpl.cm.ScalarMappable(norm=Normalize(0,1),cmap=cmap); cb=fig.colorbar(sm,ax=ax,fraction=.035,pad=.02); cb.set_ticks([0,1],labels=["低","高"]); cb.set_label("特征值")

ad=fig.add_subplot(gs[0,1]); inter=X[:,3]
ad.scatter(X[:,top],S[:,top],c=inter,cmap="viridis",s=18,alpha=.62,edgecolor="none"); ad.axhline(0,color="#777777",lw=.7)
ad.set_xlabel(names[top]); ad.set_ylabel("该特征的SHAP值"); ad.set_title("非线性依赖与交互",loc="left",weight="bold")

aw=fig.add_subplot(gs[1,1]); balance=np.minimum((S>0).sum(1),(S<0).sum(1)); k=np.argmax(balance*3+np.abs(S).sum(1)); contrib=S[k]; idx=np.argsort(np.abs(contrib))
vals=contrib[idx]; labs=names[idx]; colors=np.where(vals>=0,"#D55E00","#0072B2")
aw.barh(np.arange(len(idx)),vals,color=colors,alpha=.85); aw.axvline(0,color="#333333",lw=.8); aw.set_yticks(range(len(idx)),labs); aw.set_xlabel("局部贡献"); aw.set_title(f"单样本解释：基准值＋Σ贡献 = {3.8+contrib.sum():.2f}",loc="left",weight="bold")
for y,v in enumerate(vals):
    if v>=0: aw.text(v+.03,y,f"{v:+.2f}",ha="left",va="center",fontsize=9)
    else: aw.text(v+.05,y,f"{v:+.2f}",ha="left",va="center",fontsize=9,color="white" if abs(v)>.55 else "#222222")
fig.savefig("SHAP解释诊断面板.png"); plt.close(fig)
print("已输出：SHAP解释诊断面板.png")
```

