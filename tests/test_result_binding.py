"""Cross-result Analysis Run binding -- ``F3-RB1`` ／ ``Option A′`` (Human Decision, APPROVED).

Every deterministic rule result carries the existing :class:`AnalysisRunContext` of the construction
it was produced from, and every rule verifies its upstream results against its own construction
before it consumes any business value.  A foreign, stale or mismatched upstream result rejects the
**invocation** with the inherited ``PROVENANCE`` ／ ``PROVENANCE_MISMATCH`` finding; no foreign
business value is consumed, no business grain is manufactured and no ``NORMAL`` ／ ``SHORTAGE`` ／
numeric business result is returned.  A result that carries no binding at all is the distinct
``PROVENANCE`` ／ ``PROVENANCE_UNRESOLVED``.

The tests reuse the existing end-to-end chain fixture builder (``tests.test_shortage_calculation``),
which materialises one accepted package, constructs its canonical objects and runs the whole
deterministic chain, so a "foreign" result is a second genuine run of that same chain.
"""

from __future__ import annotations

import dataclasses
import unittest

from snapshot_loader import (
    AnalysisRunBindingError,
    CATEGORY_PROVENANCE,
    REASON_PROVENANCE_MISMATCH,
    REASON_PROVENANCE_UNRESOLVED,
    compute_effective_inbound,
    compute_opening_usable_inventory,
    compute_requirement_calculation,
    compute_shortage,
    compute_substitute_supply,
)
from tests.test_shortage_calculation import (
    D2,
    DEMAND,
    SOURCE,
    Demand,
    ShortageRuleTestCase,
)

#: The package identity the chain fixture builds by default.
PACKAGE_A = "SIMULATED-PKG-0001"


class AnalysisRunBindingTestCase(ShortageRuleTestCase):
    """Two genuine runs of the whole chain, plus the bindings every rule must carry."""

    def build_run_a(self):
        return self.build(
            demand=(Demand(DEMAND, DEMAND, "150", D2),),
            inventory={DEMAND: "100", SOURCE: "100"},
            safety_stock={DEMAND: "5", SOURCE: "0"},
            targets=((DEMAND, D2, "APPROVED"),),
            analysis_run_id="RUN-A",
            analysis_date="2026-10-01",
            package_id=PACKAGE_A,
            name="binding-run-a",
        )

    def build_run_b(
        self,
        *,
        inventory: dict[str, str] | None = None,
        analysis_run_id: str = "RUN-B",
        analysis_date: str = "2026-10-02",
        package_id: str = PACKAGE_A,
    ):
        return self.build(
            demand=(Demand(DEMAND, DEMAND, "150", D2),),
            inventory=inventory or {DEMAND: "1000", SOURCE: "1000"},
            safety_stock={DEMAND: "5", SOURCE: "0"},
            targets=((DEMAND, D2, "APPROVED"),),
            analysis_run_id=analysis_run_id,
            analysis_date=analysis_date,
            package_id=package_id,
            name="binding-run-b",
        )

    def assert_rejected(self, error: AnalysisRunBindingError, reason: str) -> None:
        self.assertEqual(error.issues[0].category, CATEGORY_PROVENANCE)
        self.assertEqual(error.issues[0].reason, reason)
        self.assertTrue(all(issue.category == CATEGORY_PROVENANCE for issue in error.issues))
        self.assertTrue(all(issue.reason == reason for issue in error.issues))
        self.assertEqual(error.to_dict()["outcome"], "INVOCATION_REJECTED")
        if reason == REASON_PROVENANCE_MISMATCH:
            self.assertTrue(error.mismatch)
            self.assertFalse(error.unresolved)
        else:
            self.assertTrue(error.unresolved)
            self.assertFalse(error.mismatch)


