from __future__ import annotations

import json
from typing import Any, Protocol
from urllib import error, parse, request

from src.execution.connectors.base import ExecutionResult, ExecutionTask


class BufferTransport(Protocol):
    def post_update(self, url: str, headers: dict[str, str], data: bytes, timeout: int) -> dict[str, Any]:
        """Send a Buffer update request and return decoded JSON."""


class UrlLibBufferTransport:
    def post_update(self, url: str, headers: dict[str, str], data: bytes, timeout: int) -> dict[str, Any]:
        req = request.Request(url=url, data=data, headers=headers, method="POST")
        with request.urlopen(req, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
        decoded = json.loads(payload or "{}")
        if not isinstance(decoded, dict):
            raise ValueError("Buffer returned a non-object response.")
        return decoded


class BufferExecutor:
    name = "BufferExecutor"

    def __init__(
        self,
        *,
        access_token: str,
        profile_id: str,
        timezone: str,
        dry_run: bool = True,
        api_base: str = "https://api.bufferapp.com/1",
        transport: BufferTransport | None = None,
    ) -> None:
        self.access_token = access_token
        self.profile_id = profile_id
        self.timezone = timezone
        self.dry_run = dry_run
        self.api_base = api_base.rstrip("/")
        self.transport = transport or UrlLibBufferTransport()

    def execute(self, task: ExecutionTask) -> ExecutionResult:
        if task.connector != self.name:
            return ExecutionResult.failed(
                task,
                timezone=self.timezone,
                error=f"{self.name} cannot execute connector {task.connector}.",
                next_retry=None,
            )

        text = str(task.payload.get("text") or "").strip()
        if not text:
            return ExecutionResult.failed(
                task,
                timezone=self.timezone,
                error="Buffer task payload is missing text.",
                next_retry=None,
            )
        media = task.payload.get("media")
        if task.payload.get("require_media") and not (
            isinstance(media, dict) and (media.get("photo") or media.get("video"))
        ):
            return ExecutionResult.blocked(
                task,
                timezone=self.timezone,
                error="Buffer task requires media proof before publishing.",
                next_retry="after ImageExecutor or VideoExecutor completes",
                result={"required_media": True},
            )
        if task.payload.get("require_public_media") and not str(task.payload.get("public_url") or "").startswith(
            ("http://", "https://")
        ):
            return ExecutionResult.blocked(
                task,
                timezone=self.timezone,
                error="Buffer task requires a public media URL before publishing.",
                next_retry="after ImageExecutor uploads the asset to a public URL",
                result={"required_public_url": True},
            )

        if not self.access_token or not self.profile_id:
            return ExecutionResult.blocked(
                task,
                timezone=self.timezone,
                error="Buffer credentials are not configured.",
                next_retry="tomorrow 08:00 Asia/Jerusalem",
                result={"required_secrets": ["BUFFER_ACCESS_TOKEN", "BUFFER_PROFILE_ID"]},
            )

        if self.dry_run or task.dry_run:
            return ExecutionResult.blocked(
                task,
                timezone=self.timezone,
                error="Execution dry-run is enabled; Buffer publish was not sent.",
                next_retry="next non-dry-run execution window",
                result={"dry_run": True, "profile_id": self.profile_id},
            )

        data = self._encode_payload(task, text)
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        try:
            response = self.transport.post_update(
                f"{self.api_base}/updates/create.json",
                headers,
                data,
                timeout=30,
            )
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            return ExecutionResult.failed(
                task,
                timezone=self.timezone,
                error=f"Buffer HTTP {exc.code}: {body[:300]}",
                next_retry="tomorrow 08:00 Asia/Jerusalem",
            )
        except Exception as exc:
            return ExecutionResult.failed(
                task,
                timezone=self.timezone,
                error=f"Buffer publish failed: {exc}",
                next_retry="tomorrow 08:00 Asia/Jerusalem",
            )

        update = self._extract_update(response)
        update_id = str(update.get("id") or response.get("id") or "")
        update_url = str(
            update.get("instagram_url")
            or update.get("service_link")
            or update.get("url")
            or update.get("permalink")
            or response.get("instagram_url")
            or response.get("url")
            or ""
        )
        if not update_id:
            return ExecutionResult.failed(
                task,
                timezone=self.timezone,
                error="Buffer response did not include an update id.",
                next_retry="tomorrow 08:00 Asia/Jerusalem",
                result={"buffer_response": response},
            )

        proof = {
            "buffer_update_id": update_id,
            "instagram_url": update_url,
            "url": update_url,
            "profile_id": self.profile_id,
            "caption_hash": str(task.payload.get("caption_hash") or ""),
            "image_sha256": str(task.payload.get("image_sha256") or ""),
            "image_path": str(task.payload.get("image_path") or ""),
            "public_url": str(task.payload.get("public_url") or ""),
            "sent_to_buffer": True,
        }
        return ExecutionResult.completed(
            task,
            timezone=self.timezone,
            artifact_ids={
                "buffer_update_id": update_id,
                "instagram_url": update_url,
                "caption_hash": proof["caption_hash"],
                "image_sha256": proof["image_sha256"],
                "public_url": proof["public_url"],
            },
            proof=proof,
            result={"buffer_response": response},
        )

    def _encode_payload(self, task: ExecutionTask, text: str) -> bytes:
        payload: dict[str, Any] = {
            "profile_ids[]": self.profile_id,
            "text": text,
            "now": "true" if task.payload.get("publish_now", True) else "false",
        }
        scheduled_at = task.payload.get("scheduled_at")
        if scheduled_at:
            payload["scheduled_at"] = str(scheduled_at)
        media = task.payload.get("media")
        if isinstance(media, dict):
            for key, value in media.items():
                payload[f"media[{key}]"] = str(value)
        return parse.urlencode(payload).encode("utf-8")

    def _extract_update(self, response: dict[str, Any]) -> dict[str, Any]:
        updates = response.get("updates")
        if isinstance(updates, list) and updates and isinstance(updates[0], dict):
            return updates[0]
        update = response.get("update")
        if isinstance(update, dict):
            return update
        return response
