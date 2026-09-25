"""``BR-REQUIREMENT-001`` Requirement Calculation tests (POC Design v0.2 §2.4).

Coverage mirrors the registered acceptance examples and the rule's fail-safe boundary:

* Example A -- no loss (``Base = 200``, ``Gross = 200``);
* Example B -- 5% loss (``Gross = 200 / 0.95``, no automatic rounding);
* Example C -- missing ``loss_rate`` -> ``DATA_INCOMPLETE``, no numeric requirement;
* Example D -- invalid ``loss_rate`` (``1.0`` / negative) -> ``DATA_INCOMPLETE``, no clamp;
* Example E -- BOM unresolved -> ``DATA_INCOMPLETE``;
* Example F -- cumulative requirement per registered grouping;
* Example G -- substitute supply cannot reduce the requirement side;
* separate plants never aggregate; the same component under different Requirement
  Calculation Contexts never reuses another context; ``M2`` / ``M3`` under one parent use
  their own ``loss_rate``; deterministic decimal arithmetic without binary float;
* only resolved canonical construction output is consumed.

All fixtures are SIMULATED.
"""

from __future__ import annotations

import unittest
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any

from snapshot_loader import (
    BomParentContextHandoff,
    HandoffEvidence,
    LossRateHandoff,
    PhaseAHandoff,
    TrustedInputBoundary,
    compute_requirement_calculation,
    construct_canonical_objects,
    load_package,
)
from snapshot_loader.requirement_calculation import (
    OUTCOME_DATA_INCOMPLETE,
    OUTCOME_NUMERIC,
    RULE_ID,
    base_requirement,
    gross_requirement,
)
from tests.helpers import DatasetSpec, PackageSpec, build_package

SCRATCH_ROOT = Path(__file__).resolve().parents[1] / "build" / "test-scratch"

PLANT = "P1"
PLANT_B = "P2"
PARENT = "M1"
COMPONENT = "M2"
COMPONENT_B = "M3"
REQUIRED_DATE = "2026-02-01"

#: Opaque Stable Source Evidence Locator strings registered by the SIMULATED fixtures.
EVIDENCE_REQUIREMENT = "SIMULATED-SRC-REQ-1"
EVIDENCE_BOM = "SIMULATED-SRC-BOM-1"
BASIS_LOSS_RATE = "SIMULATED-APPROVED-LOSS-RATE-MAPPING"

#: ``200 / 0.95`` does not terminate in base 10.  This is the exact registered value the
#: rule must keep: no round / ceil / floor / truncation (``§2.4.8``).
EXACT_GROSS_200_5PCT = "210.526315789473684210526315789473684210526315789473684210526"


class Omit:
    """Sentinel distinguishing "omitted" from a present JSON ``null``."""

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "<omit>"


OMIT = Omit()


def with_provenance(
    record: dict[str, Any],
    associations: list[tuple[str, list[str], str | None]],
) -> dict[str, Any]:
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


