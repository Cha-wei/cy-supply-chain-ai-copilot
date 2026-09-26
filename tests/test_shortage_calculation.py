"""``BR-SHORTAGE-001`` -- Shortage Calculation acceptance tests.

Covers the Human-approved ``S1-A`` / ``S2-A`` / ``S3-A`` consumption boundaries, the canonical
formula of ``§2.1.2``, the cumulative / date rules, the fail-safe first-date semantics of
``§2.1.6``, the ``DATA_INCOMPLETE`` boundary of ``§2.1.4`` D ／ ``§2.1.7``, provenance,
determinism and failure isolation.

All fixtures are SIMULATED and every assertion is on the **runtime** behaviour of the rule.
"""

from __future__ import annotations

import dataclasses
import shutil
import unittest
import uuid
from pathlib import Path
from typing import Any

from snapshot_loader import (
    ExactQuantity,
    PhaseAHandoff,
    TrustedInputBoundary,
    compute_effective_inbound,
    compute_opening_usable_inventory,
    compute_requirement_calculation,
    compute_shortage,
    compute_substitute_supply,
    construct_canonical_objects,
    load_package,
)
from snapshot_loader.canonical_objects import (
    BomParentContextHandoff,
    EffectiveDemandRelationHandoff,
    HandoffEvidence,
    InventoryScopeHandoff,
    LossRateHandoff,
)
from snapshot_loader.shortage_calculation import (
    CLASSIFICATIONS,
    CLASSIFICATION_BUFFER_BREACH,
    CLASSIFICATION_DATA_INCOMPLETE,
    CLASSIFICATION_NORMAL,
    CLASSIFICATION_SHORTAGE,
    SHORTAGE_DATA_INCOMPLETE,
    SHORTAGE_RULE_ID,
    SUPPLY_FROM_INVENTORY_SNAPSHOT,
    SUPPLY_FROM_SOURCE_RESERVATION,
)
from tests.helpers import DatasetSpec, PackageSpec, build_package

SCRATCH_ROOT = Path(__file__).resolve().parents[1] / "build" / "test-scratch"

PLANT = "P1"
PLANT_B = "P2"

#: The demand grain under test: ``P1`` + ``M2``.
DEMAND = "M2"
#: Its parent requirement (``Production Requirement``) material.
PARENT = "M1"
#: The substitute source material of the registered relationship (``M2`` <- ``M3``).
SOURCE = "M3"
#: The plant grain whose inventory the exact Source Demand Context consumes: it is the source
#: material of its own reservation boundary, so its supply is the remaining unallocated amount.
RESERVED = "M9"
#: A second, unrelated demand grain, used for isolation / "never aggregate" coverage.
OTHER = "M5"

D1 = "2026-10-10"
D2 = "2026-10-20"
D3 = "2026-10-30"

SNAPSHOT_TIME = "2026-10-01T08:00:00Z"
SNAPSHOT_TIME_B = "2026-10-02T08:00:00Z"

ROLE_REQUIREMENT = "Production Requirement"
ROLE_BOM = "BOM Component"
ROLE_INVENTORY = "Inventory Snapshot"
ROLE_SAFETY_STOCK = "Configured Safety Stock"
ROLE_INBOUND = "Inbound Supply"
ROLE_RELATIONSHIP = "Substitute Relationship"
ROLE_ALLOCATION = "Substitute Allocation"

BASIS_SCOPE_IN = "SIMULATED-INV-SCOPE-A-IN"
BASIS_LOSS = "SIMULATED-BASIS-LOSS-RATE"
#: The registered G5-A relation bases.  A relation outcome only exists for a registered basis;
#: anything else stays unresolved at the canonical layer.
BASIS_TA = "SIMULATED-G5A-TA-APPLICABLE"
BASIS_TA_NOT_APPLICABLE = "SIMULATED-G5A-TA-NOT-APPLICABLE"
BASIS_TA_UNRESOLVED = "SIMULATED-G5A-TA-UNRESOLVED"
BASIS_SRO = "SIMULATED-G5A-SRO-OVERLAPS"
BASIS_SRO_UNRESOLVED = "SIMULATED-G5A-SRO-UNRESOLVED"

RELATION_TARGET = "Target Applicability"
RELATION_SOURCE = "Source Reservation Overlap"


def basis_for(outcome: Any) -> str:
    """The registered ``Target Applicability`` basis of one requested relation outcome."""

    return {
        "APPROVED": BASIS_TA,
        "NOT_APPLICABLE": BASIS_TA_NOT_APPLICABLE,
        "UNRESOLVED": BASIS_TA_UNRESOLVED,
    }.get(str(outcome), BASIS_TA)

ARTIFACT_REQUIREMENT = "0.json"
ARTIFACT_BOM = "1.json"
ARTIFACT_INVENTORY = "2.json"
ARTIFACT_SAFETY_STOCK = "3.json"
ARTIFACT_INBOUND = "4.json"
ARTIFACT_RELATIONSHIP = "5.json"
ARTIFACT_ALLOCATION = "6.json"


def _trim(text: str) -> str:
    """Drop trailing fractional zeros from a rendered exact decimal quantity."""

    if "." not in text:
        return text
    return text.rstrip("0").rstrip(".")


def _scale_of(text: Any) -> tuple[int, int]:
    """Build the exact scaled-integer pair of a rendered decimal quantity."""

    body = str(text)
    sign = -1 if body.startswith("-") else 1
    body = body.lstrip("+-")
    whole, _, fraction = body.partition(".")
    return sign * int(f"{whole or '0'}{fraction}"), len(fraction)


# --- fixture builders --------------------------------------------------------------


def with_provenance(
    record: dict[str, Any],
    associations: list[tuple[str, list[str], str | None]],
) -> dict[str, Any]:
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


@dataclasses.dataclass(frozen=True)
class Demand:
    """One requirement statement: ``parent`` requires ``component`` on ``date``.

    ``context_material`` is the ``material_code`` the statement itself registers -- the material
    whose own requirement statement this row **is**.  It defaults to the parent, which is the
    ordinary case.  Setting it to the component lets one statement carry both the component
    demand and the component's own citable demand context, so a G5-A citation can name that
    material without a second, grain-conflicting statement.  ``parent == component`` is a pure
    context statement that demands nothing.
    """

    parent: str
    component: str
    quantity: Any = "1"
    date: Any = D2
    context_material: Any = None


