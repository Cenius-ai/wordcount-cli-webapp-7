#!/usr/bin/env bash
# demo.sh — a non-interactive, end-to-end walkthrough of wordcount.py.
#
# Runs the tool for real against the files in examples/, prints an aligned
# table of the results, then exercises every failure path and the exit-status
# contract.  It needs nothing but python3, writes only inside a scratch
# directory that it removes on exit, never prompts, and returns 0 only when
# every expectation it checked held.
set -uo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT

# Committed design direction (see DESIGN.md): a terminal-dark neutral ramp with
# one teal accent for primary status and muted chrome.  Colour is dropped when
# stdout is not a terminal or NO_COLOR is set, so piped and recorded output
# stays plain.
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ] && [ "${TERM:-}" != "dumb" ]; then
  ACCENT=$'\033[38;2;0;144;111m'
  MUTED=$'\033[38;2;154;168;164m'
  RESET=$'\033[0m'
else
  ACCENT=''
  MUTED=''
  RESET=''
fi

RULE='──────────────────────────────────────────────────────────────────────'
CHECKS=0
FAILURES=0

rule() { printf '%s%s%s\n' "$MUTED" "$RULE" "$RESET"; }

check() {  # check <description> <expected> <actual>
  CHECKS=$((CHECKS + 1))
  if [ "$2" != "$3" ]; then
    FAILURES=$((FAILURES + 1))
    printf '   %s %s: expected %s, got %s\n' "${ACCENT}MISMATCH${RESET}" "$1" "$2" "$3"
  fi
}

row() {  # row <file> <words> <verdict> <tone>
  local tint=''
  case "$4" in
    accent) tint="$ACCENT" ;;
    muted) tint="$MUTED" ;;
  esac
  printf '   %-32s %6s  %s\n' "$1" "$2" "${tint}$3${RESET}"
}

run_tool() {  # run_tool <args...>  -> sets STATUS, STDOUT_TEXT, STDERR_TEXT
  STDOUT_TEXT="$("$PYTHON" wordcount.py "$@" 2>"$SCRATCH/stderr")"
  STATUS=$?
  STDERR_TEXT="$(cat "$SCRATCH/stderr")"
  return 0
}

probe() {  # probe <expected status> <displayed command> <args...>
  local expected="$1" display="$2"
  shift 2
  run_tool "$@"
  check "'$display' exit status" "$expected" "$STATUS"
  check "'$display' leaves stdout empty" "" "$STDOUT_TEXT"
  printf '   $ %s\n' "$display"
  printf '     exit %s  stdout: %s\n' "$STATUS" "${STDOUT_TEXT:-<empty>}"
  printf '     stderr: %s\n' "$STDERR_TEXT"
  case "$STDERR_TEXT" in
    *Traceback*)
      FAILURES=$((FAILURES + 1))
      printf '     %s\n' "${ACCENT}a Python traceback leaked${RESET}"
      ;;
  esac
}

printf '%s\n' "${ACCENT}wordcount 0.3.0${RESET} ${MUTED}· one word total from the shell · standard library only${RESET}"
rule
printf '\n'

# ---------------------------------------------------------------- 1 · counting
printf '1 · Counting the example files\n'
rule
printf '   %-32s %6s  %s\n' "file" "words" "status"
printf '   %s\n' "${MUTED}────────────────────────────────  ──────  ──────${RESET}"
for target in examples/sample.txt examples/release_notes.md examples/empty.txt examples/whitespace.txt; do
  run_tool "$target"
  row "$target" "${STDOUT_TEXT:-<empty>}" "ok" accent
done
run_tool examples/sample.txt
check "sample.txt counts four words" 4 "$STDOUT_TEXT"
run_tool examples/empty.txt
check "zero-byte file counts zero" 0 "$STDOUT_TEXT"
run_tool examples/whitespace.txt
check "whitespace-only file counts zero" 0 "$STDOUT_TEXT"
printf '\n'

