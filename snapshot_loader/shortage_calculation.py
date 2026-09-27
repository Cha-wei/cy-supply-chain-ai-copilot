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
  ``OpeningUsableInventory`` and ``SafetyStock``; **zero** targets, or more than one distinct
  ``inventory_snapshot_time``, is ``DATA_INCOMPLETE``.  There is no earliest ／ latest win, no
  cross-snapshot sum, no average, no ``inventory_snapshot_time = AnalysisDate`` equivalence and no
  legal zero inferred from an absent target.
* **S3-A -- substitute result completeness.**  The substitute supply is consumed **only** from the
  explicitly completed ``BR-SUBSTITUTE-001`` downstream result: a cited Target Demand Context
  contributes its own cumulative value, a grain cited only as an exact Source Demand Context
  contributes the explicit valid zero of ``§4.4.88``, and a grain the result does not state fails
  closed.  A missing ``SubstituteTarget`` is never guessed as ``0``, and neither the construction's
  role-presence facts nor any raw ／ canonical substitute evidence is read to re-decide a citation.

``DATA_INCOMPLETE`` has priority over every business classification (``§2.1.4`` D): the complete
critical-input set, ``SafetyStock`` included, is decided before any comparison, so a negative
projection with an unresolved threshold is ``DATA_INCOMPLETE`` and not ``SHORTAGE``.

Deliberately **not** implemented here: any new business enum, any canonical field ／ entity ／
identity component, any reservation ／ demand-window field, any snapshot selection algorithm,
any persistence, any external configuration, any Adapter ／ ERP mapping, any LLM ／ Agent
behaviour and any rounding ／ quantization ／ float arithmetic.  ``ADR-001`` is unchanged.

Numeric semantics follow the registered precedent (``BR-REQUIREMENT-001`` ／
``BR-INBOUND-001`` ／ ``BR-INVENTORY-001`` ／ ``BR-SUBSTITUTE-001``): quantities stay exact.  The
consumed canonical finite decimals are read as exact rationals, and a derived quantity
(``ProjectedAvailable`` ／ ``ShortageQty`` ／ ``BufferGap`` and the consumed cumulative values) is
carried as an exact :class:`fractions.Fraction`.  An upstream exact rational that has **no** finite
base-10 representation (for example ``4000/19``) is a reliable quantity, never truncated, rounded or
quantized and never downgraded to ``DATA_INCOMPLETE``; it is serialised through the repository's
existing derived-quantity representation ``{"numerator": …, "denominator": …}``.  No ``float``, no
rounding, no quantization and no ``Decimal`` default context is used anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Iterable, Sequence

