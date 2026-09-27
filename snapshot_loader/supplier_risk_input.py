"""Supplier Risk runtime input seam (``A′``, Human Decision, Issue #162).

`BR-SUPPLIER-RISK-001` (``poc-design-v0.2.md`` §2.7) needs two runtime surfaces that did not exist:
a deterministic **Supplier-Material relationship eligibility** resolution and a registered
**composition** between the plant-scoped Procurement Recommendation Context and the supplier-material
Risk Evidence Card.  This module is that seam and nothing else:

* it resolves the registered conceptual eligibility outcome -- ``eligible`` ／ ``ineligible`` ／
  ``unresolved`` -- from the accepted ``Supplier-Material Relationship`` evidence: the source-specific
  ``sourcing_status`` value, its exact Stable Source Evidence Locator and the **exact registered
  ``mapping_basis``** of that observation, through the approved closed **SIMULATED** mapping registry
  (``§2.7.25`` ／ ``§4.4.62`` ／ ``§4.5.11``);
* it composes, for every Procurement Recommendation Context the registered upstream result states, one
  **evaluation context** per eligible relationship of the same material -- keeping the Supplier Risk
  business grain ``supplier_id`` + ``material_code`` and carrying ``plant_id`` as **evaluation context
  only** (``§2.7.2`` ／ ``§2.7.25`` C);
* it preserves the real upstream surfaces a future rule needs (relationship evidence, eligibility
  resolution, Supplier Performance evidence, ``standard_lead_time_days``, ``DeliveryPerformance``,
  ``QualityPerformance``, ``PerformancePeriod``, ``PerformanceUpdatedAt``, ``RecommendationNeedDate``
  and the Analysis Run's ``AnalysisDate``) as **read-only** objects and references.

It deliberately computes **no** risk: no ``DaysUntilNeed``, no ``LeadTimeRisk`` ／ ``DeliveryRisk`` ／
``QualityRisk`` ／ ``OverallSupplierRisk``, no threshold comparison, no ranking ／ selection ／
recommendation and no change to any procurement quantity.  The ``A′`` seam only decides *which*
supplier-material relationships may enter the evaluation and *which* evaluation context each of them
belongs to.

Boundaries preserved by construction:

* ``eligible`` ／ ``ineligible`` ／ ``unresolved`` are a **runtime conceptual mapping outcome**, never a
  source enum, canonical ／ persisted field, business status, ranking or selection result; no real ERP ／
  SRM vocabulary is defined, assumed or interpreted (``§4.1.4`` I ／ ``§2.7.24`` ／ ``§4.4.62``);
* the registry maps the **approved ``mapping_basis`` literal** to the outcome -- never the raw source
  ``sourcing_status`` value -- so the source-specific interpretation stays with the approved mapping
  evidence and is never re-invented here;
* the caller can never inject an outcome: the outcome comes only from the accepted package's own
  evidence plus the exact registered basis, and ``relationship exists`` never implies ``eligible``;
* ``RecommendationNeedDate`` keeps its single registered authority (``BR-SHORTAGE-001``
  ``FirstShortageDate`` → the registered Procurement Recommendation ／ handoff): it is never
  recomputed, never caller-overridden, never re-read from raw evidence and never borrowed across
  Plants (``§4.4.65`` ／ ``§4.3.31`` G I-4).  A recommendation entry's claimed date is only accepted
  when the entry's **own upstream shortage reference** names exactly that ``plant_id`` +
  ``material_code`` + ``RecommendationNeedDate``; a reference that is absent or points elsewhere is
  never repaired -- the context keeps the reliable supplier-side evidence with no need date and fails
  closed with the existing ``PROVENANCE`` ／ ``PROVENANCE_UNRESOLVED`` ／ ``PROVENANCE_MISMATCH``
  semantics (``§4.4.69`` ／ ``§4.4.93``);
* an unavailable capability (a required supplier-side evidence role was **not provided**) stays the
  registered ``EVIDENCE_AVAILABILITY`` ／ ``EVIDENCE_ROLE_NOT_PROVIDED`` condition and is never faked
  into a business ``DATA_INCOMPLETE`` Risk Card (``§4.4.6`` Capability C ／ ``§4.4.80`` #2 ／
  ``§4.4.81`` #2 ／ ``§4.4.84``).

``ADR-001`` is unchanged: every value this seam carries is either an accepted canonical value copied
verbatim or an existing runtime reference; no canonical entity ／ field ／ grain ／ business enum and no
Validation Category ／ Reason is created.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from .canonical_objects import (
    AcceptedPackage,
    AnalysisRunContext,
    CanonicalConstructionReport,
    CanonicalObject,
    EvidenceReference,
    JsonObject,
    StrictJsonError,
    parse_strict_json,
    read_provenance_associations,
)
from .constants import (
    CATEGORY_PROVENANCE,
    CATEGORY_SEMANTIC_RESOLUTION,
    LAYER_2,
    REASON_PROVENANCE_MISMATCH,
    REASON_PROVENANCE_UNRESOLVED,
    REASON_SEMANTIC_UNRESOLVED,
)
from .issues import Issue
from .procurement_recommendation import (
    PROCUREMENT_RECOMMENDATION_RULE_ID,
    ProcurementRecommendation,
    ProcurementRecommendationResult,
)
from .result_binding import require_same_accepted_package, require_same_analysis_run
from .shortage_calculation import SHORTAGE_RULE_ID

# --- vocabulary --------------------------------------------------------------------

#: The runtime stage identity of this seam.  It is a runtime trace label -- **not** a business rule id,
#: canonical field, enum or status.
SUPPLIER_RISK_INPUT_STAGE: str = "SUPPLIER_RISK_INPUT"

#: The registered canonical targets ／ recognized role literals this seam consumes (``§4.2.18`` role 10
#: and role 11).  They are the existing names ``objects_for`` ／ ``present_roles`` already use; this
#: module introduces no new target, role or property name.
SUPPLIER_RELATIONSHIP_TARGET: str = "Supplier-Material Relationship"
SUPPLIER_PERFORMANCE_TARGET: str = "Supplier Performance"

#: The registered observation the relationship's eligibility evidence is registered under
#: (``§4.2.8``: ``sourcing_status`` = Supplier-Material relationship eligibility context).
SUPPLIER_RISK_OBSERVATION: str = "sourcing_status"

#: The registered **conceptual mapping outcomes** of a Supplier-Material relationship (``§4.1.4`` I ／
#: ``§4.5.11``).  They are runtime mapping conditions: not a source enum, not a canonical ／ persisted
#: field, not a business status, not a Risk Level and not a ranking ／ selection result.
ELIGIBILITY_ELIGIBLE: str = "eligible"
ELIGIBILITY_INELIGIBLE: str = "ineligible"
ELIGIBILITY_UNRESOLVED: str = "unresolved"

#: The complete outcome vocabulary of the registry (closed).
SUPPLIER_ELIGIBILITY_OUTCOMES: frozenset[str] = frozenset(
    {ELIGIBILITY_ELIGIBLE, ELIGIBILITY_INELIGIBLE}
)

#: Runtime trace labels for **why** a relationship eligibility is unresolved.  They are trace only --
#: not a new Validation taxonomy, not a canonical vocabulary and not a wire property; the registered
#: ``Issue`` category ／ reason stays the inherited ``SEMANTIC_RESOLUTION`` ／ ``SEMANTIC_UNRESOLVED``
#: (``§4.4.62`` path C).
ROOT_RELATIONSHIP_IDENTITY_UNRESOLVED: str = "SUPPLIER_RELATIONSHIP_IDENTITY_UNRESOLVED"
ROOT_SOURCING_STATUS_UNRESOLVED: str = "SOURCING_STATUS_UNRESOLVED"
ROOT_NO_MAPPING_EVIDENCE: str = "SOURCING_STATUS_NO_MAPPING_EVIDENCE"
ROOT_MAPPING_AMBIGUOUS: str = "SOURCING_STATUS_MAPPING_AMBIGUOUS"
ROOT_CONFLICTING_RELATIONSHIP_EVIDENCE: str = "SUPPLIER_RELATIONSHIP_EVIDENCE_CONFLICT"
ROOT_RELATIONSHIP_ABSENT: str = "SUPPLIER_RELATIONSHIP_ABSENT"
ROOT_NEED_DATE_UNRESOLVED: str = "RECOMMENDATION_NEED_DATE_UNRESOLVED"
#: The claimed ``RecommendationNeedDate`` of an entry whose own upstream shortage reference does not
#: support it: the required linkage is either absent or points at another context.
ROOT_NEED_DATE_LINKAGE_ABSENT: str = "RECOMMENDATION_NEED_DATE_LINKAGE_ABSENT"
ROOT_NEED_DATE_LINKAGE_MISMATCH: str = "RECOMMENDATION_NEED_DATE_LINKAGE_MISMATCH"

#: The **existing** registered capability-readiness pair for a required logical evidence role that the
#: accepted package did not provide (``§4.4.80`` #2 ／ ``§4.4.81`` #2), used verbatim exactly as the
#: other layers use their registered pairs.
_CATEGORY_EVIDENCE_AVAILABILITY: str = "EVIDENCE_AVAILABILITY"
_REASON_EVIDENCE_ROLE_NOT_PROVIDED: str = "EVIDENCE_ROLE_NOT_PROVIDED"


# --- approved SIMULATED eligibility mapping registry -------------------------------


@dataclass(frozen=True, slots=True)
class SupplierEligibilityBasis:
    """One registered eligibility ``mapping_basis`` literal → exact conceptual outcome.

    The literal is the exact ``mapping_basis`` a ``Supplier-Material Relationship`` record must itself
    register on its ``sourcing_status`` association: it is the **approved mapping evidence** that has
    already interpreted the source-specific status, so this registry never interprets the raw source
    value itself and never defines a source vocabulary (``§4.5.11`` ／ ``§2.7.25`` D).
    """

    basis: str
    outcome: str
    design_reference: str


#: The approved **SIMULATED** eligibility mapping registry: ``exact mapping_basis literal -> exact
#: outcome``.  Like the existing G5-A ／ inventory-scope ／ loss-rate ／ MOQ-policy registries these are
#: runtime literals of this POC's accepted-package handoff -- explicitly SIMULATED, **not** real ERP ／
#: SRM vocabulary, not a canonical field, not a business enum and not a claim about any real source
#: value (``§2.7.24`` ／ ``§4.4.33``: `SOURCE-SPECIFIC` must never become a runtime enum value).
SUPPLIER_ELIGIBILITY_REGISTRY: tuple[SupplierEligibilityBasis, ...] = (
    SupplierEligibilityBasis(
        basis="SIMULATED-SOURCING-ELIGIBLE",
        outcome=ELIGIBILITY_ELIGIBLE,
        design_reference="§2.7.25 B ／ §4.4.62 A / §4.5.11",
    ),
    SupplierEligibilityBasis(
        basis="SIMULATED-SOURCING-INELIGIBLE",
        outcome=ELIGIBILITY_INELIGIBLE,
        design_reference="§2.7.25 B ／ §4.4.62 B / §4.5.11",
    ),
)

#: ``exact mapping_basis literal -> registered basis``.  Closed and exact-match only: no trim, no case
#: folding, no normalisation, no heuristic and no precedence.
SUPPLIER_ELIGIBILITY_BASIS_BY_LITERAL: Mapping[str, SupplierEligibilityBasis] = {
    entry.basis: entry for entry in SUPPLIER_ELIGIBILITY_REGISTRY
}


# --- result representation ---------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SupplierRelationshipEligibility:
    """The resolved eligibility of **one** ``supplier_id`` + ``material_code`` relationship.

    ``outcome`` is the registered conceptual mapping condition: ``eligible`` (the relationship may
    enter Supplier Risk evaluation), ``ineligible`` (valid but not applicable -- no Validation Issue,
    never ``DATA_INCOMPLETE``, excluded from the candidate set) or ``unresolved``
    (``SEMANTIC_RESOLUTION`` ／ ``SEMANTIC_UNRESOLVED``; the capability fails closed when it needs the
    relationship, and the outcome is never defaulted).

    ``sourcing_status`` ／ ``mapping_basis`` ／ ``relationship_reference`` ／ ``evidence_reference`` are
    the preserved provenance of the decision: the accepted source-specific value carried verbatim, the
    **exact approved** ``mapping_basis`` literal that interpreted it, the relationship evidence's G3-A
    technical record reference and its package-scoped :class:`EvidenceReference`.
    ``considered_references`` names every record that had to be taken into account, so an unresolved
    relationship cannot hide which evidence was seen.

    A reference is **only** present when the upstream item really exists (``master-data-mapping.md``
    決定 7 ／ 決定 11): a relationship with no evidence at all carries no relationship reference rather
    than a synthesised one.
    """

    supplier_id: Any
    material_code: Any
    outcome: str
    sourcing_status: Any = None
    mapping_basis: str | None = None
    relationship_reference: str | None = None
    evidence_reference: EvidenceReference | None = None
    considered_references: tuple[str, ...] = ()
    root_condition: str | None = None
    notes: tuple[str, ...] = ()
    rule_issues: tuple[Issue, ...] = ()

    @property
    def grain(self) -> tuple[Any, Any]:
        """The registered Supplier-Material grain -- never widened with ``plant_id`` (``§2.7.2``)."""

        return (self.supplier_id, self.material_code)

    @property
    def eligible(self) -> bool:
        return self.outcome == ELIGIBILITY_ELIGIBLE

    @property
    def ineligible(self) -> bool:
        return self.outcome == ELIGIBILITY_INELIGIBLE

    @property
    def unresolved(self) -> bool:
        return self.outcome == ELIGIBILITY_UNRESOLVED

    @property
    def issues(self) -> tuple[Issue, ...]:
        return _deduplicate_issues(self.rule_issues)

    def to_dict(self) -> dict[str, object]:
        return {
            "stage": SUPPLIER_RISK_INPUT_STAGE,
            "supplier_id": self.supplier_id,
            "material_code": self.material_code,
            "eligibility": self.outcome,
            "sourcing_status": self.sourcing_status,
            "mapping_basis": self.mapping_basis,
            "relationship_reference": self.relationship_reference,
            "evidence_reference": _evidence_payload(self.evidence_reference),
            "considered_references": list(self.considered_references),
            "root_condition": self.root_condition,
            "notes": list(self.notes),
            "rule_issues": [issue.to_dict() for issue in self.rule_issues],
        }


@dataclass(frozen=True, slots=True)
class SupplierRiskEvaluationContext:
    """One Supplier Risk evaluation context: an eligible relationship of a procurement context.

    The business grain stays ``supplier_id`` + ``material_code`` (``§2.7.2``); ``plant_id`` and
    ``recommendation_need_date`` are **evaluation context** only -- the same supplier + material
    demanded by two Plants forms two independent contexts, and no need date is ever borrowed across
    Plants (``§2.7.25`` C).

    ``recommendation_need_date`` is the registered ``RecommendationNeedDate`` of that exact
    ``plant_id`` + ``material_code`` family -- and only when the consumed recommendation entry's own
    upstream shortage reference supports exactly that Plant ／ material ／ date (``§4.4.65`` ／
    ``§4.4.66`` ／ ``§4.4.69`` ／ ``§4.4.93``).  When it is ``None`` the composition state stays
    **unresolved**, either because the need date itself is unresolved (``§2.7.25`` F3) or because the
    claimed date's required linkage is absent ／ inconsistent (``PROVENANCE`` ／
    ``PROVENANCE_UNRESOLVED`` ／ ``PROVENANCE_MISMATCH``): the context is still formed so the reliable
    supplier-side evidence is preserved, and a future ``LeadTimeRisk`` ／ ``OverallSupplierRisk`` must
    fail closed on it.  No date is guessed and no date is borrowed from another context.

    ``performance`` ／ ``unresolved_performance`` carry the real accepted ``Supplier Performance``
    canonical objects of this exact supplier + material -- resolved and supplied-but-ungrainable (for
    example a missing measurement period) -- so a future rule can read ``standard_lead_time_days``,
    ``DeliveryPerformance``, ``QualityPerformance``, ``PerformancePeriod`` and
    ``PerformanceUpdatedAt`` without re-reading any raw evidence and without this seam computing
    anything.  This seam states no risk value at all.
    """

    plant_id: Any
    material_code: Any
    supplier_id: Any
    recommendation_need_date: Any
    eligibility: SupplierRelationshipEligibility
    performance: tuple[CanonicalObject, ...] = ()
    unresolved_performance: tuple[CanonicalObject, ...] = ()
    root_condition: str | None = None
    notes: tuple[str, ...] = ()
    inherited_issues: tuple[Issue, ...] = ()
    rule_issues: tuple[Issue, ...] = ()

    @property
    def grain(self) -> tuple[Any, Any]:
        """The business grain of the Risk Evidence Card (``supplier_id`` + ``material_code``)."""

        return (self.supplier_id, self.material_code)

    @property
    def evaluation_context(self) -> tuple[Any, Any, Any]:
        """The evaluation context key ``plant_id`` + ``material_code`` + ``supplier_id``."""

        return (self.plant_id, self.material_code, self.supplier_id)

    @property
    def recommendation_need_date_resolved(self) -> bool:
        return self.recommendation_need_date is not None

    @property
    def issues(self) -> tuple[Issue, ...]:
        return _deduplicate_issues(self.inherited_issues + self.rule_issues)

    def to_dict(self) -> dict[str, object]:
        return {
            "stage": SUPPLIER_RISK_INPUT_STAGE,
            "plant_id": self.plant_id,
            "material_code": self.material_code,
            "supplier_id": self.supplier_id,
            "RecommendationNeedDate": self.recommendation_need_date,
            "recommendation_need_date_resolved": self.recommendation_need_date_resolved,
            "eligibility": self.eligibility.to_dict(),
            "performance": [_object_payload(item) for item in self.performance],
            "unresolved_performance": [
                _object_payload(item) for item in self.unresolved_performance
            ],
            "root_condition": self.root_condition,
            "notes": list(self.notes),
            "inherited_issues": [issue.to_dict() for issue in self.inherited_issues],
            "rule_issues": [issue.to_dict() for issue in self.rule_issues],
        }


@dataclass(frozen=True, slots=True)
class SupplierRiskInputResult:
    """Deterministic read-only result of the ``A′`` Supplier Risk runtime input seam.

    ``relationships`` states exactly one eligibility decision per ``supplier_id`` +
    ``material_code`` the accepted package's supplier-side evidence claims, ordered deterministically.
    ``evaluation_contexts`` states one composition entry per (Procurement Recommendation Context,
    eligible relationship) pair.  ``valid_absence_grains`` names the families whose reliable
    ``NORMAL`` ／ ``BUFFER_BREACH`` horizon means **no** Supplier Risk evaluation context exists at all
    (``§4.4.87``: valid absence, which is not ``DATA_INCOMPLETE``).  It is consumed **verbatim** from
    the upstream registered result, which already derives it from the consumed shortage result and
    validates its own family partition: this seam never widens it, never adds a family of its own and
    therefore never claims a stronger guarantee than the upstream result provides.

    ``capability_issues`` carries the registered ``EVIDENCE_AVAILABILITY`` ／
    ``EVIDENCE_ROLE_NOT_PROVIDED`` finding when a required supplier-side evidence role was not provided:
    the capability is then unavailable and the seam forms **no** evaluation context, because a missing
    evidence role is never reported as a business ``DATA_INCOMPLETE`` Risk Card (``§4.4.84``).

    ``analysis_run`` is the construction's existing :class:`AnalysisRunContext`, so a consumer can
    verify its own binding before consuming anything, and ``AnalysisDate`` -- the ``DaysUntilNeed``
    subtrahend of the future rule -- stays reachable without any re-read.
    """

    analysis_run: AnalysisRunContext
    relationships: tuple[SupplierRelationshipEligibility, ...] = ()
    evaluation_contexts: tuple[SupplierRiskEvaluationContext, ...] = ()
    valid_absence_grains: tuple[tuple[Any, Any], ...] = ()
    capability_issues: tuple[Issue, ...] = ()
    inherited_issues: tuple[Issue, ...] = ()
    rule_issues: tuple[Issue, ...] = ()
    notes: tuple[str, ...] = ()

    @property
    def issues(self) -> tuple[Issue, ...]:
        return _deduplicate_issues(
            self.capability_issues + self.inherited_issues + self.rule_issues
        )

    @property
    def capability_available(self) -> bool:
        """Whether every required supplier-side evidence role was provided (``§4.4.6`` C)."""

        return not self.capability_issues

    @property
    def analysis_date(self) -> Any:
        return self.analysis_run.analysis_date

    @property
    def eligible_relationships(self) -> tuple[SupplierRelationshipEligibility, ...]:
        return tuple(item for item in self.relationships if item.eligible)

    @property
    def unresolved_relationships(self) -> tuple[SupplierRelationshipEligibility, ...]:
        return tuple(item for item in self.relationships if item.unresolved)

    @property
    def ineligible_relationships(self) -> tuple[SupplierRelationshipEligibility, ...]:
        return tuple(item for item in self.relationships if item.ineligible)

    def eligibility_for(
        self, supplier_id: Any, material_code: Any
    ) -> SupplierRelationshipEligibility | None:
        """The eligibility decision of one exact ``supplier_id`` + ``material_code``, or ``None``.

        ``None`` means the accepted supplier-side evidence claims no such relationship **and**
        ``Supplier-Material Relationship`` evidence was provided for the analysis: the pair is then not
        a candidate at all.  It never means "eligible".
        """

        for item in self.relationships:
            if item.supplier_id == supplier_id and item.material_code == material_code:
                return item
        return None

    def contexts_for(
        self, supplier_id: Any, material_code: Any
    ) -> tuple[SupplierRiskEvaluationContext, ...]:
        """Every evaluation context of one exact supplier + material, in deterministic order."""

        return tuple(
            item
            for item in self.evaluation_contexts
            if item.supplier_id == supplier_id and item.material_code == material_code
        )

    def context_for(
        self, plant_id: Any, supplier_id: Any, material_code: Any
    ) -> SupplierRiskEvaluationContext | None:
        """The evaluation context of one exact plant + supplier + material, or ``None``."""

        for item in self.evaluation_contexts:
            if (
                item.plant_id == plant_id
                and item.supplier_id == supplier_id
                and item.material_code == material_code
            ):
                return item
        return None

    def is_valid_absence(self, plant_id: Any, material_code: Any) -> bool:
        """Whether the family is a reliable ``NORMAL`` ／ ``BUFFER_BREACH`` valid absence."""

        return (plant_id, material_code) in self.valid_absence_grains

    def to_dict(self) -> dict[str, object]:
        return {
            "stage": SUPPLIER_RISK_INPUT_STAGE,
            "analysis_run": {
                "analysis_run_id": self.analysis_run.analysis_run_id,
                "AnalysisDate": self.analysis_run.analysis_date,
                "snapshot_package_identity": (
                    self.analysis_run.snapshot_package_identity
                ),
                "accepted_content_view_digest": (
                    self.analysis_run.accepted_content_view_digest
                ),
            },
            "capability_available": self.capability_available,
            "relationships": [item.to_dict() for item in self.relationships],
            "evaluation_contexts": [
                item.to_dict() for item in self.evaluation_contexts
            ],
            "valid_absence_grains": [
                {"plant_id": plant_id, "material_code": material_code}
                for plant_id, material_code in self.valid_absence_grains
            ],
            "capability_issues": [issue.to_dict() for issue in self.capability_issues],
            "rule_issues": [issue.to_dict() for issue in self.rule_issues],
            "notes": list(self.notes),
        }


# --- entry point -------------------------------------------------------------------


def compute_supplier_risk_input(
    construction: CanonicalConstructionReport,
    recommendations: ProcurementRecommendationResult,
    *,
    accepted: AcceptedPackage,
) -> SupplierRiskInputResult:
    """Resolve the Supplier Risk runtime inputs of one analysis run (``A′``).

    ``construction`` supplies the Phase A supplier-side canonical objects (roles 10 ／ 11), the
    recognized-role surface and the Analysis Run binding; ``recommendations`` supplies the registered
    Procurement Recommendation Contexts and their ``RecommendationNeedDate``; ``accepted`` is the
    evidence authority of the ``sourcing_status`` mapping associations.  All three must belong to the
    same Analysis Run and the same accepted package ／ accepted content view, verified **before** any
    evidence is consumed (``F3-RB1`` ／ ``§4.3.31`` E): a foreign, stale or unbound input rejects the
    invocation instead of being combined.

    Only the accepted content view's supplier-side datasets are read (never the filesystem and never a
    raw source), and no risk value is computed anywhere.
    """

    require_same_analysis_run(
        construction.analysis_run,
        (PROCUREMENT_RECOMMENDATION_RULE_ID, recommendations.analysis_run),
    )
    require_same_accepted_package(
        construction.analysis_run,
        package_id=accepted.package_id,
        accepted_content_view_digest=accepted.content_view_digest,
    )

    records = _supplier_records(accepted)
    relationship_evidence = _relationship_evidence(construction)
    performance_evidence = _performance_evidence(construction)
    relationship_role_present = SUPPLIER_RELATIONSHIP_TARGET in construction.present_roles

    capability_issues = _capability_issues(construction)

    evidence = tuple(
        _resolve_evidence(obj, records.get(obj.provenance.record_path))
        for obj in relationship_evidence
    )
    relationships = _relationships(
        evidence,
        performance_evidence=performance_evidence,
        relationship_role_present=relationship_role_present,
    )

    evaluation_contexts: list[SupplierRiskEvaluationContext] = []
    if not capability_issues:
        evaluation_contexts.extend(
            _composition(relationships, performance_evidence, recommendations)
        )

    ordered_contexts = sorted(evaluation_contexts, key=_context_key)
    return SupplierRiskInputResult(
        analysis_run=construction.analysis_run,
        relationships=relationships,
        evaluation_contexts=tuple(ordered_contexts),
        valid_absence_grains=tuple(
            sorted(recommendations.valid_absence_grains, key=_family_key)
        ),
        capability_issues=capability_issues,
        inherited_issues=_deduplicate_issues(
            tuple(issue for item in ordered_contexts for issue in item.inherited_issues)
        ),
        rule_issues=_deduplicate_issues(
            tuple(issue for item in relationships for issue in item.rule_issues)
            + tuple(issue for item in ordered_contexts for issue in item.rule_issues)
        ),
        notes=(
            "the seam resolves Supplier-Material eligibility and the supplier-material evaluation "
            "composition only; it computes no DaysUntilNeed and no risk level, applies no threshold "
            "and performs no ranking ／ selection ／ recommendation (§2.7.25 / A′ scope)",
        ),
    )


# --- eligibility resolution --------------------------------------------------------


def _resolve_evidence(
    obj: CanonicalObject, record: JsonObject | None
) -> SupplierRelationshipEligibility:
    """Resolve one accepted relationship record's eligibility from approved mapping evidence.

    The decision uses the accepted record's own ``sourcing_status`` association: the source-specific
    value must be present as an exact JSON string and the association must register **exactly one**
    approved ``mapping_basis`` literal.  Everything else stays ``unresolved`` -- never defaulted to
    ``eligible`` or ``ineligible`` and never inferred from the relationship's mere existence.
    """

    supplier_id = obj.value_of("supplier_id", None)
    material_code = obj.value_of("material_code", None)
    reference = obj.record_reference
    provenance = obj.provenance
    sourcing_status = obj.value_of(SUPPLIER_RISK_OBSERVATION, None)

    if obj.grain is None:
        return _unresolved_relationship(
            supplier_id=supplier_id,
            material_code=material_code,
            root=ROOT_RELATIONSHIP_IDENTITY_UNRESOLVED,
            considered=(reference,),
            relationship_reference=reference,
            detail=(
                "the accepted Supplier-Material Relationship record does not state a reliably "
                "established supplier_id + material_code grain, so the relationship cannot be scoped "
                "and its eligibility is unresolved; it is never accepted as a candidate and never "
                "silently dropped (§2.7.24 / §4.4.61 / §4.4.26)"
            ),
        )
    if not isinstance(sourcing_status, str) or sourcing_status == "":
        return _unresolved_relationship(
            supplier_id=supplier_id,
            material_code=material_code,
            root=ROOT_SOURCING_STATUS_UNRESOLVED,
            considered=(reference,),
            relationship_reference=reference,
            provenance=provenance,
            detail=(
                "the accepted Supplier-Material Relationship record states no usable "
                "sourcing_status evidence (absent, JSON null, empty or not an exact JSON string), so "
                "the registered eligibility mapping evidence cannot be applied and the outcome stays "
                "unresolved -- never defaulted (§4.4.33 / §4.4.62 C)"
            ),
        )

    associations = () if record is None else read_provenance_associations(record)
    registrations = tuple(
        item
        for item in associations
        if item.observation == SUPPLIER_RISK_OBSERVATION
    )
    approved = tuple(
        item
        for item in registrations
        if (item.mapping_basis or "") in SUPPLIER_ELIGIBILITY_BASIS_BY_LITERAL
    )
    if not registrations:
        return _unresolved_relationship(
            supplier_id=supplier_id,
            material_code=material_code,
            root=ROOT_NO_MAPPING_EVIDENCE,
            considered=(reference,),
            relationship_reference=reference,
            provenance=provenance,
            sourcing_status=sourcing_status,
            detail=(
                "the accepted Supplier-Material Relationship record registers no "
                "sourcing_status eligibility mapping evidence at all, so whether this relationship "
                "may enter Supplier Risk evaluation cannot be established and the outcome stays "
                "unresolved (§4.4.33 / §4.4.62 C / §4.5.11)"
            ),
        )
    if len(registrations) != 1 or len(approved) != 1:
        return _unresolved_relationship(
            supplier_id=supplier_id,
            material_code=material_code,
            root=ROOT_MAPPING_AMBIGUOUS,
            considered=(reference,),
            relationship_reference=reference,
            provenance=provenance,
            sourcing_status=sourcing_status,
            detail=(
                "the accepted Supplier-Material Relationship record does not register exactly one "
                "approved eligibility mapping basis (several registrations, or a basis literal that is "
                "not approved), so the eligibility outcome cannot be reliably determined; it is never "
                "resolved by first ／ last wins or any other precedence (§4.4.62 C / §4.5.11)"
            ),
        )

    entry = SUPPLIER_ELIGIBILITY_BASIS_BY_LITERAL[approved[0].mapping_basis or ""]
    return SupplierRelationshipEligibility(
        supplier_id=supplier_id,
        material_code=material_code,
        outcome=entry.outcome,
        sourcing_status=sourcing_status,
        mapping_basis=entry.basis,
        relationship_reference=reference,
        evidence_reference=provenance,
        considered_references=(reference,),
        notes=(
            "the eligibility outcome is the registered conceptual mapping condition of the approved "
            "mapping evidence: eligible allows Supplier Risk evaluation, ineligible is a valid "
            "exclusion with no issue and no DATA_INCOMPLETE (never a candidate), and neither is a "
            "source enum, business status, ranking or selection result (§2.7.25 B / §4.4.62)",
        ),
    )


def _relationships(
    evidence: Sequence[SupplierRelationshipEligibility],
    *,
    performance_evidence: Sequence[CanonicalObject],
    relationship_role_present: bool,
) -> tuple[SupplierRelationshipEligibility, ...]:
    """One eligibility decision per claimed ``supplier_id`` + ``material_code`` pair.

    Conflicting evidence for one pair (several accepted records claiming the same relationship, or a
    resolved record next to an unscopeable one) is never resolved by picking one: the pair stays
    ``unresolved``.  A pair that only ``Supplier Performance`` evidence claims, while
    ``Supplier-Material Relationship`` evidence **was** provided, is unresolved as well -- performance
    evidence never implies a relationship (``§4.4.61``), and no relationship reference is fabricated
    for it.
    """

    pairs: list[tuple[Any, Any]] = []
    for pair in [
        (item.supplier_id, item.material_code) for item in evidence
    ] + [
        (obj.value_of("supplier_id", None), obj.value_of("material_code", None))
        for obj in performance_evidence
        if obj.value_of("supplier_id", None) is not None
        and obj.value_of("material_code", None) is not None
    ]:
        if not any(pair == existing for existing in pairs):
            pairs.append(pair)

    decisions: list[SupplierRelationshipEligibility] = []
    for pair in pairs:
        candidates = [
            item
            for item in evidence
            if (item.supplier_id, item.material_code) == pair
        ]
        if len(candidates) == 1:
            decisions.append(candidates[0])
            continue
        if candidates:
            decisions.append(
                _unresolved_relationship(
                    supplier_id=pair[0],
                    material_code=pair[1],
                    root=ROOT_CONFLICTING_RELATIONSHIP_EVIDENCE,
                    considered=tuple(
                        item.relationship_reference or "" for item in candidates
                    ),
                    detail=(
                        f"{len(candidates)} accepted Supplier-Material Relationship records claim this "
                        "exact supplier_id + material_code pair, so the eligibility evidence "
                        "conflicts; the pair stays unresolved and no record is silently preferred "
                        "(§4.4.61 / §4.4.62 C)"
                    ),
                )
            )
            continue
        if not relationship_role_present:
            # No ``Supplier-Material Relationship`` evidence was provided at all: that absence is a
            # capability-readiness condition, so no business finding is fabricated for this pair.
            continue
        # The pair is only claimed by Supplier Performance evidence: performance never implies a
        # relationship, and no relationship reference exists to preserve.
        decisions.append(
            _unresolved_relationship(
                supplier_id=pair[0],
                material_code=pair[1],
                root=ROOT_RELATIONSHIP_ABSENT,
                considered=tuple(
                    obj.record_reference
                    for obj in performance_evidence
                    if (obj.value_of("supplier_id", None), obj.value_of("material_code", None))
                    == pair
                ),
                detail=(
                    "Supplier Performance evidence claims this supplier_id + material_code pair, "
                    "but no reliably identified Supplier-Material Relationship evidence states it, "
                    "so the relationship is unresolved: the supplier is never treated as a "
                    "candidate for this material and no relationship reference is fabricated "
                    "(§2.7.24 / §4.4.61 / §4.4.62 C)"
                ),
            )
        )

    decisions.sort(key=_relationship_key)
    return tuple(decisions)


def _unresolved_relationship(
    *,
    supplier_id: Any,
    material_code: Any,
    root: str,
    considered: tuple[str, ...],
    detail: str,
    provenance: EvidenceReference | None = None,
    sourcing_status: Any = None,
    relationship_reference: str | None = None,
) -> SupplierRelationshipEligibility:
    """One ``unresolved`` eligibility decision with the registered taxonomy pair.

    ``relationship_reference`` is passed in explicitly and is **never** derived from
    ``considered_references``: a pair whose relationship evidence does not exist (only ``Supplier
    Performance`` evidence claims it) must carry no relationship reference at all rather than a
    reference to a record of another kind.
    """

    return SupplierRelationshipEligibility(
        supplier_id=supplier_id,
        material_code=material_code,
        outcome=ELIGIBILITY_UNRESOLVED,
        sourcing_status=sourcing_status,
        relationship_reference=relationship_reference,
        evidence_reference=provenance,
        considered_references=tuple(item for item in considered if item),
        root_condition=root,
        notes=(
            "the relationship eligibility cannot be reliably determined, so the relationship may "
            "neither enter Supplier Risk evaluation nor be excluded by default; a capability that "
            "needs it fails closed (§2.7.25 B / §4.4.62 C)",
        ),
        rule_issues=(
            Issue(
                location=(
                    "supplier_risk_input["
                    f"{_sort_text(supplier_id)}/{_sort_text(material_code)}]"
                ),
                detail=detail,
                category=CATEGORY_SEMANTIC_RESOLUTION,
                reason=REASON_SEMANTIC_UNRESOLVED,
                layer=LAYER_2,
                affected_evidence=SUPPLIER_RELATIONSHIP_TARGET,
                blast_radius="the Supplier Risk candidate evaluation of this relationship only",
                design_reference=(
                    "§2.7.24 / §2.7.25 B / §4.1.4 I / §4.4.61 / §4.4.62 / §4.5.10 / §4.5.11"
                ),
                consequence_context=(
                    "the relationship is neither eligible nor ineligible; the outcome is never "
                    "defaulted to either and a capability that needs it must fail closed rather than "
                    "invent an eligibility"
                ),
            ),
        ),
    )


# --- composition -------------------------------------------------------------------


def _composition(
    relationships: Sequence[SupplierRelationshipEligibility],
    performance_evidence: Sequence[CanonicalObject],
    recommendations: ProcurementRecommendationResult,
) -> list[SupplierRiskEvaluationContext]:
    """One evaluation context per (Procurement Recommendation Context, eligible relationship).

    The registered context behaviour (``§2.7.25`` F) is applied exactly: a reliable
    ``RecommendationNeedDate`` forms the context; a `DATA_INCOMPLETE` procurement **quantity** does not
    prevent it (the failure stays with the procurement result); an unresolved
    ``RecommendationNeedDate`` keeps the context with an unresolved composition state; and a reliable
    ``NORMAL`` ／ ``BUFFER_BREACH`` valid absence forms no context at all.

    A claimed reliable date is only accepted when the entry's **own upstream shortage reference**
    supports exactly that ``plant_id`` + ``material_code`` + ``RecommendationNeedDate``
    (``§4.4.65`` ／ ``§4.4.66`` ／ ``§4.4.69`` ／ ``§4.4.93``): an entry whose reference is absent or
    points at another context never becomes a normal evaluation context and never has its claimed date
    trusted -- the context keeps the reliable supplier-side evidence with **no** need date, so a future
    ``LeadTimeRisk`` ／ ``OverallSupplierRisk`` must fail closed.
    """

    eligible = [item for item in relationships if item.eligible]
    contexts: list[SupplierRiskEvaluationContext] = []
    for entry in recommendations.recommendations:
        decision = _need_date_decision(entry)
        for relationship in eligible:
            if relationship.material_code != entry.material_code:
                continue
            performance, unresolved_performance = _performance_for(
                performance_evidence,
                supplier_id=relationship.supplier_id,
                material_code=entry.material_code,
            )
            contexts.append(
                SupplierRiskEvaluationContext(
                    plant_id=entry.plant_id,
                    material_code=entry.material_code,
                    supplier_id=relationship.supplier_id,
                    recommendation_need_date=decision.need_date,
                    eligibility=relationship,
                    performance=performance,
                    unresolved_performance=unresolved_performance,
                    root_condition=decision.root_condition,
                    notes=(decision.note,),
                    inherited_issues=decision.inherited_issues,
                    rule_issues=decision.rule_issues,
                )
            )
    return contexts


@dataclass(frozen=True, slots=True)
class _NeedDateDecision:
    """What one recommendation entry's ``RecommendationNeedDate`` may contribute to a context."""

    need_date: Any
    root_condition: str | None
    note: str
    inherited_issues: tuple[Issue, ...] = ()
    rule_issues: tuple[Issue, ...] = ()


