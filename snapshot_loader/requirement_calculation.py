"""``BR-REQUIREMENT-001`` -- Requirement Calculation (Scrap / Loss, ``§2.4``).

This module implements the first deterministic business rule:

```
BaseRequirement  = ProductionQty x BOMComponentQty
GrossRequirement = BaseRequirement / (1 - loss_rate)

ProductionQty   >= 0
BOMComponentQty >= 0
0 <= loss_rate  < 1
```

and the cumulative form registered for the same grain:

```
CumulativeGrossRequirement(<= t) = sum of GrossRequirement where required_date <= t
```

Canonical authority implemented:

* ``poc-design-v0.2.md`` §2.4 (``BR-REQUIREMENT-001``, ``DESIGN RESOLVED`` /
  Human-approved): business definition, calculation grain, ``BaseRequirement``,
  ``loss_rate`` canonical semantic, ``GrossRequirement`` formula, ``loss_rate``
  validation, zero-vs-missing, quantity precision boundary, cumulative requirement,
  substitute boundary, fail-safe and AI boundary.
* ``data-dictionary.md`` §4.2.10: ``BaseRequirement`` / ``GrossRequirement`` /
  ``CumulativeGrossRequirement`` are ``DERIVED`` results whose missing behaviour is
  ``DATA_INCOMPLETE``.
* ``data-validation.md`` §4.4.15: the three ``loss_rate`` root conditions (A / B / C) all
  lead to ``DATA_INCOMPLETE``; §4.4.20: ``DATA_INCOMPLETE`` applies at the affected
  business grain; §4.4.85: ``DATA_INCOMPLETE`` is a **Business Outcome**, never an issue
  category or reason.
* ``adr-001-deterministic-core.md``: in-memory, standard-library-first, canonical exact
  numeric semantics (``Decimal``), core independent of the CLI.

Input boundary: the rule consumes **already resolved canonical construction output**
(:class:`~snapshot_loader.canonical_objects.CanonicalConstructionReport`) only.  It never
re-reads a raw snapshot artifact, never re-runs source mapping, never guesses the BOM or
the ``loss_rate``, never builds BOM version / validity / explosion logic and never lets a
caller inject a business value that has no provenance.

Deliberately **not** implemented here (outside this rule): ``BR-SUBSTITUTE-001`` and every
other ``§2`` rule, procurement recommendation, Phase B, persisting any result, and any
quantity precision / rounding / pack-size policy -- this rule keeps the canonical
quantity exactly as computed (``§2.4.8``).
"""

from __future__ import annotations

import datetime as _datetime
import re
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from typing import Any, Iterable, Mapping

from .canonical_objects import (
    ABSENT,
    ROLE_BOM_COMPONENT,
    ROLE_PRODUCTION_REQUIREMENT,
    CanonicalConstructionReport,
    CanonicalObject,
    CanonicalProperty,
    ContextValueReference,
    EvidenceReference,
)
from .constants import DECIMAL_STRING_PATTERN
from .issues import Issue

# --- registered outcome vocabulary -------------------------------------------------

#: The only business outcome this rule expresses, and only on failure.  Current canonical
#: authority registers ``DATA_INCOMPLETE`` (``§2.4.11`` / ``data-dictionary`` §4.2.10 /
#: ``data-validation`` §4.4.85) and **no** success status such as ``NUMERIC`` / ``OK`` /
#: ``SUCCESS``.  A successful calculation is expressed by its exact numeric derived results
#: themselves, with :attr:`RequirementCalculation.outcome` left ``None``.
OUTCOME_DATA_INCOMPLETE: str = "DATA_INCOMPLETE"

#: The rule identity this module implements.
RULE_ID: str = "BR-REQUIREMENT-001"

#: ``0 <= loss_rate < 1`` (``§2.4.5`` / ``§2.4.6``).
LOSS_RATE_MINIMUM: Fraction = Fraction(0)
LOSS_RATE_MAXIMUM_EXCLUSIVE: Fraction = Fraction(1)

_DECIMAL_STRING_RE = re.compile(rf"^{DECIMAL_STRING_PATTERN}$")
_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")

CALCULATION_GRAIN_PROPERTIES: tuple[str, ...] = (
    "plant_id",
    "material_code",
    "required_date",
)


