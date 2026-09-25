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
  * §4.2.2, §4.2.11 -- §4.2.14 -- logical types, time semantics, quantity
    constraints, status vocabulary
* ``docs/design/specs/data-integration/data-validation.md``
  * §4.4.2 / §4.4.25   -- Layer-2 boundary; a field-level issue never rejects a package
  * §4.4.26 -- §4.4.35 -- present-value field rules (range, vocabulary, representation)
  * §4.4.39 / §4.4.42  -- valid zero preservation; no stringency inflation
  * §4.4.78 -- §4.4.100 -- inherited issue taxonomy (8 categories / 12 reasons)
* ``docs/design/specs/data-integration/snapshot-import-contract.md``
  * §4.3.22 ``C-2`` -- JSON ``null`` vs property omission
  * §4.3.22 ``C-3`` -- ``C-10`` -- registered scalar representations
  * §4.3.30 -- deferred applicability / input-channel items (Layer-2 narrowing)
"""

from __future__ import annotations

from dataclasses import dataclass

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

# --- Human Decision: Layer-1 carrier presence = REQUIRED ------------------------
#
# The approved semantic set must actually be carried by the Manifest (§4.3.8 /
# §4.3.25 A).  Layer 1 verifies **presence in the approved carrier location** only:
# it does not validate the value semantics of these carriers.  In particular
# ``CF-1`` is preserved -- ``completeness_state`` presence is required, but its value
# does not gate acceptance.
#
# Where existing canonical authority already registers a representation, that
# representation is enforced (``snapshot_package_id`` and ``contract_version`` as
# exact JSON strings, ``record_count`` as a JSON integer, ``integrity_evidence`` as a
# 64-character lowercase hex SHA-256 digest).  No other value rule is introduced.
REQUIRED_PACKAGE_BLOCK_PROPERTIES: tuple[str, ...] = (
    "snapshot_package_id",
    "contract_version",
    "created_at",
    "environment",
    "evidence_classification",
    "completeness_state",
)

# --- §4.3.25 B: dataset entry literals -----------------------------------------
DATASET_ENTRY_PROPERTIES: tuple[str, ...] = (
    "role",
    "artifact",
    "record_count",
    "provenance_ref",
    "integrity_evidence",
)

#: Carriers that must be present on every included dataset entry (Human Decision).
#: ``provenance_ref`` presence is required; its value format is **not** constrained,
#: because no canonical authority registers a ``provenance_ref`` representation.
REQUIRED_DATASET_ENTRY_PROPERTIES: tuple[str, ...] = (
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

# --- §4.3.28 C.2 / D.4: which Layer-1 gates are mandatory ----------------------
#
# ``FR-3`` requires a prerequisite-blocked check to be reported as ``not evaluable``
# rather than as passed, and ``Decision 10A`` makes an unestablishable required
# consistency fail-closed.  A package may therefore only become ``ACCEPTED`` when
# every check in this set is actually *decided* (``passed`` or ``failed``).
#
# A check whose absence merely limits a *detection capability* -- without making the
# acceptance decision itself undecidable -- is deliberately absent from this set and
# is reported as an advisory ``not evaluable`` notice instead:
#   ``artifacts.independent_target_identity`` (platform exposes no file identity)
#   ``package.stable_root_identity``          (platform exposes no root identity)
MANDATORY_LAYER1_CHECKS: frozenset[str] = frozenset(
    {
        "trust_boundary.configured_and_verifiable",
        "manifest.readable",
        "manifest.strict_parse",
        "manifest.top_level_shape",
        "manifest.unknown_property",
        "manifest.package_block_unknown_property",
        "manifest.package_identity",
        "manifest.contract_version_present",
        "manifest.contract_version_supported",
        "manifest.package_block_required_carriers",
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
        "artifact.record_property_known_set",
        "artifacts.record_count_consistency",
        "package.root_listable",
        "package.unreferenced_root_artifact",
        "package.final_root_content_set",
        "package.acceptance_time_stable_view",
    }
)

# --- §4.4.2 / §4.4.80 / §4.4.81: inherited taxonomy (no new reason may be added) -
LAYER_1: int = 1
LAYER_2: int = 2

CATEGORY_PACKAGE_STRUCTURE: str = "PACKAGE_STRUCTURE"
REASON_STRUCTURAL_INCONSISTENCY: str = "STRUCTURAL_INCONSISTENCY"

# Layer-2 fields use only these inherited reasons (§4.4.81); none is added here.
CATEGORY_FIELD_VALUE: str = "FIELD_VALUE"
CATEGORY_IDENTITY_RESOLUTION: str = "IDENTITY_RESOLUTION"

REASON_INVALID_TYPE: str = "INVALID_TYPE"
REASON_OUT_OF_DEFINED_RANGE: str = "OUT_OF_DEFINED_RANGE"
REASON_INVALID_DEFINED_STATUS: str = "INVALID_DEFINED_STATUS"
REASON_UNRESOLVED_IDENTITY: str = "UNRESOLVED_IDENTITY"

#: Canonicalization semantics that cannot be reliably resolved from the approved Design
#: use the **inherited** ``§4.4.80`` category / ``§4.4.81`` reason, exactly as
#: ``§4.4.102`` D registers.  ``SEMANTIC_UNRESOLVED`` is deliberately distinct from
#: ``FIELD_VALUE`` / ``MISSING``: the latter means a *resolved* context whose required
#: value is absent (``§4.4.15`` root A), while this one means the context /
#: applicability itself could not be established (root B, ``§4.4.95``).  No new
#: category, reason, severity or error code is introduced.
CATEGORY_SEMANTIC_RESOLUTION: str = "SEMANTIC_RESOLUTION"
REASON_SEMANTIC_UNRESOLVED: str = "SEMANTIC_UNRESOLVED"

# --- Layer-2 reporting surface: no new status vocabulary ------------------------
#
# Current canonical authority registers exactly these status vocabularies, and Layer 2
# introduces none of its own:
#
#   package disposition : ``ACCEPTED`` / ``REJECTED`` / ``UNUSABLE``  (§4.3.28 B.1)
#   trusted reuse       : ``RE-VERIFIED``                            (§4.3.28 C.3)
#   check state         : ``passed`` / ``failed`` / ``not_evaluable`` (§4.3.28 B.2 FR-3)
#
# A Layer-2 ``outcome`` / report-level aggregate ``evaluation`` string would be a new,
# unapproved status contract (Issue #122 forbids new enums), so Layer 2 reports its
# result through the **existing** package ``disposition`` (§4.4.25 keeps an accepted
# package ``ACCEPTED`` even when canonical evidence defects are reported; the only
# exception is the inherited ``MG-2`` re-verification failure, which is already
# expressible as the existing ``UNUSABLE`` disposition) plus the per-check states.

# --- §4.3.22: registered scalar representations (Layer-2 basis) -----------------
#
# ``C-3`` registers ``YYYY-MM-DD``; ``C-4`` registers "ISO 8601 / RFC 3339
# compatible" with an explicit UTC offset or ``Z`` and forbids silent timezone
# inference.  The patterns below encode **only** those registered lexical forms; the
# logical validity of the date / instant they denote is a separate obligation carried
# by the logical type declared in ``§4.2.2`` (``§4.4.27`` / ``§4.4.28`` -- ``§4.4.34``
# require a *valid* ``DATE`` / *valid temporal value*).
DATE_PATTERN: str = r"[0-9]{4}-[0-9]{2}-[0-9]{2}"
TIMESTAMP_PATTERN: str = (
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt ]"
    r"[0-9]{2}:[0-9]{2}(?::[0-9]{2}(?:\.[0-9]+)?)?"
    r"(?:[Zz]|[+-][0-9]{2}:[0-9]{2})"
)
#: ``C-5`` registers a **base-10 decimal string** and forbids binary floating point,
#: locale commas, thousands separators and scientific notation.  It does **not**
#: register a leading-zero prohibition or any other lexical tightening, so none is
#: encoded here (``§4.4.24``: do not invent what is undefined).
DECIMAL_STRING_PATTERN: str = r"[+-]?[0-9]+(?:\.[0-9]+)?"

# --- §4.4.26 ～ §4.4.35: per-logical-type Layer-2 rule kind ---------------------
#
# ``kind`` selects the registered present-value rule set for a logical type.  It is
# a classification of *already registered* rules, not a new validation semantic.
KIND_IDENTIFIER: str = "identifier"
KIND_ANALYSIS_RUN_ID: str = "analysis_run_id"
KIND_DATE: str = "date"
KIND_TIMESTAMP: str = "timestamp"
KIND_DECIMAL: str = "decimal"
KIND_NON_NEGATIVE: str = "non_negative"
KIND_RATIO: str = "ratio"
KIND_PERCENTAGE: str = "percentage"
KIND_STATUS: str = "status"
KIND_TEXT_CONTEXT: str = "text_context"

LOGICAL_TYPE_KINDS: dict[str, str] = {
    "IDENTIFIER": KIND_IDENTIFIER,
    "ANALYSIS_RUN_ID": KIND_ANALYSIS_RUN_ID,
    "DATE": KIND_DATE,
    "TIMESTAMP": KIND_TIMESTAMP,
    "DECIMAL_QUANTITY": KIND_DECIMAL,
    "NON_NEGATIVE_QUANTITY": KIND_NON_NEGATIVE,
    "RATIO": KIND_RATIO,
    "PERCENTAGE": KIND_PERCENTAGE,
    "STATUS": KIND_STATUS,
    "TEXT_CONTEXT": KIND_TEXT_CONTEXT,
}


@dataclass(frozen=True)
class Layer2FieldRule:
    """Present-value rule set for one canonical field (Layer-2 narrowed subset).

    ``vocabulary`` is ``None`` when the field's values are source-specific or have no
    globally registered vocabulary; in that case **no** allowlist may be built
    (``§4.4.33``).  ``authoritative`` records whether the present-value rules for this
    field are fully derivable from current authority: when ``False`` the field is
    reported as ``not evaluable`` instead of being silently skipped or guessed.

    ``minimum`` / ``maximum`` carry a **field-level** numeric bound taken verbatim
    from the existing authority (``§4.2.13`` of the Data Dictionary, the field's own
    Data Dictionary row, or ``§4.4.28`` -- ``§4.4.35``).  They exist because the
    registered *logical type* of a field does not always carry its bound: for example
    ``on_hand_qty`` is registered ``DECIMAL_QUANTITY`` while its own row defines
    ``on_hand_qty >= 0``.  No bound is encoded unless an authority already states it
    (``§4.4.24`` / ``§4.4.29``: "如果当前 Design 未定义更严格范围，不得新增").
    """

    name: str
    logical_type: str
    authoritative: bool = True
    vocabulary: tuple[str, ...] | None = None
    note: str = ""
    minimum: str | None = None
    minimum_exclusive: bool = False
    maximum: str | None = None
    maximum_exclusive: bool = False
    bound_authority: str = ""
    bound_reference: str = ""

    @property
    def kind(self) -> str:
        return LOGICAL_TYPE_KINDS[self.logical_type]


#: Present-value registry for the 30 v0.2 canonical record properties (§4.3.30 B.1).
#:
#: Only fields whose Data Dictionary / Data Validation entry registers present-value
#: rules are marked ``authoritative``.  Fields whose applicability or input channel
#: is deferred by ``§4.3.30`` keep their representation rule (``§4.3.22`` is
#: unconditional) but are flagged so that value-level judgement is not implied.
LAYER2_REGISTRY: tuple[Layer2FieldRule, ...] = (
    # §4.2.3 Identity & Context
    Layer2FieldRule("plant_id", "IDENTIFIER"),
    Layer2FieldRule("material_code", "IDENTIFIER"),
    Layer2FieldRule("supplier_id", "IDENTIFIER"),
    Layer2FieldRule("analysis_run_id", "ANALYSIS_RUN_ID"),
    Layer2FieldRule("AnalysisDate", "DATE"),
    # §4.2.4 Requirement / BOM
    Layer2FieldRule("required_date", "DATE"),
    Layer2FieldRule("ProductionQty", "NON_NEGATIVE_QUANTITY"),
    Layer2FieldRule("BOMComponentQty", "NON_NEGATIVE_QUANTITY"),
    Layer2FieldRule("loss_rate", "RATIO"),
    # §4.2.5 Inventory
    Layer2FieldRule(
        "inventory_status",
        "STATUS",
        vocabulary=("AVAILABLE", "INSPECTION", "FROZEN"),
    ),
    # ``on_hand_qty`` is registered ``DECIMAL_QUANTITY`` -- it is *not* in the §4.2.13
    # ``NON_NEGATIVE_QUANTITY`` list -- but its own Data Dictionary row defines
    # ``on_hand_qty < 0`` as illegal input ("不得 clamp to 0", §2.2.8), which is also
    # what §4.4.29 defers to ("按当前 Dictionary / Rule 已定义的范围校验").  The bound is
    # therefore carried per field, never by widening the ``DECIMAL_QUANTITY`` logical
    # type into a non-negative type.
    Layer2FieldRule(
        "on_hand_qty",
        "DECIMAL_QUANTITY",
        minimum="0",
        bound_authority="on_hand_qty < 0 为非法输入",
        bound_reference="§2.2.8 / §4.2.5 (Data Dictionary row) + §4.4.29",
    ),
    Layer2FieldRule("inventory_snapshot_time", "TIMESTAMP"),
    Layer2FieldRule("SafetyStock", "NON_NEGATIVE_QUANTITY"),
    # §4.2.6 Inbound
    Layer2FieldRule("ordered_qty", "NON_NEGATIVE_QUANTITY"),
    Layer2FieldRule("received_qty", "NON_NEGATIVE_QUANTITY"),
    Layer2FieldRule("effective_arrival_date", "DATE"),
    Layer2FieldRule(
        "inbound_status",
        "STATUS",
        vocabulary=(
            "OPEN",
            "CONFIRMED",
            "PARTIALLY_RECEIVED",
            "CANCELLED",
            "CLOSED",
            "COMPLETED",
        ),
        note="§2.6.3 conservative classification; §4.2.14 approved vocabulary",
    ),
    # §4.2.7 Substitute
    Layer2FieldRule("target_material_code", "IDENTIFIER"),
    Layer2FieldRule("substitute_material_code", "IDENTIFIER"),
    # ``substitution_ratio`` is registered ``RATIO``, but ``RATIO`` inherently admits
    # 0 while the field's own authority requires ``> 0``: §4.2.13
    # (``substitution_ratio | > 0 | §2.3.6``), the §4.2.7 Data Dictionary row
    # (``substitution_ratio > 0``) and §4.4.31 ("必须 > 0；missing / invalid 时不得默认
    # 1.0").  ``loss_rate`` is also ``RATIO`` but bounded ``0 <= loss_rate < 1``, so the
    # two RATIO fields genuinely differ and neither may inherit the other's bound.
    Layer2FieldRule(
        "substitution_ratio",
        "RATIO",
        minimum="0",
        minimum_exclusive=True,
        bound_authority="substitution_ratio > 0",
        bound_reference="§2.3.6 / §4.2.13 / §4.2.7 + §4.4.31",
    ),
    Layer2FieldRule(
        "approval_status",
        "STATUS",
        vocabulary=("APPROVED", "PENDING", "REJECTED", "UNKNOWN"),
        note="§4.2.14: only APPROVED participates; the others are known states",
    ),
    Layer2FieldRule("AllocatedSubstituteQty", "NON_NEGATIVE_QUANTITY"),
    # §4.2.8 Supplier
    Layer2FieldRule(
        "sourcing_status",
        "STATUS",
        vocabulary=None,
        note="§4.4.33: source vocabulary is SOURCE-SPECIFIC; no allowlist may exist",
    ),
    Layer2FieldRule("standard_lead_time_days", "NON_NEGATIVE_QUANTITY"),
    Layer2FieldRule("PerformancePeriod", "TEXT_CONTEXT"),
    Layer2FieldRule("PerformanceUpdatedAt", "TIMESTAMP"),
    Layer2FieldRule("DeliveryPerformance", "PERCENTAGE"),
    Layer2FieldRule("QualityPerformance", "PERCENTAGE"),
    # §4.2.9 Procurement
    Layer2FieldRule("RecommendationNeedDate", "DATE"),
    Layer2FieldRule("ApplicableMOQ", "NON_NEGATIVE_QUANTITY"),
)

LAYER2_FIELD_RULE_BY_NAME: dict[str, Layer2FieldRule] = {
    rule.name: rule for rule in LAYER2_REGISTRY
}

#: Fields that Layer 2 deliberately does not evaluate because their present-value
#: rules are not derivable from current authority, or because applicability is
#: deferred (§4.3.30).  They are reported as ``not evaluable`` with an explicit note.
LAYER2_NOT_EVALUABLE_FIELDS: dict[str, str] = {
    "PerformancePeriod": (
        "§4.4.34: measurement-period vocabulary is NOT defined by current design, so a "
        "present value cannot be judged invalid; defer to the later subtask that owns it"
    ),
    "sourcing_status": (
        "§4.4.33: source vocabulary is SOURCE-SPECIFIC; value legality is not decidable "
        "here and no allowlist may be built"
    ),
}

