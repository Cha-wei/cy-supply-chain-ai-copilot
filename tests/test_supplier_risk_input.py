"""Supplier Risk runtime input seam (``A′``, Human Decision, Issue #162).

Covers the registered seam that closes the two `BR-SUPPLIER-RISK-001` implementation-gate blockers:
the deterministic Supplier-Material **eligibility** resolution (``eligible`` ／ ``ineligible`` ／
``unresolved`` from approved mapping evidence only) and the **composition** between the plant-scoped
Procurement Recommendation Context and the supplier-material evaluation context.

The fixtures reuse the existing end-to-end chain builder (`tests.test_shortage_calculation`, extended
with the supplier-side roles 9 ／ 10 ／ 11), so every test runs the whole registered chain.
"""

from __future__ import annotations

import ast
import dataclasses
import unittest
from pathlib import Path
from typing import Any

from snapshot_loader import (
    ELIGIBILITY_ELIGIBLE,
    ELIGIBILITY_INELIGIBLE,
    AnalysisRunBindingError,
    SupplierRiskInputResult,
    compute_procurement_policy_input,
    compute_procurement_recommendation,
    compute_supplier_risk_input,
)
from tests.test_procurement_policy_input import moq_policy_record
from tests.test_procurement_recommendation import ProcurementRecommendationTestCase
from tests.test_shortage_calculation import (
    D1,
    D2,
    DEMAND,
    OTHER,
    PLANT,
    Demand,
    with_provenance,
)

#: The approved **SIMULATED** eligibility mapping basis literals of the registered registry.
ELIGIBLE_BASIS = "SIMULATED-SOURCING-ELIGIBLE"
INELIGIBLE_BASIS = "SIMULATED-SOURCING-INELIGIBLE"
#: A basis literal that is **not** approved by the registry.
UNREGISTERED_BASIS = "SIMULATED-SOURCING-UNREGISTERED"

#: The first-tranche supplier and material of the fixtures.
SUPPLIER = "SUP-A"
SUPPLIER_B = "SUP-B"
OTHER_PLANT = "P2"


def relationship_record(
    supplier: Any = SUPPLIER,
    material: Any = DEMAND,
    *,
    status: Any = "SOURCE-LOCAL-CODE",
    basis: str | None = ELIGIBLE_BASIS,
    extra_bases: tuple[str, ...] = (),
    drop_status: bool = False,
) -> dict[str, Any]:
    """One accepted ``Supplier-Material Relationship`` record.

    ``basis`` is the ``sourcing_status`` association's registered ``mapping_basis`` (``None`` registers
    no association at all); ``extra_bases`` adds further registrations on the same observation, so a
    test can state an ambiguous registration.  ``status`` is the source-specific value, which the seam
    never interprets.
    """

    record: dict[str, Any] = {"supplier_id": supplier, "material_code": material}
    if not drop_status:
        record["sourcing_status"] = status
    associations: list[tuple[str, list[str], str | None]] = []
    if basis is not None:
        associations.append(
            (
                "sourcing_status",
                [f"SIMULATED-SRC-SOURCING-{supplier}-{material}"],
                basis,
            )
        )
    for index, extra in enumerate(extra_bases):
        associations.append(
            ("sourcing_status", [f"SIMULATED-SRC-SOURCING-EXTRA-{index}"], extra)
        )
    if not associations:
        return record
    return with_provenance(record, associations)


def performance_record(
    supplier: Any = SUPPLIER,
    material: Any = DEMAND,
    *,
    period: Any = "2026-Q3",
    updated: Any = "2026-09-30T00:00:00Z",
    delivery: Any = "97",
    quality: Any = "99",
    lead_time: Any = "10",
    drop_period: bool = False,
) -> dict[str, Any]:
    """One accepted ``Supplier Performance`` record (no risk semantics are attached here)."""

    record: dict[str, Any] = {
        "supplier_id": supplier,
        "material_code": material,
        "PerformanceUpdatedAt": updated,
        "DeliveryPerformance": delivery,
        "QualityPerformance": quality,
        "standard_lead_time_days": lead_time,
    }
    if not drop_period:
        record["PerformancePeriod"] = period
    return with_provenance(
        record,
        [("PerformancePeriod", [f"SIMULATED-SRC-PERF-{supplier}-{material}"], None)],
    )


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