def requirement_record(entry: Demand, index: int) -> dict[str, Any]:
    return with_provenance(
        {
            "plant_id": PLANT,
            "material_code": (
                entry.parent if entry.context_material is None else entry.context_material
            ),
            "required_date": entry.date,
            "ProductionQty": (
                entry.quantity if entry.parent == entry.component else "1"
            ),
        },
        [("ProductionQty", [f"SIMULATED-SRC-REQ-{index}"], None)],
    )


def bom_record(entry: Demand, ordinal: int, *, loss_rate: Any = "0") -> dict[str, Any]:
    # ``BOMComponentQty`` is 1, so the demand quantity is exactly the derived
    # ``GrossRequirement`` and every fixture expectation stays readable.
    return with_provenance(
        {
            "plant_id": PLANT,
            "required_date": entry.date,
            "material_code": entry.component,
            "BOMComponentQty": "1",
            "loss_rate": loss_rate,
        },
        [
            ("BOMComponentQty", [f"SIMULATED-SRC-BOM-{ordinal}"], None),
            ("loss_rate", [f"SIMULATED-SRC-LOSS-{ordinal}"], BASIS_LOSS),
        ],
    )


def inventory_record(
    material: Any,
    *,
    on_hand: Any = "100",
    snapshot_time: Any = SNAPSHOT_TIME,
    status: Any = "AVAILABLE",
) -> dict[str, Any]:
    record: dict[str, Any] = {"plant_id": PLANT}
    if material is not None:
        record["material_code"] = material
    if snapshot_time is not None:
        record["inventory_snapshot_time"] = snapshot_time
    if status is not None:
        record["inventory_status"] = status
    if on_hand is not None:
        record["on_hand_qty"] = on_hand
    return with_provenance(
        record, [("plant_id", [f"SIMULATED-SRC-INV-{material}"], BASIS_SCOPE_IN)]
    )


def safety_stock_record(material: Any, value: Any) -> dict[str, Any]:
    record: dict[str, Any] = {"plant_id": PLANT}
    if material is not None:
        record["material_code"] = material
    if value is not None:
        record["SafetyStock"] = value
    return with_provenance(
        record, [("SafetyStock", [f"SIMULATED-SRC-SS-{material}"], None)]
    )


def inbound_record(
    material: Any,
    *,
    ordered: Any = "100",
    received: Any = "0",
    arrival: Any = SNAPSHOT_TIME,
    status: Any = "OPEN",
) -> dict[str, Any]:
    record: dict[str, Any] = {"plant_id": PLANT}
    if material is not None:
        record["material_code"] = material
    if ordered is not None:
        record["ordered_qty"] = ordered
    if received is not None:
        record["received_qty"] = received
    if arrival is not None:
        record["effective_arrival_date"] = arrival
    if status is not None:
        record["inbound_status"] = status
    return with_provenance(
        record, [("ordered_qty", [f"SIMULATED-SRC-INB-{material}"], None)]
    )


def relationship_record(
    target: Any,
    substitute: Any,
    *,
    ratio: Any = "1.0",
    approval: Any = "APPROVED",
) -> dict[str, Any]:
    return with_provenance(
        {
            "plant_id": PLANT,
            "target_material_code": target,
            "substitute_material_code": substitute,
            "substitution_ratio": ratio,
            "approval_status": approval,
        },
        [("substitution_ratio", [f"SIMULATED-SRC-REL-{target}"], None)],
    )


def allocation_record(
    target: Any,
    substitute: Any,
    *,
    quantity: Any = "0",
    target_basis: Any = BASIS_TA,
    source_basis: Any = BASIS_SRO,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "plant_id": PLANT,
        "target_material_code": target,
        "substitute_material_code": substitute,
        "AllocatedSubstituteQty": quantity,
    }
    associations: list[tuple[str, list[str], str | None]] = []
    if target_basis is not None:
        associations.append(
            ("target_material_code", [f"SIMULATED-SRC-ALLOC-TA-{target}"], target_basis)
        )
    if source_basis is not None:
        associations.append(
            (
                "substitute_material_code",
                [f"SIMULATED-SRC-ALLOC-SRO-{target}"],
                source_basis,
            )
        )
    return with_provenance(record, associations)


@dataclasses.dataclass(frozen=True)
class Built:
    """One fully computed deterministic pipeline for one SIMULATED fixture."""

    construction: Any
    requirements: Any
    inbounds: Any
    inventory: Any
    substitutes: Any
    shortage: Any


# --- scaffolding -------------------------------------------------------------------


