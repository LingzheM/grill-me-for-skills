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

---

# NOTES — GraphRAG 轨

见 [MISSION-graphrag.md] / [learning-records/0002-graphrag-track-start.md]。

## 用户偏好（沿用 3D 轨）
- 中英混合，术语保留英文（TextUnit、Entity、Relationship、community、Leiden、map-reduce、embedding、provenance…）。
- 吃透原理 > 套用；喜欢被「拷打」+ 自己动手造。
- end goal = 从零重写 minimal GraphRAG；level = Python 熟 / RAG 浅碰。
- 成本敏感：小语料 + 便宜模型 + LLM cache 贯穿。

## 教学策略（针对此用户）
- 纵切交付：每个 milestone 端到端可跑可验收（见 roadmap）。
- 核心钩子：M0 造会失败的朴素 RAG 稻草人 → M5 用自写 global search 打败它。每课用它做 retrieval 锚点。
- 贯穿框架：indexing 6-phase + query 两路（local / global）。每课都回扣这张大图（interleaving）。
- RAG 基本功随用随补，不单独开「RAG 101」长课，嵌进 M0。

## 课程弧线（计划 = roadmap 的 milestone）
0. [路线图已出] reference/graphrag-build-roadmap.html — 项目是什么 + 8 个 milestone。
1. 下一课：M0 稻草人——亲手做朴素向量 RAG，眼见它在全局问题上失败。
2. M1 数据模型 + 管线骨架 → M2 图抽取 → M3 社区+报告 → M4 embedding → M5 query（闭环）→ M6 部署。

## 环境（已确认 2026-06-28）
- LLM = 本地 ollama 0.30.10。chat = `qwen2.5:7b`，embedding = `bge-m3`（两者已 pull）。Python 3.11.9。
- 语料 = 官方 A Christmas Carol（Gutenberg pg24022），naive_rag.py 首次运行自动下载。
- 代码项目目录：`graphrag-from-scratch/`。
- 成本无忧（本地跑），但仍用 cache + 小语料保持开发循环快。

## 进度
- [已出] Lesson M0 = `lessons/0002-graphrag-m0-strawman.html` + `graphrag-from-scratch/naive_rag.py`。
  等用户跑完、贴 Q3/Q4 实际答案 → 一起拆「烂在哪」→ 作为 M1 起点。
- 下一课：M1 数据模型 + 管线骨架。
