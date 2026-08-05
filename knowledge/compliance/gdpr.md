---
{
  "title": "GDPR Design Obligations",
  "category": "Compliance",
  "tags": [
    "GDPR",
    "Privacy",
    "Residency"
  ],
  "compliance": [
    "GDPR"
  ],
  "priority": "Critical",
  "confidence": 0.98,
  "version": "1.1",
  "document_type": "Policy",
  "author": "SAMPLE - synthetic content, not a real policy"
}
---
*Sample standard supplied with StructZero for demonstration. Not a real corporate policy.*

# GDPR Design Obligations

Systems processing EU personal data must address each obligation below explicitly in the
architecture document.

## Lawful Basis and Residency
1. State the lawful basis for each processing purpose; consent must be separable per purpose.
2. Personal data must remain in EU regions; state the residency boundary and how it is enforced.
3. Any transfer outside the EU requires a documented transfer mechanism and a DPA with the
   receiving processor.

## Data Subject Rights
1. Right to erasure must be implementable within 30 days including from backups and caches.
2. Data portability must produce a machine-readable export per data subject.
3. Retention periods must be stated per data category and enforced automatically, not manually.