def _need_date_decision(entry: ProcurementRecommendation) -> _NeedDateDecision:
    """Validate one entry's date claim against its own upstream shortage reference.

    Only the reference the upstream result **actually carries** is consumed (``§2.7.25`` D): it is
    never reconstructed or repaired.  The two registered linkage failure modes are mapped onto the
    existing ``PROVENANCE`` pair exactly as the Analysis-Run binding already maps them -- an **absent**
    required linkage is ``PROVENANCE_UNRESOLVED``, a linkage that **is** established but points at
    another Plant ／ material ／ date (or another rule) is ``PROVENANCE_MISMATCH`` (``§4.4.80`` #8 ／
    ``§4.4.81`` #11 ／ #12 ／ ``§4.4.93``, which explicitly forbids writing such a problem as
    ``CONSISTENCY_CONFLICT``).  No new Category ／ Reason is introduced.
    """

    if entry.recommendation_need_date is None:
        # A genuinely unresolved date stays unresolved: it is never upgraded into a reliable date
        # because another field or reference happens to exist (§2.7.25 F3).
        return _NeedDateDecision(
            need_date=None,
            root_condition=ROOT_NEED_DATE_UNRESOLVED,
            note=(
                "RecommendationNeedDate is unresolved for this family, so the composition state stays "
                "unresolved: the context keeps the reliable supplier-side evidence, and a future "
                "LeadTimeRisk ／ OverallSupplierRisk must fail closed on it -- no date is guessed and "
                "no second date authority exists (§2.7.25 F3 / §2.7.16)"
            ),
            inherited_issues=entry.issues,
        )

    expected = (entry.plant_id, entry.material_code, entry.recommendation_need_date)
    reference = entry.shortage_reference
    if reference is None or reference.rule != SHORTAGE_RULE_ID or tuple(reference.grain) != expected:
        absent = reference is None
        return _NeedDateDecision(
            need_date=None,
            root_condition=(
                ROOT_NEED_DATE_LINKAGE_ABSENT if absent else ROOT_NEED_DATE_LINKAGE_MISMATCH
            ),
            note=(
                "the recommendation entry's own upstream shortage reference "
                + ("is absent" if absent else f"does not support this context ({reference!r})")
                + ", so its claimed RecommendationNeedDate is never trusted: the context keeps the "
                "reliable supplier-side evidence with no need date and fails closed "
                "(§4.4.65 / §4.4.66 / §4.4.69 / §4.4.93)"
            ),
            rule_issues=(
                Issue(
                    location=(
                        "supplier_risk_input.need_date_linkage["
                        f"{_sort_text(entry.plant_id)}/{_sort_text(entry.material_code)}/"
                        f"{_sort_text(entry.recommendation_need_date)}]"
                    ),
                    detail=(
                        "the consumed Procurement Recommendation entry claims the context "
                        f"{expected!r}, but the shortage reference it actually carries "
                        + ("is absent" if absent else f"is {reference!r}")
                        + ": the required linkage between the recommendation and the "
                        "BR-SHORTAGE-001 result it derives from cannot be established for this exact "
                        "Plant ／ material ／ RecommendationNeedDate, so the claimed date is not "
                        "trusted, the Supplier Risk evaluation context stays without a need date and "
                        "no date is borrowed from another context (§4.4.65 / §4.4.66 / §4.4.69 / "
                        "§4.4.93)"
                    ),
                    category=CATEGORY_PROVENANCE,
                    reason=(
                        REASON_PROVENANCE_UNRESOLVED if absent else REASON_PROVENANCE_MISMATCH
                    ),
                    layer=LAYER_2,
                    affected_evidence=PROCUREMENT_RECOMMENDATION_RULE_ID,
                    blast_radius="the Supplier Risk evaluation context of this family only",
                    design_reference=(
                        "§4.4.65 / §4.4.66 / §4.4.69 / §4.4.80 #8 / §4.4.81 #11 ／ #12 / §4.4.93 / "
                        "§4.3.31 G I-4"
                    ),
                    consequence_context=(
                        "the claimed RecommendationNeedDate is neither trusted nor replaced, and the "
                        "context carries no need date; a downstream LeadTimeRisk ／ "
                        "OverallSupplierRisk must fail closed rather than use a date from another "
                        "Plant, material or date"
                    ),
                ),
            ),
        )

    return _NeedDateDecision(
        need_date=entry.recommendation_need_date,
        root_condition=None,
        note=(
            (
                "the Procurement Recommendation quantity of this family is DATA_INCOMPLETE while its "
                "RecommendationNeedDate stays reliable and is supported by the entry's own matching "
                "shortage reference, so the Supplier Risk evaluation context is still formed: an MOQ ／ "
                "policy-input failure never pollutes Supplier Risk (§2.7.25 F2)"
            )
            if entry.outcome is not None
            else (
                "the registered RecommendationNeedDate of this exact plant_id + material_code family "
                "forms the evaluation context of this eligible supplier-material relationship, and the "
                "entry's own shortage reference supports exactly that Plant ／ material ／ date; the "
                "business grain stays supplier_id + material_code and plant_id is evaluation context "
                "only (§2.7.25 C ／ D ／ F1)"
            )
        ),
    )


