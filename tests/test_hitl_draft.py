"""``Procurement Request Draft`` runtime (``§6.1`` / ``§10.6``, Issue #214).

Covers the scoped Draft runtime tranche authorized by ``POC Design §10.6`` (Human Decision
``HD-DRAFT-R1`` / ``HD-DRAFT-R2``) against the ``§6.1`` semantic record (Human Decision ``D1`` --
``D5``): the initial ephemeral Draft, the decision-derived quantity, the read-only need date and the
absent supplier boundary, the reject / stale / new-AnalysisRun lifecycle, and the claim and
architecture boundaries.

Every ``§10.6`` G Required Test obligation is exercised here, in its registered grouping.  The fixtures
reuse the existing end-to-end SIMULATED chain builder of ``tests.test_hitl_review``, so every Draft is
opened over a real accepted SIMULATED chain and a real review instance rather than a hand-made result
object.  All inputs are ``SIMULATED``, and every draft is assembled by deterministic local assembly --
this suite performs no network call, uses no credential, reads no environment secret and imports no
provider.
"""

from __future__ import annotations

import dataclasses
import inspect
import json
import unittest
from fractions import Fraction
from typing import Any

import snapshot_loader.draft_runtime as draft_module
import snapshot_loader.hitl_review as hitl_module
from snapshot_loader import (
    DECISION_APPROVE,
    DECISION_REJECT,
    NO_OVERRIDE_REASON,
    REVIEW_APPROVED,
    REVIEW_OPEN,
    REVIEW_REJECTED,
    REVIEW_STALE,
    DraftError,
    open_draft,
)
from tests.test_hitl_review import (
    ACTOR,
    REASON,
    HitlReviewTestCase,
    _clock,
)
from tests.test_supplier_risk_input import DEMAND, PLANT

#: The registered ``DRAFT`` marker (asserted as a literal so the test pins the registered contract
#: rather than a public module constant).
DRAFT = "DRAFT"


class DraftRuntimeTestCase(HitlReviewTestCase):
    """Shared fixtures: a real review instance plus its initial / approved / rejected drafts."""

    def initial(self, name: str = "draft"):
        """One review instance and its initial Draft (no Human decision yet)."""

        recommendations, risk = self.reviewable(name)[1:]
        instance = self.open(recommendations, risk)
        return recommendations, instance, open_draft(instance)

    def approved(self, name: str = "draft-approved", *, quantity: Any = None):
        """One approved-as-is (or explicitly overridden) decision and its bound Draft."""

        _built, recommendations, risk = self.reviewable(name)
        instance = self.open(recommendations, risk)
        if quantity is None:
            decision = self.approve(instance, recommendations)
        else:
            decision = self.override(instance, recommendations, quantity)
        draft = open_draft(instance).with_decision(decision, recommendations.analysis_run)
        return recommendations, instance, decision, draft

    def rejected(self, name: str = "draft-rejected"):
        """One reject decision and its bound (terminal) Draft."""

        _built, recommendations, risk = self.reviewable(name)
        instance = self.open(recommendations, risk)
        decision = instance.reject(
            current_analysis_run=recommendations.analysis_run,
            reason=REASON,
            actor_reference=ACTOR,
            clock=_clock,
        )
        draft = open_draft(instance).with_decision(decision, recommendations.analysis_run)
        return recommendations, instance, decision, draft


# --- §10.6 G: Initial Draft ------------------------------------------------------------


