---
title: "张雪机车为什么能“水上漂”：从初中浮力到滑行水动力学"
date: 2026-10-25 18:00:00 +0800
lang: zh-CN
categories:
- 物理学
tags:
- 流体力学
- 阿基米德原理
- 滑行升力
- 升力系数
- CFD
excerpt: "几块小板怎样托住摩托车与骑手？从液体压强、牛顿定律推导到压力积分、Navier–Stokes 方程，再讨论升力系数的测量、Savitsky 方法和自由液面 CFD 的验证。"
aside: true
aside_align: right
share: false
---

一辆摩托车加上几块窄板，就能在水面上持续行驶。最自然的疑问是：**这么小的板，能排开多少水，为什么托得住整车和骑手？如果仍然是浮力，为什么又一定要跑起来？**

2026 年 10 月 25 日，张雪在湖南麻阳驾驶改装 MX450 完成 40.74 公里的水上行驶。新华社报道确认，车辆加装了两栖滑行橇套件，入水后由前转向橇辅助转向，后轮深齿胎局部浸水并向后拨水，持续提供推力。[^xinhua] 这件事适合用来分清两个问题：静止时的阿基米德浮力，以及运动时的水动力升力。

本文先从初中的压强和受力分析开始，再逐步引入积分、流体运动方程和实验标定。**下文的质量、板面积、迎角和升力系数，凡标为“示例”的都只是教学假设，不是这辆改装车的公开实测参数；文献中的 CFD 数据也会与本文的算例明确分开。**

<!-- more -->

![张雪机车水面滑行分析：重力经过质心，前后滑行板的水动力升力经过各自压力中心，后轮拨水产生推力。](/assets/images/water-motorcycle/zhang-xue-planing-analysis.png)

*图 1：保留原讨论的机车原理图，采用后来补上质心与压力中心标注的版本，由作者提供。图为 ChatGPT 生成的概念示意，不是车辆设计图或计算得到的流线图。速度箭头表示运动方向；推力、阻力的具体作用线，以及各受力中心的数值位置，仍需测量。小图中的水流弯曲仅表达向下偏转的机制。*

## 一、先从初中知识出发：静水为什么会把物体往上推？

### 1. 液体越深，压强越大

取一根截面积为 $A$、高度为 $h$ 的静止水柱。上表面受到大气压 $p_{\rm atm}$，下表面受到水的压强 $p$。竖直受力平衡给出

<div class="post-math-display">
\[
pA-p_{\rm atm}A-\rho Ahg=0,
\qquad p-p_{\rm atm}=\rho gh.
\]
</div>

这里 $\rho$ 是水的密度，$g$ 是重力加速度。压强的单位是帕斯卡，$1\,\mathrm{Pa}=1\,\mathrm{N/m^2}$；由压强算力，需要再乘面积。

再把一个底面积为 $A$、厚度为 $H$ 的长方体完全浸没。它底面比顶面深 $H$，所以底面向上的压力比顶面向下的压力大

<div class="post-math-display">
\[
B=(p_{\rm bottom}-p_{\rm top})A
 =\rho gHA=\rho gV_{\rm disp}.
\]
</div>

这就是阿基米德浮力。水平侧面的压力互相抵消，留下一个向上的合力。对部分浸没、任意形状的物体，结论仍然成立；后面会给出一般证明。[^archimedes]

**静水浮力取决于排水体积，而不由板面积单独决定。** 面积很大但很薄的实心板，完全浸水时也未必能排开多少水；有密闭空腔的船体则可以用较小的材料质量排开很大的体积。

### 2. 用一个数量级判断，排除“几块薄板就能静浮”的解释

假设整车、骑手和装备的总质量为 $m=180\,\mathrm{kg}$。如果完全靠静水浮力承重，需要

<div class="post-math-display">
\[
V_{\rm disp}=\frac{mg}{\rho g}
=\frac{180}{1000}\,\mathrm{m^3}
=0.18\,\mathrm{m^3}=180\,\mathrm{L}.
\]
</div>

作为对照，假设几块**实心**板的总面积为 $0.10\,\mathrm{m^2}$、厚度为 $1\,\mathrm{cm}$，板自身的体积只有 $1\,\mathrm{L}$。即使全部浸没，水给板的浮力也只有约 $9.81\,\mathrm{N}$，相当于承托 $1\,\mathrm{kg}$ 的质量，而且还没有扣除板自身的重量。

这不是对实际改装件尺寸的测量，却说明了正确的判断方法：**若实际排水体积远小于所需体积，静水浮力便不足以解释承重，必须计算运动造成的额外作用力。**

## 二、运动以后发生了什么：板不断把水向下加速

先不使用流体力学公式。想象把手伸进相对运动的水中，手掌略微抬起前缘，水会推着手掌向上。滑行板也是如此：板迫使一部分水改变运动方向，水获得向下的动量，板获得向上的反作用力。

在随匀速直线运动的板一起移动的参考系中，来水速度记为 $U$。若把复杂流动简化成一股水，质量流率为 $\dot m$，竖直流速从接近零变为 $-w$，则在**稳态、控制面压强与重力等贡献可以忽略或已扣除参考值**的近似下，动量定理给出