def _performance_for(
    performance_evidence: Sequence[CanonicalObject],
    *,
    supplier_id: Any,
    material_code: Any,
) -> tuple[tuple[CanonicalObject, ...], tuple[CanonicalObject, ...]]:
    """The accepted ``Supplier Performance`` objects of one exact supplier + material.

    ``§4.4.63``: performance evidence of another material is never shared, and ``§2.7.23``: the
    measurement period is never replaced by ``updated_at``.  Objects whose grain could not be resolved
    (for example a missing ``PerformancePeriod``) are returned separately so a future rule can fail the
    affected dimensions closed while the record stays visible.
    """

    resolved: list[CanonicalObject] = []
    unresolved: list[CanonicalObject] = []
    for obj in performance_evidence:
        if (
            obj.value_of("supplier_id", None) != supplier_id
            or obj.value_of("material_code", None) != material_code
        ):
            continue
        (resolved if obj.grain is not None else unresolved).append(obj)
    return (
        tuple(sorted(resolved, key=_record_key)),
        tuple(sorted(unresolved, key=_record_key)),
    )


# --- capability --------------------------------------------------------------------


def _capability_issues(
    construction: CanonicalConstructionReport,
) -> tuple[Issue, ...]:
    """The registered capability-readiness finding for a supplier-side evidence role not provided.

    A required logical evidence role the accepted package never provided is
    ``EVIDENCE_AVAILABILITY`` ／ ``EVIDENCE_ROLE_NOT_PROVIDED`` -- the capability cannot execute
    reliably -- and it must never be reported as a business ``DATA_INCOMPLETE`` Risk Card
    (``§4.4.6`` Capability C ／ ``§4.4.80`` #2 ／ ``§4.4.81`` #2 ／ ``§4.4.84``).  Supplier and material
    identity are carried by the relationship ／ performance records' own assignable properties, so the
    roles checked here are exactly the two datasets this seam consumes.
    """

    issues: list[Issue] = []
    for target in (SUPPLIER_RELATIONSHIP_TARGET, SUPPLIER_PERFORMANCE_TARGET):
        if target in construction.present_roles:
            continue
        issues.append(
            Issue(
                location=f"supplier_risk_input.capability[{target}]",
                detail=(
                    f"the accepted package states no {target} logical evidence role, so the Supplier "
                    "Risk capability cannot execute reliably for this analysis run; this is a "
                    "capability-readiness condition and never a business DATA_INCOMPLETE outcome"
                ),
                category=_CATEGORY_EVIDENCE_AVAILABILITY,
                reason=_REASON_EVIDENCE_ROLE_NOT_PROVIDED,
                layer=LAYER_2,
                affected_evidence=target,
                blast_radius="the Supplier Risk capability of this analysis run only",
                design_reference=(
                    "§2.7.25 G / §4.4.6 Capability C / §4.4.80 #2 / §4.4.81 #2 / §4.4.84"
                ),
                consequence_context=(
                    "the capability is unavailable; no Supplier Risk evaluation context is formed and "
                    "no OverallSupplierRisk value -- including DATA_INCOMPLETE -- is produced from a "
                    "missing evidence role"
                ),
            )
        )
    return tuple(issues)


