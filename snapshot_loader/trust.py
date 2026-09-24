"""Trusted input boundary, stable content view, and accepted-package reuse.

Registered requirements implemented here:

* ``§4.3.28`` D.3 ``IG-self-C`` -- the authoritative input is a **configured trusted
  package-input boundary**; it must provide the *same stable package content view*
  that acceptance used; a missing or unverifiable boundary is ``not evaluable`` and
  therefore fail-closed.
* ``§4.3.28`` C.2 ``Decision 10A`` -- every check that contributes to ``Accepted``
  must be bound to one and the same package content view: the view that is actually
  accepted and later referenced.  Inability to establish that consistency is
  ``not evaluable`` / fail closed.
* ``§4.3.28`` C.3 ``Decision 10B`` ``MG-2`` -- before any trusted reuse, integrity
  must remain re-verifiable; a detected mutation or an integrity that can no longer
  be re-established makes the package ``UNUSABLE``.
* ``§4.3.5``/``IC-12`` -- an accepted package is immutable; the same identity must
  never denote different content.

Implementation note (explicitly *not* a design decision): the stable view is bound
by reading each file **once** into memory and performing every subsequent check on
those same bytes, plus a final directory-listing comparison that detects a
mid-acceptance change of the package.  The contract leaves locking / transaction /
atomic-move / storage-technology mechanisms open; this implementation does not claim
a filesystem transaction, and cross-process concurrent mutation is detected (then
fail-closed) rather than prevented.
"""

from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path

from .constants import DISPOSITION_UNUSABLE, MANIFEST_FILENAME
from .issues import Issue, IssueCollector
from .path_scope import is_reparse_point, physical_identity

_READ_CHUNK = 1024 * 1024


@dataclass(frozen=True, slots=True)
class FileView:
    """The exact verified view of one package file."""

    name: str
    sha256: str
    size: int
    mtime_ns: int
    identity: tuple[int, int] | None

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "sha256": self.sha256,
            "size": self.size,
            "mtime_ns": self.mtime_ns,
            "identity": list(self.identity) if self.identity else None,
        }


@dataclass(frozen=True, slots=True)
class ContentView:
    """The stable package content view that acceptance is bound to."""

    package_path: str
    root_identity: tuple[int, int] | None
    files: tuple[FileView, ...]
    directory_listing: tuple[str, ...]
    digest: str

    def file(self, name: str) -> FileView | None:
        for view in self.files:
            if view.name == name:
                return view
        return None

    def to_dict(self) -> dict[str, object]:
        return {
            "package_path": self.package_path,
            "root_identity": list(self.root_identity) if self.root_identity else None,
            "files": [view.to_dict() for view in self.files],
            "directory_listing": list(self.directory_listing),
            "digest": self.digest,
        }


@dataclass(frozen=True, slots=True)
class BoundaryResolution:
    """Outcome of resolving the configured trusted package-input boundary."""

    root: Path | None
    problem: Issue | None

    @property
    def established(self) -> bool:
        return self.root is not None and self.problem is None


