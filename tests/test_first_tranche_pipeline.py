"""First-tranche integration / acceptance closure (Issue #172).

The registered chain of ``POC Design v0.2`` §10.1 B is exercised **as a whole** through the
composition surface (:func:`snapshot_loader.run_first_tranche_pipeline` /
:func:`snapshot_loader.run_first_tranche_pipeline_from_paths`):

    Snapshot loader -> Layer-2 validation -> Phase A canonical objects
      -> requirement / inventory / inbound / substitute -> shortage
      -> Phase B procurement policy input -> procurement recommendation
      -> Supplier Risk runtime input seam (``A′``) -> Supplier Risk Evidence

The fixtures reuse the existing end-to-end chain builder
(:class:`tests.test_supplier_risk_input.SupplierRiskInputTestCase`), so every test runs the
whole registered chain over one **real** accepted SIMULATED package and compares the
composed result against the same chain computed stage by stage outside the pipeline.

No test re-implements a business rule, and no fixture states real enterprise data.
"""

from __future__ import annotations

import ast
import json
import unittest
from fractions import Fraction
from pathlib import Path
from typing import Any

import snapshot_loader.first_tranche_pipeline as pipeline_module
from snapshot_loader import (
    INBOUND_RULE_ID,
    INVENTORY_RULE_ID,
    LAYER1_NOT_ACCEPTED_REASON,
    PIPELINE_STAGES,
    PROCUREMENT_POLICY_INPUT_STAGE,
    PROCUREMENT_RECOMMENDATION_RULE_ID,
    PROCUREMENT_RECOMMENDATION_UNRESOLVED,
    RISK_LOW,
    RULE_ID,
    SHORTAGE_RULE_ID,
    STAGE_CANONICAL_OBJECTS,
    STAGE_INBOUND,
    STAGE_INVENTORY,
    STAGE_LAYER2,
    STAGE_PROCUREMENT_POLICY_INPUT,
    STAGE_PROCUREMENT_RECOMMENDATION,
    STAGE_REQUIREMENT,
    STAGE_SHORTAGE,
    STAGE_SNAPSHOT_LOADER,
    STAGE_SUBSTITUTE,
    STAGE_SUPPLIER_RISK_EVIDENCE,
    STAGE_SUPPLIER_RISK_INPUT_SEAM,
    SUBSTITUTE_RULE_ID,
    SUPPLIER_RISK_INPUT_STAGE,
    SUPPLIER_RISK_STAGE,
    AnalysisRunBindingError,
    FirstTranchePipelineResult,
    PhaseAHandoff,
    compute_procurement_recommendation,
    compute_shortage,
    compute_supplier_risk,
    compute_supplier_risk_input,
    run_first_tranche_pipeline,
    run_first_tranche_pipeline_from_paths,
    validate_layer2,
)
from tests.helpers import DatasetSpec, PackageSpec, build_package
from tests.test_procurement_policy_input import moq_policy_record
from tests.test_shortage_calculation import (
    D2,
    DEMAND,
    PLANT,
    ROLE_SUPPLIER_PERFORMANCE,
)
from tests.test_supplier_risk_input import (
    OTHER_PLANT,
    SUPPLIER,
    SUPPLIER_B,
    SupplierRiskInputTestCase,
    performance_record,
    relationship_record,
)

#: The registered entry points the composition is allowed to call, and nothing else.
REGISTERED_ENTRY_POINTS = {
    "load_package",
    "load_package_from_paths",
    "validate_layer2",
    "construct_canonical_objects",
    "compute_requirement_calculation",
    "compute_opening_usable_inventory",
    "compute_effective_inbound",
    "compute_substitute_supply",
    "compute_shortage",
    "compute_procurement_policy_input",
    "compute_procurement_recommendation",
    "compute_supplier_risk_input",
    "compute_supplier_risk",
}

