"""Layer 2 -- Canonical Evidence Validation (narrowed non-null present-value subset).

This module implements **only** what Issue #122 authorises:

```
Layer 1 = Package Structural Validation        (delivered; not re-implemented here)
Layer 2 = Canonical Evidence Validation        (this module, non-null present values)
Layer 3 = Capability Readiness Validation      NOT IN SCOPE
Layer 4 = Business Rules                       NOT IN SCOPE
```

Scope actually implemented (``§4.4.24`` ／ ``§4.4.25`` ／ ``§4.4.26`` -- ``§4.4.35``):

* logical type and registered scalar representation (``§4.3.22`` ``C-3`` -- ``C-10``),
  including whether a lexically well-formed ``DATE`` ／ ``TIMESTAMP`` denotes a real
  calendar date ／ instant with an explicit offset;
* approved numeric range -- from the field's own registered bound
  (``§4.2.13`` ／ the field's Data Dictionary row) or from its registered logical type,
  and never from a widened type;
* approved **canonical** status vocabulary;
* identifier exact-opaque-string / non-empty boundary;
* deterministic issue collection using only the inherited taxonomy
  (``§4.4.80`` 8 categories ／ ``§4.4.81`` 12 reasons).

Boundaries that are deliberately **not** crossed:

* an accepted package is never rejected here; a field-level issue only limits the
  affected evidence / grain (``§4.4.25``, ``IC-17``);
* **property omission** never produces ``MISSING`` -- per-role field applicability and
  the ``POLICY_INPUT`` ／ ``CONTEXT`` input channel are deferred by ``§4.3.30``;
* **JSON ``null``** keeps its ``C-2`` meaning (explicit missing ／ unavailable) but its
  missingness is **not** decided here, and it is never misread as ``INVALID_TYPE``;
* deferred value-level rules (``PerformancePeriod``, ``sourcing_status``) are reported
  ``not evaluable`` -- but their **representation** is still decided first, because
  ``§4.3.22`` applies to every present serialized value;
* no past/future date rejection, no planning horizon, no freshness threshold and no
  business-timezone policy (``C-4`` registers ``business timezone policy = NOT
  DEFINED``, and ``C-3`` forbids introducing a freshness threshold);
* no per-role whitelist, dataset schema or input-channel policy is invented;
* no capability readiness, no business rule, no cross-field ／ cross-dataset
  consistency, no provenance ／ semantic resolution;
* no new category, reason, severity or error code is introduced.

Trusted reuse (``§4.3.28`` C.2 ／ C.3): Layer 2 validates the accepted content view
that ``AcceptedPackage`` captured at acceptance time.  Required integrity is
re-verified first; if mutation is detected or required integrity can no longer be
re-established the package becomes ``UNUSABLE`` and normal Layer-2 validation does
**not** continue.  Changed files are never re-read and treated as accepted evidence.
The resulting re-verification findings are **inherited**, not produced here: they are
re-published on :attr:`Layer2Report.inherited_issues` with their original layer,
category, reason, location, affected evidence, blast radius and design reference.
"""

from __future__ import annotations

import datetime as _datetime
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from .constants import (
    CATEGORY_FIELD_VALUE,
    CATEGORY_IDENTITY_RESOLUTION,
    DATE_PATTERN,
    DECIMAL_STRING_PATTERN,
    DISPOSITION_ACCEPTED,
    DISPOSITION_UNUSABLE,
    EVALUATION_FAILED,
    EVALUATION_NOT_EVALUABLE,
    EVALUATION_PASSED,
    KIND_ANALYSIS_RUN_ID,
    KIND_DATE,
    KIND_DECIMAL,
    KIND_IDENTIFIER,
    KIND_NON_NEGATIVE,
    KIND_PERCENTAGE,
    KIND_RATIO,
    KIND_STATUS,
    KIND_TEXT_CONTEXT,
    KIND_TIMESTAMP,
    LAYER_2,
    LAYER2_FIELD_RULE_BY_NAME,
    LAYER2_NOT_EVALUABLE_FIELDS,
    LAYER2_REGISTRY,
    LAYER2_REUSABLE,
    LAYER2_UNUSABLE,
    REASON_INVALID_DEFINED_STATUS,
    REASON_INVALID_TYPE,
    REASON_OUT_OF_DEFINED_RANGE,
    REASON_UNRESOLVED_IDENTITY,
    TIMESTAMP_PATTERN,
    V02_CANONICAL_RECORD_PROPERTY_SET,
    Layer2FieldRule,
)
from .issues import Issue, IssueCollector
from .strict_json import JsonObject, StrictJsonError, parse_strict_json
from .trust import AcceptedPackage

