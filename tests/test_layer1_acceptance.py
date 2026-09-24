"""Layer-1 acceptance and rejection tests (Issue #118 acceptance criteria).

Every fixture is SIMULATED.  Expectations are derived from the canonical contract
text, not from the implementation: where a test asserts a disposition it also cites
the registered rule that requires it.
"""

from __future__ import annotations

import shutil
import unittest
import uuid
from pathlib import Path


from snapshot_loader import (  # noqa: E402
    DISPOSITION_ACCEPTED,
    DISPOSITION_REJECTED,
    TrustedInputBoundary,
    load_package,
)
from tests.helpers import (  # noqa: E402
    DatasetSpec,
    PackageSpec,
    build_package,
    encode_json,
    valid_package,
    write_file,
)

#: Scratch root for SIMULATED fixtures.  Kept inside the repository so that the suite
#: does not depend on a writable system temporary directory.
SCRATCH_ROOT = Path(__file__).resolve().parents[1] / "build" / "test-scratch"


class Layer1TestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = SCRATCH_ROOT / uuid.uuid4().hex
        self.boundary = self.workspace / "landing"
        self.boundary.mkdir(parents=True, exist_ok=True)
        self.addCleanup(shutil.rmtree, self.workspace, ignore_errors=True)

    def package_dir(self, name: str = "pkg") -> Path:
        return self.boundary / name

    def load(self, package_dir: Path):
        return load_package(
            package_dir, trusted_boundary=TrustedInputBoundary(root=self.boundary)
        )

    def build(self, spec: PackageSpec | None = None, *, name: str = "pkg"):
        built = build_package(
            self.package_dir(name),
            spec or PackageSpec(),
            boundary_root=self.boundary,
        )
        return built


class ValidPackageTests(Layer1TestCase):
    def test_valid_controlled_simulated_package_is_accepted(self) -> None:
        built = valid_package(self.package_dir(), boundary_root=self.boundary)
        report = self.load(built.root)

        self.assertEqual(report.disposition, DISPOSITION_ACCEPTED)
        self.assertTrue(report.evaluable)
        self.assertEqual(report.issues, ())
        self.assertIsNotNone(report.accepted_package)
        self.assertEqual(report.accepted_package.package_id, "SIMULATED-PKG-0001")
        self.assertEqual(report.accepted_package.contract_version, "v0.2")

    def test_included_empty_dataset_is_structurally_valid(self) -> None:
        # IC-4 / §4.3.25 D: included + record_count = 0 -> artifact REQUIRED, payload = []
        built = self.build(
            PackageSpec(
                datasets=[
                    DatasetSpec(
                        role="Inventory Snapshot",
                        artifact="inventory.json",
                        records=[],
                    )
                ]
            )
        )
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_ACCEPTED)

    def test_not_included_dataset_is_not_required(self) -> None:
        # §4.3.14 / IC-14: an absent, undeclared dataset is NOT a structural failure.
        built = valid_package(self.package_dir(), boundary_root=self.boundary)
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_ACCEPTED)
        self.assertEqual(
            sorted(path.name for path in built.root.glob("*.json")),
            ["manifest.json", "requirement.json"],
        )

    def test_empty_record_yields_meta_only_record(self) -> None:
        # §4.3.25 F / §4.3.28 E: records may carry only the reserved metadata namespace.
        built = self.build(
            PackageSpec(
                datasets=[
                    DatasetSpec(
                        role="Inventory Snapshot",
                        artifact="inventory.json",
                        records=[
                            {
                                "_meta": {
                                    "provenance_associations": [
                                        {
                                            "observation": "on_hand_qty",
                                            "evidence": ["SIMULATED-EVIDENCE-1"],
                                        }
                                    ]
                                },
                                "plant_id": "P1",
                                "on_hand_qty": "5",
                            }
                        ],
                    )
                ]
            )
        )
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_ACCEPTED)

    def test_multiple_datasets_with_distinct_roles_are_accepted(self) -> None:
        built = self.build(
            PackageSpec(
                datasets=[
                    DatasetSpec(
                        role="Production Requirement",
                        artifact="requirement.json",
                        records=[{"plant_id": "P1", "required_date": "2026-02-01"}],
                    ),
                    DatasetSpec(
                        role="Supplier Performance",
                        artifact="supplier_performance.json",
                        records=[
                            {
                                "supplier_id": "S1",
                                "PerformancePeriod": "2026-Q1",
                                "PerformanceUpdatedAt": "2026-01-05T08:00:00Z",
                                "DeliveryPerformance": "95",
                                "QualityPerformance": "98",
                            }
                        ],
                    ),
                ]
            )
        )
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_ACCEPTED)


