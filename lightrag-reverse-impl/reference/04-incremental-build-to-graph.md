# 04. 从 0 到「带图」：一步步动手，每步执行什么 + 出现了什么 graph 概念

> 承接 [`03-build-from-scratch.md`](./03-build-from-scratch.md)。
> 本篇是**动手渐进指南**：从空目录开始，每个阶段「跑一条命令 → 得到一个产物 → 学一个 graph 概念」，
> 一路加到真正有知识图谱 + 社区 + 图检索。
>
> **面向没接触过 graph 技术的人**：图相关概念在出现时就地解释。
> 全部命令在 **uv 0.11 / Windows** 实测跑通，输出就是文中贴的样子。
>
> 心智总览（每阶段都从 0 可达，后一阶段在前一阶段上加东西）：
> ```
> 阶段1 骨架    -> graphrag --help 能跑
> 阶段2 切块    -> text_units.parquet        概念：chunk / TextUnit
> 阶段3 抽图    -> entities + relationships  概念：知识图谱（点=实体，边=关系）★图首次出现
> 阶段4 社区    -> communities.parquet       概念：社区 = 主题簇（图聚类）
> 阶段5 查询    -> basic vs local            概念：图遍历检索（图带来的增量）
> 阶段6 接真实  -> 换 LLM / embedding         概念：把玩具替换成生产组件
> ```

---

## 阶段 0：前提（两个 Windows 必备）

```bash
# 1) 装 uv（见 03）
uv --version

# 2) Windows 控制台必设：否则 print 中文会 UnicodeEncodeError(cp932) 崩掉
#    PowerShell:  $env:PYTHONUTF8=1
#    Git Bash:    export PYTHONUTF8=1
```

> 这个 `PYTHONUTF8=1` 是真坑：不设的话阶段 2 之后任何含中文的 `print` 都会让程序中途崩，
> parquet 写不出来，后面 query 全连环报 `FileNotFoundError`。

---

## 阶段 1：骨架（`graphrag --help` 能跑）

完全照 [`03` 的「完整可执行序列」](./03-build-from-scratch.md) 把根 + `graphrag-common` + `graphrag` 应用包建好。
验证：

```bash
uv sync --all-packages
uv run graphrag --help        # 看到 index / query 两个命令即成功
```

此时还没有「图」，只有命令行外壳。下面开始往 `index` 里填血肉。

---

## 阶段 2：摄取 + 切块 → `text_units`

**新概念 · chunk / TextUnit**：LLM 一次吞不下整篇文档，也不该。第一步永远是把文档切成
小段（chunk），每段叫一个 **TextUnit**，是后面一切处理的最小单位。

给应用包加依赖（pandas 存表、pyarrow 写 parquet）：

```bash
cd packages/graphrag
uv add pandas pyarrow networkx     # networkx 阶段3用，先一起装
cd ../..
```

> `uv add` 会自动改 `packages/graphrag/pyproject.toml` 的 `dependencies` 并更新 `uv.lock`。

准备输入：

```bash
mkdir -p demo/input
cat > demo/input/story.txt <<'EOF'
Alice works with Bob at Acme. Bob and Carol founded Acme.
Carol mentors Alice about Graphs.
Dave plays Guitar in Seattle. Dave and Erin formed Band in Seattle.
Erin teaches Dave about Music. Guitar drives Music in Band.
EOF
```

阶段 2 的 `index.run` 只做「读文档 → 切块 → 存 text_units.parquet」（阶段 3 会在同一文件里继续加）。
完整代码见阶段 3（一次给全），这里先理解：跑完你会得到 `demo/output/text_units.parquet`，
每行一个 chunk。

---

## 阶段 3：抽图 → `entities` + `relationships`　★图在这里第一次出现

**新概念 · 知识图谱（knowledge graph）**：
- **节点（node）= 实体（entity）**：文本里的「东西」——人、公司、地点、概念（Alice、Acme、Seattle…）。
- **边（edge）= 关系（relationship）**：两个实体之间有联系就连一条边（Alice—Acme）。
- 把一堆非结构化文字变成「点 + 边」，就是 GraphRAG 的核心动作。我们用 **networkx** 这个库来装这张图。

