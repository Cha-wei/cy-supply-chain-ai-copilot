"""``BR-REQUIREMENT-001`` Requirement Calculation tests (POC Design v0.2 §2.4).

Coverage mirrors the registered acceptance examples and the rule's fail-safe boundary:

* Example A -- no loss (``Base = 200``, ``Gross = 200``);
* Example B -- 5% loss (``Gross = 200 / 0.95 = 4000 / 19`` exact rational);
* Example C -- missing ``loss_rate`` -> ``DATA_INCOMPLETE``, no numeric requirement;
* Example D -- invalid ``loss_rate`` (``1.0`` / negative) -> ``DATA_INCOMPLETE``, no clamp;
* Example E -- BOM unresolved -> ``DATA_INCOMPLETE``;
* Example F -- cumulative requirement per registered grouping;
* Example G -- substitute supply cannot reduce the requirement side;
* unresolved plant / component identity / required_date -> ``DATA_INCOMPLETE``;
* the calculation context comes from the resolved Production Requirement context, not from
  duplicated fields on the BOM record;
* separate plants never aggregate; the same component under different Requirement
  Calculation Contexts never reuses another context; ``M2`` / ``M3`` under one parent use
  their own ``loss_rate``; deterministic ordering and exact rational arithmetic.

All fixtures are SIMULATED.
"""

from __future__ import annotations

