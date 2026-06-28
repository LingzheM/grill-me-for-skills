# 02. GraphRAG 项目地图（七步法产出）

> 本文件是把 [`01-understand-lightrag.md`](./01-understand-lightrag.md) 的「七步扫描法」应用到 **微软 GraphRAG（v3.1.0）** 后抽取出的项目地图。
> 对象不是 LightRAG，而是 `graphrag/`（一个 `uv` monorepo）。供读完源码后对照。

---

## 0. 范围约定

GraphRAG 是 monorepo，有两个海拔：

- **应用层** `packages/graphrag` —— 业务主干（index / query / cli / api / config / data_model …）。
- **7 个基础设施包** —— `graphrag-cache`、`-chunking`、`-common`、`-input`、`-llm`、`-storage`、`-vectors`。

本地图**以应用层为主干**（第 1/5/6 步全在这里），把 7 个基础设施包**当成第 7 步的可插拔黑盒**，每个给一行契约，只在需要时拆开 `graphrag-llm`（最厚）。

---

## 1. 入口与启动路径

**一句话跑起来：**

```
graphrag init  --root ./x         # 生成配置 settings.yaml + prompts
# 放入文档到 ./x/input
graphrag index --root ./x         # 建索引（产出 parquet）
graphrag query --root ./x --method local "你的问题"
```

**调用链（CLI ↔ API 两层）：**

```
cli/main.py            typer app，注册 init/index/query/prompt_tune
  └─ cli/index.py      命令行外壳：参数解析、配置加载、stdout/进度
       └─ api/index.py 面向程序的稳定入口（library API，可被 notebook import）
            └─ index/run  真正的 pipeline
```

`cli/*` 与 `api/*` **一一对应**。职责边界：
- `cli/` 只管命令行外壳（argparse / 日志 / 进度），不含业务逻辑。
- `api/` 是**版本兼容承诺的边界**，纯函数式、不碰 stdout，返回结构化结果。
- 拆两层 = graphrag 既是 CLI 工具，又是可被 import 的 Python 库。

---

## 2. 分层与依赖方向

包之间是**单向 DAG，无环**：

```
L3 应用       packages/graphrag
                ↓ 依赖全部 7 个
L2 能力包      graphrag-llm  graphrag-input  graphrag-chunking
              graphrag-vectors  graphrag-cache
                （横向不互依，唯一例外 llm → cache：LLM 结果要缓存）
                ↓
L1 I/O 原语    graphrag-storage   （读写字节到 本地/blob/cosmos）
                ↓                  （cache、input 都建在它之上）
L0 地基        graphrag-common    （Factory 基类 / hasher / config；谁都不依赖）
```

- `common` = 稳定核心，定义全项目共享的抽象骨架。
- `storage` = 被复用的 I/O 原语，所以比 cache/input 低一层。

---

## 3. 核心骨架契约

抽象有三种风格：**ABC**、**Protocol**、**纯函数类型别名**。
项目里有 30+ 抽象，「拔掉就散架」的核心契约 8 个：

| 契约 | 位置 | 角色 |
|---|---|---|
| `Factory(ABC, Generic[T])` | common | 元抽象：所有可插拔点的母模式（单例 DI 容器） |
| `Storage(ABC)` | storage | 一切持久化的地基（L1） |
| `LLMCompletion` / `LLMEmbedding`（ABC） | llm | 所有 LLM 调用的契约 |
| `Cache(ABC)` | cache | LLM 结果缓存，决定成本与可重入 |
| `VectorStore(ABC)` | vectors | 读路径语义检索的地基 |
| `WorkflowFunction`（类型别名）+ `PipelineFactory` | index | 写路径骨架 |
| `BaseSearch(ABC, Generic[T])` | query | 读路径骨架（local/global/drift/basic 共同父类） |
| `WorkflowCallbacks`（Protocol） | callbacks | 贯穿整个 pipeline 的生命周期钩子 |

`MetricsWriter` / `Retry` / `RateLimiter` / `TemplateEngine` 等是 `graphrag-llm` 内部局部抽象，归入第 7 步黑盒，不进核心地图。

---

## 4. 数据模型（双形态）

系统里数据有**两种表现形态**，靠 adapter 互转：

- **写路径以 DataFrame/parquet 为主角**：每个 workflow 输入输出都是 pandas 表，落盘成
  `documents/text_units/entities/relationships/communities/community_reports.parquet`。
  `data_model/schemas.py` 定义列名，`row_transformers.py` 负责行↔对象转换。
- **读路径以 dataclass 为主角**：`query/indexer_adapters.py` 用 `read_indexer_*` 把 parquet 读回成对象喂给 context builder。

**领域实体图（dataclass 继承链）：**

```
Identified (id, short_id)
 ├─ Named (+title)
 │   ├─ Entity            (type, description, *_embedding, community_ids, text_unit_ids, rank)
 │   ├─ Document          (text, text_unit_ids)
 │   ├─ Community         (level, parent, children, entity_ids, relationship_ids …)
 │   └─ CommunityReport   (community_id, summary, full_content, full_content_embedding, rank)
 ├─ Relationship          (source, target, weight, description, *_embedding)
 ├─ TextUnit              (text, entity_ids, relationship_ids, covariate_ids, n_tokens, document_id)
 └─ Covariate             (subject_id, covariate_type="claim" …)
```

