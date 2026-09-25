"""``BR-INVENTORY-001`` Available Inventory / Safety Stock tests (POC Design v0.2 §2.2).

Coverage mirrors the registered acceptance examples and the fail-safe boundaries:

* A -- ``§2.2.10`` Example A: several in-scope observations of one grain aggregate to 130;
* B -- ``OUT_OF_SCOPE`` is a legal exclusion (contribution 0, no Data Quality Issue);
* C -- unresolved scope poisons the whole grain (never a partial 100);
* D -- unknown ``inventory_status`` never becomes ``AVAILABLE``;
* E -- negative ``on_hand_qty`` is a rule-level invalid prerequisite (no clamp, no row drop);
* F -- a valid zero stays a numeric zero;
* G / H / I -- no cross-Plant, cross-Material or cross-snapshot-time aggregation;
* J -- content-identical observations at distinct references both contribute (no dedup);
* K / L / M / N -- SafetyStock positive / zero / missing / negative, never subtracted;
* O / P -- ``INSPECTION`` and ``FROZEN`` only contribute 0 without a defect;
* Q -- grain readiness is independent of ownership / scope resolution;
* R / S / T -- deterministic repeatability, retained provenance and exact large numbers.

All fixtures are SIMULATED.
"""

from __future__ import annotations

import json
import unittest
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any

from snapshot_loader import (
    INVENTORY_DATA_INCOMPLETE,
    InventoryScopeHandoff,
    PhaseAHandoff,
    SafetyStockHandoff,
    TrustedInputBoundary,
    compute_opening_usable_inventory,
    construct_canonical_objects,
    load_package,
)
from snapshot_loader.canonical_objects import ContextValueReference, CanonicalProperty
from snapshot_loader.inventory_calculation import (
    EXCLUSION_FROZEN,
    EXCLUSION_INSPECTION,
    EXCLUSION_OUT_OF_SCOPE,
    INVENTORY_RULE_ID,
    SAFETY_STOCK_STATE_AMBIGUOUS,
    SAFETY_STOCK_STATE_MISSING,
    SAFETY_STOCK_STATE_RESOLVED,
    SAFETY_STOCK_STATE_UNRESOLVED,
    SCOPE_STATE_IN_SCOPE,
    SCOPE_STATE_OUT_OF_SCOPE,
    SCOPE_STATE_UNRESOLVED,
)
from tests.helpers import DatasetSpec, PackageSpec, build_package

SCRATCH_ROOT = Path(__file__).resolve().parents[1] / "build" / "test-scratch"

PLANT = "P1"
PLANT_B = "P2"
MATERIAL = "M1"
MATERIAL_B = "M2"
SNAPSHOT_TIME = "2026-01-31T08:00:00Z"
SNAPSHOT_TIME_B = "2026-02-01T08:00:00Z"
ROLE_INVENTORY = "Inventory Snapshot"
ROLE_INBOUND = "Inbound Supply"

LOCATOR_WAREHOUSE = "SIMULATED-WH-01-CONTEXT"
BASIS_A_IN = "SIMULATED-INV-SCOPE-A-IN"
BASIS_A_OUT = "SIMULATED-INV-SCOPE-A-OUT"
EVIDENCE_SAFETY_STOCK = "SIMULATED-SRC-SS-1"
BASIS_SAFETY_STOCK = "SIMULATED-APPROVED-SAFETY-STOCK-MAPPING"

LARGE_FIRST = "123456789012345678901234567890"
LARGE_SECOND = "100000000000000000000000000001"
LARGE_SUM = "223456789012345678901234567891"


def with_provenance(
    record: dict[str, object],
    associations: list[tuple[str, list[str], str | None]],
) -> dict[str, object]:
    out = dict(record)
    out["_meta"] = {
        "provenance_associations": [
            {
                "observation": observation,
                "evidence": list(evidence),
                **({"mapping_basis": basis} if basis is not None else {}),
            }
            for observation, evidence, basis in associations
        ]
    }
    return out


def INVENTORY(
    *,
    plant: Any = PLANT,
    material: Any = MATERIAL,
    snapshot_time: Any = SNAPSHOT_TIME,
    status: Any = "AVAILABLE",
    on_hand: Any = "100",
    basis: str | None = BASIS_A_IN,
) -> dict[str, object]:
    record: dict[str, object] = {}
    if plant is not None:
        record["plant_id"] = plant
    if material is not None:
        record["material_code"] = material
    if snapshot_time is not None:
        record["inventory_snapshot_time"] = snapshot_time
    if status is not None:
        record["inventory_status"] = status
    if on_hand is not None:
        record["on_hand_qty"] = on_hand
    associations: list[tuple[str, list[str], str | None]] = []
    if basis is not None:
        associations.append(("plant_id", [LOCATOR_WAREHOUSE], basis))
    return with_provenance(record, associations)


def with_scope_basis(record: dict[str, object], basis: str) -> dict[str, object]:
    """Return ``record`` whose registered ``plant_id`` association carries ``basis``.

    The registered basis and the I-9 handoff basis must match exactly: an out-of-scope
    fixture therefore has to register the ``OUT_OF_SCOPE`` basis on its own association.
    """

    out = dict(record)
    meta = dict(out.get("_meta", {}))  # type: ignore[arg-type]
    associations = [
        (
            {**association, "mapping_basis": basis}
            if association.get("observation") == "plant_id"
            else association
        )
        for association in meta.get("provenance_associations", [])  # type: ignore[union-attr]
    ]
    meta["provenance_associations"] = associations
    out["_meta"] = meta
    return out


def CONFIGURED_SAFETY_STOCK(
    value: Any = "30", *, plant: Any = PLANT, material: Any = MATERIAL
) -> dict[str, object]:
    record: dict[str, object] = {
        "plant_id": plant,
        "material_code": material,
        "SafetyStock": value,
    }
    if value is None:
        record.pop("SafetyStock")
    return with_provenance(
        record, [("SafetyStock", [EVIDENCE_SAFETY_STOCK], BASIS_SAFETY_STOCK)]
    )


