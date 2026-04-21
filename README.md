# inputctl

`inputctl` is a Windows-first CLI for synthetic input, designed to be easy for humans and AI agents to call from the command line.

Phase 1 implements keyboard input only. The backend uses the native Win32 `SendInput` API via `ctypes`; it does **not** rely on `pyautogui`.

## Features

- Windows-only keyboard automation via `SendInput`
- Typer-based CLI with explicit subcommands
- Normalized key registry with aliases like `ctrl`, `esc`, `return`, and `win`
- Clean separation between CLI, key mapping, keyboard orchestration, and Win32 injection
- Testable architecture with the Win32 boundary isolated behind a backend class

## Requirements

- Windows
- Python 3.11+

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

## Usage

```powershell
inputctl keyboard press enter
inputctl keyboard down shift
inputctl keyboard up shift
inputctl keyboard combo ctrl shift esc
inputctl keyboard type "hello world"
inputctl keyboard list-keys
```

Verbose mode and configurable delays:

```powershell
inputctl --verbose --key-delay-ms 10 --press-delay-ms 15 keyboard combo ctrl alt delete
```

## Supported commands

- `inputctl keyboard press <key>`
- `inputctl keyboard down <key>`
- `inputctl keyboard up <key>`
- `inputctl keyboard combo <keys...>`
- `inputctl keyboard type <text>`
- `inputctl keyboard list-keys`

## Key naming

The CLI accepts canonical key names and a few common aliases:

- `ctrl` → `control`
- `esc` → `escape`
- `return` → `enter`
- `win` → `lwin`

Use `inputctl keyboard list-keys` to see the current registry.

## Development and tests

```powershell
pytest
```

The tests focus on the non-OS-specific parts of the system: key normalization, command routing, and keyboard orchestration logic. The actual Win32 injection call is isolated behind `SendInputBackend`.

## Safety / limitations

- Synthetic input may not reach elevated applications if `inputctl` is running at a lower integrity level.
- Some games, anti-cheat protected software, and raw-input consumers may ignore or block `SendInput`.
- Printable character behavior assumes a standard US-style keyboard layout for Phase 1 ASCII typing.
- Full Unicode text typing is not enabled by default yet, though the backend is structured so it can be added cleanly later.

## Next steps

Planned follow-up work for gamepad support:

- Add a sibling `gamepad.py` orchestration layer
- Introduce a gamepad backend module without changing keyboard command contracts
- Expand the registry pattern to support controller buttons, axes, and aliases
- Add Unicode typing support via `KEYEVENTF_UNICODE` where appropriate