<div class="post-math-display">
\[
F_{\mathrm{plate}\to\mathrm{water},z}
\simeq \dot m(-w-0),
\qquad L_{\rm dyn}\simeq\dot m w.
\]
</div>

这不是“水撞上板的一瞬间”才能产生的冲击。只要新的水不断流过，向下的动量输运便能持续发生。若有效流束截面积为 $A_c$，则 $\dot m\sim\rho U A_c$；若偏转角较小且基本不变，则 $w\sim U\theta$，于是

<div class="post-math-display">
\[
L_{\rm dyn}\sim\rho U^2A_c\theta.
\]
</div>

这已经解释了速度平方的来源：速度增加，一方面单位时间参与作用的水更多，另一方面每单位质量的水获得的竖直速度也更大。

不过，$A_c$ 不是直接可见的板面积，$\theta$ 也不是处处相同的出水角。真实流动还包括侧向泄流、喷溅、波浪和空气进入板底。这个模型解释机制，却还不能给出准确的升力系数。[^faltinsen]

### 小板为什么也可能产生很大的力？

动压的定义是

<div class="post-math-display">
\[
q\equiv\frac12\rho U^2.
\]
</div>

在淡水中取 $U=70\,\mathrm{km/h}=19.44\,\mathrm{m/s}$，有 $q\simeq1.89\times10^5\,\mathrm{Pa}$。相比之下，深度 $h=2\,\mathrm{cm}$ 对应的静水表压只有 $\rho gh\simeq196\,\mathrm{Pa}$。两种**压强尺度**相差约 964 倍。

这不表示板底处处承受 964 倍静水压。实际压力分布还要由板形和流场决定。但它说明：高速水流的惯性可以建立远大于浅浸水静压的压力尺度，因此不必用很大的排水体积来承重。

## 三、先做一个可复算的机车算例

将运动造成的额外竖直水动力记为 $L_{\rm dyn}$，并**选定参考面积** $S_{\rm ref}$，定义

<div class="post-math-display">
\[
C_{L,\rm dyn}\equiv\frac{L_{\rm dyn}}{qS_{\rm ref}},
\qquad L_{\rm dyn}=\frac12\rho U^2S_{\rm ref}C_{L,\rm dyn}.
\]
</div>

这种写法本身是系数的定义；预测能力来自我们如何获得 $C_L$。NASA 对升力系数也采用相同的动压归一化定义。[^nasa-cl]

沿用前面的 $m=180\,\mathrm{kg}$，另假设 $S_{\rm ref}=0.10\,\mathrm{m^2}$、$C_{L,\rm dyn}=0.10$，暂时忽略静水贡献。则在 $70\,\mathrm{km/h}$ 时，

<div class="post-math-display">
\[
L_{\rm dyn}\simeq1890\,\mathrm{N},
\qquad mg\simeq1766\,\mathrm{N}.
\]
</div>

在这组假设下，面积虽小，升力数量级仍足以承重。固定同一面积和系数，$40$、$60$、$80\,\mathrm{km/h}$ 对应的升力分别约为 $617$、$1389$、$2469\,\mathrm{N}$。解出平衡速度可得

<div class="post-math-display">
\[
U_{\rm balance}
=\sqrt{\frac{2mg}{\rho S_{\rm ref}C_{L,\rm dyn}}}
\simeq67.7\,\mathrm{km/h}.
\]
</div>

**这个 $67.7\,\mathrm{km/h}$ 是假设模型的平衡速度，不是张雪机车的实测最低滑行速度。** 实车的湿面积、姿态、轮胎受力和 $C_L$ 都会变化。当速度从 $70$ 降到 $50\,\mathrm{km/h}$ 时，固定状态模型的升力变成原来的 $(50/70)^2\simeq0.51$；真实车辆可能通过更深浸水获得部分补偿，同时承担更大的阻力和姿态变化。

参考面积也不能混用。可以选固定的板平面面积，也可以选瞬时湿面积，但必须同时报告选择方式。同一升力用不同面积归一化，会得到不同的 $C_L$；这不代表物理作用力发生了变化。

## 四、刚体受力：为什么不能把所有力都画到质心？

![刚体受力修正图：静水浮力通过浮心，重力通过质心；滑行板的压力中心可以与质心错开。](/assets/images/water-motorcycle/rigid-body-buoyancy.svg)

*图 2：保留原对话中的刚体浮力分析修正图。左图取对称、直立的均匀浮体，质心 $G$ 与浮心 $C_B$ 的竖直作用线重合；右图说明升力作用线与质心错开时会产生力矩。右图仅画重力与升力，并未画出使整车达到完整平衡所需的其他力和力矩。*

初中把物体看成质点时，只需关心合力。把摩托车视为刚体，则还必须关心它会不会抬头、低头或侧翻：

<div class="post-math-display">
\[
m\ddot{\boldsymbol r}_G=\sum_i\boldsymbol F_i,
\qquad
\frac{d\boldsymbol H_G}{dt}
=\sum_i(\boldsymbol r_i-\boldsymbol r_G)\times\boldsymbol F_i.
\]
</div>