def SAFETY_STOCK_POLICY(value: Any = "30") -> dict[str, object]:
    """Policy evidence in another role, carried through the I-5 handoff surface."""

    return with_provenance(
        {"plant_id": PLANT, "material_code": MATERIAL, "SafetyStock": value},
        [("SafetyStock", [EVIDENCE_SAFETY_STOCK], BASIS_SAFETY_STOCK)],
    )


class InventoryRuleTestCase(unittest.TestCase):
    """Shared scaffolding: one accepted package per subtest directory."""

    def setUp(self) -> None:
        self.boundary = SCRATCH_ROOT / f"inventory-rule-{uuid.uuid4().hex}"
        self.boundary.mkdir(parents=True, exist_ok=True)

    def accepted(
        self,
        datasets: list[tuple[str, list[dict[str, object]]]],
        *,
        name: str | None = None,
        package_id: str = "SIMULATED-PKG-0001",
    ):
        directory = self.boundary / (name or uuid.uuid4().hex[:8])
        specs = [
            DatasetSpec(role=role, artifact=f"{index}.json", records=records)
            for index, (role, records) in enumerate(datasets)
        ]
        built = build_package(
            directory,
            PackageSpec(datasets=specs, package_id=package_id),
            boundary_root=self.boundary,
        )
        report = load_package(
            built.root, trusted_boundary=TrustedInputBoundary(root=self.boundary)
        )
        self.assertTrue(
            report.accepted,
            msg=f"fixture package was not accepted: {report.disposition_basis}",
        )
        assert report.accepted_package is not None
        return report.accepted_package

    def citation(self, accepted, *, role: str, artifact: str, ordinal: int = 0, locator=None):
        from snapshot_loader.canonical_objects import HandoffEvidence

        return HandoffEvidence(
            snapshot_package_identity=accepted.package_id,
            logical_dataset_role=role,
            artifact=artifact,
            record_ordinal=ordinal,
            evidence_locator=locator,
        )

    def scope_handoffs(
        self,
        accepted,
        *,
        inventory_ordinals: tuple[int, ...],
        artifact: str = "0.json",
        basis: str | None = BASIS_A_IN,
    ):
        """One I-9 entry per cited inventory ordinal (``basis=None`` = no resolution)."""

        if basis is None:
            return ()
        return tuple(
            InventoryScopeHandoff(
                inventory_evidence=self.citation(
                    accepted, role=ROLE_INVENTORY, artifact=artifact, ordinal=ordinal
                ),
                scope_observation="plant_id",
                scope_resolution_basis=basis,
            )
            for ordinal in inventory_ordinals
        )

    def construct(
        self,
        datasets: list[tuple[str, list[dict[str, object]]]],
        *,
        scope: tuple = (),
        safety_stock: tuple = (),
        name: str | None = None,
    ):
        accepted = self.accepted(datasets, name=name)
        handoff = PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-01-31",
            inventory_scope=scope,
            safety_stock=safety_stock,
        )
        construction = construct_canonical_objects(accepted, handoff)
        return construction, compute_opening_usable_inventory(construction)

    # --- convenience ---------------------------------------------------------------

    def single_target_report(
        self,
        records: list[dict[str, object]],
        *,
        safety_stock: dict[str, object] | list[dict[str, object]] | None = None,
        name: str,
        out_of_scope_ordinals: tuple[int, ...] = (),
        no_scope_ordinals: tuple[int, ...] = (),
    ):
        records = [
            with_scope_basis(record, BASIS_A_OUT)
            if index in out_of_scope_ordinals
            else record
            for index, record in enumerate(records)
        ]
        datasets: list[tuple[str, list[dict[str, object]]]] = [
            (ROLE_INVENTORY, records)
        ]
        if safety_stock is not None:
            safety_records = (
                safety_stock if isinstance(safety_stock, list) else [safety_stock]
            )
            datasets.append(("Configured Safety Stock", safety_records))
        accepted = self.accepted(datasets, name=name)
        in_scope_ordinals = tuple(
            index
            for index in range(len(records))
            if index not in out_of_scope_ordinals and index not in no_scope_ordinals
        )
        scope = self.scope_handoffs(
            accepted, inventory_ordinals=in_scope_ordinals, basis=BASIS_A_IN
        ) + self.scope_handoffs(
            accepted, inventory_ordinals=out_of_scope_ordinals, basis=BASIS_A_OUT
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1", analysis_date="2026-01-31", inventory_scope=scope
            ),
        )
        result = compute_opening_usable_inventory(construction)
        self.assertEqual(len(result.targets), 1, msg="fixture must form exactly one target")
        return accepted, construction, result, result.targets[0]

    def rule_issues(self, *holders) -> list:
        out = []
        for holder in holders:
            out.extend(holder.rule_issues)
        return out
