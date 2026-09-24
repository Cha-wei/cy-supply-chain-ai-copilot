"""Layer-2 Canonical Evidence Validation tests (Issue #122, narrowed subset).

Coverage required by Issue #122:

* valid values;
* malformed representation;
* invalid logical type;
* out-of-range;
* invalid approved status;
* identifier empty / malformed;
* valid zero;
* valid but ineligible;
* omission deferral;
* JSON ``null`` deferral (and never ``INVALID_TYPE``);
* deterministic ordering;
* collect-all reachable defects;
* prerequisite not-evaluable;
* accepted-view mutation / ``UNUSABLE``;
* no Layer-3 / Layer-4 behaviour.

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
    DISPOSITION_UNUSABLE,
    Layer2Report,
    TrustedInputBoundary,
    load_package,
    validate_layer2,
)
from snapshot_loader import layer2 as layer2_module
from snapshot_loader.constants import (
    CATEGORY_FIELD_VALUE,
    CATEGORY_IDENTITY_RESOLUTION,
    LAYER_2,
    LAYER2_FIELD_RULE_BY_NAME,
    LAYER2_REGISTRY,
    MANDATORY_LAYER1_CHECKS,
    REASON_INVALID_DEFINED_STATUS,
    REASON_INVALID_TYPE,
    REASON_OUT_OF_DEFINED_RANGE,
    REASON_UNRESOLVED_IDENTITY,
    V02_CANONICAL_RECORD_PROPERTIES,
)
from snapshot_loader.path_scope import validate_artifact_filename
from tests.helpers import DatasetSpec, PackageSpec, build_package, encode_json, valid_package

SCRATCH_ROOT = Path(__file__).resolve().parents[1] / "build" / "test-scratch"

#: A fully valid SIMULATED record covering every registered field with a compliant
#: non-null value.  Used as the baseline for single-field mutation tests.
VALID_RECORD: dict[str, object] = {
    "plant_id": "P1",
    "material_code": "M1",
    "supplier_id": "S1",
    "analysis_run_id": "RUN-1",
    "AnalysisDate": "2026-02-01",
    "required_date": "2026-02-01",
    "ProductionQty": "10",
    "BOMComponentQty": "2",
    "loss_rate": "0.05",
    "inventory_status": "AVAILABLE",
    "on_hand_qty": "100",
    "inventory_snapshot_time": "2026-01-31T08:00:00Z",
    "SafetyStock": "5",
    "ordered_qty": "10",
    "received_qty": "0",
    "effective_arrival_date": "2026-01-20",
    "inbound_status": "CONFIRMED",
    "target_material_code": "M1",
    "substitute_material_code": "M2",
    "substitution_ratio": "1",
    "approval_status": "APPROVED",
    "AllocatedSubstituteQty": "0",
    "sourcing_status": "SOURCE-LOCAL-CODE",
    "standard_lead_time_days": "7",
    "PerformancePeriod": "SIM-2026-Q1",
    "PerformanceUpdatedAt": "2026-01-05T08:00:00+08:00",
    "DeliveryPerformance": "95",
    "QualityPerformance": "98",
    "RecommendationNeedDate": "2026-02-01",
    "ApplicableMOQ": "0",
}


class Layer2TestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = SCRATCH_ROOT / uuid.uuid4().hex
        self.boundary = self.workspace / "landing"
        self.boundary.mkdir(parents=True, exist_ok=True)
        self.addCleanup(shutil.rmtree, self.workspace, ignore_errors=True)

    def synthetic_accepted_package(self, payload: object, *, name: str = "synthetic"):
        """Build an ``AcceptedPackage`` directly from bytes.

        Layer 1 guarantees a bare record array of JSON objects, so a malformed carrier
        can never reach Layer 2 through the loader.  The guard is still exercised by
        constructing the accepted view directly, so the obligation is verified rather
        than skipped.
        """

        import hashlib

        from snapshot_loader.trust import AcceptedPackage, ContentView, FileView

        raw = encode_json(payload)
        manifest_raw = encode_json({"synthetic": True})
        directory = self.boundary / name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "manifest.json").write_bytes(manifest_raw)
        artifact_name = "r.json"
        (directory / artifact_name).write_bytes(raw)

        artifact_digest = hashlib.sha256(raw).hexdigest()
        manifest_digest = hashlib.sha256(manifest_raw).hexdigest()
        artifact_view = FileView(
            name=artifact_name,
            sha256=artifact_digest,
            size=len(raw),
            mtime_ns=0,
            identity=None,
        )
        manifest_view = FileView(
            name="manifest.json",
            sha256=manifest_digest,
            size=len(manifest_raw),
            mtime_ns=0,
            identity=None,
        )
        content_view = ContentView(
            package_path=str(directory),
            root_identity=None,
            files=(manifest_view, artifact_view),
            directory_listing=("manifest.json", artifact_name),
            digest=f"synthetic-{name}",
        )
        return AcceptedPackage(
            package_id="SIMULATED-SYNTHETIC",
            contract_version="v0.2",
            package_path=directory,
            boundary_root=self.boundary,
            content_view=content_view,
            declared_integrity=((artifact_name, artifact_digest),),
            accepted_records=(("Production Requirement", artifact_name, raw),),
        )

    def accepted(self, records: list[dict[str, object]], *, name: str = "pkg"):
        built = build_package(
            self.boundary / name,
            PackageSpec(
                datasets=[DatasetSpec(role="Production Requirement", artifact="r.json", records=records)]
            ),
            boundary_root=self.boundary,
        )
        report = load_package(
            built.root, trusted_boundary=TrustedInputBoundary(root=self.boundary)
        )
        self.assertEqual(report.disposition, DISPOSITION_ACCEPTED)
        assert report.accepted_package is not None
        return built, report.accepted_package

    def run_layer2(self, records: list[dict[str, object]], *, name: str = "pkg") -> Layer2Report:
        _, accepted = self.accepted(records, name=name)
        return validate_layer2(accepted)

    def single(self, **overrides: object) -> Layer2Report:
        record = dict(VALID_RECORD)
        record.update(overrides)
        return self.run_layer2([record])

    def reasons(self, report: Layer2Report) -> set[str]:
        return {issue.reason for issue in report.issues}

    def locations(self, report: Layer2Report) -> set[str]:
        return {issue.location for issue in report.issues}


class ValidValueTests(Layer2TestCase):
    def test_fully_valid_record_produces_no_issue(self) -> None:
        report = self.single()
        self.assertEqual(report.issues, ())
        self.assertTrue(report.accepted)
        self.assertTrue(report.reusable)
        self.assertEqual(report.disposition, DISPOSITION_ACCEPTED)

    def test_issue_layer_is_layer_2(self) -> None:
        report = self.single(ProductionQty="-1")
        self.assertTrue(report.issues)
        for issue in report.issues:
            self.assertEqual(issue.layer, LAYER_2)

    def test_registry_covers_the_frozen_v02_property_set(self) -> None:
        registered = {rule.name for rule in LAYER2_REGISTRY}
        self.assertEqual(registered, set(V02_CANONICAL_RECORD_PROPERTIES))

    def test_registry_uses_only_registered_logical_types(self) -> None:
        allowed = {
            "IDENTIFIER",
            "ANALYSIS_RUN_ID",
            "DATE",
            "TIMESTAMP",
            "DECIMAL_QUANTITY",
            "NON_NEGATIVE_QUANTITY",
            "RATIO",
            "PERCENTAGE",
            "STATUS",
            "TEXT_CONTEXT",
        }
        for rule in LAYER2_REGISTRY:
            self.assertIn(rule.logical_type, allowed, msg=rule.name)


class MalformedRepresentationTests(Layer2TestCase):
    def test_date_alternate_format_is_invalid_type(self) -> None:
        report = self.single(required_date="01/02/2026")
        self.assertIn(REASON_INVALID_TYPE, self.reasons(report))
        self.assertIn("r.json[0].required_date", self.locations(report))

    def test_date_impossible_calendar_value_is_not_a_layer2_rule(self) -> None:
        # ``C-3`` registers the YYYY-MM-DD *form* only.  No calendar-validity rule is
        # registered, so Layer 2 must not invent one (§4.4.42).
        report = self.single(required_date="2026-13-45")
        self.assertEqual(report.issues, ())

    def test_date_wrong_shape_is_invalid_type(self) -> None:
        report = self.single(required_date="2026-2-1")
        self.assertIn(REASON_INVALID_TYPE, self.reasons(report))

    def test_timestamp_without_offset_is_invalid_type(self) -> None:
        report = self.single(inventory_snapshot_time="2026-01-31T08:00:00")
        self.assertIn(REASON_INVALID_TYPE, self.reasons(report))

    def test_timestamp_with_offset_is_accepted(self) -> None:
        report = self.single(inventory_snapshot_time="2026-01-31T08:00:00+08:00")
        self.assertEqual(report.issues, ())

    def test_decimal_scientific_notation_is_invalid_type(self) -> None:
        report = self.single(ProductionQty="1e3")
        self.assertIn(REASON_INVALID_TYPE, self.reasons(report))

    def test_decimal_thousands_separator_is_invalid_type(self) -> None:
        report = self.single(ProductionQty="1,000")
        self.assertIn(REASON_INVALID_TYPE, self.reasons(report))

    def test_decimal_leading_zero_is_invalid_type(self) -> None:
        report = self.single(ProductionQty="007")
        self.assertIn(REASON_INVALID_TYPE, self.reasons(report))


class InvalidLogicalTypeTests(Layer2TestCase):
    def test_numeric_field_as_json_number_is_invalid_type(self) -> None:
        report = self.single(ProductionQty=10)
        self.assertIn(REASON_INVALID_TYPE, self.reasons(report))

    def test_numeric_field_as_boolean_is_invalid_type(self) -> None:
        report = self.single(SafetyStock=False)
        self.assertIn(REASON_INVALID_TYPE, self.reasons(report))

    def test_sentinel_string_is_invalid_type_not_missing(self) -> None:
        report = self.single(ApplicableMOQ="UNKNOWN")
        self.assertIn(REASON_INVALID_TYPE, self.reasons(report))
        self.assertNotIn("MISSING", self.reasons(report))

    def test_identifier_as_json_number_is_invalid_type(self) -> None:
        report = self.single(plant_id=1001)
        self.assertIn(REASON_INVALID_TYPE, self.reasons(report))

    def test_status_as_json_number_is_invalid_type(self) -> None:
        report = self.single(inventory_status=1)
        self.assertIn(REASON_INVALID_TYPE, self.reasons(report))


class RangeTests(Layer2TestCase):
    def test_negative_non_negative_quantity_is_out_of_range(self) -> None:
        report = self.single(SafetyStock="-10")
        self.assertIn(REASON_OUT_OF_DEFINED_RANGE, self.reasons(report))

    def test_loss_rate_at_one_is_out_of_range(self) -> None:
        report = self.single(loss_rate="1")
        self.assertIn(REASON_OUT_OF_DEFINED_RANGE, self.reasons(report))

    def test_loss_rate_negative_is_out_of_range(self) -> None:
        report = self.single(loss_rate="-0.1")
        self.assertIn(REASON_OUT_OF_DEFINED_RANGE, self.reasons(report))

    def test_loss_rate_just_below_one_is_accepted(self) -> None:
        report = self.single(loss_rate="0.99")
        self.assertEqual(report.issues, ())

    def test_percentage_above_100_is_out_of_range(self) -> None:
        report = self.single(DeliveryPerformance="101")
        self.assertIn(REASON_OUT_OF_DEFINED_RANGE, self.reasons(report))

    def test_percentage_below_zero_is_out_of_range(self) -> None:
        report = self.single(QualityPerformance="-1")
        self.assertIn(REASON_OUT_OF_DEFINED_RANGE, self.reasons(report))

    def test_identifier_empty_is_unresolved_identity(self) -> None:
        report = self.single(plant_id="")
        self.assertIn(REASON_UNRESOLVED_IDENTITY, self.reasons(report))
        issue = next(i for i in report.issues if i.reason == REASON_UNRESOLVED_IDENTITY)
        self.assertEqual(issue.category, CATEGORY_IDENTITY_RESOLUTION)

    def test_identifier_whitespace_only_is_not_auto_trimmed(self) -> None:
        # ``C-10`` forbids trim; a whitespace-only identifier is present and opaque.
        report = self.single(plant_id="   ")
        self.assertEqual(report.issues, ())


class StatusVocabularyTests(Layer2TestCase):
    def test_inventory_status_unknown_value_is_invalid_defined_status(self) -> None:
        report = self.single(inventory_status="BROKEN")
        self.assertIn(REASON_INVALID_DEFINED_STATUS, self.reasons(report))

    def test_inventory_status_unknown_is_not_coerced_to_available(self) -> None:
        report = self.single(inventory_status="UNKNOWN")
        self.assertIn(REASON_INVALID_DEFINED_STATUS, self.reasons(report))

    def test_inbound_status_approved_vocabulary_is_accepted(self) -> None:
        for value in (
            "OPEN",
            "CONFIRMED",
            "PARTIALLY_RECEIVED",
            "CANCELLED",
            "CLOSED",
            "COMPLETED",
        ):
            with self.subTest(value=value):
                report = self.single(inbound_status=value)
                self.assertEqual(report.issues, (), msg=value)

    def test_inbound_status_unknown_value_is_invalid_defined_status(self) -> None:
        report = self.single(inbound_status="PENDING")
        self.assertIn(REASON_INVALID_DEFINED_STATUS, self.reasons(report))

    def test_sourcing_status_has_no_allowlist(self) -> None:
        rule = LAYER2_FIELD_RULE_BY_NAME["sourcing_status"]
        self.assertIsNone(rule.vocabulary)
        report = self.single(sourcing_status="ANY-SOURCE-SPECIFIC-CODE")
        self.assertEqual(report.issues, ())

    def test_sourcing_status_value_legality_is_not_evaluable(self) -> None:
        report = self.single(sourcing_status="ANY-SOURCE-SPECIFIC-CODE")
        names = {check.name for check in report.not_evaluable_checks}
        self.assertTrue(
            any("layer2.field_not_evaluable" in name and "sourcing_status" in name for name in names)
        )

    def test_approval_status_known_states_are_accepted(self) -> None:
        for value in ("APPROVED", "PENDING", "REJECTED", "UNKNOWN"):
            with self.subTest(value=value):
                report = self.single(approval_status=value)
                self.assertEqual(report.issues, (), msg=value)

    def test_approval_status_unknown_value_is_invalid_defined_status(self) -> None:
        report = self.single(approval_status="MAYBE")
        self.assertIn(REASON_INVALID_DEFINED_STATUS, self.reasons(report))


class ValidZeroTests(Layer2TestCase):
    def test_valid_zero_is_not_missing_or_out_of_range(self) -> None:
        report = self.single(
            SafetyStock="0",
            loss_rate="0",
            AllocatedSubstituteQty="0",
            ApplicableMOQ="0",
            DeliveryPerformance="0",
            QualityPerformance="0",
            received_qty="0",
        )
        self.assertEqual(report.issues, ())


class ValidButIneligibleTests(Layer2TestCase):
    def test_known_ineligible_states_produce_no_issue(self) -> None:
        report = self.single(inventory_status="INSPECTION")
        self.assertEqual(report.issues, ())

        report = self.single(inventory_status="FROZEN")
        self.assertEqual(report.issues, ())

        report = self.single(inbound_status="CANCELLED")
        self.assertEqual(report.issues, ())

        report = self.single(approval_status="PENDING")
        self.assertEqual(report.issues, ())

    def test_ineligible_is_not_reclassified_as_consistency_conflict(self) -> None:
        report = self.single(inbound_status="CANCELLED")
        self.assertNotIn("CONSISTENCY_CONFLICT", self.reasons(report))


class OmissionAndNullDeferralTests(Layer2TestCase):
    def test_omitted_property_produces_no_missing_issue(self) -> None:
        record = dict(VALID_RECORD)
        record.pop("SafetyStock")
        record.pop("PerformancePeriod")
        report = self.run_layer2([record])
        self.assertNotIn("MISSING", self.reasons(report))
        self.assertEqual(report.issues, ())

    def test_omitted_property_produces_no_invalid_type_issue(self) -> None:
        record = dict(VALID_RECORD)
        record.pop("ProductionQty")
        report = self.run_layer2([record])
        self.assertNotIn(REASON_INVALID_TYPE, self.reasons(report))

    def test_json_null_produces_no_invalid_type(self) -> None:
        report = self.single(ProductionQty=None)
        self.assertNotIn(REASON_INVALID_TYPE, self.reasons(report))

    def test_json_null_produces_no_missing_in_this_subset(self) -> None:
        report = self.single(SafetyStock=None)
        self.assertNotIn("MISSING", self.reasons(report))
        self.assertEqual(report.issues, ())

    def test_json_null_is_reported_not_evaluable(self) -> None:
        report = self.single(SafetyStock=None)
        names = {check.name for check in report.not_evaluable_checks}
        self.assertTrue(any("layer2.null_missingness" in name for name in names))

    def test_json_null_and_omission_are_distinguished(self) -> None:
        null_record = dict(VALID_RECORD)
        null_record["SafetyStock"] = None
        omitted_record = dict(VALID_RECORD)
        omitted_record.pop("SafetyStock")

        null_report = self.run_layer2([null_record], name="pkg-null")
        omitted_report = self.run_layer2([omitted_record], name="pkg-omitted")

        null_names = {check.name for check in null_report.not_evaluable_checks}
        omitted_names = {check.name for check in omitted_report.not_evaluable_checks}
        self.assertTrue(any("null_missingness" in name for name in null_names))
        self.assertFalse(any("null_missingness" in name for name in omitted_names))
        self.assertEqual(null_report.issues, ())
        self.assertEqual(omitted_report.issues, ())

    def test_null_is_not_converted_to_zero_or_empty_string(self) -> None:
        report = self.single(ProductionQty=None, plant_id=None)
        for issue in report.issues:
            self.assertNotIn("0", issue.detail.split("value")[0])
        self.assertNotIn(REASON_INVALID_TYPE, self.reasons(report))
        self.assertNotIn(REASON_OUT_OF_DEFINED_RANGE, self.reasons(report))

    def test_performance_period_present_value_is_not_evaluable(self) -> None:
        report = self.single(PerformancePeriod="anything-at-all")
        self.assertNotIn(REASON_INVALID_TYPE, self.reasons(report))
        names = {check.name for check in report.not_evaluable_checks}
        self.assertTrue(any("field_not_evaluable" in name and "PerformancePeriod" in name for name in names))


class DerivedFieldTests(Layer2TestCase):
    def test_derived_result_field_is_not_a_layer2_target(self) -> None:
        # A DERIVED result is not a snapshot wire property (§4.3.30 B.1), so Layer 1
        # rejects it as unknown content.  Layer 2 must therefore never carry a rule for
        # one (§4.4.36: validation does not recompute business logic).
        built = build_package(
            self.boundary / "pkg-derived",
            PackageSpec(
                datasets=[
                    DatasetSpec(
                        role="Production Requirement",
                        artifact="r.json",
                        records=[{"plant_id": "P1", "RecommendedPurchaseQty": "5"}],
                    )
                ]
            ),
            boundary_root=self.boundary,
        )
        layer1 = load_package(
            built.root, trusted_boundary=TrustedInputBoundary(root=self.boundary)
        )
        self.assertNotEqual(layer1.disposition, DISPOSITION_ACCEPTED)
        self.assertIsNone(layer1.accepted_package)

        derived = {
            "BaseRequirement",
            "GrossRequirement",
            "CumulativeGrossRequirement",
            "OpeningUsableInventory",
            "RemainingInboundQty",
            "EffectiveInbound",
            "CumulativeEffectiveInbound",
            "EquivalentTargetQty",
            "ApprovedSubstituteSupply",
            "CumulativeApprovedSubstituteSupply",
            "RemainingUnallocatedSourceSupply",
            "ProjectedAvailable",
            "Classification",
            "ShortageQty",
            "BufferGap",
            "FirstShortageDate",
            "DaysUntilNeed",
            "LeadTimeRisk",
            "DeliveryRisk",
            "QualityRisk",
            "OverallSupplierRisk",
            "BasePurchaseNeed",
            "MOQAdjustmentQty",
            "RecommendedPurchaseQty",
        }
        self.assertEqual(derived & set(LAYER2_FIELD_RULE_BY_NAME), set())

    def test_derived_result_is_not_evaluable_if_it_ever_reaches_layer2(self) -> None:
        # Layer 1 rejects a DERIVED property as unknown content, so this situation is
        # not reachable through the loader.  The guard is still asserted directly: if a
        # field ever reaches Layer 2 without a registered present-value rule, it must be
        # reported not evaluable rather than guessed.
        record = dict(VALID_RECORD)
        record["Classification"] = "NOT-A-BUSINESS-TRUTH"
        accepted = self.synthetic_accepted_package([record], name="synthetic-derived")

        report = validate_layer2(accepted)

        self.assertEqual(report.issues, ())
        names = {check.name for check in report.not_evaluable_checks}
        self.assertTrue(
            any("layer2.field_rule" in name and "Classification" in name for name in names)
        )

    def test_required_quantity_is_not_rebuilt(self) -> None:
        report = self.single()
        for issue in report.issues:
            self.assertNotIn("required_quantity", issue.detail)
        self.assertNotIn("required_quantity", LAYER2_FIELD_RULE_BY_NAME)


class DeterminismTests(Layer2TestCase):
    def test_issue_ordering_is_deterministic(self) -> None:
        record = dict(VALID_RECORD)
        record["ProductionQty"] = "-1"
        record["SafetyStock"] = "abc"
        record["inventory_status"] = "BROKEN"

        first = self.run_layer2([record], name="pkg-a")
        second = self.run_layer2([record], name="pkg-b")
        self.assertEqual(
            [(i.category, i.reason, i.location) for i in first.issues],
            [(i.category, i.reason, i.location) for i in second.issues],
        )

    def test_collect_all_reachable_defects(self) -> None:
        first = dict(VALID_RECORD)
        first["ProductionQty"] = "-1"
        second = dict(VALID_RECORD)
        second["SafetyStock"] = "abc"
        second["inventory_status"] = "BROKEN"
        report = self.run_layer2([first, second])
        locations = self.locations(report)
        self.assertIn("r.json[0].ProductionQty", locations)
        self.assertIn("r.json[1].SafetyStock", locations)
        self.assertIn("r.json[1].inventory_status", locations)
        self.assertGreaterEqual(len(report.issues), 3)

    def test_same_input_same_issue_set(self) -> None:
        record = dict(VALID_RECORD)
        record["DeliveryPerformance"] = "150"
        a = self.run_layer2([record], name="pkg-x")
        b = self.run_layer2([record], name="pkg-y")
        self.assertEqual(len(a.issues), len(b.issues))


class PrerequisiteNotEvaluableTests(Layer2TestCase):
    def test_non_object_record_blocks_field_checks_for_that_record(self) -> None:
        # Layer 1 guarantees record objects, so this carrier is unreachable through the
        # loader; the guard is exercised directly.  Layer 2 must not fabricate field
        # issues for a record it could not read as an object.
        accepted = self.synthetic_accepted_package([["positional"]], name="synthetic-arr")
        report = validate_layer2(accepted)
        names = {check.name for check in report.not_evaluable_checks}
        self.assertTrue(any(layer2_module.LAYER2_RECORD_CARRIER in name for name in names))
        self.assertEqual(report.issues, ())

    def test_unreachable_prerequisite_is_never_reported_as_passed(self) -> None:
        accepted = self.synthetic_accepted_package([["positional"]], name="synthetic-arr2")
        report = validate_layer2(accepted)

        # The dataset-level parse prerequisite passed; the per-record prerequisite did
        # not, and no per-record check may claim to have passed.
        dataset_check = f"{layer2_module.LAYER2_RECORD_CARRIER}:r.json"
        record_check = f"{layer2_module.LAYER2_RECORD_CARRIER}:r.json[0]"
        states = {check.name: check.state for check in report.checks}
        self.assertEqual(states[dataset_check], "passed")
        self.assertEqual(states[record_check], "not_evaluable")
        self.assertFalse(
            any(
                name.startswith("layer2.present_value:r.json[0]") and state == "passed"
                for name, state in states.items()
            )
        )

    def test_blocked_dataset_makes_the_field_rules_check_not_evaluable(self) -> None:
        accepted = self.synthetic_accepted_package([["positional"]], name="synthetic-arr3")
        report = validate_layer2(accepted)
        states = {check.name: check.state for check in report.checks}
        self.assertEqual(
            states[layer2_module.LAYER2_PRESENT_VALUE_RULES], "not_evaluable"
        )

    def test_empty_dataset_is_not_a_layer2_defect(self) -> None:
        built = build_package(
            self.boundary / "pkg-empty",
            PackageSpec(
                datasets=[
                    DatasetSpec(
                        role="Inventory Snapshot",
                        artifact="i.json",
                        records=[],
                    )
                ]
            ),
            boundary_root=self.boundary,
        )
        report = load_package(
            built.root, trusted_boundary=TrustedInputBoundary(root=self.boundary)
        )
        self.assertEqual(report.disposition, DISPOSITION_ACCEPTED)
        assert report.accepted_package is not None
        layer2 = validate_layer2(report.accepted_package)
        self.assertEqual(layer2.issues, ())


class AcceptedViewBindingTests(Layer2TestCase):
    def test_layer2_binds_to_the_accepted_content_view(self) -> None:
        _, accepted = self.accepted([dict(VALID_RECORD)])
        report = validate_layer2(accepted)
        self.assertEqual(report.accepted_content_view_digest, accepted.content_view_digest)

    def test_layer2_consumes_accepted_view_bytes_not_a_fresh_read(self) -> None:
        _, accepted = self.accepted([dict(VALID_RECORD)])
        self.assertEqual(accepted.records_for("r.json"), accepted.accepted_records[0][2])

    def test_mutated_package_is_unusable_and_layer2_does_not_run(self) -> None:
        built, accepted = self.accepted([dict(VALID_RECORD)])
        target = built.root / "r.json"
        payload = json.loads(target.read_text(encoding="utf-8"))
        payload[0]["ProductionQty"] = "-1"
        target.write_bytes(encode_json(payload))

        report = validate_layer2(accepted)

        self.assertEqual(report.disposition, DISPOSITION_UNUSABLE)
        self.assertFalse(report.reusable)
        self.assertNotIn(REASON_OUT_OF_DEFINED_RANGE, self.reasons(report))
        names = {check.name for check in report.checks}
        self.assertIn(layer2_module.LAYER2_REVERIFICATION, names)

    def test_mutation_is_detected_even_when_the_change_would_be_invalid(self) -> None:
        # A mutated file must never be re-read and validated as if it were accepted
        # evidence; it must fail at re-verification instead.
        built, accepted = self.accepted([dict(VALID_RECORD)])
        (built.root / "r.json").write_bytes(encode_json([{"ProductionQty": "-1"}]))

        report = validate_layer2(accepted)

        self.assertEqual(report.disposition, DISPOSITION_UNUSABLE)
        self.assertEqual(report.issues_for(category=CATEGORY_FIELD_VALUE), ())

    def test_deleted_artifact_is_unusable(self) -> None:
        built, accepted = self.accepted([dict(VALID_RECORD)])
        (built.root / "r.json").unlink()

        report = validate_layer2(accepted)

        self.assertEqual(report.disposition, DISPOSITION_UNUSABLE)

    def test_unchanged_package_stays_accepted_and_reusable(self) -> None:
        _, accepted = self.accepted([dict(VALID_RECORD)])
        report = validate_layer2(accepted)
        self.assertTrue(report.accepted)
        self.assertTrue(report.reusable)
        self.assertEqual(report.disposition, DISPOSITION_ACCEPTED)


class LayerBoundaryTests(Layer2TestCase):
    def test_no_layer3_or_layer4_output(self) -> None:
        report = self.single(SafetyStock="-10", DeliveryPerformance="150")
        detail_blob = " ".join(issue.detail for issue in report.issues).upper()
        consequence_blob = " ".join(
            issue.consequence_context or "" for issue in report.issues
        ).upper()
        for forbidden in (
            "CAPABILITY",
            "SHORTAGE",
            "DATA_INCOMPLETE",
            "RECOMMENDATION",
            "OVERALLSUPPLIERRISK",
        ):
            self.assertNotIn(forbidden, detail_blob)
            self.assertNotIn(forbidden, consequence_blob)

    def test_no_unapproved_reason_or_category(self) -> None:
        allowed_reasons = {
            REASON_INVALID_TYPE,
            REASON_OUT_OF_DEFINED_RANGE,
            REASON_INVALID_DEFINED_STATUS,
            REASON_UNRESOLVED_IDENTITY,
        }
        allowed_categories = {CATEGORY_FIELD_VALUE, CATEGORY_IDENTITY_RESOLUTION}
        report = self.single(
            ProductionQty="-1",
            plant_id="",
            inventory_status="BROKEN",
            SafetyStock="abc",
        )
        for issue in report.issues:
            self.assertIn(issue.reason, allowed_reasons)
            self.assertIn(issue.category, allowed_categories)

    def test_layer2_never_rejects_the_package(self) -> None:
        report = self.single(ProductionQty="-1")
        self.assertNotEqual(report.disposition, "REJECTED")
        self.assertTrue(report.accepted)

    def test_no_severity_or_error_code_surface(self) -> None:
        report = self.single(ProductionQty="-1")
        payload = report.to_dict()
        self.assertNotIn("severity", json.dumps(payload).lower())
        for issue in report.issues:
            self.assertFalse(hasattr(issue, "severity"))
            self.assertFalse(hasattr(issue, "code"))

    def test_layer3_and_layer4_reasons_are_not_emitted(self) -> None:
        report = self.single(ProductionQty="-1", inventory_status="BROKEN")
        for forbidden in (
            "EVIDENCE_ROLE_NOT_PROVIDED",
            "SEMANTIC_UNRESOLVED",
            "CONSISTENCY_CONFLICT",
            "PROVENANCE_UNRESOLVED",
            "PROVENANCE_MISMATCH",
            "UNRESOLVED_SCOPE",
        ):
            self.assertNotIn(forbidden, self.reasons(report))

    def test_cross_field_consistency_is_not_enforced_here(self) -> None:
        # registered_qty > ordered_qty is a cross-record consistency rule owned by a
        # later subtask; Layer 2 must not emit a consistency issue for it.
        report = self.single(ordered_qty="10", received_qty="20")
        self.assertEqual(report.issues, ())

    def test_no_per_role_whitelist_or_schema_module(self) -> None:
        self.assertFalse(hasattr(layer2_module, "PER_ROLE_WHITELIST"))
        self.assertFalse(hasattr(layer2_module, "DATASET_SCHEMA"))
        self.assertFalse(hasattr(layer2_module, "INPUT_CHANNEL"))

    def test_no_input_channel_or_normalisation_helpers(self) -> None:
        for forbidden in ("normalize", "coerce", "default_value", "channel_for"):
            self.assertFalse(hasattr(layer2_module, forbidden), msg=forbidden)


class Layer1RegressionTests(Layer2TestCase):
    def test_layer1_checks_are_untouched_by_layer2(self) -> None:
        built = valid_package(self.boundary / "pkg-l1", boundary_root=self.boundary)
        report = load_package(
            built.root, trusted_boundary=TrustedInputBoundary(root=self.boundary)
        )
        self.assertEqual(report.disposition, DISPOSITION_ACCEPTED)
        # Layer 1 still owns its own mandatory registry; Layer 2 adds no Layer-1 gate.
        self.assertIn("package.acceptance_time_stable_view", MANDATORY_LAYER1_CHECKS)
        layer2 = validate_layer2(report.accepted_package)  # type: ignore[arg-type]
        self.assertFalse(
            any(name.startswith("layer2.") for name in MANDATORY_LAYER1_CHECKS)
        )
        self.assertTrue(layer2.accepted)

    def test_layer1_rejection_still_prevents_layer2(self) -> None:
        built = build_package(
            self.boundary / "pkg-bad",
            PackageSpec(contract_version="v0.1"),
            boundary_root=self.boundary,
        )
        report = load_package(
            built.root, trusted_boundary=TrustedInputBoundary(root=self.boundary)
        )
        self.assertNotEqual(report.disposition, DISPOSITION_ACCEPTED)
        self.assertIsNone(report.accepted_package)


class ReportSurfaceTests(Layer2TestCase):
    def test_report_renders_text(self) -> None:
        report = self.single(ProductionQty="-1")
        text = report.render_text()
        self.assertIn("layer", text)
        self.assertIn("Canonical Evidence Validation", text)
        self.assertIn(REASON_OUT_OF_DEFINED_RANGE, text)

    def test_report_serialises(self) -> None:
        report = self.single(ProductionQty="-1")
        payload = report.to_dict()
        self.assertEqual(payload["layer"], LAYER_2)
        self.assertEqual(payload["disposition"], DISPOSITION_ACCEPTED)
        self.assertIsInstance(payload["issues"], list)


if __name__ == "__main__":
    unittest.main()
