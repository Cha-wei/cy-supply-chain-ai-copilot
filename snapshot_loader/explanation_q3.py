"""``§5.3`` Q3 -- "Why is the recommended purchase quantity X?" runtime slice.

Registered authority:

* ``POC Design v0.2`` §5.3 **Q3** -- the answer must come from ``BR-PROCUREMENT-001`` and
  must keep ``ShortageQty`` ／ ``BasePurchaseNeed`` ／ ``ApplicableMOQ`` ／
  ``MOQAdjustmentQty`` ／ ``RecommendedPurchaseQty`` distinct; the registered prohibition is
  the reading ``"实际缺料 100"`` when the actual gap is ``30`` and the recommendation is
  ``100``.
* ``POC Design v0.2`` §5.5 (the four response meanings), §5.6 ／ §5.7 ／ §5.8 (evidence
  fidelity, no unsupported fact, partial answer), §5.12 (none of these values may be decided
  by the LLM).
* ``ADR-002`` -- minimum runtime shape: existing deterministic result -> read-only
  non-canonical projection -> provider-agnostic single call -> user-facing explanation, with
  a deterministic fail-closed path.
* ``POC Design v0.2`` §7.1 (Issue #180) -- this slice performs **no** credential handling,
  reads **no** environment and performs **no** network call; a hosted adapter is a separate
  later unit.

The projection is a **read-only, non-canonical selection** of already-registered values: the
five quantities are taken from the recommendation's **own registered serialization** (exact
rational payloads ／ exact decimal text), so nothing is recomputed, rounded, repaired,
defaulted or re-classified.  The projection never carries the accepted package, the pipeline
result, the analysis run or any unrelated pipeline field.
"""

from __future__ import annotations

from collections.abc import Mapping

from .explanation_seam import (
    NOTE_INCOMPLETE,
    NOTE_NO_RECOMMENDATION_BY_DESIGN,
    NOTE_PROVIDER_UNAVAILABLE,
    NOTE_RECOMMENDATION_UNAVAILABLE,
    NOTE_RESPONSE_UNACCEPTABLE,
    OUTCOME_EXPLAINED,
    OUTCOME_NO_RECOMMENDATION_BY_DESIGN,
    OUTCOME_PROVIDER_UNAVAILABLE,
    OUTCOME_RECOMMENDATION_INCOMPLETE,
    OUTCOME_RECOMMENDATION_UNAVAILABLE,
    OUTCOME_RESPONSE_UNACCEPTABLE,
    ExplanationProvider,
    ExplanationResult,
    provider_payload,
    validate_provider_response,
)
from .procurement_recommendation import (
    ProcurementRecommendation,
    ProcurementRecommendationResult,
)

#: The registered question identifier of this slice (``§5.3`` Q3).
Q3_QUESTION: str = "Q3"

#: The five ``§5.3`` Q3 quantities, in the registered order of the rule's own serialization.
Q3_FACT_FIELDS: tuple[str, ...] = (
    "ShortageQty",
    "BasePurchaseNeed",
    "ApplicableMOQ",
    "MOQAdjustmentQty",
    "RecommendedPurchaseQty",
)

#: The recommendation identity ／ grain a Q3 answer is about.
Q3_GRAIN_FIELDS: tuple[str, ...] = (
    "plant_id",
    "material_code",
    "RecommendationNeedDate",
)

#: Completeness states of the projection (runtime metadata, never a business status).
COMPLETENESS_COMPLETE: str = "COMPLETE"
COMPLETENESS_DATA_INCOMPLETE: str = "DATA_INCOMPLETE"
COMPLETENESS_RECOMMENDATION_NOT_STATED: str = "RECOMMENDATION_NOT_STATED"


def _grain_payload(registered: Mapping[str, object]) -> dict[str, object]:
    return {name: registered.get(name) for name in Q3_GRAIN_FIELDS}


def _completeness_payload(
    *,
    state: str,
    registered: Mapping[str, object] | None,
    missing_facts: tuple[str, ...],
    valid_absence: bool | None,
) -> dict[str, object]:
    source = registered or {}
    return {
        "state": state,
        "valid_absence": valid_absence,
        "outcome": source.get("outcome"),
        "missing_facts": list(missing_facts),
        "root_condition": source.get("root_condition"),
        "policy_root_condition": source.get("policy_root_condition"),
        "applicability_basis": source.get("applicability_basis"),
        "shortage_reference": source.get("shortage_reference"),
        "policy_input_reference": source.get("policy_input_reference"),
        "inherited_issues": list(source.get("inherited_issues") or ()),
        "rule_issues": list(source.get("rule_issues") or ()),
    }


def build_q3_projection(recommendation: ProcurementRecommendation) -> dict[str, object]:
    """Build the read-only Q3 projection of one deterministic recommendation.

    Only registered values are selected: the five quantities (through the recommendation's
    own registered serialization), the grain, the outcome, the root conditions, the existing
    references and the existing issue findings.  A quantity that the deterministic result
    does not state stays ``None`` -- the projection never fills, defaults or recomputes it.
    """

    registered = recommendation.to_dict()
    facts = {name: registered.get(name) for name in Q3_FACT_FIELDS}
    missing_facts = tuple(name for name in Q3_FACT_FIELDS if facts[name] is None)
    complete = recommendation.outcome is None and not missing_facts
    return {
        "question": Q3_QUESTION,
        "grain": _grain_payload(registered),
        "facts": facts,
        "completeness": _completeness_payload(
            state=COMPLETENESS_COMPLETE if complete else COMPLETENESS_DATA_INCOMPLETE,
            registered=registered,
            missing_facts=missing_facts,
            valid_absence=None,
        ),
    }


