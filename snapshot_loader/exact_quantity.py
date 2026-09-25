"""Shared exact finite-decimal quantity machinery for the deterministic rules.

``ADR-001`` forbids treating the ``Decimal`` default context as a business precision and
forbids silent rounding from a library default.  Standard ``Decimal`` arithmetic is
context-driven -- ``Decimal("1E+30") - Decimal("1")`` is silently rounded at the default
28-digit precision -- so the deterministic rules do **not** perform quantity arithmetic in
``Decimal``.

This module is the single shared implementation used by ``BR-INBOUND-001`` and
``BR-INVENTORY-001``.  It is an internal helper module, not a canonical contract: it
creates no canonical entity, no canonical field and no wire property, and it adds no
rounding, quantization or business precision / scale policy.

It was extracted verbatim from the ``BR-INBOUND-001`` module (``Issue #138``) so both
rules share one exact implementation without one rule importing another rule; the
``BR-INBOUND-001`` behaviour and serialization are unchanged.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .constants import DECIMAL_STRING_PATTERN

_DECIMAL_STRING_RE = re.compile(rf"^{DECIMAL_STRING_PATTERN}$")


@dataclass(frozen=True, slots=True)
class ExactQuantity:
    """An exact finite base-10 quantity held as a scaled integer.

    ADR-001 forbids treating the ``Decimal`` default context as a business precision and
    forbids silent rounding from a library default.  Standard ``Decimal`` arithmetic is
    context-driven -- ``Decimal("1E+30") - Decimal("1")`` is silently rounded at the default
    28-digit precision -- so the rule does **not** do quantity arithmetic in ``Decimal``.

    Instead a canonical base-10 quantity is represented exactly as
    ``units * 10 ** -scale`` with ``units`` an arbitrary-precision integer, which makes
    addition and subtraction exact by construction on any operand size.  This is an internal
    representation only: :meth:`text` renders the registered public contract -- a plain exact
    finite decimal quantity with no exponent, no rounding, no quantization and no business
    precision / scale policy.  The exact numeric value and the stated fractional scale are
    preserved; this is **not** a character-for-character transcript of a canonical source
    string (for example ``"+5.00"`` renders as ``"5.00"`` and ``"001.20"`` as ``"1.20"``).
    """

    units: int
    scale: int

    @property
    def negative(self) -> bool:
        return self.units < 0

    def rescale(self, scale: int) -> "ExactQuantity":
        """Widen to ``scale`` decimal places (never loses value: ``scale`` only grows)."""

        if scale < self.scale:  # pragma: no cover - callers only widen
            raise ValueError("ExactQuantity cannot be narrowed without rounding")
        return ExactQuantity(self.units * 10 ** (scale - self.scale), scale)

    def __add__(self, other: "ExactQuantity") -> "ExactQuantity":
        scale = max(self.scale, other.scale)
        return ExactQuantity(
            self.rescale(scale).units + other.rescale(scale).units, scale
        )

    def __sub__(self, other: "ExactQuantity") -> "ExactQuantity":
        scale = max(self.scale, other.scale)
        return ExactQuantity(
            self.rescale(scale).units - other.rescale(scale).units, scale
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ExactQuantity):
            return NotImplemented
        scale = max(self.scale, other.scale)
        return self.rescale(scale).units == other.rescale(scale).units

    def __hash__(self) -> int:
        return hash(self._value_key())

    def __lt__(self, other: "ExactQuantity") -> bool:
        scale = max(self.scale, other.scale)
        return self.rescale(scale).units < other.rescale(scale).units

    def __le__(self, other: "ExactQuantity") -> bool:
        return self < other or self == other

    def __gt__(self, other: "ExactQuantity") -> bool:
        scale = max(self.scale, other.scale)
        return self.rescale(scale).units > other.rescale(scale).units

    def __ge__(self, other: "ExactQuantity") -> bool:
        return self > other or self == other

    def _value_key(self) -> tuple[int, int]:
        """Value identity, so equal quantities hash equally whatever scale they carry."""

        units, scale = self.units, self.scale
        while scale > 0 and units % 10 == 0:
            units //= 10
            scale -= 1
        return units, scale

    def text(self) -> str:
        """The exact canonical decimal text: plain digits, no exponent, no rounding.

        The exact value and the stored fractional scale are preserved, so ``"0.50"`` is
        rendered as ``"0.50"``: no rounding, quantization, truncation or scale normalisation
        is applied, and the scale carries no business-precision policy.  This is a lossless
        rendering of the *value*, not a character-for-character transcript of the source
        string -- a leading ``"+"`` or leading zeros are not lexical content of the quantity
        (``"+5.00"`` -> ``"5.00"``, ``"001.20"`` -> ``"1.20"``).
        """

        sign = "-" if self.units < 0 else ""
        digits = str(abs(self.units))
        if self.scale == 0:
            return f"{sign}{digits}"
        digits = digits.rjust(self.scale + 1, "0")
        whole, fraction = digits[: -self.scale], digits[-self.scale :]
        return f"{sign}{whole}.{fraction}"


def parse_exact_quantity(value: Any) -> ExactQuantity | None:
    """Parse a canonical base-10 decimal string into an exact scaled integer.

    ``None`` means the value is not a registered canonical decimal (JSON ``null``, a
    non-string, an empty string or a malformed form).  Nothing is repaired or defaulted.
    """

    if not isinstance(value, str) or not value:
        return None
    if not _DECIMAL_STRING_RE.match(value):
        return None
    body = value[1:] if value[0] in "+-" else value
    sign = -1 if value[0] == "-" else 1
    if "." in body:
        whole, fraction = body.split(".", 1)
    else:
        whole, fraction = body, ""
    digits = f"{whole or '0'}{fraction}"
    try:
        units = int(digits)
    except ValueError:  # pragma: no cover - guarded by the registered pattern
        return None
    return ExactQuantity(sign * units, len(fraction))


def parse_non_negative_quantity(value: Any) -> ExactQuantity | None:
    """Parse a canonical quantity that must be non-negative (``NON_NEGATIVE_QUANTITY``)."""

    parsed = parse_exact_quantity(value)
    if parsed is None:
        return None
    if parsed.negative:
        return None
    return parsed


__all__ = [
    "ExactQuantity",
    "parse_exact_quantity",
    "parse_non_negative_quantity",
]