class RequirementCalculationTestCase(unittest.TestCase):
    """Shared scaffolding: real accepted packages plus a real Phase A construction."""

    def setUp(self) -> None:
        self.boundary = SCRATCH_ROOT / f"requirement-{uuid.uuid4().hex}"
        self.boundary.mkdir(parents=True, exist_ok=True)

    # --- fixture plumbing ----------------------------------------------------------

    def accepted(
        self,
        datasets: list[tuple[str, list[dict[str, Any]]]],
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
        self.assertTrue(
            report.accepted,
            msg=f"fixture package was not accepted: {report.disposition_basis}",
        )
        assert report.accepted_package is not None
        return built, report.accepted_package

    def citation(
        self,
        accepted,
        *,
        role: str,
        artifact: str,
        ordinal: int = 0,
        locator: str | None = None,
    ) -> HandoffEvidence:
        return HandoffEvidence(
            snapshot_package_identity=accepted.package_id,
            logical_dataset_role=role,
            artifact=artifact,
            record_ordinal=ordinal,
            evidence_locator=locator,
        )

    def parent_handoff(
        self, accepted, *, plant: str = PLANT, required_date: str = REQUIRED_DATE
    ) -> BomParentContextHandoff:
        return BomParentContextHandoff(
            plant_id=plant,
            required_date=required_date,
            evidence=self.citation(
                accepted, role="Production Requirement", artifact="0.json", ordinal=0
            ),
        )

    def loss_rate_handoff(
        self,
        accepted,
        *,
        component: str = COMPONENT,
        value: Any = "0.05",
        plant: str = PLANT,
        parent_material: str = PARENT,
        required_date: str = REQUIRED_DATE,
        artifact: str = "1.json",
        ordinal: int = 0,
        locator: str | None = None,
        basis: str = BASIS_LOSS_RATE,
    ) -> LossRateHandoff:
        return LossRateHandoff(
            plant_id=plant,
            parent_material_code=parent_material,
            required_date=required_date,
            evidence=self.citation(
                accepted, role="BOM Component", artifact=artifact, ordinal=ordinal
            ),
            component_material_code=component,
            loss_rate_evidence=(
                self.citation(
                    accepted,
                    role="BOM Component",
                    artifact=artifact,
                    ordinal=ordinal,
                    locator=locator or f"SIMULATED-SRC-LOSS-{component}",
                ),
            ),
            loss_rate=value,
            resolution_basis=basis,
        )

    def run_rule(
        self,
        datasets: list[tuple[str, list[dict[str, Any]]]],
        *,
        name: str,
        loss_rate_handoffs: tuple[LossRateHandoff, ...],
        parent_handoffs: tuple[BomParentContextHandoff, ...] | None = None,
    ):
        _, accepted = self.accepted(datasets, name=name)
        if parent_handoffs is None:
            parent_handoffs = (self.parent_handoff(accepted),)
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-01-15",
                bom_parent_context=parent_handoffs,
                loss_rate=loss_rate_handoffs,
            ),
        )
        return accepted, construction, compute_requirement_calculation(construction)

    # --- record builders -----------------------------------------------------------

    def requirement_record(
        self,
        *,
        plant: str = PLANT,
        material: str = PARENT,
        required_date: str = REQUIRED_DATE,
        production_qty: Any = "100",
    ) -> dict[str, Any]:
        record: dict[str, Any] = {
            "plant_id": plant,
            "material_code": material,
            "required_date": required_date,
        }
        if production_qty is not OMIT:
            record["ProductionQty"] = production_qty
        return with_provenance(
            record, [("ProductionQty", [EVIDENCE_REQUIREMENT], None)]
        )

    def bom_record(
        self,
        *,
        plant: str = PLANT,
        material: Any = COMPONENT,
        required_date: str = REQUIRED_DATE,
        bom_component_qty: Any = "2",
        loss_rate: Any = OMIT,
    ) -> dict[str, Any]:
        record: dict[str, Any] = {
            "plant_id": plant,
            "required_date": required_date,
        }
        if material is not OMIT:
            record["material_code"] = material
        if bom_component_qty is not OMIT:
            record["BOMComponentQty"] = bom_component_qty
        associations: list[tuple[str, list[str], str | None]] = [
            ("BOMComponentQty", [EVIDENCE_BOM], None)
        ]
        if loss_rate is not OMIT:
            record["loss_rate"] = loss_rate
            associations.append(
                ("loss_rate", [f"SIMULATED-SRC-LOSS-{material}"], BASIS_LOSS_RATE)
            )
        return with_provenance(record, associations)

    # --- assertions -----------------------------------------------------------------

    def assert_exact(self, value: Decimal | None, expected: str) -> None:
        self.assertIsNotNone(value)
        assert value is not None
        self.assertEqual(value, Decimal(expected))


class ArithmeticTests(RequirementCalculationTestCase):
    def test_base_requirement_is_the_exact_product(self) -> None:
        self.assert_exact(base_requirement(Decimal("100"), Decimal("2")), "200")

    def test_gross_requirement_is_the_exact_division(self) -> None:
        value = gross_requirement(Decimal("200"), Decimal("0.05"))
        self.assertEqual(format(value, "f"), EXACT_GROSS_200_5PCT)
        self.assertEqual(value * Decimal("0.95"), Decimal("200"))
        self.assertNotEqual(value, Decimal("210"))
        self.assertNotEqual(value, Decimal("211"))

    def test_zero_loss_is_identity(self) -> None:
        self.assert_exact(gross_requirement(Decimal("200"), Decimal("0")), "200")

    def test_no_binary_float_is_used(self) -> None:
        value = gross_requirement(Decimal("200"), Decimal("0.05"))
        self.assertIsInstance(value, Decimal)
        self.assertNotEqual(
            format(value, "f"), repr(float(Decimal("200") / Decimal("0.95")))
        )