_DATE_RE = re.compile(rf"^{DATE_PATTERN}$")
_TIMESTAMP_RE = re.compile(rf"^{TIMESTAMP_PATTERN}$")
_DECIMAL_RE = re.compile(rf"^{DECIMAL_STRING_PATTERN}$")

LAYER2_REVERIFICATION = "layer2.trusted_reuse_reverification"
LAYER2_ACCEPTED_VIEW_BINDING = "layer2.accepted_view_binding"
LAYER2_RECORD_CARRIER = "layer2.record_carrier_prerequisite"
LAYER2_PRESENT_VALUE_RULES = "layer2.present_value_field_rules"


@dataclass(frozen=True, slots=True)
class Layer2Check:
    """One Layer-2 check and its evaluation state.

    ``state`` is ``passed``, ``failed``, or ``not_evaluable``.  ``not_evaluable`` is
    used for checks whose prerequisite is not reachable and for fields whose
    present-value rules are deliberately deferred -- it is **never** a silent pass.
    """

    name: str
    state: str
    note: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "state": self.state, "note": self.note}

    def sort_key(self) -> tuple[object, ...]:
        return (self.name, self.state, self.note or "")


@dataclass(frozen=True, slots=True)
class Layer2Report:
    """Deterministic Layer-2 validation result for one accepted package.

    ``disposition`` restates the package disposition only: Layer 2 never changes it
    (``§4.4.25``).  The single exception is the inherited trusted-reuse failure, which
    is expressed as ``UNUSABLE`` per ``§4.3.28`` C.3 ``MG-2``.

    ``inherited_issues`` carries defects that Layer 2 **did not produce** -- currently
    the ``MG-2`` re-verification findings raised by the trusted-reuse boundary.  They
    are re-published with their original layer, category, reason, location, affected
    evidence, blast radius and design reference intact, because Layer 2 is not the
    layer that established them and must not rewrite their meaning.
    """

    package_id: str
    disposition: str
    outcome: str
    evaluation: str
    collector: IssueCollector
    accepted_content_view_digest: str
    note: str = ""
    inherited_issues: tuple[Issue, ...] = ()

    @property
    def reusable(self) -> bool:
        return self.outcome == LAYER2_REUSABLE

    @property
    def unusable(self) -> bool:
        return self.disposition == DISPOSITION_UNUSABLE

    @property
    def accepted(self) -> bool:
        return self.disposition == DISPOSITION_ACCEPTED

    @property
    def issues(self) -> tuple[Issue, ...]:
        return self.collector.sorted_issues()

    @property
    def all_issues(self) -> tuple[Issue, ...]:
        """Layer-2 defects together with the inherited ones, deterministically ordered."""

        return tuple(
            sorted(self.issues + self.inherited_issues, key=Issue.sort_key)
        )

    @property
    def checks(self) -> tuple[Layer2Check, ...]:
        return self.collector.sorted_checks()

    @property
    def not_evaluable_checks(self) -> tuple[Layer2Check, ...]:
        return tuple(
            check for check in self.checks if check.state == EVALUATION_NOT_EVALUABLE
        )

    def issues_for(self, *, category: str) -> tuple[Issue, ...]:
        return tuple(issue for issue in self.issues if issue.category == category)

    def to_dict(self) -> dict[str, object]:
        return {
            "package_id": self.package_id,
            "layer": LAYER_2,
            "disposition": self.disposition,
            "outcome": self.outcome,
            "evaluation": self.evaluation,
            "accepted_content_view_digest": self.accepted_content_view_digest,
            "note": self.note,
            "issues": [issue.to_dict() for issue in self.issues],
            "inherited_issues": [
                issue.to_dict() for issue in self.inherited_issues
            ],
            "checks": [check.to_dict() for check in self.checks],
        }

    def render_text(self) -> str:
        """Human-inspectable rendering (``§4.4.79`` dimensions)."""

        lines = [
            "layer            : 2 (Canonical Evidence Validation)",
            f"package id       : {self.package_id}",
            f"disposition      : {self.disposition}",
            f"outcome          : {self.outcome}",
            f"evaluation       : {self.evaluation}",
            f"accepted view    : {self.accepted_content_view_digest}",
        ]
        if self.note:
            lines.append(f"note             : {self.note}")
        lines.append(f"issues           : {len(self.issues)}")
        for issue in self.issues:
            lines.append(
                f"  - [{issue.category}/{issue.reason}] {issue.location}: {issue.detail}"
            )
        if self.inherited_issues:
            lines.append(f"inherited issues : {len(self.inherited_issues)}")
            for issue in self.inherited_issues:
                lines.append(
                    f"  - [layer {issue.layer} {issue.category}/{issue.reason}] "
                    f"{issue.location}: {issue.detail}"
                )
        undecided = self.not_evaluable_checks
        if undecided:
            lines.append(f"not evaluable    : {len(undecided)} check(s)")
            for check in undecided:
                lines.append(f"  - {check.name}: {check.note}")
        return "\n".join(lines)


