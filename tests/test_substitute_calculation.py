"""``BR-SUBSTITUTE-001`` -- Cumulative Approved Substitute Supply acceptance tests.

Covers ``Issue #148`` AC-1 ～ AC-55: the exact formula, the Relationship <-> Allocation join,
the approved ``B1-A`` eligible-substitute-supply consumption boundary, the approved ``B2-A'``
exact Source Demand Context conservation, the approved ``Option A'-R`` allocation multiplicity
retention, the ``DATA_INCOMPLETE`` boundary, provenance ／ determinism and failure isolation.

All fixtures are SIMULATED.  Every assertion is on the **runtime** behaviour of the rule.
"""

from __future__ import annotations

import shutil
import unittest
import uuid
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from typing import Any

from snapshot_loader import (
    InventoryScopeHandoff,
    PhaseAHandoff,
    TrustedInputBoundary,
    compute_opening_usable_inventory,
    compute_substitute_supply,
    construct_canonical_objects,
    load_package,
)
from snapshot_loader.canonical_objects import (
    EffectiveDemandRelationHandoff,
    HandoffEvidence,
    SAME_GRAIN_MULTIPLICITY_TARGETS,
)
from snapshot_loader.exact_quantity import ExactQuantity
from snapshot_loader.inventory_calculation import INVENTORY_RULE_ID
from snapshot_loader.substitute_calculation import (
    CONSERVATION_OVER_ALLOCATED,
    CONSERVATION_OVERLAP_UNRESOLVED,
    CONSERVATION_SOURCE_SUPPLY_UNRESOLVED,
    CONSERVATION_WITHIN_LIMIT,
    SUBSTITUTE_RULE_ID,
    _allocation_index,
    _evaluate_target_outcome,
    _relationship_index,
)
from tests.helpers import DatasetSpec, PackageSpec, build_package

SCRATCH_ROOT = Path(__file__).resolve().parents[1] / "build" / "test-scratch"

PLANT = "P1"
PLANT_B = "P2"
TARGET = "M1"
SOURCE = "M3"

R1 = "2026-10-10"
R2 = "2026-10-20"
S1 = "2026-10-12"
S2 = "2026-11-01"

SNAPSHOT_TIME = "2026-10-01T08:00:00Z"
SNAPSHOT_TIME_B = "2026-10-02T08:00:00Z"

ROLE_RELATIONSHIP = "Substitute Relationship"
ROLE_ALLOCATION = "Substitute Allocation"
ROLE_INVENTORY = "Inventory Snapshot"
ROLE_REQUIREMENT = "Production Requirement"

LOCATOR_ALLOCATION = "SIMULATED-SRC-SUBST-ALLOC-1"
LOCATOR_RELATIONSHIP = "SIMULATED-SRC-SUBST-REL-1"
LOCATOR_INVENTORY = "SIMULATED-SRC-INV-1"
LOCATOR_REQUIREMENT = "SIMULATED-SRC-REQ-1"

BASIS_TA_APPLICABLE = "SIMULATED-G5A-TA-APPLICABLE"
BASIS_TA_NOT_APPLICABLE = "SIMULATED-G5A-TA-NOT-APPLICABLE"
BASIS_TA_UNRESOLVED = "SIMULATED-G5A-TA-UNRESOLVED"
BASIS_SRO_OVERLAPS = "SIMULATED-G5A-SRO-OVERLAPS"
BASIS_SRO_NO_OVERLAP = "SIMULATED-G5A-SRO-NO-OVERLAP"
BASIS_SRO_UNRESOLVED = "SIMULATED-G5A-SRO-UNRESOLVED"

BASIS_IN_SCOPE = "SIMULATED-INV-SCOPE-A-IN"

TARGET_RELATION = "Target Applicability"
SOURCE_RELATION = "Source Reservation Overlap"

DATA_INCOMPLETE = "DATA_INCOMPLETE"


# --- record builders ---------------------------------------------------------------


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


def RELATIONSHIP(
    *,
    plant: Any = PLANT,
    target: Any = TARGET,
    source: Any = SOURCE,
    ratio: Any = "1.0",
    approval: Any = "APPROVED",
) -> dict[str, object]:
    record: dict[str, object] = {}
    if plant is not None:
        record["plant_id"] = plant
    if target is not None:
        record["target_material_code"] = target
    if source is not None:
        record["substitute_material_code"] = source
    if ratio is not None:
        record["substitution_ratio"] = ratio
    if approval is not None:
        record["approval_status"] = approval
    return with_provenance(
        record, [("substitution_ratio", [LOCATOR_RELATIONSHIP], None)]
    )


def ALLOCATION(
    *,
    plant: Any = PLANT,
    target: Any = TARGET,
    source: Any = SOURCE,
    quantity: Any = "60",
    target_basis: str | None = BASIS_TA_APPLICABLE,
    source_basis: str | None = None,
) -> dict[str, object]:
    record: dict[str, object] = {}
    if plant is not None:
        record["plant_id"] = plant
    if target is not None:
        record["target_material_code"] = target
    if source is not None:
        record["substitute_material_code"] = source
    if quantity is not None:
        record["AllocatedSubstituteQty"] = quantity
    associations: list[tuple[str, list[str], str | None]] = []
    if target_basis is not None:
        associations.append(("target_material_code", [LOCATOR_ALLOCATION], target_basis))
    if source_basis is not None:
        associations.append(
            ("substitute_material_code", [LOCATOR_ALLOCATION], source_basis)
        )
    return with_provenance(record, associations)


