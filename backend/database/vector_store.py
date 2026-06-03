"""
Pure-Python lightweight vector store.
Drop-in replacement for ChromaDB that avoids native code crashes.
Persists data to a JSON file and uses cosine similarity for queries.
"""
import json
import math
import re
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

DIM = 384
STORE_PATH = Path("vector_store.json")


def _text_to_vector(text: str) -> List[float]:
    """Convert text to a fixed-dimension vector using hashed bag-of-words."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    words = text.split()
    vec = [0.0] * DIM
    if not words:
        return vec
    counts: Dict[str, int] = {}
    for w in words:
        counts[w] = counts.get(w, 0) + 1
    for word, count in counts.items():
        h = hashlib.md5(word.encode("utf-8")).hexdigest()
        idx = int(h[:8], 16) % DIM
        vec[idx] += math.log(1 + count)
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)


class VectorCollection:
    """In-memory vector collection with JSON persistence."""

    def __init__(self, persist_path: Path = STORE_PATH):
        self.persist_path = persist_path
        self.ids: List[str] = []
        self.documents: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []
        self.embeddings: List[List[float]] = []
        self._load()

    def _load(self):
        """Load data from JSON file if it exists."""
        if self.persist_path.exists():
            try:
                data = json.loads(self.persist_path.read_text(encoding="utf-8"))
                self.ids = data.get("ids", [])
                self.documents = data.get("documents", [])
                self.metadatas = data.get("metadatas", [])
                self.embeddings = data.get("embeddings", [])
                logger.info(f"Loaded {len(self.ids)} documents from {self.persist_path}")
            except Exception as e:
                logger.error(f"Failed to load vector store: {e}")

    def _save(self):
        """Persist data to JSON file."""
        try:
            data = {
                "ids": self.ids,
                "documents": self.documents,
                "metadatas": self.metadatas,
                "embeddings": self.embeddings,
            }
            self.persist_path.write_text(json.dumps(data), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")

    def count(self) -> int:
        return len(self.ids)

    def add(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None,
    ):
        """Add documents to the collection."""
        if ids is None:
            ids = [f"doc_{len(self.ids) + i}" for i in range(len(documents))]
        if metadatas is None:
            metadatas = [{} for _ in documents]
        if embeddings is None:
            embeddings = [_text_to_vector(doc) for doc in documents]

        for i, (doc_id, doc, meta, emb) in enumerate(zip(ids, documents, metadatas, embeddings)):
            if doc_id in self.ids:
                # Update existing
                idx = self.ids.index(doc_id)
                self.documents[idx] = doc
                self.metadatas[idx] = meta
                self.embeddings[idx] = emb
            else:
                self.ids.append(doc_id)
                self.documents.append(doc)
                self.metadatas.append(meta)
                self.embeddings.append(emb)

        self._save()
        logger.info(f"Added/updated {len(documents)} documents. Total: {self.count()}")

    def query(
        self,
        query_texts: Optional[List[str]] = None,
        query_embeddings: Optional[List[List[float]]] = None,
        n_results: int = 5,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Query the collection for similar documents."""
        if query_embeddings is None and query_texts is not None:
            query_embeddings = [_text_to_vector(q) for q in query_texts]

        if query_embeddings is None:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        all_docs: List[List[str]] = []
        all_metas: List[List[Dict]] = []
        all_dists: List[List[float]] = []

        for q_emb in query_embeddings:
            # Compute similarities
            scored = []
            for i, emb in enumerate(self.embeddings):
                sim = _cosine_similarity(q_emb, emb)
                dist = 1.0 - sim  # Convert to distance (like ChromaDB cosine)
                scored.append((dist, i))

            scored.sort(key=lambda x: x[0])  # Sort by distance (ascending)
            top_k = scored[:n_results]

            docs = [self.documents[i] for _, i in top_k]
            metas = [self.metadatas[i] for _, i in top_k]
            dists = [d for d, _ in top_k]

            all_docs.append(docs)
            all_metas.append(metas)
            all_dists.append(dists)

        return {
            "documents": all_docs,
            "metadatas": all_metas,
            "distances": all_dists,
        }

    def reset(self):
        """Clear all data."""
        self.ids.clear()
        self.documents.clear()
        self.metadatas.clear()
        self.embeddings.clear()
        self._save()


class VectorStore:
    """Simple vector store manager (replaces ChromaDBManager)."""

    def __init__(self, persist_directory: str = "./vector_store"):
        self.persist_path = Path(persist_directory) / "store.json"
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        self.collection = VectorCollection(persist_path=self.persist_path)
        logger.info(f"VectorStore ready with {self.collection.count()} documents")

    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]):
        self.collection.add(documents=documents, metadatas=metadatas, ids=ids)

    def query_documents(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        return self.collection.query(query_texts=[query], n_results=n_results)

    def get_collection_stats(self) -> Dict[str, Any]:
        return {
            "document_count": self.collection.count(),
            "collection_name": "mutual_funds",
            "status": "active",
        }

    def reset_collection(self):
        self.collection.reset()
        logger.info("Vector store reset")


# Global instance
_store: Optional[VectorStore] = None


def get_vector_store(persist_directory: str = "./vector_store") -> VectorStore:
    """Get or create the global vector store."""
    global _store
    if _store is None:
        _store = VectorStore(persist_directory=persist_directory)
    return _store
