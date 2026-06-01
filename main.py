import argparse
import os
import random
import re
import subprocess
import sys
from pathlib import Path

SANDBOX_DIR = ".agent-sandbox"
COMPOSE_FILE = "docker-compose.yaml"
SERVICE = "claude"
COMPOSE_CMD = ["podman-compose"]  # Replace with docker compose if you wish

DOCKER_COMPOSE_TEMPLATE = r"""
services:
  claude:
    container_name: {{PROJECT}}-claude
    #runtime: krun
    annotations:
      run.oci.handler: krun
      krun.ram_mib: "4096"
      krun.cpus: "4"
    user: "1000:1000"
    userns_mode: keep-id    # optional, for rootless host
    build:
      context: .
      args:
        HOST_UID: "${HOST_UID}"  # use UID and GID from the host so that files created in the container have correct permissions
        HOST_GID: "${HOST_GID}"
    volumes:
      - ../:/app:U,z                  # bind mount your project
      - {{PROJECT}}-venv-cache:/venv:U,z # shadows .venv from host, named volume prevents .venv from being recreated every time
      - claude-config:/home/appuser/.claude:U,z  # persistent claude credentials/config
    working_dir: /app
    stdin_open: true
    tty: true
    environment:
      - CLAUDE_CONFIG_DIR=/home/appuser/.claude
      - UV_LINK_MODE=copy
      - UV_PROJECT_ENVIRONMENT=/venv/env  # This is inside the cached volume
      - UV_PYTHON_INSTALL_DIR=/venv/python  # So that uv-managed python installations are not in home but cached in /venv
      - TERM=xterm-256color
      - COLORTERM=truecolor

volumes:
  {{PROJECT}}-venv-cache:
  claude-config:
    external: true
    name: claude-config
"""

DOCKERFILE_TEMPLATE = r"""
FROM fedora:44

ARG HOST_UID=1000
ARG HOST_GID=1000

# Install dependency for pnpm
RUN dnf install libatomic -y && \
    dnf clean all

# Create group and user matching host UID/GID
RUN groupadd -g ${HOST_GID} appuser && \
    useradd -u ${HOST_UID} -g ${HOST_GID} -m appuser

RUN mkdir -p /venv && chown appuser:appuser /venv
RUN mkdir -p /home/appuser/.claude && chown appuser:appuser /home/appuser/.claude

USER appuser

# Rarely-changing tooling. Kept above the dnf layer so editing the RPM list
# below does not invalidate (and re-run) these installs.
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    curl -fsSL https://claude.ai/install.sh | bash && \
    curl -fsSL https://get.pnpm.io/install.sh | sh -

USER root

# Frequently-changing RPMs. Kept last so adding a package only rebuilds from here down.
RUN dnf install git make vim fish free htop nodejs22 nodejs22-npm-bin libpq-devel python3-devel gcc -y && \
    dnf clean all

COPY --chown=appuser entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER appuser
WORKDIR /app

# This is needed because entrypoint does not have .local/bin in the PATH
ENV PATH="/home/appuser/.local/bin:$PATH"
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/bin/fish"]
"""

ENTRYPOINT_TEMPLATE = r"""
#!/bin/bash
set -e

echo "Sandbox started as user: $(id -un) in directory: $(pwd)"

if [ "$(id -un)" != "appuser" ]; then
  runuser -u appuser -- uv sync
  echo "Running ${@} as appuser"
  exec runuser -u appuser -- "$@"
fi

uv sync
exec "$@"
"""


def _slugify(name: str) -> str:
    """Turn a directory name into a docker-safe identifier."""
    slug = re.sub(r"[^a-z0-9_.-]+", "-", name.lower()).strip("-._")
    return slug or "sandbox"


def cmd_init(args: argparse.Namespace) -> int:
    """Scaffold a new sandbox config in the current directory."""
    target = Path.cwd() / SANDBOX_DIR
    if target.exists():
        print(f"{SANDBOX_DIR}/ already exists; leaving it untouched.", file=sys.stderr)
        return 1

    project = _slugify(Path.cwd().name)
    suffix = f"{random.randint(0, 999_999):06d}"
    base = f"{project}-{suffix}"

    target.mkdir()
    (target / "docker-compose.yaml").write_text(
        DOCKER_COMPOSE_TEMPLATE.replace("{{PROJECT}}", base).lstrip("\n")
    )
    (target / "Dockerfile").write_text(DOCKERFILE_TEMPLATE.lstrip("\n"))
    entrypoint = target / "entrypoint.sh"
    entrypoint.write_text(ENTRYPOINT_TEMPLATE.lstrip("\n"))
    entrypoint.chmod(0o755)

    print(f"Initialized {SANDBOX_DIR}/ (name: {base})")
    for fname in ("docker-compose.yaml", "Dockerfile", "entrypoint.sh"):
        print(f"  - {SANDBOX_DIR}/{fname}")
    return 0


def _run_compose(compose_args: list[str], verbose: bool = False) -> int:
    """Invoke `<compose> -f .agent-sandbox/docker-compose.yaml <args>` with host IDs."""
    compose_file = Path.cwd() / SANDBOX_DIR / COMPOSE_FILE
    if not compose_file.exists():
        print(
            f"No {SANDBOX_DIR}/{COMPOSE_FILE} found. Run `sbx init` first.",
            file=sys.stderr,
        )
        return 1

    env = {
        **os.environ,
        "HOST_UID": str(os.getuid()),  # mirror `id -u` / `id -g` from the Makefile so
        "HOST_GID": str(os.getgid()),  # files made in the container keep host ownership
    }

    cmd = [*COMPOSE_CMD, "-f", str(compose_file), *compose_args]
    if verbose:
        print("+ " + " ".join(cmd), file=sys.stderr)
    try:
        return subprocess.run(cmd, env=env).returncode
    except FileNotFoundError:
        print(f"`{COMPOSE_CMD[0]}` not found on PATH.", file=sys.stderr)
        return 127


def cmd_build(args: argparse.Namespace) -> int:
    """Build the sandbox image."""
    return _run_compose(["build"], args.verbose)


def cmd_run(args: argparse.Namespace) -> int:
    """Start the sandbox (optionally running a command inside it)."""
    cmd = args.cmd or []
    if cmd and cmd[0] == "--":  # argparse.REMAINDER keeps a leading `--`
        cmd = cmd[1:]
    return _run_compose(["run", "--rm", SERVICE, *cmd], args.verbose)


def cmd_down(args: argparse.Namespace) -> int:
    """Stop and remove the running sandbox."""
    return _run_compose(["down", "--remove-orphans"], args.verbose)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sbx", description="Agent sandbox manager")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")

    sub = parser.add_subparsers(dest="command", required=True, metavar="<command>")

    sub.add_parser("init", help="initialize a new sandbox here").set_defaults(
        func=cmd_init
    )
    sub.add_parser("build", help="build the sandbox image").set_defaults(func=cmd_build)

    p_run = sub.add_parser("run", help="start the sandbox")
    p_run.add_argument(
        "cmd", nargs=argparse.REMAINDER, help="command to run inside the sandbox"
    )
    p_run.set_defaults(func=cmd_run)

    sub.add_parser("down", help="tear down the sandbox").set_defaults(func=cmd_down)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
