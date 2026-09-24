"""Deterministic Layer-1 issue reporting.

The issue shape follows the **inherited** conceptual dimensions of
``data-validation.md`` §4.4.79 and the **inherited** taxonomy of §4.4.80/§4.4.81.

POC v0.2 Layer 1 uses exactly one canonical pair:

    Category : ``PACKAGE_STRUCTURE``
    Reason   : ``STRUCTURAL_INCONSISTENCY``

No additional category, reason, status enum, or package disposition literal may be
introduced here (``IC-20``/``IC-21``, ``§4.3.28`` B.2 ``FR-3``).  Human-readable
``detail`` is the only free-text surface.

``§4.3.28`` B.2 ``FR-3`` requires *collect-all* reporting **within the reachable
prerequisite range** and an explicit distinction between an ``evaluated`` check and
a check that is ``not evaluable due to prerequisite``.  Both are represented here:
:class:`Issue` carries the reachable defects, and :class:`Check` records every
check that was attempted together with its evaluation state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .constants import (
    CATEGORY_PACKAGE_STRUCTURE,
    EVALUATION_FAILED,
    EVALUATION_NOT_EVALUABLE,
    EVALUATION_PASSED,
    LAYER_1,
    REASON_STRUCTURAL_INCONSISTENCY,
)


@dataclass(frozen=True, slots=True)
class Issue:
    """One deterministically reachable Layer-1 structural defect."""

    location: str
    detail: str
    category: str = CATEGORY_PACKAGE_STRUCTURE
    reason: str = REASON_STRUCTURAL_INCONSISTENCY
    layer: int = LAYER_1
    affected_evidence: str | None = None
    blast_radius: str | None = None
    design_reference: str | None = None
    consequence_context: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "layer": self.layer,
            "category": self.category,
            "reason": self.reason,
            "location": self.location,
            "detail": self.detail,
            "affected_evidence": self.affected_evidence,
            "blast_radius": self.blast_radius,
            "design_reference": self.design_reference,
            "consequence_context": self.consequence_context,
        }

    def sort_key(self) -> tuple[object, ...]:
        return (
            self.layer,
            self.category,
            self.reason,
            self.location,
            self.detail,
            self.affected_evidence or "",
            self.blast_radius or "",
            self.design_reference or "",
            self.consequence_context or "",
        )


@dataclass(frozen=True, slots=True)
class Check:
    """One named Layer-1 check and its evaluation state.

    ``state`` is one of :data:`~snapshot_loader.constants.EVALUATION_PASSED`,
    :data:`~snapshot_loader.constants.EVALUATION_FAILED`, or
    :data:`~snapshot_loader.constants.EVALUATION_NOT_EVALUABLE`.
    """

    name: str
    state: str
    note: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "state": self.state, "note": self.note}

    def sort_key(self) -> tuple[object, ...]:
        return (self.name, self.state, self.note or "")


@dataclass(frozen=True, slots=True)
class IssueCollector:
    """Accumulates issues and check states during one acceptance attempt."""

    issues: tuple[Issue, ...] = ()
    checks: tuple[Check, ...] = ()

    def issue(self, location: str, detail: str, **kwargs: object) -> "IssueCollector":
        new = Issue(location=location, detail=detail, **kwargs)  # type: ignore[arg-type]
        return IssueCollector(issues=self.issues + (new,), checks=self.checks)

    def issue_many(
        self, entries: Iterable[tuple[str, str]], **kwargs: object
    ) -> "IssueCollector":
        collector = self
        for location, detail in entries:
            collector = collector.issue(location, detail, **kwargs)
        return collector

    def check(self, name: str, state: str, note: str | None = None) -> "IssueCollector":
        new = Check(name=name, state=state, note=note)
        return IssueCollector(issues=self.issues, checks=self.checks + (new,))

    def passed(self, name: str) -> "IssueCollector":
        return self.check(name, EVALUATION_PASSED)

    def failed(self, name: str, note: str | None = None) -> "IssueCollector":
        return self.check(name, EVALUATION_FAILED, note)

    def not_evaluable(self, name: str, note: str) -> "IssueCollector":
        return self.check(name, EVALUATION_NOT_EVALUABLE, note)

    def sorted_issues(self) -> tuple[Issue, ...]:
        return tuple(sorted(self.issues, key=Issue.sort_key))

    def sorted_checks(self) -> tuple[Check, ...]:
        return tuple(sorted(self.checks, key=Check.sort_key))
