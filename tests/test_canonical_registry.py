"""Frozen v0.2 canonical record property registry tests (§4.3.30 B).

The registered literal set is **explicit, closed, version-bound, and Human-approved**.
These tests guard that it is (a) exactly the set the canonical authority enumerates,
(b) never derived at runtime from the Data Dictionary, and (c) free of the items the
Human Decision explicitly excluded.
"""

from __future__ import annotations

import unittest
from pathlib import Path


from snapshot_loader.constants import (  # noqa: E402
    V02_CANONICAL_RECORD_PROPERTIES,
    V02_CANONICAL_RECORD_PROPERTY_SET,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DICTIONARY = REPO_ROOT / "docs" / "design" / "specs" / "data-integration" / "data-dictionary.md"
IMPORT_CONTRACT = (
    REPO_ROOT / "docs" / "design" / "specs" / "data-integration" / "snapshot-import-contract.md"
)

#: Canonical field tables are §4.2.3 -- §4.2.9 (Identity/Context, Requirement/BOM,
#: Inventory, Inbound, Substitute, Supplier, Procurement).  §4.2.10 holds DERIVED
#: results, which are deliberately outside the wire property set.
FIELD_TABLE_SECTIONS = ("4.2.3", "4.2.4", "4.2.5", "4.2.6", "4.2.7", "4.2.8", "4.2.9")

EXCLUDED_LITERALS = (
    "effective demand context",
    "snapshot_package_id",
    "_meta",
)


def _canonical_identifiers_from_data_dictionary(path: Path) -> list[str]:
    """Extract backticked canonical field identifiers from the §4.2.3 -- §4.2.9 tables."""

    section = ""
    identifiers: list[str] = []

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()

        if stripped.startswith("#### "):
            marker = stripped[5:].split(" ", 1)[0]
            section = marker

        if not stripped.startswith("|"):
            continue
        if section not in FIELD_TABLE_SECTIONS:
            continue

        columns = stripped.split("|")
        if len(columns) < 5:
            continue

        name = columns[1].strip()
        logical_type = columns[2].strip()
        if not name or set(name) <= set("-") or name == "Field":
            continue
        if not logical_type.startswith("`"):
            continue
        if not (name.startswith("`") and name.endswith("`")):
            continue

        identifiers.append(name.strip("`"))

    return identifiers


class RegistryShapeTests(unittest.TestCase):
    def test_registry_is_a_tuple_of_unique_strings(self) -> None:
        self.assertIsInstance(V02_CANONICAL_RECORD_PROPERTIES, tuple)
        self.assertTrue(all(isinstance(item, str) for item in V02_CANONICAL_RECORD_PROPERTIES))
        self.assertEqual(
            len(V02_CANONICAL_RECORD_PROPERTIES),
            len(set(V02_CANONICAL_RECORD_PROPERTIES)),
        )

    def test_registry_set_matches_the_enumeration(self) -> None:
        self.assertEqual(
            V02_CANONICAL_RECORD_PROPERTY_SET,
            frozenset(V02_CANONICAL_RECORD_PROPERTIES),
        )

    def test_registered_count_is_thirty(self) -> None:
        self.assertEqual(len(V02_CANONICAL_RECORD_PROPERTIES), 30)

    def test_excluded_items_are_absent(self) -> None:
        for excluded in EXCLUDED_LITERALS:
            with self.subTest(excluded=excluded):
                self.assertNotIn(excluded, V02_CANONICAL_RECORD_PROPERTY_SET)

    def test_naming_clarifications_are_present(self) -> None:
        # Issue #118 Human Decision: these two exact identifiers replaced descriptive
        # display names.
        self.assertIn("analysis_run_id", V02_CANONICAL_RECORD_PROPERTY_SET)
        self.assertIn("inbound_status", V02_CANONICAL_RECORD_PROPERTY_SET)

    def test_registry_preserves_registered_letter_case(self) -> None:
        # C-10 / PN-1: identifier literals are exact opaque strings; no case folding.
        for literal in ("AnalysisDate", "ProductionQty", "BOMComponentQty", "SafetyStock"):
            with self.subTest(literal=literal):
                self.assertIn(literal, V02_CANONICAL_RECORD_PROPERTY_SET)

    def test_derived_results_are_absent(self) -> None:
        for derived in (
            "BaseRequirement",
            "GrossRequirement",
            "RecommendedPurchaseQty",
            "Classification",
            "FirstShortageDate",
        ):
            with self.subTest(derived=derived):
                self.assertNotIn(derived, V02_CANONICAL_RECORD_PROPERTY_SET)


class RegistryAuthorityTests(unittest.TestCase):
    def test_registry_matches_the_canonical_data_dictionary_set(self) -> None:
        identifiers = _canonical_identifiers_from_data_dictionary(DATA_DICTIONARY)
        self.assertEqual(len(identifiers), len(set(identifiers)), "duplicate identifier")

        missing = sorted(set(identifiers) - V02_CANONICAL_RECORD_PROPERTY_SET)
        extra = sorted(V02_CANONICAL_RECORD_PROPERTY_SET - set(identifiers))

        self.assertEqual(
            missing,
            [],
            msg=(
                "canonical field identifier(s) present in the Data Dictionary but absent "
                "from the frozen v0.2 wire property set"
            ),
        )
        self.assertEqual(
            extra,
            [],
            msg=(
                "frozen v0.2 wire property literal(s) with no matching canonical field "
                "identifier in the Data Dictionary"
            ),
        )

    def test_registered_clarification_is_reflected_in_the_data_dictionary(self) -> None:
        text = DATA_DICTIONARY.read_text(encoding="utf-8")
        self.assertIn("`analysis_run_id`", text)
        self.assertIn("`inbound_status`", text)

    def test_import_contract_registers_the_frozen_set(self) -> None:
        text = IMPORT_CONTRACT.read_text(encoding="utf-8")
        self.assertIn("§4.3.30", text)
        self.assertIn("Frozen v0.2 canonical record property literals", text)
        self.assertIn("global contract-level known canonical record property set", text)
        self.assertIn("Per-role whitelist", text)

        for literal in V02_CANONICAL_RECORD_PROPERTIES:
            with self.subTest(literal=literal):
                self.assertIn(f"\n{literal}\n", text)


if __name__ == "__main__":
    unittest.main()
