"""Controlled Snapshot loader, Layer-1 package acceptance, and Layer-2 validation (POC v0.2).

Deterministic tranches delivered here:

    Snapshot loader / import
      controlled JSON package + configured trusted input boundary
        -> package acceptance, or an existing rejection / not-evaluable outcome
        -> a bound accepted content view that downstream trusted reuse consumes

    Layer 2 -- Canonical Evidence Validation (:func:`validate_layer2`)
      the narrowed non-null present-value subset: logical type, registered scalar
      representation, approved numeric range, approved canonical status vocabulary,
      and identifier non-empty boundary

    First deterministic tranche composition (:func:`run_first_tranche_pipeline`)
      Layer 1 -> Layer 2 -> Phase A canonical objects -> ``BR-REQUIREMENT-001`` ／
      ``BR-INVENTORY-001`` ／ ``BR-INBOUND-001`` ／ ``BR-SUBSTITUTE-001`` ->
      ``BR-SHORTAGE-001`` -> Phase B procurement policy input ->
      ``BR-PROCUREMENT-001`` -> Supplier Risk runtime input seam (``A′``) ->
      ``BR-SUPPLIER-RISK-001``, end to end and in memory, over the registered public
      entry points of each module.

    P0 AI Explanation -- Q3 slice (:func:`explain_q3`)
      an existing ``ProcurementRecommendation`` -> a read-only non-canonical Q3 projection
      -> one provider-agnostic call -> a response artifact carrying only the four §5.5
      meanings, plus a deterministic fail-closed path.  The provider is injected as a plain
      protocol; this package performs no network call, reads no credential or environment
      secret and selects no provider, model, framework or tool protocol.

Canonical authority:

* ``docs/design/specs/data-integration/snapshot-import-contract.md``
  §4.3.22 -- §4.3.31 (implementation: §4.3.28 ``D4`` acceptance gate)
* ``docs/design/specs/data-integration/data-validation.md``
  §4.4.2 / §4.4.24 -- §4.4.44 / §4.4.79 -- §4.4.83 (inherited taxonomy, reused unchanged)
* ``docs/design/poc-design-v0.2.md`` §2.1 -- §2.7 (business rules) and §10.1 B ／ C
  (first-tranche module responsibilities and acceptance boundary)
* ``docs/design/poc-design-v0.2.md`` §5.3 (Q3) ／ §5.5 (response meanings) ／ §5.6 -- §5.12
  (explanation boundaries) and §5.20 (Q3 runtime implementation record), plus §7.1
  (Secret Handling minimum contract)
* ``docs/architecture/adr-001-deterministic-core.md`` (minimum architecture: the thin CLI
  calls this application orchestration; the core never calls back into the CLI)
* ``docs/architecture/adr-002-p0-ai-explanation-minimum-runtime.md`` (P0 AI Explanation
  minimum runtime: in-process, single provider-agnostic call, fail-closed)

Scope boundary (deliberately narrow):

* **in scope** -- the first deterministic tranche of ``POC Design v0.2`` §10.1 B: Layer-1
  package acceptance, Layer-2 canonical evidence validation, Phase A canonical object
  construction, the §2.1 -- §2.7 deterministic business rules, the procurement
  recommendation result, the Supplier Risk evidence result, and their in-process
  composition.  Every one of those stages is the registered module entry point; the
  composition adds no business semantics of its own.  Also in scope is the provider-neutral
  P0 AI Explanation **Q3** runtime core (:func:`explain_q3` / ``build_q3_projection``):
  a read-only projection of registered quantities plus an injected provider seam and a
  deterministic fail-closed path.
* **out of scope** -- Web ／ API ／ service, a real hosted LLM provider adapter (network,
  provider SDK, provider ／ model selection, environment credential reader), Agent
  Framework ／ Tool protocol, HITL, RBAC ／ secrets, persistent Audit, database ／ persistent
  business state, real ERP ／ SRM Adapter, production write-back, P1, and every §6 -- §9
  just-in-time gate.

The core is importable and directly testable and does not depend on the CLI
(``POC Design v0.2`` §10.1 B; ADR-001).
"""

from __future__ import annotations

