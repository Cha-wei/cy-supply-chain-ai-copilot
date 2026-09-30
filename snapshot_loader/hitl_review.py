"""Minimal in-process §6 HITL review / decision runtime (non-canonical runtime artifacts).

Registered authority:

* ``POC Design v0.2`` §6 -- the Issue #198 design record (Human Decision ``HD-1`` -- ``HD-7``): the
  read-only review projection over already-registered values, the approval target, the reject
  contract, the strict AnalysisRun staleness / re-review contract, and the **non-canonical** Human
  decision record with its minimal field set.
* ``POC Design v0.2`` §10.3 -- the Issue #200 registration (Human Decision ``HD-HITL-R1`` /
  ``HD-HITL-R2``): the approved Option A runtime architecture boundary, the reduced first HITL
  coding tranche, and the Required Test obligations of §10.3 H.

What this module is
-------------------

```text
read-only Review projection
  -> Approve the deterministic RecommendedPurchaseQty as-is
  -> Reject
  -> AnalysisRun stale detection / re-review enforcement
```

It **consumes** the already-registered deterministic result surfaces (``ProcurementRecommendation``
/ ``ProcurementRecommendationResult``, the Supplier Risk evidence cards, and an explanation result's
runtime outcome + artifact as **read-only auxiliary information only**).  It recomputes nothing, fills
nothing, invents no classification / status and changes no provenance.  The artifact is never an
approval authority.

Deliberate boundaries (``HD-HITL-R1`` / ``§10.3`` C / D / ``§10.4`` / ``§10.5``):

* **explicit Human quantity override is bounded by the registered HD-3 contract.**  The only override
  path is :meth:`ReviewInstance.approve_with_override`, whose input must be an **exact finite base-10
  decimal string** that parses through the existing exact quantity machinery, is strictly positive,
  satisfies the existing ``ApplicableMOQ``, and is accompanied by a Human reason.  It never coerces:
  no float, rounding, quantization, truncation, clamping, normalization, absolute value or
  auto-adjust-to-MOQ, and no new precision / scale semantics.  A violation fails closed at the
  decision level, and no ``modify`` decision kind, canonical enum or business status is introduced.
  The Human decision record carries the registered **override-existence flag**, which truthfully
  expresses either *"no quantity override"* (the as-is / reject paths) or an explicit Human override.
* **no persistence.**  Every review instance and decision is an in-process runtime object; nothing
  is written to disk, to a database or to any durable business state.
* **no network / egress.**  The review projection is never handed to a provider.
* **no identity or permission enforcement.**  The ``actor reference`` is a **requirement slot**: it
  must be supplied non-empty at ``open_review`` **and** at each decision, and it is carried
  verbatim, but this module verifies neither identity nor permission and claims neither (``§7``
  RBAC / Data Scope / Tool Permission stay ``DESIGN PENDING``).  No rule such as "the reviewer must
  be the approver" is introduced.
* **no rule- or code-version freshness claim.**  Staleness compares exactly the four existing
  ``AnalysisRunContext`` components (``F3-RB1``); it deliberately does not claim that the same
  AnalysisRun identity proves identical deterministic output across different rule / code versions
  or different future executions (``§6`` item 6).

The explanation is consumed under its own Analysis Run binding, which the explanation runtime binds
when it produces the result.  A binding that matches the reviewed run lets the review carry the
explanation's runtime outcome, availability note and artifact as **auxiliary information only**; a
binding that differs anywhere means the explanation is explicitly unavailable for this review -- its
artifact is never consumed, nothing is regenerated, no provider is called, and the deterministic
review simply continues under its own registered approval conditions.

Freshness is a **blocking condition, not a sufficient condition**.  A matching AnalysisRun binding
means only that the freshness check does not block approval; approval must additionally satisfy
every other registered condition (an open review instance, a matching grain, an applicable numeric
recommendation, and no terminal rejected / approved / stale condition).  ``§10.3`` C / H forbid
implementing this as "same AnalysisRun implies approve".

Staleness is **irreversible in process**.  Once a review instance has been observed stale (against
whatever Analysis Run was current at that moment), that same instance never returns to
review-in-progress, can never approve or reject, and is never revived by a later caller passing the
original Analysis Run again: ``§6`` item 8 requires a **new** review instance for a new Analysis Run.
This is an in-memory instance condition, not durable persistence.

Formed artifacts are immutable.  A review projection opens no public surface that can rewrite its
grain, facts, references, supplier-risk evidence, explanation content or payload/reference, and a
formed Human decision record cannot be rewritten afterwards: mutating a projected value into a
different grain's decision is not expressible through the public surface.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from .canonical_objects import AnalysisRunContext
from .exact_quantity import ExactQuantity, parse_exact_quantity
from .procurement_recommendation import (
    ProcurementRecommendation,
    ProcurementRecommendationResult,
)
from .result_binding import ANALYSIS_RUN_COMPONENTS

if TYPE_CHECKING:  # pragma: no cover - typing only, keeps the runtime import surface minimal
    from .explanation_seam import ExplanationResult
    from .supplier_risk_calculation import SupplierRiskEvidenceCard

#: The answer-independent question identifier of this runtime surface (not a business concept).
REVIEW_QUESTION: str = "REVIEW"

#: Decision kinds.  ``§6`` item 4 registers these two kinds **in prose**; they are plain runtime
#: literals here, deliberately **not** a canonical enum or business status (``HD-6``).
DECISION_APPROVE: str = "approve"
DECISION_REJECT: str = "reject"

#: Review instance conditions.  Internal runtime state only -- never a canonical business status
#: (``HD-6`` / ``§9.6``).
REVIEW_OPEN: str = "OPEN"
REVIEW_APPROVED: str = "APPROVED"
REVIEW_REJECTED: str = "REJECTED"
REVIEW_STALE: str = "STALE"

#: Review projection outcome: the deterministic result states one numeric recommendation.
PROJECTION_RECOMMENDATION: str = "RECOMMENDATION"
#: Review projection outcome: the deterministic result states no recommendation for this family.
PROJECTION_NO_RECOMMENDATION: str = "NO_RECOMMENDATION_STATED"

#: The review projection payload keys (the only keys the projection ever carries).
PROJECTION_KEYS: tuple[str, ...] = (
    "question",
    "grain",
    "outcome",
    "facts",
    "references",
    "supplier_risk_evidence",
    "supplier_risk_facts",
    "explanation",
    "notes",
)

#: The ``§6`` item 4 deterministic-fact set of the review projection, in the rule's own order.
REVIEW_FACT_FIELDS: tuple[str, ...] = (
    "ShortageQty",
    "BasePurchaseNeed",
    "ApplicableMOQ",
    "MOQAdjustmentQty",
    "RecommendedPurchaseQty",
)

#: The registered grain of one review / decision.
REVIEW_GRAIN_FIELDS: tuple[str, ...] = (
    "plant_id",
    "material_code",
    "RecommendationNeedDate",
)

#: The evidence-reference kinds the decision record may carry.  ``§6`` item 4 registers the decision's
#: evidence references as **existing references** -- the two upstream result references, plus the
#: Supplier Risk evidence **identity**.  A reference always points at an existing registered identity:
#: raw evidence, risk values and business status are never copied into the decision record.
EVIDENCE_KIND_UPSTREAM_RESULT: str = "upstream_result_reference"
EVIDENCE_KIND_SUPPLIER_RISK: str = "supplier_risk_evidence_identity"

#: The exact keys of one upstream-result reference (a rule identity plus the upstream grain).
REFERENCE_KEYS_UPSTREAM: tuple[str, ...] = ("kind", "rule", "grain")
#: The exact keys of one Supplier Risk evidence **identity** reference.  These are identity only: the
#: card's evaluation context and grain, the Analysis Run it belongs to, and the two evidence
#: references the card itself already carries.  No risk value, no dimension level and no business
#: status is an identity, so none of them travels here (they stay in the review projection).
REFERENCE_KEYS_SUPPLIER_RISK: tuple[str, ...] = (
    "kind",
    "evaluation_context",
    "grain",
    "analysis_run_id",
    "relationship_reference",
    "performance_evidence_reference",
)

#: The Human decision record field set (``§6`` item 4) this runtime always states.
DECISION_RECORD_FIELDS: tuple[str, ...] = (
    "decision_kind",
    "grain",
    "analysis_run",
    "deterministic_recommended_value",
    "approved_value",
    "override_flag",
    "human_reason",
    "evidence_references",
    "actor_reference",
    "decision_timestamp",
    "review_projection_reference",
)

#: The single reason text this tranche can ever state alongside the override-existence flag.
NO_OVERRIDE_REASON: str = "no_quantity_override"
#: The internal reason text paired with ``override_flag = True``.  This is a **runtime
#: implementation detail**, not a canonical field or vocabulary: ``§6`` item 4 registers only that the
#: override existence flag and the Human reason must be retained together.  It is deliberately **not**
#: exported from this module or from the package, so the token never becomes public surface.
_INTERNAL_OVERRIDE_REASON: str = "explicit_human_quantity_override"

#: Deterministic, provider-independent note carried when nothing could be reviewed.
NOTE_REVIEW_NO_RECOMMENDATION: str = (
    "the consumed deterministic result states no purchase recommendation for this family, so this "
    "review instance has no recommended quantity to approve (§2.5.2 / §4.4.87)"
)
NOTE_REVIEW_NO_NUMERIC_RECOMMENDATION: str = (
    "the consumed deterministic recommendation is DATA_INCOMPLETE, so it states no numeric "
    "recommended quantity and cannot be approved as-is (§2.5.8)"
)
#: The explanation's own Analysis Run binding is not the reviewed run's (``§6`` item 6 / ``HD-4``).
NOTE_REVIEW_EXPLANATION_STALE: str = (
    "AI explanation unavailable for this review: the explanation was produced under a different "
    "Analysis Run, so its artifact is not consumed and the explanation must be regenerated or "
    "treated as unavailable (§6 item 6 / HD-4); the deterministic review is unaffected"
)

#: Explanation binding states of the review projection.  Internal runtime literals, never canonical
#: business status.
EXPLANATION_BOUND: str = "BOUND"
EXPLANATION_UNAVAILABLE_FOR_REVIEW: str = "UNAVAILABLE_FOR_REVIEW"
#: The explanation payload keys (the only keys the explanation section ever carries).
EXPLANATION_KEYS: tuple[str, ...] = (
    "binding",
    "outcome",
    "availability_note",
    "artifact",
    "analysis_run",
)


class ReviewError(Exception):
    """Base class for the invocation-level rejections of this runtime surface."""


class ReviewConflictError(ReviewError):
    """The review instance may not produce this decision (stale / terminal / mismatched grain).

    The rejection is about the *instance*, not about the deterministic evidence: nothing is
    recomputed, no deterministic value is consumed, and no decision record is produced.
    """


class ReviewPreconditionError(ReviewError):
    """The requested decision does not satisfy a registered precondition (``§6``)."""


def _instant() -> datetime:
    """The default decision clock: one timezone-aware UTC instant per decision."""

    return datetime.now(timezone.utc)


def _rational_payload(value: Fraction | None) -> dict[str, int] | None:
    """The lossless exact payload of one deterministic quantity, or ``None`` when unstated.

    Quantities are carried exactly (``§4.3.25`` C-5): no rounding, quantization, truncation or
    float conversion is ever applied here.
    """

    if value is None:
        return None
    return {"numerator": value.numerator, "denominator": value.denominator}


def _exact_fraction(quantity: ExactQuantity) -> Fraction:
    """One exact base-10 quantity as an exact rational, with no precision loss.

    The registered decision payload is an exact rational (``{"numerator", "denominator"}``), so an
    override parsed through the existing exact quantity machinery is converted **exactly** here:
    ``units / 10 ** scale`` is a power-of-ten denominator, so the value is lossless by construction
    and no rounding, quantization or scale policy is involved.
    """

    return Fraction(quantity.units, 10**quantity.scale)


def _deep_freeze(value: Any) -> Any:
    """An immutable view of an already-formed runtime payload.

    Mappings become read-only proxies and sequences become tuples, recursively.  This is what makes a
    formed review projection (and a formed decision record) unrewritable through the public surface:
    a mutation attempt raises instead of silently re-pointing a decision at another grain.  Nothing
    is serialized, copied to disk or re-shaped into a new contract -- the payload keeps exactly the
    keys and values it already had.
    """

    if isinstance(value, Mapping):
        return MappingProxyType({key: _deep_freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _grain_payload(plant_id: Any, material_code: Any, need_date: Any) -> dict[str, Any]:
    return {
        "plant_id": plant_id,
        "material_code": material_code,
        "RecommendationNeedDate": need_date,
    }


def _plain(value: Any) -> Any:
    """The plain-data view of an already-formed payload, for digesting only.

    Read-only proxies and tuples are rendered as the mappings and lists they already are; nothing is
    added, renamed or re-typed, so the digest covers exactly the projection's own content.
    """

    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def _canonical_json(payload: Any) -> str:
    return json.dumps(
        _plain(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def projection_reference(payload: Mapping[str, Any]) -> str:
    """A stable, non-canonical reference to one review projection payload.

    The reference is a digest of the projection's own registered content, so a decision can state
    **which** projection it reviewed without copying the projection and without introducing a new
    canonical identifier scheme.
    """

    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return f"review-projection:{digest}"


def payload_to_plain(payload: Any) -> Any:
    """The plain-data view of a formed runtime artifact, for inspection and serialization.

    The runtime keeps its projection and decision payloads deeply frozen, so a formed artifact cannot
    be rewritten through the public surface.  This helper renders such a payload as ordinary
    ``dict`` / ``list`` data **on demand** for a caller that wants to read, compare or serialize it.
    It adds, renames and re-types nothing: it is the same keys and values the artifact already
    carries, and it does not make the runtime artifact mutable.
    """

    return _plain(payload)


def _reference_payload(kind: str, *, rule: str, grain: Sequence[Any]) -> dict[str, Any]:
    return {"kind": kind, "rule": rule, "grain": list(grain)}


# --- review projection ---------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ReviewProjection:
    """The read-only, non-canonical review projection of one recommendation grain (``§6`` item 3).

    It selects only already-registered values -- the recommendation's grain, outcome, five
    registered quantities and its own upstream references, the Supplier Risk evidence cards as
    **read-only evidence identity**, and an explanation result's runtime outcome as **auxiliary
    information only**.  It never carries the accepted package, the whole pipeline result or a raw
    source artifact, it never recomputes or defaults a value, and it is never sent to any provider
    (no egress).

    Every mapping and sequence exposed here is deeply frozen, so a formed projection cannot be
    rewritten through the public surface: neither its grain, its facts, its references, its
    supplier-risk evidence, its explanation content nor its payload/reference can be mutated into
    another grain's review.
    """

    question: str
    outcome: str
    grain: Mapping[str, Any]
    facts: Mapping[str, Any]
    references: Mapping[str, Any]
    supplier_risk_evidence: tuple[Mapping[str, Any], ...] = ()
    supplier_risk_facts: tuple[Mapping[str, Any], ...] = ()
    explanation: Mapping[str, Any] | None = None
    notes: tuple[str, ...] = ()
    payload: Mapping[str, Any] = field(default_factory=dict)

    @property
    def reference(self) -> str:
        """The stable reference of this projection payload."""

        return projection_reference(self.payload)

    @property
    def recommendation_at_risk(self) -> bool:
        """Whether the projection carries a numeric recommended quantity."""

        return self.facts.get("RecommendedPurchaseQty") is not None

    def to_dict(self) -> dict[str, Any]:
        """A defensive plain-data copy, so callers never hold the runtime's own mapping."""

        return _plain(dict(self.payload))


