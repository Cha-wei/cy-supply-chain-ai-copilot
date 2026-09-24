"""Trusted-reuse re-verification and post-accept mutation tests.

Registered behaviour: ``§4.3.28`` C.2 ``Decision 10A`` (acceptance-time stable view),
C.3 ``Decision 10B`` ``MG-2`` (re-verify required integrity before trusted reuse;
mutation or unverifiable integrity -> ``UNUSABLE``), ``§4.3.5``/``IC-12``
(an accepted package is immutable).
"""

from __future__ import annotations

import json
import shutil
import unittest
import uuid
from pathlib import Path


from snapshot_loader import (  # noqa: E402
    DISPOSITION_ACCEPTED,
    DISPOSITION_REJECTED,
    DISPOSITION_UNUSABLE,
    TrustedInputBoundary,
    load_package,
)
from tests.helpers import (  # noqa: E402
    DatasetSpec,
    PackageSpec,
    build_package,
    encode_json,
    sha256_hex,
    valid_package,
)

SCRATCH_ROOT = Path(__file__).resolve().parents[1] / "build" / "test-scratch"


class TrustedReuseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = SCRATCH_ROOT / uuid.uuid4().hex
        self.boundary = self.workspace / "landing"
        self.boundary.mkdir(parents=True, exist_ok=True)
        self.addCleanup(shutil.rmtree, self.workspace, ignore_errors=True)

    def load(self, package_dir: Path):
        return load_package(
            package_dir, trusted_boundary=TrustedInputBoundary(root=self.boundary)
        )

    def accepted(self, package_dir: Path):
        report = self.load(package_dir)
        self.assertEqual(report.disposition, DISPOSITION_ACCEPTED)
        assert report.accepted_package is not None
        return report


class ReuseVerdictTests(TrustedReuseTestCase):
    def test_unchanged_package_reverifies_cleanly(self) -> None:
        built = valid_package(self.boundary / "pkg", boundary_root=self.boundary)
        report = self.accepted(built.root)

        verdict = report.accepted_package.reverify()  # type: ignore[union-attr]
        self.assertTrue(verdict.reusable)
        self.assertEqual(verdict.content_view_digest, report.content_view.digest)  # type: ignore[union-attr]

    def test_artifact_mutation_makes_the_package_unusable(self) -> None:
        built = valid_package(self.boundary / "pkg", boundary_root=self.boundary)
        report = self.accepted(built.root)

        target = built.root / "requirement.json"
        payload = json.loads(target.read_text(encoding="utf-8"))
        payload[0]["ProductionQty"] = "999"
        target.write_bytes(encode_json(payload))

        verdict = report.accepted_package.reverify()  # type: ignore[union-attr]
        self.assertFalse(verdict.reusable)
        self.assertEqual(verdict.disposition, DISPOSITION_UNUSABLE)
        self.assertTrue(
            any("digest changed after acceptance" in issue.detail for issue in verdict.collector.issues)
        )

    def test_manifest_mutation_makes_the_package_unusable(self) -> None:
        built = valid_package(self.boundary / "pkg", boundary_root=self.boundary)
        report = self.accepted(built.root)

        manifest = json.loads(built.manifest_path.read_text(encoding="utf-8"))
        manifest["package"]["completeness_state"] = "IN_PROGRESS"
        built.manifest_path.write_bytes(encode_json(manifest))

        verdict = report.accepted_package.reverify()  # type: ignore[union-attr]
        self.assertFalse(verdict.reusable)
        self.assertEqual(verdict.disposition, DISPOSITION_UNUSABLE)

    def test_deleted_artifact_makes_the_package_unusable(self) -> None:
        built = valid_package(self.boundary / "pkg", boundary_root=self.boundary)
        report = self.accepted(built.root)

        (built.root / "requirement.json").unlink()
        verdict = report.accepted_package.reverify()  # type: ignore[union-attr]
        self.assertFalse(verdict.reusable)
        self.assertEqual(verdict.disposition, DISPOSITION_UNUSABLE)

    def test_removed_package_directory_makes_the_package_unusable(self) -> None:
        built = valid_package(self.boundary / "pkg", boundary_root=self.boundary)
        report = self.accepted(built.root)

        shutil.rmtree(built.root)
        verdict = report.accepted_package.reverify()  # type: ignore[union-attr]
        self.assertFalse(verdict.reusable)
        self.assertEqual(verdict.disposition, DISPOSITION_UNUSABLE)

    def test_added_artifact_makes_the_package_unusable(self) -> None:
        built = valid_package(self.boundary / "pkg", boundary_root=self.boundary)
        report = self.accepted(built.root)

        (built.root / "extra.json").write_bytes(encode_json([{"plant_id": "P9"}]))
        verdict = report.accepted_package.reverify()  # type: ignore[union-attr]
        self.assertFalse(verdict.reusable)
        self.assertEqual(verdict.disposition, DISPOSITION_UNUSABLE)

    def test_declared_integrity_is_rechecked_against_current_bytes(self) -> None:
        dataset = DatasetSpec(
            role="Inventory Snapshot",
            artifact="inventory.json",
            records=[{"plant_id": "P1", "on_hand_qty": "3"}],
        )
        built = build_package(
            self.boundary / "pkg", PackageSpec(datasets=[dataset]), boundary_root=self.boundary
        )
        report = self.accepted(built.root)

        # Rewrite bytes and repair the declared digest so that only the accepted-view
        # binding can detect the change.
        target = built.root / "inventory.json"
        replacement = encode_json([{"plant_id": "P1", "on_hand_qty": "4"}])
        target.write_bytes(replacement)
        manifest = json.loads(built.manifest_path.read_text(encoding="utf-8"))
        manifest["datasets"][0]["integrity_evidence"] = sha256_hex(replacement)
        built.manifest_path.write_bytes(encode_json(manifest))

        verdict = report.accepted_package.reverify()  # type: ignore[union-attr]
        self.assertFalse(verdict.reusable)
        self.assertEqual(verdict.disposition, DISPOSITION_UNUSABLE)

    def test_reverification_is_not_confused_by_an_unrelated_rejected_package(self) -> None:
        accepted = valid_package(self.boundary / "pkg", boundary_root=self.boundary)
        report = self.accepted(accepted.root)

        build_package(
            self.boundary / "other",
            PackageSpec(contract_version="nope"),
            boundary_root=self.boundary,
        )
        other = self.load(self.boundary / "other")
        self.assertEqual(other.disposition, DISPOSITION_REJECTED)
        self.assertIsNone(other.accepted_package)

        verdict = report.accepted_package.reverify()  # type: ignore[union-attr]
        self.assertTrue(verdict.reusable)


