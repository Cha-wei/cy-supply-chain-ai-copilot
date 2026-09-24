"""Strict JSON parsing for the controlled Snapshot import boundary.

Registered requirements (``§4.3.22`` ``C-1``/``C-9``, restated as ``IC-8``):

* UTF-8 **without BOM**;
* **strict parse** -- duplicate object keys, comments, trailing commas, ``NaN`` and
  ``Infinity`` are all forbidden;
* standard JSON escaping only;
* **no** silent fix-up: no trim, no case conversion, no Unicode normalisation, no
  numeric coercion.

``decimal.Decimal`` is used for JSON numbers so that the *exact* decimal string is
preserved and no binary floating point value is ever produced (``§4.3.22`` ``C-5``,
``IC-10``, ADR-001).  Rejecting a non-compliant input is the only permitted reaction
to any violation: the parser never repairs, rewrites, or normalises anything.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

_WHITESPACE = frozenset(" \t\n\r")

_NUMBER_RE = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?")

_ESCAPES = {
    '"': '"',
    "\\": "\\",
    "/": "/",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
}

_SURROGATE_RANGE = range(0xD800, 0xE000)


class StrictJsonError(ValueError):
    """Raised when an input is not a compliant POC v0.2 JSON document."""

    def __init__(self, message: str, offset: int | None = None) -> None:
        self.offset = offset
        super().__init__(message if offset is None else f"{message} (at offset {offset})")


class JsonObject(dict):
    """A JSON object whose member *order* is retained for deterministic reporting.

    Object member order carries **no** business semantic (``C-9``); order is kept
    only so that deterministic issue ordering can be produced without re-parsing.
    """

    __slots__ = ("_order",)

    def __init__(self, pairs: list[tuple[str, Any]]) -> None:
        super().__init__(pairs)
        self._order = tuple(key for key, _ in pairs)

    @property
    def order(self) -> tuple[str, ...]:
        return self._order


def parse_strict_json(
    raw: bytes,
    *,
    source: str = "<input>",
    max_depth: int = 64,
) -> Any:
    """Parse ``raw`` as strict JSON, returning plain Python values.

    ``bytes`` input is required so that the encoding rules (UTF-8 **without BOM**)
    are enforced on the exact artifact bytes rather than on a decoded guess.
    """

    if not isinstance(raw, (bytes, bytearray)):
        raise StrictJsonError("strict JSON input must be bytes")

    if raw.startswith(b"\xef\xbb\xbf"):
        raise StrictJsonError("UTF-8 BOM is not allowed (C-1: UTF-8 without BOM)")

    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise StrictJsonError(f"input is not valid UTF-8: {exc.reason}", exc.start) from exc

    parser = _Parser(text=text, source=source, max_depth=max_depth)
    value = parser.parse_document()
    return value


class _Parser:
    def __init__(self, *, text: str, source: str, max_depth: int) -> None:
        self._text = text
        self._source = source
        self._pos = 0
        self._max_depth = max_depth

    # -- error helpers ---------------------------------------------------------

    def _fail(self, message: str, offset: int | None = None) -> "StrictJsonError":
        return StrictJsonError(
            f"{self._source}: {message}", self._pos if offset is None else offset
        )

    # -- primitives ------------------------------------------------------------

    def _skip_ws(self) -> None:
        text = self._text
        pos = self._pos
        while pos < len(text) and text[pos] in _WHITESPACE:
            pos += 1
        self._pos = pos

    def _peek(self) -> str:
        text = self._text
        pos = self._pos
        if pos >= len(text):
            raise self._fail("unexpected end of input")
        return text[pos]

    def _expect_literal(self, literal: str) -> None:
        end = self._pos + len(literal)
        if self._text[self._pos : end] != literal:
            raise self._fail(f"expected literal {literal!r}")
        self._pos = end

    # -- document --------------------------------------------------------------

    def parse_document(self) -> Any:
        self._skip_ws()
        value = self._parse_value(depth=0)
        self._skip_ws()
        if self._pos != len(self._text):
            raise self._fail("trailing content after the top-level JSON value")
        return value

    # -- values ----------------------------------------------------------------

    def _parse_value(self, *, depth: int) -> Any:
        if depth > self._max_depth:
            raise self._fail(f"maximum nesting depth {self._max_depth} exceeded")

        char = self._peek()
        if char == "{":
            return self._parse_object(depth=depth)
        if char == "[":
            return self._parse_array(depth=depth)
        if char == '"':
            return self._parse_string()
        if char == "t":
            self._expect_literal("true")
            return True
        if char == "f":
            self._expect_literal("false")
            return False
        if char == "n":
            self._expect_literal("null")
            return None
        if char == "-" or char.isdigit():
            return self._parse_number()
        if char == "/":
            raise self._fail("comments are not allowed in strict JSON")
        if self._text.startswith(("NaN", "Infinity", "-Infinity"), self._pos):
            raise self._fail("NaN and Infinity are not allowed in strict JSON (C-9)")
        raise self._fail(f"unexpected character {char!r}")

    def _parse_object(self, *, depth: int) -> JsonObject:
        self._pos += 1  # consume '{'
        pairs: list[tuple[str, Any]] = []
        seen: set[str] = set()
        self._skip_ws()
        if self._peek() == "}":
            self._pos += 1
            return JsonObject(pairs)
        while True:
            self._skip_ws()
            if self._peek() != '"':
                raise self._fail("object keys must be JSON strings")
            key = self._parse_string()
            if key in seen:
                raise self._fail(f"duplicate object key {key!r} (C-9)")
            seen.add(key)
            self._skip_ws()
            if self._peek() != ":":
                raise self._fail("expected ':' after object key")
            self._pos += 1
            self._skip_ws()
            value = self._parse_value(depth=depth + 1)
            pairs.append((key, value))
            self._skip_ws()
            char = self._peek()
            if char == ",":
                self._pos += 1
                self._skip_ws()
                if self._peek() == "}":
                    raise self._fail("trailing comma is not allowed in strict JSON (C-9)")
                continue
            if char == "}":
                self._pos += 1
                return JsonObject(pairs)
            raise self._fail("expected ',' or '}' in object")

    def _parse_array(self, *, depth: int) -> list[Any]:
        self._pos += 1  # consume '['
        items: list[Any] = []
        self._skip_ws()
        if self._peek() == "]":
            self._pos += 1
            return items
        while True:
            self._skip_ws()
            items.append(self._parse_value(depth=depth + 1))
            self._skip_ws()
            char = self._peek()
            if char == ",":
                self._pos += 1
                self._skip_ws()
                if self._peek() == "]":
                    raise self._fail("trailing comma is not allowed in strict JSON (C-9)")
                continue
            if char == "]":
                self._pos += 1
                return items
            raise self._fail("expected ',' or ']' in array")

    def _parse_string(self) -> str:
        self._pos += 1  # consume opening quote
        text = self._text
        chunks: list[str] = []
        start = self._pos
        while True:
            pos = self._pos
            if pos >= len(text):
                raise self._fail("unterminated string")
            char = text[pos]
            if char == '"':
                chunks.append(text[start:pos])
                self._pos = pos + 1
                return "".join(chunks)
            if char == "\\":
                chunks.append(text[start:pos])
                self._pos = pos + 1
                chunks.append(self._parse_escape())
                start = self._pos
                continue
            codepoint = ord(char)
            if codepoint < 0x20:
                raise self._fail(
                    f"unescaped control character U+{codepoint:04X} in string"
                )
            self._pos = pos + 1

    def _parse_escape(self) -> str:
        if self._pos >= len(self._text):
            raise self._fail("unterminated escape sequence")
        char = self._text[self._pos]
        self._pos += 1
        if char in _ESCAPES:
            return _ESCAPES[char]
        if char != "u":
            raise self._fail(f"invalid escape sequence '\\{char}'")
        first = self._parse_hex4()
        if 0xD800 <= first <= 0xDBFF:
            if self._text[self._pos : self._pos + 2] != "\\u":
                raise self._fail("lone high surrogate escape is not valid JSON")
            self._pos += 2
            second = self._parse_hex4()
            if not 0xDC00 <= second <= 0xDFFF:
                raise self._fail("high surrogate escape is not followed by a low surrogate")
            combined = 0x10000 + ((first - 0xD800) << 10) + (second - 0xDC00)
            return chr(combined)
        if first in _SURROGATE_RANGE:
            raise self._fail("lone low surrogate escape is not valid JSON")
        return chr(first)

    def _parse_hex4(self) -> int:
        digits = self._text[self._pos : self._pos + 4]
        if len(digits) != 4:
            raise self._fail("truncated \\u escape sequence")
        try:
            value = int(digits, 16)
        except ValueError as exc:
            raise self._fail(f"invalid \\u escape sequence {digits!r}") from exc
        self._pos += 4
        return value

    def _parse_number(self) -> Decimal:
        match = _NUMBER_RE.match(self._text, self._pos)
        if match is None:
            raise self._fail("invalid JSON number")
        literal = match.group(0)
        self._pos = match.end()
        try:
            # Decimal preserves the exact decimal literal: no binary floating point
            # and no rounding, quantisation or truncation (C-5 / IC-10).
            return Decimal(literal)
        except InvalidOperation as exc:  # pragma: no cover - guarded by _NUMBER_RE
            raise self._fail(f"invalid JSON number {literal!r}") from exc
