"""Phase B procurement policy input resolution (``A′``, Human Decision ``APPROVED``).

Covers the registered Phase B seam that supplies `ApplicableMOQ` to a downstream
`BR-PROCUREMENT-001`: the owner grain `plant_id + material_code + RecommendationNeedDate` built from
the **existing** shortage-side `FirstShortageDate` handoff, the exactly-one-applicable-or-unresolved
resolution, the `§4.4.67` root conditions, the valid-absence boundary, the provenance binding and the
out-of-scope guard (no procurement quantity is computed here).

The fixtures reuse the existing end-to-end chain builder (`tests.test_shortage_calculation`), which
also exposes the accepted package the chain was built from.
"""

from __future__ import annotations

import dataclasses
import unittest
from pathlib import Path

from snapshot_loader import (
    AnalysisRunBindingError,
    compute_procurement_policy_input,
)
from snapshot_loader.constants import (
    REASON_INVALID_TYPE,
    REASON_MISSING,
    REASON_OUT_OF_DEFINED_RANGE,
    REASON_SEMANTIC_UNRESOLVED,
)
from tests.test_shortage_calculation import (
    BASIS_SRO,
    D1,
    D2,
    DEMAND,
    OTHER,
    PLANT,
    Demand,
    ShortageRuleTestCase,
    with_provenance,
)

#: The registered **SIMULATED** Phase B applicability basis literals.
BASIS_MOQ_APPLICABLE = "SIMULATED-MOQ-APPLICABLE"
BASIS_MOQ_UNRESOLVED = "SIMULATED-MOQ-UNRESOLVED"
BASIS_MOQ_UNREGISTERED = "SIMULATED-MOQ-UNREGISTERED"

#: The observation a role-12 record registers its applicability under.
MOQ_OBSERVATION = "ApplicableMOQ"


def moq_policy_record(
    material: str = DEMAND,
    *,
    moq: object = "100",
    basis: str | None = BASIS_MOQ_APPLICABLE,
    plant: str = PLANT,
    locator: str | None = None,
    extra_associations: tuple[tuple[str, str], ...] = (),
) -> dict[str, object]:
    """One accepted ``Procurement policy input`` record for one material.

    ``moq`` is the stated ``ApplicableMOQ`` (omit it by passing ``moq=None`` to state no value at
    all).  ``basis`` is the applicability literal the record registers on the ``ApplicableMOQ``
    observation; ``basis=None`` registers no association for that observation at all.
    ``extra_associations`` adds further ``(basis)`` registrations on the same observation, so a test
    can state an ambiguous or unapproved registration.
    """

    record: dict[str, object] = {
        "plant_id": plant,
        "material_code": material,
    }
    if moq is not None:
        record[MOQ_OBSERVATION] = moq
    associations: list[tuple[str, list[str], str | None]] = []
    if basis is not None:
        associations.append(
            (
                MOQ_OBSERVATION,
                [locator or f"SIMULATED-SRC-MOQ-{material}"],
                basis,
            )
        )
    for extra in extra_associations:
        associations.append((MOQ_OBSERVATION, [f"SIMULATED-SRC-MOQ-EXTRA-{extra}"], extra))
    if not associations:  # pragma: no cover - a record always carries its own provenance
        return record
    return with_provenance(record, associations)


class ProcurementPolicyInputTestCase(ShortageRuleTestCase):
    """One shorted family, one never-short family and one unresolved-date family per fixture."""

    def build_chain(
        self,
        *,
        moq_policies: tuple[dict[str, object], ...] = (),
        name: str,
        include_valid_absence: bool = True,
        include_unresolved: bool = False,
        analysis_run_id: str = "RUN-1",
        package_id: str = "SIMULATED-PKG-0001",
    ):
        demand = [Demand(DEMAND, DEMAND, "110", D2)]
        inventory = {DEMAND: "100"}
        safety_stock = {DEMAND: "5"}
        targets: list[tuple[object, object, object]] = [(DEMAND, D2, "APPROVED")]
        if include_valid_absence:
            demand.append(Demand(OTHER, OTHER, "10", D2))
            inventory[OTHER] = "100"
            safety_stock[OTHER] = "5"
        if include_unresolved:
            demand.append(Demand("M7", "M7", "10", D1))
            demand.append(Demand("M7", "M7", "10", D2))
            inventory["M7"] = "100"
            safety_stock["M7"] = "5"
            targets.append(("M7", D1, "APPROVED"))
            targets.append(("M7", D2, "UNRESOLVED"))
        return self.build(
            demand=tuple(demand),
            inventory=inventory,
            safety_stock=safety_stock,
            targets=tuple(targets),
            moq_policies=moq_policies,
            analysis_run_id=analysis_run_id,
            package_id=package_id,
            name=name,
        )

    def resolve(self, built):
        return compute_procurement_policy_input(
            built.construction, built.shortage, accepted=built.accepted
        )

    def policy_artifact(self, built) -> str:
        """The artifact name of the accepted role-12 dataset of one fixture."""

        for role, artifact in built.accepted.datasets():
            if role == "Procurement policy input":
                return artifact
        raise AssertionError("the fixture carries no Procurement policy input dataset")

    def policy_reference(self, built, ordinal: int = 0) -> str:
        return f"{self.policy_artifact(built)}#{ordinal}"