def _projection_payload(
    *,
    plant_id: Any,
    material_code: Any,
    need_date: Any,
    outcome: str,
    facts: Mapping[str, Any],
    references: Mapping[str, Any],
    supplier_risk_evidence: Sequence[Mapping[str, Any]],
    supplier_risk_facts: Sequence[Mapping[str, Any]],
    explanation: Mapping[str, Any] | None,
    notes: Sequence[str],
) -> dict[str, Any]:
    return {
        "question": REVIEW_QUESTION,
        "grain": _grain_payload(plant_id, material_code, need_date),
        "outcome": outcome,
        "facts": dict(facts),
        "references": dict(references),
        "supplier_risk_evidence": [dict(item) for item in supplier_risk_evidence],
        "supplier_risk_facts": [dict(item) for item in supplier_risk_facts],
        "explanation": None if explanation is None else dict(explanation),
        "notes": list(notes),
    }


def _frozen_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    """The runtime-owned, deeply frozen view of one projection payload."""

    frozen = _deep_freeze(dict(payload))
    assert isinstance(frozen, Mapping)
    return frozen


def _from_payload(payload: Mapping[str, Any]) -> ReviewProjection:
    """Build a projection whose every exposed mapping is the frozen payload's own view."""

    frozen = _frozen_projection(payload)
    return ReviewProjection(
        question=str(frozen["question"]),
        outcome=str(frozen["outcome"]),
        grain=frozen["grain"],
        facts=frozen["facts"],
        references=frozen["references"],
        supplier_risk_evidence=frozen["supplier_risk_evidence"],
        supplier_risk_facts=frozen["supplier_risk_facts"],
        explanation=frozen["explanation"],
        notes=frozen["notes"],
        payload=frozen,
    )


