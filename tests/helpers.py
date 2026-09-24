"""Package fixture builder for the SIMULATED Layer-1 test suite.

All fixtures produced here are **SIMULATED** (``§4.3.9``): synthetic records built from
the registered canonical property literals, never real customer data, never a real
enterprise baseline.

The builder intentionally allows low-level byte control so that acceptance and
rejection behaviour can be exercised against the exact contract text instead of a
convenient subset of it.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

MANIFEST_FILENAME = "manifest.json"

BUILDING_MATERIALS = "Production Requirement"
INVENTORY = "Inventory Snapshot"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode_json(value: Any) -> bytes:
    """Encode a fixture value as UTF-8 JSON without a BOM."""

    return json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8")


@dataclass
class DatasetSpec:
    """One included logical dataset entry plus the artifact payload to write."""

    role: str = BUILDING_MATERIALS
    artifact: str = "requirement.json"
    records: list[dict[str, Any]] = field(default_factory=list)
    record_count: int | None = None
    integrity_evidence: str | None = None
    provenance_ref: str = "simulated://requirement"
    #: Raw bytes to write instead of the encoded ``records`` (malformed-input tests).
    artifact_bytes: bytes | None = None
    #: Drop the entry's ``record_count`` property entirely.
    omit_record_count: bool = False
    #: Drop the entry's ``integrity_evidence`` property entirely.
    omit_integrity: bool = False
    #: Extra properties merged into this dataset entry object.
    extra_entry_properties: dict[str, Any] = field(default_factory=dict)
    #: Override the artifact file name actually written (path / alias tests).
    written_filename: str | None = None
    #: Write the artifact outside the package and point the reference at it.
    external_target: Path | None = None


@dataclass
class PackageSpec:
    """A whole Snapshot Package fixture."""

    datasets: list[DatasetSpec] = field(default_factory=list)
    package_id: str = "SIMULATED-PKG-0001"
    contract_version: str = "v0.2"
    created_at: str = "2026-01-05T08:30:00Z"
    environment: str = "SIMULATED"
    evidence_classification: str = "SIMULATED"
    completeness_state: str = "COMPLETE"
    #: Extra properties merged into the ``"package"`` block.
    extra_package_properties: dict[str, Any] = field(default_factory=dict)
    #: Extra properties merged into the Manifest top level.
    extra_manifest_properties: dict[str, Any] = field(default_factory=dict)
    #: Replace the whole Manifest payload (raw bytes) -- e.g. duplicate-key tests.
    manifest_bytes: bytes | None = None
    #: Drop the ``"datasets"`` grouping entirely.
    omit_datasets: bool = False
    #: Drop the ``"package"`` grouping entirely.
    omit_package_block: bool = False
    #: Extra files written into the package root: ``name -> bytes``.
    extra_root_files: dict[str, bytes] = field(default_factory=dict)
    #: Extra subdirectories created in the package root: ``name -> files``.
    extra_root_dirs: dict[str, dict[str, bytes]] = field(default_factory=dict)


@dataclass
class BuiltPackage:
    """Paths and facts about a materialised fixture package."""

    root: Path
    boundary_root: Path
    manifest_path: Path
    artifact_paths: dict[str, Path]
    artifact_digests: dict[str, str]
    manifest_raw: bytes


def _artifact_bytes(spec: DatasetSpec) -> bytes:
    if spec.artifact_bytes is not None:
        return spec.artifact_bytes
    return encode_json(spec.records)


def build_package(
    root: Path,
    spec: PackageSpec,
    *,
    boundary_root: Path | None = None,
) -> BuiltPackage:
    """Materialise ``spec`` under ``root`` and return the fixture facts."""

    root.mkdir(parents=True, exist_ok=True)
    artifact_paths: dict[str, Path] = {}
    artifact_digests: dict[str, str] = {}
    entries: list[dict[str, Any]] = []

    for dataset in spec.datasets:
        payload = _artifact_bytes(dataset)
        digest = sha256_hex(payload)
        written_name = dataset.written_filename or Path(dataset.artifact).name
        target_path = dataset.external_target or (root / written_name)

        if dataset.external_target is not None:
            dataset.external_target.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(payload)

        artifact_paths[dataset.artifact] = target_path
        artifact_digests[dataset.artifact] = digest

        entry: dict[str, Any] = {"role": dataset.role, "artifact": dataset.artifact}
        if not dataset.omit_record_count:
            declared = (
                dataset.record_count
                if dataset.record_count is not None
                else len(dataset.records)
            )
            entry["record_count"] = declared
        entry["provenance_ref"] = dataset.provenance_ref
        if not dataset.omit_integrity:
            entry["integrity_evidence"] = (
                dataset.integrity_evidence
                if dataset.integrity_evidence is not None
                else digest
            )
        entry.update(dataset.extra_entry_properties)
        entries.append(entry)

    package_block: dict[str, Any] = {
        "snapshot_package_id": spec.package_id,
        "contract_version": spec.contract_version,
        "created_at": spec.created_at,
        "environment": spec.environment,
        "evidence_classification": spec.evidence_classification,
        "completeness_state": spec.completeness_state,
    }
    package_block.update(spec.extra_package_properties)

    manifest: dict[str, Any] = {}
    if not spec.omit_package_block:
        manifest["package"] = package_block
    if not spec.omit_datasets:
        manifest["datasets"] = entries
    manifest.update(spec.extra_manifest_properties)

    manifest_raw = spec.manifest_bytes if spec.manifest_bytes is not None else encode_json(manifest)
    manifest_path = root / MANIFEST_FILENAME
    manifest_path.write_bytes(manifest_raw)

    for name, payload in spec.extra_root_files.items():
        (root / name).write_bytes(payload)

    for name, files in spec.extra_root_dirs.items():
        directory = root / name
        directory.mkdir(parents=True, exist_ok=True)
        for file_name, payload in files.items():
            (directory / file_name).write_bytes(payload)

    return BuiltPackage(
        root=root,
        boundary_root=boundary_root if boundary_root is not None else root.parent,
        manifest_path=manifest_path,
        artifact_paths=artifact_paths,
        artifact_digests=artifact_digests,
        manifest_raw=manifest_raw,
    )


def write_file(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def valid_package(
    root: Path,
    *,
    boundary_root: Path | None = None,
    datasets: Iterable[DatasetSpec] | None = None,
    package_id: str = "SIMULATED-PKG-0001",
    **spec_kwargs: Any,
) -> BuiltPackage:
    """A minimal contract-conformant package: one requirement dataset, one record."""

    if datasets is None:
        datasets = [
            DatasetSpec(
                records=[
                    {
                        "plant_id": "P1",
                        "material_code": "M1",
                        "required_date": "2026-02-01",
                        "ProductionQty": "10",
                        "BOMComponentQty": "2",
                    }
                ]
            )
        ]
    spec = PackageSpec(datasets=list(datasets), package_id=package_id, **spec_kwargs)
    return build_package(root, spec, boundary_root=boundary_root)

