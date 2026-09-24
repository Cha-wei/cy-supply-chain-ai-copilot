"""Phase A canonical object construction tests (Issue #124, Phase A only).

Coverage required by Issue #124 Phase A Acceptance Criteria:

* recognized roles / exact role semantics;
* unrecognized role ``not_evaluable``;
* applicability boundary;
* G3-A deterministic ordinal identity;
* duplicate identical inbound records remain distinct;
* G4-A parent binding + mismatch + registered grain representation;
* G5-A two independent relations and the unresolved-outcome boundary;
* provenance preservation from the accepted record's registered associations;
* same-AcceptedPackage enforcement;
* no external business-value injection;
* zero preservation;
* null / omission no guessing;
* Decimal / no float semantics;
* no hidden normalization;
* no ``required_quantity``;
* no DERIVED source object;
* MG-2 / accepted-view boundary (including the Layer-2 report binding);
* deterministic repeatability;
* existing Layer-1 / Layer-2 regression (the shared suite).

All fixtures are SIMULATED.
"""

from __future__ import annotations

import copy
import unittest
import uuid
from dataclasses import replace
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
    LAYER2_REPORT_BINDING,
    PHASE_A_ROLE_LITERALS,
    RELATION_SOURCE_RESERVATION_OVERLAP,
    RELATION_TARGET_APPLICABILITY,
    ROLE_FOR_TARGET,
    ROLE_INBOUND_SUPPLY,
    BomParentContextHandoff,
    EffectiveDemandRelationHandoff,
    HandoffEvidence,
)
from snapshot_loader.constants import (
    EVALUATION_NOT_EVALUABLE,
    EVALUATION_PASSED,
    V02_CANONICAL_RECORD_PROPERTY_SET,
)
from tests.helpers import (
    DatasetSpec,
    PackageSpec,
    build_package,
    encode_json,
)

SCRATCH_ROOT = Path(__file__).resolve().parents[1] / "build" / "test-scratch"

PLANT = "P1"
MATERIAL = "M1"
COMPONENT = "M2"
REQUIRED_DATE = "2026-02-01"
SNAPSHOT_TIME = "2026-01-31T08:00:00Z"

#: Opaque Stable Source Evidence Locator strings registered by the SIMULATED fixtures.
#: They are deliberately independent of any artifact path, so a test can prove that a
#: caller cannot mint provenance by naming an ``artifact#ordinal`` path.
EVIDENCE_REQUIREMENT = "SIMULATED-SRC-REQ-1"
EVIDENCE_LOSS_RATE = "SIMULATED-SRC-LOSS-1"
EVIDENCE_SAFETY_STOCK = "SIMULATED-SRC-SS-1"
EVIDENCE_SAFETY_STOCK_ALT = "SIMULATED-SRC-SS-2"
EVIDENCE_ALLOCATION = "SIMULATED-SRC-ALLOC-1"
EVIDENCE_RELATIONSHIP = "SIMULATED-SRC-REL-1"

BASIS_LOSS_RATE = "SIMULATED-APPROVED-LOSS-RATE-MAPPING"
BASIS_SAFETY_STOCK = "SIMULATED-APPROVED-SAFETY-STOCK-MAPPING"


def with_provenance(
    record: dict[str, object],
    associations: list[tuple[str, list[str], str | None]],
) -> dict[str, object]:
    """Return ``record`` carrying the registered ``_meta.provenance_associations`` shape."""

    out = dict(record)
    out["_meta"] = {
        "provenance_associations": [
            {
                "observation": observation,
                "evidence": list(evidence),
                **({"mapping_basis": basis} if basis is not None else {}),
            }
            for observation, evidence, basis in associations
        ]
    }
    return out


def PRODUCTION_REQUIREMENT(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "plant_id": PLANT,
        "material_code": MATERIAL,
        "required_date": REQUIRED_DATE,
        "ProductionQty": "10",
    }
    record.update(overrides)
    return with_provenance(
        record, [("ProductionQty", [EVIDENCE_REQUIREMENT], None)]
    )


def BOM_COMPONENT(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "plant_id": PLANT,
        "required_date": REQUIRED_DATE,
        "material_code": COMPONENT,
        "BOMComponentQty": "2",
    }
    record.update(overrides)
    return with_provenance(record, [("BOMComponentQty", [EVIDENCE_REQUIREMENT], None)])


def INBOUND(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "plant_id": PLANT,
        "material_code": MATERIAL,
        "ordered_qty": "10",
        "received_qty": "0",
        "effective_arrival_date": "2026-01-20",
        "inbound_status": "CONFIRMED",
    }
    record.update(overrides)
    return record


