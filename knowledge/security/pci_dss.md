---
{
  "title": "PCI DSS v4 Standards",
  "category": "Compliance",
  "tags": ["PCI", "Payments", "Security", "Tokenization"],
  "compliance": ["PCI-DSS"],
  "priority": "Critical",
  "confidence": 0.98,
  "version": "4.0"
}
---

# PCI DSS v4 Requirements

Cardholder data environments (CDE) must be strictly segmented from all other network traffic.

## Tokenization Rules
1. Tokenization must be applied at the edge layer before data reaches internal microservices.
2. Under no circumstances should plain-text PAN (Primary Account Number) be stored or transmitted through internal message brokers like Kafka or RabbitMQ.
3. TLS 1.3 must be enforced for all transit.
