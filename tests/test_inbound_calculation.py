"""``BR-INBOUND-001`` Effective Inbound tests (POC Design v0.2 §2.6).

Coverage mirrors the registered acceptance examples and the rule's fail-safe boundary:

* A -- eligible ``OPEN`` PO contributes its remaining quantity;
* B -- arrival after the required date contributes 0 (not a data-quality issue) and the same
  inbound can participate at a later required date;
* C -- ``PARTIALLY_RECEIVED`` contributes only ``ordered_qty - received_qty``;
* D -- ``CANCELLED`` / ``CLOSED`` / ``COMPLETED`` are valid but ineligible and contribute 0;
* E -- missing ``effective_arrival_date`` -> ``DATA_INCOMPLETE`` with no default date;
* F -- ``received_qty > ordered_qty`` -> ``DATA_INCOMPLETE`` without clamp / negative remaining;
* G -- cumulative inbound per registered grain;
* H / I -- separate plants / materials never aggregate;
* J -- two content-identical inbound records at distinct ordinals both contribute;
* K / L / M -- unknown status, negative ``ordered_qty``, negative ``received_qty``;
* N -- ``RemainingInboundQty = 0`` is valid and contributes 0;
* O -- deterministic repeatability / ordering;
* P -- upstream provenance and G3-A record reference retained;
* Q -- the requirement result supplies the target ``required_date`` context.

All fixtures are SIMULATED.
"""

from __future__ import annotations

import unittest
import uuid
from pathlib import Path
from typing import Any

from snapshot_loader import (
    BomParentContextHandoff,
    EFFECTIVE_INBOUND_DATA_INCOMPLETE,
    ExactQuantity,
    HandoffEvidence,
    INBOUND_RULE_ID,
    LossRateHandoff,
    PhaseAHandoff,
    TrustedInputBoundary,
    compute_effective_inbound,
    compute_requirement_calculation,
    construct_canonical_objects,
    load_package,
    parse_exact_quantity,
    parse_non_negative_quantity,
    remaining_inbound_qty,
)
from tests.helpers import DatasetSpec, PackageSpec, build_package

SCRATCH_ROOT = Path(__file__).resolve().parents[1] / "build" / "test-scratch"

PLANT = "P1"
PLANT_B = "P2"
PARENT = "M1"
COMPONENT = "M2"
COMPONENT_B = "M3"
REQUIRED_DATE = "2026-10-15"
BASIS_LOSS_RATE = "SIMULATED-APPROVED-LOSS-RATE-MAPPING"
EVIDENCE_BOM = "SIMULATED-SRC-BOM-1"
EVIDENCE_REQUIREMENT = "SIMULATED-SRC-REQ-1"


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


class EffectiveInboundTestCase(unittest.TestCase):
    """Shared scaffolding: a real package, Phase A construction and the rule result."""

    def setUp(self) -> None:
        self.boundary = SCRATCH_ROOT / f"inbound-{uuid.uuid4().hex}"
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
        self, accepted, *, role: str, artifact: str, ordinal: int = 0, locator=None
    ) -> HandoffEvidence:
        return HandoffEvidence(
            snapshot_package_identity=accepted.package_id,
            logical_dataset_role=role,
            artifact=artifact,
            record_ordinal=ordinal,
            evidence_locator=locator,
        )

    # --- record builders -----------------------------------------------------------

    def requirement_record(
        self,
        *,
        plant: str = PLANT,
        material: str = PARENT,
        required_date: str = REQUIRED_DATE,
        production_qty: Any = "10",
    ) -> dict[str, Any]:
        return with_provenance(
            {
                "plant_id": plant,
                "material_code": material,
                "required_date": required_date,
                "ProductionQty": production_qty,
            },
            [("ProductionQty", [EVIDENCE_REQUIREMENT], None)],
        )

    def bom_record(
        self,
        *,
        plant: str = PLANT,
        material: Any = COMPONENT,
        required_date: str = REQUIRED_DATE,
        bom_component_qty: Any = "1",
        loss_rate: Any = "0",
    ) -> dict[str, Any]:
        record: dict[str, Any] = {
            "plant_id": plant,
            "required_date": required_date,
            "material_code": material,
            "BOMComponentQty": bom_component_qty,
            "loss_rate": loss_rate,
        }
        return with_provenance(
            record,
            [
                ("BOMComponentQty", [EVIDENCE_BOM], None),
                ("loss_rate", ["SIMULATED-SRC-LOSS"], BASIS_LOSS_RATE),
            ],
        )

    def inbound_record(
        self,
        *,
        plant: Any = PLANT,
        material: Any = COMPONENT,
        ordered_qty: Any = "100",
        received_qty: Any = "0",
        arrival: Any = "2026-10-12",
        status: Any = "OPEN",
    ) -> dict[str, Any]:
        record: dict[str, Any] = {}
        if plant is not OMIT:
            record["plant_id"] = plant
        if material is not OMIT:
            record["material_code"] = material
        if ordered_qty is not OMIT:
            record["ordered_qty"] = ordered_qty
        if received_qty is not OMIT:
            record["received_qty"] = received_qty
        if arrival is not OMIT:
            record["effective_arrival_date"] = arrival
        if status is not OMIT:
            record["inbound_status"] = status
        return record

    # --- construction helpers ------------------------------------------------------

    def build(
        self,
        *,
        name: str,
        inbounds: list[dict[str, Any]],
        requirements: list[dict[str, Any]] | None = None,
        bom_components: list[dict[str, Any]] | None = None,
        inbound_artifact: str = "2.json",
    ):
        requirements = requirements if requirements is not None else [self.requirement_record()]
        bom_components = (
            bom_components if bom_components is not None else [self.bom_record()]
        )
        _, accepted = self.accepted(
            [
                ("Production Requirement", requirements),
                ("BOM Component", bom_components),
                ("Inbound Supply", inbounds),
            ],
            name=name,
        )
        bom_bindings = tuple(
            BomParentContextHandoff(
                bom_evidence=self.citation(
                    accepted, role="BOM Component", artifact="1.json", ordinal=index
                ),
                parent_evidence=self.citation(
                    accepted,
                    role="Production Requirement",
                    artifact="0.json",
                    ordinal=min(index, len(requirements) - 1),
                ),
            )
            for index in range(len(bom_components))
        )
        loss_rates = tuple(
            LossRateHandoff(
                plant_id=component.get("plant_id", PLANT),
                parent_material_code=requirements[min(index, len(requirements) - 1)].get(
                    "material_code", PARENT
                ),
                required_date=component.get("required_date", REQUIRED_DATE),
                evidence=self.citation(
                    accepted,
                    role="BOM Component",
                    artifact="1.json",
                    ordinal=index,
                ),
                component_material_code=component.get("material_code", COMPONENT),
                loss_rate_evidence=(
                    self.citation(
                        accepted,
                        role="BOM Component",
                        artifact="1.json",
                        ordinal=index,
                        locator="SIMULATED-SRC-LOSS",
                    ),
                ),
                loss_rate=component.get("loss_rate", "0"),
                resolution_basis=BASIS_LOSS_RATE,
            )
            for index, component in enumerate(bom_components)
        )
        construction = construct_canonical_objects(
            accepted,
            PhaseAHandoff(
                analysis_run_id="RUN-1",
                analysis_date="2026-10-01",
                bom_parent_context=bom_bindings,
                loss_rate=loss_rates,
            ),
        )
        requirements_result = compute_requirement_calculation(construction)
        return construction, compute_effective_inbound(construction, requirements_result)

    def evaluate(
        self,
        *,
        name: str,
        inbound: dict[str, Any],
        required_date: str = REQUIRED_DATE,
        material: Any = COMPONENT,
        plant: str = PLANT,
    ):
        construction, result = self.build(
            name=name,
            inbounds=[inbound],
            requirements=[self.requirement_record(required_date=required_date)],
            bom_components=[
                self.bom_record(
                    plant=plant, material=material, required_date=required_date
                )
            ],
        )
        target = result.for_grain(plant, material, required_date)
        self.assertIsNotNone(target)
        return construction, result, target

    # --- assertions ----------------------------------------------------------------

    def assert_qty(self, value: ExactQuantity | None, expected: str) -> None:
        """Assert the exact canonical decimal text -- never a rounded / parsed value."""

        self.assertIsNotNone(value)
        assert value is not None
        self.assertIsInstance(value, ExactQuantity)
        self.assertEqual(value.text(), expected)


