"""Fixed SIMULATED input composition (ADR-003 D1). No business formulas.
Input/evidence lineage: registered Q3 C1 composition at main ba99e47.
Independent runtime module: never imports tests or observation tooling.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any
from snapshot_loader import PhaseAHandoff, TrustedInputBoundary, load_package, run_first_tranche_pipeline
from snapshot_loader.canonical_objects import (BomParentContextHandoff, EffectiveDemandRelationHandoff, HandoffEvidence, InventoryScopeHandoff, LossRateHandoff)

PLANT_ID: str = "SIM-P1"

MATERIAL_CODE: str = "SIM-M2"

SUBSTITUTE_MATERIAL_CODE: str = "SIM-M3"

REQUIRED_DATE: str = "2026-10-20"

SNAPSHOT_TIME: str = "2026-10-01T08:00:00Z"

ANALYSIS_DATE: str = "2026-10-01"

PACKAGE_ID: str = "SIMULATED-Q3-OBS-PKG-0001"

PACKAGE_CREATED_AT: str = "2026-10-01T08:00:00Z"

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

def fixture_records() -> dict[str, list[dict[str, Any]]]:
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
    if APPLICABLE_MOQ is not None:
        policy.append(
            _with_provenance(
                {
                    "plant_id": PLANT_ID,
                    "material_code": MATERIAL_CODE,
                    "ApplicableMOQ": APPLICABLE_MOQ,
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
    boundary_root: Path
) -> Path:
    """Materialise the fixed SIMULATED package under ``boundary_root`` and return its directory.

    The package is a direct child of the configured trusted boundary, as Layer-1 requires.  This
    writes **fixture data only**; it contains no business formula and no expected business result.
    """

    package_root = boundary_root / "q3-observation-package"
    package_root.mkdir(parents=True, exist_ok=True)
    records = fixture_records()
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

def fixture_handoff(accepted: Any, run_id: str) -> PhaseAHandoff:
    """The registered Phase A in-process handoff of the fixed fixture (fixture data only)."""

    return PhaseAHandoff(
        analysis_run_id=run_id,
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

def analyze(boundary_root: Path, run_id: str):
    package = write_simulated_fixture(boundary_root)
    report = load_package(package, trusted_boundary=TrustedInputBoundary(root=boundary_root))
    if not report.accepted or report.accepted_package is None:
        raise RuntimeError("fixed scenario acceptance failed")
    result = run_first_tranche_pipeline(report, fixture_handoff(report.accepted_package, run_id))
    recommendation = result.procurement_recommendation.for_family(PLANT_ID, MATERIAL_CODE)
    if recommendation is None or not recommendation.has_numeric_result:
        raise RuntimeError("fixed scenario analysis failed")
    return result