class TrustedBoundaryTests(Layer1TestCase):
    def test_missing_trusted_boundary_is_not_evaluable_and_fails_closed(self) -> None:
        built = valid_package(self.package_dir(), boundary_root=self.boundary)
        report = load_package(
            built.root,
            trusted_boundary=TrustedInputBoundary(root=self.workspace / "does-not-exist"),
        )

        self.assertFalse(report.evaluable)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)
        self.assertIsNone(report.accepted_package)
        self.assertTrue(
            any(
                check.name == "trust_boundary.configured_and_verifiable"
                and check.state == "not_evaluable"
                for check in report.collector.checks
            )
        )

    def test_package_outside_boundary_is_not_evaluable(self) -> None:
        outside = self.workspace / "outside" / "pkg"
        built = build_package(outside, PackageSpec(), boundary_root=self.boundary)
        report = self.load(built.root)

        self.assertFalse(report.evaluable)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_deeply_nested_package_is_not_a_direct_child(self) -> None:
        nested = self.boundary / "group" / "pkg"
        built = build_package(nested, PackageSpec(), boundary_root=self.boundary)
        report = self.load(built.root)
        self.assertFalse(report.evaluable)

    def test_symlinked_package_dir_is_fail_closed(self) -> None:
        built = valid_package(self.package_dir("real"), boundary_root=self.boundary)
        link = self.boundary / "linked"
        try:
            link.symlink_to(built.root, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is not permitted in this environment")

        report = self.load(link)
        self.assertFalse(report.evaluable)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)


