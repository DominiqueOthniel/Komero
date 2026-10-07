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