@dataclass(frozen=True, slots=True)
class TrustedInputBoundary:
    """Explicitly configured trusted package-input boundary (``IG-self-C``).

    The boundary must be **configured**, never inferred: a loader that treats any
    arbitrary path as trusted would violate ``§4.3.28`` D.3 and ``IC-16``.  A
    package is admissible only when it is a **direct child** directory of the
    boundary root, which matches the registered *flat directory package* layout
    (``§4.3.23`` A/G).
    """

    root: Path

    def resolve(self, package_dir: os.PathLike[str] | str) -> BoundaryResolution:
        try:
            root = Path(self.root).expanduser()
            root = Path(os.path.abspath(root))
        except (OSError, RuntimeError, ValueError) as exc:
            return BoundaryResolution(
                root=None,
                problem=Issue(
                    location="trust_boundary",
                    detail=f"configured trusted input boundary could not be resolved: {exc}",
                    design_reference="§4.3.28 D.3 (IG-self-C)",
                    consequence_context="Package becomes not evaluable / fail closed",
                ),
            )

        if not _is_directory(root):
            return BoundaryResolution(
                root=None,
                problem=Issue(
                    location="trust_boundary",
                    detail=(
                        "configured trusted package-input boundary is missing or is not "
                        f"a readable directory: {root}"
                    ),
                    design_reference="§4.3.28 D.3 (IG-self-C)",
                    consequence_context="Package becomes not evaluable / fail closed",
                ),
            )

        if is_reparse_point(root):
            return BoundaryResolution(
                root=None,
                problem=Issue(
                    location="trust_boundary",
                    detail=(
                        "configured trusted package-input boundary is a symlink / junction / "
                        "reparse point, so the trust premise cannot be verified"
                    ),
                    design_reference="§4.3.28 D.3 (IG-self-C) / PN-1",
                    consequence_context="Package becomes not evaluable / fail closed",
                ),
            )

        try:
            candidate = Path(os.path.abspath(Path(package_dir).expanduser()))
        except (OSError, RuntimeError, ValueError) as exc:
            return BoundaryResolution(
                root=None,
                problem=Issue(
                    location="trust_boundary",
                    detail=f"package path could not be resolved: {exc}",
                    design_reference="§4.3.28 D.3 (IG-self-C)",
                    consequence_context="Package becomes not evaluable / fail closed",
                ),
            )

        if candidate.parent != root:
            return BoundaryResolution(
                root=None,
                problem=Issue(
                    location="trust_boundary",
                    detail=(
                        "package directory must be a direct child of the configured trusted "
                        f"input boundary; got {candidate}"
                    ),
                    design_reference="§4.3.23 A/G (flat directory package) + §4.3.28 D.3",
                    consequence_context="Package becomes not evaluable / fail closed",
                ),
            )

        if is_reparse_point(candidate):
            return BoundaryResolution(
                root=None,
                problem=Issue(
                    location="trust_boundary",
                    detail=(
                        "package directory is a symlink / junction / reparse point; alias "
                        "indirection is not allowed (PN-1 rule 6)"
                    ),
                    design_reference="§4.3.28 C.1 (PN-1)",
                    consequence_context="Package becomes not evaluable / fail closed",
                ),
            )

        if not _is_directory(candidate):
            return BoundaryResolution(
                root=None,
                problem=Issue(
                    location="trust_boundary",
                    detail=f"package directory is missing or is not a directory: {candidate}",
                    design_reference="§4.3.23 A",
                    consequence_context="Package becomes not evaluable / fail closed",
                ),
            )

        return BoundaryResolution(root=root, problem=None)


def _is_directory(path: Path) -> bool:
    """``Path.is_dir`` that also survives an unaddressable path.

    ``ValueError`` is what ``os`` / :mod:`pathlib` raise for a path the host cannot
    represent; treat it exactly like ``OSError`` so the caller fails closed instead
    of crashing.
    """

    try:
        return path.is_dir()
    except (OSError, ValueError):
        return False


def read_file_bytes(path: Path) -> tuple[bytes, FileView] | None:
    """Read ``path`` exactly once and return its bytes with a verified file view.

    ``None`` means unreadable / not a regular file / a reparse point, **or** a path
    the host cannot represent at all.  The digest is computed over the **exact raw
    bytes** that were read (``IG-raw``), with no JSON canonicalisation, so the
    returned bytes and the digest always describe the same content view.

    ``ValueError`` is handled exactly like ``OSError``: ``os`` raises it for a path
    the host cannot represent (an embedded NUL, for example), and that must surface
    as an absent / unreadable declared artifact (``IC-14`` / ``IC-16``) rather than
    as an uncaught loader crash.
    """

    if is_reparse_point(path):
        return None

    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOINHERIT", 0)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags | nofollow)
    except (OSError, ValueError):
        if nofollow:
            try:
                descriptor = os.open(path, flags)
            except (OSError, ValueError):
                return None
        else:
            return None

    try:
        try:
            before = os.fstat(descriptor)
        except OSError:
            return None
        if not stat.S_ISREG(before.st_mode):
            return None

        digest = hashlib.sha256()
        chunks: list[bytes] = []
        while True:
            try:
                chunk = os.read(descriptor, _READ_CHUNK)
            except OSError:
                return None
            if not chunk:
                break
            digest.update(chunk)
            chunks.append(chunk)

        try:
            after = os.fstat(descriptor)
        except OSError:
            return None
    finally:
        os.close(descriptor)

    size = int(after.st_size)
    if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
        # The file changed while it was being read: no stable view exists.
        return None

    raw = b"".join(chunks)
    if len(raw) != size:
        return None

    identity = physical_identity(path)
    view = FileView(
        name=path.name,
        sha256=digest.hexdigest(),
        size=size,
        mtime_ns=int(after.st_mtime_ns),
        identity=identity,
    )
    return raw, view


