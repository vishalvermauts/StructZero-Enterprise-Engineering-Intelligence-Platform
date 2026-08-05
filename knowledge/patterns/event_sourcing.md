---
{
  "title": "Event Sourcing",
  "category": "Pattern",
  "tags": [
    "Event Sourcing",
    "Audit",
    "CQRS"
  ],
  "priority": "Medium",
  "confidence": 0.9,
  "version": "1.0",
  "architecture_pattern": "Event Sourcing",
  "document_type": "Pattern",
  "author": "SAMPLE - synthetic content, not a real policy"
}
---
*Sample standard supplied with StructZero for demonstration. Not a real corporate policy.*

# Event Sourcing

Event sourcing persists state as an append-only sequence of domain events. Current state is a
fold over that sequence rather than a mutable row.

## When to Use
- When a complete, tamper-evident audit trail is a hard requirement (regulated domains).
- When multiple read models must be derived from the same write history.
- When temporal queries such as "what did we believe on this date" have business value.

## Constraints
- Event schemas are append-only; breaking changes require upcasting, never mutation.
- Snapshots are mandatory once an aggregate exceeds a few thousand events.
- Personal data in events conflicts with the right to erasure; use crypto-shredding with a
  per-subject key rather than deleting events.
