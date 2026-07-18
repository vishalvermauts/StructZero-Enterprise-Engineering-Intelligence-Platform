import json
from typing import List
from core.loaders.base import BaseLoader
from core.models import KnowledgeDocument, KnowledgeChunk

class MarkdownLoader(BaseLoader):
    def load(self, file_path: str) -> KnowledgeDocument:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Parse frontmatter if exists (assuming strict format: --- \n {json} \n ---)
        metadata = {}
        raw_content = content
        if content.startswith("---\n"):
            parts = content.split("---\n", 2)
            if len(parts) >= 3:
                try:
                    metadata = json.loads(parts[1])
                    raw_content = parts[2].strip()
                except Exception as e:
                    print(f"Failed to parse metadata in {file_path}: {e}")
                    
        return KnowledgeDocument(
            title=metadata.get("title", file_path.split("/")[-1]),
            source=file_path,
            content=raw_content,
            category=metadata.get("category", "General"),
            tags=metadata.get("tags", []),
            cloud=metadata.get("cloud", []),
            technology=metadata.get("technology", []),
            industry=metadata.get("industry", []),
            compliance=metadata.get("compliance", []),
            priority=metadata.get("priority", "Medium"),
            confidence=metadata.get("confidence", 1.0),
            version=metadata.get("version", "1.0")
        )

    def chunk(self, doc: KnowledgeDocument) -> List[KnowledgeChunk]:
        # MVP Chunking: split by H2 (##)
        chunks = []
        sections = doc.content.split("\n## ")
        
        for i, section in enumerate(sections):
            text = ("## " + section) if i > 0 else section
            text = text.strip()
            if not text:
                continue
                
            chunks.append(KnowledgeChunk(
                document_id=doc.id,
                chunk_text=text,
                section=f"Section {i+1}",
                page=1,
                tokens=len(text.split()), # Naive estimation
                metadata={
                    "title": doc.title,
                    "category": doc.category,
                    "tags": doc.tags,
                    "cloud": doc.cloud,
                    "compliance": doc.compliance,
                    "technology": doc.technology
                }
            ))
        return chunks