from .canonical_objects import (
    ABSENT,
    AnalysisRunContext,
    CanonicalConstructionReport,
)
from .constants import (
    CATEGORY_SEMANTIC_RESOLUTION,
    LAYER_2,
    REASON_SEMANTIC_UNRESOLVED,
)
from .exact_quantity import ExactQuantity
from .inbound_calculation import (
    INBOUND_RULE_ID,
    EffectiveInboundResult,
    EffectiveInboundTarget,
)
from .inventory_calculation import (
    INVENTORY_RULE_ID,
    InventoryCalculationResult,
    InventoryTarget,
)
from .issues import Issue
from .requirement_calculation import (
    OUTCOME_DATA_INCOMPLETE,
    RequirementCalculation,
    RequirementCalculationResult,
)
from .requirement_calculation import RULE_ID as REQUIREMENT_RULE_ID
from .result_binding import require_same_analysis_run
from .substitute_calculation import (
    SUBSTITUTE_RULE_ID,
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


# --- exact quantity helpers --------------------------------------------------------


def _exact_rational(value: Any) -> Fraction | None:
    """Read one canonical quantity as an **exact** rational, or ``None`` when it is unusable.

    A canonical finite decimal (:class:`~snapshot_loader.exact_quantity.ExactQuantity` or the
    base-10 string form it was parsed from) becomes its exact rational value with no intermediate
    binary float and no ``Decimal`` default context.  ``None`` means the value is absent, is not a
    registered canonical decimal, or is an exact rational whose own denormalised form cannot be
    read -- it is **never** truncated, rounded or quantized.

    This is the opposite of a lossy conversion: an exact rational such as ``4000/19`` is a
    perfectly reliable quantity under ``§2.4.8`` ／ ``ADR-001`` and is carried as-is, so a
    non-terminating decimal expansion never degrades a grain to ``DATA_INCOMPLETE``.
    """

    if value is None:
        return None
    if isinstance(value, Fraction):
        return value
    if isinstance(value, ExactQuantity):
        return Fraction(value.units, 10**value.scale)
    if isinstance(value, str) and value:
        signed = value[0] in "+-"
        body = value[1:] if signed else value
        whole, dot, fraction = body.partition(".")
        if not body or (dot and not fraction):
            return None
        digits = f"{whole or '0'}{fraction}"
        if not digits.isdigit():
            return None
        sign = -1 if value[0] == "-" else 1
        return Fraction(sign * int(digits), 10 ** len(fraction))
    return None


def _quantity_text(value: ExactQuantity | None) -> str | None:
    """Render an exact decimal quantity losslessly: plain base-10 digits, no exponent.

    Used only for the fields that **are** a canonical decimal input consumed as such
    (``EffectiveOpeningSupply`` ／ ``SafetyStock``); a derived quantity is serialised as an exact
    rational payload instead, because it need not have a finite base-10 representation.
    """

    return None if value is None else value.text()


def _rational_payload(value: Fraction | None) -> dict[str, int] | None:
    """Lossless serialisation of an exact rational derived quantity.

    ``{"numerator": <integer>, "denominator": <positive integer>}`` -- the same in-memory
    representation of a derived quantity that ``BR-REQUIREMENT-001`` uses for
    ``BaseRequirement`` ／ ``GrossRequirement`` and ``BR-SUBSTITUTE-001`` for
    ``EquivalentTargetQty``.  It carries the exact value including a non-terminating decimal
    expansion, so a reliable quantity is never rounded, quantized or downgraded.
    """

    if value is None:
        return None
    return {"numerator": value.numerator, "denominator": value.denominator}


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
    unresolved critical classification input -- most visibly an unresolved ``SafetyStock``: the
    projection itself is exact, only the threshold (or another classification input) cannot be
    decided, and ``DATA_INCOMPLETE`` still takes priority over every business classification
    (``§2.1.4`` D).

    Derived quantities (``projected_available`` ／ ``shortage_qty`` ／ ``buffer_gap`` and the three
    consumed cumulative values) are **exact rationals** :class:`fractions.Fraction`, because the
    registered upstream values are exact rationals and one of them need not have a finite base-10
    representation (``§2.4.8`` ／ ``ADR-001``).  ``opening_supply`` ／ ``safety_stock`` keep the
    exact decimal :class:`~snapshot_loader.exact_quantity.ExactQuantity` they were consumed as.

    ``first_shortage_date`` ／ ``first_buffer_breach_date`` carry the ascending-order marker of
    this grain's family.  The marker is **fail-safe**: a later reliable ``SHORTAGE`` never
    becomes the reliable first shortage date while an earlier grain is ``DATA_INCOMPLETE``, and an
    already reliable earlier date is never replaced by a later one (``§2.1.6``).  A grain whose own
    classification is ``DATA_INCOMPLETE`` claims **no** date of its own.
    """

    plant_id: Any
    material_code: Any
    required_date: Any
    classification: str
    projected_available: Fraction | None = None
    shortage_qty: Fraction | None = None
    buffer_gap: Fraction | None = None
    safety_stock: ExactQuantity | None = None
    opening_supply: ExactQuantity | None = None
    cumulative_effective_inbound: Fraction | None = None
    cumulative_approved_substitute_supply: Fraction | None = None
    cumulative_gross_requirement: Fraction | None = None
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
            "ProjectedAvailable": _rational_payload(self.projected_available),
            "Classification": self.classification,
            "ShortageQty": _rational_payload(self.shortage_qty),
            "BufferGap": _rational_payload(self.buffer_gap),
            "SafetyStock": _quantity_text(self.safety_stock),
            "EffectiveOpeningSupply": _quantity_text(self.opening_supply),
            "CumulativeEffectiveInbound": _rational_payload(
                self.cumulative_effective_inbound
            ),
            "CumulativeApprovedSubstituteSupply": _rational_payload(
                self.cumulative_approved_substitute_supply
            ),
            "CumulativeGrossRequirement": _rational_payload(
                self.cumulative_gross_requirement
            ),
            # A derived quantity has exactly one serialised form: the exact rational payload above,
            # the same form ``BR-REQUIREMENT-001`` and ``BR-SUBSTITUTE-001`` use.  There is no
            # decimal companion surface, so a value with a non-terminating base-10 expansion
            # (``4000/19``) is a perfectly readable, reliable exact quantity (``§2.4.8`` ／
            # ``ADR-001``) and never becomes ``DATA_INCOMPLETE`` for being unrenderable as digits.
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

    ``analysis_run`` is the **existing** :class:`AnalysisRunContext` of the construction this
    result was produced from.  It is the derived-result provenance binding of ``F3-RB1``
    (``Option A′``): the rule verifies all four upstream bindings before it computes anything, and
    its own result carries the same context so the next consumer can verify it in turn.
    """

    analysis_run: AnalysisRunContext
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
        """The earliest reliable ``ProjectedAvailable < 0`` date, ``None`` or the fail-safe.

        This is the **result-wide** marker: it scans every grain of the whole result, so a failure or
        a shortage in one ``plant_id`` + ``material_code`` family is visible in it.  It is therefore
        **not** the per-family handoff a downstream per-material rule consumes -- use
        :meth:`first_shortage_date_for` for that.
        """

        return _first_marker(self.grains, lambda item: item.shortage)

    def first_shortage_date_for(self, plant_id: Any, material_code: Any) -> Any:
        """The reliable ``FirstShortageDate`` of one exact ``plant_id`` + ``material_code`` family.

        This is the registered **per-family consumption seam** of ``BR-SHORTAGE-001``: a downstream
        per-material rule (``BR-PROCUREMENT-001``) consumes the date for the exact family it is
        recommending for, so it never has to re-derive ``§2.1.6`` itself and is never affected by
        another family's result.

        The answer is exactly the existing three-state semantic -- no new status, no new enum:

        * a ``DATE`` -- the earliest reliable ``ProjectedAvailable < 0`` date of this family, never
          replaced by a later one;
        * ``SHORTAGE_DATA_INCOMPLETE`` -- this family's first shortage date is not reliably
          knowable: an unresolved grain of this family precedes the earliest reliable shortage (so a
          later ``SHORTAGE`` must never be claimed as the reliable first date), or the family has no
          reliable shortage at all while its horizon is unresolved (a valid-absence ``None`` is never
          produced over an unresolved horizon, ``§2.1.6`` ／ ``§4.4.87``);
        * ``None`` -- valid absence: the whole horizon of this family is reliable and it never went
          short (``§4.4.22``).

        Only this family's grains are scanned, so one family never answers for another.  A family
        this result does not name at all has no grain and therefore no horizon of its own; the
        accessor returns ``None`` exactly as the result-wide property does for an empty result, and
        the caller is expected to take the exact family from this result's own grains.
        """

        return _first_marker(
            self.for_plant_material(plant_id, material_code),
            lambda item: item.shortage,
        )

    @property
    def first_buffer_breach_date(self) -> Any:
        """The earliest reliable ``ProjectedAvailable < SafetyStock`` date, or the fail-safe."""

        return _first_marker(
            self.grains,
            lambda item: (
                not item.data_incomplete
                and item.projected_available is not None
                and item.safety_stock is not None
                and item.projected_available < _exact_rational(item.safety_stock)
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


def _fail_safe_marker(candidate: Any, incomplete_before: Any) -> Any:
    """The reliably known marker of one scanned horizon (``§2.1.6`` fail-safe).

    ``candidate`` is the earliest reliably established marker date of the scanned grains (or
    ``None``) and ``incomplete_before`` is the earliest ``required_date`` of an unresolved grain in
    the same scan (or ``None``).  The three-state answer is:

    * ``candidate`` -- a reliable date, never replaced by a later one;
    * ``SHORTAGE_DATA_INCOMPLETE`` -- an unresolved grain earlier than the candidate would have made
      the true first date unknowable, or there is no candidate at all over an unresolved horizon;
    * ``None`` -- valid absence: a fully reliable horizon without the marker.

    The result-wide scan and the per-family scan both go through this one function, so the fail-safe
    semantic is defined exactly once and no surface can disagree with it.
    """

    if candidate is None:
        return SHORTAGE_DATA_INCOMPLETE if incomplete_before is not None else None
    if incomplete_before is not None and _sort_text(incomplete_before) < _sort_text(
        candidate
    ):
        return SHORTAGE_DATA_INCOMPLETE
    return candidate


def _first_marker(grains: Sequence[ShortageGrain], marker) -> Any:
    """The reliable earliest marker **date** of the scanned grains, or the ``DATA_INCOMPLETE`` fail-safe.

    ``§2.1.6`` defines both dates over ``required_date`` ascending, and a failure is isolated to
    the affected grain rather than to one Plant ／ Material family, so the scan is a deterministic
    pass over the calendar -- never over the ``plant_id`` -> ``material_code`` order:

    * the earliest reliably established marker date is the answer and is never replaced by a later
      one, so a subsequent ``DATA_INCOMPLETE`` does not move it;
    * an unresolved grain **earlier than** that date would have made the true first date
      unknowable, so it blocks the claim and the answer fails safe to
      ``SHORTAGE_DATA_INCOMPLETE``;
    * an unresolved grain at or after the established date cannot move it and is ignored;
    * with no reliable marker at all, ``None`` (valid absence) is produced **only** when no grain
      of the horizon is unresolved; otherwise the answer fails safe.

    ``grains`` is the scanned horizon: the whole result for the result-wide markers, or exactly one
    ``plant_id`` + ``material_code`` family for :meth:`ShortageCalculationResult.first_shortage_date_for`.
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
    return _fail_safe_marker(candidate, incomplete_before)


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

    Every input is an already computed deterministic result: no raw accepted artifact is read, no
    upstream rule is re-implemented, no reservation is recomputed and no caller may inject a
    business date, quantity or ``SafetyStock``.

    ``construction`` is read **only** for the registered provenance ／ result-binding verification
    (``construction.analysis_run``, ``F3-RB1`` ／ ``Option A′``): every business fact this rule needs
    -- including whether an ``approved substitute supply`` participates in a grain -- is consumed
    from the four upstream results.  In particular the accepted package's role-presence facts and
    any raw ／ canonical substitute evidence are never consulted, so the shortage rule can never
    re-decide the business meaning of a substitute citation (S3-A); the registered findings it
    reports are the ones the consumed upstream results carry.

    All four upstream results are verified against this construction's Analysis Run **before** any
    business calculation.  A foreign, stale or mismatched result rejects the invocation with the
    inherited ``PROVENANCE`` ／ ``PROVENANCE_MISMATCH`` finding instead of being silently combined;
    a result carrying no binding at all is ``PROVENANCE`` ／ ``PROVENANCE_UNRESOLVED``.
    """

    require_same_analysis_run(
        construction.analysis_run,
        (REQUIREMENT_RULE_ID, requirements.analysis_run),
        (INBOUND_RULE_ID, inbounds.analysis_run),
        (INVENTORY_RULE_ID, inventory.analysis_run),
        (SUBSTITUTE_RULE_ID, substitutes.analysis_run),
    )

    families = _families(requirements, inbounds, substitutes)
    groups = {group.reservation_context: group for group in substitutes.conservation_groups}
    citation_attributable = not substitutes.unattributable_conservation_groups
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
        )
        grains.extend(family_grains)
        for item in family_grains:
            rule_issues.extend(item.rule_issues)

    grains.sort(key=lambda item: _grain_key(item.grain))
    return ShortageCalculationResult(
        analysis_run=construction.analysis_run,
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
        # The approved ``S2-A`` boundary: for an exact ``plant_id`` + ``material_code`` exactly one
        # reliably consumable ``InventoryTarget`` supplies ``OpeningUsableInventory`` **and**
        # ``SafetyStock``; **zero** targets is ``DATA_INCOMPLETE``, exactly like more than one.
        # A legal 0 is never inferred here: BR-INVENTORY-001 forms a target for every exact grain
        # it can state, so no target at all means the inventory snapshot evidence behind this exact
        # grain cannot be relied on, and the affected grains fail closed.
        return _OpeningSupply(
            quantity=None,
            source=SUPPLY_UNRESOLVED_INVENTORY_SNAPSHOT,
            problem=(
                "BR-INVENTORY-001 produced no InventoryTarget for this exact plant_id + "
                "material_code, so EffectiveOpeningSupply and the SafetyStock classification "
                "threshold cannot be established; zero targets is DATA_INCOMPLETE and the "
                "inventory side is never read as a legal 0 (§2.1.2 / §2.1.4 D / §2.1.12 B / S2-A)"
            ),
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
    inherited = _family_inherited(family)
    #: The ``required_date`` values of the exact Source Demand Contexts this result cites for the
    #: family.  A grain cited as a reservation boundary has an explicit ``0`` substitute supply:
    #: the substitute result stated it as a boundary and stated no approved substitute supply
    #: reaching it from any target.  The set is built through :func:`_date_key` so a date that
    #: cannot index a table is never coerced into a key that could collide with another date.
    source_cited_dates = {
        key
        for key in (_date_key(context.required_date) for context in family.sources)
        if key is not ABSENT
    }

    #: The family's running fail-safe marker state: the earliest reliable shortage ／ breach date
    #: established so far, and the earliest ``required_date`` of an unresolved grain seen so far.
    #: Each decided grain is given the marker that is reliably known **at its own date**
    #: (:func:`_fail_safe_marker`), so a later grain can never claim a reliable first date while an
    #: earlier grain of the same family is ``DATA_INCOMPLETE`` (§2.1.6 / §2.1.12 G).
    first_shortage: Any = None
    first_breach: Any = None
    incomplete_before: Any = None

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
            source_cited=required_date in source_cited_dates,
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
        #
        # The reference and the conservation state are reported only on the grain the cited context
        # actually names: ``SourceDemandContext.required_date`` is part of the grain, so a context
        # of a sibling date is never presented as if it cited this one.
        source_context_reference = None
        conservation_state = None
        if source_entry is not None:
            entry_context, entry_group = source_entry
            if entry_context.required_date == required_date:
                source_context_reference = entry_context.reference
                conservation_state = (
                    None if entry_group is None else entry_group.conservation_state
                )

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

        effective_opening = _exact_rational(opening.quantity)
        safety_stock = opening.safety_stock
        if safety_stock is None:
            issues.append(
                _issue(
                    location=location,
                    detail=(
                        "the consumable inventory target of this exact plant_id + material_code "
                        "states no reliable SafetyStock, so the classification threshold cannot be "
                        "established; DATA_INCOMPLETE takes priority over NORMAL / BUFFER_BREACH / "
                        "SHORTAGE and SafetyStock is never defaulted to 0 (§2.1.4 D / §2.2.7 / "
                        "S2-A)"
                    ),
                    design_reference="§2.1.4 D / §2.2.7 / S2-A",
                    consequence_context=(
                        "the grain stays DATA_INCOMPLETE and no classification is produced"
                    ),
                )
            )

        # The projection is produced whenever its own four inputs are reliable; it is reported even
        # on a grain whose *classification* stays DATA_INCOMPLETE, because §2.1.5 derives nothing
        # from an undecided classification and the exact projection is still a reliable fact.
        projected: Fraction | None = None
        if (
            gross is not None
            and inbound is not None
            and substitute_supply is not None
            and effective_opening is not None
        ):
            projected = effective_opening + inbound + substitute_supply - gross

        safety_stock_exact = _exact_rational(safety_stock)
        # ``§2.1.4`` D: ``DATA_INCOMPLETE`` has priority over every business classification, so the
        # complete critical-input set is decided **before** any comparison.  An unresolved
        # ``SafetyStock`` is one of those inputs, which is why it is tested here rather than in an
        # ``elif`` after the ``ProjectedAvailable < 0`` branch (``§2.1.8`` decision-table order).
        undecided = (
            projected is None or safety_stock is None or safety_stock_exact is None
        )

        if undecided:
            # A grain that could not be decided claims neither a business classification nor a
            # reliable first-shortage ／ first-breach date of its own: its marker fields stay
            # ``None`` so the per-grain surface can never contradict the fail-safe marker
            # (§2.1.6 / §2.1.12 E).  It is however remembered as the family's earliest unresolved
            # date, because a later reliable ``SHORTAGE`` must not become the family's reliable
            # first shortage date while this grain is unresolved (§2.1.6 / §2.1.12 G).
            if incomplete_before is None:
                incomplete_before = required_date
            results.append(
                ShortageGrain(
                    plant_id=family.plant_id,
                    material_code=family.material_code,
                    required_date=required_date,
                    classification=CLASSIFICATION_DATA_INCOMPLETE,
                    outcome=SHORTAGE_DATA_INCOMPLETE,
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
                    opening_provenance=opening.provenance,
                    notes=tuple(notes)
                    + (
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

        assert projected is not None and safety_stock_exact is not None

        # Every critical classification input is reliable here, so the registered decision table
        # applies in its ``§2.1.8`` order.
        if projected < 0:
            classification = CLASSIFICATION_SHORTAGE
        elif projected < safety_stock_exact:
            classification = CLASSIFICATION_BUFFER_BREACH
        else:
            classification = CLASSIFICATION_NORMAL

        shortage_qty = -projected if projected < 0 else Fraction(0)
        buffer_gap = (
            safety_stock_exact - projected
            if projected < safety_stock_exact
            else Fraction(0)
        )
        if classification == CLASSIFICATION_SHORTAGE and first_shortage is None:
            first_shortage = required_date
        if projected < safety_stock_exact and first_breach is None:
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
                # The same fail-safe the family accessor answers with, evaluated at this grain's own
                # date: a later grain never claims a reliable date across an earlier unresolved one.
                first_shortage_date=_fail_safe_marker(first_shortage, incomplete_before),
                first_buffer_breach_date=_fail_safe_marker(first_breach, incomplete_before),
                outcome=None,
                notes=tuple(notes),
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

    table: dict[Any, tuple[Fraction | None, str | None]] = {}
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
        # The upstream value is an exact rational.  It is carried as-is: a non-terminating base-10
        # expansion (for example ``4000/19``) is a **reliable** exact quantity, never truncated,
        # rounded or quantized and never turned into an unresolved value
        # (§2.4.8 / ADR-001).
        table[required_date] = (Fraction(numeric[0]), None)
    return table


def _inbound_table(
    targets: Sequence[EffectiveInboundTarget],
) -> dict[Any, tuple[Fraction | None, str | None]]:
    """``CumulativeEffectiveInbound(<= required_date)`` per date, carried forward once.

    The upstream target's own cumulative value is non-decreasing in ``required_date``, so the
    value at ``t`` is the upstream value of the latest target at or before ``t``.  That upstream
    value is never passed through a second cumulative sum.  No target at or before ``t`` states
    that no inbound evidence reaches ``t``, which is the legal ``0`` of ``§4.4.88``.
    """

    ordered = sorted(targets, key=lambda item: _sort_text(item.required_date))
    table: dict[Any, tuple[Fraction | None, str | None]] = {}
    carried: Fraction | None = Fraction(0)
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
            carried = _exact_rational(target.cumulative_effective_inbound)
            carried_problem = None
        key = _date_key(target.required_date)
        if key is not ABSENT:
            table[key] = (carried, carried_problem)
    return table


def _substitute_table(
    targets: Sequence[SubstituteTarget],
) -> dict[Any, tuple[Fraction | None, str | None, str | None]]:
    """``CumulativeApprovedSubstituteSupply(<= required_date)`` per **stated** target grain.

    The value is ``BR-SUBSTITUTE-001``'s own cumulative result for that target grain and is read
    as-is -- never recomputed from raw or canonical substitute evidence.  A target whose own
    cumulative value is unresolved makes its date ``DATA_INCOMPLETE``, and a date the result does
    not state is **never** silently read as ``0`` (S3-A).

    Only dates the result actually states enter the table.  There is deliberately no
    "fill the gaps" pass: the rule cannot tell an unstated date from a stated zero, so an unstated
    date is left out and the caller fails that grain closed rather than inventing a value.  A later
    stated target's own cumulative value already includes every earlier contribution
    (``§2.3.12``), so no earlier supply is lost by not writing intermediate dates.
    """

    ordered = sorted(targets, key=lambda item: _sort_text(item.required_date))
    table: dict[Any, tuple[Fraction | None, str | None, str | None]] = {}
    for target in ordered:
        if target.cumulative_approved_substitute_supply is None:
            carried: Fraction | None = None
            carried_problem: str | None = (
                "the BR-SUBSTITUTE-001 target of this exact grain states no reliable "
                "CumulativeApprovedSubstituteSupply, so the cumulative approved substitute "
                "supply at this required date is not obtainable and is never defaulted to 0 "
                "(§2.3.12 / S3-A)"
            )
        else:
            # The upstream value is an exact rational and is carried as-is; a non-terminating
            # base-10 expansion is a reliable exact quantity, not an unresolved one
            # (§2.4.8 / ADR-001).
            carried = Fraction(target.cumulative_approved_substitute_supply)
            carried_problem = None
        carried_note: str | None = None
        if carried is not None and not target.evaluations:
            # ``S3-A`` completion: the result states this grain even though no G5-A Target
            # Applicability context cites it and no reliable contribution accumulates to it.  Its
            # confirmed answer is therefore the legal zero of §2.3.11 A / §4.4.88, and the note
            # makes the zero visibly a *stated* conclusion rather than an omitted target.
            carried_note = (
                "no approved substitute supply reaches this grain: BR-SUBSTITUTE-001 states this "
                "material's demand context only as a resolved shortage demand grain and states no "
                "Target Demand Context for it, so the value is the explicit 0 of §4.4.88 rather "
                "than an omitted target"
            )
        key = _date_key(target.required_date)
        if key is not ABSENT:
            table[key] = (carried, carried_problem, carried_note)
    return table


def _substitute_supply_for(
    table: dict[Any, tuple[Fraction | None, str | None, str | None]],
    required_date: Any,
    *,
    source_cited: bool,
) -> tuple[Fraction | None, str | None, str | None]:
    """Resolve one grain's ``CumulativeApprovedSubstituteSupply`` under ``S3-A``.

    Only the **explicitly completed** ``BR-SUBSTITUTE-001`` downstream result is consumed here.
    That result states an explicit answer for every resolved shortage demand grain -- its own
    cumulative value (``<= t``, so an earlier reliable contribution carries forward) or the
    upstream ``DATA_INCOMPLETE`` -- so a stated grain is answered directly.

    Two further cases come from the same result's own citation surface:

    * the grain is cited as an exact Source Demand Context of this result -- the substitute rule
      stated it as a reservation boundary and stated no approved substitute supply reaching it from
      any target, so the answer is the explicit ``0`` of ``§4.4.88``;
    * nothing states the grain at all -- ``BR-SHORTAGE-001`` never infers a ``0`` from a missing
      ``SubstituteTarget`` and never re-decides the business meaning of a citation, so it fails
      closed as ``DATA_INCOMPLETE``.
    """

    if required_date in table:
        return table[required_date]
    if source_cited:
        return (
            Fraction(0),
            None,
            "no approved substitute supply reaches this grain: BR-SUBSTITUTE-001 states this "
            "material's demand context only as an exact Source Demand Context and states no "
            "Target Demand Context for it, so the value is the explicit 0 of §4.4.88 rather than "
            "an omitted target",
        )
    return (
        None,
        "BR-SUBSTITUTE-001 states no CumulativeApprovedSubstituteSupply for this exact grain, so "
        "the completed downstream result does not express a numeric cumulative substitute supply "
        "or DATA_INCOMPLETE for it; a missing target is never guessed as 0 and the grain stays "
        "DATA_INCOMPLETE (§2.1.7 / §2.3.12 / S3-A)",
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
