# StructZero Enterprise CoCo - System Architecture

**StructZero Enterprise CoCo is an Enterprise Engineering Intelligence Platform built on Snowflake Cortex. It combines an Engineering Knowledge Platform, Multi-Agent Architecture Review Board, Observability Engine, and MCP-native Knowledge Server to help engineering teams design, review, validate, and continuously evolve production software systems.**

This document outlines the system's architecture, its independent subsystems, and the evolutionary roadmap for the platform.

---

## 1. System Overview

StructZero Enterprise CoCo is decomposed into a clean separation of concerns, built natively on Snowflake. Instead of a single pipeline, it operates as independent, interacting engines:

```text
                   StructZero Enterprise

                 ┌──────────────────────┐
                 │ Engineering Knowledge│
                 │      Platform        │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │    Policy Engine     │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │      Enterprise      │
                 │ Architecture Review  │
                 │        Board         │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Validation Engine    │
                 │  + Observability     │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ MCP Knowledge Server │
                 └──────────────────────┘
```

- **Knowledge Platform** → What the system knows.
- **Policy Engine** → What the organization requires.
- **Architecture Review Board** → What the AI proposes and critiques.
- **Validation Engine** → What can be deterministically verified.
- **Observability** → How the pipeline performed.
- **MCP Server** → How external tools consume the platform.

---

## 2. The Engineering Knowledge Platform

The foundation of the system is the Knowledge Platform, treating Snowflake as an enterprise brain. 

### Responsibilities
- Document ingestion
- Chunk generation
- Metadata extraction
- Registry
- Retrieval
- Version tracking
- Future embeddings
- Future vector search
- Future knowledge graph

### Knowledge Registry
The registry acts as the control plane for ingestion:
- Prevent duplicate ingestion
- Track versions
- Track checksums
- Track loader
- Track indexing state
- Track embedding state (future)

### Knowledge Retrieval Pipeline
```text
Prompt
  ↓
Metadata Extraction
  ↓
Knowledge Search
  ↓
Ranking
  ↓
Top K Chunks
  ↓
Architect
```

### Progressive Knowledge Architecture
The platform is designed to scale from metadata matching today, to autonomous reasoning tomorrow.

```text
Current
Documents
  ↓
Chunks
  ↓
Metadata
  ↓
Retrieval

Future
Embeddings
  ↓
Hybrid Search
  ↓
Knowledge Graph
  ↓
Engineering Memory
  ↓
Autonomous Reasoning
```

### Future Search Evolution
```text
Current
Metadata Search
  ↓
Future
Hybrid Search (Metadata + Vector + Keyword + Graph)
```

---

## 3. The Policy Engine (New Subsystem)

To decouple hardcoded prompts from enterprise rules, the Policy Engine applies organizational guardrails independently of the knowledge repository. Policies become data.

```text
Knowledge
  ↓
Policy Engine
  ↓
Architect
  ↓
Reviewers
```

**Responsibilities:**
- Mandatory standards
- Compliance rules
- Prohibited technologies
- Approved architecture patterns
- Organizational constraints

---

## 4. Enterprise Architecture Review Board

Formerly known as the "Debate Engine," this subsystem utilizes Snowflake Cortex models to simulate an elite engineering committee.

```text
Architect
  ↓
Critical Review
  ↓
Security Review
  ↓
Performance Review
  ↓
Principal Architect
  ↓
Voting
  ↓
Validation
```

### The Principal Architect (Synthesizer)
The conflict-resolution agent has been upgraded to a **Principal Architect**. It doesn't just merge feedback; it produces structured rationale.

```text
Receives: [Architect Draft, Security Review, Performance Review, Critical Review, Knowledge]
  ↓
Produces: [Decision Log (Accepted, Rejected, Modified)]
  ↓
Outputs: Blueprint V2
```

The Decision Log acts as a first-class artifact, explaining *why* a critique was accepted or rejected, forming the basis of architecture explainability.

---

## 5. Engineering Telemetry (Observability)

Observability is treated as a core subsystem, vital for AI trust and cost management. 

**Measures:**
- Pipeline latency
- Agent latency
- Retrieval latency
- Knowledge usage
- Tokens
- Cost
- Validation score
- Reviewer votes
- Decision count

---

## 6. Storage Layer Evolution

Uses Snowpark to persist application state directly into Snowflake schema-less JSON (`VARIANT`) tables using double-dollar `$${...}$$` string literals.

**Current:**
- Projects
- Blueprints
- Debates
- Observability
- Knowledge Registry
- Knowledge Documents
- Knowledge Chunks

**Future:**
```text
Projects
  ↓
Blueprints
  ↓
Knowledge
  ↓
Memory
  ↓
Experiments
  ↓
Benchmarks
  ↓
Learning
```

---

## 7. MCP Knowledge Server

StructZero exposes its Snowflake-backed intelligence to local IDEs (Cursor, Claude Desktop, etc.) via the Model Context Protocol (MCP) using `fastmcp`.
This allows developers to type queries like *"Check StructZero for how we handle payment processing"* and instantly pull validated blueprints and architecture decisions directly into their editor.

---

## 8. Ultimate Evolution: Engineering Memory

The system is designed to eventually incorporate an **Engineering Memory** layer. This is distinct from the static Knowledge Base; it is the active, learned experience of the organization.

```text
Knowledge
  ↓
Memory
  ↓
Reasoning
  ↓
Blueprint
```

**Memory stores:**
- Previous blueprints
- Previous debates
- Reviewer decisions
- Successful architectures
- Rejected designs
- Lessons learned

### The Long-Term Vision

```text
Knowledge Platform
  ↓
Architecture Review Board
  ↓
Engineering Memory
  ↓
Policy Engine
  ↓
Validation Engine
  ↓
Observability
  ↓
MCP Server
  ↓
Engineering Intelligence Platform
```

With this architecture, StructZero Enterprise CoCo scales from an AI planning tool into an enterprise engineering operating system.
