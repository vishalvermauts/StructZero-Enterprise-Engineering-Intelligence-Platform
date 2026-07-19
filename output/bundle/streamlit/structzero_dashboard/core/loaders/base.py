from abc import ABC, abstractmethod
from typing import List
from core.models import KnowledgeDocument, KnowledgeChunk

class BaseLoader(ABC):
    @abstractmethod
    def load(self, file_path: str) -> KnowledgeDocument:
        """Loads a file and parses it into a KnowledgeDocument."""
        pass

    @abstractmethod
    def chunk(self, doc: KnowledgeDocument) -> List[KnowledgeChunk]:
        """Splits a KnowledgeDocument into KnowledgeChunks."""
        pass
