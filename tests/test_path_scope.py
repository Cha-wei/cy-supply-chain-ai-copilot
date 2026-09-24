"""Strict literal path semantics tests (``§4.3.28`` C.1 ``PN-1``, ``IC-1``/``IC-2``)."""

from __future__ import annotations

import unittest
from pathlib import Path, PurePosixPath, PureWindowsPath


from snapshot_loader import validate_artifact_filename  # noqa: E402
from snapshot_loader.path_scope import resolved_within  # noqa: E402


class FilenameAcceptanceTests(unittest.TestCase):
    def assert_accepted(self, reference: str) -> None:
        rejection = validate_artifact_filename(reference)
        self.assertIsNone(rejection, msg=f"{reference!r} -> {rejection}")

    def test_plain_ascii_filenames(self) -> None:
        self.assert_accepted("requirement.json")
        self.assert_accepted("supplier_performance.json")
        self.assert_accepted("a.json")
        self.assert_accepted("UPPER.JSON".lower())
        self.assert_accepted("dataset-1.v2.json")

    def test_unicode_filename_is_accepted_without_normalisation(self) -> None:
        self.assert_accepted("需求.json")

    def test_filename_may_contain_dots(self) -> None:
        self.assert_accepted("v0.2.records.json")


class FilenameRejectionTests(unittest.TestCase):
    def assert_rejected(self, reference: object, code: str) -> None:
        rejection = validate_artifact_filename(reference)
        self.assertIsNotNone(rejection, msg=f"{reference!r} unexpectedly accepted")
        assert rejection is not None
        self.assertEqual(rejection.code, code, msg=f"{reference!r} -> {rejection}")

    def test_non_string(self) -> None:
        self.assert_rejected(7, "NOT_A_STRING")
        self.assert_rejected(None, "NOT_A_STRING")
        self.assert_rejected(["a.json"], "NOT_A_STRING")

    def test_empty(self) -> None:
        self.assert_rejected("", "EMPTY")

    def test_path_separators(self) -> None:
        self.assert_rejected("sub/requirement.json", "PATH_SEPARATOR")
        self.assert_rejected("sub\\requirement.json", "PATH_SEPARATOR")
        self.assert_rejected(PurePosixPath("sub/req.json").as_posix(), "PATH_SEPARATOR")
        self.assert_rejected(str(PureWindowsPath("sub", "req.json")), "PATH_SEPARATOR")

    def test_dot_segments(self) -> None:
        self.assert_rejected("..", "DOT_SEGMENT")
        self.assert_rejected("../requirement.json", "PATH_SEPARATOR")
        self.assert_rejected("./requirement.json", "PATH_SEPARATOR")
        self.assert_rejected("..requirement.json", "DOT_SEGMENT")

    def test_uri_references(self) -> None:
        self.assert_rejected("file:///tmp/requirement.json", "URI_REFERENCE")
        self.assert_rejected("http://example.test/a.json", "URI_REFERENCE")
        self.assert_rejected("s3://bucket/a.json", "URI_REFERENCE")

    def test_manifest_filename_is_reserved(self) -> None:
        self.assert_rejected("manifest.json", "RESERVED_FILENAME")

    def test_wrong_extension(self) -> None:
        self.assert_rejected("requirement.csv", "WRONG_EXTENSION")
        self.assert_rejected("requirement", "WRONG_EXTENSION")
        self.assert_rejected("requirement.jsonl", "WRONG_EXTENSION")

    def test_whitespace_is_not_trimmed(self) -> None:
        self.assert_rejected(" requirement.json", "SURROUNDING_WHITESPACE")
        self.assert_rejected("requirement.json ", "SURROUNDING_WHITESPACE")

    def test_trailing_dot_or_space(self) -> None:
        self.assert_rejected("requirement.json.", "TRAILING_DOT_OR_SPACE")

    def test_control_characters(self) -> None:
        self.assert_rejected("requirement\n.json", "CONTROL_CHARACTER")
        self.assert_rejected("requirement\x00.json", "CONTROL_CHARACTER")

    def test_overlong_filename(self) -> None:
        self.assert_rejected("a" * 260 + ".json", "TOO_LONG")

    def test_maximum_length_filename_is_accepted(self) -> None:
        # 255 characters total: the contract limit itself is still a legal filename.
        self.assertIsNone(validate_artifact_filename("a" * 250 + ".json"))

    def test_case_is_not_folded_and_exact_match_required(self) -> None:
        # PN-1 forbids case folding: a differently-cased reference is simply a
        # different literal filename, not a rejection reason.
        self.assertIsNone(validate_artifact_filename("Requirement.JSON".lower()))


class ContainmentTests(unittest.TestCase):
    def test_direct_child_is_within(self) -> None:
        root = Path.cwd()
        self.assertTrue(resolved_within(root / "child.json", root))

    def test_root_itself_is_within(self) -> None:
        root = Path.cwd()
        self.assertTrue(resolved_within(root, root))

    def test_parent_is_not_within(self) -> None:
        root = Path.cwd()
        self.assertFalse(resolved_within(root.parent, root))


if __name__ == "__main__":
    unittest.main()
