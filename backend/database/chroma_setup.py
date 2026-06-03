"""Database setup module - uses pure Python vector store."""
import logging
from typing import List, Dict, Any
from database.vector_store import VectorStore

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChromaDBManager:
    """Compatibility wrapper using pure Python vector store."""

    def __init__(self, persist_directory: str = "./vector_store"):
        self._store = VectorStore(persist_directory=persist_directory)
        self.collection = self._store.collection
        logger.info(f"Vector store ready with {self.collection.count()} documents")

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


# Initialize global manager
chroma_manager = ChromaDBManager()


def test_chroma_connection():
    """Test vector store connection."""
    try:
        stats = chroma_manager.get_collection_stats()
        logger.info(f"Vector store test successful: {stats}")
        return True
    except Exception as e:
        logger.error(f"Vector store test failed: {e}")
        return False


if __name__ == "__main__":
    test_chroma_connection()
