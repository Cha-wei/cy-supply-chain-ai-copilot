"""G5-A single-allocation-record multi-association regression (``CB-1′``).

``§4.3.28`` E registers ``provenance_associations`` as an **array**: one source evidence
may produce several canonical outputs, the same evidence locator may appear across
associations, and each association carries its own ``mapping_basis``.  This module proves
that the G5-A seam honours exactly that:

* **one** accepted ``Substitute Allocation`` source record carries several legitimate
  associations, each with its own registered basis;
* several G5-A handoff entries cite that **same** record;
* each entry targets a different resolved ``Production Requirement`` demand context;
* each entry yields its own independent ``RelationOutcomeReference``.

It also pins the boundaries that must not be traded away to achieve that: no copied
allocation record, no Target × Source Cartesian product, no first ／ last wins, no
same-value deduplication, and no outcome taken from the caller.

All fixtures are SIMULATED.
"""

from __future__ import annotations

import unittest

from snapshot_loader import build_effective_demand_contexts, parse_strict_json
from snapshot_loader.canonical_objects import (
    EFFECTIVE_DEMAND_BASIS_REGISTRY,
    RELATION_SOURCE_RESERVATION_OVERLAP,
    RELATION_TARGET_APPLICABILITY,
    EffectiveDemandRelationHandoff,
)
from tests.test_canonical_objects import (
    EVIDENCE_RELATIONSHIP,
    MATERIAL,
    PLANT,
    PRODUCTION_REQUIREMENT,
    CanonicalObjectsTestCase,
    PhaseAHandoff,
    with_provenance,
)

SOURCE_MATERIAL = "M3"

#: Only one evidence locator per relation: the point is that the **same** locator backs
#: several associations of one record.
EVIDENCE_TA = "SIMULATED-SRC-ALLOC-1"
EVIDENCE_SRO = "SIMULATED-SRC-ALLOC-1"

R1, R2 = "2026-10-10", "2026-10-20"
S1, S2 = "2026-10-12", "2026-11-01"

BASIS_TA_APPLICABLE = "SIMULATED-G5A-TA-APPLICABLE"
BASIS_TA_NOT_APPLICABLE = "SIMULATED-G5A-TA-NOT-APPLICABLE"
BASIS_SRO_OVERLAPS = "SIMULATED-G5A-SRO-OVERLAPS"
BASIS_SRO_NO_OVERLAP = "SIMULATED-G5A-SRO-NO-OVERLAP"


def single_allocation_datasets():
    """One allocation record carrying four legitimate associations."""

    allocation = with_provenance(
        {
            "plant_id": PLANT,
            "target_material_code": MATERIAL,
            "substitute_material_code": SOURCE_MATERIAL,
            "AllocatedSubstituteQty": "60",
        },
        [
            ("target_material_code", [EVIDENCE_TA], BASIS_TA_APPLICABLE),
            ("target_material_code", [EVIDENCE_TA], BASIS_TA_NOT_APPLICABLE),
            ("substitute_material_code", [EVIDENCE_SRO], BASIS_SRO_OVERLAPS),
            ("substitute_material_code", [EVIDENCE_SRO], BASIS_SRO_NO_OVERLAP),
        ],
    )
    relationship = with_provenance(
        {
            "plant_id": PLANT,
            "target_material_code": MATERIAL,
            "substitute_material_code": SOURCE_MATERIAL,
            "substitution_ratio": "1.0",
            "approval_status": "APPROVED",
        },
        [("approval_status", [EVIDENCE_RELATIONSHIP], None)],
    )
    return [
        ("Substitute Allocation", [allocation]),
        ("Substitute Relationship", [relationship]),
        (
            "Production Requirement",
            [
                PRODUCTION_REQUIREMENT(required_date=R1),
                PRODUCTION_REQUIREMENT(required_date=R2),
                PRODUCTION_REQUIREMENT(
                    material_code=SOURCE_MATERIAL, required_date=S1
                ),
                PRODUCTION_REQUIREMENT(
                    material_code=SOURCE_MATERIAL, required_date=S2
                ),
            ],
        ),
    ]


