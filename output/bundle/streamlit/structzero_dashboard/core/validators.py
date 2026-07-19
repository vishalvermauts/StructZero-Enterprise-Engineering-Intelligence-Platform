"""
Production Validators Module
============================
A deterministic Python rules engine that validates the AI-generated architecture blueprints
against strict enterprise completeness, consistency, security, and performance criteria.
"""
from core.models import ValidationResult
import re

class ProductionValidator:
    """
    Validates raw markdown blueprints against hardcoded enterprise constraints.
    Returns a ValidationResult containing scores and warnings/errors.
    """
    def validate(self, raw_markdown: str) -> ValidationResult:
        warnings = []
        errors = []
        
        scores = {
            "Completeness": 100,
            "Security": 100,
            "Performance": 100,
            "Consistency": 100,
            "Compliance": 100
        }
        
        def deduct(category: str, amount: int, msg: str, is_error: bool = False):
            scores[category] = max(0, scores[category] - amount)
            if is_error:
                errors.append(msg)
            else:
                warnings.append(msg)
                
        # 1. Check for required sections (Completeness)
        required_sections = [
            "Executive Summary", "Architecture", 
            "Components", "Security", "Performance", "Risks", 
            "Decision Log", "Roadmap", "Recommended Actions"
        ]
        
        for section in required_sections:
            if not re.search(rf"#+.*{section}", raw_markdown, re.IGNORECASE):
                deduct("Completeness", 5, f"Missing required section: {section}", is_error=True)
                
        # 2. Graphviz Diagram
        graphviz_matches = re.findall(r"```graphviz(.*?)```", raw_markdown, re.DOTALL)
        if not graphviz_matches:
            deduct("Completeness", 10, "Missing Graphviz Diagram block.", is_error=True)
        elif len(graphviz_matches) > 1:
            deduct("Consistency", 5, "Multiple Graphviz Diagram blocks found. Only the first will be rendered.")
            
        # 3. Cross-reference checks (Consistency)
        lower_md = raw_markdown.lower()
        if "kafka" in lower_md and not re.search(r"(broker|event|queue|stream)", lower_md):
            deduct("Consistency", 5, "Kafka is mentioned but no event/broker terminology found in components.")
            
        if "redis" in lower_md and not re.search(r"(cache|caching)", lower_md):
            deduct("Consistency", 5, "Redis is mentioned but caching strategy is missing.")
            
        if "jwt" in lower_md and not re.search(r"(auth|login|token)", lower_md):
            deduct("Security", 5, "JWT mentioned but missing Authentication API endpoints.")
            
        # 4. Security Checks
        if not re.search(r"(pci|compliance|soc2|gdpr)", lower_md):
            deduct("Compliance", 15, "No compliance framework explicitly mentioned in the blueprint.", is_error=True)
            
        if not re.search(r"(encryption|tls|kms)", lower_md):
            deduct("Security", 10, "No mention of encryption or KMS.", is_error=True)

        if not re.search(r"(latency|tps|throughput)", lower_md):
            deduct("Performance", 10, "Missing concrete performance bounds (TPS/Latency).")
            
        # Overall Calculation
        overall = sum(scores.values()) // len(scores)
        
        if len(errors) > 0 or overall < 60:
            status = "REJECTED"
        elif overall < 80 or len(warnings) > 0:
            status = "APPROVED WITH WARNINGS"
        else:
            status = "APPROVED"
            
        return ValidationResult(
            status=status, 
            warnings=warnings, 
            errors=errors,
            overall_score=overall,
            category_scores=scores
        )
