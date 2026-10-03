"""Tests for wordcount.py: the counter, the command-line contract, the demo.

Run with ``python3 -m pytest`` from the project root.
"""

from __future__ import annotations

import dataclasses
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

import wordcount
from wordcount import FileProblem, WordCount, count_words, read_text

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "wordcount.py"

INTEGER_LINE = re.compile(r"\A\d+\n\Z")


def run_cli(*args: str) -> subprocess.CompletedProcess:
    """Run wordcount.py as a real subprocess, the way a shell script would."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )


@pytest.fixture
def text_file(tmp_path: Path):
    def write(name: str, content: str) -> Path:
        target = tmp_path / name
        target.write_text(content, encoding="utf-8")
        return target

    return write


class TestCountWords:
    """F1 — the pure counter."""

    def test_counts_space_separated_words(self):
        assert count_words("the quick brown fox") == 4

    def test_empty_text_counts_zero(self):
        assert count_words("") == 0

    def test_whitespace_only_text_counts_zero(self):
        assert count_words("  \n\t\n") == 0

    def test_whitespace_runs_and_edge_whitespace_do_not_add_words(self):
        assert count_words("one  two\tthree\n four ") == 4

    def test_counts_words_across_lines(self):
        assert count_words("first line\nsecond line\n\nthird\n") == 5

    def test_is_deterministic(self):
        text = "repeatable counts\n" * 50
        assert count_words(text) == count_words(text) == 100


class TestWordCountValue:
    """The result value that carries the count back to the caller."""

    def test_holds_the_path_and_the_count(self):
        result = WordCount(path="sample.txt", count=4)
        assert (result.path, result.count) == ("sample.txt", 4)

    def test_is_frozen(self):
        result = WordCount(path="sample.txt", count=4)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.count = 5


class TestCliSuccess:
    """T2 — reading the file, counting it, printing the number."""

    def test_prints_the_count_and_exits_zero(self, text_file):
        target = text_file("sample.txt", "the quick brown fox")
        result = run_cli(str(target))
        assert result.returncode == 0
        assert result.stdout == "4\n"
        assert result.stderr == ""

    def test_zero_byte_file_prints_zero(self, tmp_path):
        target = tmp_path / "empty.txt"
        target.touch()
        result = run_cli(str(target))
        assert (result.returncode, result.stdout, result.stderr) == (0, "0\n", "")

    def test_whitespace_only_file_prints_zero(self, text_file):
        target = text_file("blank.txt", "  \n\t\n")
        result = run_cli(str(target))
        assert (result.returncode, result.stdout, result.stderr) == (0, "0\n", "")

    def test_stdout_carries_only_the_integer(self, text_file):
        target = text_file("notes.md", "# Title\n\nsome  words\there\n")
        result = run_cli(str(target))
        assert INTEGER_LINE.match(result.stdout)
        assert result.stdout == "5\n"

    def test_main_passes_the_file_text_not_the_path_to_count_words(
        self, text_file, monkeypatch, capsys
    ):
        target = text_file("poem.txt", "the quick brown fox")
        seen: list[str] = []
        real_counter = wordcount.count_words

        def spy(text: str) -> int:
            seen.append(text)
            return real_counter(text)

        monkeypatch.setattr(wordcount, "count_words", spy)

        assert wordcount.main([str(target)]) == 0
        assert seen == ["the quick brown fox"]
        assert capsys.readouterr().out == "4\n"

    def test_prints_the_count_field_of_the_wordcount_value(
        self, text_file, monkeypatch, capsys
    ):
        target = text_file("sample.txt", "the quick brown fox")
        recorded: list[WordCount] = []
        real_value = wordcount.WordCount

        class Recording(real_value):  # type: ignore[misc, valid-type]
            def __init__(self, path: str, count: int) -> None:
                super().__init__(path=path, count=count)
                recorded.append(self)

        monkeypatch.setattr(wordcount, "WordCount", Recording)

        assert wordcount.main([str(target)]) == 0
        assert capsys.readouterr().out == "4\n"
        assert [(item.path, item.count) for item in recorded] == [(str(target), 4)]

    def test_shipped_example_files_are_intact(self):
        assert count_words(read_text(str(REPO_ROOT / "examples" / "sample.txt"))) == 4
        assert count_words(read_text(str(REPO_ROOT / "examples" / "empty.txt"))) == 0
        assert (
            count_words(read_text(str(REPO_ROOT / "examples" / "whitespace.txt"))) == 0
        )

    def test_one_megabyte_file_is_counted_well_under_a_second(self, tmp_path):
        target = tmp_path / "big.txt"
        target.write_text(
            "alfa bravo charlie delta echo foxtrot\n" * 28000, encoding="utf-8"
        )
        assert target.stat().st_size > 1_000_000

        started = time.perf_counter()
        result = run_cli(str(target))
        elapsed = time.perf_counter() - started

        assert result.stdout == "168000\n"
        assert result.returncode == 0
        assert elapsed < 2.0


class TestBadInvocation:
    """T3 — exactly one path argument, otherwise a one-line usage message."""

    def test_no_arguments_prints_usage_and_exits_two(self):
        result = run_cli()
        assert result.returncode == 2
        assert result.stdout == ""
        assert result.stderr.strip() == "usage: wordcount.py <path>"

    def test_two_arguments_print_usage_and_exit_two(self):
        result = run_cli("a.txt", "b.txt")
        assert result.returncode == 2
        assert result.stdout == ""
        assert result.stderr.strip() == "usage: wordcount.py <path>"

    def test_usage_names_the_script_and_the_path_placeholder(self):
        assert wordcount.USAGE == "usage: wordcount.py <path>"
        assert run_cli().stderr.strip() == wordcount.USAGE

    def test_usage_is_a_single_line(self):
        assert run_cli().stderr.count("\n") == 1

    def test_a_valid_run_prints_no_usage(self):
        result = run_cli("examples/sample.txt")
        assert result.returncode == 0
        assert "usage" not in result.stderr.lower()


class TestFileProblems:
    """T4 — plain-language errors instead of tracebacks."""

    def test_missing_file_is_named_and_exits_one(self):
        result = run_cli("missing.txt")
        assert result.returncode == 1
        assert result.stdout == ""
        assert result.stderr.strip() == "wordcount: missing.txt: no such file"

    def test_directory_is_reported(self, tmp_path):
        result = run_cli(str(tmp_path))
        assert result.returncode == 1
        assert result.stdout == ""
        assert result.stderr.strip() == f"wordcount: {tmp_path}: is a directory"

    def test_unreadable_file_is_reported(self, tmp_path):
        target = tmp_path / "locked.txt"
        target.write_text("sealed\n", encoding="utf-8")
        target.chmod(0o000)
        try:
            content = read_text(str(target))
        except FileProblem as problem:
            assert problem.reason == "permission denied"
        else:
            pytest.skip(
                f"this user can still read {content!r}, so permission denied cannot occur"
            )

        result = run_cli(str(target))
        assert result.returncode == 1
        assert result.stdout == ""
        assert result.stderr.strip() == f"wordcount: {target}: permission denied"

    def test_invalid_utf8_is_reported(self, tmp_path):
        target = tmp_path / "binary.txt"
        target.write_bytes("café\n".encode("latin-1"))
        result = run_cli(str(target))
        assert result.returncode == 1
        assert result.stdout == ""
        assert result.stderr.strip() == f"wordcount: {target}: not valid UTF-8 text"

    @pytest.mark.parametrize(
        "args",
        [
            (),
            ("missing.txt",),
            ("examples",),
            ("examples/not_utf8.txt",),
            ("a.txt", "b.txt"),
        ],
    )
    def test_no_failure_path_shows_a_traceback(self, args):
        result = run_cli(*args)
        assert "Traceback" not in result.stderr
        assert "Traceback" not in result.stdout
        assert result.returncode != 0

    def test_diagnostics_stay_plain_when_stderr_is_not_a_terminal(self):
        assert "\x1b[" not in run_cli("missing.txt").stderr


class TestExitStatusContract:
    """T5 — 0 on success, 1 for file problems, 2 for a bad invocation."""

    def test_success_status_and_stream(self):
        result = run_cli("examples/release_notes.md")
        assert result.returncode == 0
        assert INTEGER_LINE.match(result.stdout)
        assert result.stderr == ""

    def test_file_problem_status_and_stream(self):
        result = run_cli("examples/not_utf8.txt")
        assert result.returncode == 1
        assert result.stdout == ""
        assert result.stderr != ""

    def test_bad_invocation_status_and_stream(self):
        result = run_cli()
        assert result.returncode == 2
        assert result.stdout == ""
        assert result.stderr != ""

    def test_exit_statuses_are_distinct_per_error_class(self):
        assert run_cli().returncode == 2  # bad invocation
        assert run_cli("missing.txt").returncode == 1  # file problem
        assert run_cli("examples/sample.txt").returncode == 0  # counted


class TestColourIsOptional:
    """The single accent is decoration: plain output whenever it is not wanted."""

    class FakeTerminal:
        def isatty(self) -> bool:
            return True

    def test_colour_is_on_for_a_terminal(self, monkeypatch):
        monkeypatch.delenv("NO_COLOR", raising=False)
        monkeypatch.delenv("TERM", raising=False)
        assert wordcount._supports_colour(self.FakeTerminal()) is True

    def test_no_color_disables_it(self, monkeypatch):
        monkeypatch.setenv("NO_COLOR", "1")
        assert wordcount._supports_colour(self.FakeTerminal()) is False

    def test_a_dumb_terminal_disables_it(self, monkeypatch):
        monkeypatch.delenv("NO_COLOR", raising=False)
        monkeypatch.setenv("TERM", "dumb")
        assert wordcount._supports_colour(self.FakeTerminal()) is False


class TestDemo:
    """demo.sh is the recorded, non-interactive walkthrough — keep it honest."""

    def test_demo_runs_to_completion_without_input(self):
        result = subprocess.run(
            ["bash", "demo.sh"],
            check=False,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=180,
            env={**os.environ, "NO_COLOR": "1"},
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "checks passed" in result.stdout
        assert "examples/release_notes.md" in result.stdout
        assert "usage: wordcount.py <path>" in result.stdout


class TestDesignTokens:
    """DESIGN.md is the source of truth; the shipped table must match it."""

    def test_theme_carries_the_committed_accent(self):
        assert wordcount.THEME["accent"] == "oklch(0.58 0.12 170)"
        assert wordcount.THEME["accent_hex"] == "#00906f"

    def test_theme_is_monospace_only(self):
        assert "monospace" in wordcount.THEME["type"]

    def test_accent_ansi_matches_the_accent_hex(self):
        red, green, blue = 0x00, 0x90, 0x6F
        assert wordcount.THEME["accent_ansi"] == f"\x1b[38;2;{red};{green};{blue}m"