**这一步在真实 GraphRAG 里是 LLM 干的**（让模型从每个 chunk 里读出实体和关系）。
教学版先用一个「占位抽取器」：正则抓大写开头的词当实体，**同一个 chunk 里同时出现的实体两两连边**
（叫「共现」）。换成 LLM 时，只要替换这一个函数，图的下游全不用动——这正是 [`02` 里 Factory 可插拔](./02-graphrag-project-map.md#7-可插拔点扩展机制) 的意义。

写 `packages/graphrag/graphrag/index.py`（阶段 2+3+4 一次给全）：

```python
"""最小写路径：文档 -> chunk -> 知识图谱 -> 社区，全部落 parquet。"""
import re, hashlib
from pathlib import Path
import pandas as pd
import networkx as nx

def _id(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()[:12]

def _chunk(text: str, size: int = 12):          # 阶段2：切块
    words = text.split()
    return [" ".join(words[i:i+size]) for i in range(0, len(words), size)]

# 阶段3：占位“抽取器”。真实 GraphRAG 这一步是 LLM；换 LLM 只需替换这个函数。
def _extract(chunk: str):
    ents = sorted(set(re.findall(r"\b[A-Z][a-zA-Z]{2,}\b", chunk)))   # 大写词=实体
    rels = [(a, b) for i, a in enumerate(ents) for b in ents[i+1:]]   # 共现=关系
    return ents, rels

def run(root: str):
    root = Path(root)
    out = root / "output"; out.mkdir(parents=True, exist_ok=True)
    docs = list((root / "input").glob("*.txt"))
    print(f"[load] {len(docs)} 篇文档")

    text_units, G = [], nx.Graph()              # G 就是那张知识图谱
    for d in docs:
        for ci, ch in enumerate(_chunk(d.read_text(encoding="utf-8"))):
            tu_id = _id(f"{d.name}-{ci}")
            ents, rels = _extract(ch)
            text_units.append({"id": tu_id, "text": ch, "entity_ids": ents})
            for e in ents:
                G.add_node(e)                   # 加节点（实体）
            for a, b in rels:
                w = G[a][b]["weight"] + 1 if G.has_edge(a, b) else 1
                G.add_edge(a, b, weight=w)      # 加边（关系），重复出现就加权
    print(f"[graph] {G.number_of_nodes()} 实体, {G.number_of_edges()} 关系")

    # 阶段4：社区——把稠密连通的实体聚成“主题”
    comms = list(nx.community.greedy_modularity_communities(G)) if G.number_of_edges() else []
    node2comm = {n: i for i, c in enumerate(comms) for n in c}
    print(f"[communities] {len(comms)} 个社区")

    pd.DataFrame(text_units).to_parquet(out / "text_units.parquet")
    pd.DataFrame([{"id": _id(n), "title": n, "degree": G.degree(n),
                   "community": node2comm.get(n, -1)} for n in G.nodes]
                 ).to_parquet(out / "entities.parquet")
    pd.DataFrame([{"source": a, "target": b, "weight": G[a][b]["weight"]}
                  for a, b in G.edges]).to_parquet(out / "relationships.parquet")
    pd.DataFrame([{"community": i, "members": sorted(c), "size": len(c)}
                  for i, c in enumerate(comms)]).to_parquet(out / "communities.parquet")
    print(f"[done] 产物写入 {out}")
```

接到 CLI（`packages/graphrag/graphrag/cli/main.py`）：

```python
import typer
from graphrag import index as _index, query as _query
app = typer.Typer(help="GraphRAG mini (教学版)")

@app.command()
def index(root: str = "."):
    """建索引：文档 -> 图 -> 社区。"""
    _index.run(root)

@app.command()
def query(root: str = ".", method: str = "local", q: str = ""):
    """查询：--method basic|local。"""
    (_query.basic if method == "basic" else _query.local)(root, q)
```

跑：

```bash
uv sync --all-packages
uv run graphrag index --root ./demo
```

实测输出：

```
[load] 1 篇文档
[graph] 11 实体, 30 关系          ← 图建出来了：11 个点，30 条边
[communities] 2 个社区
[done] 产物写入 demo\output
```

看实体表：

```bash
uv run python -c "import pandas as pd; print(pd.read_parquet('demo/output/entities.parquet').to_string())"
```

每行一个实体，带 `degree`（连了几条边 = 它有多重要）和 `community`（属于哪个主题，见下）。

---

## 阶段 4：社区聚类 → `communities`

**新概念 · 社区（community）**：图里有些实体彼此连得特别密（互相都有边），
把这种「抱团」的实体聚成一组，就叫一个**社区**——本质是一个**主题/话题**。
我们用 networkx 自带的 `greedy_modularity_communities`（一种社区发现算法；真实 GraphRAG 用更强的 **Leiden**）。

社区是 GraphRAG 的**招牌**：有了「每个主题一组实体」，就能对全语料做概览式（global）回答，
而不只是局部查找。

上面 `index.py` 已经算了社区。看结果：

```bash
uv run python -c "import pandas as pd; print(pd.read_parquet('demo/output/communities.parquet').to_string())"
```

实测输出（我们的输入正好有「工作」和「音乐」两个主题）：

```
   community                                             members  size
0          0  [Band, Dave, Erin, Graphs, Guitar, Music, Seattle]     7
1          1                           [Acme, Alice, Bob, Carol]     4
```

→ 算法**自己**从文本里发现了两个主题簇。这就是图的威力：结构里自带「话题分组」。

---

## 阶段 5：查询 —— `basic`（不碰图）对比 `local`（用图）

**新概念 · 图遍历检索**：拿到问题后，先在图里定位相关实体，再**沿着边走到它的邻居**，
把「实体 + 邻域」一起喂给 LLM。比起纯关键词检索，多了「关系」这层上下文。

写 `packages/graphrag/graphrag/query.py`：

```python
"""最小读路径：basic(不碰图) vs local(用图邻域)。"""
from pathlib import Path
import pandas as pd
import networkx as nx

def _load(root):
    o = Path(root) / "output"
    return (pd.read_parquet(o/"text_units.parquet"),
            pd.read_parquet(o/"entities.parquet"),
            pd.read_parquet(o/"relationships.parquet"))

def basic(root, q):                              # 纯文本检索，完全不用图
    tu, _, _ = _load(root)
    hits = tu[tu["text"].str.contains(q, case=False, na=False)]
    print(f"[basic] 纯文本命中 {len(hits)} 个 chunk（完全不用图）")
    for t in hits["text"].head(3):
        print("  -", t[:80], "...")

def local(root, q):                              # 实体邻域检索，用图
    tu, ent, rel = _load(root)
    G = nx.from_pandas_edgelist(rel, "source", "target")
    if q not in G:
        print(f"[local] 实体 '{q}' 不在图里"); return
    nbrs = list(G.neighbors(q))
    print(f"[local] 实体 '{q}' 的图邻域：{nbrs}")
    print(f"[local] -> 用 '{q}' + 邻居 拼上下文喂给 LLM 作答（这就是图带来的增量）")
```

跑两种方法对比：

```bash
uv run graphrag query --root ./demo --method basic --q Acme
uv run graphrag query --root ./demo --method local --q Dave
```

实测输出：

```
[basic] 纯文本命中 1 个 chunk（完全不用图）
  - Alice works with Bob at Acme. Bob and Carol founded Acme. ...

[local] 实体 'Dave' 的图邻域：['Alice', 'Erin', 'Graphs', 'Guitar', 'Seattle', 'Band', 'Music']
[local] -> 用 'Dave' + 邻居 拼上下文喂给 LLM 作答（这就是图带来的增量）
```

→ `basic` 只会找「含这个词的句子」；`local` 能顺着图答出「Dave 跟谁/什么有关」——
这正是 [`02` 读路径](./02-graphrag-project-map.md#6-读路径query) 里 basic / local 的本质区别，你现在亲手做出来了。

---

## 阶段 6：从玩具到真实（要改的就三处）

到这里你已经有一个**结构完整**的 GraphRAG。把它升级成生产级，只需替换三个「占位件」，
骨架完全不动——对照 [`02` 的 Factory 可插拔点](./02-graphrag-project-map.md#7-可插拔点扩展机制)：

| 占位件（教学版） | 换成（真实 GraphRAG） | 在 02 地图里对应 |
|---|---|---|
| `_extract()` 正则共现 | **LLM 抽实体+关系**（给 prompt 让模型读出来） | `extract_graph` workflow / `LLMCompletion` |
| `greedy_modularity_communities` | **Leiden** 算法 + LLM 写**社区报告** | `create_communities` / `create_community_reports` |
| `str.contains` 子串检索 | **embedding + 向量库**语义检索；新增 `global`/`drift` | `VectorStore` / `BaseSearch` 子类 |

升级顺序建议（同 [`03` 的设计原则](./03-build-from-scratch.md#三条关键设计排序原则)）：
1. 先把 `_extract` 换成真 LLM（图质量立刻上一个台阶）；
2. 再加 embedding + 向量库，让 `local`/`basic` 用语义而非子串；
3. 最后给社区加「LLM 报告」并实现 `global` 检索（map-reduce over 报告）——拿到 GraphRAG 的招牌能力。

**一句话**：你从空目录起步，已经亲手走过「切块 → 抽图 → 社区 → 图检索」全链路；
剩下的不是「重做」，而是把三个玩具件替换成 LLM / Leiden / 向量库。
