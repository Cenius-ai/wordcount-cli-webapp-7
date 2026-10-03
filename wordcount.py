"""wordcount — print the number of words in a UTF-8 text file.

    python wordcount.py <path>

A word is a maximal run of non-whitespace characters, which is exactly what
``str.split()`` with no argument produces: runs of separators and leading or
trailing whitespace never yield empty words.  The count is the only thing
written to stdout, so the command stays safe inside a pipeline; every
diagnostic goes to stderr as one plain sentence.

Exit status: 0 success, 1 file problem, 2 bad invocation.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Sequence, TextIO

PROGRAM_NAME = "wordcount.py"
LABEL = "wordcount"
USAGE_TARGET = f"{PROGRAM_NAME} <path>"
USAGE = f"usage: {USAGE_TARGET}"

EXIT_SUCCESS = 0
EXIT_FILE_PROBLEM = 1
EXIT_BAD_INVOCATION = 2

# Committed design direction for the terminal surface, documented in DESIGN.md:
# a terminal-dark neutral ramp with one teal accent, oklch(0.58 0.12 170)
# == #00906f.  The 24-bit ANSI escapes below are that same palette; they are
# applied to diagnostic labels only, and only when stderr is a colour-capable
# terminal, so piped output stays byte-for-byte plain.
THEME = {
    "accent": "oklch(0.58 0.12 170)",
    "accent_hex": "#00906f",
    "accent_ansi": "\x1b[38;2;0;144;111m",
    "muted": "oklch(0.70 0.012 170)",
    "muted_hex": "#9aa8a4",
    "muted_ansi": "\x1b[38;2;154;168;164m",
    "surface": "oklch(0.16 0.008 170)",
    "surface_hex": "#0b0f0e",
    "foreground": "oklch(0.95 0.008 170)",
    "foreground_hex": "#e6edea",
    "type": "system monospace",
    "reset_ansi": "\x1b[0m",
}


@dataclass(frozen=True)
class WordCount:
    """The word total for one file, exactly as the command line computed it."""

    path: str
    count: int


class FileProblem(Exception):
    """The named file could not be turned into text.

    Carries the plain-language reason so ``main`` can report one sentence
    naming the path instead of letting an OS error surface as a traceback.
    """

    def __init__(self, path: str, reason: str) -> None:
        super().__init__(f"{path}: {reason}")
        self.path = path
        self.reason = reason


def count_words(text: str) -> int:
    """Return the number of words in *text*.

    ``str.split()`` with no argument splits on any run of whitespace (spaces,
    tabs, newlines) and drops leading and trailing whitespace, so a zero-length
    or whitespace-only text counts as 0.
    """
    return len(text.split())


def read_text(path: str) -> str:
    """Read *path* as UTF-8 text, or raise :class:`FileProblem` with the reason.

    Directories, missing paths, unreadable files and non-UTF-8 bytes are all
    normal user mistakes here, so each one becomes a plain sentence rather
    than an exception the caller has to decode.
    """
    if os.path.isdir(path):
        raise FileProblem(path, "is a directory")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except FileNotFoundError:
        raise FileProblem(path, "no such file") from None
    except IsADirectoryError:
        raise FileProblem(path, "is a directory") from None
    except PermissionError:
        raise FileProblem(path, "permission denied") from None
    except UnicodeDecodeError:
        raise FileProblem(path, "not valid UTF-8 text") from None
    except OSError as error:
        raise FileProblem(path, error.strerror or "could not be read") from None


def _supports_colour(stream: TextIO) -> bool:
    """True only for an interactive, colour-capable terminal the user asked for."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    try:
        return bool(stream.isatty())
    except (AttributeError, ValueError):
        return False


def _emit(label: str, text: str, tone: str) -> None:
    """Write ``<label> <text>`` to stderr, tinting the label on a real terminal."""
    if _supports_colour(sys.stderr):
        painted = f"{THEME[f'{tone}_ansi']}{label}{THEME['reset_ansi']}"
    else:
        painted = label
    print(f"{painted} {text}", file=sys.stderr)


def _report_usage() -> None:
    _emit("usage:", USAGE_TARGET, "muted")


def _report_problem(problem: FileProblem) -> None:
    _emit(f"{LABEL}:", f"{problem.path}: {problem.reason}", "accent")


def main(argv: Sequence[str]) -> int:
    """Count the words in the single path named by *argv* and print the total.

    Returns the process exit status: 0 when the count was printed, 2 when the
    command line did not name exactly one path, 1 when the path could not be
    read as UTF-8 text.
    """
    if len(argv) != 1:
        _report_usage()
        return EXIT_BAD_INVOCATION

    path = argv[0]
    try:
        text = read_text(path)
    except FileProblem as problem:
        _report_problem(problem)
        return EXIT_FILE_PROBLEM

    result = WordCount(path=path, count=count_words(text))
    print(result.count)
    return EXIT_SUCCESS


def cli() -> int:
    """Console-script entry point (see ``[project.scripts]`` in pyproject.toml)."""
    return main(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