# --- result representation ---------------------------------------------------------


def _rational_payload(value: Fraction | None) -> dict[str, int] | None:
    """Lossless deterministic serialisation of an exact rational **derived quantity**.

    ``{"numerator": <integer>, "denominator": <positive integer>}`` -- the in-memory
    representation of a derived requirement quantity, never a truncated decimal expansion
    and never a rounded quantity.  Only the Human-approved derived quantities
    (``BaseRequirement`` / ``GrossRequirement`` / ``CumulativeGrossRequirement``) are
    expressed this way.
    """

    if value is None:
        return None
    return {"numerator": value.numerator, "denominator": value.denominator}


@dataclass(frozen=True, slots=True)
class RequirementCalculation:
    """One deterministic requirement calculation for one calculation grain.

    ``grain`` is the calculation grain registered by ``§2.4.2``: ``plant_id`` + component
    ``material_code`` + ``required_date``.  ``outcome`` is ``None`` for a successful
    calculation and ``DATA_INCOMPLETE`` when a registered prerequisite could not be
    reliably obtained; a ``DATA_INCOMPLETE`` calculation never carries a numeric
    ``BaseRequirement`` / ``GrossRequirement`` (``§2.4.11``).

    ``base_requirement`` / ``gross_requirement`` / ``cumulative_gross_requirement`` are the
    Human-approved **exact rational** derived quantities (:class:`fractions.Fraction`).

    ``loss_rate`` is the **resolved canonical input**, kept exactly as the accepted canonical
    value states it (the canonical base-10 decimal representation, character for character).
    It is *not* a derived quantity and is *not* redefined as a rational output field: the
    exact operand used by the arithmetic is an internal, temporary conversion
    (canonical decimal -> ``Fraction`` operand -> ``GrossRequirement``) that never replaces
    the retained canonical representation and never normalises it
    (``"0.050"`` stays ``"0.050"``).

    Traceability (``§2.4.2``): ``production_requirement_reference`` and
    ``bom_component_reference`` name the canonical objects this calculation was derived
    from, ``context_reference`` is the resolved Production Requirement context the BOM
    Component relationship was bound to, and ``loss_rate_provenance`` is the resolved
    Requirement Calculation Context's own provenance.
    """

    plant_id: Any
    component_material_code: Any
    required_date: Any
    grain: tuple[CanonicalProperty, ...]
    base_requirement: Fraction | None
    loss_rate: Any
    gross_requirement: Fraction | None
    cumulative_gross_requirement: Fraction | None
    outcome: str | None = None
    notes: tuple[str, ...] = ()
    production_requirement_reference: str | None = None
    bom_component_reference: str | None = None
    context_reference: str | None = None
    bom_component_provenance: EvidenceReference | None = None
    production_requirement_provenance: EvidenceReference | None = None
    loss_rate_context_grain: tuple[CanonicalProperty, ...] | None = None
    loss_rate_provenance: EvidenceReference | None = None
    inherited_issues: tuple[Issue, ...] = ()

    def exact_loss_rate(self) -> Fraction | None:
        """Return the exact rational **operand** for the retained canonical ``loss_rate``.

        This is a read-only exact view of the canonical input used for arithmetic; it does
        not replace the canonical representation and does not introduce any precision or
        rounding policy.  ``None`` means the canonical value is absent or is not a
        registered base-10 decimal.
        """

        return _as_rational(self.loss_rate)

    @property
    def data_incomplete(self) -> bool:
        return self.outcome == OUTCOME_DATA_INCOMPLETE

    @property
    def has_numeric_result(self) -> bool:
        """Whether this calculation produced an exact numeric derived requirement.

        Derived from the presence of the numeric result itself; **no** success status
        vocabulary is created or surfaced.
        """

        return self.gross_requirement is not None

    def to_dict(self) -> dict[str, object]:
        return {
            "rule": RULE_ID,
            "plant_id": self.plant_id,
            "component_material_code": self.component_material_code,
            "required_date": self.required_date,
            "grain": [
                {"name": prop.name, "value": prop.value} for prop in self.grain
            ],
            "BaseRequirement": _rational_payload(self.base_requirement),
            # The resolved canonical input keeps its registered decimal representation.
            "loss_rate": self.loss_rate,
            "GrossRequirement": _rational_payload(self.gross_requirement),
            "CumulativeGrossRequirement": _rational_payload(
                self.cumulative_gross_requirement
            ),
            "outcome": self.outcome,
            "notes": list(self.notes),
            "trace": {
                "production_requirement_reference": (
                    self.production_requirement_reference
                ),
                "bom_component_reference": self.bom_component_reference,
                "production_requirement_context_reference": self.context_reference,
                "loss_rate_context_grain": (
                    None
                    if self.loss_rate_context_grain is None
                    else [
                        {"name": prop.name, "value": prop.value}
                        for prop in self.loss_rate_context_grain
                    ]
                ),
            },
            "inherited_issues": [issue.to_dict() for issue in self.inherited_issues],
        }


