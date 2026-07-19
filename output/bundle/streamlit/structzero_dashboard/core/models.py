from dataclasses import dataclass, field
from typing import List, Dict, Optional
import uuid
import datetime

@dataclass
class Project:
    name: str
    description: str = ""
    owner: str = "Unknown"
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class PlanningRequest:
    project_name: str
    prompt: str
    cloud_target: str
    compliance: str
    model: str
    enterprise_context: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    memory: List[str] = field(default_factory=list)

@dataclass
class ValidationResult:
    status: str # APPROVED, APPROVED WITH WARNINGS, REJECTED
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    overall_score: int = 100
    category_scores: Dict[str, int] = field(default_factory=lambda: {
        "Completeness": 100,
        "Security": 100,
        "Performance": 100,
        "Consistency": 100,
        "Compliance": 100
    })

@dataclass
class DebateSession:
    blueprint_id: str
    architect_output: str = ""
    critical_review: str = ""
    security_review: str = ""
    performance_review: str = ""
    synthesizer_output: str = ""
    critical_vote: str = ""
    security_vote: str = ""
    performance_vote: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class ExecutionMetrics:
    blueprint_id: str
    architect_model: str = ""
    reviewer_model: str = ""
    security_model: str = ""
    performance_model: str = ""
    synthesizer_model: str = ""
    
    architect_latency_ms: float = 0.0
    review_latency_ms: float = 0.0
    security_latency_ms: float = 0.0
    performance_latency_ms: float = 0.0
    synthesizer_latency_ms: float = 0.0
    validation_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    
    cortex_calls: int = 0
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    
    blueprint_score: int = 0
    security_score: int = 0
    performance_score: int = 0
    validation_score: int = 0
    
    knowledge_documents_searched: int = 0
    knowledge_chunks_searched: int = 0
    knowledge_documents_retrieved: int = 0
    knowledge_chunks_retrieved: int = 0
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class Blueprint:
    project_id: str = ""
    version: int = 1
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request: PlanningRequest = None
    raw_markdown: str = ""
    mermaid_diagram: str = ""
    validation: ValidationResult = None
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    
    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "version": self.version,
            "request": {
                "project_name": self.request.project_name,
                "prompt": self.request.prompt,
                "cloud_target": self.request.cloud_target,
                "compliance": self.request.compliance,
                "model": self.request.model
            } if self.request else None,
            "raw_markdown": self.raw_markdown,
            "mermaid_diagram": self.mermaid_diagram,
            "validation": {
                "status": self.validation.status,
                "warnings": self.validation.warnings,
                "errors": self.validation.errors,
                "overall_score": self.validation.overall_score,
                "category_scores": self.validation.category_scores
            } if self.validation else None,
            "created_at": self.created_at
        }

@dataclass
class KnowledgeDocument:
    title: str
    source: str
    content: str
    category: str = "General"
    tags: List[str] = field(default_factory=list)
    cloud: List[str] = field(default_factory=list)
    technology: List[str] = field(default_factory=list)
    industry: List[str] = field(default_factory=list)
    compliance: List[str] = field(default_factory=list)
    priority: str = "Medium"
    confidence: float = 1.0
    version: str = "1.0"
    author: str = "System"
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class KnowledgeChunk:
    document_id: str
    chunk_text: str
    section: str = ""
    page: int = 1
    tokens: int = 0
    metadata: Dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class KnowledgeRegistryEntry:
    document_id: str
    source_path: str
    checksum: str
    loader: str
    indexing_status: str = "PENDING" # PENDING, INDEXED, FAILED
    version: str = "1.0"
    ingestion_time: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
