from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from dwdlint.core import Severity, lint_paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dwdlint",
        description="Validate Dungeoneer World Definition YAML.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("worlds")],
        help="YAML file or directory to lint (default: worlds)",
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
    result = lint_paths(args.paths)

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
