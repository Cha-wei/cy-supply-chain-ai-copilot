"""First deterministic tranche composition (application orchestration).

``POC Design v0.2`` §10.1 B assigns the first tranche five module responsibilities, and
``ADR-001`` registers the orchestration boundary: the thin CLI calls application
orchestration, and that orchestration composes snapshot loading, validation, canonical
objects, deterministic rules and the recommendation result.  This module is exactly that
composition -- and nothing else.

Registered stage order (the only composition performed here)::

    snapshot loader (Layer 1)
      -> Layer-2 canonical evidence validation
      -> Phase A canonical object construction
      -> BR-REQUIREMENT-001 ／ BR-INVENTORY-001 ／ BR-INBOUND-001 ／ BR-SUBSTITUTE-001
      -> BR-SHORTAGE-001
      -> Phase B procurement policy input
      -> BR-PROCUREMENT-001
      -> Supplier Risk runtime input seam (``A′``)
      -> Supplier Risk Evidence (``BR-SUPPLIER-RISK-001``)

What this module deliberately does **not** do:

* it adds no business rule, no canonical field ／ entity ／ grain, no Validation Category
  ／ Reason and no business status;
* every stage is the already registered public entry point of its own module --- no rule
  is re-implemented, no upstream result is recomputed, no business value is derived,
  repaired, defaulted or clamped, and no accepted artifact is read outside the Layer-1
  loader (``§4.3.31`` E: file reading stays in the outer layer);
* the only caller-supplied inputs are the configured trusted package-input boundary and
  the registered in-process logical handoff (:class:`~snapshot_loader.canonical_objects.PhaseAHandoff`:
  the Analysis Run context plus injection I-2 ／ I-5 ／ I-7 ／ I-8 ／ I-9 citations,
  ``§4.3.31`` E ／ G).  This module never mints an Analysis Run of its own and never
  invents a handoff entry;
* the Analysis Run ／ exactly-one-accepted-package binding of every consumed upstream
  result is verified by the consuming seam itself (``F3-RB1`` ／
  :mod:`snapshot_loader.result_binding`).  The pipeline calls those seams in order and so
  inherits their rejection behaviour; it adds no binding check of its own and can neither
  weaken nor bypass one;
* no stage result is aggregated into a pipeline-level business status.  A
  :class:`PipelineStage` entry records **execution** facts only (whether the stage was
  entered, and why not when it was not); every business outcome stays inside its own
  registered result.

``Layer 1`` is the only stage that reads the filesystem, through
:func:`~snapshot_loader.loader.load_package`.  When the package is not ``ACCEPTED`` no
Analysis Run exists, so no downstream deterministic stage is entered at all
(``§4.4.2`` ／ ``IC-18``) and the result carries the Layer-1 outcome unchanged.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from .canonical_objects import (
    AnalysisRunContext,
    CanonicalConstructionReport,
    PhaseAHandoff,
    construct_canonical_objects,
)
from .inbound_calculation import INBOUND_RULE_ID, EffectiveInboundResult, compute_effective_inbound
from .inventory_calculation import (
    INVENTORY_RULE_ID,
    InventoryCalculationResult,
    compute_opening_usable_inventory,
)
from .layer2 import Layer2Report, validate_layer2
from .loader import load_package_from_paths
from .procurement_policy_input import (
    PROCUREMENT_POLICY_INPUT_STAGE,
    ProcurementPolicyInputResult,
    compute_procurement_policy_input,
)
from .procurement_recommendation import (
    PROCUREMENT_RECOMMENDATION_RULE_ID,
    ProcurementRecommendationResult,
    compute_procurement_recommendation,
)
from .report import ImportReport
from .requirement_calculation import (
    RULE_ID as REQUIREMENT_RULE_ID,
    RequirementCalculationResult,
    compute_requirement_calculation,
)
from .shortage_calculation import (
    SHORTAGE_RULE_ID,
    ShortageCalculationResult,
    compute_shortage,
)
from .substitute_calculation import (
    SUBSTITUTE_RULE_ID,
    SubstituteCalculationResult,
    compute_substitute_supply,
)
from .supplier_risk_calculation import (
    SUPPLIER_RISK_STAGE,
    SupplierRiskResult,
    compute_supplier_risk,
)
from .supplier_risk_input import (
    SUPPLIER_RISK_INPUT_STAGE,
    SupplierRiskInputResult,
    compute_supplier_risk_input,
)

#: Stage names.  A stage name identifies the **module responsibility** of ``§10.1`` B; it
#: is never a rule id and never a business status.  ``PIPELINE_STAGES`` pairs each stage
#: with the rule id ／ stage literal its own module already registers.
STAGE_SNAPSHOT_LOADER: str = "SNAPSHOT_LOADER"
STAGE_LAYER2: str = "LAYER2_VALIDATION"
STAGE_CANONICAL_OBJECTS: str = "CANONICAL_OBJECT_CONSTRUCTION"
STAGE_REQUIREMENT: str = "REQUIREMENT_CALCULATION"
STAGE_INVENTORY: str = "INVENTORY_CALCULATION"
STAGE_INBOUND: str = "EFFECTIVE_INBOUND"
STAGE_SUBSTITUTE: str = "SUBSTITUTE_SUPPLY"
STAGE_SHORTAGE: str = "SHORTAGE_CALCULATION"
STAGE_PROCUREMENT_POLICY_INPUT: str = "PROCUREMENT_POLICY_INPUT"
STAGE_PROCUREMENT_RECOMMENDATION: str = "PROCUREMENT_RECOMMENDATION"
STAGE_SUPPLIER_RISK_INPUT_SEAM: str = "SUPPLIER_RISK_INPUT_SEAM"
STAGE_SUPPLIER_RISK_EVIDENCE: str = "SUPPLIER_RISK_EVIDENCE"

#: The registered composition, in canonical order: ``(stage, rule id ／ stage literal)``.
#: The rule ids are the ones each module already registers -- this table mints no new
#: literal and defines no new ordering of its own (``§10.1`` B ／ ``§4.3.31`` F).
PIPELINE_STAGES: tuple[tuple[str, str | None], ...] = (
    (STAGE_SNAPSHOT_LOADER, None),
    (STAGE_LAYER2, None),
    (STAGE_CANONICAL_OBJECTS, None),
    (STAGE_REQUIREMENT, REQUIREMENT_RULE_ID),
    (STAGE_INVENTORY, INVENTORY_RULE_ID),
    (STAGE_INBOUND, INBOUND_RULE_ID),
    (STAGE_SUBSTITUTE, SUBSTITUTE_RULE_ID),
    (STAGE_SHORTAGE, SHORTAGE_RULE_ID),
    (STAGE_PROCUREMENT_POLICY_INPUT, PROCUREMENT_POLICY_INPUT_STAGE),
    (STAGE_PROCUREMENT_RECOMMENDATION, PROCUREMENT_RECOMMENDATION_RULE_ID),
    (STAGE_SUPPLIER_RISK_INPUT_SEAM, SUPPLIER_RISK_INPUT_STAGE),
    (STAGE_SUPPLIER_RISK_EVIDENCE, SUPPLIER_RISK_STAGE),
)

#: Why no downstream stage is entered when Layer 1 did not accept the package.
LAYER1_NOT_ACCEPTED_REASON: str = (
    "the package was not ACCEPTED, so no Analysis Run exists and no downstream "
    "deterministic stage is entered (§4.4.2 Layer 1 / IC-18)"
)

#: Why no downstream stage is entered when an accepted report carries no package.
LAYER1_PACKAGE_MISSING_REASON: str = (
    "the Layer-1 report states ACCEPTED but carries no accepted package, so no Analysis "
    "Run binding can be established and no downstream deterministic stage is entered"
)


@dataclass(frozen=True, slots=True)
class PipelineStage:
    """One pipeline stage's **execution** record -- never a business status.

    ``entered`` is an execution fact: the stage's registered entry point was called for
    this invocation.  ``note`` states why it was not entered, and is empty when it was.
    A stage that was entered may still yield any registered business outcome, including
    the inherited fail-closed ones; that outcome is expressed by the stage result itself
    and is never summarised here.
    """

    name: str
    rule_id: str | None
    entered: bool
    note: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "rule_id": self.rule_id,
            "entered": self.entered,
            "note": self.note,
        }


@dataclass(frozen=True, slots=True)
class FirstTranchePipelineResult:
    """The whole first-tranche composition result for one invocation.

    Every stage result is the registered result object of its own module, propagated
    **verbatim** (the same object, never a copy, a re-serialisation or a re-derivation).
    A stage whose entry point was not called is ``None`` and is also marked
    ``entered=False`` in :attr:`stages`.

    The Analysis Run ／ accepted-package binding is the one the Phase A construction
    established: :attr:`analysis_run` is that exact context and
    ``analysis_run is None`` exactly when no construction happened.
    """

    import_report: ImportReport
    stages: tuple[PipelineStage, ...]
    layer2: Layer2Report | None = None
    construction: CanonicalConstructionReport | None = None
    requirements: RequirementCalculationResult | None = None
    inventory: InventoryCalculationResult | None = None
    inbounds: EffectiveInboundResult | None = None
    substitutes: SubstituteCalculationResult | None = None
    shortage: ShortageCalculationResult | None = None
    procurement_policy_input: ProcurementPolicyInputResult | None = None
    procurement_recommendation: ProcurementRecommendationResult | None = None
    supplier_risk_input: SupplierRiskInputResult | None = None
    supplier_risk: SupplierRiskResult | None = None

    @property
    def accepted(self) -> bool:
        """Whether this invocation's Layer-1 attempt accepted the package."""

        return self.import_report.accepted

    @property
    def analysis_run(self) -> AnalysisRunContext | None:
        """The Analysis Run context of the Phase A construction, or ``None`` when it ran not."""

        return None if self.construction is None else self.construction.analysis_run

    @property
    def accepted_package_id(self) -> str | None:
        package = self.import_report.accepted_package
        return None if package is None else package.package_id

    @property
    def accepted_content_view_digest(self) -> str | None:
        package = self.import_report.accepted_package
        return None if package is None else package.content_view_digest

    def stage(self, name: str) -> PipelineStage:
        """The execution record of one registered stage."""

        for entry in self.stages:
            if entry.name == name:
                return entry
        raise KeyError(name)

    def to_dict(self) -> dict[str, object]:
        """Stable serialization: identical invocation input => identical payload."""

        return {
            "accepted": self.accepted,
            "accepted_package_id": self.accepted_package_id,
            "accepted_content_view_digest": self.accepted_content_view_digest,
            "analysis_run": _analysis_run_payload(self.analysis_run),
            "stages": [entry.to_dict() for entry in self.stages],
            "import": self.import_report.to_dict(),
            "layer2": _payload(self.layer2),
            "construction": _payload(self.construction),
            "requirements": _payload(self.requirements),
            "inventory": _payload(self.inventory),
            "inbounds": _payload(self.inbounds),
            "substitutes": _payload(self.substitutes),
            "shortage": _payload(self.shortage),
            "procurement_policy_input": _payload(self.procurement_policy_input),
            "procurement_recommendation": _payload(self.procurement_recommendation),
            "supplier_risk_input": _payload(self.supplier_risk_input),
            "supplier_risk": _payload(self.supplier_risk),
        }


