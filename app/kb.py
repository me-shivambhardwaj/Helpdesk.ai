"""Knowledge base: load help docs, chunk them, store in ChromaDB, retrieve."""
import glob
import os
import chromadb
from .config import CHROMA_DIR, KB_DIR

_col = None


def collection():
    global _col
    if _col is None:
        c = chromadb.PersistentClient(path=CHROMA_DIR)
        _col = c.get_or_create_collection("support_kb", metadata={"hnsw:space": "cosine"})
    return _col


def chunk(text: str, size: int = 800, overlap: int = 100):
    out, start = [], 0
    while start < len(text):
        out.append(text[start:start + size])
        start += size - overlap
    return out


def ingest() -> int:
    ids, docs, metas = [], [], []
    for path in glob.glob(f"{KB_DIR}/*.md"):
        name = os.path.basename(path)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        for i, c in enumerate(chunk(text)):
            ids.append(f"{name}-{i}")
            docs.append(c)
            metas.append({"source": name})
    if ids:
        collection().upsert(ids=ids, documents=docs, metadatas=metas)
    return len(ids)


def retrieve(query: str, k: int = 4):
    res = collection().query(query_texts=[query], n_results=k)
    return [
        {"text": d, "source": m["source"], "distance": dist}
        for d, m, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])
    ]
