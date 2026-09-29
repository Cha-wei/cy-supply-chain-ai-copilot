"""DeepSeek hosted provider adapter (Q3 seam) -- offline tests with a stub transport.

The suite never touches the network and never uses a real credential: the adapter's HTTP
transport is injected, and the credential is supplied through a fake environment mapping or a
patched process environment.  The real ``StdlibHttpTransport`` is exercised only against
patched ``urllib`` entry points, so a transport failure is tested without any egress.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import unittest
import urllib.error
from unittest import mock

import snapshot_loader.deepseek_provider as adapter
from snapshot_loader import (
    ANSWER_KIND_LITERALS,
    HUMAN_DECISION_REQUIRED_TEXT,
    NOTE_PROVIDER_UNAVAILABLE,
    OUTCOME_EXPLAINED,
    OUTCOME_PROVIDER_UNAVAILABLE,
    Q3_FACT_FIELDS,
    RESPONSE_KEYS,
    build_q3_projection,
)
from tests.test_explanation_q3 import (
    EQUAL_KIND,
    FIXTURE_EVIDENCE,
    FIXTURE_KIND,
    GOOD_SELECTION,
)
from tests.test_shortage_calculation import DEMAND, PLANT
from tests.test_supplier_risk_input import SupplierRiskInputTestCase

#: A credential-shaped sentinel used to prove nothing leaks (never a real key).
CREDENTIAL_SENTINEL = "DEEPSEEK-SENTINEL-NOT-A-REAL-CREDENTIAL"

#: Keys a request body may carry; anything else would mean extra egress content.
REQUEST_KEYS = {"model", "instructions", "input", "text"}


def envelope(selection: object) -> bytes:
    """A Responses-style success envelope carrying ``selection`` as structured output."""

    return json.dumps(
        {
            "id": "SIMULATED-RESPONSE",
            "model": adapter.DEEPSEEK_MODEL,
            "status": "completed",
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {"type": "output_text", "text": json.dumps(selection, ensure_ascii=False)}
                    ],
                }
            ],
        },
        ensure_ascii=False,
    ).encode("utf-8")


def envelope_with_text(text: str) -> bytes:
    return json.dumps(
        {"status": "completed", "output": [{"content": [{"type": "output_text", "text": text}]}]}
    ).encode("utf-8")


class StubTransport:
    """A stub HTTP transport: records requests, returns a canned response or raises."""

    def __init__(
        self,
        response: adapter.HttpResponse | None = None,
        error: BaseException | None = None,
    ) -> None:
        self.requests: list[adapter.HttpRequest] = []
        self._response = response if response is not None else adapter.HttpResponse(200, envelope(GOOD_SELECTION))
        self._error = error

    def send(self, request: adapter.HttpRequest) -> adapter.HttpResponse:
        self.requests.append(request)
        if self._error is not None:
            raise self._error
        return self._response

    # --- helpers for assertions -----------------------------------------------------

    def body_json(self, index: int = 0) -> dict[str, object]:
        return json.loads(self.requests[index].body.decode("utf-8"))

    def headers(self, index: int = 0) -> dict[str, str]:
        return dict(self.requests[index].headers)

    def projection_in_request(self, index: int = 0) -> object:
        payload = self.body_json(index)
        input_items = payload["input"]
        assert isinstance(input_items, list)
        content = input_items[0]["content"]
        return json.loads(content[0]["text"])


class DeepSeekAdapterTests(SupplierRiskInputTestCase):
    """One real Q3 recommendation plus the adapter's injected transport."""

    def recommendations_for(self, name: str):
        built = self.build_chain(name=name)
        return self.recommendations(built), built

    def explain(self, recommendations, provider):
        from snapshot_loader import explain_q3

        return explain_q3(recommendations, provider, plant_id=PLANT, material_code=DEMAND)

    def provider(self, transport, *, environ=None, **kwargs):
        return adapter.provider_from_environment(
            environ={adapter.DEEPSEEK_API_KEY_ENV: CREDENTIAL_SENTINEL} if environ is None else environ,
            transport=transport,
            **kwargs,
        )

    # --- 1 missing credential ---------------------------------------------------------

    def test_d1_missing_credential_means_zero_egress(self) -> None:
        recommendations, _built = self.recommendations_for("d1")
        transport = StubTransport()

        provider = self.provider(transport, environ={})
        self.assertIsInstance(provider, adapter.UnavailableProvider)

        result = self.explain(recommendations, provider)

        self.assertEqual(transport.requests, [])
        # The injected provider *was* asked (the runtime calls the seam once) but it performs
        # no egress at all: the stub transport recorded nothing.
        self.assertTrue(result.provider_invoked)
        self.assertEqual(result.outcome, OUTCOME_PROVIDER_UNAVAILABLE)
        self.assertIsNone(result.response)
        self.assertEqual(result.availability_note, NOTE_PROVIDER_UNAVAILABLE)
        payload = json.dumps(result.to_dict(), ensure_ascii=False)
        self.assertNotIn(adapter.DEEPSEEK_API_KEY_ENV, payload)
        self.assertNotIn(CREDENTIAL_SENTINEL, payload)

    # --- 2 credential boundary --------------------------------------------------------

    def test_d2_credential_only_in_authorization_header(self) -> None:
        recommendations, _built = self.recommendations_for("d2")
        transport = StubTransport()
        provider = self.provider(transport)

        result = self.explain(recommendations, provider)

        self.assertEqual(result.outcome, OUTCOME_EXPLAINED)
        self.assertEqual(len(transport.requests), 1)
        headers = transport.headers()
        self.assertEqual(headers["Authorization"], f"Bearer {CREDENTIAL_SENTINEL}")
        self.assertNotIn(CREDENTIAL_SENTINEL, transport.requests[0].body.decode("utf-8"))
        self.assertNotIn(CREDENTIAL_SENTINEL, json.dumps(result.to_dict(), ensure_ascii=False))
        self.assertNotIn(CREDENTIAL_SENTINEL, repr(provider))
        self.assertNotIn("DEEPSEEK-SENTINEL", repr(provider))

    # --- 3/4/5 request egress ---------------------------------------------------------

    def test_d3_egress_contains_q3_projection_only(self) -> None:
        recommendations, built = self.recommendations_for("d3")
        transport = StubTransport()
        recommendation = recommendations.for_family(PLANT, DEMAND)
        assert recommendation is not None
        expected_projection = build_q3_projection(recommendation)

        self.explain(recommendations, self.provider(transport))

        request = transport.requests[0]
        self.assertEqual(request.method, "POST")
        body = transport.body_json()
        self.assertEqual(set(body), REQUEST_KEYS)
        self.assertEqual(transport.projection_in_request(), expected_projection)
        text = request.body.decode("utf-8")
        self.assertNotIn(built.accepted.package_id, text)
        self.assertNotIn(built.accepted.content_view_digest, text)
        self.assertNotIn("accepted_package", text)
        self.assertNotIn("Supplier Performance", text)
        self.assertNotIn("Inventory Snapshot", text)
        self.assertNotIn("analysis_run", text)

    def test_d4_model_is_deepseek_flash(self) -> None:
        recommendations, _built = self.recommendations_for("d4")
        transport = StubTransport()

        result = self.explain(recommendations, self.provider(transport))

        self.assertEqual(adapter.DEEPSEEK_MODEL, "deepseek-flash")
        self.assertEqual(transport.body_json()["model"], "deepseek-flash")
        self.assertEqual(result.__class__.__name__, "ExplanationResult")

    def test_d5_endpoint_is_responses(self) -> None:
        recommendations, _built = self.recommendations_for("d5")
        transport = StubTransport()

        self.explain(recommendations, self.provider(transport))

        self.assertEqual(adapter.DEEPSEEK_RESPONSES_PATH, "/responses")
        self.assertEqual(adapter.DEEPSEEK_BASE_URL, "https://api.deepseek.com")
        self.assertEqual(transport.requests[0].url, "https://api.deepseek.com/responses")

    # --- 6 schema consistency ---------------------------------------------------------

    def test_d6_schema_matches_existing_selection_vocabulary(self) -> None:
        recommendations, _built = self.recommendations_for("d6")
        transport = StubTransport()

        self.explain(recommendations, self.provider(transport))

        format_block = transport.body_json()["text"]["format"]
        self.assertEqual(format_block["type"], "json_schema")
        self.assertEqual(format_block["name"], adapter.SELECTION_SCHEMA_NAME)
        self.assertTrue(format_block["strict"])
        schema = format_block["schema"]
        self.assertEqual(schema["type"], "object")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["required"], list(RESPONSE_KEYS))
        self.assertEqual(schema["properties"]["answer_kind"]["enum"], list(ANSWER_KIND_LITERALS))
        evidence = schema["properties"]["evidence"]
        self.assertEqual(evidence["items"]["enum"], list(Q3_FACT_FIELDS))
        self.assertEqual(evidence["minItems"], len(Q3_FACT_FIELDS))
        self.assertEqual(evidence["maxItems"], len(Q3_FACT_FIELDS))
        self.assertEqual(schema["properties"]["uncertainty"]["maxItems"], 0)
        self.assertEqual(schema["properties"]["human_decision_required"]["enum"], [True])
        # The runtime validation stays the authority: the schema mirrors it, it does not
        # replace it (uncertainty is typed as an array of strings but capped at zero items).
        uncertainty = schema["properties"]["uncertainty"]
        self.assertEqual(uncertainty["type"], "array")
        self.assertEqual(uncertainty["items"]["type"], "string")
        self.assertEqual(uncertainty["maxItems"], 0)

    # --- 7 success path ---------------------------------------------------------------

    def test_d7_successful_envelope_reaches_explained(self) -> None:
        recommendations, _built = self.recommendations_for("d7")
        transport = StubTransport()

        result = self.explain(recommendations, self.provider(transport))

        self.assertEqual(result.outcome, OUTCOME_EXPLAINED)
        self.assertTrue(result.provider_invoked)
        self.assertTrue(result.explained)
        response = result.response
        assert response is not None
        self.assertIn("ShortageQty = 30", response.evidence)
        self.assertEqual(response.human_decision_required, HUMAN_DECISION_REQUIRED_TEXT)
        self.assertEqual(list(response.uncertainty), [])
        self.assertEqual(len(transport.requests), 1)

    # --- 8/9/10 status failures -------------------------------------------------------

    def test_d8_401_and_403_fail_closed(self) -> None:
        for status in (401, 403):
            with self.subTest(status=status):
                recommendations, _built = self.recommendations_for(f"d8-{status}")
                transport = StubTransport(adapter.HttpResponse(status, b'{"error":"nope"}'))
                result = self.explain(recommendations, self.provider(transport))
                self.assertEqual(result.outcome, OUTCOME_PROVIDER_UNAVAILABLE)
                self.assertIsNone(result.response)
                self.assertEqual(result.availability_note, NOTE_PROVIDER_UNAVAILABLE)
                self.assertEqual(len(transport.requests), 1)
                payload = json.dumps(result.to_dict(), ensure_ascii=False)
                self.assertNotIn(CREDENTIAL_SENTINEL, payload)
                self.assertNotIn("nope", payload)
                self.assertIn("ProviderUnavailable", payload)

    def test_d9_429_fail_closed(self) -> None:
        recommendations, _built = self.recommendations_for("d9")
        transport = StubTransport(adapter.HttpResponse(429, b'{"error":"rate limited"}'))
        result = self.explain(recommendations, self.provider(transport))
        self.assertEqual(result.outcome, OUTCOME_PROVIDER_UNAVAILABLE)
        self.assertIsNone(result.response)
        self.assertEqual(len(transport.requests), 1)
        self.assertNotIn("rate limited", json.dumps(result.to_dict(), ensure_ascii=False))

    def test_d10_5xx_fail_closed(self) -> None:
        for status in (500, 503):
            with self.subTest(status=status):
                recommendations, _built = self.recommendations_for(f"d10-{status}")
                transport = StubTransport(adapter.HttpResponse(status, b""))
                result = self.explain(recommendations, self.provider(transport))
                self.assertEqual(result.outcome, OUTCOME_PROVIDER_UNAVAILABLE)
                self.assertIsNone(result.response)
                self.assertEqual(len(transport.requests), 1)

    # --- 11 transport failures --------------------------------------------------------

    def test_d11_timeout_and_transport_exception_fail_closed(self) -> None:
        recommendations, _built = self.recommendations_for("d11")

        failing = StubTransport(error=adapter.ProviderUnavailable("the hosted provider could not be reached"))
        result = self.explain(recommendations, self.provider(failing))
        self.assertEqual(result.outcome, OUTCOME_PROVIDER_UNAVAILABLE)
        self.assertIsNone(result.response)
        self.assertEqual(len(failing.requests), 1)

        timing_out = StubTransport(error=TimeoutError("simulated timeout"))
        result = self.explain(recommendations, self.provider(timing_out))
        self.assertEqual(result.outcome, OUTCOME_PROVIDER_UNAVAILABLE)
        self.assertNotIn("simulated timeout", json.dumps(result.to_dict(), ensure_ascii=False))

        # The default stdlib transport maps transport-level failures to ProviderUnavailable,
        # and an HTTP error status to a response (so the adapter itself fails closed on it).
        transport = adapter.StdlibHttpTransport()
        request = adapter.HttpRequest(
            method="POST",
            url="https://api.deepseek.com/responses",
            headers=(("Authorization", f"Bearer {CREDENTIAL_SENTINEL}"),),
            body=b"{}",
            timeout=1.0,
        )
        with mock.patch.object(
            adapter.urllib.request, "urlopen", side_effect=urllib.error.URLError("dns failure")
        ):
            with self.assertRaises(adapter.ProviderUnavailable) as caught:
                transport.send(request)
        self.assertNotIn(CREDENTIAL_SENTINEL, str(caught.exception))
        self.assertNotIn("dns failure", str(caught.exception))

        with mock.patch.object(
            adapter.urllib.request,
            "urlopen",
            side_effect=urllib.error.HTTPError(
                request.url, 401, "Unauthorized", hdrs=None, fp=io.BytesIO(b'{"error":"no"}')
            ),
        ):
            response = transport.send(request)
        self.assertEqual(response.status, 401)
        self.assertNotIn(CREDENTIAL_SENTINEL, response.body.decode("utf-8"))

    # --- 12/13 envelope and JSON failures ---------------------------------------------

    def test_d12_malformed_envelope_fail_closed(self) -> None:
        variants: tuple[tuple[str, bytes], ...] = (
            ("not-an-object", b"[]"),
            ("no-output", b'{"status":"completed"}'),
            ("wrong-content-type", b'{"output":[{"content":[{"type":"text","text":"{}"}]}]}'),
            ("failed-status", b'{"status":"failed","output":[]}'),
            ("incomplete-status", b'{"status":"incomplete","output":[]}'),
            ("error-object", b'{"error":{"message":"boom"}}'),
            ("content-not-a-list", b'{"output":[{"content":"nope"}]}'),
            ("output-not-a-list", b'{"output":"nope"}'),
        )
        for label, body in variants:
            with self.subTest(label=label):
                recommendations, _built = self.recommendations_for(f"d12-{label}")
                transport = StubTransport(adapter.HttpResponse(200, body))
                result = self.explain(recommendations, self.provider(transport))
                self.assertEqual(result.outcome, OUTCOME_PROVIDER_UNAVAILABLE)
                self.assertIsNone(result.response)
                self.assertEqual(len(transport.requests), 1)

    def test_d13_invalid_json_fail_closed(self) -> None:
        variants: tuple[tuple[str, bytes], ...] = (
            ("envelope-not-json", b"not json at all"),
            ("envelope-broken-utf8", b"\xff\xfe\x00"),
            ("output-text-not-json", envelope_with_text("ShortageQty = 30")),
            ("output-text-is-a-list", envelope_with_text("[1, 2, 3]")),
        )
        for label, body in variants:
            with self.subTest(label=label):
                recommendations, _built = self.recommendations_for(f"d13-{label}")
                transport = StubTransport(adapter.HttpResponse(200, body))
                result = self.explain(recommendations, self.provider(transport))
                self.assertEqual(result.outcome, OUTCOME_PROVIDER_UNAVAILABLE)
                self.assertIsNone(result.response)

    # --- 14 validator stays the trust boundary ----------------------------------------

    def test_d14_schema_valid_but_business_invalid_still_rejected_by_validator(self) -> None:
        recommendations, _built = self.recommendations_for("d14")
        # Both selections would satisfy the JSON schema, but contradict the projection.
        invalid_selections: tuple[tuple[str, dict[str, object]], ...] = (
            ("relations-swapped", {**GOOD_SELECTION, "answer_kind": EQUAL_KIND}),
            (
                "evidence-missing-a-fact",
                {
                    **GOOD_SELECTION,
                    "evidence": [name for name in FIXTURE_EVIDENCE if name != "ApplicableMOQ"],
                },
            ),
        )
        for label, selection in invalid_selections:
            with self.subTest(label=label):
                transport = StubTransport(adapter.HttpResponse(200, envelope(selection)))
                result = self.explain(recommendations, self.provider(transport))
                self.assertEqual(len(transport.requests), 1)
                self.assertTrue(result.provider_invoked)
                self.assertEqual(result.outcome, "RESPONSE_UNACCEPTABLE")
                self.assertIsNone(result.response)

    # --- 15 secret sentinel -----------------------------------------------------------

    def test_d15_secret_sentinel_never_leaks(self) -> None:
        recommendations, _built = self.recommendations_for("d15")
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.dict(os.environ, {adapter.DEEPSEEK_API_KEY_ENV: CREDENTIAL_SENTINEL}):
            transport = StubTransport()
            provider = adapter.provider_from_environment(transport=transport)
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = self.explain(recommendations, provider)
            failing = StubTransport(adapter.HttpResponse(401, b"{}"))
            failed = self.explain(
                recommendations, adapter.provider_from_environment(transport=failing)
            )

        self.assertEqual(result.outcome, OUTCOME_EXPLAINED)
        self.assertEqual(failed.outcome, OUTCOME_PROVIDER_UNAVAILABLE)
        texts = (
            transport.requests[0].body.decode("utf-8"),
            json.dumps(transport.projection_in_request(), ensure_ascii=False),
            json.dumps(result.to_dict(), ensure_ascii=False),
            json.dumps(failed.to_dict(), ensure_ascii=False),
            stdout.getvalue(),
            stderr.getvalue(),
            repr(provider),
        )
        for text in texts:
            self.assertNotIn(CREDENTIAL_SENTINEL, text)
        self.assertNotIn(CREDENTIAL_SENTINEL, str(adapter.ProviderUnavailable("x")))

    # --- 16 exactly one call ----------------------------------------------------------

    def test_d16_provider_called_exactly_once(self) -> None:
        recommendations, _built = self.recommendations_for("d16")
        for label, response in (
            ("success", adapter.HttpResponse(200, envelope(GOOD_SELECTION))),
            ("rate-limited", adapter.HttpResponse(429, b"")),
            ("server-error", adapter.HttpResponse(500, b"")),
        ):
            with self.subTest(label=label):
                transport = StubTransport(response)
                self.explain(recommendations, self.provider(transport))
                self.assertEqual(len(transport.requests), 1)

    # --- 17 deterministic result unchanged --------------------------------------------

    def test_d17_deterministic_recommendation_unchanged(self) -> None:
        recommendations, _built = self.recommendations_for("d17")
        recommendation = recommendations.for_family(PLANT, DEMAND)
        assert recommendation is not None
        before_result = recommendations.to_dict()
        before_recommendation = recommendation.to_dict()

        self.explain(recommendations, self.provider(StubTransport()))
        self.explain(
            recommendations,
            self.provider(StubTransport(adapter.HttpResponse(401, b"{}"))),
        )
        self.explain(
            recommendations,
            self.provider(StubTransport(error=adapter.ProviderUnavailable("down"))),
        )
        self.explain(recommendations, self.provider(StubTransport(), environ={}))

        self.assertEqual(recommendations.to_dict(), before_result)
        self.assertEqual(recommendation.to_dict(), before_recommendation)


if __name__ == "__main__":  # pragma: no cover - manual run entry point
    unittest.main()
