from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Callable
from urllib import request

from .models import AgentResult, AgentSpec, Task


class Agent(ABC):
    def __init__(self, spec: AgentSpec) -> None:
        self.spec = spec
        self.active_tasks = 0

    @abstractmethod
    def execute(self, task: Task) -> AgentResult:
        raise NotImplementedError


class FunctionAgent(Agent):
    """Local agent adapter for demos, tests, and deterministic workflows."""

    def __init__(self, spec: AgentSpec, handler: Callable[[Task], str]) -> None:
        super().__init__(spec)
        self.handler = handler

    def execute(self, task: Task) -> AgentResult:
        try:
            output = self.handler(task)
            return AgentResult(
                agent_id=self.spec.id,
                task_id=task.id,
                success=True,
                output=output,
            )
        except Exception as exc:  # controller must capture worker failure
            return AgentResult(
                agent_id=self.spec.id,
                task_id=task.id,
                success=False,
                output="",
                error=str(exc),
            )


class HttpAgent(Agent):
    """Adapter for a remote agent exposed through a simple JSON HTTP endpoint."""

    def __init__(self, spec: AgentSpec, endpoint: str, timeout_seconds: int = 30) -> None:
        super().__init__(spec)
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds

    def execute(self, task: Task) -> AgentResult:
        payload = json.dumps(
            {
                "task_id": task.id,
                "objective": task.objective,
                "metadata": task.metadata,
            }
        ).encode("utf-8")
        req = request.Request(
            self.endpoint,
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
            return AgentResult(
                agent_id=self.spec.id,
                task_id=task.id,
                success=bool(body.get("success", True)),
                output=str(body.get("output", "")),
                error=body.get("error"),
            )
        except Exception as exc:
            return AgentResult(
                agent_id=self.spec.id,
                task_id=task.id,
                success=False,
                output="",
                error=str(exc),
            )