class AcceptanceExampleTests(InventoryRuleTestCase):
    def test_example_a_eligible_warehouses_aggregate_to_130(self) -> None:
        """``§2.2.10`` Example A: 100 + 30 eligible, 40 INSPECTION and 20 FROZEN excluded."""

        records = [
            INVENTORY(on_hand="100", status="AVAILABLE"),
            INVENTORY(on_hand="30", status="AVAILABLE"),
            INVENTORY(on_hand="40", status="INSPECTION"),
            INVENTORY(on_hand="20", status="FROZEN"),
        ]
        _accepted, construction, result, target = self.single_target_report(
            records, safety_stock=CONFIGURED_SAFETY_STOCK("30"), name="example-a"
        )
        # The canonicalization layer retains all four observations and aggregates nothing.
        self.assertEqual(len(construction.objects_for(ROLE_INVENTORY)), 4)
        self.assertEqual(construction.unresolved_for(ROLE_INVENTORY), ())
        self.assertEqual(len(target.evaluations), 4)
        # The business rule performs the aggregation.
        self.assertIsNone(target.outcome)
        self.assertEqual(target.to_dict()["OpeningUsableInventory"], "130")
        self.assertEqual(target.to_dict()["SafetyStock"], "30")
        self.assertEqual(
            sorted(item.to_dict()["contribution"] for item in target.evaluations),
            ["0", "0", "100", "30"],
        )
        self.assertEqual(
            sorted(
                item.exclusion_reason
                for item in target.evaluations
                if item.exclusion_reason is not None
            ),
            [EXCLUSION_FROZEN, EXCLUSION_INSPECTION],
        )
        self.assertEqual(target.rule_issues, ())
        self.assertEqual(target.issues, ())

    def test_out_of_scope_observation_is_legally_excluded(self) -> None:
        records = [INVENTORY(on_hand="100"), INVENTORY(on_hand="500")]
        _accepted, _construction, result, target = self.single_target_report(
            records,
            safety_stock=CONFIGURED_SAFETY_STOCK("0"),
            name="out-of-scope",
            out_of_scope_ordinals=(1,),
        )
        self.assertIsNone(target.outcome)
        self.assertEqual(target.to_dict()["OpeningUsableInventory"], "100")
        excluded = target.evaluations[1]
        self.assertEqual(excluded.scope_state, SCOPE_STATE_OUT_OF_SCOPE)
        self.assertIs(excluded.in_scope, False)
        self.assertEqual(excluded.contribution.text(), "0")
        self.assertEqual(excluded.exclusion_reason, EXCLUSION_OUT_OF_SCOPE)
        # A legal exclusion is not a data-quality defect.
        self.assertEqual(target.rule_issues, ())
        self.assertEqual(result.rule_issues, ())
        self.assertEqual(
            [issue for issue in result.issues if "500" in (issue.detail or "")], []
        )

    def test_unresolved_scope_poisons_the_whole_grain(self) -> None:
        records = [INVENTORY(on_hand="100"), INVENTORY(on_hand="30")]
        _accepted, _construction, result, target = self.single_target_report(
            records,
            safety_stock=CONFIGURED_SAFETY_STOCK("0"),
            name="scope-unresolved",
            no_scope_ordinals=(1,),
        )
        self.assertEqual(target.outcome, INVENTORY_DATA_INCOMPLETE)
        self.assertIsNone(target.opening_usable_inventory)
        self.assertIsNone(target.to_dict()["OpeningUsableInventory"])
        unresolved = target.evaluations[1]
        self.assertFalse(unresolved.scope_resolved)
        self.assertEqual(unresolved.scope_state, SCOPE_STATE_UNRESOLVED)
        self.assertIsNone(unresolved.in_scope)
        self.assertIsNone(unresolved.contribution)
        # Never a partial 100, and never a silently skipped record.
        self.assertNotEqual(target.to_dict()["OpeningUsableInventory"], "100")
        self.assertEqual(
            [issue.reason for issue in result.issues], ["UNRESOLVED_SCOPE"]
        )

    def test_unknown_status_never_becomes_available(self) -> None:
        records = [INVENTORY(on_hand="100"), INVENTORY(on_hand="30", status="UNKNOWN")]
        _accepted, _construction, result, target = self.single_target_report(
            records, safety_stock=CONFIGURED_SAFETY_STOCK("0"), name="unknown-status"
        )
        self.assertEqual(target.outcome, INVENTORY_DATA_INCOMPLETE)
        self.assertIsNone(target.opening_usable_inventory)
        self.assertIsNone(target.evaluations[1].contribution)
        self.assertEqual(
            [(issue.category, issue.reason) for issue in result.rule_issues],
            [("FIELD_VALUE", "INVALID_DEFINED_STATUS")],
        )
        self.assertNotIn("AVAILABLE", [issue.reason for issue in result.rule_issues])

    def test_negative_inventory_is_invalid_without_clamp(self) -> None:
        records = [INVENTORY(on_hand="100"), INVENTORY(on_hand="-5")]
        _accepted, _construction, result, target = self.single_target_report(
            records, safety_stock=CONFIGURED_SAFETY_STOCK("0"), name="negative"
        )
        self.assertEqual(target.outcome, INVENTORY_DATA_INCOMPLETE)
        self.assertIsNone(target.opening_usable_inventory)
        negative = target.evaluations[1]
        self.assertEqual(negative.on_hand_qty.text(), "-5")
        self.assertIsNone(negative.contribution)
        self.assertEqual(
            [(issue.category, issue.reason) for issue in result.rule_issues],
            [("FIELD_VALUE", "OUT_OF_DEFINED_RANGE")],
        )
        # Never 95 (100 + (-5)), never 0, never a dropped row.
        self.assertNotIn(target.to_dict()["OpeningUsableInventory"], ("95", "0", "100"))

    def test_zero_inventory_is_a_valid_numeric_zero(self) -> None:
        _accepted, _construction, _result, target = self.single_target_report(
            [INVENTORY(on_hand="0")],
            safety_stock=CONFIGURED_SAFETY_STOCK("0"),
            name="zero",
        )
        self.assertIsNone(target.outcome)
        self.assertEqual(target.to_dict()["OpeningUsableInventory"], "0")

    def test_missing_status_is_unresolved_without_default(self) -> None:
        _accepted, _construction, result, target = self.single_target_report(
            [INVENTORY(status=None, on_hand="100")],
            safety_stock=CONFIGURED_SAFETY_STOCK("0"),
            name="missing-status",
        )
        self.assertEqual(target.outcome, INVENTORY_DATA_INCOMPLETE)
        self.assertIsNone(target.opening_usable_inventory)
        self.assertIsNone(target.evaluations[0].inventory_status)
        self.assertEqual(
            [(issue.category, issue.reason) for issue in result.rule_issues],
            [("FIELD_VALUE", "MISSING")],
        )

    def test_missing_and_non_canonical_on_hand_qty_are_unresolved(self) -> None:
        for label, kwargs, reason in (
            ("missing", {"on_hand": None}, "MISSING"),
            ("non-decimal", {"on_hand": "not-a-decimal"}, "INVALID_TYPE"),
            ("exponent", {"on_hand": "1E+3"}, "INVALID_TYPE"),
        ):
            with self.subTest(case=label):
                _accepted, _construction, result, target = self.single_target_report(
                    [INVENTORY(**kwargs)],
                    safety_stock=CONFIGURED_SAFETY_STOCK("0"),
                    name=f"on-hand-{label}",
                )
                self.assertEqual(target.outcome, INVENTORY_DATA_INCOMPLETE)
                self.assertIsNone(target.opening_usable_inventory)
                self.assertIsNone(target.evaluations[0].contribution)
                self.assertEqual(
                    [(issue.category, issue.reason) for issue in result.rule_issues],
                    [("FIELD_VALUE", reason)],
                )
                # Never repaired into a number.
                self.assertIsNone(target.to_dict()["OpeningUsableInventory"])

    def test_inspection_and_frozen_do_not_bypass_quantity_validation(self) -> None:
        """A valid-but-ineligible status is only valid when the record itself is valid.

        ``INSPECTION`` / ``FROZEN`` contribute 0 -- but a negative, missing or malformed
        ``on_hand_qty`` is a rule-level invalid prerequisite for **every** status
        (``§2.2.8`` / ``§2.2.9``), so it must never be waived as a "non-contributing" row.
        """

        cases = (
            ("INSPECTION", "-5", "OUT_OF_DEFINED_RANGE"),
            ("FROZEN", "-5", "OUT_OF_DEFINED_RANGE"),
            ("INSPECTION", None, "MISSING"),
            ("FROZEN", "not-a-decimal", "INVALID_TYPE"),
        )
        for status, on_hand, reason in cases:
            with self.subTest(status=status, on_hand=on_hand):
                _accepted, _construction, result, target = self.single_target_report(
                    [INVENTORY(status=status, on_hand=on_hand)],
                    safety_stock=CONFIGURED_SAFETY_STOCK("0"),
                    name=f"{status.lower()}-{reason.lower()}",
                )
                self.assertEqual(target.outcome, INVENTORY_DATA_INCOMPLETE)
                self.assertIsNone(target.opening_usable_inventory)
                self.assertIsNone(target.to_dict()["OpeningUsableInventory"])
                evaluation = target.evaluations[0]
                self.assertIsNone(evaluation.contribution)
                self.assertIsNone(evaluation.eligible_on_hand_qty)
                # It is a defect, not a legal exclusion.
                self.assertIsNone(evaluation.exclusion_reason)
                self.assertEqual(
                    [(issue.category, issue.reason) for issue in result.rule_issues],
                    [("FIELD_VALUE", reason)],
                )

    def test_valid_ineligible_statuses_still_contribute_zero(self) -> None:
        """The valid-but-ineligible path is not weakened by the quantity validation."""

        for status, value, exclusion in (
            ("INSPECTION", "40", EXCLUSION_INSPECTION),
            ("FROZEN", "20", EXCLUSION_FROZEN),
            ("INSPECTION", "0", EXCLUSION_INSPECTION),
        ):
            with self.subTest(status=status, on_hand=value):
                _accepted, _construction, result, target = self.single_target_report(
                    [INVENTORY(status=status, on_hand=value)],
                    safety_stock=CONFIGURED_SAFETY_STOCK("0"),
                    name=f"valid-{status.lower()}-{value}",
                )
                self.assertIsNone(target.outcome)
                self.assertEqual(target.to_dict()["OpeningUsableInventory"], "0")
                self.assertEqual(target.evaluations[0].exclusion_reason, exclusion)
                self.assertEqual(result.issues, ())

    def test_out_of_scope_exclusion_does_not_require_status_or_quantity(self) -> None:
        """The scope gate stays first: an out-of-scope record is legally excluded."""

        for kwargs in (
            {"status": "INSPECTION", "on_hand": "-5"},
            {"status": "UNKNOWN", "on_hand": "not-a-decimal"},
            {"status": None, "on_hand": None},
        ):
            with self.subTest(case=kwargs):
                _accepted, _construction, result, target = self.single_target_report(
                    [INVENTORY(basis=BASIS_A_OUT, **kwargs)],
                    safety_stock=CONFIGURED_SAFETY_STOCK("0"),
                    name="out-of-scope-no-qty-gate",
                    out_of_scope_ordinals=(0,),
                )
                self.assertIsNone(target.outcome)
                evaluation = target.evaluations[0]
                self.assertEqual(evaluation.exclusion_reason, EXCLUSION_OUT_OF_SCOPE)
                self.assertEqual(evaluation.contribution.text(), "0")
                self.assertEqual(target.to_dict()["OpeningUsableInventory"], "0")
                self.assertEqual(result.issues, ())

    def test_inspection_only_and_frozen_only_are_valid_zeroes(self) -> None:
        for status, exclusion in (
            ("INSPECTION", EXCLUSION_INSPECTION),
            ("FROZEN", EXCLUSION_FROZEN),
        ):
            with self.subTest(status=status):
                _accepted, _construction, result, target = self.single_target_report(
                    [INVENTORY(on_hand="40", status=status)],
                    safety_stock=CONFIGURED_SAFETY_STOCK("0"),
                    name=f"{status.lower()}-only",
                )
                self.assertIsNone(target.outcome)
                self.assertEqual(target.to_dict()["OpeningUsableInventory"], "0")
                self.assertEqual(target.evaluations[0].exclusion_reason, exclusion)
                self.assertEqual(result.issues, ())


