from __future__ import annotations

import base64
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Protocol
from urllib import request

from src.execution.asset_upload import AssetUploader, CloudinaryUploader
from src.execution.connectors.base import ExecutionResult, ExecutionTask


class ImageClient(Protocol):
    def generate(self, *, model: str, prompt: str, size: str) -> dict[str, Any]:
        """Generate an image and return provider response data."""


class OpenAIImageClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def generate(self, *, model: str, prompt: str, size: str) -> dict[str, Any]:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)
        response = client.images.generate(model=model, prompt=prompt, size=size)
        if hasattr(response, "model_dump"):
            return response.model_dump()
        return json.loads(response.model_dump_json())


class BrandValidator:
    def validate(self, *, prompt: str, brand_assets: dict[str, Any]) -> tuple[bool, list[str]]:
        failures: list[str] = []
        if "ChatBot2U" not in prompt:
            failures.append("Image prompt must include ChatBot2U.")
        if not brand_assets.get("colors"):
            failures.append("Brand colors are required.")
        if not brand_assets.get("logo"):
            failures.append("Approved logo reference is required.")
        forbidden = ["stock photo", "generic startup", "random logo"]
        lowered = prompt.lower()
        for phrase in forbidden:
            if phrase in lowered:
                failures.append(f"Forbidden brand phrase: {phrase}.")
        forbidden_text_requests = [
            "hebrew whatsapp demo cta",
            "hebrew cta",
            "text overlay",
            "render text",
            "include text",
            "write text",
            "words on image",
            "letters",
            "subtitles",
            "caption in image",
        ]
        for phrase in forbidden_text_requests:
            if f"no {phrase}" in lowered:
                continue
            if phrase in lowered:
                failures.append(f"Forbidden generated text request: {phrase}.")
        if "no text" not in lowered or "no letters" not in lowered:
            failures.append("Image prompt must forbid model-rendered text and letters.")
        return not failures, failures