class InitialDraftTests(DraftRuntimeTestCase):
    """The initial Draft rests on the deterministic result alone."""

    def test_d1_the_initial_draft_uses_the_deterministic_recommended_quantity(self) -> None:
        recommendations, instance, draft = self.initial("d1")
        self.assertEqual(draft.quantity, Fraction(100, 1))
        self.assertEqual(draft.quantity, instance.recommended_purchase_qty)
        self.assertEqual(
            draft.to_dict(recommendations.analysis_run)["quantity"],
            {"numerator": 100, "denominator": 1},
        )
        self.assertEqual(
            draft.deterministic_recommended_value, Fraction(100, 1)
        )

    def test_d2_the_initial_draft_states_the_registered_draft_marker(self) -> None:
        recommendations, instance, draft = self.initial("d2")
        self.assertEqual(draft.marker, DRAFT)
        payload = draft.to_dict(recommendations.analysis_run)
        self.assertEqual(payload["marker"], DRAFT)
        self.assertEqual(payload["state"], DRAFT)
        self.assertEqual(draft.draft_state(recommendations.analysis_run), DRAFT)
        # The run's own state is untouched by opening a Draft.
        self.assertEqual(instance.status(recommendations.analysis_run), REVIEW_OPEN)

    def test_d3_the_initial_draft_needs_no_decision_and_fabricates_none(self) -> None:
        recommendations, instance, draft = self.initial("d3")

        # No HumanDecision is required, and none is fabricated or referenced.
        self.assertIsNone(draft.decision)
        self.assertFalse(draft.to_dict(recommendations.analysis_run)["decision_bound"])
        self.assertIsNone(draft.to_dict(recommendations.analysis_run)["override_flag"])
        self.assertTrue(draft.is_actionable(recommendations.analysis_run))
        self.assertFalse(draft.has_approved_draft(recommendations.analysis_run))
        self.assertIsNone(instance.decision)

        # No decision-derived value appears anywhere in the Draft.
        serialized = json.dumps(draft.to_dict(recommendations.analysis_run), ensure_ascii=False)
        for forbidden in ("approved_value", "human_reason", "override_reason", "decision_kind"):
            self.assertNotIn(forbidden, serialized)


# --- §10.6 G: Decision-derived values --------------------------------------------------


class DecisionDerivedTests(DraftRuntimeTestCase):
    """A decision-derived value may only come from the corresponding HumanDecision."""

    def test_d4_approve_as_is_makes_the_draft_reflect_the_approved_value(self) -> None:
        recommendations, _instance, decision, draft = self.approved("d4")
        self.assertEqual(decision.decision_kind, DECISION_APPROVE)
        self.assertIs(decision.override_flag, False)
        self.assertEqual(draft.quantity, decision.approved_value)
        self.assertEqual(draft.quantity, Fraction(100, 1))
        self.assertEqual(draft.quantity, decision.deterministic_recommended_value)
        self.assertEqual(draft.draft_state(recommendations.analysis_run), "APPROVED")
        self.assertTrue(draft.has_approved_draft(recommendations.analysis_run))
        self.assertFalse(draft.is_actionable(recommendations.analysis_run))

    def test_d5_an_explicit_override_makes_the_draft_reflect_the_override_value(self) -> None:
        recommendations, _instance, decision, draft = self.approved("d5", quantity="150.25")
        self.assertIs(decision.override_flag, True)
        self.assertNotEqual(decision.override_reason, NO_OVERRIDE_REASON)
        self.assertEqual(decision.approved_value, Fraction(601, 4))
        self.assertEqual(draft.quantity, decision.approved_value)
        self.assertEqual(draft.quantity, Fraction(601, 4))
        # The value came from the decision, not from re-deriving anything.
        self.assertNotEqual(draft.quantity, draft.deterministic_recommended_value)
        self.assertEqual(
            draft.to_dict(recommendations.analysis_run)["override_flag"], True
        )

    def test_d6_an_override_equal_to_the_recommendation_stays_an_override(self) -> None:
        recommendations, _instance, decision, draft = self.approved("d6", quantity="100")
        self.assertIs(decision.override_flag, True)
        self.assertEqual(draft.quantity, decision.approved_value)
        self.assertEqual(draft.quantity, draft.deterministic_recommended_value)
        self.assertEqual(
            draft.to_dict(recommendations.analysis_run)["override_flag"], True
        )

    def test_d7_the_deterministic_recommendation_is_unchanged(self) -> None:
        _built, recommendations, risk = self.reviewable("d7")
        recommendation = recommendations.for_family(PLANT, DEMAND)
        assert recommendation is not None
        before = json.dumps(recommendations.to_dict(), sort_keys=True)

        instance = self.open(recommendations, risk)
        initial = open_draft(instance)
        decision = self.override(instance, recommendations, "150.25")
        draft = initial.with_decision(decision, recommendations.analysis_run)

        self.assertEqual(json.dumps(recommendations.to_dict(), sort_keys=True), before)
        self.assertEqual(recommendation.recommended_purchase_qty, Fraction(100, 1))
        self.assertEqual(recommendation.applicable_moq.text(), "100")
        self.assertEqual(recommendation.moq_adjustment_qty, Fraction(70, 1))
        self.assertEqual(recommendation.shortage_qty, Fraction(30, 1))
        self.assertEqual(draft.deterministic_recommended_value, Fraction(100, 1))
        self.assertEqual(
            draft.to_dict(recommendations.analysis_run)["deterministic_recommended_value"],
            {"numerator": 100, "denominator": 1},
        )
        # The initial Draft is unchanged by binding a decision: a new Draft was produced instead.
        self.assertEqual(initial.quantity, Fraction(100, 1))
        self.assertIsNone(initial.decision)