import unittest
import uuid
from fractions import Fraction
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
from snapshot_loader.canonical_objects import (
    AnalysisRunContext,
    CanonicalConstructionReport,
    CanonicalObject,
    CanonicalObjectSet,
    CanonicalProperty,
    ContextValueReference,
    EvidenceReference,
)
from snapshot_loader.requirement_calculation import (
    OUTCOME_DATA_INCOMPLETE,
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
    """Shared scaffolding: real accepted packages, plus a direct canonical-report fixture."""

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

    # --- construction helpers -------------------------------------------------------

    def single_component_construction(
        self,
        *,
        name: str,
        loss_rate: Any = "0",
        component: Any = COMPONENT,
        bom_component_qty: Any = "2",
        production_qty: Any = "100",
        include_loss_rate: bool = True,
        component_material: Any = COMPONENT,
    ) -> CanonicalConstructionReport:
        requirement = self.requirement_record(production_qty=production_qty)
        component_record = self.bom_record(
            material=component_material,
            bom_component_qty=bom_component_qty,
            loss_rate=loss_rate if include_loss_rate else OMIT,
        )
        _, accepted = self.accepted(
            [
                ("Production Requirement", [requirement]),
                ("BOM Component", [component_record]),
            ],
            name=name,
        )
        payload: dict[str, Any] = {
            "analysis_run_id": "RUN-1",
            "analysis_date": "2026-01-15",
            "bom_parent_context": (self.parent_handoff(accepted),),
        }
        if include_loss_rate:
            payload["loss_rate"] = (
                self.loss_rate_handoff(accepted, value=loss_rate, component=component),
            )
        return construct_canonical_objects(accepted, PhaseAHandoff(**payload))

    def two_date_construction(
        self,
        *,
        name: str,
        quantities: tuple[str, str],
        loss_rates: tuple[str, str],
        bom_quantities: tuple[str, str] = ("2", "2"),
    ) -> CanonicalConstructionReport:
        dates = ("2026-10-10", "2026-10-15")
        _, accepted = self.accepted(
            [
                (
                    "Production Requirement",
                    [
                        self.requirement_record(required_date=dates[0], production_qty=quantities[0]),
                        self.requirement_record(required_date=dates[1], production_qty=quantities[1]),
                    ],
                ),
                (
                    "BOM Component",
                    [
                        self.bom_record(
                            required_date=dates[0],
                            bom_component_qty=bom_quantities[0],
                            loss_rate=loss_rates[0],
                        ),
                        self.bom_record(
                            required_date=dates[1],
                            bom_component_qty=bom_quantities[1],
                            loss_rate=loss_rates[1],
                        ),
                    ],
                ),
            ],
            name=name,
        )
        return construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-10-01",
                bom_parent_context=tuple(
                    BomParentContextHandoff(
                        plant_id=PLANT,
                        required_date=dates[index],
                        evidence=self.citation(
                            accepted,
                            role="Production Requirement",
                            artifact="0.json",
                            ordinal=index,
                        ),
                    )
                    for index in (0, 1)
                ),
                loss_rate=tuple(
                    self.loss_rate_handoff(
                        accepted,
                        value=loss_rates[index],
                        required_date=dates[index],
                        ordinal=index,
                    )
                    for index in (0, 1)
                ),
            ),
        )

    # --- direct canonical report fixture --------------------------------------------

    def canonical_report(
        self,
        *,
        component_local_plant_and_date: bool = True,
        component_material: Any = COMPONENT,
        production_qty: Any = "100",
        bom_component_qty: Any = "2",
        loss_rate_value: Any = "0",
        include_loss_rate_context: bool = True,
        include_parent: bool = True,
    ) -> CanonicalConstructionReport:
        """Build a valid canonical construction report directly (no raw artifacts)."""

        provenance = EvidenceReference(
            snapshot_package_identity="SIMULATED-PKG-0001",
            logical_dataset_role="Production Requirement",
            artifact="0.json",
            record_ordinal=0,
            logical_observation="ProductionQty",
            stable_source_evidence_locators=(EVIDENCE_REQUIREMENT,),
        )
        requirement_properties = [
            CanonicalProperty("plant_id", PLANT),
            CanonicalProperty("material_code", PARENT),
            CanonicalProperty("required_date", REQUIRED_DATE),
        ]
        if production_qty is not OMIT:
            requirement_properties.append(
                CanonicalProperty("ProductionQty", production_qty)
            )
        requirement = CanonicalObject(
            canonical_target="Production Requirement",
            canonicalization_role="Production Requirement",
            grain=(
                CanonicalProperty("plant_id", PLANT),
                CanonicalProperty("material_code", PARENT),
                CanonicalProperty("required_date", REQUIRED_DATE),
            ),
            properties=tuple(requirement_properties),
            non_applicable_properties=(),
            record_reference="SIMULATED-PKG-0001|Production Requirement|0.json|0",
            provenance=provenance,
        )

        component_properties: list[CanonicalProperty] = []
        if component_local_plant_and_date:
            component_properties.extend(
                [
                    CanonicalProperty("plant_id", PLANT),
                    CanonicalProperty("required_date", REQUIRED_DATE),
                ]
            )
        if component_material is not OMIT:
            component_properties.append(
                CanonicalProperty("material_code", component_material)
            )
        if bom_component_qty is not OMIT:
            component_properties.append(
                CanonicalProperty("BOMComponentQty", bom_component_qty)
            )
        component = CanonicalObject(
            canonical_target="BOM Component",
            canonicalization_role="BOM Component",
            grain=(
                CanonicalProperty("material_code", component_material),
            ),
            properties=tuple(component_properties),
            non_applicable_properties=(),
            record_reference="SIMULATED-PKG-0001|BOM Component|1.json|0",
            provenance=EvidenceReference(
                snapshot_package_identity="SIMULATED-PKG-0001",
                logical_dataset_role="BOM Component",
                artifact="1.json",
                record_ordinal=0,
                logical_observation="BOMComponentQty",
                stable_source_evidence_locators=(EVIDENCE_BOM,),
            ),
            context_reference=(
                requirement.record_reference if include_parent else None
            ),
            context_provenance=provenance if include_parent else None,
        )

        contexts: tuple[ContextValueReference, ...] = ()
        if include_loss_rate_context:
            contexts = (
                ContextValueReference(
                    semantic="loss_rate",
                    grain=(
                        CanonicalProperty("plant_id", PLANT),
                        CanonicalProperty("material_code", PARENT),
                        CanonicalProperty("required_date", REQUIRED_DATE),
                        CanonicalProperty("component_material_code", COMPONENT),
                    ),
                    value=loss_rate_value,
                    provenance=EvidenceReference(
                        snapshot_package_identity="SIMULATED-PKG-0001",
                        logical_dataset_role="BOM Component",
                        artifact="1.json",
                        record_ordinal=0,
                        logical_observation="loss_rate",
                        stable_source_evidence_locators=(
                            f"SIMULATED-SRC-LOSS-{COMPONENT}",
                        ),
                        mapping_resolution_basis=BASIS_LOSS_RATE,
                    ),
                ),
            )

        return CanonicalConstructionReport(
            package_id="SIMULATED-PKG-0001",
            accepted_content_view_digest="simulated-view",
            analysis_run=AnalysisRunContext(
                analysis_run_id="RUN-1",
                analysis_date="2026-01-15",
                snapshot_package_identity="SIMULATED-PKG-0001",
                accepted_content_view_digest="simulated-view",
            ),
            analysis_date_resolved=True,
            object_sets=(
                CanonicalObjectSet(
                    "Production Requirement",
                    resolved=(requirement,) if include_parent else (),
                ),
                CanonicalObjectSet("BOM Component", resolved=(component,)),
            ),
            inbound_records=(),
            substitute_allocations=(),
            effective_demand_contexts=(),
            loss_rate_contexts=contexts,
            safety_stock_contexts=(),
            unrecognized_roles=(),
            checks=(),
            issues=(),
        )

    # --- assertions -----------------------------------------------------------------

    def assert_exact(self, value: Fraction | None, expected: Fraction) -> None:
        self.assertIsNotNone(value)
        assert value is not None
        self.assertEqual(value, expected)
        self.assertEqual(value.numerator, expected.numerator)
        self.assertEqual(value.denominator, expected.denominator)


