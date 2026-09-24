"""Thin CLI smoke tests.

The CLI is an outer run entry point only (ADR-001): it reads files, calls the
deterministic core, and renders the Layer-1 disposition.  The core never depends on
it, and the CLI creates no Analysis Run and persists nothing.
"""

from __future__ import annotations

import io
import json
import shutil
import unittest
import uuid
from contextlib import redirect_stdout
from pathlib import Path


from snapshot_loader import cli  # noqa: E402
from tests.helpers import PackageSpec, build_package, valid_package  # noqa: E402

SCRATCH_ROOT = Path(__file__).resolve().parents[1] / "build" / "test-scratch"


class CliTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = SCRATCH_ROOT / uuid.uuid4().hex
        self.boundary = self.workspace / "landing"
        self.boundary.mkdir(parents=True, exist_ok=True)
        self.addCleanup(shutil.rmtree, self.workspace, ignore_errors=True)

    def run_cli(self, *arguments: str) -> tuple[int, str]:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = cli.main(list(arguments))
        return code, buffer.getvalue()


class CliBehaviourTests(CliTestCase):
    def test_accepted_package_exits_zero_and_prints_text(self) -> None:
        built = valid_package(self.boundary / "pkg", boundary_root=self.boundary)
        code, output = self.run_cli(
            "--trusted-root", str(self.boundary), "--package", str(built.root)
        )
        self.assertEqual(code, cli.EXIT_ACCEPTED)
        self.assertIn("ACCEPTED", output)
        self.assertIn("SIMULATED-PKG-0001", output)

    def test_rejected_package_exits_non_zero(self) -> None:
        built = build_package(
            self.boundary / "pkg",
            PackageSpec(contract_version="v0.1"),
            boundary_root=self.boundary,
        )
        code, output = self.run_cli(
            "--trusted-root", str(self.boundary), "--package", str(built.root)
        )
        self.assertEqual(code, cli.EXIT_NOT_ACCEPTED)
        self.assertIn("REJECTED", output)

    def test_json_output_is_machine_readable(self) -> None:
        built = valid_package(self.boundary / "pkg", boundary_root=self.boundary)
        code, output = self.run_cli(
            "--trusted-root", str(self.boundary), "--package", str(built.root), "--json"
        )
        self.assertEqual(code, cli.EXIT_ACCEPTED)
        payload = json.loads(output)
        self.assertEqual(payload["import"]["disposition"], "ACCEPTED")
        self.assertTrue(payload["import"]["evaluable"])
        self.assertEqual(payload["import"]["issues"], [])

    def test_reverify_flag_reports_reuse_verdict(self) -> None:
        built = valid_package(self.boundary / "pkg", boundary_root=self.boundary)
        code, output = self.run_cli(
            "--trusted-root",
            str(self.boundary),
            "--package",
            str(built.root),
            "--json",
            "--reverify",
        )
        self.assertEqual(code, cli.EXIT_ACCEPTED)
        payload = json.loads(output)
        self.assertTrue(payload["reverify"]["disposition"] == "RE-VERIFIED")

    def test_reverify_is_skipped_for_a_rejected_package(self) -> None:
        built = build_package(
            self.boundary / "pkg", PackageSpec(contract_version="v0.1"), boundary_root=self.boundary
        )
        code, output = self.run_cli(
            "--trusted-root", str(self.boundary), "--package", str(built.root), "--json", "--reverify"
        )
        self.assertEqual(code, cli.EXIT_NOT_ACCEPTED)
        payload = json.loads(output)
        self.assertTrue(payload["reverify"]["skipped"])

    def test_missing_trusted_root_is_a_usage_error(self) -> None:
        built = valid_package(self.boundary / "pkg", boundary_root=self.boundary)
        with self.assertRaises(SystemExit) as context:
            self.run_cli(
                "--trusted-root",
                str(self.workspace / "absent"),
                "--package",
                str(built.root),
            )
        self.assertEqual(context.exception.code, cli.EXIT_USAGE)

    def test_cli_does_not_create_an_analysis_run_or_write_back(self) -> None:
        built = valid_package(self.boundary / "pkg", boundary_root=self.boundary)
        before = {
            path.name: path.read_bytes() for path in sorted(built.root.glob("*")) if path.is_file()
        }
        self.run_cli("--trusted-root", str(self.boundary), "--package", str(built.root))
        after = {
            path.name: path.read_bytes() for path in sorted(built.root.glob("*")) if path.is_file()
        }
        self.assertEqual(before, after)
        self.assertEqual(
            sorted(path.name for path in self.boundary.iterdir()),
            ["pkg"],
        )


if __name__ == "__main__":
    unittest.main()
