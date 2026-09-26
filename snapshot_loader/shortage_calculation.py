"""``BR-SHORTAGE-001`` -- Shortage Calculation (``§2.1``).

The rule answers:

> 某 Plant 某 Material 截至某 ``required_date`` 的**累计可用供给**，是否能够覆盖**累计物料需求**。

Calculation grain (``§2.1.1``): ``plant_id`` + ``material_code`` + ``required_date``.

Conceptual formula (``§2.1.2``), evaluated on the ascending grain order
``plant_id`` -> ``material_code`` -> ``required_date``::

    ProjectedAvailable(t)
      = EffectiveOpeningSupply(context)
      + CumulativeEffectiveInbound(<= t)
      + CumulativeApprovedSubstituteSupply(<= t)
      - CumulativeGrossRequirement(<= t)

Only already computed upstream results are consumed -- never a raw accepted artifact and never
a re-implementation of another rule:

* ``CumulativeGrossRequirement``  <- :class:`~snapshot_loader.requirement_calculation.RequirementCalculationResult`
* ``CumulativeEffectiveInbound``  <- :class:`~snapshot_loader.inbound_calculation.EffectiveInboundResult`
* ``CumulativeApprovedSubstituteSupply`` <- :class:`~snapshot_loader.substitute_calculation.SubstituteCalculationResult`
* ``OpeningUsableInventory`` ／ ``SafetyStock`` <- :class:`~snapshot_loader.inventory_calculation.InventoryCalculationResult`

**Upstream cumulative values are consumed exactly once.**  ``CumulativeEffectiveInbound(<= t)``
and ``CumulativeGrossRequirement(<= t)`` are read from the upstream result for the grain at ``t``
and are never passed through a second cumulative sum (``§4.5.9`` Decision 8 ／ AC-31: the same
upstream value is never accumulated twice).  ``CumulativeApprovedSubstituteSupply(<= t)`` is the
upstream rule's own cumulative value carried forward to ``t``; the raw substitute evidence is
never re-read and ``BR-SUBSTITUTE-001`` is never recomputed here.

Human-approved consumption boundaries implemented here:

* **S1-A -- source reservation consumption.**  For an exact Source Demand Context the
  inventory-side opening supply is the ``RemainingUnallocatedSourceSupply`` that
  ``BR-SUBSTITUTE-001`` already produced; the reservation is **never** recomputed here.  An
  already allocated source quantity is therefore never simultaneously consumed as complete
  uncommitted inventory.  An unresolved conservation, or missing ``DATA_INCOMPLETE`` evidence,
  makes the affected shortage grain ``DATA_INCOMPLETE``.
* **S2-A -- inventory snapshot consumption boundary.**  For an exact ``plant_id`` +
  ``material_code``: exactly one reliably consumable ``InventoryTarget`` supplies both
  ``OpeningUsableInventory`` and ``SafetyStock``; zero, or more than one distinct
  ``inventory_snapshot_time``, is ``DATA_INCOMPLETE``.  There is no earliest ／ latest win, no
  cross-snapshot sum, no average and no ``inventory_snapshot_time = AnalysisDate`` equivalence.
* **S3-A -- substitute result completeness.**  A missing ``SubstituteTarget`` is never guessed
  as ``0``: a shortage grain is ``DATA_INCOMPLETE`` whenever the substitute result cannot state
  a numeric cumulative substitute supply for it.

Deliberately **not** implemented here: any new business enum, any canonical field ／ entity ／
identity component, any reservation ／ demand-window field, any snapshot selection algorithm,
any persistence, any external configuration, any Adapter ／ ERP mapping, any LLM ／ Agent
behaviour and any rounding ／ quantization ／ float arithmetic.  ``ADR-001`` is unchanged.

Numeric semantics follow the registered precedent (``BR-REQUIREMENT-001`` ／
``BR-INBOUND-001`` ／ ``BR-INVENTORY-001`` ／ ``BR-SUBSTITUTE-001``): quantities stay exact.
Canonical finite decimals are consumed as
:class:`~snapshot_loader.exact_quantity.ExactQuantity`; an upstream exact rational that has no
finite base-10 representation is **not** truncated or rounded, the affected grain fails as
``DATA_INCOMPLETE`` instead.  No ``float``, no rounding, no quantization and no ``Decimal``
default context is used anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Iterable, Sequence

from .canonical_objects import (
    ABSENT,
    ROLE_SUBSTITUTE_RELATIONSHIP,
    CanonicalConstructionReport,
)
from .constants import (
    CATEGORY_SEMANTIC_RESOLUTION,
    LAYER_2,
    REASON_SEMANTIC_UNRESOLVED,
)
from .exact_quantity import ExactQuantity
from .inbound_calculation import EffectiveInboundResult, EffectiveInboundTarget
from .inventory_calculation import InventoryCalculationResult, InventoryTarget
from .issues import Issue
from .requirement_calculation import (
    OUTCOME_DATA_INCOMPLETE,
    RequirementCalculation,
    RequirementCalculationResult,
)
from .substitute_calculation import (
    ConservationGroup,
    SourceDemandContext,
    SubstituteCalculationResult,
    SubstituteTarget,
)

# --- vocabulary --------------------------------------------------------------------

#: The rule identity this module implements.
SHORTAGE_RULE_ID: str = "BR-SHORTAGE-001"

#: The registered failure outcome (``§2.1.4`` D).  It is the same canonical
#: ``DATA_INCOMPLETE`` business outcome the other rule modules re-export under their own name;
#: no new outcome vocabulary is created.
SHORTAGE_DATA_INCOMPLETE: str = OUTCOME_DATA_INCOMPLETE

#: The three business classifications registered by ``§2.1.4``.  They are the rule's own
#: registered result vocabulary (``§4.2.10``) and are **not** redefined here: no new business
#: enum, no risk level and no severity is introduced (``§2.1.11``).
CLASSIFICATION_NORMAL: str = "NORMAL"
CLASSIFICATION_BUFFER_BREACH: str = "BUFFER_BREACH"
CLASSIFICATION_SHORTAGE: str = "SHORTAGE"
CLASSIFICATION_DATA_INCOMPLETE: str = SHORTAGE_DATA_INCOMPLETE

#: The complete registered classification set.
CLASSIFICATIONS: frozenset[str] = frozenset(
    {
        CLASSIFICATION_NORMAL,
        CLASSIFICATION_BUFFER_BREACH,
        CLASSIFICATION_SHORTAGE,
        CLASSIFICATION_DATA_INCOMPLETE,
    }
)

#: Runtime trace labels for **how** the inventory-side opening supply was obtained.  They are
#: trace labels only -- not a new Validation taxonomy, not a canonical vocabulary, not a new
#: business enum and not a wire property.
SUPPLY_FROM_SOURCE_RESERVATION: str = "REMAINING_UNALLOCATED_SOURCE_SUPPLY"
SUPPLY_FROM_INVENTORY_SNAPSHOT: str = "OPENING_USABLE_INVENTORY"
SUPPLY_UNRESOLVED_SOURCE_RESERVATION: str = "SOURCE_RESERVATION_UNRESOLVED"
SUPPLY_UNRESOLVED_INVENTORY_SNAPSHOT: str = "INVENTORY_SNAPSHOT_UNRESOLVED"
SUPPLY_UNRESOLVED_CITATION_UNATTRIBUTABLE: str = "SOURCE_CITATION_UNATTRIBUTABLE"
SUPPLY_UNRESOLVED_UNASSIGNED_INVENTORY: str = "UNASSIGNED_INVENTORY_EVIDENCE"

#: The exact shortage calculation grain (``§2.1.1``).
SHORTAGE_GRAIN_PROPERTIES: tuple[str, ...] = (
    "plant_id",
    "material_code",
    "required_date",
)

_ZERO = ExactQuantity(0, 0)


# --- exact quantity helpers --------------------------------------------------------


def _decimal_rational(value: Fraction | None) -> ExactQuantity | None:
    """Convert an exact rational into an exact decimal quantity, or ``None``.

    A rational whose reduced denominator factors only into 2 and 5 is exactly representable as
    a finite decimal.  Anything else (for example ``4000/19`` from a non-terminating
    ``loss_rate``) is **not** truncated, rounded, quantized or approximated by a binary float:
    the affected grain fails as ``DATA_INCOMPLETE`` (``§2.4.8`` ／ ``ADR-001``).
    """

    if value is None:
        return None
    numerator, denominator = value.numerator, value.denominator
    scale = 0
    while denominator % 2 == 0:
        denominator //= 2
        numerator *= 5
        scale += 1
    while denominator % 5 == 0:
        denominator //= 5
        numerator *= 2
        scale += 1
    if denominator != 1:
        return None
    return ExactQuantity(numerator, scale)


def _quantity_text(value: ExactQuantity | None) -> str | None:
    """Render a canonical exact quantity losslessly: plain base-10 digits, no exponent."""

    return None if value is None else value.text()


def _provenance_payload(value: Any) -> dict[str, object] | None:
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


def _grain_key(grain: tuple[Any, Any, Any]) -> tuple[str, str, str]:
    """Deterministic ordering key of one shortage grain (never a business ordering)."""

    return (_sort_text(grain[0]), _sort_text(grain[1]), _sort_text(grain[2]))


def _groupable(values: Sequence[Any]) -> bool:
    """Whether a grain can be used as a grouping key at all.

    A canonical grain value is normally a string.  A JSON array ／ object reaching this layer
    would still be *valid* input but is not hashable, so it is never coerced by ``str()`` ／
    ``repr()`` into a group key: the affected family fails closed instead of silently sharing a
    dict key with an unrelated value.
    """

    try:
        hash(tuple(values))
    except TypeError:
        return False
    return True


# --- result representation ---------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ShortageGrain:
    """One result for the registered grain ``plant_id`` + ``material_code`` + ``required_date``.

    ``projected_available`` is ``None`` exactly when ``classification`` is ``DATA_INCOMPLETE`` on
    the input side: a normalised ``ProjectedAvailable`` is never produced for a grain whose
    critical input could not be reliably obtained (``§2.1.4`` D).  ``ProjectedAvailable`` may
    legitimately be negative; the rule never clamps it (``§2.1.5``).  The one case where
    ``projected_available`` is present while the classification is ``DATA_INCOMPLETE`` is an
    unresolved ``SafetyStock``, because the threshold -- not the projection -- is what cannot be
    decided.

    ``first_shortage_date`` ／ ``first_buffer_breach_date`` carry the ascending-order marker of
    this grain's family.  The marker is **fail-safe**: a later reliable ``SHORTAGE`` never
    becomes the reliable first shortage date while an earlier-or-equal grain of the same family
    is ``DATA_INCOMPLETE``, and an already reliable earlier date is never replaced by a later
    one (``§2.1.6``).
    """

    plant_id: Any
    material_code: Any
    required_date: Any
    classification: str
    projected_available: ExactQuantity | None = None
    shortage_qty: ExactQuantity | None = None
    buffer_gap: ExactQuantity | None = None
    safety_stock: ExactQuantity | None = None
    opening_supply: ExactQuantity | None = None
    cumulative_effective_inbound: ExactQuantity | None = None
    cumulative_approved_substitute_supply: ExactQuantity | None = None
    cumulative_gross_requirement: ExactQuantity | None = None
    supply_source: str = SUPPLY_UNRESOLVED_INVENTORY_SNAPSHOT
    source_demand_context_reference: Any = None
    conservation_state: str | None = None
    first_shortage_date: Any = None
    first_buffer_breach_date: Any = None
    outcome: str | None = None
    notes: tuple[str, ...] = ()
    opening_provenance: Any = None
    inherited_issues: tuple[Issue, ...] = ()
    rule_issues: tuple[Issue, ...] = ()

    @property
    def grain(self) -> tuple[Any, Any, Any]:
        return (self.plant_id, self.material_code, self.required_date)

    @property
    def data_incomplete(self) -> bool:
        return self.classification == CLASSIFICATION_DATA_INCOMPLETE

    @property
    def shortage(self) -> bool:
        return self.classification == CLASSIFICATION_SHORTAGE

    @property
    def issues(self) -> tuple[Issue, ...]:
        return _deduplicate_issues(self.inherited_issues + self.rule_issues)

    def to_dict(self) -> dict[str, object]:
        return {
            "rule": SHORTAGE_RULE_ID,
            "plant_id": self.plant_id,
            "material_code": self.material_code,
            "required_date": self.required_date,
            "ProjectedAvailable": _quantity_text(self.projected_available),
            "Classification": self.classification,
            "ShortageQty": _quantity_text(self.shortage_qty),
            "BufferGap": _quantity_text(self.buffer_gap),
            "SafetyStock": _quantity_text(self.safety_stock),
            "EffectiveOpeningSupply": _quantity_text(self.opening_supply),
            "CumulativeEffectiveInbound": _quantity_text(
                self.cumulative_effective_inbound
            ),
            "CumulativeApprovedSubstituteSupply": _quantity_text(
                self.cumulative_approved_substitute_supply
            ),
            "CumulativeGrossRequirement": _quantity_text(
                self.cumulative_gross_requirement
            ),
            "opening_supply_source": self.supply_source,
            "source_demand_context_reference": self.source_demand_context_reference,
            "conservation_state": self.conservation_state,
            "outcome": self.outcome,
            "notes": list(self.notes),
            "opening_provenance": _provenance_payload(self.opening_provenance),
            "inherited_issues": [issue.to_dict() for issue in self.inherited_issues],
            "rule_issues": [issue.to_dict() for issue in self.rule_issues],
        }


@dataclass(frozen=True, slots=True)
class ShortageCalculationResult:
    """Deterministic result of ``BR-SHORTAGE-001`` for one construction.

    ``grains`` is ordered deterministically by ``plant_id`` -> ``material_code`` ->
    ``required_date`` ascending (``§2.1.1`` ／ ``§2.1.2``).  No cross-Plant and no
    cross-Material aggregation ever happens: separate Plants are never combined, and one grain
    has exactly one result even when several requirement contributions share its date.

    ``first_shortage_date`` ／ ``first_buffer_breach_date`` are ``None`` only when the rule can
    reliably state **valid absence** over the whole relevant horizon (``§2.1.6`` ／ ``§4.4.22``).
    When any grain of the horizon is ``DATA_INCOMPLETE`` and no reliable marker was already
    established at an earlier-or-equal date, the corresponding date fails safe to
    ``SHORTAGE_DATA_INCOMPLETE`` -- a valid-absence ``None`` is never produced over an
    unresolved horizon (``§4.4.87``).
    """

    grains: tuple[ShortageGrain, ...]
    rule_issues: tuple[Issue, ...] = ()

    @property
    def issues(self) -> tuple[Issue, ...]:
        return _deduplicate_issues(self.rule_issues)

    @property
    def data_incomplete_grains(self) -> tuple[ShortageGrain, ...]:
        return tuple(item for item in self.grains if item.data_incomplete)

    @property
    def shortage_grains(self) -> tuple[ShortageGrain, ...]:
        return tuple(item for item in self.grains if item.shortage)

    @property
    def first_shortage_date(self) -> Any:
        """The earliest reliable ``ProjectedAvailable < 0`` date, ``None`` or the fail-safe."""

        return _first_marker(self.grains, lambda item: item.shortage)

    @property
    def first_buffer_breach_date(self) -> Any:
        """The earliest reliable ``ProjectedAvailable < SafetyStock`` date, or the fail-safe."""

        return _first_marker(
            self.grains,
            lambda item: (
                not item.data_incomplete
                and item.projected_available is not None
                and item.safety_stock is not None
                and item.projected_available < item.safety_stock
            ),
        )

    def for_grain(
        self, plant_id: Any, material_code: Any, required_date: Any
    ) -> ShortageGrain | None:
        for item in self.grains:
            if (
                item.plant_id == plant_id
                and item.material_code == material_code
                and item.required_date == required_date
            ):
                return item
        return None

    def for_plant_material(
        self, plant_id: Any, material_code: Any
    ) -> tuple[ShortageGrain, ...]:
        return tuple(
            item
            for item in self.grains
            if item.plant_id == plant_id and item.material_code == material_code
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "rule": SHORTAGE_RULE_ID,
            "grains": [item.to_dict() for item in self.grains],
            "FirstShortageDate": self.first_shortage_date,
            "FirstBufferBreachDate": self.first_buffer_breach_date,
            "rule_issues": [issue.to_dict() for issue in self.rule_issues],
        }


def _first_marker(grains: Sequence[ShortageGrain], marker) -> Any:
    """The reliable earliest marker **date** of the whole result, or the ``DATA_INCOMPLETE`` fail-safe.

    ``§2.1.6`` defines both dates over ``required_date`` ascending, and a failure is isolated to
    the affected grain rather than to one Plant ／ Material family, so the scan is a deterministic
    pass over the calendar -- never over the ``plant_id`` -> ``material_code`` order:

    * the earliest reliably established marker date is the answer and is never replaced by a later
      one, so a subsequent ``DATA_INCOMPLETE`` does not move it;
    * an unresolved grain **earlier than** that date would have made the true first date
      unknowable, so it blocks the claim and the result fails safe to
      ``SHORTAGE_DATA_INCOMPLETE``;
    * an unresolved grain at or after the established date cannot move it and is ignored;
    * with no reliable marker at all, ``None`` (valid absence) is produced **only** when no grain
      of the horizon is unresolved; otherwise the result fails safe.
    """

    ordered = sorted(grains, key=lambda item: _sort_text(item.required_date))
    candidate: Any = None
    incomplete_before: Any = None
    for item in ordered:
        if item.data_incomplete:
            if incomplete_before is None:
                incomplete_before = item.required_date
            continue
        if marker(item) and candidate is None:
            candidate = item.required_date
    if candidate is None:
        return SHORTAGE_DATA_INCOMPLETE if incomplete_before is not None else None
    if incomplete_before is not None and _sort_text(incomplete_before) < _sort_text(
        candidate
    ):
        return SHORTAGE_DATA_INCOMPLETE
    return candidate


# --- family (plant_id + material_code) index ---------------------------------------


@dataclass(frozen=True, slots=True)
class _OpeningSupply:
    """The inventory-side opening supply of one family, or why it is not obtainable."""

    quantity: ExactQuantity | None
    source: str
    safety_stock: ExactQuantity | None = None
    source_demand_context_reference: Any = None
    conservation_state: str | None = None
    provenance: Any = None
    problem: str | None = None


@dataclass(frozen=True, slots=True)
class _Family:
    """Every consumed surface of one exact ``plant_id`` + ``material_code`` family.

    The family is the cumulative grouping of ``§2.1.2``.  Nothing is ever carried across
    families: separate Plants and separate Materials never share a running total.
    """

    plant_id: Any
    material_code: Any
    dates: tuple[Any, ...]
    requirements: tuple[RequirementCalculation, ...]
    inbounds: tuple[EffectiveInboundTarget, ...]
    substitutes: tuple[SubstituteTarget, ...]
    sources: tuple[SourceDemandContext, ...]


# --- entry point -------------------------------------------------------------------


def compute_shortage(
    construction: CanonicalConstructionReport,
    requirements: RequirementCalculationResult,
    inbounds: EffectiveInboundResult,
    inventory: InventoryCalculationResult,
    substitutes: SubstituteCalculationResult,
) -> ShortageCalculationResult:
    """Run ``BR-SHORTAGE-001`` over one construction and its four upstream rule results.

    Every input is an already computed deterministic result: no raw accepted artifact is read,
    no upstream rule is re-implemented, no reservation is recomputed and no caller may inject a
    business date, quantity or ``SafetyStock``.  ``construction`` is consumed only for the one
    fact the upstream results cannot state -- whether the ``Substitute Relationship`` role is
    present -- so that a missing substitute dataset fails closed instead of being read as
    "there is no substitute".
    """

    families = _families(requirements, inbounds, substitutes)
    groups = {group.reservation_context: group for group in substitutes.conservation_groups}
    citation_attributable = not substitutes.unattributable_conservation_groups
    substitute_role_present = ROLE_SUBSTITUTE_RELATIONSHIP in construction.present_roles
    unassigned_inventory = tuple(inventory.unassigned_inventory_references)

    grains: list[ShortageGrain] = []
    rule_issues: list[Issue] = []
    for family in families:
        opening = _opening_supply(
            inventory,
            family=family,
            groups=groups,
            citation_attributable=citation_attributable,
            unassigned_inventory=unassigned_inventory,
        )
        family_grains = _evaluate_family(
            family,
            opening=opening,
            groups=groups,
            substitute_role_present=substitute_role_present,
        )
        grains.extend(family_grains)
        for item in family_grains:
            rule_issues.extend(item.rule_issues)

    grains.sort(key=lambda item: _grain_key(item.grain))
    return ShortageCalculationResult(
        grains=tuple(grains),
        rule_issues=_deduplicate_issues(tuple(rule_issues)),
    )


def _families(
    requirements: RequirementCalculationResult,
    inbounds: EffectiveInboundResult,
    substitutes: SubstituteCalculationResult,
) -> tuple[_Family, ...]:
    """Group every consumed surface by the exact ``plant_id`` + ``material_code`` family.

    A family is formed only from grains whose own components can be used as a grouping key.  A
    surface that states an ungroupable ``plant_id`` + ``material_code`` is never retyped ／
    stringified into a shared bucket; its registered upstream findings stay visible through the
    consumed result itself.
    """

    keys: list[tuple[Any, Any]] = []
    seen: set[tuple[Any, Any]] = set()

    def note(plant_id: Any, material_code: Any) -> None:
        if not _groupable((plant_id, material_code)):
            return
        key = (plant_id, material_code)
        if key not in seen:
            seen.add(key)
            keys.append(key)

    for row in requirements.calculations:
        note(row.plant_id, row.component_material_code)
    for target in inbounds.targets:
        note(target.plant_id, target.material_code)
    for target in substitutes.targets:
        note(target.plant_id, target.material_code)
    for context in substitutes.source_demand_contexts:
        note(context.plant_id, context.target_material_code)

    keys.sort(key=lambda key: (_sort_text(key[0]), _sort_text(key[1])))

    families: list[_Family] = []
    for plant_id, material_code in keys:
        rows = tuple(
            row
            for row in requirements.calculations
            if row.plant_id == plant_id and row.component_material_code == material_code
        )
        inbound_targets = tuple(
            target
            for target in inbounds.targets
            if target.plant_id == plant_id and target.material_code == material_code
        )
        substitute_targets = tuple(
            target
            for target in substitutes.targets
            if target.plant_id == plant_id and target.material_code == material_code
        )
        source_contexts = tuple(
            context
            for context in substitutes.source_demand_contexts
            if context.plant_id == plant_id
            and context.target_material_code == material_code
        )
        families.append(
            _Family(
                plant_id=plant_id,
                material_code=material_code,
                dates=_horizon(
                    rows, inbound_targets, substitute_targets, source_contexts
                ),
                requirements=rows,
                inbounds=inbound_targets,
                substitutes=substitute_targets,
                sources=source_contexts,
            )
        )
    return tuple(families)


def _horizon(
    requirements: Sequence[RequirementCalculation],
    inbounds: Sequence[EffectiveInboundTarget],
    substitutes: Sequence[SubstituteTarget],
    sources: Sequence[SourceDemandContext],
) -> tuple[Any, ...]:
    """The relevant horizon of one family: every ``required_date`` a consumed surface states.

    The horizon is the union of the dates the upstream results actually state -- the demand
    dates of this family's requirement rows plus every supply-side date that can change the
    running total.  No date is invented, extrapolated or carried over from another family, and
    an already established Plant ／ Material cumulative value is never reused for another one.
    """

    dates: list[Any] = []
    seen: set[Any] = set()

    def note(value: Any) -> None:
        if value is None or value is ABSENT:
            return
        try:
            if value in seen:
                return
            seen.add(value)
        except TypeError:  # pragma: no cover - ungroupable canonical value
            return
        dates.append(value)

    for row in requirements:
        note(row.required_date)
    for target in inbounds:
        note(target.required_date)
    for target in substitutes:
        note(target.required_date)
    for context in sources:
        note(context.required_date)

    dates.sort(key=_sort_text)
    return tuple(dates)


# --- inventory-side opening supply (S1-A / S2-A) ------------------------------------


def _opening_supply(
    inventory: InventoryCalculationResult,
    *,
    family: _Family,
    groups: dict[str, ConservationGroup],
    citation_attributable: bool,
    unassigned_inventory: tuple[str, ...],
) -> _OpeningSupply:
    """Resolve the inventory-side opening supply of one family (``S1-A`` first, then ``S2-A``).

    **S1-A.**  When this exact ``plant_id`` + ``material_code`` grain is cited by a Source Demand
    Context, the source reservation has already consumed part of the inventory, so the supply is
    the ``RemainingUnallocatedSourceSupply`` that ``BR-SUBSTITUTE-001`` produced -- never a
    freshly computed reservation and never the complete uncommitted inventory.  Exactly one
    cited context is consumable; several distinct contexts of one grain would each hand out a
    supply for the same inventory pool and are never merged or resolved by first ／ last ／
    earliest wins, so they fail closed instead.  A cited context that produced no conservation
    group, or one whose ``RemainingUnallocatedSourceSupply`` is unresolved, also fails closed.

    **S2-A.**  For the exact ``plant_id`` + ``material_code``: exactly one reliably consumable
    ``InventoryTarget`` supplies both ``OpeningUsableInventory`` and ``SafetyStock``; zero
    targets, or several targets across different ``inventory_snapshot_time`` values, is
    ``DATA_INCOMPLETE``.  No snapshot ever wins over another, snapshots are never summed or
    averaged, and ``inventory_snapshot_time`` is never equated with ``AnalysisDate``.
    """

    # --- S2-A first, because the classification threshold is an inventory-snapshot fact -----
    snapshot = _inventory_snapshot_supply(inventory, family=family)

    # --- S1-A: the exact Source Demand Context, when business cites one --------------------
    citations = family.sources
    if citations:
        if not citation_attributable:
            # A cited Source Demand Context stating no complete grain cannot be attributed to
            # any family, so no family may fall back to its complete inventory snapshot: that
            # would hand out a quantity the source reservation may already have consumed.
            return _OpeningSupply(
                quantity=None,
                source=SUPPLY_UNRESOLVED_CITATION_UNATTRIBUTABLE,
                safety_stock=snapshot.safety_stock,
                problem=(
                    "at least one cited Source Demand Context states no complete grain, so the "
                    "citation cannot be ruled out for this exact plant_id + material_code and "
                    "the inventory-side supply cannot be resolved from the remaining "
                    "unallocated source supply (§2.1.2 / S1-A)"
                ),
            )
        if len(citations) > 1:
            return _OpeningSupply(
                quantity=None,
                source=SUPPLY_UNRESOLVED_SOURCE_RESERVATION,
                safety_stock=snapshot.safety_stock,
                problem=(
                    f"{len(citations)} distinct exact Source Demand Contexts cite this exact "
                    "plant_id + material_code + required_date; each would consume the same "
                    "inventory pool independently and the current authority cannot decide "
                    "whether their reservation windows overlap, so no supply is handed out for "
                    "it and the affected grains stay DATA_INCOMPLETE (§2.1.2 / S1-A)"
                ),
            )
        context = citations[0]
        group = groups.get(str(context.reference))
        if group is None:
            return _OpeningSupply(
                quantity=None,
                source=SUPPLY_UNRESOLVED_SOURCE_RESERVATION,
                source_demand_context_reference=context.reference,
                provenance=context.provenance,
                safety_stock=snapshot.safety_stock,
                problem=(
                    "the cited exact Source Demand Context produced no conservation group, so "
                    "RemainingUnallocatedSourceSupply is not obtainable; the reservation is "
                    "never recomputed here and the complete inventory is never consumed instead "
                    "(§2.1.2 / S1-A)"
                ),
            )
        if group.remaining_unallocated_source_supply is None:
            return _OpeningSupply(
                quantity=None,
                source=SUPPLY_UNRESOLVED_SOURCE_RESERVATION,
                source_demand_context_reference=context.reference,
                conservation_state=group.conservation_state,
                provenance=_source_context_provenance(group, context),
                safety_stock=snapshot.safety_stock,
                problem=(
                    "the conservation of the cited exact Source Demand Context is unresolved "
                    f"({group.conservation_state}), so no reliable "
                    "RemainingUnallocatedSourceSupply exists and the affected shortage grains "
                    "stay DATA_INCOMPLETE instead of consuming the complete inventory "
                    "(§2.1.2 / S1-A)"
                ),
            )
        return _OpeningSupply(
            quantity=group.remaining_unallocated_source_supply,
            source=SUPPLY_FROM_SOURCE_RESERVATION,
            safety_stock=snapshot.safety_stock,
            source_demand_context_reference=context.reference,
            conservation_state=group.conservation_state,
            provenance=_source_context_provenance(group, context),
        )

    if unassigned_inventory:
        # An accepted Inventory observation whose canonical grain is incomplete is attributed to
        # no concrete target, so it can be ruled out for no family: the full-inventory fallback
        # cannot be relied on for this one either.
        return _OpeningSupply(
            quantity=None,
            source=SUPPLY_UNRESOLVED_UNASSIGNED_INVENTORY,
            safety_stock=snapshot.safety_stock,
            problem=(
                f"{len(unassigned_inventory)} accepted Inventory observation(s) state no "
                "complete canonical grain and belong to no inventory target, so they can be "
                "ruled out for no plant_id + material_code and the inventory snapshot boundary "
                "cannot be decided (§2.1.2 / S2-A)"
            ),
        )

    return snapshot


def _inventory_snapshot_supply(
    inventory: InventoryCalculationResult, *, family: _Family
) -> _OpeningSupply:
    """The approved ``S2-A`` inventory snapshot consumption boundary."""

    targets = inventory.for_plant_material(family.plant_id, family.material_code)
    if not targets:
        # BR-INVENTORY-001 produces a target for every exact Plant + Material grain it can form
        # from the accepted observations.  No target at all therefore states that the accepted
        # package carries no inventory evidence for this exact grain: the opening supply is the
        # legal 0 of §4.4.88, not an unresolved value.
        return _OpeningSupply(
            quantity=_ZERO,
            source=SUPPLY_FROM_INVENTORY_SNAPSHOT,
            safety_stock=_ZERO,
        )

    consumable = [item for item in targets if item.opening_usable_inventory is not None]
    if not consumable:
        return _OpeningSupply(
            quantity=None,
            source=SUPPLY_UNRESOLVED_INVENTORY_SNAPSHOT,
            problem=(
                "every BR-INVENTORY-001 target of this exact plant_id + material_code states no "
                "usable OpeningUsableInventory, so EffectiveOpeningSupply cannot be established "
                "(§2.1.2 / S2-A)"
            ),
        )
    if len(consumable) > 1:
        snapshots = sorted(
            {_sort_text(item.inventory_snapshot_time) for item in consumable}
        )
        return _OpeningSupply(
            quantity=None,
            source=SUPPLY_UNRESOLVED_INVENTORY_SNAPSHOT,
            problem=(
                f"{len(consumable)} reliably consumable inventory targets share this exact "
                f"plant_id + material_code across snapshot times {snapshots}; no snapshot ever "
                "wins over another, snapshots are never summed or averaged and no "
                "inventory_snapshot_time is equated with AnalysisDate, so EffectiveOpeningSupply "
                "stays DATA_INCOMPLETE (§2.1.2 / S2-A)"
            ),
        )

    target: InventoryTarget = consumable[0]
    if target.safety_stock is None:
        return _OpeningSupply(
            quantity=target.opening_usable_inventory,
            source=SUPPLY_FROM_INVENTORY_SNAPSHOT,
            provenance=_inventory_provenance(target),
            problem=(
                "the single consumable inventory target of this exact plant_id + material_code "
                f"states no reliable SafetyStock ({target.safety_stock_state}), so the "
                "classification threshold cannot be established and the affected grains stay "
                "DATA_INCOMPLETE; SafetyStock is never defaulted to 0 (§2.1.4 / §2.2.7 / S2-A)"
            ),
        )
    return _OpeningSupply(
        quantity=target.opening_usable_inventory,
        source=SUPPLY_FROM_INVENTORY_SNAPSHOT,
        safety_stock=target.safety_stock,
        provenance=_inventory_provenance(target),
    )


def _source_context_provenance(
    group: ConservationGroup | None, context: SourceDemandContext
) -> Any:
    if group is not None and group.source_supply_provenance is not None:
        return group.source_supply_provenance
    if context.provenance is not None:
        return context.provenance
    return None if group is None else group.source_context_provenance


def _inventory_provenance(target: InventoryTarget) -> Any:
    for evaluation in target.contributing_evaluations:
        if evaluation.provenance is not None:
            return evaluation.provenance
    for evaluation in target.evaluations:
        if evaluation.provenance is not None:
            return evaluation.provenance
    return None


# --- per-grain evaluation ----------------------------------------------------------


def _evaluate_family(
    family: _Family,
    *,
    opening: _OpeningSupply,
    groups: dict[str, ConservationGroup],
    substitute_role_present: bool,
) -> list[ShortageGrain]:
    """Evaluate the whole ascending horizon of one family in a single deterministic pass.

    The running total is carried forward grain by grain, so one inventory supply is never
    consumed independently by every required date (``§2.1.2`` ／ Example D).  The inventory-side
    opening supply is a **family-level** value: an exact Source Demand Context reservation is
    deducted once for the whole family (``_opening_supply``) rather than per grain, so the
    cumulative formula cannot consume one reservation N times.  A failure stays local: an
    unresolved grain only affects its own result and the family's fail-safe dates, and never
    another family.
    """

    requirement_table = _requirement_table(family.requirements)
    inbound_table = _inbound_table(family.inbounds)
    substitute_table = _substitute_table(family.substitutes)
    source_entry = _source_entry(family, groups)
    source_cited = bool(family.sources)
    inherited = _family_inherited(family)

    first_shortage: Any = None
    first_breach: Any = None

    results: list[ShortageGrain] = []
    for required_date in family.dates:
        location = (
            f"shortage[{_sort_text(family.plant_id)}/"
            f"{_sort_text(family.material_code)}/{_sort_text(required_date)}]"
        )
        issues: list[Issue] = []
        notes: list[str] = []

        # --- demand side: the upstream cumulative value is consumed exactly once ---------
        gross, gross_problem = requirement_table.get(required_date, (None, None))
        if gross is None:
            issues.append(
                _issue(
                    location=location,
                    detail=gross_problem
                    or "CumulativeGrossRequirement cannot be obtained for this grain",
                    design_reference="§2.1.2 / §2.4.9 / §2.4.11",
                    consequence_context=(
                        "the grain stays DATA_INCOMPLETE and no ProjectedAvailable / "
                        "Classification is produced"
                    ),
                )
            )

        # --- supply side ----------------------------------------------------------------
        inbound, inbound_problem = inbound_table.get(required_date, (None, None))
        if inbound is None:
            issues.append(
                _issue(
                    location=location,
                    detail=inbound_problem
                    or "CumulativeEffectiveInbound cannot be obtained for this grain",
                    design_reference="§2.1.2 / §2.6",
                    consequence_context=(
                        "the grain stays DATA_INCOMPLETE and no ProjectedAvailable / "
                        "Classification is produced"
                    ),
                )
            )

        substitute_supply, substitute_problem, substitute_note = _substitute_supply_for(
            substitute_table,
            required_date,
            source_cited=source_cited,
            role_present=substitute_role_present,
        )
        if substitute_note is not None:
            notes.append(substitute_note)
        if substitute_supply is None:
            issues.append(
                _issue(
                    location=location,
                    detail=substitute_problem
                    or "CumulativeApprovedSubstituteSupply cannot be obtained for this grain",
                    design_reference="§2.1.2 / §2.3.12 / S3-A",
                    consequence_context=(
                        "the grain stays DATA_INCOMPLETE and no ProjectedAvailable / "
                        "Classification is produced; the missing value is never defaulted to 0"
                    ),
                )
            )

        # S1-A: an exactly cited Source Demand Context replaces the complete inventory snapshot
        # with the remaining unallocated source supply of the whole family and is never added on
        # top of it.  The reservation is applied once, at family level (see ``_opening_supply``),
        # so no grain ever consumes it twice.
        source_context_reference = None
        conservation_state = None
        if source_entry is not None:
            context, group = source_entry
            source_context_reference = context.reference
            conservation_state = None if group is None else group.conservation_state

        if opening.problem is not None:
            issues.append(
                _issue(
                    location=location,
                    detail=opening.problem,
                    design_reference="§2.1.2 / §2.1.7 / S1-A / S2-A",
                    consequence_context=(
                        "the grain stays DATA_INCOMPLETE and no EffectiveOpeningSupply is produced"
                    ),
                )
            )

        effective_opening = opening.quantity
        incomplete = any(
            part is None for part in (gross, inbound, substitute_supply, effective_opening)
        )
        safety_stock = None if incomplete else opening.safety_stock

        if incomplete:
            # A grain that could not be decided never claims a reliable first-shortage ／
            # first-breach date of its own: its own marker field stays ``None`` so the per-grain
            # surface can never contradict the result-level fail-safe (§2.1.6 / §2.1.12 E).
            results.append(
                ShortageGrain(
                    plant_id=family.plant_id,
                    material_code=family.material_code,
                    required_date=required_date,
                    classification=CLASSIFICATION_DATA_INCOMPLETE,
                    outcome=SHORTAGE_DATA_INCOMPLETE,
                    safety_stock=None if opening.quantity is None else opening.safety_stock,
                    opening_supply=opening.quantity,
                    cumulative_effective_inbound=inbound,
                    cumulative_approved_substitute_supply=substitute_supply,
                    cumulative_gross_requirement=gross,
                    supply_source=opening.source,
                    source_demand_context_reference=source_context_reference,
                    conservation_state=conservation_state,
                    first_shortage_date=None,
                    first_buffer_breach_date=None,
                    opening_provenance=opening.provenance,
                    notes=(
                        "at least one critical input of this grain could not be reliably "
                        "obtained, so no NORMAL / BUFFER_BREACH / SHORTAGE is produced and no "
                        "reliable first-shortage ／ first-breach date is claimed for it "
                        "(§2.1.4 D / §2.1.7)",
                    ),
                    inherited_issues=inherited,
                    rule_issues=_deduplicate_issues(tuple(issues)),
                )
            )
            continue

        assert gross is not None and inbound is not None
        assert substitute_supply is not None and effective_opening is not None
        projected = effective_opening + inbound + substitute_supply - gross

        if projected < _ZERO:
            classification = CLASSIFICATION_SHORTAGE
        elif safety_stock is None:
            classification = CLASSIFICATION_DATA_INCOMPLETE
            issues.append(
                _issue(
                    location=location,
                    detail=(
                        "the consumable inventory target of this exact plant_id + "
                        "material_code states no reliable SafetyStock, so NORMAL / "
                        "BUFFER_BREACH cannot be decided; SafetyStock is never defaulted to 0 "
                        "and is never taken from another snapshot (§2.1.4 / §2.2.7 / S2-A)"
                    ),
                    design_reference="§2.1.4 / §2.2.7 / S2-A",
                    consequence_context=(
                        "the grain stays DATA_INCOMPLETE and no classification is produced"
                    ),
                )
            )
        elif projected < safety_stock:
            classification = CLASSIFICATION_BUFFER_BREACH
        else:
            classification = CLASSIFICATION_NORMAL

        if classification == CLASSIFICATION_DATA_INCOMPLETE:
            # The projection is exact but the SafetyStock threshold is not decidable, so this
            # grain claims no reliable classification and no first-shortage ／ first-breach date of
            # its own (the result-level fail-safe is the authority, §2.1.6 / §2.1.12 E).
            results.append(
                ShortageGrain(
                    plant_id=family.plant_id,
                    material_code=family.material_code,
                    required_date=required_date,
                    classification=classification,
                    projected_available=projected,
                    safety_stock=safety_stock,
                    opening_supply=opening.quantity,
                    cumulative_effective_inbound=inbound,
                    cumulative_approved_substitute_supply=substitute_supply,
                    cumulative_gross_requirement=gross,
                    supply_source=opening.source,
                    source_demand_context_reference=source_context_reference,
                    conservation_state=conservation_state,
                    first_shortage_date=None,
                    first_buffer_breach_date=None,
                    outcome=SHORTAGE_DATA_INCOMPLETE,
                    opening_provenance=opening.provenance,
                    inherited_issues=inherited,
                    rule_issues=_deduplicate_issues(tuple(issues)),
                )
            )
            continue

        shortage_qty = _ZERO - projected if projected < _ZERO else _ZERO
        buffer_gap = (
            safety_stock - projected
            if safety_stock is not None and projected < safety_stock
            else _ZERO
        )
        if classification == CLASSIFICATION_SHORTAGE and first_shortage is None:
            first_shortage = required_date
        if (
            safety_stock is not None
            and projected < safety_stock
            and first_breach is None
        ):
            first_breach = required_date

        results.append(
            ShortageGrain(
                plant_id=family.plant_id,
                material_code=family.material_code,
                required_date=required_date,
                classification=classification,
                projected_available=projected,
                shortage_qty=shortage_qty,
                buffer_gap=buffer_gap,
                safety_stock=safety_stock,
                opening_supply=opening.quantity,
                cumulative_effective_inbound=inbound,
                cumulative_approved_substitute_supply=substitute_supply,
                cumulative_gross_requirement=gross,
                supply_source=opening.source,
                source_demand_context_reference=source_context_reference,
                conservation_state=conservation_state,
                first_shortage_date=first_shortage,
                first_buffer_breach_date=first_breach,
                outcome=None,
                opening_provenance=opening.provenance,
                inherited_issues=inherited,
                rule_issues=_deduplicate_issues(tuple(issues)),
            )
        )

    return results


# --- per-family source (S1-A) entry ------------------------------------------------


def _source_entry(
    family: _Family,
    groups: dict[str, ConservationGroup],
) -> tuple[SourceDemandContext, ConservationGroup | None] | None:
    """The single family-level ``S1-A`` consumption entry of one family, or ``None``.

    ``None`` means business cites no Source Demand Context for this exact grain, which is the
    legal "no source reservation consumed part of this inventory" case that keeps the full
    ``OpeningUsableInventory`` path (S2-A).  Otherwise the entry is the cited context and the
    conservation group formed for it (possibly ``None``), for the reporting surface only: the
    supply itself is already resolved once per family by :func:`_opening_supply` and is never
    recomputed here.

    The entry is applied **once per family** as the family's inventory-side opening supply, not
    once per grain: the cited context is the reservation boundary of the whole
    ``plant_id`` + ``material_code`` inventory pool, so applying it per grain would consume one
    reservation N times across the cumulative horizon.
    """

    if len(family.sources) != 1:
        # The zero- and several-citation cases are decided once per family by _opening_supply;
        # several citations are already DATA_INCOMPLETE there.
        return None
    context = family.sources[0]
    return (context, groups.get(str(context.reference)))


# --- upstream cumulative tables ----------------------------------------------------


def _date_key(value: Any) -> Any:
    """The usable lookup key of one ``required_date``, or ``ABSENT`` when it cannot index a table.

    ``_horizon`` already refuses to carry an ungroupable date, so a value that cannot index a
    table would mean the horizon and the tables disagreed.  Guarding here keeps the two
    consistent: such a date is never coerced by ``str()`` ／ ``repr()`` into a key that could
    collide with an unrelated date, and the grain simply finds no entry and fails closed.
    """

    try:
        hash(value)
    except TypeError:
        return ABSENT
    return value


def _requirement_table(
    rows: Sequence[RequirementCalculation],
) -> dict[Any, tuple[ExactQuantity | None, str | None]]:
    """``CumulativeGrossRequirement(<= required_date)`` per date, consumed exactly once.

    ``BR-REQUIREMENT-001`` already accumulated the value per ``plant_id`` + component
    ``material_code``; it is read here and **never accumulated a second time**.  Several
    requirement contributions sharing one date all entered that upstream total, so the date maps
    to **one** shortage grain -- the same upstream value is never summed twice (``§2.4.9``).
    """

    per_date: dict[Any, list[Fraction | None]] = {}
    for row in rows:
        key = _date_key(row.required_date)
        if key is ABSENT:
            continue
        per_date.setdefault(key, []).append(row.cumulative_gross_requirement)

    table: dict[Any, tuple[ExactQuantity | None, str | None]] = {}
    for required_date, entries in per_date.items():
        numeric = [entry for entry in entries if entry is not None]
        if len(numeric) != len(entries):
            table[required_date] = (
                None,
                "an upstream BR-REQUIREMENT-001 calculation stating this exact grain is "
                "DATA_INCOMPLETE, so CumulativeGrossRequirement(<= required_date) is not "
                "reliably obtainable and no numeric requirement is consumed for it (§2.4.11)",
            )
            continue
        quantity = _decimal_rational(numeric[0])
        if quantity is None:
            table[required_date] = (
                None,
                "the upstream CumulativeGrossRequirement of this exact grain is an exact "
                "rational with no finite base-10 representation; it is never truncated, "
                "rounded or quantized, so this grain fails as DATA_INCOMPLETE "
                "(§2.4.8 / ADR-001)",
            )
            continue
        table[required_date] = (quantity, None)
    return table


def _inbound_table(
    targets: Sequence[EffectiveInboundTarget],
) -> dict[Any, tuple[ExactQuantity | None, str | None]]:
    """``CumulativeEffectiveInbound(<= required_date)`` per date, carried forward once.

    The upstream target's own cumulative value is non-decreasing in ``required_date``, so the
    value at ``t`` is the upstream value of the latest target at or before ``t``.  That upstream
    value is never passed through a second cumulative sum.  No target at or before ``t`` states
    that no inbound evidence reaches ``t``, which is the legal ``0`` of ``§4.4.88``.
    """

    ordered = sorted(targets, key=lambda item: _sort_text(item.required_date))
    table: dict[Any, tuple[ExactQuantity | None, str | None]] = {}
    carried: ExactQuantity | None = _ZERO
    carried_problem: str | None = None
    for target in ordered:
        if target.cumulative_effective_inbound is None:
            carried = None
            carried_problem = (
                "at least one BR-INBOUND-001 target of this exact grain is DATA_INCOMPLETE, so "
                "the cumulative effective inbound supply at this required date is not reliably "
                "obtainable (§2.6.6)"
            )
        else:
            carried = target.cumulative_effective_inbound
            carried_problem = None
        key = _date_key(target.required_date)
        if key is not ABSENT:
            table[key] = (carried, carried_problem)
    return table


def _substitute_table(
    targets: Sequence[SubstituteTarget],
) -> dict[Any, tuple[ExactQuantity | None, str | None, str | None]]:
    """``CumulativeApprovedSubstituteSupply(<= required_date)`` per date, from the upstream result.

    The value is ``BR-SUBSTITUTE-001``'s own cumulative result for this target grain, carried
    forward to ``t`` and never recomputed from raw or canonical substitute evidence.  A target
    whose own cumulative value is unresolved makes its dates ``DATA_INCOMPLETE``, and an omitted
    target is **never** silently read as ``0`` (S3-A).
    """

    ordered = sorted(targets, key=lambda item: _sort_text(item.required_date))
    table: dict[Any, tuple[ExactQuantity | None, str | None, str | None]] = {}
    carried: ExactQuantity | None = None
    carried_problem: str | None = None
    for target in ordered:
        if target.cumulative_approved_substitute_supply is None:
            carried = None
            carried_problem = (
                "the BR-SUBSTITUTE-001 target of this exact grain states no reliable "
                "CumulativeApprovedSubstituteSupply, so the cumulative approved substitute "
                "supply at this required date is not obtainable and is never defaulted to 0 "
                "(§2.3.12 / S3-A)"
            )
        else:
            quantity = _decimal_rational(target.cumulative_approved_substitute_supply)
            if quantity is None:
                carried = None
                carried_problem = (
                    "the BR-SUBSTITUTE-001 cumulative approved substitute supply of this exact "
                    "grain is an exact rational with no finite base-10 representation; it is "
                    "never truncated, rounded or quantized, so this grain fails as "
                    "DATA_INCOMPLETE (§2.4.8 / ADR-001)"
                )
            else:
                carried = quantity
                carried_problem = None
        key = _date_key(target.required_date)
        if key is not ABSENT:
            table[key] = (carried, carried_problem, None)
    return table


def _substitute_supply_for(
    table: dict[Any, tuple[ExactQuantity | None, str | None, str | None]],
    required_date: Any,
    *,
    source_cited: bool,
    role_present: bool,
) -> tuple[ExactQuantity | None, str | None, str | None]:
    """Resolve one grain's ``CumulativeApprovedSubstituteSupply`` under ``S3-A``.

    The upstream ``BR-SUBSTITUTE-001`` result is the only substitute surface consumed here; raw
    and canonical substitute evidence is never re-read.  Three cases stay strictly apart:

    * the grain is a **cited Target Demand Context** of the substitute result, so its own
      cumulative value is the answer (a numeric value, or the upstream ``DATA_INCOMPLETE``);
    * the grain is a **cited Source Demand Context** -- the substitute rule evaluated it as a
      reservation boundary and no Target Demand Context of that material was cited, so no
      approved substitute supply for it exists at all and the value is the explicit ``0`` of
      ``§4.4.88``, never an omission that looks like zero;
    * neither is cited, so the substitute result states no conclusion for this grain and the
      value is ``DATA_INCOMPLETE`` -- a missing ``SubstituteTarget`` is never guessed as ``0``
      (S3-A).
    """

    if required_date in table:
        return table[required_date]
    if not role_present:
        return (
            None,
            "the accepted package carries no Substitute Relationship role evidence, so "
            "'business states there is no approved substitute' cannot be established and "
            "CumulativeApprovedSubstituteSupply is never read as 0 (§2.1.7 / S3-A)",
            None,
        )
    if source_cited:
        return (
            _ZERO,
            None,
            "no approved substitute supply reaches this grain: BR-SUBSTITUTE-001 cites this "
            "material only as an exact Source Demand Context and cites no Target Demand Context "
            "for it, so the value is the explicit 0 of §4.4.88 rather than an omitted target",
        )
    return (
        None,
        "BR-SUBSTITUTE-001 states neither a Target Demand Context nor a Source Demand Context "
        "for this exact grain, so the cumulative approved substitute supply is not obtainable; a "
        "missing SubstituteTarget is never guessed as 0 and the grain stays DATA_INCOMPLETE "
        "(§2.3.12 / S3-A)",
        None,
    )


def _family_inherited(family: _Family) -> tuple[Issue, ...]:
    """Every registered finding the consumed upstream surfaces already carry for this family."""

    issues: list[Issue] = []
    for row in family.requirements:
        issues.extend(row.inherited_issues)
    for target in family.inbounds:
        issues.extend(target.inherited_issues)
        issues.extend(target.rule_issues)
    for target in family.substitutes:
        issues.extend(target.inherited_issues)
        issues.extend(target.rule_issues)
    return _deduplicate_issues(tuple(issues))


def _issue(
    *,
    location: str,
    detail: str,
    design_reference: str,
    consequence_context: str | None = None,
) -> Issue:
    return Issue(
        location=location,
        detail=detail,
        category=CATEGORY_SEMANTIC_RESOLUTION,
        reason=REASON_SEMANTIC_UNRESOLVED,
        layer=LAYER_2,
        affected_evidence=SHORTAGE_RULE_ID,
        blast_radius="affected shortage calculation only",
        design_reference=design_reference,
        consequence_context=consequence_context,
    )


def _deduplicate_issues(issues: Iterable[Issue]) -> tuple[Issue, ...]:
    """Keep one logical finding per ``location + category + reason``, deterministically."""

    unique: dict[tuple[str, str, str], Issue] = {}
    for issue in issues:
        unique.setdefault((issue.location, issue.category, issue.reason), issue)
    return tuple(sorted(unique.values(), key=Issue.sort_key))


__all__ = [
    "CLASSIFICATIONS",
    "CLASSIFICATION_BUFFER_BREACH",
    "CLASSIFICATION_DATA_INCOMPLETE",
    "CLASSIFICATION_NORMAL",
    "CLASSIFICATION_SHORTAGE",
    "SHORTAGE_DATA_INCOMPLETE",
    "SHORTAGE_GRAIN_PROPERTIES",
    "SHORTAGE_RULE_ID",
    "SUPPLY_FROM_INVENTORY_SNAPSHOT",
    "SUPPLY_FROM_SOURCE_RESERVATION",
    "ShortageCalculationResult",
    "ShortageGrain",
    "compute_shortage",
]
