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
import json
import unittest
from pathlib import Path
from typing import Any

from snapshot_loader import (
    ELIGIBILITY_ELIGIBLE,
    ELIGIBILITY_INELIGIBLE,
    FAIL_CLOSED_EVIDENCE_OUTCOME,
    MATERIAL_IDENTITY_TARGET,
    PERFORMANCE_OBSERVATION_FIELDS,
    PLANT_MATERIAL_IDENTITY_ROLE,
    PLANT_MATERIAL_IDENTITY_TARGET,
    ROOT_IDENTITY_UNRESOLVED,
    ROOT_PERFORMANCE_COMPETING_UNRESOLVED,
    ROOT_PERFORMANCE_OBSERVATION_ABSENT,
    ROOT_PERFORMANCE_OBSERVATION_MULTIPLE,
    ROOT_PERFORMANCE_OBSERVATION_UNRESOLVED,
    ROOT_RELATIONSHIP_ABSENT,
    SUPPLIER_IDENTITY_ROLE,
    SUPPLIER_IDENTITY_TARGET,
    SUPPLIER_RISK_EVIDENCE_STATUS_DATA_INCOMPLETE,
    AnalysisRunBindingError,
    SupplierRiskEvidenceOutcome,
    SupplierRiskIdentityState,
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
        supplier_identities: tuple[dict[str, Any], ...] | None = None,
        supplier_relationships: tuple[dict[str, Any], ...] = (),
        supplier_performances: tuple[dict[str, Any], ...] = (),
        identity_evidence: bool = True,
        identity_contexts: tuple[dict[str, Any], ...] | None = None,
        extra_plant_families: tuple[tuple[Any, Any, Any, Any], ...] = (),
        analysis_run_id: str = "RUN-1",
        package_id: str = "SIMULATED-PKG-0001",
        name: str,
    ):
        """Assemble one registered chain with optional supplier-side roles (9 ／ 10 ／ 11).

        ``extra_plant_families`` states additional Plant-scoped demand families of the same materials
        inside the *same* analysis run (``(plant_id, material_code, quantity, required_date)``), so a
        Plant-isolation test consumes genuinely formed upstream results instead of a fabricated one.

        ``supplier_identities`` ／ ``identity_evidence`` ／ ``identity_contexts`` state the **identity**
        evidence roles ``§4.4.6`` Capability C requires (``Supplier identity`` ／
        ``Plant / Material identity context``).  The defaults declare them for what the fixture itself
        describes -- one ``Supplier identity`` record per supplier named by its own role 10 ／ 11 records
        (``None``) and one ``Plant / Material identity context`` record per distinct **material**
        (``identity_evidence=True``) -- so the canonical fixture is capability-conformant **and** its
        exact identity evidence resolves: the ``Material`` canonical grain is ``material_code`` alone
        (``§4.1.4`` B), so stating one material under two Plants would leave the material identity
        unresolved (``§4.4.102`` C forbids same-value deduplication) and make the evaluation fail closed.
        ``identity_contexts`` overrides the derived records verbatim, which is how a test states
        ambiguous material identity evidence.

        Passing an explicit empty tuple ／ ``identity_evidence=False`` is how a test states *"the role
        was never provided"* -- the capability-readiness case -- which is **not** the same thing as a
        role-10 ／ 11 record carrying ``supplier_id`` ／ ``material_code``.
        """

        relationships = tuple(supplier_relationships)
        performances = tuple(supplier_performances)

        if supplier_identities is None:
            named_suppliers = {
                record["supplier_id"]
                for record in relationships + performances
                if isinstance(record.get("supplier_id"), str) and record["supplier_id"] != ""
            }
            identities = tuple(
                {"supplier_id": supplier_id}
                for supplier_id in sorted(named_suppliers, key=str)
            )
        else:
            identities = tuple(supplier_identities)

        if identity_contexts is not None:
            identity_records = tuple(identity_contexts)
        elif identity_evidence:
            materials = {material for material, _quantity, _date in demands}
            materials |= {
                record["material_code"]
                for record in relationships + performances
                if isinstance(record.get("material_code"), str)
                and record["material_code"] != ""
            }
            materials |= {
                material_code
                for _plant, material_code, _quantity, _date in extra_plant_families
                if isinstance(material_code, str) and material_code != ""
            }
            identity_records = tuple(
                {"plant_id": PLANT, "material_code": material_code}
                for material_code in sorted(materials, key=str)
            )
        else:
            identity_records = ()

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
            supplier_identities=identities,
            supplier_relationships=relationships,
            supplier_performances=performances,
            identity_contexts=identity_records,
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
        # unresolved surface so a future rule can fail the affected dimensions closed, and the approved
        # Option A applicability boundary (``§2.7.26``) states that no applicable observation exists
        # instead of reading a period-less record.
        self.assertEqual(context.performance, ())
        self.assertEqual(len(context.unresolved_performance), 1)
        unresolved = context.unresolved_performance[0]
        self.assertEqual(unresolved.value_of("DeliveryPerformance"), "97")
        self.assertEqual(unresolved.value_of("QualityPerformance"), "99")
        self.assertFalse(unresolved.has("PerformancePeriod"))
        self.assertIsNone(context.applicable_performance)
        self.assertTrue(context.performance_applicability_unresolved)
        self.assertEqual(
            context.performance_root_condition, ROOT_PERFORMANCE_OBSERVATION_UNRESOLVED
        )
        # The only finding is the registered semantic pair -- no risk value, no risk level.
        self.assertEqual(
            [(issue.category, issue.reason) for issue in context.issues],
            [("SEMANTIC_RESOLUTION", "SEMANTIC_UNRESOLVED")],
        )

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


