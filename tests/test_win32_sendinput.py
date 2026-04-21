"""Regression tests for the Win32 SendInput backend definitions."""

from __future__ import annotations

import ctypes

from inputctl.win32_sendinput import (
    HARDWAREINPUT,
    INPUT,
    INPUT_KEYBOARD,
    KEYBDINPUT,
    KEYEVENTF_EXTENDEDKEY,
    KEYEVENTF_KEYUP,
    KEYEVENTF_UNICODE,
    MOUSEINPUT,
    SendInputBackend,
    VK_A,
)


def test_input_union_matches_win32_layout_size() -> None:
    """INPUT must match the Win32 layout size expected by SendInput."""
    expected_size = 40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28
    assert ctypes.sizeof(INPUT) == expected_size


def test_input_union_is_sized_by_largest_member() -> None:
    """The INPUT union must include mouse and hardware members, not just keyboard."""
    assert ctypes.sizeof(MOUSEINPUT) >= ctypes.sizeof(KEYBDINPUT)
    assert ctypes.sizeof(INPUT) >= ctypes.sizeof(MOUSEINPUT) + ctypes.sizeof(ctypes.c_ulong)
    assert ctypes.sizeof(INPUT) >= ctypes.sizeof(HARDWAREINPUT) + ctypes.sizeof(ctypes.c_ulong)


def test_send_uses_ctypes_sizeof_input_for_cbsize() -> None:
    """SendInput must receive the ABI-correct INPUT size."""
    backend = object.__new__(SendInputBackend)
    seen: dict[str, int] = {}

    def fake_send_input(n_inputs: int, input_ptr: ctypes.Array[INPUT], cb_size: int) -> int:
        seen["n_inputs"] = n_inputs
        seen["cb_size"] = cb_size
        return n_inputs

    backend._send_input = fake_send_input
    backend._send((SendInputBackend._keyboard_input(VK_A),))

    assert seen == {"n_inputs": 1, "cb_size": ctypes.sizeof(INPUT)}


def test_key_up_sets_keyup_flag_and_preserves_other_flags(monkeypatch) -> None:
    """key_up should keep existing flags and add KEYEVENTF_KEYUP."""
    backend = object.__new__(SendInputBackend)
    captured: dict[str, INPUT] = {}

    def fake_send(inputs: tuple[INPUT, ...]) -> None:
        captured["event"] = inputs[0]

    monkeypatch.setattr(backend, "_send", fake_send)
    backend.key_up(VK_A, flags=KEYEVENTF_EXTENDEDKEY)

    event = captured["event"]
    assert event.type == INPUT_KEYBOARD
    assert event.ki.wVk == VK_A
    assert event.ki.wScan == 0
    assert event.ki.dwFlags == (KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP)
    assert event.ki.time == 0
    assert event.ki.dwExtraInfo == 0


def test_type_unicode_char_builds_unicode_down_and_up_events() -> None:
    """Unicode typing should produce a valid down/up keyboard pair."""
    backend = object.__new__(SendInputBackend)
    captured: dict[str, list[INPUT]] = {}

    def fake_send_input(n_inputs: int, input_ptr: ctypes.Array[INPUT], cb_size: int) -> int:
        captured["events"] = [input_ptr[index] for index in range(n_inputs)]
        captured["cb_size"] = cb_size
        return n_inputs

    backend._send_input = fake_send_input
    backend.type_unicode_char("A")

    down, up = captured["events"]
    assert captured["cb_size"] == ctypes.sizeof(INPUT)
    assert down.type == INPUT_KEYBOARD
    assert up.type == INPUT_KEYBOARD
    assert down.ki.wVk == 0
    assert up.ki.wVk == 0
    assert down.ki.wScan == ord("A")
    assert up.ki.wScan == ord("A")
    assert down.ki.dwFlags == KEYEVENTF_UNICODE
    assert up.ki.dwFlags == (KEYEVENTF_UNICODE | KEYEVENTF_KEYUP)