class ManifestRejectionTests(Layer1TestCase):
    def test_missing_manifest_is_rejected_with_not_evaluable_downstream(self) -> None:
        root = self.package_dir()
        root.mkdir(parents=True, exist_ok=True)
        report = self.load(root)

        self.assertEqual(report.disposition, DISPOSITION_REJECTED)
        self.assertTrue(report.evaluable)
        self.assertEqual(report.issues[0].location, "manifest.json")
        not_evaluable = {
            check.name
            for check in report.collector.checks
            if check.state == "not_evaluable"
        }
        self.assertIn("artifacts.record_count_consistency", not_evaluable)

    def test_malformed_manifest_is_rejected(self) -> None:
        built = self.build(PackageSpec(manifest_bytes=b'{"package": '))
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)
        self.assertTrue(
            any("strict JSON" in issue.detail for issue in report.issues)
        )

    def test_duplicate_manifest_key_is_rejected(self) -> None:
        raw = (
            b'{"package": {"snapshot_package_id": "A", "snapshot_package_id": "B", '
            b'"contract_version": "v0.2"}, "datasets": []}'
        )
        built = self.build(PackageSpec(manifest_bytes=raw))
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)
        self.assertTrue(any("duplicate object key" in issue.detail for issue in report.issues))

    def test_manifest_with_utf8_bom_is_rejected(self) -> None:
        payload = b"\xef\xbb\xbf" + encode_json(
            {"package": {"snapshot_package_id": "A", "contract_version": "v0.2"}, "datasets": []}
        )
        built = self.build(PackageSpec(manifest_bytes=payload))
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)
        self.assertTrue(any("BOM" in issue.detail for issue in report.issues))

    def test_manifest_with_nan_is_rejected(self) -> None:
        raw = b'{"package": {"snapshot_package_id": "A", "contract_version": "v0.2"}, "datasets": [], "x": NaN}'
        built = self.build(PackageSpec(manifest_bytes=raw))
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_unsupported_contract_version_is_rejected_without_silent_interpretation(self) -> None:
        built = self.build(PackageSpec(contract_version="v0.3"))
        report = self.load(built.root)

        self.assertEqual(report.disposition, DISPOSITION_REJECTED)
        self.assertTrue(any("VC-1" in issue.detail for issue in report.issues))
        # Version dispatch precedes unknown-content validation: the known member set is
        # never applied for an unsupported version.
        self.assertTrue(
            any(
                check.name == "artifacts.record_count_consistency"
                and check.state == "not_evaluable"
                for check in report.collector.checks
            )
        )

    def test_missing_package_identity_is_rejected(self) -> None:
        built = self.build(PackageSpec(package_id=""))
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_missing_package_block_is_rejected(self) -> None:
        built = self.build(PackageSpec(omit_package_block=True))
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_unknown_manifest_property_is_rejected(self) -> None:
        built = self.build(PackageSpec(extra_manifest_properties={"metadata": {}}))
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)
        self.assertTrue(any("UX-A reject" in issue.detail for issue in report.issues))

    def test_unknown_package_scoped_property_is_rejected(self) -> None:
        built = self.build(
            PackageSpec(extra_package_properties={"generated_by": "simulator"})
        )
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_unknown_dataset_entry_property_is_rejected(self) -> None:
        built = self.build(
            PackageSpec(
                datasets=[
                    DatasetSpec(
                        records=[{"plant_id": "P1"}],
                        extra_entry_properties={"schema_version": "1"},
                    )
                ]
            )
        )
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_datasets_must_be_an_array(self) -> None:
        built = self.build(PackageSpec(extra_manifest_properties={"datasets": {}}), name="pkg2")
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_dataset_entry_must_be_an_object(self) -> None:
        built = self.build(
            PackageSpec(extra_manifest_properties={"datasets": ["requirement.json"]}),
            name="pkg3",
        )
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)


class DatasetEntryRejectionTests(Layer1TestCase):
    def _reject(self, dataset: DatasetSpec):
        built = self.build(PackageSpec(datasets=[dataset]))
        return self.load(built.root)

    def test_duplicate_logical_dataset_role_is_rejected(self) -> None:
        built = self.build(
            PackageSpec(
                datasets=[
                    DatasetSpec(
                        role="Inventory Snapshot",
                        artifact="inventory_a.json",
                        records=[{"on_hand_qty": "1"}],
                    ),
                    DatasetSpec(
                        role="Inventory Snapshot",
                        artifact="inventory_b.json",
                        records=[{"on_hand_qty": "2"}],
                    ),
                ]
            )
        )
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)
        self.assertTrue(any("duplicate logical dataset role" in issue.detail for issue in report.issues))

    def test_two_roles_referencing_the_same_artifact_is_rejected(self) -> None:
        # IC-1: each included logical dataset needs an INDEPENDENT artifact.
        built = self.build(
            PackageSpec(
                datasets=[
                    DatasetSpec(role="Role A", artifact="shared.json", records=[{"plant_id": "P1"}]),
                    DatasetSpec(
                        role="Role B",
                        artifact="shared.json",
                        records=[{"plant_id": "P1"}],
                        written_filename="shared.json",
                    ),
                ]
            )
        )
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_role_must_be_a_non_empty_string(self) -> None:
        report = self._reject(DatasetSpec(role="", artifact="r.json"))
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_missing_record_count_is_rejected(self) -> None:
        report = self._reject(DatasetSpec(artifact="r.json", omit_record_count=True))
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_negative_record_count_is_rejected(self) -> None:
        report = self._reject(DatasetSpec(artifact="r.json", record_count=-1))
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_missing_integrity_evidence_is_rejected(self) -> None:
        report = self._reject(DatasetSpec(artifact="r.json", omit_integrity=True))
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_malformed_integrity_evidence_is_rejected(self) -> None:
        for bad in ("ABC", "z" * 64, "a" * 63, "A" * 64, 1234, "", None):
            with self.subTest(integrity=bad):
                built = self.build(
                    PackageSpec(
                        datasets=[
                            DatasetSpec(
                                artifact="r.json",
                                records=[{"plant_id": "P1"}],
                                integrity_evidence=bad,  # type: ignore[arg-type]
                                omit_integrity=bad is None,
                            )
                        ]
                    ),
                    name=f"pkg-{abs(hash(str(bad)))}",
                )
                report = self.load(built.root)
                self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_role_absence_does_not_require_the_role_to_be_in_the_illustrative_list(self) -> None:
        # §4.3.30 D: an unlisted role literal is NOT itself unknown content.
        built = self.build(
            PackageSpec(
                datasets=[
                    DatasetSpec(
                        role="A Role That Is Not In The Illustrative List",
                        artifact="r.json",
                        records=[{"plant_id": "P1"}],
                    )
                ]
            )
        )
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_ACCEPTED)


