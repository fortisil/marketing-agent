from __future__ import annotations

from dataclasses import dataclass

from src.workforce.task import WorkTask
from src.workforce.workforce import WorkforceRunResult, WorkforceRuntime


@dataclass(frozen=True)
class WorkforceScheduler:
    runtime: WorkforceRuntime

    def run_due(self, tasks: list[WorkTask]) -> WorkforceRunResult:
        """Run all due tasks known to the current sprint.

        The durable queue stores retry/dependency state; callers provide the latest
        task definitions each run so workers can continue ownership across restarts.
        """

        return self.runtime.run(tasks)
