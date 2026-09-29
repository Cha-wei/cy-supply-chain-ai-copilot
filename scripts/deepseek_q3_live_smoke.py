"""Manual opt-in live smoke for the DeepSeek Q3 explanation path.

What this is
------------

A **thin, opt-in** operator entry point that exercises the **already merged** hosted
integration contract once, end to end:

``fixed SIMULATED Q3 projection -> credential resolved by the merged composition boundary ->
merged DeepSeek provider -> one real POST /responses -> merged envelope parser ->
validate_provider_response(...) -> LIVE_SMOKE_PASS / sanitized LIVE_SMOKE_FAIL``

It reuses :mod:`snapshot_loader.deepseek_provider` (and therefore the merged parser) and the
merged :func:`snapshot_loader.explanation_seam.validate_provider_response`; it does **not**
re-implement an HTTP client, an envelope parser or a validator, and it adds no retry, no
backoff, no provider switching and no fallback.

What this is not
----------------

Not AI Eval, not a benchmark and not a model-quality judgement: it only shows whether the real
hosted integration contract works once.

Opt-in boundary
---------------

Importing this module performs **no** network I/O, and the automatic test suite never reaches
the hosted provider (the tests inject a stub transport).  A real request happens only when an
operator explicitly runs::

    python scripts/deepseek_q3_live_smoke.py
    python scripts/deepseek_q3_live_smoke.py --json

Secret boundary (``§7.1``)
--------------------------

* the credential is resolved **only** by the merged composition boundary
  (:func:`snapshot_loader.provider_from_environment`), from the **process environment** only;
  this script deliberately has **no** ``--api-key`` flag, no ``.env`` loader and no file input,
  and it never reads the credential value itself;
* the credential therefore cannot reach the projection, the prompt, stdout or the report, and
  the report is credential-safe by construction: it carries only statuses, counts, validated
  identifiers and registered vocabulary, and the run additionally verifies that no other string
  entered it (:func:`_unsanitized_strings` -- the report's own dynamic fields are re-validated
  there instead of being trusted);
* caller-supplied metadata is validated **before any egress** (a commit identifier must be
  ``UNKNOWN`` or a hex Git SHA; a timestamp must be an ISO-8601 instant).  An invalid value is
  rejected with fixed sanitized wording, is never recorded and is never echoed.

Data boundary
-------------

The only business payload is a **fixed synthetic** Q3 projection: five registered quantities,
fake plant / material identities, no package identity, no content-view digest, no Analysis Run
identity, no raw source evidence and no supplier / inventory / customer data.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:  # pragma: no cover - import path bootstrap only
    sys.path.insert(0, str(_REPO_ROOT))

from snapshot_loader import (  # noqa: E402 - the path bootstrap must precede this import
    ANSWER_KIND_LITERALS,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    DEEPSEEK_PROVIDER,
    DEEPSEEK_RESPONSES_PATH,
    HUMAN_DECISION_REQUIRED_TEXT,
    PROCUREMENT_POLICY_INPUT_STAGE,
    Q3_FACT_FIELDS,
    Q3_QUESTION,
    SHORTAGE_RULE_ID,
    HttpTransport,
    ProviderUnavailable,
    StdlibHttpTransport,
    UnavailableProvider,
    provider_from_environment,
    validate_provider_response,
)

#: Smoke status vocabulary (execution outcomes of this script, never business statuses).
STATUS_PASS: str = "LIVE_SMOKE_PASS"
STATUS_FAIL: str = "LIVE_SMOKE_FAIL"
STATUS_NOT_RUN: str = "LIVE_SMOKE_NOT_RUN"

#: Minimal, sanitized failure categories -- the whole diagnosis of a failed run.
CATEGORY_CREDENTIAL_NOT_CONFIGURED: str = "CREDENTIAL_NOT_CONFIGURED"
CATEGORY_TRANSPORT_FAILURE: str = "TRANSPORT_FAILURE"
CATEGORY_CREDENTIAL_REJECTED: str = "CREDENTIAL_REJECTED"
CATEGORY_RATE_LIMITED: str = "RATE_LIMITED"
CATEGORY_PROVIDER_SERVER_ERROR: str = "PROVIDER_SERVER_ERROR"
CATEGORY_UNEXPECTED_HTTP_STATUS: str = "UNEXPECTED_HTTP_STATUS"
CATEGORY_UNEXPECTED_ENVELOPE: str = "UNEXPECTED_ENVELOPE"
CATEGORY_VALIDATOR_REJECTED: str = "VALIDATOR_REJECTED"
CATEGORY_CRITERION_FAILED: str = "CRITERION_FAILED"
CATEGORY_UNSANITIZED_REPORT: str = "UNSANITIZED_REPORT"
CATEGORY_INVALID_METADATA: str = "INVALID_METADATA"

#: Fixed notes.  None of them interpolates provider, transport or exception text, so no foreign
#: string can enter the report through a message (``§7.1`` ``S-8``).
NOTE_CREDENTIAL_NOT_CONFIGURED: str = (
    "no provider credential is configured in the process environment, so no request was sent "
    "(LIVE_SMOKE_READY_NOT_RUN)"
)
NOTE_PROVIDER_FAILED: str = (
    "the hosted call failed closed and the merged adapter surfaced no provider detail"
)
NOTE_UNEXPECTED_FAILURE: str = (
    "the adapter raised an unexpected error; the report carries no provider or exception detail"
)
NOTE_VALIDATOR_REJECTED: str = (
    "the merged validator rejected the selection, so the runtime surfaces no explanation and "
    "nothing is treated as reliable"
)
NOTE_CRITERIA_UNSATISFIED: str = (
    "the run did not satisfy every pass criterion; the unsatisfied ones are the pass criteria "
    "absent from criteria_satisfied"
)
NOTE_UNSANITIZED_REPORT: str = (
    "the report carried a string outside the permitted status / identifier / registered "
    "vocabulary, so it was withheld as a failure and the report was rebuilt from fixed "
    "vocabulary only"
)
NOTE_INVALID_METADATA: str = (
    "the supplied run metadata is not a safe identifier (a commit identifier must be UNKNOWN or "
    "a hex Git SHA, and a timestamp must be an ISO-8601 instant), so no request was sent and the "
    "supplied value was neither recorded nor echoed"
)
NOTE_PASS: str = (
    "the real hosted integration contract worked once: one request, the merged parser accepted "
    "the envelope and the merged validator accepted the selection; this is not AI Eval and says "
    "nothing about model quality"
)

#: Synthetic identities: deliberately fake, so the payload can never be enterprise data.
SIMULATED_PLANT_ID: str = "SIM-PLANT-001"
SIMULATED_MATERIAL_CODE: str = "SIM-MATERIAL-001"
SIMULATED_NEED_DATE: str = "2026-10-20"

#: For this fixed synthetic relation (shortage 30, MOQ 100, recommended 100) exactly one
#: registered answer kind is consistent, so the smoke can check it explicitly.
EXPECTED_ANSWER_KIND: str = "MOQ_RAISED_RECOMMENDATION_ABOVE_SHORTAGE"

#: The criteria a passing run must satisfy (labels only; no business value is created here).
PASS_CRITERIA: tuple[str, ...] = (
    "exactly-one-request",
    "http-success",
    "envelope-accepted-by-merged-parser",
    "selection-parsed",
    "validator-accepted",
    "answer-kind-matches-synthetic-relation",
    "all-five-q3-facts-in-evidence",
    "uncertainty-empty",
    "human-decision-contract-preserved",
    "synthetic-input-unchanged",
    "credential-not-leaked",
)

#: Identifiers a sanitized report may carry besides the fixed vocabulary: the registered answer
#: kinds and the registered fact names.  Nothing else is permitted -- in particular the report's
#: own dynamic fields are **validated** below instead of being trusted into the allowlist.
_PERMITTED_REPORT_TEXTS: frozenset[str] = frozenset(
    {
        STATUS_PASS,
        STATUS_FAIL,
        STATUS_NOT_RUN,
        CATEGORY_CREDENTIAL_NOT_CONFIGURED,
        CATEGORY_TRANSPORT_FAILURE,
        CATEGORY_CREDENTIAL_REJECTED,
        CATEGORY_RATE_LIMITED,
        CATEGORY_PROVIDER_SERVER_ERROR,
        CATEGORY_UNEXPECTED_HTTP_STATUS,
        CATEGORY_UNEXPECTED_ENVELOPE,
        CATEGORY_VALIDATOR_REJECTED,
        CATEGORY_CRITERION_FAILED,
        CATEGORY_UNSANITIZED_REPORT,
        CATEGORY_INVALID_METADATA,
        NOTE_CREDENTIAL_NOT_CONFIGURED,
        NOTE_PROVIDER_FAILED,
        NOTE_UNEXPECTED_FAILURE,
        NOTE_VALIDATOR_REJECTED,
        NOTE_CRITERIA_UNSATISFIED,
        NOTE_UNSANITIZED_REPORT,
        NOTE_INVALID_METADATA,
        NOTE_PASS,
        DEEPSEEK_PROVIDER,
        DEEPSEEK_MODEL,
        f"{DEEPSEEK_BASE_URL}{DEEPSEEK_RESPONSES_PATH}",
        HUMAN_DECISION_REQUIRED_TEXT,
        *PASS_CRITERIA,
    }
)


#: The explicit unknown-commit marker a report may carry.
_UNKNOWN_COMMIT_SHA: str = "UNKNOWN"

#: The only shape a caller-supplied commit identifier may have: a hex Git SHA (short or full).
#: Anything else -- free text, a path, a command, a credential-like value -- is rejected **before
#: any egress** and is neither recorded nor echoed.
_COMMIT_SHA_PATTERN = re.compile(r"\A[0-9a-fA-F]{4,40}\Z")

#: The only shape a caller-supplied timestamp may have: an ISO-8601 / RFC 3339 instant.
_TIMESTAMP_PATTERN = re.compile(
    r"\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})\Z"
)


def _safe_commit_sha(value: object) -> str | None:
    """The value itself when it is a safe commit identifier, otherwise ``None``."""

    if not isinstance(value, str):
        return None
    if value == _UNKNOWN_COMMIT_SHA:
        return value
    return value if _COMMIT_SHA_PATTERN.match(value) is not None else None


def _safe_timestamp(value: object) -> str | None:
    """The value itself when it is an ISO-8601 instant of the fixed shape, otherwise ``None``."""

    if not isinstance(value, str) or _TIMESTAMP_PATTERN.match(value) is None:
        return None
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return None
    return value


def _generated_timestamp() -> str:
    """The internally generated timestamp (always of the permitted shape)."""

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def synthetic_q3_projection() -> dict[str, object]:
    """The fixed **SIMULATED** Q3 projection sent by the live smoke.

    It mirrors the runtime projection of a ``COMPLETE`` Q3 recommendation exactly (same keys,
    same exact serialization: exact rational payloads and exact decimal text) while carrying only
    fake identities and no package ／ run ／ source evidence.
    """

    grain = [SIMULATED_PLANT_ID, SIMULATED_MATERIAL_CODE, SIMULATED_NEED_DATE]
    return {
        "question": Q3_QUESTION,
        "grain": {
            "plant_id": SIMULATED_PLANT_ID,
            "material_code": SIMULATED_MATERIAL_CODE,
            "RecommendationNeedDate": SIMULATED_NEED_DATE,
        },
        "facts": {
            "ShortageQty": {"numerator": 30, "denominator": 1},
            "BasePurchaseNeed": {"numerator": 30, "denominator": 1},
            "ApplicableMOQ": "100",
            "MOQAdjustmentQty": {"numerator": 70, "denominator": 1},
            "RecommendedPurchaseQty": {"numerator": 100, "denominator": 1},
        },
        "completeness": {
            "state": "COMPLETE",
            "valid_absence": None,
            "outcome": None,
            "missing_facts": [],
            "root_condition": None,
            "policy_root_condition": None,
            "applicability_basis": "SIMULATED-MOQ-APPLICABLE",
            "shortage_reference": {"grain": grain, "rule": SHORTAGE_RULE_ID},
            "policy_input_reference": {"grain": grain, "rule": PROCUREMENT_POLICY_INPUT_STAGE},
            "inherited_issues": [],
            "rule_issues": [],
        },
    }


class _CountingTransport:
    """Wraps a transport to prove that exactly one hosted request happened (no retry)."""

    def __init__(self, inner: HttpTransport) -> None:
        self._inner = inner
        self.requests: int = 0
        self.last_status: int | None = None

    def send(self, request: Any) -> Any:
        self.requests += 1
        response = self._inner.send(request)
        self.last_status = int(response.status)
        return response


@dataclass(frozen=True, slots=True)
class SmokeReport:
    """Credential-safe smoke report: statuses, counts, identifiers and registered vocabulary.

    Every field is either a fixed literal, a count, a boolean, a registered vocabulary member
    (``answer_kind`` ／ evidence names, recorded only when they are registered) or a **validated**
    caller identifier.  No field is copied from a request, a response, a header or an exception,
    so the report has no channel through which a credential or any other foreign string could
    leave the process; :func:`_unsanitized_strings` re-checks that property on every run.
    """

    status: str
    failure_category: str | None
    provider: str
    model: str
    endpoint: str
    request_count: int
    http_status: int | None
    selection_parsed: bool
    validator_accepted: bool
    answer_kind: str | None
    evidence_names: tuple[str, ...]
    uncertainty_empty: bool
    human_decision_contract_ok: bool
    synthetic_input_unchanged: bool
    credential_not_leaked: bool
    criteria_satisfied: tuple[str, ...]
    timestamp: str
    commit_sha: str
    notes: tuple[str, ...] = ()

    @property
    def criteria_unsatisfied(self) -> tuple[str, ...]:
        return tuple(name for name in PASS_CRITERIA if name not in self.criteria_satisfied)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "failure_category": self.failure_category,
            "provider": self.provider,
            "model": self.model,
            "endpoint": self.endpoint,
            "request_count": self.request_count,
            "http_status": self.http_status,
            "selection_parsed": self.selection_parsed,
            "validator_accepted": self.validator_accepted,
            "answer_kind": self.answer_kind,
            "evidence_names": list(self.evidence_names),
            "uncertainty_empty": self.uncertainty_empty,
            "human_decision_contract_ok": self.human_decision_contract_ok,
            "synthetic_input_unchanged": self.synthetic_input_unchanged,
            "credential_not_leaked": self.credential_not_leaked,
            "criteria_satisfied": list(self.criteria_satisfied),
            "criteria_unsatisfied": list(self.criteria_unsatisfied),
            "timestamp": self.timestamp,
            "commit_sha": self.commit_sha,
            "notes": list(self.notes),
        }

    def render_text(self) -> str:
        lines = [
            f"status           : {self.status}",
            f"failure category : {self.failure_category or '-'}",
            f"provider         : {self.provider}",
            f"model            : {self.model}",
            f"endpoint         : {self.endpoint}",
            f"requests         : {self.request_count}",
            f"http status      : {self.http_status if self.http_status is not None else '-'}",
            f"selection parsed : {self.selection_parsed}",
            f"validator        : {self.validator_accepted}",
            f"answer_kind      : {self.answer_kind or '-'}",
            f"evidence         : {', '.join(self.evidence_names) or '-'}",
            f"uncertainty empty: {self.uncertainty_empty}",
            f"human decision   : {self.human_decision_contract_ok}",
            f"input unchanged  : {self.synthetic_input_unchanged}",
            f"credential safe  : {self.credential_not_leaked}",
            f"criteria         : {len(self.criteria_satisfied)}/{len(PASS_CRITERIA)} satisfied",
            f"timestamp        : {self.timestamp}",
            f"commit           : {self.commit_sha}",
        ]
        for note in self.notes:
            lines.append(f"note             : {note}")
        return "\n".join(lines)


def _report_strings(value: object) -> list[str]:
    """Every string a report value carries, at any depth."""

    found: list[str] = []
    if isinstance(value, str):
        found.append(value)
    elif isinstance(value, Mapping):
        for item in value.values():
            found.extend(_report_strings(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            found.extend(_report_strings(item))
    return found


def _unsanitized_strings(report: SmokeReport) -> tuple[str, ...]:
    """Report strings outside the permitted vocabulary -- normally none.

    The permitted set is built from **fixed** vocabulary plus the registered answer kinds and the
    registered fact names.  The report's own dynamic fields are re-**validated** here rather than
    trusted into the allowlist: a commit identifier must be a safe identifier and a timestamp must
    be an ISO-8601 instant of the fixed shape, and the answer kind ／ evidence names are only ever
    recorded when they are registered vocabulary in the first place.  A provider-controlled or
    caller-controlled arbitrary string therefore cannot be legitimised merely by the report
    carrying it: it shows up here, and the run is withheld.
    """

    permitted = set(_PERMITTED_REPORT_TEXTS) | set(ANSWER_KIND_LITERALS) | set(Q3_FACT_FIELDS)
    if _safe_commit_sha(report.commit_sha) is not None:
        permitted.add(report.commit_sha)
    if _safe_timestamp(report.timestamp) is not None:
        permitted.add(report.timestamp)
    return tuple(text for text in _report_strings(report.to_dict()) if text not in permitted)


def _failure_category(status: int | None) -> str:
    if status is None:
        return CATEGORY_TRANSPORT_FAILURE
    if status in (401, 403):
        return CATEGORY_CREDENTIAL_REJECTED
    if status == 429:
        return CATEGORY_RATE_LIMITED
    if status >= 500:
        return CATEGORY_PROVIDER_SERVER_ERROR
    if status != 200:
        return CATEGORY_UNEXPECTED_HTTP_STATUS
    return CATEGORY_UNEXPECTED_ENVELOPE


def _report(
    *,
    status: str,
    failure_category: str | None,
    counting: _CountingTransport,
    timestamp: str,
    commit_sha: str,
    selection_parsed: bool = False,
    validator_accepted: bool = False,
    answer_kind: str | None = None,
    evidence_names: tuple[str, ...] = (),
    uncertainty_empty: bool = False,
    human_decision_contract_ok: bool = False,
    synthetic_input_unchanged: bool = False,
    criteria_satisfied: tuple[str, ...] = (),
    notes: tuple[str, ...] = (),
) -> SmokeReport:
    report = SmokeReport(
        status=status,
        failure_category=failure_category,
        provider=DEEPSEEK_PROVIDER,
        model=DEEPSEEK_MODEL,
        endpoint=f"{DEEPSEEK_BASE_URL}{DEEPSEEK_RESPONSES_PATH}",
        request_count=counting.requests,
        http_status=counting.last_status,
        selection_parsed=selection_parsed,
        validator_accepted=validator_accepted,
        answer_kind=answer_kind,
        evidence_names=evidence_names,
        uncertainty_empty=uncertainty_empty,
        human_decision_contract_ok=human_decision_contract_ok,
        synthetic_input_unchanged=synthetic_input_unchanged,
        credential_not_leaked=True,
        criteria_satisfied=criteria_satisfied,
        timestamp=timestamp,
        commit_sha=commit_sha,
        notes=notes,
    )
    return replace(report, credential_not_leaked=not _unsanitized_strings(report))


def run_live_smoke(
    *,
    transport: HttpTransport | None = None,
    environ: Mapping[str, str] | None = None,
    commit_sha: str = "UNKNOWN",
    timestamp: str | None = None,
) -> SmokeReport:
    """Run the opt-in smoke once and return a credential-safe report.

    ``transport`` and ``environ`` exist so the automatic tests can prove the opt-in boundary
    (stub transport, fake environment) without any network access.  A real run uses the merged
    :class:`~snapshot_loader.deepseek_provider.StdlibHttpTransport` and the real process
    environment.  At most **one** request is ever sent.

    Caller-supplied metadata is validated here **before any egress**, for the CLI and the
    programmatic surface alike: an unsafe commit identifier or timestamp is rejected (no request,
    no credential resolution, fixed sanitized wording, non-zero exit) instead of being trusted
    into the report.
    """

    generated_stamp = _generated_timestamp()
    safe_sha = _safe_commit_sha(commit_sha)
    safe_stamp = generated_stamp if timestamp is None else _safe_timestamp(timestamp)
    counting = _CountingTransport(transport if transport is not None else StdlibHttpTransport())
    projection = synthetic_q3_projection()
    before = copy.deepcopy(projection)

    if safe_sha is None or safe_stamp is None:
        # Rejected before any egress: the supplied value is neither recorded nor echoed, and no
        # credential is resolved (the composition boundary is not reached at all).
        return _report(
            status=STATUS_FAIL,
            failure_category=CATEGORY_INVALID_METADATA,
            counting=counting,
            timestamp=generated_stamp,
            commit_sha=_UNKNOWN_COMMIT_SHA,
            synthetic_input_unchanged=projection == before,
            notes=(NOTE_INVALID_METADATA,),
        )

    stamp, commit_sha = safe_stamp, safe_sha

    # The credential is resolved only here, only from the process environment, and only by the
    # merged composition boundary; this script never reads the credential value (§7.1 S-2/S-3).
    provider = provider_from_environment(environ=environ, transport=counting)
    if isinstance(provider, UnavailableProvider):
        return _report(
            status=STATUS_NOT_RUN,
            failure_category=CATEGORY_CREDENTIAL_NOT_CONFIGURED,
            counting=counting,
            timestamp=stamp,
            commit_sha=commit_sha,
            synthetic_input_unchanged=projection == before,
            notes=(NOTE_CREDENTIAL_NOT_CONFIGURED,),
        )

    try:
        selection = provider.explain(projection)
    except ProviderUnavailable:
        return _report(
            status=STATUS_FAIL,
            failure_category=_failure_category(counting.last_status),
            counting=counting,
            timestamp=stamp,
            commit_sha=commit_sha,
            synthetic_input_unchanged=projection == before,
            notes=(NOTE_PROVIDER_FAILED,),
        )
    except Exception:  # noqa: BLE001 - any unexpected adapter failure is a smoke failure
        return _report(
            status=STATUS_FAIL,
            failure_category=CATEGORY_TRANSPORT_FAILURE,
            counting=counting,
            timestamp=stamp,
            commit_sha=commit_sha,
            synthetic_input_unchanged=projection == before,
            notes=(NOTE_UNEXPECTED_FAILURE,),
        )

    if not isinstance(selection, Mapping):
        return _report(
            status=STATUS_FAIL,
            failure_category=CATEGORY_UNEXPECTED_ENVELOPE,
            counting=counting,
            timestamp=stamp,
            commit_sha=commit_sha,
            synthetic_input_unchanged=projection == before,
        )

    raw_answer_kind = selection.get("answer_kind")
    # A provider-controlled string may enter the report only when it is a **registered** literal.
    # An unregistered (or credential-like) value is recorded as "not reported" instead of being
    # carried into the report, so the sanitized report can never echo provider-controlled text.
    answer_kind = raw_answer_kind if raw_answer_kind in ANSWER_KIND_LITERALS else None
    response = validate_provider_response(selection, projection)
    if response is None:
        return _report(
            status=STATUS_FAIL,
            failure_category=CATEGORY_VALIDATOR_REJECTED,
            counting=counting,
            timestamp=stamp,
            commit_sha=commit_sha,
            selection_parsed=True,
            answer_kind=answer_kind,
            synthetic_input_unchanged=projection == before,
            notes=(NOTE_VALIDATOR_REJECTED,),
        )

    evidence_names = tuple(line.partition(" = ")[0] for line in response.evidence)
    criteria: list[str] = []

    def check(name: str, satisfied: bool) -> None:
        if satisfied:
            criteria.append(name)

    check("exactly-one-request", counting.requests == 1)
    check("http-success", counting.last_status == 200)
    check("envelope-accepted-by-merged-parser", True)
    check("selection-parsed", True)
    check("validator-accepted", True)
    check("answer-kind-matches-synthetic-relation", answer_kind == EXPECTED_ANSWER_KIND)
    check("all-five-q3-facts-in-evidence", set(evidence_names) == set(Q3_FACT_FIELDS))
    check("uncertainty-empty", response.uncertainty == ())
    check(
        "human-decision-contract-preserved",
        response.human_decision_required == HUMAN_DECISION_REQUIRED_TEXT,
    )
    check("synthetic-input-unchanged", projection == before)
    check("credential-not-leaked", True)  # re-verified below on the assembled report

    common: dict[str, object] = {
        "counting": counting,
        "timestamp": stamp,
        "commit_sha": commit_sha,
        "selection_parsed": True,
        "validator_accepted": True,
        "answer_kind": answer_kind,
        "evidence_names": evidence_names,
        "uncertainty_empty": response.uncertainty == (),
        "human_decision_contract_ok": (
            response.human_decision_required == HUMAN_DECISION_REQUIRED_TEXT
        ),
        "synthetic_input_unchanged": projection == before,
    }

    if len(criteria) != len(PASS_CRITERIA):
        return _report(
            status=STATUS_FAIL,
            failure_category=CATEGORY_CRITERION_FAILED,
            criteria_satisfied=tuple(criteria),
            notes=(NOTE_CRITERIA_UNSATISFIED,),
            **common,
        )

    report = _report(
        status=STATUS_PASS,
        failure_category=None,
        criteria_satisfied=tuple(criteria),
        notes=(NOTE_PASS,),
        **common,
    )
    if not report.credential_not_leaked:
        # The fallback is rebuilt from fixed vocabulary only: it drops the dynamic provider
        # (``answer_kind`` ／ evidence names) and caller (commit ／ timestamp) strings entirely, so
        # the surfaced report cannot keep carrying whatever the check just rejected.
        return _report(
            status=STATUS_FAIL,
            failure_category=CATEGORY_UNSANITIZED_REPORT,
            counting=counting,
            timestamp=generated_stamp,
            commit_sha=_UNKNOWN_COMMIT_SHA,
            synthetic_input_unchanged=projection == before,
            notes=(NOTE_UNSANITIZED_REPORT,),
        )
    return report


def main(argv: Sequence[str] | None = None) -> int:
    """The opt-in CLI.  Returns ``0`` for PASS / NOT_RUN and ``1`` for FAIL."""

    parser = argparse.ArgumentParser(
        prog="deepseek_q3_live_smoke",
        description=(
            "Manual opt-in live smoke for the DeepSeek Q3 explanation path. Sends at most ONE "
            "real request, with fixed SIMULATED data only. The credential is resolved from the "
            "process environment by the merged composition boundary (no CLI flag, no file); "
            "importing this module performs no network I/O."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="print the credential-safe report as JSON instead of text",
    )
    parser.add_argument(
        "--commit-sha",
        default=os.environ.get("GITHUB_SHA", "UNKNOWN"),
        help=(
            "commit identifier recorded in the sanitized evidence: 'UNKNOWN' or a hex Git SHA "
            "(short or full). Any other value is rejected before any request is sent, is never "
            "recorded and is never echoed. Defaults to GITHUB_SHA."
        ),
    )
    arguments = parser.parse_args(argv)

    print(
        "opt-in live smoke: sending at most one request with fixed SIMULATED data only",
        file=sys.stderr,
    )
    report = run_live_smoke(commit_sha=arguments.commit_sha)
    if arguments.as_json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(report.render_text())
    return 1 if report.status == STATUS_FAIL else 0


if __name__ == "__main__":  # pragma: no cover - manual entry point
    sys.exit(main())
