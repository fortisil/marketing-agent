from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.execution.connectors import ExecutionResult, ExecutionTask
from src.workforce import PersistentTaskQueue, TaskPriority, TaskStatus, WorkforceRuntime, WorkTask, Worker


class FakeConnector:
    name = "FakeConnector"

    def __init__(self, status: str) -> None:
        self.status = status

    def execute(self, task: ExecutionTask) -> ExecutionResult:
        if self.status == "completed":
            return ExecutionResult.completed(
                task,
                timezone="Asia/Jerusalem",
                artifact_ids={"artifact": "artifact_1"},
                proof={"proof_id": "proof_1"},
                result={"ok": True},
            )
        if self.status == "blocked":
            return ExecutionResult.blocked(
                task,
                timezone="Asia/Jerusalem",
                error="Connector unavailable.",
                next_retry="tomorrow 08:00 Asia/Jerusalem",
            )
        return ExecutionResult.failed(
            task,
            timezone="Asia/Jerusalem",
            error="Connector failed.",
            next_retry="tomorrow 08:00 Asia/Jerusalem",
        )


def _task(task_id: str = "task-1") -> WorkTask:
    execution_task = ExecutionTask(
        id=task_id,
        connector="FakeConnector",
        action="do_work",
        payload={"timezone": "Asia/Jerusalem"},
        delegated_authority_used="marketing.publish_posts",
        initiative="Acquire first paying law firms",
        expected_business_impact="High",
    )
    return WorkTask(
        task_id=task_id,
        department="Social",
        capability="publish_social_post",
        title="Publish social post",
        execution_task=execution_task,
        priority=TaskPriority.HIGH,
    )


def _worker() -> Worker:
    return Worker(
        worker_id="social-worker-1",
        department="Social",
        capabilities=["publish_social_post"],
    )


class WorkforceRuntimeTests(unittest.TestCase):
    def test_completed_task_is_verified_and_worker_persists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = WorkforceRuntime(
                memory_root=Path(tmpdir),
                timezone="Asia/Jerusalem",
                workers=[_worker()],
                connectors=[FakeConnector("completed")],
            )
            result = runtime.run([_task()])
            queue = PersistentTaskQueue(Path(tmpdir))

            tasks = queue.load_tasks()
            workers = queue.load_workers()

        self.assertEqual(result.execution_results[0].status, "completed")
        self.assertEqual(tasks[0].status, TaskStatus.VERIFIED)
        self.assertEqual(workers[0].worker_id, "social-worker-1")
        self.assertEqual(workers[0].kpis["completed_tasks"], 1)

    def test_blocked_task_stays_owned_for_retry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = WorkforceRuntime(
                memory_root=Path(tmpdir),
                timezone="Asia/Jerusalem",
                workers=[_worker()],
                connectors=[FakeConnector("blocked")],
            )
            runtime.run([_task()])
            queue = PersistentTaskQueue(Path(tmpdir))
            tasks = queue.load_tasks()
            workers = queue.load_workers()

        self.assertEqual(tasks[0].status, TaskStatus.BLOCKED)
        self.assertEqual(tasks[0].assigned_worker_id, "social-worker-1")
        self.assertEqual(tasks[0].retry_count, 1)
        self.assertEqual(workers[0].current_task, "task-1")
        self.assertEqual(workers[0].kpis["blocked_tasks"], 1)

    def test_blocked_task_refreshes_execution_payload_for_retry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = PersistentTaskQueue(Path(tmpdir))
            blocked = _task()
            blocked.assign("social-worker-1", timestamp="2026-07-05T08:00:00+03:00")
            blocked.status = TaskStatus.BLOCKED
            blocked.retry_count = 1
            queue.save_tasks([blocked])

            refreshed = _task()
            refreshed.execution_task.payload["dry_run"] = False
            refreshed.priority = TaskPriority.MEDIUM
            tasks = queue.upsert_tasks([refreshed])

        self.assertEqual(tasks[0].status, TaskStatus.BLOCKED)
        self.assertEqual(tasks[0].assigned_worker_id, "social-worker-1")
        self.assertEqual(tasks[0].retry_count, 1)
        self.assertIs(tasks[0].execution_task.payload["dry_run"], False)
        self.assertEqual(tasks[0].priority, TaskPriority.MEDIUM)

    def test_dependency_prevents_execution_until_verified(self) -> None:
        dependent = _task("task-2")
        dependent.dependencies = ["task-1"]

        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = WorkforceRuntime(
                memory_root=Path(tmpdir),
                timezone="Asia/Jerusalem",
                workers=[_worker()],
                connectors=[FakeConnector("completed")],
            )
            result = runtime.run([dependent])
            queue = PersistentTaskQueue(Path(tmpdir))
            tasks = queue.load_tasks()

        self.assertEqual(result.execution_results, [])
        self.assertEqual(tasks[0].status, TaskStatus.CREATED)


if __name__ == "__main__":
    unittest.main()
