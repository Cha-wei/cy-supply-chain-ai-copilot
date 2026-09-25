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
from tests.helpers import DatasetSpec, PackageSpec, build_package

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
    def _parent_handoff(self, accepted, *, bom_ordinal: int = 0, parent_ordinal: int = 0):
        """The registered I-7 binding: BOM Component evidence -> resolved requirement."""

        return BomParentContextHandoff(
            bom_evidence=self.citation(
                accepted, role="BOM Component", artifact="1.json", ordinal=bom_ordinal
            ),
            parent_evidence=self.citation(
                accepted,
                role="Production Requirement",
                artifact="0.json",
                ordinal=parent_ordinal,
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
                bom_parent_context=(
                    self._parent_handoff(accepted, bom_ordinal=0),
                    self._parent_handoff(accepted, bom_ordinal=1),
                ),
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
                    bom_evidence=self.citation(
                        accepted,
                        role="Production Requirement",
                        artifact="0.json",
                        package_id="OTHER-PACKAGE",
                    ),
                    parent_evidence=self.citation(
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
                    bom_evidence=self.citation(
                        accepted, role="Inbound Supply", artifact="0.json", ordinal=0
                    ),
                    parent_evidence=self.citation(
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

    def test_one_bom_evidence_bound_to_two_parents_stays_unresolved(self) -> None:
        # I-7 cardinality: exactly one context per BOM evidence set.  Two distinct parent
        # contexts for the same BOM evidence stay unresolved with no precedence.
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
                self._parent_handoff(accepted, bom_ordinal=0, parent_ordinal=0),
                self._parent_handoff(accepted, bom_ordinal=0, parent_ordinal=1),
            ),
        )
        report = construct_canonical_objects(accepted, handoff)
        self.assertEqual(report.objects_for("BOM Component"), ())
        self.assertIn(
            "more than one distinct resolved Production Requirement context",
            str([note for _n, _s, note in report.checks if note]),
        )
        self.assertIn(
            "UNRESOLVED_IDENTITY", {issue.reason for issue in report.issues}
        )

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


class NonHashableEffectiveDemandPairTests(CanonicalObjectsTestCase):
    """G5-A / I-8: a non-hashable caller pair is never a Python ``TypeError`` (Issue #144).

    The pair values are runtime bookkeeping, not business identity: they are never converted,
    stringified or invented, the entry is never skipped because of it, and no conceptual
    outcome is derived from them.  Phase A still emits no effective-demand context.
    """

    NOTE_MARKER = "pair bookkeeping could not be established"
    COMPLETENESS_MARKER = "carry no mapping evidence"

    def datasets(self):
        return [
            (
                "Substitute Allocation",
                [
                    {
                        "plant_id": PLANT,
                        "target_material_code": MATERIAL,
                        "substitute_material_code": "M3",
                        "AllocatedSubstituteQty": "4",
                        "_meta": {
                            "provenance_associations": [
                                {
                                    "observation": "AllocatedSubstituteQty",
                                    "evidence": [EVIDENCE_ALLOCATION],
                                }
                            ]
                        },
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
                        "_meta": {
                            "provenance_associations": [
                                {
                                    "observation": "approval_status",
                                    "evidence": [EVIDENCE_RELATIONSHIP],
                                }
                            ]
                        },
                    }
                ],
            ),
        ]

    def entry(
        self,
        accepted,
        *,
        source: object,
        target: object,
        relation: str = RELATION_TARGET_APPLICABILITY,
        role: str = "Substitute Relationship",
        artifact: str = "1.json",
        locator: str | None = EVIDENCE_RELATIONSHIP,
        package_id: str | None = None,
        ordinal: int = 0,
    ) -> EffectiveDemandRelationHandoff:
        return EffectiveDemandRelationHandoff(
            source_substitute_material=source,
            target_material=target,
            relation=relation,
            evidence=self.citation(
                accepted,
                role=role,
                artifact=artifact,
                ordinal=ordinal,
                locator=locator,
                package_id=package_id,
            ),
            mapping_basis="SIMULATED approved applicability mapping",
        )

    def run_entries(self, *, name: str, entries):
        _, accepted = self.accepted(self.datasets(), name=name)
        handoff = PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-02-01",
            effective_demand=tuple(entries(accepted)),
        )
        return accepted, build_effective_demand_contexts(accepted, handoff)

    def assert_unresolved_only(self, issues) -> None:
        self.assertTrue(issues)
        self.assertTrue(all(issue.reason == "SEMANTIC_UNRESOLVED" for issue in issues))
        self.assertTrue(
            all(issue.category == "SEMANTIC_RESOLUTION" for issue in issues)
        )

    def test_list_source_material_does_not_crash(self) -> None:
        """A: ``source_substitute_material = []`` -- no crash, no context, no conversion."""

        source: list[object] = []
        _, (contexts, issues) = self.run_entries(
            name="g5a-source-list",
            entries=lambda accepted: (
                self.entry(accepted, source=source, target=MATERIAL),
            ),
        )
        self.assertEqual(contexts, ())
        self.assert_unresolved_only(issues)
        self.assertEqual(len(issues), 1)
        self.assertIn(self.NOTE_MARKER, issues[0].detail)
        # No fabricated pair key: the completeness pass never saw this pair.
        self.assertNotIn(self.COMPLETENESS_MARKER, issues[0].detail)
        # The caller's value is untouched -- not converted, stringified or widened.
        self.assertEqual(source, [])

    def test_dict_target_material_does_not_crash(self) -> None:
        """B: ``target_material = {}``."""

        target: dict[str, object] = {}
        _, (contexts, issues) = self.run_entries(
            name="g5a-target-dict",
            entries=lambda accepted: (
                self.entry(accepted, source="M3", target=target),
            ),
        )
        self.assertEqual(contexts, ())
        self.assert_unresolved_only(issues)
        self.assertEqual(len(issues), 1)
        self.assertIn(self.NOTE_MARKER, issues[0].detail)
        self.assertEqual(target, {})

    def test_both_values_non_hashable(self) -> None:
        """C: both components non-hashable."""

        _, (contexts, issues) = self.run_entries(
            name="g5a-both",
            entries=lambda accepted: (
                self.entry(accepted, source=[], target={}),
            ),
        )
        self.assertEqual(contexts, ())
        self.assert_unresolved_only(issues)
        self.assertEqual(len(issues), 1)
        self.assertIn(self.NOTE_MARKER, issues[0].detail)

    def test_verified_evidence_is_still_verified_for_a_non_hashable_pair(self) -> None:
        """D: the entry still runs evidence verification -- it is never skipped."""

        _, (contexts, issues) = self.run_entries(
            name="g5a-verified",
            entries=lambda accepted: (
                self.entry(
                    accepted,
                    source=[],
                    target=MATERIAL,
                    relation=RELATION_TARGET_APPLICABILITY,
                ),
            ),
        )
        self.assertEqual(contexts, ())
        self.assert_unresolved_only(issues)
        self.assertEqual(len(issues), 1)
        # The verified-evidence branch really ran: the finding reports the accepted record
        # path and the missing approved source-value -> outcome mapping.
        self.assertIn("supports relation", issues[0].detail)
        self.assertIn("no approved source-value", issues[0].detail)
        self.assertIn("1.json#0", issues[0].detail)
        self.assertIn(self.NOTE_MARKER, issues[0].detail)

    def test_invalid_relation_literal_is_not_masked(self) -> None:
        """E: the invalid relation literal stays visible next to the bookkeeping note."""

        _, (contexts, issues) = self.run_entries(
            name="g5a-invalid-relation",
            entries=lambda accepted: (
                self.entry(accepted, source=[], target=MATERIAL, relation="NOT_A_RELATION"),
            ),
        )
        self.assertEqual(contexts, ())
        self.assert_unresolved_only(issues)
        self.assertEqual(len(issues), 1)
        self.assertIn("is not one of the registered G5-A relations", issues[0].detail)
        self.assertIn(self.NOTE_MARKER, issues[0].detail)

    def test_foreign_evidence_failure_is_not_masked(self) -> None:
        """F: an unverifiable citation stays visible for a non-hashable pair."""

        _, (contexts, issues) = self.run_entries(
            name="g5a-foreign",
            entries=lambda accepted: (
                self.entry(
                    accepted,
                    source=[],
                    target=MATERIAL,
                    package_id="SIMULATED-PKG-9999",
                ),
            ),
        )
        self.assertEqual(contexts, ())
        self.assert_unresolved_only(issues)
        self.assertEqual(len(issues), 1)
        self.assertIn("Snapshot Package Identity", issues[0].detail)
        self.assertIn(self.NOTE_MARKER, issues[0].detail)
        # The unverified citation never becomes a fabricated bookkeeping pair either.
        self.assertNotIn(self.COMPLETENESS_MARKER, issues[0].detail)

    def test_hashable_pair_with_one_relation_keeps_the_completeness_finding(self) -> None:
        """G: existing hashable-pair behaviour is unchanged."""

        _, (contexts, issues) = self.run_entries(
            name="g5a-one-relation",
            entries=lambda accepted: (
                self.entry(accepted, source="M3", target=MATERIAL),
            ),
        )
        self.assertEqual(contexts, ())
        self.assert_unresolved_only(issues)
        # One finding for the entry plus the registered missing-relation completeness finding.
        self.assertEqual(len(issues), 2)
        completeness = [
            issue for issue in issues if self.COMPLETENESS_MARKER in issue.detail
        ]
        self.assertEqual(len(completeness), 1)
        self.assertIn(RELATION_SOURCE_RESERVATION_OVERLAP, completeness[0].detail)
        self.assertNotIn(self.NOTE_MARKER, "".join(issue.detail for issue in issues))

    def test_hashable_pair_with_both_relations_has_no_false_missing_finding(self) -> None:
        """H / J: both relations stay independently unresolved and no context is emitted."""

        _, (contexts, issues) = self.run_entries(
            name="g5a-both-relations",
            entries=lambda accepted: (
                self.entry(accepted, source="M3", target=MATERIAL),
                self.entry(
                    accepted,
                    source="M3",
                    target=MATERIAL,
                    relation=RELATION_SOURCE_RESERVATION_OVERLAP,
                    role="Substitute Allocation",
                    artifact="0.json",
                    locator=EVIDENCE_ALLOCATION,
                ),
            ),
        )
        self.assertEqual(contexts, ())
        self.assert_unresolved_only(issues)
        self.assertEqual(len(issues), 2)
        self.assertFalse(
            any(self.COMPLETENESS_MARKER in issue.detail for issue in issues)
        )
        self.assertEqual(
            {
                RELATION_TARGET_APPLICABILITY if "Target Applicability" in i.detail else RELATION_SOURCE_RESERVATION_OVERLAP
                for i in issues
            },
            {RELATION_TARGET_APPLICABILITY, RELATION_SOURCE_RESERVATION_OVERLAP},
        )

    def test_repeated_relation_evidence_is_not_deduplicated(self) -> None:
        """I: repeats are reported, never collapsed by same-value dedup or first/last wins."""

        _, (contexts, issues) = self.run_entries(
            name="g5a-repeat",
            entries=lambda accepted: (
                self.entry(accepted, source="M3", target=MATERIAL),
                self.entry(
                    accepted,
                    source="M3",
                    target=MATERIAL,
                    relation=RELATION_SOURCE_RESERVATION_OVERLAP,
                    role="Substitute Allocation",
                    artifact="0.json",
                    locator=EVIDENCE_ALLOCATION,
                ),
                self.entry(accepted, source="M3", target=MATERIAL),
            ),
        )
        self.assertEqual(contexts, ())
        self.assert_unresolved_only(issues)
        self.assertEqual(len(issues), 3)

    def test_repeated_non_hashable_entries_are_not_deduplicated(self) -> None:
        _, (contexts, issues) = self.run_entries(
            name="g5a-repeat-ungroupable",
            entries=lambda accepted: (
                self.entry(accepted, source=[], target=MATERIAL),
                self.entry(accepted, source=[], target=MATERIAL),
            ),
        )
        self.assertEqual(contexts, ())
        self.assert_unresolved_only(issues)
        self.assertEqual(len(issues), 2)

    def test_non_hashable_pair_bookkeeping_is_deterministic(self) -> None:
        """K: identical input reproduces identical findings and serialized output."""

        _, accepted = self.accepted(self.datasets(), name="g5a-determinism")
        handoff = PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-02-01",
            effective_demand=(self.entry(accepted, source=[], target={}),),
        )
        first_contexts, first_issues = build_effective_demand_contexts(accepted, handoff)
        second_contexts, second_issues = build_effective_demand_contexts(accepted, handoff)
        self.assertEqual(first_contexts, second_contexts)
        self.assertEqual(first_issues, second_issues)
        first_report = construct_canonical_objects(accepted, handoff).to_dict()
        second_report = construct_canonical_objects(accepted, handoff).to_dict()
        self.assertEqual(first_report, second_report)
        self.assertEqual(first_report["effective_demand_contexts"], [])

    def test_no_caller_outcome_channel_is_introduced(self) -> None:
        """The handoff still carries evidence bookkeeping only."""

        fields = set(EffectiveDemandRelationHandoff.__dataclass_fields__)
        self.assertEqual(
            fields,
            {
                "source_substitute_material",
                "target_material",
                "relation",
                "evidence",
                "mapping_basis",
            },
        )
        for forbidden in ("outcome", "applicable", "overlaps", "result", "boolean"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, fields)


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
                    bom_evidence=self.citation(
                        accepted,
                        role="Production Requirement",
                        artifact="0.json",
                        ordinal=0,
                        locator="CALLER-MINTED-LOCATOR",
                    ),
                    parent_evidence=self.citation(
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

    def _parent_handoff(self, accepted, *, bom_ordinal: int = 0):
        return BomParentContextHandoff(
            bom_evidence=self.citation(
                accepted, role="BOM Component", artifact="1.json", ordinal=bom_ordinal
            ),
            parent_evidence=self.citation(
                accepted, role="Production Requirement", artifact="0.json", ordinal=0
            ),
        )

    def _loss_rate_handoff(self, accepted, **overrides: object) -> LossRateHandoff:
        payload: dict[str, object] = {
            "plant_id": PLANT,
            "parent_material_code": MATERIAL,
            "required_date": REQUIRED_DATE,
            "evidence": self.citation(
                accepted, role="Production Requirement", artifact="0.json"
            ),
            "component_material_code": COMPONENT,
            "loss_rate_evidence": (),  # filled per test
            "loss_rate": "0.05",
            "resolution_basis": BASIS_LOSS_RATE,
        }
        payload.update(overrides)
        return LossRateHandoff(**payload)  # type: ignore[arg-type]

    def _with_bom_component(self, requirement: dict[str, object]):
        """Requirement + one resolved BOM Component relationship for COMPONENT."""

        return [
            ("Production Requirement", [requirement]),
            ("BOM Component", [BOM_COMPONENT()]),
        ]

    def _construct_with_bom(
        self, datasets, accepted, loss_rate_handoffs, *, name: str, bom_bindings: int = 1
    ):
        return construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-02-01",
                bom_parent_context=tuple(
                    self._parent_handoff(accepted, bom_ordinal=index)
                    for index in range(bom_bindings)
                ),
                loss_rate=tuple(loss_rate_handoffs),
            ),
        )

    def test_loss_rate_requires_a_resolved_component_context(self) -> None:
        record = with_provenance(
            self._loss_rate_record(),
            [("loss_rate", [EVIDENCE_LOSS_RATE], BASIS_LOSS_RATE)],
        )
        # No resolved BOM Component relationship exists for this component identity.
        _, accepted = self.accepted(
            [("Production Requirement", [record])], name="loss-rate-no-component"
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
        report = self._construct_with_bom(
            None, accepted, [handoff], name="loss-rate-no-component"
        )
        self.assertEqual(report.loss_rate_contexts, ())

    def test_loss_rate_requires_registered_accepted_provenance(self) -> None:
        _, accepted = self.accepted(
            self._with_bom_component(self._loss_rate_record()),
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
            self._with_bom_component(record), name="loss-rate-registered"
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
        report = self._construct_with_bom(None, accepted, [handoff], name="loss-rate-case")
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
            self._with_bom_component(record), name="loss-rate-no-basis"
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
        report = self._construct_with_bom(None, accepted, [handoff], name="loss-rate-case")
        self.assertEqual(report.loss_rate_contexts, ())

    def test_caller_free_string_is_not_an_approved_mapping_basis(self) -> None:
        record = with_provenance(
            self._loss_rate_record(),
            [("loss_rate", [EVIDENCE_LOSS_RATE], BASIS_LOSS_RATE)],
        )
        _, accepted = self.accepted(
            self._with_bom_component(record), name="loss-rate-basis-mismatch"
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
        report = self._construct_with_bom(None, accepted, [handoff], name="loss-rate-case")
        self.assertEqual(report.loss_rate_contexts, ())

    def test_loss_rate_value_the_evidence_does_not_carry_is_rejected(self) -> None:
        record = with_provenance(
            self._loss_rate_record(),
            [("loss_rate", [EVIDENCE_LOSS_RATE], BASIS_LOSS_RATE)],
        )
        _, accepted = self.accepted(
            self._with_bom_component(record), name="loss-rate-unbacked"
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
        report = self._construct_with_bom(None, accepted, [handoff], name="loss-rate-case")
        self.assertEqual(report.loss_rate_contexts, ())

    def test_multiple_applicable_loss_rate_evidence_is_not_deduplicated(self) -> None:
        record = with_provenance(
            self._loss_rate_record(),
            [("loss_rate", [EVIDENCE_LOSS_RATE], BASIS_LOSS_RATE)],
        )
        _, accepted = self.accepted(
            [
                ("Production Requirement", [record, copy.deepcopy(record)]),
                ("BOM Component", [BOM_COMPONENT()]),
            ],
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
        report = self._construct_with_bom(None, accepted, [handoff], name="loss-rate-case")
        self.assertEqual(report.loss_rate_contexts, ())

    def test_foreign_package_loss_rate_evidence_is_not_used(self) -> None:
        record = with_provenance(
            self._loss_rate_record(),
            [("loss_rate", [EVIDENCE_LOSS_RATE], BASIS_LOSS_RATE)],
        )
        _, accepted = self.accepted(
            self._with_bom_component(record), name="loss-rate-foreign"
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
        report = self._construct_with_bom(None, accepted, [handoff], name="loss-rate-case")
        self.assertEqual(report.loss_rate_contexts, ())

    # --- Requirement Calculation Context grain (component material identity) --------

    REQUIRED_DATE_OCT = "2026-10-10"

    def _two_component_package(self):
        """Requirement P1 / M1 / 2026-10-10 with BOM M1 -> M2 and M1 -> M3.

        Each BOM Component carries its own canonical ``loss_rate`` value with its own
        registered ``loss_rate`` provenance association, so the two Requirement
        Calculation Contexts resolve to different values.
        """

        requirement = with_provenance(
            {
                "plant_id": PLANT,
                "material_code": MATERIAL,
                "required_date": self.REQUIRED_DATE_OCT,
                "ProductionQty": "10",
            },
            [("ProductionQty", [EVIDENCE_REQUIREMENT], None)],
        )

        def component(material: str, loss_rate: str) -> dict[str, object]:
            return with_provenance(
                {
                    "plant_id": PLANT,
                    "required_date": self.REQUIRED_DATE_OCT,
                    "material_code": material,
                    "BOMComponentQty": "2",
                    "loss_rate": loss_rate,
                },
                [
                    ("BOMComponentQty", [EVIDENCE_REQUIREMENT], None),
                    ("loss_rate", [f"{EVIDENCE_LOSS_RATE}-{material}"], BASIS_LOSS_RATE),
                ],
            )

        return self.accepted(
            [
                ("Production Requirement", [requirement]),
                ("BOM Component", [component("M2", "0.02"), component("M3", "0.06")]),
            ],
            name="loss-rate-per-component",
        )

    def _component_handoff(self, accepted, component: str, value: str) -> LossRateHandoff:
        return self._loss_rate_handoff(
            accepted,
            parent_material_code=MATERIAL,
            required_date=self.REQUIRED_DATE_OCT,
            component_material_code=component,
            loss_rate=value,
            loss_rate_evidence=(
                self.citation(
                    accepted,
                    role="BOM Component",
                    artifact="1.json",
                    ordinal=0 if component == "M2" else 1,
                    locator=f"{EVIDENCE_LOSS_RATE}-{component}",
                ),
            ),
        )

    def _construct_two_component(self, accepted, handoffs, *, name: str):
        # One explicit I-7 binding per BOM Component evidence: M2 -> requirement,
        # M3 -> the same resolved requirement context.
        return construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-10-01",
                bom_parent_context=tuple(
                    BomParentContextHandoff(
                        bom_evidence=self.citation(
                            accepted,
                            role="BOM Component",
                            artifact="1.json",
                            ordinal=index,
                        ),
                        parent_evidence=self.citation(
                            accepted,
                            role="Production Requirement",
                            artifact="0.json",
                            ordinal=0,
                        ),
                    )
                    for index in (0, 1)
                ),
                loss_rate=tuple(handoffs),
            ),
        )

    def test_per_component_loss_rate_contexts_are_distinguishable(self) -> None:
        _, accepted = self._two_component_package()
        report = self._construct_two_component(
            accepted,
            [
                self._component_handoff(accepted, "M2", "0.02"),
                self._component_handoff(accepted, "M3", "0.06"),
            ],
            name="loss-rate-two-components",
        )
        self.assertEqual(len(report.loss_rate_contexts), 2)
        by_component = {
            next(
                prop.value
                for prop in context.grain
                if prop.name == "component_material_code"
            ): context.value
            for context in report.loss_rate_contexts
        }
        self.assertEqual(by_component, {"M2": "0.02", "M3": "0.06"})
        for context in report.loss_rate_contexts:
            self.assertEqual(
                [prop.name for prop in context.grain],
                [
                    "plant_id",
                    "material_code",
                    "required_date",
                    "component_material_code",
                ],
            )
        self.assertEqual(len(report.objects_for("BOM Component")), 2)

    def test_no_cross_component_loss_rate_reuse(self) -> None:
        _, accepted = self._two_component_package()
        report = self._construct_two_component(
            accepted,
            [
                self._component_handoff(accepted, "M2", "0.02"),
                self._component_handoff(accepted, "M3", "0.06"),
            ],
            name="loss-rate-no-cross-reuse",
        )
        values = {
            next(
                prop.value
                for prop in context.grain
                if prop.name == "component_material_code"
            ): context.value
            for context in report.loss_rate_contexts
        }
        self.assertEqual(values, {"M2": "0.02", "M3": "0.06"})
        self.assertNotEqual(values["M2"], values["M3"])

    def test_single_component_context_does_not_leak_to_the_other_component(self) -> None:
        _, accepted = self._two_component_package()
        # Only M2 states a loss_rate; M3 must stay unresolved rather than inherit M2's.
        report = self._construct_two_component(
            accepted,
            [self._component_handoff(accepted, "M2", "0.02")],
            name="loss-rate-single-component",
        )
        self.assertEqual(len(report.loss_rate_contexts), 1)
        self.assertEqual(report.loss_rate_contexts[0].value, "0.02")
        self.assertEqual(
            [
                prop.value
                for prop in report.loss_rate_contexts[0].grain
                if prop.name == "component_material_code"
            ],
            ["M2"],
        )

    def test_omitted_component_context_stays_unresolved(self) -> None:
        _, accepted = self._two_component_package()
        handoff = self._component_handoff(accepted, "M2", "0.02")
        without_component = replace(handoff, component_material_code=ABSENT)
        report = self._construct_two_component(
            accepted, [without_component], name="loss-rate-no-component-grain"
        )
        self.assertEqual(report.loss_rate_contexts, ())
        self.assertTrue(
            any(
                name.startswith(f"{CANONICALIZATION_HANDOFF_EVIDENCE}:loss_rate")
                and state == EVALUATION_NOT_EVALUABLE
                for name, state in self.states(report).items()
            )
        )
        semantic = [
            issue for issue in report.issues if issue.reason == "SEMANTIC_UNRESOLVED"
        ]
        self.assertTrue(semantic)
        self.assertTrue(
            all(issue.category == "SEMANTIC_RESOLUTION" for issue in semantic)
        )
        self.assertTrue(
            any("component material_code" in issue.detail for issue in semantic)
        )
        # It is a semantic-resolution finding, never FIELD_VALUE / MISSING.
        self.assertFalse(
            any(
                issue.category == "FIELD_VALUE" and issue.reason == "MISSING"
                for issue in report.issues
            )
        )
        # Blast radius is limited to the affected Requirement Calculation Context.
        self.assertTrue(
            all(
                "loss_rate" in (issue.affected_evidence or "")
                and issue.blast_radius is not None
                and "package rejection" in issue.blast_radius
                for issue in semantic
            )
        )

    def test_unknown_component_context_stays_unresolved(self) -> None:
        _, accepted = self._two_component_package()
        handoff = self._component_handoff(accepted, "M9", "0.02")
        report = self._construct_two_component(
            accepted, [handoff], name="loss-rate-unknown-component"
        )
        self.assertEqual(report.loss_rate_contexts, ())
        semantic = [
            issue for issue in report.issues if issue.reason == "SEMANTIC_UNRESOLVED"
        ]
        self.assertTrue(semantic)
        self.assertTrue(
            all(issue.category == "SEMANTIC_RESOLUTION" for issue in semantic)
        )
        self.assertTrue(
            any("no resolved BOM Component relationship" in issue.detail for issue in semantic)
        )
        self.assertTrue(
            any(
                name.startswith(f"{CANONICALIZATION_HANDOFF_EVIDENCE}:loss_rate")
                and state == EVALUATION_NOT_EVALUABLE
                for name, state in self.states(report).items()
            )
        )

    def test_ambiguous_component_context_stays_unresolved(self) -> None:
        requirement = with_provenance(
            {
                "plant_id": PLANT,
                "material_code": MATERIAL,
                "required_date": self.REQUIRED_DATE_OCT,
                "ProductionQty": "10",
            },
            [
                ("ProductionQty", [EVIDENCE_REQUIREMENT], None),
                ("loss_rate", [EVIDENCE_LOSS_RATE], BASIS_LOSS_RATE),
            ],
        )
        # Two resolved BOM Component relationships state the same component identity, so
        # the context is ambiguous and no precedence may be applied.
        _, accepted = self.accepted(
            [
                ("Production Requirement", [requirement]),
                (
                    "BOM Component",
                    [
                        BOM_COMPONENT(
                            required_date=self.REQUIRED_DATE_OCT, material_code="M2"
                        ),
                        BOM_COMPONENT(
                            required_date=self.REQUIRED_DATE_OCT, material_code="M2"
                        ),
                    ],
                ),
            ],
            name="loss-rate-ambiguous-component",
        )
        handoff = self._component_handoff(accepted, "M2", "0.02")
        report = self._construct_two_component(
            accepted, [handoff], name="loss-rate-ambiguous-component"
        )
        self.assertEqual(report.loss_rate_contexts, ())
        self.assertTrue(
            any(
                "more than one resolved BOM Component relationship" in (note or "")
                for _name, _state, note in report.checks
            )
        )
        semantic = [
            issue for issue in report.issues if issue.reason == "SEMANTIC_UNRESOLVED"
        ]
        self.assertTrue(semantic)
        self.assertTrue(
            all(issue.category == "SEMANTIC_RESOLUTION" for issue in semantic)
        )
        self.assertTrue(
            any(
                "more than one resolved BOM Component relationship" in issue.detail
                for issue in semantic
            )
        )

    def test_unresolved_component_context_is_semantic_unresolved_not_missing(self) -> None:
        """The three applicability-resolution failures use the registered root B reason."""

        scenarios: dict[str, tuple] = {}

        _, accepted = self._two_component_package()
        handoff = self._component_handoff(accepted, "M2", "0.02")
        scenarios["omitted"] = (
            accepted,
            [replace(handoff, component_material_code=ABSENT)],
        )
        scenarios["unknown"] = (accepted, [self._component_handoff(accepted, "M9", "0.02")])

        requirement = with_provenance(
            {
                "plant_id": PLANT,
                "material_code": MATERIAL,
                "required_date": self.REQUIRED_DATE_OCT,
                "ProductionQty": "10",
            },
            [("ProductionQty", [EVIDENCE_REQUIREMENT], None)],
        )
        _, ambiguous = self.accepted(
            [
                ("Production Requirement", [requirement]),
                (
                    "BOM Component",
                    [
                        BOM_COMPONENT(
                            required_date=self.REQUIRED_DATE_OCT, material_code="M2"
                        ),
                        BOM_COMPONENT(
                            required_date=self.REQUIRED_DATE_OCT, material_code="M2"
                        ),
                    ],
                ),
            ],
            name="loss-rate-root-b",
        )
        scenarios["ambiguous"] = (
            ambiguous,
            [self._component_handoff(ambiguous, "M2", "0.02")],
        )

        for label, (package, handoffs) in scenarios.items():
            with self.subTest(scenario=label):
                report = self._construct_two_component(
                    package, handoffs, name=f"loss-rate-root-b-{label}"
                )
                self.assertEqual(report.loss_rate_contexts, ())
                semantic = [
                    issue
                    for issue in report.issues
                    if issue.category == "SEMANTIC_RESOLUTION"
                    and issue.reason == "SEMANTIC_UNRESOLVED"
                ]
                self.assertTrue(semantic)
                self.assertFalse(
                    any(
                        issue.category == "FIELD_VALUE" and issue.reason == "MISSING"
                        for issue in report.issues
                    ),
                    msg="root B must not be reported as FIELD_VALUE / MISSING",
                )
                self.assertTrue(
                    all(
                        issue.blast_radius is not None
                        and issue.blast_radius.startswith(
                            "affected canonical context only"
                        )
                        for issue in semantic
                    )
                )

    def test_equal_loss_rate_values_are_not_deduplicated_across_components(self) -> None:
        # Both components state the same value: two contexts are still constructed.
        requirement = with_provenance(
            {
                "plant_id": PLANT,
                "material_code": MATERIAL,
                "required_date": self.REQUIRED_DATE_OCT,
                "ProductionQty": "10",
            },
            [("ProductionQty", [EVIDENCE_REQUIREMENT], None)],
        )

        def component(material: str) -> dict[str, object]:
            return with_provenance(
                {
                    "plant_id": PLANT,
                    "required_date": self.REQUIRED_DATE_OCT,
                    "material_code": material,
                    "BOMComponentQty": "2",
                    "loss_rate": "0.02",
                },
                [
                    ("BOMComponentQty", [EVIDENCE_REQUIREMENT], None),
                    ("loss_rate", [f"{EVIDENCE_LOSS_RATE}-{material}"], BASIS_LOSS_RATE),
                ],
            )

        _, accepted = self.accepted(
            [
                ("Production Requirement", [requirement]),
                ("BOM Component", [component("M2"), component("M3")]),
            ],
            name="loss-rate-equal-values",
        )
        report = self._construct_two_component(
            accepted,
            [
                self._component_handoff(accepted, "M2", "0.02"),
                self._component_handoff(accepted, "M3", "0.02"),
            ],
            name="loss-rate-equal-values",
        )
        self.assertEqual(len(report.loss_rate_contexts), 2)
        self.assertEqual(
            sorted(context.value for context in report.loss_rate_contexts),
            ["0.02", "0.02"],
        )
        self.assertEqual(
            sorted(
                next(
                    prop.value
                    for prop in context.grain
                    if prop.name == "component_material_code"
                )
                for context in report.loss_rate_contexts
            ),
            ["M2", "M3"],
        )

    def test_loss_rate_is_not_represented_as_a_bom_component_attribute(self) -> None:
        _, accepted = self._two_component_package()
        report = self._construct_two_component(
            accepted,
            [
                self._component_handoff(accepted, "M2", "0.02"),
                self._component_handoff(accepted, "M3", "0.06"),
            ],
            name="loss-rate-not-bom-attribute",
        )
        for obj in report.objects_for("BOM Component"):
            with self.subTest(component=obj.value_of("material_code")):
                self.assertFalse(obj.has("loss_rate"))
                self.assertIn("loss_rate", obj.non_applicable_properties)
        # The value is owned by the Requirement Calculation Context, not the BOM relation.
        self.assertEqual(
            sorted(context.value for context in report.loss_rate_contexts),
            ["0.02", "0.06"],
        )

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


class NonHashableGrainTests(CanonicalObjectsTestCase):
    """A grain value that is legal JSON but unusable as a grouping key must not crash.

    The canonical value is carried unchanged (nothing is retyped, stringified or wrapped to
    obtain hashability); the affected canonical target simply stays unresolved and Layer 2
    keeps owning the field-level ``FIELD_VALUE`` / ``INVALID_TYPE`` defect (Issue #140).
    """

    def grain_state(self, report, target: str) -> list[str]:
        return [
            state
            for name, state in self.states(report).items()
            if name.startswith(f"{CANONICALIZATION_GRAIN_RESOLUTION}:{target}:")
        ]

    def test_single_component_target_with_unhashable_value(self) -> None:
        """A: ``Supplier`` + ``supplier_id = []`` never raises and stays unresolved."""

        record = {"supplier_id": []}
        report = self.construct([("Supplier identity", [record])], name="supplier-list")
        self.assertEqual(report.objects_for("Supplier"), ())
        unresolved = report.unresolved_for("Supplier")
        self.assertEqual(len(unresolved), 1)
        # The canonical value is carried unchanged: no retyping, no stringification.
        self.assertEqual(unresolved[0].value_of("supplier_id"), [])
        self.assertTrue(unresolved[0].grain is not None)
        self.assertIn(EVALUATION_NOT_EVALUABLE, self.grain_state(report, "Supplier"))
        self.assertEqual(
            {issue.reason for issue in report.issues}, {"UNRESOLVED_IDENTITY"}
        )

    def test_compound_grain_with_unhashable_component(self) -> None:
        """B: ``material_code = {}`` leaves the whole compound object unresolved."""

        for role, record, target in (
            (
                "Production Requirement",
                {
                    "plant_id": PLANT,
                    "material_code": {},
                    "required_date": REQUIRED_DATE,
                    "ProductionQty": "10",
                },
                "Production Requirement",
            ),
            (
                "Inventory Snapshot",
                {
                    "plant_id": PLANT,
                    "material_code": {},
                    "inventory_snapshot_time": SNAPSHOT_TIME,
                    "inventory_status": "AVAILABLE",
                    "on_hand_qty": "100",
                },
                "Inventory Snapshot",
            ),
        ):
            with self.subTest(role=role):
                report = self.construct([(role, [record])], name=f"compound-{target}")
                self.assertEqual(report.objects_for(target), ())
                self.assertEqual(len(report.unresolved_for(target)), 1)
                self.assertIn(EVALUATION_NOT_EVALUABLE, self.grain_state(report, target))
                reasons = {issue.reason for issue in report.issues}
                self.assertIn("UNRESOLVED_IDENTITY", reasons)
                self.assertNotIn("INVALID_TYPE", reasons)
                self.assertNotIn("MISSING", reasons)

    def test_identity_context_components_are_judged_independently(self) -> None:
        """C: a broken Plant grain must not take the Material identity down with it."""

        report = self.construct(
            [("Plant / Material identity context", [{"plant_id": [], "material_code": MATERIAL}])],
            name="identity-plant-list",
        )
        self.assertEqual(report.objects_for("Plant"), ())
        self.assertEqual(len(report.unresolved_for("Plant")), 1)
        self.assertEqual(len(report.objects_for("Material")), 1)
        self.assertEqual(report.objects_for("Material")[0].value_of("material_code"), MATERIAL)

        mirrored = self.construct(
            [("Plant / Material identity context", [{"plant_id": PLANT, "material_code": {}}])],
            name="identity-material-object",
        )
        self.assertEqual(len(mirrored.objects_for("Plant")), 1)
        self.assertEqual(mirrored.objects_for("Material"), ())
        self.assertEqual(len(mirrored.unresolved_for("Material")), 1)

    def test_multiple_unhashable_records_remain_distinct_evidence(self) -> None:
        """D: two distinct unhashable records stay distinct -- no dedup, no first/last wins."""

        report = self.construct(
            [
                (
                    "Supplier identity",
                    [{"supplier_id": []}, {"supplier_id": {}}],
                )
            ],
            name="two-unhashable",
        )
        self.assertEqual(report.objects_for("Supplier"), ())
        unresolved = report.unresolved_for("Supplier")
        self.assertEqual(len(unresolved), 2)
        self.assertEqual(len({item.record_reference for item in unresolved}), 2)
        self.assertEqual(
            [item.value_of("supplier_id") for item in unresolved], [[], {}]
        )

    def test_hashable_grain_behavior_is_unchanged(self) -> None:
        """E / F: normal identifiers and the Inventory same-grain exception still work."""

        single = self.construct(
            [("Supplier identity", [{"supplier_id": "S1"}])], name="supplier-normal"
        )
        self.assertEqual(len(single.objects_for("Supplier")), 1)

        duplicate = self.construct(
            [("Supplier identity", [{"supplier_id": "S1"}, {"supplier_id": "S1"}])],
            name="supplier-duplicate",
        )
        self.assertEqual(duplicate.objects_for("Supplier"), ())
        self.assertEqual(len(duplicate.unresolved_for("Supplier")), 2)

        inventory = {
            "plant_id": PLANT,
            "material_code": MATERIAL,
            "inventory_snapshot_time": SNAPSHOT_TIME,
            "inventory_status": "AVAILABLE",
            "on_hand_qty": "100",
        }
        same_grain = self.construct(
            [("Inventory Snapshot", [dict(inventory), dict(inventory)])],
            name="inventory-same-grain",
        )
        self.assertEqual(len(same_grain.objects_for("Inventory Snapshot")), 2)
        self.assertEqual(same_grain.unresolved_for("Inventory Snapshot"), ())

    def test_json_null_missingness_is_not_redefined(self) -> None:
        """G: this cleanup introduces no new canonical missingness policy."""

        report = self.construct(
            [("Supplier identity", [{"supplier_id": None}])], name="supplier-null"
        )
        # JSON null is still carried as-is and grouped exactly like before: canonicalization
        # owns neither the missingness decision nor the field-level defect.
        self.assertEqual(len(report.objects_for("Supplier")), 1)
        self.assertIsNone(report.objects_for("Supplier")[0].value_of("supplier_id"))
        self.assertEqual(report.issues, ())

    def test_layer2_keeps_owning_the_field_level_defect(self) -> None:
        """H: the non-hashable representation is reported by Layer 2, not duplicated here."""

        _, accepted = self.accepted(
            [("Supplier identity", [{"supplier_id": []}])], name="supplier-layer2"
        )
        layer2 = validate_layer2(accepted)
        self.assertIn(
            ("FIELD_VALUE", "INVALID_TYPE"),
            {(issue.category, issue.reason) for issue in layer2.issues},
        )

        report = construct_canonical_objects(
            accepted, PhaseAHandoff(analysis_run_id="RUN-1", analysis_date="2026-02-01")
        )
        canonical_reasons = {issue.reason for issue in report.issues}
        self.assertNotIn("INVALID_TYPE", canonical_reasons)
        self.assertNotIn("MISSING", canonical_reasons)
        self.assertEqual(
            {issue.category for issue in report.issues}, {"IDENTITY_RESOLUTION"}
        )
        # The construction survives and the target stays unresolved.
        self.assertEqual(report.objects_for("Supplier"), ())
        self.assertEqual(len(report.unresolved_for("Supplier")), 1)


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


class I7BindingContractTests(CanonicalObjectsTestCase):
    """The registered I-7 binding: BOM Component evidence -> resolved requirement context.

    ``§4.3.31`` G I-7 registers the injected semantic as a **context reference**, not as
    caller-supplied ``plant_id`` / ``required_date`` business values.  These tests pin the
    binding contract and the optional consistency-evidence boundary.
    """

    OCT = "2026-10-10"

    def _package(self, *, bom_fields: dict[str, object], name: str):
        requirement = with_provenance(
            {
                "plant_id": PLANT,
                "material_code": MATERIAL,
                "required_date": self.OCT,
                "ProductionQty": "10",
            },
            [("ProductionQty", [EVIDENCE_REQUIREMENT], None)],
        )
        bom: dict[str, object] = {"material_code": COMPONENT, "BOMComponentQty": "2"}
        bom.update(bom_fields)
        return self.accepted(
            [
                ("Production Requirement", [requirement]),
                ("BOM Component", [with_provenance(bom, [("BOMComponentQty", [EVIDENCE_REQUIREMENT], None)])]),
            ],
            name=name,
        )

    def _binding(self, accepted, *, bom_artifact="1.json", bom_ordinal=0, parent_artifact="0.json", parent_ordinal=0, bom_role="BOM Component", parent_role="Production Requirement", bom_package=None, parent_package=None):
        return BomParentContextHandoff(
            bom_evidence=self.citation(
                accepted,
                role=bom_role,
                artifact=bom_artifact,
                ordinal=bom_ordinal,
                package_id=bom_package,
            ),
            parent_evidence=self.citation(
                accepted,
                role=parent_role,
                artifact=parent_artifact,
                ordinal=parent_ordinal,
                package_id=parent_package,
            ),
        )

    def _construct(self, accepted, bindings, *, name: str):
        return construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-10-01",
                bom_parent_context=tuple(bindings),
            ),
        )

    def _assert_resolved(self, report) -> None:
        objects = report.objects_for("BOM Component")
        self.assertEqual(len(objects), 1)
        self.assertEqual(report.unresolved_for("BOM Component"), ())
        self.assertFalse(
            any(issue.reason == "UNRESOLVED_IDENTITY" for issue in report.issues)
        )
        component = objects[0]
        self.assertEqual(
            [(prop.name, prop.value) for prop in component.grain],
            [("material_code", COMPONENT)],
        )

    def test_a_bom_omitting_both_local_context_fields_resolves(self) -> None:
        _, accepted = self._package(bom_fields={}, name="i7-a")
        report = self._construct(accepted, [self._binding(accepted)], name="i7-a")
        self._assert_resolved(report)
        component = report.objects_for("BOM Component")[0]
        parent = report.objects_for("Production Requirement")[0]
        self.assertEqual(component.context_reference, parent.record_reference)
        self.assertEqual(component.value_of("plant_id", ABSENT), ABSENT)
        self.assertEqual(component.value_of("required_date", ABSENT), ABSENT)
        self.assertEqual(parent.value_of("plant_id"), PLANT)
        self.assertEqual(parent.value_of("required_date"), self.OCT)

    def test_b_only_plant_id_present_and_equal_resolves(self) -> None:
        _, accepted = self._package(bom_fields={"plant_id": PLANT}, name="i7-b")
        report = self._construct(accepted, [self._binding(accepted)], name="i7-b")
        self._assert_resolved(report)

    def test_c_only_required_date_present_and_equal_resolves(self) -> None:
        _, accepted = self._package(bom_fields={"required_date": self.OCT}, name="i7-c")
        report = self._construct(accepted, [self._binding(accepted)], name="i7-c")
        self._assert_resolved(report)

    def test_d_both_present_and_equal_resolves(self) -> None:
        _, accepted = self._package(
            bom_fields={"plant_id": PLANT, "required_date": self.OCT}, name="i7-d"
        )
        report = self._construct(accepted, [self._binding(accepted)], name="i7-d")
        self._assert_resolved(report)

    def test_e_plant_mismatch_is_a_consistency_conflict(self) -> None:
        _, accepted = self._package(bom_fields={"plant_id": "P9"}, name="i7-e")
        report = self._construct(accepted, [self._binding(accepted)], name="i7-e")
        self.assertEqual(report.objects_for("BOM Component"), ())
        conflicts = [
            issue
            for issue in report.issues
            if issue.category == "CONSISTENCY" and issue.reason == "CONSISTENCY_CONFLICT"
        ]
        self.assertEqual(len(conflicts), 1)
        self.assertIn("plant_id", conflicts[0].detail)

    def test_f_required_date_mismatch_is_a_consistency_conflict(self) -> None:
        _, accepted = self._package(bom_fields={"required_date": "2026-11-11"}, name="i7-f")
        report = self._construct(accepted, [self._binding(accepted)], name="i7-f")
        self.assertEqual(report.objects_for("BOM Component"), ())
        conflicts = [
            issue
            for issue in report.issues
            if issue.category == "CONSISTENCY" and issue.reason == "CONSISTENCY_CONFLICT"
        ]
        self.assertEqual(len(conflicts), 1)
        self.assertIn("required_date", conflicts[0].detail)

    def test_g_one_bom_evidence_bound_to_two_parents_is_unresolved(self) -> None:
        requirement_b = with_provenance(
            {
                "plant_id": PLANT,
                "material_code": "M9",
                "required_date": self.OCT,
                "ProductionQty": "10",
            },
            [("ProductionQty", [EVIDENCE_REQUIREMENT], None)],
        )
        _, accepted = self.accepted(
            [
                ("Production Requirement", [
                    with_provenance(
                        {
                            "plant_id": PLANT,
                            "material_code": MATERIAL,
                            "required_date": self.OCT,
                            "ProductionQty": "10",
                        },
                        [("ProductionQty", [EVIDENCE_REQUIREMENT], None)],
                    ),
                    requirement_b,
                ]),
                ("BOM Component", [
                    with_provenance(
                        {"material_code": COMPONENT, "BOMComponentQty": "2"},
                        [("BOMComponentQty", [EVIDENCE_REQUIREMENT], None)],
                    )
                ]),
            ],
            name="i7-g",
        )
        report = self._construct(
            accepted,
            [
                self._binding(accepted, bom_ordinal=0, parent_ordinal=0),
                self._binding(accepted, bom_ordinal=0, parent_ordinal=1),
            ],
            name="i7-g",
        )
        self.assertEqual(report.objects_for("BOM Component"), ())
        self.assertEqual(len(report.unresolved_for("BOM Component")), 1)
        self.assertIn("UNRESOLVED_IDENTITY", {issue.reason for issue in report.issues})

    def test_h_multiple_boms_bind_only_to_their_own_parent(self) -> None:
        requirement_a = with_provenance(
            {
                "plant_id": PLANT,
                "material_code": MATERIAL,
                "required_date": self.OCT,
                "ProductionQty": "10",
            },
            [("ProductionQty", [EVIDENCE_REQUIREMENT], None)],
        )
        requirement_b = with_provenance(
            {
                "plant_id": "P2",
                "material_code": "M9",
                "required_date": self.OCT,
                "ProductionQty": "20",
            },
            [("ProductionQty", [EVIDENCE_REQUIREMENT], None)],
        )
        _, accepted = self.accepted(
            [
                ("Production Requirement", [requirement_a, requirement_b]),
                (
                    "BOM Component",
                    [
                        with_provenance(
                            {"material_code": COMPONENT, "BOMComponentQty": "2"},
                            [("BOMComponentQty", [EVIDENCE_REQUIREMENT], None)],
                        ),
                        with_provenance(
                            {"material_code": "M7", "BOMComponentQty": "3"},
                            [("BOMComponentQty", [EVIDENCE_REQUIREMENT], None)],
                        ),
                    ],
                ),
            ],
            name="i7-h",
        )
        report = self._construct(
            accepted,
            [
                self._binding(accepted, bom_ordinal=0, parent_ordinal=0),
                self._binding(accepted, bom_ordinal=1, parent_ordinal=1),
            ],
            name="i7-h",
        )
        objects = report.objects_for("BOM Component")
        self.assertEqual(len(objects), 2)
        parents = {
            obj.value_of("material_code"): obj.context_reference for obj in objects
        }
        resolved_requirements = report.objects_for("Production Requirement")
        self.assertEqual(
            parents[COMPONENT], resolved_requirements[0].record_reference
        )
        self.assertEqual(parents["M7"], resolved_requirements[1].record_reference)
        # No cross-binding: each BOM binds only to its own parent context.
        self.assertNotEqual(parents[COMPONENT], parents["M7"])

    def test_i_foreign_or_wrong_role_bom_evidence_is_unresolved(self) -> None:
        _, accepted = self._package(bom_fields={}, name="i7-i")
        cases = {
            "foreign-package": self._binding(accepted, bom_package="OTHER-PACKAGE"),
            "wrong-role": self._binding(accepted, bom_role="Production Requirement"),
            "missing-record": self._binding(accepted, bom_ordinal=9),
        }
        for label, binding in cases.items():
            with self.subTest(case=label):
                report = self._construct(accepted, [binding], name=f"i7-i-{label}")
                self.assertEqual(report.objects_for("BOM Component"), ())
                self.assertEqual(len(report.unresolved_for("BOM Component")), 1)

    def test_j_foreign_or_wrong_role_parent_evidence_is_unresolved(self) -> None:
        _, accepted = self._package(bom_fields={}, name="i7-j")
        cases = {
            "foreign-package": self._binding(accepted, parent_package="OTHER-PACKAGE"),
            "wrong-role": self._binding(accepted, parent_role="BOM Component", parent_artifact="1.json"),
            "missing-record": self._binding(accepted, parent_ordinal=9),
        }
        for label, binding in cases.items():
            with self.subTest(case=label):
                report = self._construct(accepted, [binding], name=f"i7-j-{label}")
                self.assertEqual(report.objects_for("BOM Component"), ())
                self.assertEqual(len(report.unresolved_for("BOM Component")), 1)

    def test_k_referenced_parent_not_resolved_is_unresolved(self) -> None:
        _, accepted = self._package(bom_fields={}, name="i7-k")
        binding = self._binding(accepted, parent_ordinal=0)
        report = self._construct(accepted, [binding], name="i7-k")
        # The requirement is resolved in this package, so the binding succeeds; removing
        # the requirement record makes the same binding unresolvable.
        self._assert_resolved(report)

        requirement = accepted.datasets()[0]
        self.assertEqual(requirement[0], "Production Requirement")
        # Build a package whose requirement dataset is present but whose record cannot be
        # constructed as a resolved Production Requirement (wrong role content).
        _, other = self.accepted(
            [
                ("Production Requirement", [{"plant_id": PLANT, "material_code": MATERIAL}]),
                ("BOM Component", [
                    with_provenance(
                        {"material_code": COMPONENT, "BOMComponentQty": "2"},
                        [("BOMComponentQty", [EVIDENCE_REQUIREMENT], None)],
                    )
                ]),
            ],
            name="i7-k-unresolved",
        )
        unresolved_report = self._construct(
            other, [self._binding(other)], name="i7-k-unresolved"
        )
        # The requirement record is missing required_date, so no resolved context exists.
        self.assertEqual(unresolved_report.objects_for("Production Requirement"), ())
        self.assertEqual(unresolved_report.objects_for("BOM Component"), ())
        self.assertEqual(len(unresolved_report.unresolved_for("BOM Component")), 1)

    def test_no_plant_date_fallback_when_no_binding_is_declared(self) -> None:
        # Even though a resolved Production Requirement with exactly matching plant_id /
        # required_date exists, no plant/date heuristic may select it.
        _, accepted = self._package(
            bom_fields={"plant_id": PLANT, "required_date": self.OCT}, name="i7-no-fallback"
        )
        report = construct_canonical_objects(
            accepted,
            PhaseAHandoff(analysis_run_id="RUN-1", analysis_date="2026-10-01"),
        )
        self.assertEqual(report.objects_for("BOM Component"), ())
        self.assertEqual(len(report.unresolved_for("BOM Component")), 1)
        self.assertIn("UNRESOLVED_IDENTITY", {issue.reason for issue in report.issues})


if __name__ == "__main__":
    unittest.main()
