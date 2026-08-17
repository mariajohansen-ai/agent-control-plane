from __future__ import annotations

import argparse
import json

from .agents import FunctionAgent
from .models import AgentSpec, Task
from .orchestrator import ApprovalRequired, AgentRegistry, ControlPlane


def build_demo_control_plane() -> ControlPlane:
    registry = AgentRegistry()

    registry.register(
        FunctionAgent(
            AgentSpec(
                id="research-agent",
                description="Collects facts, unknowns, and source requirements.",
                capabilities=frozenset({"research"}),
                max_concurrency=2,
            ),
            lambda task: (
                "Research brief: identify decision criteria, evidence gaps, stakeholders, "
                f"and source requirements for '{task.objective}'."
            ),
        )
    )
    registry.register(
        FunctionAgent(
            AgentSpec(
                id="analysis-agent",
                description="Turns evidence into options, trade-offs, and recommendations.",
                capabilities=frozenset({"analysis"}),
                max_concurrency=2,
            ),
            lambda task: (
                "Analysis: compare options, quantify uncertainty, identify assumptions, and "
                f"derive a recommendation. Input research: {task.metadata.get('research', '')}"
            ),
        )
    )
    registry.register(
        FunctionAgent(
            AgentSpec(
                id="review-agent",
                description="Challenges conclusions and checks governance risks.",
                capabilities=frozenset({"review"}),
            ),
            lambda task: (
                "Review: test the analysis for unsupported claims, missing evidence, risk, "
                f"and decision quality. Input: {task.metadata.get('analysis', '')}"
            ),
        )
    )
    registry.register(
        FunctionAgent(
            AgentSpec(
                id="action-agent",
                description="Represents an agent allowed to take high-impact actions.",
                capabilities=frozenset({"action"}),
                risk_level="high",
            ),
            lambda task: f"Action executed for approved task: {task.objective}",
        )
    )
    return ControlPlane(registry=registry, max_retries=1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Agent Control Plane: one supervisor governing multiple specialist agents."
    )
    parser.add_argument("objective", nargs="?", default="Assess an AI transformation proposal")
    parser.add_argument(
        "--approve-action",
        action="store_true",
        help="Demonstrate the human approval gate for a high-risk action agent.",
    )
    args = parser.parse_args()

    control = build_demo_control_plane()
    results = control.run_pipeline(args.objective)

    output: dict[str, object] = {
        "objective": args.objective,
        "agents": control.registry.snapshot(),
        "pipeline": {name: result.output for name, result in results.items()},
    }

    if args.approve_action:
        action_task = Task(
            objective="Publish the approved recommendation",
            required_capabilities={"action"},
        )
        try:
            control.execute(action_task)
        except ApprovalRequired:
            control.approve(action_task.id)
            output["approved_action"] = control.execute(action_task).output

    output["audit_log"] = control.audit_as_dicts()
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
