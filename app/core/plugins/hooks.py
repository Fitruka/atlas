"""Plugin hook/event sistemi.

Async pub/sub mekanizmasi ile plugin'lerin sistem olaylarina
abone olmasini ve tepki vermesini saglar. Her handler hata
izolasyonu ile calisir — bir handler'in hatasi digerlerini etkilemez.
"""

import logging
from collections import defaultdict
from typing import Any, Callable, Coroutine

from app.models.plugin import HookEvent

logger = logging.getLogger(__name__)

# Hook handler tipi: async callable, keyword arguman alir
HookHandler = Callable[..., Coroutine[Any, Any, None]]


class HookManager:
    """Plugin hook yoneticisi.

    Olaylara handler kaydeder, olay tetiklendiginde tum
    kayitli handler'lari oncelik sirasina gore calistirir.

    Attributes:
        _handlers: Olay -> (oncelik, plugin_adi, handler) listesi.
    """

    def __init__(self) -> None:
        """HookManager'i baslatir."""
        self._handlers: dict[HookEvent, list[tuple[int, str, HookHandler]]] = (
            defaultdict(list)
        )
        logger.info("HookManager olusturuldu")

    def register(
        self,
        event: HookEvent,
        plugin_name: str,
        handler: HookHandler,
        priority: int = 100,
    ) -> None:
        """Hook handler kaydeder.

        Args:
            event: Dinlenecek olay.
            plugin_name: Handler'in ait oldugu plugin adi.
            handler: Async handler fonksiyonu.
            priority: Oncelik (dusuk sayi = once calisir).
        """
        self._handlers[event].append((priority, plugin_name, handler))
        self._handlers[event].sort(key=lambda x: x[0])
        logger.debug(
            "Hook kaydedildi: %s -> %s (oncelik=%d)",
            event.value,
            plugin_name,
            priority,
        )

    def unregister_plugin(self, plugin_name: str) -> int:
        """Bir plugin'e ait tum handler'lari kaldirir.

        Args:
            plugin_name: Kaldirilacak plugin adi.

        Returns:
            Kaldirilan handler sayisi.
        """
        removed = 0
        for event in list(self._handlers.keys()):
            before = len(self._handlers[event])
            self._handlers[event] = [
                (p, name, h)
                for p, name, h in self._handlers[event]
                if name != plugin_name
            ]
            removed += before - len(self._handlers[event])
            if not self._handlers[event]:
                del self._handlers[event]

        if removed:
            logger.debug(
                "%s plugin'inden %d hook kaldirildi", plugin_name, removed
            )
        return removed

    async def emit(self, event: HookEvent, **kwargs: Any) -> list[str]:
        """Olayi tum kayitli handler'lara gonderir.

        Her handler bagimsiz try-except ile korunur.
        Bir handler'in hatasi diger handler'lari engellemez.

        Args:
            event: Tetiklenen olay.
            **kwargs: Handler'lara gonderilecek veriler.

        Returns:
            Hata veren plugin adlarinin listesi.
        """
        handlers = self._handlers.get(event, [])
        if not handlers:
            return []

        errors: list[str] = []
        for _priority, plugin_name, handler in handlers:
            try:
                await handler(**kwargs)
            except Exception as exc:
                errors.append(plugin_name)
                logger.error(
                    "Hook hatasi [%s -> %s]: %s",
                    event.value,
                    plugin_name,
                    exc,
                )

        return errors

    def get_handlers(self, event: HookEvent) -> list[tuple[int, str, HookHandler]]:
        """Belirli bir olay icin kayitli handler'lari dondurur.

        Args:
            event: Sorgulanacak olay.

        Returns:
            (oncelik, plugin_adi, handler) listesi.
        """
        return list(self._handlers.get(event, []))

    def get_plugin_hooks(self, plugin_name: str) -> dict[HookEvent, int]:
        """Bir plugin'in kayitli hook'larini dondurur.

        Args:
            plugin_name: Plugin adi.

        Returns:
            {olay: handler_sayisi} sozlugu.
        """
        result: dict[HookEvent, int] = {}
        for event, handlers in self._handlers.items():
            count = sum(1 for _, name, _ in handlers if name == plugin_name)
            if count:
                result[event] = count
        return result

    @property
    def total_handlers(self) -> int:
        """Toplam kayitli handler sayisi."""
        return sum(len(h) for h in self._handlers.values())

    async def emit_transform(
        self,
        event: HookEvent,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Olayi donusturucu olarak yayar.

        Handler'lar payload'u degistirip dondurebilir.
        Sirasıyla uygulanir (pipeline).

        Args:
            event: Tetiklenen olay.
            payload: Donusturulecek veri.

        Returns:
            Donusturulmus payload.
        """
        handlers = self._handlers.get(event, [])
        if not handlers:
            return payload

        current = dict(payload)
        for _priority, plugin_name, handler in handlers:
            try:
                result = await handler(**current)
                if isinstance(result, dict):
                    current = result
            except Exception as exc:
                logger.error(
                    "Transform hook hatasi [%s -> %s]: %s",
                    event.value,
                    plugin_name,
                    exc,
                )

        return current

    async def emit_llm_input(
        self,
        messages: list[dict[str, Any]],
        model: str = "",
        provider: str = "",
    ) -> list[dict[str, Any]]:
        """LLM girdi hook'unu yayar.

        Args:
            messages: LLM mesajlari.
            model: Model adi.
            provider: Saglayici adi.

        Returns:
            Donusturulmus mesajlar.
        """
        result = await self.emit_transform(
            HookEvent.LLM_INPUT,
            {
                "messages": messages,
                "model": model,
                "provider": provider,
            },
        )
        return result.get("messages", messages)

    async def emit_llm_output(
        self,
        content: str,
        model: str = "",
        provider: str = "",
        usage: dict[str, int] | None = None,
    ) -> str:
        """LLM cikti hook'unu yayar.

        Args:
            content: LLM yaniti.
            model: Model adi.
            provider: Saglayici adi.
            usage: Token kullanimi.

        Returns:
            Donusturulmus yant.
        """
        result = await self.emit_transform(
            HookEvent.LLM_OUTPUT,
            {
                "content": content,
                "model": model,
                "provider": provider,
                "usage": usage or {},
            },
        )
        return result.get("content", content)

    def clear(self) -> None:
        """Tum handler'lari temizler."""
        self._handlers.clear()
        logger.debug("Tum hook handler'lari temizlendi")
