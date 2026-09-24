"""Phase A canonical object construction tests (Issue #124, Phase A only).

Coverage required by Issue #124 Phase A Acceptance Criteria:

* recognized roles / exact role semantics;
* unrecognized role ``not_evaluable``;
* applicability boundary;
* G3-A deterministic ordinal identity;
* duplicate identical inbound records remain distinct;
* G4-A parent binding + mismatch;
* G5-A two independent relations;
* provenance preservation;
* same-AcceptedPackage enforcement;
* no external business-value injection;
* zero preservation;
* null / omission no guessing;
* Decimal / no float semantics;
* no hidden normalization;
* no ``required_quantity``;
* no DERIVED source object;
* MG-2 / accepted-view boundary;
* deterministic repeatability;
* existing Layer-1 / Layer-2 regression (the shared suite).

All fixtures are SIMULATED.
"""

from __future__ import annotations

import copy
import unittest
import uuid
from pathlib import Path

from snapshot_loader import (
    DISPOSITION_UNUSABLE,
    LossRateHandoff,
    PhaseAHandoff,
    SafetyStockHandoff,
    TrustedInputBoundary,
    build_effective_demand_contexts,
    construct_canonical_objects,
    load_package,
    validate_layer2,
)
from snapshot_loader.canonical_objects import (
    ABSENT,
    APPLICABILITY_BY_ROLE,
    CANONICALIZATION_ANALYSIS_RUN,
    CANONICALIZATION_GRAIN_RESOLUTION,
    CANONICALIZATION_HANDOFF_EVIDENCE,
    CANONICALIZATION_ROLES,
    CANONICALIZATION_ROLE_BY_LITERAL,
    CANONICALIZATION_ROLE_RECOGNITION,
    PHASE_A_ROLE_LITERALS,
    ROLE_FOR_TARGET,
    ROLE_INBOUND_SUPPLY,
    BomParentContextHandoff,
    EffectiveDemandRelationHandoff,
    EvidenceReference,
)
from snapshot_loader.constants import (
    EVALUATION_NOT_EVALUABLE,
    EVALUATION_PASSED,
    V02_CANONICAL_RECORD_PROPERTY_SET,
)
from tests.helpers import DatasetSpec, PackageSpec, build_package

SCRATCH_ROOT = Path(__file__).resolve().parents[1] / "build" / "test-scratch"

PLANT = "P1"
MATERIAL = "M1"
COMPONENT = "M2"
REQUIRED_DATE = "2026-02-01"
SNAPSHOT_TIME = "2026-01-31T08:00:00Z"

PRODUCTION_REQUIREMENT_RECORD: dict[str, object] = {
    "plant_id": PLANT,
    "material_code": MATERIAL,
    "required_date": REQUIRED_DATE,
    "ProductionQty": "10",
}

BOM_COMPONENT_RECORD: dict[str, object] = {
    "plant_id": PLANT,
    "required_date": REQUIRED_DATE,
    "material_code": COMPONENT,
    "BOMComponentQty": "2",
}

INBOUND_RECORD: dict[str, object] = {
    "plant_id": PLANT,
    "material_code": MATERIAL,
    "ordered_qty": "10",
    "received_qty": "0",
    "effective_arrival_date": "2026-01-20",
    "inbound_status": "CONFIRMED",
}

DERIVED_LITERALS = (
    "BaseRequirement",
    "GrossRequirement",
    "RecommendedPurchaseQty",
    "Classification",
    "FirstShortageDate",
    "RemainingInboundQty",
)


class CanonicalObjectsTestCase(unittest.TestCase):
    """Shared fixture scaffolding: one accepted package per subtest directory."""

    def setUp(self) -> None:
        self.boundary = SCRATCH_ROOT / f"canonical-{uuid.uuid4().hex}"
        self.boundary.mkdir(parents=True, exist_ok=True)

    def build(
        self,
        datasets: list[tuple[str, list[dict[str, object]]]],
        *,
        name: str | None = None,
        package_id: str = "SIMULATED-PKG-0001",
    ):
        directory = self.boundary / (name or uuid.uuid4().hex[:8])
        specs = [
            DatasetSpec(role=role, artifact=f"{index}.json", records=records)
            for index, (role, records) in enumerate(datasets)
        ]
        built = build_package(
            directory,
            PackageSpec(datasets=specs, package_id=package_id),
            boundary_root=self.boundary,
        )
        report = load_package(
            built.root, trusted_boundary=TrustedInputBoundary(root=self.boundary)
        )
        return built, report

    def accepted(
        self,
        datasets: list[tuple[str, list[dict[str, object]]]],
        *,
        name: str | None = None,
        package_id: str = "SIMULATED-PKG-0001",
    ):
        built, report = self.build(datasets, name=name, package_id=package_id)
        self.assertTrue(
            report.accepted,
            msg=f"fixture package was not accepted: {report.disposition_basis}",
        )
        assert report.accepted_package is not None
        return built, report.accepted_package

    def construct(
        self,
        datasets: list[tuple[str, list[dict[str, object]]]],
        handoff: PhaseAHandoff | None = None,
        *,
        name: str | None = None,
    ):
        _, accepted = self.accepted(datasets, name=name)
        if handoff is None:
            handoff = PhaseAHandoff(analysis_run_id="RUN-1", analysis_date="2026-02-01")
        return construct_canonical_objects(accepted, handoff)

    def evidence(
        self,
        accepted,
        *,
        role: str,
        artifact: str,
        ordinal: int = 0,
        property_name: str | None = None,
        package_id: str | None = None,
    ) -> EvidenceReference:
        locator = f"{artifact}#{ordinal}"
        if property_name is not None:
            locator = f"{locator}.{property_name}"
        return EvidenceReference(
            snapshot_package_identity=package_id or accepted.package_id,
            logical_dataset_role=role,
            stable_source_evidence_locator=locator,
        )

    def states(self, report) -> dict[str, str]:
        return report.check_states()

    def inbound(self, report):
        return {item.record_reference: item for item in report.inbound_records}


