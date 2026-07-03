from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from src.decisions.engine import DecisionContext


@dataclass(frozen=True)
class OutputResult:
    channel: str
    paths: dict[str, Path]
    message: str


class OutputChannel(Protocol):
    name: str

    def deliver(
        self,
        decision_context: DecisionContext,
        brief: str,
        sent: bool,
        dry_run: bool,
        delivery: dict[str, Any] | None = None,
    ) -> OutputResult:
        """Persist or deliver a generated AI CMO brief."""
