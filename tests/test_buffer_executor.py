from __future__ import annotations

import io
import unittest
from typing import Any
from urllib.error import HTTPError

from src.execution.connectors import BufferExecutor, ExecutionTask


def _task(dry_run: bool = False) -> ExecutionTask:
    return ExecutionTask(
        id="buffer-test",
        connector="BufferExecutor",
        action="publish_social_post",
        payload={
            "text": "Test post",
            "publish_now": True,
            "caption_hash": "a" * 64,
            "image_sha256": "b" * 64,
            "image_path": "/tmp/image.png",
            "public_url": "https://cdn.example.com/image.png",
        },
        delegated_authority_used="marketing.publish_posts",
        initiative="Acquire first paying law firms",
        expected_business_impact="High",
        dry_run=dry_run,
    )


class FakeBufferTransport:
    def __init__(self, responses: dict[str, Any] | list[dict[str, Any]]) -> None:
        self.responses = responses if isinstance(responses, list) else [responses]
        self.calls: list[dict[str, Any]] = []

    def post_graphql(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout: int,
    ) -> dict[str, Any]:
        self.calls.append({"url": url, "headers": headers, "payload": payload, "timeout": timeout})
        return self.responses.pop(0)


class FailingBufferTransport:
    def post_graphql(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout: int,
    ) -> dict[str, Any]:
        raise HTTPError(
            url,
            401,
            "Unauthorized",
            {},
            io.BytesIO(b'{"error":"Public API tokens are not accepted for REST API access","code":401}'),
        )


class BufferExecutorTests(unittest.TestCase):
    def test_missing_credentials_blocks_without_claiming_publish(self) -> None:
        result = BufferExecutor(
            access_token="",
            profile_id="",
            timezone="Asia/Jerusalem",
            dry_run=False,
        ).execute(_task())

        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.artifact_ids, {})
        self.assertIn("BUFFER_ACCESS_TOKEN", result.result["required_secrets"])

    def test_dry_run_blocks_without_http_call(self) -> None:
        transport = FakeBufferTransport({"data": {"createPost": {"post": {"id": "ignored"}}}})
        result = BufferExecutor(
            access_token="token",
            profile_id="profile",
            timezone="Asia/Jerusalem",
            dry_run=True,
            transport=transport,
        ).execute(_task())

        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.error, "Execution dry-run is enabled; Buffer publish was not sent.")
        self.assertEqual(transport.calls, [])

    def test_success_requires_buffer_update_id_as_proof(self) -> None:
        transport = FakeBufferTransport(
            {
                "data": {
                    "createPost": {
                        "post": {
                            "id": "post_123",
                            "status": "sent",
                            "externalLink": "https://www.instagram.com/p/test/",
                            "shareMode": "shareNow",
                        }
                    }
                },
            }
        )
        result = BufferExecutor(
            access_token="token",
            profile_id="profile",
            timezone="Asia/Jerusalem",
            dry_run=False,
            transport=transport,
        ).execute(_task())

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.artifact_ids["buffer_update_id"], "post_123")
        self.assertEqual(result.artifact_ids["buffer_post_id"], "post_123")
        self.assertEqual(result.proof["instagram_url"], "https://www.instagram.com/p/test/")
        self.assertEqual(result.proof["caption_hash"], "a" * 64)
        self.assertEqual(result.proof["image_sha256"], "b" * 64)
        self.assertEqual(result.proof["public_url"], "https://cdn.example.com/image.png")
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(transport.calls[0]["url"], "https://api.buffer.com")
        self.assertEqual(transport.calls[0]["headers"]["Authorization"], "Bearer token")
        variables = transport.calls[0]["payload"]["variables"]
        self.assertEqual(variables["input"]["channelId"], "profile")
        self.assertEqual(variables["input"]["mode"], "shareNow")
        self.assertEqual(
            variables["input"]["assets"],
            [{"image": {"url": "https://cdn.example.com/image.png"}}],
        )
        self.assertEqual(
            variables["input"]["metadata"],
            {"instagram": {"type": "post", "shouldShareToFeed": True}},
        )

    def test_image_required_post_blocks_without_media(self) -> None:
        transport = FakeBufferTransport({"data": {"createPost": {"post": {"id": "ignored"}}}})
        task = ExecutionTask(
            id="buffer-test",
            connector="BufferExecutor",
            action="publish_social_post",
            payload={"text": "Test post", "publish_now": True, "require_media": True},
            delegated_authority_used="marketing.publish_posts",
            initiative="Acquire first paying law firms",
            expected_business_impact="High",
        )
        result = BufferExecutor(
            access_token="token",
            profile_id="profile",
            timezone="Asia/Jerusalem",
            dry_run=False,
            transport=transport,
        ).execute(task)

        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.error, "Buffer task requires media proof before publishing.")
        self.assertEqual(transport.calls, [])

    def test_public_media_required_blocks_without_public_url(self) -> None:
        transport = FakeBufferTransport({"data": {"createPost": {"post": {"id": "ignored"}}}})
        task = ExecutionTask(
            id="buffer-test",
            connector="BufferExecutor",
            action="publish_social_post",
            payload={
                "text": "Test post",
                "publish_now": True,
                "require_media": True,
                "require_public_media": True,
                "media": {"photo": "https://cdn.example.com/image.png"},
            },
            delegated_authority_used="marketing.publish_posts",
            initiative="Acquire first paying law firms",
            expected_business_impact="High",
        )
        result = BufferExecutor(
            access_token="token",
            profile_id="profile",
            timezone="Asia/Jerusalem",
            dry_run=False,
            transport=transport,
        ).execute(task)

        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.error, "Buffer task requires a public media URL before publishing.")
        self.assertEqual(transport.calls, [])

    def test_unauthorized_token_type_fails_fast(self) -> None:
        result = BufferExecutor(
            access_token="token",
            profile_id="profile",
            timezone="Asia/Jerusalem",
            dry_run=False,
            transport=FailingBufferTransport(),
        ).execute(_task())

        self.assertEqual(result.status, "failed")
        self.assertIn(
            "Invalid Buffer token type. Need OAuth access token with publishing permissions.",
            result.error or "",
        )

    def test_check_connection_verifies_account_channel_and_draft(self) -> None:
        transport = FakeBufferTransport(
            [
                {
                    "data": {
                        "account": {
                            "id": "account_123",
                            "organizations": [{"id": "org_123", "name": "ChatBot2U"}],
                        }
                    }
                },
                {
                    "data": {
                        "channel": {
                            "id": "channel_123",
                            "displayName": "@chatbot2u",
                            "service": "instagram",
                            "isQueuePaused": False,
                        }
                    }
                },
                {
                    "data": {
                        "createPost": {
                            "post": {
                                "id": "draft_123",
                                "status": "draft",
                            }
                        }
                    }
                },
            ]
        )

        result = BufferExecutor(
            access_token="token",
            profile_id="channel_123",
            timezone="Asia/Jerusalem",
            dry_run=False,
            transport=transport,
        ).check_connection()

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["buffer_token_type"], "accepted")
        self.assertTrue(result["profile_accessible"])
        self.assertEqual(result["draft_create"], "created")
        self.assertEqual(result["validation_post_id"], "draft_123")
        self.assertEqual(transport.calls[2]["payload"]["variables"]["input"]["saveToDraft"], True)


if __name__ == "__main__":
    unittest.main()