class GrainIsolationTests(InventoryRuleTestCase):
    def test_separate_plants_never_aggregate(self) -> None:
        records = [
            INVENTORY(plant=PLANT, on_hand="20"),
            INVENTORY(plant=PLANT_B, on_hand="100"),
        ]
        accepted = self.accepted(
            [
                (ROLE_INVENTORY, records),
                (
                    "Configured Safety Stock",
                    [
                        CONFIGURED_SAFETY_STOCK("0", plant=PLANT),
                        CONFIGURED_SAFETY_STOCK("0", plant=PLANT_B),
                    ],
                ),
            ],
            name="cross-plant",
        )
        scope = self.scope_handoffs(
            accepted, inventory_ordinals=(0, 1), basis=BASIS_A_IN
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1", analysis_date="2026-01-31", inventory_scope=scope
            ),
        )
        cross = compute_opening_usable_inventory(construction)
        self.assertEqual(len(cross.targets), 2)
        plant_a = cross.for_grain(PLANT, MATERIAL, SNAPSHOT_TIME)
        plant_b = cross.for_grain(PLANT_B, MATERIAL, SNAPSHOT_TIME)
        assert plant_a is not None and plant_b is not None
        self.assertEqual(plant_a.to_dict()["OpeningUsableInventory"], "20")
        self.assertEqual(plant_b.to_dict()["OpeningUsableInventory"], "100")
        self.assertNotEqual(plant_a.to_dict()["OpeningUsableInventory"], "120")

    def test_separate_materials_never_aggregate(self) -> None:
        accepted = self.accepted(
            [
                (
                    ROLE_INVENTORY,
                    [
                        INVENTORY(material=MATERIAL, on_hand="20"),
                        INVENTORY(material=MATERIAL_B, on_hand="100"),
                    ],
                ),
                (
                    "Configured Safety Stock",
                    [
                        CONFIGURED_SAFETY_STOCK("0", material=MATERIAL),
                        CONFIGURED_SAFETY_STOCK("0", material=MATERIAL_B),
                    ],
                ),
            ],
            name="cross-material",
        )
        scope = self.scope_handoffs(accepted, inventory_ordinals=(0, 1))
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1", analysis_date="2026-01-31", inventory_scope=scope
            ),
        )
        result = compute_opening_usable_inventory(construction)
        first = result.for_grain(PLANT, MATERIAL, SNAPSHOT_TIME)
        second = result.for_grain(PLANT, MATERIAL_B, SNAPSHOT_TIME)
        assert first is not None and second is not None
        self.assertEqual(first.to_dict()["OpeningUsableInventory"], "20")
        self.assertEqual(second.to_dict()["OpeningUsableInventory"], "100")

    def test_separate_snapshot_times_never_win_over_each_other(self) -> None:
        accepted = self.accepted(
            [
                (
                    ROLE_INVENTORY,
                    [
                        INVENTORY(snapshot_time=SNAPSHOT_TIME, on_hand="50"),
                        INVENTORY(snapshot_time=SNAPSHOT_TIME_B, on_hand="80"),
                    ],
                ),
                ("Configured Safety Stock", [CONFIGURED_SAFETY_STOCK("0")]),
            ],
            name="cross-snapshot-time",
        )
        scope = self.scope_handoffs(accepted, inventory_ordinals=(0, 1))
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1", analysis_date="2026-01-31", inventory_scope=scope
            ),
        )
        result = compute_opening_usable_inventory(construction)
        self.assertEqual(len(result.targets), 2)
        earlier = result.for_grain(PLANT, MATERIAL, SNAPSHOT_TIME)
        later = result.for_grain(PLANT, MATERIAL, SNAPSHOT_TIME_B)
        assert earlier is not None and later is not None
        self.assertEqual(earlier.to_dict()["OpeningUsableInventory"], "50")
        self.assertEqual(later.to_dict()["OpeningUsableInventory"], "80")

    def test_content_identical_observations_are_not_deduplicated(self) -> None:
        record = INVENTORY(on_hand="40")
        _accepted, _construction, _result, target = self.single_target_report(
            [dict(record), dict(record)],
            safety_stock=CONFIGURED_SAFETY_STOCK("0"),
            name="identical",
        )
        self.assertEqual(len(target.evaluations), 2)
        self.assertEqual(
            len({item.inventory_reference for item in target.evaluations}), 2
        )
        self.assertEqual(target.to_dict()["OpeningUsableInventory"], "80")

    def test_large_numbers_aggregate_exactly(self) -> None:
        records = [
            INVENTORY(on_hand=LARGE_FIRST),
            INVENTORY(on_hand=LARGE_SECOND),
        ]
        _accepted, _construction, _result, target = self.single_target_report(
            records, safety_stock=CONFIGURED_SAFETY_STOCK("0"), name="large"
        )
        self.assertEqual(target.to_dict()["OpeningUsableInventory"], LARGE_SUM)


