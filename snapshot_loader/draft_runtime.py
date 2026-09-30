"""``Procurement Request Draft`` runtime — ephemeral, non-canonical, deterministic local assembly.

Registered authority:

* ``POC Design v0.2`` §6.1 -- the scoped semantic design (Issue #210, Human Decision ``D1`` -- ``D5``):
  the Draft's quantity authority, the ``RecommendationNeedDate`` and supplier boundary, the
  per-``ReviewInstance`` / per-``AnalysisRun`` lifecycle, the generation boundary, and the
  non-canonical artifact status.
* ``POC Design v0.2`` §10.6 -- the Issue #212 registration (Human Decision ``HD-DRAFT-R1`` /
  ``HD-DRAFT-R2``): the approved Option A runtime architecture boundary, the DoR / Code Start result
  (``PASS``; 7 PASS + 2 NOT TRIGGERED + 1 NOT REQUIRED; 0 blocking gate items), the scoped
  implementation authorization, and the Architecture re-entry conditions of §10.6 E.

What this module is
-------------------

```text
existing ReviewInstance / AnalysisRun
  -> initial ephemeral Draft          (quantity = deterministic RecommendedPurchaseQty)
  -> applicable HumanDecision exists  (Draft truthfully reflects approved_value)
  -> reject / stale / new AnalysisRun lifecycle
```

A :class:`ProcurementRequestDraft` is assembled **locally and deterministically** from values that
already exist on the review runtime.  Nothing is recomputed, filled, defaulted, parsed or inferred:
the initial quantity is the deterministic ``RecommendedPurchaseQty``; the quantity after a Human
decision is the *corresponding* ``HumanDecision.approved_value``; and the ``RecommendationNeedDate`` is
**derived** from the review grain, so the Draft holds no independent copy anyone could modify.

Deliberate boundaries (``HD-DRAFT-R1`` / §6.1):

* **no hosted LLM, no provider, no network, no egress, no credential.**  Draft wording / presentation is
  deterministic local assembly.  §6.1 D keeps its semantics for a *future* LLM wording, but hosted LLM
  wording is out of scope for this tranche and would require re-entering the Architecture / egress gate
  (§10.6 E) without inheriting ``ADR-002``.
* **no persistence.**  A Draft is an in-process runtime object; nothing is written to disk, to a
  database or to any durable business state (durable audit belongs to §8 and is not implemented here).
* **no identity or permission enforcement.**  This module performs no role / data-scope /
  Tool-permission enforcement and claims none (§7 stays ``DESIGN PENDING``).
* **no new canonical vocabulary.**  The Draft is a **non-canonical runtime artifact**, not a canonical
  entity / field / grain / enum / business status.  Its ``DRAFT`` state marker is the registered
  ``DRAFT`` marker, and it must never be described as an ERP Purchase Request, a Purchase Order, a
  submitted record or production execution.
* **no supplier.**  A supplier identity is **absent** by construction: the Draft has no supplier field
  at all, the Supplier Risk evidence remains review evidence, and supplier selection / ranking stays
  ``OUT OF SCOPE``.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from .hitl_review import (
    DECISION_APPROVE,
    DECISION_REJECT,
    HumanDecision,
    ReviewInstance,
    ReviewPreconditionError,
    analysis_run_differences,
)

#: The registered ``DRAFT`` state marker (``§3.6`` / ``§5.15`` / ``§6.1`` A).  A Draft always states it,
#: so it is never presented as a formal purchase request or as an approved business record.
DRAFT_MARKER: str = "DRAFT"

#: The draft-state token of an approved Draft.  This is an **internal runtime literal** used only by
#: :meth:`ProcurementRequestDraft.draft_state`; it is deliberately *not* exported as public surface and
#: introduces no canonical enum or business status.
_APPROVED_STATE: str = "APPROVED"

#: The draft-state token of a rejected Draft.  Internal runtime literal, same reasoning as above.
_REJECTED_STATE: str = "REJECTED"

#: The draft-state token of a Draft carrying a decision of an unregistered kind.  Internal literal for
#: defensive completeness only: the registered kinds are :data:`~.hitl_review.DECISION_APPROVE` and
#: :data:`~.hitl_review.DECISION_REJECT`, and no new kind is introduced here.
_UNDECIDED_STATE: str = "UNDECIDED"


class DraftError(ReviewPreconditionError):
    """The invocation may not bind this decision to this Draft (``§6.1`` C / ``§10.6`` D)."""


def _rational_payload(value: Fraction | None) -> dict[str, int] | None:
    """The lossless exact payload of one quantity, or ``None`` when unstated.

    Quantities are rendered exactly (``§4.3.25`` C-5): no rounding, quantization, truncation or float
    conversion is applied anywhere in this module.
    """

    if value is None:
        return None
    return {"numerator": value.numerator, "denominator": value.denominator}


def _require_identity(review: ReviewInstance, decision: HumanDecision) -> None:
    """Reject a decision that is not this review's own decision for this exact grain and run.

    ``§6.1`` C requires an approved Draft to be **bound to the corresponding ``HumanDecision``** and
    ``§6.1`` A requires a new ``AnalysisRun`` to yield a new instance and a new Draft.  A decision
    whose ``analysis_run``, grain or ``review_projection_reference`` does not match this review
    instance therefore belongs to a different review and is never consumed.
    """

    differences = analysis_run_differences(decision.analysis_run, review.analysis_run)
    if differences:
        raise DraftError(
            "this Human decision was taken under a different Analysis Run "
            f"({', '.join(differences)} differ), so it cannot be reflected by this Draft: a new "
            "Analysis Run requires a new review instance and a new Draft, and an earlier decision is "
            "never inherited (§6.1 A / C)"
        )
    if decision.grain != review.grain:
        raise DraftError(
            "this Human decision belongs to a different recommendation grain, so it cannot be "
            "reflected by this Draft (§6.1 A / C)"
        )
    if decision.review_projection_reference != review.review_projection_reference:
        raise DraftError(
            "this Human decision reviewed a different review projection, so it is not the decision "
            "corresponding to this Draft (§6.1 C)"
        )


@dataclass(frozen=True, slots=True)
class ProcurementRequestDraft:
    """One ephemeral, non-canonical ``Procurement Request Draft`` of one review instance (``§6.1``).

    The Draft is **immutable** and **ephemeral**: it lives only as this in-process object, and binding
    a Human decision produces a **new** Draft rather than rewriting this one, so a formed artifact can
    never be silently re-pointed at another value or another decision.

    Its quantity is **always** derived from exactly one of two already-registered sources:

    * no applicable Human decision yet -- the deterministic ``RecommendedPurchaseQty`` of the reviewed
      recommendation (``§6.1`` A: an initial Draft may rest on the deterministic result alone, and no
      ``HumanDecision`` is required or may be fabricated);
    * an applicable Human decision -- that decision's ``approved_value``, which is either the
      deterministic recommendation (approve-as-is) or the explicit Human override value (``§10.4``);
      the value is read from the ``HumanDecision`` and is never re-parsed, recomputed or inferred from
      an override reason (``§6.1`` D).

    ``RecommendationNeedDate`` is not stored: it is derived from the review grain on every access, so
    neither this Draft nor any renderer can modify it (``§6.1`` B).
    """

    review: ReviewInstance
    decision: HumanDecision | None = None

    # --- registered identity --------------------------------------------------------------

    @property
    def marker(self) -> str:
        """The registered ``DRAFT`` marker this artifact always states."""

        return DRAFT_MARKER

    @property
    def analysis_run(self):
        """The review instance's existing ``AnalysisRunContext`` binding (``§6.1`` C)."""

        return self.review.analysis_run

    @property
    def grain(self) -> tuple[Any, Any, Any]:
        """The reviewed recommendation grain, unchanged."""

        return self.review.grain

    @property
    def recommendation_need_date(self) -> Any:
        """``RecommendationNeedDate`` -- **derived read-only** from the review grain (``§6.1`` B)."""

        return self.review.grain[2]

    @property
    def quantity(self) -> Fraction | None:
        """The Draft quantity: the decision's ``approved_value``, else the deterministic recommendation.

        ``None`` only when the reviewed grain states no numeric recommendation at all (a valid absence
        or a ``DATA_INCOMPLETE`` recommendation); nothing is ever defaulted or invented.
        """

        if self.decision is not None:
            return self.decision.approved_value
        return self.review.recommended_purchase_qty

    @property
    def deterministic_recommended_value(self) -> Fraction | None:
        """The deterministic ``RecommendedPurchaseQty`` the reviewed recommendation states."""

        return self.review.recommended_purchase_qty

    # --- lifecycle ------------------------------------------------------------------------

    def is_stale(self, current_analysis_run) -> bool:
        """Whether this Draft's review instance is stale under ``current_analysis_run``.

        The judgement is delegated to the review instance, so it is the same four-component
        ``AnalysisRun`` comparison and the same **irreversible** staleness the review runtime already
        implements: once stale, a Draft stays non-actionable and is never revived (``§6.1`` C).
        """

        return self.review.is_stale(current_analysis_run)

    def draft_state(self, current_analysis_run) -> str:
        """The Draft's runtime state: ``DRAFT``, or the bound decision's kind, or ``STALE``.

        A stale Draft always reports ``STALE`` whatever it previously recorded.  Otherwise an initial
        Draft reports the registered ``DRAFT`` marker, an approved Draft reports its decision kind and a
        rejected Draft reports its decision kind.  These are internal runtime tokens derived from the
        registered decision kinds -- no canonical enum or business status is introduced.
        """

        if self.is_stale(current_analysis_run):
            return "STALE"
        if self.decision is None:
            return DRAFT_MARKER
        if self.decision.decision_kind == DECISION_APPROVE:
            return _APPROVED_STATE
        if self.decision.decision_kind == DECISION_REJECT:
            return _REJECTED_STATE
        return _UNDECIDED_STATE

    def is_actionable(self, current_analysis_run) -> bool:
        """Whether the Draft still permits a decision (``§6.1`` C).

        Non-actionable once the review instance is stale, and non-actionable once any decision has
        been bound: an approved Draft is already decided and a rejected Draft is **terminal** -- a
        rejection is never turned into an approval and never triggers a deterministic recomputation.
        """

        if self.is_stale(current_analysis_run):
            return False
        return self.decision is None

    def has_approved_draft(self, current_analysis_run) -> bool:
        """Whether this is an **approved** Draft: not stale and bound to an approve decision."""

        if self.is_stale(current_analysis_run) or self.decision is None:
            return False
        return self.decision.decision_kind == DECISION_APPROVE

    # --- assembly -------------------------------------------------------------------------

    def with_decision(self, decision: HumanDecision, current_analysis_run) -> "ProcurementRequestDraft":
        """Bind a **corresponding** Human decision and return the resulting new Draft.

        The decision must be this review instance's own decision for this exact grain, run and
        reviewed projection (see :func:`_require_identity`), and this Draft must still be actionable:
        a stale Draft can never be approved or revived, and a Draft that already carries a decision
        cannot be decided twice.  On success the returned Draft reflects the decision's
        ``approved_value`` truthfully -- including when that value is an explicit Human override, and
        including when it happens to equal the deterministic recommendation (an explicit override is
        never silently rewritten into approve-as-is).
        """

        if self.is_stale(current_analysis_run):
            raise DraftError(
                "this Draft is stale: a stale Draft is non-actionable, can never be approved and is "
                "never revived (§6.1 C); a new Analysis Run requires a new review instance and a new "
                "Draft"
            )
        if self.decision is not None:
            raise DraftError(
                "this Draft already carries a Human decision, so it cannot be decided again; a "
                "rejected Draft is terminal and a reconsideration takes a new decision (§6.1 C)"
            )
        _require_identity(self.review, decision)
        if decision.decision_kind == DECISION_APPROVE and decision.approved_value is None:
            raise DraftError(
                "an approve decision must state the approved value it approved, so no approved Draft "
                "can be formed from it (§6.1 A)"
            )
        return ProcurementRequestDraft(review=self.review, decision=decision)

    # --- serialization --------------------------------------------------------------------

    def to_dict(self, current_analysis_run) -> dict[str, Any]:
        """The Draft's own stable payload (exact quantities; no float conversion).

        This is a **runtime** payload for inspection and tests, not a wire / canonical contract and not
        a serialization carrier.  It carries the registered ``DRAFT`` marker, the derived read-only
        need date and the exact quantity, and it deliberately carries **no** supplier field and no
        approval / production state.
        """

        quantity = self.quantity
        deterministic = self.deterministic_recommended_value
        decision = self.decision
        return {
            "marker": DRAFT_MARKER,
            "state": self.draft_state(current_analysis_run),
            "grain": {
                "plant_id": self.grain[0],
                "material_code": self.grain[1],
                "RecommendationNeedDate": self.recommendation_need_date,
            },
            "analysis_run": {
                "analysis_run_id": self.analysis_run.analysis_run_id,
                "snapshot_package_identity": self.analysis_run.snapshot_package_identity,
                "accepted_content_view_digest": self.analysis_run.accepted_content_view_digest,
                "analysis_date": self.analysis_run.analysis_date,
            },
            "quantity": _rational_payload(quantity),
            "deterministic_recommended_value": _rational_payload(deterministic),
            "decision_bound": decision is not None,
            "override_flag": None if decision is None else decision.override_flag,
        }


def open_draft(review: ReviewInstance) -> ProcurementRequestDraft:
    """Open the **initial** ephemeral Draft of one review instance (``§6.1`` A / C).

    The Draft is opened from the review instance alone: no ``HumanDecision`` is required, none is
    fabricated and no decision-derived value appears.  Its quantity is the deterministic
    ``RecommendedPurchaseQty`` and its ``RecommendationNeedDate`` is the review grain's own value.

    Opening a Draft never mutates the deterministic result, never persists anything and never contacts
    a provider.
    """

    return ProcurementRequestDraft(review=review, decision=None)


__all__ = [
    "DRAFT_MARKER",
    "DraftError",
    "ProcurementRequestDraft",
    "open_draft",
]
