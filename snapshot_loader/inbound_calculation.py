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
* ``data-validation.md`` §4.4.30 (inbound field boundary), §4.4.47 / §4.4.92
  (``received_qty > ordered_qty`` is an internal inconsistency that must be reported with the
  registered ``CONSISTENCY`` / ``CONSISTENCY_CONFLICT`` taxonomy **and** the registered
  ``DATA_INCOMPLETE`` outcome), §4.4.88 (valid zero is not an issue), §4.4.89 (valid but
  ineligible is not an issue by default).
* ``adr-001-deterministic-core.md``: in-memory, standard-library-first, canonical exact
  numeric semantics, core independent of the CLI.  Quantity arithmetic is therefore exact by
  construction (:class:`ExactQuantity`), never ``Decimal``-context arithmetic.

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
from typing import Any, Iterable

from .canonical_objects import (
    ABSENT,
    CanonicalConstructionReport,
    CanonicalObject,
    EvidenceReference,
)
from .constants import DECIMAL_STRING_PATTERN, LAYER_2
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


@dataclass(frozen=True, slots=True)
class ExactQuantity:
    """An exact finite base-10 quantity held as a scaled integer.

    ADR-001 forbids treating the ``Decimal`` default context as a business precision and
    forbids silent rounding from a library default.  Standard ``Decimal`` arithmetic is
    context-driven -- ``Decimal("1E+30") - Decimal("1")`` is silently rounded at the default
    28-digit precision -- so the rule does **not** do quantity arithmetic in ``Decimal``.

    Instead a canonical base-10 quantity is represented exactly as
    ``units * 10 ** -scale`` with ``units`` an arbitrary-precision integer, which makes
    addition and subtraction exact by construction on any operand size.  This is an internal
    representation only: :meth:`text` renders the registered public contract -- a plain exact
    finite decimal quantity with no exponent, no rounding, no quantization and no business
    precision / scale policy (the scale a canonical value states is preserved verbatim).
    """

    units: int
    scale: int

    @property
    def negative(self) -> bool:
        return self.units < 0

    def rescale(self, scale: int) -> "ExactQuantity":
        """Widen to ``scale`` decimal places (never loses value: ``scale`` only grows)."""

        if scale < self.scale:  # pragma: no cover - callers only widen
            raise ValueError("ExactQuantity cannot be narrowed without rounding")
        return ExactQuantity(self.units * 10 ** (scale - self.scale), scale)

    def __add__(self, other: "ExactQuantity") -> "ExactQuantity":
        scale = max(self.scale, other.scale)
        return ExactQuantity(
            self.rescale(scale).units + other.rescale(scale).units, scale
        )

    def __sub__(self, other: "ExactQuantity") -> "ExactQuantity":
        scale = max(self.scale, other.scale)
        return ExactQuantity(
            self.rescale(scale).units - other.rescale(scale).units, scale
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ExactQuantity):
            return NotImplemented
        scale = max(self.scale, other.scale)
        return self.rescale(scale).units == other.rescale(scale).units

    def __hash__(self) -> int:
        return hash(self._value_key())

    def __lt__(self, other: "ExactQuantity") -> bool:
        scale = max(self.scale, other.scale)
        return self.rescale(scale).units < other.rescale(scale).units

    def __le__(self, other: "ExactQuantity") -> bool:
        return self < other or self == other

    def __gt__(self, other: "ExactQuantity") -> bool:
        scale = max(self.scale, other.scale)
        return self.rescale(scale).units > other.rescale(scale).units

    def __ge__(self, other: "ExactQuantity") -> bool:
        return self > other or self == other

    def _value_key(self) -> tuple[int, int]:
        """Value identity, so equal quantities hash equally whatever scale they carry."""

        units, scale = self.units, self.scale
        while scale > 0 and units % 10 == 0:
            units //= 10
            scale -= 1
        return units, scale

    def text(self) -> str:
        """The exact canonical decimal text: plain digits, no exponent, no rounding.

        The stored scale is preserved, so a canonical value that states ``"0.50"`` is
        rendered as ``"0.50"``.  ``IC-10`` forbids rounding, quantization, truncation and
        silent trimming of a canonical decimal representation; the scale therefore carries
        no business-precision policy, it is simply never normalised away.
        """

        sign = "-" if self.units < 0 else ""
        digits = str(abs(self.units))
        if self.scale == 0:
            return f"{sign}{digits}"
        digits = digits.rjust(self.scale + 1, "0")
        whole, fraction = digits[: -self.scale], digits[-self.scale :]
        return f"{sign}{whole}.{fraction}"