class _Collector:
    """Mutable accumulator that yields the inherited issue / check shapes.

    Layer-2 issues are always **newly constructed** here (never re-labelled): a defect
    this layer cannot reach is reported as ``not evaluable`` instead.
    """

    def __init__(self) -> None:
        self.issues: list[Issue] = []
        self.checks: list[Layer2Check] = []

    def check(self, name: str, state: str, note: str | None = None) -> None:
        self.checks.append(Layer2Check(name=name, state=state, note=note))

    def passed(self, name: str) -> None:
        self.check(name, EVALUATION_PASSED)

    def failed(self, name: str, note: str | None = None) -> None:
        self.check(name, EVALUATION_FAILED, note)

    def not_evaluable(self, name: str, note: str) -> None:
        self.check(name, EVALUATION_NOT_EVALUABLE, note)

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
                blast_radius="affected evidence / grain only (no package rejection)",
                design_reference=design_reference,
                consequence_context=consequence_context,
            )
        )

    def collect(self) -> IssueCollector:
        return IssueCollector(
            issues=tuple(sorted(self.issues, key=Issue.sort_key)),
            checks=tuple(sorted(self.checks, key=Layer2Check.sort_key)),
        )


def _is_decimal(value: object) -> bool:
    """Is ``value`` a compliant base-10 decimal string (``C-5``)? """

    if not isinstance(value, str):
        return False
    if not _DECIMAL_RE.match(value):
        return False
    try:
        Decimal(value)
    except InvalidOperation:  # pragma: no cover - guarded by the pattern
        return False
    return True


def _as_decimal(value: object) -> Decimal | None:
    if not _is_decimal(value):
        return None
    return Decimal(value)  # type: ignore[arg-type]


def _date_defect(value: str) -> str | None:
    """Is ``value`` a **valid** ``DATE`` logical value?

    ``C-3`` registers the physical form ``YYYY-MM-DD``; the logical type ``DATE``
    declared in ``§4.2.2`` additionally requires the value to *be* a date.  The
    authority asks for a "valid `DATE`" (``§4.4.28`` ``required_date``), a "有效
    `DATE`" (``§4.4.30`` ``effective_arrival_date``) and a "valid `DATE` / `TIMESTAMP`
    logical value" (``§4.4.27`` ``AnalysisDate``), so a lexically well-formed but
    impossible calendar value is decidable here and is not ``INVALID_TYPE``-free.

    Only *internal* consistency is decided.  No past/future rejection, no planning
    horizon and no freshness threshold is applied (``§4.4.28`` explicitly leaves those
    undefined, and ``C-3`` forbids introducing a freshness threshold).
    """

    if not _DATE_RE.match(value):
        return f"DATE {value!r} is not in the registered YYYY-MM-DD form (C-3)"
    try:
        _datetime.date.fromisoformat(value)
    except ValueError:
        return f"DATE {value!r} matches the C-3 form but is not a valid calendar date"
    return None


