---
{
  "title": "CQRS Architecture Pattern",
  "category": "Pattern",
  "tags": ["CQRS", "Architecture", "Event-Driven", "Microservices"],
  "priority": "Medium",
  "confidence": 0.96,
  "version": "1.1"
}
---

# CQRS (Command Query Responsibility Segregation)

CQRS is an architectural pattern that separates the models for reading and writing data.

## When to Use
- When read and write workloads have highly asymmetrical scaling requirements.
- In complex domains where the write model requires heavy validation, but the read model must be optimized for fast querying.

## Constraints
- Event-driven architecture must use Kafka to synchronize the read and write models.
- RabbitMQ and SQS are explicitly banned by the Enterprise Architecture Board for CQRS synchronization.
