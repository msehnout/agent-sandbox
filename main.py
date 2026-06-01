import argparse
import sys


def cmd_init(args: argparse.Namespace) -> int:
    """Scaffold a new sandbox config in the current directory."""
    print("init: scaffolding sandbox…")  # TODO
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    """Build the sandbox image."""
    print("build: building sandbox…")  # TODO
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Start the sandbox (optionally running a command inside it)."""
    print(f"run: starting sandbox… cmd={args.cmd or '<default>'}")  # TODO
    return 0


def cmd_down(args: argparse.Namespace) -> int:
    """Stop and remove the running sandbox."""
    print("down: tearing down sandbox…")  # TODO
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sbx", description="Agent sandbox manager")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")

    sub = parser.add_subparsers(dest="command", required=True, metavar="<command>")

    sub.add_parser("init", help="initialize a new sandbox here").set_defaults(func=cmd_init)
    sub.add_parser("build", help="build the sandbox image").set_defaults(func=cmd_build)

    p_run = sub.add_parser("run", help="start the sandbox")
    p_run.add_argument("cmd", nargs=argparse.REMAINDER, help="command to run inside the sandbox")
    p_run.set_defaults(func=cmd_run)

    sub.add_parser("down", help="tear down the sandbox").set_defaults(func=cmd_down)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
