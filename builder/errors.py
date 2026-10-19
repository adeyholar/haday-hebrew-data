"""Exceptions the builder raises. The command line turns them into a non-zero exit."""


class BuildError(Exception):
    """Base class: the dataset cannot be built as pinned."""


class SourceMismatch(BuildError):
    """A pinned source is missing, changed, or not listed in SHA256SUMS."""


class PinError(BuildError):
    """sources/PINS.txt is missing a key or has a malformed line."""


class TriageError(BuildError):
    """The triage CSV cannot be applied as written."""


class MarkError(BuildError):
    """A word's marks changed where they must not (canon not stable, or a mark lost)."""
