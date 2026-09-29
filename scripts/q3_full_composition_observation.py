"""Manual opt-in operator tooling: one **full-composition** Q3 hosted observation.

What this is
------------

A **thin**, Human-operated, manual opt-in tool that drives the **already merged** Q3 runtime
end to end, exactly as the merged ``§9.3`` *Q3 per-observation AI Eval contract* defines the
observation unit:

``deterministic pipeline -> procurement recommendation -> Q3 projection -> one real hosted
provider call -> parser -> validator -> full explain_q3(...) composition -> final
ExplanationResult -> sanitized observation report``

The full composition is driven by :func:`snapshot_loader.explain_q3`; this tooling never
performs "provider -> validator -> artifact assembly" by hand, never copies the HTTP client, the
DeepSeek envelope parser, the validator or any procurement business logic, and never changes the
provider response.

What this is **not**
--------------------

Not AI Eval closure, not a provider / model quality measurement, not an accuracy, reliability,
stability or production-readiness claim, and not a PASS / FAIL verdict.  It records, for one
observation, which canonical Q3 AI behavior criteria were satisfied or violated, and nothing more.
Any number of observations still needs a future, separately authorized aggregate contract before
any quality statement may be made.

Opt-in and safety boundary
--------------------------

* importing this module performs **no** network I/O and no filesystem work;
* the credential is resolved **only** by the merged composition boundary
  (:func:`snapshot_loader.provider_from_environment`) from the **process environment**; this
  tooling never reads the credential value, has no ``--api-key`` flag and no credential file;
* a real observation **requires the exact 40-hex merged-main commit identifier** (``HD-C``): an
  omitted, ``UNKNOWN``, abbreviated or malformed ``--commit-sha`` never opens an egress path, is
  never echoed and is never recorded, and the tooling reports a sanitized failure record with exit
  code ``1``.  The tooling does not invoke git or any subprocess to verify repository membership;
  the identifier is operator-supplied;
* at most **one** hosted request is ever sent (no retry, no backoff, no provider switching, no
  fallback); a missing credential or a non-``COMPLETE`` projection results in **zero egress**;
* the recording transport forwards the body in memory to the merged adapter and keeps **no**
  copy: it records only whether a request was sent, whether a response was returned and the HTTP
  status.  Request headers are never read, copied, printed or persisted (``§7.1`` S-8);
* CI never executes this tooling and holds no real secret; the offline test suite injects a stub
  transport and a fake environment.

Fixture boundary
----------------

The deterministic input is a **fixed, self-contained SIMULATED fixture** built by this tooling
(synthetic records only, ``SIMULATED`` identities, no enterprise data, no package / run identity
in the report).  The business result is **computed by the existing pipeline** -- the fixture
states demand, inventory, safety stock and the MOQ policy, and the recommended purchase quantity
is whatever the registered rules derive, never a hard-coded business result.  With the fixed
numbers below the registered rules derive the canonical ``§2.5.9`` example
(``ShortageQty`` 30 / ``ApplicableMOQ`` 100 / ``RecommendedPurchaseQty`` 100 /
``MOQAdjustmentQty`` 70).

Usage
-----

::

    python scripts/q3_full_composition_observation.py --commit-sha <merged-main-sha>
    python scripts/q3_full_composition_observation.py --json --commit-sha <merged-main-sha>

``--commit-sha`` must be the **exact 40-hex** merged-main commit the observation is taken on;
omitting it (or passing ``UNKNOWN``, a short SHA or anything malformed) produces a sanitized
failure record with **zero egress** and exit code ``1``.

Exit code ``0`` means the tooling completed and produced a truthful sanitized record (whether or
not an AI behavior observation was formed); exit code ``1`` means the tooling could not produce a
truthful record (unsafe metadata, fixture not accepted, more than one request observed, or an
unsanitized report).
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from fractions import Fraction
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
    OUTCOME_EXPLAINED,
    OUTCOME_NO_RECOMMENDATION_BY_DESIGN,
    OUTCOME_PROVIDER_UNAVAILABLE,
    OUTCOME_RECOMMENDATION_INCOMPLETE,
    OUTCOME_RECOMMENDATION_UNAVAILABLE,
    OUTCOME_RESPONSE_UNACCEPTABLE,
    Q3_FACT_FIELDS,
    HttpTransport,
    PhaseAHandoff,
    ProviderUnavailable,
    StdlibHttpTransport,
    TrustedInputBoundary,
    build_q3_projection,
    explain_q3,
    load_package,
    provider_from_environment,
    run_first_tranche_pipeline,
)
from snapshot_loader.canonical_objects import (  # noqa: E402 - see above
    BomParentContextHandoff,
    EffectiveDemandRelationHandoff,
    HandoffEvidence,
    InventoryScopeHandoff,
    LossRateHandoff,
)

# --- fixture constants (fixed, SIMULATED, auditable) --------------------------------

#: Granularity of the fixed SIMULATED fixture.  ``SIM-`` identities make the boundary evident.
PLANT_ID: str = "SIM-P1"
MATERIAL_CODE: str = "SIM-M2"
SUBSTITUTE_MATERIAL_CODE: str = "SIM-M3"
REQUIRED_DATE: str = "2026-10-20"
SNAPSHOT_TIME: str = "2026-10-01T08:00:00Z"
ANALYSIS_RUN_ID: str = "SIMULATED-Q3-OBS-RUN"
ANALYSIS_DATE: str = "2026-10-01"
PACKAGE_ID: str = "SIMULATED-Q3-OBS-PKG-0001"
PACKAGE_CREATED_AT: str = "2026-10-01T08:00:00Z"

#: The fixture states demand / inventory / safety stock / MOQ only; every business quantity is
#: derived by the registered rules (``§2.4`` ／ ``§2.2`` ／ ``§2.5``).
DEMAND_QUANTITY: str = "130"
ON_HAND_QUANTITY: str = "100"
SAFETY_STOCK_QUANTITY: str = "5"
APPLICABLE_MOQ: str = "100"

ROLE_REQUIREMENT: str = "Production Requirement"
ROLE_BOM: str = "BOM Component"
ROLE_INVENTORY: str = "Inventory Snapshot"
ROLE_SAFETY_STOCK: str = "Configured Safety Stock"
ROLE_RELATIONSHIP: str = "Substitute Relationship"
ROLE_ALLOCATION: str = "Substitute Allocation"
ROLE_PROCUREMENT_POLICY_INPUT: str = "Procurement policy input"
ROLE_IDENTITY_CONTEXT: str = "Plant / Material identity context"

BASIS_SCOPE_IN: str = "SIMULATED-INV-SCOPE-A-IN"
BASIS_LOSS: str = "SIMULATED-BASIS-LOSS-RATE"
BASIS_MOQ_APPLICABLE: str = "SIMULATED-MOQ-APPLICABLE"
BASIS_TARGET_APPLICABLE: str = "SIMULATED-G5A-TA-APPLICABLE"
RELATION_TARGET: str = "Target Applicability"

ARTIFACT_REQUIREMENT: str = "0.json"
ARTIFACT_BOM: str = "1.json"
ARTIFACT_INVENTORY: str = "2.json"
ARTIFACT_SAFETY_STOCK: str = "3.json"
ARTIFACT_RELATIONSHIP: str = "4.json"
ARTIFACT_ALLOCATION: str = "5.json"
ARTIFACT_POLICY: str = "6.json"
ARTIFACT_IDENTITY: str = "7.json"

# --- report vocabulary (fixed prose; no AI Eval verdict token) ----------------------

MODE_HOSTED: str = "hosted"

ADMISSIBILITY_NO_MODEL_OUTPUT: str = (
    "no model/provider output: no AI behavior observation is formed; recorded as deterministic "
    "fail-closed / integration evidence only"
)
ADMISSIBILITY_RESPONSE_WITHOUT_SELECTION: str = (
    "provider response received, but no evaluable structured selection was formed: no Q3 AI "
    "behavior observation is formed; recorded as provider-format / parser / integration evidence "
    "only (the specific parser sub-reason is deliberately not inferred)"
)
ADMISSIBILITY_SELECTION_FORMED: str = (
    "a checkable structured selection was formed: this is a Q3 AI behavior observation, whether "
    "the merged validator accepted or rejected it"
)

NOTE_PROVIDER_NOT_INVOKED: str = "the provider seam was never called"
NOTE_NO_CREDENTIAL: str = "no provider credential was configured, so no request was sent"
NOTE_TRANSPORT_FAILURE: str = "the transport failed before any provider response was returned"
NOTE_HTTP_REJECTION: str = "the provider answered with a status that carries no usable model output"
NOTE_SELECTION_NOT_FORMED: str = (
    "a provider response was returned, but the merged adapter formed no structured selection"
)
NOTE_OBSERVATION_FORMED: str = "the merged adapter formed a structured selection"
NOTE_FIXTURE_NOT_ACCEPTED: str = "the fixed SIMULATED fixture package was not accepted"
NOTE_NO_RECOMMENDATION: str = "the deterministic result states no recommendation for this family"
NOTE_PROJECTION_INCOMPLETE: str = (
    "the Q3 projection is not COMPLETE, so no provider call was made and no AI behavior "
    "observation is formed"
)
NOTE_MECHANISM_ACCEPTED: str = "accepted by the merged validator mechanism"
NOTE_MECHANISM_REJECTED: str = "rejected by the merged validator mechanism"
NOTE_MECHANISM_NOT_REACHED: str = "the merged validator was not reached"
NOTE_SINGLE_REQUEST: str = "exactly one hosted request was observed"
NOTE_MULTIPLE_REQUESTS: str = (
    "more than one hosted request was observed, which the merged contract forbids"
)
NOTE_CREDENTIAL_OBSERVATION: str = (
    "credential leakage not observed in the sanitized tooling output (closed report schema; no "
    "header or body capture; no environment dump; the credential value is never read)"
)
NOTE_UNSANITIZED: str = (
    "the assembled record carried a string outside the permitted vocabulary, so it was withheld"
)
NOTE_UNREGISTERED_VALUE_PRESENT: str = "unregistered value present"
NOTE_ABSENT: str = "absent"
NOTE_NOT_EXPRESSIBLE: str = "not expressible under the selection contract"
NOTE_NOT_DETERMINED: str = "not determined"
NOTE_NOT_VIOLATED: str = "not violated in this observation"
NOTE_VIOLATED: str = "violated"
NOTE_MISMATCH: str = (
    "mismatch finding: the merged mechanism disposition and the canonical criterion mapping "
    "disagree; the canonical design is not modified to accommodate the implementation"
)
NOTE_COMMIT_PROVENANCE: str = (
    "operator-supplied commit identifier; the tooling does not locally verify repository membership"
)
NOTE_COMMIT_REQUIRED: str = (
    "a real hosted observation requires the exact 40-hex merged-main commit identifier, so no "
    "request was sent; an omitted, unknown, abbreviated or malformed identifier never opens an "
    "egress path and is never echoed or recorded"
)
NOTE_TIMESTAMP_INVALID: str = (
    "the supplied observation timestamp is not an ISO-8601 instant, so nothing was sent"
)

#: The fixed SIMULATED identity boundary this record always states.
SIMULATED_IDENTITY_BOUNDARY: str = (
    f"SIMULATED fixture identities only ({PLANT_ID} / {MATERIAL_CODE}); "
    "no package identity, no content-view digest, no Analysis Run identity, no enterprise data"
)

#: The registered Q3 quantities, in the order the rule registers them.
Q3_QUANTITY_ORDER: tuple[str, ...] = (
    "ShortageQty",
    "BasePurchaseNeed",
    "ApplicableMOQ",
    "MOQAdjustmentQty",
    "RecommendedPurchaseQty",
)

#: Canonical criterion names and their canonical authority (the oracle).  The merged validator and
#: registry are **mechanism / enforcement evidence only** and never the oracle.
CRITERIA: tuple[tuple[str, str], ...] = (
    ("evidence fidelity / Q3 role separation", "§5.3 Q3；§2.5.9；§5.6"),
    ("unsupported fact", "§5.7；§5.5"),
    ("deterministic / LLM boundary", "§5.12；§2.5.8"),
    ("human-decision boundary", "§5.5"),
    ("required evidence coverage", "§5.3 Q3；§2.5.8"),
    ("relation correctness", "§2.5.5；§2.5.8；§2.5.9"),
)

#: The only shapes an operator-supplied commit identifier may have, and the exact shape a **real
#: hosted observation** requires (``HD-C``: the durable record must bind the executed merged-main
#: commit).  The tooling never invokes git or any subprocess to verify repository membership.
_UNKNOWN_COMMIT: str = "UNKNOWN"
_COMMIT_PATTERN = re.compile(r"\A[0-9a-fA-F]{4,40}\Z")
_FULL_COMMIT_PATTERN = re.compile(r"\A[0-9a-fA-F]{40}\Z")
_TIMESTAMP_PATTERN = re.compile(
    r"\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})\Z"
)

EXIT_RECORD_PRODUCED: int = 0
EXIT_NO_TRUTHFUL_RECORD: int = 1


# --- fixed SIMULATED fixture --------------------------------------------------------


def _with_provenance(
    record: dict[str, Any], associations: list[tuple[str, list[str], str | None]]
) -> dict[str, Any]:
    """Attach the registered provenance associations of one synthetic record."""

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


def _encode(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8")


#: The fixed fixture datasets, in artifact order.  ``moq=None`` states no Phase B policy input,
#: which is how the offline tests exercise the non-COMPLETE guard without touching the runtime.
FIXTURE_DATASETS: tuple[tuple[str, str, str], ...] = (
    (ROLE_REQUIREMENT, ARTIFACT_REQUIREMENT, "simulated://q3-observation/requirement"),
    (ROLE_BOM, ARTIFACT_BOM, "simulated://q3-observation/bom"),
    (ROLE_INVENTORY, ARTIFACT_INVENTORY, "simulated://q3-observation/inventory"),
    (ROLE_SAFETY_STOCK, ARTIFACT_SAFETY_STOCK, "simulated://q3-observation/safety-stock"),
    (ROLE_RELATIONSHIP, ARTIFACT_RELATIONSHIP, "simulated://q3-observation/substitute-relationship"),
    (ROLE_ALLOCATION, ARTIFACT_ALLOCATION, "simulated://q3-observation/substitute-allocation"),
    (ROLE_PROCUREMENT_POLICY_INPUT, ARTIFACT_POLICY, "simulated://q3-observation/moq-policy"),
    (ROLE_IDENTITY_CONTEXT, ARTIFACT_IDENTITY, "simulated://q3-observation/identity"),
)


def fixture_records(*, moq: str | None = APPLICABLE_MOQ) -> dict[str, list[dict[str, Any]]]:
    """The fixed synthetic records, keyed by logical dataset role.

    Only the **inputs** are stated; every business quantity (requirement, inventory usability,
    shortage, MOQ adjustment, recommended purchase quantity) is derived by the existing rules.
    """

    requirement = _with_provenance(
        {
            "plant_id": PLANT_ID,
            "material_code": MATERIAL_CODE,
            "required_date": REQUIRED_DATE,
            "ProductionQty": DEMAND_QUANTITY,
        },
        [("ProductionQty", ["SIMULATED-SRC-REQ-0"], None)],
    )
    bom = _with_provenance(
        {
            "plant_id": PLANT_ID,
            "required_date": REQUIRED_DATE,
            "material_code": MATERIAL_CODE,
            "BOMComponentQty": "1",
            "loss_rate": "0",
        },
        [
            ("BOMComponentQty", ["SIMULATED-SRC-BOM-0"], None),
            ("loss_rate", ["SIMULATED-SRC-LOSS-0"], BASIS_LOSS),
        ],
    )
    inventory = _with_provenance(
        {
            "plant_id": PLANT_ID,
            "material_code": MATERIAL_CODE,
            "inventory_snapshot_time": SNAPSHOT_TIME,
            "inventory_status": "AVAILABLE",
            "on_hand_qty": ON_HAND_QUANTITY,
        },
        [("plant_id", [f"SIMULATED-SRC-INV-{MATERIAL_CODE}"], BASIS_SCOPE_IN)],
    )
    safety = _with_provenance(
        {
            "plant_id": PLANT_ID,
            "material_code": MATERIAL_CODE,
            "SafetyStock": SAFETY_STOCK_QUANTITY,
        },
        [("SafetyStock", [f"SIMULATED-SRC-SS-{MATERIAL_CODE}"], None)],
    )
    policy: list[dict[str, Any]] = []
    if moq is not None:
        policy.append(
            _with_provenance(
                {
                    "plant_id": PLANT_ID,
                    "material_code": MATERIAL_CODE,
                    "ApplicableMOQ": moq,
                },
                [
                    (
                        "ApplicableMOQ",
                        [f"SIMULATED-SRC-MOQ-{MATERIAL_CODE}"],
                        BASIS_MOQ_APPLICABLE,
                    )
                ],
            )
        )
    relationship = _with_provenance(
        {
            "plant_id": PLANT_ID,
            "target_material_code": MATERIAL_CODE,
            "substitute_material_code": SUBSTITUTE_MATERIAL_CODE,
            "substitution_ratio": "1.0",
            "approval_status": "APPROVED",
        },
        [("substitution_ratio", [f"SIMULATED-SRC-REL-{MATERIAL_CODE}"], None)],
    )
    allocation = _with_provenance(
        {
            "plant_id": PLANT_ID,
            "target_material_code": MATERIAL_CODE,
            "substitute_material_code": SUBSTITUTE_MATERIAL_CODE,
            "AllocatedSubstituteQty": "0",
        },
        [
            (
                "target_material_code",
                [f"SIMULATED-SRC-ALLOC-TA-{MATERIAL_CODE}"],
                BASIS_TARGET_APPLICABLE,
            )
        ],
    )
    identity = [{"plant_id": PLANT_ID, "material_code": MATERIAL_CODE}]
    return {
        ROLE_REQUIREMENT: [requirement],
        ROLE_BOM: [bom],
        ROLE_INVENTORY: [inventory],
        ROLE_SAFETY_STOCK: [safety],
        ROLE_RELATIONSHIP: [relationship],
        ROLE_ALLOCATION: [allocation],
        ROLE_PROCUREMENT_POLICY_INPUT: policy,
        ROLE_IDENTITY_CONTEXT: identity,
    }


def write_simulated_fixture(
    boundary_root: Path, *, moq: str | None = APPLICABLE_MOQ
) -> Path:
    """Materialise the fixed SIMULATED package under ``boundary_root`` and return its directory.

    The package is a direct child of the configured trusted boundary, as Layer-1 requires.  This
    writes **fixture data only**; it contains no business formula and no expected business result.
    """

    package_root = boundary_root / "q3-observation-package"
    package_root.mkdir(parents=True, exist_ok=True)
    records = fixture_records(moq=moq)
    entries: list[dict[str, Any]] = []
    for role, artifact, provenance_ref in FIXTURE_DATASETS:
        payload = _encode(records[role])
        (package_root / artifact).write_bytes(payload)
        entries.append(
            {
                "role": role,
                "artifact": artifact,
                "record_count": len(records[role]),
                "provenance_ref": provenance_ref,
                "integrity_evidence": hashlib.sha256(payload).hexdigest(),
            }
        )
    manifest = {
        "package": {
            "snapshot_package_id": PACKAGE_ID,
            "contract_version": "v0.2",
            "created_at": PACKAGE_CREATED_AT,
            "environment": "SIMULATED",
            "evidence_classification": "SIMULATED",
            "completeness_state": "COMPLETE",
        },
        "datasets": entries,
    }
    (package_root / "manifest.json").write_bytes(_encode(manifest))
    return package_root


def _cite(accepted: Any, role: str, artifact: str, ordinal: int = 0, locator: str | None = None):
    return HandoffEvidence(
        snapshot_package_identity=accepted.package_id,
        logical_dataset_role=role,
        artifact=artifact,
        record_ordinal=ordinal,
        evidence_locator=locator,
    )


def fixture_handoff(accepted: Any) -> PhaseAHandoff:
    """The registered Phase A in-process handoff of the fixed fixture (fixture data only)."""

    return PhaseAHandoff(
        analysis_run_id=ANALYSIS_RUN_ID,
        analysis_date=ANALYSIS_DATE,
        bom_parent_context=(
            BomParentContextHandoff(
                bom_evidence=_cite(accepted, ROLE_BOM, ARTIFACT_BOM, 0),
                parent_evidence=_cite(accepted, ROLE_REQUIREMENT, ARTIFACT_REQUIREMENT, 0),
            ),
        ),
        loss_rate=(
            LossRateHandoff(
                plant_id=PLANT_ID,
                parent_material_code=MATERIAL_CODE,
                required_date=REQUIRED_DATE,
                evidence=_cite(accepted, ROLE_BOM, ARTIFACT_BOM, 0),
                component_material_code=MATERIAL_CODE,
                loss_rate_evidence=(
                    _cite(accepted, ROLE_BOM, ARTIFACT_BOM, 0, "SIMULATED-SRC-LOSS-0"),
                ),
                loss_rate="0",
                resolution_basis=BASIS_LOSS,
            ),
        ),
        inventory_scope=(
            InventoryScopeHandoff(
                inventory_evidence=_cite(accepted, ROLE_INVENTORY, ARTIFACT_INVENTORY, 0),
                scope_observation="plant_id",
                scope_resolution_basis=BASIS_SCOPE_IN,
            ),
        ),
        effective_demand=(
            # One registered Target Applicability relation for this family's own demand context,
            # citing the accepted allocation record that states the basis it claims.
            EffectiveDemandRelationHandoff(
                source_substitute_material=SUBSTITUTE_MATERIAL_CODE,
                target_material=MATERIAL_CODE,
                relation=RELATION_TARGET,
                evidence=_cite(
                    accepted,
                    ROLE_ALLOCATION,
                    ARTIFACT_ALLOCATION,
                    0,
                    f"SIMULATED-SRC-ALLOC-TA-{MATERIAL_CODE}",
                ),
                mapping_basis=BASIS_TARGET_APPLICABLE,
                context_citation=_cite(accepted, ROLE_REQUIREMENT, ARTIFACT_REQUIREMENT, 0),
            ),
        ),
    )


def run_deterministic_chain(
    boundary_root: Path, *, moq: str | None = APPLICABLE_MOQ
) -> tuple[Any, Any]:
    """Accept the fixed SIMULATED package and run the **existing** pipeline over it.

    Returns ``(pipeline_result, import_report)``.  No business logic lives here: the records above
    are inputs, and every derived quantity comes from the registered rules.
    """

    package_root = write_simulated_fixture(boundary_root, moq=moq)
    report = load_package(
        package_root, trusted_boundary=TrustedInputBoundary(root=boundary_root)
    )
    if not report.accepted or report.accepted_package is None:
        return None, report
    return run_first_tranche_pipeline(report, fixture_handoff(report.accepted_package)), report


# --- observation seams (injected; no HTTP / parser / validator copy) ----------------


@dataclass
class TransportObservation:
    """What the transport seam itself can truthfully observe (never a body or a header)."""

    requests_sent: int = 0
    response_received: bool = False
    last_status: int | None = None


class RecordingTransport:
    """Wraps the merged transport to observe request / response / status only.

    The body is forwarded **in memory** to the merged adapter and never copied, printed, stored
    or persisted; headers are never read.  This wrapper implements no HTTP of its own and never
    retries, falls back or switches provider.
    """

    def __init__(self, inner: HttpTransport) -> None:
        self._inner = inner
        self.observation = TransportObservation()

    def send(self, request: Any) -> Any:
        self.observation.requests_sent += 1
        response = self._inner.send(request)
        self.observation.response_received = True
        self.observation.last_status = int(response.status)
        return response


@dataclass
class ProviderObservation:
    """What the provider seam can truthfully observe about one ``explain`` call."""

    called: int = 0
    selection_formed: bool = False
    selection: Mapping[str, Any] | None = None
    failure_type: str | None = None
    projection: Mapping[str, Any] | None = None


class RecordingProvider:
    """Wraps the merged provider to observe the selection it returns.

    The returned object is handed to :func:`explain_q3` **unchanged**: no repair, no sanitizing
    and no re-encoding on the way in.  Only the type name of a provider-side failure is kept (the
    message is deliberately dropped, ``§7.1`` S-8).
    """

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.observation = ProviderObservation()

    def explain(self, projection: Mapping[str, object]) -> object:
        self.observation.called += 1
        self.observation.projection = copy.deepcopy(dict(projection))
        try:
            raw = self._inner.explain(projection)
        except Exception as error:  # noqa: BLE001 - recorded as a type name only
            self.observation.failure_type = type(error).__name__
            raise
        if isinstance(raw, Mapping):
            self.observation.selection_formed = True
            self.observation.selection = raw
        return raw


# --- canonical criterion mapping (oracle = canonical authority, not the mechanism) ---


def _exact_text(payload: object) -> str | None:
    """The exact decimal text of a registered quantity payload (no rounding)."""

    if isinstance(payload, str):
        return payload or None
    if isinstance(payload, Mapping):
        numerator = payload.get("numerator")
        denominator = payload.get("denominator")
        if isinstance(numerator, int) and isinstance(denominator, int) and denominator > 0:
            return str(numerator) if denominator == 1 else f"{numerator}/{denominator}"
    return None


def _projected_quantities(projection: Mapping[str, object]) -> dict[str, str]:
    facts = projection.get("facts")
    values: dict[str, str] = {}
    if isinstance(facts, Mapping):
        for name in Q3_QUANTITY_ORDER:
            text = _exact_text(facts.get(name))
            if text is not None:
                values[name] = text
    return values


def _fraction(text: str | None) -> Fraction | None:
    if text is None:
        return None
    try:
        return Fraction(text)
    except (ValueError, ZeroDivisionError):
        return None


def _canonical_relation_holds(kind: str, values: Mapping[str, str]) -> bool | None:
    """``§2.5.5`` ／ ``§2.5.8`` ／ ``§2.5.9`` applied to the projection, or ``None`` if unmappable.

    This is the canonical relation oracle; it is deliberately independent of the merged
    validator so that a mechanism defect shows up as a **mismatch finding** instead of silently
    redefining the standard.
    """

    shortage = _fraction(values.get("ShortageQty"))
    recommended = _fraction(values.get("RecommendedPurchaseQty"))
    moq = _fraction(values.get("ApplicableMOQ"))
    if shortage is None or recommended is None or moq is None:
        return None
    if kind == "MOQ_RAISED_RECOMMENDATION_ABOVE_SHORTAGE":
        return shortage < recommended and recommended == moq
    if kind == "RECOMMENDATION_EQUALS_SHORTAGE":
        return recommended == shortage
    return None


@dataclass
class SanitizedSelection:
    """The sanitized four-key semantics of one formed selection (never raw provider content)."""

    answer_kind: str
    answer_kind_registered: bool
    evidence_names: tuple[str, ...]
    evidence_unknown_name_count: int
    evidence_is_list: bool
    uncertainty_entry_count: int
    uncertainty_is_list: bool
    human_decision_required: str
    extra_key_count: int


def sanitize_selection(selection: Mapping[str, Any]) -> SanitizedSelection:
    """Reduce a formed selection to sanitized, bounded semantics.

    Unregistered provider content is **never** persisted verbatim: an unregistered ``answer_kind``
    becomes prose, unknown evidence names are counted, and extra keys are counted.
    """

    raw_kind = selection.get("answer_kind")
    if isinstance(raw_kind, str) and raw_kind in ANSWER_KIND_LITERALS:
        kind, registered = raw_kind, True
    elif raw_kind is None:
        kind, registered = NOTE_ABSENT, False
    else:
        kind, registered = NOTE_UNREGISTERED_VALUE_PRESENT, False

    raw_evidence = selection.get("evidence")
    evidence_is_list = isinstance(raw_evidence, Sequence) and not isinstance(raw_evidence, str)
    names: list[str] = []
    unknown = 0
    if evidence_is_list:
        for item in raw_evidence:
            if isinstance(item, str) and item in Q3_FACT_FIELDS:
                if item not in names:
                    names.append(item)
            else:
                unknown += 1
    raw_uncertainty = selection.get("uncertainty")
    uncertainty_is_list = isinstance(raw_uncertainty, Sequence) and not isinstance(
        raw_uncertainty, str
    )
    uncertainty_count = len(raw_uncertainty) if uncertainty_is_list else 0

    raw_human = selection.get("human_decision_required")
    if raw_human is True:
        human = "boolean true"
    elif raw_human is False:
        human = "boolean false"
    else:
        human = "other type"

    extra_keys = len([key for key in selection if key not in (
        "answer_kind",
        "evidence",
        "uncertainty",
        "human_decision_required",
    )])
    return SanitizedSelection(
        answer_kind=kind,
        answer_kind_registered=registered,
        evidence_names=tuple(names),
        evidence_unknown_name_count=unknown,
        evidence_is_list=evidence_is_list,
        uncertainty_entry_count=uncertainty_count,
        uncertainty_is_list=uncertainty_is_list,
        human_decision_required=human,
        extra_key_count=extra_keys,
    )


def canonical_criteria(
    sanitized: SanitizedSelection, projection: Mapping[str, object]
) -> list[dict[str, str]]:
    """The per-criterion observation record, derived from canonical authority.

    ``violated`` / ``not violated in this observation`` are direct observations; ``not
    expressible under the selection contract`` records that this provider contract cannot express
    the violation at all (the provider selects, the runtime assembles the wording); ``not
    determined`` records that the observation cannot decide it.

    A mechanism-shape deviation (an extra key, an unknown evidence name, an unregistered answer
    kind) is **not** by itself proof of an unsupported business fact or of an LLM deciding
    deterministic business truth: this tooling deliberately keeps no arbitrary provider value, so
    the business semantics of such content cannot be read back.  Those deviations are therefore
    recorded as ``not determined`` on the unsupported-fact criterion, and the mechanism rejection
    is recorded separately -- never converted into a canonical violation to justify the mechanism.
    """

    values = _projected_quantities(projection)
    coverage_complete = set(sanitized.evidence_names) == set(Q3_FACT_FIELDS)
    relation = (
        _canonical_relation_holds(sanitized.answer_kind, values)
        if sanitized.answer_kind_registered
        else None
    )
    human_decision_ok = sanitized.human_decision_required == "boolean true"
    unregistered_kind = (
        sanitized.answer_kind != NOTE_ABSENT and not sanitized.answer_kind_registered
    )
    deviation = (
        sanitized.extra_key_count > 0
        or sanitized.evidence_unknown_name_count > 0
        or not sanitized.evidence_is_list
        or not sanitized.uncertainty_is_list
        or sanitized.uncertainty_entry_count > 0
        or unregistered_kind
        or not human_decision_ok
    )
    #: A canonical unsupported-business-fact assertion is provable only from retained evidence that
    #: identifies the asserted business meaning.  This contract retains shape facts only, so the
    #: condition is deliberately not derivable from a deviation alone.
    unsupported_fact_provable = False

    records: list[dict[str, str]] = []
    for name, authority in CRITERIA:
        if name == "evidence fidelity / Q3 role separation":
            result = NOTE_NOT_EXPRESSIBLE
            evidence = (
                "the provider selection carries no quantity value and no role: the runtime "
                "assembles the answer, so a mutated value or a swapped role cannot be expressed; "
                "the canonical negative reading (ShortageQty 30 / RecommendedPurchaseQty 100 must "
                "not read as an actual shortage of 100) therefore cannot be violated through this "
                "contract"
            )
        elif name == "unsupported fact":
            if unsupported_fact_provable:
                result = NOTE_VIOLATED
                evidence = "the sanitized observation proves a specific unsupported business assertion"
            elif deviation:
                result = NOTE_NOT_DETERMINED
                evidence = (
                    f"a mechanism-shape deviation was observed (extra key count "
                    f"{sanitized.extra_key_count}; unknown evidence name count "
                    f"{sanitized.evidence_unknown_name_count}; answer_kind "
                    f"{sanitized.answer_kind}), but this record keeps no arbitrary provider value, "
                    "so no specific unsupported business fact, guessed reason, model inference, "
                    "approval claim or fabricated quantity/status can be proven from it"
                )
            else:
                result = NOTE_NOT_VIOLATED
                evidence = (
                    "no deviation from the registered selection vocabulary was observed, so no "
                    "unsupported business fact was observed to enter the explanation"
                )
        elif name == "deterministic / LLM boundary":
            if unsupported_fact_provable:
                result = NOTE_VIOLATED
                evidence = "a proven unsupported business assertion would mean the LLM supplied a deterministic fact"
            else:
                result = NOTE_NOT_EXPRESSIBLE
                evidence = (
                    "no business quantity, status or relation is expressible in a selection; the "
                    "registered quantities come from the deterministic projection and are rendered "
                    "by the runtime, so an LLM-decided deterministic truth cannot be expressed here "
                    "(a wrong registered relation is recorded under relation correctness instead)"
                )
        elif name == "human-decision boundary":
            result = NOTE_VIOLATED if not human_decision_ok else NOTE_NOT_VIOLATED
            evidence = f"human_decision_required = {sanitized.human_decision_required}"
        elif name == "required evidence coverage":
            result = NOTE_VIOLATED if not coverage_complete else NOTE_NOT_VIOLATED
            evidence = (
                f"registered evidence names {list(sanitized.evidence_names)} of the five required "
                f"quantities"
            )
        else:  # relation correctness
            if relation is None:
                result = NOTE_NOT_DETERMINED
                evidence = "no canonical relation is mappable for this selection"
            else:
                result = NOTE_VIOLATED if not relation else NOTE_NOT_VIOLATED
                evidence = (
                    f"kind {sanitized.answer_kind}; canonical relation holds = {bool(relation)}; "
                    f"projected quantities {values}"
                )
        records.append(
            {
                "criterion": name,
                "canonical_authority": authority,
                "observed_evidence": evidence,
                "result": result,
            }
        )
    return records


# --- metadata validation (before any egress) ----------------------------------------


def _safe_commit(value: object) -> str | None:
    """The value when it is a well-shaped commit identifier (used by the report sanitizer)."""

    if not isinstance(value, str):
        return None
    if value == _UNKNOWN_COMMIT:
        return value
    return value if _COMMIT_PATTERN.match(value) is not None else None


def _egress_commit(value: object) -> str | None:
    """The value only when it is the exact 40-hex identifier a real observation requires."""

    if not isinstance(value, str):
        return None
    return value if _FULL_COMMIT_PATTERN.match(value) is not None else None


def _safe_timestamp(value: object) -> str | None:
    if not isinstance(value, str) or _TIMESTAMP_PATTERN.match(value) is None:
        return None
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return None
    return value


def _generated_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --- the observation ----------------------------------------------------------------


@dataclass
class ObservationRecord:
    """The sanitized durable record of one attempted observation."""

    commit_under_test: str
    commit_provenance: str
    observation_timestamp: str
    provider: str
    model: str
    endpoint: str
    execution_mode: str
    simulated_identity_boundary: str
    q3_grain: dict[str, object]
    projection_quantities: dict[str, str] | None
    projection_completeness_state: str | None
    provider_invoked: bool
    request_count: int
    provider_response_received: bool
    structured_selection_formed: bool
    http_status: int | None
    mechanism_validator_disposition: str
    final_runtime_outcome: str | None
    deterministic_recommendation_unchanged: bool
    credential_leakage_observation: str
    observation_admissibility: str
    selection: dict[str, object] | None
    canonical_criteria: list[dict[str, str]] = field(default_factory=list)
    mismatch_findings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "commit_under_test": self.commit_under_test,
            "commit_provenance": self.commit_provenance,
            "observation_timestamp": self.observation_timestamp,
            "provider": self.provider,
            "model": self.model,
            "endpoint": self.endpoint,
            "execution_mode": self.execution_mode,
            "simulated_identity_boundary": self.simulated_identity_boundary,
            "q3_grain": self.q3_grain,
            "projection_quantities": self.projection_quantities,
            "projection_completeness_state": self.projection_completeness_state,
            "provider_invoked": self.provider_invoked,
            "request_count": self.request_count,
            "provider_response_received": self.provider_response_received,
            "structured_selection_formed": self.structured_selection_formed,
            "http_status": self.http_status,
            "mechanism_validator_disposition": self.mechanism_validator_disposition,
            "final_runtime_outcome": self.final_runtime_outcome,
            "deterministic_recommendation_unchanged": self.deterministic_recommendation_unchanged,
            "credential_leakage_observation": self.credential_leakage_observation,
            "observation_admissibility": self.observation_admissibility,
            "selection": self.selection,
            "canonical_criteria": [dict(item) for item in self.canonical_criteria],
            "mismatch_findings": list(self.mismatch_findings),
            "notes": list(self.notes),
        }

    def render_text(self) -> str:
        lines = [
            f"commit under test        : {self.commit_under_test}（{self.commit_provenance}）",
            f"observation timestamp    : {self.observation_timestamp}",
            f"provider / model         : {self.provider} / {self.model}",
            f"endpoint                 : {self.endpoint}",
            f"execution mode           : {self.execution_mode}",
            f"SIMULATED identity       : {self.simulated_identity_boundary}",
            f"Q3 grain                 : {json.dumps(self.q3_grain, ensure_ascii=False, sort_keys=True)}",
            f"projection completeness  : {self.projection_completeness_state or '-'}",
            f"projected quantities     : {json.dumps(self.projection_quantities, ensure_ascii=False, sort_keys=True)}",
            f"provider invoked         : {self.provider_invoked}",
            f"request count            : {self.request_count}",
            f"provider response        : {self.provider_response_received}",
            f"structured selection     : {self.structured_selection_formed}",
            f"http status              : {self.http_status if self.http_status is not None else '-'}",
            f"mechanism disposition    : {self.mechanism_validator_disposition}",
            f"final runtime outcome    : {self.final_runtime_outcome or '-'}",
            f"recommendation unchanged : {self.deterministic_recommendation_unchanged}",
            "",
            f"admissibility            : {self.observation_admissibility}",
        ]
        if self.selection is not None:
            lines.append(
                "sanitized selection      : "
                + json.dumps(self.selection, ensure_ascii=False, sort_keys=True)
            )
        for item in self.canonical_criteria:
            lines.append(
                f"criterion                : {item['criterion']} | {item['result']} | "
                f"{item['canonical_authority']} | {item['observed_evidence']}"
            )
        for finding in self.mismatch_findings:
            lines.append(f"mismatch finding         : {finding}")
        lines.append(f"credential observation   : {self.credential_leakage_observation}")
        for note in self.notes:
            lines.append(f"note                     : {note}")
        return "\n".join(lines)


def _string_values(value: object) -> list[str]:
    found: list[str] = []
    if isinstance(value, str):
        found.append(value)
    elif isinstance(value, Mapping):
        for item in value.values():
            found.extend(_string_values(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            found.extend(_string_values(item))
    return found


def _permitted_strings(record: ObservationRecord) -> set[str]:
    """Fixed vocabulary plus the validated dynamic identifiers this record may carry."""

    permitted = {
        text
        for text in (
            MODE_HOSTED,
            SIMULATED_IDENTITY_BOUNDARY,
            ADMISSIBILITY_NO_MODEL_OUTPUT,
            ADMISSIBILITY_RESPONSE_WITHOUT_SELECTION,
            ADMISSIBILITY_SELECTION_FORMED,
            NOTE_PROVIDER_NOT_INVOKED,
            NOTE_NO_CREDENTIAL,
            NOTE_TRANSPORT_FAILURE,
            NOTE_HTTP_REJECTION,
            NOTE_SELECTION_NOT_FORMED,
            NOTE_OBSERVATION_FORMED,
            NOTE_FIXTURE_NOT_ACCEPTED,
            NOTE_NO_RECOMMENDATION,
            NOTE_PROJECTION_INCOMPLETE,
            NOTE_MECHANISM_ACCEPTED,
            NOTE_MECHANISM_REJECTED,
            NOTE_MECHANISM_NOT_REACHED,
            NOTE_SINGLE_REQUEST,
            NOTE_MULTIPLE_REQUESTS,
            NOTE_CREDENTIAL_OBSERVATION,
            NOTE_UNREGISTERED_VALUE_PRESENT,
            NOTE_UNSANITIZED,
            NOTE_ABSENT,
            NOTE_NOT_EXPRESSIBLE,
            NOTE_NOT_DETERMINED,
            NOTE_NOT_VIOLATED,
            NOTE_VIOLATED,
            NOTE_COMMIT_PROVENANCE,
            NOTE_COMMIT_REQUIRED,
            NOTE_TIMESTAMP_INVALID,
            _UNKNOWN_COMMIT,
            DEEPSEEK_PROVIDER,
            DEEPSEEK_MODEL,
            f"{DEEPSEEK_BASE_URL}{DEEPSEEK_RESPONSES_PATH}",
            PLANT_ID,
            MATERIAL_CODE,
            REQUIRED_DATE,
            "COMPLETE",
            "DATA_INCOMPLETE",
            "RECOMMENDATION_NOT_STATED",
            "boolean true",
            "boolean false",
            "other type",
            "no observation",
            "observation formed",
        )
    }
    permitted |= set(ANSWER_KIND_LITERALS)
    permitted |= set(Q3_FACT_FIELDS)
    permitted |= {
        OUTCOME_EXPLAINED,
        OUTCOME_NO_RECOMMENDATION_BY_DESIGN,
        OUTCOME_RECOMMENDATION_UNAVAILABLE,
        OUTCOME_RECOMMENDATION_INCOMPLETE,
        OUTCOME_PROVIDER_UNAVAILABLE,
        OUTCOME_RESPONSE_UNACCEPTABLE,
    }
    permitted |= {name for name, _authority in CRITERIA}
    permitted |= {authority for _name, authority in CRITERIA}
    permitted |= {item["observed_evidence"] for item in record.canonical_criteria}
    permitted |= set(record.notes)
    permitted |= set(record.mismatch_findings)
    permitted |= set(record.projection_quantities or {})
    permitted |= set((record.projection_quantities or {}).values())
    if _safe_commit(record.commit_under_test) is not None:
        permitted.add(record.commit_under_test)
    if _safe_timestamp(record.observation_timestamp) is not None:
        permitted.add(record.observation_timestamp)
    return permitted


def _unsanitized_strings(record: ObservationRecord) -> tuple[str, ...]:
    permitted = _permitted_strings(record)
    return tuple(text for text in _string_values(record.to_dict()) if text not in permitted)


def run_observation(
    *,
    transport: HttpTransport | None = None,
    environ: Mapping[str, str] | None = None,
    commit_sha: str = _UNKNOWN_COMMIT,
    timestamp: str | None = None,
    moq: str | None = APPLICABLE_MOQ,
    boundary_root: Path | None = None,
) -> tuple[ObservationRecord, int]:
    """Run one attempted observation and return ``(record, exit_code)``.

    ``transport``, ``environ``, ``moq`` and ``boundary_root`` exist so the offline tests can drive
    every admissibility branch without any network access or real credential.  A real run uses the
    merged :class:`~snapshot_loader.StdlibHttpTransport` and the real process environment.
    """

    generated = _generated_timestamp()
    egress_commit = _egress_commit(commit_sha)
    safe_stamp = generated if timestamp is None else _safe_timestamp(timestamp)
    if egress_commit is None or safe_stamp is None:
        # No egress path is opened: an omitted, unknown, abbreviated or malformed commit identifier
        # never reaches the provider, is never echoed and is never recorded.
        record = ObservationRecord(
            commit_under_test=_UNKNOWN_COMMIT,
            commit_provenance=NOTE_COMMIT_PROVENANCE,
            observation_timestamp=generated,
            provider=DEEPSEEK_PROVIDER,
            model=DEEPSEEK_MODEL,
            endpoint=f"{DEEPSEEK_BASE_URL}{DEEPSEEK_RESPONSES_PATH}",
            execution_mode=MODE_HOSTED,
            simulated_identity_boundary=SIMULATED_IDENTITY_BOUNDARY,
            q3_grain={"plant_id": PLANT_ID, "material_code": MATERIAL_CODE},
            projection_quantities=None,
            projection_completeness_state=None,
            provider_invoked=False,
            request_count=0,
            provider_response_received=False,
            structured_selection_formed=False,
            http_status=None,
            mechanism_validator_disposition=NOTE_MECHANISM_NOT_REACHED,
            final_runtime_outcome=None,
            deterministic_recommendation_unchanged=True,
            credential_leakage_observation=NOTE_CREDENTIAL_OBSERVATION,
            observation_admissibility=ADMISSIBILITY_NO_MODEL_OUTPUT,
            selection=None,
            notes=(
                NOTE_COMMIT_REQUIRED
                if egress_commit is None
                else NOTE_TIMESTAMP_INVALID,
            ),
        )
        return record, EXIT_NO_TRUTHFUL_RECORD

    transport_observation = RecordingTransport(
        transport if transport is not None else StdlibHttpTransport()
    )
    with tempfile.TemporaryDirectory(prefix="q3-observation-") as scratch:
        boundary = boundary_root if boundary_root is not None else Path(scratch)
        pipeline, import_report = run_deterministic_chain(boundary, moq=moq)

        if pipeline is None:
            record = _no_egress_record(
                egress_commit, safe_stamp, transport_observation,
                notes=(NOTE_FIXTURE_NOT_ACCEPTED,), admissibility=ADMISSIBILITY_NO_MODEL_OUTPUT,
            )
            return record, EXIT_NO_TRUTHFUL_RECORD

        recommendations = pipeline.procurement_recommendation
        recommendation = recommendations.for_family(PLANT_ID, MATERIAL_CODE)
        if recommendation is None:
            record = _no_egress_record(
                egress_commit, safe_stamp, transport_observation,
                notes=(NOTE_NO_RECOMMENDATION,), admissibility=ADMISSIBILITY_NO_MODEL_OUTPUT,
            )
            return record, EXIT_RECORD_PRODUCED

        before = copy.deepcopy(recommendation.to_dict())
        projection = build_q3_projection(recommendation)
        completeness = projection.get("completeness")
        state = completeness.get("state") if isinstance(completeness, Mapping) else None
        quantities = _projected_quantities(projection)

        if state != "COMPLETE":
            # Zero egress: the merged runtime would not call a provider for a non-COMPLETE
            # projection, and neither does this tooling.
            record = _no_egress_record(
                egress_commit, safe_stamp, transport_observation,
                notes=(NOTE_PROJECTION_INCOMPLETE,),
                admissibility=ADMISSIBILITY_NO_MODEL_OUTPUT,
            )
            record.projection_completeness_state = state if isinstance(state, str) else None
            record.projection_quantities = quantities
            return record, EXIT_RECORD_PRODUCED

        provider = RecordingProvider(
            provider_from_environment(environ=environ, transport=transport_observation)
        )
        result = explain_q3(
            recommendations, provider, plant_id=PLANT_ID, material_code=MATERIAL_CODE
        )
        after = recommendation.to_dict()

    observation = transport_observation.observation
    provider_observation = provider.observation
    admissibility, notes = _admissibility(
        observation, provider_observation, transport_observation
    )

    if result.outcome == OUTCOME_EXPLAINED:
        disposition = NOTE_MECHANISM_ACCEPTED
    elif result.outcome == OUTCOME_RESPONSE_UNACCEPTABLE:
        disposition = NOTE_MECHANISM_REJECTED
    elif result.outcome == OUTCOME_PROVIDER_UNAVAILABLE:
        disposition = NOTE_MECHANISM_NOT_REACHED
    else:
        disposition = NOTE_MECHANISM_NOT_REACHED

    selection_record: dict[str, object] | None = None
    criteria: list[dict[str, str]] = []
    mismatches: list[str] = []
    if provider_observation.selection_formed and provider_observation.selection is not None:
        sanitized = sanitize_selection(provider_observation.selection)
        criteria = canonical_criteria(sanitized, projection)
        selection_record = {
            "answer_kind": sanitized.answer_kind,
            "evidence_names": list(sanitized.evidence_names),
            "evidence_unknown_name_count": sanitized.evidence_unknown_name_count,
            "evidence_is_list": sanitized.evidence_is_list,
            "uncertainty_entry_count": sanitized.uncertainty_entry_count,
            "uncertainty_is_list": sanitized.uncertainty_is_list,
            "human_decision_required": sanitized.human_decision_required,
            "extra_key_count": sanitized.extra_key_count,
        }
        observed_violation = any(item["result"] == NOTE_VIOLATED for item in criteria)
        if result.outcome == OUTCOME_RESPONSE_UNACCEPTABLE and not observed_violation:
            mismatches.append(
                NOTE_MISMATCH
                + ": the merged mechanism rejected the selection while the canonical criterion "
                "mapping found no violation among the recorded criteria; the mechanism may "
                "additionally enforce registered slice constraints that are not among those six "
                "criteria (for example the §5.20 constraint that uncertainty must be empty), so "
                "this is recorded as an observation-level disagreement, not as a defect of either side"
            )
        if result.outcome == OUTCOME_EXPLAINED and observed_violation:
            mismatches.append(
                NOTE_MISMATCH
                + ": the merged mechanism accepted the selection while the canonical criterion "
                "mapping observed a violation"
            )
    else:
        notes = notes + (
            "no structured selection exists, so no canonical criterion can be evaluated",
        )

    if observation.requests_sent == 1:
        notes = notes + (NOTE_SINGLE_REQUEST,)
    elif observation.requests_sent > 1:
        notes = notes + (NOTE_MULTIPLE_REQUESTS,)

    record = ObservationRecord(
        commit_under_test=egress_commit,
        commit_provenance=NOTE_COMMIT_PROVENANCE,
        observation_timestamp=safe_stamp,
        provider=DEEPSEEK_PROVIDER,
        model=DEEPSEEK_MODEL,
        endpoint=f"{DEEPSEEK_BASE_URL}{DEEPSEEK_RESPONSES_PATH}",
        execution_mode=MODE_HOSTED,
        simulated_identity_boundary=SIMULATED_IDENTITY_BOUNDARY,
        q3_grain={
            "plant_id": projection.get("grain", {}).get("plant_id")  # type: ignore[union-attr]
            if isinstance(projection.get("grain"), Mapping)
            else None,
            "material_code": projection.get("grain", {}).get("material_code")  # type: ignore[union-attr]
            if isinstance(projection.get("grain"), Mapping)
            else None,
            "RecommendationNeedDate": projection.get("grain", {}).get("RecommendationNeedDate")  # type: ignore[union-attr]
            if isinstance(projection.get("grain"), Mapping)
            else None,
        },
        projection_quantities=quantities,
        projection_completeness_state=state if isinstance(state, str) else None,
        provider_invoked=provider_observation.called > 0,
        request_count=observation.requests_sent,
        provider_response_received=observation.response_received,
        structured_selection_formed=provider_observation.selection_formed,
        http_status=observation.last_status,
        mechanism_validator_disposition=disposition,
        final_runtime_outcome=result.outcome,
        deterministic_recommendation_unchanged=before == after,
        credential_leakage_observation=NOTE_CREDENTIAL_OBSERVATION,
        observation_admissibility=admissibility,
        selection=selection_record,
        canonical_criteria=criteria,
        mismatch_findings=mismatches,
        notes=list(notes),
    )

    exit_code = EXIT_RECORD_PRODUCED
    if observation.requests_sent > 1:
        exit_code = EXIT_NO_TRUTHFUL_RECORD
    if _unsanitized_strings(record):
        record.notes = list(record.notes) + [NOTE_UNSANITIZED]
        record.credential_leakage_observation = NOTE_UNSANITIZED
        exit_code = EXIT_NO_TRUTHFUL_RECORD
    return record, exit_code


def _admissibility(
    observation: TransportObservation,
    provider_observation: ProviderObservation,
    transport: RecordingTransport,
) -> tuple[str, tuple[str, ...]]:
    """Classify the attempt into the merged contract's three admissibility layers."""

    if provider_observation.called == 0:
        return ADMISSIBILITY_NO_MODEL_OUTPUT, (NOTE_PROVIDER_NOT_INVOKED,)
    if observation.requests_sent == 0:
        # The provider seam was called but no request left the process.
        return ADMISSIBILITY_NO_MODEL_OUTPUT, (NOTE_NO_CREDENTIAL,)
    if not observation.response_received:
        return ADMISSIBILITY_NO_MODEL_OUTPUT, (NOTE_TRANSPORT_FAILURE,)
    status = observation.last_status
    if status != 200:
        return ADMISSIBILITY_NO_MODEL_OUTPUT, (NOTE_HTTP_REJECTION,)
    if not provider_observation.selection_formed:
        return ADMISSIBILITY_RESPONSE_WITHOUT_SELECTION, (NOTE_SELECTION_NOT_FORMED,)
    return ADMISSIBILITY_SELECTION_FORMED, (NOTE_OBSERVATION_FORMED,)