def _timestamp_defect(value: str) -> str | None:
    """Is ``value`` a **valid** ``TIMESTAMP`` logical value with explicit offset?

    ``C-4`` registers "ISO 8601 / RFC 3339 compatible" plus an explicit UTC offset or
    ``Z``, and forbids silent timezone inference.  Logical validity here therefore
    means: the lexical shape is the registered one, the calendar/clock fields denote a
    real instant, and the offset is an explicit, syntactically valid one.

    ``C-4`` also registers ``business timezone policy = NOT DEFINED``: nothing here
    converts, compares or normalises the instant against any business timezone, and no
    freshness policy is introduced.
    """

    if not _TIMESTAMP_RE.match(value):
        return (
            f"TIMESTAMP {value!r} must be ISO 8601 / RFC 3339 compatible and carry an "
            "explicit UTC offset or 'Z' (C-4)"
        )

    # ``datetime`` requires a 'T' separator; RFC 3339 is case-insensitive for the
    # designators ('T'/'Z' may be lowercase) and permits a space only when both sides
    # agree on it as a simplification, which the registered form above already accepts.
    candidate = value
    if len(candidate) > 10:
        candidate = candidate[:10] + "T" + candidate[11:]
    if candidate.endswith(("Z", "z")):
        candidate = candidate[:-1] + "+00:00"

    try:
        parsed = _datetime.datetime.fromisoformat(candidate)
    except ValueError:
        return (
            f"TIMESTAMP {value!r} matches the C-4 form but does not denote a valid "
            "instant (impossible date, clock time or UTC offset)"
        )

    if parsed.tzinfo is None:  # pragma: no cover - guarded by the registered form
        return (
            f"TIMESTAMP {value!r} carries no explicit UTC offset or 'Z' (C-4); silent "
            "timezone inference is not allowed"
        )
    return None


def _representation_defect(rule: Layer2FieldRule, value: object) -> str | None:
    """Return a defect detail when ``value`` violates its registered representation.

    ``None`` means the representation is compliant.  Only ``§4.3.22`` ``C-3`` --
    ``C-10`` and the logical type registered in ``§4.2.2`` are applied here.
    """

    kind = rule.kind

    if kind in (KIND_IDENTIFIER, KIND_ANALYSIS_RUN_ID, KIND_TEXT_CONTEXT):
        if not isinstance(value, str):
            return (
                f"logical type {rule.logical_type} requires an exact JSON string "
                f"(C-10); got {type(value).__name__}"
            )
        if kind in (KIND_IDENTIFIER, KIND_ANALYSIS_RUN_ID) and value == "":
            # §4.4.26: an empty canonical identifier leaves the affected evidence
            # unresolved.  This is the only identity judgement in this tranche;
            # mapping a present identifier to a canonical identity stays deferred.
            return (
                "canonical identifier is present but empty; §4.4.26 treats an empty "
                "identifier as leaving the affected evidence unresolved"
            )
        return None

    if kind == KIND_DATE:
        if not isinstance(value, str):
            return f"DATE requires a JSON string in YYYY-MM-DD (C-3); got {type(value).__name__}"
        return _date_defect(value)

    if kind == KIND_TIMESTAMP:
        if not isinstance(value, str):
            return (
                f"TIMESTAMP requires a JSON string (C-4); got {type(value).__name__}"
            )
        return _timestamp_defect(value)

    if kind == KIND_STATUS:
        if not isinstance(value, str):
            return f"STATUS requires an exact JSON string (C-7); got {type(value).__name__}"
        return None

    # numeric kinds: DECIMAL_QUANTITY / NON_NEGATIVE_QUANTITY / RATIO / PERCENTAGE
    if not isinstance(value, str):
        return (
            f"logical type {rule.logical_type} requires a base-10 decimal string "
            f"(C-5); got {type(value).__name__}"
        )
    if not _is_decimal(value):
        return (
            f"value {value!r} is not a registered base-10 decimal string; binary "
            "floating point, locale separators, thousands separators and scientific "
            "notation are not permitted (C-5)"
        )
    return None


