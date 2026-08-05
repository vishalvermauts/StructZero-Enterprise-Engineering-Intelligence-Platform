---
{
  "title": "GCP Customer-Managed Encryption Key Standard",
  "category": "Security",
  "tags": [
    "Encryption",
    "GCP",
    "CMEK",
    "KMS"
  ],
  "cloud": [
    "GCP"
  ],
  "compliance": [
    "PCI-DSS",
    "GDPR"
  ],
  "technology": [
    "Cloud KMS"
  ],
  "priority": "Critical",
  "confidence": 0.96,
  "version": "2.0",
  "provider": "Google Cloud",
  "document_type": "Standard",
  "author": "SAMPLE - synthetic content, not a real policy"
}
---
*Sample standard supplied with StructZero for demonstration. Not a real corporate policy.*

# GCP Customer-Managed Encryption Key Standard

All GCP services holding regulated data must be configured with CMEK backed by Cloud KMS.
Google-managed default encryption does not satisfy our key custody requirement.

## Key Ring Topology
1. Key rings must be regional and must match the data residency region of the resource.
2. A separate key ring per environment; production keys must never be reachable from
   non-production service accounts.
3. Rotation period must not exceed 365 days.

## Enforcement
1. Organisation policy constraints must deny creation of resources without CMEK.
2. Key destruction requires two-person approval and a 30-day scheduled destruction window.