def INVENTORY_RECORD(
    *,
    plant: Any = PLANT,
    material: Any = SOURCE,
    snapshot_time: Any = SNAPSHOT_TIME,
    status: Any = "AVAILABLE",
    on_hand: Any = "100",
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
    return with_provenance(
        record, [("plant_id", [LOCATOR_INVENTORY], BASIS_IN_SCOPE)]
    )


def REQUIREMENT(
    *,
    plant: Any = PLANT,
    material: Any = TARGET,
    required_date: Any = R1,
    quantity: Any = "10",
) -> dict[str, object]:
    record: dict[str, object] = {}
    if plant is not None:
        record["plant_id"] = plant
    if material is not None:
        record["material_code"] = material
    if required_date is not None:
        record["required_date"] = required_date
    if quantity is not None:
        record["ProductionQty"] = quantity
    return with_provenance(record, [("ProductionQty", [LOCATOR_REQUIREMENT], None)])


# --- scaffolding -------------------------------------------------------------------


class SubstituteRuleTestCase(unittest.TestCase):
    """Shared scaffolding: one accepted package per subtest directory."""

    def setUp(self) -> None:
        self.boundary = SCRATCH_ROOT / f"substitute-rule-{uuid.uuid4().hex}"
        self.boundary.mkdir(parents=True, exist_ok=True)
        self.addCleanup(shutil.rmtree, self.boundary, ignore_errors=True)

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

    def citation(
        self,
        accepted,
        *,
        role: str,
        artifact: str,
        ordinal: int = 0,
        locator: str | None = None,
    ) -> HandoffEvidence:
        return HandoffEvidence(
            snapshot_package_identity=accepted.package_id,
            logical_dataset_role=role,
            artifact=artifact,
            record_ordinal=ordinal,
            evidence_locator=locator,
        )

    def demand_entry(
        self,
        accepted,
        *,
        relation: str,
        basis: str,
        allocation_artifact: str,
        allocation_ordinal: int,
        context_artifact: str,
        context_ordinal: int,
        target: Any = TARGET,
        source: Any = SOURCE,
    ) -> EffectiveDemandRelationHandoff:
        return EffectiveDemandRelationHandoff(
            source_substitute_material=source,
            target_material=target,
            relation=relation,
            evidence=self.citation(
                accepted,
                role=ROLE_ALLOCATION,
                artifact=allocation_artifact,
                ordinal=allocation_ordinal,
                locator=LOCATOR_ALLOCATION,
            ),
            mapping_basis=basis,
            context_citation=self.citation(
                accepted,
                role=ROLE_REQUIREMENT,
                artifact=context_artifact,
                ordinal=context_ordinal,
                locator=LOCATOR_REQUIREMENT,
            ),
        )

    def scope_handoffs(self, accepted, *, artifact: str, ordinals: tuple[int, ...]):
        return tuple(
            InventoryScopeHandoff(
                inventory_evidence=self.citation(
                    accepted,
                    role=ROLE_INVENTORY,
                    artifact=artifact,
                    ordinal=ordinal,
                    locator=LOCATOR_INVENTORY,
                ),
                scope_observation="plant_id",
                scope_resolution_basis=BASIS_IN_SCOPE,
            )
            for ordinal in ordinals
        )

    def run_package(
        self,
        datasets: list[tuple[str, list[dict[str, object]]]],
        *,
        demand: tuple = (),
        scope: tuple = (),
        name: str | None = None,
    ):
        accepted = self.accepted(datasets, name=name)
        handoff = PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-10-01",
            inventory_scope=scope,
            effective_demand=demand,
        )
        construction = construct_canonical_objects(accepted, handoff)
        inventory = compute_opening_usable_inventory(construction)
        return (
            accepted,
            construction,
            inventory,
            compute_substitute_supply(construction, inventory),
        )

    # --- scenario builders -----------------------------------------------------------

    def target_scenario(
        self,
        *,
        quantities: tuple[Any, ...] = ("60",),
        ratio: Any = "1.0",
        approval: Any = "APPROVED",
        on_hand: Any = "100",
        with_inventory: bool = True,
        target_bases: tuple[str | None, ...] | None = None,
        requirements: tuple[dict[str, object], ...] = (),
        context_ordinals: tuple[int, ...] | None = None,
        name: str | None = None,
    ):
        """One target-context scenario with one or more same-grain allocations."""

        bases = target_bases or tuple(BASIS_TA_APPLICABLE for _ in quantities)
        allocations = [
            ALLOCATION(quantity=quantity, target_basis=basis)
            for quantity, basis in zip(quantities, bases)
        ]
        requirement_records = [REQUIREMENT(), *requirements]
        datasets: list[tuple[str, list[dict[str, object]]]] = [
            (ROLE_ALLOCATION, allocations),
            (ROLE_RELATIONSHIP, [RELATIONSHIP(ratio=ratio, approval=approval)]),
            (ROLE_REQUIREMENT, requirement_records),
        ]
        if with_inventory:
            datasets.insert(1, (ROLE_INVENTORY, [INVENTORY_RECORD(on_hand=on_hand)]))
        accepted = self.accepted(datasets, name=name)
        requirement_artifact = f"{len(datasets) - 1}.json"
        ordinals = context_ordinals or tuple(0 for _ in quantities)
        demand = tuple(
            self.demand_entry(
                accepted,
                relation=TARGET_RELATION,
                basis=bases[index],
                allocation_artifact="0.json",
                allocation_ordinal=index,
                context_artifact=requirement_artifact,
                context_ordinal=ordinals[index],
            )
            for index in range(len(allocations))
        )
        scope = (
            self.scope_handoffs(accepted, artifact="1.json", ordinals=(0,))
            if with_inventory
            else ()
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-10-01",
                inventory_scope=scope,
                effective_demand=demand,
            ),
        )
        inventory = compute_opening_usable_inventory(construction)
        return (
            accepted,
            construction,
            inventory,
            compute_substitute_supply(construction, inventory),
        )

    def source_scenario(
        self,
        *,
        quantities: tuple[Any, ...] = ("60",),
        sides: tuple[str | None, ...] | None = None,
        on_hand: Any = "100",
        inventory_records: list[dict[str, object]] | None = None,
        source_requirements: tuple[dict[str, object], ...] = (),
        context_ordinals: tuple[int, ...] | None = None,
        name: str | None = None,
        include_scope: bool = True,
    ):
        """One source-context scenario: several allocations citing the same exact context."""

        sides = sides or tuple(BASIS_SRO_OVERLAPS for _ in quantities)
        allocations = [
            ALLOCATION(quantity=quantity, target_basis=None, source_basis=side)
            for quantity, side in zip(quantities, sides)
        ]
        requirements = [
            REQUIREMENT(),
            *(
                source_requirements
                or (REQUIREMENT(material=SOURCE, required_date=S1),)
            ),
        ]
        records = inventory_records if inventory_records is not None else [
            INVENTORY_RECORD(on_hand=on_hand)
        ]
        datasets: list[tuple[str, list[dict[str, object]]]] = [
            (ROLE_ALLOCATION, allocations),
            (ROLE_INVENTORY, records),
            (ROLE_RELATIONSHIP, [RELATIONSHIP()]),
            (ROLE_REQUIREMENT, requirements),
        ]
        accepted = self.accepted(datasets, name=name)
        requirement_artifact = "3.json"
        ordinals = context_ordinals or tuple(1 for _ in quantities)
        demand = tuple(
            self.demand_entry(
                accepted,
                relation=SOURCE_RELATION,
                basis=sides[index],
                allocation_artifact="0.json",
                allocation_ordinal=index,
                context_artifact=requirement_artifact,
                context_ordinal=ordinals[index],
            )
            for index in range(len(allocations))
        )
        scope = (
            self.scope_handoffs(
                accepted, artifact="1.json", ordinals=tuple(range(len(records)))
            )
            if include_scope
            else ()
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-10-01",
                inventory_scope=scope,
                effective_demand=demand,
            ),
        )
        inventory = compute_opening_usable_inventory(construction)
        return (
            accepted,
            construction,
            inventory,
            compute_substitute_supply(construction, inventory),
        )