class ArithmeticTests(EffectiveInboundTestCase):
    def test_remaining_inbound_qty_is_the_exact_difference(self) -> None:
        self.assert_qty(
            remaining_inbound_qty(
                parse_exact_quantity("100"), parse_exact_quantity("40")
            ),
            "60",
        )
        self.assert_qty(
            remaining_inbound_qty(
                parse_exact_quantity("100"), parse_exact_quantity("100")
            ),
            "0",
        )

    def test_no_binary_float_is_used(self) -> None:
        value = remaining_inbound_qty(
            parse_exact_quantity("0.3"), parse_exact_quantity("0.1")
        )
        self.assertIsInstance(value, ExactQuantity)
        self.assertEqual(value.text(), "0.2")

    def test_subtraction_is_exact_beyond_the_decimal_default_precision(self) -> None:
        """Regression: the Decimal default context silently rounds at 28 digits.

        ``Decimal("123456789012345678901234567890") - Decimal("1")`` is silently rounded to
        ``123456789012345678901234567000`` at the default precision, which would invent a
        business quantity.  The rule must produce the exact difference.
        """

        value = remaining_inbound_qty(
            parse_exact_quantity("123456789012345678901234567890"),
            parse_exact_quantity("1"),
        )
        self.assertEqual(value.text(), "123456789012345678901234567889")

    def test_cumulative_supply_is_exact_beyond_the_decimal_default_precision(self) -> None:
        """Regression: cumulative supply must be the exact sum, never a rounded one."""

        first = parse_exact_quantity("123456789012345678901234567889")
        second = parse_exact_quantity("100000000000000000000000000001")
        assert first is not None and second is not None
        self.assertEqual(
            (first + second).text(), "223456789012345678901234567890"
        )

    def test_canonical_quantity_text_is_lossless_and_keeps_the_stated_scale(self) -> None:
        """No rounding / quantization / truncation / scale normalisation is applied."""

        self.assertEqual(parse_exact_quantity("0.10").text(), "0.10")
        self.assertEqual(parse_exact_quantity("100").text(), "100")
        self.assertEqual(parse_exact_quantity("0.500").text(), "0.500")
        self.assertEqual(parse_exact_quantity("-0.50").text(), "-0.50")
        self.assertEqual(
            parse_exact_quantity("0.000000000000000000000000000001").text(),
            "0.000000000000000000000000000001",
        )

    def test_quantity_text_is_a_lossless_value_rendering_not_a_lexical_transcript(
        self,
    ) -> None:
        """The exact value and scale survive, but this is not character-for-character.

        The registered canonical grammar admits forms whose lexical spelling is not part of
        the quantity itself (``"+"`` sign, leading zeros); the rendered text is the exact
        value, not a copy of the source characters.
        """

        self.assertEqual(parse_exact_quantity("+5.00").text(), "5.00")
        self.assertEqual(parse_exact_quantity("001.20").text(), "1.20")
        self.assertEqual(
            parse_exact_quantity("+5.00"), parse_exact_quantity("5.00")
        )
        self.assertEqual(
            parse_exact_quantity("001.20"), parse_exact_quantity("1.20")
        )

    def test_equal_quantities_at_different_scales_compare_and_hash_equally(self) -> None:
        self.assertEqual(parse_exact_quantity("5"), parse_exact_quantity("5.00"))
        self.assertEqual(
            hash(parse_exact_quantity("5")), hash(parse_exact_quantity("5.00"))
        )
        self.assertEqual(
            len({parse_exact_quantity("5"), parse_exact_quantity("5.00")}), 1
        )
        self.assertNotEqual(parse_exact_quantity("5"), parse_exact_quantity("5.01"))

    def test_non_canonical_quantities_are_never_repaired(self) -> None:
        for raw in (None, "", "1e5", "1E+5", " 1", "1 ", "abc", "1,5", [], 1):
            with self.subTest(raw=raw):
                self.assertIsNone(parse_exact_quantity(raw))
        # A sign is canonical syntax, but a negative value is not a registered
        # NON_NEGATIVE_QUANTITY, so the rule-level parse refuses it.
        self.assertIsNotNone(parse_exact_quantity("-1"))
        self.assertIsNone(parse_non_negative_quantity("-1"))
        self.assertIsNone(parse_non_negative_quantity("-0.5"))


