# agent-sandbox

A tiny CLI (`sbx`) that scaffolds and manages a containerized sandbox for running coding agents (like Claude Code) safely isolated from your host.

It generates a `.agent-sandbox/` directory with a `docker-compose.yaml`, `Dockerfile`, and `entrypoint.sh`, then builds and runs the container — bind-mounting your project and matching your host user so created files keep correct ownership.

## Requirements

- Python ≥ 3.14
- `podman-compose` (or edit `COMPOSE_CMD` in `main.py` to use `docker compose`)

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