def list_root_entries(root: Path) -> list[str] | None:
    """Return a freshly built sorted list of package-root entry names.

    A **new list object** is returned on every call, and the underlying directory is
    re-scanned each time.  Callers therefore cannot accidentally compare a cached
    listing against itself, which matters for the acceptance-time stable-view checks
    (``§4.3.28`` C.2 ``Decision 10A``).  ``None`` means the directory was unlistable.
    """

    try:
        with os.scandir(root) as iterator:
            return [entry.name for entry in iterator]
    except (OSError, ValueError):
        # ValueError: the host cannot address this directory at all.
        return None


def compute_view_digest(files: tuple[FileView, ...]) -> str:
    """Digest of the *set* of verified files, used as the stable-view identifier."""

    digest = hashlib.sha256()
    for view in sorted(files, key=lambda item: item.name):
        digest.update(view.name.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(view.sha256.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class AcceptedPackage:
    """Immutable handle for a package that reached the ``ACCEPTED`` disposition.

    The handle carries package identity, the bound stable content view, the declared
    artifact digests, and the trusted boundary it was accepted under.  It exposes no
    mutating operation: re-verification produces a new verdict and never rewrites the
    accepted view (``IC-12``).
    """

    package_id: str
    contract_version: str
    package_path: Path
    boundary_root: Path
    content_view: ContentView
    declared_integrity: tuple[tuple[str, str], ...]
    #: ``(role, artifact, raw_bytes)`` for each included dataset, captured from the
    #: exact bytes read and verified during acceptance.  Downstream trusted reuse
    #: (Layer 2) consumes these bytes instead of re-reading files, because a re-read
    #: could observe content that no longer belongs to the accepted view
    #: (``§4.3.28`` C.2 / C.3).  Re-verification still runs first, so a package whose
    #: bytes changed is reported ``UNUSABLE`` rather than silently re-read.
    accepted_records: tuple[tuple[str, str, bytes], ...] = ()

    @property
    def content_view_digest(self) -> str:
        return self.content_view.digest

    def records_for(self, artifact: str) -> bytes | None:
        """Return the accepted-view bytes for ``artifact``, or ``None`` if absent."""

        for _, name, raw in self.accepted_records:
            if name == artifact:
                return raw
        return None

    def datasets(self) -> tuple[tuple[str, str], ...]:
        """Return ``(role, artifact)`` pairs in declared order."""

        return tuple((role, name) for role, name, _ in self.accepted_records)

    def to_dict(self) -> dict[str, object]:
        return {
            "package_id": self.package_id,
            "contract_version": self.contract_version,
            "package_path": str(self.package_path),
            "trusted_boundary_root": str(self.boundary_root),
            "content_view_digest": self.content_view.digest,
            "declared_integrity": dict(self.declared_integrity),
            "files": [view.to_dict() for view in self.content_view.files],
        }

    def reverify(self) -> "ReuseVerdict":
        """Re-establish required integrity before a trusted reuse (``MG-2``).

        Returns ``UNUSABLE`` when the package is no longer present, readable, or
        byte-identical to the accepted view, or when a declared
        ``"integrity_evidence"`` no longer matches the artifact bytes.
        """

        collector = IssueCollector()
        collector = collector.passed("trusted_reuse.reverification_attempted")

        if not _is_directory(self.package_path):
            collector = collector.failed(
                "trusted_reuse.package_present",
                "accepted package directory is no longer available",
            )
            collector = collector.issue(
                "package",
                "accepted package directory is no longer available; the accepted "
                "identity can no longer be trusted",
                design_reference="§4.3.28 C.3 (MG-2) / IC-12",
                consequence_context="Package becomes UNUSABLE",
            )
            return ReuseVerdict(
                disposition=DISPOSITION_UNUSABLE,
                content_view_digest=None,
                collector=collector,
            )

        names = list_root_entries(self.package_path)
        if names is None:
            collector = collector.failed(
                "trusted_reuse.package_listable", "package root is no longer listable"
            )
            collector = collector.issue(
                "package",
                "package root can no longer be listed; the accepted view cannot be "
                "re-established",
                design_reference="§4.3.28 C.3 (MG-2)",
                consequence_context="Package becomes UNUSABLE",
            )
            return ReuseVerdict(
                disposition=DISPOSITION_UNUSABLE,
                content_view_digest=None,
                collector=collector,
            )

        expected_names = sorted(view.name for view in self.content_view.files)
        if sorted(names) != expected_names:
            collector = collector.failed(
                "trusted_reuse.directory_listing_unchanged",
                "package root contents changed after acceptance",
            )
            collector = collector.issue(
                "package",
                "package root contents differ from the accepted view "
                f"(accepted={list(expected_names)!r}, current={list(names)!r})",
                design_reference="§4.3.5 / IC-12 immutability boundary",
                consequence_context="Package becomes UNUSABLE",
            )
        else:
            collector = collector.passed("trusted_reuse.directory_listing_unchanged")

        current_views: list[FileView] = []
        for expected in self.content_view.files:
            target = self.package_path / expected.name
            read = read_file_bytes(target)
            if read is None:
                collector = collector.failed(
                    f"trusted_reuse.readable:{expected.name}",
                    "artifact can no longer be read as a stable regular file",
                )
                collector = collector.issue(
                    expected.name,
                    "declared artifact can no longer be read; required integrity cannot "
                    "be re-established",
                    affected_evidence=expected.name,
                    design_reference="§4.3.28 C.3 (MG-2) / IC-22",
                    consequence_context="Package becomes UNUSABLE",
                )
                continue
            raw, view = read
            current_views.append(view)
            if view.sha256 != expected.sha256:
                collector = collector.failed(
                    f"trusted_reuse.raw_bytes:{expected.name}",
                    "raw artifact bytes changed after acceptance",
                )
                collector = collector.issue(
                    expected.name,
                    "raw-byte digest changed after acceptance "
                    f"(accepted={expected.sha256}, current={view.sha256})",
                    affected_evidence=expected.name,
                    design_reference="§4.3.6 / IC-12 / Decision 10B (MG-2)",
                    consequence_context="Package becomes UNUSABLE",
                )
            else:
                collector = collector.passed(f"trusted_reuse.raw_bytes:{expected.name}")
            _ = raw

        for artifact, declared_digest in self.declared_integrity:
            view = None
            for candidate in current_views:
                if candidate.name == artifact:
                    view = candidate
                    break
            if view is None:
                continue
            if view.sha256 != declared_digest:
                collector = collector.failed(
                    f"trusted_reuse.declared_integrity:{artifact}",
                    "declared integrity evidence no longer matches artifact bytes",
                )
                collector = collector.issue(
                    f"datasets[].{artifact}",
                    "declared \"integrity_evidence\" no longer matches the artifact raw "
                    "bytes",
                    affected_evidence=artifact,
                    design_reference="§4.3.28 D (IG-raw) / IC-22",
                    consequence_context="Package becomes UNUSABLE",
                )

        digest = None
        if len(current_views) == len(self.content_view.files):
            digest = compute_view_digest(tuple(current_views))
            if digest != self.content_view.digest:
                collector = collector.failed(
                    "trusted_reuse.content_view_digest",
                    "recomputed content view differs from the accepted view",
                )
        else:
            collector = collector.failed(
                "trusted_reuse.content_view_digest",
                "not every accepted package file could be re-read",
            )

        disposition = (
            DISPOSITION_UNUSABLE if collector.issues else "RE-VERIFIED"
        )
        return ReuseVerdict(
            disposition=disposition,
            content_view_digest=digest,
            collector=collector,
        )


@dataclass(frozen=True, slots=True)
class ReuseVerdict:
    """Outcome of a trusted-reuse re-verification."""

    disposition: str
    content_view_digest: str | None
    collector: IssueCollector

    @property
    def reusable(self) -> bool:
        return self.disposition == "RE-VERIFIED" and not self.collector.issues

    def to_dict(self) -> dict[str, object]:
        return {
            "disposition": self.disposition,
            "content_view_digest": self.content_view_digest,
            "issues": [issue.to_dict() for issue in self.collector.sorted_issues()],
            "checks": [check.to_dict() for check in self.collector.sorted_checks()],
        }


__all__ = [
    "AcceptedPackage",
    "BoundaryResolution",
    "ContentView",
    "FileView",
    "ReuseVerdict",
    "TrustedInputBoundary",
    "compute_view_digest",
    "list_root_entries",
    "read_file_bytes",
    "MANIFEST_FILENAME",
]