class SupplierRiskInputTestCase(ProcurementRecommendationTestCase):
    """One shorted family plus the supplier-side evidence each test asks for."""

    def build_chain(
        self,
        *,
        demands: tuple[tuple[Any, Any, Any], ...] = ((DEMAND, "130", D2),),
        targets: tuple[tuple[Any, Any, Any], ...] | None = None,
        moq_policies: tuple[dict[str, Any], ...] = (
            moq_policy_record(DEMAND, moq="100"),
        ),
        supplier_identities: tuple[dict[str, Any], ...] = (),
        supplier_relationships: tuple[dict[str, Any], ...] = (),
        supplier_performances: tuple[dict[str, Any], ...] = (),
        extra_plant_families: tuple[tuple[Any, Any, Any, Any], ...] = (),
        analysis_run_id: str = "RUN-1",
        package_id: str = "SIMULATED-PKG-0001",
        name: str,
    ):
        """Assemble one registered chain with optional supplier-side roles (9 ／ 10 ／ 11).

        ``extra_plant_families`` states additional Plant-scoped demand families of the same materials
        inside the *same* analysis run (``(plant_id, material_code, quantity, required_date)``), so a
        Plant-isolation test consumes genuinely formed upstream results instead of a fabricated one.
        """

        demand = [
            Demand(material, material, quantity, date)
            for material, quantity, date in demands
        ]
        stock = {material: "100" for material, _quantity, _date in demands}
        safety = {material: "5" for material, _quantity, _date in demands}
        context_targets = (
            tuple((material, date, "APPROVED") for material, _quantity, date in demands)
            if targets is None
            else targets
        )
        return self.build(
            demand=tuple(demand),
            inventory=stock,
            safety_stock=safety,
            targets=tuple(context_targets),
            moq_policies=moq_policies,
            supplier_identities=supplier_identities,
            supplier_relationships=supplier_relationships,
            supplier_performances=supplier_performances,
            extra_plant_families=extra_plant_families,
            analysis_run_id=analysis_run_id,
            package_id=package_id,
            name=name,
        )

    def recommendations(self, built):
        """The registered procurement recommendation result of one fixture."""

        policy = compute_procurement_policy_input(
            built.construction, built.shortage, accepted=built.accepted
        )
        return compute_procurement_recommendation(
            built.construction, built.shortage, policy
        )

    def supplier_input(self, built, recommendations=None, accepted=None):
        """The seam result of one fixture, consuming the registered upstream surfaces only."""

        return compute_supplier_risk_input(
            built.construction,
            self.recommendations(built) if recommendations is None else recommendations,
            accepted=built.accepted if accepted is None else accepted,
        )

    def eligible_chain(self, name: str):
        """One eligible relationship plus its performance evidence, ready for composition tests."""

        return self.build_chain(
            supplier_identities=({"supplier_id": SUPPLIER},),
            supplier_relationships=(relationship_record(),),
            supplier_performances=(performance_record(),),
            name=name,
        )