class AcceptanceExampleTests(RequirementCalculationTestCase):
    def test_example_a_no_loss(self) -> None:
        _, accepted = self.accepted(
            [
                ("Production Requirement", [self.requirement_record()]),
                ("BOM Component", [self.bom_record(loss_rate="0")]),
            ],
            name="example-a-loss-rate",
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-01-15",
                bom_parent_context=(self.parent_handoff(accepted),),
                loss_rate=(self.loss_rate_handoff(accepted, value="0"),),
            ),
        )
        result = compute_requirement_calculation(construction)
        self.assertEqual(len(result.calculations), 1)
        calculation = result.calculations[0]
        self.assertEqual(calculation.outcome, OUTCOME_NUMERIC)
        self.assertEqual(calculation.plant_id, PLANT)
        self.assertEqual(calculation.component_material_code, COMPONENT)
        self.assertEqual(calculation.required_date, REQUIRED_DATE)
        self.assert_exact(calculation.base_requirement, "200")
        self.assert_exact(calculation.loss_rate, "0")
        self.assert_exact(calculation.gross_requirement, "200")
        self.assert_exact(calculation.cumulative_gross_requirement, "200")
        self.assertEqual(calculation.grain[0].value, PLANT)

    def test_example_b_five_percent_loss(self) -> None:
        _, accepted = self.accepted(
            [
                ("Production Requirement", [self.requirement_record()]),
                ("BOM Component", [self.bom_record(loss_rate="0.05")]),
            ],
            name="example-b",
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-01-15",
                bom_parent_context=(self.parent_handoff(accepted),),
                loss_rate=(self.loss_rate_handoff(accepted, value="0.05"),),
            ),
        )
        result = compute_requirement_calculation(construction)
        calculation = result.calculations[0]
        self.assertEqual(calculation.outcome, OUTCOME_NUMERIC)
        self.assert_exact(calculation.base_requirement, "200")
        self.assert_exact(calculation.loss_rate, "0.05")
        self.assertEqual(
            format(calculation.gross_requirement, "f"), EXACT_GROSS_200_5PCT
        )
        self.assertNotEqual(calculation.gross_requirement, Decimal("210"))
        self.assertNotEqual(calculation.gross_requirement, Decimal("211"))

    def test_example_c_missing_loss_rate_is_data_incomplete(self) -> None:
        # No resolved loss_rate context exists for this grain: the rule produces a
        # DATA_INCOMPLETE calculation and never defaults the value to 0, so no numeric
        # BaseRequirement / GrossRequirement is emitted at all.
        _, accepted = self.accepted(
            [
                ("Production Requirement", [self.requirement_record()]),
                ("BOM Component", [self.bom_record()]),
            ],
            name="example-c",
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-01-15",
                bom_parent_context=(self.parent_handoff(accepted),),
            ),
        )
        self.assertEqual(construction.loss_rate_contexts, ())
        result = compute_requirement_calculation(construction)
        self.assertEqual(len(result.calculations), 1)
        calculation = result.calculations[0]
        self.assertEqual(calculation.outcome, OUTCOME_DATA_INCOMPLETE)
        self.assertIsNone(calculation.gross_requirement)
        self.assertIsNone(calculation.base_requirement)
        self.assertIsNone(calculation.loss_rate)
        self.assertTrue(any("not defaulted to 0" in note for note in calculation.notes))

    def test_example_c_missing_loss_rate_value_is_data_incomplete(self) -> None:
        _, accepted = self.accepted(
            [
                ("Production Requirement", [self.requirement_record()]),
                ("BOM Component", [self.bom_record(loss_rate=None)]),
            ],
            name="example-c-null",
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-01-15",
                bom_parent_context=(self.parent_handoff(accepted),),
                loss_rate=(self.loss_rate_handoff(accepted, value=None),),
            ),
        )
        result = compute_requirement_calculation(construction)
        self.assertEqual(len(result.calculations), 1)
        calculation = result.calculations[0]
        self.assertEqual(calculation.outcome, OUTCOME_DATA_INCOMPLETE)
        self.assertIsNone(calculation.gross_requirement)
        self.assertIsNone(calculation.base_requirement)
        self.assertIsNone(calculation.cumulative_gross_requirement)

    def test_example_d_invalid_loss_rate_is_data_incomplete_without_clamp(self) -> None:
        for invalid in ("1.0", "-0.05", "1.2"):
            with self.subTest(loss_rate=invalid):
                _, accepted = self.accepted(
                    [
                        ("Production Requirement", [self.requirement_record()]),
                        ("BOM Component", [self.bom_record(loss_rate=invalid)]),
                    ],
                    name=f"example-d-{invalid.replace('.', '_').replace('-', 'neg')}",
                )
                construction = construct_canonical_objects(
                    accepted,
                    PhaseAHandoff(
                        analysis_run_id="RUN-1",
                        analysis_date="2026-01-15",
                        bom_parent_context=(self.parent_handoff(accepted),),
                        loss_rate=(self.loss_rate_handoff(accepted, value=invalid),),
                    ),
                )
                result = compute_requirement_calculation(construction)
                self.assertEqual(len(result.calculations), 1)
                calculation = result.calculations[0]
                self.assertEqual(calculation.outcome, OUTCOME_DATA_INCOMPLETE)
                self.assertIsNone(calculation.gross_requirement)
                self.assertIsNone(calculation.loss_rate)
                self.assertTrue(
                    any("0 <= loss_rate < 1" in note for note in calculation.notes)
                )

    def test_example_e_unresolved_bom_is_data_incomplete(self) -> None:
        # The BOM Component cannot be bound to a resolved requirement context, so no
        # calculation grain exists at all and nothing is guessed.
        _, accepted = self.accepted(
            [
                ("Production Requirement", [self.requirement_record()]),
                ("BOM Component", [self.bom_record(loss_rate="0.05")]),
            ],
            name="example-e",
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(analysis_run_id="RUN-1", analysis_date="2026-01-15"),
        )
        self.assertEqual(construction.objects_for("BOM Component"), ())
        result = compute_requirement_calculation(construction)
        self.assertEqual(result.calculations, ())
        self.assertEqual(result.numeric, ())

    def test_example_f_cumulative_requirement(self) -> None:
        _, accepted = self.accepted(
            [
                (
                    "Production Requirement",
                    [
                        self.requirement_record(
                            required_date="2026-10-10", production_qty="100"
                        ),
                        self.requirement_record(
                            required_date="2026-10-15", production_qty="70"
                        ),
                    ],
                ),
                (
                    "BOM Component",
                    [
                        self.bom_record(
                            required_date="2026-10-10", bom_component_qty="1",
                            loss_rate="0",
                        ),
                        self.bom_record(
                            required_date="2026-10-15", bom_component_qty="1",
                            loss_rate="0",
                        ),
                    ],
                ),
            ],
            name="example-f",
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-10-01",
                bom_parent_context=(
                    BomParentContextHandoff(
                        plant_id=PLANT,
                        required_date="2026-10-10",
                        evidence=self.citation(
                            accepted,
                            role="Production Requirement",
                            artifact="0.json",
                            ordinal=0,
                        ),
                    ),
                    BomParentContextHandoff(
                        plant_id=PLANT,
                        required_date="2026-10-15",
                        evidence=self.citation(
                            accepted,
                            role="Production Requirement",
                            artifact="0.json",
                            ordinal=1,
                        ),
                    ),
                ),
                loss_rate=(
                    self.loss_rate_handoff(
                        accepted, value="0", required_date="2026-10-10", ordinal=0
                    ),
                    self.loss_rate_handoff(
                        accepted, value="0", required_date="2026-10-15", ordinal=1
                    ),
                ),
            ),
        )
        result = compute_requirement_calculation(construction)
        self.assertEqual(len(result.calculations), 2)
        first = result.for_grain(PLANT, COMPONENT, "2026-10-10")
        second = result.for_grain(PLANT, COMPONENT, "2026-10-15")
        assert first is not None and second is not None
        self.assert_exact(first.gross_requirement, "100")
        self.assert_exact(second.gross_requirement, "70")
        self.assert_exact(first.cumulative_gross_requirement, "100")
        self.assert_exact(second.cumulative_gross_requirement, "170")

    def test_example_g_substitute_supply_does_not_reduce_the_requirement(self) -> None:
        # Substitute Supply is supply-side (``§2.3``) and must not change the
        # requirement-side result (``§2.4.10``).  The rule exposes no supply input at all,
        # and a construction carrying substitute relationships still yields the same
        # GrossRequirement.
        _, accepted = self.accepted(
            [
                ("Production Requirement", [self.requirement_record()]),
                ("BOM Component", [self.bom_record(loss_rate="0")]),
                (
                    "Substitute Relationship",
                    [
                        {
                            "plant_id": PLANT,
                            "target_material_code": COMPONENT,
                            "substitute_material_code": "M7",
                            "substitution_ratio": "0.5",
                            "approval_status": "APPROVED",
                        }
                    ],
                ),
            ],
            name="example-g",
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-01-15",
                bom_parent_context=(self.parent_handoff(accepted),),
                loss_rate=(self.loss_rate_handoff(accepted, value="0"),),
            ),
        )
        self.assertEqual(len(construction.objects_for("Substitute Relationship")), 1)
        result = compute_requirement_calculation(construction)
        calculation = result.calculations[0]
        self.assert_exact(calculation.gross_requirement, "200")
        self.assert_exact(calculation.base_requirement, "200")
        # The rule signature only accepts the construction report: there is no supply-side
        # parameter through which a substitute quantity could reduce the requirement.
        import inspect

        signature = inspect.signature(compute_requirement_calculation)
        self.assertEqual(list(signature.parameters), ["report"])