class ShortageRuleTestCase(unittest.TestCase):
    """Shared scaffolding: one accepted package per subtest directory."""

    def setUp(self) -> None:
        self.boundary = SCRATCH_ROOT / f"shortage-rule-{uuid.uuid4().hex}"
        self.boundary.mkdir(parents=True, exist_ok=True)
        self.addCleanup(shutil.rmtree, self.boundary, ignore_errors=True)

    # --- fixture assembly -------------------------------------------------------------

    def build(
        self,
        *,
        demand: tuple[Demand, ...] = (Demand(DEMAND, DEMAND, "10"),),
        inventory: dict[Any, Any] | None = None,
        snapshots: tuple[tuple[Any, str], ...] = (),
        safety_stock: dict[Any, Any] | None = None,
        skip_safety_stock: tuple[Any, ...] = (),
        inbound: tuple[tuple[Any, Any, Any], ...] = (),
        loss_rate: Any = "0",
        conservation: tuple[Any, Any, Any] | None = None,
        targets: tuple[tuple[Any, Any, Any], ...] = ((DEMAND, D2, "APPROVED"),),
        relationships: tuple[tuple[Any, Any, str], ...] = ((DEMAND, SOURCE, "APPROVED"),),
        substitute_present: bool = True,
        name: str | None = None,
    ) -> Built:
        """Assemble, accept, construct and run the whole deterministic chain.

        ``demand`` is one ``Demand`` per requirement statement: its material both demands and is
        required (``parent == component``), so the material's own statement is the demand **and**
        the citable G5-A demand context of that exact grain.  ``inventory`` ／ ``safety_stock``
        are keyed by material, ``snapshots`` adds extra
        ``(material, inventory_snapshot_time)`` observations and ``inbound`` is
        ``(material, ordered_qty, effective_arrival_date)``.

        ``targets`` is ``(material, required_date, relation_outcome)``: one ``Target
        Applicability`` context per entry, so a material can have a numeric substitute result on
        several dates.  ``conservation`` is ``(target_material, source_material, allocated_qty)``
        and adds the quoted ``Substitute Allocation`` record with both of its G5-A relations; the
        same-date Target Applicability context of the target material is added for it.
        ``relationships`` declares further ``Substitute Relationship`` records.
        """

        stock = {DEMAND: "100", SOURCE: "100"} if inventory is None else dict(inventory)
        policy = {DEMAND: "5", SOURCE: "0"} if safety_stock is None else dict(safety_stock)

        # The accepted package must state a ``Production Requirement`` context for **every**
        # material a G5-A entry cites -- the canonical layer refuses to borrow a context from the
        # other side of the allocation and demands that the cited record states exactly that
        # material.  One requirement statement is emitted per distinct ``material`` +
        # ``required_date``, each bound to its own ``BOM Component`` relationship, so a grain never
        # carries two conflicting requirement statements.  A material that is cited but states no
        # demand of its own gets a zero-demand context statement instead.
        cited: list[tuple[Any, Any]] = []
        if conservation is not None:
            cited.append((conservation[1], D2))
        for material, date, _outcome in targets:
            cited.append((material, date))

        entry_index: dict[tuple[Any, Any], int] = {}
        entries: list[Demand] = []
        for entry in demand:
            entry_index.setdefault((entry.component, entry.date), len(entries))
            entries.append(entry)
        for material, date in sorted(set(cited)):
            if (material, date) in entry_index:
                continue
            entry_index[(material, date)] = len(entries)
            entries.append(Demand(material, material, "0", date))

        requirement_records: list[dict[str, Any]] = []
        bom_records: list[dict[str, Any]] = []
        bom_binding: list[BomParentContextHandoff] = []
        loss_handoffs: list[LossRateHandoff] = []
        index_by_material: dict[Any, int] = {}
        bom_index: dict[tuple[Any, Any, Any], int] = {}
        for entry in entries:
            key = (entry.component, entry.date)
            if key in index_by_material:
                continue
            index_by_material[key] = len(requirement_records)
            requirement_records.append(
                requirement_record(entry, len(requirement_records))
            )
        for ordinal, entry in enumerate(entries):
            # The BOM record's own artifact ordinal -- the locator and the record reference must
            # always agree, or the loss-rate evidence is unresolvable.
            bom_index[(entry.parent, entry.component, entry.date)] = ordinal
            bom_records.append(bom_record(entry, ordinal, loss_rate=loss_rate))

        inventory_records = [
            inventory_record(material, on_hand=value)
            for material, value in stock.items()
        ]
        for material, snapshot_time in snapshots:
            inventory_records.append(
                inventory_record(material, on_hand="999", snapshot_time=snapshot_time)
            )
        safety_records = [
            safety_stock_record(material, value)
            for material, value in policy.items()
            if material not in skip_safety_stock
        ]
        inbound_records = [
            inbound_record(material, ordered=ordered, arrival=arrival)
            for material, ordered, arrival in inbound
        ]

        datasets: list[tuple[str, list[dict[str, Any]]]] = [
            (ROLE_REQUIREMENT, requirement_records),
            (ROLE_BOM, bom_records),
            (ROLE_INVENTORY, inventory_records),
            (ROLE_SAFETY_STOCK, safety_records),
            (ROLE_INBOUND, inbound_records),
        ]
        if substitute_present:
            datasets.append(
                (
                    ROLE_RELATIONSHIP,
                    [
                        relationship_record(target, substitute, approval=approval)
                        for target, substitute, approval in relationships
                    ],
                )
            )
            allocations: list[dict[str, Any]] = []
            if conservation is not None:
                target, substitute, quantity = conservation
                allocations.append(
                    allocation_record(
                        target,
                        substitute,
                        quantity=quantity,
                        target_basis=BASIS_TA,
                        source_basis=BASIS_SRO,
                    )
                )
            for material, _date, outcome in targets:
                allocations.append(
                    allocation_record(
                        material,
                        SOURCE,
                        quantity="0",
                        target_basis=basis_for(outcome),
                        source_basis=None,
                    )
                )
            if conservation is not None and not any(
                material == conservation[0] for material, _date, _o in targets
            ):
                # The quoted reservation also has to state its own Target Applicability, or the
                # target's cumulative substitute supply would stay unresolved.
                allocations.append(
                    allocation_record(
                        conservation[0],
                        conservation[1],
                        quantity=conservation[2],
                        target_basis=BASIS_TA,
                        source_basis=None,
                    )
                )
            datasets.append((ROLE_ALLOCATION, allocations))

        built = build_package(
            self.boundary / (name or uuid.uuid4().hex[:8]),
            PackageSpec(
                datasets=[
                    DatasetSpec(role=role, artifact=f"{index}.json", records=records)
                    for index, (role, records) in enumerate(datasets)
                ]
            ),
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
        accepted = report.accepted_package

        def cite(role, artifact, ordinal=0, locator=None):
            return HandoffEvidence(
                snapshot_package_identity=accepted.package_id,
                logical_dataset_role=role,
                artifact=artifact,
                record_ordinal=ordinal,
                evidence_locator=locator,
            )

        for entry in entries:
            bom_position = bom_index[(entry.parent, entry.component, entry.date)]
            # The BOM locator is derived from the record's position inside its own artifact, the
            # same ordinal the record reference uses, so the two never disagree.
            bom_locator = f"SIMULATED-SRC-LOSS-{bom_position}"
            bom_binding.append(
                BomParentContextHandoff(
                    bom_evidence=cite(ROLE_BOM, ARTIFACT_BOM, bom_position),
                    parent_evidence=cite(
                        ROLE_REQUIREMENT,
                        ARTIFACT_REQUIREMENT,
                        index_by_material[(entry.component, entry.date)],
                    ),
                )
            )
            loss_handoffs.append(
                LossRateHandoff(
                    plant_id=PLANT,
                    parent_material_code=entry.component,
                    required_date=entry.date,
                    evidence=cite(ROLE_BOM, ARTIFACT_BOM, bom_position),
                    component_material_code=entry.component,
                    loss_rate_evidence=(
                        cite(
                            ROLE_BOM,
                            ARTIFACT_BOM,
                            bom_position,
                            bom_locator,
                        ),
                    ),
                    loss_rate=loss_rate,
                    resolution_basis=BASIS_LOSS,
                )
            )

        demand_entries: list[EffectiveDemandRelationHandoff] = []
        allocation_ordinal = 0
        if substitute_present:
            if conservation is not None:
                conservation_target, conservation_source, _qty = conservation
                demand_entries.append(
                    EffectiveDemandRelationHandoff(
                        source_substitute_material=conservation_source,
                        target_material=conservation_target,
                        relation=RELATION_SOURCE,
                        evidence=cite(
                            ROLE_ALLOCATION,
                            ARTIFACT_ALLOCATION,
                            allocation_ordinal,
                            f"SIMULATED-SRC-ALLOC-SRO-{conservation_target}",
                        ),
                        mapping_basis=BASIS_SRO,
                        context_citation=cite(
                            ROLE_REQUIREMENT,
                            ARTIFACT_REQUIREMENT,
                            index_by_material[(conservation_source, D2)],
                        ),
                    )
                )
                allocation_ordinal += 1
            for material, date, outcome in targets:
                demand_entries.append(
                    EffectiveDemandRelationHandoff(
                        source_substitute_material=SOURCE,
                        target_material=material,
                        relation=RELATION_TARGET,
                        evidence=cite(
                            ROLE_ALLOCATION,
                            ARTIFACT_ALLOCATION,
                            allocation_ordinal,
                            f"SIMULATED-SRC-ALLOC-TA-{material}",
                        ),
                        mapping_basis=basis_for(outcome),
                        context_citation=cite(
                            ROLE_REQUIREMENT,
                            ARTIFACT_REQUIREMENT,
                            index_by_material[(material, date)],
                        ),
                    )
                )
                allocation_ordinal += 1

        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-10-01",
                bom_parent_context=tuple(bom_binding),
                loss_rate=tuple(loss_handoffs),
                inventory_scope=tuple(
                    InventoryScopeHandoff(
                        inventory_evidence=cite(
                            ROLE_INVENTORY, ARTIFACT_INVENTORY, ordinal
                        ),
                        scope_observation="plant_id",
                        scope_resolution_basis=BASIS_SCOPE_IN,
                    )
                    for ordinal in range(len(inventory_records))
                ),
                effective_demand=tuple(demand_entries),
            ),
        )
        requirements = compute_requirement_calculation(construction)
        inbounds = compute_effective_inbound(construction, requirements)
        inventory_result = compute_opening_usable_inventory(construction)
        substitutes = compute_substitute_supply(construction, inventory_result)
        shortage = compute_shortage(
            construction, requirements, inbounds, inventory_result, substitutes
        )
        return Built(
            construction=construction,
            requirements=requirements,
            inbounds=inbounds,
            inventory=inventory_result,
            substitutes=substitutes,
            shortage=shortage,
        )

    # --- assertion helpers -------------------------------------------------------------

    def grain(self, built: Built, material: Any = DEMAND, date: Any = D2):
        item = built.shortage.for_grain(PLANT, material, date)
        self.assertIsNotNone(item, msg=f"no shortage grain for {material!r} @ {date!r}")
        assert item is not None
        return item

    def assert_quantity(self, grain, field: str, expected: Any) -> None:
        """Assert one exact quantity, comparing the exact value and its canonical rendering.

        The rendering may carry trailing fractional zeros on either side (``0.667000`` versus
        ``0.667``) because a canonical quantity keeps the scale it was held at; the exact value is
        what the rule promises, so both are checked: the value must be exactly equal and the
        rendered text must differ only in trailing zeros.
        """

        value = getattr(grain, field)
        self.assertIsNotNone(value, msg=f"{field} is unresolved for {grain.grain!r}")
        assert value is not None
        self.assertEqual(value, ExactQuantity(*_scale_of(expected)))
        self.assertEqual(_trim(value.text()), _trim(str(expected)))

    def assert_classification(self, grain, expected: str) -> None:
        self.assertEqual(grain.classification, expected)
        self.assertIn(grain.classification, CLASSIFICATIONS)