# --- helpers -----------------------------------------------------------------------


def _relationship_evidence(
    construction: CanonicalConstructionReport,
) -> tuple[CanonicalObject, ...]:
    return tuple(construction.objects_for(SUPPLIER_RELATIONSHIP_TARGET)) + tuple(
        construction.unresolved_for(SUPPLIER_RELATIONSHIP_TARGET)
    )


def _performance_evidence(
    construction: CanonicalConstructionReport,
) -> tuple[CanonicalObject, ...]:
    return tuple(construction.objects_for(SUPPLIER_PERFORMANCE_TARGET)) + tuple(
        construction.unresolved_for(SUPPLIER_PERFORMANCE_TARGET)
    )


def _supplier_records(accepted: AcceptedPackage) -> dict[str, JsonObject]:
    """``<artifact>#<ordinal> -> accepted record`` for the two supplier-side datasets only.

    The index is built from the accepted content view's own bytes (never the filesystem and never a
    raw source), and only for the roles this seam consumes.
    """

    index: dict[str, JsonObject] = {}
    for role, artifact in accepted.datasets():
        if role not in (SUPPLIER_RELATIONSHIP_TARGET, SUPPLIER_PERFORMANCE_TARGET):
            continue
        raw = accepted.records_for(artifact)
        if raw is None:  # pragma: no cover - the accepted view always carries its bytes
            continue
        try:
            payload: Any = parse_strict_json(raw, source=artifact)
        except StrictJsonError:  # pragma: no cover - acceptance already parsed every artifact
            continue
        if not isinstance(payload, list):  # pragma: no cover - acceptance already enforced a list
            continue
        for ordinal, record in enumerate(payload):
            if not isinstance(record, JsonObject):  # pragma: no cover - acceptance enforced object
                continue
            index[f"{artifact}#{ordinal}"] = record
    return index