class ArtifactReferenceTests(Layer1TestCase):
    def _reference(self, artifact: str):
        built = self.build(
            PackageSpec(
                datasets=[
                    DatasetSpec(
                        artifact=artifact,
                        records=[{"plant_id": "P1"}],
                        written_filename=Path(artifact).name or "x.json",
                    )
                ]
            )
        )
        return self.load(built.root)

    def test_path_separator_reference_is_rejected(self) -> None:
        report = self._reference("sub/requirement.json")
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)
        self.assertTrue(any("PATH_SEPARATOR" in issue.detail for issue in report.issues))

    def test_backslash_reference_is_rejected(self) -> None:
        built = self.build(
            PackageSpec(
                datasets=[
                    DatasetSpec(artifact="sub\\requirement.json", records=[{"plant_id": "P1"}])
                ]
            )
        )
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_dot_dot_reference_is_rejected(self) -> None:
        report = self._reference("../requirements.json")
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_absolute_reference_is_rejected(self) -> None:
        absolute = str(self.workspace / "outside.json")
        write_file(Path(absolute), encode_json([{"plant_id": "P1"}]))
        built = self.build(
            PackageSpec(
                datasets=[
                    DatasetSpec(
                        artifact=absolute,
                        records=[{"plant_id": "P1"}],
                        written_filename="ignored.json",
                    )
                ]
            )
        )
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_uri_reference_is_rejected(self) -> None:
        report = self._reference("file:///tmp/requirements.json")
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_manifest_filename_is_reserved(self) -> None:
        report = self._reference("manifest.json")
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_non_json_extension_is_rejected(self) -> None:
        built = self.build(
            PackageSpec(
                datasets=[
                    DatasetSpec(
                        artifact="requirements.csv",
                        records=[{"plant_id": "P1"}],
                        written_filename="requirements.csv",
                    )
                ]
            )
        )
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_symlinked_artifact_is_rejected(self) -> None:
        built = valid_package(self.package_dir(), boundary_root=self.boundary)
        real = built.root / "requirement.json"
        moved = built.root.parent / "moved-requirement.json"
        moved.write_bytes(real.read_bytes())
        real.unlink()
        try:
            real.symlink_to(moved)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is not permitted in this environment")

        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_artifact_outside_package_boundary_is_rejected(self) -> None:
        outside = self.workspace / "elsewhere.json"
        write_file(outside, encode_json([{"plant_id": "P1"}]))
        built = self.build(
            PackageSpec(
                datasets=[
                    DatasetSpec(
                        artifact=outside.name,
                        records=[{"plant_id": "P1"}],
                        external_target=outside,
                    )
                ]
            )
        )
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)
        self.assertTrue(
            any(
                "absent" in issue.detail or "outside the package boundary" in issue.detail
                for issue in report.issues
            )
        )