class SingleAllocationRecordTests(CanonicalObjectsTestCase):
    """One allocation record, several registrations, several independent outcomes."""

    def _accepted(self, name: str):
        _built, accepted = self.accepted(single_allocation_datasets(), name=name)
        return accepted

    def _allocation_record_count(self, accepted) -> int:
        raw = accepted.records_for("0.json")
        assert raw is not None
        payload = parse_strict_json(raw, source="0.json")
        assert isinstance(payload, list)
        return len(payload)

    def _entry(
        self,
        accepted,
        *,
        relation: str,
        basis: str,
        context_ordinal: int,
    ) -> EffectiveDemandRelationHandoff:
        locator = EVIDENCE_TA if relation == RELATION_TARGET_APPLICABILITY else EVIDENCE_SRO
        return EffectiveDemandRelationHandoff(
            source_substitute_material=SOURCE_MATERIAL,
            target_material=MATERIAL,
            relation=relation,
            evidence=self.citation(
                accepted,
                role="Substitute Allocation",
                artifact="0.json",
                ordinal=0,
                locator=locator,
            ),
            mapping_basis=basis,
            context_citation=self.citation(
                accepted,
                role="Production Requirement",
                artifact="2.json",
                ordinal=context_ordinal,
                locator="SIMULATED-SRC-REQ-1",
            ),
        )

    def _handoff(self, accepted, entries) -> PhaseAHandoff:
        return PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-10-01",
            effective_demand=tuple(entries),
        )

    def _outcomes(self, contexts):
        return {
            (
                item.relation_outcome.relation,
                {
                    prop.name: prop.value
                    for prop in item.relation_outcome.context.grain
                }["required_date"],
            ): item.relation_outcome.outcome
            for item in contexts
        }

    def test_one_allocation_record_carries_all_four_relation_outcomes(self) -> None:
        accepted = self._accepted("g5a-single-allocation")
        self.assertEqual(
            self._allocation_record_count(accepted),
            1,
            msg="the regression must not rely on a copied allocation record",
        )
        handoff = self._handoff(
            accepted,
            (
                self._entry(
                    accepted,
                    relation=RELATION_TARGET_APPLICABILITY,
                    basis=BASIS_TA_APPLICABLE,
                    context_ordinal=0,
                ),
                self._entry(
                    accepted,
                    relation=RELATION_TARGET_APPLICABILITY,
                    basis=BASIS_TA_NOT_APPLICABLE,
                    context_ordinal=1,
                ),
                self._entry(
                    accepted,
                    relation=RELATION_SOURCE_RESERVATION_OVERLAP,
                    basis=BASIS_SRO_OVERLAPS,
                    context_ordinal=2,
                ),
                self._entry(
                    accepted,
                    relation=RELATION_SOURCE_RESERVATION_OVERLAP,
                    basis=BASIS_SRO_NO_OVERLAP,
                    context_ordinal=3,
                ),
            ),
        )
        contexts, issues = build_effective_demand_contexts(accepted, handoff)
        self.assertEqual(issues, ())
        self.assertEqual(len(contexts), 4)
        # Every outcome cites the very same accepted allocation record.
        self.assertEqual(
            {item.record_reference for item in contexts}, {"0.json#0"}
        )
        self.assertEqual(
            self._outcomes(contexts),
            {
                (RELATION_TARGET_APPLICABILITY, R1): "applicable",
                (RELATION_TARGET_APPLICABILITY, R2): "not applicable",
                (RELATION_SOURCE_RESERVATION_OVERLAP, S1): "overlaps",
                (RELATION_SOURCE_RESERVATION_OVERLAP, S2): "does not overlap",
            },
        )
        # Each outcome carries its own basis and its own independent context reference.
        self.assertEqual(
            {
                (
                    item.relation_outcome.mapping_basis,
                    item.relation_outcome.context.record_reference,
                )
                for item in contexts
            },
            {
                (BASIS_TA_APPLICABLE, "SIMULATED-PKG-0001|Production Requirement|2.json|0"),
                (
                    BASIS_TA_NOT_APPLICABLE,
                    "SIMULATED-PKG-0001|Production Requirement|2.json|1",
                ),
                (BASIS_SRO_OVERLAPS, "SIMULATED-PKG-0001|Production Requirement|2.json|2"),
                (
                    BASIS_SRO_NO_OVERLAP,
                    "SIMULATED-PKG-0001|Production Requirement|2.json|3",
                ),
            },
        )

    def test_same_allocation_resolves_opposite_target_outcomes(self) -> None:
        accepted = self._accepted("g5a-single-allocation-target")
        handoff = self._handoff(
            accepted,
            (
                self._entry(
                    accepted,
                    relation=RELATION_TARGET_APPLICABILITY,
                    basis=BASIS_TA_APPLICABLE,
                    context_ordinal=0,
                ),
                self._entry(
                    accepted,
                    relation=RELATION_TARGET_APPLICABILITY,
                    basis=BASIS_TA_NOT_APPLICABLE,
                    context_ordinal=1,
                ),
            ),
        )
        contexts, issues = build_effective_demand_contexts(accepted, handoff)
        self.assertEqual(
            self._outcomes(contexts),
            {
                (RELATION_TARGET_APPLICABILITY, R1): "applicable",
                (RELATION_TARGET_APPLICABILITY, R2): "not applicable",
            },
        )
        # The other relation carries no evidence for this pair, so only that relation's
        # completeness finding may appear -- nothing about the resolved outcomes.
        for issue in issues:
            self.assertIn("Source Reservation Overlap", issue.detail)

    def test_same_allocation_resolves_opposite_source_outcomes(self) -> None:
        accepted = self._accepted("g5a-single-allocation-source")
        handoff = self._handoff(
            accepted,
            (
                self._entry(
                    accepted,
                    relation=RELATION_SOURCE_RESERVATION_OVERLAP,
                    basis=BASIS_SRO_OVERLAPS,
                    context_ordinal=2,
                ),
                self._entry(
                    accepted,
                    relation=RELATION_SOURCE_RESERVATION_OVERLAP,
                    basis=BASIS_SRO_NO_OVERLAP,
                    context_ordinal=3,
                ),
            ),
        )
        contexts, issues = build_effective_demand_contexts(accepted, handoff)
        self.assertEqual(
            self._outcomes(contexts),
            {
                (RELATION_SOURCE_RESERVATION_OVERLAP, S1): "overlaps",
                (RELATION_SOURCE_RESERVATION_OVERLAP, S2): "does not overlap",
            },
        )
        # Target Applicability carries no evidence in this scenario, so any finding must be
        # about that missing relation only.
        for issue in issues:
            self.assertIn("Target Applicability", issue.detail)

    def test_one_record_does_not_create_a_target_source_product(self) -> None:
        accepted = self._accepted("g5a-single-allocation-cartesian")
        handoff = self._handoff(
            accepted,
            (
                self._entry(
                    accepted,
                    relation=RELATION_TARGET_APPLICABILITY,
                    basis=BASIS_TA_APPLICABLE,
                    context_ordinal=0,
                ),
                self._entry(
                    accepted,
                    relation=RELATION_TARGET_APPLICABILITY,
                    basis=BASIS_TA_NOT_APPLICABLE,
                    context_ordinal=1,
                ),
                self._entry(
                    accepted,
                    relation=RELATION_SOURCE_RESERVATION_OVERLAP,
                    basis=BASIS_SRO_OVERLAPS,
                    context_ordinal=2,
                ),
                self._entry(
                    accepted,
                    relation=RELATION_SOURCE_RESERVATION_OVERLAP,
                    basis=BASIS_SRO_NO_OVERLAP,
                    context_ordinal=3,
                ),
            ),
        )
        contexts, _issues = build_effective_demand_contexts(accepted, handoff)
        # 2 target + 2 source: never 4 combinations, never 8.
        self.assertEqual(len(contexts), 4)
        target_dates = {
            {prop.name: prop.value for prop in item.relation_outcome.context.grain}[
                "required_date"
            ]
            for item in contexts
            if item.relation_outcome.relation == RELATION_TARGET_APPLICABILITY
        }
        source_dates = {
            {prop.name: prop.value for prop in item.relation_outcome.context.grain}[
                "required_date"
            ]
            for item in contexts
            if item.relation_outcome.relation == RELATION_SOURCE_RESERVATION_OVERLAP
        }
        self.assertEqual(target_dates, {R1, R2})
        self.assertEqual(source_dates, {S1, S2})
        for item in contexts:
            material = {
                prop.name: prop.value
                for prop in item.relation_outcome.context.grain
            }["material_code"]
            if item.relation_outcome.relation == RELATION_TARGET_APPLICABILITY:
                self.assertEqual(material, MATERIAL)
            else:
                self.assertEqual(material, SOURCE_MATERIAL)

    def test_a_caller_cannot_name_an_unregistered_basis(self) -> None:
        accepted = self._accepted("g5a-single-allocation-unregistered")
        handoff = self._handoff(
            accepted,
            (
                self._entry(
                    accepted,
                    relation=RELATION_TARGET_APPLICABILITY,
                    basis="SIMULATED-NOT-APPROVED",
                    context_ordinal=0,
                ),
            ),
        )
        contexts, issues = build_effective_demand_contexts(accepted, handoff)
        self.assertEqual(contexts, ())
        self.assertTrue(issues)
        self.assertTrue(all(issue.reason == "SEMANTIC_UNRESOLVED" for issue in issues))

    def test_duplicate_identical_registration_is_not_resolved_by_precedence(self) -> None:
        datasets = single_allocation_datasets()
        duplicated = with_provenance(
            {
                "plant_id": PLANT,
                "target_material_code": MATERIAL,
                "substitute_material_code": SOURCE_MATERIAL,
                "AllocatedSubstituteQty": "60",
            },
            [
                ("target_material_code", [EVIDENCE_TA], BASIS_TA_APPLICABLE),
                ("target_material_code", [EVIDENCE_TA], BASIS_TA_APPLICABLE),
            ],
        )
        datasets[0] = ("Substitute Allocation", [duplicated])
        _built, accepted = self.accepted(datasets, name="g5a-single-allocation-dup")
        handoff = self._handoff(
            accepted,
            (
                self._entry(
                    accepted,
                    relation=RELATION_TARGET_APPLICABILITY,
                    basis=BASIS_TA_APPLICABLE,
                    context_ordinal=0,
                ),
            ),
        )
        contexts, issues = build_effective_demand_contexts(accepted, handoff)
        self.assertEqual(contexts, ())
        self.assertTrue(
            any(
                "same mapping_basis" in issue.detail
                or "exactly one registration" in issue.detail
                for issue in issues
            )
        )

    def test_selection_never_borrows_another_relations_observation(self) -> None:
        # The source-side literal is registered, but only on the source observation; a
        # Target Applicability entry naming it must not be served by that association.
        accepted = self._accepted("g5a-single-allocation-cross-relation")
        handoff = self._handoff(
            accepted,
            (
                self._entry(
                    accepted,
                    relation=RELATION_TARGET_APPLICABILITY,
                    basis=BASIS_SRO_OVERLAPS,
                    context_ordinal=0,
                ),
            ),
        )
        contexts, issues = build_effective_demand_contexts(accepted, handoff)
        self.assertEqual(contexts, ())
        self.assertTrue(issues)
        self.assertTrue(
            any("observation 'target_material_code'" in issue.detail for issue in issues)
        )

    def test_registry_literals_used_here_are_the_registered_ones(self) -> None:
        registered = {(rule.relation, rule.basis) for rule in EFFECTIVE_DEMAND_BASIS_REGISTRY}
        for relation, basis in (
            (RELATION_TARGET_APPLICABILITY, BASIS_TA_APPLICABLE),
            (RELATION_TARGET_APPLICABILITY, BASIS_TA_NOT_APPLICABLE),
            (RELATION_SOURCE_RESERVATION_OVERLAP, BASIS_SRO_OVERLAPS),
            (RELATION_SOURCE_RESERVATION_OVERLAP, BASIS_SRO_NO_OVERLAP),
        ):
            self.assertIn((relation, basis), registered)

    # --- blocker 1: role 8 (Substitute Allocation) is the only basis host -------------

    def test_role_7_registered_basis_is_never_a_g5a_outcome_basis(self) -> None:
        """A ``Substitute Relationship`` that registers a valid G5-A literal stays unresolved."""

        datasets = single_allocation_datasets()
        # A Substitute Relationship record that legitimately registers a G5-A literal and a
        # valid evidence locator -- and must still never serve as the outcome basis.
        relationship = with_provenance(
            {
                "plant_id": PLANT,
                "target_material_code": MATERIAL,
                "substitute_material_code": SOURCE_MATERIAL,
                "substitution_ratio": "1.0",
                "approval_status": "APPROVED",
            },
            [
                ("target_material_code", [EVIDENCE_TA], BASIS_TA_APPLICABLE),
                ("approval_status", [EVIDENCE_RELATIONSHIP], None),
            ],
        )
        datasets[1] = ("Substitute Relationship", [relationship])
        _built, accepted = self.accepted(datasets, name="g5a-role7-basis-host")

        entry = EffectiveDemandRelationHandoff(
            source_substitute_material=SOURCE_MATERIAL,
            target_material=MATERIAL,
            relation=RELATION_TARGET_APPLICABILITY,
            evidence=self.citation(
                accepted,
                role="Substitute Relationship",
                artifact="1.json",
                ordinal=0,
                locator=EVIDENCE_TA,
            ),
            mapping_basis=BASIS_TA_APPLICABLE,
            context_citation=self.citation(
                accepted,
                role="Production Requirement",
                artifact="2.json",
                ordinal=0,
                locator="SIMULATED-SRC-REQ-1",
            ),
        )
        contexts, issues = build_effective_demand_contexts(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-10-01",
                effective_demand=(entry,),
            ),
        )
        self.assertEqual(contexts, ())
        self.assertTrue(issues)
        self.assertTrue(all(issue.reason == "SEMANTIC_UNRESOLVED" for issue in issues))
        self.assertTrue(
            any("Substitute Allocation" in issue.detail for issue in issues),
            msg="the finding must name the role 8 host requirement",
        )

    # --- blocker 2: the accepted allocation record is the only identity ---------------

    def _mismatch_case(self, *, source, target, name):
        accepted = self._accepted(name)
        entry = EffectiveDemandRelationHandoff(
            source_substitute_material=source,
            target_material=target,
            relation=RELATION_TARGET_APPLICABILITY,
            evidence=self.citation(
                accepted,
                role="Substitute Allocation",
                artifact="0.json",
                ordinal=0,
                locator=EVIDENCE_TA,
            ),
            mapping_basis=BASIS_TA_APPLICABLE,
            context_citation=self.citation(
                accepted,
                role="Production Requirement",
                artifact="2.json",
                ordinal=0,
                locator="SIMULATED-SRC-REQ-1",
            ),
        )
        return build_effective_demand_contexts(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-10-01",
                effective_demand=(entry,),
            ),
        )

    def test_caller_source_material_mismatch_is_unresolved(self) -> None:
        contexts, issues = self._mismatch_case(
            source="M9", target=MATERIAL, name="g5a-caller-source-mismatch"
        )
        self.assertEqual(contexts, ())
        self.assertTrue(issues)
        self.assertTrue(
            any(
                "does not equal the accepted Substitute Allocation record" in issue.detail
                for issue in issues
            )
        )

    def test_caller_target_material_mismatch_is_unresolved(self) -> None:
        contexts, issues = self._mismatch_case(
            source=SOURCE_MATERIAL, target="M9", name="g5a-caller-target-mismatch"
        )
        self.assertEqual(contexts, ())
        self.assertTrue(issues)
        self.assertTrue(
            any(
                "does not equal the accepted Substitute Allocation record" in issue.detail
                for issue in issues
            )
        )

    def test_non_hashable_caller_material_never_crashes_on_the_normal_path(self) -> None:
        """Blocker 6: a non-hashable caller pair with a valid registered claim.

        ``CB-1′``'s binding key is ``allocation record ＋ relation ＋ resolved demand
        context``, so the caller's representation never becomes a key.  The claim cannot be
        exact-bound to the accepted record here, so the relation fails safe instead of
        raising ``TypeError``, and the caller object is left untouched.
        """

        source: list[object] = []
        target: dict[str, object] = {}
        contexts, issues = self._mismatch_case(
            source=source, target=target, name="g5a-non-hashable-normal-path"
        )
        self.assertEqual(contexts, ())
        self.assertTrue(issues)
        self.assertTrue(
            any(
                "does not equal the accepted Substitute Allocation record" in issue.detail
                for issue in issues
            )
        )
        # Never converted, stringified or widened, and never used as a key.
        self.assertEqual(source, [])
        self.assertEqual(target, {})

    def test_non_hashable_source_with_valid_registration_and_citation(self) -> None:
        """Blocker 6 (Issue #146 R-3): ``source_substitute_material = []`` only."""

        source: list[object] = []
        contexts, issues = self._mismatch_case(
            source=source, target=MATERIAL, name="g5a-non-hashable-source"
        )
        self.assertEqual(contexts, ())
        self.assertTrue(issues)
        # evidence ／ basis ／ citation validation all ran before the identity gate: the
        # finding is the claim-vs-record mismatch, which is only reachable after
        # verification, the role gate and the basis gate all succeeded.
        self.assertTrue(
            any(
                "does not equal the accepted Substitute Allocation record" in issue.detail
                for issue in issues
            )
        )
        self.assertEqual(source, [])

    def test_plant_a_allocation_is_never_bound_to_a_plant_b_context(self) -> None:
        """Blocker 2: the citation's Plant must equal the accepted allocation's Plant."""

        datasets = single_allocation_datasets()
        datasets[2] = (
            "Production Requirement",
            [
                PRODUCTION_REQUIREMENT(plant_id="P2", required_date=R1),
                PRODUCTION_REQUIREMENT(required_date=R2),
                PRODUCTION_REQUIREMENT(
                    material_code=SOURCE_MATERIAL, required_date=S1
                ),
                PRODUCTION_REQUIREMENT(
                    material_code=SOURCE_MATERIAL, required_date=S2
                ),
            ],
        )
        _built, accepted = self.accepted(datasets, name="g5a-cross-plant")
        entry = EffectiveDemandRelationHandoff(
            source_substitute_material=SOURCE_MATERIAL,
            target_material=MATERIAL,
            relation=RELATION_TARGET_APPLICABILITY,
            evidence=self.citation(
                accepted,
                role="Substitute Allocation",
                artifact="0.json",
                ordinal=0,
                locator=EVIDENCE_TA,
            ),
            mapping_basis=BASIS_TA_APPLICABLE,
            context_citation=self.citation(
                accepted,
                role="Production Requirement",
                artifact="2.json",
                ordinal=0,
                locator="SIMULATED-SRC-REQ-1",
            ),
        )
        contexts, issues = build_effective_demand_contexts(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-10-01",
                effective_demand=(entry,),
            ),
        )
        self.assertEqual(contexts, ())
        self.assertTrue(issues)
        self.assertTrue(
            any(
                "plant" in issue.detail and "P2" in issue.detail for issue in issues
            ),
            msg="the finding must name the cross-Plant mismatch",
        )

    # --- blocker 3: G5-A mapping evidence requires an exact locator -------------------

    def test_missing_evidence_locator_is_unresolved_even_with_a_valid_registration(self) -> None:
        accepted = self._accepted("g5a-missing-locator")
        entry = EffectiveDemandRelationHandoff(
            source_substitute_material=SOURCE_MATERIAL,
            target_material=MATERIAL,
            relation=RELATION_TARGET_APPLICABILITY,
            evidence=self.citation(
                accepted,
                role="Substitute Allocation",
                artifact="0.json",
                ordinal=0,
                locator=None,
            ),
            mapping_basis=BASIS_TA_APPLICABLE,
            context_citation=self.citation(
                accepted,
                role="Production Requirement",
                artifact="2.json",
                ordinal=0,
                locator="SIMULATED-SRC-REQ-1",
            ),
        )
        contexts, issues = build_effective_demand_contexts(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-10-01",
                effective_demand=(entry,),
            ),
        )
        self.assertEqual(contexts, ())
        self.assertTrue(issues)
        self.assertTrue(
            any("evidence locator" in issue.detail for issue in issues),
            msg="the finding must name the required exact locator",
        )

    # --- blocker 4: no public trusted demand-context injection ------------------------

    def test_public_api_exposes_no_trusted_demand_context_parameter(self) -> None:
        """The caller cannot hand in resolved contexts; the seam derives them itself."""

        import inspect

        signature = inspect.signature(build_effective_demand_contexts)
        self.assertEqual(
            set(signature.parameters),
            {"accepted", "handoff", "located"},
            msg=(
                "the public entry point may only accept claims; resolved demand contexts "
                "must be derived from the AcceptedPackage"
            ),
        )
        for forbidden in (
            "production_requirements",
            "demand_contexts",
            "resolved_contexts",
            "contexts",
        ):
            self.assertNotIn(forbidden, signature.parameters)
        with self.assertRaises(TypeError):
            build_effective_demand_contexts(None, None, production_requirements=())  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