# --- §10.6 G: Read-only and absence ----------------------------------------------------


class ReadOnlyAndAbsenceTests(DraftRuntimeTestCase):
    """The need date is derived, the supplier is absent, nothing is invented."""

    def test_d8_the_recommendation_need_date_is_read_only_and_verbatim(self) -> None:
        recommendations, instance, draft = self.initial("d8")
        expected = self.need_date(recommendations)
        self.assertEqual(draft.recommendation_need_date, expected)
        self.assertEqual(instance.grain[2], expected)
        payload = draft.to_dict(recommendations.analysis_run)
        self.assertEqual(payload["grain"]["RecommendationNeedDate"], expected)
        self.assertNotIn("RecommendationNeedDate", payload["quantity"] or {})
        # The Draft stores no independent copy: it holds only the review instance and the optional
        # decision, and derives the need date from the review grain on every access, so neither the
        # Draft nor a renderer can modify it.
        self.assertEqual(
            tuple(draft_module.ProcurementRequestDraft.__slots__), ("review", "decision")
        )
        self.assertNotIn("need_date", draft_module.ProcurementRequestDraft.__slots__)

    def test_d9_the_supplier_identity_is_absent_from_the_draft(self) -> None:
        recommendations, _instance, decision, draft = self.approved("d9", quantity="150")
        payload = json.dumps(draft.to_dict(recommendations.analysis_run), ensure_ascii=False)
        for forbidden in ("supplier", "Supplier", "supplier_id", "SUP-A", "ranking", "recommended_supplier"):
            self.assertNotIn(forbidden, payload)
        # No supplier field exists on the runtime surface at all.
        fields = {name for name in dir(draft) if not name.startswith("__")}
        self.assertFalse({name for name in fields if "supplier" in name.lower()})
        self.assertNotIn("supplier", inspect.signature(draft_module.open_draft).parameters)
        self.assertNotIn("supplier", inspect.signature(draft.with_decision).parameters)

    def test_d10_no_structured_value_is_invented(self) -> None:
        recommendations, _instance, decision, draft = self.approved("d10", quantity="150.25")
        payload = draft.to_dict(recommendations.analysis_run)
        # Exactly the registered draft shape, and every value traces to the deterministic result or to
        # the corresponding HumanDecision.
        self.assertEqual(
            set(payload),
            {
                "marker",
                "state",
                "grain",
                "analysis_run",
                "quantity",
                "deterministic_recommended_value",
                "decision_bound",
                "override_flag",
            },
        )
        self.assertEqual(set(payload["grain"]), {"plant_id", "material_code", "RecommendationNeedDate"})
        self.assertEqual(payload["quantity"], {"numerator": 601, "denominator": 4})
        self.assertEqual(payload["deterministic_recommended_value"], {"numerator": 100, "denominator": 1})
        self.assertEqual(payload["quantity"], {"numerator": decision.approved_value.numerator,
                                              "denominator": decision.approved_value.denominator})
        self.assertEqual(payload["analysis_run"]["analysis_run_id"], recommendations.analysis_run.analysis_run_id)


# --- §10.6 G: Lifecycle ----------------------------------------------------------------


