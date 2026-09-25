"""Inventory ownership / POC Inventory Scope runtime seam ``A′`` tests (Issue #136).

Coverage required by Issue #136 (Human Decision ``A′`` = ``APPROVED``, 2026-09-25):

* same-grain retention: several ``Inventory Snapshot`` records legally sharing one
  Plant-level canonical grain are **all** retained, with no canonicalization-time sum,
  first / last wins or same-value deduplication -- while every other grain-keyed target
  keeps its existing exactly-one-or-unresolved behaviour;
* the ``InventoryScopeHandoff`` caller boundary exposes **no** declarable outcome
  (``in_scope`` / membership / Plant ownership value / ``warehouse_id``);
* exact-association resolution: only the ``mapping_basis`` registered on the exact
  association named by the exact ``observation`` may be used, never another
  association's;
* the approved SIMULATED basis registry decides the outcome; an unregistered basis,
  a basis mismatch, a missing handoff, a duplicate applicable resolution, a foreign
  package, a wrong role, a minted locator or an unusable observation all stay
  ``SCOPE_COVERAGE`` / ``UNRESOLVED_SCOPE``;
* Shape A / Shape B × ``IN_SCOPE`` / ``OUT_OF_SCOPE``, where ``OUT_OF_SCOPE`` is a legal
  exclusion and never a Data Quality defect;
* Plant ownership comes from accepted canonical evidence and never from the caller;
* the resolved context preserves the layered logical provenance;
* the Layer-1 wire contract is unchanged (``META_MEMBERS`` / ``ASSOCIATION_MEMBERS`` /
  canonical property set).

All fixtures are SIMULATED.
"""

from __future__ import annotations

import json
import unittest
import uuid
from pathlib import Path

from snapshot_loader import (
    INVENTORY_SCOPE_BASIS_REGISTRY,
    INVENTORY_SCOPE_IN,
    INVENTORY_SCOPE_OUT,
    INVENTORY_SCOPE_SHAPE_PLANT_AGGREGATE,
    INVENTORY_SCOPE_SHAPE_WAREHOUSE,
    InventoryScopeHandoff,
    PhaseAHandoff,
    TrustedInputBoundary,
    construct_canonical_objects,
    load_package,
)
from snapshot_loader.canonical_objects import (
    CANONICALIZATION_HANDOFF_EVIDENCE,
    GRAIN_KEYED_TARGET_ORDER,
    HandoffEvidence,
    InventoryScopeContext,
    ROLE_INVENTORY_SNAPSHOT,
)
from snapshot_loader.constants import (
    ASSOCIATION_MEMBERS,
    CATEGORY_SCOPE_COVERAGE,
    META_MEMBERS,
    REASON_UNRESOLVED_SCOPE,
    V02_CANONICAL_RECORD_PROPERTIES,
)
from tests.helpers import DatasetSpec, PackageSpec, build_package

SCRATCH_ROOT = Path(__file__).resolve().parents[1] / "build" / "test-scratch"

PLANT = "P1"
PLANT_B = "P2"
MATERIAL = "M1"
SNAPSHOT_TIME = "2026-01-31T08:00:00Z"

BASIS_A_IN = "SIMULATED-INV-SCOPE-A-IN"
BASIS_A_OUT = "SIMULATED-INV-SCOPE-A-OUT"
BASIS_B_IN = "SIMULATED-INV-SCOPE-B-IN"
BASIS_B_OUT = "SIMULATED-INV-SCOPE-B-OUT"
BASIS_UNREGISTERED = "SIMULATED-UNREGISTERED-INV-BASIS"

LOCATOR_WAREHOUSE = "SIMULATED-WH-01-CONTEXT"
LOCATOR_WAREHOUSE_ALT = "SIMULATED-WH-02-CONTEXT"
LOCATOR_AGGREGATE = "SIMULATED-EXPORT-AGG-P1-M1"
LOCATOR_MINTED = "SIMULATED-MINTED-LOCATOR"