class AcceptanceExampleTests(EffectiveInboundTestCase):
    def test_example_a_eligible_open_po(self) -> None:
        _construction, _result, target = self.evaluate(
            name="example-a",
            inbound=self.inbound_record(status="OPEN", arrival="2026-10-12"),
        )
        evaluation = target.evaluations[0]
        self.assertIsNone(evaluation.outcome)
        self.assertIsNone(target.outcome)
        self.assert_qty(evaluation.remaining_inbound_qty, "100")
        self.assert_qty(evaluation.effective_inbound_qty, "100")
        self.assert_qty(target.cumulative_effective_inbound, "100")
        self.assertTrue(evaluation.status_eligible)
        self.assertTrue(evaluation.contributes)

    def test_example_b_arrival_after_requirement_is_zero_not_incomplete(self) -> None:
        _construction, result = self.build(
            name="example-b",
            inbounds=[self.inbound_record(status="CONFIRMED", arrival="2026-10-20")],
            requirements=[
                self.requirement_record(required_date="2026-10-15"),
                self.requirement_record(required_date="2026-10-20"),
            ],
            bom_components=[
                self.bom_record(required_date="2026-10-15"),
                self.bom_record(required_date="2026-10-20"),
            ],
        )
        early = result.for_grain(PLANT, COMPONENT, "2026-10-15")
        later = result.for_grain(PLANT, COMPONENT, "2026-10-20")
        assert early is not None and later is not None
        self.assertIsNone(early.outcome)
        self.assert_qty(early.evaluations[0].effective_inbound_qty, "0")
        self.assert_qty(early.cumulative_effective_inbound, "0")
        self.assertFalse(early.evaluations[0].data_incomplete)
        # The very same inbound participates at the later required date.
        self.assertIsNone(later.outcome)
        self.assert_qty(later.evaluations[0].effective_inbound_qty, "100")
        self.assert_qty(later.cumulative_effective_inbound, "100")

    def test_example_c_partially_received_contributes_only_remaining(self) -> None:
        _construction, _result, target = self.evaluate(
            name="example-c",
            inbound=self.inbound_record(
                status="PARTIALLY_RECEIVED",
                ordered_qty="100",
                received_qty="40",
                arrival="2026-10-12",
            ),
        )
        evaluation = target.evaluations[0]
        self.assert_qty(evaluation.remaining_inbound_qty, "60")
        self.assert_qty(evaluation.effective_inbound_qty, "60")
        self.assert_qty(target.cumulative_effective_inbound, "60")
        self.assertNotEqual(
            evaluation.effective_inbound_qty, parse_exact_quantity("100")
        )

    def test_example_d_ineligible_statuses_contribute_zero(self) -> None:
        for status in ("CANCELLED", "CLOSED", "COMPLETED"):
            with self.subTest(status=status):
                _construction, _result, target = self.evaluate(
                    name=f"example-d-{status.lower()}",
                    inbound=self.inbound_record(status=status, arrival="2026-10-12"),
                )
                evaluation = target.evaluations[0]
                self.assertIsNone(evaluation.outcome)
                self.assertIsNone(target.outcome)
                self.assertFalse(evaluation.status_eligible)
                self.assert_qty(evaluation.effective_inbound_qty, "0")
                self.assert_qty(target.cumulative_effective_inbound, "0")

    def test_example_e_missing_arrival_date_is_data_incomplete(self) -> None:
        _construction, _result, target = self.evaluate(
            name="example-e",
            inbound=self.inbound_record(arrival=OMIT),
        )
        evaluation = target.evaluations[0]
        self.assertEqual(evaluation.outcome, EFFECTIVE_INBOUND_DATA_INCOMPLETE)
        self.assertIsNone(evaluation.effective_inbound_qty)
        self.assertEqual(target.outcome, EFFECTIVE_INBOUND_DATA_INCOMPLETE)
        self.assertIsNone(target.cumulative_effective_inbound)

    def test_example_f_received_greater_than_ordered_is_data_incomplete(self) -> None:
        _construction, _result, target = self.evaluate(
            name="example-f",
            inbound=self.inbound_record(ordered_qty="100", received_qty="120"),
        )
        evaluation = target.evaluations[0]
        self.assertEqual(evaluation.outcome, EFFECTIVE_INBOUND_DATA_INCOMPLETE)
        # No clamped / negative / guessed remaining quantity is produced.
        self.assertIsNone(evaluation.remaining_inbound_qty)
        self.assertIsNone(evaluation.effective_inbound_qty)
        self.assertIsNone(target.cumulative_effective_inbound)

    def test_example_g_cumulative_inbound(self) -> None:
        _construction, result = self.build(
            name="example-g",
            inbounds=[
                self.inbound_record(ordered_qty="50", arrival="2026-10-08"),
                self.inbound_record(ordered_qty="80", arrival="2026-10-15"),
            ],
            requirements=[
                self.requirement_record(required_date="2026-10-10"),
                self.requirement_record(required_date="2026-10-20"),
            ],
            bom_components=[
                self.bom_record(required_date="2026-10-10"),
                self.bom_record(required_date="2026-10-20"),
            ],
        )
        first = result.for_grain(PLANT, COMPONENT, "2026-10-10")
        second = result.for_grain(PLANT, COMPONENT, "2026-10-20")
        assert first is not None and second is not None
        self.assert_qty(first.cumulative_effective_inbound, "50")
        self.assert_qty(second.cumulative_effective_inbound, "130")