def parse_exact_quantity(value: Any) -> ExactQuantity | None:
    """Parse a canonical base-10 decimal string into an exact scaled integer.

    ``None`` means the value is not a registered canonical decimal (JSON ``null``, a
    non-string, an empty string or a malformed form).  Nothing is repaired or defaulted.
    """

    if not isinstance(value, str) or not value:
        return None
    if not _DECIMAL_STRING_RE.match(value):
        return None
    body = value[1:] if value[0] in "+-" else value
    sign = -1 if value[0] == "-" else 1
    if "." in body:
        whole, fraction = body.split(".", 1)
    else:
        whole, fraction = body, ""
    digits = f"{whole or '0'}{fraction}"
    try:
        units = int(digits)
    except ValueError:  # pragma: no cover - guarded by the registered pattern
        return None
    return ExactQuantity(sign * units, len(fraction))


def parse_non_negative_quantity(value: Any) -> ExactQuantity | None:
    """Parse a canonical quantity that must be non-negative (``NON_NEGATIVE_QUANTITY``)."""

    parsed = parse_exact_quantity(value)
    if parsed is None:
        return None
    if parsed.negative:
        return None
    return parsed


def _as_date(value: Any) -> _datetime.date | None:
    """Validate the canonical ``DATE`` representation (``§4.3.22`` C-3)."""

    if not isinstance(value, str) or not _DATE_RE.match(value):
        return None
    try:
        return _datetime.date.fromisoformat(value)
    except ValueError:
        return None


