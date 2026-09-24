"""Controlled Snapshot loader and Layer-1 package acceptance (POC v0.2).

First deterministic tranche, module 1 of ``POC Design v0.2`` §10.1 B:

    Snapshot loader / import
      controlled JSON package + configured trusted input boundary
        -> package acceptance, or an existing rejection / not-evaluable outcome

Canonical authority:

* ``docs/design/specs/data-integration/snapshot-import-contract.md``
  §4.3.22 -- §4.3.30 (implementation: §4.3.28 ``D4`` acceptance gate)
* ``docs/design/specs/data-integration/data-validation.md``
  §4.4.2 / §4.4.79 -- §4.4.83 (inherited taxonomy, reused unchanged)

Scope boundary (deliberately narrow):

* **in scope** -- package structural acceptance: trusted input boundary, strict JSON,
  contract version exact-match, unknown / undeclared content policy, role and
  artifact cardinality, strict literal paths, declared artifact existence and
  readability, raw-byte SHA-256 integrity, record carrier shape, canonical record
  property membership, and ``"_meta"`` shape.
* **out of scope** -- ``§4.4`` Layer 2+ validation, canonical business objects,
  ``§2`` business rules, procurement recommendation, persistence, CLI-only concerns,
  network, LLM, database.

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
