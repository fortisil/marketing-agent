from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any, Literal, Protocol
from zoneinfo import ZoneInfo


ExecutionStatus = Literal["completed", "blocked", "failed"]


@dataclass(frozen=True)
class ExecutionTask:
    id: str
    connector: str
    action: str
    payload: dict[str, Any]
    delegated_authority_used: str
    initiative: str
    expected_business_impact: str
    dry_run: bool = False
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "connector": self.connector,
            "action": self.action,
            "payload": self.payload,
            "delegated_authority_used": self.delegated_authority_used,
            "initiative": self.initiative,
            "expected_business_impact": self.expected_business_impact,
            "dry_run": self.dry_run,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }


@dataclass(frozen=True)
class ExecutionResult:
    task_id: str
    connector: str
    status: ExecutionStatus
    action: str
    timestamp: str
    artifact_ids: dict[str, str] = field(default_factory=dict)
    proof: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    next_retry: str | None = None
    worker_id: str | None = None

    @classmethod
    def completed(
        cls,
        task: ExecutionTask,
        *,
        timezone: str,
        artifact_ids: dict[str, str],
        proof: dict[str, Any],
        result: dict[str, Any],
    ) -> "ExecutionResult":
        return cls(
            task_id=task.id,
            connector=task.connector,
            status="completed",
            action=task.action,
            timestamp=datetime.now(ZoneInfo(timezone)).isoformat(),
            artifact_ids=artifact_ids,
            proof=proof,
            result=result,
        )

    @classmethod
    def blocked(
        cls,
        task: ExecutionTask,
        *,
        timezone: str,
        error: str,
        next_retry: str,
        result: dict[str, Any] | None = None,
    ) -> "ExecutionResult":
        return cls(
            task_id=task.id,
            connector=task.connector,
            status="blocked",
            action=task.action,
            timestamp=datetime.now(ZoneInfo(timezone)).isoformat(),
            error=error,
            next_retry=next_retry,
            result=result or {},
        )

    @classmethod
    def failed(
        cls,
        task: ExecutionTask,
        *,
        timezone: str,
        error: str,
        next_retry: str | None,
        result: dict[str, Any] | None = None,
    ) -> "ExecutionResult":
        return cls(
            task_id=task.id,
            connector=task.connector,
            status="failed",
            action=task.action,
            timestamp=datetime.now(ZoneInfo(timezone)).isoformat(),
            error=error,
            next_retry=next_retry,
            result=result or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "connector": self.connector,
            "status": self.status,
            "action": self.action,
            "timestamp": self.timestamp,
            "artifact_ids": self.artifact_ids,
            "proof": self.proof,
            "result": self.result,
            "error": self.error,
            "next_retry": self.next_retry,
            "worker_id": self.worker_id,
        }

    def with_worker_evidence(self, worker_id: str) -> "ExecutionResult":
        proof = {
            **self.proof,
            "worker_id": worker_id,
            "timestamp": self.proof.get("timestamp") or self.timestamp,
        }
        return replace(self, proof=proof, worker_id=worker_id)


class ExecutionConnector(Protocol):
    name: str

    def execute(self, task: ExecutionTask) -> ExecutionResult:
        """Execute one task and return proof or a truthful failure state."""