class ArithmeticTests(RequirementCalculationTestCase):
    def test_base_requirement_is_the_exact_product(self) -> None:
        self.assert_exact(
            base_requirement(Fraction(100), Fraction(2)), Fraction(200, 1)
        )

    def test_gross_requirement_is_the_exact_rational(self) -> None:
        value = gross_requirement(Fraction(200), Fraction(1, 20))
        self.assertEqual(value, Fraction(4000, 19))
        self.assertEqual(value.numerator, 4000)
        self.assertEqual(value.denominator, 19)

    def test_zero_loss_is_identity(self) -> None:
        self.assert_exact(
            gross_requirement(Fraction(200), Fraction(0)), Fraction(200, 1)
        )

    def test_no_fixed_decimal_precision_participates(self) -> None:
        import snapshot_loader.requirement_calculation as module

        self.assertFalse(hasattr(module, "WORKING_DECIMAL_PRECISION"))
        self.assertNotIn("OUTCOME_NUMERIC", module.__all__)
        source = Path(module.__file__).read_text(encoding="utf-8")
        for forbidden in ("localcontext", "quantize", "round("):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_no_binary_float_is_used(self) -> None:
        value = gross_requirement(Fraction(200), Fraction(1, 20))
        self.assertIsInstance(value, Fraction)
        self.assertEqual(value * 19, Fraction(4000))
        # Any finite decimal expansion of this quantity is a lossy approximation.
        self.assertNotEqual(value.denominator, 1)


