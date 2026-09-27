"""Cross-result Analysis Run binding for the deterministic rule chain.

**``F3-RB1`` ／ ``Option A′`` (Human Decision, ``APPROVED``).**

The existing provenance authority states that a derived result's provenance is
``Analysis Run + Deterministic Rule ID + Upstream Canonical References ／ Contexts``, and that a
canonical input whose provenance points at a wrong ／ incompatible Analysis Context is
``PROVENANCE`` ／ ``PROVENANCE_MISMATCH`` and is never silently used
(``master-data-mapping.md`` Derived Result Provenance ／ Cross-Package Boundary;
``data-validation.md`` ``§4.4.93`` ／ ``§4.4.80`` ／ ``§4.4.81``;
``snapshot-import-contract.md`` ``§4.3.31`` G I-1).

This module is the **minimal runtime seam** of that contract.  Every deterministic rule result
carries the existing :class:`~snapshot_loader.canonical_objects.AnalysisRunContext` of the
construction it was produced from, and a rule that consumes an upstream deterministic result
verifies that binding **before** it consumes any business value:

``upstream_result.analysis_run == construction.analysis_run``

A mismatch **rejects the current rule invocation**: no foreign business value is consumed, no
business grain is manufactured and no ``NORMAL`` ／ ``SHORTAGE`` ／ numeric business result is
returned.  The rejection is an invocation-level provenance failure, not a grain defect: it is
**never** reported as a grain's ``DATA_INCOMPLETE`` and never converted into
``CONSISTENCY`` ／ ``CONSISTENCY_CONFLICT``.

Two root conditions stay distinct, exactly as the canonical taxonomy registers them:

* ``PROVENANCE`` ／ ``PROVENANCE_UNRESOLVED`` -- the upstream result carries **no** Analysis Run
  binding at all, so the required package-scoped linkage cannot be reliably established;
* ``PROVENANCE`` ／ ``PROVENANCE_MISMATCH`` -- the linkage **is** established but points at a wrong ／
  incompatible Analysis Context (a different ``analysis_run_id``, ``snapshot_package_identity``,
  ``accepted_content_view_digest`` or ``analysis_date``).

Nothing else is introduced: no provenance service, no result registry, no persistence, no new
canonical entity, no new business grain, no UUID scheme and no new taxonomy.
"""

from __future__ import annotations

from typing import Any

from .canonical_objects import AnalysisRunContext
from .constants import (
    CATEGORY_PROVENANCE,
    LAYER_2,
    REASON_PROVENANCE_MISMATCH,
    REASON_PROVENANCE_UNRESOLVED,
)
from .issues import Issue

#: The Analysis Run components compared by :func:`require_same_analysis_run`.  The first three are
#: the ones the approved contract requires at minimum; ``analysis_date`` is part of the same
#: existing context, and the contract compares the whole context.
ANALYSIS_RUN_COMPONENTS: tuple[str, ...] = (
    "analysis_run_id",
    "snapshot_package_identity",
    "accepted_content_view_digest",
    "analysis_date",
)


class AnalysisRunBindingError(Exception):
    """Invocation-level rejection: an upstream deterministic result is not bound to this run.

    Carries the inherited ``PROVENANCE`` :class:`~snapshot_loader.issues.Issue` findings, so the
    caller sees the existing taxonomy rather than a new error code.  The rule that raised it
    consumed **no** upstream business value and produced **no** business result.
    """

    def __init__(self, issues: tuple[Issue, ...]) -> None:
        if not issues:  # pragma: no cover - defensive: a rejection always states a finding
            raise ValueError("AnalysisRunBindingError requires at least one Issue")
        self.issues = tuple(issues)
        super().__init__(
            "; ".join(
                f"[{issue.category}/{issue.reason}] {issue.detail}" for issue in self.issues
            )
        )

    @property
    def mismatch(self) -> bool:
        """Whether this rejection is a mismatch (rather than an unestablished binding)."""

        return any(
            issue.reason == REASON_PROVENANCE_MISMATCH for issue in self.issues
        )

    @property
    def unresolved(self) -> bool:
        """Whether this rejection is an unestablished binding (rather than a mismatch)."""

        return any(
            issue.reason == REASON_PROVENANCE_UNRESOLVED for issue in self.issues
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "outcome": "INVOCATION_REJECTED",
            "category": CATEGORY_PROVENANCE,
            "issues": [issue.to_dict() for issue in self.issues],
        }


