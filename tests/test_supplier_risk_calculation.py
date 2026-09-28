"""``BR-SUPPLIER-RISK-001`` Supplier Risk Evidence calculation (Issue #170).

Covers the registered deterministic risk semantics of ``poc-design-v0.2.md`` §2.7.4 -- §2.7.16 on the
consumed ``A′`` input result: exact calendar-date ``DaysUntilNeed``, the ``LeadTimeRisk`` /
``DeliveryRisk`` / ``QualityRisk`` thresholds, ``OverallSupplierRisk`` as the max severity of the reliable
dimensions or ``DATA_INCOMPLETE``, the field-level fail-safes, the card universe and the verbatim
propagation of the seam's fail-closed evidence outcomes.

The fixtures reuse the end-to-end chain builder of ``tests.test_supplier_risk_input``, so every test runs
the whole registered chain and the rule only ever consumes the seam's read-only result.
"""

from __future__ import annotations

import ast
import dataclasses
import json
import unittest
from pathlib import Path

from snapshot_loader import (
    RISK_DATA_INCOMPLETE,
    RISK_HIGH,
    RISK_LOW,
    RISK_MEDIUM,
    SUPPLIER_RISK_STAGE,
    SupplierRiskEvidenceCard,
    SupplierRiskResult,
    compute_supplier_risk,
)
from tests.test_procurement_policy_input import moq_policy_record
from tests.test_supplier_risk_input import (
    DEMAND,
    OTHER,
    OTHER_PLANT,
    PLANT,
    SUPPLIER,
    SUPPLIER_B,
    SupplierRiskInputTestCase,
    module_identifiers,
    performance_record,
    relationship_record,
)

INELIGIBLE_BASIS = "SIMULATED-SOURCING-INELIGIBLE"
UNREGISTERED_BASIS = "SIMULATED-SOURCING-UNREGISTERED"
D20 = "2026-10-21"


