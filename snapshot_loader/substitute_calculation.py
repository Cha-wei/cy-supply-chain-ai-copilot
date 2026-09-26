"""``BR-SUBSTITUTE-001`` -- Cumulative Approved Substitute Supply (``§2.3``).

The rule answers:

> 某 Target Material 在某个 ``required_date`` 之前，可以从**已批准的替代关系**获得多少**等效供给**。

Input boundary (no raw artifact is ever re-read): the already constructed
:class:`~snapshot_loader.canonical_objects.CanonicalConstructionReport` (resolved
``Substitute Relationship`` ／ ``Substitute Allocation`` objects and the G5-A read-only
effective demand context references) plus the already computed
:class:`~snapshot_loader.inventory_calculation.InventoryCalculationResult`
(``BR-INVENTORY-001``).

Two independent consumption surfaces (``§4.1.13`` D: the two G5-A relations are never
collapsed into one Boolean, and per ``CB-1'`` they are never forced into a joint pair):

* **Target side** -- each G5-A ``Target Applicability`` reference carries its own exact
  ``Target Demand Context``; a target grain is the context grain
  ``plant_id`` + ``target_material_code`` + ``required_date`` (``§2.3.2``) and
  ``CumulativeApprovedSubstituteSupply`` accumulates every ``applicable`` allocation of it;
* **Source side** -- each G5-A ``Source Reservation Overlap`` reference carries its own exact
  ``Source Demand Context``, and that exact resolved context reference **is** the approved
  ``B2-A'`` conservation grouping boundary.

Allocation multiplicity: per Human Decision ``Option A'-R`` several accepted
``Substitute Allocation`` records may share one allocation grain, and each is one independent
explicit allocation contribution.  Canonicalization retains every one of them with its own
``record_reference``; **this rule** is where the authorized aggregation happens, and it binds
each G5-A reference to exactly its own allocation record (no first ／ last wins, no
same-value dedup, no borrowing another record's quantity).

Implemented here, and only here:

* the exact ``Substitute Relationship`` <-> ``Substitute Allocation`` join on
  ``plant_id`` + ``target_material_code`` + ``substitute_material_code``;
* exact ``APPROVED`` relationship eligibility (``§2.3.5``), ``substitution_ratio > 0``
  (``§2.3.6``) and ``AllocatedSubstituteQty >= 0`` (``§2.3.7``);
* ``EquivalentTargetQty`` ／ ``CumulativeApprovedSubstituteSupply`` (``§2.3.12``);
* the approved **B1-A** eligible-substitute-supply boundary: exactly one reliably consumable
  ``InventoryTarget`` for the exact ``plant_id`` + ``source_material_code``, otherwise
  ``DATA_INCOMPLETE``;
* the approved **B2-A'** conservation requirement: every allocation whose Source Reservation
  Overlap is ``overlaps`` for the *same exact resolved Source Demand Context reference* enters
  that context's conservation group, so ``Σ AllocatedSubstituteQty <= EligibleSubstituteSupply``
  and ``RemainingUnallocatedSourceSupply = EligibleSubstituteSupply - Σ`` (``§2.3.10``).

Deliberately **not** implemented here: ``BR-SHORTAGE-001`` (``ProjectedAvailable`` ／
``Classification`` ／ ``FirstShortageDate``), ``BR-PROCUREMENT-001``, ``BR-SUPPLIER-RISK-001``,
any reservation-group ／ demand-window field, any time-overlap algorithm, any Adapter ／ ERP
mapping, any persistence and any quantity precision ／ rounding policy.

Numeric semantics follow the registered precedent (``BR-REQUIREMENT-001`` ／ ``ADR-001``): the
multiplication runs on exact :class:`fractions.Fraction` operands and the derived quantities are
expressed as an exact rational payload -- never via ``float``, never rounded, never quantized and
never through the ``Decimal`` default context.  The eligible source supply is consumed as the
exact ``ExactQuantity`` that ``BR-INVENTORY-001`` produced.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Iterable, Mapping

from .canonical_objects import (
    ABSENT,
    DEMAND_CONTEXT_SOURCE,
    DEMAND_CONTEXT_TARGET,
    RELATION_SOURCE_RESERVATION_OVERLAP,
    RELATION_TARGET_APPLICABILITY,
    ROLE_SUBSTITUTE_ALLOCATION,
    ROLE_SUBSTITUTE_RELATIONSHIP,
    CanonicalConstructionReport,
    CanonicalObject,
    EvidenceReference,
    RelationOutcomeReference,
)
from .constants import (
    CATEGORY_SEMANTIC_RESOLUTION,
    LAYER_2,
    REASON_SEMANTIC_UNRESOLVED,
)
from .exact_quantity import ExactQuantity, parse_exact_quantity
from .inventory_calculation import InventoryCalculationResult, InventoryTarget
from .issues import Issue
from .requirement_calculation import OUTCOME_DATA_INCOMPLETE

# --- vocabulary --------------------------------------------------------------------

#: The rule identity this module implements.
SUBSTITUTE_RULE_ID: str = "BR-SUBSTITUTE-001"

#: The registered failure outcome.  It is the same canonical ``DATA_INCOMPLETE`` business
#: outcome; this module exposes it under a substitute-specific name so the rule modules can
#: re-export it without colliding.  No new outcome vocabulary is created.
SUBSTITUTE_DATA_INCOMPLETE: str = OUTCOME_DATA_INCOMPLETE

#: The only relationship approval state that may participate (``§2.3.5``).
APPROVED_APPROVAL_STATUS: str = "APPROVED"

#: Valid but ineligible approval states: they contribute ``0`` and are **not** a defect
#: (``§4.4.89``).  ``PENDING`` is not yet approved; ``REJECTED`` is a known rejection.
INELIGIBLE_APPROVAL_STATUSES: frozenset[str] = frozenset({"PENDING", "REJECTED"})

#: The registered approval vocabulary (``§4.2.14``).  A missing ／ unknown ／ invalid state is
#: never mapped onto ``APPROVED`` and never silently treated as ``0`` (``§2.3.5``).
REGISTERED_APPROVAL_STATUSES: frozenset[str] = (
    frozenset({APPROVED_APPROVAL_STATUS}) | INELIGIBLE_APPROVAL_STATUSES
)

#: Registered runtime reason literals for the eligibility ／ conservation trace.  They are trace
#: labels only -- **not** a new Validation taxonomy, not a canonical vocabulary and not a wire
#: property.
ELIGIBLE_APPROVED: str = "APPROVED"
INELIGIBLE_PENDING: str = "PENDING"
INELIGIBLE_REJECTED: str = "REJECTED"
EXCLUDED_NOT_APPLICABLE: str = "TARGET_NOT_APPLICABLE"
EXCLUDED_NO_RESERVATION: str = "SOURCE_NO_RESERVATION"

#: Runtime conservation states of one exactly resolved Source Demand Context reference, for
#: trace only.
CONSERVATION_WITHIN_LIMIT: str = "WITHIN_ELIGIBLE_SUPPLY"
CONSERVATION_OVER_ALLOCATED: str = "OVER_ALLOCATED"
CONSERVATION_SOURCE_SUPPLY_UNRESOLVED: str = "SOURCE_SUPPLY_UNRESOLVED"
CONSERVATION_OVERLAP_UNRESOLVED: str = "SOURCE_RESERVATION_OVERLAP_UNRESOLVED"

#: The exact join key of ``Substitute Relationship`` and ``Substitute Allocation``
#: (``§4.1.4`` F ／ G -- both entities share this canonical identity).
SUBSTITUTE_JOIN_PROPERTIES: tuple[str, ...] = (
    "plant_id",
    "target_material_code",
    "substitute_material_code",
)

#: The exact G5-A demand context grain (``§2.3.2``).
TARGET_CONTEXT_PROPERTIES: tuple[str, ...] = (
    "plant_id",
    "material_code",
    "required_date",
)


def _rational_payload(value: Fraction | None) -> dict[str, int] | None:
    """Lossless deterministic serialisation of an exact rational derived quantity.

    ``{"numerator": <integer>, "denominator": <positive integer>}`` -- the in-memory
    representation of a derived substitute quantity, never a truncated decimal expansion and
    never a rounded quantity.  Only the Human-approved derived quantities
    (``EquivalentTargetQty`` ／ ``CumulativeApprovedSubstituteSupply``) are expressed this way;
    ``EligibleSubstituteSupply`` ／ ``RemainingUnallocatedSourceSupply`` keep the exact
    :class:`ExactQuantity` representation they are consumed ／ produced in.
    """

    if value is None:
        return None
    return {"numerator": value.numerator, "denominator": value.denominator}


def _as_rational(value: Any) -> Fraction | None:
    """Return the exact rational value of a canonical quantity, or ``None``.

    The canonical base-10 decimal representation is converted to a :class:`Fraction` without an
    intermediate binary float and without touching the ``Decimal`` default context.  A value
    that is not a registered exact non-negative quantity is **not** coerced.
    """

    if isinstance(value, ExactQuantity):
        return Fraction(value.units, 10**value.scale)
    quantity = parse_exact_quantity(value)
    return None if quantity is None else Fraction(quantity.units, 10**quantity.scale)


# --- result representation ---------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SubstituteEvaluation:
    """One explicit allocation evaluated against one exact Demand Context.

    ``allocation_reference`` is the accepted ``Substitute Allocation`` record reference the G5-A
    reference had to bind to (Allocation-resolution boundary); when that binding cannot be
    established no quantity is read and the evaluation is ``DATA_INCOMPLETE``.
    """

    plant_id: Any
    target_material_code: Any
    required_date: Any
    allocation_reference: str
    relation: str
    substitute_material_code: Any = None
    relationship_reference: str | None = None
    allocated_substitute_qty: ExactQuantity | None = None
    substitution_ratio: Any = None
    target_applicability: Any = None
    source_reservation_overlap: Any = None
    equivalent_target_qty: Fraction | None = None
    outcome: str | None = None
    eligibility_reason: str | None = None
    notes: tuple[str, ...] = ()
    allocation_provenance: EvidenceReference | None = None
    relationship_provenance: EvidenceReference | None = None
    demand_context_reference: Any = None
    demand_context_provenance: EvidenceReference | None = None
    inherited_issues: tuple[Issue, ...] = ()
    rule_issues: tuple[Issue, ...] = ()

    @property
    def data_incomplete(self) -> bool:
        return self.outcome == SUBSTITUTE_DATA_INCOMPLETE

    @property
    def contributes(self) -> bool:
        """Whether this allocation adds eligible equivalent supply to the target grain."""

        return (
            self.outcome is None
            and self.equivalent_target_qty is not None
            and self.equivalent_target_qty > 0
        )

    @property
    def issues(self) -> tuple[Issue, ...]:
        return _deduplicate_issues(self.inherited_issues + self.rule_issues)

    def to_dict(self) -> dict[str, object]:
        return {
            "rule": SUBSTITUTE_RULE_ID,
            "target": {
                "plant_id": self.plant_id,
                "material_code": self.target_material_code,
                "required_date": self.required_date,
            },
            "relation": self.relation,
            "allocation_reference": self.allocation_reference,
            "relationship_reference": self.relationship_reference,
            "substitute_material_code": self.substitute_material_code,
            "AllocatedSubstituteQty": _quantity_text(self.allocated_substitute_qty),
            "substitution_ratio": self.substitution_ratio,
            "TargetApplicability": self.target_applicability,
            "SourceReservationOverlap": self.source_reservation_overlap,
            "EquivalentTargetQty": _rational_payload(self.equivalent_target_qty),
            "outcome": self.outcome,
            "eligibility_reason": self.eligibility_reason,
            "notes": list(self.notes),
            "allocation_provenance": _provenance_payload(self.allocation_provenance),
            "relationship_provenance": _provenance_payload(self.relationship_provenance),
            "demand_context_reference": self.demand_context_reference,
            "demand_context_provenance": _provenance_payload(
                self.demand_context_provenance
            ),
            "inherited_issues": [issue.to_dict() for issue in self.inherited_issues],
            "rule_issues": [issue.to_dict() for issue in self.rule_issues],
        }


@dataclass(frozen=True, slots=True)
class SubstituteTarget:
    """One Target Demand Context grain: ``plant_id`` + ``material_code`` + ``required_date``.

    ``cumulative_approved_substitute_supply`` is ``None`` when the target is
    ``DATA_INCOMPLETE``; a normalised cumulative supply is never produced for an unreliable
    target.  The grain comes from the resolved G5-A context reference -- the rule never invents
    a ``required_date``.
    """

    plant_id: Any
    material_code: Any
    required_date: Any
    evaluations: tuple[SubstituteEvaluation, ...]
    cumulative_approved_substitute_supply: Fraction | None
    outcome: str | None = None
    notes: tuple[str, ...] = ()
    inherited_issues: tuple[Issue, ...] = ()
    rule_issues: tuple[Issue, ...] = ()

    @property
    def data_incomplete(self) -> bool:
        return self.outcome == SUBSTITUTE_DATA_INCOMPLETE

    @property
    def contributing_evaluations(self) -> tuple[SubstituteEvaluation, ...]:
        return tuple(item for item in self.evaluations if item.contributes)

    @property
    def eligible_target_qty(self) -> int:
        return len(self.contributing_evaluations)

    @property
    def issues(self) -> tuple[Issue, ...]:
        return _deduplicate_issues(self.inherited_issues + self.rule_issues)

    def to_dict(self) -> dict[str, object]:
        return {
            "rule": SUBSTITUTE_RULE_ID,
            "plant_id": self.plant_id,
            "material_code": self.material_code,
            "required_date": self.required_date,
            "eligible_target_qty": self.eligible_target_qty,
            "CumulativeApprovedSubstituteSupply": _rational_payload(
                self.cumulative_approved_substitute_supply
            ),
            "outcome": self.outcome,
            "notes": list(self.notes),
            "evaluations": [item.to_dict() for item in self.evaluations],
            "inherited_issues": [issue.to_dict() for issue in self.inherited_issues],
            "rule_issues": [issue.to_dict() for issue in self.rule_issues],
        }


@dataclass(frozen=True, slots=True)
class ConservationGroup:
    """One exact resolved Source Demand Context reference and its conservation outcome.

    ``reservation_context`` is the exact G5-A Source Demand Context reference -- the approved
    ``B2-A'`` grouping boundary.  Allocations whose Source Reservation Overlap is ``overlaps``
    for this exact context are summed together; no cross-context merge and no date proximity
    ever happens.
    """

    reservation_context: str
    plant_id: Any
    source_material_code: Any
    source_demand_context_reference: Any
    eligible_substitute_supply: ExactQuantity | None
    allocated_substitute_qty: ExactQuantity | None
    remaining_unallocated_source_supply: ExactQuantity | None
    allocating_references: tuple[str, ...]
    conservation_state: str | None = None
    outcome: str | None = None
    notes: tuple[str, ...] = ()
    source_supply_provenance: EvidenceReference | None = None
    source_context_provenance: EvidenceReference | None = None
    inherited_issues: tuple[Issue, ...] = ()
    rule_issues: tuple[Issue, ...] = ()

    @property
    def data_incomplete(self) -> bool:
        return self.outcome == SUBSTITUTE_DATA_INCOMPLETE

    @property
    def over_allocated(self) -> bool:
        return self.conservation_state == CONSERVATION_OVER_ALLOCATED

    @property
    def issues(self) -> tuple[Issue, ...]:
        return _deduplicate_issues(self.inherited_issues + self.rule_issues)

    def to_dict(self) -> dict[str, object]:
        return {
            "rule": SUBSTITUTE_RULE_ID,
            "reservation_context": self.reservation_context,
            "plant_id": self.plant_id,
            "source_material_code": self.source_material_code,
            "source_demand_context_reference": self.source_demand_context_reference,
            "EligibleSubstituteSupply": _quantity_text(self.eligible_substitute_supply),
            "AllocatedSubstituteQty": _quantity_text(self.allocated_substitute_qty),
            "RemainingUnallocatedSourceSupply": _quantity_text(
                self.remaining_unallocated_source_supply
            ),
            "allocating_references": list(self.allocating_references),
            "conservation_state": self.conservation_state,
            "outcome": self.outcome,
            "notes": list(self.notes),
            "source_supply_provenance": _provenance_payload(self.source_supply_provenance),
            "source_context_provenance": _provenance_payload(
                self.source_context_provenance
            ),
            "inherited_issues": [issue.to_dict() for issue in self.inherited_issues],
            "rule_issues": [issue.to_dict() for issue in self.rule_issues],
        }


@dataclass(frozen=True, slots=True)
class SubstituteCalculationResult:
    """Deterministic result of ``BR-SUBSTITUTE-001`` for one construction.

    ``targets`` is ordered deterministically by ``plant_id`` + ``material_code`` +
    ``required_date``; ``conservation_groups`` by their exact reservation context reference.  No
    cross-Plant, cross-Material or cross-context aggregation happens, and no context ever wins
    over another.

    ``rule_issues`` is the authoritative result-level finding surface, deduplicated by
    ``location + category + reason``: one logical defect is registered exactly once regardless
    of how many targets re-reached it.
    """

    targets: tuple[SubstituteTarget, ...]
    conservation_groups: tuple[ConservationGroup, ...] = ()
    inherited_issues: tuple[Issue, ...] = ()
    rule_issues: tuple[Issue, ...] = ()

    @property
    def issues(self) -> tuple[Issue, ...]:
        return _deduplicate_issues(self.inherited_issues + self.rule_issues)

    @property
    def data_incomplete_targets(self) -> tuple[SubstituteTarget, ...]:
        return tuple(item for item in self.targets if item.data_incomplete)

    @property
    def over_allocated_groups(self) -> tuple[ConservationGroup, ...]:
        return tuple(item for item in self.conservation_groups if item.over_allocated)

    def for_grain(
        self, plant_id: Any, material_code: Any, required_date: Any
    ) -> SubstituteTarget | None:
        for item in self.targets:
            if (
                item.plant_id == plant_id
                and item.material_code == material_code
                and item.required_date == required_date
            ):
                return item
        return None

    def cumulative_for(
        self, plant_id: Any, material_code: Any, required_date: Any
    ) -> Fraction | None:
        """``CumulativeApprovedSubstituteSupply(<= required_date)`` for one target grain."""

        item = self.for_grain(plant_id, material_code, required_date)
        return None if item is None else item.cumulative_approved_substitute_supply

    def conservation_for(self, reservation_context: str) -> ConservationGroup | None:
        for group in self.conservation_groups:
            if group.reservation_context == reservation_context:
                return group
        return None

    def to_dict(self) -> dict[str, object]:
        return {
            "rule": SUBSTITUTE_RULE_ID,
            "targets": [item.to_dict() for item in self.targets],
            "conservation_groups": [item.to_dict() for item in self.conservation_groups],
            "inherited_issues": [issue.to_dict() for issue in self.inherited_issues],
            "rule_issues": [issue.to_dict() for issue in self.rule_issues],
        }


# --- entry point -------------------------------------------------------------------


def compute_substitute_supply(
    construction: CanonicalConstructionReport,
    inventory: InventoryCalculationResult,
) -> SubstituteCalculationResult:
    """Run ``BR-SUBSTITUTE-001`` over one construction and its inventory result.

    Target grains come from the resolved G5-A ``Target Applicability`` contexts; the candidate
    allocations come only from the resolved ``Substitute Allocation`` canonical objects; the
    eligible source supply comes only from ``BR-INVENTORY-001``'s ``OpeningUsableInventory``.  A
    raw accepted artifact is never read, an Inventory eligibility rule is never re-implemented,
    and no caller may inject a business date or a quantity.
    """

    allocations = _allocation_index(construction)
    relationships = _relationship_index(construction)
    relationship_present, relationship_resolved = _relationship_dataset_state(construction)
    inherited = _deduplicate_issues(construction.issues)

    target_contexts: dict[tuple[Any, Any, Any], list[RelationOutcomeReference]] = {}
    # One entry per **exact** Source Demand Context reference, carrying every G5-A reference that
    # cites it.  ``Option A'-R`` lets several allocations share one context, so the citations are
    # accumulated instead of overwriting: the conservation group owns the aggregation (B2-A').
    source_contexts: dict[str, tuple[tuple[Any, Any, Any], list[RelationOutcomeReference]]] = {}
    for context in construction.effective_demand_contexts:
        outcome = context.relation_outcome
        if outcome.relation == RELATION_TARGET_APPLICABILITY:
            grain = _context_grain(outcome.context, DEMAND_CONTEXT_TARGET)
            if grain is None:
                continue
            target_contexts.setdefault(grain, []).append(outcome)
        elif outcome.relation == RELATION_SOURCE_RESERVATION_OVERLAP:
            source_grain = _context_grain(outcome.context, DEMAND_CONTEXT_SOURCE)
            if source_grain is None:
                continue
            entry = source_contexts.setdefault(
                outcome.context.record_reference, (source_grain, [])
            )
            entry[1].append(outcome)

    targets: list[SubstituteTarget] = []
    for grain in sorted(
        target_contexts, key=lambda item: tuple(_sort_text(part) for part in item)
    ):
        evaluations = tuple(
            _evaluate_target_outcome(
                outcome=outcome,
                grain=grain,
                allocations=allocations,
                relationships=relationships,
                relationship_present=relationship_present,
                relationship_resolved=relationship_resolved,
            )
            for outcome in target_contexts[grain]
        )
        targets.append(_target(grain, evaluations, inherited))

    source_evaluations: list[SubstituteEvaluation] = []
    for key in sorted(source_contexts):
        _grain, outcomes = source_contexts[key]
        for outcome in outcomes:
            source_evaluations.extend(
                _evaluate_source_outcome(
                    outcome=outcome,
                    allocations=allocations,
                )
            )

    conservation = _conservation_groups(
        source_contexts=source_contexts,
        evaluations=source_evaluations,
        inventory=inventory,
    )

    rule_issues: list[Issue] = []
    for item in targets:
        rule_issues.extend(item.rule_issues)
    for group in conservation:
        rule_issues.extend(group.rule_issues)

    return SubstituteCalculationResult(
        targets=tuple(targets),
        conservation_groups=tuple(conservation),
        inherited_issues=inherited,
        rule_issues=_deduplicate_issues(tuple(rule_issues)),
    )


# --- construction index -------------------------------------------------------------


def _allocation_index(
    construction: CanonicalConstructionReport,
) -> dict[str, CanonicalObject]:
    """Resolved ``Substitute Allocation`` objects by their full record reference.

    Only objects the canonicalization actually **resolved** appear here (plus the
    ``substitute_allocations`` surface).  Under ``Option A'-R`` several allocation records may
    share one grain, and every one of them is retained as its own resolved object, so a G5-A
    reference that does not bind to one of them can never obtain a quantity
    (Allocation-resolution boundary).
    """

    index: dict[str, CanonicalObject] = {}
    for obj in tuple(construction.objects_for(ROLE_SUBSTITUTE_ALLOCATION)) + tuple(
        construction.substitute_allocations
    ):
        index.setdefault(obj.record_reference, obj)
    return index


def _relationship_index(
    construction: CanonicalConstructionReport,
) -> dict[tuple[Any, Any, Any], tuple[CanonicalObject, ...]]:
    """Resolved ``Substitute Relationship`` objects grouped by the exact join key.

    Every resolved relationship of a grain is retained: several records on one grain are a legal
    input, so the join can report "not exactly one" instead of a silent representative.
    """

    grouped: dict[tuple[Any, Any, Any], list[CanonicalObject]] = {}
    for obj in construction.objects_for(ROLE_SUBSTITUTE_RELATIONSHIP):
        key = tuple(obj.value_of(name, ABSENT) for name in SUBSTITUTE_JOIN_PROPERTIES)
        if any(value is ABSENT for value in key):
            continue
        grouped.setdefault(key, []).append(obj)
    return {key: tuple(value) for key, value in grouped.items()}


def _relationship_dataset_state(
    construction: CanonicalConstructionReport,
) -> tuple[bool, bool]:
    """Return ``(present, resolved)`` for the accepted package's ``Substitute Relationship`` role.

    ``present`` means the accepted package actually **declared** the ``Substitute Relationship``
    logical dataset (``CanonicalConstructionReport.present_roles``), so a present dataset that
    simply holds no record states "no approved substitute" while an absent role does not: the
    role is ``REQUIRED``, so the rule fails closed instead of producing a legal ``0``
    (``§2.3.11`` A versus the required-role boundary).

    ``resolved`` distinguishes the two present states: a **present but nothing resolved** dataset
    (for example several relationships sharing one grain, which ``Option A'-R`` does **not**
    exempt) may not be read as "business states none", while a present dataset whose records were
    all resolved -- including a supplied dataset that simply holds no record -- states "no
    approved substitute" on this exact grain and is a legal zero.
    """

    present = ROLE_SUBSTITUTE_RELATIONSHIP in construction.present_roles
    resolved = (
        bool(construction.objects_for(ROLE_SUBSTITUTE_RELATIONSHIP))
        or ROLE_SUBSTITUTE_RELATIONSHIP not in construction.unresolved_roles
    )
    return present, resolved


def _context_grain(context: Any, expected_semantic: str) -> tuple[Any, Any, Any] | None:
    """The exact G5-A demand context grain of the expected side, or ``None``.

    The grain is read from the resolved context reference itself; an unsatisfiable context never
    contributes a grain and no date is ever invented.
    """

    if context.semantic != expected_semantic:
        return None
    values = _grain_values(context.grain, TARGET_CONTEXT_PROPERTIES)
    if values is None:
        return None
    if any(value is None or value is ABSENT for value in values):
        return None
    return values


# --- target side -------------------------------------------------------------------


def _evaluate_target_outcome(
    *,
    outcome: RelationOutcomeReference,
    grain: tuple[Any, Any, Any],
    allocations: Mapping[str, CanonicalObject],
    relationships: Mapping[tuple[Any, Any, Any], tuple[CanonicalObject, ...]],
    relationship_present: bool,
    relationship_resolved: bool,
) -> SubstituteEvaluation:
    """Evaluate one G5-A Target Applicability reference for its own target grain."""

    reference = _artifact_ordinal(outcome)
    base: dict[str, Any] = {
        "plant_id": grain[0],
        "target_material_code": grain[1],
        "required_date": grain[2],
        "allocation_reference": reference,
        "relation": outcome.relation,
        "target_applicability": outcome.outcome,
        "demand_context_reference": outcome.context.record_reference,
        "demand_context_provenance": outcome.context.provenance,
    }

    if outcome.outcome is None:
        # The accepted record registered an approved basis that states this relation cannot
        # be reliably determined for the cited demand context.  The grain is real and the
        # capability needs the allocation, so the outcome is DATA_INCOMPLETE -- never a
        # default 0 (§2.3.11 B).
        return _unresolved(
            **base,
            detail=(
                "the cited accepted allocation registers an approved basis for 'Target "
                "Applicability' that states the relation cannot be reliably determined for "
                "this demand context, so the target applicability is unresolved and the "
                "allocation is never treated as an applicable or non-applicable substitute; "
                "the grain stays DATA_INCOMPLETE instead of defaulting to 0 (§2.3.11 B)"
            ),
            location=_target_location(grain, reference),
            affected_evidence=ROLE_SUBSTITUTE_ALLOCATION,
        )

    allocation = allocations.get(_full_reference(outcome.provenance))
    if allocation is None:
        return _unresolved(
            **base,
            detail=(
                "the G5-A reference does not bind to a resolved Substitute Allocation canonical "
                "object, so AllocatedSubstituteQty cannot be obtained; the raw accepted record "
                "is never read and no quantity is guessed (Allocation-resolution boundary)"
            ),
            location=_target_location(grain, reference),
            affected_evidence=ROLE_SUBSTITUTE_ALLOCATION,
        )

    base["allocation_provenance"] = allocation.provenance
    substitute_material = allocation.value_of("substitute_material_code", ABSENT)
    allocated_raw = allocation.value_of("AllocatedSubstituteQty", ABSENT)
    allocated = None if allocated_raw is ABSENT else parse_exact_quantity(allocated_raw)
    base["substitute_material_code"] = (
        None if substitute_material is ABSENT else substitute_material
    )
    base["allocated_substitute_qty"] = allocated

    if substitute_material is ABSENT:
        return _unresolved(
            **base,
            detail=(
                "the resolved Substitute Allocation object states no substitute_material_code, "
                "so the relationship join key is incomplete and the allocation stays "
                "unresolved instead of receiving a default (§2.3.11 B)"
            ),
            location=_target_location(grain, reference),
            affected_evidence=ROLE_SUBSTITUTE_ALLOCATION,
        )
    if allocated is None:
        return _unresolved(
            **base,
            detail=(
                "AllocatedSubstituteQty is missing or is not a registered exact non-negative "
                "quantity; it is never defaulted to 0 and the allocation stays DATA_INCOMPLETE "
                "(§2.3.7)"
            ),
            location=_target_location(grain, reference),
            affected_evidence=ROLE_SUBSTITUTE_ALLOCATION,
        )
    if allocated.negative:
        return _unresolved(
            **base,
            detail=(
                f"AllocatedSubstituteQty {allocated.text()!r} is negative; it is never clamped "
                "and the allocation stays DATA_INCOMPLETE (§2.3.7)"
            ),
            location=_target_location(grain, reference),
            affected_evidence=ROLE_SUBSTITUTE_ALLOCATION,
        )

    relationship, problem = _joined_relationship(
        join_key=(grain[0], grain[1], substitute_material),
        relationships=relationships,
        relationship_present=relationship_present,
        relationship_resolved=relationship_resolved,
    )
    if relationship is None:
        if problem is None:
            # The dataset is present and states no relationship for this exact grain: business
            # states there is no approved substitute, which is a legal zero (§2.3.11 A).
            return _resolved(
                **base, equivalent_target_qty=Fraction(0), eligibility_reason=None
            )
        return _unresolved(
            **base,
            detail=problem,
            location=_target_location(grain, reference),
            affected_evidence=ROLE_SUBSTITUTE_RELATIONSHIP,
        )

    base["relationship_reference"] = relationship.record_reference
    base["relationship_provenance"] = relationship.provenance
    approval = relationship.value_of("approval_status", ABSENT)
    ratio_raw = relationship.value_of("substitution_ratio", ABSENT)
    base["substitution_ratio"] = None if ratio_raw is ABSENT else ratio_raw

    approval_state = _approval_state(
        approval=approval,
        **base,
        location=_target_location(grain, reference),
    )
    if isinstance(approval_state, SubstituteEvaluation):
        return approval_state

    ratio = _as_rational(ratio_raw) if ratio_raw is not ABSENT else None
    if ratio is None:
        return _unresolved(
            **base,
            detail=(
                "substitution_ratio is missing or is not a registered exact quantity; it is "
                "never defaulted to 1.0 and the allocation stays DATA_INCOMPLETE (§2.3.6)"
            ),
            location=_target_location(grain, reference),
            affected_evidence=ROLE_SUBSTITUTE_RELATIONSHIP,
        )
    if ratio <= 0:
        return _unresolved(
            **base,
            detail=(
                f"substitution_ratio {ratio_raw!r} is not greater than 0; it is never clamped or "
                "corrected and the allocation stays DATA_INCOMPLETE (§2.3.6)"
            ),
            location=_target_location(grain, reference),
            affected_evidence=ROLE_SUBSTITUTE_RELATIONSHIP,
        )

    if outcome.outcome == "not applicable":
        # A reliable explicit "not applicable" is a legal 0 contribution (§4.4.89).
        return _resolved(
            **base,
            equivalent_target_qty=Fraction(0),
            eligibility_reason=EXCLUDED_NOT_APPLICABLE,
        )
    if outcome.outcome != "applicable":
        return _unresolved(
            **base,
            detail=(
                f"Target Applicability is {outcome.outcome!r}; the allocation cannot be included "
                "in this target demand context and is never defaulted to applicable (§4.5.9 / "
                "§4.4.60 path B)"
            ),
            location=_target_location(grain, reference),
            affected_evidence=ROLE_SUBSTITUTE_ALLOCATION,
        )

    equivalent = _as_rational(allocated) * ratio
    return _resolved(
        **base, equivalent_target_qty=equivalent, eligibility_reason=ELIGIBLE_APPROVED
    )


def _approval_state(
    *,
    approval: Any,
    location: str,
    **base: Any,
) -> SubstituteEvaluation | str:
    """Classify the joined relationship's approval state.

    Returns :data:`ELIGIBLE_APPROVED` when the state is exactly ``APPROVED``, a legal-zero
    evaluation for the valid-but-ineligible states, or a ``DATA_INCOMPLETE`` evaluation when the
    state cannot be decided (``§2.3.5`` ／ ``§4.4.89``).
    """

    if approval is ABSENT or not isinstance(approval, str):
        return _unresolved(
            **base,
            detail=(
                "the joined Substitute Relationship states no usable approval_status; the state "
                "is never assumed and the allocation stays DATA_INCOMPLETE (§2.3.5)"
            ),
            location=location,
            affected_evidence=ROLE_SUBSTITUTE_RELATIONSHIP,
        )
    if approval not in REGISTERED_APPROVAL_STATUSES:
        return _unresolved(
            **base,
            detail=(
                f"approval_status {approval!r} is not decidable against the registered approval "
                "vocabulary; it is never mapped onto APPROVED and the allocation stays "
                "DATA_INCOMPLETE (§2.3.5)"
            ),
            location=location,
            affected_evidence=ROLE_SUBSTITUTE_RELATIONSHIP,
        )
    if approval in INELIGIBLE_APPROVAL_STATUSES:
        return _resolved(
            **base,
            equivalent_target_qty=Fraction(0),
            eligibility_reason=(
                INELIGIBLE_PENDING if approval == "PENDING" else INELIGIBLE_REJECTED
            ),
        )
    return ELIGIBLE_APPROVED


def _joined_relationship(
    *,
    join_key: tuple[Any, Any, Any],
    relationships: Mapping[tuple[Any, Any, Any], tuple[CanonicalObject, ...]],
    relationship_present: bool,
    relationship_resolved: bool,
) -> tuple[CanonicalObject | None, str | None]:
    """Return the exactly-one applicable relationship, or ``(None, problem)``.

    ``(None, None)`` means "the relationship dataset is present, its records were all resolved,
    and it states none for this exact grain" -- a legal zero (``§2.3.11`` A).  ``(None, problem)``
    means the state is undecidable and the calculation fails closed.  ``Substitute Relationship``
    is **not** covered by the ``Option A'-R`` multiplicity exception, so several relationships on
    one grain stay unresolved, and a present-but-unresolved dataset is never read as "none".
    """

    candidates = relationships.get(join_key, ())
    if not candidates:
        if not relationship_present:
            return None, (
                "the accepted package carries no Substitute Relationship role evidence, so "
                "'business states there is no approved substitute' cannot be established; the "
                "substitute calculation fails closed instead of producing a legal 0 (§2.3.11 A "
                "versus the required-role boundary)"
            )
        if not relationship_resolved:
            return None, (
                "the accepted package carries the Substitute Relationship role but no "
                "Substitute Relationship record resolved, so 'business states there is no "
                "approved substitute' cannot be established for this exact grain; the join key "
                "is never satisfied from an unresolved record and the substitute calculation "
                "fails closed instead of producing a legal 0 (§4.4.102 C Stage A)"
            )
        return None, None
    if len(candidates) > 1:
        return None, (
            f"{len(candidates)} resolved Substitute Relationship records state the join key "
            f"{join_key!r}; exactly one applicable relationship is required and they are never "
            "merged, deduplicated or resolved by first/last wins (§4.4.102 C Stage A)"
        )
    return candidates[0], None


def _target(
    grain: tuple[Any, Any, Any],
    evaluations: tuple[SubstituteEvaluation, ...],
    inherited: tuple[Issue, ...],
) -> SubstituteTarget:
    """Aggregate the eligible evaluations of one target grain (``§2.3.12``)."""

    contributing = [item for item in evaluations if item.contributes]
    unreliable = [item for item in evaluations if item.data_incomplete]
    cumulative: Fraction | None = Fraction(0)
    outcome: str | None = None
    notes: list[str] = []
    if unreliable:
        cumulative = None
        outcome = SUBSTITUTE_DATA_INCOMPLETE
        notes.append(
            f"{len(unreliable)} referenced allocation(s) cannot be reliably evaluated for this "
            "target demand context, so no numeric cumulative approved substitute supply is "
            "produced (§2.3.11 B)"
        )
    else:
        for item in contributing:
            assert item.equivalent_target_qty is not None
            cumulative = cumulative + item.equivalent_target_qty

    inherited_local: list[Issue] = []
    rule_findings: list[Issue] = []
    for item in evaluations:
        inherited_local.extend(item.inherited_issues)
        rule_findings.extend(item.rule_issues)

    return SubstituteTarget(
        plant_id=grain[0],
        material_code=grain[1],
        required_date=grain[2],
        evaluations=evaluations,
        cumulative_approved_substitute_supply=cumulative,
        outcome=outcome,
        notes=tuple(notes),
        inherited_issues=_deduplicate_issues(tuple(inherited) + tuple(inherited_local)),
        rule_issues=_deduplicate_issues(tuple(rule_findings)),
    )


# --- source side ／ conservation (B2-A') --------------------------------------------


def _evaluate_source_outcome(
    *,
    outcome: RelationOutcomeReference,
    allocations: Mapping[str, CanonicalObject],
) -> tuple[SubstituteEvaluation, ...]:
    """Evaluate one G5-A Source Reservation Overlap reference for its own source context.

    The evaluation is attributed to the allocation it cites; the target-side grain fields come
    from the source demand context because this reference carries no Target Demand Context
    (``CB-1'``: the two relations are independent and are never forced into a joint pair).
    """

    reference = _artifact_ordinal(outcome)
    allocation = allocations.get(_full_reference(outcome.provenance))
    grain = _context_grain(outcome.context, DEMAND_CONTEXT_SOURCE)
    base: dict[str, Any] = {
        "plant_id": None if grain is None else grain[0],
        "target_material_code": None if grain is None else grain[1],
        "required_date": None if grain is None else grain[2],
        "allocation_reference": reference,
        "relation": outcome.relation,
        "source_reservation_overlap": outcome.outcome,
        "demand_context_reference": outcome.context.record_reference,
        "demand_context_provenance": outcome.context.provenance,
    }
    if allocation is None:
        return (
            _unresolved(
                **base,
                detail=(
                    "the G5-A source-side reference does not bind to a resolved Substitute "
                    "Allocation canonical object, so AllocatedSubstituteQty cannot be obtained; "
                    "the raw accepted record is never read and no quantity is guessed "
                    "(Allocation-resolution boundary)"
                ),
                location=f"reservation_context[{outcome.context.record_reference}]",
                affected_evidence=ROLE_SUBSTITUTE_ALLOCATION,
            ),
        )
    base["allocation_provenance"] = allocation.provenance
    substitute_material = allocation.value_of("substitute_material_code", ABSENT)
    allocated_raw = allocation.value_of("AllocatedSubstituteQty", ABSENT)
    allocated = None if allocated_raw is ABSENT else parse_exact_quantity(allocated_raw)
    base["substitute_material_code"] = (
        None if substitute_material is ABSENT else substitute_material
    )
    base["allocated_substitute_qty"] = allocated
    plant_from_record = allocation.value_of("plant_id", ABSENT)
    if base["plant_id"] is None and plant_from_record is not ABSENT:
        base["plant_id"] = plant_from_record
    return (
        _resolved(
            **base,
            equivalent_target_qty=None,
            eligibility_reason=(
                None if outcome.outcome == "overlaps" else EXCLUDED_NO_RESERVATION
            ),
        ),
    )


def _conservation_groups(
    *,
    source_contexts: Mapping[
        str, tuple[tuple[Any, Any, Any], list[RelationOutcomeReference]]
    ],
    evaluations: list[SubstituteEvaluation],
    inventory: InventoryCalculationResult,
) -> list[ConservationGroup]:
    """Form one conservation group per exact resolved Source Demand Context reference.

    Only the allocations whose Source Reservation Overlap is ``overlaps`` for that exact context
    enter its sum.  A different exact context is a different group: contexts are never merged,
    never auto-overlapped and never compared by date proximity.
    """

    by_context: dict[str, list[SubstituteEvaluation]] = {}
    for item in evaluations:
        by_context.setdefault(str(item.demand_context_reference), []).append(item)

    groups: list[ConservationGroup] = []
    for reservation_context in sorted(source_contexts):
        outcomes = by_context.get(reservation_context, [])
        _grain, citations = source_contexts[reservation_context]
        if not citations:  # pragma: no cover - a group always carries its citation
            continue
        outcome = citations[0]
        resolved = [item for item in outcomes if item.substitute_material_code is not None]
        if not resolved:
            continue
        sample = resolved[0]
        plant_id = sample.plant_id
        source_material = sample.substitute_material_code

        supply, supply_problem, supply_provenance = _eligible_substitute_supply(
            inventory, plant_id=plant_id, material_code=source_material
        )
        issues: list[Issue] = []
        notes: list[str] = []
        allocated: ExactQuantity | None
        remaining: ExactQuantity | None = None
        state: str | None
        result_outcome: str | None = None
        allocating: tuple[str, ...] = ()

        if supply is None:
            allocated = None
            state = CONSERVATION_SOURCE_SUPPLY_UNRESOLVED
            result_outcome = SUBSTITUTE_DATA_INCOMPLETE
            issues.append(
                _issue(
                    location=(
                        f"source_supply[{_sort_text(plant_id)}/"
                        f"{_sort_text(source_material)}]"
                    ),
                    detail=supply_problem
                    or "EligibleSubstituteSupply cannot be established",
                    category=CATEGORY_SEMANTIC_RESOLUTION,
                    reason=REASON_SEMANTIC_UNRESOLVED,
                    affected_evidence=ROLE_SUBSTITUTE_ALLOCATION,
                    design_reference="§2.3.8 / §2.3.10 (B1-A)",
                    consequence_context=(
                        "the conservation group stays unresolved and no supply conservation "
                        "conclusion is produced"
                    ),
                )
            )
            notes.append(
                "EligibleSubstituteSupply could not be reliably consumed from BR-INVENTORY-001, "
                "so the supply-conservation invariant is not evaluated (§2.3.8 / §2.3.10)"
            )
        else:
            reserved = ExactQuantity(0, 0)
            unreliable = False
            for item in outcomes:
                side = item.source_reservation_overlap
                if side is None:
                    # The accepted record registered an approved basis that states this
                    # relation cannot be reliably determined for this exact context.  The
                    # group is real -- it is keyed by the exact resolved Source Demand
                    # Context -- so it stays DATA_INCOMPLETE rather than being dropped or
                    # treated as non-overlapping (§2.3.11 B).
                    unreliable = True
                    break
                if side == "overlaps":
                    if item.allocated_substitute_qty is None or item.data_incomplete:
                        unreliable = True
                        break
                    reserved = reserved + item.allocated_substitute_qty
                    allocating = allocating + (item.allocation_reference,)
                elif side == "does not overlap":
                    continue
                else:
                    unreliable = True
                    break
            if unreliable:
                allocated = None
                state = CONSERVATION_OVERLAP_UNRESOLVED
                result_outcome = SUBSTITUTE_DATA_INCOMPLETE
                issues.append(
                    _issue(
                        location=f"reservation_context[{reservation_context}]",
                        detail=(
                            "at least one allocation of this exact Source Demand Context states "
                            "no reliable Source Reservation Overlap outcome, so the conservation "
                            "sum cannot be formed; overlap is neither assumed nor denied "
                            "(§2.3.10 / §2.3.11 B / §4.4.60 path B)"
                        ),
                        category=CATEGORY_SEMANTIC_RESOLUTION,
                        reason=REASON_SEMANTIC_UNRESOLVED,
                        affected_evidence=ROLE_SUBSTITUTE_ALLOCATION,
                        design_reference="§2.3.10 / §4.4.60 (B2-A′)",
                        consequence_context=(
                            "the conservation group stays unresolved and no remaining "
                            "unallocated source supply is produced"
                        ),
                    )
                )
                notes.append(
                    "Source Reservation Overlap is unresolved for this exact context, so no "
                    "numeric RemainingUnallocatedSourceSupply is produced (§2.3.10)"
                )
                allocating = ()
            elif reserved > supply:
                allocated = reserved
                state = CONSERVATION_OVER_ALLOCATED
                result_outcome = SUBSTITUTE_DATA_INCOMPLETE
                issues.append(
                    _issue(
                        location=f"reservation_context[{reservation_context}]",
                        detail=(
                            f"Σ AllocatedSubstituteQty {reserved.text()} exceeds "
                            f"EligibleSubstituteSupply {supply.text()} inside this exact Source "
                            "Demand Context; supply is never silently over-allocated (§2.3.10)"
                        ),
                        category="CONSISTENCY",
                        reason="CONSISTENCY_CONFLICT",
                        affected_evidence=ROLE_SUBSTITUTE_ALLOCATION,
                        design_reference="§2.3.10 / §4.4.60 path C (B2-A′)",
                        consequence_context=(
                            "the conservation group is DATA_INCOMPLETE and no remaining "
                            "unallocated source supply is produced"
                        ),
                    )
                )
                notes.append(
                    "the same exact reservation context over-allocates its eligible source "
                    "supply (§2.3.10)"
                )
            else:
                allocated = reserved
                remaining = supply - reserved
                state = CONSERVATION_WITHIN_LIMIT

        groups.append(
            ConservationGroup(
                reservation_context=reservation_context,
                plant_id=plant_id,
                source_material_code=source_material,
                source_demand_context_reference=outcome.context.record_reference,
                eligible_substitute_supply=supply,
                allocated_substitute_qty=allocated,
                remaining_unallocated_source_supply=remaining,
                allocating_references=tuple(sorted(allocating)),
                conservation_state=state,
                outcome=result_outcome,
                notes=tuple(notes),
                source_supply_provenance=supply_provenance,
                source_context_provenance=outcome.context.provenance,
                inherited_issues=(),
                rule_issues=_deduplicate_issues(tuple(issues)),
            )
        )
    return groups


def _eligible_substitute_supply(
    inventory: InventoryCalculationResult,
    *,
    plant_id: Any,
    material_code: Any,
) -> tuple[ExactQuantity | None, str | None, EvidenceReference | None]:
    """The approved **B1-A** consumption boundary of ``BR-INVENTORY-001``.

    Exactly one reliably consumable ``InventoryTarget`` for the exact ``plant_id`` +
    ``source_material_code`` is required; zero or several different ``inventory_snapshot_time``
    targets fail closed.  No earliest ／ latest win, no snapshot sum, no average, no
    ``AnalysisDate`` equivalence and no SafetyStock pre-deduction.

    Consumability is decided by ``OpeningUsableInventory`` itself: the inventory rule sets it to
    ``None`` exactly when the **inventory side** is unreliable, while ``outcome`` is also
    ``DATA_INCOMPLETE`` when only the **SafetyStock side** is unresolved.  SafetyStock is a
    classification threshold (``§2.2.7``) and is never an input to eligible substitute supply, so
    an unresolved SafetyStock alone neither removes a usable target nor blocks the consumption.
    """

    targets = inventory.for_plant_material(plant_id, material_code)
    if not targets:
        return (
            None,
            "BR-INVENTORY-001 produced no target for the exact plant_id + source_material_code "
            "of this source supply, so EligibleSubstituteSupply cannot be established (§2.3.8 / "
            "B1-A)",
            None,
        )
    consumable = [item for item in targets if item.opening_usable_inventory is not None]
    if not consumable:
        return (
            None,
            "every BR-INVENTORY-001 target of this exact plant_id + source_material_code "
            "states no usable OpeningUsableInventory, so EligibleSubstituteSupply cannot be "
            "established (§2.3.8 / B1-A)",
            None,
        )
    if len(consumable) > 1:
        snapshots = sorted(
            {_sort_text(item.inventory_snapshot_time) for item in consumable}
        )
        return (
            None,
            f"{len(consumable)} reliably consumable inventory targets share this exact plant_id "
            f"+ source_material_code across snapshot times {snapshots}; no snapshot ever wins "
            "over another, snapshots are never summed or averaged, and no "
            "inventory_snapshot_time is equated with AnalysisDate, so EligibleSubstituteSupply "
            "stays DATA_INCOMPLETE (§2.3.8 / B1-A)",
            None,
        )
    target: InventoryTarget = consumable[0]
    return target.opening_usable_inventory, None, _supply_provenance(target)


def _supply_provenance(target: InventoryTarget) -> EvidenceReference | None:
    """The provenance of the inventory observations that contributed the eligible supply."""

    for evaluation in target.contributing_evaluations:
        if evaluation.provenance is not None:
            return evaluation.provenance
    for evaluation in target.evaluations:
        if evaluation.provenance is not None:
            return evaluation.provenance
    return None


# --- helpers -----------------------------------------------------------------------


def _artifact_ordinal(outcome: RelationOutcomeReference) -> str:
    """The G5-A runtime record path form of the cited accepted record."""

    artifact = outcome.provenance.artifact or ""
    return f"{artifact}#{outcome.provenance.record_ordinal}"


def _full_reference(provenance: EvidenceReference) -> str:
    """The canonical ``record_reference`` form of a verified G5-A citation."""

    return (
        f"{provenance.snapshot_package_identity}|{provenance.logical_dataset_role}"
        f"|{provenance.artifact}|{provenance.record_ordinal}"
    )


def _grain_values(grain: tuple[Any, ...], names: tuple[str, ...]) -> tuple[Any, ...] | None:
    """Read the named values out of a canonical grain tuple, or ``None`` when absent."""

    values: list[Any] = []
    for name in names:
        found = ABSENT
        for prop in grain:
            if getattr(prop, "name", None) == name:
                found = prop.value
                break
        if found is ABSENT:
            return None
        values.append(found)
    return tuple(values)


def _target_location(grain: tuple[Any, Any, Any], reference: str) -> str:
    return (
        f"target[{_sort_text(grain[0])}/{_sort_text(grain[1])}/{_sort_text(grain[2])}]"
        f":{reference}"
    )


def _resolved(
    *,
    equivalent_target_qty: Fraction | None,
    eligibility_reason: str | None,
    plant_id: Any,
    target_material_code: Any,
    required_date: Any,
    allocation_reference: str,
    relation: str,
    substitute_material_code: Any = None,
    relationship_reference: str | None = None,
    allocated_substitute_qty: ExactQuantity | None = None,
    substitution_ratio: Any = None,
    target_applicability: Any = None,
    source_reservation_overlap: Any = None,
    demand_context_reference: Any = None,
    demand_context_provenance: EvidenceReference | None = None,
    allocation_provenance: EvidenceReference | None = None,
    relationship_provenance: EvidenceReference | None = None,
) -> SubstituteEvaluation:
    return SubstituteEvaluation(
        plant_id=plant_id,
        target_material_code=target_material_code,
        required_date=required_date,
        allocation_reference=allocation_reference,
        relation=relation,
        substitute_material_code=substitute_material_code,
        relationship_reference=relationship_reference,
        allocated_substitute_qty=allocated_substitute_qty,
        substitution_ratio=substitution_ratio,
        target_applicability=target_applicability,
        source_reservation_overlap=source_reservation_overlap,
        equivalent_target_qty=equivalent_target_qty,
        eligibility_reason=eligibility_reason,
        allocation_provenance=allocation_provenance,
        relationship_provenance=relationship_provenance,
        demand_context_reference=demand_context_reference,
        demand_context_provenance=demand_context_provenance,
    )


def _unresolved(
    *,
    detail: str,
    location: str,
    affected_evidence: str,
    plant_id: Any,
    target_material_code: Any,
    required_date: Any,
    allocation_reference: str,
    relation: str,
    substitute_material_code: Any = None,
    relationship_reference: str | None = None,
    allocated_substitute_qty: ExactQuantity | None = None,
    substitution_ratio: Any = None,
    target_applicability: Any = None,
    source_reservation_overlap: Any = None,
    demand_context_reference: Any = None,
    demand_context_provenance: EvidenceReference | None = None,
    allocation_provenance: EvidenceReference | None = None,
    relationship_provenance: EvidenceReference | None = None,
) -> SubstituteEvaluation:
    return SubstituteEvaluation(
        plant_id=plant_id,
        target_material_code=target_material_code,
        required_date=required_date,
        allocation_reference=allocation_reference,
        relation=relation,
        substitute_material_code=substitute_material_code,
        relationship_reference=relationship_reference,
        allocated_substitute_qty=allocated_substitute_qty,
        substitution_ratio=substitution_ratio,
        target_applicability=target_applicability,
        source_reservation_overlap=source_reservation_overlap,
        equivalent_target_qty=None,
        outcome=SUBSTITUTE_DATA_INCOMPLETE,
        allocation_provenance=allocation_provenance,
        relationship_provenance=relationship_provenance,
        demand_context_reference=demand_context_reference,
        demand_context_provenance=demand_context_provenance,
        rule_issues=(
            _issue(
                location=location,
                detail=detail,
                category=CATEGORY_SEMANTIC_RESOLUTION,
                reason=REASON_SEMANTIC_UNRESOLVED,
                affected_evidence=affected_evidence,
                design_reference="§2.3 / §4.4.60 / §4.4.89 / §4.4.102",
                consequence_context=(
                    "the affected allocation stays unresolved for this demand context and no "
                    "equivalent target quantity is produced"
                ),
            ),
        ),
    )


def _issue(
    *,
    location: str,
    detail: str,
    category: str,
    reason: str,
    affected_evidence: str,
    design_reference: str,
    consequence_context: str | None = None,
) -> Issue:
    return Issue(
        location=location,
        detail=detail,
        category=category,
        reason=reason,
        layer=LAYER_2,
        affected_evidence=affected_evidence,
        blast_radius="affected substitute calculation only",
        design_reference=design_reference,
        consequence_context=consequence_context,
    )


def _deduplicate_issues(issues: Iterable[Issue]) -> tuple[Issue, ...]:
    """Keep one logical finding per ``location + category + reason``, deterministically."""

    unique: dict[tuple[str, str, str], Issue] = {}
    for issue in issues:
        unique.setdefault((issue.location, issue.category, issue.reason), issue)
    return tuple(sorted(unique.values(), key=Issue.sort_key))


def _quantity_text(value: ExactQuantity | None) -> str | None:
    """Render a canonical exact quantity losslessly: plain base-10 digits, no exponent."""

    return None if value is None else value.text()


def _provenance_payload(value: EvidenceReference | None) -> dict[str, object] | None:
    if value is None:
        return None
    return {
        "snapshot_package_identity": value.snapshot_package_identity,
        "logical_dataset_role": value.logical_dataset_role,
        "stable_source_evidence_locators": list(value.stable_source_evidence_locators),
        "logical_observation": value.logical_observation,
        "mapping_resolution_basis": value.mapping_resolution_basis,
        "accepted_record_path": value.record_path,
    }


def _sort_text(value: Any) -> str:
    return "" if value is ABSENT or value is None else str(value)


__all__ = [
    "APPROVED_APPROVAL_STATUS",
    "CONSERVATION_OVERLAP_UNRESOLVED",
    "CONSERVATION_OVER_ALLOCATED",
    "CONSERVATION_SOURCE_SUPPLY_UNRESOLVED",
    "CONSERVATION_WITHIN_LIMIT",
    "ConservationGroup",
    "ELIGIBLE_APPROVED",
    "EXCLUDED_NOT_APPLICABLE",
    "EXCLUDED_NO_RESERVATION",
    "INELIGIBLE_APPROVAL_STATUSES",
    "INELIGIBLE_PENDING",
    "INELIGIBLE_REJECTED",
    "REGISTERED_APPROVAL_STATUSES",
    "SUBSTITUTE_DATA_INCOMPLETE",
    "SUBSTITUTE_JOIN_PROPERTIES",
    "SUBSTITUTE_RULE_ID",
    "SubstituteCalculationResult",
    "SubstituteEvaluation",
    "SubstituteTarget",
    "TARGET_CONTEXT_PROPERTIES",
    "compute_substitute_supply",
]