class RoleAssignmentTests(CanonicalObjectsTestCase):
    def test_recognized_role_set_is_exactly_the_twelve_registered_literals(self) -> None:
        self.assertEqual(len(CANONICALIZATION_ROLES), 12)
        self.assertEqual(
            [role.literal for role in CANONICALIZATION_ROLES],
            [
                "Plant / Material identity context",
                "Production Requirement",
                "BOM Component",
                "Inventory Snapshot",
                "Configured Safety Stock",
                "Inbound Supply",
                "Substitute Relationship",
                "Substitute Allocation",
                "Supplier identity",
                "Supplier-Material Relationship",
                "Supplier Performance",
                "Procurement policy input",
            ],
        )

    def test_role_twelve_is_registered_for_phase_b_only(self) -> None:
        role = CANONICALIZATION_ROLE_BY_LITERAL["Procurement policy input"]
        self.assertEqual(role.phase, "B")
        self.assertEqual(len(PHASE_A_ROLE_LITERALS), 11)
        self.assertNotIn("Procurement policy input", PHASE_A_ROLE_LITERALS)

    def test_production_requirement_is_assigned_to_its_canonical_target(self) -> None:
        report = self.construct([("Production Requirement", [PRODUCTION_REQUIREMENT_RECORD])])
        objects = report.objects_for("Production Requirement")
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0].canonicalization_role, "Production Requirement")
        self.assertEqual(objects[0].value_of("ProductionQuantity", ABSENT), ABSENT)
        self.assertEqual(objects[0].value_of("ProductionQty"), "10")
        self.assertEqual(
            [prop.name for prop in objects[0].grain],
            ["plant_id", "material_code", "required_date"],
        )

    def test_plant_and_material_identity_context_yields_two_independent_identities(self) -> None:
        report = self.construct(
            [("Plant / Material identity context", [{"plant_id": PLANT, "material_code": MATERIAL}])]
        )
        self.assertEqual(len(report.objects_for("Plant")), 1)
        self.assertEqual(len(report.objects_for("Material")), 1)
        self.assertEqual(
            [prop.name for prop in report.objects_for("Plant")[0].grain], ["plant_id"]
        )

    def test_unrecognized_role_is_not_evaluable_without_issue_or_object(self) -> None:
        report = self.construct(
            [(" Production Requirement ", [PRODUCTION_REQUIREMENT_RECORD])],
            name="unrecognized-space",
        )
        self.assertEqual(report.objects_for("Production Requirement"), ())
        self.assertEqual(report.issues, ())
        self.assertIn(" Production Requirement ", report.unrecognized_roles)
        states = self.states(report)
        matching = [
            state
            for name, state in states.items()
            if name.startswith(f"{CANONICALIZATION_ROLE_RECOGNITION}:")
        ]
        self.assertTrue(matching)
        self.assertTrue(all(state == EVALUATION_NOT_EVALUABLE for state in matching))

    def test_case_folded_role_literal_is_not_recognized(self) -> None:
        report = self.construct(
            [("production requirement", [PRODUCTION_REQUIREMENT_RECORD])],
            name="unrecognized-case",
        )
        self.assertEqual(report.objects_for("Production Requirement"), ())
        self.assertEqual(report.issues, ())

    def test_role_matching_does_not_trim_or_normalize(self) -> None:
        report = self.construct(
            [("Inbound Supply", [INBOUND_RECORD])], name="recognized-inbound"
        )
        self.assertEqual(len(report.inbound_records), 1)
        for variant in (" inbound supply", "Inbound  Supply", "INBOUND SUPPLY"):
            with self.subTest(variant=variant):
                other = self.construct(
                    [(variant, [INBOUND_RECORD])], name=f"variant-{abs(hash(variant))}"
                )
                self.assertEqual(other.inbound_records, ())
                self.assertEqual(other.issues, ())

    def test_target_to_role_mapping_is_consistent_with_construction(self) -> None:
        report = self.construct(
            [
                ("Plant / Material identity context", [{"plant_id": PLANT, "material_code": MATERIAL}]),
                ("Production Requirement", [PRODUCTION_REQUIREMENT_RECORD]),
                ("Inbound Supply", [INBOUND_RECORD]),
            ],
            name="target-role-map",
        )
        for entry in report.object_sets:
            for obj in entry.resolved + entry.unresolved:
                with self.subTest(target=obj.canonical_target):
                    self.assertEqual(
                        ROLE_FOR_TARGET[obj.canonical_target],
                        obj.canonicalization_role,
                    )
        for obj in report.inbound_records:
            self.assertEqual(obj.canonicalization_role, ROLE_INBOUND_SUPPLY)

    def test_unrecognized_role_set_is_reported_once_per_literal(self) -> None:
        report = self.construct(
            [("Mystery Role", [{"plant_id": PLANT}, {"plant_id": "P2"}])],
            name="unrecognized-once",
        )
        self.assertEqual(report.unrecognized_roles, ("Mystery Role",))

    def test_unrecognized_role_does_not_create_a_layer1_rejection(self) -> None:
        built, report = self.build([("Mystery Role", [{"plant_id": PLANT}])])
        self.assertTrue(report.accepted)
        self.assertEqual(report.disposition, "ACCEPTED")


