"""Win32 keyboard input backend built on top of SendInput."""

from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes
from typing import Sequence


INPUT_KEYBOARD = 1

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

VK_BACK = 0x08
VK_TAB = 0x09
VK_RETURN = 0x0D
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_PAUSE = 0x13
VK_CAPITAL = 0x14
VK_ESCAPE = 0x1B
VK_SPACE = 0x20
VK_PRIOR = 0x21
VK_NEXT = 0x22
VK_END = 0x23
VK_HOME = 0x24
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_INSERT = 0x2D
VK_DELETE = 0x2E
VK_0 = 0x30
VK_1 = 0x31
VK_2 = 0x32
VK_3 = 0x33
VK_4 = 0x34
VK_5 = 0x35
VK_6 = 0x36
VK_7 = 0x37
VK_8 = 0x38
VK_9 = 0x39
VK_A = 0x41
VK_B = 0x42
VK_C = 0x43
VK_D = 0x44
VK_E = 0x45
VK_F = 0x46
VK_G = 0x47
VK_H = 0x48
VK_I = 0x49
VK_J = 0x4A
VK_K = 0x4B
VK_L = 0x4C
VK_M = 0x4D
VK_N = 0x4E
VK_O = 0x4F
VK_P = 0x50
VK_Q = 0x51
VK_R = 0x52
VK_S = 0x53
VK_T = 0x54
VK_U = 0x55
VK_V = 0x56
VK_W = 0x57
VK_X = 0x58
VK_Y = 0x59
VK_Z = 0x5A
VK_LWIN = 0x5B
VK_F1 = 0x70
VK_F2 = 0x71
VK_F3 = 0x72
VK_F4 = 0x73
VK_F5 = 0x74
VK_F6 = 0x75
VK_F7 = 0x76
VK_F8 = 0x77
VK_F9 = 0x78
VK_F10 = 0x79
VK_F11 = 0x7A
VK_F12 = 0x7B
VK_OEM_1 = 0xBA
VK_OEM_PLUS = 0xBB
VK_OEM_COMMA = 0xBC
VK_OEM_MINUS = 0xBD
VK_OEM_PERIOD = 0xBE
VK_OEM_2 = 0xBF
VK_OEM_3 = 0xC0
VK_OEM_4 = 0xDB
VK_OEM_5 = 0xDC
VK_OEM_6 = 0xDD
VK_OEM_7 = 0xDE

ULONG_PTR = wintypes.WPARAM


class InputInjectionError(RuntimeError):
    """Raised when Win32 input injection fails."""


class KEYBDINPUT(ctypes.Structure):
    """Structure for keyboard input events."""

    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class MOUSEINPUT(ctypes.Structure):
    """Structure for mouse input events."""

    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    """Structure for hardware input events."""

    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    """INPUT union wrapper for SendInput."""

    _anonymous_ = ("u",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("u", _INPUTUNION),
    ]


class SendInputBackend:
    """Thin Win32 SendInput wrapper for keyboard events."""

    def __init__(self) -> None:
        if sys.platform != "win32":
            raise InputInjectionError("inputctl only supports Windows.")

        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._send_input = self._user32.SendInput
        self._send_input.argtypes = (
            wintypes.UINT,
            ctypes.POINTER(INPUT),
            ctypes.c_int,
        )
        self._send_input.restype = wintypes.UINT

    def key_down(self, vk_code: int, flags: int = 0) -> None:
        """Send a key-down event for a virtual key."""
        self._send((self._keyboard_input(vk_code, flags),))

    def key_up(self, vk_code: int, flags: int = 0) -> None:
        """Send a key-up event for a virtual key."""
        self._send((self._keyboard_input(vk_code, flags | KEYEVENTF_KEYUP),))

    def press_key(self, vk_code: int, flags: int = 0, press_delay_ms: int = 0) -> None:
        """Send a key press consisting of key down followed by key up."""
        self.key_down(vk_code, flags)
        if press_delay_ms > 0:
            time.sleep(press_delay_ms / 1000)
        self.key_up(vk_code, flags)

    def type_unicode_char(self, char: str) -> None:
        """Send a single Unicode character using KEYEVENTF_UNICODE."""
        if len(char) != 1:
            raise ValueError("type_unicode_char expects a single character.")

        codepoint = ord(char)
        if codepoint > 0xFFFF:
            raise ValueError("Only BMP Unicode characters are supported by this helper.")

        down = INPUT(
            type=INPUT_KEYBOARD,
            ki=KEYBDINPUT(
                wVk=0,
                wScan=codepoint,
                dwFlags=KEYEVENTF_UNICODE,
                time=0,
                dwExtraInfo=0,
            ),
        )
        up = INPUT(
            type=INPUT_KEYBOARD,
            ki=KEYBDINPUT(
                wVk=0,
                wScan=codepoint,
                dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP,
                time=0,
                dwExtraInfo=0,
            ),
        )
        self._send((down, up))

    def _send(self, inputs: Sequence[INPUT]) -> None:
        """Send one or more keyboard input events through Win32 SendInput."""
        input_array = (INPUT * len(inputs))(*inputs)
        sent = self._send_input(len(inputs), input_array, ctypes.sizeof(INPUT))
        if sent != len(inputs):
            error_code = ctypes.get_last_error()
            error_message = ctypes.FormatError(error_code).strip() if error_code else "Unknown SendInput failure."
            raise InputInjectionError(
                f"SendInput delivered {sent} of {len(inputs)} events. "
                f"Win32 error {error_code}: {error_message}"
            )

    @staticmethod
    def _keyboard_input(vk_code: int, flags: int = 0) -> INPUT:
        """Create a keyboard INPUT record for a virtual key event."""
        return INPUT(
            type=INPUT_KEYBOARD,
            ki=KEYBDINPUT(
                wVk=vk_code,
                wScan=0,
                dwFlags=flags,
                time=0,
                dwExtraInfo=0,
            ),
        )