def _evidence_payload(value: EvidenceReference | None) -> dict[str, object] | None:
    if value is None:
        return None
    return {
        "snapshot_package_identity": value.snapshot_package_identity,
        "logical_dataset_role": value.logical_dataset_role,
        "artifact": value.artifact,
        "record_ordinal": value.record_ordinal,
        "logical_observation": value.logical_observation,
        "stable_source_evidence_locators": list(value.stable_source_evidence_locators),
        "mapping_resolution_basis": value.mapping_resolution_basis,
    }


def _object_payload(obj: CanonicalObject) -> dict[str, object]:
    """The read-only upstream surface of one accepted canonical object (no value is rewritten)."""

    return {
        "canonical_target": obj.canonical_target,
        "canonicalization_role": obj.canonicalization_role,
        "grain": (
            None
            if obj.grain is None
            else [{"name": prop.name, "value": prop.value} for prop in obj.grain]
        ),
        "properties": [
            {"name": prop.name, "value": prop.value} for prop in obj.properties
        ],
        "record_reference": obj.record_reference,
        "evidence_reference": _evidence_payload(obj.provenance),
    }


def _relationship_key(item: SupplierRelationshipEligibility) -> tuple[str, str]:
    return (_sort_text(item.supplier_id), _sort_text(item.material_code))