def with_associations(
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


def INVENTORY(
    *,
    plant_id: object = PLANT,
    material_code: object = MATERIAL,
    snapshot_time: object = SNAPSHOT_TIME,
    on_hand_qty: object = "100",
    inventory_status: object = "AVAILABLE",
    associations: list[tuple[str, list[str], str | None]] | None = None,
) -> dict[str, object]:
    record: dict[str, object] = {}
    if plant_id is not None:
        record["plant_id"] = plant_id
    if material_code is not None:
        record["material_code"] = material_code
    if snapshot_time is not None:
        record["inventory_snapshot_time"] = snapshot_time
    if inventory_status is not None:
        record["inventory_status"] = inventory_status
    if on_hand_qty is not None:
        record["on_hand_qty"] = on_hand_qty
    if associations is None:
        associations = [("plant_id", [LOCATOR_WAREHOUSE], BASIS_A_IN)]
    return with_associations(record, associations)


def SAFETY_STOCK(
    value: str = "5",
    *,
    associations: list[tuple[str, list[str], str | None]] | None = None,
) -> dict[str, object]:
    record: dict[str, object] = {
        "plant_id": PLANT,
        "material_code": MATERIAL,
        "SafetyStock": value,
    }
    if associations is None:
        associations = [("SafetyStock", ["SIMULATED-SRC-SS-1"], None)]
    return with_associations(record, associations)


class InventoryScopeSeamTestCase(unittest.TestCase):
    """Shared scaffolding: one accepted package per subtest directory."""

    def setUp(self) -> None:
        self.boundary = SCRATCH_ROOT / f"inventory-scope-{uuid.uuid4().hex}"
        self.boundary.mkdir(parents=True, exist_ok=True)

    def load(
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
        return built, load_package(
            built.root, trusted_boundary=TrustedInputBoundary(root=self.boundary)
        )

    def accepted(
        self,
        datasets: list[tuple[str, list[dict[str, object]]]],
        *,
        name: str | None = None,
        package_id: str = "SIMULATED-PKG-0001",
    ):
        _built, report = self.load(datasets, name=name, package_id=package_id)
        self.assertTrue(
            report.accepted,
            msg=f"fixture package was not accepted: {report.disposition_basis}",
        )
        assert report.accepted_package is not None
        return report.accepted_package

    def construct(
        self,
        datasets: list[tuple[str, list[dict[str, object]]]],
        handoff: PhaseAHandoff | None = None,
        *,
        name: str | None = None,
        package_id: str = "SIMULATED-PKG-0001",
    ):
        accepted = self.accepted(datasets, name=name, package_id=package_id)
        if handoff is None:
            handoff = PhaseAHandoff(
                analysis_run_id="RUN-1", analysis_date="2026-01-31"
            )
        return construct_canonical_objects(accepted, handoff)

    def citation(
        self,
        accepted,
        *,
        role: str = ROLE_INVENTORY_SNAPSHOT,
        artifact: str = "0.json",
        ordinal: int = 0,
        locator: str | None = None,
        package_id: str | None = None,
    ) -> HandoffEvidence:
        return HandoffEvidence(
            snapshot_package_identity=package_id or accepted.package_id,
            logical_dataset_role=role,
            artifact=artifact,
            record_ordinal=ordinal,
            evidence_locator=locator,
        )

    def scope_handoff(
        self,
        accepted,
        *,
        observation: str = "plant_id",
        basis: str = BASIS_A_IN,
        locator: str | None = None,
        role: str = ROLE_INVENTORY_SNAPSHOT,
        package_id: str | None = None,
        ordinal: int = 0,
    ) -> PhaseAHandoff:
        return PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-01-31",
            inventory_scope=(
                InventoryScopeHandoff(
                    inventory_evidence=self.citation(
                        accepted,
                        role=role,
                        ordinal=ordinal,
                        locator=locator,
                        package_id=package_id,
                    ),
                    scope_observation=observation,
                    scope_resolution_basis=basis,
                ),
            ),
        )

    # --- assertions ---------------------------------------------------------------

    def scope_contexts(self, report) -> tuple[InventoryScopeContext, ...]:
        return report.inventory_scope_contexts

    def only_context(self, report) -> InventoryScopeContext:
        contexts = self.scope_contexts(report)
        self.assertEqual(len(contexts), 1)
        return contexts[0]

    def assert_unresolved_scope(self, context: InventoryScopeContext) -> None:
        self.assertFalse(context.scope_resolved)
        self.assertIsNone(context.in_scope)
        self.assertIsNone(context.scope_membership)

    def issues_with(self, report, reason: str) -> list:
        return [issue for issue in report.issues if issue.reason == reason]


class SameGrainRetentionTests(InventoryScopeSeamTestCase):
    """The registered same-grain exception applies to ``Inventory Snapshot`` only."""

    def test_two_same_grain_inventory_records_are_both_retained(self) -> None:
        report = self.construct(
            [
                (
                    ROLE_INVENTORY_SNAPSHOT,
                    [
                        INVENTORY(on_hand_qty="100"),
                        INVENTORY(on_hand_qty="30"),
                    ],
                )
            ],
            name="inventory-same-grain",
        )
        retained = report.objects_for(ROLE_INVENTORY_SNAPSHOT)
        self.assertEqual(len(retained), 2)
        self.assertEqual(report.unresolved_for(ROLE_INVENTORY_SNAPSHOT), ())
        # No canonicalization-time sum / first / last / same-value dedup: both distinct
        # observations survive with their own exact quantity, and nothing is aggregated.
        self.assertEqual(
            sorted(item.value_of("on_hand_qty") for item in retained), ["100", "30"]
        )
        self.assertEqual(
            len({item.record_reference for item in retained}), 2
        )
        states = report.check_states()
        self.assertEqual(
            states[f"canonicalization.grain_resolution:{ROLE_INVENTORY_SNAPSHOT}"],
            "passed",
        )

    def test_content_identical_same_grain_inventory_records_are_not_deduplicated(self) -> None:
        record = INVENTORY(on_hand_qty="40")
        report = self.construct(
            [(ROLE_INVENTORY_SNAPSHOT, [dict(record), dict(record)])],
            name="inventory-same-grain-identical",
        )
        retained = report.objects_for(ROLE_INVENTORY_SNAPSHOT)
        self.assertEqual(len(retained), 2)
        self.assertEqual(len({item.record_reference for item in retained}), 2)

    def test_other_grain_keyed_targets_keep_exactly_one_or_unresolved(self) -> None:
        report = self.construct(
            [
                ("Configured Safety Stock", [SAFETY_STOCK("5"), SAFETY_STOCK("5")]),
                (ROLE_INVENTORY_SNAPSHOT, [INVENTORY()]),
            ],
            name="safety-stock-duplicate-grain",
        )
        self.assertEqual(report.objects_for("Configured Safety Stock"), ())
        self.assertEqual(len(report.unresolved_for("Configured Safety Stock")), 2)
        states = report.check_states()
        self.assertEqual(
            states["canonicalization.grain_resolution:Configured Safety Stock"],
            "not_evaluable",
        )
        # The Inventory exception is target-scoped and does not leak.
        self.assertEqual(len(report.objects_for(ROLE_INVENTORY_SNAPSHOT)), 1)

    def test_inventory_record_without_grain_part_stays_unresolved(self) -> None:
        report = self.construct(
            [(ROLE_INVENTORY_SNAPSHOT, [INVENTORY(snapshot_time=None)])],
            name="inventory-ungrainable",
        )
        self.assertEqual(report.objects_for(ROLE_INVENTORY_SNAPSHOT), ())
        self.assertEqual(len(report.unresolved_for(ROLE_INVENTORY_SNAPSHOT)), 1)
        self.assertEqual(
            [issue.reason for issue in self.issues_with(report, "UNRESOLVED_IDENTITY")],
            ["UNRESOLVED_IDENTITY"],
        )
        context = self.only_context(report)
        self.assertFalse(context.ownership_resolved)
        self.assert_unresolved_scope(context)


class InventoryScopeResolutionTests(InventoryScopeSeamTestCase):
    """The A′ resolution matrix: exact association → exact basis → exact outcome."""

    def resolve(self, record: dict[str, object], handoff_factory, *, name: str):
        dataset = [(ROLE_INVENTORY_SNAPSHOT, [record])]
        accepted = self.accepted(dataset, name=name)
        report = construct_canonical_objects(accepted, handoff_factory(accepted))
        return report, self.only_context(report)

    # --- Shape A ----------------------------------------------------------------

    def test_shape_a_in_scope_resolves_with_the_evidence_plant(self) -> None:
        report, context = self.resolve(
            INVENTORY(plant_id=PLANT),
            lambda accepted: self.scope_handoff(accepted, basis=BASIS_A_IN),
            name="shape-a-in",
        )
        self.assertTrue(context.ownership_resolved)
        self.assertTrue(context.scope_resolved)
        self.assertIs(context.in_scope, True)
        self.assertEqual(context.scope_membership, INVENTORY_SCOPE_IN)
        self.assertEqual(context.source_shape, INVENTORY_SCOPE_SHAPE_WAREHOUSE)
        self.assertEqual(context.plant_id, PLANT)
        self.assertEqual(context.scope_observation, "plant_id")
        self.assertEqual(context.mapping_basis, BASIS_A_IN)
        self.assertEqual(
            report.check_states()[
                f"{CANONICALIZATION_HANDOFF_EVIDENCE}:InventoryScope[0]"
            ],
            "passed",
        )
        # A resolved scope is not a Data Quality defect.
        self.assertEqual(self.issues_with(report, REASON_UNRESOLVED_SCOPE), [])

    def test_shape_a_out_of_scope_is_a_legal_exclusion(self) -> None:
        report, context = self.resolve(
            INVENTORY(associations=[("plant_id", [LOCATOR_WAREHOUSE], BASIS_A_OUT)]),
            lambda accepted: self.scope_handoff(accepted, basis=BASIS_A_OUT),
            name="shape-a-out",
        )
        self.assertTrue(context.scope_resolved)
        self.assertIs(context.in_scope, False)
        self.assertEqual(context.scope_membership, INVENTORY_SCOPE_OUT)
        self.assertEqual(context.source_shape, INVENTORY_SCOPE_SHAPE_WAREHOUSE)
        # Legal exclusion: not DATA_INCOMPLETE and not a Data Quality defect.
        self.assertEqual(self.issues_with(report, REASON_UNRESOLVED_SCOPE), [])
        self.assertEqual(report.issues, ())

    # --- Shape B ----------------------------------------------------------------

    def test_shape_b_in_scope_uses_the_approved_association_not_the_grain(self) -> None:
        """A Plant-level record is never automatically in scope."""

        record = INVENTORY(
            associations=[("on_hand_qty", [LOCATOR_AGGREGATE], BASIS_B_IN)]
        )
        report, context = self.resolve(
            record,
            lambda accepted: self.scope_handoff(
                accepted, observation="on_hand_qty", basis=BASIS_B_IN
            ),
            name="shape-b-in",
        )
        self.assertTrue(context.scope_resolved)
        self.assertIs(context.in_scope, True)
        self.assertEqual(context.source_shape, INVENTORY_SCOPE_SHAPE_PLANT_AGGREGATE)
        self.assertEqual(context.scope_observation, "on_hand_qty")
        self.assertEqual(context.mapping_basis, BASIS_B_IN)
        self.assertEqual(self.issues_with(report, REASON_UNRESOLVED_SCOPE), [])

    def test_shape_b_plant_level_aggregate_without_scope_basis_is_unresolved(self) -> None:
        """Being a Plant-level aggregate is not by itself proof of scope membership."""

        record = INVENTORY(
            associations=[("on_hand_qty", [LOCATOR_AGGREGATE], BASIS_B_IN)]
        )
        report, context = self.resolve(
            record,
            lambda accepted: self.scope_handoff(
                accepted, observation="plant_id", basis=BASIS_A_IN
            ),
            name="shape-b-no-scope-basis",
        )
        self.assertTrue(context.ownership_resolved)
        self.assert_unresolved_scope(context)
        self.assertEqual(len(self.issues_with(report, REASON_UNRESOLVED_SCOPE)), 1)

    def test_shape_b_out_of_scope_is_a_legal_exclusion(self) -> None:
        record = INVENTORY(
            associations=[("on_hand_qty", [LOCATOR_AGGREGATE], BASIS_B_OUT)]
        )
        report, context = self.resolve(
            record,
            lambda accepted: self.scope_handoff(
                accepted, observation="on_hand_qty", basis=BASIS_B_OUT
            ),
            name="shape-b-out",
        )
        self.assertTrue(context.scope_resolved)
        self.assertIs(context.in_scope, False)
        self.assertEqual(context.source_shape, INVENTORY_SCOPE_SHAPE_PLANT_AGGREGATE)
        self.assertEqual(report.issues, ())

    # --- association specificity -------------------------------------------------

    def test_only_the_named_associations_basis_is_used(self) -> None:
        record = INVENTORY(
            associations=[
                ("plant_id", [LOCATOR_WAREHOUSE], BASIS_A_OUT),
                ("on_hand_qty", [LOCATOR_AGGREGATE], BASIS_B_IN),
            ]
        )
        report, context = self.resolve(
            record,
            lambda accepted: self.scope_handoff(
                accepted, observation="plant_id", basis=BASIS_A_OUT, locator=LOCATOR_WAREHOUSE
            ),
            name="association-specific",
        )
        self.assertTrue(context.scope_resolved)
        self.assertIs(context.in_scope, False)
        self.assertEqual(context.mapping_basis, BASIS_A_OUT)
        # The other association's basis is never borrowed to upgrade the outcome.
        self.assertNotEqual(context.mapping_basis, BASIS_B_IN)
        provenance = context.provenance
        assert provenance is not None
        self.assertEqual(provenance.mapping_resolution_basis, BASIS_A_OUT)
        self.assertEqual(
            provenance.stable_source_evidence_locators, (LOCATOR_WAREHOUSE,)
        )

    def test_another_associations_basis_is_never_borrowed(self) -> None:
        record = INVENTORY(
            associations=[
                ("plant_id", [LOCATOR_WAREHOUSE], BASIS_A_OUT),
                ("on_hand_qty", [LOCATOR_AGGREGATE], BASIS_B_IN),
            ]
        )
        report, context = self.resolve(
            record,
            lambda accepted: self.scope_handoff(
                accepted, observation="plant_id", basis=BASIS_B_IN
            ),
            name="association-borrow",
        )
        self.assert_unresolved_scope(context)
        self.assertEqual(len(self.issues_with(report, REASON_UNRESOLVED_SCOPE)), 1)

    # --- unresolved paths --------------------------------------------------------

    def test_basis_mismatch_is_unresolved(self) -> None:
        report, context = self.resolve(
            INVENTORY(),
            lambda accepted: self.scope_handoff(accepted, basis=BASIS_B_IN),
            name="basis-mismatch",
        )
        self.assertTrue(context.ownership_resolved)
        self.assert_unresolved_scope(context)
        issue = self.issues_with(report, REASON_UNRESOLVED_SCOPE)[0]
        self.assertEqual(issue.category, CATEGORY_SCOPE_COVERAGE)
        self.assertEqual(issue.layer, 2)

    def test_unregistered_registered_basis_is_unresolved(self) -> None:
        """The association registers a basis, but it is not approved ⇒ unresolved."""

        record = INVENTORY(
            associations=[("plant_id", [LOCATOR_WAREHOUSE], BASIS_UNREGISTERED)]
        )
        report, context = self.resolve(
            record,
            lambda accepted: self.scope_handoff(accepted, basis=BASIS_UNREGISTERED),
            name="unknown-basis",
        )
        self.assert_unresolved_scope(context)
        notes = [
            note
            for name, _state, note in report.checks
            if name == f"{CANONICALIZATION_HANDOFF_EVIDENCE}:InventoryScope[0]"
        ]
        self.assertTrue(any("not in the approved inventory-scope basis registry" in (note or "") for note in notes))
        self.assertEqual(len(self.issues_with(report, REASON_UNRESOLVED_SCOPE)), 1)

    def test_missing_handoff_is_unresolved_scope(self) -> None:
        report, context = self.resolve(
            INVENTORY(),
            lambda accepted: PhaseAHandoff(
                analysis_run_id="RUN-1", analysis_date="2026-01-31"
            ),
            name="missing-handoff",
        )
        self.assertTrue(context.ownership_resolved)
        self.assert_unresolved_scope(context)
        self.assertEqual(len(self.issues_with(report, REASON_UNRESOLVED_SCOPE)), 1)

    def test_duplicate_applicable_resolution_is_unresolved(self) -> None:
        dataset = [(ROLE_INVENTORY_SNAPSHOT, [INVENTORY()])]
        accepted = self.accepted(dataset, name="duplicate-entries")
        citation = self.citation(accepted)
        handoff = PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-01-31",
            inventory_scope=(
                InventoryScopeHandoff(citation, "plant_id", BASIS_A_IN),
                InventoryScopeHandoff(citation, "plant_id", BASIS_A_IN),
            ),
        )
        report = construct_canonical_objects(accepted, handoff)
        context = self.only_context(report)
        self.assert_unresolved_scope(context)
        self.assertEqual(len(self.issues_with(report, REASON_UNRESOLVED_SCOPE)), 1)

    def test_foreign_package_citation_is_unresolved(self) -> None:
        report, context = self.resolve(
            INVENTORY(),
            lambda accepted: self.scope_handoff(
                accepted, package_id="SIMULATED-PKG-9999"
            ),
            name="foreign-package",
        )
        self.assert_unresolved_scope(context)
        notes = [
            note
            for name, _state, note in report.checks
            if name == f"{CANONICALIZATION_HANDOFF_EVIDENCE}:InventoryScope[0]"
        ]
        self.assertTrue(any("different Snapshot Package Identity" in (note or "") for note in notes))
        self.assertEqual(len(self.issues_with(report, REASON_UNRESOLVED_SCOPE)), 1)

    def test_wrong_declared_role_is_unresolved(self) -> None:
        report, context = self.resolve(
            INVENTORY(),
            lambda accepted: self.scope_handoff(accepted, role="Inbound Supply"),
            name="wrong-role",
        )
        self.assert_unresolved_scope(context)
        self.assertEqual(len(self.issues_with(report, REASON_UNRESOLVED_SCOPE)), 1)

    def test_minted_locator_is_unresolved(self) -> None:
        report, context = self.resolve(
            INVENTORY(),
            lambda accepted: self.scope_handoff(accepted, locator=LOCATOR_MINTED),
            name="minted-locator",
        )
        self.assert_unresolved_scope(context)
        self.assertEqual(len(self.issues_with(report, REASON_UNRESOLVED_SCOPE)), 1)

    def test_unusable_scope_observation_is_unresolved(self) -> None:
        report, context = self.resolve(
            INVENTORY(),
            lambda accepted: self.scope_handoff(accepted, observation="SafetyStock"),
            name="bad-observation",
        )
        self.assert_unresolved_scope(context)
        self.assertEqual(len(self.issues_with(report, REASON_UNRESOLVED_SCOPE)), 1)

    def test_ownership_unresolved_is_reported_as_unresolved_identity(self) -> None:
        report, context = self.resolve(
            INVENTORY(plant_id=""),
            lambda accepted: self.scope_handoff(accepted),
            name="ownership-unresolved",
        )
        self.assertFalse(context.ownership_resolved)
        self.assert_unresolved_scope(context)
        self.assertEqual(
            [issue.category for issue in self.issues_with(report, "UNRESOLVED_IDENTITY")],
            ["IDENTITY_RESOLUTION"],
        )
        # Ownership is never defaulted to the current Plant nor taken from the caller.
        self.assertEqual(context.plant_id, "")

    # --- provenance --------------------------------------------------------------

    def test_resolved_context_preserves_the_layered_logical_provenance(self) -> None:
        report, context = self.resolve(
            INVENTORY(),
            lambda accepted: self.scope_handoff(accepted, basis=BASIS_A_IN),
            name="provenance",
        )
        provenance = context.provenance
        assert provenance is not None
        self.assertEqual(provenance.snapshot_package_identity, "SIMULATED-PKG-0001")
        self.assertEqual(provenance.logical_dataset_role, ROLE_INVENTORY_SNAPSHOT)
        self.assertEqual(
            provenance.stable_source_evidence_locators, (LOCATOR_WAREHOUSE,)
        )
        self.assertEqual(provenance.logical_observation, "plant_id")
        self.assertEqual(provenance.mapping_resolution_basis, BASIS_A_IN)
        self.assertEqual(provenance.record_path, "0.json#0")
        self.assertEqual(context.inventory_reference, report.objects_for(ROLE_INVENTORY_SNAPSHOT)[0].record_reference)
        payload = context.to_dict()
        self.assertEqual(payload["record_path"], "0.json#0")
        self.assertEqual(
            payload["provenance"]["stable_source_evidence_locators"],
            [LOCATOR_WAREHOUSE],
        )
        self.assertEqual(payload["provenance"]["logical_observation"], "plant_id")


