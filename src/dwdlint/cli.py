from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from dwdlint.core import lint_paths

# Cross-corpus references (worlds -> rules packs, scenarios -> worlds) only
# resolve when the whole authored surface is linted together.
DEFAULT_SURFACE = (Path("worlds"), Path("rules"), Path("docs/simulations"))


def default_paths() -> list[Path]:
    existing = [path for path in DEFAULT_SURFACE if path.exists()]
    return existing or [Path("worlds")]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dwdlint",
        description="Validate Dungeoneer World Definition YAML.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=None,
        help=(
            "YAML files or directories to lint together "
            "(default: worlds, rules, and docs/simulations where present)"
        ),
    )
    parser.add_argument(
        "--allow-extensions",
        action="store_true",
        help="Exit successfully when only unrecognized DWD extensions are found.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Diagnostic output format.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = lint_paths(args.paths if args.paths else default_paths())

    if args.format == "json":
        print(json.dumps(result.as_dict(), indent=2))
    else:
        for diagnostic in result.diagnostics:
            print(diagnostic.format())
        print(result.summary())

    if result.error_count:
        return 1
    if result.extension_count and not args.allow_extensions:
        return 1
    return 0