@dataclass(frozen=True, slots=True)
class RequirementCalculationResult:
    """Deterministic result of ``BR-REQUIREMENT-001`` for one construction.

    ``calculations`` is ordered deterministically by calculation grain and covers every
    BOM Component relationship the construction exposes -- resolved relationships produce
    a numeric calculation when all prerequisites are reliable, and unresolved ones produce
    the registered ``DATA_INCOMPLETE`` fail-safe result (``§2.4.11`` / Example E) with no
    numeric derived requirement.  No cross-plant or cross-component aggregation is
    performed: the cumulative value is reported per calculation grain (``plant_id`` +
    component ``material_code``), which is exactly the grouping ``§2.4.9`` registers.
    """

    calculations: tuple[RequirementCalculation, ...]

    @property
    def numeric(self) -> tuple[RequirementCalculation, ...]:
        return tuple(item for item in self.calculations if item.has_numeric_result)

    @property
    def data_incomplete(self) -> tuple[RequirementCalculation, ...]:
        return tuple(item for item in self.calculations if item.data_incomplete)

    def for_grain(
        self, plant_id: Any, component_material_code: Any, required_date: Any
    ) -> RequirementCalculation | None:
        for item in self.calculations:
            if (
                item.plant_id == plant_id
                and item.component_material_code == component_material_code
                and item.required_date == required_date
            ):
                return item
        return None

    def for_plant_component(
        self, plant_id: Any, component_material_code: Any
    ) -> tuple[RequirementCalculation, ...]:
        return tuple(
            item
            for item in self.calculations
            if item.plant_id == plant_id
            and item.component_material_code == component_material_code
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "rule": RULE_ID,
            "calculations": [item.to_dict() for item in self.calculations],
        }


# --- arithmetic --------------------------------------------------------------------


def requirement_calculation_context_grain(
    context: ContextValueReference,
) -> tuple[CanonicalProperty, ...]:
    """Return the registered four-part grain of a resolved loss_rate context."""

    return context.grain


def _context_grain_key(context: ContextValueReference) -> tuple[Any, ...]:
    return tuple(prop.value for prop in context.grain)


def _groupable(values: tuple[Any, ...]) -> bool:
    """Whether a calculation grain can be used as a deterministic mapping / grouping key.

    A canonical grain component is legal wire / runtime content but not necessarily
    hashable: a JSON array or object in a ``ContextValueReference.grain`` or in an accepted
    component ``material_code`` makes ``dict.get`` / ``dict.setdefault`` raise ``TypeError``
    and would break the whole requirement calculation.

    The values are never retyped, stringified or serialized to obtain hashability; a grain
    that cannot be used as a key simply provides no reliable exact Requirement Calculation
    Context and leaves the affected calculation ``DATA_INCOMPLETE`` (``§2.4.7`` /
    ``§4.4.15``).  No new taxonomy is introduced.
    """

    try:
        hash(values)
    except TypeError:
        return False
    return True


