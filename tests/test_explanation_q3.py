"""``§5.3`` Q3 purchase-quantity explanation runtime slice (provider-neutral core).

Covers the first P0 AI Explanation implementation unit authorized by ``ADR-002``: the Q3
read-only projection, the provider-agnostic single-call seam, the response artifact and the
deterministic fail-closed paths.

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
from typing import Any

import snapshot_loader.explanation_q3 as q3_module
import snapshot_loader.explanation_seam as seam_module
from snapshot_loader import (
    COMPLETENESS_COMPLETE,
    COMPLETENESS_DATA_INCOMPLETE,
    COMPLETENESS_RECOMMENDATION_NOT_STATED,
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
    build_q3_projection,
    explain_q3,
    validate_provider_response,
)
from tests.test_shortage_calculation import D2, DEMAND, PLANT
from tests.test_supplier_risk_input import SupplierRiskInputTestCase

#: A provider answer that paraphrases the projected quantities without inventing any fact.
GOOD_RESPONSE: dict[str, object] = {
    "answer": (
        "The purchase recommendation is 100 because the actual shortage is 30 and the "
        "applicable MOQ is 100."
    ),
    "evidence": ["ShortageQty = 30", "ApplicableMOQ = 100", "RecommendedPurchaseQty = 100"],
    "uncertainty": [],
    "human_decision_required": (
        "A human decides whether to act on this recommendation; it is not an approved order."
    ),
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
    "recommendation",
    "supplier_risk_input",
    "supplier_risk",
    "Classification",
    "rule_id",
    "notes",
    "inherited_issues_total",
}

#: Key names that would indicate a credential leaked into a payload.
CREDENTIAL_KEYS = {"api_key", "apikey", "authorization", "token", "secret", "credential", "password"}


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
        self._response = GOOD_RESPONSE if response is None else response
        self._error = error

    def explain(self, projection: object) -> object:
        self.calls.append(projection)
        if self._error is not None:
            raise self._error
        return self._response


class MutatingProvider(RecordingProvider):
    """A hostile stub that mutates the payload it was handed and still answers."""

    def explain(self, projection: object) -> object:
        self.calls.append(projection)
        assert isinstance(projection, dict)
        facts = projection["facts"]
        assert isinstance(facts, dict)
        facts["ShortageQty"] = {"numerator": 999, "denominator": 1}
        projection["question"] = "TAMPERED"
        return GOOD_RESPONSE


class AlternativeProvider:
    """A second, differently-implemented provider: the seam must stay replaceable."""

    def __init__(self) -> None:
        self.received: object = None

    def explain(self, projection: object) -> object:
        self.received = projection
        return {
            "answer": "Recommended 100 for an actual shortage of 30 given MOQ 100.",
            "evidence": ["BasePurchaseNeed = 30", "MOQAdjustmentQty = 70"],
            "uncertainty": [],
            "human_decision_required": "Human review is still required.",
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

    # --- 1 complete projection --------------------------------------------------------

    def test_q3_1_complete_projection_carries_exactly_the_allowed_fields(self) -> None:
        recommendations, _built = self.complete_recommendations("q3-1")
        recommendation = recommendations.for_family(PLANT, DEMAND)
        self.assertIsNotNone(recommendation)
        assert recommendation is not None

        projection = build_q3_projection(recommendation)

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

        projection = build_q3_projection(recommendation)
        facts = projection["facts"]
        self.assertEqual(facts["ShortageQty"], {"numerator": 30, "denominator": 1})
        self.assertEqual(facts["BasePurchaseNeed"], {"numerator": 30, "denominator": 1})
        self.assertEqual(facts["ApplicableMOQ"], "100")
        self.assertEqual(facts["MOQAdjustmentQty"], {"numerator": 70, "denominator": 1})
        self.assertEqual(facts["RecommendedPurchaseQty"], {"numerator": 100, "denominator": 1})

        # A non-terminating exact rational must survive the projection without rounding.
        exact_third = dataclasses.replace(
            recommendation,
            shortage_qty=Fraction(1, 3),
            base_purchase_need=Fraction(1, 3),
            moq_adjustment_qty=Fraction(0, 1),
            recommended_purchase_qty=Fraction(1, 3),
        )
        third_facts = build_q3_projection(exact_third)["facts"]
        self.assertEqual(third_facts["ShortageQty"], {"numerator": 1, "denominator": 3})
        self.assertEqual(
            third_facts["RecommendedPurchaseQty"], {"numerator": 1, "denominator": 3}
        )
        self.assertEqual(
            json.loads(json.dumps(third_facts, sort_keys=True))["ShortageQty"],
            {"numerator": 1, "denominator": 3},
        )

        for value in _walk_values(projection):
            self.assertNotIsInstance(value, float)

    # --- 3 shortage vs recommended ----------------------------------------------------

    def test_q3_3_shortage_and_recommended_quantities_stay_distinct(self) -> None:
        recommendations, _built = self.complete_recommendations("q3-3")
        recommendation = recommendations.for_family(PLANT, DEMAND)
        assert recommendation is not None
        projection = build_q3_projection(recommendation)

        self.assertNotEqual(
            projection["facts"]["ShortageQty"],
            projection["facts"]["RecommendedPurchaseQty"],
        )
        self.assertEqual(projection["facts"]["ShortageQty"], {"numerator": 30, "denominator": 1})
        self.assertEqual(
            projection["facts"]["RecommendedPurchaseQty"], {"numerator": 100, "denominator": 1}
        )

        provider = RecordingProvider()
        result = explain_q3(recommendations, provider, plant_id=PLANT, material_code=DEMAND)
        response = result.response
        self.assertIsNotNone(response)
        assert response is not None
        shortage_evidence = [item for item in response.evidence if "ShortageQty = 30" in item]
        recommended_evidence = [
            item for item in response.evidence if "RecommendedPurchaseQty = 100" in item
        ]
        self.assertEqual(len(shortage_evidence), 1)
        self.assertEqual(len(recommended_evidence), 1)
        self.assertNotEqual(shortage_evidence[0], recommended_evidence[0])
        payload = json.dumps(result.to_dict(), ensure_ascii=False)
        self.assertIn('"ShortageQty": {"numerator": 30, "denominator": 1}', payload)
        self.assertIn('"RecommendedPurchaseQty": {"numerator": 100, "denominator": 1}', payload)

    # --- 4 projection scope -----------------------------------------------------------

    def test_q3_4_projection_excludes_package_and_unrelated_pipeline_fields(self) -> None:
        recommendations, built = self.complete_recommendations("q3-4")
        recommendation = recommendations.for_family(PLANT, DEMAND)
        assert recommendation is not None
        projection = build_q3_projection(recommendation)

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

        result = explain_q3(recommendations, provider, plant_id=PLANT, material_code=DEMAND)

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
        projection = build_q3_projection(recommendation)
        provider = RecordingProvider()

        result = explain_q3(recommendations, provider, plant_id=PLANT, material_code=DEMAND)

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

    # --- 7 response artifact ----------------------------------------------------------

    def test_q3_7_provider_response_becomes_the_response_artifact(self) -> None:
        recommendations, _built = self.complete_recommendations("q3-7")
        provider = RecordingProvider()

        result = explain_q3(recommendations, provider, plant_id=PLANT, material_code=DEMAND)

        response = result.response
        self.assertIsNotNone(response)
        assert response is not None
        self.assertEqual(set(response.to_dict()), set(RESPONSE_KEYS))
        self.assertEqual(response.answer, GOOD_RESPONSE["answer"])
        self.assertEqual(list(response.evidence), list(GOOD_RESPONSE["evidence"]))
        self.assertEqual(list(response.uncertainty), [])
        self.assertEqual(
            response.human_decision_required, GOOD_RESPONSE["human_decision_required"]
        )
        self.assertEqual(result.to_dict()["response"], response.to_dict())

        # A different provider implementation produces the same artifact shape.
        alternative = AlternativeProvider()
        other = explain_q3(recommendations, alternative, plant_id=PLANT, material_code=DEMAND)
        self.assertEqual(other.outcome, OUTCOME_EXPLAINED)
        assert other.response is not None
        self.assertEqual(set(other.response.to_dict()), set(RESPONSE_KEYS))
        self.assertIsNotNone(alternative.received)

    # --- 8/9 fail-closed: incomplete + valid absence ----------------------------------

    def test_q3_8_incomplete_recommendation_does_not_call_the_provider(self) -> None:
        recommendations, _built = self.incomplete_recommendations("q3-8")
        provider = RecordingProvider()

        result = explain_q3(recommendations, provider, plant_id=PLANT, material_code=DEMAND)

        self.assertEqual(provider.calls, [])
        self.assertFalse(result.provider_invoked)
        self.assertEqual(result.outcome, OUTCOME_RECOMMENDATION_INCOMPLETE)
        self.assertFalse(result.explained)
        self.assertIsNone(result.response)
        self.assertEqual(result.availability_note, NOTE_INCOMPLETE)
        self.assertEqual(
            result.projection["completeness"]["state"], COMPLETENESS_DATA_INCOMPLETE
        )

        # A reliable never-short horizon states no recommendation by design (§4.4.87).
        absence_built = self.build_chain(demands=((DEMAND, "10", D2),), name="q3-8-absence")
        absence = self.recommendations(absence_built)
        absence_provider = RecordingProvider()
        absence_result = explain_q3(
            absence, absence_provider, plant_id=PLANT, material_code=DEMAND
        )
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

        result = explain_q3(recommendations, provider, plant_id=PLANT, material_code=DEMAND)

        missing = result.projection["completeness"]["missing_facts"]
        self.assertIn("ApplicableMOQ", missing)
        for name in missing:
            self.assertIn(name, Q3_FACT_FIELDS)
            self.assertIsNone(result.projection["facts"][name])
        self.assertTrue(result.missing_evidence)
        payloads = json.dumps([dict(item) for item in result.missing_evidence], ensure_ascii=False)
        self.assertIn(recommendation.root_condition, payloads)
        self.assertIn("unavailable_facts", payloads)
        self.assertIn("unavailable_facts", json.dumps(result.to_dict(), ensure_ascii=False))
        self.assertIsNone(result.projection["completeness"]["valid_absence"])

    # --- 10 provider exception --------------------------------------------------------

    def test_q3_10_provider_exception_fails_closed(self) -> None:
        recommendations, _built = self.complete_recommendations("q3-10")
        before = recommendations.to_dict()
        provider = RecordingProvider(error=RuntimeError("leaked-provider-secret-sentinel"))

        result = explain_q3(recommendations, provider, plant_id=PLANT, material_code=DEMAND)

        self.assertEqual(len(provider.calls), 1)
        self.assertTrue(result.provider_invoked)
        self.assertEqual(result.outcome, OUTCOME_PROVIDER_UNAVAILABLE)
        self.assertIsNone(result.response)
        self.assertEqual(result.availability_note, NOTE_PROVIDER_UNAVAILABLE)
        payload = json.dumps(result.to_dict(), ensure_ascii=False)
        self.assertIn("RuntimeError", payload)
        self.assertNotIn("leaked-provider-secret-sentinel", payload)
        self.assertEqual(recommendations.to_dict(), before)

    # --- 11 malformed / unacceptable responses ----------------------------------------

    def test_q3_11_malformed_or_unacceptable_response_fails_closed(self) -> None:
        recommendations, _built = self.complete_recommendations("q3-11")
        echoed_projection = build_q3_projection(
            recommendations.for_family(PLANT, DEMAND)  # type: ignore[arg-type]
        )
        unacceptable: tuple[tuple[str, object], ...] = (
            ("not-a-mapping", "ShortageQty is 30"),
            ("missing-key", {k: v for k, v in GOOD_RESPONSE.items() if k != "evidence"}),
            ("extra-key", {**GOOD_RESPONSE, "RecommendedPurchaseQty": 100}),
            ("empty-answer", {**GOOD_RESPONSE, "answer": "   "}),
            ("empty-evidence", {**GOOD_RESPONSE, "evidence": []}),
            ("non-text-uncertainty", {**GOOD_RESPONSE, "uncertainty": 3}),
            ("empty-human-decision", {**GOOD_RESPONSE, "human_decision_required": ""}),
            ("blank-evidence-item", {**GOOD_RESPONSE, "evidence": ["ShortageQty = 30", "  "]}),
            ("projection-echo", echoed_projection),
        )
        for label, raw in unacceptable:
            with self.subTest(label=label):
                provider = RecordingProvider(response=raw)
                result = explain_q3(
                    recommendations, provider, plant_id=PLANT, material_code=DEMAND
                )
                self.assertEqual(len(provider.calls), 1)
                self.assertEqual(result.outcome, OUTCOME_RESPONSE_UNACCEPTABLE)
                self.assertIsNone(result.response)
                self.assertFalse(result.explained)
                self.assertEqual(result.availability_note, NOTE_RESPONSE_UNACCEPTABLE)
                self.assertIsNone(validate_provider_response(raw))

    # --- 12 deterministic result unchanged -------------------------------------------

    def test_q3_12_deterministic_recommendation_object_is_unchanged(self) -> None:
        recommendations, _built = self.complete_recommendations("q3-12")
        recommendation = recommendations.for_family(PLANT, DEMAND)
        assert recommendation is not None
        before_result = recommendations.to_dict()
        before_recommendation = recommendation.to_dict()

        explain_q3(recommendations, RecordingProvider(), plant_id=PLANT, material_code=DEMAND)
        explain_q3(
            recommendations, RecordingProvider(error=RuntimeError("boom")),
            plant_id=PLANT, material_code=DEMAND,
        )
        mutating = MutatingProvider()
        mutated = explain_q3(
            recommendations, mutating, plant_id=PLANT, material_code=DEMAND
        )

        self.assertEqual(recommendations.to_dict(), before_result)
        self.assertEqual(recommendation.to_dict(), before_recommendation)
        self.assertEqual(mutated.projection["question"], Q3_QUESTION)
        self.assertEqual(
            mutated.projection["facts"]["ShortageQty"], {"numerator": 30, "denominator": 1}
        )
        self.assertEqual(mutated.outcome, OUTCOME_EXPLAINED)

        incomplete, _ = self.incomplete_recommendations("q3-12-incomplete")
        before_incomplete = incomplete.to_dict()
        explain_q3(incomplete, RecordingProvider(), plant_id=PLANT, material_code=DEMAND)
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
            result = explain_q3(recommendations, provider, plant_id=PLANT, material_code=DEMAND)

        payload = json.dumps(result.to_dict(), ensure_ascii=False)
        projection_payload = json.dumps(provider.calls[0], ensure_ascii=False)
        response_payload = json.dumps(
            result.response.to_dict() if result.response else {}, ensure_ascii=False
        )
        for text in (payload, projection_payload, response_payload, stdout.getvalue(), stderr.getvalue()):
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
            "procurement_recommendation",
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
                    root = (node.module or "").split(".")[0]
                    self.assertIn(root, allowed_modules)
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

        first = build_q3_projection(recommendation)
        second = build_q3_projection(recommendation)
        self.assertEqual(first, second)
        self.assertEqual(
            json.dumps(first, sort_keys=True, ensure_ascii=False),
            json.dumps(second, sort_keys=True, ensure_ascii=False),
        )

        provider_one = RecordingProvider()
        provider_two = RecordingProvider()
        result_one = explain_q3(
            recommendations, provider_one, plant_id=PLANT, material_code=DEMAND
        )
        result_two = explain_q3(
            recommendations, provider_two, plant_id=PLANT, material_code=DEMAND
        )
        self.assertEqual(
            json.dumps(result_one.to_dict(), sort_keys=True, ensure_ascii=False),
            json.dumps(result_two.to_dict(), sort_keys=True, ensure_ascii=False),
        )
        self.assertIsNot(result_one.response, result_two.response)


if __name__ == "__main__":  # pragma: no cover - manual run entry point
    unittest.main()
