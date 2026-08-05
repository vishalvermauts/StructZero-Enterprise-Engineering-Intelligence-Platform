---
{
  "title": "Incident 88: Unbounded Cross-Region Egress",
  "category": "Incident",
  "tags": [
    "Cost",
    "Network",
    "Egress",
    "AWS"
  ],
  "cloud": [
    "AWS"
  ],
  "priority": "Medium",
  "confidence": 1.0,
  "version": "1.0",
  "document_type": "Post-Incident Review",
  "author": "SAMPLE - synthetic content, not a real policy"
}
---
*Sample standard supplied with StructZero for demonstration. Not a real corporate policy.*

# Incident 88: Unbounded Cross-Region Egress

On 2025-11-03 a reporting service deployed in us-east-1 began reading from a data store in
eu-west-1. Cross-region egress charges reached $63,000 over nine days before detection.

## Root Cause
The read replica endpoint was region-agnostic in configuration and defaulted to the primary.
No egress budget alarm existed for the account.

## Lessons Learned & Requirements
1. Any design crossing a region boundary must state the expected data volume per day.
2. Read paths must pin to a same-region replica explicitly, never rely on default endpoints.
3. Cost alarms must be defined per account at 20%, 50% and 80% of forecast.