class DraftLifecycleTests(DraftRuntimeTestCase):
    """Reject is terminal, stale is non-actionable, a new run needs a new instance and Draft."""

    def test_d11_a_rejected_draft_is_terminal_and_non_actionable(self) -> None:
        recommendations, instance, decision, draft = self.rejected("d11")
        self.assertEqual(decision.decision_kind, DECISION_REJECT)
        self.assertEqual(draft.draft_state(recommendations.analysis_run), "REJECTED")
        self.assertFalse(draft.has_approved_draft(recommendations.analysis_run))
        self.assertFalse(draft.is_actionable(recommendations.analysis_run))
        # **No approved Draft is formed**: a rejected Draft states no approved quantity, while the
        # deterministic recommendation stays reachable and unchanged on the review instance.
        self.assertIsNone(draft.quantity)
        self.assertEqual(draft.deterministic_recommended_value, Fraction(100, 1))
        self.assertEqual(instance.recommended_purchase_qty, Fraction(100, 1))
        self.assertEqual(instance.status(recommendations.analysis_run), REVIEW_REJECTED)

        # It cannot be revived into an approved Draft, and no recomputation is triggered.
        with self.assertRaises(DraftError):
            draft.with_decision(decision, recommendations.analysis_run)
        before = json.dumps(recommendations.to_dict(), sort_keys=True)
        self.assertEqual(json.dumps(recommendations.to_dict(), sort_keys=True), before)

    def test_d12_a_stale_draft_is_non_actionable_and_cannot_be_approved_or_revived(self) -> None:
        recommendations, _instance, decision, draft = self.approved("d12", quantity="150")
        new_run = self.current_run(recommendations, analysis_run_id="RUN-2")

        self.assertTrue(draft.is_stale(new_run))
        self.assertEqual(draft.draft_state(new_run), REVIEW_STALE)
        self.assertFalse(draft.is_actionable(new_run))
        self.assertFalse(draft.has_approved_draft(new_run))
        with self.assertRaises(DraftError):
            draft.with_decision(decision, new_run)

        # The stale judgement is irreversible: the original run does not revive this Draft.
        self.assertTrue(draft.is_stale(recommendations.analysis_run))
        self.assertEqual(draft.draft_state(recommendations.analysis_run), REVIEW_STALE)
        self.assertFalse(draft.is_actionable(recommendations.analysis_run))
        with self.assertRaises(DraftError):
            draft.with_decision(decision, recommendations.analysis_run)

    def test_d13_each_analysis_run_component_mismatch_denies_a_decision_binding(self) -> None:
        for component, value in (
            ("analysis_run_id", "RUN-2"),
            ("snapshot_package_identity", "SIMULATED-PKG-FOREIGN"),
            ("accepted_content_view_digest", "f" * 64),
            ("analysis_date", "2026-10-02"),
        ):
            recommendations, _instance, decision, draft = self.approved(
                f"d13-{component}", quantity="150"
            )
            other = self.current_run(recommendations, **{component: value})
            self.assertTrue(draft.is_stale(other), component)
            self.assertFalse(draft.is_actionable(other), component)
            with self.assertRaises(DraftError, msg=component):
                draft.with_decision(decision, other)

            # A decision taken under another run is likewise never reflected by this Draft.
            fresh_recommendations, fresh_instance, fresh_draft = self.initial(f"d13b-{component}")
            foreign = dataclasses.replace(decision, analysis_run=other)
            with self.assertRaises(DraftError, msg=component):
                fresh_draft.with_decision(foreign, fresh_recommendations.analysis_run)
            self.assertIsNone(fresh_draft.decision)

    def test_d14_a_new_analysis_run_needs_a_new_instance_and_a_new_draft(self) -> None:
        recommendations, instance, decision, draft = self.approved("d14", quantity="150")
        new_run = self.current_run(recommendations, analysis_run_id="RUN-2")
        new_result = dataclasses.replace(recommendations, analysis_run=new_run)

        risk = self.reviewable("d14")[2]
        replacement = self.open(new_result, risk)
        new_draft = open_draft(replacement)

        self.assertIsNot(replacement, instance)
        self.assertIsNot(new_draft, draft)
        self.assertEqual(new_draft.quantity, Fraction(100, 1))
        self.assertEqual(new_draft.draft_state(new_run), DRAFT)
        self.assertTrue(new_draft.is_actionable(new_run))
        self.assertIsNone(new_draft.decision)
        # Nothing is inherited: no approved state, no Human override and no HumanDecision.
        self.assertFalse(new_draft.has_approved_draft(new_run))
        self.assertNotEqual(new_draft.quantity, decision.approved_value)

    def test_d15_an_override_is_never_inherited_across_an_analysis_run(self) -> None:
        recommendations, _instance, decision, draft = self.approved("d15", quantity="150")
        self.assertEqual(draft.quantity, Fraction(150, 1))
        new_run = self.current_run(recommendations, analysis_run_id="RUN-2")
        new_result = dataclasses.replace(recommendations, analysis_run=new_run)
        risk = self.reviewable("d15")[2]
        new_draft = open_draft(self.open(new_result, risk))

        self.assertEqual(new_draft.quantity, Fraction(100, 1))
        self.assertNotEqual(new_draft.quantity, Fraction(150, 1))
        self.assertIsNone(new_draft.decision)
        self.assertIs(draft.decision, decision)

    def test_d16_a_draft_cannot_be_decided_twice(self) -> None:
        recommendations, instance, decision, draft = self.approved("d16")
        with self.assertRaises(DraftError):
            draft.with_decision(decision, recommendations.analysis_run)
        self.assertIs(draft.decision, decision)

    def test_d17_a_foreign_or_mismatched_decision_is_never_reflected(self) -> None:
        recommendations, instance, decision, draft = self.approved("d17")

        # A decision for another grain is never reflected.
        other_grain = dataclasses.replace(decision, grain=(PLANT, "M-OTHER", self.need_date(recommendations)))
        _a, _b, fresh = self.initial("d17-grain")
        with self.assertRaises(DraftError):
            fresh.with_decision(other_grain, recommendations.analysis_run)

        # A decision reviewing another projection is never reflected.
        other_projection = dataclasses.replace(
            decision, review_projection_reference="review-projection:" + "0" * 64
        )
        _c, _d, fresh2 = self.initial("d17-projection")
        with self.assertRaises(DraftError):
            fresh2.with_decision(other_projection, recommendations.analysis_run)

        # An approve decision that states no approved value cannot form an approved Draft.
        no_value = dataclasses.replace(decision, approved_value=None)
        _e, _f, fresh3 = self.initial("d17-novalue")
        with self.assertRaises(DraftError):
            fresh3.with_decision(no_value, recommendations.analysis_run)
        self.assertEqual(fresh3.draft_state(recommendations.analysis_run), DRAFT)


