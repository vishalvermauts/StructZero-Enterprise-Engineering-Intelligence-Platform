import pytest
from core.validators import ProductionValidator

def test_production_validator_approved():
    validator = ProductionValidator()
    
    # A perfect blueprint that satisfies all constraints
    markdown = """
    # Executive Summary
    # Architecture
    # Components
    # Security
    # Performance
    # Risks
    # Decision Log
    # Roadmap
    # Recommended Actions
    
    ```graphviz
    digraph G {
      A -> B;
    }
    ```
    
    We are using a redis cache and kafka broker for our events.
    For security, we use jwt token auth and KMS encryption with TLS.
    We adhere to pci compliance.
    The system supports 1000 tps with low latency.
    """
    
    result = validator.validate(markdown)
    assert result.status == "APPROVED"
    assert result.overall_score == 100
    assert len(result.errors) == 0
    assert len(result.warnings) == 0

def test_production_validator_rejected():
    validator = ProductionValidator()
    
    # A completely empty/invalid blueprint
    markdown = "This is a terrible blueprint."
    
    result = validator.validate(markdown)
    assert result.status == "REJECTED"
    assert len(result.errors) > 0