# --- AC-1 ～ AC-5 : calculation correctness -----------------------------------------


class CalculationCorrectnessTests(SubstituteRuleTestCase):
    def test_ac1_unit_ratio_yields_the_allocated_quantity(self) -> None:
        """AC-1: 60 x 1.0 = 60 (§2.3.13 Example A)."""

        _a, _c, _i, result = self.target_scenario(
            quantities=("60",), ratio="1.0", name="ac1"
        )
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        self.assertIsNone(target.outcome)
        self.assertEqual(target.cumulative_approved_substitute_supply, Fraction(60))

    def test_ac2_conversion_ratio(self) -> None:
        """AC-2: 60 x 0.8 = 48 (§2.3.13 Example B)."""

        _a, _c, _i, result = self.target_scenario(
            quantities=("60",), ratio="0.8", name="ac2"
        )
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        self.assertEqual(target.cumulative_approved_substitute_supply, Fraction(48))

    def test_ac3_zero_allocation_quantity_is_legal(self) -> None:
        """AC-3: ``AllocatedSubstituteQty = 0`` is valid, contributes 0, not DATA_INCOMPLETE."""

        _a, _c, _i, result = self.target_scenario(quantities=("0",), name="ac3")
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        self.assertFalse(target.data_incomplete)
        self.assertEqual(target.cumulative_approved_substitute_supply, Fraction(0))

    def test_ac4_multiple_same_grain_allocations_sum(self) -> None:
        """AC-4: several same-grain allocations of one target context are summed."""

        _a, construction, _i, result = self.target_scenario(
            quantities=("60", "40"), ratio="1.0", name="ac4"
        )
        self.assertEqual(len(construction.objects_for(ROLE_ALLOCATION)), 2)
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        self.assertIsNone(target.outcome)
        self.assertEqual(target.cumulative_approved_substitute_supply, Fraction(100))

    def test_ac5_each_grain_carries_its_own_cumulative_value(self) -> None:
        """AC-5: the cumulative value is scoped to the cited context's own grain."""

        _a, _c, _i, result = self.target_scenario(quantities=("60",), name="ac5")
        self.assertEqual(result.cumulative_for(PLANT, TARGET, R1), Fraction(60))
        self.assertIsNone(result.for_grain(PLANT, TARGET, R2))
        self.assertIsNone(result.cumulative_for(PLANT, TARGET, R2))


# --- AC-6 ～ AC-9 : exact numeric semantics ------------------------------------------


class NumericSemanticsTests(SubstituteRuleTestCase):
    def test_ac6_derived_quantity_is_an_exact_rational_payload(self) -> None:
        """AC-6: no float, no rounding, no quantization (ADR-001 precedent)."""

        _a, _c, _i, result = self.target_scenario(
            quantities=("60",), ratio="0.8", name="ac6"
        )
        payload = result.to_dict()["targets"][0]["CumulativeApprovedSubstituteSupply"]
        self.assertEqual(payload, {"numerator": 48, "denominator": 1})

    def test_ac7_non_representable_ratio_stays_exact(self) -> None:
        """AC-7: a ratio that is not a finite binary fraction stays rational."""

        _a, _c, _i, result = self.target_scenario(
            quantities=("1",), ratio="0.333333333333333333333333333333", name="ac7"
        )
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        payload = target.to_dict()["CumulativeApprovedSubstituteSupply"]
        self.assertGreater(payload["denominator"], 1)

    def test_ac8_ratio_at_or_below_zero_is_data_incomplete(self) -> None:
        """AC-8: ratio ``<= 0`` is never clamped or corrected (§2.3.6)."""

        for index, ratio in enumerate(("0", "-0.5")):
            with self.subTest(ratio=ratio):
                _a, _c, _i, result = self.target_scenario(
                    quantities=("60",), ratio=ratio, name=f"ac8-{index}"
                )
                target = result.for_grain(PLANT, TARGET, R1)
                assert target is not None
                self.assertTrue(target.data_incomplete)
                self.assertEqual(target.outcome, DATA_INCOMPLETE)
                self.assertIsNone(target.cumulative_approved_substitute_supply)

    def test_ac9_missing_or_invalid_allocation_quantity_is_data_incomplete(self) -> None:
        """AC-9: a missing ／ invalid quantity is never defaulted to 0 (§2.3.7)."""

        for index, quantity in enumerate((None, "not-a-number")):
            with self.subTest(quantity=quantity):
                _a, _c, _i, result = self.target_scenario(
                    quantities=(quantity,), name=f"ac9-{index}"
                )
                target = result.for_grain(PLANT, TARGET, R1)
                assert target is not None
                self.assertTrue(target.data_incomplete)
                self.assertIsNone(target.cumulative_approved_substitute_supply)


# --- AC-10 ～ AC-18 : relationship <-> allocation join --------------------------------