class GrainAndIsolationTests(RequirementCalculationTestCase):
    def test_separate_plants_never_aggregate(self) -> None:
        _, accepted = self.accepted(
            [
                (
                    "Production Requirement",
                    [
                        self.requirement_record(plant=PLANT, production_qty="100"),
                        self.requirement_record(
                            plant=PLANT_B, material="M9", production_qty="50"
                        ),
                    ],
                ),
                (
                    "BOM Component",
                    [
                        self.bom_record(plant=PLANT, bom_component_qty="1", loss_rate="0"),
                        self.bom_record(
                            plant=PLANT_B, material="M9", bom_component_qty="1",
                            loss_rate="0",
                        ),
                    ],
                ),
            ],
            name="separate-plants",
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-01-15",
                bom_parent_context=(
                    BomParentContextHandoff(
                        plant_id=PLANT,
                        required_date=REQUIRED_DATE,
                        evidence=self.citation(
                            accepted,
                            role="Production Requirement",
                            artifact="0.json",
                            ordinal=0,
                        ),
                    ),
                    BomParentContextHandoff(
                        plant_id=PLANT_B,
                        required_date=REQUIRED_DATE,
                        evidence=self.citation(
                            accepted,
                            role="Production Requirement",
                            artifact="0.json",
                            ordinal=1,
                        ),
                    ),
                ),
                loss_rate=(
                    self.loss_rate_handoff(
                        accepted, value="0", plant=PLANT, ordinal=0
                    ),
                    self.loss_rate_handoff(
                        accepted,
                        value="0",
                        plant=PLANT_B,
                        parent_material="M9",
                        component="M9",
                        ordinal=1,
                    ),
                ),
            ),
        )
        result = compute_requirement_calculation(construction)
        plant_a = result.for_plant_component(PLANT, COMPONENT)
        plant_b = result.for_plant_component(PLANT_B, "M9")
        self.assertEqual(len(plant_a), 1)
        self.assertEqual(len(plant_b), 1)
        self.assert_exact(plant_a[0].gross_requirement, "100")
        self.assert_exact(plant_b[0].gross_requirement, "50")
        # Each plant's cumulative value only ever covers its own contributions.
        self.assert_exact(plant_a[0].cumulative_gross_requirement, "100")
        self.assert_exact(plant_b[0].cumulative_gross_requirement, "50")

    def test_same_component_under_different_contexts_does_not_cross_reuse(self) -> None:
        # One component M2 under two different parent requirements: each calculation must
        # use its own ProductionQty / BOMComponentQty / loss_rate.
        _, accepted = self.accepted(
            [
                (
                    "Production Requirement",
                    [
                        self.requirement_record(
                            required_date="2026-10-10", production_qty="100"
                        ),
                        self.requirement_record(
                            required_date="2026-10-15", production_qty="100"
                        ),
                    ],
                ),
                (
                    "BOM Component",
                    [
                        self.bom_record(
                            required_date="2026-10-10", bom_component_qty="2",
                            loss_rate="0",
                        ),
                        self.bom_record(
                            required_date="2026-10-15", bom_component_qty="2",
                            loss_rate="0.5",
                        ),
                    ],
                ),
            ],
            name="cross-context",
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-10-01",
                bom_parent_context=(
                    BomParentContextHandoff(
                        plant_id=PLANT,
                        required_date="2026-10-10",
                        evidence=self.citation(
                            accepted,
                            role="Production Requirement",
                            artifact="0.json",
                            ordinal=0,
                        ),
                    ),
                    BomParentContextHandoff(
                        plant_id=PLANT,
                        required_date="2026-10-15",
                        evidence=self.citation(
                            accepted,
                            role="Production Requirement",
                            artifact="0.json",
                            ordinal=1,
                        ),
                    ),
                ),
                loss_rate=(
                    self.loss_rate_handoff(
                        accepted, value="0", required_date="2026-10-10", ordinal=0
                    ),
                    self.loss_rate_handoff(
                        accepted, value="0.5", required_date="2026-10-15", ordinal=1
                    ),
                ),
            ),
        )
        result = compute_requirement_calculation(construction)
        first = result.for_grain(PLANT, COMPONENT, "2026-10-10")
        second = result.for_grain(PLANT, COMPONENT, "2026-10-15")
        assert first is not None and second is not None
        self.assert_exact(first.loss_rate, "0")
        self.assert_exact(second.loss_rate, "0.5")
        self.assert_exact(first.gross_requirement, "200")
        self.assert_exact(second.gross_requirement, "400")
        # Different Requirement Calculation Contexts, different loss_rate provenance.
        self.assertNotEqual(
            first.loss_rate_provenance.logical_observation,
            None,
        )
        self.assertNotEqual(
            first.loss_rate_context_grain, second.loss_rate_context_grain
        )

    def test_m2_and_m3_under_one_parent_use_their_own_loss_rate(self) -> None:
        _, accepted = self.accepted(
            [
                ("Production Requirement", [self.requirement_record()]),
                (
                    "BOM Component",
                    [
                        self.bom_record(
                            material=COMPONENT, bom_component_qty="2", loss_rate="0.02"
                        ),
                        self.bom_record(
                            material=COMPONENT_B, bom_component_qty="4", loss_rate="0.06"
                        ),
                    ],
                ),
            ],
            name="m2-m3",
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-01-15",
                bom_parent_context=(self.parent_handoff(accepted),),
                loss_rate=(
                    self.loss_rate_handoff(
                        accepted, component=COMPONENT, value="0.02", ordinal=0
                    ),
                    self.loss_rate_handoff(
                        accepted, component=COMPONENT_B, value="0.06", ordinal=1
                    ),
                ),
            ),
        )
        result = compute_requirement_calculation(construction)
        self.assertEqual(len(result.calculations), 2)
        m2 = result.for_grain(PLANT, COMPONENT, REQUIRED_DATE)
        m3 = result.for_grain(PLANT, COMPONENT_B, REQUIRED_DATE)
        assert m2 is not None and m3 is not None
        self.assert_exact(m2.base_requirement, "200")
        self.assert_exact(m2.loss_rate, "0.02")
        self.assert_exact(m3.base_requirement, "400")
        self.assert_exact(m3.loss_rate, "0.06")
        # No cross-context reuse: each component's gross value uses its own loss_rate.
        self.assertEqual(
            m2.gross_requirement,
            gross_requirement(Decimal("200"), Decimal("0.02")),
        )
        self.assertEqual(
            m3.gross_requirement,
            gross_requirement(Decimal("400"), Decimal("0.06")),
        )
        self.assertNotEqual(
            m2.gross_requirement,
            gross_requirement(Decimal("200"), Decimal("0.06")),
        )
        self.assertNotEqual(
            m3.gross_requirement,
            gross_requirement(Decimal("400"), Decimal("0.02")),
        )

    def test_calculation_order_is_deterministic(self) -> None:
        # Same-date multi-contribution for one component/context is governed upstream by
        # the exactly-one BOM relationship contract, so the ordering that matters here is
        # the calculation grain order, which must be stable and reproducible.
        _, accepted = self.accepted(
            [
                ("Production Requirement", [self.requirement_record()]),
                (
                    "BOM Component",
                    [
                        self.bom_record(
                            material=COMPONENT, bom_component_qty="2", loss_rate="0.02"
                        ),
                        self.bom_record(
                            material=COMPONENT_B, bom_component_qty="4", loss_rate="0.06"
                        ),
                    ],
                ),
            ],
            name="order",
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-01-15",
                bom_parent_context=(self.parent_handoff(accepted),),
                loss_rate=(
                    self.loss_rate_handoff(
                        accepted, component=COMPONENT, value="0.02", ordinal=0
                    ),
                    self.loss_rate_handoff(
                        accepted, component=COMPONENT_B, value="0.06", ordinal=1
                    ),
                ),
            ),
        )
        first = compute_requirement_calculation(construction)
        second = compute_requirement_calculation(construction)
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(
            [item.component_material_code for item in first.calculations],
            [COMPONENT, COMPONENT_B],
        )


