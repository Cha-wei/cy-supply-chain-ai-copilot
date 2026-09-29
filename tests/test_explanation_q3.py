"""``§5.3`` Q3 purchase-quantity explanation runtime slice (provider-neutral core).

Covers the first P0 AI Explanation implementation unit authorized by ``ADR-002``: the Q3
read-only projection, the provider-agnostic single-call seam, the runtime-assembled response
artifact, the deterministic fail-closed paths and -- specifically -- the evidence-fidelity
protection that keeps a structurally valid but semantically wrong provider answer from ever
becoming ``OUTCOME_EXPLAINED``.

Every provider used here is a **stub / fake**: this suite performs no network call, uses no
real credential, reads no environment secret and imports no provider SDK.  The complete
recommendation fixtures reuse the existing end-to-end chain builder, so the projection is
exercised against a **real** accepted SIMULATED package rather than a hand-made dictionary.
"""

from __future__ import annotations

import ast
import contextlib
import dataclasses
import io
import json
import os
import unittest
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import Any

import snapshot_loader.explanation_q3 as q3_module
import snapshot_loader.explanation_seam as seam_module
from snapshot_loader import (
    ANSWER_KINDS,
    ANSWER_KIND_LITERALS,
    COMPLETENESS_COMPLETE,
    COMPLETENESS_DATA_INCOMPLETE,
    COMPLETENESS_RECOMMENDATION_NOT_STATED,
    HUMAN_DECISION_REQUIRED_TEXT,
    NOTE_INCOMPLETE,
    NOTE_NO_RECOMMENDATION_BY_DESIGN,
    NOTE_PROVIDER_UNAVAILABLE,
    NOTE_RESPONSE_UNACCEPTABLE,
    OUTCOME_EXPLAINED,
    OUTCOME_NO_RECOMMENDATION_BY_DESIGN,
    OUTCOME_PROVIDER_UNAVAILABLE,
    OUTCOME_RECOMMENDATION_INCOMPLETE,
    OUTCOME_RESPONSE_UNACCEPTABLE,
    Q3_FACT_FIELDS,
    Q3_GRAIN_FIELDS,
    Q3_QUESTION,
    RESPONSE_KEYS,
    ProcurementRecommendationResult,
    parse_exact_quantity,
    validate_provider_response,
)
from tests.test_shortage_calculation import D2, DEMAND, PLANT
from tests.test_supplier_risk_input import SupplierRiskInputTestCase

#: The registered kind that matches the fixture's relation (recommended 100 > shortage 30).
FIXTURE_KIND = "MOQ_RAISED_RECOMMENDATION_ABOVE_SHORTAGE"
#: The registered kind that matches a recommendation equal to the shortage.
EQUAL_KIND = "RECOMMENDATION_EQUALS_SHORTAGE"
#: All five quantities are required evidence for :data:`FIXTURE_KIND`.
FIXTURE_EVIDENCE: tuple[str, ...] = (
    "ShortageQty",
    "BasePurchaseNeed",
    "ApplicableMOQ",
    "MOQAdjustmentQty",
    "RecommendedPurchaseQty",
)

#: The four ``§5.5`` meanings carried by the assembled artifact (runtime-owned strings).
ARTIFACT_KEYS: tuple[str, ...] = (
    "answer",
    "evidence",
    "uncertainty",
    "human_decision_required",
)

#: A compliant provider **selection** (no prose: the runtime renders every string).
GOOD_SELECTION: dict[str, object] = {
    "answer_kind": FIXTURE_KIND,
    "evidence": list(FIXTURE_EVIDENCE),
    "uncertainty": [],
    "human_decision_required": True,
}

#: The prose payload the independent review used to demonstrate the merge blocker: it is
#: structurally plausible but misstates the shortage and invents an approval.
REVIEW_FINDING_PROSE: dict[str, object] = {
    "answer": "实际缺料 100，所以建议采购 100。",
    "evidence": ["ShortageQty = 100"],
    "uncertainty": [],
    "human_decision_required": "无需人工决策，该采购已经批准。",
}

#: Keys that must never appear anywhere in a Q3 projection (``§5.3`` Q3 boundary).
FORBIDDEN_PROJECTION_KEYS = {
    "accepted_package",
    "content_view_digest",
    "analysis_run",
    "layer2",
    "construction",
    "requirements",
    "inventory",
    "inbounds",
    "substitutes",
    "shortage",
    "procurement_policy_input",
    "supplier_risk_input",
    "supplier_risk",
    "Classification",
    "rule_id",
    "notes",
}

#: Key names that would indicate a credential leaked into a payload.
CREDENTIAL_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "token",
    "secret",
    "credential",
    "password",
}


def _walk_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            keys.add(key)
            keys |= _walk_keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            keys |= _walk_keys(item)
    return keys


