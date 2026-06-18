# 3D-rotations 项目完全讲解（自学版）

> 这份文档是把"我（助手）读代码 + 推理 + 拷打你的 8 道题"全过程拆成步骤写下来的。
> 你之前只是点了选项、没真正读码思考，所以这里把每一步的**代码依据**和**为什么**都摊开，
> 让你能自己重走一遍。读完后回到作业（文末）自己动手。
>
> 项目路径：`RotatingOnScrollAnimations/`
> 涉及文件：`index.html`~`index5.html`、`js/index.js`~`index5.js`、`css/base.css`

---

## 目录

- [第 0 步：项目长什么样](#第-0-步项目长什么样)
- [第 1 步：5 个 variation 共享的骨架](#第-1-步5-个-variation-共享的骨架)
- [第 2 步：地基概念 A —— perspective（透视）](#第-2-步地基概念-a--perspective透视)
- [第 3 步：地基概念 B —— 三根旋转轴](#第-3-步地基概念-b--三根旋转轴)
- [第 4 步：核心机制 —— 滚动进度驱动 + "经过 0 摆正"](#第-4-步核心机制--滚动进度驱动--经过-0-摆正)
- [第 5 步：差异旋钮① —— z 景深曲线（sin 的指数）](#第-5-步差异旋钮-z-景深曲线sin-的指数)
- [第 6 步：差异旋钮② —— 蛇形布局（振幅与频率）](#第-6-步差异旋钮-蛇形布局振幅与频率)
- [第 7 步：差异旋钮③ —— 进度重映射 holdAtMiddle（V5）](#第-7-步差异旋钮-进度重映射-holdatmiddlev5)
- [第 8 步：差异旋钮④ —— 位置驱动 vs 速度驱动（V4）](#第-8-步差异旋钮-位置驱动-vs-速度驱动v4)
- [第 9 步：写法之争 —— fromTo vs 手动 onUpdate](#第-9-步写法之争--fromto-vs-手动-onupdate)
- [第 10 步：逐个 variation 拆解](#第-10-步逐个-variation-拆解)
- [总表：5 个 variation 的全部差异](#总表5-个-variation-的全部差异)
- [附：8 道拷打题与正确答案](#附8-道拷打题与正确答案)
- [课题作业](#课题作业variation-6造一个属于你自己的旋转)

---

## 第 0 步：项目长什么样

```
RotatingOnScrollAnimations/
├── index.html ~ index5.html      # 5 个页面，每个 <body class="demo-N">，引一个 indexN.js
├── css/base.css                  # 所有页面共用同一份 CSS，靠 .demo-N 切换变量
├── js/
│   ├── index.js ~ index5.js      # 5 个 variation 的动画逻辑（差异都在这里）
│   ├── gsap.min.js               # 动画引擎
│   ├── ScrollTrigger.min.js      # GSAP 的滚动触发插件
│   ├── lenis.min.js              # 平滑滚动库
│   └── imagesloaded.pkgd.min.js  # 等图片加载完再开始
└── assets/landscape/01~20.webp   # 20 张图
```

**关键观察**：5 个 `indexN.js` 95% 的代码是一模一样的。真正不同的只有两个函数：
- `initGalleryAnimation()` —— 每张卡随滚动怎么旋转/变形/加滤镜
- `positionGalleryItems()` —— 卡片在页面上横向怎么散开

> 💡 学习策略：先彻底搞懂"共享骨架"（第 1 步），剩下的就只是对比这两个函数的差别。

HTML 结构（以 index.html 为例，5 个页面结构相同，只换 `demo-N` 和脚本名）：

```html
<body class="demo-1 loading">
  <div class="gallery">
    <div class="gallery__item" style="background-image: url('assets/landscape/19.webp')"></div>
    <!-- ... 共 20 个 .gallery__item ... -->
  </div>
  <div class="mark font-1"><div class="mark__inner"><span>...</span></div></div>
  <script src="js/imagesloaded.pkgd.min.js"></script>
  <script src="js/lenis.min.js"></script>
  <script src="js/gsap.min.js"></script>
  <script src="js/ScrollTrigger.min.js"></script>
  <script src="js/index.js"></script>   <!-- 唯一的变量 -->
</body>
```

注意：`.gallery__item` 在 HTML 里是**平铺的**，并没有 `.gallery__item-wrap` 父层。那个父层是 **JS 动态创建**的（见下一步）。

---

## 第 1 步：5 个 variation 共享的骨架

每个 `indexN.js` 的 `init()` 都是这几步：

```js
function init() {
  initSmoothScrolling();    // 1. Lenis 平滑滚动接到 GSAP ticker
  createGalleryWrappers();  // 2. 给每张卡套一个 .gallery__item-wrap 父层
  positionGalleryItems();   // 3. 蛇形横向布局（V3 没有这步！）
  initGalleryAnimation();   // 4. ★核心：每张卡的滚动动画
  animateMarquee();         // 5. 背景大字横向滚动
  initEvents();             // 6. resize 时重算
}
document.addEventListener('DOMContentLoaded', async () => {
  await preloadImages('.gallery__item');     // 等图片背景加载完
  document.body.classList.remove('loading'); // 移除 loading 遮罩
  init();
});
```

### 1.1 平滑滚动（所有 variation 一样）

```js
function initSmoothScrolling() {
  lenis = new Lenis();
  lenis.on('scroll', ScrollTrigger.update);        // 滚动时通知 ScrollTrigger 更新
  gsap.ticker.add((time) => lenis.raf(time * 1000)); // 用 GSAP 的帧循环驱动 lenis
  gsap.ticker.lagSmoothing(0);
}
```
作用：把浏览器原生那种"一格一格跳"的滚动，换成有惯性的丝滑滚动，并且让 GSAP 和 lenis 用同一个时钟。
（V4 在这里做了改动 —— 它额外读了 `velocity`，见第 8 步。）

### 1.2 动态创建 3D 容器（所有 variation 一样）

```js
function createGalleryWrappers() {
  items = gsap.utils.toArray('.gallery__item');
  items.forEach((item) => {
    const wrapper = document.createElement('div');
    wrapper.classList.add('gallery__item-wrap');
    item.parentNode.insertBefore(wrapper, item); // 在卡前面插入 wrap
    wrapper.appendChild(item);                    // 把卡塞进 wrap
  });
  wraps = gsap.utils.toArray('.gallery__item-wrap');
}
```
结果是 DOM 从这样：
```html
<div class="gallery">
  <div class="gallery__item"></div>
</div>
```
变成这样：
```html
<div class="gallery">
  <div class="gallery__item-wrap">   <!-- 提供 perspective，被横向定位 -->
    <div class="gallery__item"></div> <!-- 被旋转/变形 -->
  </div>
</div>
```

**为什么要分两层？** —— 这是整个项目最重要的结构决策：
- **外层 wrap** 负责"透视舞台"和"横向位置"（`x`）。
- **内层 item** 负责"旋转和变形"（`rotateX/z/scale/filter`）。

分开后，旋转不会干扰定位，定位也不会干扰旋转，互不打架。

### 1.3 CSS 里的 3D 设置（base.css 关键几行）

```css
.gallery__item-wrap {
  max-width: var(--item-width);
  perspective: 900px;        /* ★ 透视舞台，写在父层 */
  margin-bottom: -5rem;      /* 负 margin 让卡片上下重叠 */
}
.gallery__item {
  transform-style: preserve-3d; /* ★ 让子元素保留 3D 空间 */
  will-change: transform, filter; /* 提示浏览器这俩会频繁变，提前优化 */
  border-radius: var(--item-br);
  aspect-ratio: var(--item-ar);
  background-size: cover;
}
```

记住这个分工，后面 8 道题里有 3 道都建立在它上面。

---

## 第 2 步：地基概念 A —— perspective（透视）

### 它在干什么
`perspective` 定义"观察者的眼睛离屏幕平面有多远"。它把"远处的东西显示得更小"这个真实世界规律，套到 3D 变换上。

### 实验：有它 vs 没它
对同一个 `rotateX(60deg)`：

| | 有 `perspective: 900px` | 没有 perspective |
|---|---|---|
| 效果 | 近边变大、远边变小，像真的被掀起来的牌 | 只是被竖向压扁的矩形（正交投影），没有近大远小 |
| 术语 | 透视投影 | 正交投影 |

**所以删掉 perspective，旋转照样发生，但立体感消失了。** 这就是第 1 道拷打题的答案。

### 旋钮：perspective 的值
- 值**越小** → 眼睛离屏幕越近 → 透视**越夸张**（近大远小更极端，畸变更强烈）。
- 值**越大** → 越接近正交投影 → 越平。
- 本项目用 `900px`，属于中等偏温和。

> 🔧 作业拷打题 1："perspective 改成 200px 会怎样？" → 透视急剧夸张，旋转时卡片畸变会非常猛烈、近边巨大。

### 旋钮：perspective 放在父层 vs 卡片自己身上
- **放父层**（本项目做法）：所有子卡片**共享同一个消失点**，像真实房间里所有家具朝同一个灭点收缩，群组协调。
- **放卡片自己身上**（`transform: perspective(900px) rotateX(...)`）：每张卡有独立灭点，群组感会散掉。

---

## 第 3 步：地基概念 B —— 三根旋转轴

一张正对你贴在屏幕上的卡片：

| 变换 | 绕哪根轴 | 现实类比 | 90° 时 |
|---|---|---|---|
| `rotateX(90deg)` | 水平横轴 | **点头**（前后倒） | 薄成一条横线，几乎看不见 |
| `rotateY(90deg)` | 垂直竖轴 | **摇头 / 开关门** | 薄成一条竖线，几乎看不见 |
| `rotateZ(90deg)` | 垂直于屏幕的轴 | **转圈**（时钟指针） | 在屏幕平面内转 90°，不会变薄 |

**关键推论**（贯穿整个动画）：
- `rotateX(0deg)` = 卡片**完全正对你**（最清晰、最大）。
- `rotateX(±90deg)` = 卡片**侧面对你 = 薄成一条线**。

> 各 variation 的"主导轴"：V1/V2/V3/V5 主要绕 **X**（点头翻牌），V4 主要绕 **Y**（开门转门）。
> V1/V5 还叠加了 Z（转圈）做点歪斜。

---

## 第 4 步：核心机制 —— 滚动进度驱动 + "经过 0 摆正"

### ScrollTrigger 的 progress
每张卡都有一个 ScrollTrigger，触发区间：
```js
scrollTrigger: {
  trigger: item,
  start: 'top bottom+=20%',   // 卡片顶部到达"视口底部再往下 20%"时，progress=0
  end: 'bottom top-=20%',     // 卡片底部到达"视口顶部再往上 20%"时，progress=1
  scrub: true,                // ★ 把动画进度死死绑在滚动进度上（不是自动播放）
  invalidateOnRefresh: true,  // resize 后重新测量
}
```
`scrub: true` 是灵魂：动画不会自己播，而是**你滚到哪、动画就停在哪**。`progress` 是 0→1 的数，代表"这张卡从入场到离场走了多少"。

### "经过 0"的设计（以 V1 为例）
```js
const rotationX = gsap.utils.random(70, 120);   // 比如抽到 95
gsap.fromTo(item,
  { rotationX },                                  // 起点：+95°
  { rotationX: -rotationX, ease: 'none', scrollTrigger: {...} } // 终点：-95°
);
```
随着滚动 progress 0→1，`rotationX` 从 **+95° 线性 → −95°**：

| progress | rotationX | 卡片状态 |
|---|---|---|
| 0（刚入场，屏幕底部） | +95° | 侧斜面，快看不见 |
| **0.5（屏幕正中）** | **0°** | **完全正对你，最清晰** |
| 1（离场，屏幕顶部） | −95° | 另一侧斜面，又快看不见 |

**为什么要"经过 0"而不是从 0 转到 95？**
因为这样卡片恰好在**视野正中央转正、亮相给你看**，然后继续翻走，形成"翻进 → 摆正 → 翻出"的流动节奏。这是整个视觉效果的核心戏剧点。这就是第 3 道拷打题的答案。

> 🔧 作业拷打题 2："z 系数从 -400 改成 +400 会怎样？" → 见第 5 步：负 z 是"凹进屏幕（远离你）"，正 z 是"凸出屏幕（冲向你）"，卡片会在中点扑到你脸上。

---

## 第 5 步：差异旋钮① —— z 景深曲线（sin 的指数）

5 个 variation 都让卡片在中点往屏幕里"凹"进去（`z` 负值 = 远离观众），都用同一个母函数：

```js
const z = Math.sin(progress * Math.PI) * (负数);
```

`Math.sin(progress * π)` 的形状（这是关键）：

| progress | progress·π | sin 值 |
|---|---|---|
| 0 | 0 | 0 |
| 0.5 | π/2 | 1（峰值） |
| 1 | π | 0 |

所以这是一个"两端=0、中间=1"的驼峰——卡片入场和离场时 z=0（贴在原位），到中点凹到最深。

### 指数旋钮（V1/V2/V3 的真正区别）

```js
// V1
const z = Math.sin(p * Math.PI)        * -50;
// V2
const z = Math.pow(Math.sin(p*Math.PI), 4) * -300;
// V3
const z = Math.pow(Math.sin(p*Math.PI), 8) * -800;
```

把 `sin` 的指数从 1 提到 8，驼峰会越来越"尖"：

| 指数 | 曲线形状 | 体感 |
|---|---|---|
| 1 | 胖驼峰，从头慢慢凹 | V1：全程缓缓轻推，温柔 |
| 4 | 中间才明显凹 | V2：两边偏平，中段集中下沉 |
| 8 | 针尖一样的尖峰 | V3：平时贴平，只在正中央"猛地一下"扎进屏幕深处 |

**为什么指数越高越尖？** 因为底数 sin 在 0~1 之间，小数的高次方会变得更小（例：`0.9⁸ ≈ 0.43`，`0.5⁸ ≈ 0.004`），只有非常接近 1（即非常接近 progress=0.5）的地方才保留较大值。于是凹陷被"挤"到正中央。这就是第 4 道拷打题的答案。

> 配合后面更大的负深度（-50 → -300 → -800），V1 是"全程缓推"，V3 是"平时不动、正中央扎一记重拳"。

---

## 第 6 步：差异旋钮② —— 蛇形布局（振幅与频率）

`positionGalleryItems()` 决定卡片横向怎么排：

```js
function positionGalleryItems() {
  const amplitude = window.innerWidth * 0.2;   // V1：振幅
  wraps.forEach((wrap, i) => {
    const angle = i * 0.45;                     // V1：相位系数
    gsap.set(wrap, { x: Math.sin(angle) * amplitude });
  });
}
```
每张卡横向位置 = `sin(i × 系数) × amplitude`，于是往下走时卡片像蛇一样左右摆。

| 旋钮 | 控制什么 | 大 → | 小 → |
|---|---|---|---|
| `amplitude` | 振幅：最多偏左/偏右多远 | 摆得宽 | 几乎竖直 |
| 系数（i 的乘数） | 频率/相位步进：相邻两卡相位差 | 摆得密（来回快） | 摆得缓 |

各 variation：
- V1：`amplitude = 0.2·宽`，系数 `0.45`（中等宽、缓摆）
- V4：`amplitude = 0.2·宽`，系数 `1`（注意 V4 是 `Math.sin(i)`，没乘小数 → 摆得更跳）
- V5：`amplitude = 0.05·宽`，系数 `0.9`（几乎竖直、密摆）
- **V3：根本不调用这个函数** → 所有卡 `x=0` → **全部居中竖直堆叠**（配合 CSS 负 margin 互相重叠）。这就是第 7 道拷打题的答案，也是 V3"卡片从黑暗中一张张浮现"观感的来源。

> 🔧 作业拷打题 4："系数从 0.6 改成 6.28(≈2π) 会怎样？" → 相邻卡相位差接近一整圈，sin 值看起来"乱跳"，蛇形规律被打散，接近随机左右。

---

## 第 7 步：差异旋钮③ —— 进度重映射 holdAtMiddle（V5）

V5 最高级的一招：不直接用滚动 `progress`，先"加工"一道再喂给所有效果。

```js
function holdAtMiddle(progress, hold = 0.25) {
  const half = hold * 0.5;                                    // 0.125
  if (progress < 0.5 - half) return mapRange(0, 0.375, 0, 0.5, progress);
  if (progress > 0.5 + half) return mapRange(0.625, 1, 0.5, 1, progress);
  return 0.5;  // ★ 中间这 25% 区间，直接吐 0.5
}
```
（`mapRange(a,b,c,d,x)` = 把落在 [a,b] 的 x 线性映射到 [c,d]。）

把真实 `progress` 喂进去得到加工后的 `t`：

| 真实 progress | 加工后 t |
|---|---|
| 0 → 0.375 | 0 → 0.5（正常推进，略快） |
| **0.375 → 0.625** | **恒为 0.5（冻住）** |
| 0.625 → 1 | 0.5 → 1（正常推进） |

然后 V5 所有效果都用 `t` 算：
```js
const t = holdAtMiddle(self.progress, 0.25);
const rX = interpolate(-rotationX, rotationX, t);
const z  = Math.sin(t * Math.PI) * -750;
const blur = Math.pow(Math.cos(t * Math.PI), 2) * 12;
const scaleX = 1 + Math.pow(Math.cos(t*Math.PI), 2) * 0.6;  // 边缘变宽
const scaleY = 0.5 + Math.pow(Math.sin(t*Math.PI), 2) * 0.5;// 中点变高
const brightness = Math.pow(Math.sin(t*Math.PI), 6);
```
因为 `t=0.5` 意味着"正对你 / 最亮 / 最清晰 / 拉伸到位"，而中间 25% 的滚动里 `t` 恒为 0.5，所以**卡片会在正中央"冻住/停留"一段滚动距离**，像把卡片端到你面前定格展示，然后才继续翻走。这是第 6 道拷打题的答案。

> 附带 V5 的"挤压拉伸"（scaleX/scaleY）：边缘时卡片宽而扁，中点时窄而高，像橡皮被拉。这是 5 个 variation 里唯一玩缩放的。

---

## 第 8 步：差异旋钮④ —— 位置驱动 vs 速度驱动（V4）

V1/V2/V3/V5 的所有效果都是 `progress`（滚动**位置**）的纯函数：你停在哪，画面就定在哪，倒着滚完全对称还原。

**V4 引入了一个全新维度：滚动速度。**

```js
let scrollVelocity = 0;
let blurAmount = 0;

function initSmoothScrolling() {
  lenis = new Lenis();
  lenis.on('scroll', ({ velocity }) => {        // ★ 读滚动速度
    scrollVelocity = Math.abs(velocity);
    ScrollTrigger.update();
  });
  gsap.ticker.add((time) => {                   // ★ 每一帧都跑
    lenis.raf(time * 1000);
    const velocityNorm = Math.min(scrollVelocity / 40, 1);  // 归一化到 0~1
    const targetBlur = velocityNorm * 15;
    blurAmount = gsap.utils.interpolate(blurAmount, targetBlur, 0.45); // ★ 缓动追赶
    const filter = `blur(${blurAmount}px) saturate(${1 - velocityNorm})`;
    filterSetters.forEach((setFilter) => setFilter(filter)); // 套到所有卡
  });
}
```

区别本质：

| | V1/V2/V3/V5 | V4 的模糊 |
|---|---|---|
| 驱动量 | 滚动**位置** progress | 滚动**速度** velocity |
| 停下不动 | 画面定格不变 | velocity→0，模糊**逐渐退到 0**（变清晰） |
| 有没有"记忆/惯性" | 无，是纯函数 | 有，`interpolate(..., 0.45)` 让模糊每帧只追上目标的 45%，产生拖尾/重量感 |

所以"滚到一半手停下，V4 卡片最终会变清晰"——这是第 5 道拷打题的答案。

> 🔧 作业拷打题 5：`interpolate(blur, target, 0.45)` 的 0.45 是"追赶速度"。
> - 调到 `0.05`：每帧只追 5%，模糊变化非常黏、拖尾很长，停下后要很久才清晰。
> - 调到 `1`：每帧瞬间追满，等于没有惯性，模糊跟速度硬绑、很生硬。

V4 的旋转：主导 Y 轴（`rotationY: random(200,290)` 大幅开门转），X/Z 只给 ±10 小歪斜。

---

## 第 9 步：写法之争 —— fromTo vs 手动 onUpdate

两种代码骨架：

```js
// 写法 A（V1/V2）：声明式。给起点和终点，GSAP 自己在两点间按单一 ease 补间
gsap.fromTo(item,
  { rotationX: 95 },
  { rotationX: -95, ease: 'none', scrollTrigger: { scrub: true } }
);

// 写法 B（V3/V4/V5）：命令式。自己在每一帧拿 progress 算所有属性
ScrollTrigger.create({
  trigger: item, start: '...', end: '...', scrub: true,
  onUpdate(self) {
    const p = self.progress;
    setTransform({ rotationX: f(p), z: g(p), yPercent: h(p) }); // 全自己算
    setFilter(`saturate(${s(p)}) brightness(${b(p)})`);
  }
});
```

**为什么 V3/V4/V5 不能用 fromTo？**
`fromTo` 只能在"一个起点 → 一个终点"之间按**单一缓动**插值。但：
- V3 的 `z = sin(p·π)⁸·-800` 是 **0→最深→0 的来回**，不是从一个值单调到另一个值；
- V3 的 `rotationX = sign(cos)·|cos|^0.6·90` 是**非线性整形**；
- V5 的 `holdAtMiddle` 是**自定义重映射**（中间冻住）；
- V4 的模糊是**速度驱动**，根本不在 progress 上。

这些都不是"两个端点之间插值"能凑出来的，所以必须自己接管 `progress`、每帧手算，再用 `gsap.quickSetter`（高性能写 DOM 的工具）写回去。这是第 8 道拷打题的答案。

> 记忆口诀：**效果是 progress 的单调插值 → 能用 fromTo；非单调 / 耦合 / 自定义重映射 / 速度驱动 → 必须 onUpdate 手算。**

---

## 第 10 步：逐个 variation 拆解

### Variation 1（index.js）—— 温柔基准
- 布局：`amplitude = 0.2·宽`，系数 `0.45`。
- 旋转：`rotationX random(70,120)`、`rotationY random(-20,20)`、`rotationZ random(-20,20)`，`fromTo` 从 +rot 线性到 -rot。
- 景深：`z = sin(p·π)·-50`（浅）。
- 滤镜：无。
- 写法：`fromTo`。
- **观感**：一群微微歪斜的卡片，滚过中央时温柔转正，轻轻往里凹一下。最克制。

### Variation 2（index2.js）—— 猛翻 + 深扎
- 布局：同 V1。
- 旋转：`rotationX random(240,290)`（近 270° 大翻！）、`rotationZ random(-50,50)`（更大歪）。
- 景深：`z = sin(p·π)⁴·-300`（中段集中、深）。
- 写法：`fromTo`。
- **观感**：卡片大幅翻滚、歪得厉害，中段猛地往屏幕深处沉。比 V1 戏剧化得多。

### Variation 3（index3.js）—— 居中堆叠 + 显影
- 布局：**不调用 positionGalleryItems** → 全部居中竖直堆叠重叠。
- 全程**无随机**，纯靠 progress 数学：
  - `rotationX = sign(cos(p·π))·|cos(p·π)|^0.6·90`（+90→0→−90，带非线性整形）
  - `z = sin(p·π)⁸·-800`（针尖式极深扎入）
  - `yPercent = 1 + cos(p·π)²·-40`（上下位移）
  - `filter: saturate / brightness 都 = sin(p·π)³`（两端暗淡、中央才变鲜亮全亮）
- 写法：`ScrollTrigger.create` + `quickSetter`。
- **观感**：黑底上卡片在正中央一张张"显影"——从黑暗里浮现、转正变亮、再沉回黑暗。

### Variation 4（index4.js）—— 转门 + 速度模糊
- 布局：`amplitude = 0.2·宽`，`Math.sin(i)`（系数=1）。
- 旋转：主导 **Y 轴** `rotationY random(200,290)`（开门式横转），X/Z 仅 ±10。用 `interpolate(rot,-rot,p)` 手动插值。
- 景深：`z = sin(p·π)·-150`。
- 滤镜：**速度驱动**的 `blur + saturate`（见第 8 步），在 ticker 里全局套到所有卡，有惯性拖尾。
- 写法：`ScrollTrigger.create` + 速度逻辑。
- **观感**：卡片像一扇扇门横向开合；滚得越快整屏越糊越灰，停下慢慢变清晰。

### Variation 5（index5.js）—— 中点定格 + 橡皮拉伸
- 布局：`amplitude = 0.05·宽`（很窄），系数 `0.9`（几乎竖直密排）。
- 用 `holdAtMiddle(progress, 0.25)` 重映射，让卡片在正中央**冻住一段**（见第 7 步）。
- 旋转：`rotationX random(130,220)`、`rotationZ` 固定 `-50`。
- 景深：`z = sin(t·π)·-750`（深）。
- 变形：`scaleX = 1+cos²·0.6`、`scaleY = 0.5+sin²·0.5`（边缘宽扁、中点窄高，挤压拉伸）。
- 滤镜：`blur = cos(t·π)²·12`、`brightness = sin(t·π)⁶`。
- 写法：`ScrollTrigger.create` + `holdAtMiddle` + `quickSetter`。
- **观感**：卡片像被橡皮筋拉着翻上来，到正中央定格展示一会儿（清晰、明亮、拉伸到位），再翻走。最复杂、最有"仪式感"。

---

## 总表：5 个 variation 的全部差异

| | 横向布局 | 主导旋转轴 | z 景深曲线 | 进度处理 | 额外特效 | 写法 |
|---|---|---|---|---|---|---|
| V1 | sin, amp 0.2, k0.45 | X 70–120° 翻 | `sin·-50` 浅 | 线性 | 无 | `fromTo` |
| V2 | 同 V1 | X 240–290° 猛翻 | `sin⁴·-300` 深 | 线性 | 无 | `fromTo` |
| V3 | **不散开**（堆叠） | X ±90°（cos 整形） | `sin⁸·-800` 极深 | 线性 | saturate+brightness 显影 | `create`+quickSetter |
| V4 | sin(i), amp 0.2, k1 | **Y 200–290° 转门** | `sin·-150` | 线性 | **速度驱动运动模糊** | create+interpolate |
| V5 | sin, amp 0.05 窄, k0.9 | X 130–220° + Z 固定 −50 | `sin·-750` 深 | **holdAtMiddle 中点定格** | blur+brightness+**挤压拉伸** | create+holdAtMiddle |

**一句话总结整个项目**：
> 同一套舞台（父层 perspective + 子层 preserve-3d）+ 同一个核心戏（滚动 progress 驱动、旋转经过 0 在中央摆正）。
> 5 个 variation 只是在拧 6 类旋钮：① 旋转轴与幅度 ② sin 母函数的指数与深度 ③ 蛇形布局的振幅与频率 ④ 进度是否重映射 ⑤ 滤镜是位置驱动还是速度驱动 ⑥ 用 fromTo 还是手动 onUpdate。

---

## 附：8 道拷打题与正确答案

| # | 题 | 正确答案 | 依据章节 |
|---|---|---|---|
| 1 | perspective 是什么，删了只留 rotateX(60) 会怎样 | 控制眼睛离屏幕距离；删了旋转仍发生但没了近大远小（变正交投影） | 第 2 步 |
| 2 | 正对卡 rotateX/Y/Z(90°) 分别怎么动 | X=点头、Y=摇头/开门、Z=转圈 | 第 3 步 |
| 3 | rotationX +95→−95，progress 0.5 是几度、为何经过 0 | 0°正对；为了在屏幕中央摆正亮相再翻走 | 第 4 步 |
| 4 | sin 指数 1→4→8 凹陷曲线怎么变 | 越高越集中越尖锐（平时贴平，正中央猛扎） | 第 5 步 |
| 5 | V4 模糊被什么驱动，停下会怎样 | 速度驱动；停下后逐渐变清晰（带惯性） | 第 8 步 |
| 6 | progress 0.375~0.625 时 t=? 什么效果 | t 恒为 0.5；卡片在中央冻住/定格一段 | 第 7 步 |
| 7 | amplitude/系数各管什么，V3 不调用排成啥样 | amp=左右摆多宽、系数=摆多密；V3 竖直堆叠 | 第 6 步 |
| 8 | 为何 V3/4/5 不能用 fromTo | 它们的值是 progress 的非单调/耦合/重映射/速度函数，fromTo 只能两端点插值 | 第 9 步 |

> ⚠️ 自检提醒：你之前是**点选项**答对的，不算真懂。请把这 8 题盖住答案，自己用嘴/笔复述一遍，卡壳的地方回对应章节重读。

---

## 课题作业：Variation 6 —— 造一个属于你自己的旋转

**规则：禁止复制 V1–V5 的 JS。** `base.css` 和库可以用，旋转逻辑必须自己写。允许看不允许抄。

### Part A — 从零搭地基（概念 1–3）
- **M0｜纯 CSS 静态卡（不写 JS）**：新建 `index6.html` 放一张 `.gallery__item`，用 CSS 让它 `rotateX(55deg)` 且有正确透视（近边大、远边小）。
  ✅ 验收：是"被掀起的梯形"而非"被压扁的矩形"；能说出 perspective / preserve-3d 各放哪层。
- **M1｜接滚动**：引入 Lenis + ScrollTrigger，让这张卡随滚动 `rotationX` 从 +80° 经过 0 转到 −80°（`scrub:true`）。
  ✅ 验收：卡到屏幕中央时正对你。

### Part B — 复刻指定行为（概念 4、7、9）
- **M2｜20 张卡 + 蛇形 + 景深**：横向 `amplitude = innerWidth*0.12`、相位系数 `0.6`；景深 `z = sin(p·π)³·-400`。
  ⚠️ 陷阱：这步你还能用 fromTo 吗？自己判断（提示：z 是来回的，不能）。判断错 M2 不算过。

### Part C — 造你自己的第 6 种（概念 5/6/7 综合）
- **M3｜满足创新配额**（每类至少一个，且至少一个效果是耦合/非单调、必须 onUpdate 手算）：
  1. 一个非线性进度整形（自定义 `sin^k` 或你自己的 remap）。
  2. 一个 Y 轴或 Z 轴运用（不能只玩 X）。
  3. 一个滤镜（blur/brightness/saturate/挤压拉伸 任选）。
- **M4｜加分（概念 8 速度驱动）**：加一个读 `velocity`、用 `interpolate` 缓动追赶的效果，停下后能自己平复。

### 🔥 答辩拷打题（提交时逐条问）
1. perspective 从 900px 改成 200px 会怎样？为什么？
2. M2 的 z 系数 -400 改成 +400，卡片往哪走？
3. M3 里哪个效果绝对不能改写成 fromTo？为什么？
4. 相位系数 0.6 改成 6.28(≈2π)，20 张卡蛇形变成什么样？
5. 速度模糊里 `interpolate(blur,target,0.45)` 的 0.45 调成 0.05 / 1 各会怎样？

### 评分
| 档 | 标准 |
|---|---|
| 及格 | M0–M2 完成 + 地基题答对 |
| 良好 | + M3 配额满足 + 答辩 5 题对 4 |
| 优秀 | + M4 速度驱动 + 全部答辩对 + 能讲清每个旋钮取值动机 |