class EligibilityResolutionTests(SupplierRiskInputTestCase):
    # --- A′ §K 1-8: the eligibility resolution itself --------------------------------

    def test_a1_exact_approved_eligibility_basis_resolves_eligible(self) -> None:
        built = self.eligible_chain("a1-eligible")
        result = self.supplier_input(built)
        relationship = result.eligibility_for(SUPPLIER, DEMAND)
        assert relationship is not None
        self.assertEqual(relationship.outcome, ELIGIBILITY_ELIGIBLE)
        self.assertTrue(relationship.eligible)
        self.assertFalse(relationship.unresolved)
        self.assertFalse(relationship.ineligible)
        self.assertEqual(relationship.grain, (SUPPLIER, DEMAND))
        self.assertEqual(relationship.mapping_basis, ELIGIBLE_BASIS)
        self.assertEqual(relationship.sourcing_status, "SOURCE-LOCAL-CODE")
        self.assertEqual(relationship.root_condition, None)
        self.assertEqual(relationship.issues, ())
        self.assertEqual(len(result.relationships), 1)

    def test_a2_exact_approved_ineligible_basis_resolves_ineligible(self) -> None:
        built = self.chain_with_relationships(
            (relationship_record(basis=INELIGIBLE_BASIS),), "a2-ineligible"
        )
        result = self.supplier_input(built)
        relationship = result.eligibility_for(SUPPLIER, DEMAND)
        assert relationship is not None
        self.assertEqual(relationship.outcome, ELIGIBILITY_INELIGIBLE)
        self.assertTrue(relationship.ineligible)
        # Valid but ineligible: no Validation Issue, no DATA_INCOMPLETE, excluded from the candidates.
        self.assertEqual(relationship.issues, ())
        self.assertEqual(result.issues, ())
        self.assertEqual(result.evaluation_contexts, ())
        self.assertEqual(result.eligible_relationships, ())
        self.assertEqual(result.ineligible_relationships, (relationship,))

    def test_a3_unknown_or_unregistered_basis_is_unresolved(self) -> None:
        built = self.chain_with_relationships(
            (relationship_record(basis=UNREGISTERED_BASIS),), "a3-unregistered"
        )
        relationship = self.supplier_input(built).eligibility_for(SUPPLIER, DEMAND)
        assert relationship is not None
        self.assertTrue(relationship.unresolved)
        self.assertIsNone(relationship.mapping_basis)
        self.assertEqual(relationship.root_condition, "SOURCING_STATUS_MAPPING_AMBIGUOUS")
        self.assertEqual(
            [(issue.category, issue.reason) for issue in relationship.rule_issues],
            [("SEMANTIC_RESOLUTION", "SEMANTIC_UNRESOLVED")],
        )

    def test_a4_multiple_or_conflicting_resolutions_are_unresolved(self) -> None:
        # (a) two approved registrations on the same observation: no precedence may pick one.
        ambiguous = self.chain_with_relationships(
            (relationship_record(extra_bases=(INELIGIBLE_BASIS,)),), "a4-ambiguous"
        )
        first = self.supplier_input(ambiguous).eligibility_for(SUPPLIER, DEMAND)
        assert first is not None
        self.assertTrue(first.unresolved)
        self.assertEqual(first.root_condition, "SOURCING_STATUS_MAPPING_AMBIGUOUS")
        # (b) two accepted records claiming the same relationship: the grain is unresolved and the
        # pair-level decision stays unresolved instead of silently preferring one record.
        conflicting = self.chain_with_relationships(
            (relationship_record(), relationship_record()), "a4-conflicting-records"
        )
        second = self.supplier_input(conflicting).eligibility_for(SUPPLIER, DEMAND)
        assert second is not None
        self.assertTrue(second.unresolved)
        self.assertEqual(
            second.root_condition, "SUPPLIER_RELATIONSHIP_EVIDENCE_CONFLICT"
        )
        self.assertEqual(len(second.considered_references), 2)
        # (c) no association at all: the mapping evidence is missing, never assumed.
        absent = self.chain_with_relationships(
            (relationship_record(basis=None),), "a4-no-mapping-evidence"
        )
        third = self.supplier_input(absent).eligibility_for(SUPPLIER, DEMAND)
        assert third is not None
        self.assertTrue(third.unresolved)
        self.assertEqual(third.root_condition, "SOURCING_STATUS_NO_MAPPING_EVIDENCE")

    def test_a5_the_caller_can_never_inject_the_outcome(self) -> None:
        import inspect

        import snapshot_loader.supplier_risk_input as module

        parameters = list(inspect.signature(compute_supplier_risk_input).parameters)
        self.assertEqual(parameters, ["construction", "recommendations", "accepted"])
        self.assertFalse(
            {"eligibility", "outcome", "eligible", "mapping_basis"} & set(parameters)
        )
        # The registry maps the approved **mapping_basis** literal, never the source value: a record
        # whose source value literally says "APPROVED"/"ELIGIBLE" stays unresolved when its basis is
        # not approved -- no real source vocabulary is interpreted anywhere.
        for source_value in ("APPROVED", "ACTIVE", "QUALIFIED", "ELIGIBLE", "BLOCKED"):
            with self.subTest(source_value=source_value):
                built = self.chain_with_relationships(
                    (
                        relationship_record(
                            status=source_value, basis=UNREGISTERED_BASIS
                        ),
                    ),
                    name=f"a5-{source_value.lower()}",
                )
                relationship = self.supplier_input(built).eligibility_for(
                    SUPPLIER, DEMAND
                )
                assert relationship is not None
                self.assertTrue(relationship.unresolved)
        identifiers = module_identifiers(module)
        for forbidden in ("APPROVED", "ACTIVE", "QUALIFIED", "BLOCKED", "INACTIVE"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, identifiers)
        self.assertEqual(
            module.SUPPLIER_ELIGIBILITY_OUTCOMES,
            frozenset({ELIGIBILITY_ELIGIBLE, ELIGIBILITY_INELIGIBLE}),
        )
        self.assertEqual(
            set(module.SUPPLIER_ELIGIBILITY_BASIS_BY_LITERAL),
            {ELIGIBLE_BASIS, INELIGIBLE_BASIS},
        )

    def test_a6_relationship_existence_alone_is_never_eligible(self) -> None:
        built = self.chain_with_relationships(
            (relationship_record(basis=None),), "a6-existence-only"
        )
        result = self.supplier_input(built)
        relationship = result.eligibility_for(SUPPLIER, DEMAND)
        assert relationship is not None
        self.assertFalse(relationship.eligible)
        self.assertEqual(result.evaluation_contexts, ())
        # Supplier identity alone (role 9) never creates a relationship either: with no
        # ``Supplier-Material Relationship`` evidence provided at all, the pair has no relationship
        # decision and the capability is unavailable -- no business finding is fabricated for it.
        identity_only = self.build_chain(
            supplier_identities=({"supplier_id": SUPPLIER},),
            supplier_performances=(performance_record(),),
            name="a6-identity-only",
        )
        identity_result = self.supplier_input(identity_only)
        self.assertEqual(identity_result.eligible_relationships, ())
        self.assertEqual(identity_result.relationships, ())
        self.assertIsNone(identity_result.eligibility_for(SUPPLIER, DEMAND))
        self.assertFalse(identity_result.capability_available)
        # When the relationship role *is* provided but states no such pair, the performance evidence
        # alone never makes it a candidate and no relationship reference is fabricated for it.
        declared_elsewhere = self.build_chain(
            demands=((DEMAND, "130", D2),),
            supplier_relationships=(
                relationship_record(SUPPLIER, OTHER, basis=ELIGIBLE_BASIS),
            ),
            supplier_performances=(performance_record(SUPPLIER, DEMAND),),
            name="a6-declared-elsewhere",
        )
        absent = self.supplier_input(declared_elsewhere).eligibility_for(SUPPLIER, DEMAND)
        assert absent is not None
        self.assertTrue(absent.unresolved)
        self.assertEqual(absent.root_condition, "SUPPLIER_RELATIONSHIP_ABSENT")
        self.assertIsNone(absent.relationship_reference)
        self.assertIsNone(absent.evidence_reference)
        self.assertEqual(len(absent.considered_references), 1)

    def test_a7_ineligible_is_a_valid_exclusion(self) -> None:
        built = self.build_chain(
            supplier_relationships=(relationship_record(basis=INELIGIBLE_BASIS),),
            supplier_performances=(performance_record(),),
            name="a7-valid-exclusion",
        )
        result = self.supplier_input(built)
        relationship = result.eligibility_for(SUPPLIER, DEMAND)
        assert relationship is not None
        self.assertTrue(relationship.ineligible)
        # No issue, no DATA_INCOMPLETE, no evaluation context, and the procurement side is untouched.
        self.assertEqual(relationship.issues, ())
        self.assertEqual(result.rule_issues, ())
        self.assertEqual(result.capability_issues, ())
        self.assertEqual(result.evaluation_contexts, ())
        self.assertIsNone(result.context_for(PLANT, SUPPLIER, DEMAND))

    def test_a8_unresolved_uses_the_existing_taxonomy(self) -> None:
        built = self.chain_with_relationships(
            (relationship_record(basis=UNREGISTERED_BASIS),), "a8-unresolved-taxonomy"
        )
        result = self.supplier_input(built)
        relationship = result.eligibility_for(SUPPLIER, DEMAND)
        assert relationship is not None
        issues = relationship.rule_issues
        self.assertEqual(len(issues), 1)
        self.assertEqual((issues[0].category, issues[0].reason), (
            "SEMANTIC_RESOLUTION",
            "SEMANTIC_UNRESOLVED",
        ))
        self.assertEqual(issues[0].layer, 2)
        self.assertIn("§4.4.62", issues[0].design_reference)
        # The outcome is never defaulted to eligible or ineligible.
        self.assertEqual(result.evaluation_contexts, ())

    def chain_with_relationships(
        self, relationships: tuple[dict[str, Any], ...], name: str
    ):
        return self.build_chain(
            supplier_identities=({"supplier_id": SUPPLIER},),
            supplier_relationships=relationships,
            supplier_performances=(performance_record(),),
            name=name,
        )


