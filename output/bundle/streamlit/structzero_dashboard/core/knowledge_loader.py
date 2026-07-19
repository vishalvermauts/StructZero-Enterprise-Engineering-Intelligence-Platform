"""
Knowledge Loader Module
=======================
The ingestion engine for the Enterprise Knowledge Base. Scans local directories for markdown
policies and incident reports, parses them, and upserts the chunks natively into Snowflake.
"""
import os
import hashlib
from typing import Dict
from core.loaders.base import BaseLoader
from core.loaders.markdown import MarkdownLoader
from core.storage import StorageClient
from core.models import KnowledgeRegistryEntry

class KnowledgeOrchestrator:
    """
    Coordinates the scanning of knowledge directories, hashing to detect changes, 
    and delegating the actual chunking to specific file loaders.
    """
    def __init__(self, storage: StorageClient):
        self.storage = storage
        self.loaders: Dict[str, BaseLoader] = {
            ".md": MarkdownLoader()
        }

    def _hash_file(self, file_path: str) -> str:
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def load_directory(self, root_dir: str):
        """
        Recursively walks the root directory, chunks supported files, and stores them in Snowflake.
        """
        print(f"Starting Knowledge Ingestion from {root_dir}...")
        docs_indexed = 0
        chunks_indexed = 0

        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in self.loaders:
                    filepath = os.path.join(dirpath, filename)
                    normalized_path = filepath.replace("\\", "/")
                    file_hash = self._hash_file(filepath)
                    
                    # Check registry
                    existing_entry = self.storage.get_knowledge_registry_by_path(normalized_path)
                    if existing_entry and existing_entry.get("checksum") == file_hash:
                        # Unchanged
                        continue
                        
                    print(f"Ingesting {normalized_path}...")
                    loader = self.loaders[ext]
                    try:
                        doc = loader.load(filepath)
                        chunks = loader.chunk(doc)
                        
                        # Store in Snowflake
                        self.storage.upsert_knowledge_document(doc.to_dict() if hasattr(doc, 'to_dict') else doc.__dict__)
                        
                        # Clear old chunks if updating
                        if existing_entry:
                            self.storage.clear_document_chunks(existing_entry["document_id"])
                            
                        for chunk in chunks:
                            self.storage.upsert_knowledge_chunk(chunk.to_dict() if hasattr(chunk, 'to_dict') else chunk.__dict__)
                            chunks_indexed += 1
                            
                        # Update registry
                        registry_entry = KnowledgeRegistryEntry(
                            document_id=doc.id,
                            source_path=normalized_path,
                            checksum=file_hash,
                            loader=loader.__class__.__name__,
                            indexing_status="INDEXED"
                        )
                        self.storage.upsert_knowledge_registry(registry_entry.to_dict() if hasattr(registry_entry, 'to_dict') else registry_entry.__dict__)
                        docs_indexed += 1
                    except Exception as e:
                        print(f"Error ingesting {normalized_path}: {e}")
                        
        print(f"Knowledge Ingestion Complete. {docs_indexed} documents, {chunks_indexed} chunks.")
