"""Phase A -- pre-rule canonicalization / canonical object construction (Issue #124).

This module implements **only** the Phase A scope that Issue #124 authorises:

```
Snapshot loader -> Layer 1 acceptance -> Layer 2 evidence validation
  -> Canonical data objects  (this module, Phase A = pre-rule canonicalization)
  -> Deterministic business rules / Procurement recommendation   NOT IN SCOPE
```

It is a *runtime representation* of the current canonical authority, not a new
authority source.  No canonical entity, canonical business field, wire property,
``"_meta"`` member, input carrier, validation category / reason / status / enum or
precedence rule is introduced here.

Canonical authority implemented:

* ``snapshot-import-contract.md`` §4.3.31 -- the 12 recognized canonicalization role
  literals (B), the unrecognized-role rule (C), the G3-A AcceptedPackage-scoped
  technical record reference for ``Inbound Supply`` (D), the injection boundary (E),
  the Phase A / Phase B ordering (F) and the injection contract (G).
* ``canonical-data-model.md`` §4.1.13 -- role -> target assignment, G3-A, G4-A BOM
  parent / requirement context binding, G5-A read-only effective demand context
  reference, ``POLICY_INPUT`` / ``CONTEXT`` handoff.  No new entity.
* ``data-dictionary.md`` §4.2.18 -- the canonicalization applicability matrix,
  explicitly separated from REQUIRED / MISSING / capability requirement.
* ``data-validation.md`` §4.4.102 -- outcome vocabulary (existing only) and the
  two-stage Stage A / Stage B conflict boundary.
* ``data-validation.md`` §4.4.87 / §4.4.88 / §4.4.89 -- valid absence, valid zero and
  valid-but-ineligible generate no issue.

Deliberately **not** implemented (outside the authorised tranche): Phase B
(``RecommendationNeedDate`` / ``ApplicableMOQ`` Procurement Recommendation Context
resolution), deterministic business rules §2.1 -- §2.7, shortage calculation,
procurement recommendation, Layer-3 capability readiness, omission-based ``MISSING``,
JSON-null missingness decisions, full cross-field / cross-dataset consistency,
cross-record aggregation / precedence, real ERP Adapter or source-field mapping, Web /
API, database / persistence, LLM / Agent, HITL, RBAC, persistent audit.

Boundaries preserved by construction:

* the accepted content view is the only evidence source -- business artifacts are never
  re-read from the filesystem, and the Layer-2 ``MG-2`` trusted-reuse result is not
  bypassed;
* an unrecognized Layer-1 ``role`` stays an exact opaque JSON string and becomes
  ``not_evaluable`` only; it never becomes a Validation Issue or a Layer-1 rejection;
* applicability is *assignability*, never requiredness: a property that is absent is
  never inferred, defaulted or guessed;
* canonical values are preserved exactly -- no trim, case fold, normalization,
  rounding, quantization, truncation or re-typing; ``0`` stays a valid value and JSON
  ``null`` is never read as ``0`` / ``false`` / ``""``;
* no DERIVED result (``data-dictionary.md`` §4.2.10) is represented as a source
  canonical object, and ``required_quantity`` never reappears;
* object construction failure is never rewritten as a Layer-1 package rejection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping
import re

from .constants import (
    CATEGORY_IDENTITY_RESOLUTION,
    DECIMAL_STRING_PATTERN,
    EVALUATION_FAILED,
    EVALUATION_NOT_EVALUABLE,
    EVALUATION_PASSED,
    LAYER_2,
    REASON_UNRESOLVED_IDENTITY,
    V02_CANONICAL_RECORD_PROPERTY_SET,
)
from .issues import Issue
from .layer2 import Layer2Report, validate_layer2
from .strict_json import JsonObject, StrictJsonError, parse_strict_json
from .trust import AcceptedPackage

_DECIMAL_STRING_RE = re.compile(rf"^{DECIMAL_STRING_PATTERN}$")

# --- §4.3.30 B.1 / §4.3.31 A: exact wire literals (never normalized) --------------

PROPERTY_META: str = "_meta"
ROLE_INBOUND_SUPPLY: str = "Inbound Supply"
ROLE_PRODUCTION_REQUIREMENT: str = "Production Requirement"
ROLE_BOM_COMPONENT: str = "BOM Component"
ROLE_SUBSTITUTE_ALLOCATION: str = "Substitute Allocation"
ROLE_SUBSTITUTE_RELATIONSHIP: str = "Substitute Relationship"
ROLE_CONFIGURED_SAFETY_STOCK: str = "Configured Safety Stock"

# --- Phase A construction check names --------------------------------------------
#
# Check state uses the existing vocabulary only (``§4.3.28`` B.2 ``FR-3``):
# ``passed`` / ``failed`` / ``not_evaluable``.  No new status, reason or enum exists.

CANONICALIZATION_ROLE_RECOGNITION = "canonicalization.recognized_role"
CANONICALIZATION_APPLICABILITY = "canonicalization.applicability"
CANONICALIZATION_TARGET_ASSIGNMENT = "canonicalization.target_assignment"
CANONICALIZATION_GRAIN_RESOLUTION = "canonicalization.grain_resolution"
CANONICALIZATION_INBOUND_IDENTITY = "canonicalization.inbound_record_identity"
CANONICALIZATION_BOM_PARENT = "canonicalization.bom_parent_context"
CANONICALIZATION_EFFECTIVE_DEMAND = "canonicalization.effective_demand_relation"
CANONICALIZATION_HANDOFF_EVIDENCE = "canonicalization.handoff_evidence"
CANONICALIZATION_ANALYSIS_RUN = "canonicalization.analysis_run_context"

#: ``MG-2`` binding gate: the Layer-2 result a construction relies on must belong to
#: the **same** accepted package identity and the **same** accepted content view
#: (``§4.3.28`` C.2 / C.3).  A foreign or stale report stops construction here.
LAYER2_REPORT_BINDING = "canonicalization.layer2_report_binding"


# --- §4.3.31 B: the 12 recognized canonicalization roles ---------------------------


@dataclass(frozen=True, slots=True)
class CanonicalizationRole:
    """One recognized first-tranche canonicalization role (``§4.3.31`` B).

    ``literal`` is the **exact** Layer-1 role string.  ``target`` names the canonical
    entity / relationship / context the role's evidence is assigned to.  ``phase`` is
    the registered phase for that assignment: ``A`` for every role this module
    constructs, ``B`` for the procurement-policy channel that Phase A must not open.
    """

    number: int
    literal: str
    target: str
    role_kind: str
    phase: str = "A"


CANONICALIZATION_ROLES: tuple[CanonicalizationRole, ...] = (
    CanonicalizationRole(
        1, "Plant / Material identity context", "Plant + Material", "identity context"
    ),
    CanonicalizationRole(
        2, "Production Requirement", "Production Requirement", "entity (source)"
    ),
    CanonicalizationRole(3, "BOM Component", "BOM Component", "relationship"),
    CanonicalizationRole(
        4, "Inventory Snapshot", "Inventory Snapshot", "entity (source)"
    ),
    CanonicalizationRole(
        5,
        "Configured Safety Stock",
        "Configured Safety Stock",
        "entity (policy input)",
    ),
    CanonicalizationRole(6, "Inbound Supply", "Inbound Supply", "entity (source)"),
    CanonicalizationRole(
        7, "Substitute Relationship", "Substitute Relationship", "relationship"
    ),
    CanonicalizationRole(
        8, "Substitute Allocation", "Substitute Allocation", "relationship"
    ),
    CanonicalizationRole(9, "Supplier identity", "Supplier", "identity"),
    CanonicalizationRole(
        10,
        "Supplier-Material Relationship",
        "Supplier-Material Relationship",
        "relationship",
    ),
    CanonicalizationRole(
        11, "Supplier Performance", "Supplier Performance", "entity (source)"
    ),
    CanonicalizationRole(
        12,
        "Procurement policy input",
        "ApplicableMOQ POLICY_INPUT channel",
        "policy-input channel",
        phase="B",
    ),
)

CANONICALIZATION_ROLE_BY_LITERAL: Mapping[str, CanonicalizationRole] = {
    role.literal: role for role in CANONICALIZATION_ROLES
}

#: Phase A targets in construction order (``§4.3.31`` F: role 1 -- 11).
PHASE_A_ROLE_LITERALS: tuple[str, ...] = tuple(
    role.literal for role in CANONICALIZATION_ROLES if role.phase == "A"
)


# --- §4.2.18: canonicalization applicability matrix --------------------------------


@dataclass(frozen=True, slots=True)
class RoleApplicability:
    """The assignable existing canonical properties of one recognized role (§4.2.18).

    ``assignable`` maps a **property name that exists on the wire** to the exact
    canonical property it is assigned to.  It is derived from the registered
    applicability matrix and never widened at runtime.  ``assignable`` describes
    assignability only: it is explicitly **not** a per-record REQUIRED schema, **not**
    ``MISSING`` semantics and **not** a capability requirement (``§4.2.18``).

    ``contextual`` lists, for documentation and review, the contextual / injected
    inputs the matrix registers for that role; those are carried by the in-process
    handoff objects of this module, never by a fabricated wire property.
    """

    literal: str
    assignable: Mapping[str, str]
    contextual: tuple[str, ...] = ()
    not_assignable: tuple[str, ...] = ()


def _applicability() -> tuple[RoleApplicability, ...]:
    return (
        RoleApplicability(
            literal="Plant / Material identity context",
            assignable={"plant_id": "plant_id", "material_code": "material_code"},
        ),
        RoleApplicability(
            literal="Production Requirement",
            assignable={
                "plant_id": "plant_id",
                "material_code": "material_code",
                "required_date": "required_date",
                "ProductionQty": "ProductionQty",
            },
            contextual=(
                "loss_rate + Requirement Calculation Context (never assigned by this record)",
                "BOM context (via role 3)",
                "Analysis Run context",
            ),
        ),
        RoleApplicability(
            literal="BOM Component",
            assignable={
                "plant_id": "plant_id",
                "required_date": "required_date",
                "material_code": "material_code",
                "BOMComponentQty": "BOMComponentQty",
            },
            contextual=("parent / requirement context binding (G4-A)",),
        ),
        RoleApplicability(
            literal="Inventory Snapshot",
            assignable={
                "plant_id": "plant_id",
                "material_code": "material_code",
                "inventory_snapshot_time": "inventory_snapshot_time",
                "inventory_status": "inventory_status",
                "on_hand_qty": "on_hand_qty",
            },
        ),
        RoleApplicability(
            literal="Configured Safety Stock",
            assignable={
                "plant_id": "plant_id",
                "material_code": "material_code",
                "SafetyStock": "SafetyStock",
            },
            contextual=("SafetyStock (internal handoff; §4.4.102 rules)",),
        ),
        RoleApplicability(
            literal="Inbound Supply",
            assignable={
                "plant_id": "plant_id",
                "material_code": "material_code",
                "ordered_qty": "ordered_qty",
                "received_qty": "received_qty",
                "effective_arrival_date": "effective_arrival_date",
                "inbound_status": "inbound_status",
            },
            contextual=(
                "record identity = G3-A technical record reference (not a canonical property)",
            ),
        ),
        RoleApplicability(
            literal="Substitute Relationship",
            assignable={
                "plant_id": "plant_id",
                "target_material_code": "target_material_code",
                "substitute_material_code": "substitute_material_code",
                "substitution_ratio": "substitution_ratio",
                "approval_status": "approval_status",
            },
        ),
        RoleApplicability(
            literal="Substitute Allocation",
            assignable={
                "plant_id": "plant_id",
                "target_material_code": "target_material_code",
                "substitute_material_code": "substitute_material_code",
                "AllocatedSubstituteQty": "AllocatedSubstituteQty",
            },
            contextual=("effective demand context reference (G5-A)",),
        ),
        RoleApplicability(
            literal="Supplier identity",
            assignable={"supplier_id": "supplier_id"},
        ),
        RoleApplicability(
            literal="Supplier-Material Relationship",
            assignable={
                "supplier_id": "supplier_id",
                "material_code": "material_code",
                "sourcing_status": "sourcing_status",
            },
            contextual=(
                "eligibility mapping outcome (conceptual; never a canonical field)",
            ),
        ),
        RoleApplicability(
            literal="Supplier Performance",
            assignable={
                "supplier_id": "supplier_id",
                "material_code": "material_code",
                "PerformancePeriod": "PerformancePeriod",
                "PerformanceUpdatedAt": "PerformanceUpdatedAt",
                "DeliveryPerformance": "DeliveryPerformance",
                "QualityPerformance": "QualityPerformance",
                "standard_lead_time_days": "standard_lead_time_days",
            },
            contextual=("Analysis Run context (AnalysisDate)",),
        ),
    )


APPLICABILITY_BY_ROLE: Mapping[str, RoleApplicability] = {
    entry.literal: entry for entry in _applicability()
}


# --- exact-value carriers ----------------------------------------------------------


class _Absent:
    """Sentinel distinguishing *omitted* from *present with JSON null*."""

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "<absent>"


ABSENT = _Absent()


@dataclass(frozen=True, slots=True)
class CanonicalProperty:
    """One canonical property of a constructed object, with its value preserved exactly.

    ``value`` is the accepted-view JSON value, unchanged.  JSON ``null`` is carried as
    ``None`` (``§4.3.22`` C-2 explicit missing / unavailable) and is never converted to
    ``0``, ``false`` or ``""``.  An omitted property simply has no entry at all.
    """

    name: str
    value: Any

    def decimal_value(self) -> Decimal | None:
        """Return the exact base-10 ``Decimal`` for a registered decimal string.

        ``None`` means "not a compliant registered decimal string" (including JSON
        ``null`` and non-string values).  No binary floating point is used, and no
        rounding / quantization / truncation is applied: the accepted canonical value
        itself is never rewritten, this accessor only exposes it as
        :class:`~decimal.Decimal` for later deterministic calculation.  ``0`` stays a
        valid value and is never conflated with missing (``§4.2.12``).
        """

        if not isinstance(self.value, str):
            return None
        if not _DECIMAL_STRING_RE.match(self.value):
            return None
        try:
            return Decimal(self.value)
        except InvalidOperation:  # pragma: no cover - guarded by the pattern
            return None


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    """Package-scoped logical provenance for one piece of accepted evidence.

    ``§4.5.22`` Option D ``Layered Logical Provenance Contract``:
    ``Snapshot Package Identity`` + ``Logical Dataset Role`` +
    ``Stable Source Evidence Locator`` + ``Mapping / Resolution Basis`` (when
    applicable).

    ``stable_source_evidence_locators`` / ``mapping_resolution_basis`` are the values
    the accepted record itself registers under
    ``_meta.provenance_associations`` (``§4.3.28`` E): they are carried **exactly**, in
    declared order, with no trim / case conversion / normalisation and no heuristic
    interpretation.  ``logical_observation`` is the registered ``"observation"`` the
    association states.  Nothing here is synthesised: an accepted record without a
    registered association contributes no locator, and the package-scoped path to the
    record is reported separately as :attr:`artifact` / :attr:`record_ordinal` (an
    internal construction-time path, never presented as an authoritative locator).

    This is a logical carrier only; it is deliberately **not** a wire property,
    **not** a ``"_meta"`` member and **not** a canonical field.
    """

    snapshot_package_identity: str
    logical_dataset_role: str
    artifact: str
    record_ordinal: int
    logical_observation: str | None = None
    stable_source_evidence_locators: tuple[str, ...] = ()
    mapping_resolution_basis: str | None = None
    #: Every registered ``"observation"`` the accepted record states, in declared order.
    #: Present so record-level provenance reports the registered associations without
    #: silently dropping them when no single observation was requested.
    registered_observations: tuple[str, ...] = ()

    @property
    def record_path(self) -> str:
        """Internal construction-time path to the record (never an authoritative locator)."""

        return f"{self.artifact}#{self.record_ordinal}"


@dataclass(frozen=True, slots=True)
class CanonicalObject:
    """One constructed canonical entity / relationship instance.

    ``canonicalization_role`` and ``canonical_target`` name the ``§4.3.31`` B
    assignment.  ``grain`` is the canonical grain the object was grouped under, or
    ``None`` when the object's identity is the G3-A technical record reference (an
    ``Inbound Supply`` record) rather than a composite business grain.

    ``properties`` holds only properties that are assignable for the role
    (``§4.2.18``) and that were actually present in the accepted record.  Absent
    properties are not listed and never defaulted.

    ``record_reference`` is the G3-A AcceptedPackage-scoped technical record reference
    (``§4.3.31`` D) -- a construction-time identity representation only.

    ``context_reference`` / ``context_provenance`` are present exactly when the object
    was constructed against a **resolved upstream canonical context**.  For a
    ``BOM Component`` this is the resolved ``Production Requirement`` context
    (``§4.1.13`` C, G4-A): the reference names the context object and the provenance is
    that context's own package-scoped provenance, so the upstream evidence the binding
    relied on is preserved rather than flattened into a new field.

    This class is a canonical **object**, not a wire record: a property that is absent
    here means "not assignable or not present at construction time", never "missing
    per an approved requiredness authority".
    """

    canonical_target: str
    canonicalization_role: str
    grain: tuple[CanonicalProperty, ...] | None
    properties: tuple[CanonicalProperty, ...]
    non_applicable_properties: tuple[str, ...]
    record_reference: str
    provenance: EvidenceReference
    context_reference: str | None = None
    context_provenance: EvidenceReference | None = None

    def value_of(self, name: str, default: Any = ABSENT) -> Any:
        """Return the exact value of ``name`` or ``default`` when it is not assigned."""

        for item in self.properties:
            if item.name == name:
                return item.value
        return default

    def has(self, name: str) -> bool:
        return any(item.name == name for item in self.properties)


@dataclass(frozen=True, slots=True)
class RecordReference:
    """G3-A AcceptedPackage-scoped deterministic technical record reference.

    ``§4.3.31`` D: this is *not* a canonical field, *not* a wire property, *not* a
    ``"_meta"`` member, *not* the ``Stable Source Evidence Locator`` and *not* a real
    ERP inbound identity.  It is deterministic for the same immutable accepted content
    view, it distinguishes two content-identical records at different ordinals, and it
    performs no content-derived deduplication and no cross-package identity matching.
    """

    snapshot_package_identity: str
    logical_dataset_role: str
    ordinal: int
    artifact: str

    @property
    def reference(self) -> str:
        return (
            f"{self.snapshot_package_identity}|{self.logical_dataset_role}"
            f"|{self.artifact}|{self.ordinal}"
        )


@dataclass(frozen=True, slots=True)
class ContextValueReference:
    """A resolved ``POLICY_INPUT`` / ``CONTEXT`` value handed in in-process.

    It exists only as an in-memory reference with its package-scoped provenance; it is
    not a canonical field, not a persisted entity and not a wire carrier.  ``value`` is
    the exact resolved value (``0`` is a valid value and is preserved).
    """

    semantic: str
    grain: tuple[CanonicalProperty, ...]
    value: Any
    provenance: EvidenceReference


@dataclass(frozen=True, slots=True)
class RelationOutcomeReference:
    """One G5-A effective-demand relation outcome, read-only.

    ``target_applicability`` and ``source_reservation_overlap`` are **independent**
    relation outcomes and are never collapsed into one Boolean (``§4.1.13`` D).  The
    outcome is carried by the approved mapping evidence and its basis; a caller cannot
    set it directly.
    """

    relation: str
    outcome: Any
    provenance: EvidenceReference
    mapping_basis: str


@dataclass(frozen=True, slots=True)
class EffectiveDemandContextReference:
    """G5-A read-only in-memory effective demand context reference.

    Not a canonical field, not a persisted entity, not a single Boolean, and no new
    identity component.  It carries the two independent relation outcomes separately.
    """

    source_substitute_material: Any
    target_material: Any
    relations: tuple[RelationOutcomeReference, ...]
    record_reference: str


@dataclass(frozen=True, slots=True)
class AnalysisRunContext:
    """Analysis Run identity + exactly-one AcceptedPackage linkage (``§4.3.31`` E/I-1).

    ``analysis_run_id`` / ``AnalysisDate`` are Analysis Run / ``CONTEXT`` and are **not**
    logical dataset source evidence: no logical dataset role and no Stable Source
    Evidence Locator is fabricated for them.  ``snapshot_package_identity`` records the
    one accepted package this run is bound to.
    """

    analysis_run_id: str
    analysis_date: Any
    snapshot_package_identity: str
    accepted_content_view_digest: str


# --- in-process logical handoff (``§4.3.31`` E) ------------------------------------


@dataclass(frozen=True, slots=True)
class HandoffEvidence:
    """Evidence citation offered by an in-process logical handoff entry.

    The citation names an accepted record by ``artifact`` + ``record_ordinal`` -- an
    internal construction-time path used only to locate the record inside the accepted
    content view, **never** presented as, nor used in place of, an authoritative Stable
    Source Evidence Locator.  ``evidence_locator`` optionally names one of the opaque
    locator strings the accepted record itself registers under
    ``_meta.provenance_associations`` (``§4.3.28`` E): when given, it must match a
    registered value exactly, because a caller cannot mint provenance.

    This is deliberately *not* an :class:`EvidenceReference`: a citation is an
    unverified claim until construction has confirmed it.  Only the accepted package
    identity may be attached here, because a handoff entry must never be able to point
    at another package (``§4.3.31`` E).
    """

    snapshot_package_identity: str
    logical_dataset_role: str
    artifact: str
    record_ordinal: int
    evidence_locator: str | None = None


@dataclass(frozen=True, slots=True)
class LossRateHandoff:
    """``loss_rate`` + Requirement Calculation Context (injection I-2, Phase A).

    The value is **not** trusted: it is carried only when the ``§4.4.15`` /
    ``§4.4.102`` Stage A resolution really used exactly one applicable package-scoped
    ``loss_rate`` reference.  ``loss_rate_evidence`` lists the accepted
    ``loss_rate`` evidence the resolution used; when it is empty, or contains more than
    one reference, or any reference cannot be resolved against the same
    ``AcceptedPackage``, or no resolution basis is given, the value stays unresolved and
    is never carried (``§4.2.18`` role 2 forbids the ``Production Requirement`` record
    itself from assigning ``loss_rate``).
    """

    plant_id: Any
    parent_material_code: Any
    required_date: Any
    evidence: HandoffEvidence
    loss_rate_evidence: tuple[HandoffEvidence, ...] = ()
    loss_rate: Any = None
    resolution_basis: str = ""
    resolution_note: str = ""


@dataclass(frozen=True, slots=True)
class SafetyStockHandoff:
    """``SafetyStock`` internal handoff (injection I-5, Phase A).

    Used when the ``Configured Safety Stock`` dataset does not resolve the grain and
    another policy evidence record inside the same AcceptedPackage does.  A value may
    only be carried when exactly one applicable ``SafetyStock`` reference resolved the
    grain; zero or more than one reference stays unresolved, and conflicting values at
    the same canonical grain are reported per ``§4.4.102`` Stage B as
    ``CONSISTENCY`` / ``CONSISTENCY_CONFLICT`` instead of being silently resolved.

    ``configured_safety_stock_evidence`` lists the accepted ``Configured Safety Stock``
    evidence for the grain.  Existing evidence from that dataset never loses to the
    handoff: two sources are never merged by precedence (``§4.4.102`` C).
    """

    plant_id: Any
    material_code: Any
    evidence: HandoffEvidence
    safety_stock_evidence: tuple[HandoffEvidence, ...] = ()
    configured_safety_stock_evidence: tuple[HandoffEvidence, ...] = ()
    safety_stock: Any = None
    resolution_basis: str = ""
    resolution_note: str = ""


@dataclass(frozen=True, slots=True)
class BomParentContextHandoff:
    """G4-A BOM parent / requirement context binding (injection I-7, Phase A).

    ``evidence`` must point at accepted ``Production Requirement`` evidence in the same
    AcceptedPackage, and that evidence record must itself have been constructed and
    grain-resolved.  A caller therefore cannot create a parent context without source
    evidence (``§4.1.13`` C).
    """

    plant_id: Any
    required_date: Any
    evidence: HandoffEvidence
    resolution_note: str = ""


#: The two G5-A relations.  They stay independent and are never collapsed into one
#: Boolean (``§4.1.13`` D).
RELATION_TARGET_APPLICABILITY: str = "Target Applicability"
RELATION_SOURCE_RESERVATION_OVERLAP: str = "Source Reservation Overlap"

#: The registered G5-A relations, in deterministic order.
G5_RELATIONS: tuple[str, ...] = (
    RELATION_TARGET_APPLICABILITY,
    RELATION_SOURCE_RESERVATION_OVERLAP,
)


@dataclass(frozen=True, slots=True)
class EffectiveDemandRelationHandoff:
    """G5-A effective demand relation evidence (injection I-8, Phase A).

    A handoff entry carries **evidence only** -- never the relation outcome, so a caller
    cannot state "applicable" / "overlaps" by hand (``§4.1.13`` D).  ``relation`` is one
    of :data:`G5_RELATIONS`; ``mapping_basis`` names the mapping the entry attributes the
    evidence to.

    Phase A does **not** derive a conceptual outcome from the cited evidence: the
    approved outcomes are ``applicable`` / ``not applicable`` / ``unresolved`` and
    ``overlaps`` / ``does not overlap`` / ``unresolved``, and the concrete source value
    -> conceptual outcome mapping is ``SOURCE-SPECIFIC`` / Adapter-defined
    (``§4.5.9`` / ``§4.5.26``) with no approved mapping available to Phase A.  Registered
    canonical values such as ``approval_status`` or ``AllocatedSubstituteQty`` are
    therefore **not** relation outcomes, and every relation is reported ``unresolved``
    rather than relabelled or invented.
    """

    source_substitute_material: Any
    target_material: Any
    relation: str
    evidence: HandoffEvidence
    mapping_basis: str


@dataclass(frozen=True, slots=True)
class PhaseAHandoff:
    """The complete in-process logical handoff for one Phase A construction.

    This interface is **not** a new external evidence source, **not** a transport
    carrier, **not** a second Snapshot Package and **not** a new top-level input
    carrier: every entry must be traceable to evidence inside the same
    ``AcceptedPackage`` (``§4.3.31`` E), and unverifiable entries leave the affected
    semantic unresolved instead of silently supplying a value.
    """

    analysis_run_id: str
    analysis_date: Any
    loss_rate: tuple[LossRateHandoff, ...] = ()
    safety_stock: tuple[SafetyStockHandoff, ...] = ()
    bom_parent_context: tuple[BomParentContextHandoff, ...] = ()
    effective_demand: tuple[EffectiveDemandRelationHandoff, ...] = ()


# --- result ------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CanonicalObjectSet:
    """Constructed canonical objects for one target, split by construction outcome."""

    canonical_target: str
    resolved: tuple[CanonicalObject, ...] = ()
    unresolved: tuple[CanonicalObject, ...] = ()


@dataclass(frozen=True, slots=True)
class CanonicalConstructionReport:
    """Deterministic Phase A construction result for one accepted package.

    ``checks`` reuses the existing ``passed`` / ``failed`` / ``not_evaluable`` state
    vocabulary only.  ``issues`` uses only the inherited taxonomy and may only ever
    contain ``IDENTITY_RESOLUTION`` / ``UNRESOLVED_IDENTITY`` and
    ``CONSISTENCY`` / ``CONSISTENCY_CONFLICT`` (``§4.4.102``); no other category,
    reason, severity or error code is created.  ``checks`` and ``issues`` are not
    aggregated into any new report-level status.
    """

    package_id: str
    accepted_content_view_digest: str
    analysis_run: AnalysisRunContext
    analysis_date_resolved: bool
    object_sets: tuple[CanonicalObjectSet, ...]
    inbound_records: tuple[CanonicalObject, ...]
    substitute_allocations: tuple[CanonicalObject, ...]
    effective_demand_contexts: tuple[EffectiveDemandContextReference, ...]
    loss_rate_contexts: tuple[ContextValueReference, ...]
    safety_stock_contexts: tuple[ContextValueReference, ...]
    unrecognized_roles: tuple[str, ...]
    checks: tuple[tuple[str, str, str | None], ...]
    issues: tuple[Issue, ...]
    layer2_note: str = ""

    def objects_for(self, canonical_target: str) -> tuple[CanonicalObject, ...]:
        for entry in self.object_sets:
            if entry.canonical_target == canonical_target:
                return entry.resolved
        return ()

    def unresolved_for(self, canonical_target: str) -> tuple[CanonicalObject, ...]:
        for entry in self.object_sets:
            if entry.canonical_target == canonical_target:
                return entry.unresolved
        return ()

    def check_states(self) -> dict[str, str]:
        return {name: state for name, state, _ in self.checks}

    def to_dict(self) -> dict[str, object]:
        return {
            "package_id": self.package_id,
            "accepted_content_view_digest": self.accepted_content_view_digest,
            "phase": "A",
            "analysis_run": {
                "analysis_run_id": self.analysis_run.analysis_run_id,
                "AnalysisDate": self.analysis_run.analysis_date,
                "snapshot_package_identity": (
                    self.analysis_run.snapshot_package_identity
                ),
                "analysis_date_resolved": self.analysis_date_resolved,
            },
            "object_sets": [
                {
                    "canonical_target": entry.canonical_target,
                    "resolved": [
                        _object_to_dict(item) for item in entry.resolved
                    ],
                    "unresolved": [
                        _object_to_dict(item) for item in entry.unresolved
                    ],
                }
                for entry in self.object_sets
            ],
            "inbound_records": [
                _object_to_dict(item) for item in self.inbound_records
            ],
            "effective_demand_contexts": [
                _effective_demand_to_dict(item)
                for item in self.effective_demand_contexts
            ],
            "loss_rate_contexts": [
                _context_value_to_dict(item) for item in self.loss_rate_contexts
            ],
            "safety_stock_contexts": [
                _context_value_to_dict(item) for item in self.safety_stock_contexts
            ],
            "unrecognized_roles": list(self.unrecognized_roles),
            "checks": [
                {"name": name, "state": state, "note": note}
                for name, state, note in self.checks
            ],
            "issues": [issue.to_dict() for issue in self.issues],
            "layer2_note": self.layer2_note,
        }


def _object_to_dict(item: CanonicalObject) -> dict[str, object]:
    return {
        "canonical_target": item.canonical_target,
        "canonicalization_role": item.canonicalization_role,
        "grain": [
            {"name": prop.name, "value": prop.value} for prop in (item.grain or ())
        ],
        "properties": [
            {"name": prop.name, "value": prop.value} for prop in item.properties
        ],
        "non_applicable_properties": list(item.non_applicable_properties),
        "record_reference": item.record_reference,
        "context_reference": item.context_reference,
        "context_provenance": (
            None
            if item.context_provenance is None
            else _provenance_to_dict(item.context_provenance)
        ),
        "provenance": _provenance_to_dict(item.provenance),
    }


def _provenance_to_dict(item: EvidenceReference) -> dict[str, object]:
    """Serialise the accepted provenance exactly as the record registered it."""

    return {
        "snapshot_package_identity": item.snapshot_package_identity,
        "logical_dataset_role": item.logical_dataset_role,
        "logical_observation": item.logical_observation,
        "registered_observations": list(item.registered_observations),
        "stable_source_evidence_locators": list(item.stable_source_evidence_locators),
        "mapping_resolution_basis": item.mapping_resolution_basis,
        "accepted_record_path": item.record_path,
    }


def _effective_demand_to_dict(item: EffectiveDemandContextReference) -> dict[str, object]:
    return {
        "source_substitute_material": item.source_substitute_material,
        "target_material": item.target_material,
        "record_reference": item.record_reference,
        "relations": [
            {
                "relation": relation.relation,
                "outcome": relation.outcome,
                "mapping_basis": relation.mapping_basis,
                "provenance": _provenance_to_dict(relation.provenance),
            }
            for relation in item.relations
        ],
    }


def _context_value_to_dict(item: ContextValueReference) -> dict[str, object]:
    return {
        "semantic": item.semantic,
        "grain": [{"name": prop.name, "value": prop.value} for prop in item.grain],
        "value": item.value,
        "provenance": _provenance_to_dict(item.provenance),
    }


# --- internal accumulator ----------------------------------------------------------


class _Construction:
    """Mutable accumulator producing the immutable Phase A result."""

    def __init__(
        self,
        *,
        package: AcceptedPackage,
        analysis_run_id: str,
        analysis_date: Any,
    ) -> None:
        self.package = package
        self.analysis_run_id = analysis_run_id
        self.analysis_date = analysis_date
        self.checks: list[tuple[str, str, str | None]] = []
        self.issues: list[Issue] = []
        self.unrecognized_roles: list[str] = []
        self.loss_rate_contexts: list[ContextValueReference] = []
        self.safety_stock_contexts: list[ContextValueReference] = []
        self.effective_demand_contexts: list[EffectiveDemandContextReference] = []

    def check(self, name: str, state: str, note: str | None = None) -> None:
        self.checks.append((name, state, note))

    def issue(
        self,
        *,
        category: str,
        reason: str,
        location: str,
        detail: str,
        affected_evidence: str,
        design_reference: str,
        consequence_context: str,
    ) -> None:
        self.issues.append(
            Issue(
                location=location,
                detail=detail,
                category=category,
                reason=reason,
                layer=LAYER_2,
                affected_evidence=affected_evidence,
                blast_radius=(
                    "affected canonical object / grain only (no package rejection)"
                ),
                design_reference=design_reference,
                consequence_context=consequence_context,
            )
        )

    def unresolved_identity(
        self,
        *,
        location: str,
        detail: str,
        affected_evidence: str,
        design_reference: str,
    ) -> None:
        self.issue(
            category=CATEGORY_IDENTITY_RESOLUTION,
            reason=REASON_UNRESOLVED_IDENTITY,
            location=location,
            detail=detail,
            affected_evidence=affected_evidence,
            design_reference=design_reference,
            consequence_context=(
                "evidence stays unresolved; no value is invented and the package "
                "disposition is unchanged"
            ),
        )


def _evidence_reference(
    *,
    package: AcceptedPackage,
    role: str,
    artifact: str,
    ordinal: int,
    record: JsonObject | None = None,
    observation: str | None = None,
) -> EvidenceReference:
    """Build the package-scoped provenance of one accepted record.

    The registered ``_meta.provenance_associations`` values are carried **exactly** as
    the record states them; when ``observation`` is given the matching association is
    the one reported.  Nothing is synthesised: a record with no registered association
    yields an empty locator tuple, and ``artifact`` / ``ordinal`` are reported only as
    the internal accepted-record path (``§4.3.28`` E / ``§4.5.22`` Option D).
    """

    associations = read_provenance_associations(record) if record is not None else ()
    association: ProvenanceAssociation | None = None
    if observation is not None:
        for item in associations:
            if item.observation == observation:
                association = item
                break
    if association is not None:
        locators = association.evidence
        basis = association.mapping_basis
        stated = association.observation
    elif observation is not None:
        locators = ()
        basis = None
        stated = observation
    else:
        # No single observation was requested: report every registered locator in
        # declared order rather than dropping the record's registered associations.
        locators = tuple(
            locator for item in associations for locator in item.evidence
        )
        basis = None
        stated = None
    return EvidenceReference(
        snapshot_package_identity=package.package_id,
        logical_dataset_role=role,
        artifact=artifact,
        record_ordinal=ordinal,
        logical_observation=stated,
        stable_source_evidence_locators=locators,
        mapping_resolution_basis=basis,
        registered_observations=tuple(
            item.observation for item in associations if item.observation is not None
        ),
    )


def _record_reference(
    *, package: AcceptedPackage, role: str, artifact: str, ordinal: int
) -> RecordReference:
    return RecordReference(
        snapshot_package_identity=package.package_id,
        logical_dataset_role=role,
        ordinal=ordinal,
        artifact=artifact,
    )


def _properties_from(
    record: JsonObject, assignable: Mapping[str, str]
) -> tuple[tuple[CanonicalProperty, ...], tuple[str, ...]]:
    """Project one accepted record onto its role's assignable canonical properties.

    Only properties that are present in the record are carried; a property that is
    absent is never materialised, defaulted or guessed (``§4.2.18``).  A present
    property outside the registered assignable set is reported as not applicable and is
    never coerced into a canonical property.
    """

    assigned: list[CanonicalProperty] = []
    non_applicable: list[str] = []

    for name in record.order:
        if name == PROPERTY_META:
            # Layer-1 owns the reserved namespace shape; canonicalization neither
            # recreates nor reads it (``§4.3.31`` D forbids creating a "_meta" member).
            continue
        if name not in V02_CANONICAL_RECORD_PROPERTY_SET:
            # Layer-1 already rejected undeclared record properties; this is defensive
            # only and never becomes a canonical property.
            non_applicable.append(name)
            continue
        canonical_name = assignable.get(name)
        if canonical_name is None:
            non_applicable.append(name)
            continue
        assigned.append(CanonicalProperty(canonical_name, record[name]))

    return tuple(assigned), tuple(sorted(non_applicable))


def _grain_tuple(
    record: JsonObject, keys: Iterable[str]
) -> tuple[CanonicalProperty, ...] | None:
    """Return the exact grain values, or ``None`` when an identity part is not present.

    A missing identity part is never replaced by a default: the object stays
    unresolved instead (``§4.4.26``).
    """

    parts: list[CanonicalProperty] = []
    for key in keys:
        if key not in record:
            return None
        parts.append(CanonicalProperty(key, record[key]))
    return tuple(parts)


def _grain_key(record: JsonObject, keys: Iterable[str]) -> tuple[Any, ...] | None:
    key: list[Any] = []
    for name in keys:
        if name not in record:
            return None
        key.append(record[name])
    return tuple(key)


def _grain_label(grain: tuple[CanonicalProperty, ...] | None) -> str:
    if not grain:
        return "<no grain>"
    return " + ".join(f"{prop.name}={prop.value!r}" for prop in grain)


# --- Phase A construction ----------------------------------------------------------

#: Canonical targets that Phase A constructs as grain-keyed entity sets.  ``Inbound
#: Supply`` is deliberately absent: its identity representation is the G3-A technical
#: record reference, so each accepted inbound record is its own canonical instance
#: (``§4.3.31`` D / ``§4.1.13`` B).
GRAIN_KEYED_TARGETS: Mapping[str, tuple[str, ...]] = {
    "Plant": ("plant_id",),
    "Material": ("material_code",),
    "Production Requirement": ("plant_id", "material_code", "required_date"),
    "Inventory Snapshot": (
        "plant_id",
        "material_code",
        "inventory_snapshot_time",
    ),
    "Configured Safety Stock": ("plant_id", "material_code"),
    "Substitute Relationship": (
        "plant_id",
        "target_material_code",
        "substitute_material_code",
    ),
    "Substitute Allocation": (
        "plant_id",
        "target_material_code",
        "substitute_material_code",
    ),
    "Supplier": ("supplier_id",),
    "Supplier-Material Relationship": ("supplier_id", "material_code"),
    "Supplier Performance": (
        "supplier_id",
        "material_code",
        "PerformancePeriod",
    ),
}

#: Construction order of the grain-keyed canonical targets (``§4.3.31`` F, role 1--11).
GRAIN_KEYED_TARGET_ORDER: tuple[str, ...] = (
    "Plant",
    "Material",
    "Production Requirement",
    "Inventory Snapshot",
    "Configured Safety Stock",
    "Substitute Relationship",
    "Substitute Allocation",
    "Supplier",
    "Supplier-Material Relationship",
    "Supplier Performance",
)

ROLE_FOR_TARGET: Mapping[str, str] = {
    "Plant": "Plant / Material identity context",
    "Material": "Plant / Material identity context",
    "Production Requirement": "Production Requirement",
    "Inventory Snapshot": "Inventory Snapshot",
    "Configured Safety Stock": "Configured Safety Stock",
    "Substitute Relationship": "Substitute Relationship",
    "Substitute Allocation": "Substitute Allocation",
    "Supplier": "Supplier identity",
    "Supplier-Material Relationship": "Supplier-Material Relationship",
    "Supplier Performance": "Supplier Performance",
}

#: ``Plant / Material identity context`` evidence yields two canonical identities, so
#: its two identity components are resolved independently.
IDENTITY_COMPONENT_TARGETS: Mapping[str, str] = {
    "plant_id": "Plant",
    "material_code": "Material",
}


@dataclass(frozen=True, slots=True)
class ProvenanceAssociation:
    """One ``_meta.provenance_associations[]`` entry, exactly as the record registers it.

    ``§4.3.28`` E registers the controlled member shape and its literals
    (``"provenance_associations"`` / ``"observation"`` / ``"evidence"`` /
    ``"mapping_basis"``).  ``evidence`` is an array of opaque Stable Source Evidence
    Locator strings; ``mapping_basis`` is an optional exact JSON string required only
    when a semantic mapping / resolution happened.  No trim, case conversion, Unicode
    normalisation, numeric coercion or heuristic interpretation is applied.
    """

    observation: str | None
    evidence: tuple[str, ...]
    mapping_basis: str | None


def read_provenance_associations(record: JsonObject) -> tuple[ProvenanceAssociation, ...]:
    """Read the registered provenance associations of one accepted record.

    Only the approved ``_meta`` shape is read (``§4.3.28`` E).  Anything absent or not
    in the registered shape contributes **no** association, because a locator or basis
    may never be invented: an accepted record without registered provenance simply has
    no registered provenance.
    """

    meta = record.get(PROPERTY_META) if PROPERTY_META in record else None
    if not isinstance(meta, dict):
        return ()
    associations = meta.get("provenance_associations")
    if not isinstance(associations, list):
        return ()

    outbound: list[ProvenanceAssociation] = []
    for association in associations:
        if not isinstance(association, dict):
            continue
        observation = association.get("observation")
        basis = association.get("mapping_basis")
        evidence = association.get("evidence")
        locators: tuple[str, ...] = ()
        if isinstance(evidence, list):
            locators = tuple(item for item in evidence if isinstance(item, str))
        outbound.append(
            ProvenanceAssociation(
                observation=observation if isinstance(observation, str) else None,
                evidence=locators,
                mapping_basis=basis if isinstance(basis, str) else None,
            )
        )
    return tuple(outbound)


def _accepted_record_index(accepted: AcceptedPackage) -> dict[str, JsonObject]:
    """Return ``<artifact>#<ordinal> -> accepted record`` for the accepted content view.

    The index is built from the accepted bytes only, so a handoff citation can be
    checked against the evidence the package actually carries.  A record that is not a
    JSON object is simply absent from the index and can therefore never back a claim.
    """

    index: dict[str, JsonObject] = {}
    for _role, artifact in accepted.datasets():
        raw = accepted.records_for(artifact)
        if raw is None:
            continue
        try:
            payload: Any = parse_strict_json(raw, source=artifact)
        except StrictJsonError:
            continue
        if not isinstance(payload, list):
            continue
        for ordinal, record in enumerate(payload):
            if isinstance(record, JsonObject):
                index[f"{artifact}#{ordinal}"] = record
    return index


def _targets_by_artifact(
    accepted: AcceptedPackage,
) -> tuple[dict[str, tuple[str, int]], tuple[str, ...]]:
    """Return ``artifact -> (role, ordinal)`` plus parse-blocked artifacts.

    Every record's position is the **dataset-internal ordinal over the accepted stable
    content view**, which is what G3-A requires.  Business artifacts are never re-read
    from the filesystem.
    """

    located: dict[str, tuple[str, int]] = {}
    blocked: list[str] = []

    for role, artifact in accepted.datasets():
        raw = accepted.records_for(artifact)
        if raw is None:
            blocked.append(artifact)
            continue
        try:
            payload: Any = parse_strict_json(raw, source=artifact)
        except StrictJsonError:
            blocked.append(artifact)
            continue
        if not isinstance(payload, list):
            blocked.append(artifact)
            continue
        for ordinal, record in enumerate(payload):
            if not isinstance(record, JsonObject):
                continue
            located[f"{artifact}#{ordinal}"] = (role, ordinal)

    return located, tuple(blocked)


@dataclass(frozen=True, slots=True)
class _EvidenceVerification:
    """Outcome of verifying one offered handoff evidence citation."""

    verified: bool
    problem: str | None
    role: str | None = None
    ordinal: int | None = None
    artifact: str | None = None
    value: Any = None
    association: ProvenanceAssociation | None = None

    @property
    def record_path(self) -> str:
        if self.artifact is None or self.ordinal is None:
            return ""
        return f"{self.artifact}#{self.ordinal}"


def _verify_handoff_evidence(
    *,
    accepted: AcceptedPackage,
    evidence: HandoffEvidence,
    located: Mapping[str, tuple[str, int]],
    records: Mapping[str, JsonObject],
    expected_roles: tuple[str, ...] | None = None,
    observation: str | None = None,
) -> _EvidenceVerification:
    """Verify one offered handoff citation against the accepted content view.

    The citation names an accepted record by ``artifact`` + ``record_ordinal`` (an
    internal construction-time path, **not** an authoritative Stable Source Evidence
    Locator) and may name an ``evidence_locator`` the record registered.  A citation is
    only accepted when **all** of the following hold:

    * it names the same ``AcceptedPackage`` identity;
    * the record path resolves to a real accepted record;
    * its ``logical_dataset_role`` matches the role that record actually belongs to;
    * when ``expected_roles`` is given, that role is one of them;
    * when ``evidence_locator`` is given, the accepted record's registered
      ``_meta.provenance_associations`` actually contain that exact opaque locator
      string -- a caller cannot mint an authoritative locator (``§4.3.28`` E);
    * when ``observation`` is given, a registered association states that exact
      ``"observation"``, and the record carries that canonical property; the returned
      ``value`` is then the accepted value.

    Anything else stays unverified, and an unverified citation never supplies a value
    (``§4.3.31`` E: no external caller value, no default, no synthetic fallback).
    """

    if evidence.snapshot_package_identity != accepted.package_id:
        return _EvidenceVerification(
            verified=False,
            problem=(
                "evidence cites a different Snapshot Package Identity; an external "
                "caller value may not supply this semantic (§4.3.31 E)"
            ),
        )

    path = f"{evidence.artifact}#{evidence.record_ordinal}"
    found = located.get(path)
    if found is None:
        return _EvidenceVerification(
            verified=False,
            problem=(
                f"cited accepted record path {path!r} does not resolve to a record of "
                "this package (§4.3.31 E)"
            ),
        )

    role, ordinal = found
    if evidence.logical_dataset_role != role:
        return _EvidenceVerification(
            verified=False,
            problem=(
                f"evidence declares logical dataset role "
                f"{evidence.logical_dataset_role!r} but {path!r} belongs to role "
                f"{role!r}; the citation is inconsistent and is not used"
            ),
        )

    if expected_roles is not None and role not in expected_roles:
        return _EvidenceVerification(
            verified=False,
            problem=(
                f"evidence role {role!r} is not one of the accepted roles that may "
                f"support this semantic {list(expected_roles)}"
            ),
            role=role,
            ordinal=ordinal,
            artifact=evidence.artifact,
        )

    record = records.get(path)
    if record is None:
        return _EvidenceVerification(
            verified=False,
            problem=(
                f"accepted record {path!r} could not be read as a record object; the "
                "cited evidence cannot be established"
            ),
            role=role,
            ordinal=ordinal,
            artifact=evidence.artifact,
        )

    associations = read_provenance_associations(record)

    if evidence.evidence_locator is not None:
        registered = [
            locator
            for association in associations
            for locator in association.evidence
        ]
        if evidence.evidence_locator not in registered:
            return _EvidenceVerification(
                verified=False,
                problem=(
                    f"the cited evidence locator {evidence.evidence_locator!r} is not "
                    "registered by the accepted record's _meta.provenance_associations; "
                    "a locator may not be minted by the caller (§4.3.28 E)"
                ),
                role=role,
                ordinal=ordinal,
                artifact=evidence.artifact,
            )

    value: Any = None
    association: ProvenanceAssociation | None = None
    if observation is not None:
        matching = [
            item
            for item in associations
            if item.observation == observation
            and (
                evidence.evidence_locator is None
                or evidence.evidence_locator in item.evidence
            )
        ]
        if not matching:
            return _EvidenceVerification(
                verified=False,
                problem=(
                    f"the accepted record {path!r} registers no "
                    f"_meta.provenance_associations entry for observation "
                    f"{observation!r}"
                    + (
                        f" with evidence {evidence.evidence_locator!r}"
                        if evidence.evidence_locator is not None
                        else ""
                    )
                    + "; the injected value has no accepted provenance supporting it "
                    "(§4.3.28 E / §4.3.31 E)"
                ),
                role=role,
                ordinal=ordinal,
                artifact=evidence.artifact,
            )
        if len(matching) > 1:
            return _EvidenceVerification(
                verified=False,
                problem=(
                    f"the accepted record {path!r} registers {len(matching)} "
                    f"associations for observation {observation!r}; exactly one "
                    "applicable association is required and they are not merged "
                    "(§4.4.102 C Stage A)"
                ),
                role=role,
                ordinal=ordinal,
                artifact=evidence.artifact,
            )
        association = matching[0]
        if observation not in record:
            return _EvidenceVerification(
                verified=False,
                problem=(
                    f"the accepted record {path!r} registers observation "
                    f"{observation!r} but does not carry that canonical property; the "
                    "value cannot be established"
                ),
                role=role,
                ordinal=ordinal,
                artifact=evidence.artifact,
            )
        value = record[observation]

    return _EvidenceVerification(
        verified=True,
        problem=None,
        role=role,
        ordinal=ordinal,
        artifact=evidence.artifact,
        value=value,
        association=association,
    )


def _resolved_evidence_reference(
    *, accepted: AcceptedPackage, verification: _EvidenceVerification
) -> EvidenceReference:
    """Build the confirmed provenance for a verified handoff citation.

    Only the values the accepted record itself registered are carried: its opaque
    ``evidence`` locators, its ``mapping_basis`` and its ``observation``.  An accepted
    record without a registered association contributes an empty locator tuple rather
    than a synthesised one (``§4.3.28`` E).
    """

    assert verification.role is not None and verification.artifact is not None
    assert verification.ordinal is not None
    association = verification.association
    return EvidenceReference(
        snapshot_package_identity=accepted.package_id,
        logical_dataset_role=verification.role,
        artifact=verification.artifact,
        record_ordinal=verification.ordinal,
        logical_observation=(
            association.observation if association is not None else None
        ),
        stable_source_evidence_locators=(
            association.evidence if association is not None else ()
        ),
        mapping_resolution_basis=(
            association.mapping_basis if association is not None else None
        ),
    )


def construct_canonical_objects(
    accepted: AcceptedPackage,
    handoff: PhaseAHandoff,
    *,
    layer2_report: Layer2Report | None = None,
) -> CanonicalConstructionReport:
    """Construct the Phase A canonical objects for one accepted package.

    Input boundary: ``AcceptedPackage`` (+ optionally its already-computed Layer-2
    report) and the approved Phase A in-process handoff.  Output: deterministic,
    immutable, in-memory canonical entities / relationships / context references with
    their provenance.

    Layer-2 is re-verified before any construction (``MG-2`` / ``§4.3.28`` C.3), and a
    supplied report must belong to this very package and accepted content view.  When
    required integrity can no longer be re-established, or the supplied report is
    foreign / stale, nothing is constructed and no Layer-1 rejection is implied.
    """

    return _construct(accepted, handoff, layer2_report=layer2_report)


def _report_binding_problem(
    accepted: AcceptedPackage, layer2_report: Layer2Report
) -> str | None:
    """Return why ``layer2_report`` may not authorise construction, or ``None``.

    ``MG-2`` trusted reuse requires the reuse to be bound to the **same** accepted
    package identity and the **same** accepted content view.  A report produced for
    another package, or for a different content view of this package, is foreign /
    stale and must never let canonicalization continue.
    """

    if layer2_report.package_id != accepted.package_id:
        return (
            "the supplied Layer-2 report belongs to package "
            f"{layer2_report.package_id!r}, not to {accepted.package_id!r}; a foreign "
            "report never authorises construction (§4.3.28 C.2/C.3)"
        )
    if layer2_report.accepted_content_view_digest != accepted.content_view_digest:
        return (
            "the supplied Layer-2 report was produced against accepted content view "
            f"{layer2_report.accepted_content_view_digest!r}, not against "
            f"{accepted.content_view_digest!r}; a stale report never authorises "
            "construction (§4.3.28 C.2/C.3)"
        )
    return None


def _construct(
    accepted: AcceptedPackage,
    handoff: PhaseAHandoff,
    *,
    layer2_report: Layer2Report | None = None,
) -> CanonicalConstructionReport:

    if layer2_report is None:
        layer2_report = validate_layer2(accepted)

    build = _Construction(
        package=accepted,
        analysis_run_id=handoff.analysis_run_id,
        analysis_date=handoff.analysis_date,
    )

    analysis_run = AnalysisRunContext(
        analysis_run_id=handoff.analysis_run_id,
        analysis_date=handoff.analysis_date,
        snapshot_package_identity=accepted.package_id,
        accepted_content_view_digest=accepted.content_view_digest,
    )

    binding_problem = _report_binding_problem(accepted, layer2_report)
    if binding_problem is not None:
        build.check(
            LAYER2_REPORT_BINDING,
            EVALUATION_FAILED,
            binding_problem,
        )
        return _empty_report(build, accepted, analysis_run, layer2_report)

    if not layer2_report.reusable:
        build.check(
            CANONICALIZATION_ANALYSIS_RUN,
            EVALUATION_FAILED,
            "trusted reuse re-verification did not pass; no canonical object was "
            "constructed and no Layer-1 rejection is implied (§4.3.28 C.3 MG-2)",
        )
        return _empty_report(build, accepted, analysis_run, layer2_report)

    located, blocked = _targets_by_artifact(accepted)
    accepted_records = _accepted_record_index(accepted)

    # --- Analysis Run context (I-1): identity + exactly-one package linkage ---------
    build.check(
        CANONICALIZATION_ANALYSIS_RUN,
        EVALUATION_PASSED,
        "Analysis Run identity is bound to exactly one AcceptedPackage; no logical "
        "dataset role and no Stable Source Evidence Locator is fabricated for it "
        "(§4.3.31 E / I-1)",
    )
    analysis_date_resolved = handoff.analysis_date is not None
    if not analysis_date_resolved:
        build.check(
            f"{CANONICALIZATION_ANALYSIS_RUN}.AnalysisDate",
            EVALUATION_NOT_EVALUABLE,
            "AnalysisDate stays unresolved because no value was handed in; no default "
            "date is invented",
        )

    if blocked:
        for artifact in sorted(blocked):
            build.check(
                f"{CANONICALIZATION_TARGET_ASSIGNMENT}:{artifact}",
                EVALUATION_NOT_EVALUABLE,
                "accepted-view artifact is not reachable as a bare record array; no "
                "canonical object is constructed from it",
            )

    # --- role recognition + assignment + applicability (AC A / B) ------------------
    records: list[tuple[str, str, int, JsonObject]] = []
    for role, artifact in accepted.datasets():
        raw = accepted.records_for(artifact)
        if raw is None:
            continue
        try:
            payload: Any = parse_strict_json(raw, source=artifact)
        except StrictJsonError:
            continue
        if not isinstance(payload, list):
            continue

        recognized = role in CANONICALIZATION_ROLE_BY_LITERAL
        for ordinal, record in enumerate(payload):
            if not isinstance(record, JsonObject):
                continue
            location = f"{artifact}#{ordinal}"
            if not recognized:
                if role not in build.unrecognized_roles:
                    build.unrecognized_roles.append(role)
                build.check(
                    f"{CANONICALIZATION_ROLE_RECOGNITION}:{location}",
                    EVALUATION_NOT_EVALUABLE,
                    "unrecognized logical dataset role at the canonicalization stage; "
                    "no automatic Validation Issue and no Layer-1 rejection is created "
                    "(§4.3.31 C / §4.4.102 B)",
                )
                continue
            canonicalization_role = CANONICALIZATION_ROLE_BY_LITERAL[role]
            if canonicalization_role.phase == "B":
                # Phase A must not open the procurement-policy channel; doing so would
                # pre-execute Phase B (§4.3.31 F).  No object is constructed.
                build.check(
                    f"{CANONICALIZATION_ROLE_RECOGNITION}:{location}",
                    EVALUATION_NOT_EVALUABLE,
                    "role 12 'Procurement policy input' is registered for Phase B only; "
                    "Phase A does not resolve ApplicableMOQ and does not create a "
                    "Procurement Recommendation Context (§4.3.31 F)",
                )
                continue
            applicability = APPLICABILITY_BY_ROLE.get(role)
            if applicability is None:  # pragma: no cover - registry is closed
                build.check(
                    f"{CANONICALIZATION_APPLICABILITY}:{location}",
                    EVALUATION_NOT_EVALUABLE,
                    "no applicability row is registered for this role; nothing is "
                    "assigned and nothing is guessed",
                )
                continue
            build.check(f"{CANONICALIZATION_ROLE_RECOGNITION}:{location}", EVALUATION_PASSED)
            build.check(f"{CANONICALIZATION_APPLICABILITY}:{location}", EVALUATION_PASSED)
            records.append((role, artifact, ordinal, record))

    # --- grain resolution for grain-keyed targets ---------------------------------
    object_sets, resolved_objects = _resolve_grain_keyed(build, accepted, records)

    # --- G3-A Inbound Supply technical record reference ----------------------------
    inbound_records = _construct_inbound(build, accepted, records)

    # --- G5-A effective demand context references (read-only) ----------------------
    effective_demand, demand_issues = _effective_demand_references(
        accepted, handoff, located, accepted_records
    )
    build.effective_demand_contexts.extend(effective_demand)
    build.issues.extend(demand_issues)

    # --- POLICY_INPUT / CONTEXT internal handoff -----------------------------------
    production_requirements = resolved_objects.get("Production Requirement", ())
    _handoff_loss_rate(
        build,
        accepted,
        located,
        accepted_records,
        handoff,
        production_requirements,
    )
    safety_stock_targets = resolved_objects.get("Configured Safety Stock", ())
    _handoff_safety_stock(
        build,
        accepted,
        located,
        accepted_records,
        handoff,
        safety_stock_targets,
    )

    # --- G4-A BOM parent / requirement context binding ------------------------------
    bom_resolved, bom_unresolved = _construct_bom_components(
        build,
        accepted,
        records,
        handoff,
        located,
        accepted_records,
        production_requirements,
    )
    object_sets.append(
        CanonicalObjectSet(
            "BOM Component", resolved=bom_resolved, unresolved=bom_unresolved
        )
    )

    # --- G5-A allocation relationship objects (read-only context) -------------------
    return CanonicalConstructionReport(
        package_id=accepted.package_id,
        accepted_content_view_digest=accepted.content_view_digest,
        analysis_run=analysis_run,
        analysis_date_resolved=analysis_date_resolved,
        object_sets=tuple(object_sets),
        inbound_records=tuple(inbound_records),
        substitute_allocations=resolved_objects.get("Substitute Allocation", ()),
        effective_demand_contexts=tuple(build.effective_demand_contexts),
        loss_rate_contexts=tuple(build.loss_rate_contexts),
        safety_stock_contexts=tuple(build.safety_stock_contexts),
        unrecognized_roles=tuple(build.unrecognized_roles),
        checks=_sorted_checks(build.checks),
        issues=tuple(sorted(build.issues, key=Issue.sort_key)),
        layer2_note=layer2_report.note,
    )


def _empty_report(
    build: _Construction,
    accepted: AcceptedPackage,
    analysis_run: AnalysisRunContext,
    layer2_report: Layer2Report,
) -> CanonicalConstructionReport:
    return CanonicalConstructionReport(
        package_id=accepted.package_id,
        accepted_content_view_digest=accepted.content_view_digest,
        analysis_run=analysis_run,
        analysis_date_resolved=False,
        object_sets=(),
        inbound_records=(),
        substitute_allocations=(),
        effective_demand_contexts=(),
        loss_rate_contexts=(),
        safety_stock_contexts=(),
        unrecognized_roles=(),
        checks=_sorted_checks(build.checks),
        issues=tuple(sorted(build.issues, key=Issue.sort_key)),
        layer2_note=layer2_report.note,
    )


def _sorted_checks(
    checks: Iterable[tuple[str, str, str | None]]
) -> tuple[tuple[str, str, str | None], ...]:
    return tuple(sorted(checks, key=lambda item: (item[0], item[1], item[2] or "")))


def _resolve_grain_keyed(
    build: _Construction,
    accepted: AcceptedPackage,
    records: list[tuple[str, str, int, JsonObject]],
) -> tuple[list[CanonicalObjectSet], dict[str, tuple[CanonicalObject, ...]]]:
    """Group accepted evidence by canonical grain and resolve exactly-one-or-unresolved.

    **Stage A** (``§4.4.102`` C): exactly one applicable evidence resolves the grain;
    more than one applicable evidence stays unresolved and is never reconciled by a
    value comparison, a first/last-wins rule or any other unapproved precedence.
    """

    buckets: dict[str, dict[tuple[Any, ...], list[CanonicalObject]]] = {
        target: {} for target in GRAIN_KEYED_TARGET_ORDER
    }
    ungrainable: dict[str, list[CanonicalObject]] = {
        target: [] for target in GRAIN_KEYED_TARGET_ORDER
    }

    for role, artifact, ordinal, record in records:
        canonicalization_role = CANONICALIZATION_ROLE_BY_LITERAL[role]
        target = canonicalization_role.target

        if role == "Plant / Material identity context":
            _assign_identity_context(
                build, accepted, artifact, ordinal, record, buckets, ungrainable
            )
            continue

        if target not in buckets:
            # ``BOM Component`` / ``Inbound Supply`` carry their own identity
            # representation and are handled by their dedicated constructors.
            continue

        applicability = APPLICABILITY_BY_ROLE[role]
        properties, non_applicable = _properties_from(record, applicability.assignable)
        grain = _grain_tuple(record, GRAIN_KEYED_TARGETS[target])
        reference = _record_reference(
            package=accepted, role=role, artifact=artifact, ordinal=ordinal
        )
        provenance = _evidence_reference(
            package=accepted,
            role=role,
            artifact=artifact,
            ordinal=ordinal,
            record=record,
        )
        obj = CanonicalObject(
            canonical_target=target,
            canonicalization_role=role,
            grain=grain,
            properties=properties,
            non_applicable_properties=non_applicable,
            record_reference=reference.reference,
            provenance=provenance,
        )
        if grain is None:
            ungrainable[target].append(obj)
            build.check(
                f"{CANONICALIZATION_GRAIN_RESOLUTION}:{target}:{reference.reference}",
                EVALUATION_NOT_EVALUABLE,
                "a canonical identity component is not present on the accepted record; "
                "the object stays unresolved instead of receiving a default",
            )
            build.unresolved_identity(
                location=f"{artifact}[{ordinal}]",
                detail=(
                    f"{target} identity cannot be resolved: a registered canonical "
                    "identity component is not present on the accepted record"
                ),
                affected_evidence=artifact,
                design_reference="§4.4.26 / §4.4.94 / §4.1.3",
            )
            continue

        key = _grain_key(record, GRAIN_KEYED_TARGETS[target])
        if key is None:
            # An identity part is not present: the object stays unresolved and no
            # placeholder value is invented (``§4.4.26``).
            ungrainable[target].append(obj)
            build.check(
                f"{CANONICALIZATION_GRAIN_RESOLUTION}:{target}:{reference.reference}",
                EVALUATION_NOT_EVALUABLE,
                "a canonical identity component is not present on the accepted record; "
                "the object stays unresolved instead of receiving a default",
            )
            build.unresolved_identity(
                location=f"{artifact}[{ordinal}]",
                detail=(
                    f"{target} identity cannot be resolved: a registered canonical "
                    "identity component is not present on the accepted record"
                ),
                affected_evidence=artifact,
                design_reference="§4.4.26 / §4.4.94 / §4.1.3",
            )
            continue
        buckets[target].setdefault(key, []).append(obj)

    object_sets: list[CanonicalObjectSet] = []
    resolved_by_target: dict[str, tuple[CanonicalObject, ...]] = {}

    for target in GRAIN_KEYED_TARGET_ORDER:
        resolved: list[CanonicalObject] = []
        unresolved: list[CanonicalObject] = list(ungrainable[target])

        for key in sorted(buckets[target], key=lambda item: repr(item)):
            candidates = buckets[target][key]
            label = _grain_label(candidates[0].grain)
            if len(candidates) == 1:
                resolved.append(candidates[0])
                build.check(
                    f"{CANONICALIZATION_GRAIN_RESOLUTION}:{target}",
                    EVALUATION_PASSED,
                    f"exactly one applicable evidence for grain [{label}]",
                )
                continue

            unresolved.extend(candidates)
            build.check(
                f"{CANONICALIZATION_GRAIN_RESOLUTION}:{target}",
                EVALUATION_NOT_EVALUABLE,
                f"{len(candidates)} applicable evidence records share the same canonical "
                f"grain [{label}]; the grain stays unresolved and no precedence, "
                "aggregation or same-value deduplication is applied (§4.4.102 C)",
            )

        object_sets.append(
            CanonicalObjectSet(
                canonical_target=target,
                resolved=tuple(resolved),
                unresolved=tuple(unresolved),
            )
        )
        resolved_by_target[target] = tuple(resolved)

    return object_sets, resolved_by_target


def _assign_identity_context(
    build: _Construction,
    accepted: AcceptedPackage,
    artifact: str,
    ordinal: int,
    record: JsonObject,
    buckets: dict[str, dict[tuple[Any, ...], list[CanonicalObject]]],
    ungrainable: dict[str, list[CanonicalObject]],
) -> None:
    """Assign one ``Plant / Material identity context`` record to those identities.

    ``§4.3.31`` B assigns this role to entity **Plant** and entity **Material**
    (``§4.1.4`` A / B).  Each identity is resolved on its own grain, and the two are
    never merged into one composite object.
    """

    applicability = APPLICABILITY_BY_ROLE["Plant / Material identity context"]
    properties, non_applicable = _properties_from(record, applicability.assignable)
    reference = _record_reference(
        package=accepted, role="Plant / Material identity context", artifact=artifact,
        ordinal=ordinal,
    )
    provenance = _evidence_reference(
        package=accepted,
        role="Plant / Material identity context",
        artifact=artifact,
        ordinal=ordinal,
        record=record,
    )

    for key_name, target in IDENTITY_COMPONENT_TARGETS.items():
        grain = _grain_tuple(record, (key_name,))
        obj = CanonicalObject(
            canonical_target=target,
            canonicalization_role="Plant / Material identity context",
            grain=grain,
            properties=properties,
            non_applicable_properties=non_applicable,
            record_reference=reference.reference,
            provenance=provenance,
        )
        if grain is None:
            ungrainable[target].append(obj)
            build.check(
                f"{CANONICALIZATION_GRAIN_RESOLUTION}:{target}:{reference.reference}",
                EVALUATION_NOT_EVALUABLE,
                f"identity component {key_name!r} is not present on the accepted "
                "record; the identity stays unresolved instead of receiving a default",
            )
            continue
        buckets[target].setdefault((record[key_name],), []).append(obj)


def _construct_inbound(
    build: _Construction,
    accepted: AcceptedPackage,
    records: list[tuple[str, str, int, JsonObject]],
) -> list[CanonicalObject]:
    """G3-A Inbound Supply identity representation (``§4.3.31`` D / ``§4.1.13`` B).

    Each accepted ``Inbound Supply`` record becomes its own canonical instance whose
    identity representation is the AcceptedPackage-scoped technical record reference.
    Two content-identical records at different ordinals therefore remain distinct, and
    no content-derived deduplication happens.
    """

    applicability = APPLICABILITY_BY_ROLE[ROLE_INBOUND_SUPPLY]
    outbound: list[CanonicalObject] = []

    for role, artifact, ordinal, record in records:
        if role != ROLE_INBOUND_SUPPLY:
            continue
        properties, non_applicable = _properties_from(record, applicability.assignable)
        reference = _record_reference(
            package=accepted, role=role, artifact=artifact, ordinal=ordinal
        )
        provenance = _evidence_reference(
            package=accepted,
            role=role,
            artifact=artifact,
            ordinal=ordinal,
            record=record,
        )
        if "plant_id" not in record and "material_code" not in record:
            # ``§4.1.4`` E registers ``plant_id`` + ``material_code`` as the inbound
            # identity basis; without them the business identity is unresolved even
            # though the technical record reference itself stays deterministic.
            build.unresolved_identity(
                location=f"{artifact}[{ordinal}]",
                detail=(
                    "Inbound Supply record carries neither plant_id nor material_code; "
                    "the inbound identity stays unresolved (§4.1.4 E)"
                ),
                affected_evidence=artifact,
                design_reference="§4.1.4 E / §4.3.31 D (G3-A)",
            )
        outbound.append(
            CanonicalObject(
                canonical_target=ROLE_INBOUND_SUPPLY,
                canonicalization_role=ROLE_INBOUND_SUPPLY,
                grain=None,
                properties=properties,
                non_applicable_properties=non_applicable,
                record_reference=reference.reference,
                provenance=provenance,
            )
        )
        build.check(
            f"{CANONICALIZATION_INBOUND_IDENTITY}:{artifact}#{ordinal}",
            EVALUATION_PASSED,
            "AcceptedPackage identity + exact role 'Inbound Supply' + dataset-internal "
            "record ordinal over the accepted stable content view (§4.3.31 D)",
        )

    return outbound


def _construct_bom_components(
    build: _Construction,
    accepted: AcceptedPackage,
    records: list[tuple[str, str, int, JsonObject]],
    handoff: PhaseAHandoff,
    located: Mapping[str, tuple[str, int]],
    accepted_records: Mapping[str, JsonObject],
    production_requirements: tuple[CanonicalObject, ...],
) -> tuple[tuple[CanonicalObject, ...], tuple[CanonicalObject, ...]]:
    """G4-A BOM Component construction with a resolved parent context reference.

    ``material_code`` is the **component** material identity.  The parent / requirement
    context is a reference to an already constructed / resolved ``Production
    Requirement`` context (``plant_id`` + parent ``material_code`` + ``required_date``);
    a caller cannot create that context without accepted source evidence, and the
    binding's own provenance is preserved on the object rather than discarded.

    The constructed grain is the canonical one (``§4.1.13`` C):
    ``plant_id`` + parent ``material_code`` + ``required_date`` + component
    ``material_code``.  The parent ``material_code`` is read from the **resolved
    context**, never invented, and no ``parent_material_code`` canonical field is
    created.

    When the BOM record also carries ``plant_id`` / ``required_date`` they must be
    **exactly equal** to the referenced context, otherwise the registered
    ``CONSISTENCY`` / ``CONSISTENCY_CONFLICT`` finding is raised and no silent
    precedence is applied.
    """

    applicability = APPLICABILITY_BY_ROLE[ROLE_BOM_COMPONENT]

    parents: dict[tuple[Any, ...], list[tuple[CanonicalObject, EvidenceReference]]] = {}
    for entry in handoff.bom_parent_context:
        verification = _verify_handoff_evidence(
            accepted=accepted,
            evidence=entry.evidence,
            located=located,
            records=accepted_records,
            expected_roles=(ROLE_PRODUCTION_REQUIREMENT,),
        )
        if not verification.verified:
            build.check(
                f"{CANONICALIZATION_HANDOFF_EVIDENCE}:bom_parent_context",
                EVALUATION_NOT_EVALUABLE,
                verification.problem or "handoff evidence is not package-scoped",
            )
            continue
        reference = _record_reference(
            package=accepted,
            role=verification.role or ROLE_PRODUCTION_REQUIREMENT,
            artifact=verification.artifact or "",
            ordinal=verification.ordinal or 0,
        )
        parent = next(
            (
                item
                for item in production_requirements
                if item.record_reference == reference.reference
            ),
            None,
        )
        if parent is None:
            build.check(
                f"{CANONICALIZATION_HANDOFF_EVIDENCE}:bom_parent_context",
                EVALUATION_NOT_EVALUABLE,
                "the referenced Production Requirement context is not resolved, so it "
                "cannot serve as a BOM parent context (§4.1.13 C)",
            )
            continue
        parents.setdefault((entry.plant_id, entry.required_date), []).append(
            (parent, _resolved_evidence_reference(accepted=accepted, verification=verification))
        )

    # Package-level index used only to recognise a grain mismatch against a *unique*
    # resolved Production Requirement context of the same plant.  It never selects a
    # parent on its own: ambiguity always stays unresolved (``§4.4.102`` C).
    by_plant: dict[Any, list[CanonicalObject]] = {}
    for item in production_requirements:
        by_plant.setdefault(item.value_of("plant_id", ABSENT), []).append(item)

    resolved: list[CanonicalObject] = []
    unresolved: list[CanonicalObject] = []

    def _unresolved_object(
        properties: tuple[CanonicalProperty, ...],
        non_applicable: tuple[str, ...],
        reference: RecordReference,
        provenance: EvidenceReference,
    ) -> CanonicalObject:
        """A BOM Component whose parent / requirement context could not be bound.

        It keeps the record's assignable properties and its G3-A technical record
        reference, but carries no grain and no parent reference: no parent context is
        invented and no value is guessed (``§4.1.13`` C).
        """

        return CanonicalObject(
            canonical_target=ROLE_BOM_COMPONENT,
            canonicalization_role=ROLE_BOM_COMPONENT,
            grain=None,
            properties=properties,
            non_applicable_properties=non_applicable,
            record_reference=reference.reference,
            provenance=provenance,
        )

    for role, artifact, ordinal, record in records:
        if role != ROLE_BOM_COMPONENT:
            continue
        properties, non_applicable = _properties_from(record, applicability.assignable)
        reference = _record_reference(
            package=accepted, role=role, artifact=artifact, ordinal=ordinal
        )
        provenance = _evidence_reference(
            package=accepted,
            role=role,
            artifact=artifact,
            ordinal=ordinal,
            record=record,
        )

        record_plant = record["plant_id"] if "plant_id" in record else ABSENT
        record_required = (
            record["required_date"] if "required_date" in record else ABSENT
        )
        candidates = parents.get((record_plant, record_required), [])
        if record_plant is ABSENT or record_required is ABSENT:
            build.check(
                f"{CANONICALIZATION_BOM_PARENT}:{reference.reference}",
                EVALUATION_NOT_EVALUABLE,
                "the BOM evidence does not carry plant_id / required_date, so no BOM "
                "parent / requirement context can be bound from it; no parent context "
                "is created and no value is guessed (§4.1.13 C)",
            )
            build.unresolved_identity(
                location=f"{artifact}[{ordinal}]",
                detail=(
                    "BOM Component parent / requirement context cannot be bound: the "
                    "accepted evidence does not carry the grain key"
                ),
                affected_evidence=artifact,
                design_reference="§4.1.13 C / §4.3.31 G I-7",
            )
            unresolved.append(
                _unresolved_object(properties, non_applicable, reference, provenance)
            )
            continue

        if not candidates:
            # No parent context was handed in for this grain key.  A *unique* resolved
            # Production Requirement context of the same plant lets an exact-equality
            # violation be recognised as the registered ``CONSISTENCY`` finding instead
            # of being silently reported as "no parent".  Ambiguity (more than one
            # resolved requirement for the plant) never resolves here.
            same_plant = by_plant.get(record_plant, [])
            if len(same_plant) == 1:
                sole = same_plant[0]
                sole_required = sole.value_of("required_date", ABSENT)
                sole_plant = sole.value_of("plant_id", ABSENT)
                grain_agrees = sole_plant == record_plant and sole_required == record_required
                if not grain_agrees:
                    build.check(
                        f"{CANONICALIZATION_BOM_PARENT}:{reference.reference}",
                        EVALUATION_FAILED,
                        "BOM record grain values do not match the resolved Production "
                        "Requirement context of the same plant: "
                        f"plant_id record={record_plant!r} vs context={sole_plant!r}; "
                        f"required_date record={record_required!r} vs "
                        f"context={sole_required!r}",
                    )
                    build.issue(
                        category="CONSISTENCY",
                        reason="CONSISTENCY_CONFLICT",
                        location=f"{artifact}[{ordinal}]",
                        detail=(
                            "BOM Component record carries plant_id / required_date that "
                            "differ from the referenced Production Requirement context: "
                            f"plant_id record={record_plant!r} vs context={sole_plant!r}; "
                            f"required_date record={record_required!r} vs "
                            f"context={sole_required!r}"
                        ),
                        affected_evidence=artifact,
                        design_reference="§4.1.13 C (G4-A) / §4.4.102 C Stage B",
                        consequence_context=(
                            "the affected BOM Component relationship stays unresolved; "
                            "no silent precedence and no package rejection"
                        ),
                    )
                    unresolved.append(
                        _unresolved_object(
                            properties, non_applicable, reference, provenance
                        )
                    )
                    continue
                # The grain agrees but no package-scoped parent evidence was handed in:
                # the parent context still cannot be created from nothing (§4.1.13 C).
                build.check(
                    f"{CANONICALIZATION_BOM_PARENT}:{reference.reference}",
                    EVALUATION_NOT_EVALUABLE,
                    "a resolved Production Requirement context with the same grain "
                    "exists, but no accepted package-scoped parent evidence was handed "
                    "in; no parent context is created from nothing (§4.1.13 C)",
                )
                build.unresolved_identity(
                    location=f"{artifact}[{ordinal}]",
                    detail=(
                        "BOM Component parent / requirement context is unresolved: no "
                        "package-scoped parent / requirement context evidence was "
                        "provided (§4.3.31 G I-7)"
                    ),
                    affected_evidence=artifact,
                    design_reference="§4.1.13 C / §4.3.31 G I-7",
                )
                unresolved.append(
                    _unresolved_object(properties, non_applicable, reference, provenance)
                )
                continue

            build.check(
                f"{CANONICALIZATION_BOM_PARENT}:{reference.reference}",
                EVALUATION_NOT_EVALUABLE,
                "no resolved Production Requirement context is bound for "
                f"plant_id={record_plant!r} + required_date={record_required!r}; the "
                "parent stays unresolved and no parent context is invented "
                "(§4.1.13 C / §4.3.31 C)",
            )
            build.unresolved_identity(
                location=f"{artifact}[{ordinal}]",
                detail=(
                    "BOM Component parent / requirement context is unresolved: no "
                    "resolved Production Requirement context with exact match on "
                    "plant_id + required_date"
                ),
                affected_evidence=artifact,
                design_reference="§4.1.13 C / §4.3.31 G I-7",
            )
            unresolved.append(
                _unresolved_object(properties, non_applicable, reference, provenance)
            )
            continue

        distinct = {item[0].record_reference for item in candidates}
        if len(distinct) > 1:
            build.check(
                f"{CANONICALIZATION_BOM_PARENT}:{reference.reference}",
                EVALUATION_NOT_EVALUABLE,
                f"{len(distinct)} different resolved parent contexts were handed in for "
                "the same grain key; the binding stays unresolved and no precedence is "
                "applied (§4.4.102 C)",
            )
            unresolved.append(
                _unresolved_object(properties, non_applicable, reference, provenance)
            )
            continue

        parent, parent_evidence = candidates[0]
        parent_plant = parent.value_of("plant_id", ABSENT)
        parent_required = parent.value_of("required_date", ABSENT)

        mismatch: list[str] = []
        if record_plant is not ABSENT and parent_plant is not ABSENT:
            if record_plant != parent_plant:
                mismatch.append(
                    f"plant_id record={record_plant!r} vs context={parent_plant!r}"
                )
        if record_required is not ABSENT and parent_required is not ABSENT:
            if record_required != parent_required:
                mismatch.append(
                    "required_date record="
                    f"{record_required!r} vs context={parent_required!r}"
                )

        if mismatch:
            # ``§4.1.13`` C: an exact-equality violation is the registered
            # ``CONSISTENCY`` / ``CONSISTENCY_CONFLICT`` finding; no silent precedence.
            build.check(
                f"{CANONICALIZATION_BOM_PARENT}:{reference.reference}",
                EVALUATION_FAILED,
                "BOM record grain values do not match the referenced Production "
                f"Requirement context: {'; '.join(mismatch)}",
            )
            build.issue(
                category="CONSISTENCY",
                reason="CONSISTENCY_CONFLICT",
                location=f"{artifact}[{ordinal}]",
                detail=(
                    "BOM Component record carries plant_id / required_date that differ "
                    "from the referenced Production Requirement context: "
                    + "; ".join(mismatch)
                ),
                affected_evidence=artifact,
                design_reference="§4.1.13 C (G4-A) / §4.4.102 C Stage B",
                consequence_context=(
                    "the affected BOM Component relationship stays unresolved; no "
                    "silent precedence and no package rejection"
                ),
            )
            unresolved.append(
                _unresolved_object(properties, non_applicable, reference, provenance)
            )
            continue

        build.check(
            f"{CANONICALIZATION_BOM_PARENT}:{reference.reference}",
            EVALUATION_PASSED,
            "parent / requirement context bound to resolved Production Requirement "
            "context "
            f"[{_grain_label(parent.grain)}] via {parent_evidence.record_path}",
        )
        # ``§4.1.13`` C / ``§4.1.4`` N canonical semantic for this relationship is
        # ``resolved Production Requirement context`` + ``component material_code``.
        # It is represented structurally, without adding any canonical property:
        #
        #   * the resolved Production Requirement context (plant_id + parent
        #     material_code + required_date) is carried by ``context_reference`` /
        #     ``context_provenance`` below; and
        #   * the BOM-local grain below is the role's existing ``material_code``, which
        #     means the **component** material identity.
        #
        # Together those two parts are the effective BOM grain / identity.  No
        # ``component_material_code`` and no ``parent_material_code`` canonical field or
        # identity component is created.
        parent_material = parent.value_of("material_code", ABSENT)
        if parent_material is ABSENT:
            build.check(
                f"{CANONICALIZATION_BOM_PARENT}:{reference.reference}",
                EVALUATION_NOT_EVALUABLE,
                "the resolved Production Requirement context does not carry a "
                "material_code, so the BOM Component grain cannot be stated; the object "
                "stays unresolved instead of receiving a default (§4.1.13 C)",
            )
            build.unresolved_identity(
                location=f"{artifact}[{ordinal}]",
                detail=(
                    "BOM Component grain is incomplete: the resolved Production "
                    "Requirement context carries no parent material_code"
                ),
                affected_evidence=artifact,
                design_reference="§4.1.13 C / §4.4.26 / §4.4.94",
            )
            unresolved.append(
                _unresolved_object(properties, non_applicable, reference, provenance)
            )
            continue

        grain = (CanonicalProperty("material_code", record["material_code"]),)
        resolved.append(
            CanonicalObject(
                canonical_target=ROLE_BOM_COMPONENT,
                canonicalization_role=role,
                grain=grain,
                properties=properties,
                non_applicable_properties=non_applicable,
                record_reference=reference.reference,
                provenance=provenance,
                context_reference=parent.record_reference,
                context_provenance=parent.provenance,
            )
        )

    return tuple(resolved), tuple(unresolved)


def _handoff_loss_rate(
    build: _Construction,
    accepted: AcceptedPackage,
    located: Mapping[str, tuple[str, int]],
    accepted_records: Mapping[str, JsonObject],
    handoff: PhaseAHandoff,
    production_requirements: tuple[CanonicalObject, ...],
) -> None:
    """Resolve ``loss_rate`` + Requirement Calculation Context (injection I-2).

    ``loss_rate`` is never assigned by the ``Production Requirement`` record itself
    (``§4.2.18`` role 2).  A value is carried only when **all** of the following hold:

    * the requirement grain matches a resolved ``Production Requirement`` context;
    * the handoff cites exactly one applicable ``loss_rate`` record inside the **same**
      ``AcceptedPackage``, and that record registers a ``_meta.provenance_associations``
      entry for the ``loss_rate`` observation -- an unverifiable citation, or one
      without registered provenance, never supplies a value;
    * the resolution basis is the ``mapping_basis`` the accepted record itself registers;
      a caller-supplied free string is not an approved mapping basis.

    More than one applicable reference stays unresolved: values are never deduplicated,
    never aggregated and never chosen by precedence (``§4.4.102`` C Stage A).  The
    Entity / Dataset / Source Field ownership of ``loss_rate`` is **not** decided here
    (``§4.4.15``).
    """

    for index, entry in enumerate(handoff.loss_rate):
        check_name = f"{CANONICALIZATION_HANDOFF_EVIDENCE}:loss_rate[{index}]"
        grain = (
            CanonicalProperty("plant_id", entry.plant_id),
            CanonicalProperty("material_code", entry.parent_material_code),
            CanonicalProperty("required_date", entry.required_date),
        )

        matched = any(
            obj.value_of("plant_id", ABSENT) == entry.plant_id
            and obj.value_of("material_code", ABSENT) == entry.parent_material_code
            and obj.value_of("required_date", ABSENT) == entry.required_date
            for obj in production_requirements
        )
        if not matched:
            build.check(
                check_name,
                EVALUATION_NOT_EVALUABLE,
                "no resolved Production Requirement context matches the Requirement "
                "Calculation Context grain of this loss_rate handoff; the value is not "
                "carried (§4.1.13 E)",
            )
            continue

        gate = _verify_handoff_evidence(
            accepted=accepted,
            evidence=entry.evidence,
            located=located,
            records=accepted_records,
        )
        if not gate.verified:
            build.check(
                check_name,
                EVALUATION_NOT_EVALUABLE,
                gate.problem or "loss_rate resolution evidence is not package-scoped",
            )
            continue

        if len(entry.loss_rate_evidence) != 1:
            build.check(
                check_name,
                EVALUATION_NOT_EVALUABLE,
                "the Requirement Calculation Context resolution used "
                f"{len(entry.loss_rate_evidence)} applicable loss_rate reference(s); "
                "exactly one applicable reference is required and equal values are "
                "never deduplicated, so the value stays unresolved (§4.4.15 / "
                "§4.4.102 C Stage A)",
            )
            continue

        value_gate = _verify_handoff_evidence(
            accepted=accepted,
            evidence=entry.loss_rate_evidence[0],
            located=located,
            records=accepted_records,
            observation="loss_rate",
        )
        if not value_gate.verified:
            build.check(
                check_name,
                EVALUATION_NOT_EVALUABLE,
                value_gate.problem
                or "the cited loss_rate evidence is not verifiable in this package",
            )
            continue

        # The basis must be the one the accepted record itself registers: a caller's
        # free string is not an approved mapping basis (§4.3.28 E / §4.5.22 Option D).
        accepted_basis = (
            value_gate.association.mapping_basis
            if value_gate.association is not None
            else None
        )
        if not accepted_basis:
            build.check(
                check_name,
                EVALUATION_NOT_EVALUABLE,
                "the accepted record registers no \"mapping_basis\" for the loss_rate "
                "association, so the resolution basis cannot be tied to approved "
                "package evidence; the value is not carried (§4.3.28 E)",
            )
            continue
        if entry.resolution_basis and entry.resolution_basis != accepted_basis:
            build.check(
                check_name,
                EVALUATION_NOT_EVALUABLE,
                "the handed-in resolution basis does not equal the mapping_basis the "
                "accepted record registers; a caller free string is not an approved "
                "mapping basis (§4.3.28 E)",
            )
            continue

        if value_gate.value != entry.loss_rate:
            build.check(
                check_name,
                EVALUATION_NOT_EVALUABLE,
                "the handed-in loss_rate does not equal the value carried by the cited "
                "accepted evidence; a caller may not supply a value the evidence does "
                "not support (§4.3.31 E)",
            )
            continue

        build.check(
            check_name,
            EVALUATION_PASSED,
            "loss_rate carried as an in-process logical handoff, supported by accepted "
            f"record {value_gate.record_path} with registered provenance and basis "
            f"{accepted_basis!r}; Entity / Dataset / Source Field ownership is not "
            "decided here (§4.4.15)",
        )
        build.loss_rate_contexts.append(
            ContextValueReference(
                semantic="loss_rate",
                grain=grain,
                value=value_gate.value,
                provenance=_resolved_evidence_reference(
                    accepted=accepted, verification=value_gate
                ),
            )
        )


def _handoff_safety_stock(
    build: _Construction,
    accepted: AcceptedPackage,
    located: Mapping[str, tuple[str, int]],
    accepted_records: Mapping[str, JsonObject],
    handoff: PhaseAHandoff,
    safety_stock_targets: tuple[CanonicalObject, ...],
) -> None:
    """Resolve the ``SafetyStock`` internal handoff (injection I-5).

    Two obligations are implemented here, in this order:

    * **Stage B over accepted evidence (handoff-independent).**  Two accepted
      ``Configured Safety Stock`` records that state different ``SafetyStock`` values on
      the same ``plant_id`` + ``material_code`` grain are the registered ``§4.4.92``
      case and are reported as ``CONSISTENCY`` / ``CONSISTENCY_CONFLICT``
      (``§4.4.102`` C Stage B) whether or not any handoff entry exists -- generic
      duplicate handling never downgrades or overrides it.
    * **Internal handoff.**  A value is carried only when the same ``AcceptedPackage``
      resolves the grain through exactly one applicable record whose registered
      provenance states the ``SafetyStock`` observation, whose own ``plant_id`` /
      ``material_code`` equal the claimed grain, and no conflicting accepted value
      exists at that grain.  A handoff can therefore neither invent a value nor shadow
      accepted evidence (no implicit ``injection wins``).
    """

    grains_stated_by_configured_dataset = _configured_safety_stock_grains(
        accepted, accepted_records
    )
    conflicting_grains = _report_safety_stock_grain_conflicts(
        build, accepted, accepted_records
    )

    for index, entry in enumerate(handoff.safety_stock):
        check_name = f"{CANONICALIZATION_HANDOFF_EVIDENCE}:SafetyStock[{index}]"
        grain = (
            CanonicalProperty("plant_id", entry.plant_id),
            CanonicalProperty("material_code", entry.material_code),
        )
        grain_label = f"plant_id={entry.plant_id!r} + material_code={entry.material_code!r}"

        gate = _verify_handoff_evidence(
            accepted=accepted,
            evidence=entry.evidence,
            located=located,
            records=accepted_records,
        )
        if not gate.verified:
            build.check(
                check_name,
                EVALUATION_NOT_EVALUABLE,
                gate.problem or "SafetyStock resolution evidence is not package-scoped",
            )
            continue

        if (entry.plant_id, entry.material_code) in grains_stated_by_configured_dataset:
            build.check(
                check_name,
                EVALUATION_NOT_EVALUABLE,
                "the Configured Safety Stock dataset itself states this grain, so the "
                "internal handoff is not used and no precedence between the two sources "
                "is applied (§4.4.102 C Stage B)",
            )
            continue

        if (entry.plant_id, entry.material_code) in conflicting_grains:
            build.check(
                check_name,
                EVALUATION_NOT_EVALUABLE,
                "conflicting accepted SafetyStock values were reported for this grain; "
                "the handoff may not resolve the conflict and no value is carried "
                "(§4.4.92 / §4.4.102 C Stage B)",
            )
            continue

        # Accepted Configured Safety Stock evidence for this grain, verified in-package.
        competing: list[_EvidenceVerification] = []
        competing_ok = True
        for citation in entry.configured_safety_stock_evidence:
            verification = _verify_handoff_evidence(
                accepted=accepted,
                evidence=citation,
                located=located,
                records=accepted_records,
                expected_roles=(ROLE_CONFIGURED_SAFETY_STOCK,),
                observation="SafetyStock",
            )
            if not verification.verified:
                build.check(
                    check_name,
                    EVALUATION_NOT_EVALUABLE,
                    verification.problem
                    or "Configured Safety Stock evidence is not verifiable in this package",
                )
                competing_ok = False
                break
            competing.append(verification)
        if not competing_ok:
            continue

        if len(entry.safety_stock_evidence) != 1:
            build.check(
                check_name,
                EVALUATION_NOT_EVALUABLE,
                "the SafetyStock resolution used "
                f"{len(entry.safety_stock_evidence)} applicable evidence reference(s); "
                "exactly one applicable reference is required, so the value stays "
                "unresolved and is never defaulted (§4.3.31 E / I-5)",
            )
            continue

        value_gate = _verify_handoff_evidence(
            accepted=accepted,
            evidence=entry.safety_stock_evidence[0],
            located=located,
            records=accepted_records,
            observation="SafetyStock",
        )
        if not value_gate.verified:
            build.check(
                check_name,
                EVALUATION_NOT_EVALUABLE,
                value_gate.problem
                or "the cited SafetyStock evidence is not verifiable in this package",
            )
            continue

        # The cited evidence must state the very grain the handoff claims: evidence for
        # another plant / material may not support this context.
        evidence_grain = _safety_stock_record_grain(accepted_records, value_gate.record_path)
        if evidence_grain != (entry.plant_id, entry.material_code):
            build.check(
                check_name,
                EVALUATION_NOT_EVALUABLE,
                "the cited SafetyStock evidence states grain "
                f"{evidence_grain!r} which is not the claimed grain "
                f"[{grain_label}]; evidence for another grain may not support this "
                "context (§4.1.4 O / §4.4.92)",
            )
            continue

        # The basis must be the one the accepted record itself registers: a caller's
        # free string is not an approved mapping basis (§4.3.28 E / §4.5.22 Option D).
        accepted_basis = (
            value_gate.association.mapping_basis
            if value_gate.association is not None
            else None
        )
        if not accepted_basis:
            build.check(
                check_name,
                EVALUATION_NOT_EVALUABLE,
                "the accepted record registers no \"mapping_basis\" for the SafetyStock "
                "association, so the resolution basis cannot be tied to approved "
                "package evidence; the value is not carried (§4.3.28 E)",
            )
            continue
        if entry.resolution_basis and entry.resolution_basis != accepted_basis:
            build.check(
                check_name,
                EVALUATION_NOT_EVALUABLE,
                "the handed-in resolution basis does not equal the mapping_basis the "
                "accepted record registers; a caller free string is not an approved "
                "mapping basis (§4.3.28 E)",
            )
            continue

        # Stage B: conflicting SafetyStock values at the same canonical grain.
        conflicting = [
            verification
            for verification in competing
            if verification.value != value_gate.value
        ]
        if conflicting:
            detail = (
                "conflicting SafetyStock values at the same canonical grain "
                f"[{grain_label}]: "
                f"Configured Safety Stock evidence "
                f"{', '.join(f'{item.record_path}={item.value!r}' for item in competing)} "
                f"vs resolved policy evidence "
                f"{value_gate.record_path}={value_gate.value!r}"
            )
            build.check(
                check_name,
                EVALUATION_FAILED,
                detail,
            )
            build.issue(
                category="CONSISTENCY",
                reason="CONSISTENCY_CONFLICT",
                location=f"{value_gate.record_path}",
                detail=detail,
                affected_evidence=value_gate.artifact or "SafetyStock",
                design_reference="§4.4.92 / §4.4.102 C Stage B",
                consequence_context=(
                    "the affected SafetyStock grain stays unresolved; no precedence, no "
                    "aggregation and no package rejection"
                ),
            )
            continue

        if value_gate.value != entry.safety_stock:
            build.check(
                check_name,
                EVALUATION_NOT_EVALUABLE,
                "the handed-in SafetyStock does not equal the value carried by the cited "
                "accepted evidence; a caller may not supply a value the evidence does "
                "not support (§4.3.31 E)",
            )
            continue

        build.check(
            check_name,
            EVALUATION_PASSED,
            "SafetyStock carried as an in-process logical handoff, supported by accepted "
            f"record {value_gate.record_path} with registered provenance and basis "
            f"{accepted_basis!r}; no default of 0 is applied",
        )
        build.safety_stock_contexts.append(
            ContextValueReference(
                semantic="SafetyStock",
                grain=grain,
                value=value_gate.value,
                provenance=_resolved_evidence_reference(
                    accepted=accepted, verification=value_gate
                ),
            )
        )


def _safety_stock_record_grain(
    accepted_records: Mapping[str, JsonObject], record_path: str
) -> tuple[Any, Any] | None:
    """The ``plant_id`` + ``material_code`` grain an accepted record itself states."""

    record = accepted_records.get(record_path)
    if record is None:
        return None
    if "plant_id" not in record or "material_code" not in record:
        return None
    return (record["plant_id"], record["material_code"])


def _configured_safety_stock_grains(
    accepted: AcceptedPackage, accepted_records: Mapping[str, JsonObject]
) -> set[tuple[Any, Any]]:
    """Grains the accepted ``Configured Safety Stock`` dataset itself states."""

    grains: set[tuple[Any, Any]] = set()
    for role, artifact in accepted.datasets():
        if role != ROLE_CONFIGURED_SAFETY_STOCK:
            continue
        for path, record in accepted_records.items():
            if not path.startswith(f"{artifact}#"):
                continue
            grain = _safety_stock_record_grain(accepted_records, path)
            if grain is not None:
                grains.add(grain)
    return grains


def _report_safety_stock_grain_conflicts(
    build: _Construction,
    accepted: AcceptedPackage,
    accepted_records: Mapping[str, JsonObject],
) -> set[tuple[Any, Any]]:
    """Report ``§4.4.92`` conflicting SafetyStock at one grain, handoff-independent.

    Two accepted ``Configured Safety Stock`` records that state different
    ``SafetyStock`` values on the same ``plant_id`` + ``material_code`` grain violate the
    registered consistency invariant, so they are reported as ``CONSISTENCY`` /
    ``CONSISTENCY_CONFLICT`` (``§4.4.102`` C Stage B).  This runs over the accepted
    content view alone, with or without any handoff entry; the generic "more than one
    applicable evidence" handling never downgrades it.
    """

    per_grain: dict[tuple[Any, Any], list[tuple[str, Any]]] = {}
    for role, artifact in accepted.datasets():
        if role != ROLE_CONFIGURED_SAFETY_STOCK:
            continue
        for path, record in accepted_records.items():
            if not path.startswith(f"{artifact}#"):
                continue
            if "SafetyStock" not in record:
                continue
            grain = _safety_stock_record_grain(accepted_records, path)
            if grain is None:
                continue
            per_grain.setdefault(grain, []).append((path, record["SafetyStock"]))

    conflicting: set[tuple[Any, Any]] = set()
    for grain in sorted(per_grain, key=lambda item: repr(item)):
        values = per_grain[grain]
        distinct = {repr(value) for _path, value in values}
        if len(distinct) < 2:
            continue
        conflicting.add(grain)
        detail = (
            "conflicting SafetyStock values at the same canonical grain "
            f"[plant_id={grain[0]!r} + material_code={grain[1]!r}]: "
            + ", ".join(f"{path}={value!r}" for path, value in values)
        )
        build.check(
            f"{CANONICALIZATION_HANDOFF_EVIDENCE}:SafetyStock:grain_conflict",
            EVALUATION_FAILED,
            detail,
        )
        build.issue(
            category="CONSISTENCY",
            reason="CONSISTENCY_CONFLICT",
            location=f"{values[0][0]}",
            detail=detail,
            affected_evidence=ROLE_CONFIGURED_SAFETY_STOCK,
            design_reference="§4.4.92 / §4.4.102 C Stage B",
            consequence_context=(
                "the affected SafetyStock grain stays unresolved; no precedence, no "
                "aggregation and no package rejection"
            ),
        )
    return conflicting


# --- G5-A effective demand relation outcomes ---------------------------------------


def build_effective_demand_contexts(
    accepted: AcceptedPackage,
    handoff: PhaseAHandoff,
    *,
    located: Mapping[str, tuple[str, int]] | None = None,
) -> tuple[tuple[EffectiveDemandContextReference, ...], tuple[Issue, ...]]:
    """Return the G5-A read-only effective demand context references.

    Each reference keeps ``Target Applicability`` and ``Source Reservation Overlap`` as
    **two independent** relation outcomes, each with its own provenance and mapping
    basis.  A caller can never state an outcome.

    Phase A currently emits **no** context: the concrete source value -> approved
    conceptual outcome mapping is ``SOURCE-SPECIFIC`` / Adapter-defined and no approved
    mapping is available, so every relation is reported ``unresolved``
    (``SEMANTIC_RESOLUTION`` / ``SEMANTIC_UNRESOLVED``) instead of being relabelled,
    guessed or replaced by a supplied Boolean.
    """

    if located is None:
        located, _ = _targets_by_artifact(accepted)
    return _effective_demand_references(
        accepted, handoff, located, _accepted_record_index(accepted)
    )


def _effective_demand_references(
    accepted: AcceptedPackage,
    handoff: PhaseAHandoff,
    located: Mapping[str, tuple[str, int]],
    accepted_records: Mapping[str, JsonObject],
) -> tuple[tuple[EffectiveDemandContextReference, ...], tuple[Issue, ...]]:
    """Report the G5-A relation evidence status and the unresolved boundary.

    Per ``§4.3.31`` G I-8 the cardinality is *exactly one pair or unresolved*.  Phase A
    emits no pair at all: the concrete source value -> approved conceptual outcome
    mapping is ``SOURCE-SPECIFIC`` / Adapter-defined and is not registered in the
    current authority, so the conceptual outcome of every relation stays
    ``unresolved``.  Incoming entries are still checked against the accepted content
    view, so the report distinguishes "evidence not verifiable in this package" from
    "evidence verified, but the outcome cannot be formed without the deferred mapping".
    Nothing is relabelled from a registered canonical value and nothing is taken from
    the caller.
    """

    issues: list[Issue] = []
    seen_pairs: dict[tuple[Any, Any], set[str]] = {}

    def _unresolved(*, role: str, detail: str) -> None:
        issues.append(
            Issue(
                location="effective_demand_context",
                detail=detail,
                category="SEMANTIC_RESOLUTION",
                reason="SEMANTIC_UNRESOLVED",
                layer=LAYER_2,
                affected_evidence=role,
                blast_radius="affected effective demand context only",
                design_reference="§4.1.13 D (G5-A) / §4.3.31 G I-8",
                consequence_context=(
                    "the relation pair stays unresolved; a caller may not set the "
                    "outcome directly and no Boolean is synthesised"
                ),
            )
        )

    for entry in handoff.effective_demand:
        key = (entry.source_substitute_material, entry.target_material)
        seen_pairs.setdefault(key, set()).add(entry.relation)

        if entry.relation not in G5_RELATIONS:
            _unresolved(
                role=entry.evidence.logical_dataset_role,
                detail=(
                    f"relation {entry.relation!r} is not one of the registered G5-A "
                    f"relations {list(G5_RELATIONS)}; the pair stays unresolved"
                ),
            )
            continue

        verification = _verify_handoff_evidence(
            accepted=accepted,
            evidence=entry.evidence,
            located=located,
            records=accepted_records,
            expected_roles=(ROLE_SUBSTITUTE_ALLOCATION, ROLE_SUBSTITUTE_RELATIONSHIP),
        )
        if not verification.verified:
            _unresolved(
                role=entry.evidence.logical_dataset_role,
                detail=(
                    verification.problem
                    or "the cited mapping evidence is not verifiable in this package"
                ),
            )
            continue

        # Verified, in-package evidence.  The outcome is still not formed here: the
        # approved outcomes are ``applicable`` / ``not applicable`` / ``unresolved`` and
        # ``overlaps`` / ``does not overlap`` / ``unresolved``; the concrete source value
        # -> conceptual outcome mapping is SOURCE-SPECIFIC / Adapter-defined
        # (``§4.5.9`` / ``§4.5.26``) and is not registered.  A registered canonical value
        # such as ``approval_status`` or ``AllocatedSubstituteQty`` is therefore *not*
        # itself a relation outcome and is never relabelled as one.
        _unresolved(
            role=entry.evidence.logical_dataset_role,
            detail=(
                f"the accepted evidence {verification.record_path} supports relation "
                f"{entry.relation!r} but no approved source-value -> "
                "applicable / not applicable / overlaps / does not overlap mapping is "
                "available in the current authority (SOURCE-SPECIFIC / Adapter-defined); "
                "the conceptual outcome stays unresolved and is never taken from the "
                "caller nor invented by canonicalization (§4.1.13 D)"
            ),
        )

    for key in sorted(seen_pairs, key=lambda item: repr(item)):
        seen = seen_pairs[key]
        missing = [name for name in G5_RELATIONS if name not in seen]
        if not missing:
            continue
        issues.append(
            Issue(
                location="effective_demand_context",
                detail=(
                    f"relation(s) {missing} carry no mapping evidence for substitute/"
                    f"target pair {key!r}; the pair stays unresolved (exactly one pair or "
                    "unresolved, §4.3.31 G I-8)"
                ),
                category="SEMANTIC_RESOLUTION",
                reason="SEMANTIC_UNRESOLVED",
                layer=LAYER_2,
                affected_evidence="Substitute Allocation",
                blast_radius="affected effective demand context only",
                design_reference="§4.1.13 D (G5-A) / §4.3.31 G I-8",
                consequence_context=(
                    "the relation pair stays unresolved; Target Applicability and Source "
                    "Reservation Overlap are never collapsed into one Boolean"
                ),
            )
        )

    # ``§4.1.13`` D / ``§4.3.31`` G I-8: no effective demand context is produced in
    # Phase A while the source-specific mapping is unavailable.
    return (), tuple(issues)


__all__ = [
    "ABSENT",
    "APPLICABILITY_BY_ROLE",
    "AnalysisRunContext",
    "BomParentContextHandoff",
    "CANONICALIZATION_APPLICABILITY",
    "CANONICALIZATION_ANALYSIS_RUN",
    "CANONICALIZATION_BOM_PARENT",
    "CANONICALIZATION_EFFECTIVE_DEMAND",
    "CANONICALIZATION_GRAIN_RESOLUTION",
    "CANONICALIZATION_HANDOFF_EVIDENCE",
    "CANONICALIZATION_INBOUND_IDENTITY",
    "CANONICALIZATION_ROLES",
    "CANONICALIZATION_ROLE_BY_LITERAL",
    "CANONICALIZATION_ROLE_RECOGNITION",
    "CANONICALIZATION_TARGET_ASSIGNMENT",
    "CanonicalConstructionReport",
    "CanonicalObject",
    "CanonicalObjectSet",
    "CanonicalProperty",
    "CanonicalizationRole",
    "ContextValueReference",
    "EffectiveDemandContextReference",
    "EffectiveDemandRelationHandoff",
    "EvidenceReference",
    "G5_RELATIONS",
    "GRAIN_KEYED_TARGETS",
    "HandoffEvidence",
    "IDENTITY_COMPONENT_TARGETS",
    "LAYER2_REPORT_BINDING",
    "LossRateHandoff",
    "PHASE_A_ROLE_LITERALS",
    "PhaseAHandoff",
    "RELATION_SOURCE_RESERVATION_OVERLAP",
    "RELATION_TARGET_APPLICABILITY",
    "ROLE_BOM_COMPONENT",
    "ROLE_INBOUND_SUPPLY",
    "ROLE_PRODUCTION_REQUIREMENT",
    "ROLE_SUBSTITUTE_ALLOCATION",
    "ROLE_SUBSTITUTE_RELATIONSHIP",
    "RecordReference",
    "RelationOutcomeReference",
    "RoleApplicability",
    "SafetyStockHandoff",
    "build_effective_demand_contexts",
    "construct_canonical_objects",
]