$\boldsymbol H_G$ 是关于质心的角动量，第二式的导数在惯性坐标系中计算。重力的合力作用线经过质心；均匀密度静水中的浮力作用线经过**排水体积的形心**，即浮心；运动压力形成的合力则要根据分布求出作用线。对于平面问题、只合并竖直压力分量的近似，压力中心的纵向位置满足

<div class="post-math-display">
\[
x_{C_P}=\frac{\int x\,dF_z}{\int dF_z},
\qquad L=\int dF_z.
\]
</div>

令 $x$ 向车头方向为正，并规定抬头力矩为正，该升力的俯仰力矩就是 $(x_{C_P}-x_G)L$。如果把这个力平移到质心，却不补上相应的力偶矩，便改变了刚体的转动问题。一般三维分布载荷更应保留完整的合力与合力矩，不能只用一个压力中心代替全部信息。

例如前板在质心前方 $a$，后板在后方 $b$。忽略其他竖直受力及推力、阻力的俯仰力矩，稳态要求

<div class="post-math-display">
\[
L_f+L_r=mg,
\qquad aL_f-bL_r=0,
\]
\[
L_f=\frac{b}{a+b}mg,
\qquad L_r=\frac{a}{a+b}mg.
\]
</div>

所以总升力够大只是第一步，前后如何分配同样重要。实际车辆还要把轮胎的水动力、推力高度、阻力高度以及骑手移动造成的质心变化纳入力矩平衡。

## 五、进到大学层次：两类承托力来自同一个表面应力积分

### 1. 从“压强乘面积”推广到任意曲面

把表面切成许多很小的面片，每片的压强力都沿局部法线。以 $\boldsymbol n$ 表示从物体指向外侧流体的单位法向量，用表压 $p_g=p-p_{\rm atm}$，水作用于物体的合力为

<div class="post-math-display">
\[
\boldsymbol F_{\rm water}
=\int_{S_w}\left[-p_g\boldsymbol n
+\boldsymbol\tau\boldsymbol n\right]dA.
\]
</div>

$S_w$ 是实际湿表面，$\boldsymbol\tau$ 是黏性应力张量。这里忽略空气相对大气压的扰动和表面张力的接触线作用；若研究它们，再将相应项加入。式中压力和黏性应力都具有“单位面积上的力”的量纲。所谓静水浮力与滑行升力，区别在于**表面上的压力和应力场如何形成**。

### 2. 阿基米德原理的一般证明

取 $z$ 向上，静水面为 $z=0$。均匀静水满足

<div class="post-math-display">
\[
\nabla p_g=-\rho g\hat{\boldsymbol z}.
\]
</div>

对排水体积 $V_{\rm disp}$ 应用散度定理：

<div class="post-math-display">
\[
\begin{aligned}
\boldsymbol B
&=-\oint_{\partial V_{\rm disp}}p_g\boldsymbol n\,dA\\
&=-\int_{V_{\rm disp}}\nabla p_g\,dV\\
&=\rho gV_{\rm disp}\hat{\boldsymbol z}.
\end{aligned}
\]
</div>

对部分浸没物体，用位于静水面上的虚拟平面封闭湿表面；该平面上 $p_g=0$，所以不会增加表压合力。这说明为什么任意静浮形状都得到同一个公式。把相同推导用于力矩，也得到

<div class="post-math-display">
\[
\boldsymbol M_G^{\rm hydrostatic}
=(\boldsymbol r_{C_B}-\boldsymbol r_G)
\times\rho gV_{\rm disp}\hat{\boldsymbol z}.
\]
</div>

阿基米德公式因此是**均匀密度、均匀重力、静水等假设下的力学结果**，无需为每一种外形重新拟合一个浮力系数。[^archimedes]

## 六、从牛顿定律推到流体运动方程，再看速度平方

### 1. 水的一小块也服从牛顿第二定律

取体积 $dV$ 的流体微元。压力在相对的两个面上略有不同，其合力为 $-\nabla p\,dV$；黏性应力的合力为 $(\nabla\cdot\boldsymbol\tau)dV$，再加重力。对质量为 $\rho dV$ 的微元写牛顿定律、除以 $dV$，得到

<div class="post-math-display">
\[
\rho\frac{D\boldsymbol u}{Dt}
=-\nabla p+\nabla\cdot\boldsymbol\tau
-\rho g\hat{\boldsymbol z},
\]
\[
\frac{D\boldsymbol u}{Dt}
=\frac{\partial\boldsymbol u}{\partial t}
+(\boldsymbol u\cdot\nabla)\boldsymbol u.
\]
</div>

第二式叫随体导数：一滴水的速度变化，既可能来自原地流场随时间变化，也可能来自它流入了速度不同的位置。对不可压缩、黏度 $\mu$ 恒定的牛顿流体，采用本构关系 $\boldsymbol\tau=\mu[\nabla\boldsymbol u+(\nabla\boldsymbol u)^{\mathsf T}]$，再结合质量守恒，就得到水相内部的 Navier–Stokes 方程：

<div class="post-math-display">
\[
\begin{aligned}
\rho\left[\partial_t\boldsymbol u
+(\boldsymbol u\cdot\nabla)\boldsymbol u\right]
&=-\nabla p+\mu\nabla^2\boldsymbol u
-\rho g\hat{\boldsymbol z},\\
\nabla\cdot\boldsymbol u&=0.
\end{aligned}
\]
</div>

