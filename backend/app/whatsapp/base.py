from abc import ABC, abstractmethod
from typing import Any


class WhatsAppAdapter(ABC):
    @abstractmethod
    def send_text(self, to: str, body: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def send_buttons(
        self, to: str, body: str, buttons: list[dict[str, str]]
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def send_document(
        self,
        to: str,
        *,
        document_path: str,
        filename: str,
        caption: str | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def send_cta_url(
        self, to: str, body: str, *, button_text: str, url: str
    ) -> dict[str, Any]:
        """Optional CTA link button. Defaults to plain text with URL."""
        return self.send_text(to, f"{body}\n{url}")

    def download_media(self, media_id: str, *, suffix: str = ".bin") -> str:
        """Download inbound media to local storage. Returns absolute file path."""
        raise NotImplementedError("Media download not supported by this adapter")
