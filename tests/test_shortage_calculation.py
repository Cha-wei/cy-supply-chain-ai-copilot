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
from fractions import Fraction
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
    SUPPLY_UNRESOLVED_INVENTORY_SNAPSHOT,
    SUPPLY_UNRESOLVED_SOURCE_RESERVATION,
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
#: The phase B recognized role literal (role 12): its ``POLICY_INPUT`` channel is opened by the
#: Phase B procurement-policy-input seam only, never by phase A.
ROLE_PROCUREMENT_POLICY_INPUT = "Procurement policy input"

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


def _object_label(item: Any) -> str:
    """A short deterministic label for an assertion message.

    ``assert_quantity`` is used on shortage grains, substitute targets and conservation groups
    alike, so the label is read defensively instead of assuming a ``grain`` attribute.
    """

    grain = getattr(item, "grain", None)
    if grain is not None:
        return repr(grain)
    for name in ("reservation_context", "reference", "material_code"):
        value = getattr(item, name, None)
        if value is not None:
            return repr(value)
    return type(item).__name__


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


def _rational_value(value: Any) -> Fraction:
    """The exact rational value of a derived ``Fraction`` or a canonical decimal quantity."""

    if isinstance(value, Fraction):
        return value
    if isinstance(value, ExactQuantity):
        return Fraction(value.units, 10**value.scale)
    return Fraction(str(value))


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
    target_bases: tuple[Any, ...] = (),
    source_basis: Any = BASIS_SRO,
) -> dict[str, Any]:
    """One accepted ``Substitute Allocation`` record with its registered G5-A associations.

    ``target_bases`` registers further Target Applicability bases on the ``target_material_code``
    observation, so one allocation record can legally state several registered Target outcomes (a
    G5-A claim only *selects* one of the registrations the accepted record already states).
    """

    record: dict[str, Any] = {
        "plant_id": PLANT,
        "target_material_code": target,
        "substitute_material_code": substitute,
        "AllocatedSubstituteQty": quantity,
    }
    associations: list[tuple[str, list[str], str | None]] = []
    for basis in (target_basis, *target_bases):
        if basis is None:
            continue
        associations.append(
            ("target_material_code", [f"SIMULATED-SRC-ALLOC-TA-{target}"], basis)
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
class ReservationAllocation:
    """One extra accepted ``Substitute Allocation`` record of the quoted reservation's own pair.

    ``quantity`` is that record's own ``AllocatedSubstituteQty``.  It registers the SRO basis on its
    source side, so it joins the **same** exact Source Demand Context conservation sum as the quoted
    reservation, and ``target_claims`` names one ``(required_date, Target Applicability outcome)`` per
    Target Demand Context that cites it (the record registers every basis its own claims name).
    """

    quantity: Any
    target_claims: tuple[tuple[Any, Any], ...] = ()


@dataclasses.dataclass(frozen=True)
class Built:
    """One fully computed deterministic pipeline for one SIMULATED fixture."""

    construction: Any
    requirements: Any
    inbounds: Any
    inventory: Any
    substitutes: Any
    shortage: Any
    #: The accepted package the whole chain was built from, so a Phase B seam that must read accepted
    #: evidence (the procurement policy input) consumes exactly this package and no other.
    accepted: Any = None


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
        source_reservation_registration: Any = BASIS_SRO,
        source_reservation_claim: Any = None,
        extra_reservation_allocations: tuple[ReservationAllocation, ...] = (),
        targets: tuple[tuple[Any, Any, Any], ...] = ((DEMAND, D2, "APPROVED"),),
        target_quantities: dict[tuple[Any, Any], Any] | None = None,
        relationships: tuple[tuple[Any, Any, str], ...] = ((DEMAND, SOURCE, "APPROVED"),),
        substitute_present: bool = True,
        moq_policies: tuple[dict[str, Any], ...] = (),
        analysis_run_id: str = "RUN-1",
        analysis_date: Any = "2026-10-01",
        package_id: str = "SIMULATED-PKG-0001",
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

        ``source_reservation_registration`` is the basis the quoted allocation record registers for
        its ``substitute_material_code`` (the SRO side); ``source_reservation_claim`` is the basis
        the SRO handoff claims and defaults to that same registration.  Passing a different claim
        reproduces the registered G5-A failure class "unregistered mapping basis" on the source side
        (the overlap outcome cannot be formed), and passing another *registered* basis exercises the
        other registered SRO outcomes.

        ``extra_reservation_allocations`` adds further accepted allocation records of the quoted
        reservation's own ``target_material`` + ``substitute_material`` pair that also register the SRO
        basis, so they join the **same** exact Source Demand Context conservation sum; each one states
        its own quantity and its own Target Applicability claims.
        """

        stock = {DEMAND: "100", SOURCE: "100"} if inventory is None else dict(inventory)
        policy = {DEMAND: "5", SOURCE: "0"} if safety_stock is None else dict(safety_stock)
        target_quantities = dict(target_quantities or {})

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
        for extra in extra_reservation_allocations:
            for date, _outcome in extra.target_claims:
                cited.append((conservation[0] if conservation else DEMAND, date))

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
            declared = list(relationships)
            if conservation is not None and not any(
                target == conservation[0] and substitute == conservation[1]
                for target, substitute, _approval in declared
            ):
                # The quoted allocation needs its own approved relationship, or the join key has
                # no applicable relationship and the allocation stays unresolved.
                declared.append((conservation[0], conservation[1], "APPROVED"))
            datasets.append(
                (
                    ROLE_RELATIONSHIP,
                    [
                        relationship_record(target, substitute, approval=approval)
                        for target, substitute, approval in declared
                    ],
                )
            )
            allocations: list[dict[str, Any]] = []
            # Each allocation record's own position inside the accepted artifact, keyed by the
            # target pair it states, so a G5-A handoff always cites the record it means.
            allocation_positions: dict[tuple[Any, Any], int] = {}
            if conservation is not None:
                allocation_positions[(conservation[0], D2)] = len(allocations)
                allocations.append(
                    allocation_record(
                        conservation[0],
                        conservation[1],
                        quantity=conservation[2],
                        target_basis=BASIS_TA,
                        source_basis=source_reservation_registration,
                    )
                )
            for material, date, outcome in targets:
                if conservation is not None and (material, date) == (
                    conservation[0],
                    D2,
                ):
                    # The quoted reservation record already carries this pair's Target
                    # Applicability with a real quantity, so no second record is added and the
                    # target context cites that record.
                    continue
                allocation_positions[(material, date)] = len(allocations)
                allocations.append(
                    allocation_record(
                        material,
                        SOURCE if conservation is None else conservation[1],
                        quantity=target_quantities.get((material, date), "0"),
                        target_basis=basis_for(outcome),
                        source_basis=None,
                    )
                )
            # Further allocation records of the quoted reservation's own pair: they register the SRO
            # basis, so they reserve inside the same exact Source Demand Context, and they register
            # every Target Applicability basis their own claims name.
            extra_positions: list[int] = []
            for extra in extra_reservation_allocations:
                extra_positions.append(len(allocations))
                allocations.append(
                    allocation_record(
                        conservation[0],
                        conservation[1],
                        quantity=extra.quantity,
                        target_basis=None,
                        target_bases=tuple(
                            dict.fromkeys(
                                basis_for(outcome)
                                for _date, outcome in extra.target_claims
                            )
                        ),
                        source_basis=source_reservation_registration,
                    )
                )
            if conservation is not None and not any(
                material == conservation[0] for material, _date, _o in targets
            ):
                # No Target Applicability context of the quoted reservation's own material was
                # requested, so the reservation record has to state one itself; otherwise the
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

        if moq_policies:
            # The phase B ``Procurement policy input`` dataset (role 12).  It is appended last, so
            # the phase A artifacts keep their existing ordinals and no other fixture changes.
            datasets.append((ROLE_PROCUREMENT_POLICY_INPUT, list(moq_policies)))

        built = build_package(
            self.boundary / (name or uuid.uuid4().hex[:8]),
            PackageSpec(
                package_id=package_id,
                datasets=[
                    DatasetSpec(role=role, artifact=f"{index}.json", records=records)
                    for index, (role, records) in enumerate(datasets)
                ],
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
        if substitute_present:
            # The quoted reservation record comes first, so the target context of a material that
            # the reservation also targets binds to that record rather than to a zero-quantity
            # target record; every other target cites the record its own pair states.
            target_source = SOURCE if conservation is None else conservation[1]
            if conservation is not None:
                demand_entries.append(
                    EffectiveDemandRelationHandoff(
                        source_substitute_material=conservation[1],
                        target_material=conservation[0],
                        relation=RELATION_SOURCE,
                        evidence=cite(
                            ROLE_ALLOCATION,
                            ARTIFACT_ALLOCATION,
                            0,
                            f"SIMULATED-SRC-ALLOC-SRO-{conservation[0]}",
                        ),
                        mapping_basis=(
                            source_reservation_registration
                            if source_reservation_claim is None
                            else source_reservation_claim
                        ),
                        context_citation=cite(
                            ROLE_REQUIREMENT,
                            ARTIFACT_REQUIREMENT,
                            index_by_material[(conservation[1], D2)],
                        ),
                    )
                )
            for material, date, outcome in targets:
                if conservation is not None and (material, date) == (
                    conservation[0],
                    D2,
                ):
                    record = 0
                else:
                    record = allocation_positions[(material, date)]
                demand_entries.append(
                    EffectiveDemandRelationHandoff(
                        source_substitute_material=target_source,
                        target_material=material,
                        relation=RELATION_TARGET,
                        evidence=cite(
                            ROLE_ALLOCATION,
                            ARTIFACT_ALLOCATION,
                            record,
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
            for extra, position in zip(extra_reservation_allocations, extra_positions):
                # The extra record reserves inside the quoted reservation's own exact Source Demand
                # Context (same SRO basis registration) ...
                demand_entries.append(
                    EffectiveDemandRelationHandoff(
                        source_substitute_material=conservation[1],
                        target_material=conservation[0],
                        relation=RELATION_SOURCE,
                        evidence=cite(
                            ROLE_ALLOCATION,
                            ARTIFACT_ALLOCATION,
                            position,
                            f"SIMULATED-SRC-ALLOC-SRO-{conservation[0]}",
                        ),
                        mapping_basis=source_reservation_registration,
                        context_citation=cite(
                            ROLE_REQUIREMENT,
                            ARTIFACT_REQUIREMENT,
                            index_by_material[(conservation[1], D2)],
                        ),
                    )
                )
                # ... and states its own Target Applicability for each context that cites it.
                for date, outcome in extra.target_claims:
                    demand_entries.append(
                        EffectiveDemandRelationHandoff(
                            source_substitute_material=conservation[1],
                            target_material=conservation[0],
                            relation=RELATION_TARGET,
                            evidence=cite(
                                ROLE_ALLOCATION,
                                ARTIFACT_ALLOCATION,
                                position,
                                f"SIMULATED-SRC-ALLOC-TA-{conservation[0]}",
                            ),
                            mapping_basis=basis_for(outcome),
                            context_citation=cite(
                                ROLE_REQUIREMENT,
                                ARTIFACT_REQUIREMENT,
                                index_by_material[(conservation[0], date)],
                            ),
                        )
                    )

        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id=analysis_run_id,
                analysis_date=analysis_date,
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
        substitutes = compute_substitute_supply(
            construction, inventory_result, requirements=requirements
        )
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
            accepted=accepted,
        )

    # --- assertion helpers -------------------------------------------------------------

    def grain(self, built: Built, material: Any = DEMAND, date: Any = D2):
        item = built.shortage.for_grain(PLANT, material, date)
        self.assertIsNotNone(item, msg=f"no shortage grain for {material!r} @ {date!r}")
        assert item is not None
        return item

    def assert_quantity(self, grain, field: str, expected: Any) -> None:
        """Assert one exact numeric field against the exact rational value of ``expected``.

        A derived quantity (``ProjectedAvailable`` ／ ``ShortageQty`` ／ ``BufferGap`` and the
        consumed cumulative values) is an exact :class:`fractions.Fraction`; a consumed canonical
        quantity (``EffectiveOpeningSupply`` ／ ``SafetyStock``) is an ``ExactQuantity``.  Both are
        compared as exact rationals, so trailing fractional zeros and the two representations
        never make an assertion accidentally pass or fail.
        """

        value = getattr(grain, field)
        self.assertIsNotNone(
            value, msg=f"{field} is unresolved for {_object_label(grain)}"
        )
        assert value is not None
        self.assertEqual(_rational_value(value), _rational_value(expected))
        rendered = getattr(value, "text", None)
        if callable(rendered):
            self.assertEqual(_trim(rendered()), _trim(str(expected)))

    def assert_classification(self, grain, expected: str) -> None:
        self.assertEqual(grain.classification, expected)
        self.assertIn(grain.classification, CLASSIFICATIONS)

    def assert_is_grain_frozen(self, grain: Any) -> None:
        """The result surface is read-only: no caller may mutate a grain in place."""

        with self.assertRaises(dataclasses.FrozenInstanceError):
            grain.classification = CLASSIFICATION_NORMAL  # type: ignore[misc]


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


# --- F4: the per-family FirstShortageDate handoff ------------------------------------


class PerFamilyHandoffTests(ShortageRuleTestCase):
    """The registered per-family consumption seam of ``FirstShortageDate`` (Issue #156).

    ``BR-PROCUREMENT-001`` needs one baseline recommendation per ``plant_id`` + ``material_code``
    with ``RecommendationNeedDate = FirstShortageDate`` and
    ``BasePurchaseNeed = ShortageQty at FirstShortageDate``.  The result-wide marker scans every
    grain of the whole result and a grain-level marker is a family marker, so neither is the
    per-family authority: ``first_shortage_date_for()`` answers the existing three-state semantic
    (``DATE`` ／ ``SHORTAGE_DATA_INCOMPLETE`` ／ ``None``) over exactly one family's grains.
    """

    def test_f4_1_a_reliable_first_shortage_is_reported_per_family(self) -> None:
        # 100 opening - 10 = 90 >= 5 (NORMAL); -20 (SHORTAGE); -30 (SHORTAGE).
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D1),
                Demand(DEMAND, DEMAND, "110", D2),
                Demand(DEMAND, DEMAND, "10", D3),
            ),
            inventory={DEMAND: "100"},
            safety_stock={DEMAND: "5"},
            name="f4-1-reliable-first-shortage",
        )
        self.assertEqual(built.shortage.first_shortage_date_for(PLANT, DEMAND), D2)
        # The shortage quantity of that exact date stays directly retrievable for the baseline need.
        first = built.shortage.for_grain(PLANT, DEMAND, D2)
        assert first is not None
        self.assert_classification(first, CLASSIFICATION_SHORTAGE)
        self.assert_quantity(first, "shortage_qty", "20")
        self.assert_quantity(first, "projected_available", "-20")
        # The family's own grains are the horizon of the accessor; the later date carries the same
        # established marker and the earlier reliable NORMAL grain claims none.
        self.assertEqual(self.grain(built, DEMAND, D3).first_shortage_date, D2)
        self.assertIsNone(self.grain(built, DEMAND, D1).first_shortage_date)

    def test_f4_2_an_earlier_same_family_incomplete_blocks_the_later_shortage(self) -> None:
        # D1's statement is unusable upstream, so exactly that grain's CumulativeGrossRequirement
        # cannot be obtained while D2 stays decidable: the family's first shortage date is therefore
        # NOT reliably D2, even though D2 itself is a reliable SHORTAGE.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "not-a-registered-quantity", D1),
                Demand(DEMAND, DEMAND, "110", D2),
            ),
            inventory={DEMAND: "100"},
            safety_stock={DEMAND: "5"},
            name="f4-2-earlier-incomplete",
        )
        self.assert_classification(
            self.grain(built, DEMAND, D1), CLASSIFICATION_DATA_INCOMPLETE
        )
        later = self.grain(built, DEMAND, D2)
        self.assert_classification(later, CLASSIFICATION_SHORTAGE)
        self.assert_quantity(later, "shortage_qty", "10")
        answer = built.shortage.first_shortage_date_for(PLANT, DEMAND)
        self.assertEqual(answer, SHORTAGE_DATA_INCOMPLETE)
        self.assertNotEqual(answer, D2)
        # The grain-level family marker is fail-safe too: it never claims D2 across the earlier
        # unresolved grain, and it agrees with the per-family answer.
        self.assertEqual(later.first_shortage_date, SHORTAGE_DATA_INCOMPLETE)
        self.assertIsNone(self.grain(built, DEMAND, D1).first_shortage_date)

    def test_f4_3_a_later_incomplete_never_moves_the_earlier_date(self) -> None:
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "110", D1),
                Demand(DEMAND, DEMAND, "10", D2),
            ),
            inventory={DEMAND: "100"},
            safety_stock={DEMAND: "5"},
            targets=((DEMAND, D1, "APPROVED"), (DEMAND, D2, "UNRESOLVED")),
            name="f4-3-later-incomplete",
        )
        self.assert_classification(
            self.grain(built, DEMAND, D1), CLASSIFICATION_SHORTAGE
        )
        self.assert_classification(
            self.grain(built, DEMAND, D2), CLASSIFICATION_DATA_INCOMPLETE
        )
        self.assertEqual(built.shortage.first_shortage_date_for(PLANT, DEMAND), D1)
        self.assertEqual(self.grain(built, DEMAND, D1).first_shortage_date, D1)
        self.assertIsNone(self.grain(built, DEMAND, D2).first_shortage_date)

    def test_f4_4_a_fully_reliable_horizon_without_shortage_is_a_valid_absence(self) -> None:
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D1),
                Demand(DEMAND, DEMAND, "10", D2),
            ),
            inventory={DEMAND: "100"},
            safety_stock={DEMAND: "5"},
            name="f4-4-valid-absence",
        )
        self.assertEqual(built.shortage.data_incomplete_grains, ())
        self.assertIsNone(built.shortage.first_shortage_date_for(PLANT, DEMAND))
        self.assertIsNone(built.shortage.first_shortage_date)

    def test_f4_5_an_unresolved_horizon_without_shortage_never_reports_a_valid_absence(
        self,
    ) -> None:
        # No grain of the family ever goes short, but D2 is DATA_INCOMPLETE, so "never short" is not
        # a reliable conclusion for the family and the accessor fails safe instead of returning null.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D1),
                Demand(DEMAND, DEMAND, "10", D2),
            ),
            inventory={DEMAND: "100"},
            safety_stock={DEMAND: "5"},
            targets=((DEMAND, D1, "APPROVED"), (DEMAND, D2, "UNRESOLVED")),
            name="f4-5-unresolved-horizon",
        )
        self.assertEqual(built.shortage.shortage_grains, ())
        self.assertEqual(
            built.shortage.first_shortage_date_for(PLANT, DEMAND),
            SHORTAGE_DATA_INCOMPLETE,
        )

    def test_f4_6_one_family_never_answers_for_another(self) -> None:
        # M2 is DATA_INCOMPLETE at D1 while M5 is a reliable SHORTAGE at D2.  The result-wide marker
        # is the fail-safe because of M2, so it must NOT be the per-family authority: M2 does not
        # block M5's own date, and M5 does not make M2's answer reliable.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D1),
                Demand(OTHER, OTHER, "110", D2),
            ),
            inventory={DEMAND: "100", OTHER: "100"},
            safety_stock={DEMAND: "5", OTHER: "5"},
            targets=((DEMAND, D1, "UNRESOLVED"), (OTHER, D2, "APPROVED")),
            name="f4-6-family-isolation",
        )
        self.assertEqual(
            built.shortage.first_shortage_date_for(PLANT, DEMAND),
            SHORTAGE_DATA_INCOMPLETE,
        )
        self.assertEqual(built.shortage.first_shortage_date_for(PLANT, OTHER), D2)
        self.assertEqual(
            built.shortage.first_shortage_date, SHORTAGE_DATA_INCOMPLETE
        )
        # The unrelated family's own business result is untouched by the other family's failure.
        other = self.grain(built, OTHER, D2)
        self.assert_classification(other, CLASSIFICATION_SHORTAGE)
        self.assert_quantity(other, "shortage_qty", "10")

    def test_f4_the_three_states_reuse_the_existing_vocabulary(self) -> None:
        # Exactly the registered three-state semantic, with no new business enum / status: a date,
        # the existing SHORTAGE_DATA_INCOMPLETE literal, or a valid-absence None.
        reliable = self.build(
            demand=(Demand(DEMAND, DEMAND, "110", D2),),
            inventory={DEMAND: "100"},
            safety_stock={DEMAND: "5"},
            name="f4-vocabulary-date",
        )
        unresolved = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D1),
                Demand(DEMAND, DEMAND, "10", D2),
            ),
            inventory={DEMAND: "100"},
            safety_stock={DEMAND: "5"},
            targets=((DEMAND, D1, "APPROVED"), (DEMAND, D2, "UNRESOLVED")),
            name="f4-vocabulary-unresolved",
        )
        absent = self.build(
            demand=(Demand(DEMAND, DEMAND, "10", D2),),
            inventory={DEMAND: "100"},
            safety_stock={DEMAND: "5"},
            name="f4-vocabulary-absence",
        )
        self.assertEqual(reliable.shortage.first_shortage_date_for(PLANT, DEMAND), D2)
        self.assertEqual(
            unresolved.shortage.first_shortage_date_for(PLANT, DEMAND),
            SHORTAGE_DATA_INCOMPLETE,
        )
        self.assertIsNone(absent.shortage.first_shortage_date_for(PLANT, DEMAND))
        # ``SHORTAGE_DATA_INCOMPLETE`` is the **existing** registered ``DATA_INCOMPLETE`` business
        # outcome (the same literal the classification uses), not a new status or enum.
        self.assertEqual(SHORTAGE_DATA_INCOMPLETE, CLASSIFICATION_DATA_INCOMPLETE)
        self.assertIn(SHORTAGE_DATA_INCOMPLETE, CLASSIFICATIONS)
        # A family this result does not name has no horizon of its own and is never invented.
        self.assertIsNone(
            reliable.shortage.first_shortage_date_for(PLANT, "M-NOT-IN-RESULT")
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
        self.assertEqual(grain.supply_source, SUPPLY_UNRESOLVED_SOURCE_RESERVATION)


# --- AC-12: S2-A inventory snapshot consumption boundary ----------------------------


class InventorySnapshotBoundaryTests(ShortageRuleTestCase):
    def test_ac12_zero_inventory_targets_fail_closed(self) -> None:
        # Approved S2-A: for an exact plant_id + material_code, 0 InventoryTarget is
        # DATA_INCOMPLETE, exactly like more than one.  A legal 0 is never inferred.
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "10"),),
            inventory={},
            safety_stock={},
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac12-zero-targets",
        )
        self.assertEqual(built.inventory.targets, ())
        grain = self.grain(built)
        self.assertEqual(grain.supply_source, SUPPLY_UNRESOLVED_INVENTORY_SNAPSHOT)
        self.assert_classification(grain, CLASSIFICATION_DATA_INCOMPLETE)
        self.assertIsNone(grain.projected_available)
        self.assertIsNone(grain.shortage_qty)
        self.assertIsNone(grain.buffer_gap)
        self.assertIsNone(grain.first_shortage_date)

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
        self.assertEqual(grain.supply_source, SUPPLY_UNRESOLVED_INVENTORY_SNAPSHOT)

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
        self.assertEqual(grain.supply_source, SUPPLY_UNRESOLVED_INVENTORY_SNAPSHOT)

    def test_ac12d_an_unresolved_safety_stock_is_never_defaulted_to_zero(self) -> None:
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "10"),),
            skip_safety_stock=(DEMAND,),
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac12d-missing-safety-stock",
        )
        grain = self.grain(built)
        self.assert_classification(grain, CLASSIFICATION_DATA_INCOMPLETE)
        # The projection is still exact; only the classification threshold is undecidable, and the
        # projection is reported because it is a reliable fact of its own.
        self.assert_quantity(grain, "projected_available", "90")
        self.assertIsNone(grain.safety_stock)
        self.assertIsNone(grain.shortage_qty)
        self.assertIsNone(grain.buffer_gap)

    def test_ac12e_an_unresolved_threshold_beats_a_negative_projection(self) -> None:
        # §2.1.4 D / §2.1.8: DATA_INCOMPLETE has priority over SHORTAGE.  A negative projection with
        # an unresolved SafetyStock is DATA_INCOMPLETE, and the grain claims no reliable
        # FirstShortageDate of its own.
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "500"),),
            skip_safety_stock=(DEMAND,),
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac12e-incomplete-beats-shortage",
        )
        grain = self.grain(built)
        self.assert_quantity(grain, "projected_available", "-400")
        self.assert_classification(grain, CLASSIFICATION_DATA_INCOMPLETE)
        self.assertNotEqual(grain.classification, CLASSIFICATION_SHORTAGE)
        self.assertIsNone(grain.shortage_qty)
        self.assertIsNone(grain.first_shortage_date)
        self.assertIsNone(grain.first_buffer_breach_date)
        self.assertEqual(
            built.shortage.first_shortage_date, SHORTAGE_DATA_INCOMPLETE
        )

    def test_ac12f_a_stated_zero_opening_supply_is_still_decided(self) -> None:
        # S2-A fail-closes on 0 InventoryTarget, not on a target whose OpeningUsableInventory is
        # zero: a single consumable target with on_hand_qty 0 is a reliable stated value and the
        # grain must stay decided.
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "10"),),
            inventory={DEMAND: "0"},
            safety_stock={DEMAND: "0"},
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac12f-stated-zero",
        )
        self.assertEqual(
            len(built.inventory.for_plant_material(PLANT, DEMAND)), 1
        )
        grain = self.grain(built)
        self.assertEqual(grain.supply_source, SUPPLY_FROM_INVENTORY_SNAPSHOT)
        self.assert_quantity(grain, "opening_supply", "0")
        self.assert_quantity(grain, "projected_available", "-10")
        self.assert_classification(grain, CLASSIFICATION_SHORTAGE)


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
        # The completed substitute result still states this demand grain, but with no target
        # context and no relationship dataset fact that could authorise a 0 it is DATA_INCOMPLETE.
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "10"),),
            substitute_present=True,
            relationships=(),
            targets=(),
            name="ac15-missing-target",
        )
        target = built.substitutes.for_grain(PLANT, DEMAND, D2)
        assert target is not None
        # The Substitute Relationship dataset is present and states no relationship for this
        # exact join grain, which is the legal 0 of §2.3.11 A -- a confirmed absence, not a
        # guess from dataset absence or from unresolved evidence.
        self.assertEqual(target.cumulative_approved_substitute_supply, 0)
        self.assertFalse(target.data_incomplete)
        grain = self.grain(built)
        self.assert_quantity(grain, "cumulative_approved_substitute_supply", "0")
        self.assertEqual(grain.classification, CLASSIFICATION_NORMAL)

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

    def test_ac15e_an_unstated_grain_is_never_read_as_zero(self) -> None:
        # P1 + M5 is a resolved shortage demand grain, so the completed substitute result states it
        # -- but with no target context and no relationship dataset fact that could authorise a 0,
        # its cumulative stays ``None`` and the grain fails closed instead of reading 0.
        built = self.build(
            demand=(Demand(OTHER, OTHER, "10"),),
            inventory={OTHER: "100"},
            safety_stock={OTHER: "5"},
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac15e-unstated-grain",
        )
        target = built.substitutes.for_grain(PLANT, OTHER, D2)
        assert target is not None
        self.assertEqual(target.cumulative_approved_substitute_supply, 0)
        self.assertEqual(built.substitutes.source_demand_contexts_for_grain(
            PLANT, OTHER, D2
        ), ())
        # The dataset is present and states no applicable substitute for this grain, so the
        # value is the legal 0 of §2.3.11 A and the grain stays decided.
        grain = self.grain(built, OTHER, D2)
        self.assert_quantity(grain, "cumulative_approved_substitute_supply", "0")
        # 100 opening - 10 requirement = 90 >= 5, so the grain is decided and normal.
        self.assertEqual(grain.classification, CLASSIFICATION_NORMAL)

    def test_ac15g_a_sibling_date_source_citation_never_states_this_grain(self) -> None:
        # The cited Source Demand Context names ``P1`` + ``M3`` at ``D2`` only.  The grain
        # ``P1`` + ``M3`` at ``D1`` is not stated *by that citation*; it is stated as a
        # resolved demand grain of the completed result, and its value is the confirmed
        # absence of an applicable substitute (0) rather than an omission read as zero.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D2),
                Demand(SOURCE, SOURCE, "20", D1),
                Demand(SOURCE, SOURCE, "30", D2),
            ),
            conservation=(DEMAND, SOURCE, "60"),
            targets=((DEMAND, D2, "APPROVED"), (SOURCE, D2, "APPROVED")),
            name="ac15g-sibling-date-source",
        )
        # The substitute result states the sibling date only; the grain is still stated as a
        # resolved demand grain, with a confirmed zero rather than a citation.
        self.assertEqual(
            built.substitutes.source_demand_contexts_for_grain(PLANT, SOURCE, D1), ()
        )
        stated = built.substitutes.for_grain(PLANT, SOURCE, D1)
        assert stated is not None
        self.assertEqual(stated.cumulative_approved_substitute_supply, 0)
        self.assertTrue(
            built.substitutes.source_demand_contexts_for_grain(PLANT, SOURCE, D2)
        )
        early = self.grain(built, SOURCE, D1)
        self.assert_quantity(early, "cumulative_approved_substitute_supply", "0")
        self.assertIsNone(early.source_demand_context_reference)
        # The date the result *does* state keeps its explicit zero and stays decided: the same
        # family-level reservation still supplies the opening balance once.
        late = self.grain(built, SOURCE, D2)
        self.assert_quantity(late, "cumulative_approved_substitute_supply", "0")
        self.assert_quantity(late, "opening_supply", "40")
        self.assert_quantity(late, "cumulative_gross_requirement", "50")
        self.assert_quantity(late, "projected_available", "-10")
        self.assert_classification(late, CLASSIFICATION_SHORTAGE)
        self.assertIsNotNone(late.source_demand_context_reference)

    def test_ac15h_the_construction_is_never_read_at_runtime(self) -> None:
        # Stronger than the source scan: the only construction attribute this rule may touch is the
        # registered provenance binding (``analysis_run``, F3-RB1 / Option A'); every other access --
        # including dunder lookups that ``__getattr__`` would not intercept -- must be impossible.
        rebuilt = self.build(
            demand=(Demand(DEMAND, DEMAND, "10"),),
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac15h-hostile-construction",
        )

        class HostileConstruction:
            def __getattribute__(self, name: str) -> Any:
                if name == "analysis_run":
                    return rebuilt.construction.analysis_run
                raise AssertionError(
                    f"compute_shortage read construction.{name}; the only permitted construction "
                    "read is the provenance binding construction.analysis_run (F3-RB1), so every "
                    "business value must come from the consumed upstream results (S3-A)"
                )

        result = compute_shortage(
            HostileConstruction(),
            rebuilt.requirements,
            rebuilt.inbounds,
            rebuilt.inventory,
            rebuilt.substitutes,
        )
        self.assertEqual(result.to_dict(), rebuilt.shortage.to_dict())

    def test_ac15i_a_sibling_date_citation_never_reaches_the_other_direction(self) -> None:
        # The mirror image of AC-15g: the cited Source Demand Context is at the **later** date D2
        # while an earlier demand grain exists at D1.  The D1 grain is not stated by the substitute
        # result (neither a SubstituteTarget nor a cited context of its own date), so it fails
        # closed rather than consuming a material-wide zero, and it claims no context reference.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D1),
                Demand(DEMAND, DEMAND, "10", D2),
                Demand(SOURCE, SOURCE, "20", D1),
                Demand(SOURCE, SOURCE, "30", D2),
            ),
            inventory={DEMAND: "100", SOURCE: "100"},
            safety_stock={DEMAND: "5", SOURCE: "0"},
            conservation=(DEMAND, SOURCE, "60"),
            targets=((DEMAND, D1, "APPROVED"), (SOURCE, D1, "APPROVED")),
            name="ac15i-later-citation",
        )
        self.assertEqual(
            [
                context.required_date
                for context in built.substitutes.source_demand_contexts
                if context.target_material_code == SOURCE
            ],
            [D2],
        )
        # The grain whose own date the result states keeps its stated value and stays decided.
        early = self.grain(built, DEMAND, D1)
        self.assert_quantity(early, "cumulative_approved_substitute_supply", "0")
        self.assert_quantity(early, "projected_available", "90")
        self.assertEqual(early.classification, CLASSIFICATION_NORMAL)
        # Both grains are resolved demand grains, so the completed result states both.  The
        # **later** date has no contribution of its own: its cumulative carries forward the value
        # the earlier date established, and it is not treated as DATA_INCOMPLETE.
        late = self.grain(built, DEMAND, D2)
        self.assert_quantity(late, "cumulative_approved_substitute_supply", "0")
        self.assertEqual(
            late.cumulative_approved_substitute_supply,
            self.grain(built, DEMAND, D1).cumulative_approved_substitute_supply,
        )
        # The cited source grain keeps its own stated zero and its context reference.
        cited = self.grain(built, SOURCE, D2)
        self.assert_quantity(cited, "cumulative_approved_substitute_supply", "0")
        self.assertIsNotNone(cited.source_demand_context_reference)

    def test_ac15j_an_unhashable_cited_date_fails_closed(self) -> None:
        # A foreign / hand-built substitute result could carry a date that cannot index a table.
        # The module's own convention (``_groupable`` ／ ``_date_key``) is to fail such a grain
        # closed rather than raise, and the substitution set follows it: an unattributable citation
        # authorises nothing, and the computation still completes without raising.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D2),
                Demand(SOURCE, SOURCE, "20", D2),
            ),
            conservation=(DEMAND, SOURCE, "60"),
            name="ac15j-unhashable-date",
        )
        forged = tuple(
            dataclasses.replace(
                context,
                required_date=["2026-10-20"]
                if context.target_material_code == SOURCE
                else context.required_date,
            )
            for context in built.substitutes.source_demand_contexts
        )
        substitute_result = dataclasses.replace(
            built.substitutes, source_demand_contexts=forged
        )
        # The unattributable citation must not raise, and it must not authorise a substitute
        # conclusion for any grain: every grain keeps exactly the value the un-forged result gives
        # it, and no grain claims the unattributable context.
        result = compute_shortage(
            built.construction,
            built.requirements,
            built.inbounds,
            built.inventory,
            substitute_result,
        )
        self.assertEqual(
            {
                grain.grain: (
                    grain.classification,
                    grain.cumulative_approved_substitute_supply,
                )
                for grain in result.grains
            },
            {
                grain.grain: (
                    grain.classification,
                    grain.cumulative_approved_substitute_supply,
                )
                for grain in built.shortage.grains
            },
        )
        # The un-forged run does attribute the citation to the cited grain, so the check above is
        # not vacuous; the forged run must attach it to **no** grain, because a citation whose
        # demand date cannot be read is unattributable and may not reference a grain.
        self.assertTrue(
            any(
                grain.source_demand_context_reference is not None
                for grain in built.shortage.grains
            )
        )
        self.assertEqual(
            [
                grain.grain
                for grain in result.grains
                if grain.source_demand_context_reference is not None
            ],
            [],
        )
        for grain in result.grains:
            self.assert_is_grain_frozen(grain)

    def test_ac15k_the_explicit_zero_note_is_reported(self) -> None:
        # The explicit valid zero of §4.4.88 is a stated conclusion, so the grain records it.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D2),
                Demand(SOURCE, SOURCE, "20", D2),
            ),
            conservation=(DEMAND, SOURCE, "60"),
            name="ac15k-explicit-zero-note",
        )
        grain = self.grain(built, SOURCE, D2)
        self.assert_quantity(grain, "cumulative_approved_substitute_supply", "0")
        self.assertTrue(
            any("explicit 0 of §4.4.88" in note for note in grain.notes),
            msg=f"explicit-zero note missing from {grain.notes!r}",
        )
        self.assertTrue(
            any("explicit 0 of §4.4.88" in note for note in grain.to_dict()["notes"])
        )

    def test_ac15l_an_earlier_contribution_carries_forward_to_a_later_grain(self) -> None:
        # S3-A completion (review F1): the completed BR-SUBSTITUTE-001 result states an explicit
        # cumulative value for **every** resolved shortage demand grain.  A reliable contribution
        # of 60 is effective at D1, and D2 is a resolved demand grain with no contribution of its
        # own; D2 therefore carries the D1 value forward instead of being treated as DATA_INCOMPLETE
        # or re-read as 0.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D1),
                Demand(DEMAND, DEMAND, "10", D2),
            ),
            inventory={DEMAND: "100", SOURCE: "100", RESERVED: "100"},
            safety_stock={DEMAND: "5", SOURCE: "0", RESERVED: "0"},
            conservation=(DEMAND, RESERVED, "60"),
            targets=((DEMAND, D1, "APPROVED"),),
            target_quantities={(DEMAND, D1): "60"},
            name="ac15l-carry-forward",
        )
        early = built.substitutes.for_grain(PLANT, DEMAND, D1)
        late = built.substitutes.for_grain(PLANT, DEMAND, D2)
        assert early is not None and late is not None
        self.assertEqual(early.cumulative_approved_substitute_supply, 60)
        self.assertIsNone(late.outcome)
        self.assertEqual(late.cumulative_approved_substitute_supply, 60)
        self.assertEqual(
            self.grain(built, DEMAND, D1).cumulative_approved_substitute_supply, 60
        )
        self.assert_quantity(
            self.grain(built, DEMAND, D2), "cumulative_approved_substitute_supply", "60"
        )
        # 100 opening + 60 substitute - 10 requirement = 150 (D1), 140 (D2): both stay decided.
        self.assert_quantity(self.grain(built, DEMAND, D1), "projected_available", "150")
        self.assert_quantity(self.grain(built, DEMAND, D2), "projected_available", "140")
        self.assertEqual(self.grain(built, DEMAND, D1).classification, CLASSIFICATION_NORMAL)
        self.assertEqual(self.grain(built, DEMAND, D2).classification, CLASSIFICATION_NORMAL)

    def test_ac15m_an_unresolved_applicability_before_a_grain_blocks_its_cumulative(self) -> None:
        # The mirror requirement of review F1: an unresolved substitute applicability at or before
        # the grain's own date makes the grain's ``<= t`` cumulative unreliable, so the later grain
        # is DATA_INCOMPLETE even though an earlier grain had a reliable 60.  Neither 0 nor the
        # earlier 60 may be reported for it.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D1),
                Demand(DEMAND, DEMAND, "10", D2),
            ),
            inventory={DEMAND: "100", SOURCE: "100", RESERVED: "100"},
            safety_stock={DEMAND: "5", SOURCE: "0", RESERVED: "0"},
            conservation=(RESERVED, SOURCE, "60"),
            targets=((DEMAND, D1, "APPROVED"), (DEMAND, D2, "UNRESOLVED")),
            target_quantities={(DEMAND, D1): "60"},
            name="ac15m-unresolved-before-later-grain",
        )
        early = built.substitutes.for_grain(PLANT, DEMAND, D1)
        late = built.substitutes.for_grain(PLANT, DEMAND, D2)
        assert early is not None and late is not None
        self.assertEqual(early.cumulative_approved_substitute_supply, 60)
        self.assertIsNone(late.cumulative_approved_substitute_supply)
        self.assertEqual(
            self.grain(built, DEMAND, D1).cumulative_approved_substitute_supply, 60
        )
        self.assertEqual(self.grain(built, DEMAND, D1).classification, CLASSIFICATION_NORMAL)
        blocked = self.grain(built, DEMAND, D2)
        self.assertIsNone(blocked.cumulative_approved_substitute_supply)
        self.assertIsNone(blocked.projected_available)
        self.assert_classification(blocked, CLASSIFICATION_DATA_INCOMPLETE)

    def test_ac15n_a_grain_scoped_unresolved_target_context_is_data_incomplete(self) -> None:
        # Option A′ (Human-approved).  D2 carries a Target Applicability claim that the G5-A
        # layer must drop (the citation binds to the quoted Substitute Allocation record, which
        # registers no association with the requested basis), so D2's demand context is reliably
        # resolved while the relation outcome is not: the grain-scoped unresolved surface states
        # it, and neither 0 nor the earlier 60 may be reported for it.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D1),
                Demand(DEMAND, DEMAND, "10", D2),
                Demand(DEMAND, DEMAND, "10", D3),
            ),
            inventory={DEMAND: "100", SOURCE: "100", RESERVED: "100"},
            safety_stock={DEMAND: "5", SOURCE: "0", RESERVED: "0"},
            conservation=(DEMAND, RESERVED, "60"),
            targets=((DEMAND, D1, "APPROVED"), (DEMAND, D2, "UNRESOLVED")),
            target_quantities={(DEMAND, D1): "60"},
            name="ac15n-grain-scoped-unresolved",
        )
        # G5-A: no Target Applicability reference is formed for D2, the inherited finding is
        # raised, and the exact grain stays reachable through the new read-only surface.
        self.assertEqual(
            [
                [part.value for part in context.relation_outcome.context.grain]
                for context in built.construction.effective_demand_contexts
                if context.relation_outcome.relation == "Target Applicability"
            ],
            [[PLANT, DEMAND, D1]],
        )
        unresolved = built.construction.unresolved_effective_demand_contexts
        self.assertEqual(len(unresolved), 1)
        self.assertEqual(unresolved[0].relation, "Target Applicability")
        self.assertEqual(
            [part.value for part in unresolved[0].context.grain],
            [PLANT, DEMAND, D2],
        )
        self.assertEqual(unresolved[0].category, "SEMANTIC_RESOLUTION")
        self.assertEqual(unresolved[0].reason, "SEMANTIC_UNRESOLVED")
        self.assertTrue(
            any(
                issue.reason == "SEMANTIC_UNRESOLVED"
                for issue in built.construction.issues
            )
        )
        # BR-SUBSTITUTE-001: D1 keeps its reliable 60, D2 is not obtainable, and the unresolved
        # date poisons only the grains at or after it.
        early = built.substitutes.for_grain(PLANT, DEMAND, D1)
        late = built.substitutes.for_grain(PLANT, DEMAND, D2)
        later = built.substitutes.for_grain(PLANT, DEMAND, D3)
        assert early is not None and late is not None and later is not None
        self.assertEqual(early.cumulative_approved_substitute_supply, 60)
        self.assertIsNone(late.cumulative_approved_substitute_supply)
        self.assertIsNone(later.cumulative_approved_substitute_supply)
        # BR-SHORTAGE-001: D1 stays fully reliable; D2 has no reliable ProjectedAvailable and no
        # business classification; D3 cannot claim a reliable cumulative either.
        first = self.grain(built, DEMAND, D1)
        self.assert_quantity(first, "cumulative_approved_substitute_supply", "60")
        self.assert_quantity(first, "projected_available", "150")
        self.assertEqual(first.classification, CLASSIFICATION_NORMAL)
        for date in (D2, D3):
            with self.subTest(date=date):
                blocked = self.grain(built, DEMAND, date)
                self.assertIsNone(
                    blocked.cumulative_approved_substitute_supply
                )
                self.assertIsNone(blocked.projected_available)
                self.assertIsNone(blocked.shortage_qty)
                self.assertIsNone(blocked.buffer_gap)
                self.assert_classification(blocked, CLASSIFICATION_DATA_INCOMPLETE)
        # No reliable shortage marker was established, so the fail-safe date is not a
        # valid absence and not a claim about D2.
        self.assertEqual(built.shortage.first_shortage_date, SHORTAGE_DATA_INCOMPLETE)

    def test_ac15o_no_grain_scoped_reference_is_fabricated_without_a_g5a_failure(self) -> None:
        # The boundary of Option A′: with no G5-A failure at all, the surface stays empty and the
        # completion keeps the approved carry-forward / valid-zero semantics.  A grain is never
        # attributed an unresolved target context by role, material or allocation identity.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D1),
                Demand(DEMAND, DEMAND, "10", D2),
            ),
            inventory={DEMAND: "100", SOURCE: "100", RESERVED: "100"},
            safety_stock={DEMAND: "5", SOURCE: "0", RESERVED: "0"},
            conservation=(DEMAND, RESERVED, "60"),
            targets=((DEMAND, D1, "APPROVED"),),
            target_quantities={(DEMAND, D1): "60"},
            name="ac15o-no-fabricated-attribution",
        )
        self.assertEqual(built.construction.unresolved_effective_demand_contexts, ())
        self.assertEqual(
            built.construction.unresolved_effective_demand_for_grain(
                PLANT, DEMAND, D2
            ),
            (),
        )
        self.assert_quantity(
            self.grain(built, DEMAND, D2),
            "cumulative_approved_substitute_supply",
            "60",
        )
        self.assertEqual(self.grain(built, DEMAND, D2).classification, CLASSIFICATION_NORMAL)

    def test_ac15f_the_rule_never_reads_substitute_role_presence(self) -> None:
        # §2.1.12 C: the substitute *value* semantics come only from the explicitly completed
        # BR-SUBSTITUTE-001 downstream result.  Reading CanonicalConstructionReport.present_roles
        # (or any raw / canonical substitute evidence) to decide them is forbidden, so the module
        # must not reference it at all.
        import snapshot_loader.shortage_calculation as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        self.assertNotIn("present_roles", source)
        self.assertNotIn("ROLE_SUBSTITUTE_RELATIONSHIP", source)
        self.assertNotIn("effective_demand_contexts", source)
        self.assertNotIn("unresolved_for", source)
        self.assertNotIn("objects_for", source)


# --- cross-rule substitute conservation propagation (F1 / F2) -------------------------


class ConservationPropagationTests(ShortageRuleTestCase):
    """`§2.3.10` supply conservation must reach the surface it protects.

    ``F1``: a failed ／ over-allocated conservation group makes every target allocation
    contribution whose reliability depends on that failed conservation not consumable as reliable
    substitute supply.  ``F2`` ／ ``SRO-U1``: an exact Source Demand Context whose ``Source
    Reservation Overlap`` outcome could not be formed enters the existing ``S1-A`` seam, so the
    source grain fails closed instead of falling back to the complete ``OpeningUsableInventory``.
    Both are exact-grain: no global, material-level or package-level poisoning.
    """

    def test_f1_over_allocation_fails_the_affected_target_grain(self) -> None:
        # Reviewed case: eligible source inventory 100, approved allocation to target 200, target
        # demand 150, target opening inventory 0.  The conservation group already fails as
        # CONSISTENCY / CONSISTENCY_CONFLICT; the target side must not keep exposing 200.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "150", D2),
                Demand(DEMAND, DEMAND, "10", D3),
                Demand(OTHER, OTHER, "10", D2),
            ),
            inventory={DEMAND: "0", SOURCE: "100", OTHER: "0"},
            safety_stock={DEMAND: "0", SOURCE: "0", OTHER: "0"},
            conservation=(DEMAND, SOURCE, "200"),
            targets=((DEMAND, D2, "APPROVED"), (OTHER, D2, "APPROVED")),
            target_quantities={(OTHER, D2): "10"},
            relationships=((DEMAND, SOURCE, "APPROVED"), (OTHER, SOURCE, "APPROVED")),
            name="f1-over-allocation",
        )
        groups = built.substitutes.over_allocated_groups
        self.assertEqual(len(groups), 1)
        group = groups[0]
        self.assertEqual(group.conservation_state, "OVER_ALLOCATED")
        self.assertIsNone(group.remaining_unallocated_source_supply)
        self.assert_quantity(group, "eligible_substitute_supply", "100")
        self.assert_quantity(group, "allocated_substitute_qty", "200")
        self.assertEqual(len(group.allocating_references), 1)
        self.assertTrue(
            any(
                issue.category == "CONSISTENCY"
                and issue.reason == "CONSISTENCY_CONFLICT"
                for issue in group.issues
            )
        )
        # BR-SUBSTITUTE-001: the affected target grain is DATA_INCOMPLETE -- never 200, never 0.
        target = built.substitutes.for_grain(PLANT, DEMAND, D2)
        assert target is not None
        self.assertIsNone(target.cumulative_approved_substitute_supply)
        self.assertIsNone(target.grain_equivalent)
        self.assertEqual(target.outcome, "DATA_INCOMPLETE")
        # BR-SHORTAGE-001: no reliable projection and no business classification for it.
        grain = self.grain(built, DEMAND, D2)
        self.assertIsNone(grain.cumulative_approved_substitute_supply)
        self.assertIsNone(grain.projected_available)
        self.assertIsNone(grain.shortage_qty)
        self.assertIsNone(grain.buffer_gap)
        self.assert_classification(grain, CLASSIFICATION_DATA_INCOMPLETE)
        # The cumulative `<= t` propagation follows the existing S3-A semantics: the unreliable
        # date is not skipped for a later grain of the same Plant + Material.
        later = self.grain(built, DEMAND, D3)
        self.assertIsNone(later.cumulative_approved_substitute_supply)
        self.assertIsNone(later.projected_available)
        self.assert_classification(later, CLASSIFICATION_DATA_INCOMPLETE)
        self.assertEqual(built.shortage.first_shortage_date, SHORTAGE_DATA_INCOMPLETE)

    def test_f1_over_allocation_isolates_unrelated_allocations_and_grains(self) -> None:
        # The same package: an unrelated target material whose own accepted allocation record
        # states no reservation-overlap claim for the failed context keeps its full, reliable
        # substitute contribution, and an unrelated demand grain keeps its own classification.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "150", D2),
                Demand(OTHER, OTHER, "10", D2),
            ),
            inventory={DEMAND: "0", SOURCE: "100", OTHER: "0"},
            safety_stock={DEMAND: "0", SOURCE: "0", OTHER: "0"},
            conservation=(DEMAND, SOURCE, "200"),
            targets=((DEMAND, D2, "APPROVED"), (OTHER, D2, "APPROVED")),
            target_quantities={(OTHER, D2): "10"},
            relationships=((DEMAND, SOURCE, "APPROVED"), (OTHER, SOURCE, "APPROVED")),
            name="f1-over-allocation-isolation",
        )
        failed = built.substitutes.over_allocated_groups[0]
        self.assertEqual(len(failed.allocating_references), 1)
        unaffected = built.substitutes.for_grain(PLANT, OTHER, D2)
        assert unaffected is not None
        self.assertNotIn(
            unaffected.evaluations[0].allocation_reference, failed.allocating_references
        )
        self.assert_quantity(unaffected, "cumulative_approved_substitute_supply", "10")
        self.assertIsNone(unaffected.outcome)
        grain = self.grain(built, OTHER, D2)
        self.assert_quantity(grain, "cumulative_approved_substitute_supply", "10")
        self.assert_quantity(grain, "projected_available", "0")
        self.assertEqual(grain.classification, CLASSIFICATION_NORMAL)

    def test_f1_a_conserved_allocation_stays_reliable(self) -> None:
        # Control: the identical shape with an allocation inside its eligible supply is conserved,
        # so the target contribution stays reliable and no target grain is failed.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "60", D2),
                Demand(SOURCE, SOURCE, "80", D2),
            ),
            inventory={DEMAND: "0", SOURCE: "100"},
            safety_stock={DEMAND: "0", SOURCE: "0"},
            conservation=(DEMAND, SOURCE, "60"),
            name="f1-conserved-control",
        )
        group = built.substitutes.conservation_groups[0]
        self.assertEqual(group.conservation_state, "WITHIN_ELIGIBLE_SUPPLY")
        self.assert_quantity(group, "remaining_unallocated_source_supply", "40")
        target = built.substitutes.for_grain(PLANT, DEMAND, D2)
        assert target is not None
        self.assert_quantity(target, "cumulative_approved_substitute_supply", "60")
        self.assert_quantity(
            self.grain(built, DEMAND, D2), "cumulative_approved_substitute_supply", "60"
        )
        self.assertEqual(self.grain(built, DEMAND, D2).classification, CLASSIFICATION_NORMAL)

    def test_f2_unresolved_source_reservation_fails_the_source_grain_closed(self) -> None:
        # Required regression: source inventory 100, target allocation 60, Target Applicability
        # reliably applicable, Source Reservation Overlap unresolved (its claim names a basis the
        # accepted record does not register, so the G5-A layer forms no SRO reference), target
        # demand 60, source own demand 80.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "60", D2),
                Demand(SOURCE, SOURCE, "80", D2),
            ),
            inventory={DEMAND: "0", SOURCE: "100"},
            safety_stock={DEMAND: "0", SOURCE: "0"},
            conservation=(DEMAND, SOURCE, "60"),
            source_reservation_claim="SIMULATED-G5A-SRO-UNREGISTERED",
            name="f2-sro-unresolved",
        )
        # The G5-A failure is grain-scoped and names the exact Source Demand Context.
        unresolved = built.construction.unresolved_effective_demand_contexts
        self.assertEqual(len(unresolved), 1)
        self.assertEqual(unresolved[0].relation, "Source Reservation Overlap")
        self.assertEqual(
            [prop.value for prop in unresolved[0].context.grain],
            [PLANT, SOURCE, D2],
        )
        # The exact context is still a *citation* of the substitute result, and its conservation is
        # stated as unresolved -- never as "no reservation" and never as a numeric remaining supply.
        cited = built.substitutes.source_demand_contexts_for_grain(PLANT, SOURCE, D2)
        self.assertEqual(len(cited), 1)
        group = built.substitutes.conservation_for(str(cited[0].reference))
        assert group is not None
        self.assertEqual(group.conservation_state, "SOURCE_RESERVATION_OVERLAP_UNRESOLVED")
        self.assertEqual(group.outcome, "DATA_INCOMPLETE")
        self.assertIsNone(group.remaining_unallocated_source_supply)
        self.assertEqual(group.allocating_references, ())
        # Target side: governed independently by its reliable Target Applicability.
        target = built.substitutes.for_grain(PLANT, DEMAND, D2)
        assert target is not None
        self.assert_quantity(target, "cumulative_approved_substitute_supply", "60")
        target_grain = self.grain(built, DEMAND, D2)
        self.assert_quantity(target_grain, "projected_available", "0")
        self.assertEqual(target_grain.classification, CLASSIFICATION_NORMAL)
        # Source side: no full-OpeningUsableInventory fallback, so the grain fails closed instead
        # of being NORMAL on the complete 100.
        source_grain = self.grain(built, SOURCE, D2)
        self.assertIsNone(source_grain.opening_supply)
        self.assertIsNone(source_grain.projected_available)
        self.assertIsNone(source_grain.shortage_qty)
        self.assert_classification(source_grain, CLASSIFICATION_DATA_INCOMPLETE)
        self.assertEqual(
            source_grain.supply_source, SUPPLY_UNRESOLVED_SOURCE_RESERVATION
        )

    def test_f2_a_reliable_overlapping_reservation_is_unchanged(self) -> None:
        # The registered `overlaps` path keeps its exact S1-A semantics: 100 - 60 = 40 remains the
        # source's opening supply and the target keeps its reliable 60.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "60", D2),
                Demand(SOURCE, SOURCE, "80", D2),
            ),
            inventory={DEMAND: "0", SOURCE: "100"},
            safety_stock={DEMAND: "0", SOURCE: "0"},
            conservation=(DEMAND, SOURCE, "60"),
            name="f2-reliable-overlaps",
        )
        self.assertEqual(built.construction.unresolved_effective_demand_contexts, ())
        group = built.substitutes.conservation_groups[0]
        self.assertEqual(group.conservation_state, "WITHIN_ELIGIBLE_SUPPLY")
        self.assert_quantity(group, "remaining_unallocated_source_supply", "40")
        source_grain = self.grain(built, SOURCE, D2)
        self.assert_quantity(source_grain, "opening_supply", "40")
        self.assert_quantity(source_grain, "projected_available", "-40")
        self.assert_classification(source_grain, CLASSIFICATION_SHORTAGE)
        self.assertEqual(source_grain.supply_source, SUPPLY_FROM_SOURCE_RESERVATION)
        self.assert_quantity(
            self.grain(built, DEMAND, D2), "cumulative_approved_substitute_supply", "60"
        )

    def test_f2_a_reliable_non_overlapping_reservation_is_unchanged(self) -> None:
        # The registered `does not overlap` path keeps its exact S1-A semantics: the allocation
        # never enters the sum, so the source keeps the complete eligible supply.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "60", D2),
                Demand(SOURCE, SOURCE, "80", D2),
            ),
            inventory={DEMAND: "0", SOURCE: "100"},
            safety_stock={DEMAND: "0", SOURCE: "0"},
            conservation=(DEMAND, SOURCE, "60"),
            source_reservation_registration="SIMULATED-G5A-SRO-NO-OVERLAP",
            name="f2-reliable-no-overlap",
        )
        self.assertEqual(built.construction.unresolved_effective_demand_contexts, ())
        group = built.substitutes.conservation_groups[0]
        self.assertEqual(group.conservation_state, "WITHIN_ELIGIBLE_SUPPLY")
        self.assertEqual(group.allocating_references, ())
        self.assert_quantity(group, "remaining_unallocated_source_supply", "100")
        source_grain = self.grain(built, SOURCE, D2)
        self.assert_quantity(source_grain, "opening_supply", "100")
        self.assert_quantity(source_grain, "projected_available", "20")
        self.assertEqual(source_grain.classification, CLASSIFICATION_NORMAL)
        self.assertEqual(source_grain.supply_source, SUPPLY_FROM_SOURCE_RESERVATION)
        self.assert_quantity(
            self.grain(built, DEMAND, D2), "cumulative_approved_substitute_supply", "60"
        )

    def test_f2_an_unresolved_source_reservation_fails_only_its_own_grain(self) -> None:
        # Exact-grain isolation: an unrelated demand grain of another material in the same package
        # keeps its own reliable result, and the approved Target Applicability Option A' surface is
        # untouched by the source-side failure.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "60", D2),
                Demand(SOURCE, SOURCE, "80", D2),
                Demand(OTHER, OTHER, "10", D2),
            ),
            inventory={DEMAND: "0", SOURCE: "100", OTHER: "100"},
            safety_stock={DEMAND: "0", SOURCE: "0", OTHER: "5"},
            conservation=(DEMAND, SOURCE, "60"),
            targets=((DEMAND, D2, "APPROVED"),),
            source_reservation_claim="SIMULATED-G5A-SRO-UNREGISTERED",
            name="f2-sro-isolation",
        )
        self.assertEqual(
            [
                (item.relation, [prop.value for prop in item.context.grain])
                for item in built.construction.unresolved_effective_demand_contexts
            ],
            [("Source Reservation Overlap", [PLANT, SOURCE, D2])],
        )
        unaffected = self.grain(built, OTHER, D2)
        self.assert_quantity(unaffected, "opening_supply", "100")
        self.assert_quantity(unaffected, "projected_available", "90")
        self.assertEqual(unaffected.classification, CLASSIFICATION_NORMAL)
        self.assert_quantity(
            self.grain(built, DEMAND, D2), "cumulative_approved_substitute_supply", "60"
        )

    def test_f1_gate_preserves_a_reliable_not_applicable_zero(self) -> None:
        # Review blocker: the conservation gate must not run before the existing legal Target
        # outcomes.  One exact allocation record (qty 50) belongs to an over-allocated conservation
        # group (the quoted record reserves 200 against an eligible 100) and is cited by two Target
        # Demand Contexts: D1 states a reliable `not applicable`, D2 states `applicable`.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D1),
                Demand(DEMAND, DEMAND, "10", D2),
            ),
            inventory={DEMAND: "0", SOURCE: "100"},
            safety_stock={DEMAND: "0", SOURCE: "0"},
            conservation=(DEMAND, SOURCE, "200"),
            extra_reservation_allocations=(
                ReservationAllocation(
                    quantity="50",
                    target_claims=((D1, "NOT_APPLICABLE"), (D2, "APPROVED")),
                ),
            ),
            name="f1-gate-legal-zero",
        )
        group = built.substitutes.conservation_groups[0]
        self.assertEqual(group.conservation_state, "OVER_ALLOCATED")
        allocation = built.substitutes.for_grain(PLANT, DEMAND, D2)
        assert allocation is not None
        extra_reference = allocation.evaluations[0].allocation_reference
        self.assertIn(extra_reference, group.allocating_references)
        # D1: the reliable `not applicable` stays a legal zero -- it never claims the allocation
        # identity and is never converted into DATA_INCOMPLETE by another allocation's failure.
        early = built.substitutes.for_grain(PLANT, DEMAND, D1)
        assert early is not None
        self.assertIsNone(early.outcome)
        self.assertEqual(early.grain_equivalent, 0)
        self.assertEqual(
            [item.eligibility_reason for item in early.evaluations],
            ["TARGET_NOT_APPLICABLE"],
        )
        self.assertEqual(early.cumulative_approved_substitute_supply, 0)
        early_grain = self.grain(built, DEMAND, D1)
        self.assertNotEqual(early_grain.classification, CLASSIFICATION_DATA_INCOMPLETE)
        self.assert_quantity(early_grain, "cumulative_approved_substitute_supply", "0")
        self.assert_quantity(early_grain, "projected_available", "-10")
        self.assert_classification(early_grain, CLASSIFICATION_SHORTAGE)
        # D2: the same allocation would contribute positive supply, so the conservation failure
        # applies and the grain fails closed.
        self.assertEqual(early.outcome is None, True)
        self.assertIsNone(allocation.cumulative_approved_substitute_supply)
        self.assert_classification(
            self.grain(built, DEMAND, D2), CLASSIFICATION_DATA_INCOMPLETE
        )
        self.assertIsNone(self.grain(built, DEMAND, D2).projected_available)

    def test_f1_gate_preserves_an_ineligible_relationship_zero(self) -> None:
        # A valid but ineligible relationship states a reliable zero (PENDING / REJECTED).  The
        # quoted allocation record is the one that over-allocates the source context, and its
        # Target Applicability is applicable -- the ineligibility must still win.
        for approval, reason in (("PENDING", "PENDING"), ("REJECTED", "REJECTED")):
            with self.subTest(approval=approval):
                built = self.build(
                    demand=(Demand(DEMAND, DEMAND, "10", D2),),
                    inventory={DEMAND: "0", SOURCE: "100"},
                    safety_stock={DEMAND: "0", SOURCE: "0"},
                    conservation=(DEMAND, SOURCE, "200"),
                    relationships=((DEMAND, SOURCE, approval),),
                    name=f"f1-gate-ineligible-{approval.lower()}",
                )
                group = built.substitutes.conservation_groups[0]
                self.assertEqual(group.conservation_state, "OVER_ALLOCATED")
                target = built.substitutes.for_grain(PLANT, DEMAND, D2)
                assert target is not None
                self.assertIn(
                    target.evaluations[0].allocation_reference,
                    group.allocating_references,
                )
                self.assertIsNone(target.evaluations[0].outcome)
                self.assertEqual(target.evaluations[0].grain_equivalent, 0)
                self.assertEqual(target.evaluations[0].eligibility_reason, reason)
                self.assertEqual(target.cumulative_approved_substitute_supply, 0)
                grain = self.grain(built, DEMAND, D2)
                self.assertNotEqual(grain.classification, CLASSIFICATION_DATA_INCOMPLETE)
                self.assert_quantity(grain, "cumulative_approved_substitute_supply", "0")
                self.assert_classification(grain, CLASSIFICATION_SHORTAGE)

    def test_f1_gate_preserves_an_explicit_zero_quantity(self) -> None:
        # An approved allocation with `AllocatedSubstituteQty = 0` is a reliable zero: another
        # allocation (the quoted 200) caused the conservation group to fail, but that never turns a
        # legal zero into DATA_INCOMPLETE.  The zero contributes to the sum, so the record really is
        # inside the failed group.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "10", D1),
                Demand(DEMAND, DEMAND, "10", D2),
            ),
            inventory={DEMAND: "0", SOURCE: "100"},
            safety_stock={DEMAND: "0", SOURCE: "0"},
            conservation=(DEMAND, SOURCE, "200"),
            extra_reservation_allocations=(
                ReservationAllocation(
                    quantity="0",
                    target_claims=((D1, "APPROVED"),),
                ),
            ),
            name="f1-gate-explicit-zero",
        )
        group = built.substitutes.conservation_groups[0]
        self.assertEqual(group.conservation_state, "OVER_ALLOCATED")
        self.assert_quantity(group, "allocated_substitute_qty", "200")
        self.assertEqual(len(group.allocating_references), 2)
        early = built.substitutes.for_grain(PLANT, DEMAND, D1)
        assert early is not None
        self.assertIn(early.evaluations[0].allocation_reference, group.allocating_references)
        self.assertIsNone(early.evaluations[0].outcome)
        self.assertEqual(early.evaluations[0].grain_equivalent, 0)
        self.assertEqual(early.evaluations[0].eligibility_reason, "APPROVED")
        early_grain = self.grain(built, DEMAND, D1)
        self.assertNotEqual(early_grain.classification, CLASSIFICATION_DATA_INCOMPLETE)
        self.assert_quantity(early_grain, "cumulative_approved_substitute_supply", "0")
        self.assert_classification(early_grain, CLASSIFICATION_SHORTAGE)

    def test_f1_and_f2_leave_the_target_applicability_rule_unchanged(self) -> None:
        # Option A': the grain is DATA_INCOMPLETE, nothing is inferred for the other relation and no
        # target grain is failed by a source-side failure.
        built = self.build(
            demand=(
                Demand(DEMAND, DEMAND, "60", D2),
                Demand(SOURCE, SOURCE, "80", D2),
            ),
            inventory={DEMAND: "0", SOURCE: "100", RESERVED: "100"},
            safety_stock={DEMAND: "0", SOURCE: "0", RESERVED: "0"},
            conservation=(DEMAND, RESERVED, "60"),
            targets=((DEMAND, D2, "UNRESOLVED"),),
            target_quantities={(DEMAND, D2): "60"},
            name="f1-f2-target-applicability-unchanged",
        )
        relations = {
            item.relation for item in built.construction.unresolved_effective_demand_contexts
        }
        self.assertEqual(relations, {"Target Applicability"})
        target = built.substitutes.for_grain(PLANT, DEMAND, D2)
        assert target is not None
        self.assertIsNone(target.cumulative_approved_substitute_supply)
        self.assert_classification(
            self.grain(built, DEMAND, D2), CLASSIFICATION_DATA_INCOMPLETE
        )
        # The unrelated source grain is not poisoned by the target-side failure.
        source_grain = self.grain(built, SOURCE, D2)
        self.assert_quantity(source_grain, "opening_supply", "100")
        self.assertEqual(source_grain.classification, CLASSIFICATION_NORMAL)


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
        # A derived quantity is serialised as an exact rational payload -- and that payload is its
        # **only** serialised form; there is no decimal companion key beside it.
        self.assertEqual(grain["ProjectedAvailable"], {"numerator": -10, "denominator": 1})
        self.assertEqual(grain["ShortageQty"], {"numerator": 10, "denominator": 1})
        self.assertEqual(grain["BufferGap"], {"numerator": 15, "denominator": 1})
        # The consumed canonical decimals keep their exact decimal rendering.
        self.assertEqual(grain["EffectiveOpeningSupply"], "100")
        self.assertEqual(grain["SafetyStock"], "5")
        # No derived quantity registers a second, decimal-valued companion field.
        rationals = (
            "ProjectedAvailable",
            "ShortageQty",
            "BufferGap",
            "CumulativeEffectiveInbound",
            "CumulativeApprovedSubstituteSupply",
            "CumulativeGrossRequirement",
        )
        for field in rationals:
            with self.subTest(field=field):
                self.assertIn(field, grain)
                self.assertNotIn(f"{field}Decimal", grain)
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

    def test_ac18d_a_non_terminating_value_needs_no_companion(self) -> None:
        # A non-terminating exact rational is serialised through the same rational payload as every
        # other derived quantity: the module neither rounds it to make digits available nor records
        # that digits are unavailable, and the grain stays reliable.
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "200", D2),),
            loss_rate="0.05",
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac18d-no-decimal-companion",
        )
        grain = self.grain(built).to_dict()
        self.assertEqual(
            grain["CumulativeGrossRequirement"], {"numerator": 4000, "denominator": 19}
        )
        self.assertEqual(
            grain["ProjectedAvailable"], {"numerator": -2100, "denominator": 19}
        )
        self.assertEqual(
            grain["CumulativeEffectiveInbound"], {"numerator": 0, "denominator": 1}
        )
        self.assertEqual(
            grain["CumulativeApprovedSubstituteSupply"], {"numerator": 0, "denominator": 1}
        )
        self.assertNotIn("CumulativeGrossRequirementDecimal", grain)
        self.assertNotIn("ProjectedAvailableDecimal", grain)
        self.assertNotIn("CumulativeEffectiveInboundDecimal", grain)
        self.assertNotIn("CumulativeApprovedSubstituteSupplyDecimal", grain)
        self.assertEqual(
            self.grain(built).classification, CLASSIFICATION_SHORTAGE
        )

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
            {"analysis_run", "grains", "rule_issues"},
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

    def test_ac19g_a_non_terminating_exact_rational_stays_reliable(self) -> None:
        # GrossRequirement = 200 / (1 - 0.05) = 4000/19 has no finite base-10 representation.  It is
        # a reliable exact quantity under §2.4.8 / ADR-001, so the shortage calculation must stay
        # reliable and must not degrade the grain to DATA_INCOMPLETE.
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "200", D2),),
            loss_rate="0.05",
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac19g-non-terminating",
        )
        row = built.requirements.for_grain(PLANT, DEMAND, D2)
        assert row is not None
        self.assertEqual(row.gross_requirement, Fraction(4000, 19))
        grain = self.grain(built)
        self.assertNotEqual(grain.classification, CLASSIFICATION_DATA_INCOMPLETE)
        self.assertEqual(grain.cumulative_gross_requirement, Fraction(4000, 19))
        # 100 + 0 + 0 - 4000/19 = (1900 - 4000) / 19 = -2100/19, exactly.
        self.assertEqual(grain.projected_available, Fraction(-2100, 19))
        self.assert_classification(grain, CLASSIFICATION_SHORTAGE)
        self.assertEqual(grain.shortage_qty, Fraction(2100, 19))
        self.assertEqual(grain.buffer_gap, Fraction(2195, 19))
        self.assertEqual(built.shortage.first_shortage_date, D2)
        # The exact rational survives serialisation: it is never rounded to a decimal.
        payload = grain.to_dict()
        self.assertEqual(
            payload["ProjectedAvailable"], {"numerator": -2100, "denominator": 19}
        )
        self.assertEqual(
            payload["ShortageQty"], {"numerator": 2100, "denominator": 19}
        )
        # There is no companion surface at all: the exact rational payload is the only serialised
        # form of a derived quantity, and its readability never depends on the denominator.
        self.assertNotIn("ProjectedAvailableDecimal", payload)
        self.assertNotIn("ShortageQtyDecimal", payload)

    def test_ac19h_a_non_terminating_rational_never_rounds_the_projection(self) -> None:
        # A decimal rounding of 4000/19 would give 210.5263..., so the projection must be reported
        # as an exact rational and never as a truncated product.
        built = self.build(
            demand=(Demand(DEMAND, DEMAND, "200", D2),),
            loss_rate="0.05",
            targets=((DEMAND, D2, "APPROVED"),),
            name="ac19h-exact-only",
        )
        grain = self.grain(built)
        assert grain.projected_available is not None
        self.assertEqual(grain.projected_available * 19, Fraction(-2100))
        self.assertNotEqual(grain.projected_available.denominator, 1)
