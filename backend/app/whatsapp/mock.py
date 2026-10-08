from pathlib import Path
from typing import Any

from app.whatsapp.base import WhatsAppAdapter

_SENT: list[dict[str, Any]] = []
MEDIA_DIR = Path(__file__).resolve().parents[2] / "storage" / "inbound"


class MockWhatsAppAdapter(WhatsAppAdapter):
    """In-memory mock shared across requests in the same process."""

    def __init__(self) -> None:
        self.sent = _SENT

    def send_text(self, to: str, body: str) -> dict[str, Any]:
        payload = {"to": to, "type": "text", "body": body, "id": f"mock-{len(self.sent)+1}"}
        self.sent.append(payload)
        return payload

    def send_buttons(
        self, to: str, body: str, buttons: list[dict[str, str]]
    ) -> dict[str, Any]:
        payload = {
            "to": to,
            "type": "buttons",
            "body": body,
            "buttons": buttons,
            "id": f"mock-{len(self.sent)+1}",
        }
        self.sent.append(payload)
        return payload

    def send_cta_url(
        self, to: str, body: str, *, button_text: str, url: str
    ) -> dict[str, Any]:
        payload = {
            "to": to,
            "type": "cta_url",
            "body": body,
            "button_text": button_text,
            "url": url,
            "id": f"mock-{len(self.sent)+1}",
        }
        self.sent.append(payload)
        return payload

    def send_document(
        self,
        to: str,
        *,
        document_path: str,
        filename: str,
        caption: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "to": to,
            "type": "document",
            "document_path": document_path,
            "filename": filename,
            "caption": caption,
            "id": f"mock-{len(self.sent)+1}",
        }
        self.sent.append(payload)
        return payload

    def download_media(self, media_id: str, *, suffix: str = ".bin") -> str:
        MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        path = MEDIA_DIR / f"{media_id}{suffix}"
        if not path.exists():
            path.write_bytes(b"mock-media")
        return str(path)
