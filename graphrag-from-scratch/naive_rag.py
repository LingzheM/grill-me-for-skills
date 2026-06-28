"""
M0 · 稻草人：朴素向量 RAG (naive vector RAG)
------------------------------------------------
目标：建立 baseline，亲眼看它「答对局部问题、答砸全局问题」。
这就是后面 M1~M5 要打败的稻草人。

依赖：pip install ollama numpy
模型：本地 ollama —— 嵌入 bge-m3，对话 qwen2.5:7b
语料：官方 quickstart 同款 A Christmas Carol（首次运行自动下载）
"""
import os
import urllib.request
import numpy as np
import ollama

BOOK_URL = "https://www.gutenberg.org/cache/epub/24022/pg24022.txt"
BOOK_PATH = "input/book.txt"
CACHE_PATH = "cache/chunks.npz"

EMBED_MODEL = "bge-m3"
CHAT_MODEL = "qwen2.5:7b"

CHUNK_SIZE = 1200      # 先用「字符数」粗略近似 token，够 M0 用
CHUNK_OVERLAP = 100    # 相邻 chunk 重叠，避免把句子拦腰切断
TOP_K = 5              # 检索召回多少个 chunk 塞进 prompt —— 故意留作旋钮


def ensure_book() -> str:
    """没有书就下载；返回去掉 Gutenberg 页眉页脚后的正文。"""
    os.makedirs("input", exist_ok=True)
    if not os.path.exists(BOOK_PATH):
        print("下载 A Christmas Carol ...")
        urllib.request.urlretrieve(BOOK_URL, BOOK_PATH)
    text = open(BOOK_PATH, encoding="utf-8").read()
    start = text.find("MARLEY")          # 正文起点附近
    end = text.find("END OF THE PROJECT GUTENBERG")
    return text[start:end] if start != -1 and end != -1 else text


def chunk_text(text: str) -> list[str]:
    """最朴素的定长切块（带 overlap）。这就是 naive RAG 的『切』。"""
    chunks, i = [], 0
    while i < len(text):
        chunks.append(text[i:i + CHUNK_SIZE])
        i += CHUNK_SIZE - CHUNK_OVERLAP
    return [c.strip() for c in chunks if c.strip()]


def embed(texts: list[str]) -> np.ndarray:
    """逐条调用 ollama 的 bge-m3 拿向量。"""
    vecs = [ollama.embeddings(model=EMBED_MODEL, prompt=t)["embedding"] for t in texts]
    return np.array(vecs, dtype=np.float32)


def build_index() -> tuple[list[str], np.ndarray]:
    """切块 + 全量 embedding，结果缓存到磁盘（重跑就不再烧算力）。"""
    os.makedirs("cache", exist_ok=True)
    if os.path.exists(CACHE_PATH):
        d = np.load(CACHE_PATH, allow_pickle=True)
        return list(d["chunks"]), d["vecs"]
    chunks = chunk_text(ensure_book())
    print(f"chunk 数：{len(chunks)}，开始 embedding（bge-m3）...")
    vecs = embed(chunks)
    np.savez(CACHE_PATH, chunks=np.array(chunks, dtype=object), vecs=vecs)
    return chunks, vecs


def cosine_topk(qvec: np.ndarray, vecs: np.ndarray, k: int):
    """归一化后点积 = cosine 相似度，取最高的 k 个。"""
    a = qvec / (np.linalg.norm(qvec) + 1e-9)
    b = vecs / (np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9)
    sims = b @ a
    idx = np.argsort(-sims)[:k]
    return idx, sims[idx]


def answer(query: str, chunks: list[str], vecs: np.ndarray) -> None:
    """naive RAG 全流程：embed query → 检索 top-k → 塞 prompt → LLM 答。"""
    qvec = embed([query])[0]
    idx, sims = cosine_topk(qvec, vecs, TOP_K)
    context = "\n\n---\n\n".join(f"[chunk {i}] {chunks[i]}" for i in idx)
    prompt = (
        "只依据下面的上下文回答问题。若上下文不足以回答，就直说不知道。\n\n"
        f"上下文：\n{context}\n\n问题：{query}\n答案："
    )
    resp = ollama.chat(model=CHAT_MODEL, messages=[{"role": "user", "content": prompt}])
    print("\n" + "=" * 70)
    print(f"问题：{query}")
    print(f"命中 chunks：{list(idx)}（top-{TOP_K}，相似度 {np.round(sims, 3).tolist()}）")
    print("答案：", resp["message"]["content"].strip())


if __name__ == "__main__":
    chunks, vecs = build_index()

    # —— 局部问题：答案集中在书里某几处，naive RAG 擅长 ——
    answer("Who is Ebenezer Scrooge and what is he like?", chunks, vecs)
    answer("What does Marley's ghost say to Scrooge?", chunks, vecs)

    # —— 全局问题：需要纵观全书，没有哪几个 chunk 能代表全局 → 翻车 ——
    answer("What are the main themes of the whole book?", chunks, vecs)
    answer("How does Scrooge's character transform across the whole story, step by step?", chunks, vecs)
