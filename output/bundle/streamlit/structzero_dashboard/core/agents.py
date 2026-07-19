from core.models import PlanningRequest
from core.cortex_gateway import CortexGateway
from core.prompts import (
    ARCHITECT_SYSTEM_PROMPT, 
    CRITICAL_REVIEWER_PROMPT,
    SECURITY_REVIEWER_PROMPT,
    PERFORMANCE_REVIEWER_PROMPT,
    SYNTHESIZER_PROMPT,
    VOTER_PROMPT
)
from core.model_router import MODEL_ROUTER

class ArchitectAgent:
    def __init__(self, gateway: CortexGateway):
        self.gateway = gateway
        
    def generate_blueprint(self, request: PlanningRequest) -> str:
        standards = "\n".join([f"- {r}" for r in request.enterprise_context]) if request.enterprise_context else "None"
        constraints = f"""
        Cloud Target: {request.cloud_target}
        Compliance: {request.compliance}
        
        Enterprise Standards:
        {standards}
        """
        full_prompt = f"{ARCHITECT_SYSTEM_PROMPT}\n\n=== CONSTRAINTS & STANDARDS ===\n{constraints}\n\n=== PLANNING REQUEST ===\n{request.prompt}"
        return self.gateway.complete(full_prompt, MODEL_ROUTER["architect"])

class CriticalReviewerAgent:
    def __init__(self, gateway: CortexGateway):
        self.gateway = gateway
    def review(self, blueprint_markdown: str, context: list[str]) -> str:
        standards = "\n".join([f"- {r}" for r in context]) if context else "None"
        prompt = f"{CRITICAL_REVIEWER_PROMPT}\n\n=== ENTERPRISE STANDARDS TO ENFORCE ===\n{standards}\n\n=== BLUEPRINT ===\n{blueprint_markdown}"
        return self.gateway.complete(prompt, MODEL_ROUTER["critical"])
        
    def vote(self, blueprint_v2: str) -> str:
        return self.gateway.complete(f"{VOTER_PROMPT}\n\n=== BLUEPRINT VERSION 2 ===\n{blueprint_v2}", MODEL_ROUTER["critical"])

class SecurityReviewerAgent:
    def __init__(self, gateway: CortexGateway):
        self.gateway = gateway
    def review(self, blueprint_markdown: str, context: list[str]) -> str:
        standards = "\n".join([f"- {r}" for r in context]) if context else "None"
        prompt = f"{SECURITY_REVIEWER_PROMPT}\n\n=== ENTERPRISE STANDARDS TO ENFORCE ===\n{standards}\n\n=== BLUEPRINT ===\n{blueprint_markdown}"
        return self.gateway.complete(prompt, MODEL_ROUTER["security"])

    def vote(self, blueprint_v2: str) -> str:
        return self.gateway.complete(f"{VOTER_PROMPT}\n\n=== BLUEPRINT VERSION 2 ===\n{blueprint_v2}", MODEL_ROUTER["security"])

class PerformanceReviewerAgent:
    def __init__(self, gateway: CortexGateway):
        self.gateway = gateway
    def review(self, blueprint_markdown: str, context: list[str]) -> str:
        standards = "\n".join([f"- {r}" for r in context]) if context else "None"
        prompt = f"{PERFORMANCE_REVIEWER_PROMPT}\n\n=== ENTERPRISE STANDARDS TO ENFORCE ===\n{standards}\n\n=== BLUEPRINT ===\n{blueprint_markdown}"
        return self.gateway.complete(prompt, MODEL_ROUTER["performance"])
        
    def vote(self, blueprint_v2: str) -> str:
        return self.gateway.complete(f"{VOTER_PROMPT}\n\n=== BLUEPRINT VERSION 2 ===\n{blueprint_v2}", MODEL_ROUTER["performance"])

class SynthesizerAgent:
    def __init__(self, gateway: CortexGateway):
        self.gateway = gateway
    def synthesize(self, draft: str, critical: str, security: str, performance: str) -> str:
        full_prompt = f"""
        {SYNTHESIZER_PROMPT}
        
        === ORIGINAL DRAFT ===
        {draft}
        
        === CRITICAL REVIEW ===
        {critical}
        
        === SECURITY REVIEW ===
        {security}
        
        === PERFORMANCE REVIEW ===
        {performance}
        """
        return self.gateway.complete(full_prompt, MODEL_ROUTER["synthesizer"])
