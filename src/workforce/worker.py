from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.execution.connectors.base import ExecutionResult


class WorkerStatus(str, Enum):
    IDLE = "IDLE"
    WORKING = "WORKING"
    WAITING_FOR_CONNECTOR = "WAITING_FOR_CONNECTOR"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"


@dataclass
class Worker:
    worker_id: str
    department: str
    capabilities: list[str]
    current_task: str | None = None
    status: WorkerStatus = WorkerStatus.IDLE
    last_execution: str | None = None
    retry_count: int = 0
    execution_history: list[dict[str, Any]] = field(default_factory=list)
    kpis: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Worker":
        return cls(
            worker_id=str(payload["worker_id"]),
            department=str(payload["department"]),
            capabilities=[str(item) for item in payload.get("capabilities", [])],
            current_task=payload.get("current_task"),
            status=WorkerStatus(str(payload.get("status", WorkerStatus.IDLE.value))),
            last_execution=payload.get("last_execution"),
            retry_count=int(payload.get("retry_count", 0)),
            execution_history=[item for item in payload.get("execution_history", []) if isinstance(item, dict)],
            kpis=payload.get("kpis", {}) if isinstance(payload.get("kpis", {}), dict) else {},
        )

    def can_execute(self, capability: str) -> bool:
        return capability in self.capabilities

    def assign(self, task_id: str, *, timestamp: str) -> None:
        self.current_task = task_id
        self.status = WorkerStatus.WORKING
        self.last_execution = timestamp
        self.execution_history.append({"timestamp": timestamp, "event": "assigned", "task_id": task_id})

    def record_result(self, result: ExecutionResult) -> None:
        self.last_execution = result.timestamp
        self.execution_history.append(
            {
                "timestamp": result.timestamp,
                "event": "execution_result",
                "task_id": result.task_id,
                "status": result.status,
                "connector": result.connector,
                "error": result.error,
                "proof": result.proof,
            }
        )
        if result.status == "completed":
            self.status = WorkerStatus.COMPLETED
            self.current_task = None
            self.kpis["completed_tasks"] = int(self.kpis.get("completed_tasks", 0)) + 1
        elif result.status == "blocked":
            self.status = WorkerStatus.WAITING_FOR_CONNECTOR
            self.retry_count += 1
            self.kpis["blocked_tasks"] = int(self.kpis.get("blocked_tasks", 0)) + 1
        else:
            self.status = WorkerStatus.FAILED
            self.retry_count += 1
            self.kpis["failed_tasks"] = int(self.kpis.get("failed_tasks", 0)) + 1

    def release_if_done(self) -> None:
        if self.status == WorkerStatus.COMPLETED:
            self.status = WorkerStatus.IDLE

    def to_dict(self) -> dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "department": self.department,
            "capabilities": self.capabilities,
            "current_task": self.current_task,
            "status": self.status.value,
            "last_execution": self.last_execution,
            "retry_count": self.retry_count,
            "execution_history": self.execution_history,
            "kpis": self.kpis,
        }
