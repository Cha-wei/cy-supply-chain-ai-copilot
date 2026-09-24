"""Registered POC v0.2 contract literals.

Every value in this module is an **exact literal registered by a Human-approved
canonical decision**.  Nothing here may be invented, normalised, or derived at
runtime.

Authorities (current `main` of Cha-wei/cy-supply-chain-ai-copilot):

* ``docs/design/specs/data-integration/snapshot-import-contract.md``
  * §4.3.22 ``C-1``/``C-9``  -- UTF-8 without BOM, strict JSON parse
  * §4.3.23 ``C``/``D``/``G`` -- flat package root, ``manifest.json``, ``.json`` artifacts
  * §4.3.25 ``A``/``B``/``D``/``E``/``F`` -- Manifest, dataset entry, record carriers
  * §4.3.28 ``A.1``/``A.2``   -- ``VC-1`` version token, ``UX-A`` unknown content policy
  * §4.3.28 ``D4``            -- acceptance gate and validation partial order
  * §4.3.28 ``E``             -- ``"_meta"`` known member set (Bundle 5)
  * §4.3.30                   -- Issue #118 Human Decision: v0.2 record-level wire binding
* ``docs/design/specs/data-integration/data-dictionary.md``
  * §4.2.3 -- §4.2.9 canonical field identifiers (incl. ``analysis_run_id``,
    ``inbound_status`` as registered by Issue #118)
"""

from __future__ import annotations

# --- §4.3.22 VC-1 / §4.3.28 A.1 -------------------------------------------------
CONTRACT_VERSION_PROPERTY: str = "contract_version"
SUPPORTED_CONTRACT_VERSION: str = "v0.2"

# --- §4.3.23 C / D --------------------------------------------------------------
MANIFEST_FILENAME: str = "manifest.json"
ARTIFACT_EXTENSION: str = ".json"

# --- §4.3.25 A: manifest grouping and package-scoped literals -------------------
GROUPING_PACKAGE: str = "package"
GROUPING_DATASETS: str = "datasets"

PACKAGE_SCOPED_PROPERTIES: tuple[str, ...] = (
    "snapshot_package_id",
    "contract_version",
    "created_at",
    "environment",
    "evidence_classification",
    "completeness_state",
)

MANIFEST_TOP_LEVEL_PROPERTIES: tuple[str, ...] = (
    GROUPING_PACKAGE,
    GROUPING_DATASETS,
)

# --- §4.3.25 B: dataset entry literals -----------------------------------------
DATASET_ENTRY_PROPERTIES: tuple[str, ...] = (
    "role",
    "artifact",
    "record_count",
    "provenance_ref",
    "integrity_evidence",
)

# --- §4.3.25 F / §4.3.28 E: reserved record-level carrier metadata namespace -----
RECORD_META_NAMESPACE: str = "_meta"

META_MEMBERS: tuple[str, ...] = ("provenance_associations",)

ASSOCIATION_MEMBERS: tuple[str, ...] = (
    "observation",
    "evidence",
    "mapping_basis",
)

REQUIRED_ASSOCIATION_MEMBERS: tuple[str, ...] = ("observation", "evidence")

OPTIONAL_ASSOCIATION_MEMBERS: tuple[str, ...] = ("mapping_basis",)

# --- §4.3.28 D.1 / D.2: integrity contract -------------------------------------
INTEGRITY_ALGORITHM: str = "sha256"
INTEGRITY_EVIDENCE_LENGTH: int = 64
INTEGRITY_HEX_DIGITS: str = "0123456789abcdef"

# --- §4.3.30 B.1: frozen v0.2 canonical record property literals ----------------
#
# Explicit, closed, version-bound enumeration registered by the Issue #118 Human
# Decision.  It is deliberately written out literally: the set must NOT be derived
# at runtime from the Data Dictionary, and must NOT be extended by any agent.
V02_CANONICAL_RECORD_PROPERTIES: tuple[str, ...] = (
    # §4.2.3 Identity & Context
    "plant_id",
    "material_code",
    "supplier_id",
    "analysis_run_id",
    "AnalysisDate",
    # §4.2.4 Requirement / BOM
    "required_date",
    "ProductionQty",
    "BOMComponentQty",
    "loss_rate",
    # §4.2.5 Inventory
    "inventory_status",
    "on_hand_qty",
    "inventory_snapshot_time",
    "SafetyStock",
    # §4.2.6 Inbound
    "ordered_qty",
    "received_qty",
    "effective_arrival_date",
    "inbound_status",
    # §4.2.7 Substitute
    "target_material_code",
    "substitute_material_code",
    "substitution_ratio",
    "approval_status",
    "AllocatedSubstituteQty",
    # §4.2.8 Supplier
    "sourcing_status",
    "standard_lead_time_days",
    "PerformancePeriod",
    "PerformanceUpdatedAt",
    "DeliveryPerformance",
    "QualityPerformance",
    # §4.2.9 Procurement
    "RecommendationNeedDate",
    "ApplicableMOQ",
)

V02_CANONICAL_RECORD_PROPERTY_SET: frozenset[str] = frozenset(
    V02_CANONICAL_RECORD_PROPERTIES
)

# --- §4.3.28 B.1: package disposition and failure expression -------------------
DISPOSITION_ACCEPTED: str = "ACCEPTED"
DISPOSITION_REJECTED: str = "REJECTED"
DISPOSITION_UNUSABLE: str = "UNUSABLE"

# --- §4.3.28 B.2: evaluation state of an individual Layer-1 check --------------
EVALUATION_PASSED: str = "passed"
EVALUATION_FAILED: str = "failed"
EVALUATION_NOT_EVALUABLE: str = "not_evaluable"

# --- §4.4.2 / §4.4.80 / §4.4.81: inherited taxonomy (no new reason may be added) -
LAYER_1: int = 1

CATEGORY_PACKAGE_STRUCTURE: str = "PACKAGE_STRUCTURE"
REASON_STRUCTURAL_INCONSISTENCY: str = "STRUCTURAL_INCONSISTENCY"
