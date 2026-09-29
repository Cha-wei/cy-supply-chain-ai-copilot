"""Minimal in-process §6 HITL review / decision runtime (``§10.3`` / Issue #200 authority).

Covers the reduced first HITL coding tranche registered by ``POC Design v0.2`` §10.3 (Human
Decision ``HD-HITL-R1`` / ``HD-HITL-R2``) against the ``§6`` Issue #198 design record:

```text
read-only Review projection
  -> Approve the deterministic RecommendedPurchaseQty as-is
  -> Reject
  -> AnalysisRun stale detection / re-review enforcement
```

Every ``§10.3 H`` Required Test obligation is exercised here, in its registered contract order and
grouping, plus the internal mechanics the obligations depend on (the projection reference, the
in-process instance condition and the override-existence flag).

The fixtures reuse the existing end-to-end chain builder of ``tests.test_supplier_risk_input``, so
every review instance is opened over a **real** accepted SIMULATED chain rather than a hand-made
result object.  All inputs are ``SIMULATED``.

Boundary assertions are deliberate: this suite checks that the module performs no network call, no
persistence, no provider egress and no production / ERP write, that it never mutates or recomputes a
deterministic result, and that no quantity-override path exists anywhere on the surface.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import json
import tempfile
import unittest
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping

import snapshot_loader.hitl_review as hitl_module
from snapshot_loader import (
    ANALYSIS_RUN_COMPONENTS,
    ANSWER_KINDS,
    AnalysisRunContext,
    HUMAN_DECISION_REQUIRED_TEXT,
    DECISION_APPROVE,
    DECISION_RECORD_FIELDS,
    DECISION_REJECT,
    EVIDENCE_KIND_SUPPLIER_RISK,
    EVIDENCE_KIND_UPSTREAM_RESULT,
    EXPLANATION_BOUND,
    EXPLANATION_KEYS,
    EXPLANATION_UNAVAILABLE_FOR_REVIEW,
    NO_OVERRIDE_REASON,
    NOTE_REVIEW_EXPLANATION_STALE,
    OUTCOME_EXPLAINED,
    OUTCOME_NO_RECOMMENDATION_BY_DESIGN,
    OUTCOME_PROVIDER_UNAVAILABLE,
    OUTCOME_RECOMMENDATION_INCOMPLETE,
    OUTCOME_RECOMMENDATION_UNAVAILABLE,
    OUTCOME_RESPONSE_UNACCEPTABLE,
    PROJECTION_KEYS,
    PROJECTION_NO_RECOMMENDATION,
    PROJECTION_RECOMMENDATION,
    REFERENCE_KEYS_SUPPLIER_RISK,
    REFERENCE_KEYS_UPSTREAM,
    REVIEW_APPROVED,
    REVIEW_FACT_FIELDS,
    REVIEW_GRAIN_FIELDS,
    REVIEW_OPEN,
    REVIEW_REJECTED,
    REVIEW_STALE,
    ReviewConflictError,
    ReviewError,
    ReviewInstance,
    ReviewPreconditionError,
    ProcurementRecommendationResult,
    compute_supplier_risk,
    open_review,
    payload_to_plain,
    projection_reference,
)
from tests.test_procurement_recommendation import module_identifiers
from tests.test_shortage_calculation import D1
from tests.test_supplier_risk_input import DEMAND, PLANT, SupplierRiskInputTestCase

#: One fixed decision instant, so a decision timestamp is asserted without a wall-clock read.
FIXED_TIME = datetime(2026, 10, 2, 3, 4, 5, tzinfo=timezone.utc)
#: The actor reference used by most cases: a **slot**, never verified by this runtime.
ACTOR = "user:simulated-reviewer"
#: The registered reject reason used by the reject cases.
REASON = "SIMULATED: the recommended quantity is not to be ordered this period"
#: The module's own code identifiers -- a docstring may explain a boundary, code may not name it.
MODULE_IDENTIFIERS: frozenset[str] = frozenset(
    module_identifiers(hitl_module)
)


def _code_constants(module) -> tuple[str, ...]:
    """Every string constant of the module's code, with documentation strings excluded.

    A docstring may *describe* a boundary ("no rounding rule is defined here"); code may not carry
    such a value.  This helper keeps the boundary assertions honest without matching prose.
    """

    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    documentation = {
        ast.get_docstring(owner, clean=False)
        for owner in ast.walk(tree)
        if isinstance(owner, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    documentation.discard(None)
    return tuple(
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value not in documentation
    )


def _clock() -> datetime:
    return FIXED_TIME


#: The fixture's five registered quantities, as the runtime renders them in the artifact.
_FIXTURE_FACT_TEXT: dict[str, str] = {
    "ShortageQty": "30",
    "BasePurchaseNeed": "30",
    "ApplicableMOQ": "100",
    "MOQAdjustmentQty": "70",
    "RecommendedPurchaseQty": "100",
}

#: The fixture's compliant selection kind (recommended 100 > shortage 30, and equals the MOQ).
_FIXTURE_KIND: str = "MOQ_RAISED_RECOMMENDATION_ABOVE_SHORTAGE"

#: One expected SIMULATED explanation artifact, **exactly** as the runtime assembles it from the
#: fixture projection: the registered template rendered with the projection's own values, the exact
#: ``"<name> = <value>"`` evidence lines, empty uncertainty and the registered human-decision
#: reminder.  No provider wording is involved.
_ARTIFACT: dict[str, Any] = {
    "answer": ANSWER_KINDS[_FIXTURE_KIND].template.format(**_FIXTURE_FACT_TEXT),
    "evidence": [
        f"{name} = {value}" for name, value in _FIXTURE_FACT_TEXT.items()
    ],
    "uncertainty": [],
    "human_decision_required": HUMAN_DECISION_REQUIRED_TEXT,
}


class _StubExplanationProvider:
    """A stub provider: it records its calls and returns a registered *selection* (no prose).

    It performs no network call, reads no credential and reads no environment.
    """

    def __init__(self, selection: Mapping[str, Any] | None = None, error: BaseException | None = None) -> None:
        self.selection = dict(selection or _SELECTION)
        self.error = error
        self.calls: list[Mapping[str, Any]] = []

    def explain(self, projection: Mapping[str, Any]) -> object:
        self.calls.append(projection)
        if self.error is not None:
            raise self.error
        return dict(self.selection)


#: A compliant provider selection over the fixture's five projected quantities.
_SELECTION: dict[str, Any] = {
    "answer_kind": "MOQ_RAISED_RECOMMENDATION_ABOVE_SHORTAGE",
    "evidence": [
        "ShortageQty",
        "BasePurchaseNeed",
        "ApplicableMOQ",
        "MOQAdjustmentQty",
        "RecommendedPurchaseQty",
    ],
    "uncertainty": [],
    "human_decision_required": True,
}


class _ExplanationBuilder:
    """Build a **real** ``ExplanationResult`` through the registered ``explain_q3`` runtime."""

    def __init__(self, recommendations: ProcurementRecommendationResult, name: str) -> None:
        self.recommendations = recommendations
        self.name = name

    def _explain(self, result=None, provider=None, material: str = DEMAND):
        from snapshot_loader import explain_q3

        return explain_q3(
            self.recommendations if result is None else result,
            _StubExplanationProvider() if provider is None else provider,
            plant_id=PLANT,
            material_code=material,
        )

    def explained(self, *, result=None, provider=None):
        return self._explain(result=result, provider=provider)

    def no_recommendation(self):
        """A family the result does not state: no recommendation and not a valid absence."""

        return self._explain(material="M-NOT-IN-PACKAGE")

    def no_recommendation_by_design(self, *, provider=None):
        """A reliable valid absence: the recommendation is not produced by design."""

        return self._explain(provider=provider)

    def incomplete(self, result=None, provider=None):
        return self._explain(result=result, provider=provider)

    def provider_unavailable(self):
        return self._explain(provider=_StubExplanationProvider(error=RuntimeError("simulated")))

    def response_unacceptable(self):
        selection = dict(_SELECTION)
        selection["uncertainty"] = ["ShortageQty"]
        return self._explain(provider=_StubExplanationProvider(selection=selection))

    def rebound(self, explanation, analysis_run):
        """The same explanation result re-bound to another Analysis Run (a stale explanation)."""

        return dataclasses.replace(explanation, analysis_run=analysis_run)


def _run_payload(context: AnalysisRunContext) -> dict[str, Any]:
    return {name: getattr(context, name) for name in ANALYSIS_RUN_COMPONENTS}


class HitlReviewTestCase(SupplierRiskInputTestCase):
    """Shared fixture: one shorted family with an eligible supplier-risk evidence card."""

    # --- fixtures ---------------------------------------------------------------------

    def reviewable(self, name: str):
        """One real accepted SIMULATED chain with a numeric recommendation and risk evidence."""

        built = self.eligible_chain(name)
        recommendations = self.recommendations(built)
        risk = compute_supplier_risk(self.supplier_input(built, recommendations))
        return built, recommendations, risk

    def incomplete(self, name: str):
        """The same chain with no applicable Phase B policy input (``DATA_INCOMPLETE``)."""

        built = self.build_chain(moq_policies=(), name=name)
        recommendations = self.recommendations(built)
        risk = compute_supplier_risk(self.supplier_input(built, recommendations))
        return built, recommendations, risk

    def valid_absence(self, name: str):
        """A real accepted chain whose family never goes short: a reliable valid absence.

        ``recommendations`` states **no** recommendation for the family (it is not produced by
        design), so a Q3 explanation over it takes the ``NO_RECOMMENDATION_BY_DESIGN`` path.
        """

        built = self.build_chain(demands=((DEMAND, "10", D1),), name=name)
        recommendations = self.recommendations(built)
        risk = compute_supplier_risk(self.supplier_input(built, recommendations))
        return built, recommendations, risk

    def open(self, recommendations, risk=None, *, actor: str = ACTOR, explanation=None):
        return open_review(
            recommendations,
            plant_id=PLANT,
            material_code=DEMAND,
            actor_reference=actor,
            supplier_risk=risk,
            explanation=explanation,
        )

    def current_run(self, recommendations, **changes: Any) -> AnalysisRunContext:
        """The same Analysis Run with one component changed (a genuinely different run)."""

        return dataclasses.replace(recommendations.analysis_run, **changes)

    def need_date(self, recommendations):
        recommendation = recommendations.for_family(PLANT, DEMAND)
        assert recommendation is not None
        return recommendation.recommendation_need_date

    def approve(self, instance, recommendations, *, run=None, actor: str = ACTOR):
        supplied = actor
        return instance.approve_as_recommended(
            current_analysis_run=recommendations.analysis_run if run is None else run,
            plant_id=PLANT,
            material_code=DEMAND,
            recommendation_need_date=self.need_date(recommendations),
            actor_reference=supplied,
            clock=_clock,
        )

    # --- shared assertions ------------------------------------------------------------

    def assert_no_float(self, value: Any, path: str = "$") -> None:
        if isinstance(value, float):
            self.fail(f"a binary floating-point value appeared at {path}")
        if isinstance(value, dict):
            for key, item in value.items():
                self.assert_no_float(item, f"{path}.{key}")
        elif isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                self.assert_no_float(item, f"{path}[{index}]")


# --- §10.3 H: Review projection (5 obligations) ---------------------------------------


class ReviewProjectionTests(HitlReviewTestCase):
    """``§10.3`` H obligations 1 -- 5: the read-only review projection."""

    def test_h1_the_projection_is_read_only_and_the_result_is_unchanged(self) -> None:
        _built, recommendations, risk = self.reviewable("h1")
        before = json.dumps(recommendations.to_dict(), sort_keys=True)
        risk_before = json.dumps(risk.to_dict(), sort_keys=True)

        projection = self.open(recommendations, risk).projection

        self.assertEqual(json.dumps(recommendations.to_dict(), sort_keys=True), before)
        self.assertEqual(json.dumps(risk.to_dict(), sort_keys=True), risk_before)
        self.assertEqual(set(projection.payload), set(PROJECTION_KEYS))

    def test_h2_the_projection_recomputes_and_mutates_nothing(self) -> None:
        _built, recommendations, risk = self.reviewable("h2")
        recommendation = recommendations.for_family(PLANT, DEMAND)
        assert recommendation is not None
        projection = self.open(recommendations, risk).projection

        # Every projected quantity is the deterministic value's own exact payload, not a re-derived
        # number: the projection selects, it never computes.
        self.assertEqual(
            projection.payload["facts"]["ShortageQty"],
            {"numerator": recommendation.shortage_qty.numerator,
             "denominator": recommendation.shortage_qty.denominator},
        )
        self.assertEqual(
            projection.payload["facts"]["RecommendedPurchaseQty"],
            {"numerator": recommendation.recommended_purchase_qty.numerator,
             "denominator": recommendation.recommended_purchase_qty.denominator},
        )
        self.assertEqual(
            projection.payload["facts"]["ApplicableMOQ"], recommendation.applicable_moq.text()
        )
        self.assertEqual(projection.payload["facts"]["MOQAdjustmentQty"]["numerator"], 70)

        # A non-terminating exact rational survives losslessly and is never rendered as a float.
        exact_third = dataclasses.replace(
            recommendation,
            recommended_purchase_qty=Fraction(1, 3),
            shortage_qty=Fraction(1, 3),
            base_purchase_need=Fraction(1, 3),
            moq_adjustment_qty=Fraction(0, 1),
            applicable_moq=None,
        )
        third = dataclasses.replace(recommendations, recommendations=(exact_third,))
        third_projection = self.open(third, None).projection
        self.assertEqual(
            third_projection.payload["facts"]["RecommendedPurchaseQty"],
            {"numerator": 1, "denominator": 3},
        )
        self.assert_no_float(third_projection.payload)

    def test_h3_the_projection_fills_invents_and_carries_nothing_forbidden(self) -> None:
        _built, recommendations, risk = self.reviewable("h3")
        projection = self.open(recommendations, risk).projection
        serialized = json.dumps(payload_to_plain(projection.payload), ensure_ascii=False)

        # Exactly the registered grain, outcome, facts, references and the read-only evidence
        # identity -- no accepted package, no pipeline result, no raw source artifact.
        self.assertEqual(set(projection.payload["grain"]), set(REVIEW_GRAIN_FIELDS))
        self.assertEqual(set(projection.payload["facts"]), set(REVIEW_FACT_FIELDS))
        self.assertEqual(projection.payload["outcome"], PROJECTION_RECOMMENDATION)
        for forbidden in (
            "accepted_package",
            "AcceptedPackage",
            "pipeline",
            "FirstTranchePipelineResult",
            "manifest",
            "raw",
            "integrity_evidence",
            "record_path",
            "content_view",
        ):
            self.assertNotIn(forbidden, serialized)
        # The evidence reference carries the registered provenance identity -- package identity,
        # logical role, artifact, record ordinal and the registered locators -- and never the accepted
        # record's own content.
        supplier_reference = projection.payload["supplier_risk_evidence"][0][
            "performance_evidence_reference"
        ]
        self.assertEqual(supplier_reference["kind"], "performance_evidence_reference")
        self.assertNotIn("records", supplier_reference)
        self.assertNotIn("properties", supplier_reference)

        # A family the result does not state at all keeps every quantity unstated: the projection
        # never fills, defaults or re-classifies a value.
        absent = open_review(
            recommendations,
            plant_id=PLANT,
            material_code="M-NOT-IN-PACKAGE",
            actor_reference=ACTOR,
            supplier_risk=risk,
        ).projection
        self.assertEqual(absent.payload["outcome"], PROJECTION_NO_RECOMMENDATION)
        self.assertEqual(absent.payload["grain"]["RecommendationNeedDate"], None)
        self.assertEqual(set(absent.payload["facts"].values()), {None})
        self.assertEqual(absent.payload["references"]["shortage_reference"], None)

    def test_h4_the_projection_has_no_egress(self) -> None:
        _built, recommendations, risk = self.reviewable("h4")
        projection = self.open(recommendations, risk).projection
        self.assertFalse(hasattr(projection, "provider"))
        self.assertFalse(any("provider" in key for key in projection.payload))

        # The module itself reaches no network, resolves no credential and imports no client: the
        # only provider-shaped names in the package live in the explanation modules, which this
        # runtime never imports.
        self.assertNotIn("provider", {node.id for node in ast.walk(ast.parse(
            Path(hitl_module.__file__).read_text(encoding="utf-8")
        )) if isinstance(node, ast.Name)})
        source = Path(hitl_module.__file__).read_text(encoding="utf-8")
        for forbidden in ("urllib", "socket", "http.client", "requests", "os.environ", "subprocess"):
            self.assertNotIn(forbidden, source)

    def test_h5_the_projection_reference_points_at_the_reviewed_projection(self) -> None:
        _built, recommendations, risk = self.reviewable("h5")
        instance = self.open(recommendations, risk)
        decision = self.approve(instance, recommendations)

        self.assertEqual(decision.review_projection_reference, instance.review_projection_reference)
        self.assertEqual(
            decision.review_projection_reference, projection_reference(instance.projection.payload)
        )

        # A different projection of the same grain (here: without the optional risk evidence) is a
        # different reviewed object and therefore a different reference.
        other = self.open(recommendations, None)
        self.assertNotEqual(
            other.review_projection_reference, instance.review_projection_reference
        )


# --- §10.3 H: Approve-as-is (4 obligations) -------------------------------------------


class ApproveAsIsTests(HitlReviewTestCase):
    """``§10.3`` H obligations 6 -- 9: approving the deterministic quantity as-is."""

    def test_h6_only_a_valid_deterministic_recommendation_can_be_approved(self) -> None:
        _built, recommendations, risk = self.reviewable("h6")
        instance = self.open(recommendations, risk)

        # DATA_INCOMPLETE states no numeric recommended quantity, so approve-as-is cannot be taken.
        _built2, incomplete, risk2 = self.incomplete("h6-incomplete")
        incomplete_instance = self.open(incomplete, risk2)
        self.assertFalse(incomplete_instance.has_approvable_recommendation)
        with self.assertRaises(ReviewPreconditionError):
            self.approve(incomplete_instance, incomplete)
        self.assertEqual(incomplete_instance.status(incomplete.analysis_run), REVIEW_OPEN)

        # A family with no recommendation at all is equally unapprovable.
        absent_instance = open_review(
            recommendations,
            plant_id=PLANT,
            material_code="M-NOT-IN-PACKAGE",
            actor_reference=ACTOR,
        )
        self.assertFalse(absent_instance.has_approvable_recommendation)
        with self.assertRaises(ReviewPreconditionError):
            absent_instance.approve_as_recommended(
                current_analysis_run=recommendations.analysis_run,
                plant_id=PLANT,
                material_code="M-NOT-IN-PACKAGE",
                recommendation_need_date=None,
                actor_reference=ACTOR,
                clock=_clock,
            )

        # The valid instance still approves, so the precondition (not the fixture) was the blocker.
        self.assertEqual(self.approve(instance, recommendations).decision_kind, DECISION_APPROVE)

    def test_h7_the_approved_value_equals_the_deterministic_value(self) -> None:
        _built, recommendations, risk = self.reviewable("h7")
        instance = self.open(recommendations, risk)
        decision = self.approve(instance, recommendations)
        recommendation = recommendations.for_family(PLANT, DEMAND)
        assert recommendation is not None

        self.assertEqual(decision.approved_value, recommendation.recommended_purchase_qty)
        self.assertEqual(decision.approved_value, instance.recommended_purchase_qty)
        self.assertEqual(decision.approved_value, Fraction(100, 1))
        self.assertEqual(
            decision.to_dict()["approved_value"], {"numerator": 100, "denominator": 1}
        )

    def test_h8_the_deterministic_value_is_preserved_losslessly(self) -> None:
        _built, recommendations, risk = self.reviewable("h8")
        instance = self.open(recommendations, risk)
        decision = self.approve(instance, recommendations)

        self.assertEqual(
            decision.deterministic_recommended_value, decision.approved_value
        )
        payload = decision.to_dict()
        self.assertEqual(
            payload["deterministic_recommended_value"], {"numerator": 100, "denominator": 1}
        )

        # An exact non-terminating quantity is carried exactly, never rounded or floated.
        recommendation = recommendations.for_family(PLANT, DEMAND)
        assert recommendation is not None
        third = dataclasses.replace(
            recommendation,
            recommended_purchase_qty=Fraction(1, 3),
            base_purchase_need=Fraction(1, 3),
            shortage_qty=Fraction(1, 3),
            moq_adjustment_qty=Fraction(0, 1),
            applicable_moq=None,
        )
        third_result = dataclasses.replace(recommendations, recommendations=(third,))
        third_decision = self.approve(self.open(third_result), third_result)
        self.assertEqual(
            third_decision.to_dict()["approved_value"], {"numerator": 1, "denominator": 3}
        )
        self.assert_no_float(third_decision.to_dict())

    def test_h9_the_decision_kind_is_stated_correctly(self) -> None:
        _built, recommendations, risk = self.reviewable("h9")
        approved = self.approve(self.open(recommendations, risk), recommendations)
        self.assertEqual(approved.decision_kind, DECISION_APPROVE)
        self.assertEqual(approved.decision_kind, approved.to_dict()["decision_kind"])

        rejected_instance = self.open(recommendations, risk)
        rejected = rejected_instance.reject(
            current_analysis_run=recommendations.analysis_run,
            reason=REASON,
            actor_reference=ACTOR,
            clock=_clock,
        )
        self.assertEqual(rejected.decision_kind, DECISION_REJECT)

        # A decision is never rewritten: a rejected instance keeps its rejection, and its record is
        # not replaced by an approval.
        self.assertIs(rejected_instance.decision, rejected)
        self.assertEqual(rejected_instance.status(recommendations.analysis_run), REVIEW_REJECTED)
        with self.assertRaises(ReviewConflictError):
            self.approve(rejected_instance, recommendations)
        self.assertIs(rejected_instance.decision, rejected)


# --- §10.3 H: AnalysisRun freshness (4 obligations) -----------------------------------


class AnalysisRunFreshnessTests(HitlReviewTestCase):
    """``§10.3`` H obligations 10 -- 13: freshness as a blocking condition only."""

    def test_h10_a_matching_binding_only_does_not_block_approval(self) -> None:
        _built, recommendations, risk = self.reviewable("h10")
        instance = self.open(recommendations, risk)

        self.assertFalse(instance.is_stale(recommendations.analysis_run))
        note = instance.freshness_note(recommendations.analysis_run)
        self.assertIn("does not block approval", note)
        # The freshness note explicitly refuses the sufficient-condition reading.
        self.assertIn("still requires an open review instance", note)

        # The freshness condition alone is not an approval: an instance whose *other* conditions do
        # not hold is still refused while its Analysis Run binding matches.
        _built2, incomplete, risk2 = self.incomplete("h10-incomplete")
        matching_but_unapprovable = self.open(incomplete, risk2)
        self.assertFalse(matching_but_unapprovable.is_stale(incomplete.analysis_run))
        with self.assertRaises(ReviewPreconditionError):
            self.approve(matching_but_unapprovable, incomplete)

        self.assertEqual(self.approve(instance, recommendations).decision_kind, DECISION_APPROVE)

    def test_h11_an_analysis_run_mismatch_is_stale_and_denies_approval(self) -> None:
        _built, recommendations, risk = self.reviewable("h11")
        instance = self.open(recommendations, risk)

        for component, value in (
            ("analysis_run_id", "RUN-2"),
            ("snapshot_package_identity", "SIMULATED-PKG-OTHER"),
            ("accepted_content_view_digest", "0" * 64),
            ("analysis_date", "2026-10-02"),
        ):
            changed = self.current_run(recommendations, **{component: value})
            self.assertTrue(instance.is_stale(changed), component)
            self.assertEqual(instance.status(changed), REVIEW_STALE)
            self.assertIn(component, instance.freshness_note(changed))
            with self.assertRaises(ReviewConflictError):
                self.approve(instance, recommendations, run=changed)

        # The same four components in the same order are the whole freshness judgement: no rule- or
        # code-version component is compared, added or claimed.
        self.assertEqual(
            ANALYSIS_RUN_COMPONENTS,
            (
                "analysis_run_id",
                "snapshot_package_identity",
                "accepted_content_view_digest",
                "analysis_date",
            ),
        )
        self.assertEqual(
            hitl_module.analysis_run_differences(
                recommendations.analysis_run, self.current_run(recommendations, analysis_run_id="RUN-2")
            ),
            ("analysis_run_id",),
        )

    def test_h12_a_stale_instance_cannot_be_revived(self) -> None:
        _built, recommendations, risk = self.reviewable("h12")
        instance = self.open(recommendations, risk)
        new_run = self.current_run(recommendations, analysis_run_id="RUN-2")

        self.assertEqual(instance.status(new_run), REVIEW_STALE)
        # Reverting the "current" run does not revive a stale instance in any durable sense: the
        # instance is judged against whatever run is current, and a stale judgement never becomes a
        # decision.
        with self.assertRaises(ReviewConflictError):
            self.approve(instance, recommendations, run=new_run)
        with self.assertRaises(ReviewConflictError):
            instance.reject(
                current_analysis_run=new_run, reason=REASON, actor_reference=ACTOR, clock=_clock
            )
        self.assertIsNone(instance.decision)
        self.assertEqual(instance.to_dict()["decision"], None)
        self.assertEqual(instance.to_dict()["instance_condition"], REVIEW_OPEN)
        self.assertEqual(instance.status(new_run), REVIEW_STALE)

    def test_h13_a_new_analysis_run_requires_a_new_review_instance(self) -> None:
        _built, recommendations, risk = self.reviewable("h13")
        first = self.open(recommendations, risk)
        first_decision = self.approve(first, recommendations)
        self.assertEqual(first.status(recommendations.analysis_run), REVIEW_APPROVED)

        new_run = self.current_run(recommendations, analysis_run_id="RUN-2")
        new_result = dataclasses.replace(recommendations, analysis_run=new_run)
        second = self.open(new_result, risk)

        self.assertIsNot(second, first)
        self.assertEqual(second.status(new_run), REVIEW_OPEN)
        self.assertEqual(second.analysis_run, new_run)
        self.assertEqual(_run_payload(second.analysis_run)["analysis_run_id"], "RUN-2")

        # The new instance starts from "review in progress": the earlier decision is not inherited,
        # not carried over and not rewritten.  Observing the new Analysis Run made the earlier
        # instance permanently stale, so it now reports STALE even against its own original run --
        # and it keeps the decision it took while it was live.
        self.assertIsNone(second.decision)
        self.assertIs(first.decision, first_decision)
        self.assertEqual(first.status(new_run), REVIEW_STALE)
        self.assertEqual(first.status(recommendations.analysis_run), REVIEW_STALE)
        self.assertTrue(first.is_stale_forever)
        self.assertFalse(second.is_stale_forever)
        self.assertEqual(first.decision.decision_kind, DECISION_APPROVE)

        second_decision = self.approve(second, new_result, run=new_run)
        self.assertEqual(second_decision.approved_value, first_decision.approved_value)
        self.assertEqual(second_decision.analysis_run, new_run)
        self.assertEqual(first_decision.analysis_run, recommendations.analysis_run)


# --- §10.3 H: Reject (3 obligations) --------------------------------------------------


class RejectTests(HitlReviewTestCase):
    """``§10.3`` H obligations 14 -- 16: the reject contract."""

    def test_h14_reject_requires_a_reason(self) -> None:
        _built, recommendations, risk = self.reviewable("h14")
        instance = self.open(recommendations, risk)

        for empty in ("", "   ", "\n\t"):
            with self.assertRaises(ReviewPreconditionError):
                instance.reject(
                    current_analysis_run=recommendations.analysis_run,
                    reason=empty,
                    actor_reference=ACTOR,
                    clock=_clock,
                )
        with self.assertRaises(ReviewPreconditionError):
            instance.reject(
                current_analysis_run=recommendations.analysis_run,
                reason=None,  # type: ignore[arg-type]
                actor_reference=ACTOR,
                clock=_clock,
            )

        self.assertIsNone(instance.decision)
        self.assertEqual(instance.status(recommendations.analysis_run), REVIEW_OPEN)
        decision = instance.reject(
            current_analysis_run=recommendations.analysis_run,
            reason=REASON,
            actor_reference=ACTOR,
            clock=_clock,
        )
        self.assertEqual(decision.human_reason, REASON)

    def test_h15_a_rejected_instance_cannot_later_approve(self) -> None:
        _built, recommendations, risk = self.reviewable("h15")
        instance = self.open(recommendations, risk)
        rejected = instance.reject(
            current_analysis_run=recommendations.analysis_run,
            reason=REASON,
            actor_reference=ACTOR,
            clock=_clock,
        )
        self.assertEqual(instance.status(recommendations.analysis_run), REVIEW_REJECTED)

        with self.assertRaises(ReviewConflictError):
            self.approve(instance, recommendations)
        with self.assertRaises(ReviewConflictError):
            instance.reject(
                current_analysis_run=recommendations.analysis_run,
                reason=REASON,
                actor_reference=ACTOR,
                clock=_clock,
            )
        self.assertIs(instance.decision, rejected)

        # Reconsideration creates a **new** decision on a **new** instance without modifying the old
        # one (which stays as a historical record in process memory only).
        reconsidered = self.open(recommendations, risk)
        new_decision = self.approve(reconsidered, recommendations)
        self.assertEqual(new_decision.decision_kind, DECISION_APPROVE)
        self.assertEqual(rejected.decision_kind, DECISION_REJECT)
        self.assertIs(instance.decision, rejected)
        self.assertEqual(rejected.human_reason, REASON)

    def test_h16_the_same_instance_cannot_approve_twice(self) -> None:
        _built, recommendations, risk = self.reviewable("h16")
        instance = self.open(recommendations, risk)
        first = self.approve(instance, recommendations)
        self.assertEqual(instance.status(recommendations.analysis_run), REVIEW_APPROVED)

        with self.assertRaises(ReviewConflictError):
            self.approve(instance, recommendations)
        self.assertIs(instance.decision, first)
        self.assertEqual(instance.to_dict()["decision"], first.to_dict())


# --- §10.3 H: Human decision record (10 obligations) ----------------------------------


class HumanDecisionRecordTests(HitlReviewTestCase):
    """``§10.3`` H obligations 17 -- 26: the ``§6`` item 4 minimal record contract."""

    def _decision(self, name: str):
        _built, recommendations, risk = self.reviewable(name)
        instance = self.open(recommendations, risk)
        return recommendations, risk, instance, self.approve(instance, recommendations)

    def test_h17_the_grain_is_fully_bound(self) -> None:
        recommendations, _risk, _instance, decision = self._decision("h17")
        recommendation = recommendations.for_family(PLANT, DEMAND)
        assert recommendation is not None

        self.assertEqual(
            decision.grain,
            (PLANT, DEMAND, recommendation.recommendation_need_date),
        )
        self.assertEqual(
            decision.to_dict()["grain"],
            {
                "plant_id": PLANT,
                "material_code": DEMAND,
                "RecommendationNeedDate": recommendation.recommendation_need_date,
            },
        )
        # A review instance decides only for its own fully bound grain.
        with self.assertRaises(ReviewConflictError):
            _instance.approve_as_recommended(
                current_analysis_run=recommendations.analysis_run,
                plant_id=PLANT,
                material_code=DEMAND,
                recommendation_need_date="2026-12-31",
                actor_reference=ACTOR,
                clock=_clock,
            )

    def test_h18_the_full_analysis_run_binding_is_bound_verbatim(self) -> None:
        recommendations, _risk, _instance, decision = self._decision("h18")
        payload = decision.to_dict()["analysis_run"]
        self.assertEqual(set(payload), set(ANALYSIS_RUN_COMPONENTS))
        self.assertEqual(payload, _run_payload(recommendations.analysis_run))
        self.assertIs(decision.analysis_run, recommendations.analysis_run)

    def test_h19_the_evidence_references_are_truthful(self) -> None:
        recommendations, risk, _instance, decision = self._decision("h19")
        recommendation = recommendations.for_family(PLANT, DEMAND)
        assert recommendation is not None

        kinds = {item["kind"] for item in decision.evidence_references}
        self.assertEqual(kinds, {EVIDENCE_KIND_UPSTREAM_RESULT, EVIDENCE_KIND_SUPPLIER_RISK})

        upstream = [
            item
            for item in decision.evidence_references
            if item["kind"] == EVIDENCE_KIND_UPSTREAM_RESULT
        ]
        self.assertEqual(
            {item["rule"] for item in upstream},
            {recommendation.shortage_reference.rule, recommendation.policy_input_reference.rule},
        )
        for item in upstream:
            self.assertEqual(tuple(item["grain"]), tuple(
                recommendation.shortage_reference.grain
            ) if item["rule"] == recommendation.shortage_reference.rule else tuple(
                recommendation.policy_input_reference.grain
            ))

        evidence = [
            item
            for item in decision.evidence_references
            if item["kind"] == EVIDENCE_KIND_SUPPLIER_RISK
        ]
        self.assertEqual(len(evidence), len(risk.cards))
        card = risk.cards[0]
        self.assertEqual(evidence[0]["evaluation_context"]["supplier_id"], card.supplier_id)
        self.assertEqual(evidence[0]["analysis_run_id"], recommendations.analysis_run.analysis_run_id)

        # A reference, never copied raw evidence: no issue objects, no performance measurement, no
        # risk value and no business status travels in the decision record.  The registered
        # provenance identity of the performance evidence reference (package identity, logical role,
        # artifact, record ordinal, locators) is a reference, so it is allowed -- the risk facts the
        # Human reviewed stay in the review projection, reachable through the decision's
        # review_projection_reference.
        serialized = json.dumps(payload_to_plain(decision.to_dict()), ensure_ascii=False)
        for forbidden in (
            "inherited_issues",
            "upstream_issues",
            "rule_issues",
            "LeadTimeRisk",
            "DeliveryRisk",
            "QualityRisk",
            "OverallSupplierRisk",
            "DeliveryPerformance",
            "QualityPerformance",
            "evidence_complete",
            "supplier_risk_facts",
        ):
            self.assertNotIn(forbidden, serialized)
        # The supplier-risk reference is identity only, exactly the registered key set.
        self.assertEqual(set(evidence[0]), set(REFERENCE_KEYS_SUPPLIER_RISK))
        self.assertEqual(
            [set(item) for item in upstream], [set(REFERENCE_KEYS_UPSTREAM)] * len(upstream)
        )

        # Every stated reference is a reference to a real registered identity: an upstream reference
        # carries the rule and the upstream grain; a supplier-risk evidence reference carries the
        # card's read-only identity.  Neither copies a raw-evidence payload.
        for item in decision.evidence_references:
            if item["kind"] == EVIDENCE_KIND_UPSTREAM_RESULT:
                self.assertEqual(set(item), set(REFERENCE_KEYS_UPSTREAM))
            else:
                self.assertEqual(item["kind"], EVIDENCE_KIND_SUPPLIER_RISK)
                self.assertEqual(set(item), set(REFERENCE_KEYS_SUPPLIER_RISK))
        for name in ("shortage_reference", "policy_input_reference"):
            reference = getattr(recommendation, name)
            self.assertIsNotNone(reference)
            self.assertIn(
                (EVIDENCE_KIND_UPSTREAM_RESULT, reference.rule, list(reference.grain)),
                [
                    (item["kind"], item["rule"], list(item["grain"]))
                    for item in decision.evidence_references
                    if item["kind"] == EVIDENCE_KIND_UPSTREAM_RESULT
                ],
            )

        # A family with no recommendation at all has no upstream reference to state, so the decision
        # states none rather than synthesising one.
        absent_instance = open_review(
            recommendations,
            plant_id=PLANT,
            material_code="M-NOT-IN-PACKAGE",
            actor_reference=ACTOR,
        )
        absent_decision = absent_instance.reject(
            current_analysis_run=recommendations.analysis_run,
            reason=REASON,
            actor_reference=ACTOR,
            clock=_clock,
        )
        self.assertEqual(absent_decision.evidence_references, ())

    def test_h20_the_actor_reference_is_carried_as_a_requirement_slot_only(self) -> None:
        recommendations, _risk, _instance, decision = self._decision("h20")
        self.assertEqual(decision.actor_reference, ACTOR)
        self.assertEqual(decision.to_dict()["actor_reference"], ACTOR)

        # The slot is required; nothing about it is verified, and no verification claim exists.
        with self.assertRaises(ReviewPreconditionError):
            self.open(recommendations, actor="")
        payload = decision.to_dict()
        for forbidden in ("identity_verified", "permission", "verified", "authorised", "authorized"):
            self.assertNotIn(forbidden, json.dumps(payload_to_plain(payload)))
        # No code identifier of the module is an identity or permission mechanism: the docstring may
        # explain the boundary, the code may not name one.
        for forbidden in (
            "permission",
            "rbac",
            "identity_verified",
            "credential",
            "authenticate",
            "authorize",
            "role",
        ):
            self.assertFalse(
                {name for name in MODULE_IDENTIFIERS if forbidden in name.lower()},
                f"an identity / permission mechanism appears in the runtime identifiers: {forbidden}",
            )

    def test_h21_the_decision_timestamp_exists(self) -> None:
        _recommendations, _risk, _instance, decision = self._decision("h21")
        self.assertIsInstance(decision.decision_timestamp, datetime)
        self.assertIsNotNone(decision.decision_timestamp.tzinfo)
        self.assertEqual(decision.decision_timestamp, FIXED_TIME)
        self.assertEqual(
            decision.to_dict()["decision_timestamp"], FIXED_TIME.isoformat()
        )

    def test_h22_the_review_projection_reference_points_at_the_reviewed_projection(self) -> None:
        _recommendations, _risk, instance, decision = self._decision("h22")
        self.assertEqual(decision.review_projection_reference, instance.review_projection_reference)
        self.assertEqual(
            decision.to_dict()["review_projection_reference"],
            projection_reference(instance.projection.payload),
        )
        self.assertEqual(set(instance.projection.payload), set(PROJECTION_KEYS))

    def test_h23_the_record_never_enters_or_rewrites_the_deterministic_result(self) -> None:
        _built, recommendations, risk = self.reviewable("h23")
        before = json.dumps(recommendations.to_dict(), sort_keys=True)
        instance = self.open(recommendations, risk)
        decision = self.approve(instance, recommendations)

        self.assertEqual(json.dumps(recommendations.to_dict(), sort_keys=True), before)
        payload = decision.to_dict()
        self.assertNotIn("ApprovedPurchaseQty", json.dumps(payload_to_plain(payload)))
        self.assertNotIn("deterministic_result", payload)
        # The record carries the deterministic value but never a business approval status.
        self.assertEqual(payload["deterministic_recommended_value"]["numerator"], 100)
        for forbidden in ("PurchaseOrder", "purchase_order", "erp", "production"):
            self.assertNotIn(forbidden, json.dumps(payload_to_plain(payload)))

    def test_h24_the_record_carries_the_override_existence_flag(self) -> None:
        _recommendations, _risk, _instance, decision = self._decision("h24")
        payload = decision.to_dict()
        self.assertIn("override_flag", payload)
        self.assertIs(payload["override_flag"], False)
        self.assertEqual(decision.override_flag, False)
        self.assertEqual(decision.override_reason, NO_OVERRIDE_REASON)
        self.assertEqual(set(payload) >= set(DECISION_RECORD_FIELDS), True)

    def test_h25_no_path_states_that_a_quantity_override_exists(self) -> None:
        _built, recommendations, risk = self.reviewable("h25")
        approved = self.approve(self.open(recommendations, risk), recommendations)
        rejected = self.open(recommendations, risk).reject(
            current_analysis_run=recommendations.analysis_run,
            reason=REASON,
            actor_reference=ACTOR,
            clock=_clock,
        )
        for decision in (approved, rejected):
            self.assertIs(decision.override_flag, False)
            self.assertEqual(decision.override_reason, NO_OVERRIDE_REASON)
            self.assertNotEqual(decision.decision_kind, "modify")

        # There is no override / modify runtime path at all: no parameter accepts a quantity, and no
        # public name on the surface is an override entry point.
        for name in hitl_module.__all__:
            lowered = name.lower()
            self.assertNotIn("override_quantity", lowered)
            self.assertNotIn("modify", lowered)
        import inspect

        for entry in (
            hitl_module.open_review,
            hitl_module.build_review_projection,
        ):
            signature = inspect.signature(entry)
            self.assertNotIn("override", str(signature))
            self.assertNotIn("quantity", str(signature))
        for method in (
            hitl_module.ReviewInstance.approve_as_recommended,
            hitl_module.ReviewInstance.reject,
        ):
            parameters = set(inspect.signature(method).parameters)
            self.assertNotIn("quantity", parameters)
            self.assertNotIn("override", parameters)
            self.assertNotIn("approved_value", parameters)

        # The approved value equals the deterministic value in every reachable case.
        self.assertEqual(approved.approved_value, approved.deterministic_recommended_value)

    def test_h26_the_flag_defines_no_future_override_semantics(self) -> None:
        _recommendations, _risk, _instance, decision = self._decision("h26")
        payload = decision.to_dict()
        self.assertEqual(payload["override_reason"], NO_OVERRIDE_REASON)
        # The flag's own value names no future override quantity domain, MOQ relation, sign rule or
        # rounding policy, and no code constant of the module registers one.
        for forbidden in ("moq", "MOQ", "rounding", "clamp", "quantize", "negative", "domain"):
            self.assertNotIn(forbidden, payload["override_reason"])
        for constant in _code_constants(hitl_module):
            for forbidden in ("OVERRIDE_DOMAIN", "OVERRIDE_MOQ", "OVERRIDE_SCALE", "rounding", "clamp"):
                self.assertNotIn(forbidden, constant)
        for forbidden in ("override_domain", "override_moq", "override_quantity", "modify"):
            self.assertFalse(
                {name for name in MODULE_IDENTIFIERS if forbidden in name.lower()},
                f"a future override semantic is named in code: {forbidden}",
            )


# --- §10.3 H: out-of-scope negative assertions (6 obligations) ------------------------


class OutOfScopeAssertionTests(HitlReviewTestCase):
    """``§10.3`` H obligations 27 -- 32: the negative assertions of the reduced tranche."""

    def test_h27_no_quantity_override_or_modify_path_exists(self) -> None:
        _built, recommendations, risk = self.reviewable("h27")
        instance = self.open(recommendations, risk)

        # The instance exposes no way to change a quantity, and the decision it produces still
        # carries the deterministic value.
        surface = {name for name in dir(instance) if not name.startswith("__")}
        self.assertFalse({name for name in surface if "override" in name.lower()} - {"override_flag"})
        with self.assertRaises(TypeError):
            instance.approve_as_recommended(  # type: ignore[call-arg]
                current_analysis_run=recommendations.analysis_run,
                plant_id=PLANT,
                material_code=DEMAND,
                recommendation_need_date=self.need_date(recommendations),
                actor_reference=ACTOR,
                approved_value=Fraction(999, 1),
            )
        decision = self.approve(instance, recommendations)
        self.assertEqual(decision.approved_value, Fraction(100, 1))
        self.assertNotEqual(decision.approved_value, Fraction(999, 1))

        # A review instance is immutable: a decision cannot be smuggled in by mutation.
        with self.assertRaises(dataclasses.FrozenInstanceError):
            instance.decision = decision  # type: ignore[misc]

    def test_h28_the_explanation_artifact_is_never_an_approval_authority(self) -> None:
        _built, recommendations, risk = self.reviewable("h28")
        explanation = _ExplanationBuilder(recommendations, "h28").explained()
        instance = self.open(recommendations, risk, explanation=explanation)

        # The auxiliary explanation contributes its runtime outcome, availability note and artifact
        # -- and never any approval or decision state.
        section = instance.projection.payload["explanation"]
        self.assertEqual(section["binding"], EXPLANATION_BOUND)
        self.assertEqual(set(section), set(EXPLANATION_KEYS))
        self.assertEqual(payload_to_plain(section["artifact"]), _ARTIFACT)
        self.assertNotIn("approval", json.dumps(payload_to_plain(section["artifact"])))

        # Its presence changes no decision: approval still needs the registered conditions, and the
        # decision record carries no explanation-driven approval claim.
        decision = self.approve(instance, recommendations)
        self.assertEqual(decision.approved_value, Fraction(100, 1))
        self.assertEqual(decision.decision_kind, DECISION_APPROVE)
        self.assertEqual(decision.override_flag, False)
        self.assertNotIn("explanation", json.dumps(payload_to_plain(decision.to_dict())).lower())

        # A second, separate instance is still an ordinary review: the explanation confers no
        # authority, so approving it requires exactly the registered conditions.
        second = self.open(recommendations, risk, explanation=explanation)
        second_decision = self.approve(second, recommendations)
        self.assertEqual(second_decision.approved_value, Fraction(100, 1))
        with self.assertRaises(ReviewConflictError):
            self.approve(second, recommendations)  # already approved: never twice

    def test_h29_the_runtime_persists_nothing(self) -> None:
        _built, recommendations, risk = self.reviewable("h29")
        # No persistence or filesystem capability is imported or named by the module's code.
        for forbidden in (
            "sqlite",
            "shelve",
            "pickle",
            "dbm",
            "tempfile",
            "pathlib",
            "shutil",
            "write_text",
            "write_bytes",
            "mkdir",
            "persist",
        ):
            self.assertFalse(
                {name for name in MODULE_IDENTIFIERS if forbidden in name.lower()},
                f"a persistence capability appears in the runtime identifiers: {forbidden}",
            )

        with tempfile.TemporaryDirectory() as scratch:
            before = sorted(p.name for p in Path(scratch).iterdir())
            instance = self.open(recommendations, risk)
            self.approve(instance, recommendations)
            instance.to_dict()
            self.assertEqual(sorted(p.name for p in Path(scratch).iterdir()), before)

        # Every artifact is an in-process object and the record is reachable only through it.
        self.assertIsInstance(instance.to_dict(), dict)
        self.assertNotIn("file", instance.to_dict())

    def test_h30_the_runtime_has_no_network_or_egress(self) -> None:
        for forbidden in (
            "urllib",
            "socket",
            "urlopen",
            "http",
            "request",
            "subprocess",
            "environ",
            "getenv",
            "credential",
            "provider",
        ):
            self.assertFalse(
                {name for name in MODULE_IDENTIFIERS if forbidden in name.lower()},
                f"a network / credential capability appears in the runtime identifiers: {forbidden}",
            )

        _built, recommendations, risk = self.reviewable("h30")
        instance = self.open(recommendations, risk)
        self.assertEqual(
            [name for name in dir(instance) if "provider" in name.lower()], []
        )
        self.assertNotIn("provider", instance.to_dict())

    def test_h31_the_runtime_performs_no_production_or_erp_write(self) -> None:
        for forbidden in (
            "erp",
            "purchase_order",
            "purchaseorder",
            "submit",
            "production",
            "write_back",
            "adapter",
        ):
            self.assertFalse(
                {name for name in MODULE_IDENTIFIERS if forbidden in name.lower()},
                f"a production / ERP write capability appears in the runtime identifiers: {forbidden}",
            )

        _built, recommendations, risk = self.reviewable("h31")
        decision = self.approve(self.open(recommendations, risk), recommendations)
        # The registered boundary stays explicit: approval in the POC is not production execution.
        self.assertEqual(decision.decision_kind, DECISION_APPROVE)
        self.assertNotIn("order", json.dumps(payload_to_plain(decision.to_dict())).lower())

    def test_h32_no_rule_or_code_version_freshness_claim_exists(self) -> None:
        for forbidden in ("rule_version", "code_version", "version"):
            self.assertFalse(
                {name for name in MODULE_IDENTIFIERS if forbidden in name.lower()},
                f"a rule / code-version component appears in the runtime identifiers: {forbidden}",
            )

        _built, recommendations, risk = self.reviewable("h32")
        instance = self.open(recommendations, risk)
        note = instance.freshness_note(recommendations.analysis_run)
        self.assertNotIn("version", note)
        self.assertNotIn("equivalent", note)
        self.assertEqual(
            hitl_module.analysis_run_differences(
                recommendations.analysis_run, recommendations.analysis_run
            ),
            (),
        )
        # A matching binding states only that freshness does not block: no equivalence claim.
        self.assertFalse(instance.is_stale(recommendations.analysis_run))
        self.assertNotIn("guarantee", json.dumps(instance.to_dict()).lower())


# --- Independent-review regression: formed artifacts and irreversible staleness ------------------


class FormedArtifactImmutabilityTests(HitlReviewTestCase):
    """A formed review projection / decision must not be rewritable through the public surface."""

    def test_r1_the_projection_cannot_be_mutated_into_another_grain_review(self) -> None:
        _built, recommendations, risk = self.reviewable("r1")
        instance = self.open(recommendations, risk)
        projection = instance.projection

        # Every exposed mapping is read-only, so a caller cannot re-point the review at another
        # grain and then decide on the mutated object.
        for container, key, value in (
            (projection.grain, "plant_id", "P-OTHER"),
            (projection.grain, "material_code", "M-OTHER"),
            (projection.grain, "RecommendationNeedDate", "2099-01-01"),
            (projection.facts, "RecommendedPurchaseQty", {"numerator": 999, "denominator": 1}),
            (projection.references, "shortage_reference", None),
            (projection.payload, "outcome", "FORGED"),
            (projection.payload, "facts", {}),
            (projection.payload["facts"], "ShortageQty", {"numerator": 999, "denominator": 1}),
            (projection.supplier_risk_evidence[0], "analysis_run_id", "RUN-FORGED"),
            (projection.supplier_risk_evidence[0]["evaluation_context"], "supplier_id", "SUP-FORGED"),
            (projection.supplier_risk_facts[0], "OverallSupplierRisk", "LOW"),
        ):
            with self.assertRaises(TypeError, msg=f"{key} was mutable"):
                container[key] = value  # type: ignore[index]

        # The projection still describes exactly the reviewed grain, and the decision it produces is
        # that grain's decision -- never another grain's.
        self.assertEqual(instance.grain, (PLANT, DEMAND, self.need_date(recommendations)))
        decision = self.approve(instance, recommendations)
        self.assertEqual(decision.grain, instance.grain)
        self.assertEqual(
            decision.to_dict()["grain"],
            {
                "plant_id": PLANT,
                "material_code": DEMAND,
                "RecommendationNeedDate": self.need_date(recommendations),
            },
        )
        self.assertEqual(decision.approved_value, Fraction(100, 1))

    def test_r2_the_projection_reference_and_to_dict_are_defensive(self) -> None:
        _built, recommendations, risk = self.reviewable("r2")
        instance = self.open(recommendations, risk)
        projection = instance.projection
        reference = projection.reference

        # A caller's own copy is a detached copy: mutating it changes neither the runtime projection
        # nor its reference.
        detached = projection.to_dict()
        detached["facts"]["RecommendedPurchaseQty"] = {"numerator": 999, "denominator": 1}
        detached["grain"]["plant_id"] = "P-OTHER"
        self.assertEqual(projection.reference, reference)
        self.assertEqual(projection.payload["facts"]["RecommendedPurchaseQty"]["numerator"], 100)
        self.assertEqual(projection.grain["plant_id"], PLANT)

    def test_r3_a_formed_decision_cannot_be_rewritten(self) -> None:
        _built, recommendations, risk = self.reviewable("r3")
        instance = self.open(recommendations, risk)
        decision = self.approve(instance, recommendations)

        # The record itself is frozen and its nested evidence references are read-only.
        with self.assertRaises(dataclasses.FrozenInstanceError):
            decision.approved_value = Fraction(999, 1)  # type: ignore[misc]
        with self.assertRaises(TypeError):
            decision.evidence_references[0]["rule"] = "BR-FORGED-001"  # type: ignore[index]
        with self.assertRaises(TypeError):
            decision.evidence_references[-1]["analysis_run_id"] = "RUN-FORGED"  # type: ignore[index]

        # A caller's copy is detached, and the instance keeps the decision it formed.
        detached = decision.to_dict()
        detached["evidence_references"][0]["rule"] = "BR-FORGED-001"
        detached["grain"]["plant_id"] = "P-OTHER"
        self.assertEqual(
            decision.evidence_references[0]["rule"],
            decision.evidence_references[0]["rule"],
        )
        self.assertNotEqual(decision.evidence_references[0]["rule"], "BR-FORGED-001")
        self.assertEqual(decision.grain[0], PLANT)
        self.assertIs(instance.decision, decision)
        self.assertEqual(instance.status(recommendations.analysis_run), REVIEW_APPROVED)

        # The frozen payload is still renderable as plain data on demand.
        plain = payload_to_plain(decision.to_dict())
        self.assertEqual(plain["grain"]["plant_id"], PLANT)
        self.assertIsInstance(plain["evidence_references"][0], dict)
        self.assertEqual(json.dumps(plain, ensure_ascii=False)[:1], "{")


class IrreversibleStaleConditionTests(HitlReviewTestCase):
    """A stale review instance never returns to review-in-progress (``§6`` item 8)."""

    def test_r4_observing_another_run_stales_the_instance_permanently(self) -> None:
        _built, recommendations, risk = self.reviewable("r4")
        instance = self.open(recommendations, risk)
        other_run = self.current_run(recommendations, analysis_run_id="RUN-2")

        # The run-1 instance is live against run 1.
        self.assertFalse(instance.is_stale(recommendations.analysis_run))
        self.assertEqual(instance.status(recommendations.analysis_run), REVIEW_OPEN)

        # Observing run 2 makes it stale ...
        self.assertTrue(instance.is_stale(other_run))
        self.assertEqual(instance.status(other_run), REVIEW_STALE)
        self.assertTrue(instance.is_stale_forever)

        # ... and passing run 1 again does not revive it: the instance stays stale, cannot decide,
        # and the freshness note says why.
        self.assertTrue(instance.is_stale(recommendations.analysis_run))
        self.assertEqual(instance.status(recommendations.analysis_run), REVIEW_STALE)
        self.assertIn("already observed stale", instance.freshness_note(recommendations.analysis_run))
        with self.assertRaises(ReviewConflictError):
            self.approve(instance, recommendations)
        with self.assertRaises(ReviewConflictError):
            instance.reject(
                current_analysis_run=recommendations.analysis_run,
                reason=REASON,
                actor_reference=ACTOR,
                clock=_clock,
            )
        self.assertIsNone(instance.decision)
        self.assertTrue(instance.to_dict()["stale"])

        # A new review instance on run 1 is the only way to review that run again.
        reopened = self.open(recommendations, risk)
        self.assertFalse(reopened.is_stale_forever)
        self.assertEqual(reopened.status(recommendations.analysis_run), REVIEW_OPEN)
        self.assertEqual(self.approve(reopened, recommendations).decision_kind, DECISION_APPROVE)

    def test_r5_an_undecided_instance_staled_by_a_new_run_is_not_revivable(self) -> None:
        _built, recommendations, risk = self.reviewable("r5")
        instance = self.open(recommendations, risk)
        new_run = self.current_run(recommendations, analysis_run_id="RUN-2")
        new_result = dataclasses.replace(recommendations, analysis_run=new_run)

        self.assertEqual(instance.status(new_run), REVIEW_STALE)
        with self.assertRaises(ReviewConflictError):
            self.approve(instance, new_result, run=new_run)

        # Even before any other decision, the original run no longer unlocks this instance.
        with self.assertRaises(ReviewConflictError):
            self.approve(instance, recommendations)
        self.assertEqual(instance.status(recommendations.analysis_run), REVIEW_STALE)

        # The new-instance path is what a new Analysis Run requires.
        replacement = self.open(new_result, risk)
        self.assertIsNot(replacement, instance)
        self.assertEqual(replacement.status(new_run), REVIEW_OPEN)
        decision = self.approve(replacement, new_result, run=new_run)
        self.assertEqual(decision.analysis_run, new_run)
        self.assertEqual(instance.status(new_run), REVIEW_STALE)


class ActorSlotRequirementTests(HitlReviewTestCase):
    """Every Human decision carries a non-empty actor-reference slot; none of it is verified."""

    def test_r6_approve_and_reject_require_a_non_empty_actor_slot(self) -> None:
        _built, recommendations, risk = self.reviewable("r6")
        for blank in ("", "   ", "\n\t"):
            instance = self.open(recommendations, risk)
            with self.assertRaises(ReviewPreconditionError):
                self.approve(instance, recommendations, actor=blank)
            with self.assertRaises(ReviewPreconditionError):
                instance.reject(
                    current_analysis_run=recommendations.analysis_run,
                    reason=REASON,
                    actor_reference=blank,
                    clock=_clock,
                )
            self.assertIsNone(instance.decision)
            self.assertEqual(instance.status(recommendations.analysis_run), REVIEW_OPEN)

        instance = self.open(recommendations, risk)
        with self.assertRaises(ReviewPreconditionError):
            self.approve(instance, recommendations, actor=None)  # type: ignore[arg-type]
        with self.assertRaises(ReviewPreconditionError):
            instance.reject(
                current_analysis_run=recommendations.analysis_run,
                reason=REASON,
                actor_reference=None,  # type: ignore[arg-type]
                clock=_clock,
            )
        self.assertIsNone(instance.decision)

        # A valid slot still decides, and the record states the slot it was given.
        decision = self.approve(instance, recommendations, actor="user:another-simulated-reviewer")
        self.assertEqual(decision.actor_reference, "user:another-simulated-reviewer")
        self.assertEqual(decision.actor_reference, decision.to_dict()["actor_reference"])

    def test_r7_the_actor_slot_confers_no_identity_or_permission(self) -> None:
        _built, recommendations, risk = self.reviewable("r7")
        # The slot is required at open time as well, and an unknown / unverifiable value is accepted:
        # presence is neither identity nor permission and this runtime introduces no approver rule.
        with self.assertRaises(ReviewPreconditionError):
            self.open(recommendations, actor="")
        decision = self.approve(
            self.open(recommendations, risk, actor="anything-non-empty"),
            recommendations,
            actor="anything-non-empty",
        )
        self.assertEqual(decision.actor_reference, "anything-non-empty")
        for forbidden in ("permission", "authorized", "authenticated", "identity_verified", "rbac"):
            self.assertNotIn(forbidden, json.dumps(payload_to_plain(decision.to_dict())))


class SupplierRiskRebindingTests(HitlReviewTestCase):
    """Supplier Risk evidence is bound by the whole Analysis Run, not by its id alone."""

    def test_r8_evidence_with_a_different_run_component_is_never_consumed(self) -> None:
        _built, recommendations, risk = self.reviewable("r8")
        instance = self.open(recommendations, risk)
        self.assertEqual(len(instance.projection.supplier_risk_evidence), len(risk.cards))

        for component, value in (
            ("snapshot_package_identity", "SIMULATED-PKG-FOREIGN"),
            ("accepted_content_view_digest", "f" * 64),
            ("analysis_date", "2026-10-02"),
            ("analysis_run_id", "RUN-2"),
        ):
            foreign_run = self.current_run(recommendations, **{component: value})
            foreign = dataclasses.replace(risk, analysis_run=foreign_run)
            self.assertTrue(
                hitl_module.analysis_run_differences(
                    foreign.analysis_run, recommendations.analysis_run
                ),
                component,
            )

            foreign_instance = self.open(recommendations, foreign)
            self.assertEqual(
                foreign_instance.projection.supplier_risk_evidence, (), component
            )
            self.assertEqual(foreign_instance.projection.supplier_risk_facts, (), component)
            decision = self.approve(foreign_instance, recommendations)
            self.assertEqual(
                [
                    item
                    for item in decision.evidence_references
                    if item["kind"] == EVIDENCE_KIND_SUPPLIER_RISK
                ],
                [],
                component,
            )

        # The same-run evidence is still consumed, so the fixture itself was not the blocker.
        same_run = self.open(recommendations, risk)
        self.assertEqual(len(same_run.projection.supplier_risk_evidence), len(risk.cards))
        decision = self.approve(same_run, recommendations)
        self.assertEqual(
            len(
                [
                    item
                    for item in decision.evidence_references
                    if item["kind"] == EVIDENCE_KIND_SUPPLIER_RISK
                ]
            ),
            len(risk.cards),
        )

    def test_r9_evidence_for_another_grain_is_never_consumed(self) -> None:
        _built, recommendations, risk = self.reviewable("r9")
        other_plant = [
            dataclasses.replace(card, plant_id="P-OTHER") for card in risk.cards
        ]
        other = dataclasses.replace(risk, cards=tuple(other_plant))
        instance = self.open(recommendations, other)
        self.assertEqual(instance.projection.supplier_risk_evidence, ())
        self.assertEqual(instance.projection.supplier_risk_facts, ())


class DecisionEvidenceReferenceShapeTests(HitlReviewTestCase):
    """``§6`` item 4 registers decision evidence as references / identity, not a risk snapshot."""

    def test_r10_the_decision_reference_is_identity_and_links_to_the_projection(self) -> None:
        _built, recommendations, risk = self.reviewable("r10")
        instance = self.open(recommendations, risk)
        decision = self.approve(instance, recommendations)
        card = risk.cards[0]

        supplier_reference = [
            item
            for item in decision.evidence_references
            if item["kind"] == EVIDENCE_KIND_SUPPLIER_RISK
        ][0]
        self.assertEqual(set(supplier_reference), set(REFERENCE_KEYS_SUPPLIER_RISK))
        self.assertEqual(
            supplier_reference["evaluation_context"],
            {
                "plant_id": card.plant_id,
                "material_code": card.material_code,
                "supplier_id": card.supplier_id,
            },
        )
        self.assertEqual(supplier_reference["analysis_run_id"], card.analysis_run_id)
        self.assertEqual(supplier_reference["relationship_reference"], card.relationship_reference)
        self.assertEqual(
            supplier_reference["performance_evidence_reference"]["kind"],
            "performance_evidence_reference",
        )

        # The risk values the Human reviewed are in the **projection**, and the decision reaches them
        # through its projection reference -- they are not copied into the record.
        self.assertEqual(len(instance.projection.supplier_risk_facts), len(risk.cards))
        self.assertEqual(
            instance.projection.supplier_risk_facts[0]["OverallSupplierRisk"],
            card.overall_supplier_risk,
        )
        self.assertEqual(
            decision.review_projection_reference, instance.review_projection_reference
        )
        serialized = json.dumps(payload_to_plain(decision.to_dict()), ensure_ascii=False)
        for forbidden in (
            "LeadTimeRisk",
            "DeliveryRisk",
            "QualityRisk",
            "OverallSupplierRisk",
            "DaysUntilNeed",
            "supplier_risk_facts",
        ):
            self.assertNotIn(forbidden, serialized)




# --- Explanation ↔ AnalysisRun binding and re-review consumption --------------------------------


class ExplanationBindingTests(HitlReviewTestCase):
    """``explain_q3`` binds every result to its consumed Analysis Run (runtime metadata only)."""

    def test_b1_every_outcome_path_is_bound_to_the_consumed_analysis_run(self) -> None:
        _built, recommendations, risk = self.reviewable("b1")
        _built2, incomplete, _risk2 = self.incomplete("b1-incomplete")
        _built3, valid_absence, _risk3 = self.valid_absence("b1-valid-absence")

        # Each outcome is produced by its **own** consumed result, and each result must carry that
        # result's exact AnalysisRunContext -- and only call a provider where the path calls one.
        explained_provider = _StubExplanationProvider()
        unavailable_provider = _StubExplanationProvider()
        unacceptable_provider = _StubExplanationProvider(
            selection=dict(_SELECTION, uncertainty=["ShortageQty"])
        )
        by_design_provider = _StubExplanationProvider()
        incomplete_provider = _StubExplanationProvider()

        cases = {
            OUTCOME_EXPLAINED: (
                _ExplanationBuilder(recommendations, "b1")._explain(provider=explained_provider),
                recommendations.analysis_run,
                1,
            ),
            OUTCOME_NO_RECOMMENDATION_BY_DESIGN: (
                _ExplanationBuilder(valid_absence, "b1-valid-absence").no_recommendation_by_design(
                    provider=by_design_provider
                ),
                valid_absence.analysis_run,
                0,
            ),
            OUTCOME_RECOMMENDATION_UNAVAILABLE: (
                _ExplanationBuilder(
                    recommendations, "b1-unavailable"
                )._explain(
                    material="M-NOT-IN-PACKAGE", provider=unavailable_provider
                ),
                recommendations.analysis_run,
                0,
            ),
            OUTCOME_RECOMMENDATION_INCOMPLETE: (
                _ExplanationBuilder(incomplete, "b1-incomplete").incomplete(
                    provider=incomplete_provider
                ),
                incomplete.analysis_run,
                0,
            ),
            OUTCOME_PROVIDER_UNAVAILABLE: (
                _ExplanationBuilder(recommendations, "b1-provider-unavailable").provider_unavailable(),
                recommendations.analysis_run,
                1,
            ),
            OUTCOME_RESPONSE_UNACCEPTABLE: (
                _ExplanationBuilder(recommendations, "b1-unacceptable")._explain(
                    provider=unacceptable_provider
                ),
                recommendations.analysis_run,
                1,
            ),
        }

        for outcome, (result, expected_run, _provider_calls) in cases.items():
            # The exact expected outcome, not a member of an accepted set.
            self.assertEqual(result.outcome, outcome)
            self.assertIs(result.analysis_run, expected_run, outcome)
            self.assertEqual(result.to_dict()["analysis_run"], _run_payload(expected_run), outcome)
            self.assertEqual(
                set(result.to_dict()["analysis_run"]), set(ANALYSIS_RUN_COMPONENTS), outcome
            )

        self.assertEqual(len(explained_provider.calls), 1)
        self.assertEqual(len(unacceptable_provider.calls), 1)
        for provider in (by_design_provider, unavailable_provider, incomplete_provider):
            self.assertEqual(provider.calls, [])

        # The valid-absence fixture really is a reliable valid absence: no recommendation is stated
        # for the family (not produced by design), which is what the by-design path asserts.
        self.assertEqual(valid_absence.valid_absence_grains, ((PLANT, DEMAND),))
        self.assertEqual(valid_absence.recommendations, ())
        self.assertTrue(valid_absence.is_valid_absence(PLANT, DEMAND))
        self.assertIsNone(valid_absence.for_family(PLANT, DEMAND))

    def test_b2_the_binding_preserves_the_four_components_verbatim(self) -> None:
        _built, recommendations, risk = self.reviewable("b2")
        result = _ExplanationBuilder(recommendations, "b2").explained()
        payload = result.to_dict()["analysis_run"]
        self.assertEqual(payload, _run_payload(recommendations.analysis_run))
        self.assertEqual(
            payload,
            {
                "analysis_run_id": recommendations.analysis_run.analysis_run_id,
                "snapshot_package_identity": (
                    recommendations.analysis_run.snapshot_package_identity
                ),
                "accepted_content_view_digest": (
                    recommendations.analysis_run.accepted_content_view_digest
                ),
                "analysis_date": recommendations.analysis_run.analysis_date,
            },
        )

    def test_b3_the_provider_facing_payload_still_carries_no_analysis_run(self) -> None:
        _built, recommendations, risk = self.reviewable("b3")
        provider = _StubExplanationProvider()
        result = _ExplanationBuilder(recommendations, "b3")._explain(provider=provider)

        self.assertEqual(len(provider.calls), 1)
        payload = provider.calls[0]
        serialized = json.dumps(payload_to_plain(payload), ensure_ascii=False)
        for forbidden in (
            "analysis_run",
            "AnalysisRun",
            "snapshot_package_identity",
            "accepted_content_view_digest",
            "analysis_date",
            "package",
        ):
            self.assertNotIn(forbidden, serialized)

        # The registered Q3 projection itself is unchanged: exactly its own keys, and the binding
        # lives only on the in-process result.
        self.assertEqual(set(payload), {"question", "grain", "facts", "completeness"})
        self.assertEqual(set(result.projection), {"question", "grain", "facts", "completeness"})
        self.assertIn("analysis_run", result.to_dict())

    def test_b4_a_bound_explanation_is_carried_as_a_read_only_auxiliary_artifact(self) -> None:
        _built, recommendations, risk = self.reviewable("b4")
        explanation = _ExplanationBuilder(recommendations, "b4").explained()
        instance = self.open(recommendations, risk, explanation=explanation)
        section = instance.projection.payload["explanation"]

        self.assertEqual(section["binding"], EXPLANATION_BOUND)
        self.assertEqual(section["outcome"], OUTCOME_EXPLAINED)
        self.assertIsNone(section["availability_note"])
        self.assertEqual(payload_to_plain(section["artifact"]), _ARTIFACT)
        self.assertEqual(section["analysis_run"], _run_payload(recommendations.analysis_run))

        # The artifact is auxiliary information only: it is neither an approval authority nor a
        # decision input, and it changes no eligibility or decision value.
        with self.assertRaises(TypeError):
            section["artifact"]["answer"] = "FORGED"
        with self.assertRaises(TypeError):
            instance.projection.payload["explanation"] = None
        self.assertEqual(
            set(section["artifact"]),
            {"answer", "evidence", "uncertainty", "human_decision_required"},
        )
        self.assertEqual(list(section["artifact"]["uncertainty"]), [])
        self.assertNotIn("data", json.dumps(payload_to_plain(section["artifact"])))
        self.assertEqual(
            instance.projection.payload["facts"]["RecommendedPurchaseQty"]["numerator"], 100
        )
        decision = self.approve(instance, recommendations)
        self.assertEqual(decision.approved_value, Fraction(100, 1))
        self.assertEqual(decision.decision_kind, DECISION_APPROVE)
        self.assertEqual(decision.override_flag, False)
        self.assertNotIn("explanation", json.dumps(payload_to_plain(decision.to_dict())).lower())


class ExplanationMismatchTests(HitlReviewTestCase):
    """A mismatched explanation is explicitly unavailable and its artifact is never consumed."""

    def test_b5_a_mismatched_binding_makes_the_explanation_unavailable(self) -> None:
        _built, recommendations, risk = self.reviewable("b5")
        builder = _ExplanationBuilder(recommendations, "b5")
        for component, value in (
            ("analysis_run_id", "RUN-2"),
            ("snapshot_package_identity", "SIMULATED-PKG-FOREIGN"),
            ("accepted_content_view_digest", "f" * 64),
            ("analysis_date", "2026-10-02"),
        ):
            stale = builder.rebound(
                builder.explained(),
                self.current_run(recommendations, **{component: value}),
            )
            instance = self.open(recommendations, risk, explanation=stale)
            section = instance.projection.payload["explanation"]

            self.assertEqual(section["binding"], EXPLANATION_UNAVAILABLE_FOR_REVIEW, component)
            self.assertIsNone(section["artifact"], component)
            self.assertIsNone(section["analysis_run"], component)
            self.assertEqual(section["availability_note"], NOTE_REVIEW_EXPLANATION_STALE)
            self.assertIn("unavailable", section["availability_note"])
            serialized = json.dumps(
                payload_to_plain(instance.projection.payload), ensure_ascii=False
            )
            self.assertNotIn("SIMULATED: the recommended quantity", serialized, component)

            # The deterministic review still follows its own registered conditions.
            decision = self.approve(instance, recommendations)
            self.assertEqual(decision.approved_value, Fraction(100, 1))
            self.assertEqual(decision.decision_kind, DECISION_APPROVE)
            self.assertNotIn(
                "explanation", json.dumps(payload_to_plain(decision.to_dict())).lower()
            )

    def test_b6_a_mismatched_explanation_never_calls_a_provider_or_infers_freshness(self) -> None:
        import snapshot_loader.explanation_q3 as q3_module

        _built, recommendations, risk = self.reviewable("b6")
        builder = _ExplanationBuilder(recommendations, "b6")
        stale = builder.rebound(
            builder.explained(),
            self.current_run(recommendations, analysis_run_id="RUN-2"),
        )

        # Opening the review and approving consume no provider: a review never regenerates an
        # explanation and never contacts one.
        calls: list[str] = []
        original = q3_module.explain_q3

        def _forbidden(*args: Any, **kwargs: Any):
            calls.append("regenerated")
            return original(*args, **kwargs)

        q3_module.explain_q3 = _forbidden
        try:
            instance = self.open(recommendations, risk, explanation=stale)
            self.approve(instance, recommendations)
        finally:
            q3_module.explain_q3 = original
        self.assertEqual(calls, [])

        # The stale explanation's own grain and quantities equal this run's; that equality is
        # deliberately not treated as a freshness proof.
        self.assertEqual(
            stale.projection["facts"]["RecommendedPurchaseQty"],
            instance.projection.payload["facts"]["RecommendedPurchaseQty"],
        )
        self.assertEqual(
            stale.projection["grain"]["RecommendationNeedDate"], self.need_date(recommendations)
        )
        self.assertEqual(
            instance.projection.payload["explanation"]["binding"],
            EXPLANATION_UNAVAILABLE_FOR_REVIEW,
        )

    def test_b7_a_new_analysis_run_needs_a_new_explanation_and_revives_nothing(self) -> None:
        _built, recommendations, risk = self.reviewable("b7")
        builder = _ExplanationBuilder(recommendations, "b7")
        old_explanation = builder.explained()
        first = self.open(recommendations, risk, explanation=old_explanation)
        first_decision = self.approve(first, recommendations)

        new_run = self.current_run(recommendations, analysis_run_id="RUN-2")
        new_result = dataclasses.replace(recommendations, analysis_run=new_run)

        # A review of the new run must not consume the old run's explanation.  Observing the new run
        # also makes the old review permanently stale.
        self.assertTrue(first.is_stale(new_run))
        stale_review = self.open(new_result, risk, explanation=old_explanation)
        self.assertEqual(
            stale_review.projection.payload["explanation"]["binding"],
            EXPLANATION_UNAVAILABLE_FOR_REVIEW,
        )
        self.assertIsNone(stale_review.projection.payload["explanation"]["artifact"])

        # A newly generated explanation for the new run binds to it and is consumable.
        regenerated = _ExplanationBuilder(new_result, "b7").explained()
        self.assertIs(regenerated.analysis_run, new_run)
        fresh_review = self.open(new_result, risk, explanation=regenerated)
        section = fresh_review.projection.payload["explanation"]
        self.assertEqual(section["binding"], EXPLANATION_BOUND)
        self.assertEqual(payload_to_plain(section["artifact"]), _ARTIFACT)
        self.assertEqual(section["analysis_run"]["analysis_run_id"], "RUN-2")

        # The old review / old artifact is never revived by the new run.
        self.assertEqual(first.status(recommendations.analysis_run), REVIEW_STALE)
        self.assertTrue(first.is_stale_forever)
        with self.assertRaises(ReviewConflictError):
            self.approve(first, recommendations)
        self.assertIs(first.decision, first_decision)
        self.assertEqual(
            first.projection.payload["explanation"]["analysis_run"]["analysis_run_id"], "RUN-1"
        )

    def test_b8_an_unavailable_explanation_is_not_an_approval_blocker(self) -> None:
        _built, recommendations, risk = self.reviewable("b8")
        builder = _ExplanationBuilder(recommendations, "b8")
        before = json.dumps(recommendations.to_dict(), sort_keys=True)

        for label, explanation in (
            (
                "mismatched",
                builder.rebound(
                    builder.explained(),
                    self.current_run(recommendations, analysis_run_id="RUN-2"),
                ),
            ),
            ("provider_unavailable", builder.provider_unavailable()),
            ("response_unacceptable", builder.response_unacceptable()),
            ("no_recommendation", builder.no_recommendation()),
            ("absent", None),
        ):
            instance = self.open(recommendations, risk, explanation=explanation)
            decision = self.approve(instance, recommendations)
            self.assertEqual(decision.approved_value, Fraction(100, 1), label)
            self.assertEqual(decision.decision_kind, DECISION_APPROVE, label)
            self.assertEqual(decision.override_flag, False, label)
            self.assertEqual(
                instance.projection.payload["facts"]["RecommendedPurchaseQty"],
                {"numerator": 100, "denominator": 1},
                label,
            )

        # The deterministic recommendation is unchanged by all of the above, and an unavailable
        # explanation does not block the reject path either.
        recommendation = recommendations.for_family(PLANT, DEMAND)
        assert recommendation is not None
        self.assertEqual(recommendation.recommended_purchase_qty, Fraction(100, 1))
        self.assertEqual(json.dumps(recommendations.to_dict(), sort_keys=True), before)
        rejected = self.open(
            recommendations,
            risk,
            explanation=builder.rebound(
                builder.explained(),
                self.current_run(recommendations, analysis_run_id="RUN-2"),
            ),
        ).reject(
            current_analysis_run=recommendations.analysis_run,
            reason=REASON,
            actor_reference=ACTOR,
            clock=_clock,
        )
        self.assertEqual(rejected.decision_kind, DECISION_REJECT)

    def test_b9_no_rule_or_code_version_freshness_is_claimed_by_the_binding(self) -> None:
        _built, recommendations, risk = self.reviewable("b9")
        explanation = _ExplanationBuilder(recommendations, "b9").explained()
        instance = self.open(recommendations, risk, explanation=explanation)
        serialized = json.dumps(
            payload_to_plain(instance.projection.payload), ensure_ascii=False
        )
        for forbidden in (
            "rule_version",
            "code_version",
            "rule-version",
            "code-version",
            "equivalent",
        ):
            self.assertNotIn(forbidden, serialized)
        # The binding compares exactly the four registered components.
        self.assertEqual(
            set(instance.projection.payload["explanation"]["analysis_run"]),
            set(ANALYSIS_RUN_COMPONENTS),
        )
        self.assertFalse({name for name in MODULE_IDENTIFIERS if "version" in name.lower()})