这个推导由动量守恒和本构假设组成；它并不意味着水在任意温度、压力、尺度下都能不加条件地视为不可压缩牛顿流体。对这里的宏观滑行问题，这是一种常见的起点。[^mit-ns]

### 2. 伯努利公式能解释压强尺度，却不能单独解出滑行板受力

若进一步假设稳态、无黏，并沿同一流线积分，欧拉方程的切向分量为

<div class="post-math-display">
\[
\rho u\frac{du}{ds}
=-\frac{dp}{ds}-\rho g\frac{dz}{ds}.
\]
\[
p+\frac12\rho u^2+\rho gz=\text{同一流线上的常数}.
\]
</div>

这便是伯努利方程，也可由流体的机械能守恒得到。若一条流线来自远处平水面附近，那里 $p=p_{\rm atm}$、$u=U$、$z=0$，则

<div class="post-math-display">
\[
p-p_{\rm atm}=-\rho gz
+\frac12\rho U^2\left(1-\frac{u^2}{U^2}\right).
\]
</div>

第一项是静水形式，第二项体现流动速度改变对应的压力变化。在相同高度的理想停滞点，速度降到零，压强增量恰为 $q$。这解释了 $\tfrac12\rho U^2$ 作为压强尺度的自然性。[^bernoulli]

但板底流速 $u$ 仍然未知，流线来自哪里也要判断；喷溅、分离和黏性区还会限制伯努利近似。**不能把“流速大压强小”一句话套到整块板上，更不能假定板底压强处处等于动压。** 升力来自满足边界条件的完整压力分布。

要闭合这个问题，还需给出远处来流、板面的无穿透条件，以及黏性模型中的无滑移条件。自由液面的位置本身也未知。若用 $z=\eta(x,y,t)$ 表示局部可写成单值函数的水面，因为水面上的流体质点应始终留在水面上，便有

<div class="post-math-display">
\[
\frac{D}{Dt}[z-\eta(x,y,t)]=0
\quad\Longrightarrow\quad
\partial_t\eta+u\partial_x\eta+v\partial_y\eta=w.
\]
</div>

这里 $(u,v,w)$ 是水面处的速度分量。再忽略空气应力、表面张力及水的黏性法向应力，自由液面上还满足 $p=p_{\rm atm}$。这两条分别是运动学与动力学边界条件。板底流场、水面形状和实际湿区需要一起求出；出现翻卷、破碎时，单值的 $\eta$ 描述不再够用，这也是后面采用 VOF 的原因。

### 3. 无量纲化说明：系数为什么不能随便取一个常数

以板长 $\ell$ 为长度尺度、$U$ 为速度尺度、$\ell/U$ 为时间尺度、$\rho U^2$ 为压强尺度，无量纲方程为

<div class="post-math-display">
\[
\partial_{t^*}\boldsymbol u^*
+(\boldsymbol u^*\cdot\nabla^*)\boldsymbol u^*
=-\nabla^*p^*
+\frac{1}{Re}\nabla^{*2}\boldsymbol u^*
-\frac{1}{Fr^2}\hat{\boldsymbol z},
\]
\[
Re=\frac{\rho U\ell}{\mu},
\qquad Fr=\frac{U}{\sqrt{g\ell}}.
\]
</div>

$Re$ 比较惯性和黏性效应，$Fr$ 比较惯性和重力效应。对于自由液面，还需要表面张力对应的 $We=\rho U^2\ell/\sigma$、几何比例、浸水状态、迎角及空气进入板底的情况。因此更完整的关系是

<div class="post-math-display">
\[
C_L=f\!\left(\alpha,Re,Fr,We,
\text{几何比例},\text{浸水状态},\ldots\right).
\]
</div>

惯性项的量级为 $\rho U^2/\ell$，压强梯度的量级为 $\Delta p/\ell$，所以惯性主导时有 $\Delta p\sim\rho U^2$，积分后得到 $L\sim\rho U^2S$。这给出尺度关系；只有当几何、姿态和相关无量纲参数使 $C_L$ 变化较小时，才近似有 $L\propto U^2$。

## 七、静浮力与“动浮力”究竟怎样放进同一条公式？

日常所说的“动浮力”，在这里更准确的名称是**滑行水动力升力**。静水浮力由重力建立的压力梯度产生；滑行升力由流动惯性、几何和自由液面共同决定。它们都由第五节的表面应力积分计算。[^faltinsen]

一种常见写法是 $F_z=B+L_{\rm dyn}$，但必须先说明如何划分。真实水面会隆起、下凹，实际湿表面也会变化，不能把任何“眼睛看到的浸水体积”都直接代入 $\rho gV$，再把全部 CFD 升力加上去。

为使分解明确，可以冻结物体的瞬时姿态，用**远处未扰动的平水面** $z=0$ 建立静水参考。在整个封闭物体表面 $S$ 上定义参考表压

<div class="post-math-display">
\[
p_{h,0}=\rho g\max(-z,0).
\]
</div>

设 $V_0$ 是物体位于该参考平面以下的体积，则同样由散度定理有

<div class="post-math-display">
\[
B_0=-\oint_S p_{h,0}n_z\,dA=\rho gV_0.
\]
</div>

