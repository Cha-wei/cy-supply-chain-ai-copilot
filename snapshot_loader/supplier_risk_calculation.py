"""``BR-SUPPLIER-RISK-001`` Supplier Risk Evidence calculation (first tranche).

The **consumption** side of the Supplier Risk runtime contract: it turns one
:class:`~snapshot_loader.supplier_risk_input.SupplierRiskInputResult` into the deterministic, explainable
``Risk Evidence`` the rule registers (``poc-design-v0.2.md`` §2.7.4 -- §2.7.16):

* ``DaysUntilNeed = RecommendationNeedDate - AnalysisDate`` -- **exact** calendar-date subtraction, no
  clock, no timezone, no clamp, no guess (``§2.7.4`` ／ ``§4.3.22`` C-3);
* ``LeadTimeRisk``: ``StandardLeadTimeDays > DaysUntilNeed`` -> ``HIGH``, otherwise ``LOW``; this version
  defines **no** ``MEDIUM`` and adds no buffer ／ grace period (``§2.7.5`` ／ ``§4.4.37``);
* ``DeliveryRisk`` ／ ``QualityRisk`` from the registered Human-approved ``SIMULATED`` thresholds
  ``95 ／ 90`` and ``98 ／ 95`` (``§2.7.6`` ／ ``§2.7.7`` ／ ``§2.7.19``);
* ``OverallSupplierRisk = max severity`` of the three reliable dimensions, ``LOW < MEDIUM < HIGH`` -- never
  a weighted score -- and ``DATA_INCOMPLETE`` as soon as one required dimension is unreliable, while the
  reliable dimensions stay displayed (``§2.7.8`` ／ ``§2.7.9``).

Input closure (Issue #170)
--------------------------

:func:`compute_supplier_risk` consumes **only** a ``SupplierRiskInputResult``: its evaluation contexts,
its request-bounded fail-closed evidence outcomes and its ``AnalysisRunContext``.  It never re-reads the
``CanonicalConstructionReport``, the ``AcceptedPackage`` ／ raw evidence, the shortage result, the
procurement internals or the filesystem, and it takes no caller-supplied date, threshold, identity or
outcome.  The ``F3-RB1`` Analysis Run ／ package binding is verified **inside** the ``A′`` seam before any
evidence is consumed (``§4.3.31`` E ／ ``§4.4.103``); this rule has exactly one upstream result, so it
performs no cross-result binding and reports no second run identity.

Card universe
-------------

Exactly one normal :class:`SupplierRiskEvidenceCard` per ``input_result.evaluation_contexts`` entry: the
evaluation key is ``plant_id`` + ``material_code`` + ``supplier_id`` and the business grain stays
``supplier_id`` + ``material_code`` (``§2.7.2``), so two Plants demanded of one supplier ／ material form
two independent cards and never share a ``RecommendationNeedDate``.  The seam only forms a context for a
request-bounded, eligible relationship with reliably resolved ``Supplier`` ／ ``Material`` identity and a
reliably keyed pair grain, so capability-unavailable, explicitly ``ineligible``, no-request ／ valid
absence, ``ROOT_RELATIONSHIP_ABSENT``, unkeyable-pair and already-fail-closed cases produce **no** normal
card here by construction.

Fail-closed propagation
-----------------------

``input_result.evidence_outcomes`` is propagated **verbatim** as
:attr:`SupplierRiskResult.fail_closed_outcomes`: those rows already state
``Risk Evidence Status = DATA_INCOMPLETE`` under the registered taxonomy (``§2.7.16`` ／ ``§2.7.27``), so no
risk dimension is recomputed for them and their identity findings are not re-scoped.

Field findings
--------------

The seam guarantees the *readiness* of the consumed evidence but does not carry every Layer-2 field
finding.  This rule therefore states its own narrow, failure-isolated findings with the **existing**
taxonomy -- ``FIELD_VALUE`` ／ ``MISSING`` ／ ``INVALID_TYPE`` ／ ``OUT_OF_DEFINED_RANGE`` (``§4.4.80`` #3 ／
``§4.4.81`` #3 -- #6 ／ ``§4.4.86``) -- built from the real accepted values and provenance of the consumed
context.  ``DATA_INCOMPLETE`` stays a **business outcome** and is never used as a reason (``§4.4.85``), no
evidence reference is fabricated, and no new Category ／ Reason ／ enum ／ status is created.

Strict scope
------------

Deterministic calculation only.  No supplier ranking ／ selection ／ winner recommendation, no procurement
quantity ／ ``ApplicableMOQ`` change, no order split, no Procurement Request Draft ／ HITL, no LLM
classification, no real ERP ／ SRM mapping, no real period ／ freshness policy, no database ／ persistence ／
service, no new canonical entity ／ field ／ grain and no new Validation Category ／ Reason; the registered
thresholds, the ``PerformancePeriod`` policy (still ``DESIGN PENDING``, ``§2.7.23``) and ``ADR-001`` are
unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as _date
import re
from typing import Any, Iterable, Sequence

from .canonical_objects import AnalysisRunContext, EvidenceReference
from .constants import (
    CATEGORY_FIELD_VALUE,
    DATE_PATTERN,
    LAYER_2,
    REASON_INVALID_TYPE,
    REASON_MISSING,
    REASON_OUT_OF_DEFINED_RANGE,
)
from .exact_quantity import ExactQuantity, parse_exact_quantity
from .issues import Issue
from .procurement_recommendation import PROCUREMENT_RECOMMENDATION_RULE_ID
from .requirement_calculation import OUTCOME_DATA_INCOMPLETE
from .supplier_risk_input import (
    SupplierPerformanceObservation,
    SupplierRelationshipEligibility,
    SupplierRiskEvaluationContext,
    SupplierRiskEvidenceOutcome,
    SupplierRiskInputResult,
)

# --- registered risk vocabulary ----------------------------------------------------
#
# These are the **existing** canonical risk status literals of ``BR-SUPPLIER-RISK-001``
# (``§2.7.5`` -- ``§2.7.8`` ／ ``§4.4.37`` ／ ``data-dictionary`` §4.2.14): this module creates no new
# status, level, enum or vocabulary, it only names the registered ones.
RISK_LOW: str = "LOW"
RISK_MEDIUM: str = "MEDIUM"
RISK_HIGH: str = "HIGH"
#: The existing business outcome literal (``§4.4.85``: a business outcome, never an issue reason).
RISK_DATA_INCOMPLETE: str = OUTCOME_DATA_INCOMPLETE

#: The three required dimensions of ``§2.7.9``, in deterministic order.
REQUIRED_RISK_DIMENSIONS: tuple[str, ...] = (
    "LeadTimeRisk",
    "DeliveryRisk",
    "QualityRisk",
)

#: ``§2.7.8`` severity order -- ``LOW < MEDIUM < HIGH``; ``DATA_INCOMPLETE`` is deliberately absent
#: because an unreliable dimension is never ranked against a reliable one.
SEVERITY_ORDER: dict[str, int] = {RISK_LOW: 0, RISK_MEDIUM: 1, RISK_HIGH: 2}

#: Human-approved ``SIMULATED`` POC thresholds.  They are fixed module constants: not configurable, not
#: caller-injectable and not extensible without a Human-approved Business Rule change (``§2.7.19``).
DELIVERY_LOW_MINIMUM: ExactQuantity = ExactQuantity(95, 0)
DELIVERY_MEDIUM_MINIMUM: ExactQuantity = ExactQuantity(90, 0)
QUALITY_LOW_MINIMUM: ExactQuantity = ExactQuantity(98, 0)
QUALITY_MEDIUM_MINIMUM: ExactQuantity = ExactQuantity(95, 0)
PERCENTAGE_MINIMUM: ExactQuantity = ExactQuantity(0, 0)
PERCENTAGE_MAXIMUM: ExactQuantity = ExactQuantity(100, 0)
ZERO_QUANTITY: ExactQuantity = ExactQuantity(0, 0)

#: Runtime stage identity of this rule (trace label only -- not a business rule id, field, enum or status).
SUPPLIER_RISK_STAGE: str = "SUPPLIER_RISK"

#: The scope note every card carries: the registered decision-support boundary of this rule.
_DECISION_SUPPORT_NOTE: str = (
    "Risk Evidence is decision support and a read-only fact statement: it never ranks, selects or "
    "recommends a supplier, never enters the procurement quantity or ApplicableMOQ, and states no fact "
    "beyond the consumed accepted evidence (§2.7.1 / §2.7.12 / §2.7.14 / §2.7.15)"
)

#: The registered property names read from the single applicable ``Supplier Performance`` observation.
LEAD_TIME_PROPERTY: str = "standard_lead_time_days"
DELIVERY_PROPERTY: str = "DeliveryPerformance"
QUALITY_PROPERTY: str = "QualityPerformance"
PERIOD_PROPERTY: str = "PerformancePeriod"

_DATE_RE = re.compile(rf"^{DATE_PATTERN}$")


# --- helpers -----------------------------------------------------------------------


def _as_date(value: Any) -> _date | None:
    """Validate the canonical ``DATE`` representation (``§4.3.22`` C-3) and return the exact date.

    Only the registered ``YYYY-MM-DD`` form that denotes a real calendar date is accepted; nothing is
    repaired, defaulted or read from the system clock.  ``None`` means "missing or invalid", which
    ``§2.7.4`` maps to ``LeadTimeRisk = DATA_INCOMPLETE``.
    """

    if not isinstance(value, str) or not _DATE_RE.match(value):
        return None
    try:
        return _date.fromisoformat(value)
    except ValueError:
        return None


@dataclass(frozen=True, slots=True)
class _FieldReading:
    """One accepted field value together with its exact reading and registered defect reason.

    ``defect`` is ``None`` when the value is a registered, in-range representation; otherwise it is one of
    the inherited ``FIELD_VALUE`` reasons (``§4.4.81`` #3 -- #6), so the caller never invents a taxonomy.
    """

    value: Any
    quantity: ExactQuantity | None
    defect: str | None


def _read_quantity(
    value: Any,
    *,
    maximum: ExactQuantity | None,
) -> _FieldReading:
    """Read one canonical quantity ／ percentage exactly, distinguishing missing from invalid.

    ``MISSING`` covers an absent or JSON ``null`` value (``§4.3.22`` C-2), ``INVALID_TYPE`` a present value
    that is not a registered base-10 decimal string (``C-5``: no binary floating point, no exponent), and
    ``OUT_OF_DEFINED_RANGE`` a registered decimal outside the field's own registered bound.  No value is
    repaired, clamped, defaulted or retyped, and no quantity arithmetic happens in ``Decimal``.
    """

    if value is None:
        return _FieldReading(value, None, REASON_MISSING)
    if not isinstance(value, str):
        return _FieldReading(value, None, REASON_INVALID_TYPE)
    parsed = parse_exact_quantity(value)
    if parsed is None:
        return _FieldReading(value, None, REASON_INVALID_TYPE)
    if parsed < ZERO_QUANTITY:
        return _FieldReading(value, None, REASON_OUT_OF_DEFINED_RANGE)
    if maximum is not None and parsed > maximum:
        return _FieldReading(value, None, REASON_OUT_OF_DEFINED_RANGE)
    return _FieldReading(value, parsed, None)


def _read_period(value: Any) -> _FieldReading:
    """Read the ``PerformancePeriod`` readiness boundary of the applicable observation.

    The first tranche only requires the measurement period to be **present as an exact, non-empty JSON
    string** (``§4.2.8`` ``REQUIRED`` ／ ``§4.3.22`` C-10): the real period vocabulary ／ window length and
    the freshness policy stay ``DESIGN PENDING`` (``§2.7.23``), so no format, length or age rule is added
    here.  ``PerformanceUpdatedAt`` is never consulted as a substitute (``§4.4.64``).
    """

    if value is None:
        return _FieldReading(value, None, REASON_MISSING)
    if not isinstance(value, str) or value == "":
        return _FieldReading(value, None, REASON_INVALID_TYPE)
    return _FieldReading(value, None, None)


def _field_issue(
    *,
    location: str,
    property_name: str,
    defect: str,
    detail: str,
    affected_evidence: str,
    consequence: str,
    design_reference: str,
) -> Issue:
    """One narrow ``FIELD_VALUE`` finding of a single evaluation request (never fabricated)."""

    return Issue(
        location=f"{location}.{property_name}",
        detail=detail,
        category=CATEGORY_FIELD_VALUE,
        reason=defect,
        layer=LAYER_2,
        affected_evidence=affected_evidence,
        blast_radius=(
            "the Supplier Risk evidence card of this exact plant_id + material_code + supplier_id "
            "evaluation request only"
        ),
        design_reference=design_reference,
        consequence_context=consequence,
    )


def _deduplicate_issues(issues: Iterable[Issue]) -> tuple[Issue, ...]:
    """Deterministic, duplicate-free issue order (same key the seam uses)."""

    seen: dict[tuple[str, str, str], Issue] = {}
    for issue in issues:
        seen.setdefault((issue.location, issue.category, issue.reason), issue)
    return tuple(sorted(seen.values(), key=Issue.sort_key))


def _sort_text(value: Any) -> str:
    return "" if value is None else str(value)


def _severity_max(risks: Sequence[str]) -> str | None:
    """``max severity`` of the reliable dimensions, or ``None`` when any of them is unreliable."""

    if any(risk not in SEVERITY_ORDER for risk in risks):
        return None
    best = RISK_LOW
    for risk in risks:
        if SEVERITY_ORDER[risk] > SEVERITY_ORDER[best]:
            best = risk
    return best


# --- result representation ---------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SupplierRiskEvidenceCard:
    """One normal Supplier Risk Evidence Card of one evaluation request (``§2.7.11``).

    The evaluation key is ``plant_id`` + ``material_code`` + ``supplier_id``; the business grain stays
    ``supplier_id`` + ``material_code`` (``§2.7.2``).  ``performance`` is the **one** applicable
    :class:`SupplierPerformanceObservation` the approved Option A boundary determined, so the five
    registered properties exposed below all come from that single observation -- never spliced across
    records or periods (``§2.7.26`` A ／ ``C``).

    ``days_until_need`` is the exact integer day count of ``RecommendationNeedDate - AnalysisDate``, or
    ``None`` when either date is missing ／ invalid; it is serialized as the registered exact base-10
    decimal text (``§4.3.25`` C-5) and is **never** clamped, so a negative value stays visible.

    ``status`` is the existing ``DATA_INCOMPLETE`` business literal when ``overall_supplier_risk`` is
    ``DATA_INCOMPLETE`` and ``None`` when the card is complete; completeness is also stated explicitly by
    :attr:`evidence_complete`, because the registered vocabulary has no "complete" status literal and this
    rule creates none.

    ``upstream_issues`` carries the findings of the consumed context verbatim -- eligibility, exact
    identity, need-date linkage and Option A applicability findings the seam already published -- and
    ``rule_issues`` carries only this rule's own narrow field findings.  Every reference is the upstream
    accepted evidence's own reference; nothing is fabricated.
    """

    analysis_run_id: str
    plant_id: Any
    material_code: Any
    supplier_id: Any
    analysis_date: Any
    recommendation_need_date: Any
    days_until_need: int | None
    lead_time_risk: str
    delivery_risk: str
    quality_risk: str
    overall_supplier_risk: str
    eligibility: SupplierRelationshipEligibility
    performance: SupplierPerformanceObservation | None = None
    upstream_issues: tuple[Issue, ...] = ()
    rule_issues: tuple[Issue, ...] = ()
    notes: tuple[str, ...] = ()

    # --- identity -------------------------------------------------------------------
    @property
    def grain(self) -> tuple[Any, Any]:
        """The business grain of the card (``supplier_id`` + ``material_code``, ``§2.7.2``)."""

        return (self.supplier_id, self.material_code)

    @property
    def evaluation_context(self) -> tuple[Any, Any, Any]:
        """The evaluation key ``plant_id`` + ``material_code`` + ``supplier_id``."""

        return (self.plant_id, self.material_code, self.supplier_id)

    # --- consumed performance surface (one coherent unit) ---------------------------
    @property
    def standard_lead_time_days(self) -> Any:
        return None if self.performance is None else self.performance.standard_lead_time_days

    @property
    def performance_period(self) -> Any:
        return None if self.performance is None else self.performance.performance_period

    @property
    def performance_updated_at(self) -> Any:
        return None if self.performance is None else self.performance.performance_updated_at

    @property
    def delivery_performance(self) -> Any:
        return None if self.performance is None else self.performance.delivery_performance

    @property
    def quality_performance(self) -> Any:
        return None if self.performance is None else self.performance.quality_performance

    @property
    def performance_evidence_reference(self) -> EvidenceReference | None:
        """The applicable observation's own package-scoped provenance, or ``None`` (never synthesised)."""

        return None if self.performance is None else self.performance.evidence_reference

    @property
    def relationship_reference(self) -> str | None:
        """The relationship evidence record reference of the card, or ``None`` (never fabricated)."""

        return self.eligibility.relationship_reference

    # --- derived ---------------------------------------------------------------------
    @property
    def days_until_need_text(self) -> str | None:
        """``DaysUntilNeed`` as the registered exact decimal text, or ``None``."""

        if self.days_until_need is None:
            return None
        return ExactQuantity(self.days_until_need, 0).text()

    @property
    def dimensions(self) -> tuple[str, ...]:
        """The three required dimension outcomes, in deterministic order."""

        return (self.lead_time_risk, self.delivery_risk, self.quality_risk)

    @property
    def reliable_dimensions(self) -> tuple[tuple[str, str], ...]:
        """The ``(dimension, level)`` pairs that are reliably determined (kept visible, ``§2.7.9``)."""

        return tuple(
            (name, risk)
            for name, risk in zip(REQUIRED_RISK_DIMENSIONS, self.dimensions)
            if risk in SEVERITY_ORDER
        )

    @property
    def evidence_complete(self) -> bool:
        """Whether all three required dimensions are reliably determined (``§2.7.9``)."""

        return all(risk in SEVERITY_ORDER for risk in self.dimensions)

    @property
    def status(self) -> str | None:
        """``DATA_INCOMPLETE`` when the card is incomplete, else ``None`` (no "complete" literal exists)."""

        return None if self.evidence_complete else RISK_DATA_INCOMPLETE

    @property
    def issues(self) -> tuple[Issue, ...]:
        return _deduplicate_issues(self.upstream_issues + self.rule_issues)

    def to_dict(self) -> dict[str, object]:
        return {
            "stage": SUPPLIER_RISK_STAGE,
            "supplier_id": self.supplier_id,
            "material_code": self.material_code,
            "plant_id": self.plant_id,
            "evaluation_context": list(self.evaluation_context),
            "grain": list(self.grain),
            "Analysis Run": self.analysis_run_id,
            "AnalysisDate": self.analysis_date,
            "RecommendationNeedDate": self.recommendation_need_date,
            "DaysUntilNeed": self.days_until_need_text,
            "StandardLeadTimeDays": self.standard_lead_time_days,
            "LeadTimeRisk": self.lead_time_risk,
            "PerformancePeriod": self.performance_period,
            "PerformanceUpdatedAt": self.performance_updated_at,
            "DeliveryPerformance": self.delivery_performance,
            "DeliveryRisk": self.delivery_risk,
            "QualityPerformance": self.quality_performance,
            "QualityRisk": self.quality_risk,
            "OverallSupplierRisk": self.overall_supplier_risk,
            "status": self.status,
            "evidence_complete": self.evidence_complete,
            "reliable_dimensions": [
                {"dimension": name, "risk": risk} for name, risk in self.reliable_dimensions
            ],
            "eligibility": self.eligibility.to_dict(),
            "performance_evidence_reference": (
                None
                if self.performance_evidence_reference is None
                else _evidence_payload(self.performance_evidence_reference)
            ),
            "relationship_reference": self.relationship_reference,
            "notes": list(self.notes),
            "upstream_issues": [issue.to_dict() for issue in self.upstream_issues],
            "rule_issues": [issue.to_dict() for issue in self.rule_issues],
        }


@dataclass(frozen=True, slots=True)
class SupplierRiskResult:
    """Deterministic read-only result of ``BR-SUPPLIER-RISK-001`` for one analysis run.

    ``cards`` holds exactly one normal :class:`SupplierRiskEvidenceCard` per consumed evaluation context,
    ordered by ``plant_id`` + ``material_code`` + ``supplier_id``.  ``fail_closed_outcomes`` holds the
    consumed seam outcomes **verbatim**: they already express
    ``Risk Evidence Status = DATA_INCOMPLETE`` for an unresolved relationship ／ exact identity, so this
    rule propagates them unchanged and computes no dimension for them (``§2.7.27`` C ／ F).

    ``capability_available`` ／ ``capability_issues`` ／ ``valid_absence_grains`` are propagated verbatim
    from the consumed input result so a consumer can distinguish capability-unavailable from a business
    outcome and valid absence from a missing request without re-reading anything upstream.

    ``analysis_run`` is the consumed ``AnalysisRunContext``: the single Analysis Run ／ package binding
    authority, so every card and fail-closed row belongs to exactly that run.
    """

    analysis_run: AnalysisRunContext
    cards: tuple[SupplierRiskEvidenceCard, ...] = ()
    fail_closed_outcomes: tuple[SupplierRiskEvidenceOutcome, ...] = ()
    capability_available: bool = True
    capability_issues: tuple[Issue, ...] = ()
    valid_absence_grains: tuple[tuple[Any, Any], ...] = ()
    notes: tuple[str, ...] = ()

    @property
    def analysis_date(self) -> Any:
        return self.analysis_run.analysis_date

    @property
    def analysis_run_id(self) -> str:
        return self.analysis_run.analysis_run_id

    @property
    def issues(self) -> tuple[Issue, ...]:
        """Every finding of this rule, deterministically ordered and duplicate-free."""

        return _deduplicate_issues(
            self.capability_issues
            + tuple(issue for card in self.cards for issue in card.issues)
            + tuple(
                issue for outcome in self.fail_closed_outcomes for issue in outcome.issues
            )
        )

    @property
    def complete_cards(self) -> tuple[SupplierRiskEvidenceCard, ...]:
        return tuple(card for card in self.cards if card.evidence_complete)

    @property
    def incomplete_cards(self) -> tuple[SupplierRiskEvidenceCard, ...]:
        return tuple(card for card in self.cards if not card.evidence_complete)

    def cards_for(
        self, supplier_id: Any, material_code: Any
    ) -> tuple[SupplierRiskEvidenceCard, ...]:
        """Every card of one exact supplier + material, in deterministic order."""

        return tuple(
            card
            for card in self.cards
            if card.supplier_id == supplier_id and card.material_code == material_code
        )

    def card_for(
        self, plant_id: Any, supplier_id: Any, material_code: Any
    ) -> SupplierRiskEvidenceCard | None:
        """The card of one exact plant + supplier + material, or ``None``."""

        for card in self.cards:
            if (
                card.plant_id == plant_id
                and card.supplier_id == supplier_id
                and card.material_code == material_code
            ):
                return card
        return None

    def fail_closed_for(
        self, supplier_id: Any, material_code: Any
    ) -> tuple[SupplierRiskEvidenceOutcome, ...]:
        """Every propagated fail-closed outcome of one exact supplier + material."""

        return tuple(
            outcome
            for outcome in self.fail_closed_outcomes
            if outcome.supplier_id == supplier_id and outcome.material_code == material_code
        )

    def is_valid_absence(self, plant_id: Any, material_code: Any) -> bool:
        """Whether the family is a reliable ``NORMAL`` ／ ``BUFFER_BREACH`` valid absence (no card)."""

        return (plant_id, material_code) in self.valid_absence_grains

    def to_dict(self) -> dict[str, object]:
        return {
            "stage": SUPPLIER_RISK_STAGE,
            "analysis_run": {
                "analysis_run_id": self.analysis_run.analysis_run_id,
                "AnalysisDate": self.analysis_run.analysis_date,
                "snapshot_package_identity": self.analysis_run.snapshot_package_identity,
                "accepted_content_view_digest": (
                    self.analysis_run.accepted_content_view_digest
                ),
            },
            "capability_available": self.capability_available,
            "cards": [card.to_dict() for card in self.cards],
            "fail_closed_outcomes": [
                outcome.to_dict() for outcome in self.fail_closed_outcomes
            ],
            "capability_issues": [issue.to_dict() for issue in self.capability_issues],
            "valid_absence_grains": [
                {"plant_id": plant_id, "material_code": material_code}
                for plant_id, material_code in self.valid_absence_grains
            ],
            "notes": list(self.notes),
        }


def _evidence_payload(value: EvidenceReference) -> dict[str, object]:
    return {
        "snapshot_package_identity": value.snapshot_package_identity,
        "logical_dataset_role": value.logical_dataset_role,
        "artifact": value.artifact,
        "record_ordinal": value.record_ordinal,
        "logical_observation": value.logical_observation,
        "stable_source_evidence_locators": list(value.stable_source_evidence_locators),
        "mapping_resolution_basis": value.mapping_resolution_basis,
    }


# --- calculation -------------------------------------------------------------------


def compute_supplier_risk(input_result: SupplierRiskInputResult) -> SupplierRiskResult:
    """Compute the registered Supplier Risk Evidence of one consumed ``A′`` input result.

    Only ``input_result`` is read: every card comes from ``input_result.evaluation_contexts`` and every
    fail-closed row is propagated from ``input_result.evidence_outcomes`` (``§2.7.27``).  No other result,
    construction, raw artifact or file is consulted, no date is read from the system clock, and no
    threshold, identity or outcome can be injected by the caller (``§2.7.17`` ／ ``§2.7.18`` ／ ``ADR-001``).
    The returned result is frozen, deterministically ordered and stably serializable: identical inputs
    produce an identical payload.
    """

    cards = tuple(
        sorted(
            (_evaluate_context(input_result, context) for context in input_result.evaluation_contexts),
            key=_card_key,
        )
    )
    return SupplierRiskResult(
        analysis_run=input_result.analysis_run,
        cards=cards,
        fail_closed_outcomes=tuple(input_result.evidence_outcomes),
        capability_available=input_result.capability_available,
        capability_issues=tuple(input_result.capability_issues),
        valid_absence_grains=tuple(input_result.valid_absence_grains),
        notes=(
            "the rule computes the registered deterministic Supplier Risk Evidence of the consumed "
            "evaluation requests only: DaysUntilNeed is exact calendar-date arithmetic, LeadTimeRisk ／ "
            "DeliveryRisk ／ QualityRisk use the registered SIMULATED thresholds, OverallSupplierRisk is "
            "the max severity of the reliable dimensions or DATA_INCOMPLETE; it performs no ranking ／ "
            "selection ／ recommendation, changes no procurement quantity and applies no LLM "
            "(§2.7.1 / §2.7.5 / §2.7.6 / §2.7.7 / §2.7.8 / §2.7.9)",
        ),
    )


def _evaluate_context(
    input_result: SupplierRiskInputResult, context: SupplierRiskEvaluationContext
) -> SupplierRiskEvidenceCard:
    """Compute the one normal card of one consumed evaluation context (no risk value is invented)."""

    location = (
        "supplier_risk["
        f"{_sort_text(context.plant_id)}/{_sort_text(context.material_code)}/"
        f"{_sort_text(context.supplier_id)}]"
    )
    rule_issues: list[Issue] = []

    # --- dates ----------------------------------------------------------------------
    analysis_date = input_result.analysis_run.analysis_date
    analysis = _as_date(analysis_date)
    if analysis is None:
        rule_issues.append(
            _field_issue(
                location=location,
                property_name="AnalysisDate",
                defect=REASON_MISSING if analysis_date is None else REASON_INVALID_TYPE,
                detail=(
                    "the consumed Analysis Run context states no valid C-3 DATE AnalysisDate "
                    f"({analysis_date!r}), so the exact number of days until the requirement cannot be "
                    "determined and LeadTimeRisk fails closed; no date is read from the system clock and "
                    "no default is applied (§2.7.4 / §4.4.27 / §4.3.22 C-3)"
                ),
                affected_evidence="Analysis Run",
                consequence=(
                    "DaysUntilNeed cannot be formed for this request and LeadTimeRisk = DATA_INCOMPLETE; "
                    "the reliable performance-derived dimensions are unaffected"
                ),
                design_reference="§2.7.4 / §2.7.16 / §4.4.27 / §4.3.22 C-3 / §4.4.85",
            )
        )

    need_date_value = context.recommendation_need_date
    need_date = _as_date(need_date_value)
    if need_date_value is not None and need_date is None:
        # A present but non-C-3 value is a form defect the seam does not decide; a genuinely unresolved
        # date already carries the seam's own registered need-date ／ linkage finding.
        rule_issues.append(
            _field_issue(
                location=location,
                property_name="RecommendationNeedDate",
                defect=REASON_INVALID_TYPE,
                detail=(
                    "the consumed evaluation context states a RecommendationNeedDate "
                    f"({need_date_value!r}) that is not a valid C-3 DATE, so the exact number of days "
                    "until the requirement cannot be determined and LeadTimeRisk fails closed; the value "
                    "is neither repaired nor replaced (§2.7.4 / §4.4.65 / §4.3.22 C-3)"
                ),
                affected_evidence=PROCUREMENT_RECOMMENDATION_RULE_ID,
                consequence=(
                    "DaysUntilNeed cannot be formed for this request and LeadTimeRisk = DATA_INCOMPLETE; "
                    "the reliable performance-derived dimensions are unaffected"
                ),
                design_reference="§2.7.4 / §2.7.16 / §4.4.65 / §4.3.22 C-3 / §4.4.85",
            )
        )

    days_until_need: int | None = None
    if analysis is not None and need_date is not None:
        days_until_need = (need_date - analysis).days
        if days_until_need < 0:
            rule_issues.append(
                _field_issue(
                    location=location,
                    property_name="DaysUntilNeed",
                    defect=REASON_OUT_OF_DEFINED_RANGE,
                    detail=(
                        f"the exact DaysUntilNeed of this request is {days_until_need} "
                        f"(RecommendationNeedDate {need_date_value!r} precedes AnalysisDate "
                        f"{analysis_date!r}), which violates the registered requirement "
                        "DaysUntilNeed >= 0, so LeadTimeRisk fails closed; the exact negative value is "
                        "reported as-is and is never clamped to 0 (§2.7.4 / §2.7.16)"
                    ),
                    affected_evidence=PROCUREMENT_RECOMMENDATION_RULE_ID,
                    consequence=(
                        "LeadTimeRisk = DATA_INCOMPLETE for this request while the reliable "
                        "performance-derived dimensions remain displayed"
                    ),
                    design_reference="§2.7.4 / §2.7.16 / §4.4.85",
                )
            )

    # --- the single applicable performance observation -------------------------------
    observation = context.applicable_performance
    lead_time_reading = _FieldReading(None, None, REASON_MISSING)
    delivery_reading = _FieldReading(None, None, REASON_MISSING)
    quality_reading = _FieldReading(None, None, REASON_MISSING)
    period_reading = _FieldReading(None, None, REASON_MISSING)
    if observation is not None:
        lead_time_reading = _read_quantity(
            observation.standard_lead_time_days, maximum=None
        )
        delivery_reading = _read_quantity(
            observation.delivery_performance, maximum=PERCENTAGE_MAXIMUM
        )
        quality_reading = _read_quantity(
            observation.quality_performance, maximum=PERCENTAGE_MAXIMUM
        )
        period_reading = _read_period(observation.performance_period)

    # --- LeadTimeRisk ---------------------------------------------------------------
    if observation is None:
        lead_time_risk = RISK_DATA_INCOMPLETE
    elif days_until_need is None or days_until_need < 0:
        lead_time_risk = RISK_DATA_INCOMPLETE
    elif lead_time_reading.quantity is None:
        lead_time_risk = RISK_DATA_INCOMPLETE
        rule_issues.append(
            _field_issue(
                location=location,
                property_name=LEAD_TIME_PROPERTY,
                defect=lead_time_reading.defect or REASON_MISSING,
                detail=(
                    "the applicable Supplier Performance observation states no usable "
                    f"standard_lead_time_days ({lead_time_reading.value!r}), so the Lead Time "
                    "Feasibility comparison cannot be performed and LeadTimeRisk fails closed; the "
                    "value is never defaulted to 0 and never clamped (§2.7.16 / §4.4.34 / §4.2.13)"
                ),
                affected_evidence=observation.record_reference,
                consequence=(
                    "LeadTimeRisk = DATA_INCOMPLETE for this request while the reliable "
                    "performance-derived dimensions remain displayed"
                ),
                design_reference="§2.7.3 / §2.7.5 / §2.7.16 / §4.4.34 / §4.2.13",
            )
        )
    else:
        lead_time_exact = lead_time_reading.quantity
        assert lead_time_exact is not None
        if lead_time_exact > ExactQuantity(days_until_need, 0):
            lead_time_risk = RISK_HIGH
        else:
            lead_time_risk = RISK_LOW

    # --- DeliveryRisk / QualityRisk -------------------------------------------------
    #
    # The registered ``§2.7.16`` row is stated once for both period-dependent dimensions, so the period
    # finding is emitted once per card and names both affected dimensions rather than being duplicated.
    period_ok = True
    if observation is not None and period_reading.defect is not None:
        period_ok = False
        rule_issues.append(
            _field_issue(
                location=location,
                property_name=PERIOD_PROPERTY,
                defect=period_reading.defect,
                detail=(
                    "the applicable Supplier Performance observation states no reliably identified "
                    f"PerformancePeriod ({period_reading.value!r}), so the DeliveryRisk and QualityRisk "
                    "evidence of this request is not complete and both fail closed; PerformanceUpdatedAt "
                    "is never used as a substitute and no period vocabulary, window length or freshness "
                    "rule is invented (§2.7.16 / §2.7.23 / §4.4.34 / §4.4.64)"
                ),
                affected_evidence=observation.record_reference,
                consequence=(
                    "DeliveryRisk and QualityRisk = DATA_INCOMPLETE for this request, while LeadTimeRisk "
                    "is still computed from its own inputs (§2.7.16 period row)"
                ),
                design_reference="§2.7.16 / §2.7.23 / §4.4.34 / §4.4.64",
            )
        )

    delivery_risk = _performance_dimension_risk(
        observation=observation,
        reading=delivery_reading,
        period_ok=period_ok,
        property_name=DELIVERY_PROPERTY,
        dimension="DeliveryRisk",
        low_minimum=DELIVERY_LOW_MINIMUM,
        medium_minimum=DELIVERY_MEDIUM_MINIMUM,
        location=location,
        rule_issues=rule_issues,
    )
    quality_risk = _performance_dimension_risk(
        observation=observation,
        reading=quality_reading,
        period_ok=period_ok,
        property_name=QUALITY_PROPERTY,
        dimension="QualityRisk",
        low_minimum=QUALITY_LOW_MINIMUM,
        medium_minimum=QUALITY_MEDIUM_MINIMUM,
        location=location,
        rule_issues=rule_issues,
    )

    # --- OverallSupplierRisk --------------------------------------------------------
    overall = _severity_max((lead_time_risk, delivery_risk, quality_risk))
    overall_supplier_risk = RISK_DATA_INCOMPLETE if overall is None else overall
    if overall is None:
        notes = (
            "at least one required dimension is unreliable, so OverallSupplierRisk = DATA_INCOMPLETE "
            "while every reliably determined dimension stays displayed; no dimension is defaulted and "
            "no value is dropped (§2.7.9)",
            _DECISION_SUPPORT_NOTE,
        )
    else:
        notes = (
            "all three required dimensions are reliably determined, so OverallSupplierRisk is their max "
            "severity (LOW < MEDIUM < HIGH) and no weighted score is applied (§2.7.8 / §2.7.9)",
            _DECISION_SUPPORT_NOTE,
        )

    return SupplierRiskEvidenceCard(
        analysis_run_id=input_result.analysis_run.analysis_run_id,
        plant_id=context.plant_id,
        material_code=context.material_code,
        supplier_id=context.supplier_id,
        analysis_date=analysis_date,
        recommendation_need_date=need_date_value,
        days_until_need=days_until_need,
        lead_time_risk=lead_time_risk,
        delivery_risk=delivery_risk,
        quality_risk=quality_risk,
        overall_supplier_risk=overall_supplier_risk,
        eligibility=context.eligibility,
        performance=observation,
        upstream_issues=context.issues,
        rule_issues=_deduplicate_issues(rule_issues),
        notes=notes,
    )


def _performance_dimension_risk(
    *,
    observation: SupplierPerformanceObservation | None,
    reading: _FieldReading,
    period_ok: bool,
    property_name: str,
    dimension: str,
    low_minimum: ExactQuantity,
    medium_minimum: ExactQuantity,
    location: str,
    rule_issues: list[Issue],
) -> str:
    """One performance-derived dimension of the single applicable observation (``§2.7.6`` ／ ``§2.7.7``).

    ``PerformancePeriod`` is required for the completeness of these two dimensions (``§2.7.16`` period row
    ／ ``§4.4.64``): an unusable period fails them closed **without** touching ``LeadTimeRisk``, which is
    computed from its own inputs, and the period finding itself is stated once per card by the caller.
    ``0`` is a valid extreme (``§2.7.10``) and is never conflated with a missing value; nothing is clamped,
    defaulted or rounded, and both comparisons are exact.
    """

    if observation is None:
        # Option A applicability is unresolved: the seam already published the registered
        # SEMANTIC_RESOLUTION ／ SEMANTIC_UNRESOLVED finding, so no field finding is duplicated here.
        return RISK_DATA_INCOMPLETE

    if not period_ok:
        return RISK_DATA_INCOMPLETE

    if reading.quantity is None:
        rule_issues.append(
            _field_issue(
                location=location,
                property_name=property_name,
                defect=reading.defect or REASON_MISSING,
                detail=(
                    f"the applicable Supplier Performance observation states no usable {property_name} "
                    f"({reading.value!r}), so the {dimension} threshold cannot be applied and the "
                    "dimension fails closed; a missing value is never defaulted to 0 or 100 and a "
                    "present-but-invalid value is never repaired (§2.7.16 / §4.4.34 / §4.4.40)"
                ),
                affected_evidence=observation.record_reference,
                consequence=(
                    f"{dimension} = DATA_INCOMPLETE for this request; the other dimensions stay "
                    "independently determined"
                ),
                design_reference="§2.7.6 / §2.7.7 / §2.7.16 / §4.4.34 / §4.4.40 / §4.4.44",
            )
        )
        return RISK_DATA_INCOMPLETE

    value = reading.quantity
    assert value is not None
    if value >= low_minimum:
        return RISK_LOW
    if value >= medium_minimum:
        return RISK_MEDIUM
    return RISK_HIGH


def _card_key(card: SupplierRiskEvidenceCard) -> tuple[str, str, str]:
    return (
        _sort_text(card.plant_id),
        _sort_text(card.material_code),
        _sort_text(card.supplier_id),
    )


__all__ = [
    "DELIVERY_LOW_MINIMUM",
    "DELIVERY_MEDIUM_MINIMUM",
    "LEAD_TIME_PROPERTY",
    "PERCENTAGE_MAXIMUM",
    "PERCENTAGE_MINIMUM",
    "QUALITY_LOW_MINIMUM",
    "QUALITY_MEDIUM_MINIMUM",
    "REQUIRED_RISK_DIMENSIONS",
    "RISK_DATA_INCOMPLETE",
    "RISK_HIGH",
    "RISK_LOW",
    "RISK_MEDIUM",
    "SEVERITY_ORDER",
    "SUPPLIER_RISK_STAGE",
    "SupplierRiskEvidenceCard",
    "SupplierRiskResult",
    "compute_supplier_risk",
]
