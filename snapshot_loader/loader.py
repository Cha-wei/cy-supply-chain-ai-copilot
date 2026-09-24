"""Controlled Snapshot package loading and Layer-1 package acceptance.

This module implements the **authoritative acceptance gate** registered in
``snapshot-import-contract.md`` §4.3.28 ``D4`` -- and nothing beyond it.

Registered partial order (``D4.1`` / ``D4.2`` / ``D4.3`` / ``D4.4``)::

    trusted input boundary established                       (D.3 IG-self-C)
      -> manifest readable
      -> strict JSON parse                                   (IC-8)
      -> required manifest structure / identity /
         contract_version determinable                       (IC-14 / IC-16)
      -> version exact-match gate                            (VC-1, "v0.2")
      -> applicable contract / known member set determined
      -> manifest + dataset-entry unknown-content checks      (UX-A reject)
      -> role / cardinality / artifact reference / path checks (IC-1 / IC-3 / IC-2 / PN-1)
      -> declared artifact existence / readability            (IC-14)
      -> artifact-level checks: raw-byte SHA-256 then strict parse,
         record carrier / canonical field / "_meta" shape,
         record_count consistency                             (D4.2 / D4.3)
      -> every acceptance-producing result bound to the same stable content view (10A)

Layer-1 scope is deliberately narrow.  The known-property check answers only whether
a direct record property is a known v0.2 canonical property (``§4.3.30`` C.1).  It
does **not** evaluate requiredness, logical value validity, business applicability,
per-role field applicability, capability readiness, semantic resolution, or
source/runtime/derived legitimacy -- all of which remain Layer 2--4 (``§4.3.30``
C.2/C.3, ``IC-17``).  No Layer-2 defect may be promoted into a package rejection.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from .constants import (
    ASSOCIATION_MEMBERS,
    CONTRACT_VERSION_PROPERTY,
    DATASET_ENTRY_PROPERTIES,
    DISPOSITION_ACCEPTED,
    DISPOSITION_REJECTED,
    EVALUATION_NOT_EVALUABLE,
    GROUPING_DATASETS,
    GROUPING_PACKAGE,
    INTEGRITY_EVIDENCE_LENGTH,
    INTEGRITY_HEX_DIGITS,
    MANDATORY_LAYER1_CHECKS,
    MANIFEST_FILENAME,
    MANIFEST_TOP_LEVEL_PROPERTIES,
    META_MEMBERS,
    OPTIONAL_ASSOCIATION_MEMBERS,
    PACKAGE_SCOPED_PROPERTIES,
    RECORD_META_NAMESPACE,
    REQUIRED_ASSOCIATION_MEMBERS,
    REQUIRED_DATASET_ENTRY_PROPERTIES,
    REQUIRED_PACKAGE_BLOCK_PROPERTIES,
    SUPPORTED_CONTRACT_VERSION,
    V02_CANONICAL_RECORD_PROPERTY_SET,
)
from .issues import IssueCollector
from .path_scope import (
    FilenameRejection,
    path_is_unrepresentable,
    physical_identity,
    resolved_within,
    validate_artifact_filename,
)
from .report import ImportReport
from .strict_json import JsonObject, StrictJsonError, parse_strict_json
from .trust import (
    AcceptedPackage,
    ContentView,
    FileView,
    TrustedInputBoundary,
    compute_view_digest,
    list_root_entries,
    read_file_bytes,
)

_MANIFEST_DESIGN_REFERENCE = "§4.3.25 A/B + §4.3.28 A.1/A.2 + D4.1"
_RECORD_DESIGN_REFERENCE = "§4.3.25 D/E/F/G + §4.3.28 E + §4.3.30"
_INTEGRITY_DESIGN_REFERENCE = "§4.3.28 D (IG-raw, IG-rep-A) + IC-22"

RECORD_PROPERTY_SET_CHECK = "artifact.record_property_known_set"


@dataclass(frozen=True, slots=True)
class _DatasetEntry:
    index: int
    role: str
    artifact: str
    record_count: int
    declared_integrity: str
    declared_integrity_text: str


class _BlockedAcceptance(Exception):
    """Raised when a prerequisite blocks the remaining acceptance checks."""

    def __init__(self, collector: IssueCollector, basis: str) -> None:
        super().__init__(basis)
        self.collector = collector
        self.basis = basis


def _is_plain_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _as_record_count(value: object) -> int | None:
    """Return ``record_count`` as ``int`` when the JSON literal is an integer.

    Strict parsing yields :class:`~decimal.Decimal` for every JSON number so that no
    binary floating point is introduced (``C-5`` / ``IC-10``).  A count is accepted
    only when the literal is integral: fractional or exponent-scaled counts are
    rejected rather than coerced, because ``PN-1``/``C-9`` forbid silent numeric
    coercion.
    """

    if _is_plain_int(value):
        return int(value)
    if isinstance(value, Decimal):
        if not value.is_finite():
            return None
        exponent = value.as_tuple().exponent
        if isinstance(exponent, int) and exponent >= 0:
            return int(value)
        return None
    return None


def _describe(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, Decimal):
        return f"number({value})"
    if isinstance(value, str):
        return f"string({value!r})"
    if isinstance(value, JsonObject):
        return "object"
    if isinstance(value, list):
        return "array"
    return type(value).__name__


def _is_valid_integrity_digest(value: object) -> bool:
    if not isinstance(value, str):
        return False
    if len(value) != INTEGRITY_EVIDENCE_LENGTH:
        return False
    return all(character in INTEGRITY_HEX_DIGITS for character in value)


def load_package(
    package_dir: os.PathLike[str] | str,
    *,
    trusted_boundary: TrustedInputBoundary,
) -> ImportReport:
    """Run one Layer-1 acceptance attempt against ``package_dir``.

    The trusted package-input boundary is a **required** parameter: the loader never
    treats an arbitrary path as trusted (``§4.3.28`` D.3 ``IG-self-C``, ADR-001).
    """

    collector = IssueCollector()
    resolution = trusted_boundary.resolve(package_dir)

    if not resolution.established:
        assert resolution.problem is not None
        collector = collector.not_evaluable(
            "trust_boundary.configured_and_verifiable",
            resolution.problem.detail,
        )
        collector = IssueCollector(
            issues=collector.issues + (resolution.problem,), checks=collector.checks
        )
        return ImportReport(
            disposition=DISPOSITION_REJECTED,
            evaluable=False,
            collector=collector,
            accepted_package=None,
            content_view=None,
            disposition_basis=(
                "trusted package-input boundary could not be established; acceptance "
                "is not evaluable and fails closed (§4.3.28 D.3 IG-self-C / IC-16)"
            ),
        )

    package_path = Path(os.path.abspath(Path(package_dir).expanduser()))
    assert resolution.root is not None
    boundary_root = resolution.root
    collector = collector.passed("trust_boundary.configured_and_verifiable")

    try:
        return _accept(package_path, boundary_root, collector)
    except _BlockedAcceptance as blocked:
        return ImportReport(
            disposition=DISPOSITION_REJECTED,
            evaluable=True,
            collector=blocked.collector,
            accepted_package=None,
            content_view=None,
            disposition_basis=blocked.basis,
        )


def _accept(
    package_path: Path,
    boundary_root: Path,
    collector: IssueCollector,
) -> ImportReport:
    # ---- 1. manifest readable + strict parse --------------------------------
    manifest_path = package_path / MANIFEST_FILENAME
    manifest_read = read_file_bytes(manifest_path)

    if manifest_read is None:
        collector = collector.failed(
            "manifest.readable", "manifest.json is missing or unreadable"
        )
        collector = collector.issue(
            MANIFEST_FILENAME,
            "Snapshot Manifest is missing or cannot be read as a stable regular file",
            affected_evidence=MANIFEST_FILENAME,
            blast_radius="whole package",
            design_reference="§4.3.23 C + §4.3.28 D4.1",
            consequence_context="Package rejected; downstream artifact checks not evaluable",
        )
        collector = _mark_manifest_dependents_not_evaluable(
            collector,
            reason="manifest unavailable: declared artifact set is unknowable",
        )
        raise _BlockedAcceptance(
            collector,
            "manifest unavailable; package-level structural acceptance fails closed "
            "(IC-14 / IC-16)",
        )

    manifest_raw, manifest_view = manifest_read
    collector = collector.passed("manifest.readable")

    try:
        manifest = parse_strict_json(manifest_raw, source=MANIFEST_FILENAME)
    except StrictJsonError as error:
        collector = collector.failed("manifest.strict_parse", str(error))
        collector = collector.issue(
            MANIFEST_FILENAME,
            f"Snapshot Manifest is not compliant strict JSON: {error}",
            affected_evidence=MANIFEST_FILENAME,
            blast_radius="whole package",
            design_reference="§4.3.22 C-1/C-9 (IC-8)",
            consequence_context="Package rejected; downstream artifact checks not evaluable",
        )
        collector = _mark_manifest_dependents_not_evaluable(
            collector,
            reason="manifest is not strict-parseable: declared artifact set is unknowable",
        )
        raise _BlockedAcceptance(
            collector,
            "manifest failed strict parse; package identity and declared artifact set "
            "cannot be determined (IC-8 / IC-16)",
        )

    collector = collector.passed("manifest.strict_parse")

    # ---- 2. manifest structure / identity / contract_version ----------------
    collector = _check_manifest_structure(manifest, collector)

    package_block = manifest.get(GROUPING_PACKAGE)
    if not isinstance(package_block, JsonObject):
        collector = _mark_manifest_dependents_not_evaluable(
            collector, reason="manifest package block unavailable"
        )
        raise _BlockedAcceptance(
            collector,
            "manifest \"package\" block is missing or not an object; package identity "
            "cannot be determined (IC-14 / IC-16)",
        )

    package_id = package_block.get("snapshot_package_id")
    contract_version = package_block.get(CONTRACT_VERSION_PROPERTY)

    # Human Decision: the approved semantic set must actually be carried by the
    # package block at Layer 1.  Presence only -- value semantics are not validated
    # here (``CF-1``: ``completeness_state`` presence is required, but its value does
    # not gate acceptance).
    collector = _check_required_carriers(
        carrier=package_block,
        required=REQUIRED_PACKAGE_BLOCK_PROPERTIES,
        check_name="manifest.package_block_required_carriers",
        location_prefix=GROUPING_PACKAGE,
        missing_detail=(
            "required package-scoped Manifest carrier is absent; the approved semantic "
            "set must be carried by the Manifest (presence is required at Layer 1; no "
            "value semantic is validated here)"
        ),
        design_reference=(
            "Human Decision (Manifest semantic-set carrier presence) + §4.3.8 / §4.3.25 A"
        ),
        collector=collector,
    )

    if not isinstance(package_id, str) or package_id == "":
        collector = collector.failed(
            "manifest.package_identity", "snapshot_package_id is missing or not a string"
        )
        collector = collector.issue(
            f"{GROUPING_PACKAGE}.snapshot_package_id",
            "package identity must be present as a non-empty JSON string",
            blast_radius="whole package",
            design_reference="§4.3.3 + §4.3.25 A + §4.3.22 C-10",
            consequence_context="Package rejected",
        )
        collector = _mark_manifest_dependents_not_evaluable(
            collector, reason="package identity undeterminable"
        )
        raise _BlockedAcceptance(
            collector,
            "package identity could not be determined; fail closed (IC-14 / IC-16)",
        )

    collector = collector.passed("manifest.package_identity")
    collector = collector.passed("manifest.contract_version_present")

    # ---- 3. version exact-match gate (VC-1) --------------------------------
    if contract_version != SUPPORTED_CONTRACT_VERSION:
        collector = collector.failed(
            "manifest.contract_version_supported",
            f"{CONTRACT_VERSION_PROPERTY}={_describe(contract_version)}",
        )
        collector = collector.issue(
            f"{GROUPING_PACKAGE}.{CONTRACT_VERSION_PROPERTY}",
            f"unsupported contract version {_describe(contract_version)}; POC v0.2 "
            f"requires the exact token \"{SUPPORTED_CONTRACT_VERSION}\" (VC-1: "
            "exact-match only, no silent interpretation)",
            blast_radius="whole package",
            design_reference="§4.3.28 A.1 (VC-1)",
            consequence_context="Package rejected at import time",
        )
        collector = _mark_manifest_dependents_not_evaluable(
            collector,
            reason=(
                "applicable contract and known member set are undetermined because the "
                "contract version is not supported"
            ),
        )
        raise _BlockedAcceptance(
            collector,
            "unsupported contract version; no silent interpretation, import-time "
            "rejection (VC-1)",
        )

    collector = collector.passed("manifest.contract_version_supported")

    # ---- 4. dataset collection structure -----------------------------------
    datasets = manifest.get(GROUPING_DATASETS)
    if not isinstance(datasets, list):
        collector = collector.failed(
            "manifest.datasets_collection", f"{GROUPING_DATASETS} is not an array"
        )
        collector = collector.issue(
            GROUPING_DATASETS,
            "\"datasets\" must be an array of dataset entry objects",
            blast_radius="whole package",
            design_reference="§4.3.25 B (D-A)",
            consequence_context="Package rejected",
        )
        collector = _mark_manifest_dependents_not_evaluable(
            collector, reason="declared dataset collection is not determinable"
        )
        raise _BlockedAcceptance(
            collector,
            "declared dataset collection is not determinable; fail closed (IC-16)",
        )

    entries, collector = _check_dataset_entries(datasets, collector)
    collector = collector.passed("manifest.datasets_collection")

    # ---- 5. role / cardinality / artifact reference / path checks ----------
    entries, collector = _check_entry_uniqueness(entries, collector)
    entries, collector = _check_entry_filenames(entries, package_path, collector)

    # ---- 6. declared artifact existence / readability + raw-byte integrity --
    artifact_bytes, artifact_views, collector = _read_and_verify_artifacts(
        entries, package_path, collector
    )

    # ---- 7. artifact-level shape and record_count consistency --------------
    collector = _check_artifacts(
        entries=entries,
        artifact_bytes=artifact_bytes,
        package_path=package_path,
        collector=collector,
    )

    # ---- 8. unreferenced root-level artifacts ------------------------------
    collector = _check_unreferenced_entries(entries, package_path, collector)

    # ---- 9. acceptance-time stable view binding (Decision 10A) -------------
    # The manifest is part of the bounded view too: it carries no declared digest,
    # so an in-place manifest mutation can only be caught by re-reading it.
    read_views: dict[str, FileView] = {MANIFEST_FILENAME: manifest_view}
    read_views.update(artifact_views)
    collector = _check_stable_view(
        package_path=package_path,
        declared_names=tuple(entry.artifact for entry in entries),
        read_views=read_views,
        collector=collector,
    )

    issues = collector.sorted_issues()
    if issues:
        return ImportReport(
            disposition=DISPOSITION_REJECTED,
            evaluable=True,
            collector=collector,
            accepted_package=None,
            content_view=None,
            disposition_basis=(
                f"{len(issues)} Layer-1 structural defect(s) collected "
                "(§4.3.28 B.2 FR-3 collect-all; RD-B import-time REJECTED)"
            ),
        )

    # A mandatory gate that could not be decided must not yield ACCEPTED.
    # ``FR-3`` forbids treating a prerequisite-blocked check as passed, and
    # ``Decision 10A`` makes an unestablishable required consistency fail-closed,
    # so an undecided mandatory gate is reported as not-decidable rather than
    # silently accepted.
    undecided = _undecided_mandatory_checks(collector)
    if undecided:
        names = ", ".join(sorted(undecided))
        return ImportReport(
            disposition=DISPOSITION_REJECTED,
            evaluable=False,
            collector=collector,
            accepted_package=None,
            content_view=None,
            disposition_basis=(
                "mandatory Layer-1 gate(s) could not be decided, so acceptance is not "
                f"decidable and fails closed: {names} "
                "(§4.3.28 B.2 FR-3 + C.2 Decision 10A)"
            ),
        )

    files = (manifest_view,) + tuple(
        view for _, view in sorted(artifact_views.items())
    )
    content_view = ContentView(
        package_path=str(package_path),
        root_identity=physical_identity(package_path),
        files=tuple(sorted(files, key=lambda item: item.name)),
        directory_listing=tuple(sorted(view.name for view in files)),
        digest=compute_view_digest(files),
    )
    accepted = AcceptedPackage(
        package_id=package_id,
        contract_version=SUPPORTED_CONTRACT_VERSION,
        package_path=package_path,
        boundary_root=boundary_root,
        content_view=content_view,
        declared_integrity=tuple(
            (entry.artifact, entry.declared_integrity) for entry in entries
        ),
        # The exact bytes that were read and verified during acceptance, carried so
        # that downstream trusted reuse (Layer 2) never has to re-read a file whose
        # content might have changed since acceptance (§4.3.28 C.2 / C.3).
        accepted_records=tuple(
            (entry.role, entry.artifact, artifact_bytes.get(entry.artifact, b""))
            for entry in entries
        ),
    )
    return ImportReport(
        disposition=DISPOSITION_ACCEPTED,
        evaluable=True,
        collector=collector,
        accepted_package=accepted,
        content_view=content_view,
        disposition_basis=(
            "all applicable Layer-1 gates passed against one stable package content "
            "view (§4.3.28 D4.1 / Decision 10A)"
        ),
    )


# ---------------------------------------------------------------------------
# manifest structure
# ---------------------------------------------------------------------------


def _undecided_mandatory_checks(collector: IssueCollector) -> tuple[str, ...]:
    """Mandatory Layer-1 gates that were *not decided* during this attempt.

    ``§4.3.28`` D.4 + ``FR-3``: a check whose prerequisite is blocked is
    ``not evaluable due to prerequisite`` and is not passed.  For a mandatory gate
    that means acceptance itself is not decidable, so the caller must fail closed
    rather than return ``ACCEPTED``.
    """

    return tuple(
        sorted(
            {
                check.name
                for check in collector.checks
                if check.state == EVALUATION_NOT_EVALUABLE
                and check.name in MANDATORY_LAYER1_CHECKS
            }
        )
    )


def _mark_manifest_dependents_not_evaluable(
    collector: IssueCollector, *, reason: str
) -> IssueCollector:
    """Record prerequisite-blocked checks explicitly as *not evaluable*.

    ``§4.3.28`` D.4: a check whose prerequisite is blocked is ``not evaluable due to
    prerequisite`` and is **not** passed, and its absence is not an under-report.
    """

    for name in (
        "manifest.datasets_collection",
        "datasets.entry_shape",
        "datasets.entry_required_carriers",
        "datasets.role_uniqueness",
        "datasets.artifact_reference_valid",
        "datasets.artifact_uniqueness",
        "artifacts.declared_exist_and_readable",
        "artifacts.raw_byte_integrity",
        "artifacts.strict_parse",
        "artifacts.record_carrier_shape",
        RECORD_PROPERTY_SET_CHECK,
        "artifacts.record_count_consistency",
        "package.unreferenced_root_artifact",
        "package.acceptance_time_stable_view",
    ):
        collector = collector.not_evaluable(name, reason)
    return collector


def _check_required_carriers(
    *,
    carrier: JsonObject,
    required: tuple[str, ...],
    check_name: str,
    location_prefix: str,
    missing_detail: str,
    design_reference: str,
    collector: IssueCollector,
) -> IssueCollector:
    """Verify that every registered carrier property is present at ``carrier``.

    Presence only (Human Decision: Manifest semantic-set carrier presence = REQUIRED
    at Layer 1).  Nothing about the property's *value* is decided here: value
    semantics, business requiredness beyond presence, applicability, semantic
    resolution and capability readiness remain Layer 2-4 concerns.
    """

    missing = [name for name in required if name not in carrier]
    if not missing:
        return collector.passed(check_name)

    collector = collector.failed(check_name, f"missing={missing!r}")
    return collector.issue_many(
        [(f"{location_prefix}.{name}", missing_detail) for name in missing],
        affected_evidence=location_prefix,
        design_reference=design_reference,
        consequence_context="Package rejected",
    )


def _check_manifest_structure(
    manifest: Any, collector: IssueCollector
) -> IssueCollector:
    if not isinstance(manifest, JsonObject):
        collector = collector.failed(
            "manifest.top_level_shape", "manifest top level is not a JSON object"
        )
        collector = collector.issue(
            MANIFEST_FILENAME,
            "Snapshot Manifest top level must be a JSON object (grouped nested carrier)",
            blast_radius="whole package",
            design_reference="§4.3.25 A (M-B)",
            consequence_context="Package rejected",
        )
        raise _BlockedAcceptance(
            collector,
            "manifest top-level carrier shape is invalid; package identity cannot be "
            "determined (IC-16)",
        )

    collector = collector.passed("manifest.top_level_shape")

    unknown_top_level = [
        key for key in manifest.order if key not in MANIFEST_TOP_LEVEL_PROPERTIES
    ]
    if unknown_top_level:
        collector = collector.failed(
            "manifest.unknown_property", f"{unknown_top_level!r}"
        )
        collector = collector.issue_many(
            [
                (
                    f"{MANIFEST_FILENAME}:{key}",
                    "unknown Manifest property; UX-A reject (the approved Manifest "
                    "grouping literals are \"package\" and \"datasets\" only)",
                )
                for key in unknown_top_level
            ],
            blast_radius="whole package",
            design_reference="§4.3.28 A.2 (UX-A) + §4.3.25 A",
            consequence_context="Package rejected",
        )
    else:
        collector = collector.passed("manifest.unknown_property")

    package_block = manifest.get(GROUPING_PACKAGE)
    if isinstance(package_block, JsonObject):
        unknown_package_properties = [
            key for key in package_block.order if key not in PACKAGE_SCOPED_PROPERTIES
        ]
        if unknown_package_properties:
            collector = collector.failed(
                "manifest.package_block_unknown_property",
                f"{unknown_package_properties!r}",
            )
            collector = collector.issue_many(
                [
                    (
                        f"{GROUPING_PACKAGE}.{key}",
                        "unknown package-scoped Manifest property; UX-A reject",
                    )
                    for key in unknown_package_properties
                ],
                blast_radius="whole package",
                design_reference="§4.3.28 A.2 (UX-A) + §4.3.25 A (2)",
                consequence_context="Package rejected",
            )
        else:
            collector = collector.passed("manifest.package_block_unknown_property")

    return collector


def _check_dataset_entries(
    datasets: list[Any], collector: IssueCollector
) -> tuple[tuple[_DatasetEntry, ...], IssueCollector]:
    entries: list[_DatasetEntry] = []
    entry_carrier_failures = 0

    for index, raw_entry in enumerate(datasets):
        location = f"{GROUPING_DATASETS}[{index}]"

        if not isinstance(raw_entry, JsonObject):
            collector = collector.failed(
                f"datasets.entry_shape:{index}", "dataset entry is not an object"
            )
            collector = collector.issue(
                location,
                "each dataset entry must be a JSON object",
                design_reference="§4.3.25 B",
                consequence_context="Package rejected",
            )
            continue

        unknown_entry_properties = [
            key for key in raw_entry.order if key not in DATASET_ENTRY_PROPERTIES
        ]
        if unknown_entry_properties:
            collector = collector.failed(
                f"datasets.entry_unknown_property:{index}",
                f"{unknown_entry_properties!r}",
            )
            collector = collector.issue_many(
                [
                    (
                        f"{location}.{key}",
                        "unknown dataset-entry property; UX-A reject",
                    )
                    for key in unknown_entry_properties
                ],
                affected_evidence=location,
                design_reference="§4.3.28 A.2 (UX-A) + §4.3.25 B",
                consequence_context="Package rejected",
            )

        role = raw_entry.get("role")
        artifact = raw_entry.get("artifact")
        declared_count = _as_record_count(raw_entry.get("record_count"))
        integrity = raw_entry.get("integrity_evidence")

        # Human Decision: every included dataset entry must carry the approved
        # dataset-entry semantic set.  Presence only: ``provenance_ref`` presence is
        # required, while its value format is not constrained because no canonical
        # authority registers a ``provenance_ref`` representation.
        missing_entry_carriers = [
            name for name in REQUIRED_DATASET_ENTRY_PROPERTIES if name not in raw_entry
        ]
        if missing_entry_carriers:
            entry_carrier_failures += 1
            collector = collector.failed(
                f"datasets.entry_required_carriers:{index}",
                f"missing={missing_entry_carriers!r}",
            )
            collector = collector.issue_many(
                [
                    (
                        f"{location}.{name}",
                        "required dataset-entry carrier is absent; every included "
                        "dataset entry must carry the approved semantic set (presence "
                        "is required at Layer 1; no value semantic is validated here)",
                    )
                    for name in missing_entry_carriers
                ],
                affected_evidence=location,
                design_reference=(
                    "Human Decision (Manifest semantic-set carrier presence) + §4.3.25 B"
                ),
                consequence_context="Package rejected",
            )

        entry_valid = True

        if not isinstance(role, str) or role == "":
            entry_valid = False
            collector = collector.failed(
                f"datasets.role:{index}", f"role is {_describe(role)}"
            )
            collector = collector.issue(
                f"{location}.role",
                "logical dataset role must be a non-empty JSON string "
                "(exact opaque string; no trim / case folding / normalisation)",
                design_reference="§4.3.30 D + §4.3.22 C-10",
                consequence_context="Package rejected",
            )

        if not isinstance(artifact, str) or artifact == "":
            entry_valid = False
            collector = collector.failed(
                f"datasets.artifact:{index}", f"artifact is {_describe(artifact)}"
            )
            collector = collector.issue(
                f"{location}.artifact",
                "artifact reference must be a non-empty JSON string",
                design_reference="§4.3.23 D + §4.3.25 B",
                consequence_context="Package rejected",
            )

        if declared_count is None or declared_count < 0:
            entry_valid = False
            collector = collector.failed(
                f"datasets.record_count:{index}",
                f"record_count is {_describe(raw_entry.get('record_count'))}",
            )
            collector = collector.issue(
                f"{location}.record_count",
                "record_count must be a non-negative JSON integer "
                "(authoritative Manifest presence metadata)",
                design_reference="§4.3.25 A(3)/B + IC-4",
                consequence_context="Package rejected",
            )

        if not _is_valid_integrity_digest(integrity):
            entry_valid = False
            collector = collector.failed(
                f"datasets.integrity_evidence:{index}",
                f"integrity_evidence is {_describe(integrity)}",
            )
            collector = collector.issue(
                f"{location}.integrity_evidence",
                "integrity evidence must be a 64-character lowercase hexadecimal "
                "SHA-256 digest (IG-alg-1 / IG-rep-A); integrity is mandatory and "
                "unverifiable integrity is a structural inconsistency (IC-22)",
                design_reference=_INTEGRITY_DESIGN_REFERENCE,
                consequence_context="Package rejected",
            )

        if not entry_valid:
            continue

        entries.append(
            _DatasetEntry(
                index=index,
                role=role,  # type: ignore[arg-type]
                artifact=artifact,  # type: ignore[arg-type]
                record_count=declared_count,
                declared_integrity=integrity,  # type: ignore[arg-type]
                declared_integrity_text=integrity,  # type: ignore[arg-type]
            )
        )

    if not any(
        check.name == "datasets.entry_shape" and check.state == "failed"
        for check in collector.checks
    ):
        collector = collector.passed("datasets.entry_shape")

    collector = (
        collector.failed(
            "datasets.entry_required_carriers",
            f"{entry_carrier_failures} entry/entries missing required carriers",
        )
        if entry_carrier_failures
        else collector.passed("datasets.entry_required_carriers")
    )

    return tuple(entries), collector


def _check_entry_uniqueness(
    entries: tuple[_DatasetEntry, ...], collector: IssueCollector
) -> tuple[tuple[_DatasetEntry, ...], IssueCollector]:
    accepted: list[_DatasetEntry] = []
    seen_roles: dict[str, int] = {}
    seen_artifacts: dict[str, int] = {}
    role_duplicate = False
    artifact_duplicate = False

    for entry in entries:
        location = f"{GROUPING_DATASETS}[{entry.index}]"
        duplicate_role = entry.role in seen_roles
        duplicate_artifact = entry.artifact in seen_artifacts
        if duplicate_role or duplicate_artifact:
            if duplicate_role:
                role_duplicate = True
                collector = collector.issue(
                    f"{location}.role",
                    f"duplicate logical dataset role {entry.role!r} (first declared at "
                    f"{GROUPING_DATASETS}[{seen_roles[entry.role]}]); one included role "
                    "must establish exactly one authoritative artifact association",
                    affected_evidence=entry.role,
                    design_reference="§4.3.25 B invariant + IC-3 (IS-3)",
                    consequence_context="Package rejected",
                )
            if duplicate_artifact:
                artifact_duplicate = True
                collector = collector.issue(
                    f"{location}.artifact",
                    f"artifact {entry.artifact!r} is referenced by more than one included "
                    f"role (first declared at {GROUPING_DATASETS}[{seen_artifacts[entry.artifact]}]); "
                    "each included logical dataset requires an independent artifact",
                    affected_evidence=entry.artifact,
                    design_reference="IC-1 independent-artifact invariant (IS-4 / IS-9)",
                    consequence_context="Package rejected",
                )
            collector = collector.failed(f"datasets.uniqueness:{entry.index}")
            continue
        seen_roles[entry.role] = entry.index
        seen_artifacts[entry.artifact] = entry.index
        accepted.append(entry)

    collector = (
        collector.failed("datasets.role_uniqueness")
        if role_duplicate
        else collector.passed("datasets.role_uniqueness")
    )
    collector = (
        collector.failed("datasets.artifact_uniqueness")
        if artifact_duplicate
        else collector.passed("datasets.artifact_uniqueness")
    )

    return tuple(accepted), collector


def _check_entry_filenames(
    entries: tuple[_DatasetEntry, ...],
    package_path: Path,
    collector: IssueCollector,
) -> tuple[tuple[_DatasetEntry, ...], IssueCollector]:
    accepted: list[_DatasetEntry] = []
    rejected = False

    for entry in entries:
        location = f"{GROUPING_DATASETS}[{entry.index}].artifact"
        rejection: FilenameRejection | None = validate_artifact_filename(entry.artifact)

        if rejection is None:
            target = package_path / entry.artifact
            # A filename that is legal under the registered rules but that the host
            # cannot represent (an embedded NUL, for example) is NOT a path-boundary
            # violation: it is left to the declared-artifact existence/readability
            # gate, which reports an absent/unreadable artifact (IC-14/IC-16) and
            # fails closed.  Only a target that is representable AND provably outside
            # the package root is a boundary error.
            if path_is_unrepresentable(target):
                accepted.append(entry)
                continue
            if not resolved_within(target, package_path):
                rejected = True
                collector = collector.issue(
                    location,
                    "artifact reference resolves outside the package boundary; the "
                    "logical resolved target must stay inside the package root",
                    affected_evidence=entry.artifact,
                    design_reference="IC-2 + §4.3.23 H (L-11)",
                    consequence_context="Package rejected",
                )
                collector = collector.failed(f"datasets.artifact_reference:{entry.index}")
                continue
            accepted.append(entry)
            continue

        rejected = True
        collector = collector.failed(
            f"datasets.artifact_reference:{entry.index}", rejection.code
        )
        collector = collector.issue(
            location,
            f"illegal artifact reference ({rejection.code}): {rejection.detail}",
            affected_evidence=entry.artifact,
            design_reference="§4.3.28 C.1 (PN-1) + IC-2",
            consequence_context="Package rejected",
        )

    collector = (
        collector.failed("datasets.artifact_reference_valid")
        if rejected
        else collector.passed("datasets.artifact_reference_valid")
    )
    return tuple(accepted), collector


def _read_and_verify_artifacts(
    entries: tuple[_DatasetEntry, ...],
    package_path: Path,
    collector: IssueCollector,
) -> tuple[dict[str, bytes], dict[str, FileView], IssueCollector]:
    artifact_bytes: dict[str, bytes] = {}
    artifact_views: dict[str, FileView] = {}
    identity_owner: dict[tuple[int, int], str] = {}
    any_missing = False
    any_identity_unavailable = False
    any_alias = False

    for entry in entries:
        raw = read_file_bytes(package_path / entry.artifact)
        if raw is None:
            any_missing = True
            collector = collector.failed(
                f"artifacts.readable:{entry.artifact}",
                "declared artifact is absent or unreadable",
            )
            collector = collector.issue(
                entry.artifact,
                "manifest declared this logical dataset as included, but the artifact is "
                "absent, unreadable, or not a stable regular file",
                affected_evidence=entry.role,
                design_reference="IC-14 + §4.3.12 A",
                consequence_context="Package rejected",
            )
            continue

        content, view = raw
        collector = collector.passed(f"artifacts.readable:{entry.artifact}")

        if view.sha256 != entry.declared_integrity:
            collector = collector.failed(
                f"artifacts.integrity:{entry.artifact}",
                "declared integrity evidence does not match artifact raw bytes",
            )
            collector = collector.issue(
                f"{GROUPING_DATASETS}[{entry.index}].integrity_evidence",
                "declared \"integrity_evidence\" does not match the SHA-256 digest of the "
                f"artifact raw bytes (declared={entry.declared_integrity_text}, "
                f"computed={view.sha256})",
                affected_evidence=entry.artifact,
                design_reference=_INTEGRITY_DESIGN_REFERENCE,
                consequence_context="Package rejected",
            )
        else:
            collector = collector.passed(f"artifacts.integrity:{entry.artifact}")

        if view.identity is None:
            any_identity_unavailable = True
        else:
            owner = identity_owner.get(view.identity)
            if owner is not None:
                any_alias = True
                collector = collector.issue(
                    f"{GROUPING_DATASETS}[{entry.index}].artifact",
                    f"artifact {entry.artifact!r} resolves to the same physical file as "
                    f"{owner!r}; different included roles must not share one artifact",
                    affected_evidence=entry.artifact,
                    design_reference="IC-1 + PN-1 rule 7 (IS-17b)",
                    consequence_context="Package rejected",
                )
            else:
                identity_owner[view.identity] = entry.artifact

        artifact_bytes[entry.artifact] = content
        artifact_views[entry.artifact] = view

    collector = (
        collector.failed("artifacts.declared_exist_and_readable")
        if any_missing
        else collector.passed("artifacts.declared_exist_and_readable")
    )

    if any_alias:
        collector = collector.failed("artifacts.independent_target_identity")
    elif any_identity_unavailable:
        collector = collector.not_evaluable(
            "artifacts.independent_target_identity",
            "the platform/filesystem did not expose a usable physical identity for every "
            "artifact, so alias equivalence could not be decided; no equivalence is "
            "claimed (PN-1 rule 6/7 is detection-limited)",
        )
    else:
        collector = collector.passed("artifacts.independent_target_identity")

    integrity_failed = any(
        check.name.startswith("artifacts.integrity:") and check.state == "failed"
        for check in collector.checks
    )
    if any_missing and not artifact_views:
        collector = collector.not_evaluable(
            "artifacts.raw_byte_integrity",
            "no declared artifact could be read, so raw-byte integrity is not evaluable",
        )
    elif integrity_failed:
        collector = collector.failed("artifacts.raw_byte_integrity")
    else:
        collector = collector.passed("artifacts.raw_byte_integrity")

    return artifact_bytes, artifact_views, collector


def _check_artifacts(
    *,
    entries: tuple[_DatasetEntry, ...],
    artifact_bytes: dict[str, bytes],
    package_path: Path,
    collector: IssueCollector,
) -> IssueCollector:
    _ = package_path
    parse_failures = 0
    shape_failures = 0
    record_count_failures = 0
    record_set_failures = 0
    record_set_not_evaluable = False

    for entry in entries:
        content = artifact_bytes.get(entry.artifact)
        if content is None:
            collector = collector.not_evaluable(
                f"artifacts.strict_parse:{entry.artifact}",
                "artifact bytes unavailable",
            )
            collector = collector.not_evaluable(
                f"artifacts.record_count_consistency:{entry.artifact}",
                "artifact bytes unavailable",
            )
            collector = collector.not_evaluable(
                f"{RECORD_PROPERTY_SET_CHECK}:{entry.artifact}",
                "artifact bytes unavailable",
            )
            record_set_not_evaluable = True
            continue

        try:
            payload = parse_strict_json(content, source=entry.artifact)
        except StrictJsonError as error:
            parse_failures += 1
            collector = collector.failed(
                f"artifacts.strict_parse:{entry.artifact}", str(error)
            )
            collector = collector.issue(
                entry.artifact,
                f"business dataset artifact is not compliant strict JSON: {error}",
                affected_evidence=entry.role,
                design_reference="§4.3.22 C-1/C-9 (IC-8) + §4.3.28 D4.3",
                consequence_context="Package rejected; record_count consistency not evaluable",
            )
            collector = collector.not_evaluable(
                f"artifacts.record_count_consistency:{entry.artifact}",
                "artifact is not strict-parseable, so record count is not determinable",
            )
            collector = collector.not_evaluable(
                f"{RECORD_PROPERTY_SET_CHECK}:{entry.artifact}",
                "artifact is not strict-parseable, so record properties are not determinable",
            )
            record_set_not_evaluable = True
            continue

        collector = collector.passed(f"artifacts.strict_parse:{entry.artifact}")

        if not isinstance(payload, list):
            shape_failures += 1
            collector = collector.failed(
                f"artifacts.record_carrier_shape:{entry.artifact}",
                f"top level is {_describe(payload)}",
            )
            collector = collector.issue(
                entry.artifact,
                "business dataset artifact top level must be a bare record array (B-A)",
                affected_evidence=entry.role,
                design_reference="§4.3.25 D + IC-6",
                consequence_context="Package rejected; record_count consistency not evaluable",
            )
            collector = collector.not_evaluable(
                f"artifacts.record_count_consistency:{entry.artifact}",
                "artifact is not a bare record array, so record count is not determinable",
            )
            collector = collector.not_evaluable(
                f"{RECORD_PROPERTY_SET_CHECK}:{entry.artifact}",
                "artifact is not a bare record array, so record properties are not determinable",
            )
            record_set_not_evaluable = True
            continue

        if len(payload) != entry.record_count:
            record_count_failures += 1
            collector = collector.failed(
                f"artifacts.record_count_consistency:{entry.artifact}",
                f"declared={entry.record_count}, actual={len(payload)}",
            )
            collector = collector.issue(
                f"{GROUPING_DATASETS}[{entry.index}].record_count",
                f"declared record_count ({entry.record_count}) does not match the artifact "
                f"record count ({len(payload)}); record_count is authoritative presence "
                "metadata, so an inconsistency makes required structural metadata "
                "undeterminable",
                affected_evidence=entry.role,
                design_reference="IC-4 / IC-16 (§4.3.28 D4.3)",
                consequence_context="Package rejected",
            )
        else:
            collector = collector.passed(
                f"artifacts.record_count_consistency:{entry.artifact}"
            )

        record_findings = _check_records(payload, entry)
        if record_findings:
            shape_failures += 1
            record_set_failures += 1
            collector = collector.issue_many(
                record_findings,
                affected_evidence=entry.role,
                design_reference=_RECORD_DESIGN_REFERENCE,
                consequence_context="Package rejected",
            )
            collector = collector.failed(
                f"artifacts.record_carrier_shape:{entry.artifact}",
                f"{len(record_findings)} record-shape defect(s)",
            )
            collector = collector.failed(
                f"{RECORD_PROPERTY_SET_CHECK}:{entry.artifact}",
                f"{len(record_findings)} record defect(s)",
            )
        else:
            collector = collector.passed(
                f"artifacts.record_carrier_shape:{entry.artifact}"
            )
            collector = collector.passed(f"{RECORD_PROPERTY_SET_CHECK}:{entry.artifact}")

    collector = (
        collector.failed("artifacts.strict_parse")
        if parse_failures
        else collector.passed("artifacts.strict_parse")
    )
    collector = (
        collector.failed("artifacts.record_carrier_shape")
        if shape_failures
        else collector.passed("artifacts.record_carrier_shape")
    )
    collector = (
        collector.failed("artifacts.record_count_consistency")
        if record_count_failures
        else collector.passed("artifacts.record_count_consistency")
    )
    if record_set_failures:
        collector = collector.failed(RECORD_PROPERTY_SET_CHECK)
    elif record_set_not_evaluable and not entries:
        collector = collector.not_evaluable(
            RECORD_PROPERTY_SET_CHECK, "no artifact record set was evaluable"
        )
    elif record_set_not_evaluable:
        collector = collector.not_evaluable(
            RECORD_PROPERTY_SET_CHECK,
            "at least one artifact record set was not reachable for property checking",
        )
    else:
        collector = collector.passed(RECORD_PROPERTY_SET_CHECK)
    return collector


def _check_records(
    records: list[Any], entry: _DatasetEntry
) -> list[tuple[str, str]]:
    """Check record carrier shape, canonical-property membership, and ``"_meta"``.

    Layer-1 responsibilities only: a record must be a JSON object; each direct
    property must be ``"_meta"`` or a member of the frozen v0.2 canonical property
    set; ``"_meta"`` must match the registered controlled member shape.  No value
    semantics, requiredness, applicability, or role-specific expectation is
    evaluated here (``§4.3.30`` C.2/C.3).
    """

    findings: list[tuple[str, str]] = []

    for index, record in enumerate(records):
        location = f"{entry.artifact}[{index}]"

        if not isinstance(record, JsonObject):
            findings.append(
                (location, "each record must be a JSON object (record carrier E)")
            )
            continue

        # An empty JSON object record is NOT a structural defect: it carries no
        # unknown property, and Layer 1 evaluates property membership and shape
        # only.  Whether a record is *sufficient* for any purpose is a Layer 2-4
        # question (§4.3.30 C.2/C.3, IC-17); rejecting it here would promote a
        # Layer-2 concern into package rejection.
        for key in record.order:
            if key == RECORD_META_NAMESPACE:
                continue
            if key not in V02_CANONICAL_RECORD_PROPERTY_SET:
                findings.append(
                    (
                        f"{location}.{key}",
                        f"unknown canonical record property {key!r}; UX-A reject (the "
                        "property is not in the frozen v0.2 known canonical record "
                        "property set)",
                    )
                )

        if RECORD_META_NAMESPACE in record:
            findings.extend(_check_record_meta(record[RECORD_META_NAMESPACE], location))

    return findings


def _check_record_meta(meta: Any, location: str) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    meta_location = f"{location}.{RECORD_META_NAMESPACE}"

    if not isinstance(meta, JsonObject):
        return [(meta_location, "\"_meta\" must be a JSON object")]

    for key in meta.order:
        if key not in META_MEMBERS:
            findings.append(
                (
                    f"{meta_location}.{key}",
                    f"unknown direct member under \"_meta\" {key!r}; reject (no other "
                    "\"_meta\" member is approved for POC v0.2)",
                )
            )

    associations = meta.get("provenance_associations")
    if associations is None:
        return findings

    if not isinstance(associations, list):
        findings.append(
            (
                f"{meta_location}.provenance_associations",
                "\"provenance_associations\" must be an array of association objects",
            )
        )
        return findings

    for index, association in enumerate(associations):
        association_location = f"{meta_location}.provenance_associations[{index}]"

        if not isinstance(association, JsonObject):
            findings.append(
                (association_location, "each provenance association must be a JSON object")
            )
            continue

        for key in association.order:
            if key not in ASSOCIATION_MEMBERS:
                findings.append(
                    (
                        f"{association_location}.{key}",
                        f"unknown member inside a provenance association {key!r}; reject",
                    )
                )

        for required in REQUIRED_ASSOCIATION_MEMBERS:
            if required not in association:
                findings.append(
                    (
                        f"{association_location}.{required}",
                        f"required association member {required!r} is missing",
                    )
                )

        observation = association.get("observation")
        if observation is not None and not isinstance(observation, str):
            findings.append(
                (
                    f"{association_location}.observation",
                    "\"observation\" must reference a canonical observation / context as "
                    "an exact JSON string",
                )
            )
        elif isinstance(observation, str) and observation not in (
            V02_CANONICAL_RECORD_PROPERTY_SET
        ):
            findings.append(
                (
                    f"{association_location}.observation",
                    f"\"observation\" value {observation!r} is not a known v0.2 canonical "
                    "property name",
                )
            )

        evidence = association.get("evidence")
        if evidence is not None:
            if not isinstance(evidence, list) or not evidence:
                findings.append(
                    (
                        f"{association_location}.evidence",
                        "\"evidence\" must be a non-empty array of opaque JSON strings",
                    )
                )
            else:
                for position, locator in enumerate(evidence):
                    if not isinstance(locator, str) or locator == "":
                        findings.append(
                            (
                                f"{association_location}.evidence[{position}]",
                                "each evidence locator must be a non-empty opaque JSON "
                                "string (no trim / normalisation)",
                            )
                        )

        basis = association.get("mapping_basis")
        if basis is not None and not isinstance(basis, str):
            findings.append(
                (
                    f"{association_location}.mapping_basis",
                    "\"mapping_basis\" must be an exact JSON string when present",
                )
            )

    return findings


def _check_unreferenced_entries(
    entries: tuple[_DatasetEntry, ...],
    package_path: Path,
    collector: IssueCollector,
) -> IssueCollector:
    names = list_root_entries(package_path)
    if names is None:
        collector = collector.failed(
            "package.root_listable", "package root could not be listed"
        )
        collector = collector.issue(
            "package",
            "package root could not be listed, so package contents are not determinable",
            blast_radius="whole package",
            design_reference="IC-16",
            consequence_context="Package rejected",
        )
        return collector

    collector = collector.passed("package.root_listable")

    declared = {entry.artifact for entry in entries}
    violations: list[tuple[str, str]] = []

    for name in names:
        if name == MANIFEST_FILENAME:
            continue
        if name in declared:
            continue
        path = package_path / name
        if path.is_dir():
            violations.append(
                (
                    name,
                    "nested directories are NOT ALLOWED for POC v0.2; the package root is "
                    "flat",
                )
            )
        elif name.endswith(".json"):
            violations.append(
                (
                    name,
                    "unreferenced root-level JSON artifact; UX-A reject (the Manifest is "
                    "the authoritative artifact association)",
                )
            )
        else:
            violations.append(
                (
                    name,
                    "undeclared entry in the package root; only manifest.json and the "
                    "Manifest-declared .json artifacts may be present",
                )
            )

    if violations:
        collector = collector.failed("package.unreferenced_root_artifact")
        collector = collector.issue_many(
            violations,
            blast_radius="whole package",
            design_reference="§4.3.28 A.2 (UX-A) + §4.3.23 D/G + IC-4",
            consequence_context="Package rejected",
        )
    else:
        collector = collector.passed("package.unreferenced_root_artifact")

    return collector


def _check_stable_view(
    *,
    package_path: Path,
    declared_names: tuple[str, ...],
    read_views: dict[str, FileView],
    collector: IssueCollector,
) -> IssueCollector:
    """Verify acceptance is bound to one stable content view (Decision 10A).

    ``Decision 10A`` requires every acceptance-producing result to be bound to the
    **same** package content view -- the view that is actually accepted and later
    consumed.  Two independent comparisons establish that:

    1. the set of verified files must equal the set the Manifest declared (catches
       an added, removed or renamed file);
    2. every file read during acceptance must still hash to the same raw bytes at
       the end of acceptance (catches an **in-place mutation** that happened after
       its content was read but before ``Accepted`` was concluded).

    Comparison 2 is the decisive one: without it, a mutation of an already-read
    file -- most importantly the Manifest itself, which carries no declared digest
    -- would leave every acceptance result computed from the stale view while the
    package on disk had changed, and an ``ACCEPTED`` verdict would be bound to a
    view that is no longer the package's content.

    Re-reading the bytes is the mechanism this implementation chooses; the contract
    leaves locking / transaction / atomic-move / storage technology open
    (``§4.3.28`` C.2).  It doubles package I/O, which is acceptable for POC-sized
    packages and is the price of an actual guarantee rather than a metadata
    approximation.
    """

    accepted_names = tuple(sorted(read_views))
    declared = tuple(sorted((MANIFEST_FILENAME,) + declared_names))

    if accepted_names != declared:
        collector = collector.failed(
            "package.acceptance_time_stable_view",
            "the set of verified files is not the set the Manifest declared",
        )
        collector = collector.issue(
            "package",
            "the verified content view is not the declared content view "
            f"(declared={list(declared)!r}, verified={list(accepted_names)!r}); acceptance "
            "results cannot be bound to one stable view",
            blast_radius="whole package",
            design_reference="§4.3.28 C.2 (Decision 10A) + IS-24",
            consequence_context="Package not evaluable / fail closed",
        )
        return collector

    mutated: list[tuple[str, str]] = []
    for name, expected in sorted(read_views.items()):
        current = read_file_bytes(package_path / name)
        if current is None:
            collector = collector.failed(
                f"package.stable_view_readable:{name}",
                "file could not be re-read to re-establish the accepted view",
            )
            mutated.append(
                (
                    name,
                    "file could not be re-read after acceptance checks completed, so "
                    "the accepted view cannot be re-established",
                )
            )
            continue
        _, observed = current
        if observed.sha256 != expected.sha256:
            collector = collector.failed(
                f"package.stable_view_bytes:{name}",
                "raw bytes changed after the file was read during acceptance",
            )
            mutated.append(
                (
                    name,
                    "raw bytes changed between being read during acceptance and the "
                    "conclusion of acceptance "
                    f"(read={expected.sha256}, now={observed.sha256})",
                )
            )
        else:
            collector = collector.passed(f"package.stable_view_bytes:{name}")

    if mutated:
        collector = collector.issue_many(
            mutated,
            blast_radius="whole package",
            design_reference="§4.3.28 C.2 (Decision 10A) + IS-24 + IC-12",
            consequence_context="Package not evaluable / fail closed",
        )
        collector = collector.failed(
            "package.acceptance_time_stable_view",
            "the package changed during acceptance",
        )
        return collector

    collector = collector.passed("package.stable_view_all_files_re_read")

    # Final root content-set re-check.  Re-reading the declared files close the
    # window for declared-file mutation, but not the window between the earlier root
    # listing and this point: an *undeclared* entry added or removed in between would
    # otherwise escape, because the declared file bytes would still match.  The set of
    # root entries must therefore equal exactly what the accepted view allows.
    expected_entries = sorted({MANIFEST_FILENAME} | set(read_views))
    final_entries = list_root_entries(package_path)
    if final_entries is None:
        collector = collector.issue(
            "package",
            "package root could not be re-listed at the conclusion of acceptance, so "
            "the accepted view cannot be confirmed",
            blast_radius="whole package",
            design_reference="§4.3.28 C.2 (Decision 10A) + IS-24",
            consequence_context="Package not evaluable / fail closed",
        )
        collector = collector.failed(
            "package.final_root_content_set",
            "package root could not be re-listed",
        )
        return collector.failed(
            "package.acceptance_time_stable_view",
            "final root content set could not be confirmed",
        )

    if sorted(final_entries) != expected_entries:
        collector = collector.issue(
            "package",
            "the package root content set changed during acceptance "
            f"(accepted view allows={expected_entries!r}, observed={sorted(final_entries)!r})",
            blast_radius="whole package",
            design_reference="§4.3.28 C.2 (Decision 10A) + IS-24 + §4.3.28 A.2 (UX-A)",
            consequence_context="Package not evaluable / fail closed",
        )
        collector = collector.failed(
            "package.final_root_content_set",
            "root entry set differs from the accepted view",
        )
        return collector.failed(
            "package.acceptance_time_stable_view",
            "the package root content set changed during acceptance",
        )

    collector = collector.passed("package.final_root_content_set")

    root_identity = physical_identity(package_path)
    if root_identity is None:
        collector = collector.not_evaluable(
            "package.stable_root_identity",
            "the platform/filesystem did not expose a usable package-root identity",
        )
    else:
        collector = collector.passed("package.stable_root_identity")

    return collector.passed("package.acceptance_time_stable_view")


def load_package_from_paths(
    package_dir: os.PathLike[str] | str,
    trusted_root: os.PathLike[str] | str,
) -> ImportReport:
    """Convenience wrapper: build the boundary from ``trusted_root`` and load."""

    return load_package(
        package_dir, trusted_boundary=TrustedInputBoundary(root=Path(trusted_root))
    )


__all__ = [
    "RECORD_PROPERTY_SET_CHECK",
    "load_package",
    "load_package_from_paths",
]
