# Orchestration engine for StructZero blueprint generation, validation and persistence.
# Co-authored with CoCo
"""
Execution Pipeline Module
=========================
The core orchestration engine for StructZero. Manages the lifecycle of a blueprint 
generation request from knowledge retrieval through the multi-agent debate, synthesis, 
validation, and final persistence into Snowflake.
"""
import time
import re
import uuid
import dataclasses
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
        
    MAX_REVISION_ROUNDS = 2

    def _record_failure(self, run_id, request, start_time, stage, message):
        """CortexGateway.complete() returns None on error/cancel; nothing checked for that,
        so a transient failure crashed the generator and no record of the run was written."""
        detail = f"{stage}: {message}"
        try:
            self.storage.save_pipeline_run({
                "id": run_id, "blueprint_id": None, "project_id": None,
                "project_name": request.project_name, "version": None, "status": "FAILED",
                "validation_status": None, "cloud_target": request.cloud_target,
                "compliance": request.compliance,
                "total_latency_ms": round((time.time() - start_time) * 1000, 2),
                "cortex_calls": self.gateway.total_calls,
                "estimated_cost_usd": round(self.gateway.estimated_cost_usd, 4),
                "error": detail})
        except Exception as e:
            print(f"Failed to record pipeline failure: {e}")
        return {"step": -1, "agent": stage, "status": "error", "error": detail}

    @staticmethod
    def parse_vote(vote_text: str) -> str:
        """First line of a vote is the verdict: APPROVE / APPROVE WITH WARNINGS / BLOCK."""
        if not vote_text:
            return ""
        first = vote_text.strip().splitlines()[0].strip().upper()
        for verdict in ("APPROVE WITH WARNINGS", "BLOCK", "APPROVE"):
            if first.startswith(verdict):
                return verdict
        return first[:40]

    def extract_diagram(self, raw_markdown: str) -> str:
        """
        Pull the architecture diagram out of the final document. The synthesizer prompt
        mandates a graphviz block; the old implementation searched for a mermaid block (the
        architect V1 format) and therefore always returned an empty string, so no blueprint
        ever persisted its diagram. Both fences are accepted now.
        """
        for fence in ("graphviz", "mermaid"):
            matches = re.findall(r"```" + fence + r"\s*(.*?)```", raw_markdown, re.DOTALL | re.IGNORECASE)
            if matches:
                return matches[0].strip()
        return ""

    def extract_mermaid(self, raw_markdown: str) -> str:
        matches = re.findall(r"```mermaid(.*?)```", raw_markdown, re.DOTALL)
        if matches:
            return matches[0].strip()
        return ""

    def run(self, request: PlanningRequest):
        from core.model_router import MODEL_ROUTER
        start_time = time.time()

        # The pipeline is cached with @st.cache_resource, so the gateway instance is reused
        # across runs. Without this reset, call counts and cost accumulate for the lifetime
        # of the session and every run reports the running total instead of its own usage.
        self.gateway.reset_metrics()
        run_id = str(uuid.uuid4())
        
        # 0. Enterprise Context
        yield {"step": 0, "agent": "Enterprise Context Builder", "status": "running"}
        # Actual indexed corpus size, reported alongside what the search retrieved
        corpus = self.storage.count_knowledge_corpus()
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
        if not draft_markdown:
            yield self._record_failure(run_id, request, start_time, "Architect",
                                       "Cortex returned no content (call failed or was cancelled)")
            return
        yield {"step": 1, "agent": "Architect", "model": MODEL_ROUTER["architect"], "status": "complete", "time": architect_time, "output": draft_markdown}
        
        # 2, 3, 4. Review Board (Parallel)
        yield {"step": 2, "agent": "Critical Reviewer", "model": MODEL_ROUTER["critical"], "status": "running"}
        yield {"step": 3, "agent": "Security Reviewer", "model": MODEL_ROUTER["security"], "status": "running"}
        yield {"step": 4, "agent": "Performance Reviewer", "model": MODEL_ROUTER["performance"], "status": "running"}
        
        reviewer_start = time.time()

        # Snowflake Native (SiS) does not support concurrent threading on the same Snowpark
        # Session, so reviewers run sequentially and each is timed individually.
        critical_start = time.time()
        critical_report = self.critical_reviewer.review(draft_markdown, request.enterprise_context)
        critical_time = time.time() - critical_start

        security_start = time.time()
        security_report = self.security_reviewer.review(draft_markdown, request.enterprise_context)
        security_time = time.time() - security_start

        performance_start = time.time()
        performance_report = self.performance_reviewer.review(draft_markdown, request.enterprise_context)
        performance_time = time.time() - performance_start

        reviewer_time = time.time() - reviewer_start

        _unavailable = "(This reviewer did not return a response for this run.)"
        critical_report = critical_report or _unavailable
        security_report = security_report or _unavailable
        performance_report = performance_report or _unavailable
        
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
        if not final_markdown:
            yield {"step": 5, "agent": "Synthesizer", "status": "error",
                   "error": "Synthesis returned no content; falling back to the architect draft."}
            final_markdown = draft_markdown
        final_markdown += footer
        
        synth_time = time.time() - synth_start
        yield {"step": 5, "agent": "Synthesizer", "model": MODEL_ROUTER["synthesizer"], "status": "complete", "time": synth_time, "output": final_markdown}

        # 5.5 Voting pass, then revision rounds while the board blocks. Previously the votes
        # were collected once, displayed and discarded: a BLOCK had no effect and there was
        # no path from "a reviewer objects" to "the design changes".
        revision_rounds = 0
        revision_history = []
        while True:
            yield {"step": 51, "agent": "Critical Voter", "model": MODEL_ROUTER["critical"], "status": "running"}
            yield {"step": 52, "agent": "Security Voter", "model": MODEL_ROUTER["security"], "status": "running"}
            yield {"step": 53, "agent": "Performance Voter", "model": MODEL_ROUTER["performance"], "status": "running"}

            # SiS does not support concurrent threading on the same Snowpark Session
            crit_vote = self.critical_reviewer.vote(final_markdown)
            sec_vote = self.security_reviewer.vote(final_markdown)
            perf_vote = self.performance_reviewer.vote(final_markdown)

            yield {"step": 51, "agent": "Critical Voter", "model": MODEL_ROUTER["critical"], "status": "complete", "output": crit_vote}
            yield {"step": 52, "agent": "Security Voter", "model": MODEL_ROUTER["security"], "status": "complete", "output": sec_vote}
            yield {"step": 53, "agent": "Performance Voter", "model": MODEL_ROUTER["performance"], "status": "complete", "output": perf_vote}

            board_votes = {
                "critical": self.parse_vote(crit_vote),
                "security": self.parse_vote(sec_vote),
                "performance": self.parse_vote(perf_vote),
            }
            blockers = [k for k, v in board_votes.items() if v == "BLOCK"]
            if not blockers or revision_rounds >= self.MAX_REVISION_ROUNDS:
                break

            revision_rounds += 1
            reasons = []
            for name, text in (("critical", crit_vote), ("security", sec_vote), ("performance", perf_vote)):
                if board_votes[name] == "BLOCK":
                    reasons.append("=== " + name.upper() + " REVIEWER BLOCKING CONCERN ===" + chr(10) + str(text))
            label = "Revision Round " + str(revision_rounds)
            yield {"step": 55, "agent": label, "model": MODEL_ROUTER["synthesizer"], "status": "running"}
            revised = self.synthesizer.revise(final_markdown, (chr(10) + chr(10)).join(reasons))
            if not revised:
                yield {"step": 55, "agent": label, "status": "error",
                       "error": "Revision returned no content; keeping the prior version."}
                break
            revision_history.append(final_markdown)
            final_markdown = revised + footer
            yield {"step": 55, "agent": label, "model": MODEL_ROUTER["synthesizer"],
                   "status": "complete", "output": final_markdown}

        diagram_code = self.extract_diagram(final_markdown)

        # 6. Validator - now given the compliance target, the original request and the
        # board verdicts, so its checks can actually fail.
        yield {"step": 6, "agent": "Production Validator", "status": "running"}
        validation_start = time.time()
        validation = self.validator.validate(
            final_markdown,
            compliance=request.compliance,
            prompt=request.prompt,
            board_votes=board_votes,
        )
        validation_time = time.time() - validation_start

        blueprint = Blueprint(
            request=request,
            raw_markdown=final_markdown,
            mermaid_diagram=diagram_code,
            validation=validation
        )
        
        total_time = time.time() - start_time
        observability_metrics = {
            "total_time_s": round(total_time, 2),
            "architect_time_s": round(architect_time, 2),
            "debate_time_s": round(reviewer_time, 2),
            "synthesizer_time_s": round(synth_time, 2),
            "validation_time_s": round(validation_time, 2),
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
                performance_vote=perf_vote,
                revision_rounds=revision_rounds,
                revision_history=revision_history
            )
            
            metrics = ExecutionMetrics(
                blueprint_id=blueprint.id,
                architect_model=MODEL_ROUTER["architect"],
                reviewer_model=MODEL_ROUTER["critical"],
                security_model=MODEL_ROUTER["security"],
                performance_model=MODEL_ROUTER["performance"],
                synthesizer_model=MODEL_ROUTER["synthesizer"],
                architect_latency_ms=round(architect_time * 1000, 2),
                review_latency_ms=round(critical_time * 1000, 2),
                security_latency_ms=round(security_time * 1000, 2),
                performance_latency_ms=round(performance_time * 1000, 2),
                validation_latency_ms=round(validation_time * 1000, 2),
                synthesizer_latency_ms=round(synth_time * 1000, 2),
                total_latency_ms=round(total_time * 1000, 2),
                cortex_calls=self.gateway.total_calls,
                estimated_input_tokens=self.gateway.estimated_input_tokens,
                estimated_output_tokens=self.gateway.estimated_output_tokens,
                estimated_cost_usd=round(self.gateway.estimated_cost_usd, 4),
                revision_rounds=revision_rounds,
                board_decision=validation.board_decision or "",
                blueprint_score=validation.overall_score,
                security_score=validation.category_scores.get("Security", 100),
                performance_score=validation.category_scores.get("Performance", 100),
                validation_score=validation.overall_score,
                knowledge_documents_searched=corpus["documents"],
                knowledge_chunks_searched=corpus["chunks"],
                knowledge_documents_retrieved=len(context_data),
                knowledge_chunks_retrieved=len(context_data)
            )

            validation_dict = dataclasses.asdict(validation)

            self.storage.save_blueprint(blueprint)
            self.storage.save_blueprint_history(blueprint)
            self.storage.save_debate_session(debate)
            self.storage.save_validation(blueprint.id, validation_dict)
            self.storage.save_validation_results(blueprint.id, validation_dict)
            self.storage.save_observability(metrics.id, blueprint.id, dataclasses.asdict(metrics))
            self.storage.save_pipeline_run({
                "id": run_id,
                "blueprint_id": blueprint.id,
                "project_id": project_id,
                "project_name": request.project_name,
                "version": version,
                "status": "SUCCEEDED",
                "validation_status": validation.status,
                "cloud_target": request.cloud_target,
                "compliance": request.compliance,
                "total_latency_ms": round(total_time * 1000, 2),
                "cortex_calls": self.gateway.total_calls,
                "estimated_cost_usd": round(self.gateway.estimated_cost_usd, 4),
                "error": None,
            })
            yield {"step": 7, "agent": "Snowflake Storage", "status": "complete"}
        except Exception as e:
            try:
                self.storage.save_pipeline_run({
                    "id": run_id,
                    "blueprint_id": blueprint.id,
                    "project_id": None,
                    "project_name": request.project_name,
                    "version": None,
                    "status": "FAILED",
                    "validation_status": validation.status,
                    "cloud_target": request.cloud_target,
                    "compliance": request.compliance,
                    "total_latency_ms": round((time.time() - start_time) * 1000, 2),
                    "cortex_calls": self.gateway.total_calls,
                    "estimated_cost_usd": round(self.gateway.estimated_cost_usd, 4),
                    "error": str(e),
                })
            except Exception as log_error:
                print(f"Failed to record pipeline run failure: {log_error}")
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

