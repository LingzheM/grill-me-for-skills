# Mission: 吃透 3D-rotations 项目（滚动驱动的 3D 卡片旋转）

## Why
用户能照抄 GSAP / CSS demo，但给一个新效果时无法独立思考"该用什么"——只能复制。
真正目标是建立**可迁移的心智模型**：看懂 `3D-rotations/RotatingOnScrollAnimations` 里 5 个 variation
的旋转为什么不同、怎么实现，从而能反过来**自己设计**一个新的滚动 3D 效果，而不是抄。

## Success looks like
- 能说清一张卡片在网页里"如何被表示成 3D"：`perspective`（在父层）+ `transform-style: preserve-3d`，以及 rotationX / rotationY / rotationZ / z 各自是什么轴。
- 能把任意一个 variation 拆成两层：**旋钮**（转哪些轴、z 多深、加什么 filter）+ **映射曲线**（progress 0→1 经过 sin/cos/pow/interpolate/holdAtMiddle 变成数值）。
- 给一个目标"感觉"（如"像门一样转 + 快速滚动时模糊"），能指出要调哪几个旋钮和曲线——这正是 5 个 variation 的差异本质。
- 最终能**从零设计并实现一个第 6 个 variation**，并讲清每个选择的理由。

## Constraints
- 前端新手：transform / GSAP 都"浅碰过"，知道 scroll/to/from 但不懂原理。
- 课程语言：中英混合（术语保留英文：perspective、rotationX、scrub、progress…）。
- 偏好"拆解 + 自己造一个新变体"式的作业，要被"拷打"到真正掌握。

## Out of scope（暂不追）
- 复杂 GSAP timeline 编排、SVG/Canvas/WebGL 3D、React 集成、性能深挖。
- 重写 Lenis / ScrollTrigger 内部原理（只需会用 + 懂 scrub/progress 的契约）。