class RelationshipJoinTests(SubstituteRuleTestCase):
    def test_ac10_exact_join_key_on_the_registered_grain(self) -> None:
        """AC-10: the join key is plant_id + target_material_code + substitute_material_code."""

        _a, construction, _i, result = self.target_scenario(
            quantities=("60",), ratio="0.5", name="ac10"
        )
        relationships = construction.objects_for(ROLE_RELATIONSHIP)
        allocations = construction.objects_for(ROLE_ALLOCATION)
        self.assertEqual(len(relationships), 1)
        self.assertEqual(len(allocations), 1)
        for name in ("plant_id", "target_material_code", "substitute_material_code"):
            self.assertEqual(
                relationships[0].value_of(name, None),
                allocations[0].value_of(name, None),
            )
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        self.assertEqual(target.cumulative_approved_substitute_supply, Fraction(30))

    def _single_relationship_free_scenario(
        self, *, relationships: list[dict[str, object]], name: str
    ):
        datasets: list[tuple[str, list[dict[str, object]]]] = [
            (ROLE_ALLOCATION, [ALLOCATION(quantity="60")]),
            (ROLE_RELATIONSHIP, relationships),
            (ROLE_REQUIREMENT, [REQUIREMENT()]),
        ]
        accepted = self.accepted(datasets, name=name)
        demand = (
            self.demand_entry(
                accepted,
                relation=TARGET_RELATION,
                basis=BASIS_TA_APPLICABLE,
                allocation_artifact="0.json",
                allocation_ordinal=0,
                context_artifact="2.json",
                context_ordinal=0,
            ),
        )
        return self.run_package(datasets, demand=demand, name=f"{name}-run")

    def test_ac11_present_dataset_with_no_relationship_is_a_legal_zero(self) -> None:
        """AC-11: business states there is no approved substitute -> supply = 0 (§2.3.11 A)."""

        _a, _c, _i, result = self._single_relationship_free_scenario(
            relationships=[], name="ac11"
        )
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        self.assertFalse(target.data_incomplete)
        self.assertEqual(target.cumulative_approved_substitute_supply, Fraction(0))

    def test_ac12_absent_relationship_role_fails_closed(self) -> None:
        """AC-12: an absent Substitute Relationship role is not a legal 0."""

        datasets: list[tuple[str, list[dict[str, object]]]] = [
            (ROLE_ALLOCATION, [ALLOCATION(quantity="60")]),
            (ROLE_REQUIREMENT, [REQUIREMENT()]),
        ]
        accepted = self.accepted(datasets, name="ac12")
        demand = (
            self.demand_entry(
                accepted,
                relation=TARGET_RELATION,
                basis=BASIS_TA_APPLICABLE,
                allocation_artifact="0.json",
                allocation_ordinal=0,
                context_artifact="1.json",
                context_ordinal=0,
            ),
        )
        _a, _c, _i, result = self.run_package(datasets, demand=demand, name="ac12b")
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        self.assertTrue(target.data_incomplete)
        self.assertIn(
            "Substitute Relationship role evidence",
            " ".join(issue.detail for issue in target.issues),
        )

    def test_ac13_exactly_one_relationship_is_used(self) -> None:
        """AC-13: a single relationship on the join grain supplies the conversion."""

        _a, _c, _i, result = self.target_scenario(
            quantities=("20",), ratio="2.5", name="ac13"
        )
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        self.assertEqual(target.cumulative_approved_substitute_supply, Fraction(50))

    def test_ac14_duplicate_relationship_grain_stays_unresolved(self) -> None:
        """AC-14: several relationships on one grain never resolve by first/last wins."""

        _a, construction, _i, result = self._single_relationship_free_scenario(
            relationships=[RELATIONSHIP(ratio="1.0"), RELATIONSHIP(ratio="0.5")],
            name="ac14",
        )
        self.assertEqual(construction.objects_for(ROLE_RELATIONSHIP), ())
        self.assertEqual(len(construction.unresolved_for(ROLE_RELATIONSHIP)), 2)
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        self.assertTrue(target.data_incomplete)

    def test_ac15_unresolved_relationship_grain_is_data_incomplete(self) -> None:
        """AC-15: an unresolved relationship is never silently skipped."""

        _a, construction, _i, result = self._single_relationship_free_scenario(
            relationships=[RELATIONSHIP(source=None)], name="ac15"
        )
        self.assertEqual(construction.objects_for(ROLE_RELATIONSHIP), ())
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        self.assertTrue(target.data_incomplete)

    def test_ac16_approved_relationship_is_eligible(self) -> None:
        """AC-16: only an exact ``APPROVED`` state participates."""

        _a, _c, _i, result = self.target_scenario(
            quantities=("10",), ratio="1.0", approval="APPROVED", name="ac16"
        )
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        self.assertEqual(target.cumulative_approved_substitute_supply, Fraction(10))
        self.assertEqual(target.eligible_target_qty, 1)

    def test_ac17_pending_and_rejected_are_legal_zero(self) -> None:
        """AC-17: valid-but-ineligible states contribute 0 and are not defects (§4.4.89)."""

        for approval in ("PENDING", "REJECTED"):
            with self.subTest(approval=approval):
                _a, _c, _i, result = self.target_scenario(
                    quantities=("60",), approval=approval, name=f"ac17{approval}"
                )
                target = result.for_grain(PLANT, TARGET, R1)
                assert target is not None
                self.assertFalse(target.data_incomplete)
                self.assertEqual(
                    target.cumulative_approved_substitute_supply, Fraction(0)
                )
                self.assertEqual(target.eligible_target_qty, 0)
                self.assertEqual(target.rule_issues, ())

    def test_ac18_missing_or_unknown_approval_is_data_incomplete(self) -> None:
        """AC-18: an undecidable approval state fails closed (§2.3.5)."""

        for index, approval in enumerate((None, "SOMETHING_ELSE", 7)):
            with self.subTest(approval=approval):
                _a, _c, _i, result = self.target_scenario(
                    quantities=("60",), approval=approval, name=f"ac18-{index}"
                )
                target = result.for_grain(PLANT, TARGET, R1)
                assert target is not None
                self.assertTrue(target.data_incomplete)
                self.assertIsNone(target.cumulative_approved_substitute_supply)


# --- AC-19 ～ AC-26 : B1-A eligible substitute supply --------------------------------