def _no_egress_record(
    commit: str,
    stamp: str,
    transport: RecordingTransport,
    *,
    notes: tuple[str, ...],
    admissibility: str,
) -> ObservationRecord:
    """A sanitized record for a branch that must not (and did not) open an egress path."""

    return ObservationRecord(
        commit_under_test=commit,
        commit_provenance=NOTE_COMMIT_PROVENANCE,
        observation_timestamp=stamp,
        provider=DEEPSEEK_PROVIDER,
        model=DEEPSEEK_MODEL,
        endpoint=f"{DEEPSEEK_BASE_URL}{DEEPSEEK_RESPONSES_PATH}",
        execution_mode=MODE_HOSTED,
        simulated_identity_boundary=SIMULATED_IDENTITY_BOUNDARY,
        q3_grain={"plant_id": PLANT_ID, "material_code": MATERIAL_CODE},
        projection_quantities=None,
        projection_completeness_state=None,
        provider_invoked=transport.observation.requests_sent > 0,
        request_count=transport.observation.requests_sent,
        provider_response_received=transport.observation.response_received,
        structured_selection_formed=False,
        http_status=transport.observation.last_status,
        mechanism_validator_disposition=NOTE_MECHANISM_NOT_REACHED,
        final_runtime_outcome=None,
        deterministic_recommendation_unchanged=True,
        credential_leakage_observation=NOTE_CREDENTIAL_OBSERVATION,
        observation_admissibility=admissibility,
        selection=None,
        notes=list(notes),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """The opt-in CLI.  ``0`` = a truthful record was produced; ``1`` = it was not."""

    parser = argparse.ArgumentParser(
        prog="q3_full_composition_observation",
        description=(
            "Manual opt-in Q3 full-composition hosted observation. Sends at most ONE hosted "
            "request with a fixed SIMULATED fixture, drives the merged explain_q3(...) "
            "composition, and prints a sanitized record. The credential is resolved from the "
            "process environment by the merged composition boundary (no CLI flag, no file); "
            "importing this module performs no network or filesystem work."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="print the sanitized record as JSON instead of text",
    )
    parser.add_argument(
        "--commit-sha",
        default=_UNKNOWN_COMMIT,
        help=(
            "the exact 40-hex merged-main commit the observation is taken on. This is REQUIRED for "
            "a real observation: omitted, 'UNKNOWN', an abbreviated SHA or any malformed value "
            "produces a sanitized failure record with zero egress and exit code 1, and is never "
            "echoed. The tooling does not verify repository membership."
        ),
    )
    arguments = parser.parse_args(argv)

    print(
        "manual opt-in observation: at most one hosted request with a fixed SIMULATED fixture",
        file=sys.stderr,
    )
    record, exit_code = run_observation(commit_sha=arguments.commit_sha)
    if arguments.as_json:
        print(json.dumps(record.to_dict(), indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(record.render_text())
    return exit_code


if __name__ == "__main__":  # pragma: no cover - manual entry point
    sys.exit(main())
