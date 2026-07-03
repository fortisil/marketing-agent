from __future__ import annotations

from base64 import urlsafe_b64encode
from email.message import EmailMessage
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from src.config import Settings


GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"


def _load_credentials(credentials_file: Path, token_file: Path) -> Credentials:
    creds = None

    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), [GMAIL_SEND_SCOPE])

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        if not credentials_file.exists():
            raise FileNotFoundError(
                f"Gmail credentials file not found: {credentials_file}. "
                "Create OAuth credentials and set GMAIL_CREDENTIALS_FILE."
            )

        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), [GMAIL_SEND_SCOPE])
        creds = flow.run_local_server(port=0)
        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(creds.to_json(), encoding="utf-8")

    return creds


def send_email(settings: Settings, to_email: str, subject: str, body: str) -> dict:
    if not settings.gmail_sender:
        raise RuntimeError("GMAIL_SENDER is required to send email.")

    creds = _load_credentials(settings.gmail_credentials_file, settings.gmail_token_file)
    service = build("gmail", "v1", credentials=creds)

    message = EmailMessage()
    message["To"] = to_email
    message["From"] = settings.gmail_sender
    message["Subject"] = subject
    message.set_content(body, subtype="plain", charset="utf-8")

    encoded = urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return service.users().messages().send(userId="me", body={"raw": encoded}).execute()
