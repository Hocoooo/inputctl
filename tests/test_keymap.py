"""Tests for key normalization and registry behavior."""

from inputctl.keymap import (
    UnknownKeyError,
    iter_key_groups,
    normalize_key_name,
    resolve_key,
    resolve_text_char,
)


def test_normalize_key_name_strips_separators() -> None:
    assert normalize_key_name(" Page-Up ") == "pageup"


def test_resolve_key_supports_aliases() -> None:
    assert resolve_key("ctrl").name == "control"
    assert resolve_key("esc").name == "escape"
    assert resolve_key("return").name == "enter"
    assert resolve_key("win").name == "lwin"


def test_unknown_key_raises_clear_error() -> None:
    try:
        resolve_key("definitely-not-a-key")
    except UnknownKeyError as exc:
        assert "Unsupported key" in str(exc)
    else:  # pragma: no cover - explicit test failure path
        raise AssertionError("Expected UnknownKeyError for unsupported key.")


def test_iter_key_groups_contains_expected_representatives() -> None:
    grouped = {group_name: [spec.name for spec in group] for group_name, group in iter_key_groups()}
    assert "control" in grouped["Modifiers"]
    assert "enter" in grouped["Control"]
    assert "f12" in grouped["Function"]


def test_resolve_text_char_maps_shifted_ascii() -> None:
    assert resolve_text_char("A") == ("shift", "a")
    assert resolve_text_char("!") == ("shift", "1")

