"""Key registry and normalization helpers for inputctl."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from inputctl.win32_sendinput import (
    KEYEVENTF_EXTENDEDKEY,
    VK_0,
    VK_1,
    VK_2,
    VK_3,
    VK_4,
    VK_5,
    VK_6,
    VK_7,
    VK_8,
    VK_9,
    VK_A,
    VK_B,
    VK_BACK,
    VK_C,
    VK_CONTROL,
    VK_D,
    VK_DELETE,
    VK_DOWN,
    VK_E,
    VK_END,
    VK_ESCAPE,
    VK_F,
    VK_F1,
    VK_F10,
    VK_F11,
    VK_F12,
    VK_F2,
    VK_F3,
    VK_F4,
    VK_F5,
    VK_F6,
    VK_F7,
    VK_F8,
    VK_F9,
    VK_G,
    VK_H,
    VK_HOME,
    VK_I,
    VK_INSERT,
    VK_J,
    VK_K,
    VK_L,
    VK_LEFT,
    VK_LWIN,
    VK_M,
    VK_MENU,
    VK_N,
    VK_NEXT,
    VK_O,
    VK_OEM_1,
    VK_OEM_2,
    VK_OEM_3,
    VK_OEM_4,
    VK_OEM_5,
    VK_OEM_6,
    VK_OEM_7,
    VK_OEM_COMMA,
    VK_OEM_MINUS,
    VK_OEM_PERIOD,
    VK_OEM_PLUS,
    VK_P,
    VK_PRIOR,
    VK_Q,
    VK_R,
    VK_RETURN,
    VK_RIGHT,
    VK_S,
    VK_SHIFT,
    VK_SPACE,
    VK_T,
    VK_TAB,
    VK_U,
    VK_UP,
    VK_V,
    VK_W,
    VK_X,
    VK_Y,
    VK_Z,
)


class UnknownKeyError(ValueError):
    """Raised when the requested key name is not in the registry."""


class UnsupportedCharacterError(ValueError):
    """Raised when phase 1 ASCII typing cannot represent a character safely."""


@dataclass(frozen=True, slots=True)
class KeySpec:
    """Canonical information for a supported key."""

    name: str
    vk_code: int
    aliases: tuple[str, ...] = ()
    input_flags: int = 0


def _key(name: str, vk_code: int, *aliases: str, input_flags: int = 0) -> KeySpec:
    return KeySpec(name=name, vk_code=vk_code, aliases=aliases, input_flags=input_flags)


MODIFIER_KEYS = (
    _key("shift", VK_SHIFT),
    _key("control", VK_CONTROL, "ctrl", "ctl"),
    _key("alt", VK_MENU, "menu"),
    _key("lwin", VK_LWIN, "win", "windows", input_flags=KEYEVENTF_EXTENDEDKEY),
)

CONTROL_KEYS = (
    _key("enter", VK_RETURN, "return"),
    _key("escape", VK_ESCAPE, "esc"),
    _key("tab", VK_TAB),
    _key("space", VK_SPACE),
    _key("backspace", VK_BACK, "bksp"),
)

NAVIGATION_KEYS = (
    _key("up", VK_UP, input_flags=KEYEVENTF_EXTENDEDKEY),
    _key("down", VK_DOWN, input_flags=KEYEVENTF_EXTENDEDKEY),
    _key("left", VK_LEFT, input_flags=KEYEVENTF_EXTENDEDKEY),
    _key("right", VK_RIGHT, input_flags=KEYEVENTF_EXTENDEDKEY),
    _key("home", VK_HOME, input_flags=KEYEVENTF_EXTENDEDKEY),
    _key("end", VK_END, input_flags=KEYEVENTF_EXTENDEDKEY),
    _key("pageup", VK_PRIOR, "pgup", "page-up", input_flags=KEYEVENTF_EXTENDEDKEY),
    _key("pagedown", VK_NEXT, "pgdn", "page-down", input_flags=KEYEVENTF_EXTENDEDKEY),
    _key("insert", VK_INSERT, "ins", input_flags=KEYEVENTF_EXTENDEDKEY),
    _key("delete", VK_DELETE, "del", input_flags=KEYEVENTF_EXTENDEDKEY),
)

FUNCTION_KEYS = tuple(
    _key(f"f{index}", vk_code)
    for index, vk_code in enumerate(
        (VK_F1, VK_F2, VK_F3, VK_F4, VK_F5, VK_F6, VK_F7, VK_F8, VK_F9, VK_F10, VK_F11, VK_F12),
        start=1,
    )
)

LETTER_KEYS = tuple(
    _key(name, vk_code)
    for name, vk_code in zip(
        "abcdefghijklmnopqrstuvwxyz",
        (VK_A, VK_B, VK_C, VK_D, VK_E, VK_F, VK_G, VK_H, VK_I, VK_J, VK_K, VK_L, VK_M, VK_N, VK_O, VK_P, VK_Q, VK_R, VK_S, VK_T, VK_U, VK_V, VK_W, VK_X, VK_Y, VK_Z),
        strict=True,
    )
)

DIGIT_KEYS = tuple(
    _key(name, vk_code)
    for name, vk_code in zip(
        "0123456789",
        (VK_0, VK_1, VK_2, VK_3, VK_4, VK_5, VK_6, VK_7, VK_8, VK_9),
        strict=True,
    )
)

PUNCTUATION_KEYS = (
    _key("semicolon", VK_OEM_1, ";"),
    _key("equals", VK_OEM_PLUS, "="),
    _key("comma", VK_OEM_COMMA, ","),
    _key("minus", VK_OEM_MINUS, "-"),
    _key("period", VK_OEM_PERIOD, "."),
    _key("slash", VK_OEM_2, "/"),
    _key("backtick", VK_OEM_3, "`", "grave"),
    _key("lbracket", VK_OEM_4, "[", "leftbracket"),
    _key("backslash", VK_OEM_5, "\\"),
    _key("rbracket", VK_OEM_6, "]", "rightbracket"),
    _key("quote", VK_OEM_7, "'"),
)

KEY_GROUPS: tuple[tuple[str, tuple[KeySpec, ...]], ...] = (
    ("Modifiers", MODIFIER_KEYS),
    ("Control", CONTROL_KEYS),
    ("Navigation", NAVIGATION_KEYS),
    ("Function", FUNCTION_KEYS),
    ("Letters", LETTER_KEYS),
    ("Digits", DIGIT_KEYS),
    ("Punctuation", PUNCTUATION_KEYS),
)

_NORMALIZE_PATTERN = re.compile(r"[\s_-]+")


def _normalize(raw: str) -> str:
    return _NORMALIZE_PATTERN.sub("", raw.strip().lower())


ALL_KEYS = tuple(spec for _, group in KEY_GROUPS for spec in group)
KEYS_BY_NAME = {spec.name: spec for spec in ALL_KEYS}

ALIASES: dict[str, str] = {}
for spec in ALL_KEYS:
    ALIASES[_normalize(spec.name)] = spec.name
    for alias in spec.aliases:
        ALIASES[_normalize(alias)] = spec.name

ASCII_CHAR_TO_KEYS: dict[str, tuple[str, ...]] = {
    " ": ("space",),
    "\t": ("tab",),
    "\n": ("enter",),
    "\r": ("enter",),
    "-": ("minus",),
    "_": ("shift", "minus"),
    "=": ("equals",),
    "+": ("shift", "equals"),
    "[": ("lbracket",),
    "{": ("shift", "lbracket"),
    "]": ("rbracket",),
    "}": ("shift", "rbracket"),
    "\\": ("backslash",),
    "|": ("shift", "backslash"),
    ";": ("semicolon",),
    ":": ("shift", "semicolon"),
    "'": ("quote",),
    '"': ("shift", "quote"),
    ",": ("comma",),
    "<": ("shift", "comma"),
    ".": ("period",),
    ">": ("shift", "period"),
    "/": ("slash",),
    "?": ("shift", "slash"),
    "`": ("backtick",),
    "~": ("shift", "backtick"),
    "!": ("shift", "1"),
    "@": ("shift", "2"),
    "#": ("shift", "3"),
    "$": ("shift", "4"),
    "%": ("shift", "5"),
    "^": ("shift", "6"),
    "&": ("shift", "7"),
    "*": ("shift", "8"),
    "(": ("shift", "9"),
    ")": ("shift", "0"),
}
for letter in "abcdefghijklmnopqrstuvwxyz":
    ASCII_CHAR_TO_KEYS[letter] = (letter,)
    ASCII_CHAR_TO_KEYS[letter.upper()] = ("shift", letter)
for digit in "0123456789":
    ASCII_CHAR_TO_KEYS[digit] = (digit,)


def normalize_key_name(raw: str) -> str:
    """Normalize a user-provided key name for registry lookup."""
    normalized = _normalize(raw)
    if not normalized:
        raise UnknownKeyError("Key name cannot be empty.")
    return normalized


def resolve_key(raw: str) -> KeySpec:
    """Resolve a raw key name or alias to a canonical KeySpec."""
    normalized = normalize_key_name(raw)
    canonical_name = ALIASES.get(normalized)
    if canonical_name is None:
        supported = ", ".join(spec.name for spec in ALL_KEYS[:12])
        raise UnknownKeyError(f"Unsupported key: {raw!r}. Example supported keys: {supported}.")
    return KEYS_BY_NAME[canonical_name]


def list_supported_keys() -> list[KeySpec]:
    """Return the full supported key list."""
    return list(ALL_KEYS)


def iter_key_groups() -> Iterable[tuple[str, tuple[KeySpec, ...]]]:
    """Yield key groups for human-friendly CLI output."""
    return KEY_GROUPS


def resolve_text_char(char: str) -> tuple[str, ...]:
    """Resolve a phase 1 text character into one or more key names."""
    if len(char) != 1:
        raise UnsupportedCharacterError("Text typing expects one character at a time.")
    if ord(char) > 0x7F:
        raise UnsupportedCharacterError(
            f"Unsupported character for phase 1 typing: {char!r}. Phase 1 supports ASCII text only."
        )
    key_names = ASCII_CHAR_TO_KEYS.get(char)
    if key_names is None:
        raise UnsupportedCharacterError(
            f"Unsupported character for phase 1 typing: {char!r}. "
            "This printable ASCII character is not mapped yet."
        )
    return key_names