class SafetyStockTests(InventoryRuleTestCase):
    def test_safety_stock_is_carried_and_never_subtracted(self) -> None:
        records = [INVENTORY(on_hand="100"), INVENTORY(on_hand="30")]
        _accepted, _construction, result, target = self.single_target_report(
            records, safety_stock=CONFIGURED_SAFETY_STOCK("30"), name="safety-stock"
        )
        self.assertIsNone(target.outcome)
        payload = target.to_dict()
        self.assertEqual(payload["OpeningUsableInventory"], "130")
        self.assertEqual(payload["SafetyStock"], "30")
        # Never pre-subtracted into 100, and no unapproved derived concept is produced.
        self.assertNotIn("NetInventoryAfterSafetyStock", json.dumps(payload))
        self.assertNotIn("UsableInventoryMinusBuffer", json.dumps(payload))
        assert target.safety_stock_provenance is not None
        self.assertEqual(
            target.safety_stock_provenance.logical_dataset_role,
            "Configured Safety Stock",
        )
        self.assertEqual(
            target.safety_stock_provenance.stable_source_evidence_locators,
            (EVIDENCE_SAFETY_STOCK,),
        )
        self.assertEqual(result.rule_issues, ())

    def test_safety_stock_zero_is_valid_and_not_missing(self) -> None:
        _accepted, _construction, _result, target = self.single_target_report(
            [INVENTORY(on_hand="100")],
            safety_stock=CONFIGURED_SAFETY_STOCK("0"),
            name="safety-stock-zero",
        )
        self.assertIsNone(target.outcome)
        self.assertEqual(target.to_dict()["SafetyStock"], "0")
        self.assertIsNotNone(target.safety_stock)

    def test_conflicting_configured_safety_stock_is_present_but_unresolved(self) -> None:
        """``5`` + ``7`` on one grain is a conflict, never a missing value."""

        _accepted, construction, result, target = self.single_target_report(
            [INVENTORY(on_hand="130")],
            safety_stock=[
                CONFIGURED_SAFETY_STOCK("5"),
                CONFIGURED_SAFETY_STOCK("7"),
            ],
            name="safety-stock-conflict",
        )
        # The canonical layer keeps both records unresolved and reports the conflict.
        self.assertEqual(construction.objects_for("Configured Safety Stock"), ())
        self.assertEqual(len(construction.unresolved_for("Configured Safety Stock")), 2)
        self.assertIn(
            ("CONSISTENCY", "CONSISTENCY_CONFLICT"),
            [(issue.category, issue.reason) for issue in construction.issues],
        )

        self.assertIsNone(target.safety_stock)
        self.assertEqual(target.outcome, INVENTORY_DATA_INCOMPLETE)
        self.assertEqual(target.safety_stock_state, SAFETY_STOCK_STATE_UNRESOLVED)
        # The upstream conflict is retained and no synthetic MISSING is manufactured.
        self.assertIn(
            ("CONSISTENCY", "CONSISTENCY_CONFLICT"),
            [(issue.category, issue.reason) for issue in target.inherited_issues],
        )
        self.assertIn(
            ("CONSISTENCY", "CONSISTENCY_CONFLICT"),
            [(issue.category, issue.reason) for issue in result.issues],
        )
        self.assertNotIn("MISSING", [issue.reason for issue in result.issues])
        self.assertNotIn("MISSING", [issue.reason for issue in result.rule_issues])
        self.assertTrue(any("present-but-unresolved" in note for note in target.notes))

    def test_equal_valued_configured_safety_stock_is_not_deduplicated(self) -> None:
        """``5`` + ``5`` is never auto-deduplicated into one value and never "missing"."""

        _accepted, construction, result, target = self.single_target_report(
            [INVENTORY(on_hand="130")],
            safety_stock=[
                CONFIGURED_SAFETY_STOCK("5"),
                CONFIGURED_SAFETY_STOCK("5"),
            ],
            name="safety-stock-duplicate",
        )
        self.assertEqual(construction.objects_for("Configured Safety Stock"), ())
        self.assertEqual(len(construction.unresolved_for("Configured Safety Stock")), 2)
        # No equal-value conflict issue is registered anywhere (§4.4.102 C Stage A), and the
        # rule must not invent one -- but the value is also not silently taken.
        self.assertEqual(construction.issues, ())
        self.assertIsNone(target.safety_stock)
        self.assertEqual(target.outcome, INVENTORY_DATA_INCOMPLETE)
        self.assertEqual(target.safety_stock_state, SAFETY_STOCK_STATE_UNRESOLVED)
        self.assertEqual(result.rule_issues, ())
        self.assertEqual(result.issues, ())
        # Evidence exists, so "missing" would be a lie; the runtime state and note say so.
        self.assertNotEqual(target.safety_stock_state, SAFETY_STOCK_STATE_MISSING)
        self.assertTrue(
            any(
                "present-but-unresolved" in note and "SafetyStock" in note
                for note in target.notes
            )
        )

    def test_missing_safety_stock_is_unresolved_and_never_defaulted(self) -> None:
        _accepted, _construction, result, target = self.single_target_report(
            [INVENTORY(on_hand="130")],
            safety_stock=None,
            name="safety-stock-missing",
        )
        self.assertEqual(target.outcome, INVENTORY_DATA_INCOMPLETE)
        self.assertIsNone(target.safety_stock)
        self.assertIsNone(target.to_dict()["SafetyStock"])
        self.assertEqual(target.safety_stock_state, SAFETY_STOCK_STATE_MISSING)
        # The reliable inventory side stays reported independently (never a normal result:
        # the target outcome is DATA_INCOMPLETE), and 0 is never invented.
        self.assertEqual(target.to_dict()["OpeningUsableInventory"], "130")
        self.assertEqual(
            [(issue.category, issue.reason) for issue in result.rule_issues],
            [("FIELD_VALUE", "MISSING")],
        )

    def test_negative_safety_stock_is_invalid_without_clamp(self) -> None:
        _accepted, _construction, result, target = self.single_target_report(
            [INVENTORY(on_hand="100")],
            safety_stock=CONFIGURED_SAFETY_STOCK("-5"),
            name="safety-stock-negative",
        )
        self.assertEqual(target.outcome, INVENTORY_DATA_INCOMPLETE)
        self.assertIsNone(target.safety_stock)
        self.assertEqual(
            [(issue.category, issue.reason) for issue in result.rule_issues],
            [("FIELD_VALUE", "OUT_OF_DEFINED_RANGE")],
        )

    def test_safety_stock_from_the_injected_policy_context(self) -> None:
        """The I-5 context surface is consumed when no Configured Safety Stock grain exists."""

        policy = SAFETY_STOCK_POLICY("30")
        accepted = self.accepted(
            [
                (ROLE_INVENTORY, [INVENTORY(on_hand="130")]),
                ("Plant / Material identity context", [policy]),
            ],
            name="safety-stock-context",
        )
        scope = self.scope_handoffs(accepted, inventory_ordinals=(0,))
        handoff = SafetyStockHandoff(
            plant_id=PLANT,
            material_code=MATERIAL,
            evidence=self.citation(
                accepted, role="Plant / Material identity context", artifact="1.json"
            ),
            safety_stock_evidence=(
                self.citation(
                    accepted,
                    role="Plant / Material identity context",
                    artifact="1.json",
                    ordinal=0,
                    locator=EVIDENCE_SAFETY_STOCK,
                ),
            ),
            safety_stock="30",
            resolution_basis=BASIS_SAFETY_STOCK,
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-01-31",
                inventory_scope=scope,
                safety_stock=(handoff,),
            ),
        )
        self.assertEqual(len(construction.safety_stock_contexts), 1)
        result = compute_opening_usable_inventory(construction)
        target = result.targets[0]
        self.assertIsNone(target.outcome)
        self.assertEqual(target.to_dict()["SafetyStock"], "30")
        self.assertEqual(target.safety_stock_state, SAFETY_STOCK_STATE_RESOLVED)

    def test_multiple_safety_stock_candidates_stay_unresolved(self) -> None:
        accepted, construction, _result, target = self.single_target_report(
            [INVENTORY(on_hand="100")],
            safety_stock=CONFIGURED_SAFETY_STOCK("30"),
            name="safety-stock-ambiguous",
        )
        # Defensive path: a report that offers a second resolved candidate must not let the
        # rule invent a precedence.
        context = ContextValueReference(
            semantic="SafetyStock",
            grain=(
                CanonicalProperty("plant_id", PLANT),
                CanonicalProperty("material_code", MATERIAL),
            ),
            value="31",
            provenance=target.evaluations[0].provenance,
        )
        tampered = replace(
            construction,
            safety_stock_contexts=construction.safety_stock_contexts + (context,),
        )
        result = compute_opening_usable_inventory(tampered)
        ambiguous = result.targets[0]
        self.assertEqual(ambiguous.outcome, INVENTORY_DATA_INCOMPLETE)
        self.assertIsNone(ambiguous.safety_stock)
        self.assertEqual(ambiguous.safety_stock_state, SAFETY_STOCK_STATE_AMBIGUOUS)
        self.assertEqual(
            [(issue.category, issue.reason) for issue in result.rule_issues],
            [("CONSISTENCY", "CONSISTENCY_CONFLICT")],
        )


