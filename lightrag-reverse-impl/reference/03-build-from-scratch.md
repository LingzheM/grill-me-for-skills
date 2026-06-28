# 03. 从 0 构建：uv monorepo + GraphRAG 的设计顺序

> 承接 [`02-graphrag-project-map.md`](./02-graphrag-project-map.md)。
> 上一篇回答「graphrag 长什么样」，本篇回答两个问题：
> ① 没用过 uv，怎么从 0 搭出这种多包单仓？
> ② 如果让我重新设计 graphrag，从哪部分开始？

---

## 一、没用过 uv，怎么从 0 搭出这种 monorepo

**uv 是什么**：Rust 写的 Python 包/项目管理器，一把替掉 `pip + venv + pip-tools + poetry`。
对这个项目最关键的两个能力：**workspace（多包单仓）** 和 **lockfile（`uv.lock` 锁全仓依赖）**。

### 0. 装 uv

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

uv --version
```

### 1. 建仓库根（workspace 根，本身不是包）

graphrag 根 `pyproject.toml` 的「根」身份就靠这三段：

```toml
[tool.uv]
package = false                      # 根目录不打包，只是个容器
[tool.uv.workspace]
members = ["packages/*"]             # 所有成员包从这里扫
```

操作：

```bash
mkdir graphrag && cd graphrag
git init
uv init --bare        # 生成最小 pyproject，再手动补上上面两段
```

### 2. 建第一个成员包（先建地基 graphrag-common）

```bash
uv init --lib packages/graphrag-common --name graphrag-common
```

每个成员都是**独立的可发布包**：自己的 `pyproject.toml` + `[build-system]`（graphrag 用 hatchling）+ 自己的 `dependencies`。
`graphrag-common` 不依赖任何兄弟包，所以依赖里只有 `pyyaml / toml / python-dotenv`。

```toml
# packages/graphrag-common/pyproject.toml（节选）
[project]
name = "graphrag-common"
version = "3.1.0"
requires-python = ">=3.11,<3.14"
dependencies = ["python-dotenv~=1.0", "pyyaml~=6.0", "toml"]

