"""CLI tests for Typer command wiring and error handling."""

from __future__ import annotations

from dataclasses import dataclass, field

from typer.testing import CliRunner

from inputctl import cli
from inputctl.keymap import UnknownKeyError, UnsupportedCharacterError


runner = CliRunner()


@dataclass
class StubController:
    """Record high-level CLI calls without touching the OS."""

    calls: list[tuple[str, object]] = field(default_factory=list)

    def press(self, key: str) -> None:
        self.calls.append(("press", key))

    def down(self, key: str) -> None:
        self.calls.append(("down", key))

    def up(self, key: str) -> None:
        self.calls.append(("up", key))

    def combo(self, keys: list[str]) -> None:
        self.calls.append(("combo", keys))

    def type_text(self, text: str) -> None:
        self.calls.append(("type", text))


def test_press_command_invokes_controller(monkeypatch) -> None:
    controller = StubController()
    monkeypatch.setattr(cli, "build_controller", lambda config: controller)

    result = runner.invoke(cli.app, ["keyboard", "press", "enter"])

    assert result.exit_code == 0
    assert controller.calls == [("press", "enter")]


def test_press_command_passes_config_to_factory(monkeypatch) -> None:
    controller = StubController()
    seen = {}

    def fake_factory(config: cli.CLIConfig) -> StubController:
        seen["config"] = config
        return controller

    monkeypatch.setattr(cli, "build_controller", fake_factory)

    result = runner.invoke(
        cli.app,
        ["--key-delay-ms", "5", "--press-delay-ms", "11", "keyboard", "press", "a"],
    )

    assert result.exit_code == 0
    assert seen["config"].key_delay_ms == 5
    assert seen["config"].press_delay_ms == 11


def test_invalid_key_returns_non_zero_exit(monkeypatch) -> None:
    class FailingController(StubController):
        def press(self, key: str) -> None:
            raise UnknownKeyError("Unsupported key: 'bad'.")

    monkeypatch.setattr(cli, "build_controller", lambda config: FailingController())

    result = runner.invoke(cli.app, ["keyboard", "press", "bad"])

    assert result.exit_code == 2
    assert "keyboard press error" in result.output


def test_combo_forwards_ordered_keys(monkeypatch) -> None:
    controller = StubController()
    monkeypatch.setattr(cli, "build_controller", lambda config: controller)

    result = runner.invoke(cli.app, ["keyboard", "combo", "ctrl", "shift", "esc"])

    assert result.exit_code == 0
    assert controller.calls == [("combo", ["ctrl", "shift", "esc"])]


def test_type_reports_unsupported_non_ascii(monkeypatch) -> None:
    class FailingController(StubController):
        def type_text(self, text: str) -> None:
            raise UnsupportedCharacterError("Unsupported character for phase 1 typing: 'é'.")

    monkeypatch.setattr(cli, "build_controller", lambda config: FailingController())

    result = runner.invoke(cli.app, ["keyboard", "type", "é"])

    assert result.exit_code == 2
    assert "Unsupported character" in result.output


def test_list_keys_prints_known_keys() -> None:
    result = runner.invoke(cli.app, ["keyboard", "list-keys"])

    assert result.exit_code == 0
    assert "Modifiers:" in result.stdout
    assert "control" in result.stdout
    assert "escape" in result.stdout