class CompositionTests(SupplierRiskInputTestCase):
    # --- A′ §K 12-20: composition, isolation, boundaries -------------------------------

    def test_a9_binding_is_verified_before_any_evidence_is_consumed(self) -> None:
        run_a = self.eligible_chain("a9-run-a")
        run_b = self.build_chain(
            supplier_relationships=(relationship_record(),),
            supplier_performances=(performance_record(),),
            analysis_run_id="RUN-B",
            package_id="SIMULATED-PKG-0002",
            name="a9-run-b",
        )
        with self.assertRaises(AnalysisRunBindingError) as caught:
            compute_supplier_risk_input(
                run_a.construction, self.recommendations(run_b), accepted=run_a.accepted
            )
        issue = caught.exception.issues[0]
        self.assertEqual((issue.category, issue.reason), ("PROVENANCE", "PROVENANCE_MISMATCH"))
        self.assertIn("BR-PROCUREMENT-001", issue.location)

    def test_a10_cross_run_foreign_package_and_unbound_inputs_are_rejected(self) -> None:
        run_a = self.eligible_chain("a10-run-a")
        run_b = self.build_chain(
            supplier_relationships=(relationship_record(),),
            supplier_performances=(performance_record(),),
            package_id="SIMULATED-PKG-0002",
            name="a10-run-b",
        )
        with self.assertRaises(AnalysisRunBindingError) as caught:
            compute_supplier_risk_input(
                run_a.construction,
                self.recommendations(run_a),
                accepted=run_b.accepted,
            )
        issue = caught.exception.issues[0]
        self.assertEqual((issue.category, issue.reason), ("PROVENANCE", "PROVENANCE_MISMATCH"))
        self.assertIn("accepted package", issue.location)
        unbound = dataclasses.replace(
            self.recommendations(run_a), analysis_run=None
        )
        with self.assertRaises(AnalysisRunBindingError) as caught:
            compute_supplier_risk_input(
                run_a.construction, unbound, accepted=run_a.accepted
            )
        self.assertEqual(caught.exception.issues[0].reason, "PROVENANCE_UNRESOLVED")

    def test_a11_references_are_real_and_never_fabricated(self) -> None:
        built = self.eligible_chain("a11-real-references")
        result = self.supplier_input(built)
        relationship = result.eligibility_for(SUPPLIER, DEMAND)
        assert relationship is not None
        # The relationship reference is the accepted record's own G3-A technical reference and its
        # evidence reference is the object's package-scoped provenance.
        self.assertIsNotNone(relationship.relationship_reference)
        self.assertIsNotNone(relationship.evidence_reference)
        self.assertEqual(
            relationship.evidence_reference.logical_dataset_role,
            "Supplier-Material Relationship",
        )
        self.assertEqual(
            relationship.evidence_reference.snapshot_package_identity,
            built.accepted.package_id,
        )
        self.assertEqual(
            relationship.considered_references, (relationship.relationship_reference,)
        )
        # The payload carries no fabricated upstream item and no evidence field it does not own.
        payload = relationship.to_dict()
        self.assertEqual(payload["relationship_reference"], relationship.relationship_reference)
        self.assertNotIn("ApplicableMOQ", payload)
        self.assertNotIn("OverallSupplierRisk", payload)
        # AnalysisDate stays reachable from the bound Analysis Run.
        self.assertEqual(result.analysis_date, built.construction.analysis_run.analysis_date)

    def test_a12_the_same_material_in_two_plants_keeps_its_own_need_date(self) -> None:
        # A genuine second Plant demand for the *same* material inside the same analysis run: both
        # Plant-scoped recommendation contexts are produced by the registered chain, each with its own
        # upstream shortage reference -- nothing about the upstream result is fabricated.
        built = self.build_chain(
            extra_plant_families=((OTHER_PLANT, DEMAND, "120", D1),),
            moq_policies=(
                moq_policy_record(DEMAND, moq="100"),
                moq_policy_record(
                    DEMAND,
                    moq="100",
                    plant=OTHER_PLANT,
                    locator="SIMULATED-SRC-MOQ-P2",
                ),
            ),
            supplier_relationships=(relationship_record(),),
            supplier_performances=(performance_record(),),
            name="a12-plant-isolation",
        )
        recommendations = self.recommendations(built)
        # Each Plant's own entry carries its own truthful shortage reference.
        for plant_id, expected_date in ((PLANT, D2), (OTHER_PLANT, D1)):
            entry = recommendations.for_family(plant_id, DEMAND)
            assert entry is not None
            self.assertEqual(entry.recommendation_need_date, expected_date)
            reference = entry.shortage_reference
            assert reference is not None
            self.assertEqual(reference.rule, "BR-SHORTAGE-001")
            self.assertEqual(reference.grain, (plant_id, DEMAND, expected_date))

        result = self.supplier_input(built, recommendations=recommendations)
        first = result.context_for(PLANT, SUPPLIER, DEMAND)
        second = result.context_for(OTHER_PLANT, SUPPLIER, DEMAND)
        assert first is not None and second is not None
        self.assertEqual(first.recommendation_need_date, D2)
        self.assertEqual(second.recommendation_need_date, D1)
        self.assertNotEqual(
            first.recommendation_need_date, second.recommendation_need_date
        )
        self.assertEqual(len(result.evaluation_contexts), 2)
        self.assertEqual(result.issues, ())
        # The business grain never absorbs plant_id; plant stays evaluation context.
        self.assertEqual(first.grain, (SUPPLIER, DEMAND))
        self.assertEqual(first.evaluation_context, (PLANT, DEMAND, SUPPLIER))
        self.assertEqual(second.evaluation_context, (OTHER_PLANT, DEMAND, SUPPLIER))

    def test_a13_a_reliable_need_date_forms_the_evaluation_context(self) -> None:
        built = self.eligible_chain("a13-reliable-need-date")
        result = self.supplier_input(built)
        context = result.context_for(PLANT, SUPPLIER, DEMAND)
        assert context is not None
        self.assertEqual(context.recommendation_need_date, D2)
        self.assertTrue(context.recommendation_need_date_resolved)
        self.assertEqual(context.root_condition, None)
        self.assertEqual(context.issues, ())
        self.assertEqual(result.contexts_for(SUPPLIER, DEMAND), (context,))
        self.assertIs(result.eligibility_for(SUPPLIER, DEMAND), context.eligibility)

    def test_a14_a_data_incomplete_quantity_does_not_pollute_the_context(self) -> None:
        built = self.build_chain(
            moq_policies=(moq_policy_record(DEMAND, moq=None),),
            supplier_relationships=(relationship_record(),),
            supplier_performances=(performance_record(),),
            name="a14-quantity-data-incomplete",
        )
        recommendations = self.recommendations(built)
        entry = recommendations.for_family(PLANT, DEMAND)
        assert entry is not None
        # The procurement quantity is DATA_INCOMPLETE while RecommendationNeedDate stays reliable and
        # is still supported by the entry's own matching shortage reference.
        self.assertEqual(entry.outcome, "DATA_INCOMPLETE")
        self.assertEqual(entry.recommendation_need_date, D2)
        assert entry.shortage_reference is not None
        self.assertEqual(entry.shortage_reference.grain, (PLANT, DEMAND, D2))
        result = self.supplier_input(built, recommendations=recommendations)
        context = result.context_for(PLANT, SUPPLIER, DEMAND)
        assert context is not None
        self.assertEqual(context.recommendation_need_date, D2)
        self.assertEqual(context.root_condition, None)
        self.assertEqual(context.issues, ())
        self.assertEqual(result.rule_issues, ())

    def test_a15_an_unresolved_need_date_keeps_the_unresolved_composition_state(self) -> None:
        built = self.build_chain(
            demands=((DEMAND, "10", D1), (DEMAND, "10", D2)),
            targets=((DEMAND, D1, "APPROVED"), (DEMAND, D2, "UNRESOLVED")),
            supplier_relationships=(relationship_record(),),
            supplier_performances=(performance_record(),),
            name="a15-need-date-unresolved",
        )
        result = self.supplier_input(built)
        context = result.context_for(PLANT, SUPPLIER, DEMAND)
        assert context is not None
        self.assertIsNone(context.recommendation_need_date)
        self.assertFalse(context.recommendation_need_date_resolved)
        self.assertEqual(context.root_condition, "RECOMMENDATION_NEED_DATE_UNRESOLVED")
        # The registered upstream reason stays visible and no date is guessed.
        self.assertEqual(
            [(issue.category, issue.reason) for issue in context.inherited_issues],
            [("SEMANTIC_RESOLUTION", "SEMANTIC_UNRESOLVED")],
        )
        # The reliable supplier-side evidence is preserved for the future rule.
        self.assertEqual(len(context.performance), 1)
        self.assertEqual(context.eligibility.outcome, ELIGIBILITY_ELIGIBLE)

    def test_a16_a_reliable_valid_absence_forms_no_evaluation_context(self) -> None:
        built = self.build_chain(
            demands=((DEMAND, "130", D2), (OTHER, "10", D2)),
            targets=((DEMAND, D2, "APPROVED"), (OTHER, D2, "APPROVED")),
            supplier_relationships=(
                relationship_record(),
                relationship_record(material=OTHER, basis=ELIGIBLE_BASIS),
            ),
            supplier_performances=(
                performance_record(material=OTHER),
                performance_record(material=DEMAND),
            ),
            name="a16-valid-absence",
        )
        result = self.supplier_input(built)
        self.assertTrue(result.is_valid_absence(PLANT, OTHER))
        self.assertIsNone(result.context_for(PLANT, SUPPLIER, OTHER))
        self.assertEqual(
            [item.material_code for item in result.evaluation_contexts], [DEMAND]
        )
        # Valid absence is never DATA_INCOMPLETE and generates no issue.
        self.assertEqual(result.issues, ())
        self.assertEqual(result.valid_absence_grains, ((PLANT, OTHER),))
        # Audit: the seam consumes the upstream valid-absence surface **verbatim** -- it neither adds
        # nor drops a family and therefore never claims a stronger authority than the registered
        # upstream result (which already derives it from the consumed shortage result and validates its
        # own family partition).  Re-validating it here would need the shortage result as a new runtime
        # input, which A′ does not authorise and which this seam must not invent.
        upstream = self.recommendations(built)
        self.assertEqual(
            set(result.valid_absence_grains), set(upstream.valid_absence_grains)
        )
        self.assertEqual(
            len(result.valid_absence_grains), len(set(result.valid_absence_grains))
        )
        self.assertEqual(result.valid_absence_grains, tuple(sorted(result.valid_absence_grains)))

    def test_a17_a_not_provided_evidence_role_is_capability_unavailable(self) -> None:
        # Supplier-Material Relationship provided, Supplier Performance not provided.
        built = self.build_chain(
            supplier_relationships=(relationship_record(),),
            name="a17-performance-not-provided",
        )
        result = self.supplier_input(built)
        self.assertFalse(result.capability_available)
        self.assertEqual(result.evaluation_contexts, ())
        self.assertEqual(len(result.capability_issues), 1)
        issue = result.capability_issues[0]
        self.assertEqual(
            (issue.category, issue.reason),
            ("EVIDENCE_AVAILABILITY", "EVIDENCE_ROLE_NOT_PROVIDED"),
        )
        self.assertIn("Supplier Performance", issue.detail)
        self.assertIn("§4.4.84", issue.design_reference)
        # The capability condition is never faked into a business DATA_INCOMPLETE Risk Card.
        self.assertNotIn("OverallSupplierRisk", result.to_dict())
        self.assertFalse(result.to_dict()["capability_available"])
        # The eligibility resolution itself is unaffected by the missing performance role.
        relationship = result.eligibility_for(SUPPLIER, DEMAND)
        assert relationship is not None
        self.assertTrue(relationship.eligible)

        # Supplier-Material Relationship itself not provided: capability unavailable, no relationship
        # decision is fabricated.
        relationship_missing = self.build_chain(
            supplier_performances=(performance_record(),),
            name="a17-relationship-not-provided",
        )
        missing_result = self.supplier_input(relationship_missing)
        self.assertFalse(missing_result.capability_available)
        self.assertEqual(missing_result.relationships, ())
        self.assertEqual(missing_result.evaluation_contexts, ())
        self.assertEqual(len(missing_result.capability_issues), 1)
        self.assertTrue(
            any(
                "Supplier-Material Relationship" in issue.detail
                for issue in missing_result.capability_issues
            )
        )

    def test_a21_a_tampered_need_date_without_a_matching_reference_fails_closed(self) -> None:
        built = self.eligible_chain("a21-tampered-date")
        recommendations = self.recommendations(built)
        entry = recommendations.for_family(PLANT, DEMAND)
        assert entry is not None and entry.shortage_reference is not None
        # The claimed date is altered while the entry keeps its original upstream shortage reference.
        tampered = dataclasses.replace(entry, recommendation_need_date=D1)
        replaced = dataclasses.replace(recommendations, recommendations=(tampered,))
        result = self.supplier_input(built, recommendations=replaced)
        context = result.context_for(PLANT, SUPPLIER, DEMAND)
        assert context is not None
        # Not a normal context: the claimed date is neither trusted nor replaced ...
        self.assertIsNone(context.recommendation_need_date)
        self.assertFalse(context.recommendation_need_date_resolved)
        self.assertEqual(
            context.root_condition, "RECOMMENDATION_NEED_DATE_LINKAGE_MISMATCH"
        )
        self.assertEqual(
            [(issue.category, issue.reason) for issue in context.rule_issues],
            [("PROVENANCE", "PROVENANCE_MISMATCH")],
        )
        self.assertEqual(
            [(issue.category, issue.reason) for issue in result.rule_issues],
            [("PROVENANCE", "PROVENANCE_MISMATCH")],
        )
        # ... while the reliable supplier-side evidence stays visible (fail closed, not dropped).
        self.assertEqual(context.eligibility.outcome, ELIGIBILITY_ELIGIBLE)
        self.assertEqual(len(context.performance), 1)

    def test_a22_a_tampered_plant_without_a_matching_reference_fails_closed(self) -> None:
        built = self.eligible_chain("a22-tampered-plant")
        recommendations = self.recommendations(built)
        entry = recommendations.for_family(PLANT, DEMAND)
        assert entry is not None and entry.shortage_reference is not None
        # The Plant is altered while the reference still points at the original Plant.
        tampered = dataclasses.replace(entry, plant_id=OTHER_PLANT)
        replaced = dataclasses.replace(recommendations, recommendations=(tampered,))
        result = self.supplier_input(built, recommendations=replaced)
        context = result.context_for(OTHER_PLANT, SUPPLIER, DEMAND)
        assert context is not None
        self.assertIsNone(context.recommendation_need_date)
        self.assertEqual(
            context.root_condition, "RECOMMENDATION_NEED_DATE_LINKAGE_MISMATCH"
        )
        self.assertEqual(
            [(issue.category, issue.reason) for issue in context.rule_issues],
            [("PROVENANCE", "PROVENANCE_MISMATCH")],
        )
        # The original Plant's context is untouched: no date moved with the claim.
        self.assertIsNone(result.context_for(PLANT, SUPPLIER, DEMAND))

    def test_a23_a_tampered_material_with_a_foreign_reference_fails_closed(self) -> None:
        built = self.build_chain(
            supplier_relationships=(
                relationship_record(material=DEMAND),
                relationship_record(material=OTHER),
            ),
            supplier_performances=(
                performance_record(material=DEMAND),
                performance_record(material=OTHER),
            ),
            name="a23-tampered-material",
        )
        recommendations = self.recommendations(built)
        entry = recommendations.for_family(PLANT, DEMAND)
        assert entry is not None and entry.shortage_reference is not None
        # The material is altered while the reference still names the original material: an eligible
        # relationship for the new material exists, so a *trusting* seam would form a normal context.
        tampered = dataclasses.replace(entry, material_code=OTHER)
        replaced = dataclasses.replace(recommendations, recommendations=(tampered,))
        result = self.supplier_input(built, recommendations=replaced)
        context = result.context_for(PLANT, SUPPLIER, OTHER)
        assert context is not None
        self.assertIsNone(context.recommendation_need_date)
        self.assertEqual(
            context.root_condition, "RECOMMENDATION_NEED_DATE_LINKAGE_MISMATCH"
        )
        self.assertEqual(
            [(issue.category, issue.reason) for issue in context.rule_issues],
            [("PROVENANCE", "PROVENANCE_MISMATCH")],
        )

    def test_a24_a_missing_or_foreign_rule_reference_is_not_a_linkage(self) -> None:
        built = self.eligible_chain("a24-reference-shapes")
        recommendations = self.recommendations(built)
        entry = recommendations.for_family(PLANT, DEMAND)
        assert entry is not None and entry.shortage_reference is not None
        # (a) no reference at all: the required linkage is absent, not mismatched.
        absent = dataclasses.replace(entry, shortage_reference=None)
        absent_result = self.supplier_input(
            built,
            recommendations=dataclasses.replace(
                recommendations, recommendations=(absent,)
            ),
        )
        absent_context = absent_result.context_for(PLANT, SUPPLIER, DEMAND)
        assert absent_context is not None
        self.assertIsNone(absent_context.recommendation_need_date)
        self.assertEqual(
            absent_context.root_condition, "RECOMMENDATION_NEED_DATE_LINKAGE_ABSENT"
        )
        self.assertEqual(
            [(issue.category, issue.reason) for issue in absent_context.rule_issues],
            [("PROVENANCE", "PROVENANCE_UNRESOLVED")],
        )
        # (b) a reference to another rule is not the registered shortage linkage either.
        foreign = dataclasses.replace(
            entry, shortage_reference=dataclasses.replace(
                entry.shortage_reference, rule="BR-NOT-THE-SHORTAGE-RULE"
            )
        )
        foreign_result = self.supplier_input(
            built,
            recommendations=dataclasses.replace(
                recommendations, recommendations=(foreign,)
            ),
        )
        foreign_context = foreign_result.context_for(PLANT, SUPPLIER, DEMAND)
        assert foreign_context is not None
        self.assertIsNone(foreign_context.recommendation_need_date)
        self.assertEqual(
            foreign_context.root_condition, "RECOMMENDATION_NEED_DATE_LINKAGE_MISMATCH"
        )
        self.assertEqual(
            [(issue.category, issue.reason) for issue in foreign_context.rule_issues],
            [("PROVENANCE", "PROVENANCE_MISMATCH")],
        )

    def test_a25_a_coherent_entry_with_a_matching_reference_still_forms_the_context(self) -> None:
        built = self.eligible_chain("a25-coherent-linkage")
        recommendations = self.recommendations(built)
        entry = recommendations.for_family(PLANT, DEMAND)
        assert entry is not None and entry.shortage_reference is not None
        self.assertEqual(entry.shortage_reference.rule, "BR-SHORTAGE-001")
        self.assertEqual(
            entry.shortage_reference.grain, (PLANT, DEMAND, entry.recommendation_need_date)
        )
        result = self.supplier_input(built, recommendations=recommendations)
        context = result.context_for(PLANT, SUPPLIER, DEMAND)
        assert context is not None
        self.assertEqual(context.recommendation_need_date, D2)
        self.assertTrue(context.recommendation_need_date_resolved)
        self.assertEqual(context.root_condition, None)
        self.assertEqual(context.issues, ())
        self.assertEqual(result.issues, ())

    def test_a20_determinism_frozen_surfaces_and_stable_serialization(self) -> None:
        first = self.build_chain(
            supplier_identities=({"supplier_id": SUPPLIER},),
            supplier_relationships=(
                relationship_record(SUPPLIER_B, basis=INELIGIBLE_BASIS),
                relationship_record(SUPPLIER, basis=ELIGIBLE_BASIS),
            ),
            supplier_performances=(
                performance_record(SUPPLIER_B),
                performance_record(SUPPLIER),
            ),
            name="a20-first",
        )
        second = self.build_chain(
            supplier_identities=({"supplier_id": SUPPLIER},),
            supplier_relationships=(
                relationship_record(SUPPLIER_B, basis=INELIGIBLE_BASIS),
                relationship_record(SUPPLIER, basis=ELIGIBLE_BASIS),
            ),
            supplier_performances=(
                performance_record(SUPPLIER_B),
                performance_record(SUPPLIER),
            ),
            name="a20-second",
        )
        first_result = self.supplier_input(first)
        second_result = self.supplier_input(second)
        self.assertEqual(first_result.to_dict(), second_result.to_dict())
        # Deterministic ordering: relationships by supplier, contexts by plant + material + supplier.
        self.assertEqual(
            [item.supplier_id for item in first_result.relationships],
            [SUPPLIER, SUPPLIER_B],
        )
        self.assertEqual(
            [item.supplier_id for item in first_result.evaluation_contexts], [SUPPLIER]
        )
        self.assertIs(first_result.analysis_run, first.construction.analysis_run)
        self.assertTrue(dataclasses.is_dataclass(first_result))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            first_result.relationships = ()  # type: ignore[misc]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            first_result.relationships[0].outcome = ELIGIBILITY_ELIGIBLE  # type: ignore[misc]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            first_result.evaluation_contexts[0].plant_id = OTHER_PLANT  # type: ignore[misc]