class ResolutionTests(ProcurementPolicyInputTestCase):
    def test_a1_exactly_one_applicable_record_resolves_the_context(self) -> None:
        built = self.build_chain(
            moq_policies=(moq_policy_record(DEMAND, moq="100"),),
            name="a1-resolved",
        )
        result = self.resolve(built)
        # The owner grain is the shortage-side family plus its per-family FirstShortageDate.
        context = result.for_owner(PLANT, DEMAND, D2)
        assert context is not None
        self.assertTrue(context.resolved)
        self.assertFalse(context.data_incomplete)
        self.assertEqual(context.applicable_moq.text(), "100")
        self.assertEqual(context.applicability_basis, BASIS_MOQ_APPLICABLE)
        self.assertEqual(context.root_condition, None)
        self.assertEqual(context.record_reference, self.policy_reference(built))
        self.assertIsNotNone(context.evidence_reference)
        self.assertEqual(
            context.evidence_reference.logical_dataset_role, "Procurement policy input"
        )
        self.assertEqual(
            context.evidence_reference.stable_source_evidence_locators,
            (f"SIMULATED-SRC-MOQ-{DEMAND}",),
        )
        self.assertEqual(
            context.evidence_reference.mapping_resolution_basis, BASIS_MOQ_APPLICABLE
        )
        self.assertEqual(result.applicable_moq_for(PLANT, DEMAND, D2).text(), "100")
        self.assertEqual(
            result.for_family(PLANT, DEMAND).recommendation_need_date, D2
        )
        self.assertEqual(context.rule_issues, ())
        # The need date is the shortage-side handoff and the shortage quantity of that date stays
        # retrievable for the downstream baseline need.
        shortage_grain = built.shortage.for_grain(PLANT, DEMAND, D2)
        assert shortage_grain is not None
        self.assertEqual(shortage_grain.first_shortage_date, D2)
        self.assertEqual(shortage_grain.shortage_qty, 10)
        self.assertEqual(context.recommendation_need_date, shortage_grain.first_shortage_date)

    def test_a2_an_explicit_zero_is_resolved_and_distinct_from_missing(self) -> None:
        built = self.build_chain(
            moq_policies=(moq_policy_record(DEMAND, moq="0"),),
            name="a2-explicit-zero",
        )
        result = self.resolve(built)
        context = result.for_owner(PLANT, DEMAND, D2)
        assert context is not None
        self.assertTrue(context.resolved)
        self.assertIsNotNone(context.applicable_moq)
        self.assertEqual(context.applicable_moq.text(), "0")
        self.assertFalse(context.applicable_moq.negative)
        self.assertEqual(result.applicable_moq_for(PLANT, DEMAND, D2).text(), "0")
        self.assertEqual(context.rule_issues, ())
        payload = context.to_dict()
        self.assertEqual(payload["ApplicableMOQ"], "0")
        self.assertIsNone(payload["outcome"])
        # Missing value is a completely different result, never a default 0.
        missing = self.build_chain(
            moq_policies=(moq_policy_record(DEMAND, moq=None),),
            name="a2-missing-not-zero",
        )
        missing_context = self.resolve(missing).for_owner(PLANT, DEMAND, D2)
        assert missing_context is not None
        self.assertTrue(missing_context.data_incomplete)
        self.assertIsNone(missing_context.applicable_moq)

    def test_a3_an_absent_value_is_missing_not_zero(self) -> None:
        built = self.build_chain(
            moq_policies=(moq_policy_record(DEMAND, moq=None),),
            name="a3-missing-value",
        )
        context = self.resolve(built).for_owner(PLANT, DEMAND, D2)
        assert context is not None
        self.assertTrue(context.data_incomplete)
        self.assertEqual(context.root_condition, "MOQ_VALUE_MISSING")
        self.assertIsNone(context.applicable_moq)
        self.assertEqual(len(context.rule_issues), 1)
        issue = context.rule_issues[0]
        self.assertEqual(issue.category, "FIELD_VALUE")
        self.assertEqual(issue.reason, REASON_MISSING)

    def test_a4_a_negative_value_fails_closed_without_clamping(self) -> None:
        built = self.build_chain(
            moq_policies=(moq_policy_record(DEMAND, moq="-5"),),
            name="a4-negative",
        )
        context = self.resolve(built).for_owner(PLANT, DEMAND, D2)
        assert context is not None
        self.assertTrue(context.data_incomplete)
        self.assertEqual(context.root_condition, "MOQ_VALUE_NEGATIVE")
        self.assertIsNone(context.applicable_moq)
        self.assertEqual(context.rule_issues[0].reason, REASON_OUT_OF_DEFINED_RANGE)
        self.assertEqual(context.rule_issues[0].category, "FIELD_VALUE")

    def test_a4b_an_unusable_value_is_not_coerced(self) -> None:
        built = self.build_chain(
            moq_policies=(moq_policy_record(DEMAND, moq="one hundred"),),
            name="a4b-unusable",
        )
        context = self.resolve(built).for_owner(PLANT, DEMAND, D2)
        assert context is not None
        self.assertTrue(context.data_incomplete)
        self.assertEqual(context.root_condition, "MOQ_VALUE_UNUSABLE")
        self.assertEqual(context.rule_issues[0].reason, REASON_INVALID_TYPE)

    def test_a5_two_applicable_records_fail_closed_without_precedence(self) -> None:
        built = self.build_chain(
            moq_policies=(
                moq_policy_record(DEMAND, moq="100"),
                moq_policy_record(DEMAND, moq="50", locator="SIMULATED-SRC-MOQ-ALT"),
            ),
            name="a5-ambiguous",
        )
        context = self.resolve(built).for_owner(PLANT, DEMAND, D2)
        assert context is not None
        self.assertTrue(context.data_incomplete)
        self.assertEqual(context.root_condition, "MOQ_APPLICABILITY_AMBIGUOUS")
        self.assertIsNone(context.applicable_moq)
        self.assertEqual(
            context.rule_issues[0].reason, REASON_SEMANTIC_UNRESOLVED
        )
        self.assertIn("never reconciled", context.rule_issues[0].detail)
        self.assertEqual(
            context.considered_references,
            (self.policy_reference(built, 0), self.policy_reference(built, 1)),
        )

    def test_a6_an_unapproved_registration_fails_closed(self) -> None:
        # One approved applicable record and one whose literal is not approved: the unapproved one
        # could apply to this context, so the resolution can never claim the approved single value.
        built = self.build_chain(
            moq_policies=(
                moq_policy_record(DEMAND, moq="100"),
                moq_policy_record(
                    DEMAND,
                    moq="70",
                    basis=BASIS_MOQ_UNREGISTERED,
                    locator="SIMULATED-SRC-MOQ-UNKNOWN",
                ),
            ),
            name="a6-unapproved-basis",
        )
        context = self.resolve(built).for_owner(PLANT, DEMAND, D2)
        assert context is not None
        self.assertTrue(context.data_incomplete)
        self.assertEqual(context.root_condition, "MOQ_APPLICABILITY_UNRESOLVED")
        self.assertEqual(context.rule_issues[0].reason, REASON_SEMANTIC_UNRESOLVED)
        self.assertEqual(
            context.considered_references,
            (self.policy_reference(built, 0), self.policy_reference(built, 1)),
        )

    def test_a6b_a_record_without_an_applicability_registration_fails_closed(self) -> None:
        built = self.build_chain(
            moq_policies=(moq_policy_record(DEMAND, moq="100", basis=None),),
            name="a6b-no-registration",
        )
        context = self.resolve(built).for_owner(PLANT, DEMAND, D2)
        assert context is not None
        self.assertTrue(context.data_incomplete)
        self.assertEqual(context.root_condition, "MOQ_APPLICABILITY_UNRESOLVED")

    def test_a6c_the_registered_unresolved_basis_is_not_a_value(self) -> None:
        built = self.build_chain(
            moq_policies=(
                moq_policy_record(DEMAND, moq="100", basis=BASIS_MOQ_UNRESOLVED),
            ),
            name="a6c-registered-unresolved",
        )
        context = self.resolve(built).for_owner(PLANT, DEMAND, D2)
        assert context is not None
        self.assertTrue(context.data_incomplete)
        self.assertEqual(context.root_condition, "MOQ_APPLICABILITY_UNRESOLVED")
        self.assertIsNone(context.applicable_moq)

    def test_a7_no_applicable_evidence_is_not_a_legal_zero(self) -> None:
        built = self.build_chain(name="a7-no-evidence")
        context = self.resolve(built).for_owner(PLANT, DEMAND, D2)
        assert context is not None
        self.assertTrue(context.data_incomplete)
        self.assertEqual(context.root_condition, "MOQ_NO_APPLICABLE_EVIDENCE")
        self.assertIsNone(context.applicable_moq)
        self.assertEqual(context.rule_issues[0].reason, REASON_MISSING)

    def test_a7b_evidence_for_another_material_is_not_borrowed(self) -> None:
        built = self.build_chain(
            moq_policies=(moq_policy_record(OTHER, moq="100"),),
            name="a7b-other-material",
        )
        result = self.resolve(built)
        context = result.for_owner(PLANT, DEMAND, D2)
        assert context is not None
        self.assertTrue(context.data_incomplete)
        self.assertEqual(context.root_condition, "MOQ_NO_APPLICABLE_EVIDENCE")
        self.assertEqual(context.considered_references, ())

    def test_a8_a_reliable_never_short_family_is_a_valid_absence(self) -> None:
        built = self.build_chain(
            moq_policies=(moq_policy_record(DEMAND, moq="100"),),
            name="a8-valid-absence",
        )
        result = self.resolve(built)
        self.assertTrue(result.is_valid_absence(PLANT, OTHER))
        self.assertIsNone(result.for_family(PLANT, OTHER))
        self.assertEqual(result.valid_absence_grains, ((PLANT, OTHER),))
        # Valid absence is not a validation failure and never an unresolved policy input.
        self.assertEqual(result.rule_issues, ())
        self.assertEqual(
            [item.to_dict() for item in result.contexts],
            [result.for_family(PLANT, DEMAND).to_dict()],
        )

    def test_a9_an_unresolved_need_date_leaves_the_context_unresolved(self) -> None:
        built = self.build_chain(
            moq_policies=(
                moq_policy_record(DEMAND, moq="100"),
                moq_policy_record("M7", moq="100", locator="SIMULATED-SRC-MOQ-M7"),
            ),
            include_unresolved=True,
            name="a9-need-date-unresolved",
        )
        result = self.resolve(built)
        context = result.for_family(PLANT, "M7")
        assert context is not None
        self.assertIsNone(context.recommendation_need_date)
        self.assertTrue(context.data_incomplete)
        self.assertEqual(context.root_condition, "RECOMMENDATION_NEED_DATE_UNRESOLVED")
        self.assertEqual(context.rule_issues[0].reason, REASON_SEMANTIC_UNRESOLVED)
        # The reliable family in the same result is unaffected.
        self.assertTrue(result.for_family(PLANT, DEMAND).resolved)

    def test_a10_a_foreign_shortage_result_rejects_the_invocation(self) -> None:
        run_a = self.build_chain(
            moq_policies=(moq_policy_record(DEMAND, moq="100"),),
            name="a10-run-a",
        )
        run_b = self.build_chain(
            moq_policies=(moq_policy_record(DEMAND, moq="100"),),
            analysis_run_id="RUN-B",
            package_id="SIMULATED-PKG-0002",
            name="a10-run-b",
        )
        with self.assertRaises(AnalysisRunBindingError) as caught:
            compute_procurement_policy_input(
                run_a.construction, run_b.shortage, accepted=run_a.accepted
            )
        self.assertEqual(caught.exception.issues[0].category, "PROVENANCE")
        self.assertEqual(caught.exception.issues[0].reason, "PROVENANCE_MISMATCH")
        self.assertIn("BR-SHORTAGE-001", caught.exception.issues[0].location)

    def test_a10b_a_foreign_accepted_package_rejects_the_invocation(self) -> None:
        run_a = self.build_chain(
            moq_policies=(moq_policy_record(DEMAND, moq="100"),),
            name="a10b-run-a",
        )
        run_b = self.build_chain(
            moq_policies=(moq_policy_record(DEMAND, moq="100"),),
            package_id="SIMULATED-PKG-0002",
            name="a10b-run-b",
        )
        with self.assertRaises(AnalysisRunBindingError) as caught:
            compute_procurement_policy_input(
                run_a.construction, run_a.shortage, accepted=run_b.accepted
            )
        issue = caught.exception.issues[0]
        self.assertEqual(issue.category, "PROVENANCE")
        self.assertEqual(issue.reason, "PROVENANCE_MISMATCH")
        self.assertIn("accepted package", issue.location)
        self.assertIn("snapshot_package_identity", issue.detail)

    def test_a10c_a_missing_binding_is_unresolved_not_mismatch(self) -> None:
        run_a = self.build_chain(
            moq_policies=(moq_policy_record(DEMAND, moq="100"),),
            name="a10c-run-a",
        )
        unbound = dataclasses.replace(run_a.shortage, analysis_run=None)
        with self.assertRaises(AnalysisRunBindingError) as caught:
            compute_procurement_policy_input(
                run_a.construction, unbound, accepted=run_a.accepted
            )
        self.assertEqual(caught.exception.issues[0].reason, "PROVENANCE_UNRESOLVED")

    def test_a11_the_result_is_deterministic_read_only_and_bound(self) -> None:
        first = self.build_chain(
            moq_policies=(moq_policy_record(DEMAND, moq="100"),),
            name="a11-first",
        )
        second = self.build_chain(
            moq_policies=(moq_policy_record(DEMAND, moq="100"),),
            name="a11-second",
        )
        first_result = self.resolve(first)
        second_result = self.resolve(second)
        self.assertEqual(first_result.to_dict(), second_result.to_dict())
        self.assertIs(first_result.analysis_run, first.construction.analysis_run)
        self.assertTrue(dataclasses.is_dataclass(first_result))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            first_result.contexts = ()  # type: ignore[misc]
        context = first_result.for_owner(PLANT, DEMAND, D2)
        assert context is not None
        with self.assertRaises(dataclasses.FrozenInstanceError):
            context.applicable_moq = None  # type: ignore[misc]

    def test_a12_no_procurement_quantity_is_produced_here(self) -> None:
        import ast

        import snapshot_loader.procurement_policy_input as module

        # The guard is an **identifier** scan, so a docstring may still explain what this seam does
        # not do while no code path, field or parameter may name a procurement quantity.
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
        for forbidden in (
            "RecommendedPurchaseQty",
            "MOQAdjustmentQty",
            "BasePurchaseNeed",
            "PurchaseOrderQty",
            "ApprovedPurchaseQty",
            "recommended_purchase_qty",
            "moq_adjustment_qty",
            "base_purchase_need",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, identifiers)
        for dataclass_type in (
            module.ProcurementPolicyInputContext,
            module.ProcurementPolicyInputResult,
        ):
            fields = {field.name for field in dataclasses.fields(dataclass_type)}
            self.assertFalse(
                fields
                & {
                    "RecommendedPurchaseQty",
                    "MOQAdjustmentQty",
                    "BasePurchaseNeed",
                    "recommended_purchase_qty",
                    "moq_adjustment_qty",
                    "base_purchase_need",
                }
            )

    def test_a12b_phase_a_still_refuses_the_policy_input_channel(self) -> None:
        # The Phase B seam must not have reopened the phase A boundary: phase A still constructs no
        # role-12 object and no procurement context.
        built = self.build_chain(
            moq_policies=(moq_policy_record(DEMAND, moq="100"),),
            name="a12b-phase-a-boundary",
        )
        self.assertEqual(
            built.construction.objects_for("ApplicableMOQ POLICY_INPUT channel"), ()
        )
        states = built.construction.check_states()
        artifact = self.policy_artifact(built)
        self.assertEqual(
            states.get(f"canonicalization.recognized_role:{artifact}#0"), "not_evaluable"
        )

    def test_a1b_the_basis_registry_is_closed_and_exact(self) -> None:
        import snapshot_loader.procurement_policy_input as module

        self.assertEqual(
            {entry.outcome for entry in module.PROCUREMENT_POLICY_INPUT_REGISTRY},
            set(module.PROCUREMENT_POLICY_INPUT_OUTCOMES),
        )
        self.assertEqual(
            module.PROCUREMENT_POLICY_INPUT_BASIS_BY_LITERAL[BASIS_MOQ_APPLICABLE].outcome,
            "applicable",
        )
        # An exact-match registry: a differently cased or padded literal is not approved.
        for literal in ("simulated-moq-applicable", " SIMULATED-MOQ-APPLICABLE"):
            with self.subTest(literal=literal):
                self.assertNotIn(literal, module.PROCUREMENT_POLICY_INPUT_BASIS_BY_LITERAL)
        self.assertEqual(module.PROCUREMENT_POLICY_OBSERVATION, MOQ_OBSERVATION)
        self.assertNotEqual(BASIS_SRO, BASIS_MOQ_APPLICABLE)


if __name__ == "__main__":  # pragma: no cover - direct invocation
    unittest.main()
