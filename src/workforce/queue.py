from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.workforce.task import TaskPriority, TaskStatus, WorkTask
from src.workforce.worker import Worker


class PersistentTaskQueue:
    """JSON-backed worker/task memory that survives process restarts."""

    def __init__(self, memory_root: Path) -> None:
        self.root = memory_root / "workforce"
        self.tasks_path = self.root / "tasks.json"
        self.workers_path = self.root / "workers.json"

    def load_tasks(self) -> list[WorkTask]:
        if not self.tasks_path.exists():
            return []
        loaded = json.loads(self.tasks_path.read_text(encoding="utf-8") or "[]")
        if not isinstance(loaded, list):
            return []
        return [WorkTask.from_dict(item) for item in loaded if isinstance(item, dict)]

    def save_tasks(self, tasks: list[WorkTask]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.tasks_path.write_text(
            json.dumps([task.to_dict() for task in tasks], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def load_workers(self) -> list[Worker]:
        if not self.workers_path.exists():
            return []
        loaded = json.loads(self.workers_path.read_text(encoding="utf-8") or "[]")
        if not isinstance(loaded, list):
            return []
        return [Worker.from_dict(item) for item in loaded if isinstance(item, dict)]

    def save_workers(self, workers: list[Worker]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.workers_path.write_text(
            json.dumps([worker.to_dict() for worker in workers], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def upsert_tasks(self, tasks: list[WorkTask]) -> list[WorkTask]:
        existing = {task.task_id: task for task in self.load_tasks()}
        for task in tasks:
            existing_task = existing.get(task.task_id)
            if existing_task and existing_task.status in {TaskStatus.VERIFIED, TaskStatus.ARCHIVED}:
                continue
            if existing_task and existing_task.status in {
                TaskStatus.ASSIGNED,
                TaskStatus.EXECUTING,
                TaskStatus.BLOCKED,
                TaskStatus.FAILED,
            }:
                existing_task.execution_task = task.execution_task
                existing_task.priority = task.priority
                existing_task.deadline = task.deadline
                existing_task.dependencies = task.dependencies
                existing_task.max_retries = task.max_retries
                continue
            existing[task.task_id] = task
        ordered = sorted(
            existing.values(),
            key=lambda task: (
                {TaskPriority.HIGH: 0, TaskPriority.MEDIUM: 1, TaskPriority.LOW: 2}[task.priority],
                task.created_at,
            ),
        )
        self.save_tasks(ordered)
        return ordered

    def snapshot(self) -> dict[str, Any]:
        return {
            "tasks_path": str(self.tasks_path),
            "workers_path": str(self.workers_path),
            "tasks": [task.to_dict() for task in self.load_tasks()],
            "workers": [worker.to_dict() for worker in self.load_workers()],
        }
