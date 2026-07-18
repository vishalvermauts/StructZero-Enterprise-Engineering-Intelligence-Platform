---
{
  "title": "Incident 104: Redis Cluster Crash",
  "category": "Incident",
  "tags": ["Redis", "Outage", "Postmortem", "Database"],
  "technology": ["Redis"],
  "priority": "High",
  "confidence": 0.95,
  "version": "1.0"
}
---

# Incident 104: Redis Cluster Crash

On 2025-04-12, the primary Redis cluster backing the payments service crashed due to unbounded queries fetching all active sessions without pagination.

## Lessons Learned & Requirements
1. All Redis queries must have explicit boundaries or timeouts.
2. A single database deployment for Redis is prohibited; Multi-AZ clusters are required to prevent SPOF (Single Point of Failure).
3. Circuit breaker patterns must be implemented around Redis calls to fail gracefully.
