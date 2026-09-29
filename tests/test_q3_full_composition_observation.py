"""Offline tests for the thin Q3 full-composition hosted observation tooling (Issue #194).

Every test here is offline: the transport is a stub, the environment is fake, and no hosted call
is ever made.  The suite pins the properties the merged ``§9.3`` Q3 per-observation contract and
Human Decision HD-A ～ HD-D require:

* the full composition is driven by :func:`snapshot_loader.explain_q3` (never re-assembled by the
  tooling), and the parser / validator / HTTP client are reused, not copied;
* the deterministic business result comes from the existing pipeline over a fixed **SIMULATED**
  fixture -- it is not a hard-coded answer;
* the three admissibility layers are distinguished truthfully (no model output / provider response
  without a structured selection / structured selection formed, accepted **or** rejected);
* the sanitized record carries no raw body, no header, no credential, no machine path and no
  unregistered provider content;
* at most one hosted request is made, with no retry, no fallback and no provider switching;
* a missing credential and a non-``COMPLETE`` projection both produce **zero egress**, and a real
  observation additionally requires the exact 40-hex merged-main commit identifier (an omitted,
  ``UNKNOWN``, abbreviated or malformed identifier never opens an egress path);
* canonical criterion mapping stays an oracle-based observation, with ``not determined`` /
  ``not expressible under the selection contract`` prose and mismatch findings instead of a second
  validator -- a mechanism-shape deviation (an extra key, an unknown evidence name, an unregistered
  answer kind) is never converted into a canonical business-semantics violation.
"""

from __future__ import annotations

import ast
import contextlib
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

from snapshot_loader import HttpResponse, ProviderUnavailable, build_q3_projection
from tests.test_deepseek_provider import CREDENTIAL_SENTINEL, StubTransport, envelope

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "q3_full_composition_observation.py"
)

FIXED_SHA = "298be2a42addbe56fcac41c89baf172c5fc26afe"
CREDENTIAL_ENV = {"DEEPSEEK_API_KEY": CREDENTIAL_SENTINEL}

#: A compliant selection for the fixture's canonical relation (recommended 100 > shortage 30).
GOOD_SELECTION: dict[str, object] = {
    "answer_kind": "MOQ_RAISED_RECOMMENDATION_ABOVE_SHORTAGE",
    "evidence": [
        "ShortageQty",
        "BasePurchaseNeed",
        "ApplicableMOQ",
        "MOQAdjustmentQty",
        "RecommendedPurchaseQty",
    ],
    "uncertainty": [],
    "human_decision_required": True,
}

#: The canonical `§2.5.9` example the fixed fixture's inputs must derive through the pipeline.
EXPECTED_QUANTITIES = {
    "ShortageQty": "30",
    "BasePurchaseNeed": "30",
    "ApplicableMOQ": "100",
    "MOQAdjustmentQty": "70",
    "RecommendedPurchaseQty": "100",
}