def _recommendation_references(
    recommendation: ProcurementRecommendation,
) -> dict[str, Any]:
    """The recommendation's own upstream references, as references (never copied evidence)."""

    references: dict[str, Any] = {
        "shortage_reference": None,
        "policy_input_reference": None,
        "rule": recommendation.to_dict().get("rule"),
    }
    for name in ("shortage_reference", "policy_input_reference"):
        reference = getattr(recommendation, name)
        references[name] = (
            None
            if reference is None
            else _reference_payload(
                EVIDENCE_KIND_UPSTREAM_RESULT, rule=reference.rule, grain=reference.grain
            )
        )
    return references


def _evidence_reference_identity(reference: Any) -> dict[str, Any]:
    """The registered provenance identity of one accepted-evidence reference.

    ``§6`` item 4 registers evidence as **references** and forbids copying raw evidence.  The
    existing :class:`~snapshot_loader.canonical_objects.EvidenceReference` is the provenance carrier:
    its identity fields are selected verbatim here (package identity, logical role, artifact,
    record ordinal, registered observation and the registered locator ／ basis values the accepted
    record itself states).  No new identifier scheme is minted and no accepted record content is
    copied.
    """

    if reference is None:
        return {"kind": "performance_evidence_reference", "present": False}
    return {
        "kind": "performance_evidence_reference",
        "present": True,
        "snapshot_package_identity": getattr(reference, "snapshot_package_identity", None),
        "logical_dataset_role": getattr(reference, "logical_dataset_role", None),
        "artifact": getattr(reference, "artifact", None),
        "record_ordinal": getattr(reference, "record_ordinal", None),
        "logical_observation": getattr(reference, "logical_observation", None),
        "stable_source_evidence_locators": list(
            getattr(reference, "stable_source_evidence_locators", ()) or ()
        ),
        "mapping_resolution_basis": getattr(reference, "mapping_resolution_basis", None),
    }


