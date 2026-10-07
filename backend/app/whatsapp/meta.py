from pathlib import Path
from typing import Any

import httpx

from app.core.config import get_settings
from app.whatsapp.base import WhatsAppAdapter


class MetaWhatsAppAdapter(WhatsAppAdapter):
    """Meta WhatsApp Business Cloud API adapter."""

    def __init__(self) -> None:
        settings = get_settings()
        self.access_token = settings.whatsapp_access_token
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.graph_base = f"https://graph.facebook.com/v21.0/{self.phone_number_id}"
        self.base_url = f"{self.graph_base}/messages"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def send_text(self, to: str, body: str) -> dict[str, Any]:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body},
        }
        with httpx.Client(timeout=30) as client:
            response = client.post(self.base_url, headers=self._headers(), json=payload)
            response.raise_for_status()
            return response.json()

    def send_buttons(
        self, to: str, body: str, buttons: list[dict[str, str]]
    ) -> dict[str, Any]:
        interactive_buttons = [
            {
                "type": "reply",
                "reply": {"id": button["id"], "title": button["title"][:20]},
            }
            for button in buttons[:3]
        ]
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body},
                "action": {"buttons": interactive_buttons},
            },
        }
        with httpx.Client(timeout=30) as client:
            response = client.post(self.base_url, headers=self._headers(), json=payload)
            response.raise_for_status()
            return response.json()

    def _upload_media(self, path: str, mime_type: str = "application/pdf") -> str:
        upload_url = f"{self.graph_base}/media"
        with httpx.Client(timeout=60) as client:
            with open(path, "rb") as handle:
                response = client.post(
                    upload_url,
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    data={"messaging_product": "whatsapp", "type": mime_type},
                    files={"file": (Path(path).name, handle, mime_type)},
                )
            response.raise_for_status()
            return str(response.json()["id"])

    def send_document(
        self,
        to: str,
        *,
        document_path: str,
        filename: str,
        caption: str | None = None,
    ) -> dict[str, Any]:
        media_id = self._upload_media(document_path)
        document: dict[str, Any] = {"id": media_id, "filename": filename}
        if caption:
            document["caption"] = caption
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "document",
            "document": document,
        }
        with httpx.Client(timeout=30) as client:
            response = client.post(self.base_url, headers=self._headers(), json=payload)
            response.raise_for_status()
            return response.json()
