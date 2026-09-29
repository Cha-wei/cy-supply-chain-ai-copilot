"""Provider-agnostic P0 AI Explanation seam (non-canonical runtime core).

Registered authority:

* ``ADR-002`` (``ACCEPTED``) -- P0 AI Explanation minimum runtime: in-process, a **single**
  provider-agnostic call, provider-neutral seam, no Agent Framework / Tool Protocol / MCP /
  Web / API / database / persistence / RAG / Vector DB / HITL / Draft / ranking, and
  ``LLM does not create business truth``.
* ``POC Design v0.2`` §5.1 / §5.2 (core principle and the controlled chain), §5.5 (the four
  response **meanings** -- explicitly *not* an API / JSON / UI schema), §5.6 ／ §5.7 ／ §5.8
  (evidence fidelity, no unsupported fact, partial answer), §5.9 (tool failure), §5.12 (the
  deterministic / LLM boundary).
* ``POC Design v0.2`` §7.1 (Secret Handling minimum contract, Issue #180): the raw
  credential never becomes a business-side parameter of this seam.  This module therefore
  contains **no** credential handling, **no** environment access and **no** network access.

Evidence-fidelity protection (why this seam is a **selection** contract)
-----------------------------------------------------------------------

A structurally valid provider answer that *misstates* a deterministic quantity -- e.g.
narrating ``ShortageQty = 100`` while the projection registers ``30`` -- would violate
§5.3 Q3, §5.5 (Recommendation ≠ Approved Decision), §5.6, §5.7 and the ``LLM does not create
business truth`` invariant.  Treating that as acceptable because the provider "should" be
well behaved, or because a prompt or a future AI Eval will fix it, is not a guarantee.

This seam therefore does not accept provider prose at all.  The provider may only **select**
registered content:

* ``answer_kind`` -- one literal from the closed :data:`ANSWER_KINDS` registry (``§5.3`` Q3
  answer shapes); the registry is **read-only**, so a caller cannot widen the accepted
  vocabulary; the runtime renders the sentence from the **projection's own values**;
* ``evidence`` -- an ordered list of **projected fact names** whose runtime-rendered
  ``"<name> = <value>"`` lines form the Evidence section; every Q3 kind requires all five
  registered quantities, so no kind can silently drop one of them;
* ``uncertainty`` -- must be **empty**: this seam is only called for a ``COMPLETE`` Q3
  projection, and a deterministic fact is never relabelled as uncertain by the provider;
* ``human_decision_required`` -- the boolean ``True``: the provider must *assert* the
  requirement, and the runtime renders the registered reminder sentence.  A procurement
  recommendation is never an approved decision (§5.5), so ``False`` or any free text fails
  closed.

Every value in the assembled artifact therefore comes from the projection or from a
registered literal, never from provider wording, so an unsupported fact, a mutated quantity,
a swapped role or an invented approval cannot be expressed.  The validation is deliberately
narrow and Q3-specific; it is **not** a general NLP fact checker and no AI Eval is involved.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from types import MappingProxyType
from typing import Protocol

#: Execution outcome: the provider was called once and returned a usable response.
OUTCOME_EXPLAINED: str = "EXPLAINED"
#: Execution outcome: the family states no recommendation (reliable valid absence misses by design).
OUTCOME_NO_RECOMMENDATION_BY_DESIGN: str = "NO_RECOMMENDATION_BY_DESIGN"
#: Execution outcome: the family states no recommendation and is not a reliable valid absence.
OUTCOME_RECOMMENDATION_UNAVAILABLE: str = "RECOMMENDATION_UNAVAILABLE"
#: Execution outcome: the recommendation is ``DATA_INCOMPLETE`` / required facts are absent.
OUTCOME_RECOMMENDATION_INCOMPLETE: str = "RECOMMENDATION_INCOMPLETE"
#: Execution outcome: the provider raised, so no explanation could be obtained.
OUTCOME_PROVIDER_UNAVAILABLE: str = "PROVIDER_UNAVAILABLE"
#: Execution outcome: the provider answered, but the answer is not usable.
OUTCOME_RESPONSE_UNACCEPTABLE: str = "RESPONSE_UNACCEPTABLE"

#: The exact keys a provider selection may carry.
RESPONSE_KEYS: tuple[str, ...] = (
    "answer_kind",
    "evidence",
    "uncertainty",
    "human_decision_required",
)

#: The registered reminder the runtime renders for a procurement recommendation (§5.5).
HUMAN_DECISION_REQUIRED_TEXT: str = (
    "需要 Human 决策：这是推荐采购量，不是已批准的采购量，也不构成采购订单或任何审批状态。"
)

#: The deterministic, provider-independent wording used when no explanation is available.
NOTE_AI_EXPLANATION_UNAVAILABLE: str = "AI explanation unavailable"
NOTE_INCOMPLETE: str = (
    "AI explanation unavailable: the consumed deterministic recommendation is "
    "DATA_INCOMPLETE, so no reliable purchase-quantity explanation can be formed (§5.5 / §5.8)"
)
NOTE_NO_RECOMMENDATION_BY_DESIGN: str = (
    "AI explanation unavailable: a reliable never-short horizon produces no purchase "
    "recommendation by design (§4.4.87)"
)
NOTE_RECOMMENDATION_UNAVAILABLE: str = (
    "AI explanation unavailable: this result states no purchase recommendation for the "
    "requested family"
)
NOTE_PROVIDER_UNAVAILABLE: str = (
    "AI explanation unavailable: the explanation provider could not be reached"
)
NOTE_RESPONSE_UNACCEPTABLE: str = (
    "AI explanation unavailable: the explanation provider returned a selection that is not "
    "usable as a Q3 explanation (§5.5 / §5.6 / §5.7)"
)


@dataclass(frozen=True, slots=True)
class AnswerKind:
    """One registered Q3 answer shape.

    ``required_evidence`` names the quantities the sentence rests on, so the provider cannot
    hide a quantity it was supposed to explain.  ``precondition`` is the registered exact
    relation the projection must satisfy for the sentence to be true; a selection whose
    precondition does not hold is not usable.
    """

    literal: str
    required_evidence: tuple[str, ...]
    template: str
    relation: str


#: The closed Q3 answer-kind registry (``§5.3`` Q3).  The literals are runtime identifiers;
#: the sentences are rendered by the runtime from the projection's own values.
#:
#: The registry is a read-only :class:`~types.MappingProxyType`, because the fidelity
#: guarantee rests on ``answer_kind`` really belonging to a **closed** registry: if a caller
#: could insert or replace an entry, the guarantee would not hold.
ANSWER_KINDS: Mapping[str, AnswerKind] = MappingProxyType(
    {
        "MOQ_RAISED_RECOMMENDATION_ABOVE_SHORTAGE": AnswerKind(
            literal="MOQ_RAISED_RECOMMENDATION_ABOVE_SHORTAGE",
            required_evidence=(
                "ShortageQty",
                "BasePurchaseNeed",
                "ApplicableMOQ",
                "MOQAdjustmentQty",
                "RecommendedPurchaseQty",
            ),
            template=(
                "实际缺口为 {ShortageQty}；基础采购需求为 {BasePurchaseNeed}；"
                "由于适用 MOQ 为 {ApplicableMOQ}，建议采购量被上调为 {RecommendedPurchaseQty}"
                "（MOQAdjustmentQty 为 {MOQAdjustmentQty}）。"
            ),
            relation="recommended_above_shortage",
        ),
        "RECOMMENDATION_EQUALS_SHORTAGE": AnswerKind(
            literal="RECOMMENDATION_EQUALS_SHORTAGE",
            required_evidence=(
                "ShortageQty",
                "BasePurchaseNeed",
                "ApplicableMOQ",
                "MOQAdjustmentQty",
                "RecommendedPurchaseQty",
            ),
            template=(
                "实际缺口为 {ShortageQty}；基础采购需求为 {BasePurchaseNeed}；"
                "适用 MOQ 为 {ApplicableMOQ}，建议采购量 {RecommendedPurchaseQty} "
                "与缺口一致、未发生上调，MOQAdjustmentQty 为 {MOQAdjustmentQty}。"
            ),
            relation="recommended_equals_shortage",
        ),
    }
)

#: The registered answer-kind literals, in registry order.
ANSWER_KIND_LITERALS: tuple[str, ...] = tuple(ANSWER_KINDS)


class ExplanationProvider(Protocol):
    """The provider-agnostic single-call seam (``ADR-002``).

    The provider receives **only** the read-only explanation projection payload and returns a
    **selection** that :func:`validate_provider_response` must accept: an ``answer_kind`` from
    the closed registry, projected fact names for ``evidence`` ／ ``uncertainty`` and the
    required-human-decision assertion.  It is called at most once per explanation request.
    No credential is ever passed here (§7.1 ``S-4``): a real hosted adapter obtains and uses
    its credential inside its own integration boundary.
    """

    def explain(self, projection: Mapping[str, object]) -> object:  # pragma: no cover
        """Return a selection over the projection (never prose)."""

        ...


@dataclass(frozen=True, slots=True)
class ExplanationResponse:
    """The user-facing explanation artifact -- a **non-canonical runtime artifact**.

    It carries only the four ``§5.5`` response meanings (Answer ／ Evidence ／
    Uncertainty・Missing Data ／ Human Decision Required).  Every string in it is rendered by
    the runtime from the projection's registered values or from a registered literal, so no
    provider wording reaches the artifact.  It adds **no** business status, no canonical
    entity ／ field ／ grain ／ enum and no approval state.
    """

    answer: str
    evidence: tuple[str, ...]
    uncertainty: tuple[str, ...]
    human_decision_required: str

    def to_dict(self) -> dict[str, object]:
        return {
            "answer": self.answer,
            "evidence": list(self.evidence),
            "uncertainty": list(self.uncertainty),
            "human_decision_required": self.human_decision_required,
        }


@dataclass(frozen=True, slots=True)
class ExplanationResult:
    """One explanation attempt: the projection, the execution outcome and the artifact.

    ``outcome`` is an **execution** outcome (:data:`OUTCOME_*`), never a business status.
    ``response`` is ``None`` whenever no reliable explanation exists; ``availability_note``
    then states the deterministic, provider-independent reason.  ``missing_evidence`` carries
    only values that already exist in the consumed deterministic result (root conditions and
    the registered issue findings), never a fabricated one.
    """

    question: str
    outcome: str
    projection: Mapping[str, object]
    provider_invoked: bool
    availability_note: str | None = None
    response: ExplanationResponse | None = None
    missing_evidence: tuple[Mapping[str, object], ...] = ()
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def explained(self) -> bool:
        """Whether a usable explanation response was produced."""

        return self.outcome == OUTCOME_EXPLAINED and self.response is not None

    def to_dict(self) -> dict[str, object]:
        return {
            "question": self.question,
            "outcome": self.outcome,
            "provider_invoked": self.provider_invoked,
            "availability_note": self.availability_note,
            "projection": copy.deepcopy(dict(self.projection)),
            "response": None if self.response is None else self.response.to_dict(),
            "missing_evidence": [dict(item) for item in self.missing_evidence],
            "notes": list(self.notes),
        }


def render_fact_text(payload: object) -> str | None:
    """Render one projected quantity exactly, or answer ``None`` when it is not renderable.

    Registered payloads are exact rational payloads (``{"numerator", "denominator"}``) or
    exact decimal text.  A rational renders as ``"30"`` when the denominator is ``1`` and as
    ``"1/3"`` otherwise -- never as a rounded or floating-point number.
    """

    if isinstance(payload, str):
        return payload or None
    if isinstance(payload, Mapping):
        numerator = payload.get("numerator")
        denominator = payload.get("denominator")
        if isinstance(numerator, int) and isinstance(denominator, int) and denominator > 0:
            return str(numerator) if denominator == 1 else f"{numerator}/{denominator}"
    return None


def _fact_values(projection: Mapping[str, object]) -> dict[str, str]:
    facts = projection.get("facts")
    if not isinstance(facts, Mapping):
        return {}
    values: dict[str, str] = {}
    for name, payload in facts.items():
        text = render_fact_text(payload)
        if text is not None:
            values[str(name)] = text
    return values


def _exact_fraction(text: str) -> Fraction | None:
    try:
        return Fraction(text)
    except (ValueError, ZeroDivisionError):
        return None


def _relation_holds(relation: str, values: Mapping[str, str]) -> bool:
    shortage = _exact_fraction(values.get("ShortageQty", ""))
    recommended = _exact_fraction(values.get("RecommendedPurchaseQty", ""))
    moq = _exact_fraction(values.get("ApplicableMOQ", ""))
    if shortage is None or recommended is None or moq is None:
        return False
    if relation == "recommended_above_shortage":
        return shortage < recommended and recommended == moq
    if relation == "recommended_equals_shortage":
        return recommended == shortage
    return False


def _name_list(value: object) -> tuple[str, ...] | None:
    """A provider selection list of projected fact names, or ``None`` when unusable."""

    if isinstance(value, str) or not isinstance(value, Sequence):
        return None
    names: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            return None
        names.append(item)
    return tuple(names)


def validate_provider_response(
    raw: object, projection: Mapping[str, object]
) -> ExplanationResponse | None:
    """Validate one provider selection and assemble the artifact, or fail closed.

    The response is usable only when it is a mapping carrying **exactly** the four registered
    keys, whose ``answer_kind`` is one of :data:`ANSWER_KINDS`, whose ``evidence`` is a
    non-empty list of projected fact names covering that kind's required evidence, whose
    ``uncertainty`` is **empty** (this seam is only called for a ``COMPLETE`` Q3 projection,
    so no deterministic fact may be relabelled as uncertain), whose
    ``human_decision_required`` is the boolean ``True``, and whose registered relation
    actually holds for this projection.

    Everything else -- extra keys, an unregistered kind, a fact name that was not projected,
    a value smuggled into a name, a mutated quantity, a missing required quantity, a relation
    that contradicts the projection, an invented uncertainty entry, or an attempt to state
    that no human decision is needed -- is **not** usable, and the runtime then surfaces no
    explanation at all.  The artifact itself is assembled here from the projection, so no
    provider wording can enter it.
    """

    if not isinstance(raw, Mapping):
        return None
    if set(raw.keys()) != set(RESPONSE_KEYS):
        return None

    kind = ANSWER_KINDS.get(raw["answer_kind"]) if isinstance(raw["answer_kind"], str) else None
    if kind is None:
        return None

    values = _fact_values(projection)
    evidence = _name_list(raw["evidence"])
    if evidence is None or not evidence:
        return None
    uncertainty = _name_list(raw["uncertainty"])
    if uncertainty is None or uncertainty:
        return None
    if raw["human_decision_required"] is not True:
        return None

    for name in evidence:
        if name not in values:
            return None
    if len(set(evidence)) != len(evidence):
        return None
    if not set(kind.required_evidence) <= set(evidence):
        return None
    if not _relation_holds(kind.relation, values):
        return None

    return ExplanationResponse(
        answer=kind.template.format(**values),
        evidence=tuple(f"{name} = {values[name]}" for name in evidence),
        uncertainty=(),
        human_decision_required=HUMAN_DECISION_REQUIRED_TEXT,
    )


def provider_payload(projection: Mapping[str, object]) -> dict[str, object]:
    """A defensive copy of the projection handed to a provider.

    The provider can therefore never mutate the projection the runtime keeps in its result,
    and the runtime never hands a provider any object other than the projection itself.
    """

    return copy.deepcopy(dict(projection))


__all__ = [
    "ANSWER_KINDS",
    "ANSWER_KIND_LITERALS",
    "AnswerKind",
    "ExplanationProvider",
    "ExplanationResponse",
    "ExplanationResult",
    "HUMAN_DECISION_REQUIRED_TEXT",
    "NOTE_AI_EXPLANATION_UNAVAILABLE",
    "NOTE_INCOMPLETE",
    "NOTE_NO_RECOMMENDATION_BY_DESIGN",
    "NOTE_PROVIDER_UNAVAILABLE",
    "NOTE_RECOMMENDATION_UNAVAILABLE",
    "NOTE_RESPONSE_UNACCEPTABLE",
    "OUTCOME_EXPLAINED",
    "OUTCOME_NO_RECOMMENDATION_BY_DESIGN",
    "OUTCOME_PROVIDER_UNAVAILABLE",
    "OUTCOME_RECOMMENDATION_INCOMPLETE",
    "OUTCOME_RECOMMENDATION_UNAVAILABLE",
    "OUTCOME_RESPONSE_UNACCEPTABLE",
    "RESPONSE_KEYS",
    "provider_payload",
    "render_fact_text",
    "validate_provider_response",
]
