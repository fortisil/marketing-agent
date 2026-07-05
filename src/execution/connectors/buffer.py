from __future__ import annotations

import json
from typing import Any, Protocol
from urllib import error, request

from src.execution.connectors.base import ExecutionResult, ExecutionTask


class BufferTransport(Protocol):
    def post_graphql(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout: int,
    ) -> dict[str, Any]:
        """Send a Buffer GraphQL request and return decoded JSON."""


class UrlLibBufferTransport:
    def post_graphql(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout: int,
    ) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
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
        api_base: str = "https://api.buffer.com",
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

        try:
            response = self._create_post(task, text)
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            return ExecutionResult.failed(
                task,
                timezone=self.timezone,
                error=self._http_error_message(exc.code, body),
                next_retry="tomorrow 08:00 Asia/Jerusalem",
            )
        except Exception as exc:
            return ExecutionResult.failed(
                task,
                timezone=self.timezone,
                error=f"Buffer publish failed: {exc}",
                next_retry="tomorrow 08:00 Asia/Jerusalem",
            )

        post = self._extract_post(response)
        post_id = str(post.get("id") or "")
        post_url = self._post_url(post_id)
        service_link = str(
            post.get("externalLink")
            or post.get("serviceLink")
            or post.get("url")
            or post.get("permalink")
            or post_url
        )
        if not post_id:
            return ExecutionResult.failed(
                task,
                timezone=self.timezone,
                error="Buffer response did not include a post id.",
                next_retry="tomorrow 08:00 Asia/Jerusalem",
                result={"buffer_response": response},
            )

        proof = {
            "buffer_update_id": post_id,
            "buffer_post_id": post_id,
            "instagram_url": service_link,
            "url": service_link,
            "buffer_post_url": post_url,
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
                "buffer_update_id": post_id,
                "buffer_post_id": post_id,
                "instagram_url": service_link,
                "buffer_post_url": post_url,
                "caption_hash": proof["caption_hash"],
                "image_sha256": proof["image_sha256"],
                "public_url": proof["public_url"],
            },
            proof=proof,
            result={"buffer_response": response},
        )

    def check_connection(self, *, create_validation_draft: bool = True) -> dict[str, Any]:
        if not self.access_token or not self.profile_id:
            return {
                "status": "blocked",
                "buffer_token_type": "missing",
                "profile_accessible": False,
                "draft_create": "skipped",
                "error": "Buffer credentials are not configured.",
                "required_secrets": ["BUFFER_ACCESS_TOKEN", "BUFFER_PROFILE_ID"],
            }

        try:
            account_response = self._graphql(
                """
                query CheckBufferAccount {
                  account {
                    id
                    organizations {
                      id
                      name
                    }
                  }
                }
                """,
                {},
            )
            channel_response = self._graphql(
                """
                query CheckBufferChannel($id: ChannelId!) {
                  channel(input: { id: $id }) {
                    id
                    name
                    displayName
                    service
                    isQueuePaused
                  }
                }
                """,
                {"id": self.profile_id},
            )
            channel = channel_response.get("data", {}).get("channel")
            if not isinstance(channel, dict) or not channel.get("id"):
                return {
                    "status": "failed",
                    "buffer_token_type": "accepted",
                    "profile_accessible": False,
                    "draft_create": "skipped",
                    "error": "BUFFER_PROFILE_ID is not an accessible Buffer channel ID.",
                }

            draft: dict[str, Any] | None = None
            if create_validation_draft:
                draft = self._extract_post(
                    self._create_validation_draft("AI CMO connector validation draft. Safe to delete.")
                )
                if not draft.get("id"):
                    return {
                        "status": "failed",
                        "buffer_token_type": "accepted",
                        "profile_accessible": True,
                        "draft_create": "failed",
                        "channel": self._public_channel(channel),
                        "error": "Buffer validation draft did not return a post id.",
                    }

            return {
                "status": "ok",
                "buffer_token_type": "accepted",
                "profile_accessible": True,
                "draft_create": "created" if create_validation_draft else "skipped",
                "channel": self._public_channel(channel),
                "organization_count": len(
                    account_response.get("data", {}).get("account", {}).get("organizations", [])
                ),
                "validation_post_id": str(draft.get("id")) if draft else "",
                "validation_post_status": str(draft.get("status")) if draft else "",
            }
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            return {
                "status": "failed",
                "buffer_token_type": "invalid",
                "profile_accessible": False,
                "draft_create": "skipped",
                "error": self._http_error_message(exc.code, body),
            }
        except Exception as exc:
            return {
                "status": "failed",
                "buffer_token_type": "unknown",
                "profile_accessible": False,
                "draft_create": "skipped",
                "error": f"Buffer connector check failed: {exc}",
            }

    def _create_post(self, task: ExecutionTask, text: str) -> dict[str, Any]:
        input_payload: dict[str, Any] = {
            "text": text,
            "channelId": self.profile_id,
            "schedulingType": "automatic",
            "mode": "shareNow" if task.payload.get("publish_now", True) else "addToQueue",
            "source": "ai-cmo",
            "aiAssisted": True,
        }
        scheduled_at = task.payload.get("scheduled_at")
        if scheduled_at:
            input_payload["dueAt"] = str(scheduled_at)
            input_payload["mode"] = "customScheduled"
        public_url = str(task.payload.get("public_url") or "")
        if public_url:
            input_payload["assets"] = [{"image": {"url": public_url}}]
        return self._create_post_with_input(input_payload)

    def _create_validation_draft(self, text: str) -> dict[str, Any]:
        return self._create_post_with_input(
            {
                "text": text,
                "channelId": self.profile_id,
                "schedulingType": "automatic",
                "mode": "addToQueue",
                "saveToDraft": True,
                "source": "ai-cmo-connector-check",
                "aiAssisted": True,
            }
        )

    def _create_post_with_input(self, input_payload: dict[str, Any]) -> dict[str, Any]:
        return self._graphql(
            """
            mutation CreatePost($input: CreatePostInput!) {
              createPost(input: $input) {
                ... on PostActionSuccess {
                  post {
                    id
                    text
                    status
                    externalLink
                    dueAt
                    channelId
                    shareMode
                    sharedNow
                    assets {
                      id
                      mimeType
                      source
                    }
                  }
                }
                ... on MutationError {
                  message
                }
              }
            }
            """,
            {"input": input_payload},
        )

    def _graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        response = self.transport.post_graphql(
            self.api_base,
            {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
            {"query": query, "variables": variables},
            timeout=30,
        )
        errors = response.get("errors")
        if isinstance(errors, list) and errors:
            messages = [
                str(item.get("message") or item)
                for item in errors
                if isinstance(item, dict) or item
            ]
            raise ValueError(f"Buffer GraphQL error: {'; '.join(messages)[:300]}")
        create_post = response.get("data", {}).get("createPost")
        mutation_error = create_post.get("message") if isinstance(create_post, dict) else ""
        if mutation_error:
            raise ValueError(f"Buffer createPost error: {mutation_error}")
        return response

    def _extract_post(self, response: dict[str, Any]) -> dict[str, Any]:
        create_post = response.get("data", {}).get("createPost")
        post = create_post.get("post") if isinstance(create_post, dict) else None
        if isinstance(post, dict):
            return post
        return {}

    def _post_url(self, post_id: str) -> str:
        return f"https://publish.buffer.com/post/{post_id}" if post_id else ""

    def _http_error_message(self, status_code: int, body: str) -> str:
        if status_code == 401:
            return (
                "Invalid Buffer token type. Need OAuth access token with publishing permissions. "
                f"Buffer HTTP 401: {body[:300]}"
            )
        return f"Buffer HTTP {status_code}: {body[:300]}"

    def _public_channel(self, channel: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(channel.get("id") or ""),
            "name": str(channel.get("displayName") or channel.get("name") or ""),
            "service": str(channel.get("service") or ""),
            "is_queue_paused": bool(channel.get("isQueuePaused")),
        }
