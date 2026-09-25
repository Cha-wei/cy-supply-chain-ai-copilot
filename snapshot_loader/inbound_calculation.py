"""``BR-INBOUND-001`` -- Effective Inbound (``§2.6``).

A purchase order / inbound record only counts as future supply when **all** of the
following hold (``§2.6.1``):

1. the PO / inbound status is eligible (``§2.6.3``);
2. ``RemainingInboundQty > 0`` (``§2.6.2``);
3. ``effective_arrival_date`` is reliably available (``§2.6.4``);
4. ``effective_arrival_date <= required_date`` (``§2.6.5``).

Canonical authority implemented:

* ``poc-design-v0.2.md`` §2.6 (``BR-INBOUND-001``, ``DESIGN RESOLVED`` /
  Human-approved): business definition, ``RemainingInboundQty``, status eligibility,
  ``effective_arrival_date`` semantics, the date boundary, the deterministic formula, the
  plant / material boundary, the no-double-counting rule, the acceptance examples and the
  AI / source-field boundaries.
* ``data-dictionary.md`` §4.2.6 / §4.2.10: ``RemainingInboundQty`` / ``EffectiveInbound`` /
  ``CumulativeEffectiveInbound`` are ``DERIVED`` and their missing behaviour is
  ``DATA_INCOMPLETE``.
* ``data-validation.md`` §4.4.30 (inbound field boundary), §4.4.88 (valid zero is not an
  issue), §4.4.89 (valid but ineligible is not an issue by default).
* ``adr-001-deterministic-core.md``: in-memory, standard-library-first, canonical exact
  numeric semantics, core independent of the CLI.

Input boundary: the rule consumes the already constructed
:attr:`~snapshot_loader.canonical_objects.CanonicalConstructionReport.inbound_records` and
the already computed ``BR-REQUIREMENT-001`` result.  It never re-reads a raw snapshot
artifact, never re-runs source mapping, never creates a real ERP PO identity, never guesses
an arrival date, a status, a plant or a material, and never deduplicates inbound records:
two content-identical records at different ordinals are two distinct supply evidence.

Target required-date contexts come from ``BR-REQUIREMENT-001``
(``plant_id`` + component ``material_code`` + ``required_date``); the caller does not inject
a business ``required_date`` and the requirement result itself is never modified.

Deliberately **not** implemented here: ``BR-INVENTORY-001`` (including inventory same-grain
aggregation and warehouse scope realisation), ``BR-SUBSTITUTE-001``, ``BR-SHORTAGE-001``,
``BR-PROCUREMENT-001``, supplier risk, any ERP adapter / PO identity, any persistence and any
quantity precision / rounding policy.  The concrete ERP source-field mapping of
``effective_arrival_date`` stays source-specific / Adapter-defined.
"""

from __future__ import annotations

import datetime as _datetime
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from .canonical_objects import (
    ABSENT,
    CanonicalConstructionReport,
    CanonicalObject,
    EvidenceReference,
)
from .constants import DECIMAL_STRING_PATTERN
from .issues import Issue
from .requirement_calculation import (
    OUTCOME_DATA_INCOMPLETE,
    RequirementCalculation,
    RequirementCalculationResult,
)

# --- vocabulary --------------------------------------------------------------------

#: The rule identity this module implements.
INBOUND_RULE_ID: str = "BR-INBOUND-001"

#: Statuses that allow an inbound to count as future supply (``§2.6.3``).
ELIGIBLE_INBOUND_STATUSES: frozenset[str] = frozenset(
    {"OPEN", "CONFIRMED", "PARTIALLY_RECEIVED"}
)

#: Statuses that are valid business states but **never** future supply (``§2.6.3``).
INELIGIBLE_INBOUND_STATUSES: frozenset[str] = frozenset(
    {"CANCELLED", "CLOSED", "COMPLETED"}
)

#: The registered failure outcome used by this rule.  It is the same canonical
#: ``DATA_INCOMPLETE`` business outcome (``§2.6`` / ``§4.4.85``); this module exposes it
#: under an inbound-specific name so both rule modules can re-export it without colliding.
#: No new outcome vocabulary is created.
EFFECTIVE_INBOUND_DATA_INCOMPLETE: str = OUTCOME_DATA_INCOMPLETE

