---
{
  "title": "On-Premise Network Zoning Standard",
  "category": "Security",
  "tags": [
    "Network",
    "Segmentation",
    "On-Prem",
    "Zoning"
  ],
  "cloud": [
    "On-Prem"
  ],
  "compliance": [
    "PCI-DSS",
    "SOC2"
  ],
  "priority": "Critical",
  "confidence": 0.94,
  "version": "4.0",
  "document_type": "Standard",
  "author": "SAMPLE - synthetic content, not a real policy"
}
---
*Sample standard supplied with StructZero for demonstration. Not a real corporate policy.*

# On-Premise Network Zoning Standard

On-premise deployments must implement four zones: untrusted, DMZ, application and data.
Traffic may only traverse adjacent zones; application tier must never be reachable directly
from untrusted networks.

## Segmentation Requirements
1. Cardholder data environments must be segmented at layer 3 with deny-by-default ACLs.
2. East-west traffic within the data zone must be authenticated with mutual TLS.
3. Jump hosts are the only permitted administrative path into the data zone.

## Physical and Operational
1. Data zone hardware must reside in an access-controlled cage with recorded entry.
2. Out-of-band management networks must be physically separate, not VLAN-separated.
