"""Imported-package report model.

The report expresses the registered Layer-1 outcome vocabulary only:

* disposition ``ACCEPTED`` / ``REJECTED`` / ``UNUSABLE`` (``§4.3.28`` B.1 ``RD-B``);
* ``not evaluable`` when a required prerequisite could not be established at all
  (``§4.3.28`` C.2 ``Decision 10A`` and D.4 ``FR-3``) -- such an attempt is reported
  as fail-closed and is **never** silently treated as passed.
"""

from __future__ import annotations

from dataclasses import dataclass

from .constants import DISPOSITION_ACCEPTED, DISPOSITION_REJECTED
from .issues import Issue, IssueCollector
from .trust import AcceptedPackage, ContentView


@dataclass(frozen=True, slots=True)
class ImportReport:
    """Deterministic result of one Layer-1 acceptance attempt."""

    disposition: str
    evaluable: bool
    collector: IssueCollector
    accepted_package: AcceptedPackage | None
    content_view: ContentView | None
    disposition_basis: str

    @property
    def accepted(self) -> bool:
        return self.disposition == DISPOSITION_ACCEPTED

    @property
    def rejected(self) -> bool:
        return self.disposition == DISPOSITION_REJECTED

    @property
    def not_evaluable(self) -> bool:
        return not self.evaluable

    @property
    def issues(self) -> tuple[Issue, ...]:
        return self.collector.sorted_issues()

    def to_dict(self) -> dict[str, object]:
        return {
            "disposition": self.disposition,
            "evaluable": self.evaluable,
            "disposition_basis": self.disposition_basis,
            "content_view_digest": (
                self.content_view.digest if self.content_view is not None else None
            ),
            "accepted_package": (
                self.accepted_package.to_dict()
                if self.accepted_package is not None
                else None
            ),
            "issues": [issue.to_dict() for issue in self.issues],
            "checks": [check.to_dict() for check in self.collector.sorted_checks()],
        }

    def render_text(self) -> str:
        """Human-inspectable rendering (``I-19`` / ``§4.4.79`` dimensions)."""

        lines = [
            f"disposition      : {self.disposition}",
            f"evaluable        : {self.evaluable}",
            f"basis            : {self.disposition_basis}",
        ]
        if self.content_view is not None:
            lines.append(f"content view     : {self.content_view.digest}")
        if self.accepted_package is not None:
            lines.append(f"package id       : {self.accepted_package.package_id}")
            lines.append(f"contract version : {self.accepted_package.contract_version}")
        lines.append(f"issues           : {len(self.issues)}")
        for issue in self.issues:
            lines.append(
                f"  - [{issue.category}/{issue.reason}] {issue.location}: {issue.detail}"
            )
        not_evaluable = [
            check for check in self.collector.sorted_checks() if check.state == "not_evaluable"
        ]
        if not_evaluable:
            lines.append(f"not evaluable    : {len(not_evaluable)} check(s)")
            for check in not_evaluable:
                lines.append(f"  - {check.name}: {check.note}")
        return "\n".join(lines)
