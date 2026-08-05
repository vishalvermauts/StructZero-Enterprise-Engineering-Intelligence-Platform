---
{
  "title": "GCP VPC Service Controls and Data Residency",
  "category": "Security",
  "tags": [
    "Network",
    "GCP",
    "Residency",
    "Perimeter"
  ],
  "cloud": [
    "GCP"
  ],
  "compliance": [
    "GDPR"
  ],
  "technology": [
    "VPC Service Controls"
  ],
  "priority": "High",
  "confidence": 0.93,
  "version": "1.2",
  "provider": "Google Cloud",
  "architecture_pattern": "Service Perimeter",
  "document_type": "Standard",
  "author": "SAMPLE - synthetic content, not a real policy"
}
---
*Sample standard supplied with StructZero for demonstration. Not a real corporate policy.*

# GCP VPC Service Controls and Data Residency

Workloads processing EU personal data must sit inside a VPC Service Controls perimeter that
denies egress to projects outside the approved EU project set.

## Perimeter Rules
1. The perimeter must enumerate allowed services explicitly; default-allow is prohibited.
2. Access levels must require corporate device identity for administrative operations.
3. Egress rules must name both the destination project and the specific service method.

## Residency Obligations
1. Storage location constraints must pin buckets and datasets to EU multi-region or an EU region.
2. Log sinks must not export to a non-EU destination.
3. Support access from outside the EU requires an approved access transparency justification.
