"""``BR-INVENTORY-001`` -- Available Inventory / Safety Stock (``§2.2``).

``OpeningUsableInventory`` is the eligible on-hand inventory of **one exact Plant-level
grain** (``§2.2.1``)::

    plant_id + material_code + inventory_snapshot_time

It aggregates only observations that satisfy **all** of (``§2.2.2`` ／ ``§2.2.4``):

1. the I-9 runtime seam resolved the record as **in** the current POC Inventory Scope;
2. ``inventory_status`` is the eligible ``AVAILABLE`` state (``§2.2.3``);
3. ``on_hand_qty`` is a valid non-negative canonical exact quantity (``§2.2.8``).

``SafetyStock`` (grain ``plant_id`` + ``material_code``, ``§2.2.5``) is an **independent**
classification threshold for ``BR-SHORTAGE-001``: it is *never* subtracted from the
inventory sum (``§2.2.7``), and this rule produces no
``NetInventoryAfterSafetyStock``-style derived concept.

Canonical authority implemented:

* ``poc-design-v0.2.md`` §2.2 (``BR-INVENTORY-001``, ``DESIGN RESOLVED`` /
  Human-approved): calculation grain, ``OpeningUsableInventory``, status eligibility,
  warehouse aggregation restricted to the current POC Inventory Scope, ``SafetyStock``
  baseline and zero-vs-missing, the no-double-counting relation, negative inventory,
  the ``§2.2.9`` data-quality safety rule, the acceptance examples and the AI boundary.
* ``data-dictionary.md`` §4.2.5 (inventory field rules) ／ §4.2.10 (``OpeningUsableInventory``
  is ``DERIVED``; missing behaviour is ``DATA_INCOMPLETE``).
* ``data-validation.md`` §4.4.12 ／ §4.4.50 (several Inventory observations may legally share
  one Plant-level grain; numeric inventory calculation requires a completed scope
  resolution), §4.4.80 ／ §4.4.81 (the inherited taxonomy -- no new vocabulary).
* ``canonical-data-model.md`` §4.1.4 D and ``master-data-mapping.md`` §4.5.12 (Warehouse is
  source ／ mapping ／ scope context only).
* ``adr-001-deterministic-core.md``: in-memory, standard-library-first, canonical exact
  numeric semantics; the exact finite-decimal machinery is shared with ``BR-INBOUND-001``
  (``snapshot_loader.exact_quantity``).

Input boundary: the rule consumes the already constructed
:class:`~snapshot_loader.canonical_objects.CanonicalConstructionReport` only --
``objects_for`` ／ ``unresolved_for("Inventory Snapshot")``, the I-9
``inventory_scope_contexts`` ／ ``inventory_scope_for()``, the resolved ``Configured Safety
Stock`` canonical objects (``§4.1.4 O`` -- the registered carrier of the configured value)
and ``safety_stock_contexts`` (the I-5 injected policy context).  It never re-reads a raw
snapshot artifact, never re-resolves a Warehouse, never re-runs source mapping, never infers
scope from a dataset role or a Warehouse name, never reads ``_meta`` itself, and never
creates a ``warehouse_id`` or any new canonical field.

``SafetyStock`` is resolved from **exactly one** candidate across both surfaces; the two are
never merged and no precedence is applied (``§4.4.102`` C): the seam already refuses the I-5
handoff when the ``Configured Safety Stock`` dataset itself states the grain, so a report
that still offers both leaves the value unresolved rather than picking one.

Deliberately **not** implemented here: ``ProjectedAvailable`` ／ ``Classification`` ／
``ShortageQty`` ／ ``BufferGap`` ／ ``FirstShortageDate`` (``BR-SHORTAGE-001``),
``BR-SUBSTITUTE-001``, ``BR-PROCUREMENT-001``, supplier risk, any Adapter ／ ERP mapping, any
persistence and any quantity precision ／ rounding policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .canonical_objects import (
    ABSENT,
    ROLE_INVENTORY_SNAPSHOT,
    TARGET_INVENTORY_SNAPSHOT,
    CanonicalConstructionReport,
    CanonicalObject,
    EvidenceReference,
)
from .constants import (
    CATEGORY_FIELD_VALUE,
    CATEGORY_IDENTITY_RESOLUTION,
    CATEGORY_SCOPE_COVERAGE,
    LAYER_2,
    REASON_INVALID_DEFINED_STATUS,
    REASON_INVALID_TYPE,
    REASON_MISSING,
    REASON_OUT_OF_DEFINED_RANGE,
    REASON_UNRESOLVED_IDENTITY,
    REASON_UNRESOLVED_SCOPE,
)
from .exact_quantity import ExactQuantity, parse_exact_quantity
from .issues import Issue
from .requirement_calculation import OUTCOME_DATA_INCOMPLETE

# --- vocabulary --------------------------------------------------------------------

#: The rule identity this module implements.
INVENTORY_RULE_ID: str = "BR-INVENTORY-001"

#: The only inventory status that contributes (``§2.2.3`` A).
ELIGIBLE_INVENTORY_STATUSES: frozenset[str] = frozenset({"AVAILABLE"})

#: Valid but ineligible statuses: they contribute ``0`` and are **not** a defect
#: (``§2.2.3`` B ／ C).  ``INSPECTION`` is not released by quality; ``FROZEN`` is not
#: available for shortage coverage.
INELIGIBLE_INVENTORY_STATUSES: frozenset[str] = frozenset({"INSPECTION", "FROZEN"})

#: The registered inventory status vocabulary (``§4.2.14``).  Unknown ／ invalid ／ missing
#: status is never mapped onto ``AVAILABLE`` and never silently treated as ``0``.
REGISTERED_INVENTORY_STATUSES: frozenset[str] = (
    ELIGIBLE_INVENTORY_STATUSES | INELIGIBLE_INVENTORY_STATUSES
)

#: The registered failure outcome used by this rule.  It is the same canonical
#: ``DATA_INCOMPLETE`` business outcome; this module exposes it under an
#: inventory-specific name so both rule modules can re-export it without colliding.  No new
#: outcome vocabulary is created.
INVENTORY_DATA_INCOMPLETE: str = OUTCOME_DATA_INCOMPLETE

#: Runtime scope states of one inventory observation, for trace only.  ``IN_SCOPE`` ／
#: ``OUT_OF_SCOPE`` are the I-9 registry's own membership literals; the unresolved state is
#: a runtime trace label, not a canonical vocabulary.
SCOPE_STATE_IN_SCOPE: str = "IN_SCOPE"
SCOPE_STATE_OUT_OF_SCOPE: str = "OUT_OF_SCOPE"
SCOPE_STATE_UNRESOLVED: str = "SCOPE_UNRESOLVED"

#: Why an inventory observation contributed ``0`` although it is *valid*.  The three cases
#: stay distinguishable in the trace: an out-of-scope record, an ``INSPECTION`` record and a
#: ``FROZEN`` record all contribute ``0`` but for three different registered reasons.
EXCLUSION_OUT_OF_SCOPE: str = "OUT_OF_SCOPE"
EXCLUSION_INSPECTION: str = "INSPECTION"
EXCLUSION_FROZEN: str = "FROZEN"


# --- result representation ---------------------------------------------------------


@dataclass(frozen=True, slots=True)
class InventoryEvaluation:
    """One Inventory observation evaluated against one exact Plant-level grain.

    ``scope_state`` ／ ``in_scope`` ／ ``ownership_resolved`` mirror the I-9 runtime context
    the evaluation consumed -- the rule never re-derives scope or ownership.  ``contribution``
    is the exact quantity this observation adds to the target (``0`` for a *valid* record
    that is out of scope or in an ineligible status) and is ``None`` when the observation is
    unreliable.  ``exclusion_reason`` keeps the three valid non-contributing cases apart.
    """

    target_plant_id: Any
    target_material_code: Any
    target_inventory_snapshot_time: Any
    inventory_reference: str
    inventory_role: str
    scope_present: bool
    scope_resolved: bool
    ownership_resolved: bool
    in_scope: bool | None
    scope_state: str
    scope_observation: Any = None
    scope_mapping_basis: Any = None
    inventory_status: Any = None
    on_hand_qty: ExactQuantity | None = None
    eligible_on_hand_qty: ExactQuantity | None = None
    contribution: ExactQuantity | None = None
    exclusion_reason: str | None = None
    outcome: str | None = None
    notes: tuple[str, ...] = ()
    provenance: EvidenceReference | None = None
    scope_provenance: EvidenceReference | None = None
    inherited_issues: tuple[Issue, ...] = ()
    rule_issues: tuple[Issue, ...] = ()

    @property
    def data_incomplete(self) -> bool:
        return self.outcome == INVENTORY_DATA_INCOMPLETE

    @property
    def contributes(self) -> bool:
        """Whether this observation adds eligible inventory at the target grain."""

        return (
            self.outcome is None
            and self.contribution is not None
            and self.contribution > ExactQuantity(0, 0)
        )

    @property
    def issues(self) -> tuple[Issue, ...]:
        return _deduplicate_issues(self.inherited_issues + self.rule_issues)

    def to_dict(self) -> dict[str, object]:
        return {
            "rule": INVENTORY_RULE_ID,
            "target": {
                "plant_id": self.target_plant_id,
                "material_code": self.target_material_code,
                "inventory_snapshot_time": self.target_inventory_snapshot_time,
            },
            "inventory_reference": self.inventory_reference,
            "inventory_role": self.inventory_role,
            "scope_present": self.scope_present,
            "scope_resolved": self.scope_resolved,
            "ownership_resolved": self.ownership_resolved,
            "in_scope": self.in_scope,
            "scope_state": self.scope_state,
            "scope_observation": self.scope_observation,
            "scope_mapping_basis": self.scope_mapping_basis,
            "inventory_status": self.inventory_status,
            "on_hand_qty": _quantity_text(self.on_hand_qty),
            "EligibleOnHandQty": _quantity_text(self.eligible_on_hand_qty),
            "contribution": _quantity_text(self.contribution),
            "exclusion_reason": self.exclusion_reason,
            "outcome": self.outcome,
            "notes": list(self.notes),
            "provenance": _provenance_payload(self.provenance),
            "scope_provenance": _provenance_payload(self.scope_provenance),
            "inherited_issues": [issue.to_dict() for issue in self.inherited_issues],
            "rule_issues": [issue.to_dict() for issue in self.rule_issues],
        }


@dataclass(frozen=True, slots=True)
class InventoryTarget:
    """The exact Plant-level grain: ``plant_id`` + ``material_code`` + ``inventory_snapshot_time``.

    ``opening_usable_inventory`` is ``None`` when the **inventory side** of the target is
    unreliable (scope ／ ownership ／ status ／ ``on_hand_qty``); ``safety_stock`` is ``None``
    when the **SafetyStock side** is unreliable (missing ／ invalid ／ negative ／ more than one
    reliable value).  ``outcome`` is ``DATA_INCOMPLETE`` when either side is unreliable -- the
    two independent inputs are reported separately (``§2.2.7`` ／ ``§2.2.9``) and a partial
    success never becomes a normal numeric result.
    """

    plant_id: Any
    material_code: Any
    inventory_snapshot_time: Any
    evaluations: tuple[InventoryEvaluation, ...]
    opening_usable_inventory: ExactQuantity | None
    safety_stock: ExactQuantity | None
    outcome: str | None = None
    safety_stock_provenance: EvidenceReference | None = None
    notes: tuple[str, ...] = ()
    inherited_issues: tuple[Issue, ...] = ()
    rule_issues: tuple[Issue, ...] = ()

    @property
    def data_incomplete(self) -> bool:
        return self.outcome == INVENTORY_DATA_INCOMPLETE

    @property
    def contributing_evaluations(self) -> tuple[InventoryEvaluation, ...]:
        return tuple(item for item in self.evaluations if item.contributes)

    @property
    def excluded_evaluations(self) -> tuple[InventoryEvaluation, ...]:
        """Valid, non-contributing observations, each with its own registered reason."""

        return tuple(
            item
            for item in self.evaluations
            if item.outcome is None and item.exclusion_reason is not None
        )

    @property
    def issues(self) -> tuple[Issue, ...]:
        return _deduplicate_issues(self.inherited_issues + self.rule_issues)

    def to_dict(self) -> dict[str, object]:
        return {
            "rule": INVENTORY_RULE_ID,
            "plant_id": self.plant_id,
            "material_code": self.material_code,
            "inventory_snapshot_time": self.inventory_snapshot_time,
            "OpeningUsableInventory": _quantity_text(self.opening_usable_inventory),
            "SafetyStock": _quantity_text(self.safety_stock),
            "outcome": self.outcome,
            "notes": list(self.notes),
            "safety_stock_provenance": _provenance_payload(self.safety_stock_provenance),
            "inventory_evaluations": [item.to_dict() for item in self.evaluations],
            "inherited_issues": [issue.to_dict() for issue in self.inherited_issues],
            "rule_issues": [issue.to_dict() for issue in self.rule_issues],
        }


@dataclass(frozen=True, slots=True)
class InventoryCalculationResult:
    """Deterministic result of ``BR-INVENTORY-001`` for one construction.

    ``targets`` is ordered deterministically by ``plant_id`` + ``material_code`` +
    ``inventory_snapshot_time``; no cross-Plant ／ cross-Material ／ cross-snapshot-time
    aggregation is performed and no snapshot ever wins over another.

    ``unassigned_inventory_references`` names the accepted Inventory observations whose
    canonical grain is incomplete.  They can be attributed to **no** concrete target, so
    they are neither pushed into some arbitrary target nor used to invent a target identity;
    their registered upstream findings stay in ``inherited_issues`` for the downstream
    fail-safe.
    """

    targets: tuple[InventoryTarget, ...]
    unassigned_inventory_references: tuple[str, ...] = ()
    inherited_issues: tuple[Issue, ...] = ()
    rule_issues: tuple[Issue, ...] = ()

    @property
    def issues(self) -> tuple[Issue, ...]:
        return _deduplicate_issues(self.inherited_issues + self.rule_issues)

    @property
    def data_incomplete_targets(self) -> tuple[InventoryTarget, ...]:
        return tuple(item for item in self.targets if item.data_incomplete)

    def for_grain(
        self, plant_id: Any, material_code: Any, inventory_snapshot_time: Any
    ) -> InventoryTarget | None:
        for item in self.targets:
            if (
                item.plant_id == plant_id
                and item.material_code == material_code
                and item.inventory_snapshot_time == inventory_snapshot_time
            ):
                return item
        return None

    def for_plant_material(
        self, plant_id: Any, material_code: Any
    ) -> tuple[InventoryTarget, ...]:
        return tuple(
            item
            for item in self.targets
            if item.plant_id == plant_id and item.material_code == material_code
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "rule": INVENTORY_RULE_ID,
            "targets": [item.to_dict() for item in self.targets],
            "unassigned_inventory_references": list(
                self.unassigned_inventory_references
            ),
            "inherited_issues": [issue.to_dict() for issue in self.inherited_issues],
            "rule_issues": [issue.to_dict() for issue in self.rule_issues],
            "issues": [issue.to_dict() for issue in self.issues],
        }


# --- rule execution ----------------------------------------------------------------


def compute_opening_usable_inventory(
    construction: CanonicalConstructionReport,
) -> InventoryCalculationResult:
    """Run ``BR-INVENTORY-001`` over one constructed canonical object report.

    Only the already constructed Phase A result is consumed: the retained Inventory
    observations, their I-9 scope contexts and the resolved ``SafetyStock`` contexts.  Each
    exact Plant-level grain is evaluated independently; every retained observation of that
    grain is evaluated on its own -- several observations sharing one grain are legal input
    (``§4.4.12`` ／ ``§4.4.50``) and are never merged, deduplicated or pre-aggregated.
    """

    retained = tuple(construction.objects_for(TARGET_INVENTORY_SNAPSHOT))
    unassignable = tuple(construction.unresolved_for(TARGET_INVENTORY_SNAPSHOT))

    groups: dict[tuple[Any, Any, Any], list[CanonicalObject]] = {}
    for obj in retained:
        assert obj.grain is not None
        key = (
            obj.value_of("plant_id", ABSENT),
            obj.value_of("material_code", ABSENT),
            obj.value_of("inventory_snapshot_time", ABSENT),
        )
        groups.setdefault(key, []).append(obj)

    targets: list[InventoryTarget] = []
    for key in sorted(groups, key=lambda item: tuple(_sort_text(part) for part in item)):
        targets.append(
            _evaluate_target(
                construction=construction,
                plant_id=key[0],
                material_code=key[1],
                inventory_snapshot_time=key[2],
                observations=tuple(groups[key]),
                safety_stock_candidates=_safety_stock_candidates(
                    construction, plant_id=key[0], material_code=key[1]
                ),
            )
        )

    unassigned_references = tuple(
        sorted(obj.record_reference for obj in unassignable)
    )
    inherited = [
        issue
        for target in targets
        for issue in target.inherited_issues
    ]
    inherited.extend(
        _issues_for_references(
            construction,
            tuple(obj.record_reference for obj in unassignable),
        )
    )
    rule = [issue for target in targets for issue in target.rule_issues]

    return InventoryCalculationResult(
        targets=tuple(targets),
        unassigned_inventory_references=unassigned_references,
        inherited_issues=_deduplicate_issues(inherited),
        rule_issues=_deduplicate_issues(rule),
    )


def _evaluate_target(
    *,
    construction: CanonicalConstructionReport,
    plant_id: Any,
    material_code: Any,
    inventory_snapshot_time: Any,
    observations: tuple[CanonicalObject, ...],
    safety_stock_candidates: tuple[
        tuple[Any, EvidenceReference | None, str], ...
    ],
) -> InventoryTarget:
    """Evaluate one exact Plant-level grain: inventory side + independent SafetyStock side."""

    evaluations = tuple(
        _evaluate_observation(
            construction=construction,
            obj=obj,
            plant_id=plant_id,
            material_code=material_code,
            inventory_snapshot_time=inventory_snapshot_time,
        )
        for obj in observations
    )

    inherited_candidates: list[Issue] = []
    for evaluation in evaluations:
        inherited_candidates.extend(evaluation.inherited_issues)
    inherited_candidates.extend(
        _safety_stock_issues(
            construction, plant_id=plant_id, material_code=material_code
        )
    )

    # --- inventory side ------------------------------------------------------------
    notes: list[str] = []
    unreliable = [item for item in evaluations if item.data_incomplete]
    if unreliable:
        opening: ExactQuantity | None = None
        notes.append(
            "at least one %s observation of this grain has an unreliable prerequisite "
            "(scope ／ ownership ／ inventory_status ／ on_hand_qty), so no numeric "
            "OpeningUsableInventory is produced (§2.2.9 / §4.4.50)" % ROLE_INVENTORY_SNAPSHOT
        )
    else:
        opening = ExactQuantity(0, 0)
        for item in evaluations:
            assert item.contribution is not None
            opening = opening + item.contribution
        excluded = [item for item in evaluations if item.exclusion_reason is not None]
        if excluded:
            notes.append(
                "valid non-contributing observations kept distinct: "
                + ", ".join(
                    f"{item.inventory_reference}={item.exclusion_reason}"
                    for item in excluded
                )
            )

    # --- SafetyStock side (independent classification threshold, §2.2.5 / §2.2.7) ---
    safety_stock, safety_provenance, safety_rule_issues, safety_notes = _resolve_safety_stock(
        plant_id=plant_id,
        material_code=material_code,
        candidates=safety_stock_candidates,
    )
    notes.extend(safety_notes)

    inherited = _deduplicate_issues(inherited_candidates)
    inherited_keys = {
        (issue.location, issue.category, issue.reason) for issue in inherited
    }
    rule_candidates: list[Issue] = []
    for evaluation in evaluations:
        rule_candidates.extend(evaluation.rule_issues)
    rule_candidates.extend(safety_rule_issues)
    rule_issues = tuple(
        issue
        for issue in _deduplicate_issues(rule_candidates)
        if (issue.location, issue.category, issue.reason) not in inherited_keys
    )

    outcome: str | None = None
    if opening is None or safety_stock is None:
        outcome = INVENTORY_DATA_INCOMPLETE

    return InventoryTarget(
        plant_id=plant_id,
        material_code=material_code,
        inventory_snapshot_time=inventory_snapshot_time,
        evaluations=evaluations,
        opening_usable_inventory=opening,
        safety_stock=safety_stock,
        outcome=outcome,
        safety_stock_provenance=safety_provenance,
        notes=tuple(notes),
        inherited_issues=inherited,
        rule_issues=rule_issues,
    )


def _evaluate_observation(
    *,
    construction: CanonicalConstructionReport,
    obj: CanonicalObject,
    plant_id: Any,
    material_code: Any,
    inventory_snapshot_time: Any,
) -> InventoryEvaluation:
    """Evaluate one retained Inventory observation against its exact grain.

    The I-9 runtime context decides ownership and scope membership; the rule only applies the
    registered status ／ quantity rules on top, and it never defaults an unresolved
    prerequisite into a numeric contribution.
    """

    reference = obj.record_reference
    artifact, ordinal = _reference_parts(reference)
    location = f"{artifact}[{ordinal}]"
    scope = construction.inventory_scope_for(reference)
    inherited = _issues_for_references(construction, (reference,))

    status_value = obj.value_of("inventory_status", ABSENT)
    on_hand_value = obj.value_of("on_hand_qty", ABSENT)
    on_hand = parse_exact_quantity(on_hand_value)

    def evaluation(
        *,
        scope_resolved: bool,
        ownership_resolved: bool,
        in_scope: bool | None,
        scope_state: str,
        eligible: ExactQuantity | None = None,
        contribution: ExactQuantity | None = None,
        exclusion_reason: str | None = None,
        outcome: str | None = None,
        notes: tuple[str, ...] = (),
        rule_issues: tuple[Issue, ...] = (),
    ) -> InventoryEvaluation:
        filtered = _filter_against_inherited(rule_issues, inherited)
        return InventoryEvaluation(
            target_plant_id=plant_id,
            target_material_code=material_code,
            target_inventory_snapshot_time=inventory_snapshot_time,
            inventory_reference=reference,
            inventory_role=obj.canonicalization_role,
            scope_present=scope is not None,
            scope_resolved=scope_resolved,
            ownership_resolved=ownership_resolved,
            in_scope=in_scope,
            scope_state=scope_state,
            scope_observation=None if scope is None else scope.scope_observation,
            scope_mapping_basis=None if scope is None else scope.mapping_basis,
            inventory_status=None if status_value is ABSENT else status_value,
            on_hand_qty=on_hand,
            eligible_on_hand_qty=eligible,
            contribution=contribution,
            exclusion_reason=exclusion_reason,
            outcome=outcome,
            notes=notes,
            provenance=obj.provenance,
            scope_provenance=None if scope is None else scope.provenance,
            inherited_issues=inherited,
            rule_issues=filtered,
        )

    # --- I-9 ownership ／ scope gate ------------------------------------------------
    if scope is None:
        # Defensive only: the I-9 seam produces a context for every accepted Inventory
        # record, so a missing context means no resolution was ever attempted.  Both
        # independent prerequisites stay unresolved and neither is defaulted.
        return evaluation(
            scope_resolved=False,
            ownership_resolved=False,
            in_scope=None,
            scope_state=SCOPE_STATE_UNRESOLVED,
            outcome=INVENTORY_DATA_INCOMPLETE,
            notes=(
                "no I-9 inventory scope context exists for this record, so neither Plant "
                "ownership nor POC Inventory Scope membership is established; the "
                "observation is neither included nor excluded (§4.5.12 / §4.3.31 G I-9)",
            ),
            rule_issues=(
                _identity_issue(
                    location=location,
                    artifact=artifact,
                    detail=(
                        "Plant ownership cannot be reliably established: no I-9 scope "
                        "context exists for this Inventory evidence, and ownership is "
                        "never taken from the caller nor defaulted to the current Plant "
                        "(§4.5.12 / §4.4.80 #4 / §4.3.31 G I-9)"
                    ),
                ),
                _scope_issue(
                    location=location,
                    artifact=artifact,
                    detail=(
                        "POC Inventory Scope membership cannot be reliably determined: no "
                        "I-9 scope resolution exists for this Inventory evidence; "
                        "membership is never defaulted to included or excluded "
                        "(§4.5.12 / §4.4.80 #5 / §4.3.31 G I-9)"
                    ),
                ),
            ),
        )

    if not scope.ownership_resolved:
        return evaluation(
            scope_resolved=scope.scope_resolved,
            ownership_resolved=False,
            in_scope=scope.in_scope,
            scope_state=SCOPE_STATE_UNRESOLVED,
            outcome=INVENTORY_DATA_INCOMPLETE,
            notes=(
                "Plant ownership is unresolved in the I-9 scope context, so this "
                "observation cannot enter the numeric aggregation (§2.2.9 / §4.5.12)",
            ),
            rule_issues=(
                _identity_issue(
                    location=location,
                    artifact=artifact,
                    detail=(
                        "Plant ownership cannot be reliably established for this Inventory "
                        "evidence, so no numeric OpeningUsableInventory is produced "
                        "(§2.2.9 / §4.4.80 #4 / §4.3.31 G I-9)"
                    ),
                ),
            ),
        )

    if not scope.scope_resolved:
        return evaluation(
            scope_resolved=False,
            ownership_resolved=True,
            in_scope=None,
            scope_state=SCOPE_STATE_UNRESOLVED,
            outcome=INVENTORY_DATA_INCOMPLETE,
            notes=(
                "POC Inventory Scope membership is unresolved, so this observation is "
                "neither included nor excluded and the grain produces no numeric result "
                "(§2.2.4 / §4.4.50)",
            ),
            rule_issues=(
                _scope_issue(
                    location=location,
                    artifact=artifact,
                    detail=(
                        "POC Inventory Scope membership cannot be reliably determined for "
                        "this Inventory evidence, so it may not be silently skipped: the "
                        "affected grain produces DATA_INCOMPLETE "
                        "(§2.2.4 / §4.4.80 #5 / §4.4.50)"
                    ),
                ),
            ),
        )

    if scope.in_scope is False:
        # A legal exclusion: the record is valid, resolved and simply not part of the
        # current POC Inventory Scope.  It contributes 0 and is not a defect.
        return evaluation(
            scope_resolved=True,
            ownership_resolved=True,
            in_scope=False,
            scope_state=SCOPE_STATE_OUT_OF_SCOPE,
            eligible=ExactQuantity(0, 0),
            contribution=ExactQuantity(0, 0),
            exclusion_reason=EXCLUSION_OUT_OF_SCOPE,
            notes=(
                "the I-9 scope context resolved this record as OUT_OF_SCOPE: a legal "
                "exclusion with contribution 0 and no Data Quality Issue (§2.2.4 / §4.5.12)",
            ),
        )

    # --- inventory status eligibility ----------------------------------------------
    if status_value is ABSENT:
        return evaluation(
            scope_resolved=True,
            ownership_resolved=True,
            in_scope=True,
            scope_state=SCOPE_STATE_IN_SCOPE,
            outcome=INVENTORY_DATA_INCOMPLETE,
            notes=(
                "inventory_status is missing; the status is never defaulted to AVAILABLE "
                "(§2.2.3 D)",
            ),
            rule_issues=(
                _field_issue(
                    location=location,
                    artifact=artifact,
                    reason=REASON_MISSING,
                    detail=(
                        "inventory_status is missing, so eligibility cannot be established; "
                        "the status is never defaulted to AVAILABLE and the grain produces "
                        "no numeric result (§2.2.3 D / §4.2.5)"
                    ),
                ),
            ),
        )
    if status_value not in REGISTERED_INVENTORY_STATUSES:
        return evaluation(
            scope_resolved=True,
            ownership_resolved=True,
            in_scope=True,
            scope_state=SCOPE_STATE_IN_SCOPE,
            outcome=INVENTORY_DATA_INCOMPLETE,
            notes=(
                f"inventory_status {status_value!r} is not in the registered vocabulary; it "
                "is never guessed, case-folded or treated as 0 (§2.2.3 D)",
            ),
            rule_issues=(
                _field_issue(
                    location=location,
                    artifact=artifact,
                    reason=REASON_INVALID_DEFINED_STATUS,
                    detail=(
                        f"inventory_status {status_value!r} is not one of the registered "
                        "AVAILABLE ／ INSPECTION ／ FROZEN states, so eligibility cannot be "
                        "established and the grain produces no numeric result "
                        "(§2.2.3 D / §4.2.14)"
                    ),
                ),
            ),
        )

    if status_value in INELIGIBLE_INVENTORY_STATUSES:
        # Valid but ineligible (INSPECTION ／ FROZEN): contributes 0, no Data Quality Issue.
        exclusion = (
            EXCLUSION_INSPECTION
            if status_value == "INSPECTION"
            else EXCLUSION_FROZEN
        )
        return evaluation(
            scope_resolved=True,
            ownership_resolved=True,
            in_scope=True,
            scope_state=SCOPE_STATE_IN_SCOPE,
            eligible=ExactQuantity(0, 0),
            contribution=ExactQuantity(0, 0),
            exclusion_reason=exclusion,
            notes=(
                f"inventory_status {status_value} is valid but ineligible: contribution 0 "
                "and no Data Quality Issue (§2.2.3 B ／ C)",
            ),
        )

    # --- on_hand_qty (exact canonical quantity) -------------------------------------
    if on_hand is None:
        if on_hand_value is ABSENT:
            reason = REASON_MISSING
            detail = (
                "on_hand_qty is missing, so the eligible quantity cannot be established; "
                "no default of 0 is applied (§2.2.8 / §4.2.5)"
            )
        else:
            reason = REASON_INVALID_TYPE
            detail = (
                f"on_hand_qty {on_hand_value!r} is not a registered canonical base-10 "
                "decimal quantity, so it is never coerced or repaired (§2.2.8 / §4.2.5)"
            )
        return evaluation(
            scope_resolved=True,
            ownership_resolved=True,
            in_scope=True,
            scope_state=SCOPE_STATE_IN_SCOPE,
            outcome=INVENTORY_DATA_INCOMPLETE,
            notes=(
                "on_hand_qty is not a usable canonical quantity, so the grain produces no "
                "numeric result (§2.2.8 / §2.2.9)",
            ),
            rule_issues=(
                _field_issue(
                    location=location,
                    artifact=artifact,
                    reason=reason,
                    detail=detail,
                ),
            ),
        )

    if on_hand.negative:
        # Negative inventory is a rule-level invalid prerequisite: never clamped, never
        # abs()'d, never dropped while the rest of the grain keeps a normal total
        # (``§2.2.8``: even ``100 + (-5) = 95`` is forbidden).
        return evaluation(
            scope_resolved=True,
            ownership_resolved=True,
            in_scope=True,
            scope_state=SCOPE_STATE_IN_SCOPE,
            outcome=INVENTORY_DATA_INCOMPLETE,
            notes=(
                f"on_hand_qty {on_hand.text()} is negative: the observation is never "
                "clamped, never made absolute and never ignored while the remaining "
                "observations keep a normal total (§2.2.8)",
            ),
            rule_issues=(
                _field_issue(
                    location=location,
                    artifact=artifact,
                    reason=REASON_OUT_OF_DEFINED_RANGE,
                    detail=(
                        f"on_hand_qty {on_hand.text()} is negative, which is invalid input; "
                        "no clamp to 0, no abs() and no row-level exclusion is applied "
                        "(§2.2.8 / §4.2.5)"
                    ),
                ),
            ),
        )

    return evaluation(
        scope_resolved=True,
        ownership_resolved=True,
        in_scope=True,
        scope_state=SCOPE_STATE_IN_SCOPE,
        eligible=on_hand,
        contribution=on_hand,
        notes=(
            "in scope and AVAILABLE: the exact on_hand_qty is eligible "
            "(§2.2.2 / §2.2.3 A)",
        ),
    )


# --- SafetyStock ------------------------------------------------------------------


def _safety_stock_candidates(
    construction: CanonicalConstructionReport, *, plant_id: Any, material_code: Any
) -> tuple[tuple[Any, EvidenceReference | None, str], ...]:
    """Every resolved SafetyStock candidate of one ``plant_id`` + ``material_code`` grain.

    Two approved surfaces can carry the configured value: the resolved ``Configured Safety
    Stock`` canonical objects (``§4.1.4 O``) and the I-5 injected ``safety_stock_contexts``
    (a policy evidence record inside the same package).  Both are collected **without**
    merging them and without any precedence (``§4.4.102`` C): the caller receives the full
    candidate set so ``>1`` stays unresolved instead of silently winning.

    The grain is ``plant_id`` + ``material_code`` only -- the inventory snapshot time is
    deliberately irrelevant (``§2.2.5``).
    """

    candidates: list[tuple[Any, EvidenceReference | None, str]] = []
    for obj in construction.objects_for("Configured Safety Stock"):
        if (
            obj.value_of("plant_id", ABSENT) != plant_id
            or obj.value_of("material_code", ABSENT) != material_code
        ):
            continue
        candidates.append(
            (
                obj.value_of("SafetyStock", ABSENT),
                obj.provenance,
                f"Configured Safety Stock evidence {obj.record_reference}",
            )
        )
    for context in construction.safety_stock_contexts:
        if context.semantic != "SafetyStock":
            continue
        if _grain_values(context.grain, ("plant_id", "material_code")) != (
            plant_id,
            material_code,
        ):
            continue
        candidates.append(
            (context.value, context.provenance, "injected SafetyStock context (I-5)")
        )
    return tuple(candidates)


def _resolve_safety_stock(
    *,
    plant_id: Any,
    material_code: Any,
    candidates: tuple[tuple[Any, EvidenceReference | None, str], ...],
) -> tuple[ExactQuantity | None, EvidenceReference | None, tuple[Issue, ...], tuple[str, ...]]:
    """Resolve the independent ``SafetyStock`` classification threshold for one grain.

    Exactly one reliable candidate is used; ``0`` is a legal configured value and is never
    treated as missing, while a missing, invalid, negative or ambiguous value leaves
    ``SafetyStock`` unresolved (never defaulted to 0, never clamped, never chosen by
    precedence).
    """

    location = f"SafetyStock[{plant_id}|{material_code}]"
    if not candidates:
        return (
            None,
            None,
            (
                _field_issue(
                    location=location,
                    artifact="SafetyStock",
                    reason=REASON_MISSING,
                    detail=(
                        f"no resolved SafetyStock evidence or context exists for grain "
                        f"plant_id={plant_id!r} + material_code={material_code!r}; the value "
                        "is never defaulted to 0 (§2.2.5 / §2.2.6 / §4.4.51)"
                    ),
                ),
            ),
            (
                "no reliable SafetyStock value exists for this plant + material grain, so "
                "the SafetyStock side is unresolved and is never defaulted to 0 "
                "(§2.2.5 / §2.2.6)",
            ),
        )

    if len(candidates) > 1:
        sources = ", ".join(sorted(source for _value, _prov, source in candidates))
        return (
            None,
            None,
            (
                Issue(
                    location=location,
                    detail=(
                        f"{len(candidates)} resolved SafetyStock candidates exist for grain "
                        f"plant_id={plant_id!r} + material_code={material_code!r} "
                        f"({sources}); no precedence, min ／ max, first ／ last wins or "
                        "same-value deduplication is applied and the value stays unresolved "
                        "(§2.2.5 / §4.4.51)"
                    ),
                    category="CONSISTENCY",
                    reason="CONSISTENCY_CONFLICT",
                    layer=LAYER_2,
                    affected_evidence="SafetyStock",
                    blast_radius=(
                        "affected SafetyStock grain only (no package rejection)"
                    ),
                    design_reference="§4.4.51 / §4.4.92 / §4.4.102 C Stage B",
                    consequence_context=(
                        "SafetyStock stays unresolved; no precedence is invented and the "
                        "package disposition is unchanged"
                    ),
                ),
            ),
            (
                f"{len(candidates)} resolved SafetyStock candidates exist for this grain; no "
                "precedence is applied and the SafetyStock side stays unresolved "
                "(§2.2.5 / §4.4.51)",
            ),
        )

    raw_value, provenance, source = candidates[0]
    if raw_value is ABSENT:
        return (
            None,
            provenance,
            (
                _field_issue(
                    location=location,
                    artifact="SafetyStock",
                    reason=REASON_MISSING,
                    detail=(
                        f"the resolved SafetyStock evidence {source!r} carries no SafetyStock "
                        "value; it is never defaulted to 0 (§2.2.5 / §4.2.5)"
                    ),
                ),
            ),
            (
                "the resolved SafetyStock evidence carries no value, so the SafetyStock side "
                "is unresolved and is never defaulted to 0 (§2.2.5)",
            ),
        )

    value = parse_exact_quantity(raw_value)
    if value is None:
        return (
            None,
            provenance,
            (
                _field_issue(
                    location=location,
                    artifact="SafetyStock",
                    reason=REASON_INVALID_TYPE,
                    detail=(
                        f"the resolved SafetyStock value {raw_value!r} is not a registered "
                        "canonical base-10 decimal quantity; it is never coerced and never "
                        "replaced by 0 (§2.2.5 / §4.4.51)"
                    ),
                ),
            ),
            (
                "the resolved SafetyStock value is not a usable canonical quantity, so the "
                "SafetyStock side is unresolved (§2.2.5)",
            ),
        )
    if value.negative:
        return (
            None,
            provenance,
            (
                _field_issue(
                    location=location,
                    artifact="SafetyStock",
                    reason=REASON_OUT_OF_DEFINED_RANGE,
                    detail=(
                        f"SafetyStock {value.text()} is negative, which is invalid input; it "
                        "is never clamped to 0 (§2.2.5 / §4.2.5)"
                    ),
                ),
            ),
            (
                f"SafetyStock {value.text()} is negative: the SafetyStock side is "
                "unresolved and the value is never clamped (§2.2.5)",
            ),
        )

    return (
        value,
        provenance,
        (),
        (
            f"SafetyStock resolved as {value.text()} from {source} for grain plant_id + "
            "material_code; it stays an independent classification threshold and is never "
            "subtracted from OpeningUsableInventory (§2.2.5 / §2.2.7)",
        ),
    )


# --- issue construction -----------------------------------------------------------


def _field_issue(
    *, location: str, artifact: str, reason: str, detail: str
) -> Issue:
    """One registered ``FIELD_VALUE`` finding (``§4.4.80`` #3 / ``§4.4.81``)."""

    return Issue(
        location=location,
        detail=detail,
        category=CATEGORY_FIELD_VALUE,
        reason=reason,
        layer=LAYER_2,
        affected_evidence=artifact,
        blast_radius="affected inventory grain only (no package rejection)",
        design_reference="§4.4.80 #3 / §4.4.81 / §2.2.9",
        consequence_context=(
            "the affected grain produces DATA_INCOMPLETE; no value is invented, clamped or "
            "defaulted and the package disposition is unchanged"
        ),
    )


def _identity_issue(*, location: str, artifact: str, detail: str) -> Issue:
    """One registered ``IDENTITY_RESOLUTION`` / ``UNRESOLVED_IDENTITY`` finding."""

    return Issue(
        location=location,
        detail=detail,
        category=CATEGORY_IDENTITY_RESOLUTION,
        reason=REASON_UNRESOLVED_IDENTITY,
        layer=LAYER_2,
        affected_evidence=artifact,
        blast_radius="affected inventory grain only (no package rejection)",
        design_reference="§4.5.12 / §4.4.80 #4 / §4.3.31 G I-9",
        consequence_context=(
            "Plant ownership stays unresolved; no value is invented and the package "
            "disposition is unchanged"
        ),
    )


def _scope_issue(*, location: str, artifact: str, detail: str) -> Issue:
    """One registered ``SCOPE_COVERAGE`` / ``UNRESOLVED_SCOPE`` finding."""

    return Issue(
        location=location,
        detail=detail,
        category=CATEGORY_SCOPE_COVERAGE,
        reason=REASON_UNRESOLVED_SCOPE,
        layer=LAYER_2,
        affected_evidence=artifact,
        blast_radius="affected inventory grain only (no package rejection)",
        design_reference="§4.5.12 / §4.4.80 #5 / §4.3.31 G I-9",
        consequence_context=(
            "POC Inventory Scope membership stays unresolved; the observation is neither "
            "included nor excluded and the package disposition is unchanged"
        ),
    )


def _issues_for_references(
    construction: CanonicalConstructionReport, references: tuple[str, ...]
) -> tuple[Issue, ...]:
    """Registered upstream findings that already describe these Inventory records."""

    if not references:
        return ()
    keys: list[str] = []
    for reference in references:
        artifact, ordinal = _reference_parts(reference)
        if artifact:
            keys.append(reference)
            keys.append(f"{artifact}#{ordinal}")
            keys.append(f"{artifact}[{ordinal}]")
    matched: list[Issue] = []
    for issue in construction.issues:
        haystacks = (
            issue.location or "",
            issue.affected_evidence or "",
            issue.detail or "",
        )
        if any(key and key in haystack for key in keys for haystack in haystacks):
            matched.append(issue)
    return _deduplicate_issues(matched)


def _safety_stock_issues(
    construction: CanonicalConstructionReport, *, plant_id: Any, material_code: Any
) -> tuple[Issue, ...]:
    """Registered upstream findings about the SafetyStock grain of one inventory target."""

    matched: list[Issue] = []
    for issue in construction.issues:
        detail = issue.detail or ""
        if "SafetyStock" not in detail and "SafetyStock" not in (issue.location or ""):
            continue
        if f"{plant_id!r}" in detail and f"{material_code!r}" in detail:
            matched.append(issue)
    return _deduplicate_issues(matched)


def _filter_against_inherited(
    issues: tuple[Issue, ...], inherited: tuple[Issue, ...]
) -> tuple[Issue, ...]:
    """Never report a second logical defect that upstream evidence already reported."""

    if not issues:
        return ()
    inherited_keys = {
        (issue.location, issue.category, issue.reason) for issue in inherited
    }
    return tuple(
        issue
        for issue in _deduplicate_issues(issues)
        if (issue.location, issue.category, issue.reason) not in inherited_keys
    )


def _deduplicate_issues(issues: Iterable[Issue]) -> tuple[Issue, ...]:
    """Keep one logical finding per ``location + category + reason``, deterministically."""

    unique: dict[tuple[str, str, str], Issue] = {}
    for issue in issues:
        unique.setdefault((issue.location, issue.category, issue.reason), issue)
    return tuple(sorted(unique.values(), key=Issue.sort_key))


# --- small helpers ----------------------------------------------------------------


def _reference_parts(reference: str) -> tuple[str, str]:
    """``artifact`` + ``ordinal`` of a G3-A technical record reference."""

    parts = (reference or "").split("|")
    artifact = parts[2] if len(parts) > 2 else ""
    ordinal = parts[3] if len(parts) > 3 else ""
    return artifact, ordinal


def _grain_values(
    grain: tuple[Any, ...], names: tuple[str, ...]
) -> tuple[Any, ...] | None:
    """Read the named values out of a canonical grain tuple, or ``None`` when absent."""

    values: list[Any] = []
    for name in names:
        found = ABSENT
        for prop in grain:
            if getattr(prop, "name", None) == name:
                found = prop.value
                break
        if found is ABSENT:
            return None
        values.append(found)
    return tuple(values)


def _quantity_text(value: ExactQuantity | None) -> str | None:
    """Render a canonical exact quantity losslessly: plain base-10 digits, no exponent."""

    return None if value is None else value.text()


def _provenance_payload(value: EvidenceReference | None) -> dict[str, object] | None:
    if value is None:
        return None
    return {
        "snapshot_package_identity": value.snapshot_package_identity,
        "logical_dataset_role": value.logical_dataset_role,
        "stable_source_evidence_locators": list(value.stable_source_evidence_locators),
        "logical_observation": value.logical_observation,
        "mapping_resolution_basis": value.mapping_resolution_basis,
        "accepted_record_path": value.record_path,
    }


def _sort_text(value: Any) -> str:
    return "" if value is ABSENT or value is None else str(value)


__all__ = [
    "ELIGIBLE_INVENTORY_STATUSES",
    "EXCLUSION_FROZEN",
    "EXCLUSION_INSPECTION",
    "EXCLUSION_OUT_OF_SCOPE",
    "INELIGIBLE_INVENTORY_STATUSES",
    "INVENTORY_DATA_INCOMPLETE",
    "INVENTORY_RULE_ID",
    "REGISTERED_INVENTORY_STATUSES",
    "SCOPE_STATE_IN_SCOPE",
    "SCOPE_STATE_OUT_OF_SCOPE",
    "SCOPE_STATE_UNRESOLVED",
    "InventoryCalculationResult",
    "InventoryEvaluation",
    "InventoryTarget",
    "compute_opening_usable_inventory",
]
