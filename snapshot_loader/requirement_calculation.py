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
from decimal import Decimal, InvalidOperation, localcontext
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

#: Business outcome used by ``§2.4`` and by ``§4.4.85``: a business result, not a
#: validation issue category / reason.  No new taxonomy is introduced.
OUTCOME_NUMERIC: str = "NUMERIC"
OUTCOME_DATA_INCOMPLETE: str = "DATA_INCOMPLETE"

#: The rule identity this module implements.
RULE_ID: str = "BR-REQUIREMENT-001"

#: ``0 <= loss_rate < 1`` (``§2.4.5`` / ``§2.4.6``).
LOSS_RATE_MINIMUM: Decimal = Decimal("0")
LOSS_RATE_MAXIMUM_EXCLUSIVE: Decimal = Decimal("1")

#: Working precision for the ``GrossRequirement`` division.
#:
#: ``BaseRequirement / (1 - loss_rate)`` need not terminate in base 10, so the division
#: is performed under an explicitly widened precision instead of silently inheriting the
#: library default.  This is **not** a business precision / rounding policy (``§2.4.8``
#: leaves that to a later Design Rule): no rounding, quantizing or truncation is applied;
#: the operation is merely carried out with a precision far beyond any registered
#: quantity semantics so that no intermediate step silently loses digits.
WORKING_DECIMAL_PRECISION: int = 60

_DECIMAL_STRING_RE = re.compile(rf"^{DECIMAL_STRING_PATTERN}$")
_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")

CALCULATION_GRAIN_PROPERTIES: tuple[str, ...] = (
    "plant_id",
    "material_code",
    "required_date",
)