把干燥表面上的实际表压和水的黏性应力延拓为零，并令 $p'=p_g-p_{h,0}$，就得到在上述忽略空气扰动等假设下的恒等分解：

<div class="post-math-display">
\[
\begin{aligned}
F_{\mathrm{water},z}&=B_0+L_{\rm dyn},\\
L_{\rm dyn}&=-\oint_S p'n_z\,dA
+\int_{S_w}(\boldsymbol\tau\boldsymbol n)_z\,dA.
\end{aligned}
\]
</div>

这里 $L_{\rm dyn}$ 包括相对参考静水状态的压力变化和竖直黏性贡献；参考平面以下但实际已经露出水面的区域，也会通过 $p'$ 计入修正。因此这是一个明确的记账方式，不是在假定真实自由液面仍然平坦。

若以此定义 $C_{L,\rm dyn}$，竖直运动方程写成

<div class="post-math-display">
\[
m\ddot z_G=B_0+qS_{\rm ref}C_{L,\rm dyn}-mg.
\]
</div>

如果另一个软件或文献定义 $C_{L,\rm total}=F_{\mathrm{water},z}/(qS_{\rm ref})$，它已经包含静水贡献，就不应再加 $B_0$。在 $U\to0$ 时，也不能把一个固定的高速 $C_L$ 外推到底；总升力系数的分母趋于零，有非零浮力时它甚至会发散，而实际浮力完全可以保持有限。

## 八、怎样测量 $C_L$：先明确测的力，再做归一化

### 1. 水槽中的固定姿态试验

把已知几何的滑行板安装到多分量测力装置上，由拖车牵引，或者在循环水槽中让水以给定速度流过。先固定板的迎角、离参考水面的高度和横滚角，逐个改变速度；同时记录竖直力、阻力、俯仰力矩和湿区照片。高速船模试验对安装、标定、航行姿态和湿面积的处理，可参考 ITTC 的专门程序。[^ittc]

测力装置的原始读数包含安装件受力及板重的影响，符号也取决于传感器方向。应先标定、去皮并校正支架作用，得到**水对板向上的作用力** $F_z$，再计算

<div class="post-math-display">
\[
C_{L,\rm total}=\frac{F_z}{qS_{\rm ref}},
\qquad
C_{L,\rm dyn}=\frac{F_z-B_0}{qS_{\rm ref}}.
\]
</div>

只有在姿态与浸水条件保持可比时，才适合用多组 $F_z$ 对 $q$ 的数据拟合一个近似系数。若让板自由升沉和俯仰，每次改变速度后状态都会改变；这时应报告 $C_L(U)$ 连同对应姿态，而不是把所有数据强行拟合成同一条直线。

### 2. 一个教学用标定例子

假设某固定姿态试验在 $U=20.0\,\mathrm{m/s}$、$\rho=1000\,\mathrm{kg/m^3}$ 时，校正后的读数为 $F_z=1900\,\mathrm N$，参考静水浮力为 $B_0=20\,\mathrm N$，固定参考面积为 $0.100\,\mathrm{m^2}$。则

<div class="post-math-display">
\[
C_{L,\rm dyn}
=\frac{1900-20}{\tfrac12\times1000\times20.0^2\times0.100}
=0.0940.
\]
</div>

这些是**演示数据，并非真实试验记录**。若各输入独立，标准不确定度分别取 $u(F_z)=30\,\mathrm N$、$u(B_0)=5\,\mathrm N$、$u(\rho)=2\,\mathrm{kg/m^3}$、$u(U)=0.2\,\mathrm{m/s}$、$u(S)=0.002\,\mathrm{m^2}$，则对 $L=F_z-B_0$ 的一阶误差传播给出

<div class="post-math-display">
\[
\left(\frac{u(C_L)}{C_L}\right)^2
\simeq
\frac{u(F_z)^2+u(B_0)^2}{L^2}
+\left(\frac{u(\rho)}{\rho}\right)^2
+4\left(\frac{u(U)}{U}\right)^2
+\left(\frac{u(S)}{S}\right)^2.
\]
</div>

结果约为 $C_{L,\rm dyn}=0.0940\pm0.0031$，这里的“$\pm$”是标准不确定度，不是自动等于 95% 置信区间。这也显示了为什么速度误差会被平方关系放大，以及为什么用照片估计不断变化的湿面积可能成为主要误差来源。

### 3. 用整车行驶数据反推时，需要注意什么？

若车辆稳定直行、平均竖直加速度接近零，而且其他竖直外力可以忽略，便可由 $F_{\mathrm{water},z}\simeq mg$ 反推整车的有效总系数。但其中包含前后板、轮胎及其他浸水件的共同作用，不能据此得到某一块板的独立系数。

缩尺试验也有边界。若原型与模型的长度比为 $\lambda_s$，匹配重力自由液面的 Froude 数要求 $U_{\rm prototype}/U_{\rm model}=\sqrt{\lambda_s}$；同一种水中的 Reynolds 数却相差 $\lambda_s^{3/2}$。通常无法仅靠调整速度同时匹配两者，需另外评估摩擦、转捩、喷溅和通气的尺度效应。[^ittc]