class AcceptanceExampleTests(RequirementCalculationTestCase):
    def test_example_a_no_loss(self) -> None:
        construction = self.single_component_construction(name="example-a", loss_rate="0")
        result = compute_requirement_calculation(construction)
        self.assertEqual(len(result.calculations), 1)
        calculation = result.calculations[0]
        # A successful calculation carries no invented success status.
        self.assertIsNone(calculation.outcome)
        self.assertTrue(calculation.has_numeric_result)
        self.assertEqual(calculation.plant_id, PLANT)
        self.assertEqual(calculation.component_material_code, COMPONENT)
        self.assertEqual(calculation.required_date, REQUIRED_DATE)
        self.assert_exact(calculation.base_requirement, Fraction(200, 1))
        # The resolved canonical input keeps its exact decimal representation.
        self.assertEqual(calculation.loss_rate, '0')
        self.assert_exact(calculation.exact_loss_rate(), Fraction(0, 1))
        self.assert_exact(calculation.gross_requirement, Fraction(200, 1))
        self.assert_exact(calculation.cumulative_gross_requirement, Fraction(200, 1))

    def test_example_b_five_percent_loss(self) -> None:
        construction = self.single_component_construction(
            name="example-b", loss_rate="0.05"
        )
        result = compute_requirement_calculation(construction)
        calculation = result.calculations[0]
        self.assertIsNone(calculation.outcome)
        self.assert_exact(calculation.base_requirement, Fraction(200, 1))
        self.assertEqual(calculation.loss_rate, '0.05')
        self.assert_exact(calculation.exact_loss_rate(), Fraction(1, 20))
        self.assert_exact(calculation.gross_requirement, Fraction(4000, 19))
        self.assertEqual(calculation.gross_requirement.numerator, 4000)
        self.assertEqual(calculation.gross_requirement.denominator, 19)

    def test_example_c_missing_loss_rate_is_data_incomplete(self) -> None:
        construction = self.single_component_construction(
            name="example-c", include_loss_rate=False
        )
        self.assertEqual(construction.loss_rate_contexts, ())
        result = compute_requirement_calculation(construction)
        self.assertEqual(len(result.calculations), 1)
        calculation = result.calculations[0]
        self.assertEqual(calculation.outcome, OUTCOME_DATA_INCOMPLETE)
        self.assertFalse(calculation.has_numeric_result)
        self.assertIsNone(calculation.gross_requirement)
        self.assertIsNone(calculation.base_requirement)
        self.assertIsNone(calculation.loss_rate)
        self.assertTrue(any("not defaulted to 0" in note for note in calculation.notes))

    def test_example_c_missing_loss_rate_value_is_data_incomplete(self) -> None:
        construction = self.single_component_construction(
            name="example-c-null", loss_rate=None
        )
        result = compute_requirement_calculation(construction)
        calculation = result.calculations[0]
        self.assertEqual(calculation.outcome, OUTCOME_DATA_INCOMPLETE)
        self.assertIsNone(calculation.gross_requirement)
        self.assertIsNone(calculation.cumulative_gross_requirement)

    def test_example_d_invalid_loss_rate_is_data_incomplete_without_clamp(self) -> None:
        for invalid in ("1.0", "-0.05", "1.2"):
            with self.subTest(loss_rate=invalid):
                construction = self.single_component_construction(
                    name=f"example-d-{invalid.replace('.', '_').replace('-', 'neg')}",
                    loss_rate=invalid,
                )
                result = compute_requirement_calculation(construction)
                calculation = result.calculations[0]
                self.assertEqual(calculation.outcome, OUTCOME_DATA_INCOMPLETE)
                self.assertIsNone(calculation.gross_requirement)
                self.assertIsNone(calculation.loss_rate)
                self.assertTrue(
                    any("0 <= loss_rate < 1" in note for note in calculation.notes)
                )

    def test_example_e_unresolved_bom_is_data_incomplete(self) -> None:
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
        self.assertEqual(len(construction.unresolved_for("BOM Component")), 1)
        result = compute_requirement_calculation(construction)
        self.assertEqual(len(result.calculations), 1)
        calculation = result.calculations[0]
        self.assertEqual(calculation.outcome, OUTCOME_DATA_INCOMPLETE)
        self.assertIsNone(calculation.base_requirement)
        self.assertIsNone(calculation.gross_requirement)
        self.assertIsNone(calculation.cumulative_gross_requirement)
        # The BOM evidence / reference and the canonical issues stay available for audit.
        self.assertIsNotNone(calculation.bom_component_reference)
        self.assertTrue(calculation.inherited_issues)
        self.assertTrue(
            any(
                "no resolved Production Requirement context" in note
                for note in calculation.notes
            )
        )

    def test_example_f_cumulative_requirement(self) -> None:
        construction = self.two_date_construction(
            name="example-f",
            quantities=("100", "70"),
            loss_rates=("0", "0"),
            bom_quantities=("1", "1"),
        )
        result = compute_requirement_calculation(construction)
        self.assertEqual(len(result.calculations), 2)
        first = result.for_grain(PLANT, COMPONENT, "2026-10-10")
        second = result.for_grain(PLANT, COMPONENT, "2026-10-15")
        assert first is not None and second is not None
        self.assert_exact(first.gross_requirement, Fraction(100, 1))
        self.assert_exact(second.gross_requirement, Fraction(70, 1))
        self.assert_exact(first.cumulative_gross_requirement, Fraction(100, 1))
        self.assert_exact(second.cumulative_gross_requirement, Fraction(170, 1))

    def test_example_g_substitute_supply_does_not_reduce_the_requirement(self) -> None:
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
        self.assert_exact(calculation.gross_requirement, Fraction(200, 1))
        self.assert_exact(calculation.base_requirement, Fraction(200, 1))
        import inspect

        signature = inspect.signature(compute_requirement_calculation)
        self.assertEqual(list(signature.parameters), ["report"])