class PrerequisiteIndependenceTests(InventoryRuleTestCase):
    def test_ownership_unresolved_produces_no_numeric_result(self) -> None:
        _accepted, construction, result, target = self.single_target_report(
            [INVENTORY(plant="", on_hand="100")],
            safety_stock=CONFIGURED_SAFETY_STOCK("0", plant=""),
            name="ownership-unresolved",
        )
        scope_context = construction.inventory_scope_contexts[0]
        self.assertFalse(scope_context.ownership_resolved)
        evaluation = target.evaluations[0]
        self.assertFalse(evaluation.ownership_resolved)
        self.assertEqual(target.outcome, INVENTORY_DATA_INCOMPLETE)
        self.assertIsNone(target.opening_usable_inventory)
        self.assertIn(
            "UNRESOLVED_IDENTITY", [issue.reason for issue in result.issues]
        )

    def test_incomplete_grain_is_never_pushed_into_another_target(self) -> None:
        accepted = self.accepted(
            [
                (
                    ROLE_INVENTORY,
                    [
                        INVENTORY(on_hand="100"),
                        INVENTORY(snapshot_time=None, on_hand="999"),
                    ],
                ),
                ("Configured Safety Stock", [CONFIGURED_SAFETY_STOCK("0")]),
            ],
            name="grain-vs-scope",
        )
        scope = self.scope_handoffs(accepted, inventory_ordinals=(0, 1))
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1", analysis_date="2026-01-31", inventory_scope=scope
            ),
        )
        incomplete_reference = construction.unresolved_for(ROLE_INVENTORY)[0].record_reference
        # Ownership and scope are resolved independently of the incomplete grain.
        context = construction.inventory_scope_for(incomplete_reference)
        assert context is not None
        self.assertTrue(context.ownership_resolved)
        self.assertTrue(context.scope_resolved)

        result = compute_opening_usable_inventory(construction)
        self.assertEqual(len(result.targets), 1)
        target = result.targets[0]
        self.assertEqual(len(target.evaluations), 1)
        self.assertNotIn(
            incomplete_reference,
            [item.inventory_reference for item in target.evaluations],
        )
        # It is neither lent to this grain nor used to invent a target, and its upstream
        # finding is preserved for the downstream fail-safe.
        self.assertEqual(target.to_dict()["OpeningUsableInventory"], "100")
        self.assertEqual(
            result.unassigned_inventory_references, (incomplete_reference,)
        )
        self.assertIn(
            "UNRESOLVED_IDENTITY", [issue.reason for issue in result.inherited_issues]
        )

    def test_inventory_scope_for_decides_scope_and_not_the_rule(self) -> None:
        """The rule consumes the I-9 context; it never re-derives scope itself."""

        _accepted, construction, result, target = self.single_target_report(
            [INVENTORY(on_hand="100")],
            safety_stock=CONFIGURED_SAFETY_STOCK("0"),
            name="scope-consumed",
        )
        evaluation = target.evaluations[0]
        context = construction.inventory_scope_for(evaluation.inventory_reference)
        assert context is not None
        self.assertTrue(evaluation.scope_present)
        self.assertEqual(evaluation.scope_state, SCOPE_STATE_IN_SCOPE)
        self.assertEqual(evaluation.in_scope, context.in_scope)
        self.assertEqual(evaluation.scope_mapping_basis, context.mapping_basis)
        self.assertEqual(evaluation.scope_provenance, context.provenance)

    def test_no_i9_context_is_unresolved_and_never_defaulted(self) -> None:
        """A missing I-9 resolution leaves ownership and scope unresolved, never defaulted."""

        accepted = self.accepted(
            [
                (ROLE_INVENTORY, [INVENTORY(on_hand="100")]),
                ("Configured Safety Stock", [CONFIGURED_SAFETY_STOCK("0")]),
            ],
            name="no-i9-context",
        )
        construction = construct_canonical_objects(
            accepted, PhaseAHandoff(analysis_run_id="RUN-1", analysis_date="2026-01-31")
        )
        # The seam records an unresolved scope context; the rule must not duplicate the
        # upstream finding, must not default the observation into the aggregate.
        self.assertEqual(len(construction.inventory_scope_contexts), 1)
        self.assertFalse(construction.inventory_scope_contexts[0].scope_resolved)

        result = compute_opening_usable_inventory(construction)
        target = result.targets[0]
        self.assertEqual(target.outcome, INVENTORY_DATA_INCOMPLETE)
        self.assertIsNone(target.opening_usable_inventory)
        evaluation = target.evaluations[0]
        self.assertTrue(evaluation.scope_present)
        self.assertFalse(evaluation.scope_resolved)
        self.assertIsNone(evaluation.in_scope)
        self.assertEqual(result.rule_issues, ())
        self.assertEqual(
            [(issue.category, issue.reason) for issue in result.issues],
            [("SCOPE_COVERAGE", "UNRESOLVED_SCOPE")],
        )

        # Defensive path: no scope context at all.  The upstream scope finding still exists in
        # the construction report, so the rule reports only the missing ownership and never
        # duplicates the upstream scope defect; both stay visible on the combined surface and
        # the observation is never defaulted included or excluded.
        tampered = replace(construction, inventory_scope_contexts=())
        missing = compute_opening_usable_inventory(tampered)
        absent = missing.targets[0]
        self.assertEqual(absent.outcome, INVENTORY_DATA_INCOMPLETE)
        self.assertIsNone(absent.opening_usable_inventory)
        self.assertFalse(absent.evaluations[0].scope_present)
        self.assertIsNone(absent.evaluations[0].in_scope)
        self.assertEqual(
            sorted((issue.category, issue.reason) for issue in missing.rule_issues),
            [("IDENTITY_RESOLUTION", "UNRESOLVED_IDENTITY")],
        )
        self.assertEqual(
            sorted((issue.category, issue.reason) for issue in missing.issues),
            [
                ("IDENTITY_RESOLUTION", "UNRESOLVED_IDENTITY"),
                ("SCOPE_COVERAGE", "UNRESOLVED_SCOPE"),
            ],
        )