def _context_by_grain(
    contexts: Iterable[ContextValueReference],
) -> dict[tuple[Any, ...], ContextValueReference]:
    """Index the resolved ``loss_rate`` Requirement Calculation Contexts by their grain.

    Exactly one context per registered four-part grain is the canonicalization contract
    (``§4.3.31`` G I-2 / ``§4.4.15``); if one grain somehow appears more than once it is
    kept out of the index rather than letting one silently win.

    A context whose grain cannot serve as a deterministic grouping key is not indexed at
    all: it can never be selected, and it neither replaces nor is replaced by another
    context.  The affected calculation then simply finds no exact context and stays
    ``DATA_INCOMPLETE`` -- ``loss_rate`` is never defaulted to 0.
    """

    index: dict[tuple[Any, ...], ContextValueReference] = {}
    duplicated: set[tuple[Any, ...]] = set()
    for context in contexts:
        key = _context_grain_key(context)
        if not _groupable(key):
            continue
        if key in index:
            duplicated.add(key)
            continue
        index[key] = context
    for key in duplicated:
        index.pop(key, None)
    return index


def _as_decimal(value: Any) -> Decimal | None:
    """Return the exact base-10 ``Decimal`` for a canonical decimal value.

    This is the **canonical input** parser: the accepted decimal string is read exactly as
    written.  Returns ``None`` for JSON ``null``, for a non-string value and for a string
    that is not a registered base-10 decimal (``§4.3.25`` C-5).  No binary floating point
    is used, and no value is repaired or defaulted.
    """

    if not isinstance(value, str):
        return None
    if not _DECIMAL_STRING_RE.match(value):
        return None
    try:
        return Decimal(value)
    except InvalidOperation:  # pragma: no cover - guarded by the pattern
        return None


def _as_rational(value: Any) -> Fraction | None:
    """Parse a canonical decimal value into its **exact** rational value.

    ``Decimal("0.05")`` becomes ``Fraction(1, 20)`` with no intermediate binary float and no
    dependence on any ``Decimal`` context precision.  ``None`` means the value is not a
    registered base-10 decimal string (or is absent), and it is never defaulted.
    """

    parsed = _as_decimal(value)
    if parsed is None:
        return None
    return Fraction(parsed)


def _as_date(value: Any) -> _datetime.date | None:
    """Validate the canonical ``DATE`` representation (``§4.3.22`` C-3)."""

    if not isinstance(value, str) or not _DATE_RE.match(value):
        return None
    try:
        return _datetime.date.fromisoformat(value)
    except ValueError:
        return None


def base_requirement(production_qty: Fraction, bom_component_qty: Fraction) -> Fraction:
    """``BaseRequirement = ProductionQty x BOMComponentQty`` (``§2.4.3``).

    Exact rational arithmetic: no ``Decimal`` context precision, no rounding and no
    conversion back to a finite decimal.
    """

    return Fraction(production_qty) * Fraction(bom_component_qty)


def gross_requirement(base: Fraction, loss_rate: Fraction) -> Fraction:
    """``GrossRequirement = BaseRequirement / (1 - loss_rate)`` (``§2.4.5``).

    The caller has already established ``0 <= loss_rate < 1``.  The result is an exact
    rational value, so a non-terminating base-10 quantity such as ``200 / 0.95`` is kept as
    ``Fraction(4000, 19)`` instead of being truncated at some finite ``Decimal`` precision.
    No rounding, ceiling, flooring, truncation or pack-size adjustment is applied
    (``§2.4.8``).
    """

    return Fraction(base) / (Fraction(1) - Fraction(loss_rate))


def _valid_loss_rate(value: Fraction) -> bool:
    return LOSS_RATE_MINIMUM <= value < LOSS_RATE_MAXIMUM_EXCLUSIVE


# --- rule execution ----------------------------------------------------------------


def compute_requirement_calculation(
    report: CanonicalConstructionReport,
) -> RequirementCalculationResult:
    """Run ``BR-REQUIREMENT-001`` over the canonical construction output.

    Every ``BOM Component`` relationship the construction exposes is accounted for exactly
    once: a **resolved** relationship produces an exact numeric calculation when all
    registered prerequisites are reliable, and an **unresolved** relationship produces the
    registered ``DATA_INCOMPLETE`` fail-safe result (``§2.4.11`` / Example E) with **no**
    numeric derived requirement.  The rule never fabricates a BOM, a quantity, a
    ``required_date`` or a ``loss_rate``: unresolved canonical state is only ever reported,
    never repaired.
    """

    contexts = _context_by_grain(report.loss_rate_contexts)
    requirements = {
        obj.record_reference: obj
        for obj in report.objects_for(ROLE_PRODUCTION_REQUIREMENT)
    }

    components = list(report.objects_for(ROLE_BOM_COMPONENT)) + list(
        report.unresolved_for(ROLE_BOM_COMPONENT)
    )

    calculations = [
        _calculate_component(
            component=component,
            requirements=requirements,
            contexts=contexts,
            report=report,
        )
        for component in components
    ]

    calculations.sort(
        key=lambda item: (
            _sort_text(item.plant_id),
            _sort_text(item.component_material_code),
            _sort_text(item.required_date),
            item.bom_component_reference or "",
        )
    )
    return RequirementCalculationResult(calculations=_with_cumulative(calculations))