class GrainAndIsolationTests(EffectiveInboundTestCase):
    def test_h_separate_plants_never_aggregate(self) -> None:
        _construction, result = self.build(
            name="separate-plants",
            inbounds=[
                self.inbound_record(plant=PLANT, material=COMPONENT, ordered_qty="50"),
                self.inbound_record(plant=PLANT_B, material=COMPONENT, ordered_qty="80"),
            ],
            requirements=[
                self.requirement_record(plant=PLANT),
                self.requirement_record(plant=PLANT_B),
            ],
            bom_components=[
                self.bom_record(plant=PLANT),
                self.bom_record(plant=PLANT_B),
            ],
        )
        plant_a = result.for_grain(PLANT, COMPONENT, REQUIRED_DATE)
        plant_b = result.for_grain(PLANT_B, COMPONENT, REQUIRED_DATE)
        assert plant_a is not None and plant_b is not None
        self.assert_qty(plant_a.cumulative_effective_inbound, "50")
        self.assert_qty(plant_b.cumulative_effective_inbound, "80")

    def test_i_separate_materials_never_aggregate(self) -> None:
        _construction, result = self.build(
            name="separate-materials",
            inbounds=[
                self.inbound_record(material=COMPONENT, ordered_qty="50"),
                self.inbound_record(material=COMPONENT_B, ordered_qty="80"),
            ],
            bom_components=[
                self.bom_record(material=COMPONENT),
                self.bom_record(material=COMPONENT_B),
            ],
        )
        m2 = result.for_grain(PLANT, COMPONENT, REQUIRED_DATE)
        m3 = result.for_grain(PLANT, COMPONENT_B, REQUIRED_DATE)
        assert m2 is not None and m3 is not None
        self.assert_qty(m2.cumulative_effective_inbound, "50")
        self.assert_qty(m3.cumulative_effective_inbound, "80")
        # No cross-material reuse: M2's inbound does not feed M3.
        m2_evaluation = m2.evaluations[1]
        self.assert_qty(m2_evaluation.effective_inbound_qty, "0")
        self.assertIsNone(m2_evaluation.outcome)

    def test_j_content_identical_inbounds_at_distinct_ordinals_both_contribute(self) -> None:
        duplicate = self.inbound_record(ordered_qty="40")
        _construction, _result, target = self.evaluate(
            name="identical-inbounds",
            inbound=duplicate,
        )
        construction, result = self.build(
            name="identical-inbounds-pair",
            inbounds=[dict(duplicate), dict(duplicate)],
        )
        target = result.for_grain(PLANT, COMPONENT, REQUIRED_DATE)
        assert target is not None
        self.assertEqual(len(target.evaluations), 2)
        self.assertEqual(
            len({item.inbound_reference for item in target.evaluations}), 2
        )
        for evaluation in target.evaluations:
            self.assert_qty(evaluation.effective_inbound_qty, "40")
        # Both distinct supply evidence records contribute: 40 + 40, no deduplication.
        self.assert_qty(target.cumulative_effective_inbound, "80")


class FailSafeTests(EffectiveInboundTestCase):
    def test_k_unknown_status_is_data_incomplete(self) -> None:
        _construction, _result, target = self.evaluate(
            name="unknown-status",
            inbound=self.inbound_record(status="SOMETHING_ELSE"),
        )
        evaluation = target.evaluations[0]
        self.assertEqual(evaluation.outcome, EFFECTIVE_INBOUND_DATA_INCOMPLETE)
        self.assertIsNone(evaluation.effective_inbound_qty)
        self.assertIsNone(target.cumulative_effective_inbound)

    def test_l_negative_ordered_qty_is_data_incomplete(self) -> None:
        _construction, _result, target = self.evaluate(
            name="negative-ordered",
            inbound=self.inbound_record(ordered_qty="-1"),
        )
        self.assertEqual(
            target.evaluations[0].outcome, EFFECTIVE_INBOUND_DATA_INCOMPLETE
        )
        self.assertIsNone(target.cumulative_effective_inbound)

    def test_m_negative_received_qty_is_data_incomplete(self) -> None:
        _construction, _result, target = self.evaluate(
            name="negative-received",
            inbound=self.inbound_record(received_qty="-5"),
        )
        self.assertEqual(
            target.evaluations[0].outcome, EFFECTIVE_INBOUND_DATA_INCOMPLETE
        )
        self.assertIsNone(target.cumulative_effective_inbound)

    def test_missing_ordered_qty_is_data_incomplete(self) -> None:
        _construction, _result, target = self.evaluate(
            name="missing-ordered",
            inbound=self.inbound_record(ordered_qty=OMIT),
        )
        self.assertEqual(
            target.evaluations[0].outcome, EFFECTIVE_INBOUND_DATA_INCOMPLETE
        )

    def test_missing_status_is_data_incomplete(self) -> None:
        _construction, _result, target = self.evaluate(
            name="missing-status",
            inbound=self.inbound_record(status=OMIT),
        )
        self.assertEqual(
            target.evaluations[0].outcome, EFFECTIVE_INBOUND_DATA_INCOMPLETE
        )

    def test_invalid_arrival_date_is_data_incomplete(self) -> None:
        _construction, _result, target = self.evaluate(
            name="invalid-arrival",
            inbound=self.inbound_record(arrival="2026-02-30"),
        )
        self.assertEqual(
            target.evaluations[0].outcome, EFFECTIVE_INBOUND_DATA_INCOMPLETE
        )

    def test_n_zero_remaining_is_valid_and_contributes_zero(self) -> None:
        _construction, _result, target = self.evaluate(
            name="zero-remaining",
            inbound=self.inbound_record(ordered_qty="100", received_qty="100"),
        )
        evaluation = target.evaluations[0]
        self.assertIsNone(evaluation.outcome)
        self.assert_qty(evaluation.remaining_inbound_qty, "0")
        self.assert_qty(evaluation.effective_inbound_qty, "0")
        self.assert_qty(target.cumulative_effective_inbound, "0")

    def test_unresolved_requirement_context_makes_the_target_data_incomplete(self) -> None:
        construction, result = self.build(
            name="unresolved-requirement",
            inbounds=[self.inbound_record(ordered_qty="50")],
            requirements=[self.requirement_record(production_qty="not-a-decimal")],
        )
        target = result.for_grain(PLANT, COMPONENT, REQUIRED_DATE)
        assert target is not None
        self.assertEqual(target.outcome, EFFECTIVE_INBOUND_DATA_INCOMPLETE)
        self.assertIsNone(target.cumulative_effective_inbound)
        self.assertTrue(target.notes)

    def test_no_new_validation_taxonomy_is_used(self) -> None:
        allowed = {
            "PACKAGE_STRUCTURE",
            "FIELD_VALUE",
            "IDENTITY_RESOLUTION",
            "SEMANTIC_RESOLUTION",
            "CONSISTENCY",
            "PROVENANCE",
            "BUSINESS_DATA",
        }
        _construction, _result, target = self.evaluate(
            name="taxonomy",
            inbound=self.inbound_record(arrival=OMIT),
        )
        for evaluation in target.evaluations:
            for issue in evaluation.issues:
                self.assertIn(issue.category, allowed)
        self.assertNotIn(INBOUND_RULE_ID, allowed)


