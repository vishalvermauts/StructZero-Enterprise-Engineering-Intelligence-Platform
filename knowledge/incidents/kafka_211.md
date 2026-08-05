---
{
  "title": "Incident 211: Kafka Consumer Lag Cascade",
  "category": "Incident",
  "tags": [
    "Kafka",
    "Backpressure",
    "Outage"
  ],
  "technology": [
    "Kafka"
  ],
  "priority": "High",
  "confidence": 1.0,
  "version": "1.0",
  "architecture_pattern": "Event Driven",
  "document_type": "Post-Incident Review",
  "author": "SAMPLE - synthetic content, not a real policy"
}
---
*Sample standard supplied with StructZero for demonstration. Not a real corporate policy.*

# Incident 211: Kafka Consumer Lag Cascade

On 2026-02-19 a slow downstream database caused consumer lag to grow unbounded across 14
partitions. Retention expired before consumers caught up and 41 minutes of events were lost
permanently.

## Root Cause
A single consumer group had no lag alerting and no dead-letter path. Backpressure propagated
upstream until producers began timing out.

## Lessons Learned & Requirements
1. Every consumer group must have a lag SLO with alerting at 50% of retention.
2. Any consumer performing database writes must have a dead-letter topic and bounded retry.
3. Retention must exceed the worst observed recovery time by at least a factor of three.
4. Designs using Kafka must state partition count and per-partition throughput assumptions.
