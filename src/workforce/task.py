from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from zoneinfo import ZoneInfo

from src.execution.connectors.base import ExecutionTask


class TaskStatus(str, Enum):
    CREATED = "Created"
    ASSIGNED = "Assigned"
    EXECUTING = "Executing"
    COMPLETED = "Completed"
    VERIFIED = "Verified"
    ARCHIVED = "Archived"
    BLOCKED = "Blocked"
    FAILED = "Failed"


class TaskPriority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class WorkTask:
    task_id: str
    department: str
    capability: str
    title: str
    execution_task: ExecutionTask
    priority: TaskPriority = TaskPriority.MEDIUM
    deadline: str | None = None
    dependencies: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.CREATED
    assigned_worker_id: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: str = ""
    updated_at: str = ""
    history: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        now = datetime.now(ZoneInfo(str(self.execution_task.payload.get("timezone", "Asia/Jerusalem")))).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "WorkTask":
        execution_task = ExecutionTask(**payload["execution_task"])
        return cls(
            task_id=str(payload["task_id"]),
            department=str(payload["department"]),
            capability=str(payload["capability"]),
            title=str(payload["title"]),
            execution_task=execution_task,
            priority=TaskPriority(str(payload.get("priority", TaskPriority.MEDIUM.value))),
            deadline=payload.get("deadline"),
            dependencies=[str(item) for item in payload.get("dependencies", [])],
            status=TaskStatus(str(payload.get("status", TaskStatus.CREATED.value))),
            assigned_worker_id=payload.get("assigned_worker_id"),
            retry_count=int(payload.get("retry_count", 0)),
            max_retries=int(payload.get("max_retries", 3)),
            created_at=str(payload.get("created_at", "")),
            updated_at=str(payload.get("updated_at", "")),
            history=[item for item in payload.get("history", []) if isinstance(item, dict)],
        )

    def assign(self, worker_id: str, *, timestamp: str) -> None:
        self.assigned_worker_id = worker_id
        self.status = TaskStatus.ASSIGNED
        self.updated_at = timestamp
        self.history.append({"timestamp": timestamp, "event": "assigned", "worker_id": worker_id})

    def mark_executing(self, *, timestamp: str) -> None:
        self.status = TaskStatus.EXECUTING
        self.updated_at = timestamp
        self.history.append({"timestamp": timestamp, "event": "executing"})

    def record_result(self, *, status: TaskStatus, timestamp: str, result: dict[str, Any]) -> None:
        self.status = status
        self.updated_at = timestamp
        if status in {TaskStatus.BLOCKED, TaskStatus.FAILED}:
            self.retry_count += 1
        self.history.append({"timestamp": timestamp, "event": status.value.lower(), "result": result})

    def mark_verified(self, *, timestamp: str, proof: dict[str, Any]) -> None:
        self.status = TaskStatus.VERIFIED
        self.updated_at = timestamp
        self.history.append({"timestamp": timestamp, "event": "verified", "proof": proof})

    def can_run(self, completed_task_ids: set[str]) -> bool:
        if self.status in {TaskStatus.VERIFIED, TaskStatus.ARCHIVED, TaskStatus.EXECUTING}:
            return False
        if self.retry_count >= self.max_retries and self.status in {TaskStatus.BLOCKED, TaskStatus.FAILED}:
            return False
        return all(dependency in completed_task_ids for dependency in self.dependencies)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "department": self.department,
            "capability": self.capability,
            "title": self.title,
            "execution_task": self.execution_task.to_dict(),
            "priority": self.priority.value,
            "deadline": self.deadline,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "assigned_worker_id": self.assigned_worker_id,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "history": self.history,
        }