class OutputAndBoundaryTests(EffectiveInboundTestCase):
    def test_o_deterministic_repeatability_and_ordering(self) -> None:
        construction, result = self.build(
            name="determinism",
            inbounds=[
                self.inbound_record(ordered_qty="50", arrival="2026-10-08"),
                self.inbound_record(ordered_qty="80", arrival="2026-10-15"),
            ],
        )
        requirements = compute_requirement_calculation(construction)
        first = compute_effective_inbound(construction, requirements).to_dict()
        second = compute_effective_inbound(construction, requirements).to_dict()
        self.assertEqual(first, second)
        self.assertEqual(
            [item.required_date for item in result.targets],
            sorted(item.required_date for item in result.targets),
        )
        self.assertEqual(
            [item.inbound_reference for item in result.targets[0].evaluations],
            sorted(
                item.inbound_reference for item in result.targets[0].evaluations
            ),
        )

    def test_p_provenance_and_g3a_reference_are_retained(self) -> None:
        _construction, _result, target = self.evaluate(
            name="provenance",
            inbound=self.inbound_record(),
        )
        evaluation = target.evaluations[0]
        self.assertTrue(evaluation.inbound_reference.startswith("SIMULATED-PKG-0001|Inbound Supply|"))
        self.assertIsNotNone(evaluation.provenance)
        assert evaluation.provenance is not None
        self.assertEqual(
            evaluation.provenance.logical_dataset_role, "Inbound Supply"
        )
        self.assertEqual(evaluation.provenance.snapshot_package_identity, "SIMULATED-PKG-0001")
        self.assertEqual(evaluation.inbound_role, "Inbound Supply")

    def test_q_target_context_comes_from_the_requirement_result(self) -> None:
        construction, result = self.build(
            name="context-source",
            inbounds=[self.inbound_record(ordered_qty="50")],
        )
        requirements = compute_requirement_calculation(construction)
        inbound_result = compute_effective_inbound(construction, requirements)
        # The target grain mirrors the BR-REQUIREMENT-001 result exactly.
        self.assertEqual(
            sorted(
                (
                    item.plant_id,
                    item.component_material_code,
                    item.required_date,
                )
                for item in requirements.calculations
            ),
            sorted(
                (item.plant_id, item.material_code, item.required_date)
                for item in inbound_result.targets
            ),
        )
        self.assertEqual(inbound_result.to_dict(), result.to_dict())
        # No raw artifact is re-read: the rule is a pure function of the two results.
        self.assertEqual(
            inbound_result.to_dict(),
            compute_effective_inbound(construction, requirements).to_dict(),
        )
        # The requirement result itself is never modified by the inbound rule.
        self.assertEqual(
            requirements.to_dict(),
            compute_requirement_calculation(construction).to_dict(),
        )

    def test_canonical_input_value_and_scale_survive_into_the_output(self) -> None:
        """The exact value and stated fractional scale are serialized losslessly."""

        _construction, result, target = self.evaluate(
            name="representation",
            inbound=self.inbound_record(
                status="PARTIALLY_RECEIVED",
                ordered_qty="100.00",
                received_qty="0.50",
                arrival="2026-10-12",
            ),
        )
        payload = target.evaluations[0].to_dict()
        self.assertEqual(payload["ordered_qty"], "100.00")
        self.assertEqual(payload["received_qty"], "0.50")
        self.assertEqual(payload["RemainingInboundQty"], "99.50")
        self.assertEqual(payload["EffectiveInboundQty"], "99.50")
        self.assert_qty(target.cumulative_effective_inbound, "99.50")

    def test_non_lexical_canonical_forms_keep_their_exact_value(self) -> None:
        """``"+5.00"`` / ``"001.20"`` are consumed exactly; only the value is rendered."""

        _construction, _result, target = self.evaluate(
            name="representation-lexical",
            inbound=self.inbound_record(
                status="PARTIALLY_RECEIVED",
                ordered_qty="001.20",
                received_qty="+0.20",
                arrival="2026-10-12",
            ),
        )
        payload = target.evaluations[0].to_dict()
        self.assertEqual(payload["ordered_qty"], "1.20")
        self.assertEqual(payload["received_qty"], "0.20")
        self.assertEqual(payload["RemainingInboundQty"], "1.00")

    def test_minimum_output_fields(self) -> None:
        _construction, result, target = self.evaluate(
            name="minimum-output",
            inbound=self.inbound_record(),
        )
        payload = result.to_dict()
        self.assertEqual(payload["rule"], INBOUND_RULE_ID)
        target_payload = payload["targets"][0]
        for field in (
            "plant_id",
            "material_code",
            "required_date",
            "CumulativeEffectiveInbound",
            "outcome",
        ):
            with self.subTest(field=field):
                self.assertIn(field, target_payload)
        evaluation = target_payload["evaluations"][0]
        for field in (
            "inbound_reference",
            "ordered_qty",
            "received_qty",
            "RemainingInboundQty",
            "inbound_status",
            "effective_arrival_date",
            "EffectiveInboundQty",
            "outcome",
        ):
            with self.subTest(field=field):
                self.assertIn(field, evaluation)
        self.assertEqual(evaluation["RemainingInboundQty"], "100")
        self.assertEqual(evaluation["EffectiveInboundQty"], "100")

    def test_inbound_is_not_a_po_identity(self) -> None:
        _construction, result, _target = self.evaluate(
            name="no-po-id",
            inbound=self.inbound_record(),
        )
        payload = str(result.to_dict())
        for forbidden in ("purchase_order", "po_id", "PO-"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, payload)