from .canonical_objects import (
    CANONICALIZATION_ROLES,
    CANONICALIZATION_ROLE_BY_LITERAL,
    INVENTORY_SCOPE_BASIS_BY_LITERAL,
    INVENTORY_SCOPE_BASIS_REGISTRY,
    INVENTORY_SCOPE_IN,
    INVENTORY_SCOPE_OUT,
    INVENTORY_SCOPE_SHAPE_PLANT_AGGREGATE,
    INVENTORY_SCOPE_SHAPE_WAREHOUSE,
    PHASE_A_ROLE_LITERALS,
    AnalysisRunContext,
    BomParentContextHandoff,
    CanonicalConstructionReport,
    CanonicalObject,
    CanonicalProperty,
    ContextValueReference,
    EffectiveDemandContextReference,
    UnresolvedEffectiveDemandContextReference,
    EffectiveDemandRelationHandoff,
    EvidenceReference,
    HandoffEvidence,
    InventoryScopeBasis,
    InventoryScopeContext,
    InventoryScopeHandoff,
    LossRateHandoff,
    PhaseAHandoff,
    RecordReference,
    SafetyStockHandoff,
    build_effective_demand_contexts,
    build_effective_demand_results,
    construct_canonical_objects,
)
from .constants import (
    CATEGORY_PROVENANCE,
    CONTRACT_VERSION_PROPERTY,
    DISPOSITION_ACCEPTED,
    DISPOSITION_REJECTED,
    DISPOSITION_UNUSABLE,
    MANIFEST_FILENAME,
    REASON_PROVENANCE_MISMATCH,
    REASON_PROVENANCE_UNRESOLVED,
    SUPPORTED_CONTRACT_VERSION,
    V02_CANONICAL_RECORD_PROPERTIES,
)
from .issues import Check, Issue
from .result_binding import (
    ANALYSIS_RUN_COMPONENTS,
    AnalysisRunBindingError,
    require_same_accepted_package,
    require_same_analysis_run,
)
from .exact_quantity import (
    ExactQuantity,
    parse_exact_quantity,
    parse_non_negative_quantity,
)
from .explanation_q3 import (
    COMPLETENESS_COMPLETE,
    COMPLETENESS_DATA_INCOMPLETE,
    COMPLETENESS_RECOMMENDATION_NOT_STATED,
    Q3_FACT_FIELDS,
    Q3_GRAIN_FIELDS,
    Q3_QUESTION,
    build_q3_projection,
    explain_q3,
)
from .explanation_seam import (
    NOTE_AI_EXPLANATION_UNAVAILABLE,
    NOTE_INCOMPLETE,
    NOTE_NO_RECOMMENDATION_BY_DESIGN,
    NOTE_PROVIDER_UNAVAILABLE,
    NOTE_RECOMMENDATION_UNAVAILABLE,
    NOTE_RESPONSE_UNACCEPTABLE,
    OUTCOME_EXPLAINED,
    OUTCOME_NO_RECOMMENDATION_BY_DESIGN,
    OUTCOME_PROVIDER_UNAVAILABLE,
    OUTCOME_RECOMMENDATION_INCOMPLETE,
    OUTCOME_RECOMMENDATION_UNAVAILABLE,
    OUTCOME_RESPONSE_UNACCEPTABLE,
    RESPONSE_KEYS,
    ExplanationProvider,
    ExplanationResponse,
    ExplanationResult,
    provider_payload,
    validate_provider_response,
)
from .inbound_calculation import (
    EFFECTIVE_INBOUND_DATA_INCOMPLETE,
    ELIGIBLE_INBOUND_STATUSES,
    INBOUND_RULE_ID,
    INELIGIBLE_INBOUND_STATUSES,
    REGISTERED_INBOUND_STATUSES,
    EffectiveInboundEvaluation,
    EffectiveInboundResult,
    EffectiveInboundTarget,
    UpstreamRequirementTrace,
    compute_effective_inbound,
    remaining_inbound_qty,
)
from .inventory_calculation import (
    ELIGIBLE_INVENTORY_STATUSES,
    INELIGIBLE_INVENTORY_STATUSES,
    INVENTORY_DATA_INCOMPLETE,
    INVENTORY_RULE_ID,
    REGISTERED_INVENTORY_STATUSES,
    InventoryCalculationResult,
    InventoryEvaluation,
    InventoryTarget,
    compute_opening_usable_inventory,
)
from .layer2 import (
    LAYER2_PRESENT_VALUE_RULES,
    LAYER2_REGISTRY,
    Layer2Check,
    Layer2Report,
    validate_layer2,
)
from .loader import RECORD_PROPERTY_SET_CHECK, load_package, load_package_from_paths
from .path_scope import validate_artifact_filename
from .report import ImportReport
from .requirement_calculation import (
    OUTCOME_DATA_INCOMPLETE,
    RULE_ID,
    RequirementCalculation,
    RequirementCalculationResult,
    compute_requirement_calculation,
)
from .strict_json import StrictJsonError, parse_strict_json
from .procurement_policy_input import (
    PROCUREMENT_POLICY_INPUT_BASIS_BY_LITERAL,
    PROCUREMENT_POLICY_INPUT_OUTCOMES,
    PROCUREMENT_POLICY_INPUT_REGISTRY,
    PROCUREMENT_POLICY_INPUT_STAGE,
    PROCUREMENT_POLICY_INPUT_UNRESOLVED,
    PROCUREMENT_POLICY_OBSERVATION,
    ProcurementPolicyInputBasis,
    ProcurementPolicyInputContext,
    ProcurementPolicyInputResult,
    compute_procurement_policy_input,
)
from .procurement_recommendation import (
    PROCUREMENT_RECOMMENDATION_RULE_ID,
    PROCUREMENT_RECOMMENDATION_UNRESOLVED,
    ROOT_MOQ_INPUT_UNRESOLVED,
    ROOT_POLICY_PARTITION_INCONSISTENT,
    ROOT_POLICY_PARTITION_UNRESOLVED,
    ROOT_SHORTAGE_INPUT_INCONSISTENT,
    ROOT_SHORTAGE_INPUT_UNRESOLVED,
    ProcurementRecommendation,
    ProcurementRecommendationResult,
    UpstreamResultReference,
    compute_procurement_recommendation,
)
from .shortage_calculation import (
    CLASSIFICATIONS,
    CLASSIFICATION_BUFFER_BREACH,
    CLASSIFICATION_DATA_INCOMPLETE,
    CLASSIFICATION_NORMAL,
    CLASSIFICATION_SHORTAGE,
    SHORTAGE_DATA_INCOMPLETE,
    SHORTAGE_GRAIN_PROPERTIES,
    SHORTAGE_RULE_ID,
    SUPPLY_FROM_INVENTORY_SNAPSHOT,
    SUPPLY_FROM_SOURCE_RESERVATION,
    ShortageCalculationResult,
    ShortageGrain,
    compute_shortage,
)
from .substitute_calculation import (
    APPROVED_APPROVAL_STATUS,
    CONSERVATION_CROSS_CONTEXT_UNRESOLVED,
    CONSERVATION_OVERLAP_UNRESOLVED,
    CONSERVATION_OVER_ALLOCATED,
    CONSERVATION_SOURCE_SUPPLY_UNRESOLVED,
    CONSERVATION_WITHIN_LIMIT,
    INELIGIBLE_APPROVAL_STATUSES,
    REGISTERED_APPROVAL_STATUSES,
    SUBSTITUTE_DATA_INCOMPLETE,
    SUBSTITUTE_JOIN_PROPERTIES,
    SUBSTITUTE_RULE_ID,
    ConservationGroup,
    SourceDemandContext,
    SubstituteCalculationResult,
    SubstituteEvaluation,
    SubstituteTarget,
    TARGET_CONTEXT_PROPERTIES,
    compute_substitute_supply,
)
from .supplier_risk_input import (
    ELIGIBILITY_ELIGIBLE,
    ELIGIBILITY_INELIGIBLE,
    ELIGIBILITY_UNRESOLVED,
    FAIL_CLOSED_EVIDENCE_OUTCOME,
    IDENTITY_FINDING_TARGETS,
    MATERIAL_IDENTITY_TARGET,
    PAIR_IDENTITY_COMPONENTS,
    PERFORMANCE_OBSERVATION_FIELDS,
    PLANT_MATERIAL_IDENTITY_ROLE,
    PLANT_MATERIAL_IDENTITY_TARGET,
    ROOT_CONFLICTING_RELATIONSHIP_EVIDENCE,
    ROOT_IDENTITY_UNRESOLVED,
    ROOT_MAPPING_AMBIGUOUS,
    ROOT_NEED_DATE_LINKAGE_ABSENT,
    ROOT_NEED_DATE_LINKAGE_MISMATCH,
    ROOT_NEED_DATE_UNRESOLVED,
    ROOT_NO_MAPPING_EVIDENCE,
    ROOT_PERFORMANCE_COMPETING_UNRESOLVED,
    ROOT_PERFORMANCE_OBSERVATION_ABSENT,
    ROOT_PERFORMANCE_OBSERVATION_MULTIPLE,
    ROOT_PERFORMANCE_OBSERVATION_UNRESOLVED,
    ROOT_RELATIONSHIP_ABSENT,
    ROOT_RELATIONSHIP_IDENTITY_UNRESOLVED,
    ROOT_SOURCING_STATUS_UNRESOLVED,
    SUPPLIER_ELIGIBILITY_BASIS_BY_LITERAL,
    SUPPLIER_ELIGIBILITY_OUTCOMES,
    SUPPLIER_ELIGIBILITY_REGISTRY,
    SUPPLIER_IDENTITY_ROLE,
    SUPPLIER_IDENTITY_TARGET,
    SUPPLIER_PERFORMANCE_TARGET,
    SUPPLIER_RELATIONSHIP_TARGET,
    SUPPLIER_RISK_EVIDENCE_STATUS_DATA_INCOMPLETE,
    SUPPLIER_RISK_INPUT_STAGE,
    SUPPLIER_RISK_OBSERVATION,
    SupplierEligibilityBasis,
    SupplierPerformanceObservation,
    SupplierRelationshipEligibility,
    SupplierRiskEvaluationContext,
    SupplierRiskEvidenceOutcome,
    SupplierRiskIdentityState,
    SupplierRiskInputResult,
    compute_supplier_risk_input,
)
from .supplier_risk_calculation import (
    REQUIRED_RISK_DIMENSIONS,
    RISK_DATA_INCOMPLETE,
    RISK_HIGH,
    RISK_LOW,
    RISK_MEDIUM,
    SEVERITY_ORDER,
    SUPPLIER_RISK_STAGE,
    SupplierRiskEvidenceCard,
    SupplierRiskResult,
    compute_supplier_risk,
)
from .first_tranche_pipeline import (
    LAYER1_NOT_ACCEPTED_REASON,
    LAYER1_PACKAGE_MISSING_REASON,
    PIPELINE_STAGES,
    STAGE_CANONICAL_OBJECTS,
    STAGE_INBOUND,
    STAGE_INVENTORY,
    STAGE_LAYER2,
    STAGE_PROCUREMENT_POLICY_INPUT,
    STAGE_PROCUREMENT_RECOMMENDATION,
    STAGE_REQUIREMENT,
    STAGE_SHORTAGE,
    STAGE_SNAPSHOT_LOADER,
    STAGE_SUBSTITUTE,
    STAGE_SUPPLIER_RISK_EVIDENCE,
    STAGE_SUPPLIER_RISK_INPUT_SEAM,
    FirstTranchePipelineResult,
    PipelineStage,
    run_first_tranche_pipeline,
    run_first_tranche_pipeline_from_paths,
)
from .trust import (
    AcceptedPackage,
    ContentView,
    ReuseVerdict,
    TrustedInputBoundary,
)