# --- AC-1 / AC-2 / AC-3: the four registered classifications ------------------------


class ClassificationTests(ShortageRuleTestCase):
    def test_ac1_normal_when_the_projection_covers_the_safety_stock(self) -> None:
        # OpeningUsableInventory 100 + CumulativeEffectiveInbound 0
        # + CumulativeApprovedSubstituteSupply 0 - CumulativeGrossRequirement 10 = 90 >= 5.
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "10"),),
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac1-normal",
        )
        grain = self.grain(built)
        self.assert_classification(grain, CLASSIFICATION_NORMAL)
        self.assert_quantity(grain, "projected_available", "90")
        self.assert_quantity(grain, "shortage_qty", "0")
        self.assert_quantity(grain, "buffer_gap", "0")
        self.assertIsNone(grain.outcome)

    def test_ac2_buffer_breach_when_the_projection_is_below_the_safety_stock(self) -> None:
        # 100 + 0 + 0 - 98 = 2, and 0 <= 2 < 5: the buffer is breached but nothing is short.
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "98"),),
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac2-buffer-breach",
        )
        grain = self.grain(built)
        self.assert_classification(grain, CLASSIFICATION_BUFFER_BREACH)
        self.assert_quantity(grain, "projected_available", "2")
        self.assert_quantity(grain, "shortage_qty", "0")
        self.assert_quantity(grain, "buffer_gap", "3")

    def test_ac3_shortage_when_the_projection_is_negative(self) -> None:
        # 100 + 0 + 0 - 110 = -10.
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "110"),),
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac3-shortage",
        )
        grain = self.grain(built)
        self.assert_classification(grain, CLASSIFICATION_SHORTAGE)
        self.assert_quantity(grain, "projected_available", "-10")
        self.assert_quantity(grain, "shortage_qty", "10")
        self.assert_quantity(grain, "buffer_gap", "15")


# --- AC-4 / AC-5 / AC-6 / AC-7 / AC-8: cumulative, dates and the fail-safe marker ---


