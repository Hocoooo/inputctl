"""Tests for high-level keyboard orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from inputctl.keyboard import KeyboardController
from inputctl.keymap import UnknownKeyError, UnsupportedCharacterError
from inputctl.win32_sendinput import VK_A, VK_B, VK_ESCAPE, VK_SHIFT


@dataclass
class FakeBackend:
    """Fake backend used for controller tests."""

    events: list[tuple[str, int, int, int]] = field(default_factory=list)

    def key_down(self, vk_code: int, flags: int = 0) -> None:
        self.events.append(("down", vk_code, flags, 0))

    def key_up(self, vk_code: int, flags: int = 0) -> None:
        self.events.append(("up", vk_code, flags, 0))

    def press_key(self, vk_code: int, flags: int = 0, press_delay_ms: int = 0) -> None:
        self.events.append(("press", vk_code, flags, press_delay_ms))


def test_press_calls_backend_press_once() -> None:
    backend = FakeBackend()
    controller = KeyboardController(backend=backend, key_delay_ms=0, press_delay_ms=7)

    controller.press("a")

    assert backend.events == [("press", VK_A, 0, 7)]


def test_combo_presses_in_order_and_releases_in_reverse() -> None:
    backend = FakeBackend()
    controller = KeyboardController(backend=backend, key_delay_ms=0, press_delay_ms=0)

    controller.combo(["shift", "escape"])

    assert backend.events == [
        ("down", VK_SHIFT, 0, 0),
        ("down", VK_ESCAPE, 0, 0),
        ("up", VK_ESCAPE, 0, 0),
        ("up", VK_SHIFT, 0, 0),
    ]


def test_combo_validates_all_keys_before_sending_events() -> None:
    backend = FakeBackend()
    controller = KeyboardController(backend=backend, key_delay_ms=0, press_delay_ms=0)

    with pytest.raises(UnknownKeyError):
        controller.combo(["shift", "not-a-real-key"])

    assert backend.events == []


def test_type_text_maps_ascii_with_shift_sequences() -> None:
    backend = FakeBackend()
    controller = KeyboardController(backend=backend, key_delay_ms=0, press_delay_ms=0)

    controller.type_text("Ab")

    assert backend.events == [
        ("down", VK_SHIFT, 0, 0),
        ("down", VK_A, 0, 0),
        ("up", VK_A, 0, 0),
        ("up", VK_SHIFT, 0, 0),
        ("press", VK_B, 0, 0),
    ]


def test_type_text_rejects_non_ascii() -> None:
    backend = FakeBackend()
    controller = KeyboardController(backend=backend, key_delay_ms=0, press_delay_ms=0)

    with pytest.raises(UnsupportedCharacterError):
        controller.type_text("é")