## 九、经验公式的真实案例：Savitsky 方法怎么用？

对于简单的棱柱形滑行船体，未必一开始就需要完整 CFD。Savitsky 的经典论文把模型试验与力学分析结合，给出升力、湿长度、阻力、压力中心和纵向跳跃失稳的估算方法。它是**有适用范围的半经验模型**。[^savitsky]

以论文中零底升角的平底滑行面为例，式 (15) 为

<div class="post-math-display">
\[
C_{L0}=\tau^{1.1}
\left(0.0120\lambda^{1/2}
+\frac{0.0055\lambda^{5/2}}{C_V^2}\right),
\]
\[
C_V=\frac{U}{\sqrt{gb}},
\qquad \lambda=\frac{L_m}{b},
\qquad C_{L0}=\frac{L_{\rm total}}{\tfrac12\rho U^2b^2}.
\]
</div>

$b$ 为板宽，$L_m$ 为平均湿长度，$\tau$ 为纵倾角；**式中 $\tau$ 代入以度为单位的数值**。该式给出的范围为 $0.60\leq C_V\leq13.00$、$2^\circ\leq\tau\leq15^\circ$、$\lambda\leq4$。这是一条拟合关系，数值常数和角度单位不可任意更换。[^savitsky]

取教学参数 $b=0.25\,\mathrm m$、$\lambda=2$、$\tau=5^\circ$、$C_V=5$，得到

<div class="post-math-display">
\[
U\simeq7.83\,\mathrm{m/s},
\quad C_{L0}\simeq0.1070,
\quad L_{\rm total}\simeq205\,\mathrm N.
\]
</div>

它有两个值得特别检查的地方：

1. **面积约定不同。** 这里分母是 $qb^2$。如果改用 $S_{\rm ref}=bL_m=\lambda b^2$，同一个总承托力对应的系数是 $C_{L,\rm total}=C_{L0}/\lambda\simeq0.0535$。
2. **该式已经含有静水贡献。** 括号中的第二项带 $C_V^{-2}$，乘回 $q$ 后，在固定 $b,\lambda,\tau$ 时速度因子抵消；它表达模型中的浮力贡献。因此不能把上面 $205\,\mathrm N$ 当成纯动态升力，再额外加一次静水浮力。

这个计算是在给定姿态与湿长度下求承托力，不等于已经求出一辆自由运动摩托车的平衡姿态。真正用 Savitsky 方法作性能预测，还需联立载荷和力矩平衡求解纵倾、湿长度等未知量，并检查适用几何与稳定性。两块分离的窄板、旋转轮胎以及板间尾流干扰，都可能超出这个简单模型的覆盖范围。

## 十、用什么工具模拟，以及一项可执行的建模顺序

### 1. 参数扫描：Python、Mathematica 或电子表格

第一层任务是复算第三节的量级关系，或实现第九节的半经验方程。输入质量、参考面积、速度、迎角及几何比例，观察承托力、阻力和力矩怎样变化。这类工具适合参数扫描与求平衡根；算出一个数字，只说明所选模型的计算完成了。

例如，第三节的核心计算可直接复现：

```python
from math import sqrt

rho, g = 1000.0, 9.81
mass, area, cl = 180.0, 0.10, 0.10  # 教学假设
for speed_kmh in (40, 60, 70, 80):
    speed = speed_kmh / 3.6
    lift = 0.5 * rho * speed**2 * area * cl
    print(speed_kmh, round(lift), round(lift / g, 1))
balance_kmh = 3.6 * sqrt(2 * mass * g / (rho * area * cl))
print("balance speed under these assumptions:", round(balance_kmh, 1))
```

### 2. 自由液面 CFD：OpenFOAM

OpenFOAM 可以求解空气与水的两相自由液面流动，使用 VOF（流体体积法）描述各网格中的水体积分数。若以 $\chi$ 表示水相比例，理想的不可压缩输运方程及混合密度可写为

<div class="post-math-display">
\[
\partial_t\chi+\nabla\cdot(\chi\boldsymbol u)=0,
\qquad
\rho=\chi\rho_w+(1-\chi)\rho_a.
\]
</div>

VOF 的经典出处是 Hirt 与 Nichols 的原论文；实际软件还会加入界面重构或压缩等离散处理。[^vof] 对滑行问题，需将自由液面、湍流模型、壁面条件和刚体运动耦合。后面介绍的公开案例就是一项真实的 OpenFOAM 滑行船体研究。[^gpph]

后处理时先积分得到有量纲的力和力矩，再按所选 $\rho_w,U,S_{\rm ref}$ 自行核对系数。尤其要区分实际压力 $p$ 与减去重力势压强后的变量 `p_rgh`：它们不是同一物理量，恢复关系和参考高度应按所用版本检查，不能把 `p_rgh` 直接当作实际表压积分后再重复加减浮力。官方文档分别说明了压力变换和力系数的参考量。[^openfoam-pressure][^openfoam-forces]

### 3. 商业工具：Fluent 与 Simcenter STAR-CCM+

Fluent 的 VOF／明渠流设置提供自由液面高度、入口出口与波浪边界等处理；Simcenter STAR-CCM+ 的船舶应用覆盖阻力、动态升沉、纵倾和操纵分析。两者适合已有授权与相应建模经验的团队。选择软件以后，仍需用同一几何、边界条件和试验数据核对结果。[^fluent][^siemens]