class ArtifactIntegrityTests(Layer1TestCase):
    def test_missing_declared_artifact_is_a_structural_inconsistency(self) -> None:
        # IC-14 / §4.3.12 A: declared included + artifact missing = structural failure.
        built = self.build(
            PackageSpec(
                datasets=[DatasetSpec(artifact="inventory.json", records=[{"on_hand_qty": "1"}])]
            )
        )
        (built.root / "inventory.json").unlink()
        report = self.load(built.root)

        self.assertEqual(report.disposition, DISPOSITION_REJECTED)
        self.assertTrue(any(issue.category == "PACKAGE_STRUCTURE" for issue in report.issues))
        self.assertTrue(all(issue.reason == "STRUCTURAL_INCONSISTENCY" for issue in report.issues))

    def test_unreadable_artifact_is_rejected(self) -> None:
        built = valid_package(self.package_dir(), boundary_root=self.boundary)
        target = built.root / "requirement.json"
        directory = built.root / "requirement.json.tmp"
        target.rename(directory)  # a directory where a file is declared
        target.mkdir()
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_integrity_mismatch_is_rejected(self) -> None:
        built = self.build(
            PackageSpec(
                datasets=[
                    DatasetSpec(
                        artifact="r.json",
                        records=[{"plant_id": "P1"}],
                        integrity_evidence="0" * 64,
                    )
                ]
            )
        )
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)
        self.assertTrue(
            any("does not match the SHA-256 digest" in issue.detail for issue in report.issues)
        )

    def test_raw_byte_integrity_is_not_json_canonicalised(self) -> None:
        # IG-raw: digest covers exact raw bytes, so a whitespace-only reformat breaks it.
        built = valid_package(self.package_dir(), boundary_root=self.boundary)
        target = built.root / "requirement.json"
        payload = target.read_bytes()
        target.write_bytes(payload + b"\n")
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)


class UnreferencedContentTests(Layer1TestCase):
    def test_unreferenced_root_level_json_artifact_is_rejected(self) -> None:
        built = self.build(
            PackageSpec(extra_root_files={"extra.json": encode_json([{"plant_id": "P1"}])})
        )
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)
        self.assertTrue(
            any("unreferenced root-level JSON artifact" in issue.detail for issue in report.issues)
        )

    def test_nested_directory_is_rejected(self) -> None:
        built = self.build(
            PackageSpec(extra_root_dirs={"nested": {"data.json": encode_json([])}})
        )
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)
        self.assertTrue(any("nested directories" in issue.detail for issue in report.issues))

    def test_undeclared_non_json_root_entry_is_rejected(self) -> None:
        built = self.build(PackageSpec(extra_root_files={"notes.txt": b"simulated"}))
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)


