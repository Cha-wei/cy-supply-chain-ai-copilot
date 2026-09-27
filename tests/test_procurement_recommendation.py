"""``BR-PROCUREMENT-001`` Purchase Recommendation Quantity (Issue #160).

Covers the registered deterministic quantity rule: the trigger, the one-baseline-recommendation owner
grain, ``RecommendationNeedDate`` from the Phase B context, ``BasePurchaseNeed`` from the exact
shortage grain, ``RecommendedPurchaseQty = max(BasePurchaseNeed, ApplicableMOQ)``,
``MOQAdjustmentQty``, the exact numeric representation, the ``DATA_INCOMPLETE`` ／ valid-absence
boundaries, the ``F3-RB1`` binding, determinism and the out-of-scope guards.

The fixtures reuse the existing end-to-end chain builder (`tests.test_shortage_calculation`) and the
registered Phase B policy-input fixture (`tests.test_procurement_policy_input`), so every test runs the
whole registered chain instead of hand-built partial results.
"""

from __future__ import annotations

import ast
import dataclasses
import unittest
from fractions import Fraction
from pathlib import Path
from typing import Any

from snapshot_loader import (
    CLASSIFICATION_DATA_INCOMPLETE,
    AnalysisRunBindingError,
    PROCUREMENT_POLICY_INPUT_STAGE,
    compute_procurement_policy_input,
    compute_procurement_recommendation,
)
from snapshot_loader import constants as taxonomy
from tests.test_procurement_policy_input import (
    BASIS_MOQ_UNRESOLVED,
    ProcurementPolicyInputTestCase,
    moq_policy_record,
)
from tests.test_shortage_calculation import (
    D1,
    D2,
    DEMAND,
    OTHER,
    PLANT,
    Demand,
)

#: The observation/role the policy-input fixture registers its MOQ evidence under.
M7 = "M7"