# ------------------------------------------------- 2 · the scriptable contract
printf '2 · The scriptable contract — the integer on stdout, everything else on stderr\n'
rule
run_tool examples/release_notes.md
NOTES_WORDS="$STDOUT_TEXT"
NOTES_BYTES="$(printf '%s\n' "$NOTES_WORDS" | wc -c | tr -d ' ')"
check "release notes counted with status 0" 0 "$STATUS"
printf '   $ %s wordcount.py examples/release_notes.md\n' "$PYTHON"
printf '   %s\n' "$NOTES_WORDS"
printf '   $ %s wordcount.py examples/release_notes.md | wc -c\n' "$PYTHON"
printf '   %s\n' "$NOTES_BYTES"
printf '   %s\n' "${MUTED}stdout is the count plus one newline and nothing else — safe to capture${RESET}"
printf '   $ words=$(%s wordcount.py examples/release_notes.md); echo "counted $words words"\n' "$PYTHON"
printf '   counted %s words\n' "$NOTES_WORDS"
printf '\n'

# --------------------------------------------------------------- 3 · failures
printf '3 · Failures — one plain sentence on stderr, a distinct exit status, no traceback\n'
rule
probe 1 "python3 wordcount.py missing.txt" missing.txt
probe 1 "python3 wordcount.py examples" examples
probe 1 "python3 wordcount.py examples/not_utf8.txt" examples/not_utf8.txt

LOCKED="$SCRATCH/locked.txt"
printf 'sealed\n' > "$LOCKED"
chmod 000 "$LOCKED"
if [ -r "$LOCKED" ]; then
  printf '   %s\n' "${MUTED}(unreadable-file case skipped: this user may read every file)${RESET}"
else
  probe 1 "python3 wordcount.py $LOCKED" "$LOCKED"
fi

probe 2 "python3 wordcount.py"
probe 2 "python3 wordcount.py a.txt b.txt" a.txt b.txt
printf '   %s\n' "${MUTED}exit 1 = file problem, exit 2 = bad invocation; there are no flags by design${RESET}"
printf '\n'

# ---------------------------------------------------------------- 4 · timing
printf '4 · Size and determinism — a multi-megabyte file, counted in milliseconds\n'
rule
BIG="$SCRATCH/big.txt"
"$PYTHON" -c "import sys; open(sys.argv[1], 'w', encoding='utf-8').write('alfa bravo charlie delta echo foxtrot\n' * 36200)" "$BIG"
BIG_BYTES="$(wc -c < "$BIG" | tr -d ' ')"
TIMING="$("$PYTHON" -c "
import subprocess, sys, time
start = time.perf_counter()
done = subprocess.run([sys.executable, 'wordcount.py', sys.argv[1]], capture_output=True, text=True)
print(done.stdout.strip(), round((time.perf_counter() - start) * 1000))
" "$BIG")"
BIG_WORDS="${TIMING% *}"
BIG_MS="${TIMING##* }"
run_tool "$BIG"
SECOND_PASS="$STDOUT_TEXT"
check "large-file count is deterministic" "$BIG_WORDS" "$SECOND_PASS"
printf '   %s bytes → %s words in %s ms, and the same integer on a second run\n' "$BIG_BYTES" "$BIG_WORDS" "$BIG_MS"
printf '\n'

# ------------------------------------------------------------------ 5 · usage
printf '5 · Where to go next\n'
rule
printf '   %-14s %s\n' "count a file" "$PYTHON wordcount.py <path>"
printf '   %-14s %s\n' "test suite" "$PYTHON -m pytest"
printf '   %-14s %s\n' "setup script" "bash install.sh"
printf '\n'
rule
if [ "$FAILURES" -gt 0 ]; then
  printf '%s\n' "${ACCENT}$FAILURES of $CHECKS checks failed${RESET}"
  exit 1
fi
printf '%s\n' "${ACCENT}all $CHECKS checks passed${RESET}"
exit 0
