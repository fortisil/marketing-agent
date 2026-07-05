from __future__ import annotations

import unittest
from typing import Any

from src.execution.connectors import BufferExecutor, ExecutionTask


def _task(dry_run: bool = False) -> ExecutionTask:
    return ExecutionTask(
        id="buffer-test",
        connector="BufferExecutor",
        action="publish_social_post",
        payload={"text": "Test post", "publish_now": True},
        delegated_authority_used="marketing.publish_posts",
        initiative="Acquire first paying law firms",
        expected_business_impact="High",
        dry_run=dry_run,
    )


class FakeBufferTransport:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def post_update(self, url: str, headers: dict[str, str], data: bytes, timeout: int) -> dict[str, Any]:
        self.calls.append({"url": url, "headers": headers, "data": data, "timeout": timeout})
        return self.response


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
        transport = FakeBufferTransport({"updates": [{"id": "ignored"}]})
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
                "success": True,
                "updates": [
                    {
                        "id": "update_123",
                        "url": "https://buffer.com/app/posts/update_123",
                    }
                ],
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
        self.assertEqual(result.artifact_ids["buffer_update_id"], "update_123")
        self.assertEqual(result.proof["url"], "https://buffer.com/app/posts/update_123")
        self.assertEqual(len(transport.calls), 1)

    def test_image_required_post_blocks_without_media(self) -> None:
        transport = FakeBufferTransport({"updates": [{"id": "ignored"}]})
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


if __name__ == "__main__":
    unittest.main()
