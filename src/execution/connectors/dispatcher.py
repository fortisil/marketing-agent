from __future__ import annotations

from typing import Any

from src.execution.connectors.base import ExecutionConnector, ExecutionResult, ExecutionTask


class ExecutionDispatcher:
    """Dispatches approved tasks to execution connectors."""

    def __init__(self, connectors: list[ExecutionConnector]) -> None:
        self.connectors = {connector.name: connector for connector in connectors}

    def dispatch(self, tasks: list[ExecutionTask]) -> list[ExecutionResult]:
        results: list[ExecutionResult] = []
        for task in tasks:
            connector = self.connectors.get(task.connector)
            if connector is None:
                results.append(
                    ExecutionResult.failed(
                        task,
                        timezone=str(task.payload.get("timezone", "Asia/Jerusalem")),
                        error=f"No connector registered for {task.connector}.",
                        next_retry=None,
                    )
                )
                continue
            results.append(connector.execute(task))
        return results

    def to_dict(self) -> dict[str, Any]:
        return {"connectors": sorted(self.connectors)}
