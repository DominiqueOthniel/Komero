from typing import Any

from app.whatsapp.base import WhatsAppAdapter

_SENT: list[dict[str, Any]] = []


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
