from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class TaskStatus(str, Enum):
    PENDING = "pending"
    WAITING_APPROVAL = "waiting_approval"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(slots=True)
class Task:
    objective: str
    required_capabilities: set[str]
    priority: int = 5
    requires_approval: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    status: TaskStatus = TaskStatus.PENDING


@dataclass(slots=True, frozen=True)
class AgentSpec:
    id: str
    description: str
    capabilities: frozenset[str]
    max_concurrency: int = 1
    risk_level: str = "low"


@dataclass(slots=True)
class AgentResult:
    agent_id: str
    task_id: str
    success: bool
    output: str
    attempts: int = 1
    error: str | None = None


@dataclass(slots=True)
class AuditEvent:
    event: str
    task_id: str
    agent_id: str | None = None
    detail: str = ""