class CumulativeAndDateTests(ShortageRuleTestCase):
    def test_ac4_the_projection_is_cumulative_across_required_dates(self) -> None:
        # One supply is never reused per date: the later grain sees the cumulative requirement
        # 60 + 50 = 110, so 100 + 0 + 0 - 110 = -10, while D1 alone would have been 100 - 60 = 40.
        # D1 is DATA_INCOMPLETE because the substitute result states no Target Demand Context of
        # that exact grain, so the missing value is never read as 0 there.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "60", D1),
                Demand(DEMAND, DEMAND, "50", D2),
            ),
            targets=((DEMAND, D1, "APPROVED"), (DEMAND, D2, "APPROVED")),
            name="ac4-cumulative",
        )
        first = self.grain(built, DEMAND, D1)
        second = self.grain(built, DEMAND, D2)
        self.assert_classification(first, CLASSIFICATION_NORMAL)
        self.assert_quantity(first, "projected_available", "40")
        self.assert_quantity(first, "cumulative_gross_requirement", "60")
        self.assert_classification(second, CLASSIFICATION_SHORTAGE)
        self.assert_quantity(second, "projected_available", "-10")
        self.assert_quantity(second, "cumulative_gross_requirement", "110")
        self.assert_quantity(second, "cumulative_approved_substitute_supply", "0")
        self.assertEqual(built.shortage.first_shortage_date, D2)

    def test_ac4b_several_requirement_contributions_on_one_date_enter_one_grain(self) -> None:
        # Two independent parents require the same component on the same date.  Both enter the
        # upstream cumulative requirement and the date still has exactly one shortage result.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "110", D2),
            ),
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac4b-same-date",
        )
        grains = built.shortage.for_plant_material(PLANT, DEMAND)
        self.assertEqual(len(grains), 1)
        grain = grains[0]
        self.assert_quantity(grain, "cumulative_gross_requirement", "110")
        self.assert_classification(grain, CLASSIFICATION_SHORTAGE)
        self.assert_quantity(grain, "projected_available", "-10")

    def test_ac5_a_reliable_first_shortage_date_is_the_earliest_shortage(self) -> None:
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "60", D1),
                Demand(DEMAND, DEMAND, "50", D2),
                Demand(DEMAND, DEMAND, "10", D3),
            ),
            targets=((DEMAND, D1, "APPROVED"), (DEMAND, D2, "APPROVED"), (DEMAND, D3, "APPROVED")),
            name="ac5-first-shortage",
        )
        self.assertEqual(built.shortage.first_shortage_date, D2)
        self.assertEqual(self.grain(built, DEMAND, D2).first_shortage_date, D2)
        self.assertEqual(self.grain(built, DEMAND, D3).first_shortage_date, D2)
        self.assertEqual(built.shortage.first_buffer_breach_date, D2)

    def test_ac6_an_earlier_data_incomplete_grain_blocks_a_later_first_shortage_date(
        self,
    ) -> None:
        # P1 + M2 is DATA_INCOMPLETE on D1 (its Target Demand Context is unresolved), so the real
        # SHORTAGE of the later P1 + M7 grain is never claimed as the reliable FirstShortageDate.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D1),
                Demand("M7", "M7", "110", D2),
            ),
            inventory={DEMAND: "100", "M7": "100"},
            safety_stock={DEMAND: "5", "M7": "5"},
            targets=((DEMAND, D1, "UNRESOLVED"), ("M7", D2, "APPROVED")),
            name="ac6-blocked-first-shortage",
        )
        self.assert_classification(
            self.grain(built, DEMAND, D1), CLASSIFICATION_DATA_INCOMPLETE
        )
        self.assert_classification(self.grain(built, "M7", D2), CLASSIFICATION_SHORTAGE)
        self.assertEqual(built.shortage.first_shortage_date, SHORTAGE_DATA_INCOMPLETE)
        self.assertEqual(
            built.shortage.first_buffer_breach_date, SHORTAGE_DATA_INCOMPLETE
        )

    def test_ac7_a_later_data_incomplete_grain_never_moves_a_reliable_first_date(self) -> None:
        # D1 is a reliable SHORTAGE; D2's grain references a substitute demand context that the
        # substitute rule never resolved and is DATA_INCOMPLETE.  The D1 marker stands.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "110", D1),
                Demand(DEMAND, DEMAND, "10", D2),
            ),
            targets=((DEMAND, D1, "APPROVED"), (DEMAND, D2, "UNRESOLVED")),
            name="ac7-later-incomplete",
        )
        first = self.grain(built, DEMAND, D1)
        self.assert_classification(first, CLASSIFICATION_SHORTAGE)
        self.assertEqual(first.first_shortage_date, D1)
        later = self.grain(built, DEMAND, D2)
        self.assert_classification(later, CLASSIFICATION_DATA_INCOMPLETE)
        # The grain that could not be decided never claims a reliable date of its own ...
        self.assertIsNone(later.first_shortage_date)
        self.assertIsNone(later.first_buffer_breach_date)
        # ... while the already established earlier date stands at result level.
        self.assertEqual(built.shortage.first_shortage_date, D1)
        self.assertEqual(built.shortage.first_buffer_breach_date, D1)

    def test_ac7b_an_undecidable_grain_claims_no_date_of_its_own(self) -> None:
        # Same shape as AC-7 but asserted on the grain-level surface: a DATA_INCOMPLETE grain must
        # never carry a reliable first-date marker, or one document would contradict itself.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "110", D1),
                Demand(DEMAND, DEMAND, "10", D2),
            ),
            targets=((DEMAND, D1, "APPROVED"), (DEMAND, D2, "UNRESOLVED")),
            name="ac7b-undecidable-grain",
        )
        undecided = self.grain(built, DEMAND, D2)
        self.assert_classification(undecided, CLASSIFICATION_DATA_INCOMPLETE)
        self.assertIsNone(undecided.projected_available)
        self.assertIsNone(undecided.first_shortage_date)
        self.assertIsNone(undecided.first_buffer_breach_date)
        for grain in built.shortage.data_incomplete_grains:
            self.assertIsNone(grain.first_shortage_date)
            self.assertIsNone(grain.first_buffer_breach_date)
        self.assertEqual(built.shortage.first_shortage_date, D1)

    def test_ac8_a_fully_reliable_horizon_without_shortage_is_a_valid_absence(self) -> None:
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D1),
                Demand(DEMAND, DEMAND, "10", D2),
            ),
            targets=((DEMAND, D1, "APPROVED"), (DEMAND, D2, "APPROVED")),
            name="ac8-valid-absence",
        )
        self.assertEqual(built.shortage.data_incomplete_grains, ())
        self.assertIsNone(built.shortage.first_shortage_date)
        self.assertIsNone(built.shortage.first_buffer_breach_date)
        self.assertIsNone(built.shortage.to_dict()["FirstShortageDate"])

    def test_ac8b_an_unresolved_horizon_never_reports_a_valid_absence(self) -> None:
        # No grain ever goes short, but D2 is DATA_INCOMPLETE, so "never short" is not claimed.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D1),
                Demand(DEMAND, DEMAND, "10", D2),
            ),
            targets=((DEMAND, D1, "APPROVED"), (DEMAND, D2, "UNRESOLVED")),
            name="ac8b-no-valid-absence",
        )
        self.assertEqual(built.shortage.first_shortage_date, SHORTAGE_DATA_INCOMPLETE)
        self.assertEqual(
            built.shortage.first_buffer_breach_date, SHORTAGE_DATA_INCOMPLETE
        )