def _risk_evidence_identity(card: "SupplierRiskEvidenceCard") -> dict[str, Any]:
    """The read-only **identity** of one Supplier Risk evidence card.

    Identity only: the card's own evaluation context and grain, the Analysis Run it belongs to, and
    the two evidence references the card already carries.  No risk dimension, no performance value
    and no business status travels here -- those stay in the projection as risk facts.
    """

    return {
        "kind": EVIDENCE_KIND_SUPPLIER_RISK,
        "evaluation_context": {
            "plant_id": card.plant_id,
            "material_code": card.material_code,
            "supplier_id": card.supplier_id,
        },
        "grain": {
            "supplier_id": card.supplier_id,
            "material_code": card.material_code,
        },
        "analysis_run_id": card.analysis_run_id,
        "relationship_reference": card.relationship_reference,
        "performance_evidence_reference": _evidence_reference_identity(
            card.performance_evidence_reference
        ),
    }


def _risk_evidence_facts(card: "SupplierRiskEvidenceCard") -> dict[str, Any]:
    """The card's registered read-only risk values, kept in the **projection** (not the decision).

    These are the values a Human reviews; they are risk judgements and measurements, so they are
    deliberately not part of the decision record's evidence references.
    """

    return {
        "supplier_id": card.supplier_id,
        "material_code": card.material_code,
        "plant_id": card.plant_id,
        "analysis_run_id": card.analysis_run_id,
        "RecommendationNeedDate": card.recommendation_need_date,
        "DaysUntilNeed": card.days_until_need_text,
        "StandardLeadTimeDays": card.standard_lead_time_days,
        "LeadTimeRisk": card.lead_time_risk,
        "PerformancePeriod": card.performance_period,
        "PerformanceUpdatedAt": card.performance_updated_at,
        "DeliveryPerformance": card.delivery_performance,
        "DeliveryRisk": card.delivery_risk,
        "QualityPerformance": card.quality_performance,
        "QualityRisk": card.quality_risk,
        "OverallSupplierRisk": card.overall_supplier_risk,
        "status": card.status,
        "evidence_complete": card.evidence_complete,
    }


def _explanation_section(
    explanation: "ExplanationResult | None", analysis_run: AnalysisRunContext
) -> Mapping[str, Any] | None:
    """The review projection's explanation section (``§6`` items 3 / 6).

    The explanation is **auxiliary information only**: it is never an approval authority, never a
    deterministic fact source and never a decision input authority, so nothing here changes approve /
    reject eligibility.

    The explanation result carries its own ``AnalysisRunContext``, bound by the runtime that produced
    it (never declared by a caller).  That binding is compared with the reviewed run through the
    existing ``F3-RB1`` component set:

    * **bound** -- the whole binding matches, so the runtime outcome, the availability note and the
      artifact (when one exists) are carried read-only;
    * **unavailable for this review** -- any component differs, so the explanation is explicitly
      unavailable: the artifact is **not** consumed, and it is never inferred fresh from an equal
      grain or equal quantities (``§6`` item 6 forbids treating Analysis Run identity as a
      cross-rule-version equivalence guarantee, and no rule- or code-version freshness exists here).

    Nothing is regenerated and no provider is called: this function only reads what it was given.
    """

    if explanation is None:
        return None

    differences = analysis_run_differences(explanation.analysis_run, analysis_run)
    if differences:
        return {
            "binding": EXPLANATION_UNAVAILABLE_FOR_REVIEW,
            "outcome": explanation.outcome,
            "availability_note": NOTE_REVIEW_EXPLANATION_STALE,
            "artifact": None,
            "analysis_run": None,
        }

    artifact = None if explanation.response is None else explanation.response.to_dict()
    return {
        "binding": EXPLANATION_BOUND,
        "outcome": explanation.outcome,
        "availability_note": explanation.availability_note,
        "artifact": artifact,
        "analysis_run": {
            "analysis_run_id": explanation.analysis_run.analysis_run_id,
            "snapshot_package_identity": explanation.analysis_run.snapshot_package_identity,
            "accepted_content_view_digest": (
                explanation.analysis_run.accepted_content_view_digest
            ),
            "analysis_date": explanation.analysis_run.analysis_date,
        },
    }