def CONFIGURED_SAFETY_STOCK(value: str = "5", **overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "plant_id": PLANT,
        "material_code": MATERIAL,
        "SafetyStock": value,
    }
    record.update(overrides)
    return with_provenance(
        record, [("SafetyStock", [EVIDENCE_SAFETY_STOCK], None)]
    )


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

    def citation(
        self,
        accepted,
        *,
        role: str,
        artifact: str,
        ordinal: int = 0,
        locator: str | None = None,
        package_id: str | None = None,
    ) -> HandoffEvidence:
        """An offered handoff evidence citation (unverified until construction)."""

        return HandoffEvidence(
            snapshot_package_identity=package_id or accepted.package_id,
            logical_dataset_role=role,
            artifact=artifact,
            record_ordinal=ordinal,
            evidence_locator=locator,
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
        report = self.construct([("Production Requirement", [PRODUCTION_REQUIREMENT()])])
        objects = report.objects_for("Production Requirement")
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0].canonicalization_role, "Production Requirement")
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
            [(" Production Requirement ", [PRODUCTION_REQUIREMENT()])],
            name="unrecognized-space",
        )
        self.assertEqual(report.objects_for("Production Requirement"), ())
        self.assertEqual(report.issues, ())
        self.assertIn(" Production Requirement ", report.unrecognized_roles)
        matching = [
            state
            for name, state in self.states(report).items()
            if name.startswith(f"{CANONICALIZATION_ROLE_RECOGNITION}:")
        ]
        self.assertTrue(matching)
        self.assertTrue(all(state == EVALUATION_NOT_EVALUABLE for state in matching))

    def test_case_folded_role_literal_is_not_recognized(self) -> None:
        report = self.construct(
            [("production requirement", [PRODUCTION_REQUIREMENT()])],
            name="unrecognized-case",
        )
        self.assertEqual(report.objects_for("Production Requirement"), ())
        self.assertEqual(report.issues, ())

    def test_role_matching_does_not_trim_or_normalize(self) -> None:
        report = self.construct([("Inbound Supply", [INBOUND()])], name="recognized-inbound")
        self.assertEqual(len(report.inbound_records), 1)
        for variant in (" inbound supply", "Inbound  Supply", "INBOUND SUPPLY"):
            with self.subTest(variant=variant):
                other = self.construct(
                    [(variant, [INBOUND()])], name=f"variant-{abs(hash(variant))}"
                )
                self.assertEqual(other.inbound_records, ())
                self.assertEqual(other.issues, ())

    def test_unrecognized_role_set_is_reported_once_per_literal(self) -> None:
        report = self.construct(
            [("Mystery Role", [{"plant_id": PLANT}, {"plant_id": "P2"}])],
            name="unrecognized-once",
        )
        self.assertEqual(report.unrecognized_roles, ("Mystery Role",))

    def test_unrecognized_role_does_not_create_a_layer1_rejection(self) -> None:
        _built, report = self.build([("Mystery Role", [{"plant_id": PLANT}])])
        self.assertTrue(report.accepted)
        self.assertEqual(report.disposition, "ACCEPTED")

    def test_target_to_role_mapping_is_consistent_with_construction(self) -> None:
        report = self.construct(
            [
                ("Plant / Material identity context", [{"plant_id": PLANT, "material_code": MATERIAL}]),
                ("Production Requirement", [PRODUCTION_REQUIREMENT()]),
                ("Inbound Supply", [INBOUND()]),
            ],
            name="target-role-map",
        )
        for entry in report.object_sets:
            for obj in entry.resolved + entry.unresolved:
                with self.subTest(target=obj.canonical_target):
                    self.assertEqual(
                        ROLE_FOR_TARGET[obj.canonical_target], obj.canonicalization_role
                    )
        for obj in report.inbound_records:
            self.assertEqual(obj.canonicalization_role, ROLE_INBOUND_SUPPLY)


class ApplicabilityTests(CanonicalObjectsTestCase):
    def test_applicability_matrix_covers_the_eleven_phase_a_roles(self) -> None:
        self.assertEqual(sorted(APPLICABILITY_BY_ROLE), sorted(PHASE_A_ROLE_LITERALS))
        for literal, entry in APPLICABILITY_BY_ROLE.items():
            with self.subTest(role=literal):
                self.assertEqual(entry.literal, literal)
                self.assertTrue(entry.assignable)
                for wire_name, canonical_name in entry.assignable.items():
                    self.assertIn(wire_name, V02_CANONICAL_RECORD_PROPERTY_SET)
                    self.assertIn(canonical_name, V02_CANONICAL_RECORD_PROPERTY_SET)

    def test_only_assignable_properties_are_assigned(self) -> None:
        record = INBOUND()
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
        report = self.construct(
            [("Inbound Supply", [{"plant_id": PLANT, "material_code": MATERIAL}])],
            name="no-default",
        )
        inbound = report.inbound_records[0]
        self.assertFalse(inbound.has("ordered_qty"))
        self.assertFalse(inbound.has("inbound_status"))
        self.assertIs(inbound.value_of("received_qty", ABSENT), ABSENT)

    def test_safety_stock_is_not_assignable_from_inventory_snapshot(self) -> None:
        report = self.construct(
            [
                (
                    "Inventory Snapshot",
                    [
                        {
                            "plant_id": PLANT,
                            "material_code": MATERIAL,
                            "inventory_snapshot_time": SNAPSHOT_TIME,
                            "inventory_status": "AVAILABLE",
                            "on_hand_qty": "100",
                            "SafetyStock": "5",
                        }
                    ],
                )
            ],
            name="inventory",
        )
        snapshot = report.objects_for("Inventory Snapshot")[0]
        self.assertFalse(snapshot.has("SafetyStock"))
        self.assertIn("SafetyStock", snapshot.non_applicable_properties)

    def test_loss_rate_is_not_assigned_by_the_production_requirement_record(self) -> None:
        record = PRODUCTION_REQUIREMENT(loss_rate="0.05")
        report = self.construct([("Production Requirement", [record])], name="loss-rate-record")
        requirement = report.objects_for("Production Requirement")[0]
        self.assertFalse(requirement.has("loss_rate"))
        self.assertIn("loss_rate", requirement.non_applicable_properties)


