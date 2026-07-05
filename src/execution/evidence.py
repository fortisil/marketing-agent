from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.execution.connectors.base import ExecutionResult


REQUIRED_PROOF_BY_ACTION: dict[str, tuple[str, ...]] = {
    "generate_branded_social_image": (
        "image_path",
        "sha256",
        "public_url",
        "upload_provider",
        "brand_validation",
        "timestamp",
        "worker_id",
    ),
    "publish_social_post": (
        "buffer_update_id",
        "buffer_post_url",
        "publish_status",
        "timestamp",
        "caption_hash",
        "image_sha256",
        "public_url",
        "worker_id",
    ),
}


@dataclass(frozen=True)
class EvidenceValidation:
    valid: bool
    missing: list[str]
    invalid: list[str]

    @property
    def errors(self) -> list[str]:
        return [*self.missing, *self.invalid]


class EvidenceValidator:
    """Validate that completed work has auditable business proof."""

    def validate(self, result: ExecutionResult) -> EvidenceValidation:
        if result.status != "completed":
            return EvidenceValidation(valid=True, missing=[], invalid=[])

        required = REQUIRED_PROOF_BY_ACTION.get(result.action, ("timestamp", "worker_id"))
        missing = [key for key in required if not self._present(result.proof.get(key))]
        invalid = self._invalid_values(result.action, result.proof)
        return EvidenceValidation(valid=not missing and not invalid, missing=missing, invalid=invalid)

    def _present(self, value: Any) -> bool:
        return value is not None and str(value).strip() != ""

    def _invalid_values(self, action: str, proof: dict[str, Any]) -> list[str]:
        invalid: list[str] = []
        if action == "generate_branded_social_image":
            if proof.get("brand_validation") != "passed":
                invalid.append("brand_validation must be passed")
            image_path = proof.get("image_path")
            if self._present(image_path) and not Path(str(image_path)).exists():
                invalid.append("image_path must exist")
            url = str(proof.get("public_url") or "")
            if url and not url.startswith(("http://", "https://")):
                invalid.append("public_url must be an absolute URL")
        if action == "publish_social_post":
            url = str(proof.get("instagram_url") or "")
            if url and not url.startswith(("http://", "https://")):
                invalid.append("instagram_url must be an absolute URL")
            if url and "instagram.com" not in url:
                invalid.append("instagram_url must be an Instagram permalink")
            buffer_url = str(proof.get("buffer_post_url") or "")
            if buffer_url and not buffer_url.startswith(("http://", "https://")):
                invalid.append("buffer_post_url must be an absolute URL")
            public_url = str(proof.get("public_url") or "")
            if public_url and not public_url.startswith(("http://", "https://")):
                invalid.append("public_url must be an absolute URL")
            if proof.get("caption_hash") and len(str(proof["caption_hash"])) < 32:
                invalid.append("caption_hash must be a stable content hash")
            if proof.get("image_sha256") and len(str(proof["image_sha256"])) != 64:
                invalid.append("image_sha256 must be a SHA256 hex digest")
        return invalid
