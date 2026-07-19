"""
Execution Pipeline Module
=========================
The core orchestration engine for StructZero. Manages the lifecycle of a blueprint 
generation request from knowledge retrieval through the multi-agent debate, synthesis, 
validation, and final persistence into Snowflake.
"""
import time
import re
import dataclasses
import concurrent.futures
from core.models import PlanningRequest, Blueprint
from core.cortex_gateway import CortexGateway
from core.agents import (
    ArchitectAgent, 
    CriticalReviewerAgent,
    SecurityReviewerAgent,
    PerformanceReviewerAgent,
    SynthesizerAgent
)
from core.validators import ProductionValidator

from core.validators import ProductionValidator
from core.storage import StorageClient
from core.knowledge_loader import KnowledgeOrchestrator

class PlanningPipeline:
    """Orchestrates the entire AI architecture generation process."""
    def __init__(self):
        self.gateway = CortexGateway()
        self.storage = StorageClient(self.gateway.session)
        # Ingest knowledge repo on boot
        self.knowledge_loader = KnowledgeOrchestrator(self.storage)
        self.knowledge_loader.load_directory("knowledge/")
        
        self.architect = ArchitectAgent(self.gateway)
        self.critical_reviewer = CriticalReviewerAgent(self.gateway)
        self.security_reviewer = SecurityReviewerAgent(self.gateway)
        self.performance_reviewer = PerformanceReviewerAgent(self.gateway)
        self.synthesizer = SynthesizerAgent(self.gateway)
        self.validator = ProductionValidator()
        
    def extract_mermaid(self, raw_markdown: str) -> str:
        matches = re.findall(r"```mermaid(.*?)```", raw_markdown, re.DOTALL)
        if matches:
            return matches[0].strip()
        return ""

    def run(self, request: PlanningRequest):
        from core.model_router import MODEL_ROUTER
        start_time = time.time()
        
        # 0. Enterprise Context
        yield {"step": 0, "agent": "Enterprise Context Builder", "status": "running"}
        # Fetch matching enterprise standards from Snowflake Cortex Search
        context_data = self.storage.get_enterprise_context(
            prompt=request.prompt,
            cloud=request.cloud_target,
            compliance=request.compliance,
            limit=8
        )
        
        # Format the context rules for the LLMs
        request.enterprise_context = [
            f"[{c['metadata'].get('source', 'Knowledge')}] (Relevance Score {c.get('score', 0.95)}): {c['chunk_text']}" 
            for c in context_data
        ]
        
        # Format citations for the UI
        citations = []
        for c in context_data:
            citations.append({
                "source": c['metadata'].get('source', 'Unknown'),
                "cloud": c['metadata'].get('cloud', ''),
                "compliance": c['metadata'].get('compliance', ''),
                "score": c.get('score', 0.95)
            })
            
        yield {"step": 0, "agent": "Enterprise Context Builder", "status": "complete", "citations": citations}
        
        # 1. Architect
        yield {"step": 1, "agent": "Architect", "model": MODEL_ROUTER["architect"], "status": "running"}
        architect_start = time.time()
        draft_markdown = self.architect.generate_blueprint(request)
        architect_time = time.time() - architect_start
        yield {"step": 1, "agent": "Architect", "model": MODEL_ROUTER["architect"], "status": "complete", "time": architect_time, "output": draft_markdown}
        
        # 2, 3, 4. Review Board (Parallel)
        yield {"step": 2, "agent": "Critical Reviewer", "model": MODEL_ROUTER["critical"], "status": "running"}
        yield {"step": 3, "agent": "Security Reviewer", "model": MODEL_ROUTER["security"], "status": "running"}
        yield {"step": 4, "agent": "Performance Reviewer", "model": MODEL_ROUTER["performance"], "status": "running"}
        
        reviewer_start = time.time()
        
        # Snowflake Native (SiS) does not support concurrent threading on the same Snowpark Session
        critical_report = self.critical_reviewer.review(draft_markdown, request.enterprise_context)
        security_report = self.security_reviewer.review(draft_markdown, request.enterprise_context)
        performance_report = self.performance_reviewer.review(draft_markdown, request.enterprise_context)
            
        reviewer_time = time.time() - reviewer_start
        
        yield {"step": 2, "agent": "Critical Reviewer", "model": MODEL_ROUTER["critical"], "status": "complete", "output": critical_report}
        yield {"step": 3, "agent": "Security Reviewer", "model": MODEL_ROUTER["security"], "status": "complete", "output": security_report}
        yield {"step": 4, "agent": "Performance Reviewer", "model": MODEL_ROUTER["performance"], "status": "complete", "output": performance_report}
        
        # 5. Synthesizer
        yield {"step": 5, "agent": "Synthesizer", "model": MODEL_ROUTER["synthesizer"], "status": "running"}
        synth_start = time.time()
        final_markdown = self.synthesizer.synthesize(
            draft=draft_markdown, 
            critical=critical_report, 
            security=security_report, 
            performance=performance_report
        )
        
        # Inject standard attribution footer
        footer = "\n\n---\n\nGenerated by StructZero Enterprise Engineering Intelligence Platform\n\nDeveloped by Vishal Verma\n\nhttps://www.vishalverma.me/\n"
        final_markdown += footer
        
        synth_time = time.time() - synth_start
        mermaid_code = self.extract_mermaid(final_markdown)
        yield {"step": 5, "agent": "Synthesizer", "model": MODEL_ROUTER["synthesizer"], "status": "complete", "time": synth_time, "output": final_markdown}
        
        # 5.5 Voting Pass (Parallel)
        yield {"step": 51, "agent": "Critical Voter", "model": MODEL_ROUTER["critical"], "status": "running"}
        yield {"step": 52, "agent": "Security Voter", "model": MODEL_ROUTER["security"], "status": "running"}
        yield {"step": 53, "agent": "Performance Voter", "model": MODEL_ROUTER["performance"], "status": "running"}
        
        # Snowflake Native (SiS) does not support concurrent threading on the same Snowpark Session
        crit_vote = self.critical_reviewer.vote(final_markdown)
        sec_vote = self.security_reviewer.vote(final_markdown)
        perf_vote = self.performance_reviewer.vote(final_markdown)
            
        yield {"step": 51, "agent": "Critical Voter", "model": MODEL_ROUTER["critical"], "status": "complete", "output": crit_vote}
        yield {"step": 52, "agent": "Security Voter", "model": MODEL_ROUTER["security"], "status": "complete", "output": sec_vote}
        yield {"step": 53, "agent": "Performance Voter", "model": MODEL_ROUTER["performance"], "status": "complete", "output": perf_vote}
        
        # 6. Validator
        yield {"step": 6, "agent": "Production Validator", "status": "running"}
        validation = self.validator.validate(final_markdown)
        
        blueprint = Blueprint(
            request=request,
            raw_markdown=final_markdown,
            mermaid_diagram=mermaid_code,
            validation=validation
        )
        
        total_time = time.time() - start_time
        observability_metrics = {
            "total_time_s": round(total_time, 2),
            "architect_time_s": round(architect_time, 2),
            "debate_time_s": round(reviewer_time, 2),
            "synthesizer_time_s": round(synth_time, 2),
            "model_used": "Multi-Model Debate"
        }
        
        yield {"step": 6, "agent": "Production Validator", "status": "complete", "validation": validation}
        
        # 7. Snowflake Storage
        yield {"step": 7, "agent": "Snowflake Storage", "status": "running"}
        try:
            from core.models import Project, DebateSession, ExecutionMetrics
            
            # Find or Create Project
            existing_projects = self.storage.list_projects()
            proj = next((p for p in existing_projects if p.get("name") == request.project_name), None)
            
            if not proj:
                project = Project(name=request.project_name)
                self.storage.save_project(project)
                project_id = project.id
                version = 1
            else:
                project_id = proj["id"]
                versions = self.storage.list_project_versions(project_id)
                version = len(versions) + 1

            blueprint.project_id = project_id
            blueprint.version = version
            
            debate = DebateSession(
                blueprint_id=blueprint.id,
                architect_output=draft_markdown,
                critical_review=critical_report,
                security_review=security_report,
                performance_review=performance_report,
                synthesizer_output=final_markdown,
                critical_vote=crit_vote,
                security_vote=sec_vote,
                performance_vote=perf_vote
            )
            
            metrics = ExecutionMetrics(
                blueprint_id=blueprint.id,
                architect_model=MODEL_ROUTER["architect"],
                reviewer_model=MODEL_ROUTER["critical"],
                security_model=MODEL_ROUTER["security"],
                performance_model=MODEL_ROUTER["performance"],
                synthesizer_model=MODEL_ROUTER["synthesizer"],
                architect_latency_ms=round(architect_time * 1000, 2),
                review_latency_ms=round(reviewer_time * 1000, 2),
                synthesizer_latency_ms=round(synth_time * 1000, 2),
                total_latency_ms=round(total_time * 1000, 2),
                cortex_calls=self.gateway.total_calls,
                estimated_input_tokens=self.gateway.estimated_input_tokens,
                estimated_output_tokens=self.gateway.estimated_output_tokens,
                estimated_cost_usd=round(self.gateway.estimated_cost_usd, 4),
                blueprint_score=validation.overall_score,
                security_score=validation.category_scores.get("Security", 100),
                performance_score=validation.category_scores.get("Performance", 100),
                validation_score=validation.overall_score,
                knowledge_documents_searched=128, # MVP Mocks
                knowledge_chunks_searched=652,
                knowledge_documents_retrieved=len(context_data),
                knowledge_chunks_retrieved=len(context_data)
            )

            self.storage.save_blueprint(blueprint)
            self.storage.save_debate_session(debate)
            self.storage.save_observability(metrics.id, blueprint.id, dataclasses.asdict(metrics))
            yield {"step": 7, "agent": "Snowflake Storage", "status": "complete"}
        except Exception as e:
            yield {"step": 7, "agent": "Snowflake Storage", "status": "error", "error": str(e)}
            return
        
        reviews = {
            "critical": critical_report,
            "security": security_report,
            "performance": performance_report,
            "votes": {
                "critical": crit_vote,
                "security": sec_vote,
                "performance": perf_vote
            }
        }
        
        yield {"step": 8, "status": "finished", "blueprint": blueprint, "reviews": reviews, "metrics": dataclasses.asdict(metrics)}

