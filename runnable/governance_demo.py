#!/usr/bin/env python3
"""
Runnable Agentic AI Governance Demo
-----------------------------------
A small, dependency-free demonstration of governance-by-design for an
enterprise AI agent.

The demo intentionally uses synthetic data and mock tools. It shows how
policy configuration, least-privilege tool access, human approval gates,
logging/telemetry, redaction, escalation, and a kill switch can be applied
around agent-proposed actions.

This is a portfolio demonstration, not a production control plane.
"""

from __future__ import annotations

import argparse
import json
import os
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set


@dataclass
class GovernanceDecision:
    action_id: str
    tool: str
    risk_tier: str
    decision: str
    reason: str
    executed: bool = False


class AuditLogger:
    """Append-only JSONL logger with simple field-level redaction."""

    def __init__(self, path: Path, redact_keys: Iterable[str]) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.redact_keys = {key.lower() for key in redact_keys}

    def _redact(self, value: Any) -> Any:
        if isinstance(value, Mapping):
            cleaned: Dict[str, Any] = {}
            for key, item in value.items():
                if str(key).lower() in self.redact_keys:
                    cleaned[str(key)] = "<redacted>"
                else:
                    cleaned[str(key)] = self._redact(item)
            return cleaned
        if isinstance(value, list):
            return [self._redact(item) for item in value]
        return value

    def log(self, event_type: str, payload: Mapping[str, Any]) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            **self._redact(dict(payload)),
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


class Telemetry:
    """Minimal runtime telemetry for governance outcomes."""

    def __init__(self) -> None:
        self.started = time.perf_counter()
        self.requested = 0
        self.executed = 0
        self.denied = 0
        self.approval_required = 0
        self.errors = 0

    def summary(self) -> Dict[str, Any]:
        return {
            "requested_actions": self.requested,
            "executed_actions": self.executed,
            "denied_actions": self.denied,
            "approval_required_actions": self.approval_required,
            "errors": self.errors,
            "duration_ms": round((time.perf_counter() - self.started) * 1000, 2),
        }


class PolicyEngine:
    """Evaluate an agent-proposed action against declarative policy."""

    def __init__(self, policy: Mapping[str, Any]) -> None:
        self.policy = dict(policy)

    @property
    def enabled(self) -> bool:
        env = os.getenv("AI_AGENT_ENABLED")
        if env is not None:
            return env.strip().lower() in {"1", "true", "yes", "on"}
        return bool(self.policy.get("agent_enabled", True))

    def evaluate(
        self,
        role: str,
        action: Mapping[str, Any],
        approvals: Set[str],
    ) -> GovernanceDecision:
        action_id = str(action.get("id", "unknown"))
        tool = str(action.get("tool", ""))
        tool_controls = self.policy.get("tools", {})
        control = tool_controls.get(tool, {})
        risk_tier = str(control.get("risk_tier", "unknown"))

        if not self.enabled:
            return GovernanceDecision(
                action_id, tool, risk_tier, "deny",
                "Agent execution is disabled by the governance kill switch."
            )

        if tool in set(self.policy.get("blocked_tools", [])):
            return GovernanceDecision(
                action_id, tool, risk_tier, "deny",
                "Tool is globally blocked by policy."
            )

        roles = self.policy.get("roles", {})
        if role not in roles:
            return GovernanceDecision(
                action_id, tool, risk_tier, "deny",
                f"Unknown or unauthorized role: {role}."
            )

        allowed_tools = set(roles[role].get("allowed_tools", []))
        if tool not in allowed_tools:
            return GovernanceDecision(
                action_id, tool, risk_tier, "deny",
                f"Role '{role}' does not have permission to use '{tool}'."
            )

        if tool not in tool_controls:
            return GovernanceDecision(
                action_id, tool, "unknown", "deny",
                "Tool has no registered governance control."
            )

        if bool(control.get("requires_human_approval", False)) and action_id not in approvals:
            return GovernanceDecision(
                action_id, tool, risk_tier, "approval_required",
                "Policy requires explicit human approval before execution."
            )

        return GovernanceDecision(
            action_id, tool, risk_tier, "allow",
            "Action is permitted by role and tool policy."
        )


