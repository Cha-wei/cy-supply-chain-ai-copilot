"""``BR-PROCUREMENT-001`` Purchase Recommendation Quantity (Issue #160).

The registered semantics live in ``poc-design-v0.2.md`` §2.5 (``DESIGN RESOLVED``, Human-approved):
when the Shortage Engine has reliably established a real ``SHORTAGE`` for one
``plant_id`` + ``material_code`` family, the POC recommends **one** baseline purchase quantity for
that family in that analysis run:

```
RecommendationNeedDate   = FirstShortageDate
BasePurchaseNeed         = ShortageQty at RecommendationNeedDate
RecommendedPurchaseQty   = max(BasePurchaseNeed, ApplicableMOQ)
MOQAdjustmentQty         = RecommendedPurchaseQty - BasePurchaseNeed（>= 0）
```

This module is that deterministic rule and nothing more.  It consumes **only** already approved
runtime surfaces -- the ``BR-SHORTAGE-001`` result (``§2.1`` ／ ``§4.4.65`` ／ ``§4.4.66``), the Phase B
``ApplicableMOQ`` policy input (``§4.4.67`` ／ ``§4.3.31`` G I-3 ／ I-4, ``§2.5.19``) and the existing
``AnalysisRunContext`` binding (``F3-RB1`` ／ ``§4.4.93``):

* it never re-reads raw ／ canonical ／ accepted evidence, so no accepted package is a parameter;
* it never recomputes a shortage value, a shortage date or a classification -- ``ShortageQty`` is
  taken from the exact upstream grain and ``RecommendationNeedDate`` from the policy context whose own
  date is the registered per-family ``FirstShortageDate`` handoff (one date authority, caller cannot
  override it);
* it never re-resolves ``ApplicableMOQ``: the exactly-one-applicable-or-unresolved contract is decided
  **before** this rule (``§4.5.22`` Option D) and an unresolved ／ missing ／ invalid ／ ambiguous policy
  input simply leaves this recommendation without a numeric value (``§2.5.2`` ／ ``§2.5.6``).

Numeric semantics (``ADR-001``; ``§2.4.8``): every quantity is an exact value.  ``ShortageQty`` is an
exact rational, ``ApplicableMOQ`` an exact finite decimal quantity, and the three derived results are
exact rationals.  Nothing is rounded, ceilinged, floored, quantized, converted to an order multiple or
inferred into a packaging ／ UOM rule (``§2.5.10`` ／ ``§2.5.11``): a value such as ``2100/19`` is a
reliable quantity, never a reason for ``DATA_INCOMPLETE``.  The rule never touches lead time or risk
(``§2.5.12``) and never selects a supplier or a MOQ candidate by any precedence (``§2.5.13``).

Deliberately **not** implemented here: ``§2.7`` ``BR-SUPPLIER-RISK-001`` (Lead Time ／ Risk Evidence),
``Procurement Request Draft`` ／ P0-3, HITL, persistence ／ service and the real ERP physical carrier of
``ApplicableMOQ`` (still ``NOT YET DEFINED``).  No canonical field ／ entity ／ grain ／ business enum ／
Validation Category ／ Reason is created, and ``ADR-001`` is unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Iterable

from .canonical_objects import AnalysisRunContext, CanonicalConstructionReport
from .constants import (
    CATEGORY_SEMANTIC_RESOLUTION,
    LAYER_2,
    REASON_SEMANTIC_UNRESOLVED,
)
from .exact_quantity import ExactQuantity
from .issues import Issue
from .procurement_policy_input import (
    PROCUREMENT_POLICY_INPUT_STAGE,
    ProcurementPolicyInputContext,
    ProcurementPolicyInputResult,
)
from .requirement_calculation import OUTCOME_DATA_INCOMPLETE
from .result_binding import require_same_analysis_run
from .shortage_calculation import (
    SHORTAGE_DATA_INCOMPLETE,
    SHORTAGE_RULE_ID,
    ShortageCalculationResult,
)

# --- vocabulary --------------------------------------------------------------------

#: The **existing** registered deterministic rule id (``§2.5``, ``§4.5.22`` 決定 7).  It is the
#: calculation-basis identifier of this derived result -- never a new entity, field or enum.
PROCUREMENT_RECOMMENDATION_RULE_ID: str = "BR-PROCUREMENT-001"

#: The resolved outcome of one family: ``None`` means a numeric recommendation was produced;
#: ``DATA_INCOMPLETE`` is the **existing** registered outcome (``§2.5.2`` ／ ``§4.2.10``) used whenever
#: a required input cannot be reliably obtained (No Numeric Recommendation).
PROCUREMENT_RECOMMENDATION_UNRESOLVED: str = OUTCOME_DATA_INCOMPLETE

#: Runtime trace labels for **why** a family has no numeric recommendation.  They are trace only --
#: not a new Validation taxonomy, not a canonical vocabulary, not a wire property and not a business
#: status; the registered ``Issue`` category ／ reason stays the inherited one (or the existing
#: ``SEMANTIC_RESOLUTION`` ／ ``SEMANTIC_UNRESOLVED`` and ``CONSISTENCY`` ／ ``CONSISTENCY_CONFLICT``
#: pairs that the approved design already assigns to an unresolved ／ inconsistent upstream input).
ROOT_MOQ_INPUT_UNRESOLVED: str = "MOQ_POLICY_INPUT_UNRESOLVED"
ROOT_SHORTAGE_INPUT_UNRESOLVED: str = "SHORTAGE_INPUT_UNRESOLVED"
ROOT_SHORTAGE_INPUT_INCONSISTENT: str = "SHORTAGE_INPUT_INCONSISTENT"

#: The **existing** registered consistency pair (``§4.4.80`` #7 ／ ``§4.4.81`` #10, ``§4.4.92``), used
#: verbatim exactly as the other deterministic rules use it: two individually valid evidences that
#: must agree on the same canonical grain ／ fact do not.
_CATEGORY_CONSISTENCY: str = "CONSISTENCY"
_REASON_CONSISTENCY_CONFLICT: str = "CONSISTENCY_CONFLICT"


# --- result representation ---------------------------------------------------------


@dataclass(frozen=True, slots=True)
class UpstreamResultReference:
    """The minimum reference to one consumed upstream deterministic result ／ context.

    ``master-data-mapping.md`` 決定 7 ／ 決定 11 define a derived result's provenance as the Analysis
    Run identity (carried by this result) ＋ the deterministic Rule ID ＋ references to the upstream
    canonical inputs ／ contexts.  They explicitly forbid copying all upstream source metadata into a
    derived value, so the reference is exactly the producing rule ／ seam and the upstream grain; the
    upstream result itself keeps the evidence ／ record reference that answers "which source evidence
    supported it".
    """

    rule: str
    grain: tuple[Any, Any, Any]

    def to_dict(self) -> dict[str, object]:
        return {"rule": self.rule, "grain": list(self.grain)}


@dataclass(frozen=True, slots=True)
class ProcurementRecommendation:
    """One baseline purchase recommendation of one exact ``plant_id`` + ``material_code`` family.

    The family's owner grain is the registered Procurement Recommendation context
    (``Analysis Run`` ＋ ``plant_id`` ＋ ``material_code`` ＋ ``RecommendationNeedDate``,
    ``§4.4.66``): ``recommendation_need_date`` is the exact ``FirstShortageDate`` the Phase B policy
    context received from the shortage-side handoff, never a recomputed or injected date.

    ``outcome`` is ``None`` when the numeric results were produced and ``DATA_INCOMPLETE`` otherwise.
    ``shortage_qty`` is the consumed exact ``ShortageQty`` of that grain and equals
    ``base_purchase_need`` by definition (``§2.5.4``); ``applicable_moq`` is the exact policy input
    value consumed losslessly (possibly the valid explicit ``0``); ``moq_adjustment_qty`` is
    ``recommended_purchase_qty - base_purchase_need`` and is therefore never negative
    (``§2.5.8`` ／ ``§2.5.9``).

    ``shortage_classification`` is the consumed upstream ``Classification`` (an existing status, never
    a new one) or ``None`` when the family's own need date is unresolved.  ``root_condition`` is this
    rule's runtime trace of why no numeric value exists, and ``policy_root_condition`` passes through
    the Phase B ``§4.4.67`` root of the consumed context, so the precise upstream classification is
    never re-derived here.  ``inherited_issues`` carries the registered findings of the consumed
    policy input verbatim; ``rule_issues`` carries only findings this rule owns (an upstream Shortage
    Result that cannot state the registered grain, or that contradicts it).
    """

    plant_id: Any
    material_code: Any
    recommendation_need_date: Any
    outcome: str | None = None
    shortage_classification: str | None = None
    shortage_qty: Fraction | None = None
    base_purchase_need: Fraction | None = None
    applicable_moq: ExactQuantity | None = None
    moq_adjustment_qty: Fraction | None = None
    recommended_purchase_qty: Fraction | None = None
    root_condition: str | None = None
    policy_root_condition: str | None = None
    applicability_basis: str | None = None
    shortage_reference: UpstreamResultReference | None = None
    policy_input_reference: UpstreamResultReference | None = None
    notes: tuple[str, ...] = ()
    inherited_issues: tuple[Issue, ...] = ()
    rule_issues: tuple[Issue, ...] = ()

    @property
    def grain(self) -> tuple[Any, Any, Any]:
        return (self.plant_id, self.material_code, self.recommendation_need_date)

    @property
    def data_incomplete(self) -> bool:
        return self.outcome == PROCUREMENT_RECOMMENDATION_UNRESOLVED

    @property
    def has_numeric_result(self) -> bool:
        return self.outcome is None and self.recommended_purchase_qty is not None

    @property
    def issues(self) -> tuple[Issue, ...]:
        return _deduplicate_issues(self.inherited_issues + self.rule_issues)

    def to_dict(self) -> dict[str, object]:
        return {
            "rule": PROCUREMENT_RECOMMENDATION_RULE_ID,
            "plant_id": self.plant_id,
            "material_code": self.material_code,
            "RecommendationNeedDate": self.recommendation_need_date,
            "Classification": self.shortage_classification,
            "ShortageQty": _rational_payload(self.shortage_qty),
            "BasePurchaseNeed": _rational_payload(self.base_purchase_need),
            "ApplicableMOQ": (
                None if self.applicable_moq is None else self.applicable_moq.text()
            ),
            "MOQAdjustmentQty": _rational_payload(self.moq_adjustment_qty),
            "RecommendedPurchaseQty": _rational_payload(self.recommended_purchase_qty),
            "outcome": self.outcome,
            "root_condition": self.root_condition,
            "policy_root_condition": self.policy_root_condition,
            "applicability_basis": self.applicability_basis,
            "shortage_reference": (
                None if self.shortage_reference is None else self.shortage_reference.to_dict()
            ),
            "policy_input_reference": (
                None
                if self.policy_input_reference is None
                else self.policy_input_reference.to_dict()
            ),
            "notes": list(self.notes),
            "inherited_issues": [issue.to_dict() for issue in self.inherited_issues],
            "rule_issues": [issue.to_dict() for issue in self.rule_issues],
        }


@dataclass(frozen=True, slots=True)
class ProcurementRecommendationResult:
    """Deterministic result of ``BR-PROCUREMENT-001`` for one construction (``§4.4.69``).

    ``recommendations`` is ordered deterministically by ``plant_id`` -> ``material_code`` and states
    **at most one** baseline recommendation per family per analysis run (``§2.5.3``): a numeric
    recommendation, or a fail-closed ``DATA_INCOMPLETE`` one.  A family whose whole horizon is reliable
    and never went short is **not** a recommendation at all -- ``NORMAL`` ／ ``BUFFER_BREACH`` are the
    ``§4.4.87`` valid absence boundary, so the fields are `not produced by design` and never
    ``DATA_INCOMPLETE``.

    ``analysis_run`` is the construction's existing :class:`AnalysisRunContext` (the derived-result
    provenance binding of ``F3-RB1``): it carries the accepted package identity ／ content view, so a
    downstream consumer can verify in turn that this recommendation belongs to its own Analysis Run
    before consuming any value.  ``inherited_issues`` ／ ``rule_issues`` are the deduplicated union of
    the per-family findings.
    """

    analysis_run: AnalysisRunContext
    recommendations: tuple[ProcurementRecommendation, ...] = ()
    valid_absence_grains: tuple[tuple[Any, Any], ...] = ()
    inherited_issues: tuple[Issue, ...] = ()
    rule_issues: tuple[Issue, ...] = ()

    @property
    def issues(self) -> tuple[Issue, ...]:
        return _deduplicate_issues(self.inherited_issues + self.rule_issues)

    @property
    def numeric_recommendations(self) -> tuple[ProcurementRecommendation, ...]:
        return tuple(item for item in self.recommendations if item.has_numeric_result)

    @property
    def data_incomplete_recommendations(self) -> tuple[ProcurementRecommendation, ...]:
        return tuple(item for item in self.recommendations if item.data_incomplete)

    def for_family(
        self, plant_id: Any, material_code: Any
    ) -> ProcurementRecommendation | None:
        """The single stated recommendation of one exact family, or ``None``.

        ``None`` means this result states no recommendation for that family: either the family is a
        reliable valid absence (a purchase recommendation is **not produced by design**) or the result
        does not name the family at all.  It never means "numeric zero".
        """

        for item in self.recommendations:
            if item.plant_id == plant_id and item.material_code == material_code:
                return item
        return None

    def for_owner(
        self, plant_id: Any, material_code: Any, recommendation_need_date: Any
    ) -> ProcurementRecommendation | None:
        """The stated recommendation of one exact owner grain, or ``None``."""

        item = self.for_family(plant_id, material_code)
        if item is None or item.recommendation_need_date != recommendation_need_date:
            return None
        return item

    def recommended_purchase_qty_for(
        self, plant_id: Any, material_code: Any
    ) -> Fraction | None:
        """The numeric ``RecommendedPurchaseQty`` of one family, or ``None``.

        ``None`` covers exactly the two non-numeric cases and never hides a value: the family is a
        valid absence (no recommendation by design) or the recommendation is ``DATA_INCOMPLETE``
        (``§2.5.2``).  ``recommended_purchase_qty_for(...)`` therefore never fabricates a ``0``.
        """

        item = self.for_family(plant_id, material_code)
        return None if item is None else item.recommended_purchase_qty

    def is_valid_absence(self, plant_id: Any, material_code: Any) -> bool:
        """Whether this result states a reliable, never-short horizon for that exact family."""

        return (plant_id, material_code) in self.valid_absence_grains

    def to_dict(self) -> dict[str, object]:
        return {
            "rule": PROCUREMENT_RECOMMENDATION_RULE_ID,
            "analysis_run": {
                "analysis_run_id": self.analysis_run.analysis_run_id,
                "AnalysisDate": self.analysis_run.analysis_date,
                "snapshot_package_identity": (
                    self.analysis_run.snapshot_package_identity
                ),
                "accepted_content_view_digest": (
                    self.analysis_run.accepted_content_view_digest
                ),
            },
            "recommendations": [item.to_dict() for item in self.recommendations],
            "valid_absence_grains": [
                {"plant_id": plant_id, "material_code": material_code}
                for plant_id, material_code in self.valid_absence_grains
            ],
            "rule_issues": [issue.to_dict() for issue in self.rule_issues],
        }


# --- entry point -------------------------------------------------------------------


def compute_procurement_recommendation(
    construction: CanonicalConstructionReport,
    shortage: ShortageCalculationResult,
    policy_input: ProcurementPolicyInputResult,
) -> ProcurementRecommendationResult:
    """Produce the baseline purchase recommendation of every triggered family.

    ``construction`` supplies the Analysis Run binding (and nothing else); ``shortage`` supplies
    ``Classification`` ／ ``FirstShortageDate`` ／ ``ShortageQty``; ``policy_input`` supplies the
    resolved ``ApplicableMOQ`` of the exact Procurement Recommendation Context.  All three must belong
    to the same Analysis Run, verified **before** any upstream business value is consumed
    (``F3-RB1`` ``Option A′`` ／ ``§4.4.65`` ／ ``§4.4.93``): a foreign, stale or unbound upstream result
    rejects the invocation instead of being combined, and that rejection is never disguised as a
    business ``DATA_INCOMPLETE``.

    Only the families the policy-input result states a context for are evaluated; its
    ``valid_absence_grains`` stay the registered valid absence (``NORMAL`` ／ ``BUFFER_BREACH`` ⇒ **No
    Purchase Recommendation**, ``§2.5.2`` ／ ``§4.4.87``).  No clock, randomness, locale, caller-provided
    quantity or raw evidence is involved anywhere, so identical inputs produce identical payloads.
    """

    require_same_analysis_run(
        construction.analysis_run,
        (SHORTAGE_RULE_ID, shortage.analysis_run),
        (PROCUREMENT_POLICY_INPUT_STAGE, policy_input.analysis_run),
    )

    recommendations = [
        _evaluate(context, shortage)
        for context in sorted(policy_input.contexts, key=_context_key)
    ]
    return ProcurementRecommendationResult(
        analysis_run=construction.analysis_run,
        recommendations=tuple(recommendations),
        valid_absence_grains=tuple(sorted(policy_input.valid_absence_grains, key=_family_key)),
        inherited_issues=_deduplicate_issues(
            tuple(issue for item in recommendations for issue in item.inherited_issues)
        ),
        rule_issues=_deduplicate_issues(
            tuple(issue for item in recommendations for issue in item.rule_issues)
        ),
    )


# --- one family --------------------------------------------------------------------


def _evaluate(
    context: ProcurementPolicyInputContext,
    shortage: ShortageCalculationResult,
) -> ProcurementRecommendation:
    """Evaluate one exact family: the registered quantity rule, or a fail-closed outcome.

    The order of the checks is the registered one: the owner grain and its date authority first
    (``§4.4.65`` ／ ``§4.4.66``), then the trigger ``Classification = SHORTAGE`` ＋ ``ShortageQty > 0``
    on the exact grain (``§2.5.2``), then the ``ApplicableMOQ`` the Phase B seam already resolved
    (``§4.5.22`` Option D).  Nothing here selects, ranks, defaults or repairs anything.
    """

    plant_id = context.plant_id
    material_code = context.material_code
    need_date = context.recommendation_need_date
    policy_reference = UpstreamResultReference(
        rule=PROCUREMENT_POLICY_INPUT_STAGE, grain=context.grain
    )
    inherited = context.issues

    if need_date is None:
        # The family's own FirstShortageDate is unresolved, so the exact Procurement Recommendation
        # Context cannot be established at all: no numeric recommendation exists for it (§2.5.2
        # DATA_INCOMPLETE ／ §4.3.31 G I-4).  The registered finding is the policy input's own.
        return _no_numeric(
            context=context,
            root=ROOT_MOQ_INPUT_UNRESOLVED,
            note=(
                "RecommendationNeedDate (= FirstShortageDate) is unresolved for this family, so the "
                "registered recommendation grain cannot be established and no quantity is computed "
                "(§2.5.2 / §4.4.65 / §2.5.19)"
            ),
            policy_input_reference=policy_reference,
            inherited_issues=inherited,
        )

    shortage_reference = UpstreamResultReference(
        rule=SHORTAGE_RULE_ID, grain=(plant_id, material_code, need_date)
    )
    expected = shortage.first_shortage_date_for(plant_id, material_code)
    if expected != need_date:
        # §4.4.65 requires this recommendation's RecommendationNeedDate to be exactly the First
        # ShortageDate the consumed shortage result states for the same family: the two must agree on
        # that grain.  A disagreement between two individually valid results is the registered
        # Stage B consistency conflict; an answer that is not a reliable date at all means the
        # required linkage cannot be established (Stage A).  Neither is ever resolved by picking one.
        if expected is None or expected == SHORTAGE_DATA_INCOMPLETE:
            return _no_numeric(
                context=context,
                root=ROOT_SHORTAGE_INPUT_UNRESOLVED,
                note=(
                    "the consumed shortage result states no reliable FirstShortageDate for this exact "
                    "family, so the registered RecommendationNeedDate linkage cannot be established "
                    "and no quantity is computed from an unverifiable date (§4.4.65 / §2.5.2)"
                ),
                policy_input_reference=policy_reference,
                shortage_reference=shortage_reference,
                inherited_issues=inherited,
                category=CATEGORY_SEMANTIC_RESOLUTION,
                reason=REASON_SEMANTIC_UNRESOLVED,
                detail=(
                    "the consumed BR-SHORTAGE-001 result answers "
                    f"{'valid absence' if expected is None else expected!r} for this exact "
                    "plant_id + material_code, while the Procurement Recommendation Context states "
                    f"RecommendationNeedDate {need_date!r}; the registered requirement that both agree "
                    "on the same family grain cannot be reliably established, so the required input is "
                    "unresolved rather than assumed (§4.4.65 / §4.4.87 / §4.4.95)"
                ),
            )
        return _no_numeric(
            context=context,
            root=ROOT_SHORTAGE_INPUT_INCONSISTENT,
            note=(
                "the consumed shortage result states a different FirstShortageDate for this exact "
                "family, so the registered RecommendationNeedDate consistency invariant is violated "
                "and no quantity is computed from either date (§4.4.65 / §4.4.92)"
            ),
            policy_input_reference=policy_reference,
            shortage_reference=shortage_reference,
            inherited_issues=inherited,
            category=_CATEGORY_CONSISTENCY,
            reason=_REASON_CONSISTENCY_CONFLICT,
            detail=(
                "two individually valid results disagree on the same canonical family grain: the "
                "consumed BR-SHORTAGE-001 result states FirstShortageDate "
                f"{expected!r} for this exact plant_id + material_code, while the Procurement "
                f"Recommendation Context states RecommendationNeedDate {need_date!r}. The approved "
                "design requires both to be the same date; no date is chosen by precedence, first ／ "
                "last wins or any other rule (§4.4.65 / §4.4.92 / §2.5.3)"
            ),
        )

    grain = shortage.for_grain(plant_id, material_code, need_date)
    if (
        grain is None
        or grain.data_incomplete
        or grain.shortage_qty is None
        or not grain.shortage
        or grain.shortage_qty <= 0
    ):  # pragma: no cover - the handoff check above already proves this exact reliable grain
        # The registered trigger is **read from the grain itself** -- ``Classification = SHORTAGE``
        # and ``ShortageQty > 0`` (§2.5.2) -- and never inferred from the date handoff alone, so a
        # consumed shortage result that does not state that reliable positive shortage for the
        # registered grain fails closed instead of being trusted.  The consistency check above makes
        # this branch unreachable for a self-consistent upstream result.
        return _no_numeric(
            context=context,
            root=ROOT_SHORTAGE_INPUT_INCONSISTENT,
            note=(
                "the consumed shortage result does not state a reliable positive SHORTAGE at the "
                "registered recommendation grain, so the registered trigger is not satisfied "
                "(§2.5.2)"
            ),
            policy_input_reference=policy_reference,
            shortage_reference=shortage_reference,
            inherited_issues=inherited,
            shortage_classification=None if grain is None else grain.classification,
            category=_CATEGORY_CONSISTENCY,
            reason=_REASON_CONSISTENCY_CONFLICT,
            detail=(
                "the Procurement Recommendation Context is triggered for "
                f"{plant_id!r} + {material_code!r} + {need_date!r}, but the consumed "
                "BR-SHORTAGE-001 result states no reliable positive SHORTAGE for that exact grain "
                f"(Classification {None if grain is None else grain.classification!r}); the "
                "registered trigger requires a reliable SHORTAGE with a positive ShortageQty and no "
                "value is taken from an unverifiable or contradicting grain (§2.5.2 / §4.4.66)"
            ),
        )

    applicable_moq = context.applicable_moq
    if applicable_moq is None:
        # The Phase B seam already decided the exactly-one-applicable-or-unresolved contract: this
        # rule consumes the answer and never re-resolves, selects or defaults it (§4.5.22 決定 4/5/6,
        # §4.4.67).  Its registered finding is inherited verbatim, so the precise root A ／ B ／ C
        # taxonomy is never re-derived here.
        return _no_numeric(
            context=context,
            root=ROOT_MOQ_INPUT_UNRESOLVED,
            note=(
                "the resolved ApplicableMOQ of this exact Procurement Recommendation Context is "
                "unresolved, so no numeric recommendation exists for this family (§2.5.2 / §2.5.6)"
            ),
            policy_input_reference=policy_reference,
            shortage_reference=shortage_reference,
            inherited_issues=inherited,
            shortage_classification=grain.classification,
        )

    base_purchase_need = grain.shortage_qty
    moq_quantity = _exact_rational(applicable_moq)
    recommended_purchase_qty = max(base_purchase_need, moq_quantity)
    moq_adjustment_qty = recommended_purchase_qty - base_purchase_need
    return ProcurementRecommendation(
        plant_id=plant_id,
        material_code=material_code,
        recommendation_need_date=need_date,
        outcome=None,
        shortage_classification=grain.classification,
        shortage_qty=base_purchase_need,
        base_purchase_need=base_purchase_need,
        applicable_moq=applicable_moq,
        moq_adjustment_qty=moq_adjustment_qty,
        recommended_purchase_qty=recommended_purchase_qty,
        applicability_basis=context.applicability_basis,
        shortage_reference=shortage_reference,
        policy_input_reference=policy_reference,
        notes=(
            "BasePurchaseNeed is the consumed ShortageQty of the exact FirstShortageDate grain "
            "(BufferGap is never added, §2.5.4); RecommendedPurchaseQty = "
            "max(BasePurchaseNeed, ApplicableMOQ) and MOQAdjustmentQty = RecommendedPurchaseQty - "
            "BasePurchaseNeed >= 0 are exact rationals with no rounding, ceiling, floor, "
            "quantization, order multiple or packaging ／ UOM inference (§2.5.8 / §2.5.10 / §2.5.11 "
            "/ ADR-001)",
        ),
    )


def _no_numeric(
    *,
    context: ProcurementPolicyInputContext,
    root: str,
    note: str,
    policy_input_reference: UpstreamResultReference,
    inherited_issues: tuple[Issue, ...],
    shortage_reference: UpstreamResultReference | None = None,
    shortage_classification: str | None = None,
    category: str | None = None,
    reason: str | None = None,
    detail: str | None = None,
) -> ProcurementRecommendation:
    """One fail-closed ``DATA_INCOMPLETE`` family: **No Numeric Recommendation** (``§2.5.2``).

    ``category`` ／ ``reason`` are ``None`` whenever the registered finding is already stated by the
    consumed Phase B policy input: that ``Issue`` is inherited verbatim rather than re-classified, so
    an upstream ``§4.4.67`` root A ／ B ／ C keeps its own taxonomy.  They are set only for a finding
    this rule owns -- an upstream Shortage Result that cannot state the registered recommendation grain
    (``SEMANTIC_RESOLUTION`` ／ ``SEMANTIC_UNRESOLVED``) or that contradicts it
    (``CONSISTENCY`` ／ ``CONSISTENCY_CONFLICT``).

    No value is ever defaulted here, and the family keeps its exact owner grain and the references to
    the upstream results it was evaluated against.
    """

    issues: tuple[Issue, ...] = ()
    if category is not None and reason is not None:
        assert detail is not None
        issues = (
            Issue(
                location=(
                    "procurement_recommendation["
                    f"{_sort_text(context.plant_id)}/{_sort_text(context.material_code)}/"
                    f"{_sort_text(context.recommendation_need_date)}]"
                ),
                detail=detail,
                category=category,
                reason=reason,
                layer=LAYER_2,
                affected_evidence=PROCUREMENT_RECOMMENDATION_RULE_ID,
                blast_radius="the purchase recommendation of this exact family only",
                design_reference=(
                    "§2.5.2 / §2.5.3 / §2.5.4 / §4.4.65 / §4.4.66 / §4.4.69 / §4.4.92 / §4.4.93"
                ),
                consequence_context=(
                    "the family carries no numeric recommendation and no value is defaulted, "
                    "clamped, repaired or chosen by precedence; a downstream consumer cannot produce "
                    "a numeric recommendation from it (§2.5.2 No Numeric Recommendation)"
                ),
            ),
        )
    return ProcurementRecommendation(
        plant_id=context.plant_id,
        material_code=context.material_code,
        recommendation_need_date=context.recommendation_need_date,
        outcome=PROCUREMENT_RECOMMENDATION_UNRESOLVED,
        shortage_classification=shortage_classification,
        applicable_moq=context.applicable_moq,
        root_condition=root,
        policy_root_condition=context.root_condition,
        applicability_basis=context.applicability_basis,
        shortage_reference=shortage_reference,
        policy_input_reference=policy_input_reference,
        notes=(
            note,
            "the context is DATA_INCOMPLETE and never carries a numeric quantity: missing ／ "
            "invalid ／ unresolved inputs are never defaulted to 0 and never guessed "
            "(§2.5.2 / §2.5.6 / §2.5.7)",
        ),
        inherited_issues=inherited_issues,
        rule_issues=issues,
    )


# --- helpers -----------------------------------------------------------------------


def _exact_rational(value: ExactQuantity) -> Fraction:
    """The exact rational value of one canonical finite-decimal quantity (``ADR-001``).

    ``ExactQuantity`` holds ``units * 10 ** -scale`` as an arbitrary-precision integer pair, so the
    conversion is exact for every canonical base-10 quantity -- it never approximates, truncates or
    rounds, and it is the same conversion the deterministic rules already use to compare a
    finite-decimal quantity with an exact rational one.
    """

    return Fraction(value.units, 10**value.scale)


def _rational_payload(value: Fraction | None) -> dict[str, int] | None:
    """The registered lossless serialisation of an exact rational derived quantity.

    ``{"numerator": <integer>, "denominator": <positive integer>}`` -- the single serialised form of a
    derived quantity in this repository (``§4.2.10`` ／ ``§2.4.8`` ／ ``ADR-001``), the same form
    ``BR-REQUIREMENT-001`` ／ ``BR-SUBSTITUTE-001`` ／ ``BR-SHORTAGE-001`` use.  It carries the exact
    value including a non-terminating decimal expansion, so a reliable quantity is never rounded,
    quantized or downgraded, and no parallel ／ companion decimal text field exists.
    """

    if value is None:
        return None
    return {"numerator": value.numerator, "denominator": value.denominator}


def _context_key(
    context: ProcurementPolicyInputContext,
) -> tuple[str, str]:
    return (_sort_text(context.plant_id), _sort_text(context.material_code))


def _family_key(family: tuple[Any, Any]) -> tuple[str, str]:
    return (_sort_text(family[0]), _sort_text(family[1]))


def _deduplicate_issues(issues: Iterable[Issue]) -> tuple[Issue, ...]:
    seen: dict[tuple[str, str, str], Issue] = {}
    for issue in issues:
        seen.setdefault((issue.location, issue.category, issue.reason), issue)
    return tuple(sorted(seen.values(), key=Issue.sort_key))


def _sort_text(value: Any) -> str:
    return "" if value is None else str(value)


__all__ = [
    "PROCUREMENT_RECOMMENDATION_RULE_ID",
    "PROCUREMENT_RECOMMENDATION_UNRESOLVED",
    "ROOT_MOQ_INPUT_UNRESOLVED",
    "ROOT_SHORTAGE_INPUT_INCONSISTENT",
    "ROOT_SHORTAGE_INPUT_UNRESOLVED",
    "ProcurementRecommendation",
    "ProcurementRecommendationResult",
    "UpstreamResultReference",
    "compute_procurement_recommendation",
]