def _sort_text(value: Any) -> str:
    return "" if value is None else str(value)


def _calculate_component(
    *,
    component: CanonicalObject,
    requirements: Mapping[str, CanonicalObject],
    contexts: Mapping[tuple[Any, ...], ContextValueReference],
    report: CanonicalConstructionReport,
) -> RequirementCalculation:
    """Derive one calculation for one BOM Component relationship.

    The **parent / requirement context of a resolved BOM Component relationship is the
    resolved Production Requirement context**, so ``plant_id``, the parent
    ``material_code``, ``required_date`` and ``ProductionQty`` are read from that context.
    The resolved BOM Component supplies the component ``material_code`` and
    ``BOMComponentQty``.  Values the BOM record happens to repeat locally are upstream
    consistency evidence, not the calculation context authority.
    """

    parent = requirements.get(component.context_reference or "")

    plant_id = parent.value_of("plant_id", ABSENT) if parent is not None else ABSENT
    parent_material = (
        parent.value_of("material_code", ABSENT) if parent is not None else ABSENT
    )
    required_date = (
        parent.value_of("required_date", ABSENT) if parent is not None else ABSENT
    )
    component_material = component.value_of("material_code", ABSENT)

    grain = (
        CanonicalProperty("plant_id", plant_id),
        CanonicalProperty("material_code", component_material),
        CanonicalProperty("required_date", required_date),
    )

    def incomplete(*notes: str) -> RequirementCalculation:
        return RequirementCalculation(
            plant_id=None if plant_id is ABSENT else plant_id,
            component_material_code=(
                None if component_material is ABSENT else component_material
            ),
            required_date=None if required_date is ABSENT else required_date,
            grain=grain,
            base_requirement=None,
            loss_rate=None,
            gross_requirement=None,
            cumulative_gross_requirement=None,
            outcome=OUTCOME_DATA_INCOMPLETE,
            notes=tuple(notes),
            production_requirement_reference=(
                parent.record_reference if parent is not None else None
            ),
            bom_component_reference=component.record_reference,
            context_reference=component.context_reference,
            bom_component_provenance=component.provenance,
            production_requirement_provenance=(
                parent.provenance if parent is not None else None
            ),
            inherited_issues=_relevant_issues(report, component=component),
        )

    # --- prerequisite: resolved Production Requirement (parent) context -------------
    if parent is None:
        return incomplete(
            "no resolved Production Requirement context is available for this BOM "
            "Component relationship, so the Requirement Calculation Context cannot be "
            "established; no numeric requirement is produced and no parent context is "
            "guessed (§2.4.3 / §2.4.11)"
        )

    # --- prerequisite: calculation grain identity (from the parent context) --------
    if plant_id is ABSENT:
        return incomplete(
            "plant identity is unresolved in the resolved Production Requirement context; "
            "no requirement calculation"
        )
    if parent_material is ABSENT:
        return incomplete(
            "the parent / requirement material identity is unresolved; no requirement "
            "calculation"
        )
    if required_date is ABSENT:
        return incomplete("required_date is missing; no requirement calculation")
    if _as_date(required_date) is None:
        return incomplete(
            f"required_date {required_date!r} is not a valid DATE; no requirement "
            "calculation"
        )

    # --- prerequisite: component material identity ---------------------------------
    if component_material is ABSENT:
        return incomplete(
            "component material identity is unresolved, so the calculation grain cannot "
            "be stated; no numeric requirement and no material code is invented "
            "(§2.4.11)"
        )

    production_qty = _as_rational(parent.value_of("ProductionQty", ABSENT))
    if production_qty is None:
        return incomplete(
            "ProductionQty is missing or is not a registered base-10 decimal; no "
            "requirement calculation and no default is applied (§2.4.11)"
        )
    if production_qty < Fraction(0):
        return incomplete(
            "ProductionQty is negative; no requirement calculation (§2.4.3 / §2.4.11)"
        )

    bom_component_qty = _as_rational(component.value_of("BOMComponentQty", ABSENT))
    if bom_component_qty is None:
        return incomplete(
            "BOMComponentQty is missing or is not a registered base-10 decimal; no "
            "requirement calculation and no BOM quantity is guessed (§2.4.11)"
        )
    if bom_component_qty < Fraction(0):
        return incomplete(
            "BOMComponentQty is negative; no requirement calculation (§2.4.3 / §2.4.11)"
        )

    # --- prerequisite: resolved loss_rate Requirement Calculation Context ----------
    context_key = (plant_id, parent_material, required_date, component_material)
    if not _groupable(context_key):
        # The exact Requirement Calculation Context cannot even be looked up: one grain
        # component carries an accepted representation that is not usable as a
        # deterministic key.  The original value is retained for trace / audit, nothing is
        # retyped, stringified or borrowed, and no loss_rate default is applied.
        return incomplete(
            "the calculation grain cannot be used as a deterministic lookup key because a "
            "grain component carries an accepted representation that is not hashable "
            f"(plant_id={plant_id!r}, parent material_code={parent_material!r}, "
            f"required_date={required_date!r}, component material_code="
            f"{component_material!r}); no Requirement Calculation Context is selected, the "
            "value is never retyped or stringified and no loss_rate default is applied "
            "(§2.4.7 / §4.4.15)"
        )
    context = contexts.get(context_key)
    if context is None:
        # ``§4.4.15`` root A / B: the exact context was never resolved for this grain, or
        # its required value is absent.  Both are ``DATA_INCOMPLETE``, and the value is
        # never defaulted to 0 (``§2.4.7``).
        return incomplete(
            "the exact Requirement Calculation Context "
            f"(plant_id={plant_id!r}, parent material_code={parent_material!r}, "
            f"required_date={required_date!r}, component material_code="
            f"{component_material!r}) has no resolved loss_rate; the value is not "
            "defaulted to 0 (§2.4.7 / §4.4.15)"
        )

    # The retained canonical input is the accepted canonical representation, unchanged.
    canonical_loss_rate = context.value
    # Exact rational **operand** used for the arithmetic only: the canonical decimal is
    # converted temporarily and never replaces the retained canonical value.
    loss_rate_operand = _as_rational(canonical_loss_rate)
    if loss_rate_operand is None:
        return incomplete(
            "the resolved loss_rate value is missing or is not a registered base-10 "
            "decimal; no requirement calculation and no default is applied (§2.4.7)"
        )
    if not _valid_loss_rate(loss_rate_operand):
        return incomplete(
            f"loss_rate {canonical_loss_rate!r} is outside the registered range "
            "0 <= loss_rate < 1; the value is not clamped, not replaced by 0 and not "
            "replaced by the maximum (§2.4.6 / §4.4.15 root C)"
        )

    base = base_requirement(production_qty, bom_component_qty)
    gross = gross_requirement(base, loss_rate_operand)

    return RequirementCalculation(
        plant_id=plant_id,
        component_material_code=component_material,
        required_date=required_date,
        grain=grain,
        base_requirement=base,
        loss_rate=canonical_loss_rate,
        gross_requirement=gross,
        cumulative_gross_requirement=None,  # filled by the cumulative pass
        outcome=None,  # success is expressed by the exact numeric results themselves
        production_requirement_reference=parent.record_reference,
        bom_component_reference=component.record_reference,
        context_reference=component.context_reference,
        bom_component_provenance=component.provenance,
        production_requirement_provenance=parent.provenance,
        loss_rate_context_grain=context.grain,
        loss_rate_provenance=context.provenance,
        inherited_issues=(),
    )