def build_review_projection(
    recommendations: ProcurementRecommendationResult,
    *,
    plant_id: Any,
    material_code: Any,
    supplier_risk: Any | None = None,
    explanation: "ExplanationResult | None" = None,
) -> ReviewProjection:
    """Build the read-only review projection of one recommendation grain (``§6`` item 3).

    Every value is selected from the consumed deterministic result; nothing is recomputed, filled,
    re-classified or repaired, and a value the deterministic result does not state stays ``None``.

    Supplier Risk cards are read only when they belong to this exact plant + material family **and**
    their consumed result's whole ``AnalysisRunContext`` matches the consumed recommendation
    result's own context on all four registered components (``F3-RB1``): an evidence card whose
    package identity, accepted content view or analysis date differs is foreign / stale evidence and
    is never consumed, even when the run id looks the same.

    The explanation is consumed under its own runtime ``AnalysisRun`` binding: an
    ``ExplanationResult`` carries the ``AnalysisRunContext`` of the deterministic result it was
    produced from.  When that binding matches this review's run on all four registered components,
    the explanation may contribute its runtime outcome, availability note and artifact as **read-only
    auxiliary information only**.  When any component differs, the artifact is **unavailable for this
    review** and is not consumed.  This review never regenerates an explanation and never calls a
    provider, and the artifact never affects Approve / Reject authority.
    """

    recommendation = recommendations.for_family(plant_id, material_code)
    if recommendation is None:
        facts = {name: None for name in REVIEW_FACT_FIELDS}
        notes = (NOTE_REVIEW_NO_RECOMMENDATION,)
        payload = _projection_payload(
            plant_id=plant_id,
            material_code=material_code,
            need_date=None,
            outcome=PROJECTION_NO_RECOMMENDATION,
            facts=facts,
            references={"shortage_reference": None, "policy_input_reference": None, "rule": None},
            supplier_risk_evidence=(),
            supplier_risk_facts=(),
            explanation=_explanation_section(explanation, recommendations.analysis_run),
            notes=notes,
        )
        return _from_payload(payload)

    registered = recommendation.to_dict()
    facts = {name: registered.get(name) for name in REVIEW_FACT_FIELDS}
    references = _recommendation_references(recommendation)

    evidence: list[dict[str, Any]] = []
    risk_facts: list[dict[str, Any]] = []
    if supplier_risk is not None:
        foreign = analysis_run_differences(
            supplier_risk.analysis_run, recommendations.analysis_run
        )
        if not foreign:
            for card in supplier_risk.cards:
                if card.plant_id != plant_id or card.material_code != material_code:
                    continue
                evidence.append(_risk_evidence_identity(card))
                risk_facts.append(_risk_evidence_facts(card))

    explanation_payload = _explanation_section(explanation, recommendations.analysis_run)

    # An applicable numeric recommendation is the reviewable case; a recommendation the rule states
    # as DATA_INCOMPLETE keeps its own registered outcome and is never silently promoted.
    stated_outcome = registered.get("outcome")
    outcome = (
        PROJECTION_RECOMMENDATION
        if recommendation.has_numeric_result
        else (stated_outcome if isinstance(stated_outcome, str) else PROJECTION_RECOMMENDATION)
    )
    notes: tuple[str, ...] = ()
    if not recommendation.has_numeric_result:
        notes = (NOTE_REVIEW_NO_NUMERIC_RECOMMENDATION,)

    payload = _projection_payload(
        plant_id=plant_id,
        material_code=material_code,
        need_date=recommendation.recommendation_need_date,
        outcome=outcome,
        facts=facts,
        references=references,
        supplier_risk_evidence=evidence,
        supplier_risk_facts=risk_facts,
        explanation=explanation_payload,
        notes=notes,
    )
    return _from_payload(payload)


# --- AnalysisRun freshness ----------------------------------------------------------------


def analysis_run_differences(
    bound: AnalysisRunContext, current: AnalysisRunContext
) -> tuple[str, ...]:
    """The ``AnalysisRunContext`` components that differ, in the registered comparison order.

    The comparison covers exactly the four existing components (``F3-RB1``); no rule-version or
    code-version component exists here and none is invented.
    """

    return tuple(
        name
        for name in ANALYSIS_RUN_COMPONENTS
        if getattr(bound, name, None) != getattr(current, name, None)
    )


def analysis_run_is_current(bound: AnalysisRunContext, current: AnalysisRunContext) -> bool:
    """Whether the review's own binding is still the current Analysis Run."""

    return not analysis_run_differences(bound, current)


# --- Human decision record ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class HumanDecision:
    """The non-canonical Human decision runtime record (``§6`` item 4 minimal field set).

    This is a **runtime artifact, not a canonical entity**: it never enters a deterministic result
    and never becomes an ``ApprovedPurchaseQty`` enterprise fact (``§2.5.15``), and it is never
    persisted (durable approval history belongs to ``§8`` and is not implemented here).

    ``override_flag`` is the registered override-existence flag.  It is ``False`` for the as-is and
    reject paths (with ``override_reason`` = :data:`NO_OVERRIDE_REASON`), and ``True`` for an explicit
    Human quantity override (with an internal, non-exported ``override_reason`` value), in which case
    ``approved_value`` is the exact Human override value while ``deterministic_recommended_value``
    keeps the original deterministic ``RecommendedPurchaseQty``.  ``override_reason`` is a **runtime
    implementation detail**, not a canonical field or vocabulary: ``§6`` item 4 registers only that
    the override existence flag and the Human reason are retained together.  No ``modify`` decision
    kind, canonical enum or business status is introduced.

    ``actor_reference`` is carried verbatim as a **requirement slot** and is required to be
    non-empty for every decision.  It is **not** an identity assertion and **not** a permission
    check: this runtime verifies neither, and it introduces no rule about who may approve.

    ``evidence_references`` holds **references / identity only** (see
    :data:`REFERENCE_KEYS_UPSTREAM` / :data:`REFERENCE_KEYS_SUPPLIER_RISK`); the risk values the
    Human reviewed stay in the review projection, which this record links to through
    ``review_projection_reference``.  Every reference is deeply frozen, so a formed decision cannot
    be rewritten afterwards.
    """

    decision_kind: str
    grain: tuple[Any, Any, Any]
    analysis_run: AnalysisRunContext
    deterministic_recommended_value: Fraction | None
    approved_value: Fraction | None
    override_flag: bool
    override_reason: str | None
    human_reason: str | None
    evidence_references: tuple[Mapping[str, Any], ...]
    actor_reference: str
    decision_timestamp: datetime
    review_projection_reference: str

    def to_dict(self) -> dict[str, Any]:
        """The record's own stable payload (exact quantities, no float conversion)."""

        return {
            "decision_kind": self.decision_kind,
            "grain": _grain_payload(*self.grain),
            "analysis_run": {
                "analysis_run_id": self.analysis_run.analysis_run_id,
                "snapshot_package_identity": self.analysis_run.snapshot_package_identity,
                "accepted_content_view_digest": self.analysis_run.accepted_content_view_digest,
                "analysis_date": self.analysis_run.analysis_date,
            },
            "deterministic_recommended_value": _rational_payload(
                self.deterministic_recommended_value
            ),
            "approved_value": _rational_payload(self.approved_value),
            "override_flag": self.override_flag,
            "override_reason": self.override_reason,
            "human_reason": self.human_reason,
            "evidence_references": [_plain(dict(item)) for item in self.evidence_references],
            "actor_reference": self.actor_reference,
            "decision_timestamp": self.decision_timestamp.isoformat(),
            "review_projection_reference": self.review_projection_reference,
        }