def _absent_projection(
    plant_id: object,
    material_code: object,
    *,
    valid_absence: bool,
) -> dict[str, object]:
    """The projection of a family for which the deterministic result states no recommendation."""

    return {
        "question": Q3_QUESTION,
        "grain": {
            "plant_id": plant_id,
            "material_code": material_code,
            "RecommendationNeedDate": None,
        },
        "facts": {name: None for name in Q3_FACT_FIELDS},
        "completeness": _completeness_payload(
            state=COMPLETENESS_RECOMMENDATION_NOT_STATED,
            registered=None,
            missing_facts=Q3_FACT_FIELDS,
            valid_absence=valid_absence,
        ),
    }


def _missing_evidence(projection: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    """The already-registered evidence that explains why no reliable answer exists.

    Only values the consumed result already carries are propagated: the unstated quantities,
    the registered root conditions (and, where present, the Phase B policy root condition),
    and the recommendation's own inherited ／ rule issue findings, verbatim.
    """

    completeness = projection["completeness"]
    assert isinstance(completeness, Mapping)
    entries: list[Mapping[str, object]] = []
    missing = completeness.get("missing_facts") or ()
    if missing:
        entries.append({"unavailable_facts": list(missing)})
    for name in ("root_condition", "policy_root_condition"):
        value = completeness.get(name)
        if value is not None:
            entries.append({name: value})
    for name in ("inherited_issues", "rule_issues"):
        for issue in completeness.get(name) or ():
            entries.append({"issue": issue})
    return tuple(entries)


def explain_q3(
    recommendations: ProcurementRecommendationResult,
    provider: ExplanationProvider,
    *,
    plant_id: object,
    material_code: object,
) -> ExplanationResult:
    """Explain one family's recommended purchase quantity (``§5.3`` Q3).

    The provider is called **at most once**, and only when the consumed deterministic
    recommendation is complete and carries all five registered quantities.  In every other
    case -- no recommendation stated, a reliable valid absence, ``DATA_INCOMPLETE`` or an
    absent quantity -- the runtime fails closed **without** calling the provider, states the
    deterministic reason and exposes the already-registered missing evidence instead of
    inventing a value or a narration.  A provider that raises or answers unusably also fails
    closed; the consumed deterministic recommendation is never modified.
    """

    recommendation = recommendations.for_family(plant_id, material_code)

    if recommendation is None:
        valid_absence = recommendations.is_valid_absence(plant_id, material_code)
        projection = _absent_projection(
            plant_id, material_code, valid_absence=valid_absence
        )
        return ExplanationResult(
            question=Q3_QUESTION,
            outcome=(
                OUTCOME_NO_RECOMMENDATION_BY_DESIGN
                if valid_absence
                else OUTCOME_RECOMMENDATION_UNAVAILABLE
            ),
            projection=projection,
            provider_invoked=False,
            availability_note=(
                NOTE_NO_RECOMMENDATION_BY_DESIGN
                if valid_absence
                else NOTE_RECOMMENDATION_UNAVAILABLE
            ),
            notes=(
                "the consumed result states no purchase recommendation for this family, so "
                "there is no recommended quantity to explain",
            ),
        )

    projection = build_q3_projection(recommendation)
    completeness = projection["completeness"]
    assert isinstance(completeness, Mapping)
    if completeness["state"] != COMPLETENESS_COMPLETE:
        return ExplanationResult(
            question=Q3_QUESTION,
            outcome=OUTCOME_RECOMMENDATION_INCOMPLETE,
            projection=projection,
            provider_invoked=False,
            availability_note=NOTE_INCOMPLETE,
            missing_evidence=_missing_evidence(projection),
            notes=(
                "the deterministic recommendation is not complete, so no reliable "
                "purchase-quantity explanation can be formed and no provider is called",
            ),
        )

    try:
        raw = provider.explain(provider_payload(projection))
    except Exception as error:  # noqa: BLE001 - any provider failure must fail closed
        return ExplanationResult(
            question=Q3_QUESTION,
            outcome=OUTCOME_PROVIDER_UNAVAILABLE,
            projection=projection,
            provider_invoked=True,
            availability_note=NOTE_PROVIDER_UNAVAILABLE,
            notes=(
                "the explanation provider raised "
                f"{type(error).__name__}; the deterministic recommendation is unchanged and "
                "no explanation is presented (the provider message is deliberately not "
                "propagated, §7.1 S-8)",
            ),
        )

    response = validate_provider_response(raw)
    if response is None:
        return ExplanationResult(
            question=Q3_QUESTION,
            outcome=OUTCOME_RESPONSE_UNACCEPTABLE,
            projection=projection,
            provider_invoked=True,
            availability_note=NOTE_RESPONSE_UNACCEPTABLE,
            notes=(
                "the provider response is not a usable explanation and is never surfaced "
                "(§5.5 / §5.7); the deterministic recommendation is unchanged",
            ),
        )

    return ExplanationResult(
        question=Q3_QUESTION,
        outcome=OUTCOME_EXPLAINED,
        projection=projection,
        provider_invoked=True,
        response=response,
        notes=(
            "the explanation paraphrases the projected deterministic quantities and adds no "
            "business fact (§5.6 / §5.7)",
        ),
    )


__all__ = [
    "COMPLETENESS_COMPLETE",
    "COMPLETENESS_DATA_INCOMPLETE",
    "COMPLETENESS_RECOMMENDATION_NOT_STATED",
    "Q3_FACT_FIELDS",
    "Q3_GRAIN_FIELDS",
    "Q3_QUESTION",
    "build_q3_projection",
    "explain_q3",
]