class ApplicabilityTests(CanonicalObjectsTestCase):
    def test_applicability_matrix_covers_the_eleven_phase_a_roles(self) -> None:
        self.assertEqual(
            sorted(APPLICABILITY_BY_ROLE), sorted(PHASE_A_ROLE_LITERALS)
        )
        for literal, entry in APPLICABILITY_BY_ROLE.items():
            with self.subTest(role=literal):
                self.assertEqual(entry.literal, literal)
                self.assertTrue(entry.assignable)
                for wire_name, canonical_name in entry.assignable.items():
                    self.assertIn(wire_name, V02_CANONICAL_RECORD_PROPERTY_SET)
                    self.assertIn(canonical_name, V02_CANONICAL_RECORD_PROPERTY_SET)

    def test_only_assignable_properties_are_assigned(self) -> None:
        record = copy.deepcopy(INBOUND_RECORD)
        record["ProductionQty"] = "10"
        record["SafetyStock"] = "5"
        report = self.construct([("Inbound Supply", [record])], name="applicability")
        inbound = self.inbound(report)[report.inbound_records[0].record_reference]
        self.assertEqual(
            sorted(prop.name for prop in inbound.properties),
            [
                "effective_arrival_date",
                "inbound_status",
                "material_code",
                "ordered_qty",
                "plant_id",
                "received_qty",
            ],
        )
        self.assertEqual(
            inbound.non_applicable_properties, ("ProductionQty", "SafetyStock")
        )
        self.assertFalse(inbound.has("SafetyStock"))

    def test_absence_of_an_assignable_property_is_not_defaulted(self) -> None:
        record = {"plant_id": PLANT, "material_code": MATERIAL}
        report = self.construct([("Inbound Supply", [record])], name="no-default")
        inbound = report.inbound_records[0]
        self.assertFalse(inbound.has("ordered_qty"))
        self.assertFalse(inbound.has("received_qty"))
        self.assertFalse(inbound.has("inbound_status"))
        self.assertIs(inbound.value_of("received_qty", ABSENT), ABSENT)

    def test_safety_stock_is_not_assignable_from_inventory_snapshot(self) -> None:
        record = {
            "plant_id": PLANT,
            "material_code": MATERIAL,
            "inventory_snapshot_time": SNAPSHOT_TIME,
            "inventory_status": "AVAILABLE",
            "on_hand_qty": "100",
            "SafetyStock": "5",
        }
        report = self.construct([("Inventory Snapshot", [record])], name="inventory")
        snapshot = report.objects_for("Inventory Snapshot")[0]
        self.assertFalse(snapshot.has("SafetyStock"))
        self.assertIn("SafetyStock", snapshot.non_applicable_properties)

    def test_loss_rate_is_not_assigned_by_the_production_requirement_record(self) -> None:
        record = copy.deepcopy(PRODUCTION_REQUIREMENT_RECORD)
        record["loss_rate"] = "0.05"
        report = self.construct([("Production Requirement", [record])], name="loss-rate-record")
        requirement = report.objects_for("Production Requirement")[0]
        self.assertFalse(requirement.has("loss_rate"))
        self.assertIn("loss_rate", requirement.non_applicable_properties)


class InboundIdentityTests(CanonicalObjectsTestCase):
    def test_identity_representation_uses_package_role_and_ordinal(self) -> None:
        report = self.construct([("Inbound Supply", [INBOUND_RECORD])], name="inbound-identity")
        self.assertEqual(len(report.inbound_records), 1)
        reference = report.inbound_records[0].record_reference
        self.assertTrue(reference.startswith("SIMULATED-PKG-0001|Inbound Supply|"))
        self.assertTrue(reference.endswith("|0"))
        self.assertIsNone(report.inbound_records[0].grain)
        self.assertEqual(
            report.inbound_records[0].provenance.stable_source_evidence_locator,
            "0.json#0",
        )

    def test_content_identical_inbound_records_remain_distinct(self) -> None:
        report = self.construct(
            [("Inbound Supply", [copy.deepcopy(INBOUND_RECORD), copy.deepcopy(INBOUND_RECORD)])],
            name="inbound-duplicate",
        )
        self.assertEqual(len(report.inbound_records), 2)
        references = {item.record_reference for item in report.inbound_records}
        self.assertEqual(len(references), 2)
        self.assertEqual(
            sorted(item.provenance.stable_source_evidence_locator for item in report.inbound_records),
            ["0.json#0", "0.json#1"],
        )

    def test_identity_is_deterministic_for_the_same_accepted_view(self) -> None:
        _, accepted = self.accepted(
            [("Inbound Supply", [INBOUND_RECORD])], name="inbound-determinism"
        )
        handoff = PhaseAHandoff(analysis_run_id="RUN-1", analysis_date="2026-02-01")
        first = construct_canonical_objects(accepted, handoff)
        second = construct_canonical_objects(accepted, handoff)
        self.assertEqual(
            [item.record_reference for item in first.inbound_records],
            [item.record_reference for item in second.inbound_records],
        )
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_identity_does_not_reuse_the_stable_source_evidence_locator(self) -> None:
        report = self.construct([("Inbound Supply", [INBOUND_RECORD])], name="inbound-locator")
        item = report.inbound_records[0]
        self.assertNotEqual(
            item.record_reference, item.provenance.stable_source_evidence_locator
        )
        self.assertIn("|", item.record_reference)

    def test_no_inbound_record_id_or_extra_wire_property_is_created(self) -> None:
        report = self.construct([("Inbound Supply", [INBOUND_RECORD])], name="no-new-field")
        self.assertNotIn("inbound_record_id", V02_CANONICAL_RECORD_PROPERTY_SET)
        self.assertNotIn("parent_material_code", V02_CANONICAL_RECORD_PROPERTY_SET)
        item = report.inbound_records[0]
        for prop in item.properties:
            self.assertIn(prop.name, V02_CANONICAL_RECORD_PROPERTY_SET)
            self.assertNotIn(prop.name, ("inbound_record_id", "parent_material_code"))
        self.assertNotIn("inbound_record_id", item.__dataclass_fields__)


