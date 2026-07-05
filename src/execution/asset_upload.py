from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
import json
from pathlib import Path
import time
from typing import Any, Protocol
from urllib import request


@dataclass(frozen=True)
class UploadedAsset:
    provider: str
    public_url: str
    provider_asset_id: str
    result: dict[str, Any]


class AssetUploader(Protocol):
    provider: str

    def upload(self, *, image_path: Path, public_id: str, folder: str) -> UploadedAsset:
        """Upload a generated asset and return a public URL."""


class CloudinaryUploader:
    provider = "cloudinary"

    def __init__(
        self,
        *,
        cloud_name: str,
        api_key: str,
        api_secret: str,
        timeout: int = 60,
    ) -> None:
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout = timeout

    def upload(self, *, image_path: Path, public_id: str, folder: str) -> UploadedAsset:
        if not self.cloud_name or not self.api_key or not self.api_secret:
            raise ValueError("Cloudinary credentials are not configured.")
        timestamp = str(int(time.time()))
        params = {
            "folder": folder,
            "public_id": public_id,
            "timestamp": timestamp,
        }
        signature = self._signature(params)
        fields = {
            **params,
            "api_key": self.api_key,
            "signature": signature,
        }
        data, content_type = self._multipart(fields=fields, file_path=image_path)
        req = request.Request(
            url=f"https://api.cloudinary.com/v1_1/{self.cloud_name}/image/upload",
            data=data,
            headers={"Content-Type": content_type},
            method="POST",
        )
        with request.urlopen(req, timeout=self.timeout) as response:
            decoded = json.loads(response.read().decode("utf-8") or "{}")
        secure_url = str(decoded.get("secure_url") or "")
        provider_asset_id = str(decoded.get("public_id") or public_id)
        if not secure_url:
            raise ValueError("Cloudinary upload did not return secure_url.")
        return UploadedAsset(
            provider=self.provider,
            public_url=secure_url,
            provider_asset_id=provider_asset_id,
            result=decoded,
        )

    def _signature(self, params: dict[str, str]) -> str:
        payload = "&".join(f"{key}={params[key]}" for key in sorted(params))
        return sha1(f"{payload}{self.api_secret}".encode("utf-8")).hexdigest()

    def _multipart(self, *, fields: dict[str, str], file_path: Path) -> tuple[bytes, str]:
        boundary = f"----ai-cmo-cloudinary-{int(time.time() * 1000)}"
        chunks: list[bytes] = []
        for key, value in fields.items():
            chunks.extend(
                [
                    f"--{boundary}\r\n".encode("utf-8"),
                    f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"),
                    str(value).encode("utf-8"),
                    b"\r\n",
                ]
            )
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                (
                    'Content-Disposition: form-data; name="file"; '
                    f'filename="{file_path.name}"\r\n'
                ).encode("utf-8"),
                b"Content-Type: image/png\r\n\r\n",
                file_path.read_bytes(),
                b"\r\n",
                f"--{boundary}--\r\n".encode("utf-8"),
            ]
        )
        return b"".join(chunks), f"multipart/form-data; boundary={boundary}"
