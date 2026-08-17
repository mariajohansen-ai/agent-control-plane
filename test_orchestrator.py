import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_control_plane.agents import FunctionAgent
from agent_control_plane.models import AgentSpec, Task, TaskStatus
from agent_control_plane.orchestrator import (
    AgentRegistry,
    ApprovalRequired,
    ControlPlane,
    NoEligibleAgent,
)


class ControlPlaneTests(unittest.TestCase):
    def test_routes_to_capable_agent(self):
        registry = AgentRegistry()
        registry.register(
            FunctionAgent(
                AgentSpec("researcher", "research", frozenset({"research"})),
                lambda task: "done",
            )
        )
        control = ControlPlane(registry)
        task = Task("Find evidence", {"research"})
        result = control.execute(task)
        self.assertTrue(result.success)
        self.assertEqual(result.agent_id, "researcher")
        self.assertEqual(task.status, TaskStatus.SUCCEEDED)

    def test_retries_failure(self):
        attempts = {"count": 0}

        def flaky(task):
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise RuntimeError("temporary failure")
            return "recovered"

        registry = AgentRegistry()
        registry.register(
            FunctionAgent(
                AgentSpec("flaky", "flaky", frozenset({"analysis"})), flaky
            )
        )
        result = ControlPlane(registry, max_retries=1).execute(
            Task("Analyse", {"analysis"})
        )
        self.assertTrue(result.success)
        self.assertEqual(result.attempts, 2)

    def test_high_risk_agent_requires_approval(self):
        registry = AgentRegistry()
        registry.register(
            FunctionAgent(
                AgentSpec(
                    "actor",
                    "takes action",
                    frozenset({"action"}),
                    risk_level="high",
                ),
                lambda task: "executed",
            )
        )
        control = ControlPlane(registry)
        task = Task("Deploy", {"action"})
        with self.assertRaises(ApprovalRequired):
            control.execute(task)
        self.assertEqual(task.status, TaskStatus.WAITING_APPROVAL)

        control.approve(task.id)
        result = control.execute(task)
        self.assertTrue(result.success)

    def test_no_eligible_agent(self):
        control = ControlPlane(AgentRegistry())
        with self.assertRaises(NoEligibleAgent):
            control.execute(Task("Unknown", {"missing"}))


if __name__ == "__main__":
    unittest.main()
