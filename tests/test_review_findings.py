"""Regression tests for the PR #119 Independent Review findings.

Each test names the finding it guards so that a future regression is attributable:

* F1  -- ``§4.3.30`` ``DERIVED`` internal contradiction (spec-level, guarded here);
* F3  -- an empty JSON object record must not be promoted to a Layer-1 rejection;
* F4  -- ``Decision 10A`` stable view must detect an in-place mutation that happens
         after a file was read but before acceptance concludes;
* F5  -- ``PN-1`` must not carry unapproved filename rejection policy;
* F6  -- an undecided **mandatory** Layer-1 gate must not yield ``ACCEPTED``.

All fixtures are SIMULATED.
"""

from __future__ import annotations

import json
import shutil
import unittest
import uuid
from pathlib import Path

from snapshot_loader import (
    DISPOSITION_ACCEPTED,
    DISPOSITION_REJECTED,
    TrustedInputBoundary,
    load_package,
)
from snapshot_loader import loader as loader_module
from snapshot_loader.constants import (
    MANDATORY_LAYER1_CHECKS,
    RECORD_META_NAMESPACE,
    V02_CANONICAL_RECORD_PROPERTIES,
)
from snapshot_loader.path_scope import validate_artifact_filename
from tests.helpers import (
    DatasetSpec,
    PackageSpec,
    build_package,
    encode_json,
    valid_package,
)

SCRATCH_ROOT = Path(__file__).resolve().parents[1] / "build" / "test-scratch"


class ReviewFindingTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = SCRATCH_ROOT / uuid.uuid4().hex
        self.boundary = self.workspace / "landing"
        self.boundary.mkdir(parents=True, exist_ok=True)
        self.addCleanup(shutil.rmtree, self.workspace, ignore_errors=True)

    def load(self, package_dir: Path):
        return load_package(
            package_dir, trusted_boundary=TrustedInputBoundary(root=self.boundary)
        )

    def build(self, spec: PackageSpec, *, name: str = "pkg"):
        return build_package(
            self.boundary / name, spec, boundary_root=self.boundary
        )


class F3EmptyRecordTests(ReviewFindingTestCase):
    """F3 -- empty object record is structurally valid at Layer 1."""

    def _record_report(self, record, *, name="pkg"):
        built = self.build(
            PackageSpec(datasets=[DatasetSpec(artifact="r.json", records=[record])]),
            name=name,
        )
        return self.load(built.root)

    def test_empty_object_record_is_accepted(self) -> None:
        report = self._record_report({})
        self.assertEqual(
            report.disposition,
            DISPOSITION_ACCEPTED,
            msg=(
                "an empty JSON object record carries no unknown property; rejecting it "
                "would promote a Layer-2 sufficiency concern into package rejection"
            ),
        )
        self.assertEqual(report.issues, ())

    def test_meta_only_record_is_accepted(self) -> None:
        report = self._record_report(
            {
                RECORD_META_NAMESPACE: {
                    "provenance_associations": [
                        {"observation": "plant_id", "evidence": ["SIM-EV-1"]}
                    ]
                }
            }
        )
        self.assertEqual(report.disposition, DISPOSITION_ACCEPTED)

    def test_empty_record_in_multi_record_dataset_is_accepted(self) -> None:
        built = self.build(
            PackageSpec(
                datasets=[
                    DatasetSpec(
                        artifact="r.json",
                        records=[
                            {"plant_id": "P1"},
                            {},
                            {"plant_id": "P2"},
                        ],
                    )
                ]
            )
        )
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_ACCEPTED)

    def test_empty_object_record_in_an_empty_dataset_is_not_required(self) -> None:
        # included + record_count = 0 remains valid independently of record content
        built = self.build(
            PackageSpec(
                datasets=[
                    DatasetSpec(role="Inventory Snapshot", artifact="i.json", records=[])
                ]
            )
        )
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_ACCEPTED)


