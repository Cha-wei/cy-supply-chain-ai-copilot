"""Phase B procurement policy input resolution (``A′``, Human Decision ``APPROVED``).

``BR-PROCUREMENT-001`` needs one baseline recommendation per ``plant_id`` + ``material_code`` per
analysis run, with ``RecommendationNeedDate = FirstShortageDate`` and
``RecommendedPurchaseQty = max(BasePurchaseNeed, ApplicableMOQ)``.  The shortage side of that input
is already registered and implemented (the per-family ``FirstShortageDate`` handoff), but
``ApplicableMOQ`` is a **``POLICY_INPUT``** whose owner is the exact **Procurement Recommendation
Context** and which the approved design resolves in **Phase B**
(``snapshot-import-contract.md`` §4.3.31 **F** phase ordering ＋ **G I-3** ／ **I-4**;
``data-validation.md`` §4.4.67; ``data-dictionary.md`` §4.2.9 ＋ role table row 12;
``master-data-mapping.md`` §4.5.22 Option D).

This module is that Phase B runtime seam and nothing more:

* it establishes the exact Procurement Recommendation Context grain
  ``plant_id + material_code + RecommendationNeedDate`` from the **existing** shortage-side
  ``FirstShortageDate`` handoff (``ShortageCalculationResult.first_shortage_date_for``) -- shortage
  dates are never recomputed and no second date authority is created
  (``§4.3.31`` G **I-4** / ``§4.4.65``);
* it resolves **exactly one** applicable ``ApplicableMOQ`` for that context from the accepted
  package's role-12 ``Procurement policy input`` evidence, or fails closed as ``DATA_INCOMPLETE``
  with the registered ``§4.4.67`` root condition (missing value, unresolvable applicability,
  negative value), while ``ApplicableMOQ = 0`` stays a **valid explicit** no-MOQ result and is never
  confused with missing ／ invalid;
* it preserves the evidence ／ association ／ provenance needed to verify the resolved value (accepted
  record reference ＋ accepted evidence reference with locators and the exact registered
  ``mapping_basis``) and exposes only a **narrow read-only consumption surface** for the downstream
  rule.

It deliberately does **not** implement ``BR-PROCUREMENT-001``: no ``BasePurchaseNeed``, no
``RecommendedPurchaseQty``, no ``MOQAdjustmentQty`` and no recommendation output generation.  No
canonical entity ／ field ／ business enum is added, no supplier selection or precedence rule exists,
the Phase A ``POLICY_INPUT`` refusal is untouched and ``ADR-001`` is unchanged.  The real ERP ／
source-field carrier of ``ApplicableMOQ`` remains ``NOT YET DEFINED`` (``§4.2.9`` ／ ``§4.5.22``):
only the accepted-package in-process handoff shape of this POC is wired here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from .canonical_objects import (
    ROLE_PROCUREMENT_POLICY_INPUT,
    AcceptedPackage,
    AnalysisRunContext,
    CanonicalConstructionReport,
    EvidenceReference,
    JsonObject,
    StrictJsonError,
    parse_strict_json,
    read_provenance_associations,
)
from .constants import (
    CATEGORY_FIELD_VALUE,
    CATEGORY_IDENTITY_RESOLUTION,
    CATEGORY_SEMANTIC_RESOLUTION,
    LAYER_2,
    REASON_INVALID_TYPE,
    REASON_MISSING,
    REASON_OUT_OF_DEFINED_RANGE,
    REASON_SEMANTIC_UNRESOLVED,
    REASON_UNRESOLVED_IDENTITY,
)
from .exact_quantity import ExactQuantity, parse_exact_quantity
from .issues import Issue
from .requirement_calculation import OUTCOME_DATA_INCOMPLETE
from .result_binding import require_same_accepted_package, require_same_analysis_run
from .shortage_calculation import (
    SHORTAGE_DATA_INCOMPLETE,
    SHORTAGE_RULE_ID,
    ShortageCalculationResult,
)

# --- vocabulary --------------------------------------------------------------------

#: The Phase B stage identity.  It is a runtime trace label of the ``§4.3.31`` F phase ordering --
#: **not** a new business rule id, canonical field, enum or status.
PROCUREMENT_POLICY_INPUT_STAGE: str = "PHASE_B_PROCUREMENT_POLICY_INPUT"

#: The **existing** canonical property role 12 assigns (``data-dictionary.md`` §4.2.9 ＋ role table
#: row 12).  A role-12 record registers its applicability under exactly this observation.
PROCUREMENT_POLICY_OBSERVATION: str = "ApplicableMOQ"

#: The resolved business outcome of one context.  ``None`` means **resolved** (with a value, possibly
#: the valid explicit ``0``); ``DATA_INCOMPLETE`` is the **existing** registered outcome and is used
#: whenever the value cannot be reliably resolved (``§4.4.67`` roots A ／ B ／ C).
PROCUREMENT_POLICY_INPUT_UNRESOLVED: str = OUTCOME_DATA_INCOMPLETE

#: Runtime trace labels for **why** a context is unresolved.  They are trace only -- not a new
#: Validation taxonomy, not a canonical vocabulary and not a wire property; the registered
#: ``Issue`` category ／ reason stays the inherited one.
ROOT_MISSING_VALUE: str = "MOQ_VALUE_MISSING"
ROOT_UNUSABLE_VALUE: str = "MOQ_VALUE_UNUSABLE"
ROOT_NEGATIVE_VALUE: str = "MOQ_VALUE_NEGATIVE"
ROOT_APPLICABILITY_UNRESOLVED: str = "MOQ_APPLICABILITY_UNRESOLVED"
ROOT_AMBIGUOUS_APPLICABILITY: str = "MOQ_APPLICABILITY_AMBIGUOUS"
ROOT_NO_APPLICABLE_EVIDENCE: str = "MOQ_NO_APPLICABLE_EVIDENCE"
ROOT_NEED_DATE_UNRESOLVED: str = "RECOMMENDATION_NEED_DATE_UNRESOLVED"
ROOT_RECORD_IDENTITY_UNRESOLVED: str = "MOQ_RECORD_IDENTITY_UNRESOLVED"


# --- registered Phase B applicability wiring ---------------------------------------


@dataclass(frozen=True, slots=True)
class ProcurementPolicyInputBasis:
    """One registered Phase B ``mapping_basis`` literal -> applicability outcome.

    The literal is the exact ``mapping_basis`` an accepted role-12 record must itself register on the
    ``ApplicableMOQ`` association (``§4.3.28`` E).  Merely registering a basis is not an outcome and
    a literal is never borrowed from another association, another observation or another role: it
    only *selects* the registration the accepted record already states, and an unregistered literal
    leaves the context unresolved instead of being ignored (``§4.4.67`` root B).
    """

    basis: str
    outcome: str
    design_reference: str


#: The approved **SIMULATED** Phase B applicability registry: ``exact literal -> exact semantic``.
#: Like the existing G5-A ／ inventory-scope ／ loss-rate registries these are runtime literals of this
#: POC's accepted-package handoff, **not** canonical fields, not a business enum and not a claim
#: about the real ERP source form (``§4.2.9`` physical carrier ``NOT YET DEFINED``).
PROCUREMENT_POLICY_INPUT_REGISTRY: tuple[ProcurementPolicyInputBasis, ...] = (
    ProcurementPolicyInputBasis(
        basis="SIMULATED-MOQ-APPLICABLE",
        outcome="applicable",
        design_reference="§4.4.67 root A ／ C ／ D / §4.3.31 G I-3",
    ),
    ProcurementPolicyInputBasis(
        basis="SIMULATED-MOQ-UNRESOLVED",
        outcome="unresolved",
        design_reference="§4.4.67 root B / §4.3.31 G I-3",
    ),
)

#: ``exact literal -> registered basis``.  Closed and exact-match only: no trim, no case folding, no
#: normalisation, no heuristic and no precedence.
PROCUREMENT_POLICY_INPUT_BASIS_BY_LITERAL: Mapping[str, ProcurementPolicyInputBasis] = {
    entry.basis: entry for entry in PROCUREMENT_POLICY_INPUT_REGISTRY
}

#: The applicability outcomes the registry may state.
PROCUREMENT_POLICY_INPUT_OUTCOMES: frozenset[str] = frozenset({"applicable", "unresolved"})


# --- result representation ---------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ProcurementPolicyInputContext:
    """The resolved procurement policy input of **one** exact Procurement Recommendation Context.

    ``plant_id`` + ``material_code`` + ``recommendation_need_date`` is the owner grain registered by
    ``§4.4.66`` ／ ``§4.3.31`` G I-3: the need date is the family's reliable ``FirstShortageDate``
    consumed from the shortage result (``§4.4.65``), never a recomputed or injected date.

    ``applicable_moq`` is the resolved value (``ExactQuantity``, possibly the valid explicit ``0``)
    and is ``None`` exactly when ``outcome`` is ``DATA_INCOMPLETE``.  ``root_condition`` is the
    runtime trace of the ``§4.4.67`` root that made it unresolved; the registered ``Issue`` fields
    carry the canonical category ／ reason.

    ``record_reference`` ／ ``evidence_reference`` ／ ``applicability_basis`` are the preserved
    provenance of the resolved value: the exact accepted role-12 record, its evidence reference
    (Stable Source Evidence Locators ＋ the registered ``mapping_basis``) and the registered basis
    that made it applicable.  ``considered_references`` names every accepted record that had to be
    taken into account for this context, so an unresolved context cannot hide which evidence was
    seen.
    """

    plant_id: Any
    material_code: Any
    recommendation_need_date: Any
    applicable_moq: ExactQuantity | None = None
    outcome: str | None = None
    root_condition: str | None = None
    applicability_basis: str | None = None
    record_reference: str | None = None
    evidence_reference: EvidenceReference | None = None
    considered_references: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    rule_issues: tuple[Issue, ...] = ()

    @property
    def grain(self) -> tuple[Any, Any, Any]:
        return (self.plant_id, self.material_code, self.recommendation_need_date)

    @property
    def data_incomplete(self) -> bool:
        return self.outcome == PROCUREMENT_POLICY_INPUT_UNRESOLVED

    @property
    def resolved(self) -> bool:
        return self.outcome is None and self.applicable_moq is not None

    @property
    def issues(self) -> tuple[Issue, ...]:
        return self.rule_issues

    def to_dict(self) -> dict[str, object]:
        return {
            "stage": PROCUREMENT_POLICY_INPUT_STAGE,
            "plant_id": self.plant_id,
            "material_code": self.material_code,
            "RecommendationNeedDate": self.recommendation_need_date,
            "ApplicableMOQ": None if self.applicable_moq is None else self.applicable_moq.text(),
            "outcome": self.outcome,
            "root_condition": self.root_condition,
            "applicability_basis": self.applicability_basis,
            "record_reference": self.record_reference,
            "evidence_reference": _evidence_payload(self.evidence_reference),
            "considered_references": list(self.considered_references),
            "notes": list(self.notes),
            "rule_issues": [issue.to_dict() for issue in self.rule_issues],
        }


@dataclass(frozen=True, slots=True)
class ProcurementPolicyInputResult:
    """Deterministic Phase B result: one resolved policy input per Procurement Recommendation Context.

    ``contexts`` is ordered deterministically by ``plant_id`` -> ``material_code`` (the registered
    family order; one baseline recommendation exists per family per analysis run, so one context
    exists per family) and carries the contexts whose policy input had to be resolved --
    successfully or as a fail-closed ``DATA_INCOMPLETE``.

    ``valid_absence_grains`` names the families whose horizon is fully reliable and never went short:
    per ``§4.4.67`` no purchase recommendation applies to them, so their ``ApplicableMOQ`` is
    ``not present by design`` and **not** a validation failure.

    ``analysis_run`` is the construction's existing ``AnalysisRunContext`` (the derived-result
    provenance binding of ``F3-RB1``): a downstream deterministic rule verifies it before consuming
    any value from this result.
    """

    analysis_run: AnalysisRunContext
    contexts: tuple[ProcurementPolicyInputContext, ...] = ()
    valid_absence_grains: tuple[tuple[Any, Any], ...] = ()
    inherited_issues: tuple[Issue, ...] = ()
    rule_issues: tuple[Issue, ...] = ()

    @property
    def issues(self) -> tuple[Issue, ...]:
        return _deduplicate_issues(self.inherited_issues + self.rule_issues)

    @property
    def data_incomplete_contexts(self) -> tuple[ProcurementPolicyInputContext, ...]:
        return tuple(item for item in self.contexts if item.data_incomplete)

    def for_owner(
        self, plant_id: Any, material_code: Any, recommendation_need_date: Any
    ) -> ProcurementPolicyInputContext | None:
        """The stated policy input of one exact owner grain, or ``None``.

        ``None`` means this result states no context for that exact
        ``plant_id`` + ``material_code`` + ``RecommendationNeedDate``; the caller takes the owner
        grain from the shortage-side handoff and never invents one.
        """

        for item in self.contexts:
            if (
                item.plant_id == plant_id
                and item.material_code == material_code
                and item.recommendation_need_date == recommendation_need_date
            ):
                return item
        return None

    def for_family(
        self, plant_id: Any, material_code: Any
    ) -> ProcurementPolicyInputContext | None:
        """The stated policy input of one exact family, or ``None``."""

        for item in self.contexts:
            if item.plant_id == plant_id and item.material_code == material_code:
                return item
        return None

    def applicable_moq_for(
        self, plant_id: Any, material_code: Any, recommendation_need_date: Any
    ) -> ExactQuantity | None:
        """The resolved ``ApplicableMOQ`` of one owner grain, or ``None`` when it is unresolved.

        ``None`` never means the valid explicit ``0``: that value is returned as an
        ``ExactQuantity`` of zero, and the two are deliberately distinguishable
        (``§2.5.6`` ／ ``§4.4.67`` root D).
        """

        context = self.for_owner(plant_id, material_code, recommendation_need_date)
        return None if context is None else context.applicable_moq

    def is_valid_absence(self, plant_id: Any, material_code: Any) -> bool:
        """Whether this result states a reliable, never-short horizon for that exact family."""

        return (plant_id, material_code) in self.valid_absence_grains

    def to_dict(self) -> dict[str, object]:
        return {
            "stage": PROCUREMENT_POLICY_INPUT_STAGE,
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
            "contexts": [item.to_dict() for item in self.contexts],
            "valid_absence_grains": [
                {"plant_id": plant_id, "material_code": material_code}
                for plant_id, material_code in self.valid_absence_grains
            ],
            "rule_issues": [issue.to_dict() for issue in self.rule_issues],
        }


# --- entry point -------------------------------------------------------------------


def compute_procurement_policy_input(
    construction: CanonicalConstructionReport,
    shortage: ShortageCalculationResult,
    *,
    accepted: AcceptedPackage,
) -> ProcurementPolicyInputResult:
    """Resolve the Phase B procurement policy input for every Procurement Recommendation Context.

    ``construction`` supplies the Analysis Run ／ accepted-package binding (and nothing else);
    ``shortage`` supplies the per-family ``FirstShortageDate`` handoff; ``accepted`` is the evidence
    source of the role-12 ``Procurement policy input`` records.  All three must belong to the same
    analysis run and the same accepted package ／ accepted content view, verified **before** any
    evidence is consumed (``F3-RB1`` ／ ``§4.3.31`` E ／ ``§4.4.65``).
    """

    require_same_analysis_run(
        construction.analysis_run,
        (SHORTAGE_RULE_ID, shortage.analysis_run),
    )
    require_same_accepted_package(
        construction.analysis_run,
        package_id=accepted.package_id,
        accepted_content_view_digest=accepted.content_view_digest,
    )

    records = _policy_records(accepted)
    inherited: tuple[Issue, ...] = ()

    contexts: list[ProcurementPolicyInputContext] = []
    valid_absence: list[tuple[Any, Any]] = []
    rule_issues: list[Issue] = []
    for plant_id, material_code in _families(shortage):
        need_date = shortage.first_shortage_date_for(plant_id, material_code)
        if need_date is None:
            # A fully reliable horizon that never went short: §4.4.67 registers this as the valid
            # absence boundary, not a validation failure and not an unresolved value.
            valid_absence.append((plant_id, material_code))
            continue
        if need_date == SHORTAGE_DATA_INCOMPLETE:
            context = _need_date_unresolved(plant_id, material_code)
        else:
            context = _resolve(
                plant_id=plant_id,
                material_code=material_code,
                recommendation_need_date=need_date,
                records=records,
            )
        contexts.append(context)
        rule_issues.extend(context.rule_issues)

    return ProcurementPolicyInputResult(
        analysis_run=construction.analysis_run,
        contexts=tuple(contexts),
        valid_absence_grains=tuple(valid_absence),
        inherited_issues=inherited,
        rule_issues=_deduplicate_issues(tuple(rule_issues)),
    )


# --- resolution --------------------------------------------------------------------


def _resolve(
    *,
    plant_id: Any,
    material_code: Any,
    recommendation_need_date: Any,
    records: Sequence[_PolicyRecord],
) -> ProcurementPolicyInputContext:
    """Resolve exactly one applicable ``ApplicableMOQ`` for one exact owner context, or fail closed.

    ``§4.4.67`` semantics: the applicability mapping must be reliably determined **and** the value
    must be a registered non-negative quantity; otherwise the context is ``DATA_INCOMPLETE`` and the
    value is never defaulted, clamped or chosen by precedence.

    **Identity readiness (``§4.4.26`` ／ ``§4.3.22`` C-10).**  Only a **reliably established**
    ``plant_id`` + ``material_code`` may prove that a record belongs to *another* family.  A record
    whose identity properties are present but not usable as registered canonical identifiers (JSON
    ``null``, an empty string, a non-string) cannot be scoped to any family, so it is never silently
    excluded: its applicability to this exact context is unresolved and it participates in the
    fail-closed path.
    """

    considered: list[str] = []
    applicable: list[_PolicyRecord] = []
    identity_unresolved: list[_PolicyRecord] = []
    unresolved_evidence = False

    for record in records:
        if record.identity_resolved and (
            record.plant_id,
            record.material_code,
        ) != (plant_id, material_code):
            # Only a reliably established identity proves another family: the record is not
            # evidence about this context, so it neither applies to it nor blocks it.
            continue
        considered.append(record.reference)
        if not record.identity_resolved:
            identity_unresolved.append(record)
            continue
        if record.problem is not None or record.outcome == "unresolved":
            # A record that may belong to this context but whose applicability cannot be reliably
            # determined can never be silently ignored: the resolution fails closed instead of
            # claiming a single value from a partial view.
            unresolved_evidence = True
            continue
        applicable.append(record)

    if identity_unresolved:
        # The record's own canonical identity is not reliably resolved, so nothing proves it belongs
        # to another family -- and its applicability to this context is unresolved.  The context is
        # never resolved from the remaining evidence (no numeric value from a partial view).
        sample = identity_unresolved[0]
        return _unresolved_context(
            plant_id=plant_id,
            material_code=material_code,
            recommendation_need_date=recommendation_need_date,
            root=ROOT_RECORD_IDENTITY_UNRESOLVED,
            considered=tuple(sorted(considered)),
            detail=(
                f"{len(identity_unresolved)} accepted Procurement policy input record(s) state a "
                "plant_id ／ material_code that is present but is not a reliably established "
                "canonical identifier, so the family they belong to cannot be resolved; such a "
                "record may belong to this exact plant_id + material_code, so its applicability to "
                "this Procurement Recommendation Context is unresolved and no MOQ is resolved from "
                "the remaining evidence (§4.4.26 / §4.3.22 C-10 / §4.4.67 root B)"
            ),
            category=CATEGORY_SEMANTIC_RESOLUTION,
            reason=REASON_SEMANTIC_UNRESOLVED,
            record_issues=tuple(
                issue for item in identity_unresolved for issue in item.identity_issues
            ),
            record_reference=sample.reference,
            evidence_reference=sample.evidence,
        )

    if unresolved_evidence:
        return _unresolved_context(
            plant_id=plant_id,
            material_code=material_code,
            recommendation_need_date=recommendation_need_date,
            root=ROOT_APPLICABILITY_UNRESOLVED,
            considered=tuple(sorted(considered)),
            detail=(
                "at least one accepted Procurement policy input record of this exact "
                "plant_id + material_code either states no registered Phase B applicability basis "
                "for its ApplicableMOQ association or registers the approved 'cannot be reliably "
                "determined' basis; the applicable MOQ ／ its applicability mapping cannot be "
                "reliably determined for this exact Procurement Recommendation Context, and the "
                "evidence is never ignored so that a single value could be claimed from a partial "
                "view (§4.4.67 root B / §4.3.31 G I-3)"
            ),
            category=CATEGORY_SEMANTIC_RESOLUTION,
            reason=REASON_SEMANTIC_UNRESOLVED,
        )
    if not applicable:
        return _unresolved_context(
            plant_id=plant_id,
            material_code=material_code,
            recommendation_need_date=recommendation_need_date,
            root=ROOT_NO_APPLICABLE_EVIDENCE,
            considered=tuple(sorted(considered)),
            detail=(
                "no accepted Procurement policy input record states an applicable ApplicableMOQ "
                "for this exact plant_id + material_code, so the required MOQ value of this "
                "triggered recommendation is missing; it is never defaulted to 0 and no value is "
                "invented (§2.5.6 B / §4.4.67 root A)"
            ),
            category=CATEGORY_FIELD_VALUE,
            reason=REASON_MISSING,
        )
    if len(applicable) > 1:
        return _unresolved_context(
            plant_id=plant_id,
            material_code=material_code,
            recommendation_need_date=recommendation_need_date,
            root=ROOT_AMBIGUOUS_APPLICABILITY,
            considered=tuple(sorted(considered)),
            detail=(
                f"{len(applicable)} accepted Procurement policy input records state an applicable "
                "ApplicableMOQ for this exact plant_id + material_code; exactly one applicable "
                "result is required and they are never reconciled by first ／ last wins, by source "
                "type, by a minimum ／ maximum or by any other unapproved precedence (§4.4.67 "
                "root B / multiple policy source validation)"
            ),
            category=CATEGORY_SEMANTIC_RESOLUTION,
            reason=REASON_SEMANTIC_UNRESOLVED,
        )

    record = applicable[0]
    if record.value is None:
        if record.negative:
            root = ROOT_NEGATIVE_VALUE
            detail = (
                "the applicable Procurement policy input record of this exact "
                "plant_id + material_code states a negative ApplicableMOQ value "
                f"{record.raw_value!r}; it is never clamped, absolutised or turned into 0, and the "
                "context stays DATA_INCOMPLETE (§2.5.7 / §4.4.67 root C)"
            )
            reason = REASON_OUT_OF_DEFINED_RANGE
        elif record.raw_value is None:
            root = ROOT_MISSING_VALUE
            detail = (
                "the applicable Procurement policy input record of this exact "
                "plant_id + material_code states no ApplicableMOQ property, so the required MOQ "
                "value of this triggered recommendation is missing and is never defaulted to 0 "
                "(§2.5.6 B / §4.4.67 root A)"
            )
            reason = REASON_MISSING
        else:
            root = ROOT_UNUSABLE_VALUE
            detail = (
                "the applicable Procurement policy input record of this exact "
                "plant_id + material_code states an ApplicableMOQ value "
                f"{record.raw_value!r} that is not a registered exact non-negative quantity; it is "
                "never coerced, repaired or defaulted (§4.4.67 root A)"
            )
            reason = REASON_INVALID_TYPE
        return _unresolved_context(
            plant_id=plant_id,
            material_code=material_code,
            recommendation_need_date=recommendation_need_date,
            root=root,
            considered=tuple(sorted(considered)),
            detail=detail,
            category=CATEGORY_FIELD_VALUE,
            reason=reason,
            record_reference=record.reference,
            evidence_reference=record.evidence,
            applicability_basis=record.basis,
        )

    return ProcurementPolicyInputContext(
        plant_id=plant_id,
        material_code=material_code,
        recommendation_need_date=recommendation_need_date,
        applicable_moq=record.value,
        outcome=None,
        applicability_basis=record.basis,
        record_reference=record.reference,
        evidence_reference=record.evidence,
        considered_references=tuple(sorted(considered)),
        notes=(
            "ApplicableMOQ resolved for the exact Procurement Recommendation Context from exactly "
            "one applicable accepted Procurement policy input record; the value is carried as the "
            "exact canonical quantity it was accepted as (§4.4.67 root D for the explicit valid 0)",
        ),
    )


def _need_date_unresolved(
    plant_id: Any, material_code: Any
) -> ProcurementPolicyInputContext:
    """The context of a family whose ``RecommendationNeedDate`` is itself unresolved (``I-4``)."""

    return _unresolved_context(
        plant_id=plant_id,
        material_code=material_code,
        recommendation_need_date=None,
        root=ROOT_NEED_DATE_UNRESOLVED,
        considered=(),
        detail=(
            "the shortage-side handoff of this exact plant_id + material_code states "
            "SHORTAGE_DATA_INCOMPLETE, so RecommendationNeedDate (= FirstShortageDate) is unresolved "
            "and the exact Procurement Recommendation Context cannot be established; the shortage "
            "date is never recomputed here and no MOQ is resolved or guessed for it (§4.3.31 G I-4 "
            "/ §4.4.65 / §2.1.6)"
        ),
        category=CATEGORY_SEMANTIC_RESOLUTION,
        reason=REASON_SEMANTIC_UNRESOLVED,
    )


def _unresolved_context(
    *,
    plant_id: Any,
    material_code: Any,
    recommendation_need_date: Any,
    root: str,
    considered: tuple[str, ...],
    detail: str,
    category: str,
    reason: str,
    record_reference: str | None = None,
    evidence_reference: EvidenceReference | None = None,
    applicability_basis: str | None = None,
    record_issues: tuple[Issue, ...] = (),
) -> ProcurementPolicyInputContext:
    location = (
        f"procurement_policy_input[{_sort_text(plant_id)}/"
        f"{_sort_text(material_code)}/{_sort_text(recommendation_need_date)}]"
    )
    issue = Issue(
        location=location,
        detail=detail,
        category=category,
        reason=reason,
        layer=LAYER_2,
        affected_evidence=ROLE_PROCUREMENT_POLICY_INPUT,
        blast_radius="the procurement policy input of this exact context only",
        design_reference="§4.4.67 / §4.3.31 G I-3 ／ I-4 / §2.5.5 ～ §2.5.7",
        consequence_context=(
            "the context carries no numeric ApplicableMOQ and no value is defaulted, clamped or "
            "chosen by precedence; a downstream numeric recommendation cannot be produced from it"
        ),
    )
    return ProcurementPolicyInputContext(
        plant_id=plant_id,
        material_code=material_code,
        recommendation_need_date=recommendation_need_date,
        applicable_moq=None,
        outcome=PROCUREMENT_POLICY_INPUT_UNRESOLVED,
        root_condition=root,
        applicability_basis=applicability_basis,
        record_reference=record_reference,
        evidence_reference=evidence_reference,
        considered_references=considered,
        notes=(
            "the required ApplicableMOQ of this exact Procurement Recommendation Context is not "
            "reliably available, so the context is DATA_INCOMPLETE and never carries a guessed value",
        ),
        rule_issues=(issue, *record_issues),
    )


# --- accepted role-12 evidence -----------------------------------------------------


@dataclass(frozen=True, slots=True)
class _PolicyRecord:
    """One accepted role-12 record projected onto the minimum Phase B decision inputs.

    ``identity_resolved`` says whether the record states a **reliably established**
    ``plant_id`` + ``material_code`` -- the registered canonical identifier representation
    (``§4.3.22`` C-10: an exact JSON string; ``§4.4.26``: a present identifier that is empty does not
    resolve identity).  Only then may the record be scoped to a family and skipped as another family's
    evidence; otherwise it is unscopable, must be taken into account for every context and fails closed
    (never silently dropped).  ``identity_issues`` carries that record's own registered identity
    findings (one per unusable component), and ``problem`` states why an *identified* record of this
    exact context cannot be interpreted (no ／ ambiguous ／ unapproved applicability registration).
    """

    reference: str
    identity_resolved: bool
    plant_id: Any
    material_code: Any
    identity_issues: tuple[Issue, ...]
    problem: str | None
    basis: str | None
    outcome: str | None
    raw_value: Any
    value: ExactQuantity | None
    negative: bool
    evidence: EvidenceReference | None


def _policy_records(accepted: AcceptedPackage) -> tuple[_PolicyRecord, ...]:
    """Every accepted role-12 record as a Phase B decision input, in declared artifact order.

    Only the **same accepted package** evidence is read (``§4.3.31`` E): business artifacts are never
    re-read from the filesystem and no external source is consulted.  A record that cannot be parsed
    or whose declared role differs from its real role is reported as an unusable record, so it can
    never be silently dropped.
    """

    records: list[_PolicyRecord] = []
    for role, artifact in accepted.datasets():
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
            if role != ROLE_PROCUREMENT_POLICY_INPUT:
                continue
            reference = f"{artifact}#{ordinal}"
            records.append(
                _policy_record(
                    accepted=accepted,
                    role=role,
                    artifact=artifact,
                    ordinal=ordinal,
                    record=record,
                )
            )
    return tuple(records)


def _policy_record(
    *,
    accepted: AcceptedPackage,
    role: str,
    artifact: str,
    ordinal: int,
    record: JsonObject,
) -> _PolicyRecord:
    reference = f"{artifact}#{ordinal}"
    states = (_identifier_state(record, "plant_id"), _identifier_state(record, "material_code"))
    identity_resolved = all(state.usable for state in states)
    identity_issues = tuple(
        _identity_issue(reference=reference, state=state)
        for state in states
        if not state.usable
    )
    evidence = _evidence_reference(
        accepted=accepted, role=role, artifact=artifact, ordinal=ordinal, record=record
    )
    raw_value = (
        record[PROCUREMENT_POLICY_OBSERVATION]
        if PROCUREMENT_POLICY_OBSERVATION in record
        else None
    )
    parsed = None if raw_value is None else parse_exact_quantity(raw_value)
    negative = parsed is not None and parsed.negative
    value = None if parsed is None or negative else parsed

    problem: str | None = None
    basis_literal: str | None = None
    outcome: str | None = None
    if not identity_resolved:
        problem = (
            "the accepted Procurement policy input record does not state a reliably established "
            "plant_id + material_code, so the family it belongs to cannot be resolved"
        )
    else:
        registrations = [
            item
            for item in read_provenance_associations(record)
            if item.observation == PROCUREMENT_POLICY_OBSERVATION
        ]
        approved = [
            item
            for item in registrations
            if (item.mapping_basis or "") in PROCUREMENT_POLICY_INPUT_BASIS_BY_LITERAL
        ]
        if not registrations:
            problem = (
                "the accepted Procurement policy input record registers no ApplicableMOQ "
                "association at all, so whether it states an applicable MOQ cannot be established"
            )
        elif len(registrations) > 1 or len(approved) != 1:
            problem = (
                "the accepted Procurement policy input record does not register exactly one "
                "approved Phase B ApplicableMOQ association (unapproved basis literals or several "
                "registrations), so its applicability to this context cannot be reliably "
                "determined"
            )
        else:
            entry = PROCUREMENT_POLICY_INPUT_BASIS_BY_LITERAL[approved[0].mapping_basis or ""]
            basis_literal = entry.basis
            outcome = entry.outcome
    return _PolicyRecord(
        reference=reference,
        identity_resolved=identity_resolved,
        plant_id=states[0].value,
        material_code=states[1].value,
        identity_issues=identity_issues,
        problem=problem,
        basis=basis_literal,
        outcome=outcome,
        raw_value=raw_value,
        value=value,
        negative=negative,
        evidence=evidence,
    )


#: The two **existing** registered ways an accepted value can fail to establish canonical identity.
#: They are the categories ／ reasons ``layer2`` itself reports for the very same value
#: (``§4.4.26`` ／ ``§4.3.22`` C-10) -- never a new identity vocabulary.
_IDENTITY_REPRESENTATION: str = "REPRESENTATION"
_IDENTITY_UNRESOLVED: str = "UNRESOLVED"


@dataclass(frozen=True, slots=True)
class _IdentifierState:
    """One canonical identity component of an accepted record, as the registered rule reads it.

    ``usable`` is ``True`` only when the component **reliably establishes** identity: the property is
    present and holds a non-empty exact JSON string (``§4.3.22`` C-10 ＋ ``§4.4.26``).  Everything else
    is present-but-unusable -- or not present at all -- and carries the registered ``category`` ／
    ``reason`` of that defect (``kind`` says which of the two, for the record's own ``Issue``).
    """

    name: str
    value: Any
    problem: str | None
    kind: str | None
    category: str | None
    reason: str | None

    @property
    def usable(self) -> bool:
        return self.problem is None


def _identifier_state(record: JsonObject, name: str) -> _IdentifierState:
    """Read one canonical identity component exactly as the **existing** registered rule does.

    The rule is the one ``layer2._representation_defect`` already applies (``§4.3.22`` C-10 ＋
    ``§4.4.26``): a canonical identifier is an exact JSON string, and an empty one leaves the affected
    evidence unresolved.  Nothing is repaired, coerced or defaulted here, and no new identity rule is
    introduced:

    * the property is **absent** -- a registered canonical identity component is not present, the same
      condition ``canonicalization`` reports as unresolved identity for an ungrainable record
      (``§4.4.26`` ／ ``§4.4.94``);
    * the value is JSON ``null`` -- ``§4.3.22`` C-2 explicit missing ／ unavailable, which ``layer2``
      reports as *not evaluable* and **never** as ``INVALID_TYPE``: no identifier value exists to
      resolve identity with, so identity is not established;
    * the value is **not** a JSON string -- the registered representation is violated
      (``§4.3.22`` C-10) and is classified precisely as ``layer2`` classifies it:
      ``FIELD_VALUE`` ／ ``INVALID_TYPE``;
    * the value is an **empty** string -- ``§4.4.26``: the identifier is present but empty and leaves
      the affected evidence unresolved (``IDENTITY_RESOLUTION`` ／ ``UNRESOLVED_IDENTITY``).
    """

    if name not in record:
        return _IdentifierState(
            name=name,
            value=None,
            problem=(
                f"the accepted record states no {name} at all, so this canonical identity component "
                "is not present"
            ),
            kind=_IDENTITY_UNRESOLVED,
            category=CATEGORY_IDENTITY_RESOLUTION,
            reason=REASON_UNRESOLVED_IDENTITY,
        )

    value = record[name]
    if value is None:
        return _IdentifierState(
            name=name,
            value=None,
            problem=(
                f"{name} is present as JSON null, i.e. an explicit missing ／ unavailable value "
                "(§4.3.22 C-2), so no identifier value resolves this identity"
            ),
            kind=_IDENTITY_UNRESOLVED,
            category=CATEGORY_IDENTITY_RESOLUTION,
            reason=REASON_UNRESOLVED_IDENTITY,
        )
    if not isinstance(value, str):
        return _IdentifierState(
            name=name,
            value=value,
            problem=(
                f"{name} is present as JSON {type(value).__name__}, not the exact JSON string the "
                "registered canonical identifier representation requires (§4.3.22 C-10)"
            ),
            kind=_IDENTITY_REPRESENTATION,
            category=CATEGORY_FIELD_VALUE,
            reason=REASON_INVALID_TYPE,
        )
    if value == "":
        return _IdentifierState(
            name=name,
            value=value,
            problem=(
                f"{name} is present but empty; §4.4.26 treats an empty canonical identifier as "
                "leaving the affected evidence's identity unresolved"
            ),
            kind=_IDENTITY_UNRESOLVED,
            category=CATEGORY_IDENTITY_RESOLUTION,
            reason=REASON_UNRESOLVED_IDENTITY,
        )
    return _IdentifierState(
        name=name,
        value=value,
        problem=None,
        kind=None,
        category=None,
        reason=None,
    )


def _identity_issue(*, reference: str, state: _IdentifierState) -> Issue:
    """The record's own registered finding for one unusable identity component.

    The category ／ reason are the inherited ones and mirror ``layer2`` for the very same value:
    ``IDENTITY_RESOLUTION`` ／ ``UNRESOLVED_IDENTITY`` for an identifier that is missing (absent or JSON
    ``null``) or empty, and ``FIELD_VALUE`` ／ ``INVALID_TYPE`` for a present value whose representation
    is not the registered one.  One ``Issue`` is reported per unusable component, so a record with two
    defective components never has to invent an ordering between them.
    """

    assert state.problem is not None
    return Issue(
        location=f"procurement_policy_input_record[{reference}].{state.name}",
        detail=(
            "this accepted Procurement policy input record does not state a reliably established "
            f"canonical identity: {state.problem}. It is never treated as confidently belonging to "
            "another family and never silently ignored; its applicability to the Procurement "
            "Recommendation Contexts stays unresolved (§4.4.26 / §4.3.22 C-10 / §4.4.67 root B)"
        ),
        category=state.category,
        reason=state.reason,
        layer=LAYER_2,
        affected_evidence=ROLE_PROCUREMENT_POLICY_INPUT,
        blast_radius="every Procurement Recommendation Context of this result",
        design_reference=(
            "§4.4.27 ～ §4.4.34 + §4.3.22 C-10"
            if state.kind == _IDENTITY_REPRESENTATION
            else "§4.4.26 (identifier) + §4.3.22 C-10"
        ),
        consequence_context=(
            "the affected policy input cannot be scoped to a family, so no context may be resolved "
            "from a partial view of the evidence"
        ),
    )


def _families(shortage: ShortageCalculationResult) -> tuple[tuple[Any, Any], ...]:
    """Every ``plant_id`` + ``material_code`` family the shortage result states, in grain order."""

    families: list[tuple[Any, Any]] = []
    seen: set[tuple[Any, Any]] = set()
    for grain in shortage.grains:
        key = (grain.plant_id, grain.material_code)
        try:
            if key in seen:
                continue
            seen.add(key)
        except TypeError:  # pragma: no cover - an ungroupable family is not a context
            continue
        families.append(key)
    families.sort(key=lambda item: (_sort_text(item[0]), _sort_text(item[1])))
    return tuple(families)


# --- helpers -----------------------------------------------------------------------


def _evidence_reference(
    *,
    accepted: AcceptedPackage,
    role: str,
    artifact: str,
    ordinal: int,
    record: JsonObject,
) -> EvidenceReference:
    """The package-scoped provenance of one accepted role-12 record (locators ＋ basis as stated)."""

    locators: list[str] = []
    basis: str | None = None
    for item in read_provenance_associations(record):
        if item.observation != PROCUREMENT_POLICY_OBSERVATION:
            continue
        for locator in item.evidence:
            if locator not in locators:
                locators.append(locator)
        if item.mapping_basis is not None:
            basis = item.mapping_basis
    return EvidenceReference(
        snapshot_package_identity=accepted.package_id,
        logical_dataset_role=role,
        artifact=artifact,
        record_ordinal=ordinal,
        logical_observation=PROCUREMENT_POLICY_OBSERVATION,
        stable_source_evidence_locators=tuple(locators),
        mapping_resolution_basis=basis,
    )


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


def _deduplicate_issues(issues: Iterable[Issue]) -> tuple[Issue, ...]:
    seen: dict[tuple[str, str, str], Issue] = {}
    for issue in issues:
        seen.setdefault((issue.location, issue.category, issue.reason), issue)
    return tuple(sorted(seen.values(), key=Issue.sort_key))


def _sort_text(value: Any) -> str:
    return "" if value is None else str(value)


__all__ = [
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
]