class MockToolRegistry:
    """Synthetic tools used only to demonstrate policy enforcement around tool use."""

    def execute(self, tool: str, args: Mapping[str, Any]) -> Dict[str, Any]:
        handlers = {
            "search_documents": self.search_documents,
            "summarize_evidence": self.summarize_evidence,
            "draft_report": self.draft_report,
            "publish_external": self.publish_external,
            "read_restricted_record": self.read_restricted_record,
        }
        if tool not in handlers:
            raise ValueError(f"No tool implementation registered for '{tool}'.")
        return handlers[tool](dict(args))

    @staticmethod
    def search_documents(args: Dict[str, Any]) -> Dict[str, Any]:
        query = str(args.get("query", ""))
        return {
            "query": query,
            "matches": [
                {"document_id": "SYN-001", "score": 0.91},
                {"document_id": "SYN-002", "score": 0.84},
            ],
        }

    @staticmethod
    def summarize_evidence(args: Dict[str, Any]) -> Dict[str, Any]:
        ids = args.get("document_ids", [])
        return {
            "document_ids": ids,
            "summary": "Synthetic evidence summary produced for demonstration.",
            "uncertainty": "medium",
        }

    @staticmethod
    def draft_report(args: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "draft_created",
            "title": str(args.get("title", "Untitled")),
            "evidence_ids": args.get("evidence_ids", []),
        }

    @staticmethod
    def publish_external(args: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "simulated_publish_complete",
            "destination": str(args.get("destination", "unknown")),
            "note": "No external system was contacted.",
        }

    @staticmethod
    def read_restricted_record(args: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "record_id": str(args.get("record_id", "unknown")),
            "personal_data": "synthetic-sensitive-value",
        }


class AgenticGovernanceRunner:
    """Run a pre-defined agent plan through policy before any tool executes."""

    def __init__(
        self,
        policy: Mapping[str, Any],
        audit_path: Path,
        tool_registry: Optional[MockToolRegistry] = None,
    ) -> None:
        self.policy = dict(policy)
        self.engine = PolicyEngine(self.policy)
        self.tools = tool_registry or MockToolRegistry()
        redact_keys = self.policy.get("logging", {}).get(
            "redact_keys",
            ["token", "secret", "password", "personal_data"],
        )
        self.audit = AuditLogger(Path(audit_path), redact_keys)

    def run(
        self,
        scenario: Mapping[str, Any],
        approvals: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        approval_set = set(approvals or [])
        telemetry = Telemetry()
        run_id = str(uuid.uuid4())
        scenario_name = str(scenario.get("name", "unnamed"))
        role = str(scenario.get("actor", {}).get("role", ""))
        actions = list(scenario.get("actions", []))
        max_actions = int(self.policy.get("limits", {}).get("max_actions_per_run", 10))

        self.audit.log("run_started", {
            "run_id": run_id,
            "scenario": scenario_name,
            "role": role,
            "policy_version": self.policy.get("policy_version", "unknown"),
        })

        decisions: List[GovernanceDecision] = []

        if len(actions) > max_actions:
            self.audit.log("anomaly_detected", {
                "run_id": run_id,
                "reason": "max_actions_per_run_exceeded",
                "requested": len(actions),
                "limit": max_actions,
            })
            actions = actions[:max_actions]

        for action in actions:
            telemetry.requested += 1
            self.audit.log("action_proposed", {
                "run_id": run_id,
                "action_id": action.get("id"),
                "tool": action.get("tool"),
                "args": action.get("args", {}),
            })

            decision = self.engine.evaluate(role, action, approval_set)

            if decision.decision == "deny":
                telemetry.denied += 1
                self.audit.log("action_denied", {"run_id": run_id, **asdict(decision)})
                decisions.append(decision)
                continue

            if decision.decision == "approval_required":
                telemetry.approval_required += 1
                self.audit.log("human_approval_required", {"run_id": run_id, **asdict(decision)})
                decisions.append(decision)
                continue

            try:
                result = self.tools.execute(str(action["tool"]), action.get("args", {}))
                decision.executed = True
                telemetry.executed += 1
                self.audit.log("action_executed", {
                    "run_id": run_id,
                    **asdict(decision),
                    "result": result,
                })
            except Exception as exc:
                telemetry.errors += 1
                decision.decision = "error"
                decision.reason = f"Tool execution failed: {type(exc).__name__}"
                self.audit.log("action_error", {"run_id": run_id, **asdict(decision)})

            decisions.append(decision)

        summary = telemetry.summary()
        self.audit.log("run_completed", {"run_id": run_id, "scenario": scenario_name, **summary})

        return {
            "run_id": run_id,
            "scenario": scenario_name,
            "policy_version": self.policy.get("policy_version", "unknown"),
            "decisions": [asdict(item) for item in decisions],
            "telemetry": summary,
            "audit_log": str(self.audit.path),
        }


def load_json(path: Path) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a synthetic agent plan through Responsible AI governance controls."
    )
    parser.add_argument("--scenario", required=True, type=Path)
    parser.add_argument(
        "--policy",
        default=Path(__file__).with_name("policy.json"),
        type=Path,
    )
    parser.add_argument(
        "--audit",
        default=Path(__file__).parent / "artifacts" / "audit.jsonl",
        type=Path,
    )
    parser.add_argument(
        "--approve",
        action="append",
        default=[],
        metavar="ACTION_ID",
        help="Explicitly approve one action ID. Repeat as needed.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    policy = load_json(args.policy)
    scenario = load_json(args.scenario)
    runner = AgenticGovernanceRunner(policy, args.audit)
    result = runner.run(scenario, approvals=args.approve)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
