"""Manual opt-in DeepSeek Q3 live smoke -- offline contract tests (no network, no real secret).

``scripts/deepseek_q3_live_smoke.py`` is the operator-facing live smoke of the **already
merged** hosted integration contract.  These tests pin its two hard properties:

1. **Opt-in boundary** -- importing the entry point performs no network I/O, the automatic suite
   never reaches the hosted provider, a missing credential is ``LIVE_SMOKE_READY_NOT_RUN`` with
   **zero** egress, and the credential cannot be supplied through the command line.
2. **Sanitized reporting** -- every failure mode becomes a ``LIVE_SMOKE_FAIL`` with a minimal
   category, and no credential, Authorization header, provider body or exception text can reach
   the report (``§7.1`` ``S-6`` ／ ``S-7`` ／ ``S-8`` ／ ``S-11``).

No test here performs a real network call, and no test here uses a real credential: the
transport is always injected and the credential value is a sentinel.  The entry point is loaded
from its path (it is a script, not an importable package module) and is exercised exactly as an
operator would invoke it, with a stub transport.
"""

from __future__ import annotations

import ast
import contextlib
import dataclasses
import importlib.util
import io
import json
import os
import sys
import unittest
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest import mock

import snapshot_loader.deepseek_provider as adapter
from snapshot_loader import (
    ANSWER_KIND_LITERALS,
    DEEPSEEK_API_KEY_ENV,
    HttpResponse,
    Q3_FACT_FIELDS,
    Q3_GRAIN_FIELDS,
    Q3_QUESTION,
    build_q3_projection,
    validate_provider_response,
)
from tests.test_deepseek_provider import (
    CREDENTIAL_SENTINEL,
    StubTransport,
    envelope,
    envelope_from_output,
    envelope_with_text,
)
from tests.test_explanation_q3 import (
    CREDENTIAL_KEYS,
    EQUAL_KIND,
    FIXTURE_EVIDENCE,
    FORBIDDEN_PROJECTION_KEYS,
    GOOD_SELECTION,
)
from tests.test_shortage_calculation import DEMAND, PLANT
from tests.test_supplier_risk_input import SupplierRiskInputTestCase

#: The opt-in entry point under test.
SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "deepseek_q3_live_smoke.py"

#: Fixed, caller-supplied evidence identifiers (so the report never shells out to ``git``).
FIXED_TIMESTAMP = "2026-09-29T00:00:00+00:00"
FIXED_SHA = "4dc6e07066dbcf1c47b7d42b1dd4bc07cd6feee2"

#: The complete, sanitized report surface (no request ／ response ／ header ／ error field).
REPORT_KEYS = {
    "status",
    "failure_category",
    "provider",
    "model",
    "endpoint",
    "request_count",
    "http_status",
    "selection_parsed",
    "validator_accepted",
    "answer_kind",
    "evidence_names",
    "uncertainty_empty",
    "human_decision_contract_ok",
    "synthetic_input_unchanged",
    "credential_not_leaked",
    "criteria_satisfied",
    "criteria_unsatisfied",
    "timestamp",
    "commit_sha",
    "notes",
}

#: Hostile canaries: provider bodies and exception messages that must never be echoed.
PROVIDER_BODY_CANARY = b'{"error": {"message": "LEAK-CANARY-PROVIDER-BODY"}}'
EXCEPTION_CANARY = "LEAK-CANARY-EXCEPTION-TEXT"
CANARIES = (CREDENTIAL_SENTINEL, "LEAK-CANARY", "Authorization", "Bearer", "input_text", "output_text")