class EligibleSupplyBoundaryTests(SubstituteRuleTestCase):
    def test_ac19_supply_is_consumed_from_the_inventory_rule_result(self) -> None:
        """AC-19: only ``OpeningUsableInventory`` is consumed, nothing is re-implemented."""

        _a, _c, _i, result = self.source_scenario(
            quantities=("60",),
            inventory_records=[
                INVENTORY_RECORD(on_hand="100", status="AVAILABLE"),
                INVENTORY_RECORD(on_hand="40", status="INSPECTION"),
            ],
            name="ac19",
        )
        group = result.conservation_groups[0]
        # 100 AVAILABLE only: INSPECTION is excluded by BR-INVENTORY-001, not re-decided here.
        self.assertEqual(group.eligible_substitute_supply, ExactQuantity(100, 0))
        self.assertEqual(
            group.source_supply_provenance.logical_dataset_role, ROLE_INVENTORY
        )

    def test_ac20_eligible_supply_is_plant_and_source_material_scoped(self) -> None:
        """AC-20: a cross-Plant inventory pool never supplies this source material."""

        _a, _c, _i, result = self.source_scenario(
            quantities=("60",),
            inventory_records=[
                INVENTORY_RECORD(on_hand="100"),
                INVENTORY_RECORD(plant=PLANT_B, on_hand="999"),
            ],
            name="ac20",
        )
        group = result.conservation_groups[0]
        self.assertEqual(group.eligible_substitute_supply, ExactQuantity(100, 0))
        self.assertEqual(group.remaining_unallocated_source_supply, ExactQuantity(40, 0))

    def test_ac21_exactly_one_snapshot_target_is_used(self) -> None:
        """AC-21: exactly one reliably consumable InventoryTarget is consumed."""

        _a, _c, _i, result = self.source_scenario(quantities=("60",), name="ac21")
        group = result.conservation_groups[0]
        self.assertIsNone(group.outcome)
        self.assertEqual(group.conservation_state, CONSERVATION_WITHIN_LIMIT)

    def test_ac22_zero_snapshot_targets_is_data_incomplete(self) -> None:
        """AC-22: no inventory target for this source material fails closed."""

        _a, _c, _i, result = self.source_scenario(
            quantities=("60",),
            inventory_records=[],
            name="ac22",
            include_scope=False,
        )
        group = result.conservation_groups[0]
        self.assertTrue(group.data_incomplete)
        self.assertEqual(
            group.conservation_state, CONSERVATION_SOURCE_SUPPLY_UNRESOLVED
        )

    def test_ac23_multiple_snapshots_never_win_or_merge(self) -> None:
        """AC-23: several snapshot targets fail closed -- no earliest/latest, no sum."""

        _a, _c, _i, result = self.source_scenario(
            quantities=("60",),
            inventory_records=[
                INVENTORY_RECORD(on_hand="100", snapshot_time=SNAPSHOT_TIME),
                INVENTORY_RECORD(on_hand="50", snapshot_time=SNAPSHOT_TIME_B),
            ],
            name="ac23",
        )
        group = result.conservation_groups[0]
        self.assertTrue(group.data_incomplete)
        self.assertIsNone(group.eligible_substitute_supply)
        self.assertEqual(
            group.conservation_state, CONSERVATION_SOURCE_SUPPLY_UNRESOLVED
        )
        self.assertIn(
            "no snapshot ever wins",
            " ".join(issue.detail for issue in group.issues),
        )

    def test_ac24_unreliable_inventory_target_propagates_data_incomplete(self) -> None:
        """AC-24: an unreliable inventory target propagates ``DATA_INCOMPLETE``."""

        _a, _c, _i, result = self.source_scenario(
            quantities=("60",),
            inventory_records=[INVENTORY_RECORD(on_hand="-5")],
            name="ac24",
        )
        group = result.conservation_groups[0]
        self.assertTrue(group.data_incomplete)

    def test_ac25_safety_stock_is_not_pre_deducted(self) -> None:
        """AC-25: SafetyStock is a classification threshold, never an inventory deduction."""

        _a, _c, _i, result = self.source_scenario(quantities=("60",), name="ac25")
        group = result.conservation_groups[0]
        self.assertEqual(group.eligible_substitute_supply, ExactQuantity(100, 0))
        self.assertEqual(group.remaining_unallocated_source_supply, ExactQuantity(40, 0))

    def test_ac26_consumed_target_grain_is_plant_and_source_material(self) -> None:
        """AC-26: the consumed target grain is exactly plant_id + source material_code."""

        _a, _c, _i, result = self.source_scenario(quantities=("10",), name="ac26")
        group = result.conservation_groups[0]
        self.assertEqual(group.plant_id, PLANT)
        self.assertEqual(group.source_material_code, SOURCE)
        self.assertEqual(group.eligible_substitute_supply, ExactQuantity(100, 0))


# --- AC-27 ～ AC-32 : target applicability consumption -------------------------------


class TargetApplicabilityTests(SubstituteRuleTestCase):
    def test_ac27_context_grain_comes_from_the_g5a_reference(self) -> None:
        """AC-27: the grain is the cited context's own plant + material + required_date."""

        _a, construction, _i, result = self.target_scenario(
            quantities=("10",), name="ac27"
        )
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        self.assertEqual(
            (target.plant_id, target.material_code, target.required_date),
            (PLANT, TARGET, R1),
        )
        self.assertEqual(len(construction.effective_demand_contexts), 1)

    def test_ac28_applicable_contributes(self) -> None:
        """AC-28: ``applicable`` contributes to that target demand context."""

        _a, _c, _i, result = self.target_scenario(
            quantities=("60",), target_bases=(BASIS_TA_APPLICABLE,), name="ac28"
        )
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        self.assertEqual(target.cumulative_approved_substitute_supply, Fraction(60))

    def test_ac29_not_applicable_is_a_legal_zero_without_issue(self) -> None:
        """AC-29: a reliable ``not applicable`` is 0 and not a defect (§4.4.89)."""

        _a, _c, _i, result = self.target_scenario(
            quantities=("60",), target_bases=(BASIS_TA_NOT_APPLICABLE,), name="ac29"
        )
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        self.assertFalse(target.data_incomplete)
        self.assertEqual(target.cumulative_approved_substitute_supply, Fraction(0))
        self.assertEqual(target.rule_issues, ())

    def test_ac30_unresolved_target_applicability_is_data_incomplete(self) -> None:
        """AC-30: an unresolved target applicability fails closed (§4.4.60 path B)."""

        _a, construction, _i, result = self.target_scenario(
            quantities=("60",),
            target_bases=(BASIS_TA_UNRESOLVED,),
            name="ac30",
        )
        # The registered "unresolved" basis still yields the demand context reference, so the
        # grain stays reachable and the rule -- not a default 0 -- decides the outcome.
        self.assertEqual(len(construction.effective_demand_contexts), 1)
        self.assertIsNone(
            construction.effective_demand_contexts[0].relation_outcome.outcome
        )
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        self.assertTrue(target.data_incomplete)
        self.assertIsNone(target.cumulative_approved_substitute_supply)
        self.assertEqual(target.outcome, DATA_INCOMPLETE)
        self.assertTrue(
            any(issue.reason == "SEMANTIC_UNRESOLVED" for issue in target.issues)
        )

    def test_ac31_uncited_requirement_never_becomes_a_target_grain(self) -> None:
        """AC-31: grains come only from cited contexts; nothing is re-dated or re-counted."""

        _a, _c, _i, result = self.target_scenario(
            quantities=("60",),
            requirements=(REQUIREMENT(required_date=R2),),
            name="ac31",
        )
        self.assertEqual(len(result.targets), 1)
        self.assertEqual(result.cumulative_for(PLANT, TARGET, R1), Fraction(60))
        self.assertIsNone(result.for_grain(PLANT, TARGET, R2))

    def test_ac32_mapping_basis_never_encodes_context_identity(self) -> None:
        """AC-32: the registry literal is context-neutral (CB-1′)."""

        _a, _c, _i, result = self.target_scenario(quantities=("10",), name="ac32")
        self.assertNotIn(R1, BASIS_TA_APPLICABLE)
        self.assertNotIn(R1, BASIS_SRO_OVERLAPS)
        for target in result.targets:
            for evaluation in target.evaluations:
                self.assertNotIn(R1, evaluation.allocation_reference)
                self.assertNotIn(R1, str(evaluation.relationship_reference))


