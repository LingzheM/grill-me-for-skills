# RESOURCES

高质量、高信任来源。每节课的主推来源（primary source）从这里挑。

## 主来源（Primary）

- **[Codrops — Exploring 3D Image Rotations on Scroll](https://tympanus.net/codrops/?p=116660)** ⭐
  by Manoela Ilic (2026-06-18)。**就是我们正在拆的这个项目**的官方文章，含 demo + GitHub。
  → 整体动机与作者思路的第一来源。

- **[MDN — Using CSS transforms](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_transforms/Using_CSS_transforms)** ⭐
  3D transform 的权威入门：perspective、transform-style、rotate3d、translateZ。
  → Lesson 1（The 3D Stage）主来源。

- **[GSAP — ScrollTrigger Docs](https://gsap.com/docs/v3/Plugins/ScrollTrigger/)** ⭐ (v3.15)
  scrub、start/end、onUpdate、self.progress（0=start, 0.5=middle, 1=end）的权威定义。
  → Lesson 2（The Scroll Engine）主来源。

## 参考（Reference）

- [MDN — `perspective`](https://developer.mozilla.org/en-US/docs/Web/CSS/perspective)
- [MDN — `transform-style`](https://developer.mozilla.org/en-US/docs/Web/CSS/transform-style)
- [MDN — `Math.sin` / `Math.cos`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Math)
- [GSAP — `gsap.utils.interpolate` / `mapRange`](https://gsap.com/docs/v3/GSAP/UtilityMethods/)
- [Lenis (smooth scroll)](https://github.com/darkroomengineering/lenis)

## 社区（Wisdom — 测真本事的地方）

- [GreenSock Forums](https://gsap.com/community/) — GSAP 官方论坛，作者们会答 ScrollTrigger 问题。
- [Codrops 文章评论区 / Tympanus](https://tympanus.net/codrops/) — 同类效果的作者社群。
- r/Frontend, r/webdev — 贴 CodePen 求反馈。

---

# RESOURCES — GraphRAG 轨

见 [MISSION-graphrag.md]。目标：从零重写一条最小 GraphRAG 管线。

## 主来源（Primary）

- **[GraphRAG 论文 — arXiv 2404.16130](https://arxiv.org/pdf/2404.16130)** ⭐
  方法论第一来源。重点：community 检测 + global search 的 map-reduce 设计。
- **[官方文档站](https://microsoft.github.io/graphrag/)** ⭐ + 本地 `graphrag/docs/`
  - `docs/index/default_dataflow.md` — 6-phase indexing 管线（最重要）。
  - `docs/index/architecture.md` — Knowledge Model、LLM cache、factory/provider 模式。
  - `docs/query/global_search.md` / `docs/query/local_search.md` / `docs/query/drift_search.md`。
  - `docs/get_started.md` — CLI 端到端 quickstart（A Christmas Carol 语料）。
- **[MS Research 博客](https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/)** — 动机与直觉的科普版。

## 参考（Reference）

- 本地源码 `graphrag/packages/` — 每个 milestone 写之前先读官方对应实现作对照。
- 本地 `graphrag/.../prompts/` — entity-extraction / community-report 等真实 prompt 模板。
- `LightRAG/` + `lightrag-reverse-impl/` — 同类系统的精简实现，重写时的「参考答案」。
- [networkx](https://networkx.org/) · [graspologic hierarchical_leiden](https://graspologic.readthedocs.io/)（官方社区检测）· [leidenalg](https://leidenalg.readthedocs.io/)（替代）· [lancedb](https://lancedb.github.io/lancedb/)（轻量向量库）。

## 社区（Wisdom）

- [microsoft/graphrag GitHub Discussions](https://github.com/microsoft/graphrag/discussions) — 官方答疑，重写遇坑可搜。
- r/LocalLLaMA, r/Rag — 贴自己的重写实现求反馈。