class FailSafeTests(RequirementCalculationTestCase):
    def test_missing_bom_component_qty_is_data_incomplete(self) -> None:
        _, accepted = self.accepted(
            [
                ("Production Requirement", [self.requirement_record()]),
                ("BOM Component", [self.bom_record(bom_component_qty=OMIT, loss_rate="0")]),
            ],
            name="missing-bom-qty",
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-01-15",
                bom_parent_context=(self.parent_handoff(accepted),),
                loss_rate=(self.loss_rate_handoff(accepted, value="0"),),
            ),
        )
        result = compute_requirement_calculation(construction)
        self.assertEqual(len(result.calculations), 1)
        self.assertEqual(result.calculations[0].outcome, OUTCOME_DATA_INCOMPLETE)
        self.assertIsNone(result.calculations[0].gross_requirement)

    def test_missing_production_qty_is_data_incomplete(self) -> None:
        _, accepted = self.accepted(
            [
                (
                    "Production Requirement",
                    [self.requirement_record(production_qty=OMIT)],
                ),
                ("BOM Component", [self.bom_record(loss_rate="0")]),
            ],
            name="missing-production-qty",
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-01-15",
                bom_parent_context=(self.parent_handoff(accepted),),
                loss_rate=(self.loss_rate_handoff(accepted, value="0"),),
            ),
        )
        result = compute_requirement_calculation(construction)
        self.assertEqual(len(result.calculations), 1)
        self.assertEqual(result.calculations[0].outcome, OUTCOME_DATA_INCOMPLETE)

    def test_negative_quantities_are_data_incomplete(self) -> None:
        cases = {
            "negative-production": (self.requirement_record(production_qty="-1"), self.bom_record(loss_rate="0")),
            "negative-bom": (self.requirement_record(), self.bom_record(bom_component_qty="-2", loss_rate="0")),
        }
        for label, (requirement, component) in cases.items():
            with self.subTest(case=label):
                _, accepted = self.accepted(
                    [
                        ("Production Requirement", [requirement]),
                        ("BOM Component", [component]),
                    ],
                    name=label,
                )
                construction = construct_canonical_objects(
                    accepted,
                    PhaseAHandoff(
                        analysis_run_id="RUN-1",
                        analysis_date="2026-01-15",
                        bom_parent_context=(self.parent_handoff(accepted),),
                        loss_rate=(self.loss_rate_handoff(accepted, value="0"),),
                    ),
                )
                result = compute_requirement_calculation(construction)
                self.assertEqual(result.calculations[0].outcome, OUTCOME_DATA_INCOMPLETE)
                self.assertIsNone(result.calculations[0].gross_requirement)

    def test_unresolved_component_identity_is_data_incomplete(self) -> None:
        # The component material_code is omitted, so canonicalization leaves the BOM
        # Component unresolved and the rule reports it rather than guessing.
        _, accepted = self.accepted(
            [
                ("Production Requirement", [self.requirement_record()]),
                (
                    "BOM Component",
                    [self.bom_record(material=OMIT, loss_rate="0")],
                ),
            ],
            name="unresolved-component",
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-01-15",
                bom_parent_context=(self.parent_handoff(accepted),),
            ),
        )
        result = compute_requirement_calculation(construction)
        self.assertEqual(result.calculations, ())
        self.assertEqual(result.numeric, ())

    def test_data_incomplete_never_carries_a_numeric_gross_requirement(self) -> None:
        _, accepted = self.accepted(
            [
                ("Production Requirement", [self.requirement_record()]),
                ("BOM Component", [self.bom_record(loss_rate="1.0")]),
            ],
            name="no-numeric",
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-01-15",
                bom_parent_context=(self.parent_handoff(accepted),),
                loss_rate=(self.loss_rate_handoff(accepted, value="1.0"),),
            ),
        )
        result = compute_requirement_calculation(construction)
        payload = result.to_dict()
        calculation = payload["calculations"][0]
        self.assertEqual(calculation["outcome"], OUTCOME_DATA_INCOMPLETE)
        self.assertIsNone(calculation["GrossRequirement"])
        self.assertIsNone(calculation["BaseRequirement"])
        self.assertIsNone(calculation["CumulativeGrossRequirement"])


