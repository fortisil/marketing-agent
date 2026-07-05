from __future__ import annotations

import base64
import tempfile
import unittest
from pathlib import Path
from typing import Any

from src.execution.asset_upload import UploadedAsset
from src.execution.connectors import ExecutionTask, ImageExecutor


def _task(dry_run: bool = False) -> ExecutionTask:
    return ExecutionTask(
        id="image-test",
        connector="ImageExecutor",
        action="generate_branded_social_image",
        payload={
            "run_date": "2026-07-05",
            "prompt": "ChatBot2U branded image using approved colors and logo.",
            "brand_assets": {"colors": ["#111827"], "logo": "logo.svg"},
        },
        delegated_authority_used="marketing.generate_images",
        initiative="Acquire first paying law firms",
        expected_business_impact="High",
        dry_run=dry_run,
    )


class FakeImageClient:
    def __init__(self, image_bytes: bytes) -> None:
        self.image_bytes = image_bytes
        self.calls: list[dict[str, Any]] = []

    def generate(self, *, model: str, prompt: str, size: str) -> dict[str, Any]:
        self.calls.append({"model": model, "prompt": prompt, "size": size})
        return {"data": [{"b64_json": base64.b64encode(self.image_bytes).decode("ascii")}]}


class FakeUploader:
    provider = "cloudinary"

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def upload(self, *, image_path: Path, public_id: str, folder: str) -> UploadedAsset:
        self.calls.append({"image_path": image_path, "public_id": public_id, "folder": folder})
        return UploadedAsset(
            provider="cloudinary",
            public_url=f"https://res.cloudinary.com/demo/image/upload/{folder}/{public_id}.png",
            provider_asset_id=f"{folder}/{public_id}",
            result={"secure_url": "https://res.cloudinary.com/demo/image/upload/file.png"},
        )


class ImageExecutorTests(unittest.TestCase):
    def test_disabled_image_generation_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ImageExecutor(
                api_key="key",
                assets_root=Path(tmpdir),
                timezone="Asia/Jerusalem",
                enabled=False,
                dry_run=False,
            ).execute(_task())

        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.error, "Image generation is disabled for this runtime.")

    def test_brand_validation_failure_does_not_generate(self) -> None:
        client = FakeImageClient(b"png")
        bad_task = ExecutionTask(
            id="bad-image",
            connector="ImageExecutor",
            action="generate_branded_social_image",
            payload={"prompt": "Generic startup picture", "brand_assets": {}},
            delegated_authority_used="marketing.generate_images",
            initiative="Acquire first paying law firms",
            expected_business_impact="High",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ImageExecutor(
                api_key="key",
                assets_root=Path(tmpdir),
                timezone="Asia/Jerusalem",
                enabled=True,
                dry_run=False,
                client=client,
            ).execute(bad_task)

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error, "Brand validation failed.")
        self.assertEqual(client.calls, [])

    def test_success_stores_png_and_returns_proof(self) -> None:
        image_bytes = b"fake-png"
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ImageExecutor(
                api_key="key",
                assets_root=Path(tmpdir),
                timezone="Asia/Jerusalem",
                enabled=True,
                dry_run=False,
                client=FakeImageClient(image_bytes),
            ).execute(_task())
            image_path = Path(result.proof["image_path"])

            self.assertTrue(image_path.exists())
            self.assertEqual(image_path.read_bytes(), image_bytes)

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.proof["brand_validation"], "passed")
        self.assertIn("sha256", result.artifact_ids)

    def test_public_url_required_blocks_without_upload_provider(self) -> None:
        task = _task()
        task.payload["require_public_url"] = True
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ImageExecutor(
                api_key="key",
                assets_root=Path(tmpdir),
                timezone="Asia/Jerusalem",
                enabled=True,
                dry_run=False,
                client=FakeImageClient(b"fake-png"),
            ).execute(task)

        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.error, "Image task requires public asset upload before publishing.")

    def test_cloudinary_upload_returns_public_url_evidence(self) -> None:
        uploader = FakeUploader()
        image_bytes = b"fake-png"
        task = _task()
        task.payload["require_public_url"] = True
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ImageExecutor(
                api_key="key",
                assets_root=Path(tmpdir),
                timezone="Asia/Jerusalem",
                enabled=True,
                dry_run=False,
                upload_provider="cloudinary",
                cloudinary_cloud_name="cloud",
                cloudinary_api_key="api-key",
                cloudinary_api_secret="secret",
                client=FakeImageClient(image_bytes),
                uploader=uploader,
            ).execute(task)

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.proof["upload_provider"], "cloudinary")
        self.assertTrue(result.proof["public_url"].startswith("https://res.cloudinary.com/"))
        self.assertEqual(len(uploader.calls), 1)


if __name__ == "__main__":
    unittest.main()