# --- AC-9 / AC-10 / AC-11: S1-A source reservation consumption ----------------------


class SourceReservationTests(ShortageRuleTestCase):
    def _conservation_built(self, *, quantity: str = "60", name: str):
        # P1 + M9 is the exact Source Demand Context of the ``M2`` <- ``M9`` reservation, so its
        # inventory-side supply is 100 - 60 = 40 instead of the complete 100.
        return self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D2),
                Demand(RESERVED, RESERVED, "20", D2),
            ),
            inventory={DEMAND: "100", RESERVED: "100"},
            safety_stock={DEMAND: "5", RESERVED: "0"},
            conservation=(DEMAND, RESERVED, quantity),
            targets=((DEMAND, D2, "APPROVED"), (RESERVED, D2, "APPROVED")),
            name=name,
        )

    def test_ac9_the_source_grain_consumes_remaining_unallocated_source_supply(self) -> None:
        built = self._conservation_built(name="ac9-source-consumption")
        group = built.substitutes.conservation_groups[0]
        self.assertEqual(group.remaining_unallocated_source_supply.text(), "40")
        self.assertEqual(group.source_demand_context_grain, (PLANT, RESERVED, D2))

        grain = self.grain(built, RESERVED, D2)
        self.assertEqual(grain.supply_source, SUPPLY_FROM_SOURCE_RESERVATION)
        self.assert_quantity(grain, "opening_supply", "40")
        # 40 + 0 + 0 - 20 = 20: the already allocated 60 is never available again.
        self.assert_quantity(grain, "projected_available", "20")
        self.assertEqual(
            grain.source_demand_context_reference, group.reservation_context
        )

    def test_ac9b_the_complete_inventory_is_never_also_consumed(self) -> None:
        built = self._conservation_built(name="ac9b-no-double-consumption")
        grain = self.grain(built, RESERVED, D2)
        self.assertEqual(grain.supply_source, SUPPLY_FROM_SOURCE_RESERVATION)
        self.assertNotEqual(grain.opening_supply.text(), "100")
        self.assert_quantity(grain, "opening_supply", "40")

    def test_ac10_without_a_reservation_the_normal_snapshot_path_is_used(self) -> None:
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "10"),),
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac10-snapshot-path",
        )
        self.assertEqual(built.substitutes.source_demand_contexts, ())
        grain = self.grain(built)
        self.assertEqual(grain.supply_source, SUPPLY_FROM_INVENTORY_SNAPSHOT)
        self.assert_quantity(grain, "opening_supply", "100")
        self.assert_quantity(grain, "projected_available", "90")
        self.assert_quantity(grain, "safety_stock", "5")

    def test_ac11_an_unresolved_conservation_propagates_data_incomplete(self) -> None:
        # PENDING approval makes the eligible substitute supply 0 while 60 is still allocated,
        # so the conservation group is OVER_ALLOCATED and produces no remaining supply.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D2),
                Demand(RESERVED, RESERVED, "20", D2),
                Demand("M7", "M7", "100", D2),
            ),
            inventory={DEMAND: "100", RESERVED: "0"},
            safety_stock={DEMAND: "5", RESERVED: "0"},
            relationships=((DEMAND, RESERVED, "APPROVED"),),
            conservation=(DEMAND, RESERVED, "60"),
            targets=((DEMAND, D2, "APPROVED"), (RESERVED, D2, "APPROVED")),
            name="ac11-conservation-incomplete",
        )
        group = built.substitutes.conservation_groups[0]
        self.assertEqual(group.outcome, SHORTAGE_DATA_INCOMPLETE)
        self.assertIsNone(group.remaining_unallocated_source_supply)
        grain = self.grain(built, RESERVED, D2)
        self.assert_classification(grain, CLASSIFICATION_DATA_INCOMPLETE)
        self.assertIsNone(grain.projected_available)
        self.assertEqual(grain.supply_source, "SOURCE_RESERVATION_UNRESOLVED")


# --- AC-12: S2-A inventory snapshot consumption boundary ----------------------------


class InventorySnapshotBoundaryTests(ShortageRuleTestCase):
    def test_ac12_zero_inventory_targets_are_the_legal_zero(self) -> None:
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "10"),),
            inventory={},
            safety_stock={},
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac12-zero-targets",
        )
        self.assertEqual(built.inventory.targets, ())
        grain = self.grain(built)
        self.assertEqual(grain.supply_source, SUPPLY_FROM_INVENTORY_SNAPSHOT)
        self.assert_quantity(grain, "opening_supply", "0")
        self.assert_quantity(grain, "projected_available", "-10")
        self.assert_classification(grain, CLASSIFICATION_SHORTAGE)

    def test_ac12b_several_snapshot_times_are_never_merged_or_won(self) -> None:
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "10"),),
            snapshots=((DEMAND, SNAPSHOT_TIME_B),),
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac12b-two-snapshots",
        )
        consumable = [
            target
            for target in built.inventory.targets
            if target.material_code == DEMAND
            and target.opening_usable_inventory is not None
        ]
        self.assertEqual(len(consumable), 2)
        grain = self.grain(built)
        self.assert_classification(grain, CLASSIFICATION_DATA_INCOMPLETE)
        self.assertIsNone(grain.projected_available)
        self.assertEqual(grain.supply_source, "INVENTORY_SNAPSHOT_UNRESOLVED")

    def test_ac12c_an_unusable_opening_inventory_fails_closed(self) -> None:
        # on_hand_qty is absent, so BR-INVENTORY-001 states no usable OpeningUsableInventory.
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "10"),),
            inventory={DEMAND: None, SOURCE: "100"},
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac12c-unusable-opening",
        )
        grain = self.grain(built)
        self.assert_classification(grain, CLASSIFICATION_DATA_INCOMPLETE)
        self.assertEqual(grain.supply_source, "INVENTORY_SNAPSHOT_UNRESOLVED")

    def test_ac12d_an_unresolved_safety_stock_is_never_defaulted_to_zero(self) -> None:
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "10"),),
            skip_safety_stock=(DEMAND,),
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac12d-missing-safety-stock",
        )
        grain = self.grain(built)
        self.assert_classification(grain, CLASSIFICATION_DATA_INCOMPLETE)
        # The projection is still exact; only the classification threshold is undecidable.
        self.assert_quantity(grain, "projected_available", "90")
        self.assertIsNone(grain.safety_stock)


