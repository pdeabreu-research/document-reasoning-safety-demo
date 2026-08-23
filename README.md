# LLM Reasoning Safety & Agentic AI Governance

A public, redacted portfolio demonstrating methods for **Responsible AI, governance-by-design, human oversight, auditability, and reasoning safety** in LLM-assisted workflows.

> **Privacy by design:** all examples are synthetic or anonymized. This repository contains no proprietary prompts, private datasets, case-specific materials, credentials, or production endpoints.

## Two complementary parts

### 1. Runnable Agentic AI Governance Demo

The `runnable/` directory contains a dependency-free Python sandbox showing how an enterprise agent can be wrapped in practical governance controls:

- role-based / least-privilege tool permissions
- policy-configured risk tiers
- action-specific human approval gates
- logging and runtime telemetry
- audit trails with field-level redaction
- deny-by-default behavior
- a configurable emergency kill switch
- synthetic tool execution with no external side effects
- automated tests and CI

**Quick start**

```bash
python runnable/governance_demo.py \
  --scenario runnable/scenarios/approval_required_plan.json
```

Then explicitly approve the high-impact action:

```bash
python runnable/governance_demo.py \
  --scenario runnable/scenarios/approval_required_plan.json \
  --approve publish-1
```

See [`runnable/README.md`](runnable/README.md) for the architecture, scenarios, and test commands.

### 2. Conceptual Reasoning-Safety Artifacts

The `conceptual/`, `docs/`, and `examples/` directories retain non-executable design artifacts for high-stakes document analysis. They emphasize:

- separation of factual extraction from interpretation
- evidence-first reasoning
- explicit uncertainty labeling
- human primacy in consequential judgments
- traceable evidence spans
- escalation when support is ambiguous
- auditability over opaque automation

## Why both layers matter

Responsible AI requires more than a policy document and more than a technical prototype. This repository demonstrates the connection between:

**risk framing → policy requirements → technical controls → human oversight → telemetry → auditable outcomes**

The runnable sandbox focuses on operational controls around agent tool use. The conceptual artifacts focus on reasoning quality, ambiguity, and review boundaries.

## Scope and limitations

This repository is a **portfolio demonstration**, not a production AI platform, legal/compliance tool, or deployment-ready reference implementation.

The runnable demo intentionally uses mock tools and synthetic scenarios so that governance logic can be inspected and tested without credentials, external APIs, or private data. Production use would require authenticated identity, durable authorization, real model/tool integrations, tamper-resistant monitoring, security/privacy engineering, formal evaluation, incident response, and organization-specific validation.
