# Mission: 吃透 GraphRAG —— 能从零重写一条最小管线

> 注：这是 graphrag 学习轨。3D-rotations 轨的 mission 见 [MISSION.md]（不动它）。

## Why
用户能用现成 RAG/包，但对 GraphRAG「为什么这么设计、每一步在解决什么问题」没有可迁移的理解。
真正目标是用「重写」来吃透：不靠 microsoft/graphrag 这个包，自己用 Python 实现一条精简版的
indexing + query 管线（沿用其 lightrag-reverse-impl 的「逆向重写以理解」习惯）。
终点不仅是懂，而是能**指导一个 junior 从 0 设计→实现→搭建→部署可运行**。

## Success looks like
- 能讲清 GraphRAG 与普通向量 RAG 的本质差异：community reports + global map-reduce 才能答「全局问题」。
- 能画出 6-phase indexing 管线，并说清每个 phase 在解决什么、产物是什么（Knowledge Model）。
- 能从零实现并跑通：`index`（chunk→抽图→合并摘要→社区→报告→embedding）+ `query`（local / global）。
- 亲手做的 baseline（M0 稻草人）在全局问题上失败，自己实现的 global search 把它打败（M5 闭环）。
- 能打包 + 容器化部署，在干净机器上 init→index→query 跑通（M6）。
- 给一个新需求，能判断「该用 local 还是 global、该 embed 什么、社区取哪层」——可迁移决策。

## Constraints
- 底子：Python 熟；RAG/LLM 浅碰（向量检索、embedding、抽取 prompt 等需随用随补）。
- 语言：中英混合，术语保留英文（TextUnit、Entity、Relationship、community、Leiden、map-reduce、embedding、provenance…）。
- 偏好：拆解 + 自己动手造，要被「拷打」到真正掌握（沿用 3D 轨的教学风格）。
- 成本敏感：GraphRAG 极耗 LLM，所有练习用小语料 + 便宜模型 + cache。

## 路线图
见 [reference/graphrag-build-roadmap.html] —— M0 稻草人 → M5 打败它 → M6 部署。

## Out of scope（MVP 阶段不追）
- 复刻官方全部 workflow 编排、claims/covariates、DRIFT、增量索引（放 M7 stretch）。
- 大规模/分布式索引、Azure 全家桶、企业级鉴权。