class F4StableViewMutationTests(ReviewFindingTestCase):
    """F4 -- a post-read, pre-accept in-place mutation must be detected."""

    def test_manifest_mutation_after_read_is_detected(self) -> None:
        built = valid_package(self.boundary / "pkg", boundary_root=self.boundary)
        manifest_path = built.root / "manifest.json"
        original_read = loader_module.read_file_bytes
        state = {"mutated": False}

        def mutating_read(path):
            result = original_read(path)
            if (
                not state["mutated"]
                and Path(path).name == "manifest.json"
                and result is not None
            ):
                # Simulate an external writer changing the Manifest after it has
                # already been read into the accepted view.
                document = json.loads(manifest_path.read_text(encoding="utf-8"))
                document["package"]["completeness_state"] = "IN_PROGRESS"
                manifest_path.write_bytes(encode_json(document))
                state["mutated"] = True
            return result

        loader_module.read_file_bytes = mutating_read
        self.addCleanup(setattr, loader_module, "read_file_bytes", original_read)

        report = self.load(built.root)

        self.assertTrue(state["mutated"], "fixture did not mutate the manifest")
        self.assertNotEqual(
            report.disposition,
            DISPOSITION_ACCEPTED,
            msg="a manifest mutated after read must not yield ACCEPTED",
        )
        self.assertTrue(
            any(
                "changed between being read" in issue.detail
                and issue.location == "manifest.json"
                for issue in report.issues
            ),
            msg=f"expected a stable-view mutation issue, got {report.issues}",
        )

    def test_artifact_mutation_after_read_is_detected(self) -> None:
        built = valid_package(self.boundary / "pkg", boundary_root=self.boundary)
        artifact_path = built.root / "requirement.json"
        original_read = loader_module.read_file_bytes
        state = {"mutated": False}

        def mutating_read(path):
            result = original_read(path)
            if (
                not state["mutated"]
                and Path(path).name == "requirement.json"
                and result is not None
            ):
                artifact_path.write_bytes(encode_json([{"plant_id": "MUTATED"}]))
                state["mutated"] = True
            return result

        loader_module.read_file_bytes = mutating_read
        self.addCleanup(setattr, loader_module, "read_file_bytes", original_read)

        report = self.load(built.root)

        self.assertTrue(state["mutated"], "fixture did not mutate the artifact")
        self.assertNotEqual(report.disposition, DISPOSITION_ACCEPTED)

    def test_unchanged_package_still_reports_stable_view_passed(self) -> None:
        built = valid_package(self.boundary / "pkg", boundary_root=self.boundary)
        report = self.load(built.root)

        self.assertEqual(report.disposition, DISPOSITION_ACCEPTED)
        states = {check.name: check.state for check in report.collector.checks}
        self.assertEqual(states["package.acceptance_time_stable_view"], "passed")
        self.assertEqual(states["package.stable_view_all_files_re_read"], "passed")
        for name in ("manifest.json", "requirement.json"):
            self.assertEqual(states[f"package.stable_view_bytes:{name}"], "passed")


class F5PathScopePolicyTests(ReviewFindingTestCase):
    """F5 -- no unapproved filename rejection policy remains."""

    def test_no_unapproved_rejection_codes_exist(self) -> None:
        unapproved = {
            "TOO_LONG",
            "ILLEGAL_CHARACTER",
            "RESERVED_DEVICE_NAME",
            "TRAILING_DOT_OR_SPACE",
            "SURROUNDING_WHITESPACE",
        }
        observed: set[str] = set()
        samples = [
            "a" * 4000 + ".json",
            "con.json",
            'req"uirement.json',
            "requirement.json.",
            " requirement.json",
            "requirement.json ",
            "<>|?*.json",
            "nul.json",
        ]
        for sample in samples:
            rejection = validate_artifact_filename(sample)
            if rejection is not None:
                observed.add(rejection.code)
        self.assertEqual(
            observed & unapproved,
            set(),
            msg=f"unapproved filename policy still active: {observed & unapproved}",
        )

    def test_a_filename_the_host_cannot_represent_is_not_a_contract_violation(self) -> None:
        # ``<>|?*`` is not a registered PN-1 rule.  On a filesystem that rejects
        # such a name the artifact is simply absent/unreadable (IC-14); the loader
        # must not report an invented "illegal character" contract violation.
        self.assertIsNone(validate_artifact_filename("<>|?*.json"))

    def test_registered_rules_still_reject(self) -> None:
        expectations = {
            "sub/requirement.json": "PATH_SEPARATOR",
            "..\\requirement.json": "PATH_SEPARATOR",
            "file:///tmp/a.json": "URI_REFERENCE",
            "manifest.json": "RESERVED_FILENAME",
            "requirement.csv": "WRONG_EXTENSION",
            "": "EMPTY",
        }
        for sample, code in expectations.items():
            rejection = validate_artifact_filename(sample)
            self.assertIsNotNone(rejection, msg=f"{sample!r} should be rejected")
            assert rejection is not None
            self.assertEqual(rejection.code, code, msg=f"{sample!r}")