对于这辆摩托车，一个逐步增加复杂度的研究顺序是：

1. **单块板，固定姿态。** 建立三维空气—水计算域，给定速度、迎角和高度，输出升力、阻力与关于选定参考点的力矩；确认压力区和湿区的位置合理。
2. **前后板组合。** 加入实际间距和相对高度，检查前板尾流、喷溅与空气卷入如何改变后板受力。
3. **释放升沉与俯仰。** 输入整车质量、质心和转动惯量，求直线行驶的动态平衡与扰动响应；转弯时再加入横滚、偏航等自由度及操纵。
4. **加入旋转后轮。** 使用适当的动网格或重叠网格描述拨水，计算推力、扭矩和轮胎的竖直水动力，最终与整车运动耦合。

每一步都应记录网格、时间步、计算域边界距离和平均时间窗，并比较至少一组可信的力与姿态数据。对关键工况分别检查空间和时间分辨率的影响；仅有残差下降或一张漂亮的水花图，尚不足以确定 $C_L$ 的准确度。

## 十一、公开 CFD 案例：网格加密以后，结果改善了多少？

Li、Bonfiglio 与 Brizzolara 在 MARINE 2019 发表了针对 GPPH（通用棱柱形滑行船体）的 OpenFOAM 验证研究。模型长约 $2.4\,\mathrm m$、底升角 $18^\circ$，试验允许升沉和俯仰。这里摘取其 Table 2 在 $U=12.24\,\mathrm{m/s}$ 下的一组结果。[^gpph]

- 约 **114 万**网格：阻力 $220.4\,\mathrm N$，比试验值低约 **18.32%**。
- 约 **242 万**网格：阻力 $244.0\,\mathrm N$，比试验值低约 **9.57%**。
- 约 **456 万**网格：阻力 $252.0\,\mathrm N$，比试验值低约 **6.61%**。
- 对应的**试验阻力为 $269.83\,\mathrm N$**；细网格的纵倾角为 $2.19^\circ$，试验为 $2.17^\circ$。

这几组数据表明，该工况下网格加密使阻力预测更接近试验，但不同观测量的吻合程度并不相同。研究还讨论了板底／船底区域的数值通气：离散误差会让空气不恰当地扩散进承压区，改变预测受力。细网格有所改善，不能因此认定所有误差已经消失。

上述数据是**原论文的结果，本文没有重新运行这套 CFD**。船体几何也不同于机车滑行板，不能拿它的系数代替实车系数。它提供的可迁移经验是：要同时验证力、姿态与湿区，并把数值分辨率的影响量化；验证一个船体，也只建立了在相应条件下的可信度。

## 十二、承托、推进与稳定，最终要一起满足

前后板主要帮助形成向上的水动力，后轮拨水则补充克服阻力所需的机械能。稳态直行时，近似有

<div class="post-math-display">
\[
F_{\mathrm{water},z}\simeq mg,
\qquad T\simeq D,
\qquad P_{\rm shaft}\simeq\frac{DU}{\eta}.
\]
</div>

$\eta$ 是从轴功率到有效推进功率的效率。升力的方向在稳态时主要竖直，不能直接用 $LU$ 代替推进功率；真正与向前速度相乘的是阻力。

例如对一个忽略切向摩擦、压力合力垂直于板面的平面模型，纵倾角为 $\alpha$ 时有 $D_p=L\tan\alpha$。若 $L=1766\,\mathrm N$、$\alpha=5^\circ$，压力阻力约 $154\,\mathrm N$；在 $70\,\mathrm{km/h}$ 时，仅这一项就对应约 $3.0\,\mathrm{kW}$ 的有效功率，还未计入摩擦、轮胎与其他阻力及推进损失。这仍是示例估算，不是实车功率测量。

所以，两个最初的问题可以这样回答：**几块小板之所以可能托住高速运动的摩托车，是因为流动惯性建立的压力经表面积分后足以承重；静止时的 $\rho gV_{\rm disp}$ 则来自静水压力梯度。** 二者服从同一套力学，但压力场、边界条件和适用的近似不同。至于某辆车究竟有多大升力、能以多低速度滑行、能否稳定转弯，则必须进一步测量或求解它的几何、动力与姿态问题。

## 文献与资料

下列引用分别承担新闻事实、基础定律、半经验模型、数值方法与公开验证案例的证据。算例中的假设参数不作为实车数据引用。

