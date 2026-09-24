"""Strict JSON parsing tests (``§4.3.22`` ``C-1``/``C-9``, ``IC-8``)."""

from __future__ import annotations

import unittest
from decimal import Decimal
from pathlib import Path


from snapshot_loader import StrictJsonError, parse_strict_json  # noqa: E402
from snapshot_loader.strict_json import JsonObject  # noqa: E402


class StrictJsonAcceptanceTests(unittest.TestCase):
    def test_scalars(self) -> None:
        self.assertIs(parse_strict_json(b"true"), True)
        self.assertIs(parse_strict_json(b"false"), False)
        self.assertIsNone(parse_strict_json(b"null"))

    def test_numbers_use_decimal_without_binary_float(self) -> None:
        value = parse_strict_json(b"0.123456789012345678901234567890")
        self.assertIsInstance(value, Decimal)
        self.assertEqual(str(value), "0.123456789012345678901234567890")

    def test_integer_literal_is_exact(self) -> None:
        value = parse_strict_json(b"123456789012345678901234567890")
        self.assertIsInstance(value, Decimal)
        self.assertEqual(value, Decimal("123456789012345678901234567890"))

    def test_object_member_order_is_retained_without_semantics(self) -> None:
        value = parse_strict_json(b'{"b": 1, "a": 2}')
        self.assertIsInstance(value, JsonObject)
        self.assertEqual(value.order, ("b", "a"))

    def test_string_escapes(self) -> None:
        value = parse_strict_json(rb'"a\"b\\c\/d\ne\tf\u0041\u00e9"')
        self.assertEqual(value, 'a"b\\c/d\ne\tfA\u00e9')

    def test_surrogate_pair_escape_is_decoded(self) -> None:
        value = parse_strict_json(rb'"\ud83d\ude00"')
        self.assertEqual(value, "\U0001f600")

    def test_empty_containers(self) -> None:
        self.assertEqual(parse_strict_json(b"[]"), [])
        self.assertEqual(parse_strict_json(b"{}"), {})

    def test_whitespace_around_document(self) -> None:
        self.assertEqual(parse_strict_json(b" \r\n\t[] \n"), [])

    def test_utf8_multibyte_content(self) -> None:
        self.assertEqual(parse_strict_json('["云南"]'.encode()), ["云南"])


class StrictJsonRejectionTests(unittest.TestCase):
    def assert_rejected(self, payload: bytes, expected_fragment: str | None = None) -> None:
        with self.assertRaises(StrictJsonError) as context:
            parse_strict_json(payload)
        if expected_fragment is not None:
            self.assertIn(expected_fragment, str(context.exception))

    def test_utf8_bom_is_rejected(self) -> None:
        self.assert_rejected(b"\xef\xbb\xbf{}", "BOM")

    def test_invalid_utf8_is_rejected(self) -> None:
        self.assert_rejected(b'{"a": "\xff"}', "UTF-8")

    def test_duplicate_keys_are_rejected(self) -> None:
        self.assert_rejected(b'{"a": 1, "a": 2}', "duplicate object key")

    def test_nested_duplicate_keys_are_rejected(self) -> None:
        self.assert_rejected(b'{"a": {"b": 1, "b": 2}}', "duplicate object key")

    def test_comment_is_rejected(self) -> None:
        self.assert_rejected(b'{"a": 1} // trailing comment', "trailing content")
        self.assert_rejected(b'{"a": /* c */ 1}', "comments are not allowed")

    def test_trailing_comma_in_object_is_rejected(self) -> None:
        self.assert_rejected(b'{"a": 1,}', "trailing comma")

    def test_trailing_comma_in_array_is_rejected(self) -> None:
        self.assert_rejected(b"[1,]", "trailing comma")

    def test_nan_and_infinity_are_rejected(self) -> None:
        self.assert_rejected(b"NaN")
        self.assert_rejected(b"Infinity")
        self.assert_rejected(b"-Infinity")
        self.assert_rejected(b'{"a": NaN}')

    def test_unquoted_key_is_rejected(self) -> None:
        self.assert_rejected(b"{a: 1}", "object keys must be JSON strings")

    def test_single_quotes_are_rejected(self) -> None:
        self.assert_rejected(b"{'a': 1}")

    def test_trailing_content_is_rejected(self) -> None:
        self.assert_rejected(b"[] []", "trailing content")

    def test_truncated_input_is_rejected(self) -> None:
        self.assert_rejected(b'{"a": ')
        self.assert_rejected(b'["a"')

    def test_unterminated_string_is_rejected(self) -> None:
        self.assert_rejected(b'"abc')

    def test_raw_control_character_in_string_is_rejected(self) -> None:
        self.assert_rejected(b'"a\nb"', "control character")

    def test_invalid_escape_is_rejected(self) -> None:
        self.assert_rejected(rb'"\x"', "invalid escape sequence")

    def test_lone_surrogate_escapes_are_rejected(self) -> None:
        self.assert_rejected(rb'"\ud83d"', "lone high surrogate")
        self.assert_rejected(rb'"\ude00"', "lone low surrogate")

    def test_leading_zero_number_is_rejected(self) -> None:
        self.assert_rejected(b"01", "trailing content")

    def test_plus_prefixed_number_is_rejected(self) -> None:
        self.assert_rejected(b"+1")

    def test_hex_number_is_rejected(self) -> None:
        self.assert_rejected(b"0x10", "trailing content")

    def test_nesting_depth_limit_is_enforced(self) -> None:
        payload = b"[" * 200 + b"]" * 200
        self.assert_rejected(payload, "nesting depth")


if __name__ == "__main__":
    unittest.main()