class OutputAndTraceTests(InventoryRuleTestCase):
    def test_result_shape_and_deterministic_repeatability(self) -> None:
        records = [
            INVENTORY(on_hand="100"),
            INVENTORY(on_hand="30"),
            INVENTORY(on_hand="40", status="INSPECTION"),
        ]
        accepted, construction, result, target = self.single_target_report(
            records,
            safety_stock=CONFIGURED_SAFETY_STOCK("30"),
            name="determinism",
            out_of_scope_ordinals=(),
        )
        accepted_report_after = construction.to_dict()
        self.assertEqual(result.to_dict()["rule"], INVENTORY_RULE_ID)
        payload = result.to_dict()
        self.assertIn("targets", payload)
        self.assertIn("unassigned_inventory_references", payload)
        self.assertIn("inherited_issues", payload)
        self.assertIn("rule_issues", payload)
        for field in (
            "plant_id",
            "material_code",
            "inventory_snapshot_time",
            "OpeningUsableInventory",
            "SafetyStock",
            "safety_stock_state",
            "outcome",
            "inventory_evaluations",
            "safety_stock_provenance",
        ):
            with self.subTest(field=field):
                self.assertIn(field, target.to_dict())
        for field in (
            "inventory_reference",
            "scope_state",
            "in_scope",
            "inventory_status",
            "on_hand_qty",
            "contribution",
            "exclusion_reason",
            "outcome",
            "provenance",
        ):
            with self.subTest(field=field):
                self.assertIn(field, target.evaluations[0].to_dict())
        json.dumps(payload)
        # The rule is a pure function of the construction result: nothing is mutated and the
        # same input reproduces the same runtime objects and the same serialized output.
        self.assertEqual(construction.to_dict(), accepted_report_after)
        second_construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-01-31",
                inventory_scope=self.scope_handoffs(
                    accepted, inventory_ordinals=(0, 1, 2)
                ),
            ),
        )
        second = compute_opening_usable_inventory(second_construction)
        self.assertEqual(second.to_dict(), payload)
        self.assertEqual(result.targets, second.targets)

    def test_lookups_and_provenance_are_retained(self) -> None:
        records = [INVENTORY(on_hand="100"), INVENTORY(on_hand="500")]
        _accepted, _construction, result, target = self.single_target_report(
            records,
            safety_stock=CONFIGURED_SAFETY_STOCK("30"),
            name="provenance",
            out_of_scope_ordinals=(1,),
        )
        self.assertEqual(result.for_grain(PLANT, MATERIAL, SNAPSHOT_TIME), target)
        self.assertIsNone(result.for_grain(PLANT, MATERIAL, SNAPSHOT_TIME_B))
        self.assertEqual(len(result.for_plant_material(PLANT, MATERIAL)), 1)
        contributing = target.contributing_evaluations
        self.assertEqual(len(contributing), 1)
        self.assertIn("|Inventory Snapshot|", contributing[0].inventory_reference)
        assert contributing[0].provenance is not None
        self.assertEqual(
            contributing[0].provenance.logical_dataset_role, ROLE_INVENTORY
        )
        # The excluded observation keeps its own trace: reference, reason and scope provenance.
        excluded = target.excluded_evaluations
        self.assertEqual(len(excluded), 1)
        self.assertEqual(excluded[0].exclusion_reason, EXCLUSION_OUT_OF_SCOPE)
        assert excluded[0].scope_provenance is not None
        self.assertEqual(
            excluded[0].scope_provenance.logical_observation, "plant_id"
        )
        self.assertEqual(
            excluded[0].scope_provenance.mapping_resolution_basis, BASIS_A_OUT
        )
        self.assertEqual(
            {item["inventory_reference"] for item in target.to_dict()["inventory_evaluations"]},
            {item.inventory_reference for item in target.evaluations},
        )

    def test_no_warehouse_identity_is_created(self) -> None:
        _accepted, _construction, result, target = self.single_target_report(
            [INVENTORY(on_hand="100")],
            safety_stock=CONFIGURED_SAFETY_STOCK("0"),
            name="no-warehouse",
        )
        payload = json.dumps(result.to_dict())
        for forbidden in ("warehouse_id", "warehouse_code", "canonical_warehouse"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, payload)

    def test_no_downstream_derived_concepts_are_produced(self) -> None:
        _accepted, _construction, result, _target = self.single_target_report(
            [INVENTORY(on_hand="100")],
            safety_stock=CONFIGURED_SAFETY_STOCK("30"),
            name="no-downstream",
        )
        payload = json.dumps(result.to_dict())
        for forbidden in (
            "ProjectedAvailable",
            "Classification",
            "ShortageQty",
            "BufferGap",
            "FirstShortageDate",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, payload)


if __name__ == "__main__":
    unittest.main()
