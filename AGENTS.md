# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

JablotronPy is a Python client library for the Jablotron Cloud API (`api.jablonet.net`). It has no local services, databases, or servers — it is a pure HTTP client wrapper. See `README.md` for usage examples and method documentation.

### Development commands

| Task | Command |
|---|---|
| Install dependencies | `uv sync` |
| Lint | `uv run ruff check .` |
| Format check | `uv run ruff format --check .` |
| Format fix | `uv run ruff format .` |
| Run tests | `uv run python -m unittest discover -s tests -v` |
| Build package | `uv build` |

### Testing caveats

- All tests in `tests/test_jablotron.py` are **integration tests** against the live Jablotron Cloud API. They require real credentials set as environment variables: `TEST_JABLOTRON_USER`, `TEST_JABLOTRON_PASS`, `TEST_JABLOTRON_PIN`.
- Without these credentials, the test module fails to import (class-level `os.environ` lookups and `perform_login()` run at import time).
- There are no mocks, fixtures, or local test doubles in the project.
- The project does not use `pytest` — it uses stdlib `unittest`.

### Other notes

- The package manager is `uv` (lockfile: `uv.lock`). Do not use `pip install` for dev work.
- Dev dependency is `ruff` only (linter/formatter).
- Python ≥3.10 is required (`pyproject.toml`).
