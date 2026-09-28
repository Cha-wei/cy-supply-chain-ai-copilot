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

What this module deliberately is not: it selects no provider and no model, performs no HTTP
or network call, adds no dependency, and defines no business status.  The
:data:`OUTCOME_*` literals are **execution outcomes of the explanation runtime** (the same
kind of fact as ``PipelineStage.entered``); they are never a business status and must never
be presented as, or substituted for, the registered business ``DATA_INCOMPLETE`` literal.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
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
#: Execution outcome: the provider answered, but the answer is not a usable response.
OUTCOME_RESPONSE_UNACCEPTABLE: str = "RESPONSE_UNACCEPTABLE"

#: The exact keys a provider response may carry (``§5.5`` meanings only).
RESPONSE_KEYS: tuple[str, ...] = (
    "answer",
    "evidence",
    "uncertainty",
    "human_decision_required",
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
    "AI explanation unavailable: the explanation provider returned a response that is not "
    "usable as an explanation (§5.5)"
)


class ExplanationProvider(Protocol):
    """The provider-agnostic single-call seam (``ADR-002``).

    The provider receives **only** the read-only explanation projection payload and returns
    an object that :func:`validate_provider_response` must accept.  It is called at most
    once per explanation request.  No credential is ever passed here (§7.1 ``S-4``): a real
    hosted adapter obtains and uses its credential inside its own integration boundary.
    """

    def explain(self, projection: Mapping[str, object]) -> object:  # pragma: no cover
        """Return a response carrying the four ``§5.5`` meanings."""

        ...


@dataclass(frozen=True, slots=True)
class ExplanationResponse:
    """The user-facing explanation artifact -- a **non-canonical runtime artifact**.

    It carries only the four ``§5.5`` response meanings (Answer ／ Evidence ／
    Uncertainty・Missing Data ／ Human Decision Required).  It adds **no** business status,
    no canonical entity ／ field ／ grain ／ enum and no approval state.
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


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _text_sequence(value: object) -> tuple[str, ...] | None:
    """Normalise a provider text field, or answer ``None`` when it is not usable."""

    if isinstance(value, str):
        text = _non_empty_text(value)
        return None if text is None else (text,)
    if isinstance(value, Sequence):
        parts: list[str] = []
        for item in value:
            text = _non_empty_text(item)
            if text is None:
                return None
            parts.append(text)
        return tuple(parts)
    return None


def validate_provider_response(raw: object) -> ExplanationResponse | None:
    """Accept an explanation response, or answer ``None`` so the caller fails closed.

    The minimal validation registered by this slice (``§5.5``): the response must be a
    mapping carrying **exactly** the four meaning keys, with a non-empty ``answer``, a
    non-empty ``evidence`` sequence, an ``uncertainty`` sequence (which may be empty when
    nothing is missing) and a non-empty ``human_decision_required``.  Anything else -- a
    bare string, a mapping with extra or missing keys, empty text, non-text members -- is
    **not** usable and is never surfaced as an explanation.
    """

    if not isinstance(raw, Mapping):
        return None
    if set(raw.keys()) != set(RESPONSE_KEYS):
        return None
    answer = _non_empty_text(raw["answer"])
    if answer is None:
        return None
    evidence = _text_sequence(raw["evidence"])
    if evidence is None or not evidence:
        return None
    uncertainty = _text_sequence(raw["uncertainty"])
    if uncertainty is None:
        return None
    human = _non_empty_text(raw["human_decision_required"])
    if human is None:
        return None
    return ExplanationResponse(
        answer=answer,
        evidence=evidence,
        uncertainty=uncertainty,
        human_decision_required=human,
    )


def provider_payload(projection: Mapping[str, object]) -> dict[str, object]:
    """A defensive copy of the projection handed to a provider.

    The provider can therefore never mutate the projection the runtime keeps in its result,
    and the runtime never hands a provider any object other than the projection itself.
    """

    return copy.deepcopy(dict(projection))


__all__ = [
    "ExplanationProvider",
    "ExplanationResponse",
    "ExplanationResult",
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
    "validate_provider_response",
]