关系链：`Document → TextUnit →（Entity, Relationship, Covariate）→ Community → CommunityReport`，
embedding 内嵌在 Entity / Relationship / CommunityReport 上。

---

## 5. 写路径（index）

四条流水线注册在 `index/workflows/factory.py`：`Standard / Fast / StandardUpdate / FastUpdate`。
Standard 的 10 个 workflow 可归纳成 **5 个概念阶段**：

| 阶段 | workflow | 做什么 |
|---|---|---|
| ① 切块 | load_input_documents → create_base_text_units → create_final_documents | 读入文档，切成带 token 计数的 TextUnit |
| ② 抽图 | extract_graph → finalize_graph →（extract_covariates 可选） | LLM 抽实体+关系，去重/布局/打分，抽 claim |
| ③ 聚类成社区 | create_communities | Leiden 算法把实体图分层聚成 Community |
| ④ 社区摘要 | create_community_reports | LLM 为每个社区生成报告（global query 的核心资产） |
| ⑤ 向量化 | create_final_text_units → generate_text_embeddings | text/描述/报告生成 embedding 入向量库 |

**Standard vs Fast 的关键差异在 ②「抽图」：**
- Standard：`extract_graph` —— **LLM 抽实体关系**，贵/慢/质量高。
- Fast：`extract_graph_nlp` —— **NLP 名词短语抽取**（几乎不花 LLM 钱）+ `prune_graph` 清噪；社区报告也用纯文本版 `create_community_reports_text`。
- 取舍本质：**钱/时间 ↔ 图谱质量**。

Update 流水线 = 标准/快速流水线之后追加一组 `update_*` 增量合并 workflow。

---

## 6. 读路径（query）

四种 method 调用链结构同构：`api/query.{method}` → `query/factory.get_*_search_engine`
（组装 ContextBuilder + LLM）→ `BaseSearch.search()` → ContextBuilder 拼上下文 → LLM 生成答案。

本质区别在「用什么索引产物建上下文」：

| method | 主要消费 | 适合 | 用图? |
|---|---|---|---|
| **basic** | text_units 的 embedding | 简单事实问答（对照基线） | ❌ 纯向量 RAG |
| **local** | Entity 邻域（relationships / text_units / community_reports） | 关于某具体实体/局部 | ✅ |
| **global** | community_reports 做 **map-reduce** | 跨全语料的主题性/概览性问题（招牌能力） | ✅ |
| **drift** | 先 global 定方向，再 local 动态下钻 | 兼顾广度与深度 | ✅ |

一句话：**basic 不碰图；local 吃实体邻域；global 吃社区报告；drift 先 global 再 local。**

---

## 7. 可插拔点（扩展机制）

约 20 个 Factory，但分**两种风格**，对应两类插拔需求：

**A. 基础设施插拔点 —— `Factory(ABC)` DI 容器**（`graphrag-common`）
- `register(strategy, initializer, scope)` + `create(strategy, init_args)`；支持 `singleton`/`transient` 作用域，singleton 按 init_args 哈希缓存实例。
- 实现者（~17 个）：`storage / cache / vector_store / chunker / input_reader / tokenizer / completion / embedding / retry / rate_limit / metrics_* / template_*`。
- 为什么：这些是**有状态、需按 config 字符串选型并带参数实例化**的服务，需要 scope 与实例复用。

**B. workflow 插拔点 —— `PipelineFactory`（ClassVar 字典）**（`index/workflows/factory.py`）
- `workflows: dict[str, WorkflowFunction]` + `pipelines: dict[str, list[str]]`，全是 classmethod。
- 为什么：workflow 是**无状态函数**，只需「名字→函数」查表 + 「流水线=名字列表」编排，不需要 scope/实例缓存，类级字典即可。

**统一的设计哲学：**
> 有状态、需配置选型的东西 → **类 + 工厂容器（DI）**；
> 无状态的处理步骤 → **函数 + 名字注册表**。

这与第 3 步「写路径用函数 / 读路径用 ABC」的不对称**同源**。两种工厂的共性：都是「字符串 key → 实现」的注册表，都允许用户 `register` 自定义实现而**不改核心代码** —— 这就是 GraphRAG 的开放扩展点。

---

## 附：与 LightRAG 的架构差异（一句话）

| 维度 | LightRAG | GraphRAG |
|---|---|---|
| 形态 | 单包 | uv monorepo（应用 + 7 基础设施包） |
| 可插拔机制 | `STORAGES = {...}` 字典 | `Factory(ABC)` DI 容器 + `PipelineFactory` 字典（两种） |
| 写路径 | 函数式 pipeline | 注册式 workflow 函数链（4 条流水线） |
| 读路径 | mode（naive/local/global/hybrid） | BaseSearch 子类（basic/local/global/drift） |
| 数据形态 | KV/图/向量存储 | parquet 表（写）↔ dataclass（读） |