# --- AC-33 ～ AC-40 : B2-A' conservation ---------------------------------------------


class ConservationTests(SubstituteRuleTestCase):
    def test_ac33_grouping_key_is_the_exact_source_context_reference(self) -> None:
        """AC-33: the grouping boundary is the resolved Source Demand Context reference."""

        _a, _c, _i, result = self.source_scenario(quantities=("60",), name="ac33")
        self.assertEqual(len(result.conservation_groups), 1)
        group = result.conservation_groups[0]
        self.assertIn("Production Requirement", group.reservation_context)
        self.assertEqual(group.plant_id, PLANT)
        self.assertEqual(group.source_material_code, SOURCE)

    def test_ac34_same_context_allocations_sum_together(self) -> None:
        """AC-34: allocations of one exact context enter one conservation sum."""

        _a, construction, _i, result = self.source_scenario(
            quantities=("60", "30"), name="ac34"
        )
        self.assertEqual(len(construction.objects_for(ROLE_ALLOCATION)), 2)
        group = result.conservation_groups[0]
        self.assertEqual(group.allocated_substitute_qty, ExactQuantity(90, 0))
        self.assertEqual(group.remaining_unallocated_source_supply, ExactQuantity(10, 0))
        self.assertEqual(group.conservation_state, CONSERVATION_WITHIN_LIMIT)
        self.assertEqual(len(group.allocating_references), 2)

    def test_ac35_does_not_overlap_is_not_in_the_sum(self) -> None:
        """AC-35: ``does not overlap`` stays out of that context's sum."""

        _a, _c, _i, result = self.source_scenario(
            quantities=("60",), sides=(BASIS_SRO_NO_OVERLAP,), name="ac35"
        )
        group = result.conservation_groups[0]
        self.assertEqual(group.allocated_substitute_qty, ExactQuantity(0, 0))
        self.assertEqual(group.remaining_unallocated_source_supply, ExactQuantity(100, 0))
        self.assertEqual(group.allocating_references, ())

    def test_ac36_over_allocation_is_consistency_conflict(self) -> None:
        """AC-36: ``Σ > EligibleSubstituteSupply`` is a conflict, never silent."""

        _a, _c, _i, result = self.source_scenario(quantities=("60", "50"), name="ac36")
        group = result.conservation_groups[0]
        self.assertTrue(group.over_allocated)
        self.assertTrue(group.data_incomplete)
        self.assertIsNone(group.remaining_unallocated_source_supply)
        self.assertTrue(
            any(
                issue.category == "CONSISTENCY"
                and issue.reason == "CONSISTENCY_CONFLICT"
                for issue in group.issues
            )
        )
        self.assertTrue(
            any(issue.reason == "CONSISTENCY_CONFLICT" for issue in result.rule_issues)
        )

    def test_ac37_within_limit_produces_remaining_unallocated_supply(self) -> None:
        """AC-37: ``RemainingUnallocatedSourceSupply = Eligible - Σ >= 0``."""

        _a, _c, _i, result = self.source_scenario(
            quantities=("60",), on_hand="100", name="ac37"
        )
        group = result.conservation_groups[0]
        self.assertEqual(group.eligible_substitute_supply, ExactQuantity(100, 0))
        self.assertEqual(group.allocated_substitute_qty, ExactQuantity(60, 0))
        self.assertEqual(group.remaining_unallocated_source_supply, ExactQuantity(40, 0))
        self.assertEqual(group.conservation_state, CONSERVATION_WITHIN_LIMIT)

    def test_ac38_unresolved_overlap_makes_the_group_data_incomplete(self) -> None:
        """AC-38: an unresolved Source Reservation Overlap fails closed (§4.4.60 path B)."""

        _a, construction, _i, result = self.source_scenario(
            quantities=("60",),
            sides=(BASIS_SRO_UNRESOLVED,),
            name="ac38",
        )
        # The group still forms -- its key is the exact resolved Source Demand Context -- and
        # the unresolved overlap is what makes it DATA_INCOMPLETE.
        self.assertEqual(len(result.conservation_groups), 1)
        group = result.conservation_groups[0]
        self.assertTrue(group.data_incomplete)
        self.assertEqual(group.conservation_state, CONSERVATION_OVERLAP_UNRESOLVED)
        self.assertIsNone(group.remaining_unallocated_source_supply)
        self.assertEqual(group.allocating_references, ())
        self.assertTrue(
            any(issue.reason == "SEMANTIC_UNRESOLVED" for issue in group.issues)
        )

    def test_ac39_different_exact_contexts_are_never_merged(self) -> None:
        """AC-39: different exact Source Demand Contexts are separate groups, never merged."""

        _a, _c, _i, result = self.source_scenario(
            quantities=("60", "50"),
            source_requirements=(
                REQUIREMENT(material=SOURCE, required_date=S1),
                REQUIREMENT(material=SOURCE, required_date=S2),
            ),
            context_ordinals=(1, 2),
            on_hand="100",
            name="ac39",
        )
        # Two distinct contexts => two groups, each with one allocation: no cross-context sum
        # and no inferred overlap.
        self.assertEqual(len(result.conservation_groups), 2)
        for group in result.conservation_groups:
            self.assertFalse(group.over_allocated)
            self.assertIsNone(group.outcome)
        self.assertEqual(
            sorted(
                group.allocated_substitute_qty for group in result.conservation_groups
            ),
            [ExactQuantity(50, 0), ExactQuantity(60, 0)],
        )

    def test_ac40_contexts_are_never_compared_by_date_proximity(self) -> None:
        """AC-40: no proximity inference -- near-date distinct contexts stay distinct."""

        _a, _c, _i, result = self.source_scenario(
            quantities=("60", "50"),
            source_requirements=(
                REQUIREMENT(material=SOURCE, required_date=S1),
                # one day after S1: proximity must never merge the two contexts
                REQUIREMENT(material=SOURCE, required_date="2026-10-13"),
            ),
            context_ordinals=(1, 2),
            on_hand="100",
            name="ac40",
        )
        self.assertEqual(len(result.conservation_groups), 2)
        for group in result.conservation_groups:
            self.assertFalse(group.over_allocated)
            self.assertIsNone(group.outcome)