class InventoryScopeBoundaryTests(InventoryScopeSeamTestCase):
    """Caller boundary, report surface and wire stability."""

    def test_handoff_exposes_no_caller_declarable_outcome(self) -> None:
        fields = set(InventoryScopeHandoff.__dataclass_fields__)
        self.assertEqual(
            fields,
            {
                "inventory_evidence",
                "scope_observation",
                "scope_resolution_basis",
                "resolution_note",
            },
        )
        for forbidden in (
            "in_scope",
            "scope_membership",
            "membership",
            "plant_id",
            "plant_ownership",
            "warehouse_id",
            "source_shape",
            "outcome",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, fields)

    def test_in_scope_is_only_a_derived_result(self) -> None:
        report, context = self.resolve_scope()
        self.assertTrue(context.scope_resolved)
        self.assertIs(context.in_scope, True)
        payload = json.dumps(report.to_dict())
        self.assertIn('"in_scope": true', payload.replace("'", '"'))

    def resolve_scope(self):
        dataset = [(ROLE_INVENTORY_SNAPSHOT, [INVENTORY()])]
        accepted = self.accepted(dataset, name="derived-in-scope")
        report = construct_canonical_objects(
            accepted, self.scope_handoff(accepted, basis=BASIS_A_IN)
        )
        return report, self.only_context(report)

    def test_report_exposes_the_contexts_and_a_deterministic_lookup(self) -> None:
        report, context = self.resolve_scope()
        self.assertEqual(len(report.inventory_scope_contexts), 1)
        self.assertEqual(
            report.inventory_scope_for(context.inventory_reference), context
        )
        self.assertIsNone(report.inventory_scope_for("SIMULATED-PKG-0001|Nope|0.json|0"))
        payload = report.to_dict()
        self.assertEqual(len(payload["inventory_scope_contexts"]), 1)
        self.assertEqual(
            payload["inventory_scope_contexts"][0]["inventory_reference"],
            context.inventory_reference,
        )
        # Deterministic repeatability of the whole Phase A result.
        dataset = [(ROLE_INVENTORY_SNAPSHOT, [INVENTORY()])]
        accepted = self.accepted(dataset, name="determinism")
        first = construct_canonical_objects(
            accepted, self.scope_handoff(accepted, basis=BASIS_A_IN)
        ).to_dict()
        second = construct_canonical_objects(
            accepted, self.scope_handoff(accepted, basis=BASIS_A_IN)
        ).to_dict()
        self.assertEqual(first, second)
        json.dumps(first)

    def test_registered_basis_registry_is_exact_literal_to_exact_semantic(self) -> None:
        registry = {
            entry.basis: (entry.source_shape, entry.membership)
            for entry in INVENTORY_SCOPE_BASIS_REGISTRY
        }
        self.assertEqual(
            registry,
            {
                BASIS_A_IN: (INVENTORY_SCOPE_SHAPE_WAREHOUSE, INVENTORY_SCOPE_IN),
                BASIS_A_OUT: (INVENTORY_SCOPE_SHAPE_WAREHOUSE, INVENTORY_SCOPE_OUT),
                BASIS_B_IN: (INVENTORY_SCOPE_SHAPE_PLANT_AGGREGATE, INVENTORY_SCOPE_IN),
                BASIS_B_OUT: (INVENTORY_SCOPE_SHAPE_PLANT_AGGREGATE, INVENTORY_SCOPE_OUT),
            },
        )

    def test_layer1_wire_contract_is_unchanged(self) -> None:
        self.assertEqual(META_MEMBERS, ("provenance_associations",))
        self.assertEqual(
            ASSOCIATION_MEMBERS, ("observation", "evidence", "mapping_basis")
        )
        self.assertEqual(len(V02_CANONICAL_RECORD_PROPERTIES), 30)
        for forbidden in ("warehouse_id", "warehouse", "inventory_scope", "in_scope"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, V02_CANONICAL_RECORD_PROPERTIES)

    def test_unknown_meta_member_is_still_rejected_by_layer1(self) -> None:
        record = INVENTORY()
        record["_meta"] = {
            "provenance_associations": [
                {"observation": "plant_id", "evidence": [LOCATOR_WAREHOUSE], "mapping_basis": BASIS_A_IN}
            ],
            "inventory_scope": {"in_scope": True},
        }
        _built, report = self.load(
            [(ROLE_INVENTORY_SNAPSHOT, [record])], name="unknown-meta-member"
        )
        self.assertFalse(report.accepted)

    def test_no_warehouse_canonical_target_is_created(self) -> None:
        report = construct_canonical_objects(
            self.accepted([(ROLE_INVENTORY_SNAPSHOT, [INVENTORY()])], name="no-warehouse"),
            PhaseAHandoff(analysis_run_id="RUN-1", analysis_date="2026-01-31"),
        )
        targets = {entry.canonical_target for entry in report.object_sets}
        registered = set(GRAIN_KEYED_TARGET_ORDER) | {"BOM Component"}
        self.assertTrue(targets <= registered)
        for forbidden in ("Warehouse", "warehouse", "Inventory Scope"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, targets)
        payload = json.dumps(report.to_dict())
        for forbidden in ("warehouse_id", "canonical_warehouse"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, payload)


if __name__ == "__main__":
    unittest.main()