class ResultBindingTests(AnalysisRunBindingTestCase):
    def test_r4_every_result_carries_the_construction_analysis_run(self) -> None:
        built = self.build_run_a()
        run = built.construction.analysis_run
        self.assertEqual(run.analysis_run_id, "RUN-A")
        self.assertEqual(run.snapshot_package_identity, PACKAGE_A)
        for result in (
            built.requirements,
            built.inbounds,
            built.inventory,
            built.substitutes,
            built.shortage,
        ):
            with self.subTest(result=type(result).__name__):
                self.assertIs(result.analysis_run, run)
        # The same context, and the same deterministic business values, as before the binding.
        self.assert_quantity(self.grain(built, DEMAND, D2), "projected_available", "-50")
        self.assertEqual(
            self.grain(built, DEMAND, D2).classification, "SHORTAGE"
        )

    def test_r1_foreign_result_rejects_the_shortage_invocation(self) -> None:
        run_a = self.build_run_a()
        run_b = self.build_run_b()
        # Run B: same package identity and same demand, a different Analysis Run and a different
        # accepted content view (inventory 1000 instead of 100), i.e. the reviewed case.
        self.assertEqual(
            run_a.construction.analysis_run.analysis_run_id, "RUN-A"
        )
        self.assertEqual(run_b.construction.analysis_run.analysis_run_id, "RUN-B")
        with self.assertRaises(AnalysisRunBindingError) as caught:
            compute_shortage(
                run_a.construction,
                run_a.requirements,
                run_a.inbounds,
                run_b.inventory,
                run_a.substitutes,
            )
        error = caught.exception
        self.assert_rejected(error, REASON_PROVENANCE_MISMATCH)
        # The foreign inventory is named, and the forbidden silent combination is impossible.
        self.assertEqual(len(error.issues), 1)
        self.assertIn("BR-INVENTORY-001", error.issues[0].location)
        detail = error.issues[0].detail
        self.assertIn("analysis_run_id", detail)
        self.assertIn("accepted_content_view_digest", detail)
        self.assertIn("analysis_date", detail)
        # No business result exists at all: the invocation was rejected, not classified, so the
        # rejected combination can never surface as the 850 / NORMAL that mixing the runs implies.
        self.assertFalse(hasattr(error, "grains"))
        self.assertFalse(hasattr(error, "first_shortage_date"))
        self.assertNotIn("850", str(error.to_dict()))
        self.assertNotIn("NORMAL", str(error.to_dict()))
        # Run B on its own is a valid chain and does produce that different business value, so the
        # rejection is exactly about combining two runs rather than about either run being invalid.
        b_grain = self.grain(run_b, DEMAND, D2)
        self.assert_quantity(b_grain, "projected_available", "850")
        self.assertEqual(b_grain.classification, "NORMAL")

    def test_r2_same_package_different_accepted_content_view(self) -> None:
        run_a = self.build_run_a()
        run_b = self.build_run_b(analysis_run_id="RUN-A", analysis_date="2026-10-01")
        self.assertEqual(
            run_a.construction.analysis_run.snapshot_package_identity,
            run_b.construction.analysis_run.snapshot_package_identity,
        )
        self.assertNotEqual(
            run_a.construction.analysis_run.accepted_content_view_digest,
            run_b.construction.analysis_run.accepted_content_view_digest,
        )
        with self.assertRaises(AnalysisRunBindingError) as caught:
            compute_shortage(
                run_a.construction,
                run_a.requirements,
                run_a.inbounds,
                run_b.inventory,
                run_a.substitutes,
            )
        error = caught.exception
        self.assert_rejected(error, REASON_PROVENANCE_MISMATCH)
        self.assertIn("accepted_content_view_digest differ(s)", error.issues[0].detail)
        self.assertNotIn("analysis_run_id differ(s)", error.issues[0].detail)

    def test_r3_same_content_view_different_analysis_run(self) -> None:
        run_a = self.build_run_a()
        run_b = self.build_run_b(
            inventory={DEMAND: "100", SOURCE: "100"},
            analysis_run_id="RUN-B",
            analysis_date="2026-10-01",
        )
        self.assertEqual(
            run_a.construction.analysis_run.accepted_content_view_digest,
            run_b.construction.analysis_run.accepted_content_view_digest,
        )
        with self.assertRaises(AnalysisRunBindingError) as caught:
            compute_shortage(
                run_a.construction,
                run_a.requirements,
                run_a.inbounds,
                run_b.inventory,
                run_a.substitutes,
            )
        error = caught.exception
        self.assert_rejected(error, REASON_PROVENANCE_MISMATCH)
        self.assertIn("analysis_run_id differ(s)", error.issues[0].detail)
        self.assertNotIn("accepted_content_view_digest differ(s)", error.issues[0].detail)

    def test_r5_inbound_rejects_a_foreign_requirement_result(self) -> None:
        run_a = self.build_run_a()
        run_b = self.build_run_b()
        with self.assertRaises(AnalysisRunBindingError) as caught:
            compute_effective_inbound(run_a.construction, run_b.requirements)
        error = caught.exception
        self.assert_rejected(error, REASON_PROVENANCE_MISMATCH)
        self.assertIn("BR-REQUIREMENT-001", error.issues[0].location)

    def test_r5_substitute_rejects_a_foreign_requirement_result(self) -> None:
        run_a = self.build_run_a()
        run_b = self.build_run_b()
        with self.assertRaises(AnalysisRunBindingError) as caught:
            compute_substitute_supply(
                run_a.construction,
                run_a.inventory,
                requirements=run_b.requirements,
            )
        self.assert_rejected(caught.exception, REASON_PROVENANCE_MISMATCH)
        self.assertIn("BR-REQUIREMENT-001", caught.exception.issues[0].location)

    def test_r5_substitute_rejects_a_foreign_inventory_result(self) -> None:
        run_a = self.build_run_a()
        run_b = self.build_run_b()
        with self.assertRaises(AnalysisRunBindingError) as caught:
            compute_substitute_supply(
                run_a.construction,
                run_b.inventory,
                requirements=run_a.requirements,
            )
        self.assert_rejected(caught.exception, REASON_PROVENANCE_MISMATCH)
        self.assertIn("BR-INVENTORY-001", caught.exception.issues[0].location)

    def test_r5_every_foreign_upstream_is_reported_together(self) -> None:
        run_a = self.build_run_a()
        run_b = self.build_run_b()
        with self.assertRaises(AnalysisRunBindingError) as caught:
            compute_shortage(
                run_a.construction,
                run_b.requirements,
                run_b.inbounds,
                run_b.inventory,
                run_b.substitutes,
            )
        error = caught.exception
        self.assert_rejected(error, REASON_PROVENANCE_MISMATCH)
        self.assertEqual(len(error.issues), 4)
        self.assertEqual(
            [issue.location for issue in error.issues],
            [
                "result_binding[BR-REQUIREMENT-001]",
                "result_binding[BR-INBOUND-001]",
                "result_binding[BR-INVENTORY-001]",
                "result_binding[BR-SUBSTITUTE-001]",
            ],
        )

    def test_r6_a_missing_binding_is_unresolved_not_mismatch(self) -> None:
        run_a = self.build_run_a()
        unbound = dataclasses.replace(run_a.requirements, analysis_run=None)
        with self.assertRaises(AnalysisRunBindingError) as caught:
            compute_effective_inbound(run_a.construction, unbound)
        error = caught.exception
        self.assert_rejected(error, REASON_PROVENANCE_UNRESOLVED)
        self.assertIn("carries no Analysis Run binding", error.issues[0].detail)

    def test_r6_unresolved_shortage_binding_is_not_a_grain_result(self) -> None:
        run_a = self.build_run_a()
        unbound = dataclasses.replace(run_a.substitutes, analysis_run=None)
        with self.assertRaises(AnalysisRunBindingError) as caught:
            compute_shortage(
                run_a.construction,
                run_a.requirements,
                run_a.inbounds,
                run_a.inventory,
                unbound,
            )
        error = caught.exception
        self.assert_rejected(error, REASON_PROVENANCE_UNRESOLVED)
        # A mismatch and an unestablished binding are never merged into one outcome.
        self.assertNotEqual(error.issues[0].reason, REASON_PROVENANCE_MISMATCH)

    def test_mismatch_is_not_a_consistency_conflict_or_a_grain_defect(self) -> None:
        run_a = self.build_run_a()
        run_b = self.build_run_b()
        with self.assertRaises(AnalysisRunBindingError) as caught:
            compute_shortage(
                run_a.construction,
                run_a.requirements,
                run_a.inbounds,
                run_b.inventory,
                run_a.substitutes,
            )
        for issue in caught.exception.issues:
            with self.subTest(issue=issue.location):
                self.assertEqual(issue.category, CATEGORY_PROVENANCE)
                self.assertNotEqual(issue.reason, "CONSISTENCY_CONFLICT")
                self.assertNotEqual(issue.reason, "SEMANTIC_UNRESOLVED")
                self.assertNotIn("DATA_INCOMPLETE", issue.reason or "")
                self.assertEqual(issue.layer, 2)
                self.assertIn("no result is produced", issue.blast_radius or "")

    def test_a_rejected_invocation_consumes_nothing(self) -> None:
        # The rule must not touch the foreign upstream result at all: project it onto an object
        # whose every business attribute raises, keeping only the provenance binding.
        run_a = self.build_run_a()

        class BoundOnlyInventory:
            analysis_run = dataclasses.replace(
                run_a.inventory.analysis_run, analysis_run_id="RUN-B"
            )

            def __getattr__(self, name: str):
                raise AssertionError(
                    f"compute_shortage read the foreign inventory.{name}; a rejected invocation "
                    "consumes no foreign business value"
                )

        with self.assertRaises(AnalysisRunBindingError) as caught:
            compute_shortage(
                run_a.construction,
                run_a.requirements,
                run_a.inbounds,
                BoundOnlyInventory(),
                run_a.substitutes,
            )
        self.assert_rejected(caught.exception, REASON_PROVENANCE_MISMATCH)

    def test_the_chain_is_deterministic_within_one_run(self) -> None:
        first = self.build_run_a()
        second = self.build_run_a()
        self.assertEqual(first.shortage.to_dict(), second.shortage.to_dict())
        self.assertEqual(
            first.shortage.analysis_run.analysis_run_id,
            second.shortage.analysis_run.analysis_run_id,
        )
        # Every rule of the chain still runs on its own binding, and the intermediate boundary
        # verifies the same run.
        self.assertIs(
            compute_requirement_calculation(first.construction).analysis_run,
            first.construction.analysis_run,
        )
        self.assertIs(
            compute_opening_usable_inventory(first.construction).analysis_run,
            first.construction.analysis_run,
        )


if __name__ == "__main__":  # pragma: no cover - direct invocation
    unittest.main()