def _component_value(context: AnalysisRunContext | None, name: str) -> Any:
    return None if context is None else getattr(context, name, None)


def require_same_analysis_run(
    analysis_run: AnalysisRunContext | None,
    *upstream: tuple[str, AnalysisRunContext | None],
) -> None:
    """Reject the invocation unless every upstream result is bound to ``analysis_run``.

    ``upstream`` is one ``(rule_id, upstream_result.analysis_run)`` pair per consumed upstream
    deterministic result.  All findings are collected before raising, so a caller that combined
    several foreign results sees every one of them; the rule consumes nothing either way.

    The check is a pure comparison of the existing :class:`AnalysisRunContext` values: it reads no
    business value, recomputes no upstream rule and repairs nothing.
    """

    issues: list[Issue] = []
    for rule_id, upstream_run in upstream:
        location = f"result_binding[{rule_id}]"
        if upstream_run is None:
            issues.append(
                Issue(
                    location=location,
                    detail=(
                        f"the {rule_id} result carries no Analysis Run binding, so the required "
                        "package-scoped provenance linkage between it and this rule's own "
                        "construction cannot be reliably established; the result is never consumed "
                        "and its business values are never used (PROVENANCE_UNRESOLVED is distinct "
                        "from PROVENANCE_MISMATCH: an absent linkage is not a wrong linkage)"
                    ),
                    category=CATEGORY_PROVENANCE,
                    reason=REASON_PROVENANCE_UNRESOLVED,
                    layer=LAYER_2,
                    affected_evidence=rule_id,
                    blast_radius="the whole rule invocation (no result is produced)",
                    design_reference=(
                        "master-data-mapping.md Derived Result Provenance / data-validation.md "
                        "§4.4.80 / §4.4.81 (F3-RB1 Option A′)"
                    ),
                    consequence_context=(
                        "the invocation is rejected, no upstream business value is consumed and no "
                        "business result is produced"
                    ),
                )
            )
            continue
        differing = tuple(
            name
            for name in ANALYSIS_RUN_COMPONENTS
            if _component_value(upstream_run, name) != _component_value(analysis_run, name)
        )
        if not differing:
            continue
        issues.append(
            Issue(
                location=location,
                detail=(
                    f"the {rule_id} result belongs to a different Analysis Run context: "
                    f"{', '.join(differing)} differ(s) from this rule's construction "
                    f"(upstream {_render(upstream_run)} vs current {_render(analysis_run)}); a "
                    "foreign, stale or mismatched upstream result is never silently combined, and "
                    "no cross-package or cross-run fallback exists"
                ),
                category=CATEGORY_PROVENANCE,
                reason=REASON_PROVENANCE_MISMATCH,
                layer=LAYER_2,
                affected_evidence=rule_id,
                blast_radius="the whole rule invocation (no result is produced)",
                design_reference=(
                    "master-data-mapping.md Derived Result Provenance / Cross-Package Boundary / "
                    "data-validation.md §4.4.80 / §4.4.81 (F3-RB1 Option A′)"
                ),
                consequence_context=(
                    "the invocation is rejected, no upstream business value is consumed and no "
                    "business result is produced"
                ),
            )
        )
    if issues:
        raise AnalysisRunBindingError(tuple(issues))