# --- review instance ------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ReviewInstance:
    """One in-process review instance of one recommendation grain under one Analysis Run.

    A review instance is **ephemeral**: it lives only as this runtime object.  It is created for a
    specific grain and bound to the complete :class:`AnalysisRunContext` of the deterministic
    result it reviews, because ``§6`` item 6 requires the approval to be bound to the full context.

    It is immutable and its staleness is **irreversible in process**.  Once this instance has been
    observed stale against a current Analysis Run, it never returns to review-in-progress and can
    neither approve nor reject again -- not even if a later caller passes the original Analysis Run
    back.  A new Analysis Run requires a **new** review instance (``§6`` item 8); this is an
    in-memory instance condition, not durable persistence.
    """

    analysis_run: AnalysisRunContext
    projection: ReviewProjection
    actor_reference: str
    recommendation: ProcurementRecommendation | None
    _status: str = REVIEW_OPEN
    decision: HumanDecision | None = None
    notes: tuple[str, ...] = ()
    #: The first observed current Analysis Run that made this instance stale, if any.
    _stale_marker: Mapping[str, Any] | None = None

    # --- identity -------------------------------------------------------------------------

    @property
    def grain(self) -> tuple[Any, Any, Any]:
        return (
            self.projection.grain.get("plant_id"),
            self.projection.grain.get("material_code"),
            self.projection.grain.get("RecommendationNeedDate"),
        )

    @property
    def review_projection_reference(self) -> str:
        return self.projection.reference

    @property
    def recommended_purchase_qty(self) -> Fraction | None:
        """The deterministic recommended quantity of this grain, or ``None`` when unstated."""

        return (
            None if self.recommendation is None else self.recommendation.recommended_purchase_qty
        )

    @property
    def has_approvable_recommendation(self) -> bool:
        """Whether the deterministic result states an applicable numeric recommendation."""

        return self.recommendation is not None and self.recommendation.has_numeric_result

    @property
    def applicable_moq(self) -> ExactQuantity | None:
        """The **existing** deterministic ``ApplicableMOQ`` of this grain, or ``None``.

        This is the read-only MOQ the override path validates against (``§10.4`` C).  It is consumed
        from the already-registered recommendation result -- not a new input channel, not a new
        contract, and never modified, defaulted or recomputed here.
        """

        return None if self.recommendation is None else self.recommendation.applicable_moq

    @property
    def is_stale_forever(self) -> bool:
        """Whether this instance has already been observed stale (and therefore never revives)."""

        return self._stale_marker is not None

    # --- condition ------------------------------------------------------------------------

    def is_stale(self, current_analysis_run: AnalysisRunContext) -> bool:
        """Whether this review's binding differs from ``current_analysis_run``.

        The judgement is recorded: observing a difference marks this instance stale permanently, so
        the same instance cannot later be treated as live again.
        """

        if self._stale_marker is not None:
            return True
        if analysis_run_is_current(self.analysis_run, current_analysis_run):
            return False
        object.__setattr__(
            self,
            "_stale_marker",
            MappingProxyType(
                {
                    "analysis_run_id": current_analysis_run.analysis_run_id,
                    "snapshot_package_identity": current_analysis_run.snapshot_package_identity,
                    "accepted_content_view_digest": (
                        current_analysis_run.accepted_content_view_digest
                    ),
                    "analysis_date": current_analysis_run.analysis_date,
                }
            ),
        )
        return True

    def status(self, current_analysis_run: AnalysisRunContext) -> str:
        """The instance's runtime condition under ``current_analysis_run``.

        A stale instance always reports :data:`REVIEW_STALE`, whatever it previously recorded and
        whoever it is compared against afterwards: a decision taken before the Analysis Run changed
        is never re-presented as a live approval, and the stale condition is never cleared
        (``§6`` item 8).
        """

        if self.is_stale(current_analysis_run):
            return REVIEW_STALE
        return self._status

    def freshness_note(self, current_analysis_run: AnalysisRunContext) -> str:
        """Why the freshness check did or did not block approval (never an approval by itself)."""

        differing = analysis_run_differences(self.analysis_run, current_analysis_run)
        if self._stale_marker is not None and not differing:
            return (
                "this review instance was already observed stale against another Analysis Run, so "
                "it stays stale and no decision can be taken on it (§6 item 8); a new Analysis Run "
                "requires a new review instance"
            )
        if differing:
            return (
                "the current Analysis Run differs in "
                f"{', '.join(differing)}, so this review instance is stale and approval is denied"
            )
        return (
            "the Analysis Run binding matches, so the freshness check does not block approval; "
            "approval still requires an open review instance, a matching grain and an applicable "
            "numeric recommendation"
        )

    # --- decisions ------------------------------------------------------------------------

    @staticmethod
    def _require_actor(actor_reference: Any) -> str:
        """Every decision must carry a non-empty actor-reference slot (``§6`` item 4).

        The slot is required; its content is never verified.  Presence is not identity and not
        permission, and this runtime establishes no reviewer / approver rule.  The registered slot
        text is returned so a decision carries exactly the value the review states.
        """

        if not isinstance(actor_reference, str) or not actor_reference.strip():
            raise ReviewPreconditionError(
                "a Human decision record requires an identified actor-reference slot (§6 item 4): "
                "it is carried verbatim and never verified, but a decision without one is not a "
                "Human decision"
            )
        return actor_reference

    def _require_open(self, current_analysis_run: AnalysisRunContext) -> None:
        if self.is_stale(current_analysis_run):
            if self._stale_marker is not None:
                differing = analysis_run_differences(self.analysis_run, current_analysis_run)
                detail = (
                    f"the current Analysis Run differs in {', '.join(differing)}"
                    if differing
                    else (
                        "this instance was already observed stale against another Analysis Run "
                        "and is never revived"
                    )
                )
            else:  # pragma: no cover - is_stale() marks the instance, so this branch is defensive
                detail = "the Analysis Run binding no longer matches"
            raise ReviewConflictError(
                f"this review instance is stale: {detail}; a stale instance stays stale, can never "
                "be revived and can never approve or reject (§6 item 8), and a new Analysis Run "
                "requires a new review instance"
            )
        if self._status != REVIEW_OPEN:
            raise ReviewConflictError(
                f"this review instance is already in a terminal condition ({self._status}); the "
                "same instance cannot decide twice and an earlier decision is never rewritten "
                "(§6 item 8)"
            )

    def approve_as_recommended(
        self,
        *,
        current_analysis_run: AnalysisRunContext,
        plant_id: Any,
        material_code: Any,
        recommendation_need_date: Any,
        actor_reference: str,
        clock: Callable[[], datetime] = _instant,
    ) -> HumanDecision:
        """Approve the deterministic ``RecommendedPurchaseQty`` as-is (``§6`` items 2 / 4 / 6).

        Approval requires **all** of: a non-stale instance whose Analysis Run binding matches, an
        open (not stale / rejected / approved) instance, an explicitly matching grain, a non-empty
        actor-reference slot, and an applicable numeric deterministic recommendation.  A matching
        Analysis Run alone is never sufficient, and this method has no parameter that could carry an
        override quantity: the explicit override path is
        :meth:`approve_with_override` (``§10.4`` HD-3 Option A′ / ``§10.5`` C).
        """

        actor = self._require_actor(actor_reference)
        self._require_open(current_analysis_run)
        if self.recommendation is None or not self.recommendation.has_numeric_result:
            raise ReviewPreconditionError(
                "only a valid deterministic numeric recommendation can be approved as-is: this "
                "grain states no applicable numeric recommendation (§2.5.8 / §6 item 2)"
            )
        if (
            self.grain[0] != plant_id
            or self.grain[1] != material_code
            or self.grain[2] != recommendation_need_date
        ):
            raise ReviewConflictError(
                "the reviewed grain does not match the requested plant_id + material_code + "
                "RecommendationNeedDate, so this instance cannot decide for that grain (§6 item 2)"
            )

        recommended = self.recommendation.recommended_purchase_qty
        assert recommended is not None  # guarded by has_numeric_result above
        decision = HumanDecision(
            decision_kind=DECISION_APPROVE,
            grain=self.grain,
            analysis_run=self.analysis_run,
            deterministic_recommended_value=recommended,
            approved_value=recommended,
            override_flag=False,
            override_reason=NO_OVERRIDE_REASON,
            human_reason=None,
            evidence_references=self._evidence_references(),
            actor_reference=actor,
            decision_timestamp=clock(),
            review_projection_reference=self.review_projection_reference,
        )
        self._record(decision, REVIEW_APPROVED)
        return decision

    def approve_with_override(
        self,
        *,
        current_analysis_run: AnalysisRunContext,
        plant_id: Any,
        material_code: Any,
        recommendation_need_date: Any,
        override_quantity: Any,
        reason: Any,
        actor_reference: str,
        clock: Callable[[], datetime] = _instant,
    ) -> HumanDecision:
        """Approve an **explicit Human quantity override** of ``RecommendedPurchaseQty`` (``§10.4``).

        The override input is an **exact finite base-10 decimal string**, parsed with the existing
        exact quantity machinery (``§10.4`` A / ``§10.5`` D).  A usable override requires **all** of:

        * a non-empty actor-reference slot;
        * a non-stale, open instance whose Analysis Run binding matches and whose grain matches;
        * an applicable numeric deterministic recommendation;
        * ``override_quantity`` parses as an exact base-10 decimal and is **strictly positive**
          (``§10.4`` B: ``= 0`` and ``< 0`` are invalid; a Human who decides not to purchase uses
          :meth:`reject`);
        * the value is **>= the existing ``ApplicableMOQ``** (``§10.4`` C: the POC does not let an
          override bypass the MOQ);
        * a non-empty Human reason (``§10.4`` F).

        Nothing is ever coerced: no float, rounding, quantization, truncation, clamping,
        normalization, absolute value or auto-adjust-to-MOQ is applied, and no new precision or scale
        semantics is introduced.  Any violation fails closed at the **decision level** -- no
        ``HumanDecision`` is produced, this instance stays in review-in-progress, the deterministic
        result is untouched, and a corrected input may retry.

        The resulting record states the override truthfully: the decision kind stays
        :data:`DECISION_APPROVE`, ``override_flag`` is ``True``, ``approved_value`` is the exact
        Human override value, the deterministic recommended value is preserved, and the Human reason
        is preserved.  This holds even when the override value happens to equal the deterministic
        recommendation: an explicit override path is never silently rewritten into approve-as-is.
        No ``modify`` decision kind, canonical enum or business status is introduced.
        """

        actor = self._require_actor(actor_reference)
        self._require_open(current_analysis_run)
        if self.recommendation is None or not self.recommendation.has_numeric_result:
            raise ReviewPreconditionError(
                "only a grain with an applicable numeric deterministic recommendation can be "
                "overridden: this grain states no applicable numeric recommendation "
                "(§2.5.8 / §6 item 2)"
            )
        if (
            self.grain[0] != plant_id
            or self.grain[1] != material_code
            or self.grain[2] != recommendation_need_date
        ):
            raise ReviewConflictError(
                "the reviewed grain does not match the requested plant_id + material_code + "
                "RecommendationNeedDate, so this instance cannot decide for that grain (§6 item 2)"
            )
        if not isinstance(reason, str) or not reason.strip():
            raise ReviewPreconditionError(
                "an override approval requires a Human reason (§10.4 F / §6 item 4); an empty or "
                "missing reason is not a decision"
            )

        parsed = parse_exact_quantity(override_quantity)
        if parsed is None:
            raise ReviewPreconditionError(
                "the Human override quantity must be an exact finite base-10 decimal string "
                "(§10.4 A); a missing, non-string, malformed, scientific-notation, locale-formatted "
                "or otherwise unrepresentable value is not a usable override and no Human decision "
                "is recorded"
            )
        if parsed.units <= 0:
            raise ReviewPreconditionError(
                "the Human override quantity must be strictly positive (§10.4 B): zero and negative "
                "values are invalid, and a decision not to purchase is expressed with reject()"
            )

        applicable_moq = self.recommendation.applicable_moq
        if applicable_moq is None:
            raise ReviewPreconditionError(
                "an override cannot be validated against the applicable MOQ because this "
                "recommendation carries no ApplicableMOQ at all (§10.4 C); no Human decision is "
                "recorded and no value is defaulted"
            )
        if parsed < applicable_moq:
            raise ReviewPreconditionError(
                "the Human override quantity must satisfy the existing ApplicableMOQ constraint "
                "(§10.4 C): the POC does not let an override bypass the MOQ, and the deterministic "
                "ApplicableMOQ is never modified, defaulted or adjusted"
            )

        recommended = self.recommendation.recommended_purchase_qty
        assert recommended is not None  # guarded by has_numeric_result above
        decision = HumanDecision(
            decision_kind=DECISION_APPROVE,
            grain=self.grain,
            analysis_run=self.analysis_run,
            deterministic_recommended_value=recommended,
            approved_value=_exact_fraction(parsed),
            override_flag=True,
            override_reason=_INTERNAL_OVERRIDE_REASON,
            human_reason=reason,
            evidence_references=self._evidence_references(),
            actor_reference=actor,
            decision_timestamp=clock(),
            review_projection_reference=self.review_projection_reference,
        )
        self._record(decision, REVIEW_APPROVED)
        return decision

    def reject(
        self,
        *,
        current_analysis_run: AnalysisRunContext,
        reason: str,
        actor_reference: str,
        clock: Callable[[], datetime] = _instant,
    ) -> HumanDecision:
        """Reject the review instance; the reason is required (``§6`` item 7).

        Rejection terminates this instance and triggers no deterministic recomputation.  There is no
        parameter here that could carry a quantity: rejection states no approved value.
        """

        actor = self._require_actor(actor_reference)
        self._require_open(current_analysis_run)
        if not isinstance(reason, str) or not reason.strip():
            raise ReviewPreconditionError(
                "a reject decision requires a Human reason (§6 item 7); an empty or missing reason "
                "is not a decision"
            )
        decision = HumanDecision(
            decision_kind=DECISION_REJECT,
            grain=self.grain,
            analysis_run=self.analysis_run,
            deterministic_recommended_value=self.recommended_purchase_qty,
            approved_value=None,
            override_flag=False,
            override_reason=NO_OVERRIDE_REASON,
            human_reason=reason,
            evidence_references=self._evidence_references(),
            actor_reference=actor,
            decision_timestamp=clock(),
            review_projection_reference=self.review_projection_reference,
        )
        self._record(decision, REVIEW_REJECTED)
        return decision

    def _record(self, decision: HumanDecision, status: str) -> None:
        object.__setattr__(self, "decision", decision)
        object.__setattr__(self, "_status", status)

    def _evidence_references(self) -> tuple[Mapping[str, Any], ...]:
        """The decision's truthful evidence references, taken from the reviewed projection.

        ``§6`` item 4 registers these as **references**: the two existing upstream result references,
        plus the Supplier Risk evidence **identity**.  The Supplier Risk risk values the Human
        reviewed are deliberately excluded -- they are not identity, they stay in the review
        projection, and the decision links to that projection through
        ``review_projection_reference``.
        """

        references: list[Mapping[str, Any]] = []
        for name in ("shortage_reference", "policy_input_reference"):
            item = self.projection.references.get(name)
            if item is not None:
                references.append(_deep_freeze({key: item[key] for key in REFERENCE_KEYS_UPSTREAM}))
        for card in self.projection.supplier_risk_evidence:
            references.append(
                _deep_freeze({key: card[key] for key in REFERENCE_KEYS_SUPPLIER_RISK})
            )
        return tuple(references)

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_question": REVIEW_QUESTION,
            "grain": _grain_payload(*self.grain),
            "analysis_run": {
                "analysis_run_id": self.analysis_run.analysis_run_id,
                "snapshot_package_identity": self.analysis_run.snapshot_package_identity,
                "accepted_content_view_digest": self.analysis_run.accepted_content_view_digest,
                "analysis_date": self.analysis_run.analysis_date,
            },
            "review_projection_reference": self.review_projection_reference,
            "instance_condition": self._status,
            "stale": self._stale_marker is not None,
            "override_flag": False,
            "override_reason": NO_OVERRIDE_REASON,
            "decision": None if self.decision is None else self.decision.to_dict(),
            "notes": list(self.notes),
        }


