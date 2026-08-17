from __future__ import annotations

from dataclasses import asdict

from .agents import Agent
from .models import AgentResult, AuditEvent, Task, TaskStatus


class NoEligibleAgent(RuntimeError):
    pass


class ApprovalRequired(RuntimeError):
    pass


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        if agent.spec.id in self._agents:
            raise ValueError(f"Agent '{agent.spec.id}' is already registered")
        self._agents[agent.spec.id] = agent

    def get(self, agent_id: str) -> Agent:
        return self._agents[agent_id]

    def eligible(self, task: Task) -> list[Agent]:
        candidates = [
            agent
            for agent in self._agents.values()
            if task.required_capabilities.issubset(agent.spec.capabilities)
            and agent.active_tasks < agent.spec.max_concurrency
        ]
        return sorted(
            candidates,
            key=lambda a: (a.active_tasks / a.spec.max_concurrency, a.spec.id),
        )

    def snapshot(self) -> list[dict[str, object]]:
        return [
            {
                "id": agent.spec.id,
                "capabilities": sorted(agent.spec.capabilities),
                "active_tasks": agent.active_tasks,
                "max_concurrency": agent.spec.max_concurrency,
                "risk_level": agent.spec.risk_level,
            }
            for agent in self._agents.values()
        ]


class ControlPlane:
    """Supervisor for routing, approvals, retries, load control, and auditability."""

    def __init__(self, registry: AgentRegistry, max_retries: int = 1) -> None:
        self.registry = registry
        self.max_retries = max_retries
        self.audit_log: list[AuditEvent] = []
        self.approved_tasks: set[str] = set()

    def approve(self, task_id: str) -> None:
        self.approved_tasks.add(task_id)
        self._audit("approval_granted", task_id)

    def _requires_gate(self, task: Task, agent: Agent) -> bool:
        return task.requires_approval or agent.spec.risk_level == "high"

    def route(self, task: Task) -> Agent:
        candidates = self.registry.eligible(task)
        if not candidates:
            raise NoEligibleAgent(
                f"No available agent has capabilities: {sorted(task.required_capabilities)}"
            )
        chosen = candidates[0]
        self._audit("task_routed", task.id, chosen.spec.id)
        return chosen

    def execute(self, task: Task) -> AgentResult:
        agent = self.route(task)

        if self._requires_gate(task, agent) and task.id not in self.approved_tasks:
            task.status = TaskStatus.WAITING_APPROVAL
            self._audit("approval_required", task.id, agent.spec.id)
            raise ApprovalRequired(
                f"Task {task.id} requires approval before agent '{agent.spec.id}' may run it"
            )

        agent.active_tasks += 1
        task.status = TaskStatus.RUNNING
        self._audit("execution_started", task.id, agent.spec.id)

        try:
            last_result: AgentResult | None = None
            for attempt in range(1, self.max_retries + 2):
                result = agent.execute(task)
                result.attempts = attempt
                last_result = result
                if result.success:
                    task.status = TaskStatus.SUCCEEDED
                    self._audit("execution_succeeded", task.id, agent.spec.id)
                    return result
                self._audit(
                    "execution_failed_attempt",
                    task.id,
                    agent.spec.id,
                    result.error or "unknown error",
                )

            task.status = TaskStatus.FAILED
            self._audit("execution_failed", task.id, agent.spec.id)
            assert last_result is not None
            return last_result
        finally:
            agent.active_tasks -= 1

    def run_pipeline(self, objective: str) -> dict[str, AgentResult]:
        """Run a research -> analysis -> review supervisor workflow."""
        research = Task(objective=objective, required_capabilities={"research"})
        research_result = self.execute(research)

        analysis = Task(
            objective=f"Analyse this research for the original objective: {objective}",
            required_capabilities={"analysis"},
            metadata={"research": research_result.output},
        )
        analysis_result = self.execute(analysis)

        review = Task(
            objective=f"Review the proposed analysis for: {objective}",
            required_capabilities={"review"},
            metadata={"analysis": analysis_result.output},
        )
        review_result = self.execute(review)

        return {
            "research": research_result,
            "analysis": analysis_result,
            "review": review_result,
        }

    def audit_as_dicts(self) -> list[dict[str, object]]:
        return [asdict(event) for event in self.audit_log]

    def _audit(
        self,
        event: str,
        task_id: str,
        agent_id: str | None = None,
        detail: str = "",
    ) -> None:
        self.audit_log.append(
            AuditEvent(event=event, task_id=task_id, agent_id=agent_id, detail=detail)
        )
