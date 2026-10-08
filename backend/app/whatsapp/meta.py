from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

from app.core.config import get_settings
from app.whatsapp.base import WhatsAppAdapter

INBOUND_DIR = Path(__file__).resolve().parents[2] / "storage" / "inbound"


class MetaWhatsAppAdapter(WhatsAppAdapter):
    """Meta WhatsApp Business Cloud API adapter."""

    def __init__(self) -> None:
        settings = get_settings()
        self.access_token = settings.whatsapp_access_token
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.graph_root = "https://graph.facebook.com/v21.0"
        self.graph_base = f"{self.graph_root}/{self.phone_number_id}"
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
            "text": {"body": body, "preview_url": True},
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

    def send_cta_url(
        self, to: str, body: str, *, button_text: str, url: str
    ) -> dict[str, Any]:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "cta_url",
                "body": {"text": body[:1024]},
                "action": {
                    "name": "cta_url",
                    "parameters": {
                        "display_text": button_text[:20],
                        "url": url,
                    },
                },
            },
        }
        with httpx.Client(timeout=30) as client:
            response = client.post(self.base_url, headers=self._headers(), json=payload)
            response.raise_for_status()
            return response.json()

    def _upload_media(self, path: str, mime_type: str = "application/pdf") -> str:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Media file missing: {path}")
        upload_url = f"{self.graph_base}/media"
        with httpx.Client(timeout=60) as client:
            with open(file_path, "rb") as handle:
                response = client.post(
                    upload_url,
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    data={"messaging_product": "whatsapp", "type": mime_type},
                    files={"file": (file_path.name, handle, mime_type)},
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
        media_id = self._upload_media(document_path, mime_type="application/pdf")
        document: dict[str, Any] = {"id": media_id, "filename": filename}
        if caption:
            document["caption"] = caption[:1024]
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

    def download_media(self, media_id: str, *, suffix: str = ".bin") -> str:
        INBOUND_DIR.mkdir(parents=True, exist_ok=True)
        with httpx.Client(timeout=60, follow_redirects=True) as client:
            meta = client.get(
                f"{self.graph_root}/{media_id}",
                headers={"Authorization": f"Bearer {self.access_token}"},
            )
            meta.raise_for_status()
            url = meta.json().get("url")
            if not url:
                raise RuntimeError(f"No download URL for media {media_id}")
            content = client.get(
                url, headers={"Authorization": f"Bearer {self.access_token}"}
            )
            content.raise_for_status()
            path = INBOUND_DIR / f"{media_id}-{uuid4().hex[:8]}{suffix}"
            path.write_bytes(content.content)
            return str(path)