[^xinhua]: 程济安，新华社：《机车上演“水上漂”，张雪在家乡麻阳刷新吉尼斯纪录》，2026-10-25。报道包含 40.74 公里成绩及研发工程师对滑行橇、后轮拨水的说明。[新华网原文](https://www.xinhuanet.com/20261025/db3de9ebf9ab426bbaea915e46091574/c.html)。

[^archimedes]: Samuel J. Ling, Jeff Sanny, William Moebs, *University Physics, Volume 1*, OpenStax, §14.4, “Archimedes’ Principle and Buoyancy”。[教材原文](https://openstax.org/books/university-physics-volume-1/pages/14-4-archimedes-principle-and-buoyancy)。本文的散度定理及力矩表达是对静水平衡关系的展开推导。

[^nasa-cl]: NASA Glenn Research Center, “Lift Coefficient”。说明 $C_L=L/(qA)$ 的定义、形状和姿态依赖以及实验确定系数的方法。[官方资料](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/lift-coefficient-2/)。该资料针对空气动力；本文使用相同的无量纲定义，并针对水面问题另行处理自由液面和重力。

[^faltinsen]: Odd M. Faltinsen, *Hydrodynamics of High-Speed Marine Vehicles*, Cambridge University Press，2006，第 1、9 章。[DOI: 10.1017/CBO9780511546068](https://doi.org/10.1017/CBO9780511546068)，[出版社开放节选](https://assets.cambridge.org/052184/5688/excerpt/0521845688_excerpt.htm)。节选讨论静水压力、水动力压力和速度尺度；这里未据此声称已读取全书。

[^mit-ns]: MIT OpenCourseWare, *18.354J Nonlinear Dynamics II: Continuum Systems*, Spring 2015, Lecture 13, “The Navier–Stokes Equations”。[讲义 PDF](https://ocw.mit.edu/courses/18-354j-nonlinear-dynamics-ii-continuum-systems-spring-2015/6f1477ffaa90b8c93556120294eecd64_MIT18_354JS15_Ch13.pdf)。用于连续介质中的动量方程和牛顿流体本构假设。

[^bernoulli]: Ling, Sanny & Moebs, *University Physics, Volume 1*, OpenStax, §14.6, “Bernoulli’s Equation”。[教材原文](https://openstax.org/books/university-physics-volume-1/pages/14-6-bernoullis-equation)。伯努利关系有稳态、不可压缩、可忽略黏性耗散等使用条件；沿流线积分不等于不同流线之间自动共享同一常数。

[^ittc]: International Towing Tank Conference, *High Speed Marine Vehicles Resistance Test*, Recommended Procedure 7.5-02-05-01, Revision 03, 2017。这里引用这一明确版本，参见 §3 的试验安装与测量、§4.3 的湿面积、§4.6 的约束试验和 §5 的验证。[ITTC 官方 PDF](https://www.ittc.info/media/8063/75-02-05-01.pdf)。

[^savitsky]: Daniel Savitsky, “Hydrodynamic Design of Planing Hulls,” *Marine Technology*, **1**, 71–95 (1964)。本文核对了原稿 pp. 78–79，尤其式 (15) 及其后的适用范围。[DOI: 10.5957/MT1.1964.1.4.71](https://doi.org/10.5957/MT1.1964.1.4.71)，[本文核对的原文扫描副本](https://forum.katera.ru/index.php?app=core&attach_id=518175&module=attach&section=attach)。

[^vof]: C. W. Hirt and B. D. Nichols, “Volume of Fluid (VOF) Method for the Dynamics of Free Boundaries,” *Journal of Computational Physics*, **39**(1), 201–225 (1981)。[DOI: 10.1016/0021-9991(81)90145-5](https://doi.org/10.1016/0021-9991%2881%2990145-5)。

[^gpph]: Jiahui Li, Luca Bonfiglio and Stefano Brizzolara, “Verification and Validation Study of OpenFOAM on the Generic Prismatic Planing Hull Form,” *MARINE 2019: VIII International Conference on Computational Methods in Marine Engineering*, CIMNE, 2019, pp. 428–440, ISBN 978-84-949194-3-5。模型见 §3，本文摘录的数据见 Table 2，数值通气讨论见 §4.2 及结论。[大学机构库记录](https://hdl.handle.net/2117/330009)，[开放全文 PDF](https://upcommons.upc.edu/bitstream/handle/2117/330009/Marine-2019-35_Verification%20and%20validation%20study.pdf)。

[^openfoam-pressure]: OpenCFD, *OpenFOAM Documentation*, “Hydrostatic pressure effects”。说明 `p_rgh` 与实际压力及重力势项的关系。[官方文档](https://doc.openfoam.com/2606/tools/processing/solvers/algorithm-p-rgh/)。

[^openfoam-forces]: OpenCFD, *OpenFOAM Documentation*, “Force coefficients,” v2306。说明受力面、升阻力方向、速度、参考面积和参考长度等设置。[版本化官方文档](https://doc.openfoam.com/2306/tools/post-processing/function-objects/forces/forceCoeffs/)。不同 OpenFOAM 发行分支的设置应分别核对。

[^fluent]: Ansys, *Fluent User’s Guide*, 2024 R2, §26.3, “Setting Up the VOF Model”，尤其自由液面高度、明渠与波浪边界相关设置。[版本化官方文档](https://ansyshelp.ansys.com/public/Views/Secured/corp/v242/en/flu_ug/flu_ug_sec_mphase_using_steps_vof.html)。

[^siemens]: Siemens Digital Industries Software, “CFD modeling and design optimization for fast boat design”。介绍 Simcenter STAR-CCM+ 在快艇阻力、升沉、纵倾、波浪与操纵问题中的应用。[官方介绍](https://webinars.sw.siemens.com/de-DE/advanced-marine-simulation-for-fast-boats-design/)。

{% include post-math.html %}