def _range_defect(rule: Layer2FieldRule, value: object) -> str | None:
    """Return a defect detail when a compliant numeric string is out of range.

    Bounds come from exactly two authorities, and neither broadens the other:

    * the field's own registered bound carried on :class:`Layer2FieldRule`
      (``bound_reference`` records where it came from);
    * the bound implied by the field's registered logical type
      (``NON_NEGATIVE_QUANTITY`` ``>= 0``, ``PERCENTAGE`` ``0`` -- ``100``).

    A field registered with a plain ``DECIMAL_QUANTITY`` logical type gets **no**
    implicit bound from that type; ``on_hand_qty`` is bounded only because its own Data
    Dictionary row defines the bound.  ``§4.4.24`` forbids inventing any other bound.
    """

    kind = rule.kind
    if kind not in (KIND_DECIMAL, KIND_NON_NEGATIVE, KIND_RATIO, KIND_PERCENTAGE):
        return None

    number = _as_decimal(value)
    if number is None:
        return None

    if rule.minimum is not None:
        minimum = Decimal(rule.minimum)
        below = number <= minimum if rule.minimum_exclusive else number < minimum
        if below:
            return (
                f"{rule.name} must satisfy "
                f"{'>' if rule.minimum_exclusive else '>='} {rule.minimum} "
                f"({rule.bound_authority}; {rule.bound_reference})"
            )

    if rule.maximum is not None:
        maximum = Decimal(rule.maximum)
        above = number >= maximum if rule.maximum_exclusive else number > maximum
        if above:
            return (
                f"{rule.name} must satisfy "
                f"{'<' if rule.maximum_exclusive else '<='} {rule.maximum} "
                f"({rule.bound_authority}; {rule.bound_reference})"
            )

    if rule.name == "loss_rate":
        # §4.2.13 / §4.4.28: 0 <= loss_rate < 1.
        if number < 0 or number >= 1:
            return "loss_rate must satisfy 0 <= loss_rate < 1 (§2.4.6 / §4.2.13 / §4.4.28)"
        return None

    if kind == KIND_PERCENTAGE:
        if number < 0 or number > 100:
            return "PERCENTAGE must satisfy 0 <= value <= 100 (§2.7.16 / §4.4.34)"
        return None

    if kind == KIND_NON_NEGATIVE:
        if number < 0:
            return f"{rule.name} must satisfy >= 0 (§4.2.13 / §4.4.28 ～ §4.4.35)"
        return None

    return None


def _vocabulary_defect(rule: Layer2FieldRule, value: object) -> str | None:
    """Return a defect detail when a STATUS value is outside its registered universe.

    A field without a registered **canonical** vocabulary is never given an allowlist
    (``§4.4.33``), so no defect can be derived for it here.
    """

    if rule.kind != KIND_STATUS or rule.vocabulary is None:
        return None
    if not isinstance(value, str):  # already reported as INVALID_TYPE
        return None
    if value not in rule.vocabulary:
        return (
            f"{rule.name} value {value!r} is not in the registered canonical "
            f"vocabulary {list(rule.vocabulary)}"
        )
    return None


def _record_location(artifact: str, record_index: int, field: str | None = None) -> str:
    location = f"{artifact}[{record_index}]"
    return location if field is None else f"{location}.{field}"