__all__ = [
    "AcceptedPackage",
    "AnalysisRunContext",
    "BomParentContextHandoff",
    "CANONICALIZATION_ROLES",
    "CANONICALIZATION_ROLE_BY_LITERAL",
    "ANALYSIS_RUN_COMPONENTS",
    "AnalysisRunBindingError",
    "CATEGORY_PROVENANCE",
    "REASON_PROVENANCE_MISMATCH",
    "REASON_PROVENANCE_UNRESOLVED",
    "require_same_analysis_run",
    "CanonicalConstructionReport",
    "CanonicalObject",
    "CanonicalProperty",
    "Check",
    "CONTRACT_VERSION_PROPERTY",
    "ContentView",
    "ContextValueReference",
    "DISPOSITION_ACCEPTED",
    "DISPOSITION_REJECTED",
    "DISPOSITION_UNUSABLE",
    "EFFECTIVE_INBOUND_DATA_INCOMPLETE",
    "ELIGIBLE_INBOUND_STATUSES",
    "ELIGIBLE_INVENTORY_STATUSES",
    "EffectiveDemandContextReference",
    "UnresolvedEffectiveDemandContextReference",
    "EffectiveDemandRelationHandoff",
    "EffectiveInboundEvaluation",
    "EffectiveInboundResult",
    "EffectiveInboundTarget",
    "ExactQuantity",
    "EvidenceReference",
    "HandoffEvidence",
    "INBOUND_RULE_ID",
    "INELIGIBLE_INBOUND_STATUSES",
    "INELIGIBLE_INVENTORY_STATUSES",
    "INVENTORY_DATA_INCOMPLETE",
    "INVENTORY_RULE_ID",
    "INVENTORY_SCOPE_BASIS_BY_LITERAL",
    "INVENTORY_SCOPE_BASIS_REGISTRY",
    "INVENTORY_SCOPE_IN",
    "INVENTORY_SCOPE_OUT",
    "INVENTORY_SCOPE_SHAPE_PLANT_AGGREGATE",
    "INVENTORY_SCOPE_SHAPE_WAREHOUSE",
    "ImportReport",
    "InventoryScopeBasis",
    "InventoryScopeContext",
    "InventoryScopeHandoff",
    "InventoryCalculationResult",
    "InventoryEvaluation",
    "InventoryTarget",
    "Issue",
    "LAYER2_PRESENT_VALUE_RULES",
    "LAYER2_REGISTRY",
    "Layer2Check",
    "Layer2Report",
    "LossRateHandoff",
    "MANIFEST_FILENAME",
    "OUTCOME_DATA_INCOMPLETE",
    "PHASE_A_ROLE_LITERALS",
    "PhaseAHandoff",
    "RECORD_PROPERTY_SET_CHECK",
    "REGISTERED_INBOUND_STATUSES",
    "RULE_ID",
    "RecordReference",
    "RequirementCalculation",
    "RequirementCalculationResult",
    "APPROVED_APPROVAL_STATUS",
    "CONSERVATION_CROSS_CONTEXT_UNRESOLVED",
    "CONSERVATION_OVERLAP_UNRESOLVED",
    "CONSERVATION_OVER_ALLOCATED",
    "CONSERVATION_SOURCE_SUPPLY_UNRESOLVED",
    "CONSERVATION_WITHIN_LIMIT",
    "PROCUREMENT_POLICY_INPUT_BASIS_BY_LITERAL",
    "PROCUREMENT_POLICY_INPUT_OUTCOMES",
    "PROCUREMENT_POLICY_INPUT_REGISTRY",
    "PROCUREMENT_POLICY_INPUT_STAGE",
    "PROCUREMENT_POLICY_INPUT_UNRESOLVED",
    "PROCUREMENT_POLICY_OBSERVATION",
    "ProcurementPolicyInputBasis",
    "ProcurementPolicyInputContext",
    "ProcurementPolicyInputResult",
    "compute_procurement_policy_input",
    "PROCUREMENT_RECOMMENDATION_RULE_ID",
    "PROCUREMENT_RECOMMENDATION_UNRESOLVED",
    "ROOT_MOQ_INPUT_UNRESOLVED",
    "ROOT_POLICY_PARTITION_INCONSISTENT",
    "ROOT_POLICY_PARTITION_UNRESOLVED",
    "ROOT_SHORTAGE_INPUT_INCONSISTENT",
    "ROOT_SHORTAGE_INPUT_UNRESOLVED",
    "ProcurementRecommendation",
    "ProcurementRecommendationResult",
    "UpstreamResultReference",
    "compute_procurement_recommendation",
    "require_same_accepted_package",
    "CLASSIFICATIONS",
    "CLASSIFICATION_BUFFER_BREACH",
    "CLASSIFICATION_DATA_INCOMPLETE",
    "CLASSIFICATION_NORMAL",
    "CLASSIFICATION_SHORTAGE",
    "INELIGIBLE_APPROVAL_STATUSES",
    "REGISTERED_APPROVAL_STATUSES",
    "SHORTAGE_DATA_INCOMPLETE",
    "SHORTAGE_GRAIN_PROPERTIES",
    "SHORTAGE_RULE_ID",
    "SUPPLY_FROM_INVENTORY_SNAPSHOT",
    "SUPPLY_FROM_SOURCE_RESERVATION",
    "SUBSTITUTE_DATA_INCOMPLETE",
    "SUBSTITUTE_JOIN_PROPERTIES",
    "SUBSTITUTE_RULE_ID",
    "ConservationGroup",
    "ShortageCalculationResult",
    "ShortageGrain",
    "SourceDemandContext",
    "SubstituteCalculationResult",
    "SubstituteEvaluation",
    "SubstituteTarget",
    "TARGET_CONTEXT_PROPERTIES",
    "compute_shortage",
    "compute_substitute_supply",
    "ReuseVerdict",
    "SUPPORTED_CONTRACT_VERSION",
    "SafetyStockHandoff",
    "StrictJsonError",
    "TrustedInputBoundary",
    "UpstreamRequirementTrace",
    "V02_CANONICAL_RECORD_PROPERTIES",
    "build_effective_demand_contexts",
    "build_effective_demand_results",
    "compute_effective_inbound",
    "compute_opening_usable_inventory",
    "compute_requirement_calculation",
    "construct_canonical_objects",
    "load_package",
    "load_package_from_paths",
    "parse_exact_quantity",
    "parse_non_negative_quantity",
    "parse_strict_json",
    "remaining_inbound_qty",
    "validate_artifact_filename",
    "validate_layer2",
    "FirstTranchePipelineResult",
    "LAYER1_NOT_ACCEPTED_REASON",
    "LAYER1_PACKAGE_MISSING_REASON",
    "PIPELINE_STAGES",
    "PipelineStage",
    "STAGE_CANONICAL_OBJECTS",
    "STAGE_INBOUND",
    "STAGE_INVENTORY",
    "STAGE_LAYER2",
    "STAGE_PROCUREMENT_POLICY_INPUT",
    "STAGE_PROCUREMENT_RECOMMENDATION",
    "STAGE_REQUIREMENT",
    "STAGE_SHORTAGE",
    "STAGE_SNAPSHOT_LOADER",
    "STAGE_SUBSTITUTE",
    "STAGE_SUPPLIER_RISK_EVIDENCE",
    "STAGE_SUPPLIER_RISK_INPUT_SEAM",
    "run_first_tranche_pipeline",
    "run_first_tranche_pipeline_from_paths",
    "COMPLETENESS_COMPLETE",
    "COMPLETENESS_DATA_INCOMPLETE",
    "COMPLETENESS_RECOMMENDATION_NOT_STATED",
    "ExplanationProvider",
    "ExplanationResponse",
    "ExplanationResult",
    "NOTE_AI_EXPLANATION_UNAVAILABLE",
    "NOTE_INCOMPLETE",
    "NOTE_NO_RECOMMENDATION_BY_DESIGN",
    "NOTE_PROVIDER_UNAVAILABLE",
    "NOTE_RECOMMENDATION_UNAVAILABLE",
    "NOTE_RESPONSE_UNACCEPTABLE",
    "OUTCOME_EXPLAINED",
    "OUTCOME_NO_RECOMMENDATION_BY_DESIGN",
    "OUTCOME_PROVIDER_UNAVAILABLE",
    "OUTCOME_RECOMMENDATION_INCOMPLETE",
    "OUTCOME_RECOMMENDATION_UNAVAILABLE",
    "OUTCOME_RESPONSE_UNACCEPTABLE",
    "Q3_FACT_FIELDS",
    "Q3_GRAIN_FIELDS",
    "Q3_QUESTION",
    "RESPONSE_KEYS",
    "build_q3_projection",
    "explain_q3",
    "provider_payload",
    "validate_provider_response",
]

__version__ = "0.1.0"