class BomParentBindingTests(CanonicalObjectsTestCase):
    def _parent_handoff(self, accepted, *, plant=PLANT, required=REQUIRED_DATE):
        return BomParentContextHandoff(
            plant_id=plant,
            required_date=required,
            evidence=self.evidence(
                accepted, role="Production Requirement", artifact="0.json", ordinal=0
            ),
        )

    def test_bom_component_binds_to_a_resolved_production_requirement_context(self) -> None:
        _, accepted = self.accepted(
            [
                ("Production Requirement", [PRODUCTION_REQUIREMENT_RECORD]),
                ("BOM Component", [BOM_COMPONENT_RECORD]),
            ],
            name="bom-bind",
        )
        handoff = PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-02-01",
            bom_parent_context=(self._parent_handoff(accepted),),
        )
        report = construct_canonical_objects(accepted, handoff)
        objects = report.objects_for("BOM Component")
        self.assertEqual(len(objects), 1)
        component = objects[0]
        self.assertEqual(component.value_of("material_code"), COMPONENT)
        self.assertEqual(component.value_of("BOMComponentQty"), "2")
        self.assertFalse(component.has("parent_material_code"))
        self.assertNotIn("parent_material_code", str(report.to_dict()))
        self.assertEqual(
            [prop.name for prop in component.grain],
            ["plant_id", "required_date", "material_code"],
        )

    def test_parent_context_is_not_created_without_source_evidence(self) -> None:
        _, accepted = self.accepted(
            [
                ("Production Requirement", [PRODUCTION_REQUIREMENT_RECORD]),
                ("BOM Component", [BOM_COMPONENT_RECORD]),
            ],
            name="bom-no-evidence",
        )
        handoff = PhaseAHandoff(analysis_run_id="RUN-1", analysis_date="2026-02-01")
        report = construct_canonical_objects(accepted, handoff)
        self.assertEqual(report.objects_for("BOM Component"), ())
        reasons = {issue.reason for issue in report.issues}
        self.assertIn("UNRESOLVED_IDENTITY", reasons)
        self.assertTrue(
            any(
                name.startswith("canonicalization.bom_parent_context:")
                and state == EVALUATION_NOT_EVALUABLE
                for name, state in self.states(report).items()
            )
        )

    def test_parent_handoff_evidence_outside_the_package_is_not_used(self) -> None:
        _, accepted = self.accepted(
            [
                ("Production Requirement", [PRODUCTION_REQUIREMENT_RECORD]),
                ("BOM Component", [BOM_COMPONENT_RECORD]),
            ],
            name="bom-foreign-package",
        )
        handoff = PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-02-01",
            bom_parent_context=(
                BomParentContextHandoff(
                    plant_id=PLANT,
                    required_date=REQUIRED_DATE,
                    evidence=self.evidence(
                        accepted,
                        role="Production Requirement",
                        artifact="0.json",
                        ordinal=0,
                        package_id="OTHER-PACKAGE",
                    ),
                ),
            ),
        )
        report = construct_canonical_objects(accepted, handoff)
        self.assertEqual(report.objects_for("BOM Component"), ())
        self.assertTrue(
            any(
                name.startswith(f"{CANONICALIZATION_HANDOFF_EVIDENCE}:bom_parent_context")
                and state == EVALUATION_NOT_EVALUABLE
                for name, state in self.states(report).items()
            )
        )

    def test_parent_handoff_pointing_at_a_non_requirement_record_is_not_used(self) -> None:
        _, accepted = self.accepted(
            [
                ("Inbound Supply", [INBOUND_RECORD]),
                ("BOM Component", [BOM_COMPONENT_RECORD]),
            ],
            name="bom-wrong-role",
        )
        handoff = PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-02-01",
            bom_parent_context=(
                BomParentContextHandoff(
                    plant_id=PLANT,
                    required_date=REQUIRED_DATE,
                    evidence=self.evidence(
                        accepted, role="Inbound Supply", artifact="0.json", ordinal=0
                    ),
                ),
            ),
        )
        report = construct_canonical_objects(accepted, handoff)
        self.assertEqual(report.objects_for("BOM Component"), ())

    def test_record_grain_mismatch_is_a_consistency_conflict(self) -> None:
        record = copy.deepcopy(BOM_COMPONENT_RECORD)
        record["required_date"] = "2026-03-15"
        _, accepted = self.accepted(
            [
                ("Production Requirement", [PRODUCTION_REQUIREMENT_RECORD]),
                ("BOM Component", [record]),
            ],
            name="bom-mismatch",
        )
        handoff = PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-02-01",
            bom_parent_context=(self._parent_handoff(accepted),),
        )
        report = construct_canonical_objects(accepted, handoff)
        conflicts = [
            issue
            for issue in report.issues
            if issue.category == "CONSISTENCY" and issue.reason == "CONSISTENCY_CONFLICT"
        ]
        self.assertEqual(len(conflicts), 1)
        self.assertIn("required_date", conflicts[0].detail)
        self.assertEqual(report.objects_for("BOM Component"), ())

    def test_ambiguous_parent_handoffs_stay_unresolved(self) -> None:
        second_requirement = copy.deepcopy(PRODUCTION_REQUIREMENT_RECORD)
        second_requirement["material_code"] = "M9"
        _, accepted = self.accepted(
            [
                (
                    "Production Requirement",
                    [PRODUCTION_REQUIREMENT_RECORD, second_requirement],
                ),
                ("BOM Component", [BOM_COMPONENT_RECORD]),
            ],
            name="bom-ambiguous",
        )
        handoff = PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-02-01",
            bom_parent_context=(
                self._parent_handoff(accepted),
                BomParentContextHandoff(
                    plant_id=PLANT,
                    required_date=REQUIRED_DATE,
                    evidence=self.evidence(
                        accepted,
                        role="Production Requirement",
                        artifact="0.json",
                        ordinal=1,
                    ),
                ),
            ),
        )
        report = construct_canonical_objects(accepted, handoff)
        self.assertEqual(report.objects_for("BOM Component"), ())
        self.assertTrue(
            any(
                name.startswith("canonicalization.bom_parent_context:")
                and state == EVALUATION_NOT_EVALUABLE
                for name, state in self.states(report).items()
            )
        )

    def test_no_bom_header_version_or_id_entity_is_created(self) -> None:
        _, accepted = self.accepted(
            [("Production Requirement", [PRODUCTION_REQUIREMENT_RECORD])],
            name="no-bom-entity",
        )
        report = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-02-01",
                bom_parent_context=(self._parent_handoff(accepted),),
            ),
        )
        payload = str(report.to_dict())
        for forbidden in ("BOM Header", "BOM Version", "BOM ID", "BOMVersion"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, payload)