def _validate_record(
    *,
    artifact: str,
    record_index: int,
    record: JsonObject,
    collector: _Collector,
) -> None:
    """Validate the non-null present canonical values of one record."""

    for field in sorted(record.order):
        if field == "_meta":
            # Layer-1 owns the reserved namespace shape; Layer 2 adds no rule for it.
            continue

        value = record[field]
        location = _record_location(artifact, record_index, field)

        rule = LAYER2_FIELD_RULE_BY_NAME.get(field)
        if rule is None:
            collector.not_evaluable(
                f"layer2.field_rule:{artifact}[{record_index}].{field}",
                "no present-value rule is registered for this canonical field in the "
                "current authority; deferred rather than guessed",
            )
            continue

        if value is None:
            # §4.3.22 C-2: null = explicit missing / unavailable serialized value.
            # Whether that constitutes FIELD_VALUE / MISSING depends on per-role
            # applicability and requiredness, which §4.3.30 still defers.
            collector.not_evaluable(
                f"layer2.null_missingness:{location}",
                "JSON null present: C-2 semantics preserved (explicit missing / "
                "unavailable); missingness is deferred -- not decided here and never "
                "reported as INVALID_TYPE",
            )
            continue

        # Representation is decided **before** any deferral.  §4.3.22 C-3 -- C-10 are
        # unconditional: they apply to every present serialized value regardless of
        # whether the field's *value* rules are deferred.  A deferred field therefore
        # still reports INVALID_TYPE for a value of the wrong logical type, and only the
        # value-level judgement (range / vocabulary) is withheld as ``not evaluable``.
        defect = _representation_defect(rule, value)
        if defect is not None:
            reason = (
                REASON_UNRESOLVED_IDENTITY
                if rule.kind in (KIND_IDENTIFIER, KIND_ANALYSIS_RUN_ID)
                and value == ""
                else REASON_INVALID_TYPE
            )
            category = (
                CATEGORY_IDENTITY_RESOLUTION
                if reason == REASON_UNRESOLVED_IDENTITY
                else CATEGORY_FIELD_VALUE
            )
            collector.failed(f"layer2.representation:{location}", defect)
            collector.issue(
                category=category,
                reason=reason,
                location=location,
                detail=defect,
                affected_evidence=artifact,
                design_reference=(
                    "§4.4.26 (identifier) + §4.3.22 C-10"
                    if reason == REASON_UNRESOLVED_IDENTITY
                    else "§4.4.27 ～ §4.4.34 + §4.3.22 C-3 ～ C-10"
                ),
                consequence_context=(
                    "affected evidence / grain unreliable; package disposition unchanged"
                ),
            )
            continue

        note = LAYER2_NOT_EVALUABLE_FIELDS.get(field)
        if note is not None:
            collector.not_evaluable(
                f"layer2.field_not_evaluable:{location}",
                f"{note} (representation and logical type are already validated)",
            )
            continue

        range_defect = _range_defect(rule, value)
        if range_defect is not None:
            collector.failed(f"layer2.range:{location}", range_defect)
            collector.issue(
                category=CATEGORY_FIELD_VALUE,
                reason=REASON_OUT_OF_DEFINED_RANGE,
                location=location,
                detail=range_defect,
                affected_evidence=artifact,
                design_reference="§4.4.28 ～ §4.4.35 / §4.2.13",
                consequence_context=(
                    "affected evidence / grain unreliable; package disposition unchanged"
                ),
            )
            continue

        vocabulary_defect = _vocabulary_defect(rule, value)
        if vocabulary_defect is not None:
            collector.failed(f"layer2.status_vocabulary:{location}", vocabulary_defect)
            collector.issue(
                category=CATEGORY_FIELD_VALUE,
                reason=REASON_INVALID_DEFINED_STATUS,
                location=location,
                detail=vocabulary_defect,
                affected_evidence=artifact,
                design_reference="§4.4.29 ／ §4.4.30 ／ §4.2.14",
                consequence_context=(
                    "affected evidence / grain unreliable; package disposition unchanged"
                ),
            )
            continue

        collector.passed(f"layer2.present_value:{location}")


