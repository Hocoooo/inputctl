# Repository Guidelines

## Project Structure & Module Organization
This repository is currently a minimal workspace. The only tracked project folder today is `.omx/`, which stores local OMX runtime state, logs, and session metadata. Keep contributor-facing source code at the repository root or in clearly named top-level folders such as `src/`, `tests/`, and `docs/` as the project grows. Avoid mixing product code with `.omx/` artifacts.

## Build, Test, and Development Commands
There is no application build or test pipeline checked in yet. Until one is added, use a small set of repo hygiene commands:

- `Get-ChildItem -Force` — inspect the current repository layout.
- `Get-ChildItem -Recurse` — review all tracked and generated files before committing.
- `git status` — confirm the intended diff.

When build or test tooling is introduced, document the canonical commands in `README.md` and keep this file in sync.

## Coding Style & Naming Conventions
Prefer small, focused modules and predictable top-level directories. Use UTF-8 text files, 4-space indentation for code and Markdown lists, and descriptive names such as `input_controller.rs`, `keyboard_hook_test.py`, or `docs/architecture.md`. Match the formatter and linter of the language you introduce; do not add new dependencies just for style.

## Testing Guidelines
Add tests alongside any new feature or bug fix. Prefer a dedicated `tests/` folder or language-standard test layout. Name tests after behavior, for example `test_blocks_repeated_keypresses`. Keep fast unit tests as the default and add integration tests only where system-level input behavior must be verified.

## Commit & Pull Request Guidelines
This checkout does not currently include Git history, so there is no repository-specific convention to inherit. Use short, imperative commit subjects and, when working under OMX, follow the Lore-style trailer format from the active agent instructions. Pull requests should explain why the change is needed, summarize verification performed, link related issues, and include screenshots or logs when behavior is visible or system-dependent.

## Security & Configuration Tips
Treat `.omx/` as runtime state, not product code. Do not hard-code local paths, secrets, or machine-specific settings. If contributor setup becomes non-trivial, add a `docs/setup.md` guide before expanding the toolchain.