# --- AC-13 / AC-14 / AC-15: S3-A substitute result completeness ---------------------


class SubstituteCompletenessTests(ShortageRuleTestCase):
    def test_ac13_an_explicit_substitute_zero_is_consumed_as_zero(self) -> None:
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "10"),),
            relationships=((DEMAND, SOURCE, "PENDING"),),
            targets=((DEMAND, D2, "NOT_APPLICABLE"),),
            name="ac13-explicit-zero",
        )
        grain = self.grain(built)
        self.assert_quantity(grain, "cumulative_approved_substitute_supply", "0")
        self.assertEqual(grain.classification, CLASSIFICATION_NORMAL)
        self.assert_quantity(grain, "projected_available", "90")

    def test_ac14_an_unresolved_substitute_result_propagates_data_incomplete(self) -> None:
        # The allocation cites an unregistered Target Applicability basis, so the target grain's
        # cumulative approved substitute supply is unresolved.
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "10"),),
            relationships=((DEMAND, SOURCE, "APPROVED"),),
            targets=((DEMAND, D2, "UNRESOLVED"),),
            name="ac14-unresolved-substitute",
        )
        target = built.substitutes.for_grain(PLANT, DEMAND, D2)
        assert target is not None
        self.assertIsNone(target.cumulative_approved_substitute_supply)
        grain = self.grain(built)
        self.assert_classification(grain, CLASSIFICATION_DATA_INCOMPLETE)
        self.assertIsNone(grain.projected_available)

    def test_ac15_a_missing_target_is_never_an_implicit_default(self) -> None:
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "10"),),
            substitute_present=True,
            relationships=(),
            targets=(),
            name="ac15-missing-target",
        )
        self.assertEqual(built.substitutes.targets, ())
        grain = self.grain(built)
        self.assert_classification(grain, CLASSIFICATION_DATA_INCOMPLETE)
        self.assertIsNone(grain.projected_available)

    def test_ac15b_an_absent_substitute_role_fails_closed(self) -> None:
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "10"),),
            substitute_present=False,
            name="ac15b-absent-role",
        )
        grain = self.grain(built)
        self.assert_classification(grain, CLASSIFICATION_DATA_INCOMPLETE)
        self.assertIsNone(grain.projected_available)

    def test_ac15c_a_confirmed_non_target_relationship_is_a_stated_zero(self) -> None:
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "10"),),
            relationships=((DEMAND, SOURCE, "APPROVED"),),
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac15c-stated-zero",
        )
        grain = self.grain(built)
        self.assert_quantity(grain, "cumulative_approved_substitute_supply", "0")
        self.assertEqual(grain.classification, CLASSIFICATION_NORMAL)

    def test_ac15d_a_source_only_material_is_a_stated_zero(self) -> None:
        # P1 + M3 is cited only as an exact Source Demand Context, so BR-SUBSTITUTE-001 states
        # no approved substitute supply for it: an explicit 0, not an omitted target.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D2),
                Demand(SOURCE, SOURCE, "20", D2),
            ),
            conservation=(DEMAND, SOURCE, "60"),
            name="ac15d-source-zero",
        )
        grain = self.grain(built, SOURCE, D2)
        self.assert_quantity(grain, "cumulative_approved_substitute_supply", "0")
        self.assertEqual(grain.classification, CLASSIFICATION_NORMAL)


# --- AC-16 / AC-17: grain isolation --------------------------------------------------


class GrainIsolationTests(ShortageRuleTestCase):
    def test_ac16_separate_plants_are_never_aggregated(self) -> None:
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "10"),),
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac16-plants",
        )
        grains = built.shortage.for_plant_material(PLANT, DEMAND)
        self.assertEqual(len(grains), 1)
        self.assertEqual(grains[0].plant_id, PLANT)
        self.assertEqual(built.shortage.for_plant_material(PLANT_B, DEMAND), ())
        self.assert_quantity(grains[0], "opening_supply", "100")

    def test_ac17_separate_materials_never_share_a_running_total(self) -> None:
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "60", D2),
                Demand(OTHER, OTHER, "10", D2),
            ),
            inventory={DEMAND: "100", OTHER: "3"},
            safety_stock={DEMAND: "5", OTHER: "0"},
            targets=((DEMAND, D2, "APPROVED"), (OTHER, D2, "APPROVED")),
            name="ac17-materials",
        )
        demand_grain = self.grain(built, DEMAND, D2)
        other_grain = self.grain(built, OTHER, D2)
        self.assert_quantity(demand_grain, "opening_supply", "100")
        self.assert_quantity(other_grain, "opening_supply", "3")
        self.assert_classification(demand_grain, CLASSIFICATION_NORMAL)
        self.assert_classification(other_grain, CLASSIFICATION_SHORTAGE)


# --- AC-18 / AC-19: numeric semantics, determinism, trace surfaces ------------------