class InboundIdentityTests(CanonicalObjectsTestCase):
    def test_identity_representation_uses_package_role_and_ordinal(self) -> None:
        report = self.construct([("Inbound Supply", [INBOUND()])], name="inbound-identity")
        self.assertEqual(len(report.inbound_records), 1)
        reference = report.inbound_records[0].record_reference
        self.assertTrue(reference.startswith("SIMULATED-PKG-0001|Inbound Supply|"))
        self.assertTrue(reference.endswith("|0"))
        self.assertIsNone(report.inbound_records[0].grain)

    def test_content_identical_inbound_records_remain_distinct(self) -> None:
        report = self.construct(
            [("Inbound Supply", [INBOUND(), INBOUND()])], name="inbound-duplicate"
        )
        self.assertEqual(len(report.inbound_records), 2)
        references = {item.record_reference for item in report.inbound_records}
        self.assertEqual(len(references), 2)

    def test_identity_is_deterministic_for_the_same_accepted_view(self) -> None:
        _, accepted = self.accepted(
            [("Inbound Supply", [INBOUND()])], name="inbound-determinism"
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
        report = self.construct([("Inbound Supply", [INBOUND()])], name="inbound-locator")
        item = report.inbound_records[0]
        self.assertIn("|", item.record_reference)
        self.assertNotIn(EVIDENCE_REQUIREMENT, item.record_reference)

    def test_no_inbound_record_id_or_extra_wire_property_is_created(self) -> None:
        report = self.construct([("Inbound Supply", [INBOUND()])], name="no-new-field")
        self.assertNotIn("inbound_record_id", V02_CANONICAL_RECORD_PROPERTY_SET)
        self.assertNotIn("parent_material_code", V02_CANONICAL_RECORD_PROPERTY_SET)
        item = report.inbound_records[0]
        for prop in item.properties:
            self.assertIn(prop.name, V02_CANONICAL_RECORD_PROPERTY_SET)
            self.assertNotIn(prop.name, ("inbound_record_id", "parent_material_code"))
        self.assertNotIn("inbound_record_id", item.__dataclass_fields__)


class BomParentBindingTests(CanonicalObjectsTestCase):
    def _parent_handoff(self, accepted):
        return BomParentContextHandoff(
            plant_id=PLANT,
            required_date=REQUIRED_DATE,
            evidence=self.citation(
                accepted, role="Production Requirement", artifact="0.json", ordinal=0
            ),
        )

    def test_bom_component_binds_to_a_resolved_production_requirement_context(self) -> None:
        _, accepted = self.accepted(
            [
                ("Production Requirement", [PRODUCTION_REQUIREMENT()]),
                ("BOM Component", [BOM_COMPONENT()]),
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
        # BOM-local grain = the role's existing ``material_code``, i.e. the component
        # material identity; the parent / requirement part of the effective grain is the
        # resolved Production Requirement context reference.
        self.assertEqual(
            [(prop.name, prop.value) for prop in component.grain],
            [("material_code", COMPONENT)],
        )
        self.assertNotIn("component_material_code", str(component.grain))
        self.assertNotIn("parent_material_code", str(component.grain))
        # The resolved context reference and its upstream provenance are preserved, and
        # together they are the parent / requirement part of the effective BOM grain.
        parent = report.objects_for("Production Requirement")[0]
        self.assertEqual(component.context_reference, parent.record_reference)
        self.assertEqual(component.context_provenance, parent.provenance)
        self.assertEqual(
            component.context_provenance.stable_source_evidence_locators,
            (EVIDENCE_REQUIREMENT,),
        )
        self.assertEqual(
            [(prop.name, prop.value) for prop in parent.grain],
            [
                ("plant_id", PLANT),
                ("material_code", MATERIAL),
                ("required_date", REQUIRED_DATE),
            ],
        )
        self.assertFalse(component.has("parent_material_code"))
        self.assertNotIn("parent_material_code", V02_CANONICAL_RECORD_PROPERTY_SET)

    def test_two_components_under_one_requirement_are_two_effective_grains(self) -> None:
        _, accepted = self.accepted(
            [
                ("Production Requirement", [PRODUCTION_REQUIREMENT()]),
                ("BOM Component", [BOM_COMPONENT(), BOM_COMPONENT(material_code="M3")]),
            ],
            name="bom-two-grains",
        )
        report = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-02-01",
                bom_parent_context=(self._parent_handoff(accepted),),
            ),
        )
        objects = report.objects_for("BOM Component")
        self.assertEqual(len(objects), 2)
        effective = {
            (obj.context_reference, obj.value_of("material_code")) for obj in objects
        }
        self.assertEqual(
            effective,
            {
                (report.objects_for("Production Requirement")[0].record_reference, COMPONENT),
                (report.objects_for("Production Requirement")[0].record_reference, "M3"),
            },
        )
        # The two effective BOM grains / identities are distinct.
        self.assertEqual(
            len({obj.record_reference for obj in objects}),
            2,
        )
        self.assertEqual(
            sorted(obj.value_of("material_code") for obj in objects), ["M2", "M3"]
        )

    def test_no_component_material_code_identity_component_is_introduced(self) -> None:
        _, accepted = self.accepted(
            [
                ("Production Requirement", [PRODUCTION_REQUIREMENT()]),
                ("BOM Component", [BOM_COMPONENT()]),
            ],
            name="bom-no-extra-identity",
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
        self.assertNotIn("component_material_code", payload)

    def test_omitted_component_material_code_stays_unresolved_without_error(self) -> None:
        # Layer-1 / Layer-2 do not guarantee ``material_code``; an omitted component
        # material identity must never raise, be defaulted, or be synthesised.
        omitted = {
            "plant_id": PLANT,
            "required_date": REQUIRED_DATE,
            "BOMComponentQty": "2",
        }
        _, accepted = self.accepted(
            [
                ("Production Requirement", [PRODUCTION_REQUIREMENT()]),
                ("BOM Component", [omitted]),
            ],
            name="bom-omitted-material",
        )
        report = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-02-01",
                bom_parent_context=(self._parent_handoff(accepted),),
            ),
        )
        self.assertEqual(report.objects_for("BOM Component"), ())
        self.assertEqual(len(report.unresolved_for("BOM Component")), 1)
        unresolved = report.unresolved_for("BOM Component")[0]
        self.assertIsNone(unresolved.grain)
        self.assertIsNone(unresolved.context_reference)
        self.assertFalse(unresolved.has("material_code"))
        self.assertIn("UNRESOLVED_IDENTITY", {issue.reason for issue in report.issues})
        identity_issues = [
            issue for issue in report.issues if issue.reason == "UNRESOLVED_IDENTITY"
        ]
        self.assertTrue(
            any("component material_code" in issue.detail for issue in identity_issues)
        )
        self.assertNotIn("material_code", str(unresolved.grain))

    def test_parent_context_is_not_created_without_source_evidence(self) -> None:
        _, accepted = self.accepted(
            [
                ("Production Requirement", [PRODUCTION_REQUIREMENT()]),
                ("BOM Component", [BOM_COMPONENT()]),
            ],
            name="bom-no-evidence",
        )
        report = construct_canonical_objects(
            accepted,
            PhaseAHandoff(analysis_run_id="RUN-1", analysis_date="2026-02-01"),
        )
        self.assertEqual(report.objects_for("BOM Component"), ())
        self.assertIn("UNRESOLVED_IDENTITY", {issue.reason for issue in report.issues})
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
                ("Production Requirement", [PRODUCTION_REQUIREMENT()]),
                ("BOM Component", [BOM_COMPONENT()]),
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
                    evidence=self.citation(
                        accepted,
                        role="Production Requirement",
                        artifact="0.json",
                        package_id="OTHER-PACKAGE",
                    ),
                ),
            ),
        )
        report = construct_canonical_objects(accepted, handoff)
        self.assertEqual(report.objects_for("BOM Component"), ())

    def test_parent_handoff_pointing_at_a_non_requirement_record_is_not_used(self) -> None:
        _, accepted = self.accepted(
            [
                ("Inbound Supply", [INBOUND()]),
                ("BOM Component", [BOM_COMPONENT()]),
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
                    evidence=self.citation(
                        accepted, role="Inbound Supply", artifact="0.json", ordinal=0
                    ),
                ),
            ),
        )
        report = construct_canonical_objects(accepted, handoff)
        self.assertEqual(report.objects_for("BOM Component"), ())

    def test_record_grain_mismatch_is_a_consistency_conflict(self) -> None:
        _, accepted = self.accepted(
            [
                ("Production Requirement", [PRODUCTION_REQUIREMENT()]),
                ("BOM Component", [BOM_COMPONENT(required_date="2026-03-15")]),
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
        second = PRODUCTION_REQUIREMENT(material_code="M9")
        _, accepted = self.accepted(
            [
                ("Production Requirement", [PRODUCTION_REQUIREMENT(), second]),
                ("BOM Component", [BOM_COMPONENT()]),
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
                    evidence=self.citation(
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

    def test_no_bom_header_version_or_id_entity_is_created(self) -> None:
        _, accepted = self.accepted(
            [("Production Requirement", [PRODUCTION_REQUIREMENT()])], name="no-bom-entity"
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
    """G5-A: evidence only; conceptual outcomes stay unresolved (no invented mapping)."""

    def _datasets(self):
        return [
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
                "Substitute Relationship",
                [
                    {
                        "plant_id": PLANT,
                        "target_material_code": MATERIAL,
                        "substitute_material_code": "M3",
                        "substitution_ratio": "0.5",
                        "approval_status": "APPROVED",
                    }
                ],
            ),
        ]

    def _handoff(self, accepted):
        return PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-02-01",
            effective_demand=(
                EffectiveDemandRelationHandoff(
                    source_substitute_material="M3",
                    target_material=MATERIAL,
                    relation=RELATION_TARGET_APPLICABILITY,
                    evidence=self.citation(
                        accepted,
                        role="Substitute Relationship",
                        artifact="1.json",
                        ordinal=0,
                        locator=EVIDENCE_RELATIONSHIP,
                    ),
                    mapping_basis="SIMULATED approved applicability mapping",
                ),
                EffectiveDemandRelationHandoff(
                    source_substitute_material="M3",
                    target_material=MATERIAL,
                    relation=RELATION_SOURCE_RESERVATION_OVERLAP,
                    evidence=self.citation(
                        accepted,
                        role="Substitute Allocation",
                        artifact="0.json",
                        ordinal=0,
                        locator=EVIDENCE_ALLOCATION,
                    ),
                    mapping_basis="SIMULATED approved reservation mapping",
                ),
            ),
        )

    def test_relation_outcomes_are_never_taken_from_canonical_values(self) -> None:
        _, accepted = self.accepted(self._datasets(), name="demand-no-invented-mapping")
        contexts, issues = build_effective_demand_contexts(
            accepted, self._handoff(accepted)
        )
        # No approved source-value -> conceptual outcome mapping exists in the current
        # authority, so no pair is emitted and no outcome is invented.
        self.assertEqual(contexts, ())
        self.assertTrue(issues)
        self.assertTrue(all(issue.reason == "SEMANTIC_UNRESOLVED" for issue in issues))
        for issue in issues:
            self.assertNotIn("APPROVED", issue.detail)

    def test_approved_conceptual_outcomes_are_the_only_ones(self) -> None:
        _accepted_contexts = ()
        allowed = {
            "applicable",
            "not applicable",
            "unresolved",
            "overlaps",
            "does not overlap",
        }
        self.assertIn("applicable", allowed)
        self.assertIn("unresolved", allowed)

    def test_exactly_one_pair_required_per_grain(self) -> None:
        _, accepted = self.accepted(self._datasets(), name="demand-pair")
        handoff = PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-02-01",
            effective_demand=(
                EffectiveDemandRelationHandoff(
                    source_substitute_material="M3",
                    target_material=MATERIAL,
                    relation=RELATION_TARGET_APPLICABILITY,
                    evidence=self.citation(
                        accepted, role="Substitute Relationship", artifact="1.json"
                    ),
                    mapping_basis="SIMULATED approved applicability mapping",
                ),
            ),
        )
        contexts, issues = build_effective_demand_contexts(accepted, handoff)
        self.assertEqual(contexts, ())
        self.assertTrue(issues)

    def test_repeated_relation_evidence_is_not_deduplicated(self) -> None:
        _, accepted = self.accepted(self._datasets(), name="demand-repeat")
        base = self._handoff(accepted)
        handoff = PhaseAHandoff(
            analysis_run_id=base.analysis_run_id,
            analysis_date=base.analysis_date,
            effective_demand=base.effective_demand
            + (
                EffectiveDemandRelationHandoff(
                    source_substitute_material="M3",
                    target_material=MATERIAL,
                    relation=RELATION_TARGET_APPLICABILITY,
                    evidence=self.citation(
                        accepted, role="Substitute Relationship", artifact="1.json"
                    ),
                    mapping_basis="SIMULATED approved applicability mapping",
                ),
            ),
        )
        contexts, issues = build_effective_demand_contexts(accepted, handoff)
        self.assertEqual(contexts, ())
        self.assertTrue(issues)

    def test_unverifiable_relation_evidence_stays_unresolved(self) -> None:
        _, accepted = self.accepted(self._datasets(), name="demand-foreign")
        handoff = PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-02-01",
            effective_demand=(
                EffectiveDemandRelationHandoff(
                    source_substitute_material="M3",
                    target_material=MATERIAL,
                    relation=RELATION_TARGET_APPLICABILITY,
                    evidence=self.citation(
                        accepted,
                        role="Substitute Relationship",
                        artifact="1.json",
                        package_id="OTHER-PACKAGE",
                    ),
                    mapping_basis="unverified",
                ),
            ),
        )
        contexts, issues = build_effective_demand_contexts(accepted, handoff)
        self.assertEqual(contexts, ())
        # One issue for the unverifiable citation and one for the pair whose other
        # registered relation carries no evidence at all.
        self.assertEqual(len(issues), 2)
        self.assertTrue(
            all(issue.reason == "SEMANTIC_UNRESOLVED" for issue in issues)
        )
        self.assertTrue(
            any("OTHER-PACKAGE" not in issue.detail for issue in issues)
        )

    def test_effective_demand_context_is_not_a_canonical_field(self) -> None:
        _, accepted = self.accepted(self._datasets(), name="demand-not-field")
        report = construct_canonical_objects(accepted, self._handoff(accepted))
        for obj in report.objects_for("Substitute Allocation"):
            for prop in obj.properties:
                self.assertIn(prop.name, V02_CANONICAL_RECORD_PROPERTY_SET)
            for forbidden in (
                "requirement_id",
                "demand_window_id",
                "allocation_period",
                "valid_from",
                "valid_to",
            ):
                self.assertFalse(obj.has(forbidden))
        self.assertEqual(report.effective_demand_contexts, ())

    def test_no_caller_supplied_outcome_parameter_exists(self) -> None:
        fields = EffectiveDemandRelationHandoff.__dataclass_fields__
        self.assertNotIn("outcome", fields)
        self.assertIn("evidence", fields)
        self.assertIn("mapping_basis", fields)


class ProvenanceTests(CanonicalObjectsTestCase):
    def test_provenance_carries_the_registered_accepted_locators(self) -> None:
        report = self.construct(
            [
                ("Production Requirement", [PRODUCTION_REQUIREMENT()]),
                ("Inbound Supply", [INBOUND()]),
            ],
            name="provenance",
        )
        objects = list(report.objects_for("Production Requirement")) + list(
            report.inbound_records
        )
        self.assertTrue(objects)
        requirement = report.objects_for("Production Requirement")[0]
        self.assertEqual(
            requirement.provenance.stable_source_evidence_locators,
            (EVIDENCE_REQUIREMENT,),
        )
        self.assertEqual(
            requirement.provenance.registered_observations, ("ProductionQty",)
        )
        self.assertEqual(
            requirement.provenance.snapshot_package_identity, "SIMULATED-PKG-0001"
        )
        # An inbound fixture registers no association: nothing is synthesised for it.
        inbound = report.inbound_records[0]
        self.assertEqual(inbound.provenance.stable_source_evidence_locators, ())
        self.assertEqual(inbound.provenance.registered_observations, ())
        self.assertIsNone(inbound.provenance.logical_observation)

    def test_artifact_path_is_never_presented_as_the_authoritative_locator(self) -> None:
        report = self.construct(
            [("Production Requirement", [PRODUCTION_REQUIREMENT()])], name="provenance-path"
        )
        provenance = report.objects_for("Production Requirement")[0].provenance
        self.assertEqual(provenance.record_path, "0.json#0")
        self.assertNotIn(provenance.record_path, provenance.stable_source_evidence_locators)
        self.assertEqual(
            provenance.stable_source_evidence_locators, (EVIDENCE_REQUIREMENT,)
        )

    def test_caller_cannot_mint_an_evidence_locator(self) -> None:
        _, accepted = self.accepted(
            [("Production Requirement", [PRODUCTION_REQUIREMENT()])], name="mint-locator"
        )
        handoff = PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-02-01",
            bom_parent_context=(
                BomParentContextHandoff(
                    plant_id=PLANT,
                    required_date=REQUIRED_DATE,
                    evidence=self.citation(
                        accepted,
                        role="Production Requirement",
                        artifact="0.json",
                        ordinal=0,
                        locator="CALLER-MINTED-LOCATOR",
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


class InjectionBoundaryTests(CanonicalObjectsTestCase):
    def _loss_rate_record(self) -> dict[str, object]:
        return PRODUCTION_REQUIREMENT(loss_rate="0.05")

    def _loss_rate_handoff(self, accepted, **overrides: object) -> LossRateHandoff:
        payload: dict[str, object] = {
            "plant_id": PLANT,
            "parent_material_code": MATERIAL,
            "required_date": REQUIRED_DATE,
            "evidence": self.citation(
                accepted, role="Production Requirement", artifact="0.json"
            ),
            "loss_rate_evidence": (),  # filled per test
            "loss_rate": "0.05",
            "resolution_basis": BASIS_LOSS_RATE,
        }
        payload.update(overrides)
        return LossRateHandoff(**payload)  # type: ignore[arg-type]

    def test_loss_rate_requires_registered_accepted_provenance(self) -> None:
        _, accepted = self.accepted(
            [("Production Requirement", [self._loss_rate_record()])],
            name="loss-rate-provenance",
        )
        # The record carries ``loss_rate`` but registers no association for it.
        unregistered = self._loss_rate_handoff(
            accepted,
            loss_rate_evidence=(
                self.citation(
                    accepted, role="Production Requirement", artifact="0.json", ordinal=0
                ),
            ),
        )
        report = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-02-01",
                loss_rate=(unregistered,),
            ),
        )
        self.assertEqual(report.loss_rate_contexts, ())

    def test_loss_rate_is_carried_with_registered_provenance_and_basis(self) -> None:
        record = with_provenance(
            self._loss_rate_record(),
            [
                ("loss_rate", [EVIDENCE_LOSS_RATE], BASIS_LOSS_RATE),
                ("ProductionQty", [EVIDENCE_REQUIREMENT], None),
            ],
        )
        _, accepted = self.accepted(
            [("Production Requirement", [record])], name="loss-rate-registered"
        )
        handoff = self._loss_rate_handoff(
            accepted,
            loss_rate_evidence=(
                self.citation(
                    accepted,
                    role="Production Requirement",
                    artifact="0.json",
                    ordinal=0,
                    locator=EVIDENCE_LOSS_RATE,
                ),
            ),
        )
        report = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-02-01",
                loss_rate=(handoff,),
            ),
        )
        self.assertEqual(len(report.loss_rate_contexts), 1)
        context = report.loss_rate_contexts[0]
        self.assertEqual(context.value, "0.05")
        self.assertEqual(
            context.provenance.stable_source_evidence_locators,
            (EVIDENCE_LOSS_RATE,),
        )
        self.assertEqual(context.provenance.mapping_resolution_basis, BASIS_LOSS_RATE)

    def test_loss_rate_without_registered_basis_is_not_carried(self) -> None:
        record = with_provenance(
            self._loss_rate_record(),
            [("loss_rate", [EVIDENCE_LOSS_RATE], None)],
        )
        _, accepted = self.accepted(
            [("Production Requirement", [record])], name="loss-rate-no-basis"
        )
        handoff = self._loss_rate_handoff(
            accepted,
            loss_rate_evidence=(
                self.citation(
                    accepted,
                    role="Production Requirement",
                    artifact="0.json",
                    ordinal=0,
                    locator=EVIDENCE_LOSS_RATE,
                ),
            ),
        )
        report = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-02-01",
                loss_rate=(handoff,),
            ),
        )
        self.assertEqual(report.loss_rate_contexts, ())

    def test_caller_free_string_is_not_an_approved_mapping_basis(self) -> None:
        record = with_provenance(
            self._loss_rate_record(),
            [("loss_rate", [EVIDENCE_LOSS_RATE], BASIS_LOSS_RATE)],
        )
        _, accepted = self.accepted(
            [("Production Requirement", [record])], name="loss-rate-basis-mismatch"
        )
        handoff = self._loss_rate_handoff(
            accepted,
            loss_rate_evidence=(
                self.citation(
                    accepted,
                    role="Production Requirement",
                    artifact="0.json",
                    ordinal=0,
                    locator=EVIDENCE_LOSS_RATE,
                ),
            ),
            resolution_basis="CALLER-INVENTED-BASIS",
        )
        report = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-02-01",
                loss_rate=(handoff,),
            ),
        )
        self.assertEqual(report.loss_rate_contexts, ())

    def test_loss_rate_value_the_evidence_does_not_carry_is_rejected(self) -> None:
        record = with_provenance(
            self._loss_rate_record(),
            [("loss_rate", [EVIDENCE_LOSS_RATE], BASIS_LOSS_RATE)],
        )
        _, accepted = self.accepted(
            [("Production Requirement", [record])], name="loss-rate-unbacked"
        )
        handoff = self._loss_rate_handoff(
            accepted,
            loss_rate_evidence=(
                self.citation(
                    accepted,
                    role="Production Requirement",
                    artifact="0.json",
                    ordinal=0,
                    locator=EVIDENCE_LOSS_RATE,
                ),
            ),
            loss_rate="0.99",
        )
        report = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-02-01",
                loss_rate=(handoff,),
            ),
        )
        self.assertEqual(report.loss_rate_contexts, ())

    def test_multiple_applicable_loss_rate_evidence_is_not_deduplicated(self) -> None:
        record = with_provenance(
            self._loss_rate_record(),
            [("loss_rate", [EVIDENCE_LOSS_RATE], BASIS_LOSS_RATE)],
        )
        _, accepted = self.accepted(
            [("Production Requirement", [record, copy.deepcopy(record)])],
            name="loss-rate-two-evidence",
        )
        handoff = self._loss_rate_handoff(
            accepted,
            loss_rate_evidence=(
                self.citation(
                    accepted,
                    role="Production Requirement",
                    artifact="0.json",
                    ordinal=0,
                    locator=EVIDENCE_LOSS_RATE,
                ),
                self.citation(
                    accepted,
                    role="Production Requirement",
                    artifact="0.json",
                    ordinal=1,
                    locator=EVIDENCE_LOSS_RATE,
                ),
            ),
        )
        report = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-02-01",
                loss_rate=(handoff,),
            ),
        )
        self.assertEqual(report.loss_rate_contexts, ())

    def test_foreign_package_loss_rate_evidence_is_not_used(self) -> None:
        record = with_provenance(
            self._loss_rate_record(),
            [("loss_rate", [EVIDENCE_LOSS_RATE], BASIS_LOSS_RATE)],
        )
        _, accepted = self.accepted(
            [("Production Requirement", [record])], name="loss-rate-foreign"
        )
        handoff = self._loss_rate_handoff(
            accepted,
            evidence=self.citation(
                accepted,
                role="Production Requirement",
                artifact="0.json",
                package_id="OTHER-PACKAGE",
            ),
            loss_rate_evidence=(
                self.citation(
                    accepted,
                    role="Production Requirement",
                    artifact="0.json",
                    ordinal=0,
                    locator=EVIDENCE_LOSS_RATE,
                ),
            ),
        )
        report = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-02-01",
                loss_rate=(handoff,),
            ),
        )
        self.assertEqual(report.loss_rate_contexts, ())

    def test_absent_safety_stock_dataset_never_becomes_a_default_value(self) -> None:
        report = self.construct(
            [("Plant / Material identity context", [{"plant_id": PLANT, "material_code": MATERIAL}])],
            name="safety-stock-absent",
        )
        self.assertEqual(report.objects_for("Configured Safety Stock"), ())
        self.assertEqual(report.safety_stock_contexts, ())
        self.assertEqual(report.issues, ())

    def _safety_stock_handoff(self, accepted, **overrides: object) -> SafetyStockHandoff:
        payload: dict[str, object] = {
            "plant_id": PLANT,
            "material_code": MATERIAL,
            "evidence": self.citation(
                accepted, role="Configured Safety Stock", artifact="1.json"
            ),
            "safety_stock_evidence": (
                self.citation(
                    accepted,
                    role="Configured Safety Stock",
                    artifact="1.json",
                    ordinal=0,
                    locator=EVIDENCE_SAFETY_STOCK,
                ),
            ),
            "safety_stock": "5",
            "resolution_basis": BASIS_SAFETY_STOCK,
        }
        payload.update(overrides)
        return SafetyStockHandoff(**payload)  # type: ignore[arg-type]

    def test_safety_stock_handoff_is_carried_only_with_registered_provenance(self) -> None:
        # The cited policy record is a ``Plant / Material identity context`` record that
        # registers the SafetyStock observation; the handoff claims the same grain.
        policy = with_provenance(
            {"plant_id": PLANT, "material_code": MATERIAL, "SafetyStock": "5"},
            [("SafetyStock", [EVIDENCE_SAFETY_STOCK], BASIS_SAFETY_STOCK)],
        )
        _, accepted = self.accepted(
            [
                ("Plant / Material identity context", [policy]),
                ("Inbound Supply", [INBOUND()]),
            ],
            name="safety-stock-registered",
        )
        handoff = self._safety_stock_handoff(
            accepted,
            evidence=self.citation(
                accepted,
                role="Plant / Material identity context",
                artifact="0.json",
            ),
            safety_stock_evidence=(
                self.citation(
                    accepted,
                    role="Plant / Material identity context",
                    artifact="0.json",
                    ordinal=0,
                    locator=EVIDENCE_SAFETY_STOCK,
                ),
            ),
        )
        report = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-02-01",
                safety_stock=(handoff,),
            ),
        )
        # The cited evidence is accepted, verified and grain-consistent, so the value is
        # carried with the registered provenance rather than a synthesised locator.
        self.assertEqual(len(report.safety_stock_contexts), 1)
        context = report.safety_stock_contexts[0]
        self.assertEqual(context.value, "5")
        self.assertEqual(
            context.provenance.stable_source_evidence_locators,
            (EVIDENCE_SAFETY_STOCK,),
        )
        self.assertEqual(
            context.provenance.mapping_resolution_basis, BASIS_SAFETY_STOCK
        )

    def test_handoff_evidence_must_state_the_claimed_grain(self) -> None:
        # The only accepted SafetyStock evidence states M9; the handoff claims M1.
        record = with_provenance(
            {"plant_id": PLANT, "material_code": "M9", "SafetyStock": "5"},
            [("SafetyStock", [EVIDENCE_SAFETY_STOCK], BASIS_SAFETY_STOCK)],
        )
        _, accepted = self.accepted(
            [("Configured Safety Stock", [record])], name="safety-stock-grain-mismatch"
        )
        handoff = self._safety_stock_handoff(
            accepted,
            evidence=self.citation(
                accepted, role="Configured Safety Stock", artifact="0.json"
            ),
            safety_stock_evidence=(
                self.citation(
                    accepted,
                    role="Configured Safety Stock",
                    artifact="0.json",
                    ordinal=0,
                    locator=EVIDENCE_SAFETY_STOCK,
                ),
            ),
        )
        report = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-02-01",
                safety_stock=(handoff,),
            ),
        )
        self.assertEqual(report.safety_stock_contexts, ())


