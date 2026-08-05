---
{
  "title": "Azure Identity and Access Baseline",
  "category": "Security",
  "tags": [
    "Identity",
    "Azure",
    "RBAC",
    "Entra"
  ],
  "cloud": [
    "Azure"
  ],
  "compliance": [
    "SOC2",
    "HIPAA"
  ],
  "technology": [
    "Entra ID"
  ],
  "priority": "Critical",
  "confidence": 0.95,
  "version": "2.1",
  "provider": "Microsoft Azure",
  "document_type": "Standard",
  "author": "SAMPLE - synthetic content, not a real policy"
}
---
*Sample standard supplied with StructZero for demonstration. Not a real corporate policy.*

# Azure Identity and Access Baseline

All Azure workloads must authenticate through Entra ID. Local account authentication and
shared service credentials are prohibited in any environment that processes regulated data.

## Managed Identity Requirements
1. Every compute resource must use a user-assigned or system-assigned managed identity.
2. Connection strings containing secrets must be replaced with managed identity tokens.
3. Key Vault references must be used for any remaining secret material.

## Privileged Access
1. Privileged roles must be assigned through Privileged Identity Management with time-bound
   activation, never permanently.
2. Break-glass accounts must be excluded from conditional access but monitored for any use.
3. Role assignments at subscription scope require documented architectural justification.