# --- AC-41 ～ AC-44 and AC-51 ～ AC-55 : allocation resolution boundary --------------


class AllocationResolutionBoundaryTests(SubstituteRuleTestCase):
    def test_ac41_reference_binds_to_its_own_resolved_allocation_object(self) -> None:
        """AC-41: the quantity is taken from the resolved canonical allocation object."""

        _a, construction, _i, result = self.target_scenario(
            quantities=("60",), name="ac41"
        )
        allocations = construction.objects_for(ROLE_ALLOCATION)
        self.assertEqual(len(allocations), 1)
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        evaluation = target.evaluations[0]
        parts = allocations[0].record_reference.split("|")
        self.assertEqual(evaluation.allocation_reference, f"{parts[2]}#{parts[3]}")
        self.assertEqual(
            evaluation.allocation_provenance.snapshot_package_identity,
            construction.package_id,
        )

    def test_ac42_unbound_reference_never_reads_a_raw_record(self) -> None:
        """AC-42: a reference that binds to no resolved allocation yields DATA_INCOMPLETE.

        G5-A only ever emits a reference for evidence it verified in the accepted package, so
        this boundary cannot be produced from an accepted handoff: it is driven directly at
        the rule's own evaluation seam.  The cited allocation does exist in the accepted
        package with ``AllocatedSubstituteQty = 60`` -- only the **binding** is broken -- so a
        rule that read the raw accepted record (or guessed) would wrongly report ``60``
        instead of failing closed.
        """

        _a, construction, _i, result = self.target_scenario(
            quantities=("60",), name="ac42"
        )
        self.assertEqual(len(construction.objects_for(ROLE_ALLOCATION)), 1)
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        source_reference = construction.effective_demand_contexts[0].relation_outcome

        # Same accepted record, but the reference names an ordinal the resolved set does not
        # contain, so ``_full_reference`` cannot hit any resolved Substitute Allocation.
        unbound = replace(
            source_reference,
            provenance=replace(source_reference.provenance, record_ordinal=7),
        )
        evaluation = _evaluate_target_outcome(
            outcome=unbound,
            grain=(PLANT, TARGET, R1),
            allocations=_allocation_index(construction),
            relationships=_relationship_index(construction),
            relationship_present=ROLE_RELATIONSHIP in construction.present_roles,
            relationship_resolved=False,
        )
        self.assertEqual(evaluation.outcome, DATA_INCOMPLETE)
        self.assertTrue(evaluation.data_incomplete)
        self.assertIsNone(evaluation.allocated_substitute_qty)
        self.assertIsNone(evaluation.equivalent_target_qty)
        self.assertTrue(
            any(
                issue.reason == "SEMANTIC_UNRESOLVED"
                for issue in evaluation.rule_issues
            )
        )

    def test_ac43_same_grain_allocations_are_retained_independently(self) -> None:
        """AC-43 (superseded by Option A'-R): multiplicity itself is not DATA_INCOMPLETE."""

        _a, construction, _i, result = self.target_scenario(
            quantities=("60", "50"), name="ac43"
        )
        resolved = construction.objects_for(ROLE_ALLOCATION)
        self.assertEqual(len(resolved), 2)
        self.assertEqual(construction.unresolved_for(ROLE_ALLOCATION), ())
        self.assertEqual(
            sorted(obj.value_of("AllocatedSubstituteQty", None) for obj in resolved),
            ["50", "60"],
        )
        self.assertEqual(len({obj.record_reference for obj in resolved}), 2)
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        self.assertFalse(target.data_incomplete)
        self.assertEqual(target.cumulative_approved_substitute_supply, Fraction(110))

    def test_ac44_the_exception_is_registered_only_for_substitute_allocation(self) -> None:
        """AC-44: the registered multiplicity exception covers role 8 only."""

        self.assertIn(ROLE_ALLOCATION, SAME_GRAIN_MULTIPLICITY_TARGETS)
        self.assertNotIn(ROLE_RELATIONSHIP, SAME_GRAIN_MULTIPLICITY_TARGETS)

    def test_ac51_two_allocations_60_and_50_are_both_consumable(self) -> None:
        """AC-51: both ``60`` and ``50`` are available for downstream consumption."""

        _a, construction, _i, result = self.target_scenario(
            quantities=("60", "50"), name="ac51"
        )
        self.assertEqual(
            sorted(
                obj.value_of("AllocatedSubstituteQty", None)
                for obj in construction.objects_for(ROLE_ALLOCATION)
            ),
            ["50", "60"],
        )
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        self.assertEqual(target.cumulative_approved_substitute_supply, Fraction(110))
        self.assertEqual(
            len(
                {
                    item.allocation_provenance.record_path
                    for item in target.evaluations
                }
            ),
            2,
        )

    def test_ac52_identical_quantities_are_never_deduplicated(self) -> None:
        """AC-52: ``60`` + ``60`` keeps two records -- no same-value dedup."""

        _a, construction, _i, result = self.target_scenario(
            quantities=("60", "60"), name="ac52"
        )
        resolved = construction.objects_for(ROLE_ALLOCATION)
        self.assertEqual(len(resolved), 2)
        self.assertEqual(
            [obj.value_of("AllocatedSubstituteQty", None) for obj in resolved],
            ["60", "60"],
        )
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        self.assertEqual(target.cumulative_approved_substitute_supply, Fraction(120))

    def test_ac53_each_reference_binds_only_its_own_record(self) -> None:
        """AC-53: a reference never borrows another allocation's quantity."""

        _a, _c, _i, result = self.target_scenario(quantities=("60", "50"), name="ac53")
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        by_reference = {
            item.allocation_reference: item.allocated_substitute_qty
            for item in target.evaluations
        }
        self.assertEqual(len(by_reference), 2)
        self.assertEqual(
            sorted(quantity.text() for quantity in by_reference.values()),
            ["50", "60"],
        )
        # The two references are distinct record paths, and each carries its own quantity.
        self.assertEqual(sorted(by_reference), ["0.json#0", "0.json#1"])
        self.assertEqual(by_reference["0.json#0"].text(), "60")
        self.assertEqual(by_reference["0.json#1"].text(), "50")

    def test_ac54_same_context_two_overlaps_allocations_are_both_summed(self) -> None:
        """AC-54: B2-A' conservation includes both ``overlaps`` allocations."""

        _a, _c, _i, result = self.source_scenario(quantities=("60", "30"), name="ac54")
        group = result.conservation_groups[0]
        self.assertEqual(len(group.allocating_references), 2)
        self.assertEqual(group.allocated_substitute_qty, ExactQuantity(90, 0))
        self.assertEqual(group.remaining_unallocated_source_supply, ExactQuantity(10, 0))

    def test_ac55_relationship_duplicate_still_unresolved(self) -> None:
        """AC-55: the exception never leaks into role 7."""

        datasets: list[tuple[str, list[dict[str, object]]]] = [
            (ROLE_ALLOCATION, [ALLOCATION(quantity="60")]),
            (ROLE_RELATIONSHIP, [RELATIONSHIP(ratio="1.0"), RELATIONSHIP(ratio="1.0")]),
            (ROLE_REQUIREMENT, [REQUIREMENT()]),
        ]
        accepted = self.accepted(datasets, name="ac55")
        demand = (
            self.demand_entry(
                accepted,
                relation=TARGET_RELATION,
                basis=BASIS_TA_APPLICABLE,
                allocation_artifact="0.json",
                allocation_ordinal=0,
                context_artifact="2.json",
                context_ordinal=0,
            ),
        )
        _a, construction, _i, result = self.run_package(
            datasets, demand=demand, name="ac55b"
        )
        # Identical values are not deduplicated either: the relationship grain is unresolved.
        self.assertEqual(construction.objects_for(ROLE_RELATIONSHIP), ())
        self.assertEqual(len(construction.unresolved_for(ROLE_RELATIONSHIP)), 2)
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        self.assertTrue(target.data_incomplete)