def _record_key(obj: CanonicalObject) -> str:
    """Deterministic object order (the accepted record path of the object)."""

    return obj.provenance.record_path


def _context_key(item: SupplierRiskEvaluationContext) -> tuple[str, str, str]:
    return (
        _sort_text(item.plant_id),
        _sort_text(item.material_code),
        _sort_text(item.supplier_id),
    )


def _family_key(family: tuple[Any, Any]) -> tuple[str, str]:
    return (_sort_text(family[0]), _sort_text(family[1]))


def _deduplicate_issues(issues: Iterable[Issue]) -> tuple[Issue, ...]:
    seen: dict[tuple[str, str, str], Issue] = {}
    for issue in issues:
        seen.setdefault((issue.location, issue.category, issue.reason), issue)
    return tuple(sorted(seen.values(), key=Issue.sort_key))


def _sort_text(value: Any) -> str:
    return "" if value is None else str(value)


__all__ = [
    "ELIGIBILITY_ELIGIBLE",
    "ELIGIBILITY_INELIGIBLE",
    "ELIGIBILITY_UNRESOLVED",
    "ROOT_CONFLICTING_RELATIONSHIP_EVIDENCE",
    "ROOT_MAPPING_AMBIGUOUS",
    "ROOT_NEED_DATE_LINKAGE_ABSENT",
    "ROOT_NEED_DATE_LINKAGE_MISMATCH",
    "ROOT_NEED_DATE_UNRESOLVED",
    "ROOT_NO_MAPPING_EVIDENCE",
    "ROOT_RELATIONSHIP_ABSENT",
    "ROOT_RELATIONSHIP_IDENTITY_UNRESOLVED",
    "ROOT_SOURCING_STATUS_UNRESOLVED",
    "SUPPLIER_ELIGIBILITY_BASIS_BY_LITERAL",
    "SUPPLIER_ELIGIBILITY_OUTCOMES",
    "SUPPLIER_ELIGIBILITY_REGISTRY",
    "SUPPLIER_PERFORMANCE_TARGET",
    "SUPPLIER_RELATIONSHIP_TARGET",
    "SUPPLIER_RISK_INPUT_STAGE",
    "SUPPLIER_RISK_OBSERVATION",
    "SupplierEligibilityBasis",
    "SupplierRelationshipEligibility",
    "SupplierRiskEvaluationContext",
    "SupplierRiskInputResult",
    "compute_supplier_risk_input",
]