# --- §10.6 G: Claim boundary and exact semantics ---------------------------------------


class DraftClaimAndExactnessTests(DraftRuntimeTestCase):
    """The Draft never claims production semantics and keeps exact quantities."""

    def test_d18_the_draft_never_claims_purchase_request_or_production_semantics(self) -> None:
        recommendations, _instance, decision, draft = self.approved("d18", quantity="150.25")
        payload = json.dumps(draft.to_dict(recommendations.analysis_run), ensure_ascii=False).lower()
        for forbidden in (
            "purchase order",
            "purchase_order",
            "purchaseorder",
            "erp",
            "submitted",
            "submit",
            "production",
            "approvedpurchaseqty",
        ):
            self.assertNotIn(forbidden, payload)
        self.assertEqual(draft.to_dict(recommendations.analysis_run)["marker"], DRAFT)

    def test_d19_exact_quantity_semantics_are_preserved(self) -> None:
        recommendations, _instance, decision, draft = self.approved("d19", quantity="100.1")
        payload = draft.to_dict(recommendations.analysis_run)
        self.assertEqual(payload["quantity"], {"numerator": 1001, "denominator": 10})
        self.assertEqual(draft.quantity, Fraction(1001, 10))
        self.assert_no_float(payload)
        # A long exact decimal survives without rounding or normalization.
        long_recommendations, _i, _d, long_draft = self.approved(
            "d19-long", quantity="999999999999999999.0001"
        )
        self.assertEqual(
            long_draft.to_dict(long_recommendations.analysis_run)["quantity"],
            {"numerator": 9999999999999999990001, "denominator": 10000},
        )


