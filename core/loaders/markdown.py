# Markdown knowledge loader: parses JSON frontmatter and chunks documents by H2 heading.
# Co-authored with CoCo
import json
from typing import List
from core.loaders.base import BaseLoader
from core.models import KnowledgeDocument, KnowledgeChunk

# Frontmatter keys that map onto dedicated KnowledgeDocument fields. Anything else is
# carried through in `extra` so downstream search attributes can still resolve it.
_KNOWN_KEYS = {
    "title", "category", "tags", "cloud", "technology", "industry",
    "compliance", "priority", "confidence", "version",
}

# Columns that KNOWLEDGE_SEARCH_VIEW and the Cortex Search service expect on every chunk.
# Emitted as explicit nulls when absent so the attribute list stays stable.
_OPTIONAL_ATTRIBUTES = (
    "provider", "language", "framework", "architecture_pattern", "document_type",
)


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
            version=metadata.get("version", "1.0"),
            extra={k: v for k, v in metadata.items() if k not in _KNOWN_KEYS},
        )

    def chunk(self, doc: KnowledgeDocument) -> List[KnowledgeChunk]:
        # MVP Chunking: split by H2 (##)
        chunks = []
        sections = doc.content.split("\n## ")

        # Every chunk carries the full document provenance, so KNOWLEDGE_SEARCH_VIEW can
        # project source/version/last_updated without joining back to KNOWLEDGE_DOCUMENTS.
        base_metadata = {
            "title": doc.title,
            "source": doc.source,
            "category": doc.category,
            "tags": doc.tags,
            "cloud": doc.cloud,
            "compliance": doc.compliance,
            "technology": doc.technology,
            "industry": doc.industry,
            "priority": doc.priority,
            "confidence": doc.confidence,
            "version": doc.version,
            "last_updated": doc.updated_at,
        }
        for key in _OPTIONAL_ATTRIBUTES:
            base_metadata[key] = doc.extra.get(key)
        for key, value in doc.extra.items():
            base_metadata.setdefault(key, value)

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
                tokens=len(text.split()),  # Naive estimation
                metadata={**base_metadata, "section": f"Section {i+1}"},
            ))
        return chunks
