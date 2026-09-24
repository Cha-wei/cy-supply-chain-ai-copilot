"""Thin CLI over the deterministic core (outer run entry point only).

Registered architecture (ADR-001): the thin CLI calls application orchestration;
orchestration composes snapshot loading / validation / later tranches.  File reading
happens in this outer layer, the core consumes explicit inputs, and the core never
calls back into the CLI.

The CLI does **not** create an Analysis Run, does not persist anything, and exposes
no business semantics -- it renders the Layer-1 package disposition.

Usage::

    python -m snapshot_loader --trusted-root <dir> --package <dir>
    python -m snapshot_loader --trusted-root <dir> --package <dir> --json
    python -m snapshot_loader --trusted-root <dir> --package <dir> --reverify
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .loader import load_package
from .trust import TrustedInputBoundary

EXIT_ACCEPTED = 0
EXIT_NOT_ACCEPTED = 1
EXIT_USAGE = 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="snapshot_loader",
        description=(
            "Controlled JSON Snapshot loader -- POC v0.2 Layer-1 package acceptance "
            "(package structural validation only)"
        ),
    )
    parser.add_argument(
        "--trusted-root",
        required=True,
        metavar="DIR",
        help=(
            "configured trusted package-input boundary; the package directory must be a "
            "direct child of this directory (§4.3.28 D.3 IG-self-C)"
        ),
    )
    parser.add_argument(
        "--package",
        required=True,
        metavar="DIR",
        help="package directory to attempt to accept",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="emit the deterministic report as JSON instead of text",
    )
    parser.add_argument(
        "--reverify",
        action="store_true",
        help=(
            "after a successful acceptance, immediately re-verify required integrity as "
            "a trusted-reuse check (§4.3.28 C.3 MG-2)"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    arguments = parser.parse_args(argv)

    if not Path(arguments.trusted_root).exists():
        parser.error(f"trusted root does not exist: {arguments.trusted_root}")

    report = load_package(
        arguments.package,
        trusted_boundary=TrustedInputBoundary(root=Path(arguments.trusted_root)),
    )

    payload: dict[str, object] = {"import": report.to_dict()}

    if arguments.reverify:
        if report.accepted_package is None:
            payload["reverify"] = {
                "skipped": True,
                "reason": "package was not accepted, so there is no accepted package to reuse",
            }
        else:
            verdict = report.accepted_package.reverify()
            payload["reverify"] = verdict.to_dict()

    if arguments.as_json:
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(report.render_text())
        if arguments.reverify and report.accepted_package is not None:
            verdict = report.accepted_package.reverify()
            print()
            print("trusted reuse re-verification")
            print(f"  disposition : {verdict.disposition}")
            print(f"  reusable    : {verdict.reusable}")
            for issue in verdict.collector.sorted_issues():
                print(f"  - {issue.location}: {issue.detail}")

    return EXIT_ACCEPTED if report.accepted else EXIT_NOT_ACCEPTED


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