def _relevant_issues(
    report: CanonicalConstructionReport, *, component: CanonicalObject
) -> tuple[Issue, ...]:
    """Canonical issues that already describe this component's unresolved state.

    The rule **reuses** the existing canonical / validation issues instead of creating a
    new taxonomy: it never rewrites ``SEMANTIC_UNRESOLVED`` into ``MISSING``, never adds a
    category / reason and never changes the package disposition.  Matching is by the
    accepted record the issue is reported against, and the issues are re-published
    unchanged so the affected calculation stays auditable.
    """

    reference = component.record_reference or ""
    parts = reference.split("|")
    artifact = parts[2] if len(parts) > 2 else ""
    ordinal = parts[3] if len(parts) > 3 else ""
    record_location = f"{artifact}[{ordinal}]" if artifact and ordinal else ""

    material = component.value_of("material_code", ABSENT)
    matched = []
    for issue in report.issues:
        haystacks = (
            issue.location or "",
            issue.affected_evidence or "",
            issue.detail or "",
        )
        record_hit = any(
            reference in haystack or (record_location and record_location in haystack)
            for haystack in haystacks
        )
        artifact_hit = bool(
            artifact
            and ordinal
            and artifact in (issue.location or "")
            and f"[{ordinal}]" in (issue.location or "")
        )
        material_hit = bool(
            isinstance(material, str) and material and material in (issue.detail or "")
        )
        if record_hit or artifact_hit or material_hit:
            matched.append(issue)
    return tuple(sorted(matched, key=Issue.sort_key))


