"""Strict literal path semantics and package-boundary containment (``PN-1``).

Registered semantics (``§4.3.28`` C.1 ``PN-1``, ``§4.3.23`` D/G/H, ``IC-1``/``IC-2``):

1. an artifact reference is a **single package-root-level filename**;
2. **exact filename match**;
3. **no** path normalisation, case folding or Unicode normalisation;
4. **no** ``.`` or ``..`` segment;
5. **no** absolute, external or URI reference;
6. **no** symlink / junction / filesystem-alias indirection;
7. two included roles resolving to the same physical target violate the inherited
   independent-artifact invariant.

Plus the two ``§4.3.23`` D physical-naming requirements registered alongside it:
the serialization extension is ``.json``, and ``manifest.json`` is a reserved name.

This module implements **only** those registered rules.  It deliberately does not
invent platform-specific filename policy: there is no maximum filename length, no
Windows reserved-device-name list, no Windows illegal-character set, no "trailing
dot/space" or "surrounding whitespace" rule, no "must have a non-empty stem" rule,
and no rule that rejects a filename merely for starting with ``..``.  Any such extra
rejection would be an unapproved acceptance criterion, and a filename the host
filesystem cannot represent is reported as an absent/unreadable declared artifact
(``IC-14``) rather than as a contract violation here.

One behaviour needs an explicit boundary statement because it is **not** a registered
contract criterion:

```
filename containing a control character  ->  rejected (CONTROL_CHARACTER)
```

Control characters are disallowed because they cannot be reliably compared or
represented.  This is a documented permissive-by-default implementation behaviour,
not a canonical acceptance criterion; if a wider tolerance is ever wanted, this is
the single place to change and it requires no contract amendment.

Because ``PN-1`` performs no normalisation, a value that is not literally a plain
filename is rejected outright rather than repaired into one.  Any accepted
reference is a single path component, so the resolved target is inside the package
root by construction; the containment assertion below is redundant
defence-in-depth, not a normalisation step.

Documented residual: a *decomposed* (NFD) and a *composed* (NFC) spelling of the
same non-ASCII filename are distinct byte strings under this policy.  The contract
deliberately forbids normalising them; filesystem-level equivalence between the two
is outside Layer-1 scope and is **not** claimed to be detected.
"""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path

from .constants import ARTIFACT_EXTENSION, MANIFEST_FILENAME

_PATH_SEPARATORS = ("/", "\\")
_URI_SCHEMES = (
    "file:",
    "http:",
    "https:",
    "ftp:",
    "s3:",
    "gs:",
    "smb:",
    "data:",
    "jar:",
)


@dataclass(frozen=True, slots=True)
class FilenameRejection:
    """Why a declared artifact reference is not a legal ``PN-1`` filename."""

    code: str
    detail: str


def _has_control_characters(value: str) -> bool:
    return any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)


def validate_artifact_filename(reference: object) -> FilenameRejection | None:
    """Return ``None`` when ``reference`` is a legal ``PN-1`` filename.

    Returns a :class:`FilenameRejection` describing the first violated rule
    otherwise.  The rules are evaluated in a fixed order so that reporting is
    deterministic.
    """

    if not isinstance(reference, str):
        return FilenameRejection(
            "NOT_A_STRING",
            f"artifact reference must be a JSON string, got {type(reference).__name__}",
        )

    if reference == "":
        return FilenameRejection("EMPTY", "artifact reference must not be empty")

    if reference.casefold().startswith(_URI_SCHEMES):
        return FilenameRejection(
            "URI_REFERENCE", "URI references are not legal package-root filenames"
        )

    for separator in _PATH_SEPARATORS:
        if separator in reference:
            return FilenameRejection(
                "PATH_SEPARATOR",
                "artifact reference must be a single package-root-level filename; "
                f"separator {separator!r} is not allowed",
            )

    if reference in {".", ".."}:
        return FilenameRejection(
            "DOT_SEGMENT",
            "'.' and '..' are not filenames; a '..' *segment* is already rejected by "
            "the separator rule above",
        )

    if os.path.isabs(reference):
        return FilenameRejection(
            "ABSOLUTE_PATH", "absolute paths are not legal artifact references"
        )

    if os.path.basename(reference) != reference or os.path.dirname(reference) != "":
        return FilenameRejection(
            "NOT_A_FILENAME",
            "artifact reference must be a plain filename with no directory component",
        )

    if _has_control_characters(reference):
        return FilenameRejection(
            "CONTROL_CHARACTER",
            "filenames containing control characters are not accepted (implementation "
            "behaviour, not a registered contract criterion)",
        )

    if not reference.endswith(ARTIFACT_EXTENSION):
        return FilenameRejection(
            "WRONG_EXTENSION",
            f"artifact filename must use the {ARTIFACT_EXTENSION!r} extension "
            "(§4.3.23 D: serialization extension = .json)",
        )

    if reference == MANIFEST_FILENAME:
        return FilenameRejection(
            "RESERVED_FILENAME",
            f"{MANIFEST_FILENAME!r} is reserved for the Snapshot Manifest",
        )

    # No "non-empty stem" rule: canonical authority registers only
    # ``extension = .json`` (§4.3.23 D).  A literal ``".json"`` therefore satisfies
    # the registered rule and is accepted; requiring a stem would be an unapproved
    # acceptance criterion.

    return None


def resolved_within(candidate: Path, anchor: Path) -> bool:
    """Return ``True`` when ``candidate`` resolves inside ``anchor``.

    Used as a redundant boundary assertion (``IC-2``): on any resolution error the
    answer is ``False`` so that the caller fails closed.
    """

    try:
        resolved_anchor = anchor.resolve(strict=False)
        resolved_candidate = candidate.resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        return False

    if resolved_candidate == resolved_anchor:
        return True
    try:
        return os.path.commonpath([str(resolved_anchor), str(resolved_candidate)]) == str(
            resolved_anchor
        )
    except ValueError:
        # Different drives / mounts on Windows: not within the package boundary.
        return False


def is_reparse_point(path: Path) -> bool:
    """Best-effort symlink / junction / reparse-point detection (``PN-1`` rule 6).

    Returns ``True`` for symbolic links and, on Windows, for any other reparse
    point (junction, mount point, appexec link).  Returns ``False`` when the path
    cannot be inspected -- callers must therefore treat a ``False`` result as
    "not detected" rather than as proven alias-free.
    """

    try:
        stat_result = path.lstat()
    except OSError:
        return False

    if os.path.islink(path):
        return True

    file_attributes = getattr(stat_result, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(file_attributes & reparse_flag)


def physical_identity(path: Path) -> tuple[int, int] | None:
    """Return ``(st_dev, st_ino)`` when the platform exposes a usable identity.

    ``None`` means the platform/filesystem could not provide a trustworthy
    identity; alias detection must then be reported as *not evaluable* rather than
    as passed or failed.
    """

    try:
        stat_result = path.stat()
    except OSError:
        return None

    device = int(getattr(stat_result, "st_dev", 0) or 0)
    inode = int(getattr(stat_result, "st_ino", 0) or 0)
    if device == 0 and inode == 0:
        return None
    return (device, inode)
