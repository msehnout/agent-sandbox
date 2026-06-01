# agent-sandbox

A tiny CLI (`sbx`) that scaffolds and manages a containerized sandbox for running coding agents (like Claude Code) safely isolated from your host.

It generates a `.agent-sandbox/` directory with a `docker-compose.yaml`, `Dockerfile`, and `entrypoint.sh`, then builds and runs the container — bind-mounting your project and matching your host user so created files keep correct ownership.

## Requirements

- Python ≥ 3.14
- `podman-compose` (or edit `COMPOSE_CMD` in `main.py` to use `docker compose`)

## Installation

```bash
uv tool install --editable .
```

This installs the `sbx` command on your `PATH`. The `--editable` flag is intentional: `agent-sandbox` is meant to be a starting point, not a finished product. You're expected to tweak `main.py` (the scaffolded templates, `COMPOSE_CMD`, mounts, etc.) to fit your own workflow — and because the install is editable, those edits take effect immediately without reinstalling.

## Usage

```bash
sbx init     # scaffold .agent-sandbox/ in the current directory
sbx build    # build the sandbox image
sbx run      # start the sandbox (drops you into a shell)
sbx down     # stop and remove the sandbox
```

Run a one-off command inside the sandbox:

```bash
sbx run -- <command>
```

## Development

```bash
make help        # list available commands
make format-code # auto-format
make check       # lint + type-check
```