class SupplierRiskCalculationTests(SupplierRiskInputTestCase):
    """The deterministic risk calculation of the consumed evaluation contexts."""

    # --- helpers ---------------------------------------------------------------------

    def risk(self, built, recommendations=None) -> SupplierRiskResult:
        """The rule result of one fixture, consuming the seam result only."""

        return compute_supplier_risk(self.supplier_input(built, recommendations))

    def card(
        self,
        built,
        *,
        plant: object = PLANT,
        supplier: object = SUPPLIER,
        material: object = DEMAND,
        recommendations=None,
    ) -> SupplierRiskEvidenceCard:
        """The single card of one exact evaluation request, asserted to exist."""

        result = self.risk(built, recommendations)
        card = result.card_for(plant, supplier, material)
        assert card is not None
        return card

    def chain(self, name: str, *, performances=(), relationships=None, identities=None, **kwargs):
        """One eligible-relationship chain with the given Supplier Performance records."""

        return self.build_chain(
            supplier_identities=(
                ({"supplier_id": SUPPLIER},) if identities is None else tuple(identities)
            ),
            supplier_relationships=(
                (relationship_record(),) if relationships is None else tuple(relationships)
            ),
            supplier_performances=tuple(performances),
            name=name,
            **kwargs,
        )

    def example_chain(self, name: str, *, delivery: str, quality: str, lead_time: str):
        """A chain whose exact ``DaysUntilNeed`` is 20 (``D20`` against AnalysisDate 2026-10-01)."""

        return self.chain(
            name,
            demands=((DEMAND, "130", D20),),
            performances=(
                performance_record(
                    delivery=delivery, quality=quality, lead_time=lead_time
                ),
            ),
        )

    # --- 1 ／ 2: the registered deterministic examples ---------------------------------

    def test_b1_example_a_is_low_on_every_dimension(self) -> None:
        built = self.example_chain(
            "b1-example-a", delivery="97", quality="99", lead_time="10"
        )
        card = self.card(built)
        self.assertEqual(card.days_until_need, 20)
        self.assertEqual(card.days_until_need_text, "20")
        self.assertEqual(card.lead_time_risk, RISK_LOW)
        self.assertEqual(card.delivery_risk, RISK_LOW)
        self.assertEqual(card.quality_risk, RISK_LOW)
        self.assertEqual(card.overall_supplier_risk, RISK_LOW)
        self.assertTrue(card.evidence_complete)
        self.assertIsNone(card.status)
        self.assertEqual(card.rule_issues, ())
        payload = card.to_dict()
        self.assertEqual(payload["DaysUntilNeed"], "20")
        self.assertEqual(payload["LeadTimeRisk"], "LOW")
        self.assertEqual(payload["OverallSupplierRisk"], "LOW")
        self.assertEqual(payload["status"], None)
        self.assertTrue(payload["evidence_complete"])

    def test_b2_example_b_is_high_on_every_dimension(self) -> None:
        built = self.example_chain(
            "b2-example-b", delivery="84", quality="94", lead_time="35"
        )
        card = self.card(built)
        self.assertEqual(card.days_until_need, 20)
        self.assertEqual(card.lead_time_risk, RISK_HIGH)
        self.assertEqual(card.delivery_risk, RISK_HIGH)
        self.assertEqual(card.quality_risk, RISK_HIGH)
        self.assertEqual(card.overall_supplier_risk, RISK_HIGH)
        self.assertTrue(card.evidence_complete)

    # --- 3: max severity --------------------------------------------------------------

    def test_b3_overall_is_the_max_severity_of_the_reliable_dimensions(self) -> None:
        cases = (
            # lead time HIGH, delivery MEDIUM, quality LOW -> HIGH
            ("35", "92", "99", RISK_HIGH),
            # lead time LOW, delivery MEDIUM, quality LOW -> MEDIUM
            ("5", "90", "99", RISK_MEDIUM),
            # lead time LOW, delivery LOW, quality MEDIUM -> MEDIUM
            ("5", "99", "96", RISK_MEDIUM),
            # lead time LOW, delivery HIGH, quality LOW -> HIGH
            ("5", "89", "99", RISK_HIGH),
        )
        for lead_time, delivery, quality, expected in cases:
            with self.subTest(lead_time=lead_time, delivery=delivery, quality=quality):
                card = self.card(
                    self.example_chain(
                        f"b3-{lead_time}-{delivery}-{quality}",
                        delivery=delivery,
                        quality=quality,
                        lead_time=lead_time,
                    )
                )
                self.assertEqual(card.overall_supplier_risk, expected)
                self.assertTrue(card.evidence_complete)
        # Never a weighted score: equal inputs can only ever yield one of the three registered levels.
        card = self.card(
            self.example_chain("b3-weight", delivery="99", quality="99", lead_time="5")
        )
        self.assertIn(
            card.overall_supplier_risk, (RISK_LOW, RISK_MEDIUM, RISK_HIGH)
        )

    # --- 4 ／ 5: the DaysUntilNeed boundary -------------------------------------------

    def test_b4_lead_time_equal_to_days_until_need_is_low(self) -> None:
        card = self.card(
            self.example_chain("b4-equal", delivery="97", quality="99", lead_time="20")
        )
        self.assertEqual(card.days_until_need, 20)
        self.assertEqual(card.standard_lead_time_days, "20")
        self.assertEqual(card.lead_time_risk, RISK_LOW)
        # One day longer is HIGH -- the boundary is exact, not fuzzy.
        card = self.card(
            self.example_chain("b4-over", delivery="97", quality="99", lead_time="20.0001")
        )
        self.assertEqual(card.lead_time_risk, RISK_HIGH)

    def test_b5_negative_days_until_need_fails_lead_time_closed(self) -> None:
        built = self.chain(
            "b5-negative-days",
            demands=((DEMAND, "130", "2026-09-25"),),
            performances=(performance_record(delivery="97", quality="99", lead_time="1"),),
        )
        card = self.card(built)
        self.assertEqual(card.days_until_need, -6)
        self.assertEqual(card.days_until_need_text, "-6")
        self.assertEqual(card.lead_time_risk, RISK_DATA_INCOMPLETE)
        # The exact negative value stays visible (never clamped) and the performance dimensions stay.
        self.assertEqual(card.delivery_risk, RISK_LOW)
        self.assertEqual(card.quality_risk, RISK_LOW)
        self.assertEqual(card.overall_supplier_risk, RISK_DATA_INCOMPLETE)
        self.assertFalse(card.evidence_complete)
        self.assertEqual(
            [(issue.category, issue.reason) for issue in card.rule_issues],
            [("FIELD_VALUE", "OUT_OF_DEFINED_RANGE")],
        )
        self.assertEqual(card.rule_issues[0].location.endswith(".DaysUntilNeed"), True)

    # --- 6 ／ 7: date fail-safes -------------------------------------------------------

    def test_b6_analysis_date_missing_or_invalid_fails_lead_time_closed(self) -> None:
        built = self.chain("b6-analysis-date", performances=(performance_record(),))
        seam = self.supplier_input(built)
        for label, value, expected_reason in (
            ("missing", None, "MISSING"),
            ("null", None, "MISSING"),
            ("invalid-form", "2026/10/01", "INVALID_TYPE"),
            ("impossible", "2026-02-30", "INVALID_TYPE"),
        ):
            with self.subTest(case=label):
                tampered = dataclasses.replace(
                    seam,
                    analysis_run=dataclasses.replace(
                        seam.analysis_run, analysis_date=value
                    ),
                )
                card = compute_supplier_risk(tampered).card_for(PLANT, SUPPLIER, DEMAND)
                assert card is not None
                self.assertIsNone(card.days_until_need)
                self.assertIsNone(card.days_until_need_text)
                self.assertEqual(card.lead_time_risk, RISK_DATA_INCOMPLETE)
                self.assertEqual(card.delivery_risk, RISK_LOW)
                self.assertEqual(card.quality_risk, RISK_LOW)
                self.assertEqual(card.overall_supplier_risk, RISK_DATA_INCOMPLETE)
                analysis_issues = [
                    issue
                    for issue in card.rule_issues
                    if issue.location.endswith(".AnalysisDate")
                ]
                self.assertEqual(len(analysis_issues), 1)
                self.assertEqual(
                    (analysis_issues[0].category, analysis_issues[0].reason),
                    ("FIELD_VALUE", expected_reason),
                )

    def test_b7_recommendation_need_date_unresolved_or_invalid_fails_lead_time_closed(self) -> None:
        # Genuine unresolved state: the consumed upstream result states an unresolved need date.
        unresolved = self.chain(
            "b7-need-date-unresolved",
            demands=((DEMAND, "10", "2026-10-10"), (DEMAND, "10", D20)),
            targets=((DEMAND, "2026-10-10", "APPROVED"), (DEMAND, D20, "UNRESOLVED")),
            performances=(performance_record(),),
        )
        card = self.card(unresolved)
        self.assertIsNone(card.recommendation_need_date)
        self.assertIsNone(card.days_until_need)
        self.assertEqual(card.lead_time_risk, RISK_DATA_INCOMPLETE)
        self.assertEqual(card.delivery_risk, RISK_LOW)
        self.assertEqual(card.quality_risk, RISK_LOW)
        self.assertEqual(card.overall_supplier_risk, RISK_DATA_INCOMPLETE)
        # The seam already published the registered need-date finding: the rule adds no duplicate.
        self.assertEqual(
            [(issue.category, issue.reason) for issue in card.upstream_issues],
            [("SEMANTIC_RESOLUTION", "SEMANTIC_UNRESOLVED")],
        )
        self.assertEqual(card.rule_issues, ())

        # A present but non-C-3 date is a form defect the seam does not decide, so the rule states it.
        built = self.chain("b7-need-date-invalid", performances=(performance_record(),))
        seam = self.supplier_input(built)
        context = seam.context_for(PLANT, SUPPLIER, DEMAND)
        assert context is not None
        tampered = dataclasses.replace(
            seam,
            evaluation_contexts=(
                dataclasses.replace(context, recommendation_need_date="20-10-2026"),
            ),
        )
        invalid_card = compute_supplier_risk(tampered).card_for(
            PLANT, SUPPLIER, DEMAND
        )
        assert invalid_card is not None
        self.assertIsNone(invalid_card.days_until_need)
        self.assertEqual(invalid_card.lead_time_risk, RISK_DATA_INCOMPLETE)
        need_date_issues = [
            issue
            for issue in invalid_card.rule_issues
            if issue.location.endswith(".RecommendationNeedDate")
        ]
        self.assertEqual(
            [(issue.category, issue.reason) for issue in need_date_issues],
            [("FIELD_VALUE", "INVALID_TYPE")],
        )

    # --- 8: lead time fail-safes ------------------------------------------------------

    def test_b8_lead_time_missing_invalid_or_negative_fails_closed(self) -> None:
        missing = performance_record()
        missing.pop("standard_lead_time_days")
        cases = (
            ("missing-property", missing, "MISSING"),
            ("json-null", performance_record(lead_time=None), "MISSING"),
            ("not-a-number", performance_record(lead_time="ten"), "INVALID_TYPE"),
            ("exponent-form", performance_record(lead_time="1e1"), "INVALID_TYPE"),
            ("negative", performance_record(lead_time="-3"), "OUT_OF_DEFINED_RANGE"),
        )
        for label, record, expected_reason in cases:
            with self.subTest(case=label):
                card = self.card(self.chain(f"b8-{label}", performances=(record,)))
                self.assertEqual(card.standard_lead_time_days, record.get("standard_lead_time_days"))
                self.assertEqual(card.lead_time_risk, RISK_DATA_INCOMPLETE)
                self.assertEqual(card.delivery_risk, RISK_LOW)
                self.assertEqual(card.quality_risk, RISK_LOW)
                self.assertEqual(card.overall_supplier_risk, RISK_DATA_INCOMPLETE)
                lead_issues = [
                    issue
                    for issue in card.rule_issues
                    if issue.location.endswith(".standard_lead_time_days")
                ]
                self.assertEqual(
                    [(issue.category, issue.reason) for issue in lead_issues],
                    [("FIELD_VALUE", expected_reason)],
                )
                assert lead_issues[0].affected_evidence is not None
                self.assertIn("|", lead_issues[0].affected_evidence)

    # --- 9 ／ 10: percentage thresholds and valid extremes ----------------------------

    def test_b9_delivery_thresholds_and_extremes(self) -> None:
        cases = (
            ("100", RISK_LOW),
            ("99.5", RISK_LOW),
            ("95", RISK_LOW),
            ("94.999", RISK_MEDIUM),
            ("92", RISK_MEDIUM),
            ("90", RISK_MEDIUM),
            ("89.999", RISK_HIGH),
            ("0", RISK_HIGH),
        )
        for delivery, expected in cases:
            with self.subTest(delivery=delivery):
                card = self.card(
                    self.example_chain(
                        f"b9-{delivery}",
                        delivery=delivery,
                        quality="99",
                        lead_time="5",
                    )
                )
                self.assertEqual(card.delivery_risk, expected)
        for delivery, expected_reason in (
            ("100.01", "OUT_OF_DEFINED_RANGE"),
            ("-1", "OUT_OF_DEFINED_RANGE"),
            ("ninety", "INVALID_TYPE"),
            (None, "MISSING"),
        ):
            with self.subTest(delivery=delivery):
                card = self.card(
                    self.example_chain(
                        f"b9-bad-{delivery}",
                        delivery=delivery,  # type: ignore[arg-type]
                        quality="99",
                        lead_time="5",
                    )
                )
                self.assertEqual(card.delivery_risk, RISK_DATA_INCOMPLETE)
                self.assertEqual(card.quality_risk, RISK_LOW)
                self.assertEqual(card.overall_supplier_risk, RISK_DATA_INCOMPLETE)
                issues = [
                    issue
                    for issue in card.rule_issues
                    if issue.location.endswith(".DeliveryPerformance")
                ]
                self.assertEqual(len(issues), 1)
                self.assertEqual(issues[0].reason, expected_reason)

    def test_b10_quality_thresholds_and_extremes(self) -> None:
        cases = (
            ("100", RISK_LOW),
            ("98", RISK_LOW),
            ("97.999", RISK_MEDIUM),
            ("96", RISK_MEDIUM),
            ("95", RISK_MEDIUM),
            ("94.999", RISK_HIGH),
            ("0", RISK_HIGH),
        )
        for quality, expected in cases:
            with self.subTest(quality=quality):
                card = self.card(
                    self.example_chain(
                        f"b10-{quality}",
                        delivery="99",
                        quality=quality,
                        lead_time="5",
                    )
                )
                self.assertEqual(card.quality_risk, expected)
        for quality, expected_reason in (
            ("100.5", "OUT_OF_DEFINED_RANGE"),
            ("-0.5", "OUT_OF_DEFINED_RANGE"),
            ("high", "INVALID_TYPE"),
            (None, "MISSING"),
        ):
            with self.subTest(quality=quality):
                card = self.card(
                    self.example_chain(
                        f"b10-bad-{quality}",
                        delivery="99",
                        quality=quality,  # type: ignore[arg-type]
                        lead_time="5",
                    )
                )
                self.assertEqual(card.quality_risk, RISK_DATA_INCOMPLETE)
                self.assertEqual(card.delivery_risk, RISK_LOW)
                self.assertEqual(card.overall_supplier_risk, RISK_DATA_INCOMPLETE)
                issues = [
                    issue
                    for issue in card.rule_issues
                    if issue.location.endswith(".QualityPerformance")
                ]
                self.assertEqual(len(issues), 1)
                self.assertEqual(issues[0].reason, expected_reason)

    # --- 11 ／ 12: the performance period and applicability ---------------------------

    def test_b11_performance_period_missing_or_invalid(self) -> None:
        # Variant 1: the period property is absent, so canonicalization leaves the record unresolved and
        # Option A applicability is unresolved -> all four outputs fail closed (no dimension is read).
        unresolved_record = performance_record()
        unresolved_record.pop("PerformancePeriod")
        card = self.card(
            self.chain("b11-period-absent", performances=(unresolved_record,))
        )
        self.assertIsNone(card.performance)
        self.assertEqual(card.performance_period, None)
        self.assertEqual(
            [card.lead_time_risk, card.delivery_risk, card.quality_risk],
            [RISK_DATA_INCOMPLETE, RISK_DATA_INCOMPLETE, RISK_DATA_INCOMPLETE],
        )
        self.assertEqual(card.overall_supplier_risk, RISK_DATA_INCOMPLETE)
        # The seam's registered applicability finding is preserved; no field finding is duplicated.
        self.assertEqual(
            [(issue.category, issue.reason) for issue in card.upstream_issues],
            [("SEMANTIC_RESOLUTION", "SEMANTIC_UNRESOLVED")],
        )
        self.assertEqual(card.rule_issues, ())

        # Variant 2: the observation is uniquely determined but its period itself is unusable, so only
        # the period-dependent dimensions fail closed while LeadTimeRisk is computed from its own inputs.
        for label, period, expected_reason in (
            ("json-null", None, "MISSING"),
            ("not-a-string", 20260301, "INVALID_TYPE"),
            ("empty", "", "INVALID_TYPE"),
        ):
            with self.subTest(case=label):
                card = self.card(
                    self.chain(
                        f"b11-period-{label}",
                        performances=(
                            performance_record(
                                period=period,
                                delivery="97",
                                quality="99",
                                lead_time="5",
                            ),
                        ),
                    )
                )
                self.assertIsNotNone(card.performance)
                self.assertEqual(card.performance_period, period)
                self.assertEqual(card.lead_time_risk, RISK_LOW)
                self.assertEqual(card.delivery_risk, RISK_DATA_INCOMPLETE)
                self.assertEqual(card.quality_risk, RISK_DATA_INCOMPLETE)
                self.assertEqual(card.overall_supplier_risk, RISK_DATA_INCOMPLETE)
                # One finding for the one field defect of this request, naming both affected dimensions.
                period_issues = [
                    issue
                    for issue in card.rule_issues
                    if issue.location.endswith(".PerformancePeriod")
                ]
                self.assertEqual(len(period_issues), 1)
                self.assertEqual(period_issues[0].category, "FIELD_VALUE")
                self.assertEqual(period_issues[0].reason, expected_reason)
                self.assertIn("DeliveryRisk", period_issues[0].consequence_context or "")
                self.assertIn("QualityRisk", period_issues[0].consequence_context or "")
                self.assertIn("|", period_issues[0].affected_evidence or "")

    def test_b12_applicability_unresolved_fails_every_dimension_closed(self) -> None:
        # Two distinct resolved periods: Option A applicability is unresolved, so the rule must not read
        # any performance field at all -- and must not pick an observation.
        card = self.card(
            self.chain(
                "b12-two-periods",
                performances=(
                    performance_record(period="2026-Q2", lead_time="1", delivery="100"),
                    performance_record(period="2026-Q3", lead_time="99", delivery="0"),
                ),
            )
        )
        self.assertIsNone(card.performance)
        self.assertEqual(card.days_until_need, 19)
        self.assertEqual(
            [card.lead_time_risk, card.delivery_risk, card.quality_risk],
            [RISK_DATA_INCOMPLETE, RISK_DATA_INCOMPLETE, RISK_DATA_INCOMPLETE],
        )
        self.assertEqual(card.overall_supplier_risk, RISK_DATA_INCOMPLETE)
        self.assertEqual(card.reliable_dimensions, ())
        # A competing unresolved record is equally not selectable.
        competing = self.card(
            self.chain(
                "b12-competing",
                performances=(
                    performance_record(period="2026-Q3"),
                    performance_record(period="2026-Q3", drop_period=True),
                ),
            )
        )
        self.assertIsNone(competing.performance)
        self.assertEqual(competing.overall_supplier_risk, RISK_DATA_INCOMPLETE)

    # --- 13 ／ 14: overall completeness ------------------------------------------------

    def test_b13_one_unreliable_dimension_makes_only_the_overall_incomplete(self) -> None:
        record = performance_record(delivery="97", quality="99")
        record.pop("standard_lead_time_days")
        card = self.card(self.chain("b13-one-unreliable", performances=(record,)))
        self.assertEqual(card.lead_time_risk, RISK_DATA_INCOMPLETE)
        self.assertEqual(card.delivery_risk, RISK_LOW)
        self.assertEqual(card.quality_risk, RISK_LOW)
        self.assertEqual(card.overall_supplier_risk, RISK_DATA_INCOMPLETE)
        self.assertFalse(card.evidence_complete)
        self.assertEqual(card.status, RISK_DATA_INCOMPLETE)
        # The reliable dimensions are retained on the card and in the payload.
        self.assertEqual(
            card.reliable_dimensions,
            (("DeliveryRisk", RISK_LOW), ("QualityRisk", RISK_LOW)),
        )
        payload = card.to_dict()
        self.assertEqual(payload["DeliveryRisk"], "LOW")
        self.assertEqual(payload["QualityRisk"], "LOW")
        self.assertEqual(payload["LeadTimeRisk"], "DATA_INCOMPLETE")
        self.assertEqual(payload["status"], "DATA_INCOMPLETE")
        self.assertEqual(len(payload["reliable_dimensions"]), 2)

    def test_b14_performance_updated_at_never_decides_completeness(self) -> None:
        for label, record in (
            ("json-null", performance_record(updated=None)),
            ("absent", None),
        ):
            with self.subTest(case=label):
                if record is None:
                    record = performance_record()
                    record.pop("PerformanceUpdatedAt")
                card = self.card(self.chain(f"b14-{label}", performances=(record,)))
                self.assertIsNone(card.performance_updated_at)
                self.assertEqual(card.lead_time_risk, RISK_LOW)
                self.assertEqual(card.delivery_risk, RISK_LOW)
                self.assertEqual(card.quality_risk, RISK_LOW)
                self.assertEqual(card.overall_supplier_risk, RISK_LOW)
                self.assertTrue(card.evidence_complete)
                self.assertEqual(card.rule_issues, ())

    # --- 15: fail-closed propagation --------------------------------------------------

    def test_b15_consumes_the_seam_outcomes_verbatim(self) -> None:
        built = self.chain(
            "b15-fail-closed",
            relationships=(relationship_record(basis=UNREGISTERED_BASIS),),
            performances=(performance_record(),),
        )
        seam = self.supplier_input(built)
        result = compute_supplier_risk(seam)
        self.assertEqual(result.cards, ())
        self.assertEqual(len(result.fail_closed_outcomes), 1)
        # The very same object is propagated: no copy, no recalculation, no re-scoping.
        self.assertIs(result.fail_closed_outcomes[0], seam.evidence_outcomes[0])
        self.assertEqual(
            result.fail_closed_outcomes[0].status, RISK_DATA_INCOMPLETE
        )
        self.assertEqual(
            result.to_dict()["fail_closed_outcomes"],
            [seam.evidence_outcomes[0].to_dict()],
        )
        # No risk identifier may appear anywhere in a fail-closed row's payload.
        payload = result.fail_closed_outcomes[0].to_dict()
        for forbidden in ("LeadTimeRisk", "DeliveryRisk", "QualityRisk", "OverallSupplierRisk"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, payload)

    # --- 16 -- 20: the card universe --------------------------------------------------

    def test_b16_the_card_universe_is_exactly_the_consumed_contexts(self) -> None:
        built = self.chain("b16-universe", performances=(performance_record(),))
        seam = self.supplier_input(built)
        self.assertEqual(len(seam.evaluation_contexts), 1)
        result = compute_supplier_risk(seam)
        self.assertEqual(len(result.cards), 1)
        self.assertEqual(result.cards[0].evaluation_context, (PLANT, DEMAND, SUPPLIER))
        self.assertEqual(result.cards[0].grain, (SUPPLIER, DEMAND))
        self.assertEqual(result.analysis_run, seam.analysis_run)
        self.assertEqual(result.cards_for(SUPPLIER, DEMAND), result.cards)

    def test_b17_capability_unavailable_produces_no_card(self) -> None:
        built = self.build_chain(
            supplier_identities=(),
            supplier_relationships=(relationship_record(),),
            supplier_performances=(performance_record(),),
            name="b17-capability-unavailable",
        )
        seam = self.supplier_input(built)
        self.assertFalse(seam.capability_available)
        self.assertEqual(seam.evaluation_contexts, ())
        result = compute_supplier_risk(seam)
        self.assertEqual(result.cards, ())
        self.assertEqual(result.fail_closed_outcomes, ())
        self.assertFalse(result.capability_available)
        self.assertEqual(
            [(issue.category, issue.reason) for issue in result.capability_issues],
            [("EVIDENCE_AVAILABILITY", "EVIDENCE_ROLE_NOT_PROVIDED")],
        )
        # Capability unavailable is never expressed as a business DATA_INCOMPLETE card.
        self.assertNotIn("overall_supplier_risk", result.to_dict())

    def test_b18_ineligible_relationship_produces_no_card(self) -> None:
        built = self.chain(
            "b18-ineligible",
            relationships=(relationship_record(basis=INELIGIBLE_BASIS),),
            performances=(performance_record(),),
        )
        result = self.risk(built)
        self.assertEqual(result.cards, ())
        self.assertEqual(result.fail_closed_outcomes, ())
        self.assertEqual(result.issues, ())

    def test_b19_valid_absence_produces_no_card(self) -> None:
        built = self.build_chain(
            demands=((DEMAND, "10", "2026-10-21"),),
            supplier_identities=({"supplier_id": SUPPLIER},),
            supplier_relationships=(relationship_record(),),
            supplier_performances=(performance_record(),),
            name="b19-valid-absence",
        )
        result = self.risk(built)
        self.assertEqual(result.cards, ())
        self.assertEqual(result.fail_closed_outcomes, ())
        self.assertTrue(result.is_valid_absence(PLANT, DEMAND))
        self.assertEqual(result.valid_absence_grains, ((PLANT, DEMAND),))

    def test_b20_performance_only_and_unkeyable_pairs_produce_no_keyed_card(self) -> None:
        # ROOT_RELATIONSHIP_ABSENT: performance evidence claims the pair, no relationship states it.
        performance_only = self.build_chain(
            supplier_relationships=(
                relationship_record(SUPPLIER, OTHER, basis="SIMULATED-SOURCING-ELIGIBLE"),
            ),
            supplier_performances=(performance_record(SUPPLIER, DEMAND),),
            name="b20-performance-only",
        )
        result = self.risk(performance_only)
        self.assertEqual(result.cards, ())
        self.assertEqual(result.fail_closed_outcomes, ())
        self.assertEqual(result.cards_for(SUPPLIER, DEMAND), ())

        # Unkeyable pair: the relationship evidence states no reliable pair grain.
        unkeyable = self.chain(
            "b20-unkeyable",
            relationships=(relationship_record(supplier=[]),),
            performances=(performance_record(),),
        )
        unkeyable_result = self.risk(unkeyable)
        self.assertEqual(unkeyable_result.cards, ())
        self.assertEqual(unkeyable_result.fail_closed_outcomes, ())
        self.assertEqual(len(self.supplier_input(unkeyable).unkeyable_relationships), 1)
        self.assertEqual(
            [
                (issue.category, issue.reason)
                for issue in self.supplier_input(unkeyable).identity_issues
            ],
            [("IDENTITY_RESOLUTION", "UNRESOLVED_IDENTITY")],
        )

    # --- 21: Plant isolation ----------------------------------------------------------

    def test_b21_two_plants_produce_two_isolated_cards(self) -> None:
        built = self.chain(
            "b21-two-plants",
            demands=((DEMAND, "130", D20),),
            extra_plant_families=((OTHER_PLANT, DEMAND, "120", "2026-10-10"),),
            moq_policies=(
                moq_policy_record(DEMAND, moq="100"),
                moq_policy_record(
                    DEMAND,
                    moq="100",
                    plant=OTHER_PLANT,
                    locator="SIMULATED-SRC-MOQ-P2",
                ),
            ),
            performances=(performance_record(delivery="97", quality="99", lead_time="5"),),
        )
        result = self.risk(built)
        self.assertEqual(len(result.cards), 2)
        first = result.card_for(PLANT, SUPPLIER, DEMAND)
        second = result.card_for(OTHER_PLANT, SUPPLIER, DEMAND)
        assert first is not None and second is not None
        self.assertEqual(first.recommendation_need_date, "2026-10-21")
        self.assertEqual(second.recommendation_need_date, "2026-10-10")
        self.assertEqual(first.days_until_need, 20)
        self.assertEqual(second.days_until_need, 9)
        self.assertNotEqual(first.evaluation_context, second.evaluation_context)
        # Both keep the business grain and each keeps its own level decision.
        for card in (first, second):
            with self.subTest(plant=card.plant_id):
                self.assertEqual(card.grain, (SUPPLIER, DEMAND))
                self.assertEqual(card.overall_supplier_risk, RISK_LOW)
        # Deterministic order: plant, then material, then supplier.
        self.assertEqual(
            [card.evaluation_context for card in result.cards],
            [(PLANT, DEMAND, SUPPLIER), (OTHER_PLANT, DEMAND, SUPPLIER)],
        )

    # --- 22: exact arithmetic ---------------------------------------------------------

    def test_b22_arithmetic_is_exact_and_float_free(self) -> None:
        # Exact decimal comparisons at the registered boundaries (no binary floating point).
        for delivery, expected in (("95.0000001", RISK_LOW), ("94.9999999", RISK_MEDIUM)):
            with self.subTest(delivery=delivery):
                card = self.card(
                    self.example_chain(
                        f"b22-{delivery}", delivery=delivery, quality="99", lead_time="5"
                    )
                )
                self.assertEqual(card.delivery_risk, expected)
        # Exact scale-insensitive equality: 90.00 is the same quantity as 90.
        card = self.card(
            self.example_chain("b22-scale", delivery="90.00", quality="98.0", lead_time="5")
        )
        self.assertEqual(card.delivery_risk, RISK_MEDIUM)
        self.assertEqual(card.quality_risk, RISK_LOW)
        # The payload states the exact decimal text of the days count (no float formatting).
        self.assertEqual(card.days_until_need_text, "20")

        source = Path(
            __import__("snapshot_loader.supplier_risk_calculation", fromlist=["x"]).__file__
        ).read_text(encoding="utf-8")
        tree = ast.parse(source)
        floats = [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, float)
        ]
        self.assertEqual(floats, [], "the rule must not contain float literals")
        for forbidden in ("float(", "round(", "quantize(", "clamp(", "Decimal("):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    # --- 23: truthful provenance ------------------------------------------------------

    def test_b23_references_are_truthful(self) -> None:
        built = self.chain("b23-references", performances=(performance_record(),))
        seam = self.supplier_input(built)
        context = seam.context_for(PLANT, SUPPLIER, DEMAND)
        assert context is not None
        card = compute_supplier_risk(seam).cards[0]
        self.assertIs(card.eligibility, context.eligibility)
        self.assertIs(card.performance, context.applicable_performance)
        self.assertEqual(
            card.relationship_reference, context.eligibility.relationship_reference
        )
        assert card.relationship_reference is not None
        self.assertIn("|", card.relationship_reference)
        reference = card.performance_evidence_reference
        assert reference is not None
        self.assertEqual(reference.logical_dataset_role, "Supplier Performance")
        self.assertIs(reference, context.applicable_performance.evidence_reference)
        payload = card.to_dict()
        self.assertEqual(
            payload["performance_evidence_reference"]["logical_dataset_role"],
            "Supplier Performance",
        )
        self.assertEqual(
            payload["relationship_reference"], card.relationship_reference
        )

    # --- 24: determinism --------------------------------------------------------------

    def test_b24_identical_inputs_produce_identical_payloads(self) -> None:
        first = self.chain("b24-first", performances=(performance_record(),))
        second = self.chain("b24-second", performances=(performance_record(),))
        first_result = compute_supplier_risk(self.supplier_input(first))
        second_result = compute_supplier_risk(self.supplier_input(second))
        self.assertEqual(first_result.to_dict(), second_result.to_dict())
        json.dumps(first_result.to_dict())
        self.assertEqual(
            [card.evaluation_context for card in first_result.cards],
            [(PLANT, DEMAND, SUPPLIER)],
        )
        self.assertEqual(first_result.notes, second_result.notes)

    def test_b25_surfaces_are_frozen_and_stable(self) -> None:
        built = self.chain("b25-frozen", performances=(performance_record(),))
        result = self.risk(built)
        card = result.cards[0]
        self.assertIsInstance(card, SupplierRiskEvidenceCard)
        self.assertIsInstance(result, SupplierRiskResult)
        self.assertTrue(dataclasses.is_dataclass(result))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            card.overall_supplier_risk = RISK_HIGH  # type: ignore[misc]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.cards = ()  # type: ignore[misc]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            card.rule_issues = ()  # type: ignore[misc]
        payload = card.to_dict()
        for key in (
            "supplier_id",
            "material_code",
            "plant_id",
            "Analysis Run",
            "AnalysisDate",
            "RecommendationNeedDate",
            "DaysUntilNeed",
            "StandardLeadTimeDays",
            "LeadTimeRisk",
            "PerformancePeriod",
            "PerformanceUpdatedAt",
            "DeliveryPerformance",
            "DeliveryRisk",
            "QualityPerformance",
            "QualityRisk",
            "OverallSupplierRisk",
            "status",
            "evidence_complete",
        ):
            with self.subTest(key=key):
                self.assertIn(key, payload)
        self.assertEqual(payload["stage"], SUPPLIER_RISK_STAGE)
        self.assertEqual(payload["Analysis Run"], result.analysis_run_id)
        self.assertEqual(payload["AnalysisDate"], "2026-10-01")
        self.assertEqual(payload["PerformancePeriod"], "2026-Q3")
        self.assertEqual(payload["PerformanceUpdatedAt"], "2026-09-30T00:00:00Z")

    # --- 26: scope guard --------------------------------------------------------------

    def test_b26_the_rule_adds_no_out_of_scope_capability(self) -> None:
        import snapshot_loader.supplier_risk_calculation as module

        identifiers = module_identifiers(module)
        for forbidden in (
            "ranking",
            "rank",
            "selection",
            "select_supplier",
            "winner",
            "best_supplier",
            "RecommendedPurchaseQty",
            "MOQAdjustmentQty",
            "ApplicableMOQ",
            "order_split",
            "ProcurementRequestDraft",
            "hitl",
            "llm",
            "float",
            # Input closure: the rule never names the construction, the accepted package or the
            # upstream rule results, so it cannot re-read them.
            "CanonicalConstructionReport",
            "AcceptedPackage",
            "compute_shortage",
            "ShortageCalculationResult",
            "construct_canonical_objects",
            "compute_procurement_recommendation",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, identifiers)
        # No filesystem / raw-evidence access anywhere in the rule.
        source = Path(module.__file__).read_text(encoding="utf-8")
        for forbidden in ("open(", "read_text(", "Path(", "os.path", "glob(", "read_bytes"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)
        # Only the registered risk vocabulary is named.
        self.assertEqual((RISK_LOW, RISK_MEDIUM, RISK_HIGH), ("LOW", "MEDIUM", "HIGH"))
        self.assertEqual(RISK_DATA_INCOMPLETE, "DATA_INCOMPLETE")
        self.assertNotIn(
            RISK_DATA_INCOMPLETE, {RISK_LOW, RISK_MEDIUM, RISK_HIGH}
        )


if __name__ == "__main__":  # pragma: no cover - direct invocation
    unittest.main()