def remaining_inbound_qty(
    ordered_qty: ExactQuantity, received_qty: ExactQuantity
) -> ExactQuantity:
    """``RemainingInboundQty = ordered_qty - received_qty`` (``§2.6.2``).

    Exact finite base-10 subtraction on scaled integers: no ``Decimal`` context, no clamp,
    no absolute value and no coercion to ``0``.  A negative result is a data-quality
    condition handled by the caller as ``DATA_INCOMPLETE``.
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
    ordered_qty: ExactQuantity | None
    received_qty: ExactQuantity | None
    remaining_inbound_qty: ExactQuantity | None
    inbound_status: Any
    effective_arrival_date: Any
    status_eligible: bool | None
    effective_inbound_qty: ExactQuantity | None
    outcome: str | None = None
    notes: tuple[str, ...] = ()
    provenance: EvidenceReference | None = None
    #: Canonical findings that already describe this accepted record, re-published verbatim.
    inherited_issues: tuple[Issue, ...] = ()
    #: Findings this rule itself must raise under its registered design references -- here
    #: the ``CONSISTENCY`` / ``CONSISTENCY_CONFLICT`` finding ``§2.6.2`` / ``§4.4.47``
    #: require for ``received_qty > ordered_qty``.  No new category, reason or severity is
    #: introduced, so they are kept separate from the re-published upstream findings.
    rule_issues: tuple[Issue, ...] = ()

    @property
    def issues(self) -> tuple[Issue, ...]:
        """Every canonical finding relevant to this evaluation, deterministically ordered."""

        return _deduplicate_issues(self.inherited_issues + self.rule_issues)

    @property
    def data_incomplete(self) -> bool:
        return self.outcome == EFFECTIVE_INBOUND_DATA_INCOMPLETE

    @property
    def contributes(self) -> bool:
        """Whether this inbound adds supply at the target required date."""

        return (
            self.outcome is None
            and self.effective_inbound_qty is not None
            and self.effective_inbound_qty > ExactQuantity(0, 0)
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
            "rule_issues": [issue.to_dict() for issue in self.rule_issues],
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
    cumulative_effective_inbound: ExactQuantity | None
    outcome: str | None = None
    notes: tuple[str, ...] = ()
    #: Every upstream `BR-REQUIREMENT-001` calculation reference contributing to this
    #: target grain, in deterministic order.  The target is a **group**, never one
    #: arbitrarily chosen representative row.
    requirement_references: tuple[str, ...] = ()
    requirement_provenances: tuple[EvidenceReference, ...] = ()
    inherited_issues: tuple[Issue, ...] = ()
    #: Findings this rule itself raised for the inbound records evaluated against this
    #: target, one logical finding per ``location + category + reason``.
    rule_issues: tuple[Issue, ...] = ()

    @property
    def issues(self) -> tuple[Issue, ...]:
        """Every canonical finding relevant to this target, deterministically ordered."""

        return _deduplicate_issues(self.inherited_issues + self.rule_issues)

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
            "requirement_references": list(self.requirement_references),
            "evaluations": [item.to_dict() for item in self.evaluations],
            "inherited_issues": [issue.to_dict() for issue in self.inherited_issues],
            "rule_issues": [issue.to_dict() for issue in self.rule_issues],
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


def _quantity_text(value: ExactQuantity | None) -> str | None:
    """Render a canonical quantity exactly: plain base-10 digits, never an exponent."""

    if value is None:
        return None
    return value.text()


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

    A target grain is a **group** of every upstream requirement calculation row that states
    it.  There is no first-row-wins / last-row-wins / same-value-dedup representative: if any
    upstream row of that grain is ``DATA_INCOMPLETE``, the target is ``DATA_INCOMPLETE`` and
    no numeric cumulative supply is produced.
    """

    targets = _targets_from_requirements(requirements)
    inbounds = tuple(construction.inbound_records)

    outbound: list[EffectiveInboundTarget] = []
    for plant_id, material_code, required_date, rows in targets:
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
        cumulative: ExactQuantity | None = ExactQuantity(0, 0)
        notes: list[str] = []
        outcome: str | None = None

        unreliable_rows = [row for row in rows if row.data_incomplete]
        if not rows or unreliable_rows:
            cumulative = None
            outcome = EFFECTIVE_INBOUND_DATA_INCOMPLETE
            notes.append(
                "at least one upstream BR-REQUIREMENT-001 calculation for this target grain "
                "is DATA_INCOMPLETE, so the required-date evaluation context is not reliable "
                "and no numeric cumulative effective inbound supply is produced (§2.6.6)"
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
        rule_findings: list[Issue] = []
        for item in evaluations:
            inherited.extend(item.inherited_issues)
            rule_findings.extend(item.rule_issues)
        for row in rows:
            inherited.extend(row.inherited_issues)

        outbound.append(
            EffectiveInboundTarget(
                plant_id=plant_id,
                material_code=material_code,
                required_date=required_date,
                evaluations=evaluations,
                cumulative_effective_inbound=cumulative,
                outcome=outcome,
                notes=tuple(notes),
                requirement_references=tuple(
                    reference
                    for reference in (
                        row.bom_component_reference for row in rows
                    )
                    if reference is not None
                ),
                requirement_provenances=tuple(
                    provenance
                    for provenance in (row.loss_rate_provenance for row in rows)
                    if provenance is not None
                ),
                inherited_issues=_deduplicate_issues(inherited),
                rule_issues=_deduplicate_issues(rule_findings),
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


def _deduplicate_issues(issues: Iterable[Issue]) -> tuple[Issue, ...]:
    """Keep one logical finding per ``location + category + reason``.

    The same inbound evidence can be evaluated against many target required dates; an
    evidence-level defect must not be invented as N distinct defects just because it was
    reached N times.
    """

    unique: dict[tuple[str, str, str], Issue] = {}
    for issue in issues:
        unique.setdefault(
            (issue.location, issue.category, issue.reason), issue
        )
    return tuple(sorted(unique.values(), key=Issue.sort_key))


def _targets_from_requirements(
    requirements: RequirementCalculationResult,
) -> tuple[
    tuple[Any, Any, Any, tuple[RequirementCalculation, ...]], ...
]:
    """Group requirement rows into the registered targets.

    The grain is ``plant_id`` + component ``material_code`` + ``required_date``.  **Every**
    upstream row stating that grain belongs to the same target: no row is treated as a
    representative, and no first / last wins.  A row whose calculation is
    ``DATA_INCOMPLETE`` still states the grain, so it produces a ``DATA_INCOMPLETE`` target
    rather than a silently missing one.
    """

    grouped: dict[tuple[Any, Any, Any], list[RequirementCalculation]] = {}
    for calculation in requirements.calculations:
        key = (
            calculation.plant_id,
            calculation.component_material_code,
            calculation.required_date,
        )
        grouped.setdefault(key, []).append(calculation)

    return tuple(
        (key[0], key[1], key[2], tuple(grouped[key]))
        for key in sorted(grouped, key=lambda item: tuple(_sort_text(part) for part in item))
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

    ordered_qty = parse_non_negative_quantity(inbound.value_of("ordered_qty", ABSENT))
    received_qty = parse_non_negative_quantity(
        inbound.value_of("received_qty", ABSENT)
    )
    status_value = inbound.value_of("inbound_status", ABSENT)
    arrival_value = inbound.value_of("effective_arrival_date", ABSENT)
    inbound_material = inbound.value_of("material_code", ABSENT)
    inbound_plant = inbound.value_of("plant_id", ABSENT)

    def evaluation(
        *,
        remaining: ExactQuantity | None,
        status_eligible: bool | None,
        effective: ExactQuantity | None,
        outcome: str | None,
        notes: tuple[str, ...],
        issues: tuple[Issue, ...] = (),
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
            rule_issues=issues,
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
            effective=ExactQuantity(0, 0),
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
            effective=ExactQuantity(0, 0),
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
                "ordered_qty is missing, non-numeric or negative; it is not a registered "
                "canonical NON_NEGATIVE_QUANTITY, so no remaining quantity is produced "
                "and no default is applied (§2.6.2 / §4.2.6)",
            ),
        )
    if received_qty is None:
        return evaluation(
            remaining=None,
            status_eligible=None,
            effective=None,
            outcome=EFFECTIVE_INBOUND_DATA_INCOMPLETE,
            notes=(
                "received_qty is missing, non-numeric or negative; it is not a registered "
                "canonical NON_NEGATIVE_QUANTITY, so no remaining quantity is produced "
                "and no default is applied (§2.6.2 / §4.2.6)",
            ),
        )
    if received_qty > ordered_qty:
        # ``§2.6.2`` / ``§4.4.47``: never clamped, never coerced to 0, never interpreted.
        # ``§4.4.92`` registers the taxonomy for this cross-field defect.
        return evaluation(
            remaining=None,
            status_eligible=None,
            effective=None,
            outcome=EFFECTIVE_INBOUND_DATA_INCOMPLETE,
            notes=(
                f"received_qty {received_qty.text()} exceeds ordered_qty "
                f"{ordered_qty.text()}; the remaining quantity is not clamped, not replaced "
                "by 0 and not given a guessed business meaning (§2.6.2 / §4.4.47)"
            ),
            issues=(
                _over_receipt_issue(
                    inbound=inbound,
                    ordered_qty=ordered_qty,
                    received_qty=received_qty,
                ),
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
            effective=ExactQuantity(0, 0),
            outcome=None,
            notes=(
                "status is valid but ineligible for future supply; the record stays valid "
                "and contributes 0 (§2.6.3 / §4.4.89)",
            ),
        )
    if remaining <= ExactQuantity(0, 0):
        return evaluation(
            remaining=remaining,
            status_eligible=True,
            effective=ExactQuantity(0, 0),
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
            effective=ExactQuantity(0, 0),
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


def _over_receipt_issue(
    *,
    inbound: CanonicalObject,
    ordered_qty: ExactQuantity,
    received_qty: ExactQuantity,
) -> Issue:
    """The registered Data Quality Issue for ``received_qty > ordered_qty``.

    ``§2.6.2`` / ``§4.4.47`` require ``DATA_INCOMPLETE`` **plus** a Data Quality Issue, and
    ``§4.4.92`` already registers the taxonomy for this cross-field defect.  The existing
    :class:`~snapshot_loader.issues.Issue` shape is reused: no new category, reason,
    severity or error code is introduced.

    The finding describes the **inbound evidence**, not a target date, so the same record
    evaluated against several required dates yields one logical finding
    (deduplicated by location + category + reason).
    """

    reference = inbound.record_reference or ""
    parts = reference.split("|")
    artifact = parts[2] if len(parts) > 2 else ""
    ordinal = parts[3] if len(parts) > 3 else ""
    location = f"{artifact}[{ordinal}]" if artifact and ordinal else (artifact or reference)

    return Issue(
        location=location,
        detail=(
            f"received_qty {received_qty.text()} exceeds ordered_qty "
            f"{ordered_qty.text()}; the inbound record is internally inconsistent"
        ),
        category="CONSISTENCY",
        reason="CONSISTENCY_CONFLICT",
        layer=LAYER_2,
        affected_evidence=artifact or inbound.canonicalization_role,
        blast_radius=(
            "affected inbound evidence / effective-inbound target only (no package "
            "rejection)"
        ),
        design_reference="§2.6.2 / §4.4.47 / §4.4.92",
        consequence_context=(
            "the affected inbound and its effective-inbound target are DATA_INCOMPLETE; no "
            "clamp is applied and the package disposition is unchanged"
        ),
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
    "ExactQuantity",
    "compute_effective_inbound",
    "parse_exact_quantity",
    "parse_non_negative_quantity",
    "remaining_inbound_qty",
]