class ExactCumulativeTests(RequirementCalculationTestCase):
    def test_cumulative_stays_exact_with_non_terminating_contributions(self) -> None:
        # 4000/19 + 4000/19 = 8000/19 exactly, with no Decimal context re-entry.
        construction = self.two_date_construction(
            name="exact-cumulative",
            quantities=("100", "100"),
            loss_rates=("0.05", "0.05"),
        )
        result = compute_requirement_calculation(construction)
        first = result.for_grain(PLANT, COMPONENT, "2026-10-10")
        second = result.for_grain(PLANT, COMPONENT, "2026-10-15")
        assert first is not None and second is not None
        self.assert_exact(first.gross_requirement, Fraction(4000, 19))
        self.assert_exact(first.cumulative_gross_requirement, Fraction(4000, 19))
        self.assert_exact(second.cumulative_gross_requirement, Fraction(8000, 19))
        self.assertEqual(second.cumulative_gross_requirement.denominator, 19)


class CanonicalLossRateRepresentationTests(RequirementCalculationTestCase):
    """``loss_rate`` is a resolved canonical **input**, not a derived quantity."""

    def test_canonical_decimal_representation_is_preserved_exactly(self) -> None:
        # ``0.050`` must stay ``0.050``: the exact operand used for arithmetic never
        # normalises or replaces the retained canonical representation.
        report = self.canonical_report(loss_rate_value="0.050")
        result = compute_requirement_calculation(report)
        calculation = result.calculations[0]
        self.assertEqual(calculation.loss_rate, "0.050")
        self.assertEqual(calculation.to_dict()["loss_rate"], "0.050")
        # The mathematics is still exact: 0.050 = 1/20 and 200 / (1 - 1/20) = 4000/19.
        self.assert_exact(calculation.exact_loss_rate(), Fraction(1, 20))
        self.assert_exact(calculation.base_requirement, Fraction(200, 1))
        self.assert_exact(calculation.gross_requirement, Fraction(4000, 19))

    def test_loss_rate_is_not_serialised_as_a_rational_field(self) -> None:
        report = self.canonical_report(loss_rate_value="0.05")
        calculation = compute_requirement_calculation(report).to_dict()[
            "calculations"
        ][0]
        self.assertIsInstance(calculation["loss_rate"], str)
        self.assertNotIsInstance(calculation["loss_rate"], dict)
        # Derived quantities are the ones expressed as exact rationals.
        self.assertEqual(
            calculation["GrossRequirement"], {"numerator": 4000, "denominator": 19}
        )
        self.assertEqual(
            calculation["BaseRequirement"], {"numerator": 200, "denominator": 1}
        )

    def test_no_new_loss_rate_field_or_field_renaming(self) -> None:
        report = self.canonical_report()
        payload = compute_requirement_calculation(report).to_dict()["calculations"][0]
        for forbidden in ("loss_rate_ratio", "loss_rate_fraction", "loss_rate_rational"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, payload)

    def test_zero_loss_rate_stays_a_valid_explicit_zero(self) -> None:
        report = self.canonical_report(loss_rate_value="0")
        calculation = compute_requirement_calculation(report).calculations[0]
        self.assertEqual(calculation.loss_rate, "0")
        self.assert_exact(calculation.exact_loss_rate(), Fraction(0, 1))
        self.assert_exact(calculation.gross_requirement, Fraction(200, 1))

    def test_missing_loss_rate_is_never_a_rational_default(self) -> None:
        report = self.canonical_report(include_loss_rate_context=False)
        calculation = compute_requirement_calculation(report).calculations[0]
        self.assertEqual(calculation.outcome, OUTCOME_DATA_INCOMPLETE)
        self.assertIsNone(calculation.loss_rate)
        self.assertIsNone(calculation.exact_loss_rate())
        self.assertIsNone(calculation.to_dict()["loss_rate"])


