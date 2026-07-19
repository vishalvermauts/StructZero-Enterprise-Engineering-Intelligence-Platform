---
{
  "title": "AWS KMS Security Standards",
  "category": "Security",
  "tags": ["Encryption", "Security", "AWS", "KMS"],
  "cloud": ["AWS"],
  "compliance": ["PCI-DSS", "SOC2"],
  "priority": "Critical",
  "confidence": 0.99,
  "version": "3.2"
}
---

# AWS KMS Security Standards

All AWS deployments must use Customer Managed KMS Keys (CMK) for data at rest. Default AWS managed keys are strictly not permitted for production workloads.

## Implementation Guidelines
1. Keys must be rotated annually.
2. IAM policies must restrict key usage to specific service roles.
3. Envelope encryption should be used for large payloads (e.g., S3 objects).
