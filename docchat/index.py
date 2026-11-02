"""Векторний індекс: ембединги шматків + пошук по змісту.

Ембединг - це набір чисел, що описує зміст тексту. Тексти з близьким
змістом мають близькі числа, тому пошук працює за змістом, а не за словами.
Усе виконується локально, інтернет потрібен лише для першого завантаження моделі.
"""

from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from .chunker import Chunk
from .context import merge_blocks

# Багатомовна модель, розуміє українську. Завантажується один раз (~0.5 ГБ).
# ВАЖЛИВО: після зміни моделі індекс треба перебудувати (видали папку db).
MODEL_NAME = "intfloat/multilingual-e5-small"
DB_PATH = Path("db")
COLLECTION = "documents"

_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"Завантажую модель {MODEL_NAME} ...")
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def get_collection():
    client = chromadb.PersistentClient(path=str(DB_PATH))
    # cosine: порівнюємо напрямок векторів, а не їхню довжину
    return client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})


def is_indexed(source: str) -> bool:
    found = get_collection().get(where={"source": source}, limit=1)
    return len(found["ids"]) > 0


def list_indexed_sources() -> list[str]:
    """Назви всіх документів, які вже є в базі."""
    metadatas = get_collection().get(include=["metadatas"])["metadatas"]
    return sorted({m["source"] for m in metadatas})


def index_chunks(chunks: list[Chunk], batch_size: int = 32, on_progress=None) -> None:
    """Рахує ембединги й зберігає шматки в базу.

    on_progress(зроблено, всього) - необов'язкова функція для індикатора прогресу.
    Без неї прогрес друкується в консоль.
    """
    model = get_model()
    collection = get_collection()

    total = len(chunks)
    for start in range(0, total, batch_size):
        batch = chunks[start:start + batch_size]
        # модель e5 вимагає префікс "passage: " для документів
        vectors = model.encode(
            [f"passage: {c.text}" for c in batch],
            normalize_embeddings=True,
        ).tolist()
        collection.add(
            ids=[f"{c.source}-{start + i}" for i, c in enumerate(batch)],
            embeddings=vectors,
            documents=[c.text for c in batch],
            metadatas=[
                {"source": c.source, "page": c.page, "idx": start + i}
                for i, c in enumerate(batch)
            ],
        )
        done = min(start + batch_size, total)
        if on_progress:
            on_progress(done, total)
        else:
            print(f"  проіндексовано {done} / {total}")


def search(query: str, k: int = 5, sources: list[str] | None = None) -> list[dict]:
    """Повертає k найближчих за змістом шматків.

    sources - список назв документів, серед яких шукати (None = усі).
    """
    model = get_model()
    # для питань префікс "query: "
    vector = model.encode([f"query: {query}"], normalize_embeddings=True).tolist()

    where = None
    if sources:
        where = {"source": sources[0]} if len(sources) == 1 else {"source": {"$in": sources}}
    result = get_collection().query(query_embeddings=vector, n_results=k, where=where)

    hits = []
    for text, meta, dist in zip(result["documents"][0], result["metadatas"][0], result["distances"][0]):
        hits.append({
            "text": text,
            "source": meta["source"],
            "page": meta["page"],
            "idx": meta["idx"],
            "score": 1 - dist,  # чим ближче до 1, тим схожіше
        })
    return hits


def expand_with_neighbors(hits: list[dict], radius: int = 1) -> list[dict]:
    """Додає до кожного знайденого шматка `radius` сусідів ліворуч і праворуч.

    Якщо думка розірвана між двома шматками, друга половина все одно
    потрапить в контекст. Повертає блоки (див. context.merge_blocks).
    """
    wanted_ids = set()
    for h in hits:
        for shift in range(-radius, radius + 1):
            if h["idx"] + shift >= 0:
                wanted_ids.add(f"{h['source']}-{h['idx'] + shift}")

    # get() повертає лише ті id, що існують (за межами документа їх просто немає)
    found = get_collection().get(ids=list(wanted_ids))
    records = [
        {"source": m["source"], "idx": m["idx"], "page": m["page"], "text": doc}
        for doc, m in zip(found["documents"], found["metadatas"])
    ]
    return merge_blocks(records)
