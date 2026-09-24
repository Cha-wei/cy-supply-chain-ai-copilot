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

Canonical authority:

* ``docs/design/specs/data-integration/snapshot-import-contract.md``
  §4.3.22 -- §4.3.30 (implementation: §4.3.28 ``D4`` acceptance gate)
* ``docs/design/specs/data-integration/data-validation.md``
  §4.4.2 / §4.4.24 -- §4.4.44 / §4.4.79 -- §4.4.83 (inherited taxonomy, reused unchanged)

Scope boundary (deliberately narrow):

* **in scope (Layer 1)** -- package structural acceptance: trusted input boundary,
  strict JSON, contract version exact-match, unknown / undeclared content policy, role
  and artifact cardinality, strict literal paths, declared artifact existence and
  readability, raw-byte SHA-256 integrity, record carrier shape, canonical record
  property membership, and ``"_meta"`` shape.
* **in scope (Layer 2)** -- :func:`validate_layer2` over an :class:`AcceptedPackage`,
  non-null present values only, reported against the inherited issue taxonomy with
  ``not_evaluable`` used wherever the authority does not decide the question.
* **out of scope** -- ``§4.4`` Layer 3 (capability readiness) and Layer 4 (business
  rules), cross-field / cross-dataset consistency, ``§2`` business rules, procurement
  recommendation, persistence, network, LLM, database.

The core is importable and directly testable and does not depend on the CLI
(``POC Design v0.2`` §10.1 B; ADR-001).
"""

from __future__ import annotations

from .constants import (
    CONTRACT_VERSION_PROPERTY,
    DISPOSITION_ACCEPTED,
    DISPOSITION_REJECTED,
    DISPOSITION_UNUSABLE,
    MANIFEST_FILENAME,
    SUPPORTED_CONTRACT_VERSION,
    V02_CANONICAL_RECORD_PROPERTIES,
)
from .issues import Check, Issue
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
from .strict_json import StrictJsonError, parse_strict_json
from .trust import (
    AcceptedPackage,
    ContentView,
    ReuseVerdict,
    TrustedInputBoundary,
)

__all__ = [
    "AcceptedPackage",
    "Check",
    "CONTRACT_VERSION_PROPERTY",
    "ContentView",
    "DISPOSITION_ACCEPTED",
    "DISPOSITION_REJECTED",
    "DISPOSITION_UNUSABLE",
    "ImportReport",
    "Issue",
    "LAYER2_PRESENT_VALUE_RULES",
    "LAYER2_REGISTRY",
    "Layer2Check",
    "Layer2Report",
    "MANIFEST_FILENAME",
    "RECORD_PROPERTY_SET_CHECK",
    "ReuseVerdict",
    "SUPPORTED_CONTRACT_VERSION",
    "StrictJsonError",
    "TrustedInputBoundary",
    "V02_CANONICAL_RECORD_PROPERTIES",
    "load_package",
    "load_package_from_paths",
    "parse_strict_json",
    "validate_artifact_filename",
    "validate_layer2",
]

__version__ = "0.1.0"
