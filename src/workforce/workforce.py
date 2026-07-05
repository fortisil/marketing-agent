from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.execution.connectors.base import ExecutionConnector, ExecutionResult
from src.execution.connectors.dispatcher import ExecutionDispatcher
from src.execution.evidence import EvidenceValidator
from src.workforce.queue import PersistentTaskQueue
from src.workforce.task import TaskStatus, WorkTask
from src.workforce.worker import Worker


@dataclass(frozen=True)
class WorkforceRunResult:
    workers: list[Worker]
    tasks: list[WorkTask]
    execution_results: list[ExecutionResult]
    escalations: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "workers": [worker.to_dict() for worker in self.workers],
            "tasks": [task.to_dict() for task in self.tasks],
            "execution_results": [result.to_dict() for result in self.execution_results],
            "escalations": self.escalations,
        }


class WorkforceRuntime:
    """Persistent workers that own tasks until connector execution completes."""

    def __init__(
        self,
        *,
        memory_root: Path,
        timezone: str,
        workers: list[Worker],
        connectors: list[ExecutionConnector],
    ) -> None:
        self.queue = PersistentTaskQueue(memory_root)
        self.timezone = timezone
        self.default_workers = workers
        self.dispatcher = ExecutionDispatcher(connectors)
        self.evidence_validator = EvidenceValidator()

    def run(self, new_tasks: list[WorkTask]) -> WorkforceRunResult:
        workers = self._load_workers()
        tasks = self.queue.upsert_tasks(new_tasks)
        completed_task_ids = {
            task.task_id
            for task in tasks
            if task.status in {TaskStatus.COMPLETED, TaskStatus.VERIFIED, TaskStatus.ARCHIVED}
        }
        execution_results: list[ExecutionResult] = []
        escalations: list[dict[str, Any]] = []

        for task in tasks:
            if not task.can_run(completed_task_ids):
                continue
            worker = self._worker_for(task, workers)
            if worker is None:
                escalations.append(
                    {
                        "task_id": task.task_id,
                        "reason": f"No worker with capability {task.capability}.",
                    }
                )
                continue

            timestamp = self._now()
            if task.assigned_worker_id != worker.worker_id:
                task.assign(worker.worker_id, timestamp=timestamp)
            worker.assign(task.task_id, timestamp=timestamp)
            task.mark_executing(timestamp=timestamp)
            result = self.dispatcher.dispatch([task.execution_task])[0]
            result = result.with_worker_evidence(worker.worker_id)
            evidence = self.evidence_validator.validate(result)
            if not evidence.valid:
                result = ExecutionResult.failed(
                    task.execution_task,
                    timezone=self.timezone,
                    error="Evidence validation failed; completed action was not verified.",
                    next_retry="next workforce scheduler run",
                    result={
                        "missing_evidence": evidence.missing,
                        "invalid_evidence": evidence.invalid,
                        "original_result": result.to_dict(),
                    },
                ).with_worker_evidence(worker.worker_id)
            execution_results.append(result)
            worker.record_result(result)

            if result.status == "completed":
                task.record_result(
                    status=TaskStatus.COMPLETED,
                    timestamp=result.timestamp,
                    result=result.to_dict(),
                )
                if result.proof:
                    task.mark_verified(timestamp=result.timestamp, proof=result.proof)
                    completed_task_ids.add(task.task_id)
            elif result.status == "blocked":
                task.record_result(
                    status=TaskStatus.BLOCKED,
                    timestamp=result.timestamp,
                    result=result.to_dict(),
                )
                escalations.append(
                    {
                        "task_id": task.task_id,
                        "worker_id": worker.worker_id,
                        "reason": result.error,
                        "next_retry": result.next_retry,
                    }
                )
            else:
                task.record_result(
                    status=TaskStatus.FAILED,
                    timestamp=result.timestamp,
                    result=result.to_dict(),
                )
                escalations.append(
                    {
                        "task_id": task.task_id,
                        "worker_id": worker.worker_id,
                        "reason": result.error,
                        "next_retry": result.next_retry,
                    }
                )
            worker.release_if_done()

        self.queue.save_tasks(tasks)
        self.queue.save_workers(workers)
        return WorkforceRunResult(
            workers=workers,
            tasks=tasks,
            execution_results=execution_results,
            escalations=escalations,
        )

    def _load_workers(self) -> list[Worker]:
        existing = {worker.worker_id: worker for worker in self.queue.load_workers()}
        for worker in self.default_workers:
            existing.setdefault(worker.worker_id, worker)
        return list(existing.values())

    def _worker_for(self, task: WorkTask, workers: list[Worker]) -> Worker | None:
        if task.assigned_worker_id:
            for worker in workers:
                if worker.worker_id == task.assigned_worker_id and worker.can_execute(task.capability):
                    return worker
        candidates = [worker for worker in workers if worker.can_execute(task.capability)]
        if not candidates:
            return None
        return sorted(
            candidates,
            key=lambda worker: (
                worker.current_task is not None,
                worker.retry_count,
            ),
        )[0]

    def _now(self) -> str:
        return datetime.now(ZoneInfo(self.timezone)).isoformat()