class PerformanceSurfaceTests(SupplierRiskInputTestCase):
    """A′ §H: the real performance surfaces are preserved without computing any risk."""

    def test_r1_the_performance_inputs_stay_reachable(self) -> None:
        built = self.eligible_chain("r1-performance-surface")
        context = self.supplier_input(built).context_for(PLANT, SUPPLIER, DEMAND)
        assert context is not None
        self.assertEqual(len(context.performance), 1)
        performance = context.performance[0]
        self.assertEqual(performance.canonical_target, "Supplier Performance")
        self.assertEqual(performance.value_of("PerformancePeriod"), "2026-Q3")
        self.assertEqual(
            performance.value_of("PerformanceUpdatedAt"), "2026-09-30T00:00:00Z"
        )
        self.assertEqual(performance.value_of("DeliveryPerformance"), "97")
        self.assertEqual(performance.value_of("QualityPerformance"), "99")
        self.assertEqual(performance.value_of("standard_lead_time_days"), "10")
        payload = context.to_dict()
        self.assertEqual(payload["RecommendationNeedDate"], D2)
        self.assertIn("AnalysisDate", self.supplier_input(built).to_dict()["analysis_run"])
        self.assertNotIn("DaysUntilNeed", payload)
        self.assertNotIn("LeadTimeRisk", payload)

    def test_r2_a_missing_period_stays_visible_without_becoming_a_risk(self) -> None:
        built = self.build_chain(
            supplier_relationships=(relationship_record(),),
            supplier_performances=(performance_record(drop_period=True),),
            name="r2-missing-period",
        )
        result = self.supplier_input(built)
        context = result.context_for(PLANT, SUPPLIER, DEMAND)
        assert context is not None
        # The record is supplied but its measurement period is unresolved: it stays visible on the
        # unresolved surface so a future rule can fail the affected dimensions closed.
        self.assertEqual(context.performance, ())
        self.assertEqual(len(context.unresolved_performance), 1)
        unresolved = context.unresolved_performance[0]
        self.assertEqual(unresolved.value_of("DeliveryPerformance"), "97")
        self.assertEqual(unresolved.value_of("QualityPerformance"), "99")
        self.assertFalse(unresolved.has("PerformancePeriod"))
        self.assertEqual(context.issues, ())

    def test_r3_performance_is_never_shared_across_materials(self) -> None:
        built = self.build_chain(
            demands=((DEMAND, "130", D2),),
            supplier_relationships=(
                relationship_record(),
                relationship_record(material=OTHER),
            ),
            supplier_performances=(
                performance_record(material=DEMAND),
                performance_record(material=OTHER),
            ),
            name="r3-no-shared-performance",
        )
        result = self.supplier_input(built)
        # Only the Procurement Recommendation family (DEMAND) forms a context; the OTHER relationship
        # is eligible but has no procurement context to belong to.
        self.assertEqual(
            [item.material_code for item in result.evaluation_contexts], [DEMAND]
        )
        self.assertIsNone(result.context_for(PLANT, SUPPLIER, OTHER))
        context = result.context_for(PLANT, SUPPLIER, DEMAND)
        assert context is not None
        # Exactly this material's performance evidence -- never another material's.
        self.assertEqual(len(context.performance), 1)
        self.assertEqual(context.performance[0].value_of("material_code"), DEMAND)
        self.assertEqual(
            [item.value_of("material_code") for item in context.performance], [DEMAND]
        )
        for relationship in result.relationships:
            self.assertTrue(relationship.eligible)

    def test_r4_serialization_has_no_risk_or_selection_vocabulary(self) -> None:
        import snapshot_loader.supplier_risk_input as module

        identifiers = module_identifiers(module)
        for forbidden in (
            "DaysUntilNeed",
            "LeadTimeRisk",
            "DeliveryRisk",
            "QualityRisk",
            "OverallSupplierRisk",
            "rank",
            "ranking",
            "winner",
            "selection",
            "best_supplier",
            "recommended_purchase_qty",
            "MOQAdjustmentQty",
            "ProcurementRequestDraft",
            "LeadTimeRiskData",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, identifiers)
        for forbidden in ("LOW", "MEDIUM", "HIGH"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, identifiers)
        # No filesystem / raw-source access anywhere in the seam.
        source = Path(module.__file__).read_text(encoding="utf-8")
        for forbidden in ("open(", "Path(", "os.path", "glob(", "read_bytes", "read_text"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)
        # The result surface carries no risk-value field at all.
        fields = {
            field.name
            for dataclass_type in (
                SupplierRiskInputResult,
                module.SupplierRiskEvaluationContext,
                module.SupplierRelationshipEligibility,
            )
            for field in dataclasses.fields(dataclass_type)
        }
        self.assertFalse(
            fields
            & {
                "days_until_need",
                "lead_time_risk",
                "delivery_risk",
                "quality_risk",
                "overall_supplier_risk",
                "risk_level",
                "score",
            }
        )


if __name__ == "__main__":  # pragma: no cover - direct invocation
    unittest.main()