class F6MandatoryUndecidedTests(ReviewFindingTestCase):
    """F6 -- an undecided mandatory gate must fail closed, not accept."""

    def test_advisory_checks_are_not_mandatory(self) -> None:
        self.assertNotIn("artifacts.independent_target_identity", MANDATORY_LAYER1_CHECKS)
        self.assertNotIn("package.stable_root_identity", MANDATORY_LAYER1_CHECKS)

    def test_stable_view_gate_is_mandatory(self) -> None:
        self.assertIn("package.acceptance_time_stable_view", MANDATORY_LAYER1_CHECKS)

    def test_mandatory_registry_is_covered_by_emitted_checks(self) -> None:
        # Every mandatory name must actually be emitted by a clean acceptance run,
        # otherwise the registry could silently stop guarding a real gate.
        built = valid_package(self.boundary / "pkg", boundary_root=self.boundary)
        report = self.load(built.root)
        emitted = {check.name for check in report.collector.checks}
        missing = sorted(name for name in MANDATORY_LAYER1_CHECKS if name not in emitted)
        self.assertEqual(
            missing,
            [],
            msg=f"mandatory check name(s) never emitted: {missing}",
        )

    def test_accepted_never_carries_an_undecided_mandatory_check(self) -> None:
        built = valid_package(self.boundary / "pkg", boundary_root=self.boundary)
        report = self.load(built.root)
        self.assertEqual(report.disposition, DISPOSITION_ACCEPTED)
        self.assertEqual(report.undecided_mandatory_checks, ())

    def test_undecided_mandatory_forces_not_decidable(self) -> None:
        from snapshot_loader.issues import IssueCollector

        collector = IssueCollector()
        collector = collector.not_evaluable(
            "artifacts.record_count_consistency", "artifact bytes unavailable"
        )
        names = loader_module._undecided_mandatory_checks(collector)
        self.assertEqual(names, ("artifacts.record_count_consistency",))

    def test_undecided_advisory_does_not_force_rejection(self) -> None:
        from snapshot_loader.issues import IssueCollector

        collector = IssueCollector()
        collector = collector.not_evaluable(
            "artifacts.independent_target_identity", "no usable file identity"
        )
        self.assertEqual(loader_module._undecided_mandatory_checks(collector), ())

    def test_no_accepted_report_ever_carries_an_undecided_mandatory_check(self) -> None:
        # Drive a mandatory gate into ``not evaluable`` while leaving no collected
        # issue, so the *only* reason acceptance cannot be concluded is the
        # undecided mandatory gate.  The loader must then report a disposition that
        # does not claim acceptance and does not claim evaluability.
        built = valid_package(self.boundary / "pkg", boundary_root=self.boundary)
        original = loader_module._check_stable_view
        state = {"patched": False}

        def patched_stable_view(**kwargs):  # noqa: ANN003
            collector = original(**kwargs)
            if not state["patched"]:
                collector = collector.not_evaluable(
                    "package.acceptance_time_stable_view",
                    "synthetic: stable-view consistency could not be established",
                )
                state["patched"] = True
            return collector

        loader_module._check_stable_view = patched_stable_view
        self.addCleanup(setattr, loader_module, "_check_stable_view", original)

        report = self.load(built.root)

        self.assertTrue(state["patched"], "fixture did not force an undecided mandatory gate")
        self.assertEqual(report.issues, (), "fixture must not also produce a defect issue")
        self.assertNotEqual(
            report.disposition,
            DISPOSITION_ACCEPTED,
            msg="an undecided mandatory gate must not yield ACCEPTED",
        )
        self.assertFalse(
            report.evaluable,
            msg="an undecided mandatory gate must be reported as not decidable",
        )
        self.assertIn(
            "package.acceptance_time_stable_view",
            report.disposition_basis,
            msg="the basis must name the undecided mandatory gate",
        )
        self.assertIn(
            "package.acceptance_time_stable_view",
            [check.name for check in report.undecided_mandatory_checks],
        )


class F1DerivedSetConsistencyTests(ReviewFindingTestCase):
    """F1 -- the frozen set and its documentation must not contradict each other."""

    def test_registry_contains_exactly_the_enumerated_literals(self) -> None:
        contract = (
            Path(__file__).resolve().parents[1]
            / "docs"
            / "design"
            / "specs"
            / "data-integration"
            / "snapshot-import-contract.md"
        ).read_text(encoding="utf-8")
        for literal in V02_CANONICAL_RECORD_PROPERTIES:
            self.assertIn(
                f"\n{literal}\n",
                contract,
                msg=f"{literal!r} is registered in code but not enumerated in §4.3.30 B.1",
            )

    def test_derived_results_are_absent_from_the_set(self) -> None:
        for derived in ("BaseRequirement", "RecommendedPurchaseQty", "Classification"):
            self.assertNotIn(derived, V02_CANONICAL_RECORD_PROPERTIES)

    def test_contract_no_longer_claims_derived_is_represented(self) -> None:
        contract = (
            Path(__file__).resolve().parents[1]
            / "docs"
            / "design"
            / "specs"
            / "data-integration"
            / "snapshot-import-contract.md"
        ).read_text(encoding="utf-8")
        self.assertNotIn(
            "`POLICY_INPUT` ／ `DERIVED`），Layer 1 对这些类别不做语义合法性判断",
            contract,
            msg="the contradiction claiming DERIVED is represented must be gone",
        )
        self.assertIn("closed enumeration", contract)


if __name__ == "__main__":
    unittest.main()
