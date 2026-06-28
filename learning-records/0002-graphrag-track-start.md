# 新轨开启：GraphRAG（重写以理解），起点 = Python 熟 / RAG 浅碰

3D-rotations 轨告一段落，用户开新轨：**graphrag**。通过 `/teach` 给出诉求——
「这个项目是什么 + 如果指导一个 junior，从 0 设计/实现/搭建/部署可运行，分阶段分 milestone」。

## 诊断（决定教什么 / ZPD）
- 用户自选：end goal = **自己从零重写一个 GraphRAG**（非「跑官方包」、非「只理解不动手」）。
  → 这与他 workspace 里已有的 `lightrag-reverse-impl` 习惯一致：逆向重写来吃透。
- 用户自选：level = **Python 熟，RAG/LLM 浅碰**。
  → 不能从「装 graphrag 包」教起；要从 RAG 基本功（chunk/embed/检索）随用随补，
    但管线工程对他不是障碍，可大胆纵切到 LLM 抽取与 map-reduce。

## 教学决策
- 路线图按「纵切」设计：每个 milestone 都端到端可跑、可验收。见 [reference/graphrag-build-roadmap.html]。
- 核心钩子：**M0 先造会失败的稻草人（朴素向量 RAG）→ M5 用自己写的 global search 打败它**。
  这个反差就是用户对 GraphRAG 价值的「可迁移理解」，也是后续每课的 retrieval 锚点。
- 贯穿框架：indexing 6-phase（chunk→抽图→合并/摘要→社区→报告→embedding）+ query 两路（local / global）。
- 沿用 3D 轨风格：中英混合、被「拷打」、自己动手造。见 [MISSION-graphrag.md]。

## 待定 / 下一步
- 首课从 M0 起。需确认用户实验语料与可用 LLM（OpenAI key？本地模型？）——影响成本与 M0 代码。