class RecordLevelRejectionTests(Layer1TestCase):
    def _records(self, records, *, name="pkg"):
        built = self.build(
            PackageSpec(
                datasets=[
                    DatasetSpec(artifact="r.json", records=records)
                ]
            ),
            name=name,
        )
        return self.load(built.root)

    def test_unknown_canonical_record_property_is_rejected(self) -> None:
        report = self._records([{"plant_id": "P1", "unknown_field": "x"}])
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)
        self.assertTrue(
            any("unknown canonical record property" in issue.detail for issue in report.issues)
        )

    def test_snake_case_invention_of_runtime_context_is_rejected(self) -> None:
        # analysis_run_id IS in the frozen set; an invented variant is not.
        report = self._records([{"plant_id": "P1", "analysis_run": "R1"}])
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_registered_analysis_run_id_and_inbound_status_are_known_properties(self) -> None:
        report = self._records(
            [
                {
                    "plant_id": "P1",
                    "analysis_run_id": "RUN-1",
                    "inbound_status": "CONFIRMED",
                    "ordered_qty": "10",
                    "received_qty": "0",
                    "effective_arrival_date": "2026-02-01",
                }
            ]
        )
        self.assertEqual(report.disposition, DISPOSITION_ACCEPTED)

    def test_derived_result_property_is_rejected(self) -> None:
        # §4.2.10 derived results are not canonical record properties of a snapshot.
        report = self._records([{"plant_id": "P1", "RecommendedPurchaseQty": "5"}])
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_effective_demand_context_is_rejected(self) -> None:
        report = self._records([{"plant_id": "P1", "effective demand context": "x"}])
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_snapshot_package_id_is_not_a_record_property(self) -> None:
        report = self._records([{"plant_id": "P1", "snapshot_package_id": "PKG-1"}])
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_record_must_be_an_object(self) -> None:
        report = self._records([["P1", "M1"]])
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)
        self.assertTrue(any("must be a JSON object" in issue.detail for issue in report.issues))

    def test_records_may_not_be_positional_arrays_of_values(self) -> None:
        report = self._records(["P1"])
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_artifact_top_level_must_be_a_bare_record_array(self) -> None:
        built = self.build(
            PackageSpec(
                datasets=[
                    DatasetSpec(artifact="r.json", artifact_bytes=encode_json({"records": []}))
                ]
            )
        )
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)
        self.assertTrue(any("bare record array" in issue.detail for issue in report.issues))

    def test_duplicate_record_key_is_rejected(self) -> None:
        built = self.build(
            PackageSpec(
                datasets=[
                    DatasetSpec(
                        artifact="r.json",
                        artifact_bytes=b'[{"plant_id": "P1", "plant_id": "P2"}]',
                    )
                ]
            )
        )
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_record_count_mismatch_is_rejected(self) -> None:
        built = self.build(
            PackageSpec(
                datasets=[
                    DatasetSpec(
                        artifact="r.json",
                        records=[{"plant_id": "P1"}, {"plant_id": "P2"}],
                        record_count=5,
                    )
                ]
            )
        )
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)
        self.assertTrue(
            any("does not match the artifact record count" in issue.detail for issue in report.issues)
        )

    def test_included_empty_record_count_with_non_empty_payload_is_rejected(self) -> None:
        built = self.build(
            PackageSpec(
                datasets=[
                    DatasetSpec(
                        artifact="r.json",
                        records=[{"plant_id": "P1"}],
                        record_count=0,
                    )
                ]
            )
        )
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_layer_two_defects_are_not_promoted_to_package_rejection(self) -> None:
        # Requiredness, logical type, range, status vocabulary, applicability and
        # semantic resolution belong to Layer 2-4 (§4.4.2, IC-17).  A record whose
        # values are absent or semantically odd must still be structurally acceptable.
        report = self._records(
            [
                {
                    "plant_id": "P1",
                    "ProductionQty": "not-a-number",
                    "required_date": "01/02/2026",
                    "inventory_status": "NOT_A_DEFINED_STATUS",
                    "loss_rate": "42",
                }
            ]
        )
        self.assertEqual(report.disposition, DISPOSITION_ACCEPTED)


class MetaNamespaceTests(Layer1TestCase):
    def _record(self, record, *, name="pkg"):
        built = self.build(
            PackageSpec(datasets=[DatasetSpec(artifact="r.json", records=[record])]),
            name=name,
        )
        return self.load(built.root)

    def test_unknown_meta_member_is_rejected(self) -> None:
        report = self._record({"plant_id": "P1", "_meta": {"source_system": "ERP"}})
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)
        self.assertTrue(any('unknown direct member under "_meta"' in issue.detail for issue in report.issues))

    def test_unknown_association_member_is_rejected(self) -> None:
        report = self._record(
            {
                "plant_id": "P1",
                "_meta": {
                    "provenance_associations": [
                        {"observation": "plant_id", "evidence": ["E1"], "rule": "R1"}
                    ]
                },
            }
        )
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_mapping_basis_is_optional(self) -> None:
        report = self._record(
            {
                "plant_id": "P1",
                "_meta": {"provenance_associations": [{"observation": "plant_id", "evidence": ["E1"]}]},
            }
        )
        self.assertEqual(report.disposition, DISPOSITION_ACCEPTED)

    def test_mapping_basis_when_present_must_be_a_string(self) -> None:
        report = self._record(
            {
                "plant_id": "P1",
                "_meta": {
                    "provenance_associations": [
                        {"observation": "plant_id", "evidence": ["E1"], "mapping_basis": 7}
                    ]
                },
            }
        )
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_observation_must_reference_a_registered_property(self) -> None:
        report = self._record(
            {
                "plant_id": "P1",
                "_meta": {"provenance_associations": [{"observation": "made_up", "evidence": ["E1"]}]},
            }
        )
        self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_evidence_must_be_a_non_empty_array_of_strings(self) -> None:
        for evidence in ([], "", [7], ["ok", 7]):
            with self.subTest(evidence=evidence):
                report = self._record(
                    {
                        "plant_id": "P1",
                        "_meta": {
                            "provenance_associations": [
                                {"observation": "plant_id", "evidence": evidence}
                            ]
                        },
                    },
                    name=f"pkg-{abs(hash(str(evidence)))}",
                )
                self.assertEqual(report.disposition, DISPOSITION_REJECTED)

    def test_multiple_evidence_locators_are_allowed(self) -> None:
        report = self._record(
            {
                "plant_id": "P1",
                "_meta": {
                    "provenance_associations": [
                        {"observation": "plant_id", "evidence": ["E1", "E2"]}
                    ]
                },
            }
        )
        self.assertEqual(report.disposition, DISPOSITION_ACCEPTED)


