from __future__ import annotations

from datetime import datetime
import json
import logging
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


logger = logging.getLogger(__name__)
RESEND_EMAILS_URL = "https://api.resend.com/emails"


def send_email_resend(
    *,
    api_key: str,
    from_email: str,
    to_email: str,
    subject: str,
    body_markdown: str,
    timezone: str = "Asia/Jerusalem",
    urlopen_func: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    if not api_key:
        raise ValueError("RESEND_API_KEY is required.")
    if not from_email:
        raise ValueError("EMAIL_FROM is required.")
    if not to_email:
        raise ValueError("EMAIL_TO is required.")

    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "text": _plain_text_fallback(body_markdown),
    }
    request = Request(
        RESEND_EMAILS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ai-executive-os/1.0.0",
        },
        method="POST",
    )

    timestamp = datetime.now(ZoneInfo(timezone)).isoformat()
    try:
        with urlopen_func(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw) if raw else {}
        message_id = str(data.get("id", ""))
        logger.info(
            "resend_delivery_sent",
            extra={"_recipient": to_email, "_message_id": message_id},
        )
        return {
            "channel": "resend",
            "status": "sent",
            "recipient": to_email,
            "timestamp": timestamp,
            "message_id": message_id,
        }
    except HTTPError as exc:
        reason = _safe_error_reason(exc)
    except URLError as exc:
        reason = str(exc.reason)
    except Exception as exc:  # noqa: BLE001 - delivery failure must be reported, not crash memory saving.
        reason = exc.__class__.__name__

    logger.warning("resend_delivery_failed", extra={"_recipient": to_email, "_reason": reason})
    return {
        "channel": "resend",
        "status": "failed",
        "recipient": to_email,
        "timestamp": timestamp,
        "reason": reason,
    }


def _plain_text_fallback(body_markdown: str) -> str:
    return body_markdown.strip() + "\n"


def _safe_error_reason(exc: HTTPError) -> str:
    try:
        raw = exc.read().decode("utf-8")
    except Exception:  # noqa: BLE001
        raw = ""
    if not raw:
        return f"HTTP {exc.code}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return _trim_reason(f"HTTP {exc.code}: {raw}")

    error = data.get("error")
    if isinstance(error, dict):
        message = error.get("message") or error.get("name") or error.get("code")
    else:
        message = error

    message = (
        message
        or data.get("message")
        or data.get("name")
        or data.get("code")
        or data.get("statusCode")
        or f"HTTP {exc.code}"
    )
    return _trim_reason(f"HTTP {exc.code}: {message}")


def _trim_reason(reason: str) -> str:
    compact = " ".join(reason.split())
    if len(compact) <= 300:
        return compact
    return compact[:297] + "..."
