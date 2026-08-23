# Runnable Agentic AI Governance Demo

A small, dependency-free Python demonstration of **governance-by-design** for an enterprise AI agent.

It is intentionally synthetic. No external API, model provider, credential, private dataset, or production system is required.

## What this demonstrates

- **Bounded autonomy:** an agent plan cannot execute outside declared policy.
- **Least-privilege tool access:** each role receives an explicit tool allowlist.
- **Human approval gates:** high-impact write actions pause until an action-specific approval is supplied.
- **Logging and telemetry:** proposed actions, governance decisions, executions, and run summaries are recorded in JSONL.
- **Data minimization:** configured sensitive fields are redacted before audit events are written.
- **Policy-as-control:** tool risk tiers and approval requirements live in `policy.json`, not hard-coded in the agent plan.
- **Kill switch:** `AI_AGENT_ENABLED=false` disables tool execution without code changes.
- **Deny-by-default behavior:** unregistered, blocked, or unauthorized tools do not execute.
- **Synthetic tool use:** mock tools make the control flow runnable without creating external side effects.

## Architecture

```text
agent plan (JSON)
      |
      v
PolicyEngine ---- policy.json / role allowlist / tool controls
      |
      +---- deny --------------------------> audit log
      |
      +---- approval required ------------> human gate + audit log
      |
      +---- allow
              |
              v
       MockToolRegistry
              |
              v
      execution result + telemetry + audit log
```

## Quick start

Requires **Python 3.9+** and no third-party packages.

From the repository root:

```bash
python runnable/governance_demo.py \
  --scenario runnable/scenarios/low_risk_plan.json
```

The result includes per-action governance decisions, execution status, runtime telemetry, and the path to the append-only audit log.

### Approval-gated action

First run without approval:

```bash
python runnable/governance_demo.py \
  --scenario runnable/scenarios/approval_required_plan.json
```

The `publish-1` action is not executed. It returns `approval_required`.

Then run with explicit human approval:

```bash
python runnable/governance_demo.py \
  --scenario runnable/scenarios/approval_required_plan.json \
  --approve publish-1
```

Only that named action receives approval.

### Least-privilege denial

```bash
python runnable/governance_demo.py \
  --scenario runnable/scenarios/restricted_tool_plan.json
```

The technically available `read_restricted_record` tool is denied because the `research_assistant` role is not allowed to use it.

### Emergency pause / kill switch

```bash
AI_AGENT_ENABLED=false python runnable/governance_demo.py \
  --scenario runnable/scenarios/low_risk_plan.json
```

All tool actions are denied while the agent is disabled.

## Run tests

```bash
python -m unittest discover -s runnable/tests -v
```

The repository also includes a GitHub Actions workflow that runs these tests on each push or pull request.

## Files

- `governance_demo.py` — policy engine, mock tool registry, audit logging, telemetry, and CLI.
- `policy.json` — role permissions, tool risk tiers, approval requirements, blocked tools, limits, and redaction settings.
- `system_policy.txt` — illustrative system-level behavioral instructions.
- `scenarios/` — synthetic agent plans covering normal, approval-gated, and denied actions.
- `tests/` — automated tests for allow, deny, and human-approval behavior.
- `artifacts/` — generated audit logs (ignored by Git).

## Scope

This is a **portfolio demonstration**, not a production agent platform, security control plane, or regulatory compliance system. A production deployment would require authenticated identity, durable authorization, real model/tool integrations, tamper-resistant telemetry, incident response, model evaluation, privacy/security engineering, and organization-specific validation.