class ImageExecutor:
    name = "ImageExecutor"

    def __init__(
        self,
        *,
        api_key: str,
        assets_root: Path,
        timezone: str,
        enabled: bool = False,
        dry_run: bool = True,
        model: str = "gpt-image-1",
        size: str = "1024x1024",
        upload_provider: str = "",
        cloudinary_cloud_name: str = "",
        cloudinary_api_key: str = "",
        cloudinary_api_secret: str = "",
        client: ImageClient | None = None,
        validator: BrandValidator | None = None,
        uploader: AssetUploader | None = None,
    ) -> None:
        self.api_key = api_key
        self.assets_root = assets_root
        self.timezone = timezone
        self.enabled = enabled
        self.dry_run = dry_run
        self.model = model
        self.size = size
        self.upload_provider = upload_provider.strip().lower()
        self.cloudinary_cloud_name = cloudinary_cloud_name
        self.cloudinary_api_key = cloudinary_api_key
        self.cloudinary_api_secret = cloudinary_api_secret
        self.client = client
        self.validator = validator or BrandValidator()
        self.uploader = uploader

    def execute(self, task: ExecutionTask) -> ExecutionResult:
        if task.connector != self.name:
            return ExecutionResult.failed(
                task,
                timezone=self.timezone,
                error=f"{self.name} cannot execute connector {task.connector}.",
                next_retry=None,
            )

        prompt = str(task.payload.get("prompt") or "").strip()
        if not prompt:
            return ExecutionResult.failed(
                task,
                timezone=self.timezone,
                error="Image task payload is missing prompt.",
                next_retry=None,
            )

        valid, failures = self.validator.validate(
            prompt=prompt,
            brand_assets=task.payload.get("brand_assets", {}),
        )
        if not valid:
            return ExecutionResult.failed(
                task,
                timezone=self.timezone,
                error="Brand validation failed.",
                next_retry=None,
                result={"brand_validation_errors": failures},
            )

        if not self.enabled:
            return ExecutionResult.blocked(
                task,
                timezone=self.timezone,
                error="Image generation is disabled for this runtime.",
                next_retry="enable IMAGE_GENERATION_ENABLED with OpenAI image credentials",
                result={"required_connector": "ImageExecutor"},
            )

        if not self.api_key:
            return ExecutionResult.blocked(
                task,
                timezone=self.timezone,
                error="OpenAI image API key is not configured.",
                next_retry="tomorrow 08:00 Asia/Jerusalem",
                result={"required_secrets": ["OPENAI_API_KEY"]},
            )

        if self.dry_run or task.dry_run:
            return ExecutionResult.blocked(
                task,
                timezone=self.timezone,
                error="Execution dry-run is enabled; image was not generated.",
                next_retry="next non-dry-run execution window",
                result={"dry_run": True, "model": self.model, "size": self.size},
            )

        if task.payload.get("require_public_url") and not self.upload_provider:
            return ExecutionResult.blocked(
                task,
                timezone=self.timezone,
                error="Image task requires public asset upload before publishing.",
                next_retry="configure ASSET_UPLOAD_PROVIDER=cloudinary",
                result={"required_provider": "cloudinary"},
            )
        if self.upload_provider == "cloudinary" and not (
            self.cloudinary_cloud_name and self.cloudinary_api_key and self.cloudinary_api_secret
        ):
            return ExecutionResult.blocked(
                task,
                timezone=self.timezone,
                error="Cloudinary upload credentials are not configured.",
                next_retry="tomorrow 08:00 Asia/Jerusalem",
                result={
                    "required_secrets": [
                        "CLOUDINARY_CLOUD_NAME",
                        "CLOUDINARY_API_KEY",
                        "CLOUDINARY_API_SECRET",
                    ]
                },
            )
        if self.upload_provider and self.upload_provider != "cloudinary":
            return ExecutionResult.failed(
                task,
                timezone=self.timezone,
                error=f"Unsupported asset upload provider: {self.upload_provider}.",
                next_retry=None,
            )

        try:
            response = (self.client or OpenAIImageClient(self.api_key)).generate(
                model=self.model,
                prompt=prompt,
                size=str(task.payload.get("size") or self.size),
            )
            image_bytes = self._extract_image_bytes(response)
        except Exception as exc:
            return ExecutionResult.failed(
                task,
                timezone=self.timezone,
                error=f"Image generation failed: {exc}",
                next_retry="tomorrow 08:00 Asia/Jerusalem",
            )

        run_date = str(task.payload.get("run_date") or "undated")
        output_dir = self.assets_root / "social" / run_date
        output_dir.mkdir(parents=True, exist_ok=True)
        digest = sha256(image_bytes).hexdigest()[:16]
        image_path = output_dir / f"{task.id}-{digest}.png"
        image_path.write_bytes(image_bytes)
        public_url = ""
        upload_provider = ""
        upload_asset_id = ""
        upload_result: dict[str, Any] = {}
        if self.upload_provider == "cloudinary":
            try:
                upload = (self.uploader or CloudinaryUploader(
                    cloud_name=self.cloudinary_cloud_name,
                    api_key=self.cloudinary_api_key,
                    api_secret=self.cloudinary_api_secret,
                )).upload(
                    image_path=image_path,
                    public_id=f"{task.id}-{digest}",
                    folder=f"chatbot2u/social/{run_date}",
                )
            except Exception as exc:
                return ExecutionResult.failed(
                    task,
                    timezone=self.timezone,
                    error=f"Asset upload failed: {exc}",
                    next_retry="tomorrow 08:00 Asia/Jerusalem",
                )
            public_url = upload.public_url
            upload_provider = upload.provider
            upload_asset_id = upload.provider_asset_id
            upload_result = upload.result

        proof = {
            "image_path": str(image_path),
            "sha256": sha256(image_bytes).hexdigest(),
            "public_url": public_url,
            "upload_provider": upload_provider,
            "upload_asset_id": upload_asset_id,
            "brand_validation": "passed",
            "provider": "openai",
            "model": self.model,
            "size": str(task.payload.get("size") or self.size),
            "text_policy": str(task.payload.get("text_policy") or "no_model_rendered_text"),
            "language_policy": str(task.payload.get("language_policy") or ""),
        }
        return ExecutionResult.completed(
            task,
            timezone=self.timezone,
            artifact_ids={
                "image_path": str(image_path),
                "sha256": proof["sha256"],
                "public_url": public_url,
                "upload_asset_id": upload_asset_id,
            },
            proof=proof,
            result={"brand_validation": "passed", "asset_upload": upload_result},
        )

    def _extract_image_bytes(self, response: dict[str, Any]) -> bytes:
        data = response.get("data")
        if not isinstance(data, list) or not data:
            raise ValueError("Image response did not include data.")
        first = data[0]
        if not isinstance(first, dict):
            raise ValueError("Image response data was not an object.")
        b64_json = first.get("b64_json")
        if b64_json:
            return base64.b64decode(str(b64_json))
        url = first.get("url")
        if url:
            with request.urlopen(str(url), timeout=60) as response_handle:
                return response_handle.read()
        raise ValueError("Image response did not include b64_json or url.")
