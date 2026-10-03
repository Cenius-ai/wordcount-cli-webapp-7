# wordcount release notes

## 0.3.0 — 2024-05-14

The scriptable contract is frozen. A successful run writes one decimal integer
to stdout and nothing else, so `$(...)` capture and `wc`-style pipelines keep
working without trimming. Exit statuses carry meaning: zero for a count, one for
a file the tool could not read, and two for a command line that did not name
exactly one path.

## 0.2.0 — 2024-04-02

File problems stopped reaching the user as a traceback. A missing file, a
directory, a permission-denied file and a file whose bytes are not valid UTF-8
now produce a single sentence on stderr naming the path, while stdout stays
empty — which is the first thing a shell script checks.

## 0.1.0 — 2024-03-11

First cut: `count_words` returns `len(text.split())` and the command line reads
one named file as UTF-8 text. A word is a maximal run of non-whitespace
characters, so runs of separators and leading or trailing whitespace never
produce an extra word.

## Notes for contributors

Run `bash demo.sh` for a full non-interactive walkthrough, and
`python3 -m pytest` for the suite. The tool is one file with no dependencies,
so there is nothing to build and nothing to configure: clone it and run it.
Counts are deterministic — the same bytes always print the same integer.
