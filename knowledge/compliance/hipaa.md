---
{
  "title": "HIPAA Design Obligations",
  "category": "Compliance",
  "tags": [
    "HIPAA",
    "PHI",
    "Healthcare"
  ],
  "compliance": [
    "HIPAA"
  ],
  "industry": [
    "Healthcare"
  ],
  "priority": "Critical",
  "confidence": 0.98,
  "version": "1.0",
  "document_type": "Policy",
  "author": "SAMPLE - synthetic content, not a real policy"
}
---
*Sample standard supplied with StructZero for demonstration. Not a real corporate policy.*

# HIPAA Design Obligations

Any system handling protected health information must satisfy the following before design
approval. Absence of an explicit statement is treated as non-compliance.

## PHI Handling
1. PHI must be identified field by field in the data model, not described in aggregate.
2. De-identification must occur before data leaves the clinical trust boundary, using
   Safe Harbor or an documented expert determination.
3. PHI must never appear in application logs, traces or error payloads.

## Contracts and Audit
1. Every third-party processor touching PHI requires a Business Associate Agreement.
2. Access to PHI must be logged with user, record identifier, timestamp and purpose.
3. Audit logs must be retained for six years and be tamper-evident.