def require_same_accepted_package(
    analysis_run: AnalysisRunContext | None,
    *,
    package_id: Any,
    accepted_content_view_digest: Any,
    label: str = "accepted package",
) -> None:
    """Reject the invocation unless ``label`` is the Analysis Run's own accepted package.

    The provenance contract binds one Analysis Run to **exactly one** accepted Snapshot Package and
    one accepted content view (``§4.3.31`` E ／ ``§4.4.68``): evidence whose package identity or
    accepted-content-view digest differs from the Analysis Run's own is a foreign ／ stale evidence
    source and is never consumed.  Phase B consumption of accepted role-12 evidence uses this check,
    because that seam reads the accepted package directly rather than through a Phase A report.

    Both root conditions keep their existing taxonomy: a missing Analysis Run binding is
    ``PROVENANCE`` ／ ``PROVENANCE_UNRESOLVED``, a mismatch is ``PROVENANCE`` ／
    ``PROVENANCE_MISMATCH``, and the invocation is rejected either way.
    """

    issues: list[Issue] = []
    if analysis_run is None:
        issues.append(
            Issue(
                location=f"result_binding[{label}]",
                detail=(
                    f"this invocation carries no Analysis Run binding, so the required "
                    f"package-scoped linkage between the {label} and the Analysis Run it is used "
                    "for cannot be reliably established; the evidence is never consumed "
                    "(PROVENANCE_UNRESOLVED is distinct from PROVENANCE_MISMATCH)"
                ),
                category=CATEGORY_PROVENANCE,
                reason=REASON_PROVENANCE_UNRESOLVED,
                layer=LAYER_2,
                affected_evidence=label,
                blast_radius="the whole rule invocation (no result is produced)",
                design_reference=(
                    "§4.3.31 E ／ §4.4.68 / master-data-mapping.md Cross-Package Boundary "
                    "(F3-RB1 Option A′)"
                ),
                consequence_context=(
                    "the invocation is rejected, no accepted evidence is consumed and no business "
                    "result is produced"
                ),
            )
        )
    else:
        differing = tuple(
            name
            for name, supplied in (
                ("snapshot_package_identity", package_id),
                ("accepted_content_view_digest", accepted_content_view_digest),
            )
            if supplied != _component_value(analysis_run, name)
        )
        if differing:
            issues.append(
                Issue(
                    location=f"result_binding[{label}]",
                    detail=(
                        f"the {label} is not this Analysis Run's own accepted package: "
                        f"{', '.join(differing)} differ(s) from the Analysis Run context "
                        f"(current {_render(analysis_run)}); foreign or stale accepted evidence is "
                        "never silently combined and no cross-package or cross-content-view "
                        "fallback exists"
                    ),
                    category=CATEGORY_PROVENANCE,
                    reason=REASON_PROVENANCE_MISMATCH,
                    layer=LAYER_2,
                    affected_evidence=label,
                    blast_radius="the whole rule invocation (no result is produced)",
                    design_reference=(
                        "§4.3.31 E ／ §4.4.68 / master-data-mapping.md Cross-Package Boundary "
                        "(F3-RB1 Option A′)"
                    ),
                    consequence_context=(
                        "the invocation is rejected, no accepted evidence is consumed and no "
                        "business result is produced"
                    ),
                )
            )
    if issues:
        raise AnalysisRunBindingError(tuple(issues))


def _render(context: AnalysisRunContext | None) -> str:
    if context is None:
        return "<no Analysis Run binding>"
    return (
        f"[analysis_run_id={context.analysis_run_id!r} "
        f"snapshot_package_identity={context.snapshot_package_identity!r} "
        f"accepted_content_view_digest={_short(context.accepted_content_view_digest)} "
        f"analysis_date={context.analysis_date!r}]"
    )


def _short(value: Any) -> str:
    if not isinstance(value, str):
        return repr(value)
    return value if len(value) <= 12 else f"{value[:12]}…"


__all__ = [
    "ANALYSIS_RUN_COMPONENTS",
    "AnalysisRunBindingError",
    "require_same_accepted_package",
    "require_same_analysis_run",
]