def run_first_tranche_pipeline(
    import_report: ImportReport,
    handoff: PhaseAHandoff,
) -> FirstTranchePipelineResult:
    """Compose the registered first-tranche stages over one Layer-1 attempt.

    ``import_report`` is the completed Layer-1 attempt (accepted or not) and ``handoff``
    is the registered in-process logical handoff (``§4.3.31`` E ／ G) built from evidence
    of the same accepted package.  Not accepted: nothing downstream is entered and the
    Layer-1 outcome is returned unchanged.
    """

    accepted = import_report.accepted_package
    if not import_report.accepted or accepted is None:
        reason = (
            LAYER1_NOT_ACCEPTED_REASON
            if not import_report.accepted
            else LAYER1_PACKAGE_MISSING_REASON
        )
        return FirstTranchePipelineResult(
            import_report=import_report,
            stages=_stages(entered_downstream=False, reason=reason),
        )

    # Layer 2 -- canonical evidence validation (the report is passed on so Phase A can
    # trust the very same accepted content view instead of re-deriving it).
    layer2 = validate_layer2(accepted)

    # Phase A -- canonical objects, from the accepted package plus the registered handoff.
    construction = construct_canonical_objects(accepted, handoff, layer2_report=layer2)

    # The four supply-side deterministic rules over the same construction.
    requirements = compute_requirement_calculation(construction)
    inventory = compute_opening_usable_inventory(construction)
    inbounds = compute_effective_inbound(construction, requirements)
    substitutes = compute_substitute_supply(
        construction, inventory, requirements=requirements
    )

    # Shortage classification, then the Phase B procurement-context resolution.
    shortage = compute_shortage(
        construction, requirements, inbounds, inventory, substitutes
    )
    policy_input = compute_procurement_policy_input(
        construction, shortage, accepted=accepted
    )
    recommendation = compute_procurement_recommendation(
        construction, shortage, policy_input
    )

    # The supplier-side seam (A′) and the registered risk-evidence rule over it.
    risk_input = compute_supplier_risk_input(
        construction, recommendation, accepted=accepted
    )
    risk = compute_supplier_risk(risk_input)

    return FirstTranchePipelineResult(
        import_report=import_report,
        stages=_stages(entered_downstream=True, reason=""),
        layer2=layer2,
        construction=construction,
        requirements=requirements,
        inventory=inventory,
        inbounds=inbounds,
        substitutes=substitutes,
        shortage=shortage,
        procurement_policy_input=policy_input,
        procurement_recommendation=recommendation,
        supplier_risk_input=risk_input,
        supplier_risk=risk,
    )