class EffectiveDemandTests(CanonicalObjectsTestCase):
    def _handoff(self, accepted):
        return PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-02-01",
            effective_demand=(
                EffectiveDemandRelationHandoff(
                    source_substitute_material="M3",
                    target_material=MATERIAL,
                    relation="Target Applicability",
                    outcome="applicable",
                    evidence=self.evidence(
                        accepted, role="Substitute Allocation", artifact="0.json", ordinal=0
                    ),
                    mapping_basis="SIMULATED approved allocation applicability mapping",
                ),
                EffectiveDemandRelationHandoff(
                    source_substitute_material="M3",
                    target_material=MATERIAL,
                    relation="Source Reservation Overlap",
                    outcome="overlaps",
                    evidence=self.evidence(
                        accepted, role="Substitute Allocation", artifact="0.json", ordinal=0
                    ),
                    mapping_basis="SIMULATED approved source reservation mapping",
                ),
            ),
        )

    def test_two_relations_stay_independent_references(self) -> None:
        _, accepted = self.accepted(
            [
                (
                    "Substitute Allocation",
                    [
                        {
                            "plant_id": PLANT,
                            "target_material_code": MATERIAL,
                            "substitute_material_code": "M3",
                            "AllocatedSubstituteQty": "4",
                        }
                    ],
                ),
                (
                    "Plant / Material identity context",
                    [{"plant_id": PLANT, "material_code": MATERIAL}],
                ),
            ],
            name="demand-relations",
        )
        contexts, issues = build_effective_demand_contexts(accepted, self._handoff(accepted))
        self.assertEqual(issues, ())
        self.assertEqual(len(contexts), 1)
        relations = {item.relation: item.outcome for item in contexts[0].relations}
        self.assertEqual(
            relations,
            {"Target Applicability": "applicable", "Source Reservation Overlap": "overlaps"},
        )
        for relation in contexts[0].relations:
            self.assertTrue(relation.mapping_basis)
            self.assertTrue(relation.provenance.stable_source_evidence_locator)

    def test_relations_are_not_collapsed_into_one_boolean(self) -> None:
        _, accepted = self.accepted(
            [("Substitute Allocation", [{"plant_id": PLANT, "target_material_code": MATERIAL, "substitute_material_code": "M3", "AllocatedSubstituteQty": "4"}])],
            name="demand-not-boolean",
        )
        contexts, _ = build_effective_demand_contexts(accepted, self._handoff(accepted))
        relation_names = {item.relation for item in contexts[0].relations}
        self.assertEqual(len(relation_names), 2)
        self.assertTrue(
            all(isinstance(item.outcome, str) for item in contexts[0].relations)
        )

    def test_outcome_without_package_scoped_evidence_stays_unresolved(self) -> None:
        _, accepted = self.accepted(
            [("Substitute Allocation", [{"plant_id": PLANT, "target_material_code": MATERIAL, "substitute_material_code": "M3", "AllocatedSubstituteQty": "4"}])],
            name="demand-foreign",
        )
        handoff = PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-02-01",
            effective_demand=(
                EffectiveDemandRelationHandoff(
                    source_substitute_material="M3",
                    target_material=MATERIAL,
                    relation="Target Applicability",
                    outcome="applicable",
                    evidence=self.evidence(
                        accepted,
                        role="Substitute Allocation",
                        artifact="0.json",
                        ordinal=0,
                        package_id="OTHER-PACKAGE",
                    ),
                    mapping_basis="unverified",
                ),
            ),
        )
        contexts, issues = build_effective_demand_contexts(accepted, handoff)
        self.assertEqual(contexts, ())
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].reason, "SEMANTIC_UNRESOLVED")

    def test_effective_demand_context_is_not_a_canonical_field(self) -> None:
        _, accepted = self.accepted(
            [("Substitute Allocation", [{"plant_id": PLANT, "target_material_code": MATERIAL, "substitute_material_code": "M3", "AllocatedSubstituteQty": "4"}])],
            name="demand-not-field",
        )
        report = construct_canonical_objects(accepted, self._handoff(accepted))
        for obj in report.objects_for("Substitute Allocation"):
            for prop in obj.properties:
                self.assertIn(prop.name, V02_CANONICAL_RECORD_PROPERTY_SET)
            self.assertFalse(obj.has("requirement_id"))
            self.assertFalse(obj.has("demand_window_id"))
            self.assertFalse(obj.has("allocation_period"))
            self.assertFalse(obj.has("valid_from"))
            self.assertFalse(obj.has("valid_to"))
        for context in report.effective_demand_contexts:
            self.assertEqual(len(context.relations), 2)