class GroupedRequirementTargetTests(EffectiveInboundTestCase):
    """Regression: a target grain is a **group** of upstream requirement rows.

    ``BR-INBOUND-001`` takes its required-date context from ``BR-REQUIREMENT-001``.  Several
    BOM Component relationships can state the same grain (``plant_id`` + component
    ``material_code`` + ``required_date``): here two different parent materials of the same
    plant demand the same component on the same date, so two ``BR-REQUIREMENT-001`` rows
    exist for one target.  No row may be treated as a representative: if any upstream row of
    the grain is ``DATA_INCOMPLETE`` the target is ``DATA_INCOMPLETE`` and no numeric
    cumulative supply is produced -- whatever the rows' order.
    """

    PARENT_B = "M1B"

    def _two_parent_rows(self, *, unusable_position: int | None):
        """Two upstream rows on one target grain; one may be ``DATA_INCOMPLETE``."""

        requirements = [
            self.requirement_record(
                material=PARENT,
                production_qty=(
                    "not-a-decimal" if unusable_position == 0 else "10"
                ),
            ),
            self.requirement_record(
                material=self.PARENT_B,
                production_qty=(
                    "not-a-decimal" if unusable_position == 1 else "10"
                ),
            ),
        ]
        return self.build(
            name=f"grouped-{unusable_position}",
            inbounds=[self.inbound_record(ordered_qty="50", arrival="2026-10-12")],
            requirements=requirements,
            bom_components=[
                self.bom_record(material=COMPONENT),
                self.bom_record(material=COMPONENT),
            ],
        )

    def test_grouped_rows_are_one_target(self) -> None:
        construction, result = self._two_parent_rows(unusable_position=None)
        upstream = compute_requirement_calculation(construction)
        self.assertEqual(len(upstream.calculations), 2)
        self.assertEqual(
            len(
                {
                    (
                        row.plant_id,
                        row.component_material_code,
                        row.required_date,
                    )
                    for row in upstream.calculations
                }
            ),
            1,
            msg="fixture must state one target grain from two requirement rows",
        )
        self.assertEqual(len(result.targets), 1)
        target = result.targets[0]
        self.assertIsNone(target.outcome)
        self.assert_qty(target.cumulative_effective_inbound, "50")
        # Both upstream rows are retained in the trace: neither is discarded.
        self.assertEqual(len(target.requirement_traces), 2)
        self.assertEqual(
            len(
                {
                    trace.production_requirement_reference
                    for trace in target.requirement_traces
                }
            ),
            2,
        )

    def test_grouped_target_retains_every_upstream_trace_dimension(self) -> None:
        """Each upstream row keeps its real parent, BOM Component and provenance.

        Publishing the ``BOM Component`` reference as a "requirement reference" -- or the
        ``loss_rate`` provenance as the requirement provenance -- would mis-describe the
        evidence for every downstream consumer.
        """

        construction, result = self._two_parent_rows(unusable_position=None)
        target = result.targets[0]
        traces = target.requirement_traces
        self.assertEqual(len(traces), 2)

        parent_references = {
            trace.production_requirement_reference for trace in traces
        }
        component_references = {trace.bom_component_reference for trace in traces}
        self.assertEqual(len(parent_references), 2)
        self.assertEqual(len(component_references), 2)
        # A BOM Component reference is never published as a Production Requirement one.
        self.assertEqual(parent_references & component_references, set())

        for trace in traces:
            assert trace.production_requirement_reference is not None
            assert trace.bom_component_reference is not None
            self.assertIn(
                "|Production Requirement|", trace.production_requirement_reference
            )
            self.assertIn("|BOM Component|", trace.bom_component_reference)
            self.assertTrue(trace.production_requirement_context_reference)

            parent = trace.production_requirement_provenance
            component = trace.bom_component_provenance
            loss_rate = trace.loss_rate_provenance
            assert parent is not None and component is not None and loss_rate is not None
            # Each dimension keeps its own provenance; no dimension masquerades as another.
            self.assertEqual(parent.logical_dataset_role, "Production Requirement")
            self.assertEqual(component.logical_dataset_role, "BOM Component")
            self.assertEqual(
                parent.stable_source_evidence_locators, (EVIDENCE_REQUIREMENT,)
            )
            self.assertIn(EVIDENCE_BOM, component.stable_source_evidence_locators)
            self.assertEqual(
                loss_rate.stable_source_evidence_locators, ("SIMULATED-SRC-LOSS",)
            )
            # The parent evidence is never replaced by the BOM Component evidence.
            self.assertNotEqual(parent, component)
            self.assertNotEqual(parent.logical_dataset_role, component.logical_dataset_role)
            # The retained reference and the retained provenance describe the same record.
            self.assertTrue(
                trace.production_requirement_reference.endswith(
                    parent.record_path.replace("#", "|")
                )
            )
            self.assertTrue(
                trace.bom_component_reference.endswith(
                    component.record_path.replace("#", "|")
                )
            )

        # The traces are exactly the upstream requirement calculation rows, in their order.
        upstream = compute_requirement_calculation(construction)
        self.assertEqual(
            [trace.production_requirement_reference for trace in traces],
            [
                row.production_requirement_reference
                for row in upstream.calculations
            ],
        )

        # The serialized output states the same semantics as the runtime objects.
        payload = target.to_dict()["requirement_traces"]
        self.assertEqual(len(payload), 2)
        self.assertEqual(
            [item["production_requirement_reference"] for item in payload],
            [trace.production_requirement_reference for trace in traces],
        )
        self.assertEqual(
            [item["bom_component_reference"] for item in payload],
            [trace.bom_component_reference for trace in traces],
        )
        self.assertEqual(
            [
                item["production_requirement_context_reference"]
                for item in payload
            ],
            [trace.production_requirement_context_reference for trace in traces],
        )
        for item, trace in zip(payload, traces):
            self.assertNotEqual(
                item["production_requirement_reference"],
                item["bom_component_reference"],
            )
            assert trace.production_requirement_provenance is not None
            assert trace.bom_component_provenance is not None
            assert trace.loss_rate_provenance is not None
            self.assertEqual(
                item["production_requirement_provenance"]["accepted_record_path"],
                trace.production_requirement_provenance.record_path,
            )
            self.assertEqual(
                item["bom_component_provenance"]["accepted_record_path"],
                trace.bom_component_provenance.record_path,
            )
            self.assertEqual(
                item["loss_rate_provenance"]["accepted_record_path"],
                trace.loss_rate_provenance.record_path,
            )

    def test_data_incomplete_row_first_makes_the_target_data_incomplete(self) -> None:
        _construction, result = self._two_parent_rows(unusable_position=0)
        self.assertEqual(len(result.targets), 1)
        target = result.targets[0]
        self.assertEqual(target.outcome, EFFECTIVE_INBOUND_DATA_INCOMPLETE)
        self.assertIsNone(target.cumulative_effective_inbound)

    def test_data_incomplete_row_last_makes_the_target_data_incomplete(self) -> None:
        """The former first-row-wins behaviour must not hide a later unreliable row."""

        _construction, result = self._two_parent_rows(unusable_position=1)
        self.assertEqual(len(result.targets), 1)
        target = result.targets[0]
        self.assertEqual(target.outcome, EFFECTIVE_INBOUND_DATA_INCOMPLETE)
        self.assertIsNone(target.cumulative_effective_inbound)

    def test_grouped_data_incomplete_target_keeps_every_upstream_trace(self) -> None:
        _construction, result = self._two_parent_rows(unusable_position=1)
        target = result.targets[0]
        self.assertEqual(len(target.requirement_traces), 2)
        self.assertEqual(
            len(
                {
                    trace.production_requirement_reference
                    for trace in target.requirement_traces
                }
            ),
            2,
        )
        self.assertEqual(
            len({trace.bom_component_reference for trace in target.requirement_traces}),
            2,
        )
        self.assertTrue(target.notes)

    def test_incomplete_row_does_not_remove_a_sole_normal_row(self) -> None:
        """A single normal row is still a normal target (no invented representative)."""

        _construction, result = self.build(
            name="grouped-single-row",
            inbounds=[self.inbound_record(ordered_qty="50", arrival="2026-10-12")],
            requirements=[self.requirement_record(production_qty="10")],
            bom_components=[self.bom_record()],
        )
        target = result.targets[0]
        self.assertIsNone(target.outcome)
        self.assert_qty(target.cumulative_effective_inbound, "50")
        self.assertEqual(len(target.requirement_traces), 1)
        trace = target.requirement_traces[0]
        self.assertIn("|Production Requirement|", trace.production_requirement_reference)
        self.assertIn("|BOM Component|", trace.bom_component_reference)


