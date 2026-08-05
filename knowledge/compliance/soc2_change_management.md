---
{
  "title": "SOC2 Change Management Requirements",
  "category": "Compliance",
  "tags": [
    "SOC2",
    "Change Management",
    "Governance"
  ],
  "compliance": [
    "SOC2"
  ],
  "priority": "High",
  "confidence": 0.95,
  "version": "2.3",
  "document_type": "Policy",
  "author": "SAMPLE - synthetic content, not a real policy"
}
---
*Sample standard supplied with StructZero for demonstration. Not a real corporate policy.*

# SOC2 Change Management Requirements

Change management evidence is the most commonly failed SOC2 control in our audits. Designs
must state how each requirement is met.

## Change Control
1. All production change must originate from a peer-reviewed, version-controlled pull request.
2. Deployment pipelines must be the only path to production; manual access is break-glass only.
3. Rollback procedure must be documented and exercised, not merely asserted.

## Separation of Duties
1. The author of a change must not be its sole approver.
2. Production credentials must not be obtainable by developers in the normal course of work.
3. Emergency changes require retrospective review within five business days.