class ProvenanceAndInjectionTests(CanonicalObjectsTestCase):
    def test_provenance_is_preserved_for_every_constructed_object(self) -> None:
        report = self.construct(
            [
                ("Production Requirement", [PRODUCTION_REQUIREMENT_RECORD]),
                ("Inbound Supply", [INBOUND_RECORD]),
            ],
            name="provenance",
        )
        objects = list(report.objects_for("Production Requirement")) + list(
            report.inbound_records
        )
        self.assertTrue(objects)
        for obj in objects:
            with self.subTest(target=obj.canonical_target):
                self.assertEqual(obj.provenance.snapshot_package_identity, "SIMULATED-PKG-0001")
                self.assertEqual(obj.provenance.logical_dataset_role, obj.canonicalization_role)
                self.assertTrue(obj.provenance.stable_source_evidence_locator)

    def test_loss_rate_handoff_requires_same_package_evidence(self) -> None:
        _, accepted = self.accepted(
            [("Production Requirement", [PRODUCTION_REQUIREMENT_RECORD])],
            name="loss-rate-handoff",
        )
        good = PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-02-01",
            loss_rate=(
                LossRateHandoff(
                    plant_id=PLANT,
                    parent_material_code=MATERIAL,
                    required_date=REQUIRED_DATE,
                    evidence=self.evidence(
                        accepted,
                        role="Production Requirement",
                        artifact="0.json",
                        ordinal=0,
                        property_name="loss_rate",
                    ),
                    resolved=True,
                    loss_rate="0.05",
                ),
            ),
        )
        report = construct_canonical_objects(accepted, good)
        self.assertEqual(len(report.loss_rate_contexts), 1)
        self.assertEqual(report.loss_rate_contexts[0].value, "0.05")

        foreign = PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-02-01",
            loss_rate=(
                LossRateHandoff(
                    plant_id=PLANT,
                    parent_material_code=MATERIAL,
                    required_date=REQUIRED_DATE,
                    evidence=self.evidence(
                        accepted,
                        role="Production Requirement",
                        artifact="0.json",
                        ordinal=0,
                        package_id="OTHER-PACKAGE",
                    ),
                    resolved=True,
                    loss_rate="0.05",
                ),
            ),
        )
        report = construct_canonical_objects(accepted, foreign)
        self.assertEqual(report.loss_rate_contexts, ())
        self.assertTrue(
            any(
                name.startswith(f"{CANONICALIZATION_HANDOFF_EVIDENCE}:loss_rate")
                and state == EVALUATION_NOT_EVALUABLE
                for name, state in self.states(report).items()
            )
        )

    def test_unresolved_loss_rate_is_not_given_a_value(self) -> None:
        _, accepted = self.accepted(
            [("Production Requirement", [PRODUCTION_REQUIREMENT_RECORD])],
            name="loss-rate-unresolved",
        )
        handoff = PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-02-01",
            loss_rate=(
                LossRateHandoff(
                    plant_id=PLANT,
                    parent_material_code=MATERIAL,
                    required_date=REQUIRED_DATE,
                    evidence=self.evidence(
                        accepted, role="Production Requirement", artifact="0.json"
                    ),
                    resolved=False,
                    loss_rate="0.05",
                ),
            ),
        )
        report = construct_canonical_objects(accepted, handoff)
        self.assertEqual(report.loss_rate_contexts, ())

    def test_safety_stock_handoff_is_not_defaulted_to_zero(self) -> None:
        _, accepted = self.accepted(
            [("Plant / Material identity context", [{"plant_id": PLANT, "material_code": MATERIAL}])],
            name="safety-stock-handoff",
        )
        handoff = PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-02-01",
            safety_stock=(
                SafetyStockHandoff(
                    plant_id=PLANT,
                    material_code=MATERIAL,
                    evidence=self.evidence(
                        accepted, role="Plant / Material identity context", artifact="0.json"
                    ),
                    resolved=False,
                    safety_stock="0",
                ),
            ),
        )
        report = construct_canonical_objects(accepted, handoff)
        self.assertEqual(report.safety_stock_contexts, ())

    def test_absent_safety_stock_dataset_never_becomes_a_default_value(self) -> None:
        report = self.construct(
            [("Plant / Material identity context", [{"plant_id": PLANT, "material_code": MATERIAL}])],
            name="safety-stock-absent",
        )
        self.assertEqual(report.objects_for("Configured Safety Stock"), ())
        self.assertEqual(report.safety_stock_contexts, ())
        self.assertEqual(report.issues, ())

    def test_analysis_run_context_uses_identity_plus_single_package_linkage(self) -> None:
        report = self.construct(
            [("Production Requirement", [PRODUCTION_REQUIREMENT_RECORD])],
            name="analysis-run",
        )
        context = report.analysis_run
        self.assertEqual(context.analysis_run_id, "RUN-1")
        self.assertEqual(context.snapshot_package_identity, "SIMULATED-PKG-0001")
        self.assertEqual(
            context.accepted_content_view_digest, report.accepted_content_view_digest
        )
        payload = str(report.to_dict())
        self.assertNotIn("Analysis Run|", payload)

    def test_unresolved_analysis_date_is_not_invented(self) -> None:
        _, accepted = self.accepted(
            [("Production Requirement", [PRODUCTION_REQUIREMENT_RECORD])],
            name="analysis-date",
        )
        report = construct_canonical_objects(
            accepted, PhaseAHandoff(analysis_run_id="RUN-1", analysis_date=None)
        )
        self.assertIsNone(report.analysis_run.analysis_date)
        self.assertFalse(report.analysis_date_resolved)
        self.assertTrue(
            any(
                name.startswith(f"{CANONICALIZATION_ANALYSIS_RUN}.AnalysisDate")
                and state == EVALUATION_NOT_EVALUABLE
                for name, state in self.states(report).items()
            )
        )