def _walk_values(value: Any) -> list[Any]:
    values: list[Any] = [value]
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_values(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            values.extend(_walk_values(item))
    return values


class RecordingProvider:
    """A stub provider that records the payloads it receives (no network, no credential)."""

    def __init__(self, response: object = None, error: BaseException | None = None) -> None:
        self.calls: list[object] = []
        self._response = GOOD_SELECTION if response is None else response
        self._error = error

    def explain(self, projection: object) -> object:
        self.calls.append(projection)
        if self._error is not None:
            raise self._error
        return self._response


class MutatingProvider(RecordingProvider):
    """A hostile stub that mutates the payload it was handed and still selects validly."""

    def explain(self, projection: object) -> object:
        self.calls.append(projection)
        assert isinstance(projection, dict)
        facts = projection["facts"]
        assert isinstance(facts, dict)
        facts["ShortageQty"] = {"numerator": 999, "denominator": 1}
        projection["question"] = "TAMPERED"
        return dict(GOOD_SELECTION)


class AlternativeProvider:
    """A second, differently-implemented provider: the seam must stay replaceable."""

    def __init__(self) -> None:
        self.received: object = None

    def explain(self, projection: object) -> object:
        self.received = projection
        return {
            "answer_kind": FIXTURE_KIND,
            "evidence": [
                "RecommendedPurchaseQty",
                "ApplicableMOQ",
                "ShortageQty",
                "BasePurchaseNeed",
                "MOQAdjustmentQty",
            ],
            "uncertainty": [],
            "human_decision_required": True,
        }


class Q3ExplanationTests(SupplierRiskInputTestCase):
    """One real Q3 recommendation plus the stubbed provider seam."""

    # --- fixtures ---------------------------------------------------------------------

    def complete_recommendations(self, name: str):
        """A real accepted SIMULATED chain whose family has a numeric recommendation."""

        built = self.build_chain(name=name)
        return self.recommendations(built), built

    def incomplete_recommendations(self, name: str):
        """The same chain with no applicable Phase B policy input (``DATA_INCOMPLETE``)."""

        built = self.build_chain(moq_policies=(), name=name)
        return self.recommendations(built), built

    def explain(self, recommendations, provider):
        return q3_module.explain_q3(
            recommendations, provider, plant_id=PLANT, material_code=DEMAND
        )

    # --- 1 complete projection --------------------------------------------------------

    def test_q3_1_complete_projection_carries_exactly_the_allowed_fields(self) -> None:
        recommendations, _built = self.complete_recommendations("q3-1")
        recommendation = recommendations.for_family(PLANT, DEMAND)
        self.assertIsNotNone(recommendation)
        assert recommendation is not None

        projection = q3_module.build_q3_projection(recommendation)

        self.assertEqual(set(projection), {"question", "grain", "facts", "completeness"})
        self.assertEqual(projection["question"], Q3_QUESTION)
        self.assertEqual(set(projection["grain"]), set(Q3_GRAIN_FIELDS))
        self.assertEqual(set(projection["facts"]), set(Q3_FACT_FIELDS))
        self.assertEqual(
            set(projection["completeness"]),
            {
                "state",
                "valid_absence",
                "outcome",
                "missing_facts",
                "root_condition",
                "policy_root_condition",
                "applicability_basis",
                "shortage_reference",
                "policy_input_reference",
                "inherited_issues",
                "rule_issues",
            },
        )
        self.assertEqual(projection["completeness"]["state"], COMPLETENESS_COMPLETE)
        self.assertEqual(projection["completeness"]["missing_facts"], [])
        self.assertIsNone(projection["completeness"]["valid_absence"])
        self.assertEqual(projection["grain"]["plant_id"], PLANT)
        self.assertEqual(projection["grain"]["material_code"], DEMAND)
        self.assertEqual(projection["grain"]["RecommendationNeedDate"], D2)

    # --- 2 exact numeric semantics ----------------------------------------------------

    def test_q3_2_exact_numeric_semantics_are_lossless(self) -> None:
        recommendations, _built = self.complete_recommendations("q3-2")
        recommendation = recommendations.for_family(PLANT, DEMAND)
        assert recommendation is not None

        facts = q3_module.build_q3_projection(recommendation)["facts"]
        self.assertEqual(facts["ShortageQty"], {"numerator": 30, "denominator": 1})
        self.assertEqual(facts["BasePurchaseNeed"], {"numerator": 30, "denominator": 1})
        self.assertEqual(facts["ApplicableMOQ"], "100")
        self.assertEqual(facts["MOQAdjustmentQty"], {"numerator": 70, "denominator": 1})
        self.assertEqual(facts["RecommendedPurchaseQty"], {"numerator": 100, "denominator": 1})

        # A non-terminating exact rational survives the projection without rounding, and the
        # runtime renders it exactly rather than as a float.  The MOQ is set to the same exact
        # value so the registered relation (recommended == MOQ > shortage) still holds.
        exact_third = dataclasses.replace(
            recommendation,
            shortage_qty=Fraction(1, 3),
            base_purchase_need=Fraction(1, 3),
            moq_adjustment_qty=Fraction(2, 3),
            recommended_purchase_qty=Fraction(1, 1),
            applicable_moq=parse_exact_quantity("1"),
        )
        third_facts = q3_module.build_q3_projection(exact_third)["facts"]
        self.assertEqual(third_facts["ShortageQty"], {"numerator": 1, "denominator": 3})
        self.assertEqual(
            json.loads(json.dumps(third_facts, sort_keys=True))["ShortageQty"],
            {"numerator": 1, "denominator": 3},
        )
        third_result = self.explain(
            ProcurementRecommendationResult(
                analysis_run=recommendations.analysis_run,
                recommendations=(exact_third,),
            ),
            RecordingProvider(),
        )
        self.assertEqual(third_result.outcome, OUTCOME_EXPLAINED)
        assert third_result.response is not None
        self.assertIn("ShortageQty = 1/3", third_result.response.evidence)

        for value in _walk_values(q3_module.build_q3_projection(recommendation)):
            self.assertNotIsInstance(value, float)

    # --- 3 shortage vs recommended ----------------------------------------------------

    def test_q3_3_shortage_and_recommended_quantities_stay_distinct(self) -> None:
        recommendations, _built = self.complete_recommendations("q3-3")
        recommendation = recommendations.for_family(PLANT, DEMAND)
        assert recommendation is not None
        projection = q3_module.build_q3_projection(recommendation)

        self.assertEqual(projection["facts"]["ShortageQty"], {"numerator": 30, "denominator": 1})
        self.assertEqual(
            projection["facts"]["RecommendedPurchaseQty"], {"numerator": 100, "denominator": 1}
        )

        result = self.explain(recommendations, RecordingProvider())
        response = result.response
        self.assertIsNotNone(response)
        assert response is not None
        self.assertIn("ShortageQty = 30", response.evidence)
        self.assertIn("RecommendedPurchaseQty = 100", response.evidence)
        self.assertNotIn("ShortageQty = 100", response.evidence)
        self.assertIn("实际缺口为 30", response.answer)
        self.assertIn("建议采购量被上调为 100", response.answer)
        self.assertNotIn("实际缺料 100", response.answer)
        payload = json.dumps(result.to_dict(), ensure_ascii=False)
        self.assertIn("ShortageQty = 30", payload)
        self.assertIn("RecommendedPurchaseQty = 100", payload)

    # --- 4 projection scope -----------------------------------------------------------

    def test_q3_4_projection_excludes_package_and_unrelated_pipeline_fields(self) -> None:
        recommendations, built = self.complete_recommendations("q3-4")
        recommendation = recommendations.for_family(PLANT, DEMAND)
        assert recommendation is not None
        projection = q3_module.build_q3_projection(recommendation)

        self.assertEqual(_walk_keys(projection) & FORBIDDEN_PROJECTION_KEYS, set())
        payload = json.dumps(projection, ensure_ascii=False, sort_keys=True)
        self.assertNotIn(built.accepted.package_id, payload)
        self.assertNotIn(built.accepted.content_view_digest, payload)
        self.assertNotIn("accepted_content_view_digest", payload)
        self.assertNotIn("Supplier Performance", payload)
        self.assertNotIn("Inventory Snapshot", payload)

    # --- 5 provider called exactly once ----------------------------------------------

    def test_q3_5_complete_recommendation_calls_the_provider_exactly_once(self) -> None:
        recommendations, _built = self.complete_recommendations("q3-5")
        provider = RecordingProvider()

        result = self.explain(recommendations, provider)

        self.assertEqual(len(provider.calls), 1)
        self.assertTrue(result.provider_invoked)
        self.assertEqual(result.outcome, OUTCOME_EXPLAINED)
        self.assertTrue(result.explained)
        self.assertIsNone(result.availability_note)

    # --- 6 provider receives projection only -----------------------------------------

    def test_q3_6_provider_receives_only_the_projection(self) -> None:
        recommendations, _built = self.complete_recommendations("q3-6")
        recommendation = recommendations.for_family(PLANT, DEMAND)
        assert recommendation is not None
        projection = q3_module.build_q3_projection(recommendation)
        provider = RecordingProvider()

        result = self.explain(recommendations, provider)

        received = provider.calls[0]
        self.assertEqual(received, projection)
        self.assertIsNot(received, result.projection)
        self.assertIsNot(received, recommendations)
        self.assertIsNot(received, recommendation)
        self.assertIsInstance(received, dict)
        self.assertEqual(received["question"], Q3_QUESTION)
        self.assertEqual(_walk_keys(received) & FORBIDDEN_PROJECTION_KEYS, set())
        for value in _walk_values(received):
            self.assertIsInstance(value, (dict, list, str, int, bool, type(None)))

    # --- 7 response artifact is runtime-assembled ------------------------------------

    def test_q3_7_provider_response_becomes_the_response_artifact(self) -> None:
        recommendations, _built = self.complete_recommendations("q3-7")
        provider = RecordingProvider()

        result = self.explain(recommendations, provider)

        response = result.response
        self.assertIsNotNone(response)
        assert response is not None
        self.assertEqual(set(response.to_dict()), set(ARTIFACT_KEYS))
        self.assertEqual(set(RESPONSE_KEYS), set(GOOD_SELECTION))
        self.assertEqual(
            response.answer,
            ANSWER_KINDS[FIXTURE_KIND].template.format(
                ShortageQty="30",
                BasePurchaseNeed="30",
                ApplicableMOQ="100",
                MOQAdjustmentQty="70",
                RecommendedPurchaseQty="100",
            ),
        )
        self.assertEqual(
            list(response.evidence),
            [
                "ShortageQty = 30",
                "BasePurchaseNeed = 30",
                "ApplicableMOQ = 100",
                "MOQAdjustmentQty = 70",
                "RecommendedPurchaseQty = 100",
            ],
        )
        self.assertEqual(list(response.uncertainty), [])
        self.assertEqual(response.human_decision_required, HUMAN_DECISION_REQUIRED_TEXT)
        self.assertEqual(result.to_dict()["response"], response.to_dict())

        # A different provider implementation selecting a different evidence order is still
        # accepted: the artifact stays runtime-assembled and provider-neutral.
        alternative = AlternativeProvider()
        other = self.explain(recommendations, alternative)
        self.assertEqual(other.outcome, OUTCOME_EXPLAINED)
        assert other.response is not None
        self.assertEqual(set(other.response.to_dict()), set(ARTIFACT_KEYS))
        self.assertEqual(
            other.response.human_decision_required, HUMAN_DECISION_REQUIRED_TEXT
        )
        self.assertIsNotNone(alternative.received)
        self.assertEqual(other.response.evidence[0], "RecommendedPurchaseQty = 100")

    # --- 8/9 fail-closed: incomplete + valid absence ----------------------------------

    def test_q3_8_incomplete_recommendation_does_not_call_the_provider(self) -> None:
        recommendations, _built = self.incomplete_recommendations("q3-8")
        provider = RecordingProvider()

        result = self.explain(recommendations, provider)

        self.assertEqual(provider.calls, [])
        self.assertFalse(result.provider_invoked)
        self.assertEqual(result.outcome, OUTCOME_RECOMMENDATION_INCOMPLETE)
        self.assertFalse(result.explained)
        self.assertIsNone(result.response)
        self.assertEqual(result.availability_note, NOTE_INCOMPLETE)
        self.assertEqual(
            result.projection["completeness"]["state"], COMPLETENESS_DATA_INCOMPLETE
        )

        absence_built = self.build_chain(demands=((DEMAND, "10", D2),), name="q3-8-absence")
        absence = self.recommendations(absence_built)
        absence_provider = RecordingProvider()
        absence_result = self.explain(absence, absence_provider)
        self.assertEqual(absence_provider.calls, [])
        self.assertEqual(absence_result.outcome, OUTCOME_NO_RECOMMENDATION_BY_DESIGN)
        self.assertEqual(absence_result.availability_note, NOTE_NO_RECOMMENDATION_BY_DESIGN)
        self.assertEqual(
            absence_result.projection["completeness"]["state"],
            COMPLETENESS_RECOMMENDATION_NOT_STATED,
        )
        self.assertTrue(absence_result.projection["completeness"]["valid_absence"])
        self.assertEqual(
            absence_result.projection["completeness"]["missing_facts"], list(Q3_FACT_FIELDS)
        )

    def test_q3_9_incomplete_evidence_is_reported_explicitly(self) -> None:
        recommendations, _built = self.incomplete_recommendations("q3-9")
        recommendation = recommendations.for_family(PLANT, DEMAND)
        assert recommendation is not None
        provider = RecordingProvider()

        result = self.explain(recommendations, provider)

        missing = result.projection["completeness"]["missing_facts"]
        self.assertIn("ApplicableMOQ", missing)
        for name in missing:
            self.assertIn(name, Q3_FACT_FIELDS)
            self.assertIsNone(result.projection["facts"][name])
        self.assertTrue(result.missing_evidence)
        payloads = json.dumps([dict(item) for item in result.missing_evidence], ensure_ascii=False)
        self.assertIn(recommendation.root_condition, payloads)
        self.assertIn("unavailable_facts", payloads)
        self.assertIsNone(result.projection["completeness"]["valid_absence"])

    # --- 10 provider exception --------------------------------------------------------

    def test_q3_10_provider_exception_fails_closed(self) -> None:
        recommendations, _built = self.complete_recommendations("q3-10")
        before = recommendations.to_dict()
        provider = RecordingProvider(error=RuntimeError("leaked-provider-secret-sentinel"))

        result = self.explain(recommendations, provider)

        self.assertEqual(len(provider.calls), 1)
        self.assertTrue(result.provider_invoked)
        self.assertEqual(result.outcome, OUTCOME_PROVIDER_UNAVAILABLE)
        self.assertIsNone(result.response)
        self.assertEqual(result.availability_note, NOTE_PROVIDER_UNAVAILABLE)
        payload = json.dumps(result.to_dict(), ensure_ascii=False)
        self.assertIn("RuntimeError", payload)
        self.assertNotIn("leaked-provider-secret-sentinel", payload)
        self.assertEqual(recommendations.to_dict(), before)

    # --- 11 malformed / unacceptable selections ---------------------------------------

    def test_q3_11_malformed_or_unacceptable_response_fails_closed(self) -> None:
        recommendations, _built = self.complete_recommendations("q3-11")
        projection = q3_module.build_q3_projection(
            recommendations.for_family(PLANT, DEMAND)  # type: ignore[arg-type]
        )
        unacceptable: tuple[tuple[str, object], ...] = (
            ("not-a-mapping", "ShortageQty = 30"),
            ("missing-key", {k: v for k, v in GOOD_SELECTION.items() if k != "evidence"}),
            ("extra-key", {**GOOD_SELECTION, "note": "shortage was 100"}),
            ("unregistered-kind", {**GOOD_SELECTION, "answer_kind": "SUPPLIER_PRICE_INCREASE"}),
            ("empty-evidence", {**GOOD_SELECTION, "evidence": []}),
            ("evidence-not-a-list", {**GOOD_SELECTION, "evidence": "ShortageQty"}),
            ("unknown-fact-name", {**GOOD_SELECTION, "evidence": ["Classification"]}),
            ("value-smuggled-in-name", {**GOOD_SELECTION, "evidence": ["ShortageQty = 100"]}),
            ("evidence-missing-required-fact", {**GOOD_SELECTION, "evidence": ["ShortageQty"]}),
            ("duplicate-evidence", {**GOOD_SELECTION, "evidence": ["ShortageQty", "ShortageQty"]}),
            ("uncertainty-not-a-list", {**GOOD_SELECTION, "uncertainty": 3}),
            ("uncertainty-invented", {**GOOD_SELECTION, "uncertainty": ["ShortageQty"]}),
            ("uncertainty-unknown-name", {**GOOD_SELECTION, "uncertainty": ["SupplierPrice"]}),
            ("human-decision-false", {**GOOD_SELECTION, "human_decision_required": False}),
            (
                "human-decision-prose",
                {**GOOD_SELECTION, "human_decision_required": "无需人工决策，该采购已经批准。"},
            ),
            ("relations-swapped", {**GOOD_SELECTION, "answer_kind": EQUAL_KIND}),
            ("projection-echo", projection),
            ("review-finding-prose", REVIEW_FINDING_PROSE),
        )
        for label, raw in unacceptable:
            with self.subTest(label=label):
                provider = RecordingProvider(response=raw)
                result = self.explain(recommendations, provider)
                self.assertEqual(len(provider.calls), 1)
                self.assertEqual(result.outcome, OUTCOME_RESPONSE_UNACCEPTABLE)
                self.assertIsNone(result.response)
                self.assertFalse(result.explained)
                self.assertEqual(result.availability_note, NOTE_RESPONSE_UNACCEPTABLE)
                self.assertIsNone(validate_provider_response(raw, result.projection))

    # --- 12 deterministic result unchanged -------------------------------------------

    def test_q3_12_deterministic_recommendation_object_is_unchanged(self) -> None:
        recommendations, _built = self.complete_recommendations("q3-12")
        recommendation = recommendations.for_family(PLANT, DEMAND)
        assert recommendation is not None
        before_result = recommendations.to_dict()
        before_recommendation = recommendation.to_dict()

        self.explain(recommendations, RecordingProvider())
        self.explain(recommendations, RecordingProvider(error=RuntimeError("boom")))
        mutating = MutatingProvider()
        mutated = self.explain(recommendations, mutating)

        self.assertEqual(recommendations.to_dict(), before_result)
        self.assertEqual(recommendation.to_dict(), before_recommendation)
        self.assertEqual(mutated.projection["question"], Q3_QUESTION)
        self.assertEqual(
            mutated.projection["facts"]["ShortageQty"], {"numerator": 30, "denominator": 1}
        )
        self.assertEqual(mutated.outcome, OUTCOME_EXPLAINED)

        incomplete, _ = self.incomplete_recommendations("q3-12-incomplete")
        before_incomplete = incomplete.to_dict()
        self.explain(incomplete, RecordingProvider())
        self.assertEqual(incomplete.to_dict(), before_incomplete)

    # --- 13 no secret / credential anywhere -------------------------------------------

    def test_q3_13_no_secret_or_credential_in_projection_response_or_captured_output(
        self,
    ) -> None:
        sentinel = "POC-TEST-SECRET-SENTINEL-NOT-A-REAL-CREDENTIAL"
        previous = os.environ.get("POC_TEST_SECRET_SENTINEL")
        os.environ["POC_TEST_SECRET_SENTINEL"] = sentinel
        self.addCleanup(self._restore_environment, previous)

        recommendations, _built = self.complete_recommendations("q3-13")
        provider = RecordingProvider()
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = self.explain(recommendations, provider)

        texts = (
            json.dumps(result.to_dict(), ensure_ascii=False),
            json.dumps(provider.calls[0], ensure_ascii=False),
            json.dumps(result.response.to_dict() if result.response else {}, ensure_ascii=False),
            stdout.getvalue(),
            stderr.getvalue(),
        )
        for text in texts:
            self.assertNotIn(sentinel, text)

        for value in (
            _walk_keys(provider.calls[0]),
            _walk_keys(result.to_dict()),
            _walk_keys(result.response.to_dict() if result.response else {}),
        ):
            self.assertEqual({key.lower() for key in value} & CREDENTIAL_KEYS, set())

        self._assert_modules_stay_offline()

    def _restore_environment(self, previous: str | None) -> None:
        if previous is None:
            os.environ.pop("POC_TEST_SECRET_SENTINEL", None)
        else:
            os.environ["POC_TEST_SECRET_SENTINEL"] = previous

    def _assert_modules_stay_offline(self) -> None:
        """The runtime core reads no environment, opens no file and imports no client."""

        allowed_modules = {
            "__future__",
            "collections",
            "copy",
            "dataclasses",
            "explanation_q3",
            "explanation_seam",
            "fractions",
            "procurement_recommendation",
            "types",
            "typing",
        }
        forbidden_names = {"environ", "getenv", "open", "socket", "urlopen"}
        for module in (seam_module, q3_module):
            source = Path(module.__file__).read_text(encoding="utf-8")
            tree = ast.parse(source)
            identifiers: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertIn(alias.name.split(".")[0], allowed_modules)
                elif isinstance(node, ast.ImportFrom):
                    self.assertIn((node.module or "").split(".")[0], allowed_modules)
                elif isinstance(node, ast.Name):
                    identifiers.add(node.id)
                elif isinstance(node, ast.Attribute):
                    identifiers.add(node.attr)
                elif isinstance(node, ast.keyword):
                    identifiers.add(node.arg or "")
            self.assertEqual(identifiers & forbidden_names, set(), msg=module.__name__)

    # --- 14 repeatable serialization ---------------------------------------------------

    def test_q3_14_projection_serialization_is_repeatable(self) -> None:
        recommendations, _built = self.complete_recommendations("q3-14")
        recommendation = recommendations.for_family(PLANT, DEMAND)
        assert recommendation is not None

        first = q3_module.build_q3_projection(recommendation)
        second = q3_module.build_q3_projection(recommendation)
        self.assertEqual(first, second)
        self.assertEqual(
            json.dumps(first, sort_keys=True, ensure_ascii=False),
            json.dumps(second, sort_keys=True, ensure_ascii=False),
        )

        provider_one = RecordingProvider()
        provider_two = RecordingProvider()
        result_one = self.explain(recommendations, provider_one)
        result_two = self.explain(recommendations, provider_two)
        self.assertEqual(
            json.dumps(result_one.to_dict(), sort_keys=True, ensure_ascii=False),
            json.dumps(result_two.to_dict(), sort_keys=True, ensure_ascii=False),
        )
        self.assertIsNot(result_one.response, result_two.response)

    # --- 15 adversarial: mutated quantity cannot be expressed -------------------------

    def test_q3_15_structurally_valid_mutated_quantity_fails_closed(self) -> None:
        recommendations, _built = self.complete_recommendations("q3-15")
        attempts: tuple[tuple[str, object], ...] = (
            ("value-in-evidence-name", {**GOOD_SELECTION, "evidence": ["ShortageQty = 100"]}),
            ("extra-numeric-key", {**GOOD_SELECTION, "ShortageQty": "100"}),
            (
                "prose-answer-with-wrong-number",
                {
                    "answer_kind": FIXTURE_KIND,
                    "evidence": list(FIXTURE_EVIDENCE),
                    "uncertainty": [],
                    "human_decision_required": True,
                    "answer": "实际缺料 100。",
                },
            ),
        )
        for label, raw in attempts:
            with self.subTest(label=label):
                result = self.explain(recommendations, RecordingProvider(response=raw))
                self.assertEqual(result.outcome, OUTCOME_RESPONSE_UNACCEPTABLE)
                self.assertIsNone(result.response)
                payload = json.dumps(result.to_dict(), ensure_ascii=False)
                self.assertNotIn("ShortageQty = 100", payload)
                self.assertNotIn("实际缺料 100", payload)

        # The compliant path states the projected values, not the provider's claim.
        explained = self.explain(recommendations, RecordingProvider())
        assert explained.response is not None
        self.assertIn("ShortageQty = 30", explained.response.evidence)
        self.assertNotIn("ShortageQty = 100", explained.response.evidence)

    # --- 16 adversarial: role swap / contradicted relation ----------------------------

    def test_q3_16_structurally_valid_role_swap_fails_closed(self) -> None:
        recommendations, _built = self.complete_recommendations("q3-16")

        # The provider claims the recommendation equals the shortage, but 100 != 30.
        swapped = self.explain(
            recommendations,
            RecordingProvider(response={**GOOD_SELECTION, "answer_kind": EQUAL_KIND}),
        )
        self.assertEqual(swapped.outcome, OUTCOME_RESPONSE_UNACCEPTABLE)
        self.assertIsNone(swapped.response)

        # And the reverse: with a projection whose recommendation equals the shortage, the
        # "MOQ raised it above the shortage" kind contradicts the facts and is rejected.
        equal = dataclasses.replace(
            recommendations.for_family(PLANT, DEMAND),  # type: ignore[arg-type]
            shortage_qty=Fraction(100, 1),
            base_purchase_need=Fraction(100, 1),
            moq_adjustment_qty=Fraction(0, 1),
            recommended_purchase_qty=Fraction(100, 1),
        )
        equal_result = ProcurementRecommendationResult(
            analysis_run=recommendations.analysis_run,
            recommendations=(equal,),
        )
        rejected = self.explain(equal_result, RecordingProvider(response=GOOD_SELECTION))
        self.assertEqual(rejected.outcome, OUTCOME_RESPONSE_UNACCEPTABLE)
        self.assertIsNone(rejected.response)

        accepted = self.explain(
            equal_result,
            RecordingProvider(
                response={
                    "answer_kind": EQUAL_KIND,
                    "evidence": list(FIXTURE_EVIDENCE),
                    "uncertainty": [],
                    "human_decision_required": True,
                }
            ),
        )
        self.assertEqual(accepted.outcome, OUTCOME_EXPLAINED)
        assert accepted.response is not None
        self.assertIn("未发生上调", accepted.response.answer)
        self.assertIn("MOQAdjustmentQty 为 0", accepted.response.answer)

    # --- 17 adversarial: unsupported fact / reason ------------------------------------

    def test_q3_17_structurally_valid_unsupported_fact_or_reason_fails_closed(self) -> None:
        recommendations, _built = self.complete_recommendations("q3-17")
        attempts: tuple[tuple[str, object], ...] = (
            ("invented-reason-kind", {**GOOD_SELECTION, "answer_kind": "SUPPLIER_PRICE_INCREASE"}),
            ("free-text-reason-field", {**GOOD_SELECTION, "reason": "供应商涨价 20%"}),
            ("unprojected-fact", {**GOOD_SELECTION, "evidence": ["Classification"]}),
            ("narrative-field", {**GOOD_SELECTION, "narrative": "由于交期缩短，采购被提前"}),
        )
        for label, raw in attempts:
            with self.subTest(label=label):
                result = self.explain(recommendations, RecordingProvider(response=raw))
                self.assertEqual(result.outcome, OUTCOME_RESPONSE_UNACCEPTABLE)
                payload = json.dumps(result.to_dict(), ensure_ascii=False)
                self.assertNotIn("供应商涨价", payload)
                self.assertNotIn("交期缩短", payload)
        self.assertEqual(ANSWER_KIND_LITERALS, tuple(ANSWER_KINDS))
        self.assertNotIn("SUPPLIER_PRICE_INCREASE", ANSWER_KIND_LITERALS)

    # --- 18 adversarial: approval claim -----------------------------------------------

    def test_q3_18_structurally_valid_approval_claim_fails_closed(self) -> None:
        recommendations, _built = self.complete_recommendations("q3-18")
        attempts: tuple[tuple[str, object], ...] = (
            ("decision-not-required", {**GOOD_SELECTION, "human_decision_required": False}),
            (
                "claimed-approval",
                {
                    **GOOD_SELECTION,
                    "human_decision_required": "无需人工决策，该采购已经批准。",
                },
            ),
            ("approved-boolean-string", {**GOOD_SELECTION, "human_decision_required": "true"}),
        )
        for label, raw in attempts:
            with self.subTest(label=label):
                result = self.explain(recommendations, RecordingProvider(response=raw))
                self.assertEqual(result.outcome, OUTCOME_RESPONSE_UNACCEPTABLE)
                self.assertIsNone(result.response)
                payload = json.dumps(result.to_dict(), ensure_ascii=False)
                self.assertNotIn("已经批准", payload)
                self.assertNotIn("无需人工决策", payload)

        # The compliant artifact always carries the registered reminder verbatim.
        explained = self.explain(recommendations, RecordingProvider())
        assert explained.response is not None
        self.assertEqual(
            explained.response.human_decision_required, HUMAN_DECISION_REQUIRED_TEXT
        )
        self.assertIn("不是已批准的采购量", explained.response.human_decision_required)


    # --- 19 adversarial: provider cannot invent uncertainty ---------------------------

    def test_q3_19_provider_cannot_invent_uncertainty(self) -> None:
        recommendations, _built = self.complete_recommendations("q3-19")
        attempts: tuple[tuple[str, object], ...] = (
            ("relabel-shortage", {**GOOD_SELECTION, "uncertainty": ["ShortageQty"]}),
            ("relabel-moq", {**GOOD_SELECTION, "uncertainty": ["ApplicableMOQ"]}),
            (
                "relabel-several",
                {
                    **GOOD_SELECTION,
                    "uncertainty": ["ShortageQty", "RecommendedPurchaseQty"],
                },
            ),
        )
        for label, raw in attempts:
            with self.subTest(label=label):
                result = self.explain(recommendations, RecordingProvider(response=raw))
                self.assertEqual(result.outcome, OUTCOME_RESPONSE_UNACCEPTABLE)
                self.assertIsNone(result.response)
                self.assertEqual(result.availability_note, NOTE_RESPONSE_UNACCEPTABLE)
                payload = json.dumps(result.to_dict(), ensure_ascii=False)
                self.assertNotIn('"uncertainty": ["ShortageQty"]', payload)

        # The provider-called COMPLETE path keeps uncertainty runtime-owned and empty.
        explained = self.explain(recommendations, RecordingProvider())
        self.assertEqual(explained.outcome, OUTCOME_EXPLAINED)
        assert explained.response is not None
        self.assertEqual(list(explained.response.uncertainty), [])
        self.assertEqual(explained.to_dict()["response"]["uncertainty"], [])

    # --- 20 equality kind must cover all five Q3 quantities ---------------------------

    def test_q3_20_equality_kind_covers_all_five_quantities(self) -> None:
        recommendations, _built = self.complete_recommendations("q3-20")
        equal = dataclasses.replace(
            recommendations.for_family(PLANT, DEMAND),  # type: ignore[arg-type]
            shortage_qty=Fraction(100, 1),
            base_purchase_need=Fraction(100, 1),
            moq_adjustment_qty=Fraction(0, 1),
            recommended_purchase_qty=Fraction(100, 1),
        )
        equal_result = ProcurementRecommendationResult(
            analysis_run=recommendations.analysis_run,
            recommendations=(equal,),
        )

        incomplete_selections: tuple[tuple[str, list[str]], ...] = (
            (
                "missing-ApplicableMOQ",
                ["ShortageQty", "BasePurchaseNeed", "MOQAdjustmentQty", "RecommendedPurchaseQty"],
            ),
            (
                "missing-MOQAdjustmentQty",
                ["ShortageQty", "BasePurchaseNeed", "ApplicableMOQ", "RecommendedPurchaseQty"],
            ),
            ("only-three", ["ShortageQty", "BasePurchaseNeed", "RecommendedPurchaseQty"]),
        )
        for label, evidence in incomplete_selections:
            with self.subTest(label=label):
                result = self.explain(
                    equal_result,
                    RecordingProvider(
                        response={
                            "answer_kind": EQUAL_KIND,
                            "evidence": evidence,
                            "uncertainty": [],
                            "human_decision_required": True,
                        }
                    ),
                )
                self.assertEqual(result.outcome, OUTCOME_RESPONSE_UNACCEPTABLE)
                self.assertIsNone(result.response)

        explained = self.explain(
            equal_result,
            RecordingProvider(
                response={
                    "answer_kind": EQUAL_KIND,
                    "evidence": list(FIXTURE_EVIDENCE),
                    "uncertainty": [],
                    "human_decision_required": True,
                }
            ),
        )
        self.assertEqual(explained.outcome, OUTCOME_EXPLAINED)
        response = explained.response
        assert response is not None
        self.assertEqual(
            list(response.evidence),
            [
                "ShortageQty = 100",
                "BasePurchaseNeed = 100",
                "ApplicableMOQ = 100",
                "MOQAdjustmentQty = 0",
                "RecommendedPurchaseQty = 100",
            ],
        )
        self.assertIn("MOQAdjustmentQty 为 0", response.answer)
        self.assertIn("100", response.answer)
        # All five quantities stay explicit across the artifact: the answer carries the
        # registered values and the evidence section names every one of them.
        self.assertEqual(
            [line.split(" = ")[0] for line in response.evidence], list(Q3_FACT_FIELDS)
        )
        self.assertEqual(
            set(_walk_keys(response.to_dict())),
            {"answer", "evidence", "uncertainty", "human_decision_required"},
        )

    # --- 21 the answer-kind registry is immutable -------------------------------------

    def test_q3_21_answer_kind_registry_is_immutable(self) -> None:
        self.assertIsInstance(ANSWER_KINDS, MappingProxyType)
        self.assertEqual(ANSWER_KIND_LITERALS, tuple(ANSWER_KINDS))
        self.assertEqual(set(ANSWER_KIND_LITERALS), {FIXTURE_KIND, EQUAL_KIND})
        for kind in ANSWER_KINDS.values():
            self.assertEqual(set(kind.required_evidence), set(Q3_FACT_FIELDS))

        with self.assertRaises(TypeError):
            ANSWER_KINDS["INVENTED_KIND"] = ANSWER_KINDS[FIXTURE_KIND]  # type: ignore[index]
        with self.assertRaises(TypeError):
            ANSWER_KINDS[FIXTURE_KIND] = ANSWER_KINDS[EQUAL_KIND]  # type: ignore[index]
        with self.assertRaises(TypeError):
            del ANSWER_KINDS[FIXTURE_KIND]  # type: ignore[attr-defined]
        self.assertEqual(set(ANSWER_KINDS), {FIXTURE_KIND, EQUAL_KIND})

        # The runtime therefore rejects a kind that no registry entry backs.
        recommendations, _built = self.complete_recommendations("q3-21")
        result = self.explain(
            recommendations,
            RecordingProvider(response={**GOOD_SELECTION, "answer_kind": "INVENTED_KIND"}),
        )
        self.assertEqual(result.outcome, OUTCOME_RESPONSE_UNACCEPTABLE)


if __name__ == "__main__":  # pragma: no cover - manual run entry point
    unittest.main()