"""Typer CLI for inputctl."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Annotated

import typer

from inputctl.keymap import UnknownKeyError, UnsupportedCharacterError, iter_key_groups
from inputctl.keyboard import KeyboardController
from inputctl.win32_sendinput import InputInjectionError, SendInputBackend


app = typer.Typer(
    name="inputctl",
    help="Windows-first CLI for synthetic input.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)
keyboard_app = typer.Typer(
    name="keyboard",
    help="Keyboard input commands.",
    no_args_is_help=True,
)
app.add_typer(keyboard_app, name="keyboard")


@dataclass(frozen=True, slots=True)
class CLIConfig:
    """Shared CLI configuration for command handlers."""

    verbose: bool = False
    key_delay_ms: int = 20
    press_delay_ms: int = 20


@app.callback()
def main(
    ctx: typer.Context,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose logging.")] = False,
    key_delay_ms: Annotated[
        int,
        typer.Option(help="Delay between multi-key operations and typed characters, in milliseconds.", min=0),
    ] = 20,
    press_delay_ms: Annotated[
        int,
        typer.Option(help="Delay between key down and key up for single key presses, in milliseconds.", min=0),
    ] = 20,
) -> None:
    """Initialize shared CLI state."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    ctx.obj = CLIConfig(verbose=verbose, key_delay_ms=key_delay_ms, press_delay_ms=press_delay_ms)


def build_controller(config: CLIConfig) -> KeyboardController:
    """Create the keyboard controller used by command handlers."""
    return KeyboardController(
        backend=SendInputBackend(),
        key_delay_ms=config.key_delay_ms,
        press_delay_ms=config.press_delay_ms,
        logger=logging.getLogger("inputctl.keyboard"),
    )


def get_config(ctx: typer.Context) -> CLIConfig:
    """Return validated config from Typer context."""
    config = ctx.obj
    if not isinstance(config, CLIConfig):
        return CLIConfig()
    return config


def handle_action(action: str, fn: Callable[[], None]) -> None:
    """Run a keyboard action with standardized error handling."""
    try:
        fn()
    except (UnknownKeyError, UnsupportedCharacterError, ValueError) as exc:
        typer.echo(f"{action} error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    except InputInjectionError as exc:
        typer.echo(f"{action} failed: {exc}", err=True)
        raise typer.Exit(code=3) from exc


@keyboard_app.command()
def press(ctx: typer.Context, key: str) -> None:
    """Press and release a single key."""
    controller = build_controller(get_config(ctx))
    handle_action("keyboard press", lambda: controller.press(key))


@keyboard_app.command()
def down(ctx: typer.Context, key: str) -> None:
    """Hold a key down."""
    controller = build_controller(get_config(ctx))
    handle_action("keyboard down", lambda: controller.down(key))


@keyboard_app.command()
def up(ctx: typer.Context, key: str) -> None:
    """Release a key."""
    controller = build_controller(get_config(ctx))
    handle_action("keyboard up", lambda: controller.up(key))


@keyboard_app.command()
def combo(ctx: typer.Context, keys: list[str]) -> None:
    """Press keys in order, then release them in reverse order."""
    controller = build_controller(get_config(ctx))
    handle_action("keyboard combo", lambda: controller.combo(keys))


@keyboard_app.command("type")
def type_command(ctx: typer.Context, text: str) -> None:
    """Type an ASCII text string."""
    controller = build_controller(get_config(ctx))
    handle_action("keyboard type", lambda: controller.type_text(text))


@keyboard_app.command("list-keys")
def list_keys() -> None:
    """Print the supported key registry in a human-friendly format."""
    for group_name, group in iter_key_groups():
        typer.echo(f"{group_name}:")
        for spec in group:
            alias_suffix = f" (aliases: {', '.join(spec.aliases)})" if spec.aliases else ""
            typer.echo(f"  - {spec.name}{alias_suffix}")


if __name__ == "__main__":
    app()