class PerformanceApplicabilityTests(SupplierRiskInputTestCase):
    """Option A (Issue #164): exactly-one ``Supplier Performance`` observation applicability.

    Covers ``§2.7.26``: a normal evaluation context consumes performance evidence only when exactly one
    ``Supplier Performance`` observation is applicable to its exact ``supplier_id`` ＋ ``material_code``
    -- exactly one resolved observation and no competing unresolved performance evidence -- and states
    ``SEMANTIC_RESOLUTION`` ／ ``SEMANTIC_UNRESOLVED`` otherwise, never selecting an observation.
    """

    def context(self, built, *, plant: Any = PLANT, supplier: Any = SUPPLIER, material: Any = DEMAND):
        """The evaluation context of one fixture, asserted to exist."""

        context = self.supplier_input(built).context_for(plant, supplier, material)
        assert context is not None
        return context

    def two_distinct_periods(self, name: str):
        """One eligible relationship with two resolved observations of different periods."""

        return self.build_chain(
            supplier_relationships=(relationship_record(),),
            supplier_performances=(
                performance_record(period="2026-Q2"),
                performance_record(period="2026-Q3"),
            ),
            name=name,
        )

    # --- 1 ／ 7 ／ 8: exactly one applicable observation, consumed as one unit ------------------

    def test_a26_exactly_one_observation_is_applicable(self) -> None:
        built = self.eligible_chain("a26-exactly-one")
        result = self.supplier_input(built)
        context = result.context_for(PLANT, SUPPLIER, DEMAND)
        assert context is not None
        observation = context.applicable_performance
        assert observation is not None
        self.assertFalse(context.performance_applicability_unresolved)
        self.assertIsNone(context.performance_root_condition)
        self.assertEqual(context.issues, ())
        # The applicable observation **is** the accepted resolved object: one record, not a merge.
        self.assertIs(observation.object, context.performance[0])
        self.assertEqual(observation.canonical_target, "Supplier Performance")
        self.assertEqual(observation.record_reference, context.performance[0].record_reference)
        self.assertIs(observation.evidence_reference, context.performance[0].provenance)
        # All five registered properties come from that same observation, as one coherent unit.
        self.assertEqual(observation.performance_period, "2026-Q3")
        self.assertEqual(observation.performance_updated_at, "2026-09-30T00:00:00Z")
        self.assertEqual(observation.delivery_performance, "97")
        self.assertEqual(observation.quality_performance, "99")
        self.assertEqual(observation.standard_lead_time_days, "10")
        self.assertEqual(
            observation.values(),
            {
                "PerformancePeriod": "2026-Q3",
                "PerformanceUpdatedAt": "2026-09-30T00:00:00Z",
                "DeliveryPerformance": "97",
                "QualityPerformance": "99",
                "standard_lead_time_days": "10",
            },
        )
        self.assertEqual(observation.absent_fields(), ())
        self.assertEqual(context.performance_observed_for, "2026-Q3")
        self.assertEqual(context.unresolved_performance, ())

    def test_a27_no_field_is_ever_spliced_across_records(self) -> None:
        # Two candidate observations whose fields are deliberately *complementary*: a splicer would
        # combine 2026-Q2 with 2026-Q3 (for example the period of one and the lead time of the other).
        built = self.build_chain(
            supplier_relationships=(relationship_record(),),
            supplier_performances=(
                performance_record(period="2026-Q2", delivery="90", quality="91", lead_time="7"),
                performance_record(period="2026-Q3", delivery="97", quality="99", lead_time="10"),
            ),
            name="a27-no-splicing",
        )
        context = self.context(built)
        # No applicable unit exists, so no field of either record may be consumed at all.
        self.assertIsNone(context.applicable_performance)
        self.assertIsNone(context.performance_observed_for)
        self.assertEqual(
            [item.value_of("PerformancePeriod") for item in context.performance],
            ["2026-Q2", "2026-Q3"],
        )
        self.assertEqual(
            [item.value_of("standard_lead_time_days") for item in context.performance],
            ["7", "10"],
        )
        payload = context.to_dict()
        self.assertIsNone(payload["applicable_performance"])
        self.assertTrue(payload["performance_applicability_unresolved"])
        # Each record stays individually readable -- visible, never merged and never dropped.
        self.assertEqual(len(payload["performance"]), 2)

    # --- 2 ／ 6: multiple periods, and ``PerformanceUpdatedAt`` as a non-authority ----------------

    def test_a28_two_resolved_periods_are_unresolved_without_precedence(self) -> None:
        built = self.two_distinct_periods("a28-two-periods")
        context = self.context(built)
        self.assertIsNone(context.applicable_performance)
        self.assertTrue(context.performance_applicability_unresolved)
        self.assertEqual(
            context.performance_root_condition, ROOT_PERFORMANCE_OBSERVATION_MULTIPLE
        )
        # Both reliable observations stay visible on the resolved surface.
        self.assertEqual(len(context.performance), 2)
        self.assertEqual(context.unresolved_performance, ())
        # Exactly one finding, using only the registered taxonomy pair.
        self.assertEqual(
            [(issue.category, issue.reason) for issue in context.issues],
            [("SEMANTIC_RESOLUTION", "SEMANTIC_UNRESOLVED")],
        )
        issue = context.issues[0]
        self.assertEqual(issue.layer, 2)
        self.assertEqual(issue.affected_evidence, "Supplier Performance")
        self.assertIn("performance_applicability", issue.location)
        self.assertIn("§2.7.26", issue.design_reference)

    def test_a29_a_newer_performance_updated_at_never_selects(self) -> None:
        # The newest ``PerformanceUpdatedAt`` belongs to the *earlier* period, so neither "latest
        # period" nor "newest updated_at" could be honoured -- and neither is.
        built = self.build_chain(
            supplier_relationships=(relationship_record(),),
            supplier_performances=(
                performance_record(period="2026-Q2", updated="2026-12-31T00:00:00Z"),
                performance_record(period="2026-Q3", updated="2026-10-01T00:00:00Z"),
            ),
            name="a29-updated-at-is-not-an-authority",
        )
        context = self.context(built)
        self.assertIsNone(context.applicable_performance)
        self.assertEqual(
            context.performance_root_condition, ROOT_PERFORMANCE_OBSERVATION_MULTIPLE
        )
        # Every record keeps its own ``PerformanceUpdatedAt`` verbatim and none is promoted.
        self.assertEqual(
            [item.value_of("PerformanceUpdatedAt") for item in context.performance],
            ["2026-12-31T00:00:00Z", "2026-10-01T00:00:00Z"],
        )

    # --- 3 ／ 4 ／ 5: same-period duplicate, competing unresolved, missing period ---------------

    def test_a30_a_same_period_duplicate_is_never_promoted(self) -> None:
        built = self.build_chain(
            supplier_relationships=(relationship_record(),),
            supplier_performances=(
                performance_record(period="2026-Q3"),
                performance_record(period="2026-Q3", updated="2026-10-31T00:00:00Z"),
            ),
            name="a30-same-period-duplicate",
        )
        report = built.construction
        # The canonicalization left both records unresolved on one (supplier, material, period) grain,
        # and each of them still carries a grain ...
        self.assertEqual(report.objects_for("Supplier Performance"), ())
        unresolved_objects = report.unresolved_for("Supplier Performance")
        self.assertEqual(len(unresolved_objects), 2)
        self.assertTrue(all(item.grain is not None for item in unresolved_objects))
        # ... so the seam reports that bucket verbatim: re-deriving "resolved" from ``grain is not
        # None`` (the merged-bucket defect this test is the regression for) would have promoted both.
        context = self.context(built)
        self.assertEqual(context.performance, ())
        self.assertEqual(len(context.unresolved_performance), 2)
        self.assertIsNone(context.applicable_performance)
        self.assertEqual(
            context.performance_root_condition, ROOT_PERFORMANCE_OBSERVATION_UNRESOLVED
        )
        self.assertEqual(
            [(issue.category, issue.reason) for issue in context.issues],
            [("SEMANTIC_RESOLUTION", "SEMANTIC_UNRESOLVED")],
        )

    def test_a31_one_resolved_observation_next_to_competing_unresolved_evidence(self) -> None:
        built = self.build_chain(
            supplier_relationships=(relationship_record(),),
            supplier_performances=(
                performance_record(period="2026-Q3"),
                performance_record(period="2026-Q3", drop_period=True),
            ),
            name="a31-competing-unresolved",
        )
        context = self.context(built)
        # One resolved observation is *not* adopted while same-grain competing evidence is unresolved.
        self.assertEqual(len(context.performance), 1)
        self.assertEqual(len(context.unresolved_performance), 1)
        self.assertIsNone(context.applicable_performance)
        self.assertEqual(
            context.performance_root_condition, ROOT_PERFORMANCE_COMPETING_UNRESOLVED
        )
        self.assertEqual(
            [(issue.category, issue.reason) for issue in context.issues],
            [("SEMANTIC_RESOLUTION", "SEMANTIC_UNRESOLVED")],
        )

    def test_a32_a_missing_period_and_absent_evidence_are_distinguishable(self) -> None:
        missing_period = self.build_chain(
            supplier_relationships=(relationship_record(),),
            supplier_performances=(performance_record(drop_period=True),),
            name="a32-missing-period",
        )
        context = self.context(missing_period)
        self.assertIsNone(context.applicable_performance)
        self.assertEqual(
            context.performance_root_condition, ROOT_PERFORMANCE_OBSERVATION_UNRESOLVED
        )
        self.assertEqual((context.performance, len(context.unresolved_performance)), ((), 1))

        # The performance role **is** provided here, but no record claims this supplier + material.
        absent = self.build_chain(
            supplier_relationships=(relationship_record(),),
            supplier_performances=(performance_record(material=OTHER),),
            name="a32-absent-for-this-pair",
        )
        result = self.supplier_input(absent)
        self.assertTrue(result.capability_available)
        absent_context = result.context_for(PLANT, SUPPLIER, DEMAND)
        assert absent_context is not None
        self.assertEqual(absent_context.performance, ())
        self.assertEqual(absent_context.unresolved_performance, ())
        self.assertIsNone(absent_context.applicable_performance)
        self.assertEqual(
            absent_context.performance_root_condition, ROOT_PERFORMANCE_OBSERVATION_ABSENT
        )
        self.assertEqual(
            [(issue.category, issue.reason) for issue in absent_context.issues],
            [("SEMANTIC_RESOLUTION", "SEMANTIC_UNRESOLVED")],
        )

    # --- 9 ／ 11 ／ 12 ／ 13: isolation, eligibility, Plant ／ need date, capability ------------

    def test_a33_another_supplier_or_material_never_participates(self) -> None:
        built = self.build_chain(
            supplier_relationships=(
                relationship_record(),
                relationship_record(SUPPLIER_B),
            ),
            supplier_performances=(
                performance_record(),
                performance_record(SUPPLIER_B, period="2026-Q1"),
                performance_record(material=OTHER, period="2026-Q1"),
            ),
            name="a33-no-foreign-performance",
        )
        result = self.supplier_input(built)
        first = result.context_for(PLANT, SUPPLIER, DEMAND)
        second = result.context_for(PLANT, SUPPLIER_B, DEMAND)
        assert first is not None and second is not None
        # Neither context sees the other supplier's or another material's evidence -- so both stay
        # exactly-one applicable rather than becoming "competing evidence".
        for context, supplier, period in (
            (first, SUPPLIER, "2026-Q3"),
            (second, SUPPLIER_B, "2026-Q1"),
        ):
            with self.subTest(supplier=supplier):
                observation = context.applicable_performance
                assert observation is not None
                self.assertEqual(observation.performance_period, period)
                self.assertEqual(observation.object.value_of("supplier_id"), supplier)
                self.assertEqual(observation.object.value_of("material_code"), DEMAND)
                self.assertEqual(len(context.performance), 1)
                self.assertEqual(context.unresolved_performance, ())
        # The performance-only witness of another material is never shared into a DEMAND context.
        self.assertIsNone(result.context_for(PLANT, SUPPLIER, OTHER))

    def test_a34_eligibility_semantics_are_unchanged(self) -> None:
        built = self.build_chain(
            supplier_relationships=(
                relationship_record(),
                relationship_record(SUPPLIER_B, basis=INELIGIBLE_BASIS),
            ),
            supplier_performances=(
                performance_record(),
                performance_record(SUPPLIER_B),
            ),
            name="a34-eligibility-unchanged",
        )
        result = self.supplier_input(built)
        eligible = result.eligibility_for(SUPPLIER, DEMAND)
        ineligible = result.eligibility_for(SUPPLIER_B, DEMAND)
        assert eligible is not None and ineligible is not None
        self.assertEqual(eligible.outcome, ELIGIBILITY_ELIGIBLE)
        self.assertEqual(ineligible.outcome, ELIGIBILITY_INELIGIBLE)
        self.assertEqual(eligible.issues, ())
        # An ineligible relationship is a valid exclusion: no issue and no evaluation context.
        self.assertEqual(ineligible.issues, ())
        self.assertEqual(
            [item.supplier_id for item in result.evaluation_contexts], [SUPPLIER]
        )
        context = result.context_for(PLANT, SUPPLIER, DEMAND)
        assert context is not None
        self.assertIsNotNone(context.applicable_performance)

    def test_a35_plant_and_need_date_isolation_is_unchanged(self) -> None:
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
            name="a35-plant-isolation",
        )
        result = self.supplier_input(built)
        first = result.context_for(PLANT, SUPPLIER, DEMAND)
        second = result.context_for(OTHER_PLANT, SUPPLIER, DEMAND)
        assert first is not None and second is not None
        # The applicability boundary changes nothing about the Plant ／ need-date composition: each
        # Plant keeps its own date and both consume their own single applicable observation.
        self.assertEqual(first.recommendation_need_date, D2)
        self.assertEqual(second.recommendation_need_date, D1)
        for context in (first, second):
            with self.subTest(plant=context.plant_id):
                observation = context.applicable_performance
                assert observation is not None
                self.assertEqual(observation.performance_period, "2026-Q3")
                self.assertEqual(context.grain, (SUPPLIER, DEMAND))
        self.assertEqual(result.issues, ())

    def test_a36_the_capability_boundary_is_unchanged(self) -> None:
        built = self.build_chain(
            supplier_relationships=(relationship_record(),),
            supplier_performances=(),
            name="a36-capability-unavailable",
        )
        result = self.supplier_input(built)
        self.assertFalse(result.capability_available)
        # A not-provided evidence role never becomes a business applicability finding: no context is
        # formed at all and the registered capability pair stays the only finding.
        self.assertEqual(result.evaluation_contexts, ())
        self.assertEqual(
            [(issue.category, issue.reason) for issue in result.issues],
            [("EVIDENCE_AVAILABILITY", "EVIDENCE_ROLE_NOT_PROVIDED")],
        )
        self.assertIn("Supplier Performance", result.issues[0].detail)

    # --- 10 ／ 14: determinism ／ serialization, and the scope guard ----------------------------

    def test_a37_applicability_is_deterministic_frozen_and_serializable(self) -> None:
        first = self.eligible_chain("a37-first")
        second = self.eligible_chain("a37-second")
        first_result = self.supplier_input(first)
        second_result = self.supplier_input(second)
        self.assertEqual(first_result.to_dict(), second_result.to_dict())
        json.dumps(first_result.to_dict())

        context = first_result.context_for(PLANT, SUPPLIER, DEMAND)
        assert context is not None
        observation = context.applicable_performance
        assert observation is not None
        payload = context.to_dict()
        self.assertFalse(payload["performance_applicability_unresolved"])
        self.assertIsNone(payload["performance_root_condition"])
        self.assertEqual(
            payload["applicable_performance"]["values"],
            {
                "PerformancePeriod": "2026-Q3",
                "PerformanceUpdatedAt": "2026-09-30T00:00:00Z",
                "DeliveryPerformance": "97",
                "QualityPerformance": "99",
                "standard_lead_time_days": "10",
            },
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            context.applicable_performance = None  # type: ignore[misc]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            observation.object = None  # type: ignore[misc]
        # The named accessors are read-only views of the wrapped object, not settable seats.
        with self.assertRaises((dataclasses.FrozenInstanceError, TypeError)):
            observation.performance_period = "2026-Q4"  # type: ignore[misc]

        # The unresolved case is equally deterministic and keeps both buckets in the payload.
        unresolved_first = self.two_distinct_periods("a37-unresolved-first")
        unresolved_second = self.two_distinct_periods("a37-unresolved-second")
        self.assertEqual(
            self.supplier_input(unresolved_first).to_dict(),
            self.supplier_input(unresolved_second).to_dict(),
        )
        unresolved_payload = self.context(unresolved_first).to_dict()
        self.assertTrue(unresolved_payload["performance_applicability_unresolved"])
        self.assertEqual(
            unresolved_payload["performance_root_condition"],
            ROOT_PERFORMANCE_OBSERVATION_MULTIPLE,
        )
        self.assertEqual(len(unresolved_payload["performance"]), 2)

    def test_a38_the_boundary_states_no_risk_and_no_threshold(self) -> None:
        import snapshot_loader.supplier_risk_input as module

        identifiers = module_identifiers(module)
        for forbidden in (
            "DaysUntilNeed",
            "LeadTimeRisk",
            "DeliveryRisk",
            "QualityRisk",
            "OverallSupplierRisk",
            "risk_level",
            "freshness",
            "threshold",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, identifiers)
        for forbidden in ("LOW", "MEDIUM", "HIGH"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, identifiers)
        # The consumed unit is exactly the five registered properties -- no new canonical field.
        self.assertEqual(
            PERFORMANCE_OBSERVATION_FIELDS,
            (
                "PerformancePeriod",
                "PerformanceUpdatedAt",
                "DeliveryPerformance",
                "QualityPerformance",
                "standard_lead_time_days",
            ),
        )
        self.assertEqual(
            PERFORMANCE_OBSERVATION_FIELDS, tuple(module.PERFORMANCE_OBSERVATION_FIELDS)
        )
        # One coherence unit: the observation holds the accepted object itself, so a caller can never
        # assemble one from separately supplied values.
        self.assertEqual(
            {field.name for field in dataclasses.fields(module.SupplierPerformanceObservation)},
            {"object"},
        )
        # The new runtime surface is additive on the existing evaluation context.
        context_fields = {
            field.name
            for field in dataclasses.fields(module.SupplierRiskEvaluationContext)
        }
        self.assertLessEqual(
            {
                "applicable_performance",
                "performance_root_condition",
                "performance",
                "unresolved_performance",
            },
            context_fields,
        )
        self.assertEqual(
            sorted(
                name
                for name in module.__all__
                if isinstance(getattr(module, name), str)
                and getattr(module, name).startswith("PERFORMANCE_")
            ),
            [
                "ROOT_PERFORMANCE_COMPETING_UNRESOLVED",
                "ROOT_PERFORMANCE_OBSERVATION_ABSENT",
                "ROOT_PERFORMANCE_OBSERVATION_MULTIPLE",
                "ROOT_PERFORMANCE_OBSERVATION_UNRESOLVED",
            ],
        )


class CapabilityIdentityTests(SupplierRiskInputTestCase):
    """``§4.4.6`` Capability C: the **identity** evidence roles are capability-readiness gates.

    Capability C requires ``Supplier identity`` and ``Material identity`` evidence for an explicit
    ``supplier_id`` + ``material_code``.  The gate is **role provision** -- reported by
    ``CanonicalConstructionReport.present_roles`` -- and never a property that happens to be assignable
    on a role 10 ／ 11 record (``§4.3.30`` C.2 ／ ``§4.2.18``: "可被指派" ≠ "必须存在").
    """

    def test_a39_a_missing_supplier_identity_role_is_capability_unavailable(self) -> None:
        built = self.build_chain(
            supplier_identities=(),
            supplier_relationships=(relationship_record(),),
            supplier_performances=(performance_record(),),
            name="a39-no-supplier-identity",
        )
        self.assertNotIn(SUPPLIER_IDENTITY_TARGET, built.construction.present_roles)
        result = self.supplier_input(built)
        self.assertFalse(result.capability_available)
        # No evaluation context and therefore no Risk Card is formed.
        self.assertEqual(result.evaluation_contexts, ())
        self.assertIsNone(result.context_for(PLANT, SUPPLIER, DEMAND))
        self.assertEqual(
            [(issue.category, issue.reason) for issue in result.capability_issues],
            [("EVIDENCE_AVAILABILITY", "EVIDENCE_ROLE_NOT_PROVIDED")],
        )
        issue = result.capability_issues[0]
        self.assertEqual(issue.affected_evidence, SUPPLIER_IDENTITY_ROLE)
        self.assertIn(SUPPLIER_IDENTITY_ROLE, issue.location)
        self.assertIn(SUPPLIER_IDENTITY_ROLE, issue.detail)
        self.assertEqual(issue.layer, 2)
        self.assertIn("§4.4.6", issue.design_reference)
        # The relationship decision itself is still resolved and nothing is dropped.
        relationship = result.eligibility_for(SUPPLIER, DEMAND)
        assert relationship is not None
        self.assertEqual(relationship.outcome, ELIGIBILITY_ELIGIBLE)

    def test_a40_all_required_identity_evidence_keeps_the_context_unchanged(self) -> None:
        built = self.build_chain(
            supplier_identities=({"supplier_id": SUPPLIER},),
            supplier_relationships=(relationship_record(),),
            supplier_performances=(performance_record(),),
            name="a40-all-required-evidence",
        )
        # Both identity evidence roles really are provided (not inferred from role 10 ／ 11 properties).
        self.assertIn(SUPPLIER_IDENTITY_TARGET, built.construction.present_roles)
        self.assertIn(PLANT_MATERIAL_IDENTITY_TARGET, built.construction.present_roles)
        result = self.supplier_input(built)
        self.assertTrue(result.capability_available)
        self.assertEqual(result.capability_issues, ())
        self.assertEqual(result.issues, ())
        context = result.context_for(PLANT, SUPPLIER, DEMAND)
        assert context is not None
        self.assertEqual(context.grain, (SUPPLIER, DEMAND))
        self.assertEqual(context.evaluation_context, (PLANT, DEMAND, SUPPLIER))
        self.assertEqual(context.recommendation_need_date, D2)
        observation = context.applicable_performance
        assert observation is not None
        self.assertEqual(observation.performance_period, "2026-Q3")
        self.assertEqual(observation.standard_lead_time_days, "10")
        self.assertEqual(context.issues, ())

    def test_a41_a_missing_material_identity_role_is_capability_unavailable(self) -> None:
        # Upstream does **not** make this construction impossible: the identity role is the only
        # registered carrier of Material identity evidence and nothing in the canonicalization ／
        # shortage ／ procurement chain requires it, so the same fixture still yields a complete
        # procurement family.  It therefore has to be gated here.
        built = self.build_chain(
            supplier_identities=({"supplier_id": SUPPLIER},),
            supplier_relationships=(relationship_record(),),
            supplier_performances=(performance_record(),),
            identity_evidence=False,
            name="a41-no-material-identity",
        )
        self.assertNotIn(PLANT_MATERIAL_IDENTITY_TARGET, built.construction.present_roles)
        entry = self.recommendations(built).for_family(PLANT, DEMAND)
        assert entry is not None
        self.assertEqual(entry.recommendation_need_date, D2)
        result = self.supplier_input(built)
        self.assertFalse(result.capability_available)
        self.assertEqual(result.evaluation_contexts, ())
        self.assertEqual(
            [(issue.category, issue.reason) for issue in result.capability_issues],
            [("EVIDENCE_AVAILABILITY", "EVIDENCE_ROLE_NOT_PROVIDED")],
        )
        self.assertEqual(
            result.capability_issues[0].affected_evidence, PLANT_MATERIAL_IDENTITY_ROLE
        )
        self.assertIn("§4.4.6", result.capability_issues[0].design_reference)

    def test_a42_an_identity_capability_failure_is_not_a_business_outcome(self) -> None:
        built = self.build_chain(
            supplier_identities=(),
            supplier_relationships=(relationship_record(),),
            supplier_performances=(performance_record(),),
            identity_evidence=False,
            name="a42-identity-capability-vs-business",
        )
        result = self.supplier_input(built)
        self.assertFalse(result.capability_available)
        self.assertEqual(result.evaluation_contexts, ())
        # Both identity rows are reported, in deterministic order, using the existing taxonomy only.
        self.assertEqual(
            [issue.affected_evidence for issue in result.capability_issues],
            [SUPPLIER_IDENTITY_ROLE, PLANT_MATERIAL_IDENTITY_ROLE],
        )
        self.assertEqual(
            {(issue.category, issue.reason) for issue in result.issues},
            {("EVIDENCE_AVAILABILITY", "EVIDENCE_ROLE_NOT_PROVIDED")},
        )
        # Not a semantic finding, not a business outcome and not a valid absence.
        self.assertEqual(result.rule_issues, ())
        self.assertEqual(result.inherited_issues, ())
        self.assertFalse(result.is_valid_absence(PLANT, DEMAND))
        payload = result.to_dict()
        self.assertFalse(payload["capability_available"])
        self.assertEqual(payload["evaluation_contexts"], [])
        # The eligibility decision stays published: the capability gate drops no reliable evidence.
        self.assertEqual(
            [item["eligibility"] for item in payload["relationships"]],
            [ELIGIBILITY_ELIGIBLE],
        )
        for forbidden in (
            "DaysUntilNeed",
            "LeadTimeRisk",
            "DeliveryRisk",
            "QualityRisk",
            "OverallSupplierRisk",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, payload)

    def test_a43_role_provision_is_gated_not_the_identity_value(self) -> None:
        # A **declared** identity role whose record carries no usable identity value stays a
        # canonicalization ／ field-level matter (``§4.4.26`` ／ ``§4.4.94``): the evidence role *was*
        # provided, so the capability gate does not fire and no capability finding is fabricated.  The
        # exact identity of the evaluated pair is then **not** reliably resolved, which is the
        # registered fail-closed evidence-outcome case (Issue #168 ``§F1``) -- never a normal context.
        null_identity = self.build_chain(
            supplier_identities=({"supplier_id": None},),
            supplier_relationships=(relationship_record(),),
            supplier_performances=(performance_record(),),
            name="a43-null-identity-value",
        )
        self.assertIn(SUPPLIER_IDENTITY_TARGET, null_identity.construction.present_roles)
        null_result = self.supplier_input(null_identity)
        self.assertTrue(null_result.capability_available)
        self.assertEqual(null_result.capability_issues, ())
        self.assertEqual(null_result.evaluation_contexts, ())
        null_outcome = null_result.outcome_for(PLANT, SUPPLIER, DEMAND)
        assert null_outcome is not None
        self.assertTrue(null_outcome.data_incomplete)
        self.assertTrue(null_outcome.identity_unreliable)
        self.assertEqual(null_outcome.outcome_root_condition, ROOT_IDENTITY_UNRESOLVED)

        # An identity value the deterministic grouping key cannot use leaves the *identity* unresolved
        # at canonicalization; the role is still provided and the gate still does not fire.
        unresolved_identity = self.build_chain(
            supplier_identities=({"supplier_id": []},),
            supplier_relationships=(relationship_record(),),
            supplier_performances=(performance_record(),),
            name="a43-unresolvable-identity-value",
        )
        self.assertIn(SUPPLIER_IDENTITY_TARGET, unresolved_identity.construction.present_roles)
        self.assertEqual(
            unresolved_identity.construction.objects_for(SUPPLIER_IDENTITY_TARGET), ()
        )
        self.assertEqual(
            len(unresolved_identity.construction.unresolved_for(SUPPLIER_IDENTITY_TARGET)), 1
        )
        unresolved_result = self.supplier_input(unresolved_identity)
        self.assertTrue(unresolved_result.capability_available)
        self.assertEqual(unresolved_result.capability_issues, ())
        # The canonicalization's own identity finding is now reachable through the seam (Issue #168
        # ``§G``): the consumer learns the exact identity could not be resolved without re-reading the
        # construction, and no capability finding is invented for it.
        self.assertEqual(
            {(issue.category, issue.reason) for issue in unresolved_result.issues},
            {("IDENTITY_RESOLUTION", "UNRESOLVED_IDENTITY")},
        )
        self.assertEqual(
            [issue.category for issue in unresolved_result.identity_issues],
            ["IDENTITY_RESOLUTION"],
        )


class NonNormalEvidenceOutcomeTests(SupplierRiskInputTestCase):
    """Issue #168 Option A: the request-bounded fail-closed Supplier Risk evidence outcome.

    Every runtime entry is driven by a procurement evaluation request that actually exists; the seam
    never derives a request from performance ／ identity ／ relationship evidence, never runs a normal
    risk evaluation on a fail-closed outcome and never produces a keyed result it cannot truthfully key.
    """

    def outcomes(self, built, *, plant: Any = PLANT, supplier: Any = SUPPLIER, material: Any = DEMAND):
        """The single fail-closed outcome of one exact plant ／ supplier ／ material, asserted to exist."""

        result = self.supplier_input(built)
        outcome = result.outcome_for(plant, supplier, material)
        assert outcome is not None
        return result, outcome

    def unresolved_pair(self, name: str, **kwargs):
        """One claimed pair whose relationship eligibility is unresolved (no approved basis)."""

        return self.build_chain(
            supplier_relationships=(relationship_record(basis=UNREGISTERED_BASIS),),
            supplier_performances=(performance_record(),),
            name=name,
            **kwargs,
        )

    def test_a44_the_normal_path_stays_a_context_and_creates_no_outcome(self) -> None:
        built = self.eligible_chain("a44-normal-path")
        result = self.supplier_input(built)
        self.assertTrue(result.capability_available)
        self.assertEqual(result.evidence_outcomes, ())
        self.assertEqual(result.unkeyable_relationships, ())
        context = result.context_for(PLANT, SUPPLIER, DEMAND)
        assert context is not None
        self.assertEqual(context.grain, (SUPPLIER, DEMAND))
        self.assertEqual(context.recommendation_need_date, D2)
        observation = context.applicable_performance
        assert observation is not None
        self.assertEqual(observation.standard_lead_time_days, "10")
        # The pair identities are published on the normal context (Issue #168 §G) and both resolve.
        self.assertTrue(context.identity_reliable)
        self.assertEqual(
            [item.target for item in context.identities],
            [SUPPLIER_IDENTITY_TARGET, MATERIAL_IDENTITY_TARGET],
        )
        for state in context.identities:
            with self.subTest(target=state.target):
                self.assertTrue(state.reliable)
                self.assertIsNotNone(state.identity_reference)
                self.assertEqual(state.unresolved_references, ())
        self.assertEqual(result.issues, ())

    def test_a45_an_ineligible_relationship_is_a_valid_exclusion(self) -> None:
        built = self.build_chain(
            supplier_relationships=(relationship_record(basis=INELIGIBLE_BASIS),),
            supplier_performances=(performance_record(),),
            name="a45-ineligible-exclusion",
        )
        result = self.supplier_input(built)
        self.assertTrue(result.capability_available)
        # Valid exclusion: no context, no fail-closed outcome, no DATA_INCOMPLETE and no issue.
        self.assertEqual(result.evaluation_contexts, ())
        self.assertEqual(result.evidence_outcomes, ())
        self.assertEqual(result.issues, ())
        relationship = result.eligibility_for(SUPPLIER, DEMAND)
        assert relationship is not None
        self.assertTrue(relationship.ineligible)
        self.assertEqual(relationship.issues, ())

    def test_a46_an_unresolved_relationship_yields_one_fail_closed_outcome(self) -> None:
        built = self.unresolved_pair("a46-unresolved-one-request")
        result, outcome = self.outcomes(built)
        # Exactly one evaluated request ／ pair entry, and it is fail-closed -- never a normal context.
        self.assertEqual(result.evaluation_contexts, ())
        self.assertEqual(len(result.evidence_outcomes), 1)
        self.assertEqual(outcome.status, SUPPLIER_RISK_EVIDENCE_STATUS_DATA_INCOMPLETE)
        self.assertTrue(outcome.data_incomplete)
        self.assertEqual(outcome.grain, (SUPPLIER, DEMAND))
        self.assertEqual(outcome.evaluation_context, (PLANT, DEMAND, SUPPLIER))
        self.assertEqual(outcome.recommendation_need_date, D2)
        self.assertEqual(outcome.analysis_run_id, built.construction.analysis_run.analysis_run_id)
        # The relationship state, its root condition and its finding are preserved.
        self.assertTrue(outcome.eligibility.unresolved)
        self.assertEqual(
            outcome.outcome_root_condition, outcome.eligibility.root_condition
        )
        self.assertEqual(
            [(issue.category, issue.reason) for issue in outcome.eligibility.issues],
            [("SEMANTIC_RESOLUTION", "SEMANTIC_UNRESOLVED")],
        )
        # Not a card: no risk vocabulary and no applicable-performance unit on a fail-closed outcome.
        payload = outcome.to_dict()
        self.assertEqual(payload["outcome_kind"], FAIL_CLOSED_EVIDENCE_OUTCOME)
        self.assertNotIn("applicable_performance", payload)
        for forbidden in (
            "DaysUntilNeed",
            "LeadTimeRisk",
            "DeliveryRisk",
            "QualityRisk",
            "OverallSupplierRisk",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, payload)

    def test_a47_the_same_pair_under_two_plants_yields_two_isolated_outcomes(self) -> None:
        built = self.unresolved_pair(
            "a47-two-plants",
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
        )
        result = self.supplier_input(built)
        self.assertEqual(result.evaluation_contexts, ())
        self.assertEqual(len(result.evidence_outcomes), 2)
        first = result.outcome_for(PLANT, SUPPLIER, DEMAND)
        second = result.outcome_for(OTHER_PLANT, SUPPLIER, DEMAND)
        assert first is not None and second is not None
        # Two independent Plant-scoped outcomes, each with its own upstream need date.
        self.assertEqual(first.recommendation_need_date, D2)
        self.assertEqual(second.recommendation_need_date, D1)
        self.assertNotEqual(first.recommendation_need_date, second.recommendation_need_date)
        self.assertEqual(first.evaluation_context, (PLANT, DEMAND, SUPPLIER))
        self.assertEqual(second.evaluation_context, (OTHER_PLANT, DEMAND, SUPPLIER))
        for outcome in (first, second):
            with self.subTest(plant=outcome.plant_id):
                self.assertTrue(outcome.data_incomplete)
                # The business grain never absorbs plant_id (§2.7.2): only the context differs.
                self.assertEqual(outcome.grain, (SUPPLIER, DEMAND))
                self.assertEqual(
                    outcome.need_date_reference.grain if outcome.need_date_reference else None,
                    (outcome.plant_id, DEMAND, outcome.recommendation_need_date),
                )

    def test_a48_a_pair_without_a_request_yields_no_outcome(self) -> None:
        # The claim exists and is unresolved, but no procurement evaluation request names its material.
        built = self.build_chain(
            demands=((DEMAND, "130", D2),),
            supplier_relationships=(relationship_record(material=OTHER, basis=UNREGISTERED_BASIS),),
            supplier_performances=(performance_record(material=OTHER),),
            name="a48-no-request",
        )
        result = self.supplier_input(built)
        self.assertTrue(result.capability_available)
        relationship = result.eligibility_for(SUPPLIER, OTHER)
        assert relationship is not None
        self.assertTrue(relationship.unresolved)
        # No request for OTHER ⇒ no business outcome at all, and the finding stays visible.
        self.assertEqual(result.evidence_outcomes, ())
        self.assertEqual(result.evaluation_contexts, ())
        self.assertEqual(result.outcomes_for(SUPPLIER, OTHER), ())
        self.assertEqual(relationship.issues[0].reason, "SEMANTIC_UNRESOLVED")

    def test_a49_performance_evidence_alone_never_creates_an_outcome(self) -> None:
        # Supplier Performance claims (SUPPLIER, DEMAND) but the relationship role states another pair:
        # performance evidence never establishes a relationship, so no Risk Evidence outcome exists.
        built = self.build_chain(
            supplier_relationships=(relationship_record(SUPPLIER, OTHER, basis=ELIGIBLE_BASIS),),
            supplier_performances=(performance_record(SUPPLIER, DEMAND),),
            name="a49-performance-only-pair",
        )
        result = self.supplier_input(built)
        self.assertEqual(result.evidence_outcomes, ())
        self.assertEqual(result.outcomes_for(SUPPLIER, DEMAND), ())
        claimed = result.eligibility_for(SUPPLIER, DEMAND)
        assert claimed is not None
        self.assertTrue(claimed.unresolved)
        self.assertEqual(claimed.root_condition, ROOT_RELATIONSHIP_ABSENT)
        # The semantic finding is preserved and no relationship ／ evidence reference is fabricated.
        self.assertIsNone(claimed.relationship_reference)
        self.assertIsNone(claimed.evidence_reference)
        self.assertEqual(len(claimed.considered_references), 1)
        self.assertEqual(
            [(issue.category, issue.reason) for issue in claimed.issues],
            [("SEMANTIC_RESOLUTION", "SEMANTIC_UNRESOLVED")],
        )
        # The eligible OTHER pair has no request, so the whole result stays outcome-free.
        self.assertEqual(result.outcomes_for(SUPPLIER, OTHER), ())

    def test_a50_an_unresolved_supplier_identity_is_a_fail_closed_outcome(self) -> None:
        # Role 9 is provided (capability available) but the exact identity of SUP-A is unresolved:
        # two identity records share the ``supplier_id`` grain, and no same-value dedup applies.
        built = self.build_chain(
            supplier_identities=(
                {"supplier_id": SUPPLIER},
                {"supplier_id": SUPPLIER},
            ),
            supplier_relationships=(relationship_record(),),
            supplier_performances=(performance_record(),),
            name="a50-supplier-identity-unresolved",
        )
        self.assertEqual(len(built.construction.unresolved_for(SUPPLIER_IDENTITY_TARGET)), 2)
        result, outcome = self.outcomes(built)
        self.assertTrue(result.capability_available)
        self.assertEqual(result.capability_issues, ())
        self.assertTrue(outcome.data_incomplete)
        self.assertEqual(outcome.outcome_root_condition, ROOT_IDENTITY_UNRESOLVED)
        self.assertTrue(outcome.identity_unreliable)
        supplier_state = next(
            item for item in outcome.identities if item.target == SUPPLIER_IDENTITY_TARGET
        )
        material_state = next(
            item for item in outcome.identities if item.target == MATERIAL_IDENTITY_TARGET
        )
        self.assertFalse(supplier_state.reliable)
        self.assertEqual(supplier_state.resolved_references, ())
        self.assertEqual(len(supplier_state.unresolved_references), 2)
        self.assertTrue(material_state.reliable)
        # The exact pair and the request context are preserved, and no level is produced.
        self.assertEqual(outcome.grain, (SUPPLIER, DEMAND))
        self.assertEqual(outcome.recommendation_need_date, D2)
        self.assertEqual(result.evaluation_contexts, ())

    def test_a51_an_unresolved_material_identity_is_a_fail_closed_outcome(self) -> None:
        # Role 1 is provided but states the same material under two Plants: the ``Material`` canonical
        # grain is ``material_code`` alone, so the material identity stays unresolved.
        built = self.build_chain(
            supplier_relationships=(relationship_record(),),
            supplier_performances=(performance_record(),),
            identity_contexts=(
                {"plant_id": PLANT, "material_code": DEMAND},
                {"plant_id": OTHER_PLANT, "material_code": DEMAND},
            ),
            name="a51-material-identity-unresolved",
        )
        self.assertEqual(len(built.construction.unresolved_for(MATERIAL_IDENTITY_TARGET)), 2)
        result, outcome = self.outcomes(built)
        self.assertTrue(result.capability_available)
        self.assertTrue(outcome.data_incomplete)
        self.assertEqual(outcome.outcome_root_condition, ROOT_IDENTITY_UNRESOLVED)
        material_state = next(
            item for item in outcome.identities if item.target == MATERIAL_IDENTITY_TARGET
        )
        supplier_state = next(
            item for item in outcome.identities if item.target == SUPPLIER_IDENTITY_TARGET
        )
        self.assertFalse(material_state.reliable)
        self.assertEqual(len(material_state.unresolved_references), 2)
        self.assertTrue(supplier_state.reliable)
        self.assertEqual(outcome.grain, (SUPPLIER, DEMAND))

    def test_a52_an_unkeyable_pair_yields_no_keyed_outcome(self) -> None:
        # The relationship evidence states no reliable pair grain: an unhashable identity component and
        # a JSON null one both leave the pair unkeyable -- no keyed outcome, no placeholder grain.
        unhashable = self.build_chain(
            supplier_relationships=(relationship_record(supplier=[]),),
            supplier_performances=(performance_record(),),
            name="a52-unhashable-pair",
        )
        result = self.supplier_input(unhashable)
        self.assertEqual(result.evidence_outcomes, ())
        self.assertEqual(result.outcomes_for([], DEMAND), ())
        self.assertEqual(len(result.unkeyable_relationships), 1)
        self.assertEqual(
            result.unkeyable_relationships[0].root_condition,
            "SUPPLIER_RELATIONSHIP_IDENTITY_UNRESOLVED",
        )
        # The canonicalization's IDENTITY_RESOLUTION ／ UNRESOLVED_IDENTITY finding survives verbatim.
        self.assertEqual(
            [(issue.category, issue.reason) for issue in result.identity_issues],
            [("IDENTITY_RESOLUTION", "UNRESOLVED_IDENTITY")],
        )

        null_identity = self.build_chain(
            supplier_relationships=(relationship_record(supplier=None),),
            supplier_performances=(performance_record(),),
            name="a52-null-pair",
        )
        null_result = self.supplier_input(null_identity)
        # No keyed outcome is invented for a null identity component (no fuzzy match, no placeholder).
        self.assertEqual(null_result.evidence_outcomes, ())
        self.assertEqual(len(null_result.unkeyable_relationships), 1)
        self.assertIsNone(null_result.unkeyable_relationships[0].supplier_id)

    def test_a53_a_not_provided_role_still_makes_the_capability_unavailable(self) -> None:
        built = self.unresolved_pair("a53-role-not-provided")
        missing = dataclasses.replace(built.accepted, ) if False else None  # noqa: F841
        # Role 9 not provided at all: capability unavailable, no outcome, and never DATA_INCOMPLETE.
        unavailable = self.build_chain(
            supplier_identities=(),
            supplier_relationships=(relationship_record(basis=UNREGISTERED_BASIS),),
            supplier_performances=(performance_record(),),
            name="a53-no-supplier-identity-role",
        )
        result = self.supplier_input(unavailable)
        self.assertFalse(result.capability_available)
        self.assertEqual(result.evaluation_contexts, ())
        self.assertEqual(result.evidence_outcomes, ())
        self.assertEqual(
            [(issue.category, issue.reason) for issue in result.capability_issues],
            [("EVIDENCE_AVAILABILITY", "EVIDENCE_ROLE_NOT_PROVIDED")],
        )
        self.assertFalse(result.is_valid_absence(PLANT, DEMAND))

    def test_a54_an_unresolved_need_date_is_preserved_without_guessing(self) -> None:
        built = self.build_chain(
            demands=((DEMAND, "10", D1), (DEMAND, "10", D2)),
            targets=((DEMAND, D1, "APPROVED"), (DEMAND, D2, "UNRESOLVED")),
            supplier_relationships=(relationship_record(basis=UNREGISTERED_BASIS),),
            supplier_performances=(performance_record(),),
            name="a54-unresolved-need-date",
        )
        result, outcome = self.outcomes(built)
        self.assertIsNone(outcome.recommendation_need_date)
        self.assertFalse(outcome.recommendation_need_date_resolved)
        self.assertEqual(outcome.need_date_root_condition, "RECOMMENDATION_NEED_DATE_UNRESOLVED")
        self.assertIsNone(outcome.need_date_reference)
        # The registered upstream reason is preserved and no date is guessed.
        self.assertEqual(
            [(issue.category, issue.reason) for issue in outcome.inherited_issues],
            [("SEMANTIC_RESOLUTION", "SEMANTIC_UNRESOLVED")],
        )
        self.assertTrue(outcome.data_incomplete)

    def test_a55_performance_evidence_is_preserved_for_explainability(self) -> None:
        # Two resolved periods plus a period-less record: the Option A contract is unchanged on the
        # normal path, and a fail-closed outcome still keeps the reliable evidence visible.
        normal = self.build_chain(
            supplier_relationships=(relationship_record(),),
            supplier_performances=(
                performance_record(period="2026-Q2"),
                performance_record(period="2026-Q3"),
            ),
            name="a55-normal-applicability",
        )
        normal_result = self.supplier_input(normal)
        normal_context = normal_result.context_for(PLANT, SUPPLIER, DEMAND)
        assert normal_context is not None
        self.assertIsNone(normal_context.applicable_performance)
        self.assertEqual(
            normal_context.performance_root_condition, ROOT_PERFORMANCE_OBSERVATION_MULTIPLE
        )
        self.assertEqual(normal_result.evidence_outcomes, ())

        fail_closed = self.build_chain(
            supplier_relationships=(relationship_record(basis=UNREGISTERED_BASIS),),
            supplier_performances=(
                performance_record(),
                performance_record(period="2026-Q3", drop_period=True),
            ),
            name="a55-fail-closed-performance",
        )
        _, outcome = self.outcomes(fail_closed)
        self.assertEqual(len(outcome.performance), 1)
        self.assertEqual(len(outcome.unresolved_performance), 1)
        self.assertEqual(outcome.performance[0].value_of("PerformancePeriod"), "2026-Q3")
        payload = outcome.to_dict()
        self.assertEqual(len(payload["performance"]), 1)
        self.assertEqual(len(payload["unresolved_performance"]), 1)

    def test_a56_only_truthful_references_are_published(self) -> None:
        built = self.unresolved_pair("a56-truthful-references")
        _, outcome = self.outcomes(built)
        reference = outcome.eligibility.relationship_reference
        assert reference is not None
        # The relationship reference names the real accepted record and its provenance agrees.
        provenance = outcome.eligibility.evidence_reference
        assert provenance is not None
        self.assertIn(provenance.artifact, reference)
        self.assertEqual(provenance.logical_dataset_role, "Supplier-Material Relationship")
        # The upstream need-date reference is the consumed shortage result, never a synthesised one.
        need_date_reference = outcome.need_date_reference
        assert need_date_reference is not None
        self.assertEqual(need_date_reference.rule, "BR-SHORTAGE-001")
        self.assertEqual(need_date_reference.grain, (PLANT, DEMAND, D2))
        # Each identity state's reference is a real record reference, not a fabricated one.
        for state in outcome.identities:
            for published in state.considered_references:
                with self.subTest(published=published):
                    self.assertIn("|", published)
        # A performance-only pair never reaches an outcome, so no performance reference can be
        # mistaken for a relationship reference.
        self.assertIsNone(
            self.supplier_input(
                self.build_chain(
                    supplier_relationships=(
                        relationship_record(SUPPLIER, OTHER, basis=ELIGIBLE_BASIS),
                    ),
                    supplier_performances=(performance_record(SUPPLIER, DEMAND),),
                    name="a56-performance-only",
                )
            )
            .eligibility_for(SUPPLIER, DEMAND)
            .relationship_reference
        )

    def test_a57_outcomes_are_deterministic_frozen_and_serializable(self) -> None:
        def build(name: str):
            return self.unresolved_pair(
                name,
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
            )

        first_result = self.supplier_input(build("a57-first"))
        second_result = self.supplier_input(build("a57-second"))
        self.assertEqual(first_result.to_dict(), second_result.to_dict())
        json.dumps(first_result.to_dict())
        # Deterministic ordering: by plant, then material, then supplier.
        self.assertEqual(
            [item.evaluation_context for item in first_result.evidence_outcomes],
            [(PLANT, DEMAND, SUPPLIER), (OTHER_PLANT, DEMAND, SUPPLIER)],
        )
        outcome = first_result.evidence_outcomes[0]
        self.assertIsInstance(outcome, SupplierRiskEvidenceOutcome)
        self.assertIsInstance(outcome.identities[0], SupplierRiskIdentityState)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            first_result.evidence_outcomes = ()  # type: ignore[misc]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            outcome.status = "HIGH"  # type: ignore[misc]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            outcome.identities[0].value = "SUP-B"  # type: ignore[misc]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            first_result.identity_issues = ()  # type: ignore[misc]

    def test_a58_the_outcome_surface_adds_no_risk_vocabulary(self) -> None:
        import snapshot_loader.supplier_risk_input as module

        identifiers = module_identifiers(module)
        for forbidden in (
            "DaysUntilNeed",
            "LeadTimeRisk",
            "DeliveryRisk",
            "QualityRisk",
            "OverallSupplierRisk",
            "risk_level",
            "severity",
            "threshold",
            "rank",
            "ranking",
            "winner",
            "selection",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, identifiers)
        for forbidden in ("LOW", "MEDIUM", "HIGH"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, identifiers)
        # The outcome's business status is the existing DATA_INCOMPLETE literal, not a new enum.
        self.assertEqual(SUPPLIER_RISK_EVIDENCE_STATUS_DATA_INCOMPLETE, "DATA_INCOMPLETE")
        self.assertEqual(
            {field.name for field in dataclasses.fields(SupplierRiskEvidenceOutcome)}
            & {"days_until_need", "lead_time_risk", "delivery_risk", "quality_risk",
               "overall_supplier_risk", "risk_level"},
            set(),
        )


if __name__ == "__main__":  # pragma: no cover - direct invocation
    unittest.main()