def module_identifiers(module) -> set[str]:
    """Every code identifier of one module: a docstring may explain, code may not name."""

    source = Path(module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    identifiers: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            identifiers.add(node.id)
        elif isinstance(node, ast.Attribute):
            identifiers.add(node.attr)
        elif isinstance(node, ast.arg):
            identifiers.add(node.arg)
        elif isinstance(node, ast.keyword):
            identifiers.add(node.arg or "")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            identifiers.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    identifiers.add(target.id)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                identifiers.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                identifiers.add(alias.name)
    return identifiers


class ProcurementRecommendationTestCase(ProcurementPolicyInputTestCase):
    """One triggered family per fixture, plus the boundary families a test asks for."""

    def build_family(
        self,
        *,
        demands: tuple[tuple[Any, Any, Any], ...] = ((DEMAND, "130", D2),),
        inventory: dict[Any, Any] | None = None,
        safety_stock: dict[Any, Any] | None = None,
        loss_rate: Any = "0",
        targets: tuple[tuple[Any, Any, Any], ...] | None = None,
        moq_policies: tuple[dict[str, Any], ...] = (),
        include_valid_absence: bool = False,
        include_unresolved: bool = False,
        analysis_run_id: str = "RUN-1",
        package_id: str = "SIMULATED-PKG-0001",
        name: str,
    ):
        """Assemble one registered chain whose demands are ``(material, quantity, date)`` triples.

        Every demanded date registers its own ``APPROVED`` Target Applicability context unless
        ``targets`` states them explicitly, so the substitute side stays reliably "not applicable"
        and never makes a grain unresolved by accident.  ``moq_policies`` states the role-12
        ``Procurement policy input`` dataset exactly as the Phase B fixture does.
        """

        demand = [Demand(material, material, quantity, date) for material, quantity, date in demands]
        stock = {material: "100" for material, _quantity, _date in demands}
        policy = {material: "5" for material, _quantity, _date in demands}
        context_targets = (
            tuple((material, date, "APPROVED") for material, _quantity, date in demands)
            if targets is None
            else targets
        )
        target_list = list(context_targets)

        if include_valid_absence:
            demand.append(Demand(OTHER, OTHER, "10", D2))
            stock[OTHER] = "100"
            policy[OTHER] = "5"
            target_list.append((OTHER, D2, "APPROVED"))
        if include_unresolved:
            demand.append(Demand(M7, M7, "10", D1))
            demand.append(Demand(M7, M7, "10", D2))
            stock[M7] = "100"
            policy[M7] = "5"
            target_list.append((M7, D1, "APPROVED"))
            target_list.append((M7, D2, "UNRESOLVED"))

        return self.build(
            demand=tuple(demand),
            inventory={**stock, **(inventory or {})},
            safety_stock={**policy, **(safety_stock or {})},
            loss_rate=loss_rate,
            targets=tuple(target_list),
            moq_policies=moq_policies,
            analysis_run_id=analysis_run_id,
            package_id=package_id,
            name=name,
        )

    def policy(self, built):
        """The registered Phase B policy input of one fixture."""

        return compute_procurement_policy_input(
            built.construction, built.shortage, accepted=built.accepted
        )

    def recommend(self, built, policy=None):
        """The rule result of one fixture, consuming the registered upstream surfaces only."""

        return compute_procurement_recommendation(
            built.construction,
            built.shortage,
            self.policy(built) if policy is None else policy,
        )


class RecommendationTests(ProcurementRecommendationTestCase):
    # --- §2.5.16 deterministic examples A - H ---------------------------------------

    def test_a1_example_a_shortage_below_moq(self) -> None:
        built = self.build_family(
            demands=((DEMAND, "130", D2),),
            moq_policies=(moq_policy_record(DEMAND, moq="100"),),
            name="a1-below-moq",
        )
        result = self.recommend(built)
        item = result.for_family(PLANT, DEMAND)
        assert item is not None
        self.assertTrue(item.has_numeric_result)
        self.assertFalse(item.data_incomplete)
        self.assertEqual(item.recommendation_need_date, D2)
        self.assertEqual(item.shortage_qty, Fraction(30))
        self.assertEqual(item.base_purchase_need, Fraction(30))
        self.assertEqual(item.applicable_moq.text(), "100")
        self.assertEqual(item.recommended_purchase_qty, Fraction(100))
        self.assertEqual(item.moq_adjustment_qty, Fraction(70))
        self.assertEqual(item.shortage_classification, "SHORTAGE")
        self.assertEqual(item.root_condition, None)
        self.assertEqual(item.issues, ())
        self.assertEqual(result.recommended_purchase_qty_for(PLANT, DEMAND), Fraction(100))
        self.assertEqual(result.numeric_recommendations, (item,))
        # ``ShortageQty`` and ``BasePurchaseNeed`` stay separately distinguishable in the payload.
        payload = item.to_dict()
        self.assertEqual(payload["ShortageQty"], {"numerator": 30, "denominator": 1})
        self.assertEqual(payload["BasePurchaseNeed"], {"numerator": 30, "denominator": 1})
        self.assertEqual(payload["RecommendedPurchaseQty"], {"numerator": 100, "denominator": 1})
        self.assertEqual(payload["MOQAdjustmentQty"], {"numerator": 70, "denominator": 1})
        self.assertEqual(payload["ApplicableMOQ"], "100")
        self.assertIsNone(payload["outcome"])

    def test_a2_example_b_shortage_above_moq(self) -> None:
        built = self.build_family(
            demands=((DEMAND, "220", D2),),
            moq_policies=(moq_policy_record(DEMAND, moq="100"),),
            name="a2-above-moq",
        )
        item = self.recommend(built).for_family(PLANT, DEMAND)
        assert item is not None
        self.assertEqual(item.base_purchase_need, Fraction(120))
        self.assertEqual(item.recommended_purchase_qty, Fraction(120))
        self.assertEqual(item.moq_adjustment_qty, Fraction(0))
        self.assertGreaterEqual(item.moq_adjustment_qty, 0)

    def test_a3_example_c_explicit_no_moq_zero(self) -> None:
        built = self.build_family(
            demands=((DEMAND, "140", D2),),
            moq_policies=(moq_policy_record(DEMAND, moq="0"),),
            name="a3-explicit-zero",
        )
        result = self.recommend(built)
        item = result.for_family(PLANT, DEMAND)
        assert item is not None
        self.assertTrue(item.has_numeric_result)
        self.assertIsNotNone(item.applicable_moq)
        self.assertEqual(item.applicable_moq.text(), "0")
        self.assertEqual(item.base_purchase_need, Fraction(40))
        self.assertEqual(item.recommended_purchase_qty, Fraction(40))
        self.assertEqual(item.moq_adjustment_qty, Fraction(0))
        self.assertEqual(item.to_dict()["ApplicableMOQ"], "0")
        # The valid explicit zero is never an issue and is distinct from an absent MOQ (§4.4.88).
        self.assertEqual(item.issues, ())
        self.assertFalse(result.is_valid_absence(PLANT, DEMAND))

    def test_a4_example_d_missing_moq_is_data_incomplete(self) -> None:
        built = self.build_family(
            demands=((DEMAND, "140", D2),),
            moq_policies=(moq_policy_record(DEMAND, moq=None),),
            name="a4-missing-moq",
        )
        result = self.recommend(built)
        item = result.for_family(PLANT, DEMAND)
        assert item is not None
        self.assertTrue(item.data_incomplete)
        self.assertFalse(item.has_numeric_result)
        self.assertIsNone(item.recommended_purchase_qty)
        self.assertIsNone(item.moq_adjustment_qty)
        self.assertIsNone(item.applicable_moq)
        self.assertIsNone(result.recommended_purchase_qty_for(PLANT, DEMAND))
        self.assertEqual(item.to_dict()["RecommendedPurchaseQty"], None)
        # The precise upstream §4.4.67 root keeps its own registered taxonomy; this rule inherits it
        # verbatim instead of re-deriving it, and never defaults the missing MOQ to 0.
        self.assertEqual(
            [(issue.category, issue.reason) for issue in item.issues],
            [("FIELD_VALUE", "MISSING")],
        )
        self.assertEqual(item.policy_root_condition, "MOQ_VALUE_MISSING")

    def test_a5_example_e_buffer_breach_is_no_recommendation(self) -> None:
        built = self.build_family(
            demands=((DEMAND, "97", D2),),
            moq_policies=(moq_policy_record(DEMAND, moq="100"),),
            name="a5-buffer-breach",
        )
        result = self.recommend(built)
        # 100 - 97 = 3: below the SafetyStock of 5 but not short, so no recommendation is produced at
        # all -- valid absence, never DATA_INCOMPLETE and never a numeric recommendation.
        self.assertTrue(result.is_valid_absence(PLANT, DEMAND))
        self.assertIsNone(result.for_family(PLANT, DEMAND))
        self.assertIsNone(result.recommended_purchase_qty_for(PLANT, DEMAND))
        self.assertEqual(result.recommendations, ())
        self.assertEqual(result.rule_issues, ())
        self.assertEqual(result.to_dict()["valid_absence_grains"], [
            {"plant_id": PLANT, "material_code": DEMAND}
        ])

    def test_a6_example_f_normal_is_no_recommendation(self) -> None:
        built = self.build_family(
            demands=((DEMAND, "90", D2),),
            moq_policies=(moq_policy_record(DEMAND, moq="100"),),
            name="a6-normal",
        )
        result = self.recommend(built)
        self.assertTrue(result.is_valid_absence(PLANT, DEMAND))
        self.assertIsNone(result.recommended_purchase_qty_for(PLANT, DEMAND))
        self.assertEqual(result.issues, ())

    def test_a7_example_g_data_incomplete_family(self) -> None:
        built = self.build_family(
            demands=((DEMAND, "130", D2),),
            moq_policies=(
                moq_policy_record(DEMAND, moq="100"),
                moq_policy_record(M7, moq="100", locator="SIMULATED-SRC-MOQ-M7"),
            ),
            include_unresolved=True,
            name="a7-data-incomplete",
        )
        result = self.recommend(built)
        item = result.for_family(PLANT, M7)
        assert item is not None
        self.assertTrue(item.data_incomplete)
        self.assertIsNone(item.recommendation_need_date)
        self.assertIsNone(item.recommended_purchase_qty)
        self.assertEqual(item.root_condition, "MOQ_POLICY_INPUT_UNRESOLVED")
        self.assertEqual(
            item.policy_root_condition, "RECOMMENDATION_NEED_DATE_UNRESOLVED"
        )
        self.assertEqual(
            [(issue.category, issue.reason) for issue in item.issues],
            [("SEMANTIC_RESOLUTION", "SEMANTIC_UNRESOLVED")],
        )
        # The reliable family of the same run is unaffected (failure isolation per family).
        self.assertTrue(result.for_family(PLANT, DEMAND).has_numeric_result)

    def test_a8_example_h_first_shortage_only(self) -> None:
        # D1 already shorts by 30 while D2 shorts far more: the registered rule uses the first
        # reliable shortage date only and never generates a second recommendation for D2.
        built = self.build_family(
            demands=((DEMAND, "130", D1), (DEMAND, "100", D2)),
            moq_policies=(moq_policy_record(DEMAND, moq="50"),),
            name="a8-first-shortage-only",
        )
        result = self.recommend(built)
        item = result.for_family(PLANT, DEMAND)
        assert item is not None
        self.assertEqual(item.recommendation_need_date, D1)
        self.assertEqual(item.base_purchase_need, Fraction(30))
        self.assertEqual(item.recommended_purchase_qty, Fraction(50))
        self.assertEqual(item.moq_adjustment_qty, Fraction(20))
        # Exactly one recommendation for the family, and none of its grains carries the later date.
        self.assertEqual(len(result.recommendations), 1)
        self.assertIsNone(result.for_owner(PLANT, DEMAND, D2))
        self.assertEqual(result.for_owner(PLANT, DEMAND, D1), item)
        self.assertIsNotNone(built.shortage.for_grain(PLANT, DEMAND, D2))

    def test_a9_an_exact_non_terminating_rational_is_kept(self) -> None:
        # 200 / (1 - 0.05) = 4000/19, so 100 - 4000/19 = -2100/19 is the exact ShortageQty.
        built = self.build_family(
            demands=((DEMAND, "200", D2),),
            loss_rate="0.05",
            moq_policies=(moq_policy_record(DEMAND, moq="200"),),
            name="a9-exact-rational",
        )
        item = self.recommend(built).for_family(PLANT, DEMAND)
        assert item is not None
        self.assertTrue(item.has_numeric_result)
        self.assertEqual(item.shortage_qty, Fraction(2100, 19))
        self.assertEqual(item.base_purchase_need, Fraction(2100, 19))
        self.assertEqual(item.recommended_purchase_qty, Fraction(200))
        self.assertEqual(item.moq_adjustment_qty, Fraction(1700, 19))
        payload = item.to_dict()
        self.assertEqual(payload["ShortageQty"], {"numerator": 2100, "denominator": 19})
        self.assertEqual(payload["RecommendedPurchaseQty"], {"numerator": 200, "denominator": 1})
        self.assertEqual(payload["MOQAdjustmentQty"], {"numerator": 1700, "denominator": 19})
        # A non-terminating value stays a reliable quantity and is never downgraded or rounded.
        lower = self.build_family(
            demands=((DEMAND, "200", D2),),
            loss_rate="0.05",
            moq_policies=(moq_policy_record(DEMAND, moq="50"),),
            name="a9-exact-rational-below",
        )
        below = self.recommend(lower).for_family(PLANT, DEMAND)
        assert below is not None
        self.assertEqual(below.recommended_purchase_qty, Fraction(2100, 19))
        self.assertEqual(below.moq_adjustment_qty, Fraction(0))
        self.assertEqual(
            below.to_dict()["RecommendedPurchaseQty"],
            {"numerator": 2100, "denominator": 19},
        )

    # --- boundaries ------------------------------------------------------------------

    def test_a10_family_isolation(self) -> None:
        built = self.build_family(
            demands=((DEMAND, "130", D2), (OTHER, "120", D2)),
            targets=((DEMAND, D2, "APPROVED"), (OTHER, D2, "APPROVED")),
            moq_policies=(
                moq_policy_record(DEMAND, moq="100"),
                moq_policy_record(OTHER, moq="5"),
            ),
            name="a10-family-isolation",
        )
        result = self.recommend(built)
        demand = result.for_family(PLANT, DEMAND)
        other = result.for_family(PLANT, OTHER)
        assert demand is not None and other is not None
        # Each family keeps its own ShortageQty and its own policy input; nothing is aggregated.
        self.assertEqual(demand.base_purchase_need, Fraction(30))
        self.assertEqual(demand.recommended_purchase_qty, Fraction(100))
        self.assertEqual(demand.moq_adjustment_qty, Fraction(70))
        self.assertEqual(other.base_purchase_need, Fraction(20))
        self.assertEqual(other.recommended_purchase_qty, Fraction(20))
        self.assertEqual(other.moq_adjustment_qty, Fraction(0))
        self.assertNotEqual(demand.recommended_purchase_qty, other.recommended_purchase_qty)

    def test_a11_binding_is_verified_before_any_consumption(self) -> None:
        run_a = self.build_family(
            demands=((DEMAND, "130", D2),),
            moq_policies=(moq_policy_record(DEMAND, moq="100"),),
            name="a11-run-a",
        )
        run_b = self.build_family(
            demands=((DEMAND, "130", D2),),
            moq_policies=(moq_policy_record(DEMAND, moq="100"),),
            analysis_run_id="RUN-B",
            package_id="SIMULATED-PKG-0002",
            name="a11-run-b",
        )
        policy_b = self.policy(run_b)
        with self.assertRaises(AnalysisRunBindingError) as caught:
            compute_procurement_recommendation(
                run_a.construction, run_b.shortage, policy_b
            )
        reasons = {issue.reason for issue in caught.exception.issues}
        self.assertEqual(reasons, {"PROVENANCE_MISMATCH"})
        locations = " ".join(issue.location for issue in caught.exception.issues)
        self.assertIn("BR-SHORTAGE-001", locations)
        self.assertIn(PROCUREMENT_POLICY_INPUT_STAGE, locations)
        for issue in caught.exception.issues:
            self.assertEqual(issue.category, "PROVENANCE")
        # An absent linkage is a distinct outcome: PROVENANCE_UNRESOLVED, never a mismatch and never
        # a business DATA_INCOMPLETE.
        unbound_shortage = dataclasses.replace(run_a.shortage, analysis_run=None)
        with self.assertRaises(AnalysisRunBindingError) as caught:
            compute_procurement_recommendation(
                run_a.construction, unbound_shortage, self.policy(run_a)
            )
        self.assertEqual(
            {issue.reason for issue in caught.exception.issues}, {"PROVENANCE_UNRESOLVED"}
        )
        unbound_policy = dataclasses.replace(self.policy(run_a), analysis_run=None)
        with self.assertRaises(AnalysisRunBindingError) as caught:
            compute_procurement_recommendation(
                run_a.construction, run_a.shortage, unbound_policy
            )
        self.assertEqual(
            {issue.reason for issue in caught.exception.issues}, {"PROVENANCE_UNRESOLVED"}
        )

    def test_a12_valid_absence_is_not_data_incomplete_and_has_no_issue(self) -> None:
        built = self.build_family(
            demands=((DEMAND, "130", D2),),
            moq_policies=(moq_policy_record(DEMAND, moq="100"),),
            include_valid_absence=True,
            name="a12-valid-absence",
        )
        result = self.recommend(built)
        self.assertTrue(result.for_family(PLANT, DEMAND).has_numeric_result)
        self.assertTrue(result.is_valid_absence(PLANT, OTHER))
        self.assertIsNone(result.recommended_purchase_qty_for(PLANT, OTHER))
        self.assertEqual(result.valid_absence_grains, ((PLANT, OTHER),))
        self.assertEqual(result.rule_issues, ())
        self.assertEqual(
            [item.material_code for item in result.recommendations], [DEMAND]
        )

    def test_a13_determinism_read_only_and_bound(self) -> None:
        first = self.build_family(
            demands=((DEMAND, "130", D2), (OTHER, "120", D2)),
            targets=((DEMAND, D2, "APPROVED"), (OTHER, D2, "APPROVED")),
            moq_policies=(
                moq_policy_record(DEMAND, moq="100"),
                moq_policy_record(OTHER, moq="5"),
            ),
            name="a13-first",
        )
        second = self.build_family(
            demands=((DEMAND, "130", D2), (OTHER, "120", D2)),
            targets=((DEMAND, D2, "APPROVED"), (OTHER, D2, "APPROVED")),
            moq_policies=(
                moq_policy_record(DEMAND, moq="100"),
                moq_policy_record(OTHER, moq="5"),
            ),
            name="a13-second",
        )
        first_result = self.recommend(first)
        second_result = self.recommend(second)
        self.assertEqual(first_result.to_dict(), second_result.to_dict())
        # Deterministic canonical ordering: plant_id -> material_code, never discovery order.
        self.assertEqual(
            [item.material_code for item in first_result.recommendations],
            [DEMAND, OTHER],
        )
        self.assertIs(first_result.analysis_run, first.construction.analysis_run)
        self.assertEqual(
            first_result.to_dict()["analysis_run"]["analysis_run_id"], "RUN-1"
        )
        self.assertEqual(
            first_result.to_dict()["analysis_run"]["snapshot_package_identity"],
            first.construction.analysis_run.snapshot_package_identity,
        )
        self.assertTrue(dataclasses.is_dataclass(first_result))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            first_result.recommendations = ()  # type: ignore[misc]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            first_result.recommendations[0].recommended_purchase_qty = None  # type: ignore[misc]

    def test_a14_no_supplier_selection_no_precedence(self) -> None:
        # Two applicable policy records: the Phase B seam already refuses to pick one, and this rule
        # consumes that unresolved answer instead of re-deciding it by any precedence.
        built = self.build_family(
            demands=((DEMAND, "130", D2),),
            moq_policies=(
                moq_policy_record(DEMAND, moq="100"),
                moq_policy_record(DEMAND, moq="50", locator="SIMULATED-SRC-MOQ-ALT"),
            ),
            name="a14-no-precedence",
        )
        result = self.recommend(built)
        item = result.for_family(PLANT, DEMAND)
        assert item is not None
        self.assertTrue(item.data_incomplete)
        self.assertIsNone(item.recommended_purchase_qty)
        self.assertIsNone(item.applicable_moq)
        self.assertEqual(
            [(issue.category, issue.reason) for issue in item.issues],
            [("SEMANTIC_RESOLUTION", "SEMANTIC_UNRESOLVED")],
        )
        # The unresolved registered basis is not a value either, and never becomes a numeric result.
        unresolved_basis = self.build_family(
            demands=((DEMAND, "130", D2),),
            moq_policies=(
                moq_policy_record(DEMAND, moq="100", basis=BASIS_MOQ_UNRESOLVED),
            ),
            name="a14-unresolved-basis",
        )
        other = self.recommend(unresolved_basis).for_family(PLANT, DEMAND)
        assert other is not None
        self.assertTrue(other.data_incomplete)
        self.assertIsNone(other.recommended_purchase_qty)
        self.assertEqual(other.policy_root_condition, "MOQ_APPLICABILITY_UNRESOLVED")
        self.assertEqual(
            [(issue.category, issue.reason) for issue in other.issues],
            [("SEMANTIC_RESOLUTION", "SEMANTIC_UNRESOLVED")],
        )

    def test_a15_no_rounding_or_quantization_anywhere(self) -> None:
        import snapshot_loader.procurement_recommendation as module

        identifiers = module_identifiers(module)
        for forbidden in (
            "round",
            "ceil",
            "floor",
            "quantize",
            "Decimal",
            "ROUND_HALF_UP",
            "to_integral_value",
            "order_multiple",
            "pack_size",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, identifiers)
        # The registered formula does use ``max``; it is never a candidate selection (see a14).
        self.assertIn("max", identifiers)
        self.assertNotIn("min", identifiers)

    def test_a16_no_second_recommendation_and_no_time_phased_loop(self) -> None:
        built = self.build_family(
            demands=((DEMAND, "130", D1), (DEMAND, "100", D2)),
            moq_policies=(moq_policy_record(DEMAND, moq="50"),),
            name="a16-no-second-recommendation",
        )
        result = self.recommend(built)
        self.assertEqual(len(result.recommendations), 1)
        self.assertEqual(
            {item.recommendation_need_date for item in result.recommendations}, {D1}
        )
        # The later shortage grain exists upstream and is deliberately not turned into a second
        # recommendation: only the first reliable shortage date is used (§2.5.3 / §2.5.16 Example H).
        later = built.shortage.for_grain(PLANT, DEMAND, D2)
        assert later is not None
        self.assertEqual(later.classification, "SHORTAGE")
        self.assertEqual(later.shortage_qty, Fraction(130))

    def test_a17_no_raw_evidence_is_read(self) -> None:
        import snapshot_loader.procurement_recommendation as module

        identifiers = module_identifiers(module)
        for forbidden in (
            "AcceptedPackage",
            "TrustedInputBoundary",
            "load_package",
            "construct_canonical_objects",
            "parse_strict_json",
            "read_provenance_associations",
            "records_for",
            "accepted_package",
            "datasets",
            "EvidenceReference",
            "ContentView",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, identifiers)
        # The function itself takes no accepted package / artifact / evidence parameter.
        import inspect

        parameters = list(
            inspect.signature(compute_procurement_recommendation).parameters
        )
        self.assertEqual(parameters, ["construction", "shortage", "policy_input"])
        self.assertNotIn("accepted", parameters)

    def test_a18_no_section_2_7_or_p0_3_implementation(self) -> None:
        import snapshot_loader.procurement_recommendation as module

        identifiers = module_identifiers(module)
        for forbidden in (
            "LeadTimeRisk",
            "DaysUntilNeed",
            "DeliveryRisk",
            "QualityRisk",
            "OverallSupplierRisk",
            "standard_lead_time_days",
            "lead_time",
            "supplier_id",
            "supplier_selection",
            "sourcing_status",
            "ProcurementRequestDraft",
            "procurement_request_draft",
            "ApprovedPurchaseQty",
            "PurchaseOrderQty",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, identifiers)

    def test_a19_trigger_strictness_an_available_moq_never_triggers_alone(self) -> None:
        for label, quantity, expected_classification in (
            ("normal", "90", "NORMAL"),
            ("buffer-breach", "97", "BUFFER_BREACH"),
        ):
            with self.subTest(label=label):
                built = self.build_family(
                    demands=((DEMAND, quantity, D2),),
                    moq_policies=(moq_policy_record(DEMAND, moq="100"),),
                    name=f"a19-{label}",
                )
                grain = built.shortage.for_grain(PLANT, DEMAND, D2)
                assert grain is not None
                self.assertEqual(grain.classification, expected_classification)
                self.assertEqual(grain.shortage_qty, Fraction(0))
                result = self.recommend(built)
                # A resolvable ApplicableMOQ exists for the family, yet no recommendation is produced:
                # the trigger requires a reliable SHORTAGE with a positive ShortageQty (§2.5.2).
                self.assertEqual(result.recommendations, ())
                self.assertTrue(result.is_valid_absence(PLANT, DEMAND))
                self.assertIsNone(result.recommended_purchase_qty_for(PLANT, DEMAND))
                self.assertEqual(result.issues, ())

    def test_a20_output_surface_distinguishes_the_registered_fields(self) -> None:
        built = self.build_family(
            demands=((DEMAND, "130", D2),),
            moq_policies=(moq_policy_record(DEMAND, moq="100"),),
            name="a20-output-surface",
        )
        result = self.recommend(built)
        item = result.for_family(PLANT, DEMAND)
        assert item is not None
        payload = item.to_dict()
        for key in (
            "plant_id",
            "material_code",
            "RecommendationNeedDate",
            "Classification",
            "ShortageQty",
            "BasePurchaseNeed",
            "ApplicableMOQ",
            "MOQAdjustmentQty",
            "RecommendedPurchaseQty",
            "outcome",
            "root_condition",
            "shortage_reference",
            "policy_input_reference",
            "inherited_issues",
            "rule_issues",
        ):
            with self.subTest(key=key):
                self.assertIn(key, payload)
        # Only the minimum upstream references are kept: the producing rule/seam and the grain.  The
        # upstream results keep their own evidence ／ record references (決定 7 ／ 決定 11).
        self.assertEqual(set(payload["shortage_reference"]), {"rule", "grain"})
        self.assertEqual(set(payload["policy_input_reference"]), {"rule", "grain"})
        self.assertEqual(payload["shortage_reference"]["rule"], "BR-SHORTAGE-001")
        self.assertEqual(payload["policy_input_reference"]["rule"], PROCUREMENT_POLICY_INPUT_STAGE)
        self.assertEqual(
            payload["shortage_reference"]["grain"], [PLANT, DEMAND, D2]
        )
        self.assertEqual(
            payload["policy_input_reference"]["grain"], [PLANT, DEMAND, D2]
        )
        self.assertNotIn("evidence_reference", payload)
        self.assertNotIn("record_reference", payload)
        self.assertEqual(
            set(result.to_dict()),
            {
                "rule",
                "analysis_run",
                "recommendations",
                "valid_absence_grains",
                "rule_issues",
            },
        )
        self.assertEqual(result.to_dict()["rule"], "BR-PROCUREMENT-001")

    def test_a21_an_inconsistent_upstream_result_fails_closed(self) -> None:
        # Two individually valid results that disagree on the same family grain: the policy context
        # states D1 while the consumed shortage result answers D2.  The registered consistency
        # invariant is violated, so nothing is recommended and no date is chosen by precedence.
        built = self.build_family(
            demands=((DEMAND, "130", D1), (DEMAND, "100", D2)),
            moq_policies=(moq_policy_record(DEMAND, moq="50"),),
            name="a21-inconsistent-upstream",
        )
        policy = self.policy(built)
        remaining = tuple(
            grain for grain in built.shortage.grains if grain.required_date != D1
        )
        inconsistent = dataclasses.replace(built.shortage, grains=remaining)
        self.assertEqual(
            inconsistent.first_shortage_date_for(PLANT, DEMAND), D2
        )
        result = compute_procurement_recommendation(
            built.construction, inconsistent, policy
        )
        item = result.for_family(PLANT, DEMAND)
        assert item is not None
        self.assertTrue(item.data_incomplete)
        self.assertIsNone(item.recommended_purchase_qty)
        self.assertEqual(item.root_condition, "SHORTAGE_INPUT_INCONSISTENT")
        self.assertEqual(
            [(issue.category, issue.reason) for issue in item.rule_issues],
            [("CONSISTENCY", "CONSISTENCY_CONFLICT")],
        )

    def test_a22_a_fail_safe_need_date_linkage_fails_closed(self) -> None:
        # The consumed shortage result cannot state a reliable first shortage date for the family
        # (an earlier unresolved grain blocks it), so the required RecommendationNeedDate linkage is
        # unresolved and the context stays DATA_INCOMPLETE -- never a guessed date or quantity.
        built = self.build_family(
            demands=((DEMAND, "130", D1), (DEMAND, "100", D2)),
            moq_policies=(moq_policy_record(DEMAND, moq="50"),),
            name="a22-need-date-linkage",
        )
        policy = self.policy(built)
        demoted = tuple(
            dataclasses.replace(
                grain,
                classification=CLASSIFICATION_DATA_INCOMPLETE,
                shortage_qty=None,
                projected_available=None,
            )
            if grain.required_date == D1
            else grain
            for grain in built.shortage.grains
        )
        unresolved = dataclasses.replace(built.shortage, grains=demoted)
        self.assertEqual(
            unresolved.first_shortage_date_for(PLANT, DEMAND), "DATA_INCOMPLETE"
        )
        result = compute_procurement_recommendation(
            built.construction, unresolved, policy
        )
        item = result.for_family(PLANT, DEMAND)
        assert item is not None
        self.assertTrue(item.data_incomplete)
        self.assertIsNone(item.recommended_purchase_qty)
        self.assertEqual(item.root_condition, "SHORTAGE_INPUT_UNRESOLVED")
        self.assertEqual(
            [(issue.category, issue.reason) for issue in item.rule_issues],
            [("SEMANTIC_RESOLUTION", "SEMANTIC_UNRESOLVED")],
        )

    def test_a23_the_rule_adds_no_new_taxonomy(self) -> None:
        import snapshot_loader.procurement_recommendation as module

        registered_categories = {
            value
            for name, value in vars(taxonomy).items()
            if name.startswith("CATEGORY_") and isinstance(value, str)
        }
        registered_reasons = {
            value
            for name, value in vars(taxonomy).items()
            if name.startswith("REASON_") and isinstance(value, str)
        }
        # ``CONSISTENCY`` / ``CONSISTENCY_CONFLICT`` is the existing registered pair the other
        # deterministic rules already use verbatim (§4.4.80 #7 / §4.4.81 #10).
        registered_categories.add("CONSISTENCY")
        registered_reasons.add("CONSISTENCY_CONFLICT")
        self.assertIn(module._CATEGORY_CONSISTENCY, registered_categories)
        self.assertIn(module._REASON_CONSISTENCY_CONFLICT, registered_reasons)
        # The rule's own outcome vocabulary is the existing DATA_INCOMPLETE outcome plus runtime trace
        # labels: no new business enum ／ status ／ classification is introduced.
        self.assertEqual(module.PROCUREMENT_RECOMMENDATION_UNRESOLVED, "DATA_INCOMPLETE")
        self.assertEqual(module.PROCUREMENT_RECOMMENDATION_RULE_ID, "BR-PROCUREMENT-001")
        self.assertEqual(
            {
                module.ROOT_MOQ_INPUT_UNRESOLVED,
                module.ROOT_SHORTAGE_INPUT_INCONSISTENT,
                module.ROOT_SHORTAGE_INPUT_UNRESOLVED,
            },
            {
                "MOQ_POLICY_INPUT_UNRESOLVED",
                "SHORTAGE_INPUT_INCONSISTENT",
                "SHORTAGE_INPUT_UNRESOLVED",
            },
        )
        for forbidden in (
            "NOT_APPLICABLE",
            "NO_RECOMMENDATION",
            "N/A",
            "NO_SHORTAGE",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, module_identifiers(module))


if __name__ == "__main__":  # pragma: no cover - direct invocation
    unittest.main()