def validate_layer2(accepted: AcceptedPackage) -> Layer2Report:
    """Run the narrowed Layer-2 present-value validation over an accepted package.

    Trusted reuse is re-verified first (``MG-2``).  If required integrity can no
    longer be re-established the package is reported ``UNUSABLE`` and no canonical
    evidence validation is performed.
    """

    collector = _Collector()
    digest = accepted.content_view_digest

    verdict = accepted.reverify()
    if not verdict.reusable:
        # ``MG-2`` / ``IC-12``: required integrity could not be re-established before
        # trusted reuse.  The gate has exactly one state -- ``failed``.  It is never
        # also recorded as ``passed`` (``FR-3``: an undecided prerequisite must not be
        # reported as a pass, and a failed gate must not be reported as both).
        collector.failed(
            LAYER2_REVERIFICATION,
            "trusted reuse re-verification failed; normal Layer-2 validation not performed",
        )
        return Layer2Report(
            package_id=accepted.package_id,
            disposition=DISPOSITION_UNUSABLE,
            outcome=LAYER2_UNUSABLE,
            evaluation=EVALUATION_FAILED,
            collector=collector.collect(),
            accepted_content_view_digest=digest,
            note=(
                "required integrity could not be re-established before trusted reuse "
                "(§4.3.28 C.3 MG-2); changed files are never re-read as accepted evidence"
            ),
            # Re-published exactly as raised: Layer 2 did not establish these findings,
            # so it does not relabel their layer, category, reason, location, affected
            # evidence, blast radius or design reference.
            inherited_issues=verdict.collector.sorted_issues(),
        )

    collector.passed(LAYER2_REVERIFICATION)

    datasets = accepted.datasets()
    if not datasets:
        collector.not_evaluable(
            LAYER2_ACCEPTED_VIEW_BINDING,
            "accepted package exposes no dataset content view to validate",
        )
        return Layer2Report(
            package_id=accepted.package_id,
            disposition=DISPOSITION_ACCEPTED,
            outcome=LAYER2_REUSABLE,
            evaluation=EVALUATION_NOT_EVALUABLE,
            collector=collector.collect(),
            accepted_content_view_digest=digest,
            note="no dataset content view available; nothing was evaluated",
        )

    collector.passed(LAYER2_ACCEPTED_VIEW_BINDING)

    blocked_datasets: list[str] = []
    for _role, artifact in datasets:
        raw = accepted.records_for(artifact)
        if raw is None:
            blocked_datasets.append(artifact)
            collector.not_evaluable(
                f"{LAYER2_RECORD_CARRIER}:{artifact}",
                "accepted-view bytes for this dataset are unavailable",
            )
            continue

        try:
            payload: Any = parse_strict_json(raw, source=artifact)
        except StrictJsonError as error:
            blocked_datasets.append(artifact)
            collector.not_evaluable(
                f"{LAYER2_RECORD_CARRIER}:{artifact}",
                f"accepted-view artifact is not strict-parseable ({error})",
            )
            continue

        if not isinstance(payload, list):
            blocked_datasets.append(artifact)
            collector.not_evaluable(
                f"{LAYER2_RECORD_CARRIER}:{artifact}",
                "accepted-view artifact top level is not a bare record array",
            )
            continue

        collector.passed(f"{LAYER2_RECORD_CARRIER}:{artifact}")

        for record_index, record in enumerate(payload):
            if not isinstance(record, JsonObject):
                blocked_datasets.append(artifact)
                collector.not_evaluable(
                    f"{LAYER2_RECORD_CARRIER}:{artifact}[{record_index}]",
                    "record carrier is not a JSON object; field-level checks for this "
                    "record are not reachable",
                )
                continue
            _validate_record(
                artifact=artifact,
                record_index=record_index,
                record=record,
                collector=collector,
            )

    issues = tuple(sorted(collector.issues, key=Issue.sort_key))
    not_evaluable = [c for c in collector.checks if c.state == EVALUATION_NOT_EVALUABLE]

    if issues:
        collector.failed(LAYER2_PRESENT_VALUE_RULES, f"{len(issues)} canonical evidence defect(s)")
    elif blocked_datasets:
        collector.not_evaluable(
            LAYER2_PRESENT_VALUE_RULES,
            "at least one dataset was not reachable for field-level checks",
        )
    else:
        collector.passed(LAYER2_PRESENT_VALUE_RULES)

    evaluation = (
        EVALUATION_NOT_EVALUABLE
        if (blocked_datasets or not_evaluable)
        else (EVALUATION_FAILED if issues else EVALUATION_PASSED)
    )
    note = ""
    if not_evaluable:
        note = (
            f"{len(not_evaluable)} check(s) not evaluable: deferred present-value rules "
            "(§4.3.30 applicability / input channel) and JSON null missingness are "
            "outside this authorised subset"
        )

    return Layer2Report(
        package_id=accepted.package_id,
        disposition=DISPOSITION_ACCEPTED,
        outcome=LAYER2_REUSABLE,
        evaluation=evaluation,
        collector=collector.collect(),
        accepted_content_view_digest=digest,
        note=note,
    )


__all__ = [
    "LAYER2_ACCEPTED_VIEW_BINDING",
    "LAYER2_NOT_EVALUABLE_FIELDS",
    "LAYER2_PRESENT_VALUE_RULES",
    "LAYER2_RECORD_CARRIER",
    "LAYER2_REVERIFICATION",
    "Layer2Check",
    "Layer2Report",
    "LAYER2_FIELD_RULE_BY_NAME",
    "LAYER2_REGISTRY",
    "validate_layer2",
]