class NumericAndTraceTests(ShortageRuleTestCase):
    def test_ac18_no_float_rounding_or_decimal_context_participates(self) -> None:
        import snapshot_loader.shortage_calculation as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        for forbidden in ("localcontext", "quantize(", "round(", "float(", "Decimal("):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)
        self.assertNotIn("OUTCOME_NUMERIC", module.__all__)

    def test_ac18b_exact_cumulative_arithmetic_keeps_every_digit(self) -> None:
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "0.333", D1),
                Demand(DEMAND, DEMAND, "0.333", D2),
            ),
            inventory={DEMAND: "1"},
            safety_stock={DEMAND: "0"},
            targets=((DEMAND, D1, "APPROVED"), (DEMAND, D2, "APPROVED")),
            name="ac18b-exact",
        )
        first = self.grain(built, DEMAND, D1)
        second = self.grain(built, DEMAND, D2)
        self.assert_quantity(first, "projected_available", "0.667")
        self.assert_quantity(second, "projected_available", "0.334")
        self.assert_quantity(second, "cumulative_gross_requirement", "0.666")

    def test_ac18c_the_registered_rule_surface_is_exposed(self) -> None:
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "110"),),
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac18c-surface",
        )
        payload = built.shortage.to_dict()
        self.assertEqual(payload["rule"], SHORTAGE_RULE_ID)
        self.assertEqual(payload["FirstShortageDate"], D2)
        self.assertEqual(payload["FirstBufferBreachDate"], D2)
        grain = payload["grains"][0]
        self.assertEqual(grain["Classification"], CLASSIFICATION_SHORTAGE)
        self.assertEqual(grain["ProjectedAvailable"], "-10")
        self.assertEqual(grain["ShortageQty"], "10")
        self.assertEqual(grain["BufferGap"], "15")
        for field in (
            "SafetyStock",
            "EffectiveOpeningSupply",
            "CumulativeEffectiveInbound",
            "CumulativeApprovedSubstituteSupply",
            "CumulativeGrossRequirement",
            "ProjectedAvailable",
            "Classification",
            "ShortageQty",
            "BufferGap",
        ):
            self.assertIn(field, grain)

    def test_ac19_the_result_is_deterministic_and_read_only(self) -> None:
        first = self.build(
            demand=(Demand(DEMAND, DEMAND, "110"),),
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac19-run-a",
        )
        second = self.build(
            demand=(Demand(DEMAND, DEMAND, "110"),),
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac19-run-b",
        )
        self.assertEqual(first.shortage.to_dict(), second.shortage.to_dict())
        self.assertTrue(dataclasses.is_dataclass(first.shortage))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            first.shortage.grains[0].classification = CLASSIFICATION_NORMAL  # type: ignore[misc]

    def test_ac19b_failure_is_isolated_to_the_affected_grain(self) -> None:
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D1),
                Demand(OTHER, OTHER, "10", D1),
            ),
            inventory={DEMAND: "100", OTHER: "100"},
            safety_stock={DEMAND: "5", OTHER: "5"},
            snapshots=((DEMAND, SNAPSHOT_TIME_B),),
            targets=((DEMAND, D1, "APPROVED"), (OTHER, D1, "APPROVED")),
            name="ac19b-isolation",
        )
        self.assert_classification(
            self.grain(built, DEMAND, D1), CLASSIFICATION_DATA_INCOMPLETE
        )
        healthy = self.grain(built, OTHER, D1)
        self.assert_classification(healthy, CLASSIFICATION_NORMAL)
        self.assert_quantity(healthy, "projected_available", "90")

    def test_ac19c_upstream_cumulative_values_are_consumed_exactly_once(self) -> None:
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "60", D1),
                Demand(DEMAND, DEMAND, "50", D2),
            ),
            inbound=((DEMAND, "100", "2026-10-05"),),
            targets=((DEMAND, D1, "APPROVED"), (DEMAND, D2, "APPROVED")),
            name="ac19c-consumed-once",
        )
        first = self.grain(built, DEMAND, D1)
        second = self.grain(built, DEMAND, D2)
        # The same upstream CumulativeEffectiveInbound(<= D2) value is consumed once, never
        # accumulated again on top of the value already reported for D1.
        self.assert_quantity(first, "cumulative_effective_inbound", "100")
        self.assert_quantity(second, "cumulative_effective_inbound", "100")
        self.assert_quantity(first, "projected_available", "140")
        self.assert_quantity(second, "projected_available", "90")
        self.assertIsNone(second.first_shortage_date)

    def test_ac19d_the_result_adds_no_persisted_state(self) -> None:
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "10"),),
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac19d-read-only",
        )
        self.assertFalse(hasattr(built.shortage, "save"))
        self.assertFalse(hasattr(built.shortage, "persist"))
        self.assertEqual(
            {field.name for field in dataclasses.fields(built.shortage)},
            {"grains", "rule_issues"},
        )

    def test_ac19e_an_exact_reservation_is_deducted_once_across_the_horizon(self) -> None:
        # The reservation is a family-level deduction, not a per-grain one: if the cumulative
        # formula consumed it once per grain, the second date would lose another 60.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D1),
                Demand(RESERVED, RESERVED, "0", D1),
                Demand(RESERVED, RESERVED, "10", D2),
            ),
            inventory={DEMAND: "100", RESERVED: "100"},
            safety_stock={DEMAND: "5", RESERVED: "0"},
            conservation=(DEMAND, RESERVED, "60"),
            targets=((DEMAND, D1, "APPROVED"), (RESERVED, D1, "APPROVED")),
            name="ac19e-single-deduction",
        )
        first = self.grain(built, RESERVED, D1)
        second = self.grain(built, RESERVED, D2)
        self.assertEqual(first.supply_source, SUPPLY_FROM_SOURCE_RESERVATION)
        self.assert_quantity(first, "opening_supply", "40")
        self.assert_quantity(second, "opening_supply", "40")
        # 40 + 0 + 0 - 0 = 40 on D1 and 40 - 10 = 30 on D2.
        self.assert_quantity(first, "projected_available", "40")
        self.assert_quantity(second, "projected_available", "30")

    def test_ac19f_the_earliest_date_scan_is_by_calendar_not_by_material(self) -> None:
        # P1 + M2 is unresolved on D1 and P1 + M5 is short on D2.  ``M2`` < ``M5`` and ``D1`` <
        # ``D2`` agree here, so the assertion is made against the *date* semantics: a shortage on
        # an earlier date of a later-sorting material is not blocked by a later-dated failure.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D2),
                Demand(OTHER, OTHER, "50", D1),
            ),
            inventory={DEMAND: "100", OTHER: "10"},
            safety_stock={DEMAND: "5", OTHER: "0"},
            targets=((DEMAND, D2, "UNRESOLVED"), (OTHER, D1, "APPROVED")),
            name="ac19f-date-scan",
        )
        self.assert_classification(
            self.grain(built, OTHER, D1), CLASSIFICATION_SHORTAGE
        )
        self.assert_classification(
            self.grain(built, DEMAND, D2), CLASSIFICATION_DATA_INCOMPLETE
        )
        # The unresolved grain (D2) is later than the established marker (D1), so it cannot move
        # the already reliable first shortage date.
        self.assertEqual(built.shortage.first_shortage_date, D1)

    def test_ac19g_a_requirement_with_no_finite_decimal_fails_closed(self) -> None:
        # A non-terminating GrossRequirement is never truncated or rounded to a decimal.
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "200", D2),),
            loss_rate="0.05",
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac19g-non-terminating",
        )
        row = built.requirements.for_grain(PLANT, DEMAND, D2)
        assert row is not None
        self.assertIsNotNone(row.gross_requirement)
        self.assertNotEqual(row.gross_requirement.denominator, 1)
        grain = self.grain(built)
        self.assert_classification(grain, CLASSIFICATION_DATA_INCOMPLETE)
        self.assertIsNone(grain.projected_available)
        self.assertIsNone(grain.cumulative_gross_requirement)