def open_review(
    recommendations: ProcurementRecommendationResult,
    *,
    plant_id: Any,
    material_code: Any,
    actor_reference: str,
    supplier_risk: Any | None = None,
    explanation: "ExplanationResult | None" = None,
) -> ReviewInstance:
    """Open a **new** review instance for one recommendation grain (``§6`` items 3 / 6 / 8).

    A new review instance is created when the Analysis Run changes (replacement / new-instance
    creation): the previous instance stays stale and unchanged, and this new one starts open.  This
    function never mutates a deterministic result, never persists anything and never contacts a
    provider.
    """

    ReviewInstance._require_actor(actor_reference)
    projection = build_review_projection(
        recommendations,
        plant_id=plant_id,
        material_code=material_code,
        supplier_risk=supplier_risk,
        explanation=explanation,
    )
    return ReviewInstance(
        analysis_run=recommendations.analysis_run,
        projection=projection,
        actor_reference=actor_reference,
        recommendation=recommendations.for_family(plant_id, material_code),
    )


__all__ = [
    "DECISION_APPROVE",
    "DECISION_RECORD_FIELDS",
    "DECISION_REJECT",
    "EVIDENCE_KIND_SUPPLIER_RISK",
    "EVIDENCE_KIND_UPSTREAM_RESULT",
    "EXPLANATION_BOUND",
    "EXPLANATION_KEYS",
    "EXPLANATION_UNAVAILABLE_FOR_REVIEW",
    "HumanDecision",
    "NO_OVERRIDE_REASON",
    "NOTE_REVIEW_EXPLANATION_STALE",
    "NOTE_REVIEW_NO_NUMERIC_RECOMMENDATION",
    "NOTE_REVIEW_NO_RECOMMENDATION",
    "PROJECTION_KEYS",
    "PROJECTION_NO_RECOMMENDATION",
    "PROJECTION_RECOMMENDATION",
    "REFERENCE_KEYS_SUPPLIER_RISK",
    "REFERENCE_KEYS_UPSTREAM",
    "REVIEW_APPROVED",
    "REVIEW_FACT_FIELDS",
    "REVIEW_GRAIN_FIELDS",
    "REVIEW_OPEN",
    "REVIEW_QUESTION",
    "REVIEW_REJECTED",
    "REVIEW_STALE",
    "ReviewConflictError",
    "ReviewError",
    "ReviewInstance",
    "ReviewPreconditionError",
    "ReviewProjection",
    "analysis_run_differences",
    "analysis_run_is_current",
    "build_review_projection",
    "open_review",
    "payload_to_plain",
    "projection_reference",
]
