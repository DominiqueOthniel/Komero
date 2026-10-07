from typing import Any

from app.whatsapp.base import WhatsAppAdapter


class MockWhatsAppAdapter(WhatsAppAdapter):
    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []

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
