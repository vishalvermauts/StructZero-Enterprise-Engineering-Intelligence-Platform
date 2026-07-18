from core.models import ValidationResult
import re

class ProductionValidator:
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
            "Decision Log", "Executive Summary", "Requirements", "Architecture", 
            "Components", "Folder Structure", "API Design", 
            "Security", "Trade-offs & Alternatives", "Risks", 
            "Assumptions", "Implementation Plan"
        ]
        
        for section in required_sections:
            if not re.search(rf"#+\s*{section}", raw_markdown, re.IGNORECASE):
                deduct("Completeness", 5, f"Missing required section: {section}", is_error=True)
                
        # 2. Mermaid Diagram
        mermaid_matches = re.findall(r"```mermaid(.*?)```", raw_markdown, re.DOTALL)
        if not mermaid_matches:
            deduct("Completeness", 10, "Missing Mermaid Diagram block.", is_error=True)
        elif len(mermaid_matches) > 1:
            deduct("Consistency", 5, "Multiple Mermaid Diagram blocks found. Only the first will be rendered.")
            
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
        
        if len(errors) > 0 or overall < 80:
            status = "REJECTED" if overall < 60 else "APPROVED WITH WARNINGS"
        elif len(warnings) > 0:
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