class ContextSourceTests(RequirementCalculationTestCase):
    def test_calculation_context_comes_from_the_parent_requirement(self) -> None:
        report = self.canonical_report(component_local_plant_and_date=False)
        result = compute_requirement_calculation(report)
        self.assertEqual(len(result.calculations), 1)
        calculation = result.calculations[0]
        self.assertIsNone(calculation.outcome)
        self.assertEqual(calculation.plant_id, PLANT)
        self.assertEqual(calculation.required_date, REQUIRED_DATE)
        self.assertEqual(calculation.component_material_code, COMPONENT)
        self.assert_exact(calculation.base_requirement, Fraction(200, 1))
        self.assert_exact(calculation.gross_requirement, Fraction(200, 1))
        component = report.objects_for("BOM Component")[0]
        self.assertFalse(
            any(
                prop.name in ("plant_id", "required_date")
                for prop in component.properties
            )
        )

    def test_rule_does_not_read_bom_local_plant_or_date(self) -> None:
        without_local = compute_requirement_calculation(
            self.canonical_report(component_local_plant_and_date=False)
        )
        with_local = compute_requirement_calculation(
            self.canonical_report(component_local_plant_and_date=True)
        )
        self.assertEqual(
            without_local.calculations[0].to_dict(),
            with_local.calculations[0].to_dict(),
        )

    def test_unresolved_parent_produces_data_incomplete(self) -> None:
        report = self.canonical_report(include_parent=False)
        result = compute_requirement_calculation(report)
        self.assertEqual(len(result.calculations), 1)
        calculation = result.calculations[0]
        self.assertEqual(calculation.outcome, OUTCOME_DATA_INCOMPLETE)
        self.assertIsNone(calculation.gross_requirement)
        self.assertIsNone(calculation.base_requirement)
        self.assertIsNone(calculation.plant_id)
        self.assertIsNone(calculation.required_date)
        self.assertEqual(calculation.component_material_code, COMPONENT)


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
                    self.loss_rate_handoff(accepted, value="0", plant=PLANT, ordinal=0),
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
        self.assert_exact(plant_a[0].gross_requirement, Fraction(100, 1))
        self.assert_exact(plant_b[0].gross_requirement, Fraction(50, 1))
        self.assert_exact(plant_a[0].cumulative_gross_requirement, Fraction(100, 1))
        self.assert_exact(plant_b[0].cumulative_gross_requirement, Fraction(50, 1))

    def test_same_component_under_different_contexts_does_not_cross_reuse(self) -> None:
        construction = self.two_date_construction(
            name="cross-context",
            quantities=("100", "100"),
            loss_rates=("0", "0.5"),
        )
        result = compute_requirement_calculation(construction)
        first = result.for_grain(PLANT, COMPONENT, "2026-10-10")
        second = result.for_grain(PLANT, COMPONENT, "2026-10-15")
        assert first is not None and second is not None
        self.assertEqual(first.loss_rate, '0')
        self.assertEqual(second.loss_rate, '0.5')
        self.assert_exact(first.exact_loss_rate(), Fraction(0, 1))
        self.assert_exact(second.exact_loss_rate(), Fraction(1, 2))
        self.assert_exact(first.gross_requirement, Fraction(200, 1))
        self.assert_exact(second.gross_requirement, Fraction(400, 1))
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
        m2 = result.for_grain(PLANT, COMPONENT, REQUIRED_DATE)
        m3 = result.for_grain(PLANT, COMPONENT_B, REQUIRED_DATE)
        assert m2 is not None and m3 is not None
        self.assert_exact(m2.base_requirement, Fraction(200, 1))
        self.assertEqual(m2.loss_rate, '0.02')
        self.assert_exact(m2.exact_loss_rate(), Fraction(1, 50))
        self.assert_exact(m3.base_requirement, Fraction(400, 1))
        self.assertEqual(m3.loss_rate, '0.06')
        self.assert_exact(m3.exact_loss_rate(), Fraction(3, 50))
        self.assert_exact(
            m2.gross_requirement, gross_requirement(Fraction(200), Fraction(1, 50))
        )
        self.assert_exact(
            m3.gross_requirement, gross_requirement(Fraction(400), Fraction(3, 50))
        )
        self.assertNotEqual(
            m2.gross_requirement,
            gross_requirement(Fraction(200), Fraction(3, 50)),
        )

    def test_calculation_order_is_deterministic(self) -> None:
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
        report = self.canonical_report(bom_component_qty=OMIT)
        result = compute_requirement_calculation(report)
        self.assertEqual(len(result.calculations), 1)
        self.assertEqual(result.calculations[0].outcome, OUTCOME_DATA_INCOMPLETE)
        self.assertIsNone(result.calculations[0].gross_requirement)

    def test_missing_production_qty_is_data_incomplete(self) -> None:
        report = self.canonical_report(production_qty=OMIT)
        result = compute_requirement_calculation(report)
        self.assertEqual(len(result.calculations), 1)
        self.assertEqual(result.calculations[0].outcome, OUTCOME_DATA_INCOMPLETE)

    def test_negative_quantities_are_data_incomplete(self) -> None:
        cases = {
            "negative-production": {"production_qty": "-1"},
            "negative-bom": {"bom_component_qty": "-2"},
        }
        for label, overrides in cases.items():
            with self.subTest(case=label):
                report = self.canonical_report(**overrides)
                result = compute_requirement_calculation(report)
                self.assertEqual(
                    result.calculations[0].outcome, OUTCOME_DATA_INCOMPLETE
                )
                self.assertIsNone(result.calculations[0].gross_requirement)

    def test_unresolved_component_identity_is_data_incomplete(self) -> None:
        _, accepted = self.accepted(
            [
                ("Production Requirement", [self.requirement_record()]),
                ("BOM Component", [self.bom_record(material=OMIT, loss_rate="0")]),
            ],
            name="unresolved-component",
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
        self.assertEqual(calculation.outcome, OUTCOME_DATA_INCOMPLETE)
        self.assertIsNone(calculation.component_material_code)
        self.assertIsNone(calculation.gross_requirement)
        self.assertIsNone(calculation.base_requirement)
        self.assertIsNotNone(calculation.bom_component_reference)
        self.assertTrue(calculation.inherited_issues)

    def test_missing_loss_rate_context_is_data_incomplete(self) -> None:
        report = self.canonical_report(include_loss_rate_context=False)
        result = compute_requirement_calculation(report)
        self.assertEqual(len(result.calculations), 1)
        calculation = result.calculations[0]
        self.assertEqual(calculation.outcome, OUTCOME_DATA_INCOMPLETE)
        self.assertIsNone(calculation.gross_requirement)

    def test_data_incomplete_never_carries_a_numeric_gross_requirement(self) -> None:
        report = self.canonical_report(loss_rate_value="1.0")
        result = compute_requirement_calculation(report)
        calculation = result.to_dict()["calculations"][0]
        self.assertEqual(calculation["outcome"], OUTCOME_DATA_INCOMPLETE)
        self.assertIsNone(calculation["GrossRequirement"])
        self.assertIsNone(calculation["BaseRequirement"])
        self.assertIsNone(calculation["CumulativeGrossRequirement"])
        self.assertFalse(result.calculations[0].has_numeric_result)


class OutputAndBoundaryTests(RequirementCalculationTestCase):
    def test_result_exposes_the_minimum_required_fields(self) -> None:
        construction = self.single_component_construction(
            name="minimum-output", loss_rate="0.05"
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
        # Lossless rational serialisation, never a truncated decimal expansion.
        self.assertEqual(
            calculation["GrossRequirement"], {"numerator": 4000, "denominator": 19}
        )
        self.assertEqual(
            calculation["BaseRequirement"], {"numerator": 200, "denominator": 1}
        )
        # The canonical input keeps its exact decimal representation, not a rational field.
        self.assertEqual(calculation["loss_rate"], "0.05")
        trace = calculation["trace"]
        self.assertIn("production_requirement_reference", trace)
        self.assertIn("bom_component_reference", trace)
        self.assertIn("loss_rate_context_grain", trace)

    def test_rule_consumes_only_resolved_canonical_output(self) -> None:
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
        construction = self.single_component_construction(
            name="deterministic", loss_rate="0.05"
        )
        first = compute_requirement_calculation(construction).to_dict()
        second = compute_requirement_calculation(construction).to_dict()
        self.assertEqual(first, second)

    def test_no_new_validation_taxonomy_is_used(self) -> None:
        allowed = {
            "FIELD_VALUE",
            "IDENTITY_RESOLUTION",
            "SEMANTIC_RESOLUTION",
            "CONSISTENCY",
            "PROVENANCE",
            "BUSINESS_DATA",
            "PACKAGE_STRUCTURE",
        }
        report = self.canonical_report(include_loss_rate_context=False)
        before = report.to_dict()
        result = compute_requirement_calculation(report)
        for calculation in result.calculations:
            for issue in calculation.inherited_issues:
                self.assertIn(issue.category, allowed)
        # The construction report itself is not mutated by the rule.
        self.assertEqual(before, report.to_dict())

    def test_no_success_status_vocabulary_is_surfaced(self) -> None:
        report = self.canonical_report()
        calculation = compute_requirement_calculation(report).to_dict()[
            "calculations"
        ][0]
        self.assertIsNone(calculation["outcome"])
        for forbidden in ("NUMERIC", "OK", "SUCCESS", "COMPLETE", "READY"):
            with self.subTest(forbidden=forbidden):
                self.assertNotEqual(calculation["outcome"], forbidden)


if __name__ == "__main__":
    unittest.main()