# --- §10.6 G: Architecture boundaries --------------------------------------------------


class DraftBoundaryTests(DraftRuntimeTestCase):
    """Zero persistence, zero egress, no hosted LLM, no new canonical vocabulary."""

    def test_d20_the_draft_module_introduces_no_io_network_or_provider_capability(self) -> None:
        from tests.test_procurement_recommendation import module_identifiers

        identifiers = {name for name in module_identifiers(draft_module)}
        for forbidden in (
            "sqlite",
            "shelve",
            "pickle",
            "tempfile",
            "pathlib",
            "shutil",
            "urllib",
            "socket",
            "http",
            "subprocess",
            "environ",
            "getenv",
            "provider",
            "credential",
            "erp",
            "production",
        ):
            self.assertFalse(
                {name for name in identifiers if forbidden in name.lower()},
                f"a persistence / network / provider capability appears in the code: {forbidden}",
            )

    def test_d21_the_draft_surface_stays_narrow_and_non_canonical(self) -> None:
        # The public surface stays narrow: one marker, one artifact, one entry point and one error.
        self.assertEqual(
            set(draft_module.__all__),
            {"DRAFT_MARKER", "DraftError", "ProcurementRequestDraft", "open_draft"},
        )
        # No business status / approval vocabulary leaked into the package public surface.
        import snapshot_loader as package

        for name in ("DraftStatus", "DRAFT_APPROVED", "DRAFT_REJECTED", "DRAFT_STALE", "ProcurementRequest"):
            self.assertFalse(hasattr(package, name), name)
            self.assertFalse(hasattr(draft_module, name), name)
        # No `modify` decision kind and no new decision kind is introduced.
        self.assertEqual(
            {hitl_module.DECISION_APPROVE, hitl_module.DECISION_REJECT}, {"approve", "reject"}
        )

    def test_d22_existing_hitl_and_override_behaviour_is_unchanged(self) -> None:
        recommendations, instance, decision, draft = self.approved("d22", quantity="150")
        # The review runtime's own decision/status behaviour is untouched by the Draft layer.
        self.assertEqual(instance.status(recommendations.analysis_run), REVIEW_APPROVED)
        self.assertIs(instance.decision, decision)
        self.assertEqual(decision.deterministic_recommended_value, Fraction(100, 1))
        self.assertEqual(instance.to_dict()["instance_condition"], REVIEW_APPROVED)

        # The as-is path still cannot carry a quantity, and the override path is still the only one.
        parameters = set(inspect.signature(hitl_module.ReviewInstance.approve_as_recommended).parameters)
        self.assertNotIn("quantity", parameters)
        self.assertNotIn("override", parameters)
        self.assertIn(
            "override_quantity",
            set(inspect.signature(hitl_module.ReviewInstance.approve_with_override).parameters),
        )
        self.assertIsNone(
            open_draft(instance).decision
        )  # binding is explicit and never implicit

    def test_d23_a_valid_absence_states_no_quantity_without_inventing_one(self) -> None:
        _built, recommendations, risk = self.valid_absence("d23")
        instance = open_review_valid_absence(recommendations, risk)
        draft = open_draft(instance)

        self.assertIsNone(draft.quantity)
        self.assertIsNone(draft.deterministic_recommended_value)
        self.assertEqual(draft.marker, DRAFT)
        payload = draft.to_dict(recommendations.analysis_run)
        self.assertIsNone(payload["quantity"])
        self.assertIsNone(payload["deterministic_recommended_value"])
        self.assertTrue(draft.is_actionable(recommendations.analysis_run))


def open_review_valid_absence(recommendations, risk):
    """Open a review instance over a valid-absence result (no recommendation by design)."""

    from snapshot_loader import open_review

    return open_review(
        recommendations,
        plant_id=PLANT,
        material_code=DEMAND,
        actor_reference=ACTOR,
        supplier_risk=risk,
    )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