class OverReceiptIssueTests(EffectiveInboundTestCase):
    """Regression: ``received_qty > ordered_qty`` must also raise a Data Quality Issue.

    ``§2.6.2`` / ``§4.4.47`` require the ``DATA_INCOMPLETE`` outcome **and** a reported
    finding, using the already registered ``CONSISTENCY`` / ``CONSISTENCY_CONFLICT``
    taxonomy (``§4.4.92``).  No new category, reason or severity is introduced.
    """

    @staticmethod
    def _conflicts(issues) -> list:
        return [
            issue
            for issue in issues
            if issue.category == "CONSISTENCY"
            and issue.reason == "CONSISTENCY_CONFLICT"
        ]

    @staticmethod
    def _payload_conflicts(issues: list) -> list:
        return [
            issue
            for issue in issues
            if issue["category"] == "CONSISTENCY"
            and issue["reason"] == "CONSISTENCY_CONFLICT"
        ]

    def _two_required_dates(self, *, name: str, inbounds: list[dict[str, Any]]):
        return self.build(
            name=name,
            inbounds=inbounds,
            requirements=[
                self.requirement_record(required_date="2026-10-15"),
                self.requirement_record(required_date="2026-10-20"),
            ],
            bom_components=[
                self.bom_record(required_date="2026-10-15"),
                self.bom_record(required_date="2026-10-20"),
            ],
        )

    def test_over_receipt_emits_exactly_one_registered_conflict(self) -> None:
        _construction, result, target = self.evaluate(
            name="over-receipt-issue",
            inbound=self.inbound_record(ordered_qty="100", received_qty="120"),
        )
        evaluation = target.evaluations[0]
        self.assertEqual(evaluation.outcome, EFFECTIVE_INBOUND_DATA_INCOMPLETE)
        evaluation_conflicts = self._conflicts(evaluation.rule_issues)
        self.assertEqual(len(evaluation_conflicts), 1)
        issue = evaluation_conflicts[0]
        self.assertEqual(issue.category, "CONSISTENCY")
        self.assertEqual(issue.reason, "CONSISTENCY_CONFLICT")
        # Layer 2 (evidence/value validation), not Layer 1 package structure.
        self.assertEqual(issue.layer, 2)
        self.assertTrue(issue.location)
        self.assertTrue(issue.design_reference)
        self.assertIn("120", issue.detail)
        self.assertIn("100", issue.detail)
        # The consolidated finding surface exposes it too, and only once.
        self.assertEqual(len(self._conflicts(evaluation.issues)), 1)
        # Exactly one logical finding at target level too: no N-fold duplication.
        self.assertEqual(len(self._conflicts(target.rule_issues)), 1)
        self.assertEqual(len(self._conflicts(target.issues)), 1)
        # And exactly one at the authoritative result level.
        self.assertEqual(len(self._conflicts(result.rule_issues)), 1)

    def test_over_receipt_conflict_is_deduplicated_across_required_dates(self) -> None:
        _construction, result = self._two_required_dates(
            name="over-receipt-multi-date",
            inbounds=[self.inbound_record(ordered_qty="100", received_qty="120")],
        )
        keys: set[tuple[str, str, str]] = set()
        for target in result.targets:
            conflicts = self._conflicts(target.rule_issues)
            self.assertEqual(len(conflicts), 1)
            for issue in conflicts:
                keys.add((issue.location, issue.category, issue.reason))
        # The defect belongs to the inbound evidence, not to a required date.
        self.assertEqual(len(keys), 1)

    def test_result_rule_issues_register_one_evidence_defect_once(self) -> None:
        """A: one over-receipt inbound + 2 required dates -> exactly one logical finding.

        The defect is an **inbound evidence** defect, not a ``(required_date, inbound)``
        defect, so the authoritative result-level surface must not repeat it per target.
        """

        _construction, result = self._two_required_dates(
            name="over-receipt-result-dedup",
            inbounds=[self.inbound_record(ordered_qty="100", received_qty="120")],
        )
        self.assertEqual(len(result.targets), 2)
        # Local trace may carry it on every target it was re-reached from.
        for target in result.targets:
            self.assertEqual(len(self._conflicts(target.rule_issues)), 1)
        self.assertEqual(len(result.rule_issues), 1)
        self.assertEqual(len(self._conflicts(result.rule_issues)), 1)
        # The affected inbound evidence is still identified, not lost to the dedup.
        issue = result.rule_issues[0]
        self.assertIn("2.json[0]", issue.location)
        self.assertIn("120", issue.detail)

        payload = result.to_dict()
        self.assertEqual(len(self._payload_conflicts(payload["rule_issues"])), 1)
        self.assertEqual(len(self._payload_conflicts(payload["issues"])), 1)
        self.assertEqual(
            payload["rule_issues"][0],
            result.rule_issues[0].to_dict(),
        )

    def test_two_distinct_inbound_records_keep_two_logical_findings(self) -> None:
        """B: two distinct G3-A over-receipt records -> two logical findings.

        Content-identical records at different ordinals are distinct supply evidence, so the
        result-level dedup must not merge their defects.
        """

        record = self.inbound_record(ordered_qty="100", received_qty="120")
        _construction, result = self._two_required_dates(
            name="over-receipt-two-records",
            inbounds=[dict(record), dict(record)],
        )
        self.assertEqual(len(result.targets), 2)
        self.assertEqual(len(result.rule_issues), 2)
        self.assertEqual(
            len({issue.location for issue in result.rule_issues}), 2
        )

        payload = result.to_dict()
        self.assertEqual(len(self._payload_conflicts(payload["rule_issues"])), 2)
        self.assertEqual(len(self._payload_conflicts(payload["issues"])), 2)
        self.assertEqual(
            {issue["location"] for issue in payload["rule_issues"]},
            {issue.location for issue in result.rule_issues},
        )

    def test_over_receipt_conflict_uses_no_new_taxonomy(self) -> None:
        _construction, _result, target = self.evaluate(
            name="over-receipt-taxonomy",
            inbound=self.inbound_record(ordered_qty="0", received_qty="0.5"),
        )
        conflicts = self._conflicts(target.rule_issues)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(
            {issue.category for issue in conflicts}, {"CONSISTENCY"}
        )
        self.assertEqual(
            {issue.reason for issue in conflicts}, {"CONSISTENCY_CONFLICT"}
        )

    def test_valid_non_contributing_records_raise_no_conflict(self) -> None:
        cases = {
            "ineligible-cancelled": dict(status="CANCELLED", arrival="2026-10-12"),
            "ineligible-closed": dict(status="CLOSED", arrival="2026-10-12"),
            "ineligible-completed": dict(status="COMPLETED", arrival="2026-10-12"),
            "arrival-after-required": dict(status="OPEN", arrival="2026-10-20"),
            "zero-remaining": dict(
                status="OPEN", ordered_qty="100", received_qty="100"
            ),
            "fully-open": dict(status="OPEN", ordered_qty="100", received_qty="0"),
        }
        for name, kwargs in cases.items():
            with self.subTest(case=name):
                _construction, _result, target = self.evaluate(
                    name=f"no-conflict-{name}",
                    inbound=self.inbound_record(**kwargs),
                )
                self.assertIsNone(target.evaluations[0].outcome)
                self.assertEqual(self._conflicts(target.rule_issues), [])
                self.assertEqual(self._conflicts(target.issues), [])

    def test_missing_and_negative_quantities_do_not_invent_a_conflict(self) -> None:
        for name, kwargs in {
            "missing-ordered": dict(ordered_qty=OMIT),
            "missing-received": dict(received_qty=OMIT),
            "negative-ordered": dict(ordered_qty="-1"),
            "negative-received": dict(received_qty="-5"),
        }.items():
            with self.subTest(case=name):
                _construction, _result, target = self.evaluate(
                    name=f"no-conflict-{name}",
                    inbound=self.inbound_record(**kwargs),
                )
                self.assertEqual(
                    target.evaluations[0].outcome, EFFECTIVE_INBOUND_DATA_INCOMPLETE
                )
                # A missing / negative quantity is not a cross-field conflict.
                self.assertEqual(self._conflicts(target.rule_issues), [])

    def test_over_receipt_conflict_is_json_serialisable(self) -> None:
        _construction, result, _target = self.evaluate(
            name="over-receipt-json",
            inbound=self.inbound_record(ordered_qty="100", received_qty="120"),
        )
        payload = result.to_dict()
        for surface in ("rule_issues", "issues"):
            with self.subTest(surface=surface):
                self.assertIn(surface, payload)
        target_payload = payload["targets"][0]
        for surface in ("rule_issues", "inherited_issues", "requirement_traces"):
            with self.subTest(surface=surface):
                self.assertIn(surface, target_payload)
        conflicts = [
            issue
            for issue in target_payload["rule_issues"]
            if issue["category"] == "CONSISTENCY"
            and issue["reason"] == "CONSISTENCY_CONFLICT"
        ]
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["layer"], 2)
        self.assertEqual(
            len(
                [
                    issue
                    for issue in target_payload["evaluations"][0]["rule_issues"]
                    if issue["category"] == "CONSISTENCY"
                    and issue["reason"] == "CONSISTENCY_CONFLICT"
                ]
            ),
            1,
        )
        # C: the top-level finding surface keeps the same cardinality.
        self.assertEqual(len(self._payload_conflicts(payload["rule_issues"])), 1)
        self.assertEqual(
            payload["rule_issues"], target_payload["rule_issues"]
        )


if __name__ == "__main__":
    unittest.main()