def _load_smoke_module() -> ModuleType:
    """Load the entry point from its path (loading it must not perform network I/O)."""

    spec = importlib.util.spec_from_file_location("deepseek_q3_live_smoke", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


smoke = _load_smoke_module()


class _ProseProvider:
    """A hostile stand-in that answers with prose instead of a selection (defensive guard)."""

    def explain(self, projection: object) -> object:
        return "实际缺料 100，建议采购 100（LEAK-CANARY-PROSE）。"


class DeepSeekLiveSmokeTests(SupplierRiskInputTestCase):
    """The opt-in entry point driven through injected transports and fake environments."""

    # --- helpers ----------------------------------------------------------------------

    def report(
        self, transport: StubTransport | None = None, *, environ: object = None, **kwargs: Any
    ):
        environment = {DEEPSEEK_API_KEY_ENV: CREDENTIAL_SENTINEL} if environ is None else environ
        kwargs.setdefault("timestamp", FIXED_TIMESTAMP)
        kwargs.setdefault("commit_sha", FIXED_SHA)
        return smoke.run_live_smoke(
            environ=environment,
            transport=transport if transport is not None else StubTransport(),
            **kwargs,
        )

    def ok(self, selection: object) -> HttpResponse:
        return HttpResponse(200, envelope(selection))

    def serialized(self, report: Any) -> str:
        return (
            json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True)
            + "\n"
            + report.render_text()
        )

    def assert_no_canary(self, text: str) -> None:
        for canary in CANARIES:
            self.assertNotIn(canary, text)

    def assert_not_recorded(self, report: Any, value: str) -> None:
        """The value is not one of the report's own strings (exact, so a date prefix is fine)."""

        self.assertNotIn(value, smoke._report_strings(report.to_dict()))

    def shape(self, value: object) -> object:
        if isinstance(value, dict):
            return {key: self.shape(item) for key, item in sorted(value.items())}
        return type(value).__name__

    def nested_keys(self, value: object) -> set[str]:
        keys: set[str] = set()
        if isinstance(value, dict):
            for key, item in value.items():
                keys.add(key)
                keys |= self.nested_keys(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                keys |= self.nested_keys(item)
        return keys

    # --- 1-4 opt-in boundary and missing credential -----------------------------------

    def test_smoke_1_no_credential_is_ready_not_run_with_zero_egress(self) -> None:
        transport = StubTransport()

        report = self.report(transport, environ={})

        self.assertEqual(report.status, smoke.STATUS_NOT_RUN)
        self.assertEqual(report.failure_category, smoke.CATEGORY_CREDENTIAL_NOT_CONFIGURED)
        self.assertEqual(report.request_count, 0)
        self.assertEqual(transport.requests, [])
        self.assertIsNone(report.http_status)
        self.assertFalse(report.selection_parsed)
        self.assertFalse(report.validator_accepted)
        self.assertIsNone(report.answer_kind)
        self.assertEqual(report.evidence_names, ())
        self.assertTrue(report.synthetic_input_unchanged)
        self.assertTrue(report.credential_not_leaked)
        self.assertEqual(report.criteria_satisfied, ())
        self.assertEqual(report.notes, (smoke.NOTE_CREDENTIAL_NOT_CONFIGURED,))
        self.assertEqual(smoke._unsanitized_strings(report), ())
        self.assert_no_canary(self.serialized(report))

    def test_smoke_2_a_blank_credential_also_fails_closed_before_egress(self) -> None:
        for blank in ("", "   ", "\t", "\n"):
            with self.subTest(operand=repr(blank)):
                transport = StubTransport()

                report = self.report(transport, environ={DEEPSEEK_API_KEY_ENV: blank})

                self.assertEqual(report.status, smoke.STATUS_NOT_RUN)
                self.assertEqual(report.failure_category, smoke.CATEGORY_CREDENTIAL_NOT_CONFIGURED)
                self.assertEqual(transport.requests, [])

    def test_smoke_3_the_import_and_the_cli_touch_no_network_without_a_credential(self) -> None:
        environment = {key: value for key, value in os.environ.items() if key != DEEPSEEK_API_KEY_ENV}
        stdout, stderr = io.StringIO(), io.StringIO()

        with mock.patch.dict(os.environ, environment, clear=True), mock.patch(
            "urllib.request.urlopen", side_effect=AssertionError("no egress in this test")
        ) as urlopen, contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = smoke.main(["--json"])

        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], smoke.STATUS_NOT_RUN)
        self.assertEqual(payload["failure_category"], smoke.CATEGORY_CREDENTIAL_NOT_CONFIGURED)
        self.assertEqual(payload["request_count"], 0)
        urlopen.assert_not_called()
        # the env var name and the credential value are never printed
        self.assertNotIn(DEEPSEEK_API_KEY_ENV, stdout.getvalue() + stderr.getvalue())
        self.assert_no_canary(stdout.getvalue() + stderr.getvalue())

    def test_smoke_4_the_credential_cannot_be_passed_on_the_command_line(self) -> None:
        help_text = io.StringIO()
        with contextlib.redirect_stdout(help_text), self.assertRaises(SystemExit) as caught:
            smoke.main(["--help"])
        self.assertEqual(caught.exception.code, 0)
        for option in ("api-key", "apikey", "token", "secret"):
            self.assertNotIn(option, help_text.getvalue())

        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                smoke.main(["--api-key", CREDENTIAL_SENTINEL])
        self.assertEqual(caught.exception.code, 2)

    # --- 5-6 the passing path ---------------------------------------------------------

    def test_smoke_5_a_passing_run_sends_one_request_and_satisfies_every_criterion(self) -> None:
        transport = StubTransport()

        report = self.report(transport)

        self.assertEqual(report.status, smoke.STATUS_PASS)
        self.assertIsNone(report.failure_category)
        self.assertEqual(report.request_count, 1)
        self.assertEqual(len(transport.requests), 1)
        self.assertEqual(report.http_status, 200)
        self.assertTrue(report.selection_parsed)
        self.assertTrue(report.validator_accepted)
        self.assertEqual(report.answer_kind, smoke.EXPECTED_ANSWER_KIND)
        self.assertEqual(set(report.evidence_names), set(Q3_FACT_FIELDS))
        self.assertTrue(report.uncertainty_empty)
        self.assertTrue(report.human_decision_contract_ok)
        self.assertTrue(report.synthetic_input_unchanged)
        self.assertTrue(report.credential_not_leaked)
        self.assertEqual(set(report.criteria_satisfied), set(smoke.PASS_CRITERIA))
        self.assertEqual(report.criteria_unsatisfied, ())
        self.assertEqual(report.notes, (smoke.NOTE_PASS,))
        self.assertEqual(report.timestamp, FIXED_TIMESTAMP)
        self.assertEqual(report.commit_sha, FIXED_SHA)
        self.assertEqual(smoke._unsanitized_strings(report), ())
        self.assertEqual(set(report.to_dict()), REPORT_KEYS)
        self.assertEqual(self.nested_keys(report.to_dict()) & CREDENTIAL_KEYS, set())
        self.assert_no_canary(self.serialized(report))

        # The request carried exactly the fixed synthetic projection, and the sentinel appears
        # only in the transport boundary -- never in the report.
        self.assertEqual(transport.projection_in_request(0), smoke.synthetic_q3_projection())
        self.assertEqual(transport.headers(0).get("Authorization"), f"Bearer {CREDENTIAL_SENTINEL}")

    def test_smoke_6_evidence_order_does_not_change_the_outcome(self) -> None:
        reversed_selection = {**GOOD_SELECTION, "evidence": list(reversed(FIXTURE_EVIDENCE))}

        report = self.report(StubTransport(response=self.ok(reversed_selection)))

        self.assertEqual(report.status, smoke.STATUS_PASS)
        self.assertEqual(set(report.evidence_names), set(Q3_FACT_FIELDS))
        self.assertEqual(report.criteria_unsatisfied, ())

    # --- 7-10 failures are sanitized and never retried --------------------------------

    def test_smoke_7_http_failures_map_to_minimal_categories_without_retry(self) -> None:
        cases = (
            ("credential-rejected-401", 401, smoke.CATEGORY_CREDENTIAL_REJECTED),
            ("credential-rejected-403", 403, smoke.CATEGORY_CREDENTIAL_REJECTED),
            ("rate-limited-429", 429, smoke.CATEGORY_RATE_LIMITED),
            ("server-error-500", 500, smoke.CATEGORY_PROVIDER_SERVER_ERROR),
            ("server-error-503", 503, smoke.CATEGORY_PROVIDER_SERVER_ERROR),
            ("unexpected-status-204", 204, smoke.CATEGORY_UNEXPECTED_HTTP_STATUS),
            ("unexpected-status-302", 302, smoke.CATEGORY_UNEXPECTED_HTTP_STATUS),
        )
        for name, status, category in cases:
            with self.subTest(case=name):
                transport = StubTransport(response=HttpResponse(status, PROVIDER_BODY_CANARY))

                report = self.report(transport)

                self.assertEqual(report.status, smoke.STATUS_FAIL)
                self.assertEqual(report.failure_category, category)
                self.assertEqual(report.request_count, 1)
                self.assertEqual(len(transport.requests), 1)
                self.assertEqual(report.http_status, status)
                self.assertFalse(report.selection_parsed)
                self.assertFalse(report.validator_accepted)
                self.assertIsNone(report.answer_kind)
                self.assertEqual(report.criteria_satisfied, ())
                self.assertEqual(report.notes, (smoke.NOTE_PROVIDER_FAILED,))
                self.assertTrue(report.credential_not_leaked)
                self.assertEqual(smoke._unsanitized_strings(report), ())
                self.assert_no_canary(self.serialized(report))

    def test_smoke_8_transport_and_unexpected_failures_are_sanitized(self) -> None:
        cases = (
            ("provider-unavailable", adapter.ProviderUnavailable(EXCEPTION_CANARY), smoke.NOTE_PROVIDER_FAILED),
            ("unexpected-error", RuntimeError(EXCEPTION_CANARY), smoke.NOTE_UNEXPECTED_FAILURE),
        )
        for name, error, note in cases:
            with self.subTest(case=name):
                transport = StubTransport(error=error)

                report = self.report(transport)

                self.assertEqual(report.status, smoke.STATUS_FAIL)
                self.assertEqual(report.failure_category, smoke.CATEGORY_TRANSPORT_FAILURE)
                self.assertEqual(report.request_count, 1)
                self.assertEqual(len(transport.requests), 1)
                self.assertIsNone(report.http_status)
                self.assertEqual(report.notes, (note,))
                self.assertTrue(report.credential_not_leaked)
                self.assert_no_canary(self.serialized(report))

    def test_smoke_9_unusable_envelopes_fail_closed_without_echoing_the_body(self) -> None:
        cases = (
            ("status-not-completed", envelope_from_output([], status="incomplete")),
            ("no-output", envelope_from_output([])),
            ("prose-output", envelope_with_text("实际缺料 100，建议采购 100。")),
            ("output-not-json", b"<html>LEAK-CANARY</html>"),
            ("envelope-not-an-object", b'["LEAK-CANARY"]'),
            ("provider-error", PROVIDER_BODY_CANARY),
            ("missing-status-field", b'{"output": [], "LEAK-CANARY": true}'),
        )
        for name, body in cases:
            with self.subTest(case=name):
                transport = StubTransport(response=HttpResponse(200, body))

                report = self.report(transport)

                self.assertEqual(report.status, smoke.STATUS_FAIL)
                self.assertEqual(report.failure_category, smoke.CATEGORY_UNEXPECTED_ENVELOPE)
                self.assertEqual(report.request_count, 1)
                self.assertEqual(report.http_status, 200)
                self.assertTrue(report.credential_not_leaked)
                self.assert_no_canary(self.serialized(report))

    def test_smoke_10_a_prose_answer_is_failed_closed_even_if_an_adapter_returned_it(self) -> None:
        with mock.patch.object(smoke, "provider_from_environment", return_value=_ProseProvider()):
            report = self.report(StubTransport())

        self.assertEqual(report.status, smoke.STATUS_FAIL)
        self.assertEqual(report.failure_category, smoke.CATEGORY_UNEXPECTED_ENVELOPE)
        self.assertEqual(report.request_count, 0)
        self.assertFalse(report.selection_parsed)
        self.assertFalse(report.validator_accepted)
        self.assert_no_canary(self.serialized(report))

    # --- 11-12 validator rejection ----------------------------------------------------

    def test_smoke_11_a_selection_contradicting_the_synthetic_relation_is_rejected(self) -> None:
        equal = {**GOOD_SELECTION, "answer_kind": EQUAL_KIND}

        report = self.report(StubTransport(response=self.ok(equal)))

        self.assertEqual(report.status, smoke.STATUS_FAIL)
        self.assertEqual(report.failure_category, smoke.CATEGORY_VALIDATOR_REJECTED)
        self.assertEqual(report.request_count, 1)
        self.assertEqual(report.http_status, 200)
        self.assertTrue(report.selection_parsed)
        self.assertFalse(report.validator_accepted)
        self.assertEqual(report.answer_kind, EQUAL_KIND)
        self.assertEqual(report.evidence_names, ())
        self.assertEqual(report.notes, (smoke.NOTE_VALIDATOR_REJECTED,))
        self.assertTrue(report.credential_not_leaked)
        self.assert_no_canary(self.serialized(report))

    def test_smoke_12_other_unusable_selections_are_rejected_without_echo(self) -> None:
        cases = (
            ("invented-uncertainty", {**GOOD_SELECTION, "uncertainty": ["ShortageQty"]}),
            ("missing-required-fact", {**GOOD_SELECTION, "evidence": list(FIXTURE_EVIDENCE[:-1])}),
            ("invented-answer-kind", {**GOOD_SELECTION, "answer_kind": "SUPPLIER_PRICE_INCREASE"}),
            ("decision-not-required", {**GOOD_SELECTION, "human_decision_required": False}),
            ("extra-prose-key", {**GOOD_SELECTION, "reason": "LEAK-CANARY 供应商涨价 20%"}),
        )
        for name, selection in cases:
            with self.subTest(case=name):
                report = self.report(StubTransport(response=self.ok(selection)))

                self.assertEqual(report.status, smoke.STATUS_FAIL)
                self.assertEqual(report.failure_category, smoke.CATEGORY_VALIDATOR_REJECTED)
                self.assertEqual(report.request_count, 1)
                self.assertFalse(report.validator_accepted)
                self.assert_no_canary(self.serialized(report))

    # --- 13-14 the criterion and sanitization gates -----------------------------------

    def test_smoke_13_an_unsatisfied_criterion_withholds_the_pass(self) -> None:
        extended = (*smoke.PASS_CRITERIA, "always-unsatisfied")
        with mock.patch.object(smoke, "PASS_CRITERIA", extended), mock.patch.object(
            smoke, "_PERMITTED_REPORT_TEXTS", smoke._PERMITTED_REPORT_TEXTS | {"always-unsatisfied"}
        ):
            report = self.report(StubTransport())
            unsatisfied = report.criteria_unsatisfied
            satisfied = set(report.criteria_satisfied)

        self.assertEqual(unsatisfied, ("always-unsatisfied",))
        self.assertEqual(satisfied, set(smoke.PASS_CRITERIA))
        self.assertEqual(report.status, smoke.STATUS_FAIL)
        self.assertEqual(report.failure_category, smoke.CATEGORY_CRITERION_FAILED)
        self.assertEqual(report.notes, (smoke.NOTE_CRITERIA_UNSATISFIED,))

    def test_smoke_14_a_foreign_report_string_withholds_the_run(self) -> None:
        with mock.patch.object(smoke, "NOTE_PASS", EXCEPTION_CANARY):
            report = self.report(StubTransport())
            unsatisfied = report.criteria_unsatisfied

        self.assertEqual(report.status, smoke.STATUS_FAIL)
        self.assertEqual(report.failure_category, smoke.CATEGORY_UNSANITIZED_REPORT)
        self.assertEqual(len(unsatisfied), len(smoke.PASS_CRITERIA))
        self.assertEqual(report.notes, (smoke.NOTE_UNSANITIZED_REPORT,))
        # The fallback is rebuilt from fixed vocabulary only: it drops the dynamic provider
        # (answer kind / evidence) and caller (commit / timestamp) strings entirely, so the
        # surfaced report cannot keep carrying whatever the check just rejected.
        self.assertIsNone(report.answer_kind)
        self.assertEqual(report.evidence_names, ())
        self.assertEqual(report.commit_sha, "UNKNOWN")
        self.assertNotEqual(report.timestamp, FIXED_TIMESTAMP)
        self.assertIsNotNone(smoke._safe_timestamp(report.timestamp))
        self.assertFalse(report.selection_parsed)
        self.assertFalse(report.validator_accepted)
        self.assertEqual(report.criteria_satisfied, ())
        # The surfaced report is itself clean.
        self.assertTrue(report.credential_not_leaked)
        self.assertEqual(smoke._unsanitized_strings(report), ())
        self.assert_no_canary(self.serialized(report))

    # --- 15-16 the synthetic data boundary --------------------------------------------

    def test_smoke_15_the_synthetic_projection_carries_only_the_registered_scope(self) -> None:
        projection = smoke.synthetic_q3_projection()

        self.assertEqual(set(projection), {"question", "grain", "facts", "completeness"})
        self.assertEqual(projection["question"], Q3_QUESTION)
        self.assertEqual(set(projection["grain"]), set(Q3_GRAIN_FIELDS))
        self.assertEqual(set(projection["facts"]), set(Q3_FACT_FIELDS))
        self.assertEqual(projection["completeness"]["state"], "COMPLETE")
        self.assertEqual(projection["completeness"]["missing_facts"], [])
        self.assertEqual(self.nested_keys(projection) & FORBIDDEN_PROJECTION_KEYS, set())
        self.assertTrue(smoke.SIMULATED_PLANT_ID.startswith("SIM-"))
        self.assertTrue(smoke.SIMULATED_MATERIAL_CODE.startswith("SIM-"))
        self.assertEqual(projection["grain"]["plant_id"], smoke.SIMULATED_PLANT_ID)
        self.assertEqual(projection["grain"]["material_code"], smoke.SIMULATED_MATERIAL_CODE)
        simulated_grain = [
            smoke.SIMULATED_PLANT_ID,
            smoke.SIMULATED_MATERIAL_CODE,
            smoke.SIMULATED_NEED_DATE,
        ]
        for reference in ("shortage_reference", "policy_input_reference"):
            with self.subTest(reference=reference):
                self.assertEqual(projection["completeness"][reference]["grain"], simulated_grain)

        serialized = json.dumps(projection, ensure_ascii=False, sort_keys=True)
        for marker in (
            "AnalysisRun",
            "analysis_run",
            "content_view",
            "digest",
            "sha256",
            "snapshot_package_id",
            "evidence_classification",
        ):
            self.assertNotIn(marker, serialized)

        # A fresh copy per call, and repeatable: the smoke can never mutate its own fixture.
        self.assertEqual(smoke.synthetic_q3_projection(), projection)
        mutated = smoke.synthetic_q3_projection()
        mutated["facts"]["ShortageQty"] = {"numerator": 100, "denominator": 1}
        self.assertEqual(smoke.synthetic_q3_projection(), projection)

    def test_smoke_16_the_synthetic_projection_matches_the_runtime_projection(self) -> None:
        built = self.build_chain(name="smoke-16")
        recommendations = self.recommendations(built)
        recommendation = recommendations.for_family(PLANT, DEMAND)
        assert recommendation is not None

        runtime = build_q3_projection(recommendation)
        synthetic = smoke.synthetic_q3_projection()

        # Identical shape and identical projected quantities (the registered §5.3 relation),
        # with deliberately different (SIMULATED) identities.
        self.assertEqual(self.shape(synthetic), self.shape(runtime))
        self.assertEqual(synthetic["facts"], runtime["facts"])
        self.assertEqual(
            runtime["completeness"]["state"], synthetic["completeness"]["state"]
        )
        self.assertNotEqual(synthetic["grain"], runtime["grain"])
        for name in Q3_FACT_FIELDS:
            with self.subTest(fact=name):
                self.assertIs(type(synthetic["facts"][name]), type(runtime["facts"][name]))

        # Exactly one registered answer kind is consistent with the fixed numbers, so the smoke's
        # expectation is grounded in the registry rather than in a hand-picked literal.
        accepted = [
            literal
            for literal in ANSWER_KIND_LITERALS
            if validate_provider_response({**GOOD_SELECTION, "answer_kind": literal}, synthetic)
            is not None
        ]
        self.assertEqual(accepted, [smoke.EXPECTED_ANSWER_KIND])
        self.assertEqual(set(ANSWER_KIND_LITERALS), {smoke.EXPECTED_ANSWER_KIND, EQUAL_KIND})

    # --- 17-19 the thin-boundary and CLI contract -------------------------------------

    def test_smoke_17_the_entry_point_keeps_the_thin_boundary(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        allowed_modules = {
            "__future__",
            "argparse",
            "collections",
            "copy",
            "dataclasses",
            "datetime",
            "json",
            "os",
            "pathlib",
            "re",
            "snapshot_loader",
            "sys",
            "typing",
        }
        imported: set[str] = set()
        attributes: set[str] = set()
        names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                imported.add((node.module or "").split(".")[0])
            elif isinstance(node, ast.Attribute):
                attributes.add(node.attr)
            elif isinstance(node, ast.Name):
                names.add(node.id)

        self.assertEqual(imported - allowed_modules, set(), msg="unexpected import")
        # No HTTP client, no provider SDK, no subprocess and no own parser ／ validator.
        self.assertEqual(
            attributes & {"urlopen", "Request", "HTTPError", "URLError", "Popen", "run", "check_output"},
            set(),
        )
        self.assertEqual(names & {"subprocess", "socket", "ssl", "http", "urllib"}, set())
        self.assertEqual(names & {"DeepSeekProvider", "selection_json_schema", "INSTRUCTIONS"}, set())
        # The credential is resolved only by the merged composition boundary: the entry point
        # neither names the credential variable nor ever builds an Authorization header.
        self.assertNotIn("DEEPSEEK_API_KEY", source)
        self.assertNotIn("Authorization", source)
        self.assertNotIn("api_key", source)

    def test_smoke_18_the_cli_exits_nonzero_on_failure_and_records_the_sha(self) -> None:
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, {DEEPSEEK_API_KEY_ENV: CREDENTIAL_SENTINEL}, clear=True), mock.patch.object(
            smoke,
            "StdlibHttpTransport",
            lambda: StubTransport(response=HttpResponse(503, PROVIDER_BODY_CANARY)),
        ), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = smoke.main(["--json", "--commit-sha", FIXED_SHA])

        self.assertEqual(code, 1)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], smoke.STATUS_FAIL)
        self.assertEqual(payload["failure_category"], smoke.CATEGORY_PROVIDER_SERVER_ERROR)
        self.assertEqual(payload["commit_sha"], FIXED_SHA)
        self.assertEqual(payload["request_count"], 1)
        self.assertEqual(set(payload), REPORT_KEYS)
        self.assertIn("SIMULATED", stderr.getvalue())
        self.assert_no_canary(stdout.getvalue() + stderr.getvalue())

    def test_smoke_19_the_default_cli_prints_the_text_report(self) -> None:
        environment = {key: value for key, value in os.environ.items() if key != DEEPSEEK_API_KEY_ENV}
        stdout = io.StringIO()
        with mock.patch.dict(os.environ, environment, clear=True), contextlib.redirect_stdout(
            stdout
        ), contextlib.redirect_stderr(io.StringIO()):
            code = smoke.main([])

        self.assertEqual(code, 0)
        text = stdout.getvalue()
        self.assertIn(smoke.STATUS_NOT_RUN, text)
        self.assertIn("credential safe  : True", text)
        self.assertIn("requests         : 0", text)
        self.assert_no_canary(text)

    # --- 21-28 provider- and caller-controlled strings cannot enter the report -------------

    def test_smoke_21_an_unregistered_answer_kind_is_never_recorded(self) -> None:
        unregistered = "LEAK-CANARY-UNREGISTERED-KIND"

        transport = StubTransport(
            response=self.ok({**GOOD_SELECTION, "answer_kind": unregistered})
        )
        report = self.report(transport)

        self.assertEqual(report.status, smoke.STATUS_FAIL)
        self.assertEqual(report.failure_category, smoke.CATEGORY_VALIDATOR_REJECTED)
        self.assertEqual(report.request_count, 1)
        self.assertIsNone(report.answer_kind)
        self.assertTrue(report.credential_not_leaked)
        self.assertEqual(smoke._unsanitized_strings(report), ())
        self.assert_no_canary(self.serialized(report))
        self.assertNotIn(unregistered, self.serialized(report))

    def test_smoke_22_a_credential_like_answer_kind_is_never_recorded(self) -> None:
        cases = (
            ("credential-sentinel", CREDENTIAL_SENTINEL),
            ("bearer-shaped", f"Bearer {CREDENTIAL_SENTINEL}"),
            ("header-shaped", "Authorization: Bearer LEAK-CANARY"),
            ("free-prose", "实际缺料 100，建议采购 100（LEAK-CANARY）。"),
        )
        for name, answer_kind in cases:
            with self.subTest(case=name):
                transport = StubTransport(
                    response=self.ok({**GOOD_SELECTION, "answer_kind": answer_kind})
                )

                report = self.report(transport)

                self.assertEqual(report.status, smoke.STATUS_FAIL)
                self.assertEqual(report.failure_category, smoke.CATEGORY_VALIDATOR_REJECTED)
                self.assertIsNone(report.answer_kind)
                self.assertFalse(report.validator_accepted)
                self.assertTrue(report.credential_not_leaked)
                serialized = self.serialized(report)
                self.assertNotIn(answer_kind, serialized)
                self.assert_no_canary(serialized)

    def test_smoke_23_invalid_commit_metadata_is_rejected_before_any_egress(self) -> None:
        canary = f"{CREDENTIAL_SENTINEL}; rm -rf /"

        with mock.patch.object(
            smoke, "provider_from_environment", side_effect=AssertionError("no credential read")
        ), mock.patch(
            "urllib.request.urlopen", side_effect=AssertionError("no egress in this test")
        ) as urlopen:
            report = self.report(StubTransport(), commit_sha=canary)

        urlopen.assert_not_called()
        self.assertEqual(report.status, smoke.STATUS_FAIL)
        self.assertEqual(report.failure_category, smoke.CATEGORY_INVALID_METADATA)
        self.assertEqual(report.request_count, 0)
        self.assertEqual(report.commit_sha, "UNKNOWN")
        self.assertIsNotNone(smoke._safe_timestamp(report.timestamp))
        self.assertTrue(report.credential_not_leaked)
        self.assertEqual(report.notes, (smoke.NOTE_INVALID_METADATA,))
        self.assert_not_recorded(report, canary)
        self.assert_no_canary(self.serialized(report))

    def test_smoke_24_invalid_commit_metadata_is_never_echoed_by_the_cli(self) -> None:
        canary = f"{CREDENTIAL_SENTINEL}-NOT-A-SHA"
        stdout, stderr = io.StringIO(), io.StringIO()

        with mock.patch.dict(
            os.environ, {DEEPSEEK_API_KEY_ENV: CREDENTIAL_SENTINEL}, clear=True
        ), mock.patch(
            "urllib.request.urlopen", side_effect=AssertionError("no egress in this test")
        ) as urlopen, contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = smoke.main(["--json", "--commit-sha", canary])

        urlopen.assert_not_called()
        self.assertEqual(code, 1)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], smoke.STATUS_FAIL)
        self.assertEqual(payload["failure_category"], smoke.CATEGORY_INVALID_METADATA)
        self.assertEqual(payload["commit_sha"], "UNKNOWN")
        self.assertEqual(payload["request_count"], 0)
        self.assertEqual(set(payload), REPORT_KEYS)
        self.assertNotIn(canary, stdout.getvalue() + stderr.getvalue())
        self.assert_no_canary(stdout.getvalue() + stderr.getvalue())

    def test_smoke_25_only_safe_commit_identifiers_are_recorded(self) -> None:
        accepted = (
            "UNKNOWN",
            FIXED_SHA,
            FIXED_SHA[:7],
            FIXED_SHA[:4],
            FIXED_SHA.upper(),
        )
        for value in accepted:
            with self.subTest(case=f"accepted:{value}"):
                report = self.report(StubTransport(), commit_sha=value)

                self.assertEqual(report.status, smoke.STATUS_PASS)
                self.assertEqual(report.commit_sha, value)

        rejected = (
            "",
            "   ",
            "xyz",
            "abc",
            FIXED_SHA + "0",
            f"{FIXED_SHA} ",
            "HEAD",
            "refs/heads/main",
            "../../etc/passwd",
            CREDENTIAL_SENTINEL,
            "0123456789abcdef" * 5,
            "deadbeef; rm -rf /",
        )
        for value in rejected:
            with self.subTest(case=f"rejected:{value!r}"):
                report = self.report(StubTransport(), commit_sha=value)

                self.assertEqual(report.status, smoke.STATUS_FAIL)
                self.assertEqual(report.failure_category, smoke.CATEGORY_INVALID_METADATA)
                self.assertEqual(report.commit_sha, "UNKNOWN")
                self.assertEqual(report.request_count, 0)
                self.assertEqual(report.criteria_satisfied, ())
                self.assertTrue(report.credential_not_leaked)
                self.assert_not_recorded(report, value)

    def test_smoke_26_an_invalid_injected_timestamp_cannot_enter_the_report(self) -> None:
        for value in (
            EXCEPTION_CANARY,
            "2026-09-29",
            "2026-09-29T00:00:00",
            "not-a-date",
            "2026-13-45T99:99:99+00:00",
            CREDENTIAL_SENTINEL,
        ):
            with self.subTest(case=value):
                report = self.report(StubTransport(), timestamp=value)

                self.assertEqual(report.status, smoke.STATUS_FAIL)
                self.assertEqual(report.failure_category, smoke.CATEGORY_INVALID_METADATA)
                self.assertEqual(report.request_count, 0)
                self.assertEqual(report.notes, (smoke.NOTE_INVALID_METADATA,))
                self.assertNotEqual(report.timestamp, value)
                self.assertIsNotNone(smoke._safe_timestamp(report.timestamp))
                self.assertTrue(report.credential_not_leaked)
                self.assert_not_recorded(report, value)
                self.assert_no_canary(self.serialized(report))

        # A valid injected timestamp (the test surface) is still recorded verbatim.
        recorded = self.report(StubTransport(), timestamp=FIXED_TIMESTAMP)
        self.assertEqual(recorded.status, smoke.STATUS_PASS)
        self.assertEqual(recorded.timestamp, FIXED_TIMESTAMP)

    def test_smoke_27_the_cli_shape_check_strings_are_sanitized(self) -> None:
        self.assertEqual(smoke._safe_commit_sha("UNKNOWN"), "UNKNOWN")
        self.assertEqual(smoke._safe_commit_sha(FIXED_SHA), FIXED_SHA)
        self.assertIsNone(smoke._safe_commit_sha(None))
        self.assertIsNone(smoke._safe_commit_sha(12345))
        self.assertIsNone(smoke._safe_commit_sha(EXCEPTION_CANARY))
        self.assertEqual(smoke._safe_timestamp(FIXED_TIMESTAMP), FIXED_TIMESTAMP)
        self.assertEqual(
            smoke._safe_timestamp("2026-09-29T00:00:00.123456Z"),
            "2026-09-29T00:00:00.123456Z",
        )
        self.assertIsNone(smoke._safe_timestamp(EXCEPTION_CANARY))
        self.assertIsNone(smoke._safe_timestamp(None))
        self.assertIsNotNone(smoke._safe_timestamp(smoke._generated_timestamp()))

    def test_smoke_28_the_sanitizer_validates_dynamic_fields_instead_of_trusting_them(
        self,
    ) -> None:
        clean = self.report(StubTransport())
        self.assertTrue(clean.credential_not_leaked)
        self.assertEqual(smoke._unsanitized_strings(clean), ())

        # Every dynamic field the report carries is *validated*, never trusted into the allowlist:
        # an unregistered answer kind, an unregistered evidence name and unsafe caller metadata
        # are all detected even though the report "carries" them.
        contaminated = dataclasses.replace(
            clean,
            answer_kind=EXCEPTION_CANARY,
            evidence_names=(EXCEPTION_CANARY,),
            commit_sha=EXCEPTION_CANARY,
            timestamp=EXCEPTION_CANARY,
        )
        self.assertEqual(set(smoke._unsanitized_strings(contaminated)), {EXCEPTION_CANARY})

        # A registered answer kind and a registered evidence name are still permitted.
        registered = dataclasses.replace(
            clean, answer_kind=smoke.EXPECTED_ANSWER_KIND, evidence_names=tuple(Q3_FACT_FIELDS)
        )
        self.assertEqual(smoke._unsanitized_strings(registered), ())

    def test_smoke_20_the_suite_path_never_reaches_the_network(self) -> None:
        with mock.patch(
            "urllib.request.urlopen", side_effect=AssertionError("no egress in this test")
        ) as urlopen:
            passed = self.report(StubTransport())
            missing = self.report(StubTransport(), environ={})
            failed = self.report(StubTransport(response=HttpResponse(500, PROVIDER_BODY_CANARY)))

        urlopen.assert_not_called()
        self.assertEqual(passed.status, smoke.STATUS_PASS)
        self.assertEqual(missing.status, smoke.STATUS_NOT_RUN)
        self.assertEqual(failed.status, smoke.STATUS_FAIL)


if __name__ == "__main__":  # pragma: no cover - direct invocation
    unittest.main()