#: Sibling modules the composition may import from (no ``constants``, no rule internals).
ALLOWED_SIBLING_MODULES = {
    "canonical_objects",
    "inbound_calculation",
    "inventory_calculation",
    "layer2",
    "loader",
    "procurement_policy_input",
    "procurement_recommendation",
    "report",
    "requirement_calculation",
    "shortage_calculation",
    "substitute_calculation",
    "supplier_risk_calculation",
    "supplier_risk_input",
}

#: Standard-library modules a pure composition may import (types and path plumbing only).
ALLOWED_STDLIB_MODULES = {
    "__future__",
    "collections",
    "dataclasses",
    "datetime",
    "fractions",
    "os",
    "typing",
}

#: The registered business literals the composition may never mint or name as a value.
FORBIDDEN_BUSINESS_LITERALS = {
    "ACCEPTED",
    "REJECTED",
    "UNUSABLE",
    "DATA_INCOMPLETE",
    "SHORTAGE",
    "NORMAL",
    "BUFFER_BREACH",
    "HIGH",
    "MEDIUM",
    "LOW",
    "eligible",
    "ineligible",
    "unresolved",
}


class FirstTranchePipelineTests(SupplierRiskInputTestCase):
    """One accepted SIMULATED package composed through the registered entry points."""

    # --- helpers ---------------------------------------------------------------------

    def complete_chain(self, name: str, **kwargs: Any):
        """The registered chain of one shorted family plus eligible supplier evidence."""

        return self.build_chain(
            supplier_relationships=(relationship_record(),),
            supplier_performances=(performance_record(),),
            name=name,
            **kwargs,
        )

    def pipeline(self, built) -> FirstTranchePipelineResult:
        """Run the composition over the exact accepted package the fixture built."""

        return run_first_tranche_pipeline_from_paths(
            built.root, built.boundary, built.handoff
        )

    def stage_results(self, result: FirstTranchePipelineResult) -> dict[str, Any]:
        """The registered result object of every stage, keyed by its stage name."""

        return {
            STAGE_SNAPSHOT_LOADER: result.import_report,
            STAGE_LAYER2: result.layer2,
            STAGE_CANONICAL_OBJECTS: result.construction,
            STAGE_REQUIREMENT: result.requirements,
            STAGE_INVENTORY: result.inventory,
            STAGE_INBOUND: result.inbounds,
            STAGE_SUBSTITUTE: result.substitutes,
            STAGE_SHORTAGE: result.shortage,
            STAGE_PROCUREMENT_POLICY_INPUT: result.procurement_policy_input,
            STAGE_PROCUREMENT_RECOMMENDATION: result.procurement_recommendation,
            STAGE_SUPPLIER_RISK_INPUT_SEAM: result.supplier_risk_input,
            STAGE_SUPPLIER_RISK_EVIDENCE: result.supplier_risk,
        }

    # --- tests -----------------------------------------------------------------------

    def test_g1_a_complete_simulated_package_reaches_every_stage(self) -> None:
        """One accepted package runs the whole chain to recommendation and risk evidence."""

        built = self.complete_chain("g1")
        result = self.pipeline(built)

        self.assertTrue(result.accepted)
        self.assertEqual(
            [entry.name for entry in result.stages], [name for name, _ in PIPELINE_STAGES]
        )
        for name, stage_result in self.stage_results(result).items():
            self.assertIsNotNone(stage_result, msg=f"stage result missing: {name}")
            self.assertTrue(result.stage(name).entered, msg=f"stage not entered: {name}")
        self.assertIsNotNone(result.analysis_run)

        recommendation = result.procurement_recommendation.for_family(PLANT, DEMAND)
        self.assertIsNotNone(recommendation)
        assert recommendation is not None
        self.assertTrue(recommendation.has_numeric_result)
        self.assertEqual(recommendation.recommendation_need_date, D2)

        card = result.supplier_risk.card_for(PLANT, SUPPLIER, DEMAND)
        self.assertIsNotNone(card)
        assert card is not None
        self.assertEqual(card.overall_supplier_risk, RISK_LOW)
        self.assertIsNone(card.status)
        self.assertTrue(card.evidence_complete)
        self.assertTrue(result.supplier_risk.capability_available)

    def test_g2_the_composition_reproduces_the_registered_chain_stage_by_stage(self) -> None:
        """Every stage result equals the same stage computed outside the pipeline."""

        built = self.complete_chain("g2")
        result = self.pipeline(built)

        self.assertEqual(result.layer2.to_dict(), validate_layer2(built.accepted).to_dict())
        self.assertEqual(result.construction.to_dict(), built.construction.to_dict())
        self.assertEqual(result.requirements.to_dict(), built.requirements.to_dict())
        self.assertEqual(result.inventory.to_dict(), built.inventory.to_dict())
        self.assertEqual(result.inbounds.to_dict(), built.inbounds.to_dict())
        self.assertEqual(result.substitutes.to_dict(), built.substitutes.to_dict())
        self.assertEqual(result.shortage.to_dict(), built.shortage.to_dict())

        policy_input = self.resolve(built)
        self.assertEqual(
            result.procurement_policy_input.to_dict(), policy_input.to_dict()
        )
        recommendations = compute_procurement_recommendation(
            built.construction, built.shortage, policy_input
        )
        self.assertEqual(
            result.procurement_recommendation.to_dict(), recommendations.to_dict()
        )
        supplier_input = compute_supplier_risk_input(
            built.construction, recommendations, accepted=built.accepted
        )
        self.assertEqual(result.supplier_risk_input.to_dict(), supplier_input.to_dict())
        self.assertEqual(
            result.supplier_risk.to_dict(),
            compute_supplier_risk(supplier_input).to_dict(),
        )

    def test_g3_one_accepted_package_and_one_analysis_run_bind_every_stage(self) -> None:
        """The whole chain carries exactly one accepted content view and one Analysis Run."""

        built = self.complete_chain("g3")
        result = self.pipeline(built)
        accepted = built.accepted

        self.assertEqual(result.accepted_package_id, accepted.package_id)
        self.assertEqual(result.accepted_content_view_digest, accepted.content_view_digest)
        self.assertEqual(result.analysis_run, built.construction.analysis_run)
        self.assertEqual(result.analysis_run.snapshot_package_identity, accepted.package_id)
        self.assertEqual(
            result.analysis_run.accepted_content_view_digest, accepted.content_view_digest
        )
        self.assertEqual(
            result.analysis_run.analysis_run_id, built.handoff.analysis_run_id
        )

        bound = (
            result.construction,
            result.requirements,
            result.inventory,
            result.inbounds,
            result.substitutes,
            result.shortage,
            result.procurement_policy_input,
            result.procurement_recommendation,
            result.supplier_risk_input,
            result.supplier_risk,
        )
        for stage_result in bound:
            self.assertEqual(stage_result.analysis_run, result.analysis_run)

        self.assertEqual(result.layer2.package_id, accepted.package_id)
        self.assertEqual(
            result.layer2.accepted_content_view_digest, accepted.content_view_digest
        )

    def test_g4_repeatability_and_stable_serialization(self) -> None:
        """Identical package, handoff and rule set produce an identical payload."""

        built = self.complete_chain("g4")
        first = self.pipeline(built)
        second = self.pipeline(built)

        self.assertIsNot(first.supplier_risk, second.supplier_risk)
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.supplier_risk.to_dict(), second.supplier_risk.to_dict())
        self.assertEqual(
            json.dumps(first.to_dict(), sort_keys=True, ensure_ascii=False),
            json.dumps(second.to_dict(), sort_keys=True, ensure_ascii=False),
        )

    def test_g5_exact_numeric_semantics_survive_the_composition(self) -> None:
        """The composed results keep the registered exact quantities and day counts."""

        built = self.complete_chain("g5")
        result = self.pipeline(built)

        recommendation = result.procurement_recommendation.for_family(PLANT, DEMAND)
        card = result.supplier_risk.card_for(PLANT, SUPPLIER, DEMAND)
        assert recommendation is not None and card is not None

        self.assertEqual(recommendation.shortage_qty, Fraction(30, 1))
        self.assertEqual(recommendation.base_purchase_need, Fraction(30, 1))
        self.assertEqual(recommendation.applicable_moq.text(), "100")
        self.assertEqual(recommendation.recommended_purchase_qty, Fraction(100, 1))
        self.assertEqual(recommendation.moq_adjustment_qty, Fraction(70, 1))
        self.assertEqual(
            recommendation.to_dict()["RecommendedPurchaseQty"],
            {"numerator": 100, "denominator": 1},
        )

        self.assertEqual(card.days_until_need, 19)
        self.assertEqual(card.days_until_need_text, "19")
        self.assertEqual(card.standard_lead_time_days, "10")
        self.assertEqual(card.lead_time_risk, RISK_LOW)
        for value in (recommendation.shortage_qty, recommendation.recommended_purchase_qty):
            self.assertNotIsInstance(value, float)

    def test_g6_provenance_and_upstream_references_stay_continuous(self) -> None:
        """Every composed reference is a real upstream grain of this very package."""

        built = self.complete_chain("g6")
        result = self.pipeline(built)

        recommendation = result.procurement_recommendation.for_family(PLANT, DEMAND)
        card = result.supplier_risk.card_for(PLANT, SUPPLIER, DEMAND)
        assert recommendation is not None and card is not None

        self.assertIsNotNone(recommendation.shortage_reference)
        self.assertEqual(recommendation.shortage_reference.rule, SHORTAGE_RULE_ID)
        self.assertEqual(recommendation.shortage_reference.grain, (PLANT, DEMAND, D2))
        self.assertIsNotNone(recommendation.policy_input_reference)
        self.assertIsNotNone(result.shortage.for_grain(PLANT, DEMAND, D2))

        self.assertEqual(card.recommendation_need_date, D2)
        self.assertEqual(card.recommendation_need_date, recommendation.recommendation_need_date)
        self.assertIsNotNone(card.relationship_reference)
        reference = card.performance_evidence_reference
        self.assertIsNotNone(reference)
        assert reference is not None
        self.assertEqual(reference.snapshot_package_identity, built.accepted.package_id)
        self.assertEqual(reference.logical_dataset_role, ROLE_SUPPLIER_PERFORMANCE)

    def test_g7_capability_unavailable_fails_closed_without_blocking_upstream(self) -> None:
        """An unprovided supplier-side evidence role fails that capability closed only."""

        built = self.build_chain(name="g7")
        result = self.pipeline(built)

        self.assertTrue(result.accepted)
        self.assertTrue(result.supplier_risk_input.capability_issues)
        self.assertFalse(result.supplier_risk.capability_available)
        self.assertEqual(result.supplier_risk.cards, ())
        for name, _rule in PIPELINE_STAGES:
            self.assertTrue(result.stage(name).entered)

        recommendation = result.procurement_recommendation.for_family(PLANT, DEMAND)
        self.assertIsNotNone(recommendation)
        assert recommendation is not None
        self.assertTrue(recommendation.has_numeric_result)

    def test_g8_valid_absence_stays_distinct_from_data_incomplete(self) -> None:
        """A never-short family is a valid absence; a missing policy input is not."""

        absence = self.pipeline(
            self.build_chain(demands=((DEMAND, "10", D2),), name="g8-absence")
        )
        self.assertEqual(
            absence.procurement_policy_input.valid_absence_grains, ((PLANT, DEMAND),)
        )
        self.assertTrue(
            absence.procurement_recommendation.is_valid_absence(PLANT, DEMAND)
        )
        self.assertIsNone(absence.procurement_recommendation.for_family(PLANT, DEMAND))
        self.assertTrue(absence.supplier_risk.is_valid_absence(PLANT, DEMAND))
        self.assertEqual(absence.supplier_risk.cards, ())

        incomplete = self.pipeline(self.build_chain(moq_policies=(), name="g8-incomplete"))
        item = incomplete.procurement_recommendation.for_family(PLANT, DEMAND)
        self.assertIsNotNone(item)
        assert item is not None
        self.assertTrue(item.data_incomplete)
        self.assertEqual(item.outcome, PROCUREMENT_RECOMMENDATION_UNRESOLVED)
        self.assertFalse(
            incomplete.procurement_recommendation.is_valid_absence(PLANT, DEMAND)
        )
        self.assertEqual(incomplete.procurement_recommendation.valid_absence_grains, ())
        self.assertFalse(incomplete.supplier_risk.is_valid_absence(PLANT, DEMAND))

    def test_g9_plant_isolation_never_borrows_another_plants_answer(self) -> None:
        """Two Plants of one material keep their own grains, quantities and policy answers."""

        built = self.build_chain(
            supplier_relationships=(relationship_record(),),
            supplier_performances=(performance_record(),),
            extra_plant_families=((OTHER_PLANT, DEMAND, "130", D2),),
            name="g9",
        )
        result = self.pipeline(built)

        primary = result.procurement_recommendation.for_family(PLANT, DEMAND)
        other = result.procurement_recommendation.for_family(OTHER_PLANT, DEMAND)
        self.assertIsNotNone(primary)
        self.assertIsNotNone(other)
        assert primary is not None and other is not None
        self.assertNotEqual(primary.plant_id, other.plant_id)

        # Each Plant's shortage grain is its own: one material under two Plants never shares a
        # running total, and one Plant's policy answer never answers for the other.
        primary_grain = result.shortage.for_grain(PLANT, DEMAND, D2)
        other_grain = result.shortage.for_grain(OTHER_PLANT, DEMAND, D2)
        self.assertIsNotNone(primary_grain)
        self.assertIsNotNone(other_grain)
        assert primary_grain is not None and other_grain is not None
        self.assertIsNot(primary_grain, other_grain)
        self.assertEqual(primary_grain.shortage_qty, Fraction(30, 1))
        self.assertEqual(other_grain.shortage_qty, Fraction(30, 1))
        self.assertEqual(primary_grain.classification, other_grain.classification)

        self.assertTrue(primary.has_numeric_result)
        self.assertEqual(primary.applicable_moq.text(), "100")
        self.assertTrue(other.data_incomplete)
        self.assertIsNone(other.applicable_moq)
        self.assertIsNotNone(other.root_condition)
        self.assertIsNotNone(other.policy_root_condition)

        # Both Plants keep their own evaluation context and their own card.
        primary_card = result.supplier_risk.card_for(PLANT, SUPPLIER, DEMAND)
        other_card = result.supplier_risk.card_for(OTHER_PLANT, SUPPLIER, DEMAND)
        self.assertIsNotNone(primary_card)
        self.assertIsNotNone(other_card)
        assert primary_card is not None and other_card is not None
        self.assertIsNot(primary_card, other_card)
        self.assertEqual(primary_card.evaluation_context, (PLANT, DEMAND, SUPPLIER))
        self.assertEqual(other_card.evaluation_context, (OTHER_PLANT, DEMAND, SUPPLIER))
        self.assertEqual(primary_card.recommendation_need_date, D2)
        self.assertEqual(other_card.recommendation_need_date, D2)
        self.assertEqual(len(result.supplier_risk.cards), 2)

    def test_g10_supplier_isolation_keeps_two_cards_of_one_material(self) -> None:
        """Two suppliers of one material keep two independent evaluation contexts."""

        built = self.build_chain(
            supplier_relationships=(
                relationship_record(SUPPLIER),
                relationship_record(SUPPLIER_B),
            ),
            supplier_performances=(
                performance_record(SUPPLIER),
                performance_record(SUPPLIER_B),
            ),
            name="g10",
        )
        result = self.pipeline(built)

        cards_a = result.supplier_risk.cards_for(SUPPLIER, DEMAND)
        cards_b = result.supplier_risk.cards_for(SUPPLIER_B, DEMAND)
        self.assertEqual(len(cards_a), 1)
        self.assertEqual(len(cards_b), 1)
        self.assertEqual(cards_a[0].grain, (SUPPLIER, DEMAND))
        self.assertEqual(cards_b[0].grain, (SUPPLIER_B, DEMAND))
        self.assertEqual(cards_a[0].plant_id, cards_b[0].plant_id)
        self.assertEqual(cards_a[0].evaluation_context, (PLANT, DEMAND, SUPPLIER))
        self.assertEqual(cards_a[0].recommendation_need_date, cards_b[0].recommendation_need_date)
        self.assertEqual(len(result.supplier_risk.cards), 2)

    def test_g11_a_rejected_package_enters_no_downstream_stage(self) -> None:
        """Without an accepted package there is no Analysis Run and no rule stage."""

        boundary = self.boundary / "g11"
        built = build_package(
            boundary / "rejected",
            PackageSpec(
                datasets=[
                    DatasetSpec(
                        records=[
                            {
                                "plant_id": PLANT,
                                "material_code": DEMAND,
                                "required_date": D2,
                                "ProductionQty": "1",
                            }
                        ],
                        integrity_evidence="0" * 64,
                    )
                ]
            ),
            boundary_root=boundary,
        )
        result = run_first_tranche_pipeline_from_paths(
            built.root,
            boundary,
            PhaseAHandoff(analysis_run_id="RUN-1", analysis_date="2026-10-01"),
        )

        self.assertFalse(result.accepted)
        self.assertIsNone(result.import_report.accepted_package)
        self.assertIsNone(result.analysis_run)
        self.assertTrue(result.stage(STAGE_SNAPSHOT_LOADER).entered)
        for entry in result.stages[1:]:
            self.assertFalse(entry.entered, msg=entry.name)
            self.assertEqual(entry.note, LAYER1_NOT_ACCEPTED_REASON, msg=entry.name)
        for name, stage_result in self.stage_results(result).items():
            if name == STAGE_SNAPSHOT_LOADER:
                continue
            self.assertIsNone(stage_result, msg=name)
        self.assertIsNone(result.to_dict()["analysis_run"])

    def test_g12_foreign_analysis_run_results_are_rejected(self) -> None:
        """Cross-run results are rejected by the consuming seams, never silently combined."""

        first = self.pipeline(self.complete_chain("g12-a", analysis_run_id="RUN-A"))
        second = self.pipeline(self.complete_chain("g12-b", analysis_run_id="RUN-B"))

        self.assertNotEqual(first.analysis_run, second.analysis_run)
        self.assertEqual(
            first.procurement_recommendation.analysis_run.analysis_run_id, "RUN-A"
        )
        self.assertEqual(
            second.procurement_recommendation.analysis_run.analysis_run_id, "RUN-B"
        )

        with self.assertRaises(AnalysisRunBindingError) as caught:
            compute_shortage(
                first.construction,
                first.requirements,
                first.inbounds,
                first.inventory,
                second.substitutes,
            )
        self.assertTrue(caught.exception.mismatch)

        with self.assertRaises(AnalysisRunBindingError):
            compute_procurement_recommendation(
                first.construction, first.shortage, second.procurement_policy_input
            )

        with self.assertRaises(AnalysisRunBindingError):
            compute_supplier_risk_input(
                first.construction,
                second.procurement_recommendation,
                accepted=first.import_report.accepted_package,
            )

    def test_g13_the_module_is_composition_only(self) -> None:
        """The composition mints no literal, reads no evidence and calls only the seams."""

        source = Path(pipeline_module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)

        forbidden_calls = {
            "open",
            "read_text",
            "read_bytes",
            "readlines",
            "listdir",
            "walk",
            "glob",
            "iglob",
            "scandir",
        }
        forbidden_names = {
            "json",
            "Decimal",
            "float",
            "round",
            "quantize",
            "Fraction",
            "eval",
            "exec",
            "compile",
        }
        forbidden_import_prefixes = (
            "CATEGORY_",
            "REASON_",
            "CLASSIFICATION_",
            "ROOT_",
            "BASIS_",
            "ELIGIBILITY_",
            "CONSERVATION_",
            "THRESHOLD",
        )

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.level == 1:
                    self.assertIn(node.module, ALLOWED_SIBLING_MODULES, msg=str(node.module))
                else:
                    self.assertEqual(node.level, 0, msg=f"unexpected relative import level")
                    self.assertIn(node.module, ALLOWED_STDLIB_MODULES, msg=str(node.module))
                for alias in node.names:
                    for prefix in forbidden_import_prefixes:
                        self.assertFalse(
                            alias.name.startswith(prefix),
                            msg=f"business literal imported: {alias.name}",
                        )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertIn(
                        alias.name.split(".")[0],
                        ALLOWED_STDLIB_MODULES,
                        msg=f"unexpected module import: {alias.name}",
                    )
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                called = node.func.id
                if called.startswith(("compute_", "construct_", "validate_", "load_")):
                    self.assertIn(
                        called,
                        REGISTERED_ENTRY_POINTS,
                        msg=f"unregistered entry point called: {called}",
                    )
                self.assertNotIn(called, forbidden_calls)
                self.assertNotIn(called, forbidden_names)
            if isinstance(node, ast.Attribute):
                self.assertNotIn(node.attr, forbidden_calls)
                self.assertNotIn(node.attr, forbidden_names)
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                self.assertNotIn(
                    node.value,
                    FORBIDDEN_BUSINESS_LITERALS,
                    msg=f"business literal minted: {node.value}",
                )

        built = self.complete_chain("g13")
        result = self.pipeline(built)
        for entry in result.stages:
            self.assertEqual(
                set(entry.to_dict()), {"name", "rule_id", "entered", "note"}
            )
        self.assertEqual(
            set(result.to_dict()),
            {
                "accepted",
                "accepted_package_id",
                "accepted_content_view_digest",
                "analysis_run",
                "stages",
                "import",
                "layer2",
                "construction",
                "requirements",
                "inventory",
                "inbounds",
                "substitutes",
                "shortage",
                "procurement_policy_input",
                "procurement_recommendation",
                "supplier_risk_input",
                "supplier_risk",
            },
        )

    def test_g14_the_stage_table_carries_the_registered_rule_ids(self) -> None:
        """The composition order restates the registered rule ids and mints none."""

        self.assertEqual(
            [rule for _name, rule in PIPELINE_STAGES],
            [
                None,
                None,
                None,
                RULE_ID,
                INVENTORY_RULE_ID,
                INBOUND_RULE_ID,
                SUBSTITUTE_RULE_ID,
                SHORTAGE_RULE_ID,
                PROCUREMENT_POLICY_INPUT_STAGE,
                PROCUREMENT_RECOMMENDATION_RULE_ID,
                SUPPLIER_RISK_INPUT_STAGE,
                SUPPLIER_RISK_STAGE,
            ],
        )
        self.assertEqual(
            [name for name, _rule in PIPELINE_STAGES],
            [
                STAGE_SNAPSHOT_LOADER,
                STAGE_LAYER2,
                STAGE_CANONICAL_OBJECTS,
                STAGE_REQUIREMENT,
                STAGE_INVENTORY,
                STAGE_INBOUND,
                STAGE_SUBSTITUTE,
                STAGE_SHORTAGE,
                STAGE_PROCUREMENT_POLICY_INPUT,
                STAGE_PROCUREMENT_RECOMMENDATION,
                STAGE_SUPPLIER_RISK_INPUT_SEAM,
                STAGE_SUPPLIER_RISK_EVIDENCE,
            ],
        )
        self.assertEqual(len({name for name, _rule in PIPELINE_STAGES}), 12)
        self.assertEqual(
            run_first_tranche_pipeline.__module__,
            "snapshot_loader.first_tranche_pipeline",
        )


if __name__ == "__main__":  # pragma: no cover - manual run entry point
    unittest.main()