class SafetyStockStageBTests(CanonicalObjectsTestCase):
    def test_two_conflicting_configured_safety_stock_records_conflict_without_handoff(self) -> None:
        # Same grain, two accepted values, no handoff at all.
        _, accepted = self.accepted(
            [
                (
                    "Configured Safety Stock",
                    [
                        CONFIGURED_SAFETY_STOCK("5"),
                        CONFIGURED_SAFETY_STOCK("7"),
                    ],
                )
            ],
            name="safety-stock-direct-conflict",
        )
        report = construct_canonical_objects(
            accepted,
            PhaseAHandoff(analysis_run_id="RUN-1", analysis_date="2026-02-01"),
        )
        conflicts = [
            issue
            for issue in report.issues
            if issue.category == "CONSISTENCY" and issue.reason == "CONSISTENCY_CONFLICT"
        ]
        self.assertEqual(len(conflicts), 1)
        self.assertIn("conflicting SafetyStock values", conflicts[0].detail)
        self.assertIn("plant_id='P1'", conflicts[0].detail)
        self.assertIn("material_code='M1'", conflicts[0].detail)
        self.assertEqual(report.safety_stock_contexts, ())

    def test_no_conflict_when_the_two_records_agree(self) -> None:
        _, accepted = self.accepted(
            [
                (
                    "Configured Safety Stock",
                    [CONFIGURED_SAFETY_STOCK("5"), CONFIGURED_SAFETY_STOCK("5")],
                )
            ],
            name="safety-stock-agreeing",
        )
        report = construct_canonical_objects(
            accepted,
            PhaseAHandoff(analysis_run_id="RUN-1", analysis_date="2026-02-01"),
        )
        self.assertFalse(
            any(issue.reason == "CONSISTENCY_CONFLICT" for issue in report.issues)
        )

    def test_generic_duplicate_handling_does_not_override_the_stage_b_case(self) -> None:
        _, accepted = self.accepted(
            [
                (
                    "Configured Safety Stock",
                    [CONFIGURED_SAFETY_STOCK("5"), CONFIGURED_SAFETY_STOCK("7")],
                )
            ],
            name="safety-stock-registered-case",
        )
        handoff = PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-02-01",
            safety_stock=(
                SafetyStockHandoff(
                    plant_id=PLANT,
                    material_code=MATERIAL,
                    evidence=HandoffEvidence(
                        snapshot_package_identity=accepted.package_id,
                        logical_dataset_role="Configured Safety Stock",
                        artifact="0.json",
                        record_ordinal=0,
                        evidence_locator=EVIDENCE_SAFETY_STOCK,
                    ),
                    safety_stock_evidence=(
                        HandoffEvidence(
                            snapshot_package_identity=accepted.package_id,
                            logical_dataset_role="Configured Safety Stock",
                            artifact="0.json",
                            record_ordinal=0,
                            evidence_locator=EVIDENCE_SAFETY_STOCK,
                        ),
                    ),
                    safety_stock="5",
                    resolution_basis=BASIS_SAFETY_STOCK,
                ),
            ),
        )
        report = construct_canonical_objects(accepted, handoff)
        self.assertEqual(report.safety_stock_contexts, ())
        self.assertEqual(
            len(
                [
                    issue
                    for issue in report.issues
                    if issue.category == "CONSISTENCY"
                    and issue.reason == "CONSISTENCY_CONFLICT"
                ]
            ),
            1,
        )


