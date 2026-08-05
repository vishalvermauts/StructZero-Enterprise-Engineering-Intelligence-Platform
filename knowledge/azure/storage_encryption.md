---
{
  "title": "Azure Storage Encryption Standard",
  "category": "Security",
  "tags": [
    "Encryption",
    "Azure",
    "Storage",
    "CMK"
  ],
  "cloud": [
    "Azure"
  ],
  "compliance": [
    "PCI-DSS",
    "HIPAA"
  ],
  "technology": [
    "Azure Storage",
    "Key Vault"
  ],
  "priority": "Critical",
  "confidence": 0.97,
  "version": "1.4",
  "provider": "Microsoft Azure",
  "document_type": "Standard",
  "author": "SAMPLE - synthetic content, not a real policy"
}
---
*Sample standard supplied with StructZero for demonstration. Not a real corporate policy.*

# Azure Storage Encryption Standard

Storage accounts holding regulated data must use customer-managed keys held in Key Vault with
purge protection enabled. Platform-managed keys are acceptable only for non-regulated
telemetry.

## Key Management Rules
1. Keys must be rotated at least annually with automated rotation configured.
2. Key Vault must have soft-delete and purge protection enabled; both are irreversible.
3. Cross-region replication must not move keys outside the data residency boundary.

## Transport and Access
1. Only TLS 1.2 or above; the minimum TLS version must be enforced on the account.
2. Public blob access must be disabled at account level.
3. Access must be through private endpoints where the consuming service supports them.
