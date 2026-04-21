"""Module entry point for ``python -m inputctl``."""

from inputctl.cli import app


def main() -> None:
    """Run the Typer application."""
    app()


if __name__ == "__main__":
    main()