def run_first_tranche_pipeline_from_paths(
    package_dir: os.PathLike[str] | str,
    trusted_root: os.PathLike[str] | str,
    handoff: PhaseAHandoff,
) -> FirstTranchePipelineResult:
    """Convenience wrapper: run Layer 1 from a configured boundary, then compose.

    This is the only entry point that touches the filesystem, and it does so through the
    registered Layer-1 loader (:func:`~snapshot_loader.loader.load_package_from_paths`)
    with an explicitly configured trusted package-input boundary (``§4.3.28`` D.3
    ``IG-self-C`` ／ ADR-001).
    """

    return run_first_tranche_pipeline(
        load_package_from_paths(package_dir, trusted_root), handoff
    )


def _stages(*, entered_downstream: bool, reason: str) -> tuple[PipelineStage, ...]:
    """The stage execution records of one invocation.

    The Layer-1 stage is always ``entered``: an :class:`ImportReport` only exists because
    a Layer-1 attempt was made.
    """

    entries: list[PipelineStage] = []
    for index, (name, rule_id) in enumerate(PIPELINE_STAGES):
        if index == 0 or entered_downstream:
            entries.append(PipelineStage(name=name, rule_id=rule_id, entered=True))
        else:
            entries.append(
                PipelineStage(name=name, rule_id=rule_id, entered=False, note=reason)
            )
    return tuple(entries)


def _analysis_run_payload(context: AnalysisRunContext | None) -> dict[str, object] | None:
    """The existing Analysis Run components, read back for serialization only."""

    if context is None:
        return None
    return {
        "analysis_run_id": context.analysis_run_id,
        "analysis_date": context.analysis_date,
        "snapshot_package_identity": context.snapshot_package_identity,
        "accepted_content_view_digest": context.accepted_content_view_digest,
    }


def _payload(result: Any) -> dict[str, object] | None:
    """A stage result's own registered serialization, or ``None`` when it did not run."""

    return None if result is None else result.to_dict()


__all__ = [
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
]