#: The exact registered inbound status vocabulary (``§2.6.3`` / ``§4.2.14``).
REGISTERED_INBOUND_STATUSES: frozenset[str] = (
    ELIGIBLE_INBOUND_STATUSES | INELIGIBLE_INBOUND_STATUSES
)

_DECIMAL_STRING_RE = re.compile(rf"^{DECIMAL_STRING_PATTERN}$")
_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


def _as_decimal(value: Any) -> Decimal | None:
    """Return the exact base-10 ``Decimal`` for a canonical decimal value.

    Canonical quantity inputs keep their exact base-10 value: a JSON ``null``, a non-string
    value or a string outside the registered decimal form yields ``None`` and is never
    repaired, clamped or defaulted.
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


def remaining_inbound_qty(ordered_qty: Decimal, received_qty: Decimal) -> Decimal:
    """``RemainingInboundQty = ordered_qty - received_qty`` (``§2.6.2``).

    The caller has already established ``ordered_qty >= 0`` and
    ``received_qty >= 0``.  No clamp, no absolute value and no coercion to ``0`` is applied;
    a negative result is a data-quality condition handled by the caller as
    ``DATA_INCOMPLETE``.
    """

    return ordered_qty - received_qty


# --- result representation ---------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EffectiveInboundEvaluation:
    """One inbound record evaluated against one target required date.

    ``remaining_inbound_qty`` is ``None`` when the affected evaluation is
    ``DATA_INCOMPLETE``; a normalised value is never emitted for an unreliable record.
    ``effective_inbound_qty`` is the registered ``EffectiveInbound`` derived quantity for
    this ``(inbound, required_date)`` pair -- ``0`` for a *valid* record that simply does
    not contribute (ineligible status, arrival after the required date, or zero remaining),
    and ``None`` when the record itself is unreliable.

    ``inbound_reference`` is the G3-A AcceptedPackage-scoped technical record reference; no
    real ERP PO identity is created.
    """

    target_plant_id: Any
    target_material_code: Any
    target_required_date: Any
    inbound_reference: str
    inbound_role: str
    ordered_qty: Decimal | None
    received_qty: Decimal | None
    remaining_inbound_qty: Decimal | None
    inbound_status: Any
    effective_arrival_date: Any
    status_eligible: bool | None
    effective_inbound_qty: Decimal | None
    outcome: str | None = None
    notes: tuple[str, ...] = ()
    provenance: EvidenceReference | None = None
    inherited_issues: tuple[Issue, ...] = ()

    @property
    def data_incomplete(self) -> bool:
        return self.outcome == EFFECTIVE_INBOUND_DATA_INCOMPLETE

    @property
    def contributes(self) -> bool:
        """Whether this inbound adds supply at the target required date."""

        return (
            self.outcome is None
            and self.effective_inbound_qty is not None
            and self.effective_inbound_qty > Decimal("0")
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "rule": INBOUND_RULE_ID,
            "target": {
                "plant_id": self.target_plant_id,
                "material_code": self.target_material_code,
                "required_date": self.target_required_date,
            },
            "inbound_reference": self.inbound_reference,
            "inbound_role": self.inbound_role,
            "ordered_qty": _quantity_text(self.ordered_qty),
            "received_qty": _quantity_text(self.received_qty),
            "RemainingInboundQty": _quantity_text(self.remaining_inbound_qty),
            "inbound_status": self.inbound_status,
            "effective_arrival_date": self.effective_arrival_date,
            "status_eligible": self.status_eligible,
            "EffectiveInboundQty": _quantity_text(self.effective_inbound_qty),
            "outcome": self.outcome,
            "notes": list(self.notes),
            "provenance": (
                None
                if self.provenance is None
                else {
                    "snapshot_package_identity": (
                        self.provenance.snapshot_package_identity
                    ),
                    "logical_dataset_role": self.provenance.logical_dataset_role,
                    "stable_source_evidence_locators": list(
                        self.provenance.stable_source_evidence_locators
                    ),
                    "accepted_record_path": self.provenance.record_path,
                }
            ),
            "inherited_issues": [issue.to_dict() for issue in self.inherited_issues],
        }


@dataclass(frozen=True, slots=True)
class EffectiveInboundTarget:
    """The registered cumulative grain: ``plant_id`` + ``material_code`` + ``required_date``.

    ``cumulative_effective_inbound`` is ``None`` when the affected target is
    ``DATA_INCOMPLETE``; a normalised cumulative supply is never produced for an
    unreliable target.
    """

    plant_id: Any
    material_code: Any
    required_date: Any
    evaluations: tuple[EffectiveInboundEvaluation, ...]
    cumulative_effective_inbound: Decimal | None
    outcome: str | None = None
    notes: tuple[str, ...] = ()
    requirement_reference: str | None = None
    requirement_provenance: EvidenceReference | None = None
    inherited_issues: tuple[Issue, ...] = ()

    @property
    def data_incomplete(self) -> bool:
        return self.outcome == EFFECTIVE_INBOUND_DATA_INCOMPLETE

    @property
    def contributing_evaluations(self) -> tuple[EffectiveInboundEvaluation, ...]:
        return tuple(item for item in self.evaluations if item.contributes)

    def to_dict(self) -> dict[str, object]:
        return {
            "rule": INBOUND_RULE_ID,
            "plant_id": self.plant_id,
            "material_code": self.material_code,
            "required_date": self.required_date,
            "CumulativeEffectiveInbound": _quantity_text(
                self.cumulative_effective_inbound
            ),
            "outcome": self.outcome,
            "notes": list(self.notes),
            "requirement_reference": self.requirement_reference,
            "evaluations": [item.to_dict() for item in self.evaluations],
            "inherited_issues": [issue.to_dict() for issue in self.inherited_issues],
        }


@dataclass(frozen=True, slots=True)
class EffectiveInboundResult:
    """Deterministic result of ``BR-INBOUND-001`` for one construction.

    ``targets`` is ordered deterministically by ``plant_id`` + ``material_code`` +
    ``required_date``.  No cross-plant or cross-material aggregation is performed.
    """

    targets: tuple[EffectiveInboundTarget, ...]

    @property
    def data_incomplete_targets(self) -> tuple[EffectiveInboundTarget, ...]:
        return tuple(item for item in self.targets if item.data_incomplete)

    def for_grain(
        self, plant_id: Any, material_code: Any, required_date: Any
    ) -> EffectiveInboundTarget | None:
        for item in self.targets:
            if (
                item.plant_id == plant_id
                and item.material_code == material_code
                and item.required_date == required_date
            ):
                return item
        return None

    def to_dict(self) -> dict[str, object]:
        return {
            "rule": INBOUND_RULE_ID,
            "targets": [item.to_dict() for item in self.targets],
        }


def _quantity_text(value: Decimal | None) -> str | None:
    """Render a canonical quantity exactly: plain base-10 digits, never an exponent."""

    if value is None:
        return None
    return format(value, "f")


# --- rule execution ----------------------------------------------------------------


def compute_effective_inbound(
    construction: CanonicalConstructionReport,
    requirements: RequirementCalculationResult,
) -> EffectiveInboundResult:
    """Run ``BR-INBOUND-001`` over constructed inbounds and requirement contexts.

    Target grains come from ``BR-REQUIREMENT-001`` (``plant_id`` + component
    ``material_code`` + ``required_date``); the caller never injects a business
    ``required_date`` and the requirement result is not modified.  Every constructed inbound
    record is evaluated against every target independently: inbound records are never
    deduplicated, aggregated across plants / materials, or reconciled by any precedence.
    """

    targets = _targets_from_requirements(requirements)
    inbounds = tuple(construction.inbound_records)

    outbound: list[EffectiveInboundTarget] = []
    for plant_id, material_code, required_date, requirement in targets:
        evaluations = tuple(
            _evaluate_inbound(
                inbound=inbound,
                plant_id=plant_id,
                material_code=material_code,
                required_date=required_date,
                construction=construction,
            )
            for inbound in inbounds
        )
        cumulative: Decimal | None = Decimal("0")
        notes: list[str] = []
        outcome: str | None = None

        if requirement is None or requirement.data_incomplete:
            cumulative = None
            outcome = EFFECTIVE_INBOUND_DATA_INCOMPLETE
            notes.append(
                "the required-date evaluation context is DATA_INCOMPLETE, so no numeric "
                "cumulative effective inbound supply is produced (§2.6.6)"
            )
        elif any(item.data_incomplete for item in evaluations):
            # A required-date boundary cannot be resolved while any contributing inbound
            # record is unreliable: no normalised cumulative supply is produced.
            cumulative = None
            outcome = EFFECTIVE_INBOUND_DATA_INCOMPLETE
            notes.append(
                "at least one inbound record has an unreliable prerequisite "
                "(§2.6.2 / §2.6.3 / §2.6.5), so no numeric cumulative effective inbound "
                "supply is produced for this target"
            )
        else:
            for item in evaluations:
                assert item.effective_inbound_qty is not None
                cumulative = cumulative + item.effective_inbound_qty

        inherited: list[Issue] = []
        for item in evaluations:
            inherited.extend(item.inherited_issues)
        if requirement is not None:
            inherited.extend(requirement.inherited_issues)

        outbound.append(
            EffectiveInboundTarget(
                plant_id=plant_id,
                material_code=material_code,
                required_date=required_date,
                evaluations=evaluations,
                cumulative_effective_inbound=cumulative,
                outcome=outcome,
                notes=tuple(notes),
                requirement_reference=(
                    requirement.bom_component_reference
                    if requirement is not None
                    else None
                ),
                requirement_provenance=(
                    requirement.loss_rate_provenance
                    if requirement is not None
                    else None
                ),
                inherited_issues=tuple(sorted(inherited, key=Issue.sort_key)),
            )
        )

    outbound.sort(
        key=lambda item: (
            _sort_text(item.plant_id),
            _sort_text(item.material_code),
            _sort_text(item.required_date),
        )
    )
    return EffectiveInboundResult(targets=tuple(outbound))


def _targets_from_requirements(
    requirements: RequirementCalculationResult,
) -> tuple[tuple[Any, Any, Any, RequirementCalculation | None], ...]:
    """The registered targets: ``plant_id`` + ``material_code`` + ``required_date``.

    The contexts come from the resolved ``BR-REQUIREMENT-001`` result, so no caller-supplied
    business ``required_date`` is accepted and no raw artifact is re-read.  A requirement
    row whose calculation is ``DATA_INCOMPLETE`` still states the grain and therefore
    produces a ``DATA_INCOMPLETE`` target rather than a silently missing one.
    """

    seen: dict[tuple[Any, Any, Any], RequirementCalculation] = {}
    for calculation in requirements.calculations:
        key = (
            calculation.plant_id,
            calculation.component_material_code,
            calculation.required_date,
        )
        if key in seen:
            continue
        seen[key] = calculation

    return tuple(
        (plant_id, material_code, required_date, seen[key])
        for key in sorted(seen, key=lambda item: tuple(_sort_text(part) for part in item))
        for plant_id, material_code, required_date in (key,)
    )


def _sort_text(value: Any) -> str:
    return "" if value is None else str(value)


def _evaluate_inbound(
    *,
    inbound: CanonicalObject,
    plant_id: Any,
    material_code: Any,
    required_date: Any,
    construction: CanonicalConstructionReport,
) -> EffectiveInboundEvaluation:
    """Evaluate one inbound record against one target required date (``§2.6.6``)."""

    ordered_qty = _as_decimal(inbound.value_of("ordered_qty", ABSENT))
    received_qty = _as_decimal(inbound.value_of("received_qty", ABSENT))
    status_value = inbound.value_of("inbound_status", ABSENT)
    arrival_value = inbound.value_of("effective_arrival_date", ABSENT)
    inbound_material = inbound.value_of("material_code", ABSENT)
    inbound_plant = inbound.value_of("plant_id", ABSENT)

    def evaluation(
        *,
        remaining: Decimal | None,
        status_eligible: bool | None,
        effective: Decimal | None,
        outcome: str | None,
        notes: tuple[str, ...],
    ) -> EffectiveInboundEvaluation:
        return EffectiveInboundEvaluation(
            target_plant_id=plant_id,
            target_material_code=material_code,
            target_required_date=required_date,
            inbound_reference=inbound.record_reference,
            inbound_role=inbound.canonicalization_role,
            ordered_qty=ordered_qty,
            received_qty=received_qty,
            remaining_inbound_qty=remaining,
            inbound_status=None if status_value is ABSENT else status_value,
            effective_arrival_date=(
                None if arrival_value is ABSENT else arrival_value
            ),
            status_eligible=status_eligible,
            effective_inbound_qty=effective,
            outcome=outcome,
            notes=notes,
            provenance=inbound.provenance,
            inherited_issues=_relevant_issues(inbound, construction),
        )

    # --- prerequisite: the inbound must map to this plant / material ----------------
    if inbound_plant is ABSENT:
        return evaluation(
            remaining=None,
            status_eligible=None,
            effective=None,
            outcome=EFFECTIVE_INBOUND_DATA_INCOMPLETE,
            notes=(
                "the inbound record's plant identity is unresolved, so it cannot be "
                "mapped to this target plant (§2.6.7)",
            ),
        )
    if inbound_plant != plant_id:
        # A valid record that belongs to another plant: it is not this target's supply, and
        # no cross-plant borrowing is applied.
        return evaluation(
            remaining=None,
            status_eligible=None,
            effective=Decimal("0"),
            outcome=None,
            notes=(
                "the inbound record belongs to another plant; it does not contribute to "
                "this target and is never borrowed across plants (§2.6.7)",
            ),
        )
    if inbound_material is ABSENT:
        return evaluation(
            remaining=None,
            status_eligible=None,
            effective=None,
            outcome=EFFECTIVE_INBOUND_DATA_INCOMPLETE,
            notes=(
                "the inbound record's material identity is unresolved, so it cannot be "
                "mapped to this target material (§2.6.7)",
            ),
        )
    if inbound_material != material_code:
        # A valid record that simply belongs to another material: it is not this target's
        # supply, and no cross-material reuse is applied.
        return evaluation(
            remaining=None,
            status_eligible=None,
            effective=Decimal("0"),
            outcome=None,
            notes=(
                "the inbound record belongs to another material; it does not contribute to "
                "this target and is never reused across materials (§2.6.7)",
            ),
        )

    # --- prerequisite: ordered / received quantities -------------------------------
    if ordered_qty is None:
        return evaluation(
            remaining=None,
            status_eligible=None,
            effective=None,
            outcome=EFFECTIVE_INBOUND_DATA_INCOMPLETE,
            notes=(
                "ordered_qty is missing or is not a registered base-10 decimal; no "
                "remaining quantity is produced and no default is applied (§2.6.2)",
            ),
        )
    if ordered_qty < Decimal("0"):
        return evaluation(
            remaining=None,
            status_eligible=None,
            effective=None,
            outcome=EFFECTIVE_INBOUND_DATA_INCOMPLETE,
            notes=(
                "ordered_qty is negative, which is not a registered canonical quantity "
                "(§2.6.2 / §4.2.6)",
            ),
        )
    if received_qty is None:
        return evaluation(
            remaining=None,
            status_eligible=None,
            effective=None,
            outcome=EFFECTIVE_INBOUND_DATA_INCOMPLETE,
            notes=(
                "received_qty is missing or is not a registered base-10 decimal; no "
                "remaining quantity is produced and no default is applied (§2.6.2)",
            ),
        )
    if received_qty < Decimal("0"):
        return evaluation(
            remaining=None,
            status_eligible=None,
            effective=None,
            outcome=EFFECTIVE_INBOUND_DATA_INCOMPLETE,
            notes=(
                "received_qty is negative, which is not a registered canonical quantity "
                "(§2.6.2 / §4.2.6)",
            ),
        )
    if received_qty > ordered_qty:
        # ``§2.6.2``: never clamped, never coerced to 0, never interpreted.
        return evaluation(
            remaining=None,
            status_eligible=None,
            effective=None,
            outcome=EFFECTIVE_INBOUND_DATA_INCOMPLETE,
            notes=(
                f"received_qty {received_qty} exceeds ordered_qty {ordered_qty}; the "
                "remaining quantity is not clamped, not replaced by 0 and not given a "
                "guessed business meaning (§2.6.2)",
            ),
        )

    remaining = remaining_inbound_qty(ordered_qty, received_qty)

    # --- prerequisite: status eligibility ------------------------------------------
    if status_value is ABSENT:
        return evaluation(
            remaining=remaining,
            status_eligible=None,
            effective=None,
            outcome=EFFECTIVE_INBOUND_DATA_INCOMPLETE,
            notes=(
                "inbound_status is missing; the status is never defaulted to OPEN / "
                "CONFIRMED (§2.6.3)",
            ),
        )
    if not isinstance(status_value, str) or status_value not in REGISTERED_INBOUND_STATUSES:
        return evaluation(
            remaining=remaining,
            status_eligible=None,
            effective=None,
            outcome=EFFECTIVE_INBOUND_DATA_INCOMPLETE,
            notes=(
                f"inbound_status {status_value!r} is not in the registered canonical "
                "vocabulary; the status is never guessed (§2.6.3)",
            ),
        )

    eligible = status_value in ELIGIBLE_INBOUND_STATUSES

    # --- prerequisite: effective arrival date --------------------------------------
    arrival = _as_date(arrival_value)
    if arrival is None:
        return evaluation(
            remaining=remaining,
            status_eligible=eligible,
            effective=None,
            outcome=EFFECTIVE_INBOUND_DATA_INCOMPLETE,
            notes=(
                "effective_arrival_date is missing or is not a valid DATE; it is never "
                "defaulted to today, the required date, the analysis date or the PO "
                "creation date (§2.6.5)",
            ),
        )

    required = _as_date(required_date)
    if required is None:
        return evaluation(
            remaining=remaining,
            status_eligible=eligible,
            effective=None,
            outcome=EFFECTIVE_INBOUND_DATA_INCOMPLETE,
            notes=(
                "the target required_date is not a valid DATE, so the arrival-date "
                "boundary cannot be evaluated (§2.6.5)",
            ),
        )

    # A valid but ineligible status, a zero remaining quantity and a later arrival are all
    # ``0`` contributions -- never a Data Quality Issue (§2.6.5 / §4.4.88 / §4.4.89).
    if not eligible:
        return evaluation(
            remaining=remaining,
            status_eligible=False,
            effective=Decimal("0"),
            outcome=None,
            notes=(
                "status is valid but ineligible for future supply; the record stays valid "
                "and contributes 0 (§2.6.3 / §4.4.89)",
            ),
        )
    if remaining <= Decimal("0"):
        return evaluation(
            remaining=remaining,
            status_eligible=True,
            effective=Decimal("0"),
            outcome=None,
            notes=(
                "RemainingInboundQty is 0, which is a valid value and contributes 0 "
                "(§2.6.2 / §4.4.88)",
            ),
        )
    if arrival > required:
        return evaluation(
            remaining=remaining,
            status_eligible=True,
            effective=Decimal("0"),
            outcome=None,
            notes=(
                "effective_arrival_date is after the target required_date; it is not a "
                "data-quality issue and the record can contribute at a later required "
                "date (§2.6.5)",
            ),
        )

    return evaluation(
        remaining=remaining,
        status_eligible=True,
        effective=remaining,
        outcome=None,
        notes=(),
    )


def _relevant_issues(
    inbound: CanonicalObject, construction: CanonicalConstructionReport
) -> tuple[Issue, ...]:
    """Canonical issues already describing this inbound record (reused unchanged).

    The rule never adds a validation category / reason and never rewrites an invalid or
    unresolved condition into ``MISSING``: the findings the construction already raised for
    this accepted record are re-published exactly as they were.
    """

    reference = inbound.record_reference or ""
    parts = reference.split("|")
    artifact = parts[2] if len(parts) > 2 else ""
    ordinal = parts[3] if len(parts) > 3 else ""
    record_location = f"{artifact}[{ordinal}]" if artifact and ordinal else ""
    material = inbound.value_of("material_code", ABSENT)

    matched = []
    for issue in construction.issues:
        haystacks = (
            issue.location or "",
            issue.affected_evidence or "",
            issue.detail or "",
        )
        record_hit = any(
            reference in haystack or (record_location and record_location in haystack)
            for haystack in haystacks
        )
        material_hit = bool(
            isinstance(material, str) and material and material in (issue.detail or "")
        )
        if record_hit or material_hit:
            matched.append(issue)
    return tuple(sorted(matched, key=Issue.sort_key))

__all__ = [
    "EFFECTIVE_INBOUND_DATA_INCOMPLETE",
    "ELIGIBLE_INBOUND_STATUSES",
    "INBOUND_RULE_ID",
    "INELIGIBLE_INBOUND_STATUSES",
    "REGISTERED_INBOUND_STATUSES",
    "EffectiveInboundEvaluation",
    "EffectiveInboundResult",
    "EffectiveInboundTarget",
    "compute_effective_inbound",
    "remaining_inbound_qty",
]
