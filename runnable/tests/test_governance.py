import tempfile
import unittest
from pathlib import Path
import sys

RUNNABLE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNNABLE))

from governance_demo import AgenticGovernanceRunner, load_json  # noqa: E402


class GovernanceDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = load_json(RUNNABLE / "policy.json")
        cls.scenarios = RUNNABLE / "scenarios"

    def run_scenario(self, name, approvals=None):
        with tempfile.TemporaryDirectory() as tmp:
            runner = AgenticGovernanceRunner(
                self.policy,
                Path(tmp) / "audit.jsonl",
            )
            scenario = load_json(self.scenarios / name)
            return runner.run(scenario, approvals=approvals or [])

    def test_low_risk_plan_executes(self):
        result = self.run_scenario("low_risk_plan.json")
        self.assertEqual(result["telemetry"]["executed_actions"], 3)
        self.assertEqual(result["telemetry"]["denied_actions"], 0)
        self.assertEqual(result["telemetry"]["approval_required_actions"], 0)

    def test_external_publish_requires_human_approval(self):
        result = self.run_scenario("approval_required_plan.json")
        decisions = {d["action_id"]: d for d in result["decisions"]}
        self.assertEqual(decisions["publish-1"]["decision"], "approval_required")
        self.assertFalse(decisions["publish-1"]["executed"])

    def test_external_publish_executes_after_explicit_approval(self):
        result = self.run_scenario(
            "approval_required_plan.json",
            approvals=["publish-1"],
        )
        decisions = {d["action_id"]: d for d in result["decisions"]}
        self.assertEqual(decisions["publish-1"]["decision"], "allow")
        self.assertTrue(decisions["publish-1"]["executed"])

    def test_role_based_access_control_denies_restricted_tool(self):
        result = self.run_scenario("restricted_tool_plan.json")
        decisions = {d["action_id"]: d for d in result["decisions"]}
        self.assertEqual(decisions["restricted-1"]["decision"], "deny")
        self.assertFalse(decisions["restricted-1"]["executed"])
        self.assertTrue(decisions["search-1"]["executed"])


if __name__ == "__main__":
    unittest.main()
