"""Keyboard orchestration layer for inputctl."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import time
from typing import Protocol, Sequence

from inputctl.keymap import KeySpec, resolve_key, resolve_text_char


class KeyboardBackend(Protocol):
    """Minimal backend contract required by KeyboardController."""

    def key_down(self, vk_code: int, flags: int = 0) -> None:
        """Send a key-down event."""

    def key_up(self, vk_code: int, flags: int = 0) -> None:
        """Send a key-up event."""

    def press_key(self, vk_code: int, flags: int = 0, press_delay_ms: int = 0) -> None:
        """Send a full key press."""


@dataclass(slots=True)
class KeyboardController:
    """High-level keyboard actions built on top of an injection backend."""

    backend: KeyboardBackend
    key_delay_ms: int = 20
    press_delay_ms: int = 20
    logger: logging.Logger | None = None

    def __post_init__(self) -> None:
        self.logger = self.logger or logging.getLogger(__name__)

    def press(self, key_name: str) -> None:
        """Press and release a single key."""
        spec = resolve_key(key_name)
        self.logger.debug("Pressing key %s (vk=0x%02X)", spec.name, spec.vk_code)
        self.backend.press_key(spec.vk_code, flags=spec.input_flags, press_delay_ms=self.press_delay_ms)

    def down(self, key_name: str) -> None:
        """Hold a key down."""
        spec = resolve_key(key_name)
        self.logger.debug("Key down %s (vk=0x%02X)", spec.name, spec.vk_code)
        self.backend.key_down(spec.vk_code, flags=spec.input_flags)

    def up(self, key_name: str) -> None:
        """Release a key."""
        spec = resolve_key(key_name)
        self.logger.debug("Key up %s (vk=0x%02X)", spec.name, spec.vk_code)
        self.backend.key_up(spec.vk_code, flags=spec.input_flags)

    def combo(self, keys: Sequence[str]) -> None:
        """Press keys in order and release them in reverse order."""
        if not keys:
            raise ValueError("At least one key is required for a combo.")

        specs = [resolve_key(key_name) for key_name in keys]
        held: list[KeySpec] = []
        operation_error: Exception | None = None

        self.logger.debug("Running combo: %s", " + ".join(spec.name for spec in specs))
        try:
            for index, spec in enumerate(specs):
                self.backend.key_down(spec.vk_code, flags=spec.input_flags)
                held.append(spec)
                if index != len(specs) - 1:
                    self._sleep_key_delay()
        except Exception as exc:  # pragma: no cover - defensive path
            operation_error = exc

        release_error = self._release_reverse(held)

        if operation_error is not None:
            if release_error is not None:
                operation_error.add_note(f"Cleanup during combo release also failed: {release_error}")
            raise operation_error
        if release_error is not None:
            raise release_error

    def type_text(self, text: str) -> None:
        """Type ASCII text using the current key registry."""
        normalized_text = text.replace("\r\n", "\n")
        for index, char in enumerate(normalized_text):
            key_names = resolve_text_char(char)
            self.logger.debug("Typing character %r as %s", char, " + ".join(key_names))
            if len(key_names) == 1:
                self.press(key_names[0])
            else:
                self.combo(key_names)
            if index != len(normalized_text) - 1:
                self._sleep_key_delay()

    def _release_reverse(self, held: Sequence[KeySpec]) -> Exception | None:
        first_error: Exception | None = None
        for index, spec in enumerate(reversed(held)):
            try:
                self.backend.key_up(spec.vk_code, flags=spec.input_flags)
            except Exception as exc:  # pragma: no cover - defensive path
                if first_error is None:
                    first_error = exc
            if index != len(held) - 1:
                self._sleep_key_delay()
        return first_error

    def _sleep_key_delay(self) -> None:
        if self.key_delay_ms > 0:
            time.sleep(self.key_delay_ms / 1000)