def _with_cumulative(
    calculations: list[RequirementCalculation],
) -> tuple[RequirementCalculation, ...]:
    """Attach ``CumulativeGrossRequirement`` per registered grouping (``§2.4.9``).

    The grouping is ``plant_id`` + component ``material_code``; within a group the
    cumulative value at a calculation's ``required_date`` is the exact rational sum over
    **all** numeric ``GrossRequirement`` contributions whose ``required_date`` is less than
    or equal to it.  Several contributions on the same date all enter the sum -- there is no
    first-wins / last-wins selection -- and no cross-plant or cross-component aggregation
    happens.  The accumulation stays in exact rational arithmetic: no ``Decimal`` context
    precision is re-entered.

    Only calculations that actually carry a numeric ``GrossRequirement`` enter the grouping:
    an incomplete calculation keeps ``CumulativeGrossRequirement = None`` and is never pulled
    into a group (its grain representation may not even be usable as a grouping key).  As a
    defensive guarantee, a numeric grain that still cannot be grouped keeps an unresolved
    cumulative value instead of breaking the whole result -- the value is never retyped,
    stringified or grouped by ``repr``, and no same-value deduplication happens.
    """

    groups: dict[tuple[Any, Any], list[int]] = {}
    for position, item in enumerate(calculations):
        if not item.has_numeric_result:
            continue
        key = (item.plant_id, item.component_material_code)
        if not _groupable(key):
            continue
        groups.setdefault(key, []).append(position)

    cumulative: dict[int, Fraction] = {}
    for positions in groups.values():
        dated: list[tuple[str, int]] = []
        for position in positions:
            item = calculations[position]
            if not item.has_numeric_result:
                continue
            dated.append((_sort_text(item.required_date), position))
        dated.sort(key=lambda pair: (pair[0], pair[1]))

        running = Fraction(0)
        pending: list[int] = []
        current_date: str | None = None
        for date_key, position in dated:
            if date_key != current_date:
                for queued in pending:
                    cumulative[queued] = running
                pending = []
                current_date = date_key
            # Every contribution on the same date joins the same cumulative total: no
            # first-wins / last-wins selection.
            pending.append(position)
            assert calculations[position].gross_requirement is not None
            running = running + calculations[position].gross_requirement  # type: ignore[operator]
        for queued in pending:
            cumulative[queued] = running

    return tuple(
        replace(item, cumulative_gross_requirement=cumulative.get(position))
        for position, item in enumerate(calculations)
    )


__all__ = [
    "CALCULATION_GRAIN_PROPERTIES",
    "LOSS_RATE_MAXIMUM_EXCLUSIVE",
    "LOSS_RATE_MINIMUM",
    "OUTCOME_DATA_INCOMPLETE",
    "RULE_ID",
    "RequirementCalculation",
    "RequirementCalculationResult",
    "base_requirement",
    "compute_requirement_calculation",
    "gross_requirement",
    "requirement_calculation_context_grain",
]