class CrossPackageIsolationTests(TrustedReuseTestCase):
    def test_each_analysis_input_binds_to_exactly_one_accepted_package(self) -> None:
        first = valid_package(
            self.boundary / "pkg-one", boundary_root=self.boundary, package_id="SIMULATED-PKG-ONE"
        )
        second = build_package(
            self.boundary / "pkg-two",
            PackageSpec(
                package_id="SIMULATED-PKG-TWO",
                datasets=[
                    DatasetSpec(
                        role="Inventory Snapshot",
                        artifact="inventory.json",
                        records=[{"plant_id": "P1", "on_hand_qty": "7"}],
                    )
                ],
            ),
            boundary_root=self.boundary,
        )

        first_report = self.load(first.root)
        second_report = self.load(second.root)

        self.assertEqual(first_report.disposition, DISPOSITION_ACCEPTED)
        self.assertEqual(second_report.disposition, DISPOSITION_ACCEPTED)
        self.assertNotEqual(
            first_report.content_view.digest, second_report.content_view.digest
        )
        self.assertNotEqual(
            first_report.accepted_package.package_id,  # type: ignore[union-attr]
            second_report.accepted_package.package_id,  # type: ignore[union-attr]
        )

    def test_accepted_package_has_no_mutating_operation(self) -> None:
        built = valid_package(self.boundary / "pkg", boundary_root=self.boundary)
        report = self.accepted(built.root)
        accepted = report.accepted_package
        assert accepted is not None

        public = {name for name in dir(accepted) if not name.startswith("_")}
        self.assertEqual(
            public,
            {
                "boundary_root",
                "content_view",
                "content_view_digest",
                "contract_version",
                "declared_integrity",
                "package_id",
                "package_path",
                "reverify",
                "to_dict",
            },
        )


if __name__ == "__main__":
    unittest.main()