class RepresentationBoundaryTests(CanonicalObjectsTestCase):
    def test_zero_is_preserved_as_a_valid_value(self) -> None:
        record = copy.deepcopy(INBOUND_RECORD)
        record["received_qty"] = "0"
        report = self.construct([("Inbound Supply", [record])], name="zero")
        inbound = report.inbound_records[0]
        self.assertEqual(inbound.value_of("received_qty"), "0")
        self.assertNotEqual(inbound.value_of("received_qty", ABSENT), ABSENT)

    def test_json_null_is_preserved_and_never_guessed(self) -> None:
        record = copy.deepcopy(PRODUCTION_REQUIREMENT_RECORD)
        record["ProductionQty"] = None
        report = self.construct([("Production Requirement", [record])], name="null")
        requirement = report.objects_for("Production Requirement")[0]
        self.assertTrue(requirement.has("ProductionQty"))
        self.assertIsNone(requirement.value_of("ProductionQty"))
        self.assertNotEqual(requirement.value_of("ProductionQty"), "0")
        self.assertNotEqual(requirement.value_of("ProductionQty"), "")

    def test_omitted_property_is_not_guessed(self) -> None:
        record = {"plant_id": PLANT, "material_code": MATERIAL, "required_date": REQUIRED_DATE}
        report = self.construct([("Production Requirement", [record])], name="omitted")
        requirement = report.objects_for("Production Requirement")[0]
        self.assertFalse(requirement.has("ProductionQty"))
        self.assertIs(requirement.value_of("ProductionQty", ABSENT), ABSENT)

    def test_values_are_not_normalized(self) -> None:
        record = copy.deepcopy(PRODUCTION_REQUIREMENT_RECORD)
        record["material_code"] = "  M1  "
        record["ProductionQty"] = "10.500"
        report = self.construct([("Production Requirement", [record])], name="exact")
        requirement = report.objects_for("Production Requirement")[0]
        self.assertEqual(requirement.value_of("material_code"), "  M1  ")
        self.assertEqual(requirement.value_of("ProductionQty"), "10.500")

    def test_decimal_accessor_uses_decimal_and_never_binary_float(self) -> None:
        from decimal import Decimal

        record = copy.deepcopy(INBOUND_RECORD)
        record["ordered_qty"] = "0.1"
        record["received_qty"] = "0.7"
        report = self.construct([("Inbound Supply", [record])], name="decimal")
        inbound = report.inbound_records[0]
        ordered = next(prop for prop in inbound.properties if prop.name == "ordered_qty")
        received = next(prop for prop in inbound.properties if prop.name == "received_qty")
        self.assertEqual(ordered.decimal_value(), Decimal("0.1"))
        self.assertEqual(received.decimal_value(), Decimal("0.7"))
        self.assertEqual(
            ordered.decimal_value() + received.decimal_value(), Decimal("0.8")
        )
        # Binary floating point would not reproduce this exact base-10 result.
        self.assertNotEqual(
            float(ordered.decimal_value()) + float(received.decimal_value()), 0.8
        )
        self.assertNotIsInstance(ordered.value, float)
        self.assertIsInstance(ordered.value, str)

    def test_decimal_accessor_returns_none_for_non_decimal_values(self) -> None:
        record = copy.deepcopy(INBOUND_RECORD)
        record["received_qty"] = None
        report = self.construct([("Inbound Supply", [record])], name="decimal-none")
        inbound = report.inbound_records[0]
        received = next(prop for prop in inbound.properties if prop.name == "received_qty")
        self.assertIsNone(received.decimal_value())

    def test_required_quantity_never_reappears(self) -> None:
        report = self.construct(
            [
                ("Production Requirement", [PRODUCTION_REQUIREMENT_RECORD]),
                ("BOM Component", [BOM_COMPONENT_RECORD]),
            ],
            name="required-quantity",
        )
        self.assertNotIn("required_quantity", str(report.to_dict()))

    def test_derived_results_are_never_represented_as_source_objects(self) -> None:
        report = self.construct(
            [
                ("Production Requirement", [PRODUCTION_REQUIREMENT_RECORD]),
                ("Inbound Supply", [INBOUND_RECORD]),
            ],
            name="derived",
        )
        payload = str(report.to_dict())
        for derived in DERIVED_LITERALS:
            with self.subTest(derived=derived):
                self.assertNotIn(derived, payload)
        for target in {obj.canonical_target for obj in report.inbound_records}:
            self.assertNotIn(target, DERIVED_LITERALS)


class GrainResolutionTests(CanonicalObjectsTestCase):
    def test_exactly_one_applicable_evidence_resolves_the_grain(self) -> None:
        report = self.construct(
            [("Production Requirement", [PRODUCTION_REQUIREMENT_RECORD])],
            name="grain-resolved",
        )
        self.assertEqual(len(report.objects_for("Production Requirement")), 1)
        self.assertTrue(
            any(
                name.startswith(f"{CANONICALIZATION_GRAIN_RESOLUTION}:Production Requirement")
                and state == EVALUATION_PASSED
                for name, state in self.states(report).items()
            )
        )

    def test_multiple_applicable_evidence_stays_unresolved_without_precedence(self) -> None:
        duplicate = copy.deepcopy(PRODUCTION_REQUIREMENT_RECORD)
        duplicate["ProductionQty"] = "99"
        report = self.construct(
            [("Production Requirement", [PRODUCTION_REQUIREMENT_RECORD, duplicate])],
            name="grain-conflict",
        )
        self.assertEqual(report.objects_for("Production Requirement"), ())
        self.assertEqual(len(report.unresolved_for("Production Requirement")), 2)
        self.assertFalse(
            any(
                issue.reason == "CONSISTENCY_CONFLICT" for issue in report.issues
            ),
            msg="same-grain values must not be reconciled as a Stage B conflict",
        )
        self.assertTrue(
            any(
                name.startswith(f"{CANONICALIZATION_GRAIN_RESOLUTION}:Production Requirement")
                and state == EVALUATION_NOT_EVALUABLE
                for name, state in self.states(report).items()
            )
        )

    def test_missing_identity_component_leaves_the_object_unresolved(self) -> None:
        report = self.construct(
            [("Production Requirement", [{"plant_id": PLANT, "material_code": MATERIAL}])],
            name="grain-incomplete",
        )
        self.assertEqual(report.objects_for("Production Requirement"), ())
        self.assertEqual(len(report.unresolved_for("Production Requirement")), 1)
        self.assertIn("UNRESOLVED_IDENTITY", {issue.reason for issue in report.issues})


