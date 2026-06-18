# NOTES — 教学偏好与工作笔记

## 用户偏好
- **语言**：中英混合。讲解用中文，专业术语保留英文原词（perspective、rotationX/Y/Z、scrub、progress、interpolate…）。代码注释可中英混。
- **学习目标类型**：吃透原理 > 套用。痛点是"无法独立决定该用什么，只能照抄"。所以每课都要落到**可迁移的决策**：给一个效果 → 该调哪个旋钮 / 哪条曲线。
- **作业风格**：喜欢被"拷打"。要有明确的、可自检的挑战，最终是自己从零造一个第 6 variation。

## 教学策略（针对此用户的诊断）
- 他有"抄 demo 的流利度幻觉"（fluency），但无 storage strength、无 transfer。
- 核心框架贯穿全程：**每个 variation = 旋钮(knobs) × 映射曲线(curves)**。把 5 个 variation 始终放进这张表里对比（interleaving）。
- 多用 retrieval practice：不要只让他读，要让他先预测/回答再揭晓。

## 课程弧线（计划）
1. [已出] The 3D Stage：perspective + preserve-3d + 三个旋转轴 + z。交互式滑块。
2. The Scroll Engine：ScrollTrigger + scrub + progress(0→1) + start/end。
3. The Mapping Layer：progress → 数值 的曲线库（sin/cos/pow/sign/interpolate/holdAtMiddle）。这是"为什么不同"的核心。
4. Decompose all 5：旋钮 × 曲线 对比大表（interleaving / 测验）。
5. 作业：设计并实现你自己的 Variation 6。