BODY_CANARY = "LEAK-CANARY-RAW-PROVIDER-BODY"
PROSE_CANARY = "LEAK-CANARY-UNREGISTERED-PROVIDER-PROSE"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("q3_full_composition_observation", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


obs = _load_module()


class Q3FullCompositionObservationTests(unittest.TestCase):
    """The tooling driven entirely through injected seams."""

    # --- helpers ----------------------------------------------------------------------

    def run_tool(
        self, transport: Any | None = None, *, environ: Any = None, **kwargs: Any
    ):
        transport = StubTransport() if transport is None else transport
        record, exit_code = obs.run_observation(
            transport=transport,
            environ=CREDENTIAL_ENV if environ is None else environ,
            commit_sha=kwargs.pop("commit_sha", FIXED_SHA),
            **kwargs,
        )
        return record, exit_code, transport

    def serialized(self, record: Any) -> str:
        return (
            json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True)
            + "\n"
            + record.render_text()
        )

    def criterion(self, record: Any, name: str) -> dict[str, str]:
        for item in record.canonical_criteria:
            if item["criterion"] == name:
                return item
        raise AssertionError(f"criterion not recorded: {name}")

    def stub(self, selection: object) -> StubTransport:
        return StubTransport(response=HttpResponse(200, envelope(selection)))

    # --- 1-2 structured selection formed: accepted and rejected both count -------------

    def test_obs_1_accepted_selection_is_an_observation_driven_by_explain_q3(self) -> None:
        calls: list[object] = []
        original = obs.explain_q3

        def recording_explain(*args: Any, **kwargs: Any):
            calls.append(args[1])
            return original(*args, **kwargs)

        with mock.patch.object(obs, "explain_q3", side_effect=recording_explain):
            record, exit_code, transport = self.run_tool(self.stub(GOOD_SELECTION))

        self.assertEqual(len(calls), 1, "the full composition must be driven by explain_q3")
        self.assertEqual(exit_code, obs.EXIT_RECORD_PRODUCED)
        self.assertEqual(len(transport.requests), 1)
        self.assertEqual(record.request_count, 1)
        self.assertTrue(record.provider_invoked)
        self.assertTrue(record.provider_response_received)
        self.assertTrue(record.structured_selection_formed)
        self.assertEqual(record.http_status, 200)
        self.assertEqual(record.final_runtime_outcome, "EXPLAINED")
        self.assertEqual(
            record.mechanism_validator_disposition, obs.NOTE_MECHANISM_ACCEPTED
        )
        self.assertEqual(
            record.observation_admissibility, obs.ADMISSIBILITY_SELECTION_FORMED
        )
        self.assertTrue(record.deterministic_recommendation_unchanged)
        self.assertEqual(record.mismatch_findings, [])
        self.assertEqual(
            record.projection_quantities, EXPECTED_QUANTITIES
        )
        self.assertEqual(record.projection_completeness_state, "COMPLETE")
        self.assertEqual(obs._unsanitized_strings(record), ())
        self.assert_no_sensitive(self.serialized(record))

    def test_obs_2_rejected_selection_stays_an_observation_with_violations(self) -> None:
        rejected = {**GOOD_SELECTION, "uncertainty": ["ShortageQty"]}

        record, exit_code, transport = self.run_tool(self.stub(rejected))

        self.assertEqual(exit_code, obs.EXIT_RECORD_PRODUCED)
        self.assertEqual(len(transport.requests), 1)
        self.assertTrue(record.structured_selection_formed)
        self.assertEqual(record.final_runtime_outcome, "RESPONSE_UNACCEPTABLE")
        self.assertEqual(
            record.mechanism_validator_disposition, obs.NOTE_MECHANISM_REJECTED
        )
        # A rejected real selection must never be reclassified as "no observation".
        self.assertEqual(
            record.observation_admissibility, obs.ADMISSIBILITY_SELECTION_FORMED
        )
        # The mechanism enforces a registered slice constraint outside the six recorded canonical
        # criteria, so the disagreement is recorded as a mismatch finding, not silently resolved.
        self.assertTrue(record.mismatch_findings)
        self.assertIn("mismatch finding", record.mismatch_findings[0])
        self.assertEqual(obs._unsanitized_strings(record), ())
        self.assert_no_sensitive(self.serialized(record))

    # --- 3-6 the three admissibility layers and zero-egress guards --------------------

    def test_obs_3_response_without_structured_selection(self) -> None:
        transport = StubTransport(response=HttpResponse(200, f"<html>{BODY_CANARY}</html>".encode()))

        record, exit_code, transport = self.run_tool(transport)

        self.assertEqual(exit_code, obs.EXIT_RECORD_PRODUCED)
        self.assertEqual(len(transport.requests), 1)
        self.assertTrue(record.provider_response_received)
        self.assertFalse(record.structured_selection_formed)
        self.assertEqual(
            record.observation_admissibility, obs.ADMISSIBILITY_RESPONSE_WITHOUT_SELECTION
        )
        self.assertIsNone(record.selection)
        self.assertEqual(record.canonical_criteria, [])
        self.assertEqual(record.final_runtime_outcome, "PROVIDER_UNAVAILABLE")
        self.assertEqual(obs._unsanitized_strings(record), ())
        self.assertNotIn(BODY_CANARY, self.serialized(record))

    def test_obs_4_transport_failure_before_response(self) -> None:
        transport = StubTransport(error=ProviderUnavailable("transport failed"))

        record, exit_code, transport = self.run_tool(transport)

        self.assertEqual(exit_code, obs.EXIT_RECORD_PRODUCED)
        self.assertEqual(len(transport.requests), 1)
        self.assertFalse(record.provider_response_received)
        self.assertFalse(record.structured_selection_formed)
        self.assertEqual(
            record.observation_admissibility, obs.ADMISSIBILITY_NO_MODEL_OUTPUT
        )
        self.assertIn(obs.NOTE_TRANSPORT_FAILURE, record.notes)

    def test_obs_5_missing_credential_is_zero_egress(self) -> None:
        record, exit_code, transport = self.run_tool(environ={})

        self.assertEqual(exit_code, obs.EXIT_RECORD_PRODUCED)
        self.assertEqual(len(transport.requests), 0)
        self.assertEqual(record.request_count, 0)
        self.assertFalse(record.provider_response_received)
        self.assertFalse(record.structured_selection_formed)
        self.assertEqual(
            record.observation_admissibility, obs.ADMISSIBILITY_NO_MODEL_OUTPUT
        )
        self.assertIn(obs.NOTE_NO_CREDENTIAL, record.notes)
        self.assertIsNone(record.selection)

    def test_obs_6_non_complete_projection_is_zero_egress(self) -> None:
        record, exit_code, transport = self.run_tool(moq=None)

        self.assertEqual(exit_code, obs.EXIT_RECORD_PRODUCED)
        self.assertEqual(len(transport.requests), 0)
        self.assertEqual(record.request_count, 0)
        self.assertEqual(record.projection_completeness_state, "DATA_INCOMPLETE")
        self.assertEqual(
            record.observation_admissibility, obs.ADMISSIBILITY_NO_MODEL_OUTPUT
        )
        self.assertIn(obs.NOTE_PROJECTION_INCOMPLETE, record.notes)
        self.assertEqual(record.canonical_criteria, [])

    # --- 7-9 determinism, request count and no retry ----------------------------------

    def test_obs_7_deterministic_recommendation_is_unchanged(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as scratch:
            pipeline, report = obs.run_deterministic_chain(Path(scratch))
            recommendation = pipeline.procurement_recommendation.for_family(
                obs.PLANT_ID, obs.MATERIAL_CODE
            )
            assert recommendation is not None
            before = copy_of(recommendation.to_dict())
            projection_before = build_q3_projection(recommendation)

            record, _exit, _transport = self.run_tool(
                self.stub(GOOD_SELECTION), boundary_root=Path(scratch)
            )

            self.assertEqual(recommendation.to_dict(), before)
            self.assertEqual(build_q3_projection(recommendation), projection_before)
            self.assertEqual(record.projection_quantities, EXPECTED_QUANTITIES)
            self.assertTrue(record.deterministic_recommendation_unchanged)

    def test_obs_8_request_count_is_at_most_one_on_every_path(self) -> None:
        cases = (
            ("accepted", self.stub(GOOD_SELECTION), CREDENTIAL_ENV),
            ("rejected", self.stub({**GOOD_SELECTION, "uncertainty": ["ShortageQty"]}), CREDENTIAL_ENV),
            ("no-selection", StubTransport(response=HttpResponse(200, b"not json")), CREDENTIAL_ENV),
            ("transport-failure", StubTransport(error=ProviderUnavailable("x")), CREDENTIAL_ENV),
            ("missing-credential", StubTransport(), {}),
        )
        for name, transport, environ in cases:
            with self.subTest(case=name):
                _record, _exit, transport = self.run_tool(transport, environ=environ)
                self.assertLessEqual(len(transport.requests), 1)

    def test_obs_9_no_retry_fallback_or_provider_switch(self) -> None:
        for status in (401, 403, 429, 500, 503):
            with self.subTest(status=status):
                transport = StubTransport(response=HttpResponse(status, b"{}"))

                record, _exit, transport = self.run_tool(transport)

                self.assertEqual(len(transport.requests), 1)
                self.assertEqual(record.request_count, 1)
                self.assertFalse(record.structured_selection_formed)
                self.assertEqual(record.http_status, status)
                self.assertEqual(
                    record.observation_admissibility, obs.ADMISSIBILITY_NO_MODEL_OUTPUT
                )
                self.assertIn(obs.NOTE_HTTP_REJECTION, record.notes)

    # --- 10-11 sanitization -----------------------------------------------------------

    def test_obs_10_report_carries_no_body_header_credential_or_machine_path(self) -> None:
        transport = StubTransport(response=HttpResponse(200, f"<html>{BODY_CANARY}</html>".encode()))

        record, _exit, _transport = self.run_tool(transport)
        serialized = self.serialized(record)

        self.assert_no_sensitive(serialized)
        self.assertNotIn(BODY_CANARY, serialized)
        self.assertNotIn("q3-observation-", serialized)  # no scratch path
        self.assertEqual(obs._unsanitized_strings(record), ())

    def test_obs_11_unregistered_provider_content_is_sanitized(self) -> None:
        hostile = {
            "answer_kind": PROSE_CANARY,
            "evidence": ["ShortageQty", PROSE_CANARY],
            "uncertainty": [],
            "human_decision_required": False,
            "reason": PROSE_CANARY,
        }

        record, _exit, _transport = self.run_tool(self.stub(hostile))
        serialized = self.serialized(record)

        self.assertNotIn(PROSE_CANARY, serialized)
        self.assertEqual(record.selection["answer_kind"], obs.NOTE_UNREGISTERED_VALUE_PRESENT)
        self.assertGreaterEqual(record.selection["extra_key_count"], 1)
        self.assertGreaterEqual(record.selection["evidence_unknown_name_count"], 1)
        self.assertEqual(record.selection["evidence_names"], ["ShortageQty"])
        # Unregistered content is a mechanism-shape deviation: it is recorded, but it is not proof
        # of an unsupported business fact, and it never auto-escalates to the LLM boundary criterion.
        self.assertEqual(
            self.criterion(record, "unsupported fact")["result"], obs.NOTE_NOT_DETERMINED
        )
        self.assertEqual(
            self.criterion(record, "deterministic / LLM boundary")["result"],
            obs.NOTE_NOT_EXPRESSIBLE,
        )
        self.assertEqual(
            self.criterion(record, "human-decision boundary")["result"], obs.NOTE_VIOLATED
        )
        self.assertEqual(
            self.criterion(record, "required evidence coverage")["result"], obs.NOTE_VIOLATED
        )
        self.assertEqual(
            self.criterion(record, "relation correctness")["result"], obs.NOTE_NOT_DETERMINED
        )
        self.assertEqual(obs._unsanitized_strings(record), ())
        self.assert_no_sensitive(serialized)

    # --- 12-14 canonical criterion mapping --------------------------------------------

    def test_obs_12_canonical_criterion_mapping_records_violations(self) -> None:
        missing_fact = {**GOOD_SELECTION, "evidence": ["ShortageQty"]}

        record, _exit, _transport = self.run_tool(self.stub(missing_fact))

        coverage = self.criterion(record, "required evidence coverage")
        self.assertEqual(coverage["result"], obs.NOTE_VIOLATED)
        self.assertIn("§5.3", coverage["canonical_authority"])
        self.assertEqual(
            self.criterion(record, "relation correctness")["result"], obs.NOTE_NOT_VIOLATED
        )

        wrong_relation = {**GOOD_SELECTION, "answer_kind": "RECOMMENDATION_EQUALS_SHORTAGE"}
        record, _exit, _transport = self.run_tool(self.stub(wrong_relation))
        relation = self.criterion(record, "relation correctness")
        self.assertEqual(relation["result"], obs.NOTE_VIOLATED)
        self.assertIn("§2.5", relation["canonical_authority"])

    def test_obs_13_not_determined_and_not_expressible_are_prose(self) -> None:
        record, _exit, _transport = self.run_tool(self.stub(GOOD_SELECTION))

        fidelity = self.criterion(record, "evidence fidelity / Q3 role separation")
        self.assertEqual(fidelity["result"], obs.NOTE_NOT_EXPRESSIBLE)
        self.assertIn("cannot be expressed", fidelity["observed_evidence"])
        self.assertEqual(
            self.criterion(record, "deterministic / LLM boundary")["result"],
            obs.NOTE_NOT_EXPRESSIBLE,
        )
        self.assertEqual(
            self.criterion(record, "unsupported fact")["result"], obs.NOTE_NOT_VIOLATED
        )

        record, _exit, _transport = self.run_tool(
            self.stub({**GOOD_SELECTION, "answer_kind": "UNREGISTERED_KIND"})
        )
        self.assertEqual(
            self.criterion(record, "relation correctness")["result"], obs.NOTE_NOT_DETERMINED
        )

    def test_obs_14_mismatch_finding_is_recorded_not_resolved(self) -> None:
        record, _exit, _transport = self.run_tool(
            self.stub({**GOOD_SELECTION, "uncertainty": ["ShortageQty"]})
        )

        self.assertTrue(record.mismatch_findings)
        finding = record.mismatch_findings[0]
        self.assertIn("mismatch finding", finding)
        self.assertIn("canonical design is not modified", finding)
        self.assertEqual(
            record.mechanism_validator_disposition, obs.NOTE_MECHANISM_REJECTED
        )

    # --- 15 no replay surface, and the fixture boundary ------------------------------

    def test_obs_15_no_replay_surface_and_fixture_is_simulated(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                obs.main(["--replay", "captured.json"])
        self.assertEqual(caught.exception.code, 2)

        record, _exit, _transport = self.run_tool(self.stub(GOOD_SELECTION))
        self.assertEqual(record.execution_mode, obs.MODE_HOSTED)
        self.assertIn("SIMULATED", record.simulated_identity_boundary)
        self.assertTrue(obs.PLANT_ID.startswith("SIM-"))
        self.assertTrue(obs.MATERIAL_CODE.startswith("SIM-"))
        # The fixture states inputs only; the business quantities come from the pipeline.
        records = obs.fixture_records()
        self.assertEqual(
            records[obs.ROLE_REQUIREMENT][0]["ProductionQty"], obs.DEMAND_QUANTITY
        )
        self.assertNotIn("RecommendedPurchaseQty", json.dumps(records))
        self.assertEqual(record.projection_quantities, EXPECTED_QUANTITIES)

    # --- 16-17 metadata validation and the thin-boundary guard -----------------------

    def test_obs_16_a_real_observation_requires_the_exact_40_hex_commit(self) -> None:
        # Omitted (the run_observation default), UNKNOWN, abbreviated and malformed identifiers must
        # all fail closed with zero egress, exit 1, a sanitized record and no echo of the input.
        cases = (
            ("omitted", obs._UNKNOWN_COMMIT, False),
            ("explicit-unknown", "UNKNOWN", False),
            ("short-sha", FIXED_SHA[:7], False),
            ("short-sha-4", FIXED_SHA[:4], False),
            ("not-a-sha", "not a sha", False),
            ("empty", "", False),
            ("credential-shaped", f"{CREDENTIAL_SENTINEL}; rm -rf /", False),
            ("exact-40-hex", FIXED_SHA, True),
        )
        for name, value, allowed in cases:
            with self.subTest(case=name):
                transport = StubTransport()

                record, exit_code, transport = self.run_tool(transport, commit_sha=value)

                if allowed:
                    self.assertEqual(exit_code, obs.EXIT_RECORD_PRODUCED)
                    self.assertEqual(len(transport.requests), 1)
                    self.assertEqual(record.commit_under_test, FIXED_SHA)
                    self.assertTrue(record.provider_response_received)
                else:
                    self.assertEqual(exit_code, obs.EXIT_NO_TRUTHFUL_RECORD)
                    self.assertEqual(len(transport.requests), 0)
                    self.assertEqual(record.request_count, 0)
                    self.assertFalse(record.provider_invoked)
                    self.assertEqual(record.commit_under_test, "UNKNOWN")
                    self.assertIn(obs.NOTE_COMMIT_REQUIRED, record.notes)
                    self.assertEqual(
                        record.observation_admissibility,
                        obs.ADMISSIBILITY_NO_MODEL_OUTPUT,
                    )
                    serialized = self.serialized(record)
                    # ``UNKNOWN`` is the sanitized placeholder this record legitimately carries; any
                    # other rejected input must not appear anywhere.
                    if value and value != obs._UNKNOWN_COMMIT:
                        self.assertNotIn(value, serialized)
                    self.assert_no_sensitive(serialized)
                self.assertEqual(obs._unsanitized_strings(record), ())

        # Shape helpers: the sanitizer shape and the egress gate are deliberately different.
        self.assertTrue(obs._safe_commit(FIXED_SHA[:7]))
        self.assertTrue(obs._safe_commit("UNKNOWN"))
        self.assertIsNone(obs._safe_commit("not a sha"))
        self.assertEqual(obs._egress_commit(FIXED_SHA), FIXED_SHA)
        self.assertIsNone(obs._egress_commit(FIXED_SHA[:7]))
        self.assertIsNone(obs._egress_commit("UNKNOWN"))
        self.assertIsNone(obs._egress_commit(FIXED_SHA.upper() + "0"))

    def test_obs_18_the_cli_requires_the_commit_identifier(self) -> None:
        for label, argv in (("omitted", ["--json"]), ("short", ["--json", "--commit-sha", FIXED_SHA[:7]])):
            with self.subTest(case=label):
                stdout, stderr = io.StringIO(), io.StringIO()
                with mock.patch.dict(
                    os.environ, CREDENTIAL_ENV, clear=True
                ), mock.patch(
                    "urllib.request.urlopen", side_effect=AssertionError("no egress in this test")
                ) as urlopen, contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    exit_code = obs.main(argv)

                urlopen.assert_not_called()
                self.assertEqual(exit_code, obs.EXIT_NO_TRUTHFUL_RECORD)
                payload = json.loads(stdout.getvalue())
                self.assertEqual(payload["request_count"], 0)
                self.assertEqual(payload["commit_under_test"], "UNKNOWN")
                self.assertNotIn(FIXED_SHA[:7], stdout.getvalue() + stderr.getvalue())
                self.assert_no_sensitive(stdout.getvalue() + stderr.getvalue())

    def test_obs_19_extra_key_only_is_not_a_proven_canonical_violation(self) -> None:
        # A mechanism-shape deviation alone must not be converted into a canonical violation just
        # because the mechanism rejected it.
        extra_key_only = {**GOOD_SELECTION, "reason": PROSE_CANARY}

        record, exit_code, transport = self.run_tool(self.stub(extra_key_only))

        self.assertEqual(exit_code, obs.EXIT_RECORD_PRODUCED)
        self.assertEqual(len(transport.requests), 1)
        self.assertEqual(record.final_runtime_outcome, "RESPONSE_UNACCEPTABLE")
        self.assertEqual(record.mechanism_validator_disposition, obs.NOTE_MECHANISM_REJECTED)
        # The deviation is recorded, but it proves no business semantics.
        self.assertEqual(
            self.criterion(record, "unsupported fact")["result"], obs.NOTE_NOT_DETERMINED
        )
        self.assertEqual(
            self.criterion(record, "deterministic / LLM boundary")["result"],
            obs.NOTE_NOT_EXPRESSIBLE,
        )
        self.assertEqual(
            self.criterion(record, "evidence fidelity / Q3 role separation")["result"],
            obs.NOTE_NOT_EXPRESSIBLE,
        )
        self.assertEqual(
            self.criterion(record, "human-decision boundary")["result"], obs.NOTE_NOT_VIOLATED
        )
        self.assertEqual(
            self.criterion(record, "required evidence coverage")["result"],
            obs.NOTE_NOT_VIOLATED,
        )
        self.assertEqual(
            self.criterion(record, "relation correctness")["result"], obs.NOTE_NOT_VIOLATED
        )
        # mechanism != canonical oracle: the disagreement is preserved as a mismatch finding.
        self.assertTrue(record.mismatch_findings)
        self.assertIn("mismatch finding", record.mismatch_findings[0])
        self.assertNotIn(PROSE_CANARY, self.serialized(record))
        self.assertEqual(obs._unsanitized_strings(record), ())

    def test_obs_17_entry_point_keeps_the_thin_boundary(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        allowed_modules = {
            "__future__",
            "argparse",
            "collections",
            "copy",
            "dataclasses",
            "datetime",
            "fractions",
            "hashlib",
            "json",
            "os",
            "pathlib",
            "re",
            "snapshot_loader",
            "sys",
            "tempfile",
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
        # No HTTP client, no subprocess, no own parser / validator / provider.
        self.assertEqual(attributes & {"urlopen", "Request", "HTTPError", "Popen", "run"}, set())
        self.assertEqual(names & {"subprocess", "socket", "urllib", "ssl"}, set())
        self.assertEqual(names & {"DeepSeekProvider", "selection_json_schema"}, set())
        # The credential is never named by the tooling, and no request header is ever built.
        self.assertNotIn("DEEPSEEK_API_KEY", source)
        self.assertNotIn("Authorization", source)
        self.assertNotIn("api_key", source)
        # No parser / validator / HTTP client is copied into the tooling.
        self.assertNotIn("def validate_provider_response", source)
        self.assertNotIn("def _selection_from_body", source)
        self.assertNotIn("class StdlibHttpTransport", source)
        # The full composition is driven through the merged entry points, not re-assembled.
        self.assertIn("explain_q3(", source)
        self.assertIn("provider_from_environment(", source)

    # --- assertion helpers ------------------------------------------------------------

    def assert_no_sensitive(self, text: str) -> None:
        for canary in (
            CREDENTIAL_SENTINEL,
            "Authorization",
            "Bearer",
            "LEAK-CANARY",
            "DEEPSEEK_API_KEY",
        ):
            self.assertNotIn(canary, text)


#: Frozen so the module-level vocabulary list stays readable in the assertion above.
def copy_of(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":  # pragma: no cover - direct invocation
    unittest.main()