class OutputAndBoundaryTests(RequirementCalculationTestCase):
    def test_result_exposes_the_minimum_required_fields(self) -> None:
        _, accepted = self.accepted(
            [
                ("Production Requirement", [self.requirement_record()]),
                ("BOM Component", [self.bom_record(loss_rate="0.05")]),
            ],
            name="minimum-output",
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-01-15",
                bom_parent_context=(self.parent_handoff(accepted),),
                loss_rate=(self.loss_rate_handoff(accepted, value="0.05"),),
            ),
        )
        result = compute_requirement_calculation(construction)
        payload = result.to_dict()
        self.assertEqual(payload["rule"], RULE_ID)
        calculation = payload["calculations"][0]
        for field in (
            "plant_id",
            "component_material_code",
            "required_date",
            "BaseRequirement",
            "loss_rate",
            "GrossRequirement",
            "CumulativeGrossRequirement",
            "outcome",
            "trace",
        ):
            with self.subTest(field=field):
                self.assertIn(field, calculation)
        trace = calculation["trace"]
        self.assertIn("production_requirement_reference", trace)
        self.assertIn("bom_component_reference", trace)
        self.assertIn("loss_rate_context_grain", trace)

    def test_rule_consumes_only_resolved_canonical_output(self) -> None:
        # The rule is a pure function of the construction report: feeding it a report with
        # no resolved objects yields no calculation, and no raw artifact is read.
        _, accepted = self.accepted(
            [("Production Requirement", [self.requirement_record()])],
            name="no-components",
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(analysis_run_id="RUN-1", analysis_date="2026-01-15"),
        )
        result = compute_requirement_calculation(construction)
        self.assertEqual(result.calculations, ())

    def test_deterministic_repeatability(self) -> None:
        _, accepted = self.accepted(
            [
                ("Production Requirement", [self.requirement_record()]),
                ("BOM Component", [self.bom_record(loss_rate="0.05")]),
            ],
            name="deterministic",
        )
        phase_a = PhaseAHandoff(
            analysis_run_id="RUN-1",
            analysis_date="2026-01-15",
            bom_parent_context=(self.parent_handoff(accepted),),
            loss_rate=(self.loss_rate_handoff(accepted, value="0.05"),),
        )
        construction = construct_canonical_objects(accepted, phase_a)
        first = compute_requirement_calculation(construction).to_dict()
        second = compute_requirement_calculation(construction).to_dict()
        self.assertEqual(first, second)

    def test_no_new_validation_taxonomy_is_used(self) -> None:
        _, accepted = self.accepted(
            [
                ("Production Requirement", [self.requirement_record()]),
                ("BOM Component", [self.bom_record(loss_rate="1.0")]),
            ],
            name="taxonomy",
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-01-15",
                bom_parent_context=(self.parent_handoff(accepted),),
                loss_rate=(self.loss_rate_handoff(accepted, value="1.0"),),
            ),
        )
        before = construction.to_dict()
        result = compute_requirement_calculation(construction)
        # The rule adds no issue of its own: it reuses the canonical findings unchanged.
        for calculation in result.calculations:
            for issue in calculation.inherited_issues:
                self.assertIn(issue.category, {
                    "FIELD_VALUE",
                    "IDENTITY_RESOLUTION",
                    "SEMANTIC_RESOLUTION",
                    "CONSISTENCY",
                    "PROVENANCE",
                    "BUSINESS_DATA",
                    "PACKAGE_STRUCTURE",
                })
        # The construction report itself is not mutated by the rule.
        self.assertEqual(before, construction.to_dict())


if __name__ == "__main__":
    unittest.main()