[build-system]
requires = ["hatchling>=1.27.0,<2.0.0"]
build-backend = "hatchling.build"
```

### 3. 让上层包依赖兄弟包 —— workspace 的精髓

比如 `graphrag-cache` 要用 `graphrag-common`，两步：

**成员**里正常声明依赖：

```toml
# packages/graphrag-cache/pyproject.toml
dependencies = ["graphrag-common==3.1.0", "graphrag-storage==3.1.0"]
```

**根**里告诉 uv「这个依赖来自本地 workspace，别去 PyPI 找」：

```toml
# 根 pyproject.toml
[tool.uv.sources]
graphrag-common  = { workspace = true }
graphrag-storage = { workspace = true }
graphrag-cache   = { workspace = true }
# ... 每个内部包登记一行
```

这就是仓库里那一坨 `[tool.uv.sources]` 的作用。

### 4. 一条命令装好整个 workspace

```bash
uv sync                      # 解析全部成员 + 写 uv.lock + 建 .venv
uv run graphrag --help       # 在 venv 里跑 console_scripts 入口
```

内部包之间是 **editable（可编辑）安装**：改 `graphrag-common` 的源码，`graphrag-cache` 立刻看到，不用重装。

### 5. 任务编排用 poe

uv 不管「跑测试 / 格式化」这类任务，graphrag 用 `poethepoet`（根 `[tool.poe.tasks]`）：

```bash
uv run poe test
uv run poe check     # ruff + pyright
uv run poe build
```

### 心智模型（一句话）

> 根 = 容器（`package=false` + `members` + `sources`）；
> 每个 `packages/*` = 独立包；
> `uv sync` 把它们当一个整体解析并 editable 安装；`uv.lock` 锁全仓。

### 最小可跑骨架的目录

```
graphrag/
├─ pyproject.toml              # 根：package=false + workspace + sources
├─ uv.lock
└─ packages/
   ├─ graphrag-common/
   │  ├─ pyproject.toml
   │  └─ graphrag_common/__init__.py
   └─ graphrag/
      ├─ pyproject.toml        # [project.scripts] graphrag = "graphrag.cli.main:app"
      └─ graphrag/cli/main.py
```

### 完整可执行序列：从空目录到第一次 `graphrag` 跑起来（已实测 uv 0.11）

> 上面 0~5 节是讲解，下面是**一条可整段复制**的命令流。建包用 `uv init`，
> 然后把 pyproject / 源码写成下面的内容即可。

```bash
# 0. 空目录起步
mkdir graphrag && cd graphrag && git init

# 1. 根 pyproject.toml（容器，不是包）
cat > pyproject.toml <<'EOF'
[project]
name = "graphrag-monorepo"
version = "0.0.0"
requires-python = ">=3.11"

[tool.uv]
package = false

[tool.uv.workspace]
members = ["packages/*"]

[tool.uv.sources]
graphrag-common = { workspace = true }
EOF

# 2. 地基包 graphrag-common
mkdir -p packages/graphrag-common/graphrag_common
cat > packages/graphrag-common/pyproject.toml <<'EOF'
[project]
name = "graphrag-common"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
EOF
echo '__version__ = "0.1.0"' > packages/graphrag-common/graphrag_common/__init__.py

# 3. 应用包 graphrag（带 CLI 入口，依赖 common）
mkdir -p packages/graphrag/graphrag/cli
cat > packages/graphrag/pyproject.toml <<'EOF'
[project]
name = "graphrag"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["graphrag-common==0.1.0", "typer>=0.12"]

[project.scripts]
graphrag = "graphrag.cli.main:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
EOF
: > packages/graphrag/graphrag/__init__.py
: > packages/graphrag/graphrag/cli/__init__.py
cat > packages/graphrag/graphrag/cli/main.py <<'EOF'
import typer
app = typer.Typer(help="GraphRAG mini skeleton")

@app.command()
def index(root: str = "."):
    """建索引（占位）。"""
    typer.echo(f"index root={root}")

@app.command()
def query(root: str = ".", q: str = ""):
    """查询（占位）。"""
    typer.echo(f"query root={root} q={q}")
EOF

# 4. 一键装 + 跑（注意 --all-packages，见下方坑）
uv sync --all-packages
uv run graphrag --help
uv run graphrag index --root ./demo      # -> index root=./demo
```

> ⚠️ **唯一的坑**：根是 `package = false` 的「虚拟 workspace」时，
> 普通 `uv sync` **不会把成员装进环境**，裸 `uv run graphrag` 会报
> `error: Failed to spawn: graphrag program not found`。两种解法：
> - `uv sync --all-packages`（推荐，把所有成员都装进 venv）；
> - 或临时 `uv run --package graphrag graphrag --help`（只按需构建该包）。
>
> 真实的 graphrag 仓库根 `[project]` 里把 7 个成员都列进了依赖，所以它不需要这个标志；
> 你自己起步时最省事的就是 `uv sync --all-packages`。

**graphrag 从哪里「开始」？** 就是上面第 3 步那个 `[project.scripts]` 入口 +
`cli/main.py`——`graphrag = "graphrag.cli.main:app"` 把命令行 `graphrag` 绑到 typer 的 `app`。
往后所有 `index/query/init` 命令都在这个 `app` 上加 `@app.command()` 长出来。

---

## 二、如果让我设计 graphrag，从哪部分开始

先分清一个常被混淆的点：**「搭骨架的顺序」≠「验证价值的顺序」**，两者方向相反，都重要。

### 路线 A：自底向上（按依赖 DAG，工程稳健）

就是仓库现在的分层顺序，先有地基才能往上垒：

```
1. graphrag-common   先定 Factory 基类 + config 加载    ← 一切的元抽象
2. graphrag-storage  Storage(ABC) + 本地文件实现         ← 数据落得下去
3. 能力包            llm / chunking / input / vectors / cache（可横向并行）
4. packages/graphrag 应用层：data_model → index → query
```

- 优点：每层都能独立测试，依赖永远朝下。
- 缺点：做到第 4 步才第一次看到端到端效果，前期没有可演示的东西。

### 路线 B：垂直切片（先打通最细的端到端，验证价值）—— 推荐新项目这样起步

先证明「图 RAG 比普通 RAG 强」这个核心假设，再回头补强：

1. **最小数据模型**：只定 `Entity / Relationship / TextUnit` 三个 dataclass（先别碰 Community）。
2. **最小写路径**：切块 → LLM 抽实体关系 → 存 parquet。**砍掉**社区聚类、covariate、embedding。
3. **最小读路径**：先做 `basic`（纯向量 RAG）当**基线**，再做 `local`（实体邻域）证明图带来的增量。
4. 跑通后**再加招牌**：`create_communities`（Leiden）+ `create_community_reports` + `global` 检索——这才是 GraphRAG 区别于普通 RAG 的护城河。
5. 最后才把 storage / cache / llm 抽象成可插拔的 Factory。

### 三条关键设计排序原则

1. **先定契约，后填实现**
   `graphrag-common` 的 `Factory` 和 `Storage(ABC)` 必须最先定——它们是所有人 import 的前提。路线 A、B 一致。

2. **抽象点要「延迟提取」（避免过度设计）**
   那 ~20 个 Factory 不是一开始就有的。先硬编码本地文件存储，等真的要接 blob/cosmos 时，再抽成 `Storage(ABC)` + 工厂。
   **GraphRAG 现在的工厂体系是演化出来的，不是一次设计出来的。** 抽象应等到有 2 个以上实现需求时再提取。

3. **写路径先于读路径；读路径里 basic → local → global**
   没有索引产物就没法查；读路径复杂度递增，且 basic 给你一个对照基线。

### 一句话总结

> 骨架按依赖**自底向上**（common → storage → 能力 → 应用）；
> 价值按**垂直切片**先打通「切块 → 抽实体 → local 查」最细一条线；
> 确认图 RAG 有效后再加社区 / global 招牌，**最后**才把基础设施抽象成可插拔工厂。