class BoundaryAndRegressionTests(CanonicalObjectsTestCase):
    def test_no_new_check_state_category_or_reason_is_introduced(self) -> None:
        report = self.construct(
            [
                ("Production Requirement", [PRODUCTION_REQUIREMENT_RECORD]),
                ("Mystery Role", [{"plant_id": PLANT}]),
            ],
            name="taxonomy",
        )
        allowed_states = {"passed", "failed", "not_evaluable"}
        for name, state, _ in report.checks:
            with self.subTest(check=name):
                self.assertIn(state, allowed_states)
        allowed_pairs = {
            ("PACKAGE_STRUCTURE", "STRUCTURAL_INCONSISTENCY"),
            ("FIELD_VALUE", "MISSING"),
            ("FIELD_VALUE", "INVALID_TYPE"),
            ("FIELD_VALUE", "OUT_OF_DEFINED_RANGE"),
            ("FIELD_VALUE", "INVALID_DEFINED_STATUS"),
            ("IDENTITY_RESOLUTION", "UNRESOLVED_IDENTITY"),
            ("IDENTITY_RESOLUTION", "UNRESOLVED_SCOPE"),
            ("SEMANTIC_RESOLUTION", "SEMANTIC_UNRESOLVED"),
            ("CONSISTENCY", "CONSISTENCY_CONFLICT"),
            ("PROVENANCE", "PROVENANCE_UNRESOLVED"),
            ("PROVENANCE", "PROVENANCE_MISMATCH"),
            ("BUSINESS_DATA", "DATA_INCOMPLETE"),
        }
        for issue in report.issues:
            with self.subTest(issue=issue.location):
                self.assertIn((issue.category, issue.reason), allowed_pairs)

    def test_construction_failure_is_not_a_layer1_rejection(self) -> None:
        built, accepted = self.accepted(
            [("Production Requirement", [PRODUCTION_REQUIREMENT_RECORD])],
            name="not-rejection",
        )
        report = construct_canonical_objects(
            accepted, PhaseAHandoff(analysis_run_id="RUN-1", analysis_date=None)
        )
        self.assertEqual(report.package_id, accepted.package_id)
        self.assertEqual(report.accepted_content_view_digest, accepted.content_view_digest)
        states = self.states(report)
        self.assertIn("passed", states.values())
        self.assertNotIn("REJECTED", states.values())

    def test_unusable_accepted_view_constructs_nothing(self) -> None:
        built, accepted = self.accepted(
            [("Production Requirement", [PRODUCTION_REQUIREMENT_RECORD])],
            name="unusable",
        )
        (built.root / "0.json").write_bytes(b'[{"plant_id": "TAMPERED"}]')
        layer2 = validate_layer2(accepted)
        self.assertEqual(layer2.disposition, DISPOSITION_UNUSABLE)
        report = construct_canonical_objects(
            accepted,
            PhaseAHandoff(analysis_run_id="RUN-1", analysis_date="2026-02-01"),
            layer2_report=layer2,
        )
        self.assertEqual(report.objects_for("Production Requirement"), ())
        self.assertEqual(report.inbound_records, ())
        self.assertEqual(report.issues, ())
        self.assertFalse(report.analysis_date_resolved)
        self.assertTrue(
            any(
                name == CANONICALIZATION_ANALYSIS_RUN and state == "failed"
                for name, state in self.states(report).items()
            )
        )

    def test_construction_never_re_reads_business_artifacts(self) -> None:
        built, accepted = self.accepted(
            [("Production Requirement", [PRODUCTION_REQUIREMENT_RECORD])],
            name="no-reread",
        )
        (built.root / "0.json").write_bytes(b"[]")
        report = construct_canonical_objects(
            accepted,
            PhaseAHandoff(analysis_run_id="RUN-1", analysis_date="2026-02-01"),
            layer2_report=validate_layer2(accepted),
        )
        self.assertEqual(report.objects_for("Production Requirement"), ())

    def test_construction_is_repeatable(self) -> None:
        _, accepted = self.accepted(
            [
                ("Production Requirement", [PRODUCTION_REQUIREMENT_RECORD]),
                ("Inbound Supply", [INBOUND_RECORD]),
            ],
            name="repeatable",
        )
        handoff = PhaseAHandoff(analysis_run_id="RUN-1", analysis_date="2026-02-01")
        first = construct_canonical_objects(accepted, handoff).to_dict()
        second = construct_canonical_objects(accepted, handoff).to_dict()
        self.assertEqual(first, second)

    def test_layer2_report_is_reused_when_supplied(self) -> None:
        _, accepted = self.accepted(
            [("Production Requirement", [PRODUCTION_REQUIREMENT_RECORD])],
            name="layer2-reuse",
        )
        layer2 = validate_layer2(accepted)
        report = construct_canonical_objects(
            accepted,
            PhaseAHandoff(analysis_run_id="RUN-1", analysis_date="2026-02-01"),
            layer2_report=layer2,
        )
        self.assertEqual(report.layer2_note, layer2.note)


if __name__ == "__main__":
    unittest.main()
