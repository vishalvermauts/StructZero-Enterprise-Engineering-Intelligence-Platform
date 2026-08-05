---
{
  "title": "Saga Pattern for Distributed Transactions",
  "category": "Pattern",
  "tags": [
    "Saga",
    "Consistency",
    "Microservices"
  ],
  "priority": "Medium",
  "confidence": 0.91,
  "version": "1.0",
  "architecture_pattern": "Saga",
  "document_type": "Pattern",
  "author": "SAMPLE - synthetic content, not a real policy"
}
---
*Sample standard supplied with StructZero for demonstration. Not a real corporate policy.*

# Saga Pattern for Distributed Transactions

A saga replaces a distributed transaction with a sequence of local transactions, each paired
with a compensating action that semantically undoes it.

## When to Use
- When a business process spans services that cannot share a transaction boundary.
- When eventual consistency is acceptable to the business and can be stated as a bound.

## Constraints
- Every step must have an idempotency key; retried steps must not double-apply.
- Compensation is semantic, not a rollback: a refund is not the inverse of a charge.
- Orchestration must be explicit and observable; implicit choreography across more than three
  services becomes untraceable in production.