class FailureReportingTests(Layer1TestCase):
    def test_collect_all_reachable_defects(self) -> None:
        built = self.build(
            PackageSpec(
                datasets=[
                    DatasetSpec(
                        role="Production Requirement",
                        artifact="a.json",
                        records=[{"plant_id": "P1", "unknown_field": "x"}],
                        integrity_evidence="0" * 64,
                    ),
                    DatasetSpec(
                        role="Inventory Snapshot",
                        artifact="b.json",
                        records=[{"plant_id": "P2"}],
                        record_count=9,
                    ),
                ]
            )
        )
        report = self.load(built.root)

        self.assertEqual(report.disposition, DISPOSITION_REJECTED)
        locations = {issue.location for issue in report.issues}
        # integrity mismatch (a), unknown record property (a), record_count (b)
        self.assertTrue(any("integrity_evidence" in location for location in locations))
        self.assertTrue(any("unknown_field" in location for location in locations))
        self.assertTrue(any("record_count" in location for location in locations))
        # collect-all: all three independent defects are reported together.
        self.assertGreaterEqual(len(report.issues), 3)

    def test_reporting_is_deterministically_ordered(self) -> None:
        spec = PackageSpec(
            datasets=[
                DatasetSpec(
                    artifact="a.json",
                    records=[{"plant_id": "P1", "zzz": "1", "aaa": "2"}],
                )
            ]
        )
        first = self.load(self.build(spec, name="pkg-a").root)
        second = self.load(self.build(spec, name="pkg-b").root)

        self.assertEqual(
            [issue.sort_key() for issue in first.issues],
            [issue.sort_key() for issue in second.issues],
        )

    def test_unsupported_version_reports_downstream_as_not_evaluable_not_passed(self) -> None:
        built = self.build(PackageSpec(contract_version="v9"))
        report = self.load(built.root)
        states = {
            check.name: check.state
            for check in report.collector.checks
        }
        self.assertEqual(states.get("artifacts.record_count_consistency"), "not_evaluable")
        self.assertNotEqual(states.get("artifacts.record_count_consistency"), "passed")
        self.assertEqual(states.get("manifest.contract_version_supported"), "failed")

    def test_issues_use_only_the_inherited_taxonomy(self) -> None:
        built = self.build(PackageSpec(contract_version="nope"))
        report = self.load(built.root)
        for issue in report.issues:
            self.assertEqual(issue.category, "PACKAGE_STRUCTURE")
            self.assertEqual(issue.reason, "STRUCTURAL_INCONSISTENCY")
            self.assertEqual(issue.layer, 1)

    def test_report_renders_human_readable_text(self) -> None:
        built = self.build(PackageSpec(contract_version="nope"))
        report = self.load(built.root)
        text = report.render_text()
        self.assertIn("disposition", text)
        self.assertIn("PACKAGE_STRUCTURE", text)


if __name__ == "__main__":
    unittest.main()