# --- result representation ---------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RequirementCalculation:
    """One deterministic requirement calculation for one calculation grain.

    ``grain`` is the calculation grain registered by ``§2.4.2``: ``plant_id`` + component
    ``material_code`` + ``required_date``.  ``base_requirement`` / ``gross_requirement``
    are ``None`` exactly when ``outcome`` is ``DATA_INCOMPLETE``: a ``DATA_INCOMPLETE``
    calculation never carries a numeric ``GrossRequirement`` (``§2.4.11``).

    Traceability (``§2.4.2``): ``production_requirement_reference`` and
    ``bom_component_reference`` name the resolved canonical objects this calculation was
    derived from, ``context_reference`` is the resolved Production Requirement context the
    BOM Component relationship was bound to, and ``loss_rate_provenance`` is the resolved
    Requirement Calculation Context's own provenance.
    """

    plant_id: Any
    component_material_code: Any
    required_date: Any
    grain: tuple[CanonicalProperty, ...]
    base_requirement: Decimal | None
    loss_rate: Decimal | None
    gross_requirement: Decimal | None
    cumulative_gross_requirement: Decimal | None
    outcome: str
    notes: tuple[str, ...] = ()
    production_requirement_reference: str | None = None
    bom_component_reference: str | None = None
    context_reference: str | None = None
    bom_component_provenance: EvidenceReference | None = None
    production_requirement_provenance: EvidenceReference | None = None
    loss_rate_context_grain: tuple[CanonicalProperty, ...] | None = None
    loss_rate_provenance: EvidenceReference | None = None
    inherited_issues: tuple[Issue, ...] = ()

    @property
    def data_incomplete(self) -> bool:
        return self.outcome == OUTCOME_DATA_INCOMPLETE

    @property
    def numeric(self) -> bool:
        return self.outcome == OUTCOME_NUMERIC

    def to_dict(self) -> dict[str, object]:
        return {
            "rule": RULE_ID,
            "plant_id": self.plant_id,
            "component_material_code": self.component_material_code,
            "required_date": self.required_date,
            "grain": [
                {"name": prop.name, "value": prop.value} for prop in self.grain
            ],
            "BaseRequirement": _decimal_text(self.base_requirement),
            "loss_rate": _decimal_text(self.loss_rate),
            "GrossRequirement": _decimal_text(self.gross_requirement),
            "CumulativeGrossRequirement": _decimal_text(
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

    ``calculations`` is ordered deterministically by calculation grain.  No cross-plant or
    cross-component aggregation is performed: the cumulative value is reported per
    calculation grain (``plant_id`` + component ``material_code``), which is exactly the
    grouping ``§2.4.9`` registers.
    """

    calculations: tuple[RequirementCalculation, ...]

    @property
    def numeric(self) -> tuple[RequirementCalculation, ...]:
        return tuple(item for item in self.calculations if item.numeric)

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


def _decimal_text(value: Decimal | None) -> str | None:
    """Render a canonical quantity exactly: plain base-10 digits, never an exponent."""

    if value is None:
        return None
    return format(value, "f")


# --- arithmetic --------------------------------------------------------------------


def requirement_calculation_context_grain(
    context: ContextValueReference,
) -> tuple[CanonicalProperty, ...]:
    """Return the registered four-part grain of a resolved loss_rate context."""

    return context.grain


def _context_grain_key(context: ContextValueReference) -> tuple[Any, ...]:
    return tuple(prop.value for prop in context.grain)


def _context_by_grain(
    contexts: Iterable[ContextValueReference],
) -> dict[tuple[Any, ...], ContextValueReference]:
    """Index the resolved ``loss_rate`` Requirement Calculation Contexts by their grain.

    Exactly one context per registered four-part grain is the canonicalization contract
    (``§4.3.31`` G I-2 / ``§4.4.15``); if one grain somehow appears more than once it is
    kept out of the index rather than letting one silently win.
    """

    index: dict[tuple[Any, ...], ContextValueReference] = {}
    duplicated: set[tuple[Any, ...]] = set()
    for context in contexts:
        key = _context_grain_key(context)
        if key in index:
            duplicated.add(key)
            continue
        index[key] = context
    for key in duplicated:
        index.pop(key, None)
    return index


def _as_decimal(value: Any) -> Decimal | None:
    """Return the exact base-10 ``Decimal`` for a canonical decimal value.

    Returns ``None`` for JSON ``null``, for a non-string value and for a string that is
    not a registered base-10 decimal (``§4.3.25`` C-5).  No binary floating point is used,
    and no value is repaired or defaulted.
    """

    if not isinstance(value, str):
        return None
    if not _DECIMAL_STRING_RE.match(value):
        return None
    try:
        return Decimal(value)
    except InvalidOperation:  # pragma: no cover - guarded by the pattern
        return None


def _as_date(value: Any) -> _datetime.date | None:
    """Validate the canonical ``DATE`` representation (``§4.3.22`` C-3)."""

    if not isinstance(value, str) or not _DATE_RE.match(value):
        return None
    try:
        return _datetime.date.fromisoformat(value)
    except ValueError:
        return None


def base_requirement(production_qty: Decimal, bom_component_qty: Decimal) -> Decimal:
    """``BaseRequirement = ProductionQty x BOMComponentQty`` (``§2.4.3``)."""

    with localcontext() as context:
        context.prec = WORKING_DECIMAL_PRECISION
        return production_qty * bom_component_qty


def gross_requirement(base: Decimal, loss_rate: Decimal) -> Decimal:
    """``GrossRequirement = BaseRequirement / (1 - loss_rate)`` (``§2.4.5``).

    The caller has already established ``0 <= loss_rate < 1``.  No rounding, ceiling,
    flooring, truncation or pack-size adjustment is applied (``§2.4.8``).
    """

    with localcontext() as context:
        context.prec = WORKING_DECIMAL_PRECISION
        return base / (Decimal("1") - loss_rate)


def _valid_loss_rate(value: Decimal) -> bool:
    return LOSS_RATE_MINIMUM <= value < LOSS_RATE_MAXIMUM_EXCLUSIVE


# --- rule execution ----------------------------------------------------------------


def compute_requirement_calculation(
    report: CanonicalConstructionReport,
) -> RequirementCalculationResult:
    """Run ``BR-REQUIREMENT-001`` over resolved canonical construction output.

    Only resolved canonical objects are consumed: a ``BOM Component`` that
    canonicalization left unresolved produces **no** calculation grain at all, so the rule
    never fabricates a BOM, a quantity or a ``required_date``.  Every calculation whose
    registered prerequisites cannot be reliably obtained is reported ``DATA_INCOMPLETE``
    with no numeric ``GrossRequirement``.
    """

    contexts = _context_by_grain(report.loss_rate_contexts)
    requirements = {
        obj.record_reference: obj
        for obj in report.objects_for(ROLE_PRODUCTION_REQUIREMENT)
    }

    calculations = [
        _calculate_component(
            component=component,
            requirements=requirements,
            contexts=contexts,
            report=report,
        )
        for component in report.objects_for(ROLE_BOM_COMPONENT)
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
    plant_id = component.value_of("plant_id", ABSENT)
    component_material = component.value_of("material_code", ABSENT)
    required_date = component.value_of("required_date", ABSENT)

    parent = requirements.get(component.context_reference or "")

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

    # --- prerequisite: calculation grain identity ----------------------------------
    if plant_id is ABSENT:
        return incomplete("plant identity is unresolved; no requirement calculation")
    if component_material is ABSENT:
        return incomplete(
            "component material identity is unresolved; no requirement calculation"
        )
    if required_date is ABSENT:
        return incomplete("required_date is missing; no requirement calculation")
    if _as_date(required_date) is None:
        return incomplete(
            f"required_date {required_date!r} is not a valid DATE; no requirement "
            "calculation"
        )

    # --- prerequisite: resolved Production Requirement context ---------------------
    if parent is None:
        return incomplete(
            "the resolved Production Requirement context referenced by this BOM "
            "Component is unavailable; no requirement calculation"
        )

    production_qty = _as_decimal(parent.value_of("ProductionQty", ABSENT))
    if production_qty is None:
        return incomplete(
            "ProductionQty is missing or is not a registered base-10 decimal; no "
            "requirement calculation and no default is applied (§2.4.11)"
        )
    if production_qty < Decimal("0"):
        return incomplete(
            "ProductionQty is negative; no requirement calculation (§2.4.3 / §2.4.11)"
        )

    bom_component_qty = _as_decimal(component.value_of("BOMComponentQty", ABSENT))
    if bom_component_qty is None:
        return incomplete(
            "BOMComponentQty is missing or is not a registered base-10 decimal; no "
            "requirement calculation and no BOM quantity is guessed (§2.4.11)"
        )
    if bom_component_qty < Decimal("0"):
        return incomplete(
            "BOMComponentQty is negative; no requirement calculation (§2.4.3 / §2.4.11)"
        )

    # --- prerequisite: resolved loss_rate Requirement Calculation Context ----------
    parent_material = parent.value_of("material_code", ABSENT)
    context = contexts.get(
        (plant_id, parent_material, required_date, component_material)
    )
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

    loss_rate = _as_decimal(context.value)
    if loss_rate is None:
        return incomplete(
            "the resolved loss_rate value is missing or is not a registered base-10 "
            "decimal; no requirement calculation and no default is applied (§2.4.7)"
        )
    if not _valid_loss_rate(loss_rate):
        return incomplete(
            f"loss_rate {loss_rate} is outside the registered range 0 <= loss_rate < 1; "
            "the value is not clamped, not replaced by 0 and not replaced by the maximum "
            "(§2.4.6 / §4.4.15 root C)"
        )

    base = base_requirement(production_qty, bom_component_qty)
    gross = gross_requirement(base, loss_rate)

    return RequirementCalculation(
        plant_id=plant_id,
        component_material_code=component_material,
        required_date=required_date,
        grain=grain,
        base_requirement=base,
        loss_rate=loss_rate,
        gross_requirement=gross,
        cumulative_gross_requirement=None,  # filled by the cumulative pass
        outcome=OUTCOME_NUMERIC,
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
    affected component material identity, and the issues are re-published unchanged.
    """

    material = component.value_of("material_code", ABSENT)
    if not isinstance(material, str):
        return ()
    matched = [
        issue
        for issue in report.issues
        if material and material in (issue.detail or "")
    ]
    return tuple(sorted(matched, key=Issue.sort_key))


def _with_cumulative(
    calculations: list[RequirementCalculation],
) -> tuple[RequirementCalculation, ...]:
    """Attach ``CumulativeGrossRequirement`` per registered grouping (``§2.4.9``).

    The grouping is ``plant_id`` + component ``material_code``; within a group the
    cumulative value at a calculation's ``required_date`` is the sum over **all** numeric
    ``GrossRequirement`` contributions whose ``required_date`` is less than or equal to
    it.  Several contributions on the same date all enter the sum -- there is no
    first-wins / last-wins selection -- and no cross-plant or cross-component aggregation
    happens.
    """

    groups: dict[tuple[Any, Any], list[int]] = {}
    for position, item in enumerate(calculations):
        groups.setdefault((item.plant_id, item.component_material_code), []).append(
            position
        )

    cumulative: dict[int, Decimal] = {}
    for positions in groups.values():
        dated: list[tuple[str, int]] = []
        for position in positions:
            item = calculations[position]
            if not item.numeric:
                continue
            dated.append((_sort_text(item.required_date), position))
        dated.sort(key=lambda pair: (pair[0], pair[1]))

        running = Decimal("0")
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
    "OUTCOME_NUMERIC",
    "RULE_ID",
    "WORKING_DECIMAL_PRECISION",
    "RequirementCalculation",
    "RequirementCalculationResult",
    "base_requirement",
    "compute_requirement_calculation",
    "gross_requirement",
    "requirement_calculation_context_grain",
]