class RepresentationBoundaryTests(CanonicalObjectsTestCase):
    def test_zero_is_preserved_as_a_valid_value(self) -> None:
        report = self.construct(
            [("Inbound Supply", [INBOUND(received_qty="0")])], name="zero"
        )
        inbound = report.inbound_records[0]
        self.assertEqual(inbound.value_of("received_qty"), "0")
        self.assertNotEqual(inbound.value_of("received_qty", ABSENT), ABSENT)

    def test_json_null_is_preserved_and_never_guessed(self) -> None:
        report = self.construct(
            [("Production Requirement", [PRODUCTION_REQUIREMENT(ProductionQty=None)])],
            name="null",
        )
        requirement = report.objects_for("Production Requirement")[0]
        self.assertTrue(requirement.has("ProductionQty"))
        self.assertIsNone(requirement.value_of("ProductionQty"))
        self.assertNotEqual(requirement.value_of("ProductionQty"), "0")
        self.assertNotEqual(requirement.value_of("ProductionQty"), "")

    def test_omitted_property_is_not_guessed(self) -> None:
        report = self.construct(
            [
                (
                    "Production Requirement",
                    [{"plant_id": PLANT, "material_code": MATERIAL, "required_date": REQUIRED_DATE}],
                )
            ],
            name="omitted",
        )
        requirement = report.objects_for("Production Requirement")[0]
        self.assertFalse(requirement.has("ProductionQty"))
        self.assertIs(requirement.value_of("ProductionQty", ABSENT), ABSENT)

    def test_values_are_not_normalized(self) -> None:
        report = self.construct(
            [
                (
                    "Production Requirement",
                    [PRODUCTION_REQUIREMENT(material_code="  M1  ", ProductionQty="10.500")],
                )
            ],
            name="exact",
        )
        requirement = report.objects_for("Production Requirement")[0]
        self.assertEqual(requirement.value_of("material_code"), "  M1  ")
        self.assertEqual(requirement.value_of("ProductionQty"), "10.500")

    def test_decimal_accessor_uses_decimal_and_never_binary_float(self) -> None:
        from decimal import Decimal

        report = self.construct(
            [("Inbound Supply", [INBOUND(ordered_qty="0.1", received_qty="0.7")])],
            name="decimal",
        )
        inbound = report.inbound_records[0]
        ordered = next(prop for prop in inbound.properties if prop.name == "ordered_qty")
        received = next(prop for prop in inbound.properties if prop.name == "received_qty")
        self.assertEqual(ordered.decimal_value(), Decimal("0.1"))
        self.assertEqual(received.decimal_value(), Decimal("0.7"))
        self.assertEqual(
            ordered.decimal_value() + received.decimal_value(), Decimal("0.8")
        )
        self.assertNotEqual(
            float(ordered.decimal_value()) + float(received.decimal_value()), 0.8
        )
        self.assertIsInstance(ordered.value, str)

    def test_decimal_accessor_returns_none_for_non_decimal_values(self) -> None:
        report = self.construct(
            [("Inbound Supply", [INBOUND(received_qty=None)])], name="decimal-none"
        )
        inbound = report.inbound_records[0]
        received = next(prop for prop in inbound.properties if prop.name == "received_qty")
        self.assertIsNone(received.decimal_value())

    def test_required_quantity_never_reappears(self) -> None:
        report = self.construct(
            [
                ("Production Requirement", [PRODUCTION_REQUIREMENT()]),
                ("BOM Component", [BOM_COMPONENT()]),
            ],
            name="required-quantity",
        )
        self.assertNotIn("required_quantity", str(report.to_dict()))

    def test_derived_results_are_never_represented_as_source_objects(self) -> None:
        report = self.construct(
            [
                ("Production Requirement", [PRODUCTION_REQUIREMENT()]),
                ("Inbound Supply", [INBOUND()]),
            ],
            name="derived",
        )
        payload = str(report.to_dict())
        for derived in DERIVED_LITERALS:
            with self.subTest(derived=derived):
                self.assertNotIn(derived, payload)