# --- AC-45 ～ AC-50 : trace, determinism, isolation ----------------------------------


class TraceAndIsolationTests(SubstituteRuleTestCase):
    def test_ac45_result_is_read_only_and_adds_no_persisted_entity(self) -> None:
        """AC-45: the result is derived, in-memory and exported as plain data."""

        _a, _c, _i, result = self.target_scenario(quantities=("60",), name="ac45")
        payload = result.to_dict()
        self.assertEqual(payload["rule"], SUBSTITUTE_RULE_ID)
        self.assertIn("targets", payload)
        self.assertIn("conservation_groups", payload)
        rendered = str(payload)
        for forbidden in (
            "reservation_group",
            "demand_window_id",
            "allocation_period",
            "allocation_id",
        ):
            self.assertNotIn(forbidden, rendered)

    def test_ac46_provenance_is_retained_end_to_end(self) -> None:
        """AC-46: relationship, allocation, G5-A context and inventory provenance survive."""

        _a, _c, _i, result = self.target_scenario(quantities=("60",), name="ac46")
        target = result.for_grain(PLANT, TARGET, R1)
        assert target is not None
        evaluation = target.evaluations[0]
        self.assertEqual(
            evaluation.allocation_provenance.logical_dataset_role, ROLE_ALLOCATION
        )
        self.assertEqual(
            evaluation.relationship_provenance.logical_dataset_role, ROLE_RELATIONSHIP
        )
        self.assertEqual(
            evaluation.demand_context_provenance.logical_dataset_role, ROLE_REQUIREMENT
        )
        self.assertEqual(
            target.to_dict()["evaluations"][0]["allocation_provenance"][
                "accepted_record_path"
            ],
            "0.json#0",
        )

    def test_ac47_determinism_of_results_and_serialisation(self) -> None:
        """AC-47: identical controlled input reproduces identical output."""

        _a, construction, inventory, first = self.target_scenario(
            quantities=("60", "40"), ratio="0.8", name="ac47"
        )
        second = compute_substitute_supply(construction, inventory)
        self.assertEqual(first.to_dict(), second.to_dict())
        _a2, _c2, _i2, third = self.target_scenario(
            quantities=("60", "40"), ratio="0.8", name="ac47b"
        )
        self.assertEqual(
            [
                (
                    item.plant_id,
                    item.material_code,
                    item.required_date,
                    item.cumulative_approved_substitute_supply,
                )
                for item in first.targets
            ],
            [
                (
                    item.plant_id,
                    item.material_code,
                    item.required_date,
                    item.cumulative_approved_substitute_supply,
                )
                for item in third.targets
            ],
        )

    def test_ac48_failure_isolation_between_grains(self) -> None:
        """AC-48: an unreliable context never poisons another context's numeric result."""

        _a, _c, _i, result = self.target_scenario(
            quantities=("60", "bad"),
            requirements=(REQUIREMENT(required_date=R2),),
            context_ordinals=(0, 1),
            name="ac48",
        )
        self.assertEqual(result.cumulative_for(PLANT, TARGET, R1), Fraction(60))
        second = result.for_grain(PLANT, TARGET, R2)
        assert second is not None
        self.assertTrue(second.data_incomplete)
        self.assertEqual(len(result.data_incomplete_targets), 1)

    def test_ac49_only_the_inherited_taxonomy_is_used(self) -> None:
        """AC-49: no new Validation Category ／ Reason ／ status ／ enum."""

        _a, _c, _i, result = self.target_scenario(quantities=("bad",), name="ac49")
        allowed_categories = {"SEMANTIC_RESOLUTION", "CONSISTENCY"}
        allowed_reasons = {"SEMANTIC_UNRESOLVED", "CONSISTENCY_CONFLICT"}
        self.assertTrue(result.issues)
        for issue in result.issues:
            self.assertIn(issue.category, allowed_categories)
            self.assertIn(issue.reason, allowed_reasons)
            self.assertEqual(issue.layer, 2)

    def test_ac50_rule_identities_are_the_registered_ones(self) -> None:
        """AC-50: the rule identities are unchanged (shared-suite regression is separate)."""

        self.assertEqual(SUBSTITUTE_RULE_ID, "BR-SUBSTITUTE-001")
        self.assertEqual(INVENTORY_RULE_ID, "BR-INVENTORY-001")


if __name__ == "__main__":
    unittest.main()