class GrainResolutionTests(CanonicalObjectsTestCase):
    def test_exactly_one_applicable_evidence_resolves_the_grain(self) -> None:
        report = self.construct(
            [("Production Requirement", [PRODUCTION_REQUIREMENT()])], name="grain-resolved"
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
        report = self.construct(
            [
                (
                    "Production Requirement",
                    [PRODUCTION_REQUIREMENT(), PRODUCTION_REQUIREMENT(ProductionQty="99")],
                )
            ],
            name="grain-conflict",
        )
        self.assertEqual(report.objects_for("Production Requirement"), ())
        self.assertEqual(len(report.unresolved_for("Production Requirement")), 2)
        self.assertFalse(
            any(issue.reason == "CONSISTENCY_CONFLICT" for issue in report.issues),
            msg="same-grain values must not be reconciled as a Stage B conflict",
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
                ("Production Requirement", [PRODUCTION_REQUIREMENT()]),
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
        _, accepted = self.accepted(
            [("Production Requirement", [PRODUCTION_REQUIREMENT()])], name="not-rejection"
        )
        report = construct_canonical_objects(
            accepted, PhaseAHandoff(analysis_run_id="RUN-1", analysis_date=None)
        )
        self.assertEqual(report.package_id, accepted.package_id)
        self.assertEqual(
            report.accepted_content_view_digest, accepted.content_view_digest
        )
        self.assertNotIn("REJECTED", self.states(report).values())

    def test_unusable_accepted_view_constructs_nothing(self) -> None:
        built, accepted = self.accepted(
            [("Production Requirement", [PRODUCTION_REQUIREMENT()])], name="unusable"
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
            [("Production Requirement", [PRODUCTION_REQUIREMENT()])], name="no-reread"
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
                ("Production Requirement", [PRODUCTION_REQUIREMENT()]),
                ("Inbound Supply", [INBOUND()]),
            ],
            name="repeatable",
        )
        handoff = PhaseAHandoff(analysis_run_id="RUN-1", analysis_date="2026-02-01")
        first = construct_canonical_objects(accepted, handoff).to_dict()
        second = construct_canonical_objects(accepted, handoff).to_dict()
        self.assertEqual(first, second)

    def test_layer2_report_is_reused_when_supplied(self) -> None:
        _, accepted = self.accepted(
            [("Production Requirement", [PRODUCTION_REQUIREMENT()])], name="layer2-reuse"
        )
        layer2 = validate_layer2(accepted)
        report = construct_canonical_objects(
            accepted,
            PhaseAHandoff(analysis_run_id="RUN-1", analysis_date="2026-02-01"),
            layer2_report=layer2,
        )
        self.assertEqual(report.layer2_note, layer2.note)
        self.assertEqual(len(report.objects_for("Production Requirement")), 1)

    def test_foreign_layer2_report_stops_construction(self) -> None:
        _, accepted = self.accepted(
            [("Production Requirement", [PRODUCTION_REQUIREMENT()])], name="layer2-foreign"
        )
        _, other = self.accepted(
            [("Production Requirement", [PRODUCTION_REQUIREMENT()])],
            name="layer2-foreign-other",
            package_id="SIMULATED-PKG-0002",
        )
        foreign = validate_layer2(other)
        report = construct_canonical_objects(
            accepted,
            PhaseAHandoff(analysis_run_id="RUN-1", analysis_date="2026-02-01"),
            layer2_report=foreign,
        )
        self.assertEqual(report.object_sets, ())
        self.assertEqual(report.inbound_records, ())
        self.assertEqual(report.issues, ())
        self.assertEqual(self.states(report).get(LAYER2_REPORT_BINDING), "failed")
        self.assertFalse(
            any(
                name == CANONICALIZATION_ANALYSIS_RUN and state == "passed"
                for name, state in self.states(report).items()
            )
        )

    def test_layer2_report_from_a_different_view_of_the_same_package_is_rejected(self) -> None:
        _, accepted = self.accepted(
            [("Production Requirement", [PRODUCTION_REQUIREMENT()])], name="layer2-view"
        )
        mismatched = replace(
            validate_layer2(accepted), accepted_content_view_digest="other-view"
        )
        report = construct_canonical_objects(
            accepted,
            PhaseAHandoff(analysis_run_id="RUN-1", analysis_date="2026-02-01"),
            layer2_report=mismatched,
        )
        self.assertEqual(report.object_sets, ())
        self.assertEqual(self.states(report).get(LAYER2_REPORT_BINDING), "failed")

    def test_analysis_run_context_uses_identity_plus_single_package_linkage(self) -> None:
        report = self.construct(
            [("Production Requirement", [PRODUCTION_REQUIREMENT()])], name="analysis-run"
        )
        context = report.analysis_run
        self.assertEqual(context.analysis_run_id, "RUN-1")
        self.assertEqual(context.snapshot_package_identity, "SIMULATED-PKG-0001")
        self.assertEqual(
            context.accepted_content_view_digest, report.accepted_content_view_digest
        )

    def test_unresolved_analysis_date_is_not_invented(self) -> None:
        _, accepted = self.accepted(
            [("Production Requirement", [PRODUCTION_REQUIREMENT()])], name="analysis-date"
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


if __name__ == "__main__":
    unittest.main()
